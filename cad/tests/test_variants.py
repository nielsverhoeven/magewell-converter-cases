"""The generated parameter sets (cad/parameters/variants/<slug>.json): fresh, total, numeric, and sufficient
to rebuild every OpenSCAD position the generator (#81) will need.  Offline and permanent: after the cutover
the solver and these files stay, and test_layout_parity.py then guards them against the committed fixture."""
from __future__ import annotations

import pytest

from cad import layout as LY
from cad import params
from cad.tests.support import layout_fixture, same

FIXTURE_CASES = layout_fixture()["cases"]
VARIANT_FILES = sorted(params.VARIANTS_DIR.glob("*.json"))
TEMPLATE = "pro-convert-for-ndi-to-hdmi"


def test_parameter_sets_are_fresh_and_total():
    assert LY.check_variants() == []


def test_ten_configurations_in_eight_files():
    """Nine are exported (eight slugs and `base_fan`); the template's `bare` (no rail, no lid vents) is never exported (P2-81 B6)."""
    assert len(VARIANT_FILES) == 8
    configs = [(f.stem, c) for f in VARIANT_FILES for c in params.parameter_set_configurations(f)]
    assert len(configs) == 10 and (TEMPLATE, "base_fan") in configs and (TEMPLATE, "bare") in configs
    assert sum(1 for _, c in configs if c == "default") == 8


def test_configurations_are_the_exported_ones_plus_the_test_ones():
    """B2 of the gate: `configurations(slug)` is `default` plus the sorted union of both case keys, and the exported subset is
    exactly params.exported_configurations."""
    for slug in params.case_slugs():
        doc = params.case_doc(slug)
        assert LY.configurations(slug) == ["default"] + sorted(set(doc["configurations"]) | set(doc["test_configurations"]))
        assert [c for c in LY.configurations(slug) if c not in doc["test_configurations"]] == params.exported_configurations(slug)
    assert "bare" in LY.configurations(TEMPLATE) and "bare" not in params.exported_configurations(TEMPLATE)
    assert sum(len(params.exported_configurations(s)) for s in params.case_slugs()) == 9


def test_sets_hold_no_constant_and_no_expression():
    for f in VARIANT_FILES:
        for cfg in params.parameter_set_configurations(f):
            ps = params.parameter_set(f, cfg)
            assert not any(n.startswith(("MCC_", "BRK_", "CPN_")) for n in ps["values"])
            raw = params.parameter_set_doc(f)["configurations"][cfg]["parameters"]
            assert all(params.parse_value(t) for t in raw.values())          # '<number> mm' or an integer, nothing else
            assert not any(any(ch in t for ch in "()*/+;,") for t in raw.values())


def test_the_committed_files_carry_the_contract_key_set():
    from cad.tests.test_layout_master import contract_keys

    keys, flags = contract_keys()
    for f in VARIANT_FILES:
        for cfg in params.parameter_set_configurations(f):
            ps = params.parameter_set(f, cfg)
            assert set(ps["values"]) == keys and set(ps["suppress"]) == flags, (f.name, cfg)
    ps = params.parameter_set(params.VARIANTS_DIR / f"{TEMPLATE}.json", "default")
    assert not any(n.startswith("Reserve_") for n in ps["suppress"])
    assert all(n.startswith("V_N_") == (ps["units"][n] == "none") for n in ps["values"])          # only counts are unitless
    assert all(ps["values"][n] >= 1 for n in ps["values"] if n.startswith("V_N_"))


def set_for(case):
    """The parameter set of a fixture case: read from the committed file (shipped) or built on the fly (synthetic)."""
    if case["shipped"]:
        slug, _, config = case["id"].partition("/")
        return params.parameter_set(params.VARIANTS_DIR / f"{slug}.json", config)
    sol = LY.solution_for(LY.device_from_doc(case["device"]), LY.Options(**case["options"]))
    raw = LY.parameter_set(sol)
    parsed = {n: params.parse_value(t) for n, t in raw["parameters"].items()}
    return {"values": {n: v for n, (v, _) in parsed.items()}, "units": {n: u for n, (_, u) in parsed.items()},
            "suppress": raw["flags"], "slots": raw["slots"]}


RUN_GROUPS = (("FARLO", "FarLo", "ABC", "far_low", "X0"), ("FARUP", "FarUp", "AB", "far_high", "X0"),
              ("EXH", "Exh", "A", "exhaust", "X0"), ("NEGX", "NegX", "A", "negx", "Y0"), ("LID", "Lid", "AB", "lid", "X0"))


