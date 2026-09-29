"""The sparse donor caches and the alive set, plus the plausible-range check of the target's cross-entropy
on the labeled sets and an autocast cross-entropy diagnostic.

For each donor pool (D_unif, D_code, D_prose on the main run; D_unif and D_code on the control run), g is computed
with `compute_importances` at sub-batch 64 and chunk 32 in bf16 and its nonzero entries stored per position as a
CSR structure: `indptr` (int64, one entry per position plus one), `indices` (uint16, the global subcomponent index in
`sorted(module_to_c)` order, 0 to 38,911), `values` (float32, not the bf16 of the original design: g is float32 under
autocast and every threshold g > tau must be decided on the values the harness sees). Saved with the set's ids hash,
the checkpoint hashes, the run manifest fields, the module order and offsets, and the SHA-256 of the three arrays.
Sanity, asserted: the dense g of the last sub-batch reconstructed from the CSR equals the computed g bitwise; the
mean count of nonzeros per position on D_unif is near 205 (reported for every pool, asserted within 15 percent on
D_unif as the paper's figure). The alive set: ImportanceSums over D_unif, the alive count per layer
and in total at 64, 128, 256, 512, and 1,024 sequences taken in order, and the 1,024-sequence alive set as a boolean
vector of length 38,912 beside the cache. From the caches (CPU): the prose-named set rho^union(D_prose, tau) and the
firing fraction f_code per subcomponent at tau in {0, 0.1, 0.5}, saved with hashes.
"""

from __future__ import annotations

import hashlib
import json
import time
from pathlib import Path
from typing import Any

import numpy as np
import torch
from torch import Tensor

from vpd_audit import env
from vpd_audit.constants import IMPORTANCE_CHUNK, SEQ_LEN
from vpd_audit.importances import ImportanceSums, autocast_context, compute_importances, module_keys
from vpd_audit.metrics import per_sequence_ce
from vpd_audit.results import code_commits

THRESHOLDS: tuple[float, ...] = (0.0, 0.1, 0.5)
PAPER_MEAN_NNZ = 205.0
ALIVE_CHECKPOINTS = (64, 128, 256, 512, 1024)
CE_RANGE = (1.0, 5.0)
CE_ROW_MAX = 8.0


def donors_dir() -> Path:
    d = env.CACHE_DIR / "donors"
    d.mkdir(parents=True, exist_ok=True)
    return d


def module_offsets(module_to_c: dict[str, int]) -> dict[str, int]:
    """The global index of subcomponent 0 of each module, in sorted module order."""
    off, acc = {}, 0
    for k in sorted(module_to_c):
        off[k] = acc
        acc += module_to_c[k]
    return off


def _sha(a: np.ndarray) -> str:
    return hashlib.sha256(np.ascontiguousarray(a).tobytes()).hexdigest()


def subbatch_csr(g: dict[str, Tensor]) -> tuple[Tensor, Tensor, Tensor]:
    """The nonzero entries of one sub-batch's g: (counts per position (B*T,) int64, global indices int64 sorted within
    each position, values float32), all on g's device."""
    keys = sorted(g)
    B, T = g[keys[0]].shape[:2]
    G = torch.cat([g[k].reshape(B * T, -1) for k in keys], dim=1)  # (B*T, 38912), the global index order
    nz = G != 0
    counts = nz.sum(dim=1)
    idx = torch.nonzero(nz)  # row-major: positions ascending, then columns ascending
    values = G[idx[:, 0], idx[:, 1]]
    del G, nz
    return counts, idx[:, 1], values


def dense_from_csr(indptr: np.ndarray, indices: np.ndarray, values: np.ndarray, positions: slice, n_sub: int) -> np.ndarray:
    """The dense (n_positions, 38912) float32 block for a slice of positions."""
    out = np.zeros((positions.stop - positions.start, n_sub), dtype=np.float32)
    for r, p in enumerate(range(positions.start, positions.stop)):
        a, b = indptr[p], indptr[p + 1]
        out[r, indices[a:b].astype(np.int64)] = values[a:b]
    return out


