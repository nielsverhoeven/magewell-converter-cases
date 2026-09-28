# Plan C: perfectly round D-connector holes, no printed thread

> **Implemented as amended by the architect verdict appended at the end of this file (B1–B14). Where they conflict, the verdict wins.**

Status: researched 2026-09-28 against `main` @ `047902e` (post D34–D39). Ready for `solution-architect`
gate, then implementation. Audience: a Sonnet-tier developer. Every decision below is made — do not
improvise; if something looks like a judgment call that isn't already resolved here, stop and ask.

Supersedes: the researcher's own earlier "STEP-only" framing of this ticket (obsolete once `main`
picked up D36/D39 mid-research — no separate panel plate, and an exact CSG→STEP converter already
exists) and the separate scratch plan `scratchpad/plans/B-remove-printed-threads.md` (obsolete: it
assumed the pre-D36 plate+boss architecture, which no longer exists). Both prior drafts are superseded
in full by this single plan, which covers **two combined user decisions, 2026-09-28**:

1. **D-connector holes must be perfectly round** — no teardrop — in the model, the STL and the STEP.
2. **Remove the printed M3 thread** from the connector-fixing bore. Replace it with a plain **Ø2.5 mm
   tap-drill bore**; an external CAD specialist threads it himself from the STEP export.

---

## 0. What changed under this ticket while it was being researched

The repo moved 5 commits during this research pass (teamlead fast-forwarded the checkout to
`origin/main @ 047902e`). Two of those commits matter completely:

- **D36** (`7bdcbe4`): the separate bolt-in connector panel plate is gone. Connectors now cut straight
  into the base's patch wall via `mcc_neutrik_d_wall_cut()` (new, `lib/mcc/neutrik.scad`) /
  `mcc_panel_wall_cut()` (new dispatcher, `lib/mcc/panel.scad`). The seat hole and the body window
  behind it are **truncated teardrops** (round with a flattened point at the top) so the wall — which
  prints **standing**, connector axis horizontal — never roofs over with an unsupported round arch.
  Connector fixing is two **printed M3×0.5 threads straight through the 5 mm wall** (2 mm seat + 3 mm
  behind it) — no pads, no pillars, no separate boss.
- **D39** (`1ad78e6`): STEP is no longer converted from the tessellated mesh. `render` now also writes
  `<part>.csg` (OpenSCAD's evaluated CSG tree), and `scripts/csg_to_step.py` rebuilds that tree
  directly in OpenCascade: `cylinder`/`circle`/`sphere` at ≥16 fragments become **true analytic**
  cylinders/cones/circles; polygon vertex runs that lie on a circle are refitted as arcs; a
  `polyhedron` (BOSL2 VNF threads included) stays faceted, by design — there is no curve-fitting for
  a shape that genuinely isn't a curve. `scripts/build.py`'s `export_step()` tries this exact path
  first and only falls back to the old faceted `mesh_to_step.py` on failure (unsupported CSG node,
  timeout, or a >1% volume mismatch against the rendered mesh).

Consequence for this ticket: **the STEP-export mechanism itself is not the problem any more.** D39 already
gives every `cylinder()`/`circle()` a true analytic face. What's left to fix is that (a) the seat/window
are still *teardrops*, which are genuinely not round regardless of how faithfully they're exported, and
(b) the fixing bore is still a *real printed thread* (a BOSL2 VNF), which D39's own docstring explicitly
leaves faceted on purpose (`polyhedron -> planar faces ... faceted by nature`). Both of those are shape
decisions, not export-fidelity bugs, and the fix is to change the shapes, not the converter.

`scripts/csg_to_step.py` itself needs **no changes** — it was proven (§2 below) to already do exactly
what's needed for a plain circle/cylinder/cone. This closes out the original ticket's whole "evaluate
approach (a)/(b)/(c) for the STEP pipeline" question: none of those is needed, because the repo already
shipped a fourth, better approach (an exact CSG interpreter) that reads the same source geometry, not a
second one.

---

## 1. Diagnosis

### 1.1 What the specialist is almost certainly looking at

The modeller's screenshot ("the D-connector holes are not round; the two middle ones show vertical
stripes") is very likely a STEP export of the **base**, not a plate (the plate hasn't existed since D36).
Reading the geometry:

- The long grey box with a thicker bottom band = the case floor (thicker wall band at the bottom of the
  patch wall / the floor slab visible behind it).
- The teardrop's **pointed top** is a real, deliberate, non-circular feature (`ang=45`,
  `cap_h = d/2 + MCC_APERTURE_CAP_RISE`) — this alone makes every hole "not round," independent of STL
  vs STEP vs faceted vs exact.
- "Vertical stripes across the hole area" in two of the four holes and "dark, clean" in the other two is
  consistent with looking **through** an open hole at whatever sits behind it inside the case (cradle
  ribs, structural webs) at different depths/angles per slot position — a viewing artefact of what's
  *behind* the opening, not a property of the hole boundary itself. This part of the observation is
  plausible but not independently reproduced in this pass (see §1.4).
- The two small screw holes "look round" because their **entry mouth** is a plain circumscribed circle
  either way; what's *behind* the mouth (a real M3×0.5 thread) is not visible in a shaded exterior render
  and only shows up as a topology/CAD-usability defect once the specialist tries to select/fillet it.

### 1.2 Evidence — the teardrop is genuinely not round, even under the exact STEP pipeline

Reproduced the exact wall-cut geometry in isolation (a standing 40×45 mm wall section, 5 mm thick —
the same construction as `models/coupons/neutrik-tile.scad` — built inline in scratch so no tracked
file was touched) for the **largest connector class**, `NE8FDP-B` (etherCON, Ø24.2 seat):

