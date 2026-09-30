"""cad.params: grammar, evaluator, Fusion emitter, registry structure, data tables, devices, cases.

All tests are offline and permanent: they describe what the files under cad/ must always satisfy
(the S0 comparison with OpenSCAD lives in test_scad_sync.py and ends with the oracle).
"""
from __future__ import annotations

import math
import os
import re
from pathlib import Path

import pytest

from cad import params as P

# ---------------------------------------------------------------- grammar, evaluator, emitter


def q(text, **scope):
    return P.evaluate(text, {k: P.Quantity(*v) for k, v in scope.items()})


def test_units_and_arithmetic():
    assert q("3 mm + 2 mm") == P.Quantity(5.0, P.LENGTH)
    assert q("2 * 2.0 mm") == P.Quantity(4.0, P.LENGTH)
    assert q("60 deg") == P.Quantity(60.0, P.ANGLE)
    assert q("MCC_A / 2", MCC_A=(10.0, P.LENGTH)) == P.Quantity(5.0, P.LENGTH)
    assert q("-23.5 mm").value == -23.5
    assert q("1e-3").value == 0.001


def test_unit_mismatch_is_an_error_as_in_fusion():
    with pytest.raises(P.ExpressionError):
        q("3 mm + 2")
    with pytest.raises(P.ExpressionError):
        q("max(3 mm, 2)")


def test_trig_needs_an_angle_and_is_dimensionless():
    assert q("tan(45 deg)") == P.Quantity(1.0, P.NONE)
    assert q("MCC_D / tan(60 deg)", MCC_D=(4.0, P.LENGTH)).value == pytest.approx(4 / math.sqrt(3), rel=1e-15)
    with pytest.raises(P.ExpressionError):
        q("tan(60)")


def test_only_the_neutral_grammar_is_accepted():
    for bad in ("floor(3)", "round(2.5 mm)", "if(1, 2, 3)", "3 in", "3 cm", "max(1; 2)", "2 ^ 3", "x[1]"):
        with pytest.raises(P.ExpressionError):
            q(bad, x=(1.0, P.NONE))


def test_fusion_emitter_is_the_only_place_that_knows_the_dialect():
    assert P.emit_fusion("max(MCC_A, (MCC_B + 1.0 mm) - 2 * 2.0 mm)") == "max(MCC_A; (MCC_B + 1.0 mm) - 2 * 2.0 mm)"
    assert P.emit_fusion("tan(MCC_ANGLE)") == "tan(MCC_ANGLE)"
    # the emitted text is itself evaluable once commas replace semicolons: same grammar, one separator
    assert P.evaluate(P.emit_fusion("max(3 mm, 4 mm)").replace(";", ",")).value == 4.0


def test_the_semicolon_dialect_lives_in_emit_fusion_only():
    """A1 of the gate of #76: no data, no registry() `expression` and no other function of cad/params.py holds the
    Fusion argument separator; the runtime's `fusion` text is the only place it shows up."""
    import ast
    tree = ast.parse(Path(P.__file__).read_text(encoding="utf-8"))
    docstrings = {id(n.body[0].value) for n in ast.walk(tree)
                  if isinstance(n, (ast.Module, ast.FunctionDef, ast.ClassDef)) and n.body
                  and isinstance(n.body[0], ast.Expr) and isinstance(n.body[0].value, ast.Constant)}
    holders = set()
    for fn in [n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef)]:
        for n in ast.walk(fn):
            if isinstance(n, ast.Constant) and isinstance(n.value, str) and ";" in n.value and id(n) not in docstrings:
                holders.add(fn.name)
    assert holders == {"emit_fusion", "em"}, holders            # `em` is emit_fusion's inner function
    for inline in (True, False):
        for r in P.registry([P.CONSTANTS_CSV], minmax_in_fusion=inline):
            assert ";" not in r["expression"], r["name"]


def test_names_in_and_is_literal():
    assert P.names_in("max(MCC_A, MCC_B * 2) - MCC_A") == {"MCC_A", "MCC_B"}
    assert P.is_literal("3.0 mm") and P.is_literal("-23.5 mm") and P.is_literal("1.8") and P.is_literal("60 deg")
    assert not P.is_literal("MCC_WALL") and not P.is_literal("2 * 2.0 mm")


# ---------------------------------------------------------------- registry


@pytest.fixture(scope="module")
def rows():
    return P.read_registry()


def test_registry_is_structurally_sound(rows):
    assert P.check_registry(rows) == []


