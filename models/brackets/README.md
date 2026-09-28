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
| `arch-tv-bracket.scad` (issue #47; sandwich mode issue #56, D51) | **Direct mode** (`arm`/`centre`): two identical arms (M8 pad + counterbored head, edge ribs, M3-insert lap), qty 2, plus a centre piece with the male rail, 4 M3 per lap. **Sandwich mode** (`arm_sandwich`/`centre_sandwich`/`spacer`): the same arm shape but with a FLAT clamp pad (no counterbore) and ribs starting further out, a TALLER centre (clears the TV lift's own rail + bolt head where the slide-on sweep crosses the right-hand column), and a spacer disc for the bracket's own unused row | Direct mode: screwed **directly** onto the TV's top two VESA 400 screws (M8), nothing else touches the TV. Sandwich mode: clamped **between** the TV and the TV's own mount (a TV lift) on longer M8 bolts through all four VESA holes. |
| `vertical-tv-bracket.scad` (issue #56) | One arm (`arm`, qty 2 — top and bottom screw), one centre with the male rail, one spacer disc (qty 2, for the lift's other, unoccupied column) | Sandwich-only, no direct-mount option: clamped between a Samsung TV (VESA 400×300) and its own TV lift on ONE vertical column (300 mm pitch), case outboard of the +X column (seen from behind the TV). |

The VESA 100/200 sandwich plate `tv-bracket.scad` (#26) was retired on 2026-09-28 (architecture.md
§13 D47) — its role is now split between `arch-tv-bracket.scad`'s own sandwich mode (a TV whose
own mount uses the SAME two VESA holes as the arch's direct mount) and `vertical-tv-bracket.scad`
(a TV lift on a 400×300 column pattern, D51). Neither new sandwich part reintroduces a VESA-plate
shape: both clamp through the TV's OWN mount hardware, never through a plate this repo prints.

Issue #27's truss bracket (`truss-bracket.scad`) is **deferred** — `layout-patch-wall.md` §17.1,
blocked on measurement M14 (a half-coupler's real bolt pattern) and a user safety sign-off (R26).
Not part of this directory yet.

## `arch-tv-bracket.scad` (issue #47; sandwich mode issue #56, D51)

This bracket carries **no VESA plate** — it mounts on a TV's top two VESA 400 (M8) screw positions
with a raised, arched centre section carrying the rail, so the case hangs clear of the TV's own
bezel/stand. Five printed parts from one `.scad` file (`// build.py: parts = arm, centre,
arm_sandwich, centre_sandwich, spacer`, `// build.py: print_count = arm:2, arm_sandwich:2,
spacer:2`):

- **Direct mode** (`arm` printed twice, plus one `centre`) — the original #47 shape, unchanged since
  #56: screws go straight into the TV, no VESA plate.
- **Sandwich mode** (`arm_sandwich` printed twice, one `centre_sandwich`, `spacer` printed twice) —
  for a TV whose own mount (a TV lift, in the user's installation) already uses all four VESA holes.
  The exported part NAME fixes the mode — there is no `-D` switch that changes what a real export
  produces; `MOUNT_MODE` (a top-level `.scad` variable) only changes the "assembly"/"assembly_sweep"
  **preview**, e.g. `-D part="assembly_sweep" -D MOUNT_MODE="sandwich"`.
  - The arm's own M8 pad is FLAT (no counterbore, no washer seat — R42) and its ribs start further
    from the pad so they clear the TV lift's own rail band where the arm crosses the column (T1-89).
  - The centre plate is TALLER than direct mode's (`centre_t`, ≈16.6 mm at the M20 placeholders,
    vs. 11 mm direct) so the case's own +X slide-on sweep — which crosses the RIGHT-HAND column in
    sandwich mode, unlike direct mode — clears the TV lift's rail and bolt head in Z (T1-87). The
    lap screw lengthens to M3×18 to match (same tip-clearance/engagement window as direct mode's
    M3×12, T1-57).
  - `spacer`: a flat disc for the bracket's OWN unused (bottom) row of VESA holes, matching the
    arm's sandwich pad exactly (clamp height and footprint) so the TV lift's rail stays coplanar
    across both rows (T1-90).
  - Direct-mode geometry and goldens (`arm`, `centre`) are **byte-identical** to before sandwich
    mode existed — confirmed with `git diff`.

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
- **Direct mode**: the TV's top two VESA 400 holes must not also carry another mount (2026-09-27,
  #47). **Sandwich mode** (issue #56, D51) is exactly the fix for a TV whose own mount (a TV lift)
  already uses all four holes — print `arm_sandwich`/`centre_sandwich`/`spacer` instead, with the
  §7.1 Z-clearance caveat above (T1-87).
- **Do not print for use** before M15 (the gravity-lock coupon, as plan F redefines it — see
  `models/coupons/rail-lock.scad`), M18/M20 (the TV/TV-lift measurements: top-screw-to-edge
  clearance, VESA insert thread depth, sweep-band obstacles, the lift's own rail/plate dimensions)
  and M22 (the sandwich tilt/preload check, sandwich mode only) are closed. See
  `docs/plans/2026-09-27-arch-tv-bracket.md` §9/§12.3 (direct mode) and
  `docs/plans/2026-09-28-vesa-column-bracket.md` (sandwich mode) for the full risk list and
  measurement plan.

## `vertical-tv-bracket.scad` (issue #56)

Sandwich-only — there is no direct-mount option for this bracket, because the Samsung TV's own TV
lift already occupies all four VESA holes on both columns. Three printed parts from one `.scad`
file (`// build.py: parts = arm, centre, spacer`, `// build.py: print_count = arm:2, spacer:2`):

- **Hub topology**: one `arm` part, printed TWICE (top screw and bottom screw, 300 mm pitch), placed
  by rotate(∓α) about a centre plate carrying the rail — no `mirror()`, no chirality change (the two
  screws are related by reflection about the assembly's own axis).
- **Fixed layout, no mirror**: the bracket mounts on the +X column (seen from behind the TV), case
  OUTBOARD (toward the TV's edge), slid on from the TV's edge side. This is the only layout whose
  slide-on sweep crosses no column — `COLUMN_SIDE` does not exist in this file and never will.
- **Orientation**: patch wall down (see "Orientation" below); the **UP arrow** on the centre's top
  face points toward the top screw — a cue, not a physical key (the hub's own top/bottom symmetry
  would otherwise let a 180°-about-Z install go unnoticed, flipping inboard/outboard AND gravity
  up/down at once).
- The pad is a FLAT clamp face (no counterbore, no washer seat — R42): the TV lift's own rail bears
  on it directly, with the M8 bolt passing through the lift, the pad, and into the TV. The lift's
  OTHER, unoccupied column gets two printed ASA `spacer` discs of the same clamp height/footprint, so
  the lift's rail stays coplanar across both columns.
- Print table: `arm` — **TV face on the bed**, ribs up, no supports; `centre` — **flat (TV-side)
  face on the bed**, rail up (same convention as the `rail-lock` coupon); `spacer` — either face
  down (flat disc).
- Render: `python scripts/build.py render brackets/vertical-tv-bracket --format both`. The released
  STL is rendered at the M20 placeholders (`W_LIFT_RAIL=60`, `T_LIFT_RAIL=5`, `WALL_GAP=150`); for a
  measured TV/lift, re-render with `-D W_LIFT_RAIL=<mm> -D T_LIFT_RAIL=<mm> -D WALL_GAP=<mm>` and
  re-golden before printing for use.
- Assembly order: heat-set inserts into both arms → bolt both arms to the centre (M3×12, from the
  top, on a table) → offer the assembled bracket, plus the two spacers on the lift's other column,
  to the TV/lift sandwich → four M8 bolts through the pads/spacers (length MEASURE, see `BOM.md`) →
  hang the case on and slide it until the lock clicks (see "Installing and removing a case").
- **Do not print for use** before M15 (the gravity-lock coupon), M20 (the TV/TV-lift measurements:
  VESA pitch/thread depth, the lift's own rail width/thickness, bolt-head height, the TV-to-wall
  standoff) and M22 (the sandwich tilt/preload check) are closed. See
  `docs/plans/2026-09-28-vesa-column-bracket.md` for the full risk list and measurement plan.

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
.venv\Scripts\python scripts\build.py render brackets/vertical-tv-bracket --format both
.venv\Scripts\python scripts\build.py check --all
.venv\Scripts\python scripts\build.py golden
```

`render --all` picks up every bracket automatically (`discover_brackets()` globs
`models/brackets/*.scad`).

## Orientation (Bambu Studio)

| Bracket | Orientation | Why |
|---|---|---|
| `arch-tv-bracket` `arm` / `arm_sandwich` | **TV face down on the bed** — ribs (and, direct mode only, the pad boss) and insert bores all print up, no supports. | Flat bar, minimal warp; the M8 counterbore (direct mode) and insert bores open upward, printable without bridging. Sandwich mode's flat pad is even simpler — no boss to print at all. |
| `arch-tv-bracket` `centre` / `centre_sandwich` | **Flat (TV-side, standoff) face down on the bed, rail up** — the same rail orientation as the `rail-lock` coupon. | The dovetail taper and the lock bump that follows its upper flank are the only overhangs (D44, D48), both self-supporting at 30° from vertical; the rail needs no plate window (D50); the tabs print flat with the body. Sandwich mode is simply taller — same overhangs, same orientation. |
| `arch-tv-bracket` `spacer` / `vertical-tv-bracket` `spacer` | Either face down (flat disc, no features to orient around). | Trivially self-supporting. |
| `vertical-tv-bracket` `arm` | **TV face down on the bed** — ribs and insert bores print up, no supports. | Same reasoning as the arch's own sandwich arm — flat rounded pad end, no boss. |
| `vertical-tv-bracket` `centre` | **Flat (TV-side, standoff) face down on the bed, rail up.** | Same rail/lock overhangs as arch's own centre, self-supporting at 30° from vertical. |
