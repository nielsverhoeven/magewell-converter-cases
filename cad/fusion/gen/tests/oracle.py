"""The oracle harness of the modelling kit (issue #81, milestone K4a).

The oracle is the frozen OpenSCAD library (``lib/mcc``).  This module renders *stages* of a case part and the
*shared-builder test blocks* (S1) headlessly and records volume, area and bounding box as small text fixtures
(``fixtures/s2_stages.json`` and ``fixtures/s1_blocks.json``), so that the Fusion builders can later be compared
against them.  No ``.scad`` file is committed: the two harness texts below are written to a temporary directory at
run time by ``cad.tools.openscad_runner.run_export`` (the one OpenSCAD runner of #76; this file holds no search for
OpenSCAD and no command line).  The library itself is not touched.

S2, stages of a case part.  A stage is cumulative: stage k holds the additive features of stages 1..k and the cuts of
stages 1..k, in the oracle's own order "all unions, then all cuts" (``lib/mcc/shell.scad``)::

    B1   outer shell and cavity                 L1   lid slab
    B2   tongue                                 L2   groove
    B3   lid bosses with bores, gusset webs     L3   lid screw holes (90 degree countersink, #100)
    B4   cradle                                 L4   lid vents  (= part ``lid``)
    B5   rail: sill, backing, passage, groove with lock slot and lead-in
    B6   side-bolt boss, web and cut
    B7   patch wall: recess and connector cuts
    B8   wall vents on the far wall and the minus X wall  (= part ``base`` of a compact case)
    B10  fan aperture; on the Plus family also the switch pad and cutout  (= part ``base_fan`` of a compact case and
         part ``base`` of a Plus case)

There is no stage B9: it was the floor cuts (strap pockets and stacking recesses), which issue #87 removed from the
oracle.  The stage numbers B1..B8 and B10 and the ``--stage`` values are kept, so that every plan and every command
that names a stage stays valid.

S1, shared builders in test blocks: ``tongue``, ``groove``, ``heat_set_boss``, ``lid_screw_hole``, ``side_bolt``,
``d_wall_cut``, ``rail_male``, ``rail_female``.  Block sizes are local test numbers ``T_*``; the feature dimensions
come from ``constants.scad``.  (The block ``lid_screw_hole`` was ``thumbscrew_hole`` before issue #100.)

Commands, at the repository root::

    python -m cad.fusion.gen.tests.oracle s1 --all [--update-fixtures]
    python -m cad.fusion.gen.tests.oracle s1 tongue
    python -m cad.fusion.gen.tests.oracle s2 pro-convert-for-ndi-to-hdmi base 5
    python -m cad.fusion.gen.tests.oracle s2 pro-convert-hdmi-plus base 10 --fan --switch
    python -m cad.fusion.gen.tests.oracle s2 --all [--update-fixtures]
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import unittest
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from cad.tools import openscad_runner

FIXTURES_DIR = Path(__file__).resolve().parent / "fixtures"
S1_FIXTURE = FIXTURES_DIR / "s1_blocks.json"
S2_FIXTURE = FIXTURES_DIR / "s2_stages.json"
DEFAULT_OUT = Path("build") / "oracle"

# A committed fixture equals a fresh render to these tolerances (plan 7, K4a step 3).  The box corners come from the
# exported mesh, whose vertices are printed with about seven significant digits.
VOLUME_TOL = 0.001   # mm3
AREA_TOL = 0.001     # mm2
BBOX_TOL = 0.002     # mm

BASE_STAGES = (1, 2, 3, 4, 5, 6, 7, 8, 10)
LID_STAGES = (1, 2, 3, 4)
SLUGS = (
    "pro-convert-for-ndi-to-aio", "pro-convert-for-ndi-to-hdmi-4k", "pro-convert-for-ndi-to-hdmi",
    "pro-convert-for-ndi-to-sdi", "pro-convert-hdmi-plus", "pro-convert-hdmi-tx", "pro-convert-sdi-plus",
    "pro-convert-sdi-tx",
)

S1_BLOCKS = {
    "tongue": 1, "groove": 2, "heat_set_boss": 3, "lid_screw_hole": 4,
    "side_bolt": 5, "d_wall_cut": 6, "rail_male": 7, "rail_female": 8,
}

TEMPLATE = "pro-convert-for-ndi-to-hdmi"
PLUS = "pro-convert-hdmi-plus"


class OracleError(RuntimeError):
    """The oracle could not be rendered or measured."""


# ---------------------------------------------------------------------------------------------------------------
# The harness texts.  Written to a temporary directory by run_export; no .scad file is committed.
# ---------------------------------------------------------------------------------------------------------------

def _device_includes() -> str:
    return "".join(f"include <mcc/devices/{slug}.scad>\n" for slug in SLUGS)


def _device_list() -> str:
    names = ",\n    ".join("MCC_DEV_" + slug.upper().replace("-", "_") for slug in SLUGS)
    return f"DEVS = [\n    {names},\n];\n"


_S2_HEAD = """// Stage oracle of the modelling kit (K4a): the case base or lid of ONE device up to a given stage, composed from
// the frozen library's own modules (the private ones too).  Written to a temporary file; never committed.
include <mcc/mcc.scad>
use <mcc/switch.scad>
"""

_S2_BODY = """
$fa = 1; $fs = 0.4;

