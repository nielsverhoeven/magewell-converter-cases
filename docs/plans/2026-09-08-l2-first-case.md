# Implementation plan — first full case: Pro Convert for NDI to HDMI

Status: **IMPLEMENTED, 2026-09-08.** `python scripts/build.py all` is green (smoke 7/7, render 9/9,
check 11/11, golden all-pass). All 8 PLAN-ASSUMPTIONs below were superseded by the
solution-architect's rev-5 L2 gate rulings (`layout-patch-wall.md` §15) BEFORE implementation started
— the code was written directly against those rulings, not against this plan's own original numbers.
See the bottom of this status block for what changed during implementation itself (as opposed to
during the architect's gate) and for the open items carried forward.

No GitHub issue exists for this task (`gh issue list` empty, repo has no open issues); per
`.claude/knowledge/ticket-source.md` this plan lives at `docs/plans/2026-09-08-l2-first-case.md`
instead of a ticket comment. Target branch per `.claude/knowledge/ticket-source.md`/`git-flow`:
`feature/l2-first-case` off `main` (implemented directly on the session's existing
`feature/repo-setup` branch — no branch switch performed by this pass; branch hygiene is a
teamlead/git-flow decision, not made here).

Derived strictly from `.claude/knowledge/architecture.md` (rev 4) and
`.claude/knowledge/layout-patch-wall.md` (rev 3) as originally written; both files were subsequently
revised to **rev 5** by the solution-architect specifically to gate this plan
(`layout-patch-wall.md` §15, `architecture.md` §13 D5-D8) — implementation followed rev 5, not the
rev-3/4 text quoted verbatim below in §1-§7. Where those two documents are silent, self-contradict, or
leave a value unconstrained, this plan proposes the smallest reasonable choice and marks it
**PLAN-ASSUMPTION** — see §7, and see the rulings table for how each was actually resolved.

## Implementation notes (added post-hoc, 2026-09-08 — read this before the sections below)

- **§3.0 constants table below is superseded** by six rev-5 corrections: `MCC_TG_W`/`MCC_TG_H` =
  **1.6/2.0** (not 3.0/4.0 — a centred/oversized tongue does not physically fit `MCC_WALL`/`MCC_LID_T`;
  ruling 4), `MCC_VENT_INTAKE_BAND_H` = **18.0** (not 15.0; ruling 5), and `MCC_PANEL_BEZEL_T` = 3.0 was
  added as its own named constant (needed once the rabbet became stepped, §2.5). `models/coupons/
  tg-ladder.scad`'s `T_W`/`T_H` were re-cut to reference `MCC_TG_W`/`MCC_TG_H` directly (golden
  updated — an intentional geometry change, not a regression).
- **§3.2's "4 rectangular windows" aperture design is REJECTED** (ruling 2) in favour of
  `layout-patch-wall.md` §2.5's one-stepped-rabbet-plus-minimal-crown-windows design; implemented in
  `shell.scad` as `_mcc_patch_wall_rabbet()` (two-depth stepped pocket) + `_mcc_patch_wall_window()`
  (a `hull()` of the connector clearance circle and the two rear-boss relief circles — a
  self-supporting "crown" shape, not a flat-topped rectangle, satisfying T1-34).
- **§3.3's far-flank rib hand-iteration is REJECTED** (ruling 6) in favour of the deterministic
  band-minus-exclusion rule now in `layout-patch-wall.md` §7; implemented as
  `cradle.scad:_mcc_far_flank_rib_x()`, yielding the doc's own 4-rib result
  (`x = -38.95, -12.0, +19.0, +45.95`) for this SKU.
- **§3.4's splitter-tiedown workaround is REJECTED** (ruling 7): instead of hand-rolling holes in
  `mounts.scad`, `poe_splitter.scad` gained an `orient = "flat"|"edge"` parameter (plus a
  `cable_allow` toggle) on both `mcc_splitter_envelope()` and `mcc_splitter_tiedown()` — an approved
  L1 change outside this plan's original file list. `mounts.scad` calls
  `mcc_splitter_tiedown(orient="edge")` unmodified.
- **§2.3's slot order (`hdmi_out · usb_host · usb_b · rj45`) is REJECTED** (ruling 8, confirming this
  plan's own PLAN-ASSUMPTION #8 flag was correct to raise): the algorithm's actual output —
  `rj45 · usb_b · usb_host · hdmi_out` — is what `mcc_slot_for_port()` implements and what
  `tests/test_layout.scad` asserts. No device file changes; the defect was in the (now-corrected)
  doc table, not the data.
