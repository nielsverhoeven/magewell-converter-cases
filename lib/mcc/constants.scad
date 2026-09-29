//////////////////////////////////////////////////////////////////////
// LibFile: mcc/constants.scad
//   L0. Dimensions, tolerances, and part tables for magewell-converter-cases.
//   Variables and PURE FUNCTIONS ONLY — no modules (architecture.md:90-92, hard rule).
//   This file is `include`d (not `use`d) by lib/mcc/mcc.scad; every other L1+ file gets
//   these symbols transitively through the barrel and must not include this file directly
//   except where noted in architecture.md:88-99.
// Includes:
//   include <mcc/mcc.scad>
//////////////////////////////////////////////////////////////////////

// struct_val()/search() (BOSL2 structs.scad) are used by the panel-part accessors below.
// Included directly here (rather than assumed-ambient) per the environment note: "library files
// that need BOSL2 use include <BOSL2/std.scad>" — this remains a pure-function-only file, an
// `include` is not a module definition and does not violate the "no module" rule.
include <BOSL2/std.scad>

// -----------------------------------------------------------------------------------------
// Section: Core dimensions and print policy
// -----------------------------------------------------------------------------------------

MCC_WALL      = 3.0;   // shell wall thickness, mm. architecture.md:46 "ASA shell, 3 mm walls"
MCC_FLOOR_T   = 3.0;   // floor thickness, mm. Same rationale as MCC_WALL (uniform shell spec).
MCC_LID_T     = 3.0;   // lid thickness, mm. Same rationale as MCC_WALL.
MCC_BUILD     = 256;   // build volume cube edge, mm. architecture.md:44 "Bambu Lab X1C / P1S, 256 mm cube"
MCC_BED_MARGIN = 6;    // keep-out margin from the bed edge, mm. assumed — generic FDM brim/skirt clearance.
MCC_EPS       = 0.01;  // generic non-manifold-avoidance epsilon, mm. assumed — standard CSG overlap epsilon.

// Hole compensation added to a connector's minimum documented hole diameter to get the
// nominal CAD hole diameter for a hole that must clear a real part on an FDM printer.
// knowledge/neutrik/d-series-cutout.md:38-43 "Ø24.2-24.4 mm nominal (24.0 mm official minimum +
// typical FDM hole-shrink allowance of 0.2-0.4 mm)". 0.2 is the low (conservative) end of that
// band, tuned down further by the tolerance-ladder/neutrik-tile coupons.
MCC_HOLE_COMP = 0.2;

// -----------------------------------------------------------------------------------------
// Section: Fit clearances (defaults; calibrated by the Tier-4 physical coupons per
// architecture.md:364-375 — each is replaced with a measured value + coupon name + date once
// the coupon has been printed and read back)
// -----------------------------------------------------------------------------------------

MCC_CLR_TG    = 0.25;  // tongue-and-groove per-side clearance, mm. assumed default — calibrate with
                        // models/coupons/tg-ladder.scad (architecture.md:370).
MCC_CLR_SLIDE = 0.3;   // sliding-fit per-side clearance, mm. assumed default — calibrate with
                        // models/coupons/tolerance-ladder.scad (architecture.md:372).
MCC_CLR_PRESS = 0.1;   // press-fit per-side clearance, mm. assumed default — same coupon as above.

// -----------------------------------------------------------------------------------------
// Section: Neutrik D-series cutout geometry
// All figures cross-checked from five official Neutrik drawings; see
// knowledge/neutrik/d-series-cutout.md and knowledge/neutrik/placement-and-depth.md.
// -----------------------------------------------------------------------------------------

MCC_D_FLANGE       = [26, 31]; // flange footprint W x H, mm. knowledge/neutrik/d-series-cutout.md:74
                                // "26.0 mm wide x 31.0 mm tall"
MCC_D_FLANGE_R     = 3.5;      // flange corner radius, mm. knowledge/neutrik/d-series-cutout.md:75-76
                                // "corner radius R3.5 mm (from the DBA-BL blanking-plate drawing)"
MCC_D_SCREW_PITCH  = [19.0, 24.0]; // screw hole-to-hole pitch [X,Y], mm.
                                    // knowledge/neutrik/d-series-cutout.md:47 "±9.5 mm horizontally
                                    // (19.0 mm hole-to-hole) and ±12.0 mm vertically (24.0 mm hole-to-hole)"
MCC_D_SCREW_D      = 3.2;      // screw clearance hole diameter, mm. knowledge/neutrik/d-series-cutout.md:49-52
                                // "NE8FDP: Ø3.2 mm min" — used as the conservative default for MCC_M3_CLR_D
                                // sizing at the Neutrik screw positions (a genuine M3 clearance hole is used
                                // instead, see MCC_M3_CLR_D, which is looser and covers the whole ⌀3.1-3.5 range).
MCC_D_PITCH_H      = 32;       // minimum horizontal center-to-center spacing between adjacent D cutouts, mm.
                                // knowledge/neutrik/placement-and-depth.md:42 "Horizontal ... >= 30-32 mm"
                                // (upper/conservative end of the recommended band).
MCC_D_PITCH_V      = 36;       // minimum vertical center-to-center spacing between adjacent D cutouts, mm.
                                // knowledge/neutrik/placement-and-depth.md:43 "Vertical ... >= 35-38 mm"
                                // (conservative mid-band value).
MCC_D_FLANGE_EDGE_MARGIN = 4;  // minimum web from a flange edge to the panel/frame edge, mm.
                                // architecture.md:345 Tier-1 assert "each flange 26 x 31 fits on
                                // the panel with >= 4 mm web to the frame", itself derived from
                                // knowledge/neutrik/placement-and-depth.md:44 "Increase the web
                                // further (to ~6-10 mm) if the wall is thin".
MCC_PANEL_SEAT_T   = 2.0;      // default connector-panel seat thickness, mm. architecture.md:174-176 /
                                // knowledge/neutrik/d-series-cutout.md:90 "NAHDMI-W ... max. 2 mm" — the
                                // safe common denominator across the whole D-series family.

// -----------------------------------------------------------------------------------------
// Section: Heat-set inserts, fasteners, magnets
// knowledge/components/fasteners-and-hardware.md §1-2.
// -----------------------------------------------------------------------------------------

// M3 heat-set insert (Ruthex RX-M3x5.7), keyed struct-style assoc list (BOSL2 structs.scad shape).
// hole_d: knowledge/components/fasteners-and-hardware.md:22 "Recommended print/drill hole diameter,
//         M3: 4.0 mm nominal (community and forum consensus)" — this is the value the insert-boss
//         coupon (models/coupons/insert-boss.scad) tunes; see also the CNC Kitchen shrink-comp note
//         at fasteners-and-hardware.md:26-28 and the 4.24-4.30 mm CAD-pocket cross-check table at
//         fasteners-and-hardware.md:60 (ASA/ABS column) which the brief also references.
// od:     assumed — the Ruthex spiral/knurl sleeve outer diameter is not stated in
//         fasteners-and-hardware.md (only hole sizing and length are sourced); 4.6 mm is the common
//         published Ruthex RX-M3x5.7 sleeve OD. confidence: assumed. TODO(teamlead): confirm against
//         a physical insert or the Ruthex datasheet and re-cite.
// len:    knowledge/components/fasteners-and-hardware.md:17 "Standard M3 insert | RX-M3x5.7 — length 5.7 mm"
MCC_INSERT_M3 = [
    ["hole_d", 4.0],
    ["od",     4.6],
    ["len",    5.7],
];

// 1/4"-20 heat-set insert for the case's OWN floor mounting feature (case -> tripod/cheeseplate;
// architecture.md §6 floor rule, D-09 -- NOT the device-retention side bolt below, which threads
// directly into the device's metal body and needs no insert). No 1/4"-20 insert figures exist
// anywhere in knowledge/components/fasteners-and-hardware.md (checked -- that file sources only
// the M3 RX-M3x5.7/RX-M3S inserts above); the figures below are typical brass 1/4"-20 heat-set
// insert dimensions (generic hardware-catalog range, not project-sourced). confidence: assumed.
MCC_INSERT_1_4_20 = [
    ["hole_d",     8.8],  // assumed -- mid of the typical 8.6-9.0 mm print/drill hole range.
    ["od",         9.5],  // assumed -- typical brass 1/4"-20 heat-set insert sleeve OD.
    ["len",        12.7], // assumed -- typical brass 1/4"-20 heat-set insert length.
    ["confidence", "assumed"],
];

// M4 heat-set insert (Ruthex RX-M4x8.1 class), same keyed struct shape as MCC_INSERT_M3. Currently
// UNUSED in lib/mcc/** — it backed the floor VESA 75x75 blind-insert bosses, retired by issue #25
// (D-15, rev 9, the mount rail replaces VESA). Kept as a generic M4 heat-set insert record for any
// future floor/panel feature that needs one, rather than deleted along with its only caller. No M4
// insert figures exist in knowledge/components/fasteners-and-hardware.md (which sources only the M3
// RX-M3x5.7/RX-M3S family) — the figures below are typical brass/Ruthex M4 heat-set insert
// dimensions (generic hardware-catalog range, not project-sourced), following the same "typical"
// pattern already used for MCC_INSERT_1_4_20 above. confidence: assumed.
MCC_INSERT_M4 = [
    ["hole_d", 5.5],
    ["od",     6.3],
    ["len",    8.1],
];

MCC_BOSS_MIN_RATIO = 1.8;  // heat-set boss OD >= this * insert OD. architecture.md:348 (Tier-1 assert
                            // table) / architecture.md:207 "OD ... to ~7 mm total" design rule.

// 1/4"-20 tripod thread. This is the ONLY place an inch-derived value is allowed in this repo
// (architecture.md:115-116) — it is captured here as a named mm constant, never as an inline
// literal elsewhere. 1/4 in = 6.35 mm; UNC 1/4"-20 major diameter is nominally 6.35 mm (ANSI/ASME
// B1.1 standard thread major-diameter figure — not sourced from knowledge/**, this is a fixed
// mechanical-standard constant). confidence: assumed (standard, not project-sourced).
MCC_TRIPOD_MAJOR_D = 6.35;  // 1/4"-20 (0.25 in) major thread diameter, mm.
MCC_TRIPOD_CLR_D    = 6.6;  // through-hole clearance for a 1/4"-20 bolt, mm. assumed (major dia + ~0.25 mm).

