# Plan: printed M3 threads for the Neutrik connector fixing holes (issue #30)

Status: **ready for architect review, then implementation.** Researched 2026-09-09.
Owner of this document: researcher (this plan). Implementation: a Sonnet-tier developer, after the
`solution-architect` gate (Team Charter — every code-changing session requires it).

## 0. Ticket and scope correction

GitHub issue #30: *"Neutrik D-panel screw holes printed as direct M3 threads (no inserts)"*. The
issue text says **"the four screw holes that fix each Neutrik D-series panel connector (flange holes
at ±9.5 × ±12 mm)"**.

**Scope correction (read this first — it changes what "four" means).** A Neutrik D-series flange has
**two** mounting holes, not four — confirmed by `knowledge/neutrik/d-series-cutout.md:16-34` ("Two
clearance holes... positioned diagonally opposite each other") and by the code itself:
`lib/mcc/neutrik.scad`'s `mcc_neutrik_d_bosses()` loops over exactly
`[[-screw_x, screw_y], [screw_x, -screw_y]]` — two positions. The `±9.5 × ±12 mm` figure the ticket
quotes is `MCC_D_SCREW_PITCH = [19.0, 24.0]` (`constants.scad:58`), which is the pitch **between**
those two diagonal holes, not four independent hole positions. "Four" appears to double-count the ±
signs on each axis.

There is a second, genuinely separate 4-hole system in this repo that this ticket's background
paragraph brushes up against: `_mcc_patch_wall_fixing_bosses()` in `lib/mcc/shell.scad`, which is 4
bosses at `mcc_panel_fixing_pos()` = `(±(plate_l/2−3), ±16.5)` — a completely different position
formula, used to screw the **whole panel plate** into the **shell's rabbet**, not to screw a
**connector** onto the plate. The ticket's own scope bullet cites both files as background context,
but the concrete detail it gives (`±9.5 × ±12 mm`) uniquely identifies the **connector-fixing** system
in `neutrik.scad`, not the **plate-fixing** system in `shell.scad`.

**Decision (recorded here, not re-opened per file without a new user call): this plan converts only
the connector-fixing bosses in `lib/mcc/neutrik.scad` (`mcc_neutrik_d_bosses()`) — 2 threaded pads
per connector.** The plate's own 4 retention bosses in `shell.scad` keep their existing M3 heat-set
inserts, unchanged. Rationale: they are a different physical system (fixing the plate to the shell,
not the connector to the plate), the ticket's own concrete number identifies the connector system, and
converting both at once roughly doubles the risk surface (two independently-tuned Manifold-defect
workarounds, two boss geometries, two coupons) for a ticket that did not ask for the plate-fixing
change. If the user wants the plate-fixing bosses converted too, that is a natural, cleanly-separable
follow-up ticket against `shell.scad` alone — flag it to the user, do not fold it into this change
silently.

## 1. Where the thread lives — decision

**Decision: a thicker local pad on the back of the panel plate — i.e. extend the existing
`mcc_neutrik_d_bosses()` boss, keep it on the plate.** This is "option C" in the ticket's own framing,
not "option A" (thread the 2 mm plate field itself — ~4 turns, rejected) or "option B" (move the
fixing into the shell wall).

**Why the plate (not the shell wall) — print orientation is the deciding factor, and it is not a close
call.** `architecture.md` §5 rationale 2 and the `neutrik-panel` skill both establish that the panel
plate prints **flat, face-down** (flange/front face on the bed). Tracing the actual Z convention in
`lib/mcc/panel.scad`/`neutrik.scad` (front face at local `Z=0`, the field extruded to `Z=−t`, bosses
extending further to `Z=−t−boss_h`) against that print orientation: when the front face sits on the
bed, the model's `−Z` direction (toward the boss) is the printer's `+Z` (up). **So a pad on the plate's
rear prints with its bore's axis vertical, growing straight up off the bed, one full circle per
layer — the single best orientation for a printed internal thread**: no bridging, no thread-flank
overhang, and the plate's own connector cutouts (already the reason for face-down printing) are
unaffected.

The shell wall is the opposite case. `mcc_shell_base()` prints floor-down, walls vertical; a bore
placed in a wall-mounted boss (option B) would have its axis **horizontal** — every thread crest on
the underside of the helix is then an overhang, the exact defect class `_mcc_patch_wall_fixing_bosses()`'s
own giant code comment in `shell.scad` already documents fighting (there for a different reason —
Manifold's blind-bore-flush-union limit — but the print-quality problem compounds it: a horizontal
M3 thread this small does not print cleanly on an 0.4 mm nozzle without support, and support inside a
blind M3 bore is not removable). Rejected on print-orientation grounds alone, independent of the
Manifold question.

**Verified empirically (2026-09-09, this research pass) that the pad-on-plate pattern does not
resurrect the Manifold "blind-bore-flush-against-a-face" defect** (`shell.scad`'s own comment,
deviation D10) that broke the heat-set-insert version of this same boss shape. A minimal repro — a
flat seat slab with two M3 clearance holes already cut through it (mirroring `mcc_neutrik_d_cutout()`),
then two pads unioned flush against the slab's rear face, each cut with a **through**-bore
`screw_hole(..., thread=true)` open at both the pad's rear tip and the seat-facing face — rendered
clean on the pinned OpenSCAD 2025.09.07 + Manifold: `"simple": true`, correct bbox, no `ERROR`/`WARNING`,
93 ms. The load-bearing detail, carried over unchanged from the existing T1-35 fix: **the bore must
stay a genuine through-hole, open at both ends** — do not blind-pocket it from the rear tip only, that
is exactly what broke the insert version.

**Load path, unchanged from today's design.** The connector's own two M3 screws pull the connector
flange face-down against the plate's front face; the plate itself sits in the shell's rabbet, so shear
from an impact on the connector is still carried by the shell (via the rabbet), and the screws only
ever resist pull-out — same statement as `architecture.md` §5 "Costs, accepted" bullet 1, unaffected by
this change. Nothing about the plate's own retention in the rabbet (the 4 `shell.scad` bosses, out of
scope per §0) changes.

**Consequence for the shell wall's aperture geometry: none.** Because the pad's outer diameter is kept
numerically identical to today's boss OD (§3), the wall window's boss-relief circles
(`d_rel = boss_od + 2·MCC_CLR_SLIDE = 8.88 mm`) and every T1-34a/b number in `layout-patch-wall.md`
§2.5 are untouched. This is a deliberate constraint, not a coincidence — see §3.

## 2. Thread geometry

- **Standard**: M3 × 0.5 mm (ISO metric coarse), major ⌀ 3.0 mm nominal, standard mechanical constant
  (not project-sourced — same "fixed mechanical standard" footing as `MCC_TRIPOD_MAJOR_D`,
  `constants.scad:135`).
