"""The on-device fingerprint, on CPU: T1 the Python big-integer reference; T2 chunk and layout
invariance; T3 equivalence with SHA-256 on pairs; T4 determinism, the hex round trip, and the two counts on a
hand-counted fixture. Three synthetic float32 modules of shapes (2, 5, 7), (2, 5, 7), (2, 5, 11): two share a
shape so the module-exchange case can be tested; the sizes are otherwise pairwise distinct."""

import numpy as np
import torch

from vpd_audit.fingerprint import (
    C1,
    C2,
    DTYPE_CODES,
    K_DELTA,
    K_DTYPE,
    K_MOD,
    K_MODDELTA,
    K_RES,
    K_SEQ,
    K_W,
    SALTS,
    Fingerprint,
    fingerprint,
    from_hex,
    level1,
    level1_with_weights,
    level3_hex,
    mask_counts,
    mix_py,
    mix_t,
    s64,
    sha256_masks,
    sum_hex,
    to_hex,
    u64,
)
from vpd_audit.masks import apply_binary_source
from vpd_audit.reference import ALL_CONDITIONS, build_condition_masks

T = 5
SHAPES = {"m.a": 7, "m.b": 7, "m.c": 11}


def _masks(seed: int = 0, B: int = 2) -> dict[str, torch.Tensor]:
    gen = torch.Generator().manual_seed(seed)
    out = {}
    for k, C in SHAPES.items():
        m = torch.rand((B, T, C), generator=gen)
        m[m < 0.2] = 0.0  # exact zeros, like the clamp
        m[0, 0, 0] = 0.0
        m[0, 1, 1] = 1.0
        m[1, 2, 2] = -0.0  # a negative zero: equal as a float, distinct as a bit pattern
        m[1, 3, 3] = 1.0
        out[k] = m
    return out


def _deltas(seed: int = 1, B: int = 2) -> dict[str, torch.Tensor]:
    gen = torch.Generator().manual_seed(seed)
    out = {}
    for k in SHAPES:
        d = torch.rand((B, T), generator=gen)
        d[0, 0] = 0.0
        d[1, 1] = 1.0
        out[k] = d
    return out


# --------------------------------------------------------------------------- the Python reference (T1)


def _bits(t: torch.Tensor) -> list:
    if t.dtype == torch.float32:
        return t.numpy().view(np.int32).astype(np.int64).tolist()
    assert t.dtype == torch.bfloat16
    return t.view(torch.int16).numpy().astype(np.int64).tolist()


def ref_digests(masks: dict[str, torch.Tensor], deltas: dict[str, torch.Tensor] | None, seq_index: list[int]) -> dict:
    """Levels 1 to 3 in Python big integers, from the defining formulas alone."""
    keys = sorted(masks)
    B = masks[keys[0]].shape[0]
    d = DTYPE_CODES[masks[keys[0]].dtype]
    rho = 0 if deltas is None else 1
    h: dict[str, list[int]] = {}
    hd: dict[str, list[int]] = {}
    for k in keys:
        Bk, Tk, Ck = masks[k].shape
        W = [[(mix_py(t * Ck + c + K_W) | 1) for c in range(Ck)] for t in range(Tk)]
        x = _bits(masks[k])
        h[k] = [u64(sum(W[t][c] * x[b][t][c] for t in range(Tk) for c in range(Ck))) for b in range(Bk)]
        if rho:
            Wd = [(mix_py(t + K_DELTA) | 1) for t in range(Tk)]
            xd = _bits(deltas[k])
            hd[k] = [u64(sum(Wd[t] * xd[b][t] for t in range(Tk))) for b in range(Bk)]
    phi = []
    for b in range(B):
        v = mix_py(K_DTYPE + d) + mix_py(K_RES + rho)
        for l, k in enumerate(keys):
            v += mix_py(u64(h[k][b] + mix_py(K_MOD + l)))
            if rho:
                v += mix_py(u64(hd[k][b] + mix_py(K_MODDELTA + l)))
        phi.append(u64(v))
    s = [mix_py(K_SEQ + n) for n in seq_index]
    F = u64(sum(mix_py(u64(phi[b] + s[b])) for b in range(B)))
    H = {k: u64(sum(mix_py(u64(h[k][b] + s[b])) for b in range(B))) for k in keys}
    Hd = {k: u64(sum(mix_py(u64(hd[k][b] + s[b])) for b in range(B))) for k in keys} if rho else None
    return {"phi": phi, "h": h, "hd": hd if rho else None, "F": F, "H": H, "Hd": Hd}


