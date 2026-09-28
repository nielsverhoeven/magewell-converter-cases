//////////////////////////////////////////////////////////////////////
// LibFile: mcc/fan.scad
//   L1. Fan bay review ghost (mcc_fan_envelope(), NOT the reservation -- see its doc), cutout
//   (mounting holes + opening/grille).
//   knowledge/components/fans.md. `use`d by lib/mcc/mcc.scad.
// Includes:
//   include <mcc/mcc.scad>
//////////////////////////////////////////////////////////////////////

include <BOSL2/std.scad>
include <constants.scad>
use <util.scad>

// Z-axis convention -- the two modules below use OPPOSITE senses:
//   - mcc_fan_cutout(): local Z = [0, wall_t] spans the mounting wall (matching neutrik.scad/
//     fasteners.scad); callers place it with rotate([0,90,0]) so local +Z -> world +X, outward
//     (vents.scad).
//   - mcc_fan_envelope(): local Z = 0 at the fan's mounting plane (the wall's INNER face), growing
//     toward +Z INTO the case interior by the fan's own frame depth plus MCC_FAN_INTAKE_CLR;
//     callers place it with rotate([0,-90,0]) so local +Z -> world -X, inward (shell.scad).

// mcc_fan_spec() MOVED to constants.scad (L0), rev 11 (#32, architect verdict B7) — it is a pure
// function over an L0 table, and layout.scad (which may not `use` this L1 file) needs it too. This
// file still calls it below; the call resolves via constants.scad, which fan.scad already
// `include`s.

// Module: mcc_fan_envelope()
// Usage:
//   mcc_fan_envelope([name]);
// Description:
//   REVIEW-ONLY ghost of the fan bay's reserved keep-out volume: the fan's own frame footprint
//   extruded to its frame depth plus MCC_FAN_INTAKE_CLR. `%`-ed and gated behind MCC_SHOW_GHOST
//   (default false), like every other ghost in this repo -- architecture.md §7 "Ghost rendering",
//   both belts: `%` is the mechanism, the flag is the review signal.
//   THIS MODULE IS NOT THE RESERVATION. The reservation of record is numeric: fan_bay_x/y/z from
//   mcc_case_layout() (layout.scad), enforced by T1-46a-d there and by T1-18(c) in shell.scad.
//   architecture.md §6 rev 12 / §13 D23 -- a solid box cannot be the reservation, because §3
//   forbids layout.scad (where the checks live) from `use`-ing this file at all.
//   LOCAL FRAME: Z = 0 at the fan's mounting plane (the wall's INNER face), growing toward +Z INTO
//   the case interior. That is the OPPOSITE sense to mcc_fan_cutout() below, whose local
//   Z = [0, wall_t] spans the wall outward. Callers therefore need rotate([0,-90,0]) for this
//   module and rotate([0,90,0]) for the cutout -- see shell.scad's and vents.scad's call sites.
// Arguments:
//   name = fan name, key into MCC_FANS. Default: MCC_FAN_DEFAULT.
module mcc_fan_envelope(name = MCC_FAN_DEFAULT) {
    spec  = mcc_fan_spec(name);
    frame = struct_val(spec, "frame");
    depth = frame[2] + MCC_FAN_INTAKE_CLR;
    if (MCC_SHOW_GHOST) {
        %translate([0, 0, depth / 2])
            cube([frame[0], frame[1], depth], center = true);
    }
}

// Module: _mcc_fan_grille_2d()
// Description:
//   Private helper: a 2D finger-guard grille (concentric rings + radial spokes) — the SOLID guard
//   bars, not the cut. mcc_fan_cutout() subtracts `circle(d) - _mcc_fan_grille_2d(d)` (opening minus
//   bars), not the bars directly (issue #11 — see mcc_fan_cutout()'s own comment for the root cause
//   this fixes). Every ring/spoke/hub piece here must end up ONE connected body, flush with the
//   wall at r=d/2, or it becomes a floating mesh island again the instant it is used as a cut mask.
// Arguments:
//   d = overall grille diameter, mm (matches the aperture opening_d — the guard fills the WHOLE
//       opening so its outer rim is flush with the wall, see `pitch` below).
module _mcc_fan_grille_2d(d) {
    ring_w   = 1.8; // finger-guard ring width, mm >= 1.6 (this file's module contract). assumed.
    gap_w    = 3.0; // MINIMUM clear gap between rings, mm. assumed — narrow enough to guard
                     // fingers, no sourced figure exists for this project-specific grille geometry;
                     // also this file's/architecture.md's self-supporting-span ceiling (<=10 mm,
                     // `fdm-rugged-enclosure-guidelines.md:111`, layout-patch-wall.md:763) for the
                     // open (cut-away) span between two rings.
    spoke_w  = 2.0; // spoke width, mm (this file's module contract). assumed.
    n_spokes = 6;   // assumed spoke count.
    r_max    = d / 2;
    n_rings  = max(1, floor(r_max / (ring_w + gap_w)));
    // Evenly redistribute r_max across n_rings instead of pitch-stepping from the centre and
    // clamping the last ring short (the old behaviour): `pitch >= ring_w + gap_w` always holds
    // (n_rings is a floor of r_max/(ring_w+gap_w)), and ring n_rings's own r_out lands EXACTLY on
    // r_max by construction. That flush outer ring is what fuses the whole guard to the
    // surrounding wall along the full aperture rim once mcc_fan_cutout() cuts "opening - bars"
    // instead of "bars" — a ring that stopped short of r_max (the pre-fix code: `min(r_max, i *
    // (ring_w+gap_w))`) left an un-guarded, fully open annulus between the guard and the wall,
    // severing the guard from the case entirely (still 1 disconnected part, just consolidated
    // into one big island instead of 18 small ones).
    pitch = r_max / n_rings;

