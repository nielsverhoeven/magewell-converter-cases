#!/usr/bin/env python3
"""scad_export: derive cad/parameters/constants.csv, cad/data/*.json, cad/devices/*.json,
cad/cases/*.json and the S0 fixture cad/fixtures/scad_values.json from the frozen OpenSCAD
sources (issue #76).  Transition tool: deleted together with lib/mcc at the cutover (#86).

    python -m cad.tools.scad_export write [--out DIR]    derive and write everything (default: repo cad/)
    python -m cad.tools.scad_export check                re-derive from OpenSCAD; fail on any drift

VALUES come from OpenSCAD itself: a temporary harness (written at run time, never committed) includes
constants.scad and the device files and echoes every constant and device record losslessly; a second
one evaluates the `variant` list of every models/<slug>/case.scad.  TEXT parsing (scad_source.py) is
used only for what OpenSCAD cannot say: the names and order of the statements, the source text of the
derived expressions, the comments that document each statement, the `extra_parts` marker.

The committed fixture holds the numbers OpenSCAD produced (S0).  `check` compares three things:
    fixture  == a fresh OpenSCAD run                (the fixture is faithful)
    cad/**   == the fixture, semantically           (the files are a verified mirror)
Comments, sources and provenance text are NOT compared (they are curated by hand after the export).
"""
from __future__ import annotations

import argparse
import copy
import dataclasses
import hashlib
import json
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from cad import params
from cad.numeric import close
from cad.params import Row
from cad.tools import openscad_runner as osr
from cad.tools.scad_expr import ScadExprError, translate
from cad.tools.scad_meta import FLAT_ROW_META, meta_for
from cad.tools.scad_source import Statement, comment_text, read_device_source, read_variables

REPO = osr.REPO_ROOT
CONSTANTS_SCAD = REPO / "lib" / "mcc" / "constants.scad"
DEVICES_SCAD_DIR = REPO / "lib" / "mcc" / "devices"
MODELS_DIR = REPO / "models"
FIXTURE_PATH = Path(__file__).resolve().parents[1] / "fixtures" / "scad_values.json"

# ---- explicit policy (every entry is a decision record D76.x of the plan) -----------------------------------
VECTOR_PARTS: dict[str, tuple[str, ...]] = {      # numeric vectors -> one row per part (_X/_Y/_Z, ranges _LO/_HI)
    "MCC_D_FLANGE": ("X", "Y"),
    "MCC_D_SCREW_PITCH": ("X", "Y"),
    "MCC_STRAP_SLOT": ("X", "Y"),
    "MCC_VENT_EXHAUST_Z": ("LO", "HI"),
}
FLATTEN_TABLES: dict[str, dict[str, str]] = {     # one-record tables -> flat rows NAME_<suffix>
    "MCC_INSERT_M3": {"hole_d": "HOLE_D", "od": "OD", "len": "LEN"},
    "MCC_INSERT_1_4_20": {"hole_d": "HOLE_D", "od": "OD", "len": "LEN"},
    "MCC_INSERT_M4": {"hole_d": "HOLE_D", "od": "OD", "len": "LEN"},
    "MCC_SIDE_BOLT_CLIP": {"groove_d": "GROOVE_D", "groove_w": "GROOVE_W", "od": "OD", "t": "T"},
}
JSON_TABLES: dict[str, str] = {                   # statement -> cad/data/<file>.json
    "MCC_PANEL_PARTS": "panel_parts", "MCC_FANS": "fans", "MCC_SWITCHES": "switches",
    "MCC_SPLITTERS": "splitters", "MCC_DEV_SIDE_ALLOW": "dev_side_allow", "MCC_PLUG_AXIAL": "plug_axial",
    "MCC_CONFIDENCE_ORDER": "confidence_order",
}
OPTIONS: dict[str, str] = {                       # selector strings -> cad/data/options.json rows
    "MCC_FAN_DEFAULT": "fan_default", "MCC_SWITCH_DEFAULT": "switch_default",
    "MCC_SPLITTER_DEFAULT": "splitter_default",
}
OPENSCAD_ONLY: dict[str, str] = {"MCC_SHOW_GHOST": "render-visibility flag, consumed by no Python module"}
UNITLESS = {"MCC_BOSS_MIN_RATIO", "MCC_SLOTS_MAX", "MCC_VENT_AREA_RATIO", "MCC_LID_VENT_ROWS",
            "MCC_LID_VENT_AREA_RATIO", "MCC_RIB_HEIGHT_RATIO_MAX"}
ANGLES = {"MCC_RAIL_FLANK_ANGLE", "MCC_RAIL_LOCK_RAMP_IN"}
TABLE_EXPR: dict[tuple[str, str, str], str] = {   # derived entries inside a table (file, row, field)
    ("switches", "MTS-101", "nut_d"): "8.0 mm / cos(30 deg)",
    ("switches", "MTS-101", "keepout_d"): "8.0 mm / cos(30 deg) + 2 * MCC_CLR_SLIDE",
}
# Derived from a table row through search(): kept as a literal row (value taken from OpenSCAD) and
# guarded by a permanent test that it equals the default splitter's size[2] (D76.x).
LOOKUP_LITERALS = {"MCC_END_ZONE_NEG_EXTRA_SPLITTER"}
DEVICE_FIELDS = ("id", "face", "pos", "kind", "dir", "panel", "confidence")
_LITERAL = re.compile(r"^-?(?:\d+\.?\d*|\.\d+)(?:[eE][-+]?\d+)?$")
_MODEL_CITE = re.compile(r"knowledge/magewell/models/[\w.-]+\.md:\d+(?:-\d+)?")


@dataclass(frozen=True)
class Harvest:
    """A literal that sits outside constants.scad (01-ARCH-BRIEF section B) made a named row."""
    name: str
    unit: str
    text: str            # the literal as written
    file: str            # repo-relative .scad file
    line: int
    pattern: str         # must match that source line (guards the pin)
    description: str


