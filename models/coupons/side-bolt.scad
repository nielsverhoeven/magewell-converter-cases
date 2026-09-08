//////////////////////////////////////////////////////////////////////
// models/coupons/side-bolt.scad
//   Tier-4 physical coupon (architecture.md §9). A wall slab of thickness MCC_WALL standing on a
//   base plate, carrying one captive side-bolt boss (D-09, FLUSH per D-13,
//   .claude/knowledge/layout-patch-wall.md §7.1) in the correct print orientation -- base plate
//   bed-contact, wall vertical, boss/support-web horizontal off the wall -- matching how the far
//   wall prints in the real case, so the real 1/4"-20 slotted screw, DIN 6799 E-clip, and EPDM pad
//   can be tried before any full case is printed.
//
//   Since D-13 the boss is flush by default: nothing protrudes past the wall's outer (bed-facing)
//   face, and mcc_captive_side_bolt_boss()'s central vertical support web carries the boss's
//   cantilevered weight down to THIS COUPON'S OWN BASE PLATE instead of a root fillet -- the base
//   plate stands in for the case's interior floor, and the boss axis sits at the real (unscaled)
//   height above it (MCC_SIDE_BOLT_AXIS_Z - MCC_FLOOR_T) so the web actually reaches down and
//   rests on the base, which is exactly the thing this coupon exists to verify prints clean.
//
// Render:
//   openscad --backend=Manifold -o out/side-bolt.stl models/coupons/side-bolt.scad
//   openscad --backend=Manifold -D proud=10 -o out/side-bolt-lug.stl models/coupons/side-bolt.scad
//////////////////////////////////////////////////////////////////////

$fa = 1; $fs = 0.4;

include <mcc/mcc.scad>

// scripts/build.py always passes -D part="<file-stem>" (the export part name -- see its
// discover_coupons()); "part" is reserved for that and must never be reused as this coupon's own
// parameter. This default is harmless, matching models/coupons/neutrik-tile.scad's own convention.
part = "side-bolt";

// Default renders the flush design (D-13): mcc_captive_side_bolt_boss()'s own default is
// MCC_SIDE_BOLT_PROUD, which is now DERIVED to 0.0 (constants.scad). -D proud=10 renders the
// pre-D-13 lug variant -- kept only so the module contract stays exercised at proud>0 (the old lug
// path fasteners.scad retains for tests, per its own module docstring), not as a production option.
proud = MCC_SIDE_BOLT_PROUD;

WALL_W   = 30; // X, mm. Brief's explicit instruction: "30 mm wide wall slab" -- unchanged by D-13.
BASE_T   = 4;  // base pad thickness, mm. assumed -- generous bed-adhesion footing for a coupon
                // this small.
BASE_LIP = 4;  // how far the base pad extends beyond the wall's outer face (-Y), beyond any
                // exposed proud tip, mm. assumed. At the flush default (proud=0) nothing is
                // exposed there -- this is pure margin, and only matters when `proud` is
                // overridden upward for the legacy lug variant.

// Auto-widen gap_far so the axial stack (head_rec_h + web_t + pocket_h) always fits within
// proud + MCC_WALL + gap_far - MCC_SIDE_BOLT_PAD_T, no matter what `proud` is overridden to -- the
// same "widen the duct instead of the lug" trade D-13 describes, applied automatically so
// -D proud=<anything> renders instead of failing mcc_captive_side_bolt_cut()'s own assert.
_stack    = MCC_SIDE_BOLT_HEAD_REC_H + MCC_SIDE_BOLT_WEB_T + MCC_SIDE_BOLT_POCKET_H;
gap_far   = max(MCC_GAP_FAR, _stack - proud - MCC_WALL + MCC_SIDE_BOLT_PAD_T);
total_len = proud + MCC_WALL + gap_far - MCC_SIDE_BOLT_PAD_T; // boss reach beyond the wall's outer
                                                                // face (global Y), mm.

