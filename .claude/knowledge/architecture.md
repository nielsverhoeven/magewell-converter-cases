# Architecture — magewell-converter-cases

Status: **baseline established 2026-09-07, before any OpenSCAD code exists.**
Owner: solution-architect (advisory, read-only w.r.t. production code).
This file is the source of truth for *intended* design. Code that disagrees with it is either a
deviation to be fixed, or an intended evolution to be recorded here — never silently absorbed.

---

## 1. What this repository produces

3D-printable (FDM), rugged, single-device cases for Magewell Pro Convert NDI converters used in live
performance. Every external connection leaves the case through a panel-mount connector (Neutrik
D-series black `-B` wherever one exists) with a short internal patch cable to the device. Models are
written in OpenSCAD + BOSL2, rendered headlessly, sliced in Bambu Studio, printed in ASA.

**The single most important physical fact in this repo:** the case is sized by the *connectors*, not
by the device. A Neutrik D flange is 26 × 31 mm and the connector body plus its mating plug needs
60–76 mm of clear depth behind the panel. The devices are 100.9–117.5 mm long and 23.3–23.4 mm tall.
Every architectural decision below follows from that inversion.

Derived envelopes (from `knowledge/neutrik/placement-and-depth.md` §1/§3 and
`knowledge/magewell/housing-families.md`):

| Quantity | Value | Consequence |
|---|---|---|
| Interior height | **43 mm** (37 mm panel plate + 2 × 3 mm shell band) | Height is connector-driven; the 23.4 mm device does not set it |
| Bay depth, etherCON | 59.6 mm | 34.55 panel + 25 plug/bend |
| Bay depth, USB | 60.6 mm | 40.55 + 20 |
| Bay depth, HDMI | **75.7 mm** | 40.65 + 35 (long plug, stiff cable) — the governing figure |
| Bay depth, BNC | 74.6 mm | 34 + 40.6 (Belden 4855R bend radius governs) |

**Topology: side-exit, ONE patch wall** (user decision, 2026-09-07 — resolves §11 R1). All external
connectors sit in a single long side wall; the opposite long wall and both end walls carry none. The
device lies lengthwise and its end-face ports reach the wall via short patch cables that turn 90° in
the end zones. Full derivation, coordinate frame, slot rule, keep-outs and asserts:
**`.claude/knowledge/layout-patch-wall.md`** (summarised in §14).

| Family | Outer envelope L × W × H | Lid fasteners | Bed margin (256 mm) |
|---|---|---|---|
| `compact` (device 100.9 × 60.2 × 23.3) | **174.9 × 149.9 × 49.0 mm** | 4 | 81 / 106 mm |
| `plus` (device 117.5 × 66.7 × 23.4) | **191.5 × 156.4 × 49.0 mm** | 6 | 65 / 100 mm |
| `ip_decoder` (120 × 79.3 × 24.5) | future — not derived | — | — |

Per-SKU L/W vary within the family (they are computed from the port map, not hand-typed); the figures
above are the family maxima, i.e. the size to quote and to print. The in-line envelopes previously
recorded here (~244 × 72 × 45 and ~260 × 80 × 45) are **superseded**.

---

## 2. Tech stack and pinned tooling

| Thing | Value | Notes |
|---|---|---|
| Modeller | OpenSCAD nightly, `C:\Program Files\OpenSCAD (Nightly)\openscad.exe` | Version string recorded as "2025.09.07" in the brief — **confirm** (see §12 Q1) |
| CSG backend | Manifold (`--backend=Manifold`) | Must be passed explicitly on the CLI; do not rely on GUI preferences |
| Library | BOSL2 (BelfrySCAD), git submodule at `lib/BOSL2/`, pinned SHA | Pin the SHA; BOSL2 makes breaking changes |
| Slicer | Bambu Studio, `C:\Program Files\Bambu Studio` | Bambu Lab X1C / P1S, 256 mm cube |
| Mesh checks | Python 3.14 + trimesh | `scripts/` only; never part of the model |
| Material | ASA shell, 3 mm walls / 5 perimeters | No TPU anywhere in this repo (decision) |

Determinism rule: a render is reproducible only if the OpenSCAD build, the BOSL2 SHA, and the
parameter set are all pinned. All three go into the export manifest (§8).

---

## 3. Layered module architecture

OpenSCAD has no namespaces and no import isolation, so the layering is a **convention enforced by
review and by grep-able `use`/`include` edges**, not by the language. Dependencies point downward
only. An upward edge is a deviation.

```
L4  models/<device-slug>/case.scad        assembly; the ONLY place that composes
        │                                 (one thin file per device SKU, ~40–80 lines)
        ▼
L3  lib/mcc/devices/*.scad                DATA ONLY — device envelope + port map + provenance
        │                                 no geometry, no modules, no BOSL2 calls
        ▼
L2  lib/mcc/shell.scad                    base + lid, tongue-and-groove, aperture framing
    lib/mcc/panel.scad                    connector panel plate + panel_cutout() dispatcher
    lib/mcc/cradle.scad                   device cradle, locating ribs, pad pocket
    lib/mcc/mounts.scad                   ALL floor/exterior features (see the floor rule, §6)
    lib/mcc/vents.scad                    chimney slot arrays
        │
        ▼
L1  lib/mcc/neutrik.scad                  D-series cutout, pocket, screw bosses, depth tables
    lib/mcc/fasteners.scad                heat-set bosses, captive thumbscrew, 1/4"-20 boss
    lib/mcc/fan.scad                      fan bay envelope, grille, finger guard
    lib/mcc/poe_splitter.scad             splitter bay envelope + tie-down
    lib/mcc/ghost.scad                    device ghost + plug envelopes (visual only)
        │
        ▼
L0  lib/mcc/constants.scad                dimensions, tolerances, part tables — variables + pure
    lib/mcc/ports.scad                    port-record accessors (encapsulates the data shape)
    lib/mcc/util.scad                     EPS, assert helpers, small geometry helpers
        │
        ▼
    lib/BOSL2/                            submodule, pinned
```

