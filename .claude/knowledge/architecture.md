# Architecture — magewell-converter-cases

Status: **revision 10, 2026-09-09.** Rev 10 is the architecture gate for
`docs/plans/2026-09-09-printed-m3-threads.md` (issue #30 — the Neutrik D-flange fixing holes become
**printed M3×0.5 internal threads** in the existing rear pad on the panel plate, replacing the M3
heat-set inserts). Verdict: **APPROVED WITH CHANGES — 7 blocking (B1–B7)**; full verdict, rulings
and dispatch scope in that plan file's **§9 "Architect verdict"**.

What rev 10 changes here: **§5 "Connector fixing" gains the dated evolution note below** (the
connector-fixing bosses become threaded pads; **the plate's own 4 retention bosses in `shell.scad`
are UNCHANGED — still heat-set inserts**); **§3's `$fn` policy gains one named, bounded exception**
for `screw_hole(thread=true)` bores; §9's assert list gains **T1-42a/b/c**; §11 gains **R28**; §12
gains measurement **M16**. **No envelope figure moves on any SKU** — the pad's OD (8.28) and height
(7.0) are pinned to their pre-#30 values precisely so the wall window, `d_rel = 8.88` and every
T1-34a–d number are numerically unchanged.

**The blocking correction that matters most (B1).** The plan's `MCC_THREAD_M3_SLOP = 0.15` produces
**no thread at all**. BOSL2 enlarges an internal thread by **`4·$slop` in diameter**
(`lib/BOSL2/screws.scad:753`, `lib/BOSL2/threading.scad:179`), i.e. `2·$slop` per side, while M3×0.5
has only `0.5·(3.000 − 2.459) = 0.2705 mm` of radial engagement. At `$slop = 0.15` the hole grows
0.30 mm per side — more than the whole thread depth — leaving a plain ⌀3.6 bore. **`$slop = 0.05`**
(BOSL2's own tested figure, `screws.scad:767`). The general rule this repo takes from it:
**`$slop` on a BOSL2 internal thread is `2·$slop` per side, and it must always be checked against
the thread's own radial engagement** — that check is now assert **T1-42c**, and it is the assert
that would have caught this before the printer did.

Rev 9 history follows. Rev 9 is the architecture gate for four researcher plans:
`docs/plans/2026-09-09-mount-rail-and-brackets.md` (#25/#26/#27), `…-cradle-deck.md` (#29),
`…-lid-vents.md` (#24), and their cross-cutting merge order. Verdicts:

| Plan | Issue | Verdict |
|---|---|---|
| Mount rail + brackets | #25 rail, #26 TV bracket | **APPROVED WITH CHANGES** (5 blocking) |
| Truss bracket | #27 | **REJECTED for now — DEFERRED** pending measurement **M14** and a user safety sign-off (PLAN-ASSUMPTION 1) |
| Cradle deck lattice | #29 | **APPROVED WITH CHANGES** (3 blocking) |
| Lid vents | #24 | **APPROVED WITH CHANGES** (2 blocking) |

New in rev 9: **`lib/mcc/rail.scad` at L1** (§3 — the plan's `bracket.scad` is renamed; a file named
for its consumer invites bracket-plate geometry into L1); **decision D-15** (the rail replaces VESA
75 × 75 as the case's floor mount, user decision); **D-16** (`cfg.tripod_insert` defaults **true** —
teamlead decision 2026-09-09, the user asked to keep every mounting option and dropped only VESA);
**D-17** (the deck is a ribbed lattice, not a solid slab). §6's floor rule is rewritten. Risks
**R24–R27**, measurements **M14–M15**, deviations **D19–D22**, asserts **T1-36 … T1-41**
(`layout-patch-wall.md` §9). Full rulings, including every `PLAN-ASSUMPTION` verdict and the ordered
developer dispatch: **`layout-patch-wall.md` rev 9, §17.**

**The five blocking corrections a developer must not skip** (details in §17):

1. **`MCC_RAIL_SILL_H = MCC_RAIL_DEPTH + MCC_FLOOR_T = 7.0`, not 6.0.** At 6.0 the 4 mm groove
   leaves **2.0 mm** of ASA over it — below the uniform 3 mm shell spec (§9 "wall thickness ≥
   `MCC_WALL`") on the one load path that carries the whole case when it is bracket-mounted.
2. **`MCC_RAIL_Y = −20.0`, not +20.0.** Same keep-out arithmetic by symmetry, but it puts the rail
   **under the device and the cradle deck** instead of free-standing in the connector bay, and it
   puts the case's mass *below* the rail when the patch wall hangs down (#26's own orientation
   requirement). See R24.
3. **D16's pairwise floor assert must exempt the `case_tripod_insert` / `fishtail_reserve` pair.**
   They are deliberately concentric at `(0,0)` (`layout.scad:271,276`); a naive pairwise check fails
   on all 8 SKUs on the first render (deviation **D19**).
4. **`vents.scad` must gain `use <ports.scad>`.** The lid-vent asserts call `mcc_dev_slug(dev)`,
   which lives in `ports.scad`; OpenSCAD's `use` is not transitive, so every assert message would be
   an undefined-function error (deviation **D20**).
5. **`_mcc_deck_rib_blocked()` as specified deletes whole rib lines**, because it tests a rib's full
   AABB against a keep-out. Drop the filter for v1 (recommended — `cradle.scad` is additive and
   above the floor) or make it per-segment with a published allowlist (deviation **D21**).

Rev 8 history follows. Rev 8 is the fit-check of the user's **fan-power decision**
(2026-09-09, four parts: PoE-only on stage; NF-A4x10 5V *plain* in series with a KSD9700 45 °C NO
bimetal switch on the device's metal top; **decoders** take 5 V from the device's **USB-A host**
port and **encoders** from the **Mini-DIN-8 pin 8 VCC**, no PoE splitter by default; the decoders'
now-unused host slot becomes a **`DBA-BL-B` blank that stays reusable**). Recorded as decision
**D-14** (`layout-patch-wall.md` §10; consequences in §5, §6, §11, §12 here). Verdict:
**APPROVED, with one blocking measurement on the two Plus encoders.**

- **`DBA-BL-B` gets a real hole (§5, ruling A).** `hole_d 0 → 24.0` (etherCON class, the universal
  D punch), `depth`/`plug_len`/`bend` untouched, so a blanked slot costs **no** bay depth, keeps
  rank `[0,0]` (innermost), and moves **no** envelope figure on any SKU. This is what makes §9's
  "every port with `panel != "none"` has a cutout" invariant *true* now that a blank is reachable.
  It requires one library fix: `neutrik.scad:39` tests `kind == "blank"` while `shell.scad:181` and
  `layout.scad:187` test `hole_d == 0` — the three must agree on `hole_d == 0`, or the wall window
  opens and the plate under it stays solid (deviation **D18**).
- **Decoders: no geometry change.** Blanking is a `panel` field edit in three device files.
- **Encoders (HDMI Plus, SDI Plus): BLOCKED on measurement M12.** The Mini-DIN-8 is `panel:"none"`,
  so `mcc_end_zone()` (`layout.scad:45`) and T1-18(c) (`shell.scad:373`) both filter it out — the
  end-zone solver is blind to a port that stays internal but is now *internally cabled*. The plug
  sits at `(y_dev_c, z = 19.5)`, dead inside the ⌀38 fan aperture, with **30.0 mm to the fan frame
  and 25.0 mm to the reserved fan envelope**. The Magewell breakout plug's axial length is
  `unknown` (**R23**, M12). **Do not let a developer type a guessed figure into
  `MCC_PLUG_AXIAL`.**
- **R6 (PoE budget) is largely retired for the default build**, **R21/R22/R23** are new, and the
  measurement list gains **M8–M13**. Per-SKU consequences and the §2.5 blank ruling:
  **`layout-patch-wall.md` rev 8, §2.5 + §16.6.**

Rev 7 history follows. Rev 7 is the **pre-implementation architecture gate for the seven
remaining SKUs** (GitHub issues #3–#9), which are to be built in parallel on seven branches. Verdict:
**APPROVED WITH ONE BLOCKING LIBRARY CHANGE.** Six of the seven need no library edit at all — §4's
acceptance test ("adding a device = one thin assembly + goldens + BOM, no library change") holds —
but **T1-18(c) as coded fails on all four BNC-ended SKUs** (SDI TX, SDI Plus, NDI to SDI, NDI to
AIO) because it charges the BNC cable's *lateral* bend radius against the *axial* +X end-zone
budget. That fix, plus a stale-skill fix, must land **once, first, on a single pre-flight branch**
before any of the seven is opened. Rev 7 also carries two record corrections: **§5's boss-relief
positions** (the *placed* plate's rear bosses are at `(−9.5, −12)` and `(+9.5, +12)` relative to the
slot centre — the rev-6 `(∓9.5, ±12)` was the mirror; `shell.scad` was corrected on 2026-09-08,
commit 2a7e0b0) and **D10's resolution** (the plate-fixing bosses carry a genuine *through*-bore).
Per-SKU fit-check table, ruling, and the parallel-work rules: **`layout-patch-wall.md` rev 7, §16 +
§15 "Ruling 2026-09-08c"**. New deviations **D12–D16** in §13. Nothing in §1's envelope table moves.

Rev 6 history follows. Rev 6 is the ruling on the user's rejection of the first rendered
case's patch-wall connector openings. It rewrites §5's aperture paragraph (the lip window is a
**`union()` of a truncated-teardrop body circle and two plain boss reliefs** — never a `hull()`),
**rejects the proposed top-open U-notch aperture**, and logs deviations **D9** (the rejected window
shape) and **D10** (the plate-fixing bosses have no insert bore, so the plate cannot be fastened).
Nothing in §1's envelope table moves — rev 6 is a shape-and-bore ruling. Full ruling, the five
reasons the U-notch is rejected, the replacement asserts T1-34a–d/T1-35 and the six new constants:
**`layout-patch-wall.md` rev 6, §2.5 + §9 + §11 rev-6 addendum + §15 "Ruling 2026-09-08b"**.

Rev 5 history follows. Rev 5 is the L2 architecture gate for
`docs/plans/2026-09-08-l2-first-case.md` (first full case, Pro Convert for NDI to HDMI). It adds
`lib/mcc/layout.scad` at L1 and the `shell.scad`-as-L2-composition-root rule (§3), settles what the
patch-wall aperture actually is (§5), corrects the family `W` figures to 159.85 / 166.35 (§1), and
logs deviations **D5–D8** (§13). Every rev-5 ruling, including the eight `PLAN-ASSUMPTION` verdicts,
is collected in **`layout-patch-wall.md` §15** — read that before implementing L2.

Rev 4 history follows. Baseline 2026-09-07 (before any code); rev 2 added the patch-wall
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
| `compact` (device 100.9 × 60.2 × 23.3) | **194.9 × 159.85 × 51.0 mm** | 6 | 61.1 / 96.15 mm | 55.1 / 90.15 mm |
| `plus` (device 117.5 × 66.7 × 23.4) | **211.5 × 166.35 × 51.0 mm** | 6 | 44.5 / 89.65 mm | 38.5 / 83.65 mm |

> **Rev-5 correction (2026-09-08).** The `W` figures were 159.9 / 166.4 through rev 4. The HDMI bay
> depth in the table below is rounded to "75.7"; `constants.scad` gives the exact `40.65 + 35 = 75.65`,
> so `d_bay_free = 70.65` and `W = 159.85 / 166.35`. **The code computes the exact value; do not round
> it back to match a doc.** `layout-patch-wall.md` §8 carries the per-SKU table.
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
L1  lib/mcc/layout.scad                   case layout solver — PURE FUNCTIONS ONLY, NO MODULES
                                          (envelope L/W/H, device placement, slot assignment,
                                          end zones, plate/fixing positions, fan/splitter/
                                          side-bolt/lid-fastener positions). Added rev 5.
    lib/mcc/neutrik.scad                  D-series cutout, pocket, screw bosses, depth tables
    lib/mcc/fasteners.scad                heat-set bosses, captive thumbscrew, 1/4"-20 boss
    lib/mcc/rail.scad                     mount-rail dovetail profile: male rail, female cut,
                                          spring-lip latch. ONE source of truth shared by
                                          mounts.scad (case floor) and models/brackets/*.scad
                                          (rev 9, D-15). NOT named bracket.scad — see below
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
- **`layout.scad` (L1, added rev 5, 2026-09-08).** The one place the case-layout formulas live, so
  `shell`/`panel`/`cradle`/`mounts`/`vents` never re-derive `L`/`W`/`H`/slot/end-zone maths
  independently. Constrained so it can never grow into a second shell: **functions only, never a
  module**; it may `use` only `constants.scad`, `ports.scad` and `util.scad`, and **never** an L1
  geometry provider (`neutrik`, `fasteners`, `fan`, `poe_splitter`, `ghost`). It returns positions and
  numbers; callers fetch geometry/keep-outs from the providers themselves.
- **`shell.scad` is the composition root of L2 (sanctioned exception, rev 5).** It — and only it — may
  `use` its L2 peers `cradle.scad`, `mounts.scad`, `vents.scad`. Those three, plus `panel.scad`, must
  **never** `use` each other or `shell.scad`; that keeps the L2 graph an acyclic tree rooted at
  `shell.scad` and keeps `models/<slug>/case.scad` the ~40–80-line thin assembly §4 promises. The
  alternative — composing base = shell ∪ cradle ∪ floor − vents in every L4 file — duplicates real
  composition logic per SKU and is rejected.
- **`shell.scad` must not `use <neutrik.scad>`.** If the shell ever needs a connector-shaped void it
  goes through `mcc_panel_cutout()` (§5 dispatcher rule). Today it needs neither.
- **`rail.scad` (L1, added rev 9).** Owns the mount-rail dovetail cross-section and nothing else:
  `mcc_rail_male()` (additive), `mcc_rail_female_cut()` (subtractive), `mcc_rail_sill_size()` (pure).
  Both halves of a mating interface must come out of **one** file or they drift — the same reasoning
  that moved `mcc_panel_fixing_pos()` into `layout.scad` (D6). Consumers: `mounts.scad` (L2, the
  female groove in the case floor) and `models/brackets/*.scad` (the male rail). Three rules:
  - **The file is `rail.scad`, not `bracket.scad`.** The name must describe the *interface*, not one
    of its two consumers; `bracket.scad` invites bracket plate/hole/rib geometry — which is
    per-bracket assembly work — into an L1 provider.
  - **`layout.scad` must NOT `use <rail.scad>`.** §3 already forbids `layout.scad` from importing an
    L1 geometry provider. `mcc_floor_keepout()`'s `"mount_rail"` row is built from the `MCC_RAIL_*`
    **constants** (L0), never from `mcc_rail_sill_size()`.
  - `shell.scad` reaches the rail only through `mounts.scad`, never by `use <rail.scad>` — the floor
    rule (§6) has one owner.
- **`models/brackets/*.scad` are assemblies, not cases.** They sit at the same level as
  `models/<slug>/case.scad` and `models/coupons/*.scad`: they may import only the barrel
  `<mcc/mcc.scad>`, own their own plate/holes/ribs, and must never re-derive the rail profile.
  They carry **no device record and no `case.scad`**; `scripts/build.py` discovers them through a
  separate `discover_brackets()` (mirroring `discover_coupons()`), and `discover_models()` must skip
  the `brackets` directory explicitly, exactly as it already skips `coupons`.

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
- **The one sanctioned exception: `$fn = 32` on a BOSL2 `screw_hole(thread=true)` bore** (rev 10,
  issue #30). Scoped to the **thread bore only** — the pad/boss cylinder around it still takes
  `$fn = 64` with `circum = true`. Justification, in this order: (1) `screw_hole()` accepts **no
  `circum` argument**, so the circumscribing mechanism above is simply unavailable; (2) the residual
  inscribed error at `$fn = 32` on ⌀3.0 is `3.0·(1 − cos(180/32))/2 = 0.0072 mm per side` — **2.7 %
  of the thread's 0.2705 mm radial engagement**, and ~7 % of the `$slop` term, so the fit is carried
  by `$slop` (and by assert T1-42c), not by facet count; (3) the measured cost is real —
  `$fn = 64` is ~26× the render time and ~38× the STL size of a plain bore, `$fn = 32` roughly halves
  both (table in the plan's §3.3). **This is a bounded carve-out, not a loosening of the policy**:
  it does not extend to any other hole class, and any future use must cite this bullet. Note also
  that the far bigger STL-size lever is **ASCII → binary STL** (~6×, lossless); `scripts/build.py`
  emits ASCII today (`build.py:64,423`, no `--export-format`). That is a separate ticket, deliberately
  **not** folded into #30 because it changes every export and every golden's provenance.

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
- **What "the aperture" actually is (rev 6, 2026-09-08 — supersedes the rev-5 wording).**
  One plate, **one continuous stepped rabbet**, and **`n_slots` discrete windows** through the 3 mm
  structural lip — *not* one 162–186 mm opening, which has no legal roof, and *not* one rabbet per
  window. Solid lip material survives in the inter-slot webs, which is what carries the `n_fast = 6`
  mid-span lid-fastener boss at `x_gap`.
  **Each window is a `union()` of three separate profiles and NEVER a `hull()` of them:** a plain
  body circle `⌀(mcc_cutout_d(part) + 2·MCC_CLR_SLIDE)` truncated-teardropped above its 45° tangent
  line (`cap_h = d/2 + MCC_APERTURE_CAP_RISE`, flat bridge ≤ `MCC_APERTURE_BRIDGE_MAX`), plus two
  plain circles `⌀(boss_od + 2·MCC_CLR_SLIDE) = 8.88` at the **placed** plate's rear-boss positions —
  **`(slot_x − 9.5, z_conn_c − 12)` and `(slot_x + 9.5, z_conn_c + 12)` in case `(x, z)`** — small
  enough (< `MCC_APERTURE_SELF_SUPPORT_MAX_D`) to need no teardrop of their own.
  **Corrected rev 7 (2026-09-08):** rev 6 wrote this diagonal as `(∓9.5, ±12)`, which is the plate's
  *authored* Neutrik front-view pattern. `case.scad` places the plate with `rotate([-90,0,0])`, which
  maps local `(x, y)` → world `(x, z = −y)`, so the placed bosses sit on the **other** diagonal.
  Following the doc literally produced mirrored reliefs; the user saw it and `lib/mcc/shell.scad`
  was fixed on 2026-09-08 (**commit 2a7e0b0**). **Frame rule, recorded so it is not repeated: the
  outside viewer's right is world −X, and a plate-local `+y` becomes world `−z`.** Every patch-wall
  position in this file and in `layout-patch-wall.md` is in **case** coordinates unless it explicitly
  says otherwise. Full statement: `layout-patch-wall.md` §2.5 "The frame rule" + §15 ruling
  2026-09-08c C1.
  **The acceptance criterion is what the user sees from outside:** a flat plate face 3.0 mm behind
  the wall face, `n_slots` *exactly round* cutouts and two ⌀3.4 screw holes per slot. The union
  achieves it because the body circle and its apex are everywhere *larger* than the plate's own
  cutout, so the whole window boundary hides behind the plate; only the two relief crescents intrude,
  by ≤ `MCC_APERTURE_RELIEF_INTRUSION_MAX` (1.5 mm; 1.04–1.24 mm in practice), and the fitted
  connector body covers them. Rev 5's `hull()`ed "crown" produced a 27.9 × 32.4 mm diagonal blob that
  *is* narrower than the plate cutout on its diagonal flanks, so it showed through every hole — the
  user rejected it on sight and was right (deviation **D9**). The hull also removed ~35 % more lip
  material than the union, and it was never more self-supporting than a plain circle.
  **The top-open (U-notch) aperture is rejected** — it would cost the patch wall's top continuity
  over 86 % of its length, the tongue-and-groove closure along the whole patch side, two of the four
  plate fixings, the mid-span lid fastener's gusset, and it forces `MCC_PLATE_H` off its derivation.
  Full normative spec, the arithmetic that also rules out the naive rectangle, the five U-notch
  reasons and T1-34a–d/T1-35: `layout-patch-wall.md` §2.5 + §9 + §15 ruling 2026-09-08b.
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

**Rev 6, 2026-09-08 — two rules added here after the user's "there is no place to screw the
D-connectors down".**

1. **The bosses stay on the plate.** Moving them into the shell's structural lip (which would delete
   the window's two boss reliefs and make it a single perfect circle) was evaluated and rejected: it
   makes 8 heat-set inserts per case a blind operation inside a 45 mm-deep box, needs non-stock
   ~M3×14 screws instead of the ones Neutrik ships, and destroys the "load the plate on the bench,
   then drop it in" assembly sequence that makes a 168–186 mm plate handleable
   (`layout-patch-wall.md` §15 ruling 2026-09-08b, option C).
2. **Every heat-set boss in this repo must have a bore that a screw can actually reach through**
   (assert **T1-35**): the insert bore runs from the boss's rear tip for `insert.len +
   MCC_INSERT_BORE_EXTRA`, and an `MCC_M3_CLR_D` through-bore carries it the rest of the way into the
   panel's own screw clearance hole. **No solid material anywhere on the screw axis between the
   flange face and the insert.** Rev 6 found both bores missing — `mcc_neutrik_d_bosses()` left
   0.3 mm of solid ASA on the axis and the four plate-fixing bosses in `shell.scad` had no bore at
   all (deviation **D10**), i.e. neither the connectors nor the plate could be fastened.
   **RESOLVED 2026-09-08 (rev 7).** Both are bored, and in both cases the bore is a genuine
   **through-hole**, open at the boss's rear tip *and* at its bearing face, rather than the blind
   pocket this paragraph's wording implies: Manifold on the pinned OpenSCAD **2025.09.07** cannot
   union a *blind-bored* boss flush against a face of another solid (the boss comes back as its own
   disconnected component; diagnosed by isolated bisection, reproducible with the aperture entirely
   absent and at every overlap depth tried). **The insert therefore goes in from the interior/rear
   tip** and the screw enters from the plate side — put that on the build sheet. Reasoning,
   scope and the "do not over-drive the insert" caveat: `layout-patch-wall.md` §15 ruling
   2026-09-08c C2. T1-35's wording is unchanged and is satisfied strictly by a through-bore.
   The `neutrik-tile` coupon (§9 Tier 4) exists to catch exactly this class of defect and has not
   been printed; **print it before the first full-size case.**

3. **The connector's own two screws thread into a printed M3 pad, not a heat-set insert (rev 10,
   2026-09-09, GitHub issue #30).** This **supersedes bullet 1's "Preferred: … with an M3 heat-set
   insert" and the "Self-tapping directly into 2 mm of ASA is not an approved option" line — for the
   connector-fixing system only.** (That line remains true and remains the reason this is a *pad*,
   not a thread in the 2 mm plate field: option A, threading the plate itself, gives ~4 turns and was
   rejected.) The pad is the *same* boss as before — `MCC_THREAD_M3_PAD_D = 8.28`,
   `MCC_THREAD_M3_PAD_H = 7.0`, both **pinned equal to the pre-#30 heat-set boss** — with the insert
   bore replaced by a BOSL2 `screw_hole(thread=true)` M3×0.5 bore. Consequences, all deliberate:
   - **No shell geometry moves.** Because the OD is pinned, the wall window's boss reliefs
     (`d_rel = boss_od + 2·MCC_CLR_SLIDE = 8.88`) and every T1-34a–d figure are unchanged.
     **`layout.scad:189` must therefore derive `d_rel` from `MCC_THREAD_M3_PAD_D`, not from
     `MCC_BOSS_MIN_RATIO · MCC_INSERT_M3.od`** — otherwise one physical diameter has two independent
     sources and they drift the first time anyone edits `MCC_INSERT_M3` (which stays in use for the
     plate-fixing bosses). Same rule as the `rail.scad` ruling in §3 and D6: both halves of a mating
     interface come out of one file. `layout.scad:395`'s `insert_hole_r` (T1-34d) correctly stays on
     `MCC_INSERT_M3` — that is the shell's own plate-fixing boss.
   - **The bore stays a genuine through-hole**, open at the pad's rear tip *and* its panel-facing
     face — unchanged from the rev-7 T1-35 fix, and for the same Manifold reason. Do **not**
     blind-pocket it. Bonus property worth knowing: with a through-bore an over-long screw cannot
     bottom out and jack the connector off its seat; **under**-length is the only failure mode.
   - **Print orientation is what makes this legal.** The plate prints face-down
     (`print-check/SKILL.md:59`), so model `−Z` is printer `+Z` and the bore axis is **vertical** —
     one full circle per layer, no bridging, no thread-flank overhang. The same thread in a vertical
     shell wall (option B) would be a horizontal M3 bore, unprintable without unremovable internal
     support. **Print orientation, not Manifold, is the deciding argument.**
   - **The plate's own 4 retention bosses (`_mcc_patch_wall_fixing_bosses()` in `shell.scad`) are
     UNCHANGED — still M3 heat-set inserts.** Two different physical systems: connector-to-plate vs.
     plate-to-shell. Issue #30's own text conflated them; do not repeat that. Converting the
     plate-fixing bosses is a separable follow-up ticket, and it is the point at which
     `mcc_thread_pad()` should move from `neutrik.scad` to its natural home `fasteners.scad`.
   - **One implementation shape, one source.** The pad+thread is a public `mcc_thread_pad()` in
     `neutrik.scad`; `mcc_neutrik_d_bosses()` and the `m3-thread-ladder` coupon both call it. A
     coupon that hand-rolls its own copy of the geometry cannot calibrate a production constant, and
     an L4 model calling BOSL2 `screw_hole()` directly violates §3's "models import only the barrel".
   - **Unretired until a coupon says so.** The fixing is `assumed` until `m3-thread-ladder` **and**
     `neutrik-tile` are printed in ASA and tested — see **R28** and **M16**. The fallback is a
     one-module revert (swap the bore back to an insert bore); it is cheap *only* because the pad's
     external footprint was pinned.

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

### The `DBA-BL-B` blank carries the full D hole (rev 8, 2026-09-09 — decision D-14, part 4)

**Normative: `MCC_PANEL_PARTS["DBA-BL-B"].hole_d = 24.0`, not 0.** A blanked slot is a *reserved*
slot, not a deleted one: the plate carries the full ⌀`24.0 + MCC_HOLE_COMP` = **⌀24.2** round
cutout and its two ⌀3.4 M3 holes, the wall window carries its full truncated-teardrop body circle
(`d_win = 24.8`) plus the two ⌀8.88 boss reliefs, and the purchased `DBA-BL-B` blanking plate
(26 × 31 flange, R3.5, same M3 pattern — `knowledge/components/mini-din8-feedthrough.md:179`)
simply covers it. **Any D-series connector can then be fitted later by swapping the blank for the
connector — no reprint of the plate and no reprint of the shell.** That is exactly the user's
requirement, and it is why 24.0 (the etherCON/universal-D class, `d-series-cutout.md:36`) is the
right number and 23.6 is not: a ⌀23.8 hole takes HDMI/USB/BNC but **not** an `NE8FDP-B`.

Everything else in the row is unchanged, and that is deliberate — **a blank must cost nothing**:

| Field | Value | Consequence |
|---|---|---|
| `hole_d` | **24.0** (was 0) | `mcc_cutout_d` = 24.2, inside `neutrik.scad:48`'s 24-class band `[24.0, 24.6]` |
| `depth` / `plug_len` | 3.2 / 0 (unchanged) | `mcc_bay_depth` = 3.2 → never the `max`, so `d_bay_free` and **`W` do not move** |
| `bend` | 0 (unchanged) | T1-08 untouched; **rank `[0, 0]` stays the lowest in `MCC_PANEL_PARTS`, so a blank still sorts innermost** in its block (§14 slot rule) |
| `max_panel_t` | 4.0 (unchanged) | ≥ the 2.0 mm plate seat |
| `kind` | `"blank"` (unchanged) | stays the BOM/ghost discriminator; it is **no longer** the geometry discriminator |

End zones and `L` are keyed by the port's **`kind`**, not by its `panel` part
(`mcc_dev_side_allow()`, `layout.scad:46`), so blanking a slot moves no end zone either. **Net: the
envelope of every affected SKU is unchanged to the last decimal; only the slot-3 plate cutout and
its wall window change.**

**This is also what repairs a §9 invariant.** §9's minimum set requires "every port with
`panel != "none"` has a cutout, and vice versa". With `hole_d = 0` a reachable blank would be a
`panel != "none"` port with **no** cutout — the invariant would have been violated the moment
`DBA-BL-B` stopped being dead code (D12). At `hole_d = 24.0` it holds by construction.

**The one library fix that must land with it (deviation D18).** The "is this a blank?" test is
written three ways today: `neutrik.scad:39` uses `kind == "blank"`, while `shell.scad:181` and
`layout.scad:187` use `mcc_panel_hole_d(part) == 0`. **Unify on `mcc_panel_hole_d(part) == 0`.** If
`neutrik.scad` keeps the `kind` test, the shell opens a window and the plate behind it stays solid
— the worst of both outcomes, and invisible to every assert. Once `hole_d = 24.0` those branches
are dead on every current SKU; keep them (they are the guard for a future genuinely-solid blank)
and say so in the comment.

Accepted, recorded so it is not re-litigated: a blanked slot is now a real hole covered by a 3.2 mm
PA6.6 plate on two M3 screws, 3.0 mm behind the sacrificial bezel — the same load path as any
fitted connector. It is not an ingress or a drop regression.

---

## 6. Feature ownership rules

Three rules exist because these features will otherwise collide silently:

- **The floor rule.** `mounts.scad` is the **single owner** of every feature in the case floor: the
  **mount-rail dovetail groove and its sill** (D-15, rev 9 — replaces VESA), the
  Magewell-Fishtail M4 reservation, the strap slots, the stacking profile and the splitter
  tie-downs. It exposes `mcc_floor_keepout()` and asserts non-overlap between all of them.
  `cradle.scad` never cuts the floor; if it ever needs a penetration it requests one *through*
  `mounts.scad`. The two sanctioned exceptions stay in `cradle.scad` because they are installed from
  the underside *into the deck hollow*: the case's own 1/4"-20 insert boss (T1-32) and the
  compliant-pad pocket.
  **VESA 75 × 75 is removed entirely (D-15, user decision 2026-09-09).** `_mcc_vesa_positions()`,
  `MCC_VESA75_PITCH`, `MCC_VESA_HOLE_D`, the four `vesa_*` keep-out rows and the `"vesa"` cfg key all
  go; `mcc_floor_bore_cut()` is **retired**, not left as an empty module, and its `shell.scad` call
  site becomes `mcc_rail_features_cut(dev, cfg)`. `layout.scad`'s local `vesa_pos` is renamed
  **`floor_center`** (it still anchors `case_tripod_insert` and `fishtail_reserve`). It is removed,
  **not deprecated-and-kept-optional**: there is no code path that reinstates it. If VESA is ever
  wanted back as a *third* option alongside the rail, that is new scope and a new user decision.
  **The rail is the case's primary mount.** It is the **female** half (a groove recessed up into the
  floor slab, plus a local sill that thickens the floor to `MCC_RAIL_DEPTH + MCC_FLOOR_T`); the
  **male** half lives on the printable bracket. This is forced, not preferred: the exterior floor
  face is the bed-contact face on every SKU, so a downward-protruding feature is unprintable without
  flipping the base; and D-13 already commits this repo to "nothing protrudes from any wall/face".
  **The floor's residual material over the groove is never less than `MCC_FLOOR_T` (3.0 mm)** — that
  is the §9 uniform-shell assert applied to the one surface that carries the whole case's weight
  when it is bracket-mounted (T1-38).
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
  **D-14 (2026-09-09) does not touch this rule.** The user's fan-power decision takes the fan's 5 V
  from the *device*, so **no PoE splitter is fitted by default on any SKU** — but the splitter bay
  stays reserved exactly as before, `ez_neg` stays 47, and `MCC_END_ZONE_NEG_EXTRA_SPLITTER` is
  unchanged. Nobody may "reclaim" the 20 mm because the splitter is now less likely to be fitted;
  that is the same argument the rule already rejects, and the splitter is the named fallback if
  M9/M10 show the device's own ports cannot carry the fan (§11 R21/R22).

### Fan power is device-sourced (D-14, user decision 2026-09-09)

The fan is `NF-A4x10 **5V plain**` — 0.044 A typ / **0.05 A max**, 0.22 / 0.25 W
(`knowledge/components/fans.md:22`) — in series with a **KSD9700 45 °C normally-open bimetal
switch** bonded to the device's metal top, so the fan only runs when the device is actually hot.
There is no PWM and no speed control: once the switch closes the fan runs at full 4500 rpm.

| Family | 5 V source | Rating of that source | Headroom |
|---|---|---|---|
| **Decoders** (NDI to HDMI, NDI to SDI, NDI to HDMI 4K) | device's **USB-A host** port | **not stated by Magewell anywhere** (`fan-power-sources.md:21,39-46`); the 900 mA USB-3.0 baseline is a generic USB-IF figure, not a Magewell one | `unknown` — **R21**, M9 |
| **Encoders** (HDMI Plus, SDI Plus; TX if a fan is ever fitted) | **Mini-DIN-8 pin 8 (VCC)**, GND on pin 4 | **5 V, 100 mA max — Magewell-documented** (`fan-power-sources.md:80`; `mini-din8-feedthrough.md:38`) | 50 mA, i.e. **50 % of the budget on steady state alone**, before inrush — **R22**, M10 |
| **NDI to AIO** | **none** — the model has no USB-A host port and no Mini-DIN-8 (`fan-power-sources.md:37-38,186`) | — | stays **passive**, `fan = false` |

Three architectural consequences, all recorded so they are not rediscovered:

1. **The USB-B port is not, and never was, a 5 V source.** It is a power *input* only
   (`fan-power-sources.md:23,115-131`), and under PoE it carries no 5 V at all. `BOM.md:194`
   currently tells the builder to Y-splice the HDMI Plus fan onto "the `usb_b` power feed inside
   the case" — that is unbuildable on a PoE-powered device (deviation **D17**).
2. **Tally is excluded on the encoders.** Pin 8's 100 mA is shared with the Magewell Tally Light
   #99090 and the LED matrix, whose draw is `unknown` (`fan-power-sources.md:99-106`). The user's
   decision 1 ("PTZ/Tally is not used") is what makes the fan's 50 mA acceptable — **it is a
   precondition, not a coincidence.** If a Tally Light is ever wired, the fan must move off pin 8.
3. **The Mini-DIN-8 stays `panel:"none"`.** D-01 is untouched: the port is now *internally* cabled
   to the fan, not brought out. That is precisely what makes it invisible to the end-zone solver —
   see **R23**.

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
| `panel` | a **key of `MCC_PANEL_PARTS`** or `"none"` | which panel **slot** this port occupies, and with what part. `"none"` = the port occupies no slot and stays internal (SD slot, LEDs, PTZ/Tally). **`"DBA-BL-B"` = the port occupies a slot that is blanked off** — the slot, its plate cutout, its wall window and its two M3 bosses are all built, and a `DBA-BL-B` blanking plate covers them, so the slot stays reusable (§5, D-14). **Corrected rev 8:** rev 1–7 wrote the blank value as `"blank"`; that is the row's `kind`, not its key, and `mcc_panel_cutout()` would assert on it |
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
| **printed-thread pad: wall ≥ 2.0 mm, ≥ 3 engaged turns, residual radial engagement ≥ 50 % of nominal after `$slop`** (T1-42a/b/c, rev 10) | §5 "Connector fixing" bullet 3; `lib/BOSL2/screws.scad:753` |
| rib thickness ≤ 0.6 × adjoining wall, height ≤ 3 × thickness | `fdm-rugged-enclosure-guidelines.md:65-70` |
| no two floor features overlap (`mcc_floor_keepout()`) | §6 floor rule |
| every port with `panel != "none"` has a cutout, and vice versa | §7 |

**Plus 31 topology asserts (T1-01 … T1-31)** introduced by the patch-wall layout, the side bolt and
rev 4: slot bijection, slot pitch, bay depth and lateral bend fit, end-zone cable allowance
**including the summed splitter term**, plate-fits-wall, boss-to-flange clearance, splitter/fan/vent
non-intersection, the `panel != "MINIDIN8"` guard, the six side-bolt asserts (single `tripod_1_4_20`
port on `[0,-1,0]`; keep-out ∩ vent = ∅; bolt axis inside the device side face; head fully recessed;
clip pocket inside the wall; keep-out ∩ cradle-rib = ∅), and the three rev-4 additions (duct floor,
intake free area vs. the fan aperture, flush boss). Rev 5 added T1-32/T1-33/T1-34; **rev 6 retires
T1-34 and adds T1-34a–d (aperture shape, roundness, containment, fixing-boss clearance) and T1-35
(no solid material on any fastener's screw axis between the bearing face and its insert).**
**Rev 9 adds T1-36 … T1-41** (rail sill, rail keep-out, floor residual, deck grid, pad-pocket
island, vent/keep-out). **Rev 10 adds T1-42a/b/c — the printed connector-fixing thread: pad wall
thickness, engaged turns, and residual radial thread engagement vs. `$slop`** (issue #30). **T1-42c
is the load-bearing one**: `0.5·(major − minor) − 2·$slop ≥ MCC_THREAD_ENGAGE_MIN_RADIAL`. It exists
because a BOSL2 internal thread grows by `4·$slop` in *diameter*, so a plausible-looking `$slop` can
silently erase the entire thread and leave a plain bore that every other assert happily passes.
Full table with sources: `layout-patch-wall.md` §9. Do not
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
- `m3-thread-ladder` (**new, rev 10, issue #30**) — 5 printed M3 thread pads at production
  `pad_d`/`pad_h`/`$fn`, sweeping `$slop` across **`[0.02, 0.035, 0.05, 0.065, 0.08]`** (per-side
  0.04–0.16 mm, i.e. 15–59 % of the 0.2705 mm nominal engagement). The ladder must be built from the
  same `mcc_thread_pad()` the production module calls — a coupon that duplicates the geometry cannot
  calibrate it. **Acceptance is ≥ 5 insert/remove cycles per pad, not one successful seat**: a
  connector gets unscrewed for cable service, and repeat-cycle stripping is the exact failure mode
  heat-set inserts existed to prevent (**R28**). Print it in the same batch as `neutrik-tile`.

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
**Resolution path closed on the mechanical side, 2026-09-09 (D-14).** The Plus family ships with
the fan fitted (`fan = true`) *and now has a named 5 V source and a thermostatic control element*
(§6, "Fan power is device-sourced"). What R5 still carries is **electrical, not thermal**: the
source ratings are unverified on both families (R21, R22) and the switch's trip point is not
confirmed against this case's real internal temperature (M13). If any of those fails, the fallback
is the reserved splitter bay — which is why §6's reservation rule must not be relaxed. Note also
that the switch introduces a new failure mode the old always-on assumption did not have: a fan that
**never starts** because the switch never closes is indistinguishable, from outside, from a fan
that has failed. Record it on the build sheet as a commissioning check.

**R6 — PoE power budget. LARGELY RETIRED 2026-09-09 by D-14; kept as the fallback's risk.**
Original: 802.3af delivers 12.95 W at the PD; a 10 W Plus device + splitter conversion loss (1–2 W)
+ fan (0.25–1.3 W) is at or over budget, and the splitter's own heat lands *inside* the case.
**What D-14 changes:** with no splitter fitted, **the Magewell device is itself the PD**, the link
is **802.3at (25.5 W guaranteed at the PD** — `knowledge/components/poe-splitter-verification.md:31-33`),
and the fan's **0.25 W max** comes off the device's own internal 5 V rail. Both terms that made R6
tight — the DC-DC conversion loss and the splitter's dissipation *inside the sealed case* — are
gone from the default build, and so is the "does the splitter pass gigabit?" data risk
(`poe-splitter-verification.md:72-73`, `unknown` for every candidate). R6 therefore applies only to
the **fallback** configuration and is no longer a design blocker. It is replaced, for the default
build, by two much smaller and much more specific risks: **R21** (decoder host-port rating) and
**R22** (encoder VCC 100 mA ceiling + the thermoswitch). Do not delete R6 — it is the analysis the
fallback would have to re-inherit.

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
**Second driver added 2026-09-09 (D-14):** on the two Plus encoders `fan_y` is no longer only a
thermal question — it is also the only available escape from R23's Mini-DIN-8 plug collision. The
two drivers happen to point the same way (−Y, onto the duct), which is convenient but must not be
mistaken for a decision: the thermal question is still settled by measurement.

**R21 — the decoders' USB-A host port is an unverified 5 V source. NEW 2026-09-09 (D-14).**
Magewell's 94-page decoder manual states the port's *purpose* (keyboard/mouse) and **no electrical
rating whatsoever** (`knowledge/components/fan-power-sources.md:39-46,201-205`), and never says
whether the port stays live when the unit is PoE-powered rather than USB-B-powered — that is an
inference from the manual's power architecture, not a stated fact (`:47-54`). The 900 mA USB-3.0
SuperSpeed baseline quoted in that file is generic USB-IF knowledge, explicitly *not* a
Magewell-confirmed figure for this implementation (`:55-59`). The fan needs 50 mA max, so the
*likely* headroom is large — but "likely" is not this repo's standard. **Consequences if it is
wrong are contained:** the three decoder cases still work, passively, exactly as
`pro-convert-for-ndi-to-hdmi` and `-to-sdi` already do at `fan = false`; only
`pro-convert-for-ndi-to-hdmi-4k` (Plus chassis, `fan = true`) loses its cooling and would fall back
to the splitter. **No geometry depends on this** — measure it (M9) before the first Plus-chassis
decoder is trusted on stage, not before anything is printed.

**R22 — the KSD9700 thermoswitch is unverified in four independent ways, and one of them is an
electrical single point of failure. NEW 2026-09-09 (D-14).** Every finding below is from
`knowledge/components/poe-splitter-verification.md` §4, which is explicit that this part could not
be sourced from any mainstream distributor (**DigiKey returns zero results**, `:154-156`) and that
what is known comes from a Chinese B2B marketplace aggregator, not a datasheet:

- **No DC rating exists at all.** Every published rating is **250 V AC / 5–16 A** (`:170`) — an
  appliance-motor regime. The fan is 5 V / 0.05 A, four orders of magnitude below it. The
  dry-circuit concern (contacts rated for high AC current rely on that current to burn through
  surface oxide; a 50 mA DC signal does not) is switch-design lore, **not** a confirmed defect of
  this part (`:188-196`). It is a reason to bench-test (**M8**), not to reject — but if it fails,
  the fan silently never runs and nothing in the case reports it.
- **Package and mounting are `unknown`** (`:172`). The budget is hard: the plenum above the device
  top is `H_int − deck − dev_h` = **10.8 mm** (plus) / **10.85 mm** (compact), and `MCC_LID_CLEAR`
  is 2.0, so **the switch body plus its thermal pad must be ≤ 8.8 mm tall** (**M11**). This is a
  *sourcing constraint derived from geometry*, and it is the correct way to state it — do not
  invent a body height for `constants.scad`.
- **No hysteresis / reset differential is published** (`:171`). An auto-reset switch with an
  unknown differential, driving a fan whose airflow directly cools the sensed surface, is a
  textbook hunting loop: fan on → top cools below trip → fan off → heats → on. Cosmetically noisy
  on stage; not damaging. Accept, observe, and if it hunts the answer is a higher trip point or a
  latching/hysteretic controller, not a bigger fan.
- **45 °C is the ticket's target, not a sourced conclusion** (`:234-238`). Nothing confirms it is
  the right trip point for *this* case around *this* device (**M13**).

**One further electrical unknown, on the encoders only, that R22 must carry:** the NF-A4x10's
**inrush** current is not published anywhere — Noctua give steady-state only
(`knowledge/components/fans.md:22`). A DC motor's start transient is routinely several times its
running current, and the Mini-DIN-8 VCC pin is hard-limited to **100 mA** with 50 mA already spent.
The switch closes abruptly (a snap-disc, not a ramp), so the fan sees a step. **This is the single
sharpest risk in D-14** and it cannot be reasoned away from datasheets — it is M10's whole point.
If it trips the port's limiter, the mitigation is a series resistor or a small electrolytic across
the fan, i.e. a wiring change, not a case change.

**R23 — an internally-cabled port is invisible to the end-zone solver, and on the encoders it
points straight at the fan. NEW 2026-09-09 (D-14). BLOCKING for HDMI Plus / SDI Plus.**
`mcc_end_zone()` (`lib/mcc/layout.scad:45`) and T1-18(c) (`lib/mcc/shell.scad:373`) both filter to
`mcc_ports_external(dev)`, i.e. `panel != "none"`. That was exactly right while `panel:"none"`
meant "not cabled" (`MCC_DEV_SIDE_ALLOW["minidin8"] = 0`, `constants.scad:380`, comment "internal,
not cabled (D-01)"). **D-14 breaks that equivalence:** the Mini-DIN-8 is still not brought out, but
it now carries a plug and a cable. Geometry, worked at HDMI Plus (`L = 210.5`, `ez_pos = 40`):

| Feature | Position | Note |
|---|---|---|
| Device +X face | `x = 62.25` | `x_dev_lo = −55.25`, `dev_l = 117.5` |
| Mini-DIN-8 axis | `y = y_dev_c`, `z = z_conn_c − 6 = 19.5` | `pro-convert-hdmi-plus.scad:34`, `pos [0, −6]` |
| Fan frame inner face | `x = 92.25` | `L/2 − MCC_WALL − frame_z` = `105.25 − 3 − 10` |
| Fan reserved envelope inner face | `x = 87.25` | `+ 5 mm` intake clearance (`fan.scad:42`) |
| **Free axial space for the plug** | **30.0 mm to the frame, 25.0 mm to the reservation** | |
| Fan aperture ⌀38 centred at `(y_dev_c, 25.5)` | — | the plug axis is at Δy = 0, Δz = −6: **dead inside it** |

The Magewell breakout cable's plug length is **`unknown`** — `mini-din8-feedthrough.md:66-68` gives
only a ~13.2 mm shell OD as an explicitly unsourced "sizing baseline", and its own open-questions
list (`:275-277`) records the cable OD as unverified too. So the fit is **undetermined, not
failing**: ≤ 25 mm is clean, 25–30 mm eats the fan's intake clearance, > 30 mm fouls the frame.
Moulded mini-DIN plugs with strain relief are commonly in the upper part of that range, which is
why this is called out rather than waved through.

**`fan_y` is the escape, and it is marginal.** To pull the ⌀38 aperture off the plug entirely needs
`|fan_y − y_dev_c| ≥ 20 + shell_r + clearance ≈ 27`. Toward −Y (R20's preferred direction, onto the
duct) the travel available before the aperture crowds the far wall is
`y_dev_c − (−W/2 + MCC_WALL + 19 + 3)` = **27.35 mm** on the plus family — it clears by well under a
millimetre, on a number (`shell_r`) that is itself unsourced. Toward +Y there is plenty of travel
but it puts the fan into the +X end zone exactly where the slot-3/slot-4 patch cables turn toward
the patch wall, which §5's "exhaust away from the patch wall" rule exists to prevent.

**Ruling: do not guess.** Take **M12** (measure the plug), then either (a) confirm ≤ 25 mm and
change nothing, (b) set `fan_y` in those two `case.scad` files, (c) put a right-angle or slim-boot
Mini-DIN-8 plug in the encoder BOM — note this is the *opposite* call to D-08's right-angle veto,
and defensibly so: that was a user-facing HDMI cable, this is an internal lead that is plugged in
once at build time — or (d) fall back to the reserved splitter on those two SKUs. **A developer
must not add a `minidin8` row to `MCC_PLUG_AXIAL` with an invented number**: too small and the
assert lies, too large and it fails two SKUs' builds for a figure nobody measured.

---

**R24 — the mount rail is a single line of restraint offset from the case's centre of mass. NEW
2026-09-09 (rev 9, D-15).** The device sits at `y_dev_c ≈ −30.8` (compact) / `−30.6` (plus), i.e.
well onto the far-wall side of the case; the rail is one straight dovetail. Wherever the rail is
placed in Y, the assembly's mass is off the mount line and the joint sees a roll moment reacted only
by the dovetail undercut plus flat contact between the case floor and the bracket plate.
Consequences, and why `MCC_RAIL_Y = −20.0` (not the plan's `+20.0`) is the ruling:
- **#26 requires the patch wall to hang downward.** With the rail at `−20` the case's mass then hangs
  *below* the mount line (pure tension on the dovetail); at `+20` it hangs *above* it, and the far
  edge peels off the plate. The moment is small (~0.5 N·m at <1 kg) but the sign is free to get right.
- At `−20` the rail sill lands **under the cradle deck and the device**, so it is backed by deck
  material instead of standing free in the connector bay. At `+20` it is an unsupported 150 mm rib in
  the middle of the cable bay, which is also where the patch cables run.
- The keep-out arithmetic is **identical** by symmetry about `y = 0`: 2.7 mm to the ⌀20
  `case_tripod_insert` disc and to the 60 × 20 `fishtail_reserve` band, 20 mm centre-to-centre
  (≥ `MCC_FLOOR_FEATURE_MIN_SEP` 15). At `−20` it additionally clears the splitter bay by 9.6 mm
  (compact) / 12.9 mm (plus) and the side-bolt web by ≥ 35 mm.
- **Residual risk, accepted:** the rail's Y position is still an `assumed` engineering choice, not a
  computed one, and no load case has been calculated. The `rail-latch` coupon (M15) is what turns it
  from assumed into measured. **Do not print a full-size bracket before that coupon is pulled.**

**R25 — the truss bracket's mounting-flange bolt pattern is unknown, and a placeholder is worse than
a gap. NEW 2026-09-09 (rev 9).** `docs/plans/2026-09-09-mount-rail-and-brackets.md` §4.1 proposes
`MCC_TRUSS_MOUNT_PATTERN = [40, 40]` as an explicit placeholder. That is **not** the `MCC_SPLITTERS`
precedent: an unmeasured *reservation envelope* being wrong makes the case slightly too big, whereas
an unmeasured *bolt pattern* produces a printable, plausible-looking plate that simply does not bolt
to the coupler — 8 mm of ASA and several hours of print time, with no assert and no coupon that can
catch it. It also collides with the repo's first non-negotiable ("never invent a dimension"). Add to
that: the proposed ~150 × 120 plate is **smaller in both axes than every case footprint**
(194.9 × 159.85 / 211.5 × 166.35), and a 150 mm rail on a 150 mm plate leaves zero room for the end
stop. **Ruling: #27 is deferred, not rejected on its merits — it is blocked on M14.**

**R26 — the printed safety-cable eye on an overhead mount. NEW 2026-09-09 (rev 9).** The truss
bracket's eye is a routing/pass-through feature with **no load rating**, on a bracket that hangs a
case over people. The plan's own framing (the certified rigging safety cable is the rated secondary
restraint, and the dovetail+latch is not claimed as the primary fall restraint) is the correct
framing — but it is a **user safety decision, not an architect's**. Nothing in `models/brackets/`
that is intended for overhead use may be printed for real use until the user has signed that framing
off in writing, and the file's header comment must state that the print is not rigging-certified.

**R27 — the lid vent field is an upward-facing dust and liquid path over the device's own hot top,
and over the D-14 thermoswitch. NEW 2026-09-09 (rev 9, #24).** Straight vertical through-slots (no
louvre) are ratified for v1 on the stated use case (touring/stage, `CLAUDE.md`; no ingress
requirement exists in the fixed decisions), and `thermal-guidelines.md` §6's filter rule does not
apply to an exhaust. Two consequences to carry: (a) if the user's actual use ever includes outdoor
or rain exposure, this must be revisited *before* printing — a louvre needs a sloped feature the
flat-lid print convention does not support today; (b) the field is centred on exactly the spot where
D-14 bonds the **KSD9700** to the device's metal top, so debris entering the slots lands on that
switch and its joints. Neither is a blocker; both are recorded so they are not rediscovered.

**R28 — M3 is below the conservative floor for printed FDM internal threads, and the connector
fixing now depends on one. NEW 2026-09-09 (rev 10, #30).** Sourced FDM-thread guidance treats **M6
and larger** as the safe default on a 0.4 mm nozzle and calls M3–M5 viable only "on well-tuned
machines" with "precise clearance calibration and test prints". This repo has now committed the
**connector-to-plate fixing** — the joint that holds a Neutrik connector in the patch wall on a
touring case — to exactly that class of thread. The sizing targets the upper end of what the source
considers viable (13 engaged turns, 2.44 mm wall), and the geometry is favourable (vertical bore
axis, printed off the bed), but **the premise is not retired by any of that.**
- **The gate is physical, and it is `m3-thread-ladder` + `neutrik-tile` in ASA (M16).** No full-size
  case is printed on the strength of a render.
- **The acceptance criterion is repeat cycles, not a single seat.** The failure mode that matters is
  a thread that survives installation and strips on the third service disassembly — which is
  precisely what the heat-set insert was there to prevent. **≥ 5 insert/remove cycles per pad.**
- **The fallback is cheap and pre-planned:** revert `mcc_thread_pad()`'s bore to the heat-set insert
  bore. Nothing else moves — no envelope, no wall window, no `d_rel`, no golden bbox — because the
  pad's OD (8.28) and height (7.0) were pinned to their pre-#30 values for exactly this reason.
  That pinning is the mitigation; do not let a later "optimisation" of the pad take it away.
- **Second-order:** the two systems are now different. If the ladder passes and the connector fixing
  goes threaded while the plate's own 4 retention bosses stay inserts, the build sheet must say so —
  a builder who heat-sets all 12 bosses destroys the connector pads irreversibly.

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
    measurement, not argument. **Rev 8:** on the two Plus encoders it may be forced by R23 before
    the thermal question is settled — if so, record which driver actually moved it.
17. ~~**Where does the fan's 5 V come from on a PoE-only stage rig?**~~ **RESOLVED 2026-09-09,
    D-14:** decoders from the USB-A host port, encoders from Mini-DIN-8 pin 8 VCC, AIO stays
    passive, no splitter by default. Both source ratings remain unverified — that residue is
    R21/R22, M9/M10, not this question.
18. **Is the `external_ports` variant key implemented or dropped (D12)?** Still open, and D-14
    leans on the answer: blanking the decoders' host slot is done by editing the **device file**
    (`panel: "DBA-BL-B"`), which encodes a *variant* decision in *device* data. That is acceptable
    today — there is exactly one variant per SKU, `case.scad`'s own doc comment already names the
    device file as the mechanism, and the alternative key is inert — but it is a knowing
    compromise, not the end state. When D12 is settled, the blanking moves to the variant config
    and the device files revert to describing the device.

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
| **M8** | **KSD9700 bench test: does it reliably make/break a 5 V / 0.05 A DC load, cold and after 50 cycles?** Also record its actual trip and reset temperatures | R22. Every published rating is 250 V AC / 5–16 A; **no DC rating exists** (`poe-splitter-verification.md:170,176-196`). If it fails dry-circuit, the fan silently never runs. At $0.07–0.20/unit a bench test is far cheaper than the design commitment (`:229-233`) | User, with a bench PSU and the fan |
| **M9** | **Decoder USB-A host port, device on PoE only (no USB-B adapter): (a) is it live at all? (b) does it hold 5 V under the fan's 50 mA? (c) does any current limiter trip?** | R21 — Magewell publish **no** rating and never state the port's behaviour under PoE (`fan-power-sources.md:39-59,185,201-205`). Gates the fan on `pro-convert-for-ndi-to-hdmi-4k`; the other two decoders are passive anyway | User, USB power meter |
| **M10** | **Encoder Mini-DIN-8 pin 8 (VCC) / pin 4 (GND) under PoE: rail voltage with the fan running, and the fan's INRUSH at switch-on** | **R22, the sharpest risk in D-14.** The pin is hard-limited to 100 mA and the fan's 50 mA is half of it; the NF-A4x10's inrush is not published by Noctua at all (`fans.md:22`), and the snap-disc closes as a step. Also measure with the Tally Light connected to get its `unknown` draw (`fan-power-sources.md:99-106,187`) | User, multimeter + scope or current probe |
| **M11** | **KSD9700 body height including its thermal pad/adhesive** | R22 — package dims are `unknown` (`poe-splitter-verification.md:172`). **Hard ceiling 8.8 mm** (`plenum 10.8 − MCC_LID_CLEAR 2.0`); over that it fouls the lid. A *sourcing* constraint: buy to it, do not model it | Whoever orders the switch |
| **M12** | **Magewell Mini-DIN-8 breakout cable: plug body + strain-relief axial length, and cable OD** | **R23 — BLOCKING for `pro-convert-hdmi-plus` and `pro-convert-sdi-plus`.** Free space is 30.0 mm to the fan frame, 25.0 mm to the reservation; the figure is `unknown` (`mini-din8-feedthrough.md:66-68,275-277`). Decides between "change nothing", `fan_y`, a right-angle plug, or the splitter fallback | User, with the OEM breakout cable in hand |
| **M13** | **Temperature of the device's metal top under sustained load in the closed case, ambient ~25 °C and ~35 °C** | R22 — nothing confirms 45 °C is the right trip point for this case/device pair (`poe-splitter-verification.md:234-238`). If the top never reaches 45 °C the fan never runs; if it sits at 45 °C the fan hunts | User, after the first full-size print |

| **M14** | **Buy one 50 mm half coupler (Doughty T57010 / Global Truss equivalent, M12) and measure its mounting-flange bolt pattern, flange plate L × W, and overall depth** | **R25 — BLOCKING for issue #27.** No fetched source publishes the flange pattern; `MCC_TRUSS_MOUNT_PATTERN` cannot be authored honestly without it, and a placeholder produces a plate that does not bolt on. Also fixes the truss plate's own outline, which must be ≥ the case footprint | User, after buying one |
| **M15** | **Print `models/coupons/rail-latch` and pull-test it:** slide force, axial retention at disengage (target **≥ 30 N**, `assumed`), thumb-release force, and the achieved dovetail fit at `MCC_CLR_SLIDE = 0.3` | R24 — every `MCC_RAIL_*` figure is `assumed`. Calibrates `MCC_RAIL_CLR`, `MCC_RAIL_LATCH_ENGAGE` and the retention target the same way `tg-ladder` calibrates `MCC_CLR_TG`. **"Coupons before cases" applies to brackets too — no full-size bracket prints before this** | User, with a luggage scale |

> **Numbering note (rev 8).** The fan-power ticket proposed these as "M7/M8/M9"; **M7 was already
> taken** (Fishtail pitch). They are M8–M13 here. If a downstream doc says "M7 KSD9700", it means M8.
> **Rev 9** adds M14 (truss coupler flange) and M15 (rail-latch coupon).

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
| D5 | 2026-09-08 | §7 / `layout-patch-wall.md` §3 slot rule: block A = `face.x < 0` takes the leftmost slots | `layout-patch-wall.md` §3's own "Worked results" table contradicted the rule on **6 of 8 rows** (both TX rows, all four decoder rows; HDMI Plus had slots 3/4 swapped). Root cause: the table was built from Magewell's "Face A", which is the *video* end on the decoders, not the case frame's −X block | The BOM's per-slot connector labelling, the panel plate render and any hand-check of `mcc_slot_for_port()` would all have been wrong; on the decoders it put the etherCON at the +X end, i.e. the opposite end of the case from the PoE splitter that must be fed from it | **Resolved 2026-09-08 (doc fix).** Table replaced in `layout-patch-wall.md` §3 + a naming warning added to step 3. **No device file changes** — the data is correct. Ruling detail: §15 ruling 8 |
| D6 | 2026-09-08 | `layout-patch-wall.md` §2.3 plate retention vs. the implemented plate | `lib/mcc/panel.scad:102-104` cuts the plate's 4 M3 holes at `(±(w/2 − rim_w/2), ±(h/2 − rim_w/2))` = `(±(plate_l/2 − 3), ±16.5)`; the contract said `z = z_conn_c ± 14` and implied `x = ±(plate_l/2 − 4)` | `shell.scad` placing its heat-set bosses from the doc would put them 1.0 mm out in X and 2.5 mm out in Z — the screws would not line up with the printed plate | **Resolved 2026-09-08 (doc fix + a required code change).** The plate wins; the expression moves into `mcc_panel_fixing_pos()` in the new `layout.scad`, `use`d by both `panel.scad` and `shell.scad` so they cannot drift. See `layout-patch-wall.md` §2.3 |
| D7 | 2026-09-08 | §6 reservation rule / `layout-patch-wall.md` §5 on-edge splitter (`H→X, L→Y, W→Z`) | `lib/mcc/poe_splitter.scad:38-45,62-72` — both `mcc_splitter_envelope()` and `mcc_splitter_tiedown()` are authored **flat** (`L→X, W→Y, H→Z`), and the envelope additionally inflates `size[0]` by `2 × cable_allow`, so a naive call reserves a 115 × 40 × 20 box on the wrong axes instead of §5's 20 × 75 × 40 | `shell.scad` would reserve the wrong volume and `mounts.scad` would cut the tie-downs on the wrong axis — a silent, invisible failure that only shows up when the splitter is fitted | **Open — approved fix, developer task.** Add `orient = "edge"` to both modules and a `cable_allow` toggle to the envelope; `mounts.scad` calls the module rather than hand-rolling holes. Re-verify at the end of the L2 milestone |
| D8 | 2026-09-08 | §5 "the aperture roof is a ≤45° self-supporting chamfer … no unsupported horizontal span over 10 mm" | `layout-patch-wall.md` rev 1–4 specified "a full-length rectangular aperture with a rabbet" with no window/opening distinction, which is unbuildable at 162–186 mm | Would have produced either an unprintable roof or an ad-hoc improvisation in `shell.scad` — and would have removed the wall material the `n_fast = 6` patch-wall mid fastener needs | **Resolved 2026-09-08 (doc fix).** `layout-patch-wall.md` §2.5 is now normative: one plate, one stepped rabbet, `n_slots` discrete minimal windows, T1-34 |
| **D9** | 2026-09-08 | §5 rev 6: the lip window is a `union()` of a truncated-teardrop body circle and two plain boss reliefs, and the assembled patch wall must read as *exactly round* from outside | `lib/mcc/shell.scad` `_mcc_patch_wall_window()` `hull()`s the ⌀24.4 body circle with the two ⌀8.88 reliefs at `(∓9.5, ±12)`, producing a 27.9 × 32.4 mm diagonal blob through the 3 mm structural lip. Because the hull is *narrower than the plate's own D cutout on its two diagonal flanks*, its outline shows through every plate hole | **Rejected by the user on sight** (2026-09-08, first rendered case, `models/pro-convert-for-ndi-to-hdmi`). Also removes ~35 % more of the structural lip than needed, exactly on the flanks where the plate's 2 mm flange seat needs backing (R4). The "self-supporting crown" justification in the code comment is false — the hull's top is still a horizontal-tangent arc | **Open — approved fix, developer task, rev-6 spec.** Replace `hull()` with `union()`; body circle gets a truncated teardrop (`cap_h = d/2 + MCC_APERTURE_CAP_RISE`); reliefs stay plain circles. Retire T1-34, add T1-34a–d. **The proposed top-open U-notch replacement is REJECTED** (five reasons, `layout-patch-wall.md` §15 ruling 2026-09-08b) |
| **D10** | 2026-09-08 | §5 rev 6 / T1-35: no solid material anywhere on a fastener's screw axis between the bearing face and its heat-set insert | (a) `lib/mcc/neutrik.scad:117-120` — `bore_depth = insert_len + 1 = 6.7` into a `boss_h = 7` boss, bored from the rear tip, leaving **0.3 mm of solid ASA** across the screw axis behind the plate's ⌀3.4 clearance hole. (b) `lib/mcc/shell.scad` `_mcc_patch_wall_fixing_bosses()` — the four plate-retention bosses were **plain unbored solids**, self-documented in that module as a deferred Manifold-robustness workaround | Neither the four Neutrik connectors nor the panel plate itself could be screwed down on the part as modelled — this is the literal, mm-level content of the user's "there is no place to screw the D-connectors down". A print-blocking defect, not cosmetic | **RESOLVED 2026-09-08 (rev 7) — accepted resolution: a genuine THROUGH-bore in both cases.** (a) `mcc_neutrik_d_bosses()` (`neutrik.scad:126-151`): `MCC_INSERT_M3.len + MCC_INSERT_BORE_EXTRA` = 6.2 mm at `hole_d` from the rear tip, then `MCC_M3_CLR_D` for the remaining 0.8 mm out through the panel-side face. (b) `_mcc_patch_wall_fixing_bosses()` (`shell.scad:289-321`): the same two-diameter bore, likewise open at **both** ends. **Reason it is a through-bore and not the blind pocket T1-35's wording implies:** Manifold on the pinned OpenSCAD 2025.09.07 cannot union a *blind-bored* boss flush against a face of another solid — the boss returns as its own disconnected component (`n_parts` = 1 + one per bored boss). Diagnosed by isolated bisection: it reproduces with the aperture entirely absent, at every overlap depth from `MCC_EPS` to 2 mm, and the add-then-cut-in-the-outer-`difference()` pattern used for the tripod/VESA floor bosses does not fix it. A plain unbored cylinder unions cleanly; any blind cavity breaks it. Nothing at these bosses' rear tips carries another feature, so opening them costs nothing. **Consequence, must reach the build sheet: the M3 insert is installed from the boss's INTERIOR (rear) tip**, before the lid goes on, and must not be over-driven past the 6.2 mm bore or it protrudes from the front face and stands the plate off its seat; the screw enters from the plate side through a short 0.8 mm clearance lead-in and must be started square. Full ruling: `layout-patch-wall.md` §15 ruling 2026-09-08c C2. Verified `parts=1` + watertight by `build.py check --all`; **still to be confirmed physically by the `neutrik-tile` coupon before the first full-size print** |
| **D12** | 2026-09-08 | §4 / `new-case-variant`: the variant config's `external_ports` list is what decides which of a device's ports this case brings outside ("a real Neutrik `panel` value omitted from `external_ports` gets a DBA-BL-B blank") | `lib/mcc/layout.scad:73-115,306-320` — `mcc_slot_assignment()` and `mcc_case_layout()` derive `n_slots` and every slot's part **solely** from `mcc_ports_external(dev)`. A grep of `lib/**` finds `external_ports` only inside doc comments (`layout.scad:303`, `shell.scad:341`). The key is **inert** | The one documented per-variant switch does nothing. A developer who omits a port id to blank it gets the live connector anyway — silently. It also makes `DBA-BL-B` unreachable, so the blank branch in `mcc_aperture_window()`/`mcc_panel_plate()` is untested dead code | **Open — escalated, teamlead/user call.** Either (i) implement it (`mcc_slot_assignment(dev, cfg)` filters by `external_ports` and pads unfilled slots with `DBA-BL-B`) — a library change, and it would change `n_slots` semantics; or (ii) drop the key and rewrite §4/the skill to say the **device file** is the only source. **Not** work for the seven parallel branches either way. `layout-patch-wall.md` §16.4 |
| **D13** | 2026-09-08 | Skills must describe the library that exists (§10) | `.claude/skills/new-case-variant/SKILL.md:12-31,55-73` states that `shell.scad`, `cradle.scad`, `mounts.scad`, `vents.scad`, `panel.scad`, `neutrik.scad`, `fasteners.scad`, `fan.scad`, `poe_splitter.scad`, `ghost.scad` and `ports.scad` "do not exist yet", and its template calls `mcc_shell(family=…, device=…, variant=…, half="base")` and `mcc_panel(device=…, variant=…, face=[1,0,0])` — **signatures that exist nowhere.** The real API is `mcc_shell_base(dev, cfg)` / `mcc_shell_lid(dev, cfg)` / `mcc_panel_plate(size, slots)` / `mcc_panel_plate_dims(dev)` / `mcc_slot_assignment(dev)` / `mcc_case_layout(dev, cfg)`, and `case.scad` also carries the `assembly`/`panel_placed`/`ghost_*` preview branches | This skill is the *first* thing seven Sonnet-tier developers will read. A stale template with non-existent signatures is a guaranteed seven-way rework, and the stop-and-report gate it opens with will fire on modules that are in fact present | **Open — BLOCKING in practice for the seven-SKU fan-out; fix on the pre-flight branch.** Rewrite the skill against `models/pro-convert-for-ndi-to-hdmi/case.scad`, which is the normative template until then. Also fix its `external_ports`/`DBA-BL-B` claim per D12 |
| **D14** | 2026-09-08 | §5 rev 7 frame rule: patch-wall positions are in case coordinates; the placed plate's rear bosses are at `(−9.5, −12)` / `(+9.5, +12)` | `lib/mcc/layout.scad:388-391` builds T1-34d's relief pair from `(slot_x − 9.5, z + 12)` / `(slot_x + 9.5, z − 12)` — the **mirrored** (rev-6 doc) diagonal — while `lib/mcc/shell.scad:210-211` correctly draws `(−sx, −sz)` / `(+sx, +sz)` | Numerically invariant today, because `mcc_panel_fixing_pos()` is symmetric about `z = z_conn_c`, so T1-34d's clearance multiset is identical either way (3.18 mm). Latent: the moment a fixing position becomes asymmetric, T1-34d silently checks the wrong pattern | **Open — low priority, library change.** Publish the relief pair once as a pure function in `layout.scad` and call it from both files. Do **not** fix inside a variant branch |
| **D15** | 2026-09-08 | §9 Tier 1: contract asserts live *in the model* and fire on every render | T1-30 (intake vent free area ≥ the fan aperture's area) exists only as `tests/test_shell.scad:53`, hard-wired to `MCC_DEV_PRO_CONVERT_FOR_NDI_TO_HDMI`. `mcc_vent_intake_area()` (`vents.scad:174`) is never called from `mcc_shell_base()` | Seven of the eight SKUs will render, pass, and be printed with **no** intake-area check at all — and the margin is genuinely thin: hand-evaluated, `pro-convert-sdi-tx` and `pro-convert-for-ndi-to-sdi` land at ≈1153 mm² against the 1134 mm² threshold (1.6 %), because their `W = 158.80` loses one whole slot off the −X end wall's run | **Open — recommended on the pre-flight branch, not blocking.** Call `mcc_vent_intake_area()` from `mcc_shell_base()` and assert T1-30 there, **after** a render confirms all eight devices pass. If a BNC compact SKU actually fails, that is a real thermal finding — escalate, do not relax `MCC_VENT_AREA_RATIO` |
| **D16** | 2026-09-08 | §6 floor rule: `mounts.scad` "exposes `mcc_floor_keepout()` and **asserts non-overlap** between all of them"; `layout.scad:240-243` repeats the promise | `lib/mcc/mounts.scad` asserts only VESA-boss-vs-splitter-bay (`:89-92`). There is no pairwise non-overlap check over `mcc_floor_keepout()`'s list, and `MCC_FLOOR_FEATURE_MIN_SEP` (`constants.scad:448`) is referenced by nothing | The floor is the one place §6 predicts silent collisions, and the guard that was supposed to catch them is absent. The `−X` strap slot is already positioned by a *displacement* rule whose only validation would have been this assert | **Open — library change, later single branch.** Add the pairwise `max(MCC_FLOOR_FEATURE_MIN_SEP, r1+r2+2.0)` assert over `mcc_floor_keepout(dev,cfg)` in `mounts.scad`. Not work for the seven |
| **D17** | 2026-09-09 | A BOM row must describe a wiring path that physically exists | `BOM.md:194` (pro-convert-hdmi-plus) instructs the builder to power the fan from a "USB-A to 2/3-pin fan power lead … **Y-spliced onto the `usb_b` power feed inside the case**", "5 V/GND tapped from the incoming `NAUSB-W-B` power line upstream of the device". `BOM.md:256` (ndi-to-hdmi-4k) has the same defect in milder form, offering "or splice onto the device's own USB-B +5V feed" as an alternative. `pro-convert-sdi-plus` has a fan row (`:216`) and **no** power row at all | **The device's USB-B port is a power *input* only** (`knowledge/components/fan-power-sources.md:23,115-131`; `poe-splitter-verification.md:56-66`, quoting both manuals). On a PoE-powered device there is **no 5 V present on that line to tap** — the case ships with the fan fitted (`fan = true`) and a wiring instruction that cannot work on the user's actual stage setup. It would only ever have worked on a bench with the USB-B adapter plugged in | **Open — developer task, part of the D-14 change list.** Replace with the Mini-DIN-8 pin 8 / pin 4 row on the two Plus encoders and the USB-A host row on the Plus decoder, both via the KSD9700. Add the missing row to `pro-convert-sdi-plus`. Found while gating D-14; it is not *caused* by D-14 |
| **D18** | 2026-09-09 | One geometric predicate, one definition (§3 "no magic numbers", §5 rev-8 blank ruling) | "Is this part a blank?" is written two different ways: `lib/mcc/neutrik.scad:39` `is_blank = (kind == "blank")`, versus `lib/mcc/shell.scad:181` and `lib/mcc/layout.scad:187` `is_blank = mcc_panel_hole_d(part) == 0` | Harmless while `DBA-BL-B` is both `kind=="blank"` **and** `hole_d==0` and is unreachable dead code (D12). **The moment `hole_d` becomes 24.0 (D-14) the two disagree**: the shell would cut the full window and the plate behind it would stay solid — a slot that looks open from outside and is blind 3 mm in. No assert catches it; it is only visible in the head-on patch-wall elevation (D11) | **Open — must land in the same commit as the `hole_d` change.** Unify on `mcc_panel_hole_d(part) == 0` in `neutrik.scad`. Note `is_24_class` at `:40` already reads `hole_d`, so the file is half-converted already |
| **D19** | 2026-09-09 | §6 floor rule / §7.1: "`mounts.scad` exposes `mcc_floor_keepout()` and asserts non-overlap between all of them", separation `max(MCC_FLOOR_FEATURE_MIN_SEP, r1+r2+2.0)` | `lib/mcc/layout.scad:271` registers `case_tripod_insert` (⌀20 circle at `(0,0)`) and `:276` registers `fishtail_reserve` (60 × 20 rect at the **same** `(0,0)`). They are **deliberately concentric** — the Fishtail band is anchored on the same `floor_center` as the case insert and is reserve-only, no geometry is ever cut for it (§7.1 correction 4) | The D16 fix that issue #25 is required to land (§9 "no two floor features overlap") will **fail on the first render of all 8 SKUs** unless that pair is exempted. A developer who hits it will most likely "fix" it by relaxing the assert or moving the Fishtail band — silently destroying the reservation | **Open — must be handled inside the D16 fix (issue #25).** The assert takes an explicit exemption set, initially `{("case_tripod_insert","fishtail_reserve")}`, with the reason in the code: *a reserve-only band may coincide with the feature it is anchored on; two features that both cut geometry may not*. Do **not** widen it to a blanket "skip rect-vs-circle" |
| **D20** | 2026-09-09 | §3 include discipline: a library file imports its own direct dependencies | `lib/mcc/vents.scad:14-19` `use`s `util`, `layout`, `fan`, `fasteners` — but **not** `ports.scad`. `docs/plans/2026-09-09-lid-vents.md` §3.2 calls `mcc_dev_slug(dev)` in every new lid-vent assert message, and `mcc_dev_slug()` lives in `ports.scad` | OpenSCAD's `use <>` is **not transitive** — `use <layout.scad>` does not re-export what `layout.scad` itself `use`s. Every new assert message becomes an undefined-function error, and because it is inside `str()` inside an `assert`, it only fires on the path that was supposed to report a real failure. `mounts.scad:20` already carries the exact fix, with the exact comment | **Open — one-line fix, must land with issue #24.** Add `use <ports.scad>   // mcc_dev_slug() (assert messages)` to `vents.scad`, matching `mounts.scad:20` |
| **D21** | 2026-09-09 | §6: a floor keep-out is a plan-view registry for the `mounts.scad` non-overlap assert; `cradle.scad` never cuts the floor and never consumes floor-feature *labels* | `docs/plans/2026-09-09-cradle-deck.md` §5.2 `_mcc_deck_rib_blocked()` tests a candidate rib's **whole-length AABB** against `mcc_floor_keepout()`, with a hard-coded string allowlist (`"case_tripod_insert"`, `"fishtail_reserve"`) inside `cradle.scad` | Two defects. (a) Because each rib spans the deck's full interior on its axis, **any** keep-out band crossing the deck deletes every perpendicular rib line — with the ruled `MCC_RAIL_Y = −20` the rail band sits under the deck and would silently remove the entire Y-rib set. (b) It puts label strings owned by `layout.scad`/`mounts.scad` into `cradle.scad` with no assert tying them together; a renamed label silently turns the filter off. The plan itself records the logic is unverified against any real collision (its PLAN-ASSUMPTION 3) | **Open — decided at the rev-9 gate. Preferred: delete the filter for v1.** The deck lattice is purely additive and lives entirely above `z = MCC_FLOOR_T`; nothing in the floor needs vertical daylight through it, and if something ever does, §6 already routes that request through `mounts.scad`. If the teamlead wants forward-compat instead, it must be (i) evaluated **per rib segment**, not per rib, and (ii) driven by an allowlist published as a constant next to `mcc_floor_keepout()` in `layout.scad`, never by literals in `cradle.scad` |
| **D22** | 2026-09-09 | §9 Tier 1: "rib thickness ≤ 0.6 × adjoining wall, height ≤ 3 × thickness" (`fdm-rugged-enclosure-guidelines.md:65-70`) | Already violated by the shipped cradle: `MCC_CRADLE_RIB_T = 3.0` against a 3.0 mm floor gives 1.0 ×, not ≤ 0.6 ×; `MCC_CRADLE_RIB_H = 9.0` gives exactly 3.0 : 1. `docs/plans/2026-09-09-cradle-deck.md` §5.1 then proposes a *second*, derived thickness `deck_h/3 ≈ 3.62` for the new deck ribs to keep the height ratio | The §9 rule is stated unscoped, so every future rib decision re-litigates it, and the plan's answer makes rib thickness a function of `dev_h` — two devices in the same family would print different deck geometry, and one part would carry two extrusion widths | **Resolved at the rev-9 gate by SCOPING the rule, not by relaxing it.** The ≤0.6 ×-wall / ≤3 ×-thickness rule governs **stiffening ribs standing off a plate or wall face** (a cantilevered fin — e.g. the bracket plates' cross ribs, which must satisfy it). It does **not** govern **floor-standing structural webs** that land on the floor slab along their whole length and are cross-braced at every intersection — the deck ladder and the far-flank ribs. Ruling: the deck ladder reuses **`MCC_CRADLE_RIB_T = 3.0`**; `MCC_RIB_HEIGHT_RATIO_MAX` is introduced only for the bracket-plate ribs; `_mcc_cradle_deck_rib_t()` is **not** created |
| **D11** | 2026-09-08 | §9 Tier 4 / the review gate: a geometry whose acceptance criterion is "what the user sees from outside" must be reviewed in that view | `exports/pro-convert-for-ndi-to-hdmi/` carries six ad-hoc previews and **no straight-on outside elevation of the assembled patch wall**; `scripts/build.py` renders no previews at all. The only patch-wall view showing the plate (`preview-rear.png`) is an oblique ISO | This is *why* D9 reached the user instead of being caught in review — the defect is only unambiguous in the head-on `−Y → +Y` view | **Open — process fix, teamlead's call.** Add a straight-on orthographic patch-wall elevation of base + `panel_placed` to the per-variant preview set and make it part of the `print-check` gate. Low cost, prevents a repeat |

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
centreline `z = 25.5`. One stepped rabbet (6 mm over the plate's rim ring, 5 mm over the field) plus
`n_slots` windows through the 3 mm lip; **each window is a `union()` of a truncated-teardrop body
circle and two plain ⌀8.88 boss reliefs — never a `hull()` (rev 6, D9)**, so from outside the user
sees a flat plate face with exactly-round cutouts. The top-open U-notch aperture is rejected.

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

**Architect verdict, 2026-09-09 (rev 8): the fan-power decision (D-14) is APPROVED. The
`DBA-BL-B` blank gets a real ⌀24.0 hole. The decoders need no geometry change; the two Plus
encoders are BLOCKED on measurement M12.**

- **Adopted, part A.** `MCC_PANEL_PARTS["DBA-BL-B"].hole_d = 0 → 24.0`, everything else in the row
  unchanged. A blanked slot then costs **no** bay depth, **no** end zone, **no** `L`/`W`/`H`, and
  keeps rank `[0, 0]` so it still sorts innermost — while remaining fully convertible to any D
  connector later. It also makes §9's "every `panel != "none"` port has a cutout" invariant true for
  the first time. Full ruling and the table of consequences: **§5, "The `DBA-BL-B` blank carries the
  full D hole"**; per-SKU: `layout-patch-wall.md` §16.6.
- **Adopted, part B (decoders).** The three decoders' slot 3 becomes `DBA-BL-B` by editing the
  `panel` field in three device files. **Slot order is unchanged on all three** (the blank's rank is
  the lowest, and it was already the innermost of block B), and every envelope figure is unchanged.
- **Blocking, part B (encoders).** **R23**: the Mini-DIN-8 is `panel:"none"`, so both
  `mcc_end_zone()` and T1-18(c) filter it out — the solver cannot see a port that stays internal but
  is now internally cabled. The plug sits dead inside the ⌀38 fan aperture with 30.0 mm to the fan
  frame / 25.0 mm to the reservation, and its length is `unknown`. **Take M12 before touching
  `pro-convert-hdmi-plus` or `pro-convert-sdi-plus`.** `fan_y` is the escape and it is marginal
  (27.35 mm of travel against ~27 mm needed).
- **No new printed geometry for cable management.** No zip-tie anchor, no clip, no channel, no
  thermoswitch pocket. The fan lead, the switch lead and the plug all live in free end-zone volume
  that is already reserved, and the existing answer to cable dressing is an adhesive tie base
  (`BOM.md:67`). Adding a printed floor anchor now would put a new feature into `mounts.scad` —
  positioned from unmeasured cable geometry, and guarded by a `mcc_floor_keepout()` pairwise assert
  that **does not yet exist** (D16, still open). **Deferred with an explicit trigger:** if the first
  physical build shows a lead that can reach the fan aperture, add the anchor via `mounts.scad`
  only, never in `shell.scad`, and only after D16 lands.
- **The thermoswitch is a sourcing constraint, not a modelled part.** The plenum gives
  `10.8 − MCC_LID_CLEAR 2.0` = **≤ 8.8 mm** for body + thermal pad. Publish it, buy to it, do not
  invent a body height for `constants.scad` (M11).
- **R6 is largely retired** for the default build (no splitter ⇒ the device is the PD on an 802.3at
  link, 25.5 W, and the conversion loss and in-case splitter heat both vanish). **R21, R22, R23 are
  new**; **M8–M13** added. §6's splitter reservation rule is **unchanged** — the splitter is now the
  named fallback, which is exactly why its 20 mm may not be reclaimed.
- **Two deviations found while gating: D17** (`BOM.md:194` tells the builder to tap 5 V from the
  USB-B *input*, which carries none under PoE) and **D18** (the three-way disagreement on how
  "is this a blank?" is tested, which becomes a real defect the moment `hole_d` changes).

**Architect verdict, 2026-09-08 (rev 7): the seven remaining SKUs (issues #3–#9) are APPROVED WITH
ONE BLOCKING LIBRARY CHANGE.** Full per-SKU fit-check table, ruling and parallel-work rules:
**`layout-patch-wall.md` §16**; the two record corrections: **§15 ruling 2026-09-08c**.

- **Six of seven need no library change.** Slot order, envelope, pitch, end zones, bay depth, cradle
  ribs, fastener count and every aperture assert come out correct for all seven straight from the
  data — §4's acceptance test holds. The **plus** family is `shell.scad`'s first use and was audited
  specifically: there is no compact-only assumption anywhere in L1/L2 (no family branch, no literal
  device dimension outside `devices/`). Envelopes: compact `193.9–194.9 × 158.80–159.85 × 51.0`,
  plus `210.5–211.5 × 165.30–166.35 × 51.0`, all ≥ 38.5 mm inside the 250 mm assert limit.
- **BLOCKING: T1-18(c).** `lib/mcc/shell.scad:360-366` uses `mcc_plug_len("NBB75DFGB")` = 40.6 as the
  BNC *axial* term, but that figure **is** the Belden 4855R bend radius (`constants.scad:588-592`
  says so). The assert therefore double-counts a lateral allowance against an axial budget and fails
  by **14.60 mm** on SDI TX, SDI Plus, NDI to SDI and NDI to AIO. Fix: give the axial term its own
  `assumed` table entry (`bnc → 25.0`, pending M6), leaving the envelope untouched — no geometry
  moves and no golden changes. **Growing `ez_pos` to 55.6 is rejected** (it would add 14.6 mm of `L`
  to four cases on a number that is admittedly not an axial figure), and so is downgrading the
  assert. Because it touches `constants.scad` + `shell.scad`, it must land **once, first, on a
  single pre-flight branch**, with the stale `new-case-variant` skill (D13) fixed alongside it.
- **HDMI-ended SKUs pass T1-18(c) with exactly 0.00 mm of slack.** When `depth-mockup` (M6) measures
  the straight HDMI plug above 25 mm, four cases fail at once and the answer is `L`, not the assert.
- **Merge order: compact first (#3 → #4 → #8 → #9), then plus (#5 → #6 → #7).** Develop in parallel,
  merge in order, so a plus-family surprise lands against a known-good `main`.
- **Two views per PR, both mandatory:** an ISO of the assembly *and* a straight-on `−Y → +Y`
  orthographic elevation of the patch wall with the plate placed. Both defects this repo has shipped
  to the user (D9's blob, and rev 7's mirrored reliefs) are unambiguous only in that elevation.
- **Escalations for the user, not for a developer:** (i) R5 says the fan is not optional for the 10 W
  Plus models, yet #5/#6/#7 will inherit `["fan", false]` from the copied template — confirm before
  those three merge; (ii) D12 — the `external_ports` variant key is inert, so decide whether to
  implement it or drop it.
- **Five new deviations logged (§13): D12–D16.** None of them is work for a variant branch.

**Architect verdict, 2026-09-08 (rev 6): the user's rejection of the patch-wall openings is UPHELD;
the proposed top-open (U-notch) aperture is REJECTED; the fix is a shape-and-bore change only.**

- **Adopted.** Keep the plate-in-a-stepped-rabbet aperture exactly as rev 5 specifies it — one plate,
  one continuous stepped rabbet, `n_slots` discrete windows through the 3 mm lip, plate face 3.0 mm
  behind the wall face, 4 × M3 at `mcc_panel_fixing_pos()`, flange-fixing bosses on the plate's rear.
  **Change only the window's 2-D profile:** `union()` of a truncated-teardrop body circle
  `⌀(mcc_cutout_d + 2·MCC_CLR_SLIDE)` and two plain ⌀8.88 boss reliefs — never a `hull()`. That makes
  the whole window boundary hide behind the plate, so from outside the user sees exactly what they
  asked for: a flat plate face, `n_slots` exactly-round cutouts, two ⌀3.4 screw holes per slot.
  Residual: 1.04–1.24 mm of relief crescent per slot, 2 mm behind the plate face, covered by the
  fitted connector.
- **Rejected: the top-open U-notch.** It buys "no windows" at the price of the patch wall's top
  continuity over 86 % of its length (drop rule, ASA warp), the tongue-and-groove closure along the
  whole patch side (D-07), two of the four plate fixings, the `n_fast = 6` patch-wall fastener's
  gusset, and it forces `MCC_PLATE_H` off its `MCC_D_FLANGE[1] + 2·MCC_D_FLANGE_EDGE_MARGIN`
  derivation and perturbs the fixed `H = 51.0`. One word of code removes the blob instead.
- **Rejected: moving the flange-fixing bosses into the shell lip** (option C) — it would give a
  perfect circle with no crescents, but it makes 8 inserts per case a blind operation, needs
  non-stock screws, and destroys the bench-loadable plate.
- **Two print-blocking defects found while ruling (D10):** `mcc_neutrik_d_bosses()` leaves 0.3 mm of
  solid ASA on the connector-screw axis, and the four plate-fixing bosses in `shell.scad` have no
  bore at all. **Neither the connectors nor the plate can be fastened on the part as modelled.** Fix
  both under T1-35 before any print; print the `neutrik-tile` coupon, which exists for exactly this.
- **Envelope unchanged.** `L`, `W`, `H`, `plate_l`, `MCC_PLATE_H`, slot pitch, slot assignment and
  every fixing position are untouched; only `tests/golden/*.json` volumes move.
- Six new `assumed` constants (`MCC_APERTURE_BRIDGE_MAX`, `_SELF_SUPPORT_MAX_D`, `_CAP_RISE`,
  `_RELIEF_INTRUSION_MAX`, `_LIP_WEB_MIN`, `MCC_INSERT_BORE_EXTRA`); **no `MCC_APERTURE_TOP_OPEN`.**
  Full spec: `layout-patch-wall.md` §2.5, §9 T1-34a–d/T1-35, §11 rev-6 addendum, §15 ruling
  2026-09-08b.

**Architect verdict, 2026-09-08 (rev 5): the L2 implementation plan
`docs/plans/2026-09-08-l2-first-case.md` is APPROVED WITH CHANGES.** The envelope arithmetic
(193.9 × 159.85 × 51.0), the coordinate frame, the slot/pitch/end-zone maths, the 6-fastener
placement including the far-wall displacement to −12.64, and the `part=="assembly"` export exclusion
are all correct. Changes required before a developer starts: the corrected slot order (§3), the
aperture spec (§2.5), `MCC_TG_W/H = 1.6/2.0`, `MCC_VENT_INTAKE_BAND_H = 18.0`, the deterministic
far-flank rib rule (§7), an `orient` parameter on `poe_splitter.scad` instead of hand-rolled
tie-downs, and the ten further corrections in `layout-patch-wall.md` §15. Nothing structural is
blocked; `shell.scad` may be written against `layout-patch-wall.md` **rev 5**.

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
