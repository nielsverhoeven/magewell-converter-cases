//////////////////////////////////////////////////////////////////////
// LibFile: mcc/cradle.scad
//   L2. Device cradle: deck, compliant-pad pocket, far-flank ribs (duct-clearing, deterministic
//   placement per .claude/knowledge/layout-patch-wall.md §7 rev-5 addendum), patch-flank ribs, and
//   the case's own 1/4"-20 floor-mount insert boss (T1-32, installed from the underside and
//   unioned into the deck hollow). Never cuts the floor (architecture.md §6 floor rule — that is
//   mounts.scad's job). `use`d only by lib/mcc/shell.scad (the L2 composition root, architecture.md
//   §3 rev 5) — never by panel.scad/mounts.scad/vents.scad, which must not `use` each other.
// Includes:
//   include <mcc/mcc.scad>
//////////////////////////////////////////////////////////////////////

include <BOSL2/std.scad>
include <constants.scad>
use <util.scad>
use <ports.scad>
use <layout.scad>
use <fasteners.scad> // mcc_side_bolt_keepout(), mcc_case_tripod_insert_bore()

// Module: mcc_tripod_insert_bore_cut()
// Usage:
//   mcc_tripod_insert_bore_cut(dev, cfg);
// Description:
//   SUBTRACTIVE counterpart to mcc_cradle()'s plain tripod-insert boss (T1-32): the actual M4x20
//   heat-set-insert bore, opening at the case's exterior floor face (world Z=0) and reaching up
//   into the boss. Called by shell.scad in its OUTER difference() — after the floor slab and the
//   boss are already unioned together — so the bore genuinely punches through both, rather than
//   being differenced only against the boss's own local geometry (see mcc_cradle()'s own comment
//   for why that would leave it a few mm short).
// Arguments:
//   dev = device record.
//   cfg = variant-config assoc-list.
module mcc_tripod_insert_bore_cut(dev, cfg) {
    translate([0, 0, MCC_EPS])
        rotate([180, 0, 0])
            mcc_case_tripod_insert_bore();
}

// Function: _mcc_far_flank_rib_x()
// Description:
//   Private. Deterministic far-flank rib X positions — layout-patch-wall.md §7 rev-5 addendum
//   normative rule: `band` = the device's X span less an 8 mm margin at each end; `excl` = the
//   side-bolt keep-out's X exclusion (radius `c` either side of `x_bolt`); `segments` = band minus
//   excl (0/1/2 closed intervals); each surviving segment contributes its two endpoints, plus its
//   own midpoint when the segment exceeds 40 mm. For NDI to HDMI this yields the doc's own worked
//   result, 4 ribs at x = -38.95, -12.0, +19.0, +45.95.
function _mcc_far_flank_rib_x(x_dev_lo, x_dev_hi, x_bolt) =
    let(
        c    = MCC_SIDE_BOLT_KEEPOUT_D / 2 + MCC_CRADLE_RIB_T / 2 + 2.0,
        band = [x_dev_lo + 8, x_dev_hi - 8],
        excl = [x_bolt - c, x_bolt + c],
        segs_raw = (excl[1] <= band[0] || excl[0] >= band[1])
            ? [[band[0], band[1]]]
            : [
                (excl[0] > band[0]) ? [band[0], min(excl[0], band[1])] : undef,
                (excl[1] < band[1]) ? [max(excl[1], band[0]), band[1]] : undef,
            ],
        segs = [for (s = segs_raw) if (!is_undef(s) && s[1] > s[0]) s],
        pts  = [for (s = segs) each ((s[1] - s[0] > 40) ? [s[0], (s[0] + s[1]) / 2, s[1]] : [s[0], s[1]])]
    )
    pts;

