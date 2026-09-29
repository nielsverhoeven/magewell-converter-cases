//////////////////////////////////////////////////////////////////////
// models/brackets/vertical-tv-bracket.scad
//   L4-equivalent assembly (architecture.md §3 rev 18, layout-patch-wall.md §17.2). Issue #56,
//   implemented per docs/plans/2026-09-28-vesa-column-bracket.md (plan D rev 2), as amended by the
//   architect verdict's binding changes DB1-DB16 (D-vesa-400x300-bracket.VERDICT-rev2.md) -- the
//   verdict SUPERSEDES the plan wherever they differ, and every rail-dependent number below is a
//   FORMULA re-derived from the real, post-plan-F `lib/mcc/rail.scad` (mcc_rail_male() /
//   mcc_rail_male_keepout() only -- DB1; never `mcc_rail_male_window()`, never a `MCC_RAIL_LATCH_*`
//   constant, never the rail's own footprint re-assembled by hand).
//
//   Mounts SANDWICHED on ONE vertical VESA column (400x300 pattern, 300 mm pitch): the Samsung TV's
//   own TV lift already uses all four VESA screws, so this bracket clamps between the TV and the
//   lift on longer M8 bolts through a FLAT pad -- no counterbore, no washer seat (R42, user decision
//   2026-09-28: ASA accepted in the clamp path, no steel sleeves). The lift's other, unused column
//   gets two printed ASA spacer discs (same clamp height/footprint as this bracket's own pad) so the
//   lift's rail stays coplanar across both columns.
//
//   Layout: the +X column (seen from behind the TV, R43), case OUTBOARD, slid on from the TV's edge
//   side. This is the ONLY physically valid layout once the TV lift occupies both columns (a case
//   floor cannot pass over the lift's own rail) -- there is no mirror: `COLUMN_SIDE` does not exist
//   in this file, and never will (DO-NOT, verdict rev 2).
//
//   Hub topology (A1, carried from the rev-1 verdict): the two VESA screws on this column, at
//   assembly (0, +HALF_PITCH_V) and (0, -HALF_PITCH_V), are related by reflection about the
//   assembly's own X axis. One arm part, printed TWICE, is placed at rotate(-ALPHA) for the top screw
//   and rotate(+ALPHA) for the bottom one -- for an arm shape symmetric about its own long axis this
//   reproduces the correct mirror pair by pure rotation, no `mirror()`, no chirality change (proof:
//   see the header of the plan's own §3.4). Both arms meet a single centre plate that carries the
//   rail on its top face.
//
//   Frame (viewed from BEHIND the TV, the installer's own view, matching arch-tv-bracket.scad):
//     - Assembly frame origin: the +X column's own screw midpoint, on the TV back (Z=0). +X toward
//       the TV's edge (outboard, "reach" direction), +Y real "up", +Z away from the TV. Screw
//       centres at (0, +HALF_PITCH_V), (0, -HALF_PITCH_V).
//     - Arm print frame: pad centre at the origin, arm axis = local +X (toward the joint), TV face
//       on the bed (Z=0).
//     - Centre print frame: origin = the rail centre projected onto the centre's own bottom face;
//       that bottom face (TV-facing, standing VTV_PLATE_T off the TV -- forced by the +X slide-on
//       sweep, same reasoning as arch-tv-bracket.scad's own PLAN-ASSUMPTION-3) sits on the bed.
//     - Spacer print frame: a flat disc, TV face on the bed.
//
//   Z stack (TV back = 0):
//     Arm TV face / centre gap floor ................... Z = 0
//     Arm top face = centre bottom face (stacked lap) ... Z = VTV_PLATE_T        (= 11)
//     Rail mounting face (centre top) Z_RAIL ............ Z = 2 * VTV_PLATE_T    (= 22, FLUSH -- no
//         pedestal since plan A/D44; case floor rests here at full mate and while sliding)
//     Arm feature top (ribs only -- the pad is FLAT/flush at VTV_PLATE_T, no boss, no counterbore,
//         R42/DB5/DB7) ................................. Z = VTV_PLATE_T + RIB_H (= 20)
//     Case lid top ........................................ Z = 22 + 51 = 73     (H, CLAUDE.md)
//   Sweep condition (B5/T1-74): the only feature the case's floor must clear while sliding on is the
//   ribs (the pad is lower than they are): 2*VTV_PLATE_T - (VTV_PLATE_T + RIB_H) >= SWEEP_CLR, i.e.
//   T >= 11 -- same derivation and same value as arch-tv-bracket.scad's own ARCH_PLATE_T (plan A
//   B7), reused verbatim because the physical reason (no pedestal, same rib height ratio) is
//   identical.
//
//   Assert ids: T1-70 ... T1-85 (architect-assigned, D-vesa-400x300-bracket.VERDICT-rev2.md, "Ids
//   for rev 18"), one T1- id per plan B1...B16 in order (B16/T1-85 is new -- DB5, the spacer).
//
//   PRINT GATE: do not print this bracket FOR USE before M15 (the rail-lock coupon,
//   models/coupons/rail-lock.scad), M20 (the TV and TV-lift measurements below) and M22 (the sandwich tilt/preload
//   check) are closed. The released STL is rendered at every M20 figure's own placeholder; a
//   measured TV/lift needs `-D W_LIFT_RAIL=<mm> -D T_LIFT_RAIL=<mm> -D WALL_GAP=<mm>` and a
//   re-golden.
//
// build.py: parts = arm, centre, spacer
// build.py: print_count = arm:2, spacer:2
//   (top + bottom arm: arm.3mf and the review project carry both copies; two spacers for the lift's
//   other, unoccupied column.)
//
// Render:
//   openscad --backend=Manifold -D 'part="arm"' -o out/arm.stl models/brackets/vertical-tv-bracket.scad
//   openscad --backend=Manifold -D 'part="centre"' -o out/centre.stl models/brackets/vertical-tv-bracket.scad
//   openscad --backend=Manifold -D 'part="spacer"' -o out/spacer.stl models/brackets/vertical-tv-bracket.scad
//   openscad --backend=Manifold -D 'part="assembly"' -o out/assembly.stl models/brackets/vertical-tv-bracket.scad
//   openscad --backend=Manifold -D 'part="assembly_sweep"' -o out/assembly_sweep.stl models/brackets/vertical-tv-bracket.scad
//////////////////////////////////////////////////////////////////////

$fa = 1; $fs = 0.4; // the ONLY place $fn-adjacent globals are set (openscad-authoring skill).

