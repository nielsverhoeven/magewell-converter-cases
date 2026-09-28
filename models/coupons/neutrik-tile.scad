//////////////////////////////////////////////////////////////////////
// models/coupons/neutrik-tile.scad
//   Tier-4 physical coupon (architecture.md §9). A 40 x 45 mm section of the patch wall, printed
//   STANDING exactly like the case wall, with one Neutrik D-series connector cut straight into it
//   (D36: no panel plate — a perfectly round seat hole + body window (D40) and two plain ⌀2.5 mm
//   M3x0.5 tap-drill bores (D41, no printed thread) through the MCC_PANEL_SEAT_T + MCC_WALL of wall
//   behind the bezel recess), on a foot so it stands on the bed. Verifies a real connector passes
//   the round hole's printed arch and seats flush, and that the bores line up and are round, before
//   any full case is printed (architecture.md R39/M19).
//
// Render:
//   openscad --backend=Manifold -o out/neutrik-tile.stl models/coupons/neutrik-tile.scad
//   openscad --backend=Manifold -D 'connector="NE8FDP-B"' -o out/neutrik-tile-ne8fdp.stl models/coupons/neutrik-tile.scad
//////////////////////////////////////////////////////////////////////

$fa = 1; $fs = 0.4;

include <mcc/mcc.scad>

// scripts/build.py always passes -D part="<file-stem>" (the export part name — see its
// discover_coupons()); "part" is reserved for that and must never be reused as this coupon's own
// parameter. This default is harmless: it is only ever compared against nothing, so build.py's
// override is accepted silently.
part = "neutrik-tile";

// -D connector="..." switches the connector class, e.g. -D connector="NE8FDP-B" for the 24.0-class
// hole.
connector = "NAHDMI-W-B";

TILE_SIZE = [40, 45];                        // wall section W x H, mm (was the flat tile's footprint).
WALL_T    = MCC_T_PATCH - MCC_PANEL_BEZEL_T; // the case's wall behind the recess: seat + lip (5 mm).
FOOT      = [40, 20, 3];                     // foot behind the wall so the coupon stands, mm. assumed.
LABEL_SIZE = 3.2;                            // engraved label text height, mm. assumed.

echo(str(
    "neutrik-tile: connector=\"", connector, "\" wall=", TILE_SIZE, " t=", WALL_T,
    " cutout_d=", mcc_cutout_d(connector), " bay_depth=", mcc_bay_depth(connector)
));

// Frame: the seat (outer) face is the plane Y = 0, facing -Y; the wall runs to Y = WALL_T and the
// foot extends behind it (+Y). Connector centre at mid-height. mcc_panel_wall_cut()'s frame (wall
// seen from outside, local Y up, local Z outward) maps onto it with rotate([90, 0, 0]):
// local X -> world X, local Y -> world Z, local Z -> world -Y.
difference() {
    union() {
        translate([-TILE_SIZE[0] / 2, 0, 0])
            cube([TILE_SIZE[0], WALL_T, TILE_SIZE[1]]);
        translate([-FOOT[0] / 2, WALL_T - MCC_EPS, 0])
            cube([FOOT[0], FOOT[1], FOOT[2]]);
    }

    translate([0, 0, TILE_SIZE[1] / 2])
        rotate([90, 0, 0])
            mcc_panel_wall_cut(connector, wall_t = WALL_T);

    // Engraved (recessed) part-name label on the foot.
    translate([0, WALL_T + FOOT[1] / 2, FOOT[2] - 0.6])
        linear_extrude(height = 0.6 + MCC_EPS)
            text(connector, size = LABEL_SIZE, halign = "center", valign = "center", font = "Liberation Sans:style=Bold");
}

// vim: expandtab tabstop=4 shiftwidth=4 softtabstop=4 nowrap
