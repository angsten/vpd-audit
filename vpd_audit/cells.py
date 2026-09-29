"""The grid's cells: the coordinates of a cell, the enumeration of the three
tiers, the sub-batch-outer loop over an evaluation set, and the cell table.

A `Cell` is one masked forward pass over one evaluation set at one point of the grid: run, family, evaluation set,
threshold tau, background, residual setting, draw, rung (0 to 8, the adaptive 5a and 6a, or a sub-rung S4, S16,
S64), control (none, plain, or complement-drawn), and tier. `enumerate_cells` writes down the three pre-registered
tiers exactly: rungs 1 to 7 under eight draws; rungs 0 and 8 once under a primary background and per draw under a
uniform one (rung 0 is a reference condition and appears as one); the sub-rungs once; the matched-random control
of every verdict-tier family, the complement-drawn control of the code-specific set and its sub-rungs, and the
plain control beside it; tau = 0.5 for everything above, the non-primary residual settings, the tau = 0 union, the
rounded-own-g union and its control, the donor-side pass (rungs 4 and 7 of every union draw applied
to the donor sequences themselves, with their own importances-as-masks and rounded-tau references), the domain
families at their primary configuration on E, and, marked optional, the uniform-donor soft erase on E_lab. The
counts per tier and in E-equivalent passes are reported (6,500 to 7,000 together were expected in advance).

The loop puts sub-batches of the evaluation set outside and cells inside, as `run_references` does: per sub-batch,
g and the target logits once; then per cell the masks from its source and background (the uniform background
regenerated from (master, "u", k, i)), the forward, the divergence, the switched mass and, for hard-zero cells, the
over-removal, the first touched positions at tau_q = 0.1 and 0 with the touched counts, and the
clean-prefix sum and the conditional damage d_b against the chain's rung 0, whose float32 divergence
is held for the sub-batch because the references run first, and the per-sequence rows. Sources are built once
per tier from the caches before the loop (`build_sources`). The marker keeps F_i per (cell, sub-batch) and running
sums per cell; the cell table `cells.parquet` is written at the end with the coordinates,
the seed tuples, n_on per matrix and its sum, the source hash, the control's alive hash, mask_fp_cell,
mask_fp_modules, and the two counts.

Tier 5 is added additively (every earlier path runs as it did; tests/test_tier5_cells.py holds tiers 1 to 4
to their enumeration on main, tests/test_tier5_loop.py the loop's values): the same-domain union arms, the per-text families
`self_union` and `partner_union` (one named set per text, through the per-text siblings of `family_masks`), the external-model
cells (no mask; a comparison model's predictions through the same divergence function), and, when the loop is handed a
`tier5.StoreRun`, the plain-terms extras of `plain_terms.py`, the canary, and the D_unif gate.

Tier 6 is added additively: the binary union in two forms (`rounded0_own_g`, new; `rounded_own_g` at 16 tokens, its 8
and 64 being tier 3's cells, selected by predicate), the primary's look-alike control, and the self-merge in both binary forms through
the `Cell.own_round` field (None, the default, is tier 5's self-merge, name and mask unchanged).
"""

from __future__ import annotations

import json
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import torch
from torch import Tensor

from vpd_audit.constants import IMPORTANCE_CHUNK, SEQ_LEN
from vpd_audit.fingerprint import FINGERPRINT_SPEC, level3_hex, sum_hex
from vpd_audit.importances import compute_importances, module_keys
from vpd_audit.masks import first_touched, masked_forward, over_removal, switched_mass, switched_mass_per_text, uniform_background
from vpd_audit.metrics import per_position_kl_from_probs, per_sequence_ce, summarize_kl, target_softmax_chunks
from vpd_audit.reference import CONDITIONS, CONDITION_BY_NAME, Condition, build_condition_masks, cell_key
from vpd_audit.results import RunManifest, SubbatchStore, code_commits
from vpd_audit.sources import (
    BRIDGING_RUNGS,
    INTERMEDIATE_RUNGS,
    SUB_RUNGS,
    Cache,
    DonorSet,
    code_specific_source,
    donor_set,
    dumps_seed,
    family_masks,
    matched_random_source,
    n_on,
    never_named_set,
    never_named_source,
    rho_tensors,
    rung_order,
    soft_erase_source,
    source_hash,
    sub_rung_sets,
    union_source,
)
from vpd_audit.sources import LEVELS, POSITION_SUB_RUNGS, level_source_hash, positive_label_counts, ranked_never_named_source
from vpd_audit.sources import PER_TEXT_FAMILIES, family_masks_per_text, rho_tensors_per_text  # tier 5
from vpd_audit.sources import OWN_ROUND_VALUES, ROUNDED0_FAMILY  # tier 6

K_DRAWS = 8
RUNS = ("main", "control")
TAU_PRIMARY = 0.1
E_SIZE = 1024
E_LAB_SIZE = 512
SET_SIZES = {"E": E_SIZE, "E_lab": E_LAB_SIZE, "D_unif": E_SIZE}  # D_unif: an evaluation set of tier 5 only


@dataclass(frozen=True)
class Cell:
    run: str
    family: str  # union | soft_erase | hard_zero | rounded_own_g | code_specific_hard | code_specific_soft | reference; tier 5: self_union | partner_union | external; tier 6: rounded0_own_g
    eval_set: str  # E | E_lab | donors (the donor-side pass, on the donor sequences of the cell's own draw and rung); tier 5: D_unif as well (the self-merge)
    donor_pool: str | None  # D_unif | D_code | None; tier 5: D_prose for the union family; the partner pool (E | E_lab | D_unif) for the per-text families
    tau: float | None
    background: str  # r0 | r1 | ones | uniform | none
    delta: str  # excluded | included
    draw: int
    rung: str  # "0".."8", "5a", "6a", "S4", "S16", "S64"
    control: str  # none | plain | complement | marginal (tier 4: the marginal-matched control) | usage (tier 4: the code-leaning chain's usage-matched twins)
    tier: int
    condition: str | None = None  # the reference condition's name for family == "reference"
    optional: bool = False
    donor_side_reference: str | None = None  # "importances" | "rounded" for the donor-side pass's two references
    # the level cells' s; the descriptive flag of rungs outside the pre-registered comparison count (filtered in
    # analysis.py before a chain reaches stats.py); the ranked never-named pair's ordering key and end
    level: float | None = None
    descriptive: bool = False
    rank_key: str | None = None  # "weight_norm" | "positive_count"
    rank_end: str | None = None  # "top" | "bottom"
    replicate: int = 0  # the marginal control's replicate; 0 leaves every existing name as it is
    # tier 5: the partner arm and its rotation's shift (partner_union), and the comparison
    # model of an external-model cell; the defaults leave every existing name as it is
    shift: int = 0
    arm: str | None = None  # "within" | "source" | "general"
    model: str | None = None  # a key of external_models.MODELS
    # tier 6: the binary self-merge, the text's own labels rounded at this threshold before the merge (0.0 or 0.1);
    # None is the fractional self-merge of tier 5, and the default leaves every existing name as it is
    own_round: float | None = None

    @property
    def name(self) -> str:
        if self.family == "reference":
            return f"{self.run}/{self.eval_set}/ref/{cell_key(CONDITION_BY_NAME[self.condition], self.draw)}"  # type: ignore[index]
        if self.family == "external":  # no source, no mask: the comparison model's own predictions on the set
            return f"{self.run}/{self.eval_set}/external/{self.model}"
        tau = "none" if self.tau is None else f"tau{self.tau:g}"
        ctl = "" if self.control == "none" else f"/ctl-{self.control}"
        side = "" if self.donor_side_reference is None else f"/donorref-{self.donor_side_reference}"
        lvl = "" if self.level is None else f"/s{self.level:g}"
        rank = "" if self.rank_key is None else f"/{self.rank_key}-{self.rank_end}"
        repl = "" if self.replicate == 0 else f"/rep{self.replicate}"
        arm = "" if self.arm is None else f"/arm-{self.arm}"
        shift = "" if self.shift == 0 else f"/shift{self.shift}"
        own = "" if self.own_round is None else f"/ownround{self.own_round:g}"
        return f"{self.run}/{self.eval_set}/{self.family}/{self.donor_pool}/{tau}/{self.background}/{self.delta[:4]}/k{self.draw}/r{self.rung}{ctl}{side}{lvl}{rank}{repl}{arm}{shift}{own}"

    @property
    def e_equivalent(self) -> float:
        """Passes over E this cell costs; the accounting is for the paper's grid (E, E_lab, the donor side); NaN elsewhere."""
        if self.eval_set == "donors":
            return (1 if self.rung == "4" else 64) / E_SIZE
        return SET_SIZES[self.eval_set] / E_SIZE if self.eval_set in SET_SIZES else float("nan")

    @property
    def is_hard_zero(self) -> bool:
        return self.family in HARD_ZERO_FAMILIES

    @property
    def erase_family(self) -> bool:
        return self.family in ("soft_erase", "code_specific_soft") + HARD_ZERO_FAMILIES


HARD_ZERO_FAMILIES: tuple[str, ...] = ("hard_zero", "code_specific_hard", "never_named_hard", "never_named_ranked", "code_leaning_hard")
# the mask path each family takes in family_masks: the code-specific and never-named families are hard-zero or soft-erase masks of their own sets
FAMILY_MASK_KIND: dict[str, str] = {"code_specific_hard": "hard_zero", "code_specific_soft": "soft_erase", "never_named_hard": "hard_zero", "never_named_ranked": "hard_zero", "code_leaning_hard": "hard_zero"}
RANKED_RUNS: tuple[str, ...] = ("main", "simplestories")  # the ranked pair on the main run only (and the stand-in, for its dry run)
RANK_KEYS: tuple[str, ...] = ("weight_norm", "positive_count")
RANK_ENDS: tuple[str, ...] = ("top", "bottom")
RANKED_RUNGS: tuple[str, ...] = INTERMEDIATE_RUNGS + tuple(BRIDGING_RUNGS)  # the ladder's nine rungs; the whole set is the never-named chain's rung 8


# the launch subsets of tier 3, as predicates on a cell (grid --tiers 3 --subset <name>), each into
# stores named <group>__<subset>.
def _curve1(c: "Cell", tau: float) -> bool:
    return c.family == "union" and c.eval_set == "E" and c.donor_pool == "D_unif" and c.tau == tau and c.background == "r0" and c.delta == "excluded" and c.control in ("none", "plain")


SUBSETS: dict[str, Any] = {
    "never_named": lambda c: c.family == "never_named_hard",
    "levels": lambda c: c.family == "level",
    "ranked": lambda c: c.family == "never_named_ranked",
    "curve1_extra": lambda c: (c.descriptive and _curve1(c, 0.1)) or _curve1(c, 0.5),  # the descriptive position rungs 2a, 2b; curve 1 at tau = 0.5 with its plain control
    "tau0_union": lambda c: _curve1(c, 0.0),
    "editing_extra": lambda c: (c.family == "code_specific_hard" and c.eval_set == "E_lab" and c.tau == 0.5 and c.control in ("none", "complement"))
    or (c.family == "code_specific_hard" and c.eval_set == "E" and c.tau == 0.1 and c.control == "none")
    or (c.family == "code_specific_soft" and c.eval_set == "E_lab" and c.tau == 0.1 and c.control == "none"),
    "donor_side": lambda c: c.eval_set == "donors",
}


