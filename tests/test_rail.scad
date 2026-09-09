//////////////////////////////////////////////////////////////////////
// tests/test_rail.scad
//   Tier-2 headless smoke test (architecture.md §9). Instantiates every public module/function in
//   lib/mcc/rail.scad at default (MCC_RAIL_LEN) and short (coupon-scale, len=60) parameters, and
//   exercises the two rev-9 blocking asserts issue #25 introduced:
//     - T1-38 (lib/mcc/rail.scad mcc_rail_female_cut()): >= MCC_FLOOR_T of residual floor over the
//       groove (layout-patch-wall.md §17.2 R1).
//     - D16 (lib/mcc/mounts.scad mcc_assert_floor_keepout_no_overlap()): no two
//       mcc_floor_keepout() rows overlap, except the concentric "case_tripod_insert"/
//       "fishtail_reserve" pair (D19) -- run against a real device record so the exemption is
//       actually proven, not merely asserted to exist.
//   CSG export (-o out.csg) evaluates the full tree so in-model asserts fire, without tessellating.
// Run:
//   openscad --backend=Manifold -o out.csg tests/test_rail.scad
//////////////////////////////////////////////////////////////////////

$fa = 1; $fs = 0.4;

include <mcc/mcc.scad>
include <mcc/devices/pro-convert-for-ndi-to-hdmi.scad>

// --- mcc_rail_sill_size() -- pure function, no geometry ----------------------------------------
_sill = mcc_rail_sill_size();
assert(_sill[0] == MCC_RAIL_LEN, str("mcc_rail_sill_size len=", _sill[0]));
assert(_sill[1] == MCC_RAIL_ROOT_W, str("mcc_rail_sill_size width=", _sill[1]));
assert(_sill[2] == MCC_RAIL_SILL_H, str("mcc_rail_sill_size height=", _sill[2]));

// --- T1-38: MCC_RAIL_SILL_H - MCC_RAIL_DEPTH >= MCC_FLOOR_T, checked directly (not just via the
// module assert, which only fires at render) so a constants.scad regression fails this smoke test
// with a clear message before it ever reaches a full case render. ----------------------------
assert(MCC_RAIL_SILL_H - MCC_RAIL_DEPTH >= MCC_FLOOR_T,
    str("T1-38: MCC_RAIL_SILL_H(", MCC_RAIL_SILL_H, ") - MCC_RAIL_DEPTH(", MCC_RAIL_DEPTH,
        ") must be >= MCC_FLOOR_T(", MCC_FLOOR_T, ")"));

// --- mcc_rail_male() / mcc_rail_female_cut() -- default (production MCC_RAIL_LEN) --------------
translate([0, 0, 0]) mcc_rail_male();
translate([0, 60, 0])
    difference() {
        cuboid([MCC_RAIL_LEN, MCC_RAIL_ROOT_W + 20, MCC_RAIL_SILL_H], anchor = BOTTOM);
        mcc_rail_female_cut();
    }

// --- mcc_rail_male() / mcc_rail_female_cut() -- short, coupon-scale len=60 (models/coupons/
// rail-latch.scad's own length) -- the latch must be re-derived from THIS len, not the fixed
// MCC_RAIL_LATCH_X (constants.scad, which is only valid at len=MCC_RAIL_LEN=150); this is exactly
// the regression the len=60 case here guards against. -------------------------------------------
translate([200, 0, 0]) mcc_rail_male(len = 60);
translate([200, 60, 0])
    difference() {
        cuboid([60, MCC_RAIL_ROOT_W + 20, MCC_RAIL_SILL_H], anchor = BOTTOM);
        mcc_rail_female_cut(len = 60);
    }

// --- D16 / D19 (lib/mcc/mounts.scad): pairwise floor-keepout non-overlap, against a real device
// record and its default variant config, with the mount-rail row now in the list. Emits no
// geometry (pure assert module) -- a bare module-call statement is enough to force evaluation.
DEV = MCC_DEV_PRO_CONVERT_FOR_NDI_TO_HDMI;
VARIANT = [
    ["fan",      false],
    ["splitter", false],
];
mcc_assert_floor_keepout_no_overlap(DEV, VARIANT);

// mcc_floor_keepout()'s own "mount_rail" row, sanity-checked directly (rev 9, D-15).
_ko = mcc_floor_keepout(DEV, VARIANT);
_rail_rows = [for (r = _ko) if (r[4] == "mount_rail") r];
assert(len(_rail_rows) == 1, str("expected exactly one \"mount_rail\" row, got ", len(_rail_rows)));
assert(_rail_rows[0][0] == 0 && _rail_rows[0][1] == MCC_RAIL_Y,
    str("mount_rail row centre=", [_rail_rows[0][0], _rail_rows[0][1]], " expected [0, ", MCC_RAIL_Y, "]"));
assert(_rail_rows[0][3] == [MCC_RAIL_LEN, MCC_RAIL_ROOT_W],
    str("mount_rail row size=", _rail_rows[0][3]));
// No "vesa_*" rows survive (D-15 -- VESA fully removed, not deprecated-but-optional).
_vesa_rows = [for (r = _ko) if (r[4] == "vesa_ne" || r[4] == "vesa_se" || r[4] == "vesa_nw" || r[4] == "vesa_sw") r];
assert(len(_vesa_rows) == 0, str("expected zero VESA rows, got ", len(_vesa_rows)));

// --- mcc_floor_features_add()/mcc_rail_features_cut() -- the shell.scad call-site pair, exercised
// directly (default cfg["rail"]=true) so the ADD/CUT split renders as one clean, watertight block.
translate([400, 0, 0])
    difference() {
        mcc_floor_features_add(DEV, VARIANT);
        mcc_rail_features_cut(DEV, VARIANT);
    }

// cfg["rail"]=false -- both must render (and add/cut) nothing, not error.
translate([400, 60, 0]) {
    mcc_floor_features_add(DEV, [["fan", false], ["splitter", false], ["rail", false]]);
    mcc_rail_features_cut(DEV, [["fan", false], ["splitter", false], ["rail", false]]);
}

echo("mcc test_rail: OK");

// -----------------------------------------------------------------------------------------
// Manual checks: OpenSCAD has no "expect this render to fail" mechanism, so these cannot be
// asserted automatically in a render that must otherwise succeed. To verify a guard by hand,
// append the indicated line to a scratch copy of this file and confirm the render FAILS
// (non-zero exit) with an ERROR containing the quoted text.
//
// 1. T1-38, violated directly by shrinking the constant (constants.scad would need a local
//    override, e.g. via -D, since MCC_RAIL_SILL_H is derived -- simplest is a scratch edit setting
//    MCC_RAIL_SILL_H = MCC_RAIL_DEPTH + 1.0 in constants.scad and re-running this file):
//    -> "T1-38: MCC_RAIL_SILL_H(5) - MCC_RAIL_DEPTH(4) must be >= MCC_FLOOR_T(3)"
//
// 2. D16, violated by moving the rail on top of the case's own 1/4"-20 insert keep-out (scratch
//    edit constants.scad MCC_RAIL_Y = 0):
//    -> "mcc: floor features \"case_tripod_insert\" and \"mount_rail\" overlap ... (D16)"
// -----------------------------------------------------------------------------------------

// vim: expandtab tabstop=4 shiftwidth=4 softtabstop=4 nowrap
