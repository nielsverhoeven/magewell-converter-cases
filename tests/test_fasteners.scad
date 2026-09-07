//////////////////////////////////////////////////////////////////////
// tests/test_fasteners.scad
//   Tier-2 headless smoke test (architecture.md §9). Instantiates the fastener modules in
//   lib/mcc/fasteners.scad at default, minimum(-ish), and maximum(-ish) parameters, including the
//   new captive side bolt (D-09, .claude/knowledge/layout-patch-wall.md §7.1) and the case's own
//   1/4"-20 tripod mounting insert (replaces the withdrawn mcc_tripod_boss(), deviation D2,
//   architecture.md §13). CSG export (-o out.csg) evaluates the full tree so in-model asserts
//   fire, without tessellating.
// Run:
//   openscad --backend=Manifold -o out.csg tests/test_fasteners.scad
//////////////////////////////////////////////////////////////////////

$fa = 1; $fs = 0.4;

include <mcc/mcc.scad>

// --- Heat-set insert boss/bore (M3), captive thumbscrew hole -- pre-existing coverage sanity ---
mcc_heat_set_boss(h = 8);
translate([20, 0, 0]) mcc_heat_set_bore();
translate([40, 0, 0]) mcc_captive_thumbscrew_hole(lid_t = 3.0);

// --- Captive side bolt (D-09) -- default parameters ---------------------------------------------
// boss(od=20) + cut() at every constants.scad default: proud=10, wall_t=3, gap_far=6, pad_t=2, so
// total height = 10+3+6-2 = 17, exactly matching the axial stack (head_rec_h 6 + web_t 3 +
// pocket_h 8 = 17) -- the boundary case the "pocket fits the boss" assert must accept with
// equality.
translate([0, 40, 0])
    difference() {
        mcc_captive_side_bolt_boss();
        mcc_captive_side_bolt_cut();
    }

// --- Flush variant: proud=0 (no lug), the 17 mm stack absorbed entirely by a widened gap_far ----
// instead. MCC_WALL + MCC_GAP_FAR - MCC_SIDE_BOLT_PAD_T normally provides only 3+6-2 = 7 mm, so
// proud=0 alone (7 mm total) would violate the "pocket fits the boss" assert; gap_far=16 restores
// the required 17 mm (3+16-2) without any lug. This is R18's "widen MCC_GAP_FAR instead of adding
// a lug" alternative, exercised here as a boundary case rather than adopted as the default.
translate([60, 40, 0])
    difference() {
        mcc_captive_side_bolt_boss(proud = 0, gap_far = 16);
        mcc_captive_side_bolt_cut(proud = 0, gap_far = 16);
    }

// --- Widened gap_far at the default (proud>0) lug -- total height comfortably exceeds the stack -
translate([120, 40, 0])
    difference() {
        mcc_captive_side_bolt_boss(gap_far = 12);
        mcc_captive_side_bolt_cut(gap_far = 12);
    }

// mcc_side_bolt_keepout() is a pure function (no geometry to instantiate) -- exercised directly.
echo(str("mcc test_fasteners: side_bolt_keepout default=", mcc_side_bolt_keepout(),
    " od=24 override=", mcc_side_bolt_keepout(od = 24)));

// mcc_side_bolt_envelope() is gated behind MCC_SHOW_GHOST (default false, so this renders nothing
// by default) -- instantiate it anyway so a syntax/argument regression still fails the render.
translate([180, 40, 0]) mcc_side_bolt_envelope();

// --- Case tripod-mount insert (floor -> tripod/cheeseplate), replaces mcc_tripod_boss() (D2) ----
translate([0, 80, 0]) mcc_case_tripod_insert_boss(h = 15);
translate([30, 80, 0]) mcc_case_tripod_insert_bore();
translate([60, 80, 0]) mcc_case_tripod_insert_boss(h = 20, od = 18); // explicit od override (>= 1.8*9.5=17.1)

echo("mcc test_fasteners: OK");

// -----------------------------------------------------------------------------------------
// Manual check: a too-thin retaining web (architecture.md §9 Tier-1 "every module asserts its own
// contract"). OpenSCAD has no "expect this render to fail" mechanism, so this cannot be asserted
// automatically in a render that must otherwise succeed. To verify the guard by hand, append the
// following line to a scratch copy of this file and confirm the render FAILS (non-zero exit, an
// ERROR containing "web_t=1.5 below the 2.0 mm minimum retaining-shoulder material"):
//
//   mcc_captive_side_bolt_cut(web_t = 1.5);
// -----------------------------------------------------------------------------------------

// vim: expandtab tabstop=4 shiftwidth=4 softtabstop=4 nowrap
