#!/usr/bin/env python3
"""Print-pose transforms and Bambu Studio project (.3mf) writer.

Why this exists (2026-09-27): OpenSCAD exports every part in its *model* frame — the lid floats at
Z = 48..51 (its assembled height), the panel plate hangs below Z = 0 with its bosses pointing down,
and every part is centred on the XY origin. Imported into Bambu Studio that means: all parts land
on top of each other on one plate, the base sits in the X1C's front-left exclusion zone (slicing is
blocked), the panel prints upside-down on its bosses (the whole 2 mm plate becomes a floating
region), and there is no printer/filament/process setting at all. A slicer user can do nothing
with that without re-orienting and re-arranging every part by hand.

So `build.py render` now keeps the OpenSCAD model-frame mesh (`<part>.model.stl` — goldens, STEP)
and derives the print-ready artefacts from it here:

    <part>.stl   the part in its print pose (architecture.md §8 / print-check §3), resting on Z = 0,
                 on the X1C bed centre (nudged clear of the front-left exclusion pad when a part is
                 big enough to reach it) — imports straight onto the plate.
    <part>.3mf   a real Bambu Studio *project*: one plate, part in print pose, X1C 0.4 nozzle +
                 Bambu ASA + the repo's process overrides (5 walls, outer brim).
    <slug>.3mf   (models only) the whole print set as one project, one plate per bed-load
                 (base + panel share plate 1 when they fit, lid on plate 2).

The project format mirrors what Bambu Studio 02.08.02.61 itself writes (a GUI-saved reference was
unpacked and diffed while writing this module): production-extension 3MF, one object file per
object under 3D/Objects/, Metadata/model_settings.config for names/plates, and
Metadata/project_settings.config = the full X1C + Bambu ASA preset dump
(scripts/bambu/x1c-0.4-asa.project_settings.json) with PROCESS_OVERRIDES applied and listed in
`different_settings_to_system`, exactly as the GUI records a user edit.
"""

from __future__ import annotations

import json
import math
import uuid
import zipfile
from dataclasses import dataclass
from pathlib import Path

import numpy as np

SCRIPTS_DIR = Path(__file__).resolve().parent
SETTINGS_TEMPLATE = SCRIPTS_DIR / "bambu" / "x1c-0.4-asa.project_settings.json"

# Bambu Lab X1 Carbon (CLAUDE.md: the confirmed printer). printable_area / bed_exclude_area are
# copied from the preset dump itself so they cannot drift from what the slicer enforces.
BED_X = 256.0
BED_Y = 256.0
BED_MARGIN = 6.0            # lib/mcc/constants.scad MCC_BED_MARGIN
EXCLUDE_X = 18.0            # bed_exclude_area "0x0,18x0,18x28,0x28" (front-left lidar pad)
EXCLUDE_Y = 28.0
PLATE_STRIDE = BED_X * 1.2  # Bambu lays plates out on a grid with a 1/5-plate gap (verified: 435.2 = 128 + 307.2)
PART_GAP = 12.0             # between parts sharing a plate — clears two 8 mm outer brims' worst overlap well enough for Bambu's own arrange rule
BAMBU_VERSION = "02.08.02.61"

# Process-level edits on top of Bambu's "0.20mm Standard @BBL X1C" preset — print-check §4:
# 5 perimeters on every structural wall (fixed decision), a wide outer brim against ASA warp.
PROCESS_OVERRIDES: dict[str, str] = {
    "wall_loops": "5",
    "brim_type": "outer_only",
    "brim_width": "8",
}

# Print poses. "as-modelled" keeps OpenSCAD's frame; "flip" rotates 180 deg about X (model -Z
# becomes printer +Z). print-check §3: the panel plate prints face-down (its authored front face is
# model Z = 0 with the field/bosses toward -Z), shells print open-side-up (the lid is authored in
# its assembled pose, exterior on top, so it must be flipped to put its open/tongue side up).
POSES = ("as-modelled", "flip")
DEFAULT_POSE_BY_PART = {"lid": "flip", "panel": "flip"}


def pose_matrix(pose: str) -> np.ndarray:
    if pose == "as-modelled":
        return np.eye(3)
    if pose == "flip":
        return np.array([[1.0, 0.0, 0.0], [0.0, -1.0, 0.0], [0.0, 0.0, -1.0]])
    raise ValueError(f"unknown print pose '{pose}' (expected one of {POSES})")


