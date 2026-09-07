# Pro Convert for NDI to HDMI 4K

**Priority model for this project.**

## Identity
- SKU: 641100000
- Product page: https://www.magewell.com/products/pro-convert-for-ndi-to-hdmi-4k
- Datasheet: https://www.magewell.com/static/tech-specs/Pro_Convert/ProConvertforNDI_to_HDMI_4K.pdf
- Manual: https://www.magewell.com/files/documents/User_Manual/ProConvert_Decoder-UserManual_en_US.pdf
- QSG: https://www.magewell.com/files/documents/Quick%20Start%20Guide%20for%20Pro%20Convert%20Decoders.pdf

## Type / interfaces
NDI decoder — HDMI output up to 4K60 (decode 4Kp60, alpha channel supported); USB 3.0 Type-A host.

## Physical
- Housing family: [Plus](../housing-families.md#a-plus-1175--667--234-mm) — **note:** despite being
  part of the NDI-decoder product family (electronics/manual shared with NDI to HDMI/SDI/AIO), this
  model uses the larger Plus chassis, not the Compact/TX chassis used by the other three NDI
  decoders. Confirmed by ACC10013 "Pro Convert Plus Mounting Kit" compatibility list, which includes
  this model alongside the Plus-tier encoders.
- Dimensions: 117.5 × 66.7 × 23.4 mm
- Weight: unknown

## Port layout
- Face A: USB HOST (Type-A) → MENU toggle → HDMI OUT (+ decoding LED)
- Face B: USB-B "+5V" → RJ45 "NDI+PoE"
- Top, near Face B: Tally Preview LED, 16-position rotary switch, Tally Program LED (exact order uncertain)
- Top, near Face A: SD-card slot (non-functional) + 1/4"-20 hole
- Vent slots near the top; internal fan
- No Kensington slot, no physical reset button

## Power
- PoE: IEEE 802.3af
- DC: 5 V, ~1.6 A; bundled adapter 5 V/2.1 A
- Max power: ~7.2 W

## Thermal
- Operating temperature: 0–45 °C
- Fan: **yes, variable speed** — manual p.18 explicitly: fan "ONLY available for 4K products". This
  is the source of the wider fan contradiction discussed for HDMI Plus/SDI Plus — see
  `../power-and-thermal.md`.

## Mounting
- 1/4"-20 threaded hole; L-bracket #92240 in box; Fishtail bracket STL also compatible
- ACC10013 "Pro Convert Plus Mounting Kit" compatible

## Other notes
Controls: single toggle MENU + 16-position rotary switch (no separate SELECT button, unlike NDI to
HDMI). FCC Part 15, 2-year warranty. Separate Modator 2U "Module" variant exists (different form
factor).

## Open questions
- Exact weight.
- Exact LED/rotary order on the top face near Face B (uncertain per source).
- Enclosure alloy.
