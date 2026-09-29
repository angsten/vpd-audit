"""The smoke: load a run, compute g on n sequences, run the reference conditions
(extended by the two residual test conditions) with the on-device fingerprint on, and check the
donor-free identities at that scale: M1, M2 (range and counts only), M3, M4, M5, M6a to M6e (with
the fingerprint's digests in place of the SHA-256), M12 (reported), M13 (bf16 against float32, CUDA only); and the
fingerprint's validation: G1 (CPU against CUDA, bitwise, on 8 sequences, float32 masks and their bf16
casts), G2 (SHA-256 equivalence on 8 sequences: identical all-pairs equality matrices), G3 (pairwise distinct cell
digests across the masked conditions and their draws; the residual identity per draw and sub-batch), G3b (the
residual identity on the first sub-batch of the residual test cells, both precisions, draws 0 to 3), and the cross-entropy
diagnostic added after the matched-shape bf16 rerun of check 6 returned "pass, localize": the authors' `ce_vs_labels` and our `per_sequence_ce`
on the same logits against a float64 reference. Prints a pass/fail table. Writes under results/smoke_fp/.
"""

from __future__ import annotations

import resource
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np
import torch
from torch import Tensor

from vpd_audit import env
from vpd_audit.artifacts import checkpoint_hashes, load_component_model, load_run_config
from vpd_audit.constants import IMPORTANCE_CHUNK, KL_CHUNK
from vpd_audit.data import load_set, prepare_simplestories_rows
from vpd_audit.fingerprint import fingerprint, level3_hex, sum_hex
from vpd_audit.importances import ImportanceSums, Importances, autocast_context, compute_importances, module_keys
from vpd_audit.masks import apply_binary_source, apply_source, masked_forward, rounded_mask, uniform_background, wrap_masks
from vpd_audit.metrics import per_position_kl, per_sequence_ce
from vpd_audit.reference import (
    ALL_CONDITIONS,
    CONDITION_BY_NAME,
    PAPER_ALIVE,
    PAPER_L0,
    build_condition_masks,
    cell_key,
    check_ordering,
    condition_table,
    evaluate_condition,
    run_references,
)

SMOKE_OUT_ROOT = "smoke_fp"  # results/smoke/ from the earlier smoke, before the fingerprint existed, stays untouched


@dataclass
class Check:
    id: str
    passed: bool | None  # None = reported, not gated
    detail: str


def _bitwise(a: Tensor, b: Tensor) -> bool:
    return a.shape == b.shape and a.dtype == b.dtype and bool(torch.equal(a, b))


def _maxdiff(a: Tensor, b: Tensor) -> float:
    return float((a.float() - b.float()).abs().max())


def _free(device: str) -> None:
    import gc

    gc.collect()
    if str(device).startswith("cuda"):
        torch.cuda.empty_cache()


def peak_rss_gb() -> float:
    rss = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    return rss / 1e9 if sys.platform == "darwin" else rss / 1e6


def smoke_ids(run: str, n: int) -> tuple[np.ndarray, str, str]:
    if run == "simplestories":
        prepare_simplestories_rows(n, load_run_config("simplestories"))
        ids, _, record = load_set(f"simplestories_smoke_{n}")
        return ids[:n], f"simplestories_smoke_{n}", record["sha256_ids"]
    ids, _, record = load_set("E")
    assert n <= ids.shape[0]
    return ids[:n], "E", record["sha256_ids"]


def masked_cells(n_draws: int) -> list[tuple[Any, int]]:
    return [(c, k) for c in ALL_CONDITIONS if c.kind != "target" for k in (range(n_draws) if c.per_draw else [0])]