def test_registry_evaluates_and_every_unit_matches_its_expression(rows):
    scope = P.evaluate_registry(rows)
    assert len(scope) == len(rows) and len(rows) > 140


def test_literal_rows_carry_src_and_conf_expression_rows_carry_no_conf(rows):
    lit = [r for r in rows if r.is_literal]
    expr = [r for r in rows if not r.is_literal]
    assert len(lit) > 100 and len(expr) >= 15
    assert all(r.conf in P.CONF_LEVELS and r.src for r in lit)
    assert all(r.conf is None and r.src for r in expr)


def test_every_citation_names_an_existing_file(rows):
    """src is a repository path (with :line or a section or a record id) that a reader can open.  A .scad citation is
    only checked while the oracle tree exists (it is deleted at the cutover, issue #86)."""
    repo = Path(os.environ.get("MCC_REPO_ROOT") or P.CAD_DIR.parent)
    for r in rows:
        head = r.src.split(":")[0].split(" ")[0]
        if head.endswith(".scad") and not (repo / "lib" / "mcc").is_dir():
            continue
        if head.endswith((".md", ".scad", ".csv", ".json", ".py")):
            assert (repo / head).is_file(), f"{r.name}: src {r.src!r} names no file in the repository"
        else:
            assert re.fullmatch(r"[A-Z]+\d+(?:\.\d+)?", r.src) or "/" in head, f"{r.name}: src {r.src!r} is neither a path nor a record id"


def test_derived_constants_that_mirror_a_table_row_stay_consistent():
    c = P.constants()
    splitters = P.table("splitters")
    default = P.table("options")["splitter_default"]
    assert c["MCC_END_ZONE_NEG_EXTRA_SPLITTER"] == splitters[default]["size"][2]
    assert c["MCC_SIDE_BOLT_KEEPOUT_D"] == c["MCC_SIDE_BOLT_BOSS_OD"] + 4.0   # mcc_side_bolt_keepout()["disc_d"]


def test_the_head_recess_the_cut_really_makes_is_a_named_expression_row(rows):
    """fasteners.scad:267 cuts head_d + 2 * MCC_CLR_SLIDE = 10.6, not the 12.0 of MCC_SIDE_BOLT_HEAD_REC_D; the
    bore is insert length + 1 (fasteners.scad:33), not MCC_INSERT_BORE_EXTRA (0.5)."""
    by = {r.name: r for r in rows}
    row = by["MCC_SIDE_BOLT_HEAD_CUT_D"]
    assert not row.is_literal and row.conf is None and row.src == "lib/mcc/fasteners.scad:267"
    assert row.expression == "MCC_SIDE_BOLT_HEAD_D + 2 * MCC_CLR_SLIDE"
    assert P.constants()["MCC_SIDE_BOLT_HEAD_CUT_D"] == pytest.approx(10.6)
    assert P.constants()["MCC_SIDE_BOLT_HEAD_REC_D"] == 12.0 and "MCC_SIDE_BOLT_HEAD_CUT_D" in by["MCC_SIDE_BOLT_HEAD_REC_D"].description
    assert P.constants()["MCC_INSERT_BORE_EXTRA"] == 0.5 and "MCC_INSERT_BORE_OVERDEPTH" in by["MCC_INSERT_BORE_EXTRA"].description


def test_fusion_parameter_carries_unit_expression_and_comment(rows):
    by = {r.name: r for r in rows}
    name, unit, expr, comment = P.fusion_parameter(by["MCC_GAP_FAR"])
    assert (name, unit) == ("MCC_GAP_FAR", "mm") and expr.startswith("max(MCC_GAP_FAR_DUCT_MIN; ") and " | src=" in comment
    assert P.fusion_parameter(by["MCC_BOSS_MIN_RATIO"])[1] == ""            # unitless = empty API unit
    assert P.fusion_parameter(by["MCC_RAIL_FLANK_ANGLE"])[1] == "deg"
    assert all(";" not in r.expression for r in rows)                        # no Fusion syntax in data


# ---------------------------------------------------------------- tables


PANEL_FIELDS = ("hole_d", "depth", "max_panel_t", "plug_len", "bend", "kind", "confidence")


