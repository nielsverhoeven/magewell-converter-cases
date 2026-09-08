//////////////////////////////////////////////////////////////////////
// LibFile: mcc/mounts.scad
//   L2. Every case-floor feature except the case's own 1/4"-20 insert boss and the compliant-pad
//   pocket (those two live in cradle.scad, T1-32/§7 — installed from the underside, unioned into
//   the deck hollow). Owns: VESA 75x75 blind M4 heat-set-insert bosses (layout-patch-wall.md §15
//   ruling H — architect ruling, blind bosses not through-holes, because the compact family's VESA
//   pattern lands under the device), the Fishtail M4 reservation (reserve-only, pitch unknown —
//   M7), strap slots (displaced off the reserved splitter bay per §7.1 correction 1), the splitter
//   tie-down (mcc_splitter_tiedown(orient="edge")), and a minimal stacking-profile recess.
//   Positions come from mcc_floor_keepout() (layout.scad) so this file never re-derives them.
//   `use`d only by lib/mcc/shell.scad (the L2 composition root) — never by cradle.scad/panel.scad/
//   vents.scad, which must not `use` each other.
// Includes:
//   include <mcc/mcc.scad>
//////////////////////////////////////////////////////////////////////

include <BOSL2/std.scad>
include <constants.scad>
use <util.scad>
use <ports.scad>        // mcc_dev_slug() (assert messages)
use <layout.scad>
use <fasteners.scad>   // mcc_heat_set_boss(), mcc_m4_hole()
use <poe_splitter.scad> // mcc_splitter_tiedown()

// Module: _mcc_floor_boss_from_below()
// Description:
//   Private. A PLAIN solid boss (no internal bore — see _mcc_floor_bore_from_below() below), base
//   at world Z=0 (the case's exterior floor face) rising to world Z=h. Deliberately not built from
//   mcc_heat_set_boss()'s combo (boss+internal bore): this boss's bottom cap is coplanar with the
//   (already-solid) floor slab's own bottom face over its whole footprint, and a bore differenced
//   only against the boss's own local geometry leaves the floor slab's un-bored material filling
//   back in across that overlap, so the bore silently stops short of the exterior face instead of
//   reaching it (same failure mode as cradle.scad's tripod boss — see its own comment). The
//   matching bore is cut separately, in shell.scad's OUTER difference(), by
//   _mcc_floor_bore_from_below() below via mcc_floor_bore_cut().
// Arguments:
//   od = boss outer diameter, mm.
//   h  = boss height, mm.
module _mcc_floor_boss_from_below(od, h) {
    cyl(h = h, d = od, circum = true, anchor = BOTTOM, $fn = 64);
}

// Module: _mcc_floor_bore_from_below()
// Description:
//   Private. The bore counterpart to _mcc_floor_boss_from_below(): opens at world Z=0 (the
//   exterior floor face) and reaches up into the boss by the insert's own bore depth.
//   mcc_heat_set_bore()'s own convention opens its bore at LOCAL Z=0 extending into -Z, so a
//   180 deg flip about X lands that open face at world Z=0 and the blind end at world Z=+depth.
// Arguments:
//   insert = insert record (constants.scad shape).
module _mcc_floor_bore_from_below(insert) {
    translate([0, 0, MCC_EPS])
        rotate([180, 0, 0])
            mcc_heat_set_bore(insert);
}

// Function: _mcc_vesa_positions()
// Description:
//   Private. The 4 VESA 75x75 hole centres, `vesa_pos` (default (0,0)) +- MCC_VESA75_PITCH/2.
function _mcc_vesa_positions(vesa_pos = [0, 0]) =
    [for (sx = [-1, 1]) for (sy = [-1, 1])
        [vesa_pos[0] + sx * MCC_VESA75_PITCH / 2, vesa_pos[1] + sy * MCC_VESA75_PITCH / 2]];

// Module: mcc_floor_features_add()
// Usage:
//   mcc_floor_features_add(dev, cfg);
// Description:
//   ADDITIVE floor features: the 4 VESA 75x75 blind M4 heat-set-insert bosses (skipped entirely
//   when `cfg`'s "vesa" key is explicitly false — default true, layout-patch-wall.md §15 ruling H).
//   A uniform boss height (M4 insert depth + margin) is used at all 4 points rather than a
//   per-point height keyed to whether that point happens to land under the cradle deck on this
//   particular SKU (2 of the 4 do, 2 don't, per §7.1 rev-5 correction 4) — where the deck already
//   fills the same volume the boss simply embeds in it (redundant, harmless material); where it
//   doesn't, the boss stands as a small free-standing post rising from the floor.
// Arguments:
//   dev = device record.
//   cfg = variant-config assoc-list. Optional key "vesa" (default true).
module mcc_floor_features_add(dev, cfg) {
    vesa_flag = struct_val(cfg, "vesa");
    vesa_on = is_undef(vesa_flag) ? true : vesa_flag;

