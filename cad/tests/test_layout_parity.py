"""S0 for issue #77: every solver output of cad/layout.py equals the OpenSCAD fixture
(cad/fixtures/scad_layout.json: 10 configurations, a fan x fan_switch matrix, a fan_y case, six
synthetic devices that reach the branches the real ones do not, and edge-argument probes of the list functions).

Tolerance 1e-9 mm; integers, counts, labels, part numbers and the ORDER of every list are exact.
Offline (the fixture is committed); test_layout_fixture_equals_openscad re-derives it while OpenSCAD exists.
"""
from __future__ import annotations

import pytest

from cad import layout as LY
from cad import params
from cad.tests.support import TOL, layout_fixture, same as assert_same

FIXTURE = layout_fixture()
CASES = FIXTURE["cases"]
SHIPPED = [c for c in CASES if c["shipped"]]
DEEP = [c for c in CASES if "vents" in c]           # shipped + synthetic: vent and cradle lists were echoed too


def setup(case):
    dev = LY.device_from_doc(case["device"]) if "device" in case else LY.load_device(case["slug"])
    return dev, LY.Options(**case["options"])


ids = lambda c: c["id"]  # noqa: E731


def test_the_fixture_covers_ten_configurations_and_both_fan_states():
    assert len(SHIPPED) == 10 and len(CASES) == 31 and len(DEEP) == 16          # nine exported + the template's `bare`
    assert any(c["id"] == "pro-convert-for-ndi-to-hdmi/bare" and c["options"]["rail"] is False for c in SHIPPED)
    assert sum(1 for c in CASES if "device" in c) == 6
    assert {c["slug"] for c in SHIPPED} == set(params.case_slugs())
    assert {c["options"]["fan"] for c in CASES if c["slug"] == "pro-convert-for-ndi-to-hdmi"} == {True, False}
    assert any("fan_y" in c["options"] for c in CASES)


@pytest.mark.parametrize("case", CASES, ids=ids)
def test_layout_record_equals_openscad(case):
    dev, opts = setup(case)
    l = LY.case_layout(dev, opts)
    assert set(LY.LAYOUT_KEYS) == set(case["layout"]) and len(LY.LAYOUT_KEYS) == 36
    for key in LY.LAYOUT_KEYS:
        assert_same(getattr(l, key), case["layout"][key], key)
    assert isinstance(l.n_slots, int) and isinstance(l.lid_n_fast, int)


@pytest.mark.parametrize("case", CASES, ids=ids)
def test_slots_end_zones_deck_floor_and_ports_equal_openscad(case):
    dev, opts = setup(case)
    slots = LY.slot_assignment(dev)
    assert [{"slot": s.slot, "port_id": s.port_id, "part": s.part} for s in slots] == case["slots"]
    assert_same({"neg": LY.end_zone(dev, "neg"), "pos": LY.end_zone(dev, "pos")}, case["end_zone"], "end_zone")
    assert_same(LY.cradle_deck(dev), case["cradle_deck"], "cradle_deck")
    fk = [[f.cx, f.cy, f.kind, list(f.size), f.label] for f in LY.floor_keepout(dev, opts)]
    assert_same(fk, case["floor_keepout"], "floor_keepout")
    assert opts.sw_enabled == case["sw_enabled"]
    assert [p.id for p in LY.warn_unmeasured(dev)] == case["weak"]
    for s in slots:
        if s.port_id:
            assert LY.slot_for_port(dev, s.port_id) == s.slot


@pytest.mark.parametrize("case", DEEP, ids=ids)
def test_vent_runs_reproduce_every_slot_centre_of_openscad(case):
    dev, opts = setup(case)
    l = LY.case_layout(dev, opts)
    v = case["vents"]
    bands = LY.far_wall_excl(l)
    assert_same([[b.name, list(b.z), [list(e) for e in b.excl]] for b in bands], v["far_excl"], "far_excl")
    c = params.constants()
    slot_w, web_w = c["MCC_VENT_SLOT_W"], c["MCC_VENT_WEB_W"]
    # (1) the list function itself, (2) the runs the parameter set carries, expanded the way the generator will
    for b, name in zip(bands, ("far_low", "far_high")):
        assert_same(LY.vent_slot_centers(l.x_dev_lo, l.x_dev_hi, list(b.excl)), v[name], name)
    plan = LY.vent_plan(l)
    expand = lambda runs, pitch: [r.x0 + j * pitch for r in runs for j in range(r.n)]  # noqa: E731
    assert_same(expand(plan.far_low, slot_w + web_w), v["far_low"], "far_low runs")
    assert_same(expand(plan.far_high, slot_w + web_w), v["far_high"], "far_high runs")
    assert_same(expand(plan.exhaust, slot_w + web_w), v["exhaust"], "exhaust runs")
    assert_same(expand(plan.negx, slot_w + web_w), v["negx"], "negx runs")
    assert_same(expand(plan.lid, c["MCC_LID_VENT_SLOT_W"] + c["MCC_LID_VENT_WEB_W"]), v["lid"], "lid runs")
    f = LY.lid_vent_field(l)
    assert_same({"x_lo": f.x_lo, "x_hi": f.x_hi, "y_lo": f.y_lo, "y_hi": f.y_hi, "h": f.h, "excl": [list(e) for e in f.excl]},
                v["lid_field"], "lid_field")
    assert plan.split_z == pytest.approx(bands[0].z[1], abs=TOL)


