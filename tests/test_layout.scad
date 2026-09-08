//////////////////////////////////////////////////////////////////////
// tests/test_layout.scad
//   Tier-2 headless smoke test (architecture.md §9). Exercises every lib/mcc/layout.scad function
//   against MCC_DEV_PRO_CONVERT_FOR_NDI_TO_HDMI, asserting the computed L/W/H/pitch/x_dev_c/slot
//   order match docs/plans/2026-09-08-l2-first-case.md §2 exactly (within 1e-6), and that the
//   Tier-1 topology asserts baked into mcc_case_layout() actually fire on a real device record.
// Run:
//   openscad --backend=Manifold -o out.csg tests/test_layout.scad
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

function _mcc_near(a, b, tol = 1e-6) = abs(a - b) < tol;

l = mcc_case_layout(DEV, VARIANT);

// --- Envelope (plan §2.1) ---
assert(_mcc_near(struct_val(l, "L"), 193.9), str("L=", struct_val(l, "L"), " expected 193.9"));
assert(_mcc_near(struct_val(l, "W"), 159.85), str("W=", struct_val(l, "W"), " expected 159.85"));
assert(_mcc_near(struct_val(l, "H"), 51.0), str("H=", struct_val(l, "H"), " expected 51.0"));
assert(_mcc_near(struct_val(l, "ez_neg"), 47), str("ez_neg=", struct_val(l, "ez_neg")));
assert(_mcc_near(struct_val(l, "ez_pos"), 40), str("ez_pos=", struct_val(l, "ez_pos")));

// --- Device placement (plan §2.2) ---
assert(_mcc_near(struct_val(l, "x_dev_c"), 3.50), str("x_dev_c=", struct_val(l, "x_dev_c")));
assert(_mcc_near(struct_val(l, "y_dev_c"), -30.825), str("y_dev_c=", struct_val(l, "y_dev_c")));
assert(_mcc_near(struct_val(l, "z_dev_lo"), 13.85), str("z_dev_lo=", struct_val(l, "z_dev_lo")));
assert(_mcc_near(mcc_cradle_deck(DEV), 10.85), str("mcc_cradle_deck=", mcc_cradle_deck(DEV)));

// --- Panel plate / slots (plan §2.3) ---
assert(_mcc_near(struct_val(l, "plate_l"), 167.9), str("plate_l=", struct_val(l, "plate_l")));
assert(struct_val(l, "n_slots") == 4, str("n_slots=", struct_val(l, "n_slots")));
assert(_mcc_near(struct_val(l, "pitch"), 41.9667, 1e-3), str("pitch=", struct_val(l, "pitch")));
slot_x = struct_val(l, "slot_x");
assert(_mcc_near(slot_x[0], -62.95, 1e-3), str("slot_x[0]=", slot_x[0]));
assert(_mcc_near(slot_x[3], 62.95, 1e-3), str("slot_x[3]=", slot_x[3]));

// Slot order (rev-5, layout-patch-wall.md §15 ruling 8 -- the ALGORITHM's output, not the
// (superseded) worked-results table): 1=rj45, 2=usb_b, 3=usb_host, 4=hdmi_out.
assert(mcc_slot_for_port(DEV, "rj45") == 1, "slot(rj45) != 1");
assert(mcc_slot_for_port(DEV, "usb_b") == 2, "slot(usb_b) != 2");
assert(mcc_slot_for_port(DEV, "usb_host") == 3, "slot(usb_host) != 3");
assert(mcc_slot_for_port(DEV, "hdmi_out") == 4, "slot(hdmi_out) != 4");
slots = mcc_slot_assignment(DEV);
assert(struct_val(slots[0], "part") == "NE8FDP-B", "slot 1 part");
assert(struct_val(slots[1], "part") == "NAUSB-W-B", "slot 2 part");
assert(struct_val(slots[2], "part") == "NAUSB-W-B", "slot 3 part");
assert(struct_val(slots[3], "part") == "NAHDMI-W-B", "slot 4 part");

