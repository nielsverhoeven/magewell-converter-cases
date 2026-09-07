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
//   mcc_splitter_envelope([name=]);
// Description:
//   Pure keep-out reservation box: the splitter's own footprint plus its RJ45 cable allowance
//   applied at BOTH ends along the long (X) axis. architecture.md:234-238 reservation rule — this
//   is the placeholder envelope architecture.md:485-486 flags as pending a final part choice.
// Arguments:
//   name = splitter name, key into MCC_SPLITTERS. Default: "DONGLE-75x40x20" (user decision
//          2026-09-07 — the "GAT-USBC" placeholder does not fit the single-patch-wall layout at
//          all, architecture.md §11 R11; "DONGLE-75x40x20" is the smaller dongle-class default
//          that does).
module mcc_splitter_envelope(name = "DONGLE-75x40x20") {
    spec        = mcc_splitter_spec(name);
    size        = struct_val(spec, "size");
    cable_allow = struct_val(spec, "cable_allow");
    total = [size[0] + 2 * cable_allow, size[1], size[2]];
    translate([0, 0, total[2] / 2])
        cube(total, center = true);
}

// Module: mcc_splitter_tiedown()
// Usage:
//   mcc_splitter_tiedown([name=], [floor_t=]);
// Description:
//   Negative: two zip-tie slots through the floor, one on each side (+Y/-Y) of the splitter
//   footprint, centered along its length, so a tie can loop over the splitter body and cinch
//   down through both slots. Slot size per the brief's explicit instruction, "4 x 1.5mm" — no
//   sourced figure exists for this project-specific feature; treated as a fixed constant of this
//   module's contract rather than derived from knowledge/components/fasteners-and-hardware.md's
//   generic cable-tie width table (fasteners-and-hardware.md:219-221), which covers stock tie
//   widths, not slot geometry.
// Arguments:
//   name    = splitter name, key into MCC_SPLITTERS. Default: "DONGLE-75x40x20" (matches
//             mcc_splitter_envelope()'s default — see the rationale there).
//   floor_t = floor thickness at the tie-down location, mm. Default: MCC_FLOOR_T.
module mcc_splitter_tiedown(name = "DONGLE-75x40x20", floor_t = MCC_FLOOR_T) {
    spec   = mcc_splitter_spec(name);
    size   = struct_val(spec, "size");
    slot_l = 4;   // zip-tie slot length (along the splitter's long/X axis), mm.
    slot_w = 1.5; // zip-tie slot width (across), mm.
    cut_h  = floor_t + 2 * MCC_EPS;

    for (sy = [-1, 1])
        translate([0, sy * size[1] / 2, floor_t / 2])
            cube([slot_l, slot_w, cut_h], center = true);
}

// vim: expandtab tabstop=4 shiftwidth=4 softtabstop=4 nowrap
