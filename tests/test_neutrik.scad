//////////////////////////////////////////////////////////////////////
// tests/test_neutrik.scad
//   Tier-2 headless smoke test (architecture.md §9). Instantiates mcc_neutrik_d_cutout(),
//   mcc_neutrik_d_bosses(), and mcc_panel_plate() at default, minimum, and maximum parameters.
//   CSG export (-o out.csg) evaluates the full tree so in-model asserts fire, without
//   tessellating (architecture.md:353-355).
// Run:
//   openscad --backend=Manifold -o out.csg tests/test_neutrik.scad
//////////////////////////////////////////////////////////////////////

$fa = 1; $fs = 0.4;

include <mcc/mcc.scad>

// --- Default parameters -------------------------------------------------------------------
// T1-42a/b/c (architecture.md rev 10, GitHub issue #30): mcc_neutrik_d_bosses()'s bore is now a
// printed M3x0.5 internal thread via mcc_thread_pad() -- pad wall, engaged turns, and residual
// radial engagement vs $slop all self-assert at the module's own default parameters.
mcc_neutrik_d_cutout("NE8FDP-B");
mcc_neutrik_d_bosses("NE8FDP-B");
mcc_neutrik_d_flange_outline();

// --- Minimum-ish parameters: seat_t == panel_t (no rear pocket cut at all), AND the shortest
// pad_h that still satisfies T1-42b's >=3-turn floor exactly ------------------------------
translate([40, 0, 0])
    mcc_neutrik_d_cutout("NAHDMI-W-B", mirror = true, seat_t = 1.0, panel_t = 1.0);
translate([40, 0, 0])
    // pad_h at the T1-42b boundary: chamfer + MIN_TURNS*pitch = 0.5 + 3*0.5 = 2.0.
    mcc_neutrik_d_bosses("NAHDMI-W-B", mirror = true,
        pad_h = MCC_THREAD_M3_CHAMFER + MCC_THREAD_ENGAGE_MIN_TURNS * MCC_THREAD_M3_PITCH);

// --- Maximum-ish parameters: etherCON at its full 4 mm panel-thickness rating, AND a long pad_h
// well past the production default -- exercises a long threaded bore -----------------------
translate([80, 0, 0])
    mcc_neutrik_d_cutout("NE8FDP-B", mirror = false, seat_t = 2.0, panel_t = 4.0);
translate([80, 0, 0])
    mcc_neutrik_d_bosses("NE8FDP-B", mirror = false, pad_h = 12);

// --- MCC_THREAD_FAST fast-path equivalence: the cheap clearance-bore substitute (production
// toggle: `-D MCC_THREAD_FAST=true`, architect verdict B6) must keep exactly the same pad
// envelope (OD/height) as the real-thread default. Both branches in mcc_thread_pad() share one
// `cyl(h = pad_h, d = pad_d, ...)` outer-solid statement -- only the difference()'d bore differs
// -- so the envelope is identical BY CONSTRUCTION; this instantiates both (via the `fast`
// override, same overridable-default idiom as mcc_ghost(dev, show=MCC_SHOW_GHOST)) so a future
// edit that gives the two branches their own separate outer-cylinder call, and lets them diverge,
// at least renders both paths in one smoke pass. The actual numeric cross-check (bbox
// byte-identical between a MCC_THREAD_FAST=false and =true panel render) is a Tier-3 golden
// comparison, not a Tier-2 assert -- see the PR verification notes.
translate([120, 0, 0]) mcc_thread_pad(fast = false); // real thread (default path)
translate([140, 0, 0]) mcc_thread_pad(fast = true);  // MCC_THREAD_FAST override

// --- Panel plate: single slot and a 2-slot plate at the minimum D-series pitch -------------
translate([0, 60, 0])
    mcc_panel_plate([70, 45], slots = [[0, 0, "NE8FDP-B", false]]);
translate([100, 60, 0])
    mcc_panel_plate([120, 45], slots = [[-40, 0, "NE8FDP-B", false], [40, 0, "NAHDMI-W-B", false]]);

echo("mcc test_neutrik: OK");

// -----------------------------------------------------------------------------------------
// Manual check: deliberately-bad seat thickness (architecture.md:343 Tier-1 assert "panel seat
// thickness <= mcc_panel_max_t(part)"). OpenSCAD has no "expect this render to fail" mechanism,
// so this cannot be asserted automatically in a render that must otherwise succeed. To verify the
// guard by hand, append the following line to a scratch copy of this file and confirm the render
// FAILS (non-zero exit, an ERROR naming "seat_t=3 exceeds max panel thickness 2 for
// \"NAHDMI-W-B\"") — NAHDMI-W-B's max_panel_t is 2.0 mm
// (knowledge/neutrik/d-series-cutout.md:90 "max. 2 mm"), so a requested 3 mm seat must be
// rejected:
//
//   mcc_neutrik_d_cutout("NAHDMI-W-B", seat_t = 3.0, panel_t = 3.0);
// -----------------------------------------------------------------------------------------

// vim: expandtab tabstop=4 shiftwidth=4 softtabstop=4 nowrap
