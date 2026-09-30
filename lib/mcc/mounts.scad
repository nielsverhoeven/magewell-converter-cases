//////////////////////////////////////////////////////////////////////
// LibFile: mcc/mounts.scad
//   L2. Every case-floor feature except the case's own opt-in 1/4"-20 insert boss (cradle.scad, T1-32 —
//   installed from the underside into the deck hollow; since D44 only with ["rail", false], T1-63).
//   Owns: the tool-less dovetail mount rail (D-15, rev 9, issue #25 — replaces VESA; widened, flush and
//   >= 0.5 mm-clearance since D44; closed -X end wall (D64.1), top lock and slot backing (D63.1)). The
//   strap slots and the stacking-profile recesses are removed (D87.1) and the splitter tie-down slots
//   are gone (D65.1): the floor feature is the mount-rail groove alone, the bay stays reserved and
//   nothing is cut into the floor under it.
//   Positions come from mcc_floor_keepout() (layout.scad) so this file never re-derives them; this
//   file also owns the D16 pairwise non-overlap assert over that same list (architecture.md §6,
//   §13 D16 — no exemptions since D44).
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
//   (MCC_RAIL_LEN + 2*MCC_RAIL_END_WALL) x (MCC_RAIL_ROOT_W + 2*MCC_RAIL_SILL_SIDE_W) x MCC_RAIL_SILL_H
//   solid block at (0, MCC_RAIL_Y) -- the groove's closed -X end keeps MCC_RAIL_END_WALL of it (T1-64.1)
//   -- plus the lock slot's backing (mcc_rail_female_backing(), T1-38, D63.1), skipped
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

        // T1-17 (D45, closed by D64.1): the sill -- the working length plus MCC_RAIL_END_WALL at each
        // end -- clears the reserved splitter bay by MCC_FAN_BAY_CLR (architecture.md §6 clearance rule).
        sill_x0 = -MCC_RAIL_LEN / 2 - MCC_RAIL_END_WALL;
        assert(sill_x0 >= struct_val(l, "splitter_bay_x")[1] + MCC_FAN_BAY_CLR - MCC_EPS,
            str("mcc: T1-17 rail sill -X end x=", sill_x0, " is within MCC_FAN_BAY_CLR=", MCC_FAN_BAY_CLR,
                " of the reserved splitter bay (x <= ", struct_val(l, "splitter_bay_x")[1], ") on \"",
                mcc_dev_slug(dev), "\""));
        // T1-64.1 (D64.1): the groove's closed -X end keeps a full wall behind it -- the groove
        // (MCC_RAIL_DEPTH) is deeper than the floor (MCC_FLOOR_T), so the end stop needs the sill.
        assert(MCC_RAIL_END_WALL >= MCC_WALL - MCC_EPS,
            str("mcc: T1-64.1 MCC_RAIL_END_WALL=", MCC_RAIL_END_WALL, " below MCC_WALL=", MCC_WALL));

        translate([0, MCC_RAIL_Y, 0]) {
            // Width: root + a full side wall each side (MCC_RAIL_SILL_SIDE_W, D30) — never just
            // the root width, which leaves knife-edge sill walls and an unsupported groove roof.
            _mcc_floor_boss_from_below_rect([MCC_RAIL_LEN + 2 * MCC_RAIL_END_WALL, MCC_RAIL_ROOT_W + 2 * MCC_RAIL_SILL_SIDE_W], MCC_RAIL_SILL_H);
            // D63.1: material over the lock's roof slot, so T1-38 holds there too.
            mcc_rail_female_backing();
        }

        // Insertion passage (D34): the groove runs on from the sill's +X end out through the +X wall
        // so a case can actually be slid onto a bracket. Its sill is capped by the fan-bay
        // reservation above it (fan_bay_z[0]; the bay is reserved in every variant, §6), leaving a
        // thinner roof than T1-38's — acceptable because at full mate the male no longer reaches
        // here (it only guides during insertion). The -X end zone is not an option: the splitter
        // bay reservation starts on the floor there.
        pass_h = min(MCC_RAIL_SILL_H, struct_val(l, "fan_bay_z")[0]);
        assert(pass_h - MCC_RAIL_DEPTH >= MCC_RAIL_PASSAGE_ROOF_MIN - MCC_EPS,
            str("mcc: D34 rail passage roof ", pass_h - MCC_RAIL_DEPTH, " below MCC_RAIL_PASSAGE_ROOF_MIN on \"",
                mcc_dev_slug(dev), "\""));
        pass_x0 = MCC_RAIL_LEN / 2 + MCC_RAIL_END_WALL - MCC_EPS;
        pass_x1 = L / 2 - MCC_WALL + MCC_EPS;
        translate([(pass_x0 + pass_x1) / 2, MCC_RAIL_Y, 0])
            _mcc_floor_boss_from_below_rect([pass_x1 - pass_x0, MCC_RAIL_ROOT_W + 2 * MCC_RAIL_SILL_SIDE_W], pass_h);
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
        // Open at +X through the case wall (D34): the groove's closed -X end is the end stop. The
        // +X outer face (x = L/2) gets the 45-degree lead-in on flanks, mouth and roof (D63.1).
        L = struct_val(mcc_case_layout(dev, cfg), "L");
        translate([0, MCC_RAIL_Y, 0])
            mcc_rail_female_cut(len = MCC_RAIL_LEN, open_ext = L / 2 - MCC_RAIL_LEN / 2 + 1, entry_x = L / 2);
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
//   above). No exemptions since D44 (2026-09-28): the concentric "case_tripod_insert"/
//   "fishtail_reserve" pair D19 exempted no longer exists. Called once from mcc_shell_base()
//   alongside the rest of this file's floor-feature calls.
// Arguments:
//   dev = device record.
//   cfg = variant-config assoc-list.
module mcc_assert_floor_keepout_no_overlap(dev, cfg) {
    rows = mcc_floor_keepout(dev, cfg);
    n = len(rows);
    for (i = [0:1:n - 2])
        for (j = [i + 1:1:n - 1])
            assert(!_mcc_floor_feature_overlap(rows[i], rows[j]),
                str("mcc: floor features \"", rows[i][4], "\" and \"", rows[j][4],
                    "\" overlap on \"", mcc_dev_slug(dev), "\" (D16)"));
}

// vim: expandtab tabstop=4 shiftwidth=4 softtabstop=4 nowrap
