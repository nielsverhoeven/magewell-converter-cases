//////////////////////////////////////////////////////////////////////
// LibFile: mcc/rail.scad
//   L1. Tool-less dovetail mount-rail interface (issue #25, replaces VESA — D-15, rev 9). Owns the
//   ONE cross-section shared by both mating halves so they can never drift apart (D6 precedent,
//   architecture.md §5 rev 5): mcc_rail_male() (bracket-side, additive), mcc_rail_female_cut()
//   (case-floor-side, subtractive) and mcc_rail_female_backing() (case-floor-side, additive: the
//   material over the lock's roof slot, T1-38), plus the pure accessors mcc_rail_sill_size(),
//   mcc_rail_lock_slot(), mcc_rail_z_play() and mcc_rail_male_keepout() (the plate-side keep-out every
//   bracket reads -- D50). NOT named bracket.scad (architecture.md §3 rev 9, R4/layout-patch-wall.md
//   §17.2): the name describes the INTERFACE, not one of its two consumers -- a file named for a
//   consumer invites bracket-plate/hole/rib geometry (per-bracket assembly work) into an L1 provider.
//   `layout.scad` must NOT `use` this file (architecture.md §3) — the "mount_rail" floor keep-out
//   row is built from the MCC_RAIL_* L0 constants only, never from mcc_rail_sill_size().
//   `use`d by lib/mcc/mounts.scad (the female groove, case floor) and, via the barrel, by
//   models/brackets/*.scad and models/coupons/rail-lock.scad.
// Includes:
//   include <mcc/mcc.scad>
//////////////////////////////////////////////////////////////////////

include <BOSL2/std.scad>
include <constants.scad>
use <util.scad>

// -----------------------------------------------------------------------------------------
// Local frame (shared by every module here): long axis (slide axis) = local X, spanning [-len/2,
// +len/2] for the working (dovetail) length; local Y = across the dovetail's width, centred on 0;
// local Z = depth/height, Z=0 at the mating surface (the bracket plate's top face for the male; the
// case's exterior floor face for the female), +Z runs INTO the case. Single insertion direction
// (PLAN-ASSUMPTION-2, RATIFIED, layout-patch-wall.md §17.5; ends fixed by D34): the case groove is OPEN
// at +X -- it runs out through the case's +X wall (mcc_rail_female_cut()'s `open_ext`) -- and CLOSED at
// -X, the end stop the male's -X face runs into; the case sill carries MCC_RAIL_END_WALL of solid
// material beyond it (D64.1). The male slides in -X relative to the case.
//
// Cross-section: a dovetail, narrow (MCC_RAIL_MOUTH_W) at the mating surface -- local Z=0 on BOTH
// halves (D44: male-local = female-local, Z included) -- widening to MCC_RAIL_ROOT_W at Z=MCC_RAIL_DEPTH,
// the groove roof. WIDE material sits DEEPER inside the groove, so the case cannot be lifted straight
// off the bracket; only sliding along X clears the interlock. At full mate the case's flat exterior
// floor rests FLUSH on the bracket plate outside the two footprints. The male stands MCC_RAIL_MALE_H
// tall (MCC_RAIL_ROOF_CLR short of the roof) and the groove is offset MCC_RAIL_CLR_HORIZ per side, so
// every other face has >= MCC_RAIL_MATE_CLR (T1-62).
//
// Lock (D63.1, user decision 2026-09-29 -- replaces the D48 flank bump): two rigid strips on the male's
// flat top, near its +X (trailing) end, drop into one transverse slot across the groove roof's full
// width at full insertion. A mounted case hangs patch-wall down (D49) on the rail's upper (-Y) flank,
// whose wedge presses the case floor onto the plate and holds the strips in the slot. The strips' exit
// faces (+X) are square; their entry sides (-X) carry a MCC_RAIL_LOCK_RAMP_IN chamfer, and the groove's
// +X entry carries a MCC_RAIL_LEADIN roof chamfer, so sliding on the case rides over them inside the
// joint's own Z-play (T1-63.1). Release: move the case about 1 mm away from the plate, then slide it off.
// -----------------------------------------------------------------------------------------

