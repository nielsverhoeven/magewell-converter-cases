#!/usr/bin/env python3
"""Virtual insertion sweep: slide the male mount rail into a rendered case base and check that it
mates, stops, locks, rides over its top-lock strips inside the dovetail's own play, and that the
groove is closed everywhere except its mouth and its +X entry (architecture.md §13 D34, D44, D63.1, D64.1).

    python scripts/rail_fit.py [case-slug]          # default: pro-convert-for-ndi-to-hdmi

Renders mcc_rail_male() (no plate) with the pinned OpenSCAD and loads exports/(slug)/base.model.stl
(run `build.py render (slug) --part base` first). Frame: the case as rendered (floor at Z=0); the male
sits at (dx, MCC_RAIL_Y + dy, -lift). dx is the insertion offset along X: 0 = fully mated, negative =
over-travel, positive = not yet fully in (also the direction a hanging case is pulled to remove it).
dy is the male's Y offset from the groove's centre line; lift is how far the case stands off the
plate. A case hanging patch-wall down (D49) rests on the male's -Y flank, i.e. at dy_lo; moving off
the plate it rides up that flank, i.e. dy = dy_lo + k * lift (k = the flank's run per mm of height).

Checked, exit code 0 when all hold:
  1. full mate (dx = 0): zero overlap at dy_lo, 0 and dy_hi; the play band dy_hi - dy_lo (about
     2 x 0.577 mm) and the Z-play (about 1.0 mm) are the dovetail's own;
  2. over-travel (dx = -0.5): overlap -- the groove's closed -X end stops the rail;
  3. locked (dx = MCC_RAIL_MATE_CLR + 0.1, floor on the plate): overlap only at the strips' exit
     faces, at every dy in the play band -- lifting the case alone never releases it;
  4. square exit face: the pull-off needed just past the axial play and 1.5 mm further is the same,
     about MCC_RAIL_LOCK_ENGAGE -- no cam;
  5. insertion sweep, every dx: the least pull-off that clears everything, plus
     MCC_RAIL_LOCK_PLAY_MARGIN, fits the Z-play, and at lift 0 nothing but the strips touches;
  6. the groove is closed: rays from inside it toward -X stop at its closed end, rays up (+Z) stop
     at the roof, the roof slot or the lead-in, rays across (+-Y) stop at the flanks.
"""

from __future__ import annotations

import math
import re
import sys
import tempfile
from pathlib import Path

import numpy as np
import trimesh
from trimesh.creation import box

import build

EPS_V = 1e-3    # mm^3: overlap volumes up to this count as zero (mesh noise on touching faces)
TOL = 0.005     # mm: bisection tolerance
RAY_TOL = 0.05  # mm: how far past a boundary a ray hit may land


def _const(name):
    text = (build.LIB_DIR / "mcc" / "constants.scad").read_text(encoding="utf-8")
    return float(re.search(rf"^{name}\s*=\s*([-\d.]+)", text, re.M).group(1))


def _overlap(male, base, dx, dy, lift):
    """(volume, male-frame X span or None) of the male at (dx, MCC_RAIL_Y + dy, -lift) in the base."""
    m = male.copy()
    m.apply_translation([dx, RAIL_Y + dy, -lift])
    inter = trimesh.boolean.intersection([m, base], engine="manifold")
    v = float(inter.volume) if inter is not None and len(inter.faces) else 0.0
    if v <= EPS_V:
        return 0.0, None
    return v, (float(inter.bounds[0][0]) - dx, float(inter.bounds[1][0]) - dx)


def _free(male, base, dx, dy, lift):
    return _overlap(male, base, dx, dy, lift)[0] == 0.0


def _bisect(pred, lo, hi):
    """Smallest t in [lo, hi] with pred(t) true (pred monotone in t); None if pred(hi) is false."""
    if pred(lo):
        return lo
    if not pred(hi):
        return None
    while TOL < hi - lo:
        mid = 0.5 * (lo + hi)
        if pred(mid):
            hi = mid
        else:
            lo = mid
    return hi


