//////////////////////////////////////////////////////////////////////
// LibFile: mcc/fasteners.scad
//   L1. Heat-set insert bosses/bores, captive thumbscrew holes, the captive side bolt (D-09,
//   device retention through the far wall — .claude/knowledge/layout-patch-wall.md §7.1), the
//   case's own 1/4"-20 floor mounting insert, and a generic M4 clearance hole.
//   knowledge/components/fasteners-and-hardware.md §1-2. `use`d by lib/mcc/mcc.scad.
// Includes:
//   include <mcc/mcc.scad>
//////////////////////////////////////////////////////////////////////

include <BOSL2/std.scad>
include <constants.scad>
use <util.scad>

// Z-axis convention: a boss stands with its base at Z=0 and grows to Z=h (anchor=BOTTOM); a
// panel/lid feature (mcc_captive_thumbscrew_hole) spans Z=[0, lid_t] with the outward face at
// Z=lid_t, matching lib/mcc/neutrik.scad's own convention.

// Module: mcc_heat_set_bore()
// Usage:
//   mcc_heat_set_bore([insert=]);
// Description:
//   Negative (subtractive) blind bore for a heat-set insert. Local frame: the open face is at
//   Z=0 (place with `translate([x,y,z_of_open_face]) mcc_heat_set_bore(...)`), extending blind
//   into -Z by `insert.len + 1` mm.
// Arguments:
//   insert = insert record (constants.scad MCC_INSERT_M3 shape: hole_d/od/len). Default: MCC_INSERT_M3.
module mcc_heat_set_bore(insert = MCC_INSERT_M3) {
    insert_hole_d = struct_val(insert, "hole_d");
    insert_len    = struct_val(insert, "len");
    // MCC_INSERT_M3 len (5.7, knowledge/components/fasteners-and-hardware.md:17) + 1 mm clearance
    // past the insert's own length, per this file's module contract.
    depth = insert_len + 1;
    translate([0, 0, MCC_EPS - depth / 2])
        cyl(h = depth + 2 * MCC_EPS, d = insert_hole_d, circum = true, $fn = 64);
}

// Module: mcc_heat_set_boss()
// Usage:
//   mcc_heat_set_boss([insert=], h, [od=]);
// Description:
//   Additive boss (base at Z=0, top at Z=h) with an integral blind heat-set-insert bore opening
//   at the top. Asserts the OD/insert-OD ratio and the minimum 2 mm wall around the bore
//   (architecture.md:348 "heat-set boss OD >= 1.8 x insert OD, >= 2 mm material to any edge").
// Arguments:
//   insert = insert record. Default: MCC_INSERT_M3.
//   h      = boss height, mm (required — must be >= insert.len + 1).
//   od     = boss outer diameter override, mm. Default: MCC_BOSS_MIN_RATIO * insert OD.
module mcc_heat_set_boss(insert = MCC_INSERT_M3, h, od = undef) {
    insert_od     = struct_val(insert, "od");
    insert_hole_d = struct_val(insert, "hole_d");
    insert_len    = struct_val(insert, "len");
    _od   = is_undef(od) ? MCC_BOSS_MIN_RATIO * insert_od : od;
    depth = insert_len + 1;

    assert(_od >= MCC_BOSS_MIN_RATIO * insert_od,
        str("mcc: heat_set_boss od=", _od, " below minimum ", MCC_BOSS_MIN_RATIO, "x insert OD (", insert_od, ")"));
    wall = (_od - insert_hole_d) / 2;
    assert(wall >= 2,
        str("mcc: heat_set_boss wall=", wall, " below minimum 2 mm around the bore"));
    assert(h >= depth,
        str("mcc: heat_set_boss h=", h, " shorter than required bore depth ", depth));

    difference() {
        cyl(h = h, d = _od, circum = true, anchor = BOTTOM, $fn = 64);
        translate([0, 0, h]) mcc_heat_set_bore(insert);
    }
}

