# models/brackets — mounting-bracket assemblies

Flat printed plates that carry the tool-less dovetail mount rail (`lib/mcc/rail.scad`,
issue #25 / D-15) so a case clicks onto some external mounting surface instead of (or in addition
to) sitting on its own floor. Structurally identical in shape to a `models/coupons/` target — no
base/lid split, no device record, no variant config — and discovered the same way, by
`scripts/build.py`'s `discover_brackets()` (mirrors `discover_coupons()` exactly; see
`docs/plans/2026-09-09-mount-rail-and-brackets.md` §3.2, `.claude/knowledge/layout-patch-wall.md`
§17.2).

## What each bracket carries

| Bracket | Carries | Mounting surface |
|---|---|---|
| `arch-tv-bracket.scad` (issue #47) | Two identical arms (M8 pad + counterbored head, edge ribs, M3-insert lap), qty 2, plus a centre piece with the male rail, 4 M3 per lap | Screwed **directly** onto the TV's top two VESA 400 screws (M8); nothing else touches the TV. |

The VESA 100/200 sandwich plate `tv-bracket.scad` (#26) was retired on 2026-09-28 (architecture.md
§13 D47). A vertical VESA-column bracket (Samsung 400 × 300, one column) is planned, and the arch
bracket gains a sandwich mode with it.

Issue #27's truss bracket (`truss-bracket.scad`) is **deferred** — `layout-patch-wall.md` §17.1,
blocked on measurement M14 (a half-coupler's real bolt pattern) and a user safety sign-off (R26).
Not part of this directory yet.

## `arch-tv-bracket.scad` (issue #47)

This bracket carries **no VESA plate** — it mounts directly on a TV's
top two VESA 400 (M8) screw positions with a raised, arched centre section carrying the rail, so
the case hangs clear of the TV's own bezel/stand. Three printed parts from one `.scad` file (a
single `arm` STL printed twice, plus one `centre` — `docs/plans/2026-09-27-arch-tv-bracket.md` §3.1,
`scripts/build.py`'s `discover_brackets()` reads the `// build.py: parts = arm, centre` marker at
the top of the file).

- **Orientation**: patch wall down (see "Orientation" below); the **arch points up** (see
  the "UP" arrow debossed on the centre's top face) — nothing else keys the assembly against a
  180°-rotated (upside-down, patch-wall-up) install; the arch shape and the arrow are cues, not a
  physical key (risk R-B, proposed R31).
- The case slides on **from the right** (viewed from behind the TV, i.e. from the installer's own
  side) and needs `slide_clear` (≈ 181 mm at the current parameters, echoed by the render — the
  case's own leading end wall must clear the rail's open end before the rail can begin engaging)
  of free space to the right of its final position, from 22 to 73 mm off the TV back (D44: 11 mm plates, the case floor flush on the centre).
- Print table: `arm` — **TV face on the bed**, ribs/pad boss/insert bores up, no supports;
  `centre` — **flat (TV-side) face on the bed**, rail up (same convention as the `rail-lock`
  coupon), no supports.
- Render: `python scripts/build.py render brackets/arch-tv-bracket --format both`. The released STL
  is rendered for the **placeholder** `TV_TOP_CLEAR = 150` (`unknown` → `assumed`, measurement
  M18a); for a measured TV, re-render with
  `-D TV_TOP_CLEAR=<mm>` and re-golden before printing for use.
- Assembly order: heat-set inserts into both arms → bolt both arms to the centre (M3×12, from the
  top, on a table) → offer the assembled bracket to the TV → two M8 screws through the pads (length
  MEASURE, see `BOM.md`) → hang the case on and slide it until the lock clicks (see "Installing and removing a case").
- The TV's top two VESA 400 holes must not also carry another mount — this is a **direct** mount,
  by user decision (2026-09-27, #47).
- **Do not print for use** before M15 (rail-lock coupon tests), M18 (the TV measurements: top-screw-
  to-edge clearance, VESA insert thread depth, sweep-band obstacles, and post-print rail tilt) and
  R38 (an inherited rail-interface defect, tracked as issue #48 — the female groove has no entry
  path today) are closed. See `docs/plans/2026-09-27-arch-tv-bracket.md` §9/§12.3 for the full risk
  list and measurement plan.

## Orientation (issue #26's acceptance criterion, kept for every bracket)

Every bracket places the rail with `rotate([0,0,180])`, so a case slid onto it hangs with its patch
(cable) wall facing **down** when the bracket is mounted as its own section above documents (the arch:
arch up, UP arrow). Verify it with the bracket file's `part == "assembly"` preview (a ghost case mated
onto the rail) rather than trusting the transform algebra alone; `.claude/skills/print-check/SKILL.md`
carries the one-line go/no-go version.

**A mounted case always hangs patch-wall down** (user decision 2026-09-28, architecture.md D49) — on
every bracket, the planned truss bracket (#27) included, and never on a TV turned to portrait. The
rail's gravity lock (D48) only engages in that pose: the case's weight must rest on the rail's upper
flank, where the lock bump is.

## Installing and removing a case

- **Install:** hold the case patch-wall down, with its +X end wall (the fan end, where the floor
  groove opens) toward the rail's free end; set the groove onto the rail's end — the 45° lead-in at
  the groove entrance guides it — and slide the case along until it stops and the lock clicks (the
  case rises about 0.7 mm over the lock bump on the way and drops into place).
- **Remove:** lift the case until it stops (about 1 mm — the dovetail itself limits it), then slide it
  back off the way it went on. A plain pull along the rail does not release a hanging case.
- **Before the TV moves:** take the case off before the TV is laid down, carried or tilted — including
  by a TV lift that tilts or flips it. The lock only holds while the case hangs patch-wall down (R44).

## Render

```powershell
.venv\Scripts\python scripts\build.py render brackets/arch-tv-bracket --format both
.venv\Scripts\python scripts\build.py check --all
.venv\Scripts\python scripts\build.py golden
```

`render --all` picks up every bracket automatically (`discover_brackets()` globs
`models/brackets/*.scad`).

## Orientation (Bambu Studio)

| Bracket | Orientation | Why |
|---|---|---|
| `arch-tv-bracket` `arm` | **TV face down on the bed** — pad boss, edge ribs and insert bores all print up, no supports. | Flat bar, minimal warp; the M8 counterbore and insert bores open upward, printable without bridging. |
| `arch-tv-bracket` `centre` | **Flat (TV-side, standoff) face down on the bed, rail up** — the same rail orientation as the `rail-lock` coupon. | The dovetail taper and the lock bump that follows its upper flank are the only overhangs (D44, D48), both self-supporting at 30° from vertical; the rail needs no plate window (D50); the tabs print flat with the body. |
