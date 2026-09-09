# Implementation plan — external manual fan switch + KUOQIY USB-A fan-adapter cable (GitHub issue #32)

Status: **PLANNED, not implemented.** Researched 2026-09-09 against `.claude/knowledge/architecture.md`
(rev 8) and `.claude/knowledge/layout-patch-wall.md` (rev 8) as they stand on `main` (`14ca0db`). Per
`.claude/knowledge/ticket-source.md` this plan is also posted as a comment on GitHub issue #32.
**Team Charter gate reminder for whoever picks this up:** this is a code-changing plan and must go
through `solution-architect` validation before any developer starts — this document is the
researcher's half of that handoff, not a substitute for it. In particular the architect should rule
on: (a) the new `MCC_FAN_SWITCH` constant/provider shape, (b) the placement formula in §2, and (c)
whether T1-38/T1-39 belong where this plan puts them (§4).

---

## 0. The ask, restated precisely

Two independent deliverables, both gated behind the fan being enabled:

1. **KUOQIY USB-A → 3/4-pin PWM fan adapter cable** (5 V, 30 cm, black, amazon.nl ASIN B0D1C36WKB,
   €7.98/5) as the fan power lead on the **decoders** (the fan's 3-pin plug mates directly with the
   NF-A4x10 5V — no OmniJoin/NA-AC2 adaptor needed). Of the three decoders, only
   `pro-convert-for-ndi-to-hdmi-4k` ships `fan = true` today (§16.6 of `layout-patch-wall.md`), so
   that SKU is where this cable becomes a *real* BOM line; the other two decoders only need it if a
   user builds with `-D fan=true`.
2. **A manual, panel-mount, recessed on/off switch** on the case wall, in series with the fan's +5 V
   lead, so the fan can be switched by hand from outside without opening the case, without risk of
   accidental toggling in a 1 m drop or on a dark stage.

This plan does **not** touch the encoders' Mini-DIN-8 fan-power path (`pro-convert-hdmi-plus`,
`pro-convert-sdi-plus`) beyond adding the same external switch — those two SKUs stay **blocked on
M12** (`architecture.md` §11 R23) for anything else, unchanged by this ticket.

---

## 1. Switch selection

Three candidates researched. All are electromechanical contacts with **no published DC rating** at
5 V/≤0.05 A (every switch datasheet found quotes only an AC figure) — the exact same open question
`poe-splitter-verification.md` §4 already recorded for the KSD9700 thermoswitch. This is **not**
disqualifying (0.05 A is trivial next to any of these contacts' AC ratings, and dry-circuit
switching lore is exactly that — lore, not a confirmed defect), but it is the same class of risk and
should get the same treatment: cheap enough to just buy and bench-test, not worth blocking on.