### Include discipline

- `constants.scad` contains **only** variable assignments and pure functions — **never a module**.
  That makes repeated `include <>` idempotent and warning-free. This is a hard rule; a module in
  `constants.scad` is a deviation.
- Everything else is consumed with `use <>` (modules/functions only).
- A barrel file `lib/mcc/mcc.scad` `include`s `constants.scad` and `use`s every L1/L2 file. Model
  files (`L4`) import **only** `<mcc/mcc.scad>` and their own device data file. Library files import
  their direct dependencies, not the barrel (importing the barrel from inside the library creates
  cycles).
- `lib/mcc/devices/*.scad` must import **nothing** except `ports.scad`. If a device file needs
  geometry, the design is wrong.

### Naming (mandatory — OpenSCAD has one global namespace)

| Kind | Convention | Example |
|---|---|---|
| Public module | `mcc_` prefix, snake_case | `mcc_neutrik_d_cutout()` |
| Public function | `mcc_` prefix, snake_case | `mcc_bay_depth(part)` |
| Private helper | `_mcc_` prefix | `_mcc_flange_outline()` |
| Constant | `MCC_` prefix, UPPER_SNAKE | `MCC_WALL` |
| Device data symbol | `MCC_DEV_<slug>` | `MCC_DEV_PRO_CONVERT_HDMI_TX` |
| File | lower_snake_case `.scad` | `poe_splitter.scad` |
| Model directory | Magewell slug, 1:1 with `knowledge/magewell/models/` | `models/pro-convert-hdmi-tx/` |

### Parameter conventions

- **All lengths are millimetres.** No unit suffixes, no inches anywhere except the literal
  `1/4"-20` thread, which is modelled by a named constant, never by an inline number.
- Angles in degrees (OpenSCAD default). Temperatures °C. Power W.
- Suffixes: `_d` diameter, `_r` radius, `_t` thickness, `_h` height, `_w` width, `_l` length,
  `_clr` clearance, `_n` count, `_pos` position vector, `_pitch` centre-to-centre.
- Named arguments at every call site with more than two parameters. Positional args are a
  deviation — Sonnet-tier agents get them wrong and the failure is silent geometry.
- No magic numbers in L2/L3/L4. Every dimension traceable to `constants.scad` or a device data file.
  A literal number outside `constants.scad` that is not `0`, `1`, `2`, or an obvious multiplier is a
  deviation.

### `$fn` policy

- **Never set a global `$fn`.** Top-level model files set `$fa = 1; $fs = 0.4;`.
- Set `$fn` locally and explicitly *only* where facet count is functionally meaningful — connector
  holes, insert bores, fastener clearance holes: `$fn = 64` minimum.
- For any hole that must pass a real part, use BOSL2 `cyl(..., circum = true)` (or add
  `MCC_HOLE_COMP`) so the polygonal approximation is circumscribed rather than inscribed. An
  inscribed 24.2 mm hole at `$fn=32` is effectively 24.08 mm — that matters when the Neutrik flange
  only overlaps the hole by ~0.9 mm per side.

---

## 4. Case decomposition (answers "one case per family vs one per device")

**Three layers, not a binary choice.**

1. **Shell — parametric, one per housing family.** `mcc_shell()` in `shell.scad`. Families:
   `plus` (117.5 × 66.7 × 23.4), `compact` (100.9 × 60.2 × 23.3), later `ip_decoder`
   (120 × 79.3 × 24.5). The shell knows nothing about specific devices — it takes a device envelope,
   a per-end bay depth, and a feature config.
2. **Device data — one file per SKU.** `lib/mcc/devices/<slug>.scad`. Port map with provenance. This
   is where devices on the *same* chassis diverge, and the divergence is data, not geometry.
3. **Assembly — one thin file per SKU.** `models/<slug>/case.scad` picks the family shell, passes the
   device record, sets the variant config, and exports `base` or `lid` by `-D part=`.

**Why not "one parametric case per family with variant flags":** the variation between devices on the
same chassis is *port kind, count, face, and position* (HDMI TX = HDMI IN + Mini-DIN-8 on one end;
NDI to HDMI = HDMI OUT + USB-A host; NDI to AIO = HDMI OUT + SDI OUT BNC — all on the compact
chassis, per `knowledge/magewell/housing-families.md:126-149`). Encoding that as booleans produces a
combinatorial flag soup that no reviewer can verify. It is data; it belongs in data files.

**Why not "one model per device" (copied geometry):** a fix to the D-series cutout would need eight
edits, and they would drift.

**Consequence:** adding a new device = one data file + one ~50-line assembly + one golden test. No
library change. That is the acceptance test for this decomposition — if a new device requires editing
`shell.scad`, the abstraction leaked and it is a deviation worth reporting.

---

## 5. The connector panel is a separate printed plate

**Decision: connectors mount in a bolt-in `mcc_panel()` plate, not directly in the shell wall.**
Since the side-exit decision (§1, §14) there is exactly **one plate per case**, in the long patch
wall. The patch wall carries a full-length rectangular aperture with a rabbet; the plate drops into
the rabbet and is retained by 4 × M3 into heat-set inserts.

### The patch-wall plate (one per case)

