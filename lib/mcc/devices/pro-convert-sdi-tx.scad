//////////////////////////////////////////////////////////////////////
// Device data: Pro Convert SDI TX
//   DATA ONLY — no include/use, no modules, no BOSL2 calls (architecture.md:98-99).
// Source: knowledge/magewell/models/pro-convert-sdi-tx.md (fetched 2026-09-07)
// Written: 2026-09-07
//
// Same chassis/port topology as pro-convert-hdmi-tx.scad, HDMI IN replaced by SDI IN BNC. Port
// positions estimated from the documented left-to-right order, confidence "photo" for the
// physical connectors and rotary switch, "assumed" for the tripod hole (position "estimated from
// image", knowledge/magewell/models/pro-convert-sdi-tx.md:25).
//////////////////////////////////////////////////////////////////////

MCC_DEV_PRO_CONVERT_SDI_TX = [
    ["slug",   "pro-convert-sdi-tx"],
    ["family", "compact"],
    ["size",   [100.9, 60.2, 23.3]], // knowledge/magewell/models/pro-convert-sdi-tx.md:16
    ["source", "knowledge/magewell/models/pro-convert-sdi-tx.md"],
    ["ports", [
        // Input end (knowledge/magewell/models/pro-convert-sdi-tx.md:21): SDI IN BNC -> Input LED -> Mini-DIN-8 PTZ+TALLY
        [["id", "sdi_in"],    ["face", [ 1, 0, 0]], ["pos", [-18, 0]], ["kind", "bnc"],
         ["dir", "in"],       ["panel", "NBB75DFGB"], ["confidence", "photo"]],
        // internal — not brought out (user decision 2026-09-07)
        [["id", "ptz_tally"], ["face", [ 1, 0, 0]], ["pos", [ 14, 0]], ["kind", "minidin8"],
         ["dir", "bidir"],    ["panel", "none"],      ["confidence", "photo"]],
        // Power/data end (knowledge/magewell/models/pro-convert-sdi-tx.md:22): USB-B +5V -> Power LED -> RJ45
        [["id", "usb_b"],     ["face", [-1, 0, 0]], ["pos", [-16, 0]], ["kind", "usb_b"],
         ["dir", "power"],    ["panel", "NAUSB-W-B"], ["confidence", "photo"]],
        [["id", "rj45"],      ["face", [-1, 0, 0]], ["pos", [ 15, 0]], ["kind", "rj45"],
         ["dir", "bidir"],    ["panel", "NE8FDP-B"],  ["confidence", "photo"]],
        // Long-edge side face (knowledge/magewell/models/pro-convert-sdi-tx.md:23): 16-position rotary switch
        [["id", "rotary"],    ["face", [0, -1, 0]], ["pos", [30, 0]], ["kind", "rotary16"],
         ["dir", "none"],     ["panel", "none"],      ["confidence", "photo"]],
        // 1/4"-20 thread is on a long side face (user-verified 2026-09-08); u/v position
        // unmeasured — measure X from the nearest short end, Z from the bottom, and which side
        // seen from the USB/RJ45 end; the case yaw puts this face at -Y (layout-patch-wall.md).
        [["id", "side_bolt"], ["face", [0, -1, 0]], ["pos", [0, 0]], ["kind", "tripod_1_4_20"],
         ["dir", "none"],     ["panel", "none"],      ["confidence", "assumed"]]
    ]]
];

// vim: expandtab tabstop=4 shiftwidth=4 softtabstop=4 nowrap
