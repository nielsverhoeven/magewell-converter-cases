---
name: print-check
description: Pre-slice go/no-go check before printing any part — render/check/golden status, bed-fit, orientation, overhangs, and ASA slicer hints for Bambu Studio; use right before slicing anything from this repo, and always before a coupon or full case print.
---

# print-check

The gate between "the model renders" and "send it to the printer." A clean render does not mean a
printable part — this skill is the checklist that catches the difference.

## 1. Automated checks first

```
python scripts/build.py render
python scripts/build.py check
python scripts/build.py golden
```

All three must pass before you even open Bambu Studio. `render` failing means the geometry is broken
— fix that first, nothing below matters yet. `check` failing (non-watertight, inconsistent winding,
`len(split()) != 1`) means the mesh has a real defect the slicer will either silently repair badly or
choke on — do not "just try slicing it anyway" to see if it works. `golden` failing means the geometry
changed since the last reviewed baseline — that might be intentional (you just changed a dimension)
or might be a regression; resolve which before printing, don't print through an unexplained diff.

If you want a STEP file too (for a CAD tool other than the slicer, or to hand the part to someone
without OpenSCAD) — not required just to slice and print, since Bambu Studio prints from the STL/3MF
— run `python scripts/build.py step <target>` (or `step --all`) after `render`. It converts the
already-rendered STL to `exports/<target>/<part>.step` via `scripts/mesh_to_step.py`
(`cadquery-ocp`, falling back to FreeCAD's `freecadcmd` if no wheel is available for the local
Python — `build.py doctor` reports which backend, if either, is available). Every device zip on the
project's GitHub Releases page ships the STEP alongside the STL/3MF for exactly this reason — see
`README.md`'s "Releases" and "Open in Bambu Studio" sections.

## 2. Bed-fit check

