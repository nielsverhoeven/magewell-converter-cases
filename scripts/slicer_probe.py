#!/usr/bin/env python3
"""Locate a Bambu Studio slicer warning on one part — the debugging half of `build.py slicer-check`.

`slicer-check` says *which* part Bambu Studio flags ("floating regions", "floating cantilever", ...)
but the slicer never says *where*. Three probes answer that, all driven through the real slicer CLI
(see .claude/knowledge/bambu-slicer.md §3 for when to use which):

  zbisect  <stl> [--lo Z --hi Z]
      Slice the part clipped at height z (everything above removed) and bisect z until the first
      height at which the warning appears — the Z of the offending feature. ~8 slices.

  box      <stl> --z Z --x X0 X1 --y Y0 Y1
      Slice only the part inside that box (and below Z). Halve the box repeatedly to find the XY.

  critical <stl>
      Re-slice with support_critical_regions_only=1 (supports only for sharp tails / cantilevers)
      and report where the slicer put support — per 2 mm Z band and the top of the support per X
      bin. The top of the support is the underside of what Bambu considers critical. With supports
      on the warning itself disappears; this is a diagnostic only.

<stl> is any mesh in the frame you want answers in — normally `exports/<target>/<part>.model.stl`
(model frame: the coordinates used in the .scad source). The probe re-poses it as-modelled, i.e. it
assumes the part prints in its modelled orientation; for a flipped part (lid, panel) pass the print
STL `exports/<target>/<part>.stl` instead and read the answers in print coordinates.

Needs trimesh + manifold3d + mapbox-earcut (requirements.txt) and Bambu Studio (MCC_BAMBU_STUDIO or
the default Windows install path).
"""

from __future__ import annotations

import argparse
import copy
import json
import re
import subprocess
import sys
import tempfile
from pathlib import Path

import numpy as np
import trimesh

import bambu_project
import build


def _project_for(mesh: trimesh.Trimesh, name: str, out: Path, overrides: dict | None = None):
    v = bambu_project.to_print_pose(mesh.vertices, "as-modelled")
    plates = bambu_project.layout_plates([bambu_project.PrintObject(name, v, mesh.faces)])
    saved = copy.deepcopy(bambu_project.PROCESS_OVERRIDES)
    try:
        bambu_project.PROCESS_OVERRIDES.update(overrides or {})
        bambu_project.write_project(out, plates, title=name)
    finally:
        bambu_project.PROCESS_OVERRIDES.clear()
        bambu_project.PROCESS_OVERRIDES.update(saved)
    return plates[0][0]


def _clip(mesh: trimesh.Trimesh, planes) -> trimesh.Trimesh:
    for origin, normal in planes:
        mesh = mesh.slice_plane(origin, normal, cap=True)
    return mesh


def _warnings(exe: Path, mesh: trimesh.Trimesh, tmp: Path, tag: str) -> list[str]:
    p = tmp / f"probe_{tag}.3mf"
    _project_for(mesh, "probe", p)
    _ok, w = build.slicer_check_project(exe, p)
    return w


def cmd_zbisect(args, exe: Path, mesh: trimesh.Trimesh, tmp: Path) -> int:
    lo = args.lo if args.lo is not None else float(mesh.bounds[0][2]) + 0.4
    hi = args.hi if args.hi is not None else float(mesh.bounds[1][2])
    w = _warnings(exe, mesh, tmp, "full")
    print(f"whole part: {w or 'no warning'}")
    if not w:
        return 0
    while hi - lo > 0.25:
        mid = (lo + hi) / 2
        w = _warnings(exe, _clip(mesh, [([0, 0, mid], [0, 0, -1])]), tmp, f"z{mid:.2f}")
        print(f"  z <= {mid:6.2f}: {w[0] if w else 'ok'}", flush=True)
        lo, hi = (lo, mid) if w else (mid, hi)
    print(f"first warning appears between z = {lo:.2f} and z = {hi:.2f}")
    return 0