| Property | Value | Source |
|---|---|---|
| Thickness | **2.0 mm** at every flange seat, ribbed to 3.0 mm elsewhere | `d-series-cutout.md:90` (NAHDMI-W max 2 mm) |
| Height | **37.0 mm** | set by the rear boss: 2 × (12.0 + 8.28/2 + 2.0), `d-series-cutout.md:47` + `fdm-rugged-enclosure-guidelines.md:127` |
| Length | `L − 26` (10 mm shell frame band beyond each plate end) | layout-patch-wall.md §2.3 |
| Slots | up to **4**, `pitch = (L − 68)/(n_slots − 1)`, asserted ≥ 32 mm | `placement-and-depth.md:42` |
| Rim | ribbed 3 mm rim around the whole outline | `fdm-...:65-70` |
| Retention | 4 × M3 along +Y, through tabs in the plate's end pads, into bosses on the rabbet lip | |
| Wall stack in Y | 3.0 proud bezel + 2.0 plate seat + 3.0 structural lip = **8.0 mm** | §5 rationale 5 (sacrificial bezel) |

The slots are spread **as wide as the wall allows**, not packed at the minimum pitch — the widest
pitch gives every cable the longest run to its 90° turn and puts the outer slots in the end-zone
corners where the turn is cleanest.

**Consequence recorded:** the plate is now ~138–166 mm long, not the ~70 × 40 mm quoted in
rationale 4 below. Reprinting it after a drop is still far cheaper than reprinting a 192 mm shell,
but the "small replaceable part" argument is weaker than it was under the in-line topology.

Rationale:

1. **Panel-thickness cap.** NAHDMI-W-B accepts **max 2 mm** panel thickness; etherCON up to 4 mm
   (`knowledge/neutrik/d-series-cutout.md:84-98`). The rugged wall spec is 3 mm. A separate plate can
   be exactly 2.0 mm at the flange seat and ribbed elsewhere, without thinning the structural shell.
2. **Print orientation.** A plate prints **flat, face-down**: the ⌀23.8/24.2 mm holes are perfect
   circles with no bridging, and the flange seat is a true bed-flat surface. The same hole in a
   vertical shell wall is a 24 mm bridge that droops at the top of the circle.
3. **It is the per-device variation point.** The shell is per-family; the panel is per-device. Making
   the varying thing a separately-generated part isolates change exactly where change happens.
4. **Replaceability.** After a drop that cracks a connector boss, you reprint a ~70 × 40 mm plate,
   not a 244 mm shell.
5. **Drop protection.** The shell frames the panel on all four sides and stands proud of the
   connector faces as a sacrificial bezel, so a face/corner impact loads the continuous shell
   perimeter, not the connector body — the recessed-connector principle from
   `knowledge/design/fdm-rugged-enclosure-guidelines.md:182`.

Costs, accepted: ~4–6 mm added length per end; 4 extra inserts per panel; a seam. Mitigations, which
are part of the design contract:
- The panel sits in a **full-depth rabbet**, so shear from an impact is carried by the shell, not by
  the M3 screws. The screws only resist pull-out.
- The aperture roof is a **≤45° self-supporting chamfer**, never a flat bridge. This is a general
  shell rule: *no unsupported horizontal span over 10 mm anywhere in the shell.*
- Seam sealing, if ever needed, is a gasket channel in the rabbet — not a tighter fit.

**Fallback rule:** a face carrying exactly one connector *may* be integral to the shell with a local
2 mm pocket, if a designer argues it. It still needs the 45° roof and the rear screw bosses. Do not
mix the two approaches on one case without recording why here.

### Connector fixing

The Neutrik screw holes (±9.5, ±12.0 mm) sit *inside* the 26 × 31 flange footprint, so the screws
cannot land on material outside the flange. Two supported options:

- **Preferred:** local rear bosses at the two screw positions, protruding rearward from the 2.0 mm
  seat to ~7 mm total, with an M3 heat-set insert (5.7 mm). Front face stays at 2.0 mm.
- **Alternative:** Neutrik **MFD** M3 fixing plate on the inside face
  (`knowledge/neutrik/d-series-cutout.md:105-111`) — stronger, but adds an SKU per connector.

Self-tapping directly into 2 mm of ASA is **not** an approved option.

### Panel cutout dispatcher

`panel.scad` owns `mcc_panel_cutout(part, ...)`. `neutrik.scad` is one *provider* behind it, not the
top-level abstraction. If `models/**` ever calls `mcc_neutrik_*` directly instead of
`mcc_panel_cutout()`, that is a layering deviation.

**Dispatchable parts (user decision, 2026-09-07 — resolves §12 Q5):** `NE8FDP-B`, `NAHDMI-W-B`,
`NAUSB-W-B`, `NBB75DFGB`, and the `DBA-BL-B` blank. **That is the complete set.** The Mini-DIN-8
PTZ/Tally port stays internal (`panel:"none"`) on every current SKU, so `panel.scad` needs **no**
Mini-DIN-8 branch and no bespoke round-cutout provider. `MCC_PANEL_PARTS`
(`lib/mcc/constants.scad:240`) keeps its `MINIDIN8` row as **reserved data for a possible future
variant only** (`knowledge/components/mini-din8-feedthrough.md`); a Tier-1 assert forbids any port
from referencing it (see §9, T1-05). Keeping the dispatcher genuinely single-provider today is a
simplification, not a loss — `neutrik.scad` remains behind `panel.scad` so the second provider can be
added later without touching `models/**`.

---

## 6. Feature ownership rules

Two rules exist because two features will otherwise collide silently:

- **The floor rule.** `mounts.scad` is the **single owner** of every feature in the case floor: the
  case's own 1/4"-20 insert, the VESA/Fishtail M4 pattern, strap slots, the stacking profile, and
  the through-bolt clearance for the device retention bolt. It exposes `mcc_floor_keepout()` and
  asserts non-overlap between all of them. `cradle.scad` requests a floor penetration *through*
  `mounts.scad`; it never cuts the floor itself. Decisions 5 and 7 both put a 1/4"-20 feature in the
  floor — one going up into the device, one going down into a tripod plate — and they must not
  coincide.
- **The reservation rule.** `shell.scad` always reserves the fan bay and the PoE-splitter bay as
  internal keep-out volume, **even when `fan = false` and `splitter = false`**. Otherwise enabling a
  fan later moves connectors and invalidates every printed part. `fan.scad` and `poe_splitter.scad`
  each expose an `*_envelope()` function used for reservation, separate from the module that cuts
  real geometry.

---

## 7. Port-map convention

A device record is a BOSL2 `structs` assoc-list. All access goes through `ports.scad` accessors so
the representation can change without touching device files or geometry.

```
// lib/mcc/devices/pro-convert-hdmi-tx.scad   (DATA ONLY)
MCC_DEV_PRO_CONVERT_HDMI_TX = [
  ["slug",   "pro-convert-hdmi-tx"],
  ["family", "compact"],
  ["size",   [100.9, 60.2, 23.3]],          // L, W, H  (x, y, z), origin = geometric centre
  ["source", "knowledge/magewell/models/pro-convert-hdmi-tx.md"],
  ["ports", [
    // face = outward unit normal in device-local coords (plugs straight into BOSL2 orient/attach)
    // pos  = [u, v] on that face, mm from the face centre; +u = right looking at the face, +v = up
    [["id","hdmi_in"],  ["face",[ 1,0,0]], ["pos",[-18, 0]], ["kind","hdmi_a"],
     ["dir","in"],      ["panel","NAHDMI-W-B"], ["confidence","photo"]],
    // Mini-DIN-8 PTZ/Tally stays INTERNAL on every current SKU (user decision 2026-09-07).
    // It is still in the port map — the ghost, the cradle keep-out and the BOM need to know it
    // exists — but panel:"none" means no cutout and no dispatcher branch. See §5.
    [["id","ptz_tally"],["face",[ 1,0,0]], ["pos",[ 14, 0]], ["kind","minidin8"],
     ["dir","bidir"],   ["panel","none"],       ["confidence","photo"]],
    [["id","usb_b"],    ["face",[-1,0,0]], ["pos",[-16, 0]], ["kind","usb_b"],
     ["dir","power"],   ["panel","NAUSB-W-B"],  ["confidence","photo"]],
    [["id","rj45"],     ["face",[-1,0,0]], ["pos",[ 15, 0]], ["kind","rj45"],
     ["dir","bidir"],   ["panel","NE8FDP-B"],   ["confidence","photo"]],
    [["id","rotary"],   ["face",[0,-1,0]], ["pos",[ 30, 0]], ["kind","rotary16"],
     ["dir","none"],    ["panel","none"],       ["confidence","photo"]],
    [["id","tripod"],   ["face",[0,0,-1]], ["pos",[ 30, 0]], ["kind","tripod_1_4_20"],
     ["dir","none"],    ["panel","none"],       ["confidence","assumed"]]
  ]]
];
```

Field contract:

| Field | Type | Meaning |
|---|---|---|
| `id` | string, unique per device | referenced by the variant config and the BOM |
| `face` | unit vector | outward normal, device-local; feeds BOSL2 orientation directly |
| `pos` | `[u, v]` mm | position on that face, from the face centre |
| `kind` | enum string | physical port type; drives the ghost geometry and plug envelope |
| `dir` | `in`/`out`/`bidir`/`power`/`none` | informational; drives labels and BOM |
| `panel` | part number or `"none"` | which panel connector this port is brought out to; `"none"` = stays internal (SD slot, LEDs), `"blank"` = DBA-BL |
| `confidence` | `measured`/`drawing`/`manual`/`photo`/`assumed` | **required** |

**`confidence` is not decoration.** `knowledge/magewell/housing-families.md:8-10` states plainly that
no dimensioned port-position drawing exists for any model — every position in this repo starts as
`photo` or `assumed`. Rules:
- `ports.scad` `echo()`s a WARNING listing every port below `measured` at render time.
- `scripts/build.py` fails the **release** build (not the dev build) if any port used for a real
  cutout is below `measured`.
- Upgrading a port to `measured` requires a note in the device file naming who measured what.

The `panel` value keys the depth tables in `constants.scad`:
`mcc_panel_depth(part)`, `mcc_plug_len(part)`, `mcc_bend_envelope(part)`, and
`mcc_bay_depth(part) = mcc_panel_depth(part) + mcc_plug_len(part)`. Bend envelope is a *lateral*
keep-out, tracked separately from axial depth — for BNC it is the dominant term (Belden 4855R,
40.6 mm, `knowledge/components/cables.md:63`).

Those same two fields also drive **slot assignment**: `mcc_slot_for_port()` partitions the external
ports by `face` sign and orders each half by `[mcc_bend_envelope, mcc_plug_len]` descending, stiffest
cable outermost. No device file ever names a slot index. See §14 / `layout-patch-wall.md` §3.

### Ghost rendering

`ghost.scad` provides `mcc_ghost(dev)`: the device bounding box, port receptacle stubs, and a plug
envelope extruded along each port's face normal by `mcc_plug_len(kind)` plus a bend allowance. Drawn
with the `%` modifier so it is excluded from CSG and from STL export, *and* gated behind
`MCC_SHOW_GHOST` (default `false`). Both belts: `%` is the mechanism, the flag is the review signal.
A ghost that appears in an exported mesh is a P1 deviation.