MCC_M3_CLR_D = 3.4; // generic M3 clearance hole, mm. assumed — standard M3 clearance (mid-range of the
                     // ISO 273 "medium" fit, 3.2-3.6 mm) rounded to match d-series-cutout.md:52's own
                     // "Recommendation: Ø3.5 mm clearance hole" guidance minus FDM hole-shrink undersize.
MCC_M4_CLR_D = 4.5;  // generic M4 clearance hole, mm. assumed — standard ISO 273 "medium" M4 clearance.
MCC_M8_CLR_D = 9.0;  // generic M8 clearance hole, mm. assumed — ISO-medium M8 clearance, generous
                     // enough to also pass an M6 screw (issue #26's VESA MIS-F 200x200 pattern
                     // takes M6 or M8 per the mount's own hardware —
                     // docs/plans/2026-09-09-mount-rail-and-brackets.md §3.1, VESA MIS-F spec via
                     // Wikipedia). Reused for both bolt sizes rather than adding a third clearance
                     // constant that would only drift from this one.

MCC_M3_MAJOR_D = 3.0; // M3 nominal major diameter, mm. Fixed mechanical standard (ISO metric
                       // coarse), same footing as MCC_TRIPOD_MAJOR_D above. Was
                       // MCC_THREAD_M3_MAJOR_D in the retired "Printed M3 threads" section
                       // (architecture.md §13 D41). Only consumer: models/brackets/arch-tv-bracket.scad
                       // (its T1-57 M3-engagement assert).

// -----------------------------------------------------------------------------------------
// Section: Captive side bolt (D-09) — device retention through the far (-Y) wall
// .claude/knowledge/layout-patch-wall.md §7.1 / §11. A captive 1/4"-20 slotted screw runs through
// a boss in the far wall into the device's side thread, held captive by a DIN 6799 E-clip in a
// pocket inside the boss; a compliant EPDM pad on the boss face provides the preload.
// architecture.md §6 far-wall rule / §13 D1-D2. Every figure here is `assumed` (none of this
// hardware is sourced/measured yet — architecture.md R16-R19, measurement list M1/M2/M4/M5) unless
// the comment says otherwise.
// -----------------------------------------------------------------------------------------

// --- captive side bolt (D-09) ---

MCC_SIDE_BOLT_HEAD_D     = 10.0; // slotted screw head diameter, mm. assumed (M5) —
                                  // layout-patch-wall.md §7.1 "Head diameter / height ... 10.0 /
                                  // 4.5 mm assumed. Nearest metric standard is ISO 1207/DIN 84
                                  // cheese head M6 (dk 10.0, k 3.9)".
MCC_SIDE_BOLT_HEAD_H     = 4.5;  // slotted screw head height, mm. assumed (M5), same source.
MCC_SIDE_BOLT_HEAD_REC_D = 12.0; // head recess (counterbore) diameter, mm. layout-patch-wall.md
                                  // §7.1 axial stack "[0, 6.0] Slotted head recess 12.0". assumed.
MCC_SIDE_BOLT_HEAD_REC_H = 6.0;  // head recess depth, mm. Same table; = head height + 1.5 so the
                                  // head sits >= 1 mm below the outer surface (drop rule). assumed.

MCC_SIDE_BOLT_WEB_T = 3.0; // retaining web thickness behind the head recess, mm — the shoulder the
                            // E-clip lands on. layout-patch-wall.md §7.1 axial stack "[6.0, 9.0]
                            // Retaining web, shank clearance bore ... web_t = 3.0". assumed.

// DIN 6799, nominal size 5 (the size normally listed for a 6-7 mm shaft, matching the 6.35 mm
// 1/4"-20 shank / MCC_TRIPOD_CLR_D). NOT VERIFIED: DIN 6799 is not in knowledge/** and these
// figures were not read from the standard (architecture.md R16). Confirm before ordering (M4).
// layout-patch-wall.md §7.1 "E-clip | DIN 6799, nominal size 5 ... Groove d 5.0, groove width 0.8,
// clip OD ~11.0, thickness 0.7". confidence: assumed throughout.
MCC_SIDE_BOLT_CLIP = [
    ["groove_d", 5.0],
    ["groove_w", 0.8],
    ["od",       11.0],
    ["t",        0.7],
];

MCC_SIDE_BOLT_POCKET_D = 13.0; // E-clip clearance pocket diameter, mm. assumed —
                                // layout-patch-wall.md §7.1 axial stack "[9.0, 17.0] E-clip
                                // clearance pocket 13.0".
MCC_SIDE_BOLT_POCKET_H = 8.0;  // E-clip clearance pocket depth, mm. assumed, same table;
                                // = engagement 6.0 + clip thickness 0.7 + 1.3 mm margin.

MCC_SIDE_BOLT_ENGAGE = 6.0; // thread engagement length into the device's side thread, mm. assumed
                             // (M2 — the device's thread depth is unmeasured) —
                             // layout-patch-wall.md §7.1 axial stack "[19.0, 25.05] Thread
                             // engagement into the device ... e = 6.0".

MCC_SIDE_BOLT_BOSS_OD = 20.0; // captive-bolt boss outer diameter, mm. layout-patch-wall.md §7.1
                               // "boss_od = pocket_d + 2*3.5 = 20.0". assumed (derives from the
                               // assumed pocket diameter above).

MCC_SIDE_BOLT_PAD_T  = 2.0;  // compliant EPDM pad thickness on the boss face, mm (compressed
                              // working thickness). assumed — layout-patch-wall.md §1 "Compliant
                              // pad 2.0 mm: EPDM anti-slip pad,
                              // knowledge/components/fasteners-and-hardware.md:186 (Ø12x2.5mm
                              // listed; 2.0mm used as the compressed working thickness, assumed)".
MCC_SIDE_BOLT_PAD_OD  = 18.0; // compliant pad outer diameter, mm. assumed — layout-patch-wall.md
                               // §7.1 "Compliant pad (EPDM annulus, OD 18 / ID 8)".
MCC_SIDE_BOLT_PAD_ID  = 8.0;  // compliant pad inner diameter, mm. assumed, same source.

MCC_SIDE_BOLT_AXIS_Z = 25.5; // bolt axis height in case Z coords (floor = 0), mm — used to size the
                              // internal support web's floor-to-axis run (D-13). Equals the
                              // connector centreline the whole case is built around —
                              // layout-patch-wall.md §1 "z_conn_c = MCC_FLOOR_T + MCC_PANEL_BAND +
                              // MCC_PLATE_H/2 = 3 + 3 + 19.5 = 25.5" and §7.1 "z_bolt = z_conn_c +
                              // mcc_port_pos(p)[1] = 25.5 + v", evaluated at the still-unmeasured
                              // v's documented placeholder of 0 (M1). `assumed` — MCC_PANEL_BAND and
                              // MCC_PLATE_H are not yet named constants here (they belong to the
                              // not-yet-written shell/panel milestone), so this is the doc's cited
                              // literal 25.5 rather than a live re-derivation from those two.

// D-13 (layout-patch-wall.md rev 3 §1/§7.1, architecture.md §6 far-wall rule): MCC_GAP_FAR is
// DERIVED from the captive-bolt axial stack, not chosen — solve for the gap first, then
// MCC_SIDE_BOLT_PROUD (below) falls out of that solve. Ordering requirement (layout-patch-wall.md
// §11 "Ordering constraint"): this block must come after the head/web/pocket/pad constants above
// and before MCC_SIDE_BOLT_PROUD and anything that computes W.
MCC_GAP_FAR_DUCT_MIN = 6.0; // old airflow-duct floor for MCC_GAP_FAR, mm. assumed —
                             // layout-patch-wall.md §1 "MCC_GAP_FAR_DUCT_MIN = 6.0 (assumed) is
                             // the old airflow-duct floor and is now non-binding. The duct is a
                             // consequence of the fastener, not its justification — do not
                             // 'optimise' the gap back to 6 mm". Kept only so the max() below
                             // documents both drivers.
MCC_GAP_FAR = max(MCC_GAP_FAR_DUCT_MIN,
                   (MCC_SIDE_BOLT_HEAD_REC_H + MCC_SIDE_BOLT_WEB_T + MCC_SIDE_BOLT_POCKET_H)
                       + MCC_SIDE_BOLT_PAD_T - MCC_WALL);
             // clearance gap between the far (-Y) wall's inner face and the device flank, mm.
             // DERIVED (D-13) — layout-patch-wall.md §1 "MCC_GAP_FAR = max(MCC_GAP_FAR_DUCT_MIN,
             // boss_len + MCC_PAD_T - MCC_WALL) = max(6.0, 17.0 + 2.0 - 3.0) = 16.0", where
             // boss_len = MCC_SIDE_BOLT_HEAD_REC_H + MCC_SIDE_BOLT_WEB_T + MCC_SIDE_BOLT_POCKET_H
             // = 6.0 + 3.0 + 8.0 = 17.0. Evaluates to 16.0 (was a flat 6.0 assumed, pre-D-13). If a
             // measurement (M5) makes the head taller, this constant — and therefore W — grows; the
             // wall never grows a lug again.

// Derived quantities — formulas, not magic numbers, per layout-patch-wall.md §7.1 ("all of these
// are formulas, not magic numbers, and belong in constants.scad"). Kept here (not recomputed
// inline in fasteners.scad) so a change to any input above updates every derived figure in one
// place.
MCC_SIDE_BOLT_PROUD = max(0, (MCC_SIDE_BOLT_HEAD_REC_H + MCC_SIDE_BOLT_WEB_T + MCC_SIDE_BOLT_POCKET_H)
                             - (MCC_WALL + MCC_GAP_FAR - MCC_SIDE_BOLT_PAD_T));
                     // how far the boss stands proud of the far wall's outer face, mm.
                     // DERIVED (D-13) — layout-patch-wall.md §7.1 "MCC_SIDE_BOLT_PROUD = max(0,
                     // boss_len + MCC_PAD_T - (MCC_WALL + MCC_GAP_FAR)) = max(0, 19.0 - 19.0) =
                     // 0.0". Evaluates to 0.0 (was 10.0 pre-D-13). Zero margin is intentional but
                     // tight — see T1-29 in fasteners.scad. Stays a parameter (not folded to a bare
                     // 0) so a future variant can deliberately go proud, and so a taller measured
                     // head (M5) fails loudly instead of silently reintroducing a lug.