@pytest.mark.parametrize("case", [c for c in FIXTURE_CASES if "vents" in c], ids=lambda c: c["id"])
def test_sets_rebuild_every_openscad_position_the_generator_needs(case):
    ps = set_for(case)
    v, flags, c = ps["values"], ps["suppress"], params.constants()
    l, d = case["layout"], case["derived"]
    same([v["V_CASE_L"], v["V_CASE_W"], v["V_CASE_Z_TOP"], v["V_CONN_Z"], v["V_PLATE_L"]],
         [l["L"], l["W"], d["z_top"], l["z_conn_c"], l["plate_l"]])
    same([v["V_DEV_X_LO"], v["V_DEV_X_HI"], v["V_DEV_Y_LO"], v["V_DEV_Y_HI"], v["V_DEV_Z_LO"], v["V_DEV_Z_HI"]],
         [l["x_dev_lo"], l["x_dev_hi"], l["y_dev_lo"], l["y_dev_hi"], l["z_dev_lo"], l["z_dev_hi"]])
    same([v["V_SIDEBOLT_X"], v["V_SIDEBOLT_Z"], v["V_FAN_Y"], v["V_SWITCH_Y"]],
         [l["side_bolt_x"], l["side_bolt_z"], l["fan_pos"][1], l["switch_pos"][1]])
    for bay, key in (("FANBAY", "fan_bay"), ("SPLITBAY", "splitter_bay")):
        same([v[f"V_{bay}_{a}_{b}"] for a in "XYZ" for b in ("LO", "HI")], [*l[f"{key}_x"], *l[f"{key}_y"], *l[f"{key}_z"]], bay)
    # table look-ups the master cannot compute itself
    same([v["V_BOSS_D"], v["V_INSERT_HOLE_D"], v["V_INSERT_DEPTH"]], [d["boss_d"], d["insert_hole_d"], d["insert_depth"]])
    same([v["V_FAN_OPENING_D"], v["V_FAN_HOLE_D"], v["V_FAN_HOLE_PITCH"]], d["fan"])
    # rings 1 and 2 are features; the outermost ring is the opening's edge (V_FAN_OPENING_D outside, V_FAN_RING3_ID inside)
    same([[v["V_FAN_RING1_OD"], v["V_FAN_RING1_ID"]], [v["V_FAN_RING2_OD"], v["V_FAN_RING2_ID"]],
          [v["V_FAN_OPENING_D"], v["V_FAN_RING3_ID"]]], d["rings"])
    same([v["V_SWITCH_BORE_D"], v["V_SWITCH_BODY_D"], v["V_SWITCH_PAD_D"], v["V_SWITCH_RECESS_T"], v["V_SWITCH_PAD_T"]], d["switch"])
    # slots: live slots carry the OpenSCAD positions and the connector's own diameters; the rest repeat the last live slot
    n = l["n_slots"]
    assert n == len(case["slots"]) == len(ps["slots"])
    same([v[f"V_SLOT{i}_X"] for i in range(1, n + 1)], l["slot_x"])
    assert [flags[f"Patch_Slot{i}"] for i in range(1, 5)] == [i > n for i in range(1, 5)]
    for i, s in enumerate(case["slots"], start=1):
        same(v[f"V_SLOT{i}_SEAT_D"], LY.cutout_d(s["part"]))
        same(v[f"V_SLOT{i}_WIN_D"], LY.aperture_window(s["part"]))
        assert ps["slots"][i - 1] == {"slot": s["slot"], "port": s["port_id"], "part": s["part"]}
    for i in range(n + 1, 5):
        assert [v[f"V_SLOT{i}_{k}"] for k in ("X", "SEAT_D", "WIN_D")] == [v[f"V_SLOT{n}_{k}"] for k in ("X", "SEAT_D", "WIN_D")]
    # lid fasteners: four corners are expressions of V_CASE_L/W and MCC_FASTENER_INSET; the mids come from the set
    e = c["MCC_FASTENER_INSET"]
    L, W = v["V_CASE_L"], v["V_CASE_W"]
    rebuilt = [[L / 2 - e, W / 2 - e], [L / 2 - e, -(W / 2 - e)], [-(L / 2 - e), W / 2 - e], [-(L / 2 - e), -(W / 2 - e)]]
    if not flags["Fastener_PatchMid"]:
        rebuilt.append([v["V_FAST_PATCH_MID_X"], W / 2 - e])
    if not flags["Fastener_FarMid"]:
        rebuilt.append([v["V_FAST_FAR_MID_X"], -(W / 2 - e)])
    same(rebuilt, l["lid_fastener_pos"])
    # vents: first centre + count per run, pitch from the constants
    pitches = {"LID": c["MCC_LID_VENT_SLOT_W"] + c["MCC_LID_VENT_WEB_W"]}
    vents = case["vents"]
    for group, flag, letters, key, axis in RUN_GROUPS:
        pitch = pitches.get(group, c["MCC_VENT_SLOT_W"] + c["MCC_VENT_WEB_W"])
        out = []
        lid_off = group == "LID" and not case["options"].get("lid_vents", True)        # the runs keep their values, only the flag is set
        for letter in letters:
            if lid_off or not flags[f"Vent_{flag}{letter}"]:
                out += [v[f"V_VENT_{group}{letter}_{axis}"] + j * pitch for j in range(v[f"V_N_VENT_{group}{letter}"])]
        same(out, vents[key], key)
    assert v["V_N_VENT_LID_ROWS"] == c["MCC_LID_VENT_ROWS"]
    same(v["V_VENT_LID_Y0"], vents["lid_field"]["y_lo"])
    # cradle: deck ribs from count, first position and pitch; far-flank ribs from the live instances
    cr = case["cradle"]
    same([v["V_DECK_X0"] + j * v["V_DECK_PITCH_X"] for j in range(v["V_N_DECK_X"])], cr["deck_x"])
    same([v["V_DECK_Y0"] + j * v["V_DECK_PITCH_Y"] for j in range(v["V_N_DECK_Y"])], cr["deck_y"])
    same([v[f"V_FARRIB{i}_X"] for i in range(1, 6) if not flags[f"Cradle_FarRib{i}"]], cr["flank"])
    # floor
    fk = {row[4]: row for row in case["floor_keepout"]}
    assert set(fk) == {"mount_rail", "side_bolt_web"}                 # D87.1: the floor holds the rail and the bolt web only
    same(v["V_SIDEBOLT_X"], fk["side_bolt_web"][0])