---

## 8. Export and versioning policy

**Source and small text goldens in git. Binary artefacts never in the working tree.**

- `exports/` is **gitignored**. It is local scratch output.
- `tests/golden/<slug>.json` **is** committed: bbox, volume, surface area, triangle count, part count.
  Small, diffable, and it catches unintended geometry change in review.
- Release artefacts (STL + 3MF) are built by CI from a **tag** and attached to a GitHub Release.
  Never committed.
- Every artefact ships with a manifest recording: git SHA, BOSL2 submodule SHA, OpenSCAD version
  string, the full `-D` parameter set, and the measured bbox/volume.

Rationale: STL/3MF are large, opaque, and change wholesale on any parameter tweak. Committing them
bloats the repo, produces meaningless diffs, guarantees merge conflicts, and — worst — lets a stale
binary drift from the source that supposedly produced it. Tag-built release assets give the "grab a
printable file without OpenSCAD" benefit with none of those costs.

CI (`.github/workflows/render.yml`) on every PR: submodule checkout → pinned OpenSCAD (AppImage,
pinned URL + checksum) → render every model → `--summary all` → mesh checks → compare to goldens →
upload artefacts for inspection. It does **not** commit anything.

---

## 9. Test policy

Four tiers, cheapest first.

**Tier 1 — in-model `assert()`, runs on every render, free.** Library modules assert their own
contracts, so a bad parameter fails loudly at render instead of quietly at the printer. Minimum set:

| Assertion | Source |
|---|---|
| `bbox ≤ MCC_BUILD - MCC_BED_MARGIN` per part | 256 mm cube |
| wall thickness ≥ `MCC_WALL` (3.0) | decision 8 |
| panel seat thickness ≤ `mcc_panel_max_t(part)` (2.0 for HDMI/USB) | `d-series-cutout.md:84-98` |
| D-connector horizontal pitch ≥ 32, vertical pitch ≥ 36 | `placement-and-depth.md:41-45` |
| each flange 26 × 31 fits on the panel with ≥ 4 mm web to the frame | `placement-and-depth.md:36-40` |
| `24.0 ≤ cutout_d ≤ 24.6` (never blow out the hole — flange overlap is only ~0.9 mm/side) | `d-series-cutout.md:36-43` |
| clear depth behind each cutout ≥ `mcc_bay_depth(part)` | `placement-and-depth.md:66-71` |
| heat-set boss OD ≥ 1.8 × insert OD, ≥ 2 mm material to any edge | `fasteners-and-hardware.md:123-131` |
| rib thickness ≤ 0.6 × adjoining wall, height ≤ 3 × thickness | `fdm-rugged-enclosure-guidelines.md:65-70` |
| no two floor features overlap (`mcc_floor_keepout()`) | §6 floor rule |
| every port with `panel != "none"` has a cutout, and vice versa | §7 |

**Plus 21 topology asserts (T1-01 … T1-21)** introduced by the patch-wall layout: slot bijection,
slot pitch, bay depth and lateral bend fit, end-zone cable allowance, plate-fits-wall, boss-to-flange
clearance, splitter/fan/vent non-intersection, and the `panel != "MINIDIN8"` guard. Full table with
sources: `layout-patch-wall.md` §9. Do not re-derive them in the model files; they are the
acceptance criteria for `shell.scad`, `panel.scad`, `cradle.scad`, `mounts.scad`, `vents.scad`.

**Tier 2 — headless smoke tests, `tests/*.scad`.** Instantiate every public module at its default,
minimum, and maximum parameters. Run with `openscad -o out.csg` — CSG export evaluates the tree (so
asserts fire) without tessellating, so it is fast. Non-zero exit = failure.

**Tier 3 — geometry goldens.** `openscad --summary all --summary-file <json>` on every model, diffed
against `tests/golden/*.json` with a tolerance (~0.5 % volume, 0.1 mm bbox). Plus `check_mesh.py`
(trimesh): `is_watertight`, `is_winding_consistent`, `euler_number`, `volume > 0`, and
**`len(split()) == 1`** — a case body must be one connected shell, which catches a rib or boss that
floated free after a parameter change. Do not attempt automated minimum-wall-thickness measurement in
trimesh; it is unreliable. Rely on the Tier-1 assert plus the slicer.

**Tier 4 — physical coupons, `models/coupons/`.** Non-negotiable and *first*, before any 244 mm case
is printed:
- `neutrik-tile` — one D cutout with the 2 mm pocket and rear bosses, in a 40 × 45 mm tile. Verifies a
  real connector actually fits and screws down.
- `depth-mockup` — holds one panel connector at a set distance from a mock device port face, so the
  real patch cable can be tried. **This is the only way to replace the `unknown` plug lengths.**
- `tg-ladder` — tongue-and-groove clearance ladder to calibrate `MCC_CLR_TG`.
- `insert-boss` — heat-set boss hole-diameter ladder for ASA.
- `tolerance-ladder` — general fit ladder.

Every coupon result is written back into `constants.scad` as a calibrated constant with a comment
naming the coupon and the date.

Command shapes (single implementation, two entry points):
`scripts/build.py` does render + summary + checks and is what CI runs. `scripts/render.ps1` is a thin
wrapper over it for Windows muscle memory. Do **not** maintain two independent build implementations
— they will diverge and CI will stop reflecting local behaviour.

---

## 10. Proposed skills (`.claude/skills/`)