// Function: mcc_rail_sill_size()
// Usage:
//   sz = mcc_rail_sill_size();
// Description:
//   Pure. [length, width, height] of the case-floor sill the groove is cut into -- the working length
//   plus MCC_RAIL_END_WALL at each end (D64.1) -- for BOM/preview use. NOT `use`d by layout.scad
//   (architecture.md §3 rev 9: that file builds its "mount_rail" keep-out row from the MCC_RAIL_*
//   constants directly, never from this function).
function mcc_rail_sill_size() =
    [MCC_RAIL_LEN + 2 * MCC_RAIL_END_WALL, MCC_RAIL_ROOT_W + 2 * MCC_RAIL_SILL_SIDE_W, MCC_RAIL_SILL_H];

// Module: _mcc_rail_taper()
// Description:
//   Private. The dovetail taper alone: a prismoid from MCC_RAIL_MOUTH_W at local Z=0, widening along
//   the flank's own slope for `h` mm, length `len` along X, centred on Y=0, anchored BOTTOM. The female
//   groove uses the full MCC_RAIL_DEPTH (top width == MCC_RAIL_ROOT_W exactly); the male stops at
//   MCC_RAIL_MALE_H with the SAME slope (D44), so the two profiles can never drift.
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

// Function: _mcc_rail_flank_k()
// Description: Private. Outward run of a flank per mm of height over the taper (0.577 at 60 deg).
function _mcc_rail_flank_k() = (MCC_RAIL_ROOT_W - MCC_RAIL_MOUTH_W) / (2 * MCC_RAIL_DEPTH);

// Function: mcc_rail_z_play()
// Usage:
//   zp = mcc_rail_z_play();   // = 1.0 at MCC_RAIL_MATE_CLR 0.5 and 60 deg flanks
// Description:
//   Pure. How far the case can move away from the plate, rigidly, before both flanks bind:
//   MCC_RAIL_CLR_HORIZ / flank slope (= MCC_RAIL_MATE_CLR / cos(MCC_RAIL_FLANK_ANGLE)). The lock strips'
//   ride must fit inside it with MCC_RAIL_LOCK_PLAY_MARGIN to spare (T1-63.1).
function mcc_rail_z_play() = MCC_RAIL_CLR_HORIZ / _mcc_rail_flank_k();

// -----------------------------------------------------------------------------------------
// Lock geometry (D63.1). Everything derives from the caller's own `len`, so the 60 mm coupon works.
// -----------------------------------------------------------------------------------------

// Function: _mcc_rail_lock_x()
// Description:
//   Private, pure. [x0, x1] of each lock strip's base along the slide axis for a rail of working
//   length `len`: x1 = the square exit face, MCC_RAIL_LOCK_END_OFFSET inside the male's +X end;
//   x0 = x1 - MCC_RAIL_LOCK_STRIP_X. The male slides in -X relative to the case, so x0 (the chamfered
//   entry side) meets the groove's roof chamfer first; withdrawing, the slot's +X wall meets x1.
function _mcc_rail_lock_x(len) =
    let(x1 = len / 2 - MCC_RAIL_LOCK_END_OFFSET) [x1 - MCC_RAIL_LOCK_STRIP_X, x1];

// Module: _mcc_rail_xz_prism()
// Description:
//   Private. Extrudes an outline drawn in the XZ plane (a list of [x, z] points) along +Y, from y0 to y1.
module _mcc_rail_xz_prism(pts, y0, y1) {
    translate([0, y1, 0]) rotate([90, 0, 0]) linear_extrude(height = y1 - y0) polygon(pts);
}

