//////////////////////////////////////////////////////////////////////
// models/brackets/arch-tv-bracket.scad
//   L4-equivalent assembly (architecture.md §3 rev 9/13, layout-patch-wall.md §17.2). Issue #47,
//   implemented per docs/plans/2026-09-27-arch-tv-bracket.md §0-§8/§10, as amended by the architect
//   verdict's binding changes B1-B11 (§12.2) and the PLAN-ASSUMPTION rulings (§12.5). Sibling of
//   the retired tv-bracket.scad (#26, D47); consumes lib/mcc/rail.scad's mount-rail interface (#25)
//   UNCHANGED -- the inherited rail-interface defect F1 (§12.3, proposed R38) is tracked separately
//   (issue #48) and is NOT fixed here; every rail-dependent value in this file (keep-out rectangle,
//   Z stack, RAIL_X, slide_clear) derives from MCC_RAIL_* so a future rail fix is absorbed by a
//   re-golden, no code edit.
//
//   Mounts directly on a TV's TOP TWO VESA 400 M8 screws (no VESA plate -- unlike the retired tv-bracket.scad's
//   sandwich-plate approach). This file's own `build.py` parts marker (§4.2, below) declares TWO
//   exported parts, not one: an "arm" (printed TWICE, left/right -- PLAN-ASSUMPTION-4, one part is
//   symmetric about its own axis so a proper in-plane rotation gives the mirror, not a flip) and a
//   "centre" plate carrying the mount rail, stacked ON TOP of the two arms' laps (a STACKED lap, not a half-lap --
//   plan §1.3 works out why: the case slides on from +X, its floor sweeping over the right arm's
//   M8 pad, so anything proud of the arms must sit below the case floor -- forcing the rail one
//   plate thickness higher than the arms).
//
//   Frame (viewed from BEHIND the TV, the installer's own view -- plan §1.1):
//     - Assembly frame origin: midpoint between the two top VESA screw centres, on the TV back
//       (Z=0). +X right, +Y UP, +Z away from the TV. Screw centres at (-HALF_PITCH,0), (+HALF_PITCH,0).
//     - Each printable part is authored in ITS OWN print frame (bed face at that part's own Z=0);
//       only the "assembly"/"assembly_sweep" preview branches (§6, non-exported) place them into
//       the assembly frame above.
//     - Arm print frame: pad centre at the origin, arm axis = local +X, TV face on the bed (Z=0).
//     - Centre print frame: origin = the rail centre projected onto the centre's own bottom face
//       (assembly (0, rise, ARCH_PLATE_T)); bottom face (TV-facing, but 11 mm standing off the TV --
//       PLAN-ASSUMPTION-3, forced by the +X slide-on sweep, §1.3) on the bed.
//
//   Z stack (TV back = 0; plan §1.3, re-derived for D44 -- the case floor now sits FLUSH on the
//   centre's top face, the rail has no pedestal any more):
//     Arm TV face / centre gap floor ............ Z = 0
//     Arm top face = centre bottom face (stacked lap) ... Z = ARCH_PLATE_T       (= 11)
//     Rail mounting face (centre top) Z_RAIL ..... Z = 2 * ARCH_PLATE_T          (= 22)
//     Arm feature top ARM_TOP_Z (ribs, M8 pad boss) Z = ARCH_PLATE_T + RIB_H     (= 20)
//     Case floor (exterior), at full mate and while sliding .. Z = Z_RAIL          (= 22, flush)
//     Case lid top ................................ Z = 22 + 51 = 73            (H=51, CLAUDE.md)
//   Sweep condition (T1-51 / A5): Z_RAIL - ARM_TOP_Z >= ARCH_SWEEP_CLR, i.e.
//   2T - (T + 9) >= 2 => T >= 11 -- ARCH_PLATE_T=11 is the smallest plate that clears the pad
//   during the +X slide-on approach (the case can never clear the pad by going above it -- plan
//   §1.3 -- so it must pass over it in Z instead). T was 8 while the rail carried a 3 mm pedestal.
//
//   B1 (blocking, §12.2): the plan's own A8 assert (M3 counterbore vs. the rail keep-out rectangle)
//   FAILS at the placeholder on the -X (end-stop) lap. Fix: centre the rail's physical footprint
//   (working length + end-stop flange) on the centre plate via RAIL_X = MCC_RAIL_END_STOP_L / 2,
//   used consistently in the rail call, the keep-out rectangle, the case-mate transform (assembly
//   previews) and A13/T1-59. Re-derived worst-case margin with B1: 1.87 mm on both laps (>=
//   ARCH_KEEPOUT_CLR = 1.0). If F1's eventual fix drops the end-stop flange, RAIL_X becomes 0
//   automatically -- do NOT "fix" this by moving XJ instead (the centre bbox has only ~4.3 mm of
//   244 mm bed margin to spare, T1-47).
//
//   Assert ids: T1-47 ... T1-60 (architect-assigned per B4; the highest T1 id before this file was
//   T1-46). Risk/measurement ids (R30-R38, M18a-d, D26) are recorded by the architect in
//   .claude/knowledge/architecture.md after merge (§12.5 bottom) -- this file cites the PROPOSED
//   ids in comments only.
//
//   PRINT GATE (B10): do not print this bracket FOR USE before M15 (rail-latch pull test), M18 (the
//   TV measurements below) and R38/F1 (rail entry/interference) are closed. The released STL is
//   rendered for the PLACEHOLDER TV_TOP_CLEAR=150; a measured TV needs
//   `render brackets/arch-tv-bracket -D TV_TOP_CLEAR=<mm>`.
//
// build.py: parts = arm, centre
// build.py: print_count = arm:2
//   (left + right arm: arm.3mf and the review project carry both copies)
//
// Render:
//   openscad --backend=Manifold -D 'part="arm"' -o out/arm.stl models/brackets/arch-tv-bracket.scad
//   openscad --backend=Manifold -D 'part="centre"' -o out/centre.stl models/brackets/arch-tv-bracket.scad
//   openscad --backend=Manifold -D 'part="assembly"' -o out/assembly.stl models/brackets/arch-tv-bracket.scad
//   openscad --backend=Manifold -D 'part="assembly_sweep"' -o out/assembly_sweep.stl models/brackets/arch-tv-bracket.scad
//////////////////////////////////////////////////////////////////////

$fa = 1; $fs = 0.4; // the ONLY place $fn-adjacent globals are set (openscad-authoring skill).

