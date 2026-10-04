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
| `MccCaseProject` | Creates (or reuses, name match ignores case) the hub project "Magewell converter cases" and saves one design, "MCC case variants", with every case variant (base + lid) on a grid. One document, so the Personal plan's limit on active editable documents is not stretched. |