MCC_SIDE_BOLT_SCREW_LEN = 19.05; // screw length under the head, mm (stock 3/4" UNC).
                                  // layout-patch-wall.md §7.1 "screw_len_under_head = ... = 19.0 ->
                                  // stock 3/4" = 19.05". assumed.

MCC_SIDE_BOLT_GROOVE_POS = MCC_SIDE_BOLT_WEB_T + MCC_SIDE_BOLT_ENGAGE + 1.0;
                     // retaining-groove position on the shank, mm from the under-head face.
                     // layout-patch-wall.md §7.1 "groove_pos = web_t + e + 1.0 = 10.0". assumed —
                     // on a fully-threaded stock screw this lands in the threads (see R16).

MCC_SIDE_BOLT_KEEPOUT_D = MCC_SIDE_BOLT_BOSS_OD + 2 * 2.0;
                     // far-wall keep-out disc diameter for vents/ribs/lid bosses, mm.
                     // layout-patch-wall.md §7.1 "keepout_d = boss_od + 2*2.0 = 24.0". Also
                     // exposed parametrically as mcc_side_bolt_keepout() in fasteners.scad.

MCC_SIDE_BOLT_SUPPORT_WEB_T = MCC_WALL; // central vertical support web thickness (in X), mm — D-13.
                     // The flush boss (MCC_SIDE_BOLT_PROUD=0) is a horizontal OD20 cylinder
                     // cantilevered 14 mm off a vertical wall; a pure <=45 deg conical blend alone
                     // would need a OD48 root (collides with the vent band/ribs/lid bosses), so a
                     // plain vertical fin from the interior floor up to the boss underside carries
                     // it instead. layout-patch-wall.md §7.1 "web_support_t = MCC_WALL = 3.0".
                     // Caps the largest unsupported horizontal span under the boss at
                     // (boss_od - support_web_t)/2 = 8.5 mm — see T1-31 in fasteners.scad.

MCC_SIDE_BOLT_KEEPOUT_STRIP_W = MCC_SIDE_BOLT_SUPPORT_WEB_T + 2 * 2.0;
                     // width of the vent/rib keep-out strip below the OD24 disc, running from the
                     // interior floor up to the disc — the support web's own wall footprint, so a
                     // vent slot cut there would open into solid material. DERIVED (D-13) —
                     // layout-patch-wall.md §7.1 "keepout_strip_w = web_support_t + 2*2.0 = 7.0".

// -----------------------------------------------------------------------------------------
// Section: Patch-wall layout (L2 milestone)
// .claude/knowledge/layout-patch-wall.md rev 5 / architecture.md §14. Every case-envelope,
// slot-assignment, end-zone, cradle, vent and floor-keepout formula in lib/mcc/layout.scad and the
// L2 geometry files (shell/cradle/mounts/vents.scad) is driven by the constants below — those
// files must never re-derive these numbers independently (layout-patch-wall.md §11 "Ordering
// constraint" / §15 rulings 3-5). Values marked "rev-5" replaced an earlier plan draft's guess
// after the architect's L2 gate (layout-patch-wall.md §15 addendum, 2026-09-08) — do not revert
// them to the superseded numbers.
// -----------------------------------------------------------------------------------------

MCC_PANEL_BEZEL_T = 3.0; // proud sacrificial-bezel layer of the patch-wall Y stack, mm.
                          // layout-patch-wall.md §2.1 "Proud sacrificial bezel ... 3.0 assumed";
                          // §15 addendum "the proud sacrificial-bezel layer of MCC_T_PATCH; needed
                          // explicitly now that the rabbet is stepped (§2.5)".

// Patch-wall connector-cut constants (rev-6 aperture ruling, re-scoped by D36/D40/D41 --
// architecture.md §5 rev 15). The seat hole and body window are PLAIN CIRCLES (D40, user decision
// 2026-09-28: "perfectly round"), so the teardrop constants MCC_APERTURE_BRIDGE_MAX and
// MCC_APERTURE_CAP_RISE are retired, not parameterised. Deliberately NOT added here:
// MCC_APERTURE_TOP_OPEN -- the top-open (U-notch) aperture is rejected (layout-patch-wall.md §15
// ruling 2026-09-08b).
MCC_WALL_BORE_WEB_MIN = 1.2; // assumed -- minimum wall between a connector's fixing bore and the
                          // seat hole / body window beside it, mm: three 0.4 mm perimeters. T1-61
                          // (filed as "T1-48" and named MCC_WALL_THREAD_WEB_MIN under D36; renamed
                          // by D41, renumbered by D42). The bores sit 15.3 mm from the connector
                          // centre on a ~24 mm hole, so this is the tightest web in the patch wall.
MCC_APERTURE_LIP_WEB_MIN = 2.0; // minimum lip material between any part of a window and the plate's
                          // own edge, mm. knowledge/design/fdm-rugged-enclosure-guidelines.md:127.
                          // T1-34c.
MCC_INSERT_BORE_EXTRA = 0.5; // assumed -- extra bore depth past a heat-set insert's own length so
                          // the insert seats fully, mm. Replaces the bare "+ 1" literal in
                          // the old connector bosses (deviation D10 / T1-35).

// -----------------------------------------------------------------------------------------
// Section: Connector-fixing bore (architecture.md §5 rev 15, D41) -- the connector's own two screw
// holes (MCC_D_SCREW_PITCH diagonal) are a PLAIN, UNTHREADED bore straight through the patch wall
// (MCC_PANEL_SEAT_T + MCC_WALL = 5 mm). User decision 2026-09-28: no printed thread ("the thread
// with those little triangles is really bad"); the external CAD specialist models the M3x0.5
// thread on the exact STEP. How a PRINTED case gets its thread is open (architecture.md §12 Q20).
// -----------------------------------------------------------------------------------------

MCC_FIXING_BORE_D = 2.5; // fixing-bore diameter, mm: the ISO metric M3x0.5 tap-drill size. User
                          // decision 2026-09-28 (architecture.md §13 D41). Modelled at this
                          // NOMINAL diameter -- no circum=true, no MCC_HOLE_COMP, no chamfer: it is a
                          // CAD input and the exact STEP must carry exactly 2.5 (architecture.md §3
                          // rev 15). Printed size/roundness not yet measured: neutrik-tile, M19.

MCC_T_PATCH = MCC_PANEL_BEZEL_T + MCC_PANEL_SEAT_T + MCC_WALL;
                          // total patch-wall Y stack at the panel band, mm. DERIVED —
                          // layout-patch-wall.md §2.1 "MCC_T_PATCH total = 8.0" =
                          // MCC_PANEL_BEZEL_T(3.0) + MCC_PANEL_SEAT_T(2.0, already defined above) +
                          // MCC_WALL(3.0, structural rabbet lip). §15 addendum confirms this exact
                          // decomposition.
MCC_PANEL_BAND = MCC_WALL; // continuous shell band above/below the panel aperture, mm. = MCC_WALL
                            // by definition — layout-patch-wall.md §2.2 "MCC_PANEL_BAND = 3.0 //
                            // continuous shell band above and below the aperture (= MCC_WALL)".
MCC_PLATE_H = MCC_D_FLANGE[1] + 2 * MCC_D_FLANGE_EDGE_MARGIN;
                            // panel-plate height, mm. DERIVED — layout-patch-wall.md §2.2 "MCC_PLATE_H
                            // >= MCC_D_FLANGE[1] + 2*MCC_D_FLANGE_EDGE_MARGIN = 31 + 2*4.0 = 39.0"
                            // (the web rule governs, D-06 vetoed 2026-09-08 — the rear-boss rule
                            // 36.28 is satisfied but not binding). Evaluates to 39.0.
MCC_PANEL_FRAME_MIN = 10.0; // shell frame band beyond each end of the panel plate, mm. assumed —
                             // layout-patch-wall.md §2.3.
MCC_PLATE_END_PAD = 8.0;   // plate material outboard of the outer flange, carries the M3 retaining
                            // tabs, mm. assumed — layout-patch-wall.md §2.3.
MCC_SLOTS_MAX = 4;         // max D-connectors per case (fixed user decision, CLAUDE.md "max 4
                            // D-connectors per model"). layout-patch-wall.md §3 step 1.
MCC_END_ZONE_MIN = 20.0;   // floor for a cable end zone even with no ports on that end, mm.
                            // assumed — layout-patch-wall.md §4.
MCC_GAP_DEV = 2.0;         // clearance between the deepest plug envelope and the device's patch-side
                            // flank, mm. assumed — layout-patch-wall.md §4.
MCC_LID_SPAN_MAX = 180.0;  // lid span threshold above which 6 (not 4) captive thumbscrews are used,
                            // mm. Architect-derived, user-reviewed, ACCEPTED 2026-09-08 (D-04) —
                            // layout-patch-wall.md §6 / §10.
MCC_WEB_BORE_KEEP = 0.8; // how far a lid-boss web reaches INTO its boss (radially, from the boss's
                         // outer radius), mm (D38). Only has to be a real overlap and stay well
                         // outside the insert bore; not a physical dimension of any part.
MCC_FASTENER_INSET = 10.0; // lid-fastener ring inset from the outer faces ("e"), mm. assumed —
                            // layout-patch-wall.md §6.
MCC_LID_FASTENER_CLR_MIN =
    MCC_BOSS_MIN_RATIO * struct_val(MCC_INSERT_M3, "od") / 2 + 2.0;
                            // minimum clearance from a lid-fastener boss to the nearest D-flange
                            // edge, mm. DERIVED — layout-patch-wall.md §6 "boss_od/2 + 2.0" using
                            // the same M3 heat-set boss geometry as every other captive thumbscrew
                            // in this repo (MCC_BOSS_MIN_RATIO * insert od = 8.28 mm boss_od).
                            // Evaluates to 6.14 (the doc's own worked table rounds this to "6.15";
                            // this is the exact value the code computes — layout-patch-wall.md §15's
                            // own rounding-artifact precedent for MCC's W figures applies here too).