def to_print_pose(vertices: np.ndarray, pose: str) -> np.ndarray:
    """Rotate into the print pose and rest the part on Z = 0, XY-centred on the origin."""

    v = vertices @ pose_matrix(pose).T
    lo, hi = v.min(axis=0), v.max(axis=0)
    centre = (lo + hi) / 2.0
    return v - np.array([centre[0], centre[1], lo[2]])



# -----------------------------------------------------------------------------------------
# Plate layout
# -----------------------------------------------------------------------------------------

@dataclass
class PrintObject:
    name: str
    vertices: np.ndarray  # print pose, resting on Z = 0, XY-centred on the origin (to_print_pose())
    faces: np.ndarray

    @property
    def size(self) -> np.ndarray:
        return self.vertices.max(axis=0) - self.vertices.min(axis=0)


@dataclass
class Placement:
    obj: PrintObject
    x: float  # bed coordinates of the object's XY centre
    y: float


EXCLUDE_CLR = 2.0  # clearance kept around the exclusion pad, mm


def _usable_y() -> tuple[float, float]:
    return BED_MARGIN, BED_Y - BED_MARGIN


def _hits_exclusion(p: "Placement") -> bool:
    x_lo = p.x - p.obj.size[0] / 2.0
    y_lo = p.y - p.obj.size[1] / 2.0
    return x_lo < EXCLUDE_X + EXCLUDE_CLR and y_lo < EXCLUDE_Y + EXCLUDE_CLR


def _clear_exclusion(plate: list["Placement"]) -> None:
    """Shift a laid-out plate (+Y first, then +X) just far enough that no part overlaps the X1C's
    front-left exclusion pad ("too close to exclusion area" blocks slicing), staying on the bed."""

    if not any(_hits_exclusion(p) for p in plate):
        return
    hi = BED_X - BED_MARGIN
    room_y = hi - max(p.y + p.obj.size[1] / 2.0 for p in plate)
    room_x = hi - max(p.x + p.obj.size[0] / 2.0 for p in plate)
    need_y = max(EXCLUDE_Y + EXCLUDE_CLR - (p.y - p.obj.size[1] / 2.0) for p in plate if _hits_exclusion(p))
    need_x = max(EXCLUDE_X + EXCLUDE_CLR - (p.x - p.obj.size[0] / 2.0) for p in plate if _hits_exclusion(p))
    if need_y <= room_y:
        for p in plate:
            p.y += need_y
    elif need_x <= room_x:
        for p in plate:
            p.x += need_x
    else:
        raise ValueError("cannot keep " + ", ".join(p.obj.name for p in plate) + " off the X1C exclusion area")


def _fits_x(obj: PrintObject) -> bool:
    return obj.size[0] <= BED_X - 2 * BED_MARGIN


def layout_plates(objects: list[PrintObject]) -> list[list[Placement]]:
    """Greedy shelf layout, in the given order: parts fill a row left-to-right, rows stack
    front-to-back, a new plate opens when the next row does not fit. Each plate's block of rows is
    centred on the usable bed area (rows centred in X). Every part must fit a bed on its own —
    build.py's bbox check already guarantees that for anything that renders."""

    y_lo, y_hi = _usable_y()
    usable_y = y_hi - y_lo
    usable_x = BED_X - 2 * BED_MARGIN
    plates: list[list[list[PrintObject]]] = []  # plate -> rows -> objects

    def row_w(row: list[PrintObject]) -> float:
        return sum(o.size[0] for o in row) + PART_GAP * (len(row) - 1)

    def rows_h(rows: list[list[PrintObject]]) -> float:
        return sum(max(o.size[1] for o in r) for r in rows) + PART_GAP * (len(rows) - 1)

    for obj in objects:
        if not _fits_x(obj) or obj.size[1] > usable_y:
            raise ValueError(f"{obj.name}: {obj.size[0]:.1f} x {obj.size[1]:.1f} mm does not fit the X1C bed")
        if plates:
            rows = plates[-1]
            if row_w(rows[-1]) + PART_GAP + obj.size[0] <= usable_x and rows_h(rows[:-1] + [rows[-1] + [obj]]) <= usable_y:
                rows[-1].append(obj)
                continue
            if rows_h(rows + [[obj]]) <= usable_y:
                rows.append([obj])
                continue
        plates.append([[obj]])

    placed: list[list[Placement]] = []
    for rows in plates:
        y = y_lo + (usable_y - rows_h(rows)) / 2.0
        plate: list[Placement] = []
        for r in rows:
            h = max(o.size[1] for o in r)
            x = (BED_X - row_w(r)) / 2.0
            for o in r:
                plate.append(Placement(obj=o, x=x + o.size[0] / 2.0, y=y + h / 2.0))
                x += o.size[0] + PART_GAP
            y += h + PART_GAP
        _clear_exclusion(plate)
        placed.append(plate)
    return placed


