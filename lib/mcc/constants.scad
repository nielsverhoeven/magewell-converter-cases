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

// -----------------------------------------------------------------------------------------
// Section: PoE splitter envelope
// knowledge/components/poe-splitters.md.
// -----------------------------------------------------------------------------------------

// PoE Texas GAT-USBC placeholder envelope (architecture.md:485-486 "pending
// knowledge/components/poe-splitters.md; the bay envelope is a placeholder until a part is chosen").
// size:         knowledge/components/poe-splitters.md:58 "114 x 51 x 25" (L x W x H, mm)
// weight_g:     knowledge/components/poe-splitters.md:58 "85 g"
// cable_allow:  knowledge/components/poe-splitters.md §"Space envelope" / the brief's own instruction
//               "plus 20 mm cable allowance on each RJ45 end" — 20 mm, per-end, applied at both RJ45 ends.
MCC_SPLITTERS = [
    ["GAT-USBC", [["size", [114, 51, 25]], ["weight_g", 85], ["cable_allow", 20]]],
];

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
//   MINIDIN8   (Mini-DIN-8 PTZ/Tally, printed D-footprint insert, architecture.md §5 "Mini-DIN-8
//              panel solution"): hole_d — brief's explicit instruction "hole_d 12.5 assumed"
//              (cross-checked against knowledge/components/mini-din8-feedthrough.md:68 "a standard
//              mini-DIN shell is ~13.2 mm mating-face diameter" — 12.5 mm is smaller than that figure
//              and is flagged for correction, see TODO below); depth — brief's explicit instruction
//              "depth 20 assumed" (no sourced figure exists per
//              knowledge/components/mini-din8-feedthrough.md:271-272 "Exact panel hole diameter ...
//              and depth-behind-panel for any specific branded Mini-DIN8 panel-mount connector ...
//              none could be confirmed"); max_panel_t assumed 3.0 (reuses the etherCON/general-D
//              1-3 mm band, knowledge/neutrik/d-series-cutout.md:88); plug_len assumed 15 (mini-DIN
//              mating plug is compact, no sourced figure); bend assumed 10 (no sourced figure).
//              TODO(teamlead): MINIDIN8's hole_d (12.5) is smaller than the ~13.2 mm typical mini-DIN
//              mating-face diameter cited in knowledge/components/mini-din8-feedthrough.md:68 — this
//              looks likely to be undersized for a real connector body (though it may be intentional,
//              since a mini-DIN *shell* often clears a smaller panel hole than its overall diameter,
//              similar to a bulkhead nut). Flagged rather than silently changed, since the brief gave
//              this figure explicitly. Confirm against a physically sourced Mini-DIN8 panel connector
//              before cutting the neutrik-tile-equivalent Mini-DIN coupon.
MCC_PANEL_PARTS = [
    ["NE8FDP-B",  [["hole_d", 24.0], ["depth", 34.55], ["max_panel_t", 4.0], ["plug_len", 25],   ["bend", 10],   ["kind", "rj45"],     ["confidence", "drawing"]]],
    ["NAHDMI-W-B",[["hole_d", 23.6], ["depth", 40.65], ["max_panel_t", 2.0], ["plug_len", 35],   ["bend", 15],   ["kind", "hdmi_a"],   ["confidence", "drawing"]]],
    ["NAUSB-W-B", [["hole_d", 23.6], ["depth", 40.55], ["max_panel_t", 2.0], ["plug_len", 20],   ["bend", 8],    ["kind", "usb_b"],    ["confidence", "drawing"]]],
    ["NBB75DFGB", [["hole_d", 23.6], ["depth", 34.0],  ["max_panel_t", 2.0], ["plug_len", 40.6], ["bend", 40.6], ["kind", "bnc"],      ["confidence", "drawing"]]],
    ["DBA-BL-B",  [["hole_d", 0],    ["depth", 3.2],   ["max_panel_t", 4.0], ["plug_len", 0],    ["bend", 0],    ["kind", "blank"],    ["confidence", "drawing"]]],
    ["MINIDIN8",  [["hole_d", 12.5], ["depth", 20],    ["max_panel_t", 3.0], ["plug_len", 15],   ["bend", 10],   ["kind", "minidin8"], ["confidence", "assumed"]]],
];

// -----------------------------------------------------------------------------------------
// Section: Mini-DIN-8 "PTZ+TALLY" printed D-footprint insert (optional fixing screws)
// architecture.md §5 "Mini-DIN-8 panel solution ... panel.scad models it as a parametric round
// cutout with a configurable flange/fixing pattern" / architecture.md §12 Q5 (open question).
// No mechanical drawing exists for any specific Mini-DIN8 panel-mount connector
// (knowledge/components/mini-din8-feedthrough.md:271-272 "Exact panel hole diameter ... and
// depth-behind-panel for any specific branded Mini-DIN8 panel-mount connector ... none could be
// confirmed"). Both figures below are smallest-reasonable-choice placeholders.
// TODO(teamlead): entirely assumed pending a physically sourced Mini-DIN8 panel connector; confirm
// or replace before cutting a Mini-DIN8 coupon.
// -----------------------------------------------------------------------------------------

MCC_MINIDIN8_SCREW_PITCH = 18;  // optional M2.5 fixing-screw pitch, mm. assumed.
MCC_M2_5_CLR_D            = 2.8; // M2.5 clearance hole, mm. assumed — ISO 273 "medium" M2.5 clearance.

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
