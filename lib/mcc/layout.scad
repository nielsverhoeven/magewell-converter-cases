//////////////////////////////////////////////////////////////////////
// LibFile: mcc/layout.scad
//   L1. The case-layout solver — PURE FUNCTIONS ONLY, NEVER A MODULE (architecture.md §3, added
//   rev 5, 2026-09-08 — layout-patch-wall.md §15 ruling 1, ACCEPTED). The one place the envelope
//   (L/W/H), device placement, slot assignment, end-zone, panel-plate, fan/splitter-bay,
//   side-bolt-axis and lid-fastener formulas in .claude/knowledge/layout-patch-wall.md live, so
//   shell.scad/panel.scad/cradle.scad/mounts.scad/vents.scad never re-derive them independently.
//   Constrained so this file can never grow into a second shell: it may `use` only
//   constants.scad/ports.scad/util.scad — NEVER an L1 geometry provider (neutrik/fasteners/fan/
//   poe_splitter/ghost.scad). It returns positions and numbers only; callers fetch geometry and
//   geometry-owned keep-outs (e.g. mcc_side_bolt_keepout()) from those providers themselves.
//   `use`d by lib/mcc/mcc.scad and by every L2 geometry file.
// Includes:
//   include <mcc/mcc.scad>
//////////////////////////////////////////////////////////////////////

include <BOSL2/std.scad>
include <constants.scad>
use <util.scad>
use <ports.scad>

// -----------------------------------------------------------------------------------------
// Section: End zones (layout-patch-wall.md §4)
// -----------------------------------------------------------------------------------------

// Function: mcc_end_zone()
// Usage:
//   ez = mcc_end_zone(dev, end);
// Description:
//   The X-gap end zone between the device's `end` face and the inner face of that end wall, mm.
//   `end` is "neg" (device face [-1,0,0]) or "pos" (device face [1,0,0]). Per D-12
//   (architecture.md §6 reservation rule, layout-patch-wall.md §4): the reserved PoE-splitter
//   bay's on-edge X extent is ALWAYS added on the "neg" end — the reservation rule is unconditional,
//   so `cfg`'s "splitter" flag is never consulted here, only whether a real port on that end needs
//   more than MCC_END_ZONE_MIN.
// Arguments:
//   dev = device record.
//   end = "neg" or "pos".
function mcc_end_zone(dev, end) =
    assert(end == "neg" || end == "pos",
        str("mcc: mcc_end_zone end must be \"neg\" or \"pos\", got \"", end, "\""))
    let(
        face = (end == "neg") ? [-1, 0, 0] : [1, 0, 0],
        on_end = mcc_ports_on_face(dev, face),
        ext_on_end = [for (p = on_end) if (mcc_port_panel(p) != "none") p],
        allows = [for (p = ext_on_end) mcc_dev_side_allow(mcc_port_kind(p))],
        ez_cable = max(concat([MCC_END_ZONE_MIN], allows))
    )
    ez_cable + (end == "neg" ? MCC_END_ZONE_NEG_EXTRA_SPLITTER : 0);

// -----------------------------------------------------------------------------------------
// Section: Slot assignment (layout-patch-wall.md §3)
// -----------------------------------------------------------------------------------------