HARVEST: list[Harvest] = [
    Harvest("MCC_PATCH_RECESS_ROOF_K", "none", "1.2", "lib/mcc/shell.scad", 164, r"\bk\s*=\s*1\.2\b",
            "patch-wall recess roof: rise per mm of depth (slightly steeper than 45 deg)"),
    Harvest("MCC_STRAP_X_INSET", "mm", "25", "lib/mcc/layout.scad", 211, r"L\s*/\s*2\s*-\s*25\b",
            "strap-slot X inset from the case end"),
    Harvest("MCC_STRAP_BAY_CLR", "mm", "2", "lib/mcc/layout.scad", 217, r"/\s*2\s*\+\s*2\b",
            "clearance added when the -X strap-slot pair slides off the reserved splitter bay"),
    Harvest("MCC_STRAP_Y_INSET", "mm", "12", "lib/mcc/layout.scad", 219, r"W\s*/\s*2\s*-\s*12\b",
            "strap-slot Y inset from the side walls"),
    Harvest("MCC_LID_N_FAST_LARGE", "none", "6", "lib/mcc/layout.scad", 351, r"\?\s*6\s*:\s*4\b",
            "lid thumbscrew count above MCC_LID_SPAN_MAX"),
    Harvest("MCC_LID_N_FAST_SMALL", "none", "4", "lib/mcc/layout.scad", 351, r"\?\s*6\s*:\s*4\b",
            "lid thumbscrew count up to MCC_LID_SPAN_MAX"),
    Harvest("MCC_VENT_INTAKE_Z0", "mm", "5", "lib/mcc/layout.scad", 404, r"\[\s*5\s*,\s*5\s*\+",
            "bottom of the intake vent band above the case floor plane"),
    Harvest("MCC_VENT_MID_EXCL_MARGIN", "mm", "2.0", "lib/mcc/vents.scad", 103, r"2\s*\*\s*2\.0",
            "margin on each side of the far-wall mid lid boss that vent slots must clear"),
    Harvest("MCC_CRADLE_FLANK_RIB_CLR", "mm", "2.0", "lib/mcc/cradle.scad", 133, r"\+\s*2\.0",
            "clearance between a far-flank rib and the side-bolt keep-out"),
    Harvest("MCC_CRADLE_FLANK_RIB_END_MARGIN", "mm", "8", "lib/mcc/cradle.scad", 134, r"x_dev_lo\s*\+\s*8.*x_dev_hi\s*-\s*8",
            "far-flank ribs stay this far inside each end of the device"),
    Harvest("MCC_CRADLE_FLANK_RIB_MID_SPAN", "mm", "40", "lib/mcc/cradle.scad", 143, r">\s*40\b",
            "a far-flank rib segment longer than this also gets a midpoint rib"),
    Harvest("MCC_CRADLE_PATCH_RIB_EDGE", "mm", "3", "lib/mcc/cradle.scad", 247, r"plate_l\s*/\s*2\s*-\s*3\b",
            "patch-flank ribs exist only where |x| exceeds half the plate length minus this"),
    Harvest("MCC_WEB_FACE_MARGIN", "mm", "0.5", "lib/mcc/shell.scad", 84, r"reach\s*=\s*dmin\s*-\s*0\.5\b",
            "gusset web stops this far short of its wall's outer face"),
    Harvest("MCC_WEB_HULL_INSET", "mm", "0.2", "lib/mcc/shell.scad", 94, r"boss_r\s*-\s*0\.2\b",
            "gusset web hull circle: the boss radius less this inset"),
    Harvest("MCC_INSERT_BORE_OVERDEPTH", "mm", "1", "lib/mcc/fasteners.scad", 33, r"depth\s*=\s*insert_len\s*\+\s*1\b",
            "heat-set insert bore depth beyond the insert length"),
    Harvest("MCC_CRADLE_RIB_LEG", "mm", "3.0", "lib/mcc/cradle.scad", 268, r"min\(\s*3\.0\s*,",
            "far-flank rib leg length along the floor (limited to half the far-wall gap)"),
    Harvest("MCC_STACK_RECESS_MARGIN", "mm", "1.5", "lib/mcc/mounts.scad", 210, r"/\s*2\s*\+\s*1\.5\b",
            "stacking recess radius beyond the lid boss radius"),
    Harvest("MCC_STACK_RECESS_DEPTH", "mm", "1.0", "lib/mcc/mounts.scad", 214, r"h\s*=\s*1\.0\s*\+\s*MCC_EPS",
            "stacking recess depth in the floor underside"),
    Harvest("MCC_FAN_GRILLE_RING_W", "mm", "1.8", "lib/mcc/fan.scad", 66, r"ring_w\s*=\s*1\.8\b",
            "fan finger-guard ring width"),
    Harvest("MCC_FAN_GRILLE_GAP_W", "mm", "3.0", "lib/mcc/fan.scad", 67, r"gap_w\s*=\s*3\.0\b",
            "fan finger-guard minimum clear gap between rings"),
    Harvest("MCC_FAN_GRILLE_SPOKE_W", "mm", "2.0", "lib/mcc/fan.scad", 72, r"spoke_w\s*=\s*2\.0\b",
            "fan finger-guard spoke width"),
    Harvest("MCC_FAN_GRILLE_SPOKE_PITCH", "deg", "60", "lib/mcc/fan.scad", 73, r"n_spokes\s*=\s*6\b",
            "angle between neighbouring grille spokes: 360 deg over the spoke count 6"),
    Harvest("MCC_FAN_OPENING_MARGIN", "mm", "2", "lib/mcc/fan.scad", 151, r"frame\[0\]\s*-\s*2\b",
            "round fan opening: the frame size less this margin"),
    Harvest("MCC_D_SEAT_POCKET_CLR", "mm", "1", "lib/mcc/neutrik.scad", 90, r"MCC_D_FLANGE\[0\]\s*\+\s*1\b",
            "D-series seat pocket: clearance added to the flange outline"),
    # an expression in the source, so an expression row: no conf, its inputs carry theirs
    Harvest("MCC_SIDE_BOLT_HEAD_CUT_D", "mm", "MCC_SIDE_BOLT_HEAD_D + 2 * MCC_CLR_SLIDE", "lib/mcc/fasteners.scad", 267,
            r"head_rec_d\s*=\s*head_d\s*\+\s*2\s*\*\s*MCC_CLR_SLIDE",
            "side-bolt head recess diameter the cut really makes: head diameter plus a sliding clearance per side"),
]