- **BOSL2 call**: `lib/BOSL2/screws.scad`'s `screw_hole()`, spec string `"M3,<pad_h>"`, `thread=true`,
  `tolerance="6H"` (the ISO default internal-thread tolerance class — confirmed in `screws.scad:1217`
  `tolerance = first_defined([tolerance, internal?"6H":"6g"])`; **do not** pass a clearance-hole
  tolerance name like `"loose"`/`"normal"` here — those only apply when `thread=false`,
  `screws.scad:758-761,979-984` — passing one with `thread=true` is a different code path and will not
  do what you want).
- **`$slop`**: BOSL2's own contract (`screws.scad:753,798`, `threading.scad:179` etc.) is
  *"makes the hole larger by `4·$slop` to account for printing overextrusion"* — i.e. `$slop` is a
  **per-side** radial compensation and the effective diameter growth is `4·$slop` (not `2·$slop`) per
  BOSL2's own internal-thread convention. Set `$slop = MCC_THREAD_M3_SLOP` at the call site (do not
  rely on an ambient `$slop`).
- **`$fn`**: **32**, not the repo's usual "$fn ≥ 64 minimum" (see §3's render-time finding for why this
  is a deliberate, documented exception for this one feature — not a quiet downgrade).
- **Lead-in chamfer**: `bevel1=true` on the `screw_hole()` call, at the pad's front (screw-entry) face
  — eases starting the screw after it clears the seat's plain clearance hole. Verify the resulting
  chamfer against the sourced target (0.8–1.5 mm deep, 45°) by inspection of the rendered
  `neutrik-tile` coupon STL in a slicer; if BOSL2's default bevel geometry does not land in that band,
  pass an explicit chamfer size (check `screw_hole()`'s own bevel-sizing parameters in `screws.scad` at
  implementation time — do not guess a workaround, read the actual default and adjust).
- **Engagement**: pad height `MCC_THREAD_M3_PAD_H = 7.0 mm` (numerically unchanged from today's
  `boss_h` default), minus ~1.0 mm chamfer ⇒ ≈ 6.0 mm of full thread ⇒ **12 turns** at 0.5 mm pitch,
  comfortably above the ticket's ≥ 3-turn acceptance floor and matching the sourced FDM
  best-practice engagement of 2.0–2.5× the screw diameter (6.0–7.5 mm) — see the citation in §7's
  assumption list.
- **Neutrik's own screw length**: not sourced. `knowledge/neutrik/d-series-cutout.md:100-104` confirms
  Neutrik ships **self-tapping** screws for front-mount D-connectors (not machine screws), and gives no
  length. `knowledge/components/fasteners-and-hardware.md` §4.3 has a PCB-mount D-series screw length
  (2.2 mm ⌀, 5 mm max — a different, unrelated hardware class) and a third-party (non-Neutrik) M3×12 mm
  screw+nut kit cited only as a sourcing example, not this project's chosen length. **This plan does
  not use Neutrik's bundled screw at all** — per the ticket, the BOM moves to a plain M3 machine screw
  sized by this project's own stack-up (§5), which makes the "what does Neutrik ship" question
  moot for the fastener choice, though it remains cited here so nobody re-derives a length from it by
  mistake.

## 3. New constants, asserts, render-time cost

### 3.1 New constants — add to `lib/mcc/constants.scad`, immediately after the existing
`MCC_INSERT_BORE_EXTRA` line (currently line 322-324, "Section: Patch-wall layout")

```openscad
// -----------------------------------------------------------------------------------------
// Section: Printed M3 threads (connector fixing, GitHub issue #30) — the connector's own two
// screw holes (MCC_D_SCREW_PITCH diagonal) thread directly into a printed pad on the panel
// plate's rear (architecture.md §5 "Connector fixing", 2026-09-09 revision). NOT the plate's own
// 4 retention bosses in shell.scad — those keep MCC_INSERT_M3 heat-set inserts, out of scope for
// this change (docs/plans/2026-09-09-printed-m3-threads.md §0).
// -----------------------------------------------------------------------------------------

MCC_THREAD_M3_MAJOR_D = 3.0;  // M3 nominal major diameter, mm. Fixed mechanical standard (ISO
                               // metric coarse), same footing as MCC_TRIPOD_MAJOR_D above.
MCC_THREAD_M3_PITCH   = 0.5;  // M3 coarse pitch, mm. ISO metric standard. BOSL2 screw_hole()
                               // resolves this itself from the "M3" spec string; named here only
                               // for the turns-count assert (MCC_THREAD_M3_PAD_H below).

MCC_THREAD_M3_SLOP = 0.15; // radial print-compensation passed as BOSL2's $slop, mm. assumed —
                            // docs/plans/2026-09-09-printed-m3-threads.md §7 PLAN-ASSUMPTION 1:
                            // mid of the 0.10-0.20 mm per-side range a sourced FDM-thread guide
                            // gives for a well-tuned 0.4 mm-nozzle machine (Sovol3D, "3D Printing
                            // Threads and Screws"), scaled for ASA on the Bambu X1C. NOT yet
                            // calibrated against a physical print. Calibrate with the
                            // m3-thread-ladder coupon (§4) before trusting this value; update this
                            // constant's comment with the coupon name/date once measured, same
                            // convention as every other *_CLR_* constant in this file.

MCC_THREAD_M3_PAD_D = 8.28; // connector-fixing pad outer diameter, mm. Pinned EQUAL to the
                             // pre-existing heat-set boss OD (MCC_BOSS_MIN_RATIO(1.8) *
                             // MCC_INSERT_M3 od(4.6) = 8.28, the value mcc_neutrik_d_bosses() used
                             // before this change) so the wall-aperture boss-relief circles
                             // (d_rel = boss_od + 2*MCC_CLR_SLIDE = 8.88, layout-patch-wall.md
                             // §2.5) and every T1-34a/b number are numerically UNCHANGED by this
                             // ticket — no shell.scad wall-window geometry moves. Do not derive
                             // this from MCC_INSERT_M3 any more (that struct is being dropped from
                             // this boss's own logic); it is a bare literal specifically so a
                             // future edit to MCC_INSERT_M3 cannot silently move the wall aperture
                             // via this file.
MCC_THREAD_M3_PAD_H = 7.0;  // connector-fixing pad depth, mm. Numerically unchanged from the old
                             // mcc_neutrik_d_bosses() boss_h default (architecture.md §5 "~7 mm
                             // total"). Minus MCC_THREAD_M3_CHAMFER, gives ~6.0 mm / 12 full turns
                             // of engagement at MCC_THREAD_M3_PITCH -- above both the ticket's >=3-
                             // turn floor and the sourced 2.0-2.5x-diameter (6.0-7.5mm) FDM
                             // best-practice engagement (Sovol3D, same source as the slop figure).
MCC_THREAD_M3_CHAMFER = 1.0; // lead-in chamfer depth at the pad's screw-entry face, mm. assumed --
                              // mid-low end of the sourced 0.8-1.5 mm / 45 deg range (Sovol3D),
                              // chosen low so it does not eat meaningfully into the 7.0 mm
                              // engagement above.
MCC_THREAD_WALL_MIN = 2.0;   // minimum solid wall around the M3 major diameter (+ slop), mm.
                              // Reuses this repo's existing minimum-wall-around-a-bore convention
                              // (same value as heat_set_boss()'s own wall assert, fasteners.scad,
                              // and MCC_APERTURE_LIP_WEB_MIN above) -- corroborated independently
                              // by fdm-rugged-enclosure-guidelines.md:125 ("~2.0mm... good
                              // starting reference") and the Sovol3D source (1.6-2.0mm). At
                              // MCC_THREAD_M3_PAD_D=8.28 and slop=0.15 this evaluates to
                              // (8.28 - (3.0+4*0.15))/2 = 2.34mm, comfortably clear.
MCC_THREAD_ENGAGE_MIN_TURNS = 3; // minimum full engaged thread turns, ticket acceptance criterion.

MCC_THREAD_PREVIEW = true; // when true (default, and every release/CI render), connector fixing
                            // pads carry the real BOSL2 thread=true bore. When explicitly set
                            // false (-D MCC_THREAD_PREVIEW=false), a cheap plain MCC_M3_CLR_D
                            // clearance bore is substituted -- fast dev-iteration renders and the
                            // interactive case viewer only (docs/plans/2026-09-09-printed-m3-
                            // threads.md §3.3). NEVER set false for a release/coupon/print export.
```

