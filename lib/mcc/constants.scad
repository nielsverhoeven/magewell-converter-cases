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

// M4 heat-set insert (Ruthex RX-M4x8.1 class), same keyed struct shape as MCC_INSERT_M3. Used by
// the floor VESA 75x75 blind-insert bosses (mounts.scad, layout-patch-wall.md §7.1 rev-5 correction
// H). No M4 insert figures exist in knowledge/components/fasteners-and-hardware.md (which sources
// only the M3 RX-M3x5.7/RX-M3S family) — the figures below are typical brass/Ruthex M4 heat-set
// insert dimensions (generic hardware-catalog range, not project-sourced), following the same
// "typical" pattern already used for MCC_INSERT_1_4_20 above. confidence: assumed.
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

// Rev 6 (2026-09-08) aperture-shape constants — layout-patch-wall.md §11 rev-6 addendum / §2.5 /
// §15 ruling 2026-09-08b. All five/six are print-process figures, `assumed` (not sourced
// dimensions); none of them changes L/W/H, the plate size, the slot pitch or any fixing position —
// this ruling is shape-and-bore-only. Deliberately NOT added here: MCC_APERTURE_TOP_OPEN -- the
// top-open (U-notch) aperture is rejected, not parameterised (§15 ruling 2026-09-08b).
MCC_APERTURE_BRIDGE_MAX = 10.0; // max unsupported horizontal span anywhere in the patch-wall
                          // aperture, mm — the one place architecture.md §5's "no unsupported
                          // horizontal span over 10 mm anywhere in the shell" becomes a number.
                          // Used by T1-34a (window apex flat-bridge width w_flat).
MCC_APERTURE_SELF_SUPPORT_MAX_D = 10.0; // assumed -- round-hole diameter below which a
                          // horizontally-printed hole needs NO teardrop of its own (same 10 mm span
                          // rule, read as a diameter). Used by T1-34a to justify the plain-circle
                          // boss reliefs (d_rel = 8.88 < 10.0).
MCC_APERTURE_CAP_RISE = 0.4; // assumed -- how far the truncated-teardrop cap sits above the body
                          // circle's own top, mm: cap_h = d_win/2 + MCC_APERTURE_CAP_RISE. Chosen as
                          // the smallest rise that still hides the cap behind the plate
                          // (cap_h > mcc_cutout_d(part)/2, margin 0.7 mm) while keeping w_flat under
                          // MCC_APERTURE_BRIDGE_MAX. Calibrate with the neutrik-tile coupon.
MCC_APERTURE_RELIEF_INTRUSION_MAX = 1.5; // assumed -- maximum radial intrusion of a boss relief
                          // inside the plate's own cutout silhouette, mm -- the numeric form of "the
                          // D slots must read as exactly round" (the user's rejection, 2026-09-08).
                          // Actual worst case today 1.235 mm (NE8FDP-B). T1-34b.
MCC_APERTURE_LIP_WEB_MIN = 2.0; // minimum lip material between any part of a window and the plate's
                          // own edge, mm. knowledge/design/fdm-rugged-enclosure-guidelines.md:127.
                          // T1-34c.
MCC_INSERT_BORE_EXTRA = 0.5; // assumed -- extra bore depth past a heat-set insert's own length so
                          // the insert seats fully, mm. Replaces the bare "+ 1" literal in
                          // mcc_neutrik_d_bosses() (deviation D10 / T1-35).
MCC_PLATE_RIM_W = 6.0; // the panel plate's rim (border) width, mm. Named once so
                          // mcc_panel_plate()'s rim_w default, _mcc_patch_wall_aperture()'s local
                          // rim_w and the literal passed to _mcc_patch_wall_fixing_bosses() cannot
                          // drift apart across the two L2 files that used to hardcode "6"
                          // independently -- the exact drift hazard that produced deviation D6.

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

MCC_CRADLE_RIB_T = 3.0;    // locating-rib thickness, mm. layout-patch-wall.md §7 cradle table
                            // "Locating ribs | 3.0 mm thick x 9.0 mm tall".
MCC_CRADLE_RIB_H = 9.0;    // locating-rib height, mm. Same table; <= 3x thickness rule
                            // (fdm-rugged-enclosure-guidelines.md:65-70) satisfied (9 <= 9).
MCC_CRADLE_FLOOR_PAD_T = 2.0; // compliant EPDM floor-pad thickness under the device, mm.
                               // fasteners-and-hardware.md:186, layout-patch-wall.md §7.
MCC_CRADLE_FLOOR_PAD_MIN = 40; // minimum compliant floor-pad footprint (square), mm.
                                // layout-patch-wall.md §7 "footprint >= 40x40".

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
MCC_CASE_INSERT_KEEPOUT_D = 20.0; // plan-view keep-out disc for the case's own 1/4"-20 insert, mm.
MCC_VESA_HOLE_D = 12.0;           // VESA 75x75 mounting-hole plan-view keep-out disc, mm (the holes
                                    // themselves are blind M4 heat-set-insert bosses per §15 ruling
                                    // H — see mounts.scad — this is only the keep-out footprint).
MCC_STRAP_SLOT = [25, 5];         // strap-slot [length, width], mm. assumed.
MCC_FISHTAIL_BAND = [60, 20];     // Magewell Fishtail M4 reservation band [x,y], mm — reserve-only,
                                    // hole pitch unknown (knowledge/magewell/accessories.md:26, M7).
MCC_FLOOR_FEATURE_MIN_SEP = 15.0; // minimum centre-to-centre separation between any two floor
                                    // features, mm (or r1+r2+2.0 where larger) — layout-patch-wall.md
                                    // §7.1.

// Ghost-rendering visibility flag (architecture.md:304 "gated behind MCC_SHOW_GHOST (default false)").
// Belt 2 of the two-belt ghost-exclusion rule; belt 1 is the `%` modifier used wherever ghost
// geometry is drawn (lib/mcc/ghost.scad, lib/mcc/neutrik.scad's *_envelope() keep-out boxes).
MCC_SHOW_GHOST = false;

MCC_VESA75_PITCH = 75; // VESA MIS-D 75x75 mm mounting hole pitch, mm. assumed — external VESA standard,
                        // not sourced from knowledge/** (no VESA reference exists there); included for the
                        // floor-mounts VESA pattern per architecture.md:229 "VESA/Fishtail M4 pattern".

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
//   DBA-BL-B   (D blank plate):   hole_d 0 (no cutout — a solid blank per architecture.md's
//              panel-part table spec "blank plate, hole_d 0"); depth
//              knowledge/neutrik/placement-and-depth.md:21 "DBA-BL | 3.2 mm (flat cover, not a
//              feedthrough)"; max_panel_t assumed 4.0 (not a feedthrough, no seat constraint — reuses
//              the etherCON ceiling as a generous, non-binding default); plug_len 0, bend 0 (nothing
//              plugs into a blank).
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
    ["DBA-BL-B",  [["hole_d", 0],    ["depth", 3.2],   ["max_panel_t", 4.0], ["plug_len", 0],    ["bend", 0],    ["kind", "blank"],    ["confidence", "drawing"]]],
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