def run_smoke(
    run: str,
    n: int,
    *,
    precision: str,
    device: str,
    subbatch: int | None = None,
    n_draws: int = 2,
    master_seed: int = 0,
    out_dir: Path | None = None,
    subbatch_sizes: tuple[int, ...] = (1, 4, 8),
    log: Any = print,
) -> list[Check]:
    torch.use_deterministic_algorithms(True, warn_only=True)
    checks: list[Check] = []
    subbatch = subbatch or n
    out_dir = out_dir or (env.RESULTS_DIR / SMOKE_OUT_ROOT / f"{run}_{precision}_n{n}")
    tol_eq = 1e-5 if precision == "fp32" else 1e-3

    t0 = time.time()
    model = load_component_model(run, device)
    log(f"[smoke] loaded {run} on {device} in {time.time() - t0:.1f} s; {len(model.components)} matrices, {sum(model.module_to_c.values())} subcomponents")
    weight_deltas = model.calc_weight_deltas()
    ids, set_name, set_hash = smoke_ids(run, n)
    hashes = checkpoint_hashes(run)
    keys = module_keys(model)

    # the reference conditions, extended by the two residual test conditions, on the n sequences, fingerprint on
    t0 = time.time()
    store = run_references(model, ids, job=f"smoke_{run}_{precision}_n{n}", run=run, out_dir=out_dir, precision=precision,
                           subbatch=subbatch, n_draws=n_draws, master_seed=master_seed, set_name=set_name, set_hash=set_hash,
                           checkpoint_hashes=hashes, conditions=ALL_CONDITIONS, resume=False, log=log)
    df = store.table()
    log(f"[smoke] references in {time.time() - t0:.1f} s")
    log(condition_table(df).to_string(index=False, float_format=lambda x: f"{x:.4f}"))

    batch = torch.from_numpy(np.ascontiguousarray(ids[:subbatch])).long().to(device)
    imp = compute_importances(model, batch, precision=precision)
    g = imp.g
    idx = np.arange(batch.shape[0])

    # M1: one cell twice, deterministic algorithms on
    imp2 = compute_importances(model, batch, precision=precision)
    g_same = all(_bitwise(g[k], imp2.g[k]) for k in keys)
    logits_same = _bitwise(imp.target_logits, imp2.target_logits)
    del imp2
    _free(device)
    a = evaluate_condition(model, CONDITION_BY_NAME["stochastic_delta"], batch, imp, draw=0, subbatch_index=0, master_seed=master_seed, weight_deltas=weight_deltas, keep_logits=True)
    a_logits, a_kl, a_fp = a.logits, a.kl, a.fp
    del a
    b = evaluate_condition(model, CONDITION_BY_NAME["stochastic_delta"], batch, imp, draw=0, subbatch_index=0, master_seed=master_seed, weight_deltas=weight_deltas, keep_logits=True)
    cell_same = _bitwise(a_logits, b.logits) and _bitwise(a_kl, b.kl) and a_fp == b.fp
    d_kl = _maxdiff(a_kl, b.kl)
    checks.append(Check("M1", (g_same and logits_same and cell_same) or d_kl < 1e-6,
                        f"g bitwise={g_same}, target logits bitwise={logits_same}, stochastic-delta cell bitwise={cell_same} incl. digests (max |dKL|={d_kl:.2e})"))
    del a_logits, a_kl, b
    _free(device)

    # M2: g in [0, 1] (asserted in compute_importances) and the per-layer counts
    sums = ImportanceSums.empty(model)
    sums.update(g)
    gmin = min(float(g[k].min()) for k in keys)
    gmax = max(float(g[k].max()) for k in keys)
    l0 = sums.per_layer_mean_count()
    alive = sums.alive_counts()
    detail = f"g in [{gmin:.3f}, {gmax:.3f}]; mean count g>0 per position {{{', '.join(f'{k}: {v:.1f}' for k, v in l0.items())}}}; alive on these {n} seqs {alive}"
    if run in ("main", "control"):
        detail += f"; paper L0 {PAPER_L0}, paper alive {PAPER_ALIVE} (gated in the acceptance test)"
    checks.append(Check("M2", 0.0 <= gmin and gmax <= 1.0, detail))

    # M3: our per-position divergence against the authors' scalar on the same logits
    from param_decomp.utils.general_utils import calc_kl_divergence_lm

    res = evaluate_condition(model, CONDITION_BY_NAME["importances"], batch, imp, draw=0, subbatch_index=0, master_seed=master_seed, weight_deltas=weight_deltas, keep_logits=True)
    n3 = min(KL_CHUNK, batch.shape[0])  # the authors' scalar is unchunked: 3 float32 (n, T, V) temporaries, so 8 sequences
    with torch.no_grad(), autocast_context(device, precision):
        theirs = float(calc_kl_divergence_lm(pred=res.logits[:n3], target=imp.target_logits[:n3]))
    ours = float(res.kl[:n3].mean())
    finite = bool(torch.isfinite(res.kl).all()) and float(res.kl.min()) > -1e-4
    checks.append(Check("M3", abs(ours - theirs) < 1e-6 and finite, f"on {n3} sequences: ours {ours:.8f} vs authors' {theirs:.8f} (|diff|={abs(ours - theirs):.2e}); all {batch.shape[0]} finite and > -1e-4: {finite}; min {float(res.kl.min()):.2e}"))
    del res
    _free(device)

    # M4: g from a masked forward's cache differs (tripwire); stored g equals the clean one bitwise
    zero_masks = {k: torch.zeros_like(g[k]) for k in keys}
    with torch.no_grad(), autocast_context(device, precision):
        out_masked = model(batch, mask_infos=wrap_masks(model, zero_masks), cache_type="input")
        ci_masked = model.calc_causal_importances(out_masked.cache, sampling="continuous", detach_inputs=False)
    g_masked = ci_masked.lower_leaky
    del ci_masked, out_masked, zero_masks
    differs = max(_maxdiff(g[k], g_masked[k]) for k in keys)
    del g_masked
    _free(device)
    clean_again = compute_importances(model, batch, precision=precision).g
    stored_ok = all(_bitwise(g[k], clean_again[k]) for k in keys)
    checks.append(Check("M4", differs > 0 and stored_ok, f"max |g_clean - g_from_zero_masked_cache| = {differs:.4f} (must be > 0); stored g == clean g bitwise: {stored_ok}"))
    del clean_again
    _free(device)

    # M5: per-sequence divergence at several sub-batch sizes.
    # Gate: g computed once per sub-batch at the fixed chunk and sliced, so only the forward's
    # sub-batch independence is tested. Reported beside it: g recomputed at each size, which in
    # bf16 also carries g's chunk-shape sensitivity.
    sizes = tuple(sorted(s for s in subbatch_sizes if s <= subbatch))
    per_size: dict[int, list[Tensor]] = {s: [] for s in sizes}
    per_size_recomputed: dict[int, list[Tensor]] = {s: [] for s in sizes}
    for start in range(0, n, subbatch):
        sub_ids = ids[start : start + subbatch]
        sub_all = torch.from_numpy(np.ascontiguousarray(sub_ids)).long().to(device)
        imp_all = compute_importances(model, sub_all, precision=precision)  # the fixed chunk
        for s in sizes:
            for a_ in range(0, sub_all.shape[0], s):
                b_ = min(a_ + s, sub_all.shape[0])
                imp_slice = Importances(g={k: imp_all.g[k][a_:b_] for k in keys}, target_logits=imp_all.target_logits[a_:b_],
                                        chunk=imp_all.chunk, precision=precision)
                r = evaluate_condition(model, CONDITION_BY_NAME["importances"], sub_all[a_:b_], imp_slice, draw=0, subbatch_index=0,
                                       master_seed=master_seed, weight_deltas=weight_deltas)
                per_size[s].append(r.kl.mean(dim=-1).cpu())
                del imp_slice, r
                imp_s = compute_importances(model, sub_all[a_:b_], precision=precision, chunk=max(b_ - a_, 1))
                r = evaluate_condition(model, CONDITION_BY_NAME["importances"], sub_all[a_:b_], imp_s, draw=0, subbatch_index=0,
                                       master_seed=master_seed, weight_deltas=weight_deltas)
                per_size_recomputed[s].append(r.kl.mean(dim=-1).cpu())
                del imp_s, r
        del imp_all, sub_all
        _free(device)
    ref = torch.cat(per_size[sizes[-1]])
    m5 = {s: float((torch.cat(per_size[s]) - ref).abs().max()) for s in sizes}
    ref_r = torch.cat(per_size_recomputed[sizes[-1]])
    m5_r = {s: float((torch.cat(per_size_recomputed[s]) - ref_r).abs().max()) for s in sizes}
    checks.append(Check("M5", max(m5.values()) < tol_eq, f"sub-batch sizes {sizes}, g fixed at chunk {IMPORTANCE_CHUNK} and sliced: max |dKL_b| = {max(m5.values()):.2e} (tol {tol_eq:.0e}); per size against {sizes[-1]}: {m5}"))
    checks.append(Check("M5", None, f"sub-batch sizes {sizes}, g recomputed at each size (reported): max |dKL_b| = {max(m5_r.values()):.2e}; per size: {m5_r}"))

    # M6: the donor-free ends against the references (bitwise masks, divergence, and the P4 digests)
    def run_masks(masks: dict[str, Tensor], deltas: dict[str, Tensor] | None, permitted: bool = True, keep_logits: bool = False):
        fr = masked_forward(model, batch, masks, g, permitted=permitted, precision=precision, delta_masks=deltas,
                            weight_deltas=weight_deltas if deltas is not None else None)
        kl = per_position_kl(imp.target_logits, fr.logits)
        digest = level3_hex(fr.fp, idx)
        if not keep_logits:
            fr.logits = None  # type: ignore[assignment]
        return fr, kl, digest

    def ref_masks(name: str, draw: int = 0):
        return build_condition_masks(CONDITION_BY_NAME[name], g, model.module_to_c, draw=draw, subbatch_index=0, master_seed=master_seed)

    def digests_equal(da: dict[str, Any], db: dict[str, Any]) -> bool:
        return da["F"] == db["F"] and da["phi"] == db["phi"] and da["H"] == db["H"] and da["Hd"] == db["Hd"]

    B, T = batch.shape
    dtype = g[keys[0]].dtype
    zeros_src = {k: torch.zeros(model.module_to_c[k], dtype=dtype, device=device) for k in keys}
    ones_src = {k: torch.ones(model.module_to_c[k], dtype=dtype, device=device) for k in keys}

    # M6a: union, J = empty, r = 0 -> importances-as-masks
    m_union0 = {k: apply_binary_source(g[k], zeros_src[k]) for k in keys}
    m_ref, _ = ref_masks("importances")
    fr_u, kl_u, d_u = run_masks(m_union0, None)
    fr_r, kl_r, d_r = run_masks(m_ref, None)
    ok = all(_bitwise(m_union0[k], m_ref[k]) for k in keys) and _bitwise(kl_u, kl_r) and digests_equal(d_u, d_r)
    checks.append(Check("M6a", ok, f"union(empty, r=0) vs importances-as-masks: masks bitwise, KL bitwise (max |d|={_maxdiff(kl_u, kl_r):.1e}), digests equal={digests_equal(d_u, d_r)} (F={d_u['F']})"))
    del fr_u, fr_r, kl_u, m_union0, m_ref
    _free(device)

    # M6b: soft erase, J = empty, r = 1, residual excluded -> unmasked
    m_erase1 = {k: apply_binary_source(g[k], ones_src[k]) for k in keys}
    m_ref, _ = ref_masks("unmasked")
    fr_e, kl_e, d_e = run_masks(m_erase1, None)
    fr_r, kl_r, d_r = run_masks(m_ref, None)
    ok = all(_bitwise(m_erase1[k], m_ref[k]) for k in keys) and _bitwise(kl_e, kl_r) and digests_equal(d_e, d_r)
    kl_unmasked_mean = float(kl_e.mean())
    checks.append(Check("M6b", ok, f"erase(empty, r=1) vs unmasked: masks bitwise (all ones), KL bitwise, digests equal={digests_equal(d_e, d_r)}; mean KL {kl_unmasked_mean:.3e}; n_ne_one = {sum(fr_e.n_ne_one.values())} (must be 0)"))
    ok_counts = sum(fr_e.n_ne_one.values()) == 0
    checks[-1].passed = bool(checks[-1].passed and ok_counts)
    del fr_e, fr_r, kl_e, kl_r, m_ref
    _free(device)

    # M6c: union, J = empty, uniform, draw k -> the residual-excluded stochastic reference from the same u
    u, _u_delta = uniform_background((master_seed, "u", 0, 0), model.module_to_c, B, T, dtype=dtype, device=device)
    m_union_u = {k: apply_source(g[k], torch.where(zeros_src[k].bool(), 1, u[k])) for k in keys}
    m_ref, _ = ref_masks("stochastic", draw=0)
    fr_c, kl_c, d_c = run_masks(m_union_u, None)
    fr_r, kl_r, d_r = run_masks(m_ref, None)
    ok = all(_bitwise(m_union_u[k], m_ref[k]) for k in keys) and _bitwise(kl_c, kl_r) and digests_equal(d_c, d_r)
    checks.append(Check("M6c", ok, f"union(empty, uniform k=0) vs stochastic reference: masks bitwise, KL bitwise, digests equal={digests_equal(d_c, d_r)}"))
    del u, m_union_u, m_ref, fr_c, fr_r, kl_c, kl_r
    _free(device)

    # M6d: soft erase, J = empty, r = 1, residual included -> the target itself
    deltas_ones = {k: torch.ones((B, T), dtype=dtype, device=device) for k in keys}
    fr_d, kl_d, d_d = run_masks(m_erase1, deltas_ones, keep_logits=True)
    max_logit = _maxdiff(fr_d.logits, imp.target_logits)
    kl_d_mean = float(kl_d.mean())
    ratio = kl_unmasked_mean / max(abs(kl_d_mean), 1e-12)
    if precision == "fp32":
        m6d_ok = max_logit < 1e-3 and kl_d_mean < tol_eq and ratio >= 100
        m6d_note = f"max |logits - target| = {max_logit:.2e} (< 1e-3); mean KL = {kl_d_mean:.2e} (< {tol_eq:.0e}); unmasked/this = {ratio:.1f} (>= 100)"
    else:  # bf16 logits have a spacing near 0.06 at magnitude 10: only the divergence clause gates
        m6d_ok = kl_d_mean < tol_eq
        m6d_note = f"mean KL = {kl_d_mean:.2e} (< {tol_eq:.0e}, the gate in bf16); reported: max |logits - target| = {max_logit:.2e}, unmasked/this = {ratio:.1f}"
    m_ref, d_ref = ref_masks("unmasked_delta")
    _, _, d_r = run_masks(m_ref, d_ref)
    m6d_note += f"; digests equal to unmasked_delta={digests_equal(d_d, d_r)}; residual digests present={d_d['Hd'] is not None}"
    checks.append(Check("M6d", m6d_ok and digests_equal(d_d, d_r), m6d_note))
    del fr_d, kl_d, deltas_ones, m_erase1, m_ref, d_ref
    _free(device)

    # M6e: rounded-own-g union, J = empty, tau = 0.1 -> the rounded-0.1 reference
    m_rog = {k: torch.maximum(rounded_mask(g[k], 0.1), zeros_src[k].view(1, 1, -1).expand_as(g[k])) for k in keys}
    m_ref, _ = ref_masks("rounded_0.1")
    fr_g, kl_g, d_g = run_masks(m_rog, None, permitted=False)
    fr_r, kl_r, d_r = run_masks(m_ref, None, permitted=False)
    ok = all(_bitwise(m_rog[k], m_ref[k]) for k in keys) and _bitwise(kl_g, kl_r) and digests_equal(d_g, d_r)
    checks.append(Check("M6e", ok, f"rounded-own-g union(empty, tau=0.1) vs rounded-0.1: masks bitwise, KL bitwise, digests equal={digests_equal(d_g, d_r)}"))
    del m_rog, m_ref, fr_g, fr_r, kl_g, kl_r
    _free(device)
    del imp
    _free(device)

    # G1 and G2 on the first 8 sequences, in this precision
    checks += run_fingerprint_checks(model, ids[: min(8, n)], precision=precision, weight_deltas=weight_deltas, master_seed=master_seed, n_draws=n_draws, log=log)

    # G3: from the references' marker
    checks += check_g3(store.extra, n_draws=n_draws, n_subbatches=store.n_subbatches)

    # G3b: the residual identity on the first sub-batch of the residual test cells, both precisions (bf16 needs CUDA), draws 0 to 3
    precisions = ("fp32", "bf16") if str(device).startswith("cuda") else ("fp32",)
    for p_ in precisions:
        checks.append(check_g3b(model, ids[: min(32, n)], precision=p_, weight_deltas=weight_deltas, master_seed=master_seed, log=log))
        _free(device)

    # the cross-entropy diagnostic of the matched-shape check 6 rerun's "pass, localize", on one batch of 16
    checks += ce_diagnostic(model, ids[: min(16, n)], precision=precision, weight_deltas=weight_deltas, master_seed=master_seed, log=log)
    _free(device)

    # M12: the reference orderings (reported at this scale)
    for c in check_ordering(df):
        checks.append(Check("M12", None, f"{c['item']}: {c['value']} -> {'holds' if c['pass'] else ('reported' if c['pass'] is None else 'VIOLATED')}"))

    # M13: bf16 against float32 (CUDA only), with G1 and G2 again in float32
    if precision == "bf16":
        checks += run_m13(model, ids, df, run=run, subbatch=subbatch, n_draws=n_draws, master_seed=master_seed, set_name=set_name,
                          set_hash=set_hash, hashes=hashes, out_dir=out_dir.with_name(out_dir.name + "_fp32"), weight_deltas=weight_deltas, log=log)

    log(f"[smoke] peak RSS {peak_rss_gb():.2f} GB")
    return checks


