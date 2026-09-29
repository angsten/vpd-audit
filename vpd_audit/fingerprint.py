"""The on-device mask fingerprint, the replacement for the SHA-256 of the launch precondition P4.

P4 needs, for every cell, a digest of the mask tensors the forward actually received, so that within a chain
every cell's digest is pairwise distinct and rung 0's equals the corresponding reference cell's (M6, M11). The
SHA-256 over the host copy cost 98 percent of the acceptance run. This is an exact,
position-dependent, 64-bit fingerprint of the masks' bit patterns computed on the device: a deterministic
function of the mask bits, identical on CPU and CUDA, independent of how a sub-batch is chunked. It need not
resist a constructed collision (about 1e5 digest comparisons over the grid at 2^-64 per pair).

Notation. A cell's applied masks on one sub-batch are the tensors m^(l), l = 0..23 in
`sorted(model.module_to_c)` order, of shape (B, T, C_l), and when the residual is included the residual masks
m^Delta(l) of shape (B, T); x is the integer whose bits are the entry's bits (float32 -> int32, bf16 -> int16,
sign-extended to int64), a bijection on bit patterns, so -0.0 != +0.0 and distinct NaN payloads are distinct.
Every sum and product is in Z / 2^64, represented as int64 in two's complement (PyTorch int64 arithmetic gives
the low 64 bits on CPU and CUDA; unit test T1 arbitrates against a Python big-integer reference). n_b is the
*global* index of sequence b in its evaluation set.

The mixer mu is the splitmix64 finalizer (Steele, Lea, and Flood, "Fast Splittable Pseudorandom Number
Generators", OOPSLA 2014; Java's SplittableRandom.mix64); constants and shifts checked against Sebastiano Vigna's
public-domain splitmix64.c (https://prng.di.unimi.it/splitmix64.c, 2015):
    z = (z ^ (z >>> 30)) * 0xbf58476d1ce4e5b9;  z = (z ^ (z >>> 27)) * 0x94d049bb133111eb;  return z ^ (z >>> 31);
Each step is a bijection on Z / 2^64 (xor-shift is invertible; multiplication by an odd constant is invertible
modulo 2^64), so mu is a bijection.

Weights: W_{t,c} = mu(t C + c + kappa_W) | 1 (odd, hence a unit), one tensor per mask shape, computed by integer
operations from torch.arange, so the same on every device; W^Delta_t = mu(t + kappa_Delta) | 1.

The four levels:
  1. per (module, sequence): h^(l)_b = sum_{t,c} W_{t,c} x^(l)_{b,t,c}; hd^(l)_b = sum_t W^Delta_t x^Delta(l)_{b,t}.
  2. per sequence: phi_b = mu(kappa_dtype + d) + mu(kappa_res + rho) + sum_l mu(h^(l)_b + sigma_l)
     + rho sum_l mu(hd^(l)_b + sigma^Delta_l), with sigma_l = mu(kappa_mod + l), sigma^Delta_l = mu(kappa_modDelta + l),
     d in {32, 16} the dtype code, rho in {0, 1} the residual flag.
  3. per (cell, sub-batch i): with s_b = mu(kappa_seq + n_b), F_i = sum_{b in i} mu(phi_b + s_b) and per module
     H^(l)_i = sum_{b in i} mu(h^(l)_b + s_b) (and Hd^(l)_i likewise).
  4. per cell-pass: F = sum_i F_i, H^(l) = sum_i H^(l)_i, plain modular sums; so F is the same whatever the
     sub-batch layout, and a resumed run gives the same F as an uninterrupted one.
Digests are stored as 16 lowercase hex characters of the value modulo 2^64.

Why it detects what P4 needs: one entry changing moves h by W_{t,c} (x' - x) != 0 (W odd, 0 < |x' - x| < 2^32),
then exactly one summand of phi_b changes and mu is a bijection, so phi_b, F_i, F, H change: deterministic. Two
distinct entries swapped within one (l, b) move h by (a - a')(W_{t,c} - W_{t',c'}), zero only if two mixed odd
weights agree in their low 33 bits (2^-32 per pair); with linear weights a swap of two whole positions with the
same multiset of values would go undetected, which is why the weights are mixed. Two same-shape modules exchanged
exchange H^(l) and H^(l'), detected deterministically at the module level. A wrong draw, an off-by-one along t,
bf16-rounded values, the residual silently in or out, a cast: each changes an h or the dtype or residual summand.

Memory and time: level 1 runs module by module in slabs of 8 sequences along B; for the largest module
(C = 3584) the two int64 temporaries are 117 MB each. About 44 bytes of traffic per entry, 56 GB per cell per
sub-batch of 64, about 0.05 s at 1.2 TB/s; the pre-registered trigger for revisiting the implementation is 0.1 s
per cell per sub-batch. Keep phi_b and the per-module h on the device and pull them once per cell with the other
per-sequence results.

`sha256_masks` (the acceptance run's hash, moved here from masks.py) is the oracle for unit test T3 and the smoke's G2,
behind a flag no grid run sets.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from typing import Any

import torch
from torch import Tensor

MASK64 = (1 << 64) - 1
C1 = 0xBF58476D1CE4E5B9
C2 = 0x94D049BB133111EB
SHIFTS = (30, 27, 31)

# Seven distinct salts, spaced by 2^32 so that kappa + index never collides across families for any index < 2^32.
K_W = 1 << 32
K_DELTA = 2 << 32
K_MOD = 3 << 32
K_MODDELTA = 4 << 32
K_SEQ = 5 << 32
K_DTYPE = 6 << 32
K_RES = 7 << 32
SALTS: dict[str, int] = {"W": K_W, "delta": K_DELTA, "mod": K_MOD, "mod_delta": K_MODDELTA, "seq": K_SEQ, "dtype": K_DTYPE, "res": K_RES}
assert len(set(SALTS.values())) == len(SALTS)
SLAB = 8
DTYPE_CODES: dict[torch.dtype, int] = {torch.float32: 32, torch.bfloat16: 16}
VIEW_DTYPES: dict[torch.dtype, torch.dtype] = {torch.float32: torch.int32, torch.bfloat16: torch.int16}

FINGERPRINT_SPEC: dict[str, Any] = {
    "version": 1,
    "mixer": "splitmix64",
    "mixer_constants": {"c1": f"0x{C1:016x}", "c2": f"0x{C2:016x}", "shifts": list(SHIFTS)},
    "mixer_reference": "Steele, Lea, Flood, OOPSLA 2014; Vigna, splitmix64.c (public domain), https://prng.di.unimi.it/splitmix64.c",
    "salts": dict(SALTS),
    "slab": SLAB,
    "dtype_codes": {str(k): v for k, v in DTYPE_CODES.items()},
    "levels": "1: h_b^(l) = sum W x; 2: phi_b; 3: F_i, H_i^(l) with global sequence salts; 4: F = sum_i F_i mod 2^64",
    "hex": "16 lowercase hex characters of the value modulo 2^64",
}


# ----------------------------------------------------------------------------- python-int arithmetic


def s64(v: int) -> int:
    """A Python int reduced to the int64-representable value congruent to it modulo 2^64."""
    v &= MASK64
    return v - (1 << 64) if v >= (1 << 63) else v


def u64(v: int) -> int:
    """The value modulo 2^64 in [0, 2^64)."""
    return v & MASK64


def mix_py(z: int) -> int:
    """The splitmix64 finalizer on Python ints; returns a value in [0, 2^64)."""
    z &= MASK64
    z = ((z ^ (z >> SHIFTS[0])) * C1) & MASK64
    z = ((z ^ (z >> SHIFTS[1])) * C2) & MASK64
    return z ^ (z >> SHIFTS[2])


def to_hex(v: int | Tensor) -> str:
    if isinstance(v, Tensor):
        assert v.dtype == torch.int64 and v.ndim == 0, (v.dtype, v.shape)
        v = int(v.item())
    return format(u64(v), "016x")


def from_hex(h: str) -> int:
    assert len(h) == 16, h
    return int(h, 16)


def sum_hex(hexes: list[str]) -> str:
    """Level 4: the modular sum of per-sub-batch digests."""
    return format(u64(sum(from_hex(h) for h in hexes)), "016x")


# ----------------------------------------------------------------------------- torch int64 arithmetic


def lshr(z: Tensor, k: int) -> Tensor:
    """Logical (zero-fill) shift right on int64 tensors; torch's >> is arithmetic."""
    return (z >> k) & ((1 << (64 - k)) - 1)