def test_panel_parts_table_is_complete():
    parts = P.table("panel_parts")
    assert list(parts) == ["NE8FDP-B", "NAHDMI-W-B", "NAUSB-W-B", "NBB75DFGB", "DBA-BL-B"]
    order = P.table("confidence_order")
    for part, rec in parts.items():
        assert set(rec) == set(PANEL_FIELDS), part
        assert rec["confidence"] in order
    assert parts["NAHDMI-W-B"]["depth"] + parts["NAHDMI-W-B"]["plug_len"] == pytest.approx(75.65)  # test_constants.scad:33


def test_table_expressions_are_evaluated_from_the_registry():
    sw = P.table("switches")["MTS-101"]
    assert sw["nut_d"] == pytest.approx(8.0 / math.cos(math.radians(30)), rel=1e-12)
    assert sw["keepout_d"] == pytest.approx(sw["nut_d"] + 2 * P.constants()["MCC_CLR_SLIDE"], rel=1e-12)


def test_options_name_existing_table_rows():
    opts = P.table("options")
    assert opts["fan_default"] in P.table("fans")
    assert opts["switch_default"] in P.table("switches")
    assert opts["splitter_default"] in P.table("splitters")


def test_per_kind_maps_cover_every_kind_the_panel_parts_and_devices_use():
    allow, axial = P.table("dev_side_allow"), P.table("plug_axial")
    kinds = {p["kind"] for p in P.table("panel_parts").values()}
    assert kinds <= set(axial)
    for slug in P.device_slugs():
        for port in P.device_doc(slug)["ports"]:
            assert port["kind"] in allow, (slug, port["id"])


# ---------------------------------------------------------------- devices and cases


@pytest.mark.parametrize("slug", P.device_slugs())
def test_device_files_satisfy_the_port_contract(slug):
    d = P.device_doc(slug)
    assert d["slug"] == slug and d["family"] in ("compact", "plus") and len(d["size"]) == 3 and min(d["size"]) > 0
    ids = [p["id"] for p in d["ports"]]
    assert len(ids) == len(set(ids))
    parts, order = P.table("panel_parts"), P.table("confidence_order")
    for p in d["ports"]:
        assert math.isclose(math.sqrt(sum(x * x for x in p["face"])), 1.0)
        assert p["confidence"] in order
        assert p["panel"] == "none" or p["panel"] in parts
        assert p["panel"] != "MINIDIN8"
    side = [p for p in d["ports"] if p["kind"] == "tripod_1_4_20"]          # T1-22 mirror
    assert len(side) == 1 and side[0]["id"] == "side_bolt" and side[0]["face"] == [0, -1, 0] and side[0]["panel"] == "none"
    assert d["source"]["file"].startswith("knowledge/magewell/models/")


@pytest.mark.parametrize("slug", P.case_slugs())
def test_case_definitions_hold_options_only(slug):
    c = P.case_doc(slug)
    assert c["device"] in P.device_slugs() and c["slug"] == slug
    assert set(c["options"]) <= set(P.CASE_OPTIONS) and "tripod_insert" not in c["options"]
    assert c["options"]["lid_vents"] is True
    assert set(c["configurations"]) <= {"base_fan"} and set(c["test_configurations"]) <= {"bare"}
    for overrides in list(c["configurations"].values()) + list(c["test_configurations"].values()):
        assert set(overrides) <= set(P.CASE_OPTIONS)


def test_nine_configurations_are_exported_and_bare_is_not_among_them():
    """A2 of the gate of #76: export status is data in the case definition (`configurations` = exported extras,
    `test_configurations` = never exported)."""
    exported = {slug: P.exported_configurations(slug) for slug in P.case_slugs()}
    assert len(exported) == 8 and sum(len(v) for v in exported.values()) == 9
    assert exported["pro-convert-for-ndi-to-hdmi"] == ["default", "base_fan"]
    assert all(v[0] == "default" for v in exported.values())
    assert not any("bare" in v for v in exported.values())
    assert P.case_doc("pro-convert-for-ndi-to-hdmi")["test_configurations"] == {"bare": {"rail": False, "lid_vents": False}}


def _case_json(tmp_path, **doc):
    import json
    base = {"schema": 1, "slug": "x", "device": "x", "options": {"fan": True}}
    (tmp_path / "x.json").write_text(json.dumps({**base, **doc}), encoding="utf-8")
    return tmp_path


