//////////////////////////////////////////////////////////////////////
// LibFile: mcc/poe_splitter.scad
//   L1. PoE splitter bay envelope (reservation keep-out) and zip-tie down slots.
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
    // "flat" and on Y in "edge" — same mapping used by mcc_splitter_tiedown() below, so the two
    // modules never disagree about where the splitter body sits.
    long_idx = (orient == "flat") ? 0 : 1;
    total = [for (i = [0:1:2]) (cable_allow && i == long_idx) ? dims[i] + 2 * allow : dims[i]];
    translate([0, 0, total[2] / 2])
        cube(total, center = true);
}

// Module: mcc_splitter_tiedown()
// Usage:
//   mcc_splitter_tiedown([name=], [floor_t=], [orient=]);
// Description:
//   Negative: two zip-tie slots through the floor, one on each side of the splitter footprint's
//   SHORT floor-plane axis, centered along its LONG axis, so a tie can loop over the splitter body
//   and cinch down through both slots. Slot size per the brief's explicit instruction, "4 x 1.5mm"
//   — no sourced figure exists for this project-specific feature; treated as a fixed constant of
//   this module's contract rather than derived from
//   knowledge/components/fasteners-and-hardware.md's generic cable-tie width table
//   (fasteners-and-hardware.md:219-221), which covers stock tie widths, not slot geometry.
//   `orient` (added — D7/ruling 7, same rationale as mcc_splitter_envelope()) selects the same
//   "flat"/"edge" axis mapping as that module, so the two never disagree about where the splitter
//   body — and therefore where the tie-down slots relative to it — actually sit.
// Arguments:
//   name    = splitter name, key into MCC_SPLITTERS. Default: MCC_SPLITTER_DEFAULT (matches
//             mcc_splitter_envelope()'s default — see the rationale there).
//   floor_t = floor thickness at the tie-down location, mm. Default: MCC_FLOOR_T.
//   orient  = "flat" (default, back-compat) or "edge" (layout-patch-wall.md §5).
module mcc_splitter_tiedown(name = MCC_SPLITTER_DEFAULT, floor_t = MCC_FLOOR_T, orient = "flat") {
    assert(orient == "flat" || orient == "edge",
        str("mcc: mcc_splitter_tiedown orient must be \"flat\" or \"edge\", got \"", orient, "\""));
    spec   = mcc_splitter_spec(name);
    size   = struct_val(spec, "size");
    // Same dims mapping as mcc_splitter_envelope() above.
    dims   = (orient == "flat") ? [size[0], size[1], size[2]] : [size[2], size[0], size[1]];
    slot_l = 4;   // zip-tie slot length (along the splitter's own long axis), mm.
    slot_w = 1.5; // zip-tie slot width (across, on the short floor-plane axis), mm.
    cut_h  = floor_t + 2 * MCC_EPS;

    // "flat": long axis = X (dims[0]), short = Y (dims[1]) -- slots at y=+-short/2, spanning X.
    // "edge": long axis = Y (dims[1]), short = X (dims[0]) -- slots at x=+-short/2, spanning Y.
    if (orient == "flat") {
        for (s = [-1, 1])
            translate([0, s * dims[1] / 2, floor_t / 2])
                cube([slot_l, slot_w, cut_h], center = true);
    } else {
        for (s = [-1, 1])
            translate([s * dims[0] / 2, 0, floor_t / 2])
                cube([slot_w, slot_l, cut_h], center = true);
    }
}

// vim: expandtab tabstop=4 shiftwidth=4 softtabstop=4 nowrap
