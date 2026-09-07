//////////////////////////////////////////////////////////////////////
// tests/test_neutrik.scad
//   Tier-2 headless smoke test (architecture.md §9). Instantiates mcc_neutrik_d_cutout(),
//   mcc_neutrik_d_bosses(), and mcc_panel_plate() at default, minimum, and maximum parameters.
//   CSG export (-o out.csg) evaluates the full tree so in-model asserts fire, without
//   tessellating (architecture.md:353-355).
// Run:
//   openscad --backend=Manifold -o out.csg tests/test_neutrik.scad
//////////////////////////////////////////////////////////////////////

$fa = 1; $fs = 0.4;

include <mcc/mcc.scad>

// --- Default parameters -------------------------------------------------------------------
mcc_neutrik_d_cutout("NE8FDP-B");
mcc_neutrik_d_bosses("NE8FDP-B");
mcc_neutrik_d_flange_outline();

// --- Minimum-ish parameters: seat_t == panel_t (no rear pocket cut at all) -----------------
translate([40, 0, 0])
    mcc_neutrik_d_cutout("NAHDMI-W-B", mirror = true, seat_t = 1.0, panel_t = 1.0);
translate([40, 0, 0])
    mcc_neutrik_d_bosses("NAHDMI-W-B", mirror = true, boss_h = struct_val(MCC_INSERT_M3, "len") + 1); // boss_h == bore_depth exactly

// --- Maximum-ish parameters: etherCON at its full 4 mm panel-thickness rating --------------
translate([80, 0, 0])
    mcc_neutrik_d_cutout("NE8FDP-B", mirror = false, seat_t = 2.0, panel_t = 4.0);
translate([80, 0, 0])
    mcc_neutrik_d_bosses("NE8FDP-B", mirror = false, boss_h = 12);

// --- Panel plate: single slot and a 2-slot plate at the minimum D-series pitch -------------
translate([0, 60, 0])
    mcc_panel_plate([70, 45], slots = [[0, 0, "NE8FDP-B", false]]);
translate([100, 60, 0])
    mcc_panel_plate([120, 45], slots = [[-40, 0, "NE8FDP-B", false], [40, 0, "NAHDMI-W-B", false]]);

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

// vim: expandtab tabstop=4 shiftwidth=4 softtabstop=4 nowrap
