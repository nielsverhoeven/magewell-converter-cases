//////////////////////////////////////////////////////////////////////
// models/brackets/arch-tv-bracket.scad
//   L4-equivalent assembly (architecture.md §3 rev 9/13, layout-patch-wall.md §17.2). Issue #47,
//   implemented per docs/plans/2026-09-27-arch-tv-bracket.md §0-§8/§10, as amended by the architect
//   verdict's binding changes B1-B11 (§12.2) and the PLAN-ASSUMPTION rulings (§12.5). Sibling of
//   the retired tv-bracket.scad (#26, D47); consumes lib/mcc/rail.scad's mount-rail interface (#25)
//   only through mcc_rail_male() and mcc_rail_male_keepout() (D50). The rail-interface defect F1 this
//   file inherited (§12.3, issue #48) was fixed in the library -- D34 opened the groove and retired the
//   male's end-stop flange, D48 replaced the latch with a gravity lock, D63.1 moved it on top of the rail. Every rail-dependent value
//   here (keep-out rectangle, Z stack, slide_clear) derives from MCC_RAIL_* or mcc_rail_male_keepout(),
//   so a rail change is absorbed by a re-golden or stopped by an assert, not by a code edit here.
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
//       (assembly (0, 0, ARCH_PLATE_T)); bottom face (TV-facing, but 11 mm standing off the TV --
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
//   B1 (blocking, §12.2, 2026-09-27): the plan's A8 assert (M3 counterbore vs. the rail keep-out
//   rectangle) failed on the -X lap, where the male rail then carried an end-stop flange; B1 shifted
//   the rail by RAIL_X = MCC_RAIL_END_STOP_L / 2 to centre that asymmetric footprint. D34 retired the
//   flange (RAIL_X became 0) and D52 removed RAIL_X: the rail sits at the centre plate's origin, as in
//   vertical-tv-bracket.scad. A8 lives on as T1-54, which checks every M3 counterbore on BOTH laps
//   against the keep-out rectangle on every render.
//
//   Assert ids: T1-47 ... T1-60 (architect-assigned per B4; the highest T1 id before this file was
//   T1-46; T1-49 and T1-50 are retired, never reused) plus T1-120.1 (arm axis on the top VESA row).
//   Risk/measurement ids (R30-R38, M18a-d, D26) are recorded by the architect in
//   .claude/knowledge/architecture.md after merge (§12.5 bottom) -- this file cites the PROPOSED
//   ids in comments only. Sandwich mode (issue #56, D51) adds T1-86 ... T1-90 on top -- T1-47 ...
//   T1-60 hold in BOTH modes (D-vesa-400x300-bracket.VERDICT-rev2.md, "Ids for rev 18").
//
//   PRINT GATE (B10; same gate as models/brackets/README.md): do not print this bracket FOR USE
//   before M15 (the rail-lock coupon, models/coupons/rail-lock.scad), M18/M20 (the TV / TV-lift
//   measurements) and M22 (the sandwich tilt/preload check, sandwich parts only) are closed. The
//   Geometry does not depend on TV_TOP_CLEAR; it only feeds the T1-48 validity assert.
//
//   SANDWICH MODE (issue #56, plan D rev 2, D51 -- architect verdict D-vesa-400x300-bracket.
//   VERDICT-rev2.md, DB8-DB12): a TV whose own mount (a TV lift) already uses all four VESA holes
//   needs this bracket clamped between the TV and the lift on longer M8 bolts instead of a direct
//   mount. Sandwich mode ships as its OWN exported parts -- `arm_sandwich`, `centre_sandwich` and
//   `spacer` -- beside the unchanged `arm`/`centre` direct-mode parts (the `base_fan` precedent,
//   DB8): the exported part name fixes the mode, never a `-D MOUNT_MODE=...` switch alone (that
//   survives only as the "assembly"/"assembly_sweep" preview selector).
//   - The arm's own M8 pad becomes a FLAT clamp face (no counterbore, no washer seat -- R42) at
//     Z=ARCH_PLATE_T, the same flush philosophy as `vertical-tv-bracket.scad`'s own pad (DB7); its
//     ribs start at `rib_pad_gap` instead of the pad centre, so they clear the TV lift's own rail
//     band along the crossed column (T1-89, DB10).
//   - The centre plate grows to `centre_t` (>= T_LIFT_RAIL + K_BOLT_HEAD + ARCH_SWEEP_CLR, both
//     `assumed`, M20) so the +X slide-on sweep -- which crosses the right-hand column in sandwich
//     mode, unlike direct mode -- clears the lift's own rail and bolt head in Z (T1-87, R43). The M3
//     lap screw lengthens to M3x18 inside the SAME tip/engagement window T1-57 already checks, never
//     by rounding a raw number up (DB11).
//   - `mcc_arch_tv_spacer()`: a flat ARCH_PLATE_T-thick, ARM_W-wide disc for the bracket's OWN unused
//     (bottom) row, matching the arm's sandwich pad exactly (T1-90, DB9) -- never `centre_t` or a
//     boss diameter.
//
// build.py: parts = arm, centre, arm_sandwich, centre_sandwich, spacer
// build.py: print_count = arm:2, arm_sandwich:2, spacer:2
//   (left + right arm (either mode): arm.3mf/arm_sandwich.3mf and the review project carry both
//   copies; two spacers for the bracket's own unused row in sandwich mode.)
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

// MOUNT_MODE survives ONLY as the "assembly"/"assembly_sweep" preview selector (DB8) -- every real
// exported part (arm/centre/arm_sandwich/centre_sandwich/spacer) fixes its own mode explicitly in
// the part dispatch below, never by reading this variable. Override for previewing sandwich mode:
// `-D part="assembly_sweep" -D MOUNT_MODE=\"sandwich\"`.
MOUNT_MODE = "direct"; // "direct" (default, unchanged) | "sandwich" (new, issue #56).

// -----------------------------------------------------------------------------------------
// §1.2 Parameters (plan-fixed geometry, THIS bracket's own authored dimensions -- bracket-own
// geometry stays out of constants.scad, the models/brackets convention; nothing here is
// cross-cutting library policy).
// -----------------------------------------------------------------------------------------

