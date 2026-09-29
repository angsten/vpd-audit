"""The readings of the code-leaning edit on the panels, as pure functions (analysis_s12.py applies them).

For a panel and an edit size k: H, the edit's damage (a row's divergence from the original model averaged over its 512 positions, minus
the rung-0 reference's on the same row, then the mean over rows); T, the usage-matched twins' damage on the same rows (the mean over the
draws per row first, the draws held fixed); rho = H / T. Intervals: a percentile bootstrap over the panel's **documents**, every row of a
drawn document entering together, means in ratio form (the resampled row total over the resampled row count), 10,000 replicates, one
document draw per replicate shared by H, T, and rho at both sizes; the seed (master, "boot_docs", "s12_panel", panel). rho is recomputed
in each replicate; its interval is read only if no replicate's rho is non-finite. A panel with fewer than ten documents has point values
and no interval, and no reading.

The reading (one panel, the damage bar X = 0.05 nats):

- **keep**: at the smaller size the interval of H has its lower end at or above X, and the interval of rho lies entirely above 1 at both
  sizes;
- **drop**: at the smaller size the interval of H lies entirely below X;
- **soften**: anything else; the side of 1 on which each rho lies is reported (above, below, or neither).

Keep asks every one of its three intervals to clear its bar, an intersection-union test, so its error rate is at most the per-interval
level and no correction across the three is applied. The same rule at level 1 - 0.05/3 decides whether one of three candidate panels
may stand in for the decisive one.
"""

from __future__ import annotations

from typing import Any

import numpy as np

from vpd_audit import stats as st
from vpd_audit.stats_s9 import MIN_DOCUMENTS

X = st.X_MATERIAL  # 0.05 nats
M_PANEL = 1  # every panel interval at 95 percent
M_CANDIDATES = 3  # a candidate for the decisive panel's place, one of three: 1 - 0.05/3
KEEP, SOFTEN, DROP = "keep", "soften", "drop"
ABOVE, BELOW, NEITHER, NOT_READ = "above 1", "below 1", "neither", "not read"


def document_resample(doc_ids: np.ndarray, replicates: int, seed_tuple: tuple[Any, ...]) -> st.Resample:
    """Documents drawn with replacement within the panel, as many as it has, all rows of a drawn document together (`s9_checks.document_resample`)."""
    from vpd_audit.s9_checks import document_resample as _dr

    return _dr(np.asarray(doc_ids), replicates, tuple(seed_tuple))


def ratio_mean_replicates(resample: st.Resample, v: np.ndarray) -> np.ndarray:
    """(R,) row-weighted means in ratio form: the resampled row total over the resampled row count."""
    from vpd_audit.s9_checks import doc_means

    return doc_means(resample, np.asarray(v, dtype=np.float64))


def rho_side(interval: list[float] | None) -> str:
    """The side of 1 on which an interval of rho lies."""
    if interval is None or not np.all(np.isfinite(interval)):
        return NOT_READ
    if interval[0] > 1.0:
        return ABOVE
    if interval[1] < 1.0:
        return BELOW
    return NEITHER


def edit_statistics(h: np.ndarray, t: np.ndarray, resample: st.Resample | None, n_documents: int, *, m: int = M_PANEL) -> dict[str, Any]:
    """One panel and edit size: h (N,) the group's damage per row, t (N,) the twins' per row (their mean over the draws). Point values,
    and with `resample` and at least ten documents the intervals of H, T, and rho at level 1 - 0.05/m from that one resample, rho per
    replicate from the same document draw, and the share of replicates whose rho is not finite (rho's interval is read only if it is 0)."""
    h, t = np.asarray(h, dtype=np.float64), np.asarray(t, dtype=np.float64)
    assert h.ndim == 1 and h.shape == t.shape, (h.shape, t.shape)
    H, T = float(h.mean()), float(t.mean())
    out: dict[str, Any] = {"H": H, "T": T, "rho": float(H / T) if T != 0 else float("nan"), "n_rows": int(h.size), "n_documents": int(n_documents), "m": int(m),
                           "H_interval": None, "T_interval": None, "rho_interval": None, "rho_nonfinite_share": None, "rho_readable": False}
    if resample is None or n_documents < MIN_DOCUMENTS:
        return out
    assert resample.n == h.size
    Hr, Tr = ratio_mean_replicates(resample, h), ratio_mean_replicates(resample, t)
    with np.errstate(divide="ignore", invalid="ignore"):
        rho_r = np.where(Tr != 0, Hr / np.where(Tr != 0, Tr, 1.0), np.nan)
    nonfinite = float((~np.isfinite(rho_r)).mean())
    out.update({"H_interval": list(st.percentile_interval(Hr, m)), "T_interval": list(st.percentile_interval(Tr, m)), "rho_nonfinite_share": nonfinite, "rho_readable": nonfinite == 0.0,
                "rho_interval": list(st.percentile_interval(rho_r, m)) if nonfinite == 0.0 else None})
    return out


def reading(small: dict[str, Any], large: dict[str, Any], *, x: float = X) -> dict[str, Any]:
    """keep, drop, or soften from the statistics at the smaller and the larger size (`edit_statistics`, at one level). None where the panel
    has no interval (fewer than ten documents). The side of 1 of each rho is returned beside the word."""
    sides = {"small": rho_side(small["rho_interval"] if small["rho_readable"] else None), "large": rho_side(large["rho_interval"] if large["rho_readable"] else None)}
    h_iv = small["H_interval"]
    if h_iv is None:
        return {"word": None, "reason": f"fewer than {MIN_DOCUMENTS} documents: point values only", "rho_sides": sides}
    if h_iv[1] < x:
        return {"word": DROP, "reason": f"the interval of H at the smaller size lies entirely below {x:g}", "rho_sides": sides}
    if h_iv[0] >= x and sides["small"] == ABOVE and sides["large"] == ABOVE:
        return {"word": KEEP, "reason": f"the interval of H at the smaller size starts at or above {x:g} and rho lies above 1 at both sizes", "rho_sides": sides}
    return {"word": SOFTEN, "reason": "neither keep nor drop", "rho_sides": sides}