// Function: mcc_slot_assignment()
// Usage:
//   slots = mcc_slot_assignment(dev);
// Description:
//   layout-patch-wall.md §3 steps 1-6, applied mechanically to `dev`'s actual port faces/positions
//   — NEVER a hardcoded per-SKU table (rev 5 §15 ruling 8: the doc's own worked-results table was
//   wrong on 6 of 8 rows; only the algorithm is normative). Partitions the external ports by the
//   sign of `face.x` ("block A" = the case's -X end, "block B" = +X end — this is the case-frame
//   sign, NOT Magewell's "Face A/B", see §3's naming warning), orders each block descending by
//   [mcc_bend_envelope, mcc_plug_len] (stiffest cable outermost), ties broken by `pos[0]` ascending
//   (a bit-identical [bend,plug_len,pos_x] key cannot occur between two distinct real ports in this
//   repo's device data, since pos_x always differs within a block — so no further id tie-break is
//   implemented; a future device file that violates this fails loudly via BOSL2 sort()'s own stable
//   ordering rather than silently). Unfilled slots (only possible if a caller pads n_slots) get
//   "DBA-BL-B", and are always the innermost slots by construction (block A/B fill from the outside
//   in).
// Returns:
//   A list of `n_slots` structs `[["slot",i], ["port_id",id_or_undef], ["part",part]]`, i = 1..n_slots.
function mcc_slot_assignment(dev) =
    let(
        ext = mcc_ports_external(dev),
        n_slots = len(ext)
    )
    assert(n_slots >= 1 && n_slots <= MCC_SLOTS_MAX,
        str("mcc: mcc_slot_assignment T1-02 n_slots=", n_slots, " out of range [1,", MCC_SLOTS_MAX, "] on \"", mcc_dev_slug(dev), "\""))
    let(
        _face_check = [for (p = ext)
            assert(mcc_port_face(p) == [-1, 0, 0] || mcc_port_face(p) == [1, 0, 0],
                str("mcc: mcc_slot_assignment T1-01 port \"", mcc_port_id(p), "\" on \"", mcc_dev_slug(dev),
                    "\" has face ", mcc_port_face(p), " — side-exit topology requires [-1,0,0] or [1,0,0]"))
            0],
        // Decorate each external port, BY INDEX into `ext` (not by embedding the port struct
        // itself), as a homogeneous numeric 4-vector [-bend, -plug_len, pos_x, idx] so BOSL2's
        // sort(list, idx=[0,1,2]) can do a fast, correct lexicographic sort on the first three
        // columns without ever comparing heterogeneous struct data.
        decorated = [for (i = [0:1:n_slots - 1])
            let(p = ext[i], panel = mcc_port_panel(p))
            [-mcc_bend_envelope(panel), -mcc_plug_len(panel), mcc_port_pos(p)[0], i]],
        blockA = [for (d = decorated) if (mcc_port_face(ext[d[3]])[0] < 0) d],
        blockB = [for (d = decorated) if (mcc_port_face(ext[d[3]])[0] > 0) d],
        _partition_check = assert(len(blockA) + len(blockB) == n_slots,
            str("mcc: mcc_slot_assignment internal error — block partition on \"", mcc_dev_slug(dev),
                "\" lost/duplicated a port (every external port's face.x must be nonzero, per T1-01)")),
        sortedA = len(blockA) > 0 ? sort(blockA, idx = [0, 1, 2]) : [],
        sortedB = len(blockB) > 0 ? sort(blockB, idx = [0, 1, 2]) : [],
        // Block A fills slots 1..len(A), highest rank (index 0 of the sort) -> slot 1.
        slotsA = [for (i = [0:1:len(sortedA) - 1])
            let(p = ext[sortedA[i][3]])
            [["slot", i + 1], ["port_id", mcc_port_id(p)], ["part", mcc_port_panel(p)]]],
        // Block B fills slots n_slots-len(B)+1..n_slots, highest rank -> slot n_slots.
        slotsB = [for (i = [0:1:len(sortedB) - 1])
            let(p = ext[sortedB[i][3]])
            [["slot", n_slots - i], ["port_id", mcc_port_id(p)], ["part", mcc_port_panel(p)]]],
        filled = concat(slotsA, slotsB),
        result = [for (i = [1:1:n_slots])
            let(match = [for (s = filled) if (struct_val(s, "slot") == i) s])
            (len(match) == 1) ? match[0] : [["slot", i], ["port_id", undef], ["part", "DBA-BL-B"]]]
    )
    assert(len(result) == n_slots,
        str("mcc: mcc_slot_assignment T1-03/T1-04 internal error on \"", mcc_dev_slug(dev), "\""))
    result;

// Function: mcc_slot_for_port()
// Usage:
//   slot = mcc_slot_for_port(dev, id);
// Description:
//   The 1-based slot index for external port `id` on `dev`. Asserts exactly one match.
function mcc_slot_for_port(dev, id) =
    let(matches = [for (s = mcc_slot_assignment(dev)) if (struct_val(s, "port_id") == id) s])
    assert(len(matches) == 1,
        str("mcc: mcc_slot_for_port() port id \"", id, "\" not found among the external ports of \"",
            mcc_dev_slug(dev), "\""))
    struct_val(matches[0], "slot");

// -----------------------------------------------------------------------------------------
// Section: Patch-wall aperture window (layout-patch-wall.md §2.5/§11 rev 6, §15 ruling
// 2026-09-08b -- deviation D9, retires the rev-5 hull()ed "crown")
// -----------------------------------------------------------------------------------------