### 3.2 `mcc_neutrik_d_bosses()` rewrite — `lib/mcc/neutrik.scad`

Replace the whole module body (current lines 109-153) with the pad+thread version. New contract:

```openscad
// Module: mcc_neutrik_d_bosses()
// Usage:
//   mcc_neutrik_d_bosses(part, [mirror=], [pad_h=], [pad_d=]);
// Description:
//   Two rear pads (ADDITIVE solid, union onto the panel) at the two screw positions, each carrying
//   a printed M3 internal thread the connector's own machine screw drives straight into (GitHub
//   issue #30, 2026-09-09 -- replaces the heat-set-insert version). The plate's own 4 retention
//   bosses in shell.scad are UNCHANGED (still heat-set inserts) -- this module only covers the
//   connector-to-plate fixing, docs/plans/2026-09-09-printed-m3-threads.md §0.
//   Local Z convention unchanged from before: Z=0 is the rear pocket floor (butts against the
//   panel), the pad extends to Z=-pad_h. The bore is a genuine THROUGH-hole (open at both the rear
//   tip Z=-pad_h and the panel-facing face Z=0) -- required so this union does not hit the same
//   Manifold "blind-bore-flush-against-a-face" limit documented at length in shell.scad's
//   _mcc_patch_wall_fixing_bosses() (deviation D10); verified clean for this exact pad-on-plate
//   shape by isolated repro during this ticket's research pass (plan §1).
//   When MCC_THREAD_PREVIEW is false, the bore is a plain MCC_M3_CLR_D clearance cylinder instead
//   of a real thread (cheap preview/viewer fast-path, plan §3.3) -- NEVER for a release export.
// Arguments:
//   part   = panel part number (kept only to keep the call site symmetric with the cutout call;
//            the pad geometry itself does not vary per connector).
//   mirror = mirror the two screw-hole positions left-right, matching mcc_neutrik_d_cutout()'s own
//            `mirror` argument. Default: false.
//   pad_h  = total rearward pad length from the seat, mm. Default: MCC_THREAD_M3_PAD_H (7).
//   pad_d  = pad outer diameter override, mm. Default: MCC_THREAD_M3_PAD_D (8.28).
module mcc_neutrik_d_bosses(part, mirror = false, pad_h = MCC_THREAD_M3_PAD_H, pad_d = MCC_THREAD_M3_PAD_D) {
    mirror_x = mirror ? -1 : 1;
    screw_x  = mirror_x * MCC_D_SCREW_PITCH[0] / 2;
    screw_y  = MCC_D_SCREW_PITCH[1] / 2;

    thread_major_slopped = MCC_THREAD_M3_MAJOR_D + 4 * MCC_THREAD_M3_SLOP; // BOSL2's own $slop
                                                                             // convention, screws.scad:753.
    wall = (pad_d - thread_major_slopped) / 2;
    assert(wall >= MCC_THREAD_WALL_MIN,
        str("mcc: T1-36a thread pad wall=", wall, " below minimum ", MCC_THREAD_WALL_MIN, " mm (pad_d=", pad_d, ")"));

    engaged_len = pad_h - MCC_THREAD_M3_CHAMFER;
    turns = engaged_len / MCC_THREAD_M3_PITCH;
    assert(turns >= MCC_THREAD_ENGAGE_MIN_TURNS,
        str("mcc: T1-36b thread engagement=", turns, " turns below minimum ", MCC_THREAD_ENGAGE_MIN_TURNS, " (pad_h=", pad_h, ")"));

    for (pos = [[-screw_x, screw_y], [screw_x, -screw_y]]) {
        translate([pos[0], pos[1], 0])
        difference() {
            translate([0, 0, -pad_h / 2])
                cyl(h = pad_h, d = pad_d, circum = true, $fn = 32);
            if (MCC_THREAD_PREVIEW) {
                translate([0, 0, -pad_h])
                    screw_hole(str("M3,", pad_h + 2 * MCC_EPS), thread = true, tolerance = "6H",
                        $slop = MCC_THREAD_M3_SLOP, bevel1 = true, anchor = BOTTOM, $fn = 32);
            } else {
                translate([0, 0, -pad_h - MCC_EPS])
                    cyl(h = pad_h + 2 * MCC_EPS, d = MCC_M3_CLR_D, circum = true, $fn = 32);
            }
        }
    }
}
```

`lib/mcc/neutrik.scad`'s own header `include`/`use` block needs one addition:
`include <BOSL2/screws.scad>` (a new line next to the existing `include <BOSL2/std.scad>` at the top
of the file — `screws.scad` is **not** pulled in transitively by `std.scad`, confirmed by grep during
this research pass; without this line `screw_hole()` is an unknown-module error, not a silent no-op).

**Remove** the module's old `insert`, `insert_od`, `insert_hole_d`, `insert_len` locals and the
`MCC_BOSS_MIN_RATIO` assert — none of that applies any more (no insert). Do not leave the old
boss-OD-vs-insert-OD assert in place pointing at a now-irrelevant struct.

**Everything else in `neutrik.scad` is unchanged** — `mcc_neutrik_d_cutout()` (the seat's own plain
`MCC_M3_CLR_D` clearance holes) needs no edit at all; it already provides the clearance the screw
shank passes through before it reaches the pad's thread.

### 3.3 Render-time cost — measured, not estimated

Measured during this research pass (pinned OpenSCAD 2025.09.07, `--backend=Manifold`, same machine
this repo's `build.py doctor` reports): 8 M3 holes (matching a real 4-connector panel's pad count — 2
pads × 4 connectors) in an otherwise-trivial test block.