    if (vesa_on) {
        h = struct_val(MCC_INSERT_M4, "len") + 1 + 2; // bore depth (len+1) + 2 mm margin, mm.
        l = mcc_case_layout(dev, cfg);
        bay_x = struct_val(l, "splitter_bay_x"); bay_y = struct_val(l, "splitter_bay_y");
        boss_r = MCC_BOSS_MIN_RATIO * struct_val(MCC_INSERT_M4, "od") / 2;
        for (p = _mcc_vesa_positions()) {
            // T1-17-style: a VESA boss must not intrude into the reserved splitter bay footprint.
            assert(p[0] + boss_r <= bay_x[0] || p[0] - boss_r >= bay_x[1]
                || p[1] + boss_r <= bay_y[0] || p[1] - boss_r >= bay_y[1],
                str("mcc: VESA boss at ", p, " intrudes into the reserved splitter bay ", bay_x, "x", bay_y,
                    " on \"", mcc_dev_slug(dev), "\""));
            translate([p[0], p[1], 0])
                _mcc_floor_boss_from_below(boss_r * 2, h);
        }
    }
}

// Module: mcc_floor_bore_cut()
// Usage:
//   mcc_floor_bore_cut(dev, cfg);
// Description:
//   SUBTRACTIVE counterpart to mcc_floor_features_add()'s VESA bosses (mirrors the "vesa" flag).
//   Called by shell.scad in its OUTER difference() — after the floor slab and the bosses are
//   already unioned together — so each bore genuinely punches through both (see
//   _mcc_floor_boss_from_below()'s own comment for why cutting it only inside the boss's local
//   geometry would leave it a few mm short).
// Arguments:
//   dev = device record.
//   cfg = variant-config assoc-list. Optional key "vesa" (default true).
module mcc_floor_bore_cut(dev, cfg) {
    vesa_flag = struct_val(cfg, "vesa");
    vesa_on = is_undef(vesa_flag) ? true : vesa_flag;
    if (vesa_on) {
        for (p = _mcc_vesa_positions())
            translate([p[0], p[1], 0])
                _mcc_floor_bore_from_below(MCC_INSERT_M4);
    }
}

// Module: mcc_floor_features_cut()
// Usage:
//   mcc_floor_features_cut(dev, cfg);
// Description:
//   SUBTRACTIVE floor features: the 2 (or, with the -X pair displaced clear of the splitter bay,
//   still 2) strap-slot pairs, the splitter tie-down (mcc_splitter_tiedown(orient="edge"), NOT
//   hand-rolled holes — layout-patch-wall.md §15 ruling 7), and a minimal stacking-profile recess
//   (a shallow counterbore at each corner lid-fastener position, so a stacked second case's feet
//   have somewhere to seat). The Fishtail M4 pattern is RESERVE-ONLY per §15 correction 4 (pitch
//   unknown, M7) — no holes are cut for it here, only the keep-out registered in
//   mcc_floor_keepout().
// Arguments:
//   dev = device record.
//   cfg = variant-config assoc-list.
module mcc_floor_features_cut(dev, cfg) {
    l = mcc_case_layout(dev, cfg);
    keepout = mcc_floor_keepout(dev, cfg);

    // Strap slots: through-floor rectangular cuts, from mcc_floor_keepout()'s own positions so
    // this file never re-derives the -X-pair displacement (§7.1 correction 1).
    for (f = keepout) {
        label = f[4];
        if (label == "strap_pos_y" || label == "strap_pos_neg_y" || label == "strap_neg_y" || label == "strap_neg_neg_y") {
            size = f[3];
            translate([f[0], f[1], -MCC_EPS])
                cube([size[0], size[1], MCC_FLOOR_T + 2 * MCC_EPS], center = true);
        }
    }

    // Splitter tie-down, positioned at the reserved bay's own XY centre.
    bay_x = struct_val(l, "splitter_bay_x");
    bay_y = struct_val(l, "splitter_bay_y");
    translate([(bay_x[0] + bay_x[1]) / 2, (bay_y[0] + bay_y[1]) / 2, 0])
        mcc_splitter_tiedown(orient = "edge");

    // Minimal stacking-profile recess: a shallow counterbore under each corner lid-fastener
    // position, mirroring that fastener's boss so a stacked case's feet seat cleanly.
    corner_r = MCC_BOSS_MIN_RATIO * struct_val(MCC_INSERT_M3, "od") / 2 + 1.5;
    lid_pos = struct_val(l, "lid_fastener_pos");
    for (i = [0:1:3]) // the 4 corners are always the first 4 entries (mcc_case_layout()'s own order)
        translate([lid_pos[i][0], lid_pos[i][1], -MCC_EPS])
            cyl(h = 1.0 + MCC_EPS, r = corner_r, circum = true, anchor = BOTTOM, $fn = 32);
}

// vim: expandtab tabstop=4 shiftwidth=4 softtabstop=4 nowrap