# ---- scraping -------------------------------------------------------------------------------------------


@dataclass
class Scraped:
    statements: list[Statement]
    values: dict[str, Any]              # constant name -> decoded OpenSCAD value
    devices: dict[str, Any]             # slug -> decoded device record ([[key, value], ...])
    device_sources: dict[str, Any]      # slug -> DeviceSource (comments)
    cases: dict[str, dict]              # slug -> {"variant": [[k, v]...], "extra": {part: [[k, v]...]}}
    openscad_version: str = ""
    scad_hashes: dict[str, str] = field(default_factory=dict)


def device_var(slug: str) -> str:
    return "MCC_DEV_" + slug.upper().replace("-", "_")


def values_harness(names: list[str], slugs: list[str]) -> str:
    lines = ["include <mcc/constants.scad>"]
    lines += [f"include <mcc/devices/{s}.scad>" for s in slugs]
    lines.append(osr.ENCODER_SCAD)
    lines += [f'echo("C", "{n}", oracle_enc({n}));' for n in names]
    lines += [f'echo("D", "{s}", oracle_enc({device_var(s)}));' for s in slugs]
    return "\n".join(lines) + "\n"


_EXTRA_PARTS = re.compile(r"^//\s*build\.py:\s*extra_parts\s*=\s*(.+?)\s*$", re.M)
_CASE_VARS = ("fan", "splitter", "lid_vents", "fan_effective", "variant")


def cases_harness(slugs: list[str]) -> tuple[str, dict[str, list[str]]]:
    """One function per case that evaluates the `variant` list of models/<slug>/case.scad exactly as
    written there (the statements it depends on are copied verbatim into a let()).  Including case.scad
    itself would load the whole library barrel (22 s per case)."""
    lines = [osr.ENCODER_SCAD]
    extra: dict[str, list[str]] = {}
    for i, slug in enumerate(slugs):
        path = MODELS_DIR / slug / "case.scad"
        sts = {s.name: s for s in read_variables(path)}
        missing = [n for n in ("fan", "splitter", "variant") if n not in sts]
        if missing:
            raise ValueError(f"{path}: expected top-level {missing}")
        lets = ", ".join(f"{n} = {sts[n].rhs}" for n in sorted((n for n in _CASE_VARS if n in sts), key=lambda n: sts[n].start))
        lines.append(f"function case_{i}(part) = let({lets}) variant;")
        m = _EXTRA_PARTS.search(path.read_text(encoding="utf-8"))
        extra[slug] = [p.strip() for p in m.group(1).split(",")] if m else []
        lines.append(f'echo("V", "{slug}", "base", oracle_enc(case_{i}("base")));')
        for part in extra[slug]:
            lines.append(f'echo("V", "{slug}", "{part}", oracle_enc(case_{i}("{part}")));')
    return "\n".join(lines) + "\n", extra


def scrape(exe: Path | None = None) -> Scraped:
    statements = read_variables(CONSTANTS_SCAD, r"MCC_[A-Z0-9_]+")
    slugs = sorted(p.stem for p in DEVICES_SCAD_DIR.glob("*.scad"))
    exe = exe or osr.find_openscad()
    if exe is None:
        raise FileNotFoundError("OpenSCAD not found (MCC_OPENSCAD / Windows nightly / PATH)")
    res = osr.run_harness(values_harness([s.name for s in statements], slugs), exe=exe)
    if not res.ok:
        raise osr.OpenScadError("OpenSCAD failed evaluating constants/devices: " + "; ".join(res.errors[:3]), res.errors)
    values = {e[0]: osr.decode(e[1]) for e in res.tagged("C")}
    devices = {e[0]: osr.decode(e[1]) for e in res.tagged("D")}
    missing = [s.name for s in statements if s.name not in values] + [s for s in slugs if s not in devices]
    if missing:
        raise RuntimeError(f"OpenSCAD did not echo: {missing}")
    text, _ = cases_harness(slugs)
    res_c = osr.run_harness(text, exe=exe)
    if not res_c.ok:
        raise osr.OpenScadError("OpenSCAD failed evaluating the case variants: " + "; ".join(res_c.errors[:3]), res_c.errors)
    cases: dict[str, dict] = {s: {"variant": None, "extra": {}} for s in slugs}
    for slug, part, rec in res_c.tagged("V"):
        if part == "base":
            cases[slug]["variant"] = osr.decode(rec)
        else:
            cases[slug]["extra"][part] = osr.decode(rec)
    sources = {s: read_device_source(DEVICES_SCAD_DIR / f"{s}.scad", device_var(s)) for s in slugs}
    hashes = {str(p.relative_to(REPO)).replace("\\", "/"): hashlib.sha256(p.read_bytes()).hexdigest()
              for p in [CONSTANTS_SCAD, *(DEVICES_SCAD_DIR / f"{s}.scad" for s in slugs),
                        *(MODELS_DIR / s / "case.scad" for s in slugs)]}
    return Scraped(statements, values, devices, sources, cases, osr.openscad_version(exe), hashes)


# ---- helpers --------------------------------------------------------------------------------------------


def jnum(v: float) -> int | float:
    return int(v) if isinstance(v, float) and v.is_integer() and abs(v) < 1e15 else v


def lit(v: float) -> str:
    """Shortest decimal text of a float ('4', '4.6', '0.0625')."""
    return str(int(v)) if float(v).is_integer() else repr(float(v))


def is_pairs(v: Any) -> bool:
    return (isinstance(v, list) and len(v) > 0
            and all(isinstance(r, list) and len(r) == 2 and isinstance(r[0], str) for r in v))


