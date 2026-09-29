"""The identities on the real model that need donors: M7, M8, M9, M10b, M11, M14, M15,
M16, H1, H2, H3 (M10a is asserted throughout by `masked_forward`). First on the SimpleStories decomposition with the
stand-in pools of `dry_sets`, then on the paper's model on the 40 GB card, all with the fingerprint on.

The chains run in bf16 through `run_cells`: one hard-zero chain over the whole evaluation set (D_unif donors,
tau = 0.1, Delta included, draw 0, every rung 0 to 8; rungs 0, 4, 8 for H1, every rung for M10b and M11) and one
union chain (tau = 0.1, r = 0, draw 0) for M11 and M14, with the reference cells they compare against. H1's rung-0
clause with Delta included (divergence from the target below 1e-5) holds only in float32, so it is
checked on one float32 sub-batch; in bf16 the clause gates at 1e-3. These chains are cells of verdict curves 1 and
5 at one draw: the output prints only what the identities need (the digests, the counts, the mask checks, and the
divergences of the two ends); the intermediate rungs' divergences stay on the volume, unread.
"""

from __future__ import annotations

import json
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np
import torch
from torch import Tensor

from vpd_audit import env
from vpd_audit.cells import BuiltSource, Cell, run_cells
from vpd_audit.constants import IMPORTANCE_CHUNK, SEQ_LEN
from vpd_audit.fingerprint import level3_hex
from vpd_audit.importances import compute_importances, module_keys
from vpd_audit.masks import first_touched, hard_zero_masks, masked_forward
from vpd_audit.metrics import per_position_kl
from vpd_audit.reference import CONDITION_BY_NAME
from vpd_audit.sources import (
    INTERMEDIATE_RUNGS,
    SUB_RUNGS,
    Cache,
    code_specific_source,
    donor_set,
    family_masks,
    n_on,
    rho_tensors,
    source_hash,
    sub_rung_sets,
    union_source,
)


@dataclass
class Check:
    id: str
    passed: bool | None
    detail: str


def _fmt(checks: list[Check]) -> str:
    return "\n".join(f"[{'PASS' if c.passed is True else ('FAIL' if c.passed is False else '----')}] {c.id}: {c.detail}" for c in checks)


@dataclass
class IdentityInputs:
    run: str  # the decomposition: main | control | simplestories
    cache_tag: str  # the caches' run suffix: main | control | dry_simplestories
    eval_set: str  # E | E_dry
    pool_unif: str  # D_unif | D_unif_dry
    pool_code: str  # D_code | D_code_dry
    pool_prose: str  # D_prose | D_prose_dry
    e_lab_other: str  # E_lab_other | E_lab_dry
    precision: str  # bf16 | fp32
    subbatch: int
    chunk: int
    e_lab_other_subbatches: int = 4


def _chain_cells(run: str, eval_set: str, pool: str) -> tuple[list[Cell], list[str]]:
    cells: list[Cell] = []
    for r in ("1", "2", "3", "4", "5", "6", "7", "8"):
        cells.append(Cell(run, "hard_zero", eval_set, pool, 0.1, "ones", "included", 0, r, "none", 1))
        cells.append(Cell(run, "union", eval_set, pool, 0.1, "r0", "excluded", 0, r, "none", 1))
    refs = ["target", "unmasked", "unmasked_delta", "importances", "zero_all"]
    for name in refs:
        c = CONDITION_BY_NAME[name]
        cells.append(Cell(run, "reference", eval_set, None, None, "none", c.delta, 0, "0", "none", 1, condition=name))
    return cells, refs


