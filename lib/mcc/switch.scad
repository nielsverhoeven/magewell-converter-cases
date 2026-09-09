//////////////////////////////////////////////////////////////////////
// LibFile: mcc/switch.scad
//   L1. Generic panel-switch provider (rev 11, #32, architecture.md §3). Owns the panel-switch
//   void (through-bore + outer recess pocket) and its own additive wall pad, plus a pure keep-out
//   accessor -- and nothing else: no dev/cfg, no per-SKU logic. The part is a row in MCC_SWITCHES
//   (constants.scad, L0); swapping it is a data edit, never a geometry edit (verdict B5). The
//   caller (shell.scad) places both the pad and the cutout, exactly as vents.scad places
//   mcc_fan_cutout(): local Z=[0,wall_t] spans the wall, inner face at local Z=0, outer face at
//   local Z=wall_t -- fan_pos/switch_pos (layout.scad) both carry the wall's OUTER-face plane in
//   X; every call site subtracts MCC_WALL itself (vents.scad:146 is the reference, architecture.md
//   rev-11 header finding B2).
// Includes:
//   include <mcc/mcc.scad>
//////////////////////////////////////////////////////////////////////

include <BOSL2/std.scad>
include <constants.scad>
use <util.scad>

// Function: _mcc_switch_pad_t()
// Description:
//   Private, PURE. Total wall+pad thickness at the switch position, mm -- shared by
//   mcc_switch_pad() (the additive material) and mcc_switch_cutout() (the recess/panel_t asserts)
//   so the two can never disagree about where the pad's own innermost face actually is (same
//   reasoning as mcc_panel_fixing_pos() being published once for panel.scad/shell.scad, D6).
//   recess_t is the T1-25 analogue for a switch (architecture.md R29, T1-44a) -- the actuator must
//   finish BELOW the wall's outer face, not just level with it. panel_t is CHOSEN, not derived: it
//   lands exactly on MCC_APERTURE_LIP_WEB_MIN, this repo's own 2.0 mm minimum-residual-material
//   precedent (MCC_PANEL_SEAT_T's own rabbet, the aperture lip), and sits inside every candidate
//   switch's assumed clamp range with room either way (T1-44c).
// Arguments:
//   spec   = switch record, struct from MCC_SWITCHES.
//   wall_t = wall thickness at the switch, mm.
function _mcc_switch_pad_t(spec, wall_t) =
    let(
        actuator_h = struct_val(spec, "actuator_proud_h"),
        recess_t = actuator_h + MCC_SWITCH_FLUSH_CLR,
        panel_t = MCC_APERTURE_LIP_WEB_MIN
    )
    recess_t + panel_t;

// Module: mcc_switch_pad()
// Usage:
//   mcc_switch_pad(spec, wall_t);
// Description:
//   ADDITIVE. Thickens the wall locally, INWARD only (D-13 pattern -- the outer face at local
//   Z=wall_t never moves, so no envelope figure moves on any SKU), so the recess pocket
//   mcc_switch_cutout() cuts below has somewhere to sit without thinning the wall below MCC_WALL
//   (T1-44d). A single round frustum, body_d at its deepest tip widening to the full pad_d right
//   where it meets the wall (the "pad band" footprint, which is what buys the T1-44b/c 2.0 mm lip
//   margin around the recess cut into it; layout-patch-wall.md §5's "two bands, at two depths").
//   ONE cyl() call, not a body_d cylinder + a separate 45 deg cone: a two-piece construction was
//   tried first and its internal seam came back as its own disconnected island under
//   build.py check (parts=2, watertight=False) even with an MCC_EPS overlap added at the seam --
//   the same class of Manifold/pinned-OpenSCAD-2025.09.07 robustness limit D10 (architecture.md
//   §13) diagnosed for a blind-bored boss unioned flush against a face. Tapering the WHOLE
//   pad_extra depth in one primitive removes the internal seam entirely and is also gentler
//   (shallower than 45 deg over this part's own dimensions) than the two-stage design it
//   replaces, so it stays inside architecture.md §5's <=45 deg self-supporting rule with margin
//   to spare. Never called with the switch disabled (mcc_fan_switch_enabled(cfg) gates the call
//   site, shell.scad).
// Arguments:
//   spec   = switch record, struct from MCC_SWITCHES. Default: MCC_SWITCH_DEFAULT's own row.
//   wall_t = wall thickness at the switch, mm. Default: MCC_WALL.
module mcc_switch_pad(spec = mcc_switch_spec(MCC_SWITCH_DEFAULT), wall_t = MCC_WALL) {
    pad_t = _mcc_switch_pad_t(spec, wall_t);
    pad_extra = pad_t - wall_t;
    pad_d  = struct_val(spec, "pad_d");
    body_d = struct_val(spec, "body_d");

