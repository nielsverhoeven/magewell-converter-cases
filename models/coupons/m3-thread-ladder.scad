//////////////////////////////////////////////////////////////////////
// models/coupons/m3-thread-ladder.scad
//   Tier-4 physical coupon (architecture.md §9, GitHub issue #30). 5 printed M3 thread pads at
//   production pad_d/pad_h/$fn (via the same mcc_thread_pad() the connector-fixing boss module
//   calls -- architect verdict B5, a coupon that hand-rebuilds this shape cannot calibrate the
//   production constant it exists to calibrate), sweeping $slop across the architect-corrected
//   ladder [0.02, 0.035, 0.05, 0.065, 0.08] (architecture.md rev 10 B1 -- the plan's original
//   0.05-0.25 sweep put 3 of 5 rungs past the point where BOSL2's 4*$slop diametral growth erases
//   the entire M3x0.5 thread; this range brackets the corrected MCC_THREAD_M3_SLOP default (0.05)
//   from both sides).
//
//   NOTE (flagged for architect/user confirmation, not silently resolved): the mandated top rung
//   (slop=0.08) itself fails T1-42c -- residual radial engagement = 0.2705 - 2*0.08 = 0.1105 mm,
//   below the 0.135 mm (50% of nominal) production floor by 0.0245 mm. T1-42c is a *production*
//   policy assert (mcc_neutrik_d_bosses() always enforces it); this coupon's whole purpose is to
//   physically test rungs on both sides of that floor and read back which one actually strips a
//   real screw, so this file passes mcc_thread_pad(..., enforce_min_radial=false) for every rung
//   -- the only call site in the repo allowed to do so. T1-42a (wall) and T1-42b (turns) still
//   assert normally on every rung (both pass at slop=0.08: wall=2.48mm, turns=13 unaffected).
//
//   Acceptance is >= 5 insert/remove cycles per pad, not a single successful seat (R28) -- a
//   connector gets unscrewed for cable service, and repeat-cycle stripping is exactly the failure
//   mode heat-set inserts existed to prevent. See models/coupons/README.md for the measurement
//   form.
//
// Render:
//   openscad --backend=Manifold -o out/m3-thread-ladder.stl models/coupons/m3-thread-ladder.scad
//////////////////////////////////////////////////////////////////////

$fa = 1; $fs = 0.4;

include <mcc/mcc.scad>

part = "m3-thread-ladder";

SLOPS   = [0.02, 0.035, 0.05, 0.065, 0.08]; // architect-corrected ladder (architecture.md rev 10
                                              // B1) -- brackets MCC_THREAD_M3_SLOP (0.05).
PAD_H   = MCC_THREAD_M3_PAD_H;
PAD_D   = MCC_THREAD_M3_PAD_D;
PITCH   = 16;
BASE_T  = 3.0;
MARGIN  = 8;

n      = len(SLOPS);
base_w = n * PITCH + PITCH;
base_l = PITCH + 2 * MARGIN;

echo(str("m3-thread-ladder: slops=", SLOPS, " pad_d=", PAD_D, " pad_h=", PAD_H));

difference() {
    translate([0, 0, -BASE_T])
        linear_extrude(height = BASE_T)
            square([base_w, base_l]);

    for (i = [0 : 1 : n - 1])
        translate([(i + 1) * PITCH, MARGIN - 2, -0.6])
            linear_extrude(height = 0.6 + MCC_EPS)
                text(str(SLOPS[i]), size = 3.0, halign = "center", valign = "center", font = "Liberation Sans:style=Bold");
}

for (i = [0 : 1 : n - 1])
    // mcc_thread_pad()'s own Z convention (matching the production panel boss) puts the seat face
    // (screw entry) at local Z=0 and grows the pad to Z=-pad_h -- correct when unioned onto a
    // panel's rear face, which sits BELOW the pad. Here the pad must instead sit ON TOP of this
    // coupon's base plate (base spans world Z=[-BASE_T,0], bore facing up per README.md's
    // orientation table), so it is placed at z=PAD_H: local Z=0 (seat) lands at world z=PAD_H (the
    // pad's exposed top, screw enters from above) and local Z=-pad_h (rear tip) lands at world
    // z=0 (flush with the base's own top face) -- contiguous with the base, nothing protrudes
    // below its bed-contact bottom face. (Placing at z=0 instead would drive the pad THROUGH the
    // base and 4 mm out its bottom -- caught by inspecting the required close-up render, not by
    // any Tier-1/2/3 check, since check_mesh's `parts=1` still passes on the wrongly-placed union.)
    translate([(i + 1) * PITCH, base_l - MARGIN, PAD_H])
        // enforce_min_radial=false: see the header note above -- the top rung is a deliberate
        // physical test past the T1-42c production floor, not a bypass of it in production.
        mcc_thread_pad(pad_d = PAD_D, pad_h = PAD_H, slop = SLOPS[i], enforce_min_radial = false);

// vim: expandtab tabstop=4 shiftwidth=4 softtabstop=4 nowrap
