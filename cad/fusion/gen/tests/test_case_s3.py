"""C9: the whole case master, replayed (issue #81, plan 4 'C9', verdict A7 and B5).

The document ``cad/fusion/documents/mcc-case.json`` is built with every milestone C1 to C8 (no stage), the OpenCascade replay
executes the record with the parameter set of each configuration, and the parts it exports are compared with their oracles:

* offline, with the K4a stage fixtures (``fixtures/s2_stages.json``: the template's base B8, lid L4 and base with fan B10, the Plus
  case B10 with fan and switch, and the two parts of the non-exported configuration ``bare``): every box corner within
  ``s1_support.FRAME_TOL`` and the volume within the coarse guard;
* offline, with the committed goldens of ``tests/golden``: ``scripts/parity.py compare MESH MESH --golden G`` runs the golden
  tolerances of ``scripts/build.py golden`` (0.1 mm, 0.5 %, 1 %) on the replayed mesh itself, the goldens unchanged;
* with OpenSCAD, against a fresh oracle mesh (the K4a harness at the last stage of each part, which is what the golden measures) and
  the parity gate: no residual piece both above 0.5 mm3 and thicker than 0.05 mm, at most 0.2 % in total, plus the golden.

Besides, the replay of every configuration (eight devices, base_fan, bare and the build configuration) is one valid solid per part, no feature
is dead, no re-join adds volume outside the cut it names, and the re-joins are live exactly where the fan is.  The tests that need
OpenSCAD never skip on CI: ``oracle.require_openscad()`` fails them when ``MCC_REQUIRE_OPENSCAD=1``.
"""
from __future__ import annotations

import functools
import json

import pytest

from cad import params
from cad.fusion.gen.core import plan as kitplan
from cad.fusion.gen.tests import oracle, s1_support
from cad.fusion.replay import ocp_replay

PLAN_PATH = "cad/fusion/documents/mcc-case.json"
GOLDEN_DIR = s1_support.REPO / "tests" / "golden"
TEMPLATE = oracle.TEMPLATE
PLUS = oracle.PLUS
TEMPLATE_FAN = f"{TEMPLATE}.base_fan"
TEMPLATE_BARE = f"{TEMPLATE}.bare"
BUILD = "_build"
OPENING = "Fan_Aperture_OpeningCut"
FAN_REJOINS = 5   # two rings and three bars

# (configuration, component, part, fixture key or None, oracle: slug / part / last stage / options, golden or None)
FAN = oracle.s2_options(fan=True)
FAN_SWITCH = oracle.s2_options(fan=True, fan_switch=True)
BARE = oracle.s2_options(rail=False, lid_vents=False)
PARTS = {
    "template-base": (TEMPLATE, "Base", "base", f"{TEMPLATE}.base.B8", (TEMPLATE, "base", 8, oracle.s2_options()),
                      "pro-convert-for-ndi-to-hdmi.base"),
    "template-lid": (TEMPLATE, "Lid", "lid", f"{TEMPLATE}.lid.L4", (TEMPLATE, "lid", 4, oracle.s2_options()),
                     "pro-convert-for-ndi-to-hdmi.lid"),
    "template-base_fan": (TEMPLATE_FAN, "Base", "base_fan", f"{TEMPLATE}.base.B10", (TEMPLATE, "base", 10, FAN),
                          "pro-convert-for-ndi-to-hdmi.base_fan"),
    "plus-base": (PLUS, "Base", "base", f"{PLUS}.base.B10.fan_switch", (PLUS, "base", 10, FAN_SWITCH), "pro-convert-hdmi-plus.base"),
    "plus-lid": (PLUS, "Lid", "lid", None, (PLUS, "lid", 4, oracle.s2_options()), "pro-convert-hdmi-plus.lid"),
    "bare-base": (TEMPLATE_BARE, "Base", None, f"{TEMPLATE}.base.B8.bare", (TEMPLATE, "base", 8, BARE), None),
    "bare-lid": (TEMPLATE_BARE, "Lid", None, f"{TEMPLATE}.lid.L4.bare", (TEMPLATE, "lid", 4, BARE), None),
}


