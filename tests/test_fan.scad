//////////////////////////////////////////////////////////////////////
// tests/test_fan.scad
//   Tier-2 headless smoke test (architecture.md §9). Exercises mcc_fan_spec()'s default-name
//   equivalence, mcc_fan_cutout()'s default, and mcc_fan_envelope() -- previously uncalled
//   anywhere (D23, issue #36) -- so a signature/argument regression fails the render, matching
//   tests/test_fasteners.scad's precedent for mcc_side_bolt_envelope().
// Run:
//   openscad --backend=Manifold -o out.csg tests/test_fan.scad
//////////////////////////////////////////////////////////////////////

$fa = 1; $fs = 0.4;

include <mcc/mcc.scad>

MCC_SHOW_GHOST = true;   // exercise mcc_fan_envelope()'s gated %-branch (fasteners.scad's
                         // test-only precedent left it un-evaluated; a bad argument inside the
                         // `if` would not fail the render otherwise).

assert(mcc_fan_spec(MCC_FAN_DEFAULT) == mcc_fan_spec("NF-A4x10"),
    "mcc test_fan: mcc_fan_spec(MCC_FAN_DEFAULT) != mcc_fan_spec(\"NF-A4x10\")");

// mcc_fan_cutout() default vs. explicit name -- both as negatives so the file stays solid.
translate([0, 0, 0])
    difference() {
        cube([50, 50, MCC_WALL], center = false);
        translate([25, 25, 0]) mcc_fan_cutout(wall_t = MCC_WALL, grille = true);
    }
translate([60, 0, 0])
    difference() {
        cube([50, 50, MCC_WALL], center = false);
        translate([25, 25, 0]) mcc_fan_cutout(name = MCC_FAN_DEFAULT, wall_t = MCC_WALL, grille = true);
    }

// mcc_fan_envelope() (D23) -- %-ghost gated behind MCC_SHOW_GHOST; exercised so a regression
// fails the render.
translate([0, 100, 0]) mcc_fan_envelope();
translate([60, 100, 0]) mcc_fan_envelope(MCC_FAN_DEFAULT);

echo("mcc test_fan: OK");

// vim: expandtab tabstop=4 shiftwidth=4 softtabstop=4 nowrap
