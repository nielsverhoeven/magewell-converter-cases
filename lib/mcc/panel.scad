//////////////////////////////////////////////////////////////////////
// LibFile: mcc/panel.scad
//   L2 (layout-independent). Owns the TOP-LEVEL dispatchers for every panel connector kind:
//   mcc_panel_cutout() (a flat panel — coupons) and mcc_panel_wall_cut() (the case's own patch
//   wall, D36). neutrik.scad is one *provider* behind them, not the top-level abstraction
//   (architecture.md §5). models/** must call these, never mcc_neutrik_* directly — that is a layering
//   deviation per architecture.md:217-219.
//   `use`d by lib/mcc/mcc.scad.
// Includes:
//   include <mcc/mcc.scad>
//////////////////////////////////////////////////////////////////////

include <BOSL2/std.scad>
include <constants.scad>
use <util.scad>
use <neutrik.scad>

// Z-axis convention: matches lib/mcc/neutrik.scad — a plate/panel spans Z=[0, panel_t] with the
// outward (connector-flange) face at Z=panel_t.

// Module: mcc_panel_cutout()
// Usage:
//   mcc_panel_cutout(part, [mirror=], [seat_t=], [panel_t=]);
// Description:
//   Panel-cutout dispatcher (architecture.md §5). Every dispatchable part is a Neutrik D-series
//   part (including "DBA-BL-B", the blank — it shares the same flange/screw footprint, per this
//   file's module contract), so this is a single-provider dispatcher onto mcc_neutrik_d_cutout().
//   The Mini-DIN-8 PTZ/Tally port stays internal (panel:"none") on every current SKU — it is never
//   passed here — so there is no Mini-DIN-8 branch and no bespoke round-cutout provider
//   (architecture.md §5). An unknown/unsupported `part` fails loudly with a clear assert rather
//   than silently producing no cutout.
// Arguments:
//   part    = panel part number, key into MCC_PANEL_PARTS (constants.scad).
//   mirror  = mirror the screw/fixing positions left-right. Default: false.
//   seat_t  = desired seat material thickness, mm. Default: MCC_PANEL_SEAT_T.
//   panel_t = actual panel thickness at this location, mm. Default: MCC_WALL.
module mcc_panel_cutout(part, mirror = false, seat_t = MCC_PANEL_SEAT_T, panel_t = MCC_WALL) {
    assert(search([part], MCC_PANEL_PARTS)[0] != [],
        str("mcc: mcc_panel_cutout() got unknown/unsupported panel part \"", part,
            "\" — must be a key of MCC_PANEL_PARTS (Neutrik D parts + \"DBA-BL-B\"); ",
            "\"MINIDIN8\" is reserved and not dispatchable, the PTZ/Tally port stays internal ",
            "(panel:\"none\", architecture.md §5)"));
    mcc_neutrik_d_cutout(part, mirror = mirror, seat_t = seat_t, panel_t = panel_t);
}

// Module: mcc_panel_wall_cut()
// Usage:
//   mcc_panel_wall_cut(part, [wall_t=], [seat_t=]);
// Description:
//   Dispatcher for a connector mounted DIRECTLY in a case wall (architecture.md §5 rev 14, D36 —
//   there is no separate panel plate any more). Same single-provider rule as mcc_panel_cutout():
//   every dispatchable part is a Neutrik D part, so this forwards to mcc_neutrik_d_wall_cut() (see
//   there for the frame: wall face seen from outside, Y up, seat face at Z=0, wall toward -Z).
// Arguments:
//   part   = panel part number, key into MCC_PANEL_PARTS (constants.scad).
//   wall_t = total wall thickness at the connector, mm.
//   seat_t = flange-seat thickness, mm. Default: MCC_PANEL_SEAT_T.
module mcc_panel_wall_cut(part, wall_t = MCC_PANEL_SEAT_T + MCC_WALL, seat_t = MCC_PANEL_SEAT_T) {
    assert(search([part], MCC_PANEL_PARTS)[0] != [],
        str("mcc: mcc_panel_wall_cut() got unknown/unsupported panel part \"", part,
            "\" — must be a key of MCC_PANEL_PARTS (Neutrik D parts + \"DBA-BL-B\")"));
    mcc_neutrik_d_wall_cut(part, wall_t = wall_t, seat_t = seat_t);
}

// vim: expandtab tabstop=4 shiftwidth=4 softtabstop=4 nowrap