// Module: _mcc_rail_lock_strips()
// Description:
//   Private. The two lock strips on the male's top, mirrored in Y. Each spans [x0, x1] along X and
//   [MCC_RAIL_LOCK_STRIP_Y_IN, MCC_RAIL_LOCK_STRIP_Y_OUT] in |y|: square exit face at x1; the entry side
//   rises vertically to the roof line (Z = MCC_RAIL_DEPTH), then chamfers at MCC_RAIL_LOCK_RAMP_IN over
//   the engaged height `e`; flat top at Z = MCC_RAIL_DEPTH + e. Each starts 0.2 mm inside the male's top
//   so the union shares real volume.
module _mcc_rail_lock_strips(len, e) {
    x = _mcc_rail_lock_x(len);
    ramp = e / tan(MCC_RAIL_LOCK_RAMP_IN);
    z0 = MCC_RAIL_MALE_H - 0.2;
    zr = MCC_RAIL_DEPTH;
    zt = MCC_RAIL_DEPTH + e;
    pts = [[x[0], z0], [x[0], zr], [x[0] + ramp, zt], [x[1], zt], [x[1], z0]];
    _mcc_rail_xz_prism(pts, MCC_RAIL_LOCK_STRIP_Y_IN, MCC_RAIL_LOCK_STRIP_Y_OUT);
    _mcc_rail_xz_prism(pts, -MCC_RAIL_LOCK_STRIP_Y_OUT, -MCC_RAIL_LOCK_STRIP_Y_IN);
}

// Function: mcc_rail_lock_slot()
// Usage:
//   b = mcc_rail_lock_slot([len], [lock_e]);   // [[x_lo, x_hi], [y_lo, y_hi], [z_lo, z_hi]]
// Description:
//   Pure. The case-side roof slot the strips drop into, rail-local: the strips' X span grown by
//   MCC_RAIL_MATE_CLR each side, the groove roof's full width (flank to flank at Z = MCC_RAIL_DEPTH),
//   from the roof up to MCC_RAIL_ROOF_CLR above the strips' tops. One full-width slot, never separate
//   pockets: a hole inside the roof bridge is a floating cantilever to the slicer (D33, D63.1).
// Arguments:
//   len    = working length, mm. Default: MCC_RAIL_LEN.
//   lock_e = strip engagement above the roof line, mm. Default: MCC_RAIL_LOCK_ENGAGE.
function mcc_rail_lock_slot(len = MCC_RAIL_LEN, lock_e = MCC_RAIL_LOCK_ENGAGE) =
    let(
        x = _mcc_rail_lock_x(len),
        hw = MCC_RAIL_ROOT_W / 2 + MCC_RAIL_CLR_HORIZ
    )
    [[x[0] - MCC_RAIL_MATE_CLR, x[1] + MCC_RAIL_MATE_CLR],
     [-hw, hw],
     [MCC_RAIL_DEPTH, MCC_RAIL_DEPTH + lock_e + MCC_RAIL_ROOF_CLR]];

// Module: mcc_rail_female_backing()
// Usage:
//   union() { sill(); mcc_rail_female_backing([len=], [lock_e=]); }
// Description:
//   ADDITIVE (case side). The material over the roof slot that keeps T1-38 true there: the slot's X
//   span grown by MCC_WALL each side, the sill's full width, from the sill top (Z = MCC_RAIL_SILL_H) up
//   by the slot's own height above the roof. The caller unions it with its sill (mounts.scad) or its
//   coupon plinth, in the same rail-local placement as its mcc_rail_female_cut().
// Arguments:
//   len    = working length, mm. Default: MCC_RAIL_LEN. Must match the female cut's `len`.
//   lock_e = strip engagement, mm. Default: MCC_RAIL_LOCK_ENGAGE. Must match the female cut's.
module mcc_rail_female_backing(len = MCC_RAIL_LEN, lock_e = MCC_RAIL_LOCK_ENGAGE) {
    b = mcc_rail_lock_slot(len, lock_e);
    h = b[2][1] - b[2][0];
    sw = MCC_RAIL_ROOT_W / 2 + MCC_RAIL_SILL_SIDE_W;
    // T1-38 (D63.1): at least MCC_FLOOR_T of material over the slot's ceiling too.
    assert(MCC_RAIL_SILL_H + h - b[2][1] >= MCC_FLOOR_T - MCC_EPS,
        str("mcc: rail_female_backing T1-38 residual over the lock slot = ", MCC_RAIL_SILL_H + h - b[2][1],
            " below MCC_FLOOR_T=", MCC_FLOOR_T));
    translate([b[0][0] - MCC_WALL, -sw, MCC_RAIL_SILL_H - MCC_EPS])
        cube([b[0][1] - b[0][0] + 2 * MCC_WALL, 2 * sw, h + MCC_EPS]);
}

