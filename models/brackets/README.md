# models/brackets — mounting-bracket assemblies

Flat, single-part plates that carry the tool-less dovetail mount rail (`lib/mcc/rail.scad`,
issue #25 / D-15) so a case clicks onto some external mounting surface instead of (or in addition
to) sitting on its own floor. Structurally identical in shape to a `models/coupons/` target — no
base/lid split, no device record, no variant config — and discovered the same way, by
`scripts/build.py`'s `discover_brackets()` (mirrors `discover_coupons()` exactly; see
`docs/plans/2026-09-09-mount-rail-and-brackets.md` §3.2, `.claude/knowledge/layout-patch-wall.md`
§17.2).

## What each bracket carries

| Bracket | Carries | Mounting surface |
|---|---|---|
| `tv-bracket.scad` | VESA 100×100 (M4) + 200×200 (M6/M8) through-clearance hole patterns, sharing one centre; a "+" cross of stiffening ribs on the non-rail face; the male mount rail on the rail face | Sandwiched between a TV's own back panel and its existing wall/stand mount — the same screws that normally go TV→mount now go TV→(through this plate)→mount, clamping it captive. No new fasteners added to the BOM for the VESA side (see `BOM.md` "Mounting brackets"). |
| `arch-tv-bracket.scad` (issue #47) | Two identical arms (M8 pad + counterbored head, edge ribs, M3-insert lap), qty 2, plus a centre piece with the male rail, 4 M3 per lap | Screwed **directly** onto the TV's top two VESA 400 screws (M8); nothing else touches the TV. |

Issue #27's truss bracket (`truss-bracket.scad`) is **deferred** — `layout-patch-wall.md` §17.1,
blocked on measurement M14 (a half-coupler's real bolt pattern) and a user safety sign-off (R26).
Not part of this directory yet.

## `arch-tv-bracket.scad` (issue #47)

Unlike `tv-bracket.scad`, this bracket carries **no VESA plate** — it mounts directly on a TV's
top two VESA 400 (M8) screw positions with a raised, arched centre section carrying the rail, so
the case hangs clear of the TV's own bezel/stand. Three printed parts from one `.scad` file (a
single `arm` STL printed twice, plus one `centre` — `docs/plans/2026-09-27-arch-tv-bracket.md` §3.1,
`scripts/build.py`'s `discover_brackets()` reads the `// build.py: parts = arm, centre` marker at
the top of the file).

- **Orientation**: same convention as `tv-bracket` (patch wall down); the **arch points up** (see
  the "UP" arrow debossed on the centre's top face) — nothing else keys the assembly against a
  180°-rotated (upside-down, patch-wall-up) install; the arch shape and the arrow are cues, not a
  physical key (risk R-B, proposed R31).
- The case slides on **from the right** (viewed from behind the TV, i.e. from the installer's own
  side) and needs `slide_clear` (≈ 181 mm at the current parameters, echoed by the render — the
  case's own leading end wall must clear the rail's open end before the rail can begin engaging)
  of free space to the right of its final position, from 19 to 70 mm off the TV back.
- Print table: `arm` — **TV face on the bed**, ribs/pad boss/insert bores up, no supports;
  `centre` — **flat (TV-side) face on the bed**, rail up (same convention as `tv-bracket`/
  `rail-latch`), no supports.
- Render: `python scripts/build.py render brackets/arch-tv-bracket --format both`. The released STL
  is rendered for the **placeholder** `TV_TOP_CLEAR = 150` (`unknown` → `assumed`, measurement
  M18a); for a measured TV, re-render with
  `-D TV_TOP_CLEAR=<mm>` and re-golden before printing for use.
- Assembly order: heat-set inserts into both arms → bolt both arms to the centre (M3×10, from the
  top, on a table) → offer the assembled bracket to the TV → two M8 screws through the pads (length
  MEASURE, see `BOM.md`) → click the case on.
- The TV's top two VESA 400 holes must not also carry another mount — this is a **direct** mount,
  by user decision (2026-09-27, #47).
- **Do not print for use** before M15 (rail-latch pull test), M18 (the TV measurements: top-screw-
  to-edge clearance, VESA insert thread depth, sweep-band obstacles, and post-print rail tilt) and
  R38 (an inherited rail-interface defect, tracked as issue #48 — the female groove has no entry
  path today) are closed. See `docs/plans/2026-09-27-arch-tv-bracket.md` §9/§12.3 for the full risk
  list and measurement plan.

## Orientation (issue #26's own acceptance criterion)

The rail lives on one flat face of the plate, the ribs on the other (`tv-bracket.scad`'s own
header comment has the full derivation and the exact `rotate([0,0,180])` reasoning). Convention:
**mount with the plate's own +Y axis pointing up** — the ordinary, unsurprising way to hang a
symmetric VESA square. With the rail placed as authored, a case slid onto it then hangs with its
patch (cable) wall facing down. See `.claude/skills/print-check/SKILL.md` for the one-line
go/no-go version of this note, and `tv-bracket.scad`'s `part == "assembly"` preview branch (a
ghost case mated onto the rail) for the render used to verify it visually rather than trust the
transform algebra alone.

**Open point, not blocking (flagged for the user/architect):** the VESA hole pattern is itself
left-right/up-down symmetric, so nothing in the hardware prevents installing the plate rotated
180° from the convention above — which would hang the case with its patch wall UP instead. No
keying feature exists to prevent this; would need an asymmetric marking feature to fix, out of
this ticket's scope.

## Render

```powershell
.venv\Scripts\python scripts\build.py render brackets/tv-bracket --format both
.venv\Scripts\python scripts\build.py check --all
.venv\Scripts\python scripts\build.py golden
```

`render --all` picks up every bracket automatically (`discover_brackets()` globs
`models/brackets/*.scad`).

## Orientation (Bambu Studio)

| Bracket | Orientation | Why |
|---|---|---|
| `tv-bracket` | **Flat, TV-facing face down on the bed, rail up** — exported that way (`tv-bracket.stl`/`.3mf`). The stiffening-rib cross is switched off (`RIBS = false`, architecture.md D31): with ribs on the TV face and the rail on the other, neither face could lie flat, so the plate always hung 9 mm above the bed. | Flat plate, minimal warp risk at 6 mm thick; matches the existing rail-latch coupon's own proven orientation for the same dovetail profile. |
| `arch-tv-bracket` `arm` | **TV face down on the bed** — pad boss, edge ribs and insert bores all print up, no supports. | Flat bar, minimal warp; the M8 counterbore and insert bores open upward, printable without bridging. |
| `arch-tv-bracket` `centre` | **Flat (TV-side, standoff) face down on the bed, rail up** — same rail orientation as `tv-bracket`/`rail-latch`. | Keeps the dovetail taper the only overhanging feature (the latch tab is disabled, architecture.md D28); the tabs print flat with the body. |