// Per-kind device-side cable allowance table (layout-patch-wall.md §4). Struct-style, mirrors
// MCC_PANEL_PARTS' shape. Sourced per-kind in that section's own table; ports that are never cabled
// (internal switches/buttons, the side-bolt thread) get 0.
MCC_DEV_SIDE_ALLOW = [
    ["bnc",            41], // Belden 4855R min bend radius, verified; layout-patch-wall.md §4.
    ["hdmi_a",         40], // 25 (assumed axial, straight plug — D-08 vetoed) + 15 (mcc_bend_envelope
                             // ("NAHDMI-W-B")). layout-patch-wall.md §4.
    ["rj45",           27], // 21.5 mm max plug (TIA-568.2-D, verified) + 5 mm margin.
    ["usb_a",          17], // 12 mm verified + 5 mm margin.
    ["usb_b",          17], // USB-B assumed equal to USB-A (source: unknown for USB-B specifically).
    ["minidin8",        0], // internal, not cabled (D-01).
    ["rotary16",        0], // not cabled.
    ["button",          0], // not cabled.
    ["tripod_1_4_20",   0], // the side bolt is on a long face, never an end face (D-09).
    ["blank",           0], // nothing plugs into a blank.
];

// Function: mcc_dev_side_allow()
// Usage:
//   allow = mcc_dev_side_allow(kind);
// Description:
//   Device-side end-zone cable allowance for a port `kind`, mm — layout-patch-wall.md §4's
//   ez_cable(end) input. Reads MCC_DEV_SIDE_ALLOW so it stays a single source of truth alongside
//   MCC_PANEL_PARTS' own bend/plug_len figures.
function mcc_dev_side_allow(kind) =
    let(ind = search([kind], MCC_DEV_SIDE_ALLOW)[0])
    assert(ind != [], str("mcc: unknown port kind \"", kind, "\" in mcc_dev_side_allow()"))
    MCC_DEV_SIDE_ALLOW[ind][1];

// -----------------------------------------------------------------------------------------
// Section: Axial straight-plug lengths (T1-18(c) fix, layout-patch-wall.md §16.3 / §15 ruling
// 2026-09-08c C3, architecture.md §13 blocking pre-flight change).
//
// BUG THIS REPLACES: shell.scad's +X end-zone assert (T1-18(c)) used to special-case
// `kind == "bnc"` and charge it `mcc_plug_len("NBB75DFGB")` (= 40.6 mm) as the AXIAL plug term —
// but that 40.6 is the Belden 4855R bend radius, a LATERAL figure re-used for BNC's `plug_len`/
// `bend` table entries (see the MCC_PANEL_PARTS "NBB75DFGB" row comment above: "for BNC the bend
// radius genuinely governs both axial and lateral clearance simultaneously"). Charging a lateral
// allowance against an axial budget double-counts it, and the assert failed by 14.60 mm on every
// BNC-ended SKU (SDI TX, SDI Plus, NDI to SDI, NDI to AIO — layout-patch-wall.md §16.3 worked
// table). The non-BNC branch's `mcc_dev_side_allow(kind) - mcc_bend_envelope(panel)` computation
// was itself only ever correct for hdmi_a (40 - 15 = 25, the assumed straight-plug axial length);
// it is retired here too so every kind reads its axial figure from ONE table, no per-kind
// special case in shell.scad.
//
// Sourced/assumed per kind (layout-patch-wall.md §16.3 option (a), ADOPTED):
//   hdmi_a: 25.0 assumed straight-plug axial length — cables.md:121 records the true figure as
//           "unknown — physically measure"; 25.0 matches the pre-existing `ez(hdmi_a) - bend`
//           decomposition (40 - 15 = 25) so T1-18(c) is numerically unchanged on every HDMI-ended
//           SKU (still exactly 0.00 mm slack, layout-patch-wall.md §16.3).
//   bnc:    25.0 assumed — knowledge/components/cables.md gives NO BNC male plug body length at
//           all (cables.md:64 "unknown"); pending physical measurement M6 (depth-mockup coupon).
//           Deliberately the SAME class/value of placeholder as hdmi_a (both "assumed straight
//           plug, unmeasured") rather than reusing the bend-radius figure a second time.
//   rj45:   21.5 — knowledge/components/cables.md:119 "21.5 mm max plug" (TIA-568.2-D, verified).
//           Never exercised by T1-18(c) today (RJ45 is always in the -X block per the slot rule's
//           own cross-check, layout-patch-wall.md §3), included for completeness/future-proofing.
//   usb_a/usb_b: 12.0 — knowledge/components/cables.md:125 "USB-A ... 12 mm" verified; USB-B
//           assumed equal (no USB-B-specific figure exists), same convention as
//           MCC_DEV_SIDE_ALLOW's own usb_b row above.
// -----------------------------------------------------------------------------------------

MCC_PLUG_AXIAL = [
    ["hdmi_a", 25.0], // assumed — cables.md:121 "unknown — physically measure" (M6)
    ["bnc",    25.0], // assumed — cables.md has no BNC plug-body length at all (M6)
    ["rj45",   21.5], // cables.md:119, verified (TIA-568.2-D max plug length)
    ["usb_a",  12.0], // cables.md:125, verified
    ["usb_b",  12.0], // assumed equal to usb_a — no USB-B-specific figure sourced
    ["blank",  0],    // defensive: DBA-BL-B (kind "blank") now carries a real hole (rev 8, D-14
                       // part 4), so mcc_plug_axial() can resolve "DBA-BL-B" -> "blank" via
                       // mcc_panel_kind() same as any other part; without this row that lookup
                       // would assert out. Nothing plugs into a blank, so 0.
];

// Function: mcc_plug_axial()
// Usage:
//   axial = mcc_plug_axial(kind_or_part);
// Description:
//   AXIAL (straight-plug) clearance to budget for a port, mm — the T1-18(c) end-zone-vs-fan-bay
//   assert's own input (shell.scad), tracked separately from mcc_bend_envelope()'s LATERAL figure
//   per architecture.md:295-297. Accepts either a port `kind` (a direct key of MCC_PLUG_AXIAL,
//   e.g. "bnc") or a MCC_PANEL_PARTS part number (e.g. "NBB75DFGB", resolved to its `kind` via
//   mcc_panel_kind() and looked up from there) — so a caller holding either a port's `kind` or its
//   `panel` value can use this function without first normalising which one it has.
// Arguments:
//   kind_or_part = a port kind string, or a MCC_PANEL_PARTS part number.
function mcc_plug_axial(kind_or_part) =
    let(ind = search([kind_or_part], MCC_PLUG_AXIAL)[0])
    (ind != []) ? MCC_PLUG_AXIAL[ind][1] :
    let(
        kind = mcc_panel_kind(kind_or_part), // treat the argument as a panel part number instead
        ind2 = search([kind], MCC_PLUG_AXIAL)[0]
    )
    assert(ind2 != [], str("mcc: unknown plug-axial kind/part \"", kind_or_part, "\" in mcc_plug_axial()"))
    MCC_PLUG_AXIAL[ind2][1];

MCC_CRADLE_RIB_T = 3.0;    // locating-rib thickness, mm. layout-patch-wall.md §7 cradle table
                            // "Locating ribs | 3.0 mm thick x 9.0 mm tall".
MCC_CRADLE_RIB_H = 9.0;    // locating-rib height, mm. Same table; <= 3x thickness rule
                            // (fdm-rugged-enclosure-guidelines.md:65-70) satisfied (9 <= 9).
// (MCC_CRADLE_FLOOR_PAD_T / _MIN retired with the floor-pad island, D37 — the compliant pad sits
// on the side-bolt boss face, architecture.md §11 R8.)

// Ribbed cradle deck lattice (issue #29, rev 9 D-17 -- replaces the solid deck slab). The ladder
// ribs reuse MCC_CRADLE_RIB_T above, NOT a derived per-family thickness -- architecture.md §13 D22
// scopes the <=3x-height:thickness rule to cantilevered fins, not these floor-standing,
// cross-braced webs, so no second rib-thickness constant is introduced here.
MCC_CRADLE_DECK_GRID_PITCH = 22.0; // target interior ladder-rib pitch, mm -- GitHub issue #29 ("3 mm
                                     // ribs on a 20-25 mm grid"), mid-point of that range. Achieved
                                     // pitch varies per SKU (rounds to a whole number of bays) --
                                     // bounded by the two constants below (T1-39).
MCC_CRADLE_DECK_GRID_PITCH_MIN = 16.0; // T1-39 assert lower bound on achieved grid pitch, mm.
                                         // layout-patch-wall.md §9 T1-39.
MCC_CRADLE_DECK_GRID_PITCH_MAX = 32.0; // T1-39 assert upper bound on achieved grid pitch, mm.
                                         // layout-patch-wall.md §9 T1-39.

// Tongue-and-groove production dimensions (D-07: tongue on the base, groove in the lid). REV-5
// VALUES (layout-patch-wall.md §15 ruling 4 / T1-33) — an earlier plan draft's 3.0/4.0 is
// geometrically impossible: MCC_LID_T is a fixed 3.0 mm (H=51.0 is a fixed user decision), so a
// 4 mm-deep groove cuts clean through the lid, and a *centred* 3.0 mm-wide tongue does not fit a
// 3.0 mm wall either (0.8+0.25+w+0.25+0.8 <= 3.0 -> w <= 0.9). Ruling: an OFFSET/SHIPLAP tongue
// flush with the wall's INNER face, sized so it fits inside the lid with >= 1.0 mm of lid material
// left above the groove.
MCC_TG_W = 1.6; // tongue/groove nominal width, mm. layout-patch-wall.md §15 ruling 4.
MCC_TG_H = 2.0; // tongue/groove depth, mm. Same ruling — leaves MCC_LID_T - MCC_TG_H = 1.0 mm of
                 // lid material above the groove (T1-33).

MCC_LID_CLEAR = 2.0; // minimum plenum between the cradle deck top + device height and the lid
                      // underside, mm. layout-patch-wall.md §15 ruling 3 (ACCEPTED) — mirrors this
                      // repo's other small-clearance constants (MCC_GAP_DEV, MCC_SIDE_BOLT_PAD_T).
                      // Minimum only, not the design plenum (10.85 mm on this SKU) — the plenum
                      // must never be sealed (architecture.md §12 Q10).

// Vents (layout-patch-wall.md §5). Slot/web widths are contract-cited (assumed there).
MCC_VENT_SLOT_W = 1.2; // vertical vent-slot width, mm. assumed — layout-patch-wall.md §5, nearest
                        // verified analogue 1.0 mm lattice gap (fdm-rugged-enclosure-guidelines.md:197).