VESA_TOP_PITCH = 400; // mm. User decision 2026-09-27 (#47); VESA MIS-F 400x400 is a standard
                       // pattern (https://en.wikipedia.org/wiki/VESA_mount).
HALF_PITCH = VESA_TOP_PITCH / 2; // = 200. derived.

TV_TOP_CLEAR = 150; // mm. `unknown` -> placeholder, assumed (M18a). Distance from the top-screw
                     // centreline up to the TV's top outer edge; validity input only, must be
                     // >= case_top_above_rail + TV_TOP_MARGIN (69.675 at current constants).
TV_TOP_MARGIN = 10.0; // mm. assumed -- case top stays this far below the TV top edge (bezel,
                       // measurement error, sight line over the edge).

WALL_GAP = 150.0; // mm. Sandwich mode only (issue #56, DB13) -- shares its name/value with
                   // vertical-tv-bracket.scad's own WALL_GAP: user-stated 2026-09-28 ("150-200 mm
                   // behind the TV" on a TV-lift mount), 150 the conservative end, asserted against
                   // this bracket's own sandwich lid-top Z (T1-88). M20 updates both files together.

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
CENTRE_W = 92.0; // mm. D44: holds the rail keep-out Y span (T1-53) and the UP arrow above it
                  // (T1-60). Sized for the D34 latch's [-32.5, +36.1]; since D63.1 the keep-out
                  // (mcc_rail_male_keepout()) is [-32.5, +32.5], so T1-60 needs only
                  // 2 x (32.5 + 1 + 6 + 1) = 81.0 and 92 leaves 2.75 mm on both of its bounds.
                  // Kept at 92 so neither D48 nor D63.1 moves a bracket outline. Was 40 for the 14.6 mm rail.
C_HALF = 90.0; // mm. assumed -- centre-body half-length. The rail keep-out's X half-length is
               // MCC_RAIL_LEN/2 = 68 (no end-stop flange since D34), leaving a 22 mm end web
               // (>= MCC_WALL, asserted T1-53).
XJ = 95.0; // mm. assumed -- |x| of each lap centre in the assembly frame (plan §3.2 numeric sweep).
LAP_L = 30.0; // mm. assumed -- lap length along the arm axis.
JOINT_S = 14.0; // mm. assumed -- joint hole pitch along the arm axis (2x2 pattern).
JOINT_P = 20.0; // mm. assumed -- joint hole pitch across the arm axis.
LAP_RIB_GAP = 3.0; // mm. arm ribs stop this far short of the lap; spaces the rib end from the
                    // centre tab.
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

// Sandwich mode only (issue #56, DB11/DB13). W_LIFT_RAIL/T_LIFT_RAIL/K_BOLT_HEAD share their names
// and placeholder values with vertical-tv-bracket.scad's own M20 parameters -- M20 updates both
// files together.
W_LIFT_RAIL = 60.0; // mm. assumed, M20 -- the TV lift's own rail/plate width at the crossed column.
                     // Feeds arm_sandwich's own rib_pad_gap (T1-89, DB10).
T_LIFT_RAIL = 5.0; // mm. assumed, M20 -- the TV lift's own rail/plate thickness at the crossed column.
K_BOLT_HEAD = M8_HEAD_K + M8_WASHER_H; // = 9.6. ISO 4762/7089 nominal stack -- reused from the arm's
                  // own M8 constants above, not itself a fresh guess even though the specific bolt is
                  // still to be chosen (M20).
// M3_JOINT_SCREW_L_SANDWICH (DB11): chosen INSIDE T1-57's own tip/engagement window, never by
// rounding a raw computed value up (that can bottom the screw out in the insert bore). At the
// placeholders above the window is [16.8, 18.5] (re-derived, T1-57); 18 sits inside it with margin.
M3_JOINT_SCREW_L_SANDWICH = 18; // mm. derived stock length, sandwich mode (T1-57, both modes).

ARROW_DEPTH = 0.6; // mm. assumed, cosmetic "UP" deboss (§3.5).
ARROW_L = 8.0; // mm. assumed (B3 -- the plan's original arrow had no defined size).
ARROW_W = 6.0; // mm. assumed (B3).

// Rail keep-out rectangle, centre-local frame (the rail sits at the plate origin): the rail's own
// plate-side keep-out (mcc_rail_male_keepout(), rail-local) mapped through this file's
// rotate([0,0,180]) rail placement, which negates and swaps both ranges (symmetric in Y since D63.1:
// the lock strips sit on the rail's top). D50 / F-R1: never built from MCC_RAIL_* internals.
_RAIL_KO = mcc_rail_male_keepout(MCC_RAIL_LEN);
RAIL_KEEPOUT_X = [-_RAIL_KO[0][1], -_RAIL_KO[0][0]];
RAIL_KEEPOUT_Y = [-_RAIL_KO[1][1], -_RAIL_KO[1][0]];

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
//   Private, pure. [L_max, W_max, H_max] over every _ARCH_TV_DEVS record under a
//   fan/splitter/switch-off config (researcher check, plan §1.4: neither flag changes L/W/H on any
//   current SKU -- they come only from device geometry + end zones + wall thickness, never from
//   cfg, see lib/mcc/layout.scad's own mcc_case_layout()). N3: cheap on purpose -- 8 x
//   mcc_case_layout() calls, fine for a smoke test's 3 values; do not extend this into a larger
//   sweep. H_max is new (issue #56, DB12/T1-88's lid-vs-WALL_GAP check); existing L_max/W_max
//   callers (env[0]/env[1]) are unaffected by the added index.
function _mcc_arch_tv_envelope_max() =
    let(dims = [for (dev = _ARCH_TV_DEVS) mcc_case_dims(dev, _ARCH_TV_ENV_CFG)])
    [max([for (d = dims) d[0]]), max([for (d = dims) d[1]]), max([for (d = dims) d[2]])];

// -----------------------------------------------------------------------------------------
// §1.4/§1.5: pure geometry function. Every asserted/echoed/drawn number derives from this ONE
// function (a BOSL2 struct, struct_val()-accessible) -- see mcc_arch_tv_assert() and the two
// exported-part modules below.
// -----------------------------------------------------------------------------------------

