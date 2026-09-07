//////////////////////////////////////////////////////////////////////
// models/coupons/depth-mockup.scad
//   Tier-4 physical coupon (architecture.md §9). A flat-printing U-CHANNEL jig: a floor plate
//   carrying a real panel-cutout wall at one end and a mock "device port face" wall at the other,
//   `bay` mm apart (default mcc_bay_depth(connector)), with a ruler engraved into the floor's top
//   surface so the real patch cable can be tried and the needed depth read off directly. This is
//   the ONLY way to replace the `assumed` mating-plug lengths in constants.scad
//   (architecture.md §11 R2).
//
//   Redesigned from the original C-shaped two-plates-plus-single-rail jig, which had no orientation
//   that printed without supports (every axis-aligned face left the connecting rail spanning ~75 mm
//   of open air — see models/coupons/README.md history). This U-channel instead builds everything
//   as a floor (flat on the bed) plus walls/ribs that rise directly out of the floor, so every
//   surface is either the bed itself or a wall directly stacked on material already printed below
//   it — zero overhangs, zero supports, in a single fixed orientation. The one exception is the
//   panel wall's connector hole, which is bored horizontally (see the comment at that cutout) and
//   prints with a short self-supporting bridge at its very top — expected, not a defect.
//
//   Use: seat a real connector in the panel-wall cutout (screw it to the rear bosses if convenient
//   — not required for this measurement), plug the real patch cable into its rear, bend the cable
//   90 degrees toward the mock face wall, and read the ruler tick where the plug/cable seats
//   comfortably against the mock face. Write that reading into
//   MCC_PANEL_PARTS[connector].plug_len (constants.scad) in place of the current `assumed` value —
//   see models/coupons/README.md's "depth-mockup" measurement form for the full procedure.
//
// Render:
//   openscad --backend=Manifold -o out/depth-mockup.stl models/coupons/depth-mockup.scad
//   openscad --backend=Manifold -D 'connector="NE8FDP-B"' -o out/depth-mockup-rj45.stl models/coupons/depth-mockup.scad
//   openscad --backend=Manifold -D 'bay=60' -o out/depth-mockup-bay60.stl models/coupons/depth-mockup.scad
//////////////////////////////////////////////////////////////////////

$fa = 1; $fs = 0.4;

include <mcc/mcc.scad>

// scripts/build.py always passes -D part="<file-stem>" (the export part name — see its
// discover_coupons()); "part" is reserved for that and must never be reused as this coupon's own
// parameter. This default is harmless: it is only ever compared against nothing, so build.py's
// override is accepted silently.
part = "depth-mockup";

// -D connector="..." switches the connector; -D bay=<mm> overrides the default budgeted depth.
connector = "NAHDMI-W-B";
bay       = mcc_bay_depth(connector);

// -----------------------------------------------------------------------------------------
// Dimensions
// -----------------------------------------------------------------------------------------

JIG_SIZE = 45; // brief's explicit instruction: floor width (Y) AND wall height (Z) are both 45 mm.

L      = bay + 2 * MCC_WALL; // total floor length along X: panel wall + bay cavity + mock face wall.
X_FACE = MCC_WALL + bay;     // mock-face wall's near (inward, -X-facing) surface X position.

echo(str(
    "depth-mockup: connector=\"", connector, "\" bay=", bay, " total_length=", L
));

// architecture.md:341 "bbox <= MCC_BUILD - MCC_BED_MARGIN per exported part".
assert(mcc_bbox_ok([L, JIG_SIZE, MCC_FLOOR_T + JIG_SIZE]),
    str("mcc: depth-mockup ", L, "x", JIG_SIZE, "x", (MCC_FLOOR_T + JIG_SIZE),
        " exceeds the printable envelope"));
// The cavity must be at least as deep as the connector body itself or it will not physically fit.
assert(bay >= mcc_panel_depth(connector),
    str("mcc: depth-mockup bay=", bay, " is shorter than mcc_panel_depth(\"", connector, "\")=",
        mcc_panel_depth(connector), " — the connector body would not fit in the cavity"));

// -----------------------------------------------------------------------------------------
// Ruler / label engraving parameters
// -----------------------------------------------------------------------------------------

TICK        = 5;    // brief's explicit instruction: "tick every 5 mm".
TICK_DEPTH  = 0.6;   // brief's explicit instruction: "depth 0.6".
TICK_LEN    = 4;     // brief's explicit instruction: "length 4" (minor, every-5-mm tick).
TICK_LEN_10 = 6;     // major (every-10-mm) tick length, mm. assumed — "longer tick" per the brief,
                      // 1.5x the minor tick so it reads clearly against the 5 mm ticks either side.
TICK_W      = 0.6;   // tick line width along X, mm. assumed — the brief gives depth and length but
                      // not this dimension; reuses TICK_DEPTH as a plausible single-pass engraving
                      // width.
LABEL_SIZE  = 4;      // brief's explicit instruction: "text() size 4" for both the major-tick
                       // numbers and the connector/bay label.

RIB_W = 3; // brief's explicit instruction: "3 mm-wide ... stiffening ribs".
RIB_H = 8; // brief's explicit instruction: "8 mm-tall ... stiffening ribs".

RULER_Y = JIG_SIZE / 2 - RIB_W - 4; // ruler baseline, mm from the floor's Y center. assumed — set
                                      // inboard of the +Y rib (which sits flush with the floor edge)
                                      // so the ticks stay clear of the rib instead of being buried
                                      // under it, while still reading as "along" that long edge.

FACE_MARK = [20, 12, 1]; // [Y width, Z height, X depth], mm. brief's explicit instruction: "shallow
                          // engraved rectangle (e.g. 20 x 12 x 1 mm)" marking the device port face.

