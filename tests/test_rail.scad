//////////////////////////////////////////////////////////////////////
// tests/test_rail.scad
//   Tier-2 headless smoke test (architecture.md §9). Instantiates every public module/function in
//   lib/mcc/rail.scad at default (MCC_RAIL_LEN) and short (coupon-scale, len=60) parameters, and
//   exercises the two rev-9 blocking asserts issue #25 introduced:
//     - T1-38 (lib/mcc/rail.scad mcc_rail_female_cut()): >= MCC_FLOOR_T of residual floor over the
//       groove (layout-patch-wall.md §17.2 R1).
//     - D16 (lib/mcc/mounts.scad mcc_assert_floor_keepout_no_overlap()): no two
//       mcc_floor_keepout() rows overlap (no exemptions since D44), run against a real device record.
//     - T1-62 (D44): >= MCC_RAIL_MATE_CLR normal to the flanks and at the roof.
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
assert(_sill[1] == MCC_RAIL_ROOT_W + 2 * MCC_RAIL_SILL_SIDE_W, str("mcc_rail_sill_size width=", _sill[1]));
// D30: the sill's side walls beside the groove root must be real walls, not knife edges.
assert(MCC_RAIL_SILL_SIDE_W >= MCC_WALL - MCC_EPS, str("D30: MCC_RAIL_SILL_SIDE_W=", MCC_RAIL_SILL_SIDE_W, " below MCC_WALL"));
assert(_sill[2] == MCC_RAIL_SILL_H, str("mcc_rail_sill_size height=", _sill[2]));

// --- T1-38: MCC_RAIL_SILL_H - MCC_RAIL_DEPTH >= MCC_FLOOR_T, checked directly (not just via the
// module assert, which only fires at render) so a constants.scad regression fails this smoke test
// with a clear message before it ever reaches a full case render. ----------------------------
assert(MCC_RAIL_SILL_H - MCC_RAIL_DEPTH >= MCC_FLOOR_T,
    str("T1-38: MCC_RAIL_SILL_H(", MCC_RAIL_SILL_H, ") - MCC_RAIL_DEPTH(", MCC_RAIL_DEPTH,
        ") must be >= MCC_FLOOR_T(", MCC_FLOOR_T, ")"));

// --- Latch (issue #46, D34): snap-fit rules, checked from the constants so a regression fails here
// before any render. ------------------------------------------------------------------------------
assert(MCC_RAIL_LATCH_ENABLED, "D34: the rail latch is expected to be enabled");
assert(MCC_RAIL_LATCH_ARM_L / MCC_RAIL_LATCH_ARM_T >= 8, "D34: latch arm L/t below 8");
assert(1.5 * MCC_RAIL_LATCH_ARM_T * MCC_RAIL_LATCH_ENGAGE / pow(MCC_RAIL_LATCH_ARM_L, 2) <= MCC_SNAP_STRAIN_MAX,
    "D34: latch tip strain above MCC_SNAP_STRAIN_MAX");
assert(MCC_RAIL_LATCH_SLOT > MCC_RAIL_LATCH_ENGAGE, "D34: latch slot narrower than the nub's deflection");
assert(MCC_RAIL_LATCH_RAMP_OUT >= MCC_RAIL_LATCH_RAMP_IN, "D34: exit ramp should be at least as steep as entry");
assert(MCC_RAIL_END_STOP_L == 0 && MCC_RAIL_END_STOP_H == 0, "D34: the male end-stop flange is retired");

// --- T1-62 / D44: >= MCC_RAIL_MATE_CLR on every non-bearing face, and the user's width range ------
assert(MCC_RAIL_CLR_HORIZ * sin(MCC_RAIL_FLANK_ANGLE) >= MCC_RAIL_MATE_CLR - MCC_EPS,
    str("T1-62: rail flank clearance ", MCC_RAIL_CLR_HORIZ * sin(MCC_RAIL_FLANK_ANGLE), " below ", MCC_RAIL_MATE_CLR));
assert(MCC_RAIL_DEPTH - MCC_RAIL_MALE_H >= MCC_RAIL_MATE_CLR - MCC_EPS,
    str("T1-62: rail roof clearance ", MCC_RAIL_DEPTH - MCC_RAIL_MALE_H, " below ", MCC_RAIL_MATE_CLR));
assert(MCC_RAIL_MATE_CLR >= 0.5 - MCC_EPS, "D44: the user's minimum rail clearance is 0.5 mm");
assert(MCC_RAIL_ROOT_W >= 60 && MCC_RAIL_ROOT_W <= 70,
    str("D44: MCC_RAIL_ROOT_W=", MCC_RAIL_ROOT_W, " outside the user's 60-70 mm range"));

// --- mcc_rail_male() / mcc_rail_female_cut() -- default (production MCC_RAIL_LEN) --------------
translate([0, 0, 0]) mcc_rail_male();
translate([0, -60, 0]) mcc_rail_male(plate_t = 6); // with the arm's leg through a 6 mm plate
translate([0, 60, 0])
    difference() {
        cuboid([MCC_RAIL_LEN, MCC_RAIL_ROOT_W + 20, MCC_RAIL_SILL_H], anchor = BOTTOM);
        mcc_rail_female_cut(open_ext = 20);
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
// D34: the groove runs from its closed end at -MCC_RAIL_LEN/2 out through the +X wall.
_L = struct_val(mcc_case_layout(DEV, VARIANT), "L");
assert(abs(_rail_rows[0][0] - (_L / 2 - MCC_RAIL_LEN / 2) / 2) < 1e-6 && _rail_rows[0][1] == MCC_RAIL_Y,
    str("mount_rail row centre=", [_rail_rows[0][0], _rail_rows[0][1]]));
assert(_rail_rows[0][3] == [_L / 2 + MCC_RAIL_LEN / 2, MCC_RAIL_ROOT_W],
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
// 2. D16, violated by moving the rail onto the side-bolt support web (scratch edit constants.scad
//    MCC_RAIL_Y = -40):
//    -> "mcc: floor features \"mount_rail\" and \"side_bolt_web\" overlap ... (D16)"
//
// 3. T1-63 (D44), the opt-in case insert together with the (default-on) rail:
//    mcc_cradle(DEV, [["fan", false], ["splitter", false], ["tripod_insert", true]]);
//    -> "mcc: T1-63 cfg[\"tripod_insert\"]=true needs [\"rail\", false] ..."
// -----------------------------------------------------------------------------------------

// vim: expandtab tabstop=4 shiftwidth=4 softtabstop=4 nowrap
