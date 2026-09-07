# Pro Convert for NDI to AIO

**Priority model for this project.**

## Identity
- SKU: 642100000
- Product page: https://www.magewell.com/products/pro-convert-for-ndi-to-aio
- Datasheet: https://www.magewell.com/static/tech-specs/Pro_Convert/ProConvertforNDI_to_AIO.pdf
- Manual: https://www.magewell.com/files/documents/User_Manual/ProConvert_Decoder-UserManual_en_US.pdf
- QSG: https://www.magewell.com/files/documents/Quick%20Start%20Guide%20for%20Pro%20Convert%20Decoders.pdf

## Type / interfaces
NDI decoder — HDMI 1.4 + 1× BNC 3G-SDI output, 1080p60 simultaneous; **no USB host**.

## Physical
- Housing family: [Compact/TX](../housing-families.md#b-compacttx-1009--602--233-mm)
- Dimensions: 100.9 × 60.2 × 23.3 mm
- Weight: unknown

## Port layout
- Face A: HDMI OUT → LED → SDI OUT BNC (no USB host on this model)
- Face B: USB-B (power only, no data/config role beyond power in this description) → LED → RJ45 "NDI+PoE"
- Top layout otherwise follows the shared decoder pattern (SD slot + 1/4"-20 hole; rotary switch + MENU + SELECT)
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
Controls: MENU + SELECT buttons + 16-position rotary switch (per shared decoder pattern). Only model
in the NDI-decoder group with two simultaneous video outputs (HDMI + SDI) and no USB host port. FCC
Part 15, 2-year warranty. Separate Modator 2U "Module" variant exists ("Pro Convert for NDI to AIO
Module" is explicitly listed as Modator-compatible — different form factor from this boxed unit).

## Open questions
- Exact weight.
- Whether the Face-B USB-B port has any config/data role beyond power (report only confirms "power
  only" without further detail).
- Enclosure alloy.
