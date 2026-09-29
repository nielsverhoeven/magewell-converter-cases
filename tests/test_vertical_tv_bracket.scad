//////////////////////////////////////////////////////////////////////
// tests/test_vertical_tv_bracket.scad
//   Tier-2 headless smoke test (architecture.md §9). Issue #56, plan D rev 2 §6 step 4, same
//   PLAN-ASSUMPTION-5-class precedent tests/test_arch_tv_bracket.scad set: this file `use`s (never
//   `include`s) the models/** file under test. `use` pulls in modules/functions only -- this file's
//   own top-level `part` dispatch and top-level `mcc_vert_tv_assert(G)` call in
//   vertical-tv-bracket.scad do NOT re-run here; this test never assigns `part`, and exercises the
//   asserts itself, explicitly, for a few tv_side_clear values via mcc_vert_tv_geom()/
//   mcc_vert_tv_assert() (both public, `mcc_vert_tv_` prefixed).
// Run:
//   openscad --backend=Manifold -o out.csg tests/test_vertical_tv_bracket.scad
//////////////////////////////////////////////////////////////////////

$fa = 1; $fs = 0.4;

include <mcc/mcc.scad>
use <../models/brackets/vertical-tv-bracket.scad>

// Three tv_side_clear values (mm): just above B2/T1-71's own computed minimum (case_x_hi=242.5 +
// TV_SIDE_MARGIN=10 = 252.5 at the default w_lift_rail/reach -- see the failing case below for the
// boundary itself), the file's own placeholder default (500, user-confirmed non-binding), and a
// deliberately huge value (a "the TV/room is enormous" case -- T1-71 stays satisfied by construction
// since it is a one-sided upper-bound check).
_TV_SIDE_CLEAR_VALUES = [252.5, 500, 5000];

for (i = [0:len(_TV_SIDE_CLEAR_VALUES) - 1]) {
    v = _TV_SIDE_CLEAR_VALUES[i];
    g = mcc_vert_tv_geom(tv_side_clear = v);
    mcc_vert_tv_assert(g);
    translate([i * 500, 0, 0]) mcc_vert_tv_arm(g);
    translate([i * 500, 300, 0]) mcc_vert_tv_centre(g);
}

// The spacer's own dimensions don't vary with tv_side_clear -- exercised once, at the default geom
// (fit-check FX3: mcc_vert_tv_spacer(g) now draws from g's own spacer_t/spacer_d fields).
translate([1500, 600, 0]) mcc_vert_tv_spacer(mcc_vert_tv_geom());

echo("mcc test_vertical_tv_bracket: OK");

// -----------------------------------------------------------------------------------------
// Manual check (architecture.md §9 / tests/test_arch_tv_bracket.scad's own precedent): OpenSCAD has
// no "expect this render to fail" mechanism, so this negative case is documented here, not run. To
// verify by hand, append the indicated call to a scratch copy of this file and confirm the render
// FAILS (non-zero exit) with an ERROR containing the quoted text.
//
// T1-71 (B2, "case clears the TV's side edge"), just below the computed minimum
// (case_x_hi + TV_SIDE_MARGIN = 252.5 at the default w_lift_rail):
//    mcc_vert_tv_assert(mcc_vert_tv_geom(tv_side_clear = 252));
//    -> "mcc: vertical-tv-bracket T1-71 case outboard edge+margin=252.5 exceeds tv_side_clear=252"
// -----------------------------------------------------------------------------------------

// vim: expandtab tabstop=4 shiftwidth=4 softtabstop=4 nowrap
