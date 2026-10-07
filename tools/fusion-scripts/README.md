# Fusion helper scripts (manual, outside the build)

Small Autodesk Fusion scripts the user runs by hand to look at the repository's current exports in
Fusion. They read the exact STEP files under `exports\` (from `python scripts/build.py render` +
`step`, or downloaded from a CI run, see the `bambu-studio` skill §5) and change nothing in the repo.
They are not part of the Fusion generator (`cad/fusion/**`, issues #75–#86) and not run by CI.

Install on a machine: copy each folder to
`%APPDATA%\Autodesk\Autodesk Fusion 360\API\Scripts\`, then in Fusion press **Shift+S** and run it.
The paths at the top of each script assume the checkout at `C:\repos-github\magewell-converter-cases`;
edit `EXPORTS` / `STEP` / `OUT` on another machine.

| Script | What it does |
|---|---|
| `MccShowAll` | One unsaved document per case (base + lid), bracket and coupon. Nothing is saved to the hub. |
| `MccVerifyStep` | Issue #119 check: imports the NDI-to-HDMI `base_fan.step` (or the STEP named in `exports\fusion-verify\target.txt`), exports it to STL from Fusion and counts open / non-manifold edges. Writes `exports\fusion-verify\result.txt`. PASS = 1 body, 0 / 0. |
| `MccFusionArchive` | One design per case variant (base + lid) and per TV-bracket assembly (`brackets.json`: part placements echoed from the OpenSCAD assembly preview), each written as an `.f3d` into `archive/fusion/` with `manifest.json` provenance: per-STEP sha256 and `fingerprint` (shared with the CI gate `scripts/fusion_archive.py`, D125.2), `ci_run` from `exports/ci-run.txt`, `placements_sha256` (issue #125, D125.1). Hub saving is off by default (`SAVE_TO_HUB`; 12 designs exceed the Personal plan's 10 active editable documents). Re-echo `brackets.json` when a bracket's geometry changes. |