def to_json(v: Any) -> Any:
    """Decoded OpenSCAD value -> JSON value: [[k, v], ...] becomes an ordered object."""
    if is_pairs(v):
        return {k: to_json(x) for k, x in v}
    if isinstance(v, list):
        return [to_json(x) for x in v]
    if isinstance(v, float):
        return jnum(v)
    return v


def dumps(obj: Any, indent: int = 0) -> str:
    """JSON with one key per line and scalar lists inline (diff-friendly, stable)."""
    pad = "  " * indent

    def scalar(x: Any) -> str:
        return json.dumps(jnum(x) if isinstance(x, float) else x, ensure_ascii=False)

    if isinstance(obj, dict):
        if not obj:
            return "{}"
        items = [f'{pad}  {json.dumps(k, ensure_ascii=False)}: {dumps(v, indent + 1)}' for k, v in obj.items()]
        return "{\n" + ",\n".join(items) + f"\n{pad}}}"
    if isinstance(obj, (list, tuple)):
        if all(not isinstance(x, (dict, list, tuple)) for x in obj):
            return "[" + ", ".join(scalar(x) for x in obj) + "]"
        return "[\n" + ",\n".join(f"{pad}  {dumps(x, indent + 1)}" for x in obj) + f"\n{pad}]"
    return scalar(obj)


# ---- the fixture document (S0) --------------------------------------------------------------------------


def values_doc(sc: Scraped) -> dict:
    """What OpenSCAD evaluated, as JSON.  Committed as cad/fixtures/scad_values.json."""
    return {
        "schema": 1,
        "generated_by": "python -m cad.tools.scad_export write",
        "openscad": sc.openscad_version,
        "oracle_files": sc.scad_hashes,
        "constants": {n: to_json(v) for n, v in sc.values.items()},
        "devices": {slug: to_json(rec) for slug, rec in sc.devices.items()},
        "cases": {slug: {"variant": to_json(c["variant"]), "extra": {p: to_json(v) for p, v in c["extra"].items()}}
                  for slug, c in sc.cases.items()},
    }


def expected_registry_values(constants: dict[str, Any]) -> dict[str, float]:
    """Registry row name -> the value OpenSCAD evaluated, for every row that comes from constants.scad
    (scalars, vector parts, flattened one-record tables).  Harvested literals have no fixture value."""
    out: dict[str, float] = {}
    for name, v in constants.items():
        if name in OPENSCAD_ONLY or name in OPTIONS or name in JSON_TABLES:
            continue
        if name in FLATTEN_TABLES:
            for f, sfx in FLATTEN_TABLES[name].items():
                out[f"{name}_{sfx}"] = float(v[f])
        elif name in VECTOR_PARTS:
            for part, x in zip(VECTOR_PARTS[name], v):
                out[f"{name}_{part}"] = float(x)
        elif isinstance(v, (int, float)) and not isinstance(v, bool):
            out[name] = float(v)
        else:
            raise ValueError(f"{name}: value {v!r} has no policy (scad_export.py policy tables)")
    return out


# ---- build ----------------------------------------------------------------------------------------------


@dataclass
class Report:
    src_defaulted: list[str] = field(default_factory=list)    # no citation: src is the constants.scad line
    conf_defaulted: list[str] = field(default_factory=list)   # no level stated: conf defaulted to assumed
    decided: list[tuple[str, str]] = field(default_factory=list)
    drawing: list[str] = field(default_factory=list)
    unit_guess: list[str] = field(default_factory=list)       # literal rows assigned mm without 'mm' in their text
    skipped: list[tuple[str, str]] = field(default_factory=list)


@dataclass
class Outputs:
    rows: list[Row]
    tables: dict[str, dict]
    devices: dict[str, dict]
    cases: dict[str, dict]
    report: Report
    fixture: dict


def _unit_for_literal(name: str, text: str, report: Report) -> str:
    if name in ANGLES:
        return "deg"
    if name in UNITLESS:
        return "none"
    if not re.search(r"\b(mm|deg)\b", text):
        report.unit_guess.append(name)
    return "mm"


def markdown_index() -> dict[str, list[str]]:
    """file name -> repo-relative paths of every markdown file under the documentation roots (not worktrees)."""
    index: dict[str, list[str]] = {}
    for root, pattern in ((REPO, "*.md"), (REPO / "knowledge", "**/*.md"), (REPO / ".claude" / "knowledge", "**/*.md"),
                          (REPO / "docs", "**/*.md")):
        for path in root.glob(pattern):
            index.setdefault(path.name, []).append(path.relative_to(REPO).as_posix())
    return {name: sorted(set(paths)) for name, paths in index.items()}


def resolve_citation(src: str, index: dict[str, list[str]]) -> str:
    """'architecture.md:46' -> '.claude/knowledge/architecture.md:46' when exactly one markdown file has that name;
    a citation that already has a directory, or has zero or several candidates, is returned unchanged."""
    m = re.match(r"^([\w.-]+\.md)(.*)$", src)
    if not m:
        return src
    hits = index.get(m.group(1), [])
    return hits[0] + m.group(2) if len(hits) == 1 else src


def _literal_expr(text: str, unit: str) -> str:
    return text if unit == "none" else f"{text} {unit}"