def build_cache(model: Any, ids: np.ndarray, *, run: str, set_name: str, set_hash: str, checkpoint_hashes: dict[str, str], precision: str = "bf16",
                subbatch: int = 64, chunk: int = IMPORTANCE_CHUNK, alive_checkpoints: tuple[int, ...] | None = None, out_dir: Path | None = None, log: Any = print) -> dict[str, Any]:
    """One pool's CSR cache into donors/<set>_<run>.npz with its JSON; optionally the alive counts against the number
    of sequences and the final alive set."""
    assert ids.ndim == 2 and ids.shape[1] == SEQ_LEN
    device = next(model.parameters()).device
    keys = module_keys(model)
    n_sub = sum(model.module_to_c.values())
    assert n_sub < 65536, n_sub
    offsets = module_offsets(model.module_to_c)
    out_dir = out_dir or donors_dir()
    N = ids.shape[0]
    counts_all: list[np.ndarray] = []
    indices_all: list[np.ndarray] = []
    values_all: list[np.ndarray] = []
    sums = ImportanceSums.empty(model) if alive_checkpoints else None
    alive_vs_n: dict[str, Any] = {}
    last_g: dict[str, Tensor] | None = None
    t0 = time.time()
    g_dtype = None
    for i, start in enumerate(range(0, N, subbatch)):
        batch = torch.from_numpy(np.ascontiguousarray(ids[start : start + subbatch])).long().to(device)
        imp = compute_importances(model, batch, precision=precision, chunk=chunk)
        g_dtype = str(next(iter(imp.g.values())).dtype)
        counts, gidx, vals = subbatch_csr(imp.g)
        counts_all.append(counts.cpu().numpy().astype(np.int64))
        indices_all.append(gidx.cpu().numpy().astype(np.uint16))
        values_all.append(vals.float().cpu().numpy().astype(np.float32))
        if sums is not None:
            sums.update(imp.g)
            n_seen = start + batch.shape[0]
            if n_seen in alive_checkpoints:
                alive_vs_n[str(n_seen)] = {"alive": sums.alive_counts(), "mean_count_positive_per_position": sums.per_layer_mean_count(), "n_positions": sums.n_positions}
        if start + subbatch >= N:
            last_g = {k: imp.g[k].detach().float().cpu() for k in keys}
        del imp, counts, gidx, vals, batch
        if device.type == "cuda":
            torch.cuda.empty_cache()
        log(f"[donors] {set_name}/{run}: sub-batch {i + 1}/{(N + subbatch - 1) // subbatch} ({time.time() - t0:.0f} s)")
    counts_np = np.concatenate(counts_all)
    indptr = np.zeros(counts_np.size + 1, dtype=np.int64)
    np.cumsum(counts_np, out=indptr[1:])
    indices = np.concatenate(indices_all)
    values = np.concatenate(values_all)
    assert indptr[-1] == indices.size == values.size and indptr.size == N * SEQ_LEN + 1
    # sanity: the last sub-batch reconstructed bitwise
    assert last_g is not None
    B_last = next(iter(last_g.values())).shape[0]
    pos0 = (N - B_last) * SEQ_LEN
    dense = dense_from_csr(indptr, indices, values, slice(pos0, N * SEQ_LEN), n_sub)
    G_last = torch.cat([last_g[k].reshape(B_last * SEQ_LEN, -1) for k in keys], dim=1).numpy()
    assert dense.shape == G_last.shape and np.array_equal(dense, G_last), "the dense g of the last sub-batch does not reconstruct bitwise from the CSR"
    mean_nnz = float(indptr[-1] / (N * SEQ_LEN))
    if set_name == "D_unif" and run == "main" and n_sub == 38912:  # the paper's figure, for the paper's model
        assert abs(mean_nnz - PAPER_MEAN_NNZ) <= 0.15 * PAPER_MEAN_NNZ, f"mean nonzeros per position {mean_nnz:.1f} against the paper's {PAPER_MEAN_NNZ}"
    name = f"{set_name}_{run}"
    npz = out_dir / f"{name}.npz"
    with open(npz.with_suffix(".npz.tmp"), "wb") as f:
        np.savez(f, indptr=indptr, indices=indices, values=values)
    npz.with_suffix(".npz.tmp").replace(npz)
    meta: dict[str, Any] = {"set_name": set_name, "set_hash": set_hash, "run": run, "checkpoint_hashes": checkpoint_hashes, "n_sequences": N, "seq_len": SEQ_LEN, "n_positions": N * SEQ_LEN,
                            "n_subcomponents": n_sub, "module_order": keys, "module_offsets": offsets, "module_to_c": {k: model.module_to_c[k] for k in keys},
                            "precision": precision, "g_dtype": g_dtype, "subbatch": subbatch, "importance_chunk": chunk, "values_dtype": "float32", "indices_dtype": "uint16", "indptr_dtype": "int64",
                            "nnz": int(indptr[-1]), "mean_nnz_per_position": mean_nnz, "paper_mean_nnz": PAPER_MEAN_NNZ,
                            "sha256": {"indptr": _sha(indptr), "indices": _sha(indices), "values": _sha(values)}, "bytes": int(npz.stat().st_size),
                            "reconstruction_check": f"the dense g of the last sub-batch ({B_last} sequences) equals the CSR bitwise",
                            "device": str(device), "gpu_name": torch.cuda.get_device_name(device) if device.type == "cuda" else None, "torch_version": torch.__version__,
                            "commits": code_commits(), "deterministic_algorithms": torch.are_deterministic_algorithms_enabled(), "seconds": time.time() - t0,
                            "created_at": time.strftime("%Y-%m-%dT%H:%M:%S%z")}
    if sums is not None:
        alive = np.concatenate([(sums.sum_g[k].numpy() / sums.n_positions) > 1e-6 for k in keys])
        assert alive.shape == (n_sub,)
        np.save(out_dir / f"alive_{name}.npy", alive)
        meta["alive"] = {"n_alive": int(alive.sum()), "threshold": 1e-6, "file": f"alive_{name}.npy", "sha256": _sha(alive), "by_n_sequences": alive_vs_n}
    with open(out_dir / f"{name}.json", "w") as f:
        json.dump(meta, f, indent=2, sort_keys=True)
    log(f"[donors] {name}: nnz {meta['nnz']} ({mean_nnz:.1f} per position), {meta['bytes'] / 1e6:.0f} MB, {time.time() - t0:.0f} s" + (f"; alive {meta['alive']['n_alive']}" if sums is not None else ""))
    return meta


