#!/usr/bin/env python3
"""Virtual insertion sweep: slide the male mount rail into a rendered case base and check that it
mates, stops, locks, and rides over its gravity-lock bump inside the dovetail's own play
(architecture.md §13 D34, D44, D48).

    python scripts/rail_fit.py [case-slug]          # default: pro-convert-for-ndi-to-hdmi

Renders mcc_rail_male() (no plate) with the pinned OpenSCAD and loads exports/(slug)/base.model.stl
(run `build.py render (slug) --part base` first). Frame: the case as rendered (floor at Z=0); the male
sits at (dx, MCC_RAIL_Y + dy, 0). dx is the insertion offset along X: 0 = fully mated, negative =
over-travel, positive = not yet fully in (also the direction a hanging case is pulled to remove it).
dy is the male's Y offset from the groove's centre line. A case hanging patch-wall down (D49) rests
on the male's -Y flank, i.e. at dy_lo, the most negative collision-free dy; the lock bump pushes the
case toward the far wall, i.e. the male toward larger dy.

Checked, exit code 0 when all hold:
  1. full mate (dx = 0): zero overlap at dy_lo, 0 and dy_hi -- the bump sits in its pocket with
     clearance, and the play band dy_hi - dy_lo is the dovetail's own (about 2 x 0.577 mm);
  2. over-travel (dx = -0.5): overlap -- the groove's closed -X end stops the rail;
  3. locked (dx = pocket clearance + 0.1, hanging at dy_lo): overlap, only within the bump's X span
     -- a hanging case cannot be pulled off without lifting it;
  4. insertion sweep, every dx: the least lift that clears everything, lift = dy_req - dy_lo, fits
     the play band with MCC_RAIL_LOCK_PLAY_MARGIN to spare, and at dy_lo nothing but the bump
     touches -- the case rides over the bump inside the flank play, nothing has to flex.
"""

from __future__ import annotations

import math
import re
import sys
import tempfile
from pathlib import Path

import trimesh
from trimesh.creation import box

import build

EPS_V = 1e-3    # mm^3: overlap volumes up to this count as zero (mesh noise on touching faces)
DY_TOL = 0.005  # mm: bisection tolerance of the Y searches


def _const(name):
    text = (build.LIB_DIR / "mcc" / "constants.scad").read_text(encoding="utf-8")
    return float(re.search(rf"^{name}\s*=\s*([-\d.]+)", text, re.M).group(1))


def _overlap(male, base, dx, y):
    """(volume, male-frame X span or None) of the male at (dx, y, 0) intersected with the base."""
    m = male.copy()
    m.apply_translation([dx, y, 0.0])
    inter = trimesh.boolean.intersection([m, base], engine="manifold")
    v = float(inter.volume) if inter is not None and len(inter.faces) else 0.0
    if v <= EPS_V:
        return 0.0, None
    return v, (float(inter.bounds[0][0]) - dx, float(inter.bounds[1][0]) - dx)


def _free(male, base, dx, y):
    return _overlap(male, base, dx, y)[0] == 0.0


def _extreme_free_y(male, base, dx, y0, direction, span=3.0):
    """From the collision-free y0, the farthest collision-free y in `direction` (+1 or -1)."""
    lo, hi = 0.0, span
    if _free(male, base, dx, y0 + direction * hi):
        return y0 + direction * hi
    while DY_TOL < hi - lo:
        mid = 0.5 * (lo + hi)
        if _free(male, base, dx, y0 + direction * mid):
            lo = mid
        else:
            hi = mid
    return y0 + direction * lo


def _least_free_y(male, base, dx, y_lo, y_hi):
    """The smallest collision-free y in [y_lo, y_hi] at dx, or None if even y_hi collides."""
    if _free(male, base, dx, y_lo):
        return y_lo
    if not _free(male, base, dx, y_hi):
        return None
    lo, hi = y_lo, y_hi
    while DY_TOL < hi - lo:
        mid = 0.5 * (lo + hi)
        if _free(male, base, dx, mid):
            hi = mid
        else:
            lo = mid
    return hi


