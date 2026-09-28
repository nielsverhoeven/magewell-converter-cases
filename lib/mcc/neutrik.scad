//////////////////////////////////////////////////////////////////////
// LibFile: mcc/neutrik.scad
//   L1. Neutrik D-series cutouts (flat-panel cutout with rear seat pocket; the wall-integrated
//   cut the cases use -- D36, round holes D40, plain fixing bores D41), flange outline and rear
//   keep-out envelope. One *provider* behind lib/mcc/panel.scad's dispatcher, not the top-level
//   panel abstraction (architecture.md §5).
//   `use`d by lib/mcc/mcc.scad and by lib/mcc/panel.scad; never called directly from models/**
//   (architecture.md:217-219 — calling mcc_neutrik_* from models/** is a layering deviation).
// Includes:
//   include <mcc/mcc.scad>
//////////////////////////////////////////////////////////////////////

include <BOSL2/std.scad>
include <constants.scad>
use <util.scad>
use <layout.scad> // mcc_aperture_window() -- L1 pure function; layout.scad never uses a provider (§3)

// Z-axis convention used throughout this file: the panel material spans Z in [0, panel_t], with
// Z=0 the REAR (inside-the-case) face and Z=panel_t the FRONT (outward, connector-flange) face.
// (mcc_neutrik_d_wall_cut() uses its own frame — seat face at Z=0, wall toward -Z; see there.)

// Module: mcc_neutrik_d_cutout()
// Usage:
//   mcc_neutrik_d_cutout(part, [mirror=], [seat_t=], [panel_t=]);
// Description:
//   Negative (subtractive) solid for a Neutrik D-series panel cutout: the main round hole plus
//   the two M3-class screw clearance holes on the standard diagonal, plus (when `panel_t` exceeds
//   `seat_t`) a rear pocket that leaves exactly `seat_t` mm of material at the flange seat while
//   the rest of the panel stays at full `panel_t` (architecture.md §5 decision 1).
//   Centered on the cutout/flange centroid in X/Y.
// Arguments:
//   part    = panel part number, key into MCC_PANEL_PARTS (constants.scad).
//   mirror  = mirror the two screw-hole positions left-right. knowledge/neutrik/d-series-cutout.md:53-56
//             "the drawings show the rear view mirrored" — front view uses mirror=false. Default: false.
//   seat_t  = desired flange-seat material thickness, mm. Default: MCC_PANEL_SEAT_T (2.0).
//   panel_t = actual panel thickness at this location, mm. Default: MCC_WALL (3.0).
module mcc_neutrik_d_cutout(part, mirror = false, seat_t = MCC_PANEL_SEAT_T, panel_t = MCC_WALL) {
    cutout_d    = mcc_cutout_d(part);
    kind        = mcc_panel_kind(part);
    is_blank    = mcc_panel_hole_d(part) == 0; // D18 (architecture.md §5 rev 8, layout-patch-wall.md
                                                // §2.5.1): unify the blank test on hole_d==0, same as
                                                // shell.scad:181 and layout.scad:187 — NOT `kind ==
                                                // "blank"`. DBA-BL-B keeps kind "blank" (BOM/ghost
                                                // discriminator) but now carries hole_d=24.0, so it is
                                                // no longer geometrically blank: it gets the full round
                                                // cutout like any other 24-class part. The kind-based
                                                // branch below is dead on every current SKU; it stays
                                                // as the guard for a possible future genuinely-solid
                                                // blank (hole_d actually 0).
    is_24_class = mcc_panel_hole_d(part) >= 24.0;

    // Tier-1 asserts. architecture.md:346 "24.0 <= cutout_d <= 24.6 (never blow out the hole)" for
    // 24.0-class parts (etherCON/XLR); 23.6-24.2 for the 23.6-class parts (HDMI/USB/BNC), per the
    // brief's own module contract. A genuinely solid blank (hole_d=0) has no functional hole, so it
    // is exempt from the diameter check — no current SKU takes this branch (see is_blank above).
    if (!is_blank) {
        assert(
            is_24_class ? (cutout_d >= 24.0 && cutout_d <= 24.6) : (cutout_d >= 23.6 && cutout_d <= 24.2),
            str("mcc: cutout_d(\"", part, "\")=", cutout_d, " out of range")
        );
    }
    // architecture.md:343 "panel seat thickness <= mcc_panel_max_t(part) (2.0 for HDMI/USB)".
    assert(
        seat_t <= mcc_panel_max_t(part),
        str("mcc: seat_t=", seat_t, " exceeds max panel thickness ", mcc_panel_max_t(part), " for \"", part, "\"")
    );