// Module: mcc_captive_thumbscrew_hole()
// Usage:
//   mcc_captive_thumbscrew_hole([d=], [head_d=], lid_t);
// Description:
//   Negative: a full-depth shaft clearance hole plus an outward-face counterbore sized so a
//   knurled M3 thumbscrew's head cannot pull all the way through the lid (stays captive when
//   backed out). knowledge/components/fasteners-and-hardware.md:97 "M3 knurled thumb screw ...
//   tool-less panel access"; counterbore depth is assumed at half the lid thickness (no sourced
//   figure for this specific geometry) — smallest reasonable choice, confidence assumed.
//   TODO(teamlead): confirm counterbore depth against a physical knurled M3 thumbscrew's head
//   height before finalizing the lid design.
// Arguments:
//   d      = shaft clearance diameter, mm. Default: MCC_M3_CLR_D.
//   head_d = counterbore (head-trap) diameter, mm. Default: 8 (assumed — a typical M3 knurled
//            thumbscrew head is 6-8 mm per generic hardware guides, no sourced figure in
//            knowledge/components/fasteners-and-hardware.md).
//   lid_t  = lid thickness at this location, mm (required).
module mcc_captive_thumbscrew_hole(d = MCC_M3_CLR_D, head_d = 8, lid_t) {
    assert(head_d > d, str("mcc: head_d=", head_d, " must exceed shaft clearance d=", d));
    counterbore_depth = lid_t / 2; // assumed — see TODO above.
    assert(counterbore_depth < lid_t,
        str("mcc: counterbore_depth=", counterbore_depth, " must be less than lid_t=", lid_t));

    union() {
        translate([0, 0, -MCC_EPS])
            cyl(h = lid_t + 2 * MCC_EPS, d = d, circum = true, anchor = BOTTOM, $fn = 64);
        translate([0, 0, lid_t - counterbore_depth])
            cyl(h = counterbore_depth + MCC_EPS, d = head_d, circum = true, anchor = BOTTOM, $fn = 64);
    }
}

// -----------------------------------------------------------------------------------------
// Captive side bolt (D-09) — device retention through the far (-Y) wall into the device's side
// thread. .claude/knowledge/layout-patch-wall.md §7.1; constants in constants.scad's "captive side
// bolt (D-09)" section. Both modules share the local frame described there: Z=0 at the lug's OUTER
// (free/tip) face, +Z runs INTO the case (through the wall, the MCC_GAP_FAR duct, to the compliant
// pad); shell.scad rotates this frame onto the far wall's outward normal.
// -----------------------------------------------------------------------------------------