| Skill | Scope (one line) |
|---|---|
| `knowledge-lookup` | Resolve any dimension from `knowledge/**` and cite `file:line`; return `unknown` rather than inventing a figure |
| `openscad-authoring` | House conventions for writing `.scad` here: layering, `mcc_` naming, named args, `$fn` policy, assert style, BOSL2 idioms |
| `openscad-render` | Invoke the pinned OpenSCAD headlessly with Manifold and `-D` overrides; interpret errors/warnings |
| `neutrik-panel` | Place a D-series (or Mini-DIN-8) cutout with pocket, bosses, and spacing/depth asserts; pick the right cutout ⌀ per part |
| `device-portmap` | Create/verify a device data file from `knowledge/magewell/models/*.md`, including `confidence`, and render the ghost |
| `new-case-variant` | Scaffold `models/<slug>/` + golden + export entry from a device record |
| `print-check` | Pre-slice gate: render, mesh checks, bbox vs 256, orientation/overhang review, ASA warp advice → go/no-go |
| `bom-update` | Regenerate `BOM.md` from variant configs + port maps (Neutrik parts, inserts, screws, fan, splitter, cables) |

`openscad-authoring` is the highest-value one: it is what keeps Sonnet-tier agents inside the
conventions in §3 without the teamlead restating them every time.

---

## 11. Risks carried into the design

**R1 — Plus family vs. the build plate. RESOLVED 2026-09-07 (user decision).**
The in-line layout (76 HDMI bay + 117.5 device + 61 USB bay + 6 walls = ~260.5 mm) exceeded the
256 mm bed. Resolution: **side-exit, one patch wall.** Both families now fit comfortably —
plus 191.5 × 156.4, compact 174.9 × 149.9, ≥ 64 mm of bed margin in every axis (§1, §14). The
architectural hedge held: bay depth stayed a computed function of the port map, so the new envelope
fell out of the data rather than being re-derived by hand. Residual, carried into **R14**: the new
footprint is ~54 % more bed area of ASA than the in-line one.

**R2 — the case's principal dimension derives from figures the knowledge base marks `unknown`.**
Every mating-plug length (etherCON boot, HDMI plug, USB-B plug, BNC body) is explicitly unverified
(`knowledge/components/cables.md:117-129`, `knowledge/neutrik/placement-and-depth.md:57-64`). The
60–76 mm bay depths are engineering estimates. Mitigation: they live in one table in
`constants.scad`, tagged `confidence:"assumed"`, and the `depth-mockup` coupon replaces them with
measured values before any full case is printed.

**R3 — Plus End B connector count. RESOLVED 2026-09-07 (user decision).**
Two changes remove the problem entirely: the **Mini-DIN-8 stays internal** (`panel:"none"`, §5), and
the connectors no longer share an end face at all — they sit in the patch wall, which is 138–166 mm
long. Every priority SKU now has **≤ 4 external D-size ports** (Plus encoder: video IN, loop-OUT,
etherCON, USB-B; TX: video IN, etherCON, USB-B; NDI decoders: video OUT, USB-A host, etherCON,
USB-B; AIO: HDMI OUT, BNC OUT, etherCON, USB-B), and the **HDMI loop-out is brought outside** as the
user wanted. Achieved pitch is 34.7–53.5 mm, comfortably above the 32 mm minimum.

**R4 — HDMI's 2 mm panel cap puts the weakest material at the highest-load point.** A 2 mm ASA
membrane with a 23.8 mm hole, carrying the heaviest, stiffest cable in the build. Mitigations are
already in §5 (separate flat-printed plate, rabbet takes shear, sacrificial bezel, ribs around the
pocket). **Open:** NAUSB-W and NBB75DFG panel-thickness ratings are `unknown`
(`d-series-cutout.md:92-93`) — treat as ≤3 mm and confirm before finalising.

**R5 — thermal.** With the ~244 × 84 × 45 mm shell, A ≈ 0.070 m². At the verified still-air
h = 1.6 W/m²K and ΔT = 15 K, passive rejection is ~1.7 W; the 10 W Plus models need ~12 W/m²K, above
every natural-convection figure in `knowledge/design/thermal-guidelines.md:421-443`. Devices are
rated 0–45 °C (Plus) / 0–40 °C (compact), so in a 35 °C venue the ΔT budget is ~10 K, not 15 K.
Passive-first is the right *intent*, but the fan is not optional for the 10 W Plus models. This is
why §6's reservation rule exists: vent and fan geometry are reserved in every variant from v1.

**R6 — PoE power budget.** 802.3af delivers 12.95 W at the PD. A 10 W Plus device + splitter
conversion loss (1–2 W) + fan (0.25–1.3 W) is at or over budget, and the splitter's own heat lands
*inside* the case. Design constraints: put the splitter bay in the **intake** airflow, not against
the device; confirm the chosen splitter's rated continuous output against the worst-case model.
Pending research in `knowledge/components/poe-splitters.md`. **Escalate once that lands.**

**R7 — lid fastener count. RESOLVED 2026-09-07.** Baseline stays the user's 4 captive M3
thumbscrews; the architect-derived rule **6 for any lid over 180 mm span** now applies (decision
D-04, `layout-patch-wall.md` §6/§10 — flagged for user veto). Outcome under the patch-wall envelopes:
**compact → 4** (L ≤ 174.9), **plus → 6** (L ≥ 180.5). The two extra fasteners go mid-span on the
long walls; on the patch wall the mid-span position must clear every flange edge by ≥ 6.15 mm, and
where it cannot (HDMI Plus, which clears by only 5.75 mm) it is replaced by an internal buttress rib
tying the patch wall to the lid tongue. The patch wall is the one that most needs the mid-span
restraint — it has a 138–166 mm aperture cut in it.

