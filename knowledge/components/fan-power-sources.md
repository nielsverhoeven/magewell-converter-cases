# Fan power sources on PoE-powered Magewell Pro Convert devices

Research question: with the case fan (Noctua NF-A4x10 5V PWM, 0.06 A typ / **0.07 A max**, 0.3 W typ / **0.35 W max** — see
`fans.md`) and the device running on PoE (802.3af, no external 5 V rail available inside a sealed case), which port on the
device itself can legally and safely supply the fan's small 5 V/70 mA load?

**Fetch date: 2026-09-09.** Sources are Magewell's own PDFs (fetched fresh this pass and rendered via the `Read` tool,
which parsed them as vector text/diagrams without needing `pdftoppm`), plus this repo's prior research
(`mini-din8-feedthrough.md`, `poe-splitters.md`, fetched 2026-09-07, re-cited here rather than re-fetched) and general
PoE/USB standards knowledge cited separately from Magewell's own material. `WebFetch`'s own PDF-to-markdown conversion
failed on every Magewell manual PDF this pass ("binary/compressed content, cannot extract text") — the actual content
was obtained by re-reading the same downloaded PDF files with the `Read` tool, which renders PDF pages directly. Anything
not obtained this way is marked accordingly.

---

## 1. Summary table

| Candidate | Device family | Voltage | Current available | Powered under PoE? | Confidence | Evidence |
|---|---|---|---|---|---|---|
| **USB HOST (Type-A)** | NDI decoders: NDI to HDMI, NDI to HDMI 4K, NDI to SDI (**not** NDI to AIO — no USB host port) | 5 V (USB standard) | **Not stated by Magewell.** USB 3.0 SuperSpeed downstream-port baseline per USB-IF spec is up to 900 mA; USB 2.0 baseline is 500 mA. Not independently confirmed for this specific port. | `assumed` — likely yes (it's the device's own peripheral bus, not switched separately from PoE/USB-B power), but not stated in either manual | `assumed`/`unknown` | Decoder manual (§A below) |
| **Mini-DIN-8 "PTZ+TALLY" pin 8 (VCC)** | Encoders: HDMI/SDI Plus, HDMI/SDI 4K Plus, HDMI/SDI TX | **5 V** | **Max load current 100 mA** | `measured` (documented spec, not just inferred) — the port is native to the device's own board, active whenever the device is powered, regardless of PoE vs USB-B | `measured` | Magewell Mini-DIN8-to-Tally+RS232 breakout pinout PDF (§B below) |
| **USB Type-B "+5V" port** | All families | 5 V | Power **input** only — device draws ≥2.1 A from it; not a source | **N/A — this is not a candidate.** No 5 V is present here when running on PoE. | `measured` (explicit manual text) | Both manuals (§C below) |
| **A second PD in parallel with the device's own PoE port** | N/A | — | — | **Not feasible** as a design pattern — see §D | `measured` (IEEE 802.3af/at architecture) | General PoE standards knowledge, Microchip dev docs |

---

## 2. Details

### A. USB HOST port on the NDI decoders

