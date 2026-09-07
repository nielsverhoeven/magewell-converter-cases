//////////////////////////////////////////////////////////////////////
// LibFile: mcc/ports.scad
//   L0. Accessors over the device/port record shape defined in architecture.md §7. Encapsulates
//   the BOSL2-struct representation so device data files and geometry never index the raw
//   assoc-list directly (architecture.md:244-245).
//   `use`d (not `include`d) by lib/mcc/mcc.scad per architecture.md:93.
// Includes:
//   include <mcc/mcc.scad>
//////////////////////////////////////////////////////////////////////

include <BOSL2/std.scad>
include <constants.scad>
use <util.scad>

// NOTE: MCC_CONFIDENCE_ORDER itself lives in constants.scad (not here) even though this is the
// file that consumes it — a plain variable defined in a `use`d file is invisible to anything
// outside that file's own scope (only modules/functions cross a `use` boundary), so any constant
// a test or another library file needs to read directly must live in the `include`d
// constants.scad, never in a `use`d L0/L1 file. See constants.scad's own confidence-order section.

// -----------------------------------------------------------------------------------------
// Section: Device-record accessors
// -----------------------------------------------------------------------------------------

function mcc_dev_slug(dev)   = struct_val(dev, "slug");
function mcc_dev_family(dev) = struct_val(dev, "family");
function mcc_dev_size(dev)   = struct_val(dev, "size");
function mcc_dev_source(dev) = struct_val(dev, "source");
function mcc_dev_ports(dev)  = struct_val(dev, "ports", []);

// -----------------------------------------------------------------------------------------
// Section: Port-record accessors
// -----------------------------------------------------------------------------------------

function mcc_port_id(port)         = struct_val(port, "id");
function mcc_port_face(port)       = struct_val(port, "face");
function mcc_port_pos(port)        = struct_val(port, "pos");
function mcc_port_kind(port)       = struct_val(port, "kind");
function mcc_port_dir(port)        = struct_val(port, "dir");
function mcc_port_panel(port)      = struct_val(port, "panel");
function mcc_port_confidence(port) = struct_val(port, "confidence");

// Function: mcc_ports_on_face()
// Usage:
//   ports = mcc_ports_on_face(dev, face);
// Description:
//   Every port on `dev` whose `face` unit-normal equals `face`.
function mcc_ports_on_face(dev, face) =
    [for (p = mcc_dev_ports(dev)) if (mcc_port_face(p) == face) p];

// Function: mcc_ports_external()
// Usage:
//   ports = mcc_ports_external(dev);
// Description:
//   Every port on `dev` that is brought out to a panel connector, i.e. `panel != "none"`
//   (architecture.md:282 "\"none\" = stays internal (SD slot, LEDs)").
function mcc_ports_external(dev) =
    [for (p = mcc_dev_ports(dev)) if (mcc_port_panel(p) != "none") p];

// Function: mcc_port_by_id()
// Usage:
//   port = mcc_port_by_id(dev, id);
// Description:
//   The single port on `dev` with the given `id`. Asserts exactly one match exists.
function mcc_port_by_id(dev, id) =
    let(matches = [for (p = mcc_dev_ports(dev)) if (mcc_port_id(p) == id) p])
    assert(len(matches) == 1,
        str("mcc: port id \"", id, "\" not found (or duplicated) on device \"", mcc_dev_slug(dev), "\""))
    matches[0];

function _mcc_confidence_rank(c) =
    let(ind = search([c], MCC_CONFIDENCE_ORDER)[0])
    assert(ind != [], str("mcc: unknown confidence level \"", c, "\""))
    ind;

// Function: mcc_warn_unmeasured()
// Usage:
//   weak_ports = mcc_warn_unmeasured(dev);
// Description:
//   echo()s a WARNING for every port on `dev` whose confidence is below "measured"
//   (architecture.md:288 "ports.scad echo()s a WARNING listing every port below measured at
//   render time") and returns the list of those ports for use in tests/assertions.
function mcc_warn_unmeasured(dev) =
    let(
        measured_rank = _mcc_confidence_rank("measured"),
        weak = [for (p = mcc_dev_ports(dev)) if (_mcc_confidence_rank(mcc_port_confidence(p)) < measured_rank) p],
        _ = [for (p = weak) mcc_warn(str(
            "unmeasured port \"", mcc_port_id(p), "\" on \"", mcc_dev_slug(dev),
            "\" — confidence=\"", mcc_port_confidence(p), "\""))]
    )
    weak;

// vim: expandtab tabstop=4 shiftwidth=4 softtabstop=4 nowrap
