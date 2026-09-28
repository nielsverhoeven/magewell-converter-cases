//////////////////////////////////////////////////////////////////////
// tests/test_neutrik.scad
//   Tier-2 headless smoke test (architecture.md §9). Instantiates mcc_neutrik_d_cutout(),
//   mcc_thread_pad() and the wall-integrated mcc_neutrik_d_wall_cut() / mcc_panel_wall_cut() (D36)
//   at default, minimum, and maximum parameters.
//   CSG export (-o out.csg) evaluates the full tree so in-model asserts fire, without
//   tessellating (architecture.md:353-355).
// Run:
//   openscad --backend=Manifold -o out.csg tests/test_neutrik.scad
//////////////////////////////////////////////////////////////////////

$fa = 1; $fs = 0.4;

include <mcc/mcc.scad>

// --- Default parameters -------------------------------------------------------------------
// T1-42a/b/c (architecture.md rev 10, GitHub issue #30): mcc_thread_pad()'s printed M3x0.5
// thread -- pad wall, engaged turns, and residual radial engagement vs $slop all self-assert.
mcc_neutrik_d_cutout("NE8FDP-B");
mcc_neutrik_d_flange_outline();

// --- Minimum-ish parameters: seat_t == panel_t (no rear pocket cut at all), AND the shortest
// pad_h that still satisfies T1-42b's >=3-turn floor exactly ------------------------------
translate([40, 0, 0])
    mcc_neutrik_d_cutout("NAHDMI-W-B", mirror = true, seat_t = 1.0, panel_t = 1.0);
translate([40, 0, 0])
    // pad_h at the T1-42b boundary: chamfer + MIN_TURNS*pitch = 0.5 + 3*0.5 = 2.0.
    mcc_thread_pad(pad_h = MCC_THREAD_M3_CHAMFER + MCC_THREAD_ENGAGE_MIN_TURNS * MCC_THREAD_M3_PITCH);

// --- Maximum-ish parameters: etherCON at its full 4 mm panel-thickness rating, AND a long pad_h
// well past the production default -- exercises a long threaded bore -----------------------
translate([80, 0, 0])
    mcc_neutrik_d_cutout("NE8FDP-B", mirror = false, seat_t = 2.0, panel_t = 4.0);
translate([80, 0, 0])
    mcc_thread_pad(pad_h = 12);

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

// --- Wall-integrated connector cut (D36): every part class at the production wall (seat 2 +
// lip 3), the blank, and the thinnest wall that still gives T1-42b's 3 turns. The T1-48 web and
// T1-34a bridge asserts fire inside the module. Differenced from a block so the thread renders
// as a real negative. --------------------------------------------------------------------
for (i = [0:1:3])
    translate([i * 40, 60, 0])
        difference() {
            translate([0, 0, -2.5]) cube([36, 40, 5], center = true);
            mcc_panel_wall_cut(["NE8FDP-B", "NAHDMI-W-B", "NAUSB-W-B", "DBA-BL-B"][i], wall_t = 5);
        }
translate([0, 110, 0])
    mcc_neutrik_d_wall_cut("NBB75DFGB", wall_t = MCC_THREAD_M3_CHAMFER + MCC_THREAD_ENGAGE_MIN_TURNS * MCC_THREAD_M3_PITCH + 0.5,
        seat_t = 1.0, fast = true);

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
