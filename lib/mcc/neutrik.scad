//////////////////////////////////////////////////////////////////////
// LibFile: mcc/neutrik.scad
//   L1. Neutrik D-series cutout, rear seat pocket, screw bosses, flange outline, and rear
//   keep-out envelope. One *provider* behind lib/mcc/panel.scad's dispatcher, not the top-level
//   panel abstraction (architecture.md:213-219).
//   `use`d by lib/mcc/mcc.scad and by lib/mcc/panel.scad; never called directly from models/**
//   (architecture.md:217-219 — calling mcc_neutrik_* from models/** is a layering deviation).
// Includes:
//   include <mcc/mcc.scad>
//////////////////////////////////////////////////////////////////////

include <BOSL2/std.scad>
include <constants.scad>
use <util.scad>

// Z-axis convention used throughout this file: the panel material spans Z in [0, panel_t], with
// Z=0 the REAR (inside-the-case) face and Z=panel_t the FRONT (outward, connector-flange) face.
// Rear bosses/pockets are modelled in their own local frame with Z=0 at the rear pocket floor,
// extending further rearward (negative Z) — see mcc_neutrik_d_bosses().

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
    is_blank    = (kind == "blank");
    is_24_class = mcc_panel_hole_d(part) >= 24.0;

    // Tier-1 asserts. architecture.md:346 "24.0 <= cutout_d <= 24.6 (never blow out the hole)" for
    // 24.0-class parts (etherCON/XLR); 23.6-24.2 for the 23.6-class parts (HDMI/USB/BNC), per the
    // brief's own module contract. A blank plate (hole_d=0) has no functional hole, so it is
    // exempt from the diameter check.
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

// Module: mcc_neutrik_d_bosses()
// Usage:
//   mcc_neutrik_d_bosses(part, [mirror=], [boss_h=]);
// Description:
//   Two rear bosses (ADDITIVE solid, union onto the panel) at the two screw positions, each with
//   a blind M3 heat-set-insert bore. architecture.md:206-207 "local rear bosses at the two screw
//   positions, protruding rearward from the 2.0 mm seat to ~7 mm total". Local Z convention: Z=0
//   is the rear pocket floor (butts against the panel), the boss extends to Z=-boss_h, and the
//   insert bore opens at the rear tip (Z=-boss_h) going forward.
// Arguments:
//   part    = panel part number (only used to keep the call site symmetric with the cutout call;
//             the boss geometry itself does not vary per connector).
//   mirror  = mirror the two screw-hole positions left-right, matching mcc_neutrik_d_cutout()'s
//             own `mirror` argument so the two calls stay aligned. Default: false.
//   boss_h  = total rearward boss length from the seat, mm. Default: 7 (architecture.md:207).
//   boss_od = boss outer diameter override, mm. Default: MCC_BOSS_MIN_RATIO * insert OD.
module mcc_neutrik_d_bosses(part, mirror = false, boss_h = 7, boss_od = undef) {
    insert        = MCC_INSERT_M3;
    insert_od     = struct_val(insert, "od");
    insert_hole_d = struct_val(insert, "hole_d");
    insert_len    = struct_val(insert, "len");
    _boss_od      = is_undef(boss_od) ? MCC_BOSS_MIN_RATIO * insert_od : boss_od;

    // architecture.md:348 "heat-set boss OD >= 1.8 * insert OD".
    assert(
        _boss_od >= MCC_BOSS_MIN_RATIO * insert_od,
        str("mcc: boss_od=", _boss_od, " below minimum ", MCC_BOSS_MIN_RATIO, "x insert OD (", insert_od, ")")
    );

    mirror_x   = mirror ? -1 : 1;
    screw_x    = mirror_x * MCC_D_SCREW_PITCH[0] / 2;
    screw_y    = MCC_D_SCREW_PITCH[1] / 2;
    bore_depth = insert_len + 1; // MCC_INSERT_M3 len (5.7) + 1 mm clearance past the insert's own length.

    assert(bore_depth <= boss_h,
        str("mcc: insert bore_depth=", bore_depth, " exceeds boss_h=", boss_h));

    for (pos = [[-screw_x, screw_y], [screw_x, -screw_y]]) {
        translate([pos[0], pos[1], 0])
        difference() {
            translate([0, 0, -boss_h / 2])
                cyl(h = boss_h, d = _boss_od, circum = true, $fn = 64);
            translate([0, 0, -boss_h + bore_depth / 2])
                cyl(h = bore_depth + MCC_EPS, d = insert_hole_d, circum = true, $fn = 64);
        }
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
