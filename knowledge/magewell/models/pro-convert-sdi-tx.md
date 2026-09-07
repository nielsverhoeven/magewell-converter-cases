# Pro Convert SDI TX

**Priority model for this project.**

## Identity
- SKU: 640600000 (KR variant 640600006)
- Product page: https://www.magewell.com/products/pro-convert-sdi-tx
- Tech specs: https://www.magewell.com/tech-specs/pro-convert-sdi-tx
- Datasheet (rev 06/18/2026): https://www.magewell.com/static/tech-specs/Pro_Convert/ProConvertSDI_TX.pdf

## Type / interfaces
NDI encoder — SD/HD/3G-SDI BNC input, 2048×1080p60; **no loop-out**.

## Physical
- Housing family: [Compact/TX](../housing-families.md#b-compacttx-1009--602--233-mm)
- Dimensions: 100.9 × 60.2 × 23.3 mm (same chassis as HDMI TX)
- Weight: unknown
- Enclosure: metal (alloy not stated)

## Port layout
- Input end: SDI IN BNC → Input LED → Mini-DIN-8 "PTZ+TALLY"
- Power/data end: USB 2.0 Type-B "+5V" → Power LED → RJ45 "NDI+PoE"; QR-code sticker; SD-card slot (non-functional) on this end
- Long-edge side face: 16-position rotary switch (board index)
- Top: printed label only, no vent grille (estimated from image)
- Bottom: 1/4"-20 threaded hole (near the power end, estimated from image)
- No Kensington slot, no physical reset (web UI over USB-NET only), no WiFi

## Power
- PoE: IEEE 802.3af
- DC: 5 V via USB-B, ~1.5 A max; bundled adapter 5 V/2.1 A
- Max power: ~7 W

## Thermal
- Operating temperature: 0–40 °C
- Fan: no — same chassis/manual family as HDMI TX; manual p.19 explicitly: "Fan Speed … not available for TX products"

## Mounting
- 1/4"-20 threaded hole; L-bracket #92240 in box
- Optional ACC10012 "Pro Convert TX Mounting Kit" (1 bracket, 1 D-ring 1/4" screw, 4× M3×6 knurled screws) for 1RU shelves PAR10209/PAR10210

## Other notes
In box: USB 2.0 A-to-B cable, 5 V/2.1 A adapter, Mini-DIN-8 breakout cable, Tally light, L-bracket.
No SDI loop-out, unlike the Plus-family encoders.

## Open questions
- Exact weight (no figure at all, not even a retailer fallback).
- Exact bottom-face 1/4"-20 hole position (estimated from image, not confirmed by a drawing).
- Enclosure alloy.