def test_configuration_names_are_unique_across_both_keys_and_never_default(tmp_path):
    with pytest.raises(ValueError, match="both"):
        P.case_doc("x", _case_json(tmp_path, configurations={"a": {"fan": False}}, test_configurations={"a": {"rail": False}}))
    with pytest.raises(ValueError, match="default"):
        P.case_doc("x", _case_json(tmp_path, test_configurations={"default": {"rail": False}}))
    with pytest.raises(ValueError, match="default"):
        P.case_doc("x", _case_json(tmp_path, configurations={"default": {"fan": False}}))


def test_both_configuration_keys_are_validated_against_the_closed_option_list(tmp_path):
    with pytest.raises(ValueError, match="Fan_Aperture"):
        P.case_doc("x", _case_json(tmp_path, test_configurations={"t": {"Fan_Aperture": True}}))
    with pytest.raises(ValueError, match="rail_x"):
        P.case_doc("x", _case_json(tmp_path, configurations={"t": {"rail_x": True}}))
    doc = P.case_doc("x", _case_json(tmp_path, test_configurations={"t": {"rail": False}}))
    assert doc["configurations"] == {} and P.exported_configurations("x", tmp_path) == ["default"]


def test_tripod_insert_left_the_closed_option_list(tmp_path):
    """P2-81 Q81.3 default (T1-81.7): the master has no floor insert boss, so a case definition cannot ask for one."""
    import json
    assert "tripod_insert" not in P.CASE_OPTIONS
    bad = {"schema": 1, "slug": "x", "device": "x", "options": {"fan": False, "tripod_insert": False}, "configurations": {}}
    (tmp_path / "x.json").write_text(json.dumps(bad), encoding="utf-8")
    with pytest.raises(ValueError, match="tripod_insert"):
        P.case_doc("x", tmp_path)


def test_a_case_definition_refuses_a_dimension_a_flag_or_a_feature_name(tmp_path):
    import json
    bad = {"schema": 1, "slug": "x", "device": "x", "options": {"fan": True, "Fan_Aperture": True}, "configurations": {}}
    (tmp_path / "x.json").write_text(json.dumps(bad), encoding="utf-8")
    with pytest.raises(ValueError, match="Fan_Aperture"):
        P.case_doc("x", tmp_path)


# ---------------------------------------------------------------- parameter sets and the runtime registry


def _write_set(path, **overrides):
    import json
    cfg = {"parameters": {"V_CASE_L": "193.9 mm", "V_N_DECK_X": "4", "V_CASE_ANGLE": "60 deg"},
           "flags": {"Fan_Aperture": True, "Patch_Slot4": False},
           "slots": [{"slot": 1, "port": "rj45", "part": "NE8FDP-B"}]}
    cfg.update(overrides)
    path.write_text(json.dumps({"schema": 1, "slug": path.stem, "solver": "cad/layout.py",
                                "configurations": {"default": cfg}}), encoding="utf-8")
    return path


def test_parameter_set_returns_numbers_units_and_flags(tmp_path):
    ps = P.parameter_set(_write_set(tmp_path / "a.json"), "default")
    assert ps["values"] == {"V_CASE_L": 193.9, "V_N_DECK_X": 4, "V_CASE_ANGLE": 60.0}
    assert ps["units"] == {"V_CASE_L": "mm", "V_N_DECK_X": "none", "V_CASE_ANGLE": "deg"}
    assert isinstance(ps["values"]["V_N_DECK_X"], int) and ps["suppress"] == {"Fan_Aperture": True, "Patch_Slot4": False}


@pytest.mark.parametrize("bad", [
    {"parameters": {"V_N_DECK_X": "0"}, "flags": {}},                      # a count is >= 1
    {"parameters": {"V_N_DECK_X": "2.5"}, "flags": {}},                    # and an integer
    {"parameters": {"V_CASE_L": "193.9"}, "flags": {}},                    # a length needs its unit
    {"parameters": {"CASE_L": "1 mm"}, "flags": {}},                       # V_<GROUP>_<NAME>
    {"parameters": {"V_CASE_L": "1 mm"}, "flags": {"Reserve_FanBay": True}},   # no flag may name Reserve_*
    {"parameters": {"V_CASE_L": "1 mm"}, "flags": {"Bogus_Thing": True}},      # Owner from the closed list
    {"parameters": {"V_CASE_L": "1 mm"}, "flags": {"Fan_Aperture": 1}},        # booleans only
])
def test_parameter_set_rejects_malformed_content(tmp_path, bad):
    with pytest.raises(ValueError):
        P.parameter_set(_write_set(tmp_path / "a.json", **bad), "default")


