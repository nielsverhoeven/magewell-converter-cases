//////////////////////////////////////////////////////////////////////
// LibFile: mcc/fasteners.scad
//   L1. Heat-set insert bosses/bores, captive thumbscrew holes, the 1/4"-20 tripod boss, and a
//   generic M4 clearance hole. knowledge/components/fasteners-and-hardware.md §1-2.
//   `use`d by lib/mcc/mcc.scad.
// Includes:
//   include <mcc/mcc.scad>
//////////////////////////////////////////////////////////////////////

include <BOSL2/std.scad>
include <constants.scad>
use <util.scad>

// Z-axis convention: a boss stands with its base at Z=0 and grows to Z=h (anchor=BOTTOM); a
// panel/lid feature (mcc_captive_thumbscrew_hole) spans Z=[0, lid_t] with the outward face at
// Z=lid_t, matching lib/mcc/neutrik.scad's own convention.

// Module: mcc_heat_set_bore()
// Usage:
//   mcc_heat_set_bore([insert=]);
// Description:
//   Negative (subtractive) blind bore for a heat-set insert. Local frame: the open face is at
//   Z=0 (place with `translate([x,y,z_of_open_face]) mcc_heat_set_bore(...)`), extending blind
//   into -Z by `insert.len + 1` mm.
// Arguments:
//   insert = insert record (constants.scad MCC_INSERT_M3 shape: hole_d/od/len). Default: MCC_INSERT_M3.
module mcc_heat_set_bore(insert = MCC_INSERT_M3) {
    insert_hole_d = struct_val(insert, "hole_d");
    insert_len    = struct_val(insert, "len");
    // MCC_INSERT_M3 len (5.7, knowledge/components/fasteners-and-hardware.md:17) + 1 mm clearance
    // past the insert's own length, per this file's module contract.
    depth = insert_len + 1;
    translate([0, 0, MCC_EPS - depth / 2])
        cyl(h = depth + 2 * MCC_EPS, d = insert_hole_d, circum = true, $fn = 64);
}

// Module: mcc_heat_set_boss()
// Usage:
//   mcc_heat_set_boss([insert=], h, [od=]);
// Description:
//   Additive boss (base at Z=0, top at Z=h) with an integral blind heat-set-insert bore opening
//   at the top. Asserts the OD/insert-OD ratio and the minimum 2 mm wall around the bore
//   (architecture.md:348 "heat-set boss OD >= 1.8 x insert OD, >= 2 mm material to any edge").
// Arguments:
//   insert = insert record. Default: MCC_INSERT_M3.
//   h      = boss height, mm (required — must be >= insert.len + 1).
//   od     = boss outer diameter override, mm. Default: MCC_BOSS_MIN_RATIO * insert OD.
module mcc_heat_set_boss(insert = MCC_INSERT_M3, h, od = undef) {
    insert_od     = struct_val(insert, "od");
    insert_hole_d = struct_val(insert, "hole_d");
    insert_len    = struct_val(insert, "len");
    _od   = is_undef(od) ? MCC_BOSS_MIN_RATIO * insert_od : od;
    depth = insert_len + 1;

    assert(_od >= MCC_BOSS_MIN_RATIO * insert_od,
        str("mcc: heat_set_boss od=", _od, " below minimum ", MCC_BOSS_MIN_RATIO, "x insert OD (", insert_od, ")"));
    wall = (_od - insert_hole_d) / 2;
    assert(wall >= 2,
        str("mcc: heat_set_boss wall=", wall, " below minimum 2 mm around the bore"));
    assert(h >= depth,
        str("mcc: heat_set_boss h=", h, " shorter than required bore depth ", depth));

    difference() {
        cyl(h = h, d = _od, circum = true, anchor = BOTTOM, $fn = 64);
        translate([0, 0, h]) mcc_heat_set_bore(insert);
    }
}

