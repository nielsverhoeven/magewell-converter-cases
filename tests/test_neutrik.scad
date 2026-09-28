//////////////////////////////////////////////////////////////////////
// tests/test_neutrik.scad
//   Tier-2 headless smoke test (architecture.md §9). Instantiates mcc_neutrik_d_cutout() and the
//   wall-integrated mcc_neutrik_d_wall_cut() / mcc_panel_wall_cut() (D36; round holes D40, plain
//   fixing bores D41) at default, minimum, and maximum parameters.
//   CSG export (-o out.csg) evaluates the full tree so in-model asserts fire, without
//   tessellating (architecture.md:353-355).
// Run:
//   openscad --backend=Manifold -o out.csg tests/test_neutrik.scad
//////////////////////////////////////////////////////////////////////

$fa = 1; $fs = 0.4;

include <mcc/mcc.scad>

// --- Default parameters -------------------------------------------------------------------
mcc_neutrik_d_cutout("NE8FDP-B");
mcc_neutrik_d_flange_outline();

// --- Minimum-ish parameters: seat_t == panel_t (no rear pocket cut at all) -----------------
translate([40, 0, 0])
    mcc_neutrik_d_cutout("NAHDMI-W-B", mirror = true, seat_t = 1.0, panel_t = 1.0);

// --- Maximum-ish parameters: etherCON at its full 4 mm panel-thickness rating --------------
translate([80, 0, 0])
    mcc_neutrik_d_cutout("NE8FDP-B", mirror = false, seat_t = 2.0, panel_t = 4.0);

// --- Wall-integrated connector cut (D36; round holes D40, plain bore D41): every part class at
// the production wall (seat 2 + lip 3) including the blank -- the T1-61 web assert fires inside
// the module on each -- and a thin wall for the BNC class (wall_t > seat_t is the only thickness
// assert since T1-42b retired; T1-61 does not depend on wall_t). Differenced from a block so the
// cuts render as real negatives. ------------------------------------------------------------
for (i = [0:1:3])
    translate([i * 40, 60, 0])
        difference() {
            translate([0, 0, -2.5]) cube([36, 40, 5], center = true);
            mcc_panel_wall_cut(["NE8FDP-B", "NAHDMI-W-B", "NAUSB-W-B", "DBA-BL-B"][i], wall_t = 5);
        }
translate([0, 110, 0])
    mcc_neutrik_d_wall_cut("NBB75DFGB", wall_t = 3.0, seat_t = 1.0);

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