def build(sc: Scraped) -> Outputs:
    report = Report()
    doc = values_doc(sc)
    rows: dict[str, Row] = {}
    order: list[str] = []
    units: dict[str, str] = {}
    tables: dict[str, dict] = {}
    options: dict[str, Any] = {}
    vectors: dict[str, tuple[str, ...]] = {}
    flat_tables: dict[str, dict[str, str]] = {}
    derived: list[Statement] = []
    part_word = {"X": "X component", "Y": "Y component", "Z": "Z component", "LO": "lower bound", "HI": "upper bound"}

    def own(st: Statement) -> str:
        return comment_text(st.trailing + st.continuation)

    def add(name: str, unit: str, expression: str, desc: str, src: str, conf: str | None) -> None:
        rows[name] = Row(name, unit, expression, desc, src, conf)
        order.append(name)
        units[name] = unit

    def note(name: str, meta) -> None:
        if meta.src_defaulted:
            report.src_defaulted.append(name)
        if meta.conf_defaulted:
            report.conf_defaulted.append(name)
        if meta.decided_basis:
            report.decided.append((name, meta.decided_basis))
        if meta.conf == "drawing":
            report.drawing.append(name)

    for st in sc.statements:
        name, value = st.name, doc["constants"][st.name]
        leading = comment_text(st.leading)
        if name in OPENSCAD_ONLY:
            options.setdefault("openscad_only", {})[name] = value
            report.skipped.append((name, "openscad-only: " + OPENSCAD_ONLY[name]))
            continue
        if name in OPTIONS:
            options[OPTIONS[name]] = value
            continue
        if name in JSON_TABLES:
            fname = JSON_TABLES[name]
            prov = [c.text for c in (st.leading + st.trailing + st.continuation) if c.text.strip("/ ")]
            rows_json = copy.deepcopy(value)
            for (t, r, f), expr in TABLE_EXPR.items():
                if t == fname:
                    rows_json[r][f] = {"expr": expr}
            tables[fname] = {"schema": 1, "name": fname, "scad_name": name,
                             "scad_source": f"lib/mcc/constants.scad:{st.start}-{st.end}",
                             "provenance": prov, "rows": rows_json}
            continue
        if name in FLATTEN_TABLES:
            flat_tables[name] = {f: f"{name}_{sfx}" for f, sfx in FLATTEN_TABLES[name].items()}
            unknown = set(value) - set(FLATTEN_TABLES[name]) - {"confidence"}
            if unknown:
                raise ValueError(f"{name}: unexpected fields {sorted(unknown)}")
            for f, sfx in FLATTEN_TABLES[name].items():
                pname = f"{name}_{sfx}"
                desc, src, conf, _basis = FLAT_ROW_META[pname]
                src_def, conf_def = src == "-", conf is None
                add(pname, "mm", f"{lit(float(value[f]))} mm", desc,
                    f"lib/mcc/constants.scad:{st.start}" if src_def else src, conf or "assumed")
                if src_def:
                    report.src_defaulted.append(pname)
                if conf_def:
                    report.conf_defaulted.append(pname)
            continue
        if name in VECTOR_PARTS:
            parts = VECTOR_PARTS[name]
            if not (isinstance(value, list) and len(value) == len(parts)):
                raise ValueError(f"{name}: expected a {len(parts)}-vector, got {value!r}")
            vectors[name] = tuple(f"{name}_{p}" for p in parts)
            for p, comp in zip(parts, value):
                pname = f"{name}_{p}"
                meta = meta_for(pname, own(st), leading, st.start, literal=True)
                add(pname, "mm", f"{lit(float(comp))} mm", f"{meta.description} - {part_word[p]}", meta.src, meta.conf)
                note(pname, meta)
            continue
        if isinstance(value, (bool, str, list, dict)):
            raise ValueError(f"{name}: unclassified value {value!r}; add it to the policy tables of scad_export.py")
        if name in LOOKUP_LITERALS or _LITERAL.match(st.rhs):
            if name not in LOOKUP_LITERALS and float(st.rhs) != value:
                raise ValueError(f"{name}: literal {st.rhs} != OpenSCAD value {value}")
            text = st.rhs if name not in LOOKUP_LITERALS else lit(float(value))
            unit = _unit_for_literal(name, own(st) or leading, report)
            meta = meta_for(name, own(st), leading, st.start, literal=True)
            add(name, unit, _literal_expr(text, unit), meta.description, meta.src, meta.conf)
            note(name, meta)
        else:
            derived.append(st)

    dims = {n: params.UNIT_DIM[u] for n, u in units.items()}
    pending = list(derived)
    while pending:
        progressed = False
        for st in list(pending):
            try:
                expr, dim = translate(st.rhs, dims=dims, vectors=vectors, flat_tables=flat_tables)
            except ScadExprError as exc:
                if "unknown parameter" in str(exc):
                    continue
                raise ScadExprError(f"{st.name}: {exc}  (rhs: {st.rhs})") from exc
            unit = {params.LENGTH: "mm", params.ANGLE: "deg", params.NONE: "none"}[dim]
            meta = meta_for(st.name, own(st), comment_text(st.leading), st.start, literal=False)
            add(st.name, unit, expr, meta.description, meta.src, None)
            note(st.name, meta)
            dims[st.name] = dim
            pending.remove(st)
            progressed = True
        if not progressed:
            raise ScadExprError(f"cannot translate (unknown inputs): {[s.name for s in pending]}")

    # harvested literals (outside constants.scad): text-verified against the pinned source line
    for h in HARVEST:
        line = (REPO / h.file).read_text(encoding="utf-8").splitlines()[h.line - 1]
        if not re.search(h.pattern, line):
            raise ValueError(f"{h.name}: {h.file}:{h.line} no longer matches /{h.pattern}/: {line.strip()!r}")
        is_num = re.fullmatch(r"-?[0-9.]+", h.text) is not None
        add(h.name, h.unit, _literal_expr(h.text, h.unit) if is_num else h.text, h.description, f"{h.file}:{h.line}",
            "assumed" if is_num else None)

    src_order = {s.name: i for i, s in enumerate(sc.statements)}

    def sort_key(n: str) -> tuple[int, int]:
        base = n
        for b in list(vectors) + list(flat_tables):
            if n.startswith(b + "_"):
                base = b
                break
        return src_order.get(base, src_order.get(n, 10 ** 6)), order.index(n)

    md = markdown_index()
    final = [dataclasses.replace(rows[n], src=resolve_citation(rows[n].src, md)) for n in sorted(order, key=sort_key)]
    rows = {r.name: r for r in final}

    # the registry must evaluate to exactly what OpenSCAD evaluated
    scope = params.evaluate_registry(final)
    expected = expected_registry_values(doc["constants"])
    for name, want in expected.items():
        if name not in scope:
            raise ValueError(f"row {name} missing from the registry")
        if not close(scope[name].value, want):
            raise ValueError(f"{name}: {rows[name].expression!r} evaluates to {scope[name].value!r}, OpenSCAD says {want!r}")
    for ftable in tables.values():
        params._resolve(ftable["rows"], scope)
    problems = params.check_registry(final)
    if problems:
        raise ValueError("registry is malformed: " + "; ".join(problems[:5]))

    tables["options"] = {"schema": 1, "name": "options", "scad_name": "MCC_*_DEFAULT",
                         "provenance": ["selector defaults of lib/mcc/constants.scad; openscad_only entries are "
                                        "kept for round-trip completeness"],
                         "rows": options}
    devices = {slug: device_doc(slug, rec, sc.device_sources[slug]) for slug, rec in sc.devices.items()}
    cases = {slug: case_doc(slug, c) for slug, c in doc["cases"].items()}
    return Outputs(final, tables, devices, cases, report, doc)


