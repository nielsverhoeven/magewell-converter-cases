//////////////////////////////////////////////////////////////////////
// models/coupons/tolerance-ladder.scad
//   Tier-4 physical coupon (architecture.md §9). General round-peg/hole fit ladder, per-side
//   clearance 0.10-0.40 mm, labelled, to calibrate MCC_CLR_SLIDE / MCC_CLR_PRESS
//   (constants.scad) for this printer/material combination.
//
// Render:
//   openscad --backend=Manifold -o out/tolerance-ladder.stl models/coupons/tolerance-ladder.scad
//////////////////////////////////////////////////////////////////////

$fa = 1; $fs = 0.4;

include <mcc/mcc.scad>

// brief's explicit instruction: "pegs/holes ladder 0.10...0.40 mm", stepped at 0.05 mm — assumed
// step granularity (the brief gives only the endpoints). Clearance applied per side (hole
// diameter = peg diameter + 2*clearance), consistent with tg-ladder.scad's own convention.
CLEARANCES = [0.10, 0.15, 0.20, 0.25, 0.30, 0.35, 0.40];

PEG_D  = 6.0; // nominal peg diameter, mm. assumed — representative round-fit feature size.
PEG_H  = 8.0; // mm. assumed.
PITCH  = 20;  // spacing between successive clearance steps, mm. assumed.
OFFSET = 12;  // peg-to-hole offset within one step, mm. assumed.
BASE_T = 3.0; // matches MCC_WALL.
MARGIN = 10;

n      = len(CLEARANCES);
base_w = n * PITCH + PITCH;
base_l = PITCH + 2 * MARGIN;
row_y  = base_l - MARGIN;

echo(str("tolerance-ladder: clearances=", CLEARANCES, " peg_d=", PEG_D));

difference() {
    translate([0, 0, -BASE_T])
        linear_extrude(height = BASE_T)
            square([base_w, base_l]);

    for (i = [0 : 1 : n - 1])
        translate([(i + 1) * PITCH, MARGIN - 4, -0.6])
            linear_extrude(height = 0.6 + MCC_EPS)
                text(str(CLEARANCES[i]), size = 3.2, halign = "center", valign = "center", font = "Liberation Sans:style=Bold");

    for (i = [0 : 1 : n - 1]) {
        clr = CLEARANCES[i];
        translate([(i + 1) * PITCH, row_y, PEG_H / 2])
            cyl(h = PEG_H + MCC_EPS, d = PEG_D + 2 * clr, circum = true, $fn = 64);
    }
}

for (i = [0 : 1 : n - 1]) {
    translate([(i + 1) * PITCH + OFFSET, row_y, 0])
        cyl(h = PEG_H, d = PEG_D, circum = true, anchor = BOTTOM, $fn = 64);
}

// vim: expandtab tabstop=4 shiftwidth=4 softtabstop=4 nowrap