# tier 4, on the main run (and the stand-in, for its dry run); never on the control run. Its two
# launch subsets are kept beside SUBSETS, not in it: a test asserts that every entry of SUBSETS selects tier-3 cells.
TIER_4 = 4
TIER_4_RUNS: tuple[str, ...] = ("main", "simplestories")
MARGINAL_RUNGS: tuple[str, ...] = ("1", "2", "2a", "2b", "3")  # curve 1's marginal control: 1, 8, 16, 32, 64 donor positions
MARGINAL_REPLICATE_1_RUNGS: tuple[str, ...] = ("1", "2")
MARGINAL_OTHER_FAMILY_RUNGS: tuple[str, ...] = ("1", "2", "3")  # the soft erase's and curve 2's
CODE_LEANING_RUNG_PREFIX = "G"  # a code-leaning rung is named by its size: G16, G64, ..., the whole group, then the descriptive rungs down to the wide set
SUBSETS_TIER_4: dict[str, Any] = {
    "marginal": lambda c: c.tier == TIER_4 and c.control == "marginal",
    "code_leaning": lambda c: c.tier == TIER_4 and c.family == "code_leaning_hard",
}
ALL_SUBSETS: dict[str, Any] = {**SUBSETS, **SUBSETS_TIER_4}  # what a launch's --subset may name


def code_leaning_rung(size: int) -> str:
    return f"{CODE_LEANING_RUNG_PREFIX}{int(size)}"


def code_leaning_size(rung: str) -> int:
    assert rung.startswith(CODE_LEANING_RUNG_PREFIX) and rung[1:].isdigit(), rung
    return int(rung[1:])


def marginal_canaries(run: str) -> list[Cell]:
    """The marginal store's two canaries: curve 1's union and its plain control at rung 2, draw 0, rerun inside the marginal store and
    asserted bitwise against tiers 1 and 2 by the analysis. They keep their own names and tiers, so they are added per store
    (as the references are), never enumerated twice."""
    return [Cell(run, "union", "E", "D_unif", TAU_PRIMARY, "r0", "excluded", 0, "2", "none", 1), Cell(run, "union", "E", "D_unif", TAU_PRIMARY, "r0", "excluded", 0, "2", "plain", 2)]


def tier_4_cells(run: str, draws: int, code_leaning: list[tuple[int, bool]] | None) -> list[Cell]:
    """The marginal-matched control (E, donors from D_unif, tau = 0.1, residual excluded):
    curve 1's at rungs 1, 2, 2a, 2b, 3, a second replicate at rungs 1 and 2, the soft erase's (background ones) and curve 2's
    (uniform background, draw k under its own u^(k)) at rungs 1, 2, 3; the same sets in all three, since the seed carries no
    family. The code-leaning chain (E_lab, hard zero, tau = 0.1, background ones, residual included): one cell per rung of
    `code_leaning` (the ladder of (size, descriptive) the run's caches give; None where the existence rule allows no chain)
    and eight usage-matched controls per rung."""
    cells: list[Cell] = []
    for k in range(draws):
        for r in MARGINAL_RUNGS:
            cells.append(Cell(run, "union", "E", "D_unif", TAU_PRIMARY, "r0", "excluded", k, r, "marginal", TIER_4, descriptive=r in POSITION_SUB_RUNGS))
    for k in range(draws):
        for r in MARGINAL_REPLICATE_1_RUNGS:
            cells.append(Cell(run, "union", "E", "D_unif", TAU_PRIMARY, "r0", "excluded", k, r, "marginal", TIER_4, replicate=1))
    for family, background in (("soft_erase", "r1"), ("union", "uniform")):
        for k in range(draws):
            for r in MARGINAL_OTHER_FAMILY_RUNGS:
                cells.append(Cell(run, family, "E", "D_unif", TAU_PRIMARY, background, "excluded", k, r, "marginal", TIER_4))
    for size, descriptive in code_leaning or []:
        cells.append(Cell(run, "code_leaning_hard", "E_lab", "D_code", TAU_PRIMARY, "ones", "included", 0, code_leaning_rung(size), "none", TIER_4, descriptive=descriptive))
    for size, descriptive in code_leaning or []:
        for k in range(draws):
            cells.append(Cell(run, "code_leaning_hard", "E_lab", "D_code", TAU_PRIMARY, "ones", "included", k, code_leaning_rung(size), "usage", TIER_4, descriptive=descriptive))
    return cells


# tier 5, on the main run (and the stand-in, for its dry run), enumerated on
# request after tier 4 so that tiers 1 to 4 are the same cells in the same order. Three launch subsets, kept beside ALL_SUBSETS
# (a test holds ALL_SUBSETS to SUBSETS and SUBSETS_TIER_4); LAUNCH_SUBSETS is what a launch's --subset may name.
TIER_5 = 5
TIER_5_RUNS: tuple[str, ...] = ("main", "simplestories")
SAME_DOMAIN_ARMS: tuple[tuple[str, str, bool], ...] = (("C", "D_code", True), ("U", "D_unif", True), ("P", "D_prose", False))  # (arm, donor pool, same-size random control cells)
SAME_DOMAIN_RUNGS: tuple[str, ...] = ("1", "2", "2a", "2b", "3", "4", "5", "6", "7")  # 1, 8, 16, 32, 64 tokens; 1, 4, 16, 64 texts; then the pool, once. All compared (m = 10); no 5a, 6a
SAME_DOMAIN_CONTROL_RUNGS: tuple[str, ...] = ("1", "2", "2a", "2b", "3", "4")
SELF_UNION_SETS: tuple[str, ...] = ("E", "E_lab", "D_unif")
PER_TEXT_RUNG = "4"  # a per-text merge is a merge of one whole donor text, RUNG_SCHEDULE's rung 4
PARTNER_SHIFTS: tuple[int, ...] = (1, 2, 3, 4)
PARTNER_ARMS: tuple[tuple[str, str, str], ...] = (("E", "within", "E"), ("E_lab", "source", "E_lab"), ("E_lab", "general", "D_unif"))  # (eval set, arm, partner pool); tier5.PARTNER_ARMS
EXTERNAL_RUNS: tuple[str, ...] = ("main",)  # the comparison models share the paper's tokenizer, not the stand-in's
EXTERNAL_MODEL_KEYS: tuple[str, ...] = ("pythia-70m", "pythia-160m")  # external_models.MODELS
EXTERNAL_SETS: tuple[str, ...] = ("E", "E_lab")
PLAIN_TERMS_CURVE_1_RUNGS: tuple[str, ...] = ("1", "2", "2a", "2b", "3", "4", "8")
PLAIN_TERMS_CONTROL_RUNGS: tuple[str, ...] = ("3", "4")
PLAIN_TERMS_CODE_LEANING_SIZES: tuple[int, ...] = (64, 256)  # and the whole group (G1007 on the paper's model)
LISTED_REFERENCES: tuple[str, ...] = ("unmasked", "unmasked_delta", "importances")
LISTED_ARM_POOLS: tuple[str, ...] = ("D_code", "D_unif")  # arms C and U
LISTED_ARM_RUNGS: tuple[str, ...] = ("3", "4")
SUBSETS_TIER_5: dict[str, Any] = {
    "same_domain": lambda c: c.tier == TIER_5 and c.family == "union",
    "self_merge": lambda c: c.tier == TIER_5 and c.family in PER_TEXT_FAMILIES,
    "plain_terms": lambda c: c.tier == TIER_5 and c.family == "external",  # its other cells are re-runs under committed names, added per store (plain_terms_reruns)
}
LAUNCH_SUBSETS: dict[str, Any] = {**ALL_SUBSETS, **SUBSETS_TIER_5}


def tier_5_cells(run: str, draws: int) -> list[Cell]:
    """`same_domain`: union cells on E_lab (tau = 0.1, background r0, residual excluded),
    three donor arms over the ten merge sizes, eight draws (the pool once), with same-size random controls for arms C and U at the
    six smallest sizes; rungs 2a and 2b are not descriptive here. `self_merge`: the self-merge on E, E_lab, and D_unif, and the
    partner merges under shifts 1 to 4 in three arms. The external-model cells of `plain_terms` (the paper's model only); that
    subset's other cells are re-runs of committed cells and are added per store, never enumerated a second time."""
    cells: list[Cell] = []
    for _, pool, _ in SAME_DOMAIN_ARMS:
        for k in range(draws):
            for r in SAME_DOMAIN_RUNGS:
                cells.append(Cell(run, "union", "E_lab", pool, TAU_PRIMARY, "r0", "excluded", k, r, "none", TIER_5))
        cells.append(Cell(run, "union", "E_lab", pool, TAU_PRIMARY, "r0", "excluded", 0, "8", "none", TIER_5))
    for _, pool, control in SAME_DOMAIN_ARMS:
        if control:
            for k in range(draws):
                for r in SAME_DOMAIN_CONTROL_RUNGS:
                    cells.append(Cell(run, "union", "E_lab", pool, TAU_PRIMARY, "r0", "excluded", k, r, "plain", TIER_5))
    for s in SELF_UNION_SETS:
        cells.append(Cell(run, "self_union", s, s, TAU_PRIMARY, "r0", "excluded", 0, PER_TEXT_RUNG, "none", TIER_5))
    for eval_set, arm, pool in PARTNER_ARMS:
        for shift in PARTNER_SHIFTS:
            cells.append(Cell(run, "partner_union", eval_set, pool, TAU_PRIMARY, "r0", "excluded", 0, PER_TEXT_RUNG, "none", TIER_5, shift=shift, arm=arm))
    if run in EXTERNAL_RUNS:
        for s in EXTERNAL_SETS:
            for key in EXTERNAL_MODEL_KEYS:
                cells.append(Cell(run, "external", s, None, None, "none", "none", 0, "0", "none", TIER_5, model=key))
    return cells


# tier 6, the binary union, on the main run (and the stand-in, for a local dry run), enumerated on
# request after tier 5 so that tiers 1 to 5 are the same cells in the same order. It enumerates only the cells no earlier tier names; the
# secondary form's rungs 2 and 3 are tier 3's cells (enumerated from the start, never launched) and are selected by the launch subset's
# predicate, never enumerated a second time. The one launch subset sits in a dictionary of its own beside LAUNCH_SUBSETS, which a
# test holds to ALL_SUBSETS and SUBSETS_TIER_5.
TIER_6 = 6
TIER_6_RUNS: tuple[str, ...] = ("main", "simplestories")
BINARY_RUNGS: tuple[str, ...] = ("2", "2a", "3")  # 8, 16, 64 donor tokens (sources.RUNG_SCHEDULE)
BINARY_EXISTING_RUNGS: tuple[str, ...] = ("2", "3")  # the secondary form's rungs that tier 3 already names
OWN_ROUND_PRIMARY, OWN_ROUND_SECONDARY = OWN_ROUND_VALUES  # 0.0 (permitted, decides) and 0.1 (described only)


def tier_6_cells(run: str, draws: int) -> list[Cell]:
    """All on E with donors from D_unif at tau = 0.1 (so that `build_sources` gives the headline's
    donor sets), background r0, the residual excluded. The primary form `rounded0_own_g` at 8, 16, 64 tokens under every draw; the
    secondary form `rounded_own_g` at 16 tokens (its 8 and 64 are tier 3's); the primary's look-alike control (`marginal`, whose sets
    carry no family, so they are tier 4's) at the same points; and the self-merge on E in both binary forms, through the `own_round`
    field of tier 5's per-text family. Rung 2a is compared here (the m = 4 fixed in advance), so no cell is flagged descriptive."""
    cells: list[Cell] = []
    for k in range(draws):
        for r in BINARY_RUNGS:
            cells.append(Cell(run, ROUNDED0_FAMILY, "E", "D_unif", TAU_PRIMARY, "r0", "excluded", k, r, "none", TIER_6))
    for k in range(draws):
        for r in BINARY_RUNGS:
            if r not in BINARY_EXISTING_RUNGS:
                cells.append(Cell(run, "rounded_own_g", "E", "D_unif", TAU_PRIMARY, "r0", "excluded", k, r, "none", TIER_6))
    for k in range(draws):
        for r in BINARY_RUNGS:
            cells.append(Cell(run, ROUNDED0_FAMILY, "E", "D_unif", TAU_PRIMARY, "r0", "excluded", k, r, "marginal", TIER_6))
    for t in (OWN_ROUND_PRIMARY, OWN_ROUND_SECONDARY):
        cells.append(Cell(run, "self_union", "E", "E", TAU_PRIMARY, "r0", "excluded", 0, PER_TEXT_RUNG, "none", TIER_6, own_round=t))
    return cells


