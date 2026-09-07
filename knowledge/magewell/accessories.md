# Magewell Pro Convert — Accessories

Official Magewell accessories relevant to case/mount design. Fetched 2026-09-07 (see `sources.md`).

## No official case exists

Magewell does not sell a carrying case, pouch, DIN-rail clip, wall plate, or protective enclosure
for any Pro Convert unit. The only enclosures found are third-party foam inserts (inlay-shop.de).
The **Fishtail Bracket** geometry — a 1/4"-20 boss plus a side anti-rotation hole on the unit — is
the closest thing to an official mechanical-interface reference and is the target to stay
compatible with for any custom case/mount design.

## L-bracket (in the box)

- Part **#92240**. Ships in the box with most Pro Convert TX/Plus encoders and NDI decoders.
- No published dimensions.
- Mates to the device's single 1/4"-20 threaded mounting hole (e.g. as documented on the HDMI TX
  datasheet: https://www.magewell.com/static/tech-specs/Pro_Convert/ProConvertHDMI_TX.pdf).

## Fishtail Bracket — official, free, 3D-printable

- Installation guide (PDF, vector — not text-extractable):
  https://www.magewell.com/files/documents/Fishtail-Bracket/Installation-Guide-for-the-Fishtail-Bracket.pdf
- STL file (confirmed live, ≈46.8 KB):
  https://www.magewell.com/files/documents/Fishtail-Bracket/3D-Printing-File-of-Fishtail-Bracket.stl
- **Kit contents:** 1× fishtail bracket, 2× M4×12 screws, 2× M4 nuts.
- **Shape/fit:** Y-shaped plate. One end screws to the device's 1/4"-20 boss plus a side
  anti-rotation hole; the other end bolts to a VESA pattern, monitor-cradle holes, a TV back, or
  rack rails (horizontal or vertical orientation).
- On the newer IP-decoder-generation units (e.g. Pro Convert IP to HDMI, SKU 64430,
  120 × 79.3 × 24.5 mm) the bracket ships **in the box** as part **STR00211**, together with
  **PAR10040** (thumbscrew-adapter fasteners), **MECO0067** (M4×12 black screws ×2), and
  **MECO0068** (M4 nuts ×2).

## Rack mounting kits

Source: https://www.magewell.com/accessory/rackmount

| Kit | SKU | Contents | Compatible models |
|---|---|---|---|
| Ultra Encode Mounting Kit | ACC10011 | 1 bracket, 2× M3×5 countersunk, 4× M3×6 knurled | Ultra Encode HDMI/SDI (Plus) |
| Pro Convert TX Mounting Kit | ACC10012 | 1 bracket, 1 D-ring 1/4" screw, 4× M3×6 knurled | HDMI TX, SDI TX, NDI to HDMI, NDI to AIO, NDI to SDI |
| Pro Convert Plus Mounting Kit | ACC10013 | 1 bracket, 1 D-ring 1/4" screw, 4× M3×6 knurled | HDMI 4K Plus, HDMI Plus, 12G SDI 4K Plus, SDI 4K Plus, SDI Plus, NDI to HDMI 4K |

No bracket dimensions or hole patterns are published for ACC10011/12/13.

**Not compatible:** Pro Convert AES67 and Audio DX (despite sharing the same 100.9 × 60.2 × 23.3 mm
chassis as the ACC10012-compatible TX/NDI models) are explicitly **not compatible** with the
ACC1001x rack kits.

## 1RU shelves

| Product | SKU | Dimensions |
|---|---|---|
| 1RU Rackmount Shelf, 4.7" deep | PAR10209 | 483 × 45 × 121 mm |
| 1RU Rackmount Shelf, 9.8" deep | PAR10210 | 483 × 45 × 251 mm |

Round + rounded-rectangle hole patterns are used on these shelves. "Up to 5 units per shelf" is a
third-party claim, not stated on Magewell's own page — treat as unverified.

## Modator 2U (rack chassis) — NOT compatible with boxed Pro Convert units

- SKU **B52200000T**.
- Product page: https://www.magewell.com/products/modator-2u
- Tech specs: https://www.magewell.com/tech-specs/modator-2U
- Manual: https://www.magewell.com/files/documents/User_Manual/Modator_2U_User_Manual_en_US.pdf
- **10 hot-swap slots for special "Module" SKUs only**: Pro Convert for NDI to AIO/HDMI/HDMI 4K
  Module, HDMI 4K Plus Module, HDMI Plus Module, 12G SDI 4K Plus Module, IP to AIO 4K Module, Ultra
  Encode modules. **Standard retail Pro Convert boxed units do not fit this chassis.**
- Chassis: 482 × 275 × 88 mm, 2U, ≈5.6 kg.
- Power: dual hot-swap PSU, 100–240 V AC input; internal DC distribution to modules (not PoE);
  20 W max per slot, 200 W total.
- Operating temperature: 0–50 °C.

## Summary table

| Accessory | SKU(s) | Applies to |
|---|---|---|
| L-bracket | 92240 | Most Pro Convert TX/Plus encoders and NDI decoders (in box) |
| Fishtail Bracket | (STL only, no SKU) / STR00211 + PAR10040 + MECO0067 + MECO0068 on IP-decoder-generation units | Any unit with a 1/4"-20 boss + side anti-rotation hole; ships in box on the newer IP decoders |
| Ultra Encode Mounting Kit | ACC10011 | Ultra Encode HDMI/SDI (Plus) — not Pro Convert |
| Pro Convert TX Mounting Kit | ACC10012 | HDMI TX, SDI TX, NDI to HDMI, NDI to AIO, NDI to SDI |
| Pro Convert Plus Mounting Kit | ACC10013 | HDMI 4K Plus, HDMI Plus, 12G SDI 4K Plus, SDI 4K Plus, SDI Plus, NDI to HDMI 4K |
| 1RU Shelf, 4.7" | PAR10209 | Any unit placed on a shelf rather than rack-mounted directly |
| 1RU Shelf, 9.8" | PAR10210 | Same, deeper shelf |
| Modator 2U | B52200000T | Special "Module" SKUs only — **not** boxed retail Pro Convert units |