// Function: mcc_rail_male_keepout()
// Usage:
//   ko = mcc_rail_male_keepout([len]);   // [[x_min, x_max], [y_min, y_max]]
// Description:
//   Pure. The conservative plan-view extent, in the shared rail-local frame, of everything
//   mcc_rail_male() puts on or into a consumer's plate: the taper, bounded by MCC_RAIL_ROOT_W (wider
//   than the male's own MCC_RAIL_MALE_H top). The lock strips sit on that top, inside it (D63.1). The rail
//   needs no cut in the plate (D50): a consumer unions mcc_rail_male() onto its plate and keeps its other
//   plate features out of this rectangle, adding its own clearance. A rotate([0,0,180]) placement
//   negates and swaps both ranges. Brackets read this, never the MCC_RAIL_LOCK_* constants
//   (architecture.md §3, D50).
// Arguments:
//   len = working length, mm. Default: MCC_RAIL_LEN.
function mcc_rail_male_keepout(len = MCC_RAIL_LEN) =
    [[-len / 2, len / 2], [-MCC_RAIL_ROOT_W / 2, MCC_RAIL_ROOT_W / 2]];

// Module: mcc_rail_male()
// Usage:
//   union() { plate(); mcc_rail_male([len=]); }
// Description:
//   ADDITIVE. The male dovetail rail (bracket side): the shared taper, MCC_RAIL_MALE_H tall, standing
//   directly on the consumer's plate (no pedestal since D44), over the working length [-len/2, +len/2],
//   with the two lock strips on its top near its +X end (D63.1). No separate end stop (D34): the case
//   groove's closed -X end stops the rail's -X end face. The rail needs no cut in the consumer's plate
//   (D50): the consumer unions it on and keeps its other plate features out of mcc_rail_male_keepout().
// Arguments:
//   len    = working length, mm. Default: MCC_RAIL_LEN. Must match the female cut's `len`.
//   lock_e = strip engagement above the roof line, mm. Default: MCC_RAIL_LOCK_ENGAGE. Only the rail-lock
//            coupon's e-ladder passes another value, and always the same one to mcc_rail_female_cut()
//            and mcc_rail_female_backing().
module mcc_rail_male(len = MCC_RAIL_LEN, lock_e = MCC_RAIL_LOCK_ENGAGE) {
    x = _mcc_rail_lock_x(len);
    top_hw = MCC_RAIL_MOUTH_W / 2 + MCC_RAIL_MALE_H * _mcc_rail_flank_k();
    // T1-63.1 (D63.1): the case rides over the strips inside the joint's own Z-play, with
    // MCC_RAIL_LOCK_PLAY_MARGIN to spare -- nothing is designed to flex.
    assert(0 < lock_e && lock_e + MCC_RAIL_LOCK_PLAY_MARGIN <= mcc_rail_z_play() + MCC_EPS,
        str("mcc: T1-63.1 rail lock strip ", lock_e, " + margin ", MCC_RAIL_LOCK_PLAY_MARGIN,
            " does not fit the Z-play ", mcc_rail_z_play()));
    // T1-63.2 (D63.1): the entry chamfer is 30..60 deg and shorter than the strip; the strips sit inside the
    // male's top with >= 1 mm to its edges, and inside the working length.
    assert(30 <= MCC_RAIL_LOCK_RAMP_IN && MCC_RAIL_LOCK_RAMP_IN <= 60
        && lock_e / tan(MCC_RAIL_LOCK_RAMP_IN) < MCC_RAIL_LOCK_STRIP_X,
        str("mcc: T1-63.2 rail lock entry chamfer ", MCC_RAIL_LOCK_RAMP_IN,
            " deg outside 30..60 or longer than the strip"));
    assert(0 <= MCC_RAIL_LOCK_STRIP_Y_IN && MCC_RAIL_LOCK_STRIP_Y_IN < MCC_RAIL_LOCK_STRIP_Y_OUT
        && MCC_RAIL_LOCK_STRIP_Y_OUT <= top_hw - 1,
        str("mcc: T1-63.2 rail lock strips |y| ", [MCC_RAIL_LOCK_STRIP_Y_IN, MCC_RAIL_LOCK_STRIP_Y_OUT],
            " not inside the male's top (half-width ", top_hw, ")"));
    assert(-len / 2 + 5 < x[0] && x[1] < len / 2 - 1,
        str("mcc: T1-63.2 rail lock strips x=", x, " do not fit inside len=", len));

