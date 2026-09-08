---
name: new-case-variant
description: Scaffold models/<slug>/case.scad as a thin assembly, copied from the normative models/pro-convert-for-ndi-to-hdmi/case.scad template, from an existing device data record; render/golden/BOM/preview it, and know the parallel-work file boundaries for the seven-SKU fan-out; use whenever a new Magewell device needs its own case, after its device data file already exists.
---

# new-case-variant

`models/<slug>/case.scad` (L4) is a thin, ~130-line assembly file — the **only** place that
composes geometry for a case (architecture.md §4). All of `lib/mcc/**` — `shell.scad`,
`cradle.scad`, `mounts.scad`, `vents.scad`, `panel.scad`, `neutrik.scad`, `fasteners.scad`,
`fan.scad`, `poe_splitter.scad`, `ghost.scad`, `ports.scad`, `layout.scad` — **already exists** and
is stable. The normative template is the real, already-built, already-passing first case:
**`models/pro-convert-for-ndi-to-hdmi/case.scad`.** This skill tells you to copy it, what to change,
and — just as importantly — when to stop instead of improvising.

## Stop-and-report gate — read this first

**If the layout asserts fail for your new device (`python scripts/build.py render <slug>` errors
out of `mcc_case_layout()`, `mcc_slot_assignment()`, or any Tier-1 assert inside `mcc_shell_base()`
— T1-18(c) included), STOP.** That is a library change (`lib/mcc/**`), not a variant-branch problem.
Do not edit `lib/mcc/**` from a variant branch, do not "work around" a failing assert by hand-rolling
geometry in `case.scad`, and do not weaken/relax an assert. Report which assert fired, on which
device, and with what numbers, to the teamlead/`solution-architect` — it is a single-pre-flight-branch
fix that lands once for everyone, exactly the class of bug §16.3's T1-18(c) BNC fix was
(`.claude/knowledge/layout-patch-wall.md` §16.3, architecture.md §13 deviation history). A model
file that contains real `cuboid()`/`diff()`/raw BOSL2 geometry instead of calls into L2 modules is
exactly the "adding a device touched the library" failure architecture.md §4's acceptance test
exists to catch.

## Precondition: the device data file must already exist

Use `device-portmap` first if `lib/mcc/devices/<slug>.scad` doesn't exist yet. `new-case-variant`
consumes that file; it doesn't create it. The device file's `panel` field per port is the **only**
thing that decides which connectors this case brings outside — see "cfg vs. the device file" below.

## The normative template, annotated

Read `models/pro-convert-for-ndi-to-hdmi/case.scad` end to end before scaffolding a new one. Its
real structure, in order:

1. **Includes** — exactly two, nothing else:
   ```openscad
   include <mcc/mcc.scad>
   include <mcc/devices/pro-convert-for-ndi-to-hdmi.scad>
   ```
   The barrel (`mcc/mcc.scad`) `include`s `constants.scad` and `use`s every L1/L2 file, so every
   `mcc_*` module/function used below is already in scope. Nothing else is ever `include`d/`use`d
   in an L4 file.
2. **`$fa`/`$fs`** — the one and only place `$fn`-adjacent globals are set: `$fa = 1; $fs = 0.4;`.
   Never a global `$fn`.
3. **`part`** — `part = "base";`, overridden via `-D part="..."`. Valid values:
   `"base"`, `"lid"`, `"panel"` (the three `scripts/build.py` actually renders/checks/goldens —
   `discover_models()` hardcodes `parts=["base","lid"]` plus `"panel"` iff the literal substring
   `part == "panel"` appears in the file, so **do not rename or remove that branch**), plus four
   preview-only branches never picked up by `build.py`: `"assembly"`, `"panel_placed"`,
   `"ghost_device"`, `"ghost_plugs"`.
4. **`explode`** — `explode = 0;`, a Z-lift in mm applied to the lid only when
   `part == "assembly"`. Preview aid only, no effect on exported parts.