include <mcc/mcc.scad>
// All 8 device records: the arch's own case-envelope loop (_mcc_arch_tv_envelope_max(), B7) must
// cover every current SKU, and a bracket may `include` device data files read-only for previews or
// envelope derivation (architecture.md §3 rev 13). A future 9th SKU is added to BOTH the include
// list below and _ARCH_TV_DEVS in one place (B7's own new-case-variant checklist hook).
include <mcc/devices/pro-convert-for-ndi-to-aio.scad>
include <mcc/devices/pro-convert-for-ndi-to-hdmi-4k.scad>
include <mcc/devices/pro-convert-for-ndi-to-hdmi.scad>
include <mcc/devices/pro-convert-for-ndi-to-sdi.scad>
include <mcc/devices/pro-convert-hdmi-plus.scad>
include <mcc/devices/pro-convert-hdmi-tx.scad>
include <mcc/devices/pro-convert-sdi-plus.scad>
include <mcc/devices/pro-convert-sdi-tx.scad>

// scripts/build.py always passes -D part="<name>"; "part" is reserved for that (matches every
// coupon/bracket/case.scad). Default "centre" (never "assembly" -- a bare `openscad -o x.stl`
// export must never emit a ghost).
part = "centre";

// -----------------------------------------------------------------------------------------
// §1.2 Parameters (plan-fixed geometry, THIS bracket's own authored dimensions -- bracket-own
// geometry stays out of constants.scad, the models/brackets convention; nothing here is
// cross-cutting library policy).
// -----------------------------------------------------------------------------------------

VESA_TOP_PITCH = 400; // mm. User decision 2026-09-27 (#47); VESA MIS-F 400x400 is a standard
                       // pattern (https://en.wikipedia.org/wiki/VESA_mount).
HALF_PITCH = VESA_TOP_PITCH / 2; // = 200. derived.

TV_TOP_CLEAR = 150; // mm. `unknown` -> placeholder, assumed (PLAN-ASSUMPTION-2, RATIFIED as
                     // assumed, §12.5). Distance from the top-screw CENTRELINE up to the TV's top
                     // outer edge. User bound: < TV_TOP_CLEAR_MAX (#47). Measurement M18a (§9).
                     // Override per TV with `-D TV_TOP_CLEAR=<mm>`, or measure and edit + re-golden
                     // (B10 -- do not print for use at the placeholder).
TV_TOP_CLEAR_MAX = 185; // mm. user decision 2026-09-27 ("less than 185 mm") -- an assert bound only.
TV_TOP_MARGIN = 10.0; // mm. assumed -- case top stays this far below the TV top edge (bezel,
                       // measurement error, sight line over the edge).

ARCH_PLATE_T = 11.0; // mm. derived minimum (Z-stack derivation above: T>=11 for the slide-on sweep to
                      // clear the pad once D44 removed the rail's 3 mm pedestal -- was 8) and
                      // independently justified for torsion stiffness (plan §2). A cantilevered BEAM,
                      // not a sandwiched shim.
RIB_T = MCC_WALL; // = 3.0. <= 0.6 x ARCH_PLATE_T (fdm-rugged-enclosure-guidelines.md:67).
RIB_H = MCC_RIB_HEIGHT_RATIO_MAX * RIB_T; // = 9.0 (fdm-rugged-enclosure-guidelines.md:68, D22).
ARCH_SWEEP_CLR = 2.0; // mm. assumed -- vertical clearance between the sliding case floor and the
                       // tallest arm feature while the case passes over it (§1.3); same magnitude as
                       // MCC_GAP_DEV (constants.scad).
ARM_W = 40.0; // mm. assumed -- arm width; carries the 2x2 joint pattern, two edge ribs and the M8
               // pad.
PAD_BOSS_D = 30.0; // mm. assumed -- >= counterbore diameter (16.6) + 2 x 2*MCC_WALL; asserted
                    // (T1-58).
CENTRE_W = 92.0; // mm. D44: must hold the 65 mm rail's keep-out Y span [-32.5, +36.1] (T1-53, needs
                  // >= 72.2) AND the UP arrow above it (T1-60: 36.1 + 1 + 6 + 1 = 44.1 <= CENTRE_W/2,
                  // minimum 88.2) -- 92 leaves 0.95 mm on both T1-60 bounds. Was 40 (= ARM_W) for the
                  // 14.6 mm rail.
C_HALF = 90.0; // mm. assumed -- centre-body half-length. Rail footprint half-length is
               // MCC_RAIL_LEN/2 + MCC_RAIL_END_STOP_L = 81, leaving a 9 mm end web (>= MCC_WALL,
               // asserted T1-53).
XJ = 95.0; // mm. assumed -- |x| of each lap centre in the assembly frame (plan §3.2 numeric sweep).
LAP_L = 30.0; // mm. assumed -- lap length along the arm axis.
JOINT_S = 14.0; // mm. assumed -- joint hole pitch along the arm axis (2x2 pattern).
JOINT_P = 20.0; // mm. assumed -- joint hole pitch across the arm axis.
LAP_RIB_GAP = 3.0; // mm. arm ribs stop this far short of the lap. D44: 3.0 (was 1.0) -- with the
                    // 92 mm centre body the rib end's outer corner lies inside the body's Y band at large
                    // TV_TOP_CLEAR, so T1-55's X clearance alone governs: 1.0 left 0.994 mm at
                    // TV_TOP_CLEAR=184.9 (limit 1.0, passing only on the assert's EPS); 3.0 leaves 2.34.
ARCH_KEEPOUT_CLR = 1.0; // mm. assumed -- clearance used by the hole-vs-rail and rib-vs-centre
                         // asserts.

// M8 socket-head cap screw + ISO 7089 washer -- nominal standard values, NOT in knowledge/** ->
// assumed (PLAN-ASSUMPTION-9, RATIFIED -- follow-up: add to
// knowledge/components/fasteners-and-hardware.md).
M8_HEAD_K    = 8.0;  // ISO 4762 M8 socket-head height, mm.
M8_WASHER_D  = 16.0; // ISO 7089 M8 flat-washer OD, mm.
M8_WASHER_H  = 1.6;  // ISO 7089 M8 flat-washer thickness, mm.
// M3 socket-head cap screw -- same status.
M3_HEAD_D = 5.5; // ISO 4762 M3 socket-head diameter, mm.
M3_HEAD_K = 3.0; // ISO 4762 M3 socket-head height, mm.
M3_COUNTERBORE_DEPTH = M3_HEAD_K + 1.3; // mm. D44 (T1-57): the head sits 4.3 mm deep in the 11 mm
                  // centre, leaving 6.7 mm of centre under it, so an M3x12 reaches 5.3 mm into the arm
                  // (tip 1.4 mm above the insert-bore floor, 0.9 more than T1-57's 0.5) -- the same
                  // engagement the 8 mm stack had.
