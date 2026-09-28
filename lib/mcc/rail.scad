//////////////////////////////////////////////////////////////////////
// LibFile: mcc/rail.scad
//   L1. Tool-less dovetail mount-rail interface (issue #25, replaces VESA — D-15, rev 9). Owns the
//   ONE cross-section shared by both mating halves so they can never drift apart (D6 precedent,
//   architecture.md §5 rev 5): mcc_rail_male() (bracket-side, additive — #26/#27 consume it, not
//   this branch) and mcc_rail_female_cut() (case-floor-side, subtractive — mounts.scad consumes
//   it), plus the pure mcc_rail_sill_size() accessor. NOT named bracket.scad (architecture.md §3
//   rev 9, R4/layout-patch-wall.md §17.2): the name describes the INTERFACE, not one of its two
//   consumers — a file named for a consumer invites bracket-plate/hole/rib geometry (per-bracket
//   assembly work) into an L1 provider.
//   `layout.scad` must NOT `use` this file (architecture.md §3) — the "mount_rail" floor keep-out
//   row is built from the MCC_RAIL_* L0 constants only, never from mcc_rail_sill_size().
//   `use`d by lib/mcc/mounts.scad (the female groove, case floor) and, in a later branch, by
//   models/brackets/*.scad (the male rail) via the barrel.
// Includes:
//   include <mcc/mcc.scad>
//////////////////////////////////////////////////////////////////////

include <BOSL2/std.scad>
include <constants.scad>
use <util.scad>

// -----------------------------------------------------------------------------------------
// Local frame (shared by mcc_rail_male() and mcc_rail_female_cut()): long axis (slide axis) =
// local X, spanning [-len/2, +len/2] for the working (dovetail) length; local Y = across the
// dovetail's width, centred on 0; local Z = depth/height, Z=0 at the mating surface (the bracket
// plate's top face for the male; the case's exterior floor face for the female), +Z runs INTO the
// case. Single insertion direction (PLAN-ASSUMPTION-2, RATIFIED, layout-patch-wall.md §17.5; ends
// fixed by D34, 2026-09-28): the case groove is OPEN at +X — it runs out through the case's +X wall
// (mcc_rail_female_cut()'s `open_ext`) — and CLOSED at -X, which is the end stop the male's -X face
// runs into. The male slides in -X relative to the case; the latch sits on the -Y flank near the
// open end (+len/2 - MCC_RAIL_LATCH_LEAD_IN). Before D34 the groove was closed at BOTH ends, so no
// case could ever be slid onto a bracket.
//
// Cross-section: a standard dovetail, narrow (MCC_RAIL_MOUTH_W) at the mating surface — Z=0 for
// the female groove's own local frame; Z=MCC_FLOOR_T for the male, where its taper begins, riding
// on a MCC_FLOOR_T-tall constant-width pedestal that fills the standoff gap between the bracket
// plate and the case's own exterior floor face — widening to MCC_RAIL_ROOT_W at the deepest point
// (Z=MCC_RAIL_DEPTH female-local / Z=MCC_RAIL_SILL_H male-local). WIDE material sits DEEPER inside
// the groove, so the case cannot be lifted straight off the bracket (out-of-slide-axis separation)
// — only sliding along X clears the interlock. MCC_RAIL_SILL_H = MCC_RAIL_DEPTH + MCC_FLOOR_T is
// exactly pedestal + taper, so at full mate the case's exterior floor face rests flush on the
// pedestal's top and the taper exactly fills the case's own groove.
// -----------------------------------------------------------------------------------------

// Function: mcc_rail_sill_size()
// Usage:
//   sz = mcc_rail_sill_size();
// Description:
//   Pure. [length, width, height] of the case-floor sill the groove is cut into — for BOM/preview
//   use. NOT `use`d by layout.scad itself (architecture.md §3 rev 9 — that file builds its
//   "mount_rail" keep-out row from the MCC_RAIL_* constants directly, never from this function, so
//   layout.scad never gains an L1 geometry-provider dependency).
function mcc_rail_sill_size() = [MCC_RAIL_LEN, MCC_RAIL_ROOT_W + 2 * MCC_RAIL_SILL_SIDE_W, MCC_RAIL_SILL_H];