5. **Variant config (`cfg`)** — case-level options ONLY. **There is no `external_ports` key.** An
   earlier draft of this skill described one ("omit an id to blank it"); it was never implemented —
   `mcc_slot_assignment(dev)`/`mcc_case_layout(dev, cfg)` derive `n_slots` and every slot's part
   **solely** from `mcc_ports_external(dev)`, i.e. the device file's own `panel` field per port
   (architecture.md §13 deviation D12, `.claude/knowledge/layout-patch-wall.md` §16.4). Copy the
   template's real pattern:
   ```openscad
   fan      = false; // -D fan=true      renders the live fan cutout -- quick go/no-go check
   splitter = false; // -D splitter=true (reserved key; no live cutout exists yet either way)

   variant = [
       ["fan",       fan],
       ["splitter",  splitter],
   ];
   ```
   Top-level `fan`/`splitter` variables (not just inline literals in the `variant` list) are what
   make `-D fan=true` work from the command line — keep that indirection, don't inline the
   booleans. Document every key your case actually consults in a comment block at the top of the
   file, the way the template does (`fan`, `splitter`, and the two optional ones — `vesa`
   (default true) and `fan_y` (default the device's own Y centreline) — read `mcc_shell_base()`'s
   own doc comment in `shell.scad` for the authoritative list before assuming a key exists).
6. **`dev`** — `dev = MCC_DEV_<SLUG>;`, the device record constant from your device data file.
7. **`_mcc_case_slot_list(dev, cfg)`** — a small pure **function** (data assembly, not geometry —
   legitimate per the stop-and-report gate above) that turns `mcc_slot_assignment(dev)` into the
   `[x, y, part, mirror]` list `mcc_panel_plate()` expects. Copy it verbatim; it has no per-device
   logic.
8. **`L_dims` + two `echo()`s** — `mcc_case_dims(dev, variant)` plus an echo of `L`/`W`/`H` and of
   `mcc_slot_assignment(dev)`. Keep both; they are the cheapest sanity check available and every
   PR's render log should show them.
9. **`_mcc_case_at_device(layout)`** — places `children()` at the device's assembled position
   (`x_dev_c`, `y_dev_c`, `z_dev_lo + dev_h/2`). Copy verbatim.
10. **`_mcc_case_panel_placed(layout)`** — places the panel plate at its assembled position in the
    patch wall (`rotate([-90,0,0])`, front face at the bezel-recessed plane). Copy verbatim — this
    is exactly the module whose absence caused deviation D9 (the rejected `hull()`ed aperture) and
    ruling 2026-09-08c C1 (the mirrored boss-relief positions) to go unnoticed for as long as they
    did; getting its placement right is why the elevation preview below is mandatory.
11. **The `if (part == ...)` chain** — `"base"` → `mcc_shell_base(dev, cfg)`; `"lid"` →
    `mcc_shell_lid(dev, cfg)`; `"panel"` → `mcc_panel_plate(size = mcc_panel_plate_dims(dev), slots
    = _mcc_case_slot_list(dev, variant))`; `"assembly"` → base + lid (exploded) + panel_placed +
    ghost, colour-coded, **not exported by `build.py`** (invisible to `render --all`); `"panel_placed"`
    → the plate alone at its assembled position (web-viewer convenience); `"ghost_device"` /
    `"ghost_plugs"` → solid (non-`%`) device-bbox / plug-envelope exports for a web viewer, also
    never picked up by `build.py`. Copy the whole chain; do not add new geometry inside any branch
    beyond calling these L2 modules.

**The real, current library API** (everything the template above calls):

| Symbol | File | Signature |
|---|---|---|
| `mcc_shell_base` / `mcc_shell_lid` | `shell.scad` | `(dev, cfg)` → module, emits the base/lid solid |
| `mcc_case_layout` | `layout.scad` | `(dev, cfg)` → struct (L/W/H, every derived position — L1, pure function) |
| `mcc_case_dims` | `layout.scad` | `(dev, cfg)` → `[L, W, H]` |
| `mcc_slot_assignment` | `layout.scad` | `(dev)` → list of `[["slot",i],["port_id",id],["part",part]]` |
| `mcc_panel_plate_dims` | `layout.scad` | `(dev)` → `[plate_l, MCC_PLATE_H]` |
| `mcc_panel_plate` | `panel.scad` | `(size, slots=[], t=, rim_t=, rim_w=)` → module, the flat printed plate |
| `mcc_ghost` | `ghost.scad` | `(dev, show=)` → module, `%`-modified device+plug visualisation |

There is no `mcc_shell(family=, device=, variant=, half=)` and no `mcc_panel(device=, variant=,
face=)` anywhere in this library — an earlier draft of this skill invented both signatures
(architecture.md §13 deviation D13). If you find yourself wanting to call either, you are looking
at stale muscle memory from that draft; use the table above instead.

## Scaffolding steps

1. Confirm the device data file exists and passes `tests/test_ports.scad`
   (`python scripts/build.py smoke`).
2. Copy the template:
   ```
   mkdir models/<slug>
   cp models/pro-convert-for-ndi-to-hdmi/case.scad models/<slug>/case.scad
   ```
3. Edit exactly these things in the copy — nothing structural:
   - The two `include` lines' device-file path and the `MCC_DEV_<SLUG>` symbol name (steps 1 and 6
     above).
   - Every echo string's slug prefix (`"pro-convert-for-ndi-to-hdmi: ..."` → `"<slug>: ..."`).
   - The `-o out/<part>.stl` example path in the file's own header comment.
   - The `variant` config's `fan`/`splitter` defaults, only if your device's BOM genuinely differs
     from `false`/`false` — do not flip either just to "try it"; see the escalation note below.
   - Leave every module reference, every function call, the whole `if (part == ...)` chain, and
     `_mcc_case_slot_list`/`_mcc_case_at_device`/`_mcc_case_panel_placed` untouched.