def is_binary_union_existing(c: Cell) -> bool:
    """The secondary form's cells that tier 3 enumerates (cut from every tier-3 launch): `rounded_own_g` on
    E at tau = 0.1, background r0, the residual excluded, no control, at rungs 2 and 3. Selected by this predicate, never re-enumerated."""
    return (c.tier == 3 and c.family == "rounded_own_g" and c.eval_set == "E" and c.donor_pool == "D_unif" and c.tau == TAU_PRIMARY and c.background == "r0"
            and c.delta == "excluded" and c.control == "none" and c.rung in BINARY_EXISTING_RUNGS and not c.optional and c.replicate == 0)


SUBSETS_TIER_6: dict[str, Any] = {"binary_union": lambda c: c.tier == TIER_6 or is_binary_union_existing(c)}
LAUNCH_SUBSETS_S11: dict[str, Any] = {**LAUNCH_SUBSETS, **SUBSETS_TIER_6}  # what a launch's --subset may name from tier 6 on


# Tier 7: the merges of 2 and 4 donor tokens (rungs T2 and T4) on E and E_lab, and the code-leaning edit on the random 200-row panels of
# part C, on the main run (and the stand-in, for its dry run), enumerated on request after tier 6 so that tiers 1 to 6 are the same cells in
# the same order. Two launch subsets in a dictionary of their own beside LAUNCH_SUBSETS_S11.
TIER_7 = 7
TIER_7_RUNS: tuple[str, ...] = ("main", "simplestories")
SMALL_MERGE_RUNGS: tuple[str, ...] = ("T2", "T4")  # 2 and 4 donor tokens (sources.RUNG_SCHEDULE)
SMALL_MERGE_E_CONTROLS: tuple[str, ...] = ("none", "plain", "marginal")  # the real merge, the uniform control, the frequency-matched control (replicate 0)
SMALL_MERGE_E_LAB_POOLS: tuple[str, ...] = ("D_code", "D_unif", "D_prose")
PANEL_ROWS = 200
# the panels as evaluation sets, by their saved names; the stand-in's are slices of its rows under the same names (tier7.STAND_IN_PANELS)
PANEL_EVAL_SETS: dict[str, tuple[str, ...]] = {
    "main": ("panel_Github", "panel_StackExchange", "panel_ArXiv", "panel_Pile_CC", "panel_Wikipedia__en_", "panel_DM_Mathematics", "panel_PubMed_Central", "panel_FreeLaw"),
    "simplestories": ("panel_ArXiv", "panel_Github", "panel_StackExchange", "panel_DM_Mathematics", "panel_FreeLaw"),
}
# the code-leaning edit's two sizes: a ladder rung and the whole group, each with the committed ladder's descriptive flag (both read rungs)
PANEL_EDIT_SIZES: dict[str, tuple[int, ...]] = {"main": (256, 1007), "simplestories": (64, 94)}
SET_SIZES.update({p: PANEL_ROWS for p in PANEL_EVAL_SETS["main"]})  # so that a panel cell's cost reads in E-equivalent passes (200 / 1,024)


def tier_7_cells(run: str, draws: int) -> list[Cell]:
    """The merge sizes: `union` on E with donors from D_unif (tau 0.1, background r0, the residual excluded) at rungs T2 and T4 under every
    draw, with no control, the uniform control (`plain`), and the frequency-matched control (`marginal`, replicate 0); the same family on
    E_lab from each of D_code, D_unif, D_prose, no control. All descriptive (outside every comparison count fixed in advance). The family name
    stays `union`: the uniform control's seed carries it. The panel edit: on each panel of the run, the code-leaning group's hard delete
    (family `code_leaning_hard`, background ones, the residual included) at each edit size, draw 0, and its usage-matched twins under every
    draw, with the committed ladder's descriptive flag (False for both sizes)."""
    cells: list[Cell] = []
    for ctl in SMALL_MERGE_E_CONTROLS:
        for k in range(draws):
            for r in SMALL_MERGE_RUNGS:
                cells.append(Cell(run, "union", "E", "D_unif", TAU_PRIMARY, "r0", "excluded", k, r, ctl, TIER_7, descriptive=True))
    for pool in SMALL_MERGE_E_LAB_POOLS:
        for k in range(draws):
            for r in SMALL_MERGE_RUNGS:
                cells.append(Cell(run, "union", "E_lab", pool, TAU_PRIMARY, "r0", "excluded", k, r, "none", TIER_7, descriptive=True))
    for panel in PANEL_EVAL_SETS.get(run, ()):
        for size in PANEL_EDIT_SIZES[run]:
            cells.append(Cell(run, "code_leaning_hard", panel, "D_code", TAU_PRIMARY, "ones", "included", 0, code_leaning_rung(size), "none", TIER_7, descriptive=False))
        for size in PANEL_EDIT_SIZES[run]:
            for k in range(draws):
                cells.append(Cell(run, "code_leaning_hard", panel, "D_code", TAU_PRIMARY, "ones", "included", k, code_leaning_rung(size), "usage", TIER_7, descriptive=False))
    return cells


SUBSETS_TIER_7: dict[str, Any] = {"merge_sizes": lambda c: c.tier == TIER_7 and c.family == "union", "panel_edit": lambda c: c.tier == TIER_7 and c.family == "code_leaning_hard"}
LAUNCH_SUBSETS_S12: dict[str, Any] = {**LAUNCH_SUBSETS_S11, **SUBSETS_TIER_7}  # what a launch's --subset may name from tier 7 on


def is_plain_terms_rerun(c: Cell, group_size: int | None) -> bool:
    """The plain-terms re-run cells, as a predicate on the cells of tiers 1 to 4: curve 1 on E at rungs 1, 2, 2a, 2b, 3, 4 (every
    draw) and 8; its same-size random control at rungs 3 and 4; the soft erase (background r1) at rung 4, every draw; the
    never-named removal at its whole-set rung, residual included; the code-leaning edit on E_lab at 64 and 256 members and the
    whole group (`group_size`; None where the run has no chain)."""
    if c.tier not in (1, 2, 3, 4) or c.family == "reference" or c.replicate != 0 or c.optional:
        return False
    if _curve1(c, TAU_PRIMARY):
        return c.rung in (PLAIN_TERMS_CURVE_1_RUNGS if c.control == "none" else PLAIN_TERMS_CONTROL_RUNGS)
    if c.family == "soft_erase" and c.eval_set == "E" and c.donor_pool == "D_unif" and c.tau == TAU_PRIMARY and c.background == "r1" and c.delta == "excluded" and c.control == "none":
        return c.rung == "4"
    if c.family == "never_named_hard" and c.eval_set == "E" and c.tau == TAU_PRIMARY and c.delta == "included" and c.control == "none":
        return c.rung == "8"
    if c.family == "code_leaning_hard" and c.control == "none" and not c.descriptive:
        return code_leaning_size(c.rung) in PLAIN_TERMS_CODE_LEANING_SIZES + ((group_size,) if group_size else ())
    return False


def plain_terms_reruns(all_cells: list[Cell], group_size: int | None) -> list[Cell]:
    """The re-run cells, taken from the enumeration itself so that their names, tiers, and flags are the committed ones."""
    return [c for c in all_cells if is_plain_terms_rerun(c, group_size)]


def per_position_listed(c: Cell, group_size: int | None = None) -> bool:
    """The listed cells: those whose three per-position extras are kept. The references unmasked, unmasked_delta, and
    importances on E and E_lab; every re-run cell of `plain_terms`; the self-merge on E; arms C and U at rungs 3 and 4; the
    external-model cells."""
    if c.family == "reference":
        return c.condition in LISTED_REFERENCES and c.eval_set in ("E", "E_lab")
    if c.family == "external":
        return True
    if c.tier == TIER_5:
        if c.family == "self_union":
            return c.eval_set == "E"
        return c.family == "union" and c.control == "none" and c.donor_pool in LISTED_ARM_POOLS and c.rung in LISTED_ARM_RUNGS
    return is_plain_terms_rerun(c, group_size)


def _chain(run: str, family: str, eval_set: str, pool: str, tau: float, background: str, delta: str, tier: int, *, control: str = "none",
           rungs: tuple[str, ...] = INTERMEDIATE_RUNGS, extra_rungs: tuple[str, ...] = (), end_per_draw: bool | None = None, sub_rungs: bool = False,
           optional: bool = False, draws: int = K_DRAWS) -> list[Cell]:
    """Rungs 1 to 7 (and the adaptive ones) under `draws` draws; rung 8 once under a primary background and per draw
    under a uniform one; the sub-rungs once (draw 0)."""
    cells = []
    all_rungs = tuple(sorted(set(rungs) | set(extra_rungs), key=rung_order))
    for k in range(draws):
        for r in all_rungs:
            cells.append(Cell(run, family, eval_set, pool, tau, background, delta, k, r, control, tier, optional=optional))
    per_draw = (background == "uniform") if end_per_draw is None else end_per_draw
    for k in range(draws if per_draw else 1):
        cells.append(Cell(run, family, eval_set, pool, tau, background, delta, k, "8", control, tier, optional=optional))
    if sub_rungs:
        for s in SUB_RUNGS:
            cells.append(Cell(run, family, eval_set, pool, tau, background, delta, 0, s, control, tier, optional=optional))
    return cells


def _references(run: str, eval_set: str, tier: int, conditions: tuple[Condition, ...] = CONDITIONS, draws: int = K_DRAWS) -> list[Cell]:
    return [Cell(run, "reference", eval_set, None, None, "none", c.delta, k, "0", "none", tier, condition=c.name)
            for c in conditions for k in (range(draws) if c.per_draw else [0])]


