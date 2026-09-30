"""cad.numeric: OpenSCAD semantics the solver relies on (offline tests + one live check against OpenSCAD)."""
from __future__ import annotations

import math

import pytest

from cad import numeric as N


def test_degree_trig_is_exact_at_the_special_angles_openscad_returns_exactly():
    assert N.sin_deg(30) == 0.5 and N.sin_deg(150) == 0.5 and N.sin_deg(-30) == -0.5
    assert N.cos_deg(60) == 0.5 and N.cos_deg(120) == -0.5 and N.cos_deg(90) == 0.0
    assert N.sin_deg(90) == 1.0 and N.sin_deg(270) == -1.0 and N.sin_deg(390) == 0.5
    assert N.tan_deg(45) == 1.0 and N.tan_deg(135) == -1.0 and N.tan_deg(180) == 0.0
    assert N.tan_deg(90) == math.inf and N.tan_deg(270) == -math.inf


def test_degree_trig_elsewhere_is_the_libm_value():
    assert N.sin_deg(17) == math.sin(math.radians(17))
    assert N.tan_deg(60) == pytest.approx(math.sqrt(3), rel=1e-15)


def test_round_half_away_from_zero_not_bankers():
    assert [N.round_half_away(x) for x in (0.5, 1.5, 2.5, -0.5, -2.5)] == [1, 2, 3, -1, -3]
    assert N.round_half_away(0.49999999999999994) == 1     # floor(|x| + 0.5), as OpenSCAD (C round() says 0)
    assert N.round_half_away(-0.49999999999999994) == -1 and N.round_half_away(0.1) == 0
    assert round(2.5) == 2  # the Python behaviour the port must NOT use


def test_fmod_takes_the_sign_of_the_dividend():
    assert N.fmod(-7, 3) == -1 and N.fmod(7, -3) == 1 and N.fmod(7.5, 2) == 1.5
    assert (-7) % 3 == 2  # the Python behaviour the port must NOT use


def test_floor_ceil_return_floats():
    assert N.floor_(-0.5) == -1.0 and isinstance(N.floor_(2.7), float)
    assert N.ceil_(-0.5) == 0.0 and N.ceil_(2.1) == 3.0


def test_search_and_struct_val_match_bosl2_first_match_semantics():
    table = [["bnc", 41], ["hdmi_a", 40], ["bnc", 99]]
    assert N.search_index("bnc", table) == 0 and N.search_index("x", table) is None
    assert N.struct_val(table, "hdmi_a") == 40 and N.struct_val(table, "x", -1) == -1


def test_sort_lex_is_lexicographic_ascending_and_stable():
    rows = [[-10, -25, 16, 0], [-15, -35, -16, 1], [-10, -25, 16, 2], [-10, -25, -16, 3]]
    out = N.sort_lex(rows, idx=[0, 1, 2])
    assert [r[3] for r in out] == [1, 3, 0, 2]  # equal keys (0 and 2) keep input order


def test_max_min_refuse_empty_lists():
    with pytest.raises(ValueError):
        N.max_of([])
    with pytest.raises(ValueError):
        N.min_of([])
    assert N.max_of([3, 1, 2]) == 3 and N.min_of([3, 1, 2]) == 1


def test_fmt_num_is_stable_and_trims():
    assert N.fmt_num(193.9) == "193.9" and N.fmt_num(3.0) == "3" and N.fmt_num(-0.0) == "0"
    assert N.fmt_num(41.96666666666667) == "41.966666667"


@pytest.mark.openscad
def test_numeric_semantics_equal_openscad(openscad_exe):
    """Live (S0): round/fmod/floor/ceil equal OpenSCAD exactly; degree trig within 1e-15 (sin, cos) and 5e-14 relative (tan)."""
    from cad.tools import openscad_runner as osr

    xs = [0.5, 1.5, 2.5, -0.5, -1.5, -2.5, 0.49999999999999994, 7.25, -7.25, 1e6 + 0.5]
    angles = [float(a) for a in range(-400, 761, 7)] + [17.7, 29.9, 60.1, 333.3]
    lines = [osr.ENCODER_SCAD]
    lines += [f'echo("R", {i}, oracle_enc([round({x!r}), floor({x!r}), ceil({x!r}), {x!r} % 3, {x!r} % -3]));'
              for i, x in enumerate(xs)]
    lines += [f'echo("T", {i}, oracle_enc([sin({a!r}), cos({a!r}), tan({a!r})])); ' for i, a in enumerate(angles)]
    res = osr.run_harness("\n".join(lines) + "\n", exe=openscad_exe)
    assert res.ok, res.errors
    for i, vals in res.tagged("R"):
        x = xs[i]
        got = osr.decode(vals)
        want = [N.round_half_away(x), N.floor_(x), N.ceil_(x), N.fmod(x, 3), N.fmod(x, -3)]
        assert got == want, (x, got, want)
    for i, vals in res.tagged("T"):
        a = angles[i]
        s, c, t = osr.decode(vals)
        assert abs(N.sin_deg(a) - s) <= 1e-15, a
        assert abs(N.cos_deg(a) - c) <= 1e-15, a
        if math.isfinite(t):   # 1 ulp of the argument is amplified by 1/cos^2 near a pole: measured worst 2.7e-14
            assert N.tan_deg(a) == pytest.approx(t, rel=5e-14), a