MCC_VENT_WEB_W = 1.6;  // web between vent slots, mm. assumed — layout-patch-wall.md §5.
MCC_VENT_INTAKE_BAND_H = 18.0; // intake vent band height (Z), mm. REV-5 VALUE (layout-patch-wall.md
                                 // §15 ruling 5) — 12 and 15 mm both fail T1-30 once the T1-23/T1-23b
                                 // keep-outs are subtracted from the gross free area; 18.0 clears it.
MCC_VENT_EXHAUST_Z = [32, 44]; // far-wall exhaust vent band Z range (case coords), mm.
                                 // layout-patch-wall.md §5 table.
MCC_FAN_APERTURE_D = 38.0; // +X end-wall fan aperture diameter, mm. DERIVED (informational —
                            // H_int is fixed at 45.0 mm on every current SKU since MCC_PLATE_H and
                            // MCC_PANEL_BAND never vary): H_int - 2*MCC_WALL = 45 - 6 = 39, capped
                            // to 38 so >= 3.5 mm of wall remains above/below the aperture per
                            // layout-patch-wall.md §5. assumed.

// Floor keep-out geometry (layout-patch-wall.md §7.1 floor table, rev-5 corrections).
MCC_STRAP_SLOT = [25, 5];         // strap-slot [length, width], mm. assumed.
MCC_FLOOR_FEATURE_MIN_SEP = 15.0; // minimum centre-to-centre separation between any two floor
                                    // features, mm (or r1+r2+2.0 where larger) — layout-patch-wall.md
                                    // §7.1.
MCC_FLOOR_FEATURE_EDGE_MIN = 2.0; // minimum edge-to-edge clearance between a floor feature and a
                                    // disc-shaped keep-out it is not concentric with, mm — the
                                    // "2.0 mm because disc-vs-rect" margin named per rev 9 R2
                                    // (layout-patch-wall.md §17.2), replacing an ad-hoc inline 2.0.

// Ghost-rendering visibility flag (architecture.md:304 "gated behind MCC_SHOW_GHOST (default false)").
// Belt 2 of the two-belt ghost-exclusion rule; belt 1 is the `%` modifier used wherever ghost
// geometry is drawn (lib/mcc/ghost.scad, lib/mcc/neutrik.scad's *_envelope() keep-out boxes).
MCC_SHOW_GHOST = false;

// -----------------------------------------------------------------------------------------
// Section: Mount rail (dovetail + gravity lock) — issue #25, replaces VESA (D-15, rev 9; lock D48)
// lib/mcc/rail.scad owns the geometry; this section owns only the shared cross-section constants
// both mcc_rail_male() (bracket, #26/#27) and mcc_rail_female_cut() (case floor, mounts.scad) read,
// per the D6 precedent (one file, both mating halves, so the profiles can never drift apart).
// docs/plans/2026-09-09-mount-rail-and-brackets.md §1.1, architect verdict (`architecture.md` rev 9 /
// `layout-patch-wall.md` §17.2) for the two blocking value corrections (R1/R2, called out below).
// -----------------------------------------------------------------------------------------

MCC_RAIL_DEPTH = 4.0; // dovetail groove depth (case-floor side), mm. issue #25's own cap ("depth
                       // <= 4 mm so it does not raise the case much"). assumed.

// R1 (blocking, layout-patch-wall.md §17.2): MCC_RAIL_DEPTH + MCC_FLOOR_T, NOT +2.0. At the plan's
// original +2.0 (=6.0) the 4 mm groove leaves only 2.0 mm of ASA over it on the one surface that
// carries the whole case when it is bracket-mounted — below the uniform MCC_WALL/MCC_FLOOR_T (3.0)
// shell spec. Asserted as T1-38 in lib/mcc/rail.scad (>= MCC_FLOOR_T of residual floor over the
// groove, not merely "> MCC_RAIL_DEPTH").
MCC_RAIL_SILL_H = MCC_RAIL_DEPTH + MCC_FLOOR_T; // = 7.0. Local floor thickening the groove is cut
                                                  // into: MCC_RAIL_DEPTH (the groove) + MCC_FLOOR_T
                                                  // (the residual floor T1-38 requires above it).

MCC_RAIL_FLANK_ANGLE = 60; // dovetail flank angle from the floor/horizontal plane, deg. issue #25's
                            // own "~60 deg" instruction; no repo-sourced dovetail-angle figure
                            // exists. assumed.
MCC_RAIL_ROOT_W = 65.0;    // dovetail root width (wide end: deepest into the case floor / top of the
                            // bracket's male rail), mm. USER DECISION 2026-09-28 (architecture.md
                            // §13 D44): "much wider, intermediate, root 60-70 mm"; 65 validated at the
                            // gate (max ~68.9 at MCC_RAIL_Y below before the sill meets the side-bolt
                            // web). PRIMARY since D44 -- MOUTH_W is derived from it (was the reverse).
MCC_RAIL_MOUTH_W = MCC_RAIL_ROOT_W - 2 * MCC_RAIL_DEPTH / tan(MCC_RAIL_FLANK_ANGLE);
                            // dovetail mouth width (narrow end: the case's exterior floor face / the
                            // bracket plate top), mm. DERIVED = 65.0 - 4.6188 = 60.3812.
MCC_RAIL_SILL_SIDE_W = MCC_WALL; // side wall of the floor sill beside the groove root, mm
                            // (2026-09-27, architecture.md D30). The sill used to be exactly
                            // MCC_RAIL_ROOT_W wide, i.e. its side walls ran out to a 0 mm knife
                            // edge at the groove root (the groove is deeper than MCC_FLOOR_T), so
                            // the 150 mm roof over the groove hung only on the cradle-rib crossings
                            // (Bambu Studio: "floating cantilever" on every base). A full MCC_WALL
                            // each side lets the roof bridge flank-to-flank over its whole length.
MCC_RAIL_LEN = 150.0;      // rail/groove length along its slide axis (case-local X), mm. assumed —
                            // fixed across every SKU (one interface, every case; layout-patch-wall.md
                            // §17.2 R4/§1.4). Fits the smallest family (compact, L=194.9) with
                            // >= 19 mm margin per end past the end walls' inner faces.

// Rail Y (D44, 2026-09-28 -- supersedes rev 9's R2 value -20.0). As close to the device's own centre
// of mass (y_dev_c = -30.825 on every HDMI-ended SKU, ~0.5 mm less negative on the BNC-ended ones) as
// the 65 mm root allows. Binding neighbour: the side-bolt support web's floor footprint. On the
// tightest SKU (W = 158.80) the sill's -Y edge (MCC_RAIL_Y - MCC_RAIL_ROOT_W/2 - MCC_RAIL_SILL_SIDE_W =
// -59.0) stays 3.4 mm clear of the web top (-62.4), and the groove's "mount_rail" keep-out row clears
// it by 4.4 mm beyond MCC_FLOOR_FEATURE_EDGE_MIN (D16). Negative as before (R24): the rail sits under
// the device, so the case's mass stays on the rail band when the patch wall hangs down. The case-insert
// and Fishtail reservations that pinned the rail to |y| >= 19.31 are gone (D44).
MCC_RAIL_Y = -23.5;

// Rail lock -- a GRAVITY lock (user decision 2026-09-28, architecture.md §13 D48; it replaces the D34
// snap latch, which is removed). A rigid bump on the male rail's -Y flank, near its +X end, drops into
// a pocket in the case groove's -Y flank at full insertion. Every bracket places the rail with
// rotate([0,0,180]) and a mounted case always hangs patch-wall down (fixed decision, D49), so the -Y
// flank is the upper one: the case's weight rests on it (about 1.15 x the weight, normal to the 60 deg
// flank) and holds the bump in its pocket. Nothing flexes: sliding on, the case rides over the bump
// inside the dovetail's own flank play (2 x MCC_RAIL_CLR_HORIZ = 1.155 mm horizontal, T1-64); the exit
// face is square to the slide axis, so an axial pull cannot cam a hanging case out. Release: lift the
// case about 1 mm (it stops on the lower flank) and slide it back off. Reference: the external
// specialist's DP48 plate -- 0.8 mm strips riding inside 0.97 mm of dovetail play (analysis F2).
MCC_RAIL_LOCK_ENGAGE = 0.70;      // bump protrusion beyond the flank, horizontal (Y), mm (0.61 normal to
                                   // the flank). assumed: the DP48 uses 82 % of its lift play, this is
                                   // 61 % of ours, leaving 0.45 mm for FDM tolerance. Tuned on the
                                   // rail-lock coupon's e-ladder (M15).
MCC_RAIL_LOCK_PLAY_MARGIN = 0.2;  // horizontal flank play that must remain while the bump rides the
                                   // groove flank, mm (T1-64). assumed.
MCC_RAIL_LOCK_RAMP_IN = 30;       // entry ramp (the bump's -X side) to the slide axis, deg. assumed (the
                                   // D34 nub's entry angle).
MCC_RAIL_LOCK_RAMP_OUT = 90;      // exit face (the bump's +X side) to the slide axis, deg. 90 = square:
                                   // self-locking against an axial pull at any friction (T1-65). assumed.
MCC_RAIL_LOCK_FLAT = 1.0;         // bump flat top length along X, mm. assumed.
MCC_RAIL_LOCK_END_OFFSET = 3.0;   // male's +X (trailing) end to the bump's exit face, mm. assumed -- the
                                   // DP48 strips sit 3.0-5.0 mm from their trailing end (F2). rail.scad
                                   // derives the position from its own `len`, so the 60 mm coupon works.
MCC_RAIL_LEADIN = 1.0;            // 45-deg lead-in where the groove leaves the case's +X wall: flanks and
                                   // mouth flare by this much per side (horizontal) over the last this-many
                                   // mm; the roof stays. The DP48's 1.0 x 45 deg entry chamfer (F2). assumed.
MCC_RAIL_PASSAGE_ROOF_MIN = 1.2; // minimum roof over the groove where it runs out through the case's
                               // +X end zone (D34). There the passage only guides the male during
                               // insertion — at full mate nothing loads it — so the T1-38 residual
                               // (MCC_FLOOR_T) does not apply; the fan-bay reservation above caps
                               // the passage sill at fan_bay_z[0]. assumed.