def enumerate_cells(*, extra_rungs: tuple[str, ...] = (), include_optional: bool = True, draws: int = K_DRAWS, runs: tuple[str, ...] = RUNS,
                    adaptive: dict[tuple[str, float], tuple[str, ...]] | None = None, tier_4: bool = False, code_leaning: dict[str, list[tuple[int, bool]]] | None = None,
                    tier_5: bool = False, tier_6: bool = False, tier_7: bool = False) -> list[Cell]:
    """The three pre-registered tiers, exactly. `adaptive` maps (pool, tau) to the rungs the adaptive rule inserts for that
    pool's chains at that threshold (5a and 6a), computed from n_on before any cell runs; `extra_rungs` inserts them
    everywhere (a test of the enumeration). With `tier_4`, the cells of `tier_4_cells` follow for
    the runs of TIER_4_RUNS, `code_leaning` giving each run's ladder; tiers 1 to 3 are the same cells in the same order
    either way (a test holds them to their names on main). With `tier_5`, the cells of `tier_5_cells` follow
    last for the runs of TIER_5_RUNS; tiers 1 to 4 are the same cells in the same order either way (tests/test_tier5_cells.py). With
    `tier_6`, the cells of `tier_6_cells` follow after that for the runs of TIER_6_RUNS; tiers 1 to 5 are the same cells
    in the same order either way (tests/test_tier6.py)."""
    adaptive = adaptive or {}

    def _ex(pool: str, tau: float) -> tuple[str, ...]:
        return tuple(sorted(set(extra_rungs) | set(adaptive.get((pool, tau), ()))))

    cells: list[Cell] = []
    for run in runs:
        # ---- tier 1, the verdict tier
        cells += _chain(run, "union", "E", "D_unif", TAU_PRIMARY, "r0", "excluded", 1, extra_rungs=_ex("D_unif", TAU_PRIMARY), draws=draws)
        cells += _chain(run, "union", "E", "D_unif", TAU_PRIMARY, "uniform", "excluded", 1, extra_rungs=_ex("D_unif", TAU_PRIMARY), draws=draws)
        cells += _chain(run, "hard_zero", "E", "D_unif", TAU_PRIMARY, "ones", "included", 1, extra_rungs=_ex("D_unif", TAU_PRIMARY), draws=draws)
        cells += _chain(run, "soft_erase", "E", "D_unif", TAU_PRIMARY, "r1", "excluded", 1, extra_rungs=_ex("D_unif", TAU_PRIMARY), draws=draws)
        cells += _chain(run, "soft_erase", "E", "D_unif", TAU_PRIMARY, "uniform", "excluded", 1, extra_rungs=_ex("D_unif", TAU_PRIMARY), draws=draws)
        cells += _references(run, "E", 1, draws=draws)
        cells += _chain(run, "hard_zero", "E_lab", "D_code", TAU_PRIMARY, "ones", "included", 1, extra_rungs=_ex("D_code", TAU_PRIMARY), draws=draws)
        cells += _chain(run, "soft_erase", "E_lab", "D_code", TAU_PRIMARY, "r1", "excluded", 1, extra_rungs=_ex("D_code", TAU_PRIMARY), draws=draws)
        cells += _chain(run, "code_specific_hard", "E_lab", "D_code", TAU_PRIMARY, "ones", "included", 1, extra_rungs=_ex("D_code", TAU_PRIMARY), sub_rungs=True, draws=draws)
        cells += _references(run, "E_lab", 1, draws=draws)
        # ---- tier 2, the control tier: the matched-random control of every verdict-tier family
        cells += _chain(run, "union", "E", "D_unif", TAU_PRIMARY, "r0", "excluded", 2, control="plain", extra_rungs=_ex("D_unif", TAU_PRIMARY), draws=draws)
        cells += _chain(run, "union", "E", "D_unif", TAU_PRIMARY, "uniform", "excluded", 2, control="plain", extra_rungs=_ex("D_unif", TAU_PRIMARY), draws=draws)
        cells += _chain(run, "hard_zero", "E", "D_unif", TAU_PRIMARY, "ones", "included", 2, control="plain", extra_rungs=_ex("D_unif", TAU_PRIMARY), draws=draws)
        cells += _chain(run, "soft_erase", "E", "D_unif", TAU_PRIMARY, "r1", "excluded", 2, control="plain", extra_rungs=_ex("D_unif", TAU_PRIMARY), draws=draws)
        cells += _chain(run, "soft_erase", "E", "D_unif", TAU_PRIMARY, "uniform", "excluded", 2, control="plain", extra_rungs=_ex("D_unif", TAU_PRIMARY), draws=draws)
        cells += _chain(run, "hard_zero", "E_lab", "D_code", TAU_PRIMARY, "ones", "included", 2, control="plain", extra_rungs=_ex("D_code", TAU_PRIMARY), draws=draws)
        cells += _chain(run, "soft_erase", "E_lab", "D_code", TAU_PRIMARY, "r1", "excluded", 2, control="plain", extra_rungs=_ex("D_code", TAU_PRIMARY), draws=draws)
        cells += _chain(run, "code_specific_hard", "E_lab", "D_code", TAU_PRIMARY, "ones", "included", 2, control="complement", extra_rungs=_ex("D_code", TAU_PRIMARY), sub_rungs=True, draws=draws)
        cells += _chain(run, "code_specific_hard", "E_lab", "D_code", TAU_PRIMARY, "ones", "included", 2, control="plain", extra_rungs=_ex("D_code", TAU_PRIMARY), sub_rungs=True, draws=draws)
        # ---- tier 3, the sensitivity tier: the never-named erase chain first: a hard-zero family whose
        # erased sets are the first n entries of one seeded permutation per draw of the never-named set (the complement of the
        # rung-8 union at tau over the run's own D_unif cache), n the union chain's total count at the same draw and rung;
        # the bridging rungs B50 and B75 at half and three quarters of the set; rung 8 the whole set once, plus once with
        # Delta excluded (the bridge to H4); and the strict cell, the complement of the tau = 0 rung-8 union, Delta included
        cells += _chain(run, "never_named_hard", "E", "D_unif", TAU_PRIMARY, "ones", "included", 3, extra_rungs=_ex("D_unif", TAU_PRIMARY) + tuple(BRIDGING_RUNGS), draws=draws)
        cells.append(Cell(run, "never_named_hard", "E", "D_unif", TAU_PRIMARY, "ones", "excluded", 0, "8", "none", 3))
        cells.append(Cell(run, "never_named_hard", "E", "D_unif", 0.0, "ones", "included", 0, "8", "none", 3))
        for c in [x for x in cells if x.run == run and x.tier in (1, 2) and x.family != "reference"]:
            cells.append(Cell(run, c.family, c.eval_set, c.donor_pool, 0.5, c.background, c.delta, c.draw, c.rung, c.control, 3, optional=c.optional))  # tau = 0.5 for everything above
        cells += _chain(run, "union", "E", "D_unif", TAU_PRIMARY, "uniform", "included", 3, extra_rungs=_ex("D_unif", TAU_PRIMARY), draws=draws)  # non-primary Delta (union r0 included is the same cell)
        cells += _chain(run, "soft_erase", "E", "D_unif", TAU_PRIMARY, "r1", "included", 3, extra_rungs=_ex("D_unif", TAU_PRIMARY), draws=draws)
        cells += _chain(run, "soft_erase", "E", "D_unif", TAU_PRIMARY, "uniform", "included", 3, extra_rungs=_ex("D_unif", TAU_PRIMARY), draws=draws)
        cells += _chain(run, "hard_zero", "E", "D_unif", TAU_PRIMARY, "ones", "excluded", 3, extra_rungs=_ex("D_unif", TAU_PRIMARY), draws=draws)
        cells += _chain(run, "hard_zero", "E_lab", "D_code", TAU_PRIMARY, "ones", "excluded", 3, extra_rungs=_ex("D_code", TAU_PRIMARY), draws=draws)
        cells += _chain(run, "soft_erase", "E_lab", "D_code", TAU_PRIMARY, "r1", "included", 3, extra_rungs=_ex("D_code", TAU_PRIMARY), draws=draws)
        cells += _chain(run, "code_specific_hard", "E_lab", "D_code", TAU_PRIMARY, "ones", "excluded", 3, extra_rungs=_ex("D_code", TAU_PRIMARY), sub_rungs=True, draws=draws)
        cells += _chain(run, "union", "E", "D_unif", 0.0, "r0", "excluded", 3, extra_rungs=_ex("D_unif", 0.0), draws=draws)  # tau = 0 union, primary background only
        cells += _chain(run, "union", "E", "D_unif", 0.0, "r0", "excluded", 3, control="plain", extra_rungs=_ex("D_unif", 0.0), draws=draws)  # its matched-random control (an addition to the pre-registered tiers; the Delta variants keep no controls)
        cells += _chain(run, "rounded_own_g", "E", "D_unif", TAU_PRIMARY, "r0", "excluded", 3, extra_rungs=_ex("D_unif", TAU_PRIMARY), draws=draws)
        cells += _chain(run, "rounded_own_g", "E", "D_unif", TAU_PRIMARY, "r0", "excluded", 3, control="plain", extra_rungs=_ex("D_unif", TAU_PRIMARY), draws=draws)
        cells += _chain(run, "code_specific_soft", "E_lab", "D_code", TAU_PRIMARY, "r1", "excluded", 3, extra_rungs=_ex("D_code", TAU_PRIMARY), draws=draws)  # the soft form at the primary configuration
        for k in range(draws):  # the donor-side pass: rungs 4 and 7 of every union draw on the donor sequences, with two references there
            for r in ("4", "7"):
                cells.append(Cell(run, "union", "donors", "D_unif", TAU_PRIMARY, "r0", "excluded", k, r, "none", 3))
                cells.append(Cell(run, "union", "donors", "D_unif", TAU_PRIMARY, "r0", "excluded", k, r, "none", 3, donor_side_reference="importances"))
                cells.append(Cell(run, "union", "donors", "D_unif", TAU_PRIMARY, "r0", "excluded", k, r, "none", 3, donor_side_reference="rounded"))
        cells += _chain(run, "hard_zero", "E", "D_code", TAU_PRIMARY, "ones", "included", 3, extra_rungs=_ex("D_code", TAU_PRIMARY), draws=draws)  # the domain families on E, one configuration
        cells += _chain(run, "soft_erase", "E", "D_code", TAU_PRIMARY, "r1", "excluded", 3, extra_rungs=_ex("D_code", TAU_PRIMARY), draws=draws)
        cells += _chain(run, "code_specific_hard", "E", "D_code", TAU_PRIMARY, "ones", "included", 3, extra_rungs=_ex("D_code", TAU_PRIMARY), sub_rungs=True, draws=draws)
        # the six level cells: the alive set (the rung-8 union set at tau = 0.1) at s + (1 - s) g for
        # s in {0.25, 0.5, 0.75}, crossed with the never-named set at its labels (r0) and at 1 (r1); no draws, Delta excluded
        for bg in ("r0", "r1"):
            for lvl in LEVELS:
                cells.append(Cell(run, "level", "E", "D_unif", TAU_PRIMARY, bg, "excluded", 0, "8", "none", 3, level=lvl))
        # the ranked never-named pair, main run only: the never-named set at tau = 0.1 ordered by the weight
        # norm and by the positive-label count, erased top-n and bottom-n at the ladder's sizes; four nested chains of nine rungs
        if run in RANKED_RUNS:
            for key in RANK_KEYS:
                for end in RANK_ENDS:
                    for r in RANKED_RUNGS:
                        cells.append(Cell(run, "never_named_ranked", "E", "D_unif", TAU_PRIMARY, "ones", "included", 0, r, "none", 3, rank_key=key, rank_end=end))
        # the descriptive position rungs 2a and 2b of curve 1 and its plain control, per draw (launched on main)
        for ctl in ("none", "plain"):
            for k in range(draws):
                for r in POSITION_SUB_RUNGS:
                    cells.append(Cell(run, "union", "E", "D_unif", TAU_PRIMARY, "r0", "excluded", k, r, ctl, 3, descriptive=True))
        if include_optional:
            cells += _chain(run, "soft_erase", "E_lab", "D_unif", TAU_PRIMARY, "r1", "excluded", 3, extra_rungs=_ex("D_unif", TAU_PRIMARY), optional=True, draws=draws)
    if tier_4:  # after every run's tiers 1 to 3, so that their order is untouched
        for run in runs:
            if run in TIER_4_RUNS:
                cells += tier_4_cells(run, draws, (code_leaning or {}).get(run))
    if tier_5:  # after everything else, so that the order of tiers 1 to 4 is untouched
        for run in runs:
            if run in TIER_5_RUNS:
                cells += tier_5_cells(run, draws)
    if tier_6:  # after everything else, so that the order of tiers 1 to 5 is untouched
        for run in runs:
            if run in TIER_6_RUNS:
                cells += tier_6_cells(run, draws)
    if tier_7:  # the merge sizes and the panel edit: after everything else, so that the order of tiers 1 to 6 is untouched
        for run in runs:
            if run in TIER_7_RUNS:
                cells += tier_7_cells(run, draws)
    names = [c.name for c in cells]
    assert len(set(names)) == len(names), "cell names must be unique"
    return cells


