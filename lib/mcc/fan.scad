//////////////////////////////////////////////////////////////////////
// LibFile: mcc/fan.scad
//   L1. Fan bay envelope (reservation keep-out), cutout (mounting holes + opening/grille).
//   knowledge/components/fans.md. `use`d by lib/mcc/mcc.scad.
// Includes:
//   include <mcc/mcc.scad>
//////////////////////////////////////////////////////////////////////

include <BOSL2/std.scad>
include <constants.scad>
use <util.scad>

// Z-axis convention: the fan's mounting wall spans Z=[0, wall_t] (matching neutrik.scad/
// fasteners.scad); the fan envelope's local frame has Z=0 at the mounting plane, growing toward
// +Z (into the case interior) by the fan's own frame depth plus intake clearance.

// Function: mcc_fan_spec()
// Usage:
//   spec = mcc_fan_spec(name);
// Description:
//   Looks up a fan record (frame/pitch/hole_d) from MCC_FANS (constants.scad) by name, e.g.
//   "NF-A4x10" or "NF-A6x25".
function mcc_fan_spec(name) =
    let(ind = search([name], MCC_FANS)[0])
    assert(ind != [], str("mcc: unknown fan \"", name, "\""))
    MCC_FANS[ind][1];

// Module: mcc_fan_envelope()
// Usage:
//   mcc_fan_envelope(name);
// Description:
//   Pure keep-out reservation box: the fan's own frame footprint extruded to its frame depth
//   plus a 5 mm intake clearance beyond it. architecture.md:234-238 "the reservation rule ...
//   shell.scad always reserves the fan bay ... even when fan=false"; this module is the thing
//   `shell.scad` (not built in this session) reserves against — separate from the module that
//   cuts real geometry (mcc_fan_cutout(), below), per architecture.md:236-238.
// Arguments:
//   name = fan name, key into MCC_FANS.
module mcc_fan_envelope(name) {
    spec  = mcc_fan_spec(name);
    frame = struct_val(spec, "frame");
    clr   = 5; // intake clearance, mm. assumed — generic unobstructed-intake allowance; no sourced
               // figure in knowledge/components/fans.md (which gives frame/pitch only).
    translate([0, 0, (frame[2] + clr) / 2])
        cube([frame[0], frame[1], frame[2] + clr], center = true);
}

// Module: _mcc_fan_grille_2d()
// Description:
//   Private helper: a 2D finger-guard grille (concentric rings + radial spokes), used by
//   mcc_fan_cutout() when grille=true.
// Arguments:
//   d = overall grille diameter, mm.
module _mcc_fan_grille_2d(d) {
    ring_w   = 1.8; // finger-guard ring width, mm >= 1.6 (this file's module contract). assumed.
    gap_w    = 3.0; // clear gap between rings, mm. assumed — narrow enough to guard fingers, no
                     // sourced figure exists for this project-specific grille geometry.
    spoke_w  = 2.0; // spoke width, mm (this file's module contract). assumed.
    n_spokes = 6;   // assumed spoke count.
    r_max    = d / 2;
    n_rings  = max(1, floor(r_max / (ring_w + gap_w)));

    union() {
        for (i = [1 : 1 : n_rings]) {
            r_out = min(r_max, i * (ring_w + gap_w));
            r_in  = max(0, r_out - ring_w);
            difference() {
                circle(d = 2 * r_out, $fn = 96);
                if (r_in > 0) circle(d = 2 * r_in, $fn = 96);
            }
        }
        for (a = [0 : 360 / n_spokes : 359]) {
            rotate([0, 0, a])
                translate([0, -spoke_w / 2])
                    square([r_max, spoke_w]);
        }
        circle(d = spoke_w, $fn = 32); // center hub, keeps the innermost spokes connected.
    }
}

// Module: mcc_fan_cutout()
// Usage:
//   mcc_fan_cutout(name, [wall_t=], [grille=]);
// Description:
//   Negative: 4 mounting screw clearance holes at the fan's pitch, plus either a plain round
//   opening (⌀ = frame width - 2 mm) or, when `grille=true`, an integral finger-guard grille cut
//   through the wall instead of one open hole. $fn=96 on the plain opening
//   (architecture.md:130-134 hole policy).
// Arguments:
//   name    = fan name, key into MCC_FANS.
//   wall_t  = wall thickness at the fan bay, mm. Default: MCC_WALL.
//   grille  = cut an integral finger-guard grille instead of one open hole. Default: false.
module mcc_fan_cutout(name, wall_t = MCC_WALL, grille = false) {
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
                    _mcc_fan_grille_2d(opening_d);
            } else {
                cyl(h = cut_h, d = opening_d, circum = true, $fn = 96);
            }
    }
}

// vim: expandtab tabstop=4 shiftwidth=4 softtabstop=4 nowrap
