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
include <mcc/devices/pro-convert-hdmi-plus.scad>

DEV = MCC_DEV_PRO_CONVERT_FOR_NDI_TO_HDMI;
// "external_ports" is DROPPED from cfg (D12, architecture.md §13 -- inert, never implemented; the
// slot set comes solely from mcc_ports_external(dev)). Real cfg keys only.
VARIANT = [
    ["fan",             false],
    ["splitter",        false],
];
VARIANT_FAN = [
    ["fan",             true],
    ["splitter",        false],
    // ["fan_switch",false]: the compact family's feasible switch_y interval is EMPTY (D-18,
    // layout-patch-wall.md §18.2) -- without this, T1-43 fails on this SKU's own base_fan golden.
    ["fan_switch",      false],
];

// Fan-switch coverage (rev 11, #32, D-18 §18.4): B6 stops the compact VARIANT_FAN above from
// exercising the switch cutout at all, so without a plus-family branch the feature would ship
// untested by `smoke` (D15's lesson, repeated). DEV_PLUS/VARIANT_PLUS_SWITCH exist ONLY to give
// mcc_switch_cutout()/mcc_switch_pad() and T1-43/T1-44 a real render-time exercise.
DEV_PLUS = MCC_DEV_PRO_CONVERT_HDMI_PLUS;
VARIANT_PLUS_SWITCH = [
    ["fan",             true],
    ["splitter",        false],
    ["fan_switch",      true],
];

// --- shell.scad: both halves, default (fan=false) variant ---
mcc_shell_base(dev = DEV, cfg = VARIANT);
translate([0, 250, 0]) mcc_shell_lid(dev = DEV, cfg = VARIANT);

// --- shell.scad: base with fan=true (exercises the fan-cutout branch) ---
translate([250, 0, 0]) mcc_shell_base(dev = DEV, cfg = VARIANT_FAN);

// --- shell.scad: plus-family base with fan=true + fan_switch=true (exercises the switch cutout) ---
translate([1000, 0, 0]) mcc_shell_base(dev = DEV_PLUS, cfg = VARIANT_PLUS_SWITCH);

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