def tier_counts(cells: list[Cell]) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for t in (1, 2, 3) + ((TIER_4,) if any(c.tier == TIER_4 for c in cells) else ()) + ((TIER_5,) if any(c.tier == TIER_5 for c in cells) else ()) + ((TIER_6,) if any(c.tier == TIER_6 for c in cells) else ()) + ((TIER_7,) if any(c.tier == TIER_7 for c in cells) else ()):
        sel = [c for c in cells if c.tier == t]
        extra_sets = (("D_unif",) if t == TIER_5 else ()) + (tuple(dict.fromkeys(c.eval_set for c in sel if c.eval_set.startswith("panel_"))) if t == TIER_7 else ())
        out[f"tier_{t}"] = {"cells": len(sel), "E_equivalent_passes": round(sum(c.e_equivalent for c in sel), 1), "optional_cells": sum(c.optional for c in sel),
                            "by_eval_set": {s: sum(1 for c in sel if c.eval_set == s) for s in ("E", "E_lab", "donors") + extra_sets}}
    out["total"] = {"cells": len(cells), "E_equivalent_passes": round(sum(c.e_equivalent for c in cells), 1), "expected_total": "6,500 to 7,000 E-equivalent passes"}
    return out


# ----------------------------------------------------------------------------- sources for a set of cells


@dataclass
class BuiltSource:
    rho: np.ndarray | None  # the named set (the union set, or the erased set); None for references; (N, n_sub), one row per text, for the per-text families of tier 5
    record: dict[str, Any] = field(default_factory=dict)  # n_on per module and total, source hash, seed tuples, donor set, control metadata
    aux: dict[str, np.ndarray] = field(default_factory=dict)  # tier 5: a per-text source's per-text arrays (the partner's row, the count each text receives); never in the manifest


def build_sources(cells: list[Cell], caches: dict[str, Cache], alive: dict[str, tuple[np.ndarray, str]], prose_named: dict[str, dict[float, np.ndarray]] | None,
                  f_code: dict[str, dict[float, np.ndarray]] | None, module_to_c: dict[str, int], *, master_seed: int = 0, log: Any = print,
                  weight_norms: dict[str, np.ndarray] | None = None, code_leaning: dict[str, Any] | None = None, tier5_inputs: dict[str, Any] | None = None) -> dict[str, BuiltSource]:
    """One source per non-reference cell, from the caches: `caches` keyed by "<pool>_<run>", `alive` keyed by run as
    (vector, sha256), `prose_named` and `f_code` keyed by run and then by tau (each run's own, from its D_prose and D_code
    caches: a control run's code-specific cells, sub-rungs and complement controls never read the main run's files).
    `weight_norms`, keyed by run, is the (n_sub,) vector ||U_c|| ||V_c|| of the run's loaded model
    (weight_norms.py); it is needed only when a ranked never-named cell keyed by the weight norm is among the cells.
    `code_leaning`, keyed by run, is the run's `code_leaning.CodeLeaningSets` (the group, its
    chain, and the wide set its control excludes), computed once from the run's code and prose caches by the caller; it is
    needed only when a code-leaning cell is among the cells. The marginal control's rates are computed here
    from the run's D_unif cache at tau = 0.1, the only configuration they are defined in.
    `tier5_inputs`, keyed by run, is the run's `tier5.Tier5Inputs` (the own-named sets of E,
    E_lab, and D_unif from the label caches, E_lab's source blocks and documents); it is needed only when a per-text cell
    (self_union, partner_union) is among the cells. An external-model cell has no source."""
    from vpd_audit.code_leaning import CL_WINDOW, pool_usage_above, twins_source, usage_twins
    from vpd_audit.sources import key_sha256, marginal_rates

    t0 = time.time()
    out: dict[str, BuiltSource] = {}
    union_cache: dict[tuple, np.ndarray] = {}
    offsets = next(iter(caches.values())).offsets
    count_cache: dict[str, np.ndarray] = {}
    usage_cache: dict[str, np.ndarray] = {}  # tier 4: per run, usage on D_unif at tau = 0.1 (the marginal rates; the twins' ranks)
    twins_cache: dict[tuple[str, int], tuple[np.ndarray, dict[str, Any]]] = {}

    def usage_unif(run: str) -> np.ndarray:
        if run not in usage_cache:
            usage_cache[run] = pool_usage_above(caches[f"D_unif_{run}"], TAU_PRIMARY)
        return usage_cache[run]

    def union_for(run: str, pool: str, draw: int, rung: str, tau: float) -> tuple[np.ndarray, DonorSet]:
        cache = caches[f"{pool}_{run}"]
        ds = donor_set(pool, cache.n_sequences, draw, rung, master_seed)
        key = (run, pool, draw, rung, tau)
        if key not in union_cache:
            union_cache[key] = union_source(cache, ds.positions, tau)
        return union_cache[key], ds

    for c in cells:
        if c.family == "reference" or c.donor_side_reference is not None:
            out[c.name] = BuiltSource(None, {"kind": "reference"})
            continue
        if c.family == "external":  # a comparison model's own predictions; no source, no mask
            assert c.model is not None, c.name
            out[c.name] = BuiltSource(None, {"kind": "external", "model": c.model})
            continue
        if c.family in PER_TEXT_FAMILIES:
            # one named set per text, from the evaluation sets' own label caches (tier5.py, which the
            # launch also holds to the label-only self_merge_sets.parquet); only in the configuration fixed in advance
            from vpd_audit.tier5 import per_text_source

            assert tier5_inputs is not None and c.run in tier5_inputs, f"{c.name}: the own-named sets of run {c.run!r} are needed (tier5.load_inputs, from the label caches of E, E_lab, and D_unif)"
            assert c.tau == TAU_PRIMARY and c.background == "r0" and c.delta == "excluded" and c.control == "none" and c.rung == PER_TEXT_RUNG and c.donor_pool is not None, c.name
            # the binary self-merge takes the self-merge's own set unchanged (the rounding is in the mask)
            assert c.own_round is None or (c.family == "self_union" and c.own_round in OWN_ROUND_VALUES), c.name
            rows, rec_pt, aux = per_text_source(c.family, c.eval_set, c.donor_pool, c.arm, c.shift, tier5_inputs[c.run], module_to_c, offsets, master_seed=master_seed)
            rec_pt.update({"draw": c.draw, "rung": c.rung})
            if c.own_round is not None:
                rec_pt["own_round"] = float(c.own_round)
            out[c.name] = BuiltSource(rows, rec_pt, aux)
            continue
        assert c.donor_pool is not None and c.tau is not None
        rec: dict[str, Any] = {"family": c.family, "pool": c.donor_pool, "tau": c.tau, "draw": c.draw, "rung": c.rung}
        if c.family == "level":
            # the named set is the alive set, the rung-8 union at the cell's tau over the run's own pool; the
            # source is (that set, the constant s on it, where the never-named set sits), and its hash covers all three
            assert c.control == "none" and c.background in ("r0", "r1") and c.level is not None and c.rung == "8", c.name
            rho_8, ds = union_for(c.run, c.donor_pool, 0, "8", c.tau)
            at = "labels" if c.background == "r0" else "one"
            rec.update({"donor_unit": ds.unit, "donor_size": ds.size, "seed_tuple": "", "level": float(c.level), "never_named_at": at,
                        "set_sha256": source_hash(rho_8), "set_definition": "the rung-8 union at tau over the run's own pool cache (the alive set)",
                        "named_n_on": n_on(rho_8, module_to_c, offsets), "n_on": n_on(rho_8, module_to_c, offsets), "source_sha256": level_source_hash(rho_8, float(c.level), at)})
            out[c.name] = BuiltSource(rho_8.copy(), rec)
            continue
        if c.family == "code_leaning_hard":
            # the rung is the first `size` members of the run's chain; its control is those
            # members' twins under the cell's draw. Both come from code_leaning.py, which the label-only pre-read used too.
            assert code_leaning is not None and c.run in code_leaning, f"{c.name}: the code-leaning sets of run {c.run!r} are needed (code_leaning.code_leaning_sets, from the run's D_code and D_prose caches)"
            assert c.control in ("none", "usage") and c.background == "ones" and c.tau == TAU_PRIMARY, c.name
            sets = code_leaning[c.run]
            size = code_leaning_size(c.rung)
            assert (size, bool(c.descriptive)) in sets.ladder, f"{c.name}: no rung of {size} members (descriptive {c.descriptive}) on the run's ladder {sets.ladder}"
            named = sets.named(size)
            rec.update({"donor_unit": "code_leaning", "donor_size": size, "seed_tuple": "", "named_n_on": n_on(named, module_to_c, offsets),
                        "code_leaning": {"group_threshold": sets.group_threshold, "wide_threshold": sets.wide_threshold, "n_group": sets.n_group, "n_wide": sets.n_wide, "ladder": [[int(a), bool(b)] for a, b in sets.ladder],
                                         "order_sha256": key_sha256(sets.order.astype(np.float64)), "wide_sha256": source_hash(sets.wide_full), "min_selectivity": float(sets.selectivity_full[sets.order[:size]].min())}})
            if c.control == "usage":
                if (c.run, c.draw) not in twins_cache:
                    twins_cache[(c.run, c.draw)] = usage_twins(sets.order, sets.wide_full, alive[c.run][0], usage_unif(c.run), module_to_c, draw=c.draw, master_seed=master_seed, window=CL_WINDOW, offsets=offsets)
                twins, meta = twins_cache[(c.run, c.draw)]
                ctl = twins_source(twins, size, named.shape[0])
                assert not (ctl & sets.wide_full).any()
                rec["control"] = {**meta, "alive_sha256": alive[c.run][1], "alive_run": c.run, "n_alive": int(alive[c.run][0].sum()), "shortfall_at_this_rung": int((twins[:size] < 0).sum())}
                rec["matched_source_sha256"] = source_hash(named)
                named = ctl
            rec.update({"n_on": n_on(named, module_to_c, offsets), "source_sha256": source_hash(named)})
            out[c.name] = BuiltSource(named, rec)
            continue
        if c.family == "never_named_ranked":
            # S as for the never-named chain; the ladder's size at this rung (the union's draw-0 total at rungs
            # 1 to 7, a fraction of S at the bridging rungs); the first n members of S by the key at the chain's end
            assert c.control == "none" and c.background == "ones" and c.rank_key in ("weight_norm", "positive_count") and c.rank_end in ("top", "bottom"), c.name
            rho_8, _ = union_for(c.run, c.donor_pool, 0, "8", c.tau)
            S = never_named_set(rho_8)
            rec["never_named"] = {"tau": c.tau, "pool": c.donor_pool, "run": c.run, "size": int(S.sum()), "sha256": source_hash(S),
                                  "definition": "the complement of the rung-8 union at tau over the run's own pool cache"}
            if c.rung in BRIDGING_RUNGS:
                n = int(np.floor(BRIDGING_RUNGS[c.rung] * int(S.sum())))
                rec.update({"donor_unit": "bridge", "bridge_fraction": BRIDGING_RUNGS[c.rung]})
            else:
                rho_u, ds = union_for(c.run, c.donor_pool, 0, c.rung, c.tau)  # the union chain's draw-0 total at this rung
                n = int(rho_u.sum())
                rec.update({"donor_unit": ds.unit, "donor_size": ds.size, "matched_union_n_on": n_on(rho_u, module_to_c, offsets), "matched_union_sha256": source_hash(rho_u), "matched_union_draw": 0})
            if c.rank_key == "weight_norm":
                assert weight_norms is not None and c.run in weight_norms, f"{c.name}: the weight norms of run {c.run!r} are needed (weight_norms.py, from the loaded model)"
                key = weight_norms[c.run]
                rec["rank_key_definition"] = "||U_c|| ||V_c|| of the subcomponent from the loaded model, float64 (weight_norms.py)"
            else:
                if c.run not in count_cache:
                    count_cache[c.run] = positive_label_counts(caches[f"{c.donor_pool}_{c.run}"])
                key = count_cache[c.run]
                rec["rank_key_definition"] = f"the number of {c.donor_pool} positions at which the label is positive, from the cache"
            assert key.shape == S.shape, (key.shape, S.shape)
            named, meta = ranked_never_named_source(S, key, n, end=c.rank_end, master_seed=master_seed)
            rec.update({"rank": {"key": c.rank_key, **meta}, "seed_tuple": "", "named_n_on": n_on(named, module_to_c, offsets)})
            rec.update({"n_on": n_on(named, module_to_c, offsets), "source_sha256": source_hash(named)})
            out[c.name] = BuiltSource(named, rec)
            continue
        if c.family == "never_named_hard":
            # the set S is the complement of the rung-8 union at the cell's tau over the run's own pool
            assert c.control == "none" and c.background == "ones", c.name
            rho_8, _ = union_for(c.run, c.donor_pool, 0, "8", c.tau)
            S = never_named_set(rho_8)
            rec["never_named"] = {"tau": c.tau, "pool": c.donor_pool, "run": c.run, "size": int(S.sum()), "sha256": source_hash(S),
                                  "definition": "the complement of the rung-8 union at tau over the run's own pool cache"}
            if c.rung == "8":
                named, meta = S.copy(), {"n_requested": int(S.sum()), "n_taken": int(S.sum()), "shortfall": 0, "whole_set": True}
                rec["donor_unit"] = "pool"
            else:
                if c.rung in BRIDGING_RUNGS:
                    n = int(np.floor(BRIDGING_RUNGS[c.rung] * int(S.sum())))
                    rec.update({"donor_unit": "bridge", "bridge_fraction": BRIDGING_RUNGS[c.rung]})
                else:
                    rho_u, ds = union_for(c.run, c.donor_pool, c.draw, c.rung, c.tau)  # the union chain's total count at this draw and rung
                    n = int(rho_u.sum())
                    rec.update({"donor_unit": ds.unit, "donor_size": ds.size, "matched_union_n_on": n_on(rho_u, module_to_c, offsets), "matched_union_sha256": source_hash(rho_u)})
                named, meta = never_named_source(S, n, draw=c.draw, master_seed=master_seed)
                rec["seed_tuple"] = dumps_seed(tuple(meta["seed_tuple"]))
            rec["never_named_draw"] = meta
            rec["named_n_on"] = n_on(named, module_to_c, offsets)
            rec.update({"n_on": n_on(named, module_to_c, offsets), "source_sha256": source_hash(named)})
            out[c.name] = BuiltSource(named, rec)
            continue
        needs_prose = c.rung in SUB_RUNGS or c.family in ("code_specific_hard", "code_specific_soft")
        if needs_prose:
            assert prose_named is not None and c.run in prose_named, f"{c.name}: the prose-named set of run {c.run!r} is needed (have {sorted(prose_named or {})})"
            pn = prose_named[c.run][c.tau]
            rec["prose_named_run"] = c.run
        if c.rung in SUB_RUNGS:
            assert f_code is not None and c.run in f_code and c.family in ("code_specific_hard",), f"{c.name}: the code firing fractions of run {c.run!r} are needed"
            sets, meta = sub_rung_sets(alive[c.run][0], pn, f_code[c.run][c.tau])
            named = sets[c.rung]
            rec.update({"sub_rung": meta, "prose_named_sha256": source_hash(pn)})
            matched_candidates = alive[c.run][0] & ~pn
        else:
            rho_u, ds = union_for(c.run, c.donor_pool, c.draw, c.rung, c.tau)
            rec.update({"donor_unit": ds.unit, "donor_size": ds.size, "donor_sequences": list(ds.sequences) if ds.unit != "pool" else "all", "seed_tuple": dumps_seed(ds.seed_tuple)})
            if c.family in ("code_specific_hard", "code_specific_soft"):
                named = code_specific_source(rho_u, pn)
                rec["prose_named_sha256"] = source_hash(pn)
                matched_candidates = alive[c.run][0] & ~pn
            else:
                named = rho_u
                matched_candidates = None
        rec["named_n_on"] = n_on(named, module_to_c, offsets)
        if c.control != "none":
            assert c.control in ("plain", "complement", "marginal"), c.name
            cand = matched_candidates if c.control == "complement" else None
            vec, sha = alive[c.run]
            if c.control == "marginal":
                # the same count per matrix, drawn with the real process's inclusion probabilities; the rates are defined
                # on D_unif at tau = 0.1 only, and the seed carries no family, so the three families share their sets
                assert c.donor_pool == "D_unif" and c.tau == TAU_PRIMARY and c.rung not in SUB_RUNGS, c.name
                rates = marginal_rates(usage_unif(c.run), caches[f"D_unif_{c.run}"].n_positions)
                ctl, meta = matched_random_source(rec["named_n_on"], vec, module_to_c, family=c.family, draw=c.draw, master_seed=master_seed, alive_sha256=sha, alive_run=c.run, offsets=offsets,
                                                  weights=rates, replicate=c.replicate)
            else:
                assert c.replicate == 0, c.name
                ctl, meta = matched_random_source(rec["named_n_on"], vec, module_to_c, family=c.family, draw=c.draw, master_seed=master_seed, candidates=cand, alive_sha256=sha, alive_run=c.run, offsets=offsets)
            rec["control"] = meta
            rec["matched_source_sha256"] = source_hash(named)
            named = ctl
        rec.update({"n_on": n_on(named, module_to_c, offsets), "source_sha256": source_hash(named)})
        out[c.name] = BuiltSource(named, rec)
    log(f"[cells] {len(out)} sources built in {time.time() - t0:.1f} s")
    return out


