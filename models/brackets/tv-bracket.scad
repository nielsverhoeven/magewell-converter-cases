//////////////////////////////////////////////////////////////////////
// models/brackets/tv-bracket.scad
//   L4-equivalent assembly (architecture.md §3 rev 9, layout-patch-wall.md §17.2). A flat VESA
//   100x100/200x200 sandwich plate that sits between a TV's own back panel and its existing wall
//   or stand mount, carrying the male mount-rail dovetail (lib/mcc/rail.scad, issue #25/D-15) so
//   a case clicks on tool-less. Single part, no base/lid split, no device record, no variant
//   config -- structurally identical in shape to a coupon target, discovered by
//   scripts/build.py's discover_brackets() (mirrors discover_coupons() exactly), NOT by
//   discover_models()'s case.scad-shaped mechanism (docs/plans/2026-09-09-
//   mount-rail-and-brackets.md §3.2).
//
//   Frame (this file's own local frame, as authored):
//     - Plate: a PLATE_SIZE x PLATE_SIZE x MCC_BRACKET_PLATE_T slab, centred at the origin,
//       spanning local Z in [-MCC_BRACKET_PLATE_T, 0]. Local Z=0 is the plate's RAIL face; local
//       Z=-MCC_BRACKET_PLATE_T is the plate's OTHER face (opposite the rail).
//     - Rail: mcc_rail_male() is called RAW (no rotate) except for a rotate([0,0,180]) about the
//       plate's own centre -- see "Orientation" below for why -- sitting on top of the plate at
//       local Z=0, rising into +Z. Since mcc_rail_male()'s own local Z=0 is documented
//       (lib/mcc/rail.scad) as "the pedestal foot, meets the bracket plate", the plate's own top
//       face at Z=0 IS that mating face by construction -- no extra transform needed to align it.
//     - Ribs: on the OTHER face (local Z <= -MCC_BRACKET_PLATE_T), standing off further into -Z.
//
//   Orientation (issue #26's own acceptance criterion, plan §3.1 "Orientation requirement" --
//   not a hand-derived rotate() sign, verified below by rendering `part == "assembly"` and
//   inspecting the PNG):
//     - "The rail must face away from the VESA plate side that touches the TV." Trivially true by
//       this file's own frame definition above: the rail lives on local +Z (Z=0 upward); this
//       file designates the OPPOSITE face (local Z=-MCC_BRACKET_PLATE_T, where the ribs stand off)
//       as the TV-facing face. The two are, by definition, opposite faces of one flat plate.
//     - "The case's patch (cable) wall must hang facing down when the bracket is wall-mounted
//       normally (VESA square upright)." This file's own convention: local +Y is UP. With the
//       rail placed via rotate([0,0,180]) (derived below), the mated case's own +Y face (its
//       patch wall -- .claude/knowledge/architecture.md §5, the panel plate sits at
//       `y = W/2 - MCC_PANEL_BEZEL_T`, i.e. the case's OWN +Y is the patch-wall side) lands at a
//       large NEGATIVE local Y once mated -- i.e. DOWN under the "+Y is up" convention. Installer
//       guidance: mount with the plate's own +Y axis pointing up (the ordinary, unsurprising way
//       to hang a symmetric VESA square) -- .claude/skills/print-check/SKILL.md carries the
//       one-line version of this note.
//     - Derivation of the rotate([0,0,180]): lib/mcc/mounts.scad places the case's female groove
//       at `translate([0, MCC_RAIL_Y, 0]) mcc_rail_female_cut(...)` in the case's OWN world frame
//       (floor at world Z=0, case centred at X=Y=0) -- a pure translate, no rotation, so
//       female-local (X,Y) = case-world (X, Y-MCC_RAIL_Y) directly. rail.scad's own comments
//       establish male-local (X,Y) = female-local (X,Y) directly too (same dovetail cross-section
//       convention, latch always on the male/female's shared -Y flank) and
//       male-local_Z = female-local_Z + MCC_FLOOR_T (male's pedestal-top plane, where the taper
//       begins, is exactly where the case's own exterior floor face rests at full mate -- see
//       rail.scad's mcc_rail_male() doc comment). Composing: with NO extra rotate, mating the case
//       onto a RAW mcc_rail_male() call needs `translate([0, -MCC_RAIL_Y, MCC_FLOOR_T])` applied
//       to the case's own native-frame geometry -- and since MCC_RAIL_Y = -20.0 (negative), that
//       places the case's own +Y (patch wall) at a large POSITIVE local Y, i.e. UP under the
//       "+Y is up" convention -- the WRONG way. Rotating the rail by 180 deg about its own local Z
//       (a proper rotation: local (x,y)->(-x,-y), z unchanged -- not a mirror, so the dovetail's
//       chirality, and the mate, stay physically valid) and rotating the mated case by the SAME
//       180 deg about Z composes to `translate([0, MCC_RAIL_Y, MCC_FLOOR_T]) rotate([0,0,180])`
//       applied to the case's native-frame geometry -- which puts the patch wall at a large
//       NEGATIVE local Y instead, i.e. DOWN. That is the transform the "assembly" branch below
//       uses; render it and check the PNG before trusting this comment over the picture.
//     - Open point, not blocking: the VESA hole pattern is itself left-right/up-down symmetric, so
//       nothing in the hardware physically forces an installer to insert the plate with +Y up
//       rather than +Y down (a 180 deg in-plane re-insertion is indistinguishable to the TV/mount
//       screws) -- there is no keying feature here to prevent installing it upside-down and
//       ending up with the patch wall UP instead. Flagged for the user/architect; not fixed here
//       (would need an asymmetric feature, out of this ticket's scope).
//     - Open point, not blocking: the stiffening ribs stand off the TV-facing face by up to
//       MCC_RIB_HEIGHT_RATIO_MAX * MCC_WALL = 9 mm. This assumes the TV's own back panel has
//       clearance in that zone (common -- most flat-panel TVs are not flush behind their VESA
//       bosses -- but not verified for any specific TV model).
//
// Render:
//   openscad --backend=Manifold -o out/tv-bracket.stl models/brackets/tv-bracket.scad
//   openscad --backend=Manifold -D 'part="assembly"' -o out/tv-bracket-assembly.stl models/brackets/tv-bracket.scad
//////////////////////////////////////////////////////////////////////