def _band_edge(male, base, sign):
    """At full mate on the plate, the farthest collision-free dy from the centre toward `sign`."""
    lo, hi = 0.0, 3.0
    while TOL < hi - lo:
        mid = 0.5 * (lo + hi)
        if _free(male, base, 0.0, sign * mid, 0.0):
            lo = mid
        else:
            hi = mid
    return sign * lo


RAIL_Y = _const("MCC_RAIL_Y")


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

    angle = math.radians(_const("MCC_RAIL_FLANK_ANGLE"))
    k = 1.0 / math.tan(angle)                                   # flank run per mm of height
    mate = _const("MCC_RAIL_MATE_CLR")
    e = _const("MCC_RAIL_LOCK_ENGAGE")
    margin = _const("MCC_RAIL_LOCK_PLAY_MARGIN")
    half = _const("MCC_RAIL_LEN") / 2
    x1 = half - _const("MCC_RAIL_LOCK_END_OFFSET")              # strips' exit face, male frame
    x0 = x1 - _const("MCC_RAIL_LOCK_STRIP_X")
    depth = _const("MCC_RAIL_DEPTH")
    z_top = depth + max(_const("MCC_RAIL_LEADIN"), e + mate)    # highest groove surface (slot / lead-in)
    y_side = _const("MCC_RAIL_ROOT_W") / 2 + mate / math.sin(angle) + _const("MCC_RAIL_LEADIN")

    # Everything the male can touch lies within this band; cropping the base once keeps every boolean
    # below fast and loses no contact.
    whole = trimesh.load(str(base_path), force="mesh")
    base = trimesh.boolean.intersection(
        [whole, box(bounds=[[-400, RAIL_Y - 45, -10], [400, RAIL_Y + 45, 12]])], engine="manifold")
    case_len = float(whole.bounds[1][0] - whole.bounds[0][0])
    bad = []

    # 1. Full mate.
    if not _free(male, base, 0.0, 0.0, 0.0):
        print("FAIL: fully mated and centred, but overlapping")
        print("rail fit FAILED")
        return 1
    dy_lo, dy_hi = _band_edge(male, base, -1), _band_edge(male, base, +1)
    play = dy_hi - dy_lo
    mid = 0.5 * (dy_lo + dy_hi)
    zc = _bisect(lambda s: not _free(male, base, 0.0, mid, s), 0.0, 2.0)
    z_play = (zc - TOL) if zc is not None else 2.0
    print(f"full mate: play band dy {dy_lo:+.3f} .. {dy_hi:+.3f} (play {play:.3f} mm), Z-play {z_play:.3f} mm")
    for dy in (dy_lo, 0.0, dy_hi):
        if not _free(male, base, 0.0, dy, 0.0):
            bad.append(f"fully mated but overlapping at dy={dy:+.3f}")

    # 2. Over-travel.
    if _free(male, base, -0.5, dy_lo, 0.0):
        bad.append("no end stop: over-travel at dx=-0.5 does not collide")

    # 3. Locked while hanging, floor on the plate, at every dy in the play band.
    dx_lock = mate + 0.1
    v, span = _overlap(male, base, dx_lock, dy_lo, 0.0)
    print(f"locked:    dx={dx_lock:.2f} hanging  overlap={v:.3f} mm3" + (f"  male x {span[0]:.2f}..{span[1]:.2f}" if span else ""))
    if span is None:
        bad.append(f"not locked: a hanging case slides {dx_lock:.2f} mm toward removal without collision")
    elif span[0] + mate < x0 or x1 + mate < span[1]:
        bad.append(f"lock collision outside the strips {x0:.2f}..{x1:.2f} (male x {span[0]:.2f}..{span[1]:.2f})")
    for dy in np.linspace(dy_lo, dy_hi, 5):
        if _free(male, base, dx_lock, float(dy), 0.0):
            bad.append(f"a lift alone releases the lock: free at dx={dx_lock:.2f} dy={dy:+.3f}")

    # 4. Square exit face: the same pull-off just past the axial play and 1.5 mm further.
    def pull_off(dx):
        return _bisect(lambda s: _free(male, base, dx, dy_lo + k * s, s), 0.0, z_play - 0.01)
    p_near, p_far = pull_off(mate + 0.05), pull_off(mate + 1.5)
    fmt = lambda p: "none" if p is None else f"{p:.3f}"
    print(f"release:   pull-off {fmt(p_near)} mm at dx={mate + 0.05:.2f}, {fmt(p_far)} mm at dx={mate + 1.5:.2f} (engagement {e})")
    if p_near is None or p_far is None or abs(p_near - e) > 0.02 or abs(p_far - p_near) > 0.02:
        bad.append(f"exit face not square / release pull-off {p_near}, {p_far} vs engagement {e}")

    # 5. Insertion sweep.
    dxs = [0.25, 0.4, 0.5, 0.6, 0.75, 1.0, 1.5, 2.0, 3.0, 5.0, 7.5, 10.0]
    dxs += [12.5 + 2.5 * i for i in range(int((case_len / 2 - x0 + 5.0 - 12.5) / 2.5) + 1)]
    dxs += [60.0, 90.0, 120.0, case_len / 2 + half - 1.0]
    worst = 0.0
    for dx in dxs:
        need = pull_off(dx)
        v, span = _overlap(male, base, dx, dy_lo, 0.0)
        if need is None:
            bad.append(f"dx={dx:.2f}: no collision-free position inside the Z-play")
            print(f"dx={dx:7.2f}  BLOCKED")
            continue
        worst = max(worst, need)
        if need > 0.0:
            print(f"dx={dx:7.2f}  ride: off the plate {need:.3f} mm" + (f"  (hanging overlap male x {span[0]:.2f}..{span[1]:.2f})" if span else ""))
        if z_play + TOL < need + margin:
            bad.append(f"dx={dx:.2f}: ride {need:.3f} + margin {margin} exceeds the Z-play {z_play:.3f}")
        if span and (span[0] + mate < x0 or x1 + mate < span[1]):
            bad.append(f"dx={dx:.2f}: collision outside the strips {x0:.2f}..{x1:.2f} (male x {span[0]:.2f}..{span[1]:.2f})")
    print(f"max ride off the plate {worst:.3f} mm of {z_play:.3f} mm Z-play (margin {margin} mm, strips {e} mm)")

    # 6. The groove is closed: rays from inside it.
    x_end = -half
    hits = []
    for z in (0.5, 1.5, 2.5, 3.1, 3.5, 3.9):
        for y in (-25.0, 0.0, 25.0):
            loc, _, _ = whole.ray.intersects_location([[x_end + 20.0, RAIL_Y + y, z]], [[-1.0, 0.0, 0.0]], multiple_hits=False)
            hx = float(loc[0][0]) if len(loc) else None
            hits.append(hx)
            if hx is None or hx < x_end - RAY_TOL:
                bad.append(f"-X ray at z={z} y={y:+.0f}: first hit x={hx}, past the groove's closed end x={x_end}")
    n_up = n_side = 0
    for x in np.arange(x_end + 1.0, case_len / 2 - 0.5, 2.0):
        for y in (-30.0, -15.0, 0.0, 15.0, 30.0):
            loc, _, _ = whole.ray.intersects_location([[x, RAIL_Y + y, 2.0]], [[0.0, 0.0, 1.0]], multiple_hits=False)
            n_up += 1
            if not len(loc) or loc[0][2] > z_top + RAY_TOL:
                bad.append(f"+Z ray at x={x:.1f} y={y:+.0f}: first hit {None if not len(loc) else round(float(loc[0][2]), 2)} above the groove")
        for z in (1.0, 3.0):
            for sign in (-1.0, 1.0):
                loc, _, _ = whole.ray.intersects_location([[x, RAIL_Y, z]], [[0.0, sign, 0.0]], multiple_hits=False)
                n_side += 1
                if not len(loc) or abs(loc[0][1] - RAIL_Y) > y_side + RAY_TOL:
                    bad.append(f"{'+' if sign > 0 else '-'}Y ray at x={x:.1f} z={z}: escapes the groove's flank")
    valid = [h for h in hits if h is not None]
    print(f"groove closed: {len(hits)} -X rays stop at x {min(valid):.2f} .. {max(valid):.2f} (end {x_end}); "
          f"{n_up} +Z rays and {n_side} +-Y rays stay inside the groove")

    for b in bad:
        print("FAIL:", b)
    print("rail fit OK" if not bad else "rail fit FAILED")
    return 0 if not bad else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
