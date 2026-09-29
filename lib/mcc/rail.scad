//////////////////////////////////////////////////////////////////////
// LibFile: mcc/rail.scad
//   L1. Tool-less dovetail mount-rail interface (issue #25, replaces VESA — D-15, rev 9). Owns the
//   ONE cross-section shared by both mating halves so they can never drift apart (D6 precedent,
//   architecture.md §5 rev 5): mcc_rail_male() (bracket-side, additive — #26/#27 consume it, not
//   this branch) and mcc_rail_female_cut() (case-floor-side, subtractive — mounts.scad consumes
//   it), plus the pure accessors mcc_rail_sill_size() and mcc_rail_male_keepout() (the plate-side
//   keep-out every bracket reads -- D50). NOT named bracket.scad (architecture.md §3 rev 9,
//   R4/layout-patch-wall.md §17.2): the name describes the INTERFACE, not one of its two
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
// runs into. The male slides in -X relative to the case; the gravity-lock bump sits on the -Y flank
// near the male's +X end (len/2 - MCC_RAIL_LOCK_END_OFFSET, D48), and the groove's exit through the
// case's +X wall has a 45-degree lead-in (D48). Before D34 the groove was closed at BOTH ends, so no
// case could ever be slid onto a bracket.
//
// Cross-section: a standard dovetail, narrow (MCC_RAIL_MOUTH_W) at the mating surface -- local Z=0
// on BOTH halves (D44, 2026-09-28: the male has no pedestal any more; male-local = female-local,
// Z included) -- widening to MCC_RAIL_ROOT_W at Z=MCC_RAIL_DEPTH, the groove roof. WIDE material sits
// DEEPER inside the groove, so the case cannot be lifted straight off the bracket; only sliding along
// X clears the interlock. At full mate the case's flat exterior floor rests FLUSH on the bracket
// plate everywhere outside the two footprints -- the joint's only designed bearing face. The male
// stands MCC_RAIL_MALE_H tall (MCC_RAIL_ROOF_CLR short of the roof) and the groove is offset
// MCC_RAIL_CLR_HORIZ per side, so every other face has >= MCC_RAIL_MATE_CLR (T1-62).
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
//   Private. The dovetail taper alone (no lock): a prismoid from MCC_RAIL_MOUTH_W at local Z=0,
//   widening along the flank's own slope for `h` mm, length `len` along X, centred on Y=0, anchored
//   BOTTOM. The female groove uses the full MCC_RAIL_DEPTH (top width == MCC_RAIL_ROOT_W exactly);
//   the male stops at MCC_RAIL_MALE_H with the SAME slope (D44), so the two profiles can never drift.
// Arguments:
//   len = rail/groove length along the slide axis, mm.
//   clr = per-side horizontal clearance added to both widths, mm. Default 0 (the male). The female
//         groove passes MCC_RAIL_CLR_HORIZ (D44).
//   h   = height, mm. Default MCC_RAIL_DEPTH.
module _mcc_rail_taper(len, clr = 0, h = MCC_RAIL_DEPTH) {
    w_top = MCC_RAIL_MOUTH_W + 2 * h * _mcc_rail_flank_k();
    prismoid(
        size1 = [len, MCC_RAIL_MOUTH_W + 2 * clr],
        size2 = [len, w_top + 2 * clr],
        h = h, anchor = BOTTOM
    );
}

// -----------------------------------------------------------------------------------------
// Flank helpers. The lock bump (male) and its pocket (female) are drawn in plan view at the mouth
// flank line (y = -MOUTH_W/2, the plate top) and swept up the -Y flank by _mcc_rail_flank_extrude(),
// so both stay parallel to the flank by construction.
// -----------------------------------------------------------------------------------------

// Function: _mcc_rail_flank_k()
// Description: Private. Outward (-Y) run of the -Y flank per mm of height over the taper.
function _mcc_rail_flank_k() = (MCC_RAIL_ROOT_W - MCC_RAIL_MOUTH_W) / (2 * MCC_RAIL_DEPTH);

// Module: _mcc_rail_flank_extrude()
// Description:
//   Private. Extrudes a plan-view 2-D child (drawn at the mouth flank line) over z0..z1 of the shared
//   frame so it follows the -Y flank: sheared outward with the dovetail taper above Z=0, straight
//   below it. Male Z = female Z since D44, so the same helper places the lock bump and cuts its
//   pocket.
module _mcc_rail_flank_extrude(z0, z1) {
    zb = 0;
    k = _mcc_rail_flank_k();
    if (z0 < zb)
        translate([0, 0, z0]) linear_extrude(height = min(z1, zb) - z0 + MCC_EPS) children();
    if (zb < z1)
        multmatrix([[1, 0, 0, 0], [0, 1, -k, k * zb], [0, 0, 1, 0], [0, 0, 0, 1]])
            translate([0, 0, max(z0, zb)]) linear_extrude(height = z1 - max(z0, zb)) children();
}

