---
name: device-portmap
description: Create or verify a device data file (lib/mcc/devices/<slug>.scad) from knowledge/magewell/models/<slug>.md, including the confidence field and port-to-panel mapping; use whenever a new Magewell device needs a case or an existing device file needs a review.
---

# device-portmap

A device data file is **DATA ONLY** (architecture.md L3) — a BOSL2 assoc-list, no geometry, no BOSL2
calls beyond the record shape itself, importing nothing except `ports.scad`. This skill is how you
turn a knowledge-base model file into that record correctly.

## Record shape (verbatim from architecture.md §7 — do not improvise a different shape)

```openscad
// lib/mcc/devices/pro-convert-hdmi-tx.scad   (DATA ONLY)
MCC_DEV_PRO_CONVERT_HDMI_TX = [
  ["slug",   "pro-convert-hdmi-tx"],
  ["family", "compact"],
  ["size",   [100.9, 60.2, 23.3]],          // L, W, H (x, y, z), origin = geometric centre
  ["source", "knowledge/magewell/models/pro-convert-hdmi-tx.md"],
  ["ports", [
    // face = outward unit normal in device-local coords (plugs straight into BOSL2 orient/attach)
    // pos  = [u, v] on that face, mm from the face centre; +u = right looking at the face, +v = up
    [["id","hdmi_in"],  ["face",[ 1,0,0]], ["pos",[-18, 0]], ["kind","hdmi_a"],
     ["dir","in"],      ["panel","NAHDMI-W-B"], ["confidence","photo"]],
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

(This is the HDMI TX example from architecture.md §7 with `ptz_tally`'s `panel` corrected to
`"none"` — the Mini-DIN-8 PTZ/Tally port is a **fixed decision, stays internal** in every current
variant; see CLAUDE.md and `knowledge-lookup`'s black `-B` rule section. Do not set `panel` to
`"MINIDIN8"` unless the user has explicitly asked you to build the future feedthrough variant.)

## Field contract

| Field | Type | Meaning |
|---|---|---|
| `id` | string, unique per device | referenced by the variant config and the BOM |
| `face` | unit vector, device-local | outward normal; feeds BOSL2 `orient`/`attach` directly |
| `pos` | `[u, v]` mm | position on that face, from the face centre; +u = right looking at the face, +v = up |
| `kind` | enum string | `hdmi_a`, `rj45`, `usb_b`, `usb_a`, `bnc`, `minidin8`, `sd`, `led`, `rotary16`, `button`, `tripod_1_4_20` |
| `dir` | `in`/`out`/`bidir`/`power`/`none` | informational; drives labels and the BOM |
| `panel` | part number or `"none"`/`"blank"` | which panel connector this port is brought out to (see mapping below) |
| `confidence` | `measured`/`drawing`/`manual`/`photo`/`assumed` | **required on every port** |

## `panel` mapping — which `kind` gets which part

| `kind` | `panel` | Notes |
|---|---|---|
| `hdmi_a` | `NAHDMI-W-B` | includes loop-out HDMI ports |
| `rj45` | `NE8FDP-B` | PoE/network |
| `usb_b` | `NAUSB-W-B` | power + USB-NET config port |
| `usb_a` | `NAUSB-W-B` | second one, for decoders' USB-A host port — a device can have two `usb_*` ports, each its own record with its own `panel` entry |
| `bnc` | `NBB75DFGB` | SDI in/out |
| `minidin8` | `"none"` | **fixed decision** — PTZ/Tally stays internal; see `knowledge/components/mini-din8-feedthrough.md` for the future-variant research only |
| `sd` | `"none"` | non-functional slot on every Magewell model researched so far — never brought out |
| `led` | `"none"` | status indicator, not a port; case must leave it visible, not bring it through a panel |
| `rotary16` | `"none"` | board-index switch; case must leave it accessible (thumb/screwdriver reach), not bring it through a panel |
| `button` | `"none"` | MENU/SELECT on some NDI decoders; same as rotary — accessible, not panel-mounted |
| `tripod_1_4_20` | `"none"` | this is the device's own mounting thread, handled by `cradle.scad`/`mounts.scad`, not the panel system |
| any unused port | `"blank"` | when the case brings out a cutout position but leaves it covered — rare; usually you simply omit the port from the variant config instead |

If a `kind` shows up that isn't in this table, stop and ask — don't guess a `panel` mapping for a
port type the fixed decisions haven't covered.

## Workflow: knowledge file → device record

1. Read `knowledge/magewell/models/<slug>.md` in full — identity, physical, port layout, power,
   mounting sections all matter.
2. Also read the device's row in `knowledge/magewell/housing-families.md` for the family's face-by-
   face port order — the per-model file is often terser than the family file about exact port
   ordering on a face.
3. Determine `family`: `"plus"` (117.5×66.7×23.4) or `"compact"` (100.9×60.2×23.3) — see
   `knowledge-lookup` facts #1-2. A device on an unfamiliar chassis (e.g. the IP-decoder or IP-to-USB
   families) is out of scope for the current fixed decisions — check with the user before adding a
   `family` value not already in `shell.scad`'s family list.
4. Assign `face` vectors: pick device-local axes consistently (`[1,0,0]`/`[-1,0,0]` for the two short
   ends is the convention used by every example so far; `[0,-1,0]`/`[0,1,0]` for long sides;
   `[0,0,1]`/`[0,0,-1]` for top/bottom).
5. Assign `pos` as `[u, v]` mm from each face's centre — this is the number that is almost never in
   the knowledge base as a hard dimension (architecture.md §7: "no dimensioned port-position drawing
   exists for any model"). Estimate from the description order (left-to-right becomes increasing u)
   and mark `confidence:"photo"` or `"assumed"` accordingly — never `"measured"` or `"drawing"` unless
   you actually have one.
6. Set `panel` per the mapping table above.
7. Set `confidence` **per port**, not once for the whole file — a device file commonly mixes
   `photo` (most ports, read off a manual figure) and `assumed` (anything the source flags as
   "estimated from image" or doesn't mention at all, e.g. the exact 1/4"-20 hole position).
8. Add the `source` field pointing at the exact knowledge file you read.

## Confidence: not decoration

`knowledge/magewell/housing-families.md:8-10` states plainly that no dimensioned port-position
drawing exists for any model — every position in this repo starts as `photo` or `assumed`. This is
expected, not a gap to panic over. What matters is that the field is honest:

- `ports.scad` (once written) `echo()`s a WARNING at render time listing every port below `measured`.
- `scripts/build.py`'s **release** build fails if any port used for a real cutout is below
  `measured`; the **dev** build does not — so a `photo`-confidence device is fine to develop against,
  just not to ship.
- Upgrading a port to `measured` requires a comment in the device file naming who measured what and
  when — same pattern as the coupon-result comments in `constants.scad`.

## Rendering the ghost to eyeball a new device file

Once `ghost.scad` exists, `mcc_ghost(dev)` draws the device bounding box, port receptacle stubs, and
a plug envelope per port (extruded along `face` by `mcc_plug_len(kind)` plus a bend allowance), under
the `%` modifier and gated behind `MCC_SHOW_GHOST`. Set `MCC_SHOW_GHOST = true` and render the
relevant `models/<slug>/case.scad` at `-D part="base"` to sanity-check that your `pos` estimates put
ports somewhere physically plausible (not overlapping, not off the edge of the face) before wiring
the file into a real variant config. This is a visual sanity check, not a substitute for a coupon or
a real measurement — it catches "I put both ports at the same `pos` by mistake," not "the true
position is 3 mm off."

## Test: `tests/test_ports.scad`

Once written, this Tier-2 smoke test instantiates every `lib/mcc/devices/*.scad` record and asserts,
for every port: `id` uniqueness within the device, `face` is a unit vector, `kind` is a recognized
enum value, `panel` matches the mapping table above (or is explicitly `"none"`/`"blank"`), and
`confidence` is one of the five allowed values. Run it (via `scripts/build.py smoke`, see
`openscad-render`) after adding or editing any device file — a typo in `kind` or `panel` here is
exactly the kind of silent-geometry mistake the layering in `openscad-authoring` is designed to catch
early.

## Worked note: HDMI TX vs. HDMI Plus differ in more than size

Don't copy a `compact`-family device file and just change the `size` for a `plus`-family device — the
port *count* differs too: TX has no loop-out (one video connector per short end), while the Plus
family's End B carries HDMI/SDI IN **and** OUT plus the Mini-DIN-8 on one face
(`knowledge/magewell/housing-families.md:65-67`) — three ports needing ≥90 mm of flat panel on a case
that's only ~76-80 mm wide (architecture.md §11 R3, currently unresolved — flag it rather than
silently dropping a port when you hit this on a Plus-family device).