| # | Part | Cutout | Panel thickness range | Body depth behind panel | Rating | Colour | Price class | Source (EU) |
|---|---|---|---|---|---|---|---|---|
| **1 (recommended)** | **MTS-101** (SPST ON-OFF mini toggle — see note below on why not MTS-102) | round **⌀6.4 mm** (`assumed`, generic mini-toggle bushing figure, LCSC/Finglai datasheets; ±0.2 mm typical) | **`assumed` 0.8–3.2 mm** (1/4-40NS threaded bushing + nut, generic mini-toggle convention — no MTS-series datasheet states a clamp range explicitly) | **`assumed` ≈13 mm** (SMTS-102 datasheet analogue, same manufacturer family, "13.2" dimension on the mechanical drawing; MTS-102's own drawing exists but its numeric callouts were not legibly extractable this pass — verify against the physical part) | 6 A @125 VAC / 3 A @250 VAC (no DC figure published) | Black (Bakelite/PBT body, both offered) | €1–2 each (commodity) | [Finglai MTS-102 datasheet](https://www.finglai.com/products/switches/toggle-switches/DIA6-MTS-1/MTS-102.html) (mechanical family reference); stocked generically at reichelt.com / tme.eu / conrad.de under "MTS-101"/"MTS-102" — **exact catalogue page not confirmed this pass, verify at order time** |
| 2 | **KCD11-101** mini rectangular rocker | **14 × 8.5 mm** | not stated | **17.5 mm** | 125 VAC/6 A, 250 VAC/3 A (no DC) | Black | €0.50 | [ampul.eu (Šumperk, CZ)](https://ampul.eu/en/rocker-switches/3868-mini-rectangular-rocker-switch-kcd11-101-black-250) |
| 3 | **SCI-PARTS WS R13-112 A-SW** (R13-112A8-02-BB-2) sealed IP65 round rocker | round **⌀20.2 mm** snap-in | not stated | **22.3 mm** | 10(4) A @250 VAC **and 10 A @24 VDC (a real DC rating)** | Black | €2.05 | [reichelt.com](https://www.reichelt.com/de/en/shop/product/rocker_switch_round_ip65_1_x_on_-_off_black_black-105455) |

**Recommendation: MTS-101.** Reasoning:

- **Fit is the deciding factor, not electrical rating.** §2 below computes the actual clear Y-band
  next to the fan aperture on the +X wall: **≈13 mm on the Plus family, ≈10 mm margin-checked on the
  compact family** (the `base_fan` smoke-test golden forces `fan=true`+switch on a compact SKU too,
  so this is a real render-time constraint, not a cosmetic one). Candidate 3's 20.2 mm round cutout
  does not fit that band at all — using it would require deliberately offsetting the `fan_y` shell
  parameter away from its documented default, a separate decision this ticket does not authorize (see
  §2, PLAN-ASSUMPTION 3). Candidate 1's 6.4 mm hole (≈8 mm keep-out with nut) clears both bands with
  ≥3 mm margin by construction (§2); candidate 2's 8.5 mm short axis is workable but leaves
  meaningfully less margin on the compact band with no upside (its 14 mm long axis buys nothing once
  the recess pocket already provides the flush, drop-safe profile a toggle needs).
- **A toggle needs the recess pocket for drop-safety exactly as much as a rocker does** — the "must
  not toggle by accident" requirement is met by the pocket geometry (§2), not by the switch's own
  shape, so there is no accidental-toggle penalty for choosing the toggle.
- **The ticket's own research target was "MTS-102" (SPDT ON-ON).** MTS-101 is the SPST ON-OFF sibling
  in the *same* mechanical family (identical bushing/cutout/depth) and is the electrically correct
  part for a simple series on/off switch — MTS-102 is a three-terminal ON-ON selector that would work
  wired as ON-OFF (common + one throw, other throw unused) but is a needless complication. Order
  MTS-101, not MTS-102.
- Candidate 3 remains recorded as the go-to if the team later revisits `fan_y` or wants the only
  candidate with a genuine DC rating and IP65 ingress protection (e.g. if M8-style bench testing ever
  turns up a real dry-circuit failure on the cheaper parts) — **do not implement it in this pass.**

---

## 2. Placement — the +X end wall, beside the ⌀38 fan aperture

### 2.1 What's already on that wall

- **Fan aperture**: ⌀38 mm at `(x = L/2, y = fan_y, z = z_conn_c = 25.5)`, `fan_y` defaults to
  `y_dev_c` (`layout-patch-wall.md` §5, `lib/mcc/layout.scad:404` `fan_pos = [L/2, fan_y, z_conn_c]`).
  The fan's **reservation footprint** (its own 40×40 mm frame, `MCC_FANS["NF-A4x10"].frame`) occupies
  `y ∈ [fan_y−20, fan_y+20]`, `z ∈ [z_conn_c−20, z_conn_c+20] = [5.5, 45.5]` — i.e. almost the full
  wall height, which is why the switch must go **beside** the fan in Y, not above/below it in Z (there
  is no Z escape).
- **A far-wall-side lid-fastener boss + gusset**, on every current SKU (`L > MCC_LID_SPAN_MAX` ⇒
  `n_fast = 6`, `lib/mcc/layout.scad:420-446`). The `(+X, −Y)` corner boss sits at
  `x = L/2 − MCC_FASTENER_INSET (10)`, `y = −(W/2 − 10)`; its gusset web
  (`_mcc_gusset_web()`, `lib/mcc/shell.scad:56-85`) resolves to the **+X** wall (tie broken toward
  `d_xpos`, checked first) and is a **`MCC_WALL` (3 mm) wide strip in Y**, centred on that same
  `y = −(W/2−10)`, running in X from the boss out to the wall.
- **End-zone free depth (`ez_pos`)**: not actually a constraint here — the device's own X extent ends
  tens of mm short of the +X wall (≈27–40 mm clear on every SKU below), so a ≤13 mm-deep switch body
  never reaches the device or its end-face cable envelopes. This is a straight-line X check, not a
  formula to re-derive: confirm at implementation time by comparing `x_dev_hi` to
  `L/2 − MCC_WALL − switch_depth` for the SKU in hand.

### 2.2 Placement formula

Put the switch **on the far-wall (−Y) side of the fan** (the duct side — cable routing toward the
patch-wall slots runs on the +Y side of the device, so −Y is the less-obstructed choice), at the same
Z as the fan/connector centreline:

```
switch_y = fan_y − (MCC_FANS["NF-A4x10"].frame[1]/2 + MCC_FAN_SWITCH.clr + MCC_FAN_SWITCH.keepout_d/2)
switch_z = z_conn_c                                    // = 25.5, universal
switch_pos = [L/2, switch_y, switch_z]
```

`MCC_FAN_SWITCH.clr = 3.0` (new constant, `assumed`) is the minimum Y clearance to the fan's
reservation edge — chosen, not derived, mirroring this repo's existing small-clearance constants
(`MCC_GAP_DEV`, `MCC_SIDE_BOLT_PAD_T`). By construction the gap between the switch's keep-out edge and
the fan's reservation edge is **exactly** `MCC_FAN_SWITCH.clr` on every SKU — T1-38 (§4) exists to
catch a *future* change to the fan spec or the formula, not because this pass leaves any slack to
verify at random.

### 2.3 Worked numbers (exact, computed from `mcc_case_layout()`'s own formulas)

| SKU | family | `W` | `fan_y` = `y_dev_c` | `switch_y` | `switch_z` | Far-wall-side gusset `y` | Clearance to gusset | Clearance to fan edge |
|---|---|---|---|---|---|---|---|---|
| `pro-convert-for-ndi-to-hdmi-4k` | plus | 166.35 | −30.825 | **−57.825** | 25.5 | −73.175 | 6.65 mm | 3.0 mm (by construction) |
| `pro-convert-hdmi-plus` | plus | 166.35 | −30.825 | **−57.825** | 25.5 | −73.175 | 6.65 mm | 3.0 mm |
| `pro-convert-sdi-plus` | plus | 165.30 | −30.300 | **−57.300** | 25.5 | −72.650 | 6.65 mm | 3.0 mm |
| `pro-convert-for-ndi-to-hdmi` (`base_fan` golden, compact) | compact | 159.85 | −30.825 | **−57.825** | 25.5 | −69.925 | 6.65 mm | 3.0 mm |

("Clearance to gusset" = distance from the switch keep-out's inner edge, `switch_y + keepout_d/2`, to
the gusset strip's near edge, `gusset_y − MCC_WALL/2`; positive on every row, tightest case still 6.65
mm — comfortably clear, no automated assert needed for this one per §4, but the head-on +X elevation
render is the acceptance check per §5.)

`hdmi-plus`/`hdmi-4k` share identical numbers because both are governed by the same
`max_bay_depth = 75.65` (an `NAHDMI-W-B` bay); `sdi-plus` is governed by `NBB75DFGB`'s smaller 74.6,
which shifts `W` (and therefore `fan_y`/`switch_y`) by ≈1 mm. **Do not hand-copy these numbers into
`case.scad` files** — they fall out of the formula in §2.2 automatically once `MCC_FAN_SWITCH` and the
`switch_pos` field exist in `mcc_case_layout()`; this table is for review/verification only.

### 2.4 Recess pocket and panel thickness

A **1.0 mm deep recess pocket** (new constant `MCC_FAN_SWITCH.recess_t = 1.0`, `assumed`) cut into the
wall's **outer** face over the switch's keep-out footprint, so the toggle's lever sits below the
surrounding wall surface (drop safety, no accidental toggling on stage). This leaves
`MCC_WALL − recess_t = 3.0 − 1.0 = 2.0 mm` of residual wall material at the pocket floor — chosen
deliberately to land exactly on this repo's own "2.0 mm minimum material" precedent
(`MCC_APERTURE_LIP_WEB_MIN`, `MCC_PANEL_SEAT_T`), and to fall inside MTS-101's assumed 0.8–3.2 mm
clamp range (`MCC_FAN_SWITCH.panel_t_min`/`panel_t_max`) with room either way. T1-39 (§4) asserts both
facts numerically so a future change to either constant fails loudly instead of silently.

The switch's through-hole (⌀`hole_d + MCC_HOLE_COMP`) still runs the *entire* wall thickness (bushing
must reach a nut on the inside); only the **pocket** — sized to `keepout_d + 2·MCC_CLR_SLIDE` — stops
`recess_t` short of the true outer face.

---

## 3. Wiring

The switch goes **in series in the +5 V lead** of the fan's power source, cut/stripped/soldered/
heat-shrunk. Two documented variants — **leave the choice to the user, default (a) in the BOM**:

- **(a) Manual switch only (default).** `5 V source → manual switch → fan`. Simplest, fully
  user-controllable, no dependency on the KSD9700's unverified DC behaviour.
- **(b) Manual master switch + KSD9700 in series.** `5 V source → manual switch → KSD9700 → fan`. The
  switch is a master override (can force the fan off regardless of temperature); the KSD9700 still
  regulates when the fan actually runs while the switch is on. Order of the two components on the lead
  doesn't matter electrically. Document this as an explicit user option, not a silent default — it
  doubles down on the KSD9700's own already-flagged DC-switching risk (`poe-splitter-verification.md`
  §4) stacked with the manual switch's identical risk, which is a reason to keep it optional, not to
  hide it.

Per-family lead:

- **Decoders** (`pro-convert-for-ndi-to-hdmi-4k` today; the other two decoders if built with
  `-D fan=true`): cut the **KUOQIY USB-A → 3/4-pin cable** between its USB-A end and its fan plug,
  insert the switch (and optionally the KSD9700) in the +5 V (red) conductor only, heat-shrink both
  splices. The cable's 3/4-pin end plugs straight into the NF-A4x10 5V's native 3-pin connector — no
  OmniJoin/NA-AC2 adaptor (confirmed by the ticket; also update `fans.md`, §6 below).
- **Encoders** (`pro-convert-hdmi-plus`, `pro-convert-sdi-plus`): unchanged lead (cut-down Mini-DIN-8
  pigtail → pin 8 VCC / pin 4 GND, per the existing BOM row) — insert the switch in the same +5 V
  conductor, same two variants.

---

## 4. Library design

### 4.1 New file: `lib/mcc/switch.scad` (L1 provider)

Mirrors `lib/mcc/fan.scad`'s structure and Z-axis convention ("wall spans local Z ∈ [0, wall_t]",
same comment block fan.scad carries). `include <BOSL2/std.scad>`, `include <constants.scad>`,
`use <util.scad>`. Two modules, both geometry-only (no `dev`/`cfg` — the caller translates/rotates to
world position exactly as `shell.scad` already does for `mcc_fan_cutout()` in `vents.scad`):