$fa = 1; $fs = 0.4; // the ONLY place $fn-adjacent globals are set (openscad-authoring skill).

include <mcc/mcc.scad>
include <mcc/devices/pro-convert-for-ndi-to-hdmi.scad> // "assembly" preview only -- any one
    // device record is fine per the plan (§3.1); this one is the repo's own normative template.

// scripts/build.py always passes -D part="<file-stem>" (see discover_brackets()); "part" is
// reserved for that and must never be reused as this file's own parameter -- matches every coupon
// (models/coupons/side-bolt.scad's own convention) and models/<slug>/case.scad.
part = "tv-bracket";

// -----------------------------------------------------------------------------------------
// Plan-fixed geometry (docs/plans/2026-09-09-mount-rail-and-brackets.md §3.1). These are this
// ONE bracket's own authored dimensions, not cross-cutting library policy, so they stay as named
// locals here rather than in constants.scad -- same convention models/coupons/side-bolt.scad uses
// for its own WALL_W/BASE_T/BASE_LIP. MCC_BRACKET_PLATE_T, MCC_M8_CLR_D and
// MCC_RIB_HEIGHT_RATIO_MAX ARE cross-cutting (a future truss-bracket reuses the plate-shim
// thickness class and the rib rule) and live in lib/mcc/constants.scad instead.
// -----------------------------------------------------------------------------------------

PLATE_SIZE = 230; // mm, square. assumed -- fits the ticket's own <=244 mm bed cap (build.py's
                   // MAX_AXIS_MM) with margin; contains the VESA 200x200 pattern (±100 mm) with a
                   // 15 mm edge web on every side; single-plate print, well under 256 mm.

VESA100_PITCH = 100; // mm, hole-to-hole across the square. VESA MIS-D 100x100
                      // (https://en.wikipedia.org/wiki/VESA_mount).
VESA200_PITCH = 200; // mm, hole-to-hole across the square. VESA MIS-F 200x200 (same source).

