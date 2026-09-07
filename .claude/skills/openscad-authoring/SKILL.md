---
name: openscad-authoring
description: House conventions for writing or reviewing OpenSCAD in this repo (layering, mcc_ naming, named args, $fn policy, assert style, BOSL2 idioms); use before writing or editing any .scad file under lib/mcc/** or models/**.
---

# openscad-authoring

This is the highest-value skill in the repo: it keeps every `.scad` file inside the conventions in
`.claude/knowledge/architecture.md` §3 without the rules having to be re-explained per task. OpenSCAD
has no namespaces and no import isolation — the layering below is a **convention enforced by review
and grep-able `use`/`include` edges**, not by the language. Read `architecture.md` §3-§7 in full
before writing anything non-trivial; this file is the condensed, actionable version.

## Layer map — dependencies point down only

```
L4  models/<device-slug>/case.scad        assembly; the ONLY place that composes geometry
L3  lib/mcc/devices/*.scad                DATA ONLY — no geometry, no modules, no BOSL2 calls
L2  lib/mcc/shell.scad / panel.scad / cradle.scad / mounts.scad / vents.scad
L1  lib/mcc/neutrik.scad / fasteners.scad / fan.scad / poe_splitter.scad / ghost.scad
L0  lib/mcc/constants.scad / ports.scad / util.scad   (variables + pure functions ONLY)
    lib/BOSL2/                                         submodule, pinned SHA
```

An **upward** edge (e.g. `constants.scad` calling into `shell.scad`, or a device file importing
geometry) is a deviation — stop and report it, don't quietly work around it.

## Include discipline

- `constants.scad` is **variables and pure functions only — never a module.** This is a hard rule
  (architecture.md:90-92) so repeated `include <>` stays idempotent and warning-free. `ports.scad`
  and `util.scad` follow the same rule.
- Everything else is consumed with `use <>` (pulls in modules/functions, not variables — that's
  fine, L1+ files don't define bare variables other files need).
- `lib/mcc/mcc.scad` is the barrel: it `include`s `constants.scad` and `use`s every L1/L2 file. A
  model file (`L4`) imports **only** `<mcc/mcc.scad>` plus its own device data file — nothing else.
  Library files import their own direct dependencies, never the barrel (importing the barrel from
  inside the library creates a cycle).
- `lib/mcc/devices/*.scad` imports **nothing except `ports.scad`**. If a device file seems to need
  geometry, the design is wrong — geometry belongs in L2, driven by the device's data.
- `constants.scad` currently `include <BOSL2/std.scad>` directly for `struct_val()`/`search()` — an
  `include` is not a module definition, so this doesn't violate the "no module" rule; see the
  comment at the top of `lib/mcc/constants.scad` for the exact reasoning if you need to repeat this
  pattern elsewhere.

## Naming (mandatory — one global namespace)

| Kind | Convention | Example (real, from `lib/mcc/constants.scad`) |
|---|---|---|
| Public module | `mcc_` prefix, snake_case | `mcc_neutrik_d_cutout()` |
| Public function | `mcc_` prefix, snake_case | `mcc_bay_depth(part)`, `mcc_panel_hole_d(part)` |
| Private helper | `_mcc_` prefix | `_mcc_panel_part_rec(part)` |
| Constant | `MCC_` prefix, UPPER_SNAKE | `MCC_WALL`, `MCC_D_FLANGE`, `MCC_PANEL_PARTS` |
| Device data symbol | `MCC_DEV_<slug>` | `MCC_DEV_PRO_CONVERT_HDMI_TX` |
| File | lower_snake_case `.scad` | `poe_splitter.scad` |
| Model directory | Magewell slug, 1:1 with `knowledge/magewell/models/` | `models/pro-convert-hdmi-tx/` |

## Parameter conventions

- **All lengths in millimetres, no unit suffixes.** The one exception is the literal `1/4"-20`
  thread name — always via the named constant `MCC_TRIPOD_MAJOR_D`, never an inline number. See the
  `MCC_TRIPOD_MAJOR_D` block in `lib/mcc/constants.scad` (line numbers drift — that file is under
  active development by another workstream; grep for the constant name) for how it documents its own
  provenance.
- Angles in degrees, temperatures °C, power W.
- Suffixes: `_d` diameter, `_r` radius, `_t` thickness, `_h` height, `_w` width, `_l` length, `_clr`
  clearance, `_n` count, `_pos` position vector, `_pitch` centre-to-centre.
- **Named arguments at every call site with more than two parameters.** Positional args past two are
  a deviation — a wrong-order silent mistake here is invisible geometry, not a compile error.
- **No magic numbers in L2/L3/L4.** Every dimension traces to `constants.scad` or a device data
  file. A literal number outside `constants.scad` that isn't `0`, `1`, `2`, or an obvious multiplier
  is a deviation — pull it into a named constant instead, with the same `knowledge/<file>.md:<line>`
  citation style `constants.scad` already uses (see any block in that file for the pattern: value,
  then a comment citing the exact source line).

## `$fn` policy

- **Never set a global `$fn`.** Top-level model files (`L4`, the ones with `-D part=`) set
  `$fa = 1; $fs = 0.4;` and nothing else.
- Set `$fn` locally and explicitly only where facet count is functionally meaningful — connector
  holes, insert bores, fastener clearance holes: `$fn = 64` minimum.
- For any hole that must pass a real part, use BOSL2 `cyl(..., circum = true)` so the polygonal
  approximation is **circumscribed**, not inscribed. An inscribed 24.2 mm hole at `$fn=32` is
  effectively ~24.08 mm — real, because the Neutrik flange only overlaps the hole by ~0.9 mm per
  side (`knowledge/neutrik/d-series-cutout.md:43`). Getting this backwards produces a hole that looks
  right in the OpenSCAD preview and doesn't fit the connector.

## BOSL2 idioms to prefer

- `cuboid(size, rounding=r, edges=...)` over hand-rolled `hull()` of spheres/cylinders for rounded
  boxes.
- `cyl(h=, d=, circum=true, $fn=64)` for any functional round hole (see `$fn` policy above);
  `cyl(..., anchor=BOTTOM)` etc. rather than manual `translate` centring.
- `attach()` / `position()` / `orient()` / `anchor=` for placing one part relative to another,
  instead of hand-computed `translate([x,y,z])` — this is what lets a device's port `face` unit
  vector (architecture.md §7) drive geometry directly: a port's `face` is exactly a BOSL2 orientation
  vector.
- `diff("neg") { ... tag("neg") negative_shape(); }` for subtractive features instead of raw
  `difference()` trees, so the intent (what's being cut, and why) survives in the module's own
  structure and stays composable with `attach()`.
- `struct_val(rec, "key")` / `struct_set()` (BOSL2 `structs.scad`) for the assoc-list shape used by
  device records and `MCC_PANEL_PARTS` — see the "Panel-part pure accessors" section near the bottom
  of `lib/mcc/constants.scad` (`mcc_panel_hole_d`, `mcc_bay_depth`, etc. — grep for `struct_val`, that
  file's line numbers drift as another workstream develops it) as the canonical pattern for a new
  accessor.

## Assert style

Every library module asserts its own contract so a bad parameter fails loudly at render time, not
quietly at the printer (Tier 1 tests, architecture.md §9). Use `mcc_assert_range(value, lo, hi, name)`
(or the equivalent inline `assert()` with a message that names the parameter and the values) rather
than a bare `assert(cond)` — a Sonnet-tier caller needs the message to debug a failure without
re-deriving your intent. Minimum assertions to carry on any new geometry module, drawn straight from
architecture.md §9's Tier-1 table:

| Assertion | Why |
|---|---|
| `bbox ≤ MCC_BUILD - MCC_BED_MARGIN` per exported part | 256 mm bed |
| wall thickness ≥ `MCC_WALL` | decision 8 |
| panel seat thickness ≤ `mcc_panel_max_t(part)` | HDMI/USB cap at 2.0 mm |
| D-connector pitch ≥ `MCC_D_PITCH_H` / `MCC_D_PITCH_V` when placing more than one | `placement-and-depth.md:41-45` |
| `mcc_cutout_d(part)` stays in a sane band, never blown out past the flange overlap margin | `d-series-cutout.md:36-43` |
| clear depth behind each cutout ≥ `mcc_bay_depth(part)` | connector body + plug/bend allowance |
| heat-set boss OD ≥ `MCC_BOSS_MIN_RATIO * insert od` | `fasteners-and-hardware.md` boss-cracking guidance |
| no two floor features overlap | `mcc_floor_keepout()`, architecture.md §6 floor rule |
| every port with `panel != "none"` has a cutout, and vice versa | architecture.md §7 |

## Ghosts (`%` modifier)

Device/plug visualisation uses the `%` (background/transparent) modifier so it's excluded from CSG
and from STL export by construction, *and* it's gated behind `MCC_SHOW_GHOST` (default `false`) so
review can flip it on deliberately. Both belts: `%` is the mechanism, the flag is the review signal.
A ghost that ends up in an exported mesh — i.e. `%` was forgotten, not just the flag left on — is a
P1 deviation; check for it in review.

## Review checklist (run this on any new/changed `.scad` file)

- [ ] No upward layer edge (an L0/L1 file never `use`s an L2+ file).
- [ ] `constants.scad`/`ports.scad`/`util.scad` define no modules.
- [ ] Every public symbol has the right `mcc_`/`_mcc_`/`MCC_` prefix.
- [ ] Every call with >2 params uses named args.
- [ ] No bare numeric literal outside `constants.scad` (besides `0`/`1`/`2`/obvious multipliers).
- [ ] No global `$fn`; any local `$fn` is ≥64 and paired with `circum=true` on a functional hole.
- [ ] Every module asserts its own contract (see table above) — not just "hopes" the caller passed
      something sane.
- [ ] File is LF line endings, not CRLF (see failure modes below).
- [ ] `%`-ghosted geometry is also gated behind `MCC_SHOW_GHOST`.
- [ ] `models/**` never calls `mcc_neutrik_*` directly — only `mcc_panel_cutout()` (see
      `neutrik-panel` skill).

## Common failure modes

- **Inscribed vs circumscribed holes.** Forgetting `circum=true` on a functional hole at low `$fn`
  silently undersizes it — see the `$fn` policy above. This is the single most common way a coupon
  print fails to seat a connector.
- **CRLF line endings.** OpenSCAD tolerates them but they cause noisy diffs and can break some
  editor tooling; keep `.scad` files LF. Check `git diff` for a wall of red+green on an otherwise
  one-line change — that's usually a line-ending flip.
- **`include` vs `use`.** `include` pulls in everything (variables *and* modules) and is **not**
  idempotent-safe for anything that defines a module — using it where `use` belongs is how duplicate-
  definition warnings creep in. Only `constants.scad`/`ports.scad`/`util.scad` (and the barrel
  `mcc.scad` itself) are ever `include`d; everything else is `use`d.
- **A global `$fn` sneaking into a library file.** It silently changes every downstream shape's facet
  count repo-wide the next time someone renders a model that transitively includes it — this is why
  the barrel and L1+ files must never set it, only the top-level `L4` model file may.
- **A device file (`lib/mcc/devices/*.scad`) importing BOSL2 or calling a geometry module.** That's
  the layering-leak canary from architecture.md §4: "adding a new device must not touch `shell.scad`"
  — if a device file needs geometry to describe itself, the port-map shape is missing a field, not
  missing an escape hatch into L2.
