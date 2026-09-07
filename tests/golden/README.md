# tests/golden/

Small, diffable JSON snapshots of measured geometry — bbox, volume, surface area, and triangle
(facet) count — for every rendered coupon/model part. Committed to git (unlike `exports/**`,
which is gitignored scratch output — see `.claude/knowledge/architecture.md` §8). Their whole
purpose is to catch an *unintended* geometry change in code review: a golden diff in a PR is a
geometry diff, readable without opening OpenSCAD.

## What a golden file is

One file per `(target, part)`, written by `scripts/build.py golden --update`:

```json
{
  "bbox": { "min": [...], "max": [...], "size": [...] },
  "volume_mm3": 12345.6,
  "area_mm2": 7890.1,
  "facets": 3421
}
```

`bbox`/`facets` come straight from OpenSCAD's own `--summary all --summary-file` output for the
part (pre-tessellation facet count from the CSG tree). `volume_mm3`/`area_mm2`/`facets` are
computed from the exported mesh by trimesh, because the pinned OpenSCAD nightly
(`2025.09.07`) does not populate a volume or surface-area field in its own summary JSON for 3D
solids — confirmed by direct testing, not merely assumed. `check_mesh`/`golden` in
`scripts/build.py` are the single place this augmentation happens.

## File naming

`tests/golden/<target>.json` when the part name equals the target's own basename (this is always
true for coupons, whose single part is named after the file stem), otherwise
`tests/golden/<target>.<part>.json`. A target name may itself contain a `/` (e.g.
`coupons/neutrik-tile`), which becomes a real subdirectory under `tests/golden/`. Examples:

| Target | Part | Golden path |
|---|---|---|
| `coupons/neutrik-tile` | `neutrik-tile` | `tests/golden/coupons/neutrik-tile.json` |
| `pro-convert-hdmi-tx` | `base` | `tests/golden/pro-convert-hdmi-tx.base.json` |
| `pro-convert-hdmi-tx` | `lid` | `tests/golden/pro-convert-hdmi-tx.lid.json` |

## Tolerance policy

| Field | Tolerance | Failure kind |
|---|---|---|
| `bbox.size`, per axis | ± 0.1 mm absolute | hard failure |
| `volume_mm3` | ± 0.5% relative | hard failure |
| `area_mm2` | ± 1% relative | hard failure |
| `facets` | — | informational only, printed but never fails the comparison |

Facet count is excluded from pass/fail because mesh tessellation can shift the triangle count for
reasons that don't reflect an intended geometry change (e.g. a `$fn`/`$fa`/`$fs` change on an
unrelated curved feature elsewhere in the same part, or an OpenSCAD/Manifold version bump). The
other three fields are exactly the ones that catch a real, unintended change to *this* part's
shape.

A missing golden is a **failure**, not a skip — `golden --update` is the only way to create one,
and doing so is a deliberate act that should be visible in the diff.

## Updating a golden

```
python scripts/build.py render coupons/neutrik-tile   # produce a fresh exports/**/*.summary.json
python scripts/build.py golden --update coupons/neutrik-tile
```

Omit the target to update every discovered target's golden at once. `--update` always overwrites;
there is no interactive confirmation.

**A golden change must be justified in the PR.** State in the PR description *why* the geometry
changed (e.g. "widened the etherCON boss per the neutrik-tile coupon print, +0.4mm bay depth") —
a reviewer should never have to reverse-engineer intent from a bbox/volume diff alone. A golden
update with no stated reason is a review blocker, not a rubber stamp.