// Function: mcc_arch_tv_geom()
// Usage:
//   g = mcc_arch_tv_geom([tv_top_clear=], [mount_mode=]);
// Description:
//   Pure. Derives the whole bracket's geometry from `tv_top_clear` (default TV_TOP_CLEAR) --
//   §1.4/§1.5's algebra, re-derived independently by the architect (§12.1) and matching at the
//   placeholder. See this file's header for the Z-stack table. `mount_mode` ("direct"/"sandwich",
//   issue #56, DB8) affects only `centre_t`/`z_rail`/`pad_clamp_t`/`m3_joint_screw_l`/`rib_pad_gap` --
//   in "direct" mode every one of those reduces to exactly its pre-#56 value, so direct-mode callers
//   see byte-identical numbers.
function mcc_arch_tv_geom(tv_top_clear = TV_TOP_CLEAR, mount_mode = "direct") =
    let(
        env    = _mcc_arch_tv_envelope_max(),
        l_max  = env[0], w_max = env[1], h_max = env[2],

        // CASE_TOP_ABOVE_RAIL = W_max/2 + MCC_RAIL_Y (MCC_RAIL_Y is negative -- the rail sits under
        // the device, not free-standing -- constants.scad's own R2 comment).
        case_top_above_rail = w_max / 2 + MCC_RAIL_Y,
        case_bottom_below_rail = w_max / 2 - MCC_RAIL_Y,

        // The arms lie along the top VESA row: the arm axis is the row itself.
        arm_len = HALF_PITCH - XJ,

        // Sandwich mode (issue #56, DB8/DB12 §7.1-§7.2): the +X sweep crosses the right-hand column,
        // so the centre must rise enough to clear the TV lift's own rail + bolt head there. Direct
        // mode's centre_t reduces to exactly ARCH_PLATE_T (unchanged).
        centre_t = (mount_mode == "direct") ? ARCH_PLATE_T : (T_LIFT_RAIL + K_BOLT_HEAD + ARCH_SWEEP_CLR),
        z_rail   = ARCH_PLATE_T + centre_t, // = 2*ARCH_PLATE_T in direct mode (unchanged formula value)
        arm_top_z  = ARCH_PLATE_T + RIB_H,

        // §3.4: M8 pad clamp thickness -- the number the installer needs for screw length (BOM).
        // Sandwich mode has no counterbore (R42/DB5/DB7): the pad is flat at ARCH_PLATE_T.
        m8_counterbore_depth = M8_WASHER_H + M8_HEAD_K + 0.4,
        pad_clamp_t = (mount_mode == "direct") ? (arm_top_z - m8_counterbore_depth) : ARCH_PLATE_T,

        // DB11: the sandwich M3 lap screw, chosen inside T1-57's own window (never a rounded-up raw
        // number); direct mode is unchanged.
        m3_joint_screw_l = (mount_mode == "direct") ? M3_JOINT_SCREW_L : M3_JOINT_SCREW_L_SANDWICH,

        // DB10: where arm_sandwich's own ribs may start (arm-local x), clear of the TV lift's rail
        // band along the crossed column -- same derivation as vertical-tv-bracket.scad's own
        // RIB_PAD_GAP (DB2). Computed unconditionally (cheap); only consumed when
        // mount_mode=="sandwich" (direct mode's ribs still start at the pad, DB10).
        rib_pad_gap = W_LIFT_RAIL / 2 + ARCH_KEEPOUT_CLR,

        // B6: the case can only engage once its leading (+X) end wall passes the rail's own open
        // (+X, per this file's rotate([0,0,180]) rail placement) end, at case centre
        // x = MCC_RAIL_LEN/2 + L/2 -- not "+MCC_RAIL_LEN" as the plan's own §1.3 originally had it.
        // Derived from MCC_RAIL_*, so a rail-length change is absorbed automatically.
        slide_clear = MCC_RAIL_LEN / 2 + l_max / 2,

        // Arm print bbox (§1.5): pad disc (|x|<=ARM_W/2 at x=0) unioned with the bar
        // (x in [0, arm_len+LAP_L/2]); Y = ARM_W; Z = arm_top_z (ribs/pad boss both reach it).
        arm_bbox = [arm_len + LAP_L / 2 + ARM_W / 2, ARM_W, arm_top_z],

        // Centre print bbox (§1.5): body [-C_HALF,C_HALF] x [-CENTRE_W/2,CENTRE_W/2], unioned with
        // both tabs -- each tab is the arm's own lap rectangle, a straight bar of width ARM_W
        // centred on the arm axis at |x| in [XJ - LAP_L/2, XJ + LAP_L/2].
        centre_x_max = max(C_HALF, XJ + LAP_L / 2),
        centre_y_max = max(CENTRE_W / 2, ARM_W / 2),
        centre_y_min = -max(CENTRE_W / 2, ARM_W / 2),
        centre_z_max = centre_t + MCC_RAIL_MALE_H, // = 14.5 in direct mode (the male rises
            // MCC_RAIL_MALE_H above its own foot at Z_RAIL -- D44); taller in sandwich mode since
            // centre_t is (DB8: "every formula that assumed the centre is ARCH_PLATE_T thick reads
            // centre_t instead").
        centre_bbox = [2 * centre_x_max, centre_y_max - centre_y_min, centre_z_max]
    )
    [
        ["mount_mode", mount_mode],
        ["tv_top_clear", tv_top_clear],
        ["arm_len", arm_len],
        ["centre_t", centre_t],
        ["z_rail", z_rail],
        ["arm_top_z", arm_top_z],
        ["case_top_above_rail", case_top_above_rail],
        ["case_bottom_below_rail", case_bottom_below_rail],
        ["l_max", l_max],
        ["w_max", w_max],
        ["h_max", h_max],
        ["pad_clamp_t", pad_clamp_t],
        ["m3_joint_screw_l", m3_joint_screw_l],
        ["rib_pad_gap", rib_pad_gap],
        // Fit-check FX2: the spacer's own clamp height/footprint, drawn straight from the constants
        // DB9 names (ARCH_PLATE_T / ARM_W) -- mode-independent, but carried in the struct so
        // mcc_arch_tv_spacer(g) and T1-90 both read the SAME source, never a hand-typed duplicate.
        ["spacer_t", ARCH_PLATE_T],
        ["spacer_d", ARM_W],
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
//   Private, pure. The in-plane rotation (degrees) that carries an arm-local point to the
//   assembly/centre frame (the same frame) for the given `side` (+1 = right, -1 = left): the right
//   arm is the left one turned 180 degrees.
function _mcc_arch_tv_theta(side) =
    side > 0 ? 180 : 0;

// Function: _mcc_arch_tv_rotate2()
// Description:
//   Private, pure. 2D rotation of point `p` by `theta` degrees about the origin.
function _mcc_arch_tv_rotate2(p, theta) =
    [p[0] * cos(theta) - p[1] * sin(theta), p[0] * sin(theta) + p[1] * cos(theta)];

// Function: _mcc_arch_tv_xform()
// Description:
//   Private, pure. Arm-local point `p` -> assembly/centre-frame [x,y] (same frame), for `side` in
//   {-1,+1}. Used by both the assert module (A8/T1-54, A9/T1-55) and, as the geometric mirror of
//   module _mcc_arch_tv_place() below, to build the tab/hole geometry -- the SAME rotate+translate
//   applied twice (once as an OpenSCAD transform stack for geometry, once as plain arithmetic for
//   the asserts), not two independently-derived formulas.
function _mcc_arch_tv_xform(p, side) =
    [side * HALF_PITCH, 0] + _mcc_arch_tv_rotate2(p, _mcc_arch_tv_theta(side));

// Module: _mcc_arch_tv_place()
// Description:
//   Private. Places `children()` (authored in the ARM's own local frame) into the assembly/centre
//   frame (the same frame), for the given `side`. Geometric mirror of _mcc_arch_tv_xform() above.
module _mcc_arch_tv_place(side) {
    translate([side * HALF_PITCH, 0, 0])
        rotate([0, 0, _mcc_arch_tv_theta(side)])
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
// §5: Tier-1 asserts (architecture.md §9). A1-A13 -> T1-47...T1-59 (B4), plus B3's T1-60, plus
// T1-86...T1-90 (issue #56, D51) -- all hold in BOTH modes, checked via mcc_arch_tv_assert(G) and
// mcc_arch_tv_assert(G_SANDWICH) below. Kept in a
// PUBLIC module (not bare top-level statements) so tests/test_arch_tv_bracket.scad can exercise them
// for other TV_TOP_CLEAR values via `use` (which skips bare top-level asserts) -- PLAN-ASSUMPTION-5.
// Called at top level below so every render fires it.
// -----------------------------------------------------------------------------------------

// Module: mcc_arch_tv_assert()
// Usage:
//   mcc_arch_tv_assert(g);
module mcc_arch_tv_assert(g) {
    mode                = struct_val(g, "mount_mode");
    tv_top_clear        = struct_val(g, "tv_top_clear");
    arm_len            = struct_val(g, "arm_len");
    centre_t            = struct_val(g, "centre_t");
    z_rail              = struct_val(g, "z_rail");
    arm_top_z           = struct_val(g, "arm_top_z");
    case_top_above_rail = struct_val(g, "case_top_above_rail");
    l_max               = struct_val(g, "l_max");
    h_max               = struct_val(g, "h_max");
    pad_clamp_t         = struct_val(g, "pad_clamp_t");
    m3_joint_screw_l    = struct_val(g, "m3_joint_screw_l");
    rib_pad_gap         = struct_val(g, "rib_pad_gap");
    arm_bbox            = struct_val(g, "arm_bbox");
    centre_bbox         = struct_val(g, "centre_bbox");
    centre_y_max        = struct_val(g, "centre_y_max");

    // T1-86 (DB12, new): the mode value itself is one of the two known strings.
    assert(mode == "direct" || mode == "sandwich",
        str("mcc: arch-tv-bracket T1-86 mount_mode=\"", mode, "\" must be \"direct\" or \"sandwich\""));

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

    // T1-48 (A2): the case stays fully behind the TV -- the case top and the centre's own top edge
    // both stay TV_TOP_MARGIN below the TV's top edge. (T1-49 and T1-50 are retired.)
    assert(case_top_above_rail + TV_TOP_MARGIN <= tv_top_clear + MCC_EPS,
        str("mcc: arch-tv-bracket T1-48 TV too short above the screws: needs TV_TOP_CLEAR >= ",
            case_top_above_rail + TV_TOP_MARGIN, " (tv_top_clear=", tv_top_clear, ")"));
    assert(centre_y_max <= tv_top_clear - TV_TOP_MARGIN + MCC_EPS,
        str("mcc: arch-tv-bracket T1-48 centre top edge ", centre_y_max,
            " exceeds tv_top_clear-TV_TOP_MARGIN=", tv_top_clear - TV_TOP_MARGIN));

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

    // T1-53 (A7): the rail sits entirely on the centre body -- its keep-out (mcc_rail_male_keepout(),
    // D50) plus an MCC_WALL end web inside +/-C_HALF, and its keep-out Y span inside +/-CENTRE_W/2.
    assert(RAIL_KEEPOUT_X[0] - MCC_WALL >= -C_HALF - MCC_EPS && RAIL_KEEPOUT_X[1] + MCC_WALL <= C_HALF + MCC_EPS,
        str("mcc: arch-tv-bracket T1-53 rail keep-out X span ", RAIL_KEEPOUT_X, " + MCC_WALL=", MCC_WALL,
            " exceeds +/-C_HALF=", C_HALF));
    assert(RAIL_KEEPOUT_Y[1] <= CENTRE_W / 2 + MCC_EPS && RAIL_KEEPOUT_Y[0] >= -CENTRE_W / 2 - MCC_EPS,
        str("mcc: arch-tv-bracket T1-53 rail keep-out Y span ", RAIL_KEEPOUT_Y,
            " exceeds +/-CENTRE_W/2=", CENTRE_W / 2));

    // T1-54 (A8, B1 fix): every M3 counterbore, both laps, clears the rail keep-out rectangle by
    // >= ARCH_KEEPOUT_CLR. Circle-rect distance, not an x-only check (the plan's own original table
    // under-checked this).
    m3_counterbore_r = (M3_HEAD_D + 2 * MCC_CLR_SLIDE) / 2;
    for (side = [-1, 1], h = _mcc_arch_tv_joint_holes(g)) {
        p   = _mcc_arch_tv_xform(h, side);
        gap = _mcc_arch_tv_circle_rect_gap(p, m3_counterbore_r, RAIL_KEEPOUT_X, RAIL_KEEPOUT_Y);
        assert(gap >= ARCH_KEEPOUT_CLR - MCC_EPS,
            str("mcc: arch-tv-bracket T1-54 M3 counterbore at ", p, " (side=", side,
                ") clears the rail keep-out by ", gap, ", below ARCH_KEEPOUT_CLR=", ARCH_KEEPOUT_CLR));
    }

    // T1-55 (A9, B2 fix; DB10 generalises the start for arm_sandwich): sample every rib EDGE (not
    // just its end corners) from `rib_start` (0 in direct mode -- unchanged, the ribs still start at
    // the pad; rib_pad_gap in sandwich mode, clear of the TV lift's own rail band) down to the rib
    // end, in <= 1 mm steps, both edges of both ribs, both sides -- a corner can lie outside the
    // centre body rectangle via Y while the edge re-enters it further along.
    rib_start  = (mode == "direct") ? 0 : rib_pad_gap;
    rib_end    = arm_len - LAP_L / 2 - LAP_RIB_GAP;
    n_samples  = max(2, ceil((rib_end - rib_start) / 1.0) + 1);
    for (side = [-1, 1], sy = [-1, 1], edge = [0, 1], i = [0:n_samples - 1]) {
        x      = rib_start + (rib_end - rib_start) * i / (n_samples - 1);
        y_line = sy * (edge == 0 ? ARM_W / 2 : ARM_W / 2 - RIB_T);
        p      = _mcc_arch_tv_xform([x, y_line], side);
        gap    = _mcc_arch_tv_circle_rect_gap(p, 0, [-C_HALF, C_HALF], [-CENTRE_W / 2, CENTRE_W / 2]);
        assert(gap >= ARCH_KEEPOUT_CLR - MCC_EPS,
            str("mcc: arch-tv-bracket T1-55 rib edge sample at ", p, " (side=", side,
                ") clears the centre body by ", gap, ", below ARCH_KEEPOUT_CLR=", ARCH_KEEPOUT_CLR));

        // T1-89 (DB10, new): arm_sandwich only -- the same rib edge sample must also clear the TV
        // lift's own rail band along the crossed column. The centre's frame origin is the assembly
        // origin in X/Y, so _mcc_arch_tv_xform's own X component (p[0]) already equals assembly-frame
        // X directly. The column sits at assembly X=side*HALF_PITCH.
        if (mode == "sandwich") {
            col_dist = abs(p[0] - side * HALF_PITCH);
            assert(col_dist >= W_LIFT_RAIL / 2 + ARCH_KEEPOUT_CLR - MCC_EPS,
                str("mcc: arch-tv-bracket T1-89 arm_sandwich rib edge sample at assembly X=", p[0],
                    " (side=", side, ") clears the TV lift's rail band by ",
                    col_dist - W_LIFT_RAIL / 2, ", below ARCH_KEEPOUT_CLR=", ARCH_KEEPOUT_CLR));
        }
    }

    // T1-120.1: the bracket is straight -- each arm's pad sits on its top VESA screw and its lap on
    // the centre's axis, so the arm axis lies along the top VESA row (y = 0).
    for (side = [-1, 1]) {
        pad = _mcc_arch_tv_xform([0, 0], side);
        lap = _mcc_arch_tv_xform([arm_len, 0], side);
        assert(norm(pad - [side * HALF_PITCH, 0]) <= MCC_EPS && norm(lap - [side * XJ, 0]) <= MCC_EPS,
            str("mcc: arch-tv-bracket T1-120.1 arm axis not along the top VESA row: pad=", pad, " lap=", lap));
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

    // T1-57 (A11; DB11 generalises the length and the seat/floor to both modes): the M3 screw stack
    // (§3.3) -- tip clears the bore floor, and engagement is real. z_rail/m3_joint_screw_l are
    // already mode-aware (struct fields), so direct mode reproduces exactly the pre-#56 numbers.
    m3_counterbore_depth = M3_COUNTERBORE_DEPTH;
    m3_head_seat_z = z_rail - m3_counterbore_depth;
    m3_tip_z       = m3_head_seat_z - m3_joint_screw_l;
    bore_floor_z   = ARCH_PLATE_T - bore_depth;
    engagement     = ARCH_PLATE_T - m3_tip_z;
    assert(m3_tip_z >= bore_floor_z + 0.5 - MCC_EPS,
        str("mcc: arch-tv-bracket T1-57 M3 tip z=", m3_tip_z, " must clear bore floor+0.5=", bore_floor_z + 0.5));
    assert(engagement >= 1.5 * MCC_M3_MAJOR_D - MCC_EPS,
        str("mcc: arch-tv-bracket T1-57 M3 engagement=", engagement,
            " below 1.5x major diameter=", 1.5 * MCC_M3_MAJOR_D));

    // T1-58 (A12; DB10 generalises the pad diameter/hole to sandwich mode): M8 pad -- clamp
    // thickness and pad wall (§3.4). Direct mode: the raised, counterbored PAD_BOSS_D boss, same
    // numbers as before #56. Sandwich mode: the flat ARM_W-wide pad end, plain M8 clearance hole, no
    // counterbore.
    m8_counterbore_d = M8_WASHER_D + 2 * MCC_CLR_SLIDE;
    pad_d  = (mode == "direct") ? PAD_BOSS_D : ARM_W;
    hole_d = (mode == "direct") ? m8_counterbore_d : MCC_M8_CLR_D;
    boss_wall = (pad_d - hole_d) / 2;
    assert(pad_clamp_t >= 2 * MCC_WALL - MCC_EPS,
        str("mcc: arch-tv-bracket T1-58 pad_clamp_t=", pad_clamp_t, " below 2xMCC_WALL=", 2 * MCC_WALL));
    assert(boss_wall >= 2 * MCC_WALL - MCC_EPS,
        str("mcc: arch-tv-bracket T1-58 pad wall=", boss_wall, " below 2xMCC_WALL=", 2 * MCC_WALL));

    // T1-87 (DB12, new): sandwich mode's own sweep-clearance formula (§7.1) -- trivially true by
    // construction (centre_t's own formula guarantees it), stated explicitly so a future edit to any
    // of the four inputs fails loudly instead of silently.
    assert(mode == "direct" || z_rail >= ARCH_PLATE_T + T_LIFT_RAIL + K_BOLT_HEAD + ARCH_SWEEP_CLR - MCC_EPS,
        str("mcc: arch-tv-bracket T1-87 sandwich z_rail=", z_rail, " below ARCH_PLATE_T+T_LIFT_RAIL+K_BOLT_HEAD+ARCH_SWEEP_CLR=",
            ARCH_PLATE_T + T_LIFT_RAIL + K_BOLT_HEAD + ARCH_SWEEP_CLR));

    // T1-88 (DB12, new): sandwich mode's own lid-top Z fits the user-stated wall gap.
    assert(mode == "direct" || z_rail + h_max <= WALL_GAP + MCC_EPS,
        str("mcc: arch-tv-bracket T1-88 sandwich lid-top Z=", z_rail + h_max, " exceeds WALL_GAP=", WALL_GAP));

    // T1-89.1 (issue #89, D89.1): the centre's local frame (bottom at Z=0, top at centre_t) and the
    // assembly frame (z_rail) are tied together, so a cutter placed with z_rail cannot pass unnoticed.
    assert(abs(z_rail - ARCH_PLATE_T - centre_t) <= MCC_EPS,
        str("mcc: arch-tv-bracket T1-89.1 z_rail - ARCH_PLATE_T=", z_rail - ARCH_PLATE_T, " != centre_t=", centre_t));

    // T1-90 (DB9, new): the spacer's own clamp height/footprint match the arm's sandwich pad exactly
    // (ARCH_PLATE_T / ARM_W -- never centre_t, never a boss diameter). Mode-independent (the spacer
    // itself carries no mode), asserted unconditionally.
    assert(ARCH_PLATE_T >= 2 * MCC_WALL - MCC_EPS,
        str("mcc: arch-tv-bracket T1-90 spacer thickness ARCH_PLATE_T=", ARCH_PLATE_T, " below 2xMCC_WALL=", 2 * MCC_WALL));
    assert((ARM_W - MCC_M8_CLR_D) / 2 >= 2 * MCC_WALL - MCC_EPS,
        str("mcc: arch-tv-bracket T1-90 spacer wall=", (ARM_W - MCC_M8_CLR_D) / 2, " below 2xMCC_WALL=", 2 * MCC_WALL));
    // Fit-check FX2: in sandwich mode, the drawn spacer dimensions must actually equal the arm's own
    // sandwich pad clamp height (pad_clamp_t, which is ARCH_PLATE_T in sandwich mode) and its footprint
    // (ARM_W) -- not just the always-true DB9 constants comparison above.
    if (mode == "sandwich") {
        assert(abs(struct_val(g, "spacer_t") - pad_clamp_t) < MCC_EPS,
            str("mcc: arch-tv-bracket T1-90 spacer thickness ", struct_val(g, "spacer_t"),
                " != the sandwich pad's clamp height ", pad_clamp_t));
        assert(abs(struct_val(g, "spacer_d") - ARM_W) < MCC_EPS,
            str("mcc: arch-tv-bracket T1-90 spacer diameter ", struct_val(g, "spacer_d"), " != ARM_W=", ARM_W));
    }

    // T1-59 (A13): the case hangs BETWEEN the screws (user decision); at full mate it is centred on the
    // rail, which sits at the centre plate's origin.
    assert(l_max / 2 + 10 <= HALF_PITCH - PAD_BOSS_D / 2 + MCC_EPS,
        str("mcc: arch-tv-bracket T1-59 case half-width+10=", l_max / 2 + 10,
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
//   The exported "arm" part (printed TWICE -- PLAN-ASSUMPTION-4), for either mode (`g`'s own
//   "mount_mode" field selects it -- DB8, never the top-level MOUNT_MODE preview selector): a flat
//   bar from the M8 pad (origin) to the joint lap, with a rounded pad end, two top-face edge ribs
//   and 4 heat-set insert bores in the lap. TV face on the bed (local Z=0). Direct mode adds a
//   taller boss carrying the M8 counterbore (unchanged from before #56); sandwich mode's pad is
//   FLAT at the rounded end (no boss, no counterbore -- R42/DB5/DB7) and its ribs start at
//   `rib_pad_gap` instead of the pad centre (DB10).
module mcc_arch_tv_arm(g) {
    mode      = struct_val(g, "mount_mode");
    arm_len   = struct_val(g, "arm_len");
    arm_top_z = struct_val(g, "arm_top_z");
    rib_start = (mode == "direct") ? 0 : struct_val(g, "rib_pad_gap");
    rib_end   = arm_len - LAP_L / 2 - LAP_RIB_GAP;
    // The plain M8 hole's own height: full arm_top_z in direct mode (the counterbore is cut on top
    // of that); just the flat plate's own thickness in sandwich mode (no boss to bore through).
    hole_h = (mode == "direct") ? arm_top_z : ARCH_PLATE_T;

    m8_counterbore_d     = M8_WASHER_D + 2 * MCC_CLR_SLIDE;
    m8_counterbore_depth = M8_WASHER_H + M8_HEAD_K + 0.4;

    difference() {
        union() {
            // Bar (0 -> arm_len+LAP_L/2, the lap is simply the bar's own tail) + rounded pad end --
            // in sandwich mode this rounded end IS the flat clamp pad, no separate feature.
            cuboid([arm_len + LAP_L / 2, ARM_W, ARCH_PLATE_T], anchor = LEFT + BOTTOM);
            cyl(h = ARCH_PLATE_T, d = ARM_W, anchor = BOTTOM, $fn = 64, circum = true);
            // Pad boss (direct mode only): taller than the plate, carries the M8 counterbore
            // (narrower than the pad end disc above -- ARM_W=40 > PAD_BOSS_D=30 -- so it sits
            // within/on top of it).
            if (mode == "direct")
                cyl(h = arm_top_z, d = PAD_BOSS_D, anchor = BOTTOM, $fn = 64, circum = true);
            // Edge ribs, top face, from rib_start (0 direct / rib_pad_gap sandwich) to rib_end.
            for (sy = [-1, 1])
                translate([rib_start, sy * (ARM_W / 2 - RIB_T / 2), ARCH_PLATE_T])
                    cuboid([rib_end - rib_start, RIB_T, RIB_H], anchor = LEFT + BOTTOM);
        }
        // M8 through-hole (full height) + counterbore from the top, direct mode only (§3.4).
        translate([0, 0, -MCC_EPS])
            cyl(h = hole_h + 2 * MCC_EPS, d = MCC_M8_CLR_D, anchor = BOTTOM, $fn = 64, circum = true);
        if (mode == "direct")
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
//   The exported "centre" part, for either mode (DB8): a flat body of thickness `centre_t` (11 mm
//   direct, unchanged; taller in sandwich mode -- §7.1/§7.2) carrying two tabs (the arms' own
//   lap footprint) and the male mount rail on top,
//   with 4 M3 counterbored clearance holes per tab and a cosmetic "UP" arrow deboss (§3.5, B3).
//   Bottom (TV-facing, standing off the TV by `centre_t`) face on the bed (local Z=0). Every formula
//   below that used to assume the centre is ARCH_PLATE_T thick reads `centre_t` instead (DB8) -- in
//   direct mode centre_t==ARCH_PLATE_T, so this reproduces exactly the pre-#56 geometry.
module mcc_arch_tv_centre(g) {
    centre_t = struct_val(g, "centre_t");
    m3_counterbore_d     = M3_HEAD_D + 2 * MCC_CLR_SLIDE;
    m3_counterbore_depth = M3_COUNTERBORE_DEPTH;
    arrow_y = (RAIL_KEEPOUT_Y[1] + CENTRE_W / 2) / 2;

    // The rail is unioned after the plate's own cuts; it needs no cut of its own in the plate (D50).
    union() {
    difference() {
        union() {
            cuboid([2 * C_HALF, CENTRE_W, centre_t], anchor = BOTTOM);
            // Two tabs = the arm laps' own footprint, same transform as the arms themselves
            // (_mcc_arch_tv_place(), re-expressed in centre-local coordinates); the centre has
            // to be keyed to one orientation (it cannot be flipped: the rail would then face the TV).
            for (side = [-1, 1])
                _mcc_arch_tv_place(side)
                    translate([struct_val(g, "arm_len"), 0, 0])
                        cuboid([LAP_L, ARM_W, centre_t], anchor = BOTTOM);
        }
        // 4 M3 counterbored clearance holes per tab, same placement transform as the tabs above.
        for (side = [-1, 1], h = _mcc_arch_tv_joint_holes(g)) {
            p = _mcc_arch_tv_xform(h, side);
            translate([p[0], p[1], -MCC_EPS])
                cyl(h = centre_t + 2 * MCC_EPS, d = MCC_M3_CLR_D, anchor = BOTTOM, $fn = 64, circum = true);
            translate([p[0], p[1], centre_t + MCC_EPS])
                cyl(h = m3_counterbore_depth + MCC_EPS, d = m3_counterbore_d, anchor = TOP, $fn = 64, circum = true);
        }
        // Cosmetic "UP" arrow deboss, top face, pointing +Y -- outside the rail keep-out and below
        // the body edge (T1-60), never in contact with the mated case (it sits in the plate top, centre_t, D89.1).
        translate([-30, arrow_y, centre_t - ARROW_DEPTH])
            linear_extrude(height = ARROW_DEPTH + MCC_EPS)
                polygon([[-ARROW_W / 2, -ARROW_L / 2], [ARROW_W / 2, -ARROW_L / 2], [0, ARROW_L / 2]]);
    }
    // Rail -- centred on this plate (its footprint is symmetric in X, D34), the standard
    // rotate([0,0,180]) rail call, lifted onto this plate's own top face (D50: one union, no plate
    // cut). Sits on top of the centre's OWN thickness, whatever that is in this mode.
    translate([0, 0, centre_t]) rotate([0, 0, 180]) mcc_rail_male();
    }
}

// Module: mcc_arch_tv_spacer()
// Usage:
//   mcc_arch_tv_spacer(g);
// Description:
//   The exported "spacer" part (printed TWICE -- the bracket's own unused, bottom row of VESA
//   holes, sandwich mode only): a flat disc, diameter `spacer_d`, thickness `spacer_t` -- drawn from
//   `g` (fit-check FX2) rather than the constants directly, so T1-90 actually checks what gets
//   printed. In practice spacer_d == ARM_W and spacer_t == ARCH_PLATE_T, matching the arm's own
//   sandwich pad exactly, never `centre_t`, never a boss diameter (R42/DB9) -- with one centred M8
//   through-hole.
module mcc_arch_tv_spacer(g) {
    spacer_t = struct_val(g, "spacer_t");
    spacer_d = struct_val(g, "spacer_d");
    difference() {
        cyl(h = spacer_t, d = spacer_d, anchor = BOTTOM, $fn = 64, circum = true);
        translate([0, 0, -MCC_EPS])
            cyl(h = spacer_t + 2 * MCC_EPS, d = MCC_M8_CLR_D, anchor = BOTTOM, $fn = 64, circum = true);
    }
}

// -----------------------------------------------------------------------------------------
// Top-level: geometry derivation + Tier-1 asserts, run on EVERY render (part dispatch below).
// -----------------------------------------------------------------------------------------

G = mcc_arch_tv_geom(tv_top_clear = TV_TOP_CLEAR, mount_mode = "direct");
mcc_arch_tv_assert(G);

// Sandwich mode's own geometry (issue #56, DB8) -- asserted on EVERY render, regardless of which
// part is being exported, so a change to either file's shared M20 placeholders (or to this file's
// own sandwich-only parameters) fails loudly right away rather than only when arm_sandwich/
// centre_sandwich/spacer happen to be rendered.
G_SANDWICH = mcc_arch_tv_geom(tv_top_clear = TV_TOP_CLEAR, mount_mode = "sandwich");
mcc_arch_tv_assert(G_SANDWICH);

echo(str("arch-tv-bracket: tv_top_clear=", struct_val(G, "tv_top_clear"), " (assumed unless measured, M18a)",
    " arm_len=", struct_val(G, "arm_len"),
    " arm_bbox=", struct_val(G, "arm_bbox"), " centre_bbox=", struct_val(G, "centre_bbox"),
    " case_top_above_rail=", struct_val(G, "case_top_above_rail"),
    " case_bottom_below_rail=", struct_val(G, "case_bottom_below_rail"),
    " pad_clamp_t=", struct_val(G, "pad_clamp_t"), " slide_clear=", struct_val(G, "slide_clear")));
echo(str("arch-tv-bracket sandwich: centre_t=", struct_val(G_SANDWICH, "centre_t"),
    " z_rail=", struct_val(G_SANDWICH, "z_rail"), " m3_joint_screw_l=", struct_val(G_SANDWICH, "m3_joint_screw_l"),
    " rib_pad_gap=", struct_val(G_SANDWICH, "rib_pad_gap"),
    " w_lift_rail=", W_LIFT_RAIL, " (assumed, M20) t_lift_rail=", T_LIFT_RAIL, " (assumed, M20)",
    " k_bolt_head=", K_BOLT_HEAD, " wall_gap=", WALL_GAP, " (user-stated, M20 for the exact lift standoff)"));

// -----------------------------------------------------------------------------------------
// §6: previews (non-exported, invisible to build.py -- discover_brackets() only ever asks for the
// "arm"/"centre"/"arm_sandwich"/"centre_sandwich"/"spacer" parts named by this file's own
// header-line parts marker, above). Every exported part's own mode is fixed by its NAME (DB8), never
// by the top-level MOUNT_MODE variable -- that variable selects only the "assembly"/
// "assembly_sweep" preview's own mode.
// -----------------------------------------------------------------------------------------

if (part == "arm") {
    mcc_arch_tv_arm(G);

} else if (part == "centre") {
    mcc_arch_tv_centre(G);

} else if (part == "arm_sandwich") {
    mcc_arch_tv_arm(G_SANDWICH);

} else if (part == "centre_sandwich") {
    mcc_arch_tv_centre(G_SANDWICH);

} else if (part == "spacer") {
    mcc_arch_tv_spacer(G_SANDWICH);

} else if (part == "assembly" || part == "assembly_sweep") {
    Gp = (MOUNT_MODE == "sandwich") ? G_SANDWICH : G;
    z_rail = struct_val(Gp, "z_rail");
    l_max = struct_val(Gp, "l_max");

    // Both arms, TV face on Z=0 (the assembly frame's own TV back plane).
    for (side = [-1, 1])
        color("Silver") _mcc_arch_tv_place(side) mcc_arch_tv_arm(Gp);

    // Centre, stacked on the arms' laps.
    translate([0, 0, ARCH_PLATE_T])
        color("LightSteelBlue") mcc_arch_tv_centre(Gp);

    // Translucent ghost TV-back slab (z in [-3,0]) + a thin red line at the TV's own top edge
    // (y = tv_top_clear) -- verify-by-picture (#26's own rule): confirm the case top stays below
    // the red line, and (assembly_sweep only) the case floor clears the right arm's pad.
    %translate([0, (TV_TOP_CLEAR - HALF_PITCH - 100) / 2, -3]) cuboid([2 * HALF_PITCH + 100, TV_TOP_CLEAR + HALF_PITCH + 100, 3], anchor = BOTTOM);
    color("Red") translate([0, struct_val(Gp, "tv_top_clear"), 0]) cuboid([2 * HALF_PITCH + 100, 1, 1]);

    // Grey ghost M8 heads, seated in each pad's counterbore (direct mode only -- sandwich mode's pad
    // is flat, and its bolt head sits on the OTHER side of the TV lift's own rail, represented by the
    // orange ghost below instead).
    if (MOUNT_MODE == "direct")
        for (side = [-1, 1])
            color("Gray") translate([side * HALF_PITCH, 0, struct_val(Gp, "arm_top_z") - (M8_HEAD_K / 2 + 0.4)])
                cyl(h = M8_HEAD_K, d = M8_WASHER_D, anchor = CENTER, $fn = 64, circum = true);

    // Sandwich mode only (DB12 §7.3 step 10): a translucent ghost box at the right-hand column,
    // standing ARCH_PLATE_T off the TV back, representing the TV lift's own rail + bolt head that the
    // +X slide-on sweep must clear in Z (T1-87) -- verify by picture that the ghost case floor below
    // visibly clears it during "assembly_sweep".
    if (MOUNT_MODE == "sandwich")
        %translate([HALF_PITCH, 0, ARCH_PLATE_T])
            cuboid([W_LIFT_RAIL, W_LIFT_RAIL, T_LIFT_RAIL + K_BOLT_HEAD], anchor = BOTTOM);

    // Ghost case, mated onto the rail -- the Plus-family SKU that ships the fan (CLAUDE.md fixed
    // decision), same variant its own case.scad uses. "assembly_sweep" shifts it by slide_clear
    // (B6) to show the floor passing over the right arm and pad during the +X slide-on approach.
    dev = MCC_DEV_PRO_CONVERT_HDMI_PLUS;
    variant = [["fan", true], ["splitter", false], ["fan_switch", true], ["tripod_insert", false], ["lid_vents", true]]; // tripod off: T1-63 (D44)
    layout = mcc_case_layout(dev, variant);
    x_shift = (part == "assembly_sweep") ? struct_val(Gp, "slide_clear") : 0;

    translate([x_shift, MCC_RAIL_Y, z_rail]) rotate([0, 0, 180]) { // D44: flush
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
