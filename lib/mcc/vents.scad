//////////////////////////////////////////////////////////////////////
// LibFile: mcc/vents.scad
//   L2. Chimney vent-slot arrays on the far (-Y) wall (intake low + exhaust high) and the -X end
//   wall (intake low, +Y half only — the reserved splitter bay masks -Y), plus the +X end wall's
//   fan aperture (only when a fan is enabled — the bay itself is always reserved as keep-out
//   volume, per architecture.md §6, whether or not it is vented). NEVER the patch wall (T1-19).
//   .claude/knowledge/layout-patch-wall.md §5. `use`d only by lib/mcc/shell.scad (the L2
//   composition root) — never by cradle.scad/mounts.scad/panel.scad, which must not `use` each
//   other.
// Includes:
//   include <mcc/mcc.scad>
//////////////////////////////////////////////////////////////////////

include <BOSL2/std.scad>
include <constants.scad>
use <util.scad>
use <ports.scad>     // mcc_dev_slug() (assert messages) -- D20, layout-patch-wall.md §17.4 R9:
                     // `use` is not transitive, mcc_dev_slug() is not reachable through
                     // `use <layout.scad>` alone. mounts.scad:21 carries the identical fix/comment.
use <layout.scad>
use <fan.scad>       // mcc_fan_cutout()
use <fasteners.scad> // mcc_side_bolt_keepout()

// Function: _mcc_in_any_range()
// Description:
//   Private. True if [lo,hi] overlaps any [lo,hi] pair in `ranges`.
function _mcc_in_any_range(lo, hi, ranges) =
    len([for (r = ranges) if (hi > r[0] && lo < r[1]) r]) > 0;

// Function: _mcc_vent_slot_centers()
// Description:
//   Private. Slot centre positions tiling [run_lo, run_hi] at `slot_w`/`web_w` pitch (default
//   MCC_VENT_SLOT_W/MCC_VENT_WEB_W, the wall-vent figures — every existing call site keeps calling
//   this positionally with 3 args and picks up those same defaults unchanged), centred in the run,
//   with any slot whose own [c-w/2, c+w/2] footprint overlaps an entry in `excl_ranges` dropped
//   entirely (not narrowed) — layout-patch-wall.md §5's "no vent slot inside" rule (T1-23/T1-23b),
//   so the geometry drawn and the free-area count below always agree. Generalized (issue #24,
//   docs/plans/2026-09-09-lid-vents.md §3.2 step 1) so mcc_lid_vents_cut()/mcc_lid_vent_area() can
//   reuse it at the lid-vent slot/web widths without a second copy of the tiling maths.
// Arguments:
//   run_lo, run_hi = the run to tile, mm.
//   excl_ranges    = list of [lo,hi] exclusion ranges; a slot overlapping any is dropped.
//   slot_w         = slot width, mm. Default: MCC_VENT_SLOT_W.
//   web_w          = web width between slots, mm. Default: MCC_VENT_WEB_W.
function _mcc_vent_slot_centers(run_lo, run_hi, excl_ranges = [],
                                 slot_w = MCC_VENT_SLOT_W, web_w = MCC_VENT_WEB_W) =
    let(
        pitch = slot_w + web_w,
        run = run_hi - run_lo,
        n = floor((run + web_w) / pitch),
        used = n * pitch - web_w,
        start = run_lo + (run - used) / 2 + slot_w / 2,
        all = [for (i = [0:1:n - 1]) start + i * pitch]
    )
    [for (c = all) if (!_mcc_in_any_range(c - slot_w / 2, c + slot_w / 2, excl_ranges)) c];