Source: [Pro Convert Decoder Family User Manual](https://www.magewell.com/files/documents/User_Manual/ProConvert_Decoder-UserManual_en_US.pdf)
(fetched 2026-09-09, rendered via `Read`).

- **Port presence per model** (Interfaces & Indicators, pp. 6–9): NDI to HDMI has a "USB 3.0" host port; NDI to HDMI 4K
  has a "USB 3.0" host port (labelled just "USB HOST" on the 2K models' silkscreen, "USB 3.0" in the 4K model's
  connector diagram); NDI to SDI has a "USB 3.0" host port. **NDI to AIO has no USB host port** — confirmed explicitly:
  *"AIO product does not have the USB interface for peripherals"* (Connections, p. 10).
- **Stated purpose only** (Connections, p. 10): *"Connect a wired or wireless keyboard or mouse to the USB HOST
  interface to make it more convenient to control advanced settings without requiring a computer."* This is the entire
  extent of what the manual says about the port — no current/power rating is given anywhere in the 94-page manual (no
  hits for the port outside this one sentence, its labelling in the interface diagrams, and its listing in Table 1 of
  the OSD section, which only maps front-panel buttons, not the USB port).
- **No warning found** against connecting non-keyboard/mouse accessories, and no statement of a maximum output current
  for the port. The manual's only current/power figures anywhere are for the device's own **input** requirement (see
  §C).
- **Whether it stays powered under PoE**: not addressed anywhere in the manual. Both PoE and USB-B power feed the same
  internal 5 V rail that runs the whole board (Connections, p. 10: *"For power supply: connect the other end of the USB
  cable to the power adapter... For PoE: connect the other end of the Ethernet cable to a PoE switch or a PoE adapter
  for power and Ethernet connection"* — presented as two alternative ways to power the *same* unit, not two different
  power domains). It is reasonable to expect the USB HOST port is live whenever the unit is powered by either method,
  since it is a normal-operation peripheral port, not a debug-only port — but this is an inference from the manual's
  overall power architecture, **not a directly stated fact**, and should be verified on a real unit under PoE power
  with a multimeter/USB load tester before relying on it (see §3 "what to measure").
- **USB 3.0 SuperSpeed downstream-port current baseline**: per the USB-IF USB 3.0 specification, a standard
  SuperSpeed downstream port is rated for up to 900 mA at 5 V (versus 500 mA for USB 2.0). This is general USB
  standards knowledge, not something independently re-fetched from the USB-IF spec document this pass — treat it as
  the generic ceiling a compliant USB 3.0 host port *should* support, not a Magewell-confirmed figure for this specific
  port.

### B. Mini-DIN-8 "PTZ+TALLY" port on the encoders

Source: [Mini-DIN8 to Tally (Mini-DIN8) + RS232 (DB9) Breakout pinout PDF](https://www.magewell.com/files/documents/Mini-DIN8%20to%20Tally%20(Mini-DIN8)%20+%20RS232%20(DB9)%20Breakout.pdf)
(re-fetched and rendered directly via `Read` this pass, 2026-09-09 — the `Read` tool parsed this specific PDF as
vector text without needing `pdftoppm`, unlike the larger raster-heavy manual PDFs). Cross-checked against the
[Pro Convert Encoders User Manual](https://www.magewell.com/files/documents/User_Manual/ProConvert_Encoder-UserManual_en_US.pdf)
(fetched 2026-09-09).

**Pin table (device's Mini-DIN8 male jack, "PTZ + TALLY" socket):**

| Pin | Signal | Description |
|---|---|---|
| 1 | DTR | Data Terminal Ready (OUTPUT), → RS232 leg |
| 2 | DSR | Data Set Ready (INPUT), → RS232 leg |
| 3 | TXD | Transmit Data (OUTPUT), → RS232 leg |
| 4 | GND | Ground — shared return for both breakout legs |
| 5 | RXD | Receive Data (INPUT), → RS232 leg |
| 6 | GPIO2/Matrix | Magewell 8×32 LED Matrix Display, or user-customized Tally **Program** output; drive current 20–30 mA |
| 7 | GPIO1/Tally | **Magewell Tally Light**, or user-customized Tally **Preview** output; drive current 20–30 mA |
| 8 | **PWR/VCC** | **Voltage: 5 V. Max load current: 100 mA.** |

**Physical pin layout** (from the pinout diagram, as drawn looking at the device's male Mini-DIN8 jack):

```
  6  7  8      <- top row
 3   4   5     <- middle row
   1   2       <- bottom row
```

This is the standard 8-pin mini-DIN arrangement (three rows of 3/3/2 pins in a D-shaped shell) — **pin 8 (VCC) sits at
the top-right**, **pin 4 (GND) sits in the middle of the middle row**.

**Tally Light power confirmation:** the pinout PDF's own footnote against GPIO1/Tally (pin 7) reads *"1. Magewell Tally
Light"*, i.e. pin 7 is the signal line that drives the OEM Tally Light accessory (part #99090), and the light itself
draws its power from the same jack's shared VCC (pin 8, 5 V/100 mA) and GND (pin 4) — there is no separate power feed
to the Tally Light. This matches the family manual's parts list: the HDMI Plus manual (`../magewell/models/pro-convert-hdmi-plus.md`)
lists *"Tally light #99090"* as included in the box, connected via the Mini-DIN-8 breakout cable.

**No standalone Tally Light datasheet was found.** Two guessed Magewell URLs (`/products/tally-light`,
`/accessory/tally-light`) both 404'd. A `WebSearch` for the part number surfaced only retailer listings (e.g.
[Eastwood Sound & Vision — Magewell Tally Light](https://www.eastwoodsoundandvision.com/magewell-tally-light), part
99090, no technical specs on the page beyond price/availability) and pointed back to the same pinout PDF as the only
source of electrical specs. **The Tally Light's own current draw is therefore `unknown`** beyond the port's overall
100 mA VCC budget and the 20–30 mA GPIO drive-current figure for the signal line that turns it on/off — no separate
"Tally Light draws X mA" figure exists in any fetched Magewell source. Cable length for the Tally Light accessory is
also `unknown` — not stated anywhere reached this pass.

**External-device power warning:** the encoder manual's *"Using Custom Tally Lights"* section (p. 39) states: *"Note
that the second you turn on the switch for this function, the Magewell tally light and LED matrix screen will no
longer be working."* This is a functional exclusivity warning (custom tally vs. OEM tally/matrix, both driven off the
same GPIO1/GPIO2 pins) — it is **not** a warning about drawing extra current from VCC, and no such warning about
powering third-party accessories from pin 8 exists anywhere in the encoder manual. The manual does not mention the fan
use case at all (unsurprising — it is not a documented use of the port).

### C. USB Type-B "+5V" port — confirmed power input only

Sources: both manuals, fetched 2026-09-09.

- Decoder manual, Connections (p. 10): *"For power supply: connect the other end of the USB cable to the power
  adapter."* — the USB-B cable's *other* end goes to a wall adapter; the port only ever receives power, never sources
  it.
- Decoder manual FAQ (p. 77): *"How to supply power to the Pro Convert — There are 2 ways to power your decoder... 1.
  Via USB: Plug in the supplied 5V power adapter via the USB cable to supply power. 2. Via PoE..."*
- Decoder manual FAQ (p. 77) and encoder manual FAQ (p. 58), identical wording in both: *"Pro Convert devices require a
  5V DC source with a current rating of no less than 2.1A."* — stated as a *requirement placed on the external
  adapter*, i.e. an input spec, not an output capability.
- No sentence in either manual describes the USB-B port sourcing 5 V under any condition (PoE-powered or otherwise).

This confirms the fixed assumption already recorded in `poe-splitters.md`: *"The device's USB Type-B port is a power
input only — it cannot be used to source 5 V for the fan when the device is PoE-powered."*

### D. PoE pass-through / parallel-tap feasibility

**Why a second load can't simply be wired in parallel with the device's own PoE input:**

IEEE 802.3af/at (and the newer 802.3bt) architecture requires a Powered Device (PD) to present a specific detection
signature (a resistive signature in a defined range, historically ~25 kΩ for the classic detection probe) before a
Power Sourcing Equipment (PSE) port — the PoE switch or injector — will apply full power to that port at all. This
detection/classification handshake happens once, for the port, and is designed around **one PD identity per PoE link**.
The Magewell Pro Convert devices are ordinary single-signature PDs (they present one PD controller on one pair-set) —
there's no path to attach an independent second load in parallel on the same wire pairs and have the PSE recognize and
power it as a *separate* load; the PSE either sees the combined parallel load as one (usually invalid/out-of-spec)
resistive signature and refuses to enable power at all, or — on non-compliant "passive PoE" injectors that don't do
real detection — blindly applies power to whatever is connected, which is a different (and less safe/standard) class
of product than a proper 802.3af/at switch port.

The one standards-sanctioned way to power two logically separate loads from a single PoE-capable cable is the 802.3bt
**Dual-Signature PD (DSPD)** mechanism, where the *downstream device itself* implements two independent PD controllers
on the two conductor pair-sets (Mode A / Mode B), each separately detected and classified by the PSE. This requires
the device to be designed for it from the factory — it is not something that can be added externally with a splitter,
and the Magewell Pro Convert devices are not documented as DSPDs (their datasheets describe single 802.3af/at PoE
input only).

**Practical consequence for this project:** a fan cannot be powered by tapping the incoming PoE cable in parallel with
the device's own PoE input. The only PoE-adjacent path that works is the one already documented in `poe-splitters.md`:
put a **full PoE splitter in front of the device** so the splitter itself is the sole PD on that Ethernet link, and
have the splitter's own 5 V/USB output Y-split to feed *both* the device's USB-B power-input port *and* the fan in
parallel — this works because, from the PSE's point of view, there is still only one PD (the splitter), and the
splitter does its own internal DC distribution downstream of that single PD negotiation.

**Existing commercial products found (from `poe-splitters.md`, re-cited, not re-fetched this pass):** none of the
candidates fetched are marketed specifically as a "PoE pass-through splitter for powering an accessory in parallel with
a downstream PD" — they are all standard splitters (single PD, Ethernet-in / 5V-DC-out-plus-Ethernet-out), which is the
correct category for the Y-split approach above, not a "tap" category. Fetched and reachable this pass (2026-09-07,
`poe-splitters.md`): UCTRONICS U6115 (802.3af, 5 V/2.4 A, USB-C), UCTRONICS U6114 (802.3at, 5 V/4 A, barrel),
UCTRONICS U5259 (802.3at, 5 V/4 A, barrel), Ubiquiti INS-3AF-USB (802.3af, 5 V/2 A, USB-A, gigabit data-rate
**unconfirmed**), PoE Texas GAT-USBC (802.3at, USB-C PD up to 5 V/3 A, separate gigabit data port), PoE Texas GAF-USB
(802.3af, 5 V/2 A, barrel+adapters), Planet POE-161S (802.3at, 5 V/4.5 A or 12 V/2 A DIP-switch selectable). See
`poe-splitters.md` for full detail, dimensions, and sourcing caveats — not repeated here to avoid duplicating that
document. This pass additionally searched specifically for a **Tycon Systems** product matching the ticket's named
brands: Tycon's **POE-PowerTap-BT** and the generic **POE-PowerTap** family are PoE→wire-terminal splitters (up to
90–105 W depending on model, 802.3af/at/bt or passive input) — again standard splitters, not a parallel-tap-alongside-
a-downstream-PD product; a **POE-INJ-SPLT-G** (2.5 A Gigabit PoE injector *and* splitter) also exists from Tycon but
combines an injector and a splitter as separate functions in one product line, not a simultaneous dual-load tap.
**No commercial "PoE pass-through splitter that also powers a small accessory in parallel with a downstream PD" was
found under any of the five named brands (Ubiquiti, PoE Texas, Tycon, Planet, Microchip) — treat this as `unconfirmed`
rather than `does not exist`, since this was a targeted `WebSearch`/`WebFetch` pass, not exhaustive.**

---

## 3. Recommendation for the 0.07 A fan

| Family | Recommended port | Risk | What to measure on a real unit |
|---|---|---|---|
| **NDI decoders** (NDI to HDMI, NDI to HDMI 4K, NDI to SDI) | **USB HOST (Type-A)** | No Magewell-documented current rating exists for this port — the 900 mA USB 3.0 baseline is a generic spec assumption, not a confirmed figure for this specific implementation. The fan's 0.07 A max draw is a small fraction of even a conservative estimate, so headroom is very likely adequate, but this is unverified. | Multimeter or USB power-meter inline on the USB HOST port, with the device powered via PoE only (no USB-B adapter connected), confirm: (a) the port is live at all under PoE, (b) it delivers a clean, stable 5 V under the fan's ~70 mA load, (c) no current-limiting/overcurrent protection trips at that load. |
| **NDI to AIO** | **None of the above** — this model has no USB HOST port at all. Fall back to the encoder-style approach only if this device also has a Mini-DIN-8 port (it does not — AIO is a decoder, no PTZ+TALLY port either, per the decoder manual's interface diagrams). This decoder variant has **no on-device port** documented as a fan power source under PoE. | — | Confirm no undocumented header/pad exists inside the case before ruling this out entirely; otherwise the PoE-splitter route (§D) is the fallback for this specific model. |
| **Encoders** (HDMI/SDI Plus, HDMI/SDI 4K Plus, HDMI/SDI TX) | **Mini-DIN-8 "PTZ+TALLY" pin 8 (VCC)** | **Current budget is tight**: pin 8 is rated **100 mA max total**, and the port is also expected to supply the Tally Light (draw `unknown`, see §B) and/or the LED matrix accessory when those are in use. The fan's 0.07 A (70 mA) leaves only 30 mA of headroom against the 100 mA ceiling if nothing else draws from VCC — **and if the Tally Light or matrix display is also connected and drawing any meaningful current, the combined load will exceed the port's rated 100 mA.** This is the single biggest risk identified in this research: **do not assume the fan and the Tally Light can coexist on this port without measuring the Tally Light's actual draw first.** Also note GPIO1/GPIO2 (pins 6/7) are separate signal pins rated 20–30 mA each and are not usable as a power source — only pin 8 (VCC) is. | Multimeter across pin 8 (VCC) and pin 4 (GND) at the Mini-DIN8 breakout, under PoE power, both with and without the Tally Light connected, to get its actual current draw and confirm the rail voltage holds under the fan's added load. If the fan is added, the Tally Light likely needs to be omitted (or independently powered) to stay under 100 mA — this is a real design trade-off, not just a measurement exercise. |
| **All families, if the on-device port proves inadequate** | **Full PoE splitter ahead of the device**, per the existing `poe-splitters.md` design (Y-split the splitter's own 5 V output to the device's USB-B input and the fan) | Adds a component to the reserved PoE-splitter bay (already accounted for in the case's fixed decisions) and a second cable run; increases total system current draw on the splitter, which `poe-splitters.md` already flags as tight (~2.15 A combined against some candidates' ~2.4 A rating). | N/A — this path doesn't depend on the device's own ports at all; it was already researched in `poe-splitters.md`. |

**Overall:** the **decoder USB HOST port is the lower-risk candidate** of the two on-device options — it has no
documented competing load (nothing else in the manual claims to draw power from it) and a generically much larger
current budget than the encoder's Mini-DIN8 VCC pin, even though its exact rating for this device is unconfirmed. The
**encoder Mini-DIN8 VCC pin is a real risk** because its 100 mA ceiling is Magewell-documented and tight, and the port
is explicitly shared with the Tally Light in the stock configuration. Both paths require physical measurement before
being finalized in a case design — see the table above.

---

## 4. Open questions

- **USB HOST port actual current limit** (all three decoder models that have it): not stated anywhere in Magewell's
  documentation. Needs either a multimeter/USB-power-meter measurement on a real unit, or confirmation from Magewell
  support.
- **USB HOST port powered state under PoE vs. USB-B power**: not explicitly stated; inferred likely-yes from the
  manual's power architecture description, not confirmed. Needs physical verification.
- **Magewell Tally Light (#99090) actual current draw**: no datasheet found (two guessed product-page URLs both 404'd,
  web search surfaced only retailer listings with no electrical specs). This number is required to know how much
  headroom is actually left on the encoder's Mini-DIN8 VCC pin if the fan and the stock Tally Light are meant to
  coexist.
- **Tally Light cable length**: not found in any source reached this pass.
- **Whether any commercial PoE product exists that is specifically marketed as a "pass-through with parallel accessory
  tap"** (as opposed to a plain single-PD splitter): searched under the five ticket-named brands (Ubiquiti, PoE Texas,
  Tycon, Planet, Microchip) and not found — but this was a targeted search, not an exhaustive one; treat as
  `unconfirmed` rather than a confirmed absence.
- **Whether the encoder's GPIO1/GPIO2 pins could be repurposed** (e.g. as a PWM-style on/off signal for a
  transistor-switched fan circuit rather than a direct power feed) is a possible design alternative not explored in
  this pass — it stays within the 20–30 mA signal-pin rating rather than the 100 mA VCC pin, which could avoid the
  Tally Light contention entirely, but requires additional switching circuitry outside the scope of this research.

---

## 5. Sources

**Fetched and rendered successfully this pass (2026-09-09), via `WebFetch` (binary PDF saved) + `Read` (PDF content
rendered):**
- [Pro Convert Decoder Family User Manual](https://www.magewell.com/files/documents/User_Manual/ProConvert_Decoder-UserManual_en_US.pdf) — USB HOST port description (§A), power-input FAQ (§C), AIO no-USB-host confirmation.
- [Pro Convert Encoders User Manual](https://www.magewell.com/files/documents/User_Manual/ProConvert_Encoder-UserManual_en_US.pdf) — Mini-DIN8 port labelling, custom-tally-light exclusivity note, power-input FAQ (§C).
- [Mini-DIN8 to Tally (Mini-DIN8) + RS232 (DB9) Breakout pinout PDF](https://www.magewell.com/files/documents/Mini-DIN8%20to%20Tally%20(Mini-DIN8)%20+%20RS232%20(DB9)%20Breakout.pdf) — full pin table, VCC voltage/current, physical pin-position diagram, Tally Light footnote.

**Fetched this pass, no useful content (404s):**
- `https://www.magewell.com/products/tally-light` — 404.
- `https://www.magewell.com/accessory/tally-light` — 404.

**`WebSearch` results used (2026-09-09):**
- Search "magewell tally light 99090 specifications voltage" — confirmed no independent Tally Light datasheet exists beyond the pinout PDF; surfaced [Eastwood Sound & Vision — Magewell Tally Light](https://www.eastwoodsoundandvision.com/magewell-tally-light) (price/part-number only, no specs).
- Search `"magewell" "tally light" cable length connector datasheet` — no cable-length figure found anywhere.
- Search "PoE pass-through splitter secondary low power tap Tycon Ubiquiti pass-through" — surfaced Tycon Systems POE-PowerTap-BT, POE-PowerTap, POE-INJ-SPLT-G (all standard splitters/injectors, not parallel-tap products).
- Search "Microchip PoE PD single detection signature per port application note..." — confirmed the 802.3bt Dual-Signature PD (DSPD) mechanism is the only standards-sanctioned way to power two loads off one PoE link, and that it requires the downstream device itself to implement two PD controllers (not retrofittable via an external splitter). Surfaced [Microchip Developer Help — PoE Dual Signature Classifications](https://developerhelp.microchip.com/xwiki/bin/view/applications/ethernet/poe/dspd-classification/) as the explainer source.

**Re-cited from this repo's existing knowledge base, not re-fetched this pass (original fetch date 2026-09-07):**
- `../components/poe-splitters.md` — full PoE splitter candidate table (UCTRONICS, Ubiquiti, PoE Texas, Planet), device power-input figures, and the existing Y-split design recommendation for splitter + fan + device.
- `../components/mini-din8-feedthrough.md` — Mini-DIN8 pinout table (first sourced there, cross-checked and re-confirmed by this pass's own fresh PDF fetch), Tally Light part-number cross-reference.
- `../magewell/models/pro-convert-for-ndi-to-hdmi.md`, `../magewell/models/pro-convert-hdmi-plus.md` — device port-layout summaries, box contents (Tally Light #99090 included with Plus-tier encoders).
- `../magewell/sources.md` — canonical list of manual/datasheet URLs for this device family.

**Not independently re-verified this pass (general standards knowledge, not Magewell-specific):**
- USB 3.0 SuperSpeed downstream-port 900 mA / USB 2.0 500 mA baseline current — standard USB-IF specification figures, well-established industry knowledge; not re-fetched from the USB-IF spec document itself this pass.
- IEEE 802.3af/at single-PD-per-port detection/classification architecture, and the 802.3bt Dual-Signature PD mechanism — standard PoE architecture facts, corroborated by the Microchip developer-help search result above rather than a fetched IEEE standards document (which is paywalled).