- **`mcc_switch_cutout(spec = MCC_FAN_SWITCH, wall_t = MCC_WALL)`** — negative (subtractive) solid,
  centred at local `(0,0)` with local Z the wall-normal axis:
  1. A through-hole cylinder, `d = struct_val(spec,"hole_d") + MCC_HOLE_COMP`, spanning the *entire*
     `wall_t` (local Z ∈ `[0, wall_t]` + `MCC_EPS` overshoot both ends, `cyl(..., circum = true,
     $fn = 64)`, matching `neutrik.scad`'s hole-comp/circum convention).
  2. A recess-pocket cylinder, `d = struct_val(spec,"keepout_d") + 2·MCC_CLR_SLIDE`, `h =
     struct_val(spec,"recess_t")`, positioned at the **outer** face end of the wall (local Z ∈
     `[wall_t − recess_t, wall_t]` + `MCC_EPS` overshoot at the outer end only — do not overshoot past
     `wall_t − recess_t` inward, that's the residual-wall floor T1-39 checks).
  3. **T1-39 asserts, evaluated here** (pure numbers, no geometry dependency — this is why they live in
     this module rather than in `layout.scad`, matching how `_mcc_patch_wall_rabbet()` asserts its own
     residual-lip numbers locally in `shell.scad` rather than in the pure layout solver):
     ```
     residual = wall_t - struct_val(spec, "recess_t");
     assert(residual >= 2.0,
         str("mcc: T1-39 fan-switch recess residual wall ", residual, " below the 2.0 mm minimum"));
     assert(residual >= struct_val(spec, "panel_t_min") - MCC_EPS
         && residual <= struct_val(spec, "panel_t_max") + MCC_EPS,
         str("mcc: T1-39 fan-switch residual panel thickness ", residual,
             " outside the switch clamp range [", struct_val(spec, "panel_t_min"), ",",
             struct_val(spec, "panel_t_max"), "]"));
     ```
  Return `union() { <through-hole> <pocket> }` as the subtractive solid (both cuts are positive-space
  removals, unioned before the caller differences them out — same pattern as `mcc_fan_cutout()`'s
  `union()` of its 4 mounting holes + the round opening).

- **`mcc_switch_ghost(spec = MCC_FAN_SWITCH)`** — visual-only (`%`-modifier'd by the caller, belt-2 of
  the two-belt ghost rule, `MCC_SHOW_GHOST` gated by the caller same as `ghost.scad`), a solid box/rod
  of length `struct_val(spec,"depth")` extending from local Z=0 inward (behind the panel), footprint
  `struct_val(spec,"keepout_d")` square — purely for the `case.scad` `"assembly"` preview branch, same
  spirit as `_mcc_case_at_device()`'s plug-envelope preview in `models/**/case.scad`. Not exported by
  `build.py`, not asserted — a nice-to-have, do not block the ticket on it if time is short.

- **Pure function `mcc_fan_switch_enabled(cfg)`** (small enough to live alongside the two modules in
  this file, same as `fan.scad` mixes `mcc_fan_spec()` with its cutout modules):
  ```
  function mcc_fan_switch_enabled(cfg) =
      let(v = struct_val(cfg, "fan_switch"))
      is_undef(v) ? struct_val(cfg, "fan") : v;
  ```

### 4.2 New constant: `MCC_FAN_SWITCH` (`lib/mcc/constants.scad`, new "Fan switch" subsection under "Fans")

```
MCC_FAN_SWITCH = [
    ["hole_d",       6.4],  // panel mounting hole diameter, mm. assumed -- MTS-101/102 generic mini-
                             // toggle bushing (LCSC/Finglai datasheets), +-0.2 typical.
    ["keepout_d",    8.0],  // nut-across-flats + clearance keep-out diameter, mm. assumed.
    ["depth",       13.0],  // body length behind the panel, mm. assumed -- SMTS-102 datasheet analogue
                             // (same manufacturer family); MTS-101/102's own datasheet exists but its
                             // numeric callouts were not legibly extractable this pass -- verify.
    ["recess_t",     1.0],  // outer-face recess pocket depth, mm. Chosen so MCC_WALL - recess_t = 2.0,
                             // this repo's own minimum-material precedent (MCC_PANEL_SEAT_T,
                             // MCC_APERTURE_LIP_WEB_MIN).
    ["panel_t_min",  0.8],  // assumed switch panel-clamp range minimum, mm.
    ["panel_t_max",  3.2],  // assumed switch panel-clamp range maximum, mm.
    ["clr",          3.0],  // minimum Y clearance to the fan reservation edge, mm. assumed -- mirrors
                             // MCC_GAP_DEV/MCC_SIDE_BOLT_PAD_T's own small-clearance convention.
    ["confidence", "assumed"],
];
```

### 4.3 `lib/mcc/layout.scad` — `mcc_case_layout()` additions

Add, immediately after the existing `fan_pos`/`fan_y` `let()` bindings (`layout.scad:401-404`):

```
fan_frame  = struct_val(MCC_FANS[search(["NF-A4x10"], MCC_FANS)[0]][1], "frame"),
switch_y   = fan_y - (fan_frame[1]/2 + struct_val(MCC_FAN_SWITCH, "clr")
                       + struct_val(MCC_FAN_SWITCH, "keepout_d")/2),
switch_pos = [L / 2, switch_y, z_conn_c],
```

Add `["switch_pos", switch_pos]` to the returned struct (alongside the existing `["fan_pos", fan_pos]`
row, `layout.scad:484`).

Add **T1-38** to the existing Tier-1 assert chain (after the `let()`, alongside T1-06 .. T1-28,
`layout.scad:452-474`):

```
assert(fan_y - fan_frame[1] / 2 - (switch_y + struct_val(MCC_FAN_SWITCH, "keepout_d") / 2) >= -MCC_EPS,
    str("mcc: T1-38 fan/switch Y clearance fails on \"", mcc_dev_slug(dev), "\""))
```

(This is satisfied by construction today — §2.2's formula guarantees a positive gap on every SKU — so
it functions as a regression guard against a future change to the fan spec or the placement formula,
the same role T1-34a plays for the aperture shape.)

`layout.scad` already `include`s `constants.scad` (so `MCC_FANS`/`MCC_FAN_SWITCH` are directly
visible) and stays within its "functions only, no L1 geometry provider" contract — it reads constants,
not `switch.scad`'s modules.

### 4.4 `lib/mcc/shell.scad` — call site

`use <switch.scad>` alongside the file's existing L1 `use` list (`fan.scad`, `fasteners.scad`, etc.,
`shell.scad:13-24`).

In `mcc_shell_base()`, immediately after the existing fan-cutout conditional
(`shell.scad:434-435`):

```
if (struct_val(cfg, "fan") == true)
    mcc_vents(dev, cfg, [1, 0, 0]);

if (mcc_fan_switch_enabled(cfg)) {
    switch_pos = struct_val(l, "switch_pos");
    translate([switch_pos[0], switch_pos[1], switch_pos[2]])
        rotate([0, 90, 0])
            mcc_switch_cutout(wall_t = MCC_WALL);
}
```

(`rotate([0,90,0])` matches `vents.scad`'s own fan-cutout placement exactly — local Z → world X, so
the module's wall-normal axis lands on the +X wall's outward normal; `l` is already in scope as
`mcc_shell_base()`'s own `l = mcc_case_layout(dev, cfg)`, `shell.scad:347`.)

### 4.5 `cfg.fan_switch` contract

Document in every `models/**/case.scad`'s "Documented cfg keys" comment block (same place `"fan"`,
`"splitter"`, `"fan_y"` are documented today):

```
//   "fan_switch" (bool, optional, default = cfg's own "fan" value) -- draws the live manual switch
//               cutout on the +X wall beside the fan aperture when true. Independent flag so a
//               future variant could ship the fan without the switch (or vice versa, though a
//               switch with no fan makes no sense) without a library change.
```

No `case.scad` file needs an explicit `["fan_switch", ...]` row unless it wants to *override* the
default — `mcc_fan_switch_enabled(cfg)` already falls back to `cfg`'s `"fan"` value when the key is
absent, so every existing `variant = [...]` list keeps working unchanged.

### 4.6 Asserts summary

| ID | What | Where | Kind |
|---|---|---|---|
| T1-38 | Switch keep-out does not overlap the fan's reservation footprint in Y, ≥0 mm gap | `lib/mcc/layout.scad`, `mcc_case_layout()` | pure numbers, per-SKU |
| T1-39 | Recess-pocket residual wall ≥2.0 mm **and** within the switch's clamp range | `lib/mcc/switch.scad`, `mcc_switch_cutout()` | pure numbers, constants-only (evaluated once per render, not SKU-dependent) |

### 4.7 Golden impact

`build.py golden --update` will touch:

- `tests/golden/pro-convert-for-ndi-to-hdmi-4k.base.json`
- `tests/golden/pro-convert-hdmi-plus.base.json`
- `tests/golden/pro-convert-sdi-plus.base.json`
- `tests/golden/pro-convert-for-ndi-to-hdmi.base_fan.json`

No `.lid.json` or `.panel.json` file is affected (the switch is a base-shell-only feature, like the
fan). Expect a small, real volume delta on each (a through-hole + a shallow pocket cut from the +X
wall) — update the goldens and sanity-check the delta is small and in the removing-material direction,
same diligence `layout-patch-wall.md` §16.6 already modelled for the `DBA-BL-B` blank change.

---

## 5. BOM (`BOM.md`)

### 5.1 Common "Fan power and thermal switch" section (`BOM.md:83-98`)

- **Replace** the `USB-A-to-2-pin-fan-lead power cable` row (`BOM.md:95`) with:

  | Item | Part number | Qty | Notes | Source |
  |---|---|---|---|---|
  | KUOQIY USB-A → 3/4-pin PWM fan adapter cable | KUOQIY, 5-pack (ASIN B0D1C36WKB) | 1 (of 5) | **Decoders only.** Plugs straight into the NF-A4x10 5V's native 3-pin connector — no OmniJoin/NA-AC2 adaptor needed. Runs from the device's external `usb_host` port, through the DBA-BL-B-blanked slot, through the manual switch (and optionally the thermoswitch), to the fan — rating under PoE is `unknown` and needs measurement M9 before relying on it | `.claude/knowledge/architecture.md` §5 table row "Decoders ... R21, M9"; issue #32 (cable spec, amazon.nl, fetched 2026-09-09 — not independently re-verified this pass, amazon fetches return HTTP 500) |

- **Amend** the `OmniJoin adaptor set / NA-AC2 3:2-pin adaptor cable` row (`BOM.md:98`): append
  *"— **not needed for the KUOQIY cable path** (its 3/4-pin plug mates directly with the NF-A4x10 5V's
  own connector); this row now documents only the bundled-but-unused accessory, kept so it isn't
  mistaken for missing hardware."*