// -----------------------------------------------------------------------------------------
// Gravity lock (user decision 2026-09-28, architecture.md §13 D48 -- replaces the D34 snap latch). A
// RIGID bump on the male's -Y flank, near its +X end, drops into a pocket in the groove's -Y flank at
// full insertion. Every bracket places the rail with rotate([0,0,180]) and a mounted case always hangs
// patch-wall down (D49), so the -Y flank is the upper one: the case's weight rests on it and holds the
// bump in its pocket. Nothing flexes -- sliding on, the case rides over the bump inside the
// dovetail's own flank play (T1-64). The exit face is square to the slide axis, so an axial pull
// cannot cam a hanging case out; lifting the case about 1 mm (onto the lower flank) releases it.
// -----------------------------------------------------------------------------------------

// Function: _mcc_rail_lock_geom()
// Description:
//   Private, pure. [x0, x1, ramp_in_l, ramp_out_l] of the lock bump for a rail of working length
//   `len` and protrusion `e`: exit face (its +X side) at len/2 - MCC_RAIL_LOCK_END_OFFSET, then the
//   flat top and the entry ramp toward -X. The male slides in -X relative to the case, so the
//   groove's open end meets the entry ramp first; withdrawing, the pocket's +X wall meets the exit
//   face.
function _mcc_rail_lock_geom(len, e = MCC_RAIL_LOCK_ENGAGE) =
    let(
        r_in = e / tan(MCC_RAIL_LOCK_RAMP_IN),
        r_out = MCC_RAIL_LOCK_RAMP_OUT == 90 ? 0 : e / tan(MCC_RAIL_LOCK_RAMP_OUT),
        x1 = len / 2 - MCC_RAIL_LOCK_END_OFFSET,
        x0 = x1 - r_out - MCC_RAIL_LOCK_FLAT - r_in
    )
    [x0, x1, r_in, r_out];

// Module: _mcc_rail_lock_2d()
// Description:
//   Private. The lock bump's plan outline at the mouth flank line, grown by `grow` (0 = the male
//   bump; MCC_RAIL_CLR_HORIZ = the female pocket). It reaches 0.2 mm into the rail core so the union
//   with the taper shares real volume.
module _mcc_rail_lock_2d(len, e = MCC_RAIL_LOCK_ENGAGE, grow = 0) {
    g = _mcc_rail_lock_geom(len, e);
    y0 = -MCC_RAIL_MOUTH_W / 2;
    offset(delta = grow)
        polygon([
            [g[0], y0 + 0.2],
            [g[0], y0],
            [g[0] + g[2], y0 - e],
            [g[1] - g[3], y0 - e],
            [g[1], y0],
            [g[1], y0 + 0.2],
        ]);
}

// Function: mcc_rail_male_keepout()
// Usage:
//   ko = mcc_rail_male_keepout([len]);   // [[x_min, x_max], [y_min, y_max]]
// Description:
//   Pure. The conservative plan-view extent, in the shared rail-local frame, of everything
//   mcc_rail_male() puts on or into a consumer's plate: the taper (bounded by MCC_RAIL_ROOT_W, wider
//   than the male's own MCC_RAIL_MALE_H top) plus the lock bump on the -Y flank. The rail needs no
//   cut in the plate (D50): a consumer unions mcc_rail_male() onto its plate and keeps its other plate
//   features out of this rectangle, adding its own clearance. A rotate([0,0,180]) placement negates
//   and swaps both ranges. Brackets read this, never the MCC_RAIL_LOCK_* constants (architecture.md
//   §3, D50).
// Arguments:
//   len = working length, mm. Default: MCC_RAIL_LEN.
function mcc_rail_male_keepout(len = MCC_RAIL_LEN) =
    [[-len / 2, len / 2], [-MCC_RAIL_ROOT_W / 2 - MCC_RAIL_LOCK_ENGAGE, MCC_RAIL_ROOT_W / 2]];

