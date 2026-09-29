//////////////////////////////////////////////////////////////////////
// LibFile: mcc/poe_splitter.scad
//   L1. PoE splitter spec lookup and its bay envelope module. NOT the reservation: the reservation
//   of record is mcc_case_layout()'s splitter_bay_x/y/z (architecture.md §6); the envelope is a plain
//   cube not yet gated as a review ghost (architecture.md §13 D24, open). The zip-tie slots were
//   retired (D65.1).
//   knowledge/components/poe-splitters.md. `use`d by lib/mcc/mcc.scad.
// Includes:
//   include <mcc/mcc.scad>
//////////////////////////////////////////////////////////////////////

include <BOSL2/std.scad>
include <constants.scad>
use <util.scad>

// Function: mcc_splitter_spec()
// Usage:
//   spec = mcc_splitter_spec(name);
// Description:
//   Looks up a splitter record (size/weight_g/cable_allow) from MCC_SPLITTERS (constants.scad).
function mcc_splitter_spec(name) =
    let(ind = search([name], MCC_SPLITTERS)[0])
    assert(ind != [], str("mcc: unknown splitter \"", name, "\""))
    MCC_SPLITTERS[ind][1];

// Module: mcc_splitter_envelope()
// Usage:
//   mcc_splitter_envelope([name=], [orient=], [cable_allow=]);
// Description:
//   Pure keep-out reservation box, base at Z=0 growing toward +Z. architecture.md:234-238
//   reservation rule.
//   `orient` (added — D7, architecture.md §13, approved L1 change per
//   layout-patch-wall.md §15 ruling 7): "flat" is the pre-existing mapping (size[0]/L -> X,
//   size[1]/W -> Y, size[2]/H -> Z); "edge" is layout-patch-wall.md §5's on-edge mapping
//   (size[2]/H -> X, size[0]/L -> Y, size[1]/W -> Z — "the only orientation of a 75x40x20 slab
//   that fits a 45 mm interior at all"). Getting this wrong is exactly deviation D7: a naive flat
//   call for the PoE-splitter bay reserves a box on the wrong axes entirely.
//   `cable_allow` (added — same ruling) toggles whether the splitter's own RJ45 cable allowance is
//   added to its long axis (size[0], wherever that axis lands for the chosen `orient`). Default
//   true preserves this module's original "flat" behaviour; layout-patch-wall.md §5's on-edge
//   *reservation* bay itself carries no cable-allowance term (`bay_y = [...,+env[0]]`, no
//   `+2*cable_allow`), so a caller reserving that exact bay passes `cable_allow=false`.
// Arguments:
//   name        = splitter name, key into MCC_SPLITTERS. Default: MCC_SPLITTER_DEFAULT
//                 ("DONGLE-75x40x20", constants.scad — user decision 2026-09-07: the "GAT-USBC"
//                 placeholder does not fit the single-patch-wall layout at all, architecture.md
//                 §11 R11). D-12 (layout-patch-wall.md §4/§11) derives
//                 MCC_END_ZONE_NEG_EXTRA_SPLITTER from the same named constant, so this module and
//                 the end-zone term it feeds can never disagree about which part is the default.
//   orient      = "flat" (default, back-compat) or "edge" (layout-patch-wall.md §5).
//   cable_allow = whether to inflate the long axis by 2x the splitter's own cable_allow figure.
//                 Default: true (back-compat for "flat"; pass false for the §5 on-edge bay).
module mcc_splitter_envelope(name = MCC_SPLITTER_DEFAULT, orient = "flat", cable_allow = true) {
    assert(orient == "flat" || orient == "edge",
        str("mcc: mcc_splitter_envelope orient must be \"flat\" or \"edge\", got \"", orient, "\""));
    spec  = mcc_splitter_spec(name);
    size  = struct_val(spec, "size");
    allow = struct_val(spec, "cable_allow");
    // dims = the on-floor/on-wall footprint mapped from the splitter's own [L,W,H] record.
    // "flat": L->X, W->Y, H->Z (pre-existing). "edge": H->X, L->Y, W->Z (layout-patch-wall.md §5).
    dims = (orient == "flat") ? [size[0], size[1], size[2]] : [size[2], size[0], size[1]];
    // The splitter's own long/cabled axis (size[0], where its two RJ45 leads run) lands on X in
    // "flat" and on Y in "edge".
    long_idx = (orient == "flat") ? 0 : 1;
    total = [for (i = [0:1:2]) (cable_allow && i == long_idx) ? dims[i] + 2 * allow : dims[i]];
    translate([0, 0, total[2] / 2])
        cube(total, center = true);
}

// vim: expandtab tabstop=4 shiftwidth=4 softtabstop=4 nowrap