def load_cache(name: str, out_dir: Path | None = None) -> tuple[np.ndarray, np.ndarray, np.ndarray, dict[str, Any]]:
    out_dir = out_dir or donors_dir()
    with open(out_dir / f"{name}.json") as f:
        meta = json.load(f)
    with np.load(out_dir / f"{name}.npz") as z:
        indptr, indices, values = z["indptr"], z["indices"], z["values"]
    for arr, key in ((indptr, "indptr"), (indices, "indices"), (values, "values")):
        assert _sha(arr) == meta["sha256"][key], f"{name}: {key} hash mismatch"
    return indptr, indices, values, meta


def counts_above(indices: np.ndarray, values: np.ndarray, n_sub: int, tau: float) -> np.ndarray:
    """Per subcomponent, the number of cached positions with g > tau (strict)."""
    m = values > tau
    return np.bincount(indices[m].astype(np.int64), minlength=n_sub)


def prose_named_and_f_code(prose: str = "D_prose_main", code: str = "D_code_main", out_dir: Path | None = None, thresholds: tuple[float, ...] = THRESHOLDS, log: Any = print) -> dict[str, Any]:
    """The code-specific set's inputs from the caches: rho^union(D_prose, tau) and f_code(tau) per subcomponent, saved beside the caches."""
    out_dir = out_dir or donors_dir()
    _, ip, vp, mp = load_cache(prose, out_dir)
    _, ic, vc, mc = load_cache(code, out_dir)
    assert mp["module_order"] == mc["module_order"] and mp["n_subcomponents"] == mc["n_subcomponents"]
    n_sub = mp["n_subcomponents"]
    tag = code[len("D_code_"):] if code.startswith("D_code_") else code  # "main", "control", "dry_simplestories": the files are keyed by it
    rho = {str(t): counts_above(ip, vp, n_sub, t) > 0 for t in thresholds}
    f_code = {str(t): counts_above(ic, vc, n_sub, t) / mc["n_positions"] for t in thresholds}
    np.savez(out_dir / f"prose_named_{tag}.npz", **{f"tau_{t}": rho[str(t)] for t in thresholds})
    np.savez(out_dir / f"f_code_{tag}.npz", **{f"tau_{t}": f_code[str(t)].astype(np.float32) for t in thresholds})
    meta = {"prose_cache": prose, "code_cache": code, "tag": tag, "files": {"prose_named": f"prose_named_{tag}.npz", "f_code": f"f_code_{tag}.npz"},
            "prose_sha256": mp["sha256"], "code_sha256": mc["sha256"], "thresholds": list(thresholds),
            "n_prose_named": {t: int(r.sum()) for t, r in rho.items()}, "f_code_mean": {t: float(v.mean()) for t, v in f_code.items()},
            "n_code_firing_any": {t: int((v > 0).sum()) for t, v in f_code.items()},
            "sha256": {"prose_named": {t: _sha(r) for t, r in rho.items()}, "f_code": {t: _sha(v.astype(np.float32)) for t, v in f_code.items()}}}
    with open(out_dir / f"prose_named_f_code_{tag}.json", "w") as f:
        json.dump(meta, f, indent=2, sort_keys=True)
    log(f"[donors] prose-named {meta['n_prose_named']}; code firing any {meta['n_code_firing_any']}")
    return meta