def test_options_drive_the_flags_and_the_reservations_stay_unflagged():
    def flags(slug, cfg="default"):
        return params.parameter_set(params.VARIANTS_DIR / f"{slug}.json", cfg)["suppress"]

    t, tf = flags(TEMPLATE), flags(TEMPLATE, "base_fan")
    assert t["Fan_Aperture"] is True and tf["Fan_Aperture"] is False          # fan option: the template ships without, base_fan with
    assert t["Switch_Toggle"] is True and tf["Switch_Toggle"] is True         # base_fan keeps fan_switch=false (T1-43 on compact)
    p = flags("pro-convert-hdmi-plus")
    assert p["Fan_Aperture"] is False and p["Switch_Toggle"] is False
    assert all(f["Floor_RailSill"] is False and f["Rail_Female"] is False for f in (t, tf, p))   # rail defaults to on
    for slug in params.case_slugs():
        assert not any(k.startswith("Reserve_") for k in flags(slug))
    bare = flags(TEMPLATE, "bare")                                              # both remaining options switch: rail and lid_vents
    on_t, on_bare = {k for k, v in t.items() if v}, {k for k, v in bare.items() if v}
    assert on_bare - on_t == {"Vent_LidA", "Vent_LidB", "Floor_RailSill", "Rail_Female"} and on_t <= on_bare
    hdmi_tx = flags("pro-convert-hdmi-tx")
    assert [hdmi_tx[f"Patch_Slot{i}"] for i in range(1, 5)] == [False, False, False, True]
    for slug in params.case_slugs():                                            # the flags P2-81 3.5 lists as set everywhere
        f = flags(slug)
        assert f["Cradle_FarRib5"], slug                                        # the 5th rib is live in no real configuration
        live = [k for k in f if k != "Cradle_FarRib5" and not k.startswith(("Patch_Slot", "Fan_", "Switch_"))]
        assert not any(f[k] for k in live), (slug, [k for k in live if f[k]])


def test_the_registry_the_runtime_reads_is_consistent_with_the_real_sets():
    rows = params.registry([params.CONSTANTS_CSV], VARIANT_FILES)
    names = [r["name"] for r in rows]
    assert len(names) == len(set(names)) and {"constant", "expression", "solver"} == {r["kind"] for r in rows}
    solver = [r for r in rows if r["kind"] == "solver"]
    assert len(solver) == 96 and all(r["fusion"] is None for r in solver)
    assert {r["unit"] for r in solver} == {"mm", ""}


def test_a_changed_constant_moves_the_solver_output(tmp_path, monkeypatch):
    """The solver reads the registry, not a copy: edit MCC_GAP_DEV in a copy and W follows."""
    import shutil
    from cad import params as P

    cad = tmp_path / "cad"
    shutil.copytree(P.CAD_DIR, cad, ignore=shutil.ignore_patterns("__pycache__", "tests", "tools"))
    text = (cad / "parameters" / "constants.csv").read_text(encoding="utf-8").replace("MCC_GAP_DEV,mm,2.0 mm", "MCC_GAP_DEV,mm,3.0 mm")
    (cad / "parameters" / "constants.csv").write_text(text, encoding="utf-8")
    before = LY.case_layout(LY.load_device(TEMPLATE), LY.Options()).W
    monkeypatch.setattr(P, "CONSTANTS_CSV", cad / "parameters" / "constants.csv")
    P._constants_cached.cache_clear()
    P._table_cached.cache_clear()
    after = LY.case_layout(LY.load_device(TEMPLATE), LY.Options()).W
    P._constants_cached.cache_clear()
    P._table_cached.cache_clear()
    assert after == pytest.approx(before + 1.0)