# ----------------------------------------------------------------------------- the loop


CELL_ROW_EXTRA = ("n_on", "sigma", "omega", "t_star_0.1", "t_star_0", "n_positions_below_label",
                  "kl_prefix_sum_0.1", "kl_prefix_sum_0", "d_0.1", "d_0", "n_touched_0.1", "n_touched_0")  # the last six: the clean-prefix sums, the conditional damage, and the touched counts
HARD_ZERO_REFERENCES = ("unmasked", "unmasked_delta")  # rung 0 of every hard-zero chain, by its Delta setting


def reference_for(c: Cell) -> str | None:
    """The reference condition that is rung 0 of this chain; was grid._reference_for."""
    k = c.draw
    if c.family in ("union", "code_specific_soft") and c.background == "r0":
        return "importances"
    if c.family == "union" and c.background == "uniform":
        return f"stochastic/k{k}" if c.delta == "excluded" else f"stochastic_delta/k{k}"
    if c.family in ("soft_erase", "code_specific_soft") and c.background == "r1":
        return "unmasked" if c.delta == "excluded" else "unmasked_delta"
    if c.family == "soft_erase" and c.background == "uniform":
        return f"stochastic/k{k}" if c.delta == "excluded" else f"stochastic_delta/k{k}"
    if c.is_hard_zero:
        return "unmasked_delta" if c.delta == "included" else "unmasked"
    if c.family == "rounded_own_g":
        return "rounded_0.1" if c.tau == 0.1 else ("rounded_0.5" if c.tau == 0.5 else "rounded_0")
    if c.family == "level":  # the path from importances (s = 0, never-named at labels) or from the soft erase's rung 8 (never-named at 1)
        return "importances" if c.background == "r0" else "unmasked"
    if c.family in PER_TEXT_FAMILIES:  # a per-text union on the background r0 starts from the text's own labels
        if c.own_round is not None:  # the binary self-merge starts from the text's own labels rounded at the same threshold
            return {OWN_ROUND_PRIMARY: "rounded_0", OWN_ROUND_SECONDARY: "rounded_0.1"}[c.own_round]
        return "importances"
    if c.family == ROUNDED0_FAMILY:  # the primary binary union starts from the own labels rounded at 0
        return "rounded_0"
    return None


def conditional_damage(kl: Tensor, kl_ref: Tensor, t_star: Tensor) -> tuple[Tensor, Tensor]:
    """Per sequence and in float32 from the float32 (B, T) divergences: the
    clean-prefix sum of the cell's own divergence, sum_{t < t*} KL_cell (zero when t* = 0), and the conditional damage
    d_b = (1/t*) sum_{t < t*} [KL_cell - KL_ref] against the chain's rung 0 (NaN when t* = 0; the difference of the two
    per-sequence means when t* = T). The prefix is t < t*, strictly: position t* is the first the erased set touches."""
    assert kl.ndim == 2 and kl.shape == kl_ref.shape and t_star.shape == (kl.shape[0],), (tuple(kl.shape), tuple(kl_ref.shape), tuple(t_star.shape))
    T = kl.shape[1]
    prefix = torch.arange(T, device=kl.device)[None, :] < t_star[:, None]  # (B, T) bool
    # torch.where, not a multiply by the mask: NaN times 0 is NaN, so a non-finite value outside
    # the prefix would poison the sum; where() leaves it out. For finite values the two are the same numbers.
    prefix_sum = torch.where(prefix, kl.float(), 0.0).sum(dim=1)
    diff_sum = torch.where(prefix, kl.float() - kl_ref.float(), 0.0).sum(dim=1)
    d = torch.where(t_star > 0, diff_sum / t_star.clamp(min=1).to(torch.float32), torch.full_like(diff_sum, float("nan")))
    return prefix_sum, d


