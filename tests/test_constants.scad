//////////////////////////////////////////////////////////////////////
// tests/test_constants.scad
//   Tier-2 headless smoke test (architecture.md §9). Asserts every panel part in
//   MCC_PANEL_PARTS carries the full field set, spot-checks mcc_bay_depth(), and checks every
//   panel part's cutout diameter falls in its class's valid range.
// Run:
//   openscad --backend=Manifold -o out.csg tests/test_constants.scad
//////////////////////////////////////////////////////////////////////

$fa = 1; $fs = 0.4;

include <mcc/mcc.scad>

MCC_PANEL_PART_FIELDS = ["hole_d", "depth", "max_panel_t", "plug_len", "bend", "kind", "confidence"];

for (row = MCC_PANEL_PARTS) {
    part = row[0];
    rec  = row[1];
    for (f = MCC_PANEL_PART_FIELDS) {
        assert(struct_val(rec, f) != undef,
            str("mcc test_constants: panel part \"", part, "\" missing field \"", f, "\""));
    }
}

// mcc_bay_depth(part) = mcc_panel_depth(part) + mcc_plug_len(part). architecture.md:294-295.
// NAHDMI-W-B: 40.65 (knowledge/neutrik/placement-and-depth.md:14) + 35 (brief's instruction) = 75.65.
assert(mcc_bay_depth("NAHDMI-W-B") == 75.65,
    str("mcc test_constants: mcc_bay_depth(\"NAHDMI-W-B\") = ", mcc_bay_depth("NAHDMI-W-B"), ", expected 75.65"));

// Cutout diameter ranges (architecture.md:346, this repo's neutrik.scad module contract):
// 24.0-class parts (etherCON): 24.0 <= cutout_d <= 24.6.
assert(mcc_cutout_d("NE8FDP-B") >= 24.0 && mcc_cutout_d("NE8FDP-B") <= 24.6,
    str("mcc test_constants: NE8FDP-B cutout_d out of range: ", mcc_cutout_d("NE8FDP-B")));
// 23.6-class parts (HDMI/USB/BNC): 23.6 <= cutout_d <= 24.2.
assert(mcc_cutout_d("NAHDMI-W-B") >= 23.6 && mcc_cutout_d("NAHDMI-W-B") <= 24.2,
    str("mcc test_constants: NAHDMI-W-B cutout_d out of range: ", mcc_cutout_d("NAHDMI-W-B")));
assert(mcc_cutout_d("NAUSB-W-B") >= 23.6 && mcc_cutout_d("NAUSB-W-B") <= 24.2,
    str("mcc test_constants: NAUSB-W-B cutout_d out of range: ", mcc_cutout_d("NAUSB-W-B")));
assert(mcc_cutout_d("NBB75DFGB") >= 23.6 && mcc_cutout_d("NBB75DFGB") <= 24.2,
    str("mcc test_constants: NBB75DFGB cutout_d out of range: ", mcc_cutout_d("NBB75DFGB")));

// D-13 (layout-patch-wall.md rev 3 §7.1/§11): MCC_GAP_FAR and MCC_SIDE_BOLT_PROUD are DERIVED, not
// chosen -- pin their evaluated values here so a future edit to any input constant that silently
// drifts the flush design (T1-29) is caught at smoke-test time, not only at render time.
assert(MCC_GAP_FAR == 16.0,
    str("mcc test_constants: MCC_GAP_FAR = ", MCC_GAP_FAR, ", expected 16.0 (D-13)"));
assert(MCC_SIDE_BOLT_PROUD == 0.0,
    str("mcc test_constants: MCC_SIDE_BOLT_PROUD = ", MCC_SIDE_BOLT_PROUD, ", expected 0.0 (D-13, flush)"));

// D-12 (layout-patch-wall.md §4/§11): MCC_END_ZONE_NEG_EXTRA_SPLITTER is DERIVED from
// MCC_SPLITTERS[MCC_SPLITTER_DEFAULT].size[2], not hard-typed -- pin it too.
assert(MCC_END_ZONE_NEG_EXTRA_SPLITTER == 20.0,
    str("mcc test_constants: MCC_END_ZONE_NEG_EXTRA_SPLITTER = ", MCC_END_ZONE_NEG_EXTRA_SPLITTER,
        ", expected 20.0 (", MCC_SPLITTER_DEFAULT, " default)"));

// Fans (architecture.md §13 D23, issue #36): MCC_FAN_DEFAULT/MCC_FAN_INTAKE_CLR/MCC_FAN_BAY_CLR are
// read by both fan.scad and layout.scad -- pin them, and pin mcc_fan_spec()'s lookup for both
// MCC_FANS rows.
assert(MCC_FAN_DEFAULT == "NF-A4x10",
    str("mcc test_constants: MCC_FAN_DEFAULT = ", MCC_FAN_DEFAULT, ", expected \"NF-A4x10\""));
assert(MCC_FAN_INTAKE_CLR == 5.0,
    str("mcc test_constants: MCC_FAN_INTAKE_CLR = ", MCC_FAN_INTAKE_CLR, ", expected 5.0"));
assert(MCC_FAN_BAY_CLR == 2.0,
    str("mcc test_constants: MCC_FAN_BAY_CLR = ", MCC_FAN_BAY_CLR, ", expected 2.0"));
assert(struct_val(mcc_fan_spec(MCC_FAN_DEFAULT), "frame") == [40, 40, 10],
    str("mcc test_constants: mcc_fan_spec(MCC_FAN_DEFAULT) frame = ",
        struct_val(mcc_fan_spec(MCC_FAN_DEFAULT), "frame"), ", expected [40,40,10]"));
assert(struct_val(mcc_fan_spec("NF-A6x25"), "frame") == [60, 60, 25],
    str("mcc test_constants: mcc_fan_spec(\"NF-A6x25\") frame = ",
        struct_val(mcc_fan_spec("NF-A6x25"), "frame"), ", expected [60,60,25]"));

echo(str("mcc test_constants: MCC_GAP_FAR=", MCC_GAP_FAR,
    " MCC_SIDE_BOLT_PROUD=", MCC_SIDE_BOLT_PROUD,
    " MCC_END_ZONE_NEG_EXTRA_SPLITTER=", MCC_END_ZONE_NEG_EXTRA_SPLITTER,
    " MCC_SPLITTER_DEFAULT=", MCC_SPLITTER_DEFAULT,
    " MCC_FAN_DEFAULT=", MCC_FAN_DEFAULT,
    " MCC_FAN_INTAKE_CLR=", MCC_FAN_INTAKE_CLR,
    " MCC_FAN_BAY_CLR=", MCC_FAN_BAY_CLR));

echo("mcc test_constants: OK");

// vim: expandtab tabstop=4 shiftwidth=4 softtabstop=4 nowrap