M3_JOINT_SCREW_L = 12; // mm. derived stock length (§3.3 screw-stack derivation, T1-57). Was 10 (8 mm plates).

ARROW_DEPTH = 0.6; // mm. assumed, cosmetic "UP" deboss (§3.5).
ARROW_L = 8.0; // mm. assumed (B3 -- the plan's original arrow had no defined size).
ARROW_W = 6.0; // mm. assumed (B3).

// B1: centre the rail's PHYSICAL footprint (working length + end-stop flange, [-81,75] before this
// shift) on the centre plate -- fixes the plan's own A8 failure at the -X (end-stop) lap. Used
// consistently in the rail call, the keep-out rectangle, the case-mate transform (previews) and
// A13/T1-59. If F1's eventual fix drops the end-stop flange, this becomes 0 automatically.
RAIL_X = MCC_RAIL_END_STOP_L / 2; // = 3.0

// Rail keep-out rectangle, centre-local frame, B1-shifted (plan §3.2, rail-local -> centre-local
// after the rotate([0,0,180]) rail placement below): the latch arm/nub stand on the rail-local -Y
// flank, i.e. +Y here (rail.scad:151-175). Built from MCC_RAIL_* constants only, never hand-typed.
RAIL_KEEPOUT_X = [RAIL_X - MCC_RAIL_LEN / 2 - MCC_RAIL_END_STOP_L, RAIL_X + MCC_RAIL_LEN / 2];
RAIL_KEEPOUT_Y = [-MCC_RAIL_ROOT_W / 2, MCC_RAIL_ROOT_W / 2 + MCC_RAIL_LATCH_ARM_T + MCC_RAIL_LATCH_ENGAGE];

// reused from constants.scad, no new library constant: MCC_M8_CLR_D, MCC_M3_CLR_D, MCC_INSERT_M3,
// MCC_CLR_SLIDE, MCC_RAIL_*, MCC_WALL, MCC_BUILD, MCC_BED_MARGIN, MCC_EPS,
// MCC_M3_MAJOR_D, MCC_RIB_HEIGHT_RATIO_MAX, MCC_RAIL_Y.

// -----------------------------------------------------------------------------------------
// §4/B7: one list of devices feeding the case-envelope loop. A NEW SKU MUST BE ADDED HERE (and to
// the `include` list above) -- otherwise A2/T1-48 would silently pass while a wider/taller case
// stuck up past the TV's own top edge, breaking the "fully behind the TV" user decision. See also
// .claude/skills/new-case-variant/SKILL.md's own checklist hook (B7).
// -----------------------------------------------------------------------------------------

_ARCH_TV_ENV_CFG = [["fan", false], ["splitter", false], ["fan_switch", false]];

_ARCH_TV_DEVS = [
    MCC_DEV_PRO_CONVERT_FOR_NDI_TO_AIO,
    MCC_DEV_PRO_CONVERT_FOR_NDI_TO_HDMI_4K,
    MCC_DEV_PRO_CONVERT_FOR_NDI_TO_HDMI,
    MCC_DEV_PRO_CONVERT_FOR_NDI_TO_SDI,
    MCC_DEV_PRO_CONVERT_HDMI_PLUS,
    MCC_DEV_PRO_CONVERT_HDMI_TX,
    MCC_DEV_PRO_CONVERT_SDI_PLUS,
    MCC_DEV_PRO_CONVERT_SDI_TX,
];

// Function: _mcc_arch_tv_envelope_max()
// Description:
//   Private, pure. [L_max, W_max] over every _ARCH_TV_DEVS record under a fan/splitter/switch-off
//   config (researcher check, plan §1.4: neither flag changes L/W on any current SKU -- L/W come
//   only from device geometry + end zones + wall thickness, never from cfg, see
//   lib/mcc/layout.scad's own mcc_case_layout()). N3: cheap on purpose -- 8 x mcc_case_layout()
//   calls, fine for a smoke test's 3 values; do not extend this into a larger sweep.
function _mcc_arch_tv_envelope_max() =
    let(dims = [for (dev = _ARCH_TV_DEVS) mcc_case_dims(dev, _ARCH_TV_ENV_CFG)])
    [max([for (d = dims) d[0]]), max([for (d = dims) d[1]])];

// -----------------------------------------------------------------------------------------
// §1.4/§1.5: pure geometry function. Every asserted/echoed/drawn number derives from this ONE
// function (a BOSL2 struct, struct_val()-accessible) -- see mcc_arch_tv_assert() and the two
// exported-part modules below.
// -----------------------------------------------------------------------------------------

