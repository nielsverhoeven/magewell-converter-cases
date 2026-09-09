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
include <BOSL2/screws.scad>
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
    is_blank    = mcc_panel_hole_d(part) == 0; // D18 (architecture.md §5 rev 8, layout-patch-wall.md
                                                // §2.5.1): unify the blank test on hole_d==0, same as
                                                // shell.scad:181 and layout.scad:187 — NOT `kind ==
                                                // "blank"`. DBA-BL-B keeps kind "blank" (BOM/ghost
                                                // discriminator) but now carries hole_d=24.0, so it is
                                                // no longer geometrically blank: it gets the full round
                                                // cutout like any other 24-class part. The kind-based
                                                // branch below is dead on every current SKU; it stays
                                                // as the guard for a possible future genuinely-solid
                                                // blank (hole_d actually 0).
    is_24_class = mcc_panel_hole_d(part) >= 24.0;

    // Tier-1 asserts. architecture.md:346 "24.0 <= cutout_d <= 24.6 (never blow out the hole)" for
    // 24.0-class parts (etherCON/XLR); 23.6-24.2 for the 23.6-class parts (HDMI/USB/BNC), per the
    // brief's own module contract. A genuinely solid blank (hole_d=0) has no functional hole, so it
    // is exempt from the diameter check — no current SKU takes this branch (see is_blank above).
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

// Module: mcc_thread_pad()
// Usage:
//   mcc_thread_pad([pad_d=], [pad_h=], [slop=]);
// Description:
//   One additive pad (ADDITIVE solid, union onto the panel) carrying a printed M3x0.5 internal
//   thread bore (GitHub issue #30, architecture.md §5 "Connector fixing" bullet 3, rev 10,
//   2026-09-09). Public so mcc_neutrik_d_bosses() (below, connector fixing) and
//   models/coupons/m3-thread-ladder.scad (the calibration ladder) share ONE geometry source — a
//   coupon that hand-rebuilds this shape cannot calibrate the constant it exists to calibrate
//   (architect verdict B5, docs/plans/2026-09-09-printed-m3-threads.md §9). Do not call BOSL2
//   `screw_hole()` directly from models/** — always through this module.
//   Local Z convention matches the pre-#30 boss: Z=0 is the pad's seat face (the screw ENTERS
//   here, from the panel side), the pad extends to Z=-pad_h (the rear tip). The bore is a genuine
//   THROUGH-hole, open at both Z=0 and Z=-pad_h — required so this union does not hit the same
//   Manifold "blind-bore-flush-against-a-face" defect documented at length in shell.scad's
//   _mcc_patch_wall_fixing_bosses() (deviation D10); verified clean for this exact pad-on-plate
//   shape by an isolated repro during this ticket's research pass (plan §1).
//   When MCC_THREAD_FAST is true, the bore is a plain MCC_M3_CLR_D clearance cylinder instead of a
//   real thread — fast dev-iteration renders / the interactive case-viewer artifact only
//   (architect verdict B6). NEVER true for a release/coupon/print export — goldens, CI `render`/
//   `check`, and every release/coupon export use the default (false, real thread).
//   $fn policy exception (architecture.md §3, rev 10): the thread bore itself is $fn=32 — BOSL2
//   `screw_hole()` accepts no `circum` argument, so the usual circumscribe mechanism this repo
//   otherwise requires is unavailable, and the fit is carried by `slop` + assert T1-42c, not by
//   facet count (see the architecture.md citation for the full justification). The pad's own outer
//   cylinder keeps the repo's normal $fn=64 + circum=true — this exception is scoped to the thread
//   bore only, not to the pad shape.
// Arguments:
//   pad_d = pad outer diameter, mm. Default: MCC_THREAD_M3_PAD_D (8.28).
//   pad_h = total rearward pad length from the seat, mm. Default: MCC_THREAD_M3_PAD_H (7.0).
//   slop  = BOSL2 $slop radial print-compensation for the thread bore, mm. Default:
//           MCC_THREAD_M3_SLOP (0.05).
//   fast  = force the cheap clearance-bore path regardless of MCC_THREAD_FAST. Default:
//           MCC_THREAD_FAST (false) — same overridable-default idiom as mcc_ghost(dev, show =
//           MCC_SHOW_GHOST) (ghost.scad), so a smoke test can exercise both paths from one file
//           without having to re-`include` constants.scad with a different -D value.
//   enforce_min_radial = when false, SKIP the T1-42c residual-radial-engagement assert only
//           (T1-42a wall and T1-42b turns still always assert). Default: true (every production
//           call site — mcc_neutrik_d_bosses() — keeps the full contract). Exists ONLY for
//           models/coupons/m3-thread-ladder.scad: architecture.md rev 10 B1 mandates the ladder
//           sweep $slop across EXACTLY [0.02, 0.035, 0.05, 0.065, 0.08], and rev 10 also mandates
//           T1-42c as unconditional — but the top rung (0.08) fails T1-42c by construction
//           (residual = 0.2705 - 2*0.08 = 0.1105 < 0.135), so a hard, unconditional assert makes
//           the mandated ladder physically un-renderable as one coupon. T1-42c is a *production*
//           policy floor (never ship a pad below 50% nominal engagement); the ladder's entire
//           purpose is to physically test rungs on both sides of that floor and read back which
//           one actually strips a real screw — so letting the coupon (and ONLY the coupon)
//           instantiate a rung the policy would reject for production is the point of a
//           calibration ladder, not a bug. Flagged to the architect/user in this ticket's PR
//           rather than silently resolved either by dropping T1-42c or by silently shrinking the
//           architect-mandated rung array.
module mcc_thread_pad(pad_d = MCC_THREAD_M3_PAD_D, pad_h = MCC_THREAD_M3_PAD_H, slop = MCC_THREAD_M3_SLOP, fast = MCC_THREAD_FAST, enforce_min_radial = true) {
    // T1-42a: pad wall thickness around the (slopped) major diameter. BOSL2 grows an internal
    // thread by 4*slop in DIAMETER (screws.scad:753), i.e. 2*slop per side.
    thread_major_slopped = MCC_THREAD_M3_MAJOR_D + 4 * slop;
    wall = (pad_d - thread_major_slopped) / 2;
    assert(wall >= MCC_THREAD_WALL_MIN,
        str("mcc: T1-42a thread pad wall=", wall, " below minimum ", MCC_THREAD_WALL_MIN, " mm (pad_d=", pad_d, ", slop=", slop, ")"));

