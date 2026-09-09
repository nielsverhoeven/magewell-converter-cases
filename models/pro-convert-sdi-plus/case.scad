//////////////////////////////////////////////////////////////////////
// models/pro-convert-sdi-plus/case.scad
//   L4 thin assembly (architecture.md §4, new-case-variant skill). Copied from the normative
//   template models/pro-convert-for-ndi-to-hdmi/case.scad, per the new-case-variant skill and
//   .claude/knowledge/layout-patch-wall.md §16 (issue #6). part in {"base","lid","panel",
//   "assembly","ghost_device","ghost_plugs"}; only base/lid/panel are picked up by
//   scripts/build.py's discover_models() by default (it hardcodes ["base","lid"] + "panel" iff the
//   literal substring 'part == "panel"' appears below). Plus family: fan = true by default (user
//   decision 2026-09-08, R5) -- so unlike the template's compact-family default (fan = false plus
//   a "base_fan" extra_parts CI part to force-check the cutout), no separate "base_fan" part is
//   needed here: the default "base" render already carries the live fan cutout.
// Render:
//   openscad --backend=Manifold -D 'part="base"' -o out/base.stl models/pro-convert-sdi-plus/case.scad
//////////////////////////////////////////////////////////////////////

include <mcc/mcc.scad>
include <mcc/devices/pro-convert-sdi-plus.scad>

$fa = 1; $fs = 0.4; // the ONLY place $fn-adjacent globals are set (openscad-authoring skill).

part = "base"; // overridden via -D part="..."

// explode: Z-lift (mm) applied to the lid ONLY when part=="assembly" (preview aid). No effect on
// base/lid/panel exports.
explode = 0;

// Variant config (cfg): case-level options only. The connector slot set is NEVER driven by this
// config -- it comes solely from the device file's own `panel` field per port
// (mcc_ports_external(dev) / mcc_slot_assignment(dev), lib/mcc/layout.scad). An earlier
// "external_ports" key that purported to let a variant blank or omit a physical port was found to
// be INERT -- mcc_slot_assignment()/mcc_case_layout() never read it (architecture.md §13
// deviation D12, layout-patch-wall.md §16.4) -- and has been DROPPED here rather than wired up;
// implementing it would be a library change, out of scope for a variant branch. To omit a port
// from this case, remove/edit it in lib/mcc/devices/pro-convert-sdi-plus.scad instead
// (device-portmap skill) -- or, if it must stay in the port map but never get a cutout, give it
// `["panel","none"]` there (same convention the Mini-DIN-8/rotary/button ports already use).
//
// Documented cfg keys (all consulted by lib/mcc/**, see mcc_shell_base()'s own doc comment):
//   "fan"       (bool, REQUIRED) -- draws the live +X fan aperture when true. The fan BAY is
//               reserved as internal keep-out volume regardless of this flag (architecture.md §6
//               reservation rule) -- "false" only skips the live cutout, never the reservation.
//               Fed from the top-level `fan` variable below so `-D fan=false` overrides it for a
//               quick no-fan comparison render without editing this file.
//   "splitter"  (bool, REQUIRED) -- reserved for a future live PoE-splitter cutout; the splitter
//               BAY is reserved as keep-out volume regardless of this flag today (same
//               reservation rule -- no live splitter geometry is drawn by any flag value yet).
//               Fed from the top-level `splitter` variable below, likewise overridable via
//               `-D splitter=true`.
//   "rail"      (bool, optional, default true) -- cuts the tool-less dovetail mount-rail groove in
//               the floor (mounts.scad, D-15/rev 9, issue #25 -- replaces VESA). Pass false to omit.
//   "tripod_insert" (bool, optional, default true, D-16) -- draws the case's own 1/4"-20
//               floor-mount insert boss (cradle.scad, T1-32), braced into the deck lattice with
//               a collar (T1-41). Pass false to omit both the boss and its bore cut.
//   "fan_y"     (mm, optional, default the device's own Y centreline, R20) -- shell parameter for
//               the fan aperture's Y position (layout-patch-wall.md §5).
//   "fan_switch" (bool, optional, default = cfg's own "fan" value) -- draws the recessed manual
//               fan-switch cutout+pad on the +X wall, beside the fan aperture, when true (rev 11,
//               #32, D-18). This is one of the 3 Plus-family SKUs the switch ships on (the compact
//               family's feasible switch_y interval is empty, layout-patch-wall.md §18.2) -- set
//               explicitly (tied to `fan`) for the same BOM/documentation-parity reason "fan" is
//               explicit here, rather than left to the default.
fan      = true;  // Plus-family default: fan FITTED (user decision 2026-09-08, R5 -- the Plus
                   // chassis' ~10 W thermal budget makes the fan non-optional here, unlike the
                   // compact-family template this file was copied from, which defaults to false).
                   // -D fan=false renders the base without the live cutout for comparison only.
splitter = false; // -D splitter=true (reserved key; no live cutout exists yet either way)

variant = [
    ["fan",         fan],
    ["splitter",    splitter],
    ["fan_switch",  fan],
    ["tripod_insert", true],
];

dev = MCC_DEV_PRO_CONVERT_SDI_PLUS;

