> **Ids renumbered at the architect gate (issue #68):** D52→D62.1, D53→D62.2, T1-91→T1-62.1,
> T1-92→T1-62.2, R48→R62.1, M23→M62.1, Q24→Q62.1 (see the verdict at the end). `D52` in the
> repository is #61's end-stop record, not this plan's.

# Plan G: the lid's thumbscrew holes have openings (external CAD review of `lid.step`, 2026-09-29)

Base: `main` @ 24c52c8, BOSL2 804028c. Researched, prototyped and verified in a scratch copy of the
sources (nothing in the repository was changed, nothing was posted to GitHub). This plan is written
for a developer who makes no judgment calls: every decision below is taken; section 13 lists the only
questions that need the user, and none of them blocks the fix.

Order of work: architect gate (section 9) first, then sections 5 to 8 by a developer, then the docs
in section 9 by the architect. The fix is delivered as one exact patch, `G-lid-screw-hole-openings.patch`
(Appendix A embeds the same text; `git apply --check` was run against 24c52c8 and is clean).

## 0. Summary

| | |
|---|---|
| Defect | In **every lid of all 8 SKUs**, **3 of the 6** thumbscrew holes (the two `(±X, +Y)` corners and the patch-wall middle one, 24 holes in all) have a **see-through opening in the counterbore floor**: **11.38 mm²** = **27.6 %** of the 41.22 mm² counterbore annulus. It is a circle segment bounded by a straight chord at 1.75 mm from the hole axis toward the lid edge and the counterbore rim at 4.0 mm (max 3.85 mm out), 7.2 mm wide, angular span 26° to 154°. The three far-wall holes are intact. |
| Same in | the print STL (`lid.stl`, same 3 holes, same 11.383 mm²) and the exact STEP (`lid.step`: each broken floor is 2 faces of 29.649 + 0.229 mm² instead of one 41.286 mm² annulus). |
| Second symptom | The through-hole (Ø3.4) is only **0.05 mm** from the groove void on the same side (1.75 − 1.70), i.e. not printable as a wall. |
| Cause | Two features that are each valid alone overlap in plan **and** in Z: the lid groove (`shell.scad:400`, 2.0 mm deep from the underside, z 48 to 50) and the Ø8 counterbore (`fasteners.scad:87-98`, floor at z 49.5). Overlap in Z is 0.5 mm, so where they overlap in plan the lid is cut through. On the 8 mm thick patch wall the groove runs 6.15 to 8.25 mm from the outer face, straight through the counterbores of the fasteners at `MCC_FASTENER_INSET` = 10 (rim at 5.995 mm). |
| Introduced | `b6a8b77` (2026-09-08, first full case) put the groove and the 10 mm fastener ring together; the counterbore is from `fcfdf56` (2026-09-07). Latent ever since; rendering `b6a8b77` gives the same 3 holes and 11.383 mm². |
| Not caught by | `build.py check` (topology, floating islands, cantilevers), the Bambu Studio slicer gate (0 warnings on the current lids), the goldens (the openings are 0.018 % of the lid volume, tolerance 0.5 %) and T1-33 (checks groove depth against lid thickness only). |
| Fix (recommended) | **Option T**: on the +Y patch side only, move the tongue-and-groove frame outward, tongue inner edge 4.5 mm from the wall's outer face (`MCC_TG_PATCH_INSET`). Fastener, boss, insert and cable-bay positions do not move. The counterbore then keeps a 1.245 mm web to the groove. |
| Guards | Tier-1 asserts **T1-91** (counterbore web to the groove, every fastener) and **T1-92** (patch inset range); a Tier-3 mesh check (`non_prismatic_see_through`, lids only, run by `check` and `ci`); a synthetic self-test of that check in `smoke`. |
| Verified in scratch | all 8 lids: 0 openings; STEP: 6 intact floors of 41.286 mm²; base and lid interference 0.000000 mm³ and clearance exactly 0.25 mm all round; Bambu slicer gate 0 warnings on all 17 parts; `smoke`, `check --all` and `golden` green; goldens still inside tolerance (lid −46.48 mm³, base +22.40 mm³); the new guards fail on the current main-branch lids (24 findings) and on the old geometry via `-D` override. |

## 0.1 Evidence index (all under `scratchpad\lid-holes\`)

| File | What it shows |
|---|---|
| `hero_pro-convert-hdmi-plus.png` | The specialist's view rebuilt from `lid.step` (OCP tessellation, 0.02 mm): outer face with the patch wall down, an intact hole for contrast, underside, sections. |
| `montage_<slug>_model.png` (8 files) | For each slug all 6 holes: outer view, underside view, section through the hole centre in Y (YZ) and in X (XZ). White = no material along the view ray. |
| `montage_pro-convert-hdmi-plus_print.png`, `montage_pro-convert-hdmi-tx_print.png` | The same from `lid.stl` mapped back from the print pose. |
| `before_after_pro-convert-hdmi-plus.png`, `montage_pro-convert-hdmi-plus_AFTER.png` | Current lid against the patched lid, same view; and all 6 holes of the patched Plus lid. |
| `analysis.json`, `analysis_step_faces.json`, `layout.json` | The numbers behind sections 1 and 2 (model STL, print STL, STEP faces, fastener positions). |
| `G-lid-screw-hole-openings.patch` | The exact fix. |
| `tools\` | Every script used (`step1_analyze.py`, `step3b_step_faces.py`, `apply_fix.py`, ...). |

## 1. Reproduction on the exports

Read-only on `exports\<slug>\lid.model.stl` (model frame), `lid.stl` (print pose) and `lid.step`, all built
from git head 24c52c8 (`lid.manifest.json`: `git_dirty` false). Scripts: `tools\step1_analyze.py`
(slices), `tools\step3b_step_faces.py` (STEP), `tools\step2_render.py` and `tools\step4_hero.py` (images).

Method per hole: slice the lid at the middle of every prismatic z-interval (48 to 49.5, 49.5 to 50,
50 to 51, plus three more levels), take the region inside the counterbore disc (vertex radius
4.00482) minus the through-hole that has no material at any level. That region is what you can see
through. STEP: OpenCascade B-rep faces and point classification against the solid.

### 1.1 Result (identical on all 8 slugs)

Per affected hole: counterbore annulus 41.22 mm² (mesh) / 41.286 mm² (STEP); see-through **11.383 mm²
(27.6 %)** in the mesh, 11.408 mm² missing in the STEP; y-extent +1.75 to +3.85 mm from the hole axis
toward the lid edge, x-extent ±3.60 mm at the chord (7.2 mm wide), angular span 26° to 154° centred on
+Y; the hole itself is open (99.9 %). Per intact hole: 0.005 mm² (numerical dust only).

| Slug | L × W (mm) | Affected: the 3 patch-side holes (x, y) | Intact: the 3 far-side holes (x, y) |
|---|---|---|---|
| pro-convert-hdmi-tx | 193.9 × 159.85 | (±86.95, 69.925), (−31.475, 69.925) | (±86.95, −69.925), (−12.64, −69.925) |
| pro-convert-sdi-tx | 194.9 × 158.8 | (±87.45, 69.4), (−31.725, 69.4) | (±87.45, −69.4), (−13.14, −69.4) |
| pro-convert-hdmi-plus | 210.5 × 166.35 | (±95.25, 73.175), (0, 73.175) | (±95.25, −73.175), (−12.64, −73.175) |
| pro-convert-sdi-plus | 211.5 × 165.3 | (±95.75, 72.65), (0, 72.65) | (±95.75, −72.65), (−13.14, −72.65) |
| pro-convert-for-ndi-to-hdmi | 193.9 × 159.85 | (±86.95, 69.925), (0, 69.925) | (±86.95, −69.925), (−12.64, −69.925) |
| pro-convert-for-ndi-to-hdmi-4k | 210.5 × 166.35 | (±95.25, 73.175), (0, 73.175) | (±95.25, −73.175), (−12.64, −73.175) |
| pro-convert-for-ndi-to-sdi | 194.9 × 158.8 | (±87.45, 69.4), (0, 69.4) | (±87.45, −69.4), (−13.14, −69.4) |
| pro-convert-for-ndi-to-aio | 194.9 × 159.85 | (±87.45, 69.925), (0, 69.925) | (±87.45, −69.925), (−13.14, −69.925) |

So 24 of 48 holes are broken; the pattern is "the +Y (patch-wall) side", never a far or end wall.
The counterbore rim clears the groove on the other three walls by 2.745 mm (hole centre 10 mm from the
outer face, groove inner edge at 3.25 mm from it, rim at 10 − 4.005 = 5.995 mm).

### 1.2 What the images show

- Outer face (row 1 of each montage, panel A of the hero): the counterbore ring with the Ø3.4 hole in
  its centre, and a white circle segment in the part of the ring that faces the nearby lid edge, its
  flat side 1.75 mm from the hole axis (0.05 mm from the through-hole). This is the specialist's
  screenshot (the lower third of the annulus is white, patch wall down as mounted).
- Underside (row 2): the groove ceiling (dark band, z = 50) is interrupted exactly where the white
  segment is.
- Section x = x_hole (row 3): counterbore floor at z = 49.5, groove ceiling at z = 50.0, so no
  material at all over y = 74.925 to 77.025 on the Plus (open width 2.10 mm); a hairline wall 0.05 mm
  thick stands between the through-hole and the groove. Section through the middle of the groove band
  (hero panel E): a 5.7 mm slot through the whole lid.
- Section y = y_hole (row 4): the intact hole profile, which is why a single section through the
  centre can miss it.

### 1.3 Print STL, 3MF and STEP

- `lid.stl` is `lid.model.stl` rotated 180° about X and moved to the bed centre (identical volume,
  94762.95 mm³ on the Plus). Mapped back, the same 3 holes with the same 11.383 mm². The same opening
  prints; in the print pose the counterbore is a pocket in the first 1.5 mm and the groove opens
  upward from z = 1.0, so the pocket has no roof over the segment, and the 0.05 mm wall between
  hole and groove cannot be extruded at all (one perimeter line is 0.42 mm wide).
- `lid.step` (csg-exact, valid): 263 faces on the Plus, 215 on the compact family, 12 cylindrical
  faces (6 through-holes r 1.702, 6 counterbores r 4.0048). There are 9 planar faces at z = 49.5: the
  6 counterbore floors plus 3 slivers of 0.229 mm² (the 0.155 mm wide rim that stays outside the
  groove). Each broken floor is 29.649 + 0.229 = 29.878 mm² instead of 41.286 mm². Grid classification
  of the exact solid on the Plus agrees: 27.2 % of the sampled ring, y +1.80 to +3.80.
- The slicer gate slices `lid.3mf` (the same mesh) without a warning: 68.9 g, 2.03 h on the Plus,
  61.4 g, 1.82 h on the compact family (run through `slicer_check_project()` on the current exports).

## 2. Root cause

### 2.1 The code (file:line at 24c52c8)

| Where | What it does |
|---|---|
| `lib/mcc/shell.scad:400` | Lid groove: `_mcc_tg_frame(_mcc_cavity_rect(L, W), -MCC_CLR_TG, MCC_TG_W + MCC_CLR_TG, z_top - MCC_EPS, MCC_TG_H + MCC_EPS)`: a ring 2.1 mm wide, z 47.99 to 50.0, offset from the interior-cavity rectangle. |
| `lib/mcc/shell.scad:107-108` | `_mcc_cavity_rect()`: `W - MCC_WALL - MCC_T_PATCH`, so the +Y edge of the rectangle is 8.0 mm from the outer face (patch wall) and the other three edges are 3.0 mm. |
| `lib/mcc/shell.scad:271` | The base's tongue is built from the same rectangle, which is why it sits at 6.4 to 8.0 mm from the outer face on the patch wall. |
| `lib/mcc/shell.scad:402-404` | One `mcc_captive_thumbscrew_hole(lid_t = MCC_LID_T + 2 * MCC_EPS)` per `lid_fastener_pos`, placed at z_top − EPS. |
| `lib/mcc/fasteners.scad:87-98` | `head_d = 8` (line 87) and `counterbore_depth = lid_t / 2` (line 89): the counterbore floor is 1.5 mm below the outer face, 1.5 mm above the underside; through-hole `MCC_M3_CLR_D` = 3.4. Both dimensions are `assumed`, with a TODO in the header comment. |
| `lib/mcc/layout.scad:351-378` | `e = MCC_FASTENER_INSET` (constants.scad:373, 10.0): corners `(±(L/2 − e), ±(W/2 − e))`, patch-wall middle `[x_gap, W/2 − e]`, far-wall middle. |
| `lib/mcc/constants.scad:24, 42, 343, 508-509` | `MCC_LID_T` 3.0, `MCC_CLR_TG` 0.25, `MCC_T_PATCH` 8.0, `MCC_TG_W` 1.6, `MCC_TG_H` 2.0. |
| `lib/mcc/shell.scad:381-384` | The only tongue-and-groove asserts (T1-33): groove depth + 1.0 ≤ lid thickness, tongue + clearances ≤ wall − 0.8. Nothing relates the counterbore to the groove. |

### 2.2 The arithmetic (Plus; t = distance from the patch wall's outer face)

- Groove band on the patch wall: inner edge t = 8.0 + 0.25 = 8.25, outer edge t = 8.0 − 1.6 − 0.25 = 6.15
  (Plus, y = 74.925 to 77.025 against the outer face at y = 83.175).
- Fastener axis t = 10.0, so 1.75 mm from the groove's inner edge and 3.85 mm from its outer edge. The
  counterbore rim (vertex radius 4.00482) spans t = 5.995 to 14.005; the through-hole rim is at
  t = 8.298, i.e. 0.048 mm (0.05 mm at the polygon flats) from the groove.
- Overlap in plan: the circle segment of the counterbore disc between 1.75 and 3.85 mm from the axis.
- Overlap in Z: outer face 51.0; counterbore floor 49.5; groove ceiling 50.0. The floor is 0.5 mm below
  the ceiling, so where both cuts exist the lid has no material from z = 48 to 51.
- The other three walls are fine: groove inner edge at t = 3.25, rim at 5.995, clear by 2.745 mm.
- Trigger: the ring of fasteners was set at 10 mm from the outer faces for 3 mm walls; the patch wall is
  8 mm thick, so the same 10 mm puts the axis only 2 mm from that wall's inner face, exactly where the
  frame (flush with the inner face) runs.

### 2.3 Why no gate saw it (each point checked, not assumed)

1. `build.py check` (watertight, winding, one shell, bbox, floating islands, cantilevers): passes on the
   current `lid.stl` of all 8 SKUs. A crescent is a legitimate closed void.
2. Bambu Studio slicer gate: `slicer_check_project()` on the current `lid.3mf` gives no warning
   (Plus 68.9 g, 2.03 h; compact 61.4 g, 1.82 h).
3. Goldens: the 3 openings remove 3 × 11.383 × 0.5 = 17 mm³ = 0.018 % of the lid volume; the tolerance
   is 0.5 % volume, 1 % area. The lid golden was created from the flawed geometry (first lid golden:
   NDI to HDMI in `b6a8b77`), so it cannot act as an oracle either.
4. Tier-1: T1-33 (`shell.scad:381-384`) compares groove depth to lid thickness only. The lid-vent plan
   (`docs/plans/2026-09-09-lid-vents.md` §2.2) added T1-37 keep-outs around every fastener, but only to
   protect the vent field.
5. The STEP the specialist opens was faceted until D39 (2026-09-28, `csg_to_step.py`): true circles
   made the ring and its opening plainly visible.

## 3. When it was introduced

| Commit | Date | Relevance |
|---|---|---|
| `fcfdf56` | 2026-09-07 | `mcc_captive_thumbscrew_hole()` with `head_d = 8`, `counterbore_depth = lid_t / 2` (pickaxe on `counterbore_depth`: this commit only; unchanged since). |
| `b6a8b77` | 2026-09-08 | First full case: `mcc_shell_lid()`, `_mcc_tg_frame()`, `MCC_FASTENER_INSET`, `MCC_TG_W/H`. **The defect exists from here.** A scratch render of this commit (NDI to HDMI, `lid.model.stl`) has the same 3 holes with 11.383 mm² each. |
| `b897d52`, `a43ecb3` | 2026-09-08/09 | Plus lid golden; lid vent field. Neither touches the groove or the counterbore. |
| `2235a92`, `7bdcbe4` | 2026-09-28 | D32 lid lip added, then removed by D36. Below the underside, not involved. |

`MCC_TG_W`, `MCC_TG_H`, `MCC_CLR_TG`, `MCC_LID_T`, `MCC_T_PATCH`, `MCC_WALL` and `MCC_FASTENER_INSET` have
the same values at every one of these commits where the constant exists (checked with
`git show <commit>:lib/mcc/constants.scad` at `b6a8b77`, `a43ecb3`, `2235a92`, `7bdcbe4`, `40bdbb6`,
`baacd6c` and HEAD). The exact STEP converter arrived with `1ad78e6` (D39, 2026-09-28).

## 4. Fix options and the recommendation

Every option must (a) remove the opening, (b) also remove the 0.05 mm hole-to-groove wall, (c) keep
the case height at 51 mm (fixed decision), (d) keep the base and lid slicer-clean.

| Option | What changes | Printability and slicer gate | Thumbscrew (captive) function | Tongue-and-groove seal and strength | Goldens | Verdict |
|---|---|---|---|---|---|---|
| **T** (recommended) | On the +Y patch side only, the tongue-and-groove frame moves outward: tongue inner edge 4.5 mm from the wall's outer face (new `MCC_TG_PATCH_INSET`). Tongue at 2.9 to 4.5 mm, groove at 2.65 to 4.75 mm. Fasteners stay at 10 mm. | Verified by slicing: Plus and compact base and lid, 0 warnings. The tongue stands on solid wall (only its outer 0.1 mm is over the chamfered roof of the bezel recess, where the wall is still 2.9 mm thick). Lid prints as before. | Counterbore and hole unchanged and now complete on all 6; web to the groove 1.245 mm (≥ 1.2). The lid underside around every hole stays flat, free for a future retention feature. | Frame stays continuous and closed; the tongue still sits fully on wall; skin outside the groove on the patch side 2.65 mm (was 6.15; other sides unchanged at 1.15). | Lid −46.48 mm³ (−0.049 %), base +22.40 mm³ (+0.009 %) on every SKU: inside tolerance, refresh anyway. | **Do this.** |
| A | Move the 3 patch-side fasteners inward: axis at 13.5 mm (needs ≥ 8.25 + 4.005 + 1.2 = 13.46). | Bosses, gussets and insert bores move 3.5 mm into the connector cable bay (the corners are where the outermost slot's cable turns). No assert relates bosses to plug envelopes and the plug lengths are `assumed` (M6, depth-mockup coupon, not printed): cannot be verified now. | Unchanged. | Unchanged. | All 16 case goldens move (boss geometry). | Rejected: unverifiable interior change. |
| B | Interrupt the frame: solid lid material (pad radius ≥ 5.2 = 4.005 + 1.2) over the groove at each of the 3 patch-side holes, and a matching notch (radius ≥ 5.45) in the base tongue. | Fine. | Unchanged. | Frame broken over about 10.4 mm at 3 places per lid; the tongue no longer guides the lid there. | Base and lid move slightly. | Rejected; the fallback if T were ever refused. |
| C | Drop the counterbore on the 3 patch-side holes only. | Fine. | Heads seat at two different heights (recessed on 3, proud on 3). | Unchanged. | Lid moves. | Rejected: the 0.05 mm wall between hole and groove stays. |
| D | Smaller or shallower counterbore. | Not possible: the roof over the groove is 1.0 mm and the counterbore is 1.5 mm deep; a rim 1.2 mm clear of the groove would need r ≤ 0.55 mm, less than the through-hole. | | | | Rejected: impossible. |
| E | Locally thicker lid, or raise the outer face. | | | | | Rejected: case height 51 mm is a fixed decision. |
| F | Jog the frame around each hole (both parts). | Fine but two new parametric shapes and a 45° transition each. | Unchanged. | Continuous. | Both move. | Rejected: more code than T for the same result. |
| G | No counterbore anywhere. | Fine. | Heads stand proud (recess was the design intent). | Unchanged. | Lid moves. | Deferred to the hardware decision (Q24); the 0.05 mm wall would still need T. |

Decision: **Option T** with `MCC_TG_PATCH_INSET` = 4.5. It is the largest round value that keeps the web:
10 (`MCC_FASTENER_INSET`) − 4.005 (counterbore rim) − 0.25 (`MCC_CLR_TG`) − 1.2 (web minimum) = 4.545.
The web minimum is the repo's own three-perimeter rule (`MCC_WALL_BORE_WEB_MIN` = 1.2,
`fdm-rugged-enclosure-guidelines.md:35`). Limit of the design: the counterbore may grow only to
Ø 8.09 mm before T1-91 fires (vertex radius 4.05 = 10 − 4.75 − 1.2); see R48 and Q24 in section 13.

## 5. Implementation (developer; after the architect gate in section 9)

### 5.0 Preconditions

1. `git fetch origin`, then branch `feature/lid-screw-hole-openings` off `main` (no issue number is known;
   if the teamlead opens one, name it `feature/issue-<n>-lid-screw-hole-openings`). Never commit on `main`.
2. `python scripts/build.py doctor` must be green. Working tree clean.
3. The shell hook of this workstation creates zero-byte files in the repo root from tool text that
   contains a hyphen followed by a greater-than sign and a word. Run `git status --short` after every
   step and delete only new zero-byte files that you can trace to your own text.

### 5.1 Apply the patch

```
git apply --check G-lid-screw-hole-openings.patch
git apply G-lid-screw-hole-openings.patch
git diff --stat
```

Expected stat: 6 files, 153 insertions, 20 deletions (`constants.scad` 10, `fasteners.scad` 7,
`shell.scad` 46, `tests/test_shell.scad` 3, `scripts/printability.py` 83, `scripts/build.py` 24).
The patch was generated against 24c52c8 and `git apply --check` is clean there. If `main` has moved and
the check fails, apply the hunks by hand from section 5.2; each old block occurs exactly once. The full
patch text is Appendix A.

### 5.2 What each hunk does (for a manual apply)

| # | File | Change |
|---|---|---|
| 1 | `lib/mcc/constants.scad` after `MCC_TG_H` (line 509-510) | Add `MCC_TG_PATCH_INSET = 4.5;`, `MCC_LID_CB_D = 8.0;`, `MCC_LID_CB_WEB_MIN = 1.2;` with their comments. |
| 2 | `lib/mcc/fasteners.scad:87` and its argument doc | `head_d = 8` becomes `head_d = MCC_LID_CB_D` (same value, one definition). The counterbore depth stays `lid_t / 2`. |
| 3a | `lib/mcc/shell.scad:102-108` | Replace `_mcc_cavity_rect()` by `_mcc_tg_rect()`: the same list, but the last element is `W - MCC_WALL - MCC_TG_PATCH_INSET` instead of `W - MCC_WALL - MCC_T_PATCH`. `_mcc_cavity_rect()` has no other caller (`grep -rn _mcc_cavity_rect lib models tests` gives only shell.scad). Update the `cav` argument doc of `_mcc_tg_frame()`. |
| 3b | `lib/mcc/shell.scad:263-271` (base tongue) | Call `_mcc_tg_frame(_mcc_tg_rect(L, W), 0, MCC_TG_W, ...)`; adjust the comment above it. |
| 3c | `lib/mcc/shell.scad` after the T1-33 asserts (line 384) | Add assert **T1-92** (`MCC_WALL <= MCC_TG_PATCH_INSET <= MCC_T_PATCH`) and the per-fastener assert **T1-91** (counterbore rim at least `MCC_LID_CB_WEB_MIN` from the groove ring's inner edge; the fastener must lie inside the ring). |
| 3d | `lib/mcc/shell.scad:400` (lid groove) | Call `_mcc_tg_frame(_mcc_tg_rect(L, W), -MCC_CLR_TG, MCC_TG_W + MCC_CLR_TG, ...)`. |
| 4 | `tests/test_shell.scad` | One more line: the Plus-family lid (`DEV_PLUS`, `VARIANT_PLUS_SWITCH`) so T1-91/T1-92 run on both families in `smoke`. |
| 5 | `scripts/printability.py` | Constants `SEE_THROUGH_*`, import `Polygon`, dataclass `SeeThrough`, `_section_levels()`, `non_prismatic_see_through(mesh)`, `selftest_see_through()`, one docstring bullet. |
| 6 | `scripts/build.py` | `MeshCheck.see_through` and `see_through_ok` (part of `ok`); `check_mesh()` runs the check when the file is `lid.stl`; the `ci` failure string and the `check` output list the openings; `cmd_smoke` appends the self-test as a result row. |

The resulting geometry: the base's tongue and the lid's groove on the +Y wall sit at 2.9 to 4.5 mm and
2.65 to 4.75 mm from the outer face (were 6.4 to 8.0 and 6.15 to 8.25); on the other three walls they
are unchanged (tongue 1.4 to 3.0 mm, groove 1.15 to 3.25 mm from the outer face). Base +22.40 mm³ (the
two X-side tongue segments are 3.5 mm longer), lid −46.48 mm³.

### 5.3 What must NOT change

`MCC_FASTENER_INSET`, `layout.scad` (fastener positions), the bosses, gussets and insert bores,
`vents.scad` (T1-37(a) stays true, its +Y bound is now conservative by 3.5 mm), the `_mcc_tg_frame()`
body, `MCC_TG_W`, `MCC_TG_H`, `MCC_CLR_TG`, the counterbore depth, `MCC_LID_T`. No golden is edited by
hand (section 8). Do not add explanatory comments beyond those in the patch.

## 6. Regression guards: exactly what would have caught it

| Guard | Layer | Fires when | Proof that it would have caught the original defect |
|---|---|---|---|
| **T1-91** (per fastener) and **T1-92** in `mcc_shell_lid()` | Tier 1: every lid render, `smoke` (via `tests/test_shell.scad`, both families) and `ci` | the counterbore rim is closer than `MCC_LID_CB_WEB_MIN` (1.2 mm) to the groove ring, or `MCC_TG_PATCH_INSET` leaves `[MCC_WALL, MCC_T_PATCH]` | With the old geometry forced by `-D MCC_TG_PATCH_INSET=8` the render stops with `mcc: T1-91 lid fastener [95.25, 73.175] counterbore rim is -2.25482 mm from the groove, below MCC_LID_CB_WEB_MIN=1.2 on "pro-convert-hdmi-plus"`. At `b6a8b77` the same expression gives the same −2.25 mm. |
| `non_prismatic_see_through()` in `scripts/printability.py`, run by `check_mesh()` for `lid.stl` | Tier 3: `build.py check`, `check --all`, every `ci` part group | ANY see-through opening in a lid that is not one prismatic cut, whatever the cause (counterbore against groove, a future retention pocket against the groove, a vent slot against a hole, ...) | On the current main-branch lids: `build.py check exports\<slug>\lid.stl` exits 1 with `accidental_openings=3`, area 11.39 mm² each; 24 findings over the 8 SKUs, 0.1 s per lid. On the patched lids: 0. Through-holes (also counterbored) and vent slots pass. |
| `selftest_see_through()` | Tier 2: `build.py smoke` (CI job "OpenSCAD asserts (smoke tests)") | the check itself stops working (a refactor that makes it always pass) | A synthetic lid whose groove crosses a counterbore must give exactly 1 finding, one with the groove 6 mm away none. |

How the mesh check works (so a reviewer can trust it): slice the lid at the middle of every z-interval
between two consecutive vertex heights (the model is prismatic in between); the see-through region is the
intersection of the void regions of all slices; a drawn opening is bounded by material all round at some
height, so each connected piece of the see-through region must coincide with one connected void of at
least one slice. A counterbore floor that breaks into a groove has an outline made of an arc (counterbore,
only above z = 49.5) and a chord (groove, only below z = 50): no slice bounds it all round, so it is
reported.

Limits, recorded on purpose:

- The mesh check is name-based (`lid.stl`), so it covers the 8 case lids only. Brackets and coupons
  have no lid.
- Do not extend it to bases without rework: on the Plus base it needs 540 slices (320 s) and reports
  the −X splitter tie-down slot (3.0 mm², it straddles the −X wall's inner face) as non-prismatic.
- A conical countersink in a lid would be reported (no slice bounds its narrowest circle all round);
  the lid has none. If one is ever wanted, extend the check for it in the same change.
- A golden field for the see-through area was considered and rejected: a golden records what the
  geometry is, it cannot say that it is wrong (the first lid golden already contained the openings).
- Why nothing existing could see it is in section 2.3.

## 7. Verification (commands from the repo root, PowerShell; none needs a redirect)

Interpreter: `.venv\Scripts\python.exe` (called `python` below). OpenSCAD: `--backend=Manifold` with
`OPENSCADPATH=lib` (build.py sets it).

### 7.1 Before applying the patch: save the negative control

On the clean `main`, so the old, defective lid exists as a file:

```
python scripts/build.py render pro-convert-hdmi-plus pro-convert-for-ndi-to-hdmi --part lid
New-Item -ItemType Directory -Force "$env:TEMP\mcc-old-lid\plus", "$env:TEMP\mcc-old-lid\compact"
Copy-Item exports\pro-convert-hdmi-plus\lid.stl "$env:TEMP\mcc-old-lid\plus\lid.stl"
Copy-Item exports\pro-convert-for-ndi-to-hdmi\lid.stl "$env:TEMP\mcc-old-lid\compact\lid.stl"
```

(The file must be named `lid.stl`: that is how `check_mesh()` recognises a case lid.)

### 7.2 After applying the patch

| # | Command | Expected |
|---|---|---|
| 1 | `python scripts/build.py smoke` | 12 of 12 pass, including `tests\test_shell.scad` and `scripts/printability.py selftest_see_through()`. |
| 2 | `python scripts/build.py check "$env:TEMP\mcc-old-lid\plus\lid.stl" "$env:TEMP\mcc-old-lid\compact\lid.stl"` | **FAIL, exit 1**: `accidental_openings=3` on each, three `ACCIDENTAL OPENING area=11.39mm2` lines each. This proves the new check would have caught the defect. |
| 3 | `$env:OPENSCADPATH = "$PWD\lib"` then `& "C:\Program Files\OpenSCAD (Nightly)\openscad.com" --backend=Manifold -D 'part="lid"' -D MCC_TG_PATCH_INSET=8 -o "$env:TEMP\neg.csg" models\pro-convert-hdmi-plus\case.scad` | **ERROR** `mcc: T1-91 lid fastener [95.25, 73.175] counterbore rim is -2.25482 mm from the groove, below MCC_LID_CB_WEB_MIN=1.2 on "pro-convert-hdmi-plus"` (this forces the old geometry). |
| 4 | the same with `-D MCC_LID_CB_D=12` instead | **ERROR** T1-91, rim `-0.757236` mm. |
| 5 | the same with `-D MCC_TG_PATCH_INSET=2` instead | **ERROR** `mcc: T1-92 MCC_TG_PATCH_INSET=2 outside [MCC_WALL=3, MCC_T_PATCH=8]`. |
| 6 | the same with no `-D` besides the part | no ERROR, exit 0. |
| 7 | `python scripts/build.py render pro-convert-hdmi-tx pro-convert-sdi-tx pro-convert-hdmi-plus pro-convert-sdi-plus pro-convert-for-ndi-to-hdmi pro-convert-for-ndi-to-hdmi-4k pro-convert-for-ndi-to-sdi pro-convert-for-ndi-to-aio` | all `base`, `lid` (and `base_fan`) PASS. |
| 8 | `python scripts/build.py check --all` | every `lid.stl` line ends `floating_islands=0 cantilevers=0 accidental_openings=0`; all bases 0 islands, 0 cantilevers. |
| 9 | `python scripts/build.py golden pro-convert-hdmi-tx ...` (the 8 slugs) | PASS on all (deltas inside tolerance, facet counts informational). Then refresh, section 8. |
| 10 | `python scripts/build.py slicer-check <the 8 slugs> --jobs 3` | every part PASS, no warning (Bambu Studio 02.08.02.61). |
| 11 | `python scripts/build.py step pro-convert-hdmi-plus --part lid` | `exact (csg): ok=True valid=True` and `faces=258 cylindrical=12` (was 263 faces), STEP volume 94715.6. |
| 12 | (CI equivalent, all gates per part) `python scripts/build.py ci --group 1/6 --jobs 3`, then 2/6 to 6/6 | 6 groups green, then push and wait for the GitHub `render` check to finish green before merging. |

`check --all` globs `exports/**/*.stl`: remove stale export folders (for example an old `_stale-*` directory
holding pre-fix lids) before step 8, otherwise those old `lid.stl` files fail the new check by design.

### 7.3 Numbers measured on the patched scratch tree (compare with your run)

| Slug | Lid volume mm³ (print STL) | Old | Change |
|---|---|---|---|
| pro-convert-hdmi-tx / -for-ndi-to-hdmi | 84285.23 | 84331.71 | −46.48 |
| pro-convert-sdi-tx / -for-ndi-to-sdi | 84151.27 | 84197.75 | −46.48 |
| pro-convert-for-ndi-to-aio | 84756.38 | 84802.86 | −46.48 |
| pro-convert-hdmi-plus / -for-ndi-to-hdmi-4k | 94716.47 | 94762.95 | −46.48 |
| pro-convert-sdi-plus | 94549.72 | 94596.20 | −46.48 |

Bases: Plus 258069.4 mm³ (old 258046.99, +22.40), NDI to HDMI 238361.4 (+22.40), its `base_fan` 236441.3.
Whole gate on the patched scratch tree, all 8 SKUs (17 parts): `smoke` 12 of 12, `check --all` 17 of 17
(every lid `accidental_openings=0`, every part 0 floating islands and 0 cantilevers), `golden` 17 of 17,
`slicer-check` 17 of 17 without a warning (Bambu Studio, X1C, ASA). Bases g / h: hdmi-tx 197.2 / 5.89,
sdi-tx 196.9 / 5.87, hdmi-plus 210.7 / 6.51, sdi-plus 210.4 / 6.47, ndi-to-hdmi 195.2 / 5.90 (`base_fan`
193.3 / 5.97), ndi-to-hdmi-4k 210.7 / 6.51, ndi-to-sdi 194.9 / 5.88, ndi-to-aio 195.8 / 5.91. Lids: 61.0 g
1.82 h (compact, TX, ndi-to-hdmi), 60.9 g 1.82 h (SDI), 61.3 g 1.83 h (aio), 68.5 g 2.03 h (Plus, 4k), 68.4 g
2.02 h (sdi-plus).
Also verified by the researcher on the patched Plus and NDI to HDMI: interference volume base AND lid
0.000000 mm³ (assembled pose); the tongue grown by 0.249 mm lies entirely inside the groove void, grown by
0.251 mm it does not, i.e. the clearance is exactly `MCC_CLR_TG` = 0.25 mm all round; the patched Plus
STEP has 6 counterbore floors at z = 49.5, each one face of 41.286 mm².

## 8. Goldens to refresh

The golden check passes without an update (every delta below is far inside the 0.5 % volume and 1 % area
tolerances), but the committed numbers must match the committed geometry, so refresh them, explicitly,
after every gate in section 7.2 is green:

```
python scripts/build.py golden --update pro-convert-hdmi-tx pro-convert-sdi-tx pro-convert-hdmi-plus pro-convert-sdi-plus pro-convert-for-ndi-to-hdmi pro-convert-for-ndi-to-hdmi-4k pro-convert-for-ndi-to-sdi pro-convert-for-ndi-to-aio
git diff --stat tests/golden
```

Exactly **17 files** must change, and nothing else under `tests/golden` (no coupon, no bracket; the
`tg-ladder` coupon builds its own tongue and groove and is not affected):

- `tests/golden/<slug>.base.json` and `tests/golden/<slug>.lid.json` for the 8 slugs `pro-convert-hdmi-tx`,
  `pro-convert-sdi-tx`, `pro-convert-hdmi-plus`, `pro-convert-sdi-plus`, `pro-convert-for-ndi-to-hdmi`,
  `pro-convert-for-ndi-to-hdmi-4k`, `pro-convert-for-ndi-to-sdi`, `pro-convert-for-ndi-to-aio` (16 files);
- `tests/golden/pro-convert-for-ndi-to-hdmi.base_fan.json` (1 file).

Expected change per file, the same on every SKU (measured on the patched scratch tree):

| Part | Volume | Area | bbox | Facets |
|---|---|---|---|---|
| base and `base_fan` | +22.40 mm³ (+0.009 %) | +28.0 mm² (+0.02 %) | unchanged | change (informational) |
| lid | −46.48 mm³ (−0.05 %) | +120.5 mm² (+0.17 %) | unchanged | change (informational) |

Why: the two X-side tongue segments are 3.5 mm longer (base +22.40 = 7 x 1.6 x 2.0), the groove is 7 mm longer
(−29.4) and each counterbore no longer shares 5.7 mm³ with the groove (−17.1, three of them) on the lid.
If any file shows a different volume delta, a bbox change, or a golden outside this list changes, stop and
find out why before committing. State the table above in the PR description (repo policy: a golden change
must be justified in the PR).

## 9. Architect gate: what must be recorded (`architecture.md` revision 19 and friends)

The change is small and local, but it reverses one rule (rev-5 ruling 4: the tongue is flush with the
wall's inner face) on one wall, so the mandatory gate applies. Please validate: (a) that the patch-side
offset is the right way to resolve the collision, against options A and B in section 4; (b) that
`MCC_TG_PATCH_INSET` = 4.5 and the 1.2 mm web minimum are acceptable `assumed` values; (c) that the
Tier-3 check may stay lid-only. Then record:

1. **§13 deviation row D52.** Confirmed next free: the last numbered row of §13 is D51 (D11 is listed
   after it out of order), `docs/plans/2026-09-28-vesa-column-bracket.md:781` reserves "T1-91, D52, R48,
   M23, Q24" as the next free ids, and a search of the repo finds no D52 or T1-91 anywhere. Proposed row:

   | D52 | 2026-09-29 | §5 lid row and `layout-patch-wall.md` §15 ruling 4 / T1-33: the tongue is flush with the wall's inner face and the groove is that frame widened by the clearance; the lid is one 3 mm slab, so its features must not cut through each other | `lib/mcc/shell.scad:400` with `lib/mcc/fasteners.scad:87-98` and `lib/mcc/constants.scad:373`: on the 8 mm patch wall the groove (6.15 to 8.25 mm from the outer face, 2.0 mm deep) runs through the Ø8 counterbore (rim 5.995 mm, floor 1.5 mm below the outer face) of the three patch-wall lid fasteners at `MCC_FASTENER_INSET` = 10; the cuts overlap 0.5 mm in Z, so 11.38 mm² (27.6 %) of each counterbore floor is open into the groove on all 8 SKUs (24 holes), and the through-hole is 0.05 mm from the groove | The external CAD specialist opening `lid.step` saw white crescents in the screw-hole counterbores. Latent since `b6a8b77` (2026-09-08); `check`, the slicer gate, the goldens (0.018 % of the volume) and T1-33 all pass on it | **Fixed (rev 19, plan G, option T):** on the +Y wall the tongue-and-groove frame is offset outward, `MCC_TG_PATCH_INSET` = 4.5 (tongue 2.9 to 4.5 mm, groove 2.65 to 4.75 mm from the outer face); fasteners, bosses and inserts do not move. New `MCC_LID_CB_D` (8.0, `assumed`, was a literal) and `MCC_LID_CB_WEB_MIN` (1.2); asserts **T1-91**, **T1-92**; Tier-3 `non_prismatic_see_through()` on `lid.stl` and its `smoke` self-test. Options rejected: move the fasteners (unverifiable cable-bay change), interrupt the frame with a pad and a tongue notch (fallback), drop the counterbore, thicker lid |

2. **Revision 19 header paragraph** (top of `architecture.md`, above rev 18): the D52 finding and fix in
   three sentences, "New: T1-91, T1-92, R48, M23, Q24, D52; the case envelope does not move; base +22.40
   mm³, lid −46.48 mm³ on every SKU".
3. **§5 table, row "Lid"**: replace "the tongue/groove runs unbroken" by "the tongue/groove runs unbroken;
   on the +Y patch wall the frame is offset outward by `MCC_TG_PATCH_INSET` (D52)".
4. **§9 assert table and `layout-patch-wall.md` §9**: rows T1-91 (counterbore rim to groove ring at least
   `MCC_LID_CB_WEB_MIN`, evaluated in `mcc_shell_lid()` for every fastener) and T1-92
   (`MCC_WALL <= MCC_TG_PATCH_INSET <= MCC_T_PATCH`); state "the next free id is T1-93". §9 Tier 3 and
   `.claude/knowledge/testing.md`: `check` also runs the lid see-through check; `smoke` also runs its
   self-test.
5. **`layout-patch-wall.md`**: §15 ruling 4 and the constants table row for `MCC_TG_W` / `MCC_TG_H`
   (line 1471, "tongue flush with the wall's inner face") get "except on the +Y wall, D52"; add the three
   new constants to the constants list; §6 (lid fasteners) gets one sentence on the counterbore web rule.
6. **Risk, measurement, question** (next free R48, M23, Q24):
   - **R48**: the thumbscrew hardware is undecided. The Ø8 x 1.5 counterbore is `assumed`; a DIN 653
     low-type M3 knurled thumb screw has a Ø12 head (dk max 12.35, k max 2.5;
     https://fullerfasteners.com/tech/din-653-specifications-knurled-thumb-screws-low-type/), which fits no
     counterbore that clears the frame at `MCC_FASTENER_INSET` = 10. With option T, T1-91 fires above
     `MCC_LID_CB_D` = 8.09 mm (vertex radius 4.05 = 10 − 4.75 − 1.2); the far walls allow 11.09 mm.
   - **M23**: buy the intended thumbscrews and measure head diameter, head height, shank and how they
     are made captive (the model has nothing that retains the screw: the counterbore only seats the head).
   - **Q24**: which thumbscrew, and which captive method (section 13).
7. **`CLAUDE.md`** "Standard commands" (`check` line) and **`scripts/README.md:68`** (the `check --all` row):
   add "and no accidental see-through opening in a case lid".
8. **Decision record for this session**: the D52 row above is the decision log (this repo has no separate
   `decision-log.md`); the PR description carries the rationale, the code carries none.
9. The developer adds the CHANGELOG entry (section 10) and copies this plan to
   `docs/plans/2026-09-29-lid-screw-hole-openings.md` (the repo's plan convention, `ticket-source.md`).

## 10. CHANGELOG entry and PR description (developer)

Add to `CHANGELOG.md` under `## [Unreleased]`, as a new subsection above the existing ones:

```
### Fixed (2026-09-29, external CAD review of `lid.step`): a base printed before this change does not mate with a lid printed after it

- **Lid thumbscrew holes had openings** (architecture.md D52): on all 8 SKUs the 3 patch-wall-side holes (the
  two (±X, +Y) corners and the patch-wall middle one) had a see-through opening in the Ø8 counterbore floor,
  11.4 mm² each, where the lid's groove crossed the counterbore. The tongue-and-groove frame on the +Y patch
  wall now sits 4.5 mm from the outer face (`MCC_TG_PATCH_INSET`), clear of the counterbores. The other three
  walls and every fastener, boss and insert position are unchanged. No full case has been printed yet.
- New guards: asserts T1-91 and T1-92 in `mcc_shell_lid()`; `build.py check` fails a lid with an accidental
  see-through opening; `build.py smoke` runs a self-test of that check.
```

PR description: the summary table of section 0, the images `before_after_pro-convert-hdmi-plus.png` and
`hero_pro-convert-hdmi-plus.png` (attach), the golden explanation of section 8, and the gate results of
section 7.2 (steps 1, 2, 3 to 6, 8 to 11 and the six `ci` groups). Do not merge while any GitHub check is
pending or failing. The teamlead decides whether the specialist gets the new `lid.step` and `base.step`
from the release pre-release zips (his CAD work on the +Y tongue and groove, if any, moves by 3.5 mm).

## 11. Observations outside this fix (do not act on them here)

1. **Splitter tie-down slot straddles the −X wall** (found while testing the mesh check on a base):
   `mcc_splitter_tiedown(orient = "edge")` puts its two slots at `±dims[0] / 2 = ±10` mm from the bay
   centre, which is exactly the bay edge; the −X slot (1.5 × 4 mm, x −103.0 to −101.5 on the Plus) is
   centred on the −X wall's inner face (x = −102.25), so it cuts 0.75 mm into the wall foot and only half
   of it (3.0 mm²) is open interior. Cosmetic/small; needs its own ticket.
2. **The thumbscrew is not captive in the model.** `fasteners.scad:71-78` says the counterbore stops the head
   pulling through and keeps the screw captive when backed out; it only seats the head. Nothing retains the
   screw once it is unscrewed from the insert (no groove, E-clip or O-ring pocket; Ø3.4 hole for an M3).
   See Q24. The `TODO(teamlead)` in that header (confirm the counterbore depth against a real head) is still
   open.
3. Zero-byte stray files appeared in the repo root while this research ran, made by the workstation's
   shell hook from tool text. Those traced to this research's own text (`cb`, `cut`, `missing` twice,
   `1.750`, `MCC_TG_W`; `0.999)` may be older) were deleted at once. `lower-flank`, `residual`, `2` and
   `CANTILEVER_REACH` appeared later and match nothing written here (another session is probably active in
   the repo); they were left alone. Nothing tracked was touched.


