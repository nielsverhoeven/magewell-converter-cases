"""Self-tests of scripts/parity.py (issue #80). Synthetic parts only: no OpenSCAD, no Fusion, no exports/.

    python -m pytest scripts/tests/test_parity.py -q

The four tests the architect names: identical parts pass, a part without one vent slot fails, a 0.1 mm shift
fails, a polygon against a true circle passes. The others pin the decisions around them.
"""

from __future__ import annotations

import contextlib
import io
import json
import math
import tempfile
from pathlib import Path

import numpy as np

import manifold3d as m3d
import trimesh

import parity

SLOT_XS = (-40.0, -25.0, -10.0, 5.0, 20.0, 35.0, 48.0)      # seven vent slots 12 x 2 mm through the 10 mm plate


def to_trimesh(mf: "m3d.Manifold") -> "trimesh.Trimesh":
    mm = mf.to_mesh()
    return trimesh.Trimesh(np.asarray(mm.vert_properties)[:, :3].astype(float), np.asarray(mm.tri_verts), process=True)


def cylinder(r: float, segments: int, z0: float = -1.0, h: float = 12.0, circum: bool = False, at=(0.0, 0.0)) -> "m3d.Manifold":
    radius = r / math.cos(math.pi / segments) if circum else r
    return m3d.Manifold.cylinder(h, radius, radius, segments).translate((at[0], at[1], z0))


def plate(slots: int = 7, hole_segments: int = 64, circum: bool = True, hole_r: float = 12.1,
          pocket: bool = False) -> "trimesh.Trimesh":
    """100 x 60 x 10 mm plate, `slots` vent slots, one round hole; optional 0.6 mm deep label pocket on the top face."""
    body = m3d.Manifold.cube((100.0, 60.0, 10.0), center=False).translate((-50.0, -30.0, 0.0))
    for x in SLOT_XS[:slots]:
        body = body - m3d.Manifold.cube((2.0, 12.0, 12.0)).translate((x - 1.0, -20.0 - 6.0, -1.0))
    body = body - cylinder(hole_r, hole_segments, circum=circum, at=(-20.0, 15.0))
    if pocket:
        body = body - m3d.Manifold.cube((8.0, 4.0, 0.7)).translate((20.0, 18.0, 9.4))
    return to_trimesh(body)


def disc(r: float = 20.0, segments: int = 64, circum: bool = True, h: float = 6.0) -> "trimesh.Trimesh":
    return to_trimesh(cylinder(r, segments, z0=0.0, h=h, circum=circum))


def verdict(report: dict) -> str:
    return report["verdict"]["status"]


def test_identical_parts_pass():
    p = plate()
    report, _ = parity.compare_meshes(p.copy(), p.copy(), name="identical", samples=500)
    assert verdict(report) == "pass", report["verdict"]
    assert report["residual"]["counted_volume_mm3"] == 0.0
    assert report["residual"]["regions_total"] == 0


def test_missing_vent_slot_fails_and_is_localised():
    oracle, cand = plate(slots=7), plate(slots=6)            # the candidate did not cut the seventh slot
    report, _ = parity.compare_meshes(cand, oracle, name="one slot missing", samples=500)
    assert verdict(report) == "fail"
    assert report["residual"]["regions_total"] == 1
    region = report["residual"]["regions"][0]
    assert region["side"] == "extra"                          # the candidate keeps material the oracle has cut away
    assert abs(region["volume_mm3"] - 2.0 * 12.0 * 10.0) < 0.5
    x = SLOT_XS[6]
    assert region["bbox_min"][0] <= x - 0.9 and region["bbox_max"][0] >= x + 0.9
    assert report["verdict"]["failures"]


def test_shift_of_a_tenth_of_a_millimetre_fails():
    oracle = plate()
    cand = oracle.copy()
    cand.apply_translation([0.1, 0.0, 0.0])
    report, _ = parity.compare_meshes(cand, oracle, name="shifted", samples=500)
    assert verdict(report) == "fail"
    failed = [c["name"] for c in report["checks"] if not c["ok"]]
    assert "corner_min_x" in failed and "corner_max_x" in failed
    assert any("shifted by" in h for h in report["frame_hints"])          # the size is equal, only the origin moved
    assert report["residual"]["regions_total"] >= 1                       # the shift also shows as residual sheets on the faces


