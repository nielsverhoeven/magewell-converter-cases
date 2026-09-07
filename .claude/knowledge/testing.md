# Testing — magewell-converter-cases

Agent working memory (this file lives in `.claude/knowledge/`, not `knowledge/` — see
`architecture.md` §12 Q11 for that split). Read this before touching `tests/**` or
`scripts/build.py`, or before telling a user "the tests pass."

## Project type

Not a web/mobile app. This repo produces **3D-printable CAD models** (OpenSCAD + BOSL2) plus a
Python build/measurement tool. There is no server, no UI, no device/browser e2e suite, and never
will be one for this repo — "testing" here means geometry correctness (does the model evaluate
without asserting, is the resulting mesh sane, has the shape drifted unintentionally) and,
eventually, physical fit (does a real connector screw into a real printed part). If a routing
table elsewhere sends "e2e" or "UI" work to a `tester` agent with Playwright/emulator tooling,
that tooling does not apply here — the closest equivalent is Tier 4 below, which is inherently
manual (print it, measure it, write the number back).

## The four tiers

All driven through **one** implementation, `scripts/build.py` (Windows wrapper: `scripts/render.ps1`,
which must never carry logic of its own — see architecture.md §9 "Command shapes"). Full command
reference: `../../scripts/README.md`. Tier semantics and file layout: `../../tests/README.md` and
`../../tests/golden/README.md`.

1. **Tier 1 — in-model `assert()`.** Free, runs on every render. `lib/mcc/**` modules assert their
   own geometric contracts (bbox vs. build volume, wall thickness, panel seat thickness, connector
   pitch/cutout diameter, bay depth, boss sizing, floor-feature non-overlap, port/cutout
   correspondence). No separate command — a violated assert shows up as `ERROR:` in any `render`
   or `smoke` invocation.
2. **Tier 2 — `python scripts/build.py smoke`.** Runs every `tests/test_*.scad` with
   `-o *.csg` (evaluates the CSG tree, so Tier-1 asserts fire, without tessellating — fast).
3. **Tier 3 — `python scripts/build.py check --all` and `... golden`.** `check` runs trimesh
   mesh checks (watertight, winding-consistent, positive volume, exactly one connected shell,
   bbox ≤ 244 mm/axis) against every exported STL. `golden` compares bbox/volume/area/facet-count
   from each render against a committed snapshot in `tests/golden/**`.
4. **Tier 4 — physical coupons, `models/coupons/*.scad`.** Printed and measured by a human;
   non-negotiable before any full case is printed. The calibrated result is written back into
   `lib/mcc/constants.scad` as a named constant with a comment citing the coupon and the date —
   see "Where calibration results go" below.

## What "green" means

- `python scripts/build.py doctor` exits 0 with a resolved OpenSCAD path/version, a real BOSL2
  submodule SHA, and `trimesh` reported available. This is the pre-flight check — run it first
  when anything below misbehaves, especially after a fresh clone or a BOSL2 submodule update.
- `smoke`: every `tests/test_*.scad` completed with no `ERROR:` (or there are none yet — that is
  not a failure, just an unwritten test).
- `check --all`: every STL under `exports/**` passes all five mesh checks.
- `golden`: every rendered target matches its committed golden within tolerance (bbox ±0.1 mm/axis,
  volume ±0.5%, area ±1%; facet-count differences are printed but never fail the comparison —
  they can shift for reasons unrelated to intended geometry change).
- `all` (`smoke` → `render --all` → `check --all` → `golden`) exits 0. This is exactly what CI
  (`.github/workflows/render.yml`) runs on every push/PR; `all --release` (which additionally
  fails on any `WARNING: unmeasured` in OpenSCAD's output — a port below `measured` confidence
  used for a real cutout) is what runs on `v*` tags.
- A green `check`/`golden` run says nothing about whether a part actually fits a real connector or
  printer — that's what Tier 4 is for. Do not report a case "done" off Tier 1–3 alone.

## The golden policy, in one paragraph

Goldens are committed (`tests/golden/**` is small, diffable JSON: bbox/volume/area/facets), but
the STL/3MF that produced them are not (`exports/` is gitignored — architecture.md §8). A golden
diff in a PR is a geometry diff a reviewer can read without opening OpenSCAD, so it must be
explained in the PR description, not just regenerated and merged silently. Missing golden = hard
failure, never a silent skip; the only way to create or refresh one is
`python scripts/build.py golden --update [target...]`, which is a deliberate, visible act.
Volume/area are computed by trimesh from the exported mesh (the pinned OpenSCAD nightly
`2025.09.07` does not populate those fields in its own `--summary` JSON for 3D solids — confirmed
directly, not assumed), merged into each `<part>.summary.json` alongside OpenSCAD's own
bbox/facet-count fields.

## Where coupon measurements get written back

`lib/mcc/constants.scad` — and nowhere else. Every Tier-4 physical result becomes a named
`MCC_*` constant there (e.g. a calibrated `MCC_CLR_TG` from the `tg-ladder` coupon, a calibrated
`MCC_INSERT_M3` hole diameter from `insert-boss`), with a comment naming the coupon and the
measurement date. `constants.scad` is variables and pure functions only — never a module
(architecture.md §3, a hard rule) — so this is always a value edit, never a geometry edit. Do not
let a "measured" number live only in a coupon's own file or in a PR description; if it isn't in
`constants.scad`, the next case render won't see it.

## No device/browser e2e suite

There is nothing to install, launch, or drive for this repo — no Playwright config, no emulator,
no app to screenshot. If a task description mentions UI/e2e gating (e.g. from a shared team
routing convention), it does not apply here; the equivalent gate is Tier 4 (coupons) plus, later,
a slicer/print-orientation check (the proposed `print-check` skill in architecture.md §10), both
of which are physical-world checks a human performs, not something `scripts/build.py` can run
unattended.