// Function: mcc_aperture_window()
// Usage:
//   d_win = mcc_aperture_window(part);
// Description:
//   The body window through the patch wall BEHIND the flange seat for panel part `part` (D36: the
//   connector sits in the wall itself — mcc_neutrik_d_wall_cut()): a plain round opening a little
//   larger than the seat hole (architecture.md §5 rev 15, D40 — perfectly round, no teardrop, user
//   decision 2026-09-28). Returns d_win = mcc_cutout_d(part) + 2*MCC_CLR_SLIDE, or 0 for a
//   genuinely solid blank (mcc_panel_hole_d(part) == 0; none today — DBA-BL-B carries a full hole,
//   D18). Simplified from a 3-element [d_win, cap_h, w_flat] list (rev 14/D36) now that there is no
//   teardrop cap to describe.
// Arguments:
//   part = panel part number, key into MCC_PANEL_PARTS (constants.scad).
function mcc_aperture_window(part) =
    mcc_panel_hole_d(part) == 0 ? 0 : mcc_cutout_d(part) + 2 * MCC_CLR_SLIDE;

// -----------------------------------------------------------------------------------------
// Section: Cradle deck (layout-patch-wall.md §1)
// -----------------------------------------------------------------------------------------

// Function: mcc_cradle_deck()
// Usage:
//   deck = mcc_cradle_deck(dev);
// Description:
//   Cradle deck height (interior floor to device underside), mm — family-dependent (varies with
//   `dev`'s own height), so it is a FUNCTION, never a flat MCC_CRADLE_DECK constant. Derived so the
//   device's end-face port centreline lands exactly on the connector centreline
//   (MCC_SIDE_BOLT_AXIS_Z, which doubles as z_conn_c — constants.scad). layout-patch-wall.md §1
//   "MCC_CRADLE_DECK = z_dev_lo - MCC_FLOOR_T = z_conn_c - dev_h/2 - MCC_FLOOR_T".
function mcc_cradle_deck(dev) =
    MCC_SIDE_BOLT_AXIS_Z - mcc_dev_size(dev)[2] / 2 - MCC_FLOOR_T;

// -----------------------------------------------------------------------------------------
// Section: Nearest-to-zero tie-break helper (layout-patch-wall.md §6)
// -----------------------------------------------------------------------------------------

// Function: _mcc_nearest_zero()
// Description:
//   Private helper. Among `vals`, returns the one nearest zero; on an exact |value| tie, returns
//   the smaller (more negative) one — layout-patch-wall.md §6's own tie-break rule ("if two tie ...
//   pick the -X one"), which OpenSCAD's plain min() already implements for a symmetric +-a pair.
function _mcc_nearest_zero(vals) =
    let(
        abs_vals = [for (v = vals) abs(v)],
        min_abs = min(abs_vals),
        candidates = [for (v = vals) if (abs(v) - min_abs < MCC_EPS) v]
    )
    min(candidates);

// -----------------------------------------------------------------------------------------
// Section: Floor keep-out (layout-patch-wall.md §7.1 floor table, rev-5 corrections 1-4)
// -----------------------------------------------------------------------------------------