    assert(pad_d >= body_d,
        str("mcc: mcc_switch_pad pad_d=", pad_d, " must be >= body_d=", body_d));

    if (pad_extra > MCC_EPS) {
        // Added material spans local Z in [-pad_extra, 0] -- i.e. from the pad's own deepest tip
        // (diameter body_d) up to Z=0+MCC_EPS, the ORIGINAL (pre-pad) inner wall face, overlapping
        // the plain wall block by MCC_EPS for a clean union (never [wall_t-pad_extra, wall_t],
        // which would needlessly re-cover the whole existing wall_t band a second time).
        translate([0, 0, -pad_extra])
            cyl(h = pad_extra + MCC_EPS, d1 = body_d, d2 = pad_d, circum = true, anchor = BOTTOM, $fn = 64);
    }
}

// Module: mcc_switch_cutout()
// Usage:
//   mcc_switch_cutout(spec, wall_t);
// Description:
//   SUBTRACTIVE. A through-bore (the switch's bushing/shaft, spanning the ENTIRE wall+pad
//   thickness) union()'d with an outer recess pocket (T1-44a: recess_t = actuator_proud_h +
//   MCC_SWITCH_FLUSH_CLR, so the actuator tip finishes below the wall's outer face -- the T1-25
//   analogue for a switch, architecture.md R29). Asserts T1-44(b)-(e) locally, from pure numbers,
//   the same pattern _mcc_patch_wall_rabbet() uses for its own residual-lip checks (shell.scad).
//   Always call alongside mcc_switch_pad() at the SAME position/rotation (shell.scad) -- the pad
//   is what gives this pocket somewhere to sit without thinning the wall.
// Arguments:
//   spec   = switch record, struct from MCC_SWITCHES. Default: MCC_SWITCH_DEFAULT's own row.
//   wall_t = wall thickness at the switch, mm. Default: MCC_WALL.
module mcc_switch_cutout(spec = mcc_switch_spec(MCC_SWITCH_DEFAULT), wall_t = MCC_WALL) {
    hole_d  = struct_val(spec, "hole_d");
    body_d  = struct_val(spec, "body_d");
    actuator_h = struct_val(spec, "actuator_proud_h");
    recess_t = actuator_h + MCC_SWITCH_FLUSH_CLR;
    pad_t = _mcc_switch_pad_t(spec, wall_t);
    panel_t = pad_t - recess_t;

    // T1-44(a): the actuator finishes below the outer face -- true by construction (recess_t is
    // DEFINED as actuator_proud_h + MCC_SWITCH_FLUSH_CLR above); asserted anyway so a future edit
    // that decouples the two definitions fails loudly instead of silently.
    assert(recess_t >= actuator_h + MCC_SWITCH_FLUSH_CLR - MCC_EPS,
        str("mcc: T1-44(a) fan-switch recess_t=", recess_t, " does not clear actuator_proud_h+MCC_SWITCH_FLUSH_CLR=",
            actuator_h + MCC_SWITCH_FLUSH_CLR));
    // T1-44(b): residual panel material behind the recess >= this repo's own 2.0 mm minimum.
    assert(panel_t >= MCC_APERTURE_LIP_WEB_MIN - MCC_EPS,
        str("mcc: T1-44(b) fan-switch residual panel_t=", panel_t, " below MCC_APERTURE_LIP_WEB_MIN=",
            MCC_APERTURE_LIP_WEB_MIN));
    // T1-44(c): residual panel material is inside the switch's own clamp range.
    assert(panel_t >= struct_val(spec, "panel_t_min") - MCC_EPS && panel_t <= struct_val(spec, "panel_t_max") + MCC_EPS,
        str("mcc: T1-44(c) fan-switch residual panel_t=", panel_t, " outside clamp range [",
            struct_val(spec, "panel_t_min"), ",", struct_val(spec, "panel_t_max"), "]"));
    // T1-44(d): a pad may thicken the wall, never thin it.
    assert(pad_t >= wall_t - MCC_EPS,
        str("mcc: T1-44(d) fan-switch pad_t=", pad_t, " thins the wall below wall_t=", wall_t));
    // T1-44(e): stop-and-report guard -- if the measured actuator (M17) forces a well deeper than
    // a fingertip can reach, the part is wrong; do not answer it by shaving the recess.
    assert(recess_t <= MCC_SWITCH_WELL_DEPTH_MAX + MCC_EPS,
        str("mcc: T1-44(e) fan-switch recess_t=", recess_t, " exceeds MCC_SWITCH_WELL_DEPTH_MAX=",
            MCC_SWITCH_WELL_DEPTH_MAX, " -- the part is wrong, do not shave the recess"));