// End stop: the CLOSED (-X) end of the case groove itself (D34). The male rail has no end stop of its
// own -- its old flange sat inside the case footprint and would have hit the case floor. D34 retired
// it; D52 removed its zero-valued MCC_RAIL_END_STOP_L/H constants. Any future male-side feature is a
// rail.scad change that mcc_rail_male_keepout() reports (D50), never a constant brackets add by hand.

// Rail clearances (D44, user decision 2026-09-28, from the external specialist's review): at least
// 0.5 mm on EVERY non-bearing surface of the joint. The only designed bearing face is the case's flat
// exterior floor on the bracket plate (the male has no MCC_FLOOR_T pedestal any more); on a vertical,
// TV-mounted bracket the upper flank (rail-local −Y) also bears (architecture.md R41). These replace the
// rev-9 rule "reuse MCC_CLR_SLIDE for the rail": 0.3 mm horizontal at a 60 deg flank is only 0.26 mm
// normal to it -- below the requirement. MCC_CLR_SLIDE stays for every other sliding fit.
MCC_RAIL_MATE_CLR = 0.5;    // minimum clearance on every non-bearing rail face, mm. User decision (D44).
MCC_RAIL_CLR_HORIZ = MCC_RAIL_MATE_CLR / sin(MCC_RAIL_FLANK_ANGLE); // = 0.5774. Per-side horizontal
                            // offset of the female groove and lock pocket from the male profile that
                            // gives MCC_RAIL_MATE_CLR normal to a MCC_RAIL_FLANK_ANGLE flank (T1-62).
MCC_RAIL_ROOF_CLR = MCC_RAIL_MATE_CLR; // = 0.5. Gap between the male's flat top (and the lock bump's) and
                            // the groove roof, mm. Its own constant on purpose: the roof is a ~66 mm
                            // bridge in the base's print pose (architecture.md R40) -- if the rail-lock
                            // coupon (M15) shows it sags into this gap, raise THIS; never narrow the rail.
MCC_RAIL_MALE_H = MCC_RAIL_DEPTH - MCC_RAIL_ROOF_CLR; // = 3.5. The male taper's built height above the
                            // bracket plate (no pedestal since D44).

// -----------------------------------------------------------------------------------------
// Section: Mounting brackets (models/brackets/*.scad). Bracket-own geometry stays inside each bracket
// file; only cross-cutting rules live here (§17.2's R4/R5/D22: the rib rule is stated once, generic,
// not duplicated per bracket). The VESA 100/200 sandwich plate that opened this section
// (tv-bracket.scad, #26) was retired in rev 16, with MCC_BRACKET_PLATE_T (architecture.md D47).
// -----------------------------------------------------------------------------------------

MCC_RIB_HEIGHT_RATIO_MAX = 3.0; // stiffening-rib height <= this x rib thickness, unitless.
                                 // fdm-rugged-enclosure-guidelines.md:65-70 "Rib height ... about
                                 // 3x rib thickness as a practical limit". First codified here
                                 // (D22, architecture.md §13/§17.2) — bracket ribs (the arch arm's
                                 // edge ribs) are exactly the standing stiffening fin this rule targets;
                                 // the cradle-deck lattice (#29) explicitly does NOT use it
                                 // (layout-patch-wall.md §17.3 R6 — those ribs are cross-braced webs,
                                 // a different structural class).

// -----------------------------------------------------------------------------------------
// Section: Fans
// knowledge/components/fans.md.
// -----------------------------------------------------------------------------------------

// [name, [["frame",[w,h,d]], ["pitch",p], ["hole_d",d]]]
// NF-A4x10: knowledge/components/fans.md:15-18 "Frame size: 40 x 40 x 10 mm" / "Mounting hole spacing
//           (c-to-c): 32 x 32 mm" / "Mounting hole diameter: unknown" -> hole_d assumed 4.3 mm.
// NF-A6x25: knowledge/components/fans.md:42-45 "Frame size: 60 x 60 x 25 mm" / "Mounting hole spacing
//           (c-to-c): 50 x 50 mm" / "Mounting hole diameter: unknown" -> hole_d assumed 4.3 mm.
MCC_FANS = [
    ["NF-A4x10", [["frame", [40, 40, 10]], ["pitch", 32], ["hole_d", 4.3]]],
    ["NF-A6x25", [["frame", [60, 60, 25]], ["pitch", 50], ["hole_d", 4.3]]],
];

// Name of the fan fitted by default, key into MCC_FANS above. architecture.md §10 D-18 / rev 11
// (#32) -- pulled out so layout.scad and vents.scad/shell.scad never repeat the "NF-A4x10" string
// literal (architecture.md §3 "no magic numbers").
MCC_FAN_DEFAULT = "NF-A4x10";

// Intake clearance beyond the fan's own frame depth, mm. assumed -- generic unobstructed-intake
// allowance; no sourced figure in knowledge/components/fans.md (frame/pitch/hole_d only). Single
// source of truth for the figure previously duplicated as a bare literal `5` at fan.scad's
// mcc_fan_envelope() and inside shell.scad's T1-18(c) block. architecture.md §13 D23, issue #36.
MCC_FAN_INTAKE_CLR = 5.0;

// Minimum clearance between the reserved fan bay (frame + MCC_FAN_INTAKE_CLR) and any OTHER
// feature: the (+X,-Y) corner lid-fastener boss/gusset on -Y, the connector bay's plug envelope
// on +Y (T1-46a/b, layout-patch-wall.md §9). assumed -- this repo's recurring 2 mm keep-out web
// (knowledge/design/fdm-rugged-enclosure-guidelines.md:127), the same 2.0 that gives
// MCC_SIDE_BOLT_KEEPOUT_D its `+ 2 * 2.0` and MCC_APERTURE_LIP_WEB_MIN its value (both above).
// Deliberately NOT applied to the bay's Z bounds (T1-46c/d): those bound the bay against the
// interior CAVITY surface, and a reserved volume may touch the shell it bolts to. Rule
// (architecture.md §6 rev 12): clearance is required against another FEATURE, never against the
// cavity boundary.
MCC_FAN_BAY_CLR = 2.0;

// Function: mcc_fan_spec()
// Usage:
//   spec = mcc_fan_spec(name);
// Description:
//   Looks up a fan record (frame/pitch/hole_d) from MCC_FANS above by name, e.g. "NF-A4x10" or
//   "NF-A6x25". MOVED HERE from lib/mcc/fan.scad (L1), rev 11, #32, architect verdict B7: it is a
//   pure function over an L0 table (architecture.md §3 bans a *module* in constants.scad, not a
//   function), and layout.scad — which may not `use` an L1 geometry provider — needs it to compute
//   the fan-frame clearance for the fan-switch band solve legally, instead of open-coding
//   MCC_FANS[search(["NF-A4x10"], MCC_FANS)[0]][1] at L1. No geometry change; no golden change.
function mcc_fan_spec(name) =
    let(ind = search([name], MCC_FANS)[0])
    assert(ind != [], str("mcc: unknown fan \"", name, "\""))
    MCC_FANS[ind][1];

// Minimum total intake vent free area, as a multiple of the fan aperture's own circular area
// (pi/4 * fan_aperture_d^2), when a fan bay is reserved. assumed —
// knowledge/design/thermal-guidelines.md:104-109 gives only the qualitative rule "vent free area
// comfortably larger than the fan's inlet/outlet duct area"; 1.0 (parity) is the smallest
// reasonable reading of "comfortably larger". Used by T1-30 (layout-patch-wall.md §9/§11) — at the
// rev-3 far-wall intake band geometry the current design point is ~990 mm² vs. the fan aperture's
// ~1134 mm², i.e. this assert currently FAILS; the fix is a taller/leakier intake band in the
// not-yet-written vents.scad, not a deeper far-wall duct (R20 — D-13 already made the duct one of
// several parallel paths, not the bottleneck).
MCC_VENT_AREA_RATIO = 1.0;

// Lid vents (GitHub issue #24) — additive top-exhaust field, centred over the device's own plenum,
// separate from the far-wall/±X-end-wall chimney slots above. Same physical concern (chimney vent
// sizing), applied to a new face — kept in this section rather than a new one for that reason. See
// docs/plans/2026-09-09-lid-vents.md §1-2 for the full thermal/geometry reasoning and
// layout-patch-wall.md §17.4 (R9/R10) for the architect-required changes (use <ports.scad> in
// vents.scad; named constants here rather than the plan's inline 1.0/1.6 literals).
MCC_LID_VENT_SLOT_W  = 2.0;  // lid vent slot width in X, mm. assumed -- ticket's own example figure.
MCC_LID_VENT_SLOT_L  = 20.0; // lid vent slot length in Y, mm. assumed -- ticket's own example figure.
MCC_LID_VENT_EDGE_MIN = 1.0; // minimum clearance from the lid vent field to the T&G groove band /
                               // patch-wall MCC_T_PATCH stack, mm. Named per layout-patch-wall.md
                               // §9 T1-37 / §17.4 R10 (replaces the plan's inline "1.0" literal).
                               // assumed -- same minimum-edge-material class as
                               // MCC_APERTURE_LIP_WEB_MIN.
MCC_LID_VENT_WEB_MIN = 1.6;  // minimum web between adjacent lid-vent slots, mm. Named per
                              // layout-patch-wall.md §17.4 R10 (replaces the plan's bare
                              // "assert(... >= 1.6)" literal) -- same figure/rationale as
                              // MCC_VENT_WEB_W, kept as its own named constant (not a reuse) so a
                              // future change to the wall-vent web does not silently move this one.
MCC_LID_VENT_WEB_W   = MCC_LID_VENT_WEB_MIN; // actual web used between lid-vent slots, mm. Equal to
                              // the minimum today; kept as a separate symbol from
                              // MCC_LID_VENT_WEB_MIN (the assert bound) so the two can diverge later
                              // without renaming the bound.
MCC_LID_VENT_ROW_GAP    = 6.0; // solid Y gap between the 2 slot rows, mm. assumed -- reserves room
                                 // for an optional future underside stiffening rib (plan §2.4).
MCC_LID_VENT_ROWS       = 2;    // number of slot rows. assumed -- plan §2.1 PLAN-ASSUMPTION C
                                  // (ratified, layout-patch-wall.md §17.5).
MCC_LID_VENT_END_MARGIN = 5.0;  // inset from x_dev_lo/x_dev_hi to the field's own X bounds, mm. assumed.
MCC_LID_VENT_FASTENER_KEEPOUT_R = 10.0; // defensive keep-out radius around every lid_fastener_pos, mm.
                                          // assumed -- counterbore radius 4.0 + >=2mm edge material
                                          // (fdm-rugged-enclosure-guidelines.md §8), rounded up.
