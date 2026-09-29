"""H4, a cross-check cell: on the first 128 sequences of E, the main run,
float32, the residual excluded throughout, one sequence at a time:

  (a) the authors' `EditableModel._edited_forward_batched`, as H2 drives it, with the edit set being every
      subcomponent no position of D_unif names above tau = 0.1 (the complement of the rung-8 union set), each set to 0;
  (b) our hard-zero mask of the same set on the same sequences;
  (c) our union rung-8 cell (tau = 0.1, r = 0, Delta excluded) on the same sequences: the union set at 1, the
      never-named set at g.

Reported: the three mean divergences against the target, the per-sequence maximum |(a) - (b)| on the logits, and
(c) - (b), the effect of the never-named set sitting at g rather than at 0.

The readings, stated before it runs (H4_READINGS): (a) ~ (b), the maximum |(a) - (b)| at or below 1e-5 as H2 found
on one sequence, says our mask path is not the source of the union's rung-8 divergence of 1.29 nats (identities,
M14); (c) within a few hundredths of a nat of (b) says the union's whole-pool cell is that mask.
"""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any

import numpy as np
import torch

from vpd_audit import env
from vpd_audit.importances import compute_importances, module_keys
from vpd_audit.masks import masked_forward
from vpd_audit.metrics import per_position_kl, summarize_kl
from vpd_audit.sources import Cache, donor_set, family_masks, rho_tensors, source_hash, union_source

H4_READINGS = {
    "a_vs_b": "max over the sequences of max |logits(a) - logits(b)| at or below 1e-5 (H2 found 0.00e+00 on one sequence at rung 4 and S4): our hard-zero mask path is not the source of the union's rung-8 divergence",
    "c_vs_b": "mean KL(c) within a few hundredths of a nat of mean KL(b) (the flag below uses 0.05): the union's whole-pool cell is that mask, the never-named set at g rather than at 0 being worth the difference",
    "stated": "before the launch, in this module",
}
A_VS_B_TOL = 1e-5
C_VS_B_FEW_HUNDREDTHS = 0.05


def _authors_edit_forward() -> tuple[Any, str]:
    """The authors' batched edit forward, unbound, on a stand-in exposing .model (as H2 drives it), or their method
    reproduced verbatim if their module does not import."""
    try:
        from param_decomp.editing._editing import EditableModel

        return EditableModel._edited_forward_batched, "EditableModel._edited_forward_batched, unbound, on a stand-in exposing .model"
    except Exception as e:  # noqa: BLE001
        from param_decomp.models.components import make_mask_infos

        def authors_fn(self_, tokens, edits):  # type: ignore[misc]
            seq_len = tokens.shape[1]
            component_masks = {layer: torch.ones(1, seq_len, C, device=tokens.device) for layer, C in self_.model.module_to_c.items()}
            for key, value in edits.items():
                layer, idx_str = key.rsplit(":", 1)
                component_masks[layer][0, :, int(idx_str)] = value
            return self_.model(tokens, mask_infos=make_mask_infos(component_masks, routing_masks="all"))

        return authors_fn, f"the authors' method reproduced verbatim (their module did not import: {type(e).__name__})"