// Module: mcc_captive_side_bolt_boss()
// Usage:
//   mcc_captive_side_bolt_boss([proud=], [wall_t=], [gap_far=], [pad_t=], [od=], [support_web_t=],
//                              [web_to_floor_h=]);
// Description:
//   ADDITIVE. A ⌀od cylinder spanning Z=[0, proud+wall_t+gap_far-pad_t] mm — the full captive-bolt
//   boss, from its free tip through the proud lug (if any), the wall, and the MCC_GAP_FAR duct, up
//   to the compliant-pad face (layout-patch-wall.md §7.1's axial stack). At the default (flush,
//   D-13) `proud=0`, the segment Z=[wall_t, h] is a horizontal ⌀20 cylinder cantilevered off the
//   inside of the wall — printed floor-down, its lower half is an unsupported overhang, and a pure
//   <=45° conical blend alone would need a ⌀48 root (collides with the vent band, the cradle
//   far-flank ribs and the lid-fastener boss), so it is REJECTED in favour of a central vertical
//   support web: a `support_web_t`-thick fin at the boss's own X, spanning Z=[proud+wall_t, h] (the
//   wall-inner-face-to-pad-face run) and running from the boss's own underside down to the interior
//   floor (`web_to_floor_h` below the axis) — layout-patch-wall.md §7.1 "Blend and support rule".
//   That caps the largest unsupported horizontal span at (od-support_web_t)/2 (T1-31, <=10 mm, the
//   §5 "no unsupported horizontal span over 10 mm" shell rule). The web is additive-only and unions
//   into wall, floor and boss alike once shell.scad places this feature — matching the module
//   contract in layout-patch-wall.md §7.1. Also carries T1-29 (the flush-rule assert: when
//   `proud==0`, the fixed head/web/pocket axial stack must still fit inside `wall_t+gap_far-pad_t`)
//   so a drifted MCC_GAP_FAR fails loudly here even before mcc_captive_side_bolt_cut() is applied.
//   `proud > 0` (the pre-D-13 lug variant) keeps working for tests/coupon overrides — the support
//   web is still added over its own Z=[proud+wall_t, h] span, but the exposed lug segment
//   Z=[0,proud] no longer gets a root-fillet blend (D-13 replaced that mechanism; the lug path is
//   retained only so `-D proud=<n>` still renders a valid, assert-passing part).
// Arguments:
//   proud          = how far the boss stands proud of the wall's outer face, mm.
//                    Default: MCC_SIDE_BOLT_PROUD (0, flush — D-13).
//   wall_t         = far-wall thickness, mm. Default: MCC_WALL.
//   gap_far        = clearance gap the boss crosses beyond the wall, mm. Default: MCC_GAP_FAR (16).
//   pad_t          = compliant pad thickness subtracted off the far end, mm. Default: MCC_SIDE_BOLT_PAD_T.
//   od             = boss outer diameter, mm. Default: MCC_SIDE_BOLT_BOSS_OD.
//   support_web_t  = central support-web thickness (in X, the boss's own axis direction), mm.
//                    Default: MCC_SIDE_BOLT_SUPPORT_WEB_T (= MCC_WALL, 3.0).
//   web_to_floor_h = distance from the boss axis down to the interior floor, mm — how far the
//                    support web has to reach. Default: MCC_SIDE_BOLT_AXIS_Z - MCC_FLOOR_T (22.5,
//                    `assumed` — layout-patch-wall.md §1/§7.1, the connector-centreline axis height
//                    at the still-unmeasured `pos [0,0]` placeholder).
module mcc_captive_side_bolt_boss(
    proud          = MCC_SIDE_BOLT_PROUD,
    wall_t         = MCC_WALL,
    gap_far        = MCC_GAP_FAR,
    pad_t          = MCC_SIDE_BOLT_PAD_T,
    od             = MCC_SIDE_BOLT_BOSS_OD,
    support_web_t  = MCC_SIDE_BOLT_SUPPORT_WEB_T,
    web_to_floor_h = MCC_SIDE_BOLT_AXIS_Z - MCC_FLOOR_T
) {
    h = proud + wall_t + gap_far - pad_t;
    assert(h > MCC_EPS,
        str("mcc: captive_side_bolt_boss total height ", h, " <= 0 (proud=", proud, " wall_t=", wall_t,
            " gap_far=", gap_far, " pad_t=", pad_t, ")"));
    assert(support_web_t > 0 && support_web_t < od,
        str("mcc: captive_side_bolt_boss support_web_t=", support_web_t, " must be in (0, od=", od, ")"));
    // T1-31 (layout-patch-wall.md §7.1/§9, architecture.md §5 "no unsupported horizontal span over
    // 10 mm"): the largest unsupported horizontal step under the boss, either side of the web.
    assert((od - support_web_t) / 2 <= 10.0,
        str("mcc: captive_side_bolt_boss T1-31 unsupported span=", (od - support_web_t) / 2,
            " exceeds the 10.0 mm self-supporting limit (od=", od, " support_web_t=", support_web_t, ")"));
    // T1-29 (flush rule, D-13): when this call is the flush default (proud=0), the FIXED
    // head-recess/retaining-web/E-clip-pocket axial stack (constants.scad, not this module's own
    // parameters — mcc_captive_side_bolt_boss() doesn't take them) must still fit inside
    // wall_t+gap_far-pad_t. At the rev-3 defaults this is an EQUALITY (19 == 19): zero slack, by
    // design — a taller measured head (M5) must raise MCC_GAP_FAR, not shave the recess.
    assert(proud > 0 ||
           (MCC_SIDE_BOLT_HEAD_REC_H + MCC_SIDE_BOLT_WEB_T + MCC_SIDE_BOLT_POCKET_H + pad_t) <= (wall_t + gap_far),
        str("mcc: captive_side_bolt_boss T1-29 flush rule: head_rec_h+web_t+pocket_h+pad_t=",
            MCC_SIDE_BOLT_HEAD_REC_H + MCC_SIDE_BOLT_WEB_T + MCC_SIDE_BOLT_POCKET_H + pad_t,
            " must be <= wall_t+gap_far=", wall_t + gap_far, " when proud=0 (flush, D-13)"));

    // Support web: Z=[proud+wall_t, h] (wall inner face -> pad face), X thickness support_web_t
    // centred on the boss axis, running in Y (the boss's own radial/"down" direction once
    // shell.scad orients this feature) from the axis out past the boss's underside (od/2, with a
    // small epsilon overlap so the union has no coincident/degenerate face) down to web_to_floor_h.
    web_z0  = proud + wall_t;
    web_len = h - web_z0;
    web_y0  = od / 2 - MCC_EPS;
    web_ly  = web_to_floor_h - web_y0;
    assert(web_ly > MCC_EPS,
        str("mcc: captive_side_bolt_boss web_to_floor_h=", web_to_floor_h,
            " must clear the boss radius (od/2=", od / 2, ") to actually reach the floor"));

    union() {
        cyl(h = h, d = od, circum = true, anchor = BOTTOM, $fn = 64);
        if (web_len > MCC_EPS)
            translate([-support_web_t / 2, web_y0, web_z0])
                cube([support_web_t, web_ly, web_len]);
    }
}