def run_identities(inputs: IdentityInputs, *, device: str, out_dir: Path, master_seed: int = 0, log: Any = print) -> list[Check]:
    from vpd_audit.artifacts import checkpoint_hashes, load_component_model
    from vpd_audit.data import load_set
    from vpd_audit.donors import load_prose_named_and_f_code

    torch.use_deterministic_algorithms(True, warn_only=True)
    checks: list[Check] = []
    t_all = time.time()
    model = load_component_model(inputs.run, device)
    keys = module_keys(model)
    module_to_c = {k: model.module_to_c[k] for k in keys}
    hashes = checkpoint_hashes(inputs.run)
    weight_deltas = model.calc_weight_deltas()
    ids, _, rec = load_set(inputs.eval_set)
    # caches are named <pool>_<run> (donors.build_cache); the prose-named and f_code files by the caches' tag (<pool suffix>_<run> without "D_code_")
    caches = {f"{p}_{inputs.run}": Cache.load(f"{p}_{inputs.run}") for p in (inputs.pool_unif, inputs.pool_code, inputs.pool_prose)}
    cache_unif, cache_code, cache_prose = (caches[f"{p}_{inputs.run}"] for p in (inputs.pool_unif, inputs.pool_code, inputs.pool_prose))
    alive = np.load(env.CACHE_DIR / "donors" / f"alive_{inputs.pool_unif}_{inputs.run}.npy")
    prose_named, f_code, _ = load_prose_named_and_f_code(inputs.cache_tag)
    offsets = cache_unif.offsets
    log(f"[identities] {inputs.run}: eval {inputs.eval_set} ({ids.shape[0]} seqs), pools {cache_unif.n_sequences}/{cache_code.n_sequences}/{cache_prose.n_sequences}, alive {int(alive.sum())}, {inputs.precision}")

    # ------------------------------------------------------------------ M7: one donor position at tau = 0 and 0.5
    ds1 = donor_set(inputs.pool_unif, cache_unif.n_sequences, 0, "1", master_seed)
    p = ds1.positions[0]
    rho0, rho5 = union_source(cache_unif, ds1.positions, 0.0), union_source(cache_unif, ds1.positions, 0.5)
    nnz_p = int(cache_unif.indptr[p + 1] - cache_unif.indptr[p])
    n_above_half = int((cache_unif.values[cache_unif.indptr[p] : cache_unif.indptr[p + 1]] > 0.5).sum())
    b1 = torch.from_numpy(np.ascontiguousarray(ids[:1])).long().to(device)
    imp1 = compute_importances(model, b1, precision=inputs.precision, chunk=min(inputs.chunk, 1) if inputs.chunk < 1 else inputs.chunk)
    m7_masks, _, _ = family_masks("union", imp1.g, rho_tensors(rho0, module_to_c, imp1.g[keys[0]].dtype, device, offsets), background="r0", delta="excluded")
    formula_ok = all(torch.equal(m7_masks[k], imp1.g[k] + (1 - imp1.g[k]) * torch.from_numpy(rho0[offsets[k] : offsets[k] + module_to_c[k]].astype(np.float32)).to(device=device, dtype=imp1.g[k].dtype)) for k in keys)
    checks.append(Check("M7", int(rho0.sum()) == nnz_p and int(rho5.sum()) == n_above_half and n_above_half < nnz_p and formula_ok,
                        f"donor position {p} (seq {p // SEQ_LEN}, t {p % SEQ_LEN}) of {inputs.pool_unif}: n_on at tau 0 = {int(rho0.sum())} (= the position's count of g > 0: {nnz_p}); at 0.5 = {int(rho5.sum())} (strictly fewer); "
                        f"mask = g + (1 - g) rho entrywise on sequence 0 of {inputs.eval_set}: {formula_ok}"))

    # ------------------------------------------------------------------ M8: self-union on five sequences
    n8 = min(5, ids.shape[0])
    b8 = torch.from_numpy(np.ascontiguousarray(ids[:n8])).long().to(device)
    imp8 = compute_importances(model, b8, precision=inputs.precision, chunk=inputs.chunk)
    m8_ok = True
    m8_kl = []
    for b in range(n8):
        G_b = torch.cat([imp8.g[k][b].reshape(SEQ_LEN, -1) for k in keys], dim=1).float().cpu().numpy()
        cache_b = Cache.from_dense(G_b, module_to_c)
        rho_b = union_source(cache_b, np.arange(SEQ_LEN), 0.1)
        g_b = {k: imp8.g[k][b : b + 1] for k in keys}
        masks_b, _, _ = family_masks("union", g_b, rho_tensors(rho_b, module_to_c, g_b[keys[0]].dtype, device, offsets), background="r0", delta="excluded")
        expect = {k: torch.where(g_b[k] > 0.1, torch.ones_like(g_b[k]), g_b[k]) for k in keys}
        # the sequence's own union names every subcomponent it uses anywhere above tau; at positions where g <= tau the mask is 1 if the subcomponent is used elsewhere in the sequence
        named = {k: torch.from_numpy(rho_b[offsets[k] : offsets[k] + module_to_c[k]]).to(device) for k in keys}
        expect2 = {k: torch.where(named[k].view(1, 1, -1), torch.ones_like(g_b[k]), g_b[k]) for k in keys}
        m8_ok = m8_ok and all(torch.equal(masks_b[k], expect2[k]) for k in keys) and all(bool((masks_b[k] >= expect[k]).all()) for k in keys)
        fr = masked_forward(model, b8[b : b + 1], masks_b, g_b, permitted=True, precision=inputs.precision)
        m8_kl.append(float(per_position_kl(imp8.target_logits[b : b + 1], fr.logits).mean()))
        del fr
    checks.append(Check("M8", m8_ok, f"self-union on {n8} sequences at tau 0.1: mask bitwise 1 on every subcomponent the sequence itself uses above tau (anywhere in the sequence) and g elsewhere: {m8_ok}; "
                                     f"divergence recorded, no expectation: {[round(x, 4) for x in m8_kl]}"))
    del imp8
    if str(device).startswith("cuda"):
        torch.cuda.empty_cache()

    # ------------------------------------------------------------------ M9: zero position 100 of sequence 0 only, float32
    n9 = min(4, ids.shape[0])
    b9 = torch.from_numpy(np.ascontiguousarray(ids[:n9])).long().to(device)
    imp9 = compute_importances(model, b9, precision="fp32", chunk=inputs.chunk)
    ones9 = {k: torch.ones_like(imp9.g[k]) for k in keys}
    zeroed = {k: v.clone() for k, v in ones9.items()}
    for k in keys:
        zeroed[k][0, 100, :] = 0.0
    fr_ones = masked_forward(model, b9, ones9, imp9.g, permitted=True, precision="fp32")
    fr_zero = masked_forward(model, b9, zeroed, imp9.g, permitted=False, precision="fp32")
    d = (fr_ones.logits - fr_zero.logits).abs()
    prefix_ok = float(d[0, :100].max()) < 1e-5
    at100 = float(d[0, 100].max()) > 0
    others_ok = bool(torch.equal(fr_ones.logits[1:], fr_zero.logits[1:]))
    checks.append(Check("M9", prefix_ok and at100 and others_ok, f"float32, {n9} sequences: zeroing all 24 masks at position 100 of sequence 0: positions 0-99 max |dlogit| {float(d[0, :100].max()):.2e} (< 1e-5), "
                                                                f"position 100 changed by {float(d[0, 100].max()):.3f}, later positions max {float(d[0, 101:].max()):.3f}, every other sequence bitwise unchanged: {others_ok}"))
    del imp9, fr_ones, fr_zero, ones9, zeroed
    if str(device).startswith("cuda"):
        torch.cuda.empty_cache()

    # ------------------------------------------------------------------ the two chains over the whole evaluation set (bf16 or the run's precision)
    cells, ref_names = _chain_cells(inputs.run, inputs.eval_set, inputs.pool_unif)
    sources: dict[str, BuiltSource] = {}
    rho_by_rung: dict[str, np.ndarray] = {}
    for c in cells:
        if c.family == "reference":
            sources[c.name] = BuiltSource(None, {"kind": "reference"})
            continue
        ds = donor_set(inputs.pool_unif, cache_unif.n_sequences, 0, c.rung, master_seed)
        rho = union_source(cache_unif, ds.positions, 0.1)
        rho_by_rung[c.rung] = rho
        sources[c.name] = BuiltSource(rho, {"family": c.family, "pool": inputs.pool_unif, "tau": 0.1, "draw": 0, "rung": c.rung, "donor_unit": ds.unit, "donor_size": ds.size,
                                            "seed_tuple": json.dumps(list(ds.seed_tuple)) if ds.seed_tuple else "", "named_n_on": n_on(rho, module_to_c, offsets), "n_on": n_on(rho, module_to_c, offsets), "source_sha256": source_hash(rho)})
    chain_dir = out_dir / f"chains_{inputs.run}"
    if (chain_dir / "marker.json").is_file():
        log(f"[identities] a completed or partial chain store exists at {chain_dir}: resuming it (the cells are deterministic; the marker's sums carry over)")
    store = run_cells(model, cells, ids, sources, job=f"identities_chains_{inputs.run}", run=inputs.run, out_dir=chain_dir, precision=inputs.precision, subbatch=inputs.subbatch,
                      set_name=inputs.eval_set, set_hash=rec["sha256_ids"], checkpoint_hashes=hashes, master_seed=master_seed, importance_chunk=inputs.chunk, resume=True, log=log)
    df = store.table()
    sums = store.extra["cell_sums"]
    name_of = {(c.family, c.rung, c.condition): c.name for c in cells}

    def cell_name(family: str, rung: str, condition: str | None = None) -> str:
        return name_of[(family, rung, condition)]

    def mean_kl(name: str) -> float:
        return float(df[df.cell == name].kl_mean.mean())

    # M10b: the m < g counts along the hard-zero chain
    hz_counts = {r: sums[cell_name("hard_zero", r)]["n_below_label"] for r in INTERMEDIATE_RUNGS + ("8",)}
    hz_counts["0"] = sums[cell_name("reference", "0", "unmasked_delta")]["n_below_label"]
    run_a = [hz_counts[r] for r in ("1", "2", "3")]
    run_b = [hz_counts[r] for r in ("4", "5", "6", "7", "8")]
    m10b = hz_counts["0"] == 0 and all(x <= y for x, y in zip(run_a, run_a[1:])) and all(x <= y for x, y in zip(run_b, run_b[1:])) and hz_counts["8"] > 0
    checks.append(Check("M10b", m10b, f"hard-zero chain, entries with m < g over the whole set per rung: {hz_counts}; zero at rung 0, non-decreasing within rungs 1-3 and 4-8, positive at rung 8: {m10b}; "
                                      f"positions with at least one such entry at rung 8: {sums[cell_name('hard_zero', '8')]['n_positions_below_label']}"))
    # M11: the applied-mask digests along both chains, pairwise distinct; rung 0 equals the reference's
    for fam, ref in (("hard_zero", "unmasked_delta"), ("union", "importances")):
        digests = {r: sums[cell_name(fam, r)]["F"] for r in INTERMEDIATE_RUNGS + ("8",)}
        digests["0"] = sums[cell_name("reference", "0", ref)]["F"]
        distinct = len(set(digests.values())) == len(digests)
        checks.append(Check("M11", distinct, f"{fam} chain: mask_fp_cell over rungs 0-8 pairwise distinct: {distinct}; rung 0 is the {ref} reference's digest {digests['0']}; digests {digests}"))
    # M14: the ends of the union chain
    kl0, kl8 = mean_kl(cell_name("reference", "0", "importances")), mean_kl(cell_name("union", "8"))
    kl_unm = mean_kl(cell_name("reference", "0", "unmasked"))
    checks.append(Check("M14", abs(kl8 - kl0) > 0.01, f"union chain ends: rung 0 (importances) {kl0:.4f}, rung 8 (the whole pool) {kl8:.4f}: |difference| {abs(kl8 - kl0):.4f} > 0.01 (P1); "
                                                      f"P2 reported: rung 8 against unmasked {kl_unm:.4f} and importances {kl0:.4f}"))
    # H3: the hard-zero rung 8, reported
    kl_hz8, kl_zero = mean_kl(cell_name("hard_zero", "8")), mean_kl(cell_name("reference", "0", "zero_all"))
    checks.append(Check("H3", None, f"hard-zero rung 8 (Delta included) mean divergence {kl_hz8:.3f} against zero-all {kl_zero:.3f}: order of tens of nats, reported"))
    # H1: the mask checks on one sub-batch at rungs 4 and 8 (and the residual), and the rung-0 clauses
    b_h1 = torch.from_numpy(np.ascontiguousarray(ids[: inputs.subbatch])).long().to(device)
    imp_h1 = compute_importances(model, b_h1, precision=inputs.precision, chunk=inputs.chunk)
    h1_ok = True
    h1_detail = []
    for r in ("4", "8"):
        rho = rho_by_rung[r]
        rt = rho_tensors(rho, module_to_c, imp_h1.g[keys[0]].dtype, device, offsets)
        masks, deltas, _ = family_masks("hard_zero", imp_h1.g, rt, background="ones", delta="included")
        erased_zero = all(bool((masks[k][..., rt[k].bool()] == 0).all()) for k in keys if bool(rt[k].any()))
        others_one = all(bool((masks[k][..., ~rt[k].bool()] == 1).all()) for k in keys)
        res_one = all(bool((deltas[k] == 1).all()) for k in keys)
        masks_x, deltas_x, _ = family_masks("hard_zero", imp_h1.g, rt, background="ones", delta="excluded")
        h1_ok = h1_ok and erased_zero and others_one and res_one and deltas_x is None
        h1_detail.append(f"rung {r}: erased ({n_on(rho, module_to_c, offsets)['total']}) exactly 0 at every position: {erased_zero}; others exactly 1: {others_one}; residual 1 when included: {res_one}, absent when excluded: {deltas_x is None}")
        del masks, deltas, masks_x
    # rung 0: Delta excluded bitwise the unmasked reference (digest), Delta included below tolerance from the target in this precision; the fp32 clause on one sub-batch
    rung0_excl_digest = sums[cell_name("reference", "0", "unmasked")]["F"]
    rho_none = rho_tensors(np.zeros(cache_unif.n_sub, dtype=np.bool_), module_to_c, imp_h1.g[keys[0]].dtype, device, offsets)
    masks0, _, _ = family_masks("hard_zero", imp_h1.g, rho_none, background="ones", delta="excluded")
    fr0 = masked_forward(model, b_h1, masks0, imp_h1.g, permitted=False, precision=inputs.precision)
    d0 = level3_hex(fr0.fp, np.arange(b_h1.shape[0]))["F"]
    ref_unm = masked_forward(model, b_h1, {k: torch.ones_like(imp_h1.g[k]) for k in keys}, imp_h1.g, permitted=True, precision=inputs.precision)
    same_digest = d0 == level3_hex(ref_unm.fp, np.arange(b_h1.shape[0]))["F"]
    tol = 1e-5 if inputs.precision == "fp32" else 1e-3
    kl_r0_incl = mean_kl(cell_name("reference", "0", "unmasked_delta"))
    detail0 = f"rung 0 excluded: digest equals the unmasked reference's on this sub-batch: {same_digest}; rung 0 included: divergence from the target over the set {kl_r0_incl:.2e} (< {tol:.0e} in {inputs.precision})"
    del fr0, ref_unm, masks0, rho_none, imp_h1  # free the bf16 sub-batch's g, logits, and masks before the float32 clause
    if str(device).startswith("cuda"):
        torch.cuda.empty_cache()
    fp32_clause = None
    if inputs.precision != "fp32":
        n32 = min(inputs.subbatch, 32)  # one float32 sub-batch; 32 sequences fit the 40 GB card in float32 (the residual job ran there)
        b32 = torch.from_numpy(np.ascontiguousarray(ids[:n32])).long().to(device)
        imp32 = compute_importances(model, b32, precision="fp32", chunk=inputs.chunk)
        rho_none32 = rho_tensors(np.zeros(cache_unif.n_sub, dtype=np.bool_), module_to_c, imp32.g[keys[0]].dtype, device, offsets)
        m32, d32, _ = family_masks("hard_zero", imp32.g, rho_none32, background="ones", delta="included")
        fr32 = masked_forward(model, b32, m32, imp32.g, permitted=False, precision="fp32", delta_masks=d32, weight_deltas=weight_deltas)
        fp32_clause = float(per_position_kl(imp32.target_logits, fr32.logits).mean())
        detail0 += f"; the float32 clause on one sub-batch of {n32}: {fp32_clause:.2e} (< 1e-5)"
        del imp32, m32, d32, fr32, b32
        if str(device).startswith("cuda"):
            torch.cuda.empty_cache()
    h1_pass = h1_ok and same_digest and kl_r0_incl < tol and (fp32_clause is None or fp32_clause < 1e-5)
    checks.append(Check("H1", h1_pass, "; ".join(h1_detail) + "; " + detail0 + f"; teeth: M10b's rung-8 count {hz_counts['8']} > 0"))

    # ------------------------------------------------------------------ M15: the code-specific builder on the real pools, every rung and draw (CPU)
    m15_ok = True
    prose_rho = {t: union_source(cache_prose, np.arange(cache_prose.n_positions), t) for t in (0.1, 0.5)}
    prose_hashes = set()
    checks_15 = []
    for t in (0.1, 0.5):
        assert np.array_equal(prose_rho[t], prose_named[t]), "the prose-named vector on file differs from the union over the whole prose pool"
        code_rho_8 = union_source(cache_code, np.arange(cache_code.n_positions), t)
        spec_8 = code_specific_source(code_rho_8, prose_rho[t])
        subs, _ = sub_rung_sets(alive, prose_named[t], f_code[t])
        for k in range(2):
            for r in INTERMEDIATE_RUNGS + ("8",):
                ds = donor_set(inputs.pool_code, cache_code.n_sequences, k, r, master_seed)
                u = union_source(cache_code, ds.positions, t)
                spec = code_specific_source(u, prose_rho[t])
                m15_ok = m15_ok and bool(np.all(spec <= u)) and not bool(np.any(spec & prose_rho[t]))
                prose_hashes.add(source_hash(prose_rho[t]))
        m15_ok = m15_ok and bool(np.array_equal(spec_8, code_rho_8 & ~prose_rho[t]))
        # 1[f_prose > 0] = rho_union(D_prose) exactly, both the same threshold on the same cache
        from vpd_audit.donors import counts_above

        f_prose_pos = counts_above(cache_prose.indices, cache_prose.values, cache_prose.n_sub, t) > 0
        m15_ok = m15_ok and bool(np.array_equal(f_prose_pos, prose_rho[t]))
        subsets = all(bool(np.all(subs[s] <= spec_8)) for s in SUB_RUNGS)
        m15_ok = m15_ok and subsets
        checks_15.append(f"tau {t}: prose-named {int(prose_rho[t].sum())}, rung-8 specific {int(spec_8.sum())} of code {int(code_rho_8.sum())}; sub-rungs {[int(subs[s].sum()) for s in SUB_RUNGS]} all subsets of rung 8: {subsets}")
    checks.append(Check("M15", m15_ok and len(prose_hashes) <= 2, f"every rung and draw at tau 0.1 and 0.5: rho_spec <= rho_union(J_code), rho_spec . rho_union(D_prose) = 0, one prose hash per tau ({len(prose_hashes)} values), "
                                                                 f"1[f_prose > 0] = rho_union(D_prose) exactly, rung-8 identity, sub-rungs inside rung 8: {m15_ok}; " + "; ".join(checks_15)))

    # ------------------------------------------------------------------ M16: first touched positions on E_lab_other
    ids_lab, _, _ = load_set(inputs.e_lab_other)
    n_lab = min(ids_lab.shape[0], inputs.e_lab_other_subbatches * inputs.subbatch)
    t_star: dict[tuple[str, str, float], list[np.ndarray]] = {}
    code_rho = {r: union_source(cache_code, donor_set(inputs.pool_code, cache_code.n_sequences, 0, r, master_seed).positions, 0.1) for r in INTERMEDIATE_RUNGS + ("8",)}
    spec_rho = {r: code_specific_source(code_rho[r], prose_rho[0.1]) for r in code_rho}
    for start in range(0, n_lab, inputs.subbatch):
        b = torch.from_numpy(np.ascontiguousarray(ids_lab[start : start + inputs.subbatch])).long().to(device)
        imp = compute_importances(model, b, precision=inputs.precision, chunk=inputs.chunk)
        for r in code_rho:
            for fam, rho in (("plain", code_rho[r]), ("specific", spec_rho[r])):
                rt = rho_tensors(rho, module_to_c, imp.g[keys[0]].dtype, device, offsets)
                for tq in (0.1, 0.0):
                    t_star.setdefault((fam, r, tq), []).append(first_touched(imp.g, rt, tq)[0].cpu().numpy())
        del imp
    ts = {k: np.concatenate(v) for k, v in t_star.items()}
    a = all(bool(np.all(ts[("specific", r, tq)] >= ts[("plain", r, tq)])) for r in code_rho for tq in (0.1, 0.0))
    b_ = all(bool(np.all(ts[(fam, r, 0.0)] <= ts[(fam, r, 0.1)])) for r in code_rho for fam in ("plain", "specific"))
    mono = all(bool(np.all(ts[(fam, r1, tq)] >= ts[(fam, r2, tq)])) for fam in ("plain", "specific") for tq in (0.1, 0.0) for run_ in (("1", "2", "3"), ("4", "5", "6", "7", "8")) for r1, r2 in zip(run_, run_[1:]))
    frac = {r: float((ts[("plain", r, 0.1)] / SEQ_LEN).mean()) for r in code_rho}
    frac_s = {r: float((ts[("specific", r, 0.1)] / SEQ_LEN).mean()) for r in code_rho}
    checks.append(Check("M16", a and b_ and mono, f"{n_lab} sequences of {inputs.e_lab_other}, draw 0, tau 0.1: t*(specific) >= t*(plain) for every sequence, rung, tau_q: {a}; t*(tau_q=0) <= t*(tau_q=0.1): {b_}; "
                                                  f"non-increasing within each nested run: {mono}; clean-prefix fraction at tau_q 0.1 per rung, plain {[round(v, 3) for v in frac.values()]}, specific {[round(v, 3) for v in frac_s.values()]}"))

    # ------------------------------------------------------------------ H2: our hard-zero against the authors' edit, one sequence, float32, rung 4 and S4
    b_h2 = torch.from_numpy(np.ascontiguousarray(ids[:1])).long().to(device)
    imp_h2 = compute_importances(model, b_h2, precision="fp32", chunk=inputs.chunk)
    subs, _ = sub_rung_sets(alive, prose_named[0.1], f_code[0.1])
    h2_detail = []
    h2_ok = True
    authors_fn = None
    try:
        from param_decomp.editing._editing import EditableModel

        authors_fn = EditableModel._edited_forward_batched
        how = "EditableModel._edited_forward_batched, unbound, on a stand-in exposing .model"
    except Exception as e:  # noqa: BLE001
        how = f"the authors' method reproduced verbatim (their module did not import: {type(e).__name__})"

        from param_decomp.models.components import make_mask_infos

        def authors_fn(self_, tokens, edits):  # type: ignore[misc]
            seq_len = tokens.shape[1]
            component_masks = {layer: torch.ones(1, seq_len, C, device=tokens.device) for layer, C in self_.model.module_to_c.items()}
            for key, value in edits.items():
                layer, idx_str = key.rsplit(":", 1)
                component_masks[layer][0, :, int(idx_str)] = value
            return self_.model(tokens, mask_infos=make_mask_infos(component_masks, routing_masks="all"))

    class _StandIn:
        pass

    stand_in = _StandIn()
    stand_in.model = model  # type: ignore[attr-defined]
    for label, rho in (("rung 4", code_rho["4"]), ("S4", subs["S4"])):
        rt = rho_tensors(rho, module_to_c, torch.float32, device, offsets)
        masks, _, _ = family_masks("hard_zero", imp_h2.g, rt, background="ones", delta="excluded")
        ours = masked_forward(model, b_h2, masks, imp_h2.g, permitted=False, precision="fp32").logits
        edits = {f"{k}:{int(i)}": 0.0 for k in keys for i in np.flatnonzero(rho[offsets[k] : offsets[k] + module_to_c[k]])}
        with torch.no_grad():
            theirs = authors_fn(stand_in, b_h2, edits)
        dmax = float((ours - theirs).abs().max())
        h2_ok = h2_ok and dmax < 1e-4
        h2_detail.append(f"{label} ({len(edits)} edits): max |ours - theirs| = {dmax:.2e}")
    checks.append(Check("H2", h2_ok, f"float32, sequence 0, residual excluded, against {how}: " + "; ".join(h2_detail) + " (< 1e-4)"))

    text = _fmt(checks)
    out_dir.mkdir(parents=True, exist_ok=True)
    with open(out_dir / f"checks_{inputs.run}.txt", "w") as f:
        f.write(text + "\n")
    with open(out_dir / f"identities_{inputs.run}.json", "w") as f:
        json.dump({"inputs": inputs.__dict__, "checks": [c.__dict__ for c in checks], "hard_zero_counts": hz_counts, "union_ends": {"rung_0_importances": kl0, "rung_8": kl8, "unmasked": kl_unm},
                   "hard_zero_rung_8": kl_hz8, "zero_all": kl_zero, "gpu": torch.cuda.get_device_name(0) if str(device).startswith("cuda") else None, "seconds": time.time() - t_all,
                   "chain_digests": {fam: {r: sums[cell_name(fam, r)]["F"] for r in INTERMEDIATE_RUNGS + ("8",)} for fam in ("hard_zero", "union")},
                   "reference_digests": {n: sums[cell_name("reference", "0", n)]["F"] for n in ref_names if n != "target"}}, f, indent=2, sort_keys=True)
    log(text)
    log(f"[identities] {inputs.run}: {len([c for c in checks if c.passed is True])} pass, {len([c for c in checks if c.passed is False])} fail, {len([c for c in checks if c.passed is None])} reported; {time.time() - t_all:.0f} s")
    return checks