slug = "pro-convert-for-ndi-to-hdmi";
part = "base";
stage = 1;
fan = false;
fan_switch = false;
rail = true;
lid_vents = true;

_hits = [for (d = DEVS) if (mcc_dev_slug(d) == slug) d];
assert(len(_hits) == 1, str("stage oracle: unknown slug ", slug));
dev = _hits[0];

cfg = [["fan", fan], ["splitter", false], ["fan_switch", fan_switch],
       ["tripod_insert", false], ["lid_vents", lid_vents], ["rail", rail]];

module stage_base(dev, cfg, stage) {
    l = mcc_case_layout(dev, cfg);
    L = struct_val(l, "L"); W = struct_val(l, "W");
    z_top = MCC_FLOOR_T + MCC_PANEL_BAND + MCC_PLATE_H + MCC_PANEL_BAND;
    x_bolt = struct_val(l, "side_bolt_x"); z_bolt = struct_val(l, "side_bolt_z");
    lid_pos = struct_val(l, "lid_fastener_pos");
    boss_r_lid = MCC_BOSS_MIN_RATIO * struct_val(MCC_INSERT_M3, "od") / 2;
    sw_on = mcc_fan_switch_enabled(cfg);
    sw_pos = struct_val(l, "switch_pos");

    difference() {
        union() {
            _mcc_outer_shell_solid(L, W, 0, z_top, MCC_FLOOR_T, z_top + MCC_EPS);
            if (stage >= 2)
                _mcc_tg_frame(rect = _mcc_tg_rect(L, W), r_lo = 0, r_hi = MCC_TG_W,
                              z0 = z_top - MCC_EPS, height = MCC_TG_H + MCC_EPS);
            if (stage >= 3)
                for (p = lid_pos) {
                    translate([p[0], p[1], MCC_FLOOR_T]) mcc_heat_set_boss(h = z_top - MCC_FLOOR_T);
                    _mcc_gusset_web(p[0], p[1], L, W, MCC_FLOOR_T, z_top, boss_r_lid);
                }
            if (stage >= 4) mcc_cradle(dev, cfg);
            if (stage >= 5) mcc_floor_features_add(dev, cfg);
            if (stage >= 6)
                translate([x_bolt, -W / 2 - MCC_SIDE_BOLT_PROUD, z_bolt]) rotate([-90, 0, 0])
                    mcc_captive_side_bolt_boss(web_to_floor_h = z_bolt - MCC_FLOOR_T);
            if (stage >= 10 && sw_on)
                translate([L / 2 - MCC_WALL, sw_pos[1], sw_pos[2]]) rotate([0, 90, 0])
                    mcc_switch_pad(mcc_switch_spec(MCC_SWITCH_DEFAULT), wall_t = MCC_WALL);
        }
        if (stage >= 5) mcc_rail_features_cut(dev, cfg);
        if (stage >= 6)
            translate([x_bolt, -W / 2 - MCC_SIDE_BOLT_PROUD, z_bolt]) rotate([-90, 0, 0])
                mcc_captive_side_bolt_cut();
        if (stage >= 7) _mcc_patch_wall_aperture(l, dev);
        if (stage >= 8) { mcc_vents(dev, cfg, [0, -1, 0]); mcc_vents(dev, cfg, [-1, 0, 0]); }
        if (stage >= 10) {
            if (struct_val(cfg, "fan") == true) mcc_vents(dev, cfg, [1, 0, 0]);
            if (sw_on)
                translate([L / 2 - MCC_WALL, sw_pos[1], sw_pos[2]]) rotate([0, 90, 0])
                    mcc_switch_cutout(mcc_switch_spec(MCC_SWITCH_DEFAULT), wall_t = MCC_WALL);
        }
    }
}

