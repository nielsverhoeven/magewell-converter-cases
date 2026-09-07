# etherCON (RJ45 / Ethernet, D-series)

All part numbers below use the standard D-series cutout — see `../d-series-cutout.md`. Flange
26 × 31 mm in all cases.

## Chassis (panel-mount) connectors

| Part | Description | Wiring | Mount | Panel thickness | Depth behind panel | Intermates with |
|---|---|---|---|---|---|---|
| **NE8FDP** | CAT5e feedthrough receptacle, D-shape, nickel | Feedthrough (internal RJ45-to-RJ45, accepts any standard RJ45 plug or NE8MC*) | Front or rear | max. 4 mm | **34.55 mm (front-mount)** / **36.3 mm (rear-fixed)** — see drawing ST-NE8FDP | NE8MC*, any standard RJ45 plug. Does **not** intermate with CAT6 cable connector NE8MC6-MO or NKE6S* cables |
| **NE8FDP-B** | Same as NE8FDP, black housing | Feedthrough | Front or rear | max. 4 mm | same as NE8FDP (housing color only difference; not independently re-verified) | same as NE8FDP |
| **NE8FDX-P6** | CAT6A D-shape panel connector, shielded, feedthrough, nickel | Feedthrough | Front (rear not stated) | not stated (unknown — open question) | not independently verified — expect similar to NE8FDP family (unknown — open question) | Intermateable with the existing etherCON CAT5 range (NE8MX/NE8MC*). Does **not** intermate with NE8MC6-MO or NKE6S* |
| **NE8FDX-P6-B** | Black variant of NE8FDX-P6 | Feedthrough | Front | unknown | unknown | same as NE8FDX-P6 |
| **NE8FDY-C6** | CAT6 D-shape chassis connector, IDC (gas-tight, tool-less) termination | IDC (**not** feedthrough) | Front or rear | max. 3 mm | not independently verified (unknown — open question) | Intermates **only** with NE8MC6-MO, NKE6S-*, and generic RJ45 connectors. 10 Gbit/s capable. IP65 when mated. Temp range −10 °C to +60 °C (narrower than the feedthrough parts) |
| **NE8FDY-C6-B** | Black variant of NE8FDY-C6 | IDC | Front or rear | max. 3 mm | unknown | same as NE8FDY-C6 |
| **NE8FDX-Y6 / NE8FDX-Y6-B** | Named in the request; **not individually fetched in this research pass**. By Neutrik's naming convention this is very likely a CAT6A IDC-terminated D-shape variant (parallel to how NE8FDY-C6 is the CAT6 IDC counterpart to NE8FDX-P6's feedthrough). **Do not treat this as confirmed** — verify directly at `https://www.neutrik.com/en/product/ne8fdx-y6` before use. |
| **NE8FDY-C6(-B)** | Listed above | | | | | |
| **NE8FAH** | Named in the request; **not fetched in this research pass** — verify at `https://www.neutrik.com/en/product/ne8fah`. Likely an IDC/keystone-style variant based on naming, but unconfirmed. |

## Mating cable connectors (for the internal patch cable inside the case)

| Part | Description | Cable OD range | Notes |
|---|---|---|---|
| **NE8MX** | RJ45 cable connector carrier for pre-assembled/field RJ45 plugs, nickel shell, lockable | 4.5–8 mm | CAT5e-class; mates with NE8FDP/NE8FDX-P6 family |
| **NE8MX6** | CAT6A self-termination cable connector, chuck-type strain relief | 7.0–9.5 mm | Does **not** intermate with NE8FDY-C6/-B. For cable insulation OD ≤ 1.1 mm use NE8MX6-T instead. Wire gauge AWG24/1–AWG22/1 (solid) or AWG24/7–AWG22/7 (stranded) |
| **NE8MC6** | Referenced in the request as a mating part for CAT6 IDC chassis; direct product-page fetch returned HTTP 404 in this pass (part-number/URL slug may differ, e.g. **NE8MC6-MO** is the confirmed cross-referenced part name seen on NE8FDY-C6's own page as its intermating cable connector). **Use NE8MC6-MO**, not "NE8MC6", based on cross-reference evidence. |
| **NE8MX-B** | Black housing variant of NE8MX | 4.5–8 mm (assumed, not independently re-verified) | |

## Electrical / mechanical (NE8FDP, representative of the feedthrough family)

- Rated current per contact: 1.5 A; rated voltage ≤ 57 V
- CAT5e per TIA/EIA 568A/B and ISO/IEC 11801 (NE8FDP); CAT6A 10 Gbit/s (NE8FDX-P6); CAT6 10 Gbit/s
  (NE8FDY-C6)
- PoE: Type 4 Class 8 (100 W) per IEEE 802.3bt on all three families
- Shell: zinc diecast (ZnAl4Cu1), nickel-plated; insert PBTP 15% GR (NE8FDP) / polycarbonate
  (NE8FDY-C6)
- Lifetime > 1000 mating cycles; UL 94 V-0
- Temperature: −30 °C to +80 °C (NE8FDP feedthrough family) vs. −10 °C to +60 °C (NE8FDY-C6 IDC
  family) — **note the narrower range on the IDC part** if the case will see outdoor/cold use.

## IP rating

- NE8FDP (feedthrough): no explicit IP rating stated on its datasheet page fetched.
- NE8FDY-C6 (IDC): **IP65 in mated condition**.
- General etherCON D-series parts reach higher IP ratings only when paired with the correct sealing
  boot/cap accessory (see `blanking-and-caps.md` for SCDX-style covers, used unmated).

## Downloads

- NE8FDP: datasheet `https://www.neutrik.com/en/product/ne8fdp.pdf`; technical drawing (PDF)
  `https://www.neutrik.com/media/8668/download/ne8fdp-3.pdf?v=1`; DXF
  `https://www.neutrik.com/media/12095/download/ne8fdp-4.dxf?v=1`; STEP
  `https://www.neutrik.com/media/12094/download/30010088_-_NE8FDP.stp?v=2`
- NE8FDX-P6 / NE8FDY-C6: see `https://www.neutrik.com/en/product/ne8fdx-p6` and
  `https://www.neutrik.com/en/product/ne8fdy-c6` for their own download links (not individually
  captured in this pass).

## Price class

Not gathered in this research pass (no distributor pricing data was retrieved). Open question —
check Mouser/Digi-Key/Full Compass listings directly.

## Open questions

- NE8FDX-P6 and NE8FDY-C6 exact depth-behind-panel (no dimensioned drawing fetched — only the
  NE8FDP drawing was read in full).
- Confirm NE8FDX-Y6 and NE8FAH actual descriptions/specs (named in the original request but not
  fetched here).
- Confirm exact mating part name/number for the "NE8MC6" reference (evidence points to NE8MC6-MO).
