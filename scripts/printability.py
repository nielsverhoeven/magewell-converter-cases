#!/usr/bin/env python3
"""Layer-by-layer printability analysis of a print-pose mesh (Tier 3, `build.py check`).

Bambu Studio refuses to trust a part silently: on slicing it warns "It seems object X has floating
regions. Please re-orient the object or enable support generation." for every region that starts
in mid-air. This module reproduces that test on the exported print-pose STL so it fails in CI
instead of on the slicer user's desk:

  * floating island — a connected layer region with (almost) nothing under it in the previous
    layer. Always a defect: either the pose is wrong or the geometry has a hanging cusp/boss.
  * unsupported overhang — layer area that sticks out more than one layer height (i.e. steeper
    than 45 deg) past the layer below. Reported for review, not failed on: flat bridges between
    walls are legitimate and the slicer bridges them.
  * accidental see-through opening (lids only, non_prismatic_see_through()) — a hole nobody drew,
    where two features that are each fine alone (a counterbore and a groove) together cut through.

Needs trimesh + shapely (requirements.txt).
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field

import numpy as np
from shapely.geometry import Point, Polygon

LAYER_H = 0.2             # mm — Bambu "0.20mm Standard @BBL X1C", the profile the projects ship with
LINE_W = 0.42             # mm — the preset's line_width
SUPPORT_THRESHOLD_ANGLE = 30.0  # deg — the preset's support_threshold_angle
CANTILEVER_REACH = 3.0    # mm — Bambu's hard-coded cantilever limit
CANTILEVER_MIN_AREA = 0.5  # mm^2
ISLAND_MIN_AREA = 0.2     # mm^2 — ignore tessellation slivers below this
ISLAND_SUPPORT_FRAC = 0.02  # a region counts as supported when >= 2 % of it overlaps the layer below
OVERHANG_REPORT_MIN = 20.0  # mm^2 per layer — smaller unsupported rims are just the 45 deg slope
SEE_THROUGH_Z_MERGE = 0.01   # mm — vertex heights closer than this are one break-point
SEE_THROUGH_MIN_AREA = 0.05  # mm^2 — ignore tessellation dust
SEE_THROUGH_SAME_AREA = 0.05  # mm^2 — two outlines are the same when their symmetric difference is this small


@dataclass
class Island:
    z: float
    area: float
    centroid: tuple[float, float]
    bounds: tuple[float, float, float, float]


@dataclass
class Overhang:
    z: float
    area: float
    bounds: tuple[float, float, float, float]


@dataclass
class Cantilever:
    z: float
    area: float
    reach: float  # mm — farthest point of the overhang from where it attaches to the layer below
    bounds: tuple[float, float, float, float]


@dataclass
class SeeThrough:
    area: float
    centroid: tuple[float, float]


@dataclass
class PrintabilityReport:
    islands: list[Island] = field(default_factory=list)
    cantilevers: list[Cantilever] = field(default_factory=list)
    overhangs: list[Overhang] = field(default_factory=list)
    layers: int = 0

    @property
    def ok(self) -> bool:
        return not self.islands and not self.cantilevers


def _cantilevers(layer, prev, z: float, layer_h: float) -> list[Cantilever]:
    """Bambu Studio's "floating cantilever" test (TreeSupport::detect_overhangs, support off,
    auto type): an overhang region — layer area beyond the layer below grown by
    layer_h / tan(threshold + 1 deg) — whose farthest point lies more than CANTILEVER_REACH from the
    strip where it attaches to the layer below (grown by max(line width, that offset) + 0.1 mm)."""

    grow = layer_h / math.tan(math.radians(SUPPORT_THRESHOLD_ANGLE + 1))
    over = layer.difference(prev.buffer(grow))
    if over.is_empty:
        return []
    attach_zone = prev.buffer(max(LINE_W, grow) + 0.1)
    found: list[Cantilever] = []
    for poly in (list(over.geoms) if hasattr(over, "geoms") else [over]):
        if poly.area < CANTILEVER_MIN_AREA:
            continue
        attach = poly.intersection(attach_zone)
        if attach.is_empty:
            continue  # nothing below at all — that is an island, reported separately
        reach = max(attach.distance(Point(pt)) for pt in poly.exterior.coords)
        if reach > CANTILEVER_REACH:
            found.append(Cantilever(z=z, area=round(poly.area, 1), reach=round(reach, 1),
                                    bounds=tuple(round(b, 1) for b in poly.bounds)))
    return found


def analyse(mesh, layer_h: float = LAYER_H) -> PrintabilityReport:
    """`mesh` is a trimesh.Trimesh already in its print pose (build plate = its lowest Z)."""

    from shapely.ops import unary_union

    z0 = float(mesh.bounds[0][2])
    z1 = float(mesh.bounds[1][2])
    # Slice a hair off the layer-centre grid: OpenSCAD puts whole vertex rings on round heights
    # (e.g. a circle's equator at z = 13.5), and a plane through them yields degenerate, dropped
    # contours — which then make the next layer look unsupported.
    heights = np.arange(layer_h / 2.0, z1 - z0, layer_h) + 0.0137
    report = PrintabilityReport(layers=len(heights))
    sections = mesh.section_multiplane([0.0, 0.0, z0], [0.0, 0.0, 1.0], heights)

    prev = None
    prev2 = None
    for h, sec in zip(heights, sections):
        z = round(float(h), 1)
        if sec is None:
            prev = prev2 = None
            continue
        layer = unary_union(sec.polygons_full).buffer(0)
        if prev is not None and not layer.is_empty:
            regions = list(layer.geoms) if hasattr(layer, "geoms") else [layer]
            # Supported by either of the two layers below — one dropped contour must not turn a
            # region into a false "island".
            below = (prev if prev2 is None else prev.union(prev2)).buffer(0.05)
            for reg in regions:
                if reg.area < ISLAND_MIN_AREA:
                    continue
                if reg.intersection(below).area < ISLAND_SUPPORT_FRAC * reg.area:
                    c = reg.centroid
                    report.islands.append(Island(
                        z=z, area=round(reg.area, 2), centroid=(round(c.x, 1), round(c.y, 1)),
                        bounds=tuple(round(b, 1) for b in reg.bounds),
                    ))
            free = layer.difference(prev.buffer(layer_h))
            if free.area > OVERHANG_REPORT_MIN:
                report.overhangs.append(Overhang(
                    z=z, area=round(free.area, 1), bounds=tuple(round(b, 1) for b in free.bounds),
                ))
            report.cantilevers += _cantilevers(layer, prev, z, layer_h)
        prev2, prev = prev, layer
    return report


def _section_levels(mesh) -> list[float]:
    """Mid-heights of the z-intervals between consecutive vertex heights (the model is prismatic in between)."""

    zs = np.unique(np.round(np.asarray(mesh.vertices)[:, 2] / SEE_THROUGH_Z_MERGE) * SEE_THROUGH_Z_MERGE)
    return [float((a + b) / 2) for a, b in zip(zs[:-1], zs[1:]) if b - a > 1.5 * SEE_THROUGH_Z_MERGE]


def non_prismatic_see_through(mesh) -> list[SeeThrough]:
    """Openings you can see through along Z that are not one cut. `mesh` is a trimesh.Trimesh in print pose.

    A drawn opening (a through-hole, also one with a counterbore; a vent slot) is bounded by material all
    round at some height. An accidental one, made by two features overlapping in plan, is bounded by an arc
    of one and a chord of the other and by material at no height. The see-through region is the intersection
    of the void regions of all slices; each connected piece of it must coincide with one connected void of at
    least one slice. Returns the pieces that do not."""

    from shapely.ops import unary_union

    z0 = float(mesh.bounds[0][2])
    levels = _section_levels(mesh)
    if not levels:
        return []
    sections = mesh.section_multiplane([0.0, 0.0, z0], [0.0, 0.0, 1.0], [z - z0 for z in levels])
    mats = [unary_union(sec.polygons_full).buffer(0) if sec is not None else Polygon() for sec in sections]
    outline = unary_union([Polygon(p.exterior) for m in mats for p in (m.geoms if hasattr(m, "geoms") else [m])
                           if not p.is_empty])
    voids = [outline.difference(m).buffer(0) for m in mats]
    see_through = voids[0]
    for v in voids[1:]:
        see_through = see_through.intersection(v)
    found: list[SeeThrough] = []
    for comp in (see_through.geoms if hasattr(see_through, "geoms") else [see_through]):
        if comp.is_empty or comp.area < SEE_THROUGH_MIN_AREA:
            continue
        if any(g.symmetric_difference(comp).area <= SEE_THROUGH_SAME_AREA
               for v in voids for g in (v.geoms if hasattr(v, "geoms") else [v])):
            continue
        c = comp.centroid
        found.append(SeeThrough(area=round(comp.area, 2), centroid=(round(c.x, 1), round(c.y, 1))))
    return found


def selftest_see_through() -> list[str]:
    """[] when non_prismatic_see_through() flags a synthetic lid whose groove crosses the counterbore and
    passes one whose groove does not, else the problems. Print pose: 3 mm slab on z = 0, through-hole
    d 3.4, counterbore d 8 x 1.5 from the bed, groove 2.1 wide x 2 deep from the top."""

    import trimesh

    def lid(groove_y: float):
        slab = trimesh.creation.box(extents=(40.0, 30.0, 3.0))
        slab.apply_translation((0.0, 0.0, 1.5))
        hole = trimesh.creation.cylinder(radius=1.7, height=6.0, sections=64)
        hole.apply_translation((0.0, 0.0, 1.5))
        cbore = trimesh.creation.cylinder(radius=4.0, height=2.5, sections=64)
        cbore.apply_translation((0.0, 0.0, 0.25))
        groove = trimesh.creation.box(extents=(50.0, 2.1, 3.0))
        groove.apply_translation((0.0, groove_y, 2.5))
        return trimesh.boolean.difference([slab, hole, cbore, groove], engine="manifold")

    problems = []
    broken = non_prismatic_see_through(lid(2.8))
    if len(broken) != 1:
        problems.append(f"groove crossing the counterbore: expected 1 opening, found {len(broken)}")
    fine = non_prismatic_see_through(lid(6.0))
    if fine:
        problems.append(f"groove clear of the counterbore: expected none, found {len(fine)}")
    return problems
