#!/usr/bin/env python3
"""Build per-model and per-coupon release zips from already-rendered exports/ (issue #10).

Used by `.github/workflows/release.yml` after `build.py all --with-step` has populated
`exports/**`. Never invents artefacts — every file zipped must already exist there; a target with
nothing rendered is skipped with a warning, not silently dropped from a partial zip.

Usage:
    python scripts/package_release.py <version>      # e.g. v0.1.0

Writes:
    dist/<slug>-<version>.zip    one per discovered model — STL + 3MF + STEP + manifest for every
                                  part (base/lid/panel), plus a README.txt naming the device, the
                                  version, and the git SHA (and a PRE-RELEASE notice when any of
                                  that model's ports are below "measured" confidence — see
                                  `build.py confidence`).
    dist/coupons-<version>.zip   every discovered coupon's exports in one zip, one shared README.
    dist/brackets-<version>.zip  every discovered models/brackets/*.scad target's exports in one
                                  zip, one shared README (issue #26 — same flat, single-part,
                                  no-device shape as a coupon, packaged the same way).
    dist/step/<slug>-<part>.step
                                  every rendered STEP file, copied loose out of exports/ with a
                                  unique, self-describing name (e.g.
                                  "pro-convert-for-ndi-to-hdmi-base.step",
                                  "coupons-neutrik-tile.step") — with eight-plus device cases the
                                  bare `<part>.step` name (base.step, lid.step, panel.step) used by
                                  the pre-v0.1.0 release collided across models, since GitHub
                                  release assets must be unique repo-wide (issue #10). See
                                  `_step_asset_name()`.
    dist/SHA256SUMS.txt          one line per file under dist/ (the zips above and every
                                  dist/step/*.step), `<sha256>  <relative/path>`, sorted by path —
                                  lets anyone verify a downloaded release asset wasn't corrupted or
                                  tampered with.

`dist/` is gitignored exactly like `exports/` (architecture.md §8) — CI uploads the zips straight
to the GitHub Release and never commits them; delete `dist/` locally after a manual test run.
"""

from __future__ import annotations

import hashlib
import re
import shutil
import sys
import zipfile
from datetime import datetime, timezone
from pathlib import Path

import build  # sibling module: scripts/build.py — reuses discovery, device/confidence parsing, git helpers

DIST_DIR = build.REPO_ROOT / "dist"
STEP_DIR = DIST_DIR / "step"
ARTEFACT_EXTS = (".stl", ".3mf", ".step", ".manifest.json")


def _device_display_name(device_path: Path | None, slug: str) -> str:
    if device_path is not None:
        try:
            text = device_path.read_text(encoding="utf-8")
            m = re.search(r"^//\s*Device data:\s*(.+)$", text, re.MULTILINE)
            if m:
                return m.group(1).strip()
        except OSError:
            pass
    return slug.replace("-", " ").title()


def _model_is_prerelease(target: build.Target) -> bool:
    """True unless every port on this model's device record is at 'measured' confidence.
    Missing/unparseable device data is treated conservatively as pre-release."""

    device_path = build.device_file_for_model(target)
    if device_path is None or not device_path.is_file():
        return True
    measured_rank = build.confidence_rank("measured")
    return any(
        build.confidence_rank(port["confidence"]) < measured_rank
        for port in build.parse_device_ports(device_path)
    )


def _collect_part_files(export_dir: Path, part: str) -> list[Path]:
    return [p for ext in ARTEFACT_EXTS if (p := export_dir / f"{part}{ext}").is_file()]


def _write_readme(
    zf: zipfile.ZipFile, *, title: str, version: str, sha: str, contents: list[str], prerelease: bool,
) -> None:
    lines = [
        f"{title} — magewell-converter-cases",
        f"Version: {version}",
        f"Git SHA: {sha}",
        f"Built: {datetime.now(timezone.utc).isoformat(timespec='seconds')}",
        "",
        "Contents:",
        *[f"  {c}" for c in contents],
        "",
        "Open in Bambu Studio: File -> Import -> Import 3MF/STL/STEP (Ctrl+I). Pick the Bambu Lab",
        "X1 Carbon 0.4mm-nozzle printer profile and a Bambu/Generic ASA filament profile. base/lid",
        "print open-side-up as exported; the panel plate prints face-down. The .3mf carries plain",
        "geometry only (no print settings baked in); the .step is a faceted B-rep (planar facets",
        "merged, curved surfaces stay faceted) for use in other CAD tools. See this repository's",
        "README.md \"Open in Bambu Studio\" section for the full how-to.",
    ]
    if prerelease:
        lines += ["", "PRE-RELEASE: dimensions assumed, coupons not yet measured."]
    zf.writestr("README.txt", "\n".join(lines) + "\n")


