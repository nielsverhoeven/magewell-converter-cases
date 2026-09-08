# scripts/

One build implementation, two entry points, per `.claude/knowledge/architecture.md` §9:

- `build.py` — the implementation. Python 3.11+, stdlib + `trimesh` (see `../requirements.txt`).
  This is what CI (`.github/workflows/render.yml`, `.github/workflows/release.yml`) runs.
- `render.ps1` — a thin PowerShell wrapper over `build.py` for Windows muscle memory. It
  activates `.venv` if present and forwards every argument unchanged. It must never gain logic
  of its own — if you find yourself editing `render.ps1` to change behaviour, that behaviour
  belongs in `build.py` instead.
- `mesh_to_step.py` — STL → STEP conversion (`cadquery-ocp` or FreeCAD `freecadcmd` backend),
  used by `build.py step`. Can also be run standalone for one file — see its own `--help`.
- `release_version.py` — computes the next `vX.Y.Z` from Conventional Commits since the last
  `v*` tag. Used by `.github/workflows/release.yml`; see "Release tooling" below.
- `package_release.py` — builds the per-device and coupon release zips from `exports/`. Also used
  by `release.yml`.

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

`build.py step` (STL → STEP export) additionally needs a STEP backend, kept in a separate
requirements file since it's a heavy, platform-specific wheel that a plain render/check/golden
loop never needs:

```powershell
.venv\Scripts\python -m pip install -r requirements-step.txt
```

If no wheel is available for your Python version, `mesh_to_step.py` falls back to FreeCAD's
`freecadcmd` (located via the `MCC_FREECAD` env var or the default Windows install path) — install
it with `winget install --id FreeCAD.FreeCAD --exact` if needed. `build.py doctor` reports which
backend (if either) is available.

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
| `step pro-convert-for-ndi-to-hdmi` | Convert one target's already-rendered STL(s) to `exports/<target>/<part>.step` — a B-rep with coplanar facets merged (`ShapeUpgrade_UnifySameDomain`), curved surfaces still faceted. Needs `render` to have run first. Records backend + face counts (before/after unify) into `<part>.manifest.json`'s `"step"` key. |
| `step --all` | STEP-convert every discovered target. Warns and exits 0 if no STEP backend is available locally; fails (exit 1) if `CI=true` and no backend is available. |
| `smoke` | Tier 2: run every `tests/test_*.scad` with `-o *.csg` (evaluates the tree, asserts fire, no tessellation). Fast. |
| `check --all` | Tier 3: trimesh mesh checks (watertight, winding-consistent, volume > 0, single connected shell, bbox ≤ 244 mm/axis) on every `exports/**/*.stl`. |
| `check exports/coupons/neutrik-tile/neutrik-tile.stl` | Check specific STL file(s). |
| `golden` | Tier 3: compare every rendered target's measured summary against its committed golden in `tests/golden/`. |
| `golden --update coupons/neutrik-tile` | (Re)write the golden for one target from its current render. Justify golden changes in the PR — see `tests/golden/README.md`. |
| `confidence` | Lists every model's ports below `"measured"` confidence (parsed straight from `lib/mcc/devices/*.scad`'s DATA-ONLY port records — no OpenSCAD render needed). Exit code is always `0`; this is a report, not a gate. `--json` for machine-readable output; either form writes `prerelease=true\|false` to `$GITHUB_OUTPUT` when set. Used by `release.yml` to decide the GitHub Release's pre-release flag. |
| `all` | `smoke` → `render --all` → `check --all` → `golden`, in order. What CI runs on every push/PR. |
| `all --release` | Same, with the release warning gate on (fails on any `WARNING: unmeasured` port echoed at render time). |
| `all --with-step` | `all`, then `step --all` at the end. What `release.yml` runs. |

## Environment

- OpenSCAD is located via, in order: the `MCC_OPENSCAD` environment variable, the Windows
  nightly default install path (`C:\Program Files\OpenSCAD (Nightly)\openscad.com`), then
  `openscad` on `PATH`.
- `OPENSCADPATH` is set to `<repo>/lib` automatically for every OpenSCAD subprocess, so
  `include <BOSL2/std.scad>` and `include <mcc/mcc.scad>` resolve without any manual setup.
- Every render always passes `--backend=Manifold` explicitly — never rely on a GUI preference.

## Release tooling

Used by `.github/workflows/release.yml` on every push to `main` — see `CONTRIBUTING.md`'s "Release"
section for the full flow. Not something you normally run by hand, but each is safe to run locally
for testing:

```powershell
.venv\Scripts\python scripts\release_version.py               # prints the next vX.Y.Z to stdout
.venv\Scripts\python scripts\build.py confidence --json        # ports below "measured", per model
.venv\Scripts\python scripts\package_release.py v0.0.0-test    # builds dist/*.zip from exports/
```

`release_version.py` finds the latest `v*` tag reachable from `HEAD` (`v0.0.0` if none exists) and
walks `git log <tag>..HEAD` classifying each commit's Conventional Commits header (and any
`BREAKING CHANGE:`/`BREAKING-CHANGE:` footer) into MAJOR/MINOR/PATCH, then prints the highest bump
found. `package_release.py <version>` expects `exports/` to already be populated (run `build.py all
--with-step` first) — it never renders anything itself, only zips what's already there, and skips
(with a warning, not an error) any target with nothing exported. Both scripts write their outputs to
`$GITHUB_OUTPUT` when it's set (inside a GitHub Actions step), for use by later workflow steps.

`dist/` (where `package_release.py` writes) is gitignored exactly like `exports/` — delete it after
a local test run.