// Module: mcc_vents()
// Usage:
//   mcc_vents(dev, cfg, face);
// Description:
//   SUBTRACTIVE. `face` selects which wall: [0,-1,0] (far wall — intake low over the device
//   length + exhaust high, +X half only, outboard of the side-bolt keep-out), [-1,0,0] (-X end
//   wall — intake low, +Y half only), [1,0,0] (+X end wall — the fan aperture only, when `cfg`'s
//   "fan" flag is true; solid otherwise — the bay stays reserved but unvented, architecture.md
//   §6). Never [0,1,0] (the patch wall) — T1-19, asserted.
// Arguments:
//   dev  = device record.
//   cfg  = variant-config assoc-list.
//   face = [0,-1,0] | [-1,0,0] | [1,0,0].
// Function: _mcc_far_wall_excl()
// Description:
//   Private. Shared exclusion geometry for the far wall, used identically by mcc_vents() and
//   mcc_vent_intake_area() so the two can never disagree. The side-bolt keep-out (T1-23) is NOT a
//   uniform-width exclusion band the way the far-wall mid-boss (T1-23b) is: `mcc_side_bolt_keepout()`
//   is a disc (radius `disc_d/2`, centred at the bolt axis z=z_bolt) UNION a narrower strip running
//   the full height down to the floor (layout-patch-wall.md §7.1). Modelling the disc's actual
//   circular taper is not worth the complexity here — instead the intake band is split at
//   `z = z_bolt - disc_d/2` (the disc's own lower edge) into a LOWER sub-band (below the disc
//   entirely — only the narrower strip applies) and an UPPER sub-band (within the disc's z-range —
//   the full disc diameter is excluded there, conservatively, since the disc is at its widest at
//   z=z_bolt and this repo's slots are full-height cuts through a single sub-band, not
//   z-varying). Returns [["lower",[z0,z1],excl_ranges], ["upper",[z0,z1],excl_ranges]] — either
//   entry's z-range may be empty ([a,a]) if the disc's z-range doesn't actually clip the intake
//   band (kept anyway so callers don't need special-case logic).
// Arguments:
//   l = mcc_case_layout() struct.
function _mcc_far_wall_excl(l) =
    let(
        x_bolt = struct_val(l, "side_bolt_x"),
        z_bolt = struct_val(l, "side_bolt_z"),
        intake_z = struct_val(l, "vent_intake_z"),
        ko = mcc_side_bolt_keepout(),
        sb_disc_d = struct_val(ko, "disc_d"),
        sb_strip_w = struct_val(ko, "strip_w"),
        disc_z0 = z_bolt - sb_disc_d / 2, // the disc's own lower edge (z_bolt=25.5, radius 12 -> 13.5)
        split_z = min(max(disc_z0, intake_z[0]), intake_z[1]),
        lower_z = [intake_z[0], split_z],
        upper_z = [split_z, intake_z[1]],
        strip_excl = [x_bolt - sb_strip_w / 2, x_bolt + sb_strip_w / 2],
        disc_excl  = [x_bolt - sb_disc_d / 2, x_bolt + sb_disc_d / 2],
        boss_od_lid = MCC_BOSS_MIN_RATIO * struct_val(MCC_INSERT_M3, "od"),
        mid_w = boss_od_lid + 2 * 2.0,
        x_far_mid = _mcc_lid_far_mid_x(l),
        mid_excl = is_undef(x_far_mid) ? [] : [[x_far_mid - mid_w / 2, x_far_mid + mid_w / 2]]
    )
    [
        ["lower", lower_z, concat([strip_excl], mid_excl)],
        ["upper", upper_z, concat([disc_excl], mid_excl)],
    ];

module mcc_vents(dev, cfg, face) {
    assert(face != [0, 1, 0],
        "mcc: T1-19 mcc_vents() must never be called for the patch wall face [0,1,0]");

    l = mcc_case_layout(dev, cfg);
    L = struct_val(l, "L"); W = struct_val(l, "W");
    x_dev_lo = struct_val(l, "x_dev_lo"); x_dev_hi = struct_val(l, "x_dev_hi");
    x_bolt = struct_val(l, "side_bolt_x");
    intake_z  = struct_val(l, "vent_intake_z");
    exhaust_z = struct_val(l, "vent_exhaust_z");
    fan_pos = struct_val(l, "fan_pos");
    sb_disc_d = struct_val(mcc_side_bolt_keepout(), "disc_d");
    x_far_mid = _mcc_lid_far_mid_x(l);
    boss_od_lid = MCC_BOSS_MIN_RATIO * struct_val(MCC_INSERT_M3, "od");
    mid_w = boss_od_lid + 2 * 2.0;
    mid_excl = is_undef(x_far_mid) ? [] : [[x_far_mid - mid_w / 2, x_far_mid + mid_w / 2]];