    mirror_x = mirror ? -1 : 1;
    screw_x  = mirror_x * MCC_D_SCREW_PITCH[0] / 2; // knowledge/neutrik/d-series-cutout.md:47 "±9.5 mm horizontally"
    screw_y  = MCC_D_SCREW_PITCH[1] / 2;             // knowledge/neutrik/d-series-cutout.md:47 "±12.0 mm vertically"
    cut_h    = panel_t + 2 * MCC_EPS;

    union() {
        if (!is_blank) {
            // Main circular cutout. $fn=96 + circum=true per architecture.md:130-134 — a real
            // connector flange only overlaps the hole by ~0.9 mm/side, so the polygon must
            // circumscribe, not inscribe.
            translate([0, 0, panel_t / 2])
                cyl(h = cut_h, d = cutout_d, circum = true, $fn = 96);
        }
        // Two screw clearance holes, $fn=64 minimum per architecture.md:130.
        translate([-screw_x, screw_y, panel_t / 2]) cyl(h = cut_h, d = MCC_M3_CLR_D, circum = true, $fn = 64);
        translate([ screw_x, -screw_y, panel_t / 2]) cyl(h = cut_h, d = MCC_M3_CLR_D, circum = true, $fn = 64);

        // Rear seat pocket: footprint = flange + 1 mm clearance, rounded to the flange's own
        // corner radius (architecture.md §5 decision 1 / this file's module contract).
        if (panel_t > seat_t) {
            translate([0, 0, -MCC_EPS])
                linear_extrude(height = (panel_t - seat_t) + MCC_EPS)
                    mcc_rounded_rect([MCC_D_FLANGE[0] + 1, MCC_D_FLANGE[1] + 1], MCC_D_FLANGE_R);
        }
    }
}

// Function: _mcc_seg_dist()
// Description:
//   Private, pure. Distance from 2-D point `p` to the segment [a, b].
function _mcc_seg_dist(p, a, b) =
    let(ab = b - a, t = max(0, min(1, ((p - a) * ab) / max(ab * ab, 1e-12))))
    norm(p - (a + t * ab));
// Distance from 2-D point `p` to the boundary of closed polygon `path`.
function _mcc_path_dist(p, path) =
    min([for (i = [0:1:len(path) - 1]) _mcc_seg_dist(p, path[i], path[(i + 1) % len(path)])]);

// Module: mcc_neutrik_d_wall_cut()
// Usage:
//   mcc_neutrik_d_wall_cut(part, [wall_t=], [seat_t=]);
// Description:
//   SUBTRACTIVE. Everything a Neutrik D-series connector needs from a wall it is mounted in
//   DIRECTLY -- no separate panel plate (architecture.md §5 rev 14, D36):
//     * the flange-seat hole through the first `seat_t` of wall (the connector's own
//       mcc_cutout_d(part)), and the body window behind it through the rest of the wall
//       (mcc_aperture_window(part), 2*MCC_CLR_SLIDE larger) -- both PLAIN CIRCLES, coaxial
//       (architecture.md §5 rev 15, D40, user decision 2026-09-28: perfectly round in the model, the
//       STL and the STEP -- supersedes D36's truncated teardrops). The wall prints standing, so the
//       top of each hole is a round arch: the Bambu slicer gate passes it; its print quality is
//       judged on the neutrik-tile coupon (architecture.md R39, M19). Do NOT reintroduce a
//       teardrop, cap or bridge here -- that reverses a user decision;
//     * two PLAIN cylindrical fixing bores, MCC_FIXING_BORE_D (the M3x0.5 tap-drill size), on the
//       standard diagonal (front view A(-9.5, +12) / B(+9.5, -12),
//       knowledge/neutrik/d-series-cutout.md:47,62-63), straight through the whole wall -- NOT
//       threaded (architecture.md §5 rev 15, D41, user decision 2026-09-28: the external CAD
//       specialist models the thread on the exact STEP). No chamfer, no screw pillars.
//   Local frame: X/Y is the wall face as seen FROM OUTSIDE (Y = up), Z = outward normal. The seat
//   (front) face is Z = 0 and the wall runs to Z = -wall_t (inside face). Every cut reaches MCC_EPS
//   past both faces.
//   Asserts: seat_t within the part's max panel thickness; wall_t > seat_t; at least
//   MCC_WALL_BORE_WEB_MIN of wall between each fixing bore and either opening (T1-61).
//   $fn (architecture.md §3 rev 15): the seat hole and window are $fn=96 circles at
//   mcc_cutout_d(part) / mcc_aperture_window(part), which already carry MCC_HOLE_COMP; the fixing
//   bores are $fn=64 cylinders at their NOMINAL diameter with NO circum=true, because the exact STEP
//   carries the CSG radius verbatim and the specialist needs exactly MCC_FIXING_BORE_D.
// Arguments:
//   part   = panel part number, key into MCC_PANEL_PARTS (constants.scad).
//   wall_t = total wall thickness at the connector, mm. Default: MCC_PANEL_SEAT_T + MCC_WALL.
//   seat_t = flange-seat thickness (the part of the wall the flange clamps), mm.
//            Default: MCC_PANEL_SEAT_T.
module mcc_neutrik_d_wall_cut(part, wall_t = MCC_PANEL_SEAT_T + MCC_WALL, seat_t = MCC_PANEL_SEAT_T) {
    is_blank = mcc_panel_hole_d(part) == 0;
    d_seat = mcc_cutout_d(part);
    d_win = mcc_aperture_window(part);
    sx = MCC_D_SCREW_PITCH[0] / 2; sy = MCC_D_SCREW_PITCH[1] / 2;
    screws = [[-sx, sy], [sx, -sy]]; // front view (knowledge/neutrik/d-series-cutout.md:62-63)
    bore_r = MCC_FIXING_BORE_D / 2;

