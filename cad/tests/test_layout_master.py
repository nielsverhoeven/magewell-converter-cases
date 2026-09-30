"""The numbers the case master (issue #81, P2-81 section 3.5) needs beyond mcc_case_layout(): the table look-ups
(insert, fan grille, switch), the gusset-web tangent, the capacity of the master and its proof by a sweep, the capacity
refusals with their rule ids, the parking rule, and the exact key set of the parameter sets (99 keys, 24 flags).

Offline and permanent, except test_fan_grille_matches_the_oracle_geometry (needs OpenSCAD while lib/mcc exists).
"""
from __future__ import annotations

import dataclasses
import math
import re

import pytest

from cad import layout as LY
from cad import params
from cad.tests.support import layout_fixture, same

FIXTURE = layout_fixture()
CASES = FIXTURE["cases"]
TEMPLATE = "pro-convert-for-ndi-to-hdmi"


def sol_of(case):
    dev = LY.device_from_doc(case["device"]) if "device" in case else LY.load_device(case["slug"])
    return LY.solution_for(dev, LY.Options(**case["options"]), case["slug"])


def template(config="default"):
    return LY.solve(TEMPLATE, config)


# ---------------------------------------------------------------- derived values equal the OpenSCAD arithmetic


@pytest.mark.parametrize("case", CASES, ids=lambda c: c["id"])
def test_derived_values_equal_openscad(case):
    d, sol, c = case["derived"], sol_of(case), params.constants()
    same(c["MCC_FLOOR_T"] + sol.layout.H_int, d["z_top"], "z_top")
    same([sol.insert.boss_d, sol.insert.hole_d, sol.insert.depth], [d["boss_d"], d["insert_hole_d"], d["insert_depth"]], "insert")
    same([sol.fan.opening_d, sol.fan.hole_d, sol.fan.hole_pitch], d["fan"], "fan")
    same([list(r) for r in sol.fan.rings], d["rings"], "rings")
    same([sol.switch.bore_d, sol.switch.body_d, sol.switch.pad_d, sol.switch.recess_t, sol.switch.pad_t], d["switch"], "switch")
    # the outermost ring ends exactly on the opening (fan.scad:76-85): the master drops V_FAN_RING3_OD and uses the opening
    assert abs(sol.fan.rings[-1][0] - sol.fan.opening_d) <= 1e-9


def test_the_template_numbers_quoted_in_the_master_plan():
    """P2-81 3.5: template web tangent -0.0826 and 3.9391; the fan grille has 3 rings on a 38 mm opening."""
    sol = template()
    assert sol.web == (pytest.approx(-0.0826, abs=5e-5), pytest.approx(3.9391, abs=5e-5))
    assert sol.fan.opening_d == 38 and len(sol.fan.rings) == 3
    assert sol.fan.rings[2] == (pytest.approx(38.0), pytest.approx(34.4))


def test_the_web_tangent_is_a_tangent_of_the_hull_circle():
    """shell.scad:84-97 hulls a circle (r = boss radius - inset) with the bar corner (b, a); the closed form must lie
    on that circle with the radius perpendicular to the line to the corner (b * u + a * v = r * r)."""
    c = params.constants()
    u, v = LY.web_tangent()
    a = LY.insert_dims().boss_d / 2
    b = c["MCC_FASTENER_INSET"] - c["MCC_WEB_FACE_MARGIN"]
    r = a - c["MCC_WEB_HULL_INSET"]
    assert math.hypot(u, v) == pytest.approx(r, abs=1e-12)
    assert b * u + a * v == pytest.approx(r * r, abs=1e-12)
    assert u * (b - u) + v * (a - v) == pytest.approx(0, abs=1e-12)
    assert v > 0 and u < b


@pytest.mark.openscad
def test_fan_grille_matches_the_oracle_geometry(openscad_exe):
    """The 2-D grille of fan.scad exported as SVG (6 significant digits): every ring circle of the solver is a
    vertex radius of the oracle's shape, and the spoke tips sit at multiples of MCC_FAN_GRILLE_SPOKE_PITCH."""
    tools = pytest.importorskip("cad.tools.layout_oracle", reason="cad/tools removed after the cutover (#86)")
    g = LY.fan_grille()
    geo = tools.grille_geometry(g.opening_d, exe=openscad_exe)
    for od, idd in g.rings:
        for d in (od, idd):
            assert any(abs(r - d / 2) < 1.5e-3 for r in geo["radii"]), f"ring radius {d / 2} not in {geo['radii']}"
    c = params.constants()
    pitch, half = c["MCC_FAN_GRILLE_SPOKE_PITCH"], math.degrees(math.atan2(c["MCC_FAN_GRILLE_SPOKE_W"] / 2, g.opening_d / 2))
    expected = sorted({round((k * pitch + s * half) % 360, 1) for k in range(6) for s in (-1, 1)})
    assert geo["tip_angles"] == expected