    // T1-42b: engaged thread turns.
    engaged_len = pad_h - MCC_THREAD_M3_CHAMFER;
    turns = engaged_len / MCC_THREAD_M3_PITCH;
    assert(turns >= MCC_THREAD_ENGAGE_MIN_TURNS,
        str("mcc: T1-42b thread engagement=", turns, " turns below minimum ", MCC_THREAD_ENGAGE_MIN_TURNS, " (pad_h=", pad_h, ")"));

    // T1-42c: residual radial thread engagement after slop — the assert that catches a $slop
    // value large enough to erase the thread outright (architecture.md rev 10, B1). Skippable ONLY
    // via enforce_min_radial=false (see the argument doc above) — every production call site
    // leaves this true.
    residual_radial = MCC_THREAD_M3_MAJOR_D / 2 - MCC_THREAD_M3_MINOR_D / 2 - 2 * slop;
    if (enforce_min_radial)
        assert(residual_radial >= MCC_THREAD_ENGAGE_MIN_RADIAL,
            str("mcc: T1-42c residual radial thread engagement=", residual_radial, " below minimum ", MCC_THREAD_ENGAGE_MIN_RADIAL, " mm (slop=", slop, ")"));

    difference() {
        translate([0, 0, -pad_h / 2])
            cyl(h = pad_h, d = pad_d, circum = true, $fn = 64);
        if (fast) {
            // Fast path: plain screw-clearance bore, same $fn/circum convention as every other
            // plain M3 clearance hole in this file. NEVER for a release/coupon/print export.
            translate([0, 0, -pad_h - MCC_EPS])
                cyl(h = pad_h + 2 * MCC_EPS, d = MCC_M3_CLR_D, circum = true, $fn = 64);
        } else {
            // Real path (default): printed M3x0.5 internal thread. anchor=BOTTOM at Z=-pad_h
            // means the hole's BOTTOM is the pad's rear tip and its TOP is the panel-facing seat
            // face where the screw actually starts — bevel2 (not bevel1) is therefore the correct
            // lead-in chamfer end (architect verdict B3).
            translate([0, 0, -pad_h])
                screw_hole(str("M3,", pad_h + 2 * MCC_EPS), thread = true, tolerance = "6H",
                    $slop = slop, bevel2 = true, anchor = BOTTOM, $fn = 32);
        }
    }
}

// Module: mcc_neutrik_d_bosses()
// Usage:
//   mcc_neutrik_d_bosses(part, [mirror=], [pad_h=], [pad_d=]);
// Description:
//   Two rear pads (ADDITIVE solid, union onto the panel) at the two screw positions, each carrying
//   a printed M3 internal thread the connector's own machine screw drives straight into (GitHub
//   issue #30, 2026-09-09 — replaces the heat-set-insert version of this module, T1-35/deviation
//   D10's fix). The plate's own 4 retention bosses in shell.scad are UNCHANGED (still heat-set
//   inserts) — this module only covers the connector-to-plate fixing
//   (docs/plans/2026-09-09-printed-m3-threads.md §0). Geometry lives in mcc_thread_pad() (above);
//   this module only places two of them at the standard diagonal.
// Arguments:
//   part   = panel part number (kept only to keep the call site symmetric with the cutout call;
//            the pad geometry itself does not vary per connector).
//   mirror = mirror the two screw-hole positions left-right, matching mcc_neutrik_d_cutout()'s own
//            `mirror` argument. Default: false.
//   pad_h  = total rearward pad length from the seat, mm. Default: MCC_THREAD_M3_PAD_H (7.0).
//   pad_d  = pad outer diameter override, mm. Default: MCC_THREAD_M3_PAD_D (8.28).
module mcc_neutrik_d_bosses(part, mirror = false, pad_h = MCC_THREAD_M3_PAD_H, pad_d = MCC_THREAD_M3_PAD_D) {
    mirror_x = mirror ? -1 : 1;
    screw_x  = mirror_x * MCC_D_SCREW_PITCH[0] / 2;
    screw_y  = MCC_D_SCREW_PITCH[1] / 2;

    for (pos = [[-screw_x, screw_y], [screw_x, -screw_y]])
        translate([pos[0], pos[1], 0])
            mcc_thread_pad(pad_d = pad_d, pad_h = pad_h);
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