The confirmed printer is a **Bambu Lab X1 Carbon** (user decision 2026-09-07): build volume
**256 × 256 × 256 mm**, fully enclosed (ASA-capable), AMS, 0.4 mm nozzle by default. Every part in
this repo must print on it — no part may assume a larger bed, an open frame, or a multi-material
process (no TPU is used). In Bambu Studio select printer *Bambu Lab X1 Carbon 0.4 nozzle* and the
*Bambu ASA* (or *Generic ASA*) filament profile; close the door and keep the aux/part cooling fan
low for ASA. `MCC_BUILD = 256`, `MCC_BED_MARGIN = 6` in
`lib/mcc/constants.scad` — the Tier-1 assert (`openscad-authoring`'s assert table) already checks
`bbox ≤ MCC_BUILD - MCC_BED_MARGIN` per exported part at render time, so a clean render has already
passed this. Re-confirm visually in Bambu Studio anyway: the assert checks the *axis-aligned* bbox at
the part's modeled orientation, not necessarily the orientation you're about to slice it in — a part
that fits standing up may not fit lying down, and vice versa.

Sizing background (architecture.md §11 R1): **an in-line layout does not fit the 256 mm bed for the
Plus family** (~260.5 mm > 256 mm). The user therefore chose the **side-exit, single patch-wall
layout** (all connectors in one long side wall; envelope ≈ 190 × 150 × 45 mm) — see architecture.md
for the layout contract. If a rendered part is longer than ~200 mm, something is wrong upstream;
stop and check the layout before committing plate time.

## 3. Orientation rules

| Part | Orientation | Why |
|---|---|---|
| Connector panel plate | **Face-down, flat on the bed** | The ⌀23.8/24.2 mm holes print as true circles with no bridging; the flange seat is a true bed-flat surface. The same hole cut vertically is a 24 mm bridge that droops at the top (architecture.md §5 point 2). |
| Shell base/lid | **Open side up** | Keeps the aperture rabbet's ≤45° chamfer self-supporting and avoids printing the deepest cavity upside down into supports. |
| Any part with a boss/insert hole | Hole axis vertical (printing top-down through the hole), not horizontal | A horizontal insert hole is a small bridge/overhang per hole and prints out-of-round; a vertical hole prints as a clean circular wall. |
| `models/brackets/tv-bracket.scad` | Flat, either face down — but **mount with the plate's own +Y axis up** (not a print-orientation choice; see `models/brackets/README.md` "Orientation") so the mated case hangs with its patch/cable wall down, not the fan/vent side against the TV. |

No unsupported span over **10 mm** anywhere (the general shell rule, architecture.md §5) — check any
new rabbet roof, vent hood, or aperture chamfer against this before slicing. Roofs ≤45° from vertical
print self-supporting on a 0.4 mm nozzle; steeper needs either a redesign or accepted supports (rare
in this repo — a support-requiring roof is usually a sign the geometry should be rethought, not
support-enabled by default).

## 4. ASA slicer profile hints (Bambu Studio)

| Setting | Value | Why |
|---|---|---|
| Enclosure | **Required** | ASA warps significantly without one — the #1 disadvantage of the material (`knowledge/design/fdm-rugged-enclosure-guidelines.md:17`). Do not print ASA on an open frame. |
| Nozzle temp | ~260 °C | `fdm-rugged-enclosure-guidelines.md:17`'s ASA row |
| Bed temp | 105 → 110 °C | Same source; step up if the first layer isn't sticking |
| Walls / perimeters | **5** (fixed decision) | `knowledge/design/fdm-rugged-enclosure-guidelines.md:36`'s "parts under mechanical load" range (~5-7 perimeters at 0.4 mm) — this repo standardizes on 5 for every structural wall |
| Wall thickness | **3 mm** (fixed decision, `MCC_WALL`) | matches the 5-perimeter count at 0.4 mm line width without a partial-width gap-fill pass |
| Brim | Recommended, wide | Counters ASA's warp tendency at the bed edge, especially on a footprint approaching the 244+ mm range this repo's cases run at |
| Infill | Standard (not maxed) — ribs carry the load, not infill | Per the ribs-vs-thick-walls rule: "the standard fix is to keep walls at a uniform (thinner) thickness and add ribs/gussets... for a fraction of the material" (`fdm-rugged-enclosure-guidelines.md:70`) |

## 5. Warp watch-outs

- Generous bottom-edge fillet/chamfer everywhere — never a sharp 90° bed-contact corner (architecture
  §11 R9). A sharp corner is where ASA warp starts lifting first.
- Uniform wall thickness (3 mm) with ribs, not thickened sections — a locally-thick boss/wall cools
  unevenly and sinks/warps (§4 of the FDM guidelines file).
- **Do not treat the first full-size print as the design validation.** Coupons first — see §6.
- On a long lid (>~180 mm), 4 captive thumbscrews likely aren't enough to stop mid-span bow +
  tongue-and-groove joint opening under ASA warp (architecture §11 R7, currently flagged as needing a
  user decision toward 6 thumbscrews or a mid-span rib). Check whether that decision has been made
  for the specific case before printing a long lid with only 4.

## 6. Coupons before cases — non-negotiable, and first

Do not print a full ~244 mm+ case before these five coupons (`models/coupons/`, architecture.md §9
Tier 4) exist, have been printed, and their results are written back into `constants.scad`:

| Coupon | Verifies |
|---|---|
| `neutrik-tile` | A real Neutrik connector actually fits the cutout and screws down |
| `depth-mockup` | Real mating-plug lengths, replacing the `unknown`/`assumed` bay-depth figures |
| `tg-ladder` | Tongue-and-groove clearance, calibrates `MCC_CLR_TG` |
| `insert-boss` | Heat-set boss hole diameter for ASA specifically (the 4.0 mm community figure vs. the 4.29 mm ASA/ABS CAD-pocket cross-check, `knowledge/components/fasteners-and-hardware.md:22` vs `:60`, are not yet reconciled for this printer) |
| `tolerance-ladder` | General fit ladder, calibrates `MCC_CLR_SLIDE`/`MCC_CLR_PRESS` |

If none of these exist yet for the printer/material combo in use, that itself is the go/no-go answer
for a full case: **no-go, print the coupons first.**

## 7. Reading a `check` failure

`build.py check` runs `check_mesh.py` (trimesh) against the rendered mesh. Map the failure to a fix,
don't just re-render and hope:

| `check_mesh.py` failure | Likely cause | Where to look |
|---|---|---|
| `is_watertight == False` | A gap in the mesh — usually two shapes that were meant to touch but have a sub-epsilon coincident-face gap, or a `diff()`/`difference()` that left a sliver | Check any recent `attach()`/`position()` change; verify `MCC_EPS` overlap is actually applied at the join |
| `is_winding_consistent == False` | A face normal flipped somewhere in the CSG tree — often from a boolean on non-manifold input | Re-render the suspect submodule alone (`-o sub.csg`) to isolate it |
| `euler_number` unexpected | Topological genus changed unexpectedly (e.g. an unintended hole clear through the shell) | Check the most recent cutout/vent placement against its intended bounds |
| `volume <= 0` | Inverted/degenerate solid | Usually paired with a winding-consistency failure — fix that first |
| `len(split()) != 1` | The mesh is more than one connected shell — a rib, boss, or vent grille floated free after a parameter change | This is the most common real-world hit in this repo per architecture.md §9 Tier 3 — check whatever dimension you last edited actually still reaches the wall it's supposed to be attached to |

Do not attempt to fix a `check` failure by loosening the check itself — these five conditions are the
minimum bar for "this is one printable solid," not an arbitrary strictness knob.

## 8. Bambu Studio-specific verification

Before slicing for real, in Bambu Studio:

- Confirm the imported STL's bounding box in the object manipulation panel matches what `--summary`
  reported at render time — a mismatch usually means the wrong export file (stale `exports/` output
  from an earlier render) got imported.
- Use the slicer's built-in overhang/support painting view to visually confirm the ≤45° self-
  supporting claim for any new geometry before trusting it blindly — a computed angle in OpenSCAD and
  what the slicer's support algorithm considers "needs support" can disagree at the margin.
- If the plate preview shows supports being auto-generated anywhere on the panel plate or the shell's
  outer faces, treat that as a design smell, not just a setting to turn off — supports on those faces
  usually mean an assumption in this skill's §3 orientation table doesn't hold for the specific part.

## Go/no-go checklist

- [ ] `build.py render` clean
- [ ] `build.py check` clean (watertight, consistent winding, single shell)
- [ ] `build.py golden` clean, or the diff is understood and expected
- [ ] `build.py step` clean, if a STEP file is wanted (not required to slice/print from STL/3MF)
- [ ] Bbox fits 256 mm cube minus margin, confirmed in-slicer at the actual print orientation
- [ ] Orientation matches the table in §3 for this part type
- [ ] No unsupported span >10 mm; all roofs ≤45°
- [ ] For a case base: a head-on orthographic elevation of the patch wall from OUTSIDE (assembly
      with `panel_placed`, `--projection=o`, camera along −Y) shows exactly round D holes with their
      two screw holes and no window outline around them (architecture.md §13 D11)
- [ ] Slicer profile matches §4 (enclosure on, 260°/105-110°, 5 walls, 3 mm walls, brim)
- [ ] Relevant coupons (§6) already printed and measured back into `constants.scad`, if this is a
      full case rather than a coupon itself
- [ ] No unexpected auto-generated supports in the Bambu Studio plate preview (§8)