module stage_lid(dev, cfg, stage) {
    l = mcc_case_layout(dev, cfg);
    L = struct_val(l, "L"); W = struct_val(l, "W");
    z_top = MCC_FLOOR_T + MCC_PANEL_BAND + MCC_PLATE_H + MCC_PANEL_BAND;
    lid_pos = struct_val(l, "lid_fastener_pos");
    difference() {
        translate([-L / 2, -W / 2, z_top]) cube([L, W, MCC_LID_T]);
        if (stage >= 2)
            _mcc_tg_frame(rect = _mcc_tg_rect(L, W), r_lo = -MCC_CLR_TG, r_hi = MCC_TG_W + MCC_CLR_TG,
                          z0 = z_top - MCC_EPS, height = MCC_TG_H + MCC_EPS);
        if (stage >= 3)
            for (p = lid_pos)
                translate([p[0], p[1], z_top]) mcc_lid_screw_hole(lid_t = MCC_LID_T);
        if (stage >= 4 && lid_vents) mcc_lid_vents_cut(dev, cfg);
    }
}

if (part == "base") stage_base(dev, cfg, stage);
else if (part == "lid") stage_lid(dev, cfg, stage);
else assert(false, "stage oracle: part must be base or lid");
"""

HARNESS_S2 = _S2_HEAD + _device_includes() + "\n" + _device_list() + _S2_BODY

HARNESS_S1 = """// S1 oracle of the modelling kit (K4a): one shared feature in a plain test block, from the frozen library's modules.
//   -D block=1..8
// Block sizes are local test numbers (T_*); the feature dimensions come from constants.scad.  Written to a temporary
// file; never committed.
include <mcc/mcc.scad>
$fa = 1; $fs = 0.4;
block = 1;

T_TG_L = 60; T_TG_W = 40; T_TG_PLATE = 3;            // tongue / groove ring over a 60 x 40 plate
T_BOSS_PLATE = 20; T_BOSS_H = 10;                    // heat-set boss on a 20 x 20 x 3 plate
T_LID = 20;                                          // lid screw hole in a 20 x 20 lid tile
T_SB_W = 40; T_SB_H = 45;                            // side-bolt wall tile
T_D_W = 40; T_D_H = 45;                              // D cut in a 40 x 45 wall tile
T_RAIL_LEN = 60; T_RAIL_PLATE_W = 80; T_RAIL_PLATE_T = 3;

tg = [-T_TG_L / 2 + MCC_WALL, -T_TG_W / 2 + MCC_WALL, T_TG_L - 2 * MCC_WALL, T_TG_W - 2 * MCC_WALL];