# ---------------------------------------------------------------- capacity of the master: the reachable maximum


SWEEP_STEP = 0.1     # mm; P2-81 verdict B1 asks for steps of at most 0.5; 0.01 gives the same maxima (plan evidence)


def sweep_maxima() -> dict[str, int]:
    """Largest count the solver returns for ANY side-bolt position on ANY of the eight devices (the bolt x, relative to
    the device centre, over the whole device length)."""
    best = {k: 0 for k in ("slots", "far_ribs", "far_low", "far_high", "exhaust", "negx", "lid", "fasteners", "patch_ribs")}
    for slug in params.case_slugs():
        case = params.case_doc(slug)
        dev, opts = LY.load_device(case["device"]), LY.case_options(case)
        n = int(round(dev.size[0] / SWEEP_STEP))
        for i in range(n + 1):
            off = -dev.size[0] / 2 + i * SWEEP_STEP
            ports = tuple(dataclasses.replace(p, pos=(off, p.pos[1])) if p.id == "side_bolt" else p for p in dev.ports)
            sol = LY.solution_for(dataclasses.replace(dev, ports=ports), opts, slug)
            seen = {"slots": sol.layout.n_slots, "far_ribs": len(sol.cradle.far_ribs), "far_low": len(sol.vents.far_low),
                    "far_high": len(sol.vents.far_high), "exhaust": len(sol.vents.exhaust), "negx": len(sol.vents.negx),
                    "lid": len(sol.vents.lid), "fasteners": len(sol.layout.lid_fastener_pos), "patch_ribs": len(sol.cradle.patch_ribs)}
            for k, v in seen.items():
                best[k] = max(best[k], v)
    return best


def test_capacity_is_the_reachable_maximum():
    """P2-81 D81.7, both directions: no side-bolt position on any device exceeds CAPACITY, and every entry is reached."""
    best = sweep_maxima()
    for key in ("slots", "far_ribs", "far_low", "far_high", "exhaust", "negx", "lid"):
        assert best[key] == LY.CAPACITY[key], f"{key}: the sweep reaches {best[key]}, CAPACITY says {LY.CAPACITY[key]}"
    assert best["fasteners"] == 6 and best["patch_ribs"] == 0
    assert LY.CAPACITY["fan_rings"] == len(LY.fan_grille().rings) == 3


def test_the_capacity_table_and_the_key_set_agree_in_both_directions():
    keys, flags = contract_keys()
    cap = LY.CAPACITY
    assert sum(1 for k in keys if re.fullmatch(r"V_SLOT\d_X", k)) == sum(1 for k in flags if k.startswith("Patch_Slot")) == cap["slots"]
    assert sum(1 for k in keys if re.fullmatch(r"V_FARRIB\d_X", k)) == sum(1 for k in flags if k.startswith("Cradle_FarRib")) == cap["far_ribs"]
    for group, (entry, flag) in LY.RUN_GROUPS.items():
        letters = LY.run_letters(group)
        assert len(letters) == cap[entry]
        axis = "Y0" if group == "NEGX" else "X0"
        assert {k for k in keys if re.fullmatch(rf"V_VENT_{group}[A-C]_{axis}", k)} == {f"V_VENT_{group}{x}_{axis}" for x in letters}
        assert {k for k in flags if re.fullmatch(rf"Vent_{flag}[A-C]", k)} == {f"Vent_{flag}{x}" for x in letters}
    assert sum(1 for k in keys if re.fullmatch(r"V_FAN_RING\d_ID", k)) == cap["fan_rings"]
    assert sum(1 for k in keys if re.fullmatch(r"V_FAN_RING\d_OD", k)) == cap["fan_rings"] - 1


# ---------------------------------------------------------------- capacity: what does not fit the master is refused, with its rule id


def test_every_shipped_configuration_fits_the_master():
    for slug in params.case_slugs():
        for cfg in LY.configurations(slug):
            assert LY.capacity_problems(LY.solve(slug, cfg)) == [], f"{slug}/{cfg}"


def test_the_fixture_devices_that_fit_are_exactly_the_ones_the_parameter_set_accepts():
    for case in CASES:
        sol = sol_of(case)
        assert (LY.capacity_problems(sol) == []) == (_writes(sol)), case["id"]