def device_doc(slug: str, decoded: list, src: Any) -> dict:
    rec = {k: v for k, v in decoded}
    ports_out = []
    current: str | None = None
    by_id = {p.id: p for p in src.ports}
    for port in rec["ports"]:
        p = {k: v for k, v in port}
        ps = by_id[p["id"]]
        block = " ".join(ps.above).strip()
        if block:
            m = _MODEL_CITE.search(block)
            current = m.group(0) if m else None
        entry = {k: to_json(p[k]) for k in DEVICE_FIELDS}
        entry["source"] = current
        note = [t for t in (ps.above + ps.inner) if t]
        if note:
            entry["note"] = note
        ports_out.append(entry)
    size_cite = _MODEL_CITE.search(src.size_comment or "")
    return {
        "schema": 1,
        "slug": rec["slug"],
        "family": rec["family"],
        "size": to_json(rec["size"]),
        "source": {"file": rec["source"], "size": size_cite.group(0) if size_cite else None},
        "provenance": {"scad": f"lib/mcc/devices/{slug}.scad", "header": src.header},
        "ports": ports_out,
    }


# Configurations that exist only in cad/: OpenSCAD has no part for them.  The regression procedure of the case master
# (P2-81 verdict B6) needs every option of the closed list to switch at least once, so the template gets `bare` (no rail
# groove, no lid vents), a configuration that is never exported.  Each entry is a decision; the sync check validates it
# against the closed option list and does not compare it with OpenSCAD, but the layout oracle does echo its numbers.
# The entries are written to the case definition's key `test_configurations`; `configurations` holds only the
# extras OpenSCAD exports (gate of #76, A2: export status is data in the case definition).
EXTRA_CONFIGURATIONS: dict[str, dict[str, dict]] = {
    "pro-convert-for-ndi-to-hdmi": {"bare": {"rail": False, "lid_vents": False}},
}


def case_options_of(slug: str, variant: dict) -> dict:
    """The options a case definition states: the OpenSCAD variant without `tripod_insert` (it left the closed list,
    P2-81 Q81.3 default); a variant that switches it on cannot be expressed and is refused (T1-81.7)."""
    out = dict(variant)
    if "tripod_insert" in out:
        if out["tripod_insert"]:
            raise ValueError(f"{slug}: tripod_insert is true; the option is not in {params.CASE_OPTIONS} (T1-81.7)")
        del out["tripod_insert"]
    return out


def case_doc(slug: str, c: dict) -> dict:
    base = case_options_of(slug, c["variant"])
    bad = set(base) - set(params.CASE_OPTIONS)
    if bad:
        raise ValueError(f"{slug}: variant keys {sorted(bad)} are not case options {params.CASE_OPTIONS}")
    configs = {}
    for part, variant in ((p, case_options_of(slug, v)) for p, v in c["extra"].items()):
        diff = {k: v for k, v in variant.items() if k not in base or base[k] != v}
        if set(variant) != set(base):
            raise ValueError(f"{slug}/{part}: key set differs from the base variant")
        configs[part] = diff
    tests = {}
    for part, diff in EXTRA_CONFIGURATIONS.get(slug, {}).items():
        if part in configs:
            raise ValueError(f"{slug}: configuration {part!r} is also an OpenSCAD part")
        tests[part] = dict(diff)
    return {"schema": 1, "slug": slug, "device": slug, "options": base, "configurations": configs,
            "test_configurations": tests}


# ---- write ----------------------------------------------------------------------------------------------


def write(out: Outputs, cad_dir: Path) -> list[Path]:
    written: list[Path] = []
    for sub in ("parameters", "data", "devices", "cases", "fixtures"):
        (cad_dir / sub).mkdir(parents=True, exist_ok=True)
    p = cad_dir / "parameters" / "constants.csv"
    params.write_registry(out.rows, p)
    written.append(p)
    for kind, docs in (("data", out.tables), ("devices", out.devices), ("cases", out.cases)):
        for name, d in docs.items():
            p = cad_dir / kind / f"{name}.json"
            p.write_text(dumps(d) + "\n", encoding="utf-8", newline="\n")
            written.append(p)
    p = cad_dir / "fixtures" / "scad_values.json"
    p.write_text(dumps(out.fixture) + "\n", encoding="utf-8", newline="\n")
    written.append(p)
    return written


# ---- comparison: used by `check` and by the permanent tests (no OpenSCAD needed) ---------------------------


def plain(x: Any) -> Any:
    """Read-only mappings/tuples returned by cad.params -> plain dict/list for comparison."""
    if hasattr(x, "items"):
        return {k: plain(v) for k, v in x.items()}
    if isinstance(x, (list, tuple)):
        return [plain(v) for v in x]
    return x