def mix_t(z: Tensor) -> Tensor:
    """The splitmix64 finalizer on int64 tensors, elementwise, in Z / 2^64 (two's complement)."""
    assert z.dtype == torch.int64
    z = (z ^ lshr(z, SHIFTS[0])) * s64(C1)
    z = (z ^ lshr(z, SHIFTS[1])) * s64(C2)
    return z ^ lshr(z, SHIFTS[2])


_WEIGHT_CACHE: dict[tuple[int, int, str], Tensor] = {}
_DELTA_WEIGHT_CACHE: dict[tuple[int, str], Tensor] = {}


def weights(T: int, C: int, device: torch.device | str) -> Tensor:
    """W_{t,c} = mu(t C + c + kappa_W) | 1, shape (T, C), int64, odd; cached per (T, C, device)."""
    dev = torch.device(device)
    key = (int(T), int(C), str(dev))
    if key not in _WEIGHT_CACHE:
        idx = torch.arange(T * C, dtype=torch.int64, device=dev)
        _WEIGHT_CACHE[key] = (mix_t(idx + s64(K_W)) | 1).view(T, C)
    return _WEIGHT_CACHE[key]


def delta_weights(T: int, device: torch.device | str) -> Tensor:
    """W^Delta_t = mu(t + kappa_Delta) | 1, shape (T,), int64, odd."""
    dev = torch.device(device)
    key = (int(T), str(dev))
    if key not in _DELTA_WEIGHT_CACHE:
        idx = torch.arange(T, dtype=torch.int64, device=dev)
        _DELTA_WEIGHT_CACHE[key] = mix_t(idx + s64(K_DELTA)) | 1
    return _DELTA_WEIGHT_CACHE[key]