def _hx(v: int) -> str:
    return format(u64(v), "016x")


def test_t1_mixer_constants_and_reference_values():
    # splitmix64 finalizer, Vigna's constants and shifts; mu(0) = 0 and a bijection on small inputs
    assert C1 == 0xBF58476D1CE4E5B9 and C2 == 0x94D049BB133111EB and len(set(SALTS.values())) == 7
    assert mix_py(0) == 0
    vals = [mix_py(i) for i in range(2000)]
    assert len(set(vals)) == 2000
    z = torch.arange(-1000, 1000, dtype=torch.int64)
    assert [u64(int(v)) for v in mix_t(z)] == [mix_py(int(i)) for i in range(-1000, 1000)]
    # the worked example: invented odd weights, one module with T = 2, C = 2
    W = torch.tensor([[3, 5], [7, 9]], dtype=torch.int64)
    m = torch.tensor([[[1.0, 0.0], [0.5, 1.0]]])
    assert int(level1_with_weights(m, W)) == 20182990848
    m2 = m.clone()
    m2[0, 0, 1] = -0.0
    assert int(level1_with_weights(m2, W)) - 20182990848 == 5 * (-2147483648)
    m3 = m.clone()
    m3[0, 0, 0], m3[0, 1, 0] = 0.5, 1.0
    assert abs(int(level1_with_weights(m3, W)) - 20182990848) == 33554432  # (1065353216 - 1056964608) * (7 - 3)
    m4 = m.clone()
    m4[0, 0, 0], m4[0, 1, 1] = 1.0, 1.0  # the two 1.0 entries swapped: the tensor is unchanged
    assert int(level1_with_weights(m4, W)) == 20182990848


def test_t1_torch_agrees_with_the_python_reference_bitwise():
    for dtype in (torch.float32, torch.bfloat16):
        for deltas in (None, _deltas()):
            masks = {k: v.to(dtype) for k, v in _masks().items()}
            dl = {k: v.to(dtype) for k, v in deltas.items()} if deltas is not None else None
            seq = [7, 3]  # global indices, not 0..B-1
            fp = fingerprint(masks, dl)
            ref = ref_digests(masks, dl, seq)
            assert [to_hex(fp.phi[b]) for b in range(2)] == [_hx(v) for v in ref["phi"]]
            for k in SHAPES:
                assert [to_hex(fp.h[k][b]) for b in range(2)] == [_hx(v) for v in ref["h"][k]]
                if dl is not None:
                    assert [to_hex(fp.hd[k][b]) for b in range(2)] == [_hx(v) for v in ref["hd"][k]]
            out = level3_hex(fp, seq)
            assert out["F"] == _hx(ref["F"]) and out["H"] == {k: _hx(v) for k, v in ref["H"].items()}
            assert out["phi"] == [_hx(v) for v in ref["phi"]]
            assert (out["Hd"] is None) == (dl is None)
            if dl is not None:
                assert out["Hd"] == {k: _hx(v) for k, v in ref["Hd"].items()}
    # level 4: the modular sum of two sub-batches' F equals the reference over the union
    m6, d6 = _masks(seed=3, B=6), _deltas(seed=4, B=6)
    ref_all = ref_digests(m6, d6, list(range(10, 16)))
    parts = [level3_hex(fingerprint({k: v[a:b] for k, v in m6.items()}, {k: v[a:b] for k, v in d6.items()}), list(range(10 + a, 10 + b)))["F"] for a, b in ((0, 2), (2, 6))]
    assert sum_hex(parts) == _hx(ref_all["F"])


# --------------------------------------------------------------------------- T2