def deep_compare(a: Any, b: Any, path: str, problems: list[str], rel: float = 1e-12, ordered: bool = True) -> None:
    """Numbers compare with a tight relative tolerance (int 25 == float 25.0); everything else exactly.
    Object key ORDER must match unless ordered=False (table rows are searched in order; options are not)."""
    if isinstance(a, dict) and isinstance(b, dict):
        if (list(a) != list(b)) if ordered else (set(a) != set(b)):
            problems.append(f"{path}: keys {list(a)} != {list(b)}")
            return
        for k in a:
            deep_compare(a[k], b[k], f"{path}.{k}", problems, rel, ordered)
    elif isinstance(a, (list, tuple)) and isinstance(b, (list, tuple)):
        if len(a) != len(b):
            problems.append(f"{path}: length {len(a)} != {len(b)}")
            return
        for i, (x, y) in enumerate(zip(a, b)):
            deep_compare(x, y, f"{path}[{i}]", problems, rel, ordered)
    elif isinstance(a, (int, float)) and isinstance(b, (int, float)) and not isinstance(a, bool) and not isinstance(b, bool):
        if not close(float(a), float(b), rel=rel, abs_=rel):
            problems.append(f"{path}: {a!r} != {b!r}")
    elif a != b:
        problems.append(f"{path}: {a!r} != {b!r}")


def compare_cad_to_values(doc: dict, cad_dir: Path | None = None) -> list[str]:
    """Problems between the files under `cad_dir` and the evaluated values `doc` (the fixture document).
    Reads every file through cad.params.  Empty list = cad/ is a verified mirror."""
    cad_dir = cad_dir or params.CAD_DIR
    reg_path = cad_dir / "parameters" / "constants.csv"
    data_dir = cad_dir / "data"
    problems: list[str] = []

    rows = params.read_registry(reg_path)
    problems += [f"registry: {p}" for p in params.check_registry(rows)]
    expected = expected_registry_values(doc["constants"])
    by_name = {r.name: r for r in rows}
    harvest = {h.name: h for h in HARVEST}
    for n in sorted(set(expected) - set(by_name)):
        problems.append(f"registry: row {n} missing (constants.scad has it)")
    for n in sorted(set(by_name) - set(expected) - set(harvest)):
        problems.append(f"registry: row {n} has no counterpart in constants.scad or the harvest list")
    for n in sorted(set(harvest) - set(by_name)):
        problems.append(f"registry: harvested row {n} missing")
    try:
        scope = params.evaluate_registry(rows)
    except params.ExpressionError as exc:
        return problems + [f"registry does not evaluate: {exc}"]
    for n, want in expected.items():
        if n in scope and not close(scope[n].value, want):
            problems.append(f"registry: {n} = {by_name[n].expression!r} -> {scope[n].value!r}, OpenSCAD {want!r}")
    for n, h in harvest.items():
        if n not in by_name:
            continue
        is_num = re.fullmatch(r"-?[0-9.]+", h.text) is not None
        want = float(h.text) if is_num else params.evaluate(h.text, scope).value
        if (scope[n].value != want or by_name[n].unit != h.unit or by_name[n].src != f"{h.file}:{h.line}"
                or (not is_num and by_name[n].expression != h.text) or (is_num and by_name[n].conf != "assumed")):
            problems.append(f"registry: harvested row {n} differs from the harvest list")

    for stmt, fname in JSON_TABLES.items():
        got = plain(params.table(fname, data_dir, reg_path))
        deep_compare(got, doc["constants"][stmt], f"data/{fname}.json", problems)
    want_opts = {OPTIONS[k]: doc["constants"][k] for k in OPTIONS}
    want_opts["openscad_only"] = {k: doc["constants"][k] for k in OPENSCAD_ONLY}
    deep_compare(plain(params.table("options", data_dir, reg_path)), want_opts, "data/options.json", problems, ordered=False)
    extra_tables = {p.stem for p in data_dir.glob("*.json")} - set(JSON_TABLES.values()) - {"options"}
    if extra_tables:
        problems.append(f"data/: files without an OpenSCAD table: {sorted(extra_tables)}")

    if params.device_slugs(cad_dir / "devices") != sorted(doc["devices"]):
        problems.append(f"devices/: {params.device_slugs(cad_dir / 'devices')} != {sorted(doc['devices'])}")
    for slug, want in doc["devices"].items():
        got = params.device_doc(slug, cad_dir / "devices")
        for k in ("slug", "family", "size"):
            deep_compare(got.get(k), want[k], f"devices/{slug}.{k}", problems)
        if got["source"]["file"] != want["source"]:
            problems.append(f"devices/{slug}.source.file {got['source']['file']!r} != {want['source']!r}")
        gp = [{k: p.get(k) for k in DEVICE_FIELDS} for p in got["ports"]]
        wp = [{k: p.get(k) for k in DEVICE_FIELDS} for p in want["ports"]]
        deep_compare(gp, wp, f"devices/{slug}.ports", problems)

    if params.case_slugs(cad_dir / "cases") != sorted(doc["cases"]):
        problems.append(f"cases/: {params.case_slugs(cad_dir / 'cases')} != {sorted(doc['cases'])}")
    for slug, want in doc["cases"].items():
        got = params.case_doc(slug, cad_dir / "cases")
        if got["device"] != slug or got["slug"] != slug:
            problems.append(f"cases/{slug}: slug/device differ")
        deep_compare(got["options"], case_options_of(slug, want["variant"]), f"cases/{slug}.options", problems)
        extras = EXTRA_CONFIGURATIONS.get(slug, {})
        if set(got["configurations"]) != set(want["extra"]):
            problems.append(f"cases/{slug}: configurations {sorted(got['configurations'])} != {sorted(want['extra'])}")
        if set(got["test_configurations"]) != set(extras):
            problems.append(f"cases/{slug}: test_configurations {sorted(got['test_configurations'])} != {sorted(extras)}")
        for part, variant in want["extra"].items():
            merged = {**got["options"], **got["configurations"].get(part, {})}
            deep_compare(merged, case_options_of(slug, variant), f"cases/{slug}.configurations.{part}", problems)
        for part, diff in extras.items():
            deep_compare(got["test_configurations"].get(part), diff, f"cases/{slug}.test_configurations.{part}", problems)
    return problems


