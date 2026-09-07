//////////////////////////////////////////////////////////////////////
// models/coupons/insert-boss.scad
//   Tier-4 physical coupon (architecture.md §9). 6 bosses with bore diameters 3.8/3.9/4.0/4.1/
//   4.2/4.3 mm for M3 heat-set inserts in ASA, each labelled, to calibrate MCC_INSERT_M3's
//   "hole_d" (constants.scad) for this printer/material combination
//   (knowledge/components/fasteners-and-hardware.md:22-28).
//
// Render:
//   openscad --backend=Manifold -o out/insert-boss.stl models/coupons/insert-boss.scad
//////////////////////////////////////////////////////////////////////

$fa = 1; $fs = 0.4;

include <mcc/mcc.scad>

// brief's explicit instruction: "bore ⌀ 3.8/3.9/4.0/4.1/4.2/4.3" — brackets the 4.0 mm nominal
// (knowledge/components/fasteners-and-hardware.md:22) and the CNC Kitchen shrink-compensation
// range (fasteners-and-hardware.md:26-28, "adding ~0.2-0.3 mm to the CAD hole diameter").
BORE_DS = [3.8, 3.9, 4.0, 4.1, 4.2, 4.3];

BOSS_H  = 10; // mm. assumed — exceeds MCC_INSERT_M3's 5.7 mm length with margin.
BOSS_OD = 10; // mm. Fixed (not the default MCC_BOSS_MIN_RATIO*insert_od) so every boss in this
              // ladder keeps >= 2 mm wall even at the largest bore (assert in
              // lib/mcc/fasteners.scad's mcc_heat_set_boss()): (10 - 4.3) / 2 = 2.85 mm.
PITCH   = 16; // mm. assumed.
BASE_T  = 3.0;
MARGIN  = 8;

n      = len(BORE_DS);
base_w = n * PITCH + PITCH;
base_l = PITCH + 2 * MARGIN;

echo(str("insert-boss: bore diameters=", BORE_DS, " boss_od=", BOSS_OD, " boss_h=", BOSS_H));

difference() {
    translate([0, 0, -BASE_T])
        linear_extrude(height = BASE_T)
            square([base_w, base_l]);

    for (i = [0 : 1 : n - 1])
        translate([(i + 1) * PITCH, MARGIN - 2, -0.6])
            linear_extrude(height = 0.6 + MCC_EPS)
                text(str(BORE_DS[i]), size = 3.4, halign = "center", valign = "center", font = "Liberation Sans:style=Bold");
}

for (i = [0 : 1 : n - 1]) {
    d        = BORE_DS[i];
    insert_i = struct_set(MCC_INSERT_M3, "hole_d", d);
    translate([(i + 1) * PITCH, base_l - MARGIN, 0])
        mcc_heat_set_boss(insert = insert_i, h = BOSS_H, od = BOSS_OD);
}

// vim: expandtab tabstop=4 shiftwidth=4 softtabstop=4 nowrap