// -----------------------------------------------------------------------------------------
// Geometry
// -----------------------------------------------------------------------------------------

difference() {
    union() {
        // Floor plate: X=[0,L], Y=[-JIG_SIZE/2,JIG_SIZE/2], Z=[0,MCC_FLOOR_T]. Prints flat on the
        // bed — every other feature below stacks directly on top of this or of itself, so nothing
        // in the assembly overhangs.
        translate([0, -JIG_SIZE / 2, 0])
            cube([L, JIG_SIZE, MCC_FLOOR_T]);

        // Panel wall at X=[0,MCC_WALL], built in mcc_panel_cutout()'s own local frame (a plate
        // spanning local Z=[0,panel_t], flange/front face at local Z=panel_t, rear/pocket face at
        // local Z=0) and then reoriented into the jig's global frame: rotate([0,-90,0]) maps local
        // Z -> global -X, and the subsequent translate([MCC_WALL,...]) lands the flange/front face
        // at global X=0 (the jig's outward end, where a real connector is pushed in) and the rear
        // seat-pocket face at global X=MCC_WALL (facing into the bay cavity). The connector's hole
        // axis therefore ends up horizontal, along X, as required — fit itself is verified
        // separately by neutrik-tile.scad, and a horizontal round hole prints with a short
        // self-supporting bridge at its topmost point, which is expected here, not a defect.
        translate([MCC_WALL, 0, MCC_FLOOR_T + JIG_SIZE / 2])
            rotate([0, -90, 0])
                difference() {
                    linear_extrude(height = MCC_WALL)
                        square([JIG_SIZE, JIG_SIZE], center = true);
                    // seat_t=2.0 mm seat pocket on the inside (rear) face; MCC_HOLE_COMP is already
                    // baked into mcc_cutout_d() inside this call, no extra hole allowance needed.
                    mcc_panel_cutout(connector, seat_t = MCC_PANEL_SEAT_T, panel_t = MCC_WALL);
                }

        // Rear screw bosses at the pocket floor (local Z = panel_t - seat_t), same placement
        // convention neutrik-tile.scad uses — panel.scad has no boss dispatcher (architecture.md
        // §5), so calling the neutrik.scad boss module directly here mirrors that coupon. Kept
        // because it is trivial to add and gives the jig a physically realistic mounting, even
        // though this coupon does not require the connector to be screwed down.
        translate([MCC_WALL, 0, MCC_FLOOR_T + JIG_SIZE / 2])
            rotate([0, -90, 0])
                translate([0, 0, MCC_WALL - MCC_PANEL_SEAT_T])
                    mcc_neutrik_d_bosses(connector);

        // Mock device-face wall at X=[X_FACE, X_FACE+MCC_WALL].
        translate([X_FACE, -JIG_SIZE / 2, MCC_FLOOR_T])
            cube([MCC_WALL, JIG_SIZE, JIG_SIZE]);

        // Stiffening ribs along both long edges of the floor, spanning the bay cavity between the
        // two walls only. Self-supporting (sit directly on the floor, flush with each edge) and
        // tie the two walls together for extra rigidity on the thin floor span.
        translate([MCC_WALL, JIG_SIZE / 2 - RIB_W, MCC_FLOOR_T])
            cube([bay, RIB_W, RIB_H]);
        translate([MCC_WALL, -JIG_SIZE / 2, MCC_FLOOR_T])
            cube([bay, RIB_W, RIB_H]);
    }

    // Engraved rectangle on the mock face's inward (-X-facing) side, marking where the device's
    // port face sits so the patch cable's plug has something to be pushed against, vertically
    // aligned with the panel cutout's own hole axis (both centered at Z = MCC_FLOOR_T+JIG_SIZE/2).
    translate([X_FACE - MCC_EPS, -FACE_MARK[0] / 2, MCC_FLOOR_T + JIG_SIZE / 2 - FACE_MARK[1] / 2])
        cube([FACE_MARK[2] + MCC_EPS, FACE_MARK[0], FACE_MARK[1]]);

    // Ruler ticks, engraved into the floor's top surface, counting from the panel wall's inside
    // (rear/pocket) face at X=MCC_WALL — tick i=0 sits exactly there.
    for (i = [0 : 1 : floor(bay / TICK)]) {
        major = (i % 2 == 0); // every 10 mm (i even, since TICK=5) is a major, numbered tick.
        len   = major ? TICK_LEN_10 : TICK_LEN;
        x     = MCC_WALL + i * TICK;

        translate([x - TICK_W / 2, RULER_Y - len / 2, MCC_FLOOR_T - TICK_DEPTH])
            cube([TICK_W, len, TICK_DEPTH + MCC_EPS]);

        if (major)
            translate([x, RULER_Y - len / 2 - 3, MCC_FLOOR_T - TICK_DEPTH])
                linear_extrude(height = TICK_DEPTH + MCC_EPS)
                    text(str(i * TICK), size = LABEL_SIZE, halign = "center", valign = "top",
                        font = "Liberation Sans:style=Bold");
    }

    // Connector + bay label, centered on the floor within the bay cavity.
    translate([MCC_WALL + bay / 2, 0, MCC_FLOOR_T - TICK_DEPTH])
        linear_extrude(height = TICK_DEPTH + MCC_EPS)
            text(str(connector, "  bay=", bay), size = LABEL_SIZE, halign = "center",
                valign = "center", font = "Liberation Sans:style=Bold");
}

// vim: expandtab tabstop=4 shiftwidth=4 softtabstop=4 nowrap