def test_polygon_against_true_circle_passes():
    oracle = plate(hole_segments=64, circum=True)
    cand = plate(hole_segments=1440, circum=False)              # a true circle at the nominal radius
    report, _ = parity.compare_meshes(cand, oracle, name="polygon vs circle", samples=500)
    assert verdict(report) == "pass", report["verdict"]
    sub = report["residual"]["sub_threshold"]
    ring = sub["extra"]["large_but_thin"] + sub["missing"]["large_but_thin"]
    assert ring == 1                                          # the ring around the hole is one piece of 3.7 mm3: larger than 0.5 mm3, but thin
    assert max(sub["extra"]["max_thickness_mm"], sub["missing"]["max_thickness_mm"]) < 0.02
    assert report["residual"]["regions_total"] == 0


def test_circumscribed_disc_needs_the_exact_frame():
    oracle = disc(20.0, 64, circum=True)       # OpenSCAD circumscribes: its bounding box overshoots the circle
    cand = disc(20.0, 1440, circum=False)
    overshoot = 20.0 / math.cos(math.pi / 64) - 20.0
    assert 0.02 < overshoot < 0.03
    by_mesh, _ = parity.compare_meshes(cand, oracle, name="mesh frame", samples=0)
    assert verdict(by_mesh) == "fail" and any(c["name"].startswith("corner") and not c["ok"] for c in by_mesh["checks"])
    exact = parity._box_metrics([-20.0, -20.0, 0.0], [20.0, 20.0, 6.0])
    by_brep, _ = parity.compare_meshes(cand, oracle, name="exact frame", samples=0, frame_c=exact, frame_o=exact)
    assert verdict(by_brep) == "pass", by_brep["verdict"]


def test_mesh_against_its_own_tessellation_uses_the_piece_criterion_only():
    coarse, fine = plate(hole_segments=48, circum=False), plate(hole_segments=1440, circum=False)
    report, _ = parity.compare_meshes(coarse, fine, name="own step", samples=0, mode="pieces")
    assert report["checks"] == []
    assert verdict(report) == "pass", report["verdict"]


def test_unit_and_axis_hints():
    oracle = plate()
    small = oracle.copy()
    small.apply_scale(0.1)
    report, _ = parity.compare_meshes(small, oracle, name="cm", samples=0)
    assert any("10 times smaller" in h for h in report["frame_hints"])
    swapped = oracle.copy()
    swapped.apply_transform(trimesh.transformations.rotation_matrix(math.pi / 2, [1, 0, 0]))          # Y-up: y and z swap roles
    report, _ = parity.compare_meshes(swapped, oracle, name="y-up", samples=0)
    assert any("permuted" in h for h in report["frame_hints"])


def test_label_mask_hides_glyph_pockets_only():
    oracle, cand = plate(pocket=True), plate(pocket=False)       # the candidate has no label engraving
    plain, _ = parity.compare_meshes(cand, oracle, name="no mask", samples=0)
    assert verdict(plain) == "fail"                              # 8 x 4 x 0.7 = 22 mm3, 0.7 mm thick
    box = (np.array([18.0, 17.0, 9.0]), np.array([32.0, 23.0, 10.5]))
    masked, _ = parity.compare_meshes(cand, oracle, name="mask", samples=0, masks=[box])
    assert verdict(masked) == "pass", masked["verdict"]
    assert masked["residual"]["sub_threshold"]["extra"]["masked_pieces"] + masked["residual"]["sub_threshold"]["missing"]["masked_pieces"] == 1
    far = (np.array([-50.0, -30.0, 0.0]), np.array([-40.0, -20.0, 1.0]))      # a mask elsewhere hides nothing
    not_hidden, _ = parity.compare_meshes(cand, oracle, name="far mask", samples=0, masks=[far])
    assert verdict(not_hidden) == "fail"


def test_open_mesh_is_an_error_not_a_verdict():
    p = plate()
    holed = trimesh.Trimesh(p.vertices, p.faces[:-1], process=False)
    try:
        parity.compare_meshes(holed, p, name="open", samples=0)
    except parity.ParityError as exc:
        assert "watertight" in str(exc)
    else:
        raise AssertionError("an open mesh must raise ParityError")


