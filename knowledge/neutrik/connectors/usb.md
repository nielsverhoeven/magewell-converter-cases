# USB (D-series)

Uses the standard D-series cutout — see `../d-series-cutout.md`. Flange 26 × 31 mm.

## Chassis (panel-mount) connectors

| Part | Description | USB version | Mount | Depth behind panel | Rear connection |
|---|---|---|---|---|---|
| **NAUSB-W** | Reversible USB gender changer (type A and B on either end), nickel D-housing | USB 2.0 | Front only | **40.55 mm** (front flange face to rear tip — drawing ST-NAUSB-W) | Feedthrough adapter — internal patch cable plugs straight into the rear-facing USB port; no solder/IDC termination |
| **NAUSB-W-B** | Same as NAUSB-W, black housing | USB 2.0 | Front only | same as NAUSB-W (not independently re-verified) | Feedthrough |
| **NAUSB3** | Reversible USB 3.0 gender changer (type A and B), nickel | USB 3.0 | not fetched in detail — assume same front-only pattern as NAUSB-W (unconfirmed) | unknown — open question | Feedthrough (assumed) |
| **NAUSB3-B** | Same as NAUSB3, black D-housing | USB 3.0 | unknown | unknown | Feedthrough (assumed) |

## USB-C

**Neutrik does NOT offer a USB-C connector in the classic D-size chassis shape.** Their USB-C
product is a separate, newer connector system called **mediaCON®** (category:
`https://www.neutrik.com/en/neutrik/products/multimedia-connectors/usb-type-c`), described as
"push/pull lockable and space-saving," rated 10 Gb/s data and up to 100 W power delivery. This is a
**different housing/footprint, not a drop-in D-series part** — it will need its own cutout geometry
if used (a part number consistent with "NMK-20UC" was seen referenced in an image filename on
Neutrik's multimedia category page, but not independently confirmed as the definitive part number —
**open question**, verify directly on neutrik.com before designing around it).

**Recommendation for this project**: if USB-C is required, either (a) use a NAUSB-W/NAUSB3
(A/B, not C) feedthrough plus a short USB-C adapter cable outside the case, or (b) research the
mediaCON series separately as it is mechanically unrelated to everything else in this knowledge
base — do not assume it shares the 26×31 mm flange or 24 mm cutout.

## Mating cable connector

- **NKUSB-\*** — "USB 2.0 cable with overmolded flex relief and rugged metal [connector]" — referenced
  as the mating cable for NAUSB-W's IP65-in-mated-condition rating (used together with an
  **SCDP-\*** sealing gasket). Exact NKUSB-* suffix/part list not individually captured in this pass.

## Electrical / mechanical (NAUSB-W)

- IP65 ingress protection in mated condition with NKUSB-* cable and SCDP-* sealing gasket (unmated:
  lower, unrated without a cap — see `blanking-and-caps.md`)
- Contacts: bronze (CuSn), gold-plated; insert PVC; shell zinc diecast (ZnAl4Cu1), nickel-plated
- Lifetime > 1000 mating cycles; UL 94 V-0; temperature −25 °C to +85 °C
- Standard compliance: USB 2.0 specification

## Downloads

- Datasheet: `https://www.neutrik.com/en/product/nausb-w.pdf`
- Technical drawing (PDF): `https://www.neutrik.com/media/8974/download/nausb-w-2.pdf?v=1`
  (drawing ST-NAUSB-W)
- DXF: `https://www.neutrik.com/media/12188/download/nausb-w-3.dxf?v=1`
- STEP: `https://www.neutrik.com/media/16360/download/3D%20File%20NAUSB-W-A.stp?v=1`

## Price class

Not gathered in this research pass — open question.

## Open questions

- NAUSB3 (USB 3.0) exact depth-behind-panel and mount-direction options — not fetched.
- Exact mediaCON USB-C part number and whether it can be adapted to a D-series-style cutout, or
  needs an entirely separate cutout module.
- Exact NKUSB-* and SCDP-* suffix part numbers for the sealed cable/gasket combination.
- Panel thickness rating for NAUSB-W/NAUSB3 (not stated on the fetched datasheets).
