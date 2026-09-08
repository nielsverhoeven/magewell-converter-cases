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

`dist/` is gitignored exactly like `exports/` (architecture.md §8) — CI uploads the zips straight
to the GitHub Release and never commits them; delete `dist/` locally after a manual test run.
"""

from __future__ import annotations

import re
import sys
import zipfile
from datetime import datetime, timezone
from pathlib import Path

import build  # sibling module: scripts/build.py — reuses discovery, device/confidence parsing, git helpers

DIST_DIR = build.REPO_ROOT / "dist"
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


def package_coupons(targets: list[build.Target], version: str, sha: str) -> Path | None:
    per_coupon: dict[str, list[Path]] = {}
    for target in targets:
        files: list[Path] = []
        for part in target.parts:
            files += _collect_part_files(target.export_dir, part)
        if files:
            per_coupon[target.name] = files

    if not per_coupon:
        print("  [SKIP] coupons: nothing rendered — run `build.py all` first")
        return None

    DIST_DIR.mkdir(parents=True, exist_ok=True)
    zip_path = DIST_DIR / f"coupons-{version}.zip"
    contents: list[str] = []
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for name, files in per_coupon.items():
            slug = Path(name).name  # "coupons/neutrik-tile" -> "neutrik-tile"
            for f in files:
                arcname = f"{slug}/{f.name}"
                zf.write(f, arcname=arcname)
                contents.append(arcname)
        # Coupons ARE the pre-release measurement step (architecture.md §9 Tier 4) — always flag.
        _write_readme(
            zf, title="Calibration coupons", version=version, sha=sha,
            contents=sorted(contents), prerelease=True,
        )
    n_files = sum(len(files) for files in per_coupon.values())
    print(f"  [OK]   coupons: {zip_path.relative_to(build.REPO_ROOT)} ({n_files} files)")
    return zip_path


def main(argv: list[str] | None = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    if len(args) != 1:
        raise SystemExit("usage: package_release.py <version>   (e.g. v0.1.0)")
    version = args[0]

    sha = build.git_head_sha() or "unknown"
    print(f"packaging release {version} (git {sha})")
    DIST_DIR.mkdir(parents=True, exist_ok=True)

    made: list[Path] = []
    for target in build.discover_models():
        zp = package_model(target, version, sha)
        if zp is not None:
            made.append(zp)

    zp = package_coupons(build.discover_coupons(), version, sha)
    if zp is not None:
        made.append(zp)

    if not made:
        print("error: no zips produced — nothing rendered under exports/ (run `build.py all` first)")
        return 1

    print(f"\n{len(made)} zip(s) written to {DIST_DIR.relative_to(build.REPO_ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