    union() {
        // D44: no pedestal -- the taper stands directly on the consumer's plate (local Z=0),
        // MCC_RAIL_ROOF_CLR short of the groove roof.
        _mcc_rail_taper(len, h = MCC_RAIL_MALE_H);
        // D63.1: the lock strips on the male's top.
        _mcc_rail_lock_strips(len, lock_e);
    }
}

// Module: mcc_rail_female_cut()
// Usage:
//   mcc_rail_female_cut([len=], [open_ext=], [entry_x=], [lock_e=]);
// Description:
//   SUBTRACTIVE. The matching dovetail groove (case-floor side): the shared taper widened by
//   MCC_RAIL_CLR_HORIZ per side (at least MCC_RAIL_MATE_CLR normal to the flanks, D44), from its
//   CLOSED -X end (the end stop, D34) at -len/2 through +len/2 and on by `open_ext` -- the passage the
//   male enters through, which the case runs out through its +X wall. Plus the lock's roof slot
//   (mcc_rail_lock_slot(), D63.1) and, when `entry_x` is given, a 45-degree lead-in where the groove leaves
//   the part: flanks, mouth and roof flare by MCC_RAIL_LEADIN over the last MCC_RAIL_LEADIN mm before the
//   face at X = entry_x (D63.1). Local frame: mouth at Z=0 = the case's exterior floor face, +Z into the
//   case; a MCC_EPS overlap below Z=0 pierces that face cleanly. The caller must leave at least
//   MCC_RAIL_END_WALL of solid material beyond X = -len/2 over the groove's full depth (T1-64.1) and
//   union mcc_rail_female_backing() over the slot (T1-38).
// Arguments:
//   len      = working length, mm. Default: MCC_RAIL_LEN. Must match the mating mcc_rail_male().
//   open_ext = how far the groove continues past +len/2 (the insertion passage), mm. Default 0.
//   entry_x  = X of the outer face the groove leaves through (a case: its +X wall, L/2), mm. Default
//              undef = no lead-in. Must lie in [len/2, len/2 + open_ext].
//   lock_e   = strip engagement, mm. Default MCC_RAIL_LOCK_ENGAGE -- always the male's value.
module mcc_rail_female_cut(len = MCC_RAIL_LEN, open_ext = 0, entry_x = undef, lock_e = MCC_RAIL_LOCK_ENGAGE) {
    assert(MCC_FLOOR_T - MCC_EPS <= MCC_RAIL_SILL_H - MCC_RAIL_DEPTH,
        str("mcc: rail_female_cut T1-38 residual floor over the groove = ",
            MCC_RAIL_SILL_H - MCC_RAIL_DEPTH, " below the MCC_FLOOR_T (", MCC_FLOOR_T, ") minimum"));
    // T1-62 (D44): at least MCC_RAIL_MATE_CLR on every non-bearing face -- normal to the flanks, and
    // at the roof over the male's shortened top (the slot keeps the same clearance around the strips).
    assert(MCC_RAIL_MATE_CLR - MCC_EPS <= MCC_RAIL_CLR_HORIZ * sin(MCC_RAIL_FLANK_ANGLE),
        str("mcc: T1-62 rail flank clearance ", MCC_RAIL_CLR_HORIZ * sin(MCC_RAIL_FLANK_ANGLE),
            " mm normal, below MCC_RAIL_MATE_CLR=", MCC_RAIL_MATE_CLR));
    assert(MCC_RAIL_MATE_CLR - MCC_EPS <= MCC_RAIL_DEPTH - MCC_RAIL_MALE_H,
        str("mcc: T1-62 rail roof clearance ", MCC_RAIL_DEPTH - MCC_RAIL_MALE_H,
            " mm, below MCC_RAIL_MATE_CLR=", MCC_RAIL_MATE_CLR));
    // T1-63.3 (D63.1): the roof lead-in is taller than the strips' engagement, so they meet a ramp and
    // never the face's edge, and it stays inside the wall it is cut into.
    assert(lock_e < MCC_RAIL_LEADIN && MCC_RAIL_LEADIN <= MCC_WALL + MCC_EPS,
        str("mcc: T1-63.3 rail lead-in ", MCC_RAIL_LEADIN, " must exceed the lock engagement ", lock_e,
            " and stay within MCC_WALL=", MCC_WALL));
    assert(is_undef(entry_x) || (len / 2 - MCC_EPS <= entry_x && entry_x <= len / 2 + open_ext + MCC_EPS),
        str("mcc: rail_female_cut entry_x=", entry_x, " outside [len/2, len/2 + open_ext]"));
    clr = MCC_RAIL_CLR_HORIZ;
    b = mcc_rail_lock_slot(len, lock_e);

