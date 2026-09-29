> **Ids renumbered at the architect gate (issue #68):** the plan's D52 → D63.1 / D64.1 / D65.1 / D66.1
> (per issue), T1-64 → T1-63.1, T1-65 → T1-63.2, T1-66 → T1-63.3, T1-91 → T1-64.1, R48 → R63.1, Q5 →
> M63.1 (see the verdict at the end). `D52` in the repository is #61's end-stop record.

# Plan H — top rail lock, a closed groove end, no tie-down slots (rev 1)

Status: **implementation plan for the architect gate, then a Sonnet developer.** Every decision is made
below. Where the developer meets something this plan does not describe, the answer is **stop and
report**, never improvise.

Baseline: `main` @ `24c52c8` (plans C, A, F, D merged: PRs #57, #59, #60). BOSL2 pinned at `804028c`.
A parallel cleanup may land first — branch `feature/retire-end-stop-remnants` (removes
`MCC_RAIL_END_STOP_*` and the stale `RAIL_X` comment). This plan never edits those lines; §3 says which
anchors to re-verify if it has landed.

Scratch evidence (all paths under
`C:\Users\Niels\AppData\Local\Temp\claude\C--repos-github-magewell-converter-cases\21ce76a1-d282-4f53-b50d-05d7eb636fdb\scratchpad\`):
`toplock\` (prototype trees `proto_a`, `proto_bsame`, `proto_bstag`, `proto_bstag2`, `proto_final`;
scripts and logs in `toplock\work\`), images `toplock\H1_sections.png` and `toplock\H2_lock_3d.png`.

## User decisions implemented (2026-09-29, binding)

1. The lock sits **on top of the dovetail** (DP48 style), not on the flank. The D48 flank bump and pocket
   are removed.
2. Release = move the case about 1 mm off the plate, then slide it off. The exit face is **square**. A
   pull on the case or its cables must not release it. The entry side keeps a ramp.
3. The PoE-splitter zip-tie slots are removed from every base. The splitter bay stays reserved.
4. The groove's closed −X end is **closed over its full depth** (today it is open between z = 3 and 4).
5. ≥ 0.5 mm clearance on every non-bearing face stays. A mounted case always hangs patch-wall down (D49).

Plus the user's three follow-up questions (2026-09-29): (a) top only, (b) top + flank, (c) a
squeeze-to-release latch — answered in §0 and §18, with the choice left to the user (§19).

---

## 0. Recommendation

**Implement (a): the top lock only** — the user's decision 1 — built so that it passes every gate. Offer
**(b-stag), the flank lock kept as a staggered safety catch**, as an optional follow-up (§18.1). Reject
(b-same) and (c) for now (§18.2, §18.3).

Three findings changed the literal brief:

1. **The DP48 pockets cannot be printed in our case.** DP48's tray prints with its pockets facing up. Our
   base prints floor-down, so the groove roof is a ~66 mm bridge. Two 20 mm pockets are **holes in that
   bridge**, and Bambu Studio flags "floating cantilever" on the base and on the coupon (measured; the
   D33 lesson). Without the pockets the same parts pass. **Fix:** one transverse slot across the full
   roof width. It splits the bridge instead of holing it. Measured: zero Bambu warnings on the compact
   and Plus bases, the coupon and every arch and vertical-bracket part. The two strips on the male stay
   as DP48 has them.
2. **The −X end cannot be closed at the current rail length without entering the splitter bay.** On the
   tightest SKUs (L = 193.9) the reserved bay ends at x = −73.95, and the sill already reaches −75 (D45).
   Any end cap behind a groove ending at −75 lies inside the bay. **Fix:** `MCC_RAIL_LEN` 150 → **136**.
   The sill keeps a full 3 mm end wall past the groove (x = −71 … −68) and clears the bay by 2.95 mm on
   every SKU. That also closes D45 (T1-17 finally asserted).
3. **The repo's Python cantilever check (`build.py check`) mis-reads the split roof.** It measures reach
   at raw mesh-section vertices. Mid-edge triangulation vertices on the straight slot edges read as a
   6–7 mm cantilever tip, while Bambu (the ground truth) passes the part. **Fix:** simplify each overhang
   outline by 0.05 mm before measuring (§13). This can only remove vertices, so no part that passes
   today can start failing. It needs the architect's ruling.

### Ranking (numbers in §2 and §18)

| Rank | Option | Accidental release needs | Release gesture | Print / tolerance | Verdict |
|---|---|---|---|---|---|
| 1 | **(a) top only** | the case moved ≥ 0.6 mm **away from the TV** at the strips, then slid. In-plane loads (cable plugging from below, sideways or downward pulls, vertical vibration) cannot do it | pull the case ~1 mm toward you (to the stop), slide | all gates pass; 0.40 mm margin (≈ 0.10 mm per flank face) | **recommended now** |
| 2 | (b-stag) top + flank catch 50 mm behind | a pull away **and** a slide of ~50 mm, **then** a lift ≥ 0.7 mm and a second slide | two stages: pull ~1 mm + slide, it stops; lift ~1 mm + slide | Bambu passes on both bases (bump near the leading end); 0.39/0.40 margins; coupon needs its own catch position | best robustness; user's choice (§19 Q1) |
| 3 | (b-same) top + flank at the same place | up **and** out at once | one combined gesture with a 0.30 mm window | full depth impossible (0.60 + 0.61 > 1.00 mm play); at 0.35/0.40 the ride margin is 0.25–0.30 mm with sub-line-width features | rejected |
| 4 | (c) squeeze-to-release latch | pressing both end walls | two hands, 194–212 mm apart | springs + separate parts, openings from the groove into the case, flexures fight the floor-down print pose | rejected (§18.3) |

What (a) does not catch: someone grabbing the case, pulling it ~0.6 mm off the TV and pushing it
sideways (≈ 0.6–1.1 W, W = the case's weight), or prying its fan (+X) end off the TV (≈ 0.3–0.5 W) while
pushing it sideways. That is the deliberate release gesture. (b-stag) adds a second, independent lock
for exactly that case.

---

## 1. The design in numbers (option (a))

Rail-local frame, as `rail.scad` documents it: X = slide axis (the case groove is open at +X and closed
at −X), Y across, Z = 0 at the plate / the case's exterior floor, +Z into the case. Every bracket places
the rail with `rotate([0,0,180])` and the case hangs patch-wall down (D49), so rail-local **−Y is up**
and **+Z points away from the TV**.

| Item | Value | Source |
|---|---|---|
| Working length `MCC_RAIL_LEN` | **136.0** (was 150.0); groove x ∈ [−68, +68] + passage to the +X wall | assumed; sized by T1-17 (below) |
| Sill | x ∈ [−71, +71] (`MCC_RAIL_LEN + 2·MCC_RAIL_END_WALL`), height 7.0, width 71.0; passage sill from x = 71 to the +X wall's inner face, height 5.5 | `MCC_RAIL_END_WALL = MCC_WALL` = 3.0 |
| −X end | solid end wall x ∈ [−71, −68], z 0 → 7 over the whole groove section | T1-91 (new) |
| Splitter bay clearance | sill −X end −71.0 vs bay end −73.95 (L = 193.9) → **2.95 ≥ `MCC_FAN_BAY_CLR` 2.0**; Plus 11.25 | T1-17 (implemented) |
| Lock strips (male top) | two, each 2.0 (X) × 20.0 (Y) at \|y\| ∈ [10, 30]; square exit face at x = len/2 − 3.0 (= 65.0); entry side 45° chamfer over the engaged height; top at z = 4.0 + e | DP48 strip 2.000 × 20.000, 3.0 from the trailing end [F2, measured] |
| Engagement `e` = `MCC_RAIL_LOCK_ENGAGE` | **0.60** above the roof line (strip height above the male top 1.10) | assumed; 60 % of the Z-play (DP48 uses 82 %) |
| Roof slot (case) | ONE transverse slot, x ∈ [62.5, 65.5], full roof width y ∈ ±33.08, z 4.0 → 5.1 (strip ± 0.5 in X, 0.5 above the strip top) | T1-62 clearances |
| Slot backing | x ∈ [59.5, 68.5], y ∈ ±35.5, z 7.0 → 8.1 on the sill | keeps T1-38 (≥ 3.0 above the slot) |
| Roof lead-in | at the +X outer face: flanks, mouth **and roof** flare 1.0 over the last 1.0 mm (45°) | DP48 1.0 × 45° [F2, measured] |
| Clearances | flanks 0.5 normal, roof 0.5, strip-to-slot 0.5 on every side | D44 |
| Play (measured) | 1.154 horizontal; Z-play **0.999** (analytic c/k = 1.000) | `rail_fit` |
| Ride margin | 1.0 − 0.6 = **0.40** normal (T1-64 demands ≥ `MCC_RAIL_LOCK_PLAY_MARGIN` 0.30) | measured 0.396 on 3 SKUs |
| Keep-out `mcc_rail_male_keepout()` | `[[−68, 68], [−32.5, 32.5]]` (was `[[−75, 75], [−33.2, 32.5]]`) | the strips lie inside the top |
| Tie-down slots | removed; `mcc_splitter_tiedown()` retired | decision 3 |

Release, in words for users: **pull the case about 1 mm toward you — away from the TV — until it stops,
then slide it back off the way it went on.** The dovetail itself stops the pull at 1.0 mm; the strips
clear at 0.6. Mounting: slide it on until it clicks (the click comes 0.5 mm before the end stop).

Reachability (the user's two constraints for every option): the release needs only a grip on the
faces a hand reaches behind a TV on a lift — the two end walls, the far wall (top) or the lid face
(toward the wall) — to pull the case toward you and push it sideways. Nothing is pressed or reached on
the floor side, the patch wall is not touched, and the lid stays closed. The same holds for (b-stag)'s
second stage (lift by the top or the end walls, then slide).

---

## 2. Physics, proven numerically

Scripts: `toplock\work\physics.py` (statics), `toplock\work\rail_fit_proto.py` (mesh sweeps on the
rendered prototype bases). W = the case's weight; the heaviest case is ≈ 0.8 kg `assumed` (weigh one,
M15). Centre of mass x ≈ 3, 25 mm off the plate, `assumed`.

**Hanging load path (French cleat).** The case's upper groove wall rests on the male's upper (−Y) flank
(60° to the plate). Normal force on that flank N = W/cos 30° = **1.155 W**. Its wedge presses the case
floor onto the plate with R = W·tan 30° = **0.577 W**. That clamp is what holds the strips in the slot.

**Play.** Horizontal 2c = 2 × 0.577 = 1.155; rigid Z-play before both flanks bind c/k = 0.577/0.577 =
**1.000** (= `MCC_RAIL_MATE_CLR`/cos 60°). Measured on the prototype: 1.154 and 0.999.

**Engagement.** Riding the strips, a hanging case moves off the plate by e and up the upper flank by
0.577·e; the lower flank's normal gap closes by exactly e. With e = 0.60 the ride keeps **0.40 mm
normal** at the lower flank — the same tolerance D48 had (≈ 0.10 mm per flank face). Roof sag eats the
same budget (R40), which is why e is not larger. New T1-64: e + 0.30 ≤ Z-play.

**Locked (square face).** Floor on the plate, a hanging case pulled toward removal collides only at the
strips' exit faces (x 64.9 … 65.0), **at every Y in the play band** — so lifting the case (−Y) alone
never releases it. The pull-off needed right past the 0.5 mm axial play (dx = 0.55) and 1.5 mm later
(dx = 2.0) is the same **0.603** mm: no cam.

**Insertion ride.** Every insertion position on HDMI TX (L 193.9), HDMI Plus (210.5) and SDI Plus
(211.5): the case needs 0.603 off the plate over the last 33 mm (compact) / 42 mm (Plus) of travel;
margin 0.396 normal throughout; nothing else touches. Nothing flexes.

**−X end closed.** 18 rays from inside the groove toward −X (z 0.5 … 3.9, y −25/0/+25) all stop at
x = −68.00 on the prototype; on `main` the rays at z 3.1 … 3.9 run on to the −X wall (−93.95 compact,
−102.25 Plus). 410–435 rays up (+Z) and 328–348 rays sideways (±Y) from the groove all stop at its
roof, slot, lead-in or flanks — no ray from the groove reaches the case interior. The same rays cover
the +X passage (x 71 … L/2 − 3, a 1.5 mm roof under the fan bay) and the roof chamfer inside the +X
wall (1.5 mm below the Plus fan aperture): no gap of the −X end's kind exists there.

**Release and accidental loads** (quasi-static, rigid, small rotations; μ = friction coefficient,
`assumed` 0.3 for ASA on ASA):

| Load on a hanging case | (a) top lock | D48 flank lock (on `main`) |
|---|---|---|
| Axial pull at the rail line | holds (square face) | holds (square face) |
| Pushing up at the patch wall (plugging a cable from below) | **holds** — the lower flank's wedge also presses the case onto the plate | **releases** once the push exceeds ≈ 1 W (the case lifts 0.7 mm off the upper flank) |
| Outward cable tug at the patch wall (away from the TV) | the case rotates about the plate's upper edge until the dovetail stops it (0.016–0.020 rad); the upper strip keeps **+0.14 … +0.28 mm** of its 0.60 → holds, reduced | holds (the bump separates 0.06–0.08 of 0.61) |
| Sideways (−X) pull high on the case (tips the +X end off) | frictionless 2.2 W at 25 mm height, 1.05 W at the lid edge; **self-locking for μ ≥ 0.33** (friction on the square face) | holds |
| −X pull on the case's top (far-wall) edge (in-plane yaw) | holds (no motion off the plate) | releases at ≈ 3 W (F2) |
| Pull the case off the TV (+Z) | releases at 0.58 W (μ 0) … 1.06 W (μ 0.3), then needs a slide | holds |
| Pry the +X (fan) end off the TV | releases at 0.29 W (μ 0) … 0.48 W (μ 0.3), then needs a slide | holds |
| Vertical vibration (TV lift) | holds at any level | hops at > 1 g upward |

So (a) is **better than D48** against the common handling events (plugging cables from below, bumps,
vibration) and **weaker** against pulling or prying the case off the TV — the deliberate release.
(b-stag) closes that last gap (§18.1).

---

## 3. Preconditions and anchors

1. `git fetch origin` and branch **`feature/top-rail-lock`** from `origin/main`. `main` must contain
   `24c52c8` (PR #60) and `.claude/knowledge/architecture.md` must contain `| **D51** |`.
2. Check whether `feature/retire-end-stop-remnants` has merged:
   `git log origin/main --oneline -3 -- lib/mcc/constants.scad`.
   - Merged: `MCC_RAIL_END_STOP_L`/`_H` are gone. This plan never adds, reads or removes them. Only the
     bracket comment edits H9.2 and H9.4 must be re-read first; follow their wording rule, not a line
     number.
   - Not merged: carry on; this plan does not touch the end-stop lines either way.
3. Every anchor quoted below must be found **exactly once, verbatim** (`grep -nF`), except where a step
   says "whole file". If an anchor is missing or appears twice, **stop and report**.
4. `grep -rln --include=*.scad --include=*.py "mcc_splitter_tiedown" lib models tests scripts` must list
   exactly `lib/mcc/mounts.scad` and `lib/mcc/poe_splitter.scad`. Anything else: stop and report.
5. `grep -rln --include=*.scad --include=*.py -e "MCC_RAIL_LOCK_" -e "_mcc_rail_lock_" -e "_mcc_rail_flank_extrude" lib models tests scripts`
   must list exactly `lib/mcc/constants.scad`, `lib/mcc/rail.scad`, `models/coupons/rail-lock.scad`,
   `tests/test_rail.scad` and `scripts/rail_fit.py`. Anything else (for example a bracket): stop and
   report.

Files touched: `lib/mcc/constants.scad`, `lib/mcc/rail.scad` (whole file), `lib/mcc/mounts.scad`,
`lib/mcc/poe_splitter.scad`, `lib/mcc/layout.scad` (comment), `lib/mcc/shell.scad` (comment),
`models/coupons/rail-lock.scad` (whole file), `models/brackets/arch-tv-bracket.scad` (comments),
`models/brackets/vertical-tv-bracket.scad` (comment), `tests/test_rail.scad` (whole file),
`scripts/rail_fit.py` (whole file), `scripts/printability.py`, goldens (§14), docs (§15).

---

## 4. `lib/mcc/constants.scad`

**H4.1** Replace the line
```
// Section: Mount rail (dovetail + gravity lock) — issue #25, replaces VESA (D-15, rev 9; lock D48)
```
with
```
// Section: Mount rail (dovetail + top lock) — issue #25, replaces VESA (D-15, rev 9; lock D52)
```

**H4.2** Directly after the line
```
                            // each side lets the roof bridge flank-to-flank over its whole length.
```
insert:
```openscad
MCC_RAIL_END_WALL = MCC_WALL; // solid sill beyond each end of the groove's working length, mm (D52). At
                            // the closed -X end it is the end stop's wall over the groove's full
                            // depth -- the groove (4.0 deep) is deeper than the floor (3.0), so without
                            // it the groove opened into the case between z = 3 and 4 (T1-91).
```

**H4.3** Replace the four lines
```
MCC_RAIL_LEN = 150.0;      // rail/groove length along its slide axis (case-local X), mm. assumed —
                            // fixed across every SKU (one interface, every case; layout-patch-wall.md
                            // §17.2 R4/§1.4). Fits the smallest family (compact, L=194.9) with
                            // >= 19 mm margin per end past the end walls' inner faces.
```
with
```openscad
MCC_RAIL_LEN = 136.0;      // rail/groove working length along its slide axis (case-local X), mm.
                            // assumed -- fixed across every SKU (one interface, every case;
                            // layout-patch-wall.md §17.2 R4/§1.4). D52: 150 -> 136 so the sill
                            // (MCC_RAIL_LEN + 2 * MCC_RAIL_END_WALL = 142) clears the reserved splitter
                            // bay by >= MCC_FAN_BAY_CLR on the tightest SKU (L = 193.9: bay ends at
                            // x = -73.95, sill at -71.0 -- T1-17).
```

**H4.4** Replace every line from the one starting
```
// Rail lock -- a GRAVITY lock (user decision 2026-09-28, architecture.md §13 D48; it replaces the D34
```
down to, **not including**, the line starting `MCC_RAIL_PASSAGE_ROOF_MIN = 1.2;` with exactly:
```openscad
// Rail lock -- a TOP lock (user decision 2026-09-29, architecture.md §13 D52; it replaces the D48 flank
// bump). Two rigid strips on the male rail's flat top, near its +X (trailing) end, drop into ONE
// transverse slot across the full width of the case groove's roof at full insertion. Every bracket
// places the rail with rotate([0,0,180]) and a mounted case always hangs patch-wall down (D49): its
// weight rests on the rail's upper flank, whose 60 deg wedge presses the case floor onto the plate
// (about 0.58 x the weight) and holds the strips in the slot. Nothing flexes: sliding on, the case rides
// over the strips inside the dovetail's own Z-play (mcc_rail_z_play() = 1.0, T1-64); the exit faces are
// square, so a pull along the rail cannot cam a hanging case out. Release: pull the case about 1 mm
// away from the plate (the dovetail stops it at 1.0; the strips clear at MCC_RAIL_LOCK_ENGAGE) and
// slide it back off. The slot spans the whole roof because separate pockets are holes in the roof
// bridge, which the slicer flags (bambu-slicer.md §1, D33). Reference: the external specialist's DP48
// plate -- two 2.0 x 20.0 strips, 3.0 mm from the trailing end (analysis F2).
MCC_RAIL_LOCK_ENGAGE = 0.60;      // strip height above the groove roof line, mm (the strips stand
                                   // MCC_RAIL_ROOF_CLR + this above the male's top). assumed: 60 % of
                                   // the Z-play (the DP48 uses 82 %), leaving 0.4 mm for FDM tolerance
                                   // and roof sag. Tuned on the rail-lock coupon's e-ladder (M15).
MCC_RAIL_LOCK_PLAY_MARGIN = 0.30; // Z-play that must remain while the case rides the strips, mm
                                   // (T1-64). assumed.
MCC_RAIL_LOCK_RAMP_IN = 45;       // entry chamfer of each strip (its -X side, over the engaged height)
                                   // to the slide axis, deg. DP48's 45 deg chamfer (F2). The +X (exit)
                                   // face is square by construction.
MCC_RAIL_LOCK_STRIP_X = 2.0;      // strip base length along the slide axis, mm. DP48 2.000 (F2).
MCC_RAIL_LOCK_STRIP_Y_IN = 10.0;  // |y| of each strip's inner end, mm. assumed.
MCC_RAIL_LOCK_STRIP_Y_OUT = 30.0; // |y| of each strip's outer end, mm -- 20.0 long each like the DP48's
                                   // (F2), the outer end 2.2 mm inside the male's 64.4 mm top so the
                                   // upper strip sits as close to the loaded flank as the top allows.
MCC_RAIL_LOCK_END_OFFSET = 3.0;   // male's +X (trailing) end to the strips' exit face, mm. The DP48
                                   // strips sit 3.0-5.0 mm from their trailing end (F2). rail.scad
                                   // derives the position from its own `len`, so the 60 mm coupon works.
MCC_RAIL_LEADIN = 1.0;            // 45-deg lead-in where the groove leaves the case's +X wall: flanks,
                                   // mouth AND roof flare by this much over the last this-many mm, so a
                                   // strip meets a ramp, not an edge (D52). The DP48's 1.0 x 45 deg roof
                                   // entry chamfer (F2). assumed.
```
Every value is a plain numeric literal on purpose: `scripts/rail_fit.py` reads them with a literal-only
regex. `MCC_RAIL_LOCK_RAMP_OUT` and `MCC_RAIL_LOCK_FLAT` are gone with this replacement.

**H4.5** Replace
```
                            // offset of the female groove and lock pocket from the male profile that
```
with
```
                            // offset of the female groove from the male profile that
```

**H4.6** Replace
```
MCC_RAIL_ROOF_CLR = MCC_RAIL_MATE_CLR; // = 0.5. Gap between the male's flat top (and the lock bump's) and
```
with
```
MCC_RAIL_ROOF_CLR = MCC_RAIL_MATE_CLR; // = 0.5. Gap between the male's flat top (and the lock strips' tops) and
```
In the line directly below it, replace `the groove roof, mm.` with `the groove roof (the roof slot's ceiling), mm.`

Nothing else in this file changes. `MCC_RAIL_PASSAGE_ROOF_MIN`, `MCC_RAIL_END_STOP_*`, the D44 clearance
constants and `MCC_SPLITTERS` stay exactly as they are.

---

## 5. `lib/mcc/rail.scad` — replace the whole file

Removed: `_mcc_rail_flank_extrude()`, `_mcc_rail_lock_geom()`, `_mcc_rail_lock_2d()` (the D48 flank bump and pocket; nothing else used them). New: `mcc_rail_z_play()`, `_mcc_rail_lock_x()`, `_mcc_rail_xz_prism()`, `_mcc_rail_lock_strips()`, `mcc_rail_lock_slot()`, `mcc_rail_female_backing()`; `_mcc_rail_taper_eps()` gains `h`; `mcc_rail_male_keepout()` is symmetric; `mcc_rail_sill_size()` includes the end walls. Public signatures of `mcc_rail_male(len, lock_e)` and `mcc_rail_female_cut(len, open_ext, entry_x, lock_e)` are unchanged, so no caller outside this plan changes. Replace the file's entire content with:

```openscad
//////////////////////////////////////////////////////////////////////
// LibFile: mcc/rail.scad
//   L1. Tool-less dovetail mount-rail interface (issue #25, replaces VESA — D-15, rev 9). Owns the
//   ONE cross-section shared by both mating halves so they can never drift apart (D6 precedent,
//   architecture.md §5 rev 5): mcc_rail_male() (bracket-side, additive), mcc_rail_female_cut()
//   (case-floor-side, subtractive) and mcc_rail_female_backing() (case-floor-side, additive: the
//   material over the lock's roof slot, T1-38), plus the pure accessors mcc_rail_sill_size(),
//   mcc_rail_lock_slot(), mcc_rail_z_play() and mcc_rail_male_keepout() (the plate-side keep-out every
//   bracket reads -- D50). NOT named bracket.scad (architecture.md §3 rev 9, R4/layout-patch-wall.md
//   §17.2): the name describes the INTERFACE, not one of its two consumers -- a file named for a
//   consumer invites bracket-plate/hole/rib geometry (per-bracket assembly work) into an L1 provider.
//   `layout.scad` must NOT `use` this file (architecture.md §3) — the "mount_rail" floor keep-out
//   row is built from the MCC_RAIL_* L0 constants only, never from mcc_rail_sill_size().
//   `use`d by lib/mcc/mounts.scad (the female groove, case floor) and, via the barrel, by
//   models/brackets/*.scad and models/coupons/rail-lock.scad.
// Includes:
//   include <mcc/mcc.scad>
//////////////////////////////////////////////////////////////////////

include <BOSL2/std.scad>
include <constants.scad>
use <util.scad>

// -----------------------------------------------------------------------------------------
// Local frame (shared by every module here): long axis (slide axis) = local X, spanning [-len/2,
// +len/2] for the working (dovetail) length; local Y = across the dovetail's width, centred on 0;
// local Z = depth/height, Z=0 at the mating surface (the bracket plate's top face for the male; the
// case's exterior floor face for the female), +Z runs INTO the case. Single insertion direction
// (PLAN-ASSUMPTION-2, RATIFIED, layout-patch-wall.md §17.5; ends fixed by D34): the case groove is OPEN
// at +X -- it runs out through the case's +X wall (mcc_rail_female_cut()'s `open_ext`) -- and CLOSED at
// -X, the end stop the male's -X face runs into; the case sill carries MCC_RAIL_END_WALL of solid
// material beyond it (D52). The male slides in -X relative to the case.
//
// Cross-section: a dovetail, narrow (MCC_RAIL_MOUTH_W) at the mating surface -- local Z=0 on BOTH
// halves (D44: male-local = female-local, Z included) -- widening to MCC_RAIL_ROOT_W at Z=MCC_RAIL_DEPTH,
// the groove roof. WIDE material sits DEEPER inside the groove, so the case cannot be lifted straight
// off the bracket; only sliding along X clears the interlock. At full mate the case's flat exterior
// floor rests FLUSH on the bracket plate outside the two footprints. The male stands MCC_RAIL_MALE_H
// tall (MCC_RAIL_ROOF_CLR short of the roof) and the groove is offset MCC_RAIL_CLR_HORIZ per side, so
// every other face has >= MCC_RAIL_MATE_CLR (T1-62).
//
// Lock (D52, user decision 2026-09-29 -- replaces the D48 flank bump): two rigid strips on the male's
// flat top, near its +X (trailing) end, drop into one transverse slot across the groove roof's full
// width at full insertion. A mounted case hangs patch-wall down (D49) on the rail's upper (-Y) flank,
// whose wedge presses the case floor onto the plate and holds the strips in the slot. The strips' exit
// faces (+X) are square; their entry sides (-X) carry a MCC_RAIL_LOCK_RAMP_IN chamfer, and the groove's
// +X entry carries a MCC_RAIL_LEADIN roof chamfer, so sliding on the case rides over them inside the
// joint's own Z-play (T1-64). Release: move the case about 1 mm away from the plate, then slide it off.
// -----------------------------------------------------------------------------------------

// Function: mcc_rail_sill_size()
// Usage:
//   sz = mcc_rail_sill_size();
// Description:
//   Pure. [length, width, height] of the case-floor sill the groove is cut into -- the working length
//   plus MCC_RAIL_END_WALL at each end (D52) -- for BOM/preview use. NOT `use`d by layout.scad
//   (architecture.md §3 rev 9: that file builds its "mount_rail" keep-out row from the MCC_RAIL_*
//   constants directly, never from this function).
function mcc_rail_sill_size() =
    [MCC_RAIL_LEN + 2 * MCC_RAIL_END_WALL, MCC_RAIL_ROOT_W + 2 * MCC_RAIL_SILL_SIDE_W, MCC_RAIL_SILL_H];

// Module: _mcc_rail_taper()
// Description:
//   Private. The dovetail taper alone: a prismoid from MCC_RAIL_MOUTH_W at local Z=0, widening along
//   the flank's own slope for `h` mm, length `len` along X, centred on Y=0, anchored BOTTOM. The female
//   groove uses the full MCC_RAIL_DEPTH (top width == MCC_RAIL_ROOT_W exactly); the male stops at
//   MCC_RAIL_MALE_H with the SAME slope (D44), so the two profiles can never drift.
// Arguments:
//   len = rail/groove length along the slide axis, mm.
//   clr = per-side horizontal clearance added to both widths, mm. Default 0 (the male). The female
//         groove passes MCC_RAIL_CLR_HORIZ (D44).
//   h   = height, mm. Default MCC_RAIL_DEPTH.
module _mcc_rail_taper(len, clr = 0, h = MCC_RAIL_DEPTH) {
    w_top = MCC_RAIL_MOUTH_W + 2 * h * _mcc_rail_flank_k();
    prismoid(
        size1 = [len, MCC_RAIL_MOUTH_W + 2 * clr],
        size2 = [len, w_top + 2 * clr],
        h = h, anchor = BOTTOM
    );
}

// Function: _mcc_rail_flank_k()
// Description: Private. Outward run of a flank per mm of height over the taper (0.577 at 60 deg).
function _mcc_rail_flank_k() = (MCC_RAIL_ROOT_W - MCC_RAIL_MOUTH_W) / (2 * MCC_RAIL_DEPTH);

// Function: mcc_rail_z_play()
// Usage:
//   zp = mcc_rail_z_play();   // = 1.0 at MCC_RAIL_MATE_CLR 0.5 and 60 deg flanks
// Description:
//   Pure. How far the case can move away from the plate, rigidly, before both flanks bind:
//   MCC_RAIL_CLR_HORIZ / flank slope (= MCC_RAIL_MATE_CLR / cos(MCC_RAIL_FLANK_ANGLE)). The lock strips'
//   ride must fit inside it with MCC_RAIL_LOCK_PLAY_MARGIN to spare (T1-64).
function mcc_rail_z_play() = MCC_RAIL_CLR_HORIZ / _mcc_rail_flank_k();

// -----------------------------------------------------------------------------------------
// Lock geometry (D52). Everything derives from the caller's own `len`, so the 60 mm coupon works.
// -----------------------------------------------------------------------------------------

// Function: _mcc_rail_lock_x()
// Description:
//   Private, pure. [x0, x1] of each lock strip's base along the slide axis for a rail of working
//   length `len`: x1 = the square exit face, MCC_RAIL_LOCK_END_OFFSET inside the male's +X end;
//   x0 = x1 - MCC_RAIL_LOCK_STRIP_X. The male slides in -X relative to the case, so x0 (the chamfered
//   entry side) meets the groove's roof chamfer first; withdrawing, the slot's +X wall meets x1.
function _mcc_rail_lock_x(len) =
    let(x1 = len / 2 - MCC_RAIL_LOCK_END_OFFSET) [x1 - MCC_RAIL_LOCK_STRIP_X, x1];

// Module: _mcc_rail_xz_prism()
// Description:
//   Private. Extrudes an outline drawn in the XZ plane (a list of [x, z] points) along +Y, from y0 to y1.
module _mcc_rail_xz_prism(pts, y0, y1) {
    translate([0, y1, 0]) rotate([90, 0, 0]) linear_extrude(height = y1 - y0) polygon(pts);
}

// Module: _mcc_rail_lock_strips()
// Description:
//   Private. The two lock strips on the male's top, mirrored in Y. Each spans [x0, x1] along X and
//   [MCC_RAIL_LOCK_STRIP_Y_IN, MCC_RAIL_LOCK_STRIP_Y_OUT] in |y|: square exit face at x1; the entry side
//   rises vertically to the roof line (Z = MCC_RAIL_DEPTH), then chamfers at MCC_RAIL_LOCK_RAMP_IN over
//   the engaged height `e`; flat top at Z = MCC_RAIL_DEPTH + e. Each starts 0.2 mm inside the male's top
//   so the union shares real volume.
module _mcc_rail_lock_strips(len, e) {
    x = _mcc_rail_lock_x(len);
    ramp = e / tan(MCC_RAIL_LOCK_RAMP_IN);
    z0 = MCC_RAIL_MALE_H - 0.2;
    zr = MCC_RAIL_DEPTH;
    zt = MCC_RAIL_DEPTH + e;
    pts = [[x[0], z0], [x[0], zr], [x[0] + ramp, zt], [x[1], zt], [x[1], z0]];
    _mcc_rail_xz_prism(pts, MCC_RAIL_LOCK_STRIP_Y_IN, MCC_RAIL_LOCK_STRIP_Y_OUT);
    _mcc_rail_xz_prism(pts, -MCC_RAIL_LOCK_STRIP_Y_OUT, -MCC_RAIL_LOCK_STRIP_Y_IN);
}

// Function: mcc_rail_lock_slot()
// Usage:
//   b = mcc_rail_lock_slot([len], [lock_e]);   // [[x_lo, x_hi], [y_lo, y_hi], [z_lo, z_hi]]
// Description:
//   Pure. The case-side roof slot the strips drop into, rail-local: the strips' X span grown by
//   MCC_RAIL_MATE_CLR each side, the groove roof's full width (flank to flank at Z = MCC_RAIL_DEPTH),
//   from the roof up to MCC_RAIL_ROOF_CLR above the strips' tops. One full-width slot, never separate
//   pockets: a hole inside the roof bridge is a floating cantilever to the slicer (D33, D52).
// Arguments:
//   len    = working length, mm. Default: MCC_RAIL_LEN.
//   lock_e = strip engagement above the roof line, mm. Default: MCC_RAIL_LOCK_ENGAGE.
function mcc_rail_lock_slot(len = MCC_RAIL_LEN, lock_e = MCC_RAIL_LOCK_ENGAGE) =
    let(
        x = _mcc_rail_lock_x(len),
        hw = MCC_RAIL_ROOT_W / 2 + MCC_RAIL_CLR_HORIZ
    )
    [[x[0] - MCC_RAIL_MATE_CLR, x[1] + MCC_RAIL_MATE_CLR],
     [-hw, hw],
     [MCC_RAIL_DEPTH, MCC_RAIL_DEPTH + lock_e + MCC_RAIL_ROOF_CLR]];

// Module: mcc_rail_female_backing()
// Usage:
//   union() { sill(); mcc_rail_female_backing([len=], [lock_e=]); }
// Description:
//   ADDITIVE (case side). The material over the roof slot that keeps T1-38 true there: the slot's X
//   span grown by MCC_WALL each side, the sill's full width, from the sill top (Z = MCC_RAIL_SILL_H) up
//   by the slot's own height above the roof. The caller unions it with its sill (mounts.scad) or its
//   coupon plinth, in the same rail-local placement as its mcc_rail_female_cut().
// Arguments:
//   len    = working length, mm. Default: MCC_RAIL_LEN. Must match the female cut's `len`.
//   lock_e = strip engagement, mm. Default: MCC_RAIL_LOCK_ENGAGE. Must match the female cut's.
module mcc_rail_female_backing(len = MCC_RAIL_LEN, lock_e = MCC_RAIL_LOCK_ENGAGE) {
    b = mcc_rail_lock_slot(len, lock_e);
    h = b[2][1] - b[2][0];
    sw = MCC_RAIL_ROOT_W / 2 + MCC_RAIL_SILL_SIDE_W;
    // T1-38 (D52): at least MCC_FLOOR_T of material over the slot's ceiling too.
    assert(MCC_RAIL_SILL_H + h - b[2][1] >= MCC_FLOOR_T - MCC_EPS,
        str("mcc: rail_female_backing T1-38 residual over the lock slot = ", MCC_RAIL_SILL_H + h - b[2][1],
            " below MCC_FLOOR_T=", MCC_FLOOR_T));
    translate([b[0][0] - MCC_WALL, -sw, MCC_RAIL_SILL_H - MCC_EPS])
        cube([b[0][1] - b[0][0] + 2 * MCC_WALL, 2 * sw, h + MCC_EPS]);
}

// Function: mcc_rail_male_keepout()
// Usage:
//   ko = mcc_rail_male_keepout([len]);   // [[x_min, x_max], [y_min, y_max]]
// Description:
//   Pure. The conservative plan-view extent, in the shared rail-local frame, of everything
//   mcc_rail_male() puts on or into a consumer's plate: the taper, bounded by MCC_RAIL_ROOT_W (wider
//   than the male's own MCC_RAIL_MALE_H top). The lock strips sit on that top, inside it (D52). The rail
//   needs no cut in the plate (D50): a consumer unions mcc_rail_male() onto its plate and keeps its other
//   plate features out of this rectangle, adding its own clearance. A rotate([0,0,180]) placement
//   negates and swaps both ranges. Brackets read this, never the MCC_RAIL_LOCK_* constants
//   (architecture.md §3, D50).
// Arguments:
//   len = working length, mm. Default: MCC_RAIL_LEN.
function mcc_rail_male_keepout(len = MCC_RAIL_LEN) =
    [[-len / 2, len / 2], [-MCC_RAIL_ROOT_W / 2, MCC_RAIL_ROOT_W / 2]];

// Module: mcc_rail_male()
// Usage:
//   union() { plate(); mcc_rail_male([len=]); }
// Description:
//   ADDITIVE. The male dovetail rail (bracket side): the shared taper, MCC_RAIL_MALE_H tall, standing
//   directly on the consumer's plate (no pedestal since D44), over the working length [-len/2, +len/2],
//   with the two lock strips on its top near its +X end (D52). No separate end stop (D34): the case
//   groove's closed -X end stops the rail's -X end face. The rail needs no cut in the consumer's plate
//   (D50): the consumer unions it on and keeps its other plate features out of mcc_rail_male_keepout().
// Arguments:
//   len    = working length, mm. Default: MCC_RAIL_LEN. Must match the female cut's `len`.
//   lock_e = strip engagement above the roof line, mm. Default: MCC_RAIL_LOCK_ENGAGE. Only the rail-lock
//            coupon's e-ladder passes another value, and always the same one to mcc_rail_female_cut()
//            and mcc_rail_female_backing().
module mcc_rail_male(len = MCC_RAIL_LEN, lock_e = MCC_RAIL_LOCK_ENGAGE) {
    x = _mcc_rail_lock_x(len);
    top_hw = MCC_RAIL_MOUTH_W / 2 + MCC_RAIL_MALE_H * _mcc_rail_flank_k();
    // T1-64 (D52): the case rides over the strips inside the joint's own Z-play, with
    // MCC_RAIL_LOCK_PLAY_MARGIN to spare -- nothing is designed to flex.
    assert(0 < lock_e && lock_e + MCC_RAIL_LOCK_PLAY_MARGIN <= mcc_rail_z_play() + MCC_EPS,
        str("mcc: T1-64 rail lock strip ", lock_e, " + margin ", MCC_RAIL_LOCK_PLAY_MARGIN,
            " does not fit the Z-play ", mcc_rail_z_play()));
    // T1-65 (D52): the entry chamfer is 30..60 deg and shorter than the strip; the strips sit inside the
    // male's top with >= 1 mm to its edges, and inside the working length.
    assert(30 <= MCC_RAIL_LOCK_RAMP_IN && MCC_RAIL_LOCK_RAMP_IN <= 60
        && lock_e / tan(MCC_RAIL_LOCK_RAMP_IN) < MCC_RAIL_LOCK_STRIP_X,
        str("mcc: T1-65 rail lock entry chamfer ", MCC_RAIL_LOCK_RAMP_IN,
            " deg outside 30..60 or longer than the strip"));
    assert(0 <= MCC_RAIL_LOCK_STRIP_Y_IN && MCC_RAIL_LOCK_STRIP_Y_IN < MCC_RAIL_LOCK_STRIP_Y_OUT
        && MCC_RAIL_LOCK_STRIP_Y_OUT <= top_hw - 1,
        str("mcc: T1-65 rail lock strips |y| ", [MCC_RAIL_LOCK_STRIP_Y_IN, MCC_RAIL_LOCK_STRIP_Y_OUT],
            " not inside the male's top (half-width ", top_hw, ")"));
    assert(-len / 2 + 5 < x[0] && x[1] < len / 2 - 1,
        str("mcc: T1-65 rail lock strips x=", x, " do not fit inside len=", len));

    union() {
        // D44: no pedestal -- the taper stands directly on the consumer's plate (local Z=0),
        // MCC_RAIL_ROOF_CLR short of the groove roof.
        _mcc_rail_taper(len, h = MCC_RAIL_MALE_H);
        // D52: the lock strips on the male's top.
        _mcc_rail_lock_strips(len, lock_e);
    }
}

// Module: mcc_rail_female_cut()
// Usage:
//   mcc_rail_female_cut([len=], [open_ext=], [entry_x=], [lock_e=]);
// Description:
//   SUBTRACTIVE. The matching dovetail groove (case-floor side): the shared taper widened by
//   MCC_RAIL_CLR_HORIZ per side (at least MCC_RAIL_MATE_CLR normal to the flanks, D44), from its
//   CLOSED -X end (the end stop, D34) at -len/2 through +len/2 and on by `open_ext` -- the passage the
//   male enters through, which the case runs out through its +X wall. Plus the lock's roof slot
//   (mcc_rail_lock_slot(), D52) and, when `entry_x` is given, a 45-degree lead-in where the groove leaves
//   the part: flanks, mouth and roof flare by MCC_RAIL_LEADIN over the last MCC_RAIL_LEADIN mm before the
//   face at X = entry_x (D52). Local frame: mouth at Z=0 = the case's exterior floor face, +Z into the
//   case; a MCC_EPS overlap below Z=0 pierces that face cleanly. The caller must leave at least
//   MCC_RAIL_END_WALL of solid material beyond X = -len/2 over the groove's full depth (T1-91) and
//   union mcc_rail_female_backing() over the slot (T1-38).
// Arguments:
//   len      = working length, mm. Default: MCC_RAIL_LEN. Must match the mating mcc_rail_male().
//   open_ext = how far the groove continues past +len/2 (the insertion passage), mm. Default 0.
//   entry_x  = X of the outer face the groove leaves through (a case: its +X wall, L/2), mm. Default
//              undef = no lead-in. Must lie in [len/2, len/2 + open_ext].
//   lock_e   = strip engagement, mm. Default MCC_RAIL_LOCK_ENGAGE -- always the male's value.
module mcc_rail_female_cut(len = MCC_RAIL_LEN, open_ext = 0, entry_x = undef, lock_e = MCC_RAIL_LOCK_ENGAGE) {
    assert(MCC_FLOOR_T - MCC_EPS <= MCC_RAIL_SILL_H - MCC_RAIL_DEPTH,
        str("mcc: rail_female_cut T1-38 residual floor over the groove = ",
            MCC_RAIL_SILL_H - MCC_RAIL_DEPTH, " below the MCC_FLOOR_T (", MCC_FLOOR_T, ") minimum"));
    // T1-62 (D44): at least MCC_RAIL_MATE_CLR on every non-bearing face -- normal to the flanks, and
    // at the roof over the male's shortened top (the slot keeps the same clearance around the strips).
    assert(MCC_RAIL_MATE_CLR - MCC_EPS <= MCC_RAIL_CLR_HORIZ * sin(MCC_RAIL_FLANK_ANGLE),
        str("mcc: T1-62 rail flank clearance ", MCC_RAIL_CLR_HORIZ * sin(MCC_RAIL_FLANK_ANGLE),
            " mm normal, below MCC_RAIL_MATE_CLR=", MCC_RAIL_MATE_CLR));
    assert(MCC_RAIL_MATE_CLR - MCC_EPS <= MCC_RAIL_DEPTH - MCC_RAIL_MALE_H,
        str("mcc: T1-62 rail roof clearance ", MCC_RAIL_DEPTH - MCC_RAIL_MALE_H,
            " mm, below MCC_RAIL_MATE_CLR=", MCC_RAIL_MATE_CLR));
    // T1-66 (D52): the roof lead-in is taller than the strips' engagement, so they meet a ramp and
    // never the face's edge, and it stays inside the wall it is cut into.
    assert(lock_e < MCC_RAIL_LEADIN && MCC_RAIL_LEADIN <= MCC_WALL + MCC_EPS,
        str("mcc: T1-66 rail lead-in ", MCC_RAIL_LEADIN, " must exceed the lock engagement ", lock_e,
            " and stay within MCC_WALL=", MCC_WALL));
    assert(is_undef(entry_x) || (len / 2 - MCC_EPS <= entry_x && entry_x <= len / 2 + open_ext + MCC_EPS),
        str("mcc: rail_female_cut entry_x=", entry_x, " outside [len/2, len/2 + open_ext]"));
    clr = MCC_RAIL_CLR_HORIZ;
    b = mcc_rail_lock_slot(len, lock_e);

    union() {
        // No Z shift: _mcc_rail_taper_eps() already pierces Z=0 with its own slab, so the groove roof
        // sits at exactly MCC_RAIL_DEPTH.
        translate([open_ext / 2, 0, 0])
            _mcc_rail_taper_eps(len + open_ext, clr, MCC_EPS);
        // D52: the lock's roof slot, flank to flank, so it splits the roof bridge instead of holing it.
        translate([b[0][0], b[1][0], b[2][0] - MCC_EPS])
            cube([b[0][1] - b[0][0], b[1][1] - b[1][0], b[2][1] - b[2][0] + MCC_EPS]);
        // D52: the DP48-style 45-degree lead-in at the outer face the male enters through -- the outer
        // slice is both wider and taller, so the roof chamfers as well as the flanks and the mouth.
        if (!is_undef(entry_x))
            hull() {
                translate([entry_x - MCC_RAIL_LEADIN, 0, 0])
                    _mcc_rail_taper_eps(MCC_EPS, clr, MCC_EPS);
                translate([entry_x + MCC_EPS, 0, 0])
                    _mcc_rail_taper_eps(MCC_EPS, clr + MCC_RAIL_LEADIN, MCC_EPS, h = MCC_RAIL_DEPTH + MCC_RAIL_LEADIN);
            }
    }
}

// Module: _mcc_rail_taper_eps()
// Description:
//   Private. _mcc_rail_taper() at its true [0, h], plus a thin slab at the mouth width spanning
//   [-eps, 0], so the cut pierces the caller's own Z=0 face cleanly (manifold-avoidance). Nothing is
//   shifted: D44 removed the caller's extra -eps shift, which lowered the groove roof.
module _mcc_rail_taper_eps(len, clr, eps, h = MCC_RAIL_DEPTH) {
    union() {
        _mcc_rail_taper(len, clr, h);
        // Thin slab at MOUTH width, spanning [-eps, 0] in this module's own shifted frame, so the
        // cut pierces the exterior floor face rather than sharing a coincident face with it.
        translate([0, 0, -eps])
            cuboid([len, MCC_RAIL_MOUTH_W + 2 * clr, eps], anchor = BOTTOM);
    }
}

// vim: expandtab tabstop=4 shiftwidth=4 softtabstop=4 nowrap
```

---

## 6. `lib/mcc/mounts.scad`

**H6.1** `lib/mcc/mounts.scad` — Header: the floor owner's list (tie-down gone, D52 items added).
Replace:
```openscad
//   Owns: the tool-less dovetail mount rail (D-15, rev 9, issue #25 — replaces VESA; widened, flush and
//   >= 0.5 mm-clearance since D44), strap slots (displaced off the reserved splitter bay per §7.1
//   correction 1), the splitter tie-down (mcc_splitter_tiedown(orient="edge")), and a minimal
//   stacking-profile recess.
```
with:
```openscad
//   Owns: the tool-less dovetail mount rail (D-15, rev 9, issue #25 — replaces VESA; widened, flush and
//   >= 0.5 mm-clearance since D44; closed -X end wall, top lock and its slot backing since D52), strap
//   slots (displaced off the reserved splitter bay per §7.1 correction 1), and a minimal
//   stacking-profile recess. The splitter tie-down slots are gone (D52): the bay stays reserved and
//   nothing is cut into the floor under it.
```

**H6.2** `lib/mcc/mounts.scad` — Drop the import that only served the tie-down.
Delete exactly these lines:
```openscad
use <poe_splitter.scad> // mcc_splitter_tiedown()
```

**H6.3** `lib/mcc/mounts.scad` — `mcc_floor_features_add()` doc: the sill's new length and the backing.
Replace:
```openscad
//   ADDITIVE floor features: the mount-rail sill (D-15, rev 9, issue #25 — replaces VESA), a plain
//   MCC_RAIL_LEN x (MCC_RAIL_ROOT_W + 2*MCC_RAIL_SILL_SIDE_W) x MCC_RAIL_SILL_H solid block at
//   (0, MCC_RAIL_Y), skipped
```
with:
```openscad
//   ADDITIVE floor features: the mount-rail sill (D-15, rev 9, issue #25 — replaces VESA), a plain
//   (MCC_RAIL_LEN + 2*MCC_RAIL_END_WALL) x (MCC_RAIL_ROOT_W + 2*MCC_RAIL_SILL_SIDE_W) x MCC_RAIL_SILL_H
//   solid block at (0, MCC_RAIL_Y) -- the groove's closed -X end keeps MCC_RAIL_END_WALL of it (T1-91)
//   -- plus the lock slot's backing (mcc_rail_female_backing(), T1-38, D52), skipped
```

**H6.4** `lib/mcc/mounts.scad` — The sill: T1-17 and T1-91 asserts, the sill grows by `MCC_RAIL_END_WALL` at each end, and the slot backing.
Replace:
```openscad
        translate([0, MCC_RAIL_Y, 0])
            // Width: root + a full side wall each side (MCC_RAIL_SILL_SIDE_W, D30) — never just
            // the root width, which leaves knife-edge sill walls and an unsupported groove roof.
            _mcc_floor_boss_from_below_rect([MCC_RAIL_LEN, MCC_RAIL_ROOT_W + 2 * MCC_RAIL_SILL_SIDE_W], MCC_RAIL_SILL_H);
```
with:
```openscad
        // T1-17 (D45, closed by D52): the sill -- the working length plus MCC_RAIL_END_WALL at each
        // end -- clears the reserved splitter bay by MCC_FAN_BAY_CLR (architecture.md §6 clearance rule).
        sill_x0 = -MCC_RAIL_LEN / 2 - MCC_RAIL_END_WALL;
        assert(sill_x0 >= struct_val(l, "splitter_bay_x")[1] + MCC_FAN_BAY_CLR - MCC_EPS,
            str("mcc: T1-17 rail sill -X end x=", sill_x0, " is within MCC_FAN_BAY_CLR=", MCC_FAN_BAY_CLR,
                " of the reserved splitter bay (x <= ", struct_val(l, "splitter_bay_x")[1], ") on \"",
                mcc_dev_slug(dev), "\""));
        // T1-91 (D52): the groove's closed -X end keeps a full wall behind it -- the groove
        // (MCC_RAIL_DEPTH) is deeper than the floor (MCC_FLOOR_T), so the end stop needs the sill.
        assert(MCC_RAIL_END_WALL >= MCC_WALL - MCC_EPS,
            str("mcc: T1-91 MCC_RAIL_END_WALL=", MCC_RAIL_END_WALL, " below MCC_WALL=", MCC_WALL));

        translate([0, MCC_RAIL_Y, 0]) {
            // Width: root + a full side wall each side (MCC_RAIL_SILL_SIDE_W, D30) — never just
            // the root width, which leaves knife-edge sill walls and an unsupported groove roof.
            _mcc_floor_boss_from_below_rect([MCC_RAIL_LEN + 2 * MCC_RAIL_END_WALL, MCC_RAIL_ROOT_W + 2 * MCC_RAIL_SILL_SIDE_W], MCC_RAIL_SILL_H);
            // D52: material over the lock's roof slot, so T1-38 holds there too.
            mcc_rail_female_backing();
        }
```

**H6.5** `lib/mcc/mounts.scad` — Passage comment.
Replace:
```openscad
        // Insertion passage (D34): the groove runs on from +MCC_RAIL_LEN/2 out through the +X wall
```
with:
```openscad
        // Insertion passage (D34): the groove runs on from the sill's +X end out through the +X wall
```

**H6.6** `lib/mcc/mounts.scad` — The passage now starts at the sill's +X end.
Replace:
```openscad
        pass_x0 = MCC_RAIL_LEN / 2 - MCC_EPS;
```
with:
```openscad
        pass_x0 = MCC_RAIL_LEN / 2 + MCC_RAIL_END_WALL - MCC_EPS;
```

**H6.7** `lib/mcc/mounts.scad` — `mcc_rail_features_cut()` comment: the lead-in now chamfers the roof as well.
Replace:
```openscad
        // +X outer face (x = L/2) gets the 45-degree lead-in (D48).
```
with:
```openscad
        // +X outer face (x = L/2) gets the 45-degree lead-in on flanks, mouth and roof (D52).
```

**H6.8** `lib/mcc/mounts.scad` — `mcc_floor_features_cut()` doc.
Replace:
```openscad
//   SUBTRACTIVE floor features: the 2 (or, with the -X pair displaced clear of the splitter bay,
//   still 2) strap-slot pairs, the splitter tie-down (mcc_splitter_tiedown(orient="edge"), NOT
//   hand-rolled holes — layout-patch-wall.md §15 ruling 7), and a minimal stacking-profile recess
//   (a shallow counterbore at each corner lid-fastener position, so a stacked second case's feet
//   have somewhere to seat). (The Magewell-Fishtail M4 reservation was dropped by D44.)
```
with:
```openscad
//   SUBTRACTIVE floor features: the 2 (or, with the -X pair displaced clear of the splitter bay,
//   still 2) strap-slot pairs and a minimal stacking-profile recess (a shallow counterbore at each
//   corner lid-fastener position, so a stacked second case's feet have somewhere to seat). (The
//   Magewell-Fishtail M4 reservation was dropped by D44; the splitter tie-down slots by D52.)
```

**H6.9** `lib/mcc/mounts.scad` — Delete the tie-down call (the lines and the blank line after them).
Delete exactly these lines:
```openscad
    // Splitter tie-down, positioned at the reserved bay's own XY centre.
    bay_x = struct_val(l, "splitter_bay_x");
    bay_y = struct_val(l, "splitter_bay_y");
    translate([(bay_x[0] + bay_x[1]) / 2, (bay_y[0] + bay_y[1]) / 2, 0])
        mcc_splitter_tiedown(orient = "edge");
```

## 7. `lib/mcc/poe_splitter.scad` — retire `mcc_splitter_tiedown()`

**H7.1** `lib/mcc/poe_splitter.scad` — Header.
Replace:
```openscad
//   L1. PoE splitter bay envelope (reservation keep-out) and zip-tie down slots.
```
with:
```openscad
//   L1. PoE splitter spec lookup and its bay envelope (a review ghost; the reservation of record is
//   mcc_case_layout()'s splitter_bay_x/y/z, architecture.md §6). The zip-tie slots were retired (D52).
```

**H7.2** `lib/mcc/poe_splitter.scad` — `mcc_splitter_envelope()` comment no longer points at the retired module.
Replace:
```openscad
    // The splitter's own long/cabled axis (size[0], where its two RJ45 leads run) lands on X in
    // "flat" and on Y in "edge" — same mapping used by mcc_splitter_tiedown() below, so the two
    // modules never disagree about where the splitter body sits.
```
with:
```openscad
    // The splitter's own long/cabled axis (size[0], where its two RJ45 leads run) lands on X in
    // "flat" and on Y in "edge".
```

**H7.3** Delete every line from `// Module: mcc_splitter_tiedown()` down to, **not including**, the final line `// vim: expandtab tabstop=4 shiftwidth=4 softtabstop=4 nowrap`. That removes the module, its doc block and the blank line before the `// vim:` line. `mcc_splitter_spec()` and `mcc_splitter_envelope()` stay.

## 8. `lib/mcc/layout.scad` and `lib/mcc/shell.scad` (comments only)

**H8.1** `lib/mcc/layout.scad` — `mcc_floor_keepout()` doc.
Replace:
```openscad
//   replaces VESA; widened by D44 -- strap slots, splitter tie-down anchor, the side-bolt support-web
```
with:
```openscad
//   replaces VESA; widened by D44 -- strap slots, the side-bolt support-web
```

**H8.2** `lib/mcc/shell.scad` — `mcc_shell_base()` doc.
Replace:
```openscad
//   never cut into the shell at all (it is empty interior volume by construction — only
//   mounts.scad's tie-down and the reservation asserts below touch it).
```
with:
```openscad
//   never cut into the shell at all (it is empty interior volume by construction — only the
//   reservation asserts below and mounts.scad's T1-17 touch it).
```

## 9. Brackets (comments only — their geometry changes only through `mcc_rail_male()` and `mcc_rail_male_keepout()`)

No bracket code changes. `mcc_rail_male()` now carries the strips, and `mcc_rail_male_keepout()` is symmetric, so the arch centre's UP arrow moves 0.35 mm and the vertical bracket's joint pattern `yj_v` moves 0.7 mm — through the accessor, as D50 intended. Only four comments go stale.

**H9.1** `models/brackets/arch-tv-bracket.scad` — `CENTRE_W` comment (the keep-out is symmetric now; the numbers are the ones T1-60 computes).
Replace:
```openscad
                  // (T1-60). Sized for the D34 latch's [-32.5, +36.1]; since D48 the keep-out
                  // (mcc_rail_male_keepout()) is [-32.5, +33.2], so T1-60 needs only
                  // 2 x (33.2 + 1 + 6 + 1) = 82.4 and 92 leaves 2.4 mm on both of its bounds.
                  // Kept at 92 so D48 moves no bracket outline. Was 40 for the 14.6 mm rail.
```
with:
```openscad
                  // (T1-60). Sized for the D34 latch's [-32.5, +36.1]; since D52 the keep-out
                  // (mcc_rail_male_keepout()) is [-32.5, +32.5], so T1-60 needs only
                  // 2 x (32.5 + 1 + 6 + 1) = 81.0 and 92 leaves 2.75 mm on both of its bounds.
                  // Kept at 92 so neither D48 nor D52 moves a bracket outline. Was 40 for the 14.6 mm rail.
```

**H9.2** `models/brackets/arch-tv-bracket.scad` — `C_HALF` comment. **Cleanup rule:** if `feature/retire-end-stop-remnants` has merged and this line reads differently, keep its wording and change only the two numbers: the rail half-length becomes **68** and the end web **22**.
Replace:
```openscad
               // MCC_RAIL_LEN/2 + MCC_RAIL_END_STOP_L = 81, leaving a 9 mm end web (>= MCC_WALL,
```
with:
```openscad
               // MCC_RAIL_LEN/2 + MCC_RAIL_END_STOP_L = 68, leaving a 22 mm end web (>= MCC_WALL,
```

**H9.3** `models/brackets/arch-tv-bracket.scad` — `_RAIL_KO` comment.
Replace:
```openscad
// placement, which negates and swaps both ranges -- the lock bump on the rail-local -Y flank
// lands at +Y here. D50 / F-R1: never built from MCC_RAIL_* internals.
```
with:
```openscad
// placement, which negates and swaps both ranges (symmetric in Y since D52: the lock strips sit on
// the rail's top). D50 / F-R1: never built from MCC_RAIL_* internals.
```

**H9.4** `models/brackets/vertical-tv-bracket.scad` — `CENTRE_HALF_L` comment. **Cleanup rule:** as for the arch's `C_HALF` — if the line reads differently after the cleanup, change only the numbers: **68** and **22**.
Replace:
```openscad
                       // MCC_RAIL_LEN/2 = 75 (no end-stop flange since D48 -- MCC_RAIL_END_STOP_L=0),
                       // leaving a 15 mm end web (>= MCC_WALL, asserted B7/T1-76).
```
with:
```openscad
                       // MCC_RAIL_LEN/2 = 68 (no end-stop flange since D48 -- MCC_RAIL_END_STOP_L=0),
                       // leaving a 22 mm end web (>= MCC_WALL, asserted B7/T1-76).
```

---

## 10. `models/coupons/rail-lock.scad` — replace the whole file

Changes against `main`: header text (the top lock, the new ladder), `LOCK_E` meaning, the echo (`MCC_RAIL_LOCK_RAMP_OUT` is gone), and the groove half: its plinth runs 1 mm past the working length like the case's passage, carries `mcc_rail_female_backing()`, and the lead-in sits at that face (`entry_x = LEN / 2 + 1`). The rail half is unchanged. Replace the file with:

```openscad
//////////////////////////////////////////////////////////////////////
// models/coupons/rail-lock.scad
//   Tier-4 physical coupon (architecture.md §9). A short groove tile (case-floor stand-in,
//   mcc_rail_female_cut()) plus a matching short rail (bracket-plate stand-in, mcc_rail_male()), at
//   MCC_RAIL_LEN's real cross-section but a shorter LEN=60 mm working length -- a fit/lock test, not a
//   full-length print (docs/plans/2026-09-09-mount-rail-and-brackets.md §2). It checks the D44
//   clearances (0.5 mm normal to the flanks and at the roof -- MCC_RAIL_MATE_CLR is a user decision,
//   confirmed here, not calibrated), the groove-roof bridge (architecture.md R40: the groove half
//   prints exactly like the case floor, with the lock's full-width roof slot and its backing), the
//   45-degree lead-in on flanks, mouth and roof, and the top lock (D52): the two rigid strips on the
//   rail's top ride over the roof inside the dovetail's own Z-play, click into the roof slot, and --
//   with the rail plate vertical and the groove half hanging on the upper flank -- cannot be pulled
//   out along the rail until the groove half is pulled about 1 mm away from the plate (M15).
//
//   The groove half stands directly on the bed, groove mouth down and OPEN, like the case floor; the
//   rail half stands on its own plate. Two thin snap-off strips beside the groove join them so the
//   coupon renders/checks as one connected shell (architecture.md §9 Tier 3). Snap the strips off
//   before testing.
//
//   e-ladder (M15): LOCK_E below is passed to both halves and the backing. The exported part uses the
//   production MCC_RAIL_LOCK_ENGAGE; for the ladder, render extra copies with -D LOCK_E=0.4 / 0.5 / 0.7
//   (0.7 is the largest T1-64 allows; see models/coupons/README.md "rail-lock").
//
// Render:
//   openscad --backend=Manifold -o out/rail-lock.stl models/coupons/rail-lock.scad
//////////////////////////////////////////////////////////////////////

$fa = 1; $fs = 0.4;

include <mcc/mcc.scad>

// scripts/build.py always passes -D part="(file-stem)" (the export part name -- see its
// discover_coupons()); "part" is reserved for that and must never be reused as this coupon's own
// parameter -- side-bolt.scad:26-29's documented convention.
part = "rail-lock";

LEN = 60; // working (dovetail) length under test, mm. Well under MCC_RAIL_LEN=150 -- brief's own
           // "short groove tile" instruction (docs/plans/2026-09-09-mount-rail-and-brackets.md §2).
LOCK_E = MCC_RAIL_LOCK_ENGAGE; // lock strip height above the roof line for THIS print, mm -- the
                               // e-ladder overrides it with -D; both halves always get the same value.
MARGIN = 6; // plinth/plate footprint margin beyond MCC_RAIL_ROOT_W, mm. assumed -- wall support
             // around the groove/rail cross-section, generous enough to print cleanly.
GAP = 20; // gap between the female half's own footprint and the male half's, mm. assumed --
           // handling/labelling clearance; the snap-off strips still connect them into one printed
           // shell for the CI mesh check (see the file header comment).
PLATE_T = MCC_FLOOR_T; // the rail half's own plate thickness, mm -- its "bracket plate" stand-in
                         // (mcc_rail_male()'s own local Z=0 sits at its TOP face).

footprint_d = MCC_RAIL_ROOT_W + 2 * MARGIN; // Y footprint shared by both halves' own solid stock.

x_female0 = 0;             // female groove's own [0, LEN] working length, local X; the plinth adds
                           // a MCC_WALL end-stop wall at -X (the groove's CLOSED end, D34) and the
                           // groove runs out open through the plinth's +X end, like the case.
x_male0   = LEN + GAP;     // male rail's own working-length footprint starts here, local X.
x_base0   = -MCC_WALL;     // the coupon's -X extent: the female's stop wall.
STRIP_W   = 2.0;           // snap-off joining strip width, mm. assumed -- thin enough to break by hand.
base_w    = x_male0 + LEN + MARGIN - x_base0;
base_d    = footprint_d;

// This coupon's own lock position, re-derived from ITS OWN (short) LEN, exactly as lib/mcc/rail.scad
// does: the bump's exit face sits MCC_RAIL_LOCK_END_OFFSET inside the rail's +X end.
_lock_exit_x_here = LEN / 2 - MCC_RAIL_LOCK_END_OFFSET;

echo(str(
    "rail-lock: len=", LEN, " sill_h=", MCC_RAIL_SILL_H, " depth=", MCC_RAIL_DEPTH,
    " mouth_w=", MCC_RAIL_MOUTH_W, " root_w=", MCC_RAIL_ROOT_W, " flank_angle=", MCC_RAIL_FLANK_ANGLE,
    " clr_horiz=", MCC_RAIL_CLR_HORIZ, " roof_clr=", MCC_RAIL_ROOF_CLR,
    " lock_e=", LOCK_E, " lock_exit_x=", _lock_exit_x_here,
    " lock_entry_chamfer_deg=", MCC_RAIL_LOCK_RAMP_IN, " lock_slot=", mcc_rail_lock_slot(LEN, LOCK_E),
    " flank_play=", 2 * MCC_RAIL_CLR_HORIZ, " z_play=", mcc_rail_z_play(), " leadin=", MCC_RAIL_LEADIN,
    " print_bbox=", [base_w, base_d, max(MCC_RAIL_SILL_H + LOCK_E + MCC_RAIL_ROOF_CLR, PLATE_T + MCC_RAIL_DEPTH + LOCK_E)]
));

// The rail half's own plate (the bracket-plate stand-in). The rail needs no cut in it (D50). Two
// snap-off strips join it to the groove half, 1 mm in from the coupon's outer long edges and clear of
// the groove's open +X end. (Flush with those edges they left a zero-volume sliver on the bed plane:
// in plan F's prototype, which has no latch nub, `check` saw 2 parts and no watertight mesh.)
module _rail_lock_base() {
    union() {
        translate([x_male0 - MARGIN, -base_d / 2, 0])
            cube([LEN + 2 * MARGIN, base_d, PLATE_T]);
        for (y0 = [-footprint_d / 2 + 1, footprint_d / 2 - 1 - STRIP_W])
            translate([LEN - MCC_EPS, y0, 0])
                cube([x_male0 - MARGIN - LEN + 2 * MCC_EPS, STRIP_W, PLATE_T]);
    }
}

// The male lands MCC_EPS INTO its plate (a genuine shared volume, not a coincident face -- trimesh's
// split(), the Tier-3 "one connected shell" check, would otherwise see two parts).
Z0 = PLATE_T - MCC_EPS;

// Female half: a plinth standing DIRECTLY on the bed with its groove mouth face down -- the case
// floor's own print pose, so the groove roof prints as the same ~66 mm bridge as on a real base (R40).
// mcc_rail_female_cut()'s local Z=0 (the case's exterior floor face) is the bed; the groove is closed
// at -X by a MCC_WALL stop wall and runs out open through the plinth's +X end, 1 mm past the working
// length like the case's passage (D34), with the case's 45-degree lead-in at that face (entry_x, D52).
// The lock slot's backing sits on the plinth exactly as on the case's sill (mcc_rail_female_backing()).
module _rail_lock_female() {
    translate([x_female0, 0, 0])
        difference() {
            union() {
                translate([-MCC_WALL, -footprint_d / 2, 0])
                    cube([LEN + 1 + MCC_WALL, footprint_d, MCC_RAIL_SILL_H]);
                translate([LEN / 2, 0, 0])
                    mcc_rail_female_backing(len = LEN, lock_e = LOCK_E);
            }
            translate([LEN / 2, 0, 0])
                mcc_rail_female_cut(len = LEN, open_ext = 1, entry_x = LEN / 2 + 1, lock_e = LOCK_E);
        }
}

// Male half: mcc_rail_male()'s own local Z=0 (the plate top) lands MCC_EPS into its base
// plate's own top face (world Z=Z0) -- that plate stands in for the bracket's own plate,
// so no extra plate geometry is added here.
module _rail_lock_male() {
    translate([x_male0 + LEN / 2, 0, Z0])
        mcc_rail_male(len = LEN, lock_e = LOCK_E);
}

union() {
    _rail_lock_base();
    _rail_lock_female();
    _rail_lock_male();
}

// vim: expandtab tabstop=4 shiftwidth=4 softtabstop=4 nowrap
```

---

## 11. `tests/test_rail.scad` — replace the whole file

Changes against `main`: the sill length, the lock block (T1-64 … T1-66 re-scoped, T1-91, the slot), the symmetric keep-out, the ladder's top rung 0.7 with its backing, manual checks 4–5. The `MCC_RAIL_END_STOP_*` assert is dropped (the cleanup branch retires those constants; dropping an assert is safe either way). Replace the file with:

```openscad
//////////////////////////////////////////////////////////////////////
// tests/test_rail.scad
//   Tier-2 headless smoke test (architecture.md §9). Instantiates every public module/function in
//   lib/mcc/rail.scad at default (MCC_RAIL_LEN) and short (coupon-scale, len=60) parameters, and
//   exercises the two rev-9 blocking asserts issue #25 introduced:
//     - T1-38 (lib/mcc/rail.scad mcc_rail_female_cut()): >= MCC_FLOOR_T of residual floor over the
//       groove (layout-patch-wall.md §17.2 R1).
//     - D16 (lib/mcc/mounts.scad mcc_assert_floor_keepout_no_overlap()): no two
//       mcc_floor_keepout() rows overlap (no exemptions since D44), run against a real device record.
//     - T1-64 .. T1-66 (D52): the top lock's ride budget, strips and roof lead-in; D50: the
//       rail's plate-side keep-out, mcc_rail_male_keepout().
//     - T1-91 (D52): the groove's closed -X end keeps a full end wall; T1-17 (D45/D52): the rail sill
//       clears the reserved splitter bay, against the tightest SKU (L = 193.9).
//     - T1-62 (D44): >= MCC_RAIL_MATE_CLR normal to the flanks and at the roof.
//   CSG export (-o out.csg) evaluates the full tree so in-model asserts fire, without tessellating.
// Run:
//   openscad --backend=Manifold -o out.csg tests/test_rail.scad
//////////////////////////////////////////////////////////////////////

$fa = 1; $fs = 0.4;

include <mcc/mcc.scad>
include <mcc/devices/pro-convert-for-ndi-to-hdmi.scad>

// --- mcc_rail_sill_size() -- pure function, no geometry ----------------------------------------
_sill = mcc_rail_sill_size();
assert(_sill[0] == MCC_RAIL_LEN + 2 * MCC_RAIL_END_WALL, str("mcc_rail_sill_size len=", _sill[0]));
assert(_sill[1] == MCC_RAIL_ROOT_W + 2 * MCC_RAIL_SILL_SIDE_W, str("mcc_rail_sill_size width=", _sill[1]));
// D30: the sill's side walls beside the groove root must be real walls, not knife edges.
assert(MCC_RAIL_SILL_SIDE_W >= MCC_WALL - MCC_EPS, str("D30: MCC_RAIL_SILL_SIDE_W=", MCC_RAIL_SILL_SIDE_W, " below MCC_WALL"));
assert(_sill[2] == MCC_RAIL_SILL_H, str("mcc_rail_sill_size height=", _sill[2]));

// --- T1-38: MCC_RAIL_SILL_H - MCC_RAIL_DEPTH >= MCC_FLOOR_T, checked directly (not just via the
// module assert, which only fires at render) so a constants.scad regression fails this smoke test
// with a clear message before it ever reaches a full case render. ----------------------------
assert(MCC_RAIL_SILL_H - MCC_RAIL_DEPTH >= MCC_FLOOR_T,
    str("T1-38: MCC_RAIL_SILL_H(", MCC_RAIL_SILL_H, ") - MCC_RAIL_DEPTH(", MCC_RAIL_DEPTH,
        ") must be >= MCC_FLOOR_T(", MCC_FLOOR_T, ")"));

// --- Top lock (D52): ride budget, strips and roof lead-in, checked from the constants so a regression
// fails here before any render (T1-64 .. T1-66, T1-91). ----------------------------------------------
assert(abs(mcc_rail_z_play() - MCC_RAIL_MATE_CLR / cos(MCC_RAIL_FLANK_ANGLE)) < 1e-6,
    str("mcc_rail_z_play()=", mcc_rail_z_play()));
assert(MCC_RAIL_LOCK_ENGAGE + MCC_RAIL_LOCK_PLAY_MARGIN <= mcc_rail_z_play() + MCC_EPS,
    str("T1-64: lock strip ", MCC_RAIL_LOCK_ENGAGE, " + margin ", MCC_RAIL_LOCK_PLAY_MARGIN,
        " does not fit the Z-play ", mcc_rail_z_play()));
assert(30 <= MCC_RAIL_LOCK_RAMP_IN && MCC_RAIL_LOCK_RAMP_IN <= 60, "T1-65: lock entry chamfer outside 30..60 deg");
assert(MCC_RAIL_LOCK_STRIP_Y_OUT <= MCC_RAIL_MOUTH_W / 2 + MCC_RAIL_MALE_H / tan(MCC_RAIL_FLANK_ANGLE) - 1,
    "T1-65: lock strips reach within 1 mm of the male's top edge");
assert(MCC_RAIL_LOCK_ENGAGE < MCC_RAIL_LEADIN && MCC_RAIL_LEADIN <= MCC_WALL,
    "T1-66: rail lead-in not taller than the lock engagement, or deeper than MCC_WALL");
assert(MCC_RAIL_END_WALL >= MCC_WALL - MCC_EPS, "T1-91: the groove's closed end wall is thinner than MCC_WALL");
_slot = mcc_rail_lock_slot();
assert(_slot[1] == [-(MCC_RAIL_ROOT_W / 2 + MCC_RAIL_CLR_HORIZ), MCC_RAIL_ROOT_W / 2 + MCC_RAIL_CLR_HORIZ],
    str("D52: the lock slot must span the whole roof, got y=", _slot[1]));
assert(abs(_slot[2][1] - (MCC_RAIL_DEPTH + MCC_RAIL_LOCK_ENGAGE + MCC_RAIL_ROOF_CLR)) < 1e-6,
    str("D52: lock slot ceiling z=", _slot[2][1]));

// --- D50: the plate-side keep-out every bracket reads (never the MCC_RAIL_LOCK_* constants) --------
_rail_ko = mcc_rail_male_keepout();
assert(_rail_ko == [[-MCC_RAIL_LEN / 2, MCC_RAIL_LEN / 2],
                    [-MCC_RAIL_ROOT_W / 2, MCC_RAIL_ROOT_W / 2]],
    str("D50: mcc_rail_male_keepout()=", _rail_ko));
assert(mcc_rail_male_keepout(60)[0] == [-30, 30],
    str("D50: mcc_rail_male_keepout(60)=", mcc_rail_male_keepout(60)));

// --- T1-62 / D44: >= MCC_RAIL_MATE_CLR on every non-bearing face, and the user's width range ------
assert(MCC_RAIL_CLR_HORIZ * sin(MCC_RAIL_FLANK_ANGLE) >= MCC_RAIL_MATE_CLR - MCC_EPS,
    str("T1-62: rail flank clearance ", MCC_RAIL_CLR_HORIZ * sin(MCC_RAIL_FLANK_ANGLE), " below ", MCC_RAIL_MATE_CLR));
assert(MCC_RAIL_DEPTH - MCC_RAIL_MALE_H >= MCC_RAIL_MATE_CLR - MCC_EPS,
    str("T1-62: rail roof clearance ", MCC_RAIL_DEPTH - MCC_RAIL_MALE_H, " below ", MCC_RAIL_MATE_CLR));
assert(MCC_RAIL_MATE_CLR >= 0.5 - MCC_EPS, "D44: the user's minimum rail clearance is 0.5 mm");
assert(MCC_RAIL_ROOT_W >= 60 && MCC_RAIL_ROOT_W <= 70,
    str("D44: MCC_RAIL_ROOT_W=", MCC_RAIL_ROOT_W, " outside the user's 60-70 mm range"));

// --- mcc_rail_male() / mcc_rail_female_cut() -- default (production MCC_RAIL_LEN) --------------
translate([0, 0, 0]) mcc_rail_male();
// D50: a consumer unions the rail onto its plate -- the rail needs no cut in the plate.
translate([0, -60, 0])
    union() {
        translate([0, 0, -6]) cuboid([MCC_RAIL_LEN + 10, MCC_RAIL_ROOT_W + 10, 6], anchor = BOTTOM);
        mcc_rail_male();
    }
translate([0, 60, 0])
    difference() {
        cuboid([MCC_RAIL_LEN, MCC_RAIL_ROOT_W + 20, MCC_RAIL_SILL_H], anchor = BOTTOM);
        mcc_rail_female_cut(open_ext = 20, entry_x = MCC_RAIL_LEN / 2);
    }

// --- mcc_rail_male() / mcc_rail_female_cut() -- short, coupon-scale len=60 (models/coupons/
// rail-lock.scad's own length) -- the lock strips must be re-derived from THIS len
// (len/2 - MCC_RAIL_LOCK_END_OFFSET); this is exactly the regression the len=60 case here guards
// against. The e-ladder's largest strip (lock_e = 0.7, M15; T1-64's ceiling) must render too, with
// its backing. ------------------------------------------------------------------------------------
translate([200, 0, 0]) mcc_rail_male(len = 60);
translate([200, 60, 0])
    difference() {
        cuboid([60, MCC_RAIL_ROOT_W + 20, MCC_RAIL_SILL_H], anchor = BOTTOM);
        mcc_rail_female_cut(len = 60);
    }
translate([300, 0, 0]) mcc_rail_male(len = 60, lock_e = 0.7);
translate([300, 60, 0])
    difference() {
        union() {
            cuboid([62, MCC_RAIL_ROOT_W + 20, MCC_RAIL_SILL_H], anchor = BOTTOM);
            mcc_rail_female_backing(len = 60, lock_e = 0.7);
        }
        mcc_rail_female_cut(len = 60, open_ext = 1, entry_x = 31, lock_e = 0.7);
    }

// --- D16 / D19 (lib/mcc/mounts.scad): pairwise floor-keepout non-overlap, against a real device
// record and its default variant config, with the mount-rail row now in the list. Emits no
// geometry (pure assert module) -- a bare module-call statement is enough to force evaluation.
DEV = MCC_DEV_PRO_CONVERT_FOR_NDI_TO_HDMI;
VARIANT = [
    ["fan",      false],
    ["splitter", false],
];
mcc_assert_floor_keepout_no_overlap(DEV, VARIANT);

// mcc_floor_keepout()'s own "mount_rail" row, sanity-checked directly (rev 9, D-15).
_ko = mcc_floor_keepout(DEV, VARIANT);
_rail_rows = [for (r = _ko) if (r[4] == "mount_rail") r];
assert(len(_rail_rows) == 1, str("expected exactly one \"mount_rail\" row, got ", len(_rail_rows)));
// D34: the groove runs from its closed end at -MCC_RAIL_LEN/2 out through the +X wall.
_L = struct_val(mcc_case_layout(DEV, VARIANT), "L");
assert(abs(_rail_rows[0][0] - (_L / 2 - MCC_RAIL_LEN / 2) / 2) < 1e-6 && _rail_rows[0][1] == MCC_RAIL_Y,
    str("mount_rail row centre=", [_rail_rows[0][0], _rail_rows[0][1]]));
assert(_rail_rows[0][3] == [_L / 2 + MCC_RAIL_LEN / 2, MCC_RAIL_ROOT_W],
    str("mount_rail row size=", _rail_rows[0][3]));
// No "vesa_*" rows survive (D-15 -- VESA fully removed, not deprecated-but-optional).
_vesa_rows = [for (r = _ko) if (r[4] == "vesa_ne" || r[4] == "vesa_se" || r[4] == "vesa_nw" || r[4] == "vesa_sw") r];
assert(len(_vesa_rows) == 0, str("expected zero VESA rows, got ", len(_vesa_rows)));

// --- mcc_floor_features_add()/mcc_rail_features_cut() -- the shell.scad call-site pair, exercised
// directly (default cfg["rail"]=true) so the ADD/CUT split renders as one clean, watertight block.
translate([400, 0, 0])
    difference() {
        mcc_floor_features_add(DEV, VARIANT);
        mcc_rail_features_cut(DEV, VARIANT);
    }

// cfg["rail"]=false -- both must render (and add/cut) nothing, not error.
translate([400, 60, 0]) {
    mcc_floor_features_add(DEV, [["fan", false], ["splitter", false], ["rail", false]]);
    mcc_rail_features_cut(DEV, [["fan", false], ["splitter", false], ["rail", false]]);
}

echo("mcc test_rail: OK");

// -----------------------------------------------------------------------------------------
// Manual checks: OpenSCAD has no "expect this render to fail" mechanism, so these cannot be
// asserted automatically in a render that must otherwise succeed. To verify a guard by hand,
// append the indicated line to a scratch copy of this file and confirm the render FAILS
// (non-zero exit) with an ERROR containing the quoted text.
//
// 1. T1-38, violated directly by shrinking the constant (constants.scad would need a local
//    override, e.g. via -D, since MCC_RAIL_SILL_H is derived -- simplest is a scratch edit setting
//    MCC_RAIL_SILL_H = MCC_RAIL_DEPTH + 1.0 in constants.scad and re-running this file):
//    -> "T1-38: MCC_RAIL_SILL_H(5) - MCC_RAIL_DEPTH(4) must be >= MCC_FLOOR_T(3)"
//
// 2. D16, violated by moving the rail onto the side-bolt support web (scratch edit constants.scad
//    MCC_RAIL_Y = -40):
//    -> "mcc: floor features \"mount_rail\" and \"side_bolt_web\" overlap ... (D16)"
//
// 3. T1-63 (D44), the opt-in case insert together with the (default-on) rail:
//    mcc_cradle(DEV, [["fan", false], ["splitter", false], ["tripod_insert", true]]);
//    -> "mcc: T1-63 cfg[\"tripod_insert\"]=true needs [\"rail\", false] ..."
//
// 4. T1-64 (D52), lock strips too tall for the Z-play (scratch edit constants.scad
//    MCC_RAIL_LOCK_ENGAGE = 0.8), then render a case base or the coupon; the render fails with:
//    "mcc: T1-64 rail lock strip 0.8 + margin 0.3 does not fit the Z-play 1"
//
// 5. T1-17 (D52), the rail sill running into the splitter bay (scratch edit constants.scad
//    MCC_RAIL_LEN = 150.0), then run this file; it fails with:
//    "mcc: T1-17 rail sill -X end x=-78 is within MCC_FAN_BAY_CLR=2 of the reserved splitter bay ..."
// -----------------------------------------------------------------------------------------

// vim: expandtab tabstop=4 shiftwidth=4 softtabstop=4 nowrap
```

---

## 12. `scripts/rail_fit.py` — replace the whole file

It now proves: zero overlap at full mate, the end stop, the lock while hanging (at every Y in the play band), the square exit face, the ride within the Z-play with margin, and that the groove is closed (rays toward −X, up and sideways). About 1 minute per SKU. Replace the file with:

```python
#!/usr/bin/env python3
"""Virtual insertion sweep: slide the male mount rail into a rendered case base and check that it
mates, stops, locks, rides over its top-lock strips inside the dovetail's own play, and that the
groove is closed everywhere except its mouth and its +X entry (architecture.md §13 D34, D44, D52).

    python scripts/rail_fit.py [case-slug]          # default: pro-convert-for-ndi-to-hdmi

Renders mcc_rail_male() (no plate) with the pinned OpenSCAD and loads exports/(slug)/base.model.stl
(run `build.py render (slug) --part base` first). Frame: the case as rendered (floor at Z=0); the male
sits at (dx, MCC_RAIL_Y + dy, -lift). dx is the insertion offset along X: 0 = fully mated, negative =
over-travel, positive = not yet fully in (also the direction a hanging case is pulled to remove it).
dy is the male's Y offset from the groove's centre line; lift is how far the case stands off the
plate. A case hanging patch-wall down (D49) rests on the male's -Y flank, i.e. at dy_lo; moving off
the plate it rides up that flank, i.e. dy = dy_lo + k * lift (k = the flank's run per mm of height).

Checked, exit code 0 when all hold:
  1. full mate (dx = 0): zero overlap at dy_lo, 0 and dy_hi; the play band dy_hi - dy_lo (about
     2 x 0.577 mm) and the Z-play (about 1.0 mm) are the dovetail's own;
  2. over-travel (dx = -0.5): overlap -- the groove's closed -X end stops the rail;
  3. locked (dx = MCC_RAIL_MATE_CLR + 0.1, floor on the plate): overlap only at the strips' exit
     faces, at every dy in the play band -- lifting the case alone never releases it;
  4. square exit face: the pull-off needed just past the axial play and 1.5 mm further is the same,
     about MCC_RAIL_LOCK_ENGAGE -- no cam;
  5. insertion sweep, every dx: the least pull-off that clears everything, plus
     MCC_RAIL_LOCK_PLAY_MARGIN, fits the Z-play, and at lift 0 nothing but the strips touches;
  6. the groove is closed: rays from inside it toward -X stop at its closed end, rays up (+Z) stop
     at the roof, the roof slot or the lead-in, rays across (+-Y) stop at the flanks.
"""

from __future__ import annotations

import math
import re
import sys
import tempfile
from pathlib import Path

import numpy as np
import trimesh
from trimesh.creation import box

import build

EPS_V = 1e-3    # mm^3: overlap volumes up to this count as zero (mesh noise on touching faces)
TOL = 0.005     # mm: bisection tolerance
RAY_TOL = 0.05  # mm: how far past a boundary a ray hit may land


def _const(name):
    text = (build.LIB_DIR / "mcc" / "constants.scad").read_text(encoding="utf-8")
    return float(re.search(rf"^{name}\s*=\s*([-\d.]+)", text, re.M).group(1))


def _overlap(male, base, dx, dy, lift):
    """(volume, male-frame X span or None) of the male at (dx, MCC_RAIL_Y + dy, -lift) in the base."""
    m = male.copy()
    m.apply_translation([dx, RAIL_Y + dy, -lift])
    inter = trimesh.boolean.intersection([m, base], engine="manifold")
    v = float(inter.volume) if inter is not None and len(inter.faces) else 0.0
    if v <= EPS_V:
        return 0.0, None
    return v, (float(inter.bounds[0][0]) - dx, float(inter.bounds[1][0]) - dx)


def _free(male, base, dx, dy, lift):
    return _overlap(male, base, dx, dy, lift)[0] == 0.0


def _bisect(pred, lo, hi):
    """Smallest t in [lo, hi] with pred(t) true (pred monotone in t); None if pred(hi) is false."""
    if pred(lo):
        return lo
    if not pred(hi):
        return None
    while TOL < hi - lo:
        mid = 0.5 * (lo + hi)
        if pred(mid):
            hi = mid
        else:
            lo = mid
    return hi


def _band_edge(male, base, sign):
    """At full mate on the plate, the farthest collision-free dy from the centre toward `sign`."""
    lo, hi = 0.0, 3.0
    while TOL < hi - lo:
        mid = 0.5 * (lo + hi)
        if _free(male, base, 0.0, sign * mid, 0.0):
            lo = mid
        else:
            hi = mid
    return sign * lo


RAIL_Y = _const("MCC_RAIL_Y")


def main(argv):
    slug = argv[0] if argv else "pro-convert-for-ndi-to-hdmi"
    base_path = build.EXPORTS_DIR / slug / "base.model.stl"
    if not base_path.is_file():
        print(f"error: {base_path} missing - run `build.py render {slug} --part base` first")
        return 1
    with tempfile.TemporaryDirectory(prefix="mcc_railfit_") as t:
        scad = Path(t) / "male.scad"
        scad.write_text("include <mcc/mcc.scad>\nmcc_rail_male();\n", encoding="utf-8")
        stl = Path(t) / "male.stl"
        ok, _ = build.run_openscad(build.find_openscad(), scad, {}, [stl], None)
        if not ok:
            return 1
        male = trimesh.load(str(stl), force="mesh")

    angle = math.radians(_const("MCC_RAIL_FLANK_ANGLE"))
    k = 1.0 / math.tan(angle)                                   # flank run per mm of height
    mate = _const("MCC_RAIL_MATE_CLR")
    e = _const("MCC_RAIL_LOCK_ENGAGE")
    margin = _const("MCC_RAIL_LOCK_PLAY_MARGIN")
    half = _const("MCC_RAIL_LEN") / 2
    x1 = half - _const("MCC_RAIL_LOCK_END_OFFSET")              # strips' exit face, male frame
    x0 = x1 - _const("MCC_RAIL_LOCK_STRIP_X")
    depth = _const("MCC_RAIL_DEPTH")
    z_top = depth + max(_const("MCC_RAIL_LEADIN"), e + mate)    # highest groove surface (slot / lead-in)
    y_side = _const("MCC_RAIL_ROOT_W") / 2 + mate / math.sin(angle) + _const("MCC_RAIL_LEADIN")

    # Everything the male can touch lies within this band; cropping the base once keeps every boolean
    # below fast and loses no contact.
    whole = trimesh.load(str(base_path), force="mesh")
    base = trimesh.boolean.intersection(
        [whole, box(bounds=[[-400, RAIL_Y - 45, -10], [400, RAIL_Y + 45, 12]])], engine="manifold")
    case_len = float(whole.bounds[1][0] - whole.bounds[0][0])
    bad = []

    # 1. Full mate.
    if not _free(male, base, 0.0, 0.0, 0.0):
        print("FAIL: fully mated and centred, but overlapping")
        print("rail fit FAILED")
        return 1
    dy_lo, dy_hi = _band_edge(male, base, -1), _band_edge(male, base, +1)
    play = dy_hi - dy_lo
    mid = 0.5 * (dy_lo + dy_hi)
    zc = _bisect(lambda s: not _free(male, base, 0.0, mid, s), 0.0, 2.0)
    z_play = (zc - TOL) if zc is not None else 2.0
    print(f"full mate: play band dy {dy_lo:+.3f} .. {dy_hi:+.3f} (play {play:.3f} mm), Z-play {z_play:.3f} mm")
    for dy in (dy_lo, 0.0, dy_hi):
        if not _free(male, base, 0.0, dy, 0.0):
            bad.append(f"fully mated but overlapping at dy={dy:+.3f}")

    # 2. Over-travel.
    if _free(male, base, -0.5, dy_lo, 0.0):
        bad.append("no end stop: over-travel at dx=-0.5 does not collide")

    # 3. Locked while hanging, floor on the plate, at every dy in the play band.
    dx_lock = mate + 0.1
    v, span = _overlap(male, base, dx_lock, dy_lo, 0.0)
    print(f"locked:    dx={dx_lock:.2f} hanging  overlap={v:.3f} mm3" + (f"  male x {span[0]:.2f}..{span[1]:.2f}" if span else ""))
    if span is None:
        bad.append(f"not locked: a hanging case slides {dx_lock:.2f} mm toward removal without collision")
    elif span[0] + mate < x0 or x1 + mate < span[1]:
        bad.append(f"lock collision outside the strips {x0:.2f}..{x1:.2f} (male x {span[0]:.2f}..{span[1]:.2f})")
    for dy in np.linspace(dy_lo, dy_hi, 5):
        if _free(male, base, dx_lock, float(dy), 0.0):
            bad.append(f"a lift alone releases the lock: free at dx={dx_lock:.2f} dy={dy:+.3f}")

    # 4. Square exit face: the same pull-off just past the axial play and 1.5 mm further.
    def pull_off(dx):
        return _bisect(lambda s: _free(male, base, dx, dy_lo + k * s, s), 0.0, z_play - 0.01)
    p_near, p_far = pull_off(mate + 0.05), pull_off(mate + 1.5)
    fmt = lambda p: "none" if p is None else f"{p:.3f}"
    print(f"release:   pull-off {fmt(p_near)} mm at dx={mate + 0.05:.2f}, {fmt(p_far)} mm at dx={mate + 1.5:.2f} (engagement {e})")
    if p_near is None or p_far is None or abs(p_near - e) > 0.02 or abs(p_far - p_near) > 0.02:
        bad.append(f"exit face not square / release pull-off {p_near}, {p_far} vs engagement {e}")

    # 5. Insertion sweep.
    dxs = [0.25, 0.4, 0.5, 0.6, 0.75, 1.0, 1.5, 2.0, 3.0, 5.0, 7.5, 10.0]
    dxs += [12.5 + 2.5 * i for i in range(int((case_len / 2 - x0 + 5.0 - 12.5) / 2.5) + 1)]
    dxs += [60.0, 90.0, 120.0, case_len / 2 + half - 1.0]
    worst = 0.0
    for dx in dxs:
        need = pull_off(dx)
        v, span = _overlap(male, base, dx, dy_lo, 0.0)
        if need is None:
            bad.append(f"dx={dx:.2f}: no collision-free position inside the Z-play")
            print(f"dx={dx:7.2f}  BLOCKED")
            continue
        worst = max(worst, need)
        if need > 0.0:
            print(f"dx={dx:7.2f}  ride: off the plate {need:.3f} mm" + (f"  (hanging overlap male x {span[0]:.2f}..{span[1]:.2f})" if span else ""))
        if z_play + TOL < need + margin:
            bad.append(f"dx={dx:.2f}: ride {need:.3f} + margin {margin} exceeds the Z-play {z_play:.3f}")
        if span and (span[0] + mate < x0 or x1 + mate < span[1]):
            bad.append(f"dx={dx:.2f}: collision outside the strips {x0:.2f}..{x1:.2f} (male x {span[0]:.2f}..{span[1]:.2f})")
    print(f"max ride off the plate {worst:.3f} mm of {z_play:.3f} mm Z-play (margin {margin} mm, strips {e} mm)")

    # 6. The groove is closed: rays from inside it.
    x_end = -half
    hits = []
    for z in (0.5, 1.5, 2.5, 3.1, 3.5, 3.9):
        for y in (-25.0, 0.0, 25.0):
            loc, _, _ = whole.ray.intersects_location([[x_end + 20.0, RAIL_Y + y, z]], [[-1.0, 0.0, 0.0]], multiple_hits=False)
            hx = float(loc[0][0]) if len(loc) else None
            hits.append(hx)
            if hx is None or hx < x_end - RAY_TOL:
                bad.append(f"-X ray at z={z} y={y:+.0f}: first hit x={hx}, past the groove's closed end x={x_end}")
    n_up = n_side = 0
    for x in np.arange(x_end + 1.0, case_len / 2 - 0.5, 2.0):
        for y in (-30.0, -15.0, 0.0, 15.0, 30.0):
            loc, _, _ = whole.ray.intersects_location([[x, RAIL_Y + y, 2.0]], [[0.0, 0.0, 1.0]], multiple_hits=False)
            n_up += 1
            if not len(loc) or loc[0][2] > z_top + RAY_TOL:
                bad.append(f"+Z ray at x={x:.1f} y={y:+.0f}: first hit {None if not len(loc) else round(float(loc[0][2]), 2)} above the groove")
        for z in (1.0, 3.0):
            for sign in (-1.0, 1.0):
                loc, _, _ = whole.ray.intersects_location([[x, RAIL_Y, z]], [[0.0, sign, 0.0]], multiple_hits=False)
                n_side += 1
                if not len(loc) or abs(loc[0][1] - RAIL_Y) > y_side + RAY_TOL:
                    bad.append(f"{'+' if sign > 0 else '-'}Y ray at x={x:.1f} z={z}: escapes the groove's flank")
    valid = [h for h in hits if h is not None]
    print(f"groove closed: {len(hits)} -X rays stop at x {min(valid):.2f} .. {max(valid):.2f} (end {x_end}); "
          f"{n_up} +Z rays and {n_side} +-Y rays stay inside the groove")

    for b in bad:
        print("FAIL:", b)
    print("rail fit OK" if not bad else "rail fit FAILED")
    return 0 if not bad else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
```

---

## 13. `scripts/printability.py` — measure cantilever reach on a simplified outline (architect ruling needed)

Why: `_cantilevers()` measures reach at the raw vertices of a trimesh section. A straight bridge edge that crosses a triangulated face gets a collinear mid-edge vertex, and that vertex reads as a cantilever tip. On the prototype this flagged the split roof bridge at z = 4.1 (reach 6.3 and 7.2 mm at the slot walls x = 62.5 / 65.5 and the entry chamfer x = 96.06), while Bambu Studio, the ground truth, sliced the same parts with zero warnings. Dropping vertices within 0.05 mm of the line through their neighbours (Douglas–Peucker keeps a subset of the original vertices) can only lower a measured reach, so no part that passes today can start failing; a real cantilever tip is a corner and stays. The flip side is recorded for the architect: this gate never saw holes inside a bridge (it reads only the outer contour), and still does not — the slicer gate catches those (§1 of bambu-slicer.md).

**H13.1** Replace:
```python
OVERHANG_REPORT_MIN = 20.0  # mm^2 per layer — smaller unsupported rims are just the 45 deg slope
```
with:
```python
OVERHANG_REPORT_MIN = 20.0  # mm^2 per layer — smaller unsupported rims are just the 45 deg slope
CONTOUR_SIMPLIFY = 0.05   # mm — collinear mesh-triangulation vertices are dropped from an overhang
                          # outline before its reach is measured (the slicer's own contours carry none)
```

**H13.2** Replace:
```python
        reach = max(attach.distance(Point(pt)) for pt in poly.exterior.coords)
```
with:
```python
        outline = poly.simplify(CONTOUR_SIMPLIFY, preserve_topology=True)
        reach = max(attach.distance(Point(pt)) for pt in outline.exterior.coords)
```

---

## 14. Goldens (targeted)

Relative to `main`, this PR may change **exactly** these goldens:

- the 8 `tests/golden/<slug>.base.json` and `tests/golden/pro-convert-for-ndi-to-hdmi.base_fan.json`
  (groove, sill, end wall, slot + backing, lead-in, no tie-down slots);
- `tests/golden/coupons/rail-lock.json`;
- `tests/golden/brackets/arch-tv-bracket.centre.json` and `.centre_sandwich.json` (the male rail; the
  UP arrow moves 0.35 mm with the symmetric keep-out);
- `tests/golden/brackets/vertical-tv-bracket.arm.json` and `.centre.json` (the male rail; the joint
  pattern moves 0.7 mm with the keep-out).

No `*.lid.json`, no other coupon, and not `arch-tv-bracket.arm`, `.arm_sandwich`, `.spacer` or
`vertical-tv-bracket.spacer` may change.

The bases stay **inside** the golden tolerance (prototype: HDMI TX volume +0.29 %, bbox unchanged), so
`golden` alone would pass them unchanged. Refresh them anyway, so the record matches the geometry. After
`render --all` (§16 step 6), run exactly:
```
python scripts/build.py golden pro-convert-hdmi-tx pro-convert-sdi-tx pro-convert-hdmi-plus pro-convert-sdi-plus pro-convert-for-ndi-to-hdmi pro-convert-for-ndi-to-hdmi-4k pro-convert-for-ndi-to-sdi pro-convert-for-ndi-to-aio coupons/rail-lock brackets/arch-tv-bracket brackets/vertical-tv-bracket --update
```
Then `git diff --stat main -- tests/golden/` must list only the 14 files above. Lid, arm and spacer
goldens rewritten with identical content do not show up in that diff; if any of them does show up,
stop and report. Never run an untargeted `golden --update`, and never hand-edit JSON.

---

## 15. Documentation (same PR)

Wording rule for every block below: replace the quoted text exactly; if an anchor is not found once,
stop and report.

**H15.1 `CLAUDE.md`, Fixed decisions → Closure.** Replace
```
  every non-bearing face of the joint keeps ≥ 0.5 mm clearance (flanks and roof). **The lock is a
  gravity lock** (user decision 2026-09-28, D48): a rigid 0.7 mm bump on the rail's upper flank drops
  into a pocket in the groove flank and is held there by the case's own weight; nothing flexes, there
  is no latch and no actuator — remove a case by lifting it about 1 mm and sliding it back off. The
  groove's entrance through the +X wall has a 1 × 45° lead-in.
```
with
```
  every non-bearing face of the joint keeps ≥ 0.5 mm clearance (flanks and roof). **The lock sits on
  top of the dovetail** (user decision 2026-09-29, D52 — replaces the D48 flank bump): two rigid
  0.6 mm strips on the rail's top drop into one full-width slot in the groove roof, held there because
  the case's weight on the rail's upper flank wedges the case onto the plate; nothing flexes, there is
  no latch and no actuator — remove a case by pulling it about 1 mm away from the TV (the dovetail
  stops it) and sliding it back off. The groove's entrance through the +X wall has a 1 × 45° lead-in on
  flanks and roof; its closed −X end has a full 3 mm end wall (the rail is 136 mm long).
```

**H15.2 `CLAUDE.md`, the D49 bullet.** Replace
```
  the truss mount (#27) included, and never on a TV turned to portrait: the gravity lock only engages
  when the case's weight rests on the rail's upper flank. Take the case off before the TV is laid
  down, carried or tilted (R44).
```
with
```
  the truss mount (#27) included, and never on a TV turned to portrait: the top lock is only held
  shut while the case's weight rests on the rail's upper flank. Take the case off before the TV is laid
  down, carried or tilted (R44).
```

**H15.3 `CLAUDE.md`, Non-negotiables → Coupons before cases.** Replace
`The rail-lock coupon is the physical gate for the case's groove roof (R40), pocket and lead-in (M15).`
with
`The rail-lock coupon is the physical gate for the case's groove roof (R40), lock slot, strips and lead-in (M15).`

**H15.4 `CLAUDE.md`, Current status.** Replace the two lines
```
insert (D35), no floor-pad island (D37), boss-wide lid-boss webs (D38), the rail gravity lock that
replaced the D34 latch (D48), perfectly round connector holes (D40), a plain Ø2.5 tap-drill bore
```
with
```
insert (D35), no floor-pad island (D37), boss-wide lid-boss webs (D38), the rail's top lock (D52,
which replaced the D48 flank lock), perfectly round connector holes (D40), a plain Ø2.5 tap-drill bore
```

**H15.5 `BOM.md`, the mount-rail row (line starting `| — | — | — | Tool-less dovetail mount rail`).**
In that row replace
`the female groove (case floor, with the lock pocket) and the male rail (with the rigid gravity-lock bump, D48) are printed features.`
with
`the female groove (case floor, with the lock's roof slot and a closed −X end) and the male rail (136 mm, with the two rigid top-lock strips, D52) are printed features.`

**H15.6 `BOM.md`, Mounting brackets intro.** Replace
```
interface is tool-less — a rigid gravity lock, released by lifting the case about 1 mm (D48; its
tests: `models/coupons/rail-lock.scad`, M15).
```
with
```
interface is tool-less — a rigid top lock, released by pulling the case about 1 mm away from the TV and
sliding it off (D52; its tests: `models/coupons/rail-lock.scad`, M15).
```

**H15.7 `models/brackets/README.md`.** Replace
```
rail's gravity lock (D48) only engages in that pose: the case's weight must rest on the rail's upper
flank, where the lock bump is.
```
with
```
rail's top lock (D52) is only held shut in that pose: the case's weight must rest on the rail's upper
flank, whose wedge presses the case onto the rail and keeps the lock strips in their slot.
```
and replace
```
  case rises about 0.7 mm over the lock bump on the way and drops into place).
- **Remove:** lift the case until it stops (about 1 mm — the dovetail itself limits it), then slide it
  back off the way it went on. A plain pull along the rail does not release a hanging case.
```
with
```
  case moves about 0.6 mm off the bracket over the lock strips on the way and drops into place).
- **Remove:** pull the case toward you, away from the TV, until it stops (about 1 mm — the dovetail
  itself limits it), then slide it back off the way it went on. A pull along the rail, or on the
  cables, does not release a hanging case; nor does pushing it up.
```

**H15.8 `.claude/skills/print-check/SKILL.md`, arch row.** Replace
`Install: slide the case on until the lock clicks; remove: lift it about 1 mm, then slide it back off.`
with
`Install: slide the case on until the lock clicks; remove: pull it about 1 mm away from the TV, then slide it back off.`

**H15.9 `models/coupons/README.md`.** In the table row starting `` | `rail-lock.scad` | `` replace
`and its **gravity lock** (D48)` with `and its **top lock** (D52)`. Then replace the whole
`### rail-lock` subsection (from the line `### rail-lock` down to, not including, `## print-log.md`) with:
```
### rail-lock

- Hardware needed: a luggage/fish scale, a dummy mass of the heaviest case (weigh one assembled case
  with its device; ≈ 0.8 kg `assumed` until weighed) that can be strapped to the groove half, a
  temporary loop (string/cable tie), a board to screw or clamp the rail half to vertically, calipers.
- Snap the two joining strips off first.
- **Roof sag (R40):** before inserting anything, measure the groove roof's height above the groove
  half's bottom face at mid-width, at both ends and in the middle (nominal 4.0 mm), and the lock slot's
  ceiling (nominal 5.1 mm). The rail's own top is 3.5 mm tall and its strips 4.6 mm: the roof must stay
  clear of the rail top, and the strip tops must pass under the roof with the groove half lifted.
- **Play (R41):** lying flat, slide the rail half in from the open (+X) end until it stops. With the
  strips *not yet* under the roof (rail only partly in), measure the lateral play (≈ 1.15 mm total)
  and how far the groove half lifts off the rail's plate before it binds (≈ 1.0 mm; the lock needs at
  least `MCC_RAIL_LOCK_ENGAGE` + 0.3 = 0.9 mm of it).
- **Lock, hanging:** clamp the rail half's plate vertical, slide axis horizontal, the rail's strips'
  square faces toward the rail's free end. Strap the dummy mass to the groove half. Hang the groove
  half on the rail's free end and push it along: it must ride over the strips without binding and
  click in. Then (a) pull the groove half along the rail, away from the stop, via the loop at the rail
  line: it must not release up to ≥ 50 N (record where and how it fails if it does); (b) push the
  groove half up from below with about 3 × its weight, then pull it along the rail: no release;
  (c) tug the groove half's lower edge outward, away from the plate, then pull along the rail: no
  release; (d) pull the groove half away from the plate until it stops (≤ 1.2 mm) and slide it off: it
  must release one-handed.
- **e-ladder:** the teamlead or tester produces the extra 3MFs at `LOCK_E` 0.4 / 0.5 / 0.7 for you
  (`python scripts/build.py render coupons/rail-lock -D LOCK_E=0.4`, then 0.5, then 0.7, copying
  `exports/coupons/rail-lock/rail-lock.3mf` aside after each run, then re-running
  `render coupons/rail-lock` without `-D` to restore the release export) — you do not run `build.py`
  yourself. Print each and repeat "Play" and "Lock, hanging" on it, and pick the largest strip that
  never binds.
- **Cycling:** 100 insert/remove cycles on the production copy, then repeat "Play" and "Lock,
  hanging"; inspect the strips' square faces and the slot's +X wall for crushing or wear.
- **Good** = no roof contact, smooth slide-in with a clean click, locked against (a)–(c), one-handed
  pull-and-slide release, play within the expected figures, no wear after 100 cycles.
- Record: roof and slot heights, play and lift, click quality, the pull forces reached in (a), the
  e-ladder results, wear after cycling.
- Update: `lib/mcc/constants.scad` → `MCC_RAIL_ROOF_CLR` if the roof sags into the gap (raise it;
  never narrow the rail — user decision D44), `MCC_RAIL_LOCK_ENGAGE` from the e-ladder. If the play is
  objectionable, report it — `MCC_RAIL_MATE_CLR` is a user decision, not a coupon result.
```

**H15.10 `scripts/README.md`, the `rail_fit.py` row.** Replace the row's description cell (everything
between `` | `rail_fit.py [<slug>]` | `` and the row's final `|`) with:
```
(separate script, run from `scripts/`) Virtual insertion sweep of the male mount rail into a rendered `base.model.stl`: zero overlap at full mate across the play band, the end stop blocks over-travel, a hanging case is locked by the top-lock strips at every lateral position (lifting alone never releases it), the exit faces are square, the ride over the strips fits the dovetail's Z-play with `MCC_RAIL_LOCK_PLAY_MARGIN` to spare, and rays from inside the groove never reach the case interior (closed −X end, roof, flanks) — nothing flexes (architecture.md D34, D44, D52).
```

**H15.11 `CHANGELOG.md`.** Directly under `## [Unreleased]`, insert (followed by one blank line):
```
### Changed (2026-09-29, user decisions) — MAJOR: printed bases and brackets are not interchangeable

- **The rail lock moves on top of the dovetail** (architecture.md D52): two rigid 0.6 mm strips on the
  male rail's top drop into one full-width slot in the case groove's roof (backed by extra floor
  material); the D48 flank bump and pocket are gone. Remove a case by pulling it about 1 mm away from
  the TV and sliding it off. The groove entry's 1 × 45° lead-in now chamfers the roof too.
- **The groove's closed end is closed:** the rail is 136 mm (was 150) and the case sill keeps a full
  3 mm end wall behind the groove's −X end; before, the groove opened into the case between 3 and 4 mm
  above the floor. The sill now clears the reserved PoE-splitter bay by ≥ 2 mm on every SKU (D45).
- **No zip-tie slots in the floor:** the PoE-splitter tie-down slots are removed from every base
  (`mcc_splitter_tiedown()` retired); the splitter bay stays reserved.
- `build.py check` measures a cantilever's reach on a slightly simplified outline, matching the
  slicer (no false alarms from mesh-triangulation vertices on a straight bridge edge).
```

**H15.12** The architect's records (`.claude/knowledge/architecture.md`, `layout-patch-wall.md`) are
written from the architect's verdict, not by the developer from this plan. The proposal is Appendix X.

---

## 16. Ordered steps and verification

1. §3 checks 1–5. Branch `feature/top-rail-lock`.
2. §4 (constants), §5 (rail.scad), §6 (mounts), §7 (poe_splitter), §8, §9, §10, §11, §12, §13 — in
   that order.
3. `python scripts/build.py doctor` — must be clean.
4. `python scripts/build.py smoke` — **11/11 PASS** (prototype: 11/11).
5. `grep -rn --include=*.scad --include=*.py -e mcc_splitter_tiedown -e _mcc_rail_flank_extrude -e _mcc_rail_lock_geom -e _mcc_rail_lock_2d -e MCC_RAIL_LOCK_RAMP_OUT -e MCC_RAIL_LOCK_FLAT lib models tests scripts`
   — must print nothing.
6. `python scripts/build.py render --all`.
7. `python scripts/build.py check --all` — every part **1 part, watertight, 0 floating islands, 0
   cantilevers**; explicitly all 8 bases, `base_fan`, `coupons/rail-lock`, the arch's `centre` and
   `centre_sandwich`, the vertical `arm` and `centre`.
8. From `scripts/`: `..\.venv\Scripts\python rail_fit.py pro-convert-hdmi-tx`, then
   `pro-convert-hdmi-plus`, then `pro-convert-sdi-plus` — each must end `rail fit OK` with: play
   1.154 ± 0.02, Z-play 0.999 ± 0.02, release pull-off 0.60 ± 0.02 at both positions, max ride
   0.60 ± 0.02, and 18 −X rays stopping at x = −68.00.
9. §14 targeted golden update, then `python scripts/build.py golden` (all PASS) and the
   `git diff --stat main -- tests/golden/` check.
10. `python scripts/build.py slicer-check --jobs 3` — **zero warnings on every part**.
11. `python scripts/build.py review`.
12. `python scripts/build.py ci --group k/6 --no-step` for k = 1 … 6.
13. §15 docs; confirm with the architect's verdict before touching the knowledge base (H15.12).
14. One PR into `main`; the body cites D52 (and D53 if the architect files §13 separately), T1-17,
    T1-64 … T1-66 (re-scoped), T1-91, R40, R44, R45, R48, M15, M21, pastes the three `rail_fit.py`
    summaries, and links this plan. CI-green before merge.
15. Physical gate (user): M15 on the `rail-lock` coupon (including the e-ladder), then M21 on the first
    bracket. No full-size case or bracket prints before M15 passes.

---

## 17. Prototype evidence

Trees under `toplock\`: `proto_final` = `main` + exactly this plan's edits (built by
`work\apply_final.py`, which applies every anchor above once and checks the plan text); `proto_a`,
`proto_bsame`, `proto_bstag`, `proto_bstag2` = the option studies. Logs in `toplock\work\`.

| Gate (on `proto_final`) | Result |
|---|---|
| `smoke` | 11/11 PASS |
| `render` | all 8 bases, `base_fan`, `coupons/rail-lock`, the 5 arch parts, the 3 vertical parts — PASS; no assert fires (T1-17, T1-38, T1-62, T1-64 … T1-66, T1-91) |
| `check` | **18/18**: 1 part, watertight, 0 floating islands, 0 cantilevers (with §13) |
| `rail_fit.py` | HDMI TX (L 193.9), HDMI Plus (210.5), SDI Plus (211.5): **rail fit OK** on all three — play 1.154, Z-play 0.999, locked overlap only at x 64.90 … 65.00 (the strips' exit faces), locked at every lateral position, release pull-off 0.603 at dx 0.55 and at dx 2.00 (square face), max ride 0.603 of 0.999 (margin 0.396 ≥ 0.30), 18 −X rays stop at x = −68.00, 410 / 430 / 435 +Z rays and 328 / 344 / 348 ±Y rays stay inside the groove |
| `main` before (same ray test) | rays at z 3.1 / 3.5 / 3.9 run on to the −X wall's inner face: x = −93.95 (HDMI TX), −102.25 (HDMI Plus) |
| `golden` compare vs `main` | beyond tolerance (expected): `rail-lock`, arch `centre` + `centre_sandwich`, vertical `arm` + `centre`; within tolerance (refresh anyway, §14): 8 bases + `base_fan` (HDMI TX volume +0.29 %); unchanged: arch `arm`, `arm_sandwich`, `spacer`, vertical `spacer` |
| Bambu slicer (02.08.02.61) | **zero warnings**: HDMI TX base, HDMI Plus base, `rail-lock`, all 5 arch parts, all 3 vertical parts |

Option studies behind §0 and §18:

| Study | Finding |
|---|---|
| DP48-literal pockets (`proto_a`, first build) | Bambu: "floating cantilever" on the HDMI TX base and the coupon |
| same, pockets removed (roof chamfer kept) | coupon PASS — the pockets were the cause, not the chamfer |
| full-width roof slot | Bambu PASS on both bases, the coupon and all arch parts; the Python `check` flagged the split bridge (reach 6.3 / 7.2 mm at collinear triangulation vertices) until §13 |
| (b-same) 0.35 top + 0.40 flank | ride margin 0.253 measured (0.1 mm lift grid; 0.30 analytic); Bambu PASS |
| (b-stag) catch at x = +38, pocket across the roof slot | Bambu "floating cantilever" on both bases |
| (b-stag2) catch at x = −60, pocket [−63.4, −9.4] | Bambu PASS on both bases; rides disjoint; margins 0.40 / 0.39; catch holds after the top-lock release gesture; 0.75 mm lift releases it |

Images: `toplock\H1_sections.png` — sections of `main` vs plan H, HDMI TX base: (1) the groove's closed
−X end on the rail axis (main: open between z 3 and 4; plan H: 3 mm end wall at x −71 … −68); (2) a
section through a strip at full mate (strip in the roof slot, backing on the sill, passage, roof
chamfer at the +X face); (3) the floor at z 1.5 near the −X wall (the tie-down slot is gone).
`toplock\H2_lock_3d.png` — the male rail's +X end and the case groove seen from below.

---

## 18. The other options — compact deltas

### 18.1 (b-stag): keep the flank lock as a staggered safety catch

The two locks share the dovetail's play (§18.2), so they must never be ridden, or released, at the same
time. (b-stag) keeps both at full depth by giving the flank bump a **long pocket**: at full mate the
bump sits idle at the pocket's −X end, and it only catches the case if the top lock has already been
released and the case has slid ~50 mm.

| Item | Value (prototype `proto_bstag2`, `MCC_RAIL_LEN` 136) |
|---|---|
| Top lock | exactly option (a) |
| Flank catch | the D48 bump (0.70 horizontal, 30° entry, square exit) on the upper flank, exit face at x = −60 (near the leading end) |
| Catch pocket | the bump grown by 0.577, stretched 50 mm toward +X: x ∈ [−63.4, −9.4] |
| Ride windows (never overlap) | strips ride for dx ≤ 42.75 (Plus 211.5); the catch rides for dx ∈ [50.6, 165] |
| Ride margins | 0.40 (strips) / 0.39 (catch) normal — same as (a) and as D48 |
| Catch proven | past dx = 50.6 a hanging case collides only at the bump's face (x −60.2 … −60.0), also after the top-lock release gesture (pulled off 0.6); a 0.75 mm lift releases it |
| Bambu | zero warnings on the compact and Plus bases. The first layout (bump at x = +38, pocket crossing the roof slot) failed with "floating cantilever" on both — the pocket must stay clear of the slot |
| Release | two stages: pull ~1 mm off the TV and slide; it stops after ~5 cm; lift ~1 mm and slide off |
| Insertion | two clicks; the catch rides ~110 mm of the upper flank each insertion (wear: coupon) |

Code deltas against §4–§12: keep `_mcc_rail_flank_extrude()`, `_mcc_rail_lock_geom()` and
`_mcc_rail_lock_2d()` under new `MCC_RAIL_CATCH_*` names (engage 0.70, ramp 30°, flat 1.0, exit face
at `-len/2 + 8`, pocket extension 50.0); union the bump into `mcc_rail_male()` and the stretched pocket
into `mcc_rail_female_cut()`; `mcc_rail_male_keepout()` goes back to `y_min = −ROOT_W/2 − 0.70`. New
asserts: the catch's own ride budget (0.606 + 0.3 ≤ 1.0), the two ride windows disjoint on the longest
SKU, the catch pocket inside the case on the shortest SKU and clear of the roof slot. The 60 mm coupon
cannot hold a 50 mm pocket plus the strips: the catch needs its own coupon (or a 120 mm `rail-lock`).
`rail_fit.py` gains a "caught" check. Estimated extra: ~60 lines of SCAD, ~30 lines of Python, one more
coupon.

### 18.2 (b-same): top and flank lock at the same place — rejected

- Both must be released together, and both draw on the same lower-flank gap: releasing the flank bump
  (e_n normal) and lifting the strips (e_z) need e_z + e_n ≤ 1.0 mm. At full depth 0.60 + 0.61 = 1.21:
  **no motion frees both — the case jams.**
- Shallow enough to fit (0.35 top + 0.40 flank = 0.35 normal): margin 0.30 analytic, **0.25 measured**
  (`proto_bsame`, 0.1 mm grid) — at the edge of the 0.30 target, with a 0.40 mm flank bump that is
  one extrusion line wide. The release window is only 0.30 mm wide (lift up to the stop, then out
  0.35 … 0.65 — pulling out to the stop re-engages the flank).
- It prints (zero Bambu warnings) and it would stop any single-direction accident without the case
  moving at all — but only with a looser joint: `MCC_RAIL_MATE_CLR` 0.8 would give a 1.6 mm Z-play and
  room for both at full depth. That clearance is a user decision (D44).

### 18.3 (c): squeeze-to-release latch — rejected

Assumed layout: the case hangs patch-wall down; "both sides" are the two short end walls (left and
right). The far wall (top) and the lid face are one side each.

- **Force path:** a button in each end wall → an internal wedge → a pawl that drops through a slot in
  the groove roof into a notch in the male rail's top near that end; a spring returns each pawl.
- **Space:** at +X the fan bay (fitted on the Plus family) sits right above the groove's passage; the
  pawl can only come down at case y ∈ [−8.8, +9.6], the rail's lower half, through the +X-end cable
  space. At −X the splitter bay reservation covers case y ∈ [−76.9, −1.9]; only an 8.6 mm lane
  (y ∈ [0.1, 8.7]) is left, and the −X intake vents fill y ∈ [0, W/2 − 3], z 5–23, so the button must
  sit above z = 23.
- **Hands:** the end walls are 194–212 mm apart — **two hands**, plus a push along the rail.
- **Print and parts:** a flexing pawl arm printed in the base's floor-down pose is a mid-air cantilever
  (D28) or a tongue cut from the roof bridge (a hole in a bridge, D33/D52) — both fail the zero-warning
  gate. So the pawls and buttons are separate printed parts with two stainless springs, fitted before the
  lid goes on: 4 extra parts + 2 springs per case, and a notch in every bracket's rail.
- **Flexure numbers, if one were used:** pawl travel 1.5 mm (0.8 engagement + 0.5 clearance + margin);
  ASA strain limit 2.5 % (`MCC_SNAP_STRAIN_MAX`, the retired D34 figure, `assumed`) → cantilever length
  ≥ √(1.5·t·δ/ε) = 13.4 mm at t = 2 mm; unloaded while mounted (the dovetail carries the weight);
  ASA fatigue over many cycles `unknown`.
- **Costs:** two slots open the groove into the case again (undoing T1-91's closure), two button holes
  in the end walls (drop test, dust), a new latch coupon (spring force, cycles, creep).
- **What it would add:** it works in any TV pose (R44/Q23) and needs a deliberate two-sided press.
- **Verdict:** it cannot meet "reachable, one hand, no lid" cleanly: it needs two hands, springs, extra
  parts and roof openings. It could complement (a) later if the case must stay locked while the TV is
  laid down or tilted (Q23).
- **Sketch (for the record):** pawl 6 × 8 mm, 0.8 mm into a 6.5 × 9 × 1.3 mm notch in the male's top at
  rail-local y ≈ +27, x ≈ ±(len/2 − 6); guide bore 6.5 × 8.5 mm through the sill with a boss to z ≈ 12;
  ⌀5 × 10 mm stainless compression spring (~2 N, `assumed`); ⌀10 mm plunger button at case y ≈ +5,
  z ≈ 30, 3 mm travel, 45° wedge.

---

## 19. Open questions for the user

1. **(a) or (b-stag)?** With (a), pulling the case about 1 mm off the TV and sliding it releases it —
   that is the release gesture. With (b-stag), that only moves it ~5 cm to a second catch; a lift and a
   second slide are needed (two clicks in, two stages out). Recommendation: (a) now; (b-stag) if you
   want protection against someone pulling the case off the TV and sliding it.
2. **Rail length 150 → 136 mm** (all brackets and cases). It is the only way to close the groove's end
   without entering the reserved splitter bay (D45). Other brackets: nothing is printed yet.
3. **(b-same) needs a looser joint:** both locks at full depth at one place would need 0.8 mm clearance
   instead of 0.5 (more play when handled). Not recommended.
4. **(c) the squeeze latch** needs two hands, springs and extra parts. Revisit only if a case must stay
   locked when the TV is laid down or tilted (Q23: does your TV lift ever tilt or flip the TV?).
5. **Please weigh one assembled case per family.** W sets every release force above (0.8 kg assumed).
6. The Python printability gate is changed to ignore collinear mesh vertices (§13). It can only drop
   false alarms; the slicer stays the ground truth. The architect rules on it — flagged so you know.

---

## Appendix X — proposed records (the architect's verdict owns the final text)

Revision 19 of `architecture.md` (and `layout-patch-wall.md`):

- **D52** (2026-09-29, user decisions): the rail lock moves from the flank (D48) onto the dovetail's
  top — two strips on the male, one full-width roof slot with a sill backing; square exit faces; the
  roof lead-in; `MCC_RAIL_LEN` 150 → 136 with `MCC_RAIL_END_WALL` so the groove's −X end is closed over
  its full depth (the defect: open between z 3 and 4, a 1 × 66 mm slot into the case) and the sill clears
  the splitter bay; `mcc_splitter_tiedown()` and the floor slots retired; `mcc_rail_male_keepout()`
  symmetric. **D48's flank placement is superseded** (its D34-removal and lead-in parts stand).
- **D45 closed** by D52: the sill's −X end is 2.95 mm clear of the bay on the tightest SKU; T1-17
  implemented in `mcc_floor_features_add()`.
- **D53** (or part of D52, architect's choice): `printability.py` measured cantilever reach at raw
  triangulation vertices; fixed by a 0.05 mm contour simplification (§13).
- **T1 ids:** T1-17 implemented (sill vs splitter bay, `MCC_FAN_BAY_CLR`); T1-64 re-scoped (the ride
  fits the Z-play: `MCC_RAIL_LOCK_ENGAGE + MCC_RAIL_LOCK_PLAY_MARGIN ≤ mcc_rail_z_play()`); T1-65
  re-scoped (entry chamfer 30–60° and shorter than the strip; strips inside the male's top and working
  length); T1-66 re-scoped (`MCC_RAIL_LOCK_ENGAGE < MCC_RAIL_LEADIN ≤ MCC_WALL`); T1-38 extended to the
  slot (the backing); **T1-91 new** (`MCC_RAIL_END_WALL ≥ MCC_WALL`). Next free id **T1-92**.
- **T1-38 at the slot — the ruling asked for.** Chosen: a local backing (9 × 71 × 1.1 mm on the sill),
  which keeps ≥ 3.0 mm over the slot and prints on solid sill. The alternative, no backing and a
  T1-38 exception of 1.9 mm over the slot (the `MCC_RAIL_PASSAGE_ROOF_MIN` precedent: nothing loads the
  slot's ceiling at full mate), saves ~0.7 cm³ per base; not recommended.
- **Risks:** R40 amended (the roof is split by the slot, which the slicer accepts; the roof lead-in
  leaves 1.5 mm of +X wall under the Plus fan aperture). R41: "the gravity lock (D48) holds X" → "the top
  lock (D52) holds X". R44 rewritten for the top lock (held shut by the upper flank's wedge, ≈ 0.58 W;
  released by pulling the case off the TV; still take the case off before the TV moves). R45 rewritten
  (the ride uses 0.6 of the 1.0 mm Z-play; roof sag adds to it). **R48 new:** pulling or prying the case
  off the TV (0.3–1.1 W) and sliding it releases the top lock — accepted with (a), closed by (b-stag).
- **M15** rewritten as in H15.9 (roof and slot heights, lift play, the three accidental-load tests, the
  0.4/0.5/0.7 ladder); **M21** wording: "pull-and-slide removal".
- **§3** L1 table: `rail.scad` "gravity-lock bump and pocket" → "top-lock strips, roof slot and its
  backing"; `poe_splitter.scad` "splitter bay envelope + tie-down" → "splitter spec + review-ghost
  envelope". **§6** floor rule: drop "and the splitter tie-downs"; the D44 paragraph's lock sentence →
  the top lock.

---

## Architect verdict (2026-09-29)

# Architect verdict: Plan H (rev 1), top rail lock, closed groove end, no tie-down slots, cantilever check

Gate: `solution-architect`, 2026-09-29.
- Plan: `scratchpad/plans/H-top-lock-and-floor-fixes.md`.
- Evidence: `scratchpad/toplock/` (`H1_sections.png`, prototype trees and logs).

Checked against:
- `main` @ `4e3a93f` (#61 merged), with G's expected changes (issue #62, `G-lid-screw-hole-openings.VERDICT.md` + Amendment 1) laid over it.
- `.claude/knowledge/architecture.md`, `layout-patch-wall.md` and `CLAUDE.md`.
- The code H replaces: `rail.scad`, `constants.scad` rail section, `mounts.scad`, `poe_splitter.scad`, `layout.scad`, the two brackets, `rail-lock.scad`, `test_rail.scad`, `rail_fit.py`, `printability.py`.
- The user decisions of 2026-09-29:
  - option **(a), top lock only**;
  - `MCC_RAIL_LEN` **150 → 136**;
  - the plan's decisions 1–5.

**Issues:** H's PR closes **#63** (top lock), **#64** (open −X end, rail 136), **#65** (tie-down slots) and **#66** (printability collinear vertices). Records are numbered after those issues (#68 rule).

## Verdict: **APPROVED WITH BINDING CHANGES** (HB1–HB12)

The design is sound, and the prototype evidence is the right depth (render, `check`, `rail_fit.py` on three SKUs, Bambu). I re-derived the load-bearing numbers:

- **Z-play.** Horizontal clearance 0.5774 ÷ flank run 0.5774 = **1.000 mm**. Hanging on the upper flank, lifting by s closes the lower flank's normal gap by exactly s. So e = 0.60 leaves **0.40 mm**, and T1-63.1 asserts 0.60 + 0.30 ≤ 1.0.
- **Wedge.** Hanging, the upper flank carries N = W/cos 30° = 1.155 W. Its component toward the plate is **0.577 W**, which holds the strips in the slot. The release forces in plan §2 follow.
- **Click and play.** The strips sit at x ∈ [63, 65] and the slot at [62.5, 65.5]. The case drops 0.5 mm before the end stop, and the square face gives 0.5 mm of axial play.
- **Backing.** 7.0 + 1.1 − 5.1 = **3.0**, so T1-38 holds over the slot.
- **T1-17.** The sill ends at −71.0, 2.95 mm clear of the bay on L = 193.9 and 11.25 mm on L = 210.5. **136** is the largest even length that meets `MCC_FAN_BAY_CLR`; the limit is 137.9.
- **The −X slit.** It is real (`mounts.scad:63-66`, `H1_sections.png` top-left): a 1 × 66 mm opening into the interior between z = 3 and 4.

Rulings:

1. **Layering and ownership hold.**
   - `mcc_rail_female_backing()`, `mcc_rail_lock_slot()` and `mcc_rail_z_play()` are new public symbols in L1 `rail.scad`. Only `mounts.scad` (the floor owner, §6), the coupon and the tests consume them.
   - Brackets still see only `mcc_rail_male()` and `mcc_rail_male_keepout()` (D50).
   - `mcc_rail_male_keepout()` becomes symmetric. The small bracket moves (arch arrow 0.35 mm; vertical `yj_v` 0.7 mm and `centre_h` 1.4 mm) all come through the accessor, as D50 intends.
   - `layout.scad` still builds the `"mount_rail"` row from constants. The end walls are floor thickening, not cuts, so they need no keep-out row (the D30 precedent).
2. **One full-width slot, not DP48 pockets:** approved. A hole in a roof bridge is what the slicer flags (D33, `bambu-slicer.md`). The slot splits the bridge, and its ceiling is a short bridge supported on all four sides.
3. **T1-38 over the slot (plan Appendix X): the backing, approved.** The exception alternative is rejected, because T1-38 guards the surface that carries a bracket-mounted case.
4. **The roof lead-in: approved.** Recorded cost: on Plus SKUs with the fan, the +X wall between the groove entry and the ⌀38 aperture drops from 2.5 mm to **1.5 mm** at the outer face. This is R40's already-flagged, untested drop edge, amended not escalated.
5. **Plan Q1–Q4:** Q1 is answered (a); Q2 is answered (136); Q3 and Q4 are moot. Neither (b-stag) nor (c) is built; plan §18 stays as the record.
   - **Q5** (case weights) becomes measurement **M63.1**, open for the user.
   - **Q6** (the Python gate, #66) is my ruling below.
6. **Q6 ruling (#66): APPROVED, with a binding self-test (HB6).**
   - Douglas–Peucker keeps a *subset* of the outline's vertices, so the measured reach can only drop. No passing part can start failing.
   - A real tip is a corner, and it survives at 0.05 mm. STL float noise is ~1e-5 mm, a line is 0.42 mm, the limit is 3 mm.
   - It makes the result independent of how Manifold triangulated a face, which is a determinism gain. The slicer gate stays the ground truth.
   - Because this *relaxes* a gate, it must prove the gate still bites: a 6 mm cantilever must fail and a bridge with collinear edge vertices must pass. That is the same rule I set for G's check.
7. **Base/bracket compatibility.** A base and a bracket from either side of this change do not mate (strip height, slot, rail length). So the change is **MAJOR** (CONTRIBUTING.md:35).

## What the plan missed (why the binding changes exist)

- **F1: Ids.** The plan predates #68 and G. It uses D52 (now #61's and G's history), T1-91, and re-scoped T1-64/65/66.
  - Keeping T1-64 … T1-66 while issue #64 creates T1-64.1 would put `T1-64` and `T1-64.1` side by side with unrelated meanings.
  - **Ruling:** the old T1-64/65/66 are **retired** (history). The top lock's asserts are new issue ids (HB2).
- **F2: #61 moved three bracket-comment anchors.** H9.2, H9.3 and H9.4 no longer match `main` (HB3).
- **F3: Stale "gravity-lock" text outside the plan's list** (HB7):
  - `BOM.md:153,184`;
  - `models/brackets/README.md:78,117,163,166`;
  - the two bracket headers (`arch-tv-bracket.scad:9,60`, `vertical-tv-bracket.scad:59-60`);
  - `print-check` SKILL `:75`;
  - `models/coupons/README.md:22,73`. H15.9 changes only three words of row :22, leaving "releases when the groove half is lifted".
- **F4: The new `poe_splitter.scad` header (H7.1) calls the envelope "a review ghost".** It is still an ungated cube (**D24, open**). The header must not claim otherwise (HB4).
- **F5: Stale text in the new coupon (§10):** `MCC_RAIL_LEN=150` and "the bump's exit face" (HB5).
- **F6: #66 relaxes a gate with no proof it still catches a cantilever** (HB6).
- **F7: Plan §3 and §16 assume `main` @ 24c52c8, an 11/11 smoke run and a non-issue branch** (HB1).
- **F8: D7 is still "Open" in §13, although its fix is implemented** (`orient`/`cable_allow` in `poe_splitter.scad`). Its tie-down half becomes moot here. Closed under D65.1.

## Ids (issue-based, #68)

| Issue | Records |
|---|---|
| #63 top lock | **D63.1**; **T1-63.1** (ride ≤ Z-play), **T1-63.2** (strip chamfer/placement), **T1-63.3** (roof lead-in); **R63.1** (pull/pry off the TV + slide releases it); **M63.1** (case weights, the plan's Q5); R40, R41, R44, R45, M15, M21 rewritten or amended |
| #64 −X end, rail 136 | **D64.1**; **T1-64.1** (`MCC_RAIL_END_WALL ≥ MCC_WALL`); **T1-17** implemented under its existing id; **D45 closed** |
| #65 tie-down slots | **D65.1**; **D7 closed** |
| #66 cantilever check | **D66.1** |
| retired | **T1-64, T1-65, T1-66** (the D48 flank lock's asserts: history, never reused) |

Plan-text → id map, used in HB2: `D52` → D63.1 / D64.1 / D65.1 (per block); `T1-64` → T1-63.1; `T1-65` → T1-63.2; `T1-66` → T1-63.3; `T1-91` → T1-64.1; the plan's R48 → R63.1; Q5 → M63.1.

## Binding changes

⟳ marks an anchor that exists only after G merges. Re-read it on post-G `main`, and stop and report if it is not found exactly once.

**HB1: Branch and preconditions** (replace plan §3 points 1–2 and §16 steps 1, 4 and 14).
- **Start only after G's PR has merged.**
- Run `git fetch origin`, then `git switch -c feature/issue-63-top-lock-floor-fixes origin/main`.
- `main` must contain:
  - `| **D62.1** |` in `.claude/knowledge/architecture.md` (G);
  - `mcc_thumbscrew_hole(` in `lib/mcc/fasteners.scad` (G);
  - the #61 tombstone line `// it; D52 removed its zero-valued MCC_RAIL_END_STOP_L/H constants.` in `lib/mcc/constants.scad`.
- #61 has merged, so plan §3 point 2 is settled: use HB3 for the bracket comments.
- Plan §3 points 3–5 stay.
- Plan §16 step 4: `smoke` must be **13/13**: G's 12 plus HB6's `selftest_cantilever()`.
- Plan §16 step 14: see HB11.

**HB2: Id substitutions inside the plan's own blocks.** Apply these to the text of the named plan block **before pasting it**, in the order given. Never search-and-replace in repository files: `D52` is #61's record on `main` (`constants.scad:637`, `arch-tv-bracket.scad:49`, `architecture.md`).

| Plan block | Substitutions, in this order |
|---|---|
| H4.1 | `lock D52` → `lock D63.1` |
| H4.2 | `(D52)` → `(D64.1)`; `(T1-91)` → `(T1-64.1)` |
| H4.3 | `D52: 150 -> 136` → `D64.1: 150 -> 136` |
| H4.4 | `architecture.md §13 D52;` → `architecture.md §13 D63.1;`; `T1-64` → `T1-63.1` (2×); `(D52).` → `(D63.1).` |
| §5 `rail.scad` (whole file) | 1. `T1-64` → `T1-63.1`, `T1-65` → `T1-63.2`, `T1-66` → `T1-63.3` (every occurrence). 2. `(T1-91)` → `(T1-64.1)`. 3. `material beyond it (D52)` → `material beyond it (D64.1)`; `MCC_RAIL_END_WALL at each end (D52)` → `MCC_RAIL_END_WALL at each end (D64.1)`. 4. every remaining `D52` → `D63.1` |
| H6.1 (new text) | `closed -X end wall, top lock and its slot backing since D52), strap` → `closed -X end wall (D64.1), top lock and slot backing (D63.1)), strap`; `are gone (D52):` → `are gone (D65.1):` |
| H6.3 (new text) | `(T1-91)` → `(T1-64.1)`; `T1-38, D52)` → `T1-38, D63.1)` |
| H6.4 (new text) | `closed by D52)` → `closed by D64.1)`; `// T1-91 (D52):` → `// T1-64.1 (D64.1):`; `"mcc: T1-91 MCC_RAIL_END_WALL="` → `"mcc: T1-64.1 MCC_RAIL_END_WALL="`; `// D52: material` → `// D63.1: material` |
| H6.7 (new text) | `(D52).` → `(D63.1).` |
| H6.8 (new text) | `slots by D52.)` → `slots by D65.1.)` |
| H7.1 | replaced by HB4 |
| H9.1 (new text) | `since D52 the keep-out` → `since D63.1 the keep-out`; `nor D52 moves` → `nor D63.1 moves` |
| H9.2, H9.3, H9.4 | replaced by HB3 |
| §10 `rail-lock.scad` (whole file) | `T1-64` → `T1-63.1`; every `D52` → `D63.1`; plus HB5 |
| §11 `test_rail.scad` (whole file) | 1. `T1-64` → `T1-63.1`, `T1-65` → `T1-63.2`, `T1-66` → `T1-63.3`. 2. `T1-91` → `T1-64.1`. 3. `T1-64.1 (D52)` → `T1-64.1 (D64.1)`; `T1-17 (D45/D52)` → `T1-17 (D45/D64.1)`; `T1-17 (D52), the rail sill` → `T1-17 (D64.1), the rail sill`. 4. every remaining `D52` → `D63.1` |
| §12 `rail_fit.py` | `§13 D34, D44, D52)` → `§13 D34, D44, D63.1, D64.1)` |
| H13.1 (new text) | replaced by HB6 |
| §15 | replaced by HB10 / Appendices HC–HD |

After pasting, check that no `D52` in H's changed code or doc lines means the lock, the end wall, the tie-downs or the gate.

**HB3: Bracket comments against `main` after #61** (replace plan H9.2, H9.3, H9.4; H9.1's anchor is unchanged).

- `models/brackets/arch-tv-bracket.scad`, C_HALF comment.
  - Old: `               // MCC_RAIL_LEN/2 = 75 (no end-stop flange since D34), leaving a 15 mm end web`
  - New: `               // MCC_RAIL_LEN/2 = 68 (no end-stop flange since D34), leaving a 22 mm end web`
- `models/brackets/arch-tv-bracket.scad`, the rail keep-out comment.
  - Old:
    ```
    // rotate([0,0,180]) rail placement, which negates and swaps both ranges -- the lock bump on the
    // rail-local -Y flank lands at +Y here. D50 / F-R1: never built from MCC_RAIL_* internals.
    ```
  - New:
    ```
    // rotate([0,0,180]) rail placement, which negates and swaps both ranges (symmetric in Y since D63.1:
    // the lock strips sit on the rail's top). D50 / F-R1: never built from MCC_RAIL_* internals.
    ```
- `models/brackets/vertical-tv-bracket.scad`, CENTRE_HALF_L comment.
  - Old: `                       // MCC_RAIL_LEN/2 = 75 (no end-stop flange since D34), leaving a 15 mm end web`
  - New: `                       // MCC_RAIL_LEN/2 = 68 (no end-stop flange since D34), leaving a 22 mm end web`

**HB4: `lib/mcc/poe_splitter.scad` header** (replaces H7.1's new text). Replace `//   L1. PoE splitter bay envelope (reservation keep-out) and zip-tie down slots.` with:
```openscad
//   L1. PoE splitter spec lookup and its bay envelope module. NOT the reservation: the reservation
//   of record is mcc_case_layout()'s splitter_bay_x/y/z (architecture.md §6); the envelope is a plain
//   cube not yet gated as a review ghost (architecture.md §13 D24, open). The zip-tie slots were
//   retired (D65.1).
```
H7.2 and H7.3 stay as written.

**HB5: `models/coupons/rail-lock.scad`, two stale lines in the plan's §10 text** (apply after HB2).
- `Well under MCC_RAIL_LEN=150` → `Well under MCC_RAIL_LEN=136`.
- `does: the bump's exit face sits MCC_RAIL_LOCK_END_OFFSET inside the rail's +X end.` → `does: the strips' exit face sits MCC_RAIL_LOCK_END_OFFSET inside the rail's +X end.`

**HB6: #66, the gate relaxation with its self-test.**

- Replace plan H13.1's new text with:

```python
OVERHANG_REPORT_MIN = 20.0  # mm^2 per layer — smaller unsupported rims are just the 45 deg slope
CONTOUR_SIMPLIFY = 0.05   # mm — collinear mesh-triangulation vertices are dropped from an overhang
                          # outline before its reach is measured (issue #66, architecture.md D66.1)
```

- H13.2 stays.
- ⟳ Append at the end of `scripts/printability.py`, after G's `selftest_see_through()`:

```python


def selftest_cantilever() -> list[str]:
    """[] when analyse() passes a synthetic bridge whose straight edges carry extra collinear mesh
    vertices and flags a synthetic 6 mm cantilever (issue #66, architecture.md D66.1), else the
    problems. Print pose: 5 mm square pillars 10 mm tall, 1 mm slabs on top."""

    import trimesh

    def box(x0, x1, z0, z1):
        b = trimesh.creation.box(extents=(x1 - x0, 5.0, z1 - z0))
        b.apply_translation(((x0 + x1) / 2, 2.5, (z0 + z1) / 2))
        return b

    problems = []
    bridge = trimesh.boolean.union([box(0, 5, 0, 10), box(25, 30, 0, 10), box(0, 30, 10, 11)],
                                   engine="manifold").subdivide()
    if analyse(bridge).cantilevers:
        problems.append("a bridge whose edges carry collinear vertices is reported as a cantilever")
    cantilever = trimesh.boolean.union([box(0, 5, 0, 10), box(0, 11, 10, 11)], engine="manifold")
    if not analyse(cantilever).cantilevers:
        problems.append("a 6 mm cantilever is not reported")
    return problems
```

- ⟳ In `scripts/build.py` `cmd_smoke()`, directly after G's line `    results.append(("scripts/printability.py selftest_see_through()", not problems, "; ".join(problems)))`, add:

```python
    problems = printability.selftest_cantilever()
    results.append(("scripts/printability.py selftest_cantilever()", not problems, "; ".join(problems)))
```

- If this self-test fails after H13.2 is applied, **stop and report**. Do not tune it, and do not tune `CONTOUR_SIMPLIFY`.

**HB7: Remaining stale "gravity-lock" and "bump" text.** Exact strings.

- `BOM.md` line 153.
  - Old: `for use before M15 (the gravity-lock coupon, as plan F redefines it), M18/M20 (the TV/TV-lift`
  - New: `for use before M15 (the rail-lock coupon), M18/M20 (the TV/TV-lift`
- `BOM.md` line 184: replace `(the gravity-lock coupon)` with `(the rail-lock coupon)`.
- `models/brackets/README.md` line 78.
  - Old: `- **Do not print for use** before M15 (the gravity-lock coupon, as plan F redefines it — see`
  - New: `- **Do not print for use** before M15 (the rail-lock coupon — see`
- `models/brackets/README.md` line 117.
  - Old: `- **Do not print for use** before M15 (the gravity-lock coupon), M20 (the TV/TV-lift measurements:`
  - New: `- **Do not print for use** before M15 (the rail-lock coupon), M20 (the TV/TV-lift measurements:`
- `models/brackets/README.md` line 163.
  - Old: `The dovetail taper and the lock bump that follows its upper flank are the only overhangs (D44, D48), both self-supporting at 30° from vertical;`
  - New: `The dovetail taper is the only overhang (D44), self-supporting at 30° from vertical; the lock strips stand on the rail's flat top and print straight up, their entry chamfer at 45° (D63.1);`
- `models/brackets/README.md` line 166.
  - Old: `Same rail/lock overhangs as arch's own centre, self-supporting at 30° from vertical.`
  - New: `Same rail as arch's own centre: the taper at 30° from vertical, the lock strips printing straight up on its top (D63.1).`
- `models/brackets/arch-tv-bracket.scad` line 9.
  - Old: `//   male's end-stop flange, D48 replaced the latch with the gravity lock. Every rail-dependent value`
  - New: `//   male's end-stop flange, D48 replaced the latch with a gravity lock, D63.1 moved it on top of the rail. Every rail-dependent value`
- `models/brackets/arch-tv-bracket.scad` line 60: replace `before M15 (the gravity-lock coupon, models/coupons/rail-lock.scad)` with `before M15 (the rail-lock coupon, models/coupons/rail-lock.scad)`.
- `models/brackets/vertical-tv-bracket.scad` lines 59–60.
  - Old:
    ```
    //   PRINT GATE: do not print this bracket FOR USE before M15 (the gravity-lock coupon, as plan F
    //   redefines it), M20 (the TV and TV-lift measurements below) and M22 (the sandwich tilt/preload
    ```
  - New:
    ```
    //   PRINT GATE: do not print this bracket FOR USE before M15 (the rail-lock coupon,
    //   models/coupons/rail-lock.scad), M20 (the TV and TV-lift measurements below) and M22 (the sandwich tilt/preload
    ```
- `.claude/skills/print-check/SKILL.md` line 75: apply H15.8 as written, then replace `(the gravity-lock coupon)` with `(the rail-lock coupon)`.
- `models/coupons/README.md` line 22: replace the whole row (the line starting `` | `rail-lock.scad` | ``) with:
```
| `rail-lock.scad` | The tool-less dovetail mount rail (D-15; wide, flush, ≥ 0.5 mm clearance since D44; 136 mm since D64.1) and its **top lock** (D63.1): the dovetail slides freely with the expected play, the groove roof (a ~66 mm bridge printed exactly like the case floor, split once by the lock's full-width slot) does not sag into the 0.5 mm roof gap, the case-side lead-in guides the rail in, and — with the rail plate vertical and the groove half loaded and hanging — the lock clicks, cannot be pulled off along the rail, and releases when the groove half is pulled about 1 mm away from the plate and slid | `lib/mcc/constants.scad` : `MCC_RAIL_ROOF_CLR` (raise it if the roof sags — never narrow the rail), `MCC_RAIL_LOCK_ENGAGE` (the e-ladder); confirms (does not calibrate) `MCC_RAIL_MATE_CLR`, a user decision |
```
- `models/coupons/README.md` line 73: replace the whole row (the line starting `` | `rail-lock` | ``) with:
```
| `rail-lock` | **Print as modelled, no rotation:** the groove half stands directly on the bed, groove mouth down (like the case floor); the rail half stands on its own plate, rail up (like a bracket). Two thin snap-off strips join them — break them off before testing. | Both halves in their production print pose: the groove roof prints as the same ~66 mm bridge as on a real base (architecture.md R40), the lock's roof slot, its backing and the lead-in print like the case's, and the rail's lock strips stand on its top like on a bracket. |
```
- `models/coupons/README.md` `### rail-lock` subsection: apply H15.9's second part as written. Its first part is superseded by the line-22 row above.

**HB8: Test and command docs next to G's text** (⟳ every anchor is G's added text).

- `CLAUDE.md` Standard commands, smoke line.
  - Old: `# tests/*.scad -> .csg, asserts fire; + the lid see-through check's self-test; non-zero exit = fail`
  - New: `# tests/*.scad -> .csg, asserts fire; + the printability checkers' self-tests (see-through, cantilever); non-zero exit = fail`
- `.claude/knowledge/testing.md` Tier 2.
  - Old: `must flag the broken one and pass the other — architecture.md §9, #62).`
  - New:
    ```
    must flag the broken one and pass the other — architecture.md §9, #62) and `selftest_cantilever()`
       (a bridge with collinear edge vertices must pass, a 6 mm cantilever must fail — #66).
    ```
- `.claude/knowledge/testing.md`, "What green means".
  - Old: `and `selftest_see_through()` passed.`
  - New: `and `selftest_see_through()` and `selftest_cantilever()` passed.`
- `tests/README.md`, the paragraph G added.
  - Old: `cannot silently stop finding openings (architecture.md §9, #62).`
  - New: `cannot silently stop finding openings (architecture.md §9, #62); likewise `selftest_cantilever()` for the cantilever check (#66).`
- `tests/README.md`, "Green means".
  - Old: `(or there were none yet), and `selftest_see_through()` passed.`
  - New: `(or there were none yet), and `selftest_see_through()` and `selftest_cantilever()` passed.`
- `scripts/README.md`, smoke row.
  - Old: `plus `printability.py`'s `selftest_see_through()`. Fast. |`
  - New: `plus `printability.py`'s `selftest_see_through()` and `selftest_cantilever()`. Fast. |`

**HB9: Goldens.**
- Plan §14 stands: exactly **14** files, via its targeted command, run after G is on `main`.
- The expected deltas are relative to post-G `main`: every base already carries G's +22.40 mm³.
- No `*.lid.json` may change. No other coupon may change, and neither may `arch-tv-bracket.arm`/`.arm_sandwich`/`.spacer` or `vertical-tv-bracket.spacer`.
- Never hand-edit or hand-merge golden JSON.

**HB10: Records.**
- Apply Appendices **HA** (`architecture.md`), **HL** (`layout-patch-wall.md`), **HC** (`CLAUDE.md`) and **HD** (`BOM.md`, the brackets README, `scripts/README.md`, the CHANGELOG) verbatim.
- They replace plan H15.1, H15.4–H15.7, H15.10, H15.11 and Appendix X.
- H15.2, H15.3 and H15.8 stay as written (no ids).
- Copy the plan to `docs/plans/2026-09-29-top-lock-and-floor-fixes.md`, with these three lines (and one blank line) inserted above its title:
```
> **Ids renumbered at the architect gate (issue #68):** the plan's D52 → D63.1 / D64.1 / D65.1 / D66.1
> (per issue), T1-64 → T1-63.1, T1-65 → T1-63.2, T1-66 → T1-63.3, T1-91 → T1-64.1, R48 → R63.1, Q5 →
> M63.1 (see the verdict at the end). `D52` in the repository is #61's end-stop record.
```
- Then append `\n---\n\n## Architect verdict (2026-09-29)\n\n` followed by the full text of this file.

**HB11: Commits and PR.**
- The geometry commit is MAJOR (CONTRIBUTING.md:35, :129):
  - header: `feat(rail)!: top rail lock, closed groove end, no tie-down slots (#63, #64, #65)`;
  - footer: `BREAKING CHANGE: bases and brackets printed on either side of this change do not mate (top-lock strips and slot, 136 mm rail).`
- The #66 change goes in its own `fix(check): ...` commit.
- The docs go in a `docs:` commit.
- The PR body starts with `Closes #63`, `Closes #64`, `Closes #65`, `Closes #66` on four lines. It cites:
  - D63.1–D66.1, T1-17, T1-63.1–3, T1-64.1, the retired T1-64–66;
  - R40, R41, R44, R45, R63.1, M15, M21, M63.1;
  - pastes the three `rail_fit.py` summaries and links the plan copy.
- CI must be green before merge.

**HB12: Order.**
- H lands after G; H9 of G's verdict already says so.
- If H's branch was created and pushed before G merged, it takes G by `git merge main` (CONTRIBUTING.md:100–102), never a rebase. It then re-runs the full gate and HB9.

## DO-NOTs

1. Do not change `MCC_RAIL_ROOT_W`, `MCC_RAIL_MATE_CLR` (user decisions, D44), `MCC_RAIL_Y`, `MCC_RAIL_DEPTH` or `MCC_RAIL_FLANK_ANGLE`.
2. Do not set `MCC_RAIL_LEN` to anything but 136 (user decision) or `MCC_RAIL_LOCK_ENGAGE` to anything but 0.60 (M15 tunes it later).
3. Do not build (b-stag), (b-same) or (c). Do not keep any part of the D48 flank bump or pocket.
4. Do not cut separate pockets per strip; use one full-width slot. Do not drop the backing.
5. Do not remove or shrink the splitter bay reservation, and do not reclaim its 20 mm (§6).
6. Do not touch `mcc_splitter_envelope()` beyond H7.2. D24 is a separate ticket.
7. Do not let a bracket read `MCC_RAIL_LOCK_*` or call `mcc_rail_female_backing()`, `mcc_rail_lock_slot()` or `mcc_rail_z_play()` (D50).
8. Do not change any other printability threshold, do not tune `CONTOUR_SIMPLIFY`, and do not extend G's see-through check to bases.
9. Do not touch lids, the patch wall, or anything from G.
10. Do not reuse T1-64, T1-65 or T1-66 for anything, and do not number anything sequentially (#68).
11. Do not hand-edit goldens. Only the 14 listed files may change.
12. Do not rebase a pushed branch, and do not merge while a check is pending or failing.
13. Do not `git add -A`.
14. Do not print a case or bracket for use before M15 passes.

## Implementation order

1. Wait for G's merge. Then do HB1 (branch, preconditions) and plan §3 points 3–5.
2. Apply plan §4, §5, §6, §7 and §8 with HB2 and HB4.
3. Apply plan §9 with HB2 and HB3.
4. Apply plan §10 with HB2 and HB5.
5. Apply plan §11 and §12 with HB2.
6. Apply plan §13 with HB6.
7. Run `doctor`, then `smoke`, which must be **13/13**.
8. Run plan §16 step 5's grep. Then `grep -rnE "T1-6[4-6]([^.0-9]|$)|T1-91" lib models tests scripts` must print nothing.
9. Run `render --all`, then `check --all`. Every part must be 1 part, watertight, with 0 islands and 0 cantilevers.
10. Run `rail_fit.py` on HDMI TX, HDMI Plus and SDI Plus, with the plan §16 step 8 figures.
11. Update the goldens (HB9).
12. Run `slicer-check --jobs 3`: zero warnings.
13. Run `review`.
14. Run `ci --group k/6 --no-step`. CI runs the STEP stage.
15. Apply the docs: HB7, HB8, HB10.
16. Commit and open the PR as in HB11.
17. After merge, the physical gate is the user's: M15 on `rail-lock`, including the e-ladder; M63.1; then M21 on the first bracket.

For the teamlead: add M63.1 and M15/M21 to `session-resume.md`'s physical plan.

---

## Appendix HA: `.claude/knowledge/architecture.md` (verbatim)

**HA0. Top paragraph.** ⟳ Insert before the line that begins `**Issue #68, 2026-09-29 — record ids follow GitHub issues (user rule).**`, followed by one blank line:
```
**Issues #63–#66, 2026-09-29 — top rail lock, closed groove end, no tie-down slots, cantilever check
(D63.1, D64.1, D65.1, D66.1; plan H, `docs/plans/2026-09-29-top-lock-and-floor-fixes.md`).** User
decisions: the rail lock moves **on top of the dovetail** (#63, D63.1 — option (a), top only): two rigid
0.6 mm strips on the male's top drop into one full-width slot in the groove roof, backed by 1.1 mm of
extra sill so T1-38 holds over it; square exit faces; a 1 × 45° lead-in on flanks, mouth and roof;
release = pull the case about 1 mm off the plate (the dovetail stops it) and slide it off. The D48 flank
bump and pocket are gone, and with them T1-64 … T1-66 (retired; the top lock's asserts are **T1-63.1 …
T1-63.3**). The groove's −X end, which opened into the case between z = 3 and 4, is closed by a 3 mm end
wall, and the rail is **136 mm** (was 150) so the sill clears the reserved splitter bay (#64, D64.1,
**T1-64.1**; T1-17 implemented; D45 closed). The PoE-splitter tie-down slots are removed (#65, D65.1;
D7 closed). `build.py check` measures cantilever reach on outlines stripped of collinear mesh vertices,
guarded by a `smoke` self-test (#66, D66.1). New: **D63.1, D64.1, D65.1, D66.1, T1-63.1 … T1-63.3,
T1-64.1, R63.1, M63.1**; R40, R41, R44, R45, M15, M21 amended. Base, `rail-lock` and bracket goldens
move; a base and a bracket from either side of the change do not mate (MAJOR).
```

**HA1. §3, the L1 list.**

Old:
```
    lib/mcc/rail.scad                     mount-rail dovetail profile: male rail, female cut,
                                          gravity-lock bump and pocket, plate-side keep-out
                                          (rev 17). ONE source of truth shared by
```
New:
```
    lib/mcc/rail.scad                     mount-rail dovetail profile: male rail, female cut,
                                          top-lock strips, roof slot and its backing,
                                          plate-side keep-out (D63.1). ONE source of truth shared by
```
- Old: `    lib/mcc/poe_splitter.scad             splitter bay envelope + tie-down`
- New: `    lib/mcc/poe_splitter.scad             splitter spec + bay envelope module (tie-down retired, D65.1)`

**HA2. §3, the `rail.scad` rules.**

- Old: ``  `mcc_rail_male()` (additive), `mcc_rail_female_cut()` (subtractive), `mcc_rail_sill_size()` and `mcc_rail_male_keepout()` (pure, rev 17).``
- New: ``  `mcc_rail_male()` (additive), `mcc_rail_female_cut()` (subtractive), `mcc_rail_female_backing()` (additive, case side — the material over the lock's roof slot, D63.1), and the pure `mcc_rail_sill_size()`, `mcc_rail_male_keepout()` (rev 17), `mcc_rail_lock_slot()` and `mcc_rail_z_play()` (D63.1).``

Replace the 6-line bullet that begins `  - **Brackets consume the rail through two public symbols only** (rev 17, D50)` with:
```
  - **Brackets consume the rail through two public symbols only** (rev 17, D50): `mcc_rail_male(len)`,
    unioned onto the bracket's plate — the rail needs no cut in any plate — and
    `mcc_rail_male_keepout(len)`, the rail-local plate-side keep-out (the lock strips included; they sit
    on the rail's top, so it is symmetric since D63.1) that the bracket maps through its own placement
    and pads with its own clearance. A bracket never passes `lock_e` (only the rail-lock coupon's
    e-ladder does, always the same value to male, cut and backing), never reads `MCC_RAIL_LOCK_*` or
    other rail internals, never calls the case-side `mcc_rail_female_backing()`, `mcc_rail_lock_slot()`
    or `mcc_rail_z_play()`, and never rebuilds the rail's footprint.
```

**HA3. §6, the floor rule.**

Old:
```
  **mount-rail dovetail groove and its sill** (D-15, rev 9 — replaces VESA; widened by D44), the
  strap slots, the stacking profile and the splitter tie-downs (the Magewell-Fishtail M4 reservation
  was dropped by D44). It exposes `mcc_floor_keepout()` and asserts non-overlap between all of them.
```
New:
```
  **mount-rail dovetail groove and its sill** (D-15, rev 9 — replaces VESA; widened by D44; 136 mm
  with a closed −X end wall since D64.1), the strap slots and the stacking profile (the
  Magewell-Fishtail M4 reservation was dropped by D44, the splitter tie-down slots by D65.1 — the bay
  stays reserved and nothing is cut under it). It exposes `mcc_floor_keepout()` and asserts
  non-overlap between all of them.
```

In the D44 paragraph, old:
```
  under the 4.0 groove, and the lock pocket runs the full depth over the bump) — **T1-62**. The lock
  is the gravity lock (D48): a rigid bump on the rail's upper flank in a pocket of the groove flank,
  held by the case's weight — no plate cut, no flexure. The Fishtail and case-insert reservations
```
New:
```
  under the 4.0 groove, and the lock's roof slot keeps 0.5 mm around the strips) — **T1-62**. The lock
  is the top lock (D63.1, which replaced the D48 flank lock): two rigid strips on the rail's top in one
  full-width slot in the groove roof, held there because the case's weight on the upper flank wedges
  the case onto the plate — no plate cut, no flexure. The Fishtail and case-insert reservations
```

**HA4. §8, the printability bullet.**
- Old: `  it attaches to the layer below — Bambu's "floating cantilever", same 3 mm limit). It is an`
- New:
  ```
    it attaches to the layer below — Bambu's "floating cantilever", same 3 mm limit; reach is measured
    at the overhang outline's vertices after collinear mesh-triangulation vertices are dropped — 0.05 mm,
    D66.1 — so a straight bridge edge never reads as a tip). It is an
  ```

**HA5. §9 Tier 1.** ⟳ Insert after the line ending `render trips it too. Neither is the old **T1-62** (rail clearances, rev 16).`:
```
**#63–#66 add T1-63.1 … T1-63.3 and T1-64.1, implement T1-17 and retire T1-64 … T1-66** (D63.1,
D64.1): T1-63.1 — the lock strips' ride fits the dovetail's Z-play, `MCC_RAIL_LOCK_ENGAGE +
MCC_RAIL_LOCK_PLAY_MARGIN ≤ mcc_rail_z_play()` (0.6 + 0.3 ≤ 1.0); T1-63.2 — the strips' entry chamfer is
30–60° and shorter than the strip, and the strips sit ≥ 1 mm inside the male's top and inside its
working length; T1-63.3 — the roof lead-in is taller than the engagement and no deeper than `MCC_WALL`
(all in `rail.scad` and `tests/test_rail.scad`); T1-64.1 — `MCC_RAIL_END_WALL ≥ MCC_WALL`, the groove's
closed end keeps a full wall (`mounts.scad`); T1-17 — the rail sill's −X end clears the reserved
splitter bay by `MCC_FAN_BAY_CLR` (`mounts.scad`, 2.95 mm on the tightest SKU); T1-38 now also holds over
the lock's roof slot (`mcc_rail_female_backing()`). T1-64 … T1-66 (the D48 flank lock) are retired —
history, never reused, and unrelated to T1-64.1.
```

**HA6. §9 Tier 2.** ⟳ Replace `a Tier-3 checker that silently stops finding anything is worse than none.` with:
```
a Tier-3 checker that silently stops finding anything is worse than none. Since #66 it also runs
`printability.selftest_cantilever()` (a bridge with collinear edge vertices must pass, a 6 mm
cantilever must fail — D66.1).
```

**HA7. §11.**

R40: after its last bullet (the line ending `has no test yet for this edge; flagged, not` and the next line `  blocking.`), append:
```
- **Amended by #63 (D63.1):** the lock's full-width roof slot (3 mm in X, 1.1 mm deep) splits the roof
  bridge — the slicer passes it, separate pockets did not (D33's lesson) — and its ceiling is a second,
  short 66 mm bridge whose sag eats the strips' 0.5 mm top clearance (M15 measures it). The roof
  lead-in raises the groove's entry roof to z = 5.0 at the +X face, so on the Plus family the wall
  under the ⌀38 fan aperture is 1.5 mm at the outer face (was 2.5).
```

R41:
- Old: `push against its weight lifts it off the upper flank. Acceptable (user decision), and the gravity lock`
- New: `push against its weight lifts it off the upper flank. Acceptable (user decision), and the top lock`
- In the next line, replace `(D48) holds X while the case hangs.` with `(D63.1) holds X while the case hangs.`

R44: replace the whole paragraph, from `**R44 — the rail lock is gravity-engaged.` through `Accepted by the user.`, with:
```
**R44 — the rail lock is gravity-engaged. NEW 2026-09-28 (rev 17, D48/D49); rewritten for the top lock by
#63 (D63.1).** While the case hangs patch-wall down its weight rests on the rail's upper flank, whose 60°
wedge presses the case floor onto the plate with ≈ 0.58 × the weight; that keeps the strips in the roof
slot, and their square exit faces stop any axial pull. Pushing the case up (plugging a cable from
below), outward tugs at the patch wall and vertical vibration do not release it (plan H §2). It releases
when the case is pulled ≈ 0.6 mm off the plate — ≈ 0.6–1.1 × the weight straight off the TV, ≈ 0.3–0.5 ×
when its +X end is pried off — and then slid: that is the release gesture, and its accidental version is
R63.1. It does not hold when the upper flank is unloaded: while the case is being hung, when the TV is
laid flat, carried or tilted; then only friction resists sliding. **Take the case off before the TV is
laid down, carried or tilted — including by a TV lift that tilts or flips it (Q23).** Mitigation: D49,
the install/removal text (brackets README), M21. Accepted by the user.
```

R45: replace the whole paragraph, from `**R45 — the ride-over needs the printed flank play.` through `(user decisions).`, with:
```
**R45 — the ride-over needs the printed Z-play. NEW 2026-09-28 (rev 17, D48); rewritten by #63 (D63.1).**
The case rides over the 0.60 mm strips inside the dovetail's own 1.0 mm Z-play (0.40 mm left normal to the
lower flank; T1-63.1 asserts ≥ 0.3). A print ≈ 0.1 mm oversize on each flank face, or a sagging groove
roof, eats that margin — nothing is designed to flex. M15 measures the printed play and runs the
e-ladder (0.4 / 0.5 / 0.7); if it binds, lower `MCC_RAIL_LOCK_ENGAGE`. Never widen the rail or change
`MCC_RAIL_MATE_CLR` (user decisions).
```

R63.1: ⟳ append at the end of §11, after G's R62.1 (its last line `- **Loss.** A non-captive screw can be dropped when a lid is opened on stage — accepted by the user.`), one blank line then:
```
**R63.1 — pulling the case off the TV and sliding it releases the top lock. NEW 2026-09-29 (#63, D63.1)
— accepted with option (a).** The top lock trades D48's weakness (a push up at the patch wall released
it) for this one: pulling the case ≈ 0.6 mm straight off the TV (≈ 0.6–1.1 × its weight, μ 0–0.3) or
prying its +X (fan) end off (≈ 0.3–0.5 ×) and then sliding it releases it — the release gesture, done by
accident. At ≈ 0.8 kg (`assumed`, M63.1) that is ≈ 2–9 N. The plan's option (b-stag), the D48 bump kept
as a second catch 50 mm further along (plan H §18.1), would close it; **the user chose (a)** on
2026-09-29. Re-open only on a user decision, with M21's first-bracket findings in hand.
```

**HA8. §12.**

Replace the whole `| **M15** |` row with:
```
| **M15** | **Print `models/coupons/rail-lock` and test it:** (a) roof sag on the groove half — roof height at mid-width vs 4.0 mm and the lock slot's ceiling vs 5.1 mm; the rail's 3.5 mm top must stay clear of the roof and its 4.6 mm strips must pass under it with the groove half lifted (R40); (b) play with the lock not engaged — ≈ 1.15 mm lateral and ≈ 1.0 mm lift before it binds (R41, R45); (c) **the lock, hanging**: rail plate vertical, groove half loaded to the heaviest case (M63.1) — it rides over the strips without binding and clicks; an axial pull at the rail line does not release it up to ≥ 50 N; a push up from below (≈ 3 × the weight) and then an axial pull does not release it; an outward tug at the lower edge and then an axial pull does not release it; pulling it off the plate until it stops (≤ 1.2 mm) and sliding releases it one-handed; (d) e-ladder `LOCK_E` 0.4 / 0.5 / 0.7; (e) 100 cycles, then (b)–(c) again and inspect the strips' square faces and the slot's +X wall | R40, R41, R44, R45 — every `MCC_RAIL_*` figure is `assumed` except the user-decided width and clearance. (a) decides `MCC_RAIL_ROOF_CLR`; (c)/(d) decide `MCC_RAIL_LOCK_ENGAGE`. **"Coupons before cases" applies to brackets too — no full-size bracket prints before this.** Rewritten by #63 (D63.1) | User, with a luggage scale, a dummy mass and calipers |
```

Replace the whole `| **M21** |` row with:
```
| **M21** | **First bracket print (arch, direct mode), with a real case and device:** no release for pulls on the patch-wall edge, on the cables or on the top (far-wall) edge, nor for a push up from below; the pull-off force that releases the top lock, straight off the TV and prying the +X end; then the one-hand pull-and-slide removal behind a mounted TV (R63.1) | R44, R63.1 — the 60 mm coupon cannot reproduce the full case's levers. Rewritten by #63 (D63.1) | User |
```

⟳ Append after G's `| **M62.1** |` row:
```
| **M63.1** | **Weigh one assembled case per family, with its device (and the fan where fitted)** | R44/R63.1 — every release force in plan H §2 scales with the weight (≈ 0.8 kg `assumed`); M15's dummy mass is this weight | User — **open** |
```

⟳ After G's line `> **#62** adds M62.1 (plan G). From issue #68 on, measurement ids follow the issue (§12's introduction).`, add:
```
> **#63** adds M63.1 and rewrites M15 and M21 (plan H).
```

**HA9. §13.** ⟳ Append after G's `| **D62.2** |` row, which is the last row:
```
| **D63.1** | 2026-09-29 | D48 (the gravity lock: a rigid bump on the rail's upper flank in a pocket of the groove flank) and R44/R45/M15 | **User decision 2026-09-29 (issue #63, plan H option (a)):** the lock sits on top of the dovetail, DP48 style. Research finding: DP48's two separate roof pockets are holes in the ~66 mm roof bridge, which Bambu flags as a floating cantilever on the base and the coupon (D33's lesson), so the case gets one transverse slot across the full roof width instead | The flank lock released when the case was pushed up at the patch wall (plugging a cable from below) and at ≈ 3 W in yaw; the user asked for the lock on top | **Done by #63.** Two rigid strips 2.0 × 20.0 on the male's top at \|y\| 10–30, 0.60 above the roof line, square exit face 3.0 from the male's +X end, 45° entry chamfer (`MCC_RAIL_LOCK_*`); one roof slot (`mcc_rail_lock_slot()`: the strips + 0.5 all round, full roof width) with `mcc_rail_female_backing()` so T1-38 holds over it; roof lead-in 1 × 45° on flanks, mouth and roof; `mcc_rail_male_keepout()` symmetric; `mcc_rail_z_play()`. T1-64 … T1-66 retired, **T1-63.1 … T1-63.3** new; R44, R45, M15, M21 rewritten; R40, R41 amended; **R63.1**, **M63.1**. D48's flank placement is superseded; its D34 removal and lead-in stand. (b-stag), (b-same) and (c) are recorded in the plan (§18), not built |
| **D64.1** | 2026-09-29 | D34: the groove's closed −X end is the axial end stop and the case stays closed; §6 reservation rule (a reserved bay clears every other feature — D45) | `lib/mcc/mounts.scad:63-66` (at `4e3a93f`) ended the sill at x = −`MCC_RAIL_LEN`/2 = −75, exactly where the groove ends; the groove (4.0 deep) is deeper than the floor (3.0), so at the −X end it opened into the case between z = 3 and 4 over its full 66 mm width. The sill also sat 0.55–1.05 mm inside the compact splitter bay (D45) | A 1 × 66 mm slit from outside into the case interior on every SKU, seen by no gate (#62's see-through check covers lids only) | **Fixed by #64 (user decision 2026-09-29: `MCC_RAIL_LEN` 150 → 136).** `MCC_RAIL_END_WALL` = `MCC_WALL`: the sill runs 3 mm past the groove at both ends and closes the −X end over the full groove depth (**T1-64.1**). At 136 mm the sill ends at x = −71, 2.95 mm clear of the bay on the tightest SKU (L = 193.9) — **T1-17** implemented in `mcc_floor_features_add()`; **D45 closed**. `scripts/rail_fit.py` checks it with rays from inside the groove |
| **D65.1** | 2026-09-29 | §6 floor rule (the splitter tie-downs were a floor feature); D7 (`mcc_splitter_tiedown()` must follow the on-edge splitter) | — (a user decision; plan G's mesh check also found the −X slot straddling the −X wall's inner face) | Two 1.5 × 4 mm slots through the floor under the reserved bay, for a splitter no SKU fits (D-14) | **Done by #65 (user decision 2026-09-29).** The slots and `mcc_splitter_tiedown()` are removed; the bay stays reserved (§6) and its reservation in `layout.scad` is unchanged. **D7 closed:** its envelope half (`orient`, `cable_allow`) is implemented and stays; its tie-down half is moot. D24 (the envelope is an ungated cube) stays open |
| **D66.1** | 2026-09-29 | §8 printability gate: `build.py check` approximates Bambu Studio's floating-cantilever test; the slicer is the ground truth | `scripts/printability.py` `_cantilevers()` measured reach at the raw vertices of a mesh section; a straight bridge edge that crosses triangulated faces carries collinear mid-edge vertices, which read as cantilever tips (6.3 / 7.2 mm on plan H's split roof) while Bambu passed the same parts | The result depended on how Manifold triangulated a face, not on the geometry | **Fixed by #66 (architect ruling on plan H's Q6).** Each overhang outline is simplified by `CONTOUR_SIMPLIFY` = 0.05 mm (Douglas–Peucker, a subset of the original vertices) before its reach is measured, so reach can only drop — no part that passes can start failing — and a real tip, a corner, stays. `smoke` runs `selftest_cantilever()`: a bridge with collinear edge vertices must pass, a 6 mm cantilever must fail. Unchanged: the check still reads outer contours only, and the slicer gate stays the ground truth |
```

**HA10. §14, Floor.**

Old:
```
**Floor.** The mount rail (D-15; 65 mm root at `y = −23.5`, flush seat, ≥ 0.5 mm clearance — D44),
strap slots, the splitter tie-down and the stacking profile; `mcc_floor_keepout()` asserts non-overlap.
```
New:
```
**Floor.** The mount rail (D-15; 65 mm root at `y = −23.5`, flush seat, ≥ 0.5 mm clearance — D44;
136 mm, closed −X end wall, top lock — D63.1, D64.1), strap slots and the stacking profile (no splitter
tie-down since D65.1); `mcc_floor_keepout()` asserts non-overlap.
```

## Appendix HL: `.claude/knowledge/layout-patch-wall.md` (verbatim)

**HL1. Status header.** ⟳ Insert before G's line that begins `Status: **issue #62, 2026-09-29**`, followed by one blank line:
```
Status: **issues #63–#66, 2026-09-29** (aligned with `architecture.md` — D63.1, D64.1, D65.1, D66.1,
plan H). §7.1's floor keep-out table: the mount-rail row carries the 136 mm rail, the closed −X end wall
and the top lock; the tie-down row is struck. **§9**: T1-17 implemented, T1-38 and T1-62 extended to
the lock slot and strips, T1-64 … T1-66 retired, **T1-63.1 … T1-63.3** and **T1-64.1** new. No envelope
figure moves.
```

**HL2. §7.1, the mount-rail row.** Replace the whole row that begins `| **Mount rail (dovetail groove + sill)** |` with:
```
| **Mount rail (dovetail groove + sill)** | **`[L/2 + MCC_RAIL_LEN/2] × MCC_RAIL_ROOT_W` rect — the groove from its closed −X end at −68 out through the +X wall (D34), 65 wide — at `y = MCC_RAIL_Y = −23.5`, label `"mount_rail"`** | **Rev 9 (D-15), widened rev 16 (D44), 136 mm long and closed at −X by #64 (D64.1).** Root 65 mm (user range 60–70), mouth derived (60.38); sill `ROOT_W + 2·MCC_RAIL_SILL_SIDE_W` = 71 wide, `y ∈ [−59.0, 12.0]`, and `MCC_RAIL_LEN + 2·MCC_RAIL_END_WALL` = 142 long, `x ∈ [−71, 71]` — a 3 mm end wall closes the groove's −X end over its full depth (T1-64.1); the end walls are floor thickening, not cuts, so the keep-out row stays the groove's footprint. Binding neighbours: the side-bolt web — the sill edge is 3.4 mm clear of the web top (−62.4) on the tightest SKU (W = 158.80), and the keep-out row is 4.4 mm beyond `MCC_FLOOR_FEATURE_EDGE_MIN` (D16); max root at this `y` ≈ 68.9 — and the reserved splitter bay: the sill's −X end is 2.95 mm clear of it on the tightest SKU (L = 193.9; **T1-17**, D45 closed). Z: groove `[0, 4]`, sill `[0, 7]` (T1-38: 3.0 mm over the groove); the top lock's roof slot (`z ∈ [4, 5.1]`, `x ∈ [62.5, 65.5]`, full roof width) carries a 1.1 mm backing on the sill, so T1-38 holds there too (D63.1); the male is `MCC_RAIL_MALE_H` = 3.5 tall and flush on the plate, with ≥ 0.5 mm normal clearance on the flanks, at the roof and around the lock strips (T1-62) |
```

**HL3. §7.1, the tie-down row.** Replace the whole row that begins `| Splitter tie-down |` with:
```
| ~~Splitter tie-down~~ | ~~`mcc_splitter_tiedown()` — 2 × (4 × 1.5) zip-tie slots, on-edge orientation~~ | **STRUCK by #65 (D65.1, user decision 2026-09-29).** No slots are cut under the reserved bay; the bay itself stays reserved (§5, `architecture.md` §6). `mcc_splitter_tiedown()` is retired |
```

**HL4. §9, T1-17.**
- Old: `| T1-17 | `splitter_envelope ∩ mcc_floor_keepout() == ∅` | §7 floor rule |`
- New:
  ```
  | T1-17 | the rail sill's −X end (`−MCC_RAIL_LEN/2 − MCC_RAIL_END_WALL`) clears the reserved splitter bay (`splitter_bay_x[1]`) by `MCC_FAN_BAY_CLR` — the one interior floor feature that reaches the bay's X range now the tie-down slots are gone (D65.1) | §7 floor rule, `architecture.md` §6 clearance rule. Specified as `splitter_envelope ∩ mcc_floor_keepout() == ∅` and never implemented (D45); **implemented by #64 (D64.1)** in `mcc_floor_features_add()` — 2.95 mm on the tightest SKU (L = 193.9) |
  ```

**HL5. §9, T1-38.**
- Old end of row: ``The plan's own `MCC_RAIL_SILL_H > MCC_RAIL_DEPTH` is too weak: it passes at 4.1 mm |``
- New end of row: ``The plan's own `MCC_RAIL_SILL_H > MCC_RAIL_DEPTH` is too weak: it passes at 4.1 mm. **#63 (D63.1):** over the lock's roof slot a 1.1 mm backing on the sill keeps 3.0 mm too (asserted in `mcc_rail_female_backing()`) |``

**HL6. §9, T1-62.**
- Old: `only the lock bump overlaps while sliding, and the lift it needs stays inside the flank play (T1-64))`
- New: `only the lock strips overlap while sliding, the ride they need stays inside the Z-play (T1-63.1), and the roof slot keeps 0.5 mm around them)`

**HL7. §9, T1-64, T1-65 and T1-66.** Replace the three rows that begin `| **T1-64** |`, `| **T1-65** |` and `| **T1-66** |` with:
```
| ~~**T1-64**~~ | ~~*the case rides over the lock bump inside the flank play*~~ | **RETIRED by #63 (D63.1):** the flank lock is gone. The top lock's ride budget is T1-63.1. Not related to T1-64.1 |
| ~~**T1-65**~~ | ~~*the lock is self-locking and fits the rail* (exit face, entry ramp, bump position)~~ | **RETIRED by #63 (D63.1).** The strips' geometry is T1-63.2 |
| ~~**T1-66**~~ | ~~*the case keeps wall around the lock* (sill wall behind the pocket; lead-in ≤ `MCC_WALL`)~~ | **RETIRED by #63 (D63.1):** no flank pocket any more. The lead-in rule is T1-63.3. (Recorded rev 17: T1-67 … T1-69 unused, T1-70 … T1-90 plan D) |
```

**HL8. §9, new rows.** ⟳ Append after G's `| **T1-62.2** |` row:
```
| **T1-63.1** | *the case rides over the top-lock strips inside the Z-play* — `MCC_RAIL_LOCK_ENGAGE + MCC_RAIL_LOCK_PLAY_MARGIN ≤ mcc_rail_z_play()` (0.60 + 0.30 ≤ 1.00) | **new, #63** (D63.1). Evaluated in `mcc_rail_male()` and `tests/test_rail.scad`; `scripts/rail_fit.py` measures the real ride (0.60 ± 0.02, margin 0.40) against rendered bases |
| **T1-63.2** | *the strips are well-formed and sit on the rail* — entry chamfer `MCC_RAIL_LOCK_RAMP_IN` 30–60° and shorter than the strip; `STRIP_Y_IN < STRIP_Y_OUT ≤` the male's top half-width − 1; the strips inside `(−len/2 + 5, len/2 − 1)` | **new, #63** (D63.1). Evaluated in `mcc_rail_male()` and `tests/test_rail.scad` |
| **T1-63.3** | *the roof lead-in meets the strips with a ramp* — `MCC_RAIL_LOCK_ENGAGE < MCC_RAIL_LEADIN ≤ MCC_WALL` | **new, #63** (D63.1). Evaluated in `mcc_rail_female_cut()` and `tests/test_rail.scad` |
| **T1-64.1** | *the groove's closed −X end keeps a full wall* — `MCC_RAIL_END_WALL ≥ MCC_WALL` | **new, #64** (D64.1). Evaluated in `mcc_floor_features_add()` and `tests/test_rail.scad`; `scripts/rail_fit.py` checks the geometry with rays from inside the groove |
```

## Appendix HC: `CLAUDE.md` (verbatim; replaces plan H15.1 and H15.4)

H15.2 and H15.3 stay as in the plan. The smoke line is HB8.

**HC1 (H15.1).** The old text is as in plan H15.1. New:
```
  every non-bearing face of the joint keeps ≥ 0.5 mm clearance (flanks and roof). **The lock sits on
  top of the dovetail** (user decision 2026-09-29, D63.1 — replaces the D48 flank bump): two rigid
  0.6 mm strips on the rail's top drop into one full-width slot in the groove roof, held there because
  the case's weight on the rail's upper flank wedges the case onto the plate; nothing flexes, there is
  no latch and no actuator — remove a case by pulling it about 1 mm away from the TV (the dovetail
  stops it) and sliding it back off. The groove's entrance through the +X wall has a 1 × 45° lead-in on
  flanks and roof; its closed −X end has a full 3 mm end wall (the rail is 136 mm long, D64.1).
```

**HC2 (H15.4).** The old text is as in plan H15.4. New:
```
insert (D35), no floor-pad island (D37), boss-wide lid-boss webs (D38), the rail's top lock (D63.1,
which replaced the D48 flank lock), perfectly round connector holes (D40), a plain Ø2.5 tap-drill bore
```

## Appendix HD: Other documents (verbatim; replaces plan H15.5, H15.6, H15.7, H15.10, H15.11)

**HD1 (H15.5) `BOM.md` line 67.**
- Old: `the female groove (case floor, with the lock pocket) and the male rail (with the rigid gravity-lock bump, D48) are printed features.`
- New: `the female groove (case floor, with the lock's roof slot and a closed −X end, D64.1) and the male rail (136 mm, with the two rigid top-lock strips, D63.1) are printed features.`

**HD2 (H15.6) `BOM.md` lines 140–141.** The old text is as in plan H15.6. New:
```
interface is tool-less — a rigid top lock, released by pulling the case about 1 mm away from the TV and
sliding it off (D63.1; its tests: `models/coupons/rail-lock.scad`, M15).
```

**HD3 (H15.7) `models/brackets/README.md`.** Both replacements as in plan H15.7, with `rail's top lock (D52)` → `rail's top lock (D63.1)` in the first new block.

**HD4 (H15.10) `scripts/README.md`.** As in plan H15.10, with `(architecture.md D34, D44, D52)` → `(architecture.md D34, D44, D63.1, D64.1)`.

**HD5 (H15.11) `CHANGELOG.md`.** ⟳ Insert directly under `## [Unreleased]`, above G's `### Fixed (2026-09-29, issue #62, …` entry, followed by one blank line:
```
### Changed (2026-09-29, issues #63–#65, user decisions) — MAJOR: printed bases and brackets are not interchangeable

- **The rail lock moves on top of the dovetail** (#63, architecture.md D63.1): two rigid 0.6 mm strips on
  the male rail's top drop into one full-width slot in the case groove's roof (backed by extra floor
  material); the D48 flank bump and pocket are gone. Remove a case by pulling it about 1 mm away from
  the TV and sliding it off. The groove entry's 1 × 45° lead-in now chamfers the roof too.
- **The groove's closed end is closed** (#64, D64.1): the rail is 136 mm (was 150) and the case sill keeps
  a full 3 mm end wall behind the groove's −X end; before, the groove opened into the case between 3 and
  4 mm above the floor. The sill now clears the reserved PoE-splitter bay by ≥ 2 mm on every SKU (D45).
- **No zip-tie slots in the floor** (#65, D65.1): the PoE-splitter tie-down slots are removed from every
  base (`mcc_splitter_tiedown()` retired); the splitter bay stays reserved.

### Fixed (2026-09-29, issue #66)

- `build.py check` measures a cantilever's reach on an outline stripped of collinear mesh vertices
  (architecture.md D66.1): no false alarm from triangulation vertices on a straight bridge edge.
  `build.py smoke` runs a self-test that still fails a real 6 mm cantilever.
```