include <mcc/mcc.scad>
// All 8 device records: this file's own case-envelope loop (_mcc_vert_tv_envelope_max(), a fresh
// copy, never shared with arch-tv-bracket.scad's _ARCH_TV_DEVS) must cover every current SKU. A
// future 9th SKU is added to BOTH the include list below and _VERT_TV_DEVS in one place (see the
// new-case-variant skill's second, independent checklist bullet for this file).
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
// Parameters (this bracket's own authored dimensions -- bracket-own geometry stays out of
// constants.scad, the models/brackets convention). Sourced from plan D rev 2 §4, corrected by the
// architect verdict's binding changes where they differ (DB5, DB7).
// -----------------------------------------------------------------------------------------

VESA_H_PITCH = 400; // mm. Documentation only -- Samsung 400x300 VESA; not consumed by this file's
                     // own geometry (this bracket mounts on ONE column, so only the vertical pitch
                     // below matters to the math).
VESA_V_PITCH = 300; // mm. assumed -- common Samsung 400x300 deviation from a square MIS-F pattern;
                     // M20 confirms the exact TV model's real pitch.
HALF_PITCH_V = VESA_V_PITCH / 2; // = 150. derived.

TV_SIDE_CLEAR = 500; // mm. assumed default -- user-confirmed NON-BINDING (2026-09-28: "space around
                      // the column is not a constraint"), kept as a named, asserted parameter (B2)
                      // for cheap insurance against a future parameter edit, not because this user's
                      // own TV is expected to bind it. Override per TV with `-D TV_SIDE_CLEAR=<mm>`.
TV_SIDE_MARGIN = 10.0; // mm. assumed -- mirrors arch-tv-bracket.scad's own TV_TOP_MARGIN.

W_LIFT_RAIL = 60.0; // mm. assumed, M20 -- the TV lift's own rail/plate width at the column. Feeds
                     // REACH_KEEPOUT and RIB_PAD_GAP.
T_LIFT_RAIL = 5.0;  // mm. assumed, M20 -- the TV lift's own rail/plate thickness at the column. No
                     // geometry in THIS file uses it directly (unlike arch-tv-bracket.scad's
                     // sandwich mode, whose sweep crosses a column and so needs a Z-clearance rise);
                     // it feeds only the BOM's M8 bolt-length formula (BOM.md).
WALL_GAP = 150.0;   // mm. User-stated 2026-09-28 ("150-200 mm behind the TV" on a TV-lift mount) --
                     // 150 is the conservative end of that range, asserted against this bracket's
                     // own lid-top Z (B14). The lift's own exact standoff stays `assumed` pending M20.

VTV_PLATE_T = 11.0; // mm. Derived minimum, identical derivation to arch-tv-bracket.scad's own
                     // ARCH_PLATE_T (plan A/D44): the +X slide-on sweep must clear the ribs once the
                     // rail carries no pedestal -- 2T - (T + RIB_H) >= SWEEP_CLR gives T >= 11.
RIB_T = MCC_WALL;    // = 3.0. <= 0.6 x VTV_PLATE_T (fdm-rugged-enclosure-guidelines.md:67).
RIB_H = MCC_RIB_HEIGHT_RATIO_MAX * RIB_T; // = 9.0 (fdm-rugged-enclosure-guidelines.md:68, D22).
SWEEP_CLR = 2.0;     // mm. assumed -- same magnitude as arch-tv-bracket.scad's own ARCH_SWEEP_CLR.
ARM_W = 40.0;        // mm. assumed -- arm width; carries the 2x2 joint pattern, two edge ribs and
                      // the M8 pad.
KEEPOUT_CLR = 1.0;   // mm. assumed -- clearance used by every hole-vs-rail / rib-vs-body /
                      // rib-vs-lift-rail assert; mirrors arch-tv-bracket.scad's own
                      // ARCH_KEEPOUT_CLR.

// DB5: the pad is not a separate raised boss -- it IS the arm's own rounded end (a flat disc, flush
// with the plate, no counterbore, R42/DB7). Its diameter is named PAD_D purely so the asserts below
// read the same way arch-tv-bracket.scad's PAD_BOSS_D-based ones do; it is not a new shape.
PAD_D = ARM_W; // = 40.0. DB5 -- was a separate PAD_BOSS_D=30 boss diameter pre-verdict; deleted.

CENTRE_HALF_L = 90.0; // mm. assumed -- centre-body half-length (was C_HALF pre-verdict; renamed only
                       // to avoid a same-named-different-meaning clash with arch's own C_HALF, which
                       // this file never references). The rail keep-out's X half-length is
                       // MCC_RAIL_LEN/2 = 68 (no end-stop flange since D34), leaving a 22 mm end web
                       // (>= MCC_WALL, asserted B7/T1-76).
LAP_L = 30.0;    // mm. assumed -- lap length along the arm axis. Same M3 insert class/edge-distance
                  // arithmetic as arch-tv-bracket.scad.
JOINT_S = 14.0;  // mm. assumed -- joint hole pitch along the arm axis (2x2 pattern).
JOINT_P = 20.0;  // mm. assumed -- joint hole pitch across the arm axis.
LAP_RIB_GAP = 1.0; // mm. assumed -- a rib stops at least this far short of the lap (a cap on rib_end,
                    // DB3; the binding bound is usually the centre-body clearance below it, not this
                    // one, at every current parameter).

// M3 socket-head cap screw -- ISO 4762 nominal, same status/class as arch-tv-bracket.scad's own
// M3_HEAD_D/M3_HEAD_K (PLAN-ASSUMPTION-9-class, not sourced in knowledge/**).
M3_HEAD_D = 5.5; // mm.
M3_HEAD_K = 3.0; // mm.
M3_COUNTERBORE_DEPTH = M3_HEAD_K + 1.3; // = 4.3. Matches arch-tv-bracket.scad's own re-derived value
                                          // at the same 11 mm plate thickness (plan A B7's precedent).
M3_JOINT_SCREW_L = 12; // mm. Derived stock length -- same screw-stack derivation as
                        // arch-tv-bracket.scad's own M3_JOINT_SCREW_L at the same z_rail=22 (B11/T1-80).

// M8 socket-head cap screw + ISO 7089 washer -- used only for BOM/washer geometry now: the pad
// itself carries no counterbore (R42/DB5/DB7), so nothing here seats a bolt head or washer.
M8_HEAD_K   = 8.0;  // mm.
M8_WASHER_D = 16.0; // mm.
M8_WASHER_H = 1.6;  // mm.

ARROW_DEPTH = 0.6; // mm. assumed, cosmetic "UP" deboss (A5 -- a cue, not a key: nothing else keys
                    // this assembly against a 180 deg-about-Z install, which the hub topology's own
                    // top/bottom symmetry would otherwise let happen unnoticed).
ARROW_L = 8.0; // mm. assumed.
ARROW_W = 6.0; // mm. assumed.
ARROW_X = -30.0; // mm. assumed -- centre-local X of the arrow's own centre (fit-check FX1: named so
                  // T1-82's own counterbore-clearance check reads the same value the geometry draws).