- **Amend** the KSD9700 row's notes (`BOM.md:93`): *"wired in series in the fan's +5V lead"* →
  *"wired in series in the fan's +5V lead, downstream of the manual switch below (variant (b) only —
  see the manual switch row)"*.
- **Add** a new row, immediately after the KSD9700 row:

  | Item | Part number | Qty | Notes | Source |
  |---|---|---|---|---|
  | MTS-101 SPST ON-OFF mini toggle switch, black, panel-mount | MTS-101 (or equivalent, ⌀6.4 mm mounting hole) | 1 | Wired in series in the fan's +5V lead — **default: switch only (variant a)**; optionally add the KSD9700 above in series for variant (b), master switch + thermostat. Recessed 1.0 mm into the +X wall for drop safety, beside the fan aperture (`lib/mcc/switch.scad`, `MCC_FAN_SWITCH`). DC switching at 5V/≤0.05A is unverified, same open question as the KSD9700 above — bench-test before relying on it | This plan §1; `.claude/knowledge/architecture.md` §5; `knowledge/components/switches.md` (new) |

### 5.2 Per-SKU: `pro-convert-for-ndi-to-hdmi-4k` (`BOM.md:261-291`)

- **Replace** the `USB-A-to-2-pin-fan-lead power cable` row (`BOM.md:282`) with the KUOQIY cable row
  from §5.1 (same text, `Qty 1`).