def run_cells(
    model: Any,
    cells: list[Cell],
    ids: np.ndarray,
    sources: dict[str, BuiltSource],
    *,
    job: str,
    run: str,
    out_dir: Path,
    precision: str,
    subbatch: int,
    set_name: str,
    set_hash: str,
    checkpoint_hashes: dict[str, str],
    master_seed: int = 0,
    importance_chunk: int = IMPORTANCE_CHUNK,
    resume: bool = True,
    ce_for_all: bool = False,
    on_subbatch: Any = None,
    timings: Any = None,
    log: Any = print,
    tier5: Any = None,
) -> SubbatchStore:
    """Cells of one run on one evaluation set: sub-batch outer, cells inner; the same store and manifest as the
    references, the marker with F_i per (cell, sub-batch) and running sums per cell, and cells.parquet at the end.

    `timings`, when given (`timing.time_grid_subbatch`), is an object with a `phase(name)` context
    manager that synchronizes the device and accumulates wall-clock per phase; it changes nothing else.

    `tier5`, when given (a `tier5.StoreRun`), turns on what a tier-5 store holds beside the usual
    tables: the plain-terms extras (per-text columns for every cell, per-position arrays for the listed cells,
    the target's side once per sub-batch, the top five at the example positions), the external-model cells, and
    the canary and gate checked after every sub-batch, before its checkpoint. Without it every line below runs as it did; the
    per-text families take their own mask path whether or not it is given."""
    import contextlib

    phase = timings.phase if timings is not None else (lambda name: contextlib.nullcontext())
    assert ids.ndim == 2 and ids.shape[1] == SEQ_LEN
    assert all(c.run == run for c in cells) and len({c.eval_set for c in cells}) == 1
    device = next(model.parameters()).device
    keys = module_keys(model)
    names = [c.name for c in cells]  # the store's cell list keeps the enumeration order
    # the references run first within each sub-batch (a stable sort; the uniform background is
    # regenerated per cell from its seed, so the order changes no value), and the float32 divergence of unmasked and
    # unmasked_delta is held for the sub-batch as rung 0 of every hard-zero cell. A store with a hard-zero cell must
    # therefore hold the reference that cell needs (grid.add_store_references adds the references to every store on E and E_lab).
    # The external-model cells run before everything (key -1; no other store has one, so every
    # other store's order is what it was): their float32 logits and the target's logits are freed before any masked forward.
    order = sorted(cells, key=lambda c: -1 if c.family == "external" else (0 if c.family == "reference" else 1))
    for ref in sorted({reference_for(c) for c in cells if c.is_hard_zero}):
        assert any(c.family == "reference" and c.condition == ref for c in cells), \
            f"a store with hard-zero cells must hold their rung 0: {run}/{cells[0].eval_set}/ref/{ref} is not among its cells"
    external_cells = [c for c in order if c.family == "external"]
    lx = None
    if tier5 is not None:
        from vpd_audit.plain_terms import LoopExtras

        lx = LoopExtras(names, [c.name for c in cells if tier5.listed(c)], tier5.example_positions, seq_len=SEQ_LEN)
        assert tier5.example_positions is None or tier5.example_positions.shape[0] == ids.shape[0], "one row of example positions per text of the set"
    assert not external_cells or (tier5 is not None and tier5.externals), "an external-model cell needs its loaded comparison model (tier5.StoreRun.externals)"
    store = SubbatchStore(out_dir, n_sequences=ids.shape[0], cells=names, subbatch=subbatch, extra_arrays=lx.spec() if lx is not None else None)
    done = store.resume() if resume else -1
    manifest_path = out_dir / "run_manifest.json"
    manifest: RunManifest | None = RunManifest.load(manifest_path) if (resume and manifest_path.is_file()) else None
    weight_deltas = model.calc_weight_deltas()
    dtype = None
    t_job = time.time()
    for i in range(done + 1, store.n_subbatches):
        t0 = time.time()
        sl = store.subbatch_slice(i)
        batch = torch.from_numpy(np.ascontiguousarray(ids[sl])).long().to(device)
        with phase("importances"):
            imp = compute_importances(model, batch, precision=precision, chunk=importance_chunk)
        g, target_logits = imp.g, imp.target_logits
        del imp
        dtype = g[keys[0]].dtype
        B, T = batch.shape
        if manifest is None:
            manifest = RunManifest(job=job, run=run, checkpoint_hashes=checkpoint_hashes, set_name=set_name, set_hash=set_hash, n_sequences=int(ids.shape[0]), precision=precision,
                                   g_dtype=str(dtype), subbatch=subbatch, importance_chunk=importance_chunk, master_seed=master_seed, n_draws=max([c.draw for c in cells] + [0]) + 1,
                                   device=str(device), gpu_name=torch.cuda.get_device_name(device) if device.type == "cuda" else None, torch_version=torch.__version__, commits=code_commits(),
                                   extra={"cells": names, "n_cells": len(cells), "tiers": sorted({c.tier for c in cells}), "sources": {n: sources[n].record for n in names},
                                          **({"tier5": {"target_logits_dtype": str(target_logits.dtype), "per_position_listed_cells": list(lx.listed), "extra_columns": True,
                                                        "example_positions": None if tier5.example_positions is None else [int(x) for x in tier5.example_positions.shape],
                                                        "external_models": {k: e.facts for k, e in (tier5.externals or {}).items()} if external_cells else {}}} if lx is not None else {})},
                                   fingerprint=dict(FINGERPRINT_SPEC))
            manifest.save(manifest_path)
        with phase("ce"):
            ce_target = per_sequence_ce(target_logits, batch)
        # the target's softmax once per sub-batch, in the chunks of KL_CHUNK per_position_kl
        # takes it in, then the target logits are freed (3.3 GB at sub-batch 64 on the paper's vocabulary)
        with phase("softmax_once"):
            target_probs = target_softmax_chunks(target_logits)
        if lx is not None:  # under bf16 autocast the target's logits are bf16, and exact ties between its top two tokens follow from that
            assert target_logits.dtype == (torch.bfloat16 if precision == "bf16" else torch.float32), (target_logits.dtype, precision)
        target_logits_kept = target_logits if external_cells else None  # the reverse divergence takes log P from the logits; freed after the last external cell
        del target_logits
        seq_index = np.arange(sl.start, sl.stop)
        rho_t: dict[str, dict[str, Tensor]] = {}
        ref_kl: dict[str, Tensor] = {}  # the float32 (B, T) divergence of unmasked and unmasked_delta on this sub-batch
        sub_rows: list[dict[str, Any]] = []  # tier 5: this sub-batch's rows, for the canary and the gate before the checkpoint
        ext_state: dict[str, Any] = {}
        if lx is not None:
            with phase("extras"):
                lx.start_subbatch(store, sl, target_probs)
        for c in order:
            src = sources[c.name]
            u = u_delta = None
            if c.family == "reference" and CONDITION_BY_NAME[c.condition].kind == "target":  # type: ignore[index]
                # the target itself: no mask, no forward, zero divergence, the target's cross-entropy (as run_references does)
                rows = [{"cell": c.name, "condition": "target", "draw": 0, "seq": int(seq_index[b]), "kl_mean": 0.0, "kl_max": 0.0, "kl_argmax": 0, "ce": float(ce_target[b]),
                         "ce_target": float(ce_target[b]), "mask_fp": "", "delta": "none", "precision": precision, "min_gap": 0.0, "n_below_label": 0, "n_positions_below_label": 0,
                         "n_on": 0, "sigma": float("nan"), "omega": float("nan"), "t_star_0.1": -1, "t_star_0": -1,
                         "kl_prefix_sum_0.1": float("nan"), "kl_prefix_sum_0": float("nan"), "d_0.1": float("nan"), "d_0": float("nan"), "n_touched_0.1": -1, "n_touched_0": -1}
                        for b in range(len(seq_index))]
                if lx is not None:
                    t_cols = lx.target_columns(batch)
                    for b, row in enumerate(rows):
                        row.update({k: float(v[b]) for k, v in t_cols.items()})
                store.add_rows(rows)
                sub_rows += rows
                store.set_positions(c.name, sl, np.zeros((len(seq_index), SEQ_LEN), dtype=np.float32))
                continue
            if c.family == "external":
                # a comparison model's own predictions, sliced to the target's ids, through the same
                # divergence function and the same extras as a mask's logits, with this sub-batch's own target softmax chunks
                from vpd_audit.external_models import external_cell_quantities

                with phase("external"):
                    q = external_cell_quantities(c.model, ext_state, tier5.externals, target_probs, target_logits_kept, batch)  # type: ignore[arg-type]
                    kl_mean, kl_max, kl_arg = summarize_kl(q["kl"])
                    ce = per_sequence_ce(q["logits"], batch)
                    x_cols = lx.cell(store, c.name, sl, q["logits"], batch)  # type: ignore[union-attr]
                    kl_rev, kl_oth, pm_mean, pm_max = q["kl_reverse"].mean(dim=-1), q["kl_other"].mean(dim=-1), q["padded_mass"].mean(dim=-1), q["padded_mass"].amax(dim=-1)
                rows = [{"cell": c.name, "condition": "external", "draw": 0, "seq": int(seq_index[b]), "kl_mean": float(kl_mean[b]), "kl_max": float(kl_max[b]), "kl_argmax": int(kl_arg[b]), "ce": float(ce[b]),
                         "ce_target": float(ce_target[b]), "mask_fp": "", "delta": "none", "precision": "fp32", "min_gap": 0.0, "n_below_label": 0, "n_positions_below_label": 0,
                         "n_on": 0, "sigma": float("nan"), "omega": float("nan"), "t_star_0.1": -1, "t_star_0": -1,
                         "kl_prefix_sum_0.1": float("nan"), "kl_prefix_sum_0": float("nan"), "d_0.1": float("nan"), "d_0": float("nan"), "n_touched_0.1": -1, "n_touched_0": -1,
                         **{k: float(v[b]) for k, v in x_cols.items()}, "kl_reverse_mean": float(kl_rev[b]), "kl_other_mean": float(kl_oth[b]), "padded_mass_mean": float(pm_mean[b]), "padded_mass_max": float(pm_max[b])}
                        for b in range(len(seq_index))]
                store.add_rows(rows)
                sub_rows += rows
                store.set_positions(c.name, sl, q["kl"].cpu().numpy())
                del q
                if c is external_cells[-1]:
                    ext_state.clear()
                    target_logits_kept = None
                    if device.type == "cuda":
                        torch.cuda.empty_cache()
                continue
            with phase("mask_build"):
                if c.family == "reference":
                    cond = CONDITION_BY_NAME[c.condition]  # type: ignore[index]
                    masks, deltas = build_condition_masks(cond, g, model.module_to_c, draw=c.draw, subbatch_index=i, master_seed=master_seed)
                    permitted, named = cond.permitted, None
                elif c.donor_side_reference == "importances":
                    # the donor-side pass's first reference: the importances themselves on the donor sequences (no source)
                    masks, deltas, permitted, named = {k: g[k] for k in keys}, None, True, None
                elif c.donor_side_reference == "rounded":
                    # its second reference: the paper's rounded mask 1[g > tau] on the donor sequences (no source; below g where g <= tau)
                    from vpd_audit.masks import rounded_mask

                    masks, deltas, permitted, named = {k: rounded_mask(g[k], c.tau) for k in keys}, None, False, None  # type: ignore[arg-type]
                elif c.family in PER_TEXT_FAMILIES:
                    # one row of the source per text, (B, 1, C_l), through the per-text siblings of
                    # rho_tensors, family_masks, and apply_binary_source; the batch-shared path below is untouched. The self-merge's
                    # rows, built from the label cache, must be the on-device (g > tau).any(dim=1) on every sub-batch.
                    assert src.rho is not None and src.rho.ndim == 2 and src.rho.shape[0] == ids.shape[0], (c.name, None if src.rho is None else src.rho.shape)
                    named = rho_tensors_per_text(src.rho[sl], model.module_to_c, dtype, device)
                    if c.family == "self_union":
                        n_diff = sum(int(((g[k] > c.tau).any(dim=1) != named[k].squeeze(1).bool()).sum()) for k in keys)
                        if n_diff:
                            from vpd_audit.tier5 import GateFailure

                            raise GateFailure(f"{c.name}, sub-batch {i}: the self-merge's sets from the label cache differ from the on-device (g > {c.tau:g}).any(dim=1) in {n_diff} entries")
                    # own_round None is the fractional self-merge's path exactly; a threshold rounds the text's own labels first
                    masks, deltas, permitted = family_masks_per_text(c.family, g, named, background=c.background, delta=c.delta, own_round=c.own_round)
                else:
                    assert src.rho is not None, c.name
                    if c.name not in rho_t:
                        rho_t[c.name] = rho_tensors(src.rho, model.module_to_c, dtype, device)
                    named = rho_t[c.name]
                    if c.background == "uniform":
                        # the uniform background is regenerated from its seed tuple for every cell that needs it, module
                        # by module in sorted order, so that draw k on sub-batch i is the same tensor at every rung and nothing as large
                        # as g is held across cells (about 10 ms per cell on the paper's model; holding every draw's u cost 5 GB a draw)
                        u, u_delta = uniform_background((master_seed, "u", c.draw, i), model.module_to_c, B, T, dtype=dtype, device=device)
                    fam = FAMILY_MASK_KIND.get(c.family, c.family)
                    masks, deltas, permitted = family_masks(fam, g, named, background=c.background, delta=c.delta, tau=c.tau, u=u, u_delta=u_delta, level=c.level)
            fr = masked_forward(model, batch, masks, g, permitted=permitted, precision=precision, delta_masks=deltas, weight_deltas=weight_deltas if deltas is not None else None,
                                timings=timings)
            with phase("divergence"):
                kl = per_position_kl_from_probs(target_probs, fr.logits)
            if c.family == "reference" and c.condition in HARD_ZERO_REFERENCES:
                ref_kl[c.condition] = kl  # type: ignore[index]
            with phase("ce"):
                ce = per_sequence_ce(fr.logits, batch) if (c.family == "reference" or c.donor_side_reference is not None or ce_for_all) else None
            with phase("fingerprint_l3"):
                fp_hex = level3_hex(fr.fp, seq_index)
            with phase("summarize"):
                kl_mean, kl_max, kl_arg = summarize_kl(kl)
            extra_cols: dict[str, Any] = {"n_on": src.record.get("n_on", {}).get("total", 0) if src.rho is not None else 0}
            if c.family in PER_TEXT_FAMILIES:
                with phase("columns"):  # the count and the switched mass are per text
                    extra_cols["n_on_rows"] = src.rho[sl].sum(axis=1).astype(np.int64)  # type: ignore[index]
                    extra_cols["sigma"] = switched_mass_per_text(g, named).cpu().numpy()  # type: ignore[arg-type]
            elif named is not None and c.donor_side_reference is None and c.family != "reference":
                with phase("columns"):
                    fam = FAMILY_MASK_KIND.get(c.family, c.family)
                    bg = "r1" if c.is_hard_zero else c.background
                    sigma = switched_mass(g, named, family="soft_erase" if c.is_hard_zero else fam, background=bg, u=u, level=c.level)
                    extra_cols["sigma"] = sigma.cpu().numpy()
                    if c.is_hard_zero:
                        extra_cols["omega"] = over_removal(g, named).cpu().numpy()
                        ref = reference_for(c)
                        assert ref in ref_kl, f"{c.name}: its rung 0 ({ref}) has not run on this sub-batch"
                        for tau_q, tag in ((0.1, "0.1"), (0.0, "0")):
                            t_star, n_touched = first_touched(g, named, tau_q)
                            prefix_sum, d = conditional_damage(kl, ref_kl[ref], t_star)  # type: ignore[index]
                            extra_cols[f"t_star_{tag}"] = t_star.cpu().numpy()
                            extra_cols[f"n_touched_{tag}"] = n_touched.cpu().numpy()
                            extra_cols[f"kl_prefix_sum_{tag}"] = prefix_sum.cpu().numpy()
                            extra_cols[f"d_{tag}"] = d.cpu().numpy()
            x_cols: dict[str, Any] = {}
            if lx is not None:
                with phase("extras"):  # the plain-terms columns of every cell; the per-position arrays of the listed ones
                    x_cols = lx.cell(store, c.name, sl, fr.logits, batch)
            rows = []
            for b in range(len(seq_index)):
                row = {"cell": c.name, "condition": c.condition or c.family, "draw": c.draw, "seq": int(seq_index[b]),
                       "kl_mean": float(kl_mean[b]), "kl_max": float(kl_max[b]), "kl_argmax": int(kl_arg[b]),
                       "ce": float(ce[b]) if ce is not None else float("nan"), "ce_target": float(ce_target[b]), "mask_fp": fp_hex["phi"][b],
                       "delta": c.delta, "precision": precision, "min_gap": fr.min_gap, "n_below_label": fr.n_below_label, "n_positions_below_label": fr.n_positions_below_label,
                       "n_on": int(extra_cols["n_on_rows"][b]) if "n_on_rows" in extra_cols else int(extra_cols["n_on"]), "sigma": float(extra_cols["sigma"][b]) if "sigma" in extra_cols else float("nan"),
                       "omega": float(extra_cols["omega"][b]) if "omega" in extra_cols else float("nan"),
                       "t_star_0.1": int(extra_cols["t_star_0.1"][b]) if "t_star_0.1" in extra_cols else -1, "t_star_0": int(extra_cols["t_star_0"][b]) if "t_star_0" in extra_cols else -1}
                for tag in ("0.1", "0"):
                    row[f"kl_prefix_sum_{tag}"] = float(extra_cols[f"kl_prefix_sum_{tag}"][b]) if f"kl_prefix_sum_{tag}" in extra_cols else float("nan")
                    row[f"d_{tag}"] = float(extra_cols[f"d_{tag}"][b]) if f"d_{tag}" in extra_cols else float("nan")
                    row[f"n_touched_{tag}"] = int(extra_cols[f"n_touched_{tag}"][b]) if f"n_touched_{tag}" in extra_cols else -1
                if x_cols:
                    row.update({k: float(v[b]) for k, v in x_cols.items()})
                rows.append(row)
            with phase("summarize"):
                store.add_rows(rows)
                sub_rows += rows
                store.set_positions(c.name, sl, kl.cpu().numpy())
                _record_lean(store.extra, c.name, i, fp_hex, fr.n_ne_g, fr.n_ne_one, fr.n_below_label, fr.n_positions_below_label)
            del fr, kl, masks, deltas, u, u_delta
        if tier5 is not None and tier5.checker is not None:
            tier5.checker.check(i, sub_rows)  # the canary and the D_unif gate, before this sub-batch is marked done; a failure stops the launch
        del sub_rows
        if tier5 is not None and device.type == "cuda" and i == done + 1:
            # the measured peak after the first sub-batch this process ran of every tier-5 store (the
            # external-model cells hold two float32 logit tensors beside the target's softmax and g), logged and kept in the marker
            peak_gb = torch.cuda.max_memory_allocated(device) / 1e9
            store.extra.setdefault("tier5_peak_memory_gb_after_first_subbatch", {})[str(i)] = peak_gb
            log(f"[{job}] peak GPU memory after sub-batch {i} (the first this process ran): {peak_gb:.1f} GB")
        with phase("checkpoint"):
            store.checkpoint(i)
        del g, rho_t, ref_kl, target_probs
        if device.type == "cuda":
            torch.cuda.empty_cache()
        if on_subbatch is not None:
            on_subbatch(i)
        log(f"[{job}] sub-batch {i + 1}/{store.n_subbatches} ({sl.start}..{sl.stop - 1}), {len(cells)} cells, in {time.time() - t0:.1f} s")
    if manifest is not None and store.done_through == store.n_subbatches - 1:
        manifest.mark_finished(manifest_path)
        write_cell_table(out_dir, cells, sources, store.extra, keys, n_subbatches=store.n_subbatches)
    log(f"[{job}] done: {len(store.rows)} rows, {time.time() - t_job:.1f} s")
    return store


