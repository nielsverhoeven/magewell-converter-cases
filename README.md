# magewell-converter-cases

3D-printable, rugged, single-device cases for Magewell Pro Convert NDI converters used in live
performance. Every external connection leaves the case through a panel-mount connector — Neutrik
D-series, black `-B` finish wherever a `-B` option exists — with a short internal patch cable to
the device. Models are written in OpenSCAD + BOSL2, rendered headlessly, sliced in Bambu Studio,
and printed in ASA on a **Bambu Lab X1 Carbon** (256 × 256 × 256 mm, enclosed) — the target
printer; every part must fit and print on it.

The case is sized by the *connectors*, not the device: a Neutrik D flange needs 60–76 mm of clear
depth behind the panel for its mating plug, while the devices themselves are only 23–24 mm tall.
That inversion drives most of the design decisions recorded in
`.claude/knowledge/architecture.md` — read that file before touching anything under `lib/mcc/` or
`models/`.

## Status

**All eight priority cases are implemented** (`models/<slug>/case.scad`): Pro Convert HDMI TX,
SDI TX, HDMI Plus, SDI Plus, and the NDI decoders to HDMI, HDMI 4K, SDI and AIO. Compact-family
cases are ≈ 194–195 × 159–160 × 51 mm, Plus-family cases ≈ 210–212 × 165–166 × 51 mm with a
Noctua NF-A4x10 fitted by default. Every merge to `main` publishes a pre-release with one zip per
device (STL + 3MF + STEP + manifest) — see "Releases" below. **Every dimension below `measured`
confidence is still `assumed`/`photo`**: the next step is physical — print and measure the six
calibration coupons (`models/coupons/*.scad`) on the X1 Carbon, measure the device's side 1/4"-20
hole, the PoE splitter and the E-clip, write the values into `lib/mcc/constants.scad`, then print
the first full case. See `.claude/knowledge/session-resume.md` for the ordered plan.

## Repo map

| Path | What |
|---|---|
| `knowledge/` | Sourced, cited domain research: Magewell device dimensions, Neutrik connector drawings, fasteners, fans, PoE splitters, FDM/thermal design guidelines. Stable; never invent a figure here — see the `knowledge-lookup` skill. |
| `lib/mcc/` | The case-building library: constants, port-map accessors, shell/panel/cradle/mounts/vents modules, per-device data files (`lib/mcc/devices/`). Layered per `.claude/knowledge/architecture.md` §3. |
| `lib/BOSL2/` | [BOSL2](https://github.com/BelfrySCAD/BOSL2), git submodule, pinned SHA. |
| `models/coupons/` | Small printable test parts that calibrate fit (tongue-and-groove clearance, heat-set boss sizing, connector cutout fit, bay depth) before any full case is trusted. |
| `models/<slug>/` | One directory per Magewell device SKU; `case.scad` exports `base`/`lid`/`panel` by `-D part=`. |
| `scripts/` | The build/render/test tooling — `build.py` (the implementation) and `render.ps1` (a thin Windows wrapper). See `scripts/README.md`. |
| `tests/` | Smoke tests (`test_*.scad`) and geometry goldens (`tests/golden/`). See `tests/README.md`. |
| `exports/` | Gitignored. Local render output only — never committed; see `.claude/knowledge/architecture.md` §8. |
| `.claude/` | Agent working memory: `.claude/knowledge/` (architecture, testing policy — distinct from the sourced `knowledge/` above) and `.claude/skills/`. |

## Tool install

```powershell
winget install --id OpenSCAD.OpenSCAD.Nightly --exact
winget install --id Bambulab.Bambustudio --exact
```

This repo pins the OpenSCAD **nightly** build (not stable) because it needs the Manifold CSG
backend. The exact version string in use is recorded in every export's manifest and in
`.claude/knowledge/architecture.md` §2.

## Setup

```powershell
py -3 -m venv .venv
.venv\Scripts\python -m pip install -r requirements.txt
```

If the venv's `ensurepip` also fails (a broken global Python install can do this even though the
venv itself is otherwise unaffected):

```powershell
.venv\Scripts\python -m ensurepip --upgrade
.venv\Scripts\python -m pip install -r requirements.txt
```

## Quick start

```powershell
.venv\Scripts\python scripts\build.py doctor                    # resolved tool paths/versions, discovered targets
.venv\Scripts\python scripts\build.py render coupons\neutrik-tile
.venv\Scripts\python scripts\build.py smoke                     # Tier-2 headless asserts
.venv\Scripts\python scripts\build.py all                       # smoke -> render --all -> check --all -> golden -> review
.venv\Scripts\python scripts\build.py review                    # exports\review.3mf: every design in one Bambu Studio project
```

Or equivalently via the wrapper: `scripts\render.ps1 doctor`, etc. Full command reference in
`scripts/README.md`.

## Releases

