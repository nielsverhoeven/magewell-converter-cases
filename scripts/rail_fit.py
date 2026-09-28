#!/usr/bin/env python3
"""Virtual insertion sweep: slide the male mount rail into a rendered case base and report where
they overlap (issue #46, architecture.md §13 D34 — the check that would have caught a groove closed
at both ends).

    python scripts/rail_fit.py [<case-slug>]          # default: pro-convert-for-ndi-to-hdmi

Renders mcc_rail_male() (no plate) with the pinned OpenSCAD, loads
exports/<slug>/base.model.stl (run `build.py render <slug> --part base` first) and, for a set of
insertion offsets dx (male shifted +X, i.e. not yet fully in), intersects the two over the WHOLE
base: since D44 the male's frame is the groove's (no pedestal) and the roof, like the flanks, keeps
>= MCC_RAIL_MATE_CLR -- any contact at full mate is a failure. Expected, and asserted:
  dx < 0  overlap > 0   (the groove's closed -X end stops over-travel)
  dx = 0  overlap = 0   (fully mated: nub sits in its notch with clearance)
  dx > 0  overlap only inside the nub's own X span (the arm deflects; nothing else collides)
Exit code 0 when all hold.
"""

from __future__ import annotations

import math
import re
import sys
import tempfile
from pathlib import Path

import trimesh

import build


def _const(name: str) -> float:
    text = (build.LIB_DIR / "mcc" / "constants.scad").read_text(encoding="utf-8")
    return float(re.search(rf"^{name}\s*=\s*([-\d.]+)", text, re.M).group(1))


def nub_span() -> tuple[float, float]:
    """The nub's X span in the male frame — same formula as rail.scad _mcc_rail_latch_geom()."""
    e = _const("MCC_RAIL_LATCH_ENGAGE")
    nub_l = (e / math.tan(math.radians(_const("MCC_RAIL_LATCH_RAMP_IN"))) + _const("MCC_RAIL_LATCH_FLAT")
             + e / math.tan(math.radians(_const("MCC_RAIL_LATCH_RAMP_OUT"))))
    xc = _const("MCC_RAIL_LEN") / 2 - _const("MCC_RAIL_LATCH_LEAD_IN")
    return xc - nub_l / 2, xc + nub_l / 2


def main(argv: list[str]) -> int:
    slug = argv[0] if argv else "pro-convert-for-ndi-to-hdmi"
    base_path = build.EXPORTS_DIR / slug / "base.model.stl"
    if not base_path.is_file():
        print(f"error: {base_path} missing — run `build.py render {slug} --part base` first")
        return 1
    with tempfile.TemporaryDirectory(prefix="mcc_railfit_") as t:
        scad = Path(t) / "male.scad"
        scad.write_text("include <mcc/mcc.scad>\nmcc_rail_male();\n", encoding="utf-8")
        stl = Path(t) / "male.stl"
        ok, _ = build.run_openscad(build.find_openscad(), scad, {}, [stl], None)
        if not ok:
            return 1
        male = trimesh.load(str(stl), force="mesh")
    base = trimesh.load(str(base_path), force="mesh")
    rail_y = _const("MCC_RAIL_Y")
    bad = []
    n0, n1 = nub_span()
    for dx in (-0.5, 0.0, 1.0, 5.0, 20.0, 40.0, 80.0, 140.0):
        m = male.copy()
        m.apply_translation([dx, rail_y, 0.0])
        inter = trimesh.boolean.intersection([m, base], engine="manifold")
        v = float(inter.volume) if inter is not None and len(inter.faces) else 0.0
        span = (float(inter.bounds[0][0]) - dx, float(inter.bounds[1][0]) - dx) if v > 1e-3 else None
        print(f"dx={dx:6.1f}  overlap={v:8.3f} mm3" + (f"  male x {span[0]:.1f}..{span[1]:.1f}" if span else ""))
        if dx < 0 and v <= 1e-3:
            bad.append("no end stop: over-travel does not collide")
        if dx == 0 and v > 1e-2:
            bad.append(f"fully mated but overlapping {v:.3f} mm3")
        if dx > 0 and span and (span[0] < n0 - 0.5 or span[1] > n1 + 0.5):
            bad.append(f"dx={dx}: overlap outside the nub {n0:.1f}..{n1:.1f} (male x {span[0]:.1f}..{span[1]:.1f})")
    for b in bad:
        print("FAIL:", b)
    print("rail fit OK" if not bad else "rail fit FAILED")
    return 0 if not bad else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