// Module: mcc_captive_side_bolt_cut()
// Usage:
//   mcc_captive_side_bolt_cut([proud=], [wall_t=], [gap_far=], [pad_t=], [head_d=], [head_h=],
//                              [head_rec_h=], [shank_d=], [web_t=], [clip_pocket_d=], [pocket_h=],
//                              [engage=]);
// Description:
//   SUBTRACTIVE. Union of the head recess (counterbore), the full-depth shank clearance bore, and
//   the E-clip clearance pocket, in the same local frame as mcc_captive_side_bolt_boss() — meant to
//   be `difference()`d after that boss has been unioned into the shell (layout-patch-wall.md §7.1
//   module contract). Runs Z=[-MCC_EPS, proud+wall_t+gap_far+MCC_EPS] so it also pierces the wall
//   proper cleanly at both ends. Every bore $fn=64, circum=true (architecture.md §3 `$fn` policy).
//   The boss OD (for the wall-around-the-pocket check) and the E-clip OD/groove position (for the
//   pocket-depth and clip-travel checks) are read from MCC_SIDE_BOLT_BOSS_OD / MCC_SIDE_BOLT_CLIP /
//   MCC_SIDE_BOLT_GROOVE_POS rather than taken as parameters — they check this cut against the
//   *default* boss geometry; a caller overriding the boss's own `od` is responsible for re-checking
//   this assert by hand.
//   Tier-1 asserts (named per architecture.md §9 / layout-patch-wall.md §9; the geometric
//   device-position half of T1-24/T1-27 lives in shell.scad, not here):
//     T1-25  head_rec_h >= head_h + 1.0                          (head fully recessed)
//     —      web_t >= 2.0                                        (E-clip shoulder minimum material)
//     T1-26  clip_pocket_d >= clip_od + 1.0
//     T1-26  (boss_od - clip_pocket_d) / 2 >= 3.0                 (wall around the pocket)
//     T1-26  head_rec_h + web_t + pocket_h <= proud+wall_t+gap_far-pad_t   (pocket fits the boss)
//     T1-26  groove_pos - web_t >= engage + 0.5                   (clip travels far enough to free
//                                                                   the device without dropping it
//                                                                   inside the case)
// Arguments:
//   proud, wall_t, gap_far, pad_t = same meaning/defaults as mcc_captive_side_bolt_boss().
//   head_d        = slotted screw head diameter, mm. Default: MCC_SIDE_BOLT_HEAD_D.
//   head_h        = slotted screw head height, mm. Default: MCC_SIDE_BOLT_HEAD_H.
//   head_rec_h    = head recess depth, mm. Default: MCC_SIDE_BOLT_HEAD_REC_H.
//   shank_d       = shank clearance bore diameter, mm. Default: MCC_TRIPOD_CLR_D (6.6).
//   web_t         = retaining web thickness, mm. Default: MCC_SIDE_BOLT_WEB_T.
//   clip_pocket_d = E-clip clearance pocket diameter, mm. Default: MCC_SIDE_BOLT_POCKET_D.
//   pocket_h      = E-clip clearance pocket depth, mm. Default: MCC_SIDE_BOLT_POCKET_H.
//   engage        = thread engagement length into the device, mm. Default: MCC_SIDE_BOLT_ENGAGE.
module mcc_captive_side_bolt_cut(
    proud         = MCC_SIDE_BOLT_PROUD,
    wall_t        = MCC_WALL,
    gap_far       = MCC_GAP_FAR,
    pad_t         = MCC_SIDE_BOLT_PAD_T,
    head_d        = MCC_SIDE_BOLT_HEAD_D,
    head_h        = MCC_SIDE_BOLT_HEAD_H,
    head_rec_h    = MCC_SIDE_BOLT_HEAD_REC_H,
    shank_d       = MCC_TRIPOD_CLR_D,
    web_t         = MCC_SIDE_BOLT_WEB_T,
    clip_pocket_d = MCC_SIDE_BOLT_POCKET_D,
    pocket_h      = MCC_SIDE_BOLT_POCKET_H,
    engage        = MCC_SIDE_BOLT_ENGAGE
) {
    total_h    = proud + wall_t + gap_far - pad_t;
    boss_od    = MCC_SIDE_BOLT_BOSS_OD;
    clip_od    = struct_val(MCC_SIDE_BOLT_CLIP, "od");
    groove_pos = MCC_SIDE_BOLT_GROOVE_POS;
    head_rec_d = head_d + 2 * MCC_CLR_SLIDE; // radial clearance for a hand-turned slotted head.

    assert(head_rec_h >= head_h + 1.0,
        str("mcc: side_bolt_cut T1-25 head_rec_h=", head_rec_h, " must be >= head_h+1.0 (", head_h + 1.0, ")"));
    assert(web_t >= 2.0,
        str("mcc: side_bolt_cut web_t=", web_t, " below the 2.0 mm minimum retaining-shoulder material"));
    assert(clip_pocket_d >= clip_od + 1.0,
        str("mcc: side_bolt_cut T1-26 clip_pocket_d=", clip_pocket_d, " must be >= clip od+1.0 (", clip_od + 1.0, ")"));
    assert((boss_od - clip_pocket_d) / 2 >= 3.0,
        str("mcc: side_bolt_cut T1-26 wall around clip pocket = ", (boss_od - clip_pocket_d) / 2, " below 3.0 mm minimum"));
    assert(head_rec_h + web_t + pocket_h <= total_h,
        str("mcc: side_bolt_cut T1-26 head_rec_h+web_t+pocket_h=", head_rec_h + web_t + pocket_h,
            " exceeds the boss's own length ", total_h));
    assert(groove_pos - web_t >= engage + 0.5,
        str("mcc: side_bolt_cut T1-26 clip travel=", groove_pos - web_t, " must be >= engage+0.5 (", engage + 0.5, ")"));

    union() {
        translate([0, 0, -MCC_EPS])
            cyl(h = head_rec_h + MCC_EPS, d = head_rec_d, circum = true, anchor = BOTTOM, $fn = 64);
        translate([0, 0, -MCC_EPS])
            cyl(h = total_h + 2 * MCC_EPS, d = shank_d, circum = true, anchor = BOTTOM, $fn = 64);
        translate([0, 0, head_rec_h + web_t])
            cyl(h = pocket_h, d = clip_pocket_d, circum = true, anchor = BOTTOM, $fn = 64);
    }
}