MCC_LID_VENT_AREA_RATIO = 1.0;  // minimum net lid-vent free area, as a multiple of the fan aperture's
                                  // own circular area (pi/4 * MCC_FAN_APERTURE_D^2) -- same heuristic
                                  // as MCC_VENT_AREA_RATIO/T1-30, applied to the new top exhaust path.
                                  // assumed -- thermal-guidelines.md:104-109.

// -----------------------------------------------------------------------------------------
// Section: Fan switch
// knowledge/components/switches.md. Rev 11, #32, architecture.md §10 D-18 / layout-patch-wall.md
// §5+§18. A table + a named default, mirroring MCC_FANS/MCC_SPLITTERS above (architect verdict
// B5) -- the plan's original single MCC_FAN_SWITCH struct is rejected for the same reason a
// hard-coded MCC_FAN struct would be: swapping the part must be a data edit, never a geometry
// edit. Three candidates are recorded in knowledge/components/switches.md; only MTS-101 is placed.
// -----------------------------------------------------------------------------------------

// [name, [["hole_d",d],["nut_d",d],["keepout_d",d],["pad_d",d],["body_d",d],["depth",d],
//         ["actuator_proud_h",h],["panel_t_min",t],["panel_t_max",t],["clr",c],["confidence",c]]]
//
// MTS-101 (SPST ON-OFF mini toggle -- the SPST sibling of the ticket's own researched MTS-102,
// same bushing/cutout/depth mechanical family; knowledge/components/switches.md).
// hole_d/depth/actuator_proud_h/panel_t_min/panel_t_max: assumed -- generic 1/4-40NS mini-toggle
// bushing convention (Finglai/LCSC MTS-102 datasheet family), no legible numeric callout reached
// this pass. BLOCKING measurement M17 (architecture.md §11 R29/§12) buys one and measures all
// five before the first full-size print.
// nut_d: assumed 8.0 mm across-flats (generic 1/4-40NS hex nut), circumscribed via the standard
// hex AF-to-circumscribed factor 1/cos(30 deg) -- architect verdict B5 ("a 1/4-40 bushing nut is
// ~8 mm across flats -> ~9.24 mm circumscribed").
// keepout_d: nut_d + 2*MCC_CLR_SLIDE -- the single generic panel-mount keep-out figure
// mcc_switch_keepout() (switch.scad) exposes to callers outside the two-band solve below (e.g.
// vents.scad, B8) -- NOT the same figure as pad_d/body_d, which are two DIFFERENT depths' worth of
// footprint, both wider than keepout_d because they also carry the T1-44 lip margin.
// pad_d/body_d: architect-derived (layout-patch-wall.md §5/§18, D-18/T1-43) -- a recessed toggle
// needs a nut pocket of ~10 mm (nut_d rounded up), so body_d = 10.0 (the plain nut-pocket
// footprint, used against the deeper corner-boss obstruction) and pad_d = body_d +
// 2*MCC_APERTURE_LIP_WEB_MIN = 10 + 4 = 14.0 (the wider near-wall footprint, carrying this repo's
// own 2.0 mm minimum-lip-material precedent, used against the fan reservation and the shallower
// gusset-strip obstruction).
// clr: 1.5 mm, NOT the plan's original 3.0 mm (which was "chosen, mirroring MCC_GAP_DEV/
// MCC_SIDE_BOLT_PAD_T", but made every SKU's T1-43 band infeasible under the corrected two-band
// formula). 1.5 is chosen instead so the T1-43 band solve reproduces the architect's own worked
// verdict figures exactly: plus family switch_y in [-62.535,-59.325] (pro-convert-hdmi-plus/
// pro-convert-for-ndi-to-hdmi-4k, a 3.21 mm window) and compact infeasible by 0.04 mm
// (layout-patch-wall.md §18.2) -- confirmed by hand against the raw band widths there
// (pad 17.60/20.85, body 14.96/18.21 mm, compact/plus).
MCC_SWITCHES = [
    ["MTS-101", [
        ["hole_d",           6.4],
        ["nut_d",            8.0 / cos(30)],
        ["keepout_d",        8.0 / cos(30) + 2 * MCC_CLR_SLIDE],
        ["pad_d",            14.0],
        ["body_d",           10.0],
        ["depth",            13.0],
        ["actuator_proud_h", 10.0],
        ["panel_t_min",       0.8],
        ["panel_t_max",       3.2],
        ["clr",               1.5],
        ["confidence",   "assumed"],
    ]],
];

// Name of the switch fitted by default, key into MCC_SWITCHES above. D-18 (architecture.md §10).
MCC_SWITCH_DEFAULT = "MTS-101";

// Function: mcc_switch_spec()
// Usage:
//   spec = mcc_switch_spec(name);
// Description:
//   Looks up a switch record from MCC_SWITCHES above by name, e.g. "MTS-101" -- mirrors
//   mcc_fan_spec()'s own pattern (both pure lookups over an L0 table), so callers never open-code
//   MCC_SWITCHES[search([name], MCC_SWITCHES)[0]][1] (architecture.md §3, the same rule verdict B7
//   applies to MCC_FANS).
function mcc_switch_spec(name) =
    let(ind = search([name], MCC_SWITCHES)[0])
    assert(ind != [], str("mcc: unknown switch \"", name, "\""))
    MCC_SWITCHES[ind][1];

// Minimum flush clearance below the wall's outer face for the switch actuator's tip, mm -- the
// T1-25 analogue for a switch (architecture.md R29): recess_t = actuator_proud_h + this. assumed,
// mirrors T1-25's own 1.0 mm margin (fasteners.scad mcc_captive_side_bolt_boss() head-recess rule,
// "head_rec_h >= head_h + 1.0").
MCC_SWITCH_FLUSH_CLR = 1.0;

// Stop-and-report guard (architecture.md R29 / T1-44(e)): if a measured actuator (M17) forces a
// recess deeper than this, the part is wrong -- do not answer it by shaving the recess. assumed,
// chosen so today's ~11 mm computed well (10.0 mm proud + 1.0 mm flush clearance) passes with only
// ~1 mm of margin, matching R29's own "near the depth where a fingertip can no longer reach" note.
MCC_SWITCH_WELL_DEPTH_MAX = 12.0;

// -----------------------------------------------------------------------------------------
// Section: PoE splitter envelope
// knowledge/components/poe-splitters.md.
// -----------------------------------------------------------------------------------------

// Default splitter envelope: "dongle-class" 802.3af/at->5V USB splitter (e.g. UCTRONICS
// U6114/U6115, knowledge/components/poe-splitters.md rank-2 recommendation). Its own dimensions
// are explicitly unpublished (poe-splitters.md:129-136,211-215 "physical dimensions ... not found
// on the manufacturer's product pages") — R11 (architecture.md §11) blocks the GAT-USBC placeholder
// from fitting the patch-wall topology at all, so this smaller "dongle class" default (75x40x20,
// user decision 2026-09-07) is what shell.scad reserves by default until the depth-mockup /
// physical-measurement follow-up replaces it with a measured value.
// PoE Texas GAT-USBC kept as a named, non-default alternative (larger, dimensioned, but does not
// fit the patch-wall topology per R11 — architecture.md:529-542).
// size:         knowledge/components/poe-splitters.md:58 "114 x 51 x 25" (L x W x H, mm)
// weight_g:     knowledge/components/poe-splitters.md:58 "85 g"
// cable_allow:  knowledge/components/poe-splitters.md §"Space envelope" / the brief's own instruction
//               "plus 20 mm cable allowance on each RJ45 end" — 20 mm, per-end, applied at both RJ45 ends.
MCC_SPLITTERS = [
    // weight_g intentionally omitted — genuinely unknown, not just unmeasured (no weight figure
    // exists anywhere in poe-splitters.md for a dongle-class part); struct_val() returns undef for
    // a missing key, same as an explicit undef would, without implying a datum that doesn't exist.
    ["DONGLE-75x40x20", [["size", [75, 40, 20]], ["cable_allow", 20], ["confidence", "assumed"]]],
                 // dongle-class 802.3af/at->5 V USB splitter, e.g. UCTRONICS U6114/U6115 —
                 // dimensions unpublished (knowledge/components/poe-splitters.md), measure before
                 // the shell is finalised
    ["GAT-USBC", [["size", [114, 51, 25]], ["weight_g", 85], ["cable_allow", 20]]],
                 // does not fit the single-patch-wall layout (architecture.md §11 R11)
];

// Name of the splitter reserved by default, key into MCC_SPLITTERS above. D-10/D-12
// (layout-patch-wall.md §5/§11) — named as its own constant (rather than a literal repeated inside
// poe_splitter.scad's module defaults) because MCC_END_ZONE_NEG_EXTRA_SPLITTER below, and the −X
// end-zone term it feeds (ez_neg, D-12), now depend on which part is the default.
MCC_SPLITTER_DEFAULT = "DONGLE-75x40x20";

// Extra −X end-zone allowance the reserved splitter bay ADDS to the device's own cable allowance
// (D-12, architecture.md §6 reservation rule — the two SUM, they are not `max`ed: the device's own
// −X plugs need their allowance whether or not a splitter is fitted). DERIVED from
// MCC_SPLITTERS[MCC_SPLITTER_DEFAULT].size[2] — the splitter's on-edge X extent
// (layout-patch-wall.md §5 "20 mm in X, 75 mm in Y, 40 mm in Z — the only orientation of a
// 75x40x20 slab that fits a 45 mm interior at all") — so a future measured part (M3) propagates
// straight into ez_neg, and therefore L, without hard-typing 20. Evaluates to 20.0 for the
// DONGLE-75x40x20 default. layout-patch-wall.md §4/§11, `assumed` (inherits the splitter's own
// unmeasured size).
MCC_END_ZONE_NEG_EXTRA_SPLITTER =
    struct_val(MCC_SPLITTERS[search([MCC_SPLITTER_DEFAULT], MCC_SPLITTERS)[0]][1], "size")[2];