# ----------------------------------------------------------------------------- the fingerprint's validation


def run_fingerprint_checks(model: Any, ids8: np.ndarray, *, precision: str, weight_deltas: dict[str, Tensor], master_seed: int, n_draws: int, log: Any) -> list[Check]:
    """G1: for every reference cell on these sequences, phi_b, every h_b^(l) (and hd), and F computed on the model's
    device equal those computed on CPU from .cpu() copies of the same masks, bitwise; also for bf16 casts of the same
    masks (g, hence every mask, is float32 in both precisions, so the bf16 branch is exercised on casts). G2: the
    SHA-256 and the fingerprint give identical all-pairs equality matrices over the same cells."""
    device = next(model.parameters()).device
    batch = torch.from_numpy(np.ascontiguousarray(ids8)).long().to(device)
    imp = compute_importances(model, batch, precision=precision)
    idx = np.arange(batch.shape[0])
    cells = masked_cells(n_draws)
    shas: dict[str, str] = {}
    digests: dict[str, str] = {}
    g1_fail: list[str] = []
    g1_fail_bf16: list[str] = []
    t0 = time.time()
    t_sha = 0.0
    for cond, k in cells:
        name = cell_key(cond, k)
        masks, deltas = build_condition_masks(cond, imp.g, model.module_to_c, draw=k, subbatch_index=0, master_seed=master_seed)
        t1 = time.time()
        fr = masked_forward(model, batch, masks, imp.g, permitted=cond.permitted, precision=precision, delta_masks=deltas,
                            weight_deltas=weight_deltas if deltas is not None else None, do_sha256=True)
        t_sha += time.time() - t1
        shas[name] = fr.sha256
        dev_hex = level3_hex(fr.fp, idx)
        digests[name] = dev_hex["F"]
        cpu_fp = fingerprint({kk: v.detach().cpu() for kk, v in masks.items()}, {kk: v.detach().cpu() for kk, v in deltas.items()} if deltas is not None else None)
        cpu_hex = level3_hex(cpu_fp, idx)
        same = (torch.equal(fr.fp.phi.cpu(), cpu_fp.phi) and all(torch.equal(fr.fp.h[kk].cpu(), cpu_fp.h[kk]) for kk in fr.fp.h)
                and ((fr.fp.hd is None and cpu_fp.hd is None) or all(torch.equal(fr.fp.hd[kk].cpu(), cpu_fp.hd[kk]) for kk in fr.fp.hd)) and dev_hex == cpu_hex)
        if not same:
            g1_fail.append(name)
        # the bf16 branch, on casts of the same masks
        m_bf = {kk: v.to(torch.bfloat16) for kk, v in masks.items()}
        d_bf = {kk: v.to(torch.bfloat16) for kk, v in deltas.items()} if deltas is not None else None
        fp_dev_bf = fingerprint(m_bf, d_bf)
        fp_cpu_bf = fingerprint({kk: v.cpu() for kk, v in m_bf.items()}, {kk: v.cpu() for kk, v in d_bf.items()} if d_bf is not None else None)
        if not (torch.equal(fp_dev_bf.phi.cpu(), fp_cpu_bf.phi) and level3_hex(fp_dev_bf, idx) == level3_hex(fp_cpu_bf, idx) and fp_dev_bf.dtype_code == 16):
            g1_fail_bf16.append(name)
        del fr, masks, deltas, cpu_fp, m_bf, d_bf, fp_dev_bf, fp_cpu_bf
        _free(str(device))
    names = [cell_key(c, k) for c, k in cells]
    eq_sha = [[shas[a] == shas[b] for b in names] for a in names]
    eq_fp = [[digests[a] == digests[b] for b in names] for a in names]
    n_equal_pairs = sum(eq_sha[i][j] for i in range(len(names)) for j in range(i + 1, len(names)))
    out = [Check("G1", not g1_fail and not g1_fail_bf16,
                 f"{precision}: {len(names)} cells on {batch.shape[0]} sequences of the device {device.type} against CPU: phi, h, hd, F bitwise equal for all "
                 f"({len(names) - len(g1_fail)}/{len(names)} float32 masks; {len(names) - len(g1_fail_bf16)}/{len(names)} bf16 casts); failures {g1_fail + g1_fail_bf16 or 'none'}"),
           Check("G2", eq_sha == eq_fp,
                 f"{precision}: SHA-256 and fingerprint all-pairs equality matrices over {len(names)} cells identical={eq_sha == eq_fp}; equal pairs {n_equal_pairs} "
                 f"(diagonal excluded); SHA time {t_sha / len(names):.2f} s per cell at B={batch.shape[0]} incl. the forward; total {time.time() - t0:.1f} s")]
    del imp, batch
    _free(str(device))
    return out