if (block == 1) {            // tongue: ring on top of a wall ring
    union() {
        difference() {
            translate([-T_TG_L / 2, -T_TG_W / 2, 0]) cube([T_TG_L, T_TG_W, T_TG_PLATE]);
            translate([tg[0], tg[1], -1]) cube([tg[2], tg[3], T_TG_PLATE + 2]);
        }
        _mcc_tg_frame(rect = tg, r_lo = 0, r_hi = MCC_TG_W, z0 = T_TG_PLATE - MCC_EPS, height = MCC_TG_H + MCC_EPS);
    }
} else if (block == 2) {     // groove: ring cut into the underside of a lid slab
    difference() {
        translate([-T_TG_L / 2, -T_TG_W / 2, 0]) cube([T_TG_L, T_TG_W, MCC_LID_T]);
        _mcc_tg_frame(rect = tg, r_lo = -MCC_CLR_TG, r_hi = MCC_TG_W + MCC_CLR_TG, z0 = -MCC_EPS, height = MCC_TG_H + MCC_EPS);
    }
} else if (block == 3) {     // heat-set boss with its bore on a plate
    union() {
        translate([-T_BOSS_PLATE / 2, -T_BOSS_PLATE / 2, 0]) cube([T_BOSS_PLATE, T_BOSS_PLATE, MCC_FLOOR_T]);
        translate([0, 0, MCC_FLOOR_T]) mcc_heat_set_boss(h = T_BOSS_H);
    }
} else if (block == 4) {     // countersunk lid screw hole (#100) in a lid tile; inner face z = 0, outward face z = MCC_LID_T
    difference() {
        translate([-T_LID / 2, -T_LID / 2, 0]) cube([T_LID, T_LID, MCC_LID_T]);
        mcc_lid_screw_hole(lid_t = MCC_LID_T);
    }
} else if (block == 5) {     // side-bolt boss, web and cut in a far-wall tile standing on a floor strip
    difference() {
        union() {
            translate([-T_SB_W / 2, 0, 0]) cube([T_SB_W, MCC_WALL, T_SB_H]);
            translate([-T_SB_W / 2, 0, 0]) cube([T_SB_W, MCC_WALL + MCC_GAP_FAR, MCC_FLOOR_T]);
            translate([0, 0, MCC_SIDE_BOLT_AXIS_Z]) rotate([-90, 0, 0])
                mcc_captive_side_bolt_boss(web_to_floor_h = MCC_SIDE_BOLT_AXIS_Z - MCC_FLOOR_T);
        }
        translate([0, 0, MCC_SIDE_BOLT_AXIS_Z]) rotate([-90, 0, 0]) mcc_captive_side_bolt_cut();
    }
} else if (block == 6) {     // D connector cut (etherCON class) straight in a wall tile, seat face at y = 0
    difference() {
        translate([-T_D_W / 2, -(MCC_PANEL_SEAT_T + MCC_WALL), 0]) cube([T_D_W, MCC_PANEL_SEAT_T + MCC_WALL, T_D_H]);
        translate([0, 0, T_D_H / 2]) rotate([90, 0, 180]) mcc_panel_wall_cut("NE8FDP-B", wall_t = MCC_PANEL_SEAT_T + MCC_WALL);
    }
} else if (block == 7) {     // rail male on a plate
    union() {
        translate([-T_RAIL_LEN / 2, -T_RAIL_PLATE_W / 2, -T_RAIL_PLATE_T]) cube([T_RAIL_LEN, T_RAIL_PLATE_W, T_RAIL_PLATE_T]);
        mcc_rail_male(len = T_RAIL_LEN);
    }
} else if (block == 8) {     // rail female: sill block plus backing, groove open at +X through the block end
    sw = MCC_RAIL_ROOT_W / 2 + MCC_RAIL_SILL_SIDE_W;
    x1 = T_RAIL_LEN / 2 + MCC_WALL;
    difference() {
        union() {
            translate([-T_RAIL_LEN / 2 - MCC_RAIL_END_WALL, -sw, 0]) cube([T_RAIL_LEN + MCC_RAIL_END_WALL + MCC_WALL, 2 * sw, MCC_RAIL_SILL_H]);
            mcc_rail_female_backing(len = T_RAIL_LEN);
        }
        mcc_rail_female_cut(len = T_RAIL_LEN, open_ext = MCC_WALL + 1, entry_x = x1);
    }
}
"""


# ---------------------------------------------------------------------------------------------------------------
# What is rendered and recorded
# ---------------------------------------------------------------------------------------------------------------

def stage_name(part: str, stage: int) -> str:
    """``B5`` for base stage 5, ``L3`` for lid stage 3."""
    return ("B" if part == "base" else "L") + str(stage)


def s2_options(fan: bool = False, fan_switch: bool = False, rail: bool = True, lid_vents: bool = True) -> dict:
    return {"fan": bool(fan), "fan_switch": bool(fan_switch), "rail": bool(rail), "lid_vents": bool(lid_vents)}


def _s2_key(slug: str, part: str, stage: int, tag: str = "") -> str:
    return f"{slug}.{part}.{stage_name(part, stage)}" + (f".{tag}" if tag else "")


def s2_cases() -> dict:
    """The committed S2 fixture set: key -> {slug, part, stage, options}.

    Fourteen stages of the template (``pro-convert-for-ndi-to-hdmi``: base B1..B8 and B10, lid L1..L4; stages
    B1..B8 and the lid with the fan off, B10 with the fan on), stage B10 of ``pro-convert-hdmi-plus`` with fan and
    switch (equals that case's golden ``base``), and the two parts of the non-exported configuration ``bare`` of the
    template (``rail`` off, ``lid_vents`` off): base B8 and lid L4 (verdict B6)."""
    out: dict = {}
    for stage in BASE_STAGES:
        opt = s2_options(fan=(stage == 10))
        out[_s2_key(TEMPLATE, "base", stage)] = {"slug": TEMPLATE, "part": "base", "stage": stage, "options": opt}
    for stage in LID_STAGES:
        out[_s2_key(TEMPLATE, "lid", stage)] = {"slug": TEMPLATE, "part": "lid", "stage": stage, "options": s2_options()}
    out[_s2_key(PLUS, "base", 10, "fan_switch")] = {
        "slug": PLUS, "part": "base", "stage": 10, "options": s2_options(fan=True, fan_switch=True)}
    bare = s2_options(rail=False, lid_vents=False)
    out[_s2_key(TEMPLATE, "base", 8, "bare")] = {"slug": TEMPLATE, "part": "base", "stage": 8, "options": bare}
    out[_s2_key(TEMPLATE, "lid", 4, "bare")] = {"slug": TEMPLATE, "part": "lid", "stage": 4, "options": bare}
    return out


# Where the last stage of a part equals a committed golden of the library (tests/golden/<name>.json).
S2_GOLDENS = {
    _s2_key(TEMPLATE, "base", 8): "pro-convert-for-ndi-to-hdmi.base",
    _s2_key(TEMPLATE, "base", 10): "pro-convert-for-ndi-to-hdmi.base_fan",
    _s2_key(TEMPLATE, "lid", 4): "pro-convert-for-ndi-to-hdmi.lid",
    _s2_key(PLUS, "base", 10, "fan_switch"): "pro-convert-hdmi-plus.base",
}


def _bool(value: bool) -> str:
    return "true" if value else "false"


# ---------------------------------------------------------------------------------------------------------------
# Rendering and measuring
# ---------------------------------------------------------------------------------------------------------------

def require_openscad() -> Path:
    """The OpenSCAD executable.  Missing: with ``MCC_REQUIRE_OPENSCAD=1`` (CI, the job that has OpenSCAD) an
    ``OracleError``, so that a test that needs the oracle fails and never skips; otherwise ``unittest.SkipTest``."""
    exe = openscad_runner.find_openscad()
    if exe is not None:
        return exe
    message = "OpenSCAD not found (set MCC_OPENSCAD, install the nightly or put openscad on PATH)"
    if os.environ.get("MCC_REQUIRE_OPENSCAD") == "1":
        raise OracleError(message + " but MCC_REQUIRE_OPENSCAD=1 requires it")
    raise unittest.SkipTest(message)


def measure(stl_path: str | Path) -> dict:
    """Volume (mm3), area (mm2) and the two box corners of an exported mesh, with ``trimesh`` as the goldens are."""
    import trimesh

    mesh = trimesh.load(str(stl_path), force="mesh")
    if len(mesh.faces) == 0:
        raise OracleError(f"{stl_path}: the mesh is empty")
    low, high = mesh.bounds
    return {
        "volume_mm3": float(mesh.volume),
        "area_mm2": float(mesh.area),
        "bbox_min": [float(v) for v in low],
        "bbox_max": [float(v) for v in high],
    }


def _export(harness: str, defines: dict, stl: Path, label: str) -> Path:
    exe = require_openscad()
    stl = Path(stl).resolve()   # run_export runs OpenSCAD in a temporary directory: the path must be absolute
    result = openscad_runner.run_export(harness, stl, defines, exe=exe)
    if not result.ok or not stl.is_file():
        tail = "\n".join(result.errors) or result.stderr[-600:]
        raise OracleError(f"{label}: OpenSCAD failed (exit {result.returncode})\n{tail}")
    return stl


def render_s1(block: str, out_dir: str | Path = DEFAULT_OUT) -> Path:
    """Render one S1 test block to ``<out_dir>/s1_<block>.stl`` and return that path."""
    if block not in S1_BLOCKS:
        raise OracleError(f"unknown S1 block {block!r}; known: {', '.join(S1_BLOCKS)}")
    stl = Path(out_dir) / f"s1_{block}.stl"
    return _export(HARNESS_S1, {"block": str(S1_BLOCKS[block])}, stl, f"S1 block {block}")


def render_s2(slug: str, part: str, stage: int, out_dir: str | Path = DEFAULT_OUT, fan: bool = False,
              fan_switch: bool = False, rail: bool = True, lid_vents: bool = True, tag: str = "") -> Path:
    """Render stage ``stage`` of ``part`` (``base`` or ``lid``) of the case ``slug`` to
    ``<out_dir>/s2_<slug>.<part>.<stage name>[.<tag>].stl`` and return that path."""
    if slug not in SLUGS:
        raise OracleError(f"unknown slug {slug!r}")
    if part not in ("base", "lid"):
        raise OracleError(f"part must be base or lid, not {part!r}")
    stages = BASE_STAGES if part == "base" else LID_STAGES
    if stage not in stages:
        raise OracleError(f"stage {stage} does not exist for {part}; known: {', '.join(map(str, stages))}"
                          + (" (there is no B9: the floor cuts were removed by #87)" if part == "base" else ""))
    stl = Path(out_dir) / f"s2_{_s2_key(slug, part, stage, tag)}.stl"
    defines = {
        "slug": f'"{slug}"', "part": f'"{part}"', "stage": str(stage), "fan": _bool(fan),
        "fan_switch": _bool(fan_switch), "rail": _bool(rail), "lid_vents": _bool(lid_vents),
    }
    return _export(HARNESS_S2, defines, stl, _s2_key(slug, part, stage, tag))


def render_s2_case(key: str, case: dict, out_dir: str | Path = DEFAULT_OUT) -> Path:
    tag = key.split(".", 3)[3] if key.count(".") >= 3 else ""
    return render_s2(case["slug"], case["part"], case["stage"], out_dir, tag=tag, **case["options"])


def _pool(jobs: dict, workers: int | None):
    """Run ``{key: callable}`` on a thread pool (every job is one OpenSCAD process); return ``{key: result}``."""
    workers = workers or min(len(jobs) or 1, max(1, (os.cpu_count() or 2) - 1), 12)
    with ThreadPoolExecutor(max_workers=workers) as pool:
        futures = {key: pool.submit(fn) for key, fn in jobs.items()}
        return {key: future.result() for key, future in futures.items()}


def derive_s1(out_dir: str | Path = DEFAULT_OUT, workers: int | None = None) -> dict:
    """Render and measure every S1 block: ``{block: measurement}`` in block order."""
    require_openscad()
    jobs = {b: (lambda b=b: measure(render_s1(b, out_dir))) for b in S1_BLOCKS}
    return _pool(jobs, workers)


def derive_s2(out_dir: str | Path = DEFAULT_OUT, workers: int | None = None) -> dict:
    """Render and measure every case of ``s2_cases()``: ``{key: measurement}`` in case order."""
    require_openscad()
    cases = s2_cases()
    jobs = {k: (lambda k=k, c=c: measure(render_s2_case(k, c, out_dir))) for k, c in cases.items()}
    return _pool(jobs, workers)


def derive_all(out_dir: str | Path = DEFAULT_OUT, workers: int | None = None) -> tuple[dict, dict]:
    """Every S1 block and every S2 case in one pool (the wall time of the oracle tests): ``(s1, s2)``."""
    require_openscad()
    jobs = {("s1", b): (lambda b=b: measure(render_s1(b, out_dir))) for b in S1_BLOCKS}
    jobs.update({("s2", k): (lambda k=k, c=c: measure(render_s2_case(k, c, out_dir))) for k, c in s2_cases().items()})
    done = _pool(jobs, workers)
    return ({b: done[("s1", b)] for b in S1_BLOCKS}, {k: done[("s2", k)] for k in s2_cases()})


# ---------------------------------------------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------------------------------------------

def _rounded(m: dict) -> dict:
    return {
        "volume_mm3": round(m["volume_mm3"], 3),
        "area_mm2": round(m["area_mm2"], 3),
        "bbox_min": [round(v, 3) for v in m["bbox_min"]],
        "bbox_max": [round(v, 3) for v in m["bbox_max"]],
    }


def s1_fixture(measurements: dict) -> dict:
    return {"schema": 1, "blocks": {b: _rounded(measurements[b]) for b in S1_BLOCKS}}


def s2_fixture(measurements: dict) -> dict:
    cases = s2_cases()
    return {"schema": 1, "stages": {
        k: {"slug": c["slug"], "part": c["part"], "stage": stage_name(c["part"], c["stage"]), "options": c["options"],
            **_rounded(measurements[k])}
        for k, c in cases.items()}}


def dump_fixture(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=1, ensure_ascii=False) + "\n", encoding="utf-8", newline="\n")


def load_fixture(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def differences(fresh: dict, committed: dict, label: str) -> list[str]:
    """Where a fresh measurement differs from a committed fixture entry by more than the tolerances."""
    out = []
    if abs(fresh["volume_mm3"] - committed["volume_mm3"]) > VOLUME_TOL:
        out.append(f"{label}: volume {fresh['volume_mm3']:.3f} vs fixture {committed['volume_mm3']:.3f} mm3")
    if abs(fresh["area_mm2"] - committed["area_mm2"]) > AREA_TOL:
        out.append(f"{label}: area {fresh['area_mm2']:.3f} vs fixture {committed['area_mm2']:.3f} mm2")
    for corner in ("bbox_min", "bbox_max"):
        for axis, (a, b) in enumerate(zip(fresh[corner], committed[corner])):
            if abs(a - b) > BBOX_TOL:
                out.append(f"{label}: {corner}[{axis}] {a:.4f} vs fixture {b:.4f} mm")
    return out


# ---------------------------------------------------------------------------------------------------------------
# Command line
# ---------------------------------------------------------------------------------------------------------------

def _print(label: str, m: dict) -> None:
    print(f"{label}: volume {m['volume_mm3']:.3f} mm3, area {m['area_mm2']:.3f} mm2, "
          f"box {[round(v, 3) for v in m['bbox_min']]} to {[round(v, 3) for v in m['bbox_max']]}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="python -m cad.fusion.gen.tests.oracle", description=__doc__.split("\n")[0])
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--out", default=str(DEFAULT_OUT), help="output directory for the STL files (default build/oracle)")
    common.add_argument("--update-fixtures", action="store_true", help="rewrite the committed fixture (with --all)")
    sub = parser.add_subparsers(dest="command", required=True)
    p1 = sub.add_parser("s1", parents=[common], help="render an S1 test block")
    p1.add_argument("block", nargs="?", choices=list(S1_BLOCKS))
    p1.add_argument("--all", action="store_true")
    p2 = sub.add_parser("s2", parents=[common], help="render a stage of a case part")
    p2.add_argument("slug", nargs="?")
    p2.add_argument("part", nargs="?", choices=["base", "lid"])
    p2.add_argument("stage", nargs="?", type=int)
    p2.add_argument("--all", action="store_true", help="the committed S2 set of s2_cases()")
    p2.add_argument("--fan", action="store_true")
    p2.add_argument("--switch", action="store_true", help="fan_switch on (Plus family)")
    p2.add_argument("--no-rail", action="store_true")
    p2.add_argument("--no-lid-vents", action="store_true")
    args = parser.parse_args(argv)
    try:
        if args.command == "s1":
            if args.all:
                found = derive_s1(args.out)
                for b, m in found.items():
                    _print(b, m)
                if args.update_fixtures:
                    dump_fixture(S1_FIXTURE, s1_fixture(found))
                    print(f"wrote {S1_FIXTURE}")
            elif args.block:
                stl = render_s1(args.block, args.out)
                _print(args.block, measure(stl))
                print(stl)
            else:
                parser.error("s1 needs a block name or --all")
        else:
            if args.all:
                found = derive_s2(args.out)
                for k, m in found.items():
                    _print(k, m)
                if args.update_fixtures:
                    dump_fixture(S2_FIXTURE, s2_fixture(found))
                    print(f"wrote {S2_FIXTURE}")
            elif args.slug and args.part and args.stage is not None:
                stl = render_s2(args.slug, args.part, args.stage, args.out, fan=args.fan, fan_switch=args.switch,
                                rail=not args.no_rail, lid_vents=not args.no_lid_vents)
                _print(stage_name(args.part, args.stage), measure(stl))
                print(stl)
            else:
                parser.error("s2 needs SLUG PART STAGE or --all")
    except OracleError as exc:
        print(f"oracle: {exc}", file=sys.stderr)
        return 1
    except unittest.SkipTest as exc:
        print(f"oracle: {exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
