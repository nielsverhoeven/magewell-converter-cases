# Fusion snapshots (`.f3d`)

Viewing snapshots of every case variant and TV-bracket assembly as Autodesk Fusion archives, so the
designs travel with the repository (issue #125, `architecture.md` D125.1). Open one in Fusion with
**File > Open > Open from my computer**.

- They are **dumb STEP solids without a feature tree**, imported from the exact STEP exports: not the
  parametric Fusion masters of the migration (#81-#86), never a parity input, never a source of truth
  (R125.1). The source of truth stays the OpenSCAD tree until the cutover (#86).
- Cases: one design per variant, base + lid in the assembled position. Brackets: one design per
  assembly; spacers have no assembly position in the model and lie beside the bracket, marked loose.
- Built by `tools/fusion-scripts/MccFusionArchive` (script checkout `abc10de`) from the CI
  exports of `main` abc10de. Full provenance, including every STEP's sha256 and the bracket
  part placements: `manifest.json`.
- **Refresh** after any case or bracket geometry change: download the CI exports of the new `main`
  commit into `exports/`, run `MccFusionArchive` in Fusion, commit `archive/fusion/` with the source SHA
  in the commit message.

| File | Design | Configuration | Source `main` | STEP inputs (sha256 prefix) |
|---|---|---|---|---|
| `cases/pro-convert-for-ndi-to-aio.f3d` | pro-convert-for-ndi-to-aio | default | abc10de | `exports/pro-convert-for-ndi-to-aio/base.step` `8b1d807ea9b8`<br>`exports/pro-convert-for-ndi-to-aio/lid.step` `032dd3f81539` |
| `cases/pro-convert-for-ndi-to-hdmi.f3d` | pro-convert-for-ndi-to-hdmi | default | abc10de | `exports/pro-convert-for-ndi-to-hdmi/base.step` `d67a6a8e854c`<br>`exports/pro-convert-for-ndi-to-hdmi/lid.step` `40f365a3a44d` |
| `cases/pro-convert-for-ndi-to-hdmi-fan.f3d` | pro-convert-for-ndi-to-hdmi (fan) | base_fan | abc10de | `exports/pro-convert-for-ndi-to-hdmi/base_fan.step` `35fa838b1618`<br>`exports/pro-convert-for-ndi-to-hdmi/lid.step` `40f365a3a44d` |
| `cases/pro-convert-for-ndi-to-hdmi-4k.f3d` | pro-convert-for-ndi-to-hdmi-4k | default | abc10de | `exports/pro-convert-for-ndi-to-hdmi-4k/base.step` `eb8d459a89f5`<br>`exports/pro-convert-for-ndi-to-hdmi-4k/lid.step` `2f5e4e1d0b0c` |
| `cases/pro-convert-for-ndi-to-sdi.f3d` | pro-convert-for-ndi-to-sdi | default | abc10de | `exports/pro-convert-for-ndi-to-sdi/base.step` `d3a9d8029204`<br>`exports/pro-convert-for-ndi-to-sdi/lid.step` `1bda9ebe281a` |
| `cases/pro-convert-hdmi-plus.f3d` | pro-convert-hdmi-plus | default | abc10de | `exports/pro-convert-hdmi-plus/base.step` `46d25bf9f57a`<br>`exports/pro-convert-hdmi-plus/lid.step` `46ad936b4dbf` |
| `cases/pro-convert-hdmi-tx.f3d` | pro-convert-hdmi-tx | default | abc10de | `exports/pro-convert-hdmi-tx/base.step` `3f7c9001b624`<br>`exports/pro-convert-hdmi-tx/lid.step` `618871a61d04` |
| `cases/pro-convert-sdi-plus.f3d` | pro-convert-sdi-plus | default | abc10de | `exports/pro-convert-sdi-plus/base.step` `a361449e02a5`<br>`exports/pro-convert-sdi-plus/lid.step` `67f3ae80cfa1` |
| `cases/pro-convert-sdi-tx.f3d` | pro-convert-sdi-tx | default | abc10de | `exports/pro-convert-sdi-tx/base.step` `ad20d6db8368`<br>`exports/pro-convert-sdi-tx/lid.step` `10208533208e` |
| `brackets/arch-tv-bracket-direct.f3d` | arch-tv-bracket (direct) | assembly | abc10de | `exports/brackets/arch-tv-bracket/arm.step` `a002e6e54208`<br>`exports/brackets/arch-tv-bracket/arm.step` `a002e6e54208`<br>`exports/brackets/arch-tv-bracket/centre.step` `0497888fca4f` |
| `brackets/arch-tv-bracket-sandwich.f3d` | arch-tv-bracket (sandwich) | assembly | abc10de | `exports/brackets/arch-tv-bracket/arm_sandwich.step` `0d8762610875`<br>`exports/brackets/arch-tv-bracket/arm_sandwich.step` `0d8762610875`<br>`exports/brackets/arch-tv-bracket/centre_sandwich.step` `4d97e6443c92`<br>`exports/brackets/arch-tv-bracket/spacer.step` `d76bc7a38cd4`<br>`exports/brackets/arch-tv-bracket/spacer.step` `d76bc7a38cd4` |
| `brackets/vertical-tv-bracket.f3d` | vertical-tv-bracket | assembly | abc10de | `exports/brackets/vertical-tv-bracket/arm.step` `fcc16c728bee`<br>`exports/brackets/vertical-tv-bracket/arm.step` `fcc16c728bee`<br>`exports/brackets/vertical-tv-bracket/centre.step` `6035c7478a17`<br>`exports/brackets/vertical-tv-bracket/spacer.step` `5d123d116044`<br>`exports/brackets/vertical-tv-bracket/spacer.step` `5d123d116044` |