// Bolt axis height above the base plate's top (bed-contact) surface, mm -- the doc's own figure,
// NOT scaled down: mcc_captive_side_bolt_boss()'s own `web_to_floor_h` default
// (MCC_SIDE_BOLT_AXIS_Z - MCC_FLOOR_T, layout-patch-wall.md §1/§7.1's connector centreline minus
// the interior floor). The support web must reach this same real distance in the coupon as it will
// in the case, or the coupon would not actually test the feature that could fail.
AXIS_H = MCC_SIDE_BOLT_AXIS_Z - MCC_FLOOR_T;

// WALL_H is the one free dimension here: sized to clear the boss (radius
// MCC_SIDE_BOLT_BOSS_OD/2) above the axis with a small margin, chosen so BASE_T + WALL_H stays
// comfortably inside the 60 mm design cap (this coupon is meant to sit on a corner of a build
// plate alongside others, not claim the whole bed).
WALL_H = AXIS_H + MCC_SIDE_BOLT_BOSS_OD / 2 + 5;
assert(BASE_T + WALL_H <= 60,
    str("mcc: side-bolt coupon print height ", BASE_T + WALL_H, " exceeds the 60 mm design cap"));

// Base plate must fully underlie the boss/web's reach into the wall (global Y, "into the case") so
// the support web is genuinely self-supporting (resting on the base plate) rather than
// cantilevered past its edge.
BASE_BACK = total_len + 2;

echo(str(
    "side-bolt: proud=", proud, " gap_far=", gap_far, " total_len=", total_len,
    " axis_h=", AXIS_H, " wall_h=", WALL_H, " print_h=", BASE_T + WALL_H,
    " boss_od=", MCC_SIDE_BOLT_BOSS_OD, " support_web_t=", MCC_SIDE_BOLT_SUPPORT_WEB_T,
    " head_d=", MCC_SIDE_BOLT_HEAD_D, " head_rec_d=", MCC_SIDE_BOLT_HEAD_REC_D,
    " head_rec_h=", MCC_SIDE_BOLT_HEAD_REC_H, " shank_d=", MCC_TRIPOD_CLR_D,
    " clip_pocket_d=", MCC_SIDE_BOLT_POCKET_D, " engage=", MCC_SIDE_BOLT_ENGAGE,
    " screw_len=", MCC_SIDE_BOLT_SCREW_LEN
));

module _side_bolt_base() {
    translate([-WALL_W / 2, -proud - BASE_LIP, -BASE_T])
        cube([WALL_W, proud + BASE_LIP + BASE_BACK, BASE_T]);
}

module _side_bolt_wall() {
    translate([-WALL_W / 2, 0, 0])
        cube([WALL_W, MCC_WALL, WALL_H]);
}

// Boss local frame: Z=0 at the boss's outer (free/tip) face, +Z into the case (layout-patch-wall.md
// §7.1). rotate([-90,0,0]) maps local +Z onto global +Y ("into the case") and local +Y (the
// support web's own "down toward the floor" direction) onto global -Z; translate([0,-proud,AXIS_H])
// then lands local Z=proud (the wall-plane point) at the wall's own outer face (global Y=0) and the
// boss axis (local Y=0) at global Z=AXIS_H -- so the support web, which reaches local
// Y=web_to_floor_h below the axis, lands exactly on the base plate's top surface (global Z=0),
// resting on it rather than floating.
module _side_bolt_feature() {
    translate([0, -proud, AXIS_H])
        rotate([-90, 0, 0])
            difference() {
                mcc_captive_side_bolt_boss(proud = proud, gap_far = gap_far);
                mcc_captive_side_bolt_cut(proud = proud, gap_far = gap_far);
            }
}

union() {
    _side_bolt_base();
    _side_bolt_wall();
    _side_bolt_feature();
}

// vim: expandtab tabstop=4 shiftwidth=4 softtabstop=4 nowrap