    assert(seat_t <= mcc_panel_max_t(part) + MCC_EPS,
        str("mcc: seat_t=", seat_t, " exceeds max panel thickness ", mcc_panel_max_t(part), " for \"", part, "\""));
    assert(wall_t > seat_t, str("mcc: wall_t=", wall_t, " must exceed seat_t=", seat_t));
    if (!is_blank) {
        seat_path = circle(d = d_seat, $fn = 96);
        win_path = circle(d = d_win, $fn = 96);
        for (sc = screws) {
            web = min(_mcc_path_dist(sc, seat_path), _mcc_path_dist(sc, win_path)) - bore_r;
            assert(web >= MCC_WALL_BORE_WEB_MIN - MCC_EPS,
                str("mcc: T1-61 wall web between the fixing bore at ", sc, " and the opening is ", web,
                    " mm, below MCC_WALL_BORE_WEB_MIN=", MCC_WALL_BORE_WEB_MIN, " for \"", part, "\""));
        }
    }

    union() {
        if (!is_blank) {
            translate([0, 0, -seat_t - MCC_EPS])
                linear_extrude(height = seat_t + 2 * MCC_EPS)
                    circle(d = d_seat, $fn = 96);
            translate([0, 0, -wall_t - MCC_EPS])
                linear_extrude(height = wall_t - seat_t + 2 * MCC_EPS)
                    circle(d = d_win, $fn = 96);
        }
        for (sc = screws)
            translate([sc[0], sc[1], -wall_t - MCC_EPS])
                // Genuine through-hole, open at both faces (architecture.md §13 D10 Manifold reasoning).
                cyl(h = wall_t + 2 * MCC_EPS, d = MCC_FIXING_BORE_D, anchor = BOTTOM, $fn = 64);
    }
}

// Module: mcc_neutrik_d_flange_outline()
// Usage:
//   mcc_neutrik_d_flange_outline();
// Description:
//   2D flange footprint (26 x 31 mm, R3.5 corners), centered on the origin.
//   knowledge/neutrik/d-series-cutout.md:74-76.
module mcc_neutrik_d_flange_outline() {
    mcc_rounded_rect(MCC_D_FLANGE, MCC_D_FLANGE_R);
}

// Module: mcc_neutrik_d_envelope()
// Usage:
//   mcc_neutrik_d_envelope(part);
// Description:
//   Rear keep-out box (flange footprint x mcc_bay_depth(part)) extending rearward from the panel
//   plane, for interference checking against the device/cradle/shell. `%`-rendered (excluded from
//   CSG/export) and gated behind MCC_SHOW_GHOST, per architecture.md:301-305's two-belt rule.
module mcc_neutrik_d_envelope(part) {
    if (MCC_SHOW_GHOST) {
        %translate([0, 0, -mcc_bay_depth(part) / 2])
            cube([MCC_D_FLANGE[0], MCC_D_FLANGE[1], mcc_bay_depth(part)], center = true);
    }
}

// vim: expandtab tabstop=4 shiftwidth=4 softtabstop=4 nowrap