def _writes(sol) -> bool:
    try:
        LY.parameter_set(sol)
        return True
    except LY.CapacityError:
        return False


def _with(sol, **changes):
    out = sol
    for member, value in changes.items():
        out = dataclasses.replace(out, **{member: value})
    return out


def _layout(sol, **fields):
    return dataclasses.replace(sol.layout, **fields)


def _cradle(sol, **fields):
    return dataclasses.replace(sol.cradle, **fields)


def _vents(sol, **fields):
    return dataclasses.replace(sol.vents, **fields)


RUN = LY.Run(0.0, 1)
CAPACITY_CASES = {
    "slots": (lambda s: _with(s, layout=_layout(s, n_slots=5)), "T1-02: 5 connector slots"),
    "deck": (lambda s: _with(s, cradle=_cradle(s, deck_x=LY.DeckGrid(0, 0.0, 1.0))), "T1-39: deck ladder counts 0 x 2"),
    "far ribs": (lambda s: _with(s, cradle=_cradle(s, far_ribs=tuple(float(i) for i in range(6)))), "T1-81.2: 6 far-flank ribs"),
    "far low runs": (lambda s: _with(s, vents=_vents(s, far_low=(RUN,) * 4)), "T1-81.3: vent group FARLO forms 4 runs"),
    "far high runs": (lambda s: _with(s, vents=_vents(s, far_high=(RUN,) * 3)), "T1-81.3: vent group FARUP forms 3 runs"),
    "exhaust runs": (lambda s: _with(s, vents=_vents(s, exhaust=(RUN,) * 2)), "T1-81.3: vent group EXH forms 2 runs"),
    "negx runs": (lambda s: _with(s, vents=_vents(s, negx=(RUN,) * 2)), "T1-81.3: vent group NEGX forms 2 runs"),
    "lid runs": (lambda s: _with(s, vents=_vents(s, lid=(RUN,) * 3)), "T1-81.3: vent group LID forms 3 runs"),
    "patch rib": (lambda s: _with(s, cradle=_cradle(s, patch_ribs=(5.0,))), "T1-81.4: patch-flank ribs"),
    "rings": (lambda s: _with(s, fan=dataclasses.replace(s.fan, rings=s.fan.rings[:2])), "T1-81.5: the fan grille has 2 rings"),
    "ring without hole": (lambda s: _with(s, fan=dataclasses.replace(s.fan, rings=((12.0, 0.0),) + s.fan.rings[1:])),
                          "T1-81.5: a fan grille ring without a hole"),
    "boss inset": (lambda s: _with(s, layout=_layout(s, lid_fastener_pos=((80.0, 60.0),) + s.layout.lid_fastener_pos[1:])),
                   "T1-81.6: lid fastener"),
    "tripod insert": (lambda s: _with(s, options=dataclasses.replace(s.options, tripod_insert=True)), "T1-81.7: option tripod_insert"),
}


@pytest.mark.parametrize("name", sorted(CAPACITY_CASES))
def test_a_case_beyond_the_master_is_refused_with_its_rule_id(name):
    make, reason = CAPACITY_CASES[name]
    sol = make(template())
    assert any(p.startswith(reason) for p in LY.capacity_problems(sol)), LY.capacity_problems(sol)
    with pytest.raises(LY.CapacityError, match="pro-convert-for-ndi-to-hdmi/default"):
        LY.parameter_set(sol)


def test_solve_itself_never_refuses_for_capacity():
    """solve() returns the numbers of a case the master cannot hold: the rules (#78) need them to report the violation."""
    dev = LY.device_from_doc({"slug": "x", "family": "compact", "size": [100.9, 60.2, 23.3], "ports": [
        {"id": f"p{i}", "face": [1, 0, 0], "pos": [i, 0], "kind": "rj45", "dir": "bidir", "panel": "NE8FDP-B", "confidence": "assumed"}
        for i in range(5)] + [{"id": "side_bolt", "face": [0, -1, 0], "pos": [0, 0], "kind": "tripod_1_4_20", "dir": "none",
                               "panel": "none", "confidence": "assumed"}]})
    assert LY.solution_for(dev, LY.Options(tripod_insert=True)).layout.n_slots == 5


# ---------------------------------------------------------------- the parking rule of P2-81 3.5


def _set(sol):
    raw = LY.parameter_set(sol)
    return ({n: params.parse_value(t)[0] for n, t in raw["parameters"].items()}, raw["flags"])