def run_h4(*, run: str, eval_set: str, pool: str, n_sequences: int, tau: float = 0.1, device: str, out_dir: Path, precision: str = "fp32", chunk: int = 32,
           master_seed: int = 0, log: Any = print) -> dict[str, Any]:
    from vpd_audit.artifacts import checkpoint_hashes, load_component_model
    from vpd_audit.data import load_set
    from vpd_audit.results import code_commits

    torch.use_deterministic_algorithms(True, warn_only=True)
    t0 = time.time()
    model = load_component_model(run, device)
    keys = module_keys(model)
    module_to_c = {k: model.module_to_c[k] for k in keys}
    ids_all, _, rec = load_set(eval_set)
    ids = ids_all[:n_sequences]
    cache = Cache.load(f"{pool}_{run}")
    offsets = cache.offsets
    ds = donor_set(pool, cache.n_sequences, 0, "8", master_seed)  # the whole pool
    rho_u = union_source(cache, ds.positions, tau)  # the rung-8 union set: named above tau by some position of the pool
    comp = ~rho_u.astype(bool)  # every subcomponent no position of the pool names above tau
    n_union, n_comp, n_sub = int(rho_u.sum()), int(comp.sum()), int(rho_u.size)
    authors_fn, how = _authors_edit_forward()
    edits = {f"{k}:{int(i)}": 0.0 for k in keys for i in np.flatnonzero(comp[offsets[k] : offsets[k] + module_to_c[k]])}
    assert len(edits) == n_comp

    class _StandIn:
        pass

    stand_in = _StandIn()
    stand_in.model = model  # type: ignore[attr-defined]
    log(f"[h4] {run}: {eval_set}[:{ids.shape[0]}], pool {pool} ({cache.n_sequences} sequences), tau {tau}: union set {n_union}, its complement {n_comp} of {n_sub}; {precision}, one sequence at a time; (a) via {how}")
    kl_a, kl_b, kl_c, dmax_ab, dmax_bc = [], [], [], [], []
    rt_comp = rt_union = None
    for b in range(ids.shape[0]):
        batch = torch.from_numpy(np.ascontiguousarray(ids[b : b + 1])).long().to(device)
        imp = compute_importances(model, batch, precision=precision, chunk=chunk)  # type: ignore[arg-type]
        g = imp.g
        dtype = g[keys[0]].dtype
        if rt_comp is None:
            rt_comp = rho_tensors(comp.astype(np.float32), module_to_c, dtype, device, offsets)
            rt_union = rho_tensors(rho_u, module_to_c, dtype, device, offsets)
        # (b) our hard-zero mask of the complement: 0 on the never-named set, 1 elsewhere
        masks_b, _, _ = family_masks("hard_zero", g, rt_comp, background="ones", delta="excluded")
        logits_b = masked_forward(model, batch, masks_b, g, permitted=False, precision=precision).logits.float()  # type: ignore[arg-type]
        # (a) the authors' edit forward with the same set at 0
        with torch.no_grad():
            logits_a = authors_fn(stand_in, batch, edits).float()
        # (c) our union rung-8 cell: 1 on the union set, g elsewhere
        masks_c, _, _ = family_masks("union", g, rt_union, background="r0", delta="excluded")
        logits_c = masked_forward(model, batch, masks_c, g, permitted=True, precision=precision).logits.float()  # type: ignore[arg-type]
        tgt = imp.target_logits.float()
        for store, lg in ((kl_a, logits_a), (kl_b, logits_b), (kl_c, logits_c)):
            store.append(float(summarize_kl(per_position_kl(tgt, lg))[0][0]))
        dmax_ab.append(float((logits_a - logits_b).abs().max()))
        dmax_bc.append(float((logits_c - logits_b).abs().max()))
        del imp, g, masks_b, masks_c, logits_a, logits_b, logits_c, tgt
        if (b + 1) % 16 == 0 or b + 1 == ids.shape[0]:
            log(f"[h4] {b + 1}/{ids.shape[0]}: mean KL so far (a) {np.mean(kl_a):.4f} (b) {np.mean(kl_b):.4f} (c) {np.mean(kl_c):.4f}; max |a - b| {max(dmax_ab):.2e}")
    a, bb, c = np.array(kl_a), np.array(kl_b), np.array(kl_c)
    out = {
        "identity": "H4", "run": run, "eval_set": eval_set, "set_hash": rec["sha256_ids"], "n_sequences": int(ids.shape[0]), "pool": pool, "tau": tau, "precision": precision, "residual": "excluded",
        "one_sequence_at_a_time": True, "authors_forward": how, "n_union": n_union, "n_complement": n_comp, "n_subcomponents": n_sub, "union_sha256": source_hash(rho_u), "complement_sha256": source_hash(comp),
        "readings_stated_before_run": H4_READINGS,
        "mean_kl": {"a_authors_edit_complement_to_0": float(a.mean()), "b_our_hard_zero_complement": float(bb.mean()), "c_our_union_rung_8": float(c.mean())},
        "max_abs_logit_diff_a_b": {"max_over_sequences": float(max(dmax_ab)), "per_sequence": dmax_ab},
        "max_abs_logit_diff_c_b": {"max_over_sequences": float(max(dmax_bc))},
        "kl_a_minus_b": {"mean": float((a - bb).mean()), "max_abs_per_sequence": float(np.abs(a - bb).max())},
        "kl_c_minus_b": {"mean": float((c - bb).mean()), "min": float((c - bb).min()), "max": float((c - bb).max()), "per_sequence": (c - bb).tolist()},
        "per_sequence_kl": {"a": kl_a, "b": kl_b, "c": kl_c},
        "reading": {"a_vs_b": {"pass": bool(max(dmax_ab) <= A_VS_B_TOL), "tolerance": A_VS_B_TOL},
                    "c_vs_b": {"within_few_hundredths": bool(abs(float((c - bb).mean())) <= C_VS_B_FEW_HUNDREDTHS), "few_hundredths": C_VS_B_FEW_HUNDREDTHS}},
        "gpu": torch.cuda.get_device_name(0) if str(device).startswith("cuda") else None, "torch_version": torch.__version__, "commits": code_commits(), "checkpoint_hashes": checkpoint_hashes(run),
        "seconds": time.time() - t0,
    }
    text = format_h4(out)
    out_dir.mkdir(parents=True, exist_ok=True)
    with open(out_dir / f"h4_{run}.json", "w") as f:
        json.dump(out, f, indent=2, sort_keys=True)
    with open(out_dir / f"h4_{run}.txt", "w") as f:
        f.write(text + "\n")
    log(text)
    return out