def package_model(target: build.Target, version: str, sha: str) -> Path | None:
    export_dir = target.export_dir
    device_path = build.device_file_for_model(target)
    display_name = _device_display_name(device_path, target.name)
    prerelease = _model_is_prerelease(target)

    all_files: list[Path] = []
    for part in target.parts:
        all_files += _collect_part_files(export_dir, part)

    if not all_files:
        print(f"  [SKIP] {target.name}: nothing rendered under "
              f"{export_dir.relative_to(build.REPO_ROOT)} — run `build.py all` first")
        return None

    DIST_DIR.mkdir(parents=True, exist_ok=True)
    zip_path = DIST_DIR / f"{target.name}-{version}.zip"
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for f in all_files:
            zf.write(f, arcname=f.name)
        _write_readme(
            zf, title=display_name, version=version, sha=sha,
            contents=sorted(f.name for f in all_files), prerelease=prerelease,
        )
    flag = ", PRE-RELEASE" if prerelease else ""
    print(f"  [OK]   {target.name}: {zip_path.relative_to(build.REPO_ROOT)} ({len(all_files)} files{flag})")
    return zip_path


def _package_flat_parts(
    targets: list[build.Target], version: str, sha: str, *, zip_stem: str, title: str, label: str,
) -> Path | None:
    """Shared body for package_coupons()/package_brackets(): both discover a flat list of
    single-part targets (coupons, brackets — no base/lid split, no device record) and zip each
    target's already-rendered files under `<target-stem>/<file>` in one shared zip with one
    README. `zip_stem` names the zip (`dist/<zip_stem>-<version>.zip`); `label` is the noun used
    in the skip/OK console lines (e.g. "coupons", "brackets")."""

    per_target: dict[str, list[Path]] = {}
    for target in targets:
        files: list[Path] = []
        for part in target.parts:
            files += _collect_part_files(target.export_dir, part)
        if files:
            per_target[target.name] = files

    if not per_target:
        print(f"  [SKIP] {label}: nothing rendered — run `build.py all` first")
        return None

    DIST_DIR.mkdir(parents=True, exist_ok=True)
    zip_path = DIST_DIR / f"{zip_stem}-{version}.zip"
    contents: list[str] = []
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for name, files in per_target.items():
            slug = Path(name).name  # "coupons/neutrik-tile" -> "neutrik-tile"; "brackets/tv-bracket" -> "tv-bracket"
            for f in files:
                arcname = f"{slug}/{f.name}"
                zf.write(f, arcname=arcname)
                contents.append(arcname)
        # Coupons AND brackets are pre-release/unmeasured hardware (architecture.md §9 Tier 4 for
        # coupons; the bracket's own PLAN-ASSUMPTION 5/6 retention-force and plate-thickness
        # figures, layout-patch-wall.md §17.5, are likewise un-coupon-verified) — always flag.
        _write_readme(
            zf, title=title, version=version, sha=sha,
            contents=sorted(contents), prerelease=True,
        )
    n_files = sum(len(files) for files in per_target.values())
    print(f"  [OK]   {label}: {zip_path.relative_to(build.REPO_ROOT)} ({n_files} files)")
    return zip_path


def package_coupons(targets: list[build.Target], version: str, sha: str) -> Path | None:
    return _package_flat_parts(
        targets, version, sha, zip_stem="coupons", title="Calibration coupons", label="coupons",
    )


def package_brackets(targets: list[build.Target], version: str, sha: str) -> Path | None:
    return _package_flat_parts(
        targets, version, sha, zip_stem="brackets", title="Mounting brackets", label="brackets",
    )