def main(argv):
    slug = argv[0] if argv else "pro-convert-for-ndi-to-hdmi"
    base_path = build.EXPORTS_DIR / slug / "base.model.stl"
    if not base_path.is_file():
        print(f"error: {base_path} missing - run `build.py render {slug} --part base` first")
        return 1
    with tempfile.TemporaryDirectory(prefix="mcc_railfit_") as t:
        scad = Path(t) / "male.scad"
        scad.write_text("include <mcc/mcc.scad>\nmcc_rail_male();\n", encoding="utf-8")
        stl = Path(t) / "male.stl"
        ok, _ = build.run_openscad(build.find_openscad(), scad, {}, [stl], None)
        if not ok:
            return 1
        male = trimesh.load(str(stl), force="mesh")

    rail_y = _const("MCC_RAIL_Y")
    margin = _const("MCC_RAIL_LOCK_PLAY_MARGIN")
    e = _const("MCC_RAIL_LOCK_ENGAGE")
    pocket_clr = _const("MCC_RAIL_MATE_CLR") / math.sin(math.radians(_const("MCC_RAIL_FLANK_ANGLE")))
    half = _const("MCC_RAIL_LEN") / 2
    x1 = half - _const("MCC_RAIL_LOCK_END_OFFSET")  # bump exit face, male frame (rail.scad geometry)
    x0 = x1 - _const("MCC_RAIL_LOCK_FLAT") - e / math.tan(math.radians(_const("MCC_RAIL_LOCK_RAMP_IN")))

    # Everything the male can touch lies within this band (the male is 3.5 mm tall and about 66 mm
    # wide); cropping the base to it once keeps every boolean below fast, and loses no contact.
    whole = trimesh.load(str(base_path), force="mesh")
    base = trimesh.boolean.intersection(
        [whole, box(bounds=[[-400, rail_y - 45, -10], [400, rail_y + 45, 12]])], engine="manifold")
    case_len = float(whole.bounds[1][0] - whole.bounds[0][0])
    bad = []

    # 1. Full mate.
    if not _free(male, base, 0.0, rail_y):
        print("FAIL: fully mated and centred, but overlapping")
        print("rail fit FAILED")
        return 1
    dy_lo = _extreme_free_y(male, base, 0.0, rail_y, -1) - rail_y
    dy_hi = _extreme_free_y(male, base, 0.0, rail_y, +1) - rail_y
    play = dy_hi - dy_lo
    print(f"full mate: play band dy {dy_lo:+.3f} .. {dy_hi:+.3f} (play {play:.3f} mm)")
    for dy in (dy_lo, 0.0, dy_hi):
        if not _free(male, base, 0.0, rail_y + dy):
            bad.append(f"fully mated but overlapping at dy={dy:+.3f}")

    # 2. Over-travel.
    if _free(male, base, -0.5, rail_y):
        bad.append("no end stop: over-travel at dx=-0.5 does not collide")

    # 3. Locked while hanging.
    dx_lock = pocket_clr + 0.1
    v, span = _overlap(male, base, dx_lock, rail_y + dy_lo)
    print(f"locked:    dx={dx_lock:.3f} hanging  overlap={v:.3f} mm3" + (f"  male x {span[0]:.2f}..{span[1]:.2f}" if span else ""))
    if span is None:
        bad.append(f"not locked: a hanging case slides {dx_lock:.3f} mm toward removal without collision")
    elif span[0] + 0.5 < x0 or x1 + 0.5 < span[1]:
        bad.append(f"lock collision outside the bump {x0:.2f}..{x1:.2f} (male x {span[0]:.2f}..{span[1]:.2f})")

    # 4. Insertion sweep.
    dxs = [0.1, 0.25, 0.4, 0.5, 0.6, 0.75, 1.0, 1.5, 2.0, 2.5, 3.0, 4.0, 5.0, 7.5, 10.0]
    dxs += [12.5 + 2.5 * i for i in range(int((case_len / 2 - x0 + 5.0 - 12.5) / 2.5) + 1)]
    dxs += [60.0, 90.0, 120.0, case_len / 2 + half - 1.0]
    worst = 0.0
    for dx in dxs:
        y_req = _least_free_y(male, base, dx, rail_y + dy_lo, rail_y + dy_hi)
        v, span = _overlap(male, base, dx, rail_y + dy_lo)
        if y_req is None:
            bad.append(f"dx={dx:.2f}: no collision-free position inside the play band")
            print(f"dx={dx:7.2f}  BLOCKED")
            continue
        lift = y_req - (rail_y + dy_lo)
        worst = max(worst, lift)
        print(f"dx={dx:7.2f}  lift={lift:.3f} mm" + (f"  hanging overlap male x {span[0]:.2f}..{span[1]:.2f}" if span else ""))
        if play + DY_TOL < lift + margin:
            bad.append(f"dx={dx:.2f}: lift {lift:.3f} + margin {margin} exceeds the play {play:.3f}")
        if span and (span[0] + 0.5 < x0 or x1 + 0.5 < span[1]):
            bad.append(f"dx={dx:.2f}: collision outside the bump {x0:.2f}..{x1:.2f} (male x {span[0]:.2f}..{span[1]:.2f})")
    print(f"max lift over the bump {worst:.3f} mm of {play:.3f} mm play (margin {margin} mm, bump {e} mm)")

    for b in bad:
        print("FAIL:", b)
    print("rail fit OK" if not bad else "rail fit FAILED")
    return 0 if not bad else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