// Module: mcc_cradle()
// Usage:
//   mcc_cradle(dev, cfg);
// Description:
//   ADDITIVE device cradle for `dev` under variant config `cfg`: a deck slab from the interior
//   floor to the device underside (spanning the device's XY footprint plus a small locating lip),
//   a compliant-pad pocket (subtracted) near the case centre, the deterministic far-flank ribs
//   (each with a self-supporting open notch below the deck top so the MCC_GAP_FAR duct is never
//   fully dammed — layout-patch-wall.md §7), patch-flank ribs (only outboard of the panel aperture,
//   T1-20 — none on the priority SKU today, since the device's own X span never reaches outboard of
//   the aperture), and the case's own 1/4"-20 floor-mount insert boss installed from the underside,
//   unioned into the deck hollow (T1-32).
// Arguments:
//   dev = device record.
//   cfg = variant-config assoc-list.
module mcc_cradle(dev, cfg) {
    l = mcc_case_layout(dev, cfg);
    x_dev_lo = struct_val(l, "x_dev_lo"); x_dev_hi = struct_val(l, "x_dev_hi");
    y_dev_lo = struct_val(l, "y_dev_lo"); y_dev_hi = struct_val(l, "y_dev_hi");
    z_dev_lo = struct_val(l, "z_dev_lo"); x_dev_c = struct_val(l, "x_dev_c"); y_dev_c = struct_val(l, "y_dev_c");
    plate_l  = struct_val(l, "plate_l");
    x_bolt   = struct_val(l, "side_bolt_x");

    LIP = MCC_WALL; // deck footprint margin beyond the device's own XY extent, mm — a small
                     // locating lip (this file's module contract), also wide enough that the
                     // vesa_pos-default (0,0) case tripod insert boss below lands inside the deck's
                     // hollow on every priority SKU (T1-32).
    deck_x = [x_dev_lo - LIP, x_dev_hi + LIP];
    deck_y = [y_dev_lo - LIP, y_dev_hi + LIP];

    deck_h = z_dev_lo - MCC_FLOOR_T;
    assert(deck_h > 0, str("mcc: mcc_cradle deck height ", deck_h, " <= 0 on \"", mcc_dev_slug(dev), "\""));

    union() {
        // --- Deck slab ---
        difference() {
            translate([deck_x[0], deck_y[0], MCC_FLOOR_T])
                cube([deck_x[1] - deck_x[0], deck_y[1] - deck_y[0], deck_h]);

            // Compliant floor-pad pocket, centred at (x_dev_c, y_dev_c) — inside the device's own
            // footprint by construction (layout-patch-wall.md §7).
            translate([x_dev_c, y_dev_c, MCC_FLOOR_T + deck_h - MCC_CRADLE_FLOOR_PAD_T])
                cube([MCC_CRADLE_FLOOR_PAD_MIN, MCC_CRADLE_FLOOR_PAD_MIN, MCC_CRADLE_FLOOR_PAD_T + MCC_EPS]);
        }

        // --- Case tripod-mount insert boss (T1-32): a PLAIN solid cylinder (no internal bore —
        // see mcc_tripod_insert_bore_cut() below). Installed from the underside: its own body
        // spans world Z=[0, z_dev_lo], i.e. from the case's outer floor face up into the deck
        // hollow, flush with the deck top. The bore is deliberately NOT cut here: this boss's
        // bottom cap is coplanar with the (already-solid) floor slab's own bottom face over its
        // whole footprint, and a boss+bore combo module differenced ONLY against itself (rather
        // than against the full unioned assembly) leaves the floor slab's own un-bored material
        // filling back in across that overlap — the bore would silently stop ~3 mm short of the
        // exterior face instead of reaching it. Cutting the bore separately, in shell.scad's OUTER
        // difference() (after the floor slab and this boss are already unioned together), is what
        // actually guarantees a clean through-bore. See mcc_tripod_insert_bore_cut().
        assert(struct_val(MCC_INSERT_1_4_20, "len") + 1 <= z_dev_lo,
            str("mcc: T1-32 case tripod insert stack ", struct_val(MCC_INSERT_1_4_20, "len") + 1,
                " exceeds MCC_FLOOR_T+mcc_cradle_deck(dev)=", z_dev_lo, " on \"", mcc_dev_slug(dev), "\""));
        boss_od_tripod = MCC_BOSS_MIN_RATIO * struct_val(MCC_INSERT_1_4_20, "od");
        translate([0, 0, 0])
            cyl(h = z_dev_lo, d = boss_od_tripod, circum = true, anchor = BOTTOM, $fn = 64);