def check_g3(extra: dict[str, Any], *, n_draws: int, n_subbatches: int) -> list[Check]:
    """G3 from the references' marker: pairwise distinct `mask_fp_cell` across the masked conditions and their draws
    (the target has no mask); level 4 consistent with the per-sub-batch records; and the residual identity: for the
    same draw and sub-batch, the component digests of stochastic, stochastic_delta, stochastic_delta1 are equal for
    every module and their residual digests differ."""
    cells = extra["mask_fp_cell"]
    names = sorted(cells)
    values = [cells[nm] for nm in names]
    dup = {v for v in values if values.count(v) > 1}
    distinct = len(set(values)) == len(values)
    l4_ok = all(sum_hex(list(extra["mask_fp_subbatch"][nm].values())) == cells[nm] and len(extra["mask_fp_subbatch"][nm]) == n_subbatches for nm in names)
    out = [Check("G3", distinct and l4_ok, f"mask_fp_cell pairwise distinct across {len(names)} masked cells: {distinct} (duplicates {sorted(dup) or 'none'}); "
                                            f"level 4 = sum of {n_subbatches} sub-batch digests for every cell: {l4_ok}")]
    ok = True
    n_checked = 0
    for k in range(n_draws):
        for i in range(n_subbatches):
            recs = {nm: extra["mask_fp_modules_subbatch"][f"{nm}/k{k}"][str(i)] for nm in ("stochastic", "stochastic_delta", "stochastic_delta1")}
            same_h = recs["stochastic"]["H"] == recs["stochastic_delta"]["H"] == recs["stochastic_delta1"]["H"]
            hd_u, hd_1 = recs["stochastic_delta"]["Hd"], recs["stochastic_delta1"]["Hd"]
            residual_differ = hd_u is not None and hd_1 is not None and all(hd_u[m] != hd_1[m] for m in hd_u) and recs["stochastic"]["Hd"] is None
            f_distinct = len({extra["mask_fp_subbatch"][f"{nm}/k{k}"][str(i)] for nm in recs}) == 3
            ok = ok and same_h and residual_differ and f_distinct
            n_checked += 1
    out.append(Check("G3", ok, f"residual identity on {n_checked} (draw, sub-batch) pairs: component digests H equal across stochastic, stochastic_delta, "
                               f"stochastic_delta1 for every module, residual digests Hd differ between the two included cells, the three F_i distinct: {ok}"))
    counts = extra.get("n_ne_one_cell_total", {})
    out.append(Check("G3", None, f"n(m != 1) per cell: unmasked {counts.get('unmasked')}, unmasked_delta {counts.get('unmasked_delta')}, importances {counts.get('importances')}, "
                                 f"zero_all {counts.get('zero_all')}; n(m != g): importances {extra.get('n_ne_g_cell_total', {}).get('importances')}, unmasked {extra.get('n_ne_g_cell_total', {}).get('unmasked')}"))
    return out


