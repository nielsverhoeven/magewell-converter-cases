# Bambu Studio slicer — how this repo's parts get judged, and how to debug a warning

Agent working memory (not sourced product research). Written 2026-09-27/28 after making every part
slice warning-free (architecture.md §8 rev 13, §13 D26–D33). Bambu Studio **02.08.02.61**, X1C 0.4,
Bambu ASA, the repo's project settings. Read this before touching geometry that prints as an
overhang, and whenever `build.py slicer-check` (or the CI slicer gate) fails.

## 1. The two warnings that matter

Headless slicing writes `result.json`; `sliced_plates[].warning_message` holds **one** message per
plate (the first it finds — fixing one can reveal the next).

| Message | What Bambu actually tests (support off, auto) | Typical cause here |
|---|---|---|
| `…has floating regions…` ("sharp tail") | a connected layer region with no overlap with the layer below — **however tiny** (only regions thinner than ~0.08 mm are ignored) | a downward cusp where two holes meet (D26); the lowest line of a horizontal cylinder sticking out of a vertical wall (D29); a part printed upside down |
| `…has floating cantilever…` | an overhang whose **outer contour vertices** lie > **3 mm** from where it attaches to the layer below. Overhangs of consecutive layers are *clustered*, so a gentle slope that only adds a thin sliver per layer can still form one big cluster | a flat roof/lip hanging off one edge (D32 rabbet lip, D33 pad island), a bridge whose supports turn out to be knife edges or isolated rib crossings (D30), a whole plate sitting on ribs (D31), **holes cut through a bridge region** (D33 vents) |

Empirical facts (tested with synthetic pieces and the real parts, 2026-09-28):

- A flat 6 mm lip off a continuous wall did **not** warn in isolation, but the real patch-wall
  rabbet lip did — context (clustering with neighbouring overhangs) matters. Do not reason from
  first principles; **measure with the slicer** (§3).
- A bridge closed on all sides by walls/ribs is fine. The same bridge with vent holes in it —
  a fixed grid or one hole per bay centre — **is flagged**. Vent sealed cells sideways instead.
- **A plain round hole through a standing wall does not warn** (D40, 2026-09-28): a ⌀24.8 connector
  window through a 5 mm wall section at `NE8FDP-B` sliced clean, and the CI slicer gate covers every
  base. Slicer silence is not print quality — the top ~90° of the arch still overhangs > 45°;
  `neutrik-tile` judges the sag (architecture.md R39, M19).
- Sealed internal voids (a bridge over a fully walled cell) do not bother Bambu, but they fail
  `build.py check` (parts > 1) — they are real trapped-air cavities.
- A hole in the slicer's view of "support needed" goes away when the geometry changes; an
  approximating Python detector (`scripts/printability.py`) catches most cases but not all, and
  is stricter on some bridges. **`slicer-check` is the ground truth**; the Python gate is the fast,
  always-available approximation.

## 2. Design rules that keep parts warning-free (FDM, this repo, print pose)

1. **Know the print pose before modelling.** Shells (base and lid) print open-side-up — the base's
   patch wall standing — and the `neutrik-tile` coupon stands on its foot exactly like that wall
   (D36); brackets print flat on their TV face. Anything that points down in that pose is an
   overhang.
2. **No flat overhang > 3 mm from its support edge.** Either support it on ≥ 2 opposite sides
   (a real bridge ≤ 10 mm, repo rule), give it a ≥ 45° chin/gusset, or move it to a part where it
   prints upright (D32: the top frame of the panel moved from the base to the lid).
3. **Horizontal bosses off vertical walls get a 45° chin** down the wall (shell fixing bosses, D29),
   or are dropped where optional (depth-mockup pads).
4. **Where two holes overlap in a vertical wall, look at the cusp above/below their intersection.**
   A downward-pointing tooth is a floating region; hull the smaller hole to a point of the larger
   one so the roof rises monotonically (D26: relief hulled to the cap's *left* corner — the right
   corner left a cantilevered flat cap).
5. **Blocks resting on a lattice need walls to the floor** under their edges (D33 skirt), and every
   cell that closes must be vented sideways (channels through the ribs), never through the bridge.
6. **A pocket/cut deeper than the floor needs its own side walls** — size added material to the cut
   *plus* walls, never exactly to the cut (D30 sill).
7. **Never leave both faces of a plate with protrusions** (ribs one side, rail the other) — there is
   then no printable pose (D31).
8. **Fan grilles in vertical walls:** a spoke must run straight down through every ring's lowest
   point (D27). Check which way the 2-D frame maps into the wall.

