---
name: bambu-studio
description: Drive Bambu Studio for this repo — headless slicing via its CLI (slicer-check, the CI slicer gate), locating a "floating regions"/"floating cantilever" warning with scripts/slicer_probe.py, opening projects in the GUI for the user to review, refreshing the project-settings dump and the pinned version; use whenever a part must be validated in, debugged with, or shown in Bambu Studio.
---

# bambu-studio

Every exported part must slice in Bambu Studio **without a single warning** (architecture.md §8
rev 13). This skill is the operating manual for the slicer side; the *why* behind each rule and
the history of real fixes are in `.claude/knowledge/bambu-slicer.md` — read its §1–§2 before
changing geometry.

## 1. Where Bambu Studio is

| Environment | How `build.py` finds it |
|---|---|
| This Windows PC | `C:\Program Files\Bambu Studio\bambu-studio.exe` (default in `build.find_bambu_studio()`) |
| CI (ubuntu-latest) | `.github/actions/setup-bambu-studio`: pinned AppImage, sha256-checked, cached, extracted once, wrapper under `xvfb-run -a` → `MCC_BAMBU_STUDIO` |
| Anywhere else | set `MCC_BAMBU_STUDIO` to the executable (or a wrapper script) |

Pinned version: **02.08.02.61** — the same version `scripts/bambu_project.py BAMBU_VERSION` and
`scripts/bambu/x1c-0.4-asa.project_settings.json` are made for. Bump all three together (§6).

## 2. Validate (the everyday commands)

```
.venv\Scripts\python scripts\build.py slicer-check                      # every part, serial
.venv\Scripts\python scripts\build.py slicer-check <target> --jobs 3    # one target, parallel
.venv\Scripts\python scripts\build.py ci --group k/6 --no-step          # reproduce one CI part group
```

- Input is `exports/<target>/<part>.3mf` — run `render` first (or download CI artefacts, §5).
- Output per part: PASS/FAIL, grams, print hours, and Bambu's own `warning_message`.
- Only **one** warning is reported per plate — fixing one can reveal the next; re-run until clean.
- A hung CLI process is retried once (`SLICE_TIMEOUT_S`); a second hang is reported as a failure.
- CI runs the same gate on every part in the six "Validate parts — group k of 6" jobs; a warning
  fails the required `render` check.

Raw CLI (what `slicer_check_project()` runs — never call it without a timeout, it can hang):
```
bambu-studio.exe --slice 0 --outputdir <tmpdir> <project.3mf>     # cwd=<tmpdir>
```
The GUI exe prints nothing; read `<tmpdir>/result.json` (`sliced_plates[].warning_message`,
`.filaments[].total_used_g`, `.total_predication` s). It also writes a `result.json` into its
working directory — always run it with `cwd` set to a temp dir.

## 3. Locate a warning (do not reason from first principles — measure)

```
cd scripts
..\.venv\Scripts\python slicer_probe.py zbisect  ..\exports\<target>\<part>.model.stl
..\.venv\Scripts\python slicer_probe.py critical ..\exports\<target>\<part>.model.stl
..\.venv\Scripts\python slicer_probe.py box      ..\exports\<target>\<part>.model.stl --z 46.6 --x -40 40 --y 55 81
```

1. `zbisect` → the Z where the warning first appears (~8 slices, ~1 min each for a base).
2. `critical` → re-slices with *critical-regions-only* support and prints where the support goes;
   the top of the support is the underside of the offending feature. Fastest single answer.
3. `box` → halve the XY region until the warning disappears, when 1–2 are still ambiguous.
4. Section the mesh at that Z (`mesh.section` → `to_planar` → shapely; plot with matplotlib) to
   see the feature, then fix it per `.claude/knowledge/bambu-slicer.md` §2.
5. `render <target> --part <p>` → `check <stl>` → `slicer-check <target>` again.

Use `<part>.model.stl` for parts that print as modelled (bases, coupons, brackets); for a flipped
part (lid, panel, neutrik-tile) probe the print STL `<part>.stl` and read coordinates in print pose.

## 4. Show the user (GUI)

The user reviews by opening files in Bambu Studio on this PC. After a change:
```
.venv\Scripts\python scripts\build.py review        # exports\review.3mf: every design, one project
```
Then launch it (it opens as a project with X1C + ASA already selected):
```
Start-Process "C:\Program Files\Bambu Studio\bambu-studio.exe" -ArgumentList '"C:\repos-github\magewell-converter-cases\exports\review.3mf"'
```
Single case: `exports\<slug>\<slug>.3mf`; single part: `exports\<target>\<part>.3mf`. If Bambu
Studio is already running, a second launch opens a second window — fine for review. Driving the GUI
(computer use) is only needed to demonstrate something; for validation always use the CLI.

## 5. Artefacts without a 45-minute local render

Every push to `main` and every PR uploads `exports-part-group-1..6` (render.yml). To refresh local
exports to exactly what CI validated:
```
gh run download <run-id> --dir <tmp>          # the render.yml run of the commit you want
# copy <tmp>/exports-part-group-*/* into exports/, then:
.venv\Scripts\python -c "import sys; sys.path.insert(0,'scripts'); import build; [build.write_model_project(t) for t in build.discover_models()]"
.venv\Scripts\python scripts\build.py review
```
CI writes per-part `.3mf`/`.stl`/`.step`/`.model.stl`; the case projects (`<slug>.3mf`) and
`review.3mf` are built locally from the `.model.stl` files as above.

## 6. Upgrading Bambu Studio

1. Install the new version locally; open any `exports\<part>.3mf`, select *Bambu Lab X1 Carbon 0.4
   nozzle* + *Bambu ASA*, reset the process preset to *0.20mm Standard @BBL X1C*, save the project,
   unzip it and copy `Metadata/project_settings.config` over
   `scripts/bambu/x1c-0.4-asa.project_settings.json` (it contains no personal data — check anyway).
2. Bump `BAMBU_VERSION` in `scripts/bambu_project.py`.
3. Re-pin `.github/actions/setup-bambu-studio`: `appimage-url` (the `ubuntu24.04` asset of the
   release) and `sha256` (`gh api repos/bambulab/BambuStudio/releases/tags/<tag> -q '.assets[] |
   select(.name|test("ubuntu24.04")) | .digest'`).
4. `render --all` + `slicer-check --jobs 3`; a new warning after an upgrade is a real finding —
   fix the geometry, do not pin back silently.

## 7. Things that bit us (keep)

- A 3MF opened by drag-and-drop of **STLs** loses print pose/plates/settings — always hand the user
  the `.3mf` projects.
- Bambu warns on geometry clusters, not single faces: a gentle slope can still be a "cantilever";
  holes cut through a bridge turn it into one; sealed cells pass the slicer but fail `check`.
- The X1C exclusion pad (front-left 18 × 28 mm) blocks slicing when a part touches it —
  `bambu_project.layout_plates()` keeps parts clear; never place objects by hand in the writer.
