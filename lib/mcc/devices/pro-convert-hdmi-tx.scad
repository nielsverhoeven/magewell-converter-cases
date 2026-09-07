//////////////////////////////////////////////////////////////////////
// Device data: Pro Convert HDMI TX
//   DATA ONLY — no include/use, no modules, no BOSL2 calls (architecture.md:98-99). Consumed via
//   lib/mcc/ports.scad accessors only.
// Source: knowledge/magewell/models/pro-convert-hdmi-tx.md (fetched 2026-09-07)
// Written: 2026-09-07
//
// Port positions are estimated from the documented left-to-right connector order
// (knowledge/magewell/housing-families.md:8-10 "no dimensioned port-position drawing exists for
// any model") — confidence "photo" for the four physical connectors and the rotary switch (all
// directly described/pictured in the source), "assumed" for the 1/4"-20 tripod hole (position
// only "estimated from image", knowledge/magewell/models/pro-convert-hdmi-tx.md:47).
// This exact record also appears verbatim as the worked example in architecture.md §7.
//////////////////////////////////////////////////////////////////////

MCC_DEV_PRO_CONVERT_HDMI_TX = [
    ["slug",   "pro-convert-hdmi-tx"],
    ["family", "compact"],
    ["size",   [100.9, 60.2, 23.3]], // knowledge/magewell/models/pro-convert-hdmi-tx.md:16
    ["source", "knowledge/magewell/models/pro-convert-hdmi-tx.md"],
    ["ports", [
        // Input end (knowledge/magewell/models/pro-convert-hdmi-tx.md:21): HDMI IN -> Input LED -> Mini-DIN-8 PTZ+TALLY
        [["id", "hdmi_in"],   ["face", [ 1, 0, 0]], ["pos", [-18, 0]], ["kind", "hdmi_a"],
         ["dir", "in"],       ["panel", "NAHDMI-W-B"], ["confidence", "photo"]],
        // internal — not brought out (user decision 2026-09-07)
        [["id", "ptz_tally"], ["face", [ 1, 0, 0]], ["pos", [ 14, 0]], ["kind", "minidin8"],
         ["dir", "bidir"],    ["panel", "none"],       ["confidence", "photo"]],
        // Power/data end (knowledge/magewell/models/pro-convert-hdmi-tx.md:22): USB-B +5V -> Power LED -> RJ45
        [["id", "usb_b"],     ["face", [-1, 0, 0]], ["pos", [-16, 0]], ["kind", "usb_b"],
         ["dir", "power"],    ["panel", "NAUSB-W-B"],  ["confidence", "photo"]],
        [["id", "rj45"],      ["face", [-1, 0, 0]], ["pos", [ 15, 0]], ["kind", "rj45"],
         ["dir", "bidir"],    ["panel", "NE8FDP-B"],   ["confidence", "photo"]],
        // Long-edge side face (knowledge/magewell/models/pro-convert-hdmi-tx.md:23): 16-position rotary switch
        [["id", "rotary"],    ["face", [0, -1, 0]], ["pos", [30, 0]], ["kind", "rotary16"],
         ["dir", "none"],     ["panel", "none"],       ["confidence", "photo"]],
        // Bottom (knowledge/magewell/models/pro-convert-hdmi-tx.md:25): 1/4"-20 threaded hole, "estimated from image"
        [["id", "tripod"],    ["face", [0, 0, -1]], ["pos", [30, 0]], ["kind", "tripod_1_4_20"],
         ["dir", "none"],     ["panel", "none"],       ["confidence", "assumed"]]
    ]]
];

// vim: expandtab tabstop=4 shiftwidth=4 softtabstop=4 nowrap
