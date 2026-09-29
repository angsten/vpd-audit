"""The plain-terms extras: beside a cell's divergence, how often its top predicted token differs
from the original model's, how much probability it leaves on the original's top token, and its loss on the real next token.

New code, a sibling of the divergence functions of `metrics.py`, which are not edited. The target's side is computed once per
sub-batch from the same float32 softmax chunks `metrics.target_softmax_chunks` hands to `per_position_kl_from_probs`
(`target_top`): a = argmax P (the first index on a tie, `torch.argmax`'s rule), P(a), and a flag where the top two probabilities
are exactly equal. Under bf16 autocast the target's logits are bf16, whose spacing is 1/16 at magnitudes 8 to 16, so exact ties
between the top two are not rare; the flag is stored per position and every change rate is read beside a baseline's.

A cell's side (`cell_extras`) takes the cell's logits in the chunks of KL_CHUNK the divergence runs in, one float32 log-softmax
per chunk: the cell's top token (argmax, first index on a tie), its probability on the target's top token a, and the negative
log-probability of the real next token at positions 0 to T - 2. `summarize_extras` gives the per-text columns, float32 on the
device: the share of positions whose top token differs from the target's; the same share among positions with P(a) >= 0.5 (NaN
for a text with no such position); the mean probability on the target's top token; and the share of positions 0 to T - 2 whose
top token is the real next token. `top_k_at` gives the top five ids and probabilities at fixed example positions.

Stored dtypes (results.SubbatchStore's extras): the top token id as uint16 (the vocabulary has 50,277 ids), the probability on
the target's top token and the next-token loss as float16, the target's top probability as float32 (so that the P(a) >= 0.5
mask recomputed from the stored array is bitwise the device's), the tie flag as bool.
"""

from __future__ import annotations

from typing import Any

import torch
from torch import Tensor

from vpd_audit.constants import KL_CHUNK

CONFIDENT = 0.5  # P(a) >= 0.5, fixed in advance
TOP_K = 5
EXTRA_COLUMNS: tuple[str, ...] = ("top_changed", "top_changed_confident", "p_target_top", "top_is_next")  # the per-text columns, beside the existing `ce`


def target_top(target_probs: list[Tensor]) -> dict[str, Tensor]:
    """From the target's float32 softmax chunks: `top` (B, T) int64, a = argmax P; `top_p` (B, T) float32, P(a); `tie` (B, T)
    bool, the top two probabilities exactly equal; `confident` (B, T) bool, P(a) >= 0.5."""
    tops, ps, ties = [], [], []
    for p in target_probs:
        assert p.ndim == 3 and p.dtype == torch.float32, (tuple(p.shape), p.dtype)
        a = p.argmax(dim=-1)  # the first maximal index on a tie
        pa = p.gather(-1, a.unsqueeze(-1)).squeeze(-1)
        top2 = torch.topk(p, 2, dim=-1).values
        assert torch.equal(top2[..., 0], pa), "the largest probability is the probability at the argmax"
        tops.append(a)
        ps.append(pa)
        ties.append(top2[..., 0] == top2[..., 1])
    top, top_p, tie = torch.cat(tops, dim=0), torch.cat(ps, dim=0), torch.cat(ties, dim=0)
    return {"top": top, "top_p": top_p, "tie": tie, "confident": top_p >= CONFIDENT}


