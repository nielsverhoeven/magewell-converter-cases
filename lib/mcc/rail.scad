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
// case. Single insertion direction (PLAN-ASSUMPTION-2, RATIFIED, layout-patch-wall.md §17.5): the
// latch sits near the OPEN end (-X, MCC_RAIL_LATCH_X), the end-stop flange beyond the CLOSED end
// (+X, outside the working length — see constants.scad's MCC_RAIL_END_STOP_* comment for why it
// must be a WIDTH feature, not a height bump).
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
function mcc_rail_sill_size() = [MCC_RAIL_LEN, MCC_RAIL_ROOT_W, MCC_RAIL_SILL_H];

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

// Module: mcc_rail_male()
// Usage:
//   mcc_rail_male([len=]);
// Description:
//   ADDITIVE. The male dovetail rail (bracket-side; #26/#27 place this on their own plate — this
//   branch, #25, only has to expose it) plus its integrated end-stop flange (closed/+X end, beyond
//   `len`) and spring-lip latch tab (open/-X end, near MCC_RAIL_LATCH_X) — docs/plans/2026-09-09-
//   mount-rail-and-brackets.md §1.1 "Latch flex direction". Local frame: base (pedestal foot, meets
//   the bracket plate) at Z=0, rising to Z=MCC_RAIL_SILL_H (pedestal MCC_FLOOR_T tall + taper
//   MCC_RAIL_DEPTH tall); the dovetail's WORKING length is centred on (X=0, Y=0), spanning
//   [-len/2, +len/2] — matching a female cut of the same `len` exactly — with the end-stop flange
//   extending a further MCC_RAIL_END_STOP_L beyond +len/2 (outside the female's own footprint by
//   design, see constants.scad's MCC_RAIL_END_STOP_* comment for why).
//   Latch mechanism (first-pass geometry, calibrated on models/coupons/rail-latch.scad — Tier-4,
//   architecture.md §9): a cantilever arm (MCC_RAIL_LATCH_ARM_L x MCC_RAIL_LATCH_ARM_T x
//   MCC_RAIL_LATCH_W, L/t=8.75 >= 8:1 per fasteners-and-hardware.md:133, root fillet
//   MCC_RAIL_LATCH_ROOT_FILLET >= 0.5x the arm thickness per fasteners-and-hardware.md:134) stands
//   flush with the rail's own nominal ROOT_W/2 flank line (never protruding along its own body, so
//   it cannot collide with anything during the slide) and flexes sideways in Y — the FDM-strong
//   axis for a plate that prints flat (fasteners-and-hardware.md:137) — fixed at its root end (away
//   from MCC_RAIL_LATCH_X) and free at its tip (at MCC_RAIL_LATCH_X). Only a small engagement NUB
//   at the tip, positioned near the groove's mouth (case-local Z close to 0, well inside the
//   groove's own MCC_RAIL_DEPTH-deep working envelope — never above MCC_RAIL_SILL_H, so it can
//   never intrude on the MCC_FLOOR_T of residual floor T1-38 protects), pokes MCC_RAIL_LATCH_ENGAGE
//   further -Y than the nominal flank; mcc_rail_female_cut() carries the matching pocket at the
//   identical (X,Z) window plus the thumb-release access slot.
// Arguments:
//   len = dovetail WORKING length along the slide axis, mm (matches the female cut's own `len`).
//         Default: MCC_RAIL_LEN. The rail's total physical footprint is
//         len + MCC_RAIL_END_STOP_L (the end-stop flange sits beyond +len/2).
module mcc_rail_male(len = MCC_RAIL_LEN) {
    latch_x = -len / 2 + MCC_RAIL_LATCH_LEAD_IN; // re-derived from THIS caller's own `len`, not
        // read from MCC_RAIL_LATCH_X directly — that constant is fixed to MCC_RAIL_LEN, so a
        // shorter test length (models/coupons/rail-latch.scad) would place it out of bounds.
    assert(len > MCC_RAIL_LATCH_ARM_L + 40,
        str("mcc: rail_male len=", len, " too short to carry the latch with reasonable margin"));
    // Latch-stress asserts (docs/plans/2026-09-09-mount-rail-and-brackets.md §1.5): a future edit to
    // either constant fails at render instead of silently violating the snap-fit rule.
    assert(MCC_RAIL_LATCH_ARM_L / MCC_RAIL_LATCH_ARM_T >= 8,
        str("mcc: rail latch L/t=", MCC_RAIL_LATCH_ARM_L / MCC_RAIL_LATCH_ARM_T,
            " below the 8:1 minimum (fasteners-and-hardware.md:133)"));
    assert(MCC_RAIL_LATCH_ROOT_FILLET >= 0.5 * MCC_RAIL_LATCH_ARM_T,
        str("mcc: rail latch root fillet=", MCC_RAIL_LATCH_ROOT_FILLET,
            " below 0.5x the arm thickness (fasteners-and-hardware.md:134)"));
    assert(latch_x > -len / 2 && latch_x - MCC_RAIL_LATCH_ARM_L > -len / 2,
        str("mcc: rail latch (x=", latch_x, ", arm_l=", MCC_RAIL_LATCH_ARM_L,
            ") does not fit inside len=", len));