// Function: mcc_side_bolt_keepout()
// Usage:
//   ko = mcc_side_bolt_keepout([od=], [strip_w=]);
// Description:
//   Pure function: the far-wall keep-out for shell.scad/vents.scad/cradle.scad/mounts.scad to
//   assert non-intersection against (T1-23, T1-27 — vent slots, cradle far-flank ribs,
//   lid-fastener bosses, and the splitter bay must all clear it). Since D-13 the keep-out is no
//   longer a plain disc — the internal support web (mcc_captive_side_bolt_boss()) extends it
//   downward — so this returns a struct/list `[["disc_d",od+4], ["strip_w",strip_w],
//   ["strip_to_floor",true]]` rather than a bare diameter: the OD24 disc around the boss axis,
//   PLUS a `strip_w`-wide strip running from the interior floor up to the disc (the support web's
//   own wall footprint — a vent slot cut there would open into solid material).
//   layout-patch-wall.md §7.1 "The keep-out is no longer a plain disc ... keepout_d = boss_od+2*2.0
//   = 24.0 ... union with a 7 mm-wide strip". Use mcc_side_bolt_keepout_2d() to actually draw it.
// Arguments:
//   od      = boss outer diameter, mm. Default: MCC_SIDE_BOLT_BOSS_OD.
//   strip_w = support-web keep-out strip width, mm. Default: MCC_SIDE_BOLT_KEEPOUT_STRIP_W.
function mcc_side_bolt_keepout(od = MCC_SIDE_BOLT_BOSS_OD, strip_w = MCC_SIDE_BOLT_KEEPOUT_STRIP_W) =
    [["disc_d", od + 2 * 2.0], ["strip_w", strip_w], ["strip_to_floor", true]];

