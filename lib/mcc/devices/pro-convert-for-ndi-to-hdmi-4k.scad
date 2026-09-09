//////////////////////////////////////////////////////////////////////
// Device data: Pro Convert for NDI to HDMI 4K
//   DATA ONLY — no include/use, no modules, no BOSL2 calls (architecture.md:98-99).
// Source: knowledge/magewell/models/pro-convert-for-ndi-to-hdmi-4k.md (fetched 2026-09-07)
// Written: 2026-09-07
//
// NDI decoder electronics on the Plus chassis (despite being part of the decoder family — see
// knowledge/magewell/models/pro-convert-for-ndi-to-hdmi-4k.md:16-20). Internal variable-speed fan
// is not modelled as a port (it is fully internal to the Magewell housing, not a case-facing
// feature — the case's own optional fan bay, if any, is a shell/mounts.scad concern, out of scope
// for this data file). Port positions estimated from the documented order; confidence "photo" for
// connectors/rotary/menu, "assumed" for the tripod hole (architecture.md §11 R8) and for the
// rotary/tally-LED top-row ordering, which the source itself calls "exact ... order uncertain".
//////////////////////////////////////////////////////////////////////

MCC_DEV_PRO_CONVERT_FOR_NDI_TO_HDMI_4K = [
    ["slug",   "pro-convert-for-ndi-to-hdmi-4k"],
    ["family", "plus"],
    ["size",   [117.5, 66.7, 23.4]], // knowledge/magewell/models/pro-convert-for-ndi-to-hdmi-4k.md:21
    ["source", "knowledge/magewell/models/pro-convert-for-ndi-to-hdmi-4k.md"],
    ["ports", [
        // Face A (knowledge/magewell/models/pro-convert-for-ndi-to-hdmi-4k.md:25): USB HOST -> MENU toggle -> HDMI OUT
        [["id", "usb_host"],  ["face", [ 1, 0, 0]], ["pos", [-20, 0]], ["kind", "usb_a"],
         // panel DBA-BL-B, not NAUSB-W-B (user decision 2026-09-09, D-14): host port never used by
         // the build; slot stays built and reusable behind a blank (architecture.md §5 rev 8) — on
         // the 4k the port is internally cabled to the fan (D-14, §5 "Fan power is device-sourced").
         ["dir", "bidir"],    ["panel", "DBA-BL-B"],  ["confidence", "photo"]],
        [["id", "menu"],      ["face", [ 1, 0, 0]], ["pos", [  0, 0]], ["kind", "button"],
         ["dir", "none"],     ["panel", "none"],       ["confidence", "photo"]],
        [["id", "hdmi_out"],  ["face", [ 1, 0, 0]], ["pos", [ 20, 0]], ["kind", "hdmi_a"],
         ["dir", "out"],      ["panel", "NAHDMI-W-B"], ["confidence", "photo"]],
        // Face B (knowledge/magewell/models/pro-convert-for-ndi-to-hdmi-4k.md:26): USB-B +5V -> RJ45
        [["id", "usb_b"],     ["face", [-1, 0, 0]], ["pos", [-16, 0]], ["kind", "usb_b"],
         ["dir", "power"],    ["panel", "NAUSB-W-B"],  ["confidence", "photo"]],
        [["id", "rj45"],      ["face", [-1, 0, 0]], ["pos", [ 15, 0]], ["kind", "rj45"],
         ["dir", "bidir"],    ["panel", "NE8FDP-B"],   ["confidence", "photo"]],
        // Top, near Face B: 16-position rotary switch (Tally Preview/Program LEDs not modelled), order uncertain
        [["id", "rotary"],    ["face", [0, 0, 1]], ["pos", [-15, 0]], ["kind", "rotary16"],
         ["dir", "none"],     ["panel", "none"],       ["confidence", "photo"]],
        // 1/4"-20 thread is on a long side face (user-verified 2026-09-08); u/v position
        // unmeasured — measure X from the nearest short end, Z from the bottom, and which side
        // seen from the USB/RJ45 end; the case yaw puts this face at -Y (layout-patch-wall.md).
        [["id", "side_bolt"], ["face", [0, -1, 0]], ["pos", [0, 0]], ["kind", "tripod_1_4_20"],
         ["dir", "none"],     ["panel", "none"],       ["confidence", "assumed"]]
    ]]
];

// vim: expandtab tabstop=4 shiftwidth=4 softtabstop=4 nowrap