// -----------------------------------------------------------------------------------------
// Section: Connector panel-part table
// One row per physical panel connector "part number" used by lib/mcc/panel.scad's dispatcher
// and by every device data file's ["panel", <part>] field (architecture.md §7).
//
// Fields per part (all keyed struct-style):
//   hole_d       mm, the connector's own minimum/nominal round-cutout diameter (BEFORE MCC_HOLE_COMP)
//   depth        mm, connector body depth behind the panel (flange face to rearmost point)
//   max_panel_t  mm, maximum panel thickness the connector supports
//   plug_len     mm, axial clearance to budget for the mating plug (see mcc_bay_depth())
//   bend         mm, LATERAL keep-out for cable bend allowance, tracked separately from axial
//                depth per architecture.md:295-297 ("Bend envelope is a lateral keep-out ...
//                for BNC it is the dominant term")
//   kind         connector-kind enum string, matches lib/mcc/ports.scad "kind" values
//   confidence   one of MCC_CONFIDENCE_ORDER (see lib/mcc/ports.scad)
//
// Sources per row:
//   NE8FDP-B   (etherCON, RJ45):  hole_d knowledge/neutrik/d-series-cutout.md:36 "≥ 24.0 mm ...
//              (etherCON NE8FDP, XLR NC3xD)"; depth knowledge/neutrik/placement-and-depth.md:12
//              "NE8FDP | 34.55 mm | front-mount"; max_panel_t knowledge/neutrik/d-series-cutout.md:89
//              "NE8FDP (etherCON feedthrough) | max. 4 mm"; plug_len — brief's explicit instruction
//              "etherCON/RJ45 25" (confidence: assumed, cross-checked against
//              knowledge/neutrik/placement-and-depth.md:68 "~20-25 mm"); bend — assumed lateral
//              service-loop allowance for a semi-rigid RJ45/etherCON boot, smaller than the axial
//              plug_len since Cat5e/6 patch cord is not bend-radius limited at this scale
//              (knowledge/components/cables.md:119 gives no bend-radius figure for RJ45).
//              TODO(teamlead): "bend" for RJ45 has no sourced figure at all; 10 mm is a smallest-
//              reasonable-choice placeholder, confidence assumed, to be replaced by the
//              depth-mockup coupon (architecture.md §11 R2).
//   NAHDMI-W-B (HDMI):            hole_d knowledge/neutrik/d-series-cutout.md:37 "≥ 23.6 mm (HDMI
//              NAHDMI-W ...)"; depth knowledge/neutrik/placement-and-depth.md:14 "NAHDMI-W | 40.65 mm
//              | front-mount"; max_panel_t knowledge/neutrik/d-series-cutout.md:90 "NAHDMI-W ... max.
//              2 mm"; plug_len — brief's explicit instruction "HDMI 35" (confidence: assumed,
//              cross-checked against knowledge/neutrik/placement-and-depth.md:69 "~25-35 mm"); bend —
//              assumed, HDMI cable is stiff (knowledge/components/cables.md:121-122 confirms only
//              cross-section, not bend radius) so a wider lateral allowance than RJ45/USB is used.
//              TODO(teamlead): "bend" for HDMI has no sourced figure; 15 mm is a smallest-reasonable-
//              choice placeholder, confidence assumed.
//   NAUSB-W-B  (USB A/B):         hole_d knowledge/neutrik/d-series-cutout.md:37 "≥ 23.6 mm (...
//              USB NAUSB-W ...)"; depth knowledge/neutrik/placement-and-depth.md:16 "NAUSB-W | 40.55 mm
//              | front-mount only"; max_panel_t — knowledge/neutrik/d-series-cutout.md:93 lists this
//              as an open question ("not stated on datasheet ... treat as ≤ 3 mm pending drawing
//              confirmation"); per the brief's own instruction, treated as 2.0 mm here (the same safe
//              seat as HDMI) rather than the 3 mm upper bound, confidence assumed pending R4;
//              plug_len — brief's explicit instruction "USB-B 20" (confidence: assumed, cross-checked
//              against knowledge/neutrik/placement-and-depth.md:70 "~15-20 mm"); bend — assumed, USB
//              plugs are short/compact per knowledge/components/cables.md:125 "~17 mm" recommended
//              clearance at the USB-A end, so a small lateral allowance is used.
//              TODO(teamlead): "bend" for USB has no sourced figure; 8 mm is a smallest-reasonable-
//              choice placeholder, confidence assumed.
//   NBB75DFGB  (BNC):             hole_d knowledge/neutrik/d-series-cutout.md:37 "≥ 23.6 mm (... BNC
//              NBB75DFG)"; depth knowledge/neutrik/placement-and-depth.md:17 "NBB75DFG | 34 mm |
//              front-mount only"; max_panel_t — knowledge/neutrik/d-series-cutout.md:92 open question,
//              treated as 2.0 mm here per the brief's instruction pending R4; plug_len — brief's
//              explicit instruction "BNC 40.6 (Belden 4855R bend radius,
//              knowledge/components/cables.md:63)"; bend — same 40.6 mm figure re-used for the lateral
//              term per architecture.md:296-297 ("for BNC it is the dominant term"), i.e. for BNC the
//              bend radius genuinely governs both axial and lateral clearance simultaneously.
//   DBA-BL-B   (D blank plate):   hole_d 24.0 (rev 8, 2026-09-09, D-14 part 4 — was 0). A blanked
//              slot is a RESERVED slot, not a deleted one: the plate carries the full ⌀24.0 D-class
//              hole (etherCON/universal-D class, knowledge/neutrik/d-series-cutout.md:36 "≥ 24.0 mm
//              (etherCON NE8FDP, XLR NC3xD)") so any D-series connector can be fitted later by
//              swapping the purchased DBA-BL-B blanking plate for the connector — no reprint of the
//              panel plate or the shell. See architecture.md §5 "The DBA-BL-B blank carries the full
//              D hole (rev 8)" for the full derivation (why 24.0 and not 23.6) and D18 (the
//              is_blank test in neutrik.scad must move off `kind == "blank"` onto this field, see
//              neutrik.scad:39). depth knowledge/neutrik/placement-and-depth.md:21 "DBA-BL | 3.2 mm
//              (flat cover, not a feedthrough)"; max_panel_t assumed 4.0 (not a feedthrough, no seat
//              constraint — reuses the etherCON ceiling as a generous, non-binding default); plug_len
//              0, bend 0 (nothing plugs into a blank — unchanged by rev 8, architecture.md §5 table).
// The Mini-DIN-8 PTZ/Tally port stays internal on every current SKU (panel:"none", user decision
// 2026-09-07) — it is not dispatchable, so it is intentionally NOT a row in MCC_PANEL_PARTS.
// architecture.md §5 "the Mini-DIN-8 PTZ/Tally port stays internal ... on every current variant ...
// panel.scad needs no Mini-DIN-8 branch and no bespoke round-cutout provider". A possible future
// variant is documented in knowledge/components/mini-din8-feedthrough.md, but that record is not
// wired into this table; a port referencing "MINIDIN8" here is a deviation, not a valid part.
MCC_PANEL_PARTS = [
    ["NE8FDP-B",  [["hole_d", 24.0], ["depth", 34.55], ["max_panel_t", 4.0], ["plug_len", 25],   ["bend", 10],   ["kind", "rj45"],     ["confidence", "drawing"]]],
    ["NAHDMI-W-B",[["hole_d", 23.6], ["depth", 40.65], ["max_panel_t", 2.0], ["plug_len", 35],   ["bend", 15],   ["kind", "hdmi_a"],   ["confidence", "drawing"]]],
    ["NAUSB-W-B", [["hole_d", 23.6], ["depth", 40.55], ["max_panel_t", 2.0], ["plug_len", 20],   ["bend", 8],    ["kind", "usb_b"],    ["confidence", "drawing"]]],
    ["NBB75DFGB", [["hole_d", 23.6], ["depth", 34.0],  ["max_panel_t", 2.0], ["plug_len", 40.6], ["bend", 40.6], ["kind", "bnc"],      ["confidence", "drawing"]]],
    ["DBA-BL-B",  [["hole_d", 24.0], ["depth", 3.2],   ["max_panel_t", 4.0], ["plug_len", 0],    ["bend", 0],    ["kind", "blank"],    ["confidence", "drawing"]]],
];

// -----------------------------------------------------------------------------------------
// Section: Port confidence order
// architecture.md:283 field contract table "confidence | measured/drawing/manual/photo/assumed |
// required". Ordered weakest-first so lib/mcc/ports.scad's _mcc_confidence_rank() can compare
// with plain `<`. Lives here (not in ports.scad, which is the file that actually consumes it) so
// that anything reached only via `use <mcc/ports.scad>` (which never re-exports plain variables,
// only modules/functions) can still see it through the `include`d constants.scad.
// -----------------------------------------------------------------------------------------

MCC_CONFIDENCE_ORDER = ["assumed", "photo", "manual", "drawing", "measured"];

// -----------------------------------------------------------------------------------------
// Section: Panel-part pure accessors
// -----------------------------------------------------------------------------------------

function _mcc_panel_part_rec(part) =
    let(ind = search([part], MCC_PANEL_PARTS)[0])
    assert(ind != [], str("mcc: unknown panel part \"", part, "\""))
    MCC_PANEL_PARTS[ind][1];

function mcc_panel_hole_d(part)  = struct_val(_mcc_panel_part_rec(part), "hole_d");
function mcc_panel_depth(part)   = struct_val(_mcc_panel_part_rec(part), "depth");
function mcc_panel_max_t(part)   = struct_val(_mcc_panel_part_rec(part), "max_panel_t");
function mcc_plug_len(part)      = struct_val(_mcc_panel_part_rec(part), "plug_len");
function mcc_bend_envelope(part) = struct_val(_mcc_panel_part_rec(part), "bend");
function mcc_panel_kind(part)    = struct_val(_mcc_panel_part_rec(part), "kind");
function mcc_panel_confidence(part) = struct_val(_mcc_panel_part_rec(part), "confidence");

// Total axial bay depth: connector body + mating plug/bend allowance. architecture.md:294-295.
function mcc_bay_depth(part) = mcc_panel_depth(part) + mcc_plug_len(part);

// Nominal CAD cutout diameter: documented minimum hole + FDM hole-shrink compensation.
// architecture.md:293 / knowledge/neutrik/d-series-cutout.md:38-43.
function mcc_cutout_d(part) = mcc_panel_hole_d(part) + MCC_HOLE_COMP;

// vim: expandtab tabstop=4 shiftwidth=4 softtabstop=4 nowrap