// Function: mcc_arch_tv_geom()
// Usage:
//   g = mcc_arch_tv_geom([tv_top_clear=]);
// Description:
//   Pure. Derives the whole bracket's geometry from `tv_top_clear` (default TV_TOP_CLEAR) --
//   §1.4/§1.5's algebra, re-derived independently by the architect (§12.1) and matching at the
//   placeholder. See this file's header for the Z-stack table.
function mcc_arch_tv_geom(tv_top_clear = TV_TOP_CLEAR) =
    let(
        env    = _mcc_arch_tv_envelope_max(),
        l_max  = env[0], w_max = env[1],

        // CASE_TOP_ABOVE_RAIL = W_max/2 + MCC_RAIL_Y (MCC_RAIL_Y is negative -- the rail sits under
        // the device, not free-standing -- constants.scad's own R2 comment).
        case_top_above_rail = w_max / 2 + MCC_RAIL_Y,
        // rise: the rail sits as high on the arch as the TV allows (plan §1.4).
        rise = tv_top_clear - TV_TOP_MARGIN - case_top_above_rail,

        alpha   = atan2(rise, HALF_PITCH - XJ),
        arm_len = sqrt(pow(HALF_PITCH - XJ, 2) + pow(rise, 2)),

        z_rail     = 2 * ARCH_PLATE_T,
        arm_top_z  = ARCH_PLATE_T + RIB_H,

        // §3.4: M8 pad clamp thickness -- the number the installer needs for screw length (BOM).
        m8_counterbore_depth = M8_WASHER_H + M8_HEAD_K + 0.4,
        pad_clamp_t = arm_top_z - m8_counterbore_depth,

        // B6: the case can only engage once its leading (+X) end wall passes the rail's own open
        // (+X, per this file's rotate([0,0,180]) rail placement) end, at case centre
        // x = RAIL_X + MCC_RAIL_LEN/2 + L/2 -- not "+MCC_RAIL_LEN" as the plan's own §1.3 originally
        // had it (F1's own entry-path defect notwithstanding -- this bracket derives the number
        // from MCC_RAIL_* so a future rail-interface fix is absorbed automatically).
        slide_clear = MCC_RAIL_LEN / 2 + l_max / 2,

        // Arm print bbox (§1.5): pad disc (|x|<=ARM_W/2 at x=0) unioned with the bar
        // (x in [0, arm_len+LAP_L/2]); Y = ARM_W; Z = arm_top_z (ribs/pad boss both reach it).
        arm_bbox = [arm_len + LAP_L / 2 + ARM_W / 2, ARM_W, arm_top_z],

        // Centre print bbox (§1.5): body [-C_HALF,C_HALF] x [-CENTRE_W/2,CENTRE_W/2], unioned with
        // both tabs -- each tab is the arm's own lap rectangle (arm-local corners
        // (arm_len +/- LAP_L/2, +/-ARM_W/2)) carried through the SAME rotate+translate transform
        // that places the whole arm (_mcc_arch_tv_xform()/_mcc_arch_tv_place(), below). Right and
        // left tabs are mirror images of each other by construction (theta = 180-alpha vs. alpha),
        // so only the right-side extremes need computing (closed-form corner search: cos(alpha)>0,
        // sin(alpha)>=0 for the whole valid rise range [0, TV_TOP_CLEAR_MAX), so the extremal corner
        // is always (arm_len-LAP_L/2, -ARM_W/2) for +X reach / (arm_len+-LAP_L/2, +-ARM_W/2) for
        // the Y extremes -- see this file's own PR notes for the by-hand corner-search derivation).
        tab_x_max = HALF_PITCH - (arm_len - LAP_L / 2) * cos(alpha) + (ARM_W / 2) * sin(alpha),
        centre_x_max = max(C_HALF, tab_x_max),
        tab_y_max = -rise + (arm_len + LAP_L / 2) * sin(alpha) + (ARM_W / 2) * cos(alpha),
        tab_y_min = -rise + (arm_len - LAP_L / 2) * sin(alpha) - (ARM_W / 2) * cos(alpha),
        centre_y_max = max(CENTRE_W / 2, tab_y_max),
        centre_y_min = min(-CENTRE_W / 2, tab_y_min),
        centre_z_max = ARCH_PLATE_T + MCC_RAIL_MALE_H + MCC_RAIL_END_STOP_H, // = 14.5 (the male rises
            // MCC_RAIL_MALE_H above its own foot at Z_RAIL -- D44; MCC_RAIL_END_STOP_H is 0 since D34)
        centre_bbox = [2 * centre_x_max, centre_y_max - centre_y_min, centre_z_max]
    )
    [
        ["tv_top_clear", tv_top_clear],
        ["rise", rise],
        ["alpha", alpha],
        ["arm_len", arm_len],
        ["z_rail", z_rail],
        ["arm_top_z", arm_top_z],
        ["case_top_above_rail", case_top_above_rail],
        ["l_max", l_max],
        ["w_max", w_max],
        ["pad_clamp_t", pad_clamp_t],
        ["slide_clear", slide_clear],
        ["arm_bbox", arm_bbox],
        ["centre_bbox", centre_bbox],
        ["centre_y_max", centre_y_max],
        ["centre_y_min", centre_y_min],
        ["centre_x_max", centre_x_max],
    ];

// -----------------------------------------------------------------------------------------
// §3.2: the ONE joint-hole list and the ONE placement transform, consumed identically by the arm
// (insert bores) and the centre (counterbore clearance holes) so the two halves cannot drift
// (D6 one-source rule, architecture.md §3/§5 rev 5, applied inside one file).
// -----------------------------------------------------------------------------------------

// Function: _mcc_arch_tv_joint_holes()
// Description:
//   Private, pure. 4 arm-local [x,y] joint-hole centres per lap (2x2 pattern at
//   (arm_len +/- JOINT_S/2, +/- JOINT_P/2)).
function _mcc_arch_tv_joint_holes(g) =
    let(a = struct_val(g, "arm_len"))
    [for (sx = [-1, 1], sy = [-1, 1]) [a + sx * JOINT_S / 2, sy * JOINT_P / 2]];

// Function: _mcc_arch_tv_theta()
// Description:
//   Private, pure. The in-plane rotation (degrees) that carries an arm-local point to the centre's
//   own local frame for the given `side` (+1 = right, -1 = left) -- plan §1.5.
function _mcc_arch_tv_theta(g, side) =
    side > 0 ? 180 - struct_val(g, "alpha") : struct_val(g, "alpha");

// Function: _mcc_arch_tv_rotate2()
// Description:
//   Private, pure. 2D rotation of point `p` by `theta` degrees about the origin.
function _mcc_arch_tv_rotate2(p, theta) =
    [p[0] * cos(theta) - p[1] * sin(theta), p[0] * sin(theta) + p[1] * cos(theta)];

// Function: _mcc_arch_tv_xform()
// Description:
//   Private, pure. Arm-local point `p` -> centre-local [x,y], for `side` in {-1,+1}. Used by both
//   the assert module (A8/T1-54, A9/T1-55) and, as the geometric mirror of module
//   _mcc_arch_tv_place() below, to build the tab/hole geometry -- the SAME rotate+translate
//   applied twice (once as an OpenSCAD transform stack for geometry, once as plain arithmetic for
//   the asserts), not two independently-derived formulas.
function _mcc_arch_tv_xform(p, side, g) =
    [side * HALF_PITCH, -struct_val(g, "rise")] + _mcc_arch_tv_rotate2(p, _mcc_arch_tv_theta(g, side));

// Module: _mcc_arch_tv_place()
// Description:
//   Private. Places `children()` (authored in the ARM's own local frame) into the CENTRE's own
//   local frame, for the given `side`. Geometric mirror of _mcc_arch_tv_xform() above.
module _mcc_arch_tv_place(g, side) {
    translate([side * HALF_PITCH, -struct_val(g, "rise"), 0])
        rotate([0, 0, _mcc_arch_tv_theta(g, side)])
            children();
}