    if (face == [0, -1, 0]) {
        // --- Intake, low: full device X length, split into two Z sub-bands (see _mcc_far_wall_excl()) ---
        for (band = _mcc_far_wall_excl(l)) {
            bz = band[1]; excl = band[2];
            if (bz[1] > bz[0])
                for (c = _mcc_vent_slot_centers(x_dev_lo, x_dev_hi, excl))
                    translate([c - MCC_VENT_SLOT_W / 2, -W / 2 - MCC_EPS, bz[0]])
                        cube([MCC_VENT_SLOT_W, MCC_WALL + 2 * MCC_EPS, bz[1] - bz[0]]);
        }

        // --- Exhaust, high: +X half only, inner edge outboard of the side-bolt keep-out ---
        ex_lo = max(x_bolt + sb_disc_d / 2, x_dev_lo);
        if (x_dev_hi > ex_lo)
            for (c = _mcc_vent_slot_centers(ex_lo, x_dev_hi, mid_excl))
                translate([c - MCC_VENT_SLOT_W / 2, -W / 2 - MCC_EPS, exhaust_z[0]])
                    cube([MCC_VENT_SLOT_W, MCC_WALL + 2 * MCC_EPS, exhaust_z[1] - exhaust_z[0]]);

    } else if (face == [-1, 0, 0]) {
        // --- Intake, low, +Y half only (the reserved splitter bay masks -Y) ---
        run_hi = W / 2 - MCC_WALL;
        for (c = _mcc_vent_slot_centers(0, run_hi, []))
            translate([-L / 2 - MCC_EPS, c - MCC_VENT_SLOT_W / 2, intake_z[0]])
                cube([MCC_WALL + 2 * MCC_EPS, MCC_VENT_SLOT_W, intake_z[1] - intake_z[0]]);

    } else if (face == [1, 0, 0]) {
        fan_flag = struct_val(cfg, "fan");
        if (fan_flag == true) {
            // Local frame (mcc_fan_cutout(), fan.scad): wall spans local Z=[0,wall_t], hole
            // pattern centred at local (0,0). rotate([0,90,0]) maps local Z -> world X, local Y ->
            // world Y unchanged, local X -> world -Z; translate lands local Z=0 (wall inner face)
            // at world X=L/2-MCC_WALL and centres the pattern on (fan_pos[1], fan_pos[2]).
            translate([L / 2 - MCC_WALL, fan_pos[1], fan_pos[2]])
                rotate([0, 90, 0])
                    mcc_fan_cutout("NF-A4x10", wall_t = MCC_WALL, grille = true);
        }
    }
}

// Function: _mcc_lid_far_mid_x()
// Description:
//   Private. The far-wall mid-span lid-fastener X position, or undef when `n_fast==4` (no
//   far-wall mid fastener at all). Re-derives the same result mcc_case_layout()'s own
//   `lid_fastener_pos` list already contains (its 6th/last entry when `lid_n_fast==6`) — kept as a
//   tiny separate lookup here purely so this file doesn't have to pattern-match list positions.
function _mcc_lid_far_mid_x(l) =
    let(
        n_fast = struct_val(l, "lid_n_fast"),
        pos = struct_val(l, "lid_fastener_pos")
    )
    (n_fast == 6 && len(pos) == 6) ? pos[5][0] : undef;

// Function: mcc_vent_intake_area()
// Usage:
//   area = mcc_vent_intake_area(dev, cfg);
// Description:
//   T1-30: total NET intake free area (far wall + -X end wall low bands), mm^2 — computed from the
//   SAME slot-centre lists mcc_vents() actually draws (via _mcc_vent_slot_centers()), so the number
//   this asserts against can never disagree with the geometry cut. Each surviving slot contributes
//   MCC_VENT_SLOT_W * band height.
function mcc_vent_intake_area(dev, cfg) =
    let(
        l = mcc_case_layout(dev, cfg),
        W = struct_val(l, "W"),
        x_dev_lo = struct_val(l, "x_dev_lo"), x_dev_hi = struct_val(l, "x_dev_hi"),
        far_bands = _mcc_far_wall_excl(l),
        far_area = sum([for (band = far_bands)
            let(bz = band[1])
            (bz[1] > bz[0]) ? len(_mcc_vent_slot_centers(x_dev_lo, x_dev_hi, band[2])) * MCC_VENT_SLOT_W * (bz[1] - bz[0]) : 0]),
        negx_h = struct_val(l, "vent_intake_z")[1] - struct_val(l, "vent_intake_z")[0],
        n_negx = len(_mcc_vent_slot_centers(0, W / 2 - MCC_WALL, [])),
        negx_area = n_negx * MCC_VENT_SLOT_W * negx_h
    )
    far_area + negx_area;