def plate_origin(index: int, n_plates: int) -> tuple[float, float]:
    """World XY of plate `index` (0-based) in Bambu Studio's plate grid."""

    cols = max(1, math.ceil(math.sqrt(n_plates)))
    row, col = divmod(index, cols)
    return col * PLATE_STRIDE, -row * PLATE_STRIDE


# -----------------------------------------------------------------------------------------
# Project settings
# -----------------------------------------------------------------------------------------

def project_settings(n_plates: int) -> dict:
    settings = json.loads(SETTINGS_TEMPLATE.read_text(encoding="utf-8"))
    settings.update(PROCESS_OVERRIDES)
    settings["different_settings_to_system"] = [";".join(sorted(PROCESS_OVERRIDES)), "", ""]
    # One wipe-tower position per plate (single filament: no tower is printed, but the GUI keeps
    # the per-plate list the same length as the plate list).
    settings["wipe_tower_x"] = [settings["wipe_tower_x"][0]] * n_plates
    settings["wipe_tower_y"] = [settings["wipe_tower_y"][0]] * n_plates
    settings["version"] = BAMBU_VERSION
    return settings


# -----------------------------------------------------------------------------------------
# 3MF writer
# -----------------------------------------------------------------------------------------

_NS = (
    'xmlns="http://schemas.microsoft.com/3dmanufacturing/core/2015/02" '
    'xmlns:BambuStudio="http://schemas.bambulab.com/package/2021" '
    'xmlns:p="http://schemas.microsoft.com/3dmanufacturing/production/2015/06" requiredextensions="p"'
)


