# scripts/

One build implementation, two entry points, per `.claude/knowledge/architecture.md` §9:

- `build.py` — the implementation. Python 3.11+, stdlib + `trimesh` (see `../requirements.txt`).
  This is what CI (`.github/workflows/render.yml`) runs.
- `render.ps1` — a thin PowerShell wrapper over `build.py` for Windows muscle memory. It
  activates `.venv` if present and forwards every argument unchanged. It must never gain logic
  of its own — if you find yourself editing `render.ps1` to change behaviour, that behaviour
  belongs in `build.py` instead.

## Setup

```powershell
py -3 -m venv .venv
.venv\Scripts\python -m pip install -r requirements.txt
```

If `ensurepip` fails inside the venv (a broken global Python install can do this even though the
venv itself is otherwise fine):

```powershell
.venv\Scripts\python -m ensurepip --upgrade
.venv\Scripts\python -m pip install -r requirements.txt
```

## Command cheat-sheet

Run these as `.venv\Scripts\python scripts\build.py <command>` or `scripts\render.ps1 <command>`
— they are equivalent.

| Command | Does |
|---|---|
| `doctor` | Print resolved OpenSCAD path/version, BOSL2 submodule SHA, venv/trimesh status, and every discovered coupon/model target. Run this first. |
| `render --all` | Render every discovered coupon and model part to STL in `exports/`. |
| `render coupons/neutrik-tile` | Render one coupon by name. |
| `render coupons/neutrik-tile --format both` | Also emit `.3mf`. |
| `render pro-convert-hdmi-tx --part base --part lid` | Render specific parts of a model. |
| `render path/to/some.scad --part base -D foo=1` | Render an ad-hoc `.scad` file with extra `-D` overrides. |
| `render --all --release` | Release build: also fails if OpenSCAD emits `WARNING: unmeasured` (a port below `measured` confidence used for a real cutout). |
| `smoke` | Tier 2: run every `tests/test_*.scad` with `-o *.csg` (evaluates the tree, asserts fire, no tessellation). Fast. |
| `check --all` | Tier 3: trimesh mesh checks (watertight, winding-consistent, volume > 0, single connected shell, bbox ≤ 244 mm/axis) on every `exports/**/*.stl`. |
| `check exports/coupons/neutrik-tile/neutrik-tile.stl` | Check specific STL file(s). |
| `golden` | Tier 3: compare every rendered target's measured summary against its committed golden in `tests/golden/`. |
| `golden --update coupons/neutrik-tile` | (Re)write the golden for one target from its current render. Justify golden changes in the PR — see `tests/golden/README.md`. |
| `all` | `smoke` → `render --all` → `check --all` → `golden`, in order. What CI runs on every push/PR. |
| `all --release` | Same, with the release warning gate on. What CI runs on tag builds. |

## Environment

- OpenSCAD is located via, in order: the `MCC_OPENSCAD` environment variable, the Windows
  nightly default install path (`C:\Program Files\OpenSCAD (Nightly)\openscad.com`), then
  `openscad` on `PATH`.
- `OPENSCADPATH` is set to `<repo>/lib` automatically for every OpenSCAD subprocess, so
  `include <BOSL2/std.scad>` and `include <mcc/mcc.scad>` resolve without any manual setup.
- Every render always passes `--backend=Manifold` explicitly — never rely on a GUI preference.
