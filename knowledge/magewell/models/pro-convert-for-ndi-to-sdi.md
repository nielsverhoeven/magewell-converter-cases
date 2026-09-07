# Pro Convert for NDI to SDI

**Priority model for this project.**

## Identity
- SKU: 641500000 (part 64150)
- Product page: https://www.magewell.com/products/pro-convert-for-ndi-to-sdi
- Datasheet: https://www.magewell.com/static/tech-specs/Pro_Convert/ProConvertforNDI_to_SDI.pdf
- Manual: https://www.magewell.com/files/documents/User_Manual/ProConvert_Decoder-UserManual_en_US.pdf
- QSG: https://www.magewell.com/files/documents/Quick%20Start%20Guide%20for%20Pro%20Convert%20Decoders.pdf

## Type / interfaces
NDI decoder — 1× BNC SD/HD/3G-SDI output, 1080p60; USB 3.0 Type-A host.

## Physical
- Housing family: [Compact/TX](../housing-families.md#b-compacttx-1009--602--233-mm)
- Dimensions: 100.9 × 60.2 × 23.3 mm
- Weight: unknown

## Port layout
- Face A: SDI OUT BNC → LED → USB HOST
- Face B: USB-B "+5V" → LED → RJ45 "NDI+PoE"
- Top layout otherwise follows the shared decoder pattern (SD slot + 1/4"-20 near Face A; rotary switch + MENU + SELECT near Face B), per the shared decoder manual
- No Kensington slot, no physical reset button

## Power
- PoE: IEEE 802.3af
- DC: 5 V, ~1.05 A; bundled adapter 5 V/2.1 A
- Max power: ~5.5 W

## Thermal
- Operating temperature: 0–40 °C
- Fan: no

## Mounting
- 1/4"-20 threaded hole; L-bracket #92240 in box; Fishtail bracket STL also compatible
- ACC10012 "Pro Convert TX Mounting Kit" compatible

## Other notes
Controls: MENU + SELECT buttons + 16-position rotary switch (per shared decoder pattern). FCC Part
15, 2-year warranty. Separate Modator 2U "Module" variant does not apply to NDI to SDI (not listed
among Modator-compatible module SKUs in Report A) — treat as rack-incompatible via Modator.

## Open questions
- Exact weight.
- Precise top-face LED/switch layout (only the shared decoder-family pattern is documented, not a
  model-specific photo).
- Enclosure alloy.