// Module: _mcc_arch_tv_place_assembly()
// Description:
//   Private, preview-only (§6). Places `children()` (arm-local frame) into the ASSEMBLY frame --
//   same rotation as _mcc_arch_tv_place(), but no rise-shift (the assembly frame's own Y=0 IS the
//   TV-screw line the arms sit on; only the centre's own local frame is shifted by `rise`).
module _mcc_arch_tv_place_assembly(g, side) {
    translate([side * HALF_PITCH, 0, 0])
        rotate([0, 0, _mcc_arch_tv_theta(g, side)])
            children();
}

// Function: _mcc_arch_tv_circle_rect_gap()
// Description:
//   Private, pure. Gap (mm) between a circle (`center`, radius `r`) and an axis-aligned rectangle
//   (`rect_x`=[xmin,xmax], `rect_y`=[ymin,ymax]) -- negative when they overlap. Standard
//   clamped-nearest-point formula; correct whether `center` is inside or outside the rectangle.
function _mcc_arch_tv_circle_rect_gap(center, r, rect_x, rect_y) =
    let(
        cx = min(max(center[0], rect_x[0]), rect_x[1]),
        cy = min(max(center[1], rect_y[0]), rect_y[1])
    )
    norm([center[0] - cx, center[1] - cy]) - r;

// -----------------------------------------------------------------------------------------
// §5: Tier-1 asserts (architecture.md §9). A1-A13 -> T1-47...T1-59 (B4), plus B3's T1-60. Kept in a
// PUBLIC module (not bare top-level statements) so tests/test_arch_tv_bracket.scad can exercise them
// for other TV_TOP_CLEAR values via `use` (which skips bare top-level asserts) -- PLAN-ASSUMPTION-5.
// Called at top level below so every render fires it.
// -----------------------------------------------------------------------------------------

// Module: mcc_arch_tv_assert()
// Usage:
//   mcc_arch_tv_assert(g);
module mcc_arch_tv_assert(g) {
    tv_top_clear        = struct_val(g, "tv_top_clear");
    rise                = struct_val(g, "rise");
    arm_len             = struct_val(g, "arm_len");
    z_rail              = struct_val(g, "z_rail");
    arm_top_z           = struct_val(g, "arm_top_z");
    case_top_above_rail = struct_val(g, "case_top_above_rail");
    l_max               = struct_val(g, "l_max");
    pad_clamp_t         = struct_val(g, "pad_clamp_t");
    arm_bbox            = struct_val(g, "arm_bbox");
    centre_bbox         = struct_val(g, "centre_bbox");
    centre_y_max        = struct_val(g, "centre_y_max");

    // T1-47 (A1, B9): the STRICTER cap (per-side bed margin), never the literal 244 -- D26 flags
    // that mcc_bbox_ok() (util.scad) allows MCC_BUILD - MCC_BED_MARGIN (250, a bug: MCC_BED_MARGIN
    // is a PER-SIDE margin) -- fixed in a separate ticket, not here. This assert is the real gate.
    max_axis = MCC_BUILD - 2 * MCC_BED_MARGIN; // = 244
    for (i = [0:2])
        assert(arm_bbox[i] <= max_axis + MCC_EPS,
            str("mcc: arch-tv-bracket T1-47 arm bbox axis ", i, "=", arm_bbox[i],
                " exceeds MCC_BUILD-2*MCC_BED_MARGIN=", max_axis, " (D26)"));
    for (i = [0:2])
        assert(centre_bbox[i] <= max_axis + MCC_EPS,
            str("mcc: arch-tv-bracket T1-47 centre bbox axis ", i, "=", centre_bbox[i],
                " exceeds MCC_BUILD-2*MCC_BED_MARGIN=", max_axis, " (D26)"));

    // T1-48 (A2): the case stays fully behind the TV -- both the defining rise equation (a
    // tautology unless a future edit breaks it) and the centre's own top edge.
    assert(rise + case_top_above_rail + TV_TOP_MARGIN <= tv_top_clear + MCC_EPS,
        str("mcc: arch-tv-bracket T1-48 case top ", rise + case_top_above_rail + TV_TOP_MARGIN,
            " exceeds tv_top_clear=", tv_top_clear));
    assert(rise + centre_y_max <= tv_top_clear - TV_TOP_MARGIN + MCC_EPS,
        str("mcc: arch-tv-bracket T1-48 centre top edge ", rise + centre_y_max,
            " exceeds tv_top_clear-TV_TOP_MARGIN=", tv_top_clear - TV_TOP_MARGIN));

    // T1-49 (A3): an arch, not a V.
    assert(rise >= -MCC_EPS,
        str("mcc: arch-tv-bracket T1-49 TV too short above the screws: needs TV_TOP_CLEAR >= ",
            TV_TOP_MARGIN + case_top_above_rail,
            "; a V variant is a new user decision (tv_top_clear=", tv_top_clear, ", rise=", rise, ")"));

    // T1-50 (A4): catches a typo past the user's own upper bound.
    assert(tv_top_clear < TV_TOP_CLEAR_MAX,
        str("mcc: arch-tv-bracket T1-50 tv_top_clear=", tv_top_clear,
            " must be < TV_TOP_CLEAR_MAX=", TV_TOP_CLEAR_MAX));

    // T1-51 (A5): the +X slide-on sweep clears the right arm's pad (§1.3). D44: the case floor rides
    // flush at z_rail (no pedestal), so there is no MCC_FLOOR_T term any more.
    assert(z_rail - arm_top_z >= ARCH_SWEEP_CLR - MCC_EPS,
        str("mcc: arch-tv-bracket T1-51 slide-on sweep clearance=", z_rail - arm_top_z,
            " below ARCH_SWEEP_CLR=", ARCH_SWEEP_CLR));

    // T1-52 (A6): rib proportions (fdm-rugged-enclosure-guidelines.md:67-68, D22).
    assert(RIB_T <= 0.6 * ARCH_PLATE_T,
        str("mcc: arch-tv-bracket T1-52 rib thickness ", RIB_T, " exceeds 0.6x plate thickness ",
            ARCH_PLATE_T, " (fdm-rugged-enclosure-guidelines.md:67)"));
    assert(RIB_H <= MCC_RIB_HEIGHT_RATIO_MAX * RIB_T,
        str("mcc: arch-tv-bracket T1-52 rib height ", RIB_H, " exceeds ", MCC_RIB_HEIGHT_RATIO_MAX,
            "x rib thickness ", RIB_T, " (fdm-rugged-enclosure-guidelines.md:68, D22)"));

