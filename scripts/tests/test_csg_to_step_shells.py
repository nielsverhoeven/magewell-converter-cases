"""csg_to_step.drop_empty_shells / shell_defects (issue #119, D119.1): a SOLID in an exported STEP
carries only closed shells that enclose material."""
from __future__ import annotations

import csg_to_step as c
from OCP.BRep import BRep_Builder
from OCP.BRepBuilderAPI import BRepBuilderAPI_MakeSolid
from OCP.BRepGProp import BRepGProp
from OCP.BRepPrimAPI import BRepPrimAPI_MakeBox
from OCP.GProp import GProp_GProps
from OCP.gp import gp_Pnt
from OCP.TopAbs import TopAbs_SHELL
from OCP.TopExp import TopExp_Explorer
from OCP.TopoDS import TopoDS, TopoDS_Shell


def _shells(shape):
    out, exp = [], TopExp_Explorer(shape, TopAbs_SHELL)
    while exp.More():
        out.append(TopoDS.Shell(exp.Current()))
        exp.Next()
    return out


def _box_shell(x0, size):
    return _shells(BRepPrimAPI_MakeBox(gp_Pnt(x0, 0, 0), size, size, size).Shape())[0]


def _sheet_shell():
    """A closed zero-thickness shell: one square face and the same face reversed, as the pairwise
    fuse leaves it under a boss standing on the floor."""
    face = c._first_face(BRepPrimAPI_MakeBox(gp_Pnt(2, 2, 3), 4, 4, 1).Shape())
    shell, builder = TopoDS_Shell(), BRep_Builder()
    builder.MakeShell(shell)
    builder.Add(shell, face)
    builder.Add(shell, face.Reversed())
    return shell


def _solid(*shells):
    mk = BRepBuilderAPI_MakeSolid()
    for shell in shells:
        mk.Add(shell)
    return mk.Solid()


def _volume(shape):
    props = GProp_GProps()
    BRepGProp.VolumeProperties_s(shape, props)
    return props.Mass()


def test_empty_sheet_shell_is_dropped_and_volume_kept():
    solid = _solid(_box_shell(0, 10), _sheet_shell())
    assert len(_shells(solid)) == 2
    assert c.shell_defects(solid) == ["empty shell"]
    fixed, dropped = c.drop_empty_shells(solid)
    assert dropped == 1
    assert len(_shells(fixed)) == 1
    assert abs(_volume(fixed) - 1000.0) < 1e-6
    assert c.shell_defects(fixed) == []


def test_real_shells_are_kept():
    solid = _solid(_box_shell(0, 10), _box_shell(20, 5))
    fixed, dropped = c.drop_empty_shells(solid)
    assert dropped == 0
    assert len(_shells(fixed)) == 2
    assert c.shell_defects(fixed) == []


def test_zero_area_face_is_a_defect():
    from OCP.BRepBuilderAPI import BRepBuilderAPI_MakeFace
    from OCP.gp import gp_Pln
    tiny = BRepBuilderAPI_MakeFace(gp_Pln(), 0.0, 1e-5, 0.0, 1e-5).Face()
    assert c.shell_defects(tiny) == ["zero-area face"]
    assert c.shell_defects(_solid(_box_shell(0, 10))) == []