// Module: mcc_side_bolt_keepout_2d()
// Usage:
//   mcc_side_bolt_keepout_2d(axis_z, [od=], [strip_w=], [floor_z=]);
// Description:
//   2D keep-out in the wall plane (local X = across the wall, local Z = up; the caller translates
//   this to `x_bolt` before subtracting it from a vent slot pattern — layout-patch-wall.md §5 "no
//   vent slot inside either" the disc or the strip, T1-23). Draws mcc_side_bolt_keepout()'s disc
//   centred at `z = axis_z`, unioned with a `strip_w`-wide strip centred on the local X axis
//   running from `z = floor_z` (the interior floor) up to the axis — the support web's own wall
//   footprint, so a slot cut there would open into solid material, not air.
// Arguments:
//   axis_z  = bolt axis height in the caller's own wall-plane frame, mm (required).
//   od      = boss outer diameter, mm. Default: MCC_SIDE_BOLT_BOSS_OD.
//   strip_w = keep-out strip width, mm. Default: MCC_SIDE_BOLT_KEEPOUT_STRIP_W.
//   floor_z = interior floor height in the same frame, mm. Default: MCC_FLOOR_T.
module mcc_side_bolt_keepout_2d(axis_z, od = MCC_SIDE_BOLT_BOSS_OD, strip_w = MCC_SIDE_BOLT_KEEPOUT_STRIP_W, floor_z = MCC_FLOOR_T) {
    ko        = mcc_side_bolt_keepout(od = od, strip_w = strip_w);
    disc_d    = struct_val(ko, "disc_d");
    strip_len = axis_z - floor_z;
    assert(strip_len > 0,
        str("mcc: side_bolt_keepout_2d axis_z=", axis_z, " must be above floor_z=", floor_z));

    union() {
        translate([0, axis_z]) circle(d = disc_d, $fn = 64);
        translate([-strip_w / 2, floor_z]) square([strip_w, strip_len]);
    }
}

// Module: mcc_side_bolt_envelope()
// Usage:
//   mcc_side_bolt_envelope([proud=], [wall_t=], [gap_far=], [pad_t=], [od=]);
// Description:
//   Ghosted (%) review-only visualization of the mcc_side_bolt_keepout() disc, swept the full
//   length of the boss (layout-patch-wall.md §7.1 "the same disc swept through the duct"), in the
//   same local frame as mcc_captive_side_bolt_boss() so a caller can place both identically.
//   Mirrors the mcc_fan_envelope()/mcc_splitter_envelope() reservation-box pattern (fan.scad,
//   poe_splitter.scad) in spirit, but this feature's real non-intersection checks use the plain
//   `disc_d` from mcc_side_bolt_keepout() against other features' own geometry, not a
//   CSG-intersected solid — this box is for visual review only (it does not attempt to sweep the
//   strip too — the strip is a 2D wall-plane feature, see mcc_side_bolt_keepout_2d()), so (unlike
//   the fan/splitter envelopes) it is `%`-ghosted and gated behind MCC_SHOW_GHOST like every other
//   ghost in this repo (architecture.md §3 "Ghosts" — both belts: `%` is the mechanism, the flag is
//   the review signal).
// Arguments:
//   proud, wall_t, gap_far, pad_t, od = same meaning/defaults as mcc_captive_side_bolt_boss().
module mcc_side_bolt_envelope(
    proud   = MCC_SIDE_BOLT_PROUD,
    wall_t  = MCC_WALL,
    gap_far = MCC_GAP_FAR,
    pad_t   = MCC_SIDE_BOLT_PAD_T,
    od      = MCC_SIDE_BOLT_BOSS_OD
) {
    h      = proud + wall_t + gap_far - pad_t;
    disc_d = struct_val(mcc_side_bolt_keepout(od = od), "disc_d");
    if (MCC_SHOW_GHOST) {
        %cyl(h = h, d = disc_d, circum = true, anchor = BOTTOM, $fn = 64);
    }
}