// Shared slot-list construction for the "panel" and "assembly" branches (data assembly, not raw
// geometry -- acceptable per new-case-variant's stop-and-report gate).
function _mcc_case_slot_list(dev, cfg) =
    let(
        slots_raw = mcc_slot_assignment(dev),
        layout    = mcc_case_layout(dev, cfg),
        slot_x    = struct_val(layout, "slot_x")
    )
    [for (s = slots_raw) let(i = struct_val(s, "slot")) [slot_x[i - 1], 0, struct_val(s, "part"), false]];

L_dims = mcc_case_dims(dev, variant);
echo(str("pro-convert-sdi-plus: L=", L_dims[0], " W=", L_dims[1], " H=", L_dims[2]));
echo(str("pro-convert-sdi-plus: slots=", mcc_slot_assignment(dev)));

// Place children at the device's assembled position (layout-patch-wall.md §2 frame): the device
// box is centred at (x_dev_c, y_dev_c, z_dev_lo + h/2).
module _mcc_case_at_device(layout) {
    translate([struct_val(layout, "x_dev_c"), struct_val(layout, "y_dev_c"),
               struct_val(layout, "z_dev_lo") + mcc_dev_size(dev)[2] / 2])
        children();
}

// The panel plate at its assembled position in the patch wall. Plate's local frame: front
// (connector) face at local Z=0, field/rim extend into local -Z; local X = plate width (= world X);
// local Y = plate height. rotate([-90,0,0]) maps local Z -> world Y and local Y -> world -Z (same
// rotation shell.scad uses for the side-bolt boss). The front face lands on the bezel-recessed
// plane W/2 - MCC_PANEL_BEZEL_T at connector centreline height z_conn_c.
module _mcc_case_panel_placed(layout) {
    translate([0, struct_val(layout, "W") / 2 - MCC_PANEL_BEZEL_T, struct_val(layout, "z_conn_c")])
        rotate([-90, 0, 0])
            mcc_panel_plate(size = mcc_panel_plate_dims(dev), slots = _mcc_case_slot_list(dev, variant));
}

if (part == "base") {
    mcc_shell_base(dev = dev, cfg = variant);

} else if (part == "lid") {
    mcc_shell_lid(dev = dev, cfg = variant);

} else if (part == "panel") {
    plate_sz = mcc_panel_plate_dims(dev);
    mcc_panel_plate(size = plate_sz, slots = _mcc_case_slot_list(dev, variant));

} else if (part == "assembly") {
    // Non-exported preview only. scripts/build.py's discover_models() hardcodes parts=["base",
    // "lid"] (+ "panel" iff the literal string 'part == "panel"' appears in this file) -- it never
    // looks for "assembly", so this branch is invisible to render --all / check --all / golden by
    // construction.
    layout = mcc_case_layout(dev, variant);
    color("SlateGray") mcc_shell_base(dev = dev, cfg = variant);
    translate([0, 0, explode])
        color("LightSteelBlue", 0.9) mcc_shell_lid(dev = dev, cfg = variant);
    color("DimGray") _mcc_case_panel_placed(layout);
    // device + plug envelopes at the device's assembled position; %-rendered, excluded from CSG
    _mcc_case_at_device(layout) mcc_ghost(dev, show = MCC_SHOW_GHOST);

} else if (part == "panel_placed") {
    // The plate at its assembled position (web viewer only; build.py exports the flat "panel").
    _mcc_case_panel_placed(mcc_case_layout(dev, variant));

} else if (part == "ghost_device") {
    // SOLID (no %) export of the device bounding box at its assembled position, for the web viewer
    // only -- never rendered by build.py (not in its "base"/"lid"/"panel" part set).
    _mcc_case_at_device(mcc_case_layout(dev, variant))
        cube(mcc_dev_size(dev), center = true);

} else if (part == "ghost_plugs") {
    // SOLID (no %) export of every external port's plug/bend keep-out envelope at the device's
    // assembled position, for the web viewer only.
    size = mcc_dev_size(dev);
    _mcc_case_at_device(mcc_case_layout(dev, variant))
    for (p = mcc_dev_ports(dev)) {
        panel = mcc_port_panel(p);
        if (panel != "none") {
            n = mcc_port_face(p);
            pos = mcc_port_pos(p);
            up_ref = (abs(n[2]) > 0.999) ? [0, 1, 0] : [0, 0, 1];
            right = unit(cross(up_ref, n));
            up = cross(n, right);
            total_len = mcc_plug_len(panel) + mcc_bend_envelope(panel);
            stub = n[0] != 0 ? [2, 8, 8] : n[1] != 0 ? [8, 2, 8] : [8, 8, 2];
            plug_size = [
                n[0] != 0 ? total_len : stub[0],
                n[1] != 0 ? total_len : stub[1],
                n[2] != 0 ? total_len : stub[2],
            ];
            center = [for (i = [0:2]) n[i] * size[i] / 2] + right * pos[0] + up * pos[1] + n * (total_len / 2);
            translate(center) cube(plug_size, center = true);
        }
    }

} else {
    assert(false, str("mcc: unknown part \"", part, "\""));
}

// vim: expandtab tabstop=4 shiftwidth=4 softtabstop=4 nowrap
