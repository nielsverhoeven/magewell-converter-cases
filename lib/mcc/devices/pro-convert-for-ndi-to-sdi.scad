//////////////////////////////////////////////////////////////////////
// Device data: Pro Convert for NDI to SDI
//   DATA ONLY — no include/use, no modules, no BOSL2 calls (architecture.md:98-99).
// Source: knowledge/magewell/models/pro-convert-for-ndi-to-sdi.md (fetched 2026-09-07)
// Written: 2026-09-07
//
// NDI decoder on the compact/TX chassis. Top-face layout is not independently photographed for
// this model — "only the shared decoder-family pattern is documented, not a model-specific photo"
// (knowledge/magewell/models/pro-convert-for-ndi-to-sdi.md:46-47) — so the rotary/menu/select
// positions are carried over from the shared pattern (as pro-convert-for-ndi-to-hdmi.scad) at
// confidence "assumed" rather than "photo", to flag that this specific model's layout was not
// independently confirmed.
//////////////////////////////////////////////////////////////////////

MCC_DEV_PRO_CONVERT_FOR_NDI_TO_SDI = [
    ["slug",   "pro-convert-for-ndi-to-sdi"],
    ["family", "compact"],
    ["size",   [100.9, 60.2, 23.3]], // knowledge/magewell/models/pro-convert-for-ndi-to-sdi.md:17
    ["source", "knowledge/magewell/models/pro-convert-for-ndi-to-sdi.md"],
    ["ports", [
        // Face A (knowledge/magewell/models/pro-convert-for-ndi-to-sdi.md:21): SDI OUT BNC -> LED -> USB HOST
        [["id", "sdi_out"],   ["face", [ 1, 0, 0]], ["pos", [-16, 0]], ["kind", "bnc"],
         ["dir", "out"],      ["panel", "NBB75DFGB"], ["confidence", "photo"]],
        [["id", "usb_host"],  ["face", [ 1, 0, 0]], ["pos", [ 16, 0]], ["kind", "usb_a"],
         // panel DBA-BL-B, not NAUSB-W-B (user decision 2026-09-09, D-14): host port never used by
         // the build; slot stays built and reusable behind a blank (architecture.md §5 rev 8).
         ["dir", "bidir"],    ["panel", "DBA-BL-B"], ["confidence", "photo"]],
        // Face B (knowledge/magewell/models/pro-convert-for-ndi-to-sdi.md:22): USB-B +5V -> LED -> RJ45
        [["id", "usb_b"],     ["face", [-1, 0, 0]], ["pos", [-16, 0]], ["kind", "usb_b"],
         ["dir", "power"],    ["panel", "NAUSB-W-B"], ["confidence", "photo"]],
        [["id", "rj45"],      ["face", [-1, 0, 0]], ["pos", [ 15, 0]], ["kind", "rj45"],
         ["dir", "bidir"],    ["panel", "NE8FDP-B"],  ["confidence", "photo"]],
        // 1/4"-20 thread is on a long side face (user-verified 2026-09-08); u/v position
        // unmeasured — measure X from the nearest short end, Z from the bottom, and which side
        // seen from the USB/RJ45 end; the case yaw puts this face at -Y (layout-patch-wall.md).
        [["id", "side_bolt"], ["face", [0, -1, 0]], ["pos", [0, 0]], ["kind", "tripod_1_4_20"],
         ["dir", "none"],     ["panel", "none"],      ["confidence", "assumed"]],
        [["id", "rotary"],    ["face", [0, 0, 1]], ["pos", [20, 0]],  ["kind", "rotary16"],
         ["dir", "none"],     ["panel", "none"],      ["confidence", "assumed"]],
        [["id", "menu"],      ["face", [0, 0, 1]], ["pos", [30, 8]],  ["kind", "button"],
         ["dir", "none"],     ["panel", "none"],      ["confidence", "assumed"]],
        [["id", "select"],    ["face", [0, 0, 1]], ["pos", [30, -8]], ["kind", "button"],
         ["dir", "none"],     ["panel", "none"],      ["confidence", "assumed"]]
    ]]
];

// vim: expandtab tabstop=4 shiftwidth=4 softtabstop=4 nowrap