// Module: mcc_case_tripod_insert_bore()
// Usage:
//   mcc_case_tripod_insert_bore();
// Description:
//   Negative (subtractive) blind bore for the CASE's own 1/4"-20 heat-set insert in the floor —
//   mounts the case itself on a tripod/cheeseplate (architecture.md §6 floor rule). This is NOT the
//   device-retention side bolt above, which threads directly into the device's metal body and needs
//   no insert. Local frame matches mcc_heat_set_bore(): the open face is at Z=0, extending blind
//   into -Z by MCC_INSERT_1_4_20's len + 1 mm. Replaces mcc_tripod_boss() (deviation D2,
//   architecture.md §13): that module was a clearance-hole boss for the withdrawn floor
//   through-bolt; the floor's remaining 1/4"-20 feature is threaded, per D-09.
module mcc_case_tripod_insert_bore() {
    insert_hole_d = struct_val(MCC_INSERT_1_4_20, "hole_d");
    insert_len    = struct_val(MCC_INSERT_1_4_20, "len");
    depth = insert_len + 1;
    translate([0, 0, MCC_EPS - depth / 2])
        cyl(h = depth + 2 * MCC_EPS, d = insert_hole_d, circum = true, $fn = 64);
}

// Module: mcc_case_tripod_insert_boss()
// Usage:
//   mcc_case_tripod_insert_boss(h, [od=]);
// Description:
//   Additive boss (base at Z=0, top at Z=h) with an integral blind bore for the case's own
//   1/4"-20 heat-set insert, opening at the top. Same pattern as mcc_heat_set_boss(), fixed to
//   MCC_INSERT_1_4_20 (there is exactly one part here, unlike the M3 family). Asserts the
//   OD/insert-OD ratio and the minimum 2 mm wall around the bore, same rule as mcc_heat_set_boss()
//   (architecture.md:348).
// Arguments:
//   h  = boss height, mm (required — must be >= MCC_INSERT_1_4_20.len + 1).
//   od = boss outer diameter override, mm. Default: MCC_BOSS_MIN_RATIO * insert OD.
module mcc_case_tripod_insert_boss(h, od = undef) {
    insert_od     = struct_val(MCC_INSERT_1_4_20, "od");
    insert_hole_d = struct_val(MCC_INSERT_1_4_20, "hole_d");
    insert_len    = struct_val(MCC_INSERT_1_4_20, "len");
    _od   = is_undef(od) ? MCC_BOSS_MIN_RATIO * insert_od : od;
    depth = insert_len + 1;

    assert(_od >= MCC_BOSS_MIN_RATIO * insert_od,
        str("mcc: case_tripod_insert_boss od=", _od, " below minimum ", MCC_BOSS_MIN_RATIO, "x insert OD (", insert_od, ")"));
    wall = (_od - insert_hole_d) / 2;
    assert(wall >= 2,
        str("mcc: case_tripod_insert_boss wall=", wall, " below minimum 2 mm around the bore"));
    assert(h >= depth,
        str("mcc: case_tripod_insert_boss h=", h, " shorter than required bore depth ", depth));

    difference() {
        cyl(h = h, d = _od, circum = true, anchor = BOTTOM, $fn = 64);
        translate([0, 0, h]) mcc_case_tripod_insert_bore();
    }
}

// Module: mcc_m4_hole()
// Usage:
//   mcc_m4_hole([h=]);
// Description:
//   Generic M4 clearance through-hole, base at Z=0 growing toward +Z. Currently unused in
//   lib/mcc/** — kept as a generic M4 clearance-hole helper for any future need (the Fishtail M4
//   pattern remains reserve-only, no holes cut; VESA is retired, issue #25, D-15).
// Arguments:
//   h = hole length, mm. Default: 20 (assumed — generous enough to guarantee a clean through-cut
//       through any wall/floor/boss stack in this repo; override per call site).
module mcc_m4_hole(h = 20) {
    translate([0, 0, -MCC_EPS])
        cyl(h = h + 2 * MCC_EPS, d = MCC_M4_CLR_D, circum = true, anchor = BOTTOM, $fn = 64);
}

// vim: expandtab tabstop=4 shiftwidth=4 softtabstop=4 nowrap
