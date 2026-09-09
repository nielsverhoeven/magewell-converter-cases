# Plan: tool-less mount rail + TV bracket + truss bracket (issues #25, #26, #27)

> ## Architect verdict — 2026-09-09 (`architecture.md` rev 9 / `layout-patch-wall.md` §17)
>
> **#25 rail + #26 TV bracket: APPROVED WITH CHANGES. #27 truss bracket: DEFERRED** (blocked on
> measurement **M14** and a user sign-off of the safety framing, **R26**).
> Branch 1: `feature/issue-25-mount-rail` off `main`. Then `feature/issue-26-tv-bracket` off `main`.
>
> Blocking changes — do not implement the plan as written on these five points:
> 1. `MCC_RAIL_SILL_H = MCC_RAIL_DEPTH + MCC_FLOOR_T = **7.0**` (not 6.0). Assert **T1-38**.
> 2. `MCC_RAIL_Y = **−20.0**` (not +20.0) — under the deck, mass below the mount line. **R24**.
> 3. The D16 pairwise floor assert must exempt the concentric
>    `case_tripod_insert`/`fishtail_reserve` pair, or it fails on all 8 SKUs. **D19**.
> 4. The L1 file is **`rail.scad`**, not `bracket.scad`; `layout.scad` must not `use` it.
> 5. Retire `mcc_floor_bore_cut()`; the rename is **`floor_center`** and **#25 owns it**.
>
> Also: register `discover_brackets()` in `cmd_doctor()` as well as `discover_all()`; the bracket
> plates' cross ribs are where `MCC_RIB_HEIGHT_RATIO_MAX` belongs (**D22**).
> `PLAN-ASSUMPTION` verdicts (2/5/7 ratified, 3 ratified-in-principle, 1 escalated, 4 rejected,
> 6 split): `layout-patch-wall.md` §17.5.

Status: **researcher plan, not yet architect-validated.** Route through `solution-architect` before
any developer starts (Team Charter step 2 — this is structural: new floor-feature owner, new L1
file, new `models/brackets/` discovery path, VESA removed on all 8 SKUs).