@functools.lru_cache(maxsize=None)
def _build():
    with s1_support.at_repo_root():
        document = kitplan.load_plan(PLAN_PATH)
        record, rows, sets = kitplan.build(document, None)
    return document, json.loads(json.dumps(record)), rows, sets


@functools.lru_cache(maxsize=None)
def _replay(configuration: str):
    """``{component: ComponentResult}`` of Base and Lid under one configuration."""
    _, record, rows, sets = _build()
    pset = sets[configuration]
    env = params.environment(rows, {"values": pset["values"], "units": pset["units"]})
    return ocp_replay.replay(record, env, pset["suppress"], components=["Base", "Lid"])


def _fixture(key: str) -> dict:
    return oracle.load_fixture(oracle.S2_FIXTURE)["stages"][key]


def _corner_problems(shape: dict, fixture: dict) -> list[str]:
    out = []
    for corner in ("bbox_min", "bbox_max"):
        worst = max(abs(a - b) for a, b in zip(shape[corner], fixture[corner]))
        if worst > s1_support.FRAME_TOL:
            out.append(f"{corner} differs from the fixture by {worst:.4f} mm (limit {s1_support.FRAME_TOL})")
    rel = abs(shape["volume_mm3"] - fixture["volume_mm3"]) / fixture["volume_mm3"]
    if rel > s1_support.VOLUME_GUARD:
        out.append(f"volume {shape['volume_mm3']:.3f} against {fixture['volume_mm3']:.3f} mm3 ({rel:.4%})")
    return out


@pytest.fixture(scope="module")
def meshes(tmp_path_factory):
    """The exported replay meshes of the configurations that have an allow-list: ``{(configuration, component): mesh path}``."""
    work = tmp_path_factory.mktemp("case_s3")
    document, _, _, _ = _build()
    out = {}
    for configuration in (TEMPLATE, TEMPLATE_FAN, PLUS):
        results = _replay(configuration)
        exports = [c for c in document["configurations"] if c["id"] == configuration][0]["exports"]
        records = ocp_replay.export(results, {"configurations": [{"id": configuration, "exports": exports}]}, configuration,
                                    work / configuration)
        for record in records:
            out[(configuration, record["component"])] = work / configuration / record["files"][1]
    # the bare configuration has no allow-list: export its two components under the names of the fixture
    shapes = _replay(TEMPLATE_BARE)
    plan = {"configurations": [{"id": TEMPLATE_BARE, "exports": [
        {"component": "Base", "target": TEMPLATE_BARE, "part": "base"}, {"component": "Lid", "target": TEMPLATE_BARE, "part": "lid"}]}]}
    for record in ocp_replay.export(shapes, plan, TEMPLATE_BARE, work / TEMPLATE_BARE):
        out[(TEMPLATE_BARE, record["component"])] = work / TEMPLATE_BARE / record["files"][1]
    return work, out


# --------------------------------------------------------------------------------------------------------------
# The replay of every configuration
# --------------------------------------------------------------------------------------------------------------

def test_the_document_has_eight_devices_two_template_variants_and_the_build_configuration():
    _, _, _, sets = _build()
    assert len(sets) == 11 and {BUILD, TEMPLATE_FAN, TEMPLATE_BARE} <= set(sets)


def test_the_full_build_records_every_milestone():
    """No stage: the record holds the features of every owner of the document, in the four phases."""
    document, record, _, _ = _build()
    owners = {s["name"].split("_")[0] for s in record["specs"] if s["spec"] in ("ExtrudeSpec", "LoftSpec", "PatternSpec")}
    assert owners == set(document["owners"])
    assert [c["name"] for c in record["components"]] == ["Base", "Lid", "Reserve_FanBay", "Reserve_SplitterBay", "Ghost_Device"]


@pytest.mark.parametrize("configuration", [BUILD, TEMPLATE_FAN, TEMPLATE_BARE, PLUS])
def test_the_replay_is_one_valid_solid_per_part_with_no_dead_feature(configuration):
    for component, result in _replay(configuration).items():
        shape = ocp_replay.measure(result.shape)
        assert (shape["solids"], shape["shells"], shape["valid"]) == (1, 1, True), (configuration, component)
        assert result.dead_features == [] and result.skipped == [], (configuration, component)


