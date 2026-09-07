# Pro Convert HDMI 4K Plus

## Identity
- SKU: 640100000 (KR variant 640100006)
- Product page: https://www.magewell.com/products/pro-convert-hdmi-4k-plus
- Tech specs: https://www.magewell.com/tech-specs/pro-convert-hdmi-4k-plus
- Datasheet: https://www.magewell.com/static/tech-specs/Pro_Convert/ProConvertHDMI_4K_Plus.pdf
- Manual: https://www.magewell.com/files/documents/User_Manual/ProConvert_Encoder-UserManual_en_US.pdf
- QSG: https://www.magewell.com/files/documents/Quick%20Start%20Guide%20for%20Pro%20Convert%20Encoders.pdf

## Type / interfaces
NDI encoder — HDMI 1.4/2.0 input + HDMI loop-out, up to 4096×2160p60.

## Physical
- Housing family: [Plus](../housing-families.md#a-plus-1175--667--234-mm)
- Dimensions: 117.5 × 66.7 × 23.4 mm
- Weight: unknown
- Enclosure: dark grey metal (alloy not stated)

## Port layout
- End A (data/power): corner screw hole → USB Type-B "+5V" (power + Ethernet-over-USB RNDIS/ECM config, 192.168.66.1) → RJ45 "NDI+PoE" with Power LED → SD-card slot (present, non-functional) → corner screw hole
- End B (video/control): top row — Tally "PREVIEW" LED, 16-position rotary switch (board index 0–F), Tally "PROGRAM" LED; bottom row — HDMI IN with Input LED, Mini-DIN-8 "PTZ+TALLY", HDMI OUT with Output LED
- Top: circular perforated "MAGEWELL" grille (likely vent, estimated from image)
- No analog audio jack, no Kensington slot, no physical reset button (software reset only via USB-NET web UI)

## Power
- PoE: IEEE 802.3af
- DC: 5 V via USB Type-B, ~2 A max; bundled adapter 5 V/2.1 A
- Max power: ~10 W
- Manual FAQ p.58: requires a 5 V DC source rated no less than 2.1 A

## Thermal
- Operating temperature: 0–45 °C (storage –20–70 °C, 5–90% RH)
- Fan: yes — Web-UI Dashboard "Fan Speed" field (manual p.17–19); this is a 4K-capable model, consistent with the decoder manual's "fan ONLY available for 4K products" rule (see `../power-and-thermal.md` for the full cross-report contradiction discussion)
- Manual p.18: keep free from dust; if core temperature approaches 100 °C, supply cooler air

## Mounting
- 1/4"-20 threaded hole
- L-bracket #92240 in box; Fishtail bracket also compatible

## Other notes
In box: USB 2.0 A-to-B cable, 5 V/2.1 A adapter, Mini-DIN-8 breakout cable (pinout PDF: https://www.magewell.com/files/documents/Mini-DIN8%20to%20Tally%20(Mini-DIN8)%20+%20RS232%20(DB9)%20Breakout.pdf), Tally light, L-bracket.

## Open questions
- Exact weight.
- Bottom-face layout / precise 1/4"-20 hole position (not pictured in any source).
- Enclosure alloy.