def _esc(text: str) -> str:
    return (text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;"))


def _fmt(x: float) -> str:
    s = f"{x:.6f}".rstrip("0").rstrip(".")
    return "0" if s in ("-0", "") else s


def _object_model(mesh_id: int, vertices: np.ndarray, faces: np.ndarray) -> str:
    out = [
        '<?xml version="1.0" encoding="UTF-8"?>\n',
        f'<model unit="millimeter" xml:lang="en-US" {_NS}>\n',
        ' <metadata name="BambuStudio:3mfVersion">1</metadata>\n',
        " <resources>\n",
        f'  <object id="{mesh_id}" p:UUID="{uuid.uuid4()}" type="model">\n',
        "   <mesh>\n    <vertices>\n",
    ]
    out += [f'     <vertex x="{_fmt(a)}" y="{_fmt(b)}" z="{_fmt(c)}"/>\n' for a, b, c in vertices]
    out.append("    </vertices>\n    <triangles>\n")
    out += [f'     <triangle v1="{a}" v2="{b}" v3="{c}"/>\n' for a, b, c in faces]
    out.append("    </triangles>\n   </mesh>\n  </object>\n </resources>\n <build/>\n</model>\n")
    return "".join(out)


def write_project(path: Path, plates: list[list[Placement]], *, title: str, description: str = "") -> Path:
    """Write a Bambu Studio project 3MF with one plate per entry of `plates`."""

    n_plates = len(plates)
    today = __import__("datetime").date.today().isoformat()
    obj_files: list[tuple[str, str]] = []
    top_objects: list[str] = []
    build_items: list[str] = []
    cfg_objects: list[str] = []
    cfg_plates: list[str] = []

    next_id = 1
    for p_idx, plate in enumerate(plates):
        ox, oy = plate_origin(p_idx, n_plates)
        instances: list[str] = []
        for pl in plate:
            mesh_id, obj_id, part_id = next_id, next_id + 1, next_id
            next_id += 2
            v = pl.obj.vertices
            h = float(v[:, 2].max())
            # Bambu stores each object's mesh around its own bbox centre and positions it with the
            # build transform (reference file: vertices z in [-25, 25], item transform z = 25).
            local = v - np.array([0.0, 0.0, h / 2.0])
            obj_path = f"3D/Objects/object_{mesh_id}.model"
            obj_files.append((obj_path, _object_model(mesh_id, local, pl.obj.faces)))
            top_objects.append(
                f'  <object id="{obj_id}" p:UUID="{uuid.uuid4()}" type="model">\n'
                f'   <components>\n'
                f'    <component p:path="/{obj_path}" objectid="{mesh_id}" p:UUID="{uuid.uuid4()}" '
                f'transform="1 0 0 0 1 0 0 0 1 0 0 0"/>\n'
                f'   </components>\n  </object>\n'
            )
            tx, ty, tz = ox + pl.x, oy + pl.y, h / 2.0
            build_items.append(
                f'  <item objectid="{obj_id}" p:UUID="{uuid.uuid4()}" '
                f'transform="1 0 0 0 1 0 0 0 1 {_fmt(tx)} {_fmt(ty)} {_fmt(tz)}" printable="1"/>\n'
            )
            name = _esc(pl.obj.name)
            cfg_objects.append(
                f'  <object id="{obj_id}">\n'
                f'    <metadata key="name" value="{name}"/>\n'
                f'    <metadata key="extruder" value="1"/>\n'
                f'    <part id="{part_id}" subtype="normal_part">\n'
                f'      <metadata key="name" value="{name}"/>\n'
                f'      <metadata key="matrix" value="1 0 0 0 0 1 0 0 0 0 1 0 0 0 0 1"/>\n'
                f'      <mesh_stat face_count="{len(pl.obj.faces)}" edges_fixed="0" degenerate_facets="0" '
                f'facets_removed="0" facets_reversed="0" backwards_edges="0"/>\n'
                f'    </part>\n  </object>\n'
            )
            instances.append(
                f'    <model_instance>\n'
                f'      <metadata key="object_id" value="{obj_id}"/>\n'
                f'      <metadata key="instance_id" value="0"/>\n'
                f'    </model_instance>\n'
            )
        cfg_plates.append(
            f'  <plate>\n'
            f'    <metadata key="plater_id" value="{p_idx + 1}"/>\n'
            f'    <metadata key="plater_name" value="{_esc(", ".join(pl.obj.name for pl in plate))}"/>\n'
            f'    <metadata key="locked" value="false"/>\n'
            + "".join(instances)
            + "  </plate>\n"
        )

    model = (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        f'<model unit="millimeter" xml:lang="en-US" {_NS}>\n'
        f' <metadata name="Application">BambuStudio-{BAMBU_VERSION}</metadata>\n'
        ' <metadata name="BambuStudio:3mfVersion">1</metadata>\n'
        f' <metadata name="Title">{_esc(title)}</metadata>\n'
        f' <metadata name="Description">{_esc(description)}</metadata>\n'
        f' <metadata name="CreationDate">{today}</metadata>\n'
        f' <metadata name="ModificationDate">{today}</metadata>\n'
        " <resources>\n" + "".join(top_objects) + " </resources>\n"
        f' <build p:UUID="{uuid.uuid4()}">\n' + "".join(build_items) + " </build>\n</model>\n"
    )
    model_rels = (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">\n'
        + "".join(
            f' <Relationship Target="/{p}" Id="rel-{i + 1}" '
            'Type="http://schemas.microsoft.com/3dmanufacturing/2013/01/3dmodel"/>\n'
            for i, (p, _) in enumerate(obj_files)
        )
        + "</Relationships>\n"
    )
    root_rels = (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">\n'
        ' <Relationship Target="/3D/3dmodel.model" Id="rel-1" '
        'Type="http://schemas.microsoft.com/3dmanufacturing/2013/01/3dmodel"/>\n'
        "</Relationships>\n"
    )
    content_types = (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">\n'
        ' <Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>\n'
        ' <Default Extension="model" ContentType="application/vnd.ms-package.3dmanufacturing-3dmodel+xml"/>\n'
        ' <Default Extension="png" ContentType="image/png"/>\n'
        ' <Default Extension="gcode" ContentType="text/x.gcode"/>\n'
        "</Types>\n"
    )
    model_settings = '<?xml version="1.0" encoding="UTF-8"?>\n<config>\n' + "".join(cfg_objects) + "".join(cfg_plates) + "</config>\n"
    slice_info = (
        '<?xml version="1.0" encoding="UTF-8"?>\n<config>\n  <header>\n'
        '    <header_item key="X-BBL-Client-Type" value="slicer"/>\n'
        f'    <header_item key="X-BBL-Client-Version" value="{BAMBU_VERSION}"/>\n'
        "  </header>\n</config>\n"
    )

    path.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("[Content_Types].xml", content_types)
        zf.writestr("_rels/.rels", root_rels)
        zf.writestr("3D/3dmodel.model", model)
        zf.writestr("3D/_rels/3dmodel.model.rels", model_rels)
        for p, text in obj_files:
            zf.writestr(p, text)
        zf.writestr("Metadata/model_settings.config", model_settings)
        zf.writestr("Metadata/project_settings.config", json.dumps(project_settings(n_plates), indent=4, sort_keys=True))
        zf.writestr("Metadata/slice_info.config", slice_info)
    return path