// reused from constants.scad, no new library constant: MCC_M8_CLR_D, MCC_M3_CLR_D, MCC_INSERT_M3,
// MCC_RAIL_LEN, MCC_RAIL_Y, MCC_RAIL_MALE_H, MCC_M3_MAJOR_D, MCC_WALL, MCC_BUILD, MCC_BED_MARGIN,
// MCC_EPS, MCC_RIB_HEIGHT_RATIO_MAX, MCC_CLR_SLIDE.

// -----------------------------------------------------------------------------------------
// Rail keep-out, DB1: the rotated accessor range, never MCC_RAIL_LATCH_* or a hand-built rectangle.
// A rotate([0,0,180]) placement (this file's own rail call, below) negates and swaps both ranges --
// mcc_rail_male_keepout()'s own contract.
// -----------------------------------------------------------------------------------------
_VTV_RAIL_KO = mcc_rail_male_keepout(MCC_RAIL_LEN);
RAIL_KEEPOUT_X = [-_VTV_RAIL_KO[0][1], -_VTV_RAIL_KO[0][0]];
RAIL_KEEPOUT_Y = [-_VTV_RAIL_KO[1][1], -_VTV_RAIL_KO[1][0]];

// -----------------------------------------------------------------------------------------
// One list of devices feeding the case-envelope loop. A NEW SKU MUST BE ADDED HERE (and to the
// `include` list above) -- see the new-case-variant skill's second, independent checklist bullet.
// -----------------------------------------------------------------------------------------

_VERT_TV_ENV_CFG = [["fan", false], ["splitter", false], ["fan_switch", false]];

_VERT_TV_DEVS = [
    MCC_DEV_PRO_CONVERT_FOR_NDI_TO_AIO,
    MCC_DEV_PRO_CONVERT_FOR_NDI_TO_HDMI_4K,
    MCC_DEV_PRO_CONVERT_FOR_NDI_TO_HDMI,
    MCC_DEV_PRO_CONVERT_FOR_NDI_TO_SDI,
    MCC_DEV_PRO_CONVERT_HDMI_PLUS,
    MCC_DEV_PRO_CONVERT_HDMI_TX,
    MCC_DEV_PRO_CONVERT_SDI_PLUS,
    MCC_DEV_PRO_CONVERT_SDI_TX,
];

// Function: _mcc_vert_tv_envelope_max()
// Description:
//   Private, pure. [L_max, W_max, H_max] over every _VERT_TV_DEVS record under a
//   fan/splitter/switch-off config (same reasoning as arch-tv-bracket.scad's own
//   _mcc_arch_tv_envelope_max(): neither flag changes L/W/H on any current SKU).
function _mcc_vert_tv_envelope_max() =
    let(dims = [for (dev = _VERT_TV_DEVS) mcc_case_dims(dev, _VERT_TV_ENV_CFG)])
    [max([for (d = dims) d[0]]), max([for (d = dims) d[1]]), max([for (d = dims) d[2]])];

// -----------------------------------------------------------------------------------------
// Pure geometry function. Every asserted/echoed/drawn number derives from this ONE function (a
// BOSL2 struct, struct_val()-accessible) -- see mcc_vert_tv_assert() and the exported-part modules
// below. Parametrised exactly as plan D rev 2 §6 step 2.3 specifies, so tests/test_vertical_tv_
// bracket.scad can exercise other tv_side_clear/w_lift_rail/wall_gap values via `use`.
// -----------------------------------------------------------------------------------------

// Function: mcc_vert_tv_geom()
// Usage:
//   g = mcc_vert_tv_geom([tv_side_clear=], [w_lift_rail=], [wall_gap=]);
// Description:
//   Pure. Derives the whole bracket's geometry. See this file's header for the Z-stack table.
function mcc_vert_tv_geom(tv_side_clear = TV_SIDE_CLEAR, w_lift_rail = W_LIFT_RAIL, wall_gap = WALL_GAP) =
    let(
        env   = _mcc_vert_tv_envelope_max(),
        l_max = env[0], w_max = env[1], h_max = env[2],

        // DB5: REACH_KEEPOUT covers whichever is wider, this bracket's own flat pad or the TV
        // lift's own rail -- the case's own footprint must never overlap either.
        reach_keepout = max(PAD_D, w_lift_rail) / 2 + KEEPOUT_CLR,
        reach = l_max / 2 + reach_keepout,

        // DB4: YJ_V is the 2x2 joint pattern's own circumradius clear of the rail keep-out, derived
        // from the REAL accessor range (RAIL_KEEPOUT_Y), never a hand-picked literal.
        m3_counterbore_r = (M3_HEAD_D + 2 * MCC_CLR_SLIDE) / 2,
        yj_v = RAIL_KEEPOUT_Y[1] + KEEPOUT_CLR + m3_counterbore_r + norm([JOINT_S / 2, JOINT_P / 2]),

        // Hub topology (A1/§3.4): arm-local (arm_len, 0) [the joint/lap centre] maps to assembly
        // (reach, +-yj_v) via translate([0, +-HALF_PITCH_V]) o rotate(-+ALPHA). Solving
        // arm_len*cos(alpha)=reach, arm_len*sin(alpha)=HALF_PITCH_V-yj_v gives:
        alpha   = atan2(HALF_PITCH_V - yj_v, reach),
        arm_len = sqrt(pow(reach, 2) + pow(HALF_PITCH_V - yj_v, 2)),

        centre_h  = 2 * (yj_v + ARM_W / 2),
        z_rail    = 2 * VTV_PLATE_T,
        arm_top_z = VTV_PLATE_T + RIB_H,

        // DB2: where the ribs may start (arm-local x), derived in the ASSEMBLY frame so the arm's
        // own diagonal is accounted for -- the binding rib edge is the one toward the column
        // (arm-local y=-ARM_W/2); its assembly-X at x=rib_pad_gap sits exactly on the lift-rail
        // keep-out boundary.
        rib_pad_gap = (w_lift_rail / 2 + KEEPOUT_CLR + (ARM_W / 2) * sin(alpha)) / cos(alpha),

        // DB3: where the ribs must stop -- the smallest arm-local x at which the rib edge toward the
        // centre body (same binding edge, arm-local y=-ARM_W/2) enters the body rectangle (half-
        // height centre_h/2) inflated by KEEPOUT_CLR, capped by the lap-side rule.
        rib_entry_x = (HALF_PITCH_V - (ARM_W / 2) * cos(alpha) - (centre_h / 2 + KEEPOUT_CLR)) / sin(alpha),
        rib_end     = min(rib_entry_x, arm_len - LAP_L / 2 - LAP_RIB_GAP),

        // Arm print bbox: bar [0, arm_len+LAP_L/2] unioned with the rounded pad end (|x|<=ARM_W/2 at
        // x=0); Y=ARM_W; Z=arm_top_z (only the ribs reach it -- the flat pad does not, DB5/DB7).
        arm_bbox = [arm_len + LAP_L / 2 + ARM_W / 2, ARM_W, arm_top_z],

        // Centre print bbox (DB4): the tabs (each arm's own lap footprint, carried through the same
        // rotate+translate that places the arm) stick out beyond the plain body rectangle. Both
        // tabs are mirror images of each other in Y (hub topology), so the bbox is Y-symmetric and
        // only the top tab's own extremes need computing (closed form, valid for the whole feasible
        // alpha range: cos(alpha)>0, sin(alpha)>0).
        tab_x_max   = (LAP_L / 2) * cos(alpha) + (ARM_W / 2) * sin(alpha),
        tab_y_max   = yj_v + (LAP_L / 2) * sin(alpha) + (ARM_W / 2) * cos(alpha),
        centre_x_max = max(CENTRE_HALF_L, tab_x_max),
        centre_y_max = max(centre_h / 2, tab_y_max),
        centre_z_max = VTV_PLATE_T + MCC_RAIL_MALE_H, // = 14.5 (the rail's top; no end-stop flange since D34)
        centre_bbox  = [2 * centre_x_max, 2 * centre_y_max, centre_z_max],

        // Case footprint at full mate (assembly frame): centred on the rail axis (X=reach,
        // Y=MCC_RAIL_Y), spanning the device envelope.
        case_x_lo = reach - l_max / 2, case_x_hi = reach + l_max / 2,
        case_y_lo = MCC_RAIL_Y - w_max / 2, case_y_hi = MCC_RAIL_Y + w_max / 2,

        // DB5: the spacer matches the pad's own bearing footprint and clamp height exactly (R42) --
        // not a boss diameter, not the centre plate's thickness.
        spacer_d = PAD_D, spacer_t = VTV_PLATE_T
    )
    [
        ["tv_side_clear", tv_side_clear], ["w_lift_rail", w_lift_rail], ["wall_gap", wall_gap],
        ["l_max", l_max], ["w_max", w_max], ["h_max", h_max],
        ["reach_keepout", reach_keepout], ["reach", reach], ["yj_v", yj_v],
        ["alpha", alpha], ["arm_len", arm_len], ["centre_h", centre_h],
        ["z_rail", z_rail], ["arm_top_z", arm_top_z],
        ["rib_pad_gap", rib_pad_gap], ["rib_end", rib_end],
        ["arm_bbox", arm_bbox], ["centre_bbox", centre_bbox],
        ["centre_x_max", centre_x_max], ["centre_y_max", centre_y_max],
        ["case_x_lo", case_x_lo], ["case_x_hi", case_x_hi],
        ["case_y_lo", case_y_lo], ["case_y_hi", case_y_hi],
        ["spacer_d", spacer_d], ["spacer_t", spacer_t],
    ];

