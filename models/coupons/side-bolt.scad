//////////////////////////////////////////////////////////////////////
// models/coupons/side-bolt.scad
//   Tier-4 physical coupon (architecture.md §9). A 30 mm wide wall slab of thickness MCC_WALL,
//   standing on a small base, carrying one captive side-bolt boss (D-09,
//   .claude/knowledge/layout-patch-wall.md §7.1) in the correct print orientation -- lug on the
//   outside, boss axis horizontal, wall vertical, matching how the far wall prints in the real
//   case -- so the real 1/4"-20 slotted screw, DIN 6799 E-clip, and EPDM pad can be tried before
//   any full case is printed.
//
// Render:
//   openscad --backend=Manifold -o out/side-bolt.stl models/coupons/side-bolt.scad
//   openscad --backend=Manifold -D proud=0 -o out/side-bolt-flush.stl models/coupons/side-bolt.scad
//////////////////////////////////////////////////////////////////////

$fa = 1; $fs = 0.4;

include <mcc/mcc.scad>

// scripts/build.py always passes -D part="<file-stem>" (the export part name -- see its
// discover_coupons()); "part" is reserved for that and must never be reused as this coupon's own
// parameter. This default is harmless, matching models/coupons/neutrik-tile.scad's own convention.
part = "side-bolt";

// -D proud=0 renders the flush variant (no lug). gap_far_eff below auto-widens the duct gap to
// compensate whenever `proud` is turned down, so any override here still renders a valid part
// instead of tripping mcc_captive_side_bolt_cut()'s "pocket fits the boss" assert.
proud = MCC_SIDE_BOLT_PROUD;

WALL_W    = 30; // X, mm. Brief's explicit instruction: "30 x 30 mm wall slab".
WALL_H    = 36; // Z, mm. Same instruction (rounded up from 30 so the od=20 boss, plus its root
                 // fillet, clears the slab top/bottom edges at mid-height with margin).
BASE_T    = 4;  // base pad thickness, mm. assumed -- generous bed-adhesion footing for a coupon
                 // this small.
BASE_LIP  = 4;  // how far the base pad extends beyond the wall's outer face (-Y), mm. assumed.
BASE_BACK = 10; // how far the base pad extends behind the wall's inner face (+Y), mm. assumed.

// Auto-widen gap_far so the axial stack (head_rec_h + web_t + pocket_h) always fits within
// proud + MCC_WALL + gap_far - MCC_SIDE_BOLT_PAD_T, no matter what `proud` is overridden to --
// this is exactly the same "widen the duct instead of the lug" trade R18 describes, applied
// automatically so -D proud=<anything> renders instead of failing mcc_captive_side_bolt_cut()'s
// own assert.
_stack    = MCC_SIDE_BOLT_HEAD_REC_H + MCC_SIDE_BOLT_WEB_T + MCC_SIDE_BOLT_POCKET_H;
gap_far   = max(MCC_GAP_FAR, _stack - proud - MCC_WALL + MCC_SIDE_BOLT_PAD_T);
total_len = proud + MCC_WALL + gap_far - MCC_SIDE_BOLT_PAD_T;
boss_z    = WALL_H / 2;

echo(str(
    "side-bolt: proud=", proud, " gap_far=", gap_far, " total_len=", total_len,
    " boss_od=", MCC_SIDE_BOLT_BOSS_OD, " head_d=", MCC_SIDE_BOLT_HEAD_D,
    " head_rec_d=", MCC_SIDE_BOLT_HEAD_REC_D, " head_rec_h=", MCC_SIDE_BOLT_HEAD_REC_H,
    " shank_d=", MCC_TRIPOD_CLR_D, " clip_pocket_d=", MCC_SIDE_BOLT_POCKET_D,
    " engage=", MCC_SIDE_BOLT_ENGAGE, " screw_len=", MCC_SIDE_BOLT_SCREW_LEN
));

module _side_bolt_base() {
    translate([-WALL_W / 2, -proud - BASE_LIP, -BASE_T])
        cube([WALL_W, proud + BASE_LIP + BASE_BACK, BASE_T]);
}

module _side_bolt_wall() {
    translate([-WALL_W / 2, 0, 0])
        cube([WALL_W, MCC_WALL, WALL_H]);
}

// Boss local frame: Z=0 at the lug's outer (free) face, +Z into the case (layout-patch-wall.md
// §7.1). rotate([-90,0,0]) maps local +Z onto global +Y ("into the case" = further from the
// bed-adhered wall face, away from the lug); translate([0,-proud,boss_z]) then lands local
// Z=proud (the wall-plane point) at the wall's own outer face, global Y=0, at the wall's
// mid-height -- so the tip (local Z=0) sits `proud` mm out in -Y, "on the outside".
module _side_bolt_feature() {
    translate([0, -proud, boss_z])
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