def _step_asset_name(target: build.Target, part: str) -> str:
    """Unique, self-describing dist/step/ filename for one rendered part.

    `target.name` is e.g. "pro-convert-for-ndi-to-hdmi" (a model) or "coupons/neutrik-tile" (a
    coupon) — mirrors `build.golden_path()`'s stem logic so a single-part target (coupons, ad-hoc
    paths, where `part` already equals the target's own stem) doesn't repeat its name twice
    ("coupons-neutrik-tile.step", not "coupons-neutrik-tile-neutrik-tile.step"), while a
    multi-part model target gets the part appended ("pro-convert-for-ndi-to-hdmi-base.step").
    """

    stem = Path(target.name).name
    slug = target.name.replace("/", "-")
    return f"{slug}.step" if part == stem else f"{slug}-{part}.step"


def collect_step_files(targets: list[build.Target]) -> list[Path]:
    """Copy every already-rendered `<part>.step` for `targets` into `dist/step/` under its unique
    `_step_asset_name()`. Mirrors package_model()/package_coupons()'s "never invent artefacts"
    rule: a part with no STEP file on disk is silently skipped, not an error — `build.py step`
    (or `--with-step`) may not have been run, or the local STEP backend may be unavailable."""

    copied: list[Path] = []
    for target in targets:
        for part in target.parts:
            src = target.export_dir / f"{part}.step"
            if not src.is_file():
                continue
            STEP_DIR.mkdir(parents=True, exist_ok=True)
            dest = STEP_DIR / _step_asset_name(target, part)
            shutil.copy2(src, dest)
            copied.append(dest)
    return copied


def _sha256_file(path: Path, chunk_size: int = 1 << 20) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(chunk_size), b""):
            digest.update(chunk)
    return digest.hexdigest()


def write_sha256sums(dist_dir: Path) -> Path:
    """Write dist/SHA256SUMS.txt covering every file currently under dist/ (the per-model/coupon
    zips plus dist/step/*.step), one `<sha256>  <relative/posix/path>` line each, sorted by path
    for a stable, reviewable file. Overwrites any previous SHA256SUMS.txt and never includes itself."""

    files = sorted(
        (p for p in dist_dir.rglob("*") if p.is_file() and p.name != "SHA256SUMS.txt"),
        key=lambda p: p.relative_to(dist_dir).as_posix(),
    )
    lines = [f"{_sha256_file(p)}  {p.relative_to(dist_dir).as_posix()}" for p in files]
    sums_path = dist_dir / "SHA256SUMS.txt"
    sums_path.write_text("\n".join(lines) + ("\n" if lines else ""), encoding="utf-8")
    return sums_path


def main(argv: list[str] | None = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    if len(args) != 1:
        raise SystemExit("usage: package_release.py <version>   (e.g. v0.1.0)")
    version = args[0]

    sha = build.git_head_sha() or "unknown"
    print(f"packaging release {version} (git {sha})")
    DIST_DIR.mkdir(parents=True, exist_ok=True)

    models = build.discover_models()
    coupons = build.discover_coupons()
    brackets = build.discover_brackets()

    made: list[Path] = []
    for target in models:
        zp = package_model(target, version, sha)
        if zp is not None:
            made.append(zp)

    zp = package_coupons(coupons, version, sha)
    if zp is not None:
        made.append(zp)

    zp = package_brackets(brackets, version, sha)
    if zp is not None:
        made.append(zp)

    step_files = collect_step_files(models + coupons + brackets)
    if step_files:
        print(f"  [OK]   step: {len(step_files)} file(s) -> {STEP_DIR.relative_to(build.REPO_ROOT)}")
    else:
        print("  [SKIP] step: nothing rendered under exports/**/*.step — run `build.py step --all` first")

    if not made:
        print("error: no zips produced — nothing rendered under exports/ (run `build.py all` first)")
        return 1

    sums_path = write_sha256sums(DIST_DIR)
    n_summed = len(made) + len(step_files)
    print(f"  [OK]   {sums_path.relative_to(build.REPO_ROOT)} ({n_summed} file(s) hashed)")

    print(f"\n{len(made)} zip(s), {len(step_files)} STEP file(s) written to {DIST_DIR.relative_to(build.REPO_ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