// -----------------------------------------------------------------------------------------
// The ONE joint-hole list and the ONE placement transform, consumed identically by the arm (insert
// bores) and the centre (counterbore clearance holes) so the two halves cannot drift (D6 one-source
// rule). Re-implemented in this file (never imported from arch-tv-bracket.scad, DB1/A2).
// -----------------------------------------------------------------------------------------

// Function: _mcc_vert_tv_joint_holes()
// Description:
//   Private, pure. 4 arm-local [x,y] joint-hole centres per lap (2x2 pattern at
//   (arm_len +/- JOINT_S/2, +/- JOINT_P/2)).
function _mcc_vert_tv_joint_holes(g) =
    let(a = struct_val(g, "arm_len"))
    [for (sx = [-1, 1], sy = [-1, 1]) [a + sx * JOINT_S / 2, sy * JOINT_P / 2]];

// Function: _mcc_vert_tv_theta()
// Description:
//   Private, pure. The in-plane rotation (degrees) that carries an arm-local point to the centre's
//   own local frame for the given `side` (+1 = top screw, -1 = bottom screw) -- §3.4's proof.
function _mcc_vert_tv_theta(g, side) =
    side > 0 ? -struct_val(g, "alpha") : struct_val(g, "alpha");

// Function: _mcc_vert_tv_rotate2()
// Description:
//   Private, pure. 2D rotation of point `p` by `theta` degrees about the origin.
function _mcc_vert_tv_rotate2(p, theta) =
    [p[0] * cos(theta) - p[1] * sin(theta), p[0] * sin(theta) + p[1] * cos(theta)];

// Function: _mcc_vert_tv_xform()
// Description:
//   Private, pure. Arm-local point `p` -> CENTRE-local [x,y], for `side` in {-1,+1}: the assembly
//   point translate([0, side*HALF_PITCH_V]) o rotate(theta), shifted by -reach in X (the centre's
//   own local frame is the assembly frame shifted so the rail sits at local X=0). Used by both the
//   assert module and, as the geometric mirror of module _mcc_vert_tv_place() below, to build the
//   tab/hole geometry.
function _mcc_vert_tv_xform(p, side, g) =
    [-struct_val(g, "reach"), side * HALF_PITCH_V] + _mcc_vert_tv_rotate2(p, _mcc_vert_tv_theta(g, side));

// Module: _mcc_vert_tv_place()
// Description:
//   Private. Places `children()` (authored in the ARM's own local frame) into the CENTRE's own
//   local frame, for the given `side`. Geometric mirror of _mcc_vert_tv_xform() above.
module _mcc_vert_tv_place(g, side) {
    translate([-struct_val(g, "reach"), side * HALF_PITCH_V, 0])
        rotate([0, 0, _mcc_vert_tv_theta(g, side)])
            children();
}

// Module: _mcc_vert_tv_place_assembly()
// Description:
//   Private, preview-only. Places `children()` (arm-local frame) into the ASSEMBLY frame -- same
//   rotation as _mcc_vert_tv_place(), but no reach-shift (the assembly frame's own X=0 IS the
//   screw column; only the centre's own local frame is shifted by `reach`).
module _mcc_vert_tv_place_assembly(g, side) {
    translate([0, side * HALF_PITCH_V, 0])
        rotate([0, 0, _mcc_vert_tv_theta(g, side)])
            children();
}

// Function: _mcc_vert_tv_circle_rect_gap()
// Description:
//   Private, pure. Gap (mm) between a circle (`center`, radius `r`) and an axis-aligned rectangle
//   (`rect_x`=[xmin,xmax], `rect_y`=[ymin,ymax]) -- negative when they overlap. Re-implemented here
//   (never imported from arch-tv-bracket.scad, DB1/A2).
function _mcc_vert_tv_circle_rect_gap(center, r, rect_x, rect_y) =
    let(
        cx = min(max(center[0], rect_x[0]), rect_x[1]),
        cy = min(max(center[1], rect_y[0]), rect_y[1])
    )
    norm([center[0] - cx, center[1] - cy]) - r;

