//////////////////////////////////////////////////////////////////////
// LibFile: mcc/util.scad
//   L0. Generic helpers: range asserts, warnings, small geometry, bbox check.
//   `use`d (not `include`d) by lib/mcc/mcc.scad per architecture.md:93.
// Includes:
//   include <mcc/mcc.scad>
//////////////////////////////////////////////////////////////////////

include <BOSL2/std.scad>
include <constants.scad>

// Function: mcc_assert_range()
// Usage:
//   v2 = mcc_assert_range(name, v, lo, hi);
// Description:
//   Asserts lo <= v <= hi, naming `name` and the offending value in the failure message, then
//   passes `v` through unchanged so the call can be inlined at the point of use
//   (architecture.md §9 Tier-1: "in-model assert(), runs on every render, free").
function mcc_assert_range(name, v, lo, hi) =
    assert(is_num(v), str("mcc: ", name, " must be a number, got ", v))
    assert(v >= lo && v <= hi,
        str("mcc: ", name, " = ", v, " out of range [", lo, ", ", hi, "]"))
    v;

// Function: mcc_warn()
// Usage:
//   dummy = mcc_warn(msg);
// Description:
//   Emits `WARNING: <msg>` via echo() and returns undef. OpenSCAD statements must be an
//   assignment/echo/assert/module — this is a *function* (per structs.scad's own echo_struct()
//   pattern) so callers bind the (unused) result, e.g. `_ = mcc_warn("...");`.
function mcc_warn(msg) =
    echo(str("WARNING: ", msg))
    undef;

// Function: mcc_bbox_ok()
// Usage:
//   ok = mcc_bbox_ok(size);
// Description:
//   Returns true if every element of `size` (a 2- or 3-vector, mm) is <= the printable envelope
//   (MCC_BUILD - MCC_BED_MARGIN). architecture.md:341 "bbox <= MCC_BUILD - MCC_BED_MARGIN per part".
function mcc_bbox_ok(size) =
    let(lim = MCC_BUILD - MCC_BED_MARGIN)
    [for (i = [0:1:len(size) - 1]) if (size[i] > lim) i] == [];

// Module: mcc_rounded_rect()
// Usage:
//   mcc_rounded_rect(size, r);
// Description:
//   2D rounded-rectangle helper, centered on the origin. Thin wrapper over BOSL2's rect() so
//   callers don't need to remember the `rounding=` argument name everywhere it is used
//   (flange outlines, panel plates, tile coupons).
// Arguments:
//   size = [w, h] rectangle size, mm.
//   r    = corner rounding radius, mm.
module mcc_rounded_rect(size, r) {
    rect(size, rounding = r);
}

// vim: expandtab tabstop=4 shiftwidth=4 softtabstop=4 nowrap