def _record_lean(extra: dict[str, Any], cell: str, i: int, fp_hex: dict[str, Any], n_ne_g: dict[str, int], n_ne_one: dict[str, int], n_below: int, n_pos_below: int) -> None:
    """The lean marker: F_i per (cell, sub-batch), and running sums per cell for everything else."""
    extra.setdefault("mask_fp_subbatch", {}).setdefault(cell, {})[str(i)] = fp_hex["F"]
    s = extra.setdefault("cell_sums", {}).setdefault(cell, {"F": "0" * 16, "H": {k: "0" * 16 for k in fp_hex["H"]}, "Hd": ({k: "0" * 16 for k in fp_hex["Hd"]} if fp_hex["Hd"] else None),
                                                          "n_ne_g": {k: 0 for k in n_ne_g}, "n_ne_one": {k: 0 for k in n_ne_one}, "n_below_label": 0, "n_positions_below_label": 0, "n_subbatches": 0})
    s["F"] = sum_hex([s["F"], fp_hex["F"]])
    for k, v in fp_hex["H"].items():
        s["H"][k] = sum_hex([s["H"][k], v])
    if fp_hex["Hd"]:
        for k, v in fp_hex["Hd"].items():
            s["Hd"][k] = sum_hex([s["Hd"][k], v])
    for k in n_ne_g:
        s["n_ne_g"][k] += int(n_ne_g[k])
        s["n_ne_one"][k] += int(n_ne_one[k])
    s["n_below_label"] += int(n_below)
    s["n_positions_below_label"] += int(n_pos_below)
    s["n_subbatches"] += 1


def write_cell_table(out_dir: Path, cells: list[Cell], sources: dict[str, BuiltSource], extra: dict[str, Any], keys: list[str], *, n_subbatches: int | None = None) -> pd.DataFrame:
    """cells.parquet: one row per cell with the coordinates, seed tuples, n_on per matrix and the sum, the source
    hash, the control's alive hash, mask_fp_cell, mask_fp_modules (JSON), and the two counts (per module JSON and sums).
    With `n_subbatches` (the store's), every cell's marker must have summed exactly that many sub-batches; the target
    reference, which has no mask and no marker, is given the store's count."""
    rows = []
    for c in cells:
        src = sources[c.name].record
        s = extra.get("cell_sums", {}).get(c.name, {})
        n_on_l = src.get("n_on", {})
        is_target = c.family == "reference" and c.condition is not None and CONDITION_BY_NAME[c.condition].kind == "target"
        is_target = is_target or c.family == "external"  # an external-model cell has no mask and no marker either
        n_sub = n_subbatches if (is_target and not s) else s.get("n_subbatches")
        if n_subbatches is not None:
            assert n_sub == n_subbatches, f"{c.name}: the marker summed {n_sub} sub-batches, the store has {n_subbatches}"
        row: dict[str, Any] = {**{k: v for k, v in asdict(c).items()}, "cell": c.name, "e_equivalent": c.e_equivalent,
                               "seed_tuple": src.get("seed_tuple", ""), "donor_unit": src.get("donor_unit"), "donor_size": src.get("donor_size"),
                               "source_sha256": src.get("source_sha256"), "matched_source_sha256": src.get("matched_source_sha256"),
                               "control_alive_sha256": src.get("control", {}).get("alive_sha256"), "control_alive_run": src.get("control", {}).get("alive_run"),
                               "prose_named_sha256": src.get("prose_named_sha256"), "n_on": n_on_l.get("total", 0),
                               "mask_fp_cell": s.get("F"), "mask_fp_modules": json.dumps({"H": s.get("H"), "Hd": s.get("Hd")}) if s else None,
                               "n_ne_g_total": sum(s.get("n_ne_g", {}).values()) if s else None, "n_ne_one_total": sum(s.get("n_ne_one", {}).values()) if s else None,
                               "n_ne_g_modules": json.dumps(s.get("n_ne_g")) if s else None, "n_ne_one_modules": json.dumps(s.get("n_ne_one")) if s else None,
                               "n_below_label_total": s.get("n_below_label"), "n_positions_below_label_total": s.get("n_positions_below_label"), "n_subbatches": n_sub}
        for k in keys:
            row[f"n_on__{k}"] = n_on_l.get(k, 0)
        rows.append(row)
    df = pd.DataFrame(rows)
    tmp = out_dir / "cells.parquet.tmp"
    df.to_parquet(tmp, index=False)
    tmp.replace(out_dir / "cells.parquet")
    return df