def check_g3b(model: Any, ids32: np.ndarray, *, precision: str, weight_deltas: dict[str, Tensor], master_seed: int, log: Any) -> Check:
    """G3b: the first sub-batch of the residual test cells, exactly as they run (sub-batch 32, sub-batch index 0, master seed 0), draws 0 to 3,
    through the forward with the fingerprint on: the residual identity there."""
    device = next(model.parameters()).device
    batch = torch.from_numpy(np.ascontiguousarray(ids32)).long().to(device)
    imp = compute_importances(model, batch, precision=precision)
    idx = np.arange(batch.shape[0])
    ok = True
    t0 = time.time()
    per_draw = []
    for k in range(4):
        d: dict[str, dict[str, Any]] = {}
        for nm in ("stochastic", "stochastic_delta", "stochastic_delta1"):
            cond = CONDITION_BY_NAME[nm]
            masks, deltas = build_condition_masks(cond, imp.g, model.module_to_c, draw=k, subbatch_index=0, master_seed=master_seed)
            fr = masked_forward(model, batch, masks, imp.g, permitted=True, precision=precision, delta_masks=deltas, weight_deltas=weight_deltas if deltas is not None else None)
            d[nm] = level3_hex(fr.fp, idx)
            del fr, masks, deltas
        same_h = d["stochastic"]["H"] == d["stochastic_delta"]["H"] == d["stochastic_delta1"]["H"]
        hd_differ = all(d["stochastic_delta"]["Hd"][m] != d["stochastic_delta1"]["Hd"][m] for m in d["stochastic_delta"]["Hd"]) and d["stochastic"]["Hd"] is None
        f_distinct = len({d[nm]["F"] for nm in d}) == 3
        per_draw.append(same_h and hd_differ and f_distinct)
        ok = ok and per_draw[-1]
        _free(str(device))
    del imp, batch
    _free(str(device))
    return Check("G3b", ok, f"{precision}, first sub-batch of {ids32.shape[0]} (the residual test cells, sub-batch index 0), draws 0-3 through the forward: H equal across the three "
                            f"stochastic cells, Hd differ, F distinct, per draw {per_draw}; {time.time() - t0:.1f} s")


