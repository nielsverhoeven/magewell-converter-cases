# Components knowledge base

Off-the-shelf hardware reference for the 3D-printed Magewell Pro Convert case. Fetched/searched
2026-09-07 — see `sources.md` for the full URL list (also covers `../design/`).

- **`fans.md`** — Noctua fan lineup + mounts/controller/power accessories. Headline: **NF-A6x25
  5V/5V PWM** (best airflow margin, fits 100×70mm), with **NF-A4x20 5V PWM** as the quieter/smaller
  secondary pick.
- **`fasteners-and-hardware.md`** — heat-set inserts, screws, latches, hinges, magnets, feet/bumpers.
  Headline: **Ruthex RX-M3x5.7** insert in a **~4.0mm nominal** printed hole (+0.2–0.3mm CAD
  compensation per CNC Kitchen).
- **`cables.md`** — port-to-wall depth clearance by connector type. Headline: **≥41mm** for 12G-SDI
  BNC (Belden 4855R, bend-radius-limited), **~27mm** for slim RJ45, **~30mm** for right-angle HDMI;
  several connector types remain `unknown` pending physical measurement.
- **`sources.md`** — every URL cited across all five knowledge files, grouped by source document,
  with fetch date and blocked/unparseable sources flagged.
- **`fan-power-sources.md`** (fetched 2026-09-09) — candidate on-device 5 V sources for powering the
  case fan while the device runs on PoE (no external 5 V rail in the case). Headline: **decoder USB
  HOST port** is the lower-risk candidate (no documented competing load, larger assumed current
  budget, but no Magewell-stated current rating either); **encoder Mini-DIN-8 VCC pin (5 V, 100 mA
  max)** is tighter and shared with the stock Tally Light — both need physical measurement before
  committing a case design. Confirms the USB Type-B "+5V" port is input-only, and that a fan cannot
  be powered by tapping the PoE cable in parallel with the device's own PD (see file for the
  802.3af/at/bt reasoning); the PoE-splitter route in `poe-splitters.md` remains the fallback.

See `../design/README.md` for the design-guideline files, including known numeric conflicts.
