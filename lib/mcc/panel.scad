//////////////////////////////////////////////////////////////////////
// LibFile: mcc/panel.scad
//   L2 (layout-independent — the connector panel plate). Owns mcc_panel_cutout(), the
//   TOP-LEVEL dispatcher for every panel connector kind (architecture.md §5 "Panel cutout
//   dispatcher": neutrik.scad is one *provider* behind it, not the top-level abstraction).
//   models/** must call mcc_panel_cutout(), never mcc_neutrik_* directly — that is a layering
//   deviation per architecture.md:217-219.
//   `use`d by lib/mcc/mcc.scad.
// Includes:
//   include <mcc/mcc.scad>
//////////////////////////////////////////////////////////////////////

include <BOSL2/std.scad>
include <constants.scad>
use <util.scad>
use <neutrik.scad>

// Z-axis convention: matches lib/mcc/neutrik.scad — a plate/panel spans Z=[0, panel_t] with the
// outward (connector-flange) face at Z=panel_t.

// Module: _mcc_minidin8_cutout()
// Description:
//   Private helper behind the mcc_panel_cutout() dispatcher. Mini-DIN-8 "PTZ+TALLY" cutout: a
//   round hole sized mcc_cutout_d("MINIDIN8"), plus optional M2.5 fixing screws at
//   MCC_MINIDIN8_SCREW_PITCH (both entirely assumed — see constants.scad's Mini-DIN-8 section and
//   architecture.md §12 Q5). architecture.md §5 "no D-size equivalent ... needs a bespoke round
//   cutout with its own flange/fixing pattern".
// Arguments:
//   mirror         = mirror the fixing-screw positions left-right. Default: false.
//   seat_t         = desired seat material thickness, mm. Default: MCC_PANEL_SEAT_T.
//   panel_t        = actual panel thickness at this location, mm. Default: MCC_WALL.
//   fixing_screws  = cut the two optional M2.5 fixing screws. Default: true.
module _mcc_minidin8_cutout(mirror = false, seat_t = MCC_PANEL_SEAT_T, panel_t = MCC_WALL, fixing_screws = true) {
    part = "MINIDIN8";
    assert(seat_t <= mcc_panel_max_t(part),
        str("mcc: seat_t=", seat_t, " exceeds max panel thickness ", mcc_panel_max_t(part), " for \"", part, "\""));

    d         = mcc_cutout_d(part);
    cut_h     = panel_t + 2 * MCC_EPS;
    mirror_x  = mirror ? -1 : 1;

    union() {
        translate([0, 0, panel_t / 2]) cyl(h = cut_h, d = d, circum = true, $fn = 64);

        if (fixing_screws) {
            for (sx = [-1, 1])
                translate([mirror_x * sx * MCC_MINIDIN8_SCREW_PITCH / 2, 0, panel_t / 2])
                    cyl(h = cut_h, d = MCC_M2_5_CLR_D, circum = true, $fn = 48);
        }

        // Generic round seat pocket (no Neutrik flange geometry exists for this connector) —
        // footprint margin assumed, TODO(teamlead) per constants.scad's Mini-DIN-8 section.
        if (panel_t > seat_t) {
            translate([0, 0, -MCC_EPS])
                linear_extrude(height = (panel_t - seat_t) + MCC_EPS)
                    circle(d = d + 8, $fn = 64);
        }
    }
}

// Module: mcc_panel_cutout()
// Usage:
//   mcc_panel_cutout(part, [mirror=], [seat_t=], [panel_t=]);
// Description:
//   Panel-cutout dispatcher (architecture.md §5). Routes to the right provider by part number:
//   any Neutrik D-series part (including "DBA-BL-B", the blank — it shares the same flange/screw
//   footprint, per this file's module contract) goes to mcc_neutrik_d_cutout(); "MINIDIN8" goes
//   to the bespoke round cutout above.
// Arguments:
//   part    = panel part number, key into MCC_PANEL_PARTS (constants.scad).
//   mirror  = mirror the screw/fixing positions left-right. Default: false.
//   seat_t  = desired seat material thickness, mm. Default: MCC_PANEL_SEAT_T.
//   panel_t = actual panel thickness at this location, mm. Default: MCC_WALL.
module mcc_panel_cutout(part, mirror = false, seat_t = MCC_PANEL_SEAT_T, panel_t = MCC_WALL) {
    if (part == "MINIDIN8") {
        _mcc_minidin8_cutout(mirror = mirror, seat_t = seat_t, panel_t = panel_t);
    } else {
        mcc_neutrik_d_cutout(part, mirror = mirror, seat_t = seat_t, panel_t = panel_t);
    }
}