// [x, y, d] per through-hole -- both patterns share the plate's own centre (standard VESA
// convention: 100x100 is concentric with 200x200).
VESA_HOLES = concat(
    [for (sx = [-1, 1], sy = [-1, 1])
        [sx * VESA100_PITCH / 2, sy * VESA100_PITCH / 2, MCC_M4_CLR_D]], // 4x M4, VESA MIS-D
    [for (sx = [-1, 1], sy = [-1, 1])
        [sx * VESA200_PITCH / 2, sy * VESA200_PITCH / 2, MCC_M8_CLR_D]]  // 4x M6/M8, VESA MIS-F
);

// Stiffening ribs (back/non-rail face): a "+" cross through the plate centre, each arm
// RIB_T = MCC_WALL thick (<= 0.6x the 6 mm plate -- fdm-rugged-enclosure-guidelines.md:67, same
// rib-thickness rule as the case shell), RIB_H tall (<= MCC_RIB_HEIGHT_RATIO_MAX x RIB_T --
// fdm-rugged-enclosure-guidelines.md:68, D22). Arms run along the two centrelines only (never off-
// axis), so they clear every VESA hole above by construction (every hole sits at |x| or |y| in
// {50, 100}, never at 0) without needing a per-hole relief cut.
RIB_T     = MCC_WALL;                             // = 3.0
RIB_H     = MCC_RIB_HEIGHT_RATIO_MAX * RIB_T;     // = 9.0 (the practical ceiling, not a margin)
RIB_ARM_L = 2 * (VESA200_PITCH / 2);              // = 200: full centreline span, 15 mm short of
                                                    // each edge -- the same edge web the VESA200
                                                    // holes themselves already keep (100 to 115).

// -----------------------------------------------------------------------------------------
// Tier-1 asserts (architecture.md §9) -- evaluated at include time, before any geometry is drawn.
// -----------------------------------------------------------------------------------------

assert(mcc_bbox_ok([PLATE_SIZE, PLATE_SIZE, MCC_BRACKET_PLATE_T + MCC_RAIL_SILL_H + RIB_H]),
    str("mcc: tv-bracket bbox exceeds the printable envelope: ",
        [PLATE_SIZE, PLATE_SIZE, MCC_BRACKET_PLATE_T + MCC_RAIL_SILL_H + RIB_H]));

assert(RIB_T <= 0.6 * MCC_BRACKET_PLATE_T,
    str("mcc: tv-bracket rib thickness ", RIB_T, " exceeds 0.6x the plate thickness ",
        MCC_BRACKET_PLATE_T, " (fdm-rugged-enclosure-guidelines.md:67)"));
assert(RIB_H <= MCC_RIB_HEIGHT_RATIO_MAX * RIB_T,
    str("mcc: tv-bracket rib height ", RIB_H, " exceeds ", MCC_RIB_HEIGHT_RATIO_MAX,
        "x the rib thickness ", RIB_T, " (fdm-rugged-enclosure-guidelines.md:68, D22)"));

// Rail footprint (working length + end-stop flange) must fit inside the plate with a real edge
// web on both ends -- generic over MCC_RAIL_LEN so a future change to that constant fails loudly
// here instead of silently printing a rail that overhangs the plate edge.
assert(MCC_RAIL_LEN / 2 + MCC_RAIL_END_STOP_L < PLATE_SIZE / 2,
    str("mcc: tv-bracket rail footprint (", MCC_RAIL_LEN / 2 + MCC_RAIL_END_STOP_L,
        " mm half-length) does not fit inside the ", PLATE_SIZE, " mm plate"));

// "No slot may cut the rail" (issue #26 verification instruction): every VESA hole's own disc
// must clear the rail's Y-band (+/- MCC_RAIL_ROOT_W/2, the widest point of the dovetail cross-
// section) regardless of its X position -- a stricter-than-necessary but always-correct check,
// since the rail's footprint is entirely within that Y-band at every X along its length.
for (h = VESA_HOLES)
    assert(abs(h[1]) - h[2] / 2 > MCC_RAIL_ROOT_W / 2 + MCC_EPS,
        str("mcc: tv-bracket VESA hole at ", h, " clips the rail's Y-band (+/-",
            MCC_RAIL_ROOT_W / 2, " mm)"));

// -----------------------------------------------------------------------------------------
// Geometry
// -----------------------------------------------------------------------------------------

