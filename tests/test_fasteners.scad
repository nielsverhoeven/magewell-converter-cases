//////////////////////////////////////////////////////////////////////
// tests/test_fasteners.scad
//   Tier-2 headless smoke test (architecture.md §9). Instantiates the fastener modules in
//   lib/mcc/fasteners.scad at default, minimum(-ish), and maximum(-ish) parameters, including the
//   captive side bolt (D-09, FLUSH per D-13, .claude/knowledge/layout-patch-wall.md §7.1) and the
//   case's own 1/4"-20 tripod mounting insert (replaces the withdrawn mcc_tripod_boss(),
//   deviation D2, architecture.md §13). CSG export (-o out.csg) evaluates the full tree so
//   in-model asserts fire, without tessellating.
// Run:
//   openscad --backend=Manifold -o out.csg tests/test_fasteners.scad
//////////////////////////////////////////////////////////////////////

$fa = 1; $fs = 0.4;

include <mcc/mcc.scad>

// --- Heat-set insert boss/bore (M3), captive thumbscrew hole -- pre-existing coverage sanity ---
mcc_heat_set_boss(h = 8);
translate([20, 0, 0]) mcc_heat_set_bore();
translate([40, 0, 0]) mcc_captive_thumbscrew_hole(lid_t = 3.0);

// --- Captive side bolt (D-09) -- FLUSH default parameters (D-13) -------------------------------
// boss(od=20) + cut() at every constants.scad default: proud=0, wall_t=3, gap_far=16, pad_t=2, so
// total height = 0+3+16-2 = 17, exactly matching the axial stack (head_rec_h 6 + web_t 3 +
// pocket_h 8 = 17) -- the boundary case both the "pocket fits the boss" (T1-26, in cut()) and the
// flush-rule (T1-29, in boss()) asserts must accept with equality (19 == 19 once +pad_t is folded
// in). Nothing protrudes past Z=0 (the wall's outer face) -- this is the production default.
translate([0, 40, 0])
    difference() {
        mcc_captive_side_bolt_boss();
        mcc_captive_side_bolt_cut();
    }

// --- Legacy lug variant: proud=10, gap_far=6 (the pre-D-13 rev-2 defaults, now only reachable by -
// explicit override) -- total height = 10+3+6-2 = 17, the same equality as the flush case above,
// exercised here so mcc_captive_side_bolt_boss()/_cut() keep working at proud>0 (their module
// docstrings both promise this) even though production only ever renders the flush default.
// T1-29 (boss()) is proud-gated and skipped here by design -- it only applies to the flush case.
translate([60, 40, 0])
    difference() {
        mcc_captive_side_bolt_boss(proud = 10, gap_far = 6);
        mcc_captive_side_bolt_cut(proud = 10, gap_far = 6);
    }

// --- Widened gap_far at the flush default (proud=0) -- comfortable slack above the T1-29 boundary,
// and a non-default support_web_t/web_to_floor_h to exercise both new parameters explicitly ------
translate([120, 40, 0])
    difference() {
        mcc_captive_side_bolt_boss(gap_far = 20, support_web_t = 4, web_to_floor_h = 30);
        mcc_captive_side_bolt_cut(gap_far = 20);
    }

// mcc_side_bolt_keepout() is now a pure function returning a struct/list (D-13 -- the keep-out is
// no longer a plain disc), not a bare diameter -- exercised directly via struct_val().
_ko_default  = mcc_side_bolt_keepout();
_ko_override = mcc_side_bolt_keepout(od = 24, strip_w = 9);
echo(str("mcc test_fasteners: side_bolt_keepout default disc_d=", struct_val(_ko_default, "disc_d"),
    " strip_w=", struct_val(_ko_default, "strip_w"),
    " strip_to_floor=", struct_val(_ko_default, "strip_to_floor"),
    " | od=24,strip_w=9 override disc_d=", struct_val(_ko_override, "disc_d"),
    " strip_w=", struct_val(_ko_override, "strip_w")));

// mcc_side_bolt_keepout_2d() draws the disc-plus-strip in the wall plane (D-13) -- 2D geometry, so
// it is linear_extrude()d into a thin slab purely so this file's top-level implicit union stays
// all-3D for the CSG export (mixing 2D/3D siblings at the top level is not supported). Exercised at
// the real axis height so a syntax/argument regression, or a bad axis_z <= floor_z, still fails the
// render.
translate([180, 40, 0])
    linear_extrude(height = 1)
        mcc_side_bolt_keepout_2d(axis_z = MCC_SIDE_BOLT_AXIS_Z);

// mcc_side_bolt_envelope() is gated behind MCC_SHOW_GHOST (default false, so this renders nothing
// by default) -- instantiate it anyway so a syntax/argument regression still fails the render.
translate([220, 40, 0]) mcc_side_bolt_envelope();

// --- Case tripod-mount insert (floor -> tripod/cheeseplate), replaces mcc_tripod_boss() (D2) ----
translate([0, 80, 0]) mcc_case_tripod_insert_boss(h = 15);
translate([30, 80, 0]) mcc_case_tripod_insert_bore();
translate([60, 80, 0]) mcc_case_tripod_insert_boss(h = 20, od = 18); // explicit od override (>= 1.8*9.5=17.1)

echo("mcc test_fasteners: OK");

// -----------------------------------------------------------------------------------------
// Manual checks: OpenSCAD has no "expect this render to fail" mechanism, so these cannot be
// asserted automatically in a render that must otherwise succeed (architecture.md §9 Tier-1
// "every module asserts its own contract"). To verify a guard by hand, append the indicated line
// to a scratch copy of this file and confirm the render FAILS (non-zero exit) with an ERROR
// containing the quoted text.
//
// 1. Too-thin RETAINING web (the E-clip shoulder inside mcc_captive_side_bolt_cut(), distinct from
//    the new central SUPPORT web below):
//      mcc_captive_side_bolt_cut(web_t = 1.5);
//    -> "web_t=1.5 below the 2.0 mm minimum retaining-shoulder material"
//
// 2. T1-31 (printability): a larger boss without a correspondingly thicker support web. At the
//    default od=20 this can never fail ((od-support_web_t)/2 < od/2 = 10 for any support_web_t>0),
//    so the manual check has to grow `od` instead:
//      mcc_captive_side_bolt_boss(od = 25);
//    -> "T1-31 unsupported span=11 exceeds the 10.0 mm self-supporting limit"
//
// 3. T1-29 (flush rule): shrink gap_far below the boundary at the flush default (proud=0):
//      mcc_captive_side_bolt_boss(gap_far = 10);
//    -> "T1-29 flush rule: head_rec_h+web_t+pocket_h+pad_t=19 must be <= wall_t+gap_far=13"
// -----------------------------------------------------------------------------------------

// vim: expandtab tabstop=4 shiftwidth=4 softtabstop=4 nowrap