**R8 — device retention.** A single 1/4"-20 through-bolt is one point of restraint; the device can
pivot about it, so the printed cradle's locating ribs carry all anti-rotation load and must be
designed as structural, not cosmetic. Vibration loosening is real on touring gear: specify a
thread-locking or nylon-insert solution and let the compliant pad provide preload. Also: the exact
1/4"-20 hole location is undocumented for the Plus family and only "estimated from image" for TX
(`housing-families.md:70-72`, `:132`) — it starts at `confidence:"assumed"` and must be measured.

**R9 — ASA warp on a 244 mm footprint.** `fdm-rugged-enclosure-guidelines.md:17` calls significant
warping ASA's main disadvantage. Bake in: generous bottom-edge fillet/chamfer (never a sharp bed
corner), uniform wall thickness with ribs rather than thick sections
(`fdm-rugged-enclosure-guidelines.md:65-72`), brim, and an enclosure at temperature. Do not use the
first full-size print as the design validation — coupons first.

**R10 — grounding is a non-issue that looks like an issue.** A plastic shell provides no shield
continuity between connector shells (`placement-and-depth.md:78-93`). Do not spend design effort on
grounded-vs-isolated BNC variants unless a conductive panel is later added. Recorded so it does not
get re-litigated.

**R11 — the reserved PoE-splitter bay does not fit the patch-wall topology with the placeholder
part. NEW, blocking for `shell.scad`.** §6's reservation rule requires the splitter bay to be
reserved even when `splitter = false`. Laid transversely at the −X (data/power) end — the only
functionally correct position, since all three of its connections terminate there
(`poe-splitters.md:170-192`) — the PoE Texas **GAT-USBC** placeholder (114 × 51 × 25,
`poe-splitters.md:58`) reaches `y = +38.8` while slot 1's etherCON plug envelope reaches inward to
`y = +10.6`: **≈28 mm of overlap.** Rotating it fails on width; stacking it fails on height
(25 + 23.4 > the 43 mm interior). Options: (a) reserve a smaller "dongle class" default —
75 × 40 × 20 fits with clearance, but the UCTRONICS U6114/U6115 dimensions are explicitly `unknown`
(`poe-splitters.md:129-136, 211-215`); (b) widen the plus case by ~50 mm to ~206 mm, giving a near-
square 192 × 206 footprint; (c) make PoE a separate taller shell variant. **Needs a user decision.**
Architectural hedge already in place: the reservation is computed from `MCC_SPLITTERS[part]` and
guarded by assert T1-16, so whichever part is chosen either fits or fails loudly at render — only the
*default part* is the user's call.

**R12 — the NDI decoders' 1/4"-20 hole is on the TOP face, not the bottom. NEW, blocking for
`cradle.scad` on three SKUs.** `knowledge/magewell/housing-families.md:139` states, for NDI to HDMI:
"Top, near Face A: SD-card slot (non-functional) + 1/4"-20 hole". A floor through-bolt — the fixed
retention decision — physically cannot reach it on NDI to HDMI / SDI / AIO. Options: bolt down
through the **lid** on those SKUs; retain by cradle ribs + a lid clamp pad only (accepting R8's
anti-rotation load entirely on the ribs); or verify the claim physically first, since it may be a
transcription error in the manual figure. **Needs a user decision after physical verification.**

**R13 — a right-angle HDMI adapter is now a required BOM item, not an optimisation. NEW.** The
30 mm end-zone allowance for a device-side HDMI port is only defensible with a right-angle adapter
(25.4 mm verified, `cables.md:50/122`). A *straight* HDMI plug's axial length is `unknown`
(`cables.md:121`) and would additionally need its own turn radius inside the end zone, which no
sourced figure supports. Consequence: every device-side HDMI port carries a right-angle adapter, and
`ez` for those ends must be re-derived if that changes. `bom-update` must emit it.

**R14 — bed area, not bed length, is now the ASA warp risk. NEW.** The patch-wall plus base is
191.5 × 156.4 = 30,000 mm² of first layer, ~54 % more than the superseded in-line 244 × 80 =
19,500 mm². R9's mitigations (generous bottom-edge fillet, uniform walls with ribs, brim, enclosure
at temperature) become more important, not less, even though the longest dimension shrank by 50 mm.
Print time and filament per case rise correspondingly.

---

## 12. Open questions / assumptions

1. **OpenSCAD version.** The brief says nightly **2025**.09.07; today is 2026-09-07. Is this a
   deliberately pinned year-old build, or a typo for 2026.09.07? Whichever it is, the exact version
   string must be pinned and recorded in the export manifest.
2. ~~**Layout topology** for the Plus family (R1).~~ **RESOLVED 2026-09-07:** side-exit, one patch
   wall. See §14 and `layout-patch-wall.md`.
3. ~~**Plus End B connector count** (R3).~~ **RESOLVED 2026-09-07:** Mini-DIN-8 internal, HDMI
   loop-out brought outside, ≤ 4 external D ports per SKU, all in the patch wall.
4. ~~**Fastener count** on long lids (R7).~~ **RESOLVED 2026-09-07:** 4 baseline, 6 for spans over
   180 mm (decision D-04 — architect-derived, flagged for user veto). Compact → 4, plus → 6.
5. ~~**Mini-DIN-8 panel solution.**~~ **RESOLVED 2026-09-07:** it is not brought out.
   `panel:"none"` on every SKU; `mcc_panel_cutout()` dispatches Neutrik D parts + `DBA-BL-B` only.
   `knowledge/components/mini-din8-feedthrough.md` and the `MINIDIN8` row in `MCC_PANEL_PARTS` are
   retained as reserved data for a possible future variant; assert T1-05 forbids referencing it.