def test_sets_must_be_total_across_files(tmp_path):
    a = _write_set(tmp_path / "a.json")
    b = _write_set(tmp_path / "b.json", parameters={"V_CASE_L": "1 mm"})
    assert P.check_parameter_sets([a]) == []
    assert any("parameter names differ" in p for p in P.check_parameter_sets([a, b]))


def test_registry_rows_for_the_runtime(tmp_path):
    rows = P.registry([P.CONSTANTS_CSV], [_write_set(tmp_path / "a.json")])
    by = {r["name"]: r for r in rows}
    assert by["MCC_WALL"]["kind"] == "constant" and by["MCC_WALL"]["fusion"] == "3.0 mm" and by["MCC_WALL"]["unit"] == "mm"
    assert by["MCC_GAP_FAR"]["kind"] == "expression" and by["MCC_GAP_FAR"]["fusion"].startswith("max(MCC_GAP_FAR_DUCT_MIN; ")
    assert by["MCC_BOSS_MIN_RATIO"]["unit"] == "" and by["MCC_RAIL_FLANK_ANGLE"]["unit"] == "deg"
    assert by["V_CASE_L"] == {**by["V_CASE_L"], "kind": "solver", "expression": None, "fusion": None, "unit": "mm"}
    assert by["MCC_WALL"]["expression"] == "3.0 mm" and by["MCC_GAP_FAR"]["expression"].startswith("max(MCC_GAP_FAR_DUCT_MIN, ")
    assert by["V_N_DECK_X"]["unit"] == "" and by["V_CASE_ANGLE"]["unit"] == "deg"
    with pytest.raises(ValueError, match="more than one"):
        P.registry([P.CONSTANTS_CSV, P.CONSTANTS_CSV])


def test_registry_can_inline_min_max_if_the_live_probe_says_fusion_has_none():
    by = {r["name"]: r for r in P.registry([P.CONSTANTS_CSV], minmax_in_fusion=False)}
    assert by["MCC_GAP_FAR"]["fusion"] == "16 mm"                      # max(...) evaluated; the CSV keeps the definition
    assert by["MCC_SIDE_BOLT_PROUD"]["fusion"] == "0 mm"
    assert by["MCC_T_PATCH"]["fusion"] == "MCC_PANEL_BEZEL_T + MCC_PANEL_SEAT_T + MCC_WALL"     # no min/max: unchanged
    assert by["MCC_RAIL_MOUTH_W"]["fusion"].endswith("tan(MCC_RAIL_FLANK_ANGLE)")
    assert {r["name"]: r for r in P.registry([P.CONSTANTS_CSV])}["MCC_GAP_FAR"]["fusion"].startswith("max(")
    # A1: the neutral definition stays in `expression`, whatever the flag says
    assert by["MCC_GAP_FAR"]["expression"].startswith("max(MCC_GAP_FAR_DUCT_MIN, ") and ";" not in by["MCC_GAP_FAR"]["expression"]
    assert by["MCC_GAP_FAR"]["expression"] == {r.name: r for r in P.read_registry()}["MCC_GAP_FAR"].expression
    assert by["MCC_WALL"]["expression"] == "3.0 mm"


# ---------------------------------------------------------------- environment and evaluate_number (the generator kit's two calls)


def _env(tmp_path):
    cfg = {"parameters": {"V_CASE_L": "193.9 mm", "V_SWITCH_PAD_T": "13 mm", "V_FAN_Y": "-30.825 mm",
                          "V_FAN_HOLE_PITCH": "32 mm", "V_FAN_OPENING_D": "38 mm", "V_N_DECK_X": "4"},
           "flags": {"Fan_Aperture": True}}
    return P.environment(solved=P.parameter_set(_write_set(tmp_path / "a.json", **cfg), "default"))


def test_environment_holds_every_registry_name_and_every_solver_output(tmp_path):
    env = _env(tmp_path)
    assert set(P.constants()) <= set(env)
    assert env["V_CASE_L"] == P.Quantity(193.9, P.LENGTH) and env["V_N_DECK_X"] == P.Quantity(4, P.NONE)
    assert env["MCC_FAN_GRILLE_SPOKE_PITCH"] == P.Quantity(60.0, P.ANGLE)
    assert len(env) == len(P.read_registry()) + 6