| Variant | `$fn` | OpenSCAD internal render time | Facets | STL size |
|---|---|---|---|---|
| Plain clearance cylinders (today's insert-bore shape) | 64 | 21 ms | 2,092 | 0.48 MB |
| BOSL2 `screw_hole(thread=true)` | 64 | 546 ms (**~26×**) | 59,436 (**~28×**) | 18.4 MB (**~38×**) |
| BOSL2 `screw_hole(thread=true)` | 32 | 277 ms (**~13×**) | 29,740 (**~14×**) | 9.1 MB (**~19×**) |

**Conclusion: threads are exactly as heavy as the ticket warned, and it is dominated by facet count on
the helical thread flank, not by anything algorithmic in Manifold's boolean engine (0.5 s absolute is
still fast).** Two consequences, both already reflected in this plan:

1. **`$fn=32` is the deliberate default for this feature (§2), not 64.** It roughly halves the cost at
   no meaningful loss of thread function — a printed M3 thread's real surface is already coarsened far
   more by the 0.4 mm nozzle's own extrusion width than by facet quantization above ~24-32 segments/turn;
   this is a documented, named exception to the repo's blanket "$fn ≥ 64" policy (`architecture.md` §3),
   not a silent downgrade — cite this table in the code comment and in the `openscad-authoring` skill
   update (§6).
2. **Total CI/render impact is small in absolute terms** (≤ 8 × 0.55 s ≈ 4.4 s added across all 8 panel
   renders at $fn=64, ≤ 8 × 0.28 s ≈ 2.2 s at $fn=32 — panel parts only, base/lid renders are
   untouched), **but STL file size is not** — an 18 MB jump from 8 small pads in a trivial test block is
   a real concern for (a) the release zips' panel STL/3MF, and (b) specifically the interactive NDI-to-
   HDMI case viewer artifact referenced in the user's session memory, which likely loads panel geometry
   in-browser. **`MCC_THREAD_PREVIEW=false` (§3.1) exists for exactly this: use it for the viewer's
   generation path and for any fast dev-iteration render; never for a release/coupon/print export.**

## 4. Coupon — `models/coupons/m3-thread-ladder.scad`, and the `neutrik-tile` update

**New coupon, mirrors `insert-boss.scad`'s ladder pattern.** 5 pads on one base tile, `MCC_THREAD_M3_SLOP`
swept 0.05 → 0.25 mm in 0.05 mm steps (brackets the assumed 0.15 mm default from both sides), each
engraved with its slop value, each a real M3-threaded pad at the production `pad_d`/`pad_h`/`$fn` so a
real Neutrik-shipped M3 screw (or a plain M3 machine screw, per the BOM change in §5) can be test-driven
into all 5 and the tightest-that-still-threads-cleanly value read back.

```openscad
//////////////////////////////////////////////////////////////////////
// models/coupons/m3-thread-ladder.scad
//   Tier-4 physical coupon (architecture.md §9, GitHub issue #30). 5 printed M3 thread pads at
//   $slop 0.05/0.10/0.15/0.20/0.25 mm, each labelled, to calibrate MCC_THREAD_M3_SLOP for this
//   printer/ASA combination against a real M3 machine screw.
//
// Render:
//   openscad --backend=Manifold -o out/m3-thread-ladder.stl models/coupons/m3-thread-ladder.scad
//////////////////////////////////////////////////////////////////////

$fa = 1; $fs = 0.4;

include <mcc/mcc.scad>
include <BOSL2/screws.scad>

part = "m3-thread-ladder";

SLOPS   = [0.05, 0.10, 0.15, 0.20, 0.25]; // brackets MCC_THREAD_M3_SLOP (0.15, assumed)
PAD_H   = MCC_THREAD_M3_PAD_H;
PAD_D   = MCC_THREAD_M3_PAD_D;
PITCH   = 16;
BASE_T  = 3.0;
MARGIN  = 8;

n      = len(SLOPS);
base_w = n * PITCH + PITCH;
base_l = PITCH + 2 * MARGIN;

echo(str("m3-thread-ladder: slops=", SLOPS, " pad_d=", PAD_D, " pad_h=", PAD_H));

difference() {
    translate([0, 0, -BASE_T])
        linear_extrude(height = BASE_T)
            square([base_w, base_l]);

    for (i = [0 : 1 : n - 1])
        translate([(i + 1) * PITCH, MARGIN - 2, -0.6])
            linear_extrude(height = 0.6 + MCC_EPS)
                text(str(SLOPS[i]), size = 3.0, halign = "center", valign = "center", font = "Liberation Sans:style=Bold");
}

for (i = [0 : 1 : n - 1]) {
    slop_i = SLOPS[i];
    translate([(i + 1) * PITCH, base_l - MARGIN, 0])
    difference() {
        translate([0, 0, -PAD_H / 2]) cyl(h = PAD_H, d = PAD_D, circum = true, $fn = 32);
        translate([0, 0, -PAD_H])
            screw_hole(str("M3,", PAD_H + 2 * MCC_EPS), thread = true, tolerance = "6H",
                $slop = slop_i, bevel1 = true, anchor = BOTTOM, $fn = 32);
    }
}

// vim: expandtab tabstop=4 shiftwidth=4 softtabstop=4 nowrap
```

**`neutrik-tile.scad` update**: no change needed to the file's own logic — it already calls
`mcc_neutrik_d_bosses(connector)` (line 56) with defaults, so it automatically picks up the new
threaded-pad geometry once `neutrik.scad` is rewritten. Re-render it as part of verification (§7) to
confirm the tile itself still prints a valid, single-shell part with a real connector's diagonal hole
pattern and the new pad shape — no `.scad` edit required, just a re-render + visual check.

## 5. BOM impact

`BOM.md` currently gives every priority SKU's per-variant section a pair of rows (confirmed present,
byte-identical wording, in all 8 SKU sections — `pro-convert-hdmi-tx` (6×, 3 connectors),
`pro-convert-sdi-tx` (6×), `pro-convert-hdmi-plus` (8×, 4 connectors), `pro-convert-sdi-plus` (8×),
`pro-convert-for-ndi-to-hdmi` (8×), `pro-convert-for-ndi-to-hdmi-4k` (8×), `pro-convert-for-ndi-to-sdi`
(8×), `pro-convert-for-ndi-to-aio` (8×)):

```
| M3×5.7 heat-set insert (Ruthex RX-M3x5.7) | N | 2 per connector rear boss × M connectors | ... |
| M3×8 machine screw                        | N | Paired 1:1 with the inserts above         | ... |
```

**Delete the insert row** in every one of the 8 SKU sections (2 per connector × M connectors of these
inserts no longer exist for connector fixing). **Change the screw row** to a plain M3 machine screw at
a length sized by this ticket's stack-up, not the old `M3×8` figure:

```
screw length under head >= flange thickness (unknown/assumed) + seat_t (2.0) + engagement (up to pad_h=7.0)
```