def cell_extras(target_top_ids: Tensor, logits: Tensor, ids: Tensor, *, chunk: int = KL_CHUNK) -> dict[str, Tensor]:
    """From a cell's logits (B, T, V) in any float dtype: `top` (B, T) int64, the cell's top token; `p_target_top` (B, T)
    float32, the cell's probability on the target's top token; `nll` (B, T - 1) float32, -log Q_t(x_{t+1}) for t = 0..T-2. One
    float32 log-softmax per chunk of `chunk` sequences, the chunks the divergence runs in."""
    assert logits.ndim == 3 and target_top_ids.shape == logits.shape[:2] == ids.shape, (tuple(logits.shape), tuple(target_top_ids.shape), tuple(ids.shape))
    ids = ids.to(logits.device).long()
    tops, qs, nlls = [], [], []
    for s in range(0, logits.shape[0], chunk):
        log_q = torch.log_softmax(logits[s : s + chunk].float(), dim=-1)
        tops.append(log_q.argmax(dim=-1))
        qs.append(log_q.gather(-1, target_top_ids[s : s + chunk].unsqueeze(-1)).squeeze(-1).exp())
        nlls.append(-log_q[:, :-1].gather(-1, ids[s : s + chunk, 1:].unsqueeze(-1)).squeeze(-1))
        del log_q
    out = {"top": torch.cat(tops, dim=0), "p_target_top": torch.cat(qs, dim=0), "nll": torch.cat(nlls, dim=0)}
    assert out["p_target_top"].dtype == torch.float32 and out["nll"].dtype == torch.float32 and out["nll"].shape == (logits.shape[0], logits.shape[1] - 1)
    return out


def target_as_cell(target: dict[str, Tensor]) -> dict[str, Tensor]:
    """The target's own side in a cell's form, for the per-text columns of the target reference (which has no forward): its top
    token and its probability on its own top token. Its next-token loss is the existing `ce_target` column."""
    return {"top": target["top"], "p_target_top": target["top_p"]}


def summarize_extras(cell: dict[str, Tensor], target: dict[str, Tensor], ids: Tensor) -> dict[str, Tensor]:
    """The per-text columns, (B,) float32 on the device."""
    ids = ids.to(cell["top"].device).long()
    changed = cell["top"] != target["top"]
    conf = target["confident"]
    n_conf = conf.sum(dim=1).to(torch.float32)
    changed_conf = (changed & conf).sum(dim=1).to(torch.float32)
    out = {"top_changed": changed.to(torch.float32).mean(dim=1),
           "top_changed_confident": torch.where(n_conf > 0, changed_conf / n_conf.clamp(min=1.0), torch.full_like(n_conf, float("nan"))),
           "p_target_top": cell["p_target_top"].mean(dim=1),
           "top_is_next": (cell["top"][:, :-1] == ids[:, 1:]).to(torch.float32).mean(dim=1)}
    assert all(v.dtype == torch.float32 for v in out.values())
    return out


def top_k_at(x: Tensor | list[Tensor], positions: Tensor, *, probs: bool, k: int = TOP_K) -> tuple[Tensor, Tensor]:
    """The top k ids and probabilities at the given positions of every text: `x` is a cell's logits (B, T, V) (`probs=False`:
    a float32 softmax of the selected rows is taken) or the target's softmax chunks (`probs=True`); `positions` is (B, P) int64.
    Returns (ids (B, P, k) int64, probabilities (B, P, k) float32), in descending probability."""
    if isinstance(x, list):
        assert probs
        rows, s = [], 0
        for p in x:
            b = p.shape[0]
            rows.append(p.gather(1, positions[s : s + b].to(p.device).unsqueeze(-1).expand(-1, -1, p.shape[-1])))
            s += b
        sel = torch.cat(rows, dim=0)
    else:
        sel = x.gather(1, positions.to(x.device).unsqueeze(-1).expand(-1, -1, x.shape[-1]))
        sel = sel.float() if probs else torch.softmax(sel.float(), dim=-1)
    assert sel.shape[:2] == positions.shape and sel.dtype == torch.float32
    top = torch.topk(sel, k, dim=-1)
    return top.indices, top.values


TOKEN_FILL = 65535  # uint16's last value: no token id reaches it (the vocabulary has 50,277)


def storage(cell: dict[str, Tensor]) -> dict[str, Any]:
    """The per-position arrays in their stored dtypes (numpy, on the host)."""
    top = cell["top"]
    assert int(top.max()) < TOKEN_FILL, "a token id must fit uint16 below the fill value"
    return {"top": top.cpu().numpy().astype("uint16"), "p_target_top": cell["p_target_top"].cpu().numpy().astype("float16"), "nll": cell["nll"].cpu().numpy().astype("float16")}