def labeled_ce(model: Any, sets: dict[str, np.ndarray], *, precision: str = "bf16", subbatch: int = 64, log: Any = print) -> dict[str, Any]:
    """The plausible-range check: the target's mean cross-entropy on every labeled set
    between 1 and 5 nats and no row above 8; recorded, not asserted."""
    device = next(model.parameters()).device
    out: dict[str, Any] = {}
    for name, ids in sets.items():
        ces = []
        for start in range(0, ids.shape[0], subbatch):
            batch = torch.from_numpy(np.ascontiguousarray(ids[start : start + subbatch])).long().to(device)
            with torch.no_grad(), autocast_context(device, precision):
                logits = model.target_model(batch) if hasattr(model, "target_model") else model(batch, cache_type="input").output
            if not isinstance(logits, Tensor):
                logits = logits.output if hasattr(logits, "output") else logits[0]
            ces.append(per_sequence_ce(logits, batch).cpu().numpy())
            del logits, batch
        ce = np.concatenate(ces)
        out[name] = {"n_rows": int(ce.size), "mean": float(ce.mean()), "std": float(ce.std(ddof=1)), "min": float(ce.min()), "max": float(ce.max()),
                     "mean_in_range": bool(CE_RANGE[0] <= ce.mean() <= CE_RANGE[1]), "no_row_above_8": bool(ce.max() <= CE_ROW_MAX), "range": list(CE_RANGE), "row_max": CE_ROW_MAX}
        log(f"[donors] target CE on {name}: mean {ce.mean():.3f} (in [1, 5]: {out[name]['mean_in_range']}), max {ce.max():.3f} (<= 8: {out[name]['no_row_above_8']})")
    return out


def ce_autocast_diagnostic(model: Any, ids16: np.ndarray, *, precision: str = "bf16") -> dict[str, Any]:
    """On one batch of bf16 logits, is `F.cross_entropy(logits_bf16, labels)`
    under autocast bitwise equal to `F.nll_loss(F.log_softmax(logits_bf16, dim=-1, dtype=torch.bfloat16).float(),
    labels)`? Beside them: the same with the log-softmax in float32, ours, and a float64 reference."""
    import torch.nn.functional as F

    device = next(model.parameters()).device
    batch = torch.from_numpy(np.ascontiguousarray(ids16)).long().to(device)
    with torch.no_grad(), autocast_context(device, precision):
        logits = model(batch, cache_type="input").output
    flat = logits[:, :-1].reshape(-1, logits.shape[-1])
    labels = batch[:, 1:].reshape(-1)
    with torch.no_grad(), autocast_context(device, precision):
        a = F.cross_entropy(flat, labels)
        b_in = F.nll_loss(F.log_softmax(flat, dim=-1, dtype=torch.bfloat16).float(), labels)
        c_in = F.nll_loss(F.log_softmax(flat, dim=-1, dtype=torch.float32), labels)
    with torch.no_grad():
        b_out = F.nll_loss(F.log_softmax(flat, dim=-1, dtype=torch.bfloat16).float(), labels)
        c_out = F.nll_loss(F.log_softmax(flat.float(), dim=-1), labels)
        ref = float(-(torch.log_softmax(flat.double(), dim=-1).gather(-1, labels.unsqueeze(-1))).mean())
    out = {"logits_dtype": str(logits.dtype), "n_positions": int(labels.numel()), "precision": precision,
           "cross_entropy_autocast": float(a), "nll_of_bf16_log_softmax_then_float_autocast": float(b_in), "nll_of_bf16_log_softmax_then_float_no_autocast": float(b_out),
           "nll_of_fp32_log_softmax_autocast": float(c_in), "nll_of_fp32_log_softmax_no_autocast": float(c_out), "float64_reference": ref,
           "bitwise_cross_entropy_equals_bf16_log_softmax_path": bool(torch.equal(a.float(), b_in.float())), "bitwise_cross_entropy_equals_bf16_log_softmax_path_no_autocast": bool(torch.equal(a.float(), b_out.float())),
           "bitwise_cross_entropy_equals_fp32_log_softmax_path": bool(torch.equal(a.float(), c_in.float())),
           "abs_diff_to_ref": {"cross_entropy_autocast": abs(float(a) - ref), "bf16_log_softmax_path": abs(float(b_in) - ref), "fp32_log_softmax_path": abs(float(c_in) - ref)},
           "dtypes": {"cross_entropy_autocast": str(a.dtype), "log_softmax_bf16": "torch.bfloat16 (explicit)", "log_softmax_default_under_autocast": str(F.log_softmax(flat, dim=-1).dtype) if device.type == "cuda" else None}}
    del logits, flat, labels
    return out