def test_golden_mode_uses_the_golden_tolerances():
    p = plate()
    golden = {"bbox": {"min": p.bounds[0].tolist(), "max": p.bounds[1].tolist(), "size": (p.bounds[1] - p.bounds[0]).tolist()},
              "volume_mm3": float(p.volume), "area_mm2": float(p.area), "facets": int(len(p.faces))}
    ok, _ = parity.compare_meshes(p.copy(), p.copy(), name="golden ok", samples=0, golden=golden)
    assert verdict(ok) == "pass"
    golden["volume_mm3"] *= 1.006                                  # 0.6 % > 0.5 %
    bad, _ = parity.compare_meshes(p.copy(), p.copy(), name="golden volume", samples=0, golden=golden)
    assert verdict(bad) == "fail" and any(c["name"] == "golden_volume_mm3" and not c["ok"] for c in bad["checks"])


def test_golden_constants_equal_build_py():
    import build                                                   # scripts/build.py
    assert parity.GOLDEN_BBOX_MM == build.GOLDEN_BBOX_TOL_MM
    assert parity.GOLDEN_VOLUME_REL == build.GOLDEN_VOLUME_TOL
    assert parity.GOLDEN_AREA_REL == build.GOLDEN_AREA_TOL


def test_report_is_compact_json_with_regions_not_noise():
    oracle, cand = plate(slots=7), plate(slots=6)
    report, parts = parity.compare_meshes(cand, oracle, name="json", samples=200)
    with tempfile.TemporaryDirectory() as t:
        path = parity.write_report(report, Path(t), "parity-json")
        text = path.read_text(encoding="utf-8")
        data = json.loads(text)
    assert data["schema"] == parity.SCHEMA and "_regions_full" not in data
    assert len(text.splitlines()) < 400                              # short lists stay on one line
    assert data["residual"]["regions"][0]["volume_mm3"] > 200


def test_release_diff_from_directory():
    from OCP.BRepPrimAPI import BRepPrimAPI_MakeBox
    from OCP.IFSelect import IFSelect_RetDone
    from OCP.STEPControl import STEPControl_AsIs, STEPControl_Writer
    with tempfile.TemporaryDirectory() as t:
        root = Path(t)
        (root / "exports" / "demo").mkdir(parents=True)
        box = trimesh.creation.box(extents=(20.0, 10.0, 5.0))
        box.apply_translation([10.0, 5.0, 2.5])
        box.export(str(root / "exports" / "demo" / "base.model.stl"))
        (root / "release").mkdir()
        w = STEPControl_Writer()
        w.Transfer(BRepPrimAPI_MakeBox(20.0, 10.0, 5.0).Shape(), STEPControl_AsIs)
        assert w.Write(str(root / "release" / "demo-base.step")) == IFSelect_RetDone
        for tree in parity.NON_ORACLE_TREES:                        # files of the other trees under exports/ are not oracle parts
            (root / "exports" / tree / "Doc" / "t").mkdir(parents=True)
            box.export(str(root / "exports" / tree / "Doc" / "t" / "p.model.stl"))
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            rc = parity.main(["release-diff", "--exports", str(root / "exports"), "--from-dir", str(root / "release"), "--fail-on-change"])
        assert rc == 0 and "1 of 1" not in out.getvalue() and "0 of 1 part(s) changed" in out.getvalue()
        assert not any(tree in out.getvalue() for tree in parity.NON_ORACLE_TREES)
    assert "builder-replay" in parity.NON_ORACLE_TREES


def shells_of(shape) -> list:
    from OCP.TopAbs import TopAbs_SHELL
    from OCP.TopoDS import TopoDS
    return parity._shapes(shape, TopAbs_SHELL, TopoDS.Shell)


def write_step(shape, path: Path) -> None:
    from OCP.IFSelect import IFSelect_RetDone
    from OCP.STEPControl import STEPControl_AsIs, STEPControl_Writer
    w = STEPControl_Writer()
    w.Transfer(shape, STEPControl_AsIs)
    assert w.Write(str(path)) == IFSelect_RetDone


