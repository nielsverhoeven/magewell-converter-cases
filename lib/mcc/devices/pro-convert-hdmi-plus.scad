//////////////////////////////////////////////////////////////////////
// Device data: Pro Convert HDMI Plus
//   DATA ONLY — no include/use, no modules, no BOSL2 calls (architecture.md:98-99).
// Source: knowledge/magewell/models/pro-convert-hdmi-plus.md (fetched 2026-09-07)
// Written: 2026-09-07
//
// End B carries HDMI IN + Mini-DIN-8 + HDMI OUT at ~22 mm pitch — this is TIGHTER than
// MCC_D_PITCH_H (32 mm), a known unresolved layout risk (architecture.md §11 R3, "Plus End B has
// three connectors on a face that cannot hold them"). Recorded here as the true device geometry;
// resolving the panel layout (drop the loop-out, stack vertically, widen the case, ...) is a
// shell/panel-design decision for a later session, not something this data file should silently
// pre-solve by inventing extra device width. HDMI OUT is externalized to a second NAHDMI-W-B per
// the teamlead's decision recorded in the brief ("HDMI/SDI loop-OUT -> external, per user
// decision"). Port positions estimated from the documented order; confidence "photo" for
// connectors/rotary, "assumed" for the tripod hole (architecture.md §11 R8 "exact 1/4"-20 hole
// location is undocumented for the Plus family").
//////////////////////////////////////////////////////////////////////

MCC_DEV_PRO_CONVERT_HDMI_PLUS = [
    ["slug",   "pro-convert-hdmi-plus"],
    ["family", "plus"],
    ["size",   [117.5, 66.7, 23.4]], // knowledge/magewell/models/pro-convert-hdmi-plus.md:17
    ["source", "knowledge/magewell/models/pro-convert-hdmi-plus.md"],
    ["ports", [
        // End A (knowledge/magewell/models/pro-convert-hdmi-plus.md:22): USB-B +5V -> RJ45
        [["id", "usb_b"],     ["face", [-1, 0, 0]], ["pos", [-16, 0]], ["kind", "usb_b"],
         ["dir", "power"],    ["panel", "NAUSB-W-B"],  ["confidence", "photo"]],
        [["id", "rj45"],      ["face", [-1, 0, 0]], ["pos", [ 15, 0]], ["kind", "rj45"],
         ["dir", "bidir"],    ["panel", "NE8FDP-B"],   ["confidence", "photo"]],
        // End B bottom row (knowledge/magewell/models/pro-convert-hdmi-plus.md:23): HDMI IN, Mini-DIN-8, HDMI OUT
        [["id", "hdmi_in"],   ["face", [ 1, 0, 0]], ["pos", [-22, -6]], ["kind", "hdmi_a"],
         ["dir", "in"],       ["panel", "NAHDMI-W-B"], ["confidence", "photo"]],
        [["id", "ptz_tally"], ["face", [ 1, 0, 0]], ["pos", [  0, -6]], ["kind", "minidin8"],
         ["dir", "bidir"],    ["panel", "MINIDIN8"],   ["confidence", "photo"]],
        [["id", "hdmi_out"],  ["face", [ 1, 0, 0]], ["pos", [ 22, -6]], ["kind", "hdmi_a"],
         ["dir", "out"],      ["panel", "NAHDMI-W-B"], ["confidence", "photo"]],
        // End B top row: 16-position rotary switch (flanked by Tally PREVIEW/PROGRAM LEDs, not modelled as ports)
        [["id", "rotary"],    ["face", [ 1, 0, 0]], ["pos", [  0, 10]], ["kind", "rotary16"],
         ["dir", "none"],     ["panel", "none"],       ["confidence", "photo"]],
        // Bottom: 1/4"-20 threaded hole, position undocumented for the Plus family (architecture.md §11 R8)
        [["id", "tripod"],    ["face", [0, 0, -1]], ["pos", [30, 0]], ["kind", "tripod_1_4_20"],
         ["dir", "none"],     ["panel", "none"],       ["confidence", "assumed"]]
    ]]
];

// vim: expandtab tabstop=4 shiftwidth=4 softtabstop=4 nowrap
