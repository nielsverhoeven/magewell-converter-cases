//////////////////////////////////////////////////////////////////////
// models/coupons/rail-lock.scad
//   Tier-4 physical coupon (architecture.md §9). A short groove tile (case-floor stand-in,
//   mcc_rail_female_cut()) plus a matching short rail (bracket-plate stand-in, mcc_rail_male()), at
//   MCC_RAIL_LEN's real cross-section but a shorter LEN=60 mm working length -- a fit/lock test, not a
//   full-length print (docs/plans/2026-09-09-mount-rail-and-brackets.md §2). It checks the D44
//   clearances (0.5 mm normal to the flanks and at the roof -- MCC_RAIL_MATE_CLR is a user decision,
//   confirmed here, not calibrated), the groove-roof bridge (architecture.md R40: the groove half
//   prints exactly like the case floor), the 45-degree lead-in, and the gravity lock (D48): the rigid
//   bump on the rail's -Y flank rides over the groove flank inside the dovetail's own play, clicks into
//   its pocket, and -- with the rail plate vertical and the groove half hanging on the upper flank --
//   cannot be pulled out along the rail until the groove half is lifted about 1 mm (M15).
//
//   The groove half stands directly on the bed, groove mouth down and OPEN, like the case floor; the
//   rail half stands on its own plate. Two thin snap-off strips beside the groove join them so the
//   coupon renders/checks as one connected shell (architecture.md §9 Tier 3). Snap the strips off
//   before testing.
//
//   e-ladder (M15): LOCK_E below is passed to BOTH halves. The exported part uses the production
//   MCC_RAIL_LOCK_ENGAGE; for the ladder, render extra copies with -D LOCK_E=0.5 / 0.6 / 0.8 (see
//   models/coupons/README.md "rail-lock").
//
// Render:
//   openscad --backend=Manifold -o out/rail-lock.stl models/coupons/rail-lock.scad
//////////////////////////////////////////////////////////////////////

$fa = 1; $fs = 0.4;

include <mcc/mcc.scad>

// scripts/build.py always passes -D part="(file-stem)" (the export part name -- see its
// discover_coupons()); "part" is reserved for that and must never be reused as this coupon's own
// parameter -- side-bolt.scad:26-29's documented convention.
part = "rail-lock";

LEN = 60; // working (dovetail) length under test, mm. Well under MCC_RAIL_LEN=150 -- brief's own
           // "short groove tile" instruction (docs/plans/2026-09-09-mount-rail-and-brackets.md §2).
LOCK_E = MCC_RAIL_LOCK_ENGAGE; // lock bump protrusion for THIS print, mm -- the e-ladder overrides it
                               // with -D; both halves always get the same value.
MARGIN = 6; // plinth/plate footprint margin beyond MCC_RAIL_ROOT_W, mm. assumed -- wall support
             // around the groove/rail cross-section, generous enough to print cleanly.
GAP = 20; // gap between the female half's own footprint and the male half's, mm. assumed --
           // handling/labelling clearance; the snap-off strips still connect them into one printed
           // shell for the CI mesh check (see the file header comment).
PLATE_T = MCC_FLOOR_T; // the rail half's own plate thickness, mm -- its "bracket plate" stand-in
                         // (mcc_rail_male()'s own local Z=0 sits at its TOP face).

footprint_d = MCC_RAIL_ROOT_W + 2 * MARGIN; // Y footprint shared by both halves' own solid stock.

x_female0 = 0;             // female groove's own [0, LEN] working length, local X; the plinth adds
                           // a MCC_WALL end-stop wall at -X (the groove's CLOSED end, D34) and the
                           // groove runs out open through the plinth's +X end, like the case.
x_male0   = LEN + GAP;     // male rail's own working-length footprint starts here, local X.
x_base0   = -MCC_WALL;     // the coupon's -X extent: the female's stop wall.
STRIP_W   = 2.0;           // snap-off joining strip width, mm. assumed -- thin enough to break by hand.
base_w    = x_male0 + LEN + MARGIN - x_base0;
base_d    = footprint_d;