    total_lo = wall_t - pad_t; // the pad's own innermost reach (or the plain wall's inner face,
                                // T1-44d guarantees pad_t >= wall_t so this is never past local Z=0)
    cut_h = wall_t - total_lo + 2 * MCC_EPS;

    union() {
        // Through-bore: the whole (wall + pad) depth, at the bushing/shaft clearance diameter.
        translate([0, 0, (total_lo + wall_t) / 2])
            cyl(h = cut_h, d = hole_d + MCC_HOLE_COMP, circum = true, $fn = 64);
        // Recess pocket: from the OUTER face inward by recess_t, at the nut-pocket diameter
        // (body_d -- the pad's own "body band" footprint, matching the U section's "nut pocket
        // diameter ~= 10").
        translate([0, 0, wall_t - recess_t / 2])
            cyl(h = recess_t + 2 * MCC_EPS, d = body_d, circum = true, $fn = 64);
    }
}

// Function: mcc_switch_keepout()
// Usage:
//   ko = mcc_switch_keepout(spec);
// Description:
//   PURE. The switch's own wall-plane pad footprint plus the body depth behind it -- mirrors
//   mcc_side_bolt_keepout()'s own pattern (fasteners.scad): diameters/depths only, position-
//   independent (the caller supplies switch_pos, layout.scad). Consumed by vents.scad (B8) so no
//   future +X-wall vent-slot array can ever be authored to land inside the switch's own keep-out.
//   layout.scad must NOT call this (architecture.md §3's L1-provider ban) -- its own T1-43 band
//   solve reads the MCC_SWITCHES row directly, exactly as mcc_floor_keepout()'s "mount_rail" row
//   is built from MCC_RAIL_* constants rather than from mcc_rail_sill_size() (rev 9 precedent).
// Arguments:
//   spec = switch record, struct from MCC_SWITCHES. Default: MCC_SWITCH_DEFAULT's own row.
function mcc_switch_keepout(spec = mcc_switch_spec(MCC_SWITCH_DEFAULT)) =
    [
        ["pad_d",  struct_val(spec, "pad_d")],
        ["body_d", struct_val(spec, "body_d")],
        ["depth",  struct_val(spec, "depth")],
    ];

// Module: mcc_switch_ghost()
// Usage:
//   mcc_switch_ghost(spec);
// Description:
//   Ghosted (%) review-only visualization of the switch's body envelope, swept from local Z=0
//   inward by `depth` -- same two-belt rule as ghost.scad (the % modifier is the mechanism,
//   MCC_SHOW_GHOST is the review signal the CALLER gates this behind, mirroring how
//   mcc_side_bolt_ghost() leaves gating to its own caller). Not exported by build.py, not
//   asserted -- a nice-to-have (plan §4.1), not load-bearing for #32.
// Arguments:
//   spec = switch record, struct from MCC_SWITCHES. Default: MCC_SWITCH_DEFAULT's own row.
module mcc_switch_ghost(spec = mcc_switch_spec(MCC_SWITCH_DEFAULT)) {
    body_d = struct_val(spec, "body_d");
    depth  = struct_val(spec, "depth");
    translate([0, 0, -depth])
        %cyl(h = depth, d = body_d, circum = true, anchor = BOTTOM, $fn = 32);
}

// Function: mcc_fan_switch_enabled()
// Usage:
//   on = mcc_fan_switch_enabled(cfg);
// Description:
//   Whether the live switch cutout/pad should be drawn for this `cfg` -- defaults to `cfg`'s own
//   "fan" value when "fan_switch" is absent, so every pre-#32 `variant = [...]` list keeps working
//   unchanged (a switch with no fan makes no product sense, verdict 9.4 item 5).
// Arguments:
//   cfg = variant-config assoc-list.
function mcc_fan_switch_enabled(cfg) =
    let(v = struct_val(cfg, "fan_switch"))
    is_undef(v) ? struct_val(cfg, "fan") : v;

// vim: expandtab tabstop=4 shiftwidth=4 softtabstop=4 nowrap
