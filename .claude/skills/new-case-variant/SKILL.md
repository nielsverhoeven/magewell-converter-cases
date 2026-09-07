---
name: new-case-variant
description: Scaffold models/<slug>/case.scad as a thin assembly from an existing device data record, wire up the variant config and golden test; use whenever a new Magewell device needs its own case, after its device data file already exists.
---

# new-case-variant

`models/<slug>/case.scad` (L4) is a thin, ~40-80 line assembly file — the **only** place that
composes geometry (architecture.md §4). This skill scaffolds it correctly and, critically, tells you
when to stop instead of improvising.

## Stop-and-report gate — read this first

**`lib/mcc/shell.scad`, `cradle.scad`, `mounts.scad`, and `vents.scad` do not exist yet** (next
milestone after the knowledge base + L0 constants). `panel.scad`, `neutrik.scad`, `fasteners.scad`,
`fan.scad`, `poe_splitter.scad`, `ghost.scad`, and `ports.scad` don't exist yet either. Check
`lib/mcc/` before starting:

```
find lib/mcc -type f
```

If the module you need to call isn't implemented yet, **stop and report which module is missing —
do not write ad-hoc geometry directly in the model file to work around it.** A model file that
contains real `cuboid()`/`diff()` geometry instead of calls into L2 modules is exactly the "adding a
device touched the library" failure this decomposition exists to prevent (architecture.md §4's
acceptance test). Report back with: which case you were asked to scaffold, which L1/L2 module is
missing, and — if you can tell — roughly what that module would need to do. That's a `researcher` or
`solution-architect` conversation, not something to paper over in a Sonnet-tier implementation pass.

## Precondition: the device data file must already exist

Use `device-portmap` first if `lib/mcc/devices/<slug>.scad` doesn't exist yet. `new-case-variant`
consumes that file; it doesn't create it.

## Thin-assembly template

```openscad
// models/<slug>/case.scad
include <mcc/mcc.scad>
include <mcc/devices/<slug>.scad>

$fa = 1; $fs = 0.4;   // the ONLY place $fn-adjacent globals are set — see openscad-authoring

part = "base";  // overridden via -D part="..."

// Variant config: which of the device's ports are brought to the outside, and case-level options.
// Every id here must exist in MCC_DEV_<SLUG>'s ["ports", ...] list (device-portmap skill).
variant = [
    ["external_ports", ["hdmi_in", "usb_b", "rj45"]],  // omit an id to blank it or leave it internal
    ["fan",             false],                          // reserved regardless — see reservation rule
    ["splitter",        false],                          // reserved regardless — see reservation rule
];

if (part == "base")
    mcc_shell(family = struct_val(MCC_DEV_<SLUG>, "family"),
              device = MCC_DEV_<SLUG>,
              variant = variant,
              half = "base");
else if (part == "lid")
    mcc_shell(family = struct_val(MCC_DEV_<SLUG>, "family"),
              device = MCC_DEV_<SLUG>,
              variant = variant,
              half = "lid");
else if (part == "panel")
    mcc_panel(device = MCC_DEV_<SLUG>, variant = variant, face = [1,0,0]);
else
    assert(false, str("mcc: unknown part \"", part, "\""));
```

Treat the exact `mcc_shell()`/`mcc_panel()` signatures above as illustrative until those modules
actually exist — match whatever signature `shell.scad`/`panel.scad` end up defining, and prefer named
args per `openscad-authoring`'s parameter conventions either way.

## What belongs in the variant config vs. the device file

- **Device file** (`lib/mcc/devices/<slug>.scad`): physical facts about the device — every port that
  physically exists, where it is, what kind it is. Does not change per case build.
- **Variant config** (in `case.scad`): which of those physical ports this *specific case* brings to
  the outside, plus case-level options (`fan`, `splitter`). This is what makes "port kind, count,
  face, and position vary between devices on the same chassis" a data problem instead of a
  combinatorial-flag problem (architecture.md §4's "why not one parametric case with variant flags"
  reasoning) — the device file already carries the per-device variation; the variant config only ever
  says yes/no per already-declared port id.
- A port present in the device's `["ports", ...]` list but omitted from `external_ports` stays
  internal or gets blanked, per its own `panel` field from `device-portmap` (`"none"` stays internal
  regardless of the variant config; a real Neutrik `panel` value omitted from `external_ports` gets a
  DBA-BL-B blank instead of the live connector — confirm this is actually `mcc_panel_cutout`'s
  intended behavior once `panel.scad` exists, rather than assuming).

## Fan/splitter reservation — always on, regardless of the flag

Per architecture.md §6's reservation rule: `shell.scad` reserves the fan bay and the PoE-splitter bay
as internal keep-out volume **even when `fan = false` and `splitter = false`** in the variant config.
Don't skip passing these keys "because this variant doesn't have a fan" — the whole point is that
enabling a fan later must not move connectors or invalidate an already-printed part. If the template
above is missing a `fan`/`splitter` key, that's a bug in the variant config, not something to leave
implicit.

## After scaffolding: golden test

```
python scripts/build.py golden --update
```

Run this once the case renders cleanly (`scripts/build.py render` succeeds, `check` passes) to create
`tests/golden/<slug>.json`. Review the generated bbox/volume numbers by eye before committing —
`--update` regenerates unconditionally; it does not itself validate that the geometry is *correct*,
only that it's captured. See `openscad-render` for what the golden diff actually checks going
forward.

## BOM section

Add a per-variant section to `BOM.md` listing this case's Neutrik parts (by port), inserts,
thumbscrews, the 1/4"-20 bolt + nylon nut, and fan/splitter if enabled — see `bom-update` for the
full table shape and how to regenerate it mechanically rather than hand-maintaining it.

## README status update

Update the model's status line in the repo README (existence/ownership of `README.md` itself belongs
to another workstream in this repo — only edit the specific status line/row for your new variant, not
the file's structure or other rows).

## Checklist for a new variant

- [ ] Device data file exists and passed `tests/test_ports.scad` (once that test exists).
- [ ] Confirmed every L1/L2 module the assembly needs already exists — stopped and reported if not.
- [ ] `case.scad` is thin: no direct `cuboid()`/`diff()`/raw BOSL2 geometry calls, only calls into L2.
- [ ] Variant config lists every external port by `id`, plus `fan`/`splitter` keys (even if `false`).
- [ ] `$fa`/`$fs` set once at the top of `case.scad`; no `$fn` set globally.
- [ ] `scripts/build.py render` and `check` pass for both `part="base"` and `part="lid"` (and
      `part="panel"` per external face).
- [ ] `tests/golden/<slug>.json` created via `build.py golden --update` and the numbers eyeballed.
- [ ] `BOM.md` section added (`bom-update`).
- [ ] README status line updated.