def test_an_unused_slot_repeats_the_last_live_slot_and_is_flagged():
    v, f = _set(LY.solve("pro-convert-hdmi-tx"))                  # three connectors
    assert [f[f"Patch_Slot{i}"] for i in range(1, 5)] == [False, False, False, True]
    for k in ("X", "SEAT_D", "WIN_D"):
        assert v[f"V_SLOT4_{k}"] == v[f"V_SLOT3_{k}"]


def test_the_unused_far_rib_repeats_the_last_live_rib():
    v, f = _set(template())
    live = [v[f"V_FARRIB{i}_X"] for i in range(1, 5)]
    assert live == sorted(live) and [f[f"Cradle_FarRib{i}"] for i in range(1, 6)] == [False] * 4 + [True]
    assert v["V_FARRIB5_X"] == live[-1]


def test_an_unused_vent_run_repeats_the_last_live_run_with_count_one():
    """No real configuration parks a run (every group is live at its capacity); a case with a short group does."""
    sol = template()
    v, f = _set(_with(sol, vents=_vents(sol, far_low=sol.vents.far_low[:2])))
    assert f["Vent_FarLoC"] and not f["Vent_FarLoB"]
    assert v["V_VENT_FARLOC_X0"] == v["V_VENT_FARLOB_X0"] and v["V_N_VENT_FARLOC"] == 1
    v, f = _set(_with(sol, vents=_vents(sol, far_high=sol.vents.far_high[:1])))
    assert f["Vent_FarUpB"] and v["V_VENT_FARUPB_X0"] == v["V_VENT_FARUPA_X0"] and v["V_N_VENT_FARUPB"] == 1


def test_a_missing_mid_fastener_sits_at_x_zero():
    sol = LY.solution_for(LY.device_from_doc(next(c["device"] for c in CASES if c["id"] == "synthetic/four-fasteners")), LY.Options())
    v, f = _set(sol)
    assert f["Fastener_PatchMid"] and f["Fastener_FarMid"]
    assert v["V_FAST_PATCH_MID_X"] == 0 and v["V_FAST_FAR_MID_X"] == 0


def test_an_empty_intake_sub_band_takes_the_z_pair_of_the_other_one():
    sol = template()
    upper_empty = _with(sol, vents=_vents(sol, far_high=(), upper_z=(sol.vents.lower_z[1], sol.vents.lower_z[1])))
    v, f = _set(upper_empty)
    assert (v["V_VENT_FARUP_Z_LO"], v["V_VENT_FARUP_Z_HI"]) == (v["V_VENT_FARLO_Z_LO"], v["V_VENT_FARLO_Z_HI"])
    assert f["Vent_FarUpA"] and f["Vent_FarUpB"]
    lower_empty = _with(sol, vents=_vents(sol, far_low=(), lower_z=(5.0, 5.0)))
    v, f = _set(lower_empty)
    assert (v["V_VENT_FARLO_Z_LO"], v["V_VENT_FARLO_Z_HI"]) == (v["V_VENT_FARUP_Z_LO"], v["V_VENT_FARUP_Z_HI"])
    assert f["Vent_FarLoA"] and f["Vent_FarLoB"] and f["Vent_FarLoC"]


def test_a_group_without_a_live_run_is_parked_at_the_device_box_centre():
    sol = template()
    v, f = _set(_with(sol, vents=_vents(sol, exhaust=())))
    assert f["Vent_ExhA"] and v["V_VENT_EXHA_X0"] == pytest.approx(sol.layout.x_dev_c) and v["V_N_VENT_EXHA"] == 1
    v, f = _set(_with(sol, vents=_vents(sol, negx=())))
    assert f["Vent_NegXA"] and v["V_VENT_NEGXA_Y0"] == pytest.approx(sol.layout.y_dev_c)


def test_lid_vents_off_suppresses_both_lid_runs_but_keeps_their_values():
    sol = _with(template(), options=dataclasses.replace(template().options, lid_vents=False))
    v, f = _set(sol)
    assert f["Vent_LidA"] and f["Vent_LidB"]
    assert v["V_N_VENT_LIDA"] == 11 and v["V_N_VENT_LIDB"] == 11


# ---------------------------------------------------------------- the key set IS the contract (P2-81 3.5 after the verdict: 99 keys, 24 flags)