    union() {
        // Pedestal: constant MCC_RAIL_MOUTH_W width, fills the standoff gap below the taper. Runs
        // the full physical length (working length + end-stop flange, [-len/2, len/2+END_STOP_L])
        // for a continuous base -- the cuboid's own default centre is shifted +END_STOP_L/2 so its
        // [-(len+END_STOP_L)/2, (len+END_STOP_L)/2] span lands there.
        translate([MCC_RAIL_END_STOP_L / 2, 0, 0])
            cuboid([len + MCC_RAIL_END_STOP_L, MCC_RAIL_MOUTH_W, MCC_FLOOR_T], anchor = BOTTOM);
        // Taper: the shared dovetail cross-section, riding on top of the pedestal, spanning only
        // the WORKING length (matches the female groove exactly).
        translate([0, 0, MCC_FLOOR_T]) _mcc_rail_taper(len);
        // End-stop flange: beyond the working length entirely (+X), full MCC_RAIL_ROOT_W wide so
        // the case's un-grooved floor (which starts right at the female's own len/2 boundary)
        // cannot pass it — see constants.scad's MCC_RAIL_END_STOP_* comment for the full mechanics.
        translate([len / 2, 0, MCC_FLOOR_T])
            cuboid([MCC_RAIL_END_STOP_L, MCC_RAIL_ROOT_W, MCC_RAIL_DEPTH + MCC_RAIL_END_STOP_H],
                anchor = LEFT + BOTTOM);
        // Latch tab (see module doc comment above for the geometry rationale).
        _mcc_rail_latch_tab(latch_x);
    }
}

// Module: _mcc_rail_latch_tab()
// Description:
//   Private. The spring-lip latch's cantilever arm + engagement nub, in mcc_rail_male()'s own local
//   frame. See mcc_rail_male()'s doc comment for the design rationale.
// Arguments:
//   latch_x = local X of the latch/detent (mcc_rail_male()'s own `-len/2 + MCC_RAIL_LATCH_LEAD_IN`).
module _mcc_rail_latch_tab(latch_x) {
    root_x  = latch_x - MCC_RAIL_LATCH_ARM_L; // fixed (root) end of the cantilever
    y_flank = -MCC_RAIL_ROOT_W / 2; // nominal flank line the arm's body stays flush with
    z0      = MCC_RAIL_SILL_H - MCC_RAIL_LATCH_W;