def format_h4(o: dict[str, Any]) -> str:
    m = o["mean_kl"]
    L = [f"H4 ({o['run']}, {o['eval_set']}[:{o['n_sequences']}], {o['precision']}, residual excluded, one sequence at a time; union set {o['n_union']}, complement {o['n_complement']} of {o['n_subcomponents']}; (a) via {o['authors_forward']})",
         "", "| arm | mean KL against the target (nats) |", "|---|---|",
         f"| (a) the authors' edit, the never-named set at 0 | {m['a_authors_edit_complement_to_0']:.4f} |",
         f"| (b) our hard-zero mask of the same set | {m['b_our_hard_zero_complement']:.4f} |",
         f"| (c) our union rung 8 (tau {o['tau']}, r = 0, Delta excluded): the never-named set at g | {m['c_our_union_rung_8']:.4f} |", "",
         f"max over sequences of max |logits(a) - logits(b)|: {o['max_abs_logit_diff_a_b']['max_over_sequences']:.2e} (reading: at or below {o['reading']['a_vs_b']['tolerance']:.0e} -> {'pass' if o['reading']['a_vs_b']['pass'] else 'FAIL'}); "
         f"|KL(a) - KL(b)| per sequence at most {o['kl_a_minus_b']['max_abs_per_sequence']:.2e}",
         f"(c) - (b): mean {o['kl_c_minus_b']['mean']:+.4f} nats (per sequence {o['kl_c_minus_b']['min']:+.4f} to {o['kl_c_minus_b']['max']:+.4f}); within {o['reading']['c_vs_b']['few_hundredths']}: {o['reading']['c_vs_b']['within_few_hundredths']}",
         f"readings stated before the run: {o['readings_stated_before_run']['a_vs_b']}; {o['readings_stated_before_run']['c_vs_b']}",
         f"{o['gpu'] or 'cpu'}, {o['seconds']:.0f} s"]
    return "\n".join(L)