def test_t2_slab_and_layout_invariance():
    masks = _masks(seed=5, B=6)
    for k in SHAPES:
        h_full = level1(masks[k], slab=6)
        assert torch.equal(level1(masks[k], slab=1), h_full) and torch.equal(level1(masks[k], slab=3), h_full)
    deltas = _deltas(seed=6, B=6)
    whole = level3_hex(fingerprint(masks, deltas), list(range(6)))
    for cuts in (((0, 2), (2, 4), (4, 6)), ((0, 4), (4, 6))):
        parts = [level3_hex(fingerprint({k: v[a:b] for k, v in masks.items()}, {k: v[a:b] for k, v in deltas.items()}), list(range(a, b))) for a, b in cuts]
        assert sum_hex([p["F"] for p in parts]) == whole["F"]
        for k in SHAPES:
            assert sum_hex([p["H"][k] for p in parts]) == whole["H"][k] and sum_hex([p["Hd"][k] for p in parts]) == whole["Hd"][k]
        assert [x for p in parts for x in p["phi"]] == whole["phi"]
    # the same content at different global indices gives a different F (the sequence salt)
    assert level3_hex(fingerprint(masks, deltas), list(range(100, 106)))["F"] != whole["F"]


# --------------------------------------------------------------------------- T3


def _digest(masks, deltas):
    return level3_hex(fingerprint(masks, deltas), list(range(next(iter(masks.values())).shape[0])))


def _same(a_masks, a_deltas, b_masks, b_deltas) -> tuple[bool, bool, dict, dict]:
    sha_eq = sha256_masks(a_masks, a_deltas) == sha256_masks(b_masks, b_deltas)
    da, db = _digest(a_masks, a_deltas), _digest(b_masks, b_deltas)
    return sha_eq, da["F"] == db["F"], da, db


