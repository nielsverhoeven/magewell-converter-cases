//////////////////////////////////////////////////////////////////////
// Device data: Pro Convert SDI Plus
//   DATA ONLY — no include/use, no modules, no BOSL2 calls (architecture.md:98-99).
// Source: knowledge/magewell/models/pro-convert-sdi-plus.md (fetched 2026-09-07)
// Written: 2026-09-07
//
// Same chassis/port topology as pro-convert-hdmi-plus.scad, HDMI IN/OUT replaced by SDI IN/OUT
// BNC. Same End-B pitch caveat applies (architecture.md §11 R3). Port positions estimated from
// the documented order; confidence "photo" for connectors/rotary, "assumed" for the tripod hole
// (architecture.md §11 R8).
//////////////////////////////////////////////////////////////////////

MCC_DEV_PRO_CONVERT_SDI_PLUS = [
    ["slug",   "pro-convert-sdi-plus"],
    ["family", "plus"],
    ["size",   [117.5, 66.7, 23.4]], // knowledge/magewell/models/pro-convert-sdi-plus.md:17
    ["source", "knowledge/magewell/models/pro-convert-sdi-plus.md"],
    ["ports", [
        // End A (knowledge/magewell/models/pro-convert-sdi-plus.md:22): USB-B +5V -> RJ45
        [["id", "usb_b"],     ["face", [-1, 0, 0]], ["pos", [-16, 0]], ["kind", "usb_b"],
         ["dir", "power"],    ["panel", "NAUSB-W-B"], ["confidence", "photo"]],
        [["id", "rj45"],      ["face", [-1, 0, 0]], ["pos", [ 15, 0]], ["kind", "rj45"],
         ["dir", "bidir"],    ["panel", "NE8FDP-B"],  ["confidence", "photo"]],
        // End B bottom row (knowledge/magewell/models/pro-convert-sdi-plus.md:23): SDI IN, Mini-DIN-8, SDI OUT
        [["id", "sdi_in"],    ["face", [ 1, 0, 0]], ["pos", [-22, -6]], ["kind", "bnc"],
         ["dir", "in"],       ["panel", "NBB75DFGB"], ["confidence", "photo"]],
        // internal — not brought out (user decision 2026-09-07)
        [["id", "ptz_tally"], ["face", [ 1, 0, 0]], ["pos", [  0, -6]], ["kind", "minidin8"],
         ["dir", "bidir"],    ["panel", "none"],      ["confidence", "photo"]],
        [["id", "sdi_out"],   ["face", [ 1, 0, 0]], ["pos", [ 22, -6]], ["kind", "bnc"],
         ["dir", "out"],      ["panel", "NBB75DFGB"], ["confidence", "photo"]],
        // End B top row: 16-position rotary switch (flanked by Tally PREVIEW/PROGRAM LEDs, not modelled as ports)
        [["id", "rotary"],    ["face", [ 1, 0, 0]], ["pos", [  0, 10]], ["kind", "rotary16"],
         ["dir", "none"],     ["panel", "none"],      ["confidence", "photo"]],
        // Bottom: 1/4"-20 threaded hole, position undocumented for the Plus family (architecture.md §11 R8)
        [["id", "tripod"],    ["face", [0, 0, -1]], ["pos", [30, 0]], ["kind", "tripod_1_4_20"],
         ["dir", "none"],     ["panel", "none"],      ["confidence", "assumed"]]
    ]]
];

// vim: expandtab tabstop=4 shiftwidth=4 softtabstop=4 nowrap
