# tests/

Four tiers, cheapest first, per `.claude/knowledge/architecture.md` §9. All of them run through
`scripts/build.py` (see `../scripts/README.md` for the full command reference) — there is no
separate test runner.

## Tier 1 — in-model `assert()`

Free, runs on every render, no separate command. Library modules under `lib/mcc/**` assert their
own contracts (bbox vs. build volume, wall thickness, panel seat thickness, connector pitch,
cutout diameter, bay depth, boss sizing, floor-feature non-overlap, port/cutout correspondence —
see the full table in `.claude/knowledge/architecture.md` §9). A bad parameter fails loudly at
render time instead of quietly at the printer. There is nothing to run here beyond rendering the
model; a failing assert shows up as an `ERROR:` in `scripts/build.py render`'s OpenSCAD output and
a non-zero exit code.

## Tier 2 — headless smoke tests

```
python scripts/build.py smoke
```

Runs every `tests/test_*.scad` with `openscad -o <tmp>.csg`. CSG export evaluates the full tree
(so Tier-1 asserts fire) without tessellating, so it's fast. Each smoke test should instantiate
every public module it covers at its default, minimum, and maximum parameters. Non-zero exit on
any failure; the command prints a pass/fail table naming every test file.

If no `tests/test_*.scad` files exist yet, `smoke` prints a note and exits 0 (nothing to fail).

## Tier 3 — geometry goldens and mesh checks

Two separate checks, both against files rendered by `scripts/build.py render`:

```
python scripts/build.py check --all      # mesh checks (trimesh)
python scripts/build.py golden           # geometry goldens vs. tests/golden/**
```

`check` runs, per STL: `is_watertight`, `is_winding_consistent`, `volume > 0`,
`len(mesh.split(only_watertight=False)) == 1` (exactly one connected shell — catches a rib or
boss that floated free after a parameter change), and a bounding-box ceiling of 244 mm per axis
(`256 mm` build volume − `2 × 6 mm` bed margin; both constants live in one place at the top of
`scripts/build.py`). Automated minimum-wall-thickness measurement is deliberately **not**
attempted in trimesh — architecture.md calls it unreliable. Rely on the Tier-1 assert plus a
visual/slicer check for wall thickness.

`golden` compares bbox/volume/area/facet-count from each render's `<part>.summary.json` against
the committed golden in `tests/golden/**`. See `tests/golden/README.md` for the tolerance policy
and the update workflow.

## Tier 4 — physical coupons

`models/coupons/*.scad`. Non-negotiable and printed *first*, before any full case: `neutrik-tile`,
`depth-mockup`, `tg-ladder`, `insert-boss`, `tolerance-ladder` (see architecture.md §9 for what
each one calibrates). These render and check exactly like any other target
(`python scripts/build.py render coupons/<name>`, `check`, `golden`) — the "physical" part is that
a human then prints and measures the result, and writes the calibrated constant back into
`lib/mcc/constants.scad` with a comment naming the coupon and the date. There is no software
automation for the print-and-measure step itself.

## Running everything

```
python scripts/build.py all              # smoke -> render --all -> check --all -> golden
python scripts/build.py all --release    # same, plus fails on any WARNING: unmeasured port
python scripts/build.py all --with-step  # same, plus STEP export (build.py step --all) at the end
```

This is exactly what CI runs: `.github/workflows/render.yml` runs `all` on every push/PR (`all
--release` on `v*` tag pushes) plus `step --all` separately so a broken STEP conversion fails the
PR; `.github/workflows/release.yml` runs `all --with-step` on every push to `main` as part of
building a release. STEP export is not a fifth test tier — it's release packaging, not a
correctness check — but note that `step` does re-validate the STEP it just wrote (re-reads it via
OCP, or at minimum checks the file starts with `ISO-10303-21`) before calling a conversion
successful. See `scripts/README.md`'s "Release tooling" section and `CONTRIBUTING.md`'s "Release"
section for the rest of the release pipeline (`release_version.py`, `confidence`,
`package_release.py`).

## "Green" means

- `smoke`: every `tests/test_*.scad` ran to completion with no `ERROR:` (or there were none yet).
- `check --all`: every exported STL is watertight, winding-consistent, positive-volume, a single
  connected shell, and within the 244 mm/axis bbox ceiling.
- `golden`: every rendered target's bbox is within 0.1 mm/axis, volume within 0.5%, and area
  within 1% of its committed golden (facet-count differences are printed but never fail the
  check).
- `python scripts/build.py doctor` exits 0 and shows a resolved OpenSCAD path/version, a BOSL2
  submodule SHA, and `trimesh` available — this is the pre-flight check, run it first if anything
  above behaves unexpectedly.