def bit_pattern_int64(m: Tensor) -> Tensor:
    """The entries' bit patterns as int64: float32 -> int32, bf16 -> int16, each sign-extended (a bijection)."""
    assert m.dtype in VIEW_DTYPES, f"fingerprint supports float32 and bfloat16 masks, got {m.dtype}"
    return m.view(VIEW_DTYPES[m.dtype]).to(torch.int64)


def _slab_sum(m_slab: Tensor, W: Tensor) -> Tensor:
    """One slab of level 1: the bit patterns as int64 times the weights, summed over (t, c); (b,) int64."""
    return (bit_pattern_int64(m_slab) * W).sum(dim=(1, 2))


# Optional: `_slab_sum` under torch.compile. Off unless `enable_compile(True)` is called; the
# grid never turns it on unless the timing function showed a gain of at least 0.3 s per cell-pass over E with the
# digests bitwise. The backend wraps Inductor's compiled callable so that every execution of the compiled path is
# counted: a silent fallback to eager (a recompile limit, a guard failure) leaves `COMPILE["calls"]` short of the
# number of slab calls made, which the timing function asserts against (`expected_slab_calls`).
COMPILE: dict[str, Any] = {"enabled": False, "fn": None, "calls": 0, "compiles": 0}


def _counting_backend(gm: Any, example_inputs: Any) -> Any:
    from torch._inductor.compile_fx import compile_fx

    compiled = compile_fx(gm, example_inputs)
    COMPILE["compiles"] += 1

    def run(*args: Any) -> Any:
        COMPILE["calls"] += 1
        return compiled(*args)

    return run


