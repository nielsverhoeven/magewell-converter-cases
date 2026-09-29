# Plan D: vertical VESA 400x300 column bracket (sandwiched) + arch sandwich mode (Part B)

> **Implemented as amended by the architect verdicts appended below (rev-2 verdict DB1-DB16, after plan F). Where they conflict, the verdicts win.**

> **As built (post-F, re-derived in the file, confirmed by the DB16 fit-check):** rail keep-out
> y ∈ [−32.5, 33.2]; `YJ_V` 49.46; `REACH` 136.75; α 36.33°; `ARM_LEN` 169.73; `RIB_PAD_GAP` 53.19;
> `rib_end` 107.06; `CENTRE_H` 138.91 (148.91 with tabs); arm 204.7 × 40 × 20; centre 180 × 148.9 × 14.5;
> spacer 40 × 40 × 11. Arch sandwich: `centre_t` 16.6, `z_rail` 27.6, M3×18; `arm_sandwich`
> 167.2 × 40 × 20, `centre_sandwich` 238.1 × 92 × 20.1. §2's table below predates plan F and is superseded.

Status: **researcher plan, not architect-validated.** Rev 2, written per the architect's rejection
of rev 1, the teamlead's relay of new user decisions (2026-09-28), and the architect's Amendment 1
to both this plan's own verdict and Plan A's verdict (read in full; AM-1..AM-7 in Plan A's verdict
are the authoritative wording for R42/R43/Q22/M20 — this plan aligns its own language to it). Route
through `solution-architect` before any developer starts (Team Charter step 2).

## Changelog — rev 2 (2026-09-28)

Rev 1 (same path) is superseded entirely, not amended in place — too much moved to patch. What
changed and why:

1. **Rebased on Plan A rev 2** (`A-wide-dovetail.md`) **as amended by its own architect verdict**
   (`A-wide-dovetail.VERDICT.md`) — the rail interface is not the one rev 1 was written against.
   Every rail-derived number in this plan (`YJ_V`, `CENTRE_H`, `ARM_LEN`, `α`, both bboxes, the
   Z-stack, the M3 stack) is rebased on: `MCC_RAIL_ROOT_W = 65.0` (was 14.6), `MCC_RAIL_Y = −23.5`
   (was −20), no male pedestal (`MCC_RAIL_MALE_H = 3.5`, flush case-floor-on-plate seat),
   `MCC_RAIL_MATE_CLR = 0.5` mm on every non-bearing face, `MCC_M3_MAJOR_D` (renamed),
   `VTV_PLATE_T = 11` (was 8, mirroring arch's own re-derived `ARCH_PLATE_T`).
2. **B8 (old rev 1) is fixed at the root, not patched**: the rail keep-out is now `Y ∈ [−32.5,
   +36.1]` (was `[−7.3, +10.9]`). `YJ_V` is now a **derived formula** (≈ 52.4, was an assumed 25) so
   every M3 counterbore clears the wider rail by construction, not by luck. `CENTRE_H` grows to ≈
   145 (was 90) as a direct consequence.
3. **Sandwich mount, not direct mount** (user decision): the Samsung TVs' own TV lift already
   uses all 4 VESA screws. Both new brackets in this plan clamp **between** the TV and that TV
   lift on **longer M8 bolts** — no counterbore, no washer seat on any pad; the TV lift's own
   rail/plate bears on a **flat** pad face instead.
4. **R42 resolved by explicit user decision, not the architect's recommended option**: **ASA is
   accepted in the clamp path.** No steel compression sleeves. The column/row this bracket does not
   use still needs **equal-thickness printed ASA spacers** so the TV lift's own rail stays flat
   across both columns/rows.
5. **R43/Q22(b) resolved**: fixed layout, **+X column** (seen from behind the TV), case **outboard**
   (toward the TV edge), slid on from the TV's edge side. **`COLUMN_SIDE` is deleted** — no X-mirror,
   because the case cannot be mirrored (its rail interface has one fixed slide direction) and the
   inboard layout was shown infeasible with both columns occupied by the TV lift's own rails.
6. **New: Part B — the arch bracket also gets a sandwich mode**, added on top of what Plan A already
   changes in `arch-tv-bracket.scad` (`ARCH_PLATE_T=11`, `CENTRE_W=92`, etc. — not repeated here,
   that is Plan A's own scope). A new `MOUNT_MODE` parameter (`"direct"`, unchanged default,
   `"sandwich"`, new) swaps the M8 pad from counterbored to a plain through-hole, and a new `spacer`
   part is added for the arch bracket's own unused (bottom) row.
7. **`tv-bracket.scad` is not referenced anywhere in this plan as a pattern to copy** — every
   rail-call pattern here is copied from `arch-tv-bracket.scad` instead, which stays live (see item 11
   for its actual, now-confirmed fate).
8. **`docs/plans/2026-09-27-arch-tv-bracket.md` and rev-1 framing dropped**: the "local `main` is
   stale" and "rail interface being redesigned in parallel" sections are gone — Plan A lands first,
   by rule (Team Charter, and the verdict's own sequencing), so this plan is written directly against
   its post-verdict state, not a moving target. Issue #48's apparent resolution is user bookkeeping,
   already noted once, not repeated as an open question.
9. **M20 measurements named explicitly** (§9) as `assumed` parameters with asserts, so a measured
   value becomes a one-line `-D` override or constant edit, never a silent guess baked into geometry.
10. **A `VESA_V_PITCT` typo in rev 1's own open questions is gone** (was never code, just a typo in
    prose).
11. **`tv-bracket.scad` is not merely "being retired" — Plan A's Amendment 1 deletes it outright**
    (`git rm`, its golden, `MCC_BRACKET_PLATE_T`) as part of Plan A's own PR. This plan references it
    nowhere as an existing file; every rail-call pattern is copied from `arch-tv-bracket.scad`.
12. **The TV is on a TV lift, not a generic "wall mount"** — the user clarified this is a TV LIFT
    whose own mounting interface uses the same 4 VESA screws. Renamed throughout: "wall mount" →
    "TV lift" / "lift" for accuracy; the physical concern (a sandwich on shared screws) is unchanged.
13. **`WALL_GAP` is now user-stated, not blind-guessed**: 150–200 mm behind the TV (TV-lift mount).
    This plan uses **150 mm** (the conservative end) as the asserted bound, not the earlier 100 mm
    placeholder.
14. **`TV_SIDE_CLEAR` and the lateral slide-on sweep are confirmed non-binding by the user** ("space
    around the column is not a constraint") — the feasibility assert (B2) stays (cheap, catches a
    real typo), but the risk that it might fail is closed, not merely deprioritised.
15. **New, load-bearing finding for Part B (arch sandwich mode), per the architect's Amendment 1**:
    the arch bracket's own +X slide-on sweep crosses the right-hand VESA column (the TV lift's own
    rail is there too, in sandwich mode), and at plausible assumed obstacle dimensions **arch's
    existing 11 mm plate is not tall enough to clear it**. Part B now proposes a concrete,
    sandwich-mode-only taller centre plate (a formula, not a placeholder) rather than merely flagging
    the risk — the user's "150–200 mm behind the TV" answer is exactly the headroom this needs.
