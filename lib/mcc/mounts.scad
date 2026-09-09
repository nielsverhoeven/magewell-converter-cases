//////////////////////////////////////////////////////////////////////
// LibFile: mcc/mounts.scad
//   L2. Every case-floor feature except the case's own 1/4"-20 insert boss and the compliant-pad
//   pocket (those two live in cradle.scad, T1-32/§7 — installed from the underside, unioned into
//   the deck hollow). Owns: the tool-less dovetail mount rail (D-15, rev 9, issue #25 — replaces
//   VESA), the Fishtail M4 reservation (reserve-only, pitch unknown — M7), strap slots (displaced
//   off the reserved splitter bay per §7.1 correction 1), the splitter tie-down
//   (mcc_splitter_tiedown(orient="edge")), and a minimal stacking-profile recess.
//   Positions come from mcc_floor_keepout() (layout.scad) so this file never re-derives them; this
//   file also owns the D16 pairwise non-overlap assert over that same list (architecture.md §6,
//   §13 D16 — exempting the concentric "case_tripod_insert"/"fishtail_reserve" pair, D19).
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
use <poe_splitter.scad> // mcc_splitter_tiedown()
use <rail.scad>         // mcc_rail_female_cut() -- D-15, rev 9, issue #25

// Non-manifold-avoidance pattern this file follows for every additive floor feature: a plain solid
// block/boss (base at world Z=0, the case's exterior floor face, rising to world Z=h) is unioned in
// first, and its matching cut is applied SEPARATELY, in shell.scad's OUTER difference() — never a
// bore/cut differenced only against the feature's own local geometry, which would be silently
// backfilled by the overlapping, un-cut floor slab and stop short of the exterior face (same
// failure mode as cradle.scad's tripod boss — see its own comment). mcc_rail_features_cut() below
// is the current example (it replaces the retired mcc_floor_bore_cut(), architecture.md §6 rev 9).

// Module: mcc_floor_features_add()
// Usage:
//   mcc_floor_features_add(dev, cfg);
// Description:
//   ADDITIVE floor features: the mount-rail sill (D-15, rev 9, issue #25 — replaces VESA), a plain
//   MCC_RAIL_LEN x MCC_RAIL_ROOT_W x MCC_RAIL_SILL_H solid block at (0, MCC_RAIL_Y), skipped
//   entirely when `cfg`'s "rail" key is explicitly false (default true, mirroring the old "vesa"
//   flag's off-switch convenience). Split into an ADD (here) + a separate CUT
//   (mcc_rail_features_cut(), below) for the same non-manifold reason documented at the top of this
//   file.
// Arguments:
//   dev = device record.
//   cfg = variant-config assoc-list. Optional key "rail" (default true).
module mcc_floor_features_add(dev, cfg) {
    rail_flag = struct_val(cfg, "rail");
    rail_on = is_undef(rail_flag) ? true : rail_flag;

    if (rail_on) {
        // Rail-in-floor assert (docs/plans/2026-09-09-mount-rail-and-brackets.md §1.5): MCC_RAIL_LEN
        // must fit within the usable floor X-span for this dev/cfg -- reuses the panel-frame-band
        // figure as the conservative bound (already L's tightest documented interior margin) --
        // fails loudly if a future SKU is smaller than the compact family.
        l = mcc_case_layout(dev, cfg);
        L = struct_val(l, "L");
        assert(MCC_RAIL_LEN <= L - 2 * MCC_WALL - 2 * MCC_PANEL_FRAME_MIN,
            str("mcc: MCC_RAIL_LEN=", MCC_RAIL_LEN, " does not fit the usable floor span on \"",
                mcc_dev_slug(dev), "\" (L=", L, ")"));

        translate([0, MCC_RAIL_Y, 0])
            _mcc_floor_boss_from_below_rect([MCC_RAIL_LEN, MCC_RAIL_ROOT_W], MCC_RAIL_SILL_H);
    }
}

// Module: _mcc_floor_boss_from_below_rect()
// Description:
//   Private. A plain solid block (no internal cut), base at world Z=0 rising to world Z=h, centred
//   in X/Y on the caller's own translate() — the rectangular counterpart to the non-manifold-
//   avoidance pattern documented at the top of this file. The matching cut is applied separately,
//   in shell.scad's OUTER difference(), via mcc_rail_features_cut() below.
// Arguments:
//   size = [x, y] footprint, mm.
//   h    = block height, mm.
module _mcc_floor_boss_from_below_rect(size, h) {
    cuboid([size[0], size[1], h], anchor = BOTTOM);
}

