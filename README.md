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

Each device zip contains `base`, `lid`, and (where the variant has one) `panel`, each as `.stl`,
`.3mf`, and `.step`:

1. **File → Import → Import 3MF/STL/STEP...** (`Ctrl+I`).
2. Pick `base.3mf` and `lid.3mf` — both import **open side up**, exactly as exported; no
   reorientation needed. `panel.3mf` is authored with its outward (connector) face at `Z=0`, the
   *top* of its bounding box (`lib/mcc/panel.scad`'s `mcc_panel_plate()`: "front (outward) face at
   Z=0"), so it imports connector-face-up — rotate it 180° in the slicer so the connector face
   prints **down**, flat on the bed (`.claude/skills/print-check/SKILL.md` §3 for why that
   orientation matters).
3. Select the **Bambu Lab X1 Carbon** printer with the **0.4 mm nozzle**, and a **Bambu ASA** (or
   **Generic ASA**) filament profile. Keep the enclosure closed — ASA needs it.
4. The `.3mf` is plain geometry only — it carries no print settings, supports, or plate layout, so
   there's nothing to strip before applying your own profile. The `.step` is a faceted B-rep (planar
   facets merged into single faces where coplanar; cylindrical/curved surfaces stay faceted, not
   NURBS-fitted) — use it if you want the part in another CAD tool rather than straight in the
   slicer; Bambu Studio can import it too, but the `.3mf`/`.stl` are the tested path.

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
