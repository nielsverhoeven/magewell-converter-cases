# Pro Convert SDI Plus

**Priority model for this project.**

## Identity
- SKU: 640400000 (KR variant 640400006)
- Product page: https://www.magewell.com/products/pro-convert-sdi-plus
- Datasheet (rev 06/18/2026): https://www.magewell.com/static/tech-specs/Pro_Convert/ProConvertSDI_Plus.pdf
- Manual: https://www.magewell.com/files/documents/User_Manual/pro_convert_family_user_manual_v1.1_en.pdf

## Type / interfaces
NDI encoder — SD/HD/3G-SDI BNC input, 2048×1080p60 + SDI loop-out.

## Physical
- Housing family: [Plus](../housing-families.md#a-plus-1175--667--234-mm) — shared with the 4K Plus
  tier (manual figure captioned "SDI 4K Plus/SDI Plus")
- Dimensions: 117.5 × 66.7 × 23.4 mm
- Weight: unknown
- Enclosure: dark grey metal (alloy not stated)

## Port layout
- End A (data/power): corner screw hole → SD-card slot (non-functional) → USB Type-B "+5V" → RJ45 "NDI+PoE" → QR-code sticker → corner screw hole
- End B (video/control): top row — Tally "PREVIEW" LED, 16-position rotary switch, Tally "PROGRAM" LED; bottom row — SDI IN BNC with Input LED, Mini-DIN-8 "PTZ+TALLY", SDI OUT BNC with Output LED
- Top: circular perforated "MAGEWELL" grille. Bottom: not pictured in any source.
- No Kensington slot, no physical reset button, no WiFi
- LEDs: power, tally preview/program, input signal, loop-through signal

## Power
- PoE: IEEE 802.3af
- DC: 5 V via USB-B, ~1.5 A; bundled adapter 5 V/2.1 A
- Max power: ~7 W

## Thermal
- Operating temperature: 0–45 °C
- Fan: **uncertain** — official datasheet lists no fan, but Web-UI "Fan Speed" field text is
  ambiguous about whether it applies to this (non-4K) Plus-tier model. See the full contradiction
  writeup in `../power-and-thermal.md` and `../housing-families.md`. Verify physically before
  relying on this for a sealed-case thermal design.
- General manual guidance: keep free from dust; supply cooler air if internal temperature rises.

## Mounting
- 1/4"-20 threaded hole; L-bracket #92240 in box
- Fishtail bracket also compatible
- ACC10013 "Pro Convert Plus Mounting Kit" compatible

## Other notes
In box: USB A-to-B cable, 5 V/2.1 A adapter, Mini-DIN-8 breakout cable (to Mini-DIN-8 + DB9), Tally
light #99090, L-bracket #92240.

## Open questions
- Fan presence (see Thermal section — this is the main open question for this model).
- Exact weight (no figure at all, not even a retailer fallback).
- Bottom-face layout / precise 1/4"-20 hole position.
- Enclosure alloy.