@pytest.mark.parametrize("case", DEEP, ids=ids)
def test_cradle_grids_and_ribs_reproduce_openscad(case):
    dev, opts = setup(case)
    l = LY.case_layout(dev, opts)
    cr = case["cradle"]
    c = params.constants()
    lip = c["MCC_WALL"]
    plan = LY.cradle_plan(l)
    for axis, grid, lo, hi in (("deck_x", plan.deck_x, l.x_dev_lo - lip, l.x_dev_hi + lip),
                               ("deck_y", plan.deck_y, l.y_dev_lo - lip, l.y_dev_hi + lip)):
        assert_same(LY.cradle_deck_grid(lo, hi), cr[axis], axis)
        assert_same([grid.x0 + j * grid.pitch for j in range(grid.n)], cr[axis], axis + " from count, first position and pitch")
        assert grid.n == len(cr[axis])
    assert_same(LY.far_flank_rib_x(l.x_dev_lo, l.x_dev_hi, l.side_bolt_x), cr["flank"], "flank")
    assert_same(list(plan.far_ribs), cr["flank"], "flank ribs of the plan")
    assert_same(list(plan.patch_ribs), cr["patch"], "patch")


def _excl(ranges):
    return [tuple(r) for r in ranges]


PROBE_FUNCTIONS = {
    "deck_grid": lambda lo, hi: LY.cradle_deck_grid(lo, hi),
    "vent_centres": lambda lo, hi, excl, sw, ww: LY.vent_slot_centers(lo, hi, _excl(excl), sw, ww),
    "flank": lambda a, b, c: LY.far_flank_rib_x(a, b, c),
    "nearest_zero": lambda vals: LY.nearest_zero(vals),
    "in_any_range": lambda lo, hi, ranges: LY.in_any_range(lo, hi, _excl(ranges)),
}
PROBES = [(name, i, row) for name, rows in FIXTURE["probes"].items() for i, row in enumerate(rows)]


@pytest.mark.parametrize("name,i,row", PROBES, ids=[f"{n}-{i}" for n, i, _ in PROBES])
def test_edge_argument_probes_equal_openscad(name, i, row):
    """Half-way roundings (round(2.5) = 3 here, 2 in Python), exact floor boundaries, exclusions that touch a
    slot edge, segments of exactly 40 mm, empty results."""
    assert_same(PROBE_FUNCTIONS[name](*row["args"]), row["result"], f"{name}{row['args']}")


def test_vent_segments_expand_to_the_probe_lists_too():
    c = params.constants()
    for row in FIXTURE["probes"]["vent_centres"]:
        lo, hi, excl, sw, ww = row["args"]
        sw = c["MCC_VENT_SLOT_W"] if sw is None else sw
        ww = c["MCC_VENT_WEB_W"] if ww is None else ww
        runs = LY.vent_segments(lo, hi, _excl(excl), sw, ww)
        assert_same([r.x0 + j * (sw + ww) for r in runs for j in range(r.n)], row["result"], f"segments{row['args']}")
        assert len(runs) <= len(excl) + 1


def test_accessors_equal_openscad():
    acc = FIXTURE["accessors"]
    for part, rec in acc["panel_parts"].items():
        got = {"hole_d": LY.panel_hole_d(part), "depth": LY.panel_depth(part), "max_t": LY.panel_max_t(part),
               "plug_len": LY.plug_len(part), "bend": LY.bend_envelope(part), "kind": LY.panel_kind(part),
               "confidence": LY.panel_confidence(part), "bay_depth": LY.bay_depth(part), "cutout_d": LY.cutout_d(part),
               "aperture_window": LY.aperture_window(part), "plug_axial": LY.plug_axial(part)}
        assert_same(got, rec, f"panel_parts.{part}")
    for kind, v in acc["dev_side_allow"].items():
        assert LY.dev_side_allow(kind) == v
    for kind, v in acc["plug_axial"].items():
        assert LY.plug_axial(kind) == v
    for name, rec in acc["fan_spec"].items():
        assert_same(LY.fan_spec(name), rec, f"fan_spec.{name}")
    for name, rec in acc["switch_spec"].items():
        assert_same(LY.switch_spec(name), rec, f"switch_spec.{name}")
    for name, rec in acc["splitter_spec"].items():
        assert_same(LY.splitter_spec(name), rec, f"splitter_spec.{name}")
    assert_same(LY.side_bolt_keepout(), {k: v for k, v in acc["side_bolt_keepout"].items() if k != "strip_to_floor"}, "keepout")


