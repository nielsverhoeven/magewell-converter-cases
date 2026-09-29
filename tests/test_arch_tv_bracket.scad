//////////////////////////////////////////////////////////////////////
// tests/test_arch_tv_bracket.scad
//   Tier-2 headless smoke test (architecture.md §9). Issue #47, docs/plans/2026-09-27-
//   arch-tv-bracket.md §7.1, PLAN-ASSUMPTION-5 (RATIFIED as a precedent, §12.5#5): the FIRST test
//   that `use`s (never `include`s) a models/** file. `use` pulls in modules/functions only -- this
//   file's own top-level `part` dispatch and top-level `mcc_arch_tv_assert(G)` call in
//   arch-tv-bracket.scad do NOT re-run here; this test never assigns `part`, and exercises the
//   asserts itself, explicitly, for three TV_TOP_CLEAR values via mcc_arch_tv_geom()/
//   mcc_arch_tv_assert() (both public, `mcc_arch_tv_` prefixed per the ruling's own conditions).
// Run:
//   openscad --backend=Manifold -o out.csg tests/test_arch_tv_bracket.scad
//////////////////////////////////////////////////////////////////////

$fa = 1; $fs = 0.4;

include <mcc/mcc.scad>
use <../models/brackets/arch-tv-bracket.scad>

// Three TV_TOP_CLEAR values (mm): the arch floor (69.7, just above the rise>=0 bound of ~69.675 at
// MCC_RAIL_Y=-23.5 -- T1-49, D44), the file's own placeholder default (150), and just under the user
// bound (184.9, TV_TOP_CLEAR_MAX=185 -- T1-50; the T1-55 extreme after D44).
_TV_TOP_CLEAR_VALUES = [69.7, 150, 184.9];

for (i = [0:len(_TV_TOP_CLEAR_VALUES) - 1]) {
    v = _TV_TOP_CLEAR_VALUES[i];
    g = mcc_arch_tv_geom(tv_top_clear = v);
    mcc_arch_tv_assert(g);
    translate([i * 500, 0, 0]) mcc_arch_tv_arm(g);
    translate([i * 500, 400, 0]) mcc_arch_tv_centre(g);
}

echo("mcc test_arch_tv_bracket: OK");

// -----------------------------------------------------------------------------------------
// Manual checks (architecture.md §9 / tests/test_rail.scad's own precedent): OpenSCAD has no
// "expect this render to fail" mechanism, so these two negative cases are documented here, not run.
// To verify by hand, append the indicated call to a scratch copy of this file and confirm the
// render FAILS (non-zero exit) with an ERROR containing the quoted text.
//
// 1. T1-49 (A3, "rise >= 0"), just below the arch floor:
//    mcc_arch_tv_assert(mcc_arch_tv_geom(tv_top_clear = 69));
//    -> "mcc: arch-tv-bracket T1-49 TV too short above the screws: needs TV_TOP_CLEAR >= 69.675..."
//
// 2. T1-50 (A4, "tv_top_clear < TV_TOP_CLEAR_MAX"), at the user's own upper bound:
//    mcc_arch_tv_assert(mcc_arch_tv_geom(tv_top_clear = 185));
//    -> "mcc: arch-tv-bracket T1-50 tv_top_clear=185 must be < TV_TOP_CLEAR_MAX=185"
// -----------------------------------------------------------------------------------------

// vim: expandtab tabstop=4 shiftwidth=4 softtabstop=4 nowrap