- **Add** the MTS-101 switch row from §5.1 immediately after the KSD9700 row (`BOM.md:281`).

### 5.3 Per-SKU: `pro-convert-hdmi-plus` / `pro-convert-sdi-plus` (`BOM.md:195-240`)

Both already carry the Mini-DIN-8 pigtail + KSD9700 rows unchanged (encoders use the internal
Mini-DIN-8 lead, not the KUOQIY cable). **Add** the MTS-101 switch row from §5.1 immediately after
each SKU's own KSD9700 row (`BOM.md:211` for `hdmi-plus`, `BOM.md:236` for `sdi-plus`).

### 5.4 Other decoders (`pro-convert-for-ndi-to-hdmi`, `pro-convert-for-ndi-to-sdi`)

Both are `fan = false` by default — no change to their own per-SKU tables. Their existing pointer to
the common "Fan power and thermal switch" section (`BOM.md:258-259`, `:309-310`) now correctly picks
up the KUOQIY cable + MTS-101 switch rows too for a `-D fan=true` build, with no separate edit needed.

---

## 6. Knowledge base updates

### 6.1 New page: `knowledge/components/switches.md`

Structure to match `knowledge/components/fans.md` (sourced, cited, `assumed`-flagged where
unverified). Contents:

- MTS-101/MTS-102 mechanical family (bushing, cutout, ratings) — cite the Finglai datasheet and flag
  the depth/panel-thickness figures `assumed` per §1's table.