// Function: mcc_floor_keepout()
// Usage:
//   features = mcc_floor_keepout(dev, cfg);
// Description:
//   Pure function: every floor-plan feature `mounts.scad` places (the mount rail -- D-15, rev 9,
//   replaces VESA; widened by D44 -- and the side-bolt support-web footprint; the strap slots and
//   stacking recesses were removed by D87.1), each `[cx, cy, "circle"|"rect", size_or_d, "label"]`.
//   NOT nullary (rev-5 correction 2, layout-patch-wall.md §7.1) — the rail and the side-bolt web
//   depend on `L`, `W`, and `x_bolt`. `mounts.scad` draws the real geometry from this list and asserts pairwise
//   non-overlap (MCC_FLOOR_FEATURE_MIN_SEP, or r1+r2+2.0 where larger — D16, rev 9) — this function
//   only computes positions, per this file's "functions only" contract (ruling 1); it does not itself
//   assert (the assert belongs to the L2 caller that owns the floor, architecture.md §6). The case
//   1/4"-20 insert and the Magewell-Fishtail M4 band are no longer reserved (D44: the wide rail covers
//   the floor centre; the opt-in insert is guarded by T1-63 in cradle.scad). Rev 9: `layout.scad` must
//   NOT `use <rail.scad>` (architecture.md §3) — the "mount_rail" row below is built from the MCC_RAIL_*
//   L0 constants only.
// Arguments:
//   dev = device record.
//   cfg = variant-config assoc-list (only used indirectly via mcc_case_layout()).
function mcc_floor_keepout(dev, cfg) =
    let(
        l = mcc_case_layout(dev, cfg),
        L = struct_val(l, "L"), W = struct_val(l, "W"),
        side_bolt_x = struct_val(l, "side_bolt_x"),
        // Side-bolt support-web floor footprint (rev-5 correction J): 3 x 14 mm rectangle at
        // x=x_bolt, from the far wall's inner face inward (y in [-W/2+MCC_WALL, -W/2+MCC_WALL+
        // MCC_GAP_FAR-MCC_SIDE_BOLT_PAD_T]) -- registered here so nothing else overlaps it.
        web_y0 = -W / 2 + MCC_WALL,
        web_len = MCC_GAP_FAR - MCC_SIDE_BOLT_PAD_T,
        web_cy = web_y0 + web_len / 2
    )
    [
        // Mount rail (D-15, rev 9 — replaces VESA): MCC_RAIL_Y is already negative (R2/R24,
        // layout-patch-wall.md §17.2) — under the cradle deck and the device, not free-standing in
        // the connector bay. Size is the groove CUT's footprint [MCC_RAIL_LEN, MCC_RAIL_ROOT_W] (the
        // wider of the groove's two widths, so the keep-out covers the whole cut, not just the
        // mouth). The sill's MCC_RAIL_SILL_SIDE_W side walls (D30) are interior-only solid material
        // with no cut of their own, so they need no floor keep-out.
        // D34: the groove runs from its closed end at -MCC_RAIL_LEN/2 out through the +X wall.
        [(L / 2 - MCC_RAIL_LEN / 2) / 2, MCC_RAIL_Y, "rect", [L / 2 + MCC_RAIL_LEN / 2, MCC_RAIL_ROOT_W], "mount_rail"],
        [side_bolt_x, web_cy, "rect", [MCC_SIDE_BOLT_SUPPORT_WEB_T, web_len], "side_bolt_web"],
    ];

// -----------------------------------------------------------------------------------------
// Section: The case layout — the ONE real computation (layout-patch-wall.md §1-§8)
// -----------------------------------------------------------------------------------------

