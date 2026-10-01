"""SH1: the S1 blocks of ``shared/tg.py`` (issue #81, plan 5.3 and 7): ``tongue`` and ``groove``.

Every block is built through the facade on the recording backend, checked by the plan checks, replayed with OpenCascade and
compared with its K4a oracle fixture and a fresh oracle mesh (corners within 0.02 mm; no residual piece both above 0.5 mm3 and
thicker than 0.05 mm; the residual at most 0.2 % of the part).  These tests never skip: where OpenSCAD is missing,
``oracle.require_openscad()`` fails them when ``MCC_REQUIRE_OPENSCAD=1`` (CI) and skips them only on a developer machine.
"""
from __future__ import annotations

import pytest

from cad.fusion.gen.core import expr
from cad.fusion.gen.shared import tg
from cad.fusion.gen.tests import oracle, s1_support

BLOCKS = ("tongue", "groove")
RECT = ("x0", "x1", "y0", "y1")


@pytest.fixture(scope="module")
def work(tmp_path_factory):
    return tmp_path_factory.mktemp("s1_tg")


def tg_calls() -> list:
    record, _, _ = s1_support.build_record()
    return [c for c in record["shared_calls"] if c["builder_id"].startswith("tg.")]


def test_the_plan_checks_find_nothing():
    assert [str(f) for f in s1_support.findings()] == []


def test_each_block_is_one_recorded_call_of_its_builder():
    tongue, groove = tg_calls()
    assert (tongue["builder_id"], groove["builder_id"]) == ("tg.tongue", "tg.groove")
    assert tongue["placement"] == groove["placement"] == ["x0", "x1", "y0", "y1", "z"]
    assert tongue["produced"] == ["Block_Tongue_RingAdd", "Block_Tongue_RingAddSk"]
    assert groove["produced"] == ["Block_Groove_RingCut", "Block_Groove_RingCutSk"]
    assert tongue["parent"] is None and groove["parent"] is None
    for call in (tongue, groove):  # the instance name is positional and never an argument (CK10 would compare it)
        assert "name" not in call["arguments"] and "set_name" not in call["arguments"]


def test_the_tongue_and_the_groove_take_the_same_four_rectangle_expressions():
    tongue, groove = tg_calls()
    assert {k: tongue["arguments"][k] for k in RECT} == {k: groove["arguments"][k] for k in RECT}
    assert tongue["arguments"]["width"] == groove["arguments"]["width"] == "MCC_TG_W"
    assert groove["arguments"]["clearance"] == "MCC_CLR_TG"


def test_a_ring_is_the_closed_form_volume():
    # tongue: ring 1.6 wide around a 54 x 34 rectangle, 2 high; groove: the same ring grown by the 0.25 clearance
    # (1.85 outside, 0.25 inside), 2 deep
    tongue = s1_support.block_features("tongue")["Block_Tongue_RingAdd"]
    groove = s1_support.block_features("groove")["Block_Groove_RingCut"]
    assert tongue == pytest.approx(((54 + 3.2) * (34 + 3.2) - 54 * 34) * 2, rel=1e-9)
    assert groove == pytest.approx(-((54 + 3.7) * (34 + 3.7) - (54 - 0.5) * (34 - 0.5)) * 2, rel=1e-9)


def test_a_dimension_that_is_a_number_or_a_literal_is_refused():
    kit = s1_support.new_kit()
    comp = kit.component("S1_Tongue", role="part", datum=(None, None, None))
    comp.extrude("Block_Tongue_Body", axis="Z", loops=[comp.rect(None, "T_TG_L", None, "T_TG_W")], start=None, end="T_TG_PLATE",
                 op="new")
    rect = dict(x0="MCC_WALL", x1="T_TG_L - MCC_WALL", y0="MCC_WALL", y1="T_TG_W - MCC_WALL", z="T_TG_PLATE", height="MCC_TG_H")
    with pytest.raises(expr.LiteralError):
        tg.tongue(comp, "Block_Tongue_RingAdd", width="1.6 mm", **rect)
    with pytest.raises(TypeError):
        tg.tongue(comp, "Block_Tongue_RingAdd", width=1.6, **rect)


@pytest.mark.parametrize("block", BLOCKS)
def test_a_block_replays_to_its_oracle(block, work):
    oracle.require_openscad()
    run = s1_support.run_block(block, work)
    assert s1_support.gate_problems(run) == []
    assert run.report["residual"]["counted_rel"] == 0.0  # rectangles only: the two meshes are the same solid