// Module: _mcc_tv_bracket_ribs()
// Description:
//   Private. The "+" stiffening-rib cross, standing off the plate's TV-facing face (local
//   Z = -MCC_BRACKET_PLATE_T) into further -Z. Centred on the origin, arms along both centrelines.
module _mcc_tv_bracket_ribs() {
    translate([0, 0, -MCC_BRACKET_PLATE_T])
        union() {
            cuboid([RIB_ARM_L, RIB_T, RIB_H], anchor = TOP); // arm along local X
            cuboid([RIB_T, RIB_ARM_L, RIB_H], anchor = TOP); // arm along local Y
        }
}

// Module: mcc_tv_bracket_plate()
// Description:
//   The exported part: plate + VESA through-holes + stiffening ribs + the male mount rail. See
//   this file's own header comment for the frame convention.
module mcc_tv_bracket_plate() {
    difference() {
        union() {
            cuboid([PLATE_SIZE, PLATE_SIZE, MCC_BRACKET_PLATE_T], anchor = TOP);
            _mcc_tv_bracket_ribs();
            // Rail: rotate([0,0,180]) -- see this file's header comment "Derivation of the
            // rotate([0,0,180])" for why. mcc_rail_male()'s own local Z=0 (pedestal foot) already
            // sits exactly on this plate's own rail face (local Z=0) with no extra translate.
            rotate([0, 0, 180]) mcc_rail_male();
        }
        // Through-holes span the plate's own Z range [-MCC_BRACKET_PLATE_T, 0] with an MCC_EPS
        // overlap on both faces (non-manifold-avoidance, same pattern used throughout lib/mcc) --
        // anchored TOP at local Z=+MCC_EPS so the cylinder's top face pokes MCC_EPS above the
        // plate's own top (Z=0) and its bottom reaches MCC_EPS past the plate's own bottom
        // (Z=-MCC_BRACKET_PLATE_T), rather than the CENTER-anchor default, which would only cover
        // the plate's own mid third and miss both faces (the plate itself spans [-T, 0], not
        // [-T/2, T/2]).
        for (h = VESA_HOLES)
            translate([h[0], h[1], MCC_EPS])
                cyl(h = MCC_BRACKET_PLATE_T + 2 * MCC_EPS, d = h[2], $fn = 64, circum = true,
                    anchor = TOP);
    }
}

if (part == "tv-bracket") {
    mcc_tv_bracket_plate();

} else if (part == "assembly") {
    // Non-exported preview only (mirrors models/pro-convert-for-ndi-to-hdmi/case.scad:112-124's
    // own "assembly" branch) -- invisible to build.py by construction (discover_brackets() only
    // ever asks for parts=[the file's own stem], never "assembly"). Renders the plate + rail
    // solid, and a full ghost case mated onto the rail, so the orientation claims in this file's
    // header comment can be checked against the actual picture rather than trusted on the algebra
    // alone.
    dev = MCC_DEV_PRO_CONVERT_FOR_NDI_TO_HDMI;
    variant = [["fan", false], ["splitter", false]]; // "rail" defaults true; irrelevant to this
                                                        // preview either way (it only affects the
                                                        // ghost case's OWN floor groove, invisible
                                                        // from the outside).
    layout = mcc_case_layout(dev, variant);

    color("Silver") mcc_tv_bracket_plate();

    // Case mate transform -- see this file's header comment "Derivation of the rotate([0,0,180])"
    // for the full derivation. Applied to the case's own native-frame geometry (floor at its own
    // Z=0, centred in X/Y).
    translate([0, MCC_RAIL_Y, MCC_FLOOR_T]) rotate([0, 0, 180]) {
        color("SlateGray") mcc_shell_base(dev = dev, cfg = variant);
        color("LightSteelBlue", 0.6) mcc_shell_lid(dev = dev, cfg = variant);
        translate([struct_val(layout, "x_dev_c"), struct_val(layout, "y_dev_c"),
                   struct_val(layout, "z_dev_lo") + mcc_dev_size(dev)[2] / 2])
            mcc_ghost(dev, show = true); // force-shown in this preview regardless of
                                          // MCC_SHOW_GHOST -- the whole point here is to see it.
    }

} else {
    assert(false, str("mcc: unknown part \"", part, "\""));
}

// vim: expandtab tabstop=4 shiftwidth=4 softtabstop=4 nowrap