## 12. Text for the GitHub issue comment (NOT posted; the teamlead posts it or opens the issue)

> Lid thumbscrew holes: openings in the counterbore (external CAD review of `lid.step`, 2026-09-29).
> **Scope of impact:** all 8 SKUs, 3 of the 6 lid holes each (the two (±X, +Y) corners and the patch-wall
> middle one): 24 holes. Each has a see-through opening of 11.38 mm² (27.6 % of the counterbore annulus) in
> the counterbore floor; the same in the print STL and in the exact STEP (broken floor faces 29.649 + 0.229
> instead of 41.286 mm²). The three far-wall holes are intact.
> **Cause:** the lid groove (`shell.scad:400`, 2.0 mm deep) crosses the Ø8 counterbore (`fasteners.scad:87-98`,
> floor 0.5 mm below the groove ceiling) on the 8 mm patch wall, where the groove runs 6.15 to 8.25 mm from
> the outer face and the fasteners sit 10 mm in. Latent since `b6a8b77` (2026-09-08). No gate saw it:
> `check`, the slicer gate (0 warnings), the goldens (0.018 % of the volume) and T1-33 all pass.
> **Files:** `lib/mcc/shell.scad`, `lib/mcc/constants.scad`, `lib/mcc/fasteners.scad`, `tests/test_shell.scad`,
> `scripts/printability.py`, `scripts/build.py`; goldens: 17 files (8 bases, 8 lids, `base_fan`).
> **Plan:** on the +Y wall only, move the tongue-and-groove frame outward (`MCC_TG_PATCH_INSET` = 4.5 mm);
> fasteners and bosses stay; asserts T1-91/T1-92; a Tier-3 check that fails a lid with an accidental
> see-through opening (it fails on today's main-branch lids: 24 findings); a smoke self-test. Verified in a
> scratch copy: 0 openings on all 8 lids, STEP floors intact, base/lid interference 0, slicer gate clean.
> Open: which thumbscrew (a DIN 653 M3 head is Ø12; the model assumes Ø8 x 1.5).

## Appendix A: the patch (`G-lid-screw-hole-openings.patch`, against main @ 24c52c8)

Apply from the repo root with `git apply G-lid-screw-hole-openings.patch` (check first with `--check`).

```diff
diff --git a/lib/mcc/constants.scad b/lib/mcc/constants.scad
--- a/lib/mcc/constants.scad
+++ b/lib/mcc/constants.scad
@@ -508,6 +508,16 @@
 MCC_TG_W = 1.6; // tongue/groove nominal width, mm. layout-patch-wall.md §15 ruling 4.
 MCC_TG_H = 2.0; // tongue/groove depth, mm. Same ruling — leaves MCC_LID_T - MCC_TG_H = 1.0 mm of
                  // lid material above the groove (T1-33).
+MCC_TG_PATCH_INSET = 4.5; // +Y patch wall only: distance from the wall's outer face to the tongue's
+                           // inner edge, mm (tongue at [inset - MCC_TG_W, inset]); the other three walls
+                           // keep the tongue flush with their inner face. Largest round value that keeps
+                           // MCC_LID_CB_WEB_MIN at the fastener ring: MCC_FASTENER_INSET 10 - counterbore
+                           // rim 4.005 - MCC_CLR_TG 0.25 - 1.2 = 4.545. T1-91, T1-92.
+MCC_LID_CB_D = 8.0; // lid thumbscrew counterbore diameter, mm. assumed -- no sourced figure (was the
+                     // literal `head_d = 8` in fasteners.scad). Modelled circum=true, $fn=64. T1-91.
+MCC_LID_CB_WEB_MIN = 1.2; // minimum lid material between a counterbore rim and the groove, mm: three
+                           // 0.4 mm perimeters, same rule as MCC_WALL_BORE_WEB_MIN. assumed --
+                           // knowledge/design/fdm-rugged-enclosure-guidelines.md:35. T1-91.
 
 MCC_LID_CLEAR = 2.0; // minimum plenum between the cradle deck top + device height and the lid
                       // underside, mm. layout-patch-wall.md §15 ruling 3 (ACCEPTED) — mirrors this
diff --git a/lib/mcc/fasteners.scad b/lib/mcc/fasteners.scad
--- a/lib/mcc/fasteners.scad
+++ b/lib/mcc/fasteners.scad
@@ -80,11 +80,10 @@
 //   height before finalizing the lid design.
 // Arguments:
 //   d      = shaft clearance diameter, mm. Default: MCC_M3_CLR_D.
-//   head_d = counterbore (head-trap) diameter, mm. Default: 8 (assumed — a typical M3 knurled
-//            thumbscrew head is 6-8 mm per generic hardware guides, no sourced figure in
-//            knowledge/components/fasteners-and-hardware.md).
+//   head_d = counterbore (head-trap) diameter, mm. Default: MCC_LID_CB_D (constants.scad; assumed,
+//            no sourced figure in knowledge/components/fasteners-and-hardware.md).
 //   lid_t  = lid thickness at this location, mm (required).
-module mcc_captive_thumbscrew_hole(d = MCC_M3_CLR_D, head_d = 8, lid_t) {
+module mcc_captive_thumbscrew_hole(d = MCC_M3_CLR_D, head_d = MCC_LID_CB_D, lid_t) {
     assert(head_d > d, str("mcc: head_d=", head_d, " must exceed shaft clearance d=", d));
     counterbore_depth = lid_t / 2; // assumed — see TODO above.
     assert(counterbore_depth < lid_t,
diff --git a/lib/mcc/shell.scad b/lib/mcc/shell.scad
--- a/lib/mcc/shell.scad
+++ b/lib/mcc/shell.scad
@@ -99,13 +99,15 @@
             }
 }
 
-// Function: _mcc_cavity_rect()
-// Description:
-//   Private. [x0, y0, w, h] of the interior-cavity footprint (the same rectangle
-//   _mcc_outer_shell_solid() subtracts), shared by the tongue/groove helper below so the two can
-//   never disagree about where the cavity boundary actually is.
-function _mcc_cavity_rect(L, W) =
-    [-L / 2 + MCC_WALL, -W / 2 + MCC_WALL, L - 2 * MCC_WALL, W - MCC_WALL - MCC_T_PATCH];
+// Function: _mcc_tg_rect()
+// Description:
+//   Private. [x0, y0, w, h] of the rectangle the tongue-and-groove frame is offset from (see
+//   _mcc_tg_frame()), shared by the base's tongue and the lid's groove so the two can never disagree.
+//   On the -Y and +-X sides it is the interior-cavity boundary (tongue flush with the wall's inner
+//   face); on the +Y patch side its edge sits MCC_TG_PATCH_INSET from the wall's outer face, clear of
+//   the lid's thumbscrew counterbores (T1-91).
+function _mcc_tg_rect(L, W) =
+    [-L / 2 + MCC_WALL, -W / 2 + MCC_WALL, L - 2 * MCC_WALL, W - MCC_WALL - MCC_TG_PATCH_INSET];
 
 // Module: _mcc_tg_frame()
 // Description:
@@ -116,7 +118,7 @@
 //   can never drift out of the "groove width = tongue width + 2*clearance" relationship
 //   (tg-ladder.scad's own convention).
 // Arguments:
-//   cav        = [x0,y0,w,h] cavity rect (_mcc_cavity_rect()).
+//   cav        = [x0,y0,w,h] frame reference rect (_mcc_tg_rect()).
 //   r_lo, r_hi = radial offsets from the cavity boundary, mm.
 //   z0, height = Z placement.
 module _mcc_tg_frame(cav, r_lo, r_hi, z0, height) {
@@ -260,15 +262,16 @@
             union() {
                 _mcc_outer_shell_solid(L, W, 0, z_top, MCC_FLOOR_T, z_top + MCC_EPS);
 
-                // Tongue (D-07): offset/shiplap, flush with the wall's inner face, rev-5 ruling 4.
-                // Grows OUTWARD (toward the wall's own outer face) by MCC_TG_W from the
-                // interior-cavity footprint, so it sits ON TOP of solid wall material (every wall
-                // is >= MCC_TG_W thick) rather than cantilevering out over open interior air.
+                // Tongue (D-07): offset/shiplap, flush with the inner face of the -Y/+-X walls and
+                // MCC_TG_PATCH_INSET from the patch wall's outer face (_mcc_tg_rect()). Grows OUTWARD
+                // (toward the wall's own outer face) by MCC_TG_W from that rectangle, so it sits ON TOP
+                // of solid wall material (every wall is >= MCC_TG_W thick) rather than cantilevering
+                // out over open interior air.
                 // Starts MCC_EPS below z_top so it genuinely penetrates the wall's own solid
                 // there instead of merely sitting flush on its top face — an exact coincident
                 // planar face between two independently-extruded solids is a known Manifold/
                 // STL-export degeneracy (same class of fix as the bore cuts split out below).
-                _mcc_tg_frame(_mcc_cavity_rect(L, W), 0, MCC_TG_W, z_top - MCC_EPS, MCC_TG_H + MCC_EPS);
+                _mcc_tg_frame(_mcc_tg_rect(L, W), 0, MCC_TG_W, z_top - MCC_EPS, MCC_TG_H + MCC_EPS);
 
                 // Side-bolt boss (far wall, D-09/D-13) -- exact placement per the developer contract.
                 translate([x_bolt, -W / 2 - MCC_SIDE_BOLT_PROUD, z_bolt])
@@ -382,6 +385,21 @@
         str("mcc: T1-33 MCC_TG_H+1.0=", MCC_TG_H + 1.0, " exceeds MCC_LID_T=", MCC_LID_T));
     assert(MCC_TG_W + 2 * MCC_CLR_TG <= MCC_WALL - 0.8,
         str("mcc: T1-33 tongue+clearance ", MCC_TG_W + 2 * MCC_CLR_TG, " does not fit MCC_WALL-0.8=", MCC_WALL - 0.8));
+    assert(MCC_TG_PATCH_INSET >= MCC_WALL - MCC_EPS && MCC_TG_PATCH_INSET <= MCC_T_PATCH + MCC_EPS,
+        str("mcc: T1-92 MCC_TG_PATCH_INSET=", MCC_TG_PATCH_INSET, " outside [MCC_WALL=", MCC_WALL,
+            ", MCC_T_PATCH=", MCC_T_PATCH, "]"));
+    // T1-91: web = counterbore rim to the groove ring's inner edge (gi = [x0, y0, x1, y1]).
+    tg = _mcc_tg_rect(L, W);
+    gi = [tg[0] + MCC_CLR_TG, tg[1] + MCC_CLR_TG, tg[0] + tg[2] - MCC_CLR_TG, tg[1] + tg[3] - MCC_CLR_TG];
+    cb_r = MCC_LID_CB_D / 2 / cos(180 / 64);
+    for (p = lid_pos) {
+        web = min([p[0] - gi[0], gi[2] - p[0], p[1] - gi[1], gi[3] - p[1]]) - cb_r;
+        assert(p[0] > gi[0] && p[0] < gi[2] && p[1] > gi[1] && p[1] < gi[3],
+            str("mcc: T1-91 lid fastener ", p, " is not inside the groove ring on \"", mcc_dev_slug(dev), "\""));
+        assert(web >= MCC_LID_CB_WEB_MIN - MCC_EPS,
+            str("mcc: T1-91 lid fastener ", p, " counterbore rim is ", web, " mm from the groove, below MCC_LID_CB_WEB_MIN=",
+                MCC_LID_CB_WEB_MIN, " on \"", mcc_dev_slug(dev), "\""));
+    }
     // This SKU's vent bands never cross into the lid's own Z range -- confirmed, not assumed
     // (plan §3.2's own caveat: "confirm this numerically before assuming it generalizes").
     assert(struct_val(l, "vent_intake_z")[1] <= z_top,
@@ -397,7 +415,7 @@
         // wider on BOTH its inner and outer edge than the tongue — "groove width = tongue width +
         // 2*clearance", this repo's own tg-ladder.scad convention — via the same _mcc_tg_frame()
         // helper mcc_shell_base()'s tongue uses, so the two can never drift apart.
-        _mcc_tg_frame(_mcc_cavity_rect(L, W), -MCC_CLR_TG, MCC_TG_W + MCC_CLR_TG, z_top - MCC_EPS, MCC_TG_H + MCC_EPS);
+        _mcc_tg_frame(_mcc_tg_rect(L, W), -MCC_CLR_TG, MCC_TG_W + MCC_CLR_TG, z_top - MCC_EPS, MCC_TG_H + MCC_EPS);
 
         for (p = lid_pos)
             translate([p[0], p[1], z_top - MCC_EPS])
diff --git a/tests/test_shell.scad b/tests/test_shell.scad
--- a/tests/test_shell.scad
+++ b/tests/test_shell.scad
@@ -65,6 +65,9 @@
 // --- shell.scad: plus-family base with fan=true + fan_switch=true (exercises the switch cutout) ---
 translate([1000, 0, 0]) mcc_shell_base(dev = DEV_PLUS, cfg = VARIANT_PLUS_SWITCH);
 
+// --- shell.scad: plus-family lid (T1-91/T1-92 on both families) ---
+translate([1000, 250, 0]) mcc_shell_lid(dev = DEV_PLUS, cfg = VARIANT_PLUS_SWITCH);
+
 // --- cradle.scad standalone ---
 // --- shell.scad: base with tripod_insert=false (issue #29 -- boss/collar/bore-cut all omitted) ---
 translate([250, 500, 0]) mcc_shell_base(dev = DEV, cfg = VARIANT_NO_TRIPOD);
diff --git a/scripts/printability.py b/scripts/printability.py
--- a/scripts/printability.py
+++ b/scripts/printability.py
@@ -11,6 +11,8 @@
   * unsupported overhang — layer area that sticks out more than one layer height (i.e. steeper
     than 45 deg) past the layer below. Reported for review, not failed on: flat bridges between
     walls are legitimate and the slicer bridges them.
+  * accidental see-through opening (lids only, non_prismatic_see_through()) — a hole nobody drew,
+    where two features that are each fine alone (a counterbore and a groove) together cut through.
 
 Needs trimesh + shapely (requirements.txt).
 """
@@ -21,7 +23,7 @@
 from dataclasses import dataclass, field
 
 import numpy as np
-from shapely.geometry import Point
+from shapely.geometry import Point, Polygon
 
 LAYER_H = 0.2             # mm — Bambu "0.20mm Standard @BBL X1C", the profile the projects ship with
 LINE_W = 0.42             # mm — the preset's line_width
@@ -31,6 +33,9 @@
 ISLAND_MIN_AREA = 0.2     # mm^2 — ignore tessellation slivers below this
 ISLAND_SUPPORT_FRAC = 0.02  # a region counts as supported when >= 2 % of it overlaps the layer below
 OVERHANG_REPORT_MIN = 20.0  # mm^2 per layer — smaller unsupported rims are just the 45 deg slope
+SEE_THROUGH_Z_MERGE = 0.01   # mm — vertex heights closer than this are one break-point
+SEE_THROUGH_MIN_AREA = 0.05  # mm^2 — ignore tessellation dust
+SEE_THROUGH_SAME_AREA = 0.05  # mm^2 — two outlines are the same when their symmetric difference is this small
 
 
 @dataclass
@@ -54,6 +59,12 @@
     area: float
     reach: float  # mm — farthest point of the overhang from where it attaches to the layer below
     bounds: tuple[float, float, float, float]
+
+
+@dataclass
+class SeeThrough:
+    area: float
+    centroid: tuple[float, float]
 
 
 @dataclass
@@ -137,3 +148,73 @@
             report.cantilevers += _cantilevers(layer, prev, z, layer_h)
         prev2, prev = prev, layer
     return report
+
+
+def _section_levels(mesh) -> list[float]:
+    """Mid-heights of the z-intervals between consecutive vertex heights (the model is prismatic in between)."""
+
+    zs = np.unique(np.round(np.asarray(mesh.vertices)[:, 2] / SEE_THROUGH_Z_MERGE) * SEE_THROUGH_Z_MERGE)
+    return [float((a + b) / 2) for a, b in zip(zs[:-1], zs[1:]) if b - a > 1.5 * SEE_THROUGH_Z_MERGE]
+
+
+def non_prismatic_see_through(mesh) -> list[SeeThrough]:
+    """Openings you can see through along Z that are not one cut. `mesh` is a trimesh.Trimesh in print pose.
+
+    A drawn opening (a through-hole, also one with a counterbore; a vent slot) is bounded by material all
+    round at some height. An accidental one, made by two features overlapping in plan, is bounded by an arc
+    of one and a chord of the other and by material at no height. The see-through region is the intersection
+    of the void regions of all slices; each connected piece of it must coincide with one connected void of at
+    least one slice. Returns the pieces that do not."""
+
+    from shapely.ops import unary_union
+
+    z0 = float(mesh.bounds[0][2])
+    levels = _section_levels(mesh)
+    if not levels:
+        return []
+    sections = mesh.section_multiplane([0.0, 0.0, z0], [0.0, 0.0, 1.0], [z - z0 for z in levels])
+    mats = [unary_union(sec.polygons_full).buffer(0) if sec is not None else Polygon() for sec in sections]
+    outline = unary_union([Polygon(p.exterior) for m in mats for p in (m.geoms if hasattr(m, "geoms") else [m])
+                           if not p.is_empty])
+    voids = [outline.difference(m).buffer(0) for m in mats]
+    see_through = voids[0]
+    for v in voids[1:]:
+        see_through = see_through.intersection(v)
+    found: list[SeeThrough] = []
+    for comp in (see_through.geoms if hasattr(see_through, "geoms") else [see_through]):
+        if comp.is_empty or comp.area < SEE_THROUGH_MIN_AREA:
+            continue
+        if any(g.symmetric_difference(comp).area <= SEE_THROUGH_SAME_AREA
+               for v in voids for g in (v.geoms if hasattr(v, "geoms") else [v])):
+            continue
+        c = comp.centroid
+        found.append(SeeThrough(area=round(comp.area, 2), centroid=(round(c.x, 1), round(c.y, 1))))
+    return found
+
+
+def selftest_see_through() -> list[str]:
+    """[] when non_prismatic_see_through() flags a synthetic lid whose groove crosses the counterbore and
+    passes one whose groove does not, else the problems. Print pose: 3 mm slab on z = 0, through-hole
+    d 3.4, counterbore d 8 x 1.5 from the bed, groove 2.1 wide x 2 deep from the top."""
+
+    import trimesh
+
+    def lid(groove_y: float):
+        slab = trimesh.creation.box(extents=(40.0, 30.0, 3.0))
+        slab.apply_translation((0.0, 0.0, 1.5))
+        hole = trimesh.creation.cylinder(radius=1.7, height=6.0, sections=64)
+        hole.apply_translation((0.0, 0.0, 1.5))
+        cbore = trimesh.creation.cylinder(radius=4.0, height=2.5, sections=64)
+        cbore.apply_translation((0.0, 0.0, 0.25))
+        groove = trimesh.creation.box(extents=(50.0, 2.1, 3.0))
+        groove.apply_translation((0.0, groove_y, 2.5))
+        return trimesh.boolean.difference([slab, hole, cbore, groove], engine="manifold")
+
+    problems = []
+    broken = non_prismatic_see_through(lid(2.8))
+    if len(broken) != 1:
+        problems.append(f"groove crossing the counterbore: expected 1 opening, found {len(broken)}")
+    fine = non_prismatic_see_through(lid(6.0))
+    if fine:
+        problems.append(f"groove clear of the counterbore: expected none, found {len(fine)}")
+    return problems
diff --git a/scripts/build.py b/scripts/build.py
--- a/scripts/build.py
+++ b/scripts/build.py
@@ -131,11 +131,16 @@
     extents: tuple[float, float, float] = (0.0, 0.0, 0.0)
     bbox_ok: bool = False
     printability: "printability.PrintabilityReport | None" = None
+    see_through: "list[printability.SeeThrough] | None" = None   # case lids only
     error: str | None = None
 
     @property
     def printable_ok(self) -> bool:
         return self.printability is None or self.printability.ok
+
+    @property
+    def see_through_ok(self) -> bool:
+        return not self.see_through
 
     @property
     def ok(self) -> bool:
@@ -147,6 +152,7 @@
             and self.parts_ok
             and self.bbox_ok
             and self.printable_ok
+            and self.see_through_ok
         )
 
 
@@ -519,6 +525,12 @@
             check.printability = printability.analyse(mesh)
         except Exception as exc:  # noqa: BLE001
             check.error = f"printability analysis failed: {exc}"
+
+    if path.name == "lid.stl" and check.watertight:
+        try:
+            check.see_through = printability.non_prismatic_see_through(mesh)
+        except Exception as exc:  # noqa: BLE001
+            check.error = f"see-through analysis failed: {exc}"
 
     return check
 
@@ -812,7 +824,8 @@
             errors.append("check: " + (c.error or
                 f"watertight={c.watertight} winding={c.winding_consistent} parts={c.n_parts} "
                 f"bbox_ok={c.bbox_ok} islands={len(c.printability.islands) if c.printability else '?'} "
-                f"cantilevers={len(c.printability.cantilevers) if c.printability else '?'}"))
+                f"cantilevers={len(c.printability.cantilevers) if c.printability else '?'} "
+                f"see_through={len(c.see_through) if c.see_through is not None else '-'}"))
         errors += [f"golden: {m}" for m in golden_check_part(target, part)]
         if not args.no_slice:
             ok, warnings = slicer_check_project(bambu, target.export_dir / f"{part}.3mf", stats)
@@ -1140,6 +1153,10 @@
             err = "" if ok else "\n".join(ln for ln in lines if "ERROR:" in ln) or "openscad failed"
             results.append((str(test_file.relative_to(REPO_ROOT)), ok, err))
 
+    _require_trimesh()
+    problems = printability.selftest_see_through()
+    results.append(("scripts/printability.py selftest_see_through()", not problems, "; ".join(problems)))
+
     print("\nsmoke results:")
     width = max(len(name) for name, _, _ in results)
     for name, ok, err in results:
@@ -1189,7 +1206,12 @@
         )
         if c.printability is not None:
             detail += f" floating_islands={len(c.printability.islands)} cantilevers={len(c.printability.cantilevers)}"
+        if c.see_through is not None:
+            detail += f" accidental_openings={len(c.see_through)}"
         print(f"  [{status}] {name.ljust(width)}  {detail}")
+        for st in (c.see_through or []):
+            print(f"           ACCIDENTAL OPENING area={st.area}mm2 at xy={st.centroid} (print-pose frame): "
+                  f"you can see through the lid where two features overlap")
         if c.printability is not None:
             for isl in c.printability.islands:
                 print(f"           FLOATING island z={isl.z}mm area={isl.area}mm2 at xy={isl.centroid} "
```

## Appendix B: how the numbers were produced (scratch tools, not part of the repo)

`scratchpad\lid-holes\tools\`: `step0_layout.py` (positions and the groove arithmetic), `step1_analyze.py`
(see-through areas from the model and print STL), `step3_step.py`, `step3b_step_faces.py`,
`step3c_step_after.py` (STEP faces and grid classification), `step2_render.py`, `step4_hero.py`,
`step5_before_after.py`, `step6_after_montage.py` (images), `analyze_mesh.py` (any lid STL plus CSG), `see_through_check.py`
(prototype of the Tier-3 check), `apply_fix.py` (applies the whole fix to a tree, asserting every old
block occurs once), `make_patch.py`, `render_proto.ps1`, `render_all_lids.ps1`, `negative_controls.ps1`,
`fit_check.py` (interference and clearance), `golden_deltas.py`, `verify_proto2.ps1` (the whole gate on
the patched scratch tree). The patched trees are `proto` and `proto2`, the pristine one `pristine`.
Their `lib\BOSL2` junction to the repo's submodule was removed after use (so that no recursive delete can
reach the real submodule); to render there again, recreate it with `New-Item -ItemType Junction -Path
<tree>\lib\BOSL2 -Target <repo>\lib\BOSL2`.

## 13. Open questions for the user (none blocks the fix; the default is what this plan does)

1. **Q24: which thumbscrew?** Head diameter and height, and how it is made captive. The Ø8 x 1.5 mm
   counterbore is `assumed`. A standard DIN 653 M3 knurled thumb screw has a Ø12 x 2.5 mm head, which fits
   no counterbore at a 10 mm inset (T1-91 will say so). If the real head is larger than Ø8.09 the closure
   needs a decision: no counterbore (heads proud), fasteners moved inboard on all four walls, or a smaller
   head. Default: keep Ø8 x 1.5 and proceed.
2. **Confirm the rule change**: on the patch wall only, the tongue-and-groove frame moves 3.5 mm outward
   (rev-5 ruling 4 said "flush with the inner face"). No printed case exists, so nothing has to be
   reprinted. Default: yes.
3. **Captive by design?** Should the lid get a real retention feature for the screws (separate ticket)? The
   flat underside around every hole after this fix leaves room for it. Default: not in this change.
4. **Lid-only mesh check as a hard CI failure**: OK? Default: yes; it is 0.1 s per lid and has no false
   positives on the 8 lids, the through-holes or the vent slots.

---

## Architect verdict (2026-09-29)

# Architect verdict: Plan G, lid thumbscrew-hole openings (D52) and non-captive thumbscrews (D53)

Gate: `solution-architect`, 2026-09-29. This is the mandatory pre-implementation gate.
- Plan: `scratchpad/plans/G-lid-screw-hole-openings.md`.
- Patch: `G-lid-screw-hole-openings.patch`.
- Evidence: `scratchpad/lid-holes/`.

Checked against:
- `.claude/knowledge/architecture.md` rev 18 and `layout-patch-wall.md` rev 18.
- `CLAUDE.md`.
- `main` @ 24c52c8 (read-only): `shell.scad`, `fasteners.scad`, `constants.scad`, `layout.scad`, `vents.scad`, `scripts/build.py`, `scripts/printability.py`, `render.yml`, `requirements.txt`, the goldens, the tests, and the skills.
- The user decisions of 2026-09-29, as relayed by the teamlead.
- The plan-H draft `scratchpad/plans/H-top-lock-and-floor-fixes.md` (rev 1, still being written).

**Revision and ids:** rev 19.
- Used: D52, D53, T1-91, T1-92, R48, M23 and Q24 (recorded as answered).
- Reserved for plan H: rev 20, D54 … D58, T1-93 … T1-100, R49 … R51, M24 … M25, Q25 … Q27 (see GB14).

## Verdict: **APPROVED WITH BINDING CHANGES** (GB1 to GB14)

The research is excellent. I re-derived the numbers and they hold:
- The crescent: 11.38 mm².
- The webs: 1.245 mm on the patch side, 2.745 mm elsewhere.
- The golden deltas: base 7 × 1.6 × 2.0 = +22.40 mm³; lid −29.4 − 3 × 5.7 = −46.5 mm³.
- The tongue position over the bezel recess. Its roof rises outward (`shell.scad:162-163`), so at t = 2.9 there are still 2.88 mm of wall under the tongue.

### What I validated

1. **Option T is the right resolution.**
   - Option A moves bosses into a cable bay whose plug lengths are `assumed`.
   - Option B breaks the frame's continuity at 3 places.
   - Option T keeps the frame continuous and keeps both halves built from one rectangle.
   - It leaves every fastener, boss, insert and the other three walls alone.
   - It also removes a latent coincidence: the old patch tongue's inner edge (t = 8.0) touched the M3 insert bore's edge (t = 8.0) exactly.
   - 4.5 is the value that best satisfies both constraints:
     - the tongue should stand on the full-height wall behind the recess floor (inset ≥ 4.6);
     - T1-91 needs inset ≤ 4.545;
     - so the feasible band is empty by 0.055 mm, and 4.5 leaves only 0.1 mm of tongue over the chamfered roof.
2. **This is a rule change, and it is mine to make.**
   - It amends an architect ruling: `layout-patch-wall.md` §15 ruling 4, "flush with the wall's inner face".
   - That ruling's own reason (a centred tongue does not fit a 3 mm wall) never applied to the 8 mm patch wall.
   - It is not a `CLAUDE.md` fixed decision: "tongue-and-groove lid" still holds.
   - Recorded as D52, with ruling 4 and the constants table amended.
   - **No user decision is needed; plan §13 Q2 is closed.** The teamlead should still tell the user.
3. **Base/lid mating.**
   - Both halves come from `_mcc_tg_rect()`, so they cannot drift.
   - The researcher measured zero interference and exactly `MCC_CLR_TG` all round.
   - Z is unchanged: tongue top = groove ceiling = 50.
   - No new ingress path: the recess breaks through the wall top only at t ≤ 0.5, and the lid still bears on t ∈ [0.5, 2.65].
   - **A base and a lid printed on either side of this change do not mate.** Under CONTRIBUTING.md:35 that is MAJOR (GB13).
4. **Both families.**
   - The webs are identical: the fastener ring and the patch-side frame are both measured from the outer faces.
   - The envelope, bbox and fastener positions do not move on any SKU.
   - T1-37(a) (lid vents) becomes 3.5 mm more conservative and needs no change.
5. **The new Tier-3 check is right-sized, deterministic and correctly scoped.**
   - Deterministic: slice heights come from the mesh's own vertex-Z set, rounded to 0.01 mm, and never lie on a face. It uses pure shapely set operations and no randomness.
   - Cheap: about 0.1 s per lid.
   - General: it catches any overlapping-cut pair in the lid, not only this one.
   - Fails closed: an exception sets `MeshCheck.error`.
   - Scope: lids only is correct. A base costs about 320 s, and bases, coupons and brackets have no thin slab of stacked cuts.
   - Placement: `check_mesh()` covers `check`, `check --all`, `all` and every `ci` part pipeline behind the required `render` check.
   - The self-test belongs in `smoke`. The CI smoke job installs `requirements.txt`, which already has trimesh, shapely, rtree and manifold3d.
   - **Plan §13 Q4 is answered: yes, a hard failure.** It complements T1-91 rather than replacing it.
6. **Goldens.**
   - Exactly the 17 top-level case goldens change: 8 × `<slug>.base.json`, 8 × `<slug>.lid.json`, and `pro-convert-for-ndi-to-hdmi.base_fan.json`.
   - No file under `tests/golden/coupons/` or `tests/golden/brackets/` changes.
   - The plan's targeted `golden --update <8 slugs>` writes exactly those 17 files.
   - GB1 to GB9 do not change geometry, so the plan's deltas stand: base +22.40 mm³ and +28.0 mm²; lid −46.48 mm³ and +120.5 mm²; bbox unchanged.
7. **Ids.**
   - D51 is the last D row (D11 is listed after it out of order).
   - §9 of both documents says the next free id is T1-91.
   - The last R is R47 (R46 was reserved and stays unused), the last M is M22, the last Q is Q23.
   - The researcher's ids are confirmed, plus **D53**: the non-captive decision is a separate rule change from the D52 defect.
   - **Q24 is recorded as answered, not open.** The user answered it before it was filed, and the committed plan copy cites "Q24", so the id must not be reused.

### What the plan missed (why the binding changes exist)

- **F1.** `cb_r = MCC_LID_CB_D / 2 / cos(180 / 64)` puts `fasteners.scad`'s tessellation into L2 as a bare `64`.
  - §3 treats a bare literal in L2 as a deviation, and the fact has no single owner (the D6/D14/D23/D25 pattern).
  - Fix: a public pure function beside the module (GB1, GB2).
- **F2.** T1-92 guards a constant that also moves the **base's** tongue, but it runs only in `mcc_shell_lid()`.
  - Fix: move it into `_mcc_tg_rect()`, where both halves consume the constant (GB3).
- **F3.** A public module named and documented "captive" when the screw is not captive (user decision 2).
  - Rename the module. No alias (the §6 "removed, not deprecated" precedent) (GB1).
- **F4.** The two `_mcc_tg_frame()` calls the patch rewrites pass 5 positional arguments, which violates §3's named-argument rule.
  - The parameter `cav` now carries a rectangle that is *not* the cavity on the patch side. That conflation is how D52 happened (GB4).
- **F5.** `BOM.md:38`'s "assumed M3×10" cannot clamp the lid.
  - The head seats 1.5 mm above the lid underside, and the base's blind insert bore is 6.7 mm deep (`mcc_heat_set_bore()`: insert length 5.7 + 1).
  - So at most 8.2 mm fits under the head. M3×10 bottoms out 1.8 mm before clamping.
  - Fixed in the BOM row and recorded under D53 (GB10).
- **F6.** The plan-H draft already uses **D52** and **T1-91** (`H-top-lock-and-floor-fixes.md` lines 84, 189, 198, 201, 215, 227, 258). That collides with G (GB14).
- **F7.** The lid-check scope lives as a bare `"lid.stl"` literal inside `check_mesh()`. Name it so it can be found and extended (GB7).
- **F8.** Several comments still say "captive thumbscrew" or "flush with the inner face" (GB5, GB6). `requirements.txt` says manifold3d serves only `slicer_probe.py` (GB8).

## Binding changes

Apply these **after** `git apply` of the patch, on the feature branch. Each old block below occurs exactly once. If it does not, stop and report.

**GB1: `lib/mcc/fasteners.scad`. Rename the module, rewrite its doc, add the rim-radius function.**

- Line 3.
  - Old:
    ```
    //   L1. Heat-set insert bosses/bores, captive thumbscrew holes, the captive side bolt (D-09,
    ```
  - New:
    ```
    //   L1. Heat-set insert bosses/bores, lid thumbscrew holes, the captive side bolt (D-09,
    ```
- Line 16.
  - Old:
    ```
    // panel/lid feature (mcc_captive_thumbscrew_hole) spans Z=[0, lid_t] with the outward face at
    ```
  - New:
    ```
    // panel/lid feature (mcc_thumbscrew_hole) spans Z=[0, lid_t] with the outward face at
    ```
- Replace the whole block, from the line `// Module: mcc_captive_thumbscrew_hole()` through that module's closing `}`, with:

```openscad
// Function: mcc_thumbscrew_hole_rim_r()
// Usage:
//   r = mcc_thumbscrew_hole_rim_r([head_d=]);
// Description:
//   Pure. The radius of the counterbore mcc_thumbscrew_hole() cuts, as cut: `head_d` is drawn
//   circum=true at $fn = 64, so the polygon's vertices lie at head_d / 2 / cos(180 / 64). The one
//   source for any clearance check against that counterbore (T1-91 in shell.scad's
//   mcc_shell_lid()). If the counterbore's $fn or circum below changes, change this in the same edit.
// Arguments:
//   head_d = counterbore diameter, mm. Default: MCC_LID_CB_D.
function mcc_thumbscrew_hole_rim_r(head_d = MCC_LID_CB_D) = head_d / 2 / cos(180 / 64);

// Module: mcc_thumbscrew_hole()
// Usage:
//   mcc_thumbscrew_hole([d=], [head_d=], lid_t);
// Description:
//   Negative: a full-depth shaft clearance hole plus an outward-face counterbore that seats the head
//   of a small knurled M3 thumbscrew (Ø7-8 mm, user decision 2026-09-29) recessed in the lid. The
//   screw is NOT captive (architecture.md §13 D53): nothing here retains it once it is out of the
//   base's heat-set insert — the counterbore only seats the head.
//   knowledge/components/fasteners-and-hardware.md:115 "M3 knurled thumb screw ... tool-less panel
//   access"; counterbore depth is assumed at half the lid thickness (no sourced figure for this
//   specific geometry) — smallest reasonable choice, confidence assumed.
//   TODO(teamlead): confirm the counterbore diameter and depth against the purchased thumbscrew's
//   head (architecture.md §12 M23, §11 R48) before the first full-size print.
// Arguments:
//   d      = shaft clearance diameter, mm. Default: MCC_M3_CLR_D.
//   head_d = counterbore (head seat) diameter, mm. Default: MCC_LID_CB_D (constants.scad; assumed,
//            no sourced figure in knowledge/components/fasteners-and-hardware.md). Its radius as
//            cut is mcc_thumbscrew_hole_rim_r(head_d).
//   lid_t  = lid thickness at this location, mm (required).
module mcc_thumbscrew_hole(d = MCC_M3_CLR_D, head_d = MCC_LID_CB_D, lid_t) {
    assert(head_d > d, str("mcc: head_d=", head_d, " must exceed shaft clearance d=", d));
    counterbore_depth = lid_t / 2; // assumed — see TODO above.
    assert(counterbore_depth < lid_t,
        str("mcc: counterbore_depth=", counterbore_depth, " must be less than lid_t=", lid_t));

    union() {
        translate([0, 0, -MCC_EPS])
            cyl(h = lid_t + 2 * MCC_EPS, d = d, circum = true, anchor = BOTTOM, $fn = 64);
        // $fn = 64 and circum = true must match mcc_thumbscrew_hole_rim_r() above.
        translate([0, 0, lid_t - counterbore_depth])
            cyl(h = counterbore_depth + MCC_EPS, d = head_d, circum = true, anchor = BOTTOM, $fn = 64);
    }
}
```

**GB2: `lib/mcc/shell.scad`, `mcc_shell_lid()`. T1-91 reads the rim from GB1, and T1-92 leaves this module.**

- Replace everything the patch inserted after the second T1-33 assert, from `assert(MCC_TG_PATCH_INSET >=` through the closing `}` of the `for (p = lid_pos)` loop, with:

```openscad
    // T1-91: web = counterbore rim to the groove ring's inner edge (gi = [x0, y0, x1, y1]). T1-92
    // fires inside _mcc_tg_rect().
    tg = _mcc_tg_rect(L, W);
    gi = [tg[0] + MCC_CLR_TG, tg[1] + MCC_CLR_TG, tg[0] + tg[2] - MCC_CLR_TG, tg[1] + tg[3] - MCC_CLR_TG];
    cb_r = mcc_thumbscrew_hole_rim_r(head_d = MCC_LID_CB_D);
    for (p = lid_pos) {
        web = min([p[0] - gi[0], gi[2] - p[0], p[1] - gi[1], gi[3] - p[1]]) - cb_r;
        assert(p[0] > gi[0] && p[0] < gi[2] && p[1] > gi[1] && p[1] < gi[3],
            str("mcc: T1-91 lid fastener ", p, " is not inside the groove ring on \"", mcc_dev_slug(dev), "\""));
        assert(web >= MCC_LID_CB_WEB_MIN - MCC_EPS,
            str("mcc: T1-91 lid fastener ", p, " counterbore rim is ", web, " mm from the groove, below MCC_LID_CB_WEB_MIN=",
                MCC_LID_CB_WEB_MIN, " on \"", mcc_dev_slug(dev), "\""));
    }
```

- Thumbscrew call.
  - Old:
    ```
                    mcc_captive_thumbscrew_hole(lid_t = MCC_LID_T + 2 * MCC_EPS);
    ```
  - New:
    ```
                    mcc_thumbscrew_hole(head_d = MCC_LID_CB_D, lid_t = MCC_LID_T + 2 * MCC_EPS);
    ```

**GB3: `lib/mcc/shell.scad`. T1-92 lives in `_mcc_tg_rect()`.**

Replace the patched block, from `// Function: _mcc_tg_rect()` through `... W - MCC_WALL - MCC_TG_PATCH_INSET];`, with:

```openscad
// Function: _mcc_tg_rect()
// Description:
//   Private. [x0, y0, w, h] of the rectangle the tongue-and-groove frame is offset from (see
//   _mcc_tg_frame()), shared by the base's tongue and the lid's groove so the two can never disagree.
//   On the -Y and +-X sides it is the interior-cavity boundary (tongue flush with the wall's inner
//   face, layout-patch-wall.md §15 ruling 4); on the +Y patch side its edge sits MCC_TG_PATCH_INSET
//   from the wall's outer face, clear of the lid's thumbscrew counterbores (D52, T1-91). T1-92 guards
//   the constant here, where both halves consume it.
function _mcc_tg_rect(L, W) =
    assert(MCC_TG_PATCH_INSET >= MCC_WALL - MCC_EPS && MCC_TG_PATCH_INSET <= MCC_T_PATCH + MCC_EPS,
        str("mcc: T1-92 MCC_TG_PATCH_INSET=", MCC_TG_PATCH_INSET, " outside [MCC_WALL=", MCC_WALL,
            ", MCC_T_PATCH=", MCC_T_PATCH, "]"))
    [-L / 2 + MCC_WALL, -W / 2 + MCC_WALL, L - 2 * MCC_WALL, W - MCC_WALL - MCC_TG_PATCH_INSET];
```

**GB4: `lib/mcc/shell.scad`, `_mcc_tg_frame()`. Rename `cav` to `rect`; use named arguments at both call sites.**

- Replace the block from `// Module: _mcc_tg_frame()` through the body line `x0 = cav[0]; ...` with:

```openscad
// Module: _mcc_tg_frame()
// Description:
//   Private. A rectangular picture-frame ring, radially offset from the edge of `rect`
//   (_mcc_tg_rect()) by [r_lo, r_hi] (positive = grow OUTWARD, toward the wall's own outer face;
//   negative = shrink INWARD, toward the interior) — the shared shape both the base's tongue (D-07,
//   r=[0,MCC_TG_W]) and the lid's matching groove (r=[-MCC_CLR_TG, MCC_TG_W+MCC_CLR_TG]) are built
//   from, so the two can never drift out of the "groove width = tongue width + 2*clearance"
//   relationship (tg-ladder.scad's own convention).
// Arguments:
//   rect       = [x0,y0,w,h] frame reference rect (_mcc_tg_rect()) -- NOT the interior cavity on
//                the +Y patch wall (D52).
//   r_lo, r_hi = radial offsets from `rect`'s edge, mm.
//   z0, height = Z placement.
module _mcc_tg_frame(rect, r_lo, r_hi, z0, height) {
    x0 = rect[0]; y0 = rect[1]; w = rect[2]; h = rect[3];
```

- Base tongue call.
  - Old:
    ```
                    _mcc_tg_frame(_mcc_tg_rect(L, W), 0, MCC_TG_W, z_top - MCC_EPS, MCC_TG_H + MCC_EPS);
    ```
  - New:
    ```
                    _mcc_tg_frame(rect = _mcc_tg_rect(L, W), r_lo = 0, r_hi = MCC_TG_W,
                                  z0 = z_top - MCC_EPS, height = MCC_TG_H + MCC_EPS);
    ```
- Lid groove call.
  - Old:
    ```
            _mcc_tg_frame(_mcc_tg_rect(L, W), -MCC_CLR_TG, MCC_TG_W + MCC_CLR_TG, z_top - MCC_EPS, MCC_TG_H + MCC_EPS);
    ```
  - New:
    ```
            _mcc_tg_frame(rect = _mcc_tg_rect(L, W), r_lo = -MCC_CLR_TG, r_hi = MCC_TG_W + MCC_CLR_TG,
                          z0 = z_top - MCC_EPS, height = MCC_TG_H + MCC_EPS);
    ```

**GB5: `lib/mcc/shell.scad` module docs.**

- `mcc_shell_base()` description.
  - Old:
    ```
    //   The base half: floor + 4 walls (open top) + the raised tongue along the inner top perimeter
    //   (D-07), the patch-wall connector recess + connector cuts (D36), the side-bolt boss/cut (far wall), the 6
    ```
  - New:
    ```
    //   The base half: floor + 4 walls (open top) + the raised tongue along the top perimeter (D-07;
    //   flush with the inner face of the 3 mm walls, MCC_TG_PATCH_INSET from the patch wall's outer
    //   face — D52), the patch-wall connector recess + connector cuts (D36), the side-bolt boss/cut (far wall), the 6
    ```
- `mcc_shell_lid()` description.
  - Old:
    ```
    //   it — rev-5 ruling 4 / T1-33), and 6 captive-thumbscrew holes at the same `lid_fastener_pos`
    //   the base's bosses use. No cradle, no floor features, no side-bolt feature (all base-only).
    ```
  - New:
    ```
    //   it — rev-5 ruling 4 / T1-33; offset outward on the patch wall, D52), and 6 thumbscrew holes
    //   (mcc_thumbscrew_hole(), non-captive — D53) at the same `lid_fastener_pos` the base's bosses
    //   use, each counterbore >= MCC_LID_CB_WEB_MIN clear of the groove (T1-91). No cradle, no floor
    //   features, no side-bolt feature (all base-only).
    ```

**GB6: `lib/mcc/constants.scad` comments.**

- Line 367: replace `6 (not 4) captive thumbscrews are used,` with `6 (not 4) lid thumbscrews are used,`.
- Line 379: replace `as every other captive thumbscrew` with `as every other lid thumbscrew`.
- The tongue-and-groove ruling block.
  - Old:
    ```
    // flush with the wall's INNER face, sized so it fits inside the lid with >= 1.0 mm of lid material
    // left above the groove.
    ```
  - New:
    ```
    // flush with the wall's INNER face, sized so it fits inside the lid with >= 1.0 mm of lid material
    // left above the groove. Rev 19 (D52): on the 8 mm +Y patch wall the frame sits MCC_TG_PATCH_INSET
    // from the OUTER face instead, so the lid groove clears the thumbscrew counterbores (T1-91) -- the
    // ruling's reason (a centred tongue does not fit a 3 mm wall) binds only the 3 mm walls.
    ```
- Replace the patch's `MCC_TG_PATCH_INSET` and `MCC_LID_CB_D` definitions, including their comment lines, with the block below. `MCC_LID_CB_WEB_MIN` stays exactly as the patch wrote it.

```openscad
MCC_TG_PATCH_INSET = 4.5; // +Y patch wall only (D52): distance from the wall's outer face to the
                           // tongue's inner edge, mm (tongue at [inset - MCC_TG_W, inset], groove
                           // +-MCC_CLR_TG); the other three walls keep the tongue flush with their inner
                           // face. Largest 0.5 mm step that keeps MCC_LID_CB_WEB_MIN at the fastener
                           // ring: MCC_FASTENER_INSET 10 - counterbore rim 4.005 - MCC_CLR_TG 0.25 - 1.2
                           // = 4.545; it also keeps the tongue (all but its outer 0.1 mm) on the
                           // full-height wall behind the bezel-recess floor. T1-91, T1-92. Any change
                           // is an architect re-gate (architecture.md R48), not a tweak.
MCC_LID_CB_D = 8.0; // lid thumbscrew counterbore diameter, mm. assumed -- no sourced figure (was the
                     // literal `head_d = 8` in fasteners.scad). User decision 2026-09-29: keep 8 for
                     // a small knurled head, 7-8 mm (architecture.md D53); measure the bought screw
                     // (M23). Modelled circum=true, $fn=64 (mcc_thumbscrew_hole_rim_r()). T1-91 caps
                     // it at ~8.09 while MCC_TG_PATCH_INSET = 4.5 (R48).
```

**GB7: `scripts/build.py`. Name the see-through scope.**

- Directly after `MODEL_FRAME_SUFFIX = ".model.stl"` add:

```python
# Print-pose files that get the accidental see-through check (architecture.md §8 rev 19, D52): every
# case lid. Name-based on purpose -- `check <path>` knows only the file. A new lid-like part (e.g. an
# extra_parts lid variant) must be added here in the same change.
SEE_THROUGH_FILE_NAMES = ("lid.stl",)
```

- In `check_mesh()`, replace `if path.name == "lid.stl" and check.watertight:` with `if path.name in SEE_THROUGH_FILE_NAMES and check.watertight:`.

**GB8: `requirements.txt` line 11.**
- Replace the comment `# scripts/slicer_probe.py: trimesh slice_plane(cap=True) booleans`
- with `# scripts/slicer_probe.py (slice_plane(cap=True) booleans) + printability.selftest_see_through() (build.py smoke)`.

**GB9: Tests.**

- `tests/test_fasteners.scad`, line 17: replace `captive thumbscrew hole` with `lid thumbscrew hole`.
- `tests/test_fasteners.scad`, line 20.
  - Old:
    ```
    translate([40, 0, 0]) mcc_captive_thumbscrew_hole(lid_t = 3.0);
    ```
  - New:
    ```
    translate([40, 0, 0]) mcc_thumbscrew_hole(lid_t = 3.0);
    assert(mcc_thumbscrew_hole_rim_r() > MCC_LID_CB_D / 2,
        "mcc test_fasteners: mcc_thumbscrew_hole_rim_r() must return the circumscribed (as-cut) radius");
    ```
- `tests/test_shell.scad`, the manual-check footer.
  - Old:
    ```
    //   mcc_vents(dev = DEV, cfg = VARIANT, face = [0, 1, 0]);
    // -----------------------------------------------------------------------------------------
    ```
  - New:
    ```
    //   mcc_vents(dev = DEV, cfg = VARIANT, face = [0, 1, 0]);
    //
    // Manual check (T1-91/T1-92, D52), OPENSCADPATH=lib: force the old patch-wall frame and confirm FAIL:
    //   openscad --backend=Manifold -D 'part="lid"' -D MCC_TG_PATCH_INSET=8 -o neg.csg models/pro-convert-hdmi-plus/case.scad
    //   -> ERROR "T1-91 lid fastener [95.25, 73.175] counterbore rim is -2.25482 mm from the groove ..."
    //   -D MCC_TG_PATCH_INSET=2 instead (part "lid" or "base") -> ERROR "T1-92 MCC_TG_PATCH_INSET=2 outside [...]"
    // -----------------------------------------------------------------------------------------
    ```

**GB10: `BOM.md` line 38.** Replace the whole thumbscrew row (the line starting `| M3 knurled thumb screw | generic`) with:

```
| M3 knurled thumb screw — **non-captive, small head** | generic (McMaster-Carr "Knurled Head Thumb Screws" family); **head Ø7–8 mm** (user decision 2026-09-29: it sits recessed in the lid's Ø8 × 1.5 mm counterbore, `MCC_LID_CB_D`; a DIN 653 Ø12 head does **not** fit); **≤ 8 mm under the head — M3×6 recommended** (derived: 1.5 mm of lid under the counterbore floor + the 6.7 mm blind insert bore, `mcc_heat_set_bore()` = insert 5.7 + 1, = 8.2 mm; the earlier "assumed M3×10" would bottom out before clamping the lid). Head ⌀/height `assumed` until the bought screw is measured (architecture.md §12 M23) | 6 | Not captive (architecture.md D53): nothing retains a screw once it is out of its insert. Every current SKU is over the `MCC_LID_SPAN_MAX = 180 mm` threshold post-D-12 (compact 193.9–194.9 mm, plus 210.5–211.5 mm) — both families get 6, not 4 | `.claude/knowledge/layout-patch-wall.md` §6 ("Family outcome after D-12 ... every current SKU gets 6 thumbscrews"); `knowledge/components/fasteners-and-hardware.md:115` (product family, exact stocked length not scrapeable); `lib/mcc/fasteners.scad` `mcc_thumbscrew_hole()`, `mcc_heat_set_bore()` |
```

**GB11: Skills and test docs.** Apply the verbatim texts in Appendix D:
- `print-check`, `bom-update` and `new-case-variant` skills;
- `.claude/knowledge/testing.md`;
- `tests/README.md`;
- `scripts/README.md`.

Skills must describe the library that exists (D13).

**GB12: Records.**
- Apply Appendix A (`architecture.md`), Appendix B (`layout-patch-wall.md`), Appendix C (`CLAUDE.md`) and the CHANGELOG entry in Appendix D, verbatim.
- Copy the plan to `docs/plans/2026-09-29-lid-screw-hole-openings.md` unchanged.
- Append `\n---\n\n## Architect verdict (2026-09-29)\n\n` followed by the full text of this file (repo precedent: verdicts live in the committed plan).
- Do not commit the images. Attach them to the PR.
- **Replaces the plan's §9 items 1–7 and §10's CHANGELOG text.**

**GB13: Commits and PR.**
- The geometry commit is MAJOR (CONTRIBUTING.md:35 and :129):
  - header: `fix(shell)!: move the patch-wall tongue-and-groove clear of the lid counterbores (D52)`;
  - footer: `BREAKING CHANGE: a base and a lid printed on either side of this change do not mate (the +Y tongue/groove moved 3.5 mm outward).`
- The docs go in a `docs:` commit. Stage explicit paths only.
- The PR description must include:
  - the plan's §0 table;
  - the golden table (plan §8);
  - the gate results (the Implementation order below);
  - the images `before_after_pro-convert-hdmi-plus.png` and `hero_pro-convert-hdmi-plus.png`;
  - a line stating that **the `CLAUDE.md` fixed decision "captive" is changed on the user's decision of 2026-09-29, as relayed by the teamlead**, so the user sees the new wording when reviewing.

**GB14: Ids and sequencing with plan H (binding on H).**
- **G goes first.** G is verified, smaller, and fixes a defect in a part the specialist is reviewing now. H is still in research, has open user choices (its §19), and needs its own gate, including its proposed change to `printability._cantilevers()`.
- **H branches from `main` after G merges.** If H's developer must start earlier, H is stacked on G's branch head. H's PR is not opened until G is merged; H then rebases onto `main`, re-runs its full gate and regenerates goldens with its own targeted `golden --update`. Golden JSON and the §9 "next free id" lines are never hand-merged. H re-baselines its expected volumes on post-G `main` (every base is +22.40 mm³).
- **H renumbers its draft.** Its "D52" becomes **D54**; its "T1-91" (the −X end wall) becomes **T1-93**. H's ids come only from: **rev 20, D54 … D58, T1-93 … T1-100, R49 … R51, M24 … M25, Q25 … Q27**. Unused reserved ids stay unused and are never reassigned (the rev-17 precedent). A third concurrent plan starts at D59, T1-101, R52, M26, Q28, rev 21.
- **Expected conflicts when H rebases, resolved textually:**
  - `scripts/printability.py`: G appends functions and constants; H edits `_cantilevers()`.
  - `constants.scad`: different sections.
  - `architecture.md` and `layout-patch-wall.md`: rev headers, §9 "next free" lines, and the §11/§12/§13 tails.
  - `CLAUDE.md`: G edits the Closure bullet's first lines; H edits the gravity-lock sentences of the same bullet.
  - `BOM.md`: the thumbscrew row versus the tie-down rows.
  - `CHANGELOG.md`.
- G's lid-only see-through check does **not** cover H's −X groove slit, which is a base feature. H's gate must give that slit its own assert.

## DO-NOTs

1. Do not move `MCC_FASTENER_INSET`, `lid_fastener_pos`, the bosses, gussets or insert bores. Do not edit `layout.scad` or `vents.scad`.
2. Do not change `MCC_TG_W`, `MCC_TG_H`, `MCC_CLR_TG`, `MCC_LID_T`, `MCC_T_PATCH`, the counterbore depth (`lid_t / 2`), or `_mcc_tg_frame()`'s geometry.
3. Do not change `MCC_LID_CB_D` (8.0, user decision) or `MCC_TG_PATCH_INSET` (4.5). Do not add `MCC_HOLE_COMP` to the counterbore. If T1-91 or T1-92 fires, stop and report.
4. Do not add any retention feature to the lid holes: no groove, clip pocket, O-ring seat or printed thread. The screws are non-captive by user decision.
5. Do not keep an alias `mcc_captive_thumbscrew_hole()`. Do not touch `mcc_captive_side_bolt_*`: the side bolt **is** captive.
6. Do not extend the see-through check to bases, coupons or brackets. Do not loosen any `SEE_THROUGH_*` constant to make a part pass.
7. Do not hand-edit golden JSON. No golden outside the 17 may change. Any other delta, or any bbox change, means stop and find out why.
8. Do not edit `knowledge/**`: it lists knurled and captive screws as sourced options, not as the design.
9. Do not edit history:
   - `architecture.md` rev headers up to rev 18;
   - existing §13 rows, other than the insertions below;
   - `docs/plans/**`, other than the new copy;
   - earlier CHANGELOG sections.
10. Do not touch anything in plan H's scope: the rail, the floor, the splitter tie-down slot the prototype flagged, or `printability._cantilevers()`.
11. Do not `git add -A`. The untracked `MCC_FAN_BAY_CLR`, `MCC_FLOOR_T` and `sysmon.csv` in the repo root are not yours; leave them. Never commit on `main`. Never merge while any check is pending or failing. Do not rename CI jobs.

## Implementation order

1. Run `git fetch origin`. Confirm `main` == `origin/main`.
   - Branch `feature/lid-screw-hole-openings`, or `feature/issue-<n>-lid-screw-hole-openings` if the teamlead opens an issue.
   - `build.py doctor` must be green.
2. On the clean branch, save the negative-control lids exactly as in plan §7.1.
3. Apply the patch:
   - `git apply --check "C:\Users\Niels\AppData\Local\Temp\claude\C--repos-github-magewell-converter-cases\21ce76a1-d282-4f53-b50d-05d7eb636fdb\scratchpad\plans\G-lid-screw-hole-openings.patch"`, then `git apply` the same file.
   - `git diff --stat` must show 6 files, +153/−20. If it does not, apply the hunks by hand from plan §5.2.
4. Apply GB1 to GB9 in order.
5. Run the grep checks. Each must return no hits:
   - `mcc_captive_thumbscrew_hole` in `lib models tests scripts .claude/skills`;
   - `_mcc_cavity_rect` and `cos(180 / 64)` in `lib/mcc/shell.scad`;
   - `captive thumbscrew` and `captive-thumbscrew` in `lib tests scripts .claude/skills CLAUDE.md BOM.md`.
6. Run the gates from plan §7.2, steps 1 to 11:
   - Step 1, `smoke`: 12/12.
   - Step 2: both old lids FAIL with `accidental_openings=3`.
   - Steps 3 to 5: the exact T1-91 and T1-92 errors. **Add step 5b:** `-D 'part="base"' -D MCC_TG_PATCH_INSET=2` must also fail with T1-92, which proves GB3.
   - Step 6: no error.
   - Steps 7 to 11: all green, with `accidental_openings=0` on every lid, 0 slicer warnings, and a Plus-lid STEP of 258 faces.
7. Refresh the goldens with the plan §8 command. `git diff --stat tests/golden` must show exactly the 17 files. Check every delta against the plan §8 table.
8. Apply GB10 to GB12: the BOM, skills, test docs, Appendices A to D, and the plan copy with this verdict appended.
9. Commit as in GB13. Push, open the PR, and wait for the `render` check to be green. Then merge.
10. Tell the teamlead G is merged, so H can branch or rebase under GB14.

For the teamlead, not the developer:
- add M23 to `.claude/knowledge/session-resume.md`'s physical plan;
- correct any memory note that says "captive thumbscrews".

---

## Appendix A: `.claude/knowledge/architecture.md` (verbatim)

**A1. Revision 19 header.** Insert before the line that begins `**Revision 18, 2026-09-28 (vertical VESA-column bracket`, followed by one blank line:

```
**Revision 19, 2026-09-29 (lid thumbscrew holes — D52, D53; plan G,
`docs/plans/2026-09-29-lid-screw-hole-openings.md`).** The external CAD specialist found see-through
crescents in 3 of the 6 lid thumbscrew counterbores on every SKU: on the 8 mm patch wall the lid's groove
ran through the ⌀8 counterbores of the fasteners at `MCC_FASTENER_INSET` = 10 (D52, latent since the
first lid). Fix: on the +Y wall only, the tongue-and-groove frame moves outward to `MCC_TG_PATCH_INSET` =
4.5 mm from the outer face (`layout-patch-wall.md` §15 ruling 4 amended); fasteners, bosses, inserts and
the other three walls do not move. Guards: **T1-91** (counterbore web to the groove ≥ 1.2 mm), **T1-92**
(the inset stays on the patch wall) and a Tier-3 check that fails a case lid with any accidental
see-through opening, with a `smoke` self-test (§8, §9). User decisions the same day: the thumbscrews keep
a **small Ø7–8 mm knurled head recessed in the ⌀8 counterbore** (not DIN 653) and are **not captive**
(D53; Q24 answered; `mcc_captive_thumbscrew_hole()` → `mcc_thumbscrew_hole()`). New: **T1-91, T1-92,
R48, M23, Q24, D52, D53**. Reserved for plan H (rev 20): **T1-93 … T1-100, D54 … D58, R49 … R51,
M24 … M25, Q25 … Q27**. No envelope figure moves; base +22.40 mm³, lid −46.48 mm³ on every SKU.
```

**A2. §3, the L1 list.** Old:
```
    lib/mcc/fasteners.scad                heat-set bosses, captive thumbscrew, 1/4"-20 boss
```
New:
```
    lib/mcc/fasteners.scad                heat-set bosses, lid thumbscrew hole (non-captive, D53), 1/4"-20 boss
```

**A3. §5 table, row "Lid".** Old:
```
| Lid | the D32 patch-wall lip is gone (nothing to frame); the tongue/groove runs unbroken | `shell.scad` `mcc_shell_lid()` |
```
New:
```
| Lid | the D32 patch-wall lip is gone (nothing to frame); the tongue/groove runs unbroken — on this wall 4.5 mm (`MCC_TG_PATCH_INSET`) from the outer face instead of flush with the inner face (tongue 2.9–4.5, groove 2.65–4.75 mm), so the groove clears the lid's thumbscrew counterbores (rev 19, D52, T1-91) | `shell.scad` `_mcc_tg_rect()`, `mcc_shell_lid()` |
```

**A4. §8, a new bullet.** Insert after the bullet that ends `together. >45° overhang areas are reported with `check --verbose`, not failed.`:
```
- **A case lid may not have an accidental see-through opening (rev 19, D52).** `check_mesh()` runs
  `printability.non_prismatic_see_through()` on every print-pose file named in `build.py`'s
  `SEE_THROUGH_FILE_NAMES` (`lid.stl` — every case lid) in `check`, `check --all` and each `ci` part
  pipeline: the lid is sliced at the middle of every Z interval between consecutive vertex heights, and
  each connected region that is open along Z at every height must equal one connected void of at least
  one slice. A drawn hole or slot does; an opening made by two overlapping cuts (the D52 counterbore
  crossing the groove) does not, and fails the part. `smoke` runs its self-test. **Scope, on purpose:**
  lids only (≈ 0.1 s each) — a base needs ≈ 540 slices (≈ 320 s), so bases, coupons and brackets stay
  out of the per-part gate; a new lid-like part joins `SEE_THROUGH_FILE_NAMES` in the same change, and a
  lid feature the check cannot represent (a conical countersink) extends the check in the same change.
  It complements T1-91 — the assert names the known pair at render time, the mesh check catches any
  pair — and no golden field replaces it: a golden records what the geometry is, not whether it is right.
```

**A5. §9 Tier 1.** Insert after the line ending `arch's sandwich parts; listed in `layout-patch-wall.md` §9). **The next free id is T1-91.**`:
```
**Rev 19 adds T1-91 and T1-92** (plan G, D52): T1-91 — for every lid fastener, the counterbore's radius
as cut (`mcc_thumbscrew_hole_rim_r()`) stays ≥ `MCC_LID_CB_WEB_MIN` (1.2) inside the groove ring's inner
edge, evaluated in `mcc_shell_lid()`; T1-92 — `MCC_WALL ≤ MCC_TG_PATCH_INSET ≤ MCC_T_PATCH`, evaluated
inside `_mcc_tg_rect()` so a base render trips it too. **T1-93 … T1-100 are reserved for plan H
(rev 20); the next free id after them is T1-101.**
```

**A6. §9 Tier 2.** Old: `asserts fire) without tessellating, so it is fast. Non-zero exit = failure.` New:
```
asserts fire) without tessellating, so it is fast. Non-zero exit = failure. Since rev 19 `smoke` also
runs the Python self-test of the lid see-through check (`printability.selftest_see_through()`: two
synthetic lids, one broken, one not) — a Tier-3 checker that silently stops finding anything is worse
than none.
```

**A7. §9 Tier 3.** Old: `trimesh; it is unreliable. Rely on the Tier-1 assert plus the slicer.` New:
```
trimesh; it is unreliable. Rely on the Tier-1 assert plus the slicer. **Rev 19:** `check` also fails a
case lid with an accidental see-through opening (§8, D52) — a topology test on a thin slab, not a
wall-thickness measurement, so the rule above stands.
```

**A8. §11 R7.** Old: `Baseline stays the user's 4 captive M3 thumbscrews; **6 for any lid over 180 mm span** (D-04).` New:
```
Baseline stays the user's 4 M3 thumbscrews (non-captive since D53, 2026-09-29); **6 for any lid over 180 mm span** (D-04).
```

**A9. §11 R48.** Insert after R47's last line (`… M20 measures `W_LIFT_RAIL`.`), preceded by one blank line:
```
**R48 — the lid counterbore has almost no headroom, and the thumbscrew is not yet in hand. NEW
2026-09-29 (rev 19, D52/D53).** The user fixed the hardware class: a small knurled M3 head, Ø7–8 mm,
seated in the lid's ⌀8 × 1.5 mm counterbore (`MCC_LID_CB_D`, depth `lid_t/2`, both `assumed`) — not
DIN 653's Ø12 — and non-captive. What is left:
- **Diameter.** With `e = 10` and `MCC_TG_PATCH_INSET` = 4.5, T1-91 fires above a ⌀8.09 counterbore (web
  1.245 against 1.2). A head that measures Ø8.0 will not drop into a printed ⌀8.0 counterbore (FDM holes
  print undersize — the reason `MCC_HOLE_COMP` exists), so a Ø8 head forces a larger counterbore, which
  forces a smaller inset: a base + lid change that pushes the tongue out over the bezel recess's
  chamfered roof (at 4.0 its outer edge rides on ≈ 2.3 mm of roof). **That is an architect re-gate, not a
  constant tweak.** A Ø7 head needs nothing.
- **Height.** A head taller than 1.5 mm stands proud of the lid by the difference. Deepening the
  counterbore thins the 1.5 mm of lid the head clamps on. Decide with M23 in hand.
- **Length.** The clamp stack allows ≤ 8.2 mm under the head: 1.5 mm of lid below the counterbore floor
  plus the 6.7 mm blind insert bore (`mcc_heat_set_bore()`: insert 5.7 + 1). M3×6 puts 4.5 mm into the
  5.7 mm insert; M3×8 leaves 0.2 mm nominal; the former BOM figure, M3×10, bottomed out before clamping
  (D53).
- **Loss.** A non-captive screw can be dropped when a lid is opened on stage — accepted by the user.
```

**A10. §12 Q24.** Insert after Q23's last line (`(D48) goes back to the user.`):
```
24. **Which lid thumbscrew, and is it captive? NEW and answered 2026-09-29 (rev 19, user).** A small
    knurled M3 head, **Ø7–8 mm, recessed in the ⌀8 counterbore as modelled** — not DIN 653 (Ø12, which
    fits no counterbore at `e = 10`); **not captive** (D53). The residue — the real head's ⌀ and height,
    and the screw length — is R48/M23.
```

**A11. §12, the measurement table and the numbering note.**

Insert after the `| **M22** |` row:
```
| **M23** | **Buy the chosen lid thumbscrew (small knurled M3 head, Ø7–8 mm) and measure: head ⌀ across the knurl, head height, under-head length; try it in a printed ⌀8 × 1.5 counterbore (a test print of one lid corner is enough)** | **R48 — gates the first full-size lid print.** A tight fit, or a head over ≈ 7.8 mm, means the counterbore must grow — T1-91 fires above ⌀8.09, so that is an architect re-gate, not a constant tweak. A head over 1.5 mm stands proud by the difference. Length ≤ 8.2 mm under the head (M3×6 recommended) | User, after buying |
```

Insert after the line `> **Rev 18** adds M22 (plan D).`:
```
> **Rev 19** adds M23 (plan G).
```

**A12. §13, two rows.** Insert both directly after the row that begins `| **D51** |`:
```
| **D52** | 2026-09-29 | §5 lid row / `layout-patch-wall.md` §15 ruling 4 (the tongue flush with the wall's inner face; groove = tongue ± `MCC_CLR_TG`) with §6 (the fastener ring at `e` = 10 from the outer faces). The lid is one 3 mm slab: two cuts in it must never meet | `lib/mcc/shell.scad:400` (groove) with `lib/mcc/fasteners.scad:87-98` (counterbore) and `lib/mcc/constants.scad:373` (`MCC_FASTENER_INSET`): on the 8 mm patch wall the groove (6.15–8.25 mm from the outer face, 2.0 mm deep) runs through the ⌀8 counterbore (rim 5.995 mm, floor 1.5 mm below the outer face) of the three patch-side lid fasteners; the cuts overlap 0.5 mm in Z, so 11.38 mm² (27.6 %) of each counterbore floor is open on all 8 SKUs (24 holes), and the through-hole stands 0.05 mm from the groove | Found by the external CAD specialist in the exact `lid.step`. Latent since `b6a8b77` (2026-09-08): `check`, the slicer gate, the goldens (0.018 % of the volume — the first lid golden already contained it) and T1-33 all passed it. Ruling 4's own reason — a centred tongue does not fit a 3 mm wall — never applied to the 8 mm wall | **Fixed in rev 19 (plan G, option T).** On the +Y wall only, the frame is offset outward: `MCC_TG_PATCH_INSET` = 4.5 (tongue 2.9–4.5, groove 2.65–4.75 mm from the outer face; counterbore web 1.245 mm) through `_mcc_tg_rect()`, which replaces `_mcc_cavity_rect()`; fasteners, bosses, inserts and the other three walls do not move. New `MCC_LID_CB_D` (8.0, `assumed`, was a literal), `MCC_LID_CB_WEB_MIN` (1.2), `mcc_thumbscrew_hole_rim_r()`; **T1-91**, **T1-92**; the Tier-3 lid see-through check with its `smoke` self-test (§8). Rejected: moving the three fasteners inboard (an unverifiable cable-bay change), interrupting the frame at each hole (the fallback), dropping the counterbore, a thicker lid (H = 51 is fixed). Base +22.40 mm³, lid −46.48 mm³, bbox unchanged on every SKU; a base and a lid from either side of the change do not mate (MAJOR). Ruling 4 amended in `layout-patch-wall.md` §15 |
| **D53** | 2026-09-29 | `CLAUDE.md` fixed decision "6 captive M3 knurled thumbscrews" (Closure) and `mcc_captive_thumbscrew_hole()`'s doc ("stays captive when backed out") | The model never retained the screw: `lib/mcc/fasteners.scad:70-98` cuts a ⌀3.4 clearance hole and a ⌀8 × 1.5 counterbore — no groove, clip, O-ring or thread holds an M3 once it is out of the base's insert. And `BOM.md:38`'s "assumed M3×10" bottoms out: under a 1.5 mm counterbore floor the 6.7 mm blind insert bore allows 8.2 mm under the head | A fixed decision the geometry did not implement; a public module named for a property it lacks; a BOM length that cannot clamp the lid | **Resolved by user decision 2026-09-29 — the rule changes, no geometry changes.** The thumbscrews are **non-captive**, with a **small knurled head, Ø7–8 mm, recessed in the ⌀8 counterbore** (not DIN 653, Ø12). `CLAUDE.md` Closure reworded; `mcc_captive_thumbscrew_hole()` renamed `mcc_thumbscrew_hole()` (no alias) and its doc rewritten; BOM row: small head, ≤ 8 mm under the head (M3×6), non-captive. `knowledge/**` unchanged — it lists knurled and captive screws as sourced options, not as the design. Q24 answered; residue R48/M23 |
```

## Appendix B: `.claude/knowledge/layout-patch-wall.md` (verbatim)

**B1. Status header.** Insert before the first `Status: **revision 18, 2026-09-28**` line, followed by one blank line:
```
Status: **revision 19, 2026-09-29** (aligned with `architecture.md` rev 19 — D52/D53, plan G: the lid
thumbscrew holes). §6 gains the counterbore web rule and the non-captive screw; **§9** gains **T1-91**
and **T1-92** (T1-93 … T1-100 reserved for plan H); §10 D-04 drops "captive"; §11 gains a rev-19
addendum; §15 ruling 4 is amended for the +Y wall. No envelope figure moves.
```

**B2. §6, lid fasteners.** Old:
```
Captive M3 knurled thumbscrews into M3 heat-set inserts (`MCC_INSERT_M3`, `constants.scad:96`);
boss OD ≥ 1.8 × insert OD = 8.28 mm (`constants.scad:102`), ≥ 2 mm material to any edge
(`fdm-rugged-enclosure-guidelines.md:127`).
```
New:
```
Non-captive M3 knurled thumbscrews with a small head (Ø7–8 mm, seated in the lid's ⌀8 × 1.5 mm
counterbore, `MCC_LID_CB_D`; user decision 2026-09-29, `architecture.md` D53) into M3 heat-set inserts
(`MCC_INSERT_M3`, `constants.scad:96`); boss OD ≥ 1.8 × insert OD = 8.28 mm (`constants.scad:102`),
≥ 2 mm material to any edge (`fdm-rugged-enclosure-guidelines.md:127`).

**Counterbore web rule (rev 19, D52).** The lid is one 3 mm slab, so its cuts must never meet: every
counterbore keeps ≥ `MCC_LID_CB_WEB_MIN` (1.2 mm) of lid, in plan, to the groove ring's inner edge
(**T1-91**). At `e = 10` that holds by 2.745 mm on the 3 mm walls; on the 8 mm patch wall it holds only
because the tongue-and-groove frame is offset outward there (`MCC_TG_PATCH_INSET` = 4.5, web 1.245 mm —
§15 ruling 4 as amended). The counterbore can therefore grow to ⌀8.09 at most before T1-91 fires
(`architecture.md` R48).
```

**B3. §9, two rows.** Insert after the row that begins `| **T1-86 … T1-90** |`:
```
| **T1-91** | *the lid's counterbores clear the groove* — for every `lid_fastener_pos` p: p lies inside the groove ring's inner edge `gi` (`_mcc_tg_rect()` shrunk by `MCC_CLR_TG`), and `min(p.x − gi.x0, gi.x1 − p.x, p.y − gi.y0, gi.y1 − p.y) − mcc_thumbscrew_hole_rim_r(MCC_LID_CB_D) ≥ MCC_LID_CB_WEB_MIN` (1.2) | **new rev 19** (D52, plan G). Patch-side fasteners `5.25 − 4.005 = 1.245` ✓; the other walls `6.75 − 4.005 = 2.745` ✓. Evaluated in `mcc_shell_lid()`. The old geometry (`MCC_TG_PATCH_INSET` = 8) gives −2.25 and fails |
| **T1-92** | *the patch-side frame stays on the patch wall* — `MCC_WALL ≤ MCC_TG_PATCH_INSET ≤ MCC_T_PATCH` | **new rev 19** (D52). Evaluated in `_mcc_tg_rect()`, so a base render trips it too. T1-93 … T1-100 are reserved for plan H (rev 20); **the next free id is T1-101** |
```

**B4. §10, D-04.** Old:
```
| D-04 | 4 captive M3 thumbscrews baseline; **6 for lids over 180 mm span**. | Architect-derived, user-reviewed | **ACCEPTED 2026-09-08** |
```
New:
```
| D-04 | 4 M3 thumbscrews baseline; **6 for lids over 180 mm span**. The screws are **non-captive** (user decision 2026-09-29, `architecture.md` D53). | Architect-derived, user-reviewed | **ACCEPTED 2026-09-08** |
```

**B5. §11, the rev-5 addendum row.** Old:
```
| `MCC_TG_W` / `MCC_TG_H` | **1.6 / 2.0**, offset (shiplap) tongue flush with the wall's **inner** face |
```
New (the rest of the row is unchanged):
```
| `MCC_TG_W` / `MCC_TG_H` | **1.6 / 2.0**, offset (shiplap) tongue flush with the wall's **inner** face — **except on the +Y patch wall, where its inner edge sits `MCC_TG_PATCH_INSET` (4.5) from the outer face (rev 19, D52)** |
```

**B6. §11, a new addendum.** Insert after the paragraph that ends `§15 ruling 2026-09-08b.` (the "Explicitly NOT added: `MCC_APERTURE_TOP_OPEN`" paragraph) and before the `---` preceding §15:
```
### Rev-19 addendum (2026-09-29) — the lid thumbscrew holes (D52)

| Constant | Value | Purpose / where used |
|---|---|---|
| **`MCC_TG_PATCH_INSET`** | **NEW — 4.5** | +Y patch wall only: outer face → tongue inner edge (tongue at `[inset − MCC_TG_W, inset]`, groove `± MCC_CLR_TG`). The largest 0.5 mm step that keeps T1-91's web (`10 − 4.005 − 0.25 − 1.2 = 4.545`); it also keeps the tongue (all but its outer 0.1 mm) on the full-height wall behind the bezel-recess floor. `_mcc_tg_rect()`, T1-91, T1-92. A change is an architect re-gate (R48) |
| **`MCC_LID_CB_D`** | **NEW — 8.0 `assumed`** | Lid thumbscrew counterbore diameter (was the literal `head_d = 8` in `fasteners.scad`). User decision 2026-09-29: keep ⌀8 for a small Ø7–8 mm knurled head (D53). `mcc_thumbscrew_hole()`, `mcc_thumbscrew_hole_rim_r()`, T1-91; measured by M23 |
| **`MCC_LID_CB_WEB_MIN`** | **NEW — 1.2** | Minimum lid material between a counterbore and the groove, in plan: three perimeters (`fdm-rugged-enclosure-guidelines.md:35`), the same rule as T1-61. T1-91 |
```

**B7. §15 ruling 4.** In the row that begins `| 4 | `MCC_TG_W/H = 3.0/4.0` |`, old end of row: `and must be re-cut to 1.6/2.0 |`. New end of row:
```
and must be re-cut to 1.6/2.0. **Amended rev 19 (2026-09-29, D52):** "flush with the wall's inner face" holds on the three 3 mm walls only. On the 8 mm +Y patch wall the frame is offset outward — tongue inner edge `MCC_TG_PATCH_INSET` = 4.5 mm from the outer face — because flush with that wall's inner face the lid groove ran through the ⌀8 thumbscrew counterbores at `e = 10` (T1-91). This ruling's reason (a centred tongue does not fit a 3 mm wall) never applied to the 8 mm wall |
```

## Appendix C: `CLAUDE.md` (verbatim)

**C1. Closure, the captive wording.**

Old:
```
6 captive M3 knurled thumbscrews into M3 heat-set inserts
  (rule: 6 above 180 mm lid span; both families are above it).
```
New:
```
6 **non-captive** M3 knurled thumbscrews into M3 heat-set
  inserts — a **small head, Ø7–8 mm, recessed in a Ø8 counterbore** in the lid, not DIN 653's Ø12
  (user decision 2026-09-29, D53); rule: 6 above 180 mm lid span, both families are above it. On the
  patch wall the tongue-and-groove sits 4.5 mm from the outer face so the lid groove clears those
  counterbores (architecture.md D52).
```

The text that follows, ` **Retention: captive 1/4"-20`, stays untouched: the side bolt **is** captive.

**C2. Standard commands, two lines.**

- Smoke.
  - Old:
    ```
    python scripts/build.py smoke         # tests/*.scad -> .csg, asserts fire, non-zero exit = fail
    ```
  - New:
    ```
    python scripts/build.py smoke         # tests/*.scad -> .csg, asserts fire; + the lid see-through check's self-test; non-zero exit = fail
    ```
- Check.
  - Old:
    ```
    python scripts/build.py check         # mesh checks (watertight, winding, single shell) + no floating islands
    ```
  - New:
    ```
    python scripts/build.py check         # mesh checks (watertight, winding, single shell) + no floating islands + no see-through opening in a case lid
    ```

**C3. Current status, the evolutions list.**

Old:
```
the vertical VESA-column bracket and the arch's sandwich parts (D51) — are in architecture.md §13.
```
New:
```
the vertical VESA-column bracket and the arch's sandwich parts (D51), and the patch-wall
tongue-and-groove moved clear of the lid's thumbscrew counterbores (D52) — are in architecture.md §13.
```

**C4. Current status, the next milestone.**

Old:
```
dongle splitter and the E-clip, write the measured values
```
New:
```
dongle splitter, the E-clip and the lid thumbscrews (M23), write the measured values
```

## Appendix D: Other documents (verbatim)

**D1. `.claude/skills/print-check/SKILL.md`**

- §1.
  - Old: `plus Bambu's 3 mm "floating cantilever" rule. The`
  - New: `plus Bambu's 3 mm "floating cantilever" rule, and on case lids any accidental see-through opening — two cuts meeting in the 3 mm slab (architecture.md §8 rev 19, D52). The`
- §5, the long-lid bullet (4 lines).
  - Old:
    ```
    - On a long lid (>~180 mm), 4 captive thumbscrews likely aren't enough to stop mid-span bow +
      tongue-and-groove joint opening under ASA warp (architecture §11 R7, currently flagged as needing a
      user decision toward 6 thumbscrews or a mid-span rib). Check whether that decision has been made
      for the specific case before printing a long lid with only 4.
    ```
  - New:
    ```
    - On a long lid (>~180 mm), 4 thumbscrews are not enough to stop mid-span bow + tongue-and-groove
      joint opening under ASA warp — D-04 (accepted 2026-09-08) puts 6 on every lid over 180 mm, which is
      every current SKU (architecture §11 R7). The thumbscrews are non-captive, with a small Ø7–8 mm head
      in the lid's Ø8 counterbore (D53); check the bought screw against M23 before the first lid print.
    ```
- §7 table: insert after the `len(split()) != 1` row:
  ```
  | `accidental_openings > 0` (case lid only) | Two cuts in the 3 mm lid overlap in plan and in Z — e.g. a counterbore reaching the groove (architecture.md D52) — so the lid is open where nobody drew a hole | Whatever you last moved in the lid (counterbore, groove, vent field); T1-91 and T1-37 should have fired first — if neither did, the new feature needs its own web assert |
  ```

**D2. `.claude/skills/bom-update/SKILL.md`**

- Line 29.
  - Old: `| M3 knurled thumbscrew | <n> (4, or 6 on lids >~180 mm per architecture §11 R7) | captive lid fastening | knowledge/components/fasteners-and-hardware.md §2 |`
  - New: `| M3 knurled thumbscrew (small Ø7–8 mm head, ≤ 8 mm under the head) | <n> (4, or 6 on lids >~180 mm per architecture §11 R7) | lid fastening — non-captive (architecture D53) | knowledge/components/fasteners-and-hardware.md §2 |`
- Line 101: replace `| captive lid fastening |` with `| lid fastening — non-captive (architecture D53) |`.

**D3. `.claude/skills/new-case-variant/SKILL.md`**

- Old:
  ```
  - [ ] `python scripts/build.py check --all` passes (watertight, single shell, bbox, no floating
        islands/cantilevers).
  ```
- New:
  ```
  - [ ] `python scripts/build.py check --all` passes (watertight, single shell, bbox, no floating
        islands/cantilevers, no accidental see-through opening in the lid).
  ```

**D4. `.claude/knowledge/testing.md`**

- Tier 2.
  - Old: `   `-o *.csg` (evaluates the CSG tree, so Tier-1 asserts fire, without tessellating — fast).`
  - New:
    ```
       `-o *.csg` (evaluates the CSG tree, so Tier-1 asserts fire, without tessellating — fast), plus
       `scripts/printability.py selftest_see_through()` (two synthetic lids: the lid see-through check
       must flag the broken one and pass the other — architecture.md §9 rev 19).
    ```
- Tier 3.
  - Old: `   island (Bambu Studio's "floating regions"), and the **slicer gate** `slicer-check --require``
  - New:
    ```
       island (Bambu Studio's "floating regions"); on every `lid.stl` the **lid see-through check** (no
       accidental opening where two cuts meet — architecture.md §8 rev 19, D52); and the **slicer gate** `slicer-check --require`
    ```
- Green.
  - Old: `  not a failure, just an unwritten test).`
  - New: `  not a failure, just an unwritten test), and `selftest_see_through()` passed.`
- Green.
  - Old: `  floating islands. Goldens are measured`
  - New: `  floating islands; every case lid has zero accidental see-through openings. Goldens are measured`

**D5. `tests/README.md`**

- After the line `any failure; the command prints a pass/fail table naming every test file.`, insert one blank line and:
  ```
  `smoke` also runs `scripts/printability.py selftest_see_through()` — two synthetic lids, one whose
  groove crosses a counterbore and one whose groove does not — so the lid see-through check (Tier 3)
  cannot silently stop finding openings (architecture.md §9 rev 19).
  ```
- After the line `visual/slicer check for wall thickness.`, insert one blank line and:
  ```
  Print-pose STLs also get the printability gate (`scripts/printability.py`: no floating island, no
  > 3 mm cantilever), and every `lid.stl` gets the **lid see-through check** — no region open along Z
  that is not one drawn cut (architecture.md §8 rev 19, D52).
  ```
- Green.
  - Old: `- `smoke`: every `tests/test_*.scad` ran to completion with no `ERROR:` (or there were none yet).`
  - New: `- `smoke`: every `tests/test_*.scad` ran to completion with no `ERROR:` (or there were none yet), and `selftest_see_through()` passed.`
- Green.
  - Old: `  connected shell, and within the 244 mm/axis bbox ceiling.`
  - New: `  connected shell, and within the 244 mm/axis bbox ceiling; print-pose STLs have no floating island or cantilever, and no case lid has an accidental see-through opening.`

**D6. `scripts/README.md`**

- The `smoke` row.
  - Old: `(evaluates the tree, asserts fire, no tessellation). Fast. |`
  - New: `(evaluates the tree, asserts fire, no tessellation), plus `printability.py`'s `selftest_see_through()`. Fast. |`
- The `check --all` row.
  - Old: `on every print-pose `exports/**/*.stl` (the `*.model.stl` twins are skipped).`
  - New: `on every print-pose `exports/**/*.stl` (the `*.model.stl` twins are skipped), **plus the lid see-through check** on every `lid.stl` (`printability.non_prismatic_see_through()`: no accidental opening where two cuts meet — architecture.md §8 rev 19, D52; reported as `ACCIDENTAL OPENING` lines).`

**D7. `CHANGELOG.md`.** Insert directly under `## [Unreleased]`, above `### Added (2026-09-28, issue #56)`, followed by one blank line:
```
### Fixed (2026-09-29, external CAD review of `lid.step`) — MAJOR: a base and a lid printed on either side of this change do not mate

- **Lid thumbscrew holes had openings** (architecture.md D52): on all 8 SKUs the 3 patch-wall-side
  holes (the two (±X, +Y) corners and the patch-wall middle one) had a see-through opening in the Ø8
  counterbore floor, 11.4 mm² each, where the lid's groove crossed the counterbore. The
  tongue-and-groove frame on the +Y patch wall now sits 4.5 mm from the outer face
  (`MCC_TG_PATCH_INSET`) in both the base (tongue) and the lid (groove), clear of the counterbores. The
  other three walls and every fastener, boss and insert position are unchanged. No full case has been
  printed yet.
- New guards: asserts T1-91 (counterbore-to-groove web) and T1-92 (patch inset range); `build.py check`
  and the `ci` part gate fail a case lid with an accidental see-through opening; `build.py smoke` runs a
  self-test of that check.

### Changed (2026-09-29, user decision) — the lid thumbscrews are not captive

- The 6 lid thumbscrews are **non-captive** M3 knurled thumbscrews with a small Ø7–8 mm head recessed in
  the Ø8 counterbore (architecture.md D53); the model never retained them, so no geometry changes.
  `mcc_captive_thumbscrew_hole()` is renamed `mcc_thumbscrew_hole()`. BOM: ≤ 8 mm under the head (M3×6
  recommended) — the earlier "assumed M3×10" would bottom out in the insert bore.
```

---

# Amendment 1 (issue-based IDs), 2026-09-29

**Why.**
- PR #61 (end-stop remnants) merged: `main` is now `4e3a93f`. It took `architecture.md` "Revision 19" and **D52**, both of which this verdict had assigned to G.
- The user's new rule (issue **#68**): records are numbered after their GitHub issue, and `architecture.md` no longer has revision numbers.
- G is issue **#62**.

**What this amendment does.** It **replaces GB1–GB14, the Implementation order and Appendices A–D above, in full.** Apply only the blocks in this amendment.
- Still valid from above: the validation (points 1–7), the findings F1–F8 and the DO-NOTs, all read with the id map below.
- The golden expectations are unchanged: exactly the 17 case goldens; base +22.40 mm³ / +28.0 mm²; lid −46.48 mm³ / +120.5 mm²; bbox unchanged.
- **G's PR closes #62 and #68.**

## Id map

| Was (this verdict, and the plan) | Now |
|---|---|
| D52 (the defect) | **D62.1** |
| D53 (non-captive, user decision) | **D62.2** |
| T1-91 (counterbore web) | **T1-62.1** |
| T1-92 (patch inset range) | **T1-62.2** |
| R48 | **R62.1** |
| M23 | **M62.1** |
| Q24 | **Q62.1** (answered) |
| "rev 19" (G) / "rev 20" (H) | dropped: no revision numbers from #68 on |
| H reservations (T1-93 … T1-100, D54 … D58, R49 … R51, M24 … M25, Q25 … Q27) | **withdrawn**: H numbers after its issues #63–#66 |

**Never search-and-replace these ids in the repository.** `D52` and "Revision 19" now exist on `main` as #61's records (`architecture.md` top paragraph and §13; `constants.scad:637`; `CHANGELOG.md:19`). Every corrected text is given in full below.

**One reading rule for the new scheme.** A new-scheme id always carries its `.x`:
- `T1-62` is the rail-clearance assert of rev 16; `T1-62.1` is issue #62's first assert.
- The bare ids T1-63 … T1-66 (the rail asserts) are unrelated to issues #63 … #66.
- To find an issue's asserts, search with the dot: `T1-62\.`

## Re-verification against `main` 4e3a93f

- **Code.** #61 touched `constants.scad` only at the end-stop tombstone (around line 637). `shell.scad`, `fasteners.scad`, `tests/test_shell.scad`, `tests/test_fasteners.scad`, `scripts/build.py`, `scripts/printability.py` and `requirements.txt` are unchanged.
  - Every code anchor below was re-read on 4e3a93f.
  - The patch's `constants.scad` hunk (line 508) is unchanged, so `git apply --check` is expected to be clean.
  - `smoke` still has 11 `.scad` tests, plus G's self-test, making 12.
- **`architecture.md`.** Every anchor text is still present exactly once; #61's new top paragraph shifts it by +11 lines. Current lines:
  - §3 L1 list: 424
  - §5 Lid row: 620
  - §8 printability bullet: 1163
  - §9 rev-18 line: 1260
  - Tier 2: 1267
  - Tier 3: 1274
  - §11 heading: 1319
  - R7: 1387
  - R47 end: 1899
  - §12 heading: 1903
  - Q23 end: 1997
  - M22 row: 2024
  - numbering note: 2034
  - §13 intro: 2040–2041
  - D11 row (last row): 2096
  - The top paragraph is now #61's "Revision 19".
- **Other docs.** `layout-patch-wall.md`, `CLAUDE.md`, `BOM.md`, the skills, `testing.md`, `tests/README.md` and `scripts/README.md` are unchanged. `CHANGELOG.md`: #61 added `### Removed (2026-09-29, end-stop remnants)` directly under `## [Unreleased]`, so the G entry goes above it (D7′).
- **Correction to the old GB14 (sequencing).** Once a branch is pushed or has a PR it is **not rebased**. `main` is merged into it (CONTRIBUTING.md:100–102, `git-flow` skill).

## Binding changes (complete; supersede GB1–GB14)

Apply these after `git apply` of the patch, on `feature/issue-62-lid-screw-hole-openings`. Each old text occurs exactly once. If it does not, stop and report.

**GB1′: `lib/mcc/fasteners.scad`. Rename the module, rewrite its doc, add the rim-radius function.**

- Line 3.
  - Old:
    ```
    //   L1. Heat-set insert bosses/bores, captive thumbscrew holes, the captive side bolt (D-09,
    ```
  - New:
    ```
    //   L1. Heat-set insert bosses/bores, lid thumbscrew holes, the captive side bolt (D-09,
    ```
- Line 16.
  - Old:
    ```
    // panel/lid feature (mcc_captive_thumbscrew_hole) spans Z=[0, lid_t] with the outward face at
    ```
  - New:
    ```
    // panel/lid feature (mcc_thumbscrew_hole) spans Z=[0, lid_t] with the outward face at
    ```
- Replace the whole block, from `// Module: mcc_captive_thumbscrew_hole()` through that module's closing `}`, with:

```openscad
// Function: mcc_thumbscrew_hole_rim_r()
// Usage:
//   r = mcc_thumbscrew_hole_rim_r([head_d=]);
// Description:
//   Pure. The radius of the counterbore mcc_thumbscrew_hole() cuts, as cut: `head_d` is drawn
//   circum=true at $fn = 64, so the polygon's vertices lie at head_d / 2 / cos(180 / 64). The one
//   source for any clearance check against that counterbore (T1-62.1 in shell.scad's
//   mcc_shell_lid()). If the counterbore's $fn or circum below changes, change this in the same edit.
// Arguments:
//   head_d = counterbore diameter, mm. Default: MCC_LID_CB_D.
function mcc_thumbscrew_hole_rim_r(head_d = MCC_LID_CB_D) = head_d / 2 / cos(180 / 64);

// Module: mcc_thumbscrew_hole()
// Usage:
//   mcc_thumbscrew_hole([d=], [head_d=], lid_t);
// Description:
//   Negative: a full-depth shaft clearance hole plus an outward-face counterbore that seats the head
//   of a small knurled M3 thumbscrew (Ø7-8 mm, user decision 2026-09-29) recessed in the lid. The
//   screw is NOT captive (architecture.md §13 D62.2): nothing here retains it once it is out of the
//   base's heat-set insert — the counterbore only seats the head.
//   knowledge/components/fasteners-and-hardware.md:115 "M3 knurled thumb screw ... tool-less panel
//   access"; counterbore depth is assumed at half the lid thickness (no sourced figure for this
//   specific geometry) — smallest reasonable choice, confidence assumed.
//   TODO(teamlead): confirm the counterbore diameter and depth against the purchased thumbscrew's
//   head (architecture.md §12 M62.1, §11 R62.1) before the first full-size print.
// Arguments:
//   d      = shaft clearance diameter, mm. Default: MCC_M3_CLR_D.
//   head_d = counterbore (head seat) diameter, mm. Default: MCC_LID_CB_D (constants.scad; assumed,
//            no sourced figure in knowledge/components/fasteners-and-hardware.md). Its radius as
//            cut is mcc_thumbscrew_hole_rim_r(head_d).
//   lid_t  = lid thickness at this location, mm (required).
module mcc_thumbscrew_hole(d = MCC_M3_CLR_D, head_d = MCC_LID_CB_D, lid_t) {
    assert(head_d > d, str("mcc: head_d=", head_d, " must exceed shaft clearance d=", d));
    counterbore_depth = lid_t / 2; // assumed — see TODO above.
    assert(counterbore_depth < lid_t,
        str("mcc: counterbore_depth=", counterbore_depth, " must be less than lid_t=", lid_t));

    union() {
        translate([0, 0, -MCC_EPS])
            cyl(h = lid_t + 2 * MCC_EPS, d = d, circum = true, anchor = BOTTOM, $fn = 64);
        // $fn = 64 and circum = true must match mcc_thumbscrew_hole_rim_r() above.
        translate([0, 0, lid_t - counterbore_depth])
            cyl(h = counterbore_depth + MCC_EPS, d = head_d, circum = true, anchor = BOTTOM, $fn = 64);
    }
}
```

**GB2′: `lib/mcc/shell.scad`, `mcc_shell_lid()`.**

- Replace everything the patch inserted after the second T1-33 assert, from `assert(MCC_TG_PATCH_INSET >=` through the closing `}` of the `for (p = lid_pos)` loop, with:

```openscad
    // T1-62.1: web = counterbore rim to the groove ring's inner edge (gi = [x0, y0, x1, y1]).
    // T1-62.2 fires inside _mcc_tg_rect().
    tg = _mcc_tg_rect(L, W);
    gi = [tg[0] + MCC_CLR_TG, tg[1] + MCC_CLR_TG, tg[0] + tg[2] - MCC_CLR_TG, tg[1] + tg[3] - MCC_CLR_TG];
    cb_r = mcc_thumbscrew_hole_rim_r(head_d = MCC_LID_CB_D);
    for (p = lid_pos) {
        web = min([p[0] - gi[0], gi[2] - p[0], p[1] - gi[1], gi[3] - p[1]]) - cb_r;
        assert(p[0] > gi[0] && p[0] < gi[2] && p[1] > gi[1] && p[1] < gi[3],
            str("mcc: T1-62.1 lid fastener ", p, " is not inside the groove ring on \"", mcc_dev_slug(dev), "\""));
        assert(web >= MCC_LID_CB_WEB_MIN - MCC_EPS,
            str("mcc: T1-62.1 lid fastener ", p, " counterbore rim is ", web, " mm from the groove, below MCC_LID_CB_WEB_MIN=",
                MCC_LID_CB_WEB_MIN, " on \"", mcc_dev_slug(dev), "\""));
    }
```

- Thumbscrew call.
  - Old:
    ```
                    mcc_captive_thumbscrew_hole(lid_t = MCC_LID_T + 2 * MCC_EPS);
    ```
  - New:
    ```
                    mcc_thumbscrew_hole(head_d = MCC_LID_CB_D, lid_t = MCC_LID_T + 2 * MCC_EPS);
    ```

**GB3′: `lib/mcc/shell.scad`. T1-62.2 lives in `_mcc_tg_rect()`.**

Replace the patched block, from `// Function: _mcc_tg_rect()` through `... W - MCC_WALL - MCC_TG_PATCH_INSET];`, with:

```openscad
// Function: _mcc_tg_rect()
// Description:
//   Private. [x0, y0, w, h] of the rectangle the tongue-and-groove frame is offset from (see
//   _mcc_tg_frame()), shared by the base's tongue and the lid's groove so the two can never disagree.
//   On the -Y and +-X sides it is the interior-cavity boundary (tongue flush with the wall's inner
//   face, layout-patch-wall.md §15 ruling 4); on the +Y patch side its edge sits MCC_TG_PATCH_INSET
//   from the wall's outer face, clear of the lid's thumbscrew counterbores (D62.1, T1-62.1). T1-62.2
//   guards the constant here, where both halves consume it.
function _mcc_tg_rect(L, W) =
    assert(MCC_TG_PATCH_INSET >= MCC_WALL - MCC_EPS && MCC_TG_PATCH_INSET <= MCC_T_PATCH + MCC_EPS,
        str("mcc: T1-62.2 MCC_TG_PATCH_INSET=", MCC_TG_PATCH_INSET, " outside [MCC_WALL=", MCC_WALL,
            ", MCC_T_PATCH=", MCC_T_PATCH, "]"))
    [-L / 2 + MCC_WALL, -W / 2 + MCC_WALL, L - 2 * MCC_WALL, W - MCC_WALL - MCC_TG_PATCH_INSET];
```

**GB4′: `lib/mcc/shell.scad`, `_mcc_tg_frame()`. Rename `cav` to `rect`; use named arguments at both call sites.**

- Replace the block from `// Module: _mcc_tg_frame()` through the body line `x0 = cav[0]; ...` with:

```openscad
// Module: _mcc_tg_frame()
// Description:
//   Private. A rectangular picture-frame ring, radially offset from the edge of `rect`
//   (_mcc_tg_rect()) by [r_lo, r_hi] (positive = grow OUTWARD, toward the wall's own outer face;
//   negative = shrink INWARD, toward the interior) — the shared shape both the base's tongue (D-07,
//   r=[0,MCC_TG_W]) and the lid's matching groove (r=[-MCC_CLR_TG, MCC_TG_W+MCC_CLR_TG]) are built
//   from, so the two can never drift out of the "groove width = tongue width + 2*clearance"
//   relationship (tg-ladder.scad's own convention).
// Arguments:
//   rect       = [x0,y0,w,h] frame reference rect (_mcc_tg_rect()) -- NOT the interior cavity on
//                the +Y patch wall (D62.1).
//   r_lo, r_hi = radial offsets from `rect`'s edge, mm.
//   z0, height = Z placement.
module _mcc_tg_frame(rect, r_lo, r_hi, z0, height) {
    x0 = rect[0]; y0 = rect[1]; w = rect[2]; h = rect[3];
```

- Base tongue call.
  - Old:
    ```
                    _mcc_tg_frame(_mcc_tg_rect(L, W), 0, MCC_TG_W, z_top - MCC_EPS, MCC_TG_H + MCC_EPS);
    ```
  - New:
    ```
                    _mcc_tg_frame(rect = _mcc_tg_rect(L, W), r_lo = 0, r_hi = MCC_TG_W,
                                  z0 = z_top - MCC_EPS, height = MCC_TG_H + MCC_EPS);
    ```
- Lid groove call.
  - Old:
    ```
            _mcc_tg_frame(_mcc_tg_rect(L, W), -MCC_CLR_TG, MCC_TG_W + MCC_CLR_TG, z_top - MCC_EPS, MCC_TG_H + MCC_EPS);
    ```
  - New:
    ```
            _mcc_tg_frame(rect = _mcc_tg_rect(L, W), r_lo = -MCC_CLR_TG, r_hi = MCC_TG_W + MCC_CLR_TG,
                          z0 = z_top - MCC_EPS, height = MCC_TG_H + MCC_EPS);
    ```

**GB5′: `lib/mcc/shell.scad` module docs.**

- `mcc_shell_base()`.
  - Old:
    ```
    //   The base half: floor + 4 walls (open top) + the raised tongue along the inner top perimeter
    //   (D-07), the patch-wall connector recess + connector cuts (D36), the side-bolt boss/cut (far wall), the 6
    ```
  - New:
    ```
    //   The base half: floor + 4 walls (open top) + the raised tongue along the top perimeter (D-07;
    //   flush with the inner face of the 3 mm walls, MCC_TG_PATCH_INSET from the patch wall's outer
    //   face — D62.1), the patch-wall connector recess + connector cuts (D36), the side-bolt boss/cut (far wall), the 6
    ```
- `mcc_shell_lid()`.
  - Old:
    ```
    //   it — rev-5 ruling 4 / T1-33), and 6 captive-thumbscrew holes at the same `lid_fastener_pos`
    //   the base's bosses use. No cradle, no floor features, no side-bolt feature (all base-only).
    ```
  - New:
    ```
    //   it — rev-5 ruling 4 / T1-33; offset outward on the patch wall, D62.1), and 6 thumbscrew holes
    //   (mcc_thumbscrew_hole(), non-captive — D62.2) at the same `lid_fastener_pos` the base's bosses
    //   use, each counterbore >= MCC_LID_CB_WEB_MIN clear of the groove (T1-62.1). No cradle, no floor
    //   features, no side-bolt feature (all base-only).
    ```

**GB6′: `lib/mcc/constants.scad`.**

- Line 367: replace `6 (not 4) captive thumbscrews are used,` with `6 (not 4) lid thumbscrews are used,`.
- Line 379: replace `as every other captive thumbscrew` with `as every other lid thumbscrew`.
- The tongue-and-groove ruling block.
  - Old:
    ```
    // flush with the wall's INNER face, sized so it fits inside the lid with >= 1.0 mm of lid material
    // left above the groove.
    ```
  - New:
    ```
    // flush with the wall's INNER face, sized so it fits inside the lid with >= 1.0 mm of lid material
    // left above the groove. #62 (D62.1): on the 8 mm +Y patch wall the frame sits MCC_TG_PATCH_INSET
    // from the OUTER face instead, so the lid groove clears the thumbscrew counterbores (T1-62.1) -- the
    // ruling's reason (a centred tongue does not fit a 3 mm wall) binds only the 3 mm walls.
    ```
- Replace the patch's `MCC_TG_PATCH_INSET` and `MCC_LID_CB_D` definitions, including their comment lines, with:

```openscad
MCC_TG_PATCH_INSET = 4.5; // +Y patch wall only (D62.1): distance from the wall's outer face to the
                           // tongue's inner edge, mm (tongue at [inset - MCC_TG_W, inset], groove
                           // +-MCC_CLR_TG); the other three walls keep the tongue flush with their inner
                           // face. Largest 0.5 mm step that keeps MCC_LID_CB_WEB_MIN at the fastener
                           // ring: MCC_FASTENER_INSET 10 - counterbore rim 4.005 - MCC_CLR_TG 0.25 - 1.2
                           // = 4.545; it also keeps the tongue (all but its outer 0.1 mm) on the
                           // full-height wall behind the bezel-recess floor. T1-62.1, T1-62.2. Any change
                           // is an architect re-gate (architecture.md R62.1), not a tweak.
MCC_LID_CB_D = 8.0; // lid thumbscrew counterbore diameter, mm. assumed -- no sourced figure (was the
                     // literal `head_d = 8` in fasteners.scad). User decision 2026-09-29: keep 8 for
                     // a small knurled head, 7-8 mm (architecture.md D62.2); measure the bought screw
                     // (M62.1). Modelled circum=true, $fn=64 (mcc_thumbscrew_hole_rim_r()). T1-62.1
                     // caps it at ~8.09 while MCC_TG_PATCH_INSET = 4.5 (R62.1).
```

- In the patch's `MCC_LID_CB_WEB_MIN` comment, replace `fdm-rugged-enclosure-guidelines.md:35. T1-91.` with `fdm-rugged-enclosure-guidelines.md:35. T1-62.1.`

**GB7′: `scripts/build.py`.**

- Directly after `MODEL_FRAME_SUFFIX = ".model.stl"` add:

```python
# Print-pose files that get the accidental see-through check (architecture.md §8, #62, D62.1): every
# case lid. Name-based on purpose -- `check <path>` knows only the file. A new lid-like part (e.g. an
# extra_parts lid variant) must be added here in the same change.
SEE_THROUGH_FILE_NAMES = ("lid.stl",)
```

- In `check_mesh()`, replace `if path.name == "lid.stl" and check.watertight:` with `if path.name in SEE_THROUGH_FILE_NAMES and check.watertight:`.

**GB8′: `requirements.txt` line 11.**
- Replace the comment `# scripts/slicer_probe.py: trimesh slice_plane(cap=True) booleans`
- with `# scripts/slicer_probe.py (slice_plane(cap=True) booleans) + printability.selftest_see_through() (build.py smoke)`.

**GB9′: Tests.**

- `tests/test_fasteners.scad`, line 17: replace `captive thumbscrew hole` with `lid thumbscrew hole`.
- `tests/test_fasteners.scad`, line 20.
  - Old:
    ```
    translate([40, 0, 0]) mcc_captive_thumbscrew_hole(lid_t = 3.0);
    ```
  - New:
    ```
    translate([40, 0, 0]) mcc_thumbscrew_hole(lid_t = 3.0);
    assert(mcc_thumbscrew_hole_rim_r() > MCC_LID_CB_D / 2,
        "mcc test_fasteners: mcc_thumbscrew_hole_rim_r() must return the circumscribed (as-cut) radius");
    ```
- `tests/test_shell.scad`, the line the patch added.
  - Old:
    ```
    // --- shell.scad: plus-family lid (T1-91/T1-92 on both families) ---
    ```
  - New:
    ```
    // --- shell.scad: plus-family lid (T1-62.1/T1-62.2 on both families) ---
    ```
- `tests/test_shell.scad`, the manual-check footer.
  - Old:
    ```
    //   mcc_vents(dev = DEV, cfg = VARIANT, face = [0, 1, 0]);
    // -----------------------------------------------------------------------------------------
    ```
  - New:
    ```
    //   mcc_vents(dev = DEV, cfg = VARIANT, face = [0, 1, 0]);
    //
    // Manual check (T1-62.1/T1-62.2, D62.1), OPENSCADPATH=lib: force the old patch-wall frame and confirm FAIL:
    //   openscad --backend=Manifold -D 'part="lid"' -D MCC_TG_PATCH_INSET=8 -o neg.csg models/pro-convert-hdmi-plus/case.scad
    //   -> ERROR "T1-62.1 lid fastener [95.25, 73.175] counterbore rim is -2.25482 mm from the groove ..."
    //   -D MCC_TG_PATCH_INSET=2 instead (part "lid" or "base") -> ERROR "T1-62.2 MCC_TG_PATCH_INSET=2 outside [...]"
    // -----------------------------------------------------------------------------------------
    ```

**GB10′: `BOM.md` line 38.** Replace the whole thumbscrew row (the line starting `| M3 knurled thumb screw | generic`) with:

```
| M3 knurled thumb screw — **non-captive, small head** | generic (McMaster-Carr "Knurled Head Thumb Screws" family); **head Ø7–8 mm** (user decision 2026-09-29: it sits recessed in the lid's Ø8 × 1.5 mm counterbore, `MCC_LID_CB_D`; a DIN 653 Ø12 head does **not** fit); **≤ 8 mm under the head — M3×6 recommended** (derived: 1.5 mm of lid under the counterbore floor + the 6.7 mm blind insert bore, `mcc_heat_set_bore()` = insert 5.7 + 1, = 8.2 mm; the earlier "assumed M3×10" would bottom out before clamping the lid). Head ⌀/height `assumed` until the bought screw is measured (architecture.md §12 M62.1) | 6 | Not captive (architecture.md D62.2): nothing retains a screw once it is out of its insert. Every current SKU is over the `MCC_LID_SPAN_MAX = 180 mm` threshold post-D-12 (compact 193.9–194.9 mm, plus 210.5–211.5 mm) — both families get 6, not 4 | `.claude/knowledge/layout-patch-wall.md` §6 ("Family outcome after D-12 ... every current SKU gets 6 thumbscrews"); `knowledge/components/fasteners-and-hardware.md:115` (product family, exact stocked length not scrapeable); `lib/mcc/fasteners.scad` `mcc_thumbscrew_hole()`, `mcc_heat_set_bore()` |
```

**GB11′: Skills and test docs.** Apply Appendix D′ (D1′–D6′).

**GB12′: Records.**
- Apply Appendix A′ (`architecture.md`), B′ (`layout-patch-wall.md`), C′ (`CLAUDE.md`), D7′ (`CHANGELOG.md`) and E′ (the #68 rule in `CONTRIBUTING.md`, the `git-flow` skill and `ticket-source.md`).
- Copy the plan to `docs/plans/2026-09-29-lid-screw-hole-openings.md`, with these three lines (and one blank line) inserted **above** its title:

```
> **Ids renumbered at the architect gate (issue #68):** D52→D62.1, D53→D62.2, T1-91→T1-62.1,
> T1-92→T1-62.2, R48→R62.1, M23→M62.1, Q24→Q62.1 (see the verdict at the end). `D52` in the
> repository is #61's end-stop record, not this plan's.
```

- Then append `\n---\n\n## Architect verdict (2026-09-29)\n\n` followed by the full text of this VERDICT file, including this amendment.
- Do not commit the images; attach them to the PR.
- If the plan has not been posted to #62 yet, the teamlead posts plan §12's text there (`ticket-source.md`: a plan goes back to its issue).

**GB13′: Commits and PR.**
- The geometry commit is MAJOR (CONTRIBUTING.md:35, :129):
  - header: `fix(shell)!: move the patch-wall tongue-and-groove clear of the lid counterbores (#62)`;
  - footer: `BREAKING CHANGE: a base and a lid printed on either side of this change do not mate (the +Y tongue/groove moved 3.5 mm outward).`
- The records go in a `docs:` commit, which also carries #68's texts. Stage explicit paths only.
- The PR body starts with two lines, `Closes #62` and `Closes #68`, and includes:
  - the plan's §0 table;
  - the golden table (plan §8);
  - the gate results;
  - the images `before_after_pro-convert-hdmi-plus.png` and `hero_pro-convert-hdmi-plus.png`;
  - one line stating that **the `CLAUDE.md` fixed decision "captive" is changed on the user's decision of 2026-09-29, relayed by the teamlead**.

**GB14′: Sequencing with H (binding on H).**
- **G lands first.** H branches from `main` after G merges.
- If H's branch already exists and is pushed, it takes G by `git merge main`, **not** a rebase (CONTRIBUTING.md:100–102). It then re-runs its full gate and regenerates goldens with its own targeted `golden --update`.
- Golden JSON and record ids are never hand-merged.
- H re-baselines its expected volumes on post-G `main`: every base is +22.40 mm³.
- **H's ids come from its own issues:**
  - #63 top lock: D63.x, T1-63.x, R63.x, M63.x, Q63.x.
  - #64 open −X end and `MCC_RAIL_LEN` 150 → 136: D64.x, T1-64.x.
  - #65 tie-down slots: D65.x.
  - #66 printability collinear vertices: D66.x.
  - Its draft's "D52" and "T1-91" are replaced at H's gate.
- **Expected textual conflicts when H takes G:**
  - `scripts/printability.py`: G appends; H edits `_cantilevers()`.
  - `constants.scad`: different sections.
  - `architecture.md` and `layout-patch-wall.md`: the top entries and the §9/§11/§12/§13 tails.
  - `CLAUDE.md` Closure bullet: G edits its first lines; H edits the gravity-lock sentences.
  - `BOM.md` and `CHANGELOG.md`.

## Implementation order (replaces the one above)

1. Run `git fetch origin`. `main` must equal `origin/main`, at 4e3a93f or later.
   - Create `git switch -c feature/issue-62-lid-screw-hole-openings main`.
   - `build.py doctor` must be green.
2. Save the negative-control lids exactly as in plan §7.1.
3. Apply the patch:
   - `git apply --check` on `C:\Users\Niels\AppData\Local\Temp\claude\C--repos-github-magewell-converter-cases\21ce76a1-d282-4f53-b50d-05d7eb636fdb\scratchpad\plans\G-lid-screw-hole-openings.patch`, then `git apply` the same file.
   - `git diff --stat` must show 6 files, +153/−20. If it does not, apply the hunks by hand from plan §5.2.
4. Apply GB1′ to GB9′.
5. Run the grep checks. Each must return no hits:
   - `mcc_captive_thumbscrew_hole` in `lib models tests scripts .claude/skills`;
   - `_mcc_cavity_rect` and `cos(180 / 64)` in `lib/mcc/shell.scad`;
   - `T1-91` and `T1-92` in `lib tests scripts`;
   - `captive thumbscrew` and `captive-thumbscrew` in `lib tests scripts .claude/skills CLAUDE.md BOM.md`.
6. Run the gates from plan §7.2, steps 1 to 11, with these expected messages:
   - Step 3: `mcc: T1-62.1 lid fastener [95.25, 73.175] counterbore rim is -2.25482 mm from the groove, below MCC_LID_CB_WEB_MIN=1.2 on "pro-convert-hdmi-plus"`.
   - Step 4 (`-D MCC_LID_CB_D=12`): T1-62.1, rim `-0.757236`.
   - Step 5: `mcc: T1-62.2 MCC_TG_PATCH_INSET=2 outside [MCC_WALL=3, MCC_T_PATCH=8]`.
   - **Step 5b:** the same with `-D 'part="base"'` must also fail with T1-62.2.
   - Step 1, `smoke`: 12/12.
   - Step 2: both old lids FAIL with `accidental_openings=3`.
   - Steps 7 to 11: green, with `accidental_openings=0` on every lid, 0 slicer warnings, and a Plus-lid STEP of 258 faces.
7. Refresh the goldens with the plan §8 command. `git diff --stat tests/golden` must show exactly the 17 files, and every delta must match plan §8.
8. Apply GB10′ to GB12′.
9. Commit and open the PR as in GB13′. Push, and wait for the `render` check to be green. Then merge.
10. Tell the teamlead. H follows GB14′.

For the teamlead:
- add M62.1 to `.claude/knowledge/session-resume.md`'s physical plan;
- correct any memory note that says "captive thumbscrews".

## Appendix A′: `.claude/knowledge/architecture.md` (verbatim; replaces Appendix A)

**A0′ + A1′. Two new top paragraphs.** Insert both before the line that begins `**Revision 19, 2026-09-29 (end-stop remnants retired — D52;`. Put #68 first, one blank line after each:

```
**Issue #68, 2026-09-29 — record ids follow GitHub issues (user rule).** Every feature, bug and task
gets a GitHub issue first, and the records it creates are numbered after that issue: for issue N,
decisions and deviations **DN.x** (§13), risks **RN.x** (§11), open questions **QN.x** and measurements
**MN.x** (§12), Tier-1 asserts **T1-N.x** (§9, `layout-patch-wall.md` §9 and the assert messages in
code), x = 1, 2, … within the issue. This file no longer bumps a revision number: a change is recorded
here at the top under its issue, newest first. **History stays:** rev ≤ 19, D1 … D52, T1-01 … T1-90
(with their letter suffixes), R1 … R47, M1 … M22 and Q1 … Q23 keep their numbers and are never
renumbered, and no further sequential id is allocated. A new id always carries its `.x`, so it never
reads as an old one: `T1-62` is the rail-clearance assert of rev 16, `T1-62.1` is issue #62's first
assert (search with the dot, `T1-62\.`). The rule in full: §13's introduction.

**Issue #62, 2026-09-29 — lid thumbscrew holes (D62.1, D62.2; plan G,
`docs/plans/2026-09-29-lid-screw-hole-openings.md`).** The external CAD specialist found see-through
crescents in 3 of the 6 lid thumbscrew counterbores on every SKU: on the 8 mm patch wall the lid's groove
ran through the ⌀8 counterbores of the fasteners at `MCC_FASTENER_INSET` = 10 (D62.1, latent since the
first lid). Fix: on the +Y wall only, the tongue-and-groove frame moves outward to `MCC_TG_PATCH_INSET` =
4.5 mm from the outer face (`layout-patch-wall.md` §15 ruling 4 amended); fasteners, bosses, inserts and
the other three walls do not move. Guards: **T1-62.1** (counterbore web to the groove ≥ 1.2 mm),
**T1-62.2** (the inset stays on the patch wall) and a Tier-3 check that fails a case lid with any
accidental see-through opening, with a `smoke` self-test (§8, §9). User decisions the same day: the
thumbscrews keep a **small Ø7–8 mm knurled head recessed in the ⌀8 counterbore** (not DIN 653) and are
**not captive** (D62.2; Q62.1 answered; `mcc_captive_thumbscrew_hole()` → `mcc_thumbscrew_hole()`).
New: **D62.1, D62.2, T1-62.1, T1-62.2, R62.1, M62.1, Q62.1**. No envelope figure moves; base
+22.40 mm³, lid −46.48 mm³ on every SKU.
```

**A2′. §3, the L1 list.**
- Old:
  ```
      lib/mcc/fasteners.scad                heat-set bosses, captive thumbscrew, 1/4"-20 boss
  ```
- New:
  ```
      lib/mcc/fasteners.scad                heat-set bosses, lid thumbscrew hole (non-captive, D62.2), 1/4"-20 boss
  ```

**A3′. §5 table, row "Lid".**
- Old:
  ```
  | Lid | the D32 patch-wall lip is gone (nothing to frame); the tongue/groove runs unbroken | `shell.scad` `mcc_shell_lid()` |
  ```
- New:
  ```
  | Lid | the D32 patch-wall lip is gone (nothing to frame); the tongue/groove runs unbroken — on this wall 4.5 mm (`MCC_TG_PATCH_INSET`) from the outer face instead of flush with the inner face (tongue 2.9–4.5, groove 2.65–4.75 mm), so the groove clears the lid's thumbscrew counterbores (#62, D62.1, T1-62.1) | `shell.scad` `_mcc_tg_rect()`, `mcc_shell_lid()` |
  ```

**A4′. §8, a new bullet.** Insert after the bullet that ends `together. >45° overhang areas are reported with `check --verbose`, not failed.`:
```
- **A case lid may not have an accidental see-through opening (#62, D62.1).** `check_mesh()` runs
  `printability.non_prismatic_see_through()` on every print-pose file named in `build.py`'s
  `SEE_THROUGH_FILE_NAMES` (`lid.stl` — every case lid) in `check`, `check --all` and each `ci` part
  pipeline: the lid is sliced at the middle of every Z interval between consecutive vertex heights, and
  each connected region that is open along Z at every height must equal one connected void of at least
  one slice. A drawn hole or slot does; an opening made by two overlapping cuts (the D62.1 counterbore
  crossing the groove) does not, and fails the part. `smoke` runs its self-test. **Scope, on purpose:**
  lids only (≈ 0.1 s each) — a base needs ≈ 540 slices (≈ 320 s), so bases, coupons and brackets stay
  out of the per-part gate; a new lid-like part joins `SEE_THROUGH_FILE_NAMES` in the same change, and a
  lid feature the check cannot represent (a conical countersink) extends the check in the same change.
  It complements T1-62.1 — the assert names the known pair at render time, the mesh check catches any
  pair — and no golden field replaces it: a golden records what the geometry is, not whether it is right.
```

**A5′. §9 Tier 1, the T1 ids.** Insert after the line ending `arch's sandwich parts; listed in `layout-patch-wall.md` §9). **The next free id is T1-91.**`:
```
**From issue #68 on, Tier-1 ids are issue-scoped: `T1-<issue>.<n>`** (§13's introduction); T1-01 …
T1-90 keep their numbers and no sequential id follows them. **#62 adds T1-62.1 and T1-62.2** (D62.1):
T1-62.1 — for every lid fastener, the counterbore's radius as cut (`mcc_thumbscrew_hole_rim_r()`) stays
≥ `MCC_LID_CB_WEB_MIN` (1.2) inside the groove ring's inner edge, evaluated in `mcc_shell_lid()`;
T1-62.2 — `MCC_WALL ≤ MCC_TG_PATCH_INSET ≤ MCC_T_PATCH`, evaluated inside `_mcc_tg_rect()` so a base
render trips it too. Neither is the old **T1-62** (rail clearances, rev 16).
```

**A6′. §9 Tier 2.**
- Old: `asserts fire) without tessellating, so it is fast. Non-zero exit = failure.`
- New:
  ```
  asserts fire) without tessellating, so it is fast. Non-zero exit = failure. Since #62 `smoke` also runs
  the Python self-test of the lid see-through check (`printability.selftest_see_through()`: two synthetic
  lids, one broken, one not) — a Tier-3 checker that silently stops finding anything is worse than none.
  ```

**A7′. §9 Tier 3.**
- Old: `trimesh; it is unreliable. Rely on the Tier-1 assert plus the slicer.`
- New:
  ```
  trimesh; it is unreliable. Rely on the Tier-1 assert plus the slicer. **#62:** `check` also fails a case
  lid with an accidental see-through opening (§8, D62.1) — a topology test on a thin slab, not a
  wall-thickness measurement, so the rule above stands.
  ```

**A8′. §11 R7.**
- Old: `Baseline stays the user's 4 captive M3 thumbscrews; **6 for any lid over 180 mm span** (D-04).`
- New:
  ```
  Baseline stays the user's 4 M3 thumbscrews (non-captive since D62.2, 2026-09-29); **6 for any lid over 180 mm span** (D-04).
  ```

**A9′. §11 intro and R62.1.**

After the line `## 11. Risks carried into the design` and its blank line, insert the following, followed by one blank line:
```
Risks R1 … R47 keep their numbers. From issue #68 (2026-09-29) a new risk is **R<issue>.<n>** (§13's
introduction) and is appended at the end of this section.
```

After R47's last line (`architect, not a parameter edit. M20 measures `W_LIFT_RAIL`.`), insert one blank line and:
```
**R62.1 — the lid counterbore has almost no headroom, and the thumbscrew is not yet in hand. NEW
2026-09-29 (#62, D62.1/D62.2).** The user fixed the hardware class: a small knurled M3 head, Ø7–8 mm,
seated in the lid's ⌀8 × 1.5 mm counterbore (`MCC_LID_CB_D`, depth `lid_t/2`, both `assumed`) — not
DIN 653's Ø12 — and non-captive. What is left:
- **Diameter.** With `e = 10` and `MCC_TG_PATCH_INSET` = 4.5, T1-62.1 fires above a ⌀8.09 counterbore
  (web 1.245 against 1.2). A head that measures Ø8.0 will not drop into a printed ⌀8.0 counterbore (FDM
  holes print undersize — the reason `MCC_HOLE_COMP` exists), so a Ø8 head forces a larger counterbore,
  which forces a smaller inset: a base + lid change that pushes the tongue out over the bezel recess's
  chamfered roof (at 4.0 its outer edge rides on ≈ 2.3 mm of roof). **That is an architect re-gate, not a
  constant tweak.** A Ø7 head needs nothing.
- **Height.** A head taller than 1.5 mm stands proud of the lid by the difference. Deepening the
  counterbore thins the 1.5 mm of lid the head clamps on. Decide with M62.1 in hand.
- **Length.** The clamp stack allows ≤ 8.2 mm under the head: 1.5 mm of lid below the counterbore floor
  plus the 6.7 mm blind insert bore (`mcc_heat_set_bore()`: insert 5.7 + 1). M3×6 puts 4.5 mm into the
  5.7 mm insert; M3×8 leaves 0.2 mm nominal; the former BOM figure, M3×10, bottomed out before clamping
  (D62.2).
- **Loss.** A non-captive screw can be dropped when a lid is opened on stage — accepted by the user.
```

**A10′. §12 intro and Q62.1.**

After the line `## 12. Open questions / assumptions` and its blank line, insert the following, followed by one blank line:
```
Questions 1 … 23 and measurements M1 … M22 keep their numbers. From issue #68 (2026-09-29) a new
question is **Q<issue>.<n>**, written after question 23 as a paragraph of its own, and a new measurement
is **M<issue>.<n>**, appended at the end of the measurement table (§13's introduction).
```

After question 23's last line (`    (D48) goes back to the user.`), insert one blank line and:
```
**Q62.1 — Which lid thumbscrew, and is it captive? NEW and answered 2026-09-29 (#62, user).** A small
knurled M3 head, **Ø7–8 mm, recessed in the ⌀8 counterbore as modelled** — not DIN 653 (Ø12, which fits
no counterbore at `e = 10`); **not captive** (D62.2). The residue — the real head's ⌀ and height, and the
screw length — is R62.1/M62.1.
```

**A11′. §12, the measurement table and the numbering note.**

Insert after the `| **M22** |` row:
```
| **M62.1** | **Buy the chosen lid thumbscrew (small knurled M3 head, Ø7–8 mm) and measure: head ⌀ across the knurl, head height, under-head length; try it in a printed ⌀8 × 1.5 counterbore (a test print of one lid corner is enough)** | **R62.1 — gates the first full-size lid print.** A tight fit, or a head over ≈ 7.8 mm, means the counterbore must grow — T1-62.1 fires above ⌀8.09, so that is an architect re-gate, not a constant tweak. A head over 1.5 mm stands proud by the difference. Length ≤ 8.2 mm under the head (M3×6 recommended) | User, after buying |
```

Insert after the line `> **Rev 18** adds M22 (plan D).`:
```
> **#62** adds M62.1 (plan G). From issue #68 on, measurement ids follow the issue (§12's introduction).
```

**A12′. §13 intro and two rows.**

After the line `matters, and the resolution (fixed / accepted-and-rule-updated / escalated).`, insert one blank line and the following. The heading stays `## 13. Deviations log`, because `CONTRIBUTING.md` and the PR template cite it.
```
**Record ids (issue #68, user rule 2026-09-29).** Every feature, bug and task gets a GitHub issue first.
The records it produces are numbered after that issue — for issue N: **DN.x** in this table, **RN.x** in
§11, **QN.x** and **MN.x** in §12, **T1-N.x** for a Tier-1 assert (§9, `layout-patch-wall.md` §9, and
the assert's message in code) — with x = 1, 2, … in the order the issue creates them. A decision that
changes a rule is recorded here like a deviation. A change to this file names its issue; there is no
revision number after rev 19. **History stays as written:** D1 … D52 (D11 sits out of order), rev ≤ 19,
T1-01 … T1-90, R1 … R47, M1 … M22 and Q1 … Q23 keep their numbers — nothing is renumbered and no
further sequential number is allocated. An issue-scoped id always carries its `.x`, so `T1-62` (rail
clearance, rev 16) and `T1-62.1` (issue #62) can never be confused. New rows are appended at the end of
the table.
```

Append both rows **at the end of the table**, after the row that begins `| **D11** | 2026-09-08 |`:
```
| **D62.1** | 2026-09-29 | §5 lid row / `layout-patch-wall.md` §15 ruling 4 (the tongue flush with the wall's inner face; groove = tongue ± `MCC_CLR_TG`) with §6 (the fastener ring at `e` = 10 from the outer faces). The lid is one 3 mm slab: two cuts in it must never meet | `lib/mcc/shell.scad:400` (groove) with `lib/mcc/fasteners.scad:87-98` (counterbore) and `lib/mcc/constants.scad:373` (`MCC_FASTENER_INSET`), lines at `4e3a93f`: on the 8 mm patch wall the groove (6.15–8.25 mm from the outer face, 2.0 mm deep) runs through the ⌀8 counterbore (rim 5.995 mm, floor 1.5 mm below the outer face) of the three patch-side lid fasteners; the cuts overlap 0.5 mm in Z, so 11.38 mm² (27.6 %) of each counterbore floor is open on all 8 SKUs (24 holes), and the through-hole stands 0.05 mm from the groove | Found by the external CAD specialist in the exact `lid.step`. Latent since `b6a8b77` (2026-09-08): `check`, the slicer gate, the goldens (0.018 % of the volume — the first lid golden already contained it) and T1-33 all passed it. Ruling 4's own reason — a centred tongue does not fit a 3 mm wall — never applied to the 8 mm wall | **Fixed by #62 (plan G, option T).** On the +Y wall only, the frame is offset outward: `MCC_TG_PATCH_INSET` = 4.5 (tongue 2.9–4.5, groove 2.65–4.75 mm from the outer face; counterbore web 1.245 mm) through `_mcc_tg_rect()`, which replaces `_mcc_cavity_rect()`; fasteners, bosses, inserts and the other three walls do not move. New `MCC_LID_CB_D` (8.0, `assumed`, was a literal), `MCC_LID_CB_WEB_MIN` (1.2), `mcc_thumbscrew_hole_rim_r()`; **T1-62.1**, **T1-62.2**; the Tier-3 lid see-through check with its `smoke` self-test (§8). Rejected: moving the three fasteners inboard (an unverifiable cable-bay change), interrupting the frame at each hole (the fallback), dropping the counterbore, a thicker lid (H = 51 is fixed). Base +22.40 mm³, lid −46.48 mm³, bbox unchanged on every SKU; a base and a lid from either side of the change do not mate (MAJOR). Ruling 4 amended in `layout-patch-wall.md` §15 |
| **D62.2** | 2026-09-29 | `CLAUDE.md` fixed decision "6 captive M3 knurled thumbscrews" (Closure) and `mcc_captive_thumbscrew_hole()`'s doc ("stays captive when backed out") | The model never retained the screw: `lib/mcc/fasteners.scad:70-98` cuts a ⌀3.4 clearance hole and a ⌀8 × 1.5 counterbore — no groove, clip, O-ring or thread holds an M3 once it is out of the base's insert. And `BOM.md:38`'s "assumed M3×10" bottoms out: under a 1.5 mm counterbore floor the 6.7 mm blind insert bore allows 8.2 mm under the head | A fixed decision the geometry did not implement; a public module named for a property it lacks; a BOM length that cannot clamp the lid | **Resolved by user decision 2026-09-29 (#62) — the rule changes, no geometry changes.** The thumbscrews are **non-captive**, with a **small knurled head, Ø7–8 mm, recessed in the ⌀8 counterbore** (not DIN 653, Ø12). `CLAUDE.md` Closure reworded; `mcc_captive_thumbscrew_hole()` renamed `mcc_thumbscrew_hole()` (no alias) and its doc rewritten; BOM row: small head, ≤ 8 mm under the head (M3×6), non-captive. `knowledge/**` unchanged — it lists knurled and captive screws as sourced options, not as the design. Q62.1 answered; residue R62.1/M62.1 |
```

## Appendix B′: `.claude/knowledge/layout-patch-wall.md` (verbatim; replaces Appendix B)

This file was not touched by #61, so every anchor is as in Appendix B.

**B1′. Status header.** Insert before the first `Status: **revision 18, 2026-09-28**` line, followed by one blank line:
```
Status: **issue #62, 2026-09-29** (aligned with `architecture.md` — D62.1/D62.2, plan G: the lid
thumbscrew holes). From issue #68 on this file, like `architecture.md`, names issues instead of revisions
and numbers new records after them (`architecture.md` §13 intro). §6 gains the counterbore web rule and
the non-captive screw; **§9** gains **T1-62.1** and **T1-62.2**; §10 D-04 drops "captive"; §11 gains an
addendum; §15 ruling 4 is amended for the +Y wall. No envelope figure moves.
```

**B2′. §6, lid fasteners.**

Old:
```
Captive M3 knurled thumbscrews into M3 heat-set inserts (`MCC_INSERT_M3`, `constants.scad:96`);
boss OD ≥ 1.8 × insert OD = 8.28 mm (`constants.scad:102`), ≥ 2 mm material to any edge
(`fdm-rugged-enclosure-guidelines.md:127`).
```

New:
```
Non-captive M3 knurled thumbscrews with a small head (Ø7–8 mm, seated in the lid's ⌀8 × 1.5 mm
counterbore, `MCC_LID_CB_D`; user decision 2026-09-29, `architecture.md` D62.2) into M3 heat-set inserts
(`MCC_INSERT_M3`, `constants.scad:96`); boss OD ≥ 1.8 × insert OD = 8.28 mm (`constants.scad:102`),
≥ 2 mm material to any edge (`fdm-rugged-enclosure-guidelines.md:127`).

**Counterbore web rule (#62, D62.1).** The lid is one 3 mm slab, so its cuts must never meet: every
counterbore keeps ≥ `MCC_LID_CB_WEB_MIN` (1.2 mm) of lid, in plan, to the groove ring's inner edge
(**T1-62.1**). At `e = 10` that holds by 2.745 mm on the 3 mm walls; on the 8 mm patch wall it holds only
because the tongue-and-groove frame is offset outward there (`MCC_TG_PATCH_INSET` = 4.5, web 1.245 mm —
§15 ruling 4 as amended). The counterbore can therefore grow to ⌀8.09 at most before T1-62.1 fires
(`architecture.md` R62.1).
```

**B3′. §9 intro and two rows.**

- Intro.
  - Old: `Add to `architecture.md` §9's minimum set. All are cheap, pure, and fire at render.`
  - New:
    ```
    Add to `architecture.md` §9's minimum set. All are cheap, pure, and fire at render. Ids: T1-01 … T1-90
    are history; from issue #68 (2026-09-29) a new assert is **T1-<issue>.<n>** (`architecture.md` §13
    intro), appended at the end of this table.
    ```
- Insert after the row that begins `| **T1-86 … T1-90** |`:
  ```
  | **T1-62.1** | *the lid's counterbores clear the groove* — for every `lid_fastener_pos` p: p lies inside the groove ring's inner edge `gi` (`_mcc_tg_rect()` shrunk by `MCC_CLR_TG`), and `min(p.x − gi.x0, gi.x1 − p.x, p.y − gi.y0, gi.y1 − p.y) − mcc_thumbscrew_hole_rim_r(MCC_LID_CB_D) ≥ MCC_LID_CB_WEB_MIN` (1.2) | **new, #62** (D62.1, plan G). Patch-side fasteners `5.25 − 4.005 = 1.245` ✓; the other walls `6.75 − 4.005 = 2.745` ✓. Evaluated in `mcc_shell_lid()`. The old geometry (`MCC_TG_PATCH_INSET` = 8) gives −2.25 and fails. Not the old T1-62 (rail clearances) |
  | **T1-62.2** | *the patch-side frame stays on the patch wall* — `MCC_WALL ≤ MCC_TG_PATCH_INSET ≤ MCC_T_PATCH` | **new, #62** (D62.1). Evaluated in `_mcc_tg_rect()`, so a base render trips it too |
  ```

**B4′. §10, D-04.**
- Old:
  ```
  | D-04 | 4 captive M3 thumbscrews baseline; **6 for lids over 180 mm span**. | Architect-derived, user-reviewed | **ACCEPTED 2026-09-08** |
  ```
- New:
  ```
  | D-04 | 4 M3 thumbscrews baseline; **6 for lids over 180 mm span**. The screws are **non-captive** (user decision 2026-09-29, `architecture.md` D62.2). | Architect-derived, user-reviewed | **ACCEPTED 2026-09-08** |
  ```

**B5′. §11, the rev-5 addendum row.**
- Old:
  ```
  | `MCC_TG_W` / `MCC_TG_H` | **1.6 / 2.0**, offset (shiplap) tongue flush with the wall's **inner** face |
  ```
- New (the rest of the row is unchanged):
  ```
  | `MCC_TG_W` / `MCC_TG_H` | **1.6 / 2.0**, offset (shiplap) tongue flush with the wall's **inner** face — **except on the +Y patch wall, where its inner edge sits `MCC_TG_PATCH_INSET` (4.5) from the outer face (#62, D62.1)** |
  ```

**B6′. §11, a new addendum.** Insert after the paragraph that ends `§15 ruling 2026-09-08b.` (the "Explicitly NOT added: `MCC_APERTURE_TOP_OPEN`" paragraph) and before the `---` preceding §15:
```
### Addendum (#62, 2026-09-29) — the lid thumbscrew holes (D62.1)

| Constant | Value | Purpose / where used |
|---|---|---|
| **`MCC_TG_PATCH_INSET`** | **NEW — 4.5** | +Y patch wall only: outer face → tongue inner edge (tongue at `[inset − MCC_TG_W, inset]`, groove `± MCC_CLR_TG`). The largest 0.5 mm step that keeps T1-62.1's web (`10 − 4.005 − 0.25 − 1.2 = 4.545`); it also keeps the tongue (all but its outer 0.1 mm) on the full-height wall behind the bezel-recess floor. `_mcc_tg_rect()`, T1-62.1, T1-62.2. A change is an architect re-gate (R62.1) |
| **`MCC_LID_CB_D`** | **NEW — 8.0 `assumed`** | Lid thumbscrew counterbore diameter (was the literal `head_d = 8` in `fasteners.scad`). User decision 2026-09-29: keep ⌀8 for a small Ø7–8 mm knurled head (D62.2). `mcc_thumbscrew_hole()`, `mcc_thumbscrew_hole_rim_r()`, T1-62.1; measured by M62.1 |
| **`MCC_LID_CB_WEB_MIN`** | **NEW — 1.2** | Minimum lid material between a counterbore and the groove, in plan: three perimeters (`fdm-rugged-enclosure-guidelines.md:35`), the same rule as T1-61. T1-62.1 |
```

**B7′. §15 ruling 4.** In the row that begins `| 4 | `MCC_TG_W/H = 3.0/4.0` |`:
- Old end of row: `and must be re-cut to 1.6/2.0 |`
- New end of row:
  ```
  and must be re-cut to 1.6/2.0. **Amended by #62 (2026-09-29, D62.1):** "flush with the wall's inner face" holds on the three 3 mm walls only. On the 8 mm +Y patch wall the frame is offset outward — tongue inner edge `MCC_TG_PATCH_INSET` = 4.5 mm from the outer face — because flush with that wall's inner face the lid groove ran through the ⌀8 thumbscrew counterbores at `e = 10` (T1-62.1). This ruling's reason (a centred tongue does not fit a 3 mm wall) never applied to the 8 mm wall |
  ```

## Appendix C′: `CLAUDE.md` (verbatim; replaces Appendix C)

This file was not touched by #61.

**C1′. Closure, the captive wording.**

Old:
```
6 captive M3 knurled thumbscrews into M3 heat-set inserts
  (rule: 6 above 180 mm lid span; both families are above it).
```

New:
```
6 **non-captive** M3 knurled thumbscrews into M3 heat-set
  inserts — a **small head, Ø7–8 mm, recessed in a Ø8 counterbore** in the lid, not DIN 653's Ø12
  (user decision 2026-09-29, D62.2); rule: 6 above 180 mm lid span, both families are above it. On the
  patch wall the tongue-and-groove sits 4.5 mm from the outer face so the lid groove clears those
  counterbores (architecture.md D62.1).
```

The text that follows, ` **Retention: captive 1/4"-20`, stays untouched: the side bolt **is** captive.

**C2′. Standard commands.** Unchanged from C2 (no ids): the `smoke` and `check` lines as given there.

**C3′. Current status, the evolutions list.**

Old:
```
the vertical VESA-column bracket and the arch's sandwich parts (D51) — are in architecture.md §13.
```

New:
```
the vertical VESA-column bracket and the arch's sandwich parts (D51), and the patch-wall
tongue-and-groove moved clear of the lid's thumbscrew counterbores (D62.1) — are in architecture.md §13.
```

**C4′. Current status, the next milestone.**
- Old:
  ```
  dongle splitter and the E-clip, write the measured values
  ```
- New:
  ```
  dongle splitter, the E-clip and the lid thumbscrews (M62.1), write the measured values
  ```

**C5′. The #68 rule.** Insert directly above the line `## Fixed decisions (do not re-open without a user decision)`, followed by one blank line:
```
**Record ids follow GitHub issues** (user rule 2026-09-29, issue #68). Every feature, bug and task gets
a GitHub issue first; its branch is `feature/issue-<N>-<topic>` and its PR closes the issue. The records
it creates are numbered after the issue — for issue N: decisions **DN.x**, risks **RN.x**, measurements
**MN.x**, open questions **QN.x** and Tier-1 asserts **T1-N.x** (also in the assert messages in code),
x = 1, 2, … within that issue. `architecture.md` no longer bumps a revision number; a change names its
issue. History stays as it is: rev ≤ 19, D1–D52, T1-01–T1-90, R1–R47, M1–M22 and Q1–Q23 keep their
numbers, and no new sequential number is allocated. A new id always carries its `.x`: `T1-62` is an old
assert, `T1-62.1` is issue #62's first. Full rule: `architecture.md` §13 intro.
```

## Appendix D′: Other documents (verbatim; replaces Appendix D)

The anchors are unchanged by #61. D3′ is D3 as written.

**D1′. `.claude/skills/print-check/SKILL.md`**

- §1.
  - Old: `plus Bambu's 3 mm "floating cantilever" rule. The`
  - New: `plus Bambu's 3 mm "floating cantilever" rule, and on case lids any accidental see-through opening — two cuts meeting in the 3 mm slab (architecture.md §8, #62, D62.1). The`
- §5, the long-lid bullet.
  - Old:
    ```
    - On a long lid (>~180 mm), 4 captive thumbscrews likely aren't enough to stop mid-span bow +
      tongue-and-groove joint opening under ASA warp (architecture §11 R7, currently flagged as needing a
      user decision toward 6 thumbscrews or a mid-span rib). Check whether that decision has been made
      for the specific case before printing a long lid with only 4.
    ```
  - New:
    ```
    - On a long lid (>~180 mm), 4 thumbscrews are not enough to stop mid-span bow + tongue-and-groove
      joint opening under ASA warp — D-04 (accepted 2026-09-08) puts 6 on every lid over 180 mm, which is
      every current SKU (architecture §11 R7). The thumbscrews are non-captive, with a small Ø7–8 mm head
      in the lid's Ø8 counterbore (D62.2); check the bought screw against M62.1 before the first lid print.
    ```
- §7 table: insert after the `len(split()) != 1` row:
  ```
  | `accidental_openings > 0` (case lid only) | Two cuts in the 3 mm lid overlap in plan and in Z — e.g. a counterbore reaching the groove (architecture.md D62.1) — so the lid is open where nobody drew a hole | Whatever you last moved in the lid (counterbore, groove, vent field); T1-62.1 and T1-37 should have fired first — if neither did, the new feature needs its own web assert |
  ```

**D2′. `.claude/skills/bom-update/SKILL.md`**

- Line 29.
  - Old: `| M3 knurled thumbscrew | <n> (4, or 6 on lids >~180 mm per architecture §11 R7) | captive lid fastening | knowledge/components/fasteners-and-hardware.md §2 |`
  - New: `| M3 knurled thumbscrew (small Ø7–8 mm head, ≤ 8 mm under the head) | <n> (4, or 6 on lids >~180 mm per architecture §11 R7) | lid fastening — non-captive (architecture D62.2) | knowledge/components/fasteners-and-hardware.md §2 |`
- Line 101: replace `| captive lid fastening |` with `| lid fastening — non-captive (architecture D62.2) |`.

**D3′. `.claude/skills/new-case-variant/SKILL.md`.** As D3 above.

**D4′. `.claude/knowledge/testing.md`**

- Tier 2.
  - Old: `   `-o *.csg` (evaluates the CSG tree, so Tier-1 asserts fire, without tessellating — fast).`
  - New:
    ```
       `-o *.csg` (evaluates the CSG tree, so Tier-1 asserts fire, without tessellating — fast), plus
       `scripts/printability.py selftest_see_through()` (two synthetic lids: the lid see-through check
       must flag the broken one and pass the other — architecture.md §9, #62).
    ```
- Tier 3.
  - Old: `   island (Bambu Studio's "floating regions"), and the **slicer gate** `slicer-check --require``
  - New:
    ```
       island (Bambu Studio's "floating regions"); on every `lid.stl` the **lid see-through check** (no
       accidental opening where two cuts meet — architecture.md §8, #62, D62.1); and the **slicer gate** `slicer-check --require`
    ```
- Green.
  - Old: `  not a failure, just an unwritten test).`
  - New: `  not a failure, just an unwritten test), and `selftest_see_through()` passed.`
- Green.
  - Old: `  floating islands. Goldens are measured`
  - New: `  floating islands; every case lid has zero accidental see-through openings. Goldens are measured`

**D5′. `tests/README.md`**

- After the line `any failure; the command prints a pass/fail table naming every test file.`, insert one blank line and:
  ```
  `smoke` also runs `scripts/printability.py selftest_see_through()` — two synthetic lids, one whose
  groove crosses a counterbore and one whose groove does not — so the lid see-through check (Tier 3)
  cannot silently stop finding openings (architecture.md §9, #62).
  ```
- After the line `visual/slicer check for wall thickness.`, insert one blank line and:
  ```
  Print-pose STLs also get the printability gate (`scripts/printability.py`: no floating island, no
  > 3 mm cantilever), and every `lid.stl` gets the **lid see-through check** — no region open along Z
  that is not one drawn cut (architecture.md §8, #62, D62.1).
  ```
- Green.
  - Old: `- `smoke`: every `tests/test_*.scad` ran to completion with no `ERROR:` (or there were none yet).`
  - New: `- `smoke`: every `tests/test_*.scad` ran to completion with no `ERROR:` (or there were none yet), and `selftest_see_through()` passed.`
- Green.
  - Old: `  connected shell, and within the 244 mm/axis bbox ceiling.`
  - New: `  connected shell, and within the 244 mm/axis bbox ceiling; print-pose STLs have no floating island or cantilever, and no case lid has an accidental see-through opening.`

**D6′. `scripts/README.md`**

- The `smoke` row.
  - Old: `(evaluates the tree, asserts fire, no tessellation). Fast. |`
  - New: `(evaluates the tree, asserts fire, no tessellation), plus `printability.py`'s `selftest_see_through()`. Fast. |`
- The `check --all` row.
  - Old: `on every print-pose `exports/**/*.stl` (the `*.model.stl` twins are skipped).`
  - New: `on every print-pose `exports/**/*.stl` (the `*.model.stl` twins are skipped), **plus the lid see-through check** on every `lid.stl` (`printability.non_prismatic_see_through()`: no accidental opening where two cuts meet — architecture.md §8, #62, D62.1; reported as `ACCIDENTAL OPENING` lines).`

**D7′. `CHANGELOG.md`.** Insert directly under `## [Unreleased]`, **above** `### Removed (2026-09-29, end-stop remnants)` (#61's entry), followed by one blank line:
```
### Fixed (2026-09-29, issue #62, external CAD review of `lid.step`) — MAJOR: a base and a lid printed on either side of this change do not mate

- **Lid thumbscrew holes had openings** (architecture.md D62.1): on all 8 SKUs the 3 patch-wall-side
  holes (the two (±X, +Y) corners and the patch-wall middle one) had a see-through opening in the Ø8
  counterbore floor, 11.4 mm² each, where the lid's groove crossed the counterbore. The
  tongue-and-groove frame on the +Y patch wall now sits 4.5 mm from the outer face
  (`MCC_TG_PATCH_INSET`) in both the base (tongue) and the lid (groove), clear of the counterbores. The
  other three walls and every fastener, boss and insert position are unchanged. No full case has been
  printed yet.
- New guards: asserts T1-62.1 (counterbore-to-groove web) and T1-62.2 (patch inset range); `build.py
  check` and the `ci` part gate fail a case lid with an accidental see-through opening; `build.py smoke`
  runs a self-test of that check.

### Changed (2026-09-29, issue #62, user decision) — the lid thumbscrews are not captive

- The 6 lid thumbscrews are **non-captive** M3 knurled thumbscrews with a small Ø7–8 mm head recessed in
  the Ø8 counterbore (architecture.md D62.2); the model never retained them, so no geometry changes.
  `mcc_captive_thumbscrew_hole()` is renamed `mcc_thumbscrew_hole()`. BOM: ≤ 8 mm under the head (M3×6
  recommended) — the earlier "assumed M3×10" would bottom out in the insert bore.

### Changed (2026-09-29, issue #68, user rule) — record ids follow GitHub issues

- Every feature, bug and task gets a GitHub issue first, and the decisions, risks, measurements, open
  questions and Tier-1 asserts it creates are numbered after it (D62.1, T1-62.1, …). `architecture.md`
  no longer has revision numbers. Existing ids (D1–D52, rev ≤ 19, T1-01–T1-90, R1–R47, M1–M22, Q1–Q23)
  are unchanged. Branches are always `feature/issue-<n>-<topic>` (CLAUDE.md, CONTRIBUTING.md).
```

## Appendix E′: The #68 rule in the branching and ticket documents (verbatim)

These three files still offer issue-less branches and plans, which contradicts the user's rule. #68 closes with G's PR, so they change in the same PR.

**E1′. `CONTRIBUTING.md`**

- Line 19, the Naming cell of the `feature/*` row.
  - Old: `` `feature/<kebab-topic>`, `feature/issue-<n>-<topic>` when a GitHub issue exists, or `feature/hotfix-<topic>` for an urgent fix |``
  - New: `` `feature/issue-<n>-<topic>` — every feature, bug and task gets its GitHub issue first (user rule 2026-09-29, #68), urgent fixes included |``
- Lines 21–23.
  - Old:
    ```
    A hotfix is **not** a separate branch type — it's a `feature/*` branch off `main` like any other,
    named `feature/hotfix-<topic>` (or `feature/issue-<n>-<topic>` if a GitHub issue tracks it) so it's
    recognizable in the branch list. It goes through the same PR → CI-green → merge → tag path as
    ```
  - New:
    ```
    A hotfix is **not** a separate branch type — it's a `feature/issue-<n>-<topic>` branch off `main`
    like any other, with its own issue. It goes through the same PR → CI-green → merge → tag path as
    ```
- Line 84.
  - Old: `git switch -c feature/<kebab-topic> main`
  - New: `git switch -c feature/issue-<n>-<topic> main`
- Lines 87–89.
  - Old:
    ```
    Naming: `feature/<kebab-topic>`, `feature/issue-<n>-<topic>` when a GitHub issue exists (see
    `.claude/knowledge/ticket-source.md`) — e.g. `feature/issue-12-vents` — or `feature/hotfix-<topic>`
    for an urgent fix on something already released.
    ```
  - New:
    ```
    Naming: `feature/issue-<n>-<topic>`, e.g. `feature/issue-12-vents`. Every feature, bug and task — an
    urgent fix included — gets its GitHub issue first (user rule 2026-09-29, #68; see
    `.claude/knowledge/ticket-source.md`); the PR closes it, and the records the work creates are
    numbered after it (CLAUDE.md "Record ids follow GitHub issues").
    ```
- Line 107.
  - Old: `git push -u origin feature/<kebab-topic>`
  - New: `git push -u origin feature/issue-<n>-<topic>`

**E2′. `.claude/skills/git-flow/SKILL.md`**

- Lines 22–24.
  - Old:
    ```
    | Ordinary work | `feature/<kebab-topic>` |
    | Work tracked by a GitHub issue | `feature/issue-<n>-<topic>` |
    | An urgent fix on something already released | `feature/hotfix-<topic>` (or `feature/issue-<n>-<topic>` if an issue tracks it) |
    ```
  - New:
    ```
    | Any feature, bug or task — its GitHub issue exists first (user rule, #68) | `feature/issue-<n>-<topic>` |
    | An urgent fix on something already released — also with its issue | `feature/issue-<n>-<topic>` |
    ```
- Line 39.
  - Old: `git switch -c feature/<kebab-topic> main`
  - New: `git switch -c feature/issue-<n>-<topic> main`
- Line 61.
  - Old: `git push -u origin feature/<kebab-topic>`
  - New: `git push -u origin feature/issue-<n>-<topic>`
- Lines 103–106.
  - Old:
    ```
    - `feature/<kebab-topic>`, or `feature/issue-<n>-<topic>` when a GitHub issue exists
      (`.claude/knowledge/ticket-source.md`). Don't invent an issue number — check with `gh issue list`
      first if unsure whether one exists.
    - `feature/hotfix-<topic>` for an urgent fix on something already released.
    ```
  - New:
    ```
    - `feature/issue-<n>-<topic>` — every feature, bug and task has its GitHub issue first (user rule
      2026-09-29, #68; `.claude/knowledge/ticket-source.md`), hotfixes included. Don't invent an issue
      number — check with `gh issue list`, and open the issue (or ask the teamlead to) if none exists.
      The PR closes it (`Closes #<n>`); the records the work creates are numbered after it (CLAUDE.md).
    ```

**E3′. `.claude/knowledge/ticket-source.md`**

- Lines 28–31.
  - Old:
    ```
    - **If no issue exists** (a plan was requested ad hoc, or the repo isn't pushed yet), write the plan
      to `docs/plans/<date>-<slug>.md` instead — `<date>` in `YYYY-MM-DD` form, `<slug>` a short
      kebab-case description of the task. Create `docs/plans/` if it doesn't exist yet; nothing else
      currently owns that directory.
    ```
  - New:
    ```
    - **If no issue exists yet**, one is opened first (user rule 2026-09-29, #68: every feature, bug and
      task gets a GitHub issue before any work). Only if the repo isn't pushed, write the plan to
      `docs/plans/<date>-<slug>.md` instead — `<date>` in `YYYY-MM-DD` form, `<slug>` a short kebab-case
      description of the task. A gated plan is also copied to `docs/plans/` with its architect verdict.
    ```
- Lines 36–41.
  - Old:
    ```
    a `feature/*` branch off `main`, merged back via PR. When a GitHub issue exists for a task, its
    feature branch references the issue number: `feature/issue-<n>-<topic>` (e.g.
    `feature/issue-12-vents`), so the branch and the tracked work are traceable to each other at a
    glance. When no issue exists — ad hoc work, or the repo isn't pushed yet — fall back to the plain
    `feature/<kebab-topic>` naming from `CONTRIBUTING.md`; don't invent an issue number to force the
    numbered form. See the `git-flow` skill and `CONTRIBUTING.md` for the full branching model.
    ```
  - New:
    ```
    a `feature/*` branch off `main`, merged back via PR. Every task has its GitHub issue first (user rule
    2026-09-29, #68), so its feature branch always references the issue number:
    `feature/issue-<n>-<topic>` (e.g. `feature/issue-12-vents`), its PR closes the issue, and the
    records it creates are numbered after it (CLAUDE.md "Record ids follow GitHub issues"). Don't invent
    an issue number — open the issue first. See the `git-flow` skill and `CONTRIBUTING.md` for the full
    branching model.
    ```