def test_t3_equivalence_with_sha256_on_pairs():
    base = _masks()
    deltas = _deltas()
    # an identical copy: equal under both
    copy = {k: v.clone() for k, v in base.items()}
    sha_eq, fp_eq, _, _ = _same(base, None, copy, None)
    assert sha_eq and fp_eq
    # one entry moved one ulp
    m = {k: v.clone() for k, v in base.items()}
    m["m.c"][0, 2, 3] = torch.nextafter(m["m.c"][0, 2, 3], torch.tensor(1.0))
    sha_eq, fp_eq, da, db = _same(base, None, m, None)
    assert not sha_eq and not fp_eq and da["phi"][0] != db["phi"][0] and da["phi"][1] == db["phi"][1] and da["H"]["m.c"] != db["H"]["m.c"] and da["H"]["m.a"] == db["H"]["m.a"]
    # 0.0 -> -0.0
    m = {k: v.clone() for k, v in base.items()}
    assert float(m["m.a"][0, 0, 0]) == 0.0
    m["m.a"][0, 0, 0] = -0.0
    sha_eq, fp_eq, _, _ = _same(base, None, m, None)
    assert not sha_eq and not fp_eq
    # two entries with distinct values swapped within one (l, b)
    m = {k: v.clone() for k, v in base.items()}
    a, b = m["m.b"][1, 0, 0].item(), m["m.b"][1, 4, 6].item()
    assert a != b
    m["m.b"][1, 0, 0], m["m.b"][1, 4, 6] = b, a
    sha_eq, fp_eq, _, _ = _same(base, None, m, None)
    assert not sha_eq and not fp_eq
    # two whole positions swapped, both binary with the same count of ones (a permutation-invariant summary would miss it)
    m = {k: v.clone() for k, v in base.items()}
    m["m.c"][0, 1] = torch.tensor([1, 0, 1, 0, 0, 0, 0, 0, 1, 0, 0], dtype=torch.float32)
    m["m.c"][0, 3] = torch.tensor([0, 1, 0, 0, 1, 0, 0, 1, 0, 0, 0], dtype=torch.float32)
    sw = {k: v.clone() for k, v in m.items()}
    sw["m.c"][0, 1], sw["m.c"][0, 3] = m["m.c"][0, 3].clone(), m["m.c"][0, 1].clone()
    assert torch.equal(m["m.c"][0].sum(0), sw["m.c"][0].sum(0)) and torch.equal(m["m.c"][0].sum(1), sw["m.c"][0].sum(1))
    sha_eq, fp_eq, _, _ = _same(m, None, sw, None)
    assert not sha_eq and not fp_eq
    # two sequences swapped within one module
    m = {k: v.clone() for k, v in base.items()}
    m["m.a"] = m["m.a"][[1, 0]].clone()
    sha_eq, fp_eq, da, db = _same(base, None, m, None)
    assert not sha_eq and not fp_eq and da["phi"] != db["phi"]
    # the two equal-shape modules exchanged: the cell digest differs; the module digests exchange
    m = dict(base)
    m["m.a"], m["m.b"] = base["m.b"], base["m.a"]
    assert not torch.equal(base["m.a"], base["m.b"])
    sha_eq, fp_eq, da, db = _same(base, None, m, None)
    assert not sha_eq and not fp_eq and da["H"]["m.a"] == db["H"]["m.b"] and da["H"]["m.b"] == db["H"]["m.a"] and da["H"]["m.c"] == db["H"]["m.c"]
    # residual included against excluded, identical component masks
    sha_eq, fp_eq, da, db = _same(base, None, base, deltas)
    assert not sha_eq and not fp_eq and da["H"] == db["H"] and da["Hd"] is None and db["Hd"] is not None
    # residual included, one residual entry changed
    d2 = {k: v.clone() for k, v in deltas.items()}
    d2["m.b"][1, 4] = 0.5 if float(d2["m.b"][1, 4]) != 0.5 else 0.25
    sha_eq, fp_eq, da, db = _same(base, deltas, base, d2)
    assert not sha_eq and not fp_eq and da["H"] == db["H"] and da["Hd"]["m.b"] != db["Hd"]["m.b"] and da["Hd"]["m.a"] == db["Hd"]["m.a"]
    # the same values as bf16 against float32
    m_bf = {k: v.to(torch.bfloat16) for k, v in base.items()}
    m_f32 = {k: v.float() for k, v in m_bf.items()}
    assert all(torch.equal(m_f32[k], m_bf[k].float()) for k in SHAPES)
    sha_eq, fp_eq, _, _ = _same(m_bf, None, m_f32, None)
    assert not sha_eq and not fp_eq
    # the reference-condition kinds built from one synthetic g, pairwise: SHA equality must equal fingerprint equality
    g = _masks(seed=11)
    built = {}
    for cond in ALL_CONDITIONS:
        if cond.kind == "target":
            continue
        for draw in range(2) if cond.per_draw else [0]:
            built[f"{cond.name}/k{draw}"] = build_condition_masks(cond, g, SHAPES, draw=draw, subbatch_index=0, master_seed=0)
    names = sorted(built)
    assert len(names) == 9 + 3 * 2  # 9 single-draw conditions and 3 per-draw ones at two draws
    equal_pairs = set()
    for i, a_name in enumerate(names):
        for b_name in names[i + 1 :]:
            sha_eq, fp_eq, _, _ = _same(*built[a_name], *built[b_name])
            assert sha_eq == fp_eq, (a_name, b_name)
            if sha_eq:
                equal_pairs.add(frozenset((a_name, b_name)))
    # this g has no value in (0, 0.2), so 1[g > 0] and 1[g > 0.1] are the same mask: SHA-256 and the fingerprint agree
    # that exactly this pair coincides, and every other pair differs
    assert equal_pairs == {frozenset(("rounded_0/k0", "rounded_0.1/k0"))}
    # the two residual test cells against their partners: importances_delta1 shares H with importances, differs in F
    sha_eq, fp_eq, da, db = _same(*built["importances/k0"], *built["importances_delta1/k0"])
    assert not sha_eq and not fp_eq and da["H"] == db["H"]
    for k in range(2):
        d0, du, d1 = _digest(*built[f"stochastic/k{k}"]), _digest(*built[f"stochastic_delta/k{k}"]), _digest(*built[f"stochastic_delta1/k{k}"])
        assert d0["H"] == du["H"] == d1["H"] and du["Hd"] != d1["Hd"] and len({d0["F"], du["F"], d1["F"]}) == 3


# --------------------------------------------------------------------------- T4


