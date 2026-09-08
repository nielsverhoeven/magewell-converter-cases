//////////////////////////////////////////////////////////////////////
// models/pro-convert-for-ndi-to-hdmi/case.scad
//   L4 thin assembly (architecture.md §4, new-case-variant skill). The first full case built
//   against the L2 milestone (docs/plans/2026-09-08-l2-first-case.md,
//   .claude/knowledge/layout-patch-wall.md rev 5). part in {"base","lid","panel","assembly",
//   "ghost_device","ghost_plugs"}; only base/lid/panel are ever picked up by scripts/build.py
//   (discover_models() hardcodes ["base","lid"] + "panel" iff the literal substring
//   'part == "panel"' appears below).
// Render:
//   openscad --backend=Manifold -D 'part="base"' -o out/base.stl models/pro-convert-for-ndi-to-hdmi/case.scad
//////////////////////////////////////////////////////////////////////

include <mcc/mcc.scad>
include <mcc/devices/pro-convert-for-ndi-to-hdmi.scad>

$fa = 1; $fs = 0.4; // the ONLY place $fn-adjacent globals are set (openscad-authoring skill).

part = "base"; // overridden via -D part="..."

// explode: Z-lift (mm) applied to the lid ONLY when part=="assembly" (preview aid). No effect on
// base/lid/panel exports.
explode = 0;

// Variant config: every physical port from the device's own ["ports",...] list that is brought
// out to a panel connector, plus case-level options. Fan/splitter are RESERVED regardless
// (architecture.md §6 reservation rule) -- "false" only controls whether the live cutout/hardware
// is drawn, never whether the volume is kept clear.
variant = [
    ["external_ports", ["hdmi_out", "usb_host", "usb_b", "rj45"]], // all 4 physical ports brought out
    ["fan",             false],
    ["splitter",        false],
];

dev = MCC_DEV_PRO_CONVERT_FOR_NDI_TO_HDMI;

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
echo(str("pro-convert-for-ndi-to-hdmi: L=", L_dims[0], " W=", L_dims[1], " H=", L_dims[2]));
echo(str("pro-convert-for-ndi-to-hdmi: slots=", mcc_slot_assignment(dev)));

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
    plate_sz = mcc_panel_plate_dims(dev);
    // Plate's local frame: front (connector) face at local Z=0, field/rim extend into local -Z;
    // local X = plate width (already world X, slot_x is authored in world X directly); local Y =
    // plate height (screw-hole offset axis). rotate([-90,0,0]) maps local Z -> world Y and local Y
    // -> world -Z (see shell.scad's own derivation of this same rotation, used for the side-bolt
    // boss/patch-wall fixing bosses) -- translate the front face (local Z=0) to the patch wall's
    // actual proud-bezel-recessed front plane (W/2 - MCC_PANEL_BEZEL_T), and z_conn_c to correct
    // for the Y-axis sign flip the rotation introduces.
    translate([0, struct_val(layout, "W") / 2 - MCC_PANEL_BEZEL_T, struct_val(layout, "z_conn_c")])
        rotate([-90, 0, 0])
            color("DimGray") mcc_panel_plate(size = plate_sz, slots = _mcc_case_slot_list(dev, variant));
    mcc_ghost(dev, show = true); // device + plug envelopes; %-rendered, excluded from CSG anyway

} else if (part == "ghost_device") {
    // SOLID (no %) export of the device bounding box, for the web viewer only -- never rendered by
    // build.py (not in its "base"/"lid"/"panel" part set).
    cube(mcc_dev_size(dev), center = true);

} else if (part == "ghost_plugs") {
    // SOLID (no %) export of every external port's plug/bend keep-out envelope, for the web viewer
    // only.
    size = mcc_dev_size(dev);
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