class LoopExtras:
    """What `cells.run_cells` holds for a tier-5 store: which cells keep their per-position arrays, the example positions, and
    the target's side of the current sub-batch. The arrays go to the store's extras/ folder (results.SubbatchStore):

        target__top (T) uint16, target__top_p (T) float32, target__tie (T) bool              once per store (per evaluation set)
        <cell>__top (T) uint16, <cell>__p_target_top (T) float16, <cell>__nll (T-1) float16  for every listed cell
        target__top5_ids, <cell>__top5_ids (P, 5) uint16; target__top5_p, <cell>__top5_p (P, 5) float32   with example positions
    """

    def __init__(self, cell_names: list[str], listed_names: list[str], example_positions: Any = None, *, seq_len: int):
        import numpy as np

        self.T = int(seq_len)
        self.listed = [n for n in cell_names if n in set(listed_names)]
        self.positions = None if example_positions is None else np.ascontiguousarray(example_positions, dtype=np.int64)
        self.target: dict[str, Tensor] | None = None
        self._pos_t: Tensor | None = None

    def spec(self) -> dict[str, tuple[tuple[int, ...], str, Any]]:
        T = self.T
        out: dict[str, tuple[tuple[int, ...], str, Any]] = {"target__top": ((T,), "uint16", TOKEN_FILL), "target__top_p": ((T,), "float32", float("nan")), "target__tie": ((T,), "bool", False)}
        for n in self.listed:
            out[f"{n}__top"] = ((T,), "uint16", TOKEN_FILL)
            out[f"{n}__p_target_top"] = ((T,), "float16", float("nan"))
            out[f"{n}__nll"] = ((T - 1,), "float16", float("nan"))
        if self.positions is not None:
            P = int(self.positions.shape[1])
            for n in ["target"] + self.listed:
                out[f"{n}__top5_ids"] = ((P, TOP_K), "uint16", TOKEN_FILL)
                out[f"{n}__top5_p"] = ((P, TOP_K), "float32", float("nan"))
        return out

    def start_subbatch(self, store: Any, sl: slice, target_probs: list[Tensor]) -> None:
        """Once per sub-batch, from the target's softmax chunks: a, P(a), the tie flag; stored; the top five at the examples."""
        self.target = target_top(target_probs)
        t = self.target
        assert int(t["top"].max()) < TOKEN_FILL
        store.set_extra("target__top", sl, t["top"].cpu().numpy().astype("uint16"))
        store.set_extra("target__top_p", sl, t["top_p"].cpu().numpy().astype("float32"))
        store.set_extra("target__tie", sl, t["tie"].cpu().numpy().astype("bool"))
        if self.positions is not None:
            self._pos_t = torch.from_numpy(self.positions[sl]).to(t["top"].device)
            ids5, p5 = top_k_at(target_probs, self._pos_t, probs=True)
            store.set_extra("target__top5_ids", sl, ids5.cpu().numpy().astype("uint16"))
            store.set_extra("target__top5_p", sl, p5.cpu().numpy().astype("float32"))

    def target_columns(self, ids: Tensor) -> dict[str, Any]:
        """The per-text columns of the target reference itself (no forward): nothing changes, P(a) is its own."""
        assert self.target is not None
        return {k: v.cpu().numpy() for k, v in summarize_extras(target_as_cell(self.target), self.target, ids).items()}

    def cell(self, store: Any, name: str, sl: slice, logits: Tensor, ids: Tensor) -> dict[str, Any]:
        """A cell's per-text columns (numpy, float32); its per-position arrays and its top five are stored if it is listed."""
        assert self.target is not None, "start_subbatch first"
        ex = cell_extras(self.target["top"], logits, ids)
        cols = {k: v.cpu().numpy() for k, v in summarize_extras(ex, self.target, ids).items()}
        if name in self.listed:
            for k, arr in storage(ex).items():
                store.set_extra(f"{name}__{k}", sl, arr)
            if self.positions is not None:
                ids5, p5 = top_k_at(logits, self._pos_t, probs=False)
                store.set_extra(f"{name}__top5_ids", sl, ids5.cpu().numpy().astype("uint16"))
                store.set_extra(f"{name}__top5_p", sl, p5.cpu().numpy().astype("float32"))
        return cols
