# Changelog

All notable changes to this project are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and this project
adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html) — see `CONTRIBUTING.md` for
what MAJOR/MINOR/PATCH mean for a hardware/geometry repo (MAJOR = previously printed parts become
incompatible, MINOR = a new case variant/coupon/feature, PATCH = a fix that doesn't change a golden).

Releases are GitHub Releases built from annotated `vX.Y.Z` tags on `main` — see
`.github/workflows/render.yml` and the release checklist in `CONTRIBUTING.md`.

## [Unreleased]

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
- Git Flow branching strategy: `CONTRIBUTING.md`, `.github/pull_request_template.md`, the
  `git-flow` skill, and the CI trigger set for `main`/`develop`/`release/**`/`hotfix/**`/`v*` tags.

<!-- No Changed / Deprecated / Removed / Fixed / Security entries yet. Keep a Changelog convention:
     add a subsection only once it has an entry; don't carry empty headings forward release to
     release. -->

## Releases

No versions have been tagged yet. The first tagged release will start the `[X.Y.Z] - YYYY-MM-DD`
section list below, oldest at the bottom, per Keep a Changelog convention.
