//////////////////////////////////////////////////////////////////////
// models/coupons/tg-ladder.scad
//   Tier-4 physical coupon (architecture.md §9). A tongue-and-groove clearance ladder: 5
//   tongue/groove pairs at per-side clearances 0.15/0.20/0.25/0.30/0.35 mm, each labelled, to
//   calibrate MCC_CLR_TG (constants.scad) for this printer/material combination.
//
// Render:
//   openscad --backend=Manifold -o out/tg-ladder.stl models/coupons/tg-ladder.scad
//////////////////////////////////////////////////////////////////////

$fa = 1; $fs = 0.4;

include <mcc/mcc.scad>

// brief's explicit instruction: "clearances 0.15/0.20/0.25/0.30/0.35 mm". Applied per side
// (groove width = tongue width + 2*clearance), consistent with MCC_CLR_TG's own "per-side"
// definition in constants.scad.
CLEARANCES = [0.15, 0.20, 0.25, 0.30, 0.35];

T_W    = 3.0; // nominal tongue width, mm. assumed — representative T&G feature size for this ladder.
T_L    = 14;  // tongue/groove engagement length, mm. assumed.
T_H    = 4.0; // tongue/groove height, mm. assumed.
PITCH  = 16;  // spacing between a pair's tongue and its groove, mm. assumed.
CELL   = 46;  // spacing between successive clearance pairs, mm. assumed.
BASE_T = 3.0; // base plate thickness, mm. matches MCC_WALL.
MARGIN = 6;   // base plate edge margin, mm. assumed.

n      = len(CLEARANCES);
base_w = n * CELL;
base_l = T_L + 2 * MARGIN + 10; // + label strip

echo(str("tg-ladder: clearances=", CLEARANCES, " tongue_w=", T_W, " base=", [base_w, base_l]));

difference() {
    translate([0, 0, -BASE_T])
        linear_extrude(height = BASE_T)
            square([base_w, base_l]);

    for (i = [0 : 1 : n - 1])
        translate([i * CELL + CELL / 2, MARGIN, -0.6])
            linear_extrude(height = 0.6 + MCC_EPS)
                text(str(CLEARANCES[i]), size = 3.6, halign = "center", valign = "center", font = "Liberation Sans:style=Bold");
}

for (i = [0 : 1 : n - 1]) {
    clr = CLEARANCES[i];
    x0  = i * CELL + CELL / 2;

    // Tongue half.
    translate([x0 - PITCH / 2 - T_W / 2, base_l - MARGIN - T_L, 0])
        cube([T_W, T_L, T_H]);

    // Groove half: a block with a slot cut, groove width = tongue width + 2*clearance.
    difference() {
        translate([x0 + PITCH / 2 - (T_W + 10) / 2, base_l - MARGIN - T_L, 0])
            cube([T_W + 10, T_L, T_H]);
        translate([x0 + PITCH / 2 - (T_W + 2 * clr) / 2, base_l - MARGIN - T_L - MCC_EPS, -MCC_EPS])
            cube([T_W + 2 * clr, T_L + 2 * MCC_EPS, T_H + MCC_EPS]);
    }
}

// vim: expandtab tabstop=4 shiftwidth=4 softtabstop=4 nowrap