| | current (teardrop + printed thread) | candidate (round + plain bore) |
|---|---|---|
| Rendered image | `scratchpad/roundholes/exports/wallcut/teardrop_view.png` | `scratchpad/roundholes/exports/wallcut/round_view.png` |
| Mesh facets | 11,484 | 5,708 |
| `csg_to_step.py` result | `ok=True valid=True volume=8870.3 mesh=8871.6` (0.015% diff) | `ok=True valid=True volume=8952.5 mesh=8954.3` (0.02% diff) |
| STEP total faces | 4,929 | 1,006 |
| STEP **cylindrical** faces | 8 (the round *portion* of the teardrops arc-fits correctly — D39 is doing its job) | **4** — exactly the seat hole, the window, and the two fixing bores, one clean analytic face each |
| STEP **conical** faces | 0 | **2** — exactly the two bore lead-in chamfers |
| STEP **polyhedron-derived faces** | 2 real M3×0.5 threads → the bulk of the 4,929 (each ≈2,500 tiny faces, confirmed by a location-scoped face query — the thread's radius genuinely oscillates 1.37↔1.65 mm every 0.5 mm of depth, a real helix, not a facet artefact) | 0 |
| STEP file size | 271,122 entities | 74,890 entities |

The rendered images make the point without needing CAD software: the teardrop has a visibly flattened,
pointed top; the round candidate is a clean circle. Both were produced with the identical seat/window
diameters and the identical 5 mm wall — the only variable is the hole shape.

**Conclusion: D39's exact converter already does everything it can — the round *part* of a teardrop
already arc-fits to a true circular arc. The teardrop is still not round because it genuinely isn't a
circle, and the fixing bore is still faceted because it genuinely is a helical thread. Fixing the
*shape*, not the exporter, is the only way to satisfy "perfectly round."**

### 1.3 Evidence — a plain round hole in the vertical patch wall prints clean, no mitigation needed

Sliced both coupon variants above (same wall, same pose — standing on a foot, exactly
`neutrik-tile.scad`'s own orientation) with the Bambu Studio CLI, the repo's own process overrides
(5 walls, 8 mm outer brim), X1C 0.4 + Bambu ASA:

```
teardrop: slicer-check ok=True warnings=[]
round:    slicer-check ok=True warnings=[]
```

**Zero Bambu Studio warnings for the plain round hole, tested at the largest (worst-case) connector
class.** A second render at the smallest class (`NAHDMI-W-B`, Ø23.6, 23.6-class) produced a lighter
mesh (5,136 vs 5,708 facets) — strictly less overhang than the etherCON case already tested, so it is
expected to pass as well and does not need a separate slicer-check to be confident of that. This directly
answers the coordinator's printability question: **no mitigation is required.** The reasons the
"24 mm arch" concern in the current code comment doesn't actually trip Bambu's detector here:
- The wall is only 5 mm thick in the bore's own axial direction, so each "layer disk" of the horizontal
  bore is thin and the print head clears it quickly (little time to droop before the next layer locks it in).
- A circle's overhang grows *continuously* toward its apex (unlike a flat-roofed rectangular slot), so
  Bambu's per-layer "reach beyond the layer below" never jumps sharply — the empirically measured last-layer
  chord width before the hole closes is only a few mm, not the full 24 mm diameter.
- This matches this repo's own stated debugging philosophy (`bambu-slicer.md` §1): *"Do not reason from
  first principles; measure with the slicer."* It was measured, twice, and came back clean both times.

Considered and **rejected as unnecessary**, given the clean result above: a sacrificial bridge layer,
enlarging the hole, and changing the base's print pose. All three add cost/complexity or blast radius
(a pose change touches every other feature's overhang analysis) for a problem the evidence says doesn't
exist. If a *future* connector class needs a materially larger hole than any in `MCC_PANEL_PARTS` today,
re-run `slicer-check` on it before assuming the same conclusion holds.

### 1.4 Not reproduced in this pass (cheap follow-up, not blocking)

The "ribs visible through two of the four holes" half of the specialist's observation was not
independently re-rendered against the full assembled base in this pass (time-boxed; the wall-cut
geometry evidence above is unambiguous and higher-priority). It is a plausible, low-risk explanation and
requires no design change either way — a round hole makes the case interior *more* visible through it,
not less, so it doesn't change any decision in this plan. If confirmation is wanted before sign-off,
render `models/pro-convert-for-ndi-to-hdmi/case.scad -D part="base"` and take an outside elevation of
the patch wall (camera roughly `--camera=0,-400,75,0,0,25.5`) — cheap, not on this plan's critical path.

---

## 2. Chosen approach and rejected alternatives

### 2.1 Round holes (decision 1)

**Chosen: replace `teardrop2d(...)` with a plain `circle(...)` for both the seat hole and the body
window.** Proven in §1.2/§1.3: renders clean, slices with zero warnings at the worst-case diameter,
exports as one true analytic cylindrical STEP face per opening. No geometry beyond the hole profile
itself changes — same diameters, same Z-span, same asserts except the ones that only meant something
for a teardrop (§3).

Rejected:
- **Keep the teardrop, only "improve" the STEP export of it.** Rejected outright — the user's own words
  are "perfectly round... in the model, the STL and the STEP." A teardrop is not round in any of the
  three regardless of export fidelity (§1.2). This was the previous researcher framing of the ticket and
  it no longer applies.
- **Bigger hole / sacrificial bridge layer / different print pose.** Rejected as unneeded overhead —
  §1.3's clean slicer-check result removes the reason to consider them. Recorded here only so nobody
  re-opens this without re-measuring first.

### 2.2 Remove the printed thread (decision 2)

**Chosen: a plain, unthreaded cylindrical bore, Ø2.5 mm (`MCC_FIXING_BORE_D`, the ISO metric tap-drill
size for M3×0.5), with a small 0.5 mm 45° lead-in chamfer at the seat-face mouth (`MCC_FIXING_BORE_CHAMFER`,
reusing the old thread's own chamfer depth and its BOSL2-default rationale).** Proven in §1.2: exports as
one true analytic cylindrical face plus one true conical face (the chamfer) — csg_to_step.py needs no
help at all for a plain bore, since it's already just a `cylinder()`/`cyl()` primitive.

The bore is **not** threaded in the printed part any more — self-tapping or hand-tapping before assembly
is a separate, unresolved question (see Open Questions §8.1) that this plan deliberately does not guess
at, matching the coordinator's brief ("the specialist models the thread himself in CAD").

Rejected:
- **Keep `mcc_thread_pad()`/the real BOSL2 thread, just make the STEP export prettier.** Rejected for the
  same reason as §2.1 — `csg_to_step.py`'s own docstring is explicit that a `polyhedron` (which is what a
  BOSL2 VNF thread compiles to) stays faceted by design; there is no "exact" representation of a printed
  thread's helical flank that isn't itself a polyhedron. Only removing the thread produces a true cylinder.
- **BOSL2 `screw_hole()` with a cheap thread profile, or a lower-`$fn` thread.** Still a `polyhedron` in
  the CSG tree; still faceted in the exact STEP; still the thing the user rejected ("the thread with those
  little triangles is really bad").
- **A metadata-driven "plug and recut" STEP post-process** (the original ticket's approach (a)). Explored
  and prototyped against the *old* mesh-based STEP pipeline before this ticket's scope changed (see the
  researcher's own scratch prototype, `scratchpad/roundholes/recut_holes.py` — it works, but only after
  correcting a real bug found empirically: an oversized "plug" leaves a permanent material "collar" equal
  to `(plug_diameter − design_diameter)/2` in radial thickness, and shrinking that margin too far broke
  the boolean into 9 disconnected solids on this exact mesh). **Moot** now that D39 exists: the exact CSG
  path already gives a true cylinder for free, with none of that margin-tuning risk, for any plain
  `cylinder()`/`circle()` feature. Do not resurrect this approach.

### 2.3 Why `mcc_thread_pad()` is deleted outright, not renamed

The parallel-ticket framing in the original brief ("a parallel change turns those into plain Ø2.5 mm
bores") assumed `mcc_thread_pad()` was still the live production path (via a `mcc_neutrik_d_bosses()`
that no longer exists post-D36). **Verified by grep against current `main`: `mcc_thread_pad()` has zero
production callers today.** D36's `mcc_neutrik_d_wall_cut()` already re-implemented its own inline
`screw_hole()` call rather than reusing it, because the wall-cut has no separate "pad" shape to hang a
thread off any more (screws bite the wall itself). `mcc_thread_pad()`'s only remaining callers are
`tests/test_neutrik.scad` and `models/coupons/m3-thread-ladder.scad` — both retired by this same plan
(§4.1). There is nothing left to rename; delete it.

---

## 3. Exact code changes

### 3.1 `lib/mcc/constants.scad`

**Delete** these two constants and their comment blocks (currently just above the "Printed M3 threads"
section — the block starting `// Rev 6 (2026-09-08) aperture-shape constants` keeps
`MCC_PANEL_BEZEL_T`, `MCC_WALL_THREAD_WEB_MIN` [renamed below], `MCC_APERTURE_LIP_WEB_MIN`, and
`MCC_INSERT_BORE_EXTRA` — only the two teardrop-specific ones go):

```
MCC_APERTURE_BRIDGE_MAX = 10.0; // max unsupported horizontal span anywhere in the patch-wall
                          // aperture, mm — the one place architecture.md §5's "no unsupported
                          // horizontal span over 10 mm anywhere in the shell" becomes a number.
                          // Used by T1-34a (window apex flat-bridge width w_flat).
MCC_APERTURE_CAP_RISE = 0.4; // assumed -- how far the truncated-teardrop cap sits above the body
                          // circle's own top, mm: cap_h = d_win/2 + MCC_APERTURE_CAP_RISE. Chosen as
                          // the smallest rise that still hides the cap behind the plate
                          // (cap_h > mcc_cutout_d(part)/2, margin 0.7 mm) while keeping w_flat under
                          // MCC_APERTURE_BRIDGE_MAX. Calibrate with the neutrik-tile coupon.
```

**Rename** (same value, same line position) `MCC_WALL_THREAD_WEB_MIN` → `MCC_WALL_BORE_WEB_MIN`. New
comment:
```openscad
MCC_WALL_BORE_WEB_MIN = 1.2; // assumed -- minimum wall between a connector's fixing bore (at its
                          // widest, including its lead-in chamfer) and the seat hole / body window
                          // beside it, mm (D36/D41, T1-48): three 0.4 mm perimeters. The screws sit
                          // 15.3 mm from the connector centre on a 24 mm hole, so this is the
                          // tightest web in the patch wall; only a sliver of each bore's
                          // circumference is this thin. Renamed from MCC_WALL_THREAD_WEB_MIN (D41):
                          // the fixing bore is no longer threaded, so "THREAD" no longer describes it.
```

**Replace** the entire "Section: Printed M3 threads" block — from the comment line
`// Section: Printed M3 threads (connector fixing, GitHub issue #30) -- the connector's own two` through
the line `MCC_THREAD_FAST = false; // when true (-D MCC_THREAD_FAST=true only -- NEVER the default), the`
and its full trailing multi-line comment ending `// release/coupon/print export.` (i.e. delete
`MCC_THREAD_M3_MINOR_D`, `MCC_THREAD_M3_PITCH`, `MCC_THREAD_M3_SLOP`, `MCC_THREAD_M3_PAD_D`,
`MCC_THREAD_M3_PAD_H`, `MCC_THREAD_WALL_MIN`, `MCC_THREAD_ENGAGE_MIN_TURNS`,
`MCC_THREAD_ENGAGE_MIN_RADIAL`, `MCC_THREAD_FAST` — confirmed by grep, no consumer survives outside this
plan's own deleted files) — with:

```openscad
// -----------------------------------------------------------------------------------------
// Section: Connector-fixing bore (D36 wall-mounted fixing; D41, 2026-09-28 -- plain tap-drill,
// not a printed thread). The connector's own two screw holes (MCC_D_SCREW_PITCH diagonal) pass
// straight through the patch wall as a plain, unthreaded bore -- the specialist threads it
// himself from the STEP export (user decision 2026-09-28: "the thread with those little
// triangles is really bad"). NOT the plate's own retention bosses -- there is no plate (D36).
// -----------------------------------------------------------------------------------------

MCC_FIXING_BORE_D = 2.5; // plain bore diameter, mm -- ISO metric tap-drill size for M3x0.5 (major
                          // diameter 3.0 minus pitch 0.5), standard machinist tap-drill practice,
                          // not project-sourced. confidence: assumed (standard reference figure;
                          // no coupon has measured it against this printer/ASA combination -- see
                          // Open Questions).
MCC_FIXING_BORE_CHAMFER = 0.5; // lead-in chamfer depth at the bore's seat-face mouth, mm, at 45
                          // deg. Numerically the same as the old thread's own lead-in
                          // (ex-MCC_THREAD_M3_CHAMFER; BOSL2 screw_hole()'s own bevelsize default
                          // is the thread pitch, 0.5 for M3x0.5 -- kept for continuity even though
                          // this bore is no longer threaded). assumed -- generic small-bore
                          // chamfer practice, cosmetic/assembly aid, not load-bearing. 0 omits it.
```

**Add**, immediately after the existing `MCC_M8_CLR_D` constant block (in "Section: Heat-set inserts,
fasteners, magnets" — find the comment ending `... docs/plans/2026-09-09-mount-rail-and-brackets.md
§3.1, VESA MIS-F spec via Wikipedia). Reused for both bolt sizes rather than adding a third clearance
constant that would only drift from this one.`):

```openscad

MCC_M3_MAJOR_D = 3.0; // M3 nominal major diameter, mm. Fixed mechanical standard (ISO metric
                       // coarse). Renamed from MCC_THREAD_M3_MAJOR_D (D41): this is a generic
                       // fastener constant, not specific to the (now-retired) printed thread.
                       // Reused by models/brackets/arch-tv-bracket.scad's own M3-engagement assert
                       // — its only other consumer, confirmed by repo-wide grep.
```

### 3.2 `lib/mcc/neutrik.scad`

Remove the now-unused BOSL2 include (nothing in this file calls `screw_hole()` any more once both
changes below land). Change:
```
include <BOSL2/std.scad>
include <BOSL2/screws.scad>
include <constants.scad>
use <util.scad>
use <layout.scad> // mcc_aperture_window() (L0)
```
to:
```
include <BOSL2/std.scad>
include <constants.scad>
use <util.scad>
use <layout.scad> // mcc_aperture_window() (L0)
```

**Delete** the entire `mcc_thread_pad()` module — from its `// Module: mcc_thread_pad()` doc comment
through its closing `}` (the block ending `screw_hole(str("M3,", pad_h + 2 * MCC_EPS), thread = true,
tolerance = "6H", $slop = slop, bevel2 = true, anchor = BOTTOM, $fn = 32); } }`). Nothing calls it after
§4.1/§4.5 of this plan land.

**Replace** the entire `mcc_neutrik_d_wall_cut()` module (from its `// Module: mcc_neutrik_d_wall_cut()`
doc comment through its closing `}`) with:

```openscad
// Module: mcc_neutrik_d_wall_cut()
// Usage:
//   mcc_neutrik_d_wall_cut(part, [wall_t=], [seat_t=]);
// Description:
//   SUBTRACTIVE. Everything a Neutrik D-series connector needs from a wall it is mounted in
//   DIRECTLY -- no separate panel plate (architecture.md §5 rev 14, D36):
//     * the flange-seat hole through the first `seat_t` of wall (the connector's own
//       mcc_cutout_d(part)), and the body window behind it through the rest of the wall
//       (mcc_aperture_window(part), a little larger) -- both PLAIN CIRCLES, coaxial
//       (architecture.md §5 rev 15, D40, user decision 2026-09-28: perfectly round, no teardrop —
//       supersedes the rev-14 truncated-teardrop shape; proven to slice without a Bambu Studio
//       warning at the largest connector class, see the D40 plan's §1.3);
//     * two plain cylindrical fixing bores on the standard diagonal (front view A(-9.5, +12) /
//       B(+9.5, -12), knowledge/neutrik/d-series-cutout.md:47,62-63) straight through the whole
//       wall, tap-drill sized for M3x0.5 (MCC_FIXING_BORE_D) with a small lead-in chamfer at the
//       seat-face mouth -- NOT threaded (architecture.md §5 rev 15, D41, user decision
//       2026-09-28: an external CAD specialist threads the bore himself from the STEP export).
//       There are NO screw pillars: the bore goes straight through the wall the connector sits in.
//   Local frame: X/Y is the wall face as seen FROM OUTSIDE (Y = up), Z = outward normal. The seat
//   (front) face is Z = 0 and the wall runs to Z = -wall_t (inside face). The cut reaches MCC_EPS
//   past both faces.
//   Asserts: seat_t within the part's max panel thickness; wall_t > seat_t; at least
//   MCC_WALL_BORE_WEB_MIN of wall between each fixing bore's widest point (bore + chamfer) and
//   either opening (T1-48).
//   $fn: both circles and the bore/chamfer are $fn=96/64 + circum=true, the repo's normal policy —
//   no exception. (The old $fn=32 screw_hole() exception is retired along with the thread,
//   architecture.md §3 — a plain cyl() bore has no such restriction.)
// Arguments:
//   part   = panel part number, key into MCC_PANEL_PARTS (constants.scad).
//   wall_t = total wall thickness at the connector, mm. Default: MCC_PANEL_SEAT_T + MCC_WALL.
//   seat_t = flange-seat thickness (the part of the wall the flange clamps), mm.
//            Default: MCC_PANEL_SEAT_T.
module mcc_neutrik_d_wall_cut(part, wall_t = MCC_PANEL_SEAT_T + MCC_WALL, seat_t = MCC_PANEL_SEAT_T) {
    is_blank = mcc_panel_hole_d(part) == 0;
    d_seat = mcc_cutout_d(part);
    d_win = mcc_aperture_window(part);
    sx = MCC_D_SCREW_PITCH[0] / 2; sy = MCC_D_SCREW_PITCH[1] / 2;
    screws = [[-sx, sy], [sx, -sy]]; // front view (knowledge/neutrik/d-series-cutout.md:62-63)
    bore_r = (MCC_FIXING_BORE_D + 2 * MCC_FIXING_BORE_CHAMFER) / 2; // widest point of the bore

    assert(seat_t <= mcc_panel_max_t(part) + MCC_EPS,
        str("mcc: seat_t=", seat_t, " exceeds max panel thickness ", mcc_panel_max_t(part), " for \"", part, "\""));
    assert(wall_t > seat_t, str("mcc: wall_t=", wall_t, " must exceed seat_t=", seat_t));
    if (!is_blank) {
        seat_path = circle(d = d_seat, $fn = 96);
        win_path = circle(d = d_win, $fn = 96);
        for (sc = screws) {
            web = min(_mcc_path_dist(sc, seat_path), _mcc_path_dist(sc, win_path)) - bore_r;
            assert(web >= MCC_WALL_BORE_WEB_MIN - MCC_EPS,
                str("mcc: T1-48 wall web between the fixing bore at ", sc, " and the opening is ", web,
                    " mm, below MCC_WALL_BORE_WEB_MIN=", MCC_WALL_BORE_WEB_MIN, " for \"", part, "\""));
        }
    }

    union() {
        if (!is_blank) {
            translate([0, 0, -seat_t - MCC_EPS])
                linear_extrude(height = seat_t + 2 * MCC_EPS)
                    circle(d = d_seat, $fn = 96);
            translate([0, 0, -wall_t - MCC_EPS])
                linear_extrude(height = wall_t - seat_t + 2 * MCC_EPS)
                    circle(d = d_win, $fn = 96);
        }
        for (sc = screws)
            translate([sc[0], sc[1], -wall_t - MCC_EPS])
                union() {
                    // anchor=BOTTOM at the inside face; the bore is a genuine through-hole, open at
                    // both faces -- same Manifold coincident-face reasoning as every other bored
                    // boss in this repo (architecture.md §13 D10).
                    cyl(h = wall_t + 2 * MCC_EPS, d = MCC_FIXING_BORE_D, circum = true, anchor = BOTTOM, $fn = 64);
                    if (MCC_FIXING_BORE_CHAMFER > 0)
                        translate([0, 0, wall_t - MCC_FIXING_BORE_CHAMFER])
                            cyl(h = MCC_FIXING_BORE_CHAMFER + MCC_EPS, d1 = MCC_FIXING_BORE_D,
                                d2 = MCC_FIXING_BORE_D + 2 * MCC_FIXING_BORE_CHAMFER,
                                circum = true, anchor = BOTTOM, $fn = 64);
                }
    }
}
```

Leave `mcc_neutrik_d_cutout()` (the flat-panel/coupon-only cutout, used by `depth-mockup.scad` — it has
no thread/pad and is untouched by either decision), `_mcc_seg_dist()`, `_mcc_path_dist()`,
`mcc_neutrik_d_flange_outline()`, and `mcc_neutrik_d_envelope()` exactly as they are.

### 3.3 `lib/mcc/layout.scad`

**Replace** `mcc_aperture_window()`'s doc comment and body. Current:
```openscad
// Function: mcc_aperture_window()
// Usage:
//   aw = mcc_aperture_window(part);
// Description:
//   The body window through the patch wall BEHIND the flange seat for panel part `part` (D36: the
//   connector sits in the wall itself — mcc_neutrik_d_wall_cut()): a round opening a little larger
//   than the seat hole, truncated-teardropped above its 45 deg tangent line so it prints standing.
//   Returns [d_win, cap_h, w_flat]:
//     d_win  = window diameter, mm (mcc_cutout_d(part) + 2*MCC_CLR_SLIDE).
//     cap_h  = truncated-teardrop cap height above the centre, mm (d_win/2 + MCC_APERTURE_CAP_RISE).
//     w_flat = the cap's flat bridge width, mm (<= MCC_APERTURE_BRIDGE_MAX, T1-34a).
//   All three read 0 for a genuinely solid blank (mcc_panel_hole_d(part) == 0; none today —
//   DBA-BL-B carries a full hole, D18).
// Arguments:
//   part = panel part number, key into MCC_PANEL_PARTS (constants.scad).
function mcc_aperture_window(part) =
    let(
        is_blank = mcc_panel_hole_d(part) == 0,
        d_win = is_blank ? 0 : mcc_cutout_d(part) + 2 * MCC_CLR_SLIDE,
        cap_h = is_blank ? 0 : d_win / 2 + MCC_APERTURE_CAP_RISE,
        w_flat = is_blank ? 0 : 2 * (d_win / 2 * sqrt(2) - cap_h)
    )
    [d_win, cap_h, w_flat];
```
with:
```openscad
// Function: mcc_aperture_window()
// Usage:
//   d_win = mcc_aperture_window(part);
// Description:
//   The body window through the patch wall BEHIND the flange seat for panel part `part` (D36: the
//   connector sits in the wall itself — mcc_neutrik_d_wall_cut()): a plain round opening a little
//   larger than the seat hole (architecture.md §5 rev 15, D40 — perfectly round, no teardrop, user
//   decision 2026-09-28). Returns d_win = mcc_cutout_d(part) + 2*MCC_CLR_SLIDE, or 0 for a
//   genuinely solid blank (mcc_panel_hole_d(part) == 0; none today — DBA-BL-B carries a full hole,
//   D18). Simplified from a 3-element [d_win, cap_h, w_flat] list (rev 14/D36) now that there is no
//   teardrop cap to describe.
// Arguments:
//   part = panel part number, key into MCC_PANEL_PARTS (constants.scad).
function mcc_aperture_window(part) =
    mcc_panel_hole_d(part) == 0 ? 0 : mcc_cutout_d(part) + 2 * MCC_CLR_SLIDE;
```

**Update** the T1-34c assert (the `apertures = [for (i = ...) mcc_aperture_window(...)]` block, a few
lines below). Current:
```openscad
        apertures = [for (i = [0:1:n_slots - 1]) mcc_aperture_window(struct_val(slots_assigned[i], "part"))],
        _t134c_check = [for (i = [0:1:n_slots - 1])
            assert(apertures[i][1] + MCC_APERTURE_LIP_WEB_MIN <= MCC_PLATE_H / 2 + MCC_EPS,
                str("mcc: T1-34c aperture cap containment fails for slot ", i + 1, " on \"", mcc_dev_slug(dev), "\""))
            0],
```
to (only the assert's left-hand side changes — `apertures[i][1]` [cap_h] becomes `apertures[i] / 2`
[the plain circle's own top, since there is no cap rising above it any more]):
```openscad
        apertures = [for (i = [0:1:n_slots - 1]) mcc_aperture_window(struct_val(slots_assigned[i], "part"))],
        _t134c_check = [for (i = [0:1:n_slots - 1])
            assert(apertures[i] / 2 + MCC_APERTURE_LIP_WEB_MIN <= MCC_PLATE_H / 2 + MCC_EPS,
                str("mcc: T1-34c aperture containment fails for slot ", i + 1, " on \"", mcc_dev_slug(dev), "\""))
            0],
```
(`apertures` is still a list over slots — only what each element *is* changed, from a 3-tuple to a bare
number. `MCC_PLATE_H`, `MCC_APERTURE_LIP_WEB_MIN` are untouched constants, still current/meaningful —
`MCC_PLATE_H` is the vertical band reserved around the connector centreline in the patch wall, a concept
that survived D36 unchanged in name.)

### 3.4 `models/brackets/arch-tv-bracket.scad`

This file has its own, unrelated M3 boss that reuses the generic M3 major-diameter constant — rename
only, do not touch its geometry or its own assert logic.

Change:
```
// reused from constants.scad, no new library constant: MCC_M8_CLR_D, MCC_M3_CLR_D, MCC_INSERT_M3,
// MCC_CLR_SLIDE, MCC_RAIL_*, MCC_FLOOR_T, MCC_WALL, MCC_BUILD, MCC_BED_MARGIN, MCC_EPS,
// MCC_THREAD_M3_MAJOR_D, MCC_RIB_HEIGHT_RATIO_MAX, MCC_RAIL_Y.
```
to:
```
// reused from constants.scad, no new library constant: MCC_M8_CLR_D, MCC_M3_CLR_D, MCC_INSERT_M3,
// MCC_CLR_SLIDE, MCC_RAIL_*, MCC_FLOOR_T, MCC_WALL, MCC_BUILD, MCC_BED_MARGIN, MCC_EPS,
// MCC_M3_MAJOR_D, MCC_RIB_HEIGHT_RATIO_MAX, MCC_RAIL_Y.
```

Change (both occurrences, same assert, use `replace_all`):
```
MCC_THREAD_M3_MAJOR_D
```
to:
```
MCC_M3_MAJOR_D
```
(Confirmed by repo-wide grep: this is the only other consumer of the old name. No other file
references it.)

### 3.5 `tests/test_neutrik.scad`

Replace the whole file body (everything between the `include <mcc/mcc.scad>` line and the closing
`echo("mcc test_neutrik: OK");` / manual-check comment block) with:

```openscad
// --- Default parameters -------------------------------------------------------------------
mcc_neutrik_d_cutout("NE8FDP-B");
mcc_neutrik_d_flange_outline();

// --- Minimum-ish parameters: seat_t == panel_t (no rear pocket cut at all) -----------------
translate([40, 0, 0])
    mcc_neutrik_d_cutout("NAHDMI-W-B", mirror = true, seat_t = 1.0, panel_t = 1.0);

// --- Maximum-ish parameters: etherCON at its full 4 mm panel-thickness rating --------------
translate([80, 0, 0])
    mcc_neutrik_d_cutout("NE8FDP-B", mirror = false, seat_t = 2.0, panel_t = 4.0);

// --- Wall-integrated connector cut (D36/D40/D41): every part class at the production wall
// (seat 2 + lip 3), the blank, and the thinnest wall that still passes T1-48. Round seat/window,
// plain tap-drill fixing bore -- no teardrop, no thread. Differenced from a block so the cuts
// render as real negatives. -----------------------------------------------------------------
for (i = [0:1:3])
    translate([i * 40, 60, 0])
        difference() {
            translate([0, 0, -2.5]) cube([36, 40, 5], center = true);
            mcc_panel_wall_cut(["NE8FDP-B", "NAHDMI-W-B", "NAUSB-W-B", "DBA-BL-B"][i], wall_t = 5);
        }

// Thinnest wall_t that still keeps T1-48 satisfied at MCC_FIXING_BORE_D + 2*MCC_FIXING_BORE_CHAMFER
// -- NBB75DFGB (largest 23.6-class relevant here), seat_t reduced to 1.0.
translate([0, 110, 0])
    mcc_neutrik_d_wall_cut("NBB75DFGB", wall_t = 3.0, seat_t = 1.0);

echo("mcc test_neutrik: OK");

// -----------------------------------------------------------------------------------------
// Manual check: deliberately-bad seat thickness (architecture.md:343 Tier-1 assert "panel seat
// thickness <= mcc_panel_max_t(part)"). OpenSCAD has no "expect this render to fail" mechanism,
// so this cannot be asserted automatically in a render that must otherwise succeed. To verify the
// guard by hand, append the following line to a scratch copy of this file and confirm the render
// FAILS (non-zero exit, an ERROR naming "seat_t=3 exceeds max panel thickness 2 for
// \"NAHDMI-W-B\"") — NAHDMI-W-B's max_panel_t is 2.0 mm
// (knowledge/neutrik/d-series-cutout.md:90 "max. 2 mm"), so a requested 3 mm seat must be
// rejected:
//
//   mcc_neutrik_d_cutout("NAHDMI-W-B", seat_t = 3.0, panel_t = 3.0);
// -----------------------------------------------------------------------------------------
```

Also update the file's own header doc comment (top of file) — change:
```
//   L2. The composition root...
```
(N/A — this file's own header is the one starting `// tests/test_neutrik.scad` / `//   Tier-2 headless
smoke test...`). Change:
```
//   L2. Tier-2 headless smoke test (architecture.md §9). Instantiates mcc_neutrik_d_cutout(),
//   mcc_thread_pad() and the wall-integrated mcc_neutrik_d_wall_cut() / mcc_panel_wall_cut() (D36)
//   at default, minimum, and maximum parameters.
```
to:
```
//   Tier-2 headless smoke test (architecture.md §9). Instantiates mcc_neutrik_d_cutout() and the
//   wall-integrated mcc_neutrik_d_wall_cut() / mcc_panel_wall_cut() (D36, round holes/plain bore
//   per D40/D41) at default, minimum, and maximum parameters.
```

### 3.6 Delete outright

- `models/coupons/m3-thread-ladder.scad`
- `tests/golden/coupons/m3-thread-ladder.json`

No entry in `scripts/build.py` names this coupon directly — `discover_coupons()` globs
`models/coupons/*.scad`, so deleting the file is sufficient. Do not edit `scripts/build.py`'s
discovery logic or `.github/workflows/render.yml` — `group_units()` rebalances the six CI groups
automatically from whatever `discover_all()` returns (confirmed: no static per-group part list
anywhere).

### 3.7 No code change needed (verify only)

- `lib/mcc/panel.scad` — `mcc_panel_wall_cut()`'s signature (`part, wall_t, seat_t`) is unchanged; it
  already has no `fast` parameter to remove (only `mcc_neutrik_d_wall_cut()` had one, and only
  `tests/test_neutrik.scad` called it directly with `fast=`, fixed in §3.5).
- `models/coupons/neutrik-tile.scad` — calls `mcc_panel_wall_cut(connector, wall_t = WALL_T)` with no
  `fast` argument; picks up the round hole + plain bore automatically. Its **golden moves** (§5).
- `lib/mcc/shell.scad` — `_mcc_patch_wall_aperture()` calls `mcc_panel_wall_cut(struct_val(slots[i],
  "part"), wall_t = wall_t)`; unaffected.
- `scripts/csg_to_step.py`, `scripts/mesh_to_step.py`, `scripts/bambu_project.py` — no changes. Proven
  sufficient as-is (§1.2, §2).

---

## 4. New CI check: fail if a connector hole in a STEP is not a cylinder

D39 already makes plain circles/cylinders exact, and §1.2/§3 remove the two shapes that weren't
(teardrop, thread). But nothing today *asserts* that a future change can't quietly reintroduce a
non-round hole or a silent fallback to the faceted converter — a regression there would still pass
`build.py ci` today, because `csg_to_step.py`'s only built-in check is a ±1% **volume** match against the
mesh, and a badly-shaped-but-similarly-sized hole (or a correctly-shaped hole that silently fell back to
the faceted converter) would still pass that. Add one.

### 4.1 `scripts/build.py` — capture the slot count at render time

In `render_part()`, immediately after `ok, lines = run_openscad(...)` (the call that already captures
OpenSCAD's stdout as `lines`), add:

```python
    n_connector_slots = None
    if target.kind == "model" and part in ("base", "base_fan"):
        # every models/<slug>/case.scad echoes "<slug>: slots=[[...["part", "X"]...]]" UNCONDITIONALLY
        # at file scope -- it fires for every part= value, including "lid", so the part-name guard
        # above is required; counting '["part",' occurrences (once per connector slot) is robust to
        # the exact surrounding echo text without needing a regex over the whole bracketed structure.
        n_connector_slots = sum(ln.count('["part",') for ln in lines) or None
```

Place this block immediately after `ok, lines = run_openscad(...)` and before the `if release:` block.
**Do not gate this only on the echo text being present** — `case.scad`'s `slots=` echo is unconditional
at file scope, so it appears in the captured `lines` for *every* part value of a given SKU (`base`,
`lid`, `base_fan`, ...); without the explicit `part in ("base", "base_fan")` guard, `lid`'s own render
would also get a nonzero `n_connector_slots` and the check in §4.2 would then wrongly demand cylindrical
connector-hole faces from a part that cuts no connector holes at all.
Then, where `summary` is built and written a few lines down (`summary = json.loads(...)`,
`summary["mesh_volume_mm3"] = ...` etc.), add one more line in the same block:
```python
    if n_connector_slots:
        summary["n_connector_slots"] = n_connector_slots
```
(Guard with `if n_connector_slots` so coupons/brackets, whose parts never echo a `slots=` line, don't
get a spurious `0` — `sum(...) or None` already makes this `None` for them, so the `if` is just belt and
suspenders and keeps the summary JSON free of a meaningless `0` key.)

### 4.2 `scripts/build.py` — the check itself

Add a new function, next to `golden_check_part()`:

```python
_STEP_SUMMARY_RE = re.compile(r"\bcylindrical=(\d+)\b.*\bconical=(\d+)\b")


def round_holes_step_check(target: Target, part: str) -> list[str]:
    """[] when this part's STEP export has at least the expected number of true cylindrical/conical
    faces for its connector holes (4 cylindrical + 2 conical per slot: seat, window, 2 fixing bores,
    2 lead-in chamfers -- architecture.md §5 rev 15, D40/D41) and did NOT silently fall back to the
    faceted converter. Only meaningful for a model's "base"/"base_fan" part (the only parts with
    connector slots since D36); returns [] immediately for anything else."""

    summary_path = target.export_dir / f"{part}.summary.json"
    manifest_path = target.export_dir / f"{part}.manifest.json"
    if not summary_path.exists() or not manifest_path.exists():
        return [f"no summary/manifest for {target.name}:{part} -- run render+step first"]
    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    n_slots = summary.get("n_connector_slots")
    if not n_slots:
        return []  # not a connector-bearing part (a coupon, bracket, lid, or a case's "lid")

    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    step_info = manifest.get("step", {})
    errors: list[str] = []
    if step_info.get("backend") != "csg-exact":
        errors.append(f"STEP fell back to '{step_info.get('backend')}' instead of the exact CSG "
                      f"path -- a connector hole would be faceted (why_not_exact: "
                      f"{step_info.get('why_not_exact')!r})")
        return errors  # face counts below are meaningless on a faceted fallback

    m = _STEP_SUMMARY_RE.search(step_info.get("summary", ""))
    if not m:
        return [f"could not parse cylindrical/conical face counts from step summary: "
                f"{step_info.get('summary')!r}"]
    cylindrical, conical = int(m.group(1)), int(m.group(2))
    if cylindrical < 4 * n_slots:
        errors.append(f"only {cylindrical} true cylindrical STEP faces for {n_slots} connector "
                      f"slots (expected >= {4 * n_slots}: seat + window + 2 fixing bores per slot) "
                      f"-- a hole may not be a plain circle any more")
    if conical < 2 * n_slots:
        errors.append(f"only {conical} true conical STEP faces for {n_slots} connector slots "
                      f"(expected >= {2 * n_slots}: 1 lead-in chamfer per fixing bore) -- a bore's "
                      f"chamfer may be missing or malformed")
    return errors
```

(`>=` not `==` — other legitimate round/conical features elsewhere in the base, e.g. heat-set insert
chamfers, must never make this check fail; it is a floor, not an exact count.)

### 4.3 `scripts/build.py` — wire it into the CI pipeline

In `cmd_ci()`'s `_pipeline()` closure, immediately after the existing block:
```python
        if not args.no_step:
            proc = subprocess.run(...)
            if proc.returncode != 0:
                errors.append("step: " + ...)
```
add:
```python
            else:
                errors += [f"round-holes: {m}" for m in round_holes_step_check(target, part)]
```
(Only run the new check when the STEP step itself succeeded — matches the existing pattern for
`golden_check_part()`/the slicer gate right above it in the same function.)

No changes to `.github/workflows/render.yml` — this rides inside the existing per-part pipeline in the
existing six parallel groups; nothing about CI's job structure or timing changes.

### 4.4 Also exercise it locally / in `cmd_step`

Not required for CI (which always runs `cmd_ci`), but for a developer running `build.py step` by hand,
add the same call at the end of `cmd_step()`'s per-part loop (after `_update_manifest_with_step(...)`),
printing any errors returned but not failing the command (`cmd_step` today is a conversion command, not
a gate — keep that contract; `cmd_ci` is the gate).

---

## 5. Tests / goldens to update

Run in order, stop and investigate if anything unexpected diffs (do not `--update` through a surprise):

```
python scripts/build.py doctor
python scripts/build.py smoke
python scripts/build.py render
python scripts/build.py check
python scripts/build.py golden
```

Expect the last command to report diffs on **exactly**: `coupons/neutrik-tile` and all 8 SKUs' `base`
AND `base_fan` (16 golden files:
`pro-convert-hdmi-tx.base.json`/`.base_fan.json`, `pro-convert-sdi-tx.*`, `pro-convert-hdmi-plus.*`,
`pro-convert-sdi-plus.*`, `pro-convert-for-ndi-to-hdmi.*`, `pro-convert-for-ndi-to-hdmi-4k.*`,
`pro-convert-for-ndi-to-sdi.*`, `pro-convert-for-ndi-to-aio.*`). **This is a real difference from the
stale B-plan's assumption** ("only `*.panel.json` moves") — there is no `panel` part any more; the
connectors, and therefore the geometry change, live in `base`/`base_fan` directly. If any `*.lid.json`
diffs, STOP — the lid has no connectors and must not move.

```
python scripts/build.py golden coupons/neutrik-tile \
    pro-convert-hdmi-tx pro-convert-sdi-tx pro-convert-hdmi-plus pro-convert-sdi-plus \
    pro-convert-for-ndi-to-hdmi pro-convert-for-ndi-to-hdmi-4k pro-convert-for-ndi-to-sdi pro-convert-for-ndi-to-aio \
    --update
```
(Verified against `cmd_golden()`: there is **no `--part` flag** — `golden <targets...> --update`
rewrites the golden for *every* part of each named target, including that SKU's `lid`. This is safe
here: `lid` has no connector geometry, so its golden should come back byte-for-byte identical, not
actually change. Re-run `golden` with no `--update` afterward and read `git diff -- tests/golden/` —
confirm it shows changes **only** in `coupons/neutrik-tile.json` and the 16 `*.base.json`/
`*.base_fan.json` files. If any `*.lid.json` shows an actual content diff (not just being touched with
identical content), STOP — that is a real regression, not an expected change.)

```
python scripts/build.py golden        # must be fully clean now
python scripts/build.py slicer-check  # must be zero warnings on every part, matching current status
python scripts/build.py review        # regenerate exports/review.3mf, spot-check no m3-thread-ladder part
python scripts/build.py all --with-step
```

`build.py all --with-step` (or `build.py ci --group k/6` locally per group) is what actually exercises
§4's new `round_holes_step_check()` — confirm it reports clean for all 8 SKUs' `base`/`base_fan`.

---

## 6. Docs to update

### 6.1 Developer-owned (do these directly, same PR)

- `models/coupons/README.md`:
  1. Delete the `m3-thread-ladder.scad` row from "What each coupon verifies".
  2. Delete the `m3-thread-ladder` row from "Orientation (Bambu Studio)".
  3. Delete the entire `### m3-thread-ladder` measurement-form subsection.
  4. `neutrik-tile.scad` row: change "A real Neutrik D-series connector ... drops into a **standing**
     section of the case's patch wall (D36: teardropped seat hole, no panel plate), seats flush, and its
     two M3 screws hold in the horizontal printed threads in the wall (≥5 in/out cycles)" to "... (D36:
     round seat hole and window, no panel plate — D40), seats flush; its two M3 screw shanks line up
     with the horizontal plain Ø2.5 mm tap-drill bores in the wall (D41 — no printed thread; check
     alignment and roundness only, not thread engagement)".
  5. `### neutrik-tile` measurement-form subsection: replace "Do both M3-class screws line up with the
     rear bosses and thread in without cross-threading or stripping the boss?" with "Do both M3-class
     screw shanks line up with the horizontal fixing bores? The bore is a plain Ø2.5 mm tap-drill hole
     (no printed thread, D41) — a stock M3 screw will not thread in directly; check alignment and
     roundness only." Replace the "Record" line below it similarly (fit quality / roundness / alignment,
     not "whether either screw stripped the boss").
  6. `neutrik-tile` "Orientation" row: drop "and horizontal printed M3 threads" (already covered by the
     round-hole/plain-bore rewording above), keep "teardropped hole" → "round hole" if that phrase
     appears there too.
- `BOM.md`:
  1. Change the common-hardware intro sentence (the one starting `*(Connector-count-dependent rows —
     2× M3×10 machine screw per D-connector, threading directly into...`) to describe a plain bore, not
     a thread — e.g. "...passing through a plain Ø2.5 mm bore in the patch wall, no insert (the bore is
     threaded separately before final assembly — see the per-variant tables below)...".
  2. All 8 occurrences (one per SKU section) of the row containing `Through the connector flange into
     the printed M3 thread in the patch wall itself (D36 — 5 mm of wall: 2 mm seat + 3 mm behind it; no
     pads, no inserts)` (2 with qty 6, 5 with qty 8, 1 of the qty-8 rows also has the DBA-BL-B
     parenthetical — keep whichever parenthetical each row already has): change "into the printed M3
     thread in the patch wall itself" to "through a plain Ø2.5 mm bore in the patch wall itself
     (`MCC_FIXING_BORE_D`, no printed thread — threaded separately before final assembly, D41)" — same
     substitution in every row, and drop the `docs/plans/2026-09-09-printed-m3-threads.md` citation in
     favour of `lib/mcc/constants.scad (MCC_FIXING_BORE_D)`.
  3. Delete the `m3-thread-ladder` row from the "Coupon test kit" hardware table (the one requiring "≥5
     spares" of plain M3 screws for thread/unthread cycles).
  4. In "Coupon test kit", change the coupon-count sentence to drop `m3-thread-ladder` from the list
     (mirrors `session-resume.md`'s already-current count, which never included it).
- `.claude/skills/neutrik-panel/SKILL.md`:
  1. Replace the "Seat, fixing and printability" section's bullets on "Holes are truncated teardrops"
     and "Screw fixing" with round-hole/plain-bore equivalents (mirror this plan's §3.2 doc-comment
     wording — do not describe a shape or fastening method the code no longer has).
  2. Drop the `$fn` policy exception sub-bullet entirely (no exception exists any more) and the
     `MCC_THREAD_M3_SLOP`/`MCC_THREAD_FAST` sub-bullets; add one line for `MCC_FIXING_BORE_D` (the new
     load-bearing tuning constant) per this plan's constants-file comment.
  3. In "Asserts that must hold", replace the T1-42b/T1-48 rows with the single surviving T1-48 row
     (web check, `MCC_WALL_BORE_WEB_MIN`) and drop the T1-34a bridge-width row entirely.
  4. In "Coupons — how the placeholder numbers get replaced", delete the `m3-thread-ladder` bullet.
- `.claude/skills/openscad-render/SKILL.md`: the example rendering "a variant's `base` with the fast
  (plain-bore) connector threads and the reservation ghosts on" (`-D 'MCC_THREAD_FAST=true' -D
  'MCC_SHOW_GHOST=true'`) is stale — there is no more fast/real distinction. Drop the
  `-D 'MCC_THREAD_FAST=true'` argument and reword the sentence to just describe the ghost overlay
  example (`-D 'MCC_SHOW_GHOST=true'` alone).
- `CLAUDE.md`, "Fixed decisions" → "Ruggedness" bullet: change "a 2 mm flange seat with a teardropped
  hole, and printed M3 threads in the wall itself — no screw pillars" to "a 2 mm flange seat with a
  **round** hole, and a **plain Ø2.5 mm tap-drill fixing bore** in the wall itself (threaded separately,
  outside this repo's print pipeline) — no screw pillars".

### 6.2 Architect-owned — do not edit these yourself

`architecture.md` and `layout-patch-wall.md` are the `solution-architect`'s own record. Hand this plan
to the architect gate with the following list of what must be recorded (the architect writes the text):

- `architecture.md` §5 rev 14's table (the one added by D36): update the "Seat hole"/"Body window"/
  "Connector fixing" rows to describe a plain circle and a plain tap-drill bore, not a teardrop and a
  printed thread. This is naturally a **rev 15**, since rev 14 is itself only from today.
- `architecture.md` §3's `$fn=32` thread-bore exception bullet: retire it — no `screw_hole()` call
  remains anywhere in the repo for this feature.
- `architecture.md` §9 Tier-1 assert table: replace the T1-42a/b/c row (already describing the
  *pre-D36* pad, itself already stale) and the T1-34a row with: T1-48 (fixing-bore web, unchanged
  formula, renamed constant) as the sole survivor. Confirm/update wherever the running "N topology
  asserts" count is stated in prose.
- `architecture.md` §13: two new deviation/decision rows, next free D-numbers after D39 (**D40, D41**):
  - **D40** — perfectly round D-connector holes (no teardrop), user decision 2026-09-28. Cite this
    plan's §1.2/§1.3 evidence (arc-fitting already works under D39 but the shape itself wasn't round;
    zero Bambu Studio warnings measured at the largest connector class, no mitigation needed).
  - **D41** — printed M3 thread removed, replaced by a plain Ø2.5 mm tap-drill bore
    (`MCC_FIXING_BORE_D`), user decision 2026-09-28. `mcc_thread_pad()` deleted (verified zero
    production callers post-D36); `m3-thread-ladder` coupon retired (its only purpose was calibrating
    the now-deleted `$slop`/thread constants). Note this also resolves/retires D39's own docstring
    caveat about `polyhedron`s staying faceted — there is no polyhedron here any more, so the exact
    STEP path now produces a true cylinder for this feature too.
- `layout-patch-wall.md` §9's assert table: same T1-42/T1-34a retirement, mirrored for consistency
  (repo convention: the two files' assert tables are kept in sync).
- Confirm whether §12's open-questions/measurement list should gain an entry for `MCC_FIXING_BORE_D`
  (uncalibrated tap-drill size — see Open Questions §8.2 below) — the architect's call on whether that
  needs a formal `M`-numbered measurement or is fine as a plain `assumed`-confidence constant.

### 6.3 `docs/plans/` — create the permanent record, after the architect verdict

Once the architect has validated this plan, copy its content (plus the architect's verdict section,
same convention as every other architecture-gated change) into
`docs/plans/2026-09-28-round-holes-no-threads.md`. Do not create it before the verdict is in hand.

---

## 7. Ordered implementation steps

1. `lib/mcc/constants.scad` — §3.1.
2. `lib/mcc/neutrik.scad` — §3.2.
3. `lib/mcc/layout.scad` — §3.3.
4. `models/brackets/arch-tv-bracket.scad` — §3.4.
5. `tests/test_neutrik.scad` — §3.5.
6. Delete `models/coupons/m3-thread-ladder.scad` and `tests/golden/coupons/m3-thread-ladder.json` — §3.6.
7. `scripts/build.py` — §4.1/§4.2/§4.3/§4.4 (the new round-holes STEP check).
8. `python scripts/build.py doctor` then `smoke` — fix any error before proceeding (§5).
9. `python scripts/build.py render`, `check`, `golden` (no `--update`) — confirm the diff set is
   *exactly* `coupons/neutrik-tile` + the 8 SKUs' `base`/`base_fan`, nothing else (§5). If `*.lid.json`
   or any coupon other than `neutrik-tile` moves, STOP.
10. `python scripts/build.py golden ... --update` on exactly that set (§5) then `golden` again with no
    `--update` to confirm fully clean.
11. `python scripts/build.py slicer-check` — zero warnings, matching current status.
12. `python scripts/build.py review` — regenerate, spot-check no `m3-thread-ladder` part remains.
13. `python scripts/build.py all --with-step` (or `ci --group k/6` per group, with `--jobs` as CI uses)
    — confirm green, including the new round-holes check (§4).
14. Docs: `models/coupons/README.md`, `BOM.md`, `.claude/skills/neutrik-panel/SKILL.md`,
    `.claude/skills/openscad-render/SKILL.md`, `CLAUDE.md` — §6.1.
15. Hand `architecture.md`/`layout-patch-wall.md` updates to the architect — §6.2. Do not edit either
    file yourself.
16. After the architect verdict: create `docs/plans/2026-09-28-round-holes-no-threads.md` — §6.3.
17. Re-run `python scripts/build.py all --with-step` once more after the doc edits (steps 14–16 touch no
    `.scad`, so this is a sanity check, not expected to change anything).

---

## 8. Open questions for the user

1. **Who threads the bore, and how, before physical assembly?** Confirmed: the *exported STEP* is
   threaded by the external CAD specialist. Not specified: what happens to a *physically printed* case
   before it reaches that specialist's process — hand-tap the Ø2.5 mm bore with a real M3×0.5 tap, use a
   self-tapping screw into the untapped bore, or does every physically-printed case skip this fastening
   path entirely now? This plan's BOM/coupon wording (§6.1) deliberately avoids asserting an assembly
   process that wasn't specified. Needs a call before the next physical print of any case.
2. **`MCC_FIXING_BORE_D` (2.5 mm) is an ISO reference figure, not yet calibrated against this
   printer/ASA combination.** Unlike `MCC_HOLE_COMP` (calibrated by the `tolerance-ladder` coupon), there
   is no dedicated print-tolerance check for this bore. Is confirming it via a `neutrik-tile` reprint
   sufficient (this plan's assumption), or does it warrant its own small calibration coupon? (The
   `m3-thread-ladder` coupon being retired calibrated `$slop` for a thread that no longer exists — it is
   not a substitute either way.)
3. **Confirm §1.4's "ribs visible through the hole" explanation** is acceptable as an unverified but
   low-risk assumption, or whether a straight-on outside render of the assembled base (cheap, described
   in §1.4) should be produced and checked against the original screenshot before sign-off.
4. **Whether ASA is really what gets threaded downstream** (by the specialist or by hand-tapping) —
   carried over unresolved from the pre-D36 research pass; not this repo's modelling concern, but worth
   confirming with the specialist since it affects whether 2.5 mm is even the right tap-drill figure for
   the material actually being cut.

---

## Architect verdict

# Architect verdict — Plan C: perfectly round D-connector holes, no printed thread

Gate: `solution-architect`, 2026-09-28. Plan: `scratchpad/plans/C-round-holes-no-threads.md`.
Checked against `main` = `origin/main` @ 047902e, `.claude/knowledge/architecture.md` (source of
truth) and `CLAUDE.md`. Plan B (`B-remove-printed-threads.md`) is superseded and gets no verdict.

## Verdict: **APPROVED WITH BINDING CHANGES** (B1–B14; B1, B3 and B5 are blocking as written)

The direction is right and follows both binding user decisions of 2026-09-28:
- plain circles for the seat hole and the body window;
- a plain Ø2.5 bore;
- delete `mcc_thread_pad()` and every `MCC_THREAD_*` constant;
- retire T1-34a, T1-42a/b/c, the §3 `$fn = 32` exception and the `m3-thread-ladder` coupon;
- rename `MCC_THREAD_M3_MAJOR_D` → `MCC_M3_MAJOR_D`;
- `mcc_aperture_window()` returns a scalar;
- drop `include <BOSL2/screws.scad>`. Verified: `neutrik.scad` is the only `screw_hole()` user in `lib/**`, `models/**` and `tests/**`.

No envelope figure moves and no layering rule changes.

As written, though, the plan has four defects. Implement it only as amended below.
- It cannot pass its own smoke test (B1).
- It puts a non-nominal bore diameter into the STEP (B2).
- It reuses an assert id that another file already owns (B3).
- Its CI check would pass the very design it is meant to reject (B5).

### Rulings on the questions asked

1. **Reverting D36's teardrop: approved (D40).**
   - **Printability.** Accepted on the plan's evidence: zero Bambu Studio warnings on a 5 mm standing wall section at `NE8FDP-B`, the largest class. The CI slicer gate then re-checks every base.
   - **The plan over-claims.** "No mitigation is required" goes too far: Bambu's two warnings test floating regions and cantilevers over 3 mm, not arch quality. The upper ~90° of a Ø24.2–24.8 hole printed standing overhangs more than 45°, and the Neutrik flange overlaps the hole by only ~0.9 mm per side. The physical gate is `neutrik-tile` (new **R39**, **M19**).
   - **Roof rules.** The connector holes are recorded as a deliberate exception to the ≤ 45° roof rule. The ≤ 10 mm span rule still holds.
   - **T1-34a** retires, with `MCC_APERTURE_BRIDGE_MAX` and `MCC_APERTURE_CAP_RISE`. Neither has another consumer; T1-31 carries its own literal.
   - **T1-34c** is re-scoped to the round window.
   - **T1-48**: see B3.
2. **Thread removal and every retirement: approved (D41)**, with B1/B2.
   - `mcc_thread_pad()` has no production caller (verified).
   - `MCC_THREAD_FAST` goes with it; the `openscad-render` skill example is updated.
   - `MCC_THREAD_M3_MAJOR_D` → `MCC_M3_MAJOR_D` is rename-only in `arch-tv-bracket.scad`, whose goldens must not move.
   - `m3-thread-ladder` is not in CLAUDE.md's "Coupons before cases" list, and with the thread gone it calibrates nothing: delete it and its golden.
   - R28 and M16 retire. Their "≥ 5 insert/remove cycles" acceptance idea moves to M19.
3. **The STEP face-count CI check is rejected as designed and replaced (B5).**
   - **It cannot discriminate.** A base carries many other analytic cylinders: lid-boss bores, the side-bolt boss, the D38 stadium webs. The plan's own §1.2 shows today's teardrops already refit to 8 cylindrical faces, so `cylindrical ≥ 4·n_slots` passes on the design it is meant to reject. The conical floor only tests the chamfer, which B1 removes.
   - **It is brittle.** It counts `["part",` in OpenSCAD echo text and regex-parses a free-text summary line.
   - **It sits at the wrong layer.** Roundness is a property of the model's primitives; exactness is the converter's (D39).
   - **The plan misstates how it runs.** `build.py all --with-step` does not exercise it: `cmd_all` → `cmd_step`, never `cmd_ci`.
   - **What to gate instead** is the deliverable: a case part's STEP must come from the exact CSG path. That check is deterministic and cheap (B5).
4. **The doc sweep is incomplete and partly directional (B9).** It missed:
   - the `print-check` skill (3 places);
   - the `neutrik-panel` skill's frontmatter and coupon bullet;
   - `cutout-cheatsheet.md`;
   - the `new-case-variant` elevation bullet;
   - `openscad-authoring`'s `$fn` section;
   - `bambu-slicer.md`;
   - the coupons README's "seven coupons";
   - the BOM heading;
   - CHANGELOG;
   - four stale code comments.

   Appendix D gives exact text for all of them.
5. **Other drift:**
   - B1: the chamfer.
   - B2: `circum` in the STEP.
   - B3: the id collision.
   - B7: the golden expectations are wrong. Only one `base_fan` golden exists, and the base changes fall inside the golden tolerances.
   - B10: process wording.
   - Two record-hygiene deviations found while gating: **D42** (T1-48 used twice; the arch-tv-bracket gate's ids were never registered) and **D43** (bbox cap 250 vs 244; registered only, not fixed here).

## Binding changes

**B1 — BLOCKING. No lead-in chamfer.** Delete `MCC_FIXING_BORE_CHAMFER`, the frustum, and the chamfer term in `bore_r`.
- (a) The user decided on a *plain* Ø2.5 bore.
- (b) As written, the plan fails its own web assert. Each bore axis sits 15.31 mm from the connector centre, which is 2.91 mm from the 24-class window circle (Ø24.8, `$fn = 96`), so `2.91 − 1.75 = 1.16 < 1.2 − MCC_EPS`. Every SKU carries an `NE8FDP-B` (and `DBA-BL-B` is 24.0-class too), so `smoke` and every base render would fail. With the plain bore the web is `2.91 − 1.25 = 1.66` ✓ (23.6-class: 1.86 ✓).
- (c) The frustum's top face sits exactly on Z = 0, flush with the seat face. The module's own rule is that every cut reaches `MCC_EPS` past both faces.

Use Appendix B verbatim.

**B2 — Model the fixing bore at its nominal diameter, without `circum`.** Use `cyl(h = wall_t + 2 * MCC_EPS, d = MCC_FIXING_BORE_D, anchor = BOTTOM, $fn = 64)`.
- D39's exact STEP copies each CSG primitive's radius verbatim. `cyl(circum = true)` writes `r / cos(180/$fn)` into the CSG (`lib/BOSL2/shapes3d.scad:2557-2566`), so the specialist would measure Ø2.503, not the Ø2.5 the user decided. The inscribed error at `$fn = 64` is 0.0015 mm per side, which does not matter for printing.
- The seat and window circles already carry `MCC_HOLE_COMP` via `mcc_cutout_d()` and stay plain `$fn = 96` circles. Their STEP is exactly nominal too.
- Record the rule in architecture.md (Appendix E2) and mirror it in CLAUDE.md's `$fn` non-negotiable and in the `openscad-authoring` skill (Appendix D8/D9).

**B3 — BLOCKING. Renumber the wall-web assert from T1-48 to T1-61 (D42).** The arch-tv-bracket gate assigned T1-47 … T1-60 to `models/brackets/arch-tv-bracket.scad` on 2026-09-27; its T1-48 is "the case stays behind the TV" (lines 394–400). D36 then reused T1-48. Wherever this plan writes "T1-48" for the fixing-bore web (constants comment, assert message, module doc, skill row, docs), write "T1-61". Never touch `arch-tv-bracket.scad`'s own T1-48.

**B4 — Use Appendix A verbatim for `lib/mcc/constants.scad`.** It supersedes the two blocks in plan §3.1:
- `MCC_WALL_THREAD_WEB_MIN` → `MCC_WALL_BORE_WEB_MIN`, with a chamfer-free comment;
- `MCC_FIXING_BORE_D` cites the user decision (D41), not "assumed standard figure";
- there is no chamfer constant;
- `MCC_M3_MAJOR_D` is inserted per Appendix A2.

**B5 — BLOCKING. Replace plan §4 entirely with the exact-STEP gate in Appendix C5.**
- Add `step_exact_check()` next to `golden_check_part()`, and call it in `cmd_ci`'s `_pipeline` after a successful `export_step()`.
- It fails any case part whose manifest records `step.backend != "csg-exact"`. A case part is any `Target.kind == "model"` part: `base`, `base_fan`, `lid`.
- Coupons and brackets are exempt: their engraved `text()` labels fall back by design.
- Do **not** implement §4.1 (echo scraping, `n_connector_slots`), §4.2's face-count floors, or §4.4 (`cmd_step` printing).

**B6 — Verification must actually run the gate.** The gate lives only in `build.py ci`.
- Replace plan step 13 (`all --with-step`) with `python scripts/build.py ci --group k/6 --jobs 3` for k = 1 … 6. Run it locally if Bambu Studio and cadquery-ocp are installed; otherwise the PR's CI run is the gate.
- Every group must pass.
- If `step_exact_check` fails on any case part, **stop and report**. Do not exempt the part and do not loosen the check.

**B7 — Golden expectations (replaces plan §5's).** Only one `base_fan` golden exists: `tests/golden/pro-convert-for-ndi-to-hdmi.base_fan.json`.
1. After `render`, run `golden` without `--update`:
   - `coupons/neutrik-tile` must FAIL.
   - Each of the 8 `*.base` goldens and the one `*.base_fan` may FAIL **or PASS**. The per-base change is roughly 0.1–0.2 % of volume, inside the 0.5 % volume and 1 % area tolerances, and facet counts are informational only.
   - Any FAIL on a `*.lid`, a bracket, or any other coupon: **STOP**.
2. Run exactly:
   `python scripts/build.py golden coupons/neutrik-tile pro-convert-hdmi-tx pro-convert-sdi-tx pro-convert-hdmi-plus pro-convert-sdi-plus pro-convert-for-ndi-to-hdmi pro-convert-for-ndi-to-hdmi-4k pro-convert-for-ndi-to-sdi pro-convert-for-ndi-to-aio --update`
3. Run `golden` again; everything must PASS.
4. `git diff --stat -- tests/golden/` must show exactly:
   - `coupons/m3-thread-ladder.json` deleted;
   - content changes in `coupons/neutrik-tile.json`, the 8 `*.base.json` and `pro-convert-for-ndi-to-hdmi.base_fan.json`;
   - **no** change to any `*.lid.json` or `brackets/*.json`.

**B8 — Fix the stale code comments the plan leaves behind (Appendix C1–C4).**
- The `neutrik.scad` file header, and its `use <layout.scad>` comment: "(L0)" is wrong, layout.scad is L1.
- `layout.scad:320-322`.
- `shell.scad:168-170`.
- `neutrik-tile.scad:3-8`.
- Use Appendix C4 for `tests/test_neutrik.scad`. The plan's comment about "the thinnest wall that still keeps T1-48 satisfied" is false: the web does not depend on `wall_t`.

**B9 — Doc sweep: apply Appendix D verbatim.** It supersedes plan §6.1. Do not use that section's directional instructions ("e.g.", "mirror this plan's wording").

**B10 — No assembly-process claims.** No text may say the bore is "threaded separately before final assembly" or "outside this repo's print pipeline". How a *printed* case gets its thread is an open user question (architecture.md §12 **Q20**), and every text in Appendix D says so.

**B11 — Add a CHANGELOG `[Unreleased]` entry (Appendix D10).** Every change from D34 to D39 has one.

**B12 — architecture.md and layout-patch-wall.md: paste Appendix E and Appendix F verbatim** on the feature branch, and change nothing else in those two files. This replaces plan §6.2 and step 15 ("hand to the architect").

**B13 — Permanent record.** Create `docs/plans/2026-09-28-round-holes-no-threads.md`:
1. Copy plan C in verbatim.
2. Directly under its title, insert this line:
   `> **Implemented as amended by the architect verdict appended at the end of this file (B1–B14). Where they conflict, the verdict wins.**`
3. Append this verdict file's full content under a heading `## Architect verdict`.

**B14 — Printability stop condition.** If `check` (printability.py) or `slicer-check` flags anything at a connector hole on any base or on `neutrik-tile`: **stop and report**. Every mitigation — teardrop, cap, bridge, sacrificial layer, pose change — reverses or amends D40, which is a user decision.

## DO NOT

- Do not add a chamfer, counterbore, `circum = true` or `MCC_HOLE_COMP` to the fixing bore, and do not change `MCC_FIXING_BORE_D`. Do not call `screw_hole()` or any other thread generator.
- Do not reintroduce a teardrop, cap, flat bridge or sacrificial layer, and do not change the base's print pose.
- Do not loosen `scripts/printability.py`, the slicer gate, T1-61 / `MCC_WALL_BORE_WEB_MIN`, T1-34c, or the new STEP gate. Do not exempt a case part from the STEP gate.
- Do not edit `scripts/csg_to_step.py`, `scripts/mesh_to_step.py`, `scripts/bambu_project.py`, `render_part()`, `cmd_step()`, `_unit_cost()`, `group_units()` or `.github/workflows/render.yml`.
- Do not change `arch-tv-bracket.scad` beyond the constant rename. Its T1-48 and its goldens stay as they are.
- Do not renumber any other assert, and do not fix D43 (the bbox cap) in this PR.
- Do not edit `docs/plans/2026-09-09-printed-m3-threads.md`, any other dated plan, or anything under `knowledge/**`.
- Do not `golden --update` through an unexpected diff (B7).
- Do not edit the user's memory files; that is the teamlead's call (see the notes at the end).

## Amended implementation order

1. `lib/mcc/constants.scad`: Appendix A.
2. `lib/mcc/neutrik.scad`: Appendix B.
3. `lib/mcc/layout.scad`: plan §3.3 as written, plus Appendix C1.
4. `models/brackets/arch-tv-bracket.scad`: plan §3.4. A single `replace_all` of `MCC_THREAD_M3_MAJOR_D` → `MCC_M3_MAJOR_D` in that file does both of its edits (3 occurrences: lines 172, 487, 489). Nothing else changes in that file.
5. `tests/test_neutrik.scad`: Appendix C4.
6. `lib/mcc/shell.scad` and `models/coupons/neutrik-tile.scad`: Appendix C2 and C3.
7. Delete `models/coupons/m3-thread-ladder.scad` and `tests/golden/coupons/m3-thread-ladder.json`.
8. `scripts/build.py`: Appendix C5.
9. `python scripts/build.py doctor`, then `smoke`. Both must pass; T1-61 fires on all four part classes and on the blank.
10. `render`, `check`, `golden` (no `--update`). Expectations per B7; B14 applies.
11. `golden … --update` per B7, then `golden` again, then `git diff --stat -- tests/golden/` per B7.
12. `slicer-check`: zero warnings (B14).
13. `review`: regenerate and spot-check that no `m3-thread-ladder` part remains.
14. `ci --group k/6 --jobs 3` for k = 1 … 6 (B6).
15. Appendix D: docs, skills, CLAUDE.md, CHANGELOG, bambu-slicer.md.
16. Appendix E and Appendix F.
17. The permanent record (B13).
18. `python scripts/build.py all` as a sanity check. STEP is already covered by step 14.
19. Open the PR into `main`; CI must be green. The PR body cites D40–D43 and lists Q20 and M19 as open items for the user.

---

## Appendix A — `lib/mcc/constants.scad`

### A1 — replace current lines 305–410

Replace everything from the line beginning `// Rev 6 (2026-09-08) aperture-shape constants` through the line `                          // release/coupon/print export.` (the last line of the `MCC_THREAD_FAST` comment) with the block below. The blank line and `MCC_T_PATCH = ...` that follow stay.

```openscad
// Patch-wall connector-cut constants (rev-6 aperture ruling, re-scoped by D36/D40/D41 --
// architecture.md §5 rev 15). The seat hole and body window are PLAIN CIRCLES (D40, user decision
// 2026-09-28: "perfectly round"), so the teardrop constants MCC_APERTURE_BRIDGE_MAX and
// MCC_APERTURE_CAP_RISE are retired, not parameterised. Deliberately NOT added here:
// MCC_APERTURE_TOP_OPEN -- the top-open (U-notch) aperture is rejected (layout-patch-wall.md §15
// ruling 2026-09-08b).
MCC_WALL_BORE_WEB_MIN = 1.2; // assumed -- minimum wall between a connector's fixing bore and the
                          // seat hole / body window beside it, mm: three 0.4 mm perimeters. T1-61
                          // (filed as "T1-48" and named MCC_WALL_THREAD_WEB_MIN under D36; renamed
                          // by D41, renumbered by D42). The bores sit 15.3 mm from the connector
                          // centre on a ~24 mm hole, so this is the tightest web in the patch wall.
MCC_APERTURE_LIP_WEB_MIN = 2.0; // minimum lip material between any part of a window and the plate's
                          // own edge, mm. knowledge/design/fdm-rugged-enclosure-guidelines.md:127.
                          // T1-34c.
MCC_INSERT_BORE_EXTRA = 0.5; // assumed -- extra bore depth past a heat-set insert's own length so
                          // the insert seats fully, mm. Replaces the bare "+ 1" literal in
                          // the old connector bosses (deviation D10 / T1-35).

// -----------------------------------------------------------------------------------------
// Section: Connector-fixing bore (architecture.md §5 rev 15, D41) -- the connector's own two screw
// holes (MCC_D_SCREW_PITCH diagonal) are a PLAIN, UNTHREADED bore straight through the patch wall
// (MCC_PANEL_SEAT_T + MCC_WALL = 5 mm). User decision 2026-09-28: no printed thread ("the thread
// with those little triangles is really bad"); the external CAD specialist models the M3x0.5
// thread on the exact STEP. How a PRINTED case gets its thread is open (architecture.md §12 Q20).
// -----------------------------------------------------------------------------------------

MCC_FIXING_BORE_D = 2.5; // fixing-bore diameter, mm: the ISO metric M3x0.5 tap-drill size. User
                          // decision 2026-09-28 (architecture.md §13 D41). Modelled at this
                          // NOMINAL diameter -- no circum=true, no MCC_HOLE_COMP, no chamfer: it is a
                          // CAD input and the exact STEP must carry exactly 2.5 (architecture.md §3
                          // rev 15). Printed size/roundness not yet measured: neutrik-tile, M19.
```

### A2 — insert after line 149

Insert directly after `                     // constant that would only drift from this one.` (the last line of the `MCC_M8_CLR_D` comment):

```openscad

MCC_M3_MAJOR_D = 3.0; // M3 nominal major diameter, mm. Fixed mechanical standard (ISO metric
                       // coarse), same footing as MCC_TRIPOD_MAJOR_D above. Was
                       // MCC_THREAD_M3_MAJOR_D in the retired "Printed M3 threads" section
                       // (architecture.md §13 D41). Only consumer: models/brackets/arch-tv-bracket.scad
                       // (its T1-57 M3-engagement assert).
```

## Appendix B — `lib/mcc/neutrik.scad`

### B.1 — file header

Old (lines 3–5):
```
//   L1. Neutrik D-series cutouts (flat-panel cutout with rear seat pocket; the wall-integrated
//   cut the cases use, D36), the printed-thread pad, flange outline and rear keep-out envelope. One *provider* behind lib/mcc/panel.scad's dispatcher, not the top-level
//   panel abstraction (architecture.md:213-219).
```
New:
```
//   L1. Neutrik D-series cutouts (flat-panel cutout with rear seat pocket; the wall-integrated
//   cut the cases use -- D36, round holes D40, plain fixing bores D41), flange outline and rear
//   keep-out envelope. One *provider* behind lib/mcc/panel.scad's dispatcher, not the top-level
//   panel abstraction (architecture.md §5).
```

### B.2 — the BOSL2 screws include

Delete the line `include <BOSL2/screws.scad>`.

### B.3 — the `use <layout.scad>` comment

Old: `use <layout.scad> // mcc_aperture_window() (L0)`
New: `use <layout.scad> // mcc_aperture_window() -- L1 pure function; layout.scad never uses a provider (§3)`

### B.4 — delete `mcc_thread_pad()`

Delete everything from `// Module: mcc_thread_pad()` through the module's closing `}`, plus the blank line after it.

### B.5 — replace `mcc_neutrik_d_wall_cut()`

Replace everything from `// Module: mcc_neutrik_d_wall_cut()` through the module's closing `}` with:

```openscad
// Module: mcc_neutrik_d_wall_cut()
// Usage:
//   mcc_neutrik_d_wall_cut(part, [wall_t=], [seat_t=]);
// Description:
//   SUBTRACTIVE. Everything a Neutrik D-series connector needs from a wall it is mounted in
//   DIRECTLY -- no separate panel plate (architecture.md §5 rev 14, D36):
//     * the flange-seat hole through the first `seat_t` of wall (the connector's own
//       mcc_cutout_d(part)), and the body window behind it through the rest of the wall
//       (mcc_aperture_window(part), 2*MCC_CLR_SLIDE larger) -- both PLAIN CIRCLES, coaxial
//       (architecture.md §5 rev 15, D40, user decision 2026-09-28: perfectly round in the model, the
//       STL and the STEP -- supersedes D36's truncated teardrops). The wall prints standing, so the
//       top of each hole is a round arch: the Bambu slicer gate passes it; its print quality is
//       judged on the neutrik-tile coupon (architecture.md R39, M19). Do NOT reintroduce a
//       teardrop, cap or bridge here -- that reverses a user decision;
//     * two PLAIN cylindrical fixing bores, MCC_FIXING_BORE_D (the M3x0.5 tap-drill size), on the
//       standard diagonal (front view A(-9.5, +12) / B(+9.5, -12),
//       knowledge/neutrik/d-series-cutout.md:47,62-63), straight through the whole wall -- NOT
//       threaded (architecture.md §5 rev 15, D41, user decision 2026-09-28: the external CAD
//       specialist models the thread on the exact STEP). No chamfer, no screw pillars.
//   Local frame: X/Y is the wall face as seen FROM OUTSIDE (Y = up), Z = outward normal. The seat
//   (front) face is Z = 0 and the wall runs to Z = -wall_t (inside face). Every cut reaches MCC_EPS
//   past both faces.
//   Asserts: seat_t within the part's max panel thickness; wall_t > seat_t; at least
//   MCC_WALL_BORE_WEB_MIN of wall between each fixing bore and either opening (T1-61).
//   $fn (architecture.md §3 rev 15): the seat hole and window are $fn=96 circles at
//   mcc_cutout_d(part) / mcc_aperture_window(part), which already carry MCC_HOLE_COMP; the fixing
//   bores are $fn=64 cylinders at their NOMINAL diameter with NO circum=true, because the exact STEP
//   carries the CSG radius verbatim and the specialist needs exactly MCC_FIXING_BORE_D.
// Arguments:
//   part   = panel part number, key into MCC_PANEL_PARTS (constants.scad).
//   wall_t = total wall thickness at the connector, mm. Default: MCC_PANEL_SEAT_T + MCC_WALL.
//   seat_t = flange-seat thickness (the part of the wall the flange clamps), mm.
//            Default: MCC_PANEL_SEAT_T.
module mcc_neutrik_d_wall_cut(part, wall_t = MCC_PANEL_SEAT_T + MCC_WALL, seat_t = MCC_PANEL_SEAT_T) {
    is_blank = mcc_panel_hole_d(part) == 0;
    d_seat = mcc_cutout_d(part);
    d_win = mcc_aperture_window(part);
    sx = MCC_D_SCREW_PITCH[0] / 2; sy = MCC_D_SCREW_PITCH[1] / 2;
    screws = [[-sx, sy], [sx, -sy]]; // front view (knowledge/neutrik/d-series-cutout.md:62-63)
    bore_r = MCC_FIXING_BORE_D / 2;

    assert(seat_t <= mcc_panel_max_t(part) + MCC_EPS,
        str("mcc: seat_t=", seat_t, " exceeds max panel thickness ", mcc_panel_max_t(part), " for \"", part, "\""));
    assert(wall_t > seat_t, str("mcc: wall_t=", wall_t, " must exceed seat_t=", seat_t));
    if (!is_blank) {
        seat_path = circle(d = d_seat, $fn = 96);
        win_path = circle(d = d_win, $fn = 96);
        for (sc = screws) {
            web = min(_mcc_path_dist(sc, seat_path), _mcc_path_dist(sc, win_path)) - bore_r;
            assert(web >= MCC_WALL_BORE_WEB_MIN - MCC_EPS,
                str("mcc: T1-61 wall web between the fixing bore at ", sc, " and the opening is ", web,
                    " mm, below MCC_WALL_BORE_WEB_MIN=", MCC_WALL_BORE_WEB_MIN, " for \"", part, "\""));
        }
    }

    union() {
        if (!is_blank) {
            translate([0, 0, -seat_t - MCC_EPS])
                linear_extrude(height = seat_t + 2 * MCC_EPS)
                    circle(d = d_seat, $fn = 96);
            translate([0, 0, -wall_t - MCC_EPS])
                linear_extrude(height = wall_t - seat_t + 2 * MCC_EPS)
                    circle(d = d_win, $fn = 96);
        }
        for (sc = screws)
            translate([sc[0], sc[1], -wall_t - MCC_EPS])
                // Genuine through-hole, open at both faces (architecture.md §13 D10 Manifold reasoning).
                cyl(h = wall_t + 2 * MCC_EPS, d = MCC_FIXING_BORE_D, anchor = BOTTOM, $fn = 64);
    }
}
```

Leave `mcc_neutrik_d_cutout()`, `_mcc_seg_dist()`, `_mcc_path_dist()`, `mcc_neutrik_d_flange_outline()` and `mcc_neutrik_d_envelope()` untouched.

## Appendix C — other code files

### C1 — `lib/mcc/layout.scad`

Apply plan §3.3 as written. In addition, make this comment change.

Old (lines 320–322):
```
        // Patch-wall connector openings (D36). T1-34c: every window's teardrop cap stays inside
        // the connector recess with MCC_APERTURE_LIP_WEB_MIN of wall left above it. (T1-34b/d —
        // plate boss reliefs and plate-fixing bores — went with the plate.)
```
New:
```
        // Patch-wall connector openings (D36; round since D40). T1-34c: every round window stays
        // inside the connector recess with MCC_APERTURE_LIP_WEB_MIN of wall left above it. (T1-34b/d
        // — plate boss reliefs and plate-fixing bores — went with the plate.)
```

### C2 — `lib/mcc/shell.scad`

Old (lines 168–170):
```
//   Private, SUBTRACTIVE. The whole patch-wall connector field for `dev` (D36): the bezel recess
//   plus, per slot, mcc_panel_wall_cut() — teardropped seat hole + body window and the two printed
//   M3 threads, through the MCC_PANEL_SEAT_T + MCC_WALL of wall left behind the recess.
```
New:
```
//   Private, SUBTRACTIVE. The whole patch-wall connector field for `dev` (D36): the bezel recess
//   plus, per slot, mcc_panel_wall_cut() — a perfectly round seat hole + body window (D40) and the
//   two plain ⌀2.5 fixing bores (D41), through the MCC_PANEL_SEAT_T + MCC_WALL of wall left behind
//   the recess.
```

### C3 — `models/coupons/neutrik-tile.scad`

Old (lines 3–8):
```
//   Tier-4 physical coupon (architecture.md §9). A 40 x 45 mm section of the patch wall, printed
//   STANDING exactly like the case wall, with one Neutrik D-series connector cut straight into it
//   (D36: no panel plate — teardropped seat hole + body window and two printed M3 threads through
//   the MCC_PANEL_SEAT_T + MCC_WALL of wall behind the bezel recess), on a foot so it stands on the
//   bed. Verifies a real connector fits, seats flush and screws down, and that the horizontal
//   printed M3 threads hold, before any full case is printed.
```
New:
```
//   Tier-4 physical coupon (architecture.md §9). A 40 x 45 mm section of the patch wall, printed
//   STANDING exactly like the case wall, with one Neutrik D-series connector cut straight into it
//   (D36: no panel plate — a perfectly round seat hole + body window (D40) and two plain ⌀2.5 mm
//   M3x0.5 tap-drill bores (D41, no printed thread) through the MCC_PANEL_SEAT_T + MCC_WALL of wall
//   behind the bezel recess), on a foot so it stands on the bed. Verifies a real connector passes
//   the round hole's printed arch and seats flush, and that the bores line up and are round, before
//   any full case is printed (architecture.md R39/M19).
```

### C4 — `tests/test_neutrik.scad`

Header, old (lines 3–5):
```
//   Tier-2 headless smoke test (architecture.md §9). Instantiates mcc_neutrik_d_cutout(),
//   mcc_thread_pad() and the wall-integrated mcc_neutrik_d_wall_cut() / mcc_panel_wall_cut() (D36)
//   at default, minimum, and maximum parameters.
```
New:
```
//   Tier-2 headless smoke test (architecture.md §9). Instantiates mcc_neutrik_d_cutout() and the
//   wall-integrated mcc_neutrik_d_wall_cut() / mcc_panel_wall_cut() (D36; round holes D40, plain
//   fixing bores D41) at default, minimum, and maximum parameters.
```

Body: replace everything from the line `// --- Default parameters ------…` through `echo("mcc test_neutrik: OK");` (inclusive) with the block below. The manual-check comment block after it stays.

```openscad
// --- Default parameters -------------------------------------------------------------------
mcc_neutrik_d_cutout("NE8FDP-B");
mcc_neutrik_d_flange_outline();

// --- Minimum-ish parameters: seat_t == panel_t (no rear pocket cut at all) -----------------
translate([40, 0, 0])
    mcc_neutrik_d_cutout("NAHDMI-W-B", mirror = true, seat_t = 1.0, panel_t = 1.0);

// --- Maximum-ish parameters: etherCON at its full 4 mm panel-thickness rating --------------
translate([80, 0, 0])
    mcc_neutrik_d_cutout("NE8FDP-B", mirror = false, seat_t = 2.0, panel_t = 4.0);

// --- Wall-integrated connector cut (D36; round holes D40, plain bore D41): every part class at
// the production wall (seat 2 + lip 3) including the blank -- the T1-61 web assert fires inside
// the module on each -- and a thin wall for the BNC class (wall_t > seat_t is the only thickness
// assert since T1-42b retired; T1-61 does not depend on wall_t). Differenced from a block so the
// cuts render as real negatives. ------------------------------------------------------------
for (i = [0:1:3])
    translate([i * 40, 60, 0])
        difference() {
            translate([0, 0, -2.5]) cube([36, 40, 5], center = true);
            mcc_panel_wall_cut(["NE8FDP-B", "NAHDMI-W-B", "NAUSB-W-B", "DBA-BL-B"][i], wall_t = 5);
        }
translate([0, 110, 0])
    mcc_neutrik_d_wall_cut("NBB75DFGB", wall_t = 3.0, seat_t = 1.0);

echo("mcc test_neutrik: OK");
```

### C5 — `scripts/build.py`

(1) Insert this function directly after `golden_check_part()` (after its `return _compare_golden(...)` line):

```python
def step_exact_check(target: Target, part: str) -> list[str]:
    """[] unless a case part's STEP came from the faceted fallback. architecture.md §8 rev 15 (D40/D41):
    for case parts the exact STEP is a deliverable -- their round connector holes and fixing bores
    reach CAD as true cylinders only through scripts/csg_to_step.py. Coupons and brackets may fall
    back (engraved text() labels are unsupported by design), so they are exempt."""

    if target.kind != "model":
        return []
    manifest_path = target.export_dir / f"{part}.manifest.json"
    try:
        step = json.loads(manifest_path.read_text(encoding="utf-8")).get("step", {})
    except (OSError, json.JSONDecodeError) as exc:
        return [f"cannot read {manifest_path.name} for {target.name}:{part} ({exc})"]
    if step.get("backend") != "csg-exact":
        return [f"case part fell back to the faceted STEP converter (backend={step.get('backend')!r}, "
                f"why_not_exact={step.get('why_not_exact')!r}) -- its holes would reach CAD as facets"]
    return []
```

(2) In `cmd_ci()` → `_pipeline()`:

Old:
```python
        if not args.no_step:
            ok, detail = export_step(target, part)
            stats["step"] = detail
            if not ok:
                errors.append("step: " + detail)
```
New:
```python
        if not args.no_step:
            ok, detail = export_step(target, part)
            stats["step"] = detail
            if not ok:
                errors.append("step: " + detail)
            else:
                errors += [f"step: {m}" for m in step_exact_check(target, part)]
```

Nothing else changes in `build.py`.

## Appendix D — docs (developer-owned, same PR)

### D1 — `models/coupons/README.md`

Paste rule for this appendix: every "old" or "new" string that contains a backtick is in a fenced
block; copy the text *inside* the fence, never the fence itself. Table rows are identified by their
line number and first cell; read the file to get the exact old line.

(a) Replace the whole table row whose first cell is the file name `neutrik-tile.scad` (line 16)
with:
```
| `neutrik-tile.scad` | A real Neutrik D-series connector (NAHDMI-W-B 23.6-class default, NE8FDP-B 24.0-class variant) passes through a **standing** section of the case's patch wall (D36: no panel plate; D40: perfectly round seat hole and window) and seats flush despite any sag at the top of the printed arch; its two ⌀2.5 mm fixing bores (D41: plain M3×0.5 tap-drill bores, no printed thread) line up with the flange holes and are round; once the threading route is chosen (architecture.md §12 Q20) the thread holds ≥5 in/out cycles (M19) | `lib/mcc/constants.scad` : `MCC_HOLE_COMP` (cross-checks each `MCC_PANEL_PARTS[<part>].hole_d`); reports on `MCC_FIXING_BORE_D` (a user decision — report, don't tune) |
```

(b) Delete the table row whose first cell is the file name `m3-thread-ladder.scad` (line 20).

(c) Old:
```
`render --all` picks up all seven coupons automatically (`scripts/build.py`'s `discover_coupons()`
```
New:
```
`render --all` picks up every coupon automatically (`scripts/build.py`'s `discover_coupons()`
```

(d) Replace the whole table row in "Orientation (Bambu Studio)" whose first cell is `neutrik-tile` (line 68) with:
```
| `neutrik-tile` | **Standing on its foot, as modelled** — the wall section stands exactly like the case's patch wall (D36). | It has to test the real print orientation: the round hole's arch printed standing (D40, architecture.md R39) and the horizontal ⌀2.5 fixing bores (D41). A flat-printed tile would pass where the case fails. |
```

(e) Delete the table row in "Orientation (Bambu Studio)" whose first cell is `m3-thread-ladder` (line 72).

(f) In `### neutrik-tile`, replace the bullets from `- For each: press-fit the *real* connector` through `  confirm before touching a full case.` (lines 95–105) with:
```
- For each: fit the *real* connector (Neutrik NAHDMI-W-B / NE8FDP-B, black) into the cutout.
  - Measure the seat hole and the window with calipers **horizontally and vertically**: the top of
    the round hole prints as an arch (D40, architecture.md R39) — note any sag at the top.
  - Does the connector body pass, and does the flange seat flush against the tile's front face,
    with no visible gap or forced flex?
  - Do both ⌀2.5 mm fixing bores line up with the flange's two screw holes, and are they round and
    about ⌀2.5 (a ⌀2.5 drill shank should pass with light friction)? They are plain tap-drill
    bores (D41, no printed thread): a stock M3 machine screw does **not** thread in until the bore
    has been threaded.
  - Only once the user has picked the threading route (architecture.md §12 Q20): thread one tile
    that way and screw the connector in and out **≥5 times** — does it hold without stripping?
  - Is there any slop (connector rocks/rotates in the hole) or is it a firm, square seat?
- **Good** = connector passes, flush seat, no perceptible rock, both bores aligned and round, and
  (after Q20) the chosen thread survives ≥5 cycles.
- Record: connector class, horizontal/vertical hole diameters, fit quality (slop / snug /
  tight-needs-force), bore diameter and alignment, and — after Q20 — the threading route and how
  many cycles it survived.
- Update: `lib/mcc/constants.scad` → `MCC_HOLE_COMP` (currently `0.2` mm). If the hole was too tight,
  increase; if there was excessive slop, decrease (in ~0.05 mm steps) and re-print this coupon to
  confirm before touching a full case. Report the hole-sag and bore results to the teamlead
  (architecture.md M19): the round hole shape and `MCC_FIXING_BORE_D` are user decisions (D40/D41) —
  do not change them from this coupon.
```

(g) Delete the whole `### m3-thread-ladder` subsection: from the heading through `  generic M3 machine screw) seat and re-seat cleanly.` and the blank line after it, up to (not including) `### tolerance-ladder`.

### D2 — `BOM.md`

(a) Old (lines 57–59):
```
*(Connector-count-dependent rows — 2× M3×10 machine screw per D-connector, threading directly into
the printed M3 thread in the patch wall itself (D36), no insert (rev 10, GitHub issue #30 — see the per-variant tables below) — are
in each per-variant table below, since the connector count varies 3–4 by SKU.)*
```
New:
```
*(Connector-count-dependent rows — 2× M3×10 machine screw per D-connector into a plain ⌀2.5 mm
tap-drill bore in the patch wall itself (D41 — no printed thread, no insert; how the bore gets its
M3×0.5 thread is open, architecture.md §12 Q20) — are in each per-variant table below, since the
connector count varies 3–4 by SKU.)*
```

(b) Three `replace_all` substitutions in the per-SKU tables. Check the stated count before and after each one; if a count differs, stop.

- S1 (expect 8 occurrences).
  Old: `into the printed M3 thread in the patch wall itself (D36 — 5 mm of wall: 2 mm seat + 3 mm behind it; no pads, no inserts)`
  New: `into a plain ⌀2.5 mm M3×0.5 tap-drill bore straight through the patch wall (D41 — 5 mm of wall: 2 mm seat + 3 mm behind it; no printed thread, no pads, no inserts; how the bore gets its thread is open, architecture.md §12 Q20)`
- S2 (expect 8 occurrences). The old and new strings contain backticks, so they are shown in fenced blocks:
  ```
  docs/plans/2026-09-09-printed-m3-threads.md §2/§5 (length `assumed`, no sourced Neutrik/flange figure — confirm against m3-thread-ladder coupon)
  ```
  →
  ```
  `lib/mcc/constants.scad` (`MCC_FIXING_BORE_D`, D41); length `assumed`, no sourced Neutrik/flange figure — confirm on the `neutrik-tile` coupon (M19)
  ```
- S3 (expect 3 occurrences).
  Old: `(the DBA-BL-B blank has the same 2-pad fixing pattern as a fitted connector)`
  New: `(the DBA-BL-B blank has the same 2-screw fixing pattern as a fitted connector)`

(c) Heading. Old: `## Coupon test kit — buy now to test the seven Tier-4 coupons` → New: `## Coupon test kit — buy now to test the six Tier-4 coupons`

(d) Old:
```
Per `CLAUDE.md` ("Coupons before cases") — `neutrik-tile`, `depth-mockup`, `tg-ladder`,
`insert-boss`, `tolerance-ladder`, `side-bolt`, `m3-thread-ladder` (`models/coupons/*.scad`, all
seven already written) must each be printed and measured before any full-size case is printed.
```
New:
```
Per `CLAUDE.md` ("Coupons before cases") — `neutrik-tile`, `depth-mockup`, `tg-ladder`,
`insert-boss`, `tolerance-ladder`, `side-bolt` (`models/coupons/*.scad`, all six already written)
must each be printed and measured before any full-size case is printed.
```

(e) Delete the table row beginning `| M3 machine screw, plain (no self-tap), ≥5 spares |` (line 118).

### D3 — `.claude/skills/neutrik-panel/SKILL.md`

(a) Line 3 (frontmatter). Old substring: `(teardropped seat hole + window, printed M3 threads in the wall, no screw pillars)`
New: `(perfectly round seat hole + window, plain ⌀2.5 tap-drill fixing bores in the wall — no printed thread, no screw pillars)`

(b) Heading. Old: `## Seat, fixing and printability — connectors straight in the patch wall (architecture.md §5 rev 14, D36)`
New: `## Seat, fixing and printability — connectors straight in the patch wall (architecture.md §5 rev 15, D36/D40/D41)`

(c) Replace everything from the line beginning `- **Holes are truncated teardrops**` through `    the real thread.` (current lines 86–116) with the block below. The following bullet, `- **Never add material to the connector's side…`, stays.
```
- **Holes are perfectly round** (D40, user decision 2026-09-28): the seat hole
  (`mcc_cutout_d(part)`) and the body window behind it (`mcc_aperture_window(part)`) are plain
  `$fn = 96` circles — true circles in the STL, true cylinders in the exact STEP. The wall prints
  standing, so the top of each hole is a round arch: the Bambu slicer gate passes it, and the
  `neutrik-tile` coupon judges the print quality of that arch (architecture.md R39, M19). **Never
  reintroduce a teardrop, cap or bridge** — D36's teardrop was reverted by a user decision.
- **Screw fixing** (D41, user decision 2026-09-28): the connector's two screws go into a **plain
  ⌀2.5 mm bore** (`MCC_FIXING_BORE_D`, the ISO M3×0.5 tap-drill size) straight through the 5 mm
  wall — **no printed thread**, no chamfer, no pads/pillars. The external CAD specialist models the
  M3×0.5 thread on the exact STEP; how a *printed* case gets its thread is an open user question
  (architecture.md §12 Q20). T1-61 asserts ≥ `MCC_WALL_BORE_WEB_MIN` (1.2 mm) of wall between each
  bore and either opening — the tightest web in the wall.
  - **`$fn`** (architecture.md §3 rev 15): the bore is `cyl(d = MCC_FIXING_BORE_D, $fn = 64)` at its
    **nominal** diameter, **without** `circum = true` — the exact STEP copies the CSG radius, and
    `circum` would turn ⌀2.5 into ⌀2.503 in the specialist's CAD. The old `$fn = 32` thread
    exception is retired.
  - **`MCC_FIXING_BORE_D` is a user decision, not a tuning constant.** Do not change it, add
    `MCC_HOLE_COMP` to it, or chamfer it to "help the print" — report `neutrik-tile` results (M19)
    to the teamlead instead.
  - Never call BOSL2 `screw_hole()` (or any thread generator) for this feature: a thread is a
    polyhedron and arrives faceted in the exact STEP.
```

(d) In "Asserts that must hold", replace the five rows beginning `| Wall web around each connector thread (T1-48, D36) |`, `| Teardrop cap bridges (T1-34a) |`, `| Connector-fixing thread engagement (T1-42b) |`, `| Thread pad wall (T1-42a` and `| Connector-fixing residual radial thread engagement` with this single row:
```
| Wall web around each fixing bore (T1-61; D36 filed it as "T1-48", an id `arch-tv-bracket` already owned — D42) | distance from the bore axis to the seat-hole / window circle − `MCC_FIXING_BORE_D`/2 ≥ `MCC_WALL_BORE_WEB_MIN` (1.2) |
```

(e) Old:
```
- **`neutrik-tile`** (`models/coupons/neutrik-tile.scad`) — a 40×45 mm section of the patch wall
  (5 mm, printed standing on a foot) with one connector cut exactly as in the case (D36). Verifies
  a real connector fits, seats flush and screws into the horizontal printed threads; this is what
  calibrates `MCC_HOLE_COMP` for real.
```
New:
```
- **`neutrik-tile`** (`models/coupons/neutrik-tile.scad`) — a 40×45 mm section of the patch wall
  (5 mm, printed standing on a foot) with one connector cut exactly as in the case (D36/D40/D41).
  Verifies a real connector passes the round hole's printed arch and seats flush, that the two
  ⌀2.5 fixing bores line up and are round, and — once architecture.md §12 Q20 picks a threading
  route — that the thread holds (M19); this is what calibrates `MCC_HOLE_COMP` for real.
```

(f) Delete this bullet (lines 180–184):
```
- **`m3-thread-ladder`** (`models/coupons/m3-thread-ladder.scad`, new rev 10, GitHub issue #30) — 5
  printed M3 thread pads at production `pad_d`/`pad_h`/`$fn` (built from the same `mcc_thread_pad()`
  the connector-fixing boss module calls), sweeping `$slop` across `[0.02, 0.035, 0.05, 0.065, 0.08]`.
  Calibrates `MCC_THREAD_M3_SLOP` (default 0.05, `assumed`) — the only way to replace this placeholder
  is a real M3 machine screw threaded and unthreaded ≥5 times per pad (R28).
```

### D4 — `.claude/skills/neutrik-panel/cutout-cheatsheet.md`

Old: `- Fixing: rear bosses + M3 heat-set insert (5.7 mm). Never self-tapping into 2 mm ASA.`
New: `- Fixing (D41): a plain ⌀2.5 mm M3×0.5 tap-drill bore straight through the 5 mm patch wall at each screw position — no printed thread, no bosses, no inserts; how a printed case gets its thread is open (architecture.md §12 Q20).`

### D5 — `.claude/skills/print-check/SKILL.md`

(a) Line 73, a substring inside the "Shell base/lid" row. Old:
```
their holes are truncated teardrops with one flat ≤10 mm roof bridge, the bezel recess roof is chamfered ~50°, and the connector screws thread into horizontal printed M3 threads — check those on the standing `neutrik-tile` coupon first.
```
New:
```
their holes are **perfectly round** (D40 — the top of each hole prints as a round arch, a deliberate exception to the ≤45° roof rule), the bezel recess roof is chamfered ~50°, and the connector screws go into horizontal plain Ø2.5 mm tap-drill bores (D41, no printed thread) — check the arch and the bores on the standing `neutrik-tile` coupon first (M19).
```

(b) Old:
```
- [ ] No unsupported span >10 mm; all roofs ≤45°
```
New:
```
- [ ] No unsupported span >10 mm; all roofs ≤45° — the round D-connector holes in the base's standing patch wall are a deliberate exception (D40, user decision; judged on `neutrik-tile`, architecture.md R39)
```

(c) Old:
```
      `--projection=o`, camera along −Y) shows each D hole with its teardrop cap hidden inside the
      26 × 31 flange outline, its two threaded holes, and nothing standing inside the hole
      (architecture.md §5 rev 14, D36)
```
New:
```
      `--projection=o`, camera along −Y) shows each D hole **perfectly round** inside the 26 × 31
      flange outline, its two Ø2.5 fixing bores on the Neutrik diagonal, and nothing standing inside
      the hole (architecture.md §5 rev 15, D36/D40/D41)
```

### D6 — `.claude/skills/new-case-variant/SKILL.md`

Old (lines 194–201):
```
- **What "correct" looks like in the elevation:** `n_slots` **exactly round** cutouts (never a
  diagonal/teardrop blob — that shape was deviation D9 and is retired), each with two small screw
  dots near its edge on the Neutrik diagonal, the same diagonal orientation repeated identically at
  every slot (a slot whose dots look rotated 90° relative to its neighbours is the mirrored-relief
  regression ruling 2026-09-08c C1 fixed once already — report it, don't silently "fix" it
  yourself), and the 4 plate-fixing screw dots at the rim corners. A small (≤ ~1.5 mm) crescent
  sliver at one edge of a cutout is expected (T1-34b) — it is the shell's own boss-relief window
  showing through, covered by the fitted connector body in real life; it is not a defect.
```
New:
```
- **What "correct" looks like in the elevation:** `n_slots` **perfectly round** cutouts in the
  bezel recess (never a diagonal/teardrop blob — D9's hull and D36's teardrop are both retired,
  D40), each with two small Ø2.5 bore dots near its edge on the Neutrik diagonal, the same diagonal
  orientation repeated identically at every slot (a slot whose dots look rotated 90° relative to its
  neighbours is the mirrored-pattern regression ruling 2026-09-08c C1 fixed once already — report
  it, don't silently "fix" it yourself). There is no plate since D36: no plate-fixing screw dots and
  no relief crescent — anything else visible inside a cutout's outline is a defect.
```

### D7 — `.claude/skills/openscad-render/SKILL.md`

Old:
````
`-D` can be repeated for multiple parameters, e.g. rendering a variant's `base` with the fast
(plain-bore) connector threads and the reservation ghosts on:

```powershell
& "C:\Program Files\OpenSCAD (Nightly)\openscad.com" --backend=Manifold `
    -o exports\pro-convert-hdmi-tx-base-fast.stl `
    -D 'part="base"' -D 'MCC_THREAD_FAST=true' -D 'MCC_SHOW_GHOST=true' `
    models\pro-convert-hdmi-tx\case.scad
```
````
New:
````
`-D` can be repeated for multiple parameters, e.g. rendering a variant's `base` with the reservation
ghosts on:

```powershell
& "C:\Program Files\OpenSCAD (Nightly)\openscad.com" --backend=Manifold `
    -o exports\pro-convert-hdmi-tx-base-ghost.stl `
    -D 'part="base"' -D 'MCC_SHOW_GHOST=true' `
    models\pro-convert-hdmi-tx\case.scad
```
````

### D8 — `.claude/skills/openscad-authoring/SKILL.md`

(a) Insert directly after the line `  right in the OpenSCAD preview and doesn't fit the connector.`:
```
- **Exception — holes that are CAD inputs** (architecture.md §3 rev 15, D41): the exact STEP copies
  each primitive's radius, and `circum = true` enlarges it to `r / cos(180/$fn)`. The connector
  fixing bore (`MCC_FIXING_BORE_D`, a tap-drill hole the CAD specialist threads) is therefore
  `cyl(d = MCC_FIXING_BORE_D, $fn = 64)` at its nominal size — **no** `circum`, **no**
  `MCC_HOLE_COMP`, no chamfer.
```

(b) Old:
```
- `cyl(h=, d=, circum=true, $fn=64)` for any functional round hole (see `$fn` policy above);
```
New:
```
- `cyl(h=, d=, circum=true, $fn=64)` for any functional clearance hole (see `$fn` policy above — CAD-input bores excepted);
```

### D9 — `CLAUDE.md`

(a) Ruggedness bullet. Old:
```
  behind a shell bezel. **The connectors mount straight into the patch wall** (user decision
  2026-09-28, D36 — no separate panel plate): a 3 mm bezel recess, a 2 mm flange seat with a
  teardropped hole, and printed M3 threads in the wall itself — no screw pillars (architecture.md
  §5 rev 14). Never call the Neutrik provider directly from `models/**`.
```
New:
```
  behind a shell bezel. **The connectors mount straight into the patch wall** (user decision
  2026-09-28, D36 — no separate panel plate): a 3 mm bezel recess, a 2 mm flange seat with a
  **perfectly round** hole (D40), and a **plain Ø2.5 mm M3×0.5 tap-drill bore** per screw through the
  wall itself — **no printed thread** (D41; the CAD specialist models the thread on the STEP; how a
  printed case gets its thread is open, architecture.md §12 Q20) — no screw pillars
  (architecture.md §5 rev 15). Never call the Neutrik provider directly from `models/**`.
```

(b) Non-negotiable. Old:
```
- No `$fn` set globally — see `openscad-authoring`. Functional holes get local `$fn≥64` + `circum=true`.
```
New:
```
- No `$fn` set globally — see `openscad-authoring`. Functional clearance holes get local `$fn≥64` + `circum=true` (or a diameter that already carries `MCC_HOLE_COMP`); a hole that is a CAD input — the connector's Ø2.5 tap-drill bore — is modelled at its nominal diameter, no `circum` (architecture.md §3 rev 15).
```

(c) Current status. Old substring: `latch redesign (D34) — are in architecture.md §13.`
New: `latch redesign (D34), perfectly round connector holes (D40), a plain Ø2.5 tap-drill bore instead of a printed thread (D41) — are in architecture.md §13.`

### D10 — `CHANGELOG.md`

Insert directly after `  dozens of flat facets. The faceted mesh converter remains only as a reported fallback.` (the D39 bullet, inside `## [Unreleased]` → `### Changed (modeller feedback, 2026-09-28)`):
```
- **Perfectly round connector holes** (architecture.md D40): the D-connector seat hole and window in
  the patch wall are plain circles again (D36's teardrops are gone) — in the model, the STL and the
  STEP.
- **No printed thread** (D41): each connector's two screw holes are a plain Ø2.5 mm M3×0.5 tap-drill
  bore; the thread is modelled in CAD from the STEP. The `m3-thread-ladder` coupon is retired. How a
  printed case gets its thread is still open (architecture.md §12 Q20).
- CI: a case part whose STEP falls back to the faceted converter now fails `build.py ci`.
```

### D11 — `.claude/knowledge/bambu-slicer.md`

(a) Old:
```
1. **Know the print pose before modelling.** Shells print open-side-up, the panel and neutrik-tile
   face-down (flipped by `build.py print_pose()`), brackets flat on their TV face. Anything that
   points down in that pose is an overhang.
```
New:
```
1. **Know the print pose before modelling.** Shells (base and lid) print open-side-up — the base's
   patch wall standing — and the `neutrik-tile` coupon stands on its foot exactly like that wall
   (D36); brackets print flat on their TV face. Anything that points down in that pose is an
   overhang.
```

(b) Insert directly after `  a fixed grid or one hole per bay centre — **is flagged**. Vent sealed cells sideways instead.`:
```
- **A plain round hole through a standing wall does not warn** (D40, 2026-09-28): a ⌀24.8 connector
  window through a 5 mm wall section at `NE8FDP-B` sliced clean, and the CI slicer gate covers every
  base. Slicer silence is not print quality — the top ~90° of the arch still overhangs > 45°;
  `neutrik-tile` judges the sag (architecture.md R39, M19).
```

---

## Appendix E — `.claude/knowledge/architecture.md` (paste verbatim on the feature branch)

Paste rule (applies to Appendices E and F): copy only the text *inside* each fenced block, never
the fence itself. Table rows are identified by their first cell; read the file to get the exact old
line. Anchors quoted inline contain no backticks; anchors that do are shown in fenced blocks.

### E1 — header

Insert immediately before the line beginning `**Revision 13, 2026-09-27 (export contract + printability fixes):**`. Keep one blank line after the inserted block.

```
**Revision 15, 2026-09-28 (round connector holes, no printed thread — D40/D41; plan
`docs/plans/2026-09-28-round-holes-no-threads.md`).** Two user decisions after the external CAD
specialist opened the exact STEP (D39). **(D40)** The Neutrik D holes in the patch wall are
**perfectly round** in the model, the STL and the STEP: D36's truncated teardrops are reverted,
T1-34a and `MCC_APERTURE_BRIDGE_MAX`/`MCC_APERTURE_CAP_RISE` retire, T1-34c is re-scoped. **(D41)**
The connector's fixing is a **plain ⌀2.5 mm M3×0.5 tap-drill bore** (`MCC_FIXING_BORE_D`), not a
printed thread: `mcc_thread_pad()`, every `MCC_THREAD_*` constant, T1-42a/b/c, the §3 `$fn = 32`
exception, the `m3-thread-ladder` coupon, R28 and M16 retire; `MCC_THREAD_M3_MAJOR_D` becomes
`MCC_M3_MAJOR_D`. The wall-web assert D36 filed as "T1-48" is renumbered **T1-61** (**D42**:
T1-47 … T1-60 already belonged to `arch-tv-bracket`); **D43** re-registers the bbox-cap deviation
whose proposed id "D26" collided with rev 13's D26. `build.py ci` now fails a case part whose STEP
falls back to the faceted converter (§8). New: the §3 nominal-bore rule, **R39** (the round arch
printed standing), **Q20** (how a printed case gets its thread), **M19** (`neutrik-tile` round-hole
and bore check). **No envelope figure moves on any SKU.** Rev 14 (2026-09-28, D34–D39) was
recorded in the body and §13 without a header entry; this paragraph names it.

```

### E2 — §3 `$fn` policy

Replace the whole 13-line bullet in "### `$fn` policy" that starts with `- **The one sanctioned exception:` and ends with the line below:
```
  **not** folded into #30 because it changes every export and every golden's provenance.
```
Replace it with:
```
- ~~**The one sanctioned exception: `$fn = 32` on a BOSL2 `screw_hole(thread=true)` bore** (rev 10,
  issue #30).~~ **RETIRED rev 15 (2026-09-28, D41):** there is no printed thread left in the repo, so
  there is no `$fn` exception of any kind. Kept from it because it is still true: the far bigger
  STL-size lever is **ASCII → binary STL** (~6×, lossless); that remains a separate ticket because it
  changes every export and every golden's provenance.
- **Holes that are CAD inputs are modelled at their nominal diameter (rev 15, D41).** Since D39 the
  exact STEP rebuilds OpenSCAD's CSG tree, so it carries each primitive's radius *verbatim* — and
  `cyl(..., circum = true)` puts `r / cos(180/$fn)` into that tree (⌀2.5 at `$fn = 64` becomes
  ⌀2.503 in CAD). A hole whose exact size is a downstream CAD input — today only the connector fixing
  bore (`MCC_FIXING_BORE_D`, the M3×0.5 tap-drill size the specialist threads) — is therefore
  `cyl(d = <nominal>, $fn ≥ 64)` **without** `circum` and without `MCC_HOLE_COMP`; the inscribed
  error (0.0015 mm/side at ⌀2.5, `$fn = 64`) is far below print tolerance. Clearance holes that must
  pass a real part keep the rule above (`circum = true`, or a diameter that already carries
  `MCC_HOLE_COMP`, as the D-connector circles do).
```

### E3 — §5 heading

Old: `## 5. The connectors mount directly in the patch wall (rev 14, D36 — was: a separate printed plate)`
New: `## 5. The connectors mount directly in the patch wall (rev 14 D36, rev 15 D40/D41 — was: a separate printed plate)`

### E4 — §5 table: replace four rows in place

Row beginning `| Seat hole |`:
```
| Seat hole | `mcc_cutout_d(part)` through the 2 mm seat, **perfectly round** (rev 15, D40 — was D36's truncated teardrop) | `neutrik.scad` `mcc_neutrik_d_wall_cut()` |
```
Row beginning `| Body window |`:
```
| Body window | `mcc_cutout_d + 2·MCC_CLR_SLIDE` through the 3 mm behind the seat, **perfectly round**, coaxial with the seat hole. The roof over the opening is the round arch itself — no cap, no flat bridge (T1-34a retired); the window stays inside the recess band with `MCC_APERTURE_LIP_WEB_MIN` to spare (T1-34c) | `layout.scad` `mcc_aperture_window()` |
```
Row beginning `| Connector fixing |`:
```
| Connector fixing | 2 × **plain ⌀2.5 mm bore** (`MCC_FIXING_BORE_D`, the ISO M3×0.5 tap-drill size) **through the whole 5 mm wall**, on the standard diagonal — **no printed thread** (rev 15, D41), no chamfer, no pads, no inserts, nothing standing proud of the inner face; screws M3×10 through the flange. The external CAD specialist models the thread on the exact STEP; how a *printed* case gets its thread is open (§12 Q20) | **T1-61**: ≥ `MCC_WALL_BORE_WEB_MIN` (1.2 mm, `assumed`) of wall between each bore and either opening |
```
Row beginning `| Coupon |`:
```
| Coupon | `neutrik-tile` is a 40 × 45 mm section of this wall, printed **standing**, on a foot — it tests the real geometry: the round holes' printed arch (R39) and the horizontal ⌀2.5 bores (M19) | `models/coupons/neutrik-tile.scad` |
```

### E5 — §5 paragraph under the table

Old:
```
Printed-thread risk: the threads now print with a **horizontal** axis (the `m3-thread-ladder`
calibrates them vertical). Check the screws on the `neutrik-tile` coupon before the first case; if
they strip, the fallback is the self-tapping screws Neutrik ships (`d-series-cutout.md:102`) into a
plain pilot, not pads.
```
New:
```
**Round holes and the plain bore (rev 15, 2026-09-28, D40/D41 — user decisions).** The external CAD
specialist, opening the exact STEP (D39), asked why only the D holes were not round: D36's teardrops
are genuinely not circles, and a printed thread is a polyhedron that D39 leaves faceted by design.
Both are fixed in the *shape*, not in the converter: plain circles for the seat hole and window, a
plain ⌀2.5 cylinder for each fixing bore, so all of them reach CAD as true circles/cylinders at their
nominal size (§3 nominal-bore rule). Consequences, all deliberate:
- **The round holes are a deliberate exception to the ≤ 45° roof rule** in a standing wall: their
  upper ~90° is a > 45° arch. The ≤ 10 mm span rule still holds (the last layers close a chord of a
  few mm). The plan's research pass sliced a 5 mm standing wall section at `NE8FDP-B` with no Bambu
  Studio warning, the CI slicer gate re-checks every base, and the print quality of the arch is
  judged on `neutrik-tile` (**R39**, **M19**). Do not reintroduce a teardrop, cap or bridge to "fix"
  it — that reverses D40; it goes back to the user.
- **The fixing bore is not threaded in the print.** A tap-drill bore is the right input for the
  specialist's CAD thread. For a *printed* case the route — hand-tap M3×0.5 (the knowledge base's
  recommendation for printed cases, `knowledge/neutrik/d-series-cutout.md:109-110`), Neutrik's
  bundled self-tapping screws, or the specialist's own route — is **open (§12 Q20)**. The rev-14
  fallback ("the self-tapping screws Neutrik ships into a plain pilot") is now one of those
  candidates, not a fallback.
- **The bore is plain** — no chamfer, no counterbore, no `MCC_HOLE_COMP`. Anything the specialist
  wants at the mouth he models together with the thread.
```

### E6 — pointer under `### Connector fixing`

Insert directly after the line `### Connector fixing` (keep one blank line before the next paragraph):
```

> **History (rev ≤ 13).** The current connector fixing is the rev-15 table row above: a plain ⌀2.5 mm
> tap-drill bore straight through the patch wall (D41). Bullet 3 below (the printed pad thread) and
> R28 are retired; they are kept for the reasoning behind the numbers.
```

### E7 — §8, new bullet after the D39 STEP bullet

Insert directly after `  Booleans are fused pairwise: one OCCT Fuse with many overlapping tools silently lost volume.`:
```
- **Case STEPs must be exact (rev 15, D40/D41).** The round connector holes and the ⌀2.5 fixing
  bores are only true cylinders if the part goes through `csg_to_step.py`; a faceted fallback
  silently turns them back into flat facets. `build.py ci` therefore fails any **case part**
  (`Target.kind == "model"`: `base`, `base_fan`, `lid`) whose manifest records a `step.backend`
  other than `csg-exact` (`step_exact_check()`, next to `golden_check_part()`). Coupons and brackets
  may still fall back (engraved `text()` labels are unsupported by design). The gate lives only in
  `ci`; `build.py step` stays a conversion command, so a machine without cadquery-ocp can still
  convert (faceted) locally. A per-part face-type census was considered and rejected: a base carries
  many other analytic cylinders (boss bores, the side-bolt boss, gusset stadia), so a count cannot
  tell a round connector hole from anything else.
```

### E8 — §9 Tier-1 table: replace one row with two

Replace the row beginning `| **printed-thread pad: wall ≥ 2.0 mm,` with these two rows:
```
| ~~printed-thread pad: wall ≥ 2.0 mm, ≥ 3 engaged turns, residual radial engagement ≥ 50 % of nominal after `$slop` (T1-42a/b/c, rev 10)~~ **retired rev 15 (D41): no printed thread** | — |
| connector fixing bore: ≥ `MCC_WALL_BORE_WEB_MIN` (1.2) of wall between each ⌀`MCC_FIXING_BORE_D` bore and the seat hole / window (**T1-61**, rev 15 — filed as "T1-48" by D36, renumbered by D42) | §5 rev 15 table |
```

### E9 — §9 prose, after the rev-12 sentence

Insert directly after this line (the end of the "Rev 12 adds T1-46a–d" sentence):
```
whether or not `cfg.fan` is true.
```
Insert:
```
**Rev 14 (D36)** retired T1-34b/T1-34d (the plate's boss reliefs and plate-fixing bores went with the
plate) and added the wall-web assert under the id "T1-48" — which `models/brackets/arch-tv-bracket.scad`
already used: the arch-tv-bracket gate (2026-09-27, `docs/plans/2026-09-27-arch-tv-bracket.md` B4)
owns **T1-47 … T1-60**. **Rev 15** renumbers the wall web to **T1-61** (D42), retires **T1-34a** (no
teardrop cap, D40) and **T1-42a/b/c** (no printed thread, D41), and re-scopes **T1-34c** to the round
window. **The next free id is T1-62** — take it from `layout-patch-wall.md` §9, which now lists every
id.
```

### E10 — §9 Tier 4

Old:
```
- `neutrik-tile` — one D cutout with the 2 mm pocket and rear bosses, in a 40 × 45 mm tile. Verifies a
  real connector actually fits and screws down.
```
New:
```
- `neutrik-tile` — a 40 × 45 mm section of the patch wall, printed standing (D36), with one connector
  cut exactly as in the case. Verifies a real connector passes the round hole's printed arch and
  seats flush (R39), that the two ⌀2.5 fixing bores line up and are round, and — once §12 Q20 is
  answered — that the chosen thread holds (M19).
```
Old:
```
- `m3-thread-ladder` (**new, rev 10, issue #30**) — 5 printed M3 thread pads at production
  `pad_d`/`pad_h`/`$fn`, sweeping `$slop` across **`[0.02, 0.035, 0.05, 0.065, 0.08]`** (per-side
  0.04–0.16 mm, i.e. 15–59 % of the 0.2705 mm nominal engagement). The ladder must be built from the
  same `mcc_thread_pad()` the production module calls — a coupon that duplicates the geometry cannot
  calibrate it. **Acceptance is ≥ 5 insert/remove cycles per pad, not one successful seat**: a
  connector gets unscrewed for cable service, and repeat-cycle stripping is the exact failure mode
  heat-set inserts existed to prevent (**R28**). Print it in the same batch as `neutrik-tile`.
```
New:
```
- ~~`m3-thread-ladder`~~ — **retired rev 15 (2026-09-28, D41)** together with the printed thread it
  calibrated (`MCC_THREAD_M3_SLOP`); file and golden deleted. Its acceptance idea — ≥ 5
  insert/remove cycles, not one successful seat — moves to M19 for whichever thread Q20 picks.
```

### E11 — §11 R28 heading

Old:
```
**R28 — M3 is below the conservative floor for printed FDM internal threads, and the connector
fixing now depends on one. NEW 2026-09-09 (rev 10, #30).** Sourced FDM-thread guidance treats **M6
```
New:
```
**R28 — M3 is below the conservative floor for printed FDM internal threads, and the connector
fixing now depends on one. NEW 2026-09-09 (rev 10, #30). RETIRED 2026-09-28 (rev 15, D41): the
connector fixing is a plain tap-drill bore — there is no printed thread left; kept as history (its
repeat-cycle acceptance moves to M19).** Sourced FDM-thread guidance treats **M6
```

### E12 — §11 new risk R39

Insert directly after `  documented user option, not a silent default.` (the last line of R29), with a blank line before it:
```

**R39 — the round connector holes print as a > 45° arch in a standing wall. NEW 2026-09-28 (rev 15,
D40).** (R30 … R38 are reserved to the arch-tv-bracket gate, `docs/plans/2026-09-27-arch-tv-bracket.md`.)
The user's "perfectly round" decision gives up D36's teardrop, whose whole purpose was that the wall
never roofs over with an unsupported round arch. Bambu Studio raises no warning — its warnings test
floating regions and > 3 mm cantilevers, not arch quality — so the residual risk is physical: the top
of a ⌀24.2–24.8 mm hole may sag, and the Neutrik flange overlaps the hole by only ~0.9 mm per side
(`knowledge/neutrik/d-series-cutout.md:36-43`).
- **The gate is `neutrik-tile`, both classes (M19)** — already a CLAUDE.md "Coupons before cases"
  coupon. No full-size case is printed before it passes.
- **If the arch sags enough that the connector does not pass or seat flush:** recalibrating
  `MCC_HOLE_COMP` from the coupon (its normal write-back), deburring/reaming, or a slicer setting
  keeps the holes round and needs no decision. A teardrop, cap, bridge or sacrificial layer
  reverses D40 and goes back to the user.
```

### E13 — §12 new question Q20

Insert directly after `    either way — it is a BOM row, so it must not gate the branch.` (the last line of Q19):
```
20. **How does a *printed* case get its M3×0.5 thread? NEW 2026-09-28 (rev 15, D41) — needs the
    user.** The model carries a plain ⌀2.5 tap-drill bore; the external CAD specialist models the
    thread on the STEP. For a case printed from this repo's own STL/3MF the candidates are (a)
    hand-tap M3×0.5 (the knowledge base's recommendation for printed cases,
    `knowledge/neutrik/d-series-cutout.md:109-110`), (b) the self-tapping screws Neutrik bundles with
    front-mount D connectors (`d-series-cutout.md:102-104`; their size against a ⌀2.5 pilot is
    `unknown` — §5's "no self-tapping into 2 mm of ASA" concerned a 2 mm plate, this bore is 5 mm
    deep), or (c) every physical case follows the specialist's own manufacturing route. It also
    settles whether ASA is really the material being threaded. **No geometry depends on it** (the
    bore is a user decision); it gates the BOM wording, the first physical assembly and M19's
    thread-hold test.
```

### E14 — §12 measurement list, new row M19

Insert directly after the row beginning `| **M17** |`, with no blank line:
```
| **M19** | **`neutrik-tile`, both classes (NAHDMI-W-B and NE8FDP-B), printed standing in ASA:** (a) seat-hole and window diameter measured **horizontally and vertically** (sag at the top of the arch, R39); (b) the real connector passes and its flange seats flush; (c) both ⌀2.5 fixing bores aligned with the flange holes, round, and their printed diameter; (d) once §12 Q20 is answered, the chosen thread survives **≥ 5 insert/remove cycles** (R28's acceptance idea, kept) | **R39 + Q20 — gates the first full-size print** (with the other "Coupons before cases" coupons). `MCC_HOLE_COMP` is written back from (a)/(b) as usual; `MCC_FIXING_BORE_D` and the hole shape are user decisions (D40/D41) — report, do not tune | User, calipers + a ⌀2.5 drill shank as a gauge |
```

### E15 — measurement numbering note

Old (the last line of the "> **Numbering note (rev 8).**" block):
```
> (`m3-thread-ladder` + `neutrik-tile` in ASA). **Rev 11** adds M17 (panel switch, above).
```
New:
```
> (`m3-thread-ladder` + `neutrik-tile` in ASA) — **retired rev 15 (D41)**, superseded by M19. **Rev 11**
> adds M17 (panel switch, above). **M18a–d** belong to the arch-tv-bracket gate
> (`docs/plans/2026-09-27-arch-tv-bracket.md` §9) and are not repeated here. **Rev 15** adds M19.
```

### E16 — §13 deviations log, four new rows

Insert directly after the row beginning `| **D39** | 2026-09-28 |` (and before the `| **D11** |` row). Each row is one line:
```
| **D40** | 2026-09-28 | §5 rev 14 (D36): seat hole + body window are truncated teardrops so the standing wall never roofs over with a round arch; T1-34a caps their flat bridge | Not a code defect — **a user decision reverses the rule.** The external CAD specialist opened the exact STEP (D39) and asked why only the D holes were not round: a teardrop is genuinely not a circle (D39 arc-fits its round part, the cap stays straight) | The connector holes are what the user and the specialist see first; "perfectly round in the model, the STL and the STEP" is now the requirement | **Done in rev 15 (user decision 2026-09-28).** `mcc_neutrik_d_wall_cut()` cuts plain `$fn = 96` circles; `mcc_aperture_window()` returns only `d_win`; T1-34a, `MCC_APERTURE_BRIDGE_MAX` and `MCC_APERTURE_CAP_RISE` retired; T1-34c re-scoped to the round window. Evidence: the plan's research pass sliced a 5 mm standing wall section at `NE8FDP-B` with no Bambu Studio warning; the CI slicer gate covers every base. §5 records the arch as a deliberate exception to the ≤ 45° roof rule; its print quality is **R39 / M19**. Plan: `docs/plans/2026-09-28-round-holes-no-threads.md` |
| **D41** | 2026-09-28 | §5 rev 10/rev 14: the connector's screws thread into a printed M3×0.5 thread (a pad, then the wall itself under D36); §3's `$fn = 32` exception; T1-42a/b/c; R28/M16 | Not a code defect — **a user decision reverses the rule**: "the thread with those little triangles is really bad; the specialist prefers to model the thread in himself afterwards". A BOSL2 thread is a polyhedron, which D39 exports faceted by design | The specialist threads the part in CAD; a faceted helix in the STEP is unusable for that | **Done in rev 15 (user decision 2026-09-28).** Plain ⌀2.5 bore (`MCC_FIXING_BORE_D`, the ISO M3×0.5 tap-drill size) through the whole 5 mm wall, modelled at nominal without `circum` (§3 nominal-bore rule) and without a chamfer; `mcc_thread_pad()`, `MCC_THREAD_*` (incl. `MCC_THREAD_FAST`), the `fast` argument, T1-42a/b/c, the `$fn = 32` exception, the `m3-thread-ladder` coupon + golden, R28 and M16 retired; `MCC_THREAD_M3_MAJOR_D` → `MCC_M3_MAJOR_D` (reused by `arch-tv-bracket` T1-57). How a *printed* case gets its thread: **§12 Q20**. The plan's 0.5 mm lead-in chamfer was **rejected at the gate**: it is not "plain", and counted in the web assert it fails T1-61 on every 24-class slot (`2.91 − 1.75 = 1.16 < 1.2`) |
| **D42** | 2026-09-28 | §9 / `layout-patch-wall.md` §9: every Tier-1 id is unique, and the next free id is taken from §9 (rev 11's own lesson) | `lib/mcc/neutrik.scad` (D36) filed the wall-web assert as **T1-48**, but `models/brackets/arch-tv-bracket.scad:394-400` has used **T1-48** (its A2, "the case stays behind the TV") since the arch-tv-bracket gate assigned **T1-47 … T1-60** on 2026-09-27 (`docs/plans/2026-09-27-arch-tv-bracket.md` B4). Root cause: that gate's ids (T1-47 … T1-60, R30 … R38, M18a–d and its proposed deviation "D26") were never entered in this file or in `layout-patch-wall.md` §9 — `arch-tv-bracket.scad:54-57` says the architect would record them "after merge" | Two asserts answer to one id: an assert message or a review comment citing "T1-48" is ambiguous, and the next plan would collide again | **Fixed in rev 15.** The wall web becomes **T1-61** (message, constant comment, skill, both docs). `layout-patch-wall.md` §9 now carries a row for T1-47 … T1-60 (owned by `arch-tv-bracket`); R30 … R38 and M18a–d are reserved to that gate (§11/§12 notes), so rev 15's new ids are R39, M19, Q20 and T1-61. The proposed "D26" is re-registered as **D43** (rev 13's D26 is the patch-wall window fix) |
| **D43** | 2026-09-28 | §9 Tier-1 "`bbox ≤ MCC_BUILD − MCC_BED_MARGIN` per part" vs. the per-side meaning of `MCC_BED_MARGIN` | `lib/mcc/util.scad:42-43` `mcc_bbox_ok()` caps each axis at `MCC_BUILD − MCC_BED_MARGIN` = **250**, while `scripts/build.py:57` enforces `MAX_AXIS_MM = MCC_BUILD_MM − 2 * MCC_BED_MARGIN_MM` = **244** (a margin on each side). §1's "margin vs the 250 assert limit" column and the §9 row repeat the 250 | Found by the arch-tv-bracket gate (2026-09-27, filed there as "D26", never recorded here — D42). Two ceilings for one rule, and the Tier-1 assert is the looser one: a part between 244 and 250 mm renders but fails `check` | **Open — separate small ticket, record only.** Per that gate: change `util.scad` to `MCC_BUILD − 2·MCC_BED_MARGIN`, prove it golden-neutral for every current caller of `mcc_bbox_ok()`, and update §1/§9. `arch-tv-bracket.scad` already asserts 244 explicitly (its T1-47). Not part of the D40/D41 PR |
```

### E17 — §14 "Panel aperture"

Old:
```
**Panel aperture.** Patch-wall stack in Y = 3.0 proud bezel + 2.0 plate seat + 3.0 structural lip =
8.0 mm. Aperture Z range `[6, 45]`, X range `±(plate_l/2 − 3)` with `plate_l = L − 26`. Connector
centreline `z = 25.5`. One stepped rabbet (6 mm over the plate's rim ring, 5 mm over the field) plus
`n_slots` windows through the 3 mm lip; **each window is a `union()` of a truncated-teardrop body
circle and two plain ⌀8.88 boss reliefs — never a `hull()` (rev 6, D9)**, so from outside the user
sees a flat plate face with exactly-round cutouts. The top-open U-notch aperture is rejected.
```
New:
```
**Panel aperture (rev 14 D36, rev 15 D40/D41).** Patch-wall stack in Y = 3.0 bezel recess + 2.0
flange seat + 3.0 behind it = 8.0 mm; there is **no plate** (D36). The bezel recess covers the old
plate footprint (`L − 26` × 39). Per slot, `mcc_panel_wall_cut()` cuts a **perfectly round** seat
hole (`mcc_cutout_d`) and a coaxial round window (`+ 2·MCC_CLR_SLIDE`) through the 5 mm of wall
behind the recess (D40), plus two plain ⌀2.5 fixing bores on the Neutrik diagonal (D41, no printed
thread). Connector centreline `z = 25.5`. The rev-6 plate aperture (one stepped rabbet, `union()`
windows with boss reliefs) is history; the top-open U-notch stays rejected.
```

---

## Appendix F — `.claude/knowledge/layout-patch-wall.md` (paste verbatim on the feature branch)

### F1 — header

Insert immediately before the line beginning `Status: **revision 12, 2026-09-09.** Rev 12 is the architecture gate for`, with a blank line after the block:
```
Status: **revision 15, 2026-09-28** (aligned with `architecture.md` rev 15; revs 13–14 did not edit
this file — D36's consequences for §2.5 and §9 are recorded here now). D36 removed the connector
plate; D40 makes the connector holes perfectly round; D41 replaces the printed thread with a plain
⌀2.5 tap-drill bore. What changes here: **§2.5 is marked superseded** (it describes the plate-era
aperture), and **§9** retires T1-34a (D40), T1-34b/T1-34d (D36) and T1-42a/b/c (D41), re-scopes
T1-34c and T1-35, lists **T1-47 … T1-60** (owned by `models/brackets/arch-tv-bracket.scad`) and adds
**T1-61** — the wall-web assert D36 filed under the colliding id "T1-48" (`architecture.md` §13
D42). **No envelope figure moves on any SKU.** Rev-12 status follows.
```

### F2 — §2.5 banner

Insert directly after this heading line (line 379), with a blank line before and after the inserted block:
```
### 2.5 The patch-wall aperture — ONE rabbet, `n_slots` ROUND WINDOWS + 2 BOSS RELIEFS (rev 6, 2026-09-08)
```
Insert:
```
> **SUPERSEDED (rev 15, 2026-09-28).** There is no plate since D36: each connector is cut straight
> into the patch wall by `mcc_panel_wall_cut()` — a perfectly round seat hole and a coaxial round
> window (D40) and two plain ⌀2.5 fixing bores (D41). Normative text: `architecture.md` §5 rev 15.
> Everything below in §2.5 is plate-era history, kept for the reasoning behind the numbers. §2.5.1's
> ruling (a `DBA-BL-B` blank keeps its full `hole_d = 24.0`) still holds; its shape wording is
> plate-era.
```

### F3 — §9 rows

Replace each row in place, identified by its first cell, then insert two new rows after the T1-42c row.

Row beginning `| **T1-34a** |`:
```
| ~~**T1-34a**~~ | ~~the lip window is a `union()` of a truncated-teardrop body circle and two boss reliefs, with the teardrop's flat bridge ≤ `MCC_APERTURE_BRIDGE_MAX`~~ | **RETIRED rev 15 (2026-09-28, D40).** The connector holes are perfectly round (user decision), so there is no cap and no flat bridge to bound; `MCC_APERTURE_BRIDGE_MAX` and `MCC_APERTURE_CAP_RISE` are deleted. The arch that replaces it is covered by the CI slicer gate and by `neutrik-tile` (`architecture.md` R39, M19) |
```
Row beginning `| **T1-34b** |`:
```
| ~~**T1-34b**~~ | ~~*roundness* — only the two relief crescents show through the plate's cutout~~ | **RETIRED by D36 (2026-09-28), recorded rev 15.** No plate, no boss reliefs. The user requirement it expressed ("the D slots must read as exactly round") is now met literally by D40 |
```
Row beginning `| **T1-34c** |`:
```
| **T1-34c** | *containment* — every connector window stays inside the bezel-recess band with `MCC_APERTURE_LIP_WEB_MIN (2.0)` to spare: `mcc_aperture_window(part)/2 + MCC_APERTURE_LIP_WEB_MIN <= MCC_PLATE_H/2` | **new rev 6; re-scoped rev 15 (D40)** — the round window's own top replaces the teardrop cap. `12.4 + 2.0 = 14.4 <= 19.5` ✓ for the 24-class window. Lives in `mcc_case_layout()` (`layout.scad`). The rev-6 clauses on the relief circles and `plate_l` went with the plate (D36) |
```
Row beginning `| **T1-34d** |`:
```
| ~~**T1-34d**~~ | ~~every lip window clears every plate-fixing boss's insert bore by ≥ 2.0 mm~~ | **RETIRED by D36 (2026-09-28), recorded rev 15.** No plate-fixing bosses |
```
Row beginning `| **T1-35** |`:
```
| **T1-35** | *a screw must reach its insert* — every heat-set boss's bore is continuous from the insert end through to the bearing face: **no solid material on any fastener's screw axis between the bearing face and its insert** | **new rev 6; re-scoped rev 15 (record of D36).** The two systems this row named — `mcc_neutrik_d_bosses()` and the plate's 4 fixing bosses — were removed by D36; the rule stands for every heat-set boss that remains. The connector fixing is now a plain through-bore with no insert (T1-61) |
```
Row beginning `| **T1-42a** |`:
```
| ~~**T1-42a**~~ | ~~printed thread pad has enough wall~~ | **RETIRED rev 15 (2026-09-28, D41)** — no printed thread; `mcc_thread_pad()` is deleted |
```
Row beginning `| **T1-42b** |`:
```
| ~~**T1-42b**~~ | ~~printed thread has enough engagement (≥ 3 turns; D36 applied it to the 5 mm wall)~~ | **RETIRED rev 15 (D41)** — the bore is threaded outside the print (`architecture.md` §12 Q20) |
```
Row beginning `| **T1-42c** |`:
```
| ~~**T1-42c**~~ | ~~`$slop` has not erased the thread~~ | **RETIRED rev 15 (D41).** The lesson stays in `architecture.md` rev 10: a BOSL2 internal thread grows by `4·$slop` in diameter |
```
Then insert these two rows directly after the (new) T1-42c row, which is the last row of the §9 table:
```
| **T1-47 … T1-60** | owned by `models/brackets/arch-tv-bracket.scad` (its A1 … A13 plus B3; e.g. T1-48 = "the case stays fully behind the TV") | **assigned 2026-09-27** by the arch-tv-bracket gate (`docs/plans/2026-09-27-arch-tv-bracket.md` B4), recorded here only in rev 15 (`architecture.md` §13 D42). They live in that file; do not reuse these ids |
| **T1-61** | *the connector fixing bores leave wall* — for each of the two bores at the Neutrik diagonal (`MCC_D_SCREW_PITCH/2`): distance from the bore axis to the seat-hole circle and to the window circle, minus `MCC_FIXING_BORE_D/2`, ≥ `MCC_WALL_BORE_WEB_MIN` (1.2, `assumed`) | **new rev 14 (D36) as "T1-48"; renumbered rev 15 (D42) and re-scoped to the plain bore (D41).** 24-class window (⌀24.8): `2.91 − 1.25 = 1.66 ≥ 1.2` ✓; 23.6-class (⌀24.4): `3.11 − 1.25 = 1.86` ✓. Evaluated in `mcc_neutrik_d_wall_cut()`. **The next free id is T1-62** |
```

---

## Notes for the teamlead (non-binding)

1. **CLAUDE.md non-negotiable.** B2 and D9(b) reword the `$fn` line from "Functional holes … `circum=true`" to "clearance holes …" plus the nominal-bore case. This clarification is what delivers the user's "Ø2.5 in the exact STEP", but it touches a non-negotiable; give the user a one-line heads-up.
2. **Q20 needs the user** before the first physical assembly: hand-tap, Neutrik self-tappers, or the specialist's route. It does not block the PR.
3. **User memory.** `…\memory\ndi-hdmi-case-viewer.md` still says to render the viewer with `-D MCC_THREAD_FAST=true`. After this merge that flag does nothing (harmless); update the note.
4. **Plan open questions.**
   - Q2 (a dedicated bore coupon): ruled no. M19 on `neutrik-tile` covers bore size and roundness.
   - Q3 (the specialist's "stripes"): not blocking. The `new-case-variant` skill documents an OpenCSG-preview moiré artefact inside connector cutouts, which is another plausible cause.
   - Q4 (whether ASA is the material being threaded): folded into Q20.
5. **Follow-ups outside this PR (D36 drift, not introduced here):**
   - `new-case-variant` still describes the elevation as "plate placed";
   - `neutrik-panel`'s part table still says `DBA-BL-B | 0 (solid)` (stale since rev 8);
   - `cutout-cheatsheet.md` "Entry point: `mcc_panel_cutout`" omits `mcc_panel_wall_cut`;
   - `layout-patch-wall.md` §2.1–§2.4 still describe the plate;
   - D43 (the bbox cap);
   - fixture unit tests for `csg_to_step.py`, to pin D39's primitive-to-analytic mapping once instead of per part.
6. **Id sequencing.** This revision takes rev 15, D40–D43, T1-61, R39, M19 and Q20. Any architecture-gated branch in flight must rebase and take the next free ids after these.