// -----------------------------------------------------------------------------------------
// Tier-1 asserts (architecture.md §9). T1-70 ... T1-85 (plan D rev 2 B1...B16, in the architect
// verdict's own order -- D-vesa-400x300-bracket.VERDICT-rev2.md, "Ids for rev 18"). Kept in a PUBLIC
// module (not bare top-level statements) so tests/test_vertical_tv_bracket.scad can exercise them
// via `use`. Called at top level below so every render fires it.
// -----------------------------------------------------------------------------------------

// Module: mcc_vert_tv_assert()
// Usage:
//   mcc_vert_tv_assert(g);
module mcc_vert_tv_assert(g) {
    tv_side_clear = struct_val(g, "tv_side_clear");
    w_lift_rail   = struct_val(g, "w_lift_rail");
    wall_gap      = struct_val(g, "wall_gap");
    l_max         = struct_val(g, "l_max");
    reach         = struct_val(g, "reach");
    reach_keepout = struct_val(g, "reach_keepout");
    yj_v          = struct_val(g, "yj_v");
    alpha         = struct_val(g, "alpha");
    arm_len       = struct_val(g, "arm_len");
    centre_h      = struct_val(g, "centre_h");
    z_rail        = struct_val(g, "z_rail");
    arm_top_z     = struct_val(g, "arm_top_z");
    rib_pad_gap   = struct_val(g, "rib_pad_gap");
    rib_end       = struct_val(g, "rib_end");
    arm_bbox      = struct_val(g, "arm_bbox");
    centre_bbox   = struct_val(g, "centre_bbox");
    case_x_lo = struct_val(g, "case_x_lo"); case_x_hi = struct_val(g, "case_x_hi");
    case_y_lo = struct_val(g, "case_y_lo"); case_y_hi = struct_val(g, "case_y_hi");
    spacer_d = struct_val(g, "spacer_d"); spacer_t = struct_val(g, "spacer_t");
    h_max = struct_val(g, "h_max");

    // T1-70 (B1, DB4): the STRICTER per-side-bed-margin cap, on both bboxes, WITH the centre's own
    // tabs (its plain body rectangle alone understates the true footprint).
    max_axis = MCC_BUILD - 2 * MCC_BED_MARGIN; // = 244
    for (i = [0:2])
        assert(arm_bbox[i] <= max_axis + MCC_EPS,
            str("mcc: vertical-tv-bracket T1-70 arm bbox axis ", i, "=", arm_bbox[i],
                " exceeds MCC_BUILD-2*MCC_BED_MARGIN=", max_axis));
    for (i = [0:2])
        assert(centre_bbox[i] <= max_axis + MCC_EPS,
            str("mcc: vertical-tv-bracket T1-70 centre bbox axis ", i, "=", centre_bbox[i],
                " exceeds MCC_BUILD-2*MCC_BED_MARGIN=", max_axis));
    for (d = [struct_val(g, "spacer_d"), struct_val(g, "spacer_d"), struct_val(g, "spacer_t")])
        assert(d <= max_axis + MCC_EPS, str("mcc: vertical-tv-bracket T1-70 spacer bbox axis ", d, " exceeds ", max_axis));

    // T1-71 (B2): the case's own mated footprint stays clear of the TV's side edge -- the right
    // obstacle check for this bracket's fixed OUTBOARD layout (R43). User-confirmed non-binding, kept
    // as cheap insurance.
    assert(case_x_hi + TV_SIDE_MARGIN <= tv_side_clear + MCC_EPS,
        str("mcc: vertical-tv-bracket T1-71 case outboard edge+margin=", case_x_hi + TV_SIDE_MARGIN,
            " exceeds tv_side_clear=", tv_side_clear));

    // T1-72 (B3): REACH self-consistency (protects a future edit to either formula).
    assert(reach - l_max / 2 >= reach_keepout - MCC_EPS,
        str("mcc: vertical-tv-bracket T1-72 reach-l_max/2=", reach - l_max / 2,
            " below reach_keepout=", reach_keepout));

    // T1-73 (B4, DB5 PAD_D form): the case clears both screws' own pads in Y.
    assert(case_y_hi <= HALF_PITCH_V - PAD_D / 2 + MCC_EPS,
        str("mcc: vertical-tv-bracket T1-73 case_y_hi=", case_y_hi,
            " exceeds HALF_PITCH_V-PAD_D/2=", HALF_PITCH_V - PAD_D / 2));
    assert(case_y_lo >= -(HALF_PITCH_V - PAD_D / 2) - MCC_EPS,
        str("mcc: vertical-tv-bracket T1-73 case_y_lo=", case_y_lo,
            " below -(HALF_PITCH_V-PAD_D/2)=", -(HALF_PITCH_V - PAD_D / 2)));

    // T1-74 (B5): the +X slide-on sweep clears the ribs (the tallest feature -- the pad is flush and
    // lower, R42/DB5/DB7, so it drops out of this formula entirely).
    assert(z_rail - arm_top_z >= SWEEP_CLR - MCC_EPS,
        str("mcc: vertical-tv-bracket T1-74 slide-on sweep clearance=", z_rail - arm_top_z,
            " below SWEEP_CLR=", SWEEP_CLR));

    // T1-75 (B6): rib proportions (fdm-rugged-enclosure-guidelines.md:67-68, D22).
    assert(RIB_T <= 0.6 * VTV_PLATE_T,
        str("mcc: vertical-tv-bracket T1-75 rib thickness ", RIB_T, " exceeds 0.6x plate thickness ", VTV_PLATE_T));
    assert(RIB_H <= MCC_RIB_HEIGHT_RATIO_MAX * RIB_T,
        str("mcc: vertical-tv-bracket T1-75 rib height ", RIB_H, " exceeds ", MCC_RIB_HEIGHT_RATIO_MAX, "x rib thickness ", RIB_T));

    // T1-76 (B7): the rail sits entirely on the centre body -- its keep-out (mcc_rail_male_keepout(),
    // D50) plus an MCC_WALL end web inside +-CENTRE_HALF_L -- and its keep-out Y-span sits inside
    // +-centre_h/2.
    assert(RAIL_KEEPOUT_X[0] - MCC_WALL >= -CENTRE_HALF_L - MCC_EPS && RAIL_KEEPOUT_X[1] + MCC_WALL <= CENTRE_HALF_L + MCC_EPS,
        str("mcc: vertical-tv-bracket T1-76 rail keep-out X span ", RAIL_KEEPOUT_X, " + MCC_WALL=", MCC_WALL,
            " exceeds +/-CENTRE_HALF_L=", CENTRE_HALF_L));
    assert(RAIL_KEEPOUT_Y[1] <= centre_h / 2 + MCC_EPS && RAIL_KEEPOUT_Y[0] >= -centre_h / 2 - MCC_EPS,
        str("mcc: vertical-tv-bracket T1-76 rail keep-out Y span ", RAIL_KEEPOUT_Y,
            " exceeds +/-centre_h/2=", centre_h / 2));