Source tickets: [#25](https://github.com/nielsverhoeven/magewell-converter-cases/issues/25) (rail),
[#26](https://github.com/nielsverhoeven/magewell-converter-cases/issues/26) (TV bracket),
[#27](https://github.com/nielsverhoeven/magewell-converter-cases/issues/27) (truss bracket). #26/#27
both depend on #25 — implement in that order, but all three fit in one plan because the interface
is shared and must be designed once.

Required reading before implementing: `.claude/knowledge/architecture.md` §3 (layers), §6 (floor
rule), §9 (asserts); `.claude/knowledge/layout-patch-wall.md` §7.1 (floor keep-out table), §1
(frame); `lib/mcc/mounts.scad`, `lib/mcc/layout.scad`, `lib/mcc/cradle.scad`,
`lib/mcc/fasteners.scad`, `lib/mcc/constants.scad`; `models/pro-convert-for-ndi-to-hdmi/case.scad`
(thin-assembly template); `models/coupons/tg-ladder.scad` + `side-bolt.scad` (coupon style);
`knowledge/design/fdm-rugged-enclosure-guidelines.md` §3.1-equivalent (snap-fit rules, sourced from
`knowledge/components/fasteners-and-hardware.md` §3.1 — see below); `scripts/README.md` /
`scripts/build.py` discovery functions.

---

## 0. Chosen rail concept (read this first)

**Female dovetail groove cut into the case floor (case is the fixed/expensive part, gets the
recessed/flush feature); male dovetail rail on the bracket (bracket is the cheap/replaceable part,
gets the protruding feature).** Reasons, both load-bearing on the decision:

1. **Print-orientation forces it.** The case's floor prints face-down (`architecture.md` §1: "Origin
   at ... the case underside (the bed plane)" — the exterior floor face *is* the bed-contact face on
   every current SKU). A feature that protrudes **below** that face is unprintable without flipping
   the whole base upside-down, which would break every other floor/wall convention in this repo. A
   feature that is **recessed into or stands proud above** that face (i.e. cut upward into the floor
   slab, exactly like the existing VESA/tripod bosses) prints fine face-down. So the case can only
   ever carry the **female** half. The bracket, by contrast, is a flat plate that prints face-down
   with the rail as a self-supporting vertical rib standing **up** off its top face — the male half
   fits its print orientation perfectly.
2. **Drop safety.** D-13 (`architecture.md` §1/§6) already commits this repo to "nothing protrudes
   from any wall" specifically because a protruding feature is the first thing to take a drop impact
   and becomes a stress riser. A male rail on the case floor would be the case's lowest point,
   unprotected, on every drop and every time the bare case is set down on a table. Recessing the
   female groove into the floor keeps the case's drop profile unchanged from every other SKU;
   the exposed male rail lives on the bracket instead, which is either sandwiched flat against a TV
   (protected) or clamped to a truss tube (rigging-grade handling, and a bracket is a cheap flat
   reprint if it is ever damaged — unlike the case).

**Retention/drop-safety load path:** the dovetail's mechanical interlock (undercut cross-section)
carries essentially all *transverse* (out-of-slide-axis) separation force purely geometrically — the
case cannot come off the rail perpendicular to the slide axis short of gross shear failure of the ASA
in the engaged length. The **spring-lip latch only has to resist axial slide-out** (gravity sag,
vibration walk, an incidental shove along the rail) — a much smaller, well-defined load. For the
**truss bracket specifically**, the rail+latch is explicitly **not** the sole overhead fall-restraint:
the mandatory safety-cable eye (#27's own requirement) is the independent secondary restraint that
standard rigging practice always pairs with any primary mount, regardless of how strong the primary
mount is rated. This framing is recorded as `PLAN-ASSUMPTION-1` below — it is a safety-relevant
judgement call, not a geometry detail, and the architect/user should bless it explicitly.

**Symmetric insertion (mount in both orientations)? Decided: no — single insertion direction, end
stop at one end, latch + thumb-release at the other.** A bidirectional rail would need two latches
(one per possible "last-in" end) or a single centred latch with more complex kinematics, roughly
doubling the flex-fatigue-prone parts for a benefit (choosing which end of the case faces which way
on a wall/truss) that the user has not asked for. Recorded as `PLAN-ASSUMPTION-2` — reversible later
if the user wants cable-side flexibility on the TV mount.

---

## 1. Interface spec

### 1.1 New file: `lib/mcc/bracket.scad` (L1 — geometry provider, sibling to `neutrik.scad`/
`fasteners.scad`, never an L2 peer)

Why L1, not L2: this file is **not** part of the case's own shell composition (it is never `use`d by
`shell.scad`), so the "L2 peers never `use` each other" rule doesn't apply to it. It *is* exactly the
"shared source of truth" pattern `layout.scad`'s `mcc_panel_fixing_pos()` already establishes
(deviation D6 precedent, `architecture.md` §5 rev 5): both `mounts.scad` (female cut, case-side) and
every `models/brackets/*.scad` (male rail, bracket-side) `use` this **one** file so the two profiles
can never drift apart. Register it in the barrel: add `use <bracket.scad>` to `lib/mcc/mcc.scad`
right after `use <fasteners.scad>`.

Modules/functions to add, `mcc_` prefixed, named-args only, `$fn = 64`/`circum = true` on any bore a
real part must pass (per `openscad-authoring` skill):

- `module mcc_rail_male(len = MCC_RAIL_LEN)` — **ADDITIVE.** The male dovetail rail plus its
  integrated end-stop and latch tab. Local frame: base (root, where it meets the bracket plate) at
  local `z = 0`, rising to `z = MCC_RAIL_SILL_H` (defined below); centred on local `(x=0, y=0)`;
  long axis = local X, spanning `[-len/2, +len/2]`.
- `module mcc_rail_female_cut(len = MCC_RAIL_LEN)` — **SUBTRACTIVE.** The matching groove (dovetail
  negative, sized `MCC_RAIL_CLR` per side larger than the male's nominal profile — reuse
  `MCC_CLR_SLIDE`, `constants.scad:44`, do not add a new clearance constant), plus the latch-detent
  pocket and the thumb-access through-slot. Local frame: open face at local `z = 0` (mates with
  `_mcc_floor_boss_from_below()`'s own "base at world Z=0, exterior floor face" convention already
  used throughout `mounts.scad`), extending into `+z` by `MCC_RAIL_DEPTH + margin`. Same X/Y
  footprint convention as `mcc_rail_male()` so a caller can place both with the same `translate()`.
- `function mcc_rail_sill_size() = [MCC_RAIL_LEN, MCC_RAIL_ROOT_W, MCC_RAIL_SILL_H]` — pure, for
  `mcc_floor_keepout()`/BOM/preview use.

**Cross-section (dovetail).** Fixed interface standard — **not** derived per-SKU from
`mcc_case_layout()`, because the same two brackets must mate every one of the 8 cases. New constants
in `constants.scad`, new section "Mount rail (dovetail + spring-lip latch) — issues #25/#26/#27,
replaces VESA":

| Constant | Value | Basis |
|---|---|---|
| `MCC_RAIL_DEPTH` | `4.0` | issue #25's own cap ("depth ≤ 4 mm so it does not raise the case much"). `assumed`. |
| `MCC_RAIL_SILL_H` | `MCC_RAIL_DEPTH + 2.0` = `6.0` | derived — the floor-side solid material the groove is cut into must be taller than the groove itself (2 mm margin below the groove floor, matching `MCC_APERTURE_LIP_WEB_MIN`-style minimum-material precedent). |
| `MCC_RAIL_FLANK_ANGLE` | `60` (deg, from the floor/horizontal plane) | issue #25's own "~60°" instruction; no repo-sourced dovetail-angle figure exists — `assumed`. |
| `MCC_RAIL_MOUTH_W` | `10.0` | `assumed` — clears the ≥5 mm minimum clip width (`knowledge/components/fasteners-and-hardware.md:135`) with margin either side of the latch tab. |
| `MCC_RAIL_ROOT_W` | `MCC_RAIL_MOUTH_W + 2*MCC_RAIL_DEPTH/tan(MCC_RAIL_FLANK_ANGLE)` ≈ `14.6` | derived, not hand-typed — matches the "formulas not magic numbers" rule (`architecture.md` §3). |
| `MCC_RAIL_LEN` | `150.0` | `assumed` — fixed across every SKU. Verified below to fit the smallest case (compact, `L = 194.9`) with margin; the Plus family (`L = 211.5`) then has *more* margin automatically. |
| `MCC_RAIL_Y` | `MCC_CASE_INSERT_KEEPOUT_D/2 + MCC_RAIL_ROOT_W/2 + 2.0` ≈ `19.3`, rounded to `20.0` | derived — offsets the rail off the case-plan centre (`y = 0`) far enough to clear the case's own (unmoved) 1/4"-20 floor-insert keep-out disc by the repo's standard ≥2.0 mm floor-feature separation margin (`MCC_FLOOR_FEATURE_MIN_SEP`'s own 2.0 mm minimum, not its 15 mm centre-to-centre figure, since a disc-vs-rect check is being done, not two discs — see §1.4). |
| `MCC_RAIL_CLR` | reuse `MCC_CLR_SLIDE` (`0.3`) | no new clearance constant — `constants.scad:44`. |
| `MCC_RAIL_LATCH_ARM_L` | `14.0` | `assumed` — matches `T_L = 14` already used in `tg-ladder.scad` for a similar flexure feature, and clears the L/t ≥ 8:1 rule below. |
| `MCC_RAIL_LATCH_ARM_T` | `1.6` | `assumed` — matches `MCC_TG_W`'s existing 1.6 mm feature-thickness precedent; `L/t = 8.75` ≥ 8:1 (`fasteners-and-hardware.md:133`). |
| `MCC_RAIL_LATCH_ROOT_FILLET` | `0.5 * MCC_RAIL_LATCH_ARM_T` = `0.8` | derived — `fasteners-and-hardware.md:134` "≥ 0.5× base thickness". |
| `MCC_RAIL_LATCH_ENGAGE` | `2.0` | `fasteners-and-hardware.md:136` "≥ ~2 mm for a secure catch". |
| `MCC_RAIL_LATCH_W` | `6.0` | `assumed` — clears the ≥5 mm minimum clip width (`fasteners-and-hardware.md:135`). |
| `MCC_RAIL_LATCH_X` | `-MCC_RAIL_LEN/2 + 20.0` | `assumed` — 20 mm lead-in from the open (insertion) end before the detent, so the case self-aligns on the dovetail before the latch has to do any work. |
| `MCC_RAIL_ACCESS_W`, `MCC_RAIL_ACCESS_L` | `10.0`, `14.0` | `assumed` — fingertip/thin-tool clearance for the thumb-release cutout, centred at `MCC_RAIL_LATCH_X`. |
| `MCC_RAIL_END_STOP_H` | `2.0` | `assumed` — shoulder rise at the `+X` end of the male rail that the case's groove end physically hits, capping over-travel. |

**Latch flex direction — the one non-obvious call.** The bracket plate prints flat (rail as a
vertical rib on its top face). Per `fasteners-and-hardware.md:137`, "orient the flexing arm so
bending occurs parallel to layer lines, not across them." Since the plate's layers stack in Z, a lip
that pops up/down (flexing in Z) crosses layer lines — the weak FDM axis. **The latch tab must
instead be cut into one flank of the dovetail rail and cantilever along X, flexing sideways in Y**
(within a single printed layer's plane — the strong axis). Concretely: `mcc_rail_male()`'s latch tab
is a `MCC_RAIL_LATCH_W`-wide, `MCC_RAIL_LATCH_ARM_L`-long tongue springing inward/outward in Y from
one flank of the dovetail near `MCC_RAIL_LATCH_X`, with a small nub (`MCC_RAIL_LATCH_ENGAGE`
protrusion) that springs into a matching Y-direction notch cut into the female groove's flank
(`mcc_rail_female_cut()`) at the same X position. The thumb-access cutout sits directly above the
latch tab in the case's floor (through the groove's flank) so a fingertip can press the tab back
flush (in −Y) to release while sliding the case off along −X.

**Retention force target.** No sourced figure exists for this exact interface. Target: the latch
must resist **≥ 30 N (≈3 kgf) of axial pull** before disengaging — roughly 5× an estimated <1 kg
assembled case+device weight, giving margin against vibration/incidental knocks without making
thumb-release stiff. `assumed`, marked explicitly for the rail-latch coupon (§2) to verify/tune with
a simple pull-test (luggage scale through a temporary loop), the same way `MCC_CLR_TG`/`MCC_CLR_SLIDE`
are calibrated today.

### 1.2 `lib/mcc/mounts.scad` changes — VESA removed, rail added, floor rule unchanged (mounts.scad
stays the single owner of every case-floor feature)

- **Delete** `_mcc_vesa_positions()` entirely.
- In `mcc_floor_features_add(dev, cfg)`: delete the whole `if (vesa_on) { ... }` VESA block. Add a
  new optional `cfg["rail"]` flag (bool, default `true`, mirroring the old `"vesa"` flag's contract —
  `is_undef(...) ? true : ...`). When on, ADD a rectangular solid "sill" —
  `MCC_RAIL_LEN × MCC_RAIL_ROOT_W × MCC_RAIL_SILL_H` — rising from world `z = 0` at
  `(0, MCC_RAIL_Y)`, using the same "base at world Z=0, rising to Z=h" convention as
  `_mcc_floor_boss_from_below()` (add a private `_mcc_rail_sill_from_below(len, w, h)` helper mirroring
  that module's own doc comment verbatim — same non-manifold-avoidance reasoning: this is a plain
  ADDITIVE cuboid with no local bore, the bore/groove is cut separately in the OUTER `difference()`
  by a new module below, for the exact reason `_mcc_floor_boss_from_below()`'s own comment already
  documents (a bore cut only against the sill's own local geometry gets silently backfilled by the
  overlapping, un-bored floor slab).
- **Add** `module mcc_rail_features_cut(dev, cfg)` (new — do not overload `mcc_floor_bore_cut()`,
  which stays scoped to plain circular bores): SUBTRACTIVE. When `cfg["rail"]` is on, calls
  `mcc_rail_female_cut(len = MCC_RAIL_LEN)` (from `bracket.scad`) translated to `(0, MCC_RAIL_Y, 0)`.
  Called from `shell.scad`'s OUTER `difference()`, immediately after the existing
  `mcc_floor_bore_cut(dev, cfg)` call (`shell.scad:428`), for the identical non-manifold reason.
- `mcc_floor_features_cut()` is otherwise **unchanged** (strap slots, splitter tie-down, stacking
  recess all stay as-is — none of them overlaps the new rail band, see §1.4).
- Update the file's own header doc comment (currently lists "VESA 75x75 blind M4 heat-set-insert
  bosses ..." — replace with "the tool-less mount rail (dovetail + spring-lip latch, issues
  #25/#26/#27, replaces VESA)").

### 1.3 `lib/mcc/layout.scad` — `mcc_floor_keepout()` changes

- In `mcc_floor_keepout(dev, cfg)`: **delete** the 4 `vesa_ne`/`vesa_se`/`vesa_nw`/`vesa_sw` circle
  rows. **Rename** the local `vesa_pos` variable to `floor_center` (it is still used by the case
  1/4"-20 insert row and the Fishtail reservation row, both unaffected by this change — keep both
  rows as-is, just at the renamed variable). **Add** one new row:
  `[0, MCC_RAIL_Y, "rect", [MCC_RAIL_LEN, MCC_RAIL_ROOT_W], "mount_rail"]`.
- `mcc_case_layout()` itself needs no change (the rail is a fixed-constant floor feature, not derived
  from the per-SKU envelope).

### 1.4 Keep-out verification (why `MCC_RAIL_Y = 20.0` is safe on every SKU)

Worked for the **smallest** family (compact, `W = 159.85`, the tighter case — Plus has strictly more
margin everywhere below):

- **Case 1/4"-20 insert** (`⌀20` keep-out at `(0,0)`): rail inner edge at `y = 20 - 14.6/2 = 12.7`;
  insert edge at `y = 10`. Clearance `2.7 mm ≥ 2.0 mm` ✓.
- **Fishtail reservation** (`60×20` band centred at `(0,0)`, i.e. `y ∈ [-10, 10]`): same `2.7 mm`
  clearance as above ✓ (same edge).
- **Device footprint** (compact: `y ∈ [-60.925, -0.725]`; Plus: `y ∈ [-64.175, 2.525]`): rail band
  `y ∈ [12.7, 27.3]` is clear of both by ≥ 10 mm ✓. (The rail does not need daylight through the
  device anyway — like the old VESA bosses, it only needs to reach `z ≤ MCC_RAIL_SILL_H` into the
  floor/deck stack, well under `z_dev_lo ≈ 13.8–13.85`, so plan-view overlap with the device would
  have been harmless even if it occurred — it doesn't.)
- **Strap slots** (`y = ±(W/2 - 12) = ±67.925`): far outside the rail band ✓.
- **Splitter tie-down / bay** (`y ∈ [-76.925, -1.925]`, `x`-restricted to the −X end): no Y-overlap
  with the rail band (`[12.7, 27.3]`) regardless of X ✓.
- **Side-bolt support-web floor footprint** (`y ∈ [-76.925, -62.925]`): no overlap ✓.
- **Cradle far/patch-flank ribs**: all start at `z = z_dev_lo ≈ 13.8`, entirely above the rail's
  `z ∈ [0, 6]` range — no Z-overlap regardless of XY ✓.
- **Stacking-profile corner recesses** (at the 4 lid-fastener corners, `y = ±(W/2-10) = ±69.925`):
  far outside the rail band ✓.
- **Rail X-extent** (`MCC_RAIL_LEN = 150` centred at `x=0`, i.e. `x ∈ [-75, 75]`) vs. the usable floor
  span on compact (`L = 194.9`, interior `x ∈ [-94.45, 94.45]`): **19.45 mm margin per end** past the
  end walls' inner faces, comfortably clear of the panel-frame band and every end-zone feature ✓.

Developer must still add the standard pairwise-non-overlap assert for the new `"mount_rail"` row in
`mcc_floor_keepout()`'s consumer (`mounts.scad`) alongside the others — deviation **D16** already on
record (`layout-patch-wall.md` §16.4: `mounts.scad` never actually asserts this pairwise check today,
`MCC_FLOOR_FEATURE_MIN_SEP` is unused) — **fix D16 as part of this work** (add the assert loop over
`mcc_floor_keepout()`'s own list) rather than adding a 6th floor feature that is *also* unchecked.

### 1.5 Asserts to add (Tier-1, in-model)

- **Rail-in-floor assert** (`mcc_rail_features_cut()` or `bracket.scad`'s own module): `MCC_RAIL_LEN`
  fits within the usable floor X-span for `dev`/`cfg` — i.e.
  `MCC_RAIL_LEN <= L - 2*MCC_WALL - 2*MCC_PANEL_FRAME_MIN` (reuse the panel-frame-band figure as the
  conservative bound, since it's already `L`'s tightest documented interior margin) — fails loudly if
  a future SKU is smaller than compact.
- **Floor non-overlap assert** (fixes D16, §1.4 above): loop `mcc_floor_keepout(dev,cfg)`, pairwise
  check every two rows for overlap (circle-circle, circle-rect, rect-rect as appropriate — reuse
  `MCC_FLOOR_FEATURE_MIN_SEP` for the point-like features, a plain AABB-overlap test for rect-rect)
  and assert none overlap. This one assert now covers the rail row too.
- **Latch stress rule** (in `mcc_rail_male()`): assert `MCC_RAIL_LATCH_ARM_L / MCC_RAIL_LATCH_ARM_T >= 8`
  and `MCC_RAIL_LATCH_ROOT_FILLET >= 0.5 * MCC_RAIL_LATCH_ARM_T` directly from the constants, so a
  future edit to either constant fails at render instead of silently violating the snap-fit rule.
- **Sill-depth assert**: `MCC_RAIL_SILL_H > MCC_RAIL_DEPTH` (the groove must not punch through the
  sill's own base).

---

## 2. Coupon: `models/coupons/rail-latch.scad`

New Tier-4 physical coupon (style: `models/coupons/side-bolt.scad`/`tg-ladder.scad`). A short rail +
matching groove pair, printed as **two separate parts** (like `side-bolt.scad`'s wall-slab pattern),
so the real fit/retention can be pull-tested before any full case or bracket is printed.

- `part = "rail-latch"` reserved for `-D part=`, matching every other coupon's own convention (see
  `side-bolt.scad:29`'s comment on why `part` is reserved).
- Part A: a `~60 × 40 × MCC_RAIL_SILL_H` base plinth with `mcc_rail_female_cut()` at half length
  (`len = 60`, well under `MCC_RAIL_LEN` — this is a fit/retention test, not a full-length print),
  standing in for the case floor.
- Part B: a matching flat plate with `mcc_rail_male(len = 60)` standing in for the bracket.
- `-D format=both` (via `build.py render coupons/rail-latch --format both`) so both an `.stl` (mesh
  checks/golden) and `.3mf` (Bambu Studio) come out.
- `echo()` the same style summary block `side-bolt.scad:74-82` uses (every rail constant, so the
  print log records exactly what was tested).
- Add to `models/coupons/README.md`'s table: "Verifies the dovetail slides freely, the latch clicks
  and holds ≥ `MCC_RAIL_LATCH_...` retention (pull-test with a luggage scale), and thumb-release
  disengages it cleanly | calibrates `MCC_RAIL_CLR` (cross-check against `MCC_CLR_SLIDE`),
  `MCC_RAIL_LATCH_ENGAGE`, the 30 N retention target".

This coupon is registered automatically — `discover_coupons()` globs `models/coupons/*.scad`, one
target per file, no code change needed for it specifically (unlike the brackets, §3/§4/§5).

---

## 3. TV bracket: `models/brackets/tv-bracket.scad`

New directory `models/brackets/` (sibling to `models/coupons/` and `models/<slug>/`).

### 3.1 Geometry

- Flat plate, `230 × 230 × 6.0 mm` (assumed — fits the ticket's own `≤ 244 mm` cap with margin;
  contains the VESA 200×200 pattern with generous edge margin; single-plate print, well under the
  256 mm bed). Prints face-down.
- **VESA through-holes** — 8 plain round clearance holes, both patterns sharing the plate's own
  centre (standard VESA convention — 200×200 is concentric with 100×100):
  - 4× at `(±50, ±50)` mm, `⌀MCC_M4_CLR_D` (existing constant, `4.5 mm`, `constants.scad:141`) — VESA
    MIS-D 100×100, M4. [VESA MIS-D spec via Wikipedia](https://en.wikipedia.org/wiki/VESA_mount).
  - 4× at `(±100, ±100)` mm, `⌀MCC_M8_CLR_D` (new constant, `9.0 mm`, `assumed` — ISO-medium M8
    clearance, generous enough to also pass an M6 screw) — VESA MIS-F 200×200, M6/M8.
    [VESA MIS-F spec via Wikipedia](https://en.wikipedia.org/wiki/VESA_mount);
    [Alibaba VESA screw-size guide](https://electronics.alibaba.com/question/monitor-bracket-screws-size,-vesa-fit-installation-guide)
    corroborates M6×15/M8×16 for 200×200+.
  - These are **through-clearance holes, not threaded** — the bracket sandwiches between the TV and
    the user's existing wall/stand mount, so the *same* screws that normally go TV→mount now go
    TV→(through this plate)→mount, clamping the plate captive. No new fasteners are added to the BOM
    for the VESA side; the user's own mount screws must simply be long enough to also clear the
    plate's `6.0 mm` thickness — call this out explicitly in the BOM row (§3.3).
- **Stiffening ribs** on the back (non-rail) face: a cross pattern, `MCC_WALL`-thick (3 mm, `≤ 0.6×`
  the 6 mm plate — `fdm-rugged-enclosure-guidelines.md:65-70`), height `≤ 9 mm` (`3×` thickness, same
  rule).
- **Rail**: `mcc_rail_male()` centred on the plate's front (TV-facing... see orientation below) face,
  long axis horizontal (plate-X, matching the case's own length axis once mated).
- **Orientation requirement (acceptance criterion, not a hand-derived rotate() call):** when the
  bracket is wall-mounted normally (VESA square upright) and the case is slid onto the rail, **the
  case's patch (cable) wall must hang facing down**, and neither the fan aperture nor the vent bands
  may be pressed against the TV back (per issue #26's own requirement). Since the case's floor always
  faces the bracket (the dovetail only mates in one roll — see §0), this is fixed entirely by how
  `mcc_rail_male()` is placed in `tv-bracket.scad`'s own local frame, not by any runtime choice. The
  developer must add a `part == "assembly"` preview branch to `tv-bracket.scad` (mirroring
  `models/pro-convert-for-ndi-to-hdmi/case.scad`'s own `"assembly"` branch, `case.scad:112-124`) that
  places a ghost case (any one device record is fine — reuse `MCC_DEV_PRO_CONVERT_FOR_NDI_TO_HDMI`)
  mated onto the rail, and **visually verify in that preview that the patch wall faces down** before
  finalizing the rotate(). This is the concrete, checkable substitute for hand-deriving a
  rotation-matrix sign that a Sonnet-tier pass could otherwise get backwards silently.

### 3.2 Discovery (build.py change — required, not optional)

`scripts/build.py`'s `discover_models()` only globs `models/*/case.scad` (one file per directory,
named exactly `case.scad`) — it will **not** find `models/brackets/tv-bracket.scad` or
`truss-bracket.scad`. Do **not** force these into that mechanism (they have no base/lid split, no
device, no variant config — they are single-part flat plates, structurally identical in shape to a
coupon target, not a case). **Add a new discovery function mirroring `discover_coupons()` exactly:**

```python
BRACKETS_DIR = MODELS_DIR / "brackets"

def discover_brackets() -> list[Target]:
    if not BRACKETS_DIR.is_dir():
        return []
    targets = []
    for scad_path in sorted(BRACKETS_DIR.glob("*.scad")):
        stem = scad_path.stem
        targets.append(Target(name=f"brackets/{stem}", scad_path=scad_path, parts=[stem], kind="bracket"))
    return targets
```

- Register it in `discover_all()`: `return discover_coupons() + discover_brackets() + discover_models()`.
- No `-D part=` switching needed inside `tv-bracket.scad`/`truss-bracket.scad` for their *exported*
  part (same as every coupon) — but each file still needs its own **internal** `part` variable
  reserved and set to its own stem (`part = "tv-bracket";` / `part = "truss-bracket";`), exactly per
  `side-bolt.scad:26-29`'s documented convention, so nothing collides if `build.py` ever passes
  `-D part=...` generically. The optional `part == "assembly"` preview branch from §3.1 is invisible
  to `build.py` by construction (same mechanism `case.scad`'s own `"assembly"` branch already relies
  on — `build.py` never asks for that part name).
- Golden path follows the existing naming rule (`tests/golden/README.md`): target `brackets/tv-bracket`,
  part `tv-bracket` → `tests/golden/brackets/tv-bracket.json` (part name equals target basename, same
  rule as `coupons/neutrik-tile`).
- `models/brackets/README.md` — add a short file mirroring `models/coupons/README.md`'s table format,
  documenting what each bracket verifies/calibrates.

### 3.3 BOM rows (new `## Mounting brackets` section in `BOM.md`, hand-authored — `bom-update` only
regenerates the per-device sections from device port maps, brackets have no device record)

| Item | Part number | Qty | Notes | Source |
|---|---|---|---|---|
| M4 machine screw, TV's own stock length **+ 6 mm** | generic, TV-specific | 4 | Passes through the bracket's 100×100 clearance holes into the TV's VESA threads, sandwiching the plate | VESA MIS-D spec (Wikipedia, cited above) |
| M6 or M8 machine screw, existing mount's own stock length **+ 6 mm** | generic, mount-specific | 4 | Passes through the bracket's 200×200 clearance holes | VESA MIS-F spec (Wikipedia, cited above) |
| M6/M8 spacer/standoff washers, 6 mm | generic | 0–8 (situational) | Only if the user's existing mount's screws are not already long enough for the extra 6 mm plate thickness | `assumed` — stock-length dependent, flag for the user to check before ordering |

---

## 4. Truss bracket: `models/brackets/truss-bracket.scad`

### 4.1 Half-coupler research (cited, `assumed` where the footprint bolt pattern itself is
unpublished)

- Standard **50 mm half coupler**: high-tensile aluminium extrusion, fits **48–51 mm** tube, **50 mm**
  wide, slotted for a captive **M12** nut/bolt, WLL **750 kg**, ~0.63 kg.
  [Doughty 50mm Half Coupler — Showtools](https://www.showtools.com.au/product/the-doughty-50mm-half-coupler-swl750kg-tube-diameters-48-to-51mm-fixings-m12-hole/);
  [Doughty T57010 — Stage Electrics](https://www.stage-electrics.co.uk/View/21253/doughty-t57010-aluminium-50mm-half-coupler-m12-hole-black).
- **Lightweight** variant: same 48–51 mm tube range, 50 mm wide, **M10 or M12**, WLL **500 kg**.
  [Doughty Lightweight Half Coupler](https://doughty-usa.com/products/lightweight-half-coupler/).
- A comparable half-coupler product (M10 fixing) lists an overall footprint of **~98 × 81 × 30 mm**
  (L × W × depth) — [Full Compass / Global Truss half-coupler search result]. **This is the closest
  sourced footprint figure found; it is not the specific Doughty product's own datasheet dimension
  (Doughty's own product pages did not publish plate dimensions when fetched) — mark `assumed`.**
- **Decision: standardize on M12** (the more universal bolt across the standard/heavy-duty product
  lines cited above; M10 is only offered on the "lightweight" variant) — new constant
  `MCC_TRUSS_BOLT_CLR_D = 13.5` mm (`assumed`, generic M12 ISO-medium clearance, `constants.scad`
  section "Truss half-coupler (issue #27)").
- **Gap, explicitly not invented:** the half-coupler's own **mounting-flange bolt pattern** (how its
  flat face attaches to an external plate, as opposed to the tube-clamping bolt) is **`unknown`** —
  no fetched source gave it. **Do not guess a hole pattern.** Design `truss-bracket.scad` with a
  clearly-named placeholder constant `MCC_TRUSS_MOUNT_PATTERN = [40, 40]` (a 4× M8-clearance square
  pattern, `assumed`, explicit `TODO` comment: "replace once the physical half-coupler is bought and
  measured — same Tier-4 'coupons before cases' rule the PoE splitter's own envelope followed,
  `constants.scad` `MCC_SPLITTERS` comment"), so the plate is buildable and testable today without
  fabricating a false-confidence number.

### 4.2 Geometry

- Flat plate sized to the placeholder coupler footprint + margin: `~150 × 120 × 8.0 mm` (`assumed`
  — thicker than the TV bracket, 8 mm, since this plate cantilevers the full case+device weight off
  a horizontal tube rather than lying flat against a wall).
- 4× `⌀MCC_M8_CLR_D` clearance holes at `MCC_TRUSS_MOUNT_PATTERN` for the coupler's own flange (per
  the `TODO` above).
- `mcc_rail_male()`, same orientation-verification requirement as §3.1 (a `part == "assembly"`
  preview branch, patch wall must hang accessible, vents/fan clear).
- **Safety-cable eye**: a reinforced boss with a `⌀8–10 mm` through-hole (`assumed`, scaled to match
  the M8 truss bolt already in use) for a standard rigging safety cable's shackle/carabiner. **Do not
  claim a load rating for this printed feature** — it is a routing/pass-through loop, not the rated
  fall-arrest element; the safety cable's own certified hardware (purchased, not printed) is what
  carries the rigging-code load. State this explicitly in the file's header comment so a future
  reader does not silently assume the print itself is rigging-certified.
- **Load path argument (< 1 kg + drop factor):** the coupler + M12 bolt is rated 500–750 kg WLL — many
  orders of magnitude past a <1 kg case+device. The bracket plate's own bending/shear path (coupler
  flange → plate → rail sill) is the weaker link, sized at 8 mm ASA with the same "uniform wall + ribs
  over thickening" principle as the rest of this repo (`fdm-rugged-enclosure-guidelines.md` §
  "why not just thicken the wall", cited in `mounts.scad`'s own design precedent) — add crossed ribs
  identical in spirit to §3.1's TV bracket. No FEA is attempted; the coupon (§2) plus a physical pull
  test stand in for it, per this repo's existing Tier-4 philosophy.

### 4.3 BOM rows (same new `## Mounting brackets` BOM.md section as §3.3)

| Item | Part number | Qty | Notes | Source |
|---|---|---|---|---|
| 50 mm half coupler, M12 | Doughty T57010 or equivalent (Global Truss/generic 48–51 mm, M12) | 1 | Clamps to a 48–51 mm truss tube | Showtools/Stage Electrics listings, cited §4.1 |
| M12 bolt/nut (captive in the coupler) | generic, coupler-specific | 1 | Ships with most half-couplers — confirm when purchased | `assumed` |
| M8 machine screw, `assumed` length | generic | 4 | Through `MCC_TRUSS_MOUNT_PATTERN` into the coupler's own flange — **length depends on the actual coupler once measured (§4.1 gap)** | `assumed` |
| Rigging safety cable + shackle/carabiner, rated | generic, rigging-certified | 1 | Independent secondary fall-restraint — **not** the printed eye's own rated strength; buy a certified rigging safety cable, do not substitute a generic cable tie | industry-standard rigging practice, no single-source citation — flag for user sourcing |

---

## 5. Layering/ownership summary

| Feature | Owner file | Layer | Notes |
|---|---|---|---|
| Rail cross-section geometry (male + female + keep-out size) | `lib/mcc/bracket.scad` (new) | L1 | Shared source of truth, `use`d by both `mounts.scad` and every `models/brackets/*.scad` — same pattern as `mcc_panel_fixing_pos()` (D6 precedent). |
| Female groove cut in the case floor | `lib/mcc/mounts.scad` | L2 | Stays the single floor-feature owner (`architecture.md` §6). Calls into `bracket.scad`, does not duplicate its geometry. |
| Floor keep-out registration (`"mount_rail"` row) | `lib/mcc/layout.scad`, `mcc_floor_keepout()` | L1 | Pure function, no geometry — unchanged pattern. |
| Male rail placement on each bracket | `models/brackets/tv-bracket.scad`, `truss-bracket.scad` (new) | thin assembly (bracket-equivalent of L4) | Each `use`s `bracket.scad` via the barrel; owns only its own plate/holes/ribs/eye. |
| Pairwise floor non-overlap assert | `lib/mcc/mounts.scad` | L2 | Fixes deviation D16 as part of this work (§1.4). |
| `cfg["rail"]` flag plumbing | `models/*/case.scad` (all 8) | L4 | Mechanical: delete the old `"vesa"` flag; `"rail"` needs no explicit per-file line (mounts.scad defaults it `true`, same convention `fan_y` already uses without being set everywhere). |

**VESA removal — files touched (all 8 `models/*/case.scad`, mechanical edit, identical in each):**
delete the `vesa = true;`/`vesa = false;` variable declaration, its doc-comment bullet describing the
`"vesa"` cfg key, and the `["vesa", vesa]` entry in the `variant` assoc-list. Files:
`models/pro-convert-for-ndi-to-aio/case.scad`, `-for-ndi-to-hdmi/case.scad`,
`-for-ndi-to-hdmi-4k/case.scad`, `-for-ndi-to-sdi/case.scad`, `-hdmi-plus/case.scad`,
`-hdmi-tx/case.scad`, `-sdi-plus/case.scad`, `-sdi-tx/case.scad`.

**Constants removed** (now dead once VESA's callers are gone): `MCC_VESA75_PITCH`, `MCC_VESA_HOLE_D`
(`constants.scad`). **Keep** `MCC_CASE_INSERT_KEEPOUT_D` (still used by the unchanged tripod insert)
and `MCC_FISHTAIL_BAND` (unchanged reservation, still valid at the renamed `floor_center`).

**BOM.md edits:** delete the VESA row in the "Case floor mounting" common-hardware section
(`BOM.md:65`) and the "`vesa = true` ... VESA 75×75 M4 floor bosses are present" note
(`BOM.md:262-263`); add the new `## Mounting brackets` section (§3.3 + §4.3 tables) — this is a
hand-authored addition, not something `bom-update`'s device-driven regeneration will produce, so note
in that skill's own file (or a follow-up) that brackets are out of its current scope.

**Tests/goldens impact:** every one of the 8 SKUs' `base` golden changes (VESA bosses gone, rail
groove added) — justified per `tests/golden/README.md`'s own rule ("justify golden changes in the
PR"), cite this plan. Two new golden files: `tests/golden/brackets/tv-bracket.json`,
`tests/golden/brackets/truss-bracket.json`. One new smoke test (`tests/test_bracket.scad`,
instantiate `mcc_rail_male()`/`mcc_rail_female_cut()` at default parameters, per `architecture.md` §9
Tier 2 "instantiate every public module at its default, minimum, maximum parameters").

---

## 6. Ordered implementation steps

1. **Pre-flight (single branch, before any of #25/#26/#27 diverges):** none needed — unlike the
   seven-SKU fan-out (`layout-patch-wall.md` §16.5), this is one feature landing once. Branch:
   `feature/issue-25-mount-rail` for #25's library work; #26/#27 can branch off `main` once #25 merges
   (they depend on `bracket.scad` existing), or off #25's branch if working concurrently — confirm
   with `git-flow` skill before opening branches.
2. Add the new constants section to `lib/mcc/constants.scad` (§1.1 table + §4.1's
   `MCC_TRUSS_BOLT_CLR_D`/`MCC_TRUSS_MOUNT_PATTERN` + `MCC_M8_CLR_D`). Delete `MCC_VESA75_PITCH`,
   `MCC_VESA_HOLE_D`.
3. Create `lib/mcc/bracket.scad` (§1.1): `mcc_rail_male()`, `mcc_rail_female_cut()`,
   `mcc_rail_sill_size()`, plus the latch-stress assert (§1.5). Register in `lib/mcc/mcc.scad`'s
   barrel.
4. Edit `lib/mcc/layout.scad`'s `mcc_floor_keepout()` (§1.3): delete the 4 VESA rows, rename
   `vesa_pos` → `floor_center`, add the `"mount_rail"` row.
5. Edit `lib/mcc/mounts.scad` (§1.2): delete `_mcc_vesa_positions()` and the VESA branch in
   `mcc_floor_features_add()`; add the rail-sill add (`cfg["rail"]` flag) and the new
   `mcc_rail_features_cut(dev, cfg)` module; add the pairwise floor non-overlap assert (fixes D16,
   §1.5).
6. Edit `lib/mcc/shell.scad`: add `mcc_rail_features_cut(dev, cfg);` in the OUTER `difference()`
   right after the existing `mcc_floor_bore_cut(dev, cfg);` call (`shell.scad:428`).
7. Edit all 8 `models/*/case.scad` (§5): delete the `"vesa"` cfg plumbing.
8. Render/check every SKU: `python scripts/build.py render --all && python scripts/build.py check --all`.
   Confirm the §1.4 keep-out math holds in practice (no assert failures) on all 8, not just the
   compact-family hand-check above.
9. Update goldens for all 8 SKUs' `base` part: `python scripts/build.py golden --update <slug>` for
   each (or `--update` with no target — confirm the flag's exact scope in `build.py`'s own `--help`
   first). Review each diff before committing (bbox/volume should move by roughly the VESA-bosses-out,
   rail-in delta, nothing else).
10. Add `scripts/build.py`'s `discover_brackets()` (§3.2) + register in `discover_all()`.
11. Create `models/brackets/rail-latch.scad`... **note:** the coupon lives in `models/coupons/`, not
    `models/brackets/` — create `models/coupons/rail-latch.scad` (§2). Update
    `models/coupons/README.md`'s table.
12. Create `models/brackets/tv-bracket.scad` (§3) with its `part == "assembly"` preview branch.
    Render the preview, screenshot/inspect it (per `run` skill or direct OpenSCAD GUI), confirm patch
    wall hangs down and vents/fan are clear before finalizing the rail rotate().
13. Create `models/brackets/truss-bracket.scad` (§4), same preview-and-verify step.
14. `python scripts/build.py render --all && check --all && golden` — now covers coupons + brackets +
    models. Add the new goldens (`golden --update brackets/tv-bracket`, `brackets/truss-bracket`,
    `coupons/rail-latch`).
15. Add `tests/test_bracket.scad` smoke test (§5).
16. Update `BOM.md`: delete the two VESA references (§5), add `## Mounting brackets` (§3.3 + §4.3).
17. Update `.claude/knowledge/architecture.md` (§6 floor rule paragraph — VESA reference becomes the
    rail; §3 layer diagram gains `bracket.scad` at L1) and `.claude/knowledge/decision-log.md` (record
    the female-in-floor/male-on-bracket decision, the `MCC_RAIL_Y` offset derivation, the
    single-direction-insertion decision, the truss mounting-pattern gap) — architect's call on exact
    wording, but the facts must land somewhere durable per this repo's "never silently absorb a
    deviation" rule.
18. `python scripts/build.py all` (full gate) before opening the PR(s). CI must be green
    (`CLAUDE.md` "A PR into `main` must be CI-green").

---

## 7. `PLAN-ASSUMPTION` list for the architect

1. **Safety framing (truss bracket).** The dovetail+latch is explicitly *not* claimed as the sole
   overhead fall-restraint; the safety-cable eye is a routing/pass-through feature, not a rated
   load path, and the actual rated hardware is purchased, not printed. Confirm this framing is
   acceptable before any truss-mounted use is signed off — this is a real safety judgement call, not
   a geometry detail.
2. **Single insertion direction (not bidirectional).** The rail has one open/latch end and one
   end-stop end. If the user wants to choose which end of the case (cable side vs. fan side) faces
   which way when wall/truss-mounted, this plan does not provide it — flag for a user decision, not a
   silent default.
3. **`MCC_RAIL_Y = 20.0` offset** moves the rail off the case's plan centre rather than relocating the
   existing 1/4"-20 floor insert. Confirm this is preferred over dropping/relocating that insert (the
   ticket explicitly permits dropping it if it conflicts — it does not conflict under this design, but
   the trade-off was made without user input).
4. **Truss half-coupler mounting-flange bolt pattern is `unknown`.** `MCC_TRUSS_MOUNT_PATTERN` is a
   placeholder (4× M8, 40×40 mm) pending the physical part being bought and measured — same status as
   `MCC_SPLITTERS`' own unmeasured envelope. Do not print the truss bracket for real use before this
   is replaced with a measured value.
5. **Retention force target (30 N / 3 kgf) is `assumed`**, not derived from any load calculation or
   sourced spec — it is a starting point for the rail-latch coupon's own pull-test, per this repo's
   existing "print the coupon, measure, update the constant" Tier-4 philosophy. Not a certified
   engineering figure.
6. **Bracket plate thicknesses (TV 6 mm, truss 8 mm) are `assumed`**, sized by analogy to this repo's
   existing wall-thickness/rib conventions, not by a structural calculation specific to a wall- or
   truss-mounted cantilever load. Flag if the architect wants a more rigorous sizing pass before the
   first physical print.
7. **VESA is fully removed, not deprecated-but-kept-optional.** The `cfg["rail"]` flag exists (mirrors
   the old `"vesa"` flag's off-switch convenience) but there is no code path left that reinstates the
   VESA 75×75 pattern. If any user still wants VESA 75×75 as a *third*, independent floor option
   (in addition to the rail), that is new scope, not covered here — flag rather than assume "replaces"
   meant "replaces only by default."
