"""SH1: the decorator ``shared`` of ``cad/fusion/gen/shared/__init__.py`` (plan SH1 step 1, verdict A6).

It opens ``comp.shared_call(builder_id, arguments, placement)`` around a builder, with the keyword arguments of the call as
``arguments`` (the instance name, positional, is never one), runs the builder inside it and returns its result.
"""
from __future__ import annotations

import pytest

from cad.fusion.gen import shared
from cad.fusion.gen.core.names import KitError
from cad.fusion.gen.tests import s1_support


def part():
    kit = s1_support.new_kit()
    comp = kit.component("S1_Tongue", role="part", datum=(None, None, None))
    comp.extrude("Block_Tongue_Body", axis="Z", loops=[comp.rect(None, "T_TG_L", None, "T_TG_W")], start=None, end="T_TG_PLATE",
                 op="new")
    return kit, comp


def calls(kit) -> list:
    return [c.to_json() for c in kit._backend.shared]


def test_the_keyword_arguments_are_the_recorded_arguments_and_the_result_comes_back():
    kit, comp = part()

    @shared.shared("test.cut", placement=("x",))
    def cut(comp, name, *, x, y):
        return comp.extrude(name, axis="Z", loops=[comp.rect(x, y, "MCC_WALL", "T_TG_W")], start=None, end="MCC_WALL", op="cut")

    assert cut(comp, "Block_Test_SlotCut", x="MCC_WALL", y="T_TG_L - MCC_WALL") == "Block_Test_SlotCut"
    (call,) = calls(kit)
    assert call["builder_id"] == "test.cut" and call["placement"] == ["x"]
    assert call["arguments"] == {"x": "MCC_WALL", "y": "T_TG_L - MCC_WALL"}
    assert call["produced"] == ["Block_Test_SlotCut", "Block_Test_SlotCutSk"]
    assert cut.__name__ == "cut"


def test_the_instance_name_is_never_an_argument_even_when_it_is_passed_by_keyword():
    kit, comp = part()

    @shared.shared("test.cut")
    def cut(comp, name, *, x):
        return comp.extrude(name, axis="Z", loops=[comp.rect(x, "T_TG_L", "MCC_WALL", "T_TG_W")], start=None, end="MCC_WALL", op="cut")

    cut(comp, name="Block_Test_SlotCut", x="MCC_WALL")
    assert calls(kit)[0]["arguments"] == {"x": "MCC_WALL"}


def test_a_placement_argument_the_call_does_not_pass_is_an_error():
    kit, comp = part()

    @shared.shared("test.cut", placement=("x", "z"))
    def cut(comp, name, *, x):
        raise AssertionError("not reached")

    with pytest.raises(KitError, match="placement argument 'z'"):
        cut(comp, "Block_Test_SlotCut", x="MCC_WALL")


def test_a_builder_called_inside_another_records_its_parent():
    kit, comp = part()

    @shared.shared("test.inner")
    def inner(comp, name):
        return comp.extrude(name, axis="Z", loops=[comp.rect("MCC_WALL", "T_TG_L", "MCC_WALL", "T_TG_W")], start=None,
                            end="MCC_WALL", op="cut")

    @shared.shared("test.outer")
    def outer(comp, name):
        return inner(comp, name)

    outer(comp, "Block_Test_SlotCut")
    assert [(c["builder_id"], c["parent"]) for c in calls(kit)] == [("test.outer", None), ("test.inner", "test.outer")]
    assert [c["produced"] for c in calls(kit)] == [[], ["Block_Test_SlotCut", "Block_Test_SlotCutSk"]]
