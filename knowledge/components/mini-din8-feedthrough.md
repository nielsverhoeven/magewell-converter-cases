# Mini-DIN8 "PTZ+TALLY" port — panel feedthrough options

Research for making the Magewell Pro Convert encoders' Mini-DIN8 female "PTZ+TALLY" jack
accessible on the outside of a 3D-printed case whose other connectors are all black Neutrik
D-size parts (26×31 mm flange, ⌀24 mm hole, M3 screws at ±9.5/±12 mm diagonal — see
`../neutrik/d-series-cutout.md`).

**Research date: 2026-09-07.** This pass had **no WebSearch budget available** (the session's
WebSearch quota was already exhausted before this task started) and relied entirely on WebFetch
against known/guessed URLs. A large fraction of the usual distributor catalog (Digikey, Mouser,
Farnell/Newark, TME, Conrad, RS Components, Octopart, Amazon search pages, Kycon's own site,
Hirose's own site, Lumberg/Bulgin's own site) returned 403/404/timeout/cert errors or rendered
only client-side-JS navigation chrome with no product data. Where this happened the gap is called
out explicitly and marked `unknown` rather than filled with a remembered/estimated figure. See
**Sources** at the end for the full list of attempted and blocked URLs.

The one genuinely high-value fetch that fully succeeded is the Magewell breakout-cable pinout
itself (§0) — this changes the shape of the whole downstream analysis (see §C), so read it first.

---

## 0. What the Mini-DIN8 jack actually carries (pinout)