    // Spoke angles are chosen for the print pose, not for looks: the base prints open-side-up with
    // the fan in a VERTICAL +X end wall, and the only caller (mcc_vents(), rotate([0,90,0])) maps
    // this 2-D frame's +X to world -Z (straight DOWN) and +Y to world +Y (horizontal). A spoke must
    // therefore run along local +X: it is the only thing under each ring's lowest point. Without it
    // (the previous 30 deg offset, which also left spokes at local 90/270 deg = dead horizontal) the
    // bottom of every inner ring started in mid-air — Bambu Studio's "floating regions" warning on
    // every fan=true base (2026-09-27, scripts/printability.py: islands at z=12.9/19.3 on
    // pro-convert-for-ndi-to-hdmi base_fan). Offset 0 puts spokes at straight down/up and +-60 deg
    // from vertical — none horizontal. Connectivity does not depend on the angle (every spoke
    // overlaps every ring).
    spoke_offset = 0;

    union() {
        for (i = [1 : 1 : n_rings]) {
            r_out = i * pitch;
            r_in  = max(0, r_out - ring_w);
            difference() {
                circle(d = 2 * r_out, $fn = 96);
                if (r_in > 0) circle(d = 2 * r_in, $fn = 96);
            }
        }
        for (a = [spoke_offset : 360 / n_spokes : 359]) {
            rotate([0, 0, a])
                translate([0, -spoke_w / 2])
                    square([r_max, spoke_w]);
        }
        circle(d = spoke_w, $fn = 32); // Center hub: every spoke's inner edge already passes
                                        // through the origin (square([r_max,spoke_w]) is corner-
                                        // anchored at (0,-spoke_w/2)), so the 6 rotated spokes
                                        // already overlap there in practice — this hub is a cheap,
                                        // rotation-math-independent guarantee that the spokes fuse
                                        // into one body at the centre rather than 6 separate radial
                                        // fingers meeting at a single, potentially degenerate point.
    }
}

// Module: mcc_fan_cutout()
// Usage:
//   mcc_fan_cutout(name, [wall_t=], [grille=]);
// Description:
//   Negative: 4 mounting screw clearance holes at the fan's pitch, plus either a plain round
//   opening (⌀ = frame width - 2 mm) or, when `grille=true`, that same round opening with an
//   integral finger-guard grille left standing in it (the grille bars are excluded from the cut,
//   not cut themselves). $fn=96 on the plain opening (architecture.md:130-134 hole policy).
//   ISSUE #11 ROOT CAUSE (build.py check: fan=true base rendered watertight but parts=19): the
//   pre-fix code subtracted `_mcc_fan_grille_2d()` (the rings/spokes/hub shape) DIRECTLY as the
//   cut mask, i.e. it cut the BARS out of the wall and left the GAPS between them as solid. Because
//   the gaps are bounded on every side by ring cuts (radially) and spoke cuts (angularly), the
//   "solid" left behind wasn't the wall at all — it was 18 isolated wedge-shaped islands (3 inter-
//   ring gaps x 6 spoke sectors on this SKU's 38 mm aperture) floating inside the hole, each spoke-
//   and-ring-locked slice being its own disconnected mesh part (plus the 1 real shell = 19). FIX:
//   cut `circle(d=opening_d) - _mcc_fan_grille_2d(opening_d)` (opening MINUS bars) instead of the
//   bars alone, so the rings/spokes/hub are excluded from the removed material and remain standing
//   as one solid, fused to the wall along the full aperture rim (see _mcc_fan_grille_2d()'s own
//   comment for why the outer ring must land exactly on r_max for that fusion to hold).
// Arguments:
//   name    = fan name, key into MCC_FANS. Default: MCC_FAN_DEFAULT.
//   wall_t  = wall thickness at the fan bay, mm. Default: MCC_WALL.
//   grille  = cut an integral finger-guard grille instead of one open hole. Default: false.
module mcc_fan_cutout(name = MCC_FAN_DEFAULT, wall_t = MCC_WALL, grille = false) {
    spec      = mcc_fan_spec(name);
    frame     = struct_val(spec, "frame");
    pitch     = struct_val(spec, "pitch");
    hole_d    = struct_val(spec, "hole_d");
    opening_d = frame[0] - 2; // this file's module contract: "round opening ⌀(size-2)".
    cut_h     = wall_t + 2 * MCC_EPS;

    union() {
        for (sx = [-1, 1]) for (sy = [-1, 1])
            translate([sx * pitch / 2, sy * pitch / 2, wall_t / 2])
                cyl(h = cut_h, d = hole_d, circum = true, $fn = 64);

        translate([0, 0, wall_t / 2])
            if (grille) {
                linear_extrude(height = cut_h, center = true)
                    difference() {
                        circle(d = opening_d, $fn = 96);
                        _mcc_fan_grille_2d(opening_d);
                    }
            } else {
                cyl(h = cut_h, d = opening_d, circum = true, $fn = 96);
            }
    }
}

// vim: expandtab tabstop=4 shiftwidth=4 softtabstop=4 nowrap