# ----------------------------------------------------------------------------- the alive set from a cache


def alive_from_cache(name: str, out_dir: Path | None = None, threshold: float = 1e-6, save: bool = True) -> dict[str, Any]:
    """The alive set of a pool from its CSR cache, on CPU: per subcomponent, the sum of the cached values over every
    position of the pool (float64), divided by the number of positions, above `threshold`. Saved beside the cache as
    alive_<name>.npy with its hash; where a vector from the job's ImportanceSums exists (D_unif_main), the two are
    compared and the disagreements counted (the sums differ in accumulation order only)."""
    out_dir = out_dir or donors_dir()
    indptr, indices, values, meta = load_cache(name, out_dir)
    n_sub, n_pos = int(meta["n_subcomponents"]), int(meta["n_positions"])
    sums = np.bincount(indices.astype(np.int64), weights=values.astype(np.float64), minlength=n_sub)
    mean_g = sums / n_pos
    alive = mean_g > threshold
    offsets = meta["module_offsets"]
    by_layer: dict[str, int] = {}
    for k, off in offsets.items():
        layer = f"layer_{k.split('.')[1]}"
        by_layer[layer] = by_layer.get(layer, 0) + int(alive[off : off + meta["module_to_c"][k]].sum())
    by_layer["total"] = int(alive.sum())
    result: dict[str, Any] = {"cache": name, "cache_sha256": meta["sha256"], "threshold": threshold, "n_positions": n_pos, "alive": by_layer, "alive_sha256": _sha(alive),
                              "mean_g_min_alive": float(mean_g[alive].min()) if alive.any() else None, "n_within_factor_2_of_threshold": int(((mean_g > threshold / 2) & (mean_g < threshold * 2)).sum())}
    path = out_dir / f"alive_{name}.npy"
    if path.is_file():
        saved = np.load(path)
        result["saved_vector"] = {"file": path.name, "sha256": _sha(saved), "n_alive": int(saved.sum()), "n_disagreements_with_cache": int((saved != alive).sum()),
                                  "identical": bool(np.array_equal(saved, alive))}
        if save and not np.array_equal(saved, alive):
            np.save(out_dir / f"alive_{name}.from_cache.npy", alive)
            result["from_cache_file"] = f"alive_{name}.from_cache.npy"
    elif save:
        np.save(path, alive)
        result["saved_vector"] = {"file": path.name, "sha256": _sha(alive), "n_alive": int(alive.sum()), "source": "this computation"}
    return result


def load_prose_named_and_f_code(tag: str, out_dir: Path | None = None) -> tuple[dict[float, np.ndarray], dict[float, np.ndarray], dict[str, Any]]:
    out_dir = out_dir or donors_dir()
    with open(out_dir / f"prose_named_f_code_{tag}.json") as f:
        meta = json.load(f)
    with np.load(out_dir / f"prose_named_{tag}.npz") as z:
        rho = {float(k[len("tau_"):]): z[k].astype(np.bool_) for k in z.files}
    with np.load(out_dir / f"f_code_{tag}.npz") as z:
        fc = {float(k[len("tau_"):]): z[k].astype(np.float64) for k in z.files}
    return rho, fc, meta