def cmd_box(args, exe: Path, mesh: trimesh.Trimesh, tmp: Path) -> int:
    (x0, x1), (y0, y1) = args.x, args.y
    part = _clip(mesh, [([0, 0, args.z], [0, 0, -1]), ([x0, 0, 0], [1, 0, 0]), ([x1, 0, 0], [-1, 0, 0]),
                        ([0, y0, 0], [0, 1, 0]), ([0, y1, 0], [0, -1, 0])])
    w = _warnings(exe, part, tmp, "box")
    print(f"z <= {args.z}, x {x0}..{x1}, y {y0}..{y1}: {w or 'no warning'}")
    return 0


def cmd_critical(args, exe: Path, mesh: trimesh.Trimesh, tmp: Path) -> int:
    p = tmp / "probe_critical.3mf"
    spot = _project_for(mesh, "probe", p, {"enable_support": "1", "support_critical_regions_only": "1"})
    subprocess.run([str(exe), "--slice", "0", "--outputdir", str(tmp), str(p)],
                   capture_output=True, timeout=build.SLICE_TIMEOUT_S, cwd=tmp, check=False)
    gcode = tmp / "plate_1.gcode"
    if not gcode.is_file():
        print("error: the slicer produced no G-code")
        return 1
    lo, hi = mesh.bounds
    cx, cy = (lo[0] + hi[0]) / 2, (lo[1] + hi[1]) / 2
    z, feat, pts = 0.0, None, []
    for line in gcode.read_text(errors="ignore").splitlines():
        if line.startswith(("; Z_HEIGHT:", ";Z_HEIGHT:")):
            z = float(line.split(":", 1)[1])
        elif line.startswith(("; FEATURE:", ";TYPE:")):
            feat = line.split(":", 1)[1].strip()
        elif feat and "support" in feat.lower() and line.startswith(("G1", "G2", "G3")) and " E" in line:
            mx, my = re.search(r"X([-\d.]+)", line), re.search(r"Y([-\d.]+)", line)
            if mx and my:
                pts.append((float(mx.group(1)) - spot.x + cx, float(my.group(1)) - spot.y + cy, z + lo[2]))
    if not pts:
        print("no critical support — Bambu Studio sees no sharp tail / cantilever on this part")
        return 0
    a = np.array(pts)
    print(f"{len(a)} support moves, z {a[:, 2].min():.2f}..{a[:, 2].max():.2f} (STL coordinates)")
    for zb in np.unique(np.floor(a[:, 2] / 2) * 2):
        s = a[(a[:, 2] >= zb) & (a[:, 2] < zb + 2)]
        print(f"  z {zb:5.1f}-{zb + 2:5.1f}: x {s[:, 0].min():7.1f}..{s[:, 0].max():7.1f}  "
              f"y {s[:, 1].min():7.1f}..{s[:, 1].max():7.1f}  ({len(s)} moves)")
    print("support top per 10 mm X bin (= underside of the critical feature):")
    for xb in np.arange(np.floor(a[:, 0].min() / 10) * 10, a[:, 0].max(), 10):
        s = a[(a[:, 0] >= xb) & (a[:, 0] < xb + 10)]
        if len(s):
            t = s[s[:, 2] >= s[:, 2].max() - 0.01]
            print(f"  x {xb:6.0f}..{xb + 10:4.0f}: top z = {s[:, 2].max():6.2f}  y {t[:, 1].min():6.1f}..{t[:, 1].max():6.1f}")
    return 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="slicer_probe.py", description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    z = sub.add_parser("zbisect"); z.add_argument("stl"); z.add_argument("--lo", type=float); z.add_argument("--hi", type=float)
    b = sub.add_parser("box"); b.add_argument("stl"); b.add_argument("--z", type=float, required=True)
    b.add_argument("--x", type=float, nargs=2, required=True); b.add_argument("--y", type=float, nargs=2, required=True)
    c = sub.add_parser("critical"); c.add_argument("stl")
    args = ap.parse_args(argv)

    exe = build.find_bambu_studio()
    if exe is None:
        print("error: Bambu Studio not found (set MCC_BAMBU_STUDIO)")
        return 1
    mesh = trimesh.load(args.stl, force="mesh")
    with tempfile.TemporaryDirectory(prefix="mcc_probe_") as t:
        return {"zbisect": cmd_zbisect, "box": cmd_box, "critical": cmd_critical}[args.cmd](args, exe, mesh, Path(t))


if __name__ == "__main__":
    sys.exit(main())