    union() {
        // No Z shift: _mcc_rail_taper_eps() already pierces Z=0 with its own slab, so the groove roof
        // sits at exactly MCC_RAIL_DEPTH.
        translate([open_ext / 2, 0, 0])
            _mcc_rail_taper_eps(len + open_ext, clr, MCC_EPS);
        // D63.1: the lock's roof slot, flank to flank, so it splits the roof bridge instead of holing it.
        translate([b[0][0], b[1][0], b[2][0] - MCC_EPS])
            cube([b[0][1] - b[0][0], b[1][1] - b[1][0], b[2][1] - b[2][0] + MCC_EPS]);
        // D63.1: the DP48-style 45-degree lead-in at the outer face the male enters through -- the outer
        // slice is both wider and taller, so the roof chamfers as well as the flanks and the mouth.
        if (!is_undef(entry_x))
            hull() {
                translate([entry_x - MCC_RAIL_LEADIN, 0, 0])
                    _mcc_rail_taper_eps(MCC_EPS, clr, MCC_EPS);
                translate([entry_x + MCC_EPS, 0, 0])
                    _mcc_rail_taper_eps(MCC_EPS, clr + MCC_RAIL_LEADIN, MCC_EPS, h = MCC_RAIL_DEPTH + MCC_RAIL_LEADIN);
            }
    }
}

// Module: _mcc_rail_taper_eps()
// Description:
//   Private. _mcc_rail_taper() at its true [0, h], plus a thin slab at the mouth width spanning
//   [-eps, 0], so the cut pierces the caller's own Z=0 face cleanly (manifold-avoidance). Nothing is
//   shifted: D44 removed the caller's extra -eps shift, which lowered the groove roof.
module _mcc_rail_taper_eps(len, clr, eps, h = MCC_RAIL_DEPTH) {
    union() {
        _mcc_rail_taper(len, clr, h);
        // Thin slab at MOUTH width, spanning [-eps, 0] in this module's own shifted frame, so the
        // cut pierces the exterior floor face rather than sharing a coincident face with it.
        translate([0, 0, -eps])
            cuboid([len, MCC_RAIL_MOUTH_W + 2 * clr, eps], anchor = BOTTOM);
    }
}

// vim: expandtab tabstop=4 shiftwidth=4 softtabstop=4 nowrap