    // T1-77 (B8, DB4): every M3 counterbore, both joints, clears the rail keep-out rectangle by
    // >= KEEPOUT_CLR -- a circle-rect distance per hole (yj_v is derived so the worst hole sits at
    // exactly this margin, not the joint centre's own, much larger gap).
    m3_counterbore_r = (M3_HEAD_D + 2 * MCC_CLR_SLIDE) / 2;
    for (side = [-1, 1], h = _mcc_vert_tv_joint_holes(g)) {
        p   = _mcc_vert_tv_xform(h, side, g);
        gap = _mcc_vert_tv_circle_rect_gap(p, m3_counterbore_r, RAIL_KEEPOUT_X, RAIL_KEEPOUT_Y);
        assert(gap >= KEEPOUT_CLR - MCC_EPS,
            str("mcc: vertical-tv-bracket T1-77 M3 counterbore at ", p, " (side=", side,
                ") clears the rail keep-out by ", gap, ", below KEEPOUT_CLR=", KEEPOUT_CLR));
    }

    // T1-78 (B9, DB2/DB3): sample every rib EDGE from rib_pad_gap to rib_end in <= 1 mm steps, both
    // edges of both ribs, both sides -- clear the centre body, clear the TV lift's own rail band
    // along the column, and clear the case's own mated footprint in Z where they overlap in X/Y.
    n_samples = max(2, ceil((rib_end - rib_pad_gap) / 1.0) + 1);
    for (side = [-1, 1], sy = [-1, 1], edge = [0, 1], i = [0:n_samples - 1]) {
        x      = rib_pad_gap + (rib_end - rib_pad_gap) * i / (n_samples - 1);
        y_line = sy * (edge == 0 ? ARM_W / 2 : ARM_W / 2 - RIB_T);
        p_centre   = _mcc_vert_tv_xform([x, y_line], side, g);
        gap_centre = _mcc_vert_tv_circle_rect_gap(p_centre, 0, [-CENTRE_HALF_L, CENTRE_HALF_L], [-centre_h / 2, centre_h / 2]);
        assert(gap_centre >= KEEPOUT_CLR - MCC_EPS,
            str("mcc: vertical-tv-bracket T1-78 rib edge sample at ", p_centre, " (side=", side,
                ") clears the centre body by ", gap_centre, ", below KEEPOUT_CLR=", KEEPOUT_CLR));

        // Assembly-frame X of the same sample, for the lift-rail-band check: the column runs along
        // assembly X=0 (this bracket's own screw column), width w_lift_rail.
        p_assembly_x = x * cos(alpha) + y_line * sin(alpha); // side cancels: HALF_PITCH_V*0 term drops
        assert(abs(p_assembly_x) >= w_lift_rail / 2 + KEEPOUT_CLR - MCC_EPS,
            str("mcc: vertical-tv-bracket T1-78 rib edge sample assembly X=", p_assembly_x, " (side=", side,
                ") clears the TV lift's rail band by ", abs(p_assembly_x) - w_lift_rail / 2,
                ", below KEEPOUT_CLR=", KEEPOUT_CLR));

        // Case-sweep clearance: only where the sample's assembly (X,Y) actually falls under the
        // case's own mated footprint does the Z clearance (T1-74's SWEEP_CLR) need re-checking here;
        // T1-74 already covers the worst case (the ribs' own top), so this is a redundant-by-
        // construction confirmation that no OTHER case footprint intrusion exists at a taller Z --
        // there is none, since every rib sample sits at the same Z=arm_top_z already checked.
    }

    // T1-79 (B10): insert-bore depth+skin, and hole edge distances (>= 2 mm hole wall to any part
    // edge, fdm-rugged-enclosure-guidelines.md:127).
    insert_hole_d = struct_val(MCC_INSERT_M3, "hole_d");
    insert_len    = struct_val(MCC_INSERT_M3, "len");
    bore_depth    = insert_len + 1; // mcc_heat_set_bore()'s own module contract (fasteners.scad).
    assert(bore_depth + 1.0 <= VTV_PLATE_T + MCC_EPS,
        str("mcc: vertical-tv-bracket T1-79 insert bore depth+skin=", bore_depth + 1.0, " exceeds VTV_PLATE_T=", VTV_PLATE_T));
    edge_across = ARM_W / 2 - JOINT_P / 2 - insert_hole_d / 2;
    edge_along  = LAP_L / 2 - JOINT_S / 2 - insert_hole_d / 2;
    edge_pp     = JOINT_P - insert_hole_d;
    edge_ss     = JOINT_S - insert_hole_d;
    assert(edge_across >= 2.0, str("mcc: vertical-tv-bracket T1-79 across-edge distance=", edge_across, " below 2.0 mm"));
    assert(edge_along  >= 2.0, str("mcc: vertical-tv-bracket T1-79 along-edge distance=", edge_along, " below 2.0 mm"));
    assert(edge_pp >= 2.0, str("mcc: vertical-tv-bracket T1-79 hole-to-hole (P) distance=", edge_pp, " below 2.0 mm"));
    assert(edge_ss >= 2.0, str("mcc: vertical-tv-bracket T1-79 hole-to-hole (S) distance=", edge_ss, " below 2.0 mm"));

    // T1-80 (B11): the M3 lap screw stack -- tip clears the bore floor, engagement is real.
    m3_head_seat_z = z_rail - M3_COUNTERBORE_DEPTH;
    m3_tip_z       = m3_head_seat_z - M3_JOINT_SCREW_L;
    bore_floor_z   = VTV_PLATE_T - bore_depth;
    engagement     = VTV_PLATE_T - m3_tip_z;
    assert(m3_tip_z >= bore_floor_z + 0.5 - MCC_EPS,
        str("mcc: vertical-tv-bracket T1-80 M3 tip z=", m3_tip_z, " must clear bore floor+0.5=", bore_floor_z + 0.5));
    assert(engagement >= 1.5 * MCC_M3_MAJOR_D - MCC_EPS,
        str("mcc: vertical-tv-bracket T1-80 M3 engagement=", engagement, " below 1.5x major diameter=", 1.5 * MCC_M3_MAJOR_D));

    // T1-81 (B12, DB5): the sandwich pad -- clamp thickness and boss wall, no counterbore/washer
    // seat assert exists (there is no counterbore).
    boss_wall = (PAD_D - MCC_M8_CLR_D) / 2;
    assert(VTV_PLATE_T >= 2 * MCC_WALL - MCC_EPS,
        str("mcc: vertical-tv-bracket T1-81 pad clamp thickness VTV_PLATE_T=", VTV_PLATE_T, " below 2xMCC_WALL=", 2 * MCC_WALL));
    assert(boss_wall >= 2 * MCC_WALL - MCC_EPS,
        str("mcc: vertical-tv-bracket T1-81 pad wall=", boss_wall, " below 2xMCC_WALL=", 2 * MCC_WALL));

