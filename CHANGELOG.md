# Changelog

All notable changes to this project are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and this project
adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html) — see `CONTRIBUTING.md` for
what MAJOR/MINOR/PATCH mean for a hardware/geometry repo (MAJOR = previously printed parts become
incompatible, MINOR = a new case variant/coupon/feature, PATCH = a fix that doesn't change a golden).

Releases are GitHub Releases built from annotated `vX.Y.Z` tags on `main` — see
`.github/workflows/render.yml` and the release checklist in `CONTRIBUTING.md`.

## [Unreleased]

### Changed (2026-10-04, issue #120, user decision) — MAJOR: printed arch-bracket arms and centres do not mate with the new ones

- **The arch TV bracket is straight** (#120, architecture.md D120.1, D120.2, D120.3): rise 0 in direct and
  sandwich mode, both arms lie along the top VESA 400 row and the rail centre sits on the screw line;
  same five parts, the case still hangs patch-wall down. `arm` and `arm_sandwich` are 140 mm long
  (was 167.2), `centre` and `centre_sandwich` are 220 mm wide (was 238.1) with straight tabs. Old arms
  (lap at 132.2 mm) do not fit the new centre. The arm/centre goldens change, the spacer's does not.
  The parts no longer depend on `TV_TOP_CLEAR`; T1-49 and T1-50 are retired, T1-48 is the validity
  gate and T1-120.1 checks the arm axis.

### Changed (2026-09-29, issues #63–#65, user decisions) — MAJOR: printed bases and brackets are not interchangeable

- **The rail lock moves on top of the dovetail** (#63, architecture.md D63.1): two rigid 0.6 mm strips on
  the male rail's top drop into one full-width slot in the case groove's roof (backed by extra floor
  material); the D48 flank bump and pocket are gone. Remove a case by pulling it about 1 mm away from
  the TV and sliding it off. The groove entry's 1 × 45° lead-in now chamfers the roof too.
- **The groove's closed end is closed** (#64, D64.1): the rail is 136 mm (was 150) and the case sill keeps
  a full 3 mm end wall behind the groove's −X end; before, the groove opened into the case between 3 and
  4 mm above the floor. The sill now clears the reserved PoE-splitter bay by ≥ 2 mm on every SKU (D45).
- **No zip-tie slots in the floor** (#65, D65.1): the PoE-splitter tie-down slots are removed from every
  base (`mcc_splitter_tiedown()` retired); the splitter bay stays reserved.

### Fixed (2026-09-29, issue #66)

- `build.py check` measures a cantilever's reach on an outline stripped of collinear mesh vertices
  (architecture.md D66.1): no false alarm from triangulation vertices on a straight bridge edge.
  `build.py smoke` runs a self-test that still fails a real 6 mm cantilever.

### Fixed (2026-09-29, issue #62, external CAD review of `lid.step`) — MAJOR: a base and a lid printed on either side of this change do not mate

- **Lid thumbscrew holes had openings** (architecture.md D62.1): on all 8 SKUs the 3 patch-wall-side
  holes (the two (±X, +Y) corners and the patch-wall middle one) had a see-through opening in the Ø8
  counterbore floor, 11.4 mm² each, where the lid's groove crossed the counterbore. The
  tongue-and-groove frame on the +Y patch wall now sits 4.5 mm from the outer face
  (`MCC_TG_PATCH_INSET`) in both the base (tongue) and the lid (groove), clear of the counterbores. The
  other three walls and every fastener, boss and insert position are unchanged. No full case has been
  printed yet.
- New guards: asserts T1-62.1 (counterbore-to-groove web) and T1-62.2 (patch inset range); `build.py
  check` and the `ci` part gate fail a case lid with an accidental see-through opening; `build.py smoke`
  runs a self-test of that check.

### Changed (2026-09-29, issue #62, user decision) — the lid thumbscrews are not captive

- The 6 lid thumbscrews are **non-captive** M3 knurled thumbscrews with a small Ø7–8 mm head recessed in
  the Ø8 counterbore (architecture.md D62.2); the model never retained them, so no geometry changes.
  `mcc_captive_thumbscrew_hole()` is renamed `mcc_thumbscrew_hole()`. BOM: ≤ 8 mm under the head (M3×6
  recommended) — the earlier "assumed M3×10" would bottom out in the insert bore.

### Changed (2026-09-29, issue #68, user rule) — record ids follow GitHub issues

- Every feature, bug and task gets a GitHub issue first, and the decisions, risks, measurements, open
  questions and Tier-1 asserts it creates are numbered after it (D62.1, T1-62.1, …). `architecture.md`
  no longer has revision numbers. Existing ids (D1–D52, rev ≤ 19, T1-01–T1-90, R1–R47, M1–M22, Q1–Q23)
  are unchanged. Branches are always `feature/issue-<n>-<topic>` (CLAUDE.md, CONTRIBUTING.md).

### Removed (2026-09-29, end-stop remnants)

- `MCC_RAIL_END_STOP_L`/`MCC_RAIL_END_STOP_H` and the arch bracket's `RAIL_X` rail offset — all zero
  since the end-stop flange was retired (D34) — are gone, with the comments that still described that
  flange (architecture.md D52). The arch (T1-53) and vertical (T1-76) rail-containment asserts now take
  the rail's X extent from `mcc_rail_male_keepout()`, and the arch's in-code print gate matches
  `models/brackets/README.md`. No geometry change; every golden is unchanged.

### Added (2026-09-28, issue #56)

- **Vertical VESA-column bracket** (`models/brackets/vertical-tv-bracket.scad`, architecture.md rev 18):
  sandwiched between a Samsung TV (VESA 400 × 300) and its own TV lift on one column, case outboard of
  the +X column; one arm printed twice, a centre carrying the rail, two printed ASA spacers for the
  other column.
- **Arch bracket sandwich parts** (`arm_sandwich`, `centre_sandwich`, `spacer`, D51) beside the
  unchanged direct parts: flat clamp pads, ribs clear of the lift's rail, a taller centre so the
  slide-on clears the lift's rail and bolt head (M3×18 lap screws).

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
- **STEP files carry real circles** (D39): the STEP is rebuilt from OpenSCAD's CSG tree
  (`scripts/csg_to_step.py`), so holes and roundings are true cylinders/arcs in CAD instead of
  dozens of flat facets. The faceted mesh converter remains only as a reported fallback.
- **Perfectly round connector holes** (architecture.md D40): the D-connector seat hole and window in
  the patch wall are plain circles again (D36's teardrops are gone) — in the model, the STL and the
  STEP.
- **No printed thread** (D41): each connector's two screw holes are a plain Ø2.5 mm M3×0.5 tap-drill
  bore; the thread is modelled in CAD from the STEP. The `m3-thread-ladder` coupon is retired. How a
  printed case gets its thread is still open (architecture.md §12 Q20).
- CI: a case part whose STEP falls back to the faceted converter now fails `build.py ci`.
- **Wide, flush mount rail** (architecture.md D44, user decision 2026-09-28): the dovetail's root is
  65 mm (was ≈14.6 mm) at `MCC_RAIL_Y` = −23.5, the case's exterior floor sits flush on the bracket
  plate (the rail's 3 mm pedestal is gone), and every non-bearing face of the joint keeps ≥ 0.5 mm
  clearance. Brackets and cases printed before this change do not mate with ones printed after it.
  The arch bracket's plates are 11 mm (was 8), its centre 92 mm wide (was 40), and its lap screws
  M3×12 (was M3×10).
- **Floor reservations dropped** (D44): the Magewell-Fishtail M4 band and the 1/4"-20 insert keep-out
  are gone — the rail covers the floor centre. `tripod_insert` now requires `["rail", false]`.
- `rail-latch` coupon: the groove half now prints standing on the bed with its groove open, like the
  case floor (it used to be sealed by the shared base plate, D46).

### Removed (2026-09-28)

- **`tv-bracket`** — the VESA 100/200 sandwich plate (issue #26) — is retired (architecture.md D47,
  user decision 2026-09-28): a mated case covered the VESA mount interface it was sandwiched to. The
  arch bracket stays as the horizontal option; a vertical VESA-column bracket is planned.
  `MCC_BRACKET_PLATE_T` goes with it.

### Changed (2026-09-28, gravity lock)

- **The rail lock is a gravity lock** (architecture.md D48, user decision 2026-09-28): a rigid 0.7 mm
  bump on the rail's upper flank drops into a pocket in the case groove's flank and is held there by
  the case's own weight. It replaces the D34 snap latch (arm, plate window, nub and notch are gone):
  nothing flexes; remove a case by lifting it about 1 mm and sliding it back off. Brackets and cases
  printed before this change do not mate with ones printed after it.
- **The groove entrance has a 1 × 45° lead-in** where it leaves the case's +X wall (D48).
- **A mounted case always hangs patch-wall down** (D49) — the lock depends on it.
- Brackets read the rail's plate-side keep-out from `mcc_rail_male_keepout()` and union the rail on
  with no plate cut (D50). The arch bracket's rail no longer cuts its centre plate.
- Coupon `rail-latch` is now `rail-lock` (tests the lock hanging, plus an e-ladder).

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