Flange thickness is not sourced anywhere in `knowledge/**` (checked during this pass — the D-series
drawings give flange footprint and corner radius, not stock thickness). Use **M3×10 mm** pan/socket-head
machine screw as the BOM figure — long enough to clear a thin (≤1 mm) flange plus the full 2.0 mm seat
and still engage ~7 mm of thread without bottoming the pad, short enough not to protrude past the pad's
rear tip into open interior air if the flange turns out thinner than assumed. Mark this figure
`assumed` in the BOM row's source column and flag it for confirmation once a real Neutrik connector +
its actual flange thickness is measured against the `m3-thread-ladder`/`neutrik-tile` coupons (§4).
New row wording:

```
| M3×10 machine screw (plain, no insert) | N | Threads directly into the printed pad, replacing the heat-set-insert + M3×8 pair | docs/plans/2026-09-09-printed-m3-threads.md §2/§5 (length `assumed`, no sourced Neutrik/flange figure — confirm against m3-thread-ladder coupon) |
```

`N` (the count) is unchanged in every row — still 2 screws per connector × M connectors (6 or 8 per
SKU) — only the hardware itself and its row description change; the insert row simply disappears.

Do this by running the **`bom-update` skill** after the code change lands (it regenerates `BOM.md`
from the device/variant data, per its own scope) rather than hand-editing all 8 sections; if the skill's
generation logic still emits an insert-row for connector fixing after `neutrik.scad` no longer uses
`MCC_INSERT_M3` for this boss, that generation logic itself needs updating first — check
`bom-update`'s own source before assuming a hand-edit is the only path.

**Common-hardware section (`BOM.md:41-46`, "Panel plate retention")**: unchanged — this is the
plate-to-shell system (§0 scope correction), still 4× `MCC_INSERT_M3` + 4× M3 machine screw, untouched
by this ticket.

**Coupon test kit section (`BOM.md:85-107`)**: add a row for the `m3-thread-ladder` coupon (≥5 M3
machine screws, assorted 8–12 mm, to test-seat all 5 pads) alongside the existing `insert-boss`,
`tolerance-ladder` rows — same table shape as those.

## 6. Golden, skill, and architecture-record impact

**Goldens.** Every SKU's `<slug>.panel.json` (8 files, `tests/golden/*.panel.json`) changes — the pad
shape, bore, and mesh triangle count all move. `<slug>.base.json`/`.lid.json`/`.base_fan.json` are
**not** expected to move (the pads live entirely in the panel part, never composed into base/lid).
Run `python scripts/build.py golden --update` after the code change, but **only** for `.panel.json`
targets moving — if a `.base`/`.lid`/`.base_fan` golden also diffs, that is a real regression to
investigate, not something to wave through with `--update`. Volume delta per panel should be small
(threaded material removed vs. the old insert+clearance bore removed a similar order of material) —
if any panel's volume diff is large and unexplained, stop and check for a stray un-removed old-style
bore or a duplicated pad before accepting the new golden.

**`neutrik-panel` skill** (`.claude/skills/neutrik-panel/SKILL.md`): update the "Panel seat, bosses,
and fixing" section (currently lines 76-99). Replace the "local rear bosses... with an M3 heat-set
insert" / "Self-tapping directly into 2 mm of ASA is not an approved option" paragraph with the new
printed-thread description: pad on the plate rear, printed M3 thread via BOSL2 `screw_hole(thread=true)`,
cite this plan file, keep the "Neutrik MFD" alternative-option sentence (still true, still the
documented fallback if a specific connector class ever needs it), and add the render-time/`$fn=32`
note (§3.3) since it's a deviation from this skill's own governing `openscad-authoring` `$fn` policy
that a future reader of this skill needs to know is intentional. Also update the "Asserts that must
hold" table (currently lines 126-135) — replace the "Heat-set boss OD ≥ 1.8 × insert OD" row with the
two new T1-36 rows (pad wall, engagement turns) for the connector-fixing system, and add a note that
the plate's own 4 retention bosses (out of scope here) still follow the old rule.

