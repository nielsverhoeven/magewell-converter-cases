# Panel switches for the external manual fan switch (issue #32)

Reference data for selecting a panel-mount, manually-operated on/off switch for the case's +X end
wall, wired in series in the fan's +5 V lead (`.claude/knowledge/architecture.md` §5 "Fan switch";
`.claude/knowledge/layout-patch-wall.md` §5/§18, D-18). Three candidates researched; only the first
is placed in the current design (`MCC_SWITCHES`/`MCC_SWITCH_DEFAULT`, `lib/mcc/constants.scad`) —
the other two are recorded so a future revisit does not re-derive this research from scratch.

All three switch datasheets found quote only an **AC** contact rating; none publish a DC rating at
5 V/≤0.05 A (the fan's own current draw). This is the same open question already recorded for the
KSD9700 thermal switch (`knowledge/components/poe-splitter-verification.md` §4) — not disqualifying
(0.05 A is trivial next to any of these contacts' AC ratings, and "dry-circuit switching is
unreliable at low current" is lore, not a confirmed defect for this specific hardware), but the same
class of risk and the same treatment: cheap enough to buy and bench-test, not worth blocking on.

---

## 1. MTS-101 (SPST ON-OFF mini toggle) — placed, `MCC_SWITCH_DEFAULT`

The SPST ON-OFF sibling of the mini-toggle family most commonly sold as "MTS-101"/"MTS-102"
(identical mechanical bushing/cutout/depth across the family) — generic commodity part, multiple
manufacturers (Finglai and others use this designation for the same mechanical footprint).

| Property | Value | Confidence | Source |
|---|---|---|---|
| Cutout | round, ⌀6.4 mm | `assumed` | generic 1/4-40NS mini-toggle bushing convention (LCSC/Finglai-class datasheets); ±0.2 mm typical for this switch class |
| Panel-thickness clamp range | 0.8–3.2 mm | `assumed` | generic 1/4-40NS threaded-bushing + nut convention — no MTS-series datasheet reached this pass states a clamp range explicitly |
| Nut, across flats | 8.0 mm | `assumed` | generic 1/4-40NS hex nut convention; circumscribed diameter = `8.0 / cos(30°) ≈ 9.24 mm` (`lib/mcc/constants.scad` `MCC_SWITCHES["MTS-101"].nut_d`) |
| Body depth behind panel | 13.0 mm | `assumed` | SMTS-102 datasheet analogue (same manufacturer family, "13.2" mechanical-drawing dimension); MTS-101/102's own datasheet exists but its numeric callouts were not legibly extractable this pass |
| Actuator height proud of panel (lever, ON position) | ~10 mm | `assumed` | generic mini-toggle lever length; drives `recess_t` (T1-44a) — this is the single most load-bearing unmeasured figure, since it sets how deep the recess well must be |
| Rating | 6 A @125 VAC / 3 A @250 VAC | sourced (AC only) | [Finglai MTS-102 datasheet](https://www.finglai.com/products/switches/toggle-switches/DIA6-MTS-1/MTS-102.html) (mechanical-family reference; MTS-101 is its SPST sibling, same bushing/cutout/depth) |
| Colour | black (Bakelite/PBT body, both offered) | sourced | as above |
| Price class | €1–2 each (commodity) | sourced | as above; stocked generically at reichelt.com / tme.eu / conrad.de under "MTS-101"/"MTS-102" — **exact catalogue page not confirmed this pass, verify at order time** |

**Why placed over the ticket's own researched MTS-102.** MTS-102 is a three-terminal SPDT ON-ON
selector switch (common + two throws); wiring it as an ON-OFF switch (common + one throw, other
throw left unused) works electrically but is a needless complication for a simple series on/off
function. MTS-101 is the SPST ON-OFF sibling in the identical mechanical family — same
cutout/bushing/depth — and is the electrically correct part. Order MTS-101, not MTS-102.

**M17 (architecture.md §11 R29 / §12) is BLOCKING before the first full-size print.** Buy one
(≈€1–2) and measure: actuator height proud of the panel, mounting-hole diameter, nut across-flats
(⇒ circumscribed diameter), body depth behind the panel, and the panel-clamp thickness range. All
five are load-bearing: the actuator height sets `recess_t` (T1-44a), the nut diameter sets `pad_d`
and therefore whether the part fits the +X band at all (T1-43), and the clamp range decides whether
the computed residual panel thickness is legal. The Plus family's feasible `switch_y` window is only
~3.2 mm wide (`layout-patch-wall.md` §18.2) — this is not a figure to carry through a print unmeasured.

## 2. KCD11-101 (mini rectangular rocker) — recorded alternative, rejected for #32

| Property | Value | Confidence | Source |
|---|---|---|---|
| Cutout | 14 × 8.5 mm rectangular snap-in | sourced | [ampul.eu (Šumperk, CZ)](https://ampul.eu/en/rocker-switches/3868-mini-rectangular-rocker-switch-kcd11-101-black-250) |
| Panel-thickness clamp range | not stated | `unknown` | as above |
| Body depth behind panel | 17.5 mm | sourced | as above |
| Rating | 125 VAC/6 A, 250 VAC/3 A (no DC figure) | sourced (AC only) | as above |
| Colour | black | sourced | as above |
| Price class | ≈€0.50 | sourced | as above |

**Rejected for the fan-switch placement (architect ruling, `layout-patch-wall.md` §18.2).** Its
snap-in bezel — not its cutout — sets the pocket footprint (≈15.5 × 10 mm), which needs ≈14.6 mm of
pad against the plus family's own 17.60 mm compact-family pad band (worse margin than the toggle,
and the compact family is infeasible either way). Its snap-fit panel range is also typically
~1–1.5 mm, incompatible with this repo's own 2.0 mm minimum-residual-material precedent
(`MCC_APERTURE_LIP_WEB_MIN`) — T1-44(b)/(c) would fail as soon as the range were measured. No
upside over the toggle to offset this: "must not toggle by accident" is satisfied by the recess
pocket's own geometry (T1-44a), not by the switch's own shape, so there is no accidental-toggle
penalty for choosing the toggle instead.

## 3. SCI-PARTS WS R13-112 A-SW (sealed IP65 round rocker) — recorded alternative, not placed

| Property | Value | Confidence | Source |
|---|---|---|---|
| Cutout | round, ⌀20.2 mm snap-in | sourced | [reichelt.com](https://www.reichelt.com/de/en/shop/product/rocker_switch_round_ip65_1_x_on_-_off_black_black-105455) (part R13-112A8-02-BB-2) |
| Panel-thickness clamp range | not stated | `unknown` | as above |
| Body depth behind panel | 22.3 mm | sourced | as above |
| Actuator height proud of panel | not stated | `unknown` | as above |
| Rating | 10(4) A @250 VAC **and 10 A @24 VDC — a genuine DC rating** | sourced | as above |
| Ingress protection | IP65 | sourced | as above |
| Colour | black | sourced | as above |
| Price class | ≈€2.05 | sourced | as above |

**Not placed — does not fit the current `fan_y` band at all, and moving `fan_y` does not rescue
it either.** This is the only candidate with a genuine DC rating and real ingress protection, so it
remains the go-to if the team later revisits the fan/switch placement or wants a bench-tested
low-risk contact — but its ⌀20.2 mm cutout needs a much wider band than the ≈17.6–20.9 mm raw pad
bands this repo's own +X wall geometry offers next to the fan (`layout-patch-wall.md` §5). Shifting
`fan_y` off its documented default (`y_dev_c`) to try to buy more room was evaluated and rejected
(architect ruling, `layout-patch-wall.md` §18.2): the `+Y` side is capped by the connector bay's own
inward reach (`fan_y ≤ −25.7` on the compact family), worth ≤5.1 mm where ≈10 mm is needed, and a
`fan_y` move on this basis would also re-open **R20** ("the fan-position default moves on
measurement, not on a switch's convenience"). If a future coupon or measurement changes the
governing geometry, this is the part to revisit — with its own architect sign-off, not as a silent
default change.

---

## DC switching at low current — unverified for all three

As noted above, none of the three candidates' datasheets publish a DC rating anywhere near 5 V at
≤0.05 A; all three quote only an AC figure. This mirrors the exact open question
`poe-splitter-verification.md` §4 already recorded for the KSD9700 thermoswitch — cross-referenced
here rather than duplicated: cheap contacts at trivial current relative to their AC rating are not
expected to fail, but "dry-circuit switching lore" is lore, not a confirmed defect for any specific
part. Bench-test (cold, and after ~50 cycles) before relying on any of them, same treatment the
KSD9700 already gets (M8).

[fans.md]: fans.md