@pytest.mark.openscad
def test_layout_fixture_equals_openscad(openscad_exe):
    tools = pytest.importorskip("cad.tools.layout_oracle", reason="cad/tools removed after the cutover (#86)")
    assert tools.check() == []


# ---------------------------------------------------------------- anchors from tests/test_layout.scad (oracle-independent)


TEMPLATE = "pro-convert-for-ndi-to-hdmi"


def test_template_anchors_from_the_frozen_smoke_test():
    """tests/test_layout.scad:29-81: worked figures that survive the cutover as regression anchors."""
    dev, opts = LY.load_device(TEMPLATE), LY.Options(fan=False, splitter=False)
    l = LY.case_layout(dev, opts)
    assert (l.L, l.W, l.H) == (pytest.approx(193.9, abs=1e-6), pytest.approx(159.85, abs=1e-6), 51.0)
    assert (l.ez_neg, l.ez_pos) == (47, 40) and l.n_slots == 4 and l.lid_n_fast == 6
    assert l.x_dev_c == pytest.approx(3.5, abs=1e-6) and l.y_dev_c == pytest.approx(-30.825, abs=1e-6)
    assert l.z_dev_lo == pytest.approx(13.85, abs=1e-6) and LY.cradle_deck(dev) == pytest.approx(10.85, abs=1e-6)
    assert l.plate_l == pytest.approx(167.9, abs=1e-6) and l.pitch == pytest.approx(41.9667, abs=1e-3)
    assert l.slot_x[0] == pytest.approx(-62.95, abs=1e-3) and l.slot_x[3] == pytest.approx(62.95, abs=1e-3)
    assert [LY.slot_for_port(dev, p) for p in ("rj45", "usb_b", "usb_host", "hdmi_out")] == [1, 2, 3, 4]
    assert [s.part for s in LY.slot_assignment(dev)] == ["NE8FDP-B", "NAUSB-W-B", "DBA-BL-B", "NAHDMI-W-B"]
    assert l.fan_pos[0] == pytest.approx(96.95, abs=1e-3)
    assert l.fan_bay_x == pytest.approx((78.95, 93.95), abs=1e-3) and l.fan_bay_y == pytest.approx((-50.825, -10.825), abs=1e-3)
    assert l.fan_bay_z == (5.5, 45.5) and l.splitter_bay_z == (3, 43)
    assert l.splitter_bay_x == pytest.approx((-93.95, -73.95), abs=1e-3) and l.splitter_bay_y == pytest.approx((-76.925, -1.925), abs=1e-3)
    assert (l.side_bolt_x, l.side_bolt_z) == (pytest.approx(3.5, abs=1e-3), pytest.approx(25.5, abs=1e-3))
    fp = l.lid_fastener_pos
    assert len(fp) == 6 and fp[0] == pytest.approx((86.95, 69.925), abs=1e-3)
    assert fp[4] == pytest.approx((0, 69.925), abs=1e-3) and fp[5] == pytest.approx((-12.64, -69.925), abs=1e-2)


SECTION_16 = [  # tests/test_layout.scad:170-195: slug, L, W, H, n_slots, parts in slot order, ez_neg, ez_pos
    ("pro-convert-hdmi-tx", 193.9, 159.85, 51.0, 3, ["NE8FDP-B", "NAUSB-W-B", "NAHDMI-W-B"], 47, 40),
    ("pro-convert-sdi-tx", 194.9, 158.80, 51.0, 3, ["NE8FDP-B", "NAUSB-W-B", "NBB75DFGB"], 47, 41),
    ("pro-convert-hdmi-plus", 210.5, 166.35, 51.0, 4, ["NE8FDP-B", "NAUSB-W-B", "NAHDMI-W-B", "NAHDMI-W-B"], 47, 40),
    ("pro-convert-sdi-plus", 211.5, 165.30, 51.0, 4, ["NE8FDP-B", "NAUSB-W-B", "NBB75DFGB", "NBB75DFGB"], 47, 41),
    ("pro-convert-for-ndi-to-hdmi-4k", 210.5, 166.35, 51.0, 4, ["NE8FDP-B", "NAUSB-W-B", "DBA-BL-B", "NAHDMI-W-B"], 47, 40),
    ("pro-convert-for-ndi-to-sdi", 194.9, 158.80, 51.0, 4, ["NE8FDP-B", "NAUSB-W-B", "DBA-BL-B", "NBB75DFGB"], 47, 41),
    ("pro-convert-for-ndi-to-aio", 194.9, 159.85, 51.0, 4, ["NE8FDP-B", "NAUSB-W-B", "NAHDMI-W-B", "NBB75DFGB"], 47, 41),
    (TEMPLATE, 193.9, 159.85, 51.0, 4, ["NE8FDP-B", "NAUSB-W-B", "DBA-BL-B", "NAHDMI-W-B"], 47, 40),
]