def ce_diagnostic(model: Any, ids16: np.ndarray, *, precision: str, weight_deltas: dict[str, Tensor], master_seed: int, log: Any) -> list[Check]:
    """Added after the matched-shape bf16 rerun of check 6 returned "pass, localize": on one batch, the authors' `ce_vs_labels` (verbatim from
    CEandKLLosses._calc_ce_and_kl_losses, under the autocast their update runs in) and our `per_sequence_ce(...).mean()`
    on the same logits tensor, both against a float64 reference from that tensor; for the target's logits, the
    importances-as-masks logits, and their difference (the gated quantity); the same for the KL against
    `calc_kl_divergence_lm`. Variants of theirs: without autocast, and with the logits cast to float32 first."""
    import einops
    import torch.nn.functional as F

    from param_decomp.utils.general_utils import calc_kl_divergence_lm

    device = next(model.parameters()).device
    batch = torch.from_numpy(np.ascontiguousarray(ids16)).long().to(device)
    imp = compute_importances(model, batch, precision=precision, chunk=max(batch.shape[0], 1) if batch.shape[0] < IMPORTANCE_CHUNK else IMPORTANCE_CHUNK)
    res = evaluate_condition(model, CONDITION_BY_NAME["importances"], batch, imp, draw=0, subbatch_index=0, master_seed=master_seed, weight_deltas=weight_deltas, keep_logits=True)
    logits = {"target": imp.target_logits, "importances": res.logits}

    def theirs_ce(lg: Tensor, autocast: bool, cast32: bool) -> float:
        masked_batch = batch.clone()
        masked_batch[:, 0] = -100
        flat_masked_batch = masked_batch.flatten()
        flat_logits = einops.rearrange(lg.float() if cast32 else lg, "b seq_len vocab -> (b seq_len) vocab")
        ctx = autocast_context(device, precision) if autocast else torch.autocast(device_type=device.type, enabled=False)
        with torch.no_grad(), ctx:
            return F.cross_entropy(flat_logits[:-1], flat_masked_batch[1:], ignore_index=-100).item()

    def ours_ce(lg: Tensor) -> float:
        return float(per_sequence_ce(lg, batch).mean())

    def ref_ce(lg: Tensor) -> float:
        lp = torch.log_softmax(lg.double(), dim=-1)
        nll = -lp[:, :-1].gather(-1, batch[:, 1:].unsqueeze(-1)).squeeze(-1)
        return float(nll.mean())

    def theirs_kl(lg: Tensor, autocast: bool) -> float:
        ctx = autocast_context(device, precision) if autocast else torch.autocast(device_type=device.type, enabled=False)
        with torch.no_grad(), ctx:
            return float(calc_kl_divergence_lm(pred=lg, target=imp.target_logits))

    def ours_kl(lg: Tensor) -> float:
        return float(per_position_kl(imp.target_logits, lg).mean())

    def ref_kl(lg: Tensor) -> float:
        lp, lq = torch.log_softmax(imp.target_logits.double(), -1), torch.log_softmax(lg.double(), -1)
        return float((lp.exp() * (lp - lq)).sum(-1).mean())

    out: list[Check] = []
    rows: dict[str, dict[str, float]] = {}
    for name, lg in logits.items():
        rows[name] = {"ref64": ref_ce(lg), "theirs_autocast": theirs_ce(lg, True, False), "theirs_no_autocast": theirs_ce(lg, False, False),
                      "theirs_autocast_cast32": theirs_ce(lg, True, True), "ours": ours_ce(lg), "logits_dtype": str(lg.dtype)}
    diff = {k: rows["importances"][k] - rows["target"][k] for k in ("ref64", "theirs_autocast", "theirs_no_autocast", "theirs_autocast_cast32", "ours")}
    for name, r in list(rows.items()) + [("importances - target (the gated ce difference)", diff)]:
        ref = r["ref64"]
        closer = "ours" if abs(r["ours"] - ref) < abs(r["theirs_autocast"] - ref) else "theirs"
        out.append(Check("CE-DIAG", None, f"{precision}, B={batch.shape[0]}, {name} (logits {r.get('logits_dtype', rows['target']['logits_dtype'])}): ref64 {ref:.7f}; "
                                          f"theirs(autocast) {r['theirs_autocast']:.7f} (|d|={abs(r['theirs_autocast'] - ref):.2e}); ours {r['ours']:.7f} (|d|={abs(r['ours'] - ref):.2e}); "
                                          f"theirs - ours = {r['theirs_autocast'] - r['ours']:+.2e}; closer to ref64: {closer}; "
                                          f"theirs(no autocast) |d|={abs(r['theirs_no_autocast'] - ref):.2e}; theirs(autocast, logits cast to fp32 first) |d|={abs(r['theirs_autocast_cast32'] - ref):.2e}"))
    kr = ref_kl(res.logits)
    kt, kt_na, ko = theirs_kl(res.logits, True), theirs_kl(res.logits, False), ours_kl(res.logits)
    out.append(Check("CE-DIAG", None, f"{precision}, B={batch.shape[0]}, KL(target || importances): ref64 {kr:.8f}; theirs(autocast) {kt:.8f} (|d|={abs(kt - kr):.2e}); "
                                      f"ours {ko:.8f} (|d|={abs(ko - kr):.2e}); theirs - ours = {kt - ko:+.2e}; theirs(no autocast) |d|={abs(kt_na - kr):.2e}"))
    del res, imp, logits, batch
    _free(str(device))
    return out