16. **Both brackets now use the same flat, flush, no-counterbore pad design in sandwich mode**
    (arch's Amendment-1 text says "flat pads at the arm top" too) — the rev-2-draft's earlier R-8
    ("arch keeps a raised boss, asymmetric with the vertical bracket") is resolved, not merely noted.

---

## 0. What this plan consumes, and what it must not touch

**Plan A rev 2, as amended by its verdict, has not been implemented yet** — there is no branch, no
merged `lib/mcc/rail.scad` with these values. This plan is written against the **verdict's own
Appendix A/B/D text** (the binding, final version of Plan A), transcribed and independently
re-verified by rendering a scratch probe that combines Plan A's stated constants with the real,
unaffected `mcc_case_dims()` device-envelope function from the current library (§8 has the exact
reproduction). **If Plan A's implementation deviates from its own verdict in any of the values
below, stop and report — do not silently absorb a different number.**

Rail constants this plan depends on (public symbols only, per the standing rule that a bracket never
re-derives rail cross-section/latch geometry — Plan A owns `rail.scad`):

| Symbol | Value (post Plan-A-verdict) | Was (rev 1 / pre-A) |
|---|---|---|
| `MCC_RAIL_ROOT_W` | 65.0 | 14.6188 |
| `MCC_RAIL_MOUTH_W` | 60.3812 (derived) | 10.0 |
| `MCC_RAIL_Y` | −23.5 | −20.0 |
| `MCC_RAIL_MALE_H` | 3.5 (male's real built height; no pedestal) | n/a (was `MCC_RAIL_SILL_H`-adjacent, 7.0-class) |
| `MCC_RAIL_MATE_CLR` | 0.5 | n/a (flank clearance was `MCC_CLR_SLIDE` = 0.3, no roof clearance existed) |
| `MCC_RAIL_LATCH_ARM_T`, `MCC_RAIL_LATCH_ENGAGE` | 1.6, 2.0 | unchanged |
| `MCC_RAIL_LEN` | 150.0 | unchanged |
| `MCC_RAIL_END_STOP_L/H` | 0 | unchanged (retired since D34) |
| `MCC_M3_MAJOR_D` | 3.0 (renamed from `MCC_THREAD_M3_MAJOR_D` by a plan "C") | — |
| `mcc_rail_male(len=, plate_t=)` | same signature; internally flush now, no pedestal | — |
| `mcc_rail_male_window(len=, plate_t=)` | same signature; now also clears the nub (Plan A's own B1 fix) — **this file calls it unchanged, the extra clearance is internal to `rail.scad`** | — |

**DO NOT:**
- Edit anything under `lib/mcc/**`, least of all `rail.scad` — Plan A owns it.
- Reintroduce `COLUMN_SIDE` or any mirror of the rail or the case.
- Reference `tv-bracket.scad` as a pattern, or assume it still exists — **Plan A's Amendment 1
  deletes it outright** (`git rm`, its golden, `MCC_BRACKET_PLATE_T`) as part of Plan A's own PR, not
  a future step. Copy rail-call patterns from `arch-tv-bracket.scad` (as Plan A leaves it) instead.
- Print/present a "wall mount" framing where "TV lift" is meant — the Samsung TVs sit on a TV lift
  whose own mounting interface is the same 4 VESA screws (user clarification, §Changelog item 12).
- Touch `arch-tv-bracket.scad`'s numbers that Plan A already owns (`ARCH_PLATE_T`, `CENTRE_W`,
  `LAP_RIB_GAP`, `M3_COUNTERBORE_DEPTH`, `M3_JOINT_SCREW_L`, the Z-stack, `centre_z_max`, the mate
  transform, the `tripod_insert` preview flag). **Part B (§7) adds only the sandwich-mode pad
  variant and the spacer part, layered on top of Plan A's edits, never re-stating them.**
- Print either bracket for use with ASA in the clamp path until the user's R42 acceptance (already
  given, §Changelog item 4) is recorded by the architect in `architecture.md`, and not before M15
  (rail-latch pull test) and the tilt measurement (§10) are closed.
- Invent sleeve, spacer, TV-lift, or TV dimensions — cite them or mark `assumed` (§9 lists exactly
  which).

---

## 1. Scope

- **Part A (§§2–6, 8–10):** `models/brackets/vertical-tv-bracket.scad` — new file, hub topology,
  mounted sandwiched on one VESA-300 column, fixed +X-outboard layout.
- **Part B (§7):** additive changes to `arch-tv-bracket.scad`, **on top of** Plan A's own edits —
  a `MOUNT_MODE` parameter and a new `spacer` part.
- Both parts share the same sandwich philosophy (flat clamped pad, printed ASA spacer for the unused
  screws) but are implemented independently per file, matching this repo's existing precedent that
  each bracket file owns its own geometry (architecture.md §3).

---

## 2. Sketch and key numbers (Part A, verified against Plan A's post-verdict constants)

```
                         TOP screw of the +X column (0, +150)
                              o  <- sandwiched: TV -- [ASA pad, flush, M8 through-hole only] --
                             /|     [TV lift's own rail] -- [M8 bolt head + washer]
                            / |
                           /  |   arm (one part, printed twice — rotate +/-alpha)
                          /   |
                         /    |
          Y (real "up")/     |
              ^      /      |
              |     /    +--o  joint / lap, Y = YJ_V ~= 52.4  (was 25 pre-Plan-A)
              |    /     |
              |   /      |  centre plate, 180 x 144.7 x 14.5 mm, carries
   screw     |  /       |  the rail on its TOP face, stacked 11 mm above
   column ---o-----------+========================+---   <- rail, 150 mm long,
  (X=0)      |  \       |                          |         centred at x = REACH ~= 136.75
              \  \      |
               \  +--o  joint / lap, Y = -YJ_V
                \    |
                 \   |
                  \  |
                   \ |
                    \|
                      o
                 BOTTOM screw of the +X column (0, -150)
                              --------> X (real "outboard, toward the TV's edge")

Case, mated on the rail, patch wall DOWN, ENTIRELY OUTBOARD of the column:
  spans X in [31.0, 242.5]   (clear of the column/pad/TV-lift-rail cluster by >=31 mm)
  spans Y in [-106.7, +59.7] (clear of both screws by 43.3 mm / 90.3 mm)
Slide-on: the case enters even further outboard and slides -X (INBOARD) by slide_clear=180.75 mm to
seat -- its transient outboard-most reach during engagement is ~423 mm from the column at this
plan's own W_LIFT_RAIL-adjusted REACH (the architect's own verdict, using the simpler pre-adjustment
REACH=125.75, quotes ~412 mm for the same quantity -- both are provisional on W_LIFT_RAIL, §9).
CONFIRMED NON-BINDING by the user (2026-09-28: "space around the column is not a constraint") --
kept as an assert (B2) for cheap insurance, not because it is expected to fail.
Z (into the room, away from the TV): TV back=0; arms flat 0..11 (pad flush at 11, NOT raised);
centre stacked 11..22 (rail on top); rail mounting face at 22; case floor at 22 (FLUSH, no pedestal
offset); case lid top at 73 (H=51, CLAUDE.md, unchanged).
```

| Quantity | Formula | Value (this plan's own verified probe, §8) |
|---|---|---|
| `HALF_PITCH_V` | `VESA_V_PITCH/2` | 150 |
| Rail keep-out, centre-local Y | `[-MCC_RAIL_ROOT_W/2, MCC_RAIL_ROOT_W/2+MCC_RAIL_LATCH_ARM_T+MCC_RAIL_LATCH_ENGAGE]` | `[-32.5, +36.1]` |
| `YJ_V` (derived, RD2's formula) | `RAIL_KEEPOUT_Y[1] + KEEPOUT_CLR + m3_counterbore_r + norm([JOINT_S/2, JOINT_P/2])` | 52.36 (architect's own estimate: ≈52.4) |
| `VTV_PLATE_T` | rebased, same derivation as arch's `ARCH_PLATE_T` | 11.0 |
| `REACH_KEEPOUT` | `max(PAD_BOSS_D, W_LIFT_RAIL)/2 + KEEPOUT_CLR` — **`W_LIFT_RAIL` is `assumed`, M20** | 31.0 (at the assumed placeholder `W_LIFT_RAIL=60`) |
| `REACH` | `L_max/2 + REACH_KEEPOUT` | 136.75 |
| `ARM_LEN` | `sqrt(REACH^2 + (HALF_PITCH_V-YJ_V)^2)` | 168.03 |
| `ALPHA` | `atan2(HALF_PITCH_V-YJ_V, REACH)` | 35.53° |
| Arm print bbox (X) | `ARM_LEN + LAP_L/2 + ~20` | ≈203.0 (≤244 ✓, 41 mm to spare) |
| `CENTRE_H` | `2*(YJ_V + ARM_W/2)` | 144.71 (architect's own estimate: ≈145) |
| Centre print bbox | `2*C_HALF × CENTRE_H × (VTV_PLATE_T+MCC_RAIL_MALE_H)` | 180 × 144.71 × 14.5 (all ≤244 ✓) |
| Sweep clearance | `2*VTV_PLATE_T - (VTV_PLATE_T+RIB_H)` (no `+MCC_FLOOR_T` — flush now) | 2.0 (== `SWEEP_CLR`, exactly the minimum, same margin arch ships with) |
| Case vs. screws (Y) | — | 90.3 / 43.3 mm clear (healthy) |
| `slide_clear` | `MCC_RAIL_LEN/2 + L_max/2` | 180.75 (unchanged — inputs unaffected by Plan A) |
| `TV_SIDE_CLEAR` minimum (B2's bound) | `case_x_hi + TV_SIDE_MARGIN` | 252.5 |
| M3 counterbore vs. rail keep-out | circle–rect gap at the joint | 13.2 mm clear (better margin than rev 1's old 11.0, because `YJ_V` grew faster than the keep-out) |
| M3 screw stack (arch's own re-derived numbers, reused verbatim) | tip vs. bore floor; engagement | tip clears by 1.4 mm (0.9 over the 0.5 min); engagement 5.3 mm (≥4.5 required) |

**If `W_LIFT_RAIL` turns out much larger than the 60 mm placeholder once M20 lands, re-run this
probe before implementing — `REACH` grows roughly 1:1 with it, and the arm bbox approaches the 244 mm
cap once `REACH` exceeds ≈190 mm (at which point the arm would need splitting into two parts, a
design change, not a parameter tweak). Flagged as R-7, §10.**

---

## 3. Design rationale (carrying forward what the architect approved, resolving what it flagged)

### 3.1 Still approved, unchanged from rev 1's verdict (A1, A2, A5, A7, A8)

- **Hub topology** (A1): both joints at the rail's centre X, mirrored in Y; one arm part printed
  twice, placed by `rotate(∓α)`. The proof that this reproduces a valid mirror pair without
  `mirror()` is unchanged by any of Plan A's numbers (it is pure 2D symmetry, not rail-dependent) —
  restated in §4.3 for a self-contained file.
- **Fresh sibling file** (A2): `models/brackets/vertical-tv-bracket.scad`, arch-style structure,
  sharing no code with `arch-tv-bracket.scad`. Deferred, not rejected: extracting shared pure math
  into `lib/mcc/bow_bracket.scad` if a third two-point bracket is ever requested.
- **UP arrow is a cue, not a key** (A5), reused verbatim, re-checked against the new `CENTRE_H`.
- **Test by `use`** (A7): `tests/test_vertical_tv_bracket.scad`, never assigns `part`, documents the
  one negative case without running it.
- **Public rail symbols only** (A8): `mcc_rail_male(len=, plate_t=)`, `mcc_rail_male_window(len=,
  plate_t=)`, `MCC_RAIL_*` constants. Rail unioned **after** the plate's own cuts (matches Plan A's
  own `arch-tv-bracket.scad` pattern).

### 3.2 A3 resolved: `REACH` is derived from clearance, and "inboard vs. outboard" is now fixed, not a default

Rev 1 derived `REACH` from a clearance minimum rather than from `TV_SIDE_CLEAR` (approved, A3), but
left an internal inconsistency the verdict flagged: it labelled its own default layout "inboard"
while B2's assert (bounding the case's *outboard* edge against the TV's side edge) is only the right
obstacle check for an *outboard* reach. **Rev 2 resolves this by construction, not by relabelling**:
R43/Q22(b) determined that with the TV lift's own rails occupying **both** VESA columns, the case
floor cannot pass over either rail, so **exactly one layout is physically valid**: the **+X column**,
with the case **outboard**. There is no inboard option to default to any more, and no mirror to model
— `COLUMN_SIDE` is deleted (§0). `REACH` keeps its clearance-derived formula (§2 table), now with an
added term for the TV lift's own rail width (`W_LIFT_RAIL`, §3.3).

### 3.3 Sandwich redesign: the pad becomes a clamped spacer, and gets a new keep-out neighbour

Per RD3, the pad is no longer a direct-mount boss with an M8 counterbore and washer seat — it is a
**flat spacer face**, sized so the TV lift's own rail/plate bears on it directly, with the M8
bolt passing straight through (TV → pad → the TV lift's own rail → bolt head + washer, all
outside the case). **This plan places that flat face at `Z = VTV_PLATE_T` (11), flush with the rest
of the arm's own top surface** — RD3's own recommendation. RD3 ties this specifically to *reopening
the inboard layout*; since R43/Q22(b) fixed the layout to outboard instead (§3.2), that particular
benefit is moot, but the flush design is kept anyway on its own merits: no isolated raised boss to
print, one continuous bearing plane for the TV lift's rail to seat against, and it is the simpler
shape. ~~(Part B, §7, keeps arch's *existing* raised boss instead — a different, equally valid choice,
made for a different reason: minimal disruption to an already-shipped file. Both are legitimate;
flagged for the architect to confirm it is comfortable with the asymmetry rather than demanding one
convention across both files.)~~ *(struck by DB7 — both brackets' sandwich pads are flat at the arm
top; no asymmetry exists.)*

**New keep-out consequence:** the TV lift's own rail (M20: `W_LIFT_RAIL`, unmeasured) runs along
the column, in the same (X, Y) neighbourhood as this bracket's own pad and the inboard part of each
arm. Two new, independent effects, both handled as `assumed`-parameter asserts rather than guesses:

- **`REACH_KEEPOUT` grows to cover whichever is wider, this bracket's own pad or the TV lift's
  rail** (§2 table: `max(PAD_BOSS_D, W_LIFT_RAIL)/2 + KEEPOUT_CLR`), so the case's own footprint
  never overlaps either.
- **Ribs must stay clear of the TV lift's rail band along each arm**, not just short of the lap
  (the existing `LAP_RIB_GAP` concern). New parameter `RIB_PAD_GAP` (arm-local distance from the pad
  before a rib may start), derived conservatively from `W_LIFT_RAIL/2 + KEEPOUT_CLR` — a first-order
  approximation (it does not account for the arm's own diagonal angle reducing the true clearance
  need), flagged for tightening once M20's actual rail orientation is known, not before.

### 3.4 Proof that one arm part, printed twice, still works (unchanged from rev 1, restated because
this is a fresh file)

The two screw points `(0, +150)` and `(0, −150)` are related by reflection about the assembly's
**X-axis**. For an arm shape `S` symmetric about its own long (local-X) axis, `reflect_L ∘ rotate(θ)
∘ reflect_L = rotate(−θ)` for the line `L` the two screws are reflected about — so placing the same
symmetric arm at `rotate(+ALPHA)` for one screw and `rotate(−ALPHA)` for the other reproduces the
correct mirror pair by pure rotation, no `mirror()`, no chirality change:

- **Top arm**: `translate([0, +HALF_PITCH_V, 0]) rotate([0,0,-ALPHA]) children();`
- **Bottom arm**: `translate([0, -HALF_PITCH_V, 0]) rotate([0,0,+ALPHA]) children();`

One STL, `// build.py: print_count = arm:2`.

### 3.5 R42 resolved: ASA accepted, no sleeves — but the other column still needs equal spacers

The user's explicit decision (Changelog item 4) accepts ASA creep risk in the clamp path rather than
the architect's recommended steel-sleeve mitigation. This plan implements that decision as given —
**no steel sleeve/spacer parts anywhere in this plan** — but the **physical reason** the other column
still needs a spacer is unchanged by that choice: without one, the TV lift's own rail would sit
flush on the TV at the unused column and proud (by this bracket's own pad thickness) at the used
column, skewing the mount. **A printed ASA spacer, thickness = `VTV_PLATE_T` (11 mm, matching the
pad), M8 through-hole, at each of the other column's two screws**, closes that gap. This is now the
BOM's own printable "spacer" part (§4, §6 step 2.9).

---

## 4. Parameters (Part A — `models/brackets/vertical-tv-bracket.scad`)

| Name | Value | Basis |
|---|---|---|
| `VESA_H_PITCH` | `400` | documentation only, same as arch's `VESA_TOP_PITCH` — not consumed by this file's own geometry |
| `VESA_V_PITCH` | `300` | `assumed` — common Samsung 400×300 deviation from square MIS-F; **M20** confirms the exact TV model's real pitch |
| `HALF_PITCH_V` | `VESA_V_PITCH/2` = 150 | derived |
| `TV_SIDE_CLEAR` | `500` (generous; B2 requires ≥ 252.5 at current parameters, §2) | **User-confirmed non-binding** ("space around the column is not a constraint", 2026-09-28) — kept as a named, asserted parameter (cheap insurance against a future parameter change), not because the user's own TV is expected to bind it |
| `TV_SIDE_MARGIN` | `10.0` | `assumed`, mirrors arch's `TV_TOP_MARGIN` |
| `W_LIFT_RAIL` | `60.0` | `assumed`, **M20** — the TV lift's own rail/plate width at the column. Used by `REACH_KEEPOUT` and `RIB_PAD_GAP`. |
| `T_LIFT_RAIL` | `unknown` (no geometry uses it directly in this file — it feeds the BOM's M8 bolt-length formula only, §6 step 6) | **M20** |
| `WALL_GAP` | `150.0` | **User-stated** (2026-09-28): "about 15–20 cm of space behind the TV" (TV-lift mount) — 150 is the conservative end of that range, not a blind guess. Asserted against the case's own lid-top Z (§5, B14). The lift's own exact standoff and any arm depth stay `assumed` pending M20, but the headline figure is user-given. |
| `REACH_KEEPOUT` | `max(PAD_BOSS_D, W_LIFT_RAIL)/2 + KEEPOUT_CLR` | derived, §3.3 |
| `REACH` | `L_max/2 + REACH_KEEPOUT` | derived, §2 |
| `YJ_V` | `RAIL_KEEPOUT_Y[1] + KEEPOUT_CLR + m3_counterbore_r + norm([JOINT_S/2, JOINT_P/2])` | derived, §2 (architect's own formula, RD2) |
| `VTV_PLATE_T` | `11.0` | rebased from arch's own re-derivation (Plan A B7); **same physical derivation applies here verbatim** — `2T - (T+RIB_H) >= SWEEP_CLR` |
| `RIB_T` | `MCC_WALL` = 3.0 | unchanged |
| `RIB_H` | `MCC_RIB_HEIGHT_RATIO_MAX * RIB_T` = 9.0 | unchanged |
| `SWEEP_CLR` | `2.0` | unchanged |
| `ARM_W` | `40.0` | unchanged from rev 1 |
| `PAD_BOSS_D` | `30.0` | unchanged from rev 1 — **now a flat spacer disc diameter, not a raised boss diameter** (§3.3) |
| `RIB_PAD_GAP` | `W_LIFT_RAIL/2 + KEEPOUT_CLR` | new, §3.3, `assumed`-derived, flagged for tightening post-M20 |
| `CENTRE_H` | `2*(YJ_V + ARM_W/2)` ≈ 144.7 | derived, §2 |
| `C_HALF` | `90.0` | unchanged from rev 1 |
| `LAP_L`, `JOINT_S`, `JOINT_P`, `LAP_RIB_GAP`, `KEEPOUT_CLR` | `30.0`, `14.0`, `20.0`, `1.0`, `1.0` | unchanged from rev 1 — same M3 insert class, same edge-distance arithmetic |
| `M3_COUNTERBORE_DEPTH` | `M3_HEAD_K + 1.3` | rebased, matches arch's own Plan-A-derived value (T1-57 at `VTV_PLATE_T=11`) |
| `M3_JOINT_SCREW_L` | `12` | rebased, matches arch (was 10) |
| `M8_HEAD_K`, `M8_WASHER_D`, `M8_WASHER_H` | `8.0`, `16.0`, `1.6` | unchanged — **used only for the BOM's washer/head geometry now, since the pad itself has no counterbore for them** |
| `ARROW_DEPTH`, `ARROW_L`, `ARROW_W` | `0.6`, `8.0`, `6.0` | unchanged from rev 1 |
| reused, no new constant | `MCC_M8_CLR_D`, `MCC_M3_CLR_D`, `MCC_INSERT_M3`, `MCC_RAIL_*`, `MCC_M3_MAJOR_D` (renamed), `MCC_WALL`, `MCC_BUILD`, `MCC_BED_MARGIN`, `MCC_EPS`, `MCC_RIB_HEIGHT_RATIO_MAX`, `MCC_CLR_SLIDE` (fastener clearance only, not rail) | `constants.scad`, current Plan-A-amended values |

Deleted from rev 1: `COLUMN_SIDE` and everything that read it (§0, §3.2).

---

## 5. Tier-1 asserts (Part A) — placeholder ids; **final `T1-` numbers start at T1-64** (RD6 — Plan
A's own verdict already assigns T1-62/T1-63, so the next free id after A merges is T1-64)

| Id | Assert | Source |
|---|---|---|
| B1 | arm bbox and centre bbox ≤ `MCC_BUILD - 2*MCC_BED_MARGIN` (244) per axis | same rule as arch's T1-47-class check |
| B2 | `case_x_hi + TV_SIDE_MARGIN ≤ TV_SIDE_CLEAR` | the per-TV feasibility gate, now the right check for an outboard reach (§3.2 resolves the old inconsistency) |
| B3 | `REACH - L_max/2 ≥ REACH_KEEPOUT - MCC_EPS` | self-consistency, §3.3 |
| B4 | `case_y_hi ≤ HALF_PITCH_V - PAD_BOSS_D/2` **and** `case_y_lo ≥ -(HALF_PITCH_V - PAD_BOSS_D/2)` | case clears both screws in Y |
| B5 | `2*VTV_PLATE_T - (VTV_PLATE_T + RIB_H) ≥ SWEEP_CLR - MCC_EPS` | §2, no `+MCC_FLOOR_T` term (flush since Plan A) |
| B6 | `RIB_T ≤ 0.6*VTV_PLATE_T`; `RIB_H ≤ MCC_RIB_HEIGHT_RATIO_MAX*RIB_T` | unchanged rule |
| B7 | rail footprint fits `C_HALF`; rail keep-out Y-span inside `±CENTRE_H/2` | unchanged rule, new numbers |
| B8 | every M3 counterbore (both joints) clears the rail keep-out rectangle by ≥ `KEEPOUT_CLR`, via a private circle–rect gap helper (re-implemented in this file, never imported from arch) | verified 13.2 mm clear (§2) |
| B9 | both rib edges of both arms, sampled in ≤1 mm steps: clear the centre body by ≥ `KEEPOUT_CLR`; **and** stay outside the `RIB_PAD_GAP` zone near the pad; **and** clear the case's own mated footprint by `SWEEP_CLR` in Z where they overlap in X/Y | extends the rev-1 pattern; the pad-gap clause is new (§3.3) |
| B10 | insert-bore depth + skin ≤ `VTV_PLATE_T`; hole edge distances ≥ 2 mm | unchanged arithmetic |
| B11 | M3 screw stack: tip clears bore floor + 0.5 mm; engagement ≥ `1.5 * MCC_M3_MAJOR_D` | verified: tip clears by 1.4 mm, engagement 5.3 mm (§2) |
| B12 | **rewritten for the sandwich pad**: pad thickness (`VTV_PLATE_T`) ≥ some minimum bearing thickness for an M8 clearance hole — no counterbore/washer-seat assert exists any more (there is no counterbore) | RD3 |
| B13 | UP-arrow bbox stays ≥ `KEEPOUT_CLR` inside the body edge and outside the rail keep-out | unchanged rule, re-checked at the new `CENTRE_H` |
| B14 | **new** — the case's lid-top Z (`2*VTV_PLATE_T + H` ≈ 73) fits within `WALL_GAP` | RD4, `assumed` until M20 |
| B15 | **new** — `RIB_PAD_GAP` and the pad radius together do not exceed `REACH` itself (a rib cannot start beyond where the arm already ends) | sanity, catches a future parameter edit that makes `W_LIFT_RAIL` absurdly large without also flagging the arm-length consequence (§2's R-7 note) |

Deleted from rev 1: the old B14 (`COLUMN_SIDE` typo check) — no longer applicable, no mirror exists.

Also: `echo()` one summary line per render (`reach`, `alpha`, `arm_len`, both bboxes, `yj_v`,
`centre_h`, `tv_side_clear`, `w_lift_rail`, `wall_gap`, each with the word `assumed` where
applicable) — same convention as arch. **Never** echo the literal string `WARNING: unmeasured`.

---

## 6. Ordered implementation steps (Part A)

Branch off `main` **after Plan A merges** (RD-sequencing rule: no rail change may run in parallel
with this plan). Name it per whatever the user decides in §13 Q1 (open a GitHub issue first, or stay
ad hoc).

1. **Confirm Plan A's actual merged constants match §0's table exactly.** If any value differs from
   what Plan A's verdict specifies, stop and report — do not silently adapt.
2. Create **`models/brackets/vertical-tv-bracket.scad`** (style: `arch-tv-bracket.scad` as Plan A
   leaves it — header with frame, Z-stack table, the "why one fixed outboard layout, no mirror" note
   from §3.2, the sandwich-pad note from §3.3; `$fa=1; $fs=0.4;` only; `include <mcc/mcc.scad>` +
   all 8 device includes; `// build.py: parts = arm, centre, spacer`;
   `// build.py: print_count = arm:2`; `part = "centre";` default):
   1. §4's parameters, each with its basis comment.
   2. `_mcc_vert_tv_envelope_max()` — identical pattern to arch's own, over a `_VERT_TV_DEVS` list
      (this file's own copy, not shared with arch's `_ARCH_TV_DEVS`).
   3. `mcc_vert_tv_geom(tv_side_clear=, w_lift_rail=, wall_gap=)` — pure function, returns a struct
      with every field named in §2/§4, defaulting each optional parameter to its `assumed` constant.
   4. `_mcc_vert_tv_joint_holes(g)`, `_mcc_vert_tv_place(g, side)` /
      `_mcc_vert_tv_place_assembly(g, side)` (using `rotate([0,0, side>0 ? -ALPHA : +ALPHA])` per
      §3.4's proof), `_mcc_vert_tv_xform(p, side, g)`, a private
      `_mcc_vert_tv_circle_rect_gap(centre, r, rect_x, rect_y)`.
   5. `mcc_vert_tv_arm(g)`: **flat pad** (a disc of diameter `PAD_BOSS_D`, thickness `VTV_PLATE_T`,
      flush with the plate — no raised boss, no counterbore) + M8 through-hole only (`MCC_M8_CLR_D`)
      + two top-face edge ribs, starting `RIB_PAD_GAP` from the pad centre and stopping
      `LAP_RIB_GAP` short of the lap + 4 heat-set insert bores in the lap. TV face on the bed
      (Z=0). Every functional hole `$fn=64, circum=true`, `MCC_EPS` overlaps at both faces.
   6. `mcc_vert_tv_centre(g)`: `union() { difference() { union(){ body, two tabs (arm's own end
      segment, placed via _mcc_vert_tv_place) }; mcc_rail_male_window(plate_t=VTV_PLATE_T); 4 M3
      counterbored clearance holes per tab; UP-arrow deboss }; mcc_rail_male(plate_t=VTV_PLATE_T) }`
      — rail unioned last, outside the `difference()`, matching Plan A's own `arch-tv-bracket.scad`
      pattern exactly.
   7. **`mcc_vert_tv_spacer()`**: a flat disc, diameter `PAD_BOSS_D`, thickness `VTV_PLATE_T`, one
      M8 through-hole (`MCC_M8_CLR_D`), centred. No other features. This is the "other column"
      part (§3.5) — printed twice (`// build.py: print_count = spacer:2`, a second marker line).
   8. `mcc_vert_tv_assert(g)` — B1–B15 (§5); call at top level.
   9. `echo()` summary (§5).
   10. `part == "arm"` / `"centre"` / `"spacer"` dispatch; non-exported `"assembly"` /
       `"assembly_sweep"` previews, mirroring arch's own (ghost TV-back slab, a marker at
       `TV_SIDE_CLEAR` on the reach axis, ghost case mated via
       `translate([REACH, MCC_RAIL_Y, 2*VTV_PLATE_T]) rotate([0,0,180])` — **no `+ MCC_FLOOR_T`
       term**, matching Plan A's flush convention — using the same shipped-fan Plus-family preview
       variant arch uses, with `tripod_insert: false`); `else assert(false, …)`.
3. Render locally for `echo` + preview PNGs (`-D part="assembly"` and `"assembly_sweep"`): confirm
   patch wall down, case sits entirely outboard and clear of both screws/pads, arms flat, centre
   stacked, UP arrow legible.
4. `tests/test_vertical_tv_bracket.scad` — `use`, never assigns `part`, exercises
   `mcc_vert_tv_geom()`/`mcc_vert_tv_assert()` for a few `tv_side_clear` values including one just
   above B2's computed minimum (§2: ≈252.5) and one large-TV case; documents the one failing case
   without running it.
5. `models/brackets/README.md`: new `vertical-tv-bracket.scad` row — sandwich mount, one VESA-300
   column, fixed +X-outboard layout, no mirror option; print-orientation row for `arm`/`centre`/
   `spacer`.
6. `BOM.md` → new `### vertical-tv-bracket.scad` subsection: `arm` ×2, `centre` ×1, `spacer` ×2 (all
   ASA); **M8 SHCS ×4** (all four VESA holes now carry a bolt) — "Length: MEASURE, do not guess" —
   `mount_thickness_at_hole (M20: T_LIFT_RAIL) + pad/spacer height (VTV_PLATE_T=11) + usable TV
   thread depth (M20) − ≥1 mm, rounded down"; **no** M8 washers/heads seated in a counterbore (the
   TV lift's own hardware stack governs the outer end now — note this plainly so a builder does
   not go looking for a pocket that no longer exists); M3×12 SHCS ×8; M3 heat-set insert ×8. **No
   sleeves, no steel spacers** (R42, ASA accepted).
7. `.claude/skills/print-check/SKILL.md` §3: one new row, `arm`/`centre`/`spacer` orientations; note
   the `TV_SIDE_CLEAR`/`W_LIFT_RAIL`/`WALL_GAP` overrides.
8. `.claude/skills/new-case-variant/SKILL.md` checklist: a **second**, independent bullet (own list,
   `_VERT_TV_DEVS`) alongside arch's existing one.
9. Goldens — `tests/golden/brackets/vertical-tv-bracket.{arm,centre,spacer}.json`. Render locally
   with the pinned nightly (confirmed available in this environment); fallback via CI artifact if
   not. **No existing golden may move** — `arch-tv-bracket.*`/nothing else in `tests/golden/brackets/`
   changes here (Part B's own goldens are listed in §7).
10. Push; PR to `main`; CI green (including the Bambu slicer gate) before merge. PR body cites this
    plan, lists §9's open M20 items, and names the R42/R43 user decisions already made so a reviewer
    sees them as settled, not re-litigated.

---

## 7. Part B — Arch bracket sandwich mode (additive, on top of Plan A's own edits)

Plan A already rewrites `ARCH_PLATE_T`, `CENTRE_W`, `LAP_RIB_GAP`, the M3 stack, the Z-stack, the
mate transform, `centre_z_max`, and the preview's `tripod_insert` flag (its own Appendix D.1) — **none
of that is repeated or re-touched here.** Part B adds, on top of that already-amended file.

### 7.1 The new finding (architect's Amendment 1): the sandwich-mode sweep crosses the right column

Arch's own rail sits centred at `X=0`, between its two top screws at `X=±HALF_PITCH=±200`. Its case
slides on from `+X` (D34's fixed convention) and, during engagement, reaches `L_max/2 + slide_clear
≈ 105.75+180.75 = 286.5 mm` from the arch's own centre — **past the right screw's column at
`X=200`, by ≈ 86.5 mm** (the architect's own verdict quotes ≈287 mm / ≈181 mm past final position for
the same figures). **In direct mode this crosses nothing** (a direct-mount arch precludes a coexisting
TV lift on those screws at all — that is exactly D47, now closed by retiring `tv-bracket` and adding
this sandwich mode instead). **In sandwich mode, the TV lift's own rail — and, in this plan's flat-pad
design, the M8 bolt head bearing on its outer face — occupies that same column**, and the case's floor
must clear both in Z as it slides over.

Binding check, per the architect's Amendment 1 (exact formula): with a **flat pad at the arm's own
top** (this plan's design, §7.2 — not the raised, counterbored boss Plan A already ships in direct
mode), the obstacle stack at the crossed column reaches `ARCH_PLATE_T + T_LIFT_RAIL + K_BOLT_HEAD`
off the TV back, and the case floor (at `Z_RAIL = 2*ARCH_PLATE_T` in Plan A's own direct-mode
formula) must clear it by `ARCH_SWEEP_CLR`:

```
2*ARCH_PLATE_T >= ARCH_PLATE_T + T_LIFT_RAIL + K_BOLT_HEAD + ARCH_SWEEP_CLR
i.e.  ARCH_PLATE_T >= T_LIFT_RAIL + K_BOLT_HEAD + ARCH_SWEEP_CLR
```

**At this plan's own assumed placeholders** (`T_LIFT_RAIL = 5` mm — a thin steel lift-rail guess;
`K_BOLT_HEAD = M8_HEAD_K + M8_WASHER_H = 8.0 + 1.6 = 9.6` mm — the ISO 4762/7089 nominal stack, reused
from Part A, not itself a guess even though the *specific* bolt is still to be chosen;
`ARCH_SWEEP_CLR = 2.0`, unchanged): `11 >= 5 + 9.6 + 2 = 16.6` — **fails by 5.6 mm.** This is treated
as a real, load-bearing finding (R-9, §10), not smoothed over — Plan A's own `ARCH_PLATE_T=11` is
owned by Plan A and is not reduced or otherwise touched here; instead, sandwich mode gets its own,
additional rise, entirely inside Part B's own scope.

### 7.2 The fix: a sandwich-mode-only taller centre plate ("raising the rail face")

The **arm** stays exactly as Plan A leaves it (`ARCH_PLATE_T=11`, unchanged in every mode — the M8
pad, the lap, the insert bores are all arm-side and mode-independent). Only the **centre** plate
grows, and only in sandwich mode:

```
CENTRE_T_SANDWICH = T_LIFT_RAIL + K_BOLT_HEAD + ARCH_SWEEP_CLR        // >= 16.6 at the placeholders
Z_RAIL_SANDWICH   = ARCH_PLATE_T + CENTRE_T_SANDWICH                  // >= 27.6
```

(Direct mode keeps Plan A's own `CENTRE_T_DIRECT = ARCH_PLATE_T = 11`, `Z_RAIL_DIRECT =
2*ARCH_PLATE_T = 22`, untouched.) At the placeholders this raises the case's own lid-top Z from ≈73 mm
(direct) to `Z_RAIL_SANDWICH + H ≈ 78.6` mm — still comfortably inside the user-stated 150 mm
`WALL_GAP` (§Changelog 13), which is exactly why "the space is available" resolves this rather than
blocking it.

**Consequence for the M3 lap joint, re-derived (not guessed) for the taller sandwich centre:**

```
m3_counterbore_depth   = M3_HEAD_K + 1.3 = 4.3          // unchanged, Plan A's own value
m3_head_seat_z_sandwich = Z_RAIL_SANDWICH - m3_counterbore_depth     // = 23.3 at the placeholders
tip_z_target            = ARCH_PLATE_T - 5.7 = 5.3       // same arm-side engagement Plan A targets (unchanged: the arm/insert side of the joint does not change)
M3_JOINT_SCREW_L_SANDWICH = m3_head_seat_z_sandwich - tip_z_target   // = 18.0 at the placeholders -- round UP to the nearest stock length
```

At the placeholders this gives **M3×18** for sandwich mode specifically (vs. Plan A's own M3×12 for
direct mode) — verified: tip clears the bore floor by 1.0 mm (≥0.5 required), engagement 5.7 mm
(≥4.5 required, even better than direct mode's own 5.3 mm because the length was rounded up to a
stock size). **Re-run this exact arithmetic once `T_LIFT_RAIL`/`K_BOLT_HEAD` are measured (M20) —
every number above moves if they do.**

**Structural consequence, flagged not re-derived:** arch's own case centre-of-mass offset in sandwich
mode becomes `Z_RAIL_SANDWICH + H/2 ≈ 53.1 mm` off the TV back (vs. ≈47.5 mm for Part A's vertical
bracket and for arch's own direct mode — both use the same `2T+H/2` shape) — a larger moment arm,
proportionally, than either of the numbers this plan's own §11 checks. Re-run §11's arithmetic with
this offset for arch's sandwich mode specifically before relying on "same order of magnitude as
arch's own ≈1°/≈3°" — this plan states the number but does not re-verify the tilt estimate against it.

### 7.3 Ordered steps

1. A new top-level parameter: `MOUNT_MODE = "direct";` (default — today's behaviour, unchanged) or
   `"sandwich"` (new). Tier-1 assert: `assert(MOUNT_MODE == "direct" || MOUNT_MODE == "sandwich", …)`.
2. New assumed parameters (this file's own, not Plan A's): `T_LIFT_RAIL = 5.0`, `K_BOLT_HEAD =
   M8_HEAD_K + M8_WASHER_H` (= 9.6, reusing Plan A's own arch M8 constants), each commented `assumed,
   M20`.
3. `mcc_arch_tv_geom()` gains mode-dependent fields: `centre_t = MOUNT_MODE=="direct" ?
   ARCH_PLATE_T : (T_LIFT_RAIL + K_BOLT_HEAD + ARCH_SWEEP_CLR)`; `z_rail = ARCH_PLATE_T + centre_t`
   (replaces Plan A's bare `2*ARCH_PLATE_T` — **only within this file's own mode-aware formula**, Plan
   A's direct-mode-only formula is unchanged for `MOUNT_MODE=="direct"` since `centre_t` reduces to
   `ARCH_PLATE_T` there); `m3_joint_screw_l = MOUNT_MODE=="direct" ? 12 : 18` (§7.2 — replace the
   literal with the derived value once `T_LIFT_RAIL`/`K_BOLT_HEAD` stop being placeholders).
4. In `mcc_arch_tv_arm(g)`'s M8 hole cut: wrap the **counterbore** cut (not the through-hole) in
   `if (MOUNT_MODE == "direct") { … }`. In `"sandwich"` mode the through-hole (`MCC_M8_CLR_D`) spans
   the pad's full height, but the pad itself becomes **flat at the arm's own top face** (`Z =
   ARCH_PLATE_T`, matching this plan's Part A pad design and the architect's own "flat pads at the arm
   top" wording) — **not** the raised, counterbored boss direct mode keeps. `pad_clamp_t` becomes
   mode-dependent: `MOUNT_MODE=="direct" ? (arm_top_z - m8_counterbore_depth) : ARCH_PLATE_T`.
5. `mcc_arch_tv_centre(g)` uses `struct_val(g, "centre_t")` for its own body/tab thickness and
   `struct_val(g, "z_rail")` for the rail placement — both already mode-aware from step 3.
6. New Tier-1 assert (this file's own, the §7.1 formula): `assert(MOUNT_MODE=="direct" ||
   struct_val(g,"z_rail") >= ARCH_PLATE_T + T_LIFT_RAIL + K_BOLT_HEAD + ARCH_SWEEP_CLR - MCC_EPS, …)`
   — trivially true by construction (the formula that sets `centre_t` guarantees it), but stated
   explicitly so a future edit to any of the four inputs fails loudly instead of silently.
7. Add **`mcc_arch_tv_spacer()`**: a flat disc, diameter `PAD_BOSS_D` (Plan A's own arch value),
   thickness = `struct_val(g, "centre_t")` (**mode-dependent** — matches whichever pad height is
   actually in use, so the bottom row's spacers stay coplanar with the top row's pads in *either*
   mode), one M8 through-hole, centred. This is the arch bracket's **bottom row** spacer — needed only
   in sandwich mode, always discoverable.
8. Update the file's own `// build.py: parts = arm, centre` marker to `// build.py: parts = arm,
   centre, spacer`, and add `// build.py: print_count = spacer:2`.
9. Update `mcc_arch_tv_assert(g)`: every existing M8-pad assert (boss wall / clamp thickness,
   Plan-A's T1-58-class) and the M3 stack assert (T1-57-class) must hold under **both** modes —
   verify by rendering both, not by inspection.
10. Update the `"assembly"`/`"assembly_sweep"` previews: keep `"direct"` as the shipped default (Plan
    A's own goldens/pictures stay undisturbed), but add one non-exported ghost cuboid — a translucent
    box at `(HALF_PITCH, 0, ARCH_PLATE_T)`, size `[W_LIFT_RAIL, W_LIFT_RAIL, T_LIFT_RAIL+K_BOLT_HEAD]`
    (all `assumed`, same parameters as §7.1) — **shown only when `MOUNT_MODE=="sandwich"`**, so
    rendering `assembly_sweep` in sandwich mode visually confirms the case floor clears it, the same
    "verify by picture" rule arch's own header comment already applies to the rail orientation.
11. `models/brackets/README.md`: add the direct-vs-sandwich mode note to the existing arch row,
    including the now-closed D47 caveat (a TV-mounted lift and the arch's own top-row holes cannot
    both be direct-mounted at once) — **state plainly that `MOUNT_MODE="sandwich"` is exactly the fix
    for that conflict**, with the §7.1 Z-clearance caveat spelled out, not just the mode switch.
12. `BOM.md` → arch bracket's existing section gains a `spacer` row (×2, ASA, sandwich mode only), the
    M3×18 note for sandwich mode's lap screws (vs. the existing M3×12 for direct), and the same
    "all four holes get a bolt in sandwich mode, only the top two in direct mode" caveat as Part A's
    own BOM entry.
13. Goldens: **new** `tests/golden/brackets/arch-tv-bracket.spacer.json` only, produced with
    `MOUNT_MODE` at its default (`"direct"` — the spacer's own thickness in that mode is
    `ARCH_PLATE_T=11`, per step 7's formula). **`arch-tv-bracket.{arm,centre}.json` must be
    byte-identical before and after this whole section** (`MOUNT_MODE` defaults to `"direct"`, so
    `arm`/`centre`'s own exported geometry is untouched) — confirm with `git diff` before committing.
14. Render **both modes** locally (`-D part="centre" -D MOUNT_MODE=\"sandwich\"`, etc.) and eyeball:
    the counterbore's absence, the taller centre plate, and — critically — re-render
    `"assembly_sweep"` in sandwich mode and confirm by picture that the case floor visibly clears the
    (ghost) lift-rail-and-bolt-head obstacle at the right column, not just by trusting the assert.

---

## 8. Verification commands and how this plan's own numbers were checked

This plan's §2 table was produced by extracting the **current** `origin/main`'s `lib/mcc/**` (for
the unaffected `mcc_case_dims()` envelope function) into a scratch `lib/`, then computing every
rail-dependent quantity with Plan A's **verdict-specified** constants **transcribed by hand** (no
live `rail.scad` with them exists yet) in a throwaway probe script, run with the pinned OpenSCAD
nightly:

```
# lib/mcc/** mirror (device envelope only — unaffected by Plan A):
git archive origin/main lib/mcc | tar -x -C <scratch>/lib --strip-components=1
cp -r lib/BOSL2 <scratch>/lib/BOSL2

OPENSCADPATH=<scratch>/lib "C:\Program Files\OpenSCAD (Nightly)\openscad.com" \
    --backend=Manifold -o <scratch>/probe.csg <scratch>/probe.scad
```

**This must be re-run against Plan A's real, merged `rail.scad` once it exists**, not trusted forever
against a hand-transcription — the numbers matched the architect's own independent estimates in
Plan A's verdict (`YJ_V`≈52.4, `CENTRE_H`≈145) to within rounding, which is corroborating evidence,
not a substitute for re-checking against the real file.

Once both files exist for real (repo root, `OPENSCADPATH=lib`, on a branch created after Plan A
merges):

```
python scripts/build.py doctor                                        # parts=[arm, centre, spacer] for both brackets
python scripts/build.py render brackets/vertical-tv-bracket
python scripts/build.py render brackets/arch-tv-bracket               # both MOUNT_MODE values, manually
python scripts/build.py check --all
python scripts/build.py golden --update brackets/vertical-tv-bracket brackets/arch-tv-bracket.spacer
python scripts/build.py golden                                        # confirm arch's arm/centre goldens did NOT move
python scripts/build.py slicer-check brackets/vertical-tv-bracket brackets/arch-tv-bracket --jobs 2
python scripts/build.py smoke
python scripts/build.py review
```

---

## 9. M20 — exact measurements needed before this plan can leave `assumed`

**Resolved by the user, 2026-09-28 — no longer open:**

- ~~`WALL_GAP`~~ — **150–200 mm behind the TV** (TV lift), 150 used as the conservative bound
  (§Changelog 13). The lift's own exact standoff/arm depth within that gap is still `assumed`, but the
  headline figure is not.
- ~~Free space beside the TV, in the slide direction~~ / ~~`TV_SIDE_CLEAR`~~ — **"space around the
  column is not a constraint"** (§Changelog 14, R-4 closed). `TV_SIDE_CLEAR` is set to a generous
  `500` and kept only as a permanent, cheap assert (B2), not an open risk.

**Still open, named `assumed` parameters with asserts, each a one-line change once measured:**

1. **TV model and its real VESA pattern** — confirm 400×300 (or the exact figures), and the M8
   thread depth at each hole.
2. **`W_LIFT_RAIL`** — the TV lift's own rail/plate width at the column (Part A: drives
   `REACH_KEEPOUT`, `RIB_PAD_GAP`, and — see §2's R-7 flag — whether `REACH` stays comfortably under
   the arm-length bed-fit ceiling).
3. **`T_LIFT_RAIL`** — the TV lift's own rail/plate thickness at the column (Part A: feeds the BOM's
   M8 bolt-length formula for all four bolts. **Part B: also drives `CENTRE_T_SANDWICH`/`Z_RAIL_
   SANDWICH` and the sandwich-mode M3 screw length, §7.1–7.2 — currently `assumed = 5.0`**).
4. **`K_BOLT_HEAD`** (Part B only) — the actual M8 bolt/washer combination's head height once chosen;
   `9.6` (ISO 4762/7089 nominal) is a reasonable default, not a guess, but confirm once a specific
   bolt is selected (§7.1).
5. **Wall-mount/lift footprint/arms within ~250 mm of either bracket's own arm/pad zone** — whether
   anything else (an arm, a cable channel) intrudes, independent of the now-resolved lateral-clearance
   question above (this is about *local* obstacles near the columns, not the wider room).

**Note on scope:** M20 no longer blocks the lateral/depth feasibility questions it originally covered
(§Changelog 13–14) — what remains open is specifically the TV-lift *hardware*'s own dimensions at the
column, needed for Part A's `REACH`/BOM numbers and Part B's new sandwich-mode Z-clearance fix.

---

## 10. Risks (proposed ids; architect assigns final numbers at the re-gate, after Plan A's own R40–43
land)

- **R-1 — topology still not user-validated beyond the architect's approval of its direction.** The
  hub shape and the exact joint math are this research pass's inference; the architect approved the
  *direction* (A1) but a physical/visual sign-off after the first preview render is still worthwhile.
- **R-2 — every number in §2 depends on a hand-transcription of Plan A's verdict, not live code.**
  Re-verify against the real merged `rail.scad`/`constants.scad` before implementing (§8).
- **R-3 — `W_LIFT_RAIL`/`T_LIFT_RAIL` remain `assumed`, unmeasured** (§9). `REACH`, the arm bbox and
  the BOM bolt length are provisional until M20's lift-hardware measurements land. **`WALL_GAP`
  (150 mm) and `TV_SIDE_CLEAR` are no longer in this category** — both are now user-stated/confirmed
  non-binding (§Changelog 13–14) and kept only as cheap asserted insurance, not open risks.
- **R-4 — CLOSED by the user (2026-09-28).** The transient slide-on sweep (≈412–423 mm from the
  column, depending on `W_LIFT_RAIL`) was flagged as needing confirmation that free space exists that
  far beside the TV. The user has confirmed "space around the column is not a constraint" — this risk
  is resolved, not merely deprioritised. B2 stays as a permanent assert regardless.
- **R-5 — sweep clearance is exactly at the minimum (2.0 mm)**, same margin arch ships with; zero
  slack for a future parameter tweak.
- **R-6 — the sandwich clamp path carries ASA under sustained M8 preload, by explicit user
  acceptance (R42).** Creep is a real, cited risk (`fasteners-and-hardware.md:140`), not eliminated
  by the user's decision, only accepted. The physical tilt/creep check (structural §11) remains the
  real verification, to be repeated periodically per the user's own judgement, not just once at
  first print.
- **R-7 — if `W_LIFT_RAIL` measures much larger than the 60 mm placeholder, `REACH` grows and the
  arm print bbox approaches the 244 mm cap** (§2). Above `REACH`≈190 mm the arm needs splitting into
  two printed parts — a design change, not a parameter edit. Re-run §8's probe with the measured
  value before implementing, specifically to catch this. (`WALL_GAP`'s now-generous 150 mm headroom
  does not relax this — it is an X/Y bed-fit ceiling, not a Z/depth one.)
- **R-8 — CLOSED.** Both brackets now use the same flat, flush, no-counterbore pad philosophy in
  sandwich mode (§7 Part B, revised per the architect's Amendment 1: "flat pads at the arm top"
  applies to arch too) — the earlier draft's asymmetric-convention concern no longer applies.
- **R-9 — NEW, load-bearing: arch's existing 11 mm plate is probably not tall enough to clear the TV
  lift's own rail + M8 bolt head where its sandwich-mode sweep crosses the right-hand column** (§7
  Part B, per the architect's Amendment 1 finding). At this plan's own assumed placeholders
  (`T_LIFT_RAIL=5`, bolt head+washer≈9.6 mm) the check `ARCH_PLATE_T ≥ T_LIFT_RAIL + K_BOLT_HEAD +
  ARCH_SWEEP_CLR` (11 ≥ 16.6) **fails**. Part B proposes a concrete, sandwich-mode-only taller centre
  plate as the fix (a formula, not a placeholder) — the user's "150–200 mm behind the TV" answer is
  exactly the depth headroom this needs, but the **exact** rise is still `assumed` pending M20's
  `T_LIFT_RAIL`/bolt-head figures. Do not implement Part B's sandwich mode before re-running this
  check with measured values.
- **Inherited, both parts:** M15 (rail-latch pull test) and the structural tilt measurement (§11)
  gate printing **either** bracket for actual use, same as every rail-mounted bracket in this repo.

---

## 11. Structural sanity check (rebased at `VTV_PLATE_T=11`; explicitly lighter than a full FEA)

Reuses the same load/material assumptions as before (all still `assumed`): design mass 1.5 kg,
`F_D = 3*1.5*9.81 ≈ 45 N`, `E_eff=1500 MPa`, `G≈555 MPa`. With the flush Z-stack (no pedestal), the
case's centre-of-mass offset from the TV back is now `2*VTV_PLATE_T + H/2 = 22 + 25.5 = 47.5 mm`
(was 44.5 with the old rail's pedestal) — verified in §8's probe. Moment: `M = 45 N * 47.5 mm ≈
2097 N·mm ≈ 2.1 N·m` (matches the architect's own independent estimate in Plan A's verdict, RD10,
exactly).

**Sandwich-specific addition, not present in the old direct-mount analysis:** the arms now carry the
case's load through a **clamped joint**, not a screwed-into-plastic direct mount. The relevant
contact faces are: (a) the TV's own back panel against this bracket's flat pad face (bearing, in
compression, under the M8 preload); (b) the TV lift's own rail against the pad's *other* flat
face (also compression, same preload); the M8 bolt itself carries the clamp's own tension. The
out-of-plane moment computed above still has to react through the **arm's own bending/torsion
stiffness** exactly as before (§6's arm cross-section is unchanged from a structural standpoint) —
the sandwich changes *how the pad is loaded axially*, not the arm's own moment-carrying path. Order
of magnitude is therefore still expected to match arch's own ≈1° static / ≈3° dynamic tilt result,
**not independently re-derived with rigor here.**

**Required, not optional:** the same physical tilt gate as before (static rail tilt ≤2° after 24h
with the heaviest Plus SKU; if it fails, `VTV_PLATE_T → higher` and re-derive every Z plane) —
**plus a periodic re-check of clamp preload/creep** given R42's accepted ASA-in-clamp-path risk (not
a one-time gate; the user's own judgement on inspection interval, not this plan's to set).

---

## 12. What the architect must record (after re-gating — not the developer's job)

- The B1–B15 asserts (§5) and Part B's own new asserts (§7.3 steps 1, 6), renumbered into the live
  `T1-` sequence, starting at **T1-64** (confirm this is still the next free id once Plan A has
  actually merged).
- R-1…R-9 (§10), renumbered into the live risk sequence. **R-4 and R-8 are closed** (user-resolved) —
  record them as closed, not as still-open items carried forward.
- Confirmation (or correction) of every number in §2's table, independently re-derived against Plan
  A's **real, merged** `rail.scad`/`constants.scad` — not just this plan's hand-transcription.
- **R-9, Part B's new sandwich-mode Z-clearance finding (§7.1–7.2)** — independently re-derive
  `CENTRE_T_SANDWICH`/`Z_RAIL_SANDWICH`/the M3×18 figure the same way B1 was caught in rev 1's own
  gate; this plan's own placeholders (`T_LIFT_RAIL=5`, `K_BOLT_HEAD=9.6`) are a first pass, not
  ground truth.
- Whether Part B's `MOUNT_MODE` parameter, mode-dependent `z_rail`/`centre_t` formula, and `spacer`
  part are approved as specified.
- A ruling on §13 question 1 (GitHub issue).
- The M20 measurement list (§9) as the architecture record's own open-measurement entry — narrower
  than Plan A's own verdict Appendix G7 M20 row now that the lateral/depth questions are resolved
  (§Changelog 13–14); record the resolution, not just a superseding list.

---

## 13. Open questions for the user

1. **GitHub issue** — still not opened (rev 1's question 1, unresolved; Plan A's own Amendment 1
   records "the user has been asked", answer still pending). Title suggestion: "VESA column TV
   bracket, sandwiched mount (Samsung 400×300) + arch sandwich mode." Open one before implementation,
   or confirm staying ad hoc?
2. **M20, remaining items (§9)** — the TV model and its exact VESA pattern/thread depth,
   `W_LIFT_RAIL`, `T_LIFT_RAIL`, `K_BOLT_HEAD` (once a specific M8 bolt/washer is chosen), and any
   TV-lift hardware within ~250 mm of either bracket's own arm/pad zone. (`WALL_GAP` and
   `TV_SIDE_CLEAR` are already answered, §Changelog 13–14.) None of Part A's `REACH`/BOM numbers or
   Part B's sandwich-mode rise leave `assumed` without these.
3. **Part B's proposed sandwich-mode rise (R-9, §7.1–7.2)** — at this plan's own placeholders, arch's
   sandwich mode needs a centre plate roughly 5.6 mm taller than direct mode's (16.6 mm vs. 11 mm) and
   a longer M3×18 lap screw, purely to clear the TV lift's own rail and bolt head during slide-on. Is
   this an acceptable-looking shape for the arch bracket, or should a different mitigation be
   preferred once the real `T_LIFT_RAIL`/bolt dimensions are in hand (§10 R-9)?
4. **Periodic re-inspection of the ASA clamp joint** (R-6) — now that steel sleeves are declined, is
   there a preferred re-check interval, or should this plan simply note "inspect if anything feels
   loose" and leave it at that?
5. **`spacer` parts always declared vs. only in sandwich mode** — both new "other column/row" spacer
   parts are proposed as always-discoverable (cheap, harmless if unused in direct mode). Confirm
   that's preferable to hiding them behind a config flag that would need re-rendering to surface.

---

## Architect verdict (rev 2)


Gate: `solution-architect`, 2026-09-28. Plan: `scratchpad/plans/D-vesa-400x300-bracket.md` (rev 2). The rev-1 verdict (`D-vesa-400x300-bracket.VERDICT.md`, including its Amendment 1) stays as history.

Checked against:
- C (PR #57);
- A as amended by its verdict, including Amendment 1 (A is being implemented on `feature/wide-dovetail`);
- the user decision of 2026-09-28: **gravity lock only, D34 latch removed, the case always hangs patch-wall down**. This becomes plan F, analysed in `F2-dp48-lock-analysis.md`; `F-gravity-lock.md` is not written yet.

**Revisions and ids:**
- **F is rev 17.** Reserved for F's gate: T1-64…T1-69, D48–D50, R44–R46, M21, Q23.
- **D is rev 18** and takes: **T1-70…T1-90**, **D51**, **R47**, **M22**. It also updates R42, R43, M20 and Q22.
- After D, the next free ids are: T1-91, D52, R48, M23, Q24.

## Verdict: **APPROVED WITH BINDING CHANGES** (DB1–DB16). Implement after F: order C → A → F → D.

Rev 2 does what the rev-1 verdict asked:
- rebased on A;
- `YJ_V` derived rather than chosen;
- sandwich pads;
- ASA accepted;
- the fixed +X-outboard layout, with no mirror;
- a formula for the arch sandwich rise.

I re-derived the §2 numbers at A's constants and they check out: `REACH` 136.75, `YJ_V` 52.36, `ARM_LEN` 168.03, α 35.53°, `CENTRE_H` 144.71, sweep 2.0, `slide_clear` 180.75, M3 stack 1.4 / 5.3. So do Part B's figures: rise 16.6, lid 78.6, M3×18. Only one headline number is wrong (B8, DB4).

**What is wrong:**
1. **The latch dependency.** The rail keep-out is built from `MCC_RAIL_LATCH_ARM_T` and `MCC_RAIL_LATCH_ENGAGE`, and the centre calls `mcc_rail_male_window()`. F deletes all three.
2. **The ribs would sit under the TV lift's rail.**
   - `RIB_PAD_GAP = W_LIFT_RAIL/2 + 1` = 31 is measured along the arm. The arm runs diagonally, so at 31 mm along it the rib edge nearest the column is still at X ≈ 14, inside the lift-rail band (|X| ≤ 30).
   - The plan's note has the direction backwards: the diagonal *increases* the distance needed.
3. **B9 would fail as written.** The ribs are told to stop `LAP_RIB_GAP` short of the lap, i.e. at ≈152 mm along the arm. But the arm passes under the 180 × 145 hub body from ≈104 mm on. That rule worked for arch's 40 mm-high centre, not for the hub.
4. **The arch spacer thickness is wrong.** `centre_t` = 16.6 would skew the lift: the lift's rail bears on the arm pads at `ARCH_PLATE_T` = 11, so the bottom-row spacers must be 11.
5. **Part B misses the arch's own ribs against the lift rail** in sandwich mode.
6. **Part B leaves sandwich mode as a `-D` switch, so it is never exported.** No sandwich arm or centre would be rendered, golden-checked, slicer-checked or released, which breaks the print-ready contract (architecture.md §8).
7. **Smaller items:**
   - B8's "13.2 mm clear" repeats rev 1's joint-centre mistake.
   - B12 is vague.
   - B15 bounds the wrong quantity.
   - The spacer is sized from `PAD_BOSS_D`, a boss the design no longer has.
   - §3.3 still says arch keeps a raised boss.
   - The "round UP" M3 rule can bottom the screw out in the insert bore.

## Ruling on the order: **C → A → F → D**

1. **F changes the interface every bracket consumes:** the male flank (lock bump), the keep-out, the plate protocol (no window) and M15. Built after F, D is written once against the final interface. Built before F, D would carry a latch window F deletes, and F would have to edit, re-golden and re-slice D's new file on top of the arch and the coupon.
2. **D gains nothing by going first.** No bracket can be printed for use before the lock coupon (M15, as F redefines it) passes, so the vertical bracket and the arch sandwich parts would wait for F anyway.
3. **It keeps "one rail change at a time"** (A's verdict, Appendix F). F edits `rail.scad`; D never does.

**What D must do so it does not depend on the latch (binding, DB1):**
- D never calls `mcc_rail_male_window()`;
- D never reads any `MCC_RAIL_LATCH_*` (or other rail-internal) constant;
- D never builds the rail's footprint itself.

Instead D uses only two rail-owned public symbols, which F provides and the arch also uses after F:
- **`mcc_rail_male_keepout(len)`** for every keep-out;
- **`mcc_rail_male(len)`**, unioned onto the plate exactly as the post-F arch centre does. Copy that call when D is implemented.

Every D number that depends on the rail (`YJ_V`, `CENTRE_H`, α, `ARM_LEN`, bboxes, B7, B8, B13) is already a formula, so it re-derives itself from the accessor.

**If the order must flip** (C → A → D → F), do not implement D as written. D would first have to add two rail-owned seams to `rail.scad`:
- `mcc_rail_male_keepout()`, with the latch-era body;
- `mcc_rail_male_plate_cut(len, plate_t)`, which today is the window.

It would call only those plus `mcc_rail_male()`, and F would then rewrite the seams' bodies without touching a bracket file. That opens `rail.scad` inside D, so it needs a new architect ruling first.

## Requirements this verdict places on plan F

The coordinator relays these to F's researcher; F's gate checks them.

- **F-R1 — `mcc_rail_male_keepout(len = MCC_RAIL_LEN)`, a pure function in `lib/mcc/rail.scad`.**
  - It returns `[[x_min, x_max], [y_min, y_max]]` in the rail-local frame: the conservative plan-view extent of everything the male rail puts on or into the consumer's plate, lock bump included.
  - Consumers add their own clearance and apply their own placement; `rotate([0,0,180])` negates both ranges.
  - F migrates the arch's `RAIL_KEEPOUT_X/Y` to it. They currently read `MCC_RAIL_LATCH_*`, which F deletes.
- **F-R2 — after F, a consumer puts the rail on its plate with one call:** `union() { plate(); mcc_rail_male(len) }`.
  - No plate cut is left for consumers to know about.
  - If F keeps a `plate_t` parameter, it must be optional and ignorable.
  - If F ever needs a plate interaction again, it goes behind one rail-owned module, never behind exposed internals.
- **F-R3 — rev 17**, with ids from the reserved block above. F's `architecture.md` §3 rail rules gain the consumer rule that F-R1 and F-R2 imply; its text is part of F's verdict, not this one.

## Rulings on plan D rev 2 §12 and §13

- **Q1, GitHub issue:** closed — **#56**. Branch `feature/issue-56-vesa-column-bracket` (`ticket-source.md` naming).
- **Q2, M20 items still open:** architecturally fine as `assumed` parameters behind asserts, as the user asked. Each one must be named and commented `assumed, M20`, overridable with `-D`, and echoed in the file's summary line. No bracket is printed for use before M20 is measured (DB14).
- **Q3, the arch sandwich rise:** **approved**.
  - Crossing the right-hand column cannot be avoided. The slide direction is fixed (+X) and the case must end between the screws (T1-59), so its sweep has to cross x = +200. That leaves Z clearance as the only lever.
  - Only the centre grows, and only for the sandwich parts. The formula stays; the placeholders get re-run when M20 lands.
  - A non-binding alternative rev 3 may propose: one arch design for both mounts (flat pads plus the tall centre), which drops the mode split at the cost of a ≈ 5.6 mm deeper case in direct mode. That needs the user's OK.
- **Q4, re-inspection interval:** not architectural; the user decides. R42 records the recommended practice (re-check the preload 24–48 h after installation and at every rig-in) and M22 the first check. No gate.
- **Q5, spacers:** always discovered and exported parts. The `base_fan` precedent (issue #11) applies: anything a user may print is a discovered, golden-tracked, slicer-checked part.
- **Risk mapping.**
  - R-6 is **R42** and R-9 is **R43** (both updated, Appendix G).
  - R-7 becomes **R47**.
  - R-4 and R-8 are closed.
  - Not recorded as architecture risks: R-1 (preview sign-off at PR review), R-2 (process: DB16 re-runs the probe), R-3 (that is M20) and R-5 (the known zero-slack sweep, already asserted).

## Binding changes

**DB1 — Rail interface after F.**
- Implementation starts only after F merges.
- §0's consumed-symbols table and §3.1/A8 become exactly: `mcc_rail_male(len)`, `mcc_rail_male_keepout(len)` and the `MCC_RAIL_*` cross-section constants F keeps (`MCC_RAIL_LEN`, `MCC_RAIL_Y`, `MCC_RAIL_MALE_H`).
- Replace the keep-out formula with the rotated accessor range:
  `RAIL_KEEPOUT_Y = [-ko[1][1], -ko[1][0]]`, where `ko = mcc_rail_male_keepout(MCC_RAIL_LEN)`; `RAIL_KEEPOUT_X` is built the same way from `ko[0]`.
- §6 step 2.6's centre becomes: `union() { difference() { union(){ body, tabs }; M3 holes; arrow }; <rail placement> mcc_rail_male(...) }`, with the rail call copied from the post-F arch centre.
- If F's merged interface differs from F-R1/F-R2, stop and report.

**DB2 — Where the ribs start: derived in the assembly frame, clear of the lift rail.** In `mcc_vert_tv_geom()`:
```
RIB_PAD_GAP = (W_LIFT_RAIL/2 + KEEPOUT_CLR + (ARM_W/2) * sin(ALPHA)) / cos(ALPHA)
```
That is ≈ 52.4 at A's constants and ≈ 53 after F, against the plan's 31. It applies to both ribs. **B9 (T1-78)** gains an explicit lift-rail clause:
- sample every rib edge from `RIB_PAD_GAP` to `rib_end` in ≤ 1 mm steps;
- transform each sample to the assembly frame;
- assert `|X| ≥ W_LIFT_RAIL/2 + KEEPOUT_CLR` over the whole column, both arms.

**DB3 — Where the ribs end: derived from the hub body, not from `LAP_RIB_GAP`.**
- In `mcc_vert_tv_geom()`, `rib_end` is the smallest arm-local x at which either rib edge enters the centre body rectangle inflated by `KEEPOUT_CLR`, capped at `ARM_LEN − LAP_L/2 − LAP_RIB_GAP`.
- For the top arm the binding edge is the one toward the column (lateral −ARM_W/2); its entry is `(HALF_PITCH_V − (ARM_W/2)·cos(ALPHA) − (CENTRE_H/2 + KEEPOUT_CLR)) / sin(ALPHA)`, ≈ 104 at A's constants and ≈ 107 after F. The bottom arm is the mirror image.
- Check the entry point's X lies inside the body's X range, as it does at every current value.
- B9's centre-body clause (the T1-55 pattern) is then sampled up to `rib_end`.

**DB4 — B8's real margin is ≈ `KEEPOUT_CLR`, by construction.**
- `YJ_V` uses the 2×2 pattern's circumradius, so the worst hole's counterbore clears the keep-out by 1.0003 mm at A's constants, not 13.2. The 13.2 is the joint centre's gap, the same slip as rev 1's 11.0.
- The formula is right. B8 (T1-77) asserts per hole and its message prints the worst gap; §2 states ≈ 1.0.
- `CENTRE_H`'s body is 144.7, but the tabs stick out ≈ 5 mm beyond it in Y. B1 (T1-70) computes the centre bbox **with the tabs**, as arch's geometry function does: ≈ 180 × 155 × 14.5.

**DB5 — The pad is the arm's own rounded end: `PAD_D = ARM_W`.**
- In sandwich mode there is no boss, so `PAD_BOSS_D` goes. `REACH_KEEPOUT` becomes `max(PAD_D, W_LIFT_RAIL)/2 + KEEPOUT_CLR`; B4 (T1-73) uses `PAD_D`.
- **The spacer is a disc of `PAD_D` × `VTV_PLATE_T`** with one M8 clearance hole, so it matches the pad's bearing footprint (R42). It is not 30 mm.
- **B12 (T1-81)** becomes the arch T1-58 form: `VTV_PLATE_T ≥ 2·MCC_WALL` and `(PAD_D − MCC_M8_CLR_D)/2 ≥ 2·MCC_WALL`.
- New **B16 (T1-85):** spacer thickness `== VTV_PLATE_T` and diameter `== PAD_D`.

**DB6 — B15 (T1-84)** becomes `rib_end − RIB_PAD_GAP ≥ 2·RIB_T` (a rib, not a nub). The old "does not exceed `REACH`" compared the wrong quantity.

**DB7 — Delete §3.3's parenthetical** ("Part B keeps arch's existing raised boss…"). It contradicts Changelog 16 and §7.3 step 4: both brackets' sandwich pads are flat at the arm top.

**DB8 — The arch sandwich mode ships as exported parts** (the `base_fan` precedent).
- Marker lines:
  - `// build.py: parts = arm, centre, arm_sandwich, centre_sandwich, spacer`
  - `// build.py: print_count = arm:2, arm_sandwich:2, spacer:2`
- The exported part name fixes the mode: `arm_sandwich`, `centre_sandwich` and `spacer` are sandwich; `arm` and `centre` are direct.
- `MOUNT_MODE` survives only as the preview selector for `assembly` / `assembly_sweep`.
- `mcc_arch_tv_geom()` takes `mount_mode=`, and `mcc_arch_tv_assert()` runs per part in that part's mode.
- New goldens: `arch-tv-bracket.arm_sandwich`, `.centre_sandwich` and `.spacer`.
- **`arch-tv-bracket.{arm,centre}.json` must stay byte-identical.** Check with `git diff` in the Part B commit.
- Every formula that assumed the centre is `ARCH_PLATE_T` thick reads `centre_t` instead: `z_rail`, `centre_z_max`, the body and tab extrusions, the M3 counterbore seat and T1-57.

**DB9 — The arch spacer thickness is `ARCH_PLATE_T`, the sandwich pad's clamp height, never `centre_t`.** Its diameter is the arm's pad end, `ARM_W`. New **T1-90** asserts both.

**DB10 — The arch's ribs clear the lift rail on the sandwich parts.**
- Use DB2's formula with the arch's α (it varies with `TV_TOP_CLEAR`): ≈ 31 mm at 69.7 and ≈ 68 mm at 184.9.
- It applies to `arm_sandwich` only; direct-mode ribs still start at the pad, so the goldens are unchanged.
- New **T1-89** samples the rib edges against the band `|X − HALF_PITCH| ≥ W_LIFT_RAIL/2 + KEEPOUT_CLR` at both pads.
- The existing T1-58 adapts in sandwich mode: `pad_clamp_t = ARCH_PLATE_T`, and the wall around the M8 hole `(ARM_W − MCC_M8_CLR_D)/2 ≥ 2·MCC_WALL`.

**DB11 — Choose the sandwich M3 lap-screw length inside T1-57's window, never by rounding up.**
- Head seat `= z_rail − M3_COUNTERBORE_DEPTH`.
- Valid lengths `L ∈ [seat − (ARCH_PLATE_T − 1.5·MCC_M3_MAJOR_D), seat − (ARCH_PLATE_T − bore_depth + 0.5)]`, which is [16.8, 18.5] at the placeholders, so **M3×18**.
- The file asserts the chosen stock length lies in that window. When M20 moves the window, T1-57 says so.

**DB12 — Assert the arch sandwich lid and test both modes.**
- New **T1-88:** `z_rail + H ≤ WALL_GAP` on the sandwich parts (78.6 ≤ 150 at the placeholders).
- New **T1-87:** Part B step 6's sweep formula.
- New **T1-86:** mode value ∈ {"direct", "sandwich"}.
- `tests/test_arch_tv_bracket.scad` loops the three `TV_TOP_CLEAR` values × both modes, and instantiates the arm and centre of each mode plus the spacer once.

**DB13 — One set of TV-lift parameters, `assumed` (M20).**
- `W_LIFT_RAIL`, `T_LIFT_RAIL`, `K_BOLT_HEAD` and `WALL_GAP` use the same names and the same placeholder values in both bracket files. Bracket-own convention: not in `constants.scad`.
- Each is overridable with `-D`, echoed, and asserted where used (T1-71, T1-78, T1-83, T1-87…T1-89). M20 updates both files together.
- Vertical bracket B14 (T1-83): `2·VTV_PLATE_T + H ≤ WALL_GAP`.

**DB14 — Print gate (README, BOM, print-check).** Neither bracket is printed for use before:
- M15 as F redefines it (the gravity-lock coupon);
- M20 (the lift and TV figures);
- M22 (sandwich tilt and preload).

Remove every mention of the D34 latch or the "rail-latch pull test" from D's texts; use F's wording.

**DB15 — Record.**
- Create `docs/plans/2026-09-28-vesa-column-bracket.md` from plan D rev 3 (DB16), with this banner under its title:
  `> **Implemented as amended by the architect verdicts appended below (rev-2 verdict DB1–DB16, after plan F). Where they conflict, the verdicts win.**`
- Append this verdict under `## Architect verdict (rev 2)`, and the rev-1 verdict with its Amendment 1 under `## Architect verdict (rev 1, rejected)`.
- The Appendix G/H/E texts below are pasted on D's branch.

**DB16 — Rev 3 of the plan once F has merged, then a fit-check.**
- The researcher folds DB1–DB15 into rev 3, re-runs §8's probe against the real post-F `rail.scad` (not a hand transcription), and updates §2 with the real numbers.
- The architect fit-checks rev 3 before the developer starts. That is a quick check, not a full re-gate, unless an assert fails or F's interface differs from F-R1/F-R2.

## Ids for rev 18

- **Vertical bracket:** B1…B16 → **T1-70…T1-85**, in order (B16 is new, DB5).
- **Arch sandwich parts:** **T1-86** mode value, **T1-87** sweep Z clearance, **T1-88** lid ≤ `WALL_GAP`, **T1-89** ribs vs the lift rail, **T1-90** spacer.
- The existing arch T1-47…T1-60 must hold in both modes.

## DO NOT

- Do not start D before F merges, or branch from any unmerged branch. Branch `feature/issue-56-vesa-column-bracket` from `main` after F.
- Do not call `mcc_rail_male_window()`, read `MCC_RAIL_LATCH_*`, or assemble the rail's footprint from rail constants. Use `mcc_rail_male_keepout()`.
- Do not edit `lib/mcc/**`: F owns the rail, and D consumes it.
- Do not change the arch's direct-mode geometry or goldens (`arm`, `centre`), or anything A or F changed in that file.
- Do not ship the sandwich mode as a `-D`-only switch.
- Do not size a spacer from the centre plate or from a boss diameter.
- Do not hand-type `YJ_V`, `RIB_PAD_GAP`, `rib_end`, `REACH`, `CENTRE_H`, `centre_t` or the M3 window: each is a formula in the geometry function, asserted.
- Do not reintroduce `COLUMN_SIDE`, `mirror()` of the rail or the case, or the tv-bracket.
- Do not invent lift or TV dimensions: every one is `assumed, M20` until measured.
- Do not print either bracket for use before M15 (F), M20 and M22.

## Implementation order

1. C (#57) merges. A (`feature/wide-dovetail`) merges.
2. F: plan (with F-R1…F-R3) → architect gate → implement → merge.
3. Researcher: plan D rev 3 (DB16), probe re-run against the real post-F rail. Architect: fit-check.
4. Developer, on `feature/issue-56-vesa-column-bracket` from `main`:
   - **Part A:** `models/brackets/vertical-tv-bracket.scad` (parts `arm`, `centre`, `spacer`), `tests/test_vertical_tv_bracket.scad`, then smoke, render, check, and `golden --update brackets/vertical-tv-bracket` (new goldens only).
   - **Part B, a separate commit:** the arch sandwich parts (DB8–DB12), the extended `tests/test_arch_tv_bracket.scad`, then smoke, render, check, and a targeted golden update for the three new arch goldens only. Confirm the direct goldens did not move.
5. `slicer-check brackets/vertical-tv-bracket brackets/arch-tv-bracket` with zero warnings, then `review`, then `ci --group k/6` for every k.
6. Docs: README, BOM (spacer rows; M8 × 4 per sandwich; M3×18 for the sandwich arch; no washer seats), print-check, `new-case-variant` (second, independent bullet). Then the Appendix texts and DB15.
7. PR "Closes #56", CI green, merge.
8. Print gate: M15 (F), M20, M22.

---

## Appendix G — `.claude/knowledge/architecture.md` (rev 18; paste on D's branch after F merges)

Paste rule: copy only the text inside the fences. Where an anchor is F's rev-17 text, find it by its first words; if F's final text differs, the anchor is the paragraph or row named.

**G1 — Header.** Insert immediately before the paragraph beginning `**Revision 17`, followed by one blank line:
```
**Revision 18, 2026-09-28 (vertical VESA-column bracket + arch sandwich parts — plan D rev 2, issue #56;
`docs/plans/2026-09-28-vesa-column-bracket.md`).** The user's Samsung TVs sit on a **TV lift** that uses all
four VESA holes, so both TV brackets are **sandwiched** between the TV and the lift on longer M8 bolts,
with printed ASA in the clamp path accepted (R42). New `models/brackets/vertical-tv-bracket.scad`: hub
topology (one arm printed twice by ±α rotation, a centre carrying the rail, printed spacers for the
unused column), the case outboard of the +X column (R43). The arch bracket ships **sandwich parts**
(`arm_sandwich`, `centre_sandwich`, `spacer`) beside its unchanged direct parts (D51). Both brackets
consume the rail only through `mcc_rail_male()` and `mcc_rail_male_keepout()` (rev 17). New: **T1-70 …
T1-90**, **R47**, **M22**, **D51**; R42, R43, M20 and Q22 updated. **No case geometry changes.**
```

**G2 — §9 prose.** Insert immediately before the line beginning `Full table with sources: `:
```
**Rev 18 adds T1-70 … T1-90** (plan D, issue #56: T1-70 … T1-85 the vertical bracket, T1-86 … T1-90 the
arch's sandwich parts; listed in `layout-patch-wall.md` §9). **The next free id is T1-91.**
```

**G3 — §11 R42.** Replace the whole R42 paragraph (A's Amendment 1 text) with:
```
**R42 — a sandwiched printed bracket puts ASA in the TV mount's clamp path. NEW 2026-09-28 (rev 16) —
ACCEPTED by the user.** In sandwich mode (the vertical VESA-column bracket; the arch's sandwich parts) the
bracket's pads are clamped between the TV and the TV's own mount — a TV lift in the user's installation —
by that mount's M8 screws, so the preload passes through printed ASA, which creeps under sustained load
(`knowledge/components/fasteners-and-hardware.md:140`, stated for snap arms; the creep is the material's).
**User decision 2026-09-28, in chat: accept ASA** — no steel sleeves. What follows from it:
- printed-ASA spacers under every VESA hole the bracket does not occupy, with the pad's clamp height and
  bearing footprint (T1-85, T1-90), so both sides creep alike and the lift's rails stay coplanar;
- pads and spacers are flat clamp faces with an M8 clearance hole — no counterbore, no washer seat —
  printed solid;
- recommended practice, not a gate: re-check the M8 preload 24–48 h after installation and at every
  rig-in (M22's first check);
- M8 length, the same on all four holes = the mount's thickness at the hole + the pad/spacer height + the
  usable TV thread depth − ≥ 1 mm, rounded **down** (M20). Too long can crack the TV's back panel.
```

**G4 — §11 R43.** Replace the whole R43 block (A's Amendment 1 text) with:
```
**R43 — the case must fit beside the TV's own mount, and it slides on from one side only. NEW 2026-09-28
(rev 16); layout decided by the user; the arch's sandwich sweep resolved in rev 18.** The case's groove
is open at one end only (D34) and the case always hangs patch-wall down (rev 17), so it always slides on
from the bracket frame's +X side (right, seen from behind the TV), sweeping `L + slide_clear` ≈ 392 mm
(Plus family) from its final −X edge. The TV's own mount — a TV lift in the user's installation — uses
the same four VESA holes.
- Vertical bracket: **+X column (seen from behind the TV), case outboard** (user decision 2026-09-28) —
  the only layout whose sweep crosses no column. The space behind the TV (150–200 mm) and beside it is
  not a constraint (user, 2026-09-28; `WALL_GAP` and `TV_SIDE_CLEAR` stay asserted). `REACH` keeps the
  case clear of the lift's rail band (`W_LIFT_RAIL`, M20).
- Arch bracket, sandwich parts: its sweep must cross the right-hand column, so `centre_sandwich` is
  taller — `z_rail ≥ ARCH_PLATE_T + T_LIFT_RAIL + K_BOLT_HEAD + ARCH_SWEEP_CLR` (T1-87) — which moves its
  case ≈ 5.6 mm further off the TV at the assumed lift figures (lid ≈ 79 mm ≤ `WALL_GAP`, T1-88).
- Remaining: the lift figures (M20); until measured, each is an `assumed` parameter behind an assert.
```

**G5 — §11 new risk.** Insert directly after the last risk paragraph in §11 (the highest-numbered R after F), with a blank line before:
```
**R47 — the vertical bracket's arm outgrows the bed if the TV lift's rail is wide. NEW 2026-09-28 (rev 18,
plan D).** `REACH` grows with `W_LIFT_RAIL/2` (the case must clear the lift's rail band), and the arm with
it: the arm's print length `ARM_LEN + LAP_L/2 + ARM_W/2` reaches the 244 mm cap at `W_LIFT_RAIL` ≈ 150 mm,
where T1-70 fails loudly. Beyond that the arm must split into two printed parts — a design change for the
architect, not a parameter edit. M20 measures `W_LIFT_RAIL`.
```

**G6 — §12 Q22.** Replace item 22 (A's Amendment 1 text) with:
```
22. **Plan D (vertical VESA-column bracket) — sandwich decisions. NEW 2026-09-28 (rev 16) — answered.**
    (a) R42: **accept ASA** in the TV mount's clamp path, no steel sleeves (user, in chat, 2026-09-28);
    printed-ASA spacers of the pad's height and footprint under the unoccupied holes.
    (b) R43: **the +X column (seen from behind the TV), case outboard, slid on from the TV's edge side.**
    (c) **The arch bracket gets sandwich parts** — done in rev 18 (D51).
    (d) Tracked as **issue #56**.
```

**G7 — §12 measurement list.**
1. Replace the whole row beginning `| **M20** |` with:
```
| **M20** | **The user's TV and its TV lift, for the sandwiched brackets (plan D, issue #56):** the TV model, its VESA pattern (400 × 300?) and usable M8 thread depth; the lift's rail/plate width `W_LIFT_RAIL` and thickness `T_LIFT_RAIL` at each hole; the bolt-head height `K_BOLT_HEAD`; any lift hardware within 250 mm of either bracket's arms and pads. **Resolved (user, 2026-09-28): 150–200 mm behind the TV (`WALL_GAP` = 150 asserted) and the space beside it is not a constraint (`TV_SIDE_CLEAR` asserted, non-binding).** | R42/R43/R47 — `REACH`, the rib start, the arch sandwich rise and M3 length, the spacer and M8 lengths. Until measured each is an `assumed` parameter behind an assert (T1-70 … T1-90) | User, with the TV and lift in hand — **open** |
```
2. Insert directly after the M20 row (or after F's M21 row, if F placed it there):
```
| **M22** | **Sandwich tilt and clamp check, both brackets:** hang the heaviest Plus SKU for 24 h on the vertical bracket and on the arch's sandwich parts; static rail tilt ≤ 2° (the arch's M18d rule); re-check the M8 preload at 24–48 h (R42) | R42/R47, and the arch sandwich parts' larger COM offset (≈ 53 mm off the TV back vs ≈ 47.5). If the tilt fails, thicken the plates and re-derive every Z plane | User, after the first print |
```
3. Insert after the last numbering-note line:
```
> **Rev 18** adds M22 (plan D).
```

**G8 — §13.** Insert directly after the last deviation row (F's highest D row):
```
| **D51** | 2026-09-28 | #47 / `models/brackets/README.md`: the arch bracket is a **direct** mount — its top VESA holes must not also carry another mount | **User decision 2026-09-28 (Q22(c)):** the TV's own mount (a TV lift) uses all four holes, so the arch must also work sandwiched | Without it the arch could not be used on the user's TVs | **Done in rev 18 (plan D, issue #56):** the arch ships `arm_sandwich`, `centre_sandwich` and `spacer` beside its direct parts — flat pads, ribs clear of the lift's rail band (T1-89), a taller centre so the slide-on sweep clears the lift rail and bolt head at the right-hand column (T1-87, R43), printed-ASA spacers under the bottom row (T1-90, R42). Direct-mode geometry and goldens unchanged |
```

## Appendix H — `.claude/knowledge/layout-patch-wall.md` (rev 18)

**H1.** Insert immediately before the line beginning `Status: **revision 17`, followed by one blank line:
```
Status: **revision 18, 2026-09-28** (aligned with `architecture.md` rev 18 — plan D, issue #56: the
vertical VESA-column bracket and the arch's sandwich parts). **§9** gains **T1-70 … T1-90**; no case
figure moves.
```

**H2 — §9.** Insert directly after the last T1 row (F's highest):
```
| **T1-70 … T1-85** | *vertical VESA-column bracket* (`models/brackets/vertical-tv-bracket.scad`): T1-70 bboxes incl. tabs and spacer ≤ 244; T1-71 case ≤ `TV_SIDE_CLEAR`; T1-72 `REACH` self-consistency; T1-73 case clears both pads in Y; T1-74 slide-on sweep ≥ `SWEEP_CLR`; T1-75 rib proportions; T1-76 rail footprint (`mcc_rail_male_keepout()`) on the centre body; T1-77 every M3 counterbore clears the rail keep-out; T1-78 ribs clear the centre body, the TV lift's rail band and the case (sampled); T1-79 insert bores and edge distances; T1-80 M3 stack; T1-81 sandwich pad thickness and wall; T1-82 UP arrow clear of body edge, keep-out and counterbores; T1-83 lid ≤ `WALL_GAP`; T1-84 rib run ≥ 2·`RIB_T`; T1-85 spacer = pad height and footprint | **new rev 18** (plan D, issue #56; plan ids B1 … B16) |
| **T1-86 … T1-90** | *arch sandwich parts* (`arch-tv-bracket.scad`): T1-86 mode ∈ {direct, sandwich}; T1-87 sweep clears the lift rail + bolt head at the right-hand column; T1-88 lid ≤ `WALL_GAP`; T1-89 ribs clear the lift's rail band; T1-90 spacer = pad clamp height (`ARCH_PLATE_T`) and footprint (`ARM_W`). T1-47 … T1-60 hold in both modes | **new rev 18** (D51). **The next free id is T1-91** |
```

## Appendix E — `CLAUDE.md` (rev 18)

1. Fixed decision "Mount brackets" (added by A's Amendment 1, AM-5; extended by F's verdict, FB9). Replace the whole bullet, **including F's D49 sentences at its end**, with:
```
- **Mount brackets** (user decisions 2026-09-28): the **arch bracket** is the horizontal option (top
  VESA row; direct parts, and sandwich parts for a TV whose own mount uses all four holes), and the
  **vertical VESA-column bracket** (`vertical-tv-bracket.scad`; Samsung 400 × 300, one column; the case
  sits outboard of the right-hand column seen from behind the TV) is sandwich-only. A sandwiched
  bracket is clamped between the TV and the TV's own mount (a TV lift) on longer M8 bolts, and
  **printed ASA in that clamp path is accepted** (architecture.md §11 R42). The VESA 100/200
  `tv-bracket` is **retired** (D47) — do not reintroduce it.
  **A mounted case always hangs patch-wall down** (user decision 2026-09-28, D49) — on every bracket,
  the truss mount (#27) included, and never on a TV turned to portrait: the gravity lock only engages
  when the case's weight rests on the rail's upper flank. Take the case off before the TV is laid
  down, carried or tilted (R44).
```
(Amended with F's verdict. If rev 17's text of those last sentences differs when D is implemented, keep rev 17's wording.)
2. "Current status":
   - Replace `` `arch-tv-bracket` arm ×2 `` and the following line's `+ centre)` with `` `arch-tv-bracket` direct and sandwich parts, `vertical-tv-bracket`) ``.
   - In the sentence listing §13 items, after the last item, insert `, the vertical VESA-column bracket and the arch's sandwich parts (D51)`.

---

## Architect verdict (rev 1, rejected)


Gate: `solution-architect`, 2026-09-28. Plan: `scratchpad/plans/D-vesa-400x300-bracket.md`.

Checked against:
- `main` @ 047902e, plus plan C and plan A, each as amended by its verdict. D is implemented after both.
- `.claude/knowledge/architecture.md` (source of truth), `CLAUDE.md`, `models/brackets/arch-tv-bracket.scad` and `models/brackets/README.md`.

User decisions relayed for this gate (2026-09-28):
- **Hub topology** (confirmed).
- **Samsung VESA 400 (w) × 300 (h)**, mounted on **one vertical column** (300 mm pitch).
- **Sandwiched**: the TV's own wall mount uses the same 4 screws, so this bracket sits between the TV and the wall mount on longer M8 bolts.
- **The arch bracket stays the horizontal option.**

## Verdict: **REJECTED — re-plan required.** The direction is approved (A1–A8).

This is not a "with binding changes" verdict. The plan cannot be patched into shape; it has to be re-derived. Four reasons:

1. **It predates D44 (plan A).** Every number in its §1 moves:
   - `MCC_RAIL_Y` −20 → −23.5, root 14.6 → 65 mm;
   - no pedestal, so no `+ MCC_FLOOR_T` in the Z stack or the mate;
   - `VTV_PLATE_T` 8 → 11;
   - `MCC_THREAD_M3_MAJOR_D` → `MCC_M3_MAJOR_D` (renamed by C);
   - M3×10 → M3×12.

   The plan says so itself (§0.5, §8 last bullet): if the rail redesign lands first, the numbers need a re-run. It lands first.
2. **B8 fails outright at the new width.**
   - The rail keep-out spans Y [−32.5, +36.1]. Both joint centres (±25) lie inside it, so every M3 counterbore sits under the rail.
   - The plan's "11.0 mm clear" is not reproducible. It equals the joint **centre's** gap (25 − 10.91 − 3.05) and ignores the 2 × 2 hole pattern, whose holes sit up to 12 mm closer.
   - So B8 already failed with the old rail: the nearest counterbore overlapped the keep-out by ≈ 1 mm on the latch side.
   - Fixing it moves the joints to |y| ≈ 52.4, which changes `CENTRE_H`, α, `ARM_LEN` and the rib and arrow layout.
3. **The sandwich is not handled.**
   - The pad is designed as a direct mount: an M8 head in a counterbore, `pad_clamp_t`.
   - There are no spacers for the other column.
   - The ribs start at the pad centre, right under the wall mount's rail.
   - Printed ASA sits in the TV mount's clamp path.
   - §10 Q4 still assumes a direct mount.
4. **With the wall mount on both columns, the plan's default layout cannot be slid on, and `COLUMN_SIDE` cannot exist as an X-mirror.**
   - The case's groove is open at one end only (D34) and the patch wall must hang down. So the case always approaches from the bracket frame's **+X** (right, seen from behind the TV).
   - From its final −X edge it sweeps `L_max + slide_clear` = 211.5 + 180.75 ≈ **392 mm**.
   - Plan default (−X column, case inboard): the sweep reaches 20 + 392 ≈ 412 mm from its own column, past the other column at 400 mm.
   - The mirrored layouts would cross the bracket's own column instead.
   - Mirroring the rail would need a mirrored case, which does not exist.

## Approved direction (carry into rev 2)

- **A1 — Hub topology.** Both joints at the rail's centre X, mirrored in Y. One arm part printed twice, placed by `rotate(∓α)`. The §3.1 proof is correct: the two screws are related by reflection about X, so ±α (not arch's θ / 180−θ) reproduces the mirror pair without `mirror()`.
- **A2 — File organisation, option (c).** A fresh, self-contained `models/brackets/vertical-tv-bracket.scad` in the arch style:
  - one pure geometry function, one public assert module, part dispatch, non-exported previews, `// build.py: parts = arm, centre`, `print_count = arm:2`;
  - private helpers (`_…_circle_rect_gap`, transforms) re-implemented, never imported from arch.
  - Option (b), parametrising arch, is rejected. Option (a), `lib/mcc/bow_bracket.scad`, is **deferred, not refused**: revisit it when a third two-point bracket is requested.
- **A3 — `REACH` from clearance** (`L_max/2 + REACH_KEEPOUT`), with `TV_SIDE_CLEAR` only as a per-TV feasibility assert (B2). Approved, but B2 bounds the case's outboard edge against the TV's side edge, which is the right obstacle **only for an outboard reach** (RD4). §3.2 labels its default "inboard" — an internal inconsistency to resolve in rev 2.
- **A4 — Device list and hook.**
  - The bracket's own `_VERT_TV_DEVS` list plus all 8 device includes.
  - A second `new-case-variant` checklist bullet (plan step 8), kept separate from the arch bullet.
- **A5 — The UP arrow is a cue, not a key** (§3.3), with a B13 assert.
- **A6 — The arch stays the horizontal option.** Its geometry reads only the top row's pitch, so §0.2 holds for a 400-wide top row. The sandwich caveat is RD8.
- **A7 — Test by `use`.** `tests/test_vertical_tv_bracket.scad` uses `use` (the arch precedent, architecture.md §9), never assigns `part`, and documents the negative case without running it. The echo line must never contain the reserved `WARNING: unmeasured`.
- **A8 — Public rail symbols only** (§0.5): `mcc_rail_male(len=, plate_t=)`, `mcc_rail_male_window(len=, plate_t=)` and `MCC_RAIL_*`, rail unioned **after** the plate's cuts. A keeps both signatures. No cross-section or latch geometry is re-derived in the bracket.

## Required for rev 2 (RD1–RD10)

**RD1 — Rebase every number on A (D44) and C.**
- `VTV_PLATE_T = 11`. The sweep condition is flush now: `2T − (T + RIB_H) ≥ SWEEP_CLR` gives T ≥ 11.
  - B5 loses its `+ MCC_FLOOR_T` term.
  - The preview mate is `translate([REACH, MCC_RAIL_Y, 2*VTV_PLATE_T]) rotate([0,0,180])`, with no `+ MCC_FLOOR_T`.
- Rail keep-out: arch's formula, unchanged. `RAIL_KEEPOUT_Y = [-MCC_RAIL_ROOT_W/2, MCC_RAIL_ROOT_W/2 + MCC_RAIL_LATCH_ARM_T + MCC_RAIL_LATCH_ENGAGE]` = [−32.5, +36.1]; the latch side is +Y under the `rotate([0,0,180])` rail placement.
- Centre Z extent: `VTV_PLATE_T + MCC_RAIL_MALE_H` (= 14.5), not `MCC_RAIL_SILL_H`. Do not add `MCC_RAIL_END_STOP_*` (0 since D34) to new formulas.
- M3 lap stack: identical to A's arch numbers — counterbore depth `M3_HEAD_K + 1.3`, `M3_JOINT_SCREW_L = 12`. B11 is checked against `1.5 * MCC_M3_MAJOR_D`.
- Case band relative to the rail (W_max = 166.35): Y ∈ [−106.7, +59.7] (was [−103.2, +63.2]). Gaps to the screw centres: 90.3 / 43.3; B4 passes.
- Z stack: TV back 0; arms 0–11; centre 11–22; arm features to 20; case floor 22 (flush); lid 73.
- Unchanged by D44: `REACH` = 125.75 and `slide_clear` = 180.75.
- Rewrite every figure in the plan's §1 table as a formula echoed by the file.

**RD2 — Joints clear of the 65 mm rail band (B8 as planned fails).**
- The top joint binds (latch side). Its counterbores must clear +36.1 by `KEEPOUT_CLR`.
- The rotation-independent bound uses the 2 × 2 pattern's circumradius:
  ```
  YJ_V >= RAIL_KEEPOUT_Y[1] + KEEPOUT_CLR + m3_counterbore_r + norm([JOINT_S/2, JOINT_P/2])
       =  36.1 + 1.0 + 3.05 + 12.21  ≈ 52.4
  ```
  Derive `YJ_V` in `mcc_vert_tv_geom()` from this formula (plus any margin), never as an assumed literal. B8 then asserts the exact per-hole gap.
- Consequences to re-derive and assert:
  - α ≈ 37.8° (was 44.83°); `ARM_LEN` ≈ 159 (was 177); arm bbox ≈ 194.
  - `CENTRE_H ≥ 2·(YJ_V + ARM_W/2)` ≈ 145 (was 90); centre bbox ≈ 180 × 145 × 14.5.
  - B7 (keep-out inside ±`CENTRE_H`/2).
  - B9: the ribs get shorter against the larger centre body.
  - **B13 must also keep the UP arrow clear of the joint counterbores.** The joints now sit in the band the arrow would use — a new check.

**RD3 — Design for the sandwich (user decision).**
- **Pad = a clamped spacer, not a direct-mount boss.** No M8 counterbore or washer seat. The TV mount's rail (or plate) bears on the pad's flat outer face, and the M8 passes through the mount, the pad and into the TV.
- **Pad height is a design variable.** Recommend the flat pad at the arm plate's own top (Z = T):
  - the mount's rail then sits at T … T + t_rail, below the case floor (2T) whenever t_rail ≤ T − `SWEEP_CLR`;
  - that is what can reopen the inboard layout (RD4).
- **Ribs** must stop outside the mount's rail band along the column (half-width from M20, plus clearance), or be omitted there. Today they start at the pad centre.
- **Clamp path (R42, Q22(a)).** Rev 2 implements the user's answer to Q22(a); it is the user's safety call, not the researcher's. The recommended option:
  - steel compression sleeves through both pads (length = pad height; the pad locates, the sleeve carries the preload);
  - steel spacers of the same length under the other column's two screws.
  - Equal-height spacers on the other column are needed whichever option the user picks.
  - Sleeve and spacer dimensions: cite a source in `knowledge/components/**` or mark them `assumed`. Never invent them.
- **BOM.**
  - M8 × 4 (**all four** holes get longer bolts). Length = mount thickness at the hole (M20) + pad/spacer height + usable TV thread depth − ≥ 1 mm, rounded **down** (the arch row's "MEASURE, do not guess" rule; a bolt that bottoms out can crack the TV panel).
  - Sleeves × 2, spacers × 2.
  - M3×12 × 8 and M3 inserts × 8.

**RD4 — Placement: the fixed slide direction and the wall mount (M20, Q22(b)).**
- **Delete the `COLUMN_SIDE` X-mirror** (§3.2). The file models physically valid layouts only; the rail is never mirrored.
- **With the mount's rails on both columns and a case floor that cannot pass over them, exactly one layout works:**
  - the **+X column (seen from behind the TV)**, with the case **outboard**, slid on from beyond it;
  - B2 (`TV_SIDE_CLEAR` = column-to-TV-edge) is then the right feasibility gate;
  - the sweep may run past the TV's edge in free air, if nothing stands beside the TV.
- **The −X-column inboard layout** (the plan's default) is feasible **only if** the case floor clears the other column's mount rail in Z. Using RD3's flat pad, assert `2T ≥ T + t_mount_rail + SWEEP_CLR`.
- **New asserts:**
  - the sweep band [final −X edge, + `L_max + slide_clear`] never crosses a column's mount-rail band, unless the Z-clearance assert above holds;
  - `REACH_KEEPOUT ≥ w_mount_rail/2 + clearance`;
  - the case lid (Z = 2T + H ≈ 73) fits the TV-to-wall gap. Use a `WALL_GAP` parameter, `assumed` until M20; the pad height adds to the gap.
- **The user picks the layout** (Q22(b)); rev 2 models that layout.

**RD5 — Preview variant.** No `["tripod_insert", true]`: T1-63 rejects it while the rail is on. Copy the arch preview variant as A left it (`tripod_insert` false).

**RD6 — Ids.**
- B1–B14 and RD2/RD4's new asserts get their final ids at the re-gate, starting at **T1-64**.
- The §6 tilt measurement gets the next free M id at the re-gate. Do not reuse arch's M18d.

**RD7 — Tracking (Q22(d)).** Open a GitHub issue per `.claude/knowledge/ticket-source.md` (the plan's title suggestion is fine) and name the branch per its rule. The user may explicitly keep it ad hoc instead; record that choice.

**RD8 — The arch doc line (plan step 9).**
- It must also state that the arch is a **direct** mount: its two top holes cannot also carry a TV wall mount (`models/brackets/README.md`, the "must not also carry another mount" line). On a wall-mounted Samsung the arch is therefore unusable until Q22(c) is answered.
- Write it on top of A's arch changes: A rewrites that file's header.
- Comments and prose only — no geometry or golden change, confirmed with `git diff`.

**RD9 — Drop stale content.**
- §0.1: the local `main` is current now.
- §0.5's "in parallel" framing: A lands first, by rule.
- Issue #48 (D34 fixed it): closing it is user bookkeeping, not part of D.
- The `VESA_V_PITCT` typo in §10 Q2.

**RD10 — Structural (§6).**
- Recompute at T = 11 with the new α and `ARM_LEN`. The COM now sits 2T + H/2 = 47.5 mm off the TV back (was 44.5), so M ≈ 45 N × 47.5 ≈ 2.1 N·m.
- Keep the physical tilt gate mandatory: no print for use before M15, that measurement and R42 are closed.
- The arms now carry the case through a clamped sandwich, not a direct mount. Say which contact faces carry the moment.

## Architecture record for this gate

No §13 row: nothing has drifted, because the bracket does not exist yet. The open items ride in **A's rev 16** (A's verdict, Appendix G). Paste them verbatim with A's branch; do not re-word them:
- the last sentence of the **G1** header paragraph (plan D rejected for re-plan);
- **G5**: **R42** (ASA in the clamp path) and **R43** (fit, slide direction, wall mount);
- **G6**: **Q22** (a) sleeves/spacers, (b) layout, (c) arch direct-mount conflict, (d) GitHub issue;
- **G7**: **M20** (the TV and wall-mount measurements).

If A does not merge first (e.g. the user reverses D44), paste those same four blocks as a standalone architecture.md revision on whichever branch lands first. Take R43's rail numbers from the rail as it then stands.

No `layout-patch-wall.md` or `CLAUDE.md` edit for D now:
- T1 rows are added at the re-gate;
- `CLAUDE.md` "Current status" gains the vertical bracket only when it ships.

## DO NOT

- Do not implement anything before the rev-2 re-gate (Team Charter step 2).
- Do not edit `lib/mcc/**`, least of all `rail.scad`. Rail changes belong to A, or to the future lock (A's Q21).
- Do not `use`/`include` arch's file or call its private functions.
- Do not mirror the rail or the case, and do not model a `COLUMN_SIDE` X-flip.
- Do not put an M8 counterbore or washer seat on a sandwiched pad.
- Do not print the bracket for use with ASA in the clamp path unless the user has answered Q22(a) in writing.
- Do not invent sleeve, spacer, wall-mount or TV dimensions: cite them or mark them `assumed`.
- Do not change the geometry or goldens of `arch-tv-bracket` or `tv-bracket` in D. `tests/golden/brackets/arch-tv-bracket.*` and `tv-bracket.json` must be byte-identical.
- Do not hand-type derived numbers (`YJ_V`, `CENTRE_H`, `REACH`, α): they are formulas in `mcc_vert_tv_geom()`.
- Do not branch before A is on `main`.

## Amended implementation order

1. C merges, then A merges. A's rev 16 records R42, R43, M20 and Q22.
2. The user answers Q22 (a)–(d) and supplies M20: the TV model and VESA thread depth, and the wall mount's rail width and thickness, standoff and wall-plate footprint.
3. `researcher` writes plan D rev 2 against A-merged `main`, applying RD1–RD10. It keeps A1–A8 and names the chosen layout (RD4).
4. `solution-architect` re-gates rev 2. It assigns T1-64+ and the tilt M id, and updates R42/R43 in a new revision.
5. Implement on the issue branch, off `main` after A.
6. New goldens only: `brackets/vertical-tv-bracket.{arm,centre}`, via a targeted `golden --update brackets/vertical-tv-bracket`. Run `slicer-check brackets/vertical-tv-bracket` with zero warnings, then the CI gate.
7. Print gate: M15, the tilt measurement, and R42/Q22(a) closed.

---

## Amendment 1 (2026-09-28, user decisions)

The coordinator relayed the user's answers to Q22 and D47. **Where this amendment differs from RD1–RD10, the DO-NOTs or the order above, the amendment wins.** The recorded texts (R42, R43, Q22, M20) are in A's verdict, Amendment 1, AM-4.

- **(a) ASA is accepted in the clamp path** ("user decision 2026-09-28, in chat: accept ASA").
  - RD3's steel sleeves are dropped.
  - Rev 2 keeps: flat clamp pads with an M8 clearance hole and no counterbore; ribs outside the mount's rail band; the M8 length rule.
  - Rev 2 adds **printed-ASA spacers** with the same height and bearing area as the pads, under every VESA hole the bracket does not occupy, so both sides creep alike (R42). The spacers are a printable part of the bracket file.
  - R42 is closed as a decision. The DO-NOT about ASA in the clamp path, and the print-gate item "R42/Q22(a)", are satisfied. Print gate: M15 and the tilt measurement.
- **(b) Layout: the +X column** (seen from behind the TV), **case outboard**, slid on from the TV's edge side.
  - RD4 reduces to modelling this one layout, with no `COLUMN_SIDE`.
  - B2 (`TV_SIDE_CLEAR`, column to TV edge) is its feasibility gate.
  - Keep the `WALL_GAP` assert and the `REACH_KEEPOUT`-vs-mount-rail assert.
  - The sweep's start position reaches ≈ 412 mm outboard of the column.
- **(c) The arch bracket gets a sandwich mode**, now in rev 2's scope. This supersedes RD8's "direct mount only" line; the arch keeps its direct mode.
  - Its +X sweep crosses the right-hand column. It is feasible only if the case floor clears that column's mount rail and bolt head in Z: flat pads at the arm top, `2T ≥ T + t_rail + k_head + ARCH_SWEEP_CLR`.
  - Its ≈ 73 mm stack sits between the columns, where a wall plate usually is (R43, M20).
  - It needs printed-ASA spacers under the bottom row's two holes.
  - The DO-NOT "do not change arch-tv-bracket geometry or goldens" becomes: the arch's **direct-mode** exports and goldens must stay byte-identical. How the sandwich mode is exposed (a render-time mode or separate parts, with its own goldens) is rev 2's proposal, decided at the re-gate.
- **(d) GitHub issue:** pending; the user has been asked.
- **D47:** the tv-bracket is retired inside plan A. The DO-NOT about `tv-bracket.json` staying byte-identical no longer applies; the file is gone.
- **M20** is still open. It now also covers the arch sandwich mode's Z clearance (mount-rail thickness and bolt-head height).
- **Order:** unchanged, except that step 2 now waits only for (d) and M20. Rev 2 covers the vertical bracket **and** the arch sandwich mode, both in one re-gate.

---

## Architect fit-check (DB16, after the fact)


Checked by `solution-architect`, 2026-09-28, read-only.

**What was read.** The developer's worktree `.claude/worktrees/agent-a475b61a219ead99c` at branch head `9b60cdc`, which equals the local `refs/remotes/origin/feature/vertical-tv-bracket`. I have no shell tool, so I could not run `git fetch` myself. If origin has moved past `9b60cdc`, re-check only the delta.

**Against what:**
- `D-vesa-400x300-bracket.VERDICT-rev2.md` (DB1–DB16, Appendices G/H/E);
- `F-gravity-lock.VERDICT.md` (F-R1/F-R2);
- A's verdict.

## Result: **FAIL — 7 small required fixes** (FX1–FX7)

None of them changes geometry or a golden. Once they are applied the fit-check passes, with no re-gate.

The substance is right:
- the post-F re-derivation;
- the rail interface;
- the sandwich pads and spacers;
- the exported sandwich parts;
- the rib start and rib end derivations;
- the verbatim rev-18 texts.

The failures are asserts that are missing or weaker than DB2/DB9 require, which the rev-18 records describe as if they existed, plus record and doc upkeep.

## What passes

**The re-derivation was done right.** I checked it independently against the real F interface.
- **Rail inputs:** `mcc_rail_male_keepout()` = rail-local y ∈ [−33.2, 32.5], rotated to `RAIL_KEEPOUT_Y` [−32.5, 33.2].
- **Joint position:** `YJ_V` = 33.2 + 1.0 + 3.05 + 12.207 = **49.457**.
- **Arm:** `REACH` 136.75; α 36.33°; `ARM_LEN` 169.73; arm bbox 204.7 × 40 × 20.
- **Centre:** `CENTRE_H` 138.9 for the body, 148.9 with the tabs; centre bbox 180 × 148.9 × 14.5, which equals the golden (±74.455).
- **Ribs:** `RIB_PAD_GAP` (DB2) 53.19 and `rib_end` (DB3) 107.06, so each rib runs 53.9 mm.
- **B8:** the worst hole clears the keep-out by exactly `KEEPOUT_CLR`, by construction.
- **Arch sandwich parts:** `centre_t` 16.6, `z_rail` 27.6 and lid 78.6 ≤ 150. `arm_sandwich` is 167.2 × 40 × 20; `centre_sandwich` is 238.1 × 92 × 20.1, which equals the golden (±119.066).
- **Arch rib start:** `rib_pad_gap` 31.0 / 54.3 / 68.0 at `TV_TOP_CLEAR` 69.7 / 150 / 184.9.
- **Arch lap screw:** M3 window [16.8, 18.5], so M3×18.

My rev-2 estimate of 52.4 was computed from the latch-era keep-out (36.1). The difference is expected and the formulas absorb it.

**Binding changes that pass as implemented:**
- **DB1:** only `mcc_rail_male()` (no arguments) and `mcc_rail_male_keepout()`; no window, no `MCC_RAIL_LATCH_*`.
- **DB2** and **DB3:** see the numbers above. The T1-78 lift-band clause samples both arms.
- **DB4:** B8 is checked per hole; the centre bbox includes the tabs.
- **DB5:** `PAD_D = ARM_W`; `REACH_KEEPOUT`, B4, B12 and B16 use it; the spacer is 40 × 11.
- **DB6:** T1-84 checks the rib run ≥ 2·`RIB_T`.
- **DB8:** five exported parts; the part name fixes the mode; `MOUNT_MODE` is preview-only; every centre formula reads `centre_t`. Direct mode is provably unchanged: `centre_t` = `ARCH_PLATE_T` and `hole_h` = `arm_top_z`. The six new goldens are additions only.
- **DB9 geometry:** the arch spacer is `ARCH_PLATE_T` × `ARM_W`.
- **DB10:** T1-89 is correct. Centre-local X equals assembly X for the arch, and both columns are checked.
- **DB11** and **DB12:** T1-86/87/88 are present; tests cover 3 × 2 modes plus the spacer.
- **DB13:** the TV-lift parameters have the same names and values in both files and are echoed.
- **DB14:** the print gates are in the README, BOM and print-check.

**Docs:**
- `CLAUDE.md` E1 and E2 are in, including F's D49 sentences.
- The BOM sections are complete: M8 × 4 in sandwich mode, M3×18, the spacers, no washers.
- The README, the `print-check` rows and the `new-case-variant` second bullet are all present.

**Verbatim rev-18 texts all landed:**
- `architecture.md`: header G1; §9 G2; R42 (G3), R43 (G4), R47 (G5); Q22 (G6); M20, M22 and the numbering note (G7); D51 (G8).
- `layout-patch-wall.md`: H1 and H2.

## Required fixes

**FX1 — T1-82 lacks its DB2 clause** ("the UP arrow clear of the joint counterbores").
- The rev-18 record (`layout-patch-wall.md` T1-82) says the check exists. It is clear today by about 12 mm, but it is not asserted.
- In `vertical-tv-bracket.scad`, add `ARROW_X = -30.0; // mm. assumed` next to `ARROW_L`/`ARROW_W`. Use it in `mcc_vert_tv_centre()` instead of the literal `-30`.
- Append to T1-82 in `mcc_vert_tv_assert()`:
```openscad
    // ... and the arrow stays clear of every joint counterbore (DB2: the joints sit in its band).
    arrow_r = norm([ARROW_W / 2, ARROW_L / 2]); // conservative: the arrow's circumradius
    for (side = [-1, 1], h = _mcc_vert_tv_joint_holes(g)) {
        p = _mcc_vert_tv_xform(h, side, g);
        assert(norm(p - [ARROW_X, arrow_y]) - arrow_r - m3_counterbore_r >= KEEPOUT_CLR - MCC_EPS,
            str("mcc: vertical-tv-bracket T1-82 UP arrow within ",
                norm(p - [ARROW_X, arrow_y]) - arrow_r - m3_counterbore_r, " of the M3 counterbore at ", p));
    }
```

**FX2 — T1-90 does not assert what DB9 and the record say** (spacer = the sandwich pad's clamp height and footprint).
- Today it asserts only minimum thickness and wall, and the spacer module hard-codes its dimensions. A later edit to the spacer would go unnoticed.
- In `arch-tv-bracket.scad`:
  - `mcc_arch_tv_geom()` gains `["spacer_t", ARCH_PLATE_T]` and `["spacer_d", ARM_W]`.
  - `mcc_arch_tv_spacer(g)` uses `struct_val(g, "spacer_t")` and `struct_val(g, "spacer_d")`.
  - The `part == "spacer"` dispatch calls `mcc_arch_tv_spacer(G_SANDWICH)`.
  - `tests/test_arch_tv_bracket.scad` calls `mcc_arch_tv_spacer(mcc_arch_tv_geom(mount_mode = "sandwich"))`.
- Keep the existing wall assert. Add to T1-90:
```openscad
    if (mode == "sandwich") {
        assert(abs(struct_val(g, "spacer_t") - pad_clamp_t) < MCC_EPS,
            str("mcc: arch-tv-bracket T1-90 spacer thickness ", struct_val(g, "spacer_t"),
                " != the sandwich pad's clamp height ", pad_clamp_t));
        assert(abs(struct_val(g, "spacer_d") - ARM_W) < MCC_EPS,
            str("mcc: arch-tv-bracket T1-90 spacer diameter ", struct_val(g, "spacer_d"), " != ARM_W=", ARM_W));
    }
```

**FX3 — T1-85 is a tautology.**
- `mcc_vert_tv_spacer()` ignores the `spacer_t`/`spacer_d` fields that T1-85 checks.
- Make it `mcc_vert_tv_spacer(g)` using those two fields. The `part == "spacer"` dispatch passes `G`; the test passes `g`.
- T1-85 then compares the drawn values with the pad: `spacer_t == VTV_PLATE_T`, the arm pad's clamp height, and `spacer_d == ARM_W`, the pad end's diameter.

**FX4 — T1-70's record says "bboxes incl. tabs and spacer ≤ 244"**, but the spacer's bbox is not asserted. Add one line to T1-70:
```openscad
    for (d = [struct_val(g, "spacer_d"), struct_val(g, "spacer_d"), struct_val(g, "spacer_t")])
        assert(d <= max_axis + MCC_EPS, str("mcc: vertical-tv-bracket T1-70 spacer bbox axis ", d, " exceeds ", max_axis));
```

**FX5 — The plan record (DB7, DB15, DB16)**, in `docs/plans/2026-09-28-vesa-column-bracket.md`:
- (a) Strike §3.3's parenthetical `(Part B, §7, keeps arch's *existing* raised boss instead — … demanding one convention across both files.)`. Mark it `~~…~~ *(struck by DB7)*`.
- (b) Insert directly under the banner line:
```
> **As built (post-F, re-derived in the file, confirmed by the DB16 fit-check):** rail keep-out
> y ∈ [−32.5, 33.2]; `YJ_V` 49.46; `REACH` 136.75; α 36.33°; `ARM_LEN` 169.73; `RIB_PAD_GAP` 53.19;
> `rib_end` 107.06; `CENTRE_H` 138.91 (148.91 with tabs); arm 204.7 × 40 × 20; centre 180 × 148.9 × 14.5;
> spacer 40 × 40 × 11. Arch sandwich: `centre_t` 16.6, `z_rail` 27.6, M3×18; `arm_sandwich`
> 167.2 × 40 × 20, `centre_sandwich` 238.1 × 92 × 20.1. §2's table below predates plan F and is superseded.
```
- (c) Append this fit-check under `## Architect fit-check (DB16, after the fact)`.

**FX6 — `CHANGELOG.md` has no entry for #56.** Every notable change gets one (CONTRIBUTING). Insert under `## [Unreleased]`, directly before the first `### ` heading below it:
```
### Added (2026-09-28, issue #56)

- **Vertical VESA-column bracket** (`models/brackets/vertical-tv-bracket.scad`, architecture.md rev 18):
  sandwiched between a Samsung TV (VESA 400 × 300) and its own TV lift on one column, case outboard of
  the +X column; one arm printed twice, a centre carrying the rail, two printed ASA spacers for the
  other column.
- **Arch bracket sandwich parts** (`arm_sandwich`, `centre_sandwich`, `spacer`, D51) beside the
  unchanged direct parts: flat clamp pads, ribs clear of the lift's rail, a taller centre so the
  slide-on clears the lift's rail and bolt head (M3×18 lap screws).
```

**FX7 — A stale coupon name left over from #59 (A + F), found here.** In `.claude/skills/print-check/SKILL.md` §3, replace `which the `rail-latch` coupon (M15) judges` with `which the `rail-lock` coupon (M15) judges`. F's rename missed this line, and so did my F verdict.

**After FX1–FX7:**
- `smoke`, then `render brackets/vertical-tv-bracket brackets/arch-tv-bracket`, then `check`.
- `golden`: no golden may change. FX2 and FX3 refactor the spacer modules to identical geometry.
- Push, and CI must be green. No architect re-gate is needed.

## Optional (non-blocking)

- **T1-78's comment** "side cancels" is wrong: the sign of the `y_line` term flips with `side`. The check is still complete, because both edges of both ribs are sampled on both sides. Reword the comment.
- **The arch `.scad` header's PRINT GATE** (lines 60–63) could add "sandwich parts also: M20, M22", matching the README, BOM and print-check.
- **README arch section:** give the sandwich figures beside the direct ones — 27.6 to 78.6 mm off the TV back, M3×18, four M8 bolts.
- **`tests/test_vertical_tv_bracket.scad`:** also sweep `w_lift_rail` (e.g. 40 / 60 / 120). `REACH`, the rib start and end, and R47's bed limit all move with it.
