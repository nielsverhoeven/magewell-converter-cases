"""PR gate: the committed Fusion snapshots (archive/fusion/*.f3d) match the PR's STEP exports (#125, D125.2).

`archive/fusion/manifest.json` records, per archived STEP, a `fingerprint` (see `step_fingerprint`) and the
manifest records `placements_sha256` of the bracket placement file. `check` recomputes them from the
exports of the PR's CI run and reports every disagreement, so a PR that changes a case or bracket STEP
must also carry regenerated `.f3d` files (built locally with tools/fusion-scripts/MccFusionArchive).

Constraints (architecture.md D125.2):
- Standard library only and no work at import time: Fusion's embedded Python imports this module
  (MccFusionArchive.py shares `step_fingerprint` and `placements_hash`), and the CI job installs nothing.
  The CLI runs only under `if __name__ == "__main__":`.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

_NOT_CASE_DIRS = ("brackets", "coupons", "fusion-verify")

FIX_HINT = """\
To refresh the snapshots (also needed after an OCP / cadquery-ocp bump, which changes the STEP bytes):
  1. gh run download <run-id> --pattern 'exports-part-group-*'   (this PR's render run; see the
     bambu-studio skill section 5), merge the result into exports/
  2. write the run id (one line) to exports/ci-run.txt
  3. run tools/fusion-scripts/MccFusionArchive in Autodesk Fusion
  4. commit archive/fusion/ (the .f3d files and manifest.json)"""


def step_fingerprint(path: Path) -> str:
    """sha256 (hex) of a STEP file from its first `\\nDATA;` to EOF, CRLF normalised to LF.

    The HEADER carries a timestamp and differs between runs; the DATA section is byte-identical between
    CI runs of the same geometry (measured 32/32 parts), so it is the geometry's fingerprint.
    """
    data = Path(path).read_bytes().replace(b"\r\n", b"\n")
    idx = data.find(b"\nDATA;")
    if idx < 0:
        raise ValueError(f"no DATA section in {path}")
    return hashlib.sha256(data[idx:]).hexdigest()


def placements_hash(brackets_json: Path) -> str:
    """sha256 (hex) of brackets.json, CRLF normalised to LF."""
    return hashlib.sha256(Path(brackets_json).read_bytes().replace(b"\r\n", b"\n")).hexdigest()


def expected_steps(exports: Path, brackets_json: Path) -> set[str]:
    """Repo-relative POSIX paths of every STEP that must be archived."""
    exports = Path(exports)
    out: set[str] = set()
    if exports.is_dir():
        for d in sorted(exports.iterdir()):
            if not d.is_dir() or d.name in _NOT_CASE_DIRS:
                continue
            bases = sorted(d.glob("base*.step"))
            if not bases:
                continue
            for f in bases:
                out.add(f"exports/{d.name}/{f.name}")
            if (d / "lid.step").is_file():
                out.add(f"exports/{d.name}/lid.step")
        # ARCH-4: every bracket STEP on disk, so a part missing from brackets.json is reported too.
        for f in sorted((exports / "brackets").glob("*/*.step")):
            out.add(f"exports/brackets/{f.parent.name}/{f.name}")
    spec = json.loads(Path(brackets_json).read_text(encoding="utf-8"))
    for b in spec["brackets"]:
        for p in b["parts"]:
            out.add(f"exports/brackets/{b['dir']}/{p['step']}.step")
    return out


def check(repo: Path, exports: Path, archive: Path, brackets_json: Path) -> list[str]:
    """Problems found (empty list = the snapshots are up to date)."""
    repo, archive = Path(repo), Path(archive)
    manifest_path = archive / "manifest.json"
    if not manifest_path.is_file():
        return [f"missing manifest: {manifest_path}"]
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    problems: list[str] = []
    if manifest.get("failed"):
        problems.append("manifest records failed designs: " + "; ".join(manifest["failed"]))
    if manifest.get("placements_sha256") != placements_hash(brackets_json):
        problems.append("stale: brackets.json placements changed")
    referenced: set[str] = set()
    for arch in manifest.get("archives", []):
        if not (archive / arch["file"]).is_file():
            problems.append(f"missing archive: {arch['file']}")
        for part in arch.get("parts", []):
            step = part["step"]
            referenced.add(step)
            step_path = repo / step
            if not step_path.is_file():
                msg = f"missing STEP: {step}"
                if msg not in problems:
                    problems.append(msg)
                continue
            if part.get("fingerprint") != step_fingerprint(step_path):
                msg = f"stale: {arch['file']} ({step})"
                if msg not in problems:  # a bracket's arm appears twice in one archive
                    problems.append(msg)
    for step in sorted(expected_steps(exports, brackets_json) - referenced):
        problems.append(f"not archived: {step}")
    return problems


def _archive_counts(archive: Path) -> tuple[int, int]:
    manifest = json.loads((Path(archive) / "manifest.json").read_text(encoding="utf-8"))
    archives = manifest.get("archives", [])
    steps = {p["step"] for a in archives for p in a.get("parts", [])}
    return len(archives), len(steps)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    c = sub.add_parser("check", help="verify archive/fusion against the STEP exports")
    c.add_argument("--repo", default=".")
    c.add_argument("--exports", default="exports")
    c.add_argument("--archive", default="archive/fusion")
    c.add_argument("--brackets", default="tools/fusion-scripts/MccFusionArchive/brackets.json")
    args = ap.parse_args(argv)

    repo = Path(args.repo)

    def rel(p: str) -> Path:
        q = Path(p)
        return q if q.is_absolute() else repo / q

    exports, archive, brackets = rel(args.exports), rel(args.archive), rel(args.brackets)
    problems = check(repo, exports, archive, brackets)
    if problems:
        for p in problems:
            print(p)
        print()
        print(FIX_HINT)
        return 1
    n_arch, n_steps = _archive_counts(archive)
    print(f"archive/fusion is up to date ({n_arch} archives, {n_steps} STEPs)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