def test_zero_volume_shells_are_dropped_before_the_mesh_is_built():
    from OCP.BRepBuilderAPI import BRepBuilderAPI_MakeSolid
    from OCP.BRepPrimAPI import BRepPrimAPI_MakeBox
    from OCP.gp import gp_Pnt
    outer = shells_of(BRepPrimAPI_MakeBox(gp_Pnt(0, 0, 0), 20.0, 20.0, 10.0).Shape())[0]
    tiny = shells_of(BRepPrimAPI_MakeBox(gp_Pnt(5, 5, 5), 0.1, 0.1, 0.1).Shape())[0]       # 0.001 mm3: below DEGENERATE_SHELL_MM3
    maker = BRepBuilderAPI_MakeSolid()
    maker.Add(outer)
    maker.Add(tiny)
    solid = maker.Solid()
    kept, void = parity.solid_shells(solid)
    assert len(kept) == 1 and len(void) == 1
    clean, dropped = parity.drop_void_shells(solid)
    assert dropped == 1 and len(shells_of(clean)) == 1
    same, none = parity.drop_void_shells(BRepPrimAPI_MakeBox(gp_Pnt(0, 0, 0), 20.0, 20.0, 10.0).Shape())
    assert none == 0 and len(shells_of(same)) == 1                     # a clean shape passes unchanged
    with tempfile.TemporaryDirectory() as t:
        path = Path(t) / "void.step"
        write_step(solid, path)
        mesh = parity.mesh_from_step(path)
        assert mesh.metadata["void_shells_dropped"] == 1 and mesh.is_watertight
        assert abs(mesh.area - 1600.0) < 1e-6 and abs(mesh.volume - 4000.0) < 1e-6          # the box, nothing of the void shell
        raw = parity.mesh_from_step(path, drop_void=False)
        assert abs(raw.area - 1600.06) < 1e-6                                              # with it, its six faces are in the mesh
        report, _ = parity.compare_meshes(mesh, mesh.copy(), name="void", samples=0)
        assert report["candidate"]["void_shells_dropped"] == 1 and report["oracle"]["void_shells_dropped"] == 1


def test_zero_area_triangles_are_dropped_before_the_comparison():
    p = plate()
    a, b = p.edges[0]                                            # an edge of the solid
    mid = (p.vertices[a] + p.vertices[b]) / 2.0
    verts = np.vstack([p.vertices, mid])
    faces = np.vstack([p.faces, [a, b, len(p.vertices)]])         # a sliver on the edge: the edge now belongs to three faces
    sliver = trimesh.Trimesh(verts, faces, process=False)
    assert not sliver.is_watertight                                # what trimesh says about a sound solid with the sliver
    report, _ = parity.compare_meshes(sliver, p.copy(), name="sliver", samples=0)
    assert verdict(report) == "pass", report["verdict"]
    assert report["candidate"]["dropped_degenerate_faces"] == 1 and report["oracle"]["dropped_degenerate_faces"] == 0


def test_a_zero_area_triangle_that_closes_a_t_junction_is_kept():
    box = trimesh.creation.box(extents=(10.0, 10.0, 10.0))
    verts, faces = box.vertices.copy(), box.faces.copy()
    edge = None
    for i, tri in enumerate(faces):                                   # a triangle of the top face, one of its edges shared with a side face
        if np.allclose(verts[tri][:, 2], 5.0):
            edge = (i, tri)
            break
    i, (a, b, c) = edge
    verts = np.vstack([verts, (verts[a] + verts[b]) / 2.0])            # m: the midpoint of the edge a-b
    m = len(verts) - 1
    split = np.vstack([np.delete(faces, i, axis=0), [a, m, c], [m, b, c], [a, b, m]])   # (a, m, c) and (m, b, c) replace (a, b, c); (a, b, m) has zero area and closes a-b
    mesh = trimesh.Trimesh(verts, split, process=False)
    assert mesh.is_watertight and mesh.is_winding_consistent and (mesh.area_faces < parity.DEGENERATE_AREA_MM2).sum() == 1
    cleaned, dropped = parity.clean_mesh(mesh)
    assert dropped == 0 and cleaned is mesh                            # dropping the sliver would open the T-junction
    report, _ = parity.compare_meshes(mesh.copy(), box.copy(), name="t-junction", samples=0)
    assert verdict(report) == "pass", report["verdict"]
    assert report["candidate"]["dropped_degenerate_faces"] == 0


def test_positional_command_line_is_compare():
    p = plate()
    with tempfile.TemporaryDirectory() as t:
        a, b = Path(t) / "a.stl", Path(t) / "b.stl"
        p.export(str(a))
        p.export(str(b))
        assert parity.main([str(a), str(b)]) == 0
        shifted = p.copy()
        shifted.apply_translation([0.5, 0.0, 0.0])
        shifted.export(str(b))
        assert parity.main([str(a), str(b)]) == 1

