# Changelog

All notable changes to this project are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and this project
adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html) — see `CONTRIBUTING.md` for
what MAJOR/MINOR/PATCH mean for a hardware/geometry repo (MAJOR = previously printed parts become
incompatible, MINOR = a new case variant/coupon/feature, PATCH = a fix that doesn't change a golden).

Releases are GitHub Releases built from annotated `vX.Y.Z` tags on `main` — see
`.github/workflows/render.yml` and the release checklist in `CONTRIBUTING.md`.

## [Unreleased]

### Changed (modeller feedback, 2026-09-28) — MAJOR: printed panels/bases are not interchangeable

- **No separate connector panel** (architecture.md D36): the connectors mount straight into the
  base's patch wall — 3 mm bezel recess, 2 mm flange seat with a teardropped hole, and printed M3
  threads in the wall itself. The panel part, its rabbet, the 4 plate-retention inserts/screws and
  the lid's patch-wall lip are gone. This also removes the "screw pillars in the D opening": the
  plate's rear thread pads overlapped every D hole by ~1 mm. `neutrik-tile` is now a standing
  section of that wall.
- **No floor insert** (D35): the case's own 1/4"-20 floor insert boss is off in every variant; the
  side bolt is the only screw.
- **No floor-pad island** (D37): the unexplained 40 × 40 mm square in the cradle was left over from
  the floor EPDM pad that moved to the side-bolt boss long ago.
- **Lid-boss webs** (D38) are as wide as the boss and merge into it; they used to touch it only
  along a tangent line.
- Material: base + lid ≈ 262 g (was ≈ 272 g with the panel).

### Fixed (mount rail, issue #46)

- **The mount rail could not be assembled**: the case groove was closed at both ends and the
  bracket rail's end-stop flange would have hit the case floor. The groove now runs out through the
  case's +X wall (closed −X end = end stop, flange retired), and the latch is redesigned as a
  printable in-plane snap arm cut from the rail's flank that snaps into a notch in the groove
  (architecture.md D34). Goldens of every base, the tv-bracket, the arch-tv-bracket centre and the
  rail-latch coupon change accordingly.

### Added (agent workflow)

- `bambu-studio` skill + `scripts/slicer_probe.py zbisect|box|critical`: locate a Bambu Studio
  warning on one part through the real slicer; `.claude/knowledge/bambu-slicer.md` records the
  empirical slicer rules, design rules and debugging workflow learned on 2026-09-27/28.
- `// build.py: print_count = <part>:<n>` marker: part projects and `review.3mf` carry the number
  of copies one assembly needs (arch-tv-bracket arm: 2).

### Added (CI)

- Bambu Studio slicer gate in the required `render` check: every exported part is sliced by the
  pinned Bambu Studio 02.08.02.61 Linux AppImage (`.github/actions/setup-bambu-studio`) and any
  slicer warning fails the PR. The gate runs as six parallel "Validate parts — group k of 6" jobs, pipelined per
  part (`build.py ci --group k/6`: render → check → golden → slicer → STEP), with smoke in its own
  parallel job; the `render` status check is now an aggregator job.

### Fixed

- **Exports are now usable in Bambu Studio as delivered** (user report 2026-09-27: a senior Bambu
  modeller could do nothing with them). Every `<part>.stl`/`<part>.3mf` is in its print pose on the
  X1C bed (lid and panel were upside-down / floating at assembly height, all parts landed stacked in
  the exclusion zone); each `.3mf` is a real Bambu Studio project (X1C 0.4 + Bambu ASA, 5 walls,
  8 mm outer brim); each case also ships `<slug>.3mf` with the whole print set on its plates; the
  `.3mf` files are actually in the release zips now (`build.py all` used to render STL only).
- "Floating regions" in every base: the upper patch-wall relief left a hanging lip tooth
  (`shell.scad`, D26) and the fan grille had no spoke under its ring bottoms (`fan.scad`, D27).
- "Floating cantilever" in every base, found with headless Bambu Studio slicing: the rail sill had
  knife-edge side walls under a 150 mm groove roof (D30, `MCC_RAIL_SILL_SIDE_W`), the panel-fixing
  bosses stuck straight out of the wall (D29, 45° chin), the cradle pad island hung over open bays
  (D33, skirt), and the 6 mm top bezel lip over the panel could not print (D32: the rabbet is now
  open-topped and the **lid carries the top of the panel frame**).
- `tv-bracket` had no printable pose (ribs on one face, rail on the other): ribs removed (D31).
  `neutrik-tile` now exports flange-down like the panel; `depth-mockup` lost its optional,
  unprintable horizontal screw pads (D29).

### Changed

- Rail spring-lip latch disabled (`MCC_RAIL_LATCH_ENABLED = false`, D28) — it printed in mid-air and
  did not clear the groove; redesign tracked in issue #46.

### Added

- `build.py review` → `exports/review.3mf` (every design in one Bambu Studio project; released as
  `review-<version>.3mf`), a floating-island + cantilever printability gate in `build.py check`
  (`scripts/printability.py`), and `build.py slicer-check` (local headless Bambu Studio slicing). STEP stays in the assembly frame, converted from `<part>.model.stl`.

### Added

- Sourced knowledge base under `knowledge/**` (Magewell device dimensions, Neutrik connector
  drawings, fasteners, fans, PoE splitters, FDM/thermal design guidelines) and repo working memory
  under `.claude/knowledge/**` (`architecture.md`, `testing.md`, `ticket-source.md`).
- Tooling: `scripts/build.py` (doctor/render/smoke/check/golden/all) and the `scripts/render.ps1`
  Windows wrapper, plus the pinned OpenSCAD nightly + BOSL2 submodule setup.
- `lib/mcc/constants.scad` (L0 constants layer); the L1/L2 geometry library and per-device data
  files are the next milestone (not yet written).
- Coupon plan: `neutrik-tile`, `depth-mockup`, `tg-ladder`, `insert-boss`, `tolerance-ladder` —
  required before any full case is printed, per `.claude/knowledge/architecture.md` §9 Tier 4.
- Claude Code skills: `knowledge-lookup`, `openscad-authoring`, `openscad-render`, `neutrik-panel`,
  `device-portmap`, `new-case-variant`, `print-check`, `bom-update`, and `git-flow`.
- CI: `.github/workflows/render.yml` — renders every discovered coupon/model, runs the 4-tier test
  suite, uploads exports, and (on a `v*` tag) creates a GitHub Release with the release gate
  (fails on any `WARNING: unmeasured port`).
- Simplified Git Flow: feature branches → main, releases via tags — `CONTRIBUTING.md`,
  `.github/pull_request_template.md`, the `git-flow` skill, and the CI trigger set for `main`
  and `v*` tags.
- STEP export: `scripts/mesh_to_step.py` (STL → B-rep STEP, `cadquery-ocp` preferred backend with
  a FreeCAD `freecadcmd` fallback; coplanar facets merged via `ShapeUpgrade_UnifySameDomain`,
  curved surfaces stay faceted) and `scripts/build.py step`/`step --all`/`all --with-step`.
- Automated per-push releases: `.github/workflows/release.yml` computes the next `vX.Y.Z` from
  Conventional Commits (`scripts/release_version.py`), builds everything, packages one zip per
  device case plus a coupons zip (`scripts/package_release.py`), creates the annotated tag, and
  publishes a GitHub Release — marked pre-release while any port is below `measured` confidence
  (`scripts/build.py confidence`). Manual `v*` tagging is no longer needed.
- `.github/actions/setup-openscad` composite action, factored out of `render.yml` so `render.yml`
  and `release.yml` install the pinned OpenSCAD nightly identically.
- `render.yml` also runs `build.py step --all` on every PR, so a broken STEP conversion fails the
  PR; the tag-triggered release step moved out of `render.yml` into `release.yml`.
- Fan power scheme (D-14): the case fan is powered from the device itself, not a PoE splitter —
  decoders draw 5 V from their own USB-A host port (now blanked with `DBA-BL-B`, which carries a
  full D hole so the slot stays convertible), encoders from Mini-DIN-8 pin 8 VCC / pin 4 GND, each
  in series with a KSD9700 45 °C thermoswitch, with no splitter fitted by default on any SKU.
- TV bracket (issue #26): `models/brackets/tv-bracket.scad` — a VESA 100×100/200×200 sandwich
  plate that sits between a TV's own back panel and its existing wall/stand mount, carrying the
  male mount rail (`lib/mcc/rail.scad`, issue #25) so a case clicks onto it tool-less. New
  `scripts/build.py` `discover_brackets()` (registered in both `discover_all()` and
  `cmd_doctor()`), `models/brackets/README.md`, `tests/golden/brackets/tv-bracket.json`, a
  `## Mounting brackets` section in `BOM.md`, a `dist/brackets-<version>.zip` in
  `scripts/package_release.py`, `MCC_M8_CLR_D`/`MCC_BRACKET_PLATE_T`/`MCC_RIB_HEIGHT_RATIO_MAX` in
  `lib/mcc/constants.scad`, and a one-line orientation note in
  `.claude/skills/print-check/SKILL.md`.

<!-- No Changed / Deprecated / Removed / Fixed / Security entries yet. Keep a Changelog convention:
     add a subsection only once it has an entry; don't carry empty headings forward release to
     release. -->

## Releases

No versions have been tagged yet. The first tagged release will start the `[X.Y.Z] - YYYY-MM-DD`
section list below, oldest at the bottom, per Keep a Changelog convention.