- KCD11-101 as the recorded alternative (ampul.eu, cutout, depth, price).
- SCI-PARTS WS R13-112 A-SW as the recorded IP65/DC-rated alternative, with an explicit note that it
  does **not** fit the current `fan_y` placement band (§2) without a separate `fan_y` decision.
- A short "DC switching at low current is unverified for all three" paragraph, cross-referencing
  `poe-splitter-verification.md` §4's identical KSD9700 finding rather than duplicating the reasoning.

### 6.2 `knowledge/components/fans.md`

Add a short note (near the NF-A4x10 5V table, `fans.md:13-24`, or in "Accessories"): the KUOQIY 3/4-pin
fan-adapter cable's fan-side connector mates directly with the NF-A4x10 5V's native 3-pin connector —
confirmed by the issue, no OmniJoin/NA-AC2 needed for that specific cable (contrast with the general
"generic third-party adaptor cables... not independently verified" caveat already at `fans.md:154-159`,
which this KUOQIY note narrows for this one specific product).

### 6.3 `.claude/knowledge/architecture.md` and `layout-patch-wall.md`

Once implemented, record the new provider (`switch.scad`) in `architecture.md` §3's layer diagram
(alongside `fan.scad`, `poe_splitter.scad` at L1) and add a short entry to `layout-patch-wall.md` §5
("Fan bay, PoE-splitter bay, vents") describing the switch placement formula and citing this plan —
follow this repo's own convention of recording *where* a decision landed, not just *that* it landed.
This plan does not pre-write that prose; whoever implements should keep it terse and point back here
rather than duplicating §2's derivation.