def run_m13(model: Any, ids: np.ndarray, df_bf16: Any, *, run: str, subbatch: int, n_draws: int, master_seed: int, set_name: str,
            set_hash: str, hashes: dict[str, str], out_dir: Path, weight_deltas: dict[str, Tensor], log: Any) -> list[Check]:
    """bf16 autocast against float32 on the references: differences between conditions within
    0.01 nats; the number of thresholded entries that flip between bf16 and float32 g. Then G1 and G2 in float32."""
    checks: list[Check] = []
    device = next(model.parameters()).device
    n = ids.shape[0]
    store = run_references(model, ids, job=f"smoke_{run}_fp32_n{n}", run=run, out_dir=out_dir, precision="fp32", subbatch=subbatch,
                           n_draws=n_draws, master_seed=master_seed, set_name=set_name, set_hash=set_hash, checkpoint_hashes=hashes, conditions=ALL_CONDITIONS, resume=False, log=log)
    df_fp32 = store.table()
    tb, tf = condition_table(df_bf16).set_index("condition"), condition_table(df_fp32).set_index("condition")
    worst = 0.0
    lines = []
    for col in ("ce_mean", "kl_mean"):
        for a in tb.index:
            for b in tb.index:
                if a >= b or a == "zero_all" or b == "zero_all" or a == "random_illegal" or b == "random_illegal":
                    continue
                d = abs((tb.loc[a, col] - tb.loc[b, col]) - (tf.loc[a, col] - tf.loc[b, col]))
                worst = max(worst, d)
        lines.append(f"{col}: bf16 {dict((k, round(float(v), 4)) for k, v in tb[col].items())} fp32 {dict((k, round(float(v), 4)) for k, v in tf[col].items())}")
    checks.append(Check("M13", worst <= 0.01, f"max |(a-b)_bf16 - (a-b)_fp32| over condition pairs (zero-all and random-illegal excluded) = {worst:.4f} (<= 0.01)"))
    for line in lines:
        checks.append(Check("M13", None, line))
    # flip counts
    flips = {"0.0": 0, "0.1": 0, "0.5": 0}
    total = 0
    for start in range(0, n, subbatch):
        batch = torch.from_numpy(np.ascontiguousarray(ids[start : start + subbatch])).long().to(device)
        gb = compute_importances(model, batch, precision="bf16").g
        gf = compute_importances(model, batch, precision="fp32").g
        for k in gb:
            total += gb[k].numel()
            for thr in flips:
                flips[thr] += int(((gb[k].float() > float(thr)) != (gf[k] > float(thr))).sum())
        del gb, gf
        _free(device)
    checks.append(Check("M13", None, f"thresholded entries flipping between bf16 and fp32 g out of {total}: {flips}"))
    checks += run_fingerprint_checks(model, ids[: min(8, n)], precision="fp32", weight_deltas=weight_deltas, master_seed=master_seed, n_draws=n_draws, log=log)
    checks += check_g3(store.extra, n_draws=n_draws, n_subbatches=store.n_subbatches)
    return checks


def format_checks(checks: list[Check]) -> str:
    lines = []
    for c in checks:
        status = "PASS" if c.passed is True else ("FAIL" if c.passed is False else "----")
        lines.append(f"[{status}] {c.id}: {c.detail}")
    return "\n".join(lines)