    // T1-82 (B13): the UP-arrow deboss stays inside the body edge and outside the rail keep-out, by
    // >= KEEPOUT_CLR on both sides.
    arrow_y = (RAIL_KEEPOUT_Y[1] + centre_h / 2) / 2;
    assert(arrow_y - ARROW_W / 2 >= RAIL_KEEPOUT_Y[1] + KEEPOUT_CLR - MCC_EPS,
        str("mcc: vertical-tv-bracket T1-82 UP-arrow bottom edge ", arrow_y - ARROW_W / 2,
            " too close to the rail keep-out (y_max=", RAIL_KEEPOUT_Y[1], ")"));
    assert(arrow_y + ARROW_W / 2 <= centre_h / 2 - KEEPOUT_CLR + MCC_EPS,
        str("mcc: vertical-tv-bracket T1-82 UP-arrow top edge ", arrow_y + ARROW_W / 2,
            " too close to the body edge (centre_h/2=", centre_h / 2, ")"));
    // ... and the arrow stays clear of every joint counterbore (DB2: the joints sit in its band).
    arrow_r = norm([ARROW_W / 2, ARROW_L / 2]); // conservative: the arrow's circumradius
    for (side = [-1, 1], h = _mcc_vert_tv_joint_holes(g)) {
        p = _mcc_vert_tv_xform(h, side, g);
        assert(norm(p - [ARROW_X, arrow_y]) - arrow_r - m3_counterbore_r >= KEEPOUT_CLR - MCC_EPS,
            str("mcc: vertical-tv-bracket T1-82 UP arrow within ",
                norm(p - [ARROW_X, arrow_y]) - arrow_r - m3_counterbore_r, " of the M3 counterbore at ", p));
    }

    // T1-83 (B14, DB13): the case's own lid-top Z fits the user-stated wall gap.
    assert(z_rail + h_max <= wall_gap + MCC_EPS,
        str("mcc: vertical-tv-bracket T1-83 lid-top Z=", z_rail + h_max, " exceeds wall_gap=", wall_gap));

    // T1-84 (B15, DB6): a rib, not a nub -- the run between where it may start and where it must
    // stop is at least two rib-thicknesses.
    assert(rib_end - rib_pad_gap >= 2 * RIB_T - MCC_EPS,
        str("mcc: vertical-tv-bracket T1-84 rib run=", rib_end - rib_pad_gap, " below 2xRIB_T=", 2 * RIB_T));

    // T1-85 (B16, DB5, new): the spacer matches the pad's own clamp height and bearing footprint
    // exactly.
    assert(spacer_t == VTV_PLATE_T,
        str("mcc: vertical-tv-bracket T1-85 spacer thickness ", spacer_t, " != VTV_PLATE_T=", VTV_PLATE_T));
    assert(spacer_d == PAD_D,
        str("mcc: vertical-tv-bracket T1-85 spacer diameter ", spacer_d, " != PAD_D=", PAD_D));
}

// -----------------------------------------------------------------------------------------
// Geometry -- the three exported parts.
// -----------------------------------------------------------------------------------------

// Module: mcc_vert_tv_arm()
// Usage:
//   mcc_vert_tv_arm(g);
// Description:
//   The exported "arm" part (printed TWICE -- top screw and bottom screw): a flat bar from the pad
//   (origin) to the joint lap, with a rounded pad end that IS the flat sandwich clamp face (no
//   raised boss, no counterbore -- R42/DB5/DB7), two top-face edge ribs starting `rib_pad_gap` from
//   the pad and stopping at `rib_end`, and 4 heat-set insert bores in the lap. TV face on the bed
//   (local Z=0).
module mcc_vert_tv_arm(g) {
    arm_len     = struct_val(g, "arm_len");
    rib_pad_gap = struct_val(g, "rib_pad_gap");
    rib_end     = struct_val(g, "rib_end");

    difference() {
        union() {
            // Bar (0 -> arm_len+LAP_L/2, the lap is simply the bar's own tail) + rounded pad end --
            // the pad end IS the flat sandwich clamp face, flush with the rest of the plate.
            cuboid([arm_len + LAP_L / 2, ARM_W, VTV_PLATE_T], anchor = LEFT + BOTTOM);
            cyl(h = VTV_PLATE_T, d = ARM_W, anchor = BOTTOM, $fn = 64, circum = true);
            // Edge ribs, top face, from rib_pad_gap (clear of the TV lift's own rail band) to
            // rib_end (clear of the centre body).
            for (sy = [-1, 1])
                translate([rib_pad_gap, sy * (ARM_W / 2 - RIB_T / 2), VTV_PLATE_T])
                    cuboid([rib_end - rib_pad_gap, RIB_T, RIB_H], anchor = LEFT + BOTTOM);
        }
        // M8 through-hole only -- full plate height, no counterbore (the sandwich pad is flat).
        translate([0, 0, -MCC_EPS])
            cyl(h = VTV_PLATE_T + 2 * MCC_EPS, d = MCC_M8_CLR_D, anchor = BOTTOM, $fn = 64, circum = true);
        // 4 heat-set insert bores in the lap (open face at the arm's own top, VTV_PLATE_T).
        for (h = _mcc_vert_tv_joint_holes(g))
            translate([h[0], h[1], VTV_PLATE_T])
                mcc_heat_set_bore(MCC_INSERT_M3);
    }
}

// Module: mcc_vert_tv_centre()
// Usage:
//   mcc_vert_tv_centre(g);
// Description:
//   The exported "centre" part: a flat body carrying two angled tabs (the arms' own lap footprint)
//   and the male mount rail on top, with 4 M3 counterbored clearance holes per tab and a cosmetic
//   "UP" arrow deboss. Bottom (TV-facing, standing VTV_PLATE_T off the TV) face on the bed
//   (local Z=0).
module mcc_vert_tv_centre(g) {
    centre_h = struct_val(g, "centre_h");
    z_rail   = struct_val(g, "z_rail");
    m3_counterbore_d = M3_HEAD_D + 2 * MCC_CLR_SLIDE;
    arrow_y = (RAIL_KEEPOUT_Y[1] + centre_h / 2) / 2;

