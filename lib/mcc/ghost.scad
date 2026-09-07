//////////////////////////////////////////////////////////////////////
// LibFile: mcc/ghost.scad
//   L1. Device ghost: bounding box, port receptacle stubs, and plug/bend keep-out envelopes.
//   Visual-only review aid, never part of exported geometry (architecture.md §7 "Ghost
//   rendering"). `use`d by lib/mcc/mcc.scad.
// Includes:
//   include <mcc/mcc.scad>
//////////////////////////////////////////////////////////////////////

include <BOSL2/std.scad>
include <constants.scad>
use <util.scad>
use <ports.scad>

// Function: _mcc_face_basis()
// Description:
//   Private helper. Given an axis-aligned outward unit normal `n` (a port's "face" field, per
//   architecture.md:256), returns [right, up] unit vectors spanning that face, matching the
//   port-record convention "+u = right looking at the face, +v = up" (architecture.md:256-257).
//   Top/bottom faces (n parallel to Z) fall back to a +Y "up" reference since world-up is
//   undefined for a face you are looking at from directly above/below.
function _mcc_face_basis(n) =
    let(
        up_ref = (abs(n[2]) > 0.999) ? [0, 1, 0] : [0, 0, 1],
        right  = unit(cross(up_ref, n)),
        up     = cross(n, right)
    )
    [right, up];

// Function: _mcc_face_center()
// Description:
//   Private helper. The center point of device face `n` on a device of bounding `size`.
function _mcc_face_center(size, n) = [for (i = [0:2]) n[i] * size[i] / 2];

// Function: _mcc_stub_size()
// Description:
//   Private helper. An 8x8x2 mm stub box, with the 2 mm dimension along whichever axis `n`
//   points along (this file's module contract: "box 8x8x2 at pos").
function _mcc_stub_size(n) =
    n[0] != 0 ? [2, 8, 8] :
    n[1] != 0 ? [8, 2, 8] :
    [8, 8, 2];

// Module: _mcc_ghost_port_stub()
// Description:
//   Private helper. One port receptacle stub, straddling the device surface at the port's
//   [u,v] position on its face.
module _mcc_ghost_port_stub(dev, p) {
    size  = mcc_dev_size(dev);
    n     = mcc_port_face(p);
    pos   = mcc_port_pos(p);
    basis = _mcc_face_basis(n);
    center = _mcc_face_center(size, n) + basis[0] * pos[0] + basis[1] * pos[1] + n * 1;
    translate(center) cube(_mcc_stub_size(n), center = true);
}

// Module: _mcc_ghost_plug()
// Description:
//   Private helper. The mating-plug + bend keep-out envelope for one port, extruded outward
//   along the port's face normal by mcc_plug_len(panel) + mcc_bend_envelope(panel)
//   (architecture.md:301-303 "a plug envelope extruded along each port's face normal by
//   mcc_plug_len(kind) plus a bend allowance"). Skipped when panel == "none".
module _mcc_ghost_plug(dev, p) {
    panel = mcc_port_panel(p);
    if (panel != "none") {
        size       = mcc_dev_size(dev);
        n          = mcc_port_face(p);
        pos        = mcc_port_pos(p);
        basis      = _mcc_face_basis(n);
        total_len  = mcc_plug_len(panel) + mcc_bend_envelope(panel);
        stub_size  = _mcc_stub_size(n);
        plug_size  = [
            n[0] != 0 ? total_len : stub_size[0],
            n[1] != 0 ? total_len : stub_size[1],
            n[2] != 0 ? total_len : stub_size[2],
        ];
        center = _mcc_face_center(size, n) + basis[0] * pos[0] + basis[1] * pos[1] + n * (total_len / 2);
        translate(center) cube(plug_size, center = true);
    }
}

// Module: mcc_ghost()
// Usage:
//   mcc_ghost(dev, [show=]);
// Description:
//   Device ghost for design review: `%`-rendered bounding box, a receptacle stub per port, and a
//   plug/bend keep-out envelope per externally-panelled port. Excluded from CSG/export by the `%`
//   modifier (belt 1) AND gated behind `show` (belt 2), per architecture.md:301-305's two-belt
//   rule — "A ghost that appears in an exported mesh is a P1 deviation."
// Arguments:
//   dev  = device record (lib/mcc/devices/*.scad).
//   show = whether to render the ghost at all. Default: MCC_SHOW_GHOST (false).
module mcc_ghost(dev, show = MCC_SHOW_GHOST) {
    if (show) {
        size = mcc_dev_size(dev);
        %cube(size, center = true);
        for (p = mcc_dev_ports(dev)) {
            %_mcc_ghost_port_stub(dev, p);
            %_mcc_ghost_plug(dev, p);
        }
    }
}

// vim: expandtab tabstop=4 shiftwidth=4 softtabstop=4 nowrap