// Module: _mcc_rail_taper()
// Description:
//   Private. The dovetail taper alone (no pedestal, no latch, no end-stop): a prismoid from
//   MCC_RAIL_MOUTH_W (at local Z=0) to MCC_RAIL_ROOT_W (at local Z=MCC_RAIL_DEPTH), length `len`
//   along X, centred on Y=0, anchored BOTTOM. Shared by both mcc_rail_male()'s taper (translated up
//   onto its pedestal) and mcc_rail_female_cut()'s groove (used directly — its own local Z=0 IS the
//   case's exterior floor face) so the two profiles can never independently drift — one function,
//   two callers.
// Arguments:
//   len = rail/groove length along the slide axis, mm.
//   clr = per-side clearance added to both MOUTH_W and ROOT_W, mm. Default 0 (nominal/male). The
//         female groove passes MCC_CLR_SLIDE (reused, not a new constant — constants.scad).
module _mcc_rail_taper(len, clr = 0) {
    prismoid(
        size1 = [len, MCC_RAIL_MOUTH_W + 2 * clr],
        size2 = [len, MCC_RAIL_ROOT_W + 2 * clr],
        h = MCC_RAIL_DEPTH, anchor = BOTTOM
    );
}

// -----------------------------------------------------------------------------------------
// Latch geometry (issue #46, architecture.md §13 D34). Everything below is derived from the
// MCC_RAIL_LATCH_* constants and the caller's own `len`, in the shared local frame. The latch sits
// on the -Y flank near the case's OPEN end (+X); the arm's root is on the +X side of its nub.
// -----------------------------------------------------------------------------------------

// Function: _mcc_rail_flank_k()
// Description: Private. Outward (-Y) run of the -Y flank per mm of height over the taper.
function _mcc_rail_flank_k() = (MCC_RAIL_ROOT_W - MCC_RAIL_MOUTH_W) / (2 * MCC_RAIL_DEPTH);

// Function: _mcc_rail_latch_geom()
// Description:
//   Private, pure. [nub_x0, nub_x1, tip_x, root_x, ramp_in_l, ramp_out_l] for a rail of working
//   length `len`: the nub centred on +len/2 - MCC_RAIL_LATCH_LEAD_IN, entry ramp on its -X side
//   (the side the groove's open-end edge meets first — the male slides in -X relative to the
//   case), exit ramp on its +X side; the arm's free tip at the nub's -X end, its root
//   MCC_RAIL_LATCH_ARM_L further +X.
function _mcc_rail_latch_geom(len) =
    let(
        e = MCC_RAIL_LATCH_ENGAGE,
        r_in = e / tan(MCC_RAIL_LATCH_RAMP_IN),
        r_out = e / tan(MCC_RAIL_LATCH_RAMP_OUT),
        nub_l = r_in + MCC_RAIL_LATCH_FLAT + r_out,
        xc = len / 2 - MCC_RAIL_LATCH_LEAD_IN,
        x0 = xc - nub_l / 2
    )
    [x0, x0 + nub_l, x0, x0 + MCC_RAIL_LATCH_ARM_L, r_in, r_out];

// Module: _mcc_rail_nub_2d()
// Description:
//   Private. The nub's plan outline at the pedestal flank line (y = -MOUTH_W/2), grown by `grow`
//   (0 = the male nub; MCC_CLR_SLIDE = the female notch). Overlaps MCC_EPS*20 into the flank so the
//   union with the arm is a genuine shared volume.
module _mcc_rail_nub_2d(g, grow = 0) {
    y0 = -MCC_RAIL_MOUTH_W / 2;
    e = MCC_RAIL_LATCH_ENGAGE;
    offset(delta = grow)
        polygon([
            [g[0], y0 + 0.2],
            [g[0], y0],
            [g[0] + g[4], y0 - e],
            [g[1] - g[5], y0 - e],
            [g[1], y0],
            [g[1], y0 + 0.2],
        ]);
}