def check(cad_dir: Path | None = None, fixture_path: Path | None = None, *, sc: Scraped | None = None) -> list[str]:
    """Re-derive from OpenSCAD and report every drift: fixture vs OpenSCAD, then cad/ vs the fresh values."""
    fresh = values_doc(sc or scrape())
    fixture_path = fixture_path or FIXTURE_PATH
    problems: list[str] = []
    if not fixture_path.is_file():
        problems.append(f"fixture {fixture_path} missing")
    else:
        committed = json.loads(fixture_path.read_text(encoding="utf-8"))
        for key in ("constants", "devices", "cases"):
            deep_compare(committed[key], fresh[key], f"fixture.{key}", problems, rel=1e-15)
    return problems + compare_cad_to_values(fresh, cad_dir)


# ---- manual-pass report -------------------------------------------------------------------------------


_DECISION_WORDS = re.compile(r"\buser decision\b|\bUSER DECISION\b|\bfixed user decision\b|\bACCEPTED\b", re.I)


def unreferenced_constants(statements: list[Statement]) -> tuple[list[str], list[str]]:
    """(names that no geometry, model or test mentions, names only a coupon or a test mentions), comments stripped."""
    def code(path: Path) -> str:
        text = re.sub(r"/\*.*?\*/", "", path.read_text(encoding="utf-8"), flags=re.S)
        return re.sub(r"//[^\n]*", "", text)

    files = [p for d in ("lib", "models", "tests") for p in (REPO / d).rglob("*.scad") if "BOSL2" not in p.as_posix()]
    corpus = {p: code(p) for p in files}
    unused, test_only = [], []
    for st in statements:
        if not st.name.startswith("MCC_"):
            continue
        pat = re.compile(r"\b" + re.escape(st.name) + r"\b")
        users: set[str] = set()
        for p, text in corpus.items():
            rel = p.relative_to(REPO).as_posix()
            for line in text.splitlines():
                if pat.search(line) and not (rel == "lib/mcc/constants.scad" and re.match(rf"\s*{re.escape(st.name)}\s*=", line)):
                    users.add(rel)
        if not users:
            unused.append(st.name)
        elif all(u.startswith(("tests/", "models/coupons/")) for u in users):
            test_only.append(st.name)
    return unused, test_only


def manual_pass_report(sc: Scraped, out: Outputs) -> str:
    """Markdown lists of everything the exporter had to default or could not grade: the input of the human review.
    Nothing here is a source the tool invented: src defaults to the constants.scad line, conf to `assumed`."""
    rows = {r.name: r for r in out.rows}
    rep = out.report
    lines: list[str] = []

    def section(title: str, body: list[str]) -> None:
        lines.append(f"## {title} ({len(body)})")
        lines.extend(body or ["(none)"])
        lines.append("")

    section("src defaulted to the constants.scad line (no citation in the row's own text)",
            [f"- {n}: {rows[n].src}" for n in rep.src_defaulted])
    section("conf defaulted to assumed (the text states no level)", [f"- {n}: src {rows[n].src}" for n in rep.conf_defaulted])
    section("conf decided (the row's own text names a decision)", [f"- {n}: '{basis}'" for n, basis in rep.decided])
    section("conf drawing (banner override)", [f"- {n}" for n in rep.drawing])
    decided_now = {n for n, _ in rep.decided}
    cands = []
    for st in sc.statements:
        if st.name in rows and st.name not in decided_now and rows[st.name].conf is not None:
            own = comment_text(st.trailing) + " " + comment_text(st.continuation)
            lead = comment_text(st.leading)
            if _DECISION_WORDS.search(lead) and not _DECISION_WORDS.search(own):
                cands.append(f"- {st.name} (conf {rows[st.name].conf}): its leading comment block mentions a decision")
    section("decided candidates (the leading block, not the row, mentions a decision)", cands)
    unused, test_only = unreferenced_constants(sc.statements)
    section("constants that no geometry, model or test references", [f"- {n}" for n in unused])
    section("constants referenced only by a coupon or a test", [f"- {n}" for n in test_only])
    return "\n".join(lines)


# ---- CLI ------------------------------------------------------------------------------------------------


def print_report(out: Outputs) -> None:
    r = out.report
    lit_rows = [x for x in out.rows if x.conf is not None]
    print(f"registry rows: {len(out.rows)} ({len(lit_rows)} literal, {len(out.rows) - len(lit_rows)} expression)   "
          f"tables: {sorted(out.tables)}   devices: {len(out.devices)}   cases: {len(out.cases)}")
    by_conf: dict[str, int] = {}
    for x in lit_rows:
        by_conf[x.conf] = by_conf.get(x.conf, 0) + 1
    print("literal rows by conf:", dict(sorted(by_conf.items())))
    print(f"src defaulted to the constants.scad line: {len(r.src_defaulted)}   conf defaulted to assumed: {len(r.conf_defaulted)}")
    print("decided:", [f"{n} ('{b}')" for n, b in r.decided])
    print("drawing:", r.drawing)
    print("literal rows assigned mm without 'mm' in their text:", r.unit_guess)
    print("skipped:", [f"{n} ({why})" for n, why in r.skipped])


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="cad.tools.scad_export", description=__doc__.split("\n")[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    w = sub.add_parser("write")
    w.add_argument("--out", type=Path, default=params.CAD_DIR, help="target cad/ directory")
    sub.add_parser("check")
    sub.add_parser("report", help="markdown lists for the manual pass (defaulted src/conf, decided candidates, unused constants)")
    args = ap.parse_args(argv)
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    if args.cmd == "write":
        out = build(scrape())
        files = write(out, args.out)
        print_report(out)
        print(f"wrote {len(files)} files under {args.out}")
        return 0
    if args.cmd == "report":
        sc = scrape()
        print(manual_pass_report(sc, build(sc)))
        return 0
    problems = check()
    for p in problems:
        print("DRIFT:", p)
    print("cad/ is in sync with lib/mcc" if not problems else f"{len(problems)} problem(s)")
    return 1 if problems else 0


if __name__ == "__main__":
    raise SystemExit(main())
