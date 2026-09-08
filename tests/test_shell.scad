//////////////////////////////////////////////////////////////////////
// tests/test_shell.scad
//   Tier-2 headless smoke test (architecture.md §9). Instantiates mcc_shell_base()/
//   mcc_shell_lid() (shell.scad), mcc_cradle() (cradle.scad), mcc_floor_features_add/cut()
//   (mounts.scad), and mcc_vents() for each of the 3 vented wall faces (vents.scad), all for
//   MCC_DEV_PRO_CONVERT_FOR_NDI_TO_HDMI — CSG export (-o out.csg) evaluates the full tree so every
//   in-model Tier-1 assert fires, without tessellating.
// Run:
//   openscad --backend=Manifold -o out.csg tests/test_shell.scad
//////////////////////////////////////////////////////////////////////

$fa = 1; $fs = 0.4;

include <mcc/mcc.scad>
include <mcc/devices/pro-convert-for-ndi-to-hdmi.scad>

DEV = MCC_DEV_PRO_CONVERT_FOR_NDI_TO_HDMI;
VARIANT = [
    ["external_ports", ["hdmi_out", "usb_host", "usb_b", "rj45"]],
    ["fan",             false],
    ["splitter",        false],
];
VARIANT_FAN = [
    ["external_ports", ["hdmi_out", "usb_host", "usb_b", "rj45"]],
    ["fan",             true],
    ["splitter",        false],
];

// --- shell.scad: both halves, default (fan=false) variant ---
mcc_shell_base(dev = DEV, cfg = VARIANT);
translate([0, 250, 0]) mcc_shell_lid(dev = DEV, cfg = VARIANT);

// --- shell.scad: base with fan=true (exercises the fan-cutout branch) ---
translate([250, 0, 0]) mcc_shell_base(dev = DEV, cfg = VARIANT_FAN);

// --- cradle.scad standalone ---
translate([250, 250, 0]) mcc_cradle(dev = DEV, cfg = VARIANT);

// --- mounts.scad standalone ---
translate([500, 0, 0]) mcc_floor_features_add(dev = DEV, cfg = VARIANT);
translate([500, 250, 0])
    difference() {
        cube([200, 170, 3], center = false);
        translate([100, 85, 0]) mcc_floor_features_cut(dev = DEV, cfg = VARIANT);
    }

// --- vents.scad standalone, all 3 vented faces + area sanity ---
l = mcc_case_layout(DEV, VARIANT);
W = struct_val(l, "W");
area = mcc_vent_intake_area(DEV, VARIANT);
echo(str("mcc test_shell: T1-30 net intake area=", area, " mm^2, threshold=",
    MCC_VENT_AREA_RATIO * PI / 4 * MCC_FAN_APERTURE_D * MCC_FAN_APERTURE_D, " mm^2"));
assert(area >= MCC_VENT_AREA_RATIO * PI / 4 * MCC_FAN_APERTURE_D * MCC_FAN_APERTURE_D,
    str("mcc test_shell: T1-30 net intake area ", area, " below threshold"));

translate([750, 0, 0])
    difference() {
        cube([200, W + 20, 60], center = false);
        translate([100, W / 2 + 10, 0]) mcc_vents(dev = DEV, cfg = VARIANT, face = [0, -1, 0]);
    }
translate([750, 250, 0])
    difference() {
        cube([200, W + 20, 60], center = false);
        translate([100, W / 2 + 10, 0]) mcc_vents(dev = DEV, cfg = VARIANT, face = [-1, 0, 0]);
    }
translate([750, 500, 0])
    difference() {
        cube([200, W + 20, 60], center = false);
        translate([100, W / 2 + 10, 0]) mcc_vents(dev = DEV, cfg = VARIANT_FAN, face = [1, 0, 0]);
    }

echo("mcc test_shell: OK");

// -----------------------------------------------------------------------------------------
// Manual check: mcc_vents() must reject the patch wall (T1-19). OpenSCAD has no "expect this
// render to fail" mechanism, so this cannot be asserted automatically in a render that must
// otherwise succeed. To verify by hand, append the following line to a scratch copy of this file
// and confirm the render FAILS with an ERROR containing "T1-19":
//
//   mcc_vents(dev = DEV, cfg = VARIANT, face = [0, 1, 0]);
// -----------------------------------------------------------------------------------------

// vim: expandtab tabstop=4 shiftwidth=4 softtabstop=4 nowrap