    // T1-53 (A7): the rail must sit entirely on the centre body.
    assert(MCC_RAIL_LEN / 2 + MCC_RAIL_END_STOP_L + MCC_WALL <= C_HALF,
        str("mcc: arch-tv-bracket T1-53 rail footprint half-length+wall=",
            MCC_RAIL_LEN / 2 + MCC_RAIL_END_STOP_L + MCC_WALL, " exceeds C_HALF=", C_HALF));
    assert(RAIL_KEEPOUT_Y[1] <= CENTRE_W / 2 + MCC_EPS && RAIL_KEEPOUT_Y[0] >= -CENTRE_W / 2 - MCC_EPS,
        str("mcc: arch-tv-bracket T1-53 rail keep-out Y span ", RAIL_KEEPOUT_Y,
            " exceeds +/-CENTRE_W/2=", CENTRE_W / 2));

    // T1-54 (A8, B1 fix): every M3 counterbore, both laps, clears the (B1-shifted) rail keep-out
    // rectangle by >= ARCH_KEEPOUT_CLR. Circle-rect distance, not an x-only check (the plan's own
    // original table under-checked this).
    m3_counterbore_r = (M3_HEAD_D + 2 * MCC_CLR_SLIDE) / 2;
    for (side = [-1, 1], h = _mcc_arch_tv_joint_holes(g)) {
        p   = _mcc_arch_tv_xform(h, side, g);
        gap = _mcc_arch_tv_circle_rect_gap(p, m3_counterbore_r, RAIL_KEEPOUT_X, RAIL_KEEPOUT_Y);
        assert(gap >= ARCH_KEEPOUT_CLR - MCC_EPS,
            str("mcc: arch-tv-bracket T1-54 M3 counterbore at ", p, " (side=", side,
                ") clears the rail keep-out by ", gap, ", below ARCH_KEEPOUT_CLR=", ARCH_KEEPOUT_CLR));
    }

    // T1-55 (A9, B2 fix): sample every rib EDGE (not just its end corners) from the rib end down to
    // x=0, in <= 1 mm steps, both edges of both ribs, both sides -- a corner can lie outside the
    // centre body rectangle via Y while the edge re-enters it further along.
    rib_end    = arm_len - LAP_L / 2 - LAP_RIB_GAP;
    n_samples  = max(2, ceil(rib_end / 1.0) + 1);
    for (side = [-1, 1], sy = [-1, 1], edge = [0, 1], i = [0:n_samples - 1]) {
        x      = rib_end * i / (n_samples - 1);
        y_line = sy * (edge == 0 ? ARM_W / 2 : ARM_W / 2 - RIB_T);
        p      = _mcc_arch_tv_xform([x, y_line], side, g);
        gap    = _mcc_arch_tv_circle_rect_gap(p, 0, [-C_HALF, C_HALF], [-CENTRE_W / 2, CENTRE_W / 2]);
        assert(gap >= ARCH_KEEPOUT_CLR - MCC_EPS,
            str("mcc: arch-tv-bracket T1-55 rib edge sample at ", p, " (side=", side,
                ") clears the centre body by ", gap, ", below ARCH_KEEPOUT_CLR=", ARCH_KEEPOUT_CLR));
    }

    // T1-56 (A10): insert-bore depth + skin, and hole edge distances
    // (fdm-rugged-enclosure-guidelines.md:127, >= 2 mm hole wall to any part edge).
    insert_hole_d = struct_val(MCC_INSERT_M3, "hole_d");
    insert_len    = struct_val(MCC_INSERT_M3, "len");
    bore_depth    = insert_len + 1; // mcc_heat_set_bore()'s own module contract (fasteners.scad).
    assert(bore_depth + 1.0 <= ARCH_PLATE_T + MCC_EPS,
        str("mcc: arch-tv-bracket T1-56 insert bore depth+skin=", bore_depth + 1.0,
            " exceeds ARCH_PLATE_T=", ARCH_PLATE_T));
    edge_across = ARM_W / 2 - JOINT_P / 2 - insert_hole_d / 2;
    edge_along  = LAP_L / 2 - JOINT_S / 2 - insert_hole_d / 2;
    edge_pp     = JOINT_P - insert_hole_d;
    edge_ss     = JOINT_S - insert_hole_d;
    assert(edge_across >= 2.0, str("mcc: arch-tv-bracket T1-56 across-edge distance=", edge_across, " below 2.0 mm"));
    assert(edge_along  >= 2.0, str("mcc: arch-tv-bracket T1-56 along-edge distance=", edge_along, " below 2.0 mm"));
    assert(edge_pp >= 2.0, str("mcc: arch-tv-bracket T1-56 hole-to-hole (P) distance=", edge_pp, " below 2.0 mm"));
    assert(edge_ss >= 2.0, str("mcc: arch-tv-bracket T1-56 hole-to-hole (S) distance=", edge_ss, " below 2.0 mm"));

    // T1-57 (A11): the M3 screw stack (§3.3) -- tip clears the bore floor, and engagement is real.
    m3_counterbore_depth = M3_COUNTERBORE_DEPTH;
    m3_head_seat_z = z_rail - m3_counterbore_depth;
    m3_tip_z       = m3_head_seat_z - M3_JOINT_SCREW_L;
    bore_floor_z   = ARCH_PLATE_T - bore_depth;
    engagement     = ARCH_PLATE_T - m3_tip_z;
    assert(m3_tip_z >= bore_floor_z + 0.5 - MCC_EPS,
        str("mcc: arch-tv-bracket T1-57 M3 tip z=", m3_tip_z, " must clear bore floor+0.5=", bore_floor_z + 0.5));
    assert(engagement >= 1.5 * MCC_M3_MAJOR_D - MCC_EPS,
        str("mcc: arch-tv-bracket T1-57 M3 engagement=", engagement,
            " below 1.5x major diameter=", 1.5 * MCC_M3_MAJOR_D));