// Module: _mcc_rail_flank_extrude()
// Description:
//   Private. Extrudes a plan-view 2-D child (drawn at the pedestal's flank line) over z0..z1 of the
//   MALE frame so it follows the -Y flank: straight up to MCC_FLOOR_T (pedestal), then sheared
//   outward with the dovetail taper above it. The same helper cuts the female notch (female z = male
//   z - MCC_FLOOR_T, handled by the caller's translate), so arm, slot, nub and notch stay parallel
//   to the flank by construction.
module _mcc_rail_flank_extrude(z0, z1) {
    zb = MCC_FLOOR_T;
    k = _mcc_rail_flank_k();
    if (z0 < zb)
        translate([0, 0, z0]) linear_extrude(height = min(z1, zb) - z0 + MCC_EPS) children();
    if (z1 > zb)
        multmatrix([[1, 0, 0, 0], [0, 1, -k, k * zb], [0, 0, 1, 0], [0, 0, 0, 1]])
            translate([0, 0, max(z0, zb)]) linear_extrude(height = z1 - max(z0, zb)) children();
}

// Module: _mcc_rail_latch_cut_2d()
// Description: Private. Plan view of what frees the arm: the slot behind it (rounded root end =
//   the root fillet) plus the gap at its free tip that cuts the flank clean through.
module _mcc_rail_latch_cut_2d(g) {
    y0 = -MCC_RAIL_MOUTH_W / 2;
    t = MCC_RAIL_LATCH_ARM_T;
    s = MCC_RAIL_LATCH_SLOT;
    union() {
        hull() {
            translate([g[2] - s, y0 + t]) square([MCC_EPS, s]);
            translate([g[3] - s / 2, y0 + t + s / 2]) circle(d = s, $fn = 32);
        }
        translate([g[2] - s, y0 - MCC_RAIL_LATCH_ENGAGE - 2 * MCC_RAIL_DEPTH]) // well past the flank + nub
            square([s, t + s + MCC_RAIL_LATCH_ENGAGE + 2 * MCC_RAIL_DEPTH]);
    }
}

// Module: mcc_rail_male_window()
// Usage:
//   difference() { plate(); mcc_rail_male_window(len, plate_t); }   // then union mcc_rail_male()
// Description:
//   SUBTRACTIVE, for the consumer's own plate (tv-bracket, arch-tv-bracket centre, rail-latch
//   coupon base): the window under the latch arm and its slot, through the plate's whole
//   thickness, so the arm's leg reaches the print bed and never fuses to the plate except at its
//   root. Same local frame and transform as the consumer's mcc_rail_male() call; plate top at Z=0.
//   Cut it BEFORE unioning the rail — the rail's own arm leg fills the window.
module mcc_rail_male_window(len = MCC_RAIL_LEN, plate_t) {
    if (MCC_RAIL_LATCH_ENABLED && plate_t > 0) {
        g = _mcc_rail_latch_geom(len);
        y0 = -MCC_RAIL_MOUTH_W / 2;
        c = MCC_RAIL_LATCH_WINDOW_CLR;
        translate([0, 0, -plate_t - MCC_EPS])
            linear_extrude(height = plate_t + 2 * MCC_EPS)
                intersection() {
                    offset(delta = c) union() {
                        translate([g[2], y0]) square([g[3] - g[2], MCC_RAIL_LATCH_ARM_T]);
                        _mcc_rail_latch_cut_2d(g);
                    }
                    // Never past the root: the arm's leg must stay joined to the plate there.
                    translate([g[2] - 50, y0 - 50]) square([g[3] - g[2] + 50, 100]);
                }
    }
}