@pytest.mark.parametrize("row", SECTION_16, ids=[r[0] for r in SECTION_16])
def test_section_16_fit_table_for_all_eight_devices(row):
    slug, L, W, H, n, parts, ez_neg, ez_pos = row
    dev = LY.load_device(slug)
    l = LY.case_layout(dev, LY.Options())
    assert (l.L, l.W, l.H) == (pytest.approx(L, abs=1e-2), pytest.approx(W, abs=1e-2), pytest.approx(H, abs=1e-6))
    assert l.n_slots == n and (l.ez_neg, l.ez_pos) == (pytest.approx(ez_neg, abs=1e-6), pytest.approx(ez_pos, abs=1e-6))
    assert [s.part for s in LY.slot_assignment(dev)] == parts


# ---------------------------------------------------------------- solver refusals (cannot compute or represent)


def _device(ports, size=(100.9, 60.2, 23.3)):
    return LY.Device("synthetic", "compact", size, tuple(ports))


def _port(pid, face, panel="NE8FDP-B", kind="rj45", pos=(0, 0)):
    return LY.Port(pid, face, pos, kind, "bidir", panel, "assumed")


def test_five_external_ports_are_solved_but_do_not_fit_the_master():
    """solve() can compute five slots; the parameter set cannot hold them (capacity, not computation)."""
    dev = _device([_port(f"p{i}", (1, 0, 0), pos=(i, 0)) for i in range(5)] + [_port("side_bolt", (0, -1, 0), "none", "tripod_1_4_20")])
    assert len(LY.slot_assignment(dev)) == 5
    sol = LY.solution_for(dev, LY.Options())
    assert sol.layout.n_slots == 5
    assert any("connector slots" in p for p in LY.capacity_problems(sol))
    with pytest.raises(LY.CapacityError, match="connector slots"):
        LY.parameter_set(sol)


def test_a_device_without_an_external_port_is_refused():
    dev = _device([_port("side_bolt", (0, -1, 0), "none", "tripod_1_4_20")])
    with pytest.raises(LY.SolverError, match="no external port"):
        LY.slot_assignment(dev)


def test_an_external_port_on_a_long_face_is_refused():
    dev = _device([_port("p", (0, 1, 0)), _port("side_bolt", (0, -1, 0), "none", "tripod_1_4_20")])
    with pytest.raises(LY.SolverError, match="T1-01"):
        LY.slot_assignment(dev)


def test_unknown_names_are_refused():
    with pytest.raises(LY.SolverError):
        LY.panel_part("NOPE")
    with pytest.raises(LY.SolverError):
        LY.dev_side_allow("laser")
    with pytest.raises(LY.SolverError):
        LY.fan_spec("NF-X")


def test_a_missing_side_bolt_is_refused():
    dev = _device([_port("p", (1, 0, 0))])
    with pytest.raises(LY.SolverError, match="side_bolt"):
        LY.case_layout(dev, LY.Options())


def test_equal_sort_keys_keep_input_order_like_bosl2_sort():
    a = _port("first", (-1, 0, 0), pos=(5, 0))
    b = _port("second", (-1, 0, 0), pos=(5, 0))
    dev = _device([a, b, _port("side_bolt", (0, -1, 0), "none", "tripod_1_4_20")])
    assert [s.port_id for s in LY.slot_assignment(dev)] == ["first", "second"]


def test_the_far_mid_fastener_quirk_of_vents_scad_is_reproduced():
    """vents.scad:194 reads the far mid from index 5 of the fastener list.  With no patch mid (tight pitch) the far
    mid is at index 4 and the vents ignore it: the lower far-wall band then excludes only the side-bolt strip."""
    case = next(c for c in CASES if c["id"] == "synthetic/tight-pitch")
    dev, opts = setup(case)
    l = LY.case_layout(dev, opts)
    assert l.lid_n_fast == 6 and len(l.lid_fastener_pos) == 5 and l.lid_fastener_pos[4][1] < 0
    assert LY.lid_far_mid_x(l) is None
    assert len(LY.far_wall_excl(l)[0].excl) == 1
    assert len(case["vents"]["far_excl"][0][2]) == 1
