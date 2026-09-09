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
//   Private. Slot centre positions tiling [run_lo, run_hi] at MCC_VENT_SLOT_W/MCC_VENT_WEB_W
//   pitch, centred in the run, with any slot whose own [c-w/2, c+w/2] footprint overlaps an entry
//   in `excl_ranges` dropped entirely (not narrowed) — layout-patch-wall.md §5's "no vent slot
//   inside" rule (T1-23/T1-23b), so the geometry drawn and the free-area count below always agree.
function _mcc_vent_slot_centers(run_lo, run_hi, excl_ranges = []) =
    let(
        pitch = MCC_VENT_SLOT_W + MCC_VENT_WEB_W,
        run = run_hi - run_lo,
        n = floor((run + MCC_VENT_WEB_W) / pitch),
        used = n * pitch - MCC_VENT_WEB_W,
        start = run_lo + (run - used) / 2 + MCC_VENT_SLOT_W / 2,
        all = [for (i = [0:1:n - 1]) start + i * pitch]
    )
    [for (c = all) if (!_mcc_in_any_range(c - MCC_VENT_SLOT_W / 2, c + MCC_VENT_SLOT_W / 2, excl_ranges)) c];

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
                    mcc_fan_cutout(MCC_FAN_DEFAULT, wall_t = MCC_WALL, grille = true);
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

// vim: expandtab tabstop=4 shiftwidth=4 softtabstop=4 nowrap