Fetched directly from Magewell's own pinout diagram PDF:
[Mini-DIN8 to Tally (Mini-DIN8) + RS232 (DB9) Breakout](https://www.magewell.com/files/documents/Mini-DIN8%20to%20Tally%20(Mini-DIN8)%20+%20RS232%20(DB9)%20Breakout.pdf)
(fetched 2026-09-07; WebFetch could not render the PDF as text, but the Read tool rendered the
page image and the table was transcribed directly from it).

| Mini-DIN8 male pin (device jack) | Signal | Description | Goes to |
|---|---|---|---|
| 1 | DTR | Data Terminal Ready (OUTPUT) | DB9 pin 4 |
| 2 | DSR | Data Set Ready (INPUT) | DB9 pin 6 |
| 3 | TXD | Transmit Data (OUTPUT) | DB9 pin 3 |
| 4 | GND | Ground — **shared return for both breakout legs** | DB9 pin 5 **and** DIN8-female pin 4 |
| 5 | RXD | Receive Data (INPUT) | DB9 pin 2 |
| 6 | GPIO2 / Matrix | Purpose 1: Magewell 8×32 LED Matrix Display. Purpose 2: user-customized Tally **Program** output, drive current 20–30 mA | DIN8-female pin 6 |
| 7 | GPIO1 / Tally | Purpose 1: Magewell Tally Light. Purpose 2: user-customized Tally **Preview** output, drive current 20–30 mA | DIN8-female pin 7 |
| 8 | PWR / VCC | 5 V, max load current 100 mA | DIN8-female pin 8 |

DB9 (RS232, "PTZ" leg): pins 1/7/8/9 not connected. DIN8-female ("TALLY" leg): pins 1/2/3/5 not
connected.

**All 8 physical pins of the device's Mini-DIN8 jack are used** — there is no spare pin. This is
the single most important fact for evaluating Option C below: Neutrik's largest D-shape XLR is
7-pole, one pin short of the full signal set.

---

## A. Panel-mount Mini-DIN8 female sockets

| Part | Vendor status this pass | Mounting | Panel hole ⌀ | Panel thickness | Depth behind panel | Termination | Color | Price class |
|---|---|---|---|---|---|---|---|---|
| Kycon KMDG-8S / KMDGX-8S | **Not reachable.** `kycon.com` returned a TLS certificate-verification failure on every attempt (https and http, several URL paths). No page content obtained. | unknown | unknown | unknown | unknown | unknown | unknown | unknown |
| CUI MD-80PL100 / MD-80SM | **Partially reachable.** CUI Devices has rebranded to **Same Sky Devices**; `cuidevices.com` product/PDF URLs 301-redirect to `sameskydevices.com`, but the redirected product page rendered as the site's generic homepage (no spec table), and the guessed PDF datasheet path 404'd. Product may have been delisted/renumbered in the rebrand. | unknown | unknown | unknown | unknown | unknown | unknown | unknown |
| Hirose TCS series | **Partially reachable.** `hirose.com` series/category pages loaded but rendered only navigation chrome, no per-part spec table. | unknown | unknown | unknown | unknown | unknown | unknown | unknown |
| Lumberg 0301 08 / KFV 81 | **Not reachable.** `lumberg.com` 302-redirects to its own bare root domain with no product content (brand may have been absorbed/restructured). | unknown | unknown | unknown | unknown | unknown | unknown | unknown |
| Amphenol / Switchcraft | **Not reachable.** Switchcraft's DIN-connector catalog page rendered empty; Amphenol's redirected circular-DIN category page returned 403 Forbidden. No evidence found either way that either brand makes an 8-pin mini-DIN chassis part — absence of evidence, not evidence of absence. | unknown | unknown | unknown | unknown | unknown | unknown | unknown |
| Generic "mini-DIN 8-pin female panel-mount solder" (AliExpress market) | **Reachable — listing level only.** Search-results page rendered fine; individual product pages are client-rendered (JS) and returned only site-chrome/footer content, so no per-part mechanical dimensions could be extracted. | unknown (typical generic mini-DIN shells are known to mount through a round hole well under 24 mm, since the mini-DIN plug itself is only ~13.2 mm OD, but no sourced figure was obtained this pass) | unknown | unknown | unknown | "solder terminals" (per listing titles; solder-cup vs. solder-lug not distinguished) | Mostly metal-shell/nickel per listing photos; black not confirmed | **€1.22 – €4.56** per piece/set, multi-pin (3–8 pole) listings — [search page](https://nl.aliexpress.com/w/wholesale-mini-din-8-pin-panel-mount-female.html), fetched 2026-09-07 |

**Net assessment for A:** existence of both branded and generic panel-mount Mini-DIN8 female
sockets is well established (all five brands are real, known mini-DIN connector manufacturers, and
the generic market clearly has 8-pin DIN panel sockets in stock), but **no mechanical drawing
(hole diameter, panel-thickness rating, depth-behind-panel) could be independently verified for
any specific part in this pass.** Before finalizing a design around this option, either (a) get a
distributor to email/host the datasheet directly, or (b) buy a physical sample and measure it. As
a sizing baseline only (not sourced, for rough space planning): a standard mini-DIN shell is
~13.2 mm mating-face diameter, so it fits comfortably inside a 24 mm D-size hole with plenty of
margin for a custom insert plate (see Option D/recommendation).

---

## B. Mini-DIN8 male-to-female extension / feedthrough cables

| Item | Finding | Source |
|---|---|---|
| Purpose-built Mini-DIN8 M–F extension cable, 0.15–0.5 m | **Not confirmed to exist as a stocked product.** AliExpress search for this exact description surfaced only one 8-pin mini-DIN cable product, and it is not an M–F extension — it's a factory RS232-DB9-female-to-Mini-DIN8-male cable for Delta PLC programming (length not stated, €7.89). | [nl.aliexpress.com/item/1005009077404578.html](https://nl.aliexpress.com/item/1005009077404578.html), fetched 2026-09-07 |
| Mini-DIN8 panel-mount feedthrough cable (female panel jack + pigtail male plug, one integrated part) | **No such product found.** Every Mini-DIN8 female panel-mount part found (§A) is a bare connector requiring separate internal wiring, not a combined jack+pigtail assembly like Neutrik's etherCON/HDMI/USB/BNC "feedthrough" family used elsewhere in this case. | — |

**Practical substitute (design reasoning, not a sourced product):** since no purpose-built
ultra-short extension exists, the internal pigtail can instead be made from **any longer stock
Mini-DIN8 M–F cable, cut down** — discard the molded female end, keep the factory-molded male plug
(safer/more reliable than hand-crimping loose mini-DIN pins) with its integral 8-conductor cable,
and hand-solder the raw wire ends onto whichever panel connector's terminals are chosen (§A's
solder-cup/PCB-pin sockets, or, for Option C, the XLR's solder cups). This avoids needing an
exact-length commodity product to exist.

---

## C. Neutrik D-size XLR as the panel connector

### C.1 Chassis (panel) connectors — confirmed

| Part | Pins | Type | Termination | Color | Panel cutout | Depth behind panel | Source |
|---|---|---|---|---|---|---|---|
| **NC7FD-L-B-1** | 7-pole | Female receptacle, chassis/panel mount | Solder cups | Black metal housing, gold contacts | Standardized D-size 24 mm (shared with every other D-series part, see `../neutrik/d-series-cutout.md`) | Not stated on this product's own page; **21.7 mm** by analogy to the mechanically identical 3-pole "L" solder-cup D-family, per `../neutrik/placement-and-depth.md` (sourced from the official RS-Online-hosted XLR "D" series drawing) — not independently re-confirmed for the 7-pole shell this pass | [neutrik.com/en/product/nc7fd-l-b-1](https://www.neutrik.com/en/product/nc7fd-l-b-1), fetched 2026-09-07 |
| **NC5FD-L-B-1** | 5-pole | Female receptacle, chassis/panel mount | Solder cups | Black metal housing, brass/gold contacts | Standardized D-size 24 mm | Not stated on this product's own page; same ~21.7 mm estimate as above, same caveat | [neutrik.com/en/product/nc5fd-l-b-1](https://www.neutrik.com/en/product/nc5fd-l-b-1), fetched 2026-09-07 |

Both share the D-series general panel-thickness rating of **1–3 mm** (already sourced in
`../neutrik/d-series-cutout.md` from Neutrik's general D-series page) and the standard **26×31 mm
flange / M3 holes at ±9.5 / ±12 mm** cutout pattern.

Electrical/mechanical extras confirmed on the product pages: NC7FD-L-B-1 is rated 5 A/contact,
<50 V, latch-lock, IEC 61076-2-103, -30 to +80 °C, UL recognized. NC5FD-L-B-1 is rated
7.5 A/contact, <50 V, ≤20 N insertion force, >1000 mating cycles, IP40, -30 to +80 °C, UL 94 V-0.

### C.2 Mating cable connectors — confirmed

| Part | Pins | Color | Cable OD range | Notes | Source |
|---|---|---|---|---|---|
| **NC7MXX** | 7-pole male | Nickel housing | 3.5–8.0 mm | Latch lock, polyurethane boot, 5 A/contact, >1000 cycles, -30/+80 °C | [neutrik.com/en/product/nc7mxx](https://www.neutrik.com/en/product/nc7mxx), fetched 2026-09-07 |
| **NC7MXX-B** | 7-pole male | **Black** | 3.5–8.0 mm (assumed same shell as NC7MXX) | Confirmed to exist and in stock (31 units) via a retailer listing — Neutrik's own product-page URL for this exact slug 404'd in this pass, so its own datasheet wasn't independently re-fetched; price not captured | [thomann.co.uk search "neutrik NC7MXX"](https://www.thomann.co.uk/search_dir.html?sw=neutrik%20NC7MXX), fetched 2026-09-07 |
| **NC5MXX-B** | 5-pole male | Black metal + polyurethane boot | 3.5–8.0 mm | Gold contacts, max wire 1.0 mm² (18 AWG), 7.5 A/contact, >1000 cycles, -30/+80 °C | [neutrik.com/en/product/nc5mxx-b](https://www.neutrik.com/en/product/nc5mxx-b), fetched 2026-09-07 |

### C.3 Pin budget — the real constraint on this option

Per §0, the device's Mini-DIN8 jack uses **8 distinct signals** (GND, RXD, TXD, DTR, DSR,
GPIO1/Tally, GPIO2/Matrix, VCC). Neutrik's largest D-shape XLR is **7-pole** — one short of the
full set no matter what.

**7-pin XLR (NC7FD-L-B-1) — fits everything except one signal.** Suggested mapping (XLR pin 1 =
ground, following standard XLR convention):

| XLR pin | Signal | Mini-DIN8 source pin |
|---|---|---|
| 1 | GND (shared return) | 4 |
| 2 | RXD | 5 |
| 3 | TXD | 3 |
| 4 | GPIO1 / Tally-Preview | 7 |
| 5 | GPIO2 / Matrix-Program | 6 |
| 6 | PWR / VCC (5 V, ≤100 mA) | 8 |
| 7 | **DTR or DSR — pick one** | 1 or 2 |

**Open question — escalate to the user/architect, do not guess:** which of DTR/DSR (if either) to
carry on pin 7, or whether to drop both and leave pin 7 spare. Most PTZ camera RS-232 control
protocols (VISCA, Pelco) only use TXD/RXD/GND and ignore hardware flow control, which would make
either line safe to drop — but this depends on the specific PTZ device/protocol the user will
attach, which is outside what this research pass can verify. Getting this wrong silently breaks
PTZ control for any camera that does require hardware handshake.

**5-pin XLR (NC5FD-L-B-1) — does not fit the combined signal set.** Minimum signals needed to
preserve full bidirectional PTZ control (GND, TXD, RXD) **and** both tally states **and** the tally
light's own 5 V power (GND, GPIO1, GPIO2, VCC) is **6** unique conductors even after dropping both
DTR and DSR — one more than a 5-pole connector has. A 5-pin XLR only works if the design
deliberately drops something:
- Drop VCC → full PTZ (TXD/RXD) + both tally LEDs, but this port can no longer power Magewell's
  own Tally Light accessory (part #99090, see `../magewell/housing-families.md`) — an
  independently-powered tally light or an external relay would be needed instead, **or**
- Drop one of GPIO1/GPIO2 → full PTZ + tally-light power, but only one of Preview/Program tally
  states.

**Recommendation: use the 7-pin NC7FD-L-B-1, not the 5-pin, if this option is chosen at all** — the
5-pin only makes sense if the user explicitly confirms they don't need simultaneous full PTZ +
full tally + tally-light power through this one port.

### C.4 Custom wiring required (both cable assemblies are hand-built — no off-the-shelf part exists for either)

1. **Internal pigtail:** Mini-DIN8 male plug (inserted into the device's jack) → up to 7 discrete
   wires → hand-soldered onto the NC7FD-L-B-1's 7 solder cups inside the case. No commodity
   Mini-DIN8-to-XLR cable was found (or expected to exist) — build from a cut-down stock Mini-DIN8
   cable per §B's substitute technique, using only the male end.
2. **External adapter cable (for the user, outside the case):** 7-pin XLR male (NC7MXX-B, to mate
   with the panel's NC7FD-L-B-1) → hand-wired → a Mini-DIN8 **female** connector, so that the
   Magewell OEM breakout cable's own Mini-DIN8 **male** plug can be plugged into it. This is a
   second fully custom assembly, exactly as anticipated in the ticket.

This is materially more custom wiring than Option A (§A/§B), where the panel connector's outward
face already is a Mini-DIN8 female — the OEM breakout cable plugs straight in, no adapter needed.

---

## D. Neutrik D-size blanking plate — feasibility for a drilled/printed Mini-DIN hole

Already fully documented in this knowledge base from prior research; no new fetch was needed or
performed this pass. Full detail: `../neutrik/connectors/blanking-and-caps.md` and
`../neutrik/d-series-cutout.md`.

| Part | Flange | Thickness | Material | Mounting | Source (existing KB) |
|---|---|---|---|---|---|
| DBA-BL | 26.0×31.0 mm, R3.5 mm corners | 3.2 mm | PA6.6 (nylon) | Standard M3 holes at ±9.5/±12 mm | drawing "ST-DUMMY_COVER" — [neutrik.com/media/8479/download/dba-2.pdf](https://www.neutrik.com/media/8479/download/dba-2.pdf?v=1) |
| DBA-BL-B | Same as DBA-BL | Same | Same (assumed) | Same | Color variant, not independently confirmed to be mechanically identical (see existing KB open question) |

**Feasibility of drilling/redesigning this as a Mini-DIN carrier:** two ways to get there —

1. **Buy a genuine DBA-BL-B and machine a hole in it.** Feasible in principle (3.2 mm solid nylon
   is easy to drill/mill), but wastes the purchased part's own mounting-hole tolerances and adds a
   manufacturing step with no upside over option 2.
2. **Print a custom D-footprint insert plate instead of buying DBA-BL-B** (recommended, and the
   basis of the recommendation below): since the case wall is already 3D-printed, reproduce only
   the *geometry* that matters — outer flange 26×31 mm, M3 clearance holes at the standard
   ±9.5/±12 mm diagonal pattern (both dimensions already sourced in `../neutrik/d-series-cutout.md`)
   — with a **custom center hole sized to whichever Mini-DIN8 panel connector is sourced from §A**,
   instead of the connector's own 24 mm D-hole. This lets a non-Neutrik round connector sit in a
   panel opening that fastens with the exact same M3 screw pattern as every other port on the case,
   preserving the uniform look/fastening system even though the connector body itself isn't a
   genuine Neutrik part. No new sourcing risk beyond §A's own open questions (hole diameter for the
   specific connector chosen must still be measured/confirmed).

---

## E. Rubber-capped pass-through / cable gland

| Item | Clamping range | Color/material | Price class | Source |
|---|---|---|---|---|
| Generic PG7 cable gland, IP68 | **3–6.5 mm** (consistent across multiple listings) | Black nylon | €0.22 – €2.42 per piece (bulk packs) | [nl.aliexpress.com/w/wholesale-PG7-cable-gland-black.html](https://nl.aliexpress.com/w/wholesale-PG7-cable-gland-black.html), fetched 2026-09-07 |
| Generic M12 cable gland, waterproof | **4.5–7.8 mm** (one specific listing; other listings bundle M12/M16/PG7/PG9 threads together without a clean single M12-only range) | Black nylon | €4.47 – €15.63 depending on pack size/thread combo | [nl.aliexpress.com/w/wholesale-M12-cable-gland-black-waterproof.html](https://nl.aliexpress.com/w/wholesale-M12-cable-gland-black-waterproof.html), fetched 2026-09-07 |

Both PG7 (3–6.5 mm) and M12 (4.5–7.8 mm, per the one listing found) comfortably bracket the
ticket's own "~4 mm cable" estimate for the Magewell breakout cable. **That ~4 mm figure is the
ticket's estimate, not independently verified in this pass** — the breakout cable's actual outer
diameter is not stated anywhere in Magewell's own materials reached this pass (product page,
pinout PDF) and was not otherwise confirmed. If the true OD is smaller (a thin 4-conductor-class
cable is plausible given only ~8 fine conductors), PG7 is the safer/tighter-fitting default; if
closer to 6–7 mm, M12 keeps more margin.

**Authoritative brand-name sources attempted and failed** (403/404/cert errors, listed for
transparency — see Sources): Lapp SKINTOP (lappusa.com cert mismatch, lappgroup.com 404),
Wiska ESKY (404), Jacob GmbH (404), Hummel HSK-M (404), Essentra Components (403),
engineeringtoolbox.com PG-thread table (403), Wikipedia "PG thread" article (404 — no such page
exists under that exact title), RS Components cable-glands buying guide (no numeric table in the
rendered content). Body depth behind panel for any specific gland was **not obtained** in this
pass — only clamping range and rough price class are sourced.

**Design note:** a gland does not give a disconnectable port — the OEM Magewell breakout cable (or
whatever cable is chosen) becomes a permanent pigtail through the wall, can't be unplugged at the
panel, and the whole run must be assembled as one continuous cable from the device's jack to
wherever the tally/PTZ leads terminate outside. Strain relief is provided by the gland's own
clamp, not by a connector shell.

---

## Summary comparison

| Option | Robustness on stage | Fits the D-size grid | Custom wiring required | Space envelope behind panel (mm) |
|---|---|---|---|---|
| **A. Panel-mount Mini-DIN8 female** (branded or generic) in a printed D-footprint insert (see D.2) | Same as the OEM connector itself (friction/threaded-nut retention, no positive latch — a known general characteristic of mini-DIN connectors, not independently benchmarked against XLR in this pass) | Yes, if mounted in a printed D-footprint insert plate reusing the standard M3×19×24 mm pattern (§D.2) — the connector body itself is non-Neutrik | **Lowest** — one internal 8-wire 1:1 pigtail (Mini-DIN8 male → panel connector's cups/pins), no external adapter needed since the OEM breakout cable's own Mini-DIN8 male plug mates directly with the panel's female jack | `unknown` — no depth figure verified for any specific part this pass; budget for connector body + a short service loop pending physical measurement |
| **C. Neutrik 7-pin XLR-D (NC7FD-L-B-1)** | Highest — positive latch-lock, IP-rated contacts, the same mechanism as every other connector on this case | Yes — genuine Neutrik D-series part, identical cutout/flange/screw pattern as the rest of the panel | **Highest** — two hand-built cable assemblies (internal pigtail + external adapter), plus an unresolved pin-drop decision (DTR or DSR) that needs user/protocol confirmation | ~21.7 mm connector body (estimated by analogy, see §C.1) + NC7MXX-B mating-plug/cable-bend allowance (not sourced — treat like the rest of this KB's "estimated ~55-65mm total for feedthrough-style connectors" pattern in `../neutrik/placement-and-depth.md` §3, though NC7FD-L-B-1 is a solder-cup design, not a feedthrough, so no external mating plug sits behind the panel at all — only the internal hand-soldered pigtail's own bend radius matters) |
| **C. Neutrik 5-pin XLR-D (NC5FD-L-B-1)** | Same as 7-pin | Same as 7-pin | Same category as 7-pin, plus a forced functional compromise (§C.3) — **not recommended unless the user explicitly accepts dropping tally-light power or one tally LED** | Same order of magnitude as the 7-pin variant |
| **D. Blanking plate, undrilled** | N/A — port not accessible | Yes (genuine Neutrik part or a printed equivalent) | None | 3.2 mm (confirmed, DBA-BL) |
| **E. Cable gland pass-through** | Lower — no connector at the panel at all; cable is a permanent pigtail, no disconnect point for storage/transport | No — round grommet, not a D-shape cutout | **Low** — no signal remapping, but the OEM cable must be fed through and terminated as one continuous run (harder to service/replace than a connector) | `unknown` — gland body depth not sourced this pass |

## Recommendation, ranked

1. **Option A** (a genuine or generic panel-mount Mini-DIN8 female socket, mounted in a
   custom-printed D-footprint insert plate per §D.2) is the best overall trade-off: it needs the
   least custom wiring by a wide margin (one straight 8-wire pigtail, no external adapter, no
   signal-dropping decision), it can be made to sit in the same M3 screw pattern as every other
   port so the panel still reads as one consistent grid even though the connector body itself isn't
   Neutrik-branded, and its robustness is no worse than the device's own native connector. Its main
   weakness — no verified mechanical drawing for any specific branded part in this pass — is a
   sourcing/verification task, not a design blocker: order a sample of 2–3 candidate parts (start
   with the generic AliExpress listings, cheapest to test) and physically confirm panel hole
   diameter, panel-thickness capacity, and body depth before committing the case geometry.
2. **Option C, 7-pin (NC7FD-L-B-1)** is the right call only if stage-grade positive latching is a
   hard requirement that outweighs the extra build labor — it demands two custom cable assemblies
   and a resolved (not guessed) decision on which RS232 handshake line to drop. Do not use the
   5-pin variant unless the user has explicitly signed off on losing tally-light power or one tally
   LED.
3. **Option E** (cable gland) is the fallback if no Mini-DIN8 panel connector (branded or generic)
   can be sourced/verified in time — cheapest and simplest, but gives up disconnectability at the
   panel.
4. **Option D undrilled** is only the "leave it inaccessible" baseline; it does not satisfy the
   stated requirement that the PTZ/Tally port be available on the outside of the case, so it is not
   a real candidate on its own — it's referenced here only because its geometry is the basis for
   Option A's printed-insert approach.

## Open questions

- Which of DTR/DSR (if either) the chosen PTZ camera's RS-232 protocol actually requires — decides
  the pin-drop for Option C's 7-pin mapping (§C.3). Needs the specific camera/protocol, which is
  outside this research pass.
- Exact panel hole diameter, panel-thickness rating, and depth-behind-panel for any specific
  branded Mini-DIN8 panel-mount connector (Kycon, CUI/Same Sky, Hirose, Lumberg) or for a chosen
  generic AliExpress part — none could be confirmed via WebFetch this pass; needs a distributor
  contact, a fetched datasheet, or a physical sample.
- Actual outer diameter of the Magewell Mini-DIN8-to-Tally+RS232 breakout cable (the ticket's
  "~4 mm" is an estimate, not sourced) — determines whether PG7 or M12 is the better gland fit for
  Option E, and affects internal bend-radius planning for Options A/C.
- Whether NC7FD-L-B-1's/NC5FD-L-B-1's actual depth-behind-panel is really 21.7 mm (this pass only
  carries forward the existing KB's by-analogy estimate for the 3-pole L-family; the 5-/7-pole
  shells were not independently drawn).
- Whether the printed D-footprint insert idea (§D.2) actually clears mechanically for the specific
  Mini-DIN8 connector eventually chosen — depends on that connector's own panel-side bezel/nut
  diameter, which is part of the unresolved §A dimensions.

## Sources

**Fetched successfully:**
- [Magewell Mini-DIN8 to Tally + RS232 Breakout pinout PDF](https://www.magewell.com/files/documents/Mini-DIN8%20to%20Tally%20(Mini-DIN8)%20+%20RS232%20(DB9)%20Breakout.pdf) — full pin table (§0). WebFetch couldn't parse it as text; the cached PDF was rendered via the Read tool.
- [neutrik.com/en/product/nc7fd-l-b-1](https://www.neutrik.com/en/product/nc7fd-l-b-1) — NC7FD-L-B-1 full specs.
- [neutrik.com/en/product/nc5fd-l-b-1](https://www.neutrik.com/en/product/nc5fd-l-b-1) — NC5FD-L-B-1 full specs.
- [neutrik.com/en/product/nc7mxx](https://www.neutrik.com/en/product/nc7mxx) — NC7MXX (nickel) full specs.
- [neutrik.com/en/product/nc5mxx-b](https://www.neutrik.com/en/product/nc5mxx-b) — NC5MXX-B full specs.
- [thomann.co.uk search — "neutrik NC5FD-L-B-1"](https://www.thomann.co.uk/search_dir.html?sw=neutrik%20NC5FD-L-B-1) — nearest-match price ~£34 for the 5-pole black female family.
- [thomann.co.uk search — "neutrik NC7FD"](https://www.thomann.co.uk/search_dir.html?sw=neutrik%20NC7FD) — confirms NC7 FDL-B-1 is a stocked item (price not captured).
- [thomann.co.uk search — "neutrik NC7MXX"](https://www.thomann.co.uk/search_dir.html?sw=neutrik%20NC7MXX) — confirms both NC7MXX (nickel) and **NC7MXX-B (black)** exist and are stocked (price not captured).
- [nl.aliexpress.com — mini-din-8-pin-panel-mount-female search](https://nl.aliexpress.com/w/wholesale-mini-din-8-pin-panel-mount-female.html) — generic panel-mount socket price class (§A).
- [nl.aliexpress.com/item/1005009077404578.html](https://nl.aliexpress.com/item/1005009077404578.html) — RS232-DB9-to-MiniDIN8 cable example (§B).
- [nl.aliexpress.com — mini-din-8-pin-male-to-female-extension-cable search](https://nl.aliexpress.com/w/wholesale-mini-din-8-pin-male-to-female-extension-cable.html) — confirms no dedicated short M-F extension found (§B).
- [nl.aliexpress.com — PG7-cable-gland-black search](https://nl.aliexpress.com/w/wholesale-PG7-cable-gland-black.html) — PG7 clamping range and price class (§E).
- [nl.aliexpress.com — M12-cable-gland-black-waterproof search](https://nl.aliexpress.com/w/wholesale-M12-cable-gland-black-waterproof.html) — M12 clamping range and price class (§E).
- Existing repo knowledge, re-cited rather than re-fetched: `../neutrik/d-series-cutout.md`, `../neutrik/placement-and-depth.md`, `../neutrik/connectors/blanking-and-caps.md` (all sourced from official Neutrik drawings — see `../neutrik/sources.md` for the original URLs).

**Attempted and blocked/unparseable (for transparency):**
- kycon.com (all paths) — TLS certificate verification failure / connection timeout.
- cuidevices.com / sameskydevices.com product & PDF paths for MD-80PL100 / MD-80SM — 301 redirect to homepage or 404; CUI's rebrand to Same Sky appears to have broken these specific legacy URLs.
- hirose.com TCS series pages — loaded, no per-part spec table rendered.
- lumberg.com — 302 redirect to bare root domain, no content.
- switchcraft.com DIN catalog — empty render.
- amphenol-icc.com → amphenol-cs.com circular-DIN category — 403 Forbidden.
- digikey.com, mouser.com, tme.eu, farnell.com (nl), rs-online.com, conrad.com/.de, distrelec.nl, octopart.com, monoprice.com, startech.com, ebay.com, essentracomponents.com — all returned 403/404/timeout or client-rendered navigation-only content with no product data.
- lappusa.com — TLS hostname mismatch (cert for an unrelated domain). lappgroup.com SKINTOP product path — 404.
- jacob-gmbh.de, hummel.com, bulgin.com — 404 on guessed product paths.
- engineeringtoolbox.com PG-gland-size page — 403 Forbidden.
- en.wikipedia.org/wiki/PG_thread — 404 (no such article title).
- web.archive.org — blocked entirely for this tool ("Claude Code is unable to fetch from web.archive.org"), so archived snapshots of the above dead pages could not be used as a fallback.
- neutrik.com/en/product/nc7mxx-b — 404 on the direct product-page URL, despite the part demonstrably existing per the Thomann listing above; Neutrik's own URL slug for this specific part was not found in this pass.