def test_evaluate_number_takes_builder_expressions(tmp_path):
    env = _env(tmp_path)
    assert P.evaluate_number("V_CASE_L / 2 - V_SWITCH_PAD_T", env) == pytest.approx(193.9 / 2 - 13)
    assert P.evaluate_number("V_FAN_Y + V_FAN_HOLE_PITCH / 2", env) == pytest.approx(-30.825 + 16)
    assert P.evaluate_number("V_FAN_OPENING_D / 2 * sin(2 * MCC_FAN_GRILLE_SPOKE_PITCH)", env) == pytest.approx(19 * math.sin(math.radians(120)))
    assert P.evaluate_number("min(MCC_LID_CB_D, 100 mm)", env) == pytest.approx(8.0)
    with pytest.raises(P.ExpressionError, match="unknown name"):
        P.evaluate_number("V_NOPE + 1 mm", env)
    with pytest.raises(P.ExpressionError, match="units"):
        P.evaluate_number("V_CASE_L + V_N_DECK_X", env)


def test_environment_accepts_the_rows_registry_returns(tmp_path):
    """The runtime hands a builder the dicts registry() returns; the kit evaluates from them alone (no neutral text needed)."""
    setfile = _write_set(tmp_path / "a.json", parameters={"V_CASE_L": "193.9 mm", "V_N_DECK_X": "4", "V_FAN_Y": "-30.825 mm"},
                         flags={"Fan_Aperture": True})
    solved = P.parameter_set(setfile, "default")
    for inline in (True, False):
        rows = P.registry([P.CONSTANTS_CSV], [setfile], minmax_in_fusion=inline)
        assert any(r["kind"] == "solver" for r in rows) and any(";" in r["fusion"] for r in rows if r["fusion"]) == inline
        env = P.environment(rows, solved)
        want = P.environment(solved=solved)
        assert set(env) == set(want)
        for name in want:
            assert env[name].dim == want[name].dim and env[name].value == pytest.approx(want[name].value, rel=1e-12, abs=1e-12), name
        assert P.evaluate_number("V_CASE_L / 2 + MCC_GAP_FAR", env) == pytest.approx(193.9 / 2 + 16)


def test_registry_and_environment_do_not_apply_the_name_rule(tmp_path):
    """A test document may use its own prefix (T_*): only check_registry() enforces MCC_, BRK_ and CPN_."""
    extra = tmp_path / "s1.csv"
    extra.write_text("name,unit,expression,comment\nT_BLOCK,mm,10 mm,test block | src=tests | conf=assumed\n"
                     "T_TWICE,mm,2 * T_BLOCK + MCC_WALL,derived | src=tests\n", encoding="utf-8")
    rows = P.registry([P.CONSTANTS_CSV, extra])
    env = P.environment(rows)
    assert env["T_BLOCK"].value == 10 and env["T_TWICE"].value == 23
    assert any("T_BLOCK" in problem for problem in P.check_registry(P.read_registry(extra)))


def test_a_solver_output_may_not_shadow_a_registry_name():
    with pytest.raises(ValueError, match="may not reuse"):
        P.environment(solved={"values": {"MCC_WALL": 3.0}, "units": {"MCC_WALL": "mm"}})


# ---------------------------------------------------------------- caches and unused rows (A5, A6 of the gate of #76)


def test_clear_cache_forgets_constants_and_tables(tmp_path):
    csv_path = tmp_path / "c.csv"
    csv_path.write_text("name,unit,expression,comment\nMCC_T,mm,1 mm,t | src=tests | conf=assumed\n", encoding="utf-8")
    P.clear_cache()
    assert P.constants(csv_path)["MCC_T"] == 1.0
    csv_path.write_text("name,unit,expression,comment\nMCC_T,mm,2 mm,t | src=tests | conf=assumed\n", encoding="utf-8")
    assert P.constants(csv_path)["MCC_T"] == 1.0            # cached
    P.clear_cache()
    assert P.constants(csv_path)["MCC_T"] == 2.0


def test_an_unused_row_is_marked_and_no_expression_may_name_it(rows):
    unused = {r.name for r in rows if r.is_unused}
    assert {"MCC_INSERT_BORE_EXTRA", "MCC_SIDE_BOLT_HEAD_REC_D"} <= unused
    assert P.check_registry(rows) == []                               # the shipped registry names none
    bad = P.Row("MCC_BAD", "mm", "MCC_SIDE_BOLT_HEAD_REC_D + 1 mm", "uses the dead row", "tests", None)
    assert any("MCC_BAD" in p and "MCC_SIDE_BOLT_HEAD_REC_D" in p for p in P.check_registry(rows + [bad]))