def test_t4_determinism_hex_and_the_two_counts():
    masks, deltas = _masks(), _deltas()
    a, b = _digest(masks, deltas), _digest(masks, deltas)
    assert a == b
    for v in (0, 1, -1, 2**63 - 1, -(2**63), 123456789012345, -987654321098765):
        assert from_hex(to_hex(v)) == u64(v) and len(to_hex(v)) == 16 and to_hex(v) == to_hex(torch.tensor(v, dtype=torch.int64))
    assert from_hex(to_hex(s64(2**64 - 5))) == 2**64 - 5
    # the hand-counted fixture: one matrix with four subcomponents, two positions; hand-counted values
    g = torch.tensor([[[1.0, 0.7, 0.0, 0.0], [0.2, 0.0, 0.9, 0.0]]])
    union = apply_binary_source(g, torch.tensor([0.0, 1.0, 1.0, 0.0]))
    assert torch.equal(union, torch.tensor([[[1.0, 1.0, 1.0, 0.0], [0.2, 1.0, 1.0, 0.0]]]))
    assert mask_counts(union, g) == (4, 3)
    erase = apply_binary_source(g, torch.tensor([1.0, 0.0, 0.0, 1.0]))
    assert torch.equal(erase, torch.tensor([[[1.0, 0.7, 0.0, 1.0], [1.0, 0.0, 0.9, 1.0]]]))
    assert mask_counts(erase, g) == (3, 4)
    hard_zero = torch.tensor([[[1.0, 0.0, 0.0, 1.0], [1.0, 0.0, 0.0, 1.0]]])
    assert mask_counts(hard_zero, g) == (5, 4)
    assert mask_counts(g, g) == (0, 7) and mask_counts(torch.ones_like(g), g) == (7, 0)
    # a Fingerprint carries what the schema needs
    fp = fingerprint(masks, deltas)
    assert isinstance(fp, Fingerprint) and fp.dtype_code == 32 and fp.rho == 1 and fp.keys == sorted(SHAPES)


# --------------------------------------------------------------------------- the compiled slab, gated on T1


def test_t1_compiled_slab_is_bitwise_eager_and_the_python_reference():
    """`level1_with_weights` under torch.compile gives the same h, phi, F and H as eager and as the big-integer reference,
    on the T1 example (invented odd weights) and on the synthetic masks in both dtypes with the residual on and off; the
    counting backend shows the compiled path was executed, and turning it off restores eager. Skipped where
    torch.compile cannot run (no C compiler for Inductor on this platform)."""
    from vpd_audit.fingerprint import COMPILE, enable_compile, expected_slab_calls

    W = torch.tensor([[3, 5], [7, 9]], dtype=torch.int64)
    m = torch.tensor([[[1.0, 0.0], [0.5, 1.0]]])
    try:
        enable_compile(True)
        h = level1_with_weights(m, W)
    except Exception as e:  # noqa: BLE001
        enable_compile(False)
        pytest.skip(f"torch.compile is not usable here: {type(e).__name__}: {str(e)[:120]}")
    try:
        assert int(h) == 20182990848 and COMPILE["calls"] == 1 and COMPILE["compiles"] == 1
        for dtype in (torch.float32, torch.bfloat16):
            for deltas in (None, _deltas(seed=9, B=6)):
                masks = {k: v.to(dtype) for k, v in _masks(seed=8, B=6).items()}
                dl = {k: v.to(dtype) for k, v in deltas.items()} if deltas is not None else None
                before = COMPILE["calls"]
                fp_c = fingerprint(masks, dl, slab=4)  # slabs of 4 and 2: two shapes per module
                assert COMPILE["calls"] - before == expected_slab_calls(6, len(SHAPES), 1, slab=4)
                enable_compile(False)
                fp_e = fingerprint(masks, dl, slab=4)
                enable_compile(True)
                assert torch.equal(fp_c.phi, fp_e.phi) and all(torch.equal(fp_c.h[k], fp_e.h[k]) for k in SHAPES)
                seq = [11, 5, 2, 9, 0, 7]
                ref = ref_digests(masks, dl, seq)
                out = level3_hex(fp_c, seq)
                assert out["F"] == _hx(ref["F"]) and out["H"] == {k: _hx(v) for k, v in ref["H"].items()} and out["phi"] == [_hx(v) for v in ref["phi"]]
    finally:
        enable_compile(False)
    assert COMPILE["fn"] is None and not COMPILE["enabled"]
    assert int(level1_with_weights(m, W)) == 20182990848 and COMPILE["calls"] == 0