// Module: mcc_rail_male()
// Usage:
//   mcc_rail_male([len=], [plate_t=]);
// Description:
//   ADDITIVE. The male dovetail rail (bracket side): a MCC_FLOOR_T-tall pedestal (MCC_RAIL_MOUTH_W
//   wide — the standoff under the case's exterior floor face) carrying the shared taper, over the
//   working length [-len/2, +len/2]. No separate end stop (D34): the case groove's closed -X end
//   stops the rail's -X end face.
//   Latch (issue #46, D34): on the -Y flank near +X, an in-plane snap arm — a flank-parallel strip
//   MCC_RAIL_LATCH_ARM_T thick, freed from the core by MCC_RAIL_LATCH_SLOT and from the plate by
//   mcc_rail_male_window(), root at +X, free tip at -X — with a ramped nub on its tip that snaps
//   into mcc_rail_female_cut()'s notch at full insertion. With `plate_t` > 0 the arm continues as a
//   leg down to Z = -plate_t (the print bed under the consumer's plate), so it prints standing on
//   the bed instead of hanging off the rail. The consumer MUST cut mcc_rail_male_window() out of
//   its plate first.
// Arguments:
//   len     = working length, mm. Default: MCC_RAIL_LEN. Must match the female cut's `len`.
//   plate_t = thickness of the consumer's plate under the rail (plate top at Z=0), mm. Default 0.
module mcc_rail_male(len = MCC_RAIL_LEN, plate_t = 0) {
    g = _mcc_rail_latch_geom(len);
    t = MCC_RAIL_LATCH_ARM_T;
    L = MCC_RAIL_LATCH_ARM_L;
    e = MCC_RAIL_LATCH_ENGAGE;
    strain = 1.5 * t * e / (L * L);
    if (MCC_RAIL_LATCH_ENABLED) {
        assert(L / t >= 8, str("mcc: rail latch L/t=", L / t, " below 8:1 (fasteners-and-hardware.md:133)"));
        assert(MCC_RAIL_LATCH_SLOT / 2 >= MCC_RAIL_LATCH_ROOT_FILLET - MCC_EPS,
            str("mcc: rail latch root radius ", MCC_RAIL_LATCH_SLOT / 2, " below the root fillet minimum"));
        assert(MCC_RAIL_LATCH_SLOT > e + MCC_EPS - MCC_CLR_SLIDE,
            str("mcc: rail latch slot ", MCC_RAIL_LATCH_SLOT, " cannot absorb the nub's deflection"));
        assert(strain <= MCC_SNAP_STRAIN_MAX,
            str("mcc: rail latch tip strain ", strain, " exceeds MCC_SNAP_STRAIN_MAX ", MCC_SNAP_STRAIN_MAX));
        assert(MCC_RAIL_SILL_H + plate_t >= 5,
            str("mcc: rail latch arm height ", MCC_RAIL_SILL_H + plate_t, " below the 5 mm minimum clip width"));
        assert(g[2] - MCC_RAIL_LATCH_SLOT > -len / 2 + 5 && g[3] < len / 2 - 2,
            str("mcc: rail latch (", g, ") does not fit inside len=", len));
    }

    difference() {
        union() {
            cuboid([len, MCC_RAIL_MOUTH_W, MCC_FLOOR_T], anchor = BOTTOM);
            translate([0, 0, MCC_FLOOR_T]) _mcc_rail_taper(len);
            if (MCC_RAIL_LATCH_ENABLED) {
                // Nub over the taper — the part that rides inside the groove. It starts at the
                // case bottom's level as a 2 mm ledge off the arm: well inside the slicer's 3 mm
                // cantilever limit, so no chin is needed (and none is added — a hulled chin left
                // zero-volume slivers against the arm).
                _mcc_rail_flank_extrude(MCC_FLOOR_T, MCC_RAIL_SILL_H) _mcc_rail_nub_2d(g);
            }
        }
        if (MCC_RAIL_LATCH_ENABLED)
            _mcc_rail_flank_extrude(-plate_t - 1, MCC_RAIL_SILL_H + 1) _mcc_rail_latch_cut_2d(g);
    }
    // The arm's leg through the consumer's plate window, down to the bed, drawn in its final plan
    // shape (arm band minus slot and tip gap) so the only faces it shares with the rail or the
    // plate have material on the same side. It runs MCC_RAIL_LATCH_WINDOW_CLR past the root into
    // the plate (the window stops at the root) and MCC_FLOOR_T/2 up into the pedestal.
    if (MCC_RAIL_LATCH_ENABLED && plate_t > 0)
        translate([0, 0, -plate_t])
            linear_extrude(height = plate_t + MCC_FLOOR_T / 2)
                difference() {
                    translate([g[2], -MCC_RAIL_MOUTH_W / 2])
                        square([g[3] - g[2] + MCC_RAIL_LATCH_WINDOW_CLR, t + MCC_RAIL_LATCH_SLOT]);
                    _mcc_rail_latch_cut_2d(g);
                }
}