// Module: mcc_panel_plate()
// Usage:
//   mcc_panel_plate(size, slots, [t=], [rim_t=], [rim_w=]);
// Description:
//   The bolt-in connector panel plate (architecture.md §5): a flat field at thickness `t` (the
//   uniform flange-seat thickness) with a thicker structural rim of width `rim_w` around the
//   border (for the 4-corner M3-into-heat-set-insert rabbet fixing), minus every slot's cutout,
//   plus rear screw bosses per slot. Front (outward) face at Z=0 for both the field and the rim,
//   so every connector's flange seat lands on one flush plane regardless of the local material
//   thickness behind it.
//   Asserts (architecture.md §9 Tier-1): every pair of slots clears the minimum D-series pitch
//   (MCC_D_PITCH_H horizontally or MCC_D_PITCH_V vertically), every slot's flange keeps >= 4 mm
//   web to the plate edge, and the plate fits the printable envelope.
// Arguments:
//   size  = [w, h] overall plate footprint, mm.
//   slots = list of [x, y, part, mirror] connector placements (center position, panel part
//           number, mirror flag). Default: [].
//   t     = field (flange-seat) thickness, mm. Default: MCC_PANEL_SEAT_T (2.0).
//   rim_t = rim thickness, mm. Default: MCC_WALL (3.0).
//   rim_w = rim (border) width, mm. Default: 6.
module mcc_panel_plate(size, slots = [], t = MCC_PANEL_SEAT_T, rim_t = MCC_WALL, rim_w = 6) {
    w = size[0];
    h = size[1];

    assert(mcc_bbox_ok([w, h, rim_t]),
        str("mcc: panel plate ", w, "x", h, " exceeds the printable envelope"));

    for (i = [0 : 1 : len(slots) - 1]) {
        s_i    = slots[i];
        part_i = s_i[2];
        assert(abs(s_i[0]) + MCC_D_FLANGE[0] / 2 + MCC_D_FLANGE_EDGE_MARGIN <= w / 2,
            str("mcc: slot ", i, " (\"", part_i, "\") flange is within ", MCC_D_FLANGE_EDGE_MARGIN, " mm of the panel edge (X)"));
        assert(abs(s_i[1]) + MCC_D_FLANGE[1] / 2 + MCC_D_FLANGE_EDGE_MARGIN <= h / 2,
            str("mcc: slot ", i, " (\"", part_i, "\") flange is within ", MCC_D_FLANGE_EDGE_MARGIN, " mm of the panel edge (Y)"));
        for (j = [i + 1 : 1 : len(slots) - 1]) {
            s_j = slots[j];
            dx = abs(s_j[0] - s_i[0]);
            dy = abs(s_j[1] - s_i[1]);
            assert(dx >= MCC_D_PITCH_H || dy >= MCC_D_PITCH_V,
                str("mcc: slots ", i, " and ", j, " are closer than the minimum D-series pitch"));
        }
    }

    difference() {
        union() {
            translate([0, 0, -t])
                linear_extrude(height = t)
                    square([w, h], center = true);
            translate([0, 0, -rim_t])
                linear_extrude(height = rim_t)
                    difference() {
                        square([w, h], center = true);
                        square([w - 2 * rim_w, h - 2 * rim_w], center = true);
                    }
        }

        for (cx = [-1, 1]) for (cy = [-1, 1])
            translate([cx * (w / 2 - rim_w / 2), cy * (h / 2 - rim_w / 2), -rim_t / 2])
                cyl(h = rim_t + 2 * MCC_EPS, d = MCC_M3_CLR_D, circum = true, $fn = 64);

        for (s = slots)
            translate([s[0], s[1], -t])
                mcc_panel_cutout(s[2], mirror = s[3], seat_t = t, panel_t = t);
    }

    for (s = slots)
        if (s[2] != "MINIDIN8")
            translate([s[0], s[1], -t])
                mcc_neutrik_d_bosses(s[2], mirror = s[3]);
}

// vim: expandtab tabstop=4 shiftwidth=4 softtabstop=4 nowrap