**`architecture.md` §5 "Connector fixing"** (currently lines 398-436): this section currently states
"Self-tapping directly into 2 mm of ASA is not an approved option" and describes the heat-set-insert
boss as the "Preferred" option. Add a dated evolution note (matching this file's own revision-history
convention — a new numbered sub-bullet under §5, not a silent rewrite) recording: 2026-09-09, GitHub
issue #30, the connector's own two fixing screws move from heat-set-insert bosses to printed M3
threads in the same rear pad, justification (print orientation, §1 of this plan), and an explicit
note that the plate's own 4 retention bosses (the paragraph just above, "T1-35... insert therefore
goes in from the interior/rear tip") are **unchanged** — still heat-set inserts — so a future reader
does not conflate the two systems the way this ticket's own text did (§0). Also add the new T1-36
assert pair to `architecture.md` §9's Tier-1 assert table and to the "Plus 31 topology asserts" summary
paragraph (currently ends "...and T1-35 (no solid material on any fastener's screw axis between the
bearing face and its insert)" — append "T1-36 (connector-fixing thread pad wall thickness and
engagement, GitHub issue #30)"). Mirror the same addition in `layout-patch-wall.md` §9's own assert
table (the two files' assert tables are kept in sync per this repo's established convention).

**`.claude/knowledge/decision-log.md`** — if this file exists (check first; create it only if the
teamlead/architect directs it), record the option-A/B/C decision (§1) and its rationale in one entry,
per the Team Charter's "code comments are reserved for a single terse line... rationale goes in the
decision log" rule. Do not put narrative rationale in code comments beyond what is already specified
in §3.2's module-contract comment block above (which documents *what* and *why not the old shape*, the
minimum needed to stop a future reader re-deriving the Manifold constraint from scratch — this is
functional documentation of a non-obvious constraint, not ticket-referencing narrative, and stays
within the Team Charter's "single terse line on a truly exceptional quirk" allowance).

## 7. Ordered implementation steps and verification

1. **`lib/mcc/constants.scad`**: add the new constants block (§3.1), placed after
   `MCC_INSERT_BORE_EXTRA` (current line 324) and before the `MCC_PLATE_RIM_W` line.
2. **`lib/mcc/neutrik.scad`**: add `include <BOSL2/screws.scad>` near the top (next to the existing
   `include <BOSL2/std.scad>`); replace `mcc_neutrik_d_bosses()` per §3.2. Leave
   `mcc_neutrik_d_cutout()`, `mcc_neutrik_d_flange_outline()`, `mcc_neutrik_d_envelope()` untouched.
3. **`tests/test_neutrik.scad`**: rewrite the three `mcc_neutrik_d_bosses()` smoke-test cases
   (currently lines 22, 32-33, 41 — the default/min/max pattern). The old min/max cases were built
   around the insert-bore-depth boundary (`boss_h == insert_bore_depth exactly`), which no longer
   exists. Replace with: (a) default call, (b) a `pad_h` at the minimum that still satisfies
   `MCC_THREAD_ENGAGE_MIN_TURNS` (i.e. `MCC_THREAD_M3_CHAMFER + MCC_THREAD_ENGAGE_MIN_TURNS *
   MCC_THREAD_M3_PITCH` — exercises the T1-36b boundary), (c) a long `pad_h` (e.g. 12, matching the old
   test's "well past" spirit) to exercise a long thread cut. Remove every `MCC_INSERT_M3`/
   `insert_bore_depth`/`thru_depth` reference from this file.
4. **`models/coupons/m3-thread-ladder.scad`**: create per §4.
5. **`scripts/build.py`**'s coupon discovery is directory-scan based (per `build.py doctor`'s own
   output listing every `models/coupons/*.scad` as a discovered target) — confirm the new coupon is
   picked up automatically by re-running `python scripts/build.py doctor` and checking it appears in
   the "Discovered targets" list; no registration step should be needed, but verify rather than assume.
6. **Render and check, in this order** (stop and investigate rather than pushing through a failure at
   any step):
   - `python scripts/build.py smoke` — Tier-2, exercises `tests/test_neutrik.scad`'s new cases and
     every model's CSG tree (fast, asserts-only).
   - `python scripts/build.py render` — full STL renders, all 8 models' `panel` part plus the new
     coupon and `neutrik-tile`.
   - `python scripts/build.py check` — mesh checks (watertight, single shell) on the panel parts
     specifically; this is the direct test for "did the Manifold blind-bore defect come back."
   - `python scripts/build.py golden --update` — **only** for the `.panel.json` targets that legitimately
     move (§6); verify no `.base`/`.lid`/`.base_fan` golden moved.
7. **BOM**: run the `bom-update` skill/flow (§5); verify all 8 SKU sections lost their insert row and
   gained the new M3×10 screw row, and the coupon-kit section gained the `m3-thread-ladder` row.
8. **Docs**: update `.claude/skills/neutrik-panel/SKILL.md` (§6), `architecture.md` §5 and §9 (§6),
   `layout-patch-wall.md` §9 (§6).
9. **Full gate**: `python scripts/build.py all` green before any PR.
10. **Physical verification (Tier-4, blocking before any production trust in this feature, per this
    repo's own Tier-4 policy)**: print `m3-thread-ladder` and `neutrik-tile` on the X1C in ASA, thread a
    real M3 machine screw into all 5 ladder pads and the tile's connector pads, record the
    tightest-that-still-threads-cleanly `$slop` value, update `MCC_THREAD_M3_SLOP`'s comment with the
    measured value + coupon name + date (never silently — this project's established convention,
    `MCC_INSERT_M3`'s own comment block is the template to follow).

## 8. `PLAN-ASSUMPTION` list

1. **`MCC_THREAD_M3_SLOP = 0.15 mm` is assumed**, not measured. Sourced range 0.10–0.20 mm per-side
   for a well-tuned 0.4 mm-nozzle FDM machine (Sovol3D, "3D Printing Threads and Screws: How to Design
   Reliable FDM Fasteners" — fetched during this research pass, no ASA-specific number published, PLA/
   general FDM guidance only). Genuinely `assumed` until the `m3-thread-ladder` coupon is printed and
   measured (§7 step 10) — do not treat any print before that as validating this figure.
2. **M3 is below several sourced guides' "conservative" floor for printed internal threads.** The same
   Sovol3D source recommends **M6 and larger** as the safe conservative default for 0.4 mm-nozzle FDM,
   explicitly calling M3–M5 possible only "on well-tuned machines" requiring "precise clearance
   calibration and test prints." This is a real risk to this ticket's whole premise, not just a
   tuning detail — **flag this to the user/architect explicitly, do not silently proceed as if M3
   printed threads are a routine choice.** Mitigation already built into this plan: the coupon-first
   Tier-4 gate (§7 step 10) is exactly the mechanism that catches this before any full case is printed,
   and the pad/wall/engagement sizing in §3 already targets the upper end of what sourced guidance
   considers viable for a small thread (12 turns engaged, 2.34 mm wall, both well past the sourced
   minimums). If the coupon fails (threads shear, strip, or won't reliably start), the documented
   fallback is: **the pad geometry is otherwise unchanged from today's heat-set-insert boss (§1's
   "pinned equal to old boss OD" decision was chosen partly for this reason)** — reverting to a heat-
   set insert in the same pad is a small, contained change (swap the bore logic back), not a case
   redesign, precisely because this plan did not touch the pad's external footprint or the wall
   aperture. Record this fallback path explicitly if the coupon result comes back negative.
3. **Flange thickness for the BOM screw-length figure (§5) is `unknown`** — no D-series drawing in
   `knowledge/neutrik/**` gives a flange stock thickness. M3×10 mm is a reasoned starting figure, not a
   sourced one; confirm against a real connector once purchased.
4. **`MCC_THREAD_M3_CHAMFER = 1.0 mm` and the exact BOSL2 `bevel1` geometry it produces are not
   cross-checked against each other numerically** — the plan instructs the implementing developer to
   verify the rendered chamfer lands near the sourced 0.8–1.5 mm target and adjust if `screw_hole()`'s
   default bevel sizing doesn't match, rather than asserting a number this research pass could not
   verify against BOSL2's actual bevel implementation without a deeper code read than this pass's
   effort budget allowed.
5. **`$fn=32` for the thread specifically (vs. the repo's blanket `$fn ≥ 64`) is this plan's own
   recommendation, not independently corroborated by a second source** — justified here by the
   measured render-time/file-size data (§3.3) and the general engineering observation that thread-crest
   facet count matters far less than hole-diameter facet count for a part whose real limiting factor is
   nozzle extrusion width, not a citation. If the architect or user disagrees, `$fn=64` still works
   (§3.3's table gives its exact cost) — this is a cost/quality tradeoff call, not a correctness one.

---

## 9. Architect verdict — 2026-09-09 (architecture.md rev 10)

**Verdict: APPROVE WITH CHANGES — 7 blocking (B1–B7).** The design decision at the heart of this
plan (option C: extend the existing rear pad, pin its OD/height to today's values) is **correct and
approved**, and the pinning is the single best call in the document — it is what keeps the wall
window, `d_rel = 8.88` and every T1-34a–d number numerically unchanged, and it is what makes the
R28 fallback a one-module revert instead of a case redesign. The scope correction in §0 (two flange
holes, not four; the plate's own 4 retention bosses stay heat-set inserts) is also correct.

**B1 is a correctness defect that would have reached the printer.** As written, the plan produces
**no thread at all**.

### Blocking changes

| # | Change | Why |
|---|---|---|
| **B1** | **`MCC_THREAD_M3_SLOP = 0.15` → `0.05`**, and re-cut the coupon ladder to `[0.02, 0.035, 0.05, 0.065, 0.08]`. | BOSL2 enlarges an internal thread by **`4·$slop` in diameter** (`lib/BOSL2/screws.scad:753`, `lib/BOSL2/threading.scad:179`) = **`2·$slop` per side**. M3×0.5 has only `0.5·(3.000 − 2.459) = 0.2705 mm` of radial thread engagement. At `$slop = 0.15` the hole grows **0.30 mm per side** — more than the entire thread depth. The result is a plain ⌀3.6 bore with the thread mathematically erased. Ladder rungs 0.15/0.20/0.25 are all degenerate (plain ⌀3.6/3.8/4.0 bores), so **3 of the 5 rungs test nothing**. `$slop = 0.05` is BOSL2's own tested figure (`screws.scad:767`). §2's text is self-contradictory — it quotes "4·$slop" and then calls $slop "per-side"; per-side is `2·$slop`, so the sourced 0.10–0.20 mm per-side range maps to `$slop = 0.05–0.10`, not 0.15. |
| **B2** | **Renumber `T1-36a`/`T1-36b` → `T1-42a`/`T1-42b`.** | **T1-36 … T1-41 are already allocated** by rev 9 (`layout-patch-wall.md:14`, issues #25/#26/#29/#24). Next free number is T1-42. |
| **B3** | **`bevel1=true` → `bevel2=true`**, and **`MCC_THREAD_M3_CHAMFER = 1.0` → `0.5`** (sourced, not `assumed`). | With `anchor=BOTTOM` at `z = −pad_h`, the hole's *bottom* is the pad's **rear tip**; the screw enters at the pad's panel-facing face, which is the hole's **top**. `bevel1` chamfers the wrong end — it removes engagement at the far tip and leaves no lead-in where the screw actually starts. Resolves PLAN-ASSUMPTION 4: `screws.scad:995` sets `bevelsize = pitch`, so BOSL2's bevel is **0.5 mm**, not 1.0. The repo's "never invent a dimension" rule applies — this is now derivable, so it must not stay `assumed`. Turns become `(7.0 − 0.5)/0.5 = 13`, still ≫ 3. |
| **B4** | **`lib/mcc/layout.scad:189` must derive `d_rel` from `MCC_THREAD_M3_PAD_D`**, i.e. `d_rel = MCC_THREAD_M3_PAD_D + 2*MCC_CLR_SLIDE`. | The plan pins `MCC_THREAD_M3_PAD_D = 8.28` as a bare literal and *explicitly decouples it* from `MCC_INSERT_M3` — but `layout.scad:189` still computes the mating relief as `MCC_BOSS_MIN_RATIO * MCC_INSERT_M3.od + 2*MCC_CLR_SLIDE`. That leaves **two independent sources for one physical diameter**, and the drift path is live because the plate-fixing bosses keep using `MCC_INSERT_M3`. This is exactly §3's "both halves of a mating interface must come out of one file or they drift" (the D6 / `rail.scad` rule). `layout.scad:395`'s `insert_hole_r` (T1-34d) legitimately **stays** on `MCC_INSERT_M3` — that one is the shell's own plate-fixing boss. Numerically 8.28 either way; **no geometry moves.** |
| **B5** | **Extract a public `mcc_thread_pad(pad_d, pad_h, slop)` in `neutrik.scad`.** `mcc_neutrik_d_bosses()` calls it twice; the coupon calls it through the barrel. Coupon drops `include <BOSL2/screws.scad>`. | As drafted, `models/coupons/m3-thread-ladder.scad` calls BOSL2 `screw_hole()` directly and hand-rebuilds the pad — an L4 file duplicating L1 geometry, against §3 ("model files import **only** `<mcc/mcc.scad>`") and §4 (copied geometry drifts). It also defeats the coupon's own purpose: a ladder that can drift from production geometry cannot calibrate a production constant. Keep the module in `neutrik.scad` for now — its natural long-term home is `fasteners.scad`, but moving it there today would create the repo's **first L1→L1 edge** for no benefit. Move it when/if the follow-up ticket converts `shell.scad`'s 4 plate-fixing bosses (`shell.scad` already uses `fasteners.scad`). |
| **B6** | **Rename `MCC_THREAD_PREVIEW` (default `true`) → `MCC_THREAD_FAST` (default `false`)**, opt **in** to the cheap bore via `-D MCC_THREAD_FAST=true`. | `PREVIEW=true` meaning "render the *expensive real* thread" reads backwards to every future reader, and a default-`true` flag whose dangerous state is `false` inverts the repo's existing convention. `MCC_SHOW_GHOST` is the precedent: a `constants.scad` variable, default `false`, opt-in by `-D` (`docs/plans/2026-09-08-l2-first-case.md:725`). **Mechanism = `-D`, not a `build.py` build-time flag** — §8 already requires the full `-D` set in every manifest, so the fast path self-documents in every artefact. **Goldens, CI `render`, `check`, and every release/coupon export use the real thread (the default)**, which makes a stray fast-path render fail the golden automatically. §3.1's comment "NEVER set false for a release export" is not a gate; the golden is. |
| **B7** | **STEP export of the `panel` part must use the thread-free geometry.** Render a second `panel._step.stl` with `-D MCC_THREAD_FAST=true`, convert that, and record `"threads": "omitted"` plus the `-D` set in the manifest's `step` sub-object (`build.py:531`). **Policy change — needs the user's nod (see "Escalated" below).** | The plan is silent on STEP. `scripts/mesh_to_step.py` sews **one planar face per triangle** and then merges only *coplanar* facets via `ShapeUpgrade_UnifySameDomain` (`mesh_to_step.py:5-8,186`). A helical thread flank has **no coplanar neighbours**, so ~30 k facets per panel survive as ~30 k separate B-rep faces (≈0.5 M+ STEP entities per panel). `cmd_step` converts an already-rendered STL (`build.py:578`), so this is a real pipeline step, not a flag. A 30 k-face faceted helix is worse than useless to a CAD consumer; STEP is an interchange artefact, not a print artefact. |

### Rulings on the specific questions asked

**`$fn = 32` exception — APPROVED, narrowly, with one correction.** §3's `$fn` policy exists so that
a hole which must pass a real part is *circumscribed*, because an inscribed polygon undersizes it.
`screw_hole()` accepts no `circum`, so that mechanism is unavailable — but the inscribed error at
`$fn = 32` on ⌀3.0 is `3.0·(1 − cos(180/32))/2 = 0.0072 mm per side`, i.e. **2.7 % of the thread's
0.27 mm engagement** and ~7 % of the corrected `$slop` term. The fit is carried by `$slop`, not by
facet count, so the policy's *intent* is satisfied. Grant the exception **scoped to the thread bore
only**, on two conditions: (i) **the pad's outer cylinder keeps `$fn = 64`** — the plan drops it to
32 for no reason; it is an additive boss, the saving is ~30 facets, and the change churns geometry
this ticket has no need to touch; (ii) the carve-out is written into `architecture.md` §3 as a
**named, bounded** exception, not as a general loosening.

**Preview fast-path — APPROVED as a `-D` define, not a build-time flag.** See B6.

**STL size / release zips — accepted, but the plan is optimising the wrong lever.** The measured
9.1 MB at `$fn = 32` is an **ASCII** STL (29,740 facets × ~300 B). `build.py` writes `-o <part>.stl`
(`build.py:64,423`) with no `--export-format`, so OpenSCAD emits ASCII. **Binary STL would be
~1.5 MB — a 6× reduction, lossless, three times better than the 2× the `$fn` downgrade buys.**
**Do not fold this into #30**: it changes every export in the repo and the provenance of every
golden. Raise it as a separate ticket. Meanwhile the release-zip cost is ~9 MB per SKU on the
**panel STL only** (base/lid untouched), ~72 MB across 8 SKUs; 3MF is zipped XML and will be far
smaller. Acceptable in the interim given the binary-STL lever exists.

**M3-below-M6 premise — recorded as R28, coupon is the gate.** The plan's own mitigation is sound
and the fallback is genuinely cheap *because* of the pinned OD/height. One addition, and it is not
optional: **R28's real exposure is not "the thread strips once" but "the thread strips after N
re-openings."** A connector gets unscrewed for cable service; that repeat duty cycle is the exact
failure mode heat-set inserts exist to prevent. **The coupon acceptance criterion must therefore be
≥ 5 insert/remove cycles per pad, not a single successful seat.** A ladder that only proves "a screw
went in once" does not retire R28.

**Pad height vs `max_panel_t` — CHECKED, no violation, and no new risk.** `mcc_panel_max_t()`
(`constants.scad:708`) is compared against **`seat_t` only** (`neutrik.scad:62-65`); `seat_t` stays
2.0 and every part's `max_panel_t` is 2.0 or 4.0 (`constants.scad:679-683`) — untouched by this
ticket. The pad is rear-side boss material at the screw positions, not panel thickness at the flange
seat, and §5 already sanctions "protruding rearward from the 2.0 mm seat to ~7 mm total". Because
pad OD **and** height are numerically unchanged, **every** connector-body/latch clearance question
is exactly as it was before #30. *Pre-existing item recorded, not a #30 blocker:* the pad at radius
`norm([9.5, 12]) = 15.28` with OD 8.28 reaches inward to `r = 11.14`, i.e. **inside** the ⌀24.2
cutout radius 12.1, by ~0.96 mm over the full 7 mm of pad depth — the same ~1 mm the wall-relief
intrusion records (T1-34b, 1.04–1.24 mm). Whether a fitted connector's rear body clears it is
**unverified**, because `neutrik-tile` has never been printed. #30 makes that pad load-bearing in a
new way, so **print `neutrik-tile` physically in the same batch as `m3-thread-ladder`** — the plan
only re-*renders* it.

**Thread orientation — CONFIRMED CORRECT.** `.claude/skills/print-check/SKILL.md:59` pins the
connector panel plate to "**Face-down, flat on the bed**". With the front face at local `Z = 0` and
the pad growing to `Z = −pad_h`, model `−Z` is printer `+Z`: the bore axis is **vertical**, one full
circle per layer, no bridging and no thread-flank overhang, and the bore is open at both ends (pad
tip up, plate clearance hole down at the bed). The plan's reasoning and its rejection of option B
(horizontal M3 bore in a vertical shell wall) are both sound.

**Screw length (M3×10, `unknown` sourcing) — accepted as a starting figure, BOM wording corrected.**
Two points the plan under-sells: (a) the bore is a genuine **through**-hole, so an over-long screw
**cannot bottom out and jack the connector off its seat** — it simply protrudes into a 34–40 mm-deep
bay, which is clear. **Under**-length is the only real failure mode, so the BOM row must state the
*minimum*, not just a nominal: `≥ flange_t + MCC_PANEL_SEAT_T (2.0) + 3 × MCC_THREAD_M3_PITCH (1.5)`.
(b) The plan is right that Neutrik ships **self-tapping** screws (`d-series-cutout.md:100-104`) —
those must **not** be driven into a printed M3 thread. That needs an explicit build-sheet line,
because the obvious builder error is to use the screws that came in the box.

**Assert list — T1-42a/b as proposed, plus a mandatory T1-42c; no neighbour-collision assert needed.**

| Assert | Condition | Value after B1/B3 |
|---|---|---|
| **T1-42a** | pad wall `(pad_d − (major + 4·$slop))/2 ≥ MCC_THREAD_WALL_MIN (2.0)` | **2.44 mm** ✓ |
| **T1-42b** | engagement `(pad_h − chamfer)/pitch ≥ MCC_THREAD_ENGAGE_MIN_TURNS (3)` | **13 turns** ✓ |
| **T1-42c** | **NEW, required** — residual radial engagement `0.5·(major − minor) − 2·$slop ≥ MCC_THREAD_ENGAGE_MIN_RADIAL` (0.135 = 50 % of nominal). Needs `MCC_THREAD_M3_MINOR_D = 2.459` (ISO 68-1). | **0.1705 ≥ 0.135** ✓ — and at the plan's original `$slop = 0.15` it evaluates to **−0.0295 and fails loudly.** This is the assert that would have caught B1; it is mandatory, not nice-to-have. |

**No neighbouring-slot assert is required.** Pad OD and positions are unchanged, and the two pads of
one connector sit on the *diagonal*. At the 32 mm minimum slot pitch the nearest pads of adjacent
slots are `Δx = 32 − 19 = 13`, `Δy = 24` → **27.3 mm apart**, against an 8.28 mm OD. Real pitch
today is 41.97–63.45 mm (`architecture.md` §11 R3). Existing T1-34c/T1-34d plus the ≥32 mm
slot-pitch assert already bound this; adding another would be redundant. Arithmetic recorded here so
nobody re-derives it.

**Goldens — 8 `.panel.json` move, and sequencing matters.** Agreed that `.base`/`.lid`/`.base_fan`
must **not** move, and that a diff there is a regression to investigate rather than `--update`
through. One addition: **regenerate goldens only *after* B1's `$slop` fix.** Running
`golden --update` on the 0.15 value would commit a threadless bore as the accepted baseline, and the
defect would then be invisible to every future review.

### Escalated to teamlead/user — one item

**B7 is a change to §8's export policy, not a correctness fix**, so it is the one item I will not
decide alone: *should the `panel` part's STEP ship without threads?* My recommendation is **yes**
(a faceted helix has negative value to a CAD consumer, and the STL/3MF carry the real geometry), but
it needs confirmation that nobody consumes the panel STEP expecting a threaded feature. **If the
answer is slow, the fallback is "skip STEP for the `panel` part entirely"** — a one-line change
either way, and it does not block B1–B6.

### Dispatch

**Cleared to dispatch now** on base `feature/plans-2026-09-09`, branch
`feature/issue-30-printed-m3-threads` — **scoped to B1–B6**, which are self-contained and touch no
build tooling. **Carve B7 out** and hold it for the user's answer; it is the only item that touches
`scripts/build.py`. Sequence within the branch: B1+B3 (constants) → B2 (assert numbers) → B4
(`layout.scad` single-source) → B5 (`mcc_thread_pad()` extraction) → B6 (flag rename) → tests →
coupon → `build.py all` → goldens **last**.