4. Render:
   ```
   .venv\Scripts\python scripts\build.py render <slug>
   ```
   If this errors inside `mcc_case_layout()` or `mcc_shell_base()` — stop-and-report gate above.
5. Check + golden:
   ```
   .venv\Scripts\python scripts\build.py check --all
   .venv\Scripts\python scripts\build.py golden --update <slug>
   ```
   Eyeball the new `tests/golden/<slug>.{base,lid,panel}.json` bbox/volume against
   `.claude/knowledge/layout-patch-wall.md` §16.1's fit-check table for your SKU before committing
   — `--update` captures whatever rendered, it does not itself validate that the geometry is
   *correct*.
6. Fill the `BOM.md` section for this variant — **only your own `### <slug>` block**, see
   `bom-update`.
7. Render the two mandatory preview images (below) and eyeball the elevation.
8. Run the checklist at the bottom of this file before opening the PR.

## Required preview renders (both mandatory, both go in the PR body)

Every case variant must publish an ISO view of the assembly **and** a straight-on `−Y → +Y`
orthographic elevation of the patch wall with the plate in place
(`.claude/knowledge/architecture.md` §13 deviation D11 / `.claude/knowledge/layout-patch-wall.md`
§16.5). The elevation is the **only** view in which this repo's two shipped patch-wall defects — the
`hull()`ed diagonal blob (D9) and the mirrored boss-relief positions (ruling 2026-09-08c C1) — were
visible; an oblique ISO did not catch either. A PR without the elevation is not reviewable.

Both lines below are verified working against `models/pro-convert-for-ndi-to-hdmi/case.scad` (case
centre ≈ `(0, 0, 25.5)`, footprint ≈ `194 × 160 mm`) — re-tune `--camera`'s translate/distance for a
SKU with a materially different `L`/`W` (the `plus` family is ~211 × 166 mm), but start here rather
than guessing from scratch:

```
set OPENSCADPATH=<repo>\lib

REM ISO view of the assembly, lid exploded 40 mm
"C:\Program Files\OpenSCAD (Nightly)\openscad.com" --backend=Manifold --render ^
  --projection=p --camera=0,0,25.5,55,0,35,600 --imgsize=1400,1000 ^
  -D "part=\"assembly\"" -D "explode=40" -D "MCC_SHOW_GHOST=false" ^
  -o out\preview\<slug>-iso.png models\<slug>\case.scad

REM Straight-on -Y -> +Y elevation of the patch wall, plate placed, no explode
"C:\Program Files\OpenSCAD (Nightly)\openscad.com" --backend=Manifold --render ^
  --projection=o --camera=0,80,25.5,90,0,180,600 --imgsize=1400,700 ^
  -D "part=\"assembly\"" -D "explode=0" -D "MCC_SHOW_GHOST=false" ^
  -o out\preview\<slug>-patch-wall-elevation.png models\<slug>\case.scad
```

Notes learned tuning these against NDI to HDMI, so the next developer doesn't re-discover them:

- **`--render` is required**, not optional. Without it OpenSCAD's fast OpenCSG preview does not
  depth-sort the translucent lid correctly against the opaque base/panel and produces a
  moiré/dashed-stripe artifact inside the connector cutouts that looks alarming but is a rendering
  artifact, not geometry (`build.py check`'s `parts=1`/`watertight=True` on the actual STL is the
  real ground truth, not the PNG).
- The elevation's `--camera` distance needs real headroom over the naive "half the footprint"
  guess — `300` (a plausible first guess for a ~194 mm-wide case) visibly crops the outer two slots
  off both edges of the frame; `600` frames all four slots with margin. If your SKU's `plate_l` is
  much longer (the `plus` family, up to ~185 mm vs. compact's ~168 mm) or has only 3 slots (HDMI
  TX / SDI TX), re-render once and adjust distance before trusting the crop.
- **What "correct" looks like in the elevation:** `n_slots` **exactly round** cutouts (never a
  diagonal/teardrop blob — that shape was deviation D9 and is retired), each with two small screw
  dots near its edge on the Neutrik diagonal, the same diagonal orientation repeated identically at
  every slot (a slot whose dots look rotated 90° relative to its neighbours is the mirrored-relief
  regression ruling 2026-09-08c C1 fixed once already — report it, don't silently "fix" it
  yourself), and the 4 plate-fixing screw dots at the rim corners. A small (≤ ~1.5 mm) crescent
  sliver at one edge of a cutout is expected (T1-34b) — it is the shell's own boss-relief window
  showing through, covered by the fitted connector body in real life; it is not a defect.

## cfg vs. the device file — what decides what

- **Device file** (`lib/mcc/devices/<slug>.scad`, from `device-portmap`): physical facts — every
  port that physically exists, its `face`/`pos`/`kind`, and its `panel` value (a real Neutrik part
  number, or `"none"` for internal-only). This is the **only** thing that decides the slot set,
  slot order, `n_slots`, `L`, `W`, and every panel-plate dimension — all derived mechanically by
  `mcc_slot_assignment()`/`mcc_case_layout()` from `mcc_ports_external(dev)`.
  `.claude/knowledge/layout-patch-wall.md` §3 is the algorithm; do not hand-place a slot.
