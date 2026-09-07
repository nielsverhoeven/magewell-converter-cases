---
name: openscad-render
description: Invoke the pinned OpenSCAD nightly headlessly with the Manifold backend and -D overrides, and interpret its errors/warnings/summary output; use whenever you need to actually render, smoke-test, or export a .scad file rather than just read it.
---

# openscad-render

Rendering is how you find out whether a `.scad` file's asserts actually hold — reading the file is
not enough. This skill covers invoking OpenSCAD directly and how `scripts/build.py` wraps that for
CI/local parity.

## Pinned environment

| Thing | Value |
|---|---|
| Binary | `C:\Program Files\OpenSCAD (Nightly)\openscad.com` (the `.com` console-mode binary, not `.exe`, so stdout/stderr and the exit code are usable in scripts) |
| CSG backend | `--backend=Manifold` — **must be passed explicitly on every invocation**; do not rely on a GUI preference file, headless runs don't read it |
| Library path | `OPENSCADPATH=<repo>\lib` so `include <mcc/mcc.scad>` and `include <BOSL2/std.scad>` resolve without a relative-path hack in every model file |
| BOSL2 | git submodule at `lib/BOSL2/`, pinned SHA — if a render fails with a missing-symbol error from a BOSL2 call, check the submodule is actually checked out (`git submodule status`) before debugging your own code |

Exact OpenSCAD version string is an open question (architecture.md §12 Q1 — nightly "2025.09.07" vs.
today being 2026-09-07). Whatever the resolved answer, the exact version string that produced a given
export goes into that export's manifest — never assume it doesn't matter.

## Direct invocation (what `scripts/build.py` runs under the hood)

```powershell
$env:OPENSCADPATH = "C:\repos-github\magewell-converter-cases\lib"
& "C:\Program Files\OpenSCAD (Nightly)\openscad.com" `
    --backend=Manifold `
    -o out.stl `
    -D 'part="base"' `
    --summary all --summary-file out.json `
    models\pro-convert-hdmi-tx\case.scad