        // --- Far-flank ribs (against -Y, the far/duct-side flank) ---
        rib_x = _mcc_far_flank_rib_x(x_dev_lo, x_dev_hi, x_bolt);
        assert(len(rib_x) >= 3,
            str("mcc: T1-27/§7 far-flank rib count=", len(rib_x), " < 3 on \"", mcc_dev_slug(dev), "\""));
        c_clear = MCC_SIDE_BOLT_KEEPOUT_D / 2 + MCC_CRADLE_RIB_T / 2 + 2.0;
        for (rx = rib_x) {
            assert(abs(rx - x_bolt) >= c_clear - MCC_EPS,
                str("mcc: T1-27 far-flank rib at x=", rx, " is within ", c_clear,
                    " mm of the side-bolt keepout axis x_bolt=", x_bolt, " on \"", mcc_dev_slug(dev), "\""));
            _mcc_far_flank_rib(rx, y_dev_lo, z_dev_lo);
        }

        // --- Patch-flank ribs (against +Y) -- T1-20: only where |x| > plate_l/2 - 3 ---
        patch_rib_x = [for (x = [x_dev_lo + LIP, x_dev_hi - LIP]) if (abs(x) > plate_l / 2 - 3) x];
        for (rx = patch_rib_x)
            translate([rx - MCC_CRADLE_RIB_T / 2, y_dev_hi, z_dev_lo])
                cube([MCC_CRADLE_RIB_T, MCC_GAP_DEV, MCC_CRADLE_RIB_H]);
    }
}

// Module: _mcc_far_flank_rib()
// Description:
//   Private. One far-flank rib at X position `rx`: two <=3 mm legs standing on the interior floor
//   (z=MCC_FLOOR_T) up to the deck top (z=z_dev_lo) at each Y end of the MCC_GAP_FAR duct — leaving
//   the middle of the duct open, clear span = MCC_GAP_FAR - 2*3 <= 10 mm
//   (fdm-rugged-enclosure-guidelines.md:111 / architecture.md §5) — plus a solid rib body above the
//   deck top, from the far wall's inner face to the device's far flank, MCC_CRADLE_RIB_H tall,
//   locating the device against the far wall.
// Arguments:
//   rx       = rib X position (its centre), mm.
//   y_dev_lo = the device's far (-Y) flank Y position, mm.
//   z_dev_lo = the deck top / device underside Z, mm.
module _mcc_far_flank_rib(rx, y_dev_lo, z_dev_lo) {
    y0  = y_dev_lo - MCC_GAP_FAR; // far wall inner face (y_dev_lo = -W/2+MCC_WALL+MCC_GAP_FAR, §1)
    leg = min(3.0, MCC_GAP_FAR / 2 - MCC_EPS); // <= 3 mm legs (this file's module contract / §7)

    union() {
        // Legs: floor to deck top, at each Y end of the duct.
        translate([rx - MCC_CRADLE_RIB_T / 2, y0, MCC_FLOOR_T])
            cube([MCC_CRADLE_RIB_T, leg, z_dev_lo - MCC_FLOOR_T]);
        translate([rx - MCC_CRADLE_RIB_T / 2, y_dev_lo - leg, MCC_FLOOR_T])
            cube([MCC_CRADLE_RIB_T, leg, z_dev_lo - MCC_FLOOR_T]);
        // Solid body above the deck top, spanning the full duct width, locating the device flank.
        // Starts MCC_EPS below z_dev_lo so its bottom face genuinely overlaps (not just touches)
        // the deck slab's top face, avoiding a zero-thickness coincident-face union.
        translate([rx - MCC_CRADLE_RIB_T / 2, y0, z_dev_lo - MCC_EPS])
            cube([MCC_CRADLE_RIB_T, y_dev_lo - y0, MCC_CRADLE_RIB_H + MCC_EPS]);
    }
}

// vim: expandtab tabstop=4 shiftwidth=4 softtabstop=4 nowrap
