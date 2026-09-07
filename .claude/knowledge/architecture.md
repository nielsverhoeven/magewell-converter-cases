# Architecture — magewell-converter-cases

Status: **revision 4, 2026-09-08.** Baseline 2026-09-07 (before any code); rev 2 added the patch-wall
topology; rev 3 recorded the user's decisions on R11 (dongle-class splitter), R12 (**side** bolt
retention), D-04 (accepted), D-06 (**vetoed** → H = 51), D-08 (**vetoed** → straight-plug end zones)
and the dropped `develop` branch. **Rev 4 closes the last two blockers:** R15 → the splitter
reservation and the −X cable allowance **sum** (`ez_neg = 47`, +20 mm of `L`, 6 thumbscrews on both
families), and R18 → the side-bolt boss is **flush, not proud** (`MCC_GAP_FAR` 6 → 16,
`MCC_SIDE_BOLT_PROUD` 10 → 0, +10 mm of `W`). L0/L1 (`constants`, `ports`, `util`, `neutrik`, `panel`,
`fasteners`, `fan`, `poe_splitter`, `ghost`), 8 device data files and 5 coupons exist and pass
`python scripts/build.py all`. **L2 (`shell`, `cradle`, `mounts`, `vents`) and `models/<slug>/` do
not exist yet** — this file and `layout-patch-wall.md` are their specification.
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
| Interior height | **45 mm** (39 mm panel plate + 2 × 3 mm shell band) | Height is connector-driven; the 23.4 mm device does not set it. 39 mm (not 37) because **D-06 was vetoed**: the flange-to-plate-edge web stays 4.0 mm in Z |
| Outer height `H` | **51.0 mm** (3 floor + 45 interior + 3 lid) | User decision 2026-09-08 |
| Bay depth, etherCON | 59.6 mm | 34.55 panel + 25 plug/bend |
| Bay depth, USB | 60.6 mm | 40.55 + 20 |
| Bay depth, HDMI | **75.7 mm** | 40.65 + 35 (long plug, stiff cable) — the governing figure |
| Bay depth, BNC | 74.6 mm | 34 + 40.6 (Belden 4855R bend radius governs) |

**Topology: side-exit, ONE patch wall** (user decision, 2026-09-07 — resolves §11 R1). All external
connectors sit in a single long side wall; the opposite long wall and both end walls carry none. The
device lies lengthwise and its end-face ports reach the wall via short patch cables that turn 90° in
the end zones. Full derivation, coordinate frame, slot rule, keep-outs and asserts:
**`.claude/knowledge/layout-patch-wall.md`** (summarised in §14).

| Family | Shell envelope = printed bbox, L × W × H | Lid fasteners | Bed margin vs 256 | Margin vs the 250 assert limit |
|---|---|---|---|---|
| `compact` (device 100.9 × 60.2 × 23.3) | **194.9 × 159.9 × 51.0 mm** | 6 | 61.1 / 96.1 mm | 55.1 / 90.1 mm |
| `plus` (device 117.5 × 66.7 × 23.4) | **211.5 × 166.4 × 51.0 mm** | 6 | 44.5 / 89.6 mm | 38.5 / 83.6 mm |
| `ip_decoder` (120 × 79.3 × 24.5) | future — not derived | — | — | — |

Per-SKU L/W vary within the family (they are computed from the port map, not hand-typed); the figures
above are the family maxima, i.e. the size to quote and to print. The in-line envelopes previously
recorded here (~244 × 72 × 45 and ~260 × 80 × 45) are **superseded**, and so are the rev-3 patch-wall
figures (174.9 × 149.9 and 191.5 × 156.4) — see the two decisions below.

**There is no longer a separate "bbox" column: the shell envelope *is* the printed bounding box.**
Rev 3 carried a `+ side-bolt lug` column because the far wall grew a 10 mm proud boss. **D-13
(2026-09-08) makes that boss flush** — nothing protrudes from any wall on any variant.

Base and lid are separate parts with the *same* L × W footprint, so each needs its own build plate
(2 × 211.5 or 2 × 166.4 both exceed 250 mm — they cannot be nested on one plate). The panel plate
(`L − 26` × 39, flat) *can* share a plate with the base: it fits the 250 − 166.4 = 83.6 mm strip.

**The two decisions that produced these numbers (user, 2026-09-08):**

- **R15 → accept +20 mm of `L` (decision D-12).** §6's reservation rule is honoured
  unconditionally: the dongle-class PoE-splitter bay (75 × 40 × 20, on edge) is reserved in **every**
  variant, and because the device's own −X plugs need their allowance whether or not a splitter is
  fitted, the two allowances **sum**: `ez_neg = 27 + 20 = 47`. Second-order consequence, accepted:
  at `L = 194.9` the **compact family crosses the 180 mm D-04 threshold and also goes to 6 lid
  thumbscrews** — a BOM and print-time change on all five compact SKUs, not a cosmetic 20 mm.