// This coupon's own lock position, re-derived from ITS OWN (short) LEN, exactly as lib/mcc/rail.scad
// does: the bump's exit face sits MCC_RAIL_LOCK_END_OFFSET inside the rail's +X end.
_lock_exit_x_here = LEN / 2 - MCC_RAIL_LOCK_END_OFFSET;

echo(str(
    "rail-lock: len=", LEN, " sill_h=", MCC_RAIL_SILL_H, " depth=", MCC_RAIL_DEPTH,
    " mouth_w=", MCC_RAIL_MOUTH_W, " root_w=", MCC_RAIL_ROOT_W, " flank_angle=", MCC_RAIL_FLANK_ANGLE,
    " clr_horiz=", MCC_RAIL_CLR_HORIZ, " roof_clr=", MCC_RAIL_ROOF_CLR,
    " lock_e=", LOCK_E, " lock_exit_x=", _lock_exit_x_here,
    " lock_ramps_in_out_deg=", [MCC_RAIL_LOCK_RAMP_IN, MCC_RAIL_LOCK_RAMP_OUT],
    " flank_play=", 2 * MCC_RAIL_CLR_HORIZ, " leadin=", MCC_RAIL_LEADIN,
    " print_bbox=", [base_w, base_d, max(MCC_RAIL_SILL_H, PLATE_T + MCC_RAIL_MALE_H)]
));

// The rail half's own plate (the bracket-plate stand-in). The rail needs no cut in it (D50). Two
// snap-off strips join it to the groove half, 1 mm in from the coupon's outer long edges and clear of
// the groove's open +X end. (Flush with those edges they left a zero-volume sliver on the bed plane:
// in plan F's prototype, which has no latch nub, `check` saw 2 parts and no watertight mesh.)
module _rail_lock_base() {
    union() {
        translate([x_male0 - MARGIN, -base_d / 2, 0])
            cube([LEN + 2 * MARGIN, base_d, PLATE_T]);
        for (y0 = [-footprint_d / 2 + 1, footprint_d / 2 - 1 - STRIP_W])
            translate([LEN - MCC_EPS, y0, 0])
                cube([x_male0 - MARGIN - LEN + 2 * MCC_EPS, STRIP_W, PLATE_T]);
    }
}

// The male lands MCC_EPS INTO its plate (a genuine shared volume, not a coincident face -- trimesh's
// split(), the Tier-3 "one connected shell" check, would otherwise see two parts).
Z0 = PLATE_T - MCC_EPS;

// Female half: a plinth standing DIRECTLY on the bed with its groove mouth face down -- the case
// floor's own print pose, so the groove roof prints as the same ~66 mm bridge as on a real base (R40).
// mcc_rail_female_cut()'s local Z=0 (the case's exterior floor face) is the bed; the groove is closed
// at -X by a MCC_WALL stop wall and runs out open through the plinth's +X end, like the case (D34),
// with the case's 45-degree lead-in at that face (entry_x, D48).
module _rail_lock_female() {
    translate([x_female0, 0, 0])
        difference() {
            translate([-MCC_WALL, -footprint_d / 2, 0])
                cube([LEN + MCC_WALL, footprint_d, MCC_RAIL_SILL_H]);
            translate([LEN / 2, 0, 0])
                mcc_rail_female_cut(len = LEN, open_ext = 1, entry_x = LEN / 2, lock_e = LOCK_E);
        }
}

// Male half: mcc_rail_male()'s own local Z=0 (the plate top) lands MCC_EPS into its base
// plate's own top face (world Z=Z0) -- that plate stands in for the bracket's own plate,
// so no extra plate geometry is added here.
module _rail_lock_male() {
    translate([x_male0 + LEN / 2, 0, Z0])
        mcc_rail_male(len = LEN, lock_e = LOCK_E);
}

union() {
    _rail_lock_base();
    _rail_lock_female();
    _rail_lock_male();
}

// vim: expandtab tabstop=4 shiftwidth=4 softtabstop=4 nowrap