    // T1-58 (A12): M8 pad -- clamp thickness and boss wall (§3.4).
    m8_counterbore_d = M8_WASHER_D + 2 * MCC_CLR_SLIDE;
    boss_wall = (PAD_BOSS_D - m8_counterbore_d) / 2;
    assert(pad_clamp_t >= 2 * MCC_WALL - MCC_EPS,
        str("mcc: arch-tv-bracket T1-58 pad_clamp_t=", pad_clamp_t, " below 2xMCC_WALL=", 2 * MCC_WALL));
    assert(boss_wall >= 2 * MCC_WALL - MCC_EPS,
        str("mcc: arch-tv-bracket T1-58 pad boss wall=", boss_wall, " below 2xMCC_WALL=", 2 * MCC_WALL));

    // T1-59 (A13, B1 updated): the case hangs BETWEEN the screws (user decision), now accounting
    // for the B1 RAIL_X shift.
    assert(l_max / 2 + abs(RAIL_X) + 10 <= HALF_PITCH - PAD_BOSS_D / 2 + MCC_EPS,
        str("mcc: arch-tv-bracket T1-59 case half-width+RAIL_X+10=", l_max / 2 + abs(RAIL_X) + 10,
            " exceeds HALF_PITCH-PAD_BOSS_D/2=", HALF_PITCH - PAD_BOSS_D / 2));

    // T1-60 (B3): the UP-arrow deboss stays inside the body edge and outside the rail keep-out, by
    // >= ARCH_KEEPOUT_CLR on both sides.
    arrow_y = (RAIL_KEEPOUT_Y[1] + CENTRE_W / 2) / 2;
    assert(arrow_y - ARROW_W / 2 >= RAIL_KEEPOUT_Y[1] + ARCH_KEEPOUT_CLR - MCC_EPS,
        str("mcc: arch-tv-bracket T1-60 UP-arrow bottom edge ", arrow_y - ARROW_W / 2,
            " too close to the rail keep-out (y_max=", RAIL_KEEPOUT_Y[1], ")"));
    assert(arrow_y + ARROW_W / 2 <= CENTRE_W / 2 - ARCH_KEEPOUT_CLR + MCC_EPS,
        str("mcc: arch-tv-bracket T1-60 UP-arrow top edge ", arrow_y + ARROW_W / 2,
            " too close to the body edge (CENTRE_W/2=", CENTRE_W / 2, ")"));
}

// -----------------------------------------------------------------------------------------
// Geometry -- the two exported parts (§10 step 2.6/2.7).
// -----------------------------------------------------------------------------------------

// Module: mcc_arch_tv_arm()
// Usage:
//   mcc_arch_tv_arm(g);
// Description:
//   The exported "arm" part (printed TWICE -- PLAN-ASSUMPTION-4): a flat bar from the M8 pad
//   (origin) to the joint lap, with a rounded pad end, a taller boss carrying the M8 counterbore,
//   two top-face edge ribs, and 4 heat-set insert bores in the lap. TV face on the bed (local Z=0).
module mcc_arch_tv_arm(g) {
    arm_len   = struct_val(g, "arm_len");
    arm_top_z = struct_val(g, "arm_top_z");
    rib_end   = arm_len - LAP_L / 2 - LAP_RIB_GAP;

    m8_counterbore_d     = M8_WASHER_D + 2 * MCC_CLR_SLIDE;
    m8_counterbore_depth = M8_WASHER_H + M8_HEAD_K + 0.4;

    difference() {
        union() {
            // Bar (0 -> arm_len+LAP_L/2, the lap is simply the bar's own tail) + rounded pad end.
            cuboid([arm_len + LAP_L / 2, ARM_W, ARCH_PLATE_T], anchor = LEFT + BOTTOM);
            cyl(h = ARCH_PLATE_T, d = ARM_W, anchor = BOTTOM, $fn = 64, circum = true);
            // Pad boss: taller than the plate, carries the M8 counterbore (narrower than the pad
            // end disc above -- ARM_W=40 > PAD_BOSS_D=30 -- so it sits within/on top of it).
            cyl(h = arm_top_z, d = PAD_BOSS_D, anchor = BOTTOM, $fn = 64, circum = true);
            // Edge ribs, top face, stop LAP_RIB_GAP short of the lap.
            for (sy = [-1, 1])
                translate([0, sy * (ARM_W / 2 - RIB_T / 2), ARCH_PLATE_T])
                    cuboid([rib_end, RIB_T, RIB_H], anchor = LEFT + BOTTOM);
        }
        // M8 through-hole (full height) + counterbore from the top (§3.4).
        translate([0, 0, -MCC_EPS])
            cyl(h = arm_top_z + 2 * MCC_EPS, d = MCC_M8_CLR_D, anchor = BOTTOM, $fn = 64, circum = true);
        translate([0, 0, arm_top_z + MCC_EPS])
            cyl(h = m8_counterbore_depth + MCC_EPS, d = m8_counterbore_d, anchor = TOP, $fn = 64, circum = true);
        // 4 heat-set insert bores in the lap (open face at the arm's own top, ARCH_PLATE_T).
        for (h = _mcc_arch_tv_joint_holes(g))
            translate([h[0], h[1], ARCH_PLATE_T])
                mcc_heat_set_bore(MCC_INSERT_M3);
    }
}

// Module: mcc_arch_tv_centre()
// Usage:
//   mcc_arch_tv_centre(g);
// Description:
//   The exported "centre" part: a flat body carrying two angled tabs (the arms' own lap footprint,
//   keying the assembly to one orientation -- §3.1) and the male mount rail on top, with 4 M3
//   counterbored clearance holes per tab and a cosmetic "UP" arrow deboss (§3.5, B3). Bottom (TV-
//   facing, but standing 11 mm off the TV -- PLAN-ASSUMPTION-3) face on the bed (local Z=0).
module mcc_arch_tv_centre(g) {
    z_rail = struct_val(g, "z_rail");
    m3_counterbore_d     = M3_HEAD_D + 2 * MCC_CLR_SLIDE;
    m3_counterbore_depth = M3_COUNTERBORE_DEPTH;
    arrow_y = (RAIL_KEEPOUT_Y[1] + CENTRE_W / 2) / 2;