// Module: mcc_rail_male()
// Usage:
//   union() { plate(); mcc_rail_male([len=]); }
// Description:
//   ADDITIVE. The male dovetail rail (bracket side): the shared taper, MCC_RAIL_MALE_H tall, standing
//   directly on the consumer's plate (no pedestal since D44 -- the case floor rests flush on it), over
//   the working length [-len/2, +len/2], with the rigid gravity-lock bump on its -Y flank (D48). No
//   separate end stop (D34): the case groove's closed -X end stops the rail's -X end face. The rail
//   needs no cut in the consumer's plate (D50): the consumer unions it on and keeps its other plate
//   features out of mcc_rail_male_keepout().
// Arguments:
//   len    = working length, mm. Default: MCC_RAIL_LEN. Must match the female cut's `len`.
//   lock_e = lock bump protrusion, mm. Default: MCC_RAIL_LOCK_ENGAGE. Only the rail-lock coupon's
//            e-ladder passes another value, and always the same one to mcc_rail_female_cut().
module mcc_rail_male(len = MCC_RAIL_LEN, lock_e = MCC_RAIL_LOCK_ENGAGE) {
    g = _mcc_rail_lock_geom(len, lock_e);
    // T1-64 (D48): the bump rides over the groove flank inside the dovetail's own flank play
    // (2 x MCC_RAIL_CLR_HORIZ), with MCC_RAIL_LOCK_PLAY_MARGIN to spare -- nothing is designed to flex.
    assert(0 < lock_e && lock_e + MCC_RAIL_LOCK_PLAY_MARGIN <= 2 * MCC_RAIL_CLR_HORIZ + MCC_EPS,
        str("mcc: T1-64 rail lock bump ", lock_e, " + margin ", MCC_RAIL_LOCK_PLAY_MARGIN,
            " does not fit the flank play ", 2 * MCC_RAIL_CLR_HORIZ));
    // T1-65 (D48): exit face 75..90 deg to the slide axis (90 = square, self-locking at any friction),
    // entry ramp 15..60 deg, and the whole bump inside the working length.
    assert(75 <= MCC_RAIL_LOCK_RAMP_OUT && MCC_RAIL_LOCK_RAMP_OUT <= 90,
        str("mcc: T1-65 rail lock exit face ", MCC_RAIL_LOCK_RAMP_OUT, " deg outside 75..90"));
    assert(15 <= MCC_RAIL_LOCK_RAMP_IN && MCC_RAIL_LOCK_RAMP_IN <= 60,
        str("mcc: T1-65 rail lock entry ramp ", MCC_RAIL_LOCK_RAMP_IN, " deg outside 15..60"));
    assert(-len / 2 + 5 < g[0] && g[1] < len / 2 - 1,
        str("mcc: T1-65 rail lock bump x=", [g[0], g[1]], " does not fit inside len=", len));

    union() {
        // D44: no pedestal -- the taper stands directly on the consumer's plate (local Z=0),
        // MCC_RAIL_ROOF_CLR short of the groove roof.
        _mcc_rail_taper(len, h = MCC_RAIL_MALE_H);
        // D48: the lock bump, swept up the -Y flank from the plate top to the core's own top. It
        // stands on the plate at Z=0 and fuses to it: it is rigid by design.
        _mcc_rail_flank_extrude(0, MCC_RAIL_MALE_H) _mcc_rail_lock_2d(len, lock_e);
    }
}