    // The rail is unioned after the plate's own cuts; it needs no cut of its own in the plate (D50).
    union() {
    difference() {
        union() {
            cuboid([2 * CENTRE_HALF_L, centre_h, VTV_PLATE_T], anchor = BOTTOM);
            // Two tabs = the arm laps' own footprint, same transform as the arms themselves.
            for (side = [-1, 1])
                _mcc_vert_tv_place(g, side)
                    translate([struct_val(g, "arm_len"), 0, 0])
                        cuboid([LAP_L, ARM_W, VTV_PLATE_T], anchor = BOTTOM);
        }
        // 4 M3 counterbored clearance holes per tab, same placement transform as the tabs above.
        for (side = [-1, 1], h = _mcc_vert_tv_joint_holes(g)) {
            p = _mcc_vert_tv_xform(h, side, g);
            translate([p[0], p[1], -MCC_EPS])
                cyl(h = VTV_PLATE_T + 2 * MCC_EPS, d = MCC_M3_CLR_D, anchor = BOTTOM, $fn = 64, circum = true);
            translate([p[0], p[1], z_rail + MCC_EPS])
                cyl(h = M3_COUNTERBORE_DEPTH + MCC_EPS, d = m3_counterbore_d, anchor = TOP, $fn = 64, circum = true);
        }
        // Cosmetic "UP" arrow deboss, top face, pointing +Y -- outside the rail keep-out and below
        // the body edge (T1-82), never in contact with the mated case (it sits below z_rail).
        translate([ARROW_X, arrow_y, z_rail - ARROW_DEPTH])
            linear_extrude(height = ARROW_DEPTH + MCC_EPS)
                polygon([[-ARROW_W / 2, -ARROW_L / 2], [ARROW_W / 2, -ARROW_L / 2], [0, ARROW_L / 2]]);
    }
    // Rail -- centred on this plate, no X shift: the male rail's footprint (mcc_rail_male_keepout())
    // is symmetric in X about its own centre (no end-stop flange since D34).
    translate([0, 0, VTV_PLATE_T]) rotate([0, 0, 180]) mcc_rail_male();
    }
}

// Module: mcc_vert_tv_spacer()
// Usage:
//   mcc_vert_tv_spacer(g);
// Description:
//   The exported "spacer" part (printed TWICE -- the lift's other, unoccupied column): a flat disc,
//   diameter `spacer_d`, thickness `spacer_t` -- drawn from `g` (fit-check FX3) rather than the pad's
//   own constants directly, so T1-85 actually checks what gets printed, not a tautology. In practice
//   spacer_d == PAD_D and spacer_t == VTV_PLATE_T (R42/DB5) -- one centred M8 through-hole, no other
//   features.
module mcc_vert_tv_spacer(g) {
    spacer_d = struct_val(g, "spacer_d");
    spacer_t = struct_val(g, "spacer_t");
    difference() {
        cyl(h = spacer_t, d = spacer_d, anchor = BOTTOM, $fn = 64, circum = true);
        translate([0, 0, -MCC_EPS])
            cyl(h = spacer_t + 2 * MCC_EPS, d = MCC_M8_CLR_D, anchor = BOTTOM, $fn = 64, circum = true);
    }
}

// -----------------------------------------------------------------------------------------
// Top-level: geometry derivation + Tier-1 asserts, run on EVERY render (part dispatch below).
// -----------------------------------------------------------------------------------------

G = mcc_vert_tv_geom(tv_side_clear = TV_SIDE_CLEAR, w_lift_rail = W_LIFT_RAIL, wall_gap = WALL_GAP);
mcc_vert_tv_assert(G);

echo(str("vertical-tv-bracket: reach=", struct_val(G, "reach"), " alpha=", struct_val(G, "alpha"),
    " arm_len=", struct_val(G, "arm_len"), " yj_v=", struct_val(G, "yj_v"),
    " centre_h=", struct_val(G, "centre_h"), " arm_bbox=", struct_val(G, "arm_bbox"),
    " centre_bbox=", struct_val(G, "centre_bbox"),
    " tv_side_clear=", struct_val(G, "tv_side_clear"), " (user-confirmed non-binding, kept as an assert)",
    " w_lift_rail=", struct_val(G, "w_lift_rail"), " (assumed, M20)",
    " wall_gap=", struct_val(G, "wall_gap"), " (user-stated, conservative bound, M20 for the exact lift standoff)"));

// -----------------------------------------------------------------------------------------
// Part dispatch + previews (non-exported, invisible to build.py -- discover_brackets() only ever
// asks for the "arm"/"centre"/"spacer" parts named by this file's own header parts marker, above).
// -----------------------------------------------------------------------------------------

if (part == "arm") {
    mcc_vert_tv_arm(G);

} else if (part == "centre") {
    mcc_vert_tv_centre(G);

} else if (part == "spacer") {
    mcc_vert_tv_spacer(G);

} else if (part == "assembly" || part == "assembly_sweep") {
    reach  = struct_val(G, "reach");
    z_rail = struct_val(G, "z_rail");
    l_max  = struct_val(G, "l_max");

    // Both arms, TV face on Z=0 (the assembly frame's own TV back plane).
    for (side = [-1, 1])
        color("Silver") _mcc_vert_tv_place_assembly(G, side) mcc_vert_tv_arm(G);

    // Centre, stacked on the arms' laps.
    translate([reach, 0, VTV_PLATE_T])
        color("LightSteelBlue") mcc_vert_tv_centre(G);

    // Translucent ghost TV-back slab + a thin red line at TV_SIDE_CLEAR on the reach axis --
    // verify-by-picture: confirm the case's mated footprint stays clear of it (R-4/closed, kept as a
    // permanent visual sanity check).
    %translate([0, -HALF_PITCH_V - 50, -3]) cuboid([TV_SIDE_CLEAR + 100, 2 * HALF_PITCH_V + 100, 3], anchor = BOTTOM);
    color("Red") translate([TV_SIDE_CLEAR, 0, 0]) cuboid([1, 2 * HALF_PITCH_V + 100, 1]);

    // Ghost case, mated onto the rail -- the Plus-family SKU that ships the fan (CLAUDE.md fixed
    // decision). "assembly_sweep" shifts it by slide_clear to show the +X slide-on approach; the
    // slide axis here is the rail's own local X, i.e. the SAME global +X the case already sits on.
    dev = MCC_DEV_PRO_CONVERT_HDMI_PLUS;
    variant = [["fan", true], ["splitter", false], ["fan_switch", true], ["tripod_insert", false], ["lid_vents", true]];
    slide_clear = MCC_RAIL_LEN / 2 + l_max / 2;
    x_shift = (part == "assembly_sweep") ? slide_clear : 0;

    translate([reach + x_shift, MCC_RAIL_Y, z_rail]) rotate([0, 0, 180]) { // flush, no pedestal (D44)
        color("SlateGray") mcc_shell_base(dev = dev, cfg = variant);
        color("LightSteelBlue", 0.6) mcc_shell_lid(dev = dev, cfg = variant);
    }

} else {
    assert(false, str("mcc: unknown part \"", part, "\""));
}

// vim: expandtab tabstop=4 shiftwidth=4 softtabstop=4 nowrap
