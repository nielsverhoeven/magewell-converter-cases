#!/usr/bin/env python3
"""layout_oracle: the OpenSCAD side of S0 for issue #77 (transition tool, deleted at the cutover #86).

    python -m cad.tools.layout_oracle write     re-derive cad/fixtures/scad_layout.json from OpenSCAD
    python -m cad.tools.layout_oracle check     fail if the committed fixture differs from a fresh OpenSCAD run

One temporary harness (written at run time, never committed) `use`s layout.scad, ports.scad, vents.scad,
cradle.scad, fasteners.scad, switch.scad and poe_splitter.scad, `include`s constants.scad and the eight
device files, and for every case echoes the solver outputs of lib/mcc losslessly:

    mcc_case_layout, mcc_slot_assignment, mcc_end_zone, mcc_cradle_deck, mcc_floor_keepout,
    mcc_warn_unmeasured, mcc_fan_switch_enabled                                (every case)
    _mcc_far_wall_excl + _mcc_vent_slot_centers (far low/high), the exhaust, -X wall and lid-vent runs,
    _mcc_lid_vent_field, _mcc_cradle_deck_grid, _mcc_far_flank_rib_x, the patch-flank rule   (shipped cases)

`mcc_vents()` and `mcc_cradle()` are MODULES whose list arithmetic cannot be called; the harness repeats
that arithmetic literally from vents.scad:117-151 and cradle.scad:184-190,247 (line references in the
harness text), so a change there must be mirrored here (the oracle tree is frozen until #86).
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path
from typing import Any

from cad import params
from cad.tools import openscad_runner as osr
from cad.tools.scad_export import REPO, deep_compare, dumps, to_json

LIB = REPO / "lib" / "mcc"
FIXTURE_PATH = Path(__file__).resolve().parents[1] / "fixtures" / "scad_layout.json"
ORACLE_FILES = ["constants", "layout", "ports", "vents", "cradle", "fasteners", "switch", "poe_splitter"]

CFG_KEYS = ("fan", "splitter", "fan_switch", "tripod_insert", "lid_vents", "rail", "fan_y")


def case_matrix() -> list[dict]:
    """The cases of the fixture: the ten configurations (nine exported and the template's `bare`), then a fan x fan_switch matrix on every
    device and a fan_y override on the template (all valid: no OpenSCAD assert fires)."""
    cases: list[dict] = []
    seen: list[tuple] = []

    def add(case_id: str, slug: str, options: dict, shipped: bool) -> None:
        key = (slug, tuple(sorted(options.items())))
        if key in seen:
            return
        seen.append(key)
        cases.append({"id": case_id, "slug": slug, "options": options, "shipped": shipped})

    for slug in params.case_slugs():
        c = params.case_doc(slug)
        add(f"{slug}/default", slug, dict(c["options"]), True)
        for name, over in {**c["configurations"], **c["test_configurations"]}.items():
            add(f"{slug}/{name}", slug, {**c["options"], **over}, True)
    for slug in params.case_slugs():
        base = params.case_doc(slug)["options"]
        for fan in (False, True):
            add(f"{slug}/fan={int(fan)},fan_switch=0", slug, {**base, "fan": fan, "fan_switch": False}, False)
    tmpl = "pro-convert-for-ndi-to-hdmi"
    add(f"{tmpl}/fan_y=-25", tmpl, {**params.case_doc(tmpl)["options"], "fan": True, "fan_switch": False, "fan_y": -25.0}, False)
    return cases


def _port(pid: str, face: list, pos: list, kind: str, panel: str, conf: str = "assumed", dir_: str = "bidir") -> dict:
    return {"id": pid, "face": face, "pos": pos, "kind": kind, "dir": dir_, "panel": panel, "confidence": conf}


_SIDE = _port("side_bolt", [0, -1, 0], [0, 0], "tripod_1_4_20", "none", dir_="none")


def _synthetic_device(slug: str, size: list, ports: list, bolt_pos: list | None = None) -> dict:
    side = dict(_SIDE, pos=bolt_pos or [0, 0])
    return {"slug": slug, "family": "compact", "size": size, "ports": ports + [side]}


_RJ45 = _port("rj45", [-1, 0, 0], [15, 0], "rj45", "NE8FDP-B")
_HDMI = _port("hdmi_out", [1, 0, 0], [0, 0], "hdmi_a", "NAHDMI-W-B")

# Devices that do not exist but reach branches of the solver that the eight real ones do not.  Each must
# pass every Tier-1 assert inside mcc_case_layout() (an assert aborts the OpenSCAD run).
SYNTHETIC: list[dict] = [
    {"id": "synthetic/one-port", "note": "one slot: pitch 0, no patch mid, six fasteners",
     "device": _synthetic_device("syn-one-port", [100.9, 60.2, 23.3], [_HDMI])},
    {"id": "synthetic/two-ports", "note": "one port per end: the single gap mid fastener at x = 0",
     "device": _synthetic_device("syn-two-ports", [100.9, 60.2, 23.3], [_RJ45, _HDMI])},
    {"id": "synthetic/four-fasteners", "note": "lid span <= 180: four fasteners, no mids",
     "device": _synthetic_device("syn-four-fasteners", [100.9, 60.2, 23.3],
                                 [_RJ45, _port("usb_host", [1, 0, 0], [0, 0], "usb_a", "DBA-BL-B")])},
    {"id": "synthetic/tight-pitch", "note": "six fasteners but the slot gap is too narrow: only the far mid, at index 4 (vents.scad:194 quirk)",
     "device": _synthetic_device("syn-tight-pitch", [88.5, 60.2, 23.3],
                                 [_RJ45, _port("usb_b", [-1, 0, 0], [-16, 0], "usb_b", "NAUSB-W-B"),
                                  _port("hdmi_out", [1, 0, 0], [-16, 0], "hdmi_a", "NAHDMI-W-B"),
                                  _port("usb_host", [1, 0, 0], [16, 0], "usb_a", "DBA-BL-B")])},
    {"id": "synthetic/bolt-near-minus-x", "note": "side bolt near the -X end: one far-flank segment with a midpoint rib",
     "device": _synthetic_device("syn-bolt-minus", [100.9, 60.2, 23.3], [_RJ45, _HDMI], [-40, 0])},
    {"id": "synthetic/bolt-near-plus-x", "note": "side bolt near the +X end: one far-flank segment, the exhaust run squeezed",
     "device": _synthetic_device("syn-bolt-plus", [100.9, 60.2, 23.3], [_RJ45, _HDMI], [45, 0])},
]
for _s in SYNTHETIC:
    _s["options"] = {"fan": False, "splitter": False, "tripod_insert": False, "lid_vents": True}
    _s["shipped"] = False
    _s["slug"] = _s["device"]["slug"]

# Pure-function probes with edge arguments (half-way roundings, exact floor boundaries, touching exclusions,
# segments of exactly 40 mm, empty results).  The Python side calls the same function with the same arguments.
PROBES: dict[str, list] = {
    "deck_grid": [[0, 61], [0, 39], [0, 83], [0, 105], [0, 60.999999999999], [0, 61.000000000001], [0, 6.0], [0, 10],
                  [0, 50], [0, 300], [-49.95, 56.95], [-63.925, 2.275]],
    "vent_centres": [[0, 26.4, [], None, None], [0, 26.399999999999, [], None, None], [0, 26.400000000001, [], None, None],
                     [0, 1.0, [], None, None], [0, 1.2, [], None, None], [0, 30, [[-1, 31]], None, None],
                     [0, 20, [[5, 7]], None, None], [0, 20, [[5.6, 7], [9, 9]], None, None],
                     [-46.95, 53.95, [[0, 7], [-18.78, -6.5]], None, None],
                     [-46.95, 53.95, [[-8.5, 15.5], [-18.78, -6.5]], None, None],
                     [-41.95, 48.95, [[0, 7]], 2.0, 1.6], [0, 77.325, [], None, None]],
    "flank": [[-46.95, 53.95, 3.5], [-46.95, 53.95, -60], [-46.95, 53.95, 100], [-46.95, 53.95, -36.5], [-46.95, 53.95, 45],
              [-8, 108, 55.5], [-8, 108, 55.5000001], [-8, 108, 55.4999999], [0, 40, 20], [-46.95, 53.95, -38.4]],
    "nearest_zero": [[[-5, 5]], [[5, -5]], [[3, -3.004]], [[2, 3, 4]], [[0, 0]], [[0.001, -0.001]], [[0]], [[-7, -2, 9]],
                     [[43.86, 76.14]]],   # one argument: the list
    "in_any_range": [[0, 1, [[0.5, 2]]], [0, 0.5, [[0.5, 2]]], [2, 3, [[0.5, 2]]], [2.0000001, 3, [[0.5, 2]]], [0, 1, []]],
}
_PROBE_FN = {"deck_grid": "_mcc_cradle_deck_grid({0}, {1})", "flank": "_mcc_far_flank_rib_x({0}, {1}, {2})",
             "nearest_zero": "_mcc_nearest_zero({0})", "in_any_range": "_mcc_in_any_range({0}, {1}, {2})"}


def _lit(v: Any) -> str:
    if isinstance(v, list):
        return "[" + ", ".join(_lit(x) for x in v) + "]"
    if isinstance(v, bool):
        return "true" if v else "false"
    if isinstance(v, (int, float)):
        return repr(float(v))
    return json.dumps(v)


def _probe_call(name: str, args: list) -> str:
    if name == "vent_centres":
        lo, hi, excl, sw, ww = args
        extra = "" if sw is None else f", {_lit(sw)}, {_lit(ww)}"
        return f"_mcc_vent_slot_centers({_lit(lo)}, {_lit(hi)}, {_lit(excl)}{extra})"
    return _PROBE_FN[name].format(*[_lit(a) for a in args])


def _device_scad(dev: dict) -> str:
    def port(p: dict) -> str:
        keys = ("id", "face", "pos", "kind", "dir", "panel", "confidence")
        return "[" + ", ".join(f'["{k}", {_lit(p[k])}]' for k in keys) + "]"

    ports = ", ".join(port(p) for p in dev["ports"])
    return (f'[["slug", {_lit(dev["slug"])}], ["family", {_lit(dev["family"])}], ["size", {_lit(dev["size"])}], '
            f'["source", "synthetic"], ["ports", [{ports}]]]')


def _scad_value(v: Any) -> str:
    if isinstance(v, bool):
        return "true" if v else "false"
    return repr(float(v)) if isinstance(v, (int, float)) else json.dumps(v)


def _cfg(options: dict) -> str:
    return "[" + ", ".join(f'["{k}", {_scad_value(options[k])}]' for k in CFG_KEYS if k in options) + "]"


def device_var(slug: str) -> str:
    return "MCC_DEV_" + slug.upper().replace("-", "_")


PRELUDE = r"""

// mcc_vents() arithmetic, vents.scad:117-151 (module: not callable)
function vent_probe(l) = let(
    x_dev_lo = struct_val(l, "x_dev_lo"), x_dev_hi = struct_val(l, "x_dev_hi"),
    W = struct_val(l, "W"), x_bolt = struct_val(l, "side_bolt_x"),
    far = _mcc_far_wall_excl(l),
    far_c = [for (band = far) _mcc_vent_slot_centers(x_dev_lo, x_dev_hi, band[2])],
    sb_disc_d = struct_val(mcc_side_bolt_keepout(), "disc_d"),
    x_far_mid = _mcc_lid_far_mid_x(l),
    boss_od_lid = MCC_BOSS_MIN_RATIO * struct_val(MCC_INSERT_M3, "od"),
    mid_w = boss_od_lid + 2 * 2.0,
    mid_excl = is_undef(x_far_mid) ? [] : [[x_far_mid - mid_w / 2, x_far_mid + mid_w / 2]],
    ex_lo = max(x_bolt + sb_disc_d / 2, x_dev_lo),
    exhaust = (x_dev_hi > ex_lo) ? _mcc_vent_slot_centers(ex_lo, x_dev_hi, mid_excl) : [],
    negx = _mcc_vent_slot_centers(0, W / 2 - MCC_WALL, []),
    f = _mcc_lid_vent_field(l),
    lid = _mcc_vent_slot_centers(struct_val(f, "x_lo"), struct_val(f, "x_hi"), struct_val(f, "excl"),
                                 MCC_LID_VENT_SLOT_W, MCC_LID_VENT_WEB_W)
) [["far_excl", far], ["far_low", far_c[0]], ["far_high", far_c[1]], ["exhaust", exhaust], ["negx", negx],
   ["lid_field", f], ["lid", lid]];

// mcc_cradle() arithmetic, cradle.scad:166-190 and 247 (module: not callable)
function cradle_probe(l) = let(
    x_dev_lo = struct_val(l, "x_dev_lo"), x_dev_hi = struct_val(l, "x_dev_hi"),
    y_dev_lo = struct_val(l, "y_dev_lo"), y_dev_hi = struct_val(l, "y_dev_hi"),
    plate_l = struct_val(l, "plate_l"), x_bolt = struct_val(l, "side_bolt_x"),
    LIP = MCC_WALL,
    deck_x = [x_dev_lo - LIP, x_dev_hi + LIP], deck_y = [y_dev_lo - LIP, y_dev_hi + LIP],
    patch = [for (x = [x_dev_lo + LIP, x_dev_hi - LIP]) if (abs(x) > plate_l / 2 - 3) x]
) [["deck_x", _mcc_cradle_deck_grid(deck_x[0], deck_x[1])], ["deck_y", _mcc_cradle_deck_grid(deck_y[0], deck_y[1])],
   ["flank", _mcc_far_flank_rib_x(x_dev_lo, x_dev_hi, x_bolt)], ["patch", patch]];

// the numbers the case master needs that no library function returns (P2-81 3.5): the literal arithmetic of
// fan.scad:65-106,151, switch.scad:34-40,102,136, fasteners.scad:33 and shell.scad:228,232 (line references
// as written in each source).  The tangent point of the gusset web has no OpenSCAD counterpart: the hull is
// computed by the geometry kernel, so the Python closed form is tested algebraically instead.
function derived(l) = let(
    fan = mcc_fan_spec(MCC_FAN_DEFAULT),
    frame = struct_val(fan, "frame"),
    opening_d = frame[0] - 2,
    r_max = opening_d / 2,
    n_rings = max(1, floor(r_max / (1.8 + 3.0))),
    pitch = r_max / n_rings,
    rings = [for (i = [1 : 1 : n_rings]) let(r_out = i * pitch, r_in = max(0, r_out - 1.8)) [2 * r_out, 2 * r_in]],
    sw = mcc_switch_spec(MCC_SWITCH_DEFAULT),
    recess_t = struct_val(sw, "actuator_proud_h") + MCC_SWITCH_FLUSH_CLR,
    pad_t = _mcc_switch_pad_t(sw, MCC_WALL),
    ins = MCC_INSERT_M3
) [["z_top", MCC_FLOOR_T + struct_val(l, "H_int")],
   ["boss_d", MCC_BOSS_MIN_RATIO * struct_val(ins, "od")],
   ["insert_hole_d", struct_val(ins, "hole_d")], ["insert_depth", struct_val(ins, "len") + 1],
   ["fan", [opening_d, struct_val(fan, "hole_d"), struct_val(fan, "pitch")]], ["rings", rings],
   ["switch", [struct_val(sw, "hole_d") + MCC_HOLE_COMP, struct_val(sw, "body_d"), struct_val(sw, "pad_d"), recess_t, pad_t]]];

function probe(dev, cfg, deep) = let(l = mcc_case_layout(dev, cfg)) concat([
    ["layout", l],
    ["slots", mcc_slot_assignment(dev)],
    ["end_zone", [mcc_end_zone(dev, "neg"), mcc_end_zone(dev, "pos")]],
    ["cradle_deck", mcc_cradle_deck(dev)],
    ["floor_keepout", mcc_floor_keepout(dev, cfg)],
    ["sw_enabled", mcc_fan_switch_enabled(cfg)],
    ["weak", [for (p = mcc_warn_unmeasured(dev)) mcc_port_id(p)]],
    ["derived", derived(l)],
], deep ? [["vents", vent_probe(l)], ["cradle", cradle_probe(l)]] : []);

function accessors() = [
    ["panel_parts", [for (row = MCC_PANEL_PARTS) let(part = row[0]) [part, [
        ["hole_d", mcc_panel_hole_d(part)], ["depth", mcc_panel_depth(part)], ["max_t", mcc_panel_max_t(part)],
        ["plug_len", mcc_plug_len(part)], ["bend", mcc_bend_envelope(part)], ["kind", mcc_panel_kind(part)],
        ["confidence", mcc_panel_confidence(part)], ["bay_depth", mcc_bay_depth(part)],
        ["cutout_d", mcc_cutout_d(part)], ["aperture_window", mcc_aperture_window(part)],
        ["plug_axial", mcc_plug_axial(part)]]]]],
    ["dev_side_allow", [for (row = MCC_DEV_SIDE_ALLOW) [row[0], mcc_dev_side_allow(row[0])]]],
    ["plug_axial", [for (row = MCC_PLUG_AXIAL) [row[0], mcc_plug_axial(row[0])]]],
    ["fan_spec", [for (row = MCC_FANS) [row[0], mcc_fan_spec(row[0])]]],
    ["switch_spec", [for (row = MCC_SWITCHES) [row[0], mcc_switch_spec(row[0])]]],
    ["splitter_spec", [for (row = MCC_SPLITTERS) [row[0], mcc_splitter_spec(row[0])]]],
    ["side_bolt_keepout", mcc_side_bolt_keepout()],
];
"""


def harness_text(cases: list[dict], slugs: list[str]) -> str:
    lines = ["include <mcc/constants.scad>"]
    lines += [f"use <mcc/{n}.scad>" for n in ORACLE_FILES if n != "constants"]
    lines += [f"include <mcc/devices/{s}.scad>" for s in slugs]
    lines.append(osr.ENCODER_SCAD)
    lines.append(f"SLUGS = [{', '.join(json.dumps(s) for s in slugs)}];")
    lines.append(f"DEVS = [{', '.join(device_var(s) for s in slugs)}];")
    lines.append(PRELUDE)
    lines.append('echo("A", oracle_enc(accessors()));')
    for i, c in enumerate(cases):
        dev = _device_scad(c["device"]) if "device" in c else f"DEVS[{slugs.index(c['slug'])}]"
        deep = "true" if (c["shipped"] or "device" in c) else "false"
        lines.append(f'echo("K", {i}, oracle_enc(probe({dev}, {_cfg(c["options"])}, {deep})));')
    for name, arg_lists in PROBES.items():
        for j, args in enumerate(arg_lists):
            lines.append(f'echo("P", "{name}", {j}, oracle_enc({_probe_call(name, args)}));')
    return "\n".join(lines) + "\n"


def scrape(exe: Path | None = None) -> dict:
    exe = exe or osr.find_openscad()
    if exe is None:
        raise FileNotFoundError("OpenSCAD not found (MCC_OPENSCAD / Windows nightly / PATH)")
    cases = case_matrix() + [dict(s) for s in SYNTHETIC]
    slugs = sorted(p.stem for p in (LIB / "devices").glob("*.scad"))
    res = osr.run_harness(harness_text(cases, slugs), exe=exe, timeout=900)
    if not res.ok:
        raise osr.OpenScadError("OpenSCAD failed: " + "; ".join(res.errors[:3]), res.errors)
    accessors = to_json(osr.decode(res.tagged("A")[0][0]))
    out_cases = []
    for i, rec in res.tagged("K"):
        case = dict(cases[int(i)])
        data = to_json(osr.decode(rec))
        case.update(data)
        case["end_zone"] = {"neg": data["end_zone"][0], "pos": data["end_zone"][1]}
        out_cases.append(case)
    if len(out_cases) != len(cases):
        raise RuntimeError(f"expected {len(cases)} cases, OpenSCAD echoed {len(out_cases)}")
    probes: dict[str, list] = {name: [None] * len(lists) for name, lists in PROBES.items()}
    for name, j, rec in res.tagged("P"):
        probes[name][int(j)] = {"args": PROBES[name][int(j)], "result": to_json(osr.decode(rec))}
    if any(r is None for rs in probes.values() for r in rs):
        raise RuntimeError("a probe did not echo")
    hashes = {f"lib/mcc/{n}.scad": hashlib.sha256((LIB / f"{n}.scad").read_bytes()).hexdigest() for n in ORACLE_FILES}
    return {"schema": 1, "generated_by": "python -m cad.tools.layout_oracle write", "openscad": osr.openscad_version(exe),
            "oracle_files": hashes, "accessors": accessors, "cases": out_cases, "probes": probes}


def grille_geometry(opening_d: float, exe: Path | None = None) -> dict:
    """The oracle's own 2-D fan grille (fan.scad `_mcc_fan_grille_2d`) exported as SVG: the distinct vertex radii
    (ring outer and inner circles appear among them) and the polar angles, in degrees, of the vertices at the
    spoke tips (radius sqrt(r_max^2 + (spoke_w / 2)^2)), which show the spoke angles."""
    import math

    text = (f"include <mcc/constants.scad>\nuse <mcc/fan.scad>\n_mcc_fan_grille_2d({float(opening_d)!r});\n")
    contours = osr.export_2d(text, exe=exe)
    pts = [pt for c in contours for pt in c]
    radii = sorted({round(math.hypot(x, y), 3) for x, y in pts})
    tip_r = math.hypot(opening_d / 2, params.constants()["MCC_FAN_GRILLE_SPOKE_W"] / 2)
    tips = sorted({round(math.degrees(math.atan2(y, x)) % 360, 1) for x, y in pts if abs(math.hypot(x, y) - tip_r) < 0.01})
    return {"radii": radii, "tip_angles": tips, "vertices": len(pts)}


def check(fixture_path: Path | None = None) -> list[str]:
    fresh = scrape()
    path = fixture_path or FIXTURE_PATH
    if not path.is_file():
        return [f"fixture {path} missing"]
    committed = json.loads(path.read_text(encoding="utf-8"))
    problems: list[str] = []
    for key in ("accessors", "cases", "probes"):
        deep_compare(committed[key], fresh[key], f"fixture.{key}", problems, rel=1e-15)
    return problems


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="cad.tools.layout_oracle")
    ap.add_argument("cmd", choices=["write", "check"])
    args = ap.parse_args(argv)
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    if args.cmd == "write":
        doc = scrape()
        FIXTURE_PATH.parent.mkdir(parents=True, exist_ok=True)
        FIXTURE_PATH.write_text(dumps(doc) + "\n", encoding="utf-8", newline="\n")
        print(f"wrote {FIXTURE_PATH} ({len(doc['cases'])} cases)")
        return 0
    problems = check()
    for p in problems:
        print("DRIFT:", p)
    print("fixture equals a fresh OpenSCAD run" if not problems else f"{len(problems)} problem(s)")
    return 1 if problems else 0


if __name__ == "__main__":
    raise SystemExit(main())