def test_no_feature_is_dead_and_no_re_join_leaves_its_cut_in_any_configuration():
    """Every configuration (the eight devices, the template with its fan and without rail and vents, and the build configuration): one valid solid per part, every feature live (a suppressed one is
    not dead), every re-join names the cut it refills (A2) and adds nothing outside it."""
    _, _, _, sets = _build()
    for configuration in sets:
        for component, result in _replay(configuration).items():
            shape = ocp_replay.measure(result.shape)
            assert (shape["solids"], shape["shells"], shape["valid"]) == (1, 1, True), (configuration, component)
            assert result.dead_features == [], (configuration, component)
            assert result.skipped == [], (configuration, component)
            for join in result.rejoins:
                assert join["within"] == OPENING, (configuration, join)
                assert join["outside_mm3"] <= ocp_replay.REJOIN_TOL, (configuration, join)


def test_the_re_joins_are_live_exactly_where_the_fan_is():
    _, _, _, sets = _build()
    for configuration, pset in sets.items():
        fan_on = pset["suppress"]["Fan_Aperture"] is False
        joins = _replay(configuration)["Base"].rejoins
        assert len(joins) == (FAN_REJOINS if fan_on else 0), configuration
        assert all(j["added_mm3"] > 0 for j in joins), configuration
        assert not _replay(configuration)["Lid"].rejoins, configuration


# --------------------------------------------------------------------------------------------------------------
# Offline: the replayed parts against the K4a fixtures and the committed goldens
# --------------------------------------------------------------------------------------------------------------

@pytest.mark.parametrize("name", [n for n, p in PARTS.items() if p[3]])
def test_the_replayed_part_matches_its_k4a_fixture(name):
    configuration, component, _, key, _, _ = PARTS[name]
    shape = ocp_replay.measure(_replay(configuration)[component].shape)
    assert _corner_problems(shape, _fixture(key)) == [], name


@pytest.mark.parametrize("name", [n for n, p in PARTS.items() if p[5]])
def test_the_committed_golden_passes_unchanged_on_the_replayed_mesh(name, meshes, tmp_path):
    """``parity.py compare`` with ``--golden``: the golden tolerances (bbox size 0.1 mm, volume 0.5 %, area 1 %) on the mesh."""
    configuration, component, _, _, _, golden = PARTS[name]
    work, paths = meshes
    mesh = paths[(configuration, component)]
    code, report = s1_support.parity(mesh, mesh, name, tmp_path, golden=GOLDEN_DIR / f"{golden}.json")
    assert code == 0 and report is not None, (code, report)
    checks = [c for c in report["checks"] if c["name"].startswith("golden")]
    assert checks and all(c["ok"] for c in checks), checks


# --------------------------------------------------------------------------------------------------------------
# With OpenSCAD: replay against a fresh oracle mesh and the parity gate
# --------------------------------------------------------------------------------------------------------------

@pytest.mark.parametrize("name", list(PARTS))
def test_the_replayed_part_replays_to_its_oracle(name, meshes):
    oracle.require_openscad()
    configuration, component, _, key, (slug, part, stage, options), golden = PARTS[name]
    work, paths = meshes
    mesh = paths[(configuration, component)]
    reference = oracle.render_s2(slug, part, stage, work / "oracle", tag=name, **options)
    extra = {"golden": GOLDEN_DIR / f"{golden}.json"} if golden else {}
    code, report = s1_support.parity(mesh, reference, name, work / "parity", **extra)
    fixture = _fixture(key) if key else oracle.measure(reference)
    result = _replay(configuration)[component]
    run = s1_support.BlockRun(result, ocp_replay.measure(result.shape), oracle.measure(mesh), fixture, code, report)
    assert s1_support.gate_problems(run) == []
    if golden:
        checks = [c for c in report["checks"] if c["name"].startswith("golden")]
        assert checks and all(c["ok"] for c in checks), checks
