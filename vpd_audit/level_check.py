"""The corner check of the level cells.

The six level cells map the straight path between the labelled state and the complete model, s + (1 - s) g on the alive
set with the never-named set at its labels (background r0) or at 1 (background r1). Their four corners already exist as
cells: s = 0 with the never-named set at labels is the importances reference (masks g); s = 1 at labels is the union's
rung 8 under r0 (where(rho, 1, g)); s = 0 at 1 is the soft erase's rung 8 under r1 (where(rho, g, 1)); s = 1 at 1 is
unmasked (ones). The check is that a level cell at s = 0 and s = 1 built through the new path
(`sources.level_masks` via `family_masks("level", ...)`) reproduces those four bitwise on one sub-batch: the mask
tensors, the applied-mask fingerprints, and the float32 per-position divergences, and, when a store of the same run on
the same card is given, the store's kl_mean and per-sequence mask digests of the four existing cells on that sub-batch.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import torch

from vpd_audit.fingerprint import level3_hex
from vpd_audit.importances import compute_importances, module_keys
from vpd_audit.masks import apply_binary_source, masked_forward
from vpd_audit.metrics import per_position_kl_from_probs, summarize_kl, target_softmax_chunks
from vpd_audit.sources import family_masks, rho_tensors


def level_corner_check(model: Any, ids: np.ndarray, alive_set: np.ndarray, *, run: str, precision: str, subbatch: int, chunk: int, store_dir: Path | None = None,
                       log: Any = print) -> dict[str, Any]:
    """The four corners on the first `subbatch` sequences of `ids`; `alive_set` is the rung-8 union at tau = 0.1 over the
    run's own D_unif cache (the level cells' named set), (n_sub,) bool. Returns a dictionary with `pass` and one entry per
    corner; nothing is asserted here, the caller decides."""
    device = next(model.parameters()).device
    keys = module_keys(model)
    batch = torch.from_numpy(np.ascontiguousarray(ids[:subbatch])).long().to(device)
    B = int(batch.shape[0])
    imp = compute_importances(model, batch, precision=precision, chunk=chunk)
    g, target_logits = imp.g, imp.target_logits
    del imp
    dtype = g[keys[0]].dtype
    target_probs = target_softmax_chunks(target_logits)
    del target_logits
    rho = rho_tensors(alive_set, model.module_to_c, dtype, device)
    seq_index = np.arange(B)
    rows = None
    if store_dir is not None and (Path(store_dir) / "per_sequence.parquet").is_file():
        rows = pd.read_parquet(Path(store_dir) / "per_sequence.parquet")
    corners = [
        (0.0, "r0", f"{run}/E/ref/importances", lambda: {k: g[k] for k in keys}),
        (1.0, "r0", f"{run}/E/union/D_unif/tau0.1/r0/excl/k0/r8", lambda: {k: apply_binary_source(g[k], rho[k]) for k in keys}),
        (0.0, "r1", f"{run}/E/soft_erase/D_unif/tau0.1/r1/excl/k0/r8", lambda: {k: apply_binary_source(g[k], 1 - rho[k]) for k in keys}),
        (1.0, "r1", f"{run}/E/ref/unmasked", lambda: {k: torch.ones_like(g[k]) for k in keys}),
    ]
    out: dict[str, Any] = {"n_sequences": B, "precision": precision, "store_dir": str(store_dir) if store_dir is not None else None, "corners": []}
    for level, bg, existing, build in corners:
        new_masks, _, permitted = family_masks("level", g, rho, background=bg, delta="excluded", level=level)
        old_masks = build()
        masks_equal = all(bool(torch.equal(new_masks[k], old_masks[k])) for k in keys)
        fr_new = masked_forward(model, batch, new_masks, g, permitted=permitted, precision=precision)
        fr_old = masked_forward(model, batch, old_masks, g, permitted=True, precision=precision)
        kl_new = per_position_kl_from_probs(target_probs, fr_new.logits)
        kl_old = per_position_kl_from_probs(target_probs, fr_old.logits)
        fp_new, fp_old = level3_hex(fr_new.fp, seq_index), level3_hex(fr_old.fp, seq_index)
        entry: dict[str, Any] = {"level": level, "background": bg, "never_named_at": "labels" if bg == "r0" else "one", "existing_cell": existing,
                                 "masks_bitwise": masks_equal, "fingerprints_equal": fp_new == fp_old, "kl_bitwise": bool(torch.equal(kl_new, kl_old)),
                                 "n_below_label": fr_new.n_below_label, "store_rows_equal": None}
        if rows is not None:
            sub = rows[(rows["cell"] == existing) & (rows["seq"] < B)].sort_values("seq")
            if len(sub) == B:
                kl_mean = summarize_kl(kl_new)[0].cpu().numpy().astype(np.float32)
                entry["store_rows_equal"] = bool(np.array_equal(sub["kl_mean"].to_numpy(np.float32), kl_mean) and (sub["mask_fp"].to_numpy() == np.asarray(fp_new["phi"])).all())
            else:
                entry["store_rows_equal"] = f"the store holds {len(sub)} rows of {existing} on these sequences, not {B}"
        out["corners"].append(entry)
        del fr_new, fr_old, kl_new, kl_old, new_masks, old_masks
    out["pass"] = all(e["masks_bitwise"] and e["fingerprints_equal"] and e["kl_bitwise"] and e["store_rows_equal"] in (None, True) for e in out["corners"])
    log(f"[level-corners] {B} sequences, {precision}: " + "; ".join(f"s={e['level']:g} at {e['never_named_at']} vs {e['existing_cell'].split('/', 2)[-1]}: masks {e['masks_bitwise']}, fp {e['fingerprints_equal']}, kl {e['kl_bitwise']}, store {e['store_rows_equal']}" for e in out["corners"])
        + f" -> {'pass' if out['pass'] else 'FAIL'}")
    return out
