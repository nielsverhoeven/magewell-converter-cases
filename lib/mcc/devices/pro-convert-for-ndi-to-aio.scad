//////////////////////////////////////////////////////////////////////
// Device data: Pro Convert for NDI to AIO
//   DATA ONLY — no include/use, no modules, no BOSL2 calls (architecture.md:98-99).
// Source: knowledge/magewell/models/pro-convert-for-ndi-to-aio.md (fetched 2026-09-07)
// Written: 2026-09-07
//
// NDI decoder on the compact/TX chassis; no USB host port on this model (two simultaneous video
// outputs instead). Face-B USB-B port role beyond power is explicitly an open question in the
// source (knowledge/magewell/models/pro-convert-for-ndi-to-aio.md:47-48) — modelled here with
// dir="power" as the conservative/documented reading. Top-face layout "follows the shared decoder
// pattern" without a model-specific photo, so those positions are confidence "assumed".
//////////////////////////////////////////////////////////////////////

MCC_DEV_PRO_CONVERT_FOR_NDI_TO_AIO = [
    ["slug",   "pro-convert-for-ndi-to-aio"],
    ["family", "compact"],
    ["size",   [100.9, 60.2, 23.3]], // knowledge/magewell/models/pro-convert-for-ndi-to-aio.md:17
    ["source", "knowledge/magewell/models/pro-convert-for-ndi-to-aio.md"],
    ["ports", [
        // Face A (knowledge/magewell/models/pro-convert-for-ndi-to-aio.md:21): HDMI OUT -> LED -> SDI OUT BNC
        [["id", "hdmi_out"],  ["face", [ 1, 0, 0]], ["pos", [-16, 0]], ["kind", "hdmi_a"],
         ["dir", "out"],      ["panel", "NAHDMI-W-B"], ["confidence", "photo"]],
        [["id", "sdi_out"],   ["face", [ 1, 0, 0]], ["pos", [ 16, 0]], ["kind", "bnc"],
         ["dir", "out"],      ["panel", "NBB75DFGB"],  ["confidence", "photo"]],
        // Face B (knowledge/magewell/models/pro-convert-for-ndi-to-aio.md:22): USB-B (power only) -> LED -> RJ45
        [["id", "usb_b"],     ["face", [-1, 0, 0]], ["pos", [-16, 0]], ["kind", "usb_b"],
         ["dir", "power"],    ["panel", "NAUSB-W-B"],  ["confidence", "photo"]],
        [["id", "rj45"],      ["face", [-1, 0, 0]], ["pos", [ 15, 0]], ["kind", "rj45"],
         ["dir", "bidir"],    ["panel", "NE8FDP-B"],   ["confidence", "photo"]],
        // 1/4"-20 thread is on a long side face (user-verified 2026-09-08); u/v position
        // unmeasured — measure X from the nearest short end, Z from the bottom, and which side
        // seen from the USB/RJ45 end; the case yaw puts this face at -Y (layout-patch-wall.md).
        [["id", "side_bolt"], ["face", [0, -1, 0]], ["pos", [0, 0]], ["kind", "tripod_1_4_20"],
         ["dir", "none"],     ["panel", "none"],       ["confidence", "assumed"]],
        [["id", "rotary"],    ["face", [0, 0, 1]], ["pos", [20, 0]],  ["kind", "rotary16"],
         ["dir", "none"],     ["panel", "none"],       ["confidence", "assumed"]],
        [["id", "menu"],      ["face", [0, 0, 1]], ["pos", [30, 8]],  ["kind", "button"],
         ["dir", "none"],     ["panel", "none"],       ["confidence", "assumed"]],
        [["id", "select"],    ["face", [0, 0, 1]], ["pos", [30, -8]], ["kind", "button"],
         ["dir", "none"],     ["panel", "none"],       ["confidence", "assumed"]]
    ]]
];

// vim: expandtab tabstop=4 shiftwidth=4 softtabstop=4 nowrap