// Function: mcc_case_layout()
// Usage:
//   l = mcc_case_layout(dev, cfg);
// Description:
//   Computes every envelope/placement/slot/end-zone/bay/fastener figure in
//   .claude/knowledge/layout-patch-wall.md §1-§8 for `dev` under variant config `cfg`, as a single
//   struct. `cfg` is the assoc-list from case.scad — only its optional "fan_y" key is currently
//   consulted (fan/splitter RESERVATION is unconditional per D-12/architecture.md §6, so
//   "fan"/"splitter" flags never change any number here — only whether shell.scad/vents.scad draw
//   the live cutout).
//   Carries no dependency on any L1 geometry provider (ruling 1) — it returns `side_bolt_x`/
//   `side_bolt_z` (the bolt AXIS position) but NOT a keep-out shape; callers fetch
//   mcc_side_bolt_keepout() from fasteners.scad themselves and translate it to this position.
// Arguments:
//   dev = device record.
//   cfg = variant-config assoc-list, e.g. [["fan",false],["splitter",false]]. NOT
//         "external_ports": that key is INERT/DROPPED (D12, architecture.md §13) — the slot set
//         comes solely from mcc_ports_external(dev). Pass [] where only dev-driven fields are
//         needed (they are the vast majority).
function mcc_case_layout(dev, cfg) =
    let(
        dev_size = mcc_dev_size(dev),
        dev_l = dev_size[0], dev_w = dev_size[1], dev_h = dev_size[2],

        ez_neg = mcc_end_zone(dev, "neg"),
        ez_pos = mcc_end_zone(dev, "pos"),

        ext = mcc_ports_external(dev),
        n_slots = len(ext),
        bay_depths = [for (p = ext) mcc_bay_depth(mcc_port_panel(p))],
        bend_envs  = [for (p = ext) mcc_bend_envelope(mcc_port_panel(p))],
        max_bay_depth = max(bay_depths),
        d_bay_free = max_bay_depth - (MCC_WALL + MCC_PANEL_SEAT_T),

        L = 2 * MCC_WALL + ez_neg + dev_l + ez_pos,
        W = MCC_T_PATCH + d_bay_free + MCC_GAP_DEV + dev_w + MCC_GAP_FAR + MCC_WALL,
        H_int = MCC_PANEL_BAND + MCC_PLATE_H + MCC_PANEL_BAND,
        H = MCC_FLOOR_T + H_int + MCC_LID_T,

        deck = mcc_cradle_deck(dev),

        x_dev_lo = -L / 2 + MCC_WALL + ez_neg,
        x_dev_c  = x_dev_lo + dev_l / 2,
        x_dev_hi = x_dev_lo + dev_l,

        y_dev_lo = -W / 2 + MCC_WALL + MCC_GAP_FAR,
        y_dev_c  = y_dev_lo + dev_w / 2,
        y_dev_hi = y_dev_lo + dev_w,

        z_dev_lo = MCC_FLOOR_T + deck,
        z_dev_hi = z_dev_lo + dev_h,
        z_conn_c = MCC_SIDE_BOLT_AXIS_Z,

        plate_l = L - 2 * MCC_WALL - 2 * MCC_PANEL_FRAME_MIN,
        plate_size = [plate_l, MCC_PLATE_H], // D36: the connector RECESS footprint (no plate any more)

        span  = plate_l - MCC_D_FLANGE[0] - 2 * MCC_PLATE_END_PAD,
        pitch = (n_slots > 1) ? span / (n_slots - 1) : 0,
        slot_x = [for (i = [0:1:n_slots - 1]) (n_slots > 1) ? (-span / 2 + i * pitch) : 0],

        // Patch-wall connector openings (D36; round since D40). T1-34c: every round window stays
        // inside the connector recess with MCC_APERTURE_LIP_WEB_MIN of wall left above it. (T1-34b/d
        // — plate boss reliefs and plate-fixing bores — went with the plate.)
        slots_assigned = mcc_slot_assignment(dev),
        apertures = [for (i = [0:1:n_slots - 1]) mcc_aperture_window(struct_val(slots_assigned[i], "part"))],
        _t134c_check = [for (i = [0:1:n_slots - 1])
            assert(apertures[i] / 2 + MCC_APERTURE_LIP_WEB_MIN <= MCC_PLATE_H / 2 + MCC_EPS,
                str("mcc: T1-34c aperture containment fails for slot ", i + 1, " on \"", mcc_dev_slug(dev), "\""))
            0],

        // Fan bay, +X end wall. fan_y is a shell parameter, default y_dev_c (R20).
        fan_y_cfg = struct_val(cfg, "fan_y"),
        fan_y = is_undef(fan_y_cfg) ? y_dev_c : fan_y_cfg,
        fan_pos = [L / 2, fan_y, z_conn_c],

        // Fan bay reserved world AABB (architecture.md §6 reservation rule, §13 D23, issue #36).
        // THIS IS THE RESERVATION OF RECORD -- mcc_fan_envelope() (fan.scad) is only its %-ghost.
        // Reads MCC_FANS/MCC_FAN_INTAKE_CLR directly (L0): this file may never `use` fan.scad, an
        // L1 geometry provider (§3). fan_bay_x is the SAME quantity shell.scad's T1-18(c) checks
        // against -- it reads it from this struct, it does not recompute it.
        // AXIS MAPPING (do not swap): the bay is the fan frame seen through the +X end wall, i.e.
        // through rotate([0,-90,0]) -- fan-local X -> world +Z, fan-local Y -> world Y, fan-local
        // +Z (frame depth + intake) -> world -X, inward from the wall's inner face.
        fan_frame = struct_val(mcc_fan_spec(MCC_FAN_DEFAULT), "frame"),
        fan_bay_depth = fan_frame[2] + MCC_FAN_INTAKE_CLR,
        fan_bay_x = [L / 2 - MCC_WALL - fan_bay_depth, L / 2 - MCC_WALL],
        fan_bay_y = [fan_y - fan_frame[1] / 2, fan_y + fan_frame[1] / 2],
        fan_bay_z = [z_conn_c - fan_frame[0] / 2, z_conn_c + fan_frame[0] / 2],

        // PoE-splitter bay, -X end, on edge (env[2]->X, env[0]->Y, env[1]->Z).
        splitter_ind = search([MCC_SPLITTER_DEFAULT], MCC_SPLITTERS)[0],
        splitter_env = struct_val(MCC_SPLITTERS[splitter_ind][1], "size"),
        splitter_bay_x = [-L / 2 + MCC_WALL, -L / 2 + MCC_WALL + splitter_env[2]],
        splitter_bay_y = [-W / 2 + MCC_WALL, -W / 2 + MCC_WALL + splitter_env[0]],
        splitter_bay_z = [MCC_FLOOR_T, MCC_FLOOR_T + splitter_env[1]],

        // Side-bolt axis (D-09; §7.1). Axis only — no keep-out shape (ruling 1).
        side_bolt_port = mcc_port_by_id(dev, "side_bolt"),
        sb_pos = mcc_port_pos(side_bolt_port),
        side_bolt_x = x_dev_c + sb_pos[0],
        side_bolt_z = z_conn_c + sb_pos[1],

        // Lid fasteners (§6, D-04 accepted).
        n_fast = (L > MCC_LID_SPAN_MAX) ? 6 : 4,
        e = MCC_FASTENER_INSET,
        corners = [
            [ (L / 2 - e),  (W / 2 - e)],
            [ (L / 2 - e), -(W / 2 - e)],
            [-(L / 2 - e),  (W / 2 - e)],
            [-(L / 2 - e), -(W / 2 - e)],
        ],
        // Patch-wall mid fastener: widest inter-slot gap centre nearest x=0, if it clears every
        // flange edge by >= MCC_LID_FASTENER_CLR_MIN.
        gap_candidates_all = (n_slots > 1) ? [for (i = [0:1:n_slots - 2]) (slot_x[i] + slot_x[i + 1]) / 2] : [],
        gap_clearance = (n_slots > 1) ? pitch / 2 - MCC_D_FLANGE[0] / 2 : 0,
        gap_candidates = (n_fast == 6 && gap_clearance >= MCC_LID_FASTENER_CLR_MIN) ? gap_candidates_all : [],
        x_gap = (len(gap_candidates) > 0) ? _mcc_nearest_zero(gap_candidates) : undef,
        // Far-wall mid fastener: candidates x_bolt +- (side-bolt keepout radius + lid-boss radius),
        // the tangent-clearance separation (layout-patch-wall.md §6 "required separation 16.14"),
        // whichever is legal (inside the fastener ring) and nearest x=0.
        boss_od_lid = MCC_BOSS_MIN_RATIO * struct_val(MCC_INSERT_M3, "od"),
        far_sep = MCC_SIDE_BOLT_KEEPOUT_D / 2 + boss_od_lid / 2,
        far_candidates = (n_fast == 6) ? [side_bolt_x - far_sep, side_bolt_x + far_sep] : [],
        far_legal = [for (c = far_candidates) if (abs(c) <= L / 2 - e - boss_od_lid / 2) c],
        x_far_mid = (len(far_legal) > 0) ? _mcc_nearest_zero(far_legal) : undef,
        lid_fastener_pos = (n_fast == 4) ? corners : concat(
            corners,
            (!is_undef(x_gap)) ? [[x_gap, W / 2 - e]] : [],
            (!is_undef(x_far_mid)) ? [[x_far_mid, -(W / 2 - e)]] : []
        ),

        // Fan switch (rev 11, #32, D-18): band-solved between the fan reservation and the
        // (+X,-Y) corner lid-fastener's two obstructions -- its gusset strip near the wall (the
        // "pad" band) and its boss deeper in (the "body" band) -- layout-patch-wall.md §5 "Fan
        // switch". Reads MCC_SWITCHES/mcc_fan_spec() directly, NEVER switch.scad (this file may
        // not import an L1 geometry provider, architecture.md §3) -- mirrors how
        // mcc_floor_keepout()'s "mount_rail" row is built from MCC_RAIL_* constants rather than
        // mcc_rail_sill_size() (rev 9 precedent).
        // "fan_switch" enablement, duplicated inline (NOT via switch.scad's mcc_fan_switch_enabled
        // -- same §3 ban) so compact SKUs that set ["fan_switch",false] never trip T1-43 below.
        sw_enabled = let(v = struct_val(cfg, "fan_switch")) is_undef(v) ? struct_val(cfg, "fan") : v,
        sw_spec = mcc_switch_spec(MCC_SWITCH_DEFAULT),
        sw_clr = struct_val(sw_spec, "clr"),
        sw_pad_d = struct_val(sw_spec, "pad_d"),
        sw_body_d = struct_val(sw_spec, "body_d"),
        fan_frame_sw = struct_val(mcc_fan_spec(MCC_FAN_DEFAULT), "frame"),
        // (+X,-Y) corner lid-fastener boss/gusset centre Y -- same corner `corners[1]` above.
        corner_y = -(W / 2 - e),
        gusset_edge = corner_y + MCC_WALL / 2,  // gusset strip's near (toward-fan) edge
        boss_edge   = corner_y + boss_od_lid / 2, // corner boss's near (toward-fan) edge
        switch_y_hi = fan_y - fan_frame_sw[1] / 2 - sw_clr - sw_pad_d / 2,          // fan side
        switch_y_lo = max(gusset_edge + sw_clr + sw_pad_d / 2,                     // pad vs gusset
                          boss_edge   + sw_clr + sw_body_d / 2),                   // body vs boss
        switch_y = (switch_y_lo + switch_y_hi) / 2,
        switch_pos = [L / 2, switch_y, z_conn_c], // X = the wall's OUTER face, matches fan_pos

        vent_intake_z = [5, 5 + MCC_VENT_INTAKE_BAND_H],
        vent_exhaust_z = MCC_VENT_EXHAUST_Z
    )
    // --- Tier-1 asserts (layout-patch-wall.md §9), the ones checkable from pure numbers ---
    assert(pitch == 0 || pitch >= MCC_D_PITCH_H,
        str("mcc: T1-06 pitch=", pitch, " < MCC_D_PITCH_H=", MCC_D_PITCH_H, " on \"", mcc_dev_slug(dev), "\""))
    assert(d_bay_free >= max_bay_depth - (MCC_WALL + MCC_PANEL_SEAT_T) - MCC_EPS,
        str("mcc: T1-07 d_bay_free=", d_bay_free, " below the required bay depth on \"", mcc_dev_slug(dev), "\""))
    assert(d_bay_free >= max(concat([0], bend_envs)),
        str("mcc: T1-08 d_bay_free=", d_bay_free, " below the max lateral bend envelope ", max(concat([0], bend_envs)),
            " on \"", mcc_dev_slug(dev), "\""))
    assert(ez_neg >= MCC_END_ZONE_NEG_EXTRA_SPLITTER,
        str("mcc: T1-09 ez_neg=", ez_neg, " does not include the reserved-bay term on \"", mcc_dev_slug(dev), "\""))
    assert(plate_l <= L - 2 * MCC_WALL - 2 * MCC_PANEL_FRAME_MIN + MCC_EPS,
        str("mcc: T1-10 plate_l=", plate_l, " exceeds the available frame on \"", mcc_dev_slug(dev), "\""))
    assert(MCC_PLATE_H >= 2 * (MCC_D_SCREW_PITCH[1] / 2 + boss_od_lid / 2 + 2.0) - MCC_EPS,
        str("mcc: T1-11 MCC_PLATE_H=", MCC_PLATE_H, " below the rear-boss minimum"))
    assert(H_int >= deck + dev_h + MCC_LID_CLEAR,
        str("mcc: T1-14 H_int=", H_int, " below deck+dev_h+MCC_LID_CLEAR=", deck + dev_h + MCC_LID_CLEAR,
            " on \"", mcc_dev_slug(dev), "\""))
    assert(H_int >= MCC_FAN_APERTURE_D + 2 * MCC_WALL,
        str("mcc: T1-15 H_int=", H_int, " below the fan-aperture minimum on \"", mcc_dev_slug(dev), "\""))
    assert(mcc_bbox_ok([L, W, MCC_WALL]),
        str("mcc: T1-21 case footprint ", [L, W], " exceeds the printable envelope on \"", mcc_dev_slug(dev), "\""))
    assert(splitter_bay_x[1] <= x_dev_lo + MCC_EPS,
        str("mcc: T1-28 splitter bay ", splitter_bay_x, " intrudes into the device's own -X cable envelope on \"",
            mcc_dev_slug(dev), "\""))
    // T1-43 (layout-patch-wall.md §9/§18, rev 11, #32): the fan switch has somewhere to go. Only
    // evaluated when the switch is actually enabled for this cfg -- the compact family's feasible
    // interval is empty by construction (D-18), and every compact SKU is required to set
    // ["fan_switch", false] explicitly (verdict B6) rather than trip this assert.
    assert(!sw_enabled || switch_y_hi >= switch_y_lo - MCC_EPS,
        str("mcc: T1-43 fan switch has nowhere to go on \"", mcc_dev_slug(dev), "\" (switch_y_hi=",
            switch_y_hi, " < switch_y_lo=", switch_y_lo, ") -- set [\"fan_switch\", false] for this SKU ",
            "(layout-patch-wall.md §5, D-18)"))
    // T1-46a-d: the fan bay's Y/Z footprint (architecture.md §6/§13 D23, layout-patch-wall.md
    // §5/§9, issue #36). Evaluated UNCONDITIONALLY, like T1-18(c) -- §6 reserves the bay even when
    // cfg.fan == false. All four pass by construction today (compact slack: 12.96 / 10.10 / 2.50 /
    // 2.50 mm), so they are regression guards against a future change to fan_y, MCC_FANS,
    // MCC_T_PATCH or the lid-fastener ring -- not fixes to a live failure.
    assert(fan_bay_y[0] >= corners[1][1] + max(MCC_WALL / 2, boss_od_lid / 2) + MCC_FAN_BAY_CLR - MCC_EPS,
        str("mcc: T1-46a fan bay -Y edge ", fan_bay_y[0], " is within MCC_FAN_BAY_CLR=", MCC_FAN_BAY_CLR,
            " of the (+X,-Y) corner lid-fastener boss/gusset at y=", corners[1][1], " on \"",
            mcc_dev_slug(dev), "\""))
    assert(fan_bay_y[1] <= W / 2 - MCC_T_PATCH - d_bay_free - MCC_FAN_BAY_CLR + MCC_EPS,
        str("mcc: T1-46b fan bay +Y edge ", fan_bay_y[1], " is within MCC_FAN_BAY_CLR=", MCC_FAN_BAY_CLR,
            " of the connector bay's plug envelope at y=", W / 2 - MCC_T_PATCH - d_bay_free, " on \"",
            mcc_dev_slug(dev), "\""))
    assert(fan_bay_z[0] >= MCC_FLOOR_T - MCC_EPS,
        str("mcc: T1-46c fan bay bottom ", fan_bay_z[0], " is below the interior floor on \"",
            mcc_dev_slug(dev), "\""))
    assert(fan_bay_z[1] <= MCC_FLOOR_T + H_int + MCC_EPS,
        str("mcc: T1-46d fan bay top ", fan_bay_z[1], " is above the interior ceiling on \"",
            mcc_dev_slug(dev), "\""))
    [
        ["L", L], ["W", W], ["H", H], ["H_int", H_int],
        ["ez_neg", ez_neg], ["ez_pos", ez_pos],
        ["x_dev_lo", x_dev_lo], ["x_dev_c", x_dev_c], ["x_dev_hi", x_dev_hi],
        ["y_dev_lo", y_dev_lo], ["y_dev_c", y_dev_c], ["y_dev_hi", y_dev_hi],
        ["z_dev_lo", z_dev_lo], ["z_dev_hi", z_dev_hi], ["z_conn_c", z_conn_c],
        ["plate_l", plate_l], ["plate_size", plate_size],
        ["n_slots", n_slots], ["pitch", pitch], ["slot_x", slot_x],
        ["d_bay_free", d_bay_free],
        ["fan_pos", fan_pos], ["fan_y", fan_y],
        ["fan_bay_x", fan_bay_x], ["fan_bay_y", fan_bay_y], ["fan_bay_z", fan_bay_z],
        ["switch_pos", switch_pos],
        ["splitter_bay_x", splitter_bay_x], ["splitter_bay_y", splitter_bay_y], ["splitter_bay_z", splitter_bay_z],
        ["side_bolt_x", side_bolt_x], ["side_bolt_z", side_bolt_z],
        ["lid_n_fast", n_fast], ["lid_fastener_pos", lid_fastener_pos],
        ["vent_intake_z", vent_intake_z], ["vent_exhaust_z", vent_exhaust_z],
    ];

// Function: mcc_case_dims()
// Usage:
//   dims = mcc_case_dims(dev, cfg);
// Description:
//   [L, W, H] for `dev` under `cfg` — the thin accessor case.scad's echo() and mcc_shell_*() use.
function mcc_case_dims(dev, cfg) =
    let(l = mcc_case_layout(dev, cfg))
    [struct_val(l, "L"), struct_val(l, "W"), struct_val(l, "H")];

// vim: expandtab tabstop=4 shiftwidth=4 softtabstop=4 nowrap
