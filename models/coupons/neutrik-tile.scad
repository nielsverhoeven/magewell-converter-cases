//////////////////////////////////////////////////////////////////////
// models/coupons/neutrik-tile.scad
//   Tier-4 physical coupon (architecture.md §9). A 40x45x3 mm tile with one Neutrik D-series
//   panel cutout (2 mm seat pocket) and its rear screw bosses, to verify a real connector fits
//   and screws down before any full case is printed.
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

TILE_SIZE = [40, 45]; // brief's explicit instruction: "40 x 45 x 3 mm tile".
TILE_T    = 3.0;      // brief's explicit instruction; matches MCC_WALL.
SEAT_T    = 2.0;      // brief's explicit instruction: "(2 mm seat pocket)"; matches MCC_PANEL_SEAT_T.
LABEL_SIZE = 3.2;      // engraved label text height, mm. assumed.

echo(str(
    "neutrik-tile: connector=\"", connector, "\" size=", TILE_SIZE, " t=", TILE_T, " seat_t=", SEAT_T,
    " cutout_d=", mcc_cutout_d(connector), " bay_depth=", mcc_bay_depth(connector)
));

// Tile spans Z=[0, TILE_T]; front (outward, flange) face at Z=TILE_T, matching
// lib/mcc/neutrik.scad's own convention. mcc_panel_cutout() cuts a 2 mm seat pocket from the
// rear since TILE_T (3) > SEAT_T (2).
difference() {
    linear_extrude(height = TILE_T)
        square(TILE_SIZE, center = true);

    mcc_panel_cutout(connector, seat_t = SEAT_T, panel_t = TILE_T);

    // Engraved (recessed) part-name label near one edge.
    translate([0, -TILE_SIZE[1] / 2 + 5, TILE_T - 0.6])
        linear_extrude(height = 0.6 + MCC_EPS)
            text(connector, size = LABEL_SIZE, halign = "center", valign = "center", font = "Liberation Sans:style=Bold");
}

// Rear screw bosses: local Z=0 of mcc_neutrik_d_bosses() is the rear pocket floor, which sits at
// global Z = TILE_T - SEAT_T here (see lib/mcc/panel.scad's mcc_panel_plate() for the same math).
// No panel.scad boss dispatcher exists (only a cutout dispatcher, architecture.md §5) — calling
// the neutrik.scad boss module directly here mirrors what mcc_panel_plate() itself does.
translate([0, 0, TILE_T - SEAT_T])
    mcc_neutrik_d_bosses(connector);

// vim: expandtab tabstop=4 shiftwidth=4 softtabstop=4 nowrap
