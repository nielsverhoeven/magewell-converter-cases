//////////////////////////////////////////////////////////////////////
// tests/test_arch_tv_bracket.scad
//   Tier-2 headless smoke test (architecture.md §9). Issue #47, docs/plans/2026-09-27-
//   arch-tv-bracket.md §7.1, PLAN-ASSUMPTION-5 (RATIFIED as a precedent, §12.5#5): the FIRST test
//   that `use`s (never `include`s) a models/** file. `use` pulls in modules/functions only -- this
//   file's own top-level `part` dispatch and top-level `mcc_arch_tv_assert(G)`/`mcc_arch_tv_assert(
//   G_SANDWICH)` calls in arch-tv-bracket.scad do NOT re-run here; this test never assigns `part`,
//   and exercises the asserts itself, explicitly, for two TV_TOP_CLEAR values x both mount modes
//   via mcc_arch_tv_geom()/mcc_arch_tv_assert() (both public, `mcc_arch_tv_` prefixed per the
//   ruling's own conditions). Issue #56/DB12: every existing assert must hold under both modes --
//   verified here by rendering both, not by inspection.
// Run:
//   openscad --backend=Manifold -o out.csg tests/test_arch_tv_bracket.scad
//////////////////////////////////////////////////////////////////////

$fa = 1; $fs = 0.4;

include <mcc/mcc.scad>
use <../models/brackets/arch-tv-bracket.scad>

// TV_TOP_CLEAR values (mm): the validity floor (69.675, T1-48) and the placeholder.
_TV_TOP_CLEAR_VALUES = [69.7, 150];
_MOUNT_MODES = ["direct", "sandwich"];

for (i = [0:len(_TV_TOP_CLEAR_VALUES) - 1], j = [0:len(_MOUNT_MODES) - 1]) {
    v = _TV_TOP_CLEAR_VALUES[i];
    mode = _MOUNT_MODES[j];
    g = mcc_arch_tv_geom(tv_top_clear = v, mount_mode = mode);
    mcc_arch_tv_assert(g);
    translate([i * 500, j * 700, 0]) mcc_arch_tv_arm(g);
    translate([i * 500, j * 700 + 400, 0]) mcc_arch_tv_centre(g);
}

// The spacer's own dimensions don't vary with TV_TOP_CLEAR -- exercised once, in sandwich mode
// (fit-check FX2: mcc_arch_tv_spacer(g) now draws from g's own spacer_t/spacer_d fields).
translate([1500, 1400, 0]) mcc_arch_tv_spacer(mcc_arch_tv_geom(mount_mode = "sandwich"));

echo("mcc test_arch_tv_bracket: OK");

// -----------------------------------------------------------------------------------------
// Manual checks (architecture.md §9 / tests/test_rail.scad's own precedent): OpenSCAD has no
// "expect this render to fail" mechanism, so this negative case is documented here, not run.
// To verify by hand, append the indicated call to a scratch copy of this file and confirm the
// render FAILS (non-zero exit) with an ERROR containing the quoted text.
//
// 1. T1-48, just below the validity floor:
//    mcc_arch_tv_assert(mcc_arch_tv_geom(tv_top_clear = 69));
//    -> "mcc: arch-tv-bracket T1-48 TV too short above the screws: needs TV_TOP_CLEAR >= 69.675..."
// -----------------------------------------------------------------------------------------

// vim: expandtab tabstop=4 shiftwidth=4 softtabstop=4 nowrap