6. **PoE splitter part** — still open, and now **blocking for `shell.scad`**: the GAT-USBC
   placeholder does not fit the patch-wall topology at all (R11). Choose a part or a fallback.
7. **All mating-plug lengths** (R2) — placeholder constants until the `depth-mockup` coupon is built.
8. **Device 1/4"-20 hole positions** (R8) — measure per SKU.
9. **NAUSB-W / NBB75DFG panel-thickness rating** (R4) — assumed ≤3 mm.
10. **Fan presence in HDMI Plus / SDI Plus** is contradictory across Magewell's own sources
    (`housing-families.md:44-53`). The case design must not depend on the device having or not having
    an internal fan: do not seal the device's top grille in any variant.
11. **`knowledge/` vs `.claude/knowledge/` split.** `knowledge/` is product/domain research (sourced,
    cited, stable). `.claude/knowledge/` is agent working memory (architecture, testing,
    ticket-source). Do not merge them; do not put sourced research in `.claude/`.
12. **Where the NDI decoders' 1/4"-20 hole actually is** (R12) — the manual says top face; verify
    physically before `cradle.scad` is written for those three SKUs.
13. **Straight vs. right-angle HDMI at the device end** (R13) — the end-zone length depends on it and
    the straight-plug figure is `unknown`. The `depth-mockup` coupon settles it.
14. **Two architect-derived rules flagged for user veto:** D-04 (6 fasteners over 180 mm) and D-06
    (flange-to-plate-edge web relaxed 4.0 → 3.0 mm **in Z only**, which is what buys the 49 mm case
    height instead of 51 mm). Both are recorded in `layout-patch-wall.md` §10; say so if either is
    unwanted.

---

## 13. Deviations log

Record each detected deviation with: date, intended rule, `file:line` of the violation, why it
matters, and the resolution (fixed / accepted-and-rule-updated / escalated).

_(empty — no production code exists yet)_

---

## 14. Patch-wall layout contract

**Full contract: [`layout-patch-wall.md`](layout-patch-wall.md).** It is normative for `shell.scad`,
`panel.scad`, `cradle.scad`, `mounts.scad` and `vents.scad`, and every number in it is cited to
`knowledge/**:line` or `lib/mcc/constants.scad:line`, or marked `assumed` / `unknown`. Summary:

**Frame.** Origin at the case's outer bbox centre in X/Y, at the underside in Z. X along the device
length, +Y towards the patch wall, +Z up. Interior floor `z = 3`, lid underside `z = 46`, patch wall
inner face `y = W/2 − 8`.

**Panel aperture.** Patch-wall stack in Y = 3.0 proud bezel + 2.0 plate seat + 3.0 structural lip =
8.0 mm. Aperture Z range `[6, 43]`, X range `±(plate_l/2 − 3)` with `plate_l = L − 26`. Connector
centreline `z = 24.5`.

**Cradle deck is derived, not chosen.** It is set so the device's end-face port centreline lands on
the connector centreline (`z = 24.5`), giving a 7.8 mm cradle deck + 2.0 mm compliant pad and a level
cable run. That in turn leaves 9.8 mm of plenum over the device's top grille.

**Slot rule (`mcc_slot_for_port()`).** Partition the external ports by the sign of `face.x`; end-A
ports take the leftmost slots, end-B ports the rightmost; inside each block order by
`[mcc_bend_envelope, mcc_plug_len]` descending, **stiffest cable outermost**, ties broken by `pos[0]`
then `id`. The outermost slot is the one whose plug sits in the end-zone corner opposite the device's
end face, so its cable makes exactly one 90° L rather than an S-bend — that is the slot the stiffest
cable must get. The ranking reads straight out of `MCC_PANEL_PARTS`, so it needs no new table and
self-corrects when the `depth-mockup` coupon replaces the assumed figures. Unallocated slots (always
the innermost) get `DBA-BL-B`.

**Bay and end zones.** `d_bay_free = max(mcc_bay_depth) − 5.0` (5 mm of it is plate + lip material),
= 70.65 mm for HDMI-bearing devices — and the bay must run the **full device length**, because slots
2 and 3 sit over the device's X range. End zone per end = `max(mcc_dev_side_allow(kind))` over that
end's ports: BNC 41, HDMI 30 (**right-angle adapter required**, R13), RJ45 27, USB 17. BNC's 40.6 mm
lateral bend is absorbed in the 70 mm-deep bay, so it does not force an end slot.

**Reserved bays.** Fan: +X end wall, NF-A4x10 frame inside, ⌀36 wall aperture, exhaust away from the
patch wall. PoE splitter: −X end, transverse slab — **currently does not fit with the GAT-USBC
placeholder, see R11.** Vents: intake low in the −X end wall and the far long wall (into the 6 mm
`MCC_GAP_FAR` duct along the device flank), exhaust high in the far wall's +X half; **never in the
patch wall.**

**Floor.** VESA 75×75 and the case 1/4"-20 default to the case plan centre; the device retention
through-bolt sits at the device's own tripod-hole X (per-SKU, `assumed`) on the device's Y centreline.
`vesa_pos` is a shell parameter so a colliding SKU can shift it; `mcc_floor_keepout()` asserts
non-overlap. R12 blocks this on the three NDI decoders.

**Architect verdict, 2026-09-07: APPROVED WITH CHANGES.** The topology is right and the connector
problem is solved. Three changes are required before implementation: resolve R11 (splitter bay),
resolve R12 (NDI decoder tripod hole), and accept or veto D-04/D-06/D-08.