// -----------------------------------------------------------------------------------------
// Section: Lid vents (GitHub issue #24) — additive top-exhaust field, centred over the device's
// own plenum. Called ONLY from mcc_shell_lid() (the floor stays closed — NEVER call
// mcc_lid_vents_cut() from mcc_shell_base()). docs/plans/2026-09-09-lid-vents.md,
// layout-patch-wall.md §17.4 (T1-36/T1-37).
// -----------------------------------------------------------------------------------------

// Function: _mcc_lid_vent_field()
// Description:
//   Private. The lid-vent field's own bounds and the side-bolt exclusion range, shared identically
//   by mcc_lid_vent_area() and mcc_lid_vents_cut() so the assert and the geometry can never
//   disagree (the same discipline _mcc_far_wall_excl() already carries for the wall vents).
// Arguments:
//   l = mcc_case_layout() struct.
function _mcc_lid_vent_field(l) =
    let(
        x_dev_lo = struct_val(l, "x_dev_lo"), x_dev_hi = struct_val(l, "x_dev_hi"),
        y_dev_c  = struct_val(l, "y_dev_c"),
        side_bolt_x = struct_val(l, "side_bolt_x"),
        sb_strip_w = struct_val(mcc_side_bolt_keepout(), "strip_w"),
        field_x_lo = x_dev_lo + MCC_LID_VENT_END_MARGIN,
        field_x_hi = x_dev_hi - MCC_LID_VENT_END_MARGIN,
        field_h = MCC_LID_VENT_ROWS * MCC_LID_VENT_SLOT_L
                + (MCC_LID_VENT_ROWS - 1) * MCC_LID_VENT_ROW_GAP,
        field_y_lo = y_dev_c - field_h / 2,
        field_y_hi = field_y_lo + field_h,
        excl = [[side_bolt_x - sb_strip_w / 2, side_bolt_x + sb_strip_w / 2]]
    )
    [["x_lo", field_x_lo], ["x_hi", field_x_hi], ["y_lo", field_y_lo], ["y_hi", field_y_hi],
     ["h", field_h], ["excl", excl]];

// Function: mcc_lid_vent_area()
// Usage:
//   area = mcc_lid_vent_area(dev, cfg);
// Description:
//   T1-36 (layout-patch-wall.md §9): total NET lid-vent free area, mm^2, over both rows, computed
//   from the SAME slot-centre list mcc_lid_vents_cut() draws (via _mcc_vent_slot_centers()), so the
//   assert and the geometry can never disagree.
// Arguments:
//   dev = device record.
//   cfg = variant-config assoc-list.
function mcc_lid_vent_area(dev, cfg) =
    let(
        l = mcc_case_layout(dev, cfg),
        f = _mcc_lid_vent_field(l),
        n_per_row = len(_mcc_vent_slot_centers(struct_val(f, "x_lo"), struct_val(f, "x_hi"),
            struct_val(f, "excl"), MCC_LID_VENT_SLOT_W, MCC_LID_VENT_WEB_W))
    )
    n_per_row * MCC_LID_VENT_ROWS * MCC_LID_VENT_SLOT_W * MCC_LID_VENT_SLOT_L;

// Module: mcc_lid_vents_cut()
// Usage:
//   mcc_lid_vents_cut(dev, cfg);
// Description:
//   SUBTRACTIVE. Cuts a 2-row field of vertical through-slots in the lid slab, centred over the
//   device's own footprint (over the plenum — docs/plans/2026-09-09-lid-vents.md §1.1), offset from
//   the far-wall/±X-end-wall chimney slots this file already cuts in mcc_vents(). Called ONLY from
//   mcc_shell_lid() (issue #24 — the floor stays closed; NEVER call this from mcc_shell_base()),
//   gated on cfg["lid_vents"] (default true, read once by the caller — this module does not
//   re-read the flag).
//   Asserts (layout-patch-wall.md §9):
//     T1-36 — net free area over both rows >= MCC_LID_VENT_AREA_RATIO * (pi/4) * MCC_FAN_APERTURE_D^2.
//     T1-37 — the field clears (a) the T&G groove band + patch-wall MCC_T_PATCH stack on all four
//             sides by >= MCC_LID_VENT_EDGE_MIN, and (b) every lid_fastener_pos inflated by
//             MCC_LID_VENT_FASTENER_KEEPOUT_R.
// Arguments:
//   dev = device record.
//   cfg = variant-config assoc-list.
module mcc_lid_vents_cut(dev, cfg) {
    l = mcc_case_layout(dev, cfg);
    L = struct_val(l, "L"); W = struct_val(l, "W"); H = struct_val(l, "H");
    lid_pos = struct_val(l, "lid_fastener_pos");
    z_top = H - MCC_LID_T;