// Module: mcc_captive_thumbscrew_hole()
// Usage:
//   mcc_captive_thumbscrew_hole([d=], [head_d=], lid_t);
// Description:
//   Negative: a full-depth shaft clearance hole plus an outward-face counterbore sized so a
//   knurled M3 thumbscrew's head cannot pull all the way through the lid (stays captive when
//   backed out). knowledge/components/fasteners-and-hardware.md:97 "M3 knurled thumb screw ...
//   tool-less panel access"; counterbore depth is assumed at half the lid thickness (no sourced
//   figure for this specific geometry) — smallest reasonable choice, confidence assumed.
//   TODO(teamlead): confirm counterbore depth against a physical knurled M3 thumbscrew's head
//   height before finalizing the lid design.
// Arguments:
//   d      = shaft clearance diameter, mm. Default: MCC_M3_CLR_D.
//   head_d = counterbore (head-trap) diameter, mm. Default: 8 (assumed — a typical M3 knurled
//            thumbscrew head is 6-8 mm per generic hardware guides, no sourced figure in
//            knowledge/components/fasteners-and-hardware.md).
//   lid_t  = lid thickness at this location, mm (required).
module mcc_captive_thumbscrew_hole(d = MCC_M3_CLR_D, head_d = 8, lid_t) {
    assert(head_d > d, str("mcc: head_d=", head_d, " must exceed shaft clearance d=", d));
    counterbore_depth = lid_t / 2; // assumed — see TODO above.
    assert(counterbore_depth < lid_t,
        str("mcc: counterbore_depth=", counterbore_depth, " must be less than lid_t=", lid_t));

    union() {
        translate([0, 0, -MCC_EPS])
            cyl(h = lid_t + 2 * MCC_EPS, d = d, circum = true, anchor = BOTTOM, $fn = 64);
        translate([0, 0, lid_t - counterbore_depth])
            cyl(h = counterbore_depth + MCC_EPS, d = head_d, circum = true, anchor = BOTTOM, $fn = 64);
    }
}

// Module: mcc_tripod_boss()
// Usage:
//   mcc_tripod_boss(h, [od=]);
// Description:
//   Additive boss (base at Z=0, top at Z=h) with a through-hole clearance for a 1/4"-20 tripod
//   bolt. architecture.md:116 "the literal 1/4"-20 thread, which is modelled by a named constant".
// Arguments:
//   h  = boss height, mm (required).
//   od = boss outer diameter override, mm. Default: MCC_TRIPOD_CLR_D + 6 (assumed 3 mm minimum
//        wall each side — no sourced figure for this specific boss; smallest-reasonable-choice
//        placeholder pending a physical load test).
module mcc_tripod_boss(h, od = undef) {
    _od = is_undef(od) ? MCC_TRIPOD_CLR_D + 6 : od;
    assert((_od - MCC_TRIPOD_CLR_D) / 2 >= 3,
        str("mcc: tripod boss wall below 3 mm minimum (od=", _od, ")"));
    difference() {
        cyl(h = h, d = _od, circum = true, anchor = BOTTOM, $fn = 64);
        translate([0, 0, -MCC_EPS])
            cyl(h = h + 2 * MCC_EPS, d = MCC_TRIPOD_CLR_D, circum = true, anchor = BOTTOM, $fn = 64);
    }
}

// Module: mcc_m4_hole()
// Usage:
//   mcc_m4_hole([h=]);
// Description:
//   Generic M4 clearance through-hole, base at Z=0 growing toward +Z. Used by the (not-yet-built)
//   floor VESA/Fishtail M4 pattern and any other generic M4 clearance need.
// Arguments:
//   h = hole length, mm. Default: 20 (assumed — generous enough to guarantee a clean through-cut
//       through any wall/floor/boss stack in this repo; override per call site).
module mcc_m4_hole(h = 20) {
    translate([0, 0, -MCC_EPS])
        cyl(h = h + 2 * MCC_EPS, d = MCC_M4_CLR_D, circum = true, anchor = BOTTOM, $fn = 64);
}

// vim: expandtab tabstop=4 shiftwidth=4 softtabstop=4 nowrap
