//////////////////////////////////////////////////////////////////////
// models/coupons/rail-latch.scad
//   Tier-4 physical coupon (architecture.md §9). A short groove tile (case-floor stand-in,
//   mcc_rail_female_cut()) plus a matching short rail with latch (bracket-plate stand-in,
//   mcc_rail_male()), at MCC_RAIL_LEN's real cross-section but a shorter LEN=60 mm working length
//   -- a fit/retention test, not a full-length print (docs/plans/2026-09-09-mount-rail-and-
//   brackets.md §2). Verifies the dovetail slides freely, the latch clicks and holds, and
//   thumb-release disengages it cleanly; calibrates MCC_CLR_SLIDE for this printer/material
//   combination the same way tolerance-ladder.scad calibrates it for the other fit classes, plus
//   MCC_RAIL_LATCH_ENGAGE and the 30 N retention target (assumed, layout-patch-wall.md §1.1) with a
//   simple pull-test (luggage scale through a temporary loop).
//
//   Both halves share ONE base plate so the whole coupon renders/checks as a single connected
//   shell (architecture.md §9 Tier-3 "one connected shell" — same requirement every other coupon in
//   this directory already satisfies via its own shared base). Snap or saw the thin bridging plate
//   between the two halves apart after printing, before the pull test.
//
// Render:
//   openscad --backend=Manifold -o out/rail-latch.stl models/coupons/rail-latch.scad
//////////////////////////////////////////////////////////////////////

$fa = 1; $fs = 0.4;

include <mcc/mcc.scad>

// scripts/build.py always passes -D part="<file-stem>" (the export part name -- see its
// discover_coupons()); "part" is reserved for that and must never be reused as this coupon's own
// parameter -- side-bolt.scad:26-29's documented convention.
part = "rail-latch";

LEN = 60; // working (dovetail) length under test, mm. Well under MCC_RAIL_LEN=150 -- brief's own
           // "short groove tile" instruction (docs/plans/2026-09-09-mount-rail-and-brackets.md §2).
MARGIN = 6; // plinth/plate footprint margin beyond MCC_RAIL_ROOT_W, mm. assumed -- wall support
             // around the groove/rail cross-section, generous enough to print cleanly.
GAP = 20; // gap between the female half's own footprint and the male half's, mm. assumed --
           // handling/labelling clearance; the shared base plate below still connects them into one
           // printed shell for the CI mesh check (see the file header comment).
PLATE_T = MCC_FLOOR_T; // shared base-plate thickness, mm -- doubles as the male half's own
                         // "bracket plate" stand-in (mcc_rail_male()'s own local Z=0 sits at its TOP
                         // face), so MCC_FLOOR_T keeps it a representative real-world plate gauge.

footprint_d = MCC_RAIL_ROOT_W + 2 * MARGIN; // Y footprint shared by both halves' own solid stock.

x_female0 = 0;             // female plinth's own [0, LEN] footprint, local X.
x_male0   = LEN + GAP;     // male rail's own working-length footprint starts here, local X.
base_w    = x_male0 + LEN + MCC_RAIL_END_STOP_L + MARGIN; // + the male's own end-stop overhang.
base_d    = footprint_d;

// This coupon's own latch position, re-derived from ITS OWN (short) LEN -- NOT MCC_RAIL_LATCH_X,
// which is fixed to the production MCC_RAIL_LEN=150 and would be out of bounds here (same
// re-derivation lib/mcc/rail.scad's own modules perform internally, see their shared comment).
_latch_x_here = -LEN / 2 + MCC_RAIL_LATCH_LEAD_IN;

echo(str(
    "rail-latch: len=", LEN, " sill_h=", MCC_RAIL_SILL_H, " depth=", MCC_RAIL_DEPTH,
    " mouth_w=", MCC_RAIL_MOUTH_W, " root_w=", MCC_RAIL_ROOT_W, " flank_angle=", MCC_RAIL_FLANK_ANGLE,
    " clr_slide=", MCC_CLR_SLIDE, " latch_x=", _latch_x_here, " latch_engage=", MCC_RAIL_LATCH_ENGAGE,
    " latch_arm_lxtxw=", [MCC_RAIL_LATCH_ARM_L, MCC_RAIL_LATCH_ARM_T, MCC_RAIL_LATCH_W],
    " latch_root_fillet=", MCC_RAIL_LATCH_ROOT_FILLET,
    " end_stop_lxh=", [MCC_RAIL_END_STOP_L, MCC_RAIL_END_STOP_H],
    " retention_target_N=30 (assumed)",
    " print_bbox=", [base_w, base_d, PLATE_T + MCC_RAIL_SILL_H]
));

module _rail_latch_base() {
    translate([0, -base_d / 2, 0])
        cube([base_w, base_d, PLATE_T]);
}

// Both halves land MCC_EPS INTO the base plate (not flush at world Z=PLATE_T) so the union has a
// genuine shared volume with the base plate, not just a coincident face -- an exact coincident
// planar face between two independently-extruded solids is a known Manifold/STL-export degeneracy
// (same class of fix shell.scad's own tongue frame comment documents) that trimesh's split() (the
// Tier-3 "one connected shell" check, architecture.md §9) catches as two disconnected parts even
// though the render itself looks fine.
Z0 = PLATE_T - MCC_EPS;

// Female half: a plinth standing on the shared base, with mcc_rail_female_cut() sunk into its own
// top face -- exactly mcc_rail_female_cut()'s own "Z=0 is the case's exterior floor face" local
// frame convention (offset by the MCC_EPS overlap above), here landing at world Z=Z0 (the plinth's
// own top, resting on the coupon's base plate). MCC_FLOOR_T of plinth material remains above the
// groove, same as T1-38 requires in the real case floor.
module _rail_latch_female() {
    translate([x_female0, 0, Z0])
        difference() {
            translate([0, -footprint_d / 2, 0])
                cube([LEN, footprint_d, MCC_RAIL_SILL_H + MCC_EPS]);
            translate([LEN / 2, 0, MCC_EPS])
                mcc_rail_female_cut(len = LEN);
        }
}

// Male half: mcc_rail_male()'s own local Z=0 (pedestal base) lands MCC_EPS into the shared base
// plate's own top face (world Z=Z0) -- the base plate itself stands in for the bracket's own plate,
// so no extra plate geometry is added here.
module _rail_latch_male() {
    translate([x_male0 + LEN / 2, 0, Z0])
        mcc_rail_male(len = LEN);
}

union() {
    _rail_latch_base();
    _rail_latch_female();
    _rail_latch_male();
}

// vim: expandtab tabstop=4 shiftwidth=4 softtabstop=4 nowrap