    // Arm body: its inner (+Y) face is grown MCC_EPS past the nominal flank line, into the rail's
    // own taper/pedestal solid, so the union has a genuine shared volume there instead of a
    // coincident face (a known Manifold/STL-export degeneracy — same class of fix shell.scad's own
    // tongue-frame comment documents, and the one the Tier-3 "one connected shell" check,
    // architecture.md §9, actually catches). MCC_EPS (0.01 mm) is well inside print tolerance and
    // does not meaningfully stiffen the flex. The arm otherwise never protrudes further -Y along its
    // own length — only the nub (below) pokes past it.
    translate([root_x, y_flank - MCC_RAIL_LATCH_ARM_T, z0])
        cuboid([MCC_RAIL_LATCH_ARM_L, MCC_RAIL_LATCH_ARM_T + MCC_EPS, MCC_RAIL_LATCH_W],
            anchor = LEFT + FRONT + BOTTOM);

    // Engagement nub: a short protrusion at the tip, confined to a thin Z band right at the
    // groove's mouth (case-local Z close to 0 -- MCC_FLOOR_T here, in the male's own local frame --
    // well inside the taper's own MCC_RAIL_DEPTH-deep working range, never above MCC_RAIL_SILL_H).
    // Its own inner (+Y) face is likewise grown MCC_EPS past the arm's outer face, for the same
    // genuine-overlap reason.
    nub_l = MCC_RAIL_LATCH_ENGAGE * 2;   // assumed — short discrete catch, prints/mates cleanly.
    nub_h = MCC_RAIL_LATCH_ENGAGE * 1.5; // assumed — thin band near the mouth.
    translate([latch_x - nub_l,
               y_flank - MCC_RAIL_LATCH_ARM_T - MCC_RAIL_LATCH_ENGAGE,
               MCC_FLOOR_T])
        cuboid([nub_l, MCC_RAIL_LATCH_ENGAGE + MCC_EPS, nub_h], anchor = LEFT + FRONT + BOTTOM);
}

// Module: mcc_rail_female_cut()
// Usage:
//   mcc_rail_female_cut([len=]);
// Description:
//   SUBTRACTIVE. The matching dovetail groove (case-floor side): mcc_rail_male()'s taper, widened
//   by MCC_CLR_SLIDE per side for a sliding fit (reused, not a new clearance constant — §1.1 of the
//   plan), plus the latch-detent pocket and the thumb-release access slot. Local frame: open face
//   (mouth) at local Z=0 — this IS the case's exterior floor face, matching every other floor cut
//   in mounts.scad's own "base at world Z=0" convention — extending into +Z by MCC_RAIL_DEPTH, with
//   a small MCC_EPS overlap below Z=0 so the cut genuinely pierces the exterior face rather than
//   merely touching it (same non-manifold-avoidance pattern as
//   _mcc_floor_bore_from_below()/mcc_heat_set_bore() elsewhere in this repo).
//   T1-38 (rev 9 R1, blocking — layout-patch-wall.md §17.2): asserts >= MCC_FLOOR_T of the case's
//   own floor remains solid above the groove — the residual load path when the case is bracket-
//   mounted — rather than the plan's original, weaker ">MCC_RAIL_DEPTH" check.
// Arguments:
//   len = groove length along the slide axis, mm. Default: MCC_RAIL_LEN. Must match the mating
//         mcc_rail_male()'s own `len`.
module mcc_rail_female_cut(len = MCC_RAIL_LEN) {
    assert(MCC_RAIL_SILL_H - MCC_RAIL_DEPTH >= MCC_FLOOR_T - MCC_EPS,
        str("mcc: rail_female_cut T1-38 residual floor over the groove = ",
            MCC_RAIL_SILL_H - MCC_RAIL_DEPTH, " below the MCC_FLOOR_T (", MCC_FLOOR_T, ") minimum"));

    clr = MCC_CLR_SLIDE;
    latch_x = -len / 2 + MCC_RAIL_LATCH_LEAD_IN; // same re-derivation as mcc_rail_male() — see its
                                                   // own comment; keeps the two halves' latch
                                                   // features aligned for any `len`, not just
                                                   // MCC_RAIL_LEN.