def enable_compile(enable: bool = True, *, cache_size_limit: int = 64) -> dict[str, Any]:
    """Turn the compiled slab on or off and reset its counters. With `fullgraph=True` a graph break raises instead of
    splitting; `dynamic=False` recompiles per shape (six module widths, the full and the short slab), so the dynamo cache
    limit is raised to hold them all rather than fall back to eager."""
    if enable:
        import torch._dynamo

        torch._dynamo.config.cache_size_limit = max(int(torch._dynamo.config.cache_size_limit), cache_size_limit)
        COMPILE["fn"] = torch.compile(_slab_sum, backend=_counting_backend, fullgraph=True, dynamic=False)
    else:
        COMPILE["fn"] = None
    COMPILE.update({"enabled": bool(enable), "calls": 0, "compiles": 0})
    return dict(COMPILE)


def expected_slab_calls(B: int, n_modules: int, n_cells: int, slab: int = SLAB) -> int:
    """The number of `_slab_sum` calls `n_cells` fingerprints on a sub-batch of B make: one per (cell, module, slab)."""
    return n_cells * n_modules * ((B + slab - 1) // slab)


def level1_with_weights(m: Tensor, W: Tensor, slab: int = SLAB) -> Tensor:
    """(B,) int64: h_b = sum_{t,c} W_{t,c} x_{b,t,c} for one module, in slabs along B."""
    assert m.ndim == 3 and W.shape == m.shape[1:] and W.dtype == torch.int64, (tuple(m.shape), tuple(W.shape))
    B = m.shape[0]
    h = torch.empty(B, dtype=torch.int64, device=m.device)
    fn = COMPILE["fn"] if COMPILE["enabled"] else _slab_sum
    for s in range(0, B, slab):
        h[s : s + slab] = fn(m[s : s + slab], W)
    return h


def level1(m: Tensor, slab: int = SLAB) -> Tensor:
    """(B,) int64: h_b for one (B, T, C) mask with the mixed weights of its shape."""
    B, T, C = m.shape
    return level1_with_weights(m, weights(T, C, m.device), slab)


def level1_delta(md: Tensor) -> Tensor:
    """(B,) int64 for a (B, T) residual mask."""
    assert md.ndim == 2, tuple(md.shape)
    x = bit_pattern_int64(md)
    return (x * delta_weights(md.shape[1], md.device)).sum(dim=1)


@dataclass
class Fingerprint:
    """Levels 1 and 2 of one cell on one sub-batch, all on the device: phi (B,), h and hd per module (B,)."""

    phi: Tensor
    h: dict[str, Tensor]
    hd: dict[str, Tensor] | None
    dtype_code: int
    rho: int

    @property
    def keys(self) -> list[str]:
        return list(self.h)


def fingerprint(masks: dict[str, Tensor], delta_masks: dict[str, Tensor] | None, slab: int = SLAB) -> Fingerprint:
    """Levels 1 and 2 for the masks of one cell on one sub-batch (sorted module order)."""
    keys = sorted(masks)
    assert keys, "no masks"
    dtypes = {masks[k].dtype for k in keys}
    assert len(dtypes) == 1, f"all masks must share a dtype, got {dtypes}"
    d = DTYPE_CODES[masks[keys[0]].dtype]
    rho = 0 if delta_masks is None else 1
    if rho:
        assert set(delta_masks) == set(keys), "residual masks must cover exactly the modules of the component masks"
        assert all(delta_masks[k].dtype == masks[k].dtype and delta_masks[k].shape == masks[k].shape[:2] for k in keys)
    B = masks[keys[0]].shape[0]
    assert all(masks[k].shape[0] == B for k in keys)
    h = {k: level1(masks[k], slab) for k in keys}
    hd = {k: level1_delta(delta_masks[k]) for k in keys} if rho else None
    phi = torch.full((B,), s64(mix_py(K_DTYPE + d) + mix_py(K_RES + rho)), dtype=torch.int64, device=masks[keys[0]].device)
    for l, k in enumerate(keys):
        phi = phi + mix_t(h[k] + s64(mix_py(K_MOD + l)))
        if rho:
            phi = phi + mix_t(hd[k] + s64(mix_py(K_MODDELTA + l)))  # type: ignore[index]
    return Fingerprint(phi=phi, h=h, hd=hd, dtype_code=d, rho=rho)


def sequence_salts(seq_index: Tensor | Any, device: torch.device | str) -> Tensor:
    """s_b = mu(kappa_seq + n_b) for the global indices n_b of the sub-batch's sequences."""
    idx = torch.as_tensor(seq_index, dtype=torch.int64, device=device)
    assert idx.ndim == 1
    return mix_t(idx + s64(K_SEQ))


def level3(fp: Fingerprint, seq_index: Tensor | Any) -> tuple[Tensor, dict[str, Tensor], dict[str, Tensor] | None]:
    """F_i and the per-module H_i (and Hd_i) for one sub-batch, as 0-d int64 tensors on the device."""
    s = sequence_salts(seq_index, fp.phi.device)
    assert s.shape == fp.phi.shape, (tuple(s.shape), tuple(fp.phi.shape))
    F_i = mix_t(fp.phi + s).sum()
    H_i = {k: mix_t(v + s).sum() for k, v in fp.h.items()}
    Hd_i = {k: mix_t(v + s).sum() for k, v in fp.hd.items()} if fp.hd is not None else None
    return F_i, H_i, Hd_i


def level3_hex(fp: Fingerprint, seq_index: Tensor | Any) -> dict[str, Any]:
    """Level 3 pulled from the device in one transfer: {"F": hex, "H": {module: hex}, "Hd": {module: hex} | None,
    "phi": [hex per sequence]}."""
    F_i, H_i, Hd_i = level3(fp, seq_index)
    keys = fp.keys
    parts = [F_i.view(1), torch.stack([H_i[k] for k in keys]), fp.phi]
    if Hd_i is not None:
        parts.append(torch.stack([Hd_i[k] for k in keys]))
    flat = torch.cat(parts).cpu().tolist()  # the one synchronization
    n = len(keys)
    out: dict[str, Any] = {"F": to_hex(flat[0]), "H": {k: to_hex(v) for k, v in zip(keys, flat[1 : 1 + n])},
                           "phi": [to_hex(v) for v in flat[1 + n : 1 + n + fp.phi.shape[0]]], "Hd": None}
    if Hd_i is not None:
        off = 1 + n + fp.phi.shape[0]
        out["Hd"] = {k: to_hex(v) for k, v in zip(keys, flat[off : off + n])}
    return out


# ----------------------------------------------------------------------------- the two counts


def mask_counts(m: Tensor, g: Tensor) -> tuple[int, int]:
    """(entries with m != g, entries with m != 1) for one module on one sub-batch, computed where the
    P3 check forms m - g."""
    assert m.shape == g.shape
    return int((m != g).sum()), int((m != 1).sum())


# ----------------------------------------------------------------------------- the SHA-256 oracle


def _tensor_bytes(t: Tensor) -> bytes:
    t = t.detach().cpu().contiguous()
    if t.dtype == torch.bfloat16:
        t = t.view(torch.int16)
    return t.numpy().tobytes()


def sha256_masks(masks: dict[str, Tensor], delta_masks: dict[str, Tensor] | None) -> str:
    """SHA-256 over the mask tensors in sorted module order (dtype, shape, bytes), plus the residual masks: the
    acceptance run's P4 hash, the oracle for unit test T3 and the smoke's G2. Behind a flag that no grid run sets."""
    h = hashlib.sha256()
    for k in sorted(masks):
        t = masks[k]
        h.update(f"{k}|{t.dtype}|{tuple(t.shape)}|".encode())
        h.update(_tensor_bytes(t))
    if delta_masks is None:
        h.update(b"|delta:excluded")
    else:
        for k in sorted(delta_masks):
            t = delta_masks[k]
            h.update(f"|delta:{k}|{t.dtype}|{tuple(t.shape)}|".encode())
            h.update(_tensor_bytes(t))
    return h.hexdigest()