- **R18 → the side-bolt boss is flush (decision D-13).** Instead of a 10 mm lug outside the far wall,
  the far wall moves 10 mm outward: `MCC_GAP_FAR` 6 → **16 mm**, `MCC_SIDE_BOLT_PROUD` 10 → **0**, so
  the 17 mm captive stack (head recess 6 + web 3 + clip pocket 8) sits entirely inside
  `MCC_WALL + MCC_GAP_FAR − pad = 3 + 16 − 2 = 17 mm`. **The printed bbox is unchanged by this
  decision** (rev 3's bbox was already `W + 10`); what changes is that the 10 mm is now usable
  interior — a 16 mm airflow duct along the device's far flank — instead of a stress-riser lump. Cost:
  more ASA in the floor and lid, and the boss's 14 mm cantilever moves *inside* the wall (§11 R18).

**Straight-plug end zones (D-08 vetoed).** No right-angle HDMI adapter is in the default BOM, so the
device-side HDMI end zone is sized for a *straight* plug: `ez(hdmi_a) = 25 (axial, assumed —
cables.md:121 records the real figure as `unknown`) + 15 (`mcc_bend_envelope("NAHDMI-W-B")`,
constants.scad:244, assumed) = 40 mm`, up from the 30 mm the vetoed adapter bought. Full end-zone
table and the resulting per-SKU L: `layout-patch-wall.md` §4/§8. **Family maxima did not change** —
the growth lands on SKUs that were not the family maximum. A right-angle adapter remains available as
an explicit per-variant option; if a variant declares one, it must appear in that variant's BOM.

**Both are in the table now.** The splitter reservation (+20 mm `L`) and the flush boss (+10 mm `W`)
are folded into the figures above; `layout-patch-wall.md` §8 has the per-SKU breakdown. Nothing about
the envelope is blocking any more — the remaining blockers are physical measurements (§12 M1/M2/M3/M5).

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
| Height | **39.0 mm** | set by the **4 mm flange-to-edge web in Z** (D-06 vetoed 2026-09-08): 31 + 2 × 4.0. Also clears the rear-boss minimum 2 × (12.0 + 8.28/2 + 2.0) = 36.28, `d-series-cutout.md:47` + `fdm-rugged-enclosure-guidelines.md:127` |
| Length | `L − 26` (10 mm shell frame band beyond each plate end) | layout-patch-wall.md §2.3 |
| Slots | up to **4**, `pitch = (L − 68)/(n_slots − 1)`, asserted ≥ 32 mm | `placement-and-depth.md:42` |
| Rim | ribbed 3 mm rim around the whole outline | `fdm-...:65-70` |
| Retention | 4 × M3 along +Y, through tabs in the plate's end pads, into bosses on the rabbet lip | |
| Wall stack in Y | 3.0 proud bezel + 2.0 plate seat + 3.0 structural lip = **8.0 mm** | §5 rationale 5 (sacrificial bezel) |

The slots are spread **as wide as the wall allows**, not packed at the minimum pitch — the widest
pitch gives every cable the longest run to its 90° turn and puts the outer slots in the end-zone
corners where the turn is cleanest.

**Consequence recorded:** the plate is now **~168–186 mm** long (`L − 26`, rev 4), not the ~70 × 40 mm
quoted in rationale 4 below. Reprinting it after a drop is still far cheaper than reprinting a 211 mm
shell, but the "small replaceable part" argument is weaker than it was under the in-line topology.
Practical upside: at 39 mm tall it prints flat in the strip left beside the base on one plate.

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

Three rules exist because these features will otherwise collide silently:

- **The floor rule.** `mounts.scad` is the **single owner** of every feature in the case floor: the
  case's own 1/4"-20 insert (for mounting *the case* on a plate/tripod), the VESA 75 × 75 +
  Magewell-Fishtail M4 pattern, the strap slots, the stacking profile and the splitter tie-downs. It
  exposes `mcc_floor_keepout()` and asserts non-overlap between all of them. `cradle.scad` never cuts
  the floor; if it ever needs a penetration it requests one *through* `mounts.scad`.
  **The device-retention through-bolt is withdrawn from the floor (user decision 2026-09-08, D-09):**
  the floor now carries exactly one 1/4"-20 feature, going *down* into a tripod/cheeseplate. Nothing
  in the floor goes up into the device any more, so the old "two 1/4"-20 features must not coincide"
  hazard is gone.
- **The far-wall rule (new, D-09).** Device retention is a **captive 1/4"-20 slotted bolt through the
  far (−Y, non-patch) long wall** into the device's side thread. `fasteners.scad` owns the boss
  geometry (`mcc_captive_side_bolt_boss()` / `mcc_captive_side_bolt_cut()`); `shell.scad` places it
  and publishes `mcc_side_bolt_keepout()`; `vents.scad` **must** subtract that keep-out from the
  far-wall slot arrays, and `cradle.scad` must keep its far-flank ribs out of it. Full geometry:
  `layout-patch-wall.md` §7.1. Rationale: the user physically verified that the device's 1/4"-20
  threaded hole is on a **long side face**, not the bottom (resolves R12).
  **The boss is flush (D-13, 2026-09-08):** it never protrudes past the wall's outer face. The
  captive stack is accommodated by `MCC_GAP_FAR`, which is therefore **derived, not chosen**:
  `MCC_GAP_FAR = max(MCC_GAP_FAR_DUCT_MIN, boss_len + MCC_PAD_T − MCC_WALL) = max(6, 17 + 2 − 3) = 16`.
  Nobody may "optimise" it back to 6 — the 16 mm is a fastener requirement that happens to also buy a
  duct. If a measurement (M5) makes the head taller, **`MCC_GAP_FAR` and hence `W` grow; the wall
  never grows a lug.**
- **The reservation rule.** `shell.scad` always reserves the fan bay and the PoE-splitter bay as
  internal keep-out volume, **even when `fan = false` and `splitter = false`**. Otherwise enabling a
  fan later moves connectors and invalidates every printed part. `fan.scad` and `poe_splitter.scad`
  each expose an `*_envelope()` function used for reservation, separate from the module that cuts
  real geometry.
  **Reserved volume adds, it does not overlap (D-12, 2026-09-08).** Where a reserved bay shares an
  end zone with cable allowances that are needed *regardless* of whether the bay is populated, the
  two **sum**; they are not `max`ed. Concretely
  `ez_neg = max(mcc_dev_side_allow(kind) over −X ports) + (splitter reserved ? splitter_x : 0)`
  `= 27 + 20 = 47`. Treating a reservation as free because "the splitter isn't fitted yet" is exactly
  the retrofit failure this rule exists to prevent.

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
    // Device retention: the 1/4"-20 thread is on a LONG SIDE face (user-verified 2026-09-08).
    // Always face [0,-1,0] — see "The side_bolt convention" below. pos is a placeholder.
    [["id","side_bolt"],["face",[0,-1,0]], ["pos",[  0, 0]], ["kind","tripod_1_4_20"],
     ["dir","none"],    ["panel","none"],       ["confidence","assumed"]]
  ]]
];
```

### The `side_bolt` convention (D-09, user decision 2026-09-08)

Every device record carries **exactly one** port of `kind "tripod_1_4_20"`, and it is **always** on
`face [0,-1,0]`:

| Field | Value | Notes |
|---|---|---|
| `id` | `"side_bolt"` | renamed from `"tripod"` so nothing confuses it with the case's own floor 1/4"-20 insert |
| `face` | `[0,-1,0]` | **invariant** — see the canonical-frame rule below |
| `pos` | `[u, v]` | `u` = mm along the device length from the device centre (`+u = +X` when looking at the −Y face from outside); `v` = mm from the device's mid-height (`+v = up`). From a physical measurement: `u = ±(dev_l/2 − X_from_that_short_end)`, `v = Z_from_device_bottom − dev_h/2` |
| `kind` | `"tripod_1_4_20"` | |
| `panel` | `"none"` | it is never brought out to a Neutrik slot |
| `confidence` | `"assumed"` | **on every SKU today** — nobody has measured `u`/`v` yet |

**Canonical-frame rule.** The device-local frame in a data file is *chosen* so that the side-bolt
hole is on the −Y face; the case then places the device at **zero yaw** and the hole faces the far
wall by construction. If a measurement shows the hole on the other long side, the fix is to
re-author that **device file** — negate `face.x` and `pos[0]` on every port, i.e. rotate the record
180° about Z — not to add a rotation in `shell.scad`. Consequences, all deliberate:

- No `yaw` parameter enters L2 geometry; the device orientation stays pure data.
- **The envelope is yaw-invariant.** `L = 2·MCC_WALL + ez_neg + dev_l + ez_pos` only swaps its two
  end-zone terms, and `W`/`H` do not move at all. A 180° flip mirrors the panel-slot order and
  nothing else, so the case size does not depend on the unmeasured hole side.
- Tier-1 asserts T1-22/T1-23 (`layout-patch-wall.md` §9) enforce "exactly one, on `[0,-1,0]`".

> **Deviation, open (2026-09-08).** All eight device files still carry the pre-decision record
> `["id","tripod"]` on `face [0,0,-1]` (`pro-convert-hdmi-tx.scad:37`, `-sdi-tx.scad:34`,
> `-hdmi-plus.scad:42`, `-sdi-plus.scad:36`) or `face [0,0,1]`
> (`pro-convert-for-ndi-to-hdmi.scad:29`, `-ndi-to-sdi.scad:33`, `-ndi-to-aio.scad:32`,
> `-ndi-to-hdmi-4k.scad:38`), with `pos` values (`[±30,0]`, `[20,0]`) that were positions on the
> bottom/top face and are meaningless on a side face. They must be rewritten to the convention above
> with `pos [0,0]` (the least-wrong placeholder — mid-face keeps the boss clear of both end zones)
> until the user measures. **A developer task, not an architect one.** See §13.

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

**Branching (user decision 2026-09-08 — the `develop` branch is dropped):** work happens on
`feature/*` and merges to `main` by CI-green PR; a release is an annotated `vX.Y.Z` tag on `main`,
which is the only path that produces a GitHub Release (`render.yml:11-17,133-134` already trigger on
`main` + `v*` only; `CONTRIBUTING.md`, the `git-flow` skill, the PR template and the `gitflow.*` git
config still describe `develop` and are stale).

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

**Plus 31 topology asserts (T1-01 … T1-31)** introduced by the patch-wall layout, the side bolt and
rev 4: slot bijection, slot pitch, bay depth and lateral bend fit, end-zone cable allowance
**including the summed splitter term**, plate-fits-wall, boss-to-flange clearance, splitter/fan/vent
non-intersection, the `panel != "MINIDIN8"` guard, the six side-bolt asserts (single `tripod_1_4_20`
port on `[0,-1,0]`; keep-out ∩ vent = ∅; bolt axis inside the device side face; head fully recessed;
clip pocket inside the wall; keep-out ∩ cradle-rib = ∅), and the three rev-4 additions (duct floor,
intake free area vs. the fan aperture, flush boss). Full table with sources: `layout-patch-wall.md`
§9. Do not
re-derive them in the model files; they are the acceptance criteria for `shell.scad`, `panel.scad`,
`cradle.scad`, `mounts.scad`, `vents.scad`.

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
256 mm bed. Resolution: **side-exit, one patch wall.** Both families still fit comfortably after
D-12 and D-13 — plus 211.5 × 166.4, compact 194.9 × 159.9, ≥ 44.5 mm of bed margin in every axis
(≥ 38.5 mm against the 250 mm assert limit) (§1, §14). The
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
the connectors no longer share an end face at all — they sit in the patch wall, which is **168–186 mm**
long. Every priority SKU now has **≤ 4 external D-size ports** (Plus encoder: video IN, loop-OUT,
etherCON, USB-B; TX: video IN, etherCON, USB-B; NDI decoders: video OUT, USB-A host, etherCON,
USB-B; AIO: HDMI OUT, BNC OUT, etherCON, USB-B), and the **HDMI loop-out is brought outside** as the
user wanted. Achieved pitch is **41.97–63.45 mm** at the rev-4 lengths, comfortably above the 32 mm
minimum.

**R4 — HDMI's 2 mm panel cap puts the weakest material at the highest-load point.** A 2 mm ASA
membrane with a 23.8 mm hole, carrying the heaviest, stiffest cable in the build. Mitigations are
already in §5 (separate flat-printed plate, rabbet takes shear, sacrificial bezel, ribs around the
pocket). **Open:** NAUSB-W and NBB75DFG panel-thickness ratings are `unknown`
(`d-series-cutout.md:92-93`) — treat as ≤3 mm and confirm before finalising.

**R5 — thermal. Numbers refreshed 2026-09-08 (rev 4 envelope); conclusion unchanged.** The plus shell
is now 211.5 × 166.4 × 51 mm → external A ≈ **0.109 m²** (was 0.070 m² on the superseded in-line
envelope). At the verified still-air h = 1.6 W/m²K and ΔT = 15 K, passive rejection is ~2.6 W; a 10 W
Plus model needs h ≈ 6.1 W/m²K at ΔT = 15 K, or **~9.2 W/m²K at the realistic ΔT = 10 K** (devices are
rated 0–45 °C (Plus) / 0–40 °C (compact), so a 35 °C venue leaves ~10 K). Still above every
natural-convection figure in `knowledge/design/thermal-guidelines.md:421-443`, so **the fan is not
optional for the 10 W Plus models** — but the margin improved by roughly 25 % purely from the bigger
box. Passive-first stays the intent; §6's reservation rule keeps vent and fan geometry in every
variant from v1. The 16 mm far-wall duct (D-13) is the other thermal gain — see R20 for what it does
*not* fix.

**R6 — PoE power budget.** 802.3af delivers 12.95 W at the PD. A 10 W Plus device + splitter
conversion loss (1–2 W) + fan (0.25–1.3 W) is at or over budget, and the splitter's own heat lands
*inside* the case. Design constraints: put the splitter bay in the **intake** airflow, not against
the device; confirm the chosen splitter's rated continuous output against the worst-case model.
Pending research in `knowledge/components/poe-splitters.md`. **Escalate once that lands.**

**R7 — lid fastener count. RESOLVED; D-04 ACCEPTED by the user 2026-09-08. Outcome revised by D-12.**
Baseline stays the user's 4 captive M3 thumbscrews; **6 for any lid over 180 mm span** (D-04).
Outcome under the **rev-4** envelopes: **compact → 6** (L = 193.9–194.9) and **plus → 6**
(L = 210.5–211.5) — the compact family crossed the threshold when D-12 added 20 mm, so **every
current SKU carries 6**. Keep the threshold rule anyway; a constant `6` would silently break the first
sub-180 mm variant. The two extra fasteners go mid-span on the long walls; on the patch wall the
mid-span position must clear every flange edge by ≥ 6.15 mm. At the rev-4 pitches the clearance is
10.75–10.92 mm (plus, 4 slots), **7.98–8.15 mm (compact, 4 slots — the tightest in the repo, 1.8 mm
spare)** and 18.5–18.7 mm (compact, 3 slots), so **the buttress-rib fallback is still unused on every
priority SKU** — but it is much closer than it was. The far-wall mid fastener now *always* collides
with the side-bolt keep-out and must be displaced by the deterministic rule in
`layout-patch-wall.md` §6. The patch wall is the one that most needs the mid-span restraint — it has a
168–186 mm aperture cut in it.

**R8 — device retention. REVISED 2026-09-08 (D-09: side bolt, not floor bolt).** A single 1/4"-20
bolt is still one point of restraint, now **horizontal, through the far wall into the device's side
thread**; the device can pivot about it, so the printed cradle's locating ribs carry all
anti-rotation load and must be designed as structural, not cosmetic. The compliant pad moved with the
bolt: it is now a 2 mm annular EPDM pad on the **boss face**, between the boss and the device flank,
and it provides the preload. Vibration loosening is real on touring gear — but a thread-locking
compound on a screw that goes into the *customer's device* is not acceptable, so preload must come
from the pad plus a hand-tight slotted head. The exact hole location is still undocumented
(`housing-families.md:70-72`, `:132`); `u`/`v` start at `confidence:"assumed"` and must be measured
per SKU (§12 Q8).

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
part. PARTLY RESOLVED 2026-09-08 (user decision); residue carried into R15.** The user chose
option (a): the default reservation is a **dongle-class 75 × 40 × 20 mm envelope**
(`MCC_SPLITTERS["DONGLE-75x40x20"]`, `constants.scad:164`, `confidence:"assumed"` — the UCTRONICS
U6114/U6115 dimensions are unpublished, `poe-splitters.md:129-136`; the user will buy one and
measure). `GAT-USBC` stays in the table as a named non-default alternative
(`constants.scad:168`). That clears the **connector-bay** collision (T1-16 now passes: the dongle
bay reaches `y = −0.2`, slot 1's etherCON plug envelope stops at `y = +10.6`). It does **not** clear
the **end-zone** collision — see **R15**. Original analysis, kept for the record:
§6's reservation rule requires the splitter bay to be
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

**R12 — the device's 1/4"-20 hole is not on the bottom. RESOLVED 2026-09-08 by physical
verification.** The user checked the hardware: the thread is on a **long side face**. The floor
through-bolt is withdrawn entirely and retention becomes the captive side bolt (D-09, §6 far-wall
rule, `layout-patch-wall.md` §7.1). This removes the three-SKU exception — every SKU is now retained
the same way, which is strictly better than the "bolt through the lid on decoders only" fallback that
was on the table. The manual's "Top, near Face A … + 1/4"-20 hole"
(`knowledge/magewell/housing-families.md:139`) is therefore a transcription/figure error; leave the
knowledge file alone (it records the source faithfully) but do not design to it. Residue: **which**
long side, and the hole's `u`/`v`, are unmeasured on every SKU — see R17 and §12 Q8.

**R13 — right-angle HDMI adapter. RESOLVED 2026-09-08: D-08 VETOED by the user.** No right-angle
adapter in the default BOM. End zones are sized for a *straight* plug instead:
`ez(hdmi_a) = 25 + 15 = 40 mm`, where 25 mm is an **assumed** axial plug length (`cables.md:121`
records it as `unknown — physically measure`) and 15 mm is `mcc_bend_envelope("NAHDMI-W-B")`
(`constants.scad:244`, itself assumed). Cost: +10 mm of `L` on every HDMI-ended SKU; the family
maxima are unchanged because those SKUs were not the maximum. The `depth-mockup` coupon must measure
the real figure **before the shell is printed**; if it lands above 25 mm the HDMI SKUs grow further.
A right-angle adapter is still allowed as an explicit per-variant option and must then appear in that
variant's BOM (`bom-update`). This risk is now carried by R2 (all plug lengths assumed) — it is no
longer a BOM obligation.

**R14 — bed area, not bed length, is now the ASA warp risk. UPDATED 2026-09-08 (rev 4).** The plus
base is now **211.5 × 166.4 = 35,200 mm²** of first layer (compact 194.9 × 159.9 = 31,200 mm²) — 17 %
more than rev 3's 30,000 mm² and **~80 % more than the superseded in-line 244 × 80 = 19,500 mm²**.
D-12 added the length, D-13 added the width. R9's mitigations (generous bottom-edge fillet, uniform
walls with ribs, brim, enclosure at temperature) become more important, not less, even though the
longest dimension is still 33 mm shorter than the in-line layout's. Print time and filament per case
rise correspondingly, and base + lid can no longer share a build plate (§1) — **two plates per case,
minimum.** This is the accepted price of D-12 + D-13 and should be stated in the BOM/print notes.

**R15 — the dongle-class splitter reservation collides with the −X end zone. RESOLVED 2026-09-08 —
user accepted option (a), recorded as D-12.** `ez_neg = 27 + 20 = 47`; every `L` grows 20 mm
(compact 194.9, plus 211.5); §6's reservation rule is honoured unconditionally; assert T1-28 now
passes by construction. Accepted consequences, all recorded in §1 and `layout-patch-wall.md` §8:
the **compact family crosses the 180 mm D-04 threshold and goes to 6 lid thumbscrews**; bed margin
falls to 44.5 mm on the plus family (still 38.5 mm inside the 250 mm assert limit); first-layer area
rises (R14). Two knock-ons a developer must not miss:
(i) `MCC_END_ZONE_NEG_EXTRA_SPLITTER` is **derived**, not typed — it is
`mcc_splitter_envelope(part)[2]` (the on-edge X extent, = `size[2]` = 20 for `DONGLE-75x40x20`,
`constants.scad:164`), so measurement **M3** flows straight into `L` without another decision;
(ii) with `ez_neg ≠ ez_pos` the device is no longer centred in X — `x_dev_c = +3.0…+3.5` on every
priority SKU — which pushes the default side-bolt keep-out off case centre and *always* displaces
the far-wall mid-span lid fastener (`layout-patch-wall.md` §6).
Original analysis, kept for the record: R11's dongle envelope clears the *connector bay* but not the
*cable* end zone. Standing on edge (20 mm in X, 75 mm in Y, 40 mm in Z — the only orientation that
fits a 45 mm interior) the reserved slab occupies the outer 20 mm of a 27 mm end zone, across the
full case width, at exactly the height the device's −X patch cables run (`z ≈ 19.5–31.5`, centred on
the 25.5 mm connector centreline). The device's own USB-B and RJ45 plugs still need their 17/27 mm
whether or not a splitter is fitted, so the two allowances **sum**, they do not `max`:
`ez_neg = 27 + 20 = 47 mm`. Cost: **+20 mm of `L` on every variant** → compact 194.9, plus 211.5
(bed margin 61.1 / 44.5 mm — still legal). Options: (a) accept the +20 mm and honour §6's
reservation rule unconditionally — architecturally clean, recommended; (b) make the splitter a
declared per-variant option and reserve nothing by default — cheapest cases, but it breaks the
reservation rule and a later retrofit invalidates every printed part, which is precisely what that
rule exists to prevent; (c) source a physically smaller splitter (≤ 60 × 40 × 15) once the user has
one in hand and re-derive. Note the previous doc's "costs `max(0, 40 − ez_neg)` extra mm" is wrong —
it assumed the splitter and the device-side plugs could share the end zone, and they cannot, in
either Z or Y. Secondary: the on-edge slab also masks the far half of the −X end wall, so the intake
vent band there must move to the +Y half (`layout-patch-wall.md` §5) — **this part still applies.**

**R16 — the captive side bolt is not an off-the-shelf part. NEW, sourcing risk.** The design needs a
1/4"-20 slotted machine screw, ~19 mm under the head, with a **retaining groove ~10 mm below the
head** for a DIN 6799 E-clip. Stock 1/4"-20 × 3/4" slotted screws are fully threaded and have no
groove, so either (i) the groove is turned/filed into a stock screw (a shop operation, and it lands
in the threaded section), or (ii) a pre-grooved captive panel screw is sourced —
`knowledge/components/fasteners-and-hardware.md:98` records a McMaster "Captive Panel Screws" family
including slotted drives, but stocked sizes/lengths are `unknown`. Alternatives if the E-clip proves
impractical: a cross-drilled ⌀2 mm roll pin through the shank, or a grub-screw shaft collar, both
sitting in the same clip pocket. **The E-clip dimensions themselves are unverified** — DIN 6799 is
not in `knowledge/**`; the size-5 figures in `layout-patch-wall.md` §7.1 are marked `assumed` and are
on the measurement list. Do not order hardware on them.
**Unaffected by D-13.** The flush decision leaves `proud + MCC_WALL + MCC_GAP_FAR = 19 mm` exactly as
it was (0 + 3 + 16 = 10 + 3 + 6), so `screw_len_under_head` is still 19.0 mm → stock 3/4" (19.05), and
`groove_pos` is still 10.0 mm below the under-head face. The sourcing problem is neither better nor
worse; only where the boss material sits has changed.

**R17 — the side-bolt hole position is unmeasured, and one of the two unknowns is geometrically
tight. NEW.** `u` (along the length) is benign — it only shifts the boss along the far wall and the
vent arrays step around it. `v` (height above the device's mid-plane) is not: the boss's compliant
pad must land wholly on a device flank that is only 23.3–23.4 mm tall, so
`pad_od ≤ dev_h − 2·|v| − 2`. **Unchanged by D-13** — the pad still lands on the device flank at the
same place; only the material behind it moved inboard. With the default ⌀18 pad that allows
`|v| ≤ 1.7 mm`; a ⌀12 pad (the
smallest sourced EPDM size, `fasteners-and-hardware.md:186`) allows `|v| ≤ 4.7 mm`. If the real hole
sits further off mid-height than that, the pad has to become a non-circular bearing face and the boss
spec needs revisiting. Measure `v` **before** `cradle.scad`/`shell.scad` are written, not after.
Second-order: on HDMI TX / SDI TX the 16-position rotary switch is authored on the **same** −Y face
(`pro-convert-hdmi-tx.scad:34`, `-sdi-tx.scad:31`); the boss keep-out must clear it, and if the bolt
hole turns out to be on the opposite side the canonical-frame flip (§7) puts the rotary switch facing
the patch wall, where it is unreachable — acceptable today (it is `panel:"none"`), but record it if
the user ever wants rotary access.

**R18 — the far wall grows a 10 mm proud lug. RESOLVED 2026-09-08 — the user chose FLUSH, recorded as
D-13.** The captive stack (head recess 6 + retaining web 3 + clip pocket 8 = 17 mm) needs 17 mm
between the case's outer surface and the pad face. Rev 3 bought it with a 10 mm outward lug; **rev 4
buys it by moving the whole far wall out**: `MCC_GAP_FAR` 6 → **16**, `MCC_SIDE_BOLT_PROUD` 10 → **0**,
`MCC_WALL + MCC_GAP_FAR − MCC_PAD_T = 3 + 16 − 2 = 17` exactly. What this bought:

- **No proud metal or plastic anywhere on the shell.** The drop rule (§5 sacrificial bezel, recessed
  connectors) now holds on all six faces. The far wall is clean for the strap slots and the stacking
  profile again, and the stress riser at the lug root is gone.
- **The printed bounding box did not change** (rev 3's bbox was already `W + 10`), so bed margin and
  the T1-21 assert are untouched. The 10 mm became *interior*.
- **A 16 mm airflow duct along the device's far flank**, up from 6 mm — ~2.7 × the duct
  cross-section. See R20 for why that is a smaller win than it looks.
- **The M5 risk changed shape.** A taller measured screw head now grows `MCC_GAP_FAR` and therefore
  `W` (≈ +1.5 mm of `W` per +1.5 mm of head height) instead of growing a lug. Bounded, cheap, and it
  fails loudly through T1-26 rather than silently producing an ugly lump.

What it cost, and the one thing that got harder:

- **~17 % more first-layer area and more ASA** in the floor and lid (R14).
- **The 14 mm cantilever moved inside the wall.** The boss is now a local thickening on the *inside*
  of the far wall — a ⌀20 cylinder from the wall's inner face (local `Z = 3`) to the pad face
  (`Z = 17`). Printed floor-down that is a horizontal ⌀20 cylinder cantilevered 14 mm off a vertical
  wall: its lower half is an unsupported overhang, and a purely conical ≤45° blend would need a ⌀48
  root, which collides with the vent band, the cradle far-flank ribs and the lid-fastener boss.
  **Normative resolution (`layout-patch-wall.md` §7.1): a central vertical support web** — 3 mm thick
  in X, in the plane `x = x_bolt`, from the interior floor `z = 3` to the boss underside, spanning the
  boss's full Y extent — which caps every unsupported horizontal span at `(20 − 3)/2 = 8.5 mm`, inside
  the §5 "no unsupported horizontal span over 10 mm" rule. The web is free in airflow terms because
  the boss already dams the duct at that X, but it **extends the far-wall vent keep-out downward** to
  a 7 mm-wide strip from `z = 3` to the boss (a slot cut there would open into solid material).
  Fallback if a developer prefers it: local slicer support under the boss — the base prints with its
  top open, so the boss is reachable for support removal. Do not mix the two on one variant.

**R19 — repeated screwdriver load on an ASA head-bearing web. NEW.** The 1/4"-20 thread is in the
*device* (metal), so the ASA boss never takes thread-forming torque — but the 3 mm web behind the
head recess takes the full clamp load and gets scrubbed every time the device is swapped. Mitigation
to specify in the BOM: a stainless washer (⌀12–14 × 1 mm) seated on the recess floor under the head.
Do not solve it by increasing torque headroom — hand-tight against the compliant pad is the intended
preload (R8). **D-13 makes this slightly worse and slightly better:** the web is now 3 mm of wall-
backed material instead of 3 mm of lug material (better in bending), but the head recess is a ⌀12 bore
straight through the 3 mm wall, so the wall itself carries no material at the bolt axis — the boss and
its support web are the load path. The washer stays mandatory.

**R20 — the 16 mm duct is not the thermal win it looks like; the vent *slots* are now the bottleneck,
and the fan is not aligned with the duct. NEW (2026-09-08), non-blocking, decide before `vents.scad`.**
`knowledge/design/thermal-guidelines.md:104-109` is explicit that vent openings "mainly need to be
large enough to not throttle the buoyancy-driven flow", and that the defensible sizing approach is to
make vent free area **comfortably larger than the fan's inlet/outlet duct area** when a fan is fitted.
Order-of-magnitude check with the rev-4 geometry:

| Path | Free area | Note |
|---|---|---|
| Fan aperture ⌀38 | **1134 mm²** | the thing everything else must feed |
| Far-wall duct cross-section (16 × 45) | 720 mm² | was 270 mm² at `MCC_GAP_FAR = 6` |
| Total internal cross-section normal to X, minus the device | ≈ 5400 mm² | the fan is never starved by the *case* |
| Far-wall intake slot band as specified (12 mm tall, 1.2 mm slot / 1.6 mm web, over the device length) | ≈ 590 mm² | |
| −X end-wall intake band, +Y half only | ≈ 400 mm² | |
| **Total intake free area** | **≈ 990 mm²** | **< 1134 mm² — under the cited heuristic** |

Two conclusions. **(1)** D-13 removed the duct as a restriction (720 mm² is one of several parallel
paths, and the total internal cross-section is 5 × the fan), so *widening the duct further buys
nothing thermally* — the correct lever is slot open area, i.e. a taller intake band and/or a higher
slot:web ratio. Sizing the *duct* to the fan is the wrong assert; sizing the *slots* to the fan is the
right one (new T1-30). **(2)** The fan aperture is centred on `y_dev_c`, roughly 40 mm away from the
duct mouth, so as drawn the fan pulls from the plenum over the device and only indirectly through the
duct. With a 16 mm duct there is now a real choice: keep the fan on the device centreline (even
cooling of the device's top grille, which §12 Q10 forbids sealing) or shift it toward −Y so the ⌀38
circle overlaps the duct (a genuine through-duct flow path). **Architectural hedge, not a decision:**
make the fan's Y position a shell parameter `fan_y`, defaulting to `y_dev_c` (today's behaviour), and
settle it with a thermal measurement rather than by argument. Escalate to the user only if they want
to pre-commit.

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
6. ~~**PoE splitter part and placement**~~ **RESOLVED 2026-09-07/08:** default reservation is the
   dongle class `DONGLE-75x40x20` (`constants.scad:164`), `GAT-USBC` retained as a non-default
   alternative; placement is the −X end on edge, and its 20 mm X extent **adds to** the −X cable
   allowance (`ez_neg = 47`, D-12/R15). The *envelope* is still `assumed` — measurement M3 feeds
   `L` directly.
7. **All mating-plug lengths** (R2) — placeholder constants until the `depth-mockup` coupon is built.
   Now includes the **straight HDMI plug's axial length**, assumed 25 mm, `unknown` in
   `cables.md:121`; the whole HDMI end-zone figure rests on it since D-08 was vetoed.
8. **Device side 1/4"-20 hole: `u`, `v`, and which long side** — measure per SKU (R8, R17). `u` from
   the nearest short end, `v` from the device bottom, side seen from the USB/RJ45 end. Gating for
   `cradle.scad`/`shell.scad`; `v` is the tight one.
9. **NAUSB-W / NBB75DFG panel-thickness rating** (R4) — assumed ≤3 mm.
10. **Fan presence in HDMI Plus / SDI Plus** is contradictory across Magewell's own sources
    (`housing-families.md:44-53`). The case design must not depend on the device having or not having
    an internal fan: do not seal the device's top grille in any variant.
11. **`knowledge/` vs `.claude/knowledge/` split.** `knowledge/` is product/domain research (sourced,
    cited, stable). `.claude/knowledge/` is agent working memory (architecture, testing,
    ticket-source). Do not merge them; do not put sourced research in `.claude/`.
12. ~~**Where the NDI decoders' 1/4"-20 hole actually is**~~ **RESOLVED 2026-09-08 by physical
    verification: on a long side face, on every SKU** (R12). Design to the side bolt (D-09), not to
    `housing-families.md:139`.
13. ~~**Straight vs. right-angle HDMI at the device end**~~ **RESOLVED 2026-09-08: D-08 vetoed,
    straight plug** (R13). The magnitude is still unknown — folded into Q7.
14. ~~**Two architect-derived rules flagged for user veto**~~ **RESOLVED 2026-09-08: D-04 accepted
    (6 fasteners over 180 mm), D-06 vetoed** (the flange-to-plate-edge web stays 4.0 mm in Z, so the
    plate is 39 mm and the case is **51 mm** tall, not 49).
15. ~~**Splitter reservation vs. the −X end zone (R15), and the 10 mm proud side-bolt lug
    (R18)**~~ **RESOLVED 2026-09-08: D-12 (accept +20 mm of `L`, reservation allowances sum) and
    D-13 (flush boss, `MCC_GAP_FAR = 16`, `MCC_SIDE_BOLT_PROUD = 0`).** See §1 and §11.
16. **Fan Y position vs. the 16 mm duct (R20) — new, non-blocking.** Keep the fan on the device
    centreline or shift it onto the duct? Parameterise (`fan_y`, default `y_dev_c`) and settle it by
    measurement, not argument.

### Measurement list (blocks `shell.scad` / `cradle.scad` / the first full-size print)

| # | Measure | Why it blocks | Who |
|---|---|---|---|
| M1 | Side 1/4"-20 hole `u` (from the nearest short end), `v` (from the device bottom), and **which long side** (seen from the USB/RJ45 end) — **per SKU** | Places the boss; `v` may force a smaller pad or a redesign (R17) | User, with the devices in hand |
| M2 | The device's side-thread **depth** | Sets bolt engagement `e` (assumed 6.0), which sets clip travel, pocket depth and screw length | User |
| M3 | The chosen dongle PoE splitter's real L × W × H | The 75 × 40 × 20 default is `assumed`. **Since D-12 its on-edge X extent (`size[2]`, 20 mm) is a direct term in `ez_neg` and therefore in `L`** — a part 5 mm thicker makes every case 5 mm longer (R11, R15) | User, after buying one |
| M4 | E-clip: confirm DIN 6799 nominal size for a 6.35 mm shank — groove ⌀, groove width, clip OD, thickness | Every figure in `layout-patch-wall.md` §7.1's clip block is `assumed`; not sourced anywhere in `knowledge/**` (R16) | Whoever orders the hardware |
| M5 | Slotted 1/4"-20 screw head ⌀ and head height for the part actually bought | Sets the head recess ⌀/depth → `boss_len` → **`MCC_GAP_FAR` → `W`** since D-13 (it no longer sets a lug height). +1.5 mm of head height = +1.5 mm on every case's width; T1-26 fails loudly if it is not propagated (R18) | Same |
| M6 | Straight HDMI plug axial length; etherCON/USB/BNC plug lengths | `depth-mockup` coupon — replaces every `assumed` bay depth and end zone (R2, R13) | Print the coupon |
| M7 | Magewell Fishtail M4 hole pitch | Floor pattern; derive from `knowledge/magewell/assets/magewell-fishtail-bracket.stl` | Anyone |

---

## 13. Deviations log

Record each detected deviation with: date, intended rule, `file:line` of the violation, why it
matters, and the resolution (fixed / accepted-and-rule-updated / escalated).

| # | Date | Intended rule | Violation | Why it matters | Resolution |
|---|---|---|---|---|---|
| D1 | 2026-09-08 | §7 `side_bolt` convention: exactly one `tripod_1_4_20` port, `face [0,-1,0]` | `pro-convert-hdmi-tx.scad:37`, `-sdi-tx.scad:34`, `-hdmi-plus.scad:42`, `-sdi-plus.scad:36` use `face [0,0,-1]`; `-for-ndi-to-hdmi.scad:29`, `-for-ndi-to-sdi.scad:33`, `-for-ndi-to-aio.scad:32`, `-for-ndi-to-hdmi-4k.scad:38` use `face [0,0,1]`. `id` is `"tripod"`, and `pos` (`[±30,0]`, `[20,0]`) is a bottom/top-face position | `cradle.scad`/`shell.scad` will place the retention boss from this field; a bottom-face record silently produces a floor bolt that cannot reach the thread | **Resolved 2026-09-08** (commit bb1497f: all 8 device files carry `side_bolt` on `[0,-1,0]`, T1-22 in `test_ports.scad`). Original instruction: rewrite all 8 to `["id","side_bolt"], ["face",[0,-1,0]], ["pos",[0,0]], ["confidence","assumed"]`, add T1-22/T1-23 to `tests/test_ports.scad`. Re-verify at the end of that task |
| D2 | 2026-09-08 | §6 floor rule: the floor no longer carries a device through-bolt | `lib/mcc/fasteners.scad:100-120` `mcc_tripod_boss()` is a boss with a ⌀6.6 **clearance** through-hole — i.e. exactly the withdrawn floor through-bolt geometry. The floor's remaining 1/4"-20 feature is a *threaded* one (case → tripod plate) | An unused module whose contract contradicts the design will be picked up by the first developer who greps for "tripod" | **Resolved 2026-09-08** (commit bb1497f retired `mcc_tripod_boss()` in favour of `mcc_case_tripod_insert_boss/_bore()`; flush reconciliation in the follow-up commit). Original note: same task that adds `mcc_captive_side_bolt_boss/cut()` to `fasteners.scad`. Either repurpose it as a 1/4"-20 *insert* boss for the floor, or retire it. Re-verify at the end of that task |
| D3 | 2026-09-08 | §8 branching: `develop` is dropped | `CONTRIBUTING.md`, `.claude/skills/git-flow`, the PR template, `CHANGELOG.md` and the `gitflow.*` git config still described `develop`. `.github/workflows/render.yml:11-17` was already correct | An agent reading `git-flow` will open a PR against a branch that should not exist | **RESOLVED 2026-09-08.** Branching docs rewritten: `CONTRIBUTING.md:4-6` and `.claude/skills/git-flow/SKILL.md:9-11` now state "There is no `develop`, `release/*`, `hotfix/*`, or `support/*` branch"; `CLAUDE.md:116-117`, the PR template, `CHANGELOG.md`, `README.md` and `.claude/knowledge/ticket-source.md` updated; CI triggers already `main` + `v*` + PRs to `main`; the `gitflow.*` git config was removed. Verified by grep: the only remaining `develop` hits in tracked non-BOSL2 files are negations or the English word "developer" |
| D4 | 2026-09-08 | Nothing but source and small text goldens in the working tree (§8) | Two untracked junk files in the repo root, `5` and `RJ45,` (`git status`), almost certainly the debris of a mis-quoted PowerShell redirect | They will be swept into a commit by a `git add -A`, and CI's stray-file guard may or may not catch them | **Open — trivial housekeeping, teamlead's call.** Delete them (architect is read-only; I have not touched them). Not a design issue |

---

## 14. Patch-wall layout contract

**Full contract: [`layout-patch-wall.md`](layout-patch-wall.md).** It is normative for `shell.scad`,
`panel.scad`, `cradle.scad`, `mounts.scad` and `vents.scad`, and every number in it is cited to
`knowledge/**:line` or `lib/mcc/constants.scad:line`, or marked `assumed` / `unknown`. Summary:

**Frame.** Origin at the case's outer bbox centre in X/Y, at the underside in Z. X along the device
length, +Y towards the patch wall, +Z up. Interior floor `z = 3`, lid underside `z = 48`, patch wall
inner face `y = W/2 − 8`.

**Panel aperture.** Patch-wall stack in Y = 3.0 proud bezel + 2.0 plate seat + 3.0 structural lip =
8.0 mm. Aperture Z range `[6, 45]`, X range `±(plate_l/2 − 3)` with `plate_l = L − 26`. Connector
centreline `z = 25.5`.

**Cradle deck is derived, not chosen.** It is set so the device's end-face port centreline lands on
the connector centreline (`z = 25.5`), giving an 8.8 mm cradle deck + 2.0 mm compliant pad and a
level cable run. That in turn leaves 10.8 mm of plenum over the device's top grille.

**Device retention is a side bolt, not a floor bolt (D-09), and its boss is flush (D-13).** Device
flat on the cradle at zero yaw, its 1/4"-20 side thread facing −Y; a captive 1/4"-20 slotted screw
runs horizontally through a boss in the far wall into that thread, held captive by a DIN 6799 E-clip
in a pocket inside the boss. **Nothing protrudes:** `MCC_SIDE_BOLT_PROUD = 0` and the 17 mm captive
stack lives inside `MCC_WALL + MCC_GAP_FAR = 19 mm`, with the boss a ⌀20 internal thickening from the
wall's inner face to the pad face plus a 3 mm central support web down to the floor. The floor keeps
only the case's own 1/4"-20 insert, VESA 75 + Fishtail M4, strap slots and the stacking profile — and
the stacking profile no longer has to dodge a lug.

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
end's ports: BNC 41, **HDMI 40 (straight plug — D-08 vetoed, R13)**, RJ45 27, USB 17 — **plus, on the
−X end only, the reserved splitter's 20 mm on-edge X extent (D-12): `ez_neg = 27 + 20 = 47`.**

**Reserved bays.** Fan: +X end wall, NF-A4x10 frame inside, **⌀38** wall aperture (the interior grew
to 45 mm), exhaust away from the patch wall; its Y position is a shell parameter defaulting to the
device centreline (R20). PoE splitter: −X end, **dongle class 75 × 40 × 20 standing on edge** — clears
the connector bay by 20.8 mm (R11) *and* the end-zone cables by construction now that the allowances
sum (D-12, T1-28 passes). Vents: intake low in the −X end wall (+Y half only, the splitter slab masks
the −Y half) and the far long wall (into the **16 mm** `MCC_GAP_FAR` duct along the device flank),
exhaust high in the far wall's +X half; **never in the patch wall**, and **never inside the side-bolt
keep-out** (⌀24 disc *plus* a 7 mm strip down to the floor for the boss's support web, D-13). Slot
free area — not duct depth — is the flow bottleneck; size the intake slots against the fan aperture
(R20, T1-30).

**Floor.** VESA 75×75 and the case's own 1/4"-20 insert default to the case plan centre; `vesa_pos`
is a shell parameter so a colliding SKU can shift it; `mcc_floor_keepout()` asserts non-overlap. The
device-retention through-bolt is **no longer a floor feature** (D-09).

**Architect verdict, 2026-09-08 (rev 4): APPROVED.** Both remaining design blockers are closed by
user decision — **D-12** (R15: reservation allowances sum, `ez_neg = 47`, +20 mm `L`, 6 thumbscrews on
both families) and **D-13** (R18: flush side-bolt boss, `MCC_GAP_FAR = 16`, `MCC_SIDE_BOLT_PROUD = 0`,
+10 mm `W`, printed bbox unchanged). Both are architecturally *cleaner* than the alternatives they
replace: D-12 keeps §6's reservation rule unconditional, D-13 keeps the drop rule true on all six
faces and converts a lug-height risk into a bounded width risk. Envelopes: **compact
194.9 × 159.9 × 51.0, plus 211.5 × 166.4 × 51.0**, every part ≥ 38.5 mm inside the 250 mm assert
limit. `shell.scad` may now be specified against `layout-patch-wall.md` rev 3.

Still open, none of it blocking the *design*:
- **Physical measurements M1/M2** (side-hole `u`/`v`/which side; thread depth) block the first
  full-size **print**, not the code — `pos [0,0]` is the recorded placeholder and T1-24 catches a bad
  value at render.
- **M3/M5** now feed `L` and `W` directly (see the measurement list) — expect the envelope to move by
  a few mm when the hardware lands. That is by design; nothing is hand-typed.
- **R20** (fan Y vs. the 16 mm duct; intake slot free area below the cited heuristic) — parameterise
  `fan_y`, widen the intake band, decide by measurement.
- Deviations **D1/D2/D3 are resolved** (2026-09-08); **D4** is
  two junk files in the repo root awaiting a `rm`.