```

- `-D 'part="base"'` — string `-D` values need their own quotes preserved through the shell; in
  PowerShell wrap the whole `-D` argument in single quotes with the inner value double-quoted, as
  above. A bare `-D part=base` (no quotes) is parsed as an OpenSCAD *identifier*, not a string, and
  will not match a `part == "base"` comparison in the model.
- `--summary all --summary-file out.json` — always pass both together; the JSON summary (bbox,
  volume, area, triangle count) is what `tests/golden/*.json` diffs against.
- Swap `-o out.stl` for `-o out.csg` for a smoke test — CSG export evaluates the whole tree (so every
  `assert()` fires) without tessellating the mesh, so it's much faster and is what Tier-2 smoke tests
  use.
- Swap `-o out.stl` for `-o out.3mf` for a release-quality export (3MF preserves more than STL —
  color/material hints — but STL remains the default interchange format; see the export policy
  below for which one actually ships).

## Reading the output

- **`ERROR:`** — the render did not complete; nothing was written (or a partial/corrupt file was).
  Always non-zero exit code. Treat as a hard stop.
- **`WARNING: unmeasured ...`** (emitted by `ports.scad`'s port-confidence echo, once that file
  exists) — this is the `confidence` warning from architecture.md §7: it lists every port below
  `measured`. Expected and non-fatal on a **dev** build; `scripts/build.py`'s **release** build target
  fails on it for any port that feeds a real cutout. Don't silence it — fix the source data
  (`device-portmap` skill) or accept it's a dev-only render.
- **`WARNING: Ignoring unknown module/function ...`** — almost always a missing `use`/`include`, a
  `use` where an `include` was needed (or vice versa — see `openscad-authoring`'s failure modes), or
  a BOSL2 submodule that isn't checked out.
- **Manifold-specific warnings** (self-intersection, non-manifold edge) mean the CSG tree produced
  invalid geometry — this is a modeling bug, not a backend quirk; CGAL (the older, slower backend)
  would have silently "fixed" some of these at a performance cost. Manifold's stricter behavior is
  why it's the pinned backend: it surfaces bugs CGAL hides.
- **Exit code** — 0 only on a clean render with no `ERROR:`. `scripts/build.py` treats any non-zero
  exit as a failed step; never parse stdout text as the sole success signal.

## `scripts/build.py` subcommands

Single implementation, two entry points (architecture.md §9): `scripts/build.py` is what CI runs;
`scripts/render.ps1` (if present) is a thin Windows wrapper over it. Do not maintain a second
independent implementation of any of these — they will drift from what CI actually does.

| Subcommand | Does |
|---|---|
| `doctor` | Environment sanity: OpenSCAD binary found and version-string captured, BOSL2 submodule present and at the pinned SHA, `OPENSCADPATH` resolvable. Run this first when anything else fails mysteriously. |
| `render` | Renders every `models/<slug>/case.scad` for every `part` value it declares (typically `base`, `lid`, `panel`), `--backend=Manifold`, writes to `exports/` (gitignored). |
| `smoke` | Tier-2: `-o out.csg` on every public module at default/min/max parameters — fast, asserts-only, no tessellation. Non-zero exit = failure. |
| `check` | Tier-3 mesh checks via `check_mesh.py` (trimesh): `is_watertight`, `is_winding_consistent`, `euler_number`, `volume > 0`, `len(split()) == 1` (single connected shell — catches a rib/boss that floated free). Do not expect automated minimum-wall-thickness measurement; that's unreliable in trimesh — rely on the Tier-1 `assert()` plus a slicer check instead. |
| `golden` | Diffs `--summary` output against `tests/golden/<slug>.json` with tolerance (~0.5% volume, 0.1 mm bbox). `--update` regenerates the golden after a deliberate geometry change — never run `--update` to make a red diff go away without first understanding *why* it changed. |
| `all` | `doctor` + `smoke` + `render` + `check` + `golden`, in that order — what CI runs on every PR. |

## Manifold vs CGAL

Manifold is the pinned backend (architecture.md §2) because it's dramatically faster on Boolean-heavy
trees (this repo is nothing but Booleans: shell minus aperture minus vents minus insert bores) and,
per above, surfaces invalid-geometry bugs that CGAL papers over. There is no supported CGAL path in
this repo's tooling — if you see `--backend=CGAL` in a command someone wrote, that's a mistake to
flag, not a valid alternative to reach for when Manifold complains.

## STL vs 3MF, and what's committed

- `exports/` is **gitignored** — it's local scratch output, full stop. Never `git add` anything under
  it.
- `tests/golden/<slug>.json` **is** committed — small, diffable, catches unintended geometry drift in
  review.
- Release-quality STL + 3MF are built by CI from a **git tag** and attached to a GitHub Release —
  never committed to the working tree at any point, including "just this once for a demo."
- Every real artefact (not a smoke-test throwaway) ships with a manifest: git SHA, BOSL2 submodule
  SHA, OpenSCAD version string, the full `-D` parameter set used, and the measured bbox/volume from
  `--summary`. If you're generating an export by hand for someone, write this manifest alongside it —
  a binary without provenance is exactly the drift problem the export policy exists to prevent.

## Reading the `--summary` JSON

The fields that matter for goldens and for sanity-checking a change:

| Field | Use |
|---|---|
| `"bounding box"` (min/max or size, depending on OpenSCAD version) | Compare against `MCC_BUILD - MCC_BED_MARGIN`; also what `print-check`'s bed-fit step reads |
| `"volume"` | The golden-diff tolerance is ~0.5% — a bigger jump after a "small" parameter tweak usually means an unintended feature got added/removed, not just resized |
| `"area"` | Less commonly diffed, but a sudden large jump with volume roughly flat can indicate a mesh got more porous (more internal surface) without changing overall size — worth a second look with `check` |
| `"number of facets"` / triangle count | Sanity-check against `$fn`/`$fa`/`$fs` choices; a huge unexplained jump usually traces to a stray high-`$fn` cylinder introduced somewhere |
| `"number of vertices"` | Rarely inspected directly; useful when diagnosing a `check_mesh.py` `is_watertight` failure alongside `check` |

Treat the JSON as data for `tests/golden/*.json` and for your own sanity check, not as something to
hand-edit — always regenerate it via a real render (`build.py golden --update`), never patch a golden
file's numbers directly to make a diff pass.

## Multiple `-D` overrides in one invocation

`-D` can be repeated for multiple parameters, e.g. rendering a specific variant's `panel` part
directly without going through the model file's own `part` dispatch:

```powershell
& "C:\Program Files\OpenSCAD (Nightly)\openscad.com" --backend=Manifold `
    -o exports\pro-convert-hdmi-tx-panel.stl `
    -D 'part="panel"' -D 'MCC_SHOW_GHOST=true' `
    models\pro-convert-hdmi-tx\case.scad
```

Booleans and numbers don't need the inner-quote treatment string values do (`-D 'MCC_SHOW_GHOST=true'`
is fine as-is); only string-typed top-level variables (like `part`) need the `'name="value"'` pattern
from the main invocation example above.

## Quick troubleshooting

| Symptom | Likely cause |
|---|---|
| `Can't open module file` | `OPENSCADPATH` not set, or BOSL2 submodule not checked out |
| Geometry renders but bbox assert fails | A device/panel dimension changed upstream without the model being re-checked — not a rendering bug |
| CSG smoke test (`-o out.csg`) passes but STL render hangs/crashes | Tessellation-only issue — likely a degenerate/self-intersecting shape that Manifold accepts as CSG but chokes on when meshing; zoom into the specific module with a minimal repro file |
| `-D` value silently ignored | Used identifier syntax (`part=base`) instead of string syntax (`part="base"`) — see the invocation example above |
| Render succeeds locally but CI's render step fails | Almost always a BOSL2 SHA drift — confirm the pinned SHA in the submodule config matches what CI checks out, and that `doctor` passes locally against the same SHA |
| `--summary-file` written but empty/malformed JSON | The render itself errored after summary collection started (e.g. an assert failure mid-tree) — check stdout for an `ERROR:` above the summary line, don't trust the JSON's mere existence as a success signal |
