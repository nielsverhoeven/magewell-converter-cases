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

**First full case implemented: `pro-convert-for-ndi-to-hdmi`** (compact family, 193.9 × 159.85 ×
51.0 mm). The L0/L1 library (`lib/mcc/**`: constants, ports, layout solver, Neutrik cutout,
fasteners, fan, PoE-splitter envelope, ghost, panel dispatcher) and the L2 geometry (`shell.scad`,
`cradle.scad`, `mounts.scad`, `vents.scad`) now exist alongside 8 device data files and the 6
physical calibration coupons (`models/coupons/*.scad`, with goldens); `build.py all` is green
(smoke/render/check/golden). Next: print and measure the coupons and the first case on the X1
Carbon (every dimension below `measured` confidence is still `assumed`/`photo`), then the
remaining 7 per-device case assemblies. See `.claude/knowledge/session-resume.md` for the ordered
plan.

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
.venv\Scripts\python scripts\build.py all                       # smoke -> render --all -> check --all -> golden
```

Or equivalently via the wrapper: `scripts\render.ps1 doctor`, etc. Full command reference in
`scripts/README.md`.

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
via PR. Releases are annotated `vX.Y.Z` tags on `main`. Never commit directly to `main`. See
[`CONTRIBUTING.md`](CONTRIBUTING.md) for the full model, step-by-step recipes, and the release
checklist.