---

## 7. Ordered implementation steps

1. **Architect gate** (Team Charter step 2) — validate the `MCC_FAN_SWITCH` struct shape, the
   `switch.scad` module split (`mcc_switch_cutout`/`mcc_switch_ghost`), and the §2.2 placement formula
   before any code lands.
2. `lib/mcc/constants.scad` — add the `MCC_FAN_SWITCH` struct (§4.2), in a new "Fan switch"
   subsection immediately after the existing "Fans" section (`constants.scad:528-552`).
3. `lib/mcc/switch.scad` — new file, `mcc_switch_cutout()`, `mcc_switch_ghost()`,
   `mcc_fan_switch_enabled()` (§4.1).
4. `lib/mcc/layout.scad` — add `switch_pos`/`switch_y` to `mcc_case_layout()`'s `let()` and returned
   struct, add the T1-38 assert (§4.3).
5. `lib/mcc/shell.scad` — `use <switch.scad>`, add the conditional cutout call after the existing fan
   cutout in `mcc_shell_base()` (§4.4).
6. Document `"fan_switch"` in every `models/**/case.scad`'s cfg-keys comment block (§4.5) — no
   functional edit needed unless a specific SKU wants to override the default.
7. `python scripts/build.py render pro-convert-for-ndi-to-hdmi-4k pro-convert-hdmi-plus
   pro-convert-sdi-plus pro-convert-for-ndi-to-hdmi --backend=Manifold` — confirm T1-38/T1-39 fire
   correctly (no failures expected per §2.3/§2.4's worked numbers) and the switch geometry looks right.
8. `python scripts/build.py check --all` then `python scripts/build.py golden --update` — confirm
   watertight/single-shell, then update the 4 goldens listed in §4.7; sanity-check the volume deltas
   are small and material-removing.
9. Render the mandatory **head-on +X elevation** for at least `pro-convert-for-ndi-to-hdmi-4k`:
   `openscad --backend=Manifold -D 'part="base"' --camera=400,0,25,0,0,0 --projection=o --imgsize=1200,1200
   -o preview-x.png models/pro-convert-for-ndi-to-hdmi-4k/case.scad` — confirm visually: the fan
   aperture and the switch recess sit side by side with daylight between them and between the switch
   and the far-wall gusset, matching §2.3's table. Repeat for `pro-convert-hdmi-plus`/`sdi-plus` if time
   allows (their numbers are near-identical to `hdmi-4k`'s).
10. `python scripts/build.py smoke` (confirms `tests/test_shell.scad`'s `VARIANT_FAN` branch still
    renders — it does not need editing, since `cfg.fan_switch` defaults from `cfg.fan` automatically,
    but the smoke test now implicitly exercises the switch cutout too).
11. `BOM.md` edits per §5.
12. `knowledge/components/switches.md` (new) + `knowledge/components/fans.md` note per §6.
13. `python scripts/build.py all` — full green run.
14. Update `.claude/knowledge/decision-log.md` with the switch-selection rationale (MTS-101 over
    MTS-102/KCD11/R13-112A, and why) — decision history goes there and in this plan/ticket, never as
    ticket-referencing code comments (per the researcher's own contract — do not add "// issue #32"
    or "// per the ticket" comments anywhere in `lib/mcc/switch.scad` or the edited files).
15. `architecture.md`/`layout-patch-wall.md` record update per §6.3.

---

## 8. PLAN-ASSUMPTIONs (flag to the user/architect, do not silently resolve differently)

1. **PLAN-ASSUMPTION 1 — switch choice.** Recommending **MTS-101** (not the ticket's own researched
   "MTS-102", which is electrically the wrong 3-terminal part for a simple on/off — see §1). If the
   user has a specific supplier/part already in hand, swap `MCC_FAN_SWITCH`'s figures for the measured
   ones rather than the `assumed` placeholders here.
2. **PLAN-ASSUMPTION 2 — `MCC_FAN_SWITCH.depth`/`panel_t_min`/`panel_t_max` are `assumed`,** not
   measured (§1's table; the MTS-101/102 datasheet's own numeric callouts were not legibly
   extractable from the sources reached this pass). Cheap enough to just buy the part and correct these
   three figures before or shortly after the first print, same spirit as this repo's existing M-number
   physical-measurement backlog — consider adding an **M14** entry to `architecture.md` §11's
   measurement list for "switch body depth + panel clamp range, bench-verified" rather than leaving it
   silently `assumed` forever.
3. **PLAN-ASSUMPTION 3 — the IP65 `R13-112A` candidate is recorded but not placed.** It does not fit
   the ≈10–13 mm Y-band computed in §2 without moving `fan_y` off its documented default
   (`layout-patch-wall.md` §5, R20: "parameterise now, decide by measurement; do not silently move the
   default"). If the team later wants that switch specifically, treat it as a separate `fan_y`-override
   decision requiring its own architect sign-off, not something this plan's formula should quietly
   accommodate by picking a different `clr`/`keepout_d`.
4. **PLAN-ASSUMPTION 4 — variant (a) vs (b) wiring default.** This plan defaults the BOM to (a) manual
   switch only, per the ticket's own instruction. If the user actually wants (b) as the shipped default
   (master switch + KSD9700), only §5's BOM default row needs to flip — no geometry/library change
   either way, since both variants use the identical switch cutout.
5. **PLAN-ASSUMPTION 5 — no `switch.scad` reservation-volume module.** Unlike the fan and splitter,
   this plan does **not** add a `mcc_switch_envelope()`-style unconditional reservation (`architecture.md`
   §6's reservation rule) because the switch is *always* gated behind `fan`/`fan_switch`, which is
   already unconditionally reserved via the fan bay itself — a switch with no fan makes no product
   sense, so there is no "add the switch later without moving anything" retrofit scenario to protect
   against, unlike the fan/splitter bays which are deliberately reserved even when disabled. Flag if
   the architect disagrees.
6. **Pre-existing gap noticed, out of scope for this ticket:** `mcc_fan_envelope()` (`lib/mcc/fan.scad:39`)
   is defined but **never called** anywhere in `shell.scad` — the fan bay's *depth* reservation
   (`architecture.md` §6 "the reservation rule... even when fan=false") is not actually wired up today,
   only the fan's live cutout is. This plan's placement math in §2 does not depend on that reservation
   being enforced (the switch sits beside the fan, not behind it), so it is safe to proceed without
   fixing this — but it is worth a separate ticket since it means `fan=false` SKUs do not actually
   protect the fan bay's volume from future connector/cradle changes as the architecture doc claims
   they do.