Every merge to `main` triggers `.github/workflows/release.yml`, which computes the next `vX.Y.Z`
from [Conventional Commits](https://www.conventionalcommits.org/) since the last release, builds
and tests everything (including STEP export), tags `main`, and publishes a GitHub Release —
**there is no manual tagging step**. Each release ships three kinds of asset, all with unique,
self-describing names (with eight-plus device cases, the pre-v0.1.0 release's bare `base.step` /
`lid.step` / `panel.step` names collided across models — GitHub release assets must be unique
repo-wide, see issue #10):

- **`<device-slug>-vX.Y.Z.zip`** — one per case (e.g. `pro-convert-for-ndi-to-hdmi-v0.1.0.zip`),
  containing that model's `.stl`, `.3mf`, `.step`, and `.manifest.json` for every part
  (base/lid/panel), plus a `README.txt` naming the device, the version, and the git SHA. Also
  `coupons-vX.Y.Z.zip`, with every calibration coupon's exports.
- **`<slug>-<part>.step`** — every part's STEP file again, loose (not zipped), named
  `<device-slug>-<part>.step` for a case (e.g. `pro-convert-for-ndi-to-hdmi-base.step`) or
  `coupons-<coupon-name>.step` for a coupon (e.g. `coupons-neutrik-tile.step`) — for anyone who
  wants a single part in another CAD tool without downloading the whole zip.
- **`SHA256SUMS.txt`** — one `<sha256>  <relative/path>` line per asset above, to verify a
  downloaded file wasn't corrupted or tampered with.

**A release is marked pre-release** on GitHub whenever any device still has a port below `measured`
confidence — true for every device today (nobody has physically measured a port position yet, see
`.claude/knowledge/architecture.md` §7). Download from this repository's
[Releases page](../../releases); pick the `<device-slug>-vX.Y.Z.zip` for the case you want to print,
or `coupons-vX.Y.Z.zip` to print the calibration coupons first (recommended — see "Coupons before
cases" below). Full release-flow detail: `CONTRIBUTING.md`'s "Release" section.

## Open in Bambu Studio

Every `.3mf` in a release is a **ready-to-slice Bambu Studio project** — no re-orienting, arranging
or profile picking needed:

1. Open the device zip's **`<device-slug>.3mf`** (double-click, or **File → Open Project**,
   `Ctrl+O`). It holds the whole case: base + connector panel on plate 1, lid on plate 2, each part
   already in its print pose — base and lid **open side up**, panel **connector face down** (flat on
   the bed; `.claude/skills/print-check/SKILL.md` §3 explains why).
2. The project already selects **Bambu Lab X1 Carbon 0.4 nozzle**, **Bambu ASA** and
   *0.20mm Standard @BBL X1C* with the repo's edits (5 walls, 8 mm outer brim — shown as a modified
   preset). Sync your AMS slot if needed, keep the enclosure closed (ASA), **Slice all**.
3. Want a single part? Open `<part>.3mf` instead (one plate). Another slicer? Use `<part>.stl` — same
   print pose, already sitting on the bed centre.
4. `<part>.step` is in the **assembly frame** (the parts mate when imported together) for other CAD
   tools. It is a faceted B-rep converted from the mesh — good as a reference body or for fit
   checks, not a parametric, editable model (OpenSCAD has no B-rep kernel).

**Check every generated design at once:** `python scripts/build.py review` (after `render --all`)
writes `exports/review.3mf` — every case (each on its own plates) plus all coupons and brackets in
one Bambu Studio project; each release also carries it as `review-vX.Y.Z.3mf`. Open it, **Slice
all**, and every plate should slice without a "floating regions" or exclusion-area warning —
`build.py check` gates the same floating-island / cantilever conditions in CI
(`scripts/printability.py`), and `build.py slicer-check` slices every part headlessly with Bambu
Studio's CLI and fails on any slicer warning — the ground truth. CI runs that slicer gate on every PR
(pinned Bambu Studio 02.08.02.61 AppImage), so nothing that Bambu Studio would flag reaches `main`;
run it locally too before pushing print-facing changes.

See `.claude/skills/print-check/SKILL.md` for the full pre-slice checklist (orientation, ASA
profile hints, coupons-before-cases).

## Design decisions

The full rationale — layered module architecture, why the connector panel is a separate printed
plate, the port-map data contract, the export/versioning policy, the 4-tier test policy, and the
open risks (build-plate fit, unverified plug lengths, thermal/PoE budget) — lives in
[`.claude/knowledge/architecture.md`](.claude/knowledge/architecture.md). The underlying sourced
component/device research lives in [`knowledge/README.md`](knowledge/README.md) and its
subdirectories.

## A rule worth repeating here

**Always use the black `-B` finish for Neutrik parts.** Every panel connector in the BOM and every
device data file's `panel` field should resolve to a `-B` part number (e.g. `NE8FDP-B`, not
`NE8FDP`), no exceptions.

## License

[CC0 1.0 Universal](LICENSE) — public domain dedication. See the `LICENSE` file for the full
legal text.

## Contributing

- Docs and code comments in English.
- Never invent a dimension. If a figure isn't in `knowledge/**`, it's `unknown` — say so, cite
  where you looked, and use the `knowledge-lookup` skill to resolve it or flag it for measurement.
- Coupons before cases: a fit/fastener/cutout parameter is trusted only after the corresponding
  `models/coupons/*.scad` part has been printed and measured, per
  `.claude/knowledge/architecture.md` §9 Tier 4. Don't skip straight to a full case with an
  `assumed`-confidence clearance.

## Branching

This repo uses a simplified Git Flow: `main` is the only long-lived branch (integration and release
both), and everything else — including urgent fixes — is a short-lived `feature/*` branch merged in
via PR. Releases are annotated `vX.Y.Z` tags on `main`, created **automatically** on every merge —
see "Releases" above. Never commit directly to `main`. See [`CONTRIBUTING.md`](CONTRIBUTING.md) for
the full model, step-by-step recipes, and how to verify an automatic release after merge.
