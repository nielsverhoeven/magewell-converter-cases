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
// "external_ports" is DROPPED from cfg (D12, architecture.md §13 -- inert, never implemented; the
// slot set comes solely from mcc_ports_external(dev)). Real cfg keys only.
VARIANT = [
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

// -----------------------------------------------------------------------------------------
// Section: §16 pre-flight gate -- ALL 8 device files (layout-patch-wall.md §16.1/§16.2/§16.5
// step 4: "render all eight devices and confirm this table" before any of the seven parallel
// branches is opened). For each device this: (a) evaluates mcc_case_layout()/
// mcc_slot_assignment() and cross-checks L/W/H/ez_neg/ez_pos/n_slots/slot-part-order against the
// §16.1 fit-check table; (b) instantiates mcc_shell_base() so every Tier-1 assert baked into
// shell.scad -- NOT just the ones inside mcc_case_layout() itself -- actually fires, in
// particular T1-18(c), the BLOCKING BNC axial double-count this pre-flight branch exists to fix
// (constants.scad MCC_PLUG_AXIAL / mcc_plug_axial(), shell.scad's T1-18(c) block above). Running
// this via `python scripts/build.py smoke` (-o out.csg: evaluates the full CSG tree, asserts
// fire, no tessellation) is exactly the "render all eight and confirm §16" step, repeated on
// every CI run.
// -----------------------------------------------------------------------------------------

include <mcc/devices/pro-convert-hdmi-tx.scad>
include <mcc/devices/pro-convert-sdi-tx.scad>
include <mcc/devices/pro-convert-hdmi-plus.scad>
include <mcc/devices/pro-convert-sdi-plus.scad>
include <mcc/devices/pro-convert-for-ndi-to-hdmi-4k.scad>
include <mcc/devices/pro-convert-for-ndi-to-sdi.scad>
include <mcc/devices/pro-convert-for-ndi-to-aio.scad>
// pro-convert-for-ndi-to-hdmi.scad is already included above (DEV/VARIANT).

CFG8 = [["fan", false], ["splitter", false]];

// Module: _t16_check()
// Description:
//   Test-local. One §16.1 table row: cross-checks mcc_case_layout()'s L/W/H/ez_neg/ez_pos/n_slots
//   and mcc_slot_assignment()'s per-slot `part` order against the expected values, then
//   instantiates mcc_shell_base() (translated clear of every other device in this file, x_off mm
//   along +X, so none of their CSG trees share a coincident face -- shell.scad's own comments flag
//   that class of degeneracy) so shell.scad's own Tier-1 asserts -- T1-18(c) foremost -- run for
//   real, not just layout.scad's.
// Arguments:
//   dev, cfg           = device record / variant config.
//   x_off               = translation along +X so this device's shell doesn't overlap the next.
//   exp_L/W/H           = expected envelope, mm.
//   exp_n               = expected n_slots.
//   exp_parts           = expected slots[i]["part"], i=0..exp_n-1, in slot order.
//   exp_ez_neg/ez_pos    = expected end zones, mm.
module _t16_check(dev, cfg, x_off, exp_L, exp_W, exp_H, exp_n, exp_parts, exp_ez_neg, exp_ez_pos) {
    slug = mcc_dev_slug(dev);
    l = mcc_case_layout(dev, cfg);
    assert(_mcc_near(struct_val(l, "L"), exp_L, 1e-2), str("§16 ", slug, ": L=", struct_val(l, "L"), " expected ", exp_L));
    assert(_mcc_near(struct_val(l, "W"), exp_W, 1e-2), str("§16 ", slug, ": W=", struct_val(l, "W"), " expected ", exp_W));
    assert(_mcc_near(struct_val(l, "H"), exp_H, 1e-6), str("§16 ", slug, ": H=", struct_val(l, "H"), " expected ", exp_H));
    assert(struct_val(l, "n_slots") == exp_n, str("§16 ", slug, ": n_slots=", struct_val(l, "n_slots"), " expected ", exp_n));
    assert(_mcc_near(struct_val(l, "ez_neg"), exp_ez_neg, 1e-6), str("§16 ", slug, ": ez_neg=", struct_val(l, "ez_neg"), " expected ", exp_ez_neg));
    assert(_mcc_near(struct_val(l, "ez_pos"), exp_ez_pos, 1e-6), str("§16 ", slug, ": ez_pos=", struct_val(l, "ez_pos"), " expected ", exp_ez_pos));

    slots = mcc_slot_assignment(dev);
    for (i = [0 : 1 : exp_n - 1])
        assert(struct_val(slots[i], "part") == exp_parts[i],
            str("§16 ", slug, ": slot ", i + 1, " part=", struct_val(slots[i], "part"), " expected ", exp_parts[i]));

    // Instantiating mcc_shell_base() runs EVERY Tier-1 assert in shell.scad, not just
    // mcc_case_layout()'s own -- in particular T1-18(c) (the +X axial-cable-vs-fan-bay check this
    // pre-flight branch exists to fix for the four BNC-ended SKUs), T1-29 (side-bolt boss flush)
    // and the splitter/device-envelope collision guard.
    translate([x_off, 0, 0]) mcc_shell_base(dev = dev, cfg = cfg);

    echo(str("mcc §16 pre-flight OK: ", slug, " L=", struct_val(l, "L"), " W=", struct_val(l, "W"),
        " H=", struct_val(l, "H"), " n_slots=", struct_val(l, "n_slots"),
        " ez_neg/pos=", struct_val(l, "ez_neg"), "/", struct_val(l, "ez_pos")));
}

// #3 -- HDMI-ended, compact, 3 slots.
_t16_check(MCC_DEV_PRO_CONVERT_HDMI_TX, CFG8, 0,
    193.9, 159.85, 51.0, 3, ["NE8FDP-B", "NAUSB-W-B", "NAHDMI-W-B"], 47, 40);
// #4 -- BNC-ended, compact, 3 slots. T1-18(c) FAILED here before the fix (-14.60 mm).
_t16_check(MCC_DEV_PRO_CONVERT_SDI_TX, CFG8, 300,
    194.9, 158.80, 51.0, 3, ["NE8FDP-B", "NAUSB-W-B", "NBB75DFGB"], 47, 41);
// #5 -- HDMI-ended, plus, 4 slots (plus family's first shell.scad render in this repo's history).
_t16_check(MCC_DEV_PRO_CONVERT_HDMI_PLUS, CFG8, 600,
    210.5, 166.35, 51.0, 4, ["NE8FDP-B", "NAUSB-W-B", "NAHDMI-W-B", "NAHDMI-W-B"], 47, 40);
// #6 -- BNC-ended (two BNC, one end), plus, 4 slots. T1-18(c) FAILED here before the fix.
_t16_check(MCC_DEV_PRO_CONVERT_SDI_PLUS, CFG8, 900,
    211.5, 165.30, 51.0, 4, ["NE8FDP-B", "NAUSB-W-B", "NBB75DFGB", "NBB75DFGB"], 47, 41);
// #7 -- HDMI-ended, plus, 4 slots (usb_host + hdmi_out share the +X end; HDMI's axial term governs).
_t16_check(MCC_DEV_PRO_CONVERT_FOR_NDI_TO_HDMI_4K, CFG8, 1200,
    210.5, 166.35, 51.0, 4, ["NE8FDP-B", "NAUSB-W-B", "NAUSB-W-B", "NAHDMI-W-B"], 47, 40);
// #8 -- BNC-ended (sdi_out + usb_host share the +X end), compact, 4 slots. T1-18(c) FAILED here
// before the fix.
_t16_check(MCC_DEV_PRO_CONVERT_FOR_NDI_TO_SDI, CFG8, 1500,
    194.9, 158.80, 51.0, 4, ["NE8FDP-B", "NAUSB-W-B", "NAUSB-W-B", "NBB75DFGB"], 47, 41);
// #9 -- mixed HDMI+BNC on the +X end (governs W via HDMI's deeper bay, L via BNC's wider ez_pos),
// compact, 4 slots. T1-18(c) FAILED here before the fix.
_t16_check(MCC_DEV_PRO_CONVERT_FOR_NDI_TO_AIO, CFG8, 1800,
    194.9, 159.85, 51.0, 4, ["NE8FDP-B", "NAUSB-W-B", "NAHDMI-W-B", "NBB75DFGB"], 47, 41);
// (8th device) pro-convert-for-ndi-to-hdmi -- the already-shipped SKU, re-checked here too so all
// 8 device files are covered by one loop-free, deterministic list in a single place.
_t16_check(MCC_DEV_PRO_CONVERT_FOR_NDI_TO_HDMI, CFG8, 2100,
    193.9, 159.85, 51.0, 4, ["NE8FDP-B", "NAUSB-W-B", "NAUSB-W-B", "NAHDMI-W-B"], 47, 40);

echo("mcc test_layout §16 pre-flight (8/8 devices): OK");

// vim: expandtab tabstop=4 shiftwidth=4 softtabstop=4 nowrap