    union() {
        // Main groove, with the manifold-avoidance overlap below Z=0.
        translate([0, 0, -MCC_EPS])
            _mcc_rail_taper_eps(len, clr, MCC_EPS);

        // Latch-detent pocket + thumb-release access, at the same (X,Z) window as
        // _mcc_rail_latch_tab()'s nub (mcc_rail_male()'s own local frame, shared by construction).
        _mcc_rail_latch_pocket(latch_x, clr);
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

// Module: _mcc_rail_latch_pocket()
// Description:
//   Private. SUBTRACTIVE: the pocket that receives mcc_rail_male()'s engagement nub, plus a
//   MCC_RAIL_ACCESS_W x MCC_RAIL_ACCESS_L thumb-release access slot alongside it (outside the
//   sill's own MCC_RAIL_ROOT_W footprint, so it never competes with the groove's own residual-floor
//   guarantee — T1-38 only bounds the groove itself). First-pass geometry: the exact reach-in path
//   to press the latch tab flush for release is a physical-coupon question (models/coupons/
//   rail-latch.scad, Tier-4) — this cuts a generous, buildable pocket + slot rather than
//   over-specifying an untested ergonomic detail.
// Arguments:
//   latch_x = local X of the latch/detent (same value the caller, mcc_rail_female_cut(), derived).
//   clr     = per-side sliding clearance, mm (same value mcc_rail_female_cut() itself used).
module _mcc_rail_latch_pocket(latch_x, clr) {
    nub_l   = MCC_RAIL_LATCH_ENGAGE * 2;
    nub_h   = MCC_RAIL_LATCH_ENGAGE * 1.5;
    y_flank = -MCC_RAIL_ROOT_W / 2 - clr; // matches the clearance-widened groove's own flank
    // The nub sits at mcc_rail_male()'s own local Z=[MCC_FLOOR_T, MCC_FLOOR_T+nub_h] (right at the
    // taper's own base, i.e. the mouth level once mated). THIS module is in the FEMALE's own local
    // frame, whose Z=0 already IS the mouth (no pedestal offset) — the two frames differ by exactly
    // MCC_FLOOR_T (female_z = male_z - MCC_FLOOR_T), so the matching pocket sits at female
    // Z=[0, nub_h].
    z0 = 0;

    // Pocket: generous margin around the nub's own footprint so it seats without binding.
    translate([latch_x - nub_l - 1, y_flank - MCC_RAIL_LATCH_ENGAGE - 1, z0 - 1])
        cuboid([nub_l + 2, MCC_RAIL_LATCH_ENGAGE + 2, nub_h + 2], anchor = LEFT + FRONT + BOTTOM);

    // Thumb-release access: a through-slot from the case's exterior floor face up to the nub's own
    // Z band, positioned at the sill's own -Y edge but kept INSIDE the MCC_RAIL_ROOT_W footprint
    // (never reaching past it in Y) so it can never intrude on a neighbouring floor keep-out (the
    // splitter bay sits close outside the sill at MCC_RAIL_Y=-20, layout-patch-wall.md §1.4) —
    // reachability from outside the assembled case is exactly the open question
    // models/coupons/rail-latch.scad exists to answer; this stays a safe, buildable cut in the
    // meantime.
    translate([latch_x - MCC_RAIL_ACCESS_L / 2,
               -MCC_RAIL_ROOT_W / 2 - clr,
               -MCC_EPS])
        cuboid([MCC_RAIL_ACCESS_L, min(MCC_RAIL_ACCESS_W, MCC_RAIL_ROOT_W), MCC_FLOOR_T + MCC_EPS],
            anchor = LEFT + FRONT + BOTTOM);
}

// vim: expandtab tabstop=4 shiftwidth=4 softtabstop=4 nowrap
