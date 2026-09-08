# Thermal Design Guidelines for 3D-Printed Magewell Pro Convert NDI Cases

Scope: rugged, FDM-printed protective enclosures for Magewell Pro Convert NDI video converters
(≈5–15 W dissipation) used in live/touring production. Covers passive vs. active cooling, sizing
math, component selection, and power budgeting for an optional small Noctua fan.

---

## 1. Why plastic enclosures trap heat

FDM plastics are poor thermal conductors compared with metal enclosures. Directly verified figures:

| Material | Thermal conductivity | Source |
|---|---|---|
| ABS | 0.1 W/(m·K) | [Wikipedia – ABS, physical properties table](https://en.wikipedia.org/wiki/Acrylonitrile_butadiene_styrene) (fetched 2026-09-07) |
| ABS | 0.15–0.21 W/(m·K) (range) | [EngineerExcel – Thermal Conductivity of Plastics](https://engineerexcel.com/thermal-conductivity-plastic/) (fetched 2026-09-07) |
| PETG | 0.21 W/(m·K), ASTM C177 | [Rigid.ink PETG Data Sheet (PDF), Thermal Properties table](https://devel.lulzbot.com/filament/Rigid_Ink/PETG%20DATA%20SHEET.pdf) (fetched 2026-09-07) |
| PETG | ~0.1–0.2 W/(m·K) (typical range) | [Wevolver – PETG Temperature Resistance](https://www.wevolver.com/article/petg-temperature-resistance-heat-limits-and-practical-insights-for-engineers) (fetched 2026-09-07) |
| ASA | 0.18 W/(m·K) | [MakeItFrom – Acrylonitrile Styrene Acrylate (ASA)](https://www.makeitfrom.com/material-properties/Acrylonitrile-Styrene-Acrylate-ASA) (fetched 2026-09-07) |
| ASA | field present but **value not published** on this specific TDS | [purefil ASA Material Data Sheet (PDF)](https://cdn.shopify.com/s/files/1/0919/6571/8867/files/purefil_ASA_Material_data_sheet.pdf) (fetched 2026-09-07) — confirms the property is normally reported on ASA TDS sheets but this particular sheet ships with the number blank |
| Polycarbonate (PC) | 0.2025 W/(m·K) | [designerdata.nl – Polycarbonate](https://designerdata.nl/materials/plastics/thermo-plastics/polycarbonate) (fetched 2026-09-07) |
| Aluminum | ≈204 W/(m·°C) (≈118 BTU·in/hr·ft²·°F); described as "roughly 1,000× more conductive than typical unfilled plastics" | [EngineerExcel – Thermal Conductivity of Plastics](https://engineerexcel.com/thermal-conductivity-plastic/) (fetched 2026-09-07) |

**Takeaway:** all four candidate FDM materials (PETG, ABS, ASA, PC) sit in a narrow 0.10–0.21 W/m·K
band — none is meaningfully better than another for heat spreading, and all are roughly **three
orders of magnitude** worse than aluminum. This means:

- The shell **cannot act as a heatsink**. Conduction through the wall to the outside air contributes
  almost nothing to total heat rejection compared to a metal case, where the whole shell becomes an
  isothermal heat-spreading surface.
- Nearly all heat leaving the device must do so via **air motion** (natural or forced convection)
  through vents, not via conduction through the walls.
- Wall thickness has only a second-order effect on cooling (thin walls do not meaningfully improve
  conduction because convection at the plastic's two air-facing surfaces is already the bottleneck,
  not conduction through ~2–4 mm of plastic). Design for airflow, not for a "thin thermal path."
- A metal insert or heat-spreader plate directly under/against the Magewell board (e.g., an aluminum
  plate bonded to the case wall as a thermal pad target) is a legitimate way to borrow some of
  metal's conductivity locally, but the general shell should still be treated as an insulator.

---

## 2. Natural convection (passive cooling) — the h coefficient and Q = h·A·ΔT

**Formula:**

```
Q = h · A · ΔT
```

- `Q` = heat rejected by convection, in Watts
- `h` = convective heat transfer coefficient, W/(m²·K)
- `A` = external surface area of the enclosure exposed to ambient air, m²
- `ΔT` = temperature difference between the enclosure surface (or internal air) and ambient, K (or °C — same magnitude for a difference)

This is standard heat-transfer physics (Newton's Law of Cooling), not enclosure-specific — stated
here without a dedicated citation as established textbook physics.

**Verified h values for still/quiet air**, from a directly-fetched engineering source:

| Condition | h (W/m²K) | Source |
|---|---|---|
| Still air (conservative design value) | 1.6 | [Leipole – How to Calculate Enclosure Heat Transfer Load Accurately](https://leipole.com.sg/technical-articles/how-to-calculate-enclosure-heat-transfer-load-accurately/) (fetched 2026-09-07) |
| Light air movement | 2.5 | same source |
| Forced air / wind | 6.0 or higher | same source |

The same source gives the combined formula `Q = U·A·ΔT`, where `U` is the overall heat transfer
coefficient (accounts for the series combination of internal convection, wall conduction, and
external convection resistances) — for a thin plastic wall, wall conduction resistance is small
relative to the two convection resistances, so `U ≈ h_internal‖h_external` in practice, and the
outer-surface `h` dominates the calculation used in this document.

**Wider "rule of thumb" range — flagged as lower-confidence:** several engineering-forum and
aggregator sources (an Eng-Tips.com discussion thread and a ResearchGate Q&A) are repeatedly
indexed as citing **5–10 W/m²K** as a typical natural-convection coefficient specifically for
"electronics boxes." I was not able to directly fetch the full text of either page (both blocked
automated fetching with HTTP 403, and an archive.org mirror was also unreachable from this
environment) — the figure is corroborated only by the search engine's indexed snippet text, not by
a page I could read in full. Treat 5–10 W/m²K as a **plausible but unverified upper-bound**
alternative to the confirmed 1.6–2.5 W/m²K still-air figures above; this document's worked example
uses both to bracket the answer.
Source (unverified beyond snippet): [Eng-Tips — Rule of thumb equations for convective cooling of metal surfaces](https://www.eng-tips.com/threads/rule-of-thumb-equations-for-convective-cooling-of-metal-surfaces.362994/) (indexed 2026-09-07, full text not retrievable).

**Flat-plate formula (for reference / more rigor):** [Electronics Cooling — Simplified Formula for
Estimating Natural Convection Heat Transfer Coefficient on a Flat Plate](https://www.electronics-cooling.com/2001/08/simplified-formula-for-estimating-natural-convection-heat-transfer-coefficient-on-a-flat-plate/)
(fetched 2026-09-07) gives `h = C·(ΔT/L)^0.25`, with `C = 1.42` for a vertical plate, `C = 1.32` for
a horizontal plate heated-side-up, and `C = 0.59` for a horizontal plate heated-side-down (`L` is
the characteristic plate length in meters, ΔT in K). Useful if you want an h that scales with your
actual ΔT rather than a flat rule-of-thumb constant; the article notes this simplified form
under-predicts more rigorous dimensionless correlations by roughly 3–15% depending on orientation.

---

## 3. Vent area rules of thumb

I could not verify a specific numeric "vent area per watt" ratio from a source whose full text I
could fetch. Several vendor blog pages (Polycase, TopCabinet) that appear in search results to
contain such a ratio (e.g., a commonly repeated "~1 in² of vent free area per 10 W," ≈0.65 cm²/W)
blocked automated fetching (HTTP 403) — **this specific ratio is `unknown`/unverified and should not
be treated as a citable figure.**

What **is** directly verified from three independently-fetched vendor engineering pages is a
consistent forced-air sizing formula (see §4) plus consistent qualitative placement/filter guidance
(see §5–6). For passive vent sizing specifically, the physically rigorous and verifiable approach is
to use §2's `Q = h·A·ΔT` on the *vent opening area itself is not the limiting term* — vents mainly
need to be large enough to not throttle the buoyancy-driven flow; a practical, defensible approach
used in this document is to size vent free area comfortably larger than the fan's inlet/outlet duct
area when a fan is present (see §4), and, for a fan-less design, to make inlet and outlet free area
each at least equal to the enclosure's largest internal cross-section so vents are not the
bottleneck — this is a design heuristic, not a cited numeric rule, and is flagged as such.

---

## 4. Fan sizing for a target ΔT

**Governing formula:**

```
Q = ṁ · cp · ΔT        where ṁ = ρ · V̇
⇒ V̇ = Q / (ρ · cp · ΔT)
```

- `Q` = heat load to remove by forced convection, W
- `ṁ` = mass flow rate of air, kg/s
- `cp` = specific heat of air ≈ **1005 J/(kg·K)** — standard air property, not enclosure-specific
- `ρ` = air density ≈ **1.2 kg/m³** at room temperature — standard air property, not enclosure-specific
- `ΔT` = allowable temperature rise of the air passing through the enclosure, K (or °C)
- `V̇` = required volumetric airflow, m³/s (convert to m³/h by ×3600, or to CFM by ×2118.9)

**Cross-check against industry shortcut formula.** Three independently-fetched vendor engineering
pages all give the same imperial-shortcut form for required fan airflow:

```
CFM = 3.16 × P(W) / ΔT(°F)      (approximately; one source used 3.17)
```

Sources: [FanACDC — Enclosure Ventilation](https://fanacdc.com/enclosure-ventilation/) (fetched
2026-09-07); [Airline Hydraulics blog — Electrical Enclosure Ventilation](https://blog.airlinehyd.com/ventilation-when-its-required)
(fetched 2026-09-07); [AC/DC EC Fan — Enclosure Ventilation for Electronics](https://www.acdcecfan.com/enclosure-ventilation-for-electronics/)
(fetched 2026-09-07). Note this constant (3.16 ≈ 3.412 BTU/hr per W ÷ 1.08, the standard
BTU/hr = 1.08 × CFM × ΔT°F HVAC relation) requires **ΔT in °F**, not °C, even though at least one of
the source blog posts labels its worked example in °C — this appears to be a labeling error in that
source. Using the SI formula above and converting ΔT to °F before applying the 3.16 shortcut gives a
matching answer (shown in the worked example, §11), which is a useful sanity check.

All three sources also recommend adding a **20–30% margin** to the calculated airflow to account for
filter loading, fan aging, and higher-than-nominal ambient temperature.

**Static pressure / real-world derating.** A fan's datasheet CFM/m³h rating is its **free-air**
rating — measured with nothing in front of or behind it. Once air has to pass through vent slots,
a dust filter, and around internal obstructions (the Magewell PCB, cabling, standoffs), the system
imposes **static pressure (backpressure)** that reduces actual delivered airflow below the free-air
number. This is described by the fan's **PQ curve** (airflow vs. static pressure): airflow is
maximum at zero backpressure and falls to zero at the fan's maximum ("shutoff") pressure; the real
operating point is wherever the fan's PQ curve intersects the enclosure's resistance curve.
Source: [Orion Fans — What is a PQ Curve and how is it generated?](https://orionfans.com/pq-curve/)
(fetched 2026-09-07). No universal numeric derating percentage was found in verifiable sources — the
practical implication is: **select a fan whose free-air rating comfortably exceeds the calculated
V̇ requirement** (a 2× margin is a reasonable, commonly-applied design buffer combining the vendor
20–30% filter/ambient margin above with headroom for backpressure) rather than relying on a fixed
derating percentage.

---

## 5. Inlet/outlet placement — chimney effect

Directly verified from the same three vendor sources as §4:

- **Cool air in low, warm air out high.** Warm air is less dense and rises; placing the inlet low
  and the outlet high lets buoyancy assist airflow (the "chimney effect"), which helps even a fan
  do less work, and provides some cooling even if the fan stops.
  Sources: [FanACDC](https://fanacdc.com/enclosure-ventilation/) ("Cool air should come in at the
  bottom or front. Warm air should exit at the top or rear... Placement Tip: Intake low, exhaust
  high uses natural convection to help airflow"); [AC/DC EC Fan](https://www.acdcecfan.com/enclosure-ventilation-for-electronics/)
  ("Bottom-In, Top-Out Rule" — position intake low on one side, exhaust high on the opposite side).
  (both fetched 2026-09-07)
- **Avoid short-circuiting / recirculation.** Don't let incoming air travel straight to the outlet
  without passing over the hot component — route the flow path across the Magewell board/heatsink
  area, not around it. Source: FanACDC (fetched 2026-09-07), "Avoid short circuits in airflow. Don't
  let air move straight from intake to exhaust without passing over your electronics."
- **Fan orientation:** mount the fan so it blows directly across (or pulls air directly across) the
  hottest surface of the device — for the Pro Convert, that is the metal top/chassis surface of the
  unit itself, which is the device's own primary heat-dissipation path. Position the fan as an
  exhaust (pulling hot air out, high in the case) or intake (pushing air in, low in the case, angled
  across the board) — either works as long as the flow path crosses the hot component, per the
  short-circuit-avoidance point above.

---

## 6. Dust filtering

Verified guidance from the fetched vendor sources (§4/§5):

- **Filter goes on the intake, not the exhaust** — this protects the whole internal volume rather
  than only the fan. Source: [AC/DC EC Fan](https://www.acdcecfan.com/enclosure-ventilation-for-electronics/)
  (fetched 2026-09-07), "Always place your filter on the air inlet, not the outlet."
- **Filtering restricts airflow and must be budgeted for.** All three vendor sources recommend
  20–30% extra calculated airflow specifically to offset filter resistance (see §4), and recommend
  periodic inspection/cleaning — [FanACDC](https://fanacdc.com/enclosure-ventilation/) (fetched
  2026-09-07) recommends monthly inspection, more often in dusty environments, "before they clog."
- **Practical filter media for a small touring case:** the sources surveyed listed HEPA, activated
  carbon, and electrostatic precipitator options aimed at general industrial enclosures — these are
  overkill (and in HEPA's case, far too airflow-restrictive) for a small vented FDM case moving only
  a few CFM. For this scale, the two practical options are:
  - **Open-cell foam filter** (e.g., a thin acoustic/PU foam pad) over the intake vent slots —
    low cost, easy to cut to a custom vent shape, washable/replaceable, but adds real static-pressure
    restriction that must be included in the fan-sizing margin (§4).
  - **Fine mesh screen** (metal or plastic, e.g. ~0.3–0.5 mm openings) — lower airflow restriction
    than foam, effective against larger dust/fiber debris and stray cabling/gaffer-tape fluff typical
    of a touring case, but passes finer dust that foam would catch.
  - The tradeoff is airflow vs. protection: finer filtration = more static pressure = less delivered
    airflow for a given fan (per §4's PQ-curve point), and more frequent maintenance. Given a touring
    case is opened/handled often, a coarse washable mesh is the more maintenance-friendly default;
    add a foam layer only if the venue dust/haze-fluid environment specifically warrants it.

---

## 7. Fan noise expectations for stage/live-performance use

**Typical ambient/reference sound levels**, from a directly-fetched reference chart (National
Hearing Conservation Association, statistics compiled from a study by Marshall Chasin, M.Sc.,
Aud(C), FAAA — [hearingconservation.org, Decibel (Loudness) Comparison Chart, PDF](https://www.hearingconservation.org/assets/Decibel.pdf), fetched 2026-09-07):

| Environment | Level |
|---|---|
| Whisper-quiet library | 30 dB |
| Normal conversation (3–5 ft) | 60–70 dB |
| City traffic (inside car) | 85 dB |
| Loud rock concert | 115 dB |
| Amplifier (rock), 4–6 ft | 120 dB |

**Live-venue-specific figures**, from [Thrillzing — How Loud Is a Concert? Decibel Levels by Venue &
Genre](https://thrillzing.com/music-venues/concert-decibel-levels/) (fetched 2026-09-07):

| Venue/context | Typical range |
|---|---|
| Small clubs (200–500 cap.) | 95–110 dB |
| Theaters (500–3,000 cap.) | 90–105 dB |
| Arenas (5,000–20,000 cap.) | 95–115 dB |
| Stadiums (20,000–100,000 cap.) | 100–120 dB |
| Jazz clubs | 80–95 dB |
| Classical/orchestral | 70–95 dB |
| General concert average (main set) | 95–110 dB |

**Noctua fan noise ratings** (all directly fetched from Noctua's own spec pages or authorized
retailer listings that mirror them):

| Model | Max speed | Max airflow | Max noise | Low-noise-adapter noise | Source |
|---|---|---|---|---|---|
| NF-A4x10 FLX | 4500 RPM | 4.8 CFM | 17.9 dB(A) | 12.9 dB(A) @ 3700 RPM | [QuietPC](https://www.quietpc.com/nf-a4x10) (fetched 2026-09-07) |
| NF-A4x20 FLX | 5000 RPM | 5.5 CFM | 14.9 dB(A) | 12.2 dB(A) (LNA) / 8.5 dB(A) (ULNA)† | [QuietPC](https://www.quietpc.com/nf-a4x20-flx) (fetched 2026-09-07) |
| NF-A6x25 5V‡ | 3000 RPM | 17.2 CFM | 19.3 dB(A) | 14.5 dB(A) (LNA) / 8.2 dB(A) (ULNA) | [QuietPC](https://www.quietpc.com/nf-a6x25) (fetched 2026-09-07) |
| NF-A8 ULN | 1400 RPM | 34.8 m³/h (20.48 CFM) | 10.4 dB(A) | 6.5 dB(A) @ 1100 RPM | [QuietPC USA](https://www.quietpcusa.com/Noctua-NF-A8-ULN-Quiet-Computer-Fan-80mm) (fetched 2026-09-07) |
| NF-A8 PWM | 2200 RPM | 55.5 m³/h (25.83 CFM) | 17.7 dB(A) | 13.8 dB(A) @ 1750 RPM (LNA) | [Coolerguys](https://www.coolerguys.com/products/noctua-nf-a8-pwm-fan-80x25mm-12v-4-pin) (fetched 2026-09-07) |

† **NF-A4x20 ULNA figure — corroborated by QuietPC only, not by a first-party Noctua page (corrected
2026-09-08).** `knowledge/components/fans.md`'s own NF-A4x20 table (fetched directly from Noctua's
product pages) lists a standard Low-Noise Adaptor for this frame size but has no ULNA row at all. A
same-session re-fetch of the QuietPC page cited above re-confirmed it still states "Ultra-Low-Noise
Adaptor (U.L.N.A.) ... 8.5 dB(A)", but two attempts to fetch Noctua's own NF-A4x20 5V PWM and 12V PWM
spec pages directly — to settle whether Noctua itself publishes a ULNA option for this fan — both
returned HTTP 429 ("too many requests") on 2026-09-07. Per `knowledge/design/README.md`'s resolution
for this item: treat the 8.5 dB(A) figure as **unconfirmed against a first-party Noctua source**
(effectively `unknown` at manufacturer level) rather than deleting it outright, since it remains a
real, re-verified figure from the retailer page already cited here.

‡ **Renamed from "NF-A6x25 FLX" (corrected 2026-09-08).** The RPM/airflow/noise figures in this row
match `knowledge/components/fans.md:50` (the NF-A6x25 **5V** row) exactly; "FLX" is not a Noctua-
published variant name for this frame size — fans.md's own NF-A6x25 table (fetched directly from
Noctua's product pages) lists only **5V**, **5V PWM**, and **12V PWM** variants, no "FLX". See §8
below for the matching correction to this fan's power/current figures.

**Conclusion:** the entire Noctua small-fan range tops out around 20 dB(A) at full speed (8–13 dB(A)
with the bundled low-noise adapters). Even the loudest of these, run at maximum speed, sits roughly
**60–100 dB below** a live stage/FOH noise floor of 90–120 dB(A) — completely inaudible/masked
during a show; it would not be perceptible from more than perhaps arm's length even backstage. The
only context in this product's use case where fan noise is a real concern is a **silent environment**
— e.g., a broadcast control room, an empty pre-show soundcheck, or a quiet studio (≈30–40 dB ambient
per the table above) — where an unfiltered fan at full speed (14–20 dB(A)) could be faintly audible
up close. For those contexts, using the bundled low-noise adapter (or PWM-controlling the fan down
to the minimum RPM needed for the actual heat load, see §11) keeps it under the ~10 dB(A) range,
which is at or below the "whisper-quiet library" reference level and effectively inaudible.

---

## 8. Powering a 5V fan from a device's USB port

**USB-IF current budgets**, confirmed directly:

| Spec | Unit load | Max current (high-power device) |
|---|---|---|
| USB 2.0 | 100 mA | **500 mA** (5 unit loads) |
| USB 3.0 / SuperSpeed | 150 mA | **900 mA** (6 unit loads) |

Source: [Wikipedia — USB 3.0](https://en.wikipedia.org/wiki/USB_3.0) (fetched 2026-09-07), citing
the USB-IF SuperSpeed specification's power-delivery figures directly.

**Budget remaining after a small fan.** Using the directly-verified Noctua power draws from §7's
sources (all measured at 12V; see caveat below):

| Fan | Max input power | Current at the voltage shown | % of USB 2.0 500 mA budget | % of USB 3.0 900 mA budget |
|---|---|---|---|---|
| NF-A4x10 5V (real 5V-native SKU)§ | 0.22 W typ / 0.25 W max | 0.044 A typ / 0.05 A max | 10% (at max) | 6% (at max) |
| NF-A4x20 FLX (12V, scaled to 5V — estimate, unchanged)¶ | 0.6 W | ≈120 mA | 24% | 13% |
| NF-A6x25 5V (real 5V-native SKU)§ | 0.935 W typ / 1.3 W max | 0.187 A typ / 0.26 A max | 52% (at max) | 29% (at max) |
| NF-A8 PWM (12V, scaled to 5V — estimate, unchanged)¶ | 0.96 W | ≈192 mA | 38% | 21% |

§ **Corrected 2026-09-08 (previously an order-of-magnitude 12V→5V estimate under a "FLX" label; see
`knowledge/design/README.md`'s resolved-inconsistencies list).** Noctua sells purpose-built 5V-native
SKUs for both of these frame sizes, and `knowledge/components/fans.md` has their real, directly-
fetched Noctua-published figures — used directly above instead of scaling the 12V rating down:

- **NF-A4x10 5V:** 0.044 A typ / 0.05 A max, 0.22 W typ / 0.25 W max — `knowledge/components/fans.md:22`.
- **NF-A6x25 5V:** 0.187 A typ / 0.26 A max, 0.935 W typ / 1.3 W max — `knowledge/components/fans.md:50`.
  The NF-A6x25 **12V PWM** variant is a separate SKU with its own, lower figures — 0.08 A max
  (typ `unknown`), 0.96 W max (typ `unknown`) — `knowledge/components/fans.md:52` — not directly
  comparable to the 5V figure since it is natively 12V, not 5V-scaled. The row previously here read
  "1.44 W, NF-A6x25 FLX", a figure that matched neither the real 5V nor 12V PWM Noctua numbers and
  used a variant name ("FLX") that does not appear anywhere in fans.md's NF-A6x25 table; both the
  number and the name have been corrected.

¶ The NF-A4x20 and NF-A8 rows above are **not** corrected in this pass — fans.md's real 5V-native
figures for those two families were out of scope for this fix (see `knowledge/design/README.md`).
They still use the older 12V-power-scaled, order-of-magnitude estimate method and should not be
treated as vendor-published 5V figures.

Underlying caveat (unchanged, applies to the two still-estimated rows above): a fan's 12V-rated
power/current does not scale linearly to 5V — motor current-vs-voltage behavior is non-linear (this
is exactly the reason resistor-based control is unsuitable, see §9) — so the NF-A4x20/NF-A8
"Approx." current figures remain order-of-magnitude only, useful for USB budget planning but not a
vendor-published 5V number.

**Conclusion:** any of these small Noctua fans leaves 60%+ of even the more conservative USB 2.0
budget free, so USB bus power is a comfortable option for the smaller three models if the Magewell
device exposes a powered USB host port; the NF-A6x25 (the highest-airflow option) is still workable
on USB 3.0 but eats over half a USB 2.0 budget, leaving less margin for anything else sharing that
port.

---

## 9. Powering from a 12V DC line

If the case has access to a 12V supply rail (e.g., a 12V barrel-jack-powered Magewell variant, or a
shared 12V rail from other touring gear), two real options exist:

### Option A — native 12V fan
Run a 12V-rated fan (e.g., any of the Noctua models above in their standard 12V SKU) directly off
the 12V line. This is the simplest, most efficient option — no conversion loss at all — and is the
default recommendation whenever a 12V rail already exists in the case.

### Option B — 5V fan from a 12V line, via linear regulator (LDO) or buck converter
If a 5V-only fan must be used instead (e.g., to reuse the same fan SKU as the USB-powered variant of
the case, or because a lower `CFM`/quieter fan is only available in a 5V flavor), the 12V must be
stepped down. **A simple resistor divider (or single series resistor) is the wrong approach**, for a
verified, specific reason:

> "A DC fan motor does not behave as a fixed resistor. The effective impedance changes with applied
> voltage and rotational speed... at reduced voltage, the fan attempts to maintain speed, drawing
> more current relative to voltage." Source: [Industrial Monitor Direct — Calculating Resistor
> Wattage for DC Fan Speed Control Circuits](https://industrialmonitordirect.com/blogs/knowledgebase/calculating-resistor-wattage-for-dc-fan-speed-control-circuits) (fetched 2026-09-07)

In other words, a resistor sized correctly for the fan's current at one operating point (e.g., fan
startup, or steady-state at a particular RPM) will be wrong at any other point — as RPM changes
(due to dust buildup, bearing wear, temperature, or simply spin-up), current changes, so the voltage
dropped across a *fixed* resistor changes too, meaning the fan never sees a stable, correct 5V. This
also wastes power as heat in the resistor with no useful voltage regulation.

The correct approaches are a proper voltage regulator:

- **Linear regulator (LDO):** simple, cheap, low parts count, low EMI/noise (a real consideration if
  the case shares space with sensitive video/network signal paths). Its efficiency is fundamentally
  capped at `η = Vout/Vin` regardless of load current — for 12V→5V that ceiling is **5/12 ≈ 42%**,
  meaning **58% of the input power is dissipated as heat in the regulator itself**. For a fan drawing
  even 100 mA at 5V (0.5 W delivered), the LDO must dissipate `(12V − 5V) × 0.1A = 0.7 W` as heat —
  more heat than the fan itself is consuming. This is basic Ohm's-law/power arithmetic (P = I × ΔV),
  not sourced to a specific article. At these currents (tens to a couple hundred mA) an LDO's heat
  output is small in absolute terms (well under 1 W) but is a poor use of power budget and adds
  unwanted heat directly inside a case that is already thermally constrained.
- **Buck (switching) converter:** far higher efficiency for this large a voltage drop — commonly
  90%+ even at low output currents in the tens-of-mA-to-several-hundred-mA range relevant here.
  Source: [ipXchange — When an LDO Beats a Buck: Designing for Micro-Load Efficiency](https://ipxchange.tech/industry-insights/low-power/ldo-vs-buck/)
  (fetched 2026-09-07) — this article's own crossover point is only reached at sub-100 µA loads
  (where a buck converter's own quiescent-current draw starts to dominate); a small case fan (tens to
  hundreds of mA) is far above that crossover, so the article's general finding — "buck converters
  shine at high currents and large Vin–Vout differences... often reach efficiency of up to 95%" —
  applies to this design case, favoring buck over LDO.

**Recommendation:** for a 12V→5V fan supply in this power range, prefer a small buck converter
module (widely available as inexpensive pre-built boards) over an LDO, specifically because of the
large 12V→5V voltage drop — the efficiency gap directly reduces case-internal heat generation, which
matters because that heat adds to the very thermal load the fan exists to remove. An LDO remains an
acceptable, simpler fallback if board space/cost is more constrained than the extra sub-1W of
self-heating, since that self-heating is still small in absolute terms at this current level.

---

## 10. PoE-powered devices

If the Magewell Pro Convert unit in the case is powered via PoE (802.3af/at), **there is no separate
DC rail available inside the case** — the only power entering the enclosure is on the Ethernet
cable, carried as high-voltage PoE (typically 36–57 VDC as delivered to a PD). Two practical options
exist for fan power in this scenario:

1. **USB, if the device has a powered USB host port** — see §8. This is the simplest option when
   available, since it needs no extra hardware inside the case.
2. **A small PoE splitter module** — a device that taps the PoE line and extracts a regulated low
   voltage (5V or 12V) alongside passing the Ethernet data through, functionally similar to how the
   Magewell unit itself likely receives its own power if it's a PD. A confirmed real product example:

   > **Tripp Lite / Eaton PoE to USB Micro-B, RJ45, Active Splitter (model NPOE-SPL-G-5VMU):**
   > IEEE 802.3af/at-compliant input (36–57 VDC), outputs a regulated **5V DC at 1A (5W)** via USB
   > Micro-B, while passing Ethernet data through its RJ45 port.
   > Source: [Tripp Lite / Eaton product page](https://tripplite.eaton.com/poe-to-usb-micro-b-rj45-active-splitter-802af-48v-to-5v-1a-raspberry-pi-up-to-328ft-100m~NPOESPLG5VMU) (fetched 2026-09-07)

   Other vendors (UCTRONICS, Adafruit, POE Texas) sell similar 802.3af/at→5V-USB splitter modules in
   the same general 1–2.4A output class; these were seen in search listings but not individually
   fetched/verified in this session, so treat their specific current ratings as indicative rather
   than confirmed.

   This is the more involved option (extra board, extra volume inside an already-tight case) but is
   the only way to get local 5V/12V power when USB is not available and the device is PoE-only.

**Practical recommendation:** check first whether the specific Magewell Pro Convert model/variant
being cased has a USB host port that stays powered while the unit is PoE-powered (many small
converters expose a USB-A port for config/firmware, sometimes powered even in normal operation) —
that avoids needing a splitter at all. If not, a PoE splitter tap is the fallback.

---

## 11. Worked example (10 W enclosure, 15°C max ΔT)

**Assumptions (stated explicitly):**
- Enclosure external dimensions: **150 mm × 100 mm × 50 mm** (a plausible compact case size for a
  Pro Convert unit plus a small fan and cabling clearance).
- Total heat dissipation: **Q = 10 W** (mid-range of the stated 5–15 W envelope).
- Target maximum internal-to-ambient ΔT: **15°C**.
- Enclosure treated as a closed box with all 6 faces exposed to ambient air (a conservative
  simplification — in practice one face may sit against a mounting surface, further reducing
  effective convective area and making the passive case even worse than calculated below).

### (a) Can natural convection alone handle it?

External surface area of a 0.15 m × 0.10 m × 0.05 m box:

```
A = 2×(0.15×0.10) + 2×(0.15×0.05) + 2×(0.10×0.05)
  = 2×0.0150 + 2×0.0075 + 2×0.0050
  = 0.0300 + 0.0150 + 0.0100
  = 0.0550 m²
```

Using `Q = h·A·ΔT`, rearranged to find the max Q rejectable at ΔT = 15°C for each candidate h from §2:

| h (W/m²K) | Source | Q_max = h × 0.055 m² × 15°C |
|---|---|---|
| 1.6 (still air, verified) | Leipole | 1.6 × 0.055 × 15 = **1.32 W** |
| 2.5 (light air movement, verified) | Leipole | 2.5 × 0.055 × 15 = **2.06 W** |
| 10 (upper end of unverified "5–10" range) | Eng-Tips (unverified, §2) | 10 × 0.055 × 15 = **8.25 W** |

Even at the most optimistic, **unverified** end of the natural-convection range found in this
research (h = 10 W/m²K), the enclosure can passively reject only **8.25 W** — short of the 10 W
target. At the directly-verified, conservative still-air figure (h = 1.6 W/m²K), passive convection
handles only **1.32 W**, about 13% of the load. Put another way, solving for the h that *would* be
required to hit 10 W at ΔT=15°C over this surface area:

```
h_required = Q / (A × ΔT) = 10 / (0.055 × 15) = 10 / 0.825 = 12.1 W/m²K
```

12.1 W/m²K exceeds every natural-convection figure found in this research (verified or not) — this
enclosure/power/ΔT combination has a genuinely high power density for its size (10 W ÷ 0.055 m² ≈
182 W/m²) that natural convection cannot resolve within the 15°C target.

**Conclusion (a): natural convection alone is insufficient. Active (fan) cooling is required.**

### (b) Required fan airflow

Using `V̇ = Q / (ρ · cp · ΔT)` with standard air properties (ρ = 1.2 kg/m³, cp = 1005 J/kg·K — not
enclosure-specific, standard air property):

```
V̇ = 10 / (1.2 × 1005 × 15)
  = 10 / 18,090
  = 5.53 × 10⁻⁴ m³/s
```

Convert to more usable units:

```
V̇ (m³/h) = 5.53 × 10⁻⁴ × 3600 = 1.99 m³/h  ≈ 2.0 m³/h
V̇ (CFM)  = 5.53 × 10⁻⁴ × 2118.9 = 1.17 CFM
```

**Cross-check with the industry shortcut formula from §4** (`CFM = 3.16 × P(W) / ΔT(°F)`, which
requires ΔT in °F): 15°C of *difference* = 15 × 9/5 = 27°F of difference.

```
CFM = 3.16 × 10 / 27 = 1.17 CFM
```

This matches the SI-derived figure exactly, which is a useful sanity check on both calculations.

**Applying a safety margin.** Per §4's fan-derating discussion (vendor-recommended 20–30% margin for
filter/ambient effects, plus additional headroom for static-pressure losses through vents and around
the internal PCB), apply roughly a **2× margin** to the ideal figure:

```
Target fan free-air rating ≥ 2 × 1.17 CFM ≈ 2.3–2.5 CFM  (≈ 4.0 m³/h)
```

**Conclusion (b): the case needs a fan rated for at least ~2.3–2.5 CFM (~4 m³/h) free-air delivery
to reliably hold ΔT ≤ 15°C at 10 W, after accounting for real-world derating.**

Checking this against the Noctua lineup in §7: **every model in the range clears this bar at full
speed** — even the smallest, NF-A4x10 FLX, is rated 4.8 CFM free-air, and the NF-A4x20 FLX is 5.5
CFM. Because the actual requirement (2.3–2.5 CFM) is well below the smallest fan's rating, these
fans have comfortable headroom, which means two things in practice: (1) there's margin to spare even
after real static-pressure derating from vents/filter/internal obstructions, and (2) the fan can
likely be run below full RPM (via its low-noise adapter, or PWM-controlled to a lower duty cycle)
and still meet the airflow target — which, per §7, would push its already-inaudible-on-stage noise
level down even further, useful for the quiet-environment edge cases noted there.

---

## Sources

- [Wikipedia — Acrylonitrile butadiene styrene (ABS)](https://en.wikipedia.org/wiki/Acrylonitrile_butadiene_styrene) — ABS thermal conductivity (0.1 W/m·K), glass transition/heat deflection temps. Fetched 2026-09-07.
- [EngineerExcel — Thermal Conductivity of Plastics](https://engineerexcel.com/thermal-conductivity-plastic/) — ABS conductivity range (0.15–0.21 W/m·K), aluminum conductivity (~204 W/m·°C) and plastic-vs-metal comparison. Fetched 2026-09-07.
- [Rigid.ink — PETG Data Sheet (PDF)](https://devel.lulzbot.com/filament/Rigid_Ink/PETG%20DATA%20SHEET.pdf) — PETG thermal conductivity, 0.21 W/m·K per ASTM C177, plus specific heat and other thermal properties. Fetched/read 2026-09-07.
- [Wevolver — PETG Temperature Resistance: Heat Limits and Practical Insights for Engineers](https://www.wevolver.com/article/petg-temperature-resistance-heat-limits-and-practical-insights-for-engineers) — PETG conductivity range ~0.1–0.2 W/m·K. Fetched 2026-09-07.
- [MakeItFrom — Acrylonitrile Styrene Acrylate (ASA)](https://www.makeitfrom.com/material-properties/Acrylonitrile-Styrene-Acrylate-ASA) — ASA thermal conductivity, 0.18 W/m·K. Fetched 2026-09-07.
- [purefil — ASA Material Data Sheet (PDF)](https://cdn.shopify.com/s/files/1/0919/6571/8867/files/purefil_ASA_Material_data_sheet.pdf) — confirms ASA TDS format includes a thermal-conductivity field, value blank on this sheet. Fetched/read 2026-09-07.
- [designerdata.nl — Polycarbonate](https://designerdata.nl/materials/plastics/thermo-plastics/polycarbonate) — PC thermal conductivity, 0.2025 W/m·K. Fetched 2026-09-07.
- [Leipole — How to Calculate Enclosure Heat Transfer Load Accurately](https://leipole.com.sg/technical-articles/how-to-calculate-enclosure-heat-transfer-load-accurately/) — natural convection h values (still air 1.6, light air 2.5, forced 6.0+ W/m²K), Q=U·A·ΔT formula. Fetched 2026-09-07.
- [Electronics Cooling — Simplified Formula for Estimating Natural Convection Heat Transfer Coefficient on a Flat Plate](https://www.electronics-cooling.com/2001/08/simplified-formula-for-estimating-natural-convection-heat-transfer-coefficient-on-a-flat-plate/) — h = C(ΔT/L)^0.25 formula and orientation constants. Fetched 2026-09-07.
- [Eng-Tips — Rule of thumb equations for convective cooling of metal surfaces](https://www.eng-tips.com/threads/rule-of-thumb-equations-for-convective-cooling-of-metal-surfaces.362994/) — commonly-indexed "5–10 W/m²K" figure; full text not retrievable (HTTP 403), cited with explicit unverified caveat. Indexed 2026-09-07.
- [FanACDC — Enclosure Ventilation: Complete Guide to Cooling Electronics](https://fanacdc.com/enclosure-ventilation/) — CFM sizing formula (3.16×P/ΔT), chimney-effect placement, filter-type overview. Fetched 2026-09-07.
- [Airline Hydraulics blog — Electrical Enclosure Ventilation: When It's Required and How to Size It Correctly](https://blog.airlinehyd.com/ventilation-when-its-required) — corroborating CFM formula (3.16×P/ΔT) and 20–30% safety margin guidance. Fetched 2026-09-07.
- [AC/DC EC Fan — Enclosure Ventilation: Keeping Your Electronics Cool](https://www.acdcecfan.com/enclosure-ventilation-for-electronics/) — corroborating CFM formula (3.17×P/ΔT), "Bottom-In, Top-Out" placement rule, filter-on-inlet guidance, 20–30% filter buffer. Fetched 2026-09-07.
- [Orion Fans — What is a PQ Curve and how is it generated?](https://orionfans.com/pq-curve/) — static pressure/backpressure derating concept, free-delivery vs. shutoff points. Fetched 2026-09-07.
- [Industrial Monitor Direct — Calculating Resistor Wattage for DC Fan Speed Control Circuits](https://industrialmonitordirect.com/blogs/knowledgebase/calculating-resistor-wattage-for-dc-fan-speed-control-circuits) — why a fixed resistor is unsuitable for fan power/speed control (motor impedance varies with RPM/load). Fetched 2026-09-07.
- [ipXchange — When an LDO Beats a Buck: Designing for Micro-Load Efficiency](https://ipxchange.tech/industry-insights/low-power/ldo-vs-buck/) — LDO vs. buck converter efficiency crossover point (~100 µA), buck converters reaching up to 95% efficiency at higher currents. Fetched 2026-09-07.
- [National Hearing Conservation Association — Decibel (Loudness) Comparison Chart (PDF)](https://www.hearingconservation.org/assets/Decibel.pdf) — reference ambient noise levels (whisper-quiet library 30 dB, conversation 60–70 dB, rock concert 115 dB, amplifier 120 dB), sourced to a study by Marshall Chasin, M.Sc. Fetched/read 2026-09-07.
- [Thrillzing — How Loud Is a Concert? Decibel Levels by Venue & Genre](https://thrillzing.com/music-venues/concert-decibel-levels/) — venue-type-specific concert SPL ranges (clubs, theaters, arenas, stadiums, genre breakdown). Fetched 2026-09-07.
- [QuietPC — Noctua NF-A4x10 FLX](https://www.quietpc.com/nf-a4x10) — NF-A4x10 FLX full specifications (4500 RPM, 4.8 CFM, 17.9 dB(A)). Fetched 2026-09-07.
- [QuietPC — Noctua NF-A4x20 FLX](https://www.quietpc.com/nf-a4x20-flx) — NF-A4x20 FLX full specifications (5000 RPM, 5.5 CFM, 14.9 dB(A)). Fetched 2026-09-07.
- [QuietPC — Noctua NF-A6x25 FLX](https://www.quietpc.com/nf-a6x25) — NF-A6x25 FLX full specifications (3000 RPM, 17.2 CFM, 19.3 dB(A)). Fetched 2026-09-07.
- [QuietPC USA — Noctua NF-A8 ULN](https://www.quietpcusa.com/Noctua-NF-A8-ULN-Quiet-Computer-Fan-80mm) — NF-A8 ULN full specifications (1400 RPM, 34.8 m³/h, 10.4 dB(A)). Fetched 2026-09-07.
- [Coolerguys — Noctua NF-A8 PWM](https://www.coolerguys.com/products/noctua-nf-a8-pwm-fan-80x25mm-12v-4-pin) — NF-A8 PWM full specifications (2200 RPM, 55.5 m³/h, 17.7 dB(A)). Fetched 2026-09-07.
- [Wikipedia — USB 3.0](https://en.wikipedia.org/wiki/USB_3.0) — USB 2.0 (500 mA/5 unit loads) and USB 3.0 (900 mA/6 unit loads) current budgets per USB-IF spec. Fetched 2026-09-07.
- [Noctua — NF-A4x10 5V product/specifications page](https://www.noctua.at/en/products/nf-a4x10-5v/specifications) — real Noctua-published input current (0.044 A typ / 0.05 A max) and input power (0.22 W typ / 0.25 W max), now cited directly in §8 from `knowledge/components/fans.md:22`, which fetched this page successfully on 2026-09-07. This document's earlier note that the page returned HTTP 429 described a *separate*, later fetch attempt made directly from this document's own research session — that attempt did fail, and two further attempts from this session on 2026-09-07 (while resolving this inconsistency) also returned HTTP 429, but `fans.md`'s own successful fetch is the authoritative account for this URL; see `knowledge/design/README.md`'s resolved-inconsistencies list.
- [Tripp Lite / Eaton — PoE to USB Micro-B, RJ45, Active Splitter (NPOE-SPL-G-5VMU)](https://tripplite.eaton.com/poe-to-usb-micro-b-rj45-active-splitter-802af-48v-to-5v-1a-raspberry-pi-up-to-328ft-100m~NPOESPLG5VMU) — confirmed real PoE-to-5V/1A-USB splitter product example. Fetched 2026-09-07.

### Figures explicitly marked `unknown` / unverified in this document

- ASA thermal conductivity as an official manufacturer-published number (one real ASA filament TDS
  was found with the field present but blank; a third-party aggregator (MakeItFrom) gives 0.18 W/m·K,
  used in §1 with that sourcing, but no first-party ASA filament datasheet with a filled-in value was
  found).
- The specific "~1 in² of vent free area per 10 W" (≈0.65 cm²/W) passive-vent sizing ratio (§3) —
  repeatedly indexed in search results but the source pages containing it blocked automated fetch.
- The precise "5–10 W/m²K" natural-convection rule of thumb for electronics enclosures (§2) —
  indexed via search snippet only, primary source (Eng-Tips.com thread) blocked automated fetch
  (HTTP 403), and an archive.org mirror was unreachable from this tool environment.
- ~~The exact current draw (mA) of Noctua's native-5V fan SKUs (e.g., NF-A4x10 5V)~~ — **Resolved
  2026-09-08:** `knowledge/components/fans.md` (fetched 2026-09-07) has real, directly-fetched
  Noctua-published current/power figures for the NF-A4x10 5V and NF-A6x25 5V SKUs; §8's table now
  cites those directly (`knowledge/components/fans.md:22` and `:50`) instead of a 12V-scaled
  estimate. §8's NF-A4x20 and NF-A8 rows are **still** order-of-magnitude estimates derived from
  12V power ratings scaled to 5V, not vendor-published 5V figures — that part of the original
  limitation still applies to those two fans only.
- The NF-A4x20 ULNA figure (8.5 dB(A), §7) — corroborated only by a QuietPC retailer listing, not by
  a first-party Noctua page; two direct-fetch attempts against Noctua's own NF-A4x20 spec pages on
  2026-09-07 both returned HTTP 429. Treat as unconfirmed at manufacturer level (see §7 footnote).