// Module: mcc_rail_female_cut()
// Usage:
//   mcc_rail_female_cut([len=], [open_ext=]);
// Description:
//   SUBTRACTIVE. The matching dovetail groove (case-floor side): the shared taper widened by
//   MCC_CLR_SLIDE per side for a sliding fit, from its CLOSED -X end (the end stop, D34) at -len/2
//   through +len/2 and on by `open_ext` — the passage the male enters through, which the case runs
//   out through its +X wall. Plus the latch notch in the -Y flank (the nub's outline grown by
//   MCC_CLR_SLIDE, following the flank). Local frame: mouth at Z=0 = the case's exterior floor
//   face, +Z into the case; a MCC_EPS overlap below Z=0 pierces that face cleanly.
//   T1-38 (rev 9 R1): >= MCC_FLOOR_T of floor remains above the groove over the working length.
// Arguments:
//   len      = working length, mm. Default: MCC_RAIL_LEN. Must match the mating mcc_rail_male().
//   open_ext = how far the groove continues past +len/2 (the insertion passage), mm. Default 0.
module mcc_rail_female_cut(len = MCC_RAIL_LEN, open_ext = 0) {
    assert(MCC_RAIL_SILL_H - MCC_RAIL_DEPTH >= MCC_FLOOR_T - MCC_EPS,
        str("mcc: rail_female_cut T1-38 residual floor over the groove = ",
            MCC_RAIL_SILL_H - MCC_RAIL_DEPTH, " below the MCC_FLOOR_T (", MCC_FLOOR_T, ") minimum"));
    clr = MCC_CLR_SLIDE;
    g = _mcc_rail_latch_geom(len);

    union() {
        translate([open_ext / 2, 0, -MCC_EPS])
            _mcc_rail_taper_eps(len + open_ext, clr, MCC_EPS);
        if (MCC_RAIL_LATCH_ENABLED)
            // Female z = male z - MCC_FLOOR_T; notch spans the groove's whole depth.
            translate([0, 0, -MCC_FLOOR_T])
                _mcc_rail_flank_extrude(MCC_FLOOR_T - MCC_EPS, MCC_FLOOR_T + MCC_RAIL_DEPTH)
                    _mcc_rail_nub_2d(g, grow = clr);
    }
}

// Module: _mcc_rail_taper_eps()
// Description:
//   Private. Like _mcc_rail_taper(), but with the whole shape shifted down by `eps` and grown by
//   `eps` so it overlaps the caller's own Z=0 boundary cleanly (manifold-avoidance — see
//   mcc_rail_female_cut()'s own doc comment). The extra `eps` (0.01 mm) is applied only to the
//   bottom face; the two nominal widths (at the true Z=0 mouth and Z=depth root) are unaffected.
module _mcc_rail_taper_eps(len, clr, eps) {
    union() {
        _mcc_rail_taper(len, clr);
        // Thin slab at MOUTH width, spanning [-eps, 0] in this module's own shifted frame, so the
        // cut pierces the exterior floor face rather than sharing a coincident face with it.
        translate([0, 0, -eps])
            cuboid([len, MCC_RAIL_MOUTH_W + 2 * clr, eps], anchor = BOTTOM);
    }
}

// vim: expandtab tabstop=4 shiftwidth=4 softtabstop=4 nowrap
