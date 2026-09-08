#!/usr/bin/env python3
"""Compute the next SemVer release tag from Conventional Commits since the last `v*` tag.

Used by `.github/workflows/release.yml` on every push to `main` — there is no manual
`vX.Y.Z` tagging step any more (see CONTRIBUTING.md's rewritten release section). This script:

1. Finds the latest `v*` tag reachable from HEAD (`git describe --tags --abbrev=0 --match 'v*'`).
   Falls back to `v0.0.0` (nothing tagged yet) if none is found.
2. Walks `git log <tag>..HEAD` (or every commit, if step 1 fell back) and classifies each commit
   by its Conventional Commits type + breaking-change marker:
   - `BREAKING CHANGE:`/`BREAKING-CHANGE:` footer, or a `!` before the `:` in the header
     (`feat!:`, `fix(scope)!:`) -> MAJOR
   - `feat` (or `feat(scope)`) -> MINOR
   - anything else (`fix`, `chore`, `docs`, `ci`, ...) -> PATCH
3. Bumps the highest-priority category found (MAJOR > MINOR > PATCH; at least PATCH if there is
   any commit at all) and prints the resulting `vX.Y.Z` to stdout.

If `$GITHUB_OUTPUT` is set (true inside a GitHub Actions step), also appends `version=vX.Y.Z` to
it so a workflow step can read `${{ steps.<id>.outputs.version }}`.

No network access, no tag is created here — this only computes what the *next* tag should be.
`release.yml` is responsible for actually creating it.
"""

from __future__ import annotations

import os
import re
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent

TAG_RE = re.compile(r"^v(\d+)\.(\d+)\.(\d+)$")
# Conventional Commits header: "<type>(<scope>)<!>: <description>"
HEADER_RE = re.compile(r"^(?P<type>[a-zA-Z]+)(\([^)]*\))?(?P<breaking>!)?:\s*.+")
BREAKING_FOOTER_RE = re.compile(r"^BREAKING[ -]CHANGE:", re.MULTILINE)

RECORD_SEP = "\x1e"
FIELD_SEP = "\x1f"


def _git(args: list[str], check: bool = True) -> str:
    proc = subprocess.run(
        ["git", *args], cwd=REPO_ROOT, capture_output=True, text=True, check=False,
    )
    if check and proc.returncode != 0:
        raise SystemExit(f"error: git {' '.join(args)} failed: {proc.stderr.strip()}")
    return proc.stdout.strip()


def latest_tag() -> tuple[int, int, int] | None:
    """Latest `v*` tag reachable from HEAD, or None if there isn't one."""

    proc = subprocess.run(
        ["git", "describe", "--tags", "--abbrev=0", "--match", "v*"],
        cwd=REPO_ROOT, capture_output=True, text=True, check=False,
    )
    if proc.returncode != 0:
        return None  # no v* tag reachable from HEAD — first release
    tag = proc.stdout.strip()
    m = TAG_RE.match(tag)
    if not m:
        return None  # a v*-ish tag exists but isn't strict SemVer — treat as "no baseline"
    return int(m.group(1)), int(m.group(2)), int(m.group(3))


def commits_since(tag_version: tuple[int, int, int] | None) -> list[tuple[str, str]]:
    """Returns [(subject, body), ...] for every commit since `tag_version` (or all of HEAD's
    history if `tag_version` is None — nothing has been tagged yet)."""

    range_arg = "HEAD" if tag_version is None else f"v{tag_version[0]}.{tag_version[1]}.{tag_version[2]}..HEAD"
    out = _git(["log", range_arg, f"--pretty=format:%s{FIELD_SEP}%b{RECORD_SEP}"])
    if not out:
        return []
    records = [r for r in out.split(RECORD_SEP) if r.strip()]
    commits = []
    for r in records:
        parts = r.split(FIELD_SEP, 1)
        subject = parts[0]
        body = parts[1] if len(parts) > 1 else ""
        commits.append((subject.strip(), body.strip()))
    return commits


def classify(subject: str, body: str) -> str:
    """Returns 'major', 'minor', or 'patch' for one commit."""

    if BREAKING_FOOTER_RE.search(body):
        return "major"
    m = HEADER_RE.match(subject)
    if not m:
        return "patch"  # not a recognizable Conventional Commit header — treat conservatively
    if m.group("breaking"):
        return "major"
    if m.group("type").lower() == "feat":
        return "minor"
    return "patch"


def next_version(base: tuple[int, int, int] | None, commits: list[tuple[str, str]]) -> str:
    if base is None:
        base = (0, 0, 0)

    if not commits:
        # Nothing new since the last tag — re-emit the current version unbumped. The caller
        # (release.yml) is responsible for noticing this would re-create an existing tag.
        return f"v{base[0]}.{base[1]}.{base[2]}"

    levels = {classify(subject, body) for subject, body in commits}

    major, minor, patch = base
    if "major" in levels:
        major, minor, patch = major + 1, 0, 0
    elif "minor" in levels:
        minor, patch = minor + 1, 0
        major = major
    else:
        patch = patch + 1

    return f"v{major}.{minor}.{patch}"


def main(argv: list[str] | None = None) -> int:
    base = latest_tag()
    commits = commits_since(base)
    version = next_version(base, commits)

    base_str = f"v{base[0]}.{base[1]}.{base[2]}" if base else "(none)"
    print(f"# baseline tag: {base_str}", file=sys.stderr)
    print(f"# commits since baseline: {len(commits)}", file=sys.stderr)

    print(version)

    github_output = os.environ.get("GITHUB_OUTPUT")
    if github_output:
        with open(github_output, "a", encoding="utf-8") as f:
            f.write(f"version={version}\n")

    return 0


if __name__ == "__main__":
    sys.exit(main())