    f = _mcc_lid_vent_field(l);
    field_x_lo = struct_val(f, "x_lo"); field_x_hi = struct_val(f, "x_hi");
    field_y_lo = struct_val(f, "y_lo"); field_y_hi = struct_val(f, "y_hi");
    field_h = struct_val(f, "h"); excl = struct_val(f, "excl");

    assert(field_x_hi > field_x_lo,
        str("mcc: lid vent field has non-positive X run on \"", mcc_dev_slug(dev), "\""));

    // T1-37(a) — clears the T&G groove band and the patch wall's MCC_T_PATCH stack on all four
    // sides by >= MCC_LID_VENT_EDGE_MIN. The -Y/±X walls carry MCC_WALL + the groove band
    // (MCC_TG_W + MCC_CLR_TG); the +Y (patch) wall additionally carries MCC_T_PATCH in place of
    // MCC_WALL.
    assert(field_x_lo >= -L / 2 + MCC_WALL + MCC_TG_W + MCC_CLR_TG + MCC_LID_VENT_EDGE_MIN
        && field_x_hi <= L / 2 - MCC_WALL - MCC_TG_W - MCC_CLR_TG - MCC_LID_VENT_EDGE_MIN,
        str("mcc: T1-37 lid vent field X-range ", [field_x_lo, field_x_hi],
            " intrudes on the T&G groove band on \"", mcc_dev_slug(dev), "\""));
    assert(field_y_lo >= -W / 2 + MCC_WALL + MCC_TG_W + MCC_CLR_TG + MCC_LID_VENT_EDGE_MIN
        && field_y_hi <= W / 2 - MCC_T_PATCH - MCC_TG_W - MCC_CLR_TG - MCC_LID_VENT_EDGE_MIN,
        str("mcc: T1-37 lid vent field Y-range ", [field_y_lo, field_y_hi],
            " intrudes on the T&G groove band or the patch wall on \"", mcc_dev_slug(dev), "\""));

    // T1-37(b) — every lid_fastener_pos clears the field, inflated by the keep-out radius.
    for (p = lid_pos)
        assert(p[0] < field_x_lo - MCC_LID_VENT_FASTENER_KEEPOUT_R
            || p[0] > field_x_hi + MCC_LID_VENT_FASTENER_KEEPOUT_R
            || p[1] < field_y_lo - MCC_LID_VENT_FASTENER_KEEPOUT_R
            || p[1] > field_y_hi + MCC_LID_VENT_FASTENER_KEEPOUT_R,
            str("mcc: T1-37 lid fastener ", p, " is inside the lid vent field keep-out on \"",
                mcc_dev_slug(dev), "\""));

    assert(MCC_LID_VENT_WEB_W >= MCC_LID_VENT_WEB_MIN,
        str("mcc: MCC_LID_VENT_WEB_W=", MCC_LID_VENT_WEB_W, " below the ", MCC_LID_VENT_WEB_MIN,
            " mm minimum web width"));

    // T1-36 — net free area over both rows vs. the same fan-aperture reference T1-30 uses.
    area = mcc_lid_vent_area(dev, cfg);
    area_min = MCC_LID_VENT_AREA_RATIO * PI / 4 * MCC_FAN_APERTURE_D * MCC_FAN_APERTURE_D;
    assert(area >= area_min,
        str("mcc: T1-36 lid vent net area ", area, " mm^2 below threshold ", area_min,
            " mm^2 on \"", mcc_dev_slug(dev), "\""));

    for (row = [0 : 1 : MCC_LID_VENT_ROWS - 1]) {
        y_lo = field_y_lo + row * (MCC_LID_VENT_SLOT_L + MCC_LID_VENT_ROW_GAP);
        for (c = _mcc_vent_slot_centers(field_x_lo, field_x_hi, excl,
                                         MCC_LID_VENT_SLOT_W, MCC_LID_VENT_WEB_W))
            translate([c - MCC_LID_VENT_SLOT_W / 2, y_lo, z_top - MCC_EPS])
                cube([MCC_LID_VENT_SLOT_W, MCC_LID_VENT_SLOT_L, MCC_LID_T + 2 * MCC_EPS]);
    }
}

// vim: expandtab tabstop=4 shiftwidth=4 softtabstop=4 nowrap