- **Two additional deviations found and fixed during implementation, beyond anything the architect's
  gate flagged:**
  1. `lib/mcc/panel.scad`'s `mcc_panel_plate()` (pre-existing, not part of this plan's file list) had
     a latent mesh-export defect — its field and rim solids share an exactly-coincident vertical
     face, which this pinned OpenSCAD 2025.09.07 / Manifold combination turns into spurious
     zero-volume mesh slivers (`check`'s `n_parts > 1`) on any multi-slot render. Fixed with a
     `MCC_EPS` footprint shrink on the field (see that file's own comment). This plan's §1.2 said "no
     change to panel.scad" — that held until this milestone's own `check --all` gate is what actually
     exercises a 4-slot plate for the first time and surfaced the bug; fixing it was necessary to
     satisfy this same plan's own verification requirement.
  2. A related but distinct Manifold defect, isolated over an extended debugging session: differencing
     a small bore cylinder from a boss whose flat end cap touches a much larger unioned solid (here,
     the patch wall) reliably produces the same class of spurious mesh sliver, and — unlike the
     VESA/tripod "boss from below" bores, which needed their bore cut split into the shell's OUTER
     `difference()` to avoid a *different* problem (backfill by an overlapping un-bored sibling) —
     this one persisted across every construction tried (self-contained vs. split cut, `render()` at
     multiple levels, setback distances from 0.01 mm to 15 mm, wall built as cube-minus-cavity vs.
     unioned slabs). **Root cause narrowed to `mcc_heat_set_bore()`'s own internal `MCC_EPS`
     height-padding**, not the small-bore-near-large-solid pattern itself — but even a hand-rolled
     equivalent cut still failed once the *same* outer `difference()` also carried the patch-wall
     rabbet cut. **Current state: the 4 patch-wall plate-fixing bosses are plain, unbored solids** — a
     reported, not silently absorbed, deviation; see `shell.scad:_mcc_patch_wall_fixing_bosses()`'s
     own comment and this task's final report for the full isolation log. Follow-up: revisit once a
     newer OpenSCAD/Manifold build is pinned, or hand-drill/tap the M3 bore during assembly in the
     interim.

Target device: `MCC_DEV_PRO_CONVERT_FOR_NDI_TO_HDMI` (`lib/mcc/devices/pro-convert-for-ndi-to-hdmi.scad`),
family `compact` (100.9 × 60.2 × 23.3 mm). Chosen as the first full case because it is the
`compact`-family, HDMI-ended, 4-slot representative already fully specified in
`layout-patch-wall.md` §8's per-SKU table.

None of `lib/mcc/shell.scad`, `cradle.scad`, `mounts.scad`, `vents.scad`, or any `models/<slug>/`
directory exists yet (verified 2026-09-08 via `find lib/mcc -type f` / `find models -type f`) — this
plan is exactly the "next milestone" `new-case-variant`'s stop-and-report gate is waiting for.

---

## 1. Scope

### 1.1 New files

| File | Layer | Purpose |
|---|---|---|
| `lib/mcc/layout.scad` | **L1 (new — PLAN-ASSUMPTION #1, §7)** | Pure functions only: case envelope (`mcc_case_dims`), device placement, slot assignment (`mcc_slot_for_port`), end zones (`mcc_end_zone`), panel-plate dims (`mcc_panel_plate_dims`), fan/splitter/side-bolt/lid-fastener positions. Single source of truth for every formula in `layout-patch-wall.md` §1–§8 so `shell.scad`/`panel.scad`(reuse)/`cradle.scad`/`mounts.scad`/`vents.scad` never re-derive `L`/`W`/`H` independently. |
| `lib/mcc/shell.scad` | L2 | `mcc_shell_base(dev, cfg)`, `mcc_shell_lid(dev, cfg)`: outer shell, tongue/groove, patch-wall aperture(s) + rabbet, fan/splitter bay reservation cuts, side-bolt boss integration, lid-fastener bosses. |
| `lib/mcc/cradle.scad` | L2 | `mcc_cradle(dev, cfg)`: deck, locating ribs, far-flank ribs (duct-clearing), pad pocket. |
| `lib/mcc/mounts.scad` | L2 | `mcc_floor_features(dev, cfg)`, `mcc_floor_keepout()`: case 1/4"-20 insert, VESA 75×75 + Fishtail M4 reservation, strap slots, splitter tie-down, stacking profile. Single owner of the floor (architecture.md §6). |
| `lib/mcc/vents.scad` | L2 | `mcc_vents(dev, cfg, face)`: chimney slot arrays (far wall + end walls only, never the patch wall), keep-out aware (side-bolt strip, splitter bay, end-zone cables). |
| `models/pro-convert-for-ndi-to-hdmi/case.scad` | L4 | Thin assembly: `part` ∈ `"base"`/`"lid"`/`"panel"`/`"assembly"`. |
| `tests/test_layout.scad` | Tier 2 | Exercises every `layout.scad` function against this SKU's device record; asserts the T1-01…T1-31 topology checks that are pure-function-checkable (slot bijection, end-zone sums, envelope formulas, lid-fastener displacement, side-bolt pad fit). |
| `tests/test_shell.scad` | Tier 2 | Instantiates `mcc_shell_base`/`mcc_shell_lid`/`mcc_cradle`/`mcc_floor_features`/`mcc_vents` for this SKU at `-o *.csg` (evaluates the tree, no tessellation). |
| `tests/golden/pro-convert-for-ndi-to-hdmi.base.json`, `.lid.json`, `.panel.json` | Tier 3 | Generated by `build.py golden --update` (step 15) — do not hand-write. |

### 1.2 Existing files touched

| File | Change | Why |
|---|---|---|
| `lib/mcc/constants.scad` | Add a new `Section: Patch-wall layout (L2 milestone)` block (§3.0 below) with every constant `layout-patch-wall.md` §11 lists as not-yet-defined, plus the ones this plan additionally needs (tongue/groove, lid clearance, vent band height, rib/fastener geometry) — each cited or marked `assumed`/PLAN-ASSUMPTION. | `constants.scad` is the only place a bare number may live outside `0`/`1`/`2` (`architecture.md` §3). |
| `lib/mcc/mcc.scad` | Add `use <layout.scad>;` (before the L2 files), `use <shell.scad>;`, `use <cradle.scad>;`, `use <mounts.scad>;`, `use <vents.scad>;`. Remove the header comment noting L2 files "are not part of this build pass." | Barrel must expose every new public symbol to `models/**` (architecture.md §3 include discipline). |

No change to `lib/mcc/panel.scad` or `lib/mcc/neutrik.scad` — their existing `mcc_panel_cutout()` /
`mcc_panel_plate()` API already covers what `case.scad`'s `part=="panel"` branch needs (see §4).

---

## 2. Coordinate frame and computed dimensions — Pro Convert for NDI to HDMI

Frame per `layout-patch-wall.md` §1: origin at the case's outer-bbox centre in X/Y, floor (bed
surface) in Z. `+X` = end B (video/host end here), `+Y` = towards the patch wall, `+Z` = up.

Device record: `size = [100.9, 60.2, 23.3]`, family `compact`. Ports (from
`lib/mcc/devices/pro-convert-for-ndi-to-hdmi.scad`): `hdmi_out` (face `[1,0,0]`, `NAHDMI-W-B`),
`usb_host` (face `[1,0,0]`, `NAUSB-W-B`), `usb_b` (face `[-1,0,0]`, `NAUSB-W-B`), `rj45`
(face `[-1,0,0]`, `NE8FDP-B`), `side_bolt` (face `[0,-1,0]`, `pos [0,0]` placeholder).

### 2.1 End zones and envelope (`layout-patch-wall.md` §4/§8)

```
ez_cable(-X) = max(mcc_dev_side_allow(usb_b)=17, mcc_dev_side_allow(rj45)=27) = 27
ez_neg       = ez_cable(-X) + MCC_END_ZONE_NEG_EXTRA_SPLITTER(20)            = 47
ez_cable(+X) = max(mcc_dev_side_allow(hdmi_a)=40, mcc_dev_side_allow(usb_a)=17) = 40
ez_pos       = 40                                                     // no splitter term on +X

L = 2*MCC_WALL + ez_neg + dev_l + ez_pos = 6 + 47 + 100.9 + 40        = 193.9 mm

d_bay_free = mcc_bay_depth("NAHDMI-W-B") - 5.0 = (40.65+35) - 5.0     = 70.65 mm   (HDMI present)
W = MCC_T_PATCH(8) + d_bay_free(70.65) + MCC_GAP_DEV(2) + dev_w(60.2) + MCC_GAP_FAR(16) + MCC_WALL(3)
  = 159.85 mm       // layout-patch-wall.md §8's own table rounds this to "159.9" — traced to
                     // architecture.md §1 rounding mcc_bay_depth("NAHDMI-W-B") as "75.7" instead of
                     // the exact 75.65 (40.65+35). Use the exact constants.scad-derived 159.85 mm;
                     // it is what mcc_case_dims()/the golden will actually compute. ~0.05 mm,
                     // non-blocking, informational only — do not "round" the code to 159.9.

H = MCC_FLOOR_T(3) + MCC_PANEL_BAND(3) + MCC_PLATE_H(39) + MCC_PANEL_BAND(3) + MCC_LID_T(3) = 51.0 mm
```

**Final envelope: L × W × H = 193.9 × 159.85 × 51.0 mm** (printed bbox — `MCC_SIDE_BOLT_PROUD = 0`,
nothing protrudes, D-13). Bed margin vs. 256 mm build volume: 62.1 / 96.15 mm. Vs. the 250 mm assert
limit (`MCC_BUILD - MCC_BED_MARGIN`): 56.1 / 90.15 mm — comfortably legal on both axes.

### 2.2 Device placement

```
x_dev_lo = -L/2 + MCC_WALL + ez_neg  = -96.95 + 3 + 47   = -46.95
x_dev_c  = x_dev_lo + dev_l/2                            = +3.50    // off-centre, D-12
x_dev_hi = x_dev_lo + dev_l                               = 53.95

y_dev_lo = -W/2 + MCC_WALL + MCC_GAP_FAR = -79.925 + 3 + 16 = -60.925
y_dev_c  = y_dev_lo + dev_w/2                               = -30.825
y_dev_hi = y_dev_lo + dev_w                                 = -0.725

z_dev_lo = MCC_FLOOR_T + MCC_CRADLE_DECK(compact=10.85)     = 13.85
z_dev_hi = z_dev_lo + dev_h                                  = 37.15
z_conn_c = MCC_SIDE_BOLT_AXIS_Z (constant)                   = 25.5
```

Plenum above the device's top grille: `MCC_FLOOR_T + H_int - z_dev_hi` where lid underside
`= MCC_FLOOR_T + H_int = 48.0` → `48.0 - 37.15 = 10.85 mm` clear (must never be sealed —
architecture.md §12 Q10).

### 2.3 Panel aperture, plate, slots

```
plate_l = L - 26                       = 167.9 mm
plate_size = [167.9, MCC_PLATE_H(39)]
aperture Z range (case coords)         = [6.0, 45.0]           // = [MCC_PANEL_BAND, MCC_PANEL_BAND+MCC_PLATE_H]
aperture X half-width                  = plate_l/2 - 3          = 80.95   → X range ±80.95

n_slots = len(mcc_ports_external(dev)) = 4   (hdmi_out, usb_host, usb_b, rj45 — all 4 brought out)
span    = plate_l - 42                 = 125.9
pitch   = span / (n_slots-1)           = 41.9667 mm  (≈41.97)
slot_x(i) = -span/2 + (i-1)*pitch, i=1..4:
  slot_x(1) = -62.95    slot_x(2) = -20.983    slot_x(3) = +20.983    slot_x(4) = +62.95
```

**Slot assignment.** Per `layout-patch-wall.md` §3 steps 1-6, applied mechanically to this SKU's
actual port faces:

- Block A (`face.x<0`, data/power end) = `{usb_b (NAUSB-W-B, rank [8,20]), rj45 (NE8FDP-B, rank
  [10,25])}`. Sorted rank-descending: `rj45 > usb_b`. A fills slots `1..2`, highest rank → slot 1:
  **slot 1 = NE8FDP-B (rj45)**, **slot 2 = NAUSB-W-B (usb_b)**.
- Block B (`face.x>0`, video/host end) = `{hdmi_out (NAHDMI-W-B, rank [15,35]), usb_host (NAUSB-W-B,
  rank [8,20])}`. Sorted rank-descending: `hdmi_out > usb_host`. B fills slots `3..4`, highest rank →
  slot `n_slots`(4): **slot 4 = NAHDMI-W-B (hdmi_out)**, **slot 3 = NAUSB-W-B (usb_host)**.

**Computed slot order (1→4): NE8FDP-B (rj45) · NAUSB-W-B (usb_b) · NAUSB-W-B (usb_host) ·
NAHDMI-W-B (hdmi_out).**

> This is the **mechanical result of the §3 algorithm** applied to the real device file, and it is
> what `mcc_slot_for_port()` (a pure, deterministic function of the device data — it must never
> hardcode a per-SKU table) will actually compute. **It contradicts
> `layout-patch-wall.md` §3's own "Worked results" table row for "NDI to HDMI"**, which states
> `NAHDMI-W-B · NAUSB-W-B(host) · NAUSB-W-B(usb_b) · NE8FDP-B` — exactly reversed. See
> PLAN-ASSUMPTION #8 (§7); implement the algorithm, not the table, and flag the mismatch.

### 2.4 Fan bay, splitter bay, side-bolt boss

```
fan aperture: ⌀38 at (x = L/2 = 96.95, y = fan_y [default y_dev_c = -30.825], z = z_conn_c = 25.5),
              on the +X end wall.

splitter bay (on edge; env = MCC_SPLITTERS["DONGLE-75x40x20"].size = [75,40,20], H->X, L->Y, W->Z):
  bay_x = [-L/2+MCC_WALL, -L/2+MCC_WALL+20] = [-93.95, -73.95]
  bay_y = [-W/2+MCC_WALL, -W/2+MCC_WALL+75] = [-76.925, -1.925]
  bay_z = [MCC_FLOOR_T, MCC_FLOOR_T+40]     = [3, 43]

side-bolt boss axis (pos [0,0] placeholder — confidence "assumed", M1 unmeasured):
  x_bolt = x_dev_c + u = 3.50 + 0 = 3.50
  z_bolt = z_conn_c + v = 25.5 + 0 = 25.5
  keep-out: ⌀24 disc @ (x=3.50, z=25.5) ∪ 7 mm-wide strip at x=3.50 from z=MCC_FLOOR_T(3) to z=25.5
  T1-24 pad-fit check: pad_od(18) <= dev_h(23.3) - 2*|v|(0) - 2 = 21.3  -> 18<=21.3 OK
                        |u|(0) + pad_od/2(9) <= dev_l/2(50.45) - 2 = 48.45 -> OK
```

### 2.5 Lid fasteners (n_fast = 6, `L=193.9 > MCC_LID_SPAN_MAX=180`)

```
e = MCC_FASTENER_INSET = 10.0

Corners:        (±86.95, ±69.925)                          // ±(L/2-10), ±(W/2-10)

Patch-wall mid: qualifying inter-slot gaps at x = -41.967, 0, +41.967 (midpoints of slot_x pairs);
                clearance to nearest flange edge = pitch/2 - 13 = 7.983 mm >= 6.15 mm min (pass,
                1.83 mm spare — "the tightest in the repo", layout-patch-wall.md §6).
                n_slots=4 (even) -> 3 gaps (odd) -> unique nearest-to-zero: x_gap = 0.
                -> fastener 5 = (0, +69.925)

Far-wall mid:   x_bolt = +3.50; candidates x_bolt +- 16.14 = {+19.64, -12.64}; both legal
                (|x| <= L/2 - e - boss_od/2 = 82.81); nearer to 0 is -12.64.
                -> fastener 6 = (-12.64, -69.925)
```

All 6: `(86.95,69.925) (86.95,-69.925) (-86.95,69.925) (-86.95,-69.925) (0,69.925) (-12.64,-69.925)`.

### 2.6 Floor features (`mcc_floor_keepout()`, plan view)

| Feature | Position |
|---|---|
| Case 1/4"-20 insert | ⌀20 disc @ `vesa_pos` default `(0,0)` |
| VESA 75×75 | 4×⌀12 @ `vesa_pos + (±37.5,±37.5)` = `(±37.5,±37.5)` |
| Fishtail M4 pair | **reserve only** (no holes cut — pitch `unknown`, M7): 60×20 band centred on `vesa_pos`, i.e. `x∈[-30,30], y∈[-10,10]` |
| Strap slots | 2×(25×5) @ `x=±(L/2-25)=±71.95`, `y=±(W/2-12)=±67.925` |
| Splitter tie-down | 2×⌀8, inside `bay_x×bay_y` — see PLAN-ASSUMPTION #7 (do not call `mcc_splitter_tiedown()` unmodified) |
| Side-bolt support-web footprint | 3×20 mm rect at `x=x_bolt(3.50)`, against the far wall |

---

## 3. Module contracts

All new geometry modules `include <constants.scad>; use <util.scad>; use <ports.scad>; use
<layout.scad>;` plus their own L1 deps, per `openscad-authoring`. Every module asserts its own
contract (named per T1-xx where one applies). `$fn=64, circum=true` on every functional hole.

### 3.0 `lib/mcc/constants.scad` — new constants to add

Add after the existing "Captive side bolt" section, in a new `Section: Patch-wall layout (L2
milestone)` block, in this order (an ordering dependency exists: `MCC_DEV_SIDE_ALLOW` before nothing
depends on it; the rest are independent):

```
MCC_T_PATCH          = 8.0     // layout-patch-wall.md §2.1
MCC_PANEL_BAND        = 3.0     // §2.2
MCC_PLATE_H           = MCC_D_FLANGE[1] + 2*MCC_D_FLANGE_EDGE_MARGIN   // = 39.0, §2.2
MCC_PANEL_FRAME_MIN   = 10.0    // §2.3
MCC_PLATE_END_PAD     = 8.0     // §2.3
MCC_SLOTS_MAX         = 4       // §3
MCC_END_ZONE_MIN      = 20.0    // assumed, §4
MCC_GAP_DEV           = 2.0     // assumed, §4
MCC_LID_SPAN_MAX       = 180.0  // §6
MCC_FASTENER_INSET     = 10.0   // "e", §6
MCC_LID_FASTENER_CLR_MIN = MCC_BOSS_MIN_RATIO*MCC_INSERT_M3[1][1]/2 + 2.0  // boss_od/2+2.0 = 6.15, §6

// Per-kind device-side cable allowance table (§4). struct-style, mirrors MCC_PANEL_PARTS' shape.
MCC_DEV_SIDE_ALLOW = [
    ["bnc",            41], ["hdmi_a", 40], ["rj45", 27],
    ["usb_a",          17], ["usb_b",  17],
    ["minidin8",        0], ["rotary16", 0], ["button", 0], ["tripod_1_4_20", 0], ["blank", 0],
];
function mcc_dev_side_allow(kind) =
    let(ind = search([kind], MCC_DEV_SIDE_ALLOW)[0])
    assert(ind != [], str("mcc: unknown port kind \"", kind, "\" in mcc_dev_side_allow()"))
    MCC_DEV_SIDE_ALLOW[ind][1];

// Cradle deck: family-dependent (dev_h varies), NOT a flat constant -- see mcc_cradle_deck() in
// layout.scad. z_conn_c is already MCC_SIDE_BOLT_AXIS_Z above.

MCC_CRADLE_RIB_T       = 3.0    // "3.0 mm thick", layout-patch-wall.md §7 cradle table
MCC_CRADLE_RIB_H       = 9.0    // "9.0 mm tall", same table (<= 3x thickness rule)
MCC_CRADLE_FLOOR_PAD_T  = 2.0    // EPDM floor pad thickness, §7
MCC_CRADLE_FLOOR_PAD_MIN = 40    // pad footprint >= 40x40, §7

// PLAN-ASSUMPTION #4 (see plan §7): no contract-cited T&G production dimension exists; reuse the
// tg-ladder coupon's own assumed values (models/coupons/tg-ladder.scad T_W/T_H) as named constants.
MCC_TG_W = 3.0     // PLAN-ASSUMPTION, = MCC_WALL, matches tg-ladder coupon's T_W
MCC_TG_H = 4.0     // PLAN-ASSUMPTION, matches tg-ladder coupon's T_H

// PLAN-ASSUMPTION #3: T1-14 (H_int >= MCC_CRADLE_DECK + dev_h + MCC_LID_CLEAR) has no contract
// value. 2.0 mm mirrors this repo's other small-clearance constants (MCC_GAP_DEV, MCC_SIDE_BOLT_PAD_T).
MCC_LID_CLEAR = 2.0   // PLAN-ASSUMPTION

// Vents (layout-patch-wall.md §5). Slot/web widths ARE contract-cited (assumed there); band height
// is PLAN-ASSUMPTION #5 -- the contract's own 12 mm default FAILS T1-30 (990 vs 1134 mm^2); this
// value clears it with ~9% margin (see plan §7 for the derivation).
MCC_VENT_SLOT_W        = 1.2    // layout-patch-wall.md §5, assumed
MCC_VENT_WEB_W         = 1.6    // layout-patch-wall.md §5, assumed
MCC_VENT_INTAKE_BAND_H = 15.0   // PLAN-ASSUMPTION #5 (was informally "12" in the doc's own example)
MCC_VENT_EXHAUST_Z     = [32, 44]  // far-wall exhaust band Z range, layout-patch-wall.md §5 table

// Floor keep-out geometry, layout-patch-wall.md §7.1 floor table.
MCC_CASE_INSERT_KEEPOUT_D = 20.0
MCC_VESA_HOLE_D            = 12.0
MCC_STRAP_SLOT              = [25, 5]   // assumed
MCC_FISHTAIL_BAND           = [60, 20]  // reserve-only, pitch unknown (M7)
MCC_FLOOR_FEATURE_MIN_SEP    = 15.0     // "15 mm centre-to-centre ... or (r1+r2+2.0) where larger"
```

`MCC_PLATE_H` must be defined before nothing else in this file depends on it forward; it already
only depends on `MCC_D_FLANGE`/`MCC_D_FLANGE_EDGE_MARGIN`, both defined earlier in the file — no
reordering of existing constants required.

### 3.1 `lib/mcc/layout.scad` (new, L1)

```
include <BOSL2/std.scad>
include <constants.scad>
use <util.scad>
use <ports.scad>
```

Functions (all pure; `dev` = device record, `cfg` = the variant-config assoc-list from `case.scad`,
same shape as `new-case-variant`'s template — keys `"external_ports"`, `"fan"`, `"splitter"`,
optional `"fan_y"`):

- **`mcc_end_zone(dev, end)`** — `end` is `"neg"` or `"pos"`. `face = end=="neg" ? [-1,0,0] : [1,0,0]`.
  `ez_cable = max(MCC_END_ZONE_MIN, max over mcc_ports_on_face(dev,face) of
  mcc_dev_side_allow(mcc_port_kind(p)))`. Return `ez_cable + (end=="neg" ?
  MCC_END_ZONE_NEG_EXTRA_SPLITTER : 0)` (§6's reservation rule is unconditional — D-12 — so the
  splitter term is **always** added on the `"neg"` end regardless of `cfg`'s `"splitter"` flag;
  `cfg` is not consulted here). Assert `end == "neg" || end == "pos"`.
- **`mcc_slot_assignment(dev)`** — implements `layout-patch-wall.md` §3 steps 1-6 exactly:
  1. `ext = mcc_ports_external(dev)`; assert every port's face is `[±1,0,0]` (T1-01); assert
     `len(ext) <= MCC_SLOTS_MAX` (T1-02).
  2. Partition `A = [p for ext if face.x<0]`, `B = [p for ext if face.x>0]`.
  3. Sort each block descending by `[mcc_bend_envelope(panel), mcc_plug_len(panel)]`, ties broken by
     `mcc_port_pos(p)[0]` ascending then `mcc_port_id(p)` lexicographic (OpenSCAD has no built-in
     stable multi-key sort — write an explicit comparator function, e.g. via a decorate-sort-undecorate
     idiom over a numeric composite key: `key = -bend*1e6 - plug_len*1e3 + pos_x`, then break the
     final `id`-tie by a second pass only if two keys are bit-identical, which cannot happen here
     since `pos_x` differs between any two real ports — document this simplification in a comment).
  4. Block A fills slots `1..len(A)` in sorted order (index 0 of the sort -> slot 1). Block B fills
     slots `n_slots-len(B)+1..n_slots` in sorted order (index 0 of the sort -> slot `n_slots`, index 1
     -> `n_slots-1`, …).
  5. Any unfilled slot (only when the caller pads `n_slots` — not the case for this SKU, `n_slots ==
     len(ext) == 4`) gets `"DBA-BL-B"`.
  6. Return a list of `n_slots` structs `[["slot",i], ["port_id", id_or_undef], ["part", part]]`.
  Assert result is a bijection onto `1..n_slots` (T1-03), every slot has exactly one part (T1-04).
- **`mcc_slot_for_port(dev, id)`** — `struct_val` lookup into `mcc_slot_assignment(dev)` by
  `port_id == id`; asserts exactly one match.
- **`mcc_panel_plate_dims(dev)`** — `[L - 26, MCC_PLATE_H]` where `L = mcc_case_dims(dev,[])[0]`.
- **`mcc_case_layout(dev, cfg)`** — the ONE real computation; returns a struct with every field in
  §2.1-§2.5 above (`L,W,H,ez_neg,ez_pos,x_dev_lo,x_dev_c,x_dev_hi,y_dev_lo,y_dev_c,y_dev_hi,z_dev_lo,
  z_dev_hi,z_conn_c,plate_l,plate_size,n_slots,slot_x (list),fan_pos,fan_y,splitter_bay_x,
  splitter_bay_y,splitter_bay_z,side_bolt_x,side_bolt_z,side_bolt_keepout (from
  `mcc_side_bolt_keepout()`, `fasteners.scad`),lid_n_fast,lid_fastener_pos (list of `[x,y]`)`).
  `fan_y = struct_val(cfg, "fan_y", default=y_dev_c)` if `cfg` carries that key, else `y_dev_c`.
  Every other field ignores `cfg` today (only `fan_y` is currently variant-dependent; the parameter
  is kept per this file's own contract for forward compatibility — do not drop it).
- **`mcc_case_dims(dev, cfg)`** — `let(l = mcc_case_layout(dev,cfg)) [struct_val(l,"L"),
  struct_val(l,"W"), struct_val(l,"H")]`.
- **`mcc_cradle_deck(dev)`** — `z_conn_c - mcc_dev_size(dev)[2]/2 - MCC_FLOOR_T` (per-family value;
  evaluates to 10.85 for this SKU).

Asserts to add in `mcc_case_layout()` (T1-06 through T1-15, T1-21, T1-28 — the ones checkable from
pure numbers without drawn geometry): pitch ≥ `MCC_D_PITCH_H`; `d_bay_free` ≥ every external port's
`mcc_bay_depth`/`mcc_bend_envelope`; `ez(end)` ≥ the per-end cable max + splitter term; `plate_l` fits
inside `L - 2*MCC_WALL - 2*MCC_PANEL_FRAME_MIN`; `H_int >= MCC_CRADLE_DECK + dev_h + MCC_LID_CLEAR`
(T1-14); `H_int >= MCC_FAN_APERTURE_D + 2*MCC_WALL` (T1-15); `mcc_bbox_ok([L,W,MCC_WALL])` (T1-21);
splitter-bay-vs-end-zone non-intersection (T1-28, passes by construction per D-12 — assert it anyway).

### 3.2 `lib/mcc/shell.scad` (new, L2)

```
include <constants.scad>
use <util.scad>
use <ports.scad>
use <layout.scad>
use <neutrik.scad>
use <fasteners.scad>
use <fan.scad>
use <poe_splitter.scad>
```

- **`mcc_shell_base(dev, cfg)`** — additive outer shell (walls + floor) for the `L×W×H` box from
  `mcc_case_dims()`, minus: the patch-wall aperture windows (below), the fan-wall cutout
  (`mcc_fan_cutout()` when `cfg`'s `"fan"` is true, else nothing cut — the bay stays reserved as
  keep-out volume only, never drawn as a hole, per architecture.md §6 reservation rule), the
  side-bolt cut (`mcc_captive_side_bolt_cut()`), lid-fastener insert bores
  (`mcc_heat_set_bore()` at each of the 6 positions from `mcc_case_layout()`'s `lid_fastener_pos`),
  and the tongue (base carries the tongue, D-07) running along the top inner perimeter, height
  `MCC_TG_H`, width `MCC_TG_W`, minus `MCC_CLR_TG` allowance (the groove side, in the lid, is
  oversized by `2*MCC_CLR_TG`; the tongue itself is nominal). Unions in: the side-bolt boss
  (`mcc_captive_side_bolt_boss()`, oriented via `rotate([-90,0,0])` onto the far wall per
  `models/coupons/side-bolt.scad`'s own established convention — reuse that rotation exactly), the
  6 lid-fastener bosses (`mcc_heat_set_boss()`, `MCC_INSERT_M3`), the case-floor 1/4"-20 boss
  (`mcc_case_tripod_insert_boss()`), and `mcc_floor_features(dev,cfg)` (from `mounts.scad` —
  `shell.scad` calls it, does not duplicate it; the floor rule's single owner is still `mounts.scad`,
  `shell.scad` only assembles). Also unions `mcc_cradle(dev,cfg)` (from `cradle.scad`) and subtracts
  `mcc_vents(dev,cfg,face)` for the far (`-Y`) and `+X`/`-X` end walls (never `+Y`, T1-19) — via
  `use <cradle.scad>; use <vents.scad>;` (added to this file's own includes when those two files
  exist per the build order in §5).
  **Asserts:** `mcc_bbox_ok([L,W,H])`; wall thickness == `MCC_WALL` everywhere it's drawn as a
  constant-thickness extrusion; `MCC_SIDE_BOLT_PROUD == 0` unless `cfg` explicitly overrides `proud`
  (T1-29, this repo's flush-by-default rule).
- **`mcc_shell_lid(dev, cfg)`** — same outer envelope, floor replaced by the lid slab (`MCC_LID_T`),
  groove (not tongue) along the mating perimeter (`MCC_TG_W + 2*MCC_CLR_TG` wide,
  `MCC_TG_H` deep), 6 captive-thumbscrew holes (`mcc_captive_thumbscrew_hole()`) at
  `lid_fastener_pos`, no side-bolt feature (that lives entirely in the base's far wall), no cradle,
  no floor features. Same fan/vent cutouts mirrored onto the lid only where a vent band's Z range
  crosses the lid (per `layout-patch-wall.md` §5 — the exhaust band `MCC_VENT_EXHAUST_Z=[32,44]` and
  the far-wall intake band both live entirely below `z=45` for this SKU, i.e. entirely in the base;
  no lid-side vent cutting needed for this specific SKU — confirm this numerically before assuming
  it generalizes to other SKUs).
- **Patch-wall aperture — PLAN-ASSUMPTION #2 (see §7).** Cut **4 separate rectangular windows**
  through the full `MCC_T_PATCH` (8.0 mm) Y-stack, one per `slot_x(i)`, each window
  `[MCC_D_FLANGE[0] + 2*MCC_D_FLANGE_EDGE_MARGIN (=34), MCC_PLATE_H (=39)]` in X×Z, centred at
  `(slot_x(i), z_conn_c)`. Solid wall material remains between adjacent windows (pitch 41.97 − window
  width 34 ≈ 8 mm web, plus the plate's own continuous rim backs against it) and outboard of the
  outermost windows out to the `MCC_PANEL_FRAME_MIN` band. Each window's Z-top edge is chamfered
  inward at ≤45° over its own top half (self-supporting per the ≤45°/≤10 mm-span shell rule — 34 mm
  window width means each side's chamfer only needs to rise ≤17 mm to meet the centre, which fits
  comfortably inside the 39 mm window height) rather than left as a flat bridge. Implement the
  chamfer as a `hull()` of two rectangles at different Z (BOSL2 `prismoid()` is another option) — do
  not spend more than one iteration tuning the exact chamfer profile; visual correctness in the
  preview render (§6) is the acceptance bar for this milestone, not print verification (that is a
  Tier-4/print-check concern, later).
  The **plate rabbet** (the recess the plate itself drops into) is a stepped pocket inside these same
  4 windows: `proud bezel` layer (`z` local-Y `[0,3]` from the wall's outer face) at the window's
  bezel-opening size (window size + `2*MCC_CLR_SLIDE` clearance); `plate seat + structural lip`
  layers (local-Y `[3,8]`) recessed to the plate's own local footprint at that slot (the plate is one
  continuous 167.9×39 mm part — see `panel.scad`'s existing `mcc_panel_plate()`; `shell.scad` does
  **not** re-model the plate, only the 4 window voids + the rabbet ledges the plate's continuous rim
  lands on at its two `MCC_PLATE_END_PAD` ends, per `layout-patch-wall.md` §2.3's boss positions).
  4×M3 heat-set bores (`mcc_heat_set_bore()`) at `(±(plate_l/2-...), z_conn_c±14)` — i.e. at the two
  `MCC_PLATE_END_PAD` regions, matching `layout-patch-wall.md` §2.3 "through tabs in the plate's two
  `MCC_PLATE_END_PAD` regions (two per end, at `z = z_conn_c ± 14`)" — exact X per end: outboard of
  the outermost flange edge, i.e. `x = ±(plate_l/2 - MCC_PLATE_END_PAD/2)` as a first pass; verify
  against `MCC_D_FLANGE_EDGE_MARGIN` clearance in the assert.

### 3.3 `lib/mcc/cradle.scad` (new, L2)

```
include <constants.scad>
use <util.scad>
use <ports.scad>
use <layout.scad>
use <fasteners.scad>   // mcc_side_bolt_keepout()
```

- **`mcc_cradle(dev, cfg)`** — additive. Deck: a slab from `z=MCC_FLOOR_T` to `z=z_dev_lo` (10.85 mm
  for this SKU), `MCC_WALL`-thick top plate on `MCC_WALL`-thick webs (ribbed/hollow per
  `layout-patch-wall.md` §7), footprint = the device's XY extent (`x_dev_lo..x_dev_hi`,
  `y_dev_lo..y_dev_hi`) plus a small locating lip. Compliant floor pad pocket: a
  `MCC_CRADLE_FLOOR_PAD_MIN`×`MCC_CRADLE_FLOOR_PAD_MIN` (40×40) recess `MCC_CRADLE_FLOOR_PAD_T`
  (2.0 mm) deep near the case centre (use `(x_dev_c, y_dev_c)` as the pocket centre for this SKU —
  it is inside the device's own footprint by construction).
  Locating ribs: `MCC_CRADLE_RIB_T`(3.0)×`MCC_CRADLE_RIB_H`(9.0) fins standing on the deck, against
  the device's side faces.
  Far-flank ribs (against `-Y`, the far/duct-side flank) — **PLAN-ASSUMPTION #6 (see §7):** 4 ribs at
  `x = x_dev_lo + f*dev_l` for `f ∈ {0.10, 0.35, 0.65, 0.90}` (i.e. `x ≈ -36.86, -11.51, +13.64,
  +38.86`), each individually clear of the side-bolt keep-out (`|x - x_bolt(3.50)| >=
  disc_d/2(12) + MCC_CRADLE_RIB_T/2 + 2` — verify numerically for each of the 4 positions in an
  assert, all 4 pass at these fractions since the nearest, `+13.64`, is `10.14` mm from `x_bolt`,
  short of the `12+1.5+2=15.5` mm minimum — **widen to `f ∈ {0.10, 0.30, 0.72, 0.92}` instead**, which
  puts the nearest rib (`+16.79`) `13.29` mm away — **still short**; use `f ∈ {0.10, 0.28, 0.76,
  0.92}` (`x ≈ -36.86, -15.65, +17.68, +40.76`), nearest rib `17.68`, distance from `x_bolt(3.50)` =
  `14.18` mm — still short of 15.5. **Do not hand-tune this further by trial fractions** — instead,
  place exactly 2 ribs symmetric about `x_dev_c` at `x = x_dev_c ± max(dev_l*0.30, 15.5+
  MCC_CRADLE_RIB_T/2+disc_d/2+2+1)` clamped inside `[x_dev_lo+8, x_dev_hi-8]`, plus 1 more rib at
  whichever of `x_dev_lo+8`/`x_dev_hi-8` is farther from the first two, for 3 total — **and assert
  the clearance explicitly rather than trusting the arithmetic above**; if the assert fails at
  render time, that is the correct failure mode (fix the fraction, don't relax the assert). Each rib,
  below `z = z_dev_lo` (i.e. the portion that would otherwise dam the far-wall duct), is open: a
  ≤45° self-supporting notch or chamfered arch, ≤3 mm legs at each end, clear span ≤10 mm
  (`layout-patch-wall.md` §7).
  Patch-flank ribs (against `+Y`): only where `|x| > plate_l/2 - 3` (= `80.95`), i.e. only in the two
  end-pad zones outboard of the aperture — none inside `x ∈ [-80.95, 80.95]` (T1-20).
  End ribs: partial only, clearing every end-face port cutout/plug envelope (`hdmi_out`, `usb_host` at
  `+X`; `usb_b`, `rj45` at `-X` — use `mcc_neutrik_d_envelope()`-style keep-out boxes, ghosted, to
  verify clearance visually via `MCC_SHOW_GHOST`, not as a hard assert this milestone).
  **No floor penetration** — `cradle.scad` never cuts the floor (architecture.md §6).
  **Asserts:** far-flank rib count `>= 3`; each far-flank rib clears
  `mcc_side_bolt_keepout()`'s disc+strip (T1-27, the cradle half); patch-flank ribs only outboard of
  `plate_l/2-3` (T1-20); rib height `<= 3 * MCC_CRADLE_RIB_T` (27 mm — 9 mm is well inside).

### 3.4 `lib/mcc/mounts.scad` (new, L2)

```
include <constants.scad>
use <util.scad>
use <layout.scad>
use <fasteners.scad>   // mcc_case_tripod_insert_bore/boss, mcc_m4_hole, mcc_side_bolt_keepout
use <poe_splitter.scad>
```

- **`mcc_floor_features(dev, cfg)`** — additive+subtractive combined (a single module, matching
  `mcc_shell_base`'s expectation that it can `union()`/`translate()` this call directly): case
  1/4"-20 insert boss+bore (`mcc_case_tripod_insert_boss()`/`_bore()`) at `vesa_pos` default `(0,0)`;
  VESA 4×M4 clearance holes (`mcc_m4_hole()`) at `(±37.5,±37.5)`; Fishtail band **reserved but not
  cut** (draw nothing — `MCC_FISHTAIL_BAND` is a keep-out only, per PLAN-ASSUMPTION note in §3.0);
  2 strap slots at `x=±71.95, y=±67.925` (through-cuts, `MCC_STRAP_SLOT=[25,5]`); splitter tie-down —
  **do not call `mcc_splitter_tiedown()` unmodified (PLAN-ASSUMPTION #7, §7)** — instead cut 2×⌀8
  through-floor holes directly from `bay_x`/`bay_y` (e.g. at
  `(mean(bay_x), bay_y[0]+8)` and `(mean(bay_x), bay_y[1]-8)`, i.e. inset 8 mm from each Y-end of the
  on-edge splitter footprint); side-bolt support-web floor footprint is **not cut here** (it is part
  of `mcc_captive_side_bolt_boss()`'s own additive geometry in `shell.scad`) but **is** registered in
  `mcc_floor_keepout()` below so nothing else overlaps it.
- **`mcc_floor_keepout()`** — pure function (no `dev`/`cfg` needed beyond what's already
  positionally fixed for `vesa_pos=(0,0)`): returns a list of `[cx, cy, "shape", size_or_d]` structs
  for every feature in §2.6, plus the side-bolt support-web rectangle. Asserts
  `MCC_FLOOR_FEATURE_MIN_SEP` (or `r1+r2+2.0` where larger) between every pair — a plain nested-loop
  pairwise check, mirroring `mcc_panel_plate()`'s existing pairwise-pitch assert style in `panel.scad`.
  Also asserts the splitter tie-down holes and the VESA/insert features don't collide with the
  splitter bay itself or the side-bolt web footprint (T1-17-style).

### 3.5 `lib/mcc/vents.scad` (new, L2)

```
include <constants.scad>
use <util.scad>
use <layout.scad>
use <fasteners.scad>   // mcc_side_bolt_keepout_2d()
```

- **`mcc_vents(dev, cfg, face)`** — subtractive. `face` ∈ `[-1,0,0]` (−X end wall), `[1,0,0]` (+X end
  wall — fan aperture only, no slot array), `[0,-1,0]` (far wall — intake low + exhaust high).
  **Never called for `face==[0,1,0]`** (patch wall) — assert this explicitly if ever invoked with it
  (T1-19).
  Far wall (`[0,-1,0]`): intake band `z ∈ [5, 5+MCC_VENT_INTAKE_BAND_H] = [5,20]` (PLAN-ASSUMPTION #5)
  running the device's X length (`x_dev_lo..x_dev_hi`), vertical slots `MCC_VENT_SLOT_W` wide,
  `MCC_VENT_WEB_W` web, cut through the wall (X-oriented void array in a Y-normal wall — i.e. slots
  run in Z, repeat in X). Exhaust band `z ∈ MCC_VENT_EXHAUST_Z = [32,44]`, `+X` half only
  (`x >= x_bolt + keepout_d/2 = 3.50+12 = 15.5`, per `layout-patch-wall.md` §5's "the exhaust band's
  inner edge must start at `x >= x_bolt + keepout_d/2`" rule — **not** `x>=0`). Subtract
  `mcc_side_bolt_keepout_2d(axis_z=25.5)` (translated to `x=x_bolt=3.50`) from the whole far-wall slot
  pattern before cutting (T1-23).
  −X end wall (`[-1,0,0]`): intake band, **+Y half only** (`y >= 0`, the splitter slab masks `y<0` —
  `layout-patch-wall.md` §5), same `z=[5,20]` band, same slot/web pitch, spanning
  `y ∈ [0, W/2 - MCC_WALL]`.
  +X end wall (`[1,0,0]`): no slot array — only `mcc_fan_cutout("NF-A4x10", grille=cfg's
  `"fan"`==true)` at `(fan_y, z_conn_c)` when `"fan"` is true; when `"fan"` is false the wall stays
  solid there (the bay is *reserved* as keep-out volume upstream in `shell.scad`, not vented, per the
  reservation rule — a reserved-but-disabled fan bay does not need an opening).
  **Asserts:** never called for the patch wall (T1-19); far-wall slot pattern excludes the side-bolt
  keep-out disc+strip (T1-23); T1-30 — total intake free area (far wall + −X end wall bands, at the
  actual computed geometry for this SKU) `>= MCC_VENT_AREA_RATIO * (pi/4) * MCC_FAN_APERTURE_D^2 =
  1134.1 mm²` when `cfg`'s `"fan"` reservation applies (always, per the reservation rule) — compute
  the two bands' free area from `MCC_VENT_SLOT_W/(MCC_VENT_SLOT_W+MCC_VENT_WEB_W)` duty cycle times
  each band's run-length times `MCC_VENT_INTAKE_BAND_H`, and assert the sum meets the threshold; at
  `MCC_VENT_INTAKE_BAND_H=15` this SKU's far-wall run (`dev_l=100.9`) + end-wall run
  (`~W/2-MCC_WALL≈76.9`) yields **~1237 mm²** (duty cycle `1.2/2.8=0.4286`, `(100.9+76.9)*15*0.4286 ≈
  1143`… **recompute exactly in the module and let the assert be the source of truth** — the
  hand-estimate here is illustrative only, not to be hardcoded).

---

## 4. Assembly file — `models/pro-convert-for-ndi-to-hdmi/case.scad`

```openscad
// models/pro-convert-for-ndi-to-hdmi/case.scad
include <mcc/mcc.scad>
include <mcc/devices/pro-convert-for-ndi-to-hdmi.scad>

$fa = 1; $fs = 0.4;

part = "base"; // overridden via -D part="..."

// explode: Z-lift (mm) applied to the lid ONLY when part=="assembly" (preview aid). No effect on
// base/lid/panel exports.
explode = 0;

variant = [
    ["external_ports", ["hdmi_out", "usb_host", "usb_b", "rj45"]],  // all 4 physical ports brought out
    ["fan",             false],   // reserved regardless (architecture.md §6 reservation rule)
    ["splitter",        false],   // reserved regardless
];

dev = MCC_DEV_PRO_CONVERT_FOR_NDI_TO_HDMI;
L_dims = mcc_case_dims(dev, variant);
echo(str("pro-convert-for-ndi-to-hdmi: L=", L_dims[0], " W=", L_dims[1], " H=", L_dims[2]));

if (part == "base") {
    mcc_shell_base(dev = dev, cfg = variant);
} else if (part == "lid") {
    mcc_shell_lid(dev = dev, cfg = variant);
} else if (part == "panel") {
    slots_raw = mcc_slot_assignment(dev);   // layout.scad
    layout    = mcc_case_layout(dev, variant);
    plate_sz  = mcc_panel_plate_dims(dev);
    slot_list = [for (s = slots_raw)
        let(i = struct_val(s,"slot"))
        [struct_val(layout,"slot_x")[i-1], 0, struct_val(s,"part"), false]];
    mcc_panel_plate(size = plate_sz, slots = slot_list);
} else if (part == "assembly") {
    // Non-exported preview only. build.py's discover_models() hardcodes parts=["base","lid"] (+
    // "panel" iff the literal string 'part == "panel"' appears in this file) -- it never looks for
    // "assembly", so this branch is invisible to render --all / check --all / golden by
    // construction. Never add an "assembly" string anywhere build.py's discovery regex could match.
    color("SlateGray") mcc_shell_base(dev = dev, cfg = variant);
    translate([0, 0, explode])
        color("LightSteelBlue", 0.9) mcc_shell_lid(dev = dev, cfg = variant);
    // panel plate in place (not exploded -- it lives inside the base's rabbet)
    slots_raw = mcc_slot_assignment(dev);
    layout    = mcc_case_layout(dev, variant);
    plate_sz  = mcc_panel_plate_dims(dev);
    slot_list = [for (s = slots_raw)
        let(i = struct_val(s,"slot"))
        [struct_val(layout,"slot_x")[i-1], 0, struct_val(s,"part"), false]];
    translate([0, struct_val(layout,"y_dev_hi") + 8, struct_val(layout,"z_conn_c")])
        rotate([90,0,0])
            color("DimGray") mcc_panel_plate(size = plate_sz, slots = slot_list);
    mcc_ghost(dev, show = true);   // device + plug envelopes; %-rendered, excluded from CSG anyway
} else {
    assert(false, str("mcc: unknown part \"", part, "\""));
}
```

~65 lines including the panel/assembly duplication (slot-list construction is shared between
`"panel"` and `"assembly"` — a small private helper function in `case.scad` itself,
`_mcc_case_slot_list(dev, cfg)`, is acceptable here to avoid the duplication; it is not "raw
geometry" per `new-case-variant`'s stop-and-report gate, only data assembly). Keep the whole file
under 80 lines per the skill's own budget; extract that helper if the file grows past it.

**`part=="assembly"` gate.** Confirmed by reading `scripts/build.py`'s `discover_models()`
(`scripts/build.py:129-145`): it always sets `parts = ["base", "lid"]` and appends `"panel"` only
when the literal substring `'part == "panel"'` is found in the file text — it never scans for or
adds `"assembly"`. So `render --all` / `check --all` / `golden` can **never** pick up the assembly
part; it is reachable only via an explicit `openscad ... -D part=\"assembly\"` CLI invocation (§6).
No `build.py` change is needed to keep it out of the export/golden set — it is already excluded by
construction. Do not rename it to anything containing the substring `"panel"` or add a matching
`part == "..."` string that could accidentally satisfy that regex-like check for an unrelated part.

---

## 5. Ordered implementation steps

**All steps 1-19 below are DONE (2026-09-08).** Step 20 (decision-log entry) was not done — this
plan's own "Implementation notes" block above and the task's final report to the teamlead serve that
purpose instead; no separate `.claude/knowledge/decision-log.md` was created (out of scope for a
developer pass — `.claude/**` is architect-owned).

1. **`lib/mcc/constants.scad`** — append the §3.0 block. Verify: `openscad --backend=Manifold -o
   out.csg tests/test_constants.scad` (existing test) still passes.
2. **`lib/mcc/layout.scad`** — create per §3.1. Verify: create `tests/test_layout.scad` (step 10) in
   the same pass if easier, but at minimum smoke it standalone first:
   `openscad --backend=Manifold -D 'echo(mcc_case_dims(MCC_DEV_PRO_CONVERT_FOR_NDI_TO_HDMI,[]))' ...`
   is not valid OpenSCAD CLI syntax — instead add a throwaway `echo()` at the bottom of
   `layout.scad` temporarily, or just proceed straight to step 10's real test file.
3. **`lib/mcc/mcc.scad`** — add `use <layout.scad>;` only (not yet the L2 files — they don't exist).
   Remove the "not part of this build pass" note in the header comment (partially true now).
4. **`lib/mcc/cradle.scad`** — create per §3.3.
5. **`lib/mcc/mounts.scad`** — create per §3.4.
6. **`lib/mcc/vents.scad`** — create per §3.5.
7. **`lib/mcc/shell.scad`** — create per §3.2 (depends on `cradle.scad`/`mounts.scad`/`vents.scad`
   existing — hence last of the four L2 files).
8. **`lib/mcc/mcc.scad`** — add `use <shell.scad>; use <cradle.scad>; use <mounts.scad>; use
   <vents.scad>;`.
9. **`tests/test_layout.scad`** — create: exercise every `layout.scad` function against
   `MCC_DEV_PRO_CONVERT_FOR_NDI_TO_HDMI`, assert the computed `L/W/H/pitch/x_dev_c` match §2.1/§2.3
   exactly (within `1e-6`), assert the slot order matches §2.3's computed result (not the doc's
   worked table — see PLAN-ASSUMPTION #8), assert every T1-01…T1-15/T1-21/T1-28 check from §3.1.
   Verify: `openscad --backend=Manifold -o out.csg tests/test_layout.scad`.
10. **`tests/test_shell.scad`** — create: `include <mcc/mcc.scad>; include
    <mcc/devices/pro-convert-for-ndi-to-hdmi.scad>;`, instantiate `mcc_shell_base`, `mcc_shell_lid`,
    `mcc_cradle`, `mcc_floor_features`, and `mcc_vents` for each of the 3 wall faces, at this SKU's
    device/variant. Verify: `openscad --backend=Manifold -o out.csg tests/test_shell.scad`.
11. **`models/pro-convert-for-ndi-to-hdmi/case.scad`** — create per §4.
12. `python scripts/build.py smoke` — runs every `tests/test_*.scad` including the two new ones.
    Must exit 0 with no `ERROR:`.
13. `python scripts/build.py render pro-convert-for-ndi-to-hdmi --part base --part lid --part panel`
    — first real render of all 3 exported parts. Inspect the echoed `L=...W=...H=...` line against
    §2.1's numbers.
14. `python scripts/build.py check --all` — Tier-3 mesh checks (watertight, winding-consistent,
    single shell, bbox ≤ 244 mm/axis) on the 3 new STLs.
15. `python scripts/build.py golden --update pro-convert-for-ndi-to-hdmi` — creates
    `tests/golden/pro-convert-for-ndi-to-hdmi.{base,lid,panel}.json`. Eyeball the bbox/volume numbers
    by hand against §2.1 before committing (per `new-case-variant`'s own checklist).
16. `python scripts/build.py golden` — full-repo golden comparison (confirms nothing else regressed).
17. `python scripts/build.py all` — `smoke → render --all → check --all → golden`, the exact
    CI-equivalent gate. Must exit 0.
18. Render the 4 preview PNGs + the STL trio for a web viewer (§6) — not part of `build.py`, run
    directly.
19. Add a `BOM.md` section for this variant (`bom-update` skill) and update the model's status line
    in the repo `README.md`, per `new-case-variant`'s checklist — out of this plan's strict scope but
    listed so it isn't dropped before PR.
20. Update `.claude/knowledge/decision-log.md` (create it if absent — `CLAUDE.md`'s "Plans must not
    prescribe explanatory comments" rule routes rationale here, not into code comments) with one
    entry per PLAN-ASSUMPTION in §7 that the architect confirms, recording the confirmed value and
    date. Do **not** add ticket-referencing or rationale comments to any `.scad` file for this.

---

## 6. Preview renders

Camera parameters below are **starting points** — OpenSCAD's gimbal camera convention
(`--camera=tx,ty,tz,rx,ry,rz,dist`) is easiest to tune by rendering once and adjusting; treat the
numbers as a first pass, not an exact requirement. Case centre ≈ `(0, 0, 25.5)`; case footprint
≈ `194 × 160 mm`, so `dist=550-600` frames it with margin.

```powershell
$env:OPENSCADPATH = "<repo>\lib"
$exe = "C:\Program Files\OpenSCAD (Nightly)\openscad.com"
$case = "models\pro-convert-for-ndi-to-hdmi\case.scad"
$common = @('--backend=Manifold','--render','--imgsize=1600,1200','--projection=p',
            '--colorscheme=Tomorrow','-D','part="assembly"','-D','MCC_SHOW_GHOST=true','-D','explode=40')

# iso front-patch (patch wall +Y, +X end visible)
& $exe @common --camera=0,0,25.5,55,0,35,600  -o out\preview\iso-front-patch.png $case

# iso rear (far wall -Y, -X end visible)
& $exe @common --camera=0,0,25.5,55,0,215,600 -o out\preview\iso-rear.png $case

# top (plan view)
& $exe @common --camera=0,0,25.5,0,0,0,550    -o out\preview\top.png $case

# patch-wall elevation (front-on +Y wall)
& $exe @common --camera=0,-500,25.5,90,0,0,500 -o out\preview\patch-wall-elevation.png $case
```

STL trio for a web viewer — reuse the existing `build.py` exports rather than a separate ad-hoc
path (step 13 already produced these):

```
exports\pro-convert-for-ndi-to-hdmi\base.stl
exports\pro-convert-for-ndi-to-hdmi\lid.stl
exports\pro-convert-for-ndi-to-hdmi\panel.stl
```

Send the 4 PNGs + the 3 STLs to the user for visual review before the PR (`SendUserFile`, not part
of `build.py`).

---

## 7. Open points for the architect — every PLAN-ASSUMPTION

1. **New L1 file `lib/mcc/layout.scad`.** Not enumerated in `architecture.md` §3's L1/L2 file lists
   (which name `shell/panel/cradle/mounts/vents` at L2 and
   `neutrik/fasteners/fan/poe_splitter/ghost` at L1). This plan adds it as a 6th L1 file — a
   device/variant-aware pure-function module every L2 geometry file `use`s — to avoid five
   independent (and inevitably drifting) copies of the `L/W/H`/slot/end-zone formulas. Precedent:
   `fasteners.scad` already hosts `mcc_side_bolt_keepout()`, a similar shared-pure-function role, at
   L1. Confirm this placement, or direct it elsewhere (e.g. fold into `shell.scad` and accept lateral
   L2→L2 `use` from `panel`/`cradle`/`mounts`/`vents`).
2. **Patch-wall aperture as 4 discrete windows, not one continuous 162 mm-wide opening.** A single
   opening that wide cannot satisfy architecture.md §5's "≤45° self-supporting roof, no unsupported
   span >10 mm" rule (a 45° chamfer converging from both top corners of a 161.9 mm-wide void would
   need ~81 mm of rise, far more than the 39 mm-tall opening has room for). This plan instead cuts 4
   separate ~34 mm-wide windows (one per connector slot, individually self-supporting) behind the one
   continuous 167.9 mm plate, leaving solid wall material in the ~8 mm inter-slot gaps. This is a
   genuine re-interpretation of "one patch-wall aperture" — confirm before `shell.scad` is built, or
   the aperture geometry has to be redone.
3. **`MCC_LID_CLEAR` (T1-14) = 2.0 mm.** No contract-cited value exists; this mirrors the repo's
   other 2.0 mm small-clearance constants (`MCC_GAP_DEV`, `MCC_SIDE_BOLT_PAD_T`). At this SKU's
   actual geometry the plenum is already 10.85 mm, so this assert passes trivially either way — it
   only matters for a future, taller-device SKU.
4. **`MCC_TG_W`/`MCC_TG_H` (tongue-and-groove production dimensions) = 3.0 / 4.0 mm.** No
   contract-cited production value exists — only `MCC_CLR_TG` (the per-side *clearance*, to be
   calibrated by the `tg-ladder` coupon) is defined. This plan reuses the coupon's own already-assumed
   `T_W`/`T_H` values as named constants. Confirm, or supply real values.
5. **`MCC_VENT_INTAKE_BAND_H` = 15.0 mm (was an informal 12 mm in the contract's own worked
   example).** `layout-patch-wall.md` T1-30 **fails** at 12 mm (≈990 mm² vs. the required
   ≈1134 mm²); the contract itself says "widen the intake band (e.g. `[5,20]`)" without committing to
   a number. 15 mm is the smallest height that clears T1-30 with margin at this SKU's actual run
   lengths (worked to ≈1237 mm² by hand in §3.5 — the module's own assert is authoritative, not this
   estimate). Confirm, and note this widens the far-wall/-X-end-wall vent bands for every future SKU
   too, not just this one.
6. **Far-flank cradle rib count/positions.** The contract requires "≥3 X positions" (open-notch
   design) or "exactly two, outboard of the intake band" (an alternative it does not fully specify —
   unclear how a rib "outboard of the intake band" still reaches the device flank to locate it, since
   the intake band spans the full device length). This plan uses 3 ribs, exact X positions computed
   from a clearance rule against the side-bolt keep-out (§3.3) rather than fixed fractions, with the
   module's own assert as the final authority. Confirm the rib count/placement rule, or supply exact
   positions.
7. **`mcc_splitter_tiedown()`'s coordinate convention doesn't match the on-edge splitter
   reservation.** The module (already implemented, `poe_splitter.scad`) places its 2 tie slots at
   local `Y = ±size[1]/2`, i.e. it assumes the splitter sits **flat** (`L→X, W→Y, H→Z`). Every other
   consumer of the splitter record (`mcc_splitter_envelope()`, and `layout-patch-wall.md` §5 itself)
   places it **on edge** (`H→X, L→Y, W→Z`). Calling `mcc_splitter_tiedown()` unmodified in
   `mounts.scad` would put the tie slots in the wrong place. This plan has `mounts.scad` compute the
   2 tie-down holes directly from `bay_x`/`bay_y` instead of calling the existing module. Confirm this
   workaround, or fix `mcc_splitter_tiedown()` to take an explicit orientation parameter shared with
   `mcc_splitter_envelope()` (a small `poe_splitter.scad` change, out of this plan's file list unless
   approved).
8. **Slot order for this SKU (and, by the same face-assignment pattern, the other three decoder
   SKUs — NDI to SDI/AIO/HDMI 4K) computed via `layout-patch-wall.md` §3's own algorithm CONTRADICTS
   that document's own "Worked results" table for those rows.** Algorithm (applied mechanically to
   `pro-convert-for-ndi-to-hdmi.scad`'s actual port faces): slots 1-4 =
   `NE8FDP-B · NAUSB-W-B(usb_b) · NAUSB-W-B(usb_host) · NAHDMI-W-B`. Table:
   `NAHDMI-W-B · NAUSB-W-B(usb_host) · NAUSB-W-B(usb_b) · NE8FDP-B` — exactly reversed. Verified this
   is *not* a mistake in my own derivation: the encoder-family table rows (HDMI Plus, SDI Plus, HDMI
   TX, SDI TX) **do** match the algorithm when checked the same way against their device files. Only
   the decoder rows disagree. This plan implements the algorithm (§3.1) since `mcc_slot_for_port()`
   must be a deterministic pure function of the device data, not a hardcoded per-SKU table — but the
   mismatch needs an explicit ruling: either the table has a block-A/B transcription swap for the
   decoder family (fix the doc), or the four decoder device files' face polarity was chosen to match
   the (wrong) table and should be flipped (a `device-portmap` task on 4 files, blocking this plan's
   panel/assembly output until resolved). **This does not change `L`/`W`/`H`/`pitch`/`x_dev_c`** —
   only which physical connector lands in which panel slot — so it does not block `shell.scad`/
   `cradle.scad`/`mounts.scad`/`vents.scad` implementation, only the panel/assembly renders' visual
   correctness and the BOM's per-slot connector labelling.

---

## Summary for handoff

- **Plan file:** `docs/plans/2026-09-08-l2-first-case.md` (this file).
- **Computed envelope:** `L × W × H = 193.9 × 159.85 × 51.0 mm` (contract's own table rounds `W` to
  159.9 — a ~0.05 mm documentation-rounding artifact, non-blocking).
- **Slot order (as `mcc_slot_for_port()` will actually compute it):** 1 = `NE8FDP-B` (rj45/etherCON),
  2 = `NAUSB-W-B` (usb_b), 3 = `NAUSB-W-B` (usb_host), 4 = `NAHDMI-W-B` (hdmi_out) — **contradicts**
  `layout-patch-wall.md` §3's own worked table for this SKU; see PLAN-ASSUMPTION #8.
- **8 PLAN-ASSUMPTIONs**, listed in §7, all requiring `solution-architect` sign-off before or during
  implementation — #1, #2 and #8 are structurally significant (a new L1 file, a re-interpreted
  aperture geometry, and a genuine contract self-contradiction) and should be resolved **before**
  `shell.scad`/`panel.scad` work starts; #3-#7 are narrow, low-risk numeric defaults that can be
  confirmed in parallel with implementation.
