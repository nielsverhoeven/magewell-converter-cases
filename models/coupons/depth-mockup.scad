//////////////////////////////////////////////////////////////////////
// models/coupons/depth-mockup.scad
//   Tier-4 physical coupon (architecture.md §9). A U-shaped jig: a real panel cutout at one end,
//   a mock "device port face" block at a distance `bay` (default mcc_bay_depth(part)) from the
//   panel's flange front, and a 5 mm scale engraved along a side rail so the real patch cable can
//   be tried and the needed depth read off directly. This is the ONLY way to replace the
//   `assumed` mating-plug lengths in constants.scad (architecture.md §11 R2).
//
// Render:
//   openscad --backend=Manifold -o out/depth-mockup.stl models/coupons/depth-mockup.scad
//   openscad --backend=Manifold -D 'part="NE8FDP-B"' -D 'bay=60' -o out/depth-mockup-rj45.stl models/coupons/depth-mockup.scad
//////////////////////////////////////////////////////////////////////

$fa = 1; $fs = 0.4;

include <mcc/mcc.scad>

// -D part="..." switches the connector; -D bay=<mm> overrides the default budgeted depth.
part = "NAHDMI-W-B";
bay  = mcc_bay_depth(part);

PLATE_T = 2.0; // brief's explicit instruction: "a 2 mm panel plate".
FACE_T  = 3.0; // mock device port face block thickness, mm. assumed.
RAIL_W  = 8;   // side rail width, mm. assumed — rigid enough to keep the two ends aligned.
RAIL_T  = 3.0; // side rail thickness, mm. matches MCC_WALL.
JIG_W   = MCC_D_FLANGE[0] + 14; // flange width + margin, mm.
JIG_H   = MCC_D_FLANGE[1] + 14; // flange height + margin, mm.
TICK    = 5;   // brief's explicit instruction: "a 5 mm scale ruler".

// Depths below are measured from the panel's FRONT (flange) face, matching Neutrik's own
// "depth behind panel" convention (knowledge/neutrik/placement-and-depth.md:5-8) and
// mcc_bay_depth()'s own definition (architecture.md:294-295).
d_face_near = bay;          // mock face's near side, at depth = bay behind the flange front.
d_face_far  = bay + FACE_T; // mock face's far side / overall jig depth.

echo(str(
    "depth-mockup: part=\"", part, "\" bay=", bay, " plate_t=", PLATE_T, " total_depth=", d_face_far
));

// Z-axis convention: matches lib/mcc/neutrik.scad — the panel wall spans Z=[0, PLATE_T], flange
// front at Z=PLATE_T. "Depth behind panel" d then maps to Z = PLATE_T - d (increasing d = more
// negative Z = further into the case interior).
difference() {
    union() {
        // Panel wall with the real cutout.
        difference() {
            linear_extrude(height = PLATE_T)
                square([JIG_W, JIG_H], center = true);
            mcc_panel_cutout(part, seat_t = PLATE_T, panel_t = PLATE_T);
        }

        // Mock device port face block: near face at depth d = bay behind the flange front.
        translate([-JIG_W / 2, -JIG_H / 2, PLATE_T - d_face_far])
            cube([JIG_W, JIG_H, FACE_T]);

        // Side rail connecting the two ends, running the full depth range d=[0, bay+FACE_T].
        translate([JIG_W / 2, -RAIL_W / 2, PLATE_T - d_face_far])
            cube([RAIL_T, RAIL_W, d_face_far]);
    }

    // 5 mm scale, engraved into the rail's outward (+X) face; d=0 at the flange front.
    for (i = [0 : 1 : floor(d_face_far / TICK)]) {
        tall = (i % 2 == 0); // every other tick is taller, like a ruler's cm/mm marks.
        h    = tall ? 5 : 2.5;
        d    = i * TICK;
        translate([JIG_W / 2 + RAIL_T - 0.6 + MCC_EPS, -h / 2, PLATE_T - d - 0.4])
            cube([0.6 + MCC_EPS, h, 0.8]);
    }
}

// vim: expandtab tabstop=4 shiftwidth=4 softtabstop=4 nowrap