// --- Fan / splitter bay / side-bolt (plan §2.4) ---
assert(_mcc_near(struct_val(l, "fan_pos")[0], 96.95, 1e-3), str("fan_pos.x=", struct_val(l, "fan_pos")[0]));
sbx = struct_val(l, "splitter_bay_x"); sby = struct_val(l, "splitter_bay_y"); sbz = struct_val(l, "splitter_bay_z");
assert(_mcc_near(sbx[0], -93.95, 1e-3) && _mcc_near(sbx[1], -73.95, 1e-3), str("splitter_bay_x=", sbx));
assert(_mcc_near(sby[0], -76.925, 1e-3) && _mcc_near(sby[1], -1.925, 1e-3), str("splitter_bay_y=", sby));
assert(sbz == [3, 43], str("splitter_bay_z=", sbz));
assert(_mcc_near(struct_val(l, "side_bolt_x"), 3.50, 1e-3), str("side_bolt_x=", struct_val(l, "side_bolt_x")));
assert(_mcc_near(struct_val(l, "side_bolt_z"), 25.5, 1e-3), str("side_bolt_z=", struct_val(l, "side_bolt_z")));

// --- Lid fasteners (plan §2.5) ---
assert(struct_val(l, "lid_n_fast") == 6, str("lid_n_fast=", struct_val(l, "lid_n_fast")));
fp = struct_val(l, "lid_fastener_pos");
assert(len(fp) == 6, str("len(lid_fastener_pos)=", len(fp)));
assert(_mcc_near(fp[0][0], 86.95, 1e-3) && _mcc_near(fp[0][1], 69.925, 1e-3), str("fp[0]=", fp[0]));
assert(_mcc_near(fp[4][0], 0, 1e-3) && _mcc_near(fp[4][1], 69.925, 1e-3), str("fp[4] (patch-wall mid)=", fp[4]));
assert(_mcc_near(fp[5][0], -12.64, 1e-2) && _mcc_near(fp[5][1], -69.925, 1e-3), str("fp[5] (far-wall mid)=", fp[5]));

// --- mcc_panel_fixing_pos() matches mcc_panel_plate()'s own already-implemented formula (D6) ---
fix = mcc_panel_fixing_pos([100, 40], 6);
assert(len(fix) == 4);
assert(_mcc_near(fix[0][0], -(100 / 2 - 3)) || _mcc_near(fix[0][0], (100 / 2 - 3)), "mcc_panel_fixing_pos x");

// --- mcc_end_zone() direct calls ---
assert(_mcc_near(mcc_end_zone(DEV, "neg"), 47), str("mcc_end_zone neg=", mcc_end_zone(DEV, "neg")));
assert(_mcc_near(mcc_end_zone(DEV, "pos"), 40), str("mcc_end_zone pos=", mcc_end_zone(DEV, "pos")));

// --- mcc_case_dims() matches mcc_case_layout() ---
dims = mcc_case_dims(DEV, VARIANT);
assert(dims == [struct_val(l, "L"), struct_val(l, "W"), struct_val(l, "H")], str("mcc_case_dims=", dims));

// --- mcc_floor_keepout() is non-nullary and returns a sane list ---
fk = mcc_floor_keepout(DEV, VARIANT);
assert(len(fk) > 0, "mcc_floor_keepout empty");
assert(len([for (f = fk) if (f[4] == "case_tripod_insert") f]) == 1, "case_tripod_insert missing");

echo(str("mcc test_layout: L=", struct_val(l, "L"), " W=", struct_val(l, "W"), " H=", struct_val(l, "H"),
    " n_slots=", struct_val(l, "n_slots"), " pitch=", struct_val(l, "pitch"),
    " x_dev_c=", struct_val(l, "x_dev_c"), " lid_n_fast=", struct_val(l, "lid_n_fast")));
echo("mcc test_layout: OK");

// vim: expandtab tabstop=4 shiftwidth=4 softtabstop=4 nowrap