def contract_keys() -> tuple[set[str], set[str]]:
    keys = {"V_CASE_L", "V_CASE_W", "V_CASE_Z_TOP", "V_CONN_Z", "V_PLATE_L", "V_BOSS_D", "V_INSERT_HOLE_D", "V_INSERT_DEPTH",
            "V_FAST_PATCH_MID_X", "V_FAST_FAR_MID_X", "V_WEB_TAN_U", "V_WEB_TAN_V",
            "V_N_DECK_X", "V_DECK_X0", "V_DECK_PITCH_X", "V_N_DECK_Y", "V_DECK_Y0", "V_DECK_PITCH_Y",
            "V_STRAP_POS_X", "V_STRAP_NEG_X", "V_STRAP_Y", "V_SIDEBOLT_X", "V_SIDEBOLT_Z",
            "V_VENT_FARLO_Z_LO", "V_VENT_FARLO_Z_HI", "V_VENT_FARUP_Z_LO", "V_VENT_FARUP_Z_HI",
            "V_VENT_NEGX_Z_LO", "V_VENT_NEGX_Z_HI", "V_VENT_NEGXA_Y0", "V_N_VENT_NEGXA", "V_VENT_LID_Y0", "V_N_VENT_LID_ROWS",
            "V_FAN_Y", "V_FAN_OPENING_D", "V_FAN_HOLE_D", "V_FAN_HOLE_PITCH", "V_FAN_RING3_ID",
            "V_SWITCH_Y", "V_SWITCH_BORE_D", "V_SWITCH_BODY_D", "V_SWITCH_PAD_D", "V_SWITCH_RECESS_T", "V_SWITCH_PAD_T"}
    keys |= {f"V_DEV_{a}_{b}" for a in "XYZ" for b in ("LO", "HI")}
    keys |= {f"V_SLOT{i}_{k}" for i in range(1, 5) for k in ("X", "SEAT_D", "WIN_D")}
    keys |= {f"V_FARRIB{i}_X" for i in range(1, 6)}
    for s in ("FARLOA", "FARLOB", "FARLOC", "FARUPA", "FARUPB", "EXHA", "LIDA", "LIDB"):
        keys |= {f"V_VENT_{s}_X0", f"V_N_VENT_{s}"}
    keys |= {f"V_FAN_RING{i}_{k}" for i in (1, 2) for k in ("OD", "ID")}
    keys |= {f"V_{bay}_{a}_{b}" for bay in ("FANBAY", "SPLITBAY") for a in "XYZ" for b in ("LO", "HI")}
    flags = {f"Patch_Slot{i}" for i in range(1, 5)} | {"Fastener_PatchMid", "Fastener_FarMid"}
    flags |= {f"Cradle_FarRib{i}" for i in range(1, 6)}
    flags |= {"Vent_FarLoA", "Vent_FarLoB", "Vent_FarLoC", "Vent_FarUpA", "Vent_FarUpB", "Vent_ExhA", "Vent_NegXA", "Vent_LidA", "Vent_LidB"}
    flags |= {"Fan_Aperture", "Switch_Toggle", "Floor_RailSill", "Rail_Female"}
    return keys, flags


def test_the_key_set_is_exactly_99_keys_and_24_flags_of_the_master_contract():
    keys, flags = contract_keys()
    assert (len(keys), len(flags)) == (99, 24)
    raw = LY.parameter_set(template())
    assert set(raw["parameters"]) == keys
    assert set(raw["flags"]) == flags


def test_every_value_is_a_millimetre_length_or_a_count_of_at_least_one():
    raw = LY.parameter_set(template())
    for name, text in raw["parameters"].items():
        value, unit = params.parse_value(text)
        if name.startswith("V_N_"):
            assert unit == "none" and isinstance(value, int) and value >= 1, (name, text)
        else:
            assert unit == "mm", (name, text)
    assert all(isinstance(v, bool) for v in raw["flags"].values())


def _setup(case):
    dev = LY.device_from_doc(case["device"]) if "device" in case else LY.load_device(case["slug"])
    return dev, LY.Options(**case["options"])


@pytest.mark.parametrize("case", [c for c in CASES if "vents" in c], ids=lambda c: c["id"])
def test_slot_totals_per_group_equal_the_length_of_the_openscad_lists(case):
    """The per-group totals the rules of #78 need (intake area, T1-30) are the lengths of the oracle's lists."""
    v = LY.vent_plan(LY.case_layout(*_setup(case)))
    vents = case["vents"]
    assert [v.n_far_low, v.n_far_high, v.n_exhaust, v.n_negx, v.n_lid] == [
        len(vents["far_low"]), len(vents["far_high"]), len(vents["exhaust"]), len(vents["negx"]), len(vents["lid"])]
