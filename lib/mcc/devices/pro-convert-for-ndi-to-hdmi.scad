//////////////////////////////////////////////////////////////////////
// Device data: Pro Convert for NDI to HDMI
//   DATA ONLY — no include/use, no modules, no BOSL2 calls (architecture.md:98-99).
// Source: knowledge/magewell/models/pro-convert-for-ndi-to-hdmi.md (fetched 2026-09-07)
// Written: 2026-09-07
//
// NDI decoder on the compact/TX chassis. Port positions estimated from the documented order;
// confidence "photo" for connectors/rotary/buttons, "assumed" for the tripod hole (position not
// independently confirmed for this model beyond the shared decoder-family pattern).
//////////////////////////////////////////////////////////////////////

MCC_DEV_PRO_CONVERT_FOR_NDI_TO_HDMI = [
    ["slug",   "pro-convert-for-ndi-to-hdmi"],
    ["family", "compact"],
    ["size",   [100.9, 60.2, 23.3]], // knowledge/magewell/models/pro-convert-for-ndi-to-hdmi.md:17
    ["source", "knowledge/magewell/models/pro-convert-for-ndi-to-hdmi.md"],
    ["ports", [
        // Face A (knowledge/magewell/models/pro-convert-for-ndi-to-hdmi.md:21): HDMI OUT -> decoding LED -> USB HOST
        [["id", "hdmi_out"],  ["face", [ 1, 0, 0]], ["pos", [-16, 0]], ["kind", "hdmi_a"],
         ["dir", "out"],      ["panel", "NAHDMI-W-B"], ["confidence", "photo"]],
        [["id", "usb_host"],  ["face", [ 1, 0, 0]], ["pos", [ 16, 0]], ["kind", "usb_a"],
         ["dir", "bidir"],    ["panel", "NAUSB-W-B"],  ["confidence", "photo"]],
        // Face B (knowledge/magewell/models/pro-convert-for-ndi-to-hdmi.md:22): USB-B +5V -> Power LED -> RJ45
        [["id", "usb_b"],     ["face", [-1, 0, 0]], ["pos", [-16, 0]], ["kind", "usb_b"],
         ["dir", "power"],    ["panel", "NAUSB-W-B"],  ["confidence", "photo"]],
        [["id", "rj45"],      ["face", [-1, 0, 0]], ["pos", [ 15, 0]], ["kind", "rj45"],
         ["dir", "bidir"],    ["panel", "NE8FDP-B"],   ["confidence", "photo"]],
        // Top, near Face A (knowledge/magewell/models/pro-convert-for-ndi-to-hdmi.md:23): SD slot (not modelled) + 1/4"-20 hole
        [["id", "tripod"],    ["face", [0, 0, 1]], ["pos", [-30, 0]], ["kind", "tripod_1_4_20"],
         ["dir", "none"],     ["panel", "none"],       ["confidence", "assumed"]],
        // Top, near Face B: 16-position rotary switch, MENU button, SELECT button
        [["id", "rotary"],    ["face", [0, 0, 1]], ["pos", [20, 0]],  ["kind", "rotary16"],
         ["dir", "none"],     ["panel", "none"],       ["confidence", "photo"]],
        [["id", "menu"],      ["face", [0, 0, 1]], ["pos", [30, 8]],  ["kind", "button"],
         ["dir", "none"],     ["panel", "none"],       ["confidence", "photo"]],
        [["id", "select"],    ["face", [0, 0, 1]], ["pos", [30, -8]], ["kind", "button"],
         ["dir", "none"],     ["panel", "none"],       ["confidence", "photo"]]
    ]]
];

// vim: expandtab tabstop=4 shiftwidth=4 softtabstop=4 nowrap