// Module: mcc_rail_female_cut()
// Usage:
//   mcc_rail_female_cut([len=], [open_ext=], [entry_x=], [lock_e=]);
// Description:
//   SUBTRACTIVE. The matching dovetail groove (case-floor side): the shared taper widened by
//   MCC_RAIL_CLR_HORIZ per side (at least MCC_RAIL_MATE_CLR normal to the flanks, D44), from its
//   CLOSED -X end (the end stop, D34) at -len/2 through +len/2 and on by `open_ext` -- the passage
//   the male enters through, which the case runs out through its +X wall. Plus the gravity-lock
//   pocket in the -Y flank (the bump's outline grown by MCC_RAIL_CLR_HORIZ, following the flank, over
//   the groove's full depth -- D48) and, when `entry_x` is given, a 45-degree lead-in where the
//   groove leaves the part: flanks and mouth flare by MCC_RAIL_LEADIN per side over the last
//   MCC_RAIL_LEADIN mm before the face at X = entry_x; the roof stays at MCC_RAIL_DEPTH (D48). Local
//   frame: mouth at Z=0 = the case's exterior floor face, +Z into the case; a MCC_EPS overlap below
//   Z=0 pierces that face cleanly.
//   T1-38 (rev 9 R1): at least MCC_FLOOR_T of floor remains above the groove over the working length.
// Arguments:
//   len      = working length, mm. Default: MCC_RAIL_LEN. Must match the mating mcc_rail_male().
//   open_ext = how far the groove continues past +len/2 (the insertion passage), mm. Default 0.
//   entry_x  = X of the outer face the groove leaves through (a case: its +X wall, L/2), mm. Default
//              undef = no lead-in. Must lie in [len/2, len/2 + open_ext].
//   lock_e   = lock bump protrusion, mm. Default MCC_RAIL_LOCK_ENGAGE -- always the male's value.
module mcc_rail_female_cut(len = MCC_RAIL_LEN, open_ext = 0, entry_x = undef, lock_e = MCC_RAIL_LOCK_ENGAGE) {
    assert(MCC_FLOOR_T - MCC_EPS <= MCC_RAIL_SILL_H - MCC_RAIL_DEPTH,
        str("mcc: rail_female_cut T1-38 residual floor over the groove = ",
            MCC_RAIL_SILL_H - MCC_RAIL_DEPTH, " below the MCC_FLOOR_T (", MCC_FLOOR_T, ") minimum"));
    // T1-62 (D44): at least MCC_RAIL_MATE_CLR on every non-bearing face -- normal to the flanks, and
    // at the roof over the male's (and the lock bump's) shortened top.
    assert(MCC_RAIL_MATE_CLR - MCC_EPS <= MCC_RAIL_CLR_HORIZ * sin(MCC_RAIL_FLANK_ANGLE),
        str("mcc: T1-62 rail flank clearance ", MCC_RAIL_CLR_HORIZ * sin(MCC_RAIL_FLANK_ANGLE),
            " mm normal, below MCC_RAIL_MATE_CLR=", MCC_RAIL_MATE_CLR));
    assert(MCC_RAIL_MATE_CLR - MCC_EPS <= MCC_RAIL_DEPTH - MCC_RAIL_MALE_H,
        str("mcc: T1-62 rail roof clearance ", MCC_RAIL_DEPTH - MCC_RAIL_MALE_H,
            " mm, below MCC_RAIL_MATE_CLR=", MCC_RAIL_MATE_CLR));
    // T1-66 (D48): the sill side wall behind the lock pocket keeps at least MCC_WALL/2 at the roof,
    // and the lead-in stays inside the wall it is cut into.
    assert(MCC_WALL / 2 - MCC_EPS <= MCC_RAIL_SILL_SIDE_W - MCC_RAIL_CLR_HORIZ - lock_e,
        str("mcc: T1-66 sill wall behind the rail lock pocket = ",
            MCC_RAIL_SILL_SIDE_W - MCC_RAIL_CLR_HORIZ - lock_e, " mm, below MCC_WALL/2"));
    assert(MCC_RAIL_LEADIN <= MCC_WALL + MCC_EPS,
        str("mcc: T1-66 rail lead-in ", MCC_RAIL_LEADIN, " mm deeper than MCC_WALL=", MCC_WALL));
    assert(is_undef(entry_x) || (len / 2 - MCC_EPS <= entry_x && entry_x <= len / 2 + open_ext + MCC_EPS),
        str("mcc: rail_female_cut entry_x=", entry_x, " outside [len/2, len/2 + open_ext]"));
    clr = MCC_RAIL_CLR_HORIZ;

    union() {
        // No Z shift: _mcc_rail_taper_eps() already pierces Z=0 with its own slab, so the groove roof
        // sits at exactly MCC_RAIL_DEPTH.
        translate([open_ext / 2, 0, 0])
            _mcc_rail_taper_eps(len + open_ext, clr, MCC_EPS);
        // D48: the lock pocket, over the groove's FULL depth, so the bump (which stops at
        // MCC_RAIL_MALE_H) keeps MCC_RAIL_ROOF_CLR above its top and MCC_RAIL_CLR_HORIZ around it.
        _mcc_rail_flank_extrude(-MCC_EPS, MCC_RAIL_DEPTH)
            _mcc_rail_lock_2d(len, lock_e, grow = clr);
        // D48: the DP48-style 45-degree lead-in at the outer face the male enters through.
        if (!is_undef(entry_x))
            hull() {
                translate([entry_x - MCC_RAIL_LEADIN, 0, 0])
                    _mcc_rail_taper_eps(MCC_EPS, clr, MCC_EPS);
                translate([entry_x + MCC_EPS, 0, 0])
                    _mcc_rail_taper_eps(MCC_EPS, clr + MCC_RAIL_LEADIN, MCC_EPS);
            }
    }
}

// Module: _mcc_rail_taper_eps()
// Description:
//   Private. _mcc_rail_taper() at its true [0, MCC_RAIL_DEPTH], plus a thin slab at the mouth width
//   spanning [-eps, 0], so the cut pierces the caller's own Z=0 face cleanly (manifold-avoidance).
//   Nothing is shifted: D44 removed the caller's extra -eps shift, which lowered the groove roof.
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