- **Variant config** (`case.scad`'s `variant`): case-level options only — `fan`, `splitter`, and
  the two optional keys (`vesa`, `fan_y`). It cannot add, remove, or reorder a connector. If a port
  must not appear on a case, that is a device-file decision (`["panel","none"]` on that port, the
  same convention the Mini-DIN-8/rotary/button ports already use), never a variant-config one.

## Fan/splitter reservation — always on, regardless of the flag

Per architecture.md §6's reservation rule: `mcc_shell_base()` reserves the fan bay and the
PoE-splitter bay as internal keep-out volume **even when `cfg`'s `"fan"`/`"splitter"` are `false`**.
`"false"` only skips the live cutout/hardware; it never shrinks the reserved volume. Don't drop
either key "because this variant doesn't have a fan" — the whole point is that enabling a fan later
must not move connectors or invalidate an already-printed part.

**Escalation, not a variant-branch decision:** `.claude/knowledge/layout-patch-wall.md` §16.2 item 4
/ architecture.md §13 R5 flags that the Plus-family devices' 10 W thermal budget may make
`fan = false` the wrong default — but this is an open question for the user, not something a
variant branch resolves unilaterally. Copy the template's `false`/`false` default and say so in the
PR description; do not silently flip it.

## §16.5 parallel-work rules (seven-SKU fan-out, `.claude/knowledge/layout-patch-wall.md` §16.5)

**A variant branch MAY touch — and nothing else:**

- `models/<slug>/case.scad` *(new — a copy of the template with only the changes listed above)*
- `tests/golden/<slug>.base.json`, `<slug>.lid.json`, `<slug>.panel.json` *(new, via
  `build.py golden --update <slug>`, numbers eyeballed against §16.1 before committing)*
- **only its own `### <slug>` block** under `## Per-variant BOM` in `BOM.md`
- **only its own status row** in `README.md`, if that row exists

**A variant branch MUST NOT touch:**

- **anything under `lib/mcc/`** — §4's acceptance test exists precisely so a new device never
  needs one. If it appears to, stop-and-report (top of this file).
- another SKU's `models/**` or `tests/golden/**`
- `BOM.md`'s common/coupon/purchase sections, or another slug's block
- `README.md` structure or another SKU's row; `CLAUDE.md`; `.claude/knowledge/**`;
  `.claude/skills/**`; `scripts/**`; `.github/**`; `docs/plans/**`
- `tests/test_*.scad` — shared across every SKU, and a seven-way conflict magnet

## Merge order (compact first, then Plus)

```
pre-flight (library fix, if any, always lands first and alone) -> #3 hdmi-tx -> #4 sdi-tx
                                                                -> #8 ndi-sdi -> #9 ndi-aio
                                                                -> #5 hdmi-plus -> #6 sdi-plus
                                                                -> #7 ndi-hdmi-4k
```

The compact family is proven geometry (the shipped NDI to HDMI is compact); landing the smallest
delta first (HDMI TX: 3 slots, no BNC) proves the copy-the-template path end to end, the next two
prove the BNC path, and the Plus family — `shell.scad`'s first use of that chassis — merges last, so
a Plus-specific surprise lands against a `main` the compact four have already proven good. Branches
may be *developed* in parallel; it is the **merge order** that matters.

## Checklist for a new variant

- [ ] Device data file exists and passes `tests/test_ports.scad`.
- [ ] Copied `models/pro-convert-for-ndi-to-hdmi/case.scad` — did not write geometry by hand, did
      not invent a `mcc_shell()`/`mcc_panel()` call.
- [ ] `python scripts/build.py render <slug>` succeeds for `base`/`lid`/`panel` with no library
      assert firing. If one fired, stopped and reported instead of editing `lib/mcc/**`.
- [ ] `python scripts/build.py check --all` passes (watertight, single shell, bbox).
- [ ] `tests/golden/<slug>.*.json` created via `golden --update <slug>` and eyeballed against
      `.claude/knowledge/layout-patch-wall.md` §16.1.
- [ ] ISO assembly preview **and** straight-on patch-wall elevation rendered; the elevation shows
      exactly-round cutouts with identically-oriented, aligned screw dots per slot (not mirrored,
      not a diagonal blob) — both images attached to the PR.
- [ ] `variant`'s `fan`/`splitter` left at the template default unless the user has explicitly
      decided otherwise for this SKU.
- [ ] `BOM.md`'s `### <slug>` section added (`bom-update`).
- [ ] README status line updated (only this SKU's row).
- [ ] Touched only the files §16.5 allows for a variant branch.
