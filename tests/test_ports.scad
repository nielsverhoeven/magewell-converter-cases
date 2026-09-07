//////////////////////////////////////////////////////////////////////
// tests/test_ports.scad
//   Tier-2 headless smoke test (architecture.md §9). Loads every device data file, asserts
//   unique ids, unit-vector faces, valid confidence, and that every external port has a known
//   panel part. Also echoes mcc_warn_unmeasured() for each device (WARNINGs are expected and are
//   not a failure — architecture.md:288-291).
// Run:
//   openscad --backend=Manifold -o out.csg tests/test_ports.scad
//////////////////////////////////////////////////////////////////////

$fa = 1; $fs = 0.4;

include <mcc/mcc.scad>

include <mcc/devices/pro-convert-hdmi-tx.scad>
include <mcc/devices/pro-convert-sdi-tx.scad>
include <mcc/devices/pro-convert-hdmi-plus.scad>
include <mcc/devices/pro-convert-sdi-plus.scad>
include <mcc/devices/pro-convert-for-ndi-to-hdmi.scad>
include <mcc/devices/pro-convert-for-ndi-to-hdmi-4k.scad>
include <mcc/devices/pro-convert-for-ndi-to-sdi.scad>
include <mcc/devices/pro-convert-for-ndi-to-aio.scad>

MCC_ALL_DEVICES = [
    MCC_DEV_PRO_CONVERT_HDMI_TX,
    MCC_DEV_PRO_CONVERT_SDI_TX,
    MCC_DEV_PRO_CONVERT_HDMI_PLUS,
    MCC_DEV_PRO_CONVERT_SDI_PLUS,
    MCC_DEV_PRO_CONVERT_FOR_NDI_TO_HDMI,
    MCC_DEV_PRO_CONVERT_FOR_NDI_TO_HDMI_4K,
    MCC_DEV_PRO_CONVERT_FOR_NDI_TO_SDI,
    MCC_DEV_PRO_CONVERT_FOR_NDI_TO_AIO,
];

module test_device(dev) {
    slug  = mcc_dev_slug(dev);
    ports = mcc_dev_ports(dev);

    // Unique ids.
    ids = [for (p = ports) mcc_port_id(p)];
    assert(len(ids) == len(_mcc_unique(ids)),
        str("mcc test_ports: duplicate port id on device \"", slug, "\""));

    for (p = ports) {
        id = mcc_port_id(p);

        // Unit-vector face.
        face = mcc_port_face(p);
        mag  = norm(face);
        assert(abs(mag - 1) < 1e-6,
            str("mcc test_ports: port \"", id, "\" on \"", slug, "\" has non-unit face vector ", face));

        // Valid confidence.
        conf = mcc_port_confidence(p);
        assert(search([conf], MCC_CONFIDENCE_ORDER)[0] != [],
            str("mcc test_ports: port \"", id, "\" on \"", slug, "\" has invalid confidence \"", conf, "\""));

        // Mini-DIN-8 stays internal on every current SKU (user decision 2026-09-07,
        // architecture.md §5) — no port may reference the reserved "MINIDIN8" panel part.
        panel = mcc_port_panel(p);
        assert(panel != "MINIDIN8",
            str("mcc test_ports: port \"", id, "\" on \"", slug, "\" references the reserved panel ",
                "part \"MINIDIN8\" — Mini-DIN-8 stays internal, use panel:\"none\""));

        // Every external port's panel is a key of MCC_PANEL_PARTS, or "none".
        if (panel != "none") {
            found = search([panel], MCC_PANEL_PARTS)[0] != [];
            assert(found,
                str("mcc test_ports: port \"", id, "\" on \"", slug, "\" references unknown panel part \"", panel, "\""));
        }
    }

    // Required warning surfacing (architecture.md:288).
    weak = mcc_warn_unmeasured(dev);
    echo(str("mcc test_ports: \"", slug, "\" has ", len(weak), " port(s) below \"measured\" confidence"));
}

// Private helper: de-duplicate a list of strings.
function _mcc_unique(list) =
    [for (i = [0:1:len(list)-1]) if (search([list[i]], list, 0)[0][0] == i) list[i]];

for (dev = MCC_ALL_DEVICES) test_device(dev);

echo(str("mcc test_ports: OK — ", len(MCC_ALL_DEVICES), " devices checked"));

// vim: expandtab tabstop=4 shiftwidth=4 softtabstop=4 nowrap