// Module: mcc_rail_features_cut()
// Usage:
//   mcc_rail_features_cut(dev, cfg);
// Description:
//   SUBTRACTIVE counterpart to mcc_floor_features_add()'s rail sill (mirrors the "rail" flag).
//   Called by shell.scad in its OUTER difference() — after the floor slab and the sill are already
//   unioned together — immediately after (replaces) the old mcc_floor_bore_cut() call site, for the
//   identical non-manifold reason documented at the top of this file. Retires mcc_floor_bore_cut()
//   entirely (architecture.md §6 rev 9, R5) — not left behind as an empty module.
// Arguments:
//   dev = device record.
//   cfg = variant-config assoc-list. Optional key "rail" (default true).
module mcc_rail_features_cut(dev, cfg) {
    rail_flag = struct_val(cfg, "rail");
    rail_on = is_undef(rail_flag) ? true : rail_flag;
    if (rail_on) {
        translate([0, MCC_RAIL_Y, 0])
            mcc_rail_female_cut(len = MCC_RAIL_LEN);
    }
}

// Function: _mcc_floor_feature_overlap()
// Description:
//   Private, pure. True if two mcc_floor_keepout() rows (each [cx, cy, "circle"|"rect", size_or_d,
//   label]) overlap, using the repo's own separation rule (layout-patch-wall.md §7.1: "15 mm
//   centre-to-centre, or r1+r2+2.0 where larger" for two circles; a plain inflated-AABB test
//   otherwise, since rect-vs-rect/circle-vs-rect have no simpler exact form and every rect feature
//   here is axis-aligned).
function _mcc_floor_feature_overlap(a, b) =
    let(
        ax = a[0], ay = a[1], bx = b[0], by = b[1],
        // Half-extent in X/Y for each feature -- a circle's half-extent is its radius in both axes;
        // a rect's is half its own [x,y] size.
        a_hx = a[2] == "circle" ? a[3] / 2 : a[3][0] / 2,
        a_hy = a[2] == "circle" ? a[3] / 2 : a[3][1] / 2,
        b_hx = b[2] == "circle" ? b[3] / 2 : b[3][0] / 2,
        b_hy = b[2] == "circle" ? b[3] / 2 : b[3][1] / 2,
        sep  = (a[2] == "circle" && b[2] == "circle")
            ? max(MCC_FLOOR_FEATURE_MIN_SEP, a_hx + b_hx + 2.0)
            : MCC_FLOOR_FEATURE_EDGE_MIN
    )
    (abs(ax - bx) < a_hx + b_hx + sep) && (abs(ay - by) < a_hy + b_hy + sep);

// Module: mcc_assert_floor_keepout_no_overlap()
// Usage:
//   mcc_assert_floor_keepout_no_overlap(dev, cfg);
// Description:
//   D16 (architecture.md §13, fixed by issue #25): asserts every pairwise combination of
//   mcc_floor_keepout(dev, cfg)'s own rows does not overlap (per _mcc_floor_feature_overlap()
//   above), EXCEPT the "case_tripod_insert"/"fishtail_reserve" pair, which is deliberately
//   concentric at floor_center (D19, architecture.md §13, layout-patch-wall.md §17.2 R3) -- a
//   reserve-only band may coincide with the feature it is anchored on; two features that BOTH cut
//   real geometry may not. Called once from mcc_shell_base() alongside the rest of this file's
//   floor-feature calls.
// Arguments:
//   dev = device record.
//   cfg = variant-config assoc-list.
module mcc_assert_floor_keepout_no_overlap(dev, cfg) {
    rows = mcc_floor_keepout(dev, cfg);
    n = len(rows);
    for (i = [0:1:n - 2])
        for (j = [i + 1:1:n - 1])
            if (!((rows[i][4] == "case_tripod_insert" && rows[j][4] == "fishtail_reserve")
               || (rows[i][4] == "fishtail_reserve" && rows[j][4] == "case_tripod_insert")))
                assert(!_mcc_floor_feature_overlap(rows[i], rows[j]),
                    str("mcc: floor features \"", rows[i][4], "\" and \"", rows[j][4],
                        "\" overlap on \"", mcc_dev_slug(dev), "\" (D16)"));
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