## 3. Debugging a slicer warning fast (proven workflow)

1. `python scripts/build.py slicer-check <target> [--jobs N]` — which parts, which message.
2. **Where (Z)?** Bisect the height: slice the part clipped at `z` (trimesh `slice_plane(cap=True)`,
   `manifold3d` + `mapbox-earcut` from requirements.txt) and halve the interval until the message
   appears/disappears. ~8 slices.
3. **Where (XY) and what?** Re-slice with `enable_support=1` + `support_critical_regions_only=1` in
   `PROCESS_OVERRIDES` and read the G-code: support extrusions (`; FEATURE: Support…`) sit exactly
   under what Bambu considers critical; `; Z_HEIGHT:` gives the layer. The top of the support is
   the underside of the offending feature. (With supports on, the warning disappears — that is
   expected; this is a diagnostic only.)
4. Section the model-frame mesh at that Z (`mesh.section` → `to_planar` → shapely) and plot the
   layers with matplotlib when numbers do not tell the story.
5. Fix in the `.scad`, re-render only that part (`render <target> --part <p>`), re-run 1.
   A single case base renders in ~1.5 min and slices in ~1 min.

Steps 2–3 are `scripts/slicer_probe.py zbisect|box|critical` (see the `bambu-studio` skill §3).

## 4. Running Bambu Studio headless

- Windows: `C:\Program Files\Bambu Studio\bambu-studio.exe --slice 0 --outputdir <dir> <project.3mf>`
  (0 = all plates). The GUI exe prints nothing to the console; read `<dir>/result.json`.
  It also drops a `result.json` in its **working directory** — run it with `cwd=<tmp>`.
- The CLI occasionally **hangs** (seen on thin synthetic lips and once on a panel) — always use a
  timeout; `slicer_check_project()` retries once.
- Linux/CI: pinned AppImage in `.github/actions/setup-bambu-studio` (sha256-verified, cached,
  extracted once, run under `xvfb-run -a`). `MCC_BAMBU_STUDIO` points `build.py` at any install.
- CI layout (render.yml, 2026-09-28): "OpenSCAD asserts (smoke tests)" + six parallel
  "Validate parts — group k of 6" jobs (`build.py ci --group k/6 --jobs 3`: cost-balanced part
  groups, each part pipelined render → check → golden → slice → STEP) + the `render` aggregator
  (the required check — never rename it). Whole gate ≈ 3 min. To reproduce one group locally:
  `build.py ci --group k/6 --no-step` (no local STEP backend on Python 3.14).
- Critical-regions probe settings: `enable_support=1`, `support_critical_regions_only=1`.
- Useful `result.json` fields: `sliced_plates[].warning_message`,
  `sliced_plates[].filaments[].total_used_g`, `sliced_plates[].total_predication` (seconds).

## 5. The project (.3mf) format this repo writes

`scripts/bambu_project.py` mirrors a GUI-saved 02.08.02.61 project: production-extension 3MF,
one `3D/Objects/object_N.model` per object (mesh centred on its bbox, Z from −h/2), build item
transform = plate origin + bed position + h/2; `Metadata/model_settings.config` for names and
`<plate>` membership; `Metadata/project_settings.config` = full X1C + Bambu ASA preset dump with
`PROCESS_OVERRIDES` applied and listed in `different_settings_to_system` (`[process;keys, filament,
printer]`), `wipe_tower_x/y` one entry per plate. Plates sit on a grid: `cols = ceil(sqrt(n))`,
stride `256 × 1.2 = 307.2` mm in X, `−307.2` in Y per row. X1C exclusion pad: front-left
18 × 28 mm (`bed_exclude_area`). To refresh the settings dump after a Bambu update: open any
project in the GUI with X1C 0.4 + Bambu ASA selected, save, unzip, copy
`Metadata/project_settings.config` over `scripts/bambu/x1c-0.4-asa.project_settings.json`, bump
`BAMBU_VERSION` and the CI AppImage pin together.

## 6. Material (measured 2026-09-28, compact case ≈ 272 g, Plus ≈ 296 g)

Process knobs barely move it (infill 10–15 %/gyroid ±1.5 g; 4 vs 5 walls −6 g; 0.28 mm layers
+12 g) because 3 mm walls with 5 perimeters are near-solid. Geometry is where grams are:
floor slab 37 %, outer walls 38 %, interior (cradle/deck, sill, bosses, lid pillars) 25 % of the
base. Candidate savings are listed in the session hand-off (session-resume.md).