    // The rail is unioned AFTER the plate's own cuts: its latch arm's leg fills the window
    // mcc_rail_male_window() cuts through this plate (issue #46, D34) down to the bed.
    union() {
    difference() {
        union() {
            cuboid([2 * C_HALF, CENTRE_W, ARCH_PLATE_T], anchor = BOTTOM);
            // Two tabs = the arm laps' own footprint, same transform as the arms themselves
            // (_mcc_arch_tv_place(), re-expressed in centre-local coordinates) -- the angled tabs
            // are what gives the "boomerang" outline, and key the centre to one orientation only
            // (it cannot be flipped: the rail would then face the TV).
            for (side = [-1, 1])
                _mcc_arch_tv_place(g, side)
                    translate([struct_val(g, "arm_len"), 0, 0])
                        cuboid([LAP_L, ARM_W, ARCH_PLATE_T], anchor = BOTTOM);
        }
        translate([RAIL_X, 0, ARCH_PLATE_T]) rotate([0, 0, 180]) mcc_rail_male_window(plate_t = ARCH_PLATE_T);
        // 4 M3 counterbored clearance holes per tab, same placement transform as the tabs above.
        for (side = [-1, 1], h = _mcc_arch_tv_joint_holes(g)) {
            p = _mcc_arch_tv_xform(h, side, g);
            translate([p[0], p[1], -MCC_EPS])
                cyl(h = ARCH_PLATE_T + 2 * MCC_EPS, d = MCC_M3_CLR_D, anchor = BOTTOM, $fn = 64, circum = true);
            translate([p[0], p[1], z_rail + MCC_EPS])
                cyl(h = m3_counterbore_depth + MCC_EPS, d = m3_counterbore_d, anchor = TOP, $fn = 64, circum = true);
        }
        // Cosmetic "UP" arrow deboss, top face, pointing +Y -- outside the rail keep-out and below
        // the body edge (T1-60), never in contact with the mated case (it sits below Z_RAIL).
        translate([-30, arrow_y, z_rail - ARROW_DEPTH])
            linear_extrude(height = ARROW_DEPTH + MCC_EPS)
                polygon([[-ARROW_W / 2, -ARROW_L / 2], [ARROW_W / 2, -ARROW_L / 2], [0, ARROW_L / 2]]);
    }
    // Rail (B1: RAIL_X-centred on this plate) -- the standard rotate([0,0,180]) rail call, lifted
    // onto this plate's own top face; plate_t lets the latch arm's leg reach the bed.
    translate([RAIL_X, 0, ARCH_PLATE_T]) rotate([0, 0, 180]) mcc_rail_male(plate_t = ARCH_PLATE_T);
    }
}

// -----------------------------------------------------------------------------------------
// Top-level: geometry derivation + Tier-1 asserts, run on EVERY render (part dispatch below).
// -----------------------------------------------------------------------------------------

G = mcc_arch_tv_geom(tv_top_clear = TV_TOP_CLEAR);
mcc_arch_tv_assert(G);

echo(str("arch-tv-bracket: tv_top_clear=", struct_val(G, "tv_top_clear"), " (assumed unless measured, M18a)",
    " rise=", struct_val(G, "rise"), " alpha=", struct_val(G, "alpha"), " arm_len=", struct_val(G, "arm_len"),
    " arm_bbox=", struct_val(G, "arm_bbox"), " centre_bbox=", struct_val(G, "centre_bbox"),
    " pad_clamp_t=", struct_val(G, "pad_clamp_t"), " slide_clear=", struct_val(G, "slide_clear")));

// -----------------------------------------------------------------------------------------
// §6: previews (non-exported, invisible to build.py -- discover_brackets() only ever asks for the
// "arm"/"centre" parts named by this file's own header-line parts marker, above).
// -----------------------------------------------------------------------------------------

if (part == "arm") {
    mcc_arch_tv_arm(G);

} else if (part == "centre") {
    mcc_arch_tv_centre(G);

} else if (part == "assembly" || part == "assembly_sweep") {
    rise = struct_val(G, "rise");
    z_rail = struct_val(G, "z_rail");
    l_max = struct_val(G, "l_max");

    // Both arms, TV face on Z=0 (the assembly frame's own TV back plane).
    for (side = [-1, 1])
        color("Silver") _mcc_arch_tv_place_assembly(G, side) mcc_arch_tv_arm(G);

    // Centre, stacked on the arms' laps.
    translate([0, rise, ARCH_PLATE_T])
        color("LightSteelBlue") mcc_arch_tv_centre(G);

    // Translucent ghost TV-back slab (z in [-3,0]) + a thin red line at the TV's own top edge
    // (y = tv_top_clear) -- verify-by-picture (#26's own rule): confirm the case top stays below
    // the red line, and (assembly_sweep only) the case floor clears the right arm's pad.
    %translate([0, -HALF_PITCH, -3]) cuboid([2 * HALF_PITCH + 100, 2 * HALF_PITCH + TV_TOP_CLEAR_MAX, 3], anchor = BOTTOM);
    color("Red") translate([0, struct_val(G, "tv_top_clear"), 0]) cuboid([2 * HALF_PITCH + 100, 1, 1]);

    // Grey ghost M8 heads, seated in each pad's counterbore.
    for (side = [-1, 1])
        color("Gray") translate([side * HALF_PITCH, 0, struct_val(G, "arm_top_z") - (M8_HEAD_K / 2 + 0.4)])
            cyl(h = M8_HEAD_K, d = M8_WASHER_D, anchor = CENTER, $fn = 64, circum = true);

    // Ghost case, mated onto the rail -- the Plus-family SKU that ships the fan (CLAUDE.md fixed
    // decision), same variant its own case.scad uses. "assembly_sweep" shifts it by slide_clear
    // (B6) to show the floor passing over the right arm and pad during the +X slide-on approach.
    dev = MCC_DEV_PRO_CONVERT_HDMI_PLUS;
    variant = [["fan", true], ["splitter", false], ["fan_switch", true], ["tripod_insert", false], ["lid_vents", true]]; // tripod off: T1-63 (D44)
    layout = mcc_case_layout(dev, variant);
    x_shift = (part == "assembly_sweep") ? struct_val(G, "slide_clear") : 0;

    translate([RAIL_X + x_shift, rise + MCC_RAIL_Y, z_rail]) rotate([0, 0, 180]) { // D44: flush
        color("SlateGray") mcc_shell_base(dev = dev, cfg = variant);
        color("LightSteelBlue", 0.6) mcc_shell_lid(dev = dev, cfg = variant);
        translate([struct_val(layout, "x_dev_c"), struct_val(layout, "y_dev_c"),
                   struct_val(layout, "z_dev_lo") + mcc_dev_size(dev)[2] / 2])
            mcc_ghost(dev, show = true); // force-shown regardless of MCC_SHOW_GHOST (preview only).
    }

} else {
    assert(false, str("mcc: unknown part \"", part, "\""));
}

// vim: expandtab tabstop=4 shiftwidth=4 softtabstop=4 nowrap
