"""Line-aware reader for the frozen OpenSCAD sources (transition tool, removed at the cutover).

It does TEXT parsing only for things OpenSCAD cannot tell us:
  * which top-level variables a file defines, in source order, with their line numbers;
  * the right-hand-side source text of each variable (comments stripped);
  * the comments that document each variable.
Every VALUE comes from OpenSCAD itself (see scad_export.py); nothing here evaluates an expression.

Comment attribution rules (constants.scad style: one variable per statement, the statement starts
in column 0, continuation comments are indented under the trailing comment):

  trailing      `//` text on the statement's own lines (after the `;` or between its rows)
  continuation  comment-only lines directly below the statement whose `//` is indented (col > 0),
                contiguous, ended by a blank line, a code line or a column-0 comment
  leading       comment-only lines directly above the statement whose `//` sits in column 0,
                contiguous (no blank line), banner lines ("-----", "Section:") excluded
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path

BANNER = re.compile(r"^\s*(-{5,}|={5,}|Section:|LibFile:|Includes?:)")
DIRECTIVE = re.compile(r"^\s*(include|use)\s*<[^>]*>\s*;?\s*$")


@dataclass
class Comment:
    line: int          # 1-based
    col: int           # 0-based column of the `//`
    text: str          # text after `//`, stripped
    code_before: bool  # True if code precedes the `//` on the same line


@dataclass
class Statement:
    name: str
    rhs: str                       # right-hand side, comments stripped, whitespace collapsed, no `;`
    start: int                     # first line (1-based)
    end: int                       # last line (1-based)
    trailing: list[Comment] = field(default_factory=list)
    continuation: list[Comment] = field(default_factory=list)
    leading: list[Comment] = field(default_factory=list)
    section: str = ""              # nearest preceding "Section:" banner title


def lex(text: str) -> tuple[list[str], dict[int, Comment]]:
    """Return (code_lines, comments).  code_lines[i] is line i+1 with strings kept, comments and
    block comments blanked.  comments maps line -> Comment (line comments only)."""
    code_lines: list[str] = []
    comments: dict[int, Comment] = {}
    in_block = False
    for ln, raw in enumerate(text.split("\n"), start=1):
        out: list[str] = []
        i, n = 0, len(raw)
        in_str = False
        while i < n:
            ch = raw[i]
            if in_block:
                if raw.startswith("*/", i):
                    in_block = False
                    i += 2
                else:
                    i += 1
                continue
            if in_str:
                out.append(ch)
                if ch == "\\" and i + 1 < n:
                    out.append(raw[i + 1])
                    i += 2
                    continue
                if ch == '"':
                    in_str = False
                i += 1
                continue
            if ch == '"':
                in_str = True
                out.append(ch)
                i += 1
                continue
            if raw.startswith("//", i):
                before = "".join(out).strip()
                comments[ln] = Comment(ln, i, raw[i + 2:].strip(), bool(before))
                break
            if raw.startswith("/*", i):
                in_block = True
                i += 2
                continue
            out.append(ch)
            i += 1
        code_lines.append("".join(out))
    return code_lines, comments


def _statement_end(code_lines: list[str], start_idx: int, start_col: int) -> tuple[int, int]:
    """Find the top-level `;` that ends the statement starting at code_lines[start_idx].
    Returns (end_line_idx, end_col)."""
    depth = 0
    in_str = False
    for li in range(start_idx, len(code_lines)):
        line = code_lines[li]
        j = start_col if li == start_idx else 0
        while j < len(line):
            ch = line[j]
            if in_str:
                if ch == "\\":
                    j += 2
                    continue
                if ch == '"':
                    in_str = False
            elif ch == '"':
                in_str = True
            elif ch in "([{":
                depth += 1
            elif ch in ")]}":
                depth -= 1
            elif ch == ";" and depth == 0:
                return li, j
            j += 1
    raise ValueError(f"unterminated statement starting at line {start_idx + 1}")


def read_variables(path: Path, name_re: str = r"[A-Za-z_][A-Za-z0-9_]*") -> list[Statement]:
    """Every column-0 `NAME = expr;` statement of the file, in source order."""
    text = path.read_text(encoding="utf-8")
    code_lines, comments = lex(text)
    starts = re.compile(rf"^({name_re})\s*=")
    out: list[Statement] = []
    section = ""
    for idx, line in enumerate(code_lines):
        ln = idx + 1
        c = comments.get(ln)
        if c is not None and not c.code_before:
            m = re.match(r"^Section:\s*(.+)$", c.text)
            if m:
                section = m.group(1).strip()
        m = starts.match(line)
        if not m:
            continue
        end_idx, end_col = _statement_end(code_lines, idx, m.end())
        rhs_lines = [code_lines[idx][m.end():]] + code_lines[idx + 1:end_idx + 1]
        rhs = " ".join(rhs_lines)
        rhs = rhs[: rhs.rindex(";")] if ";" in rhs else rhs
        rhs = re.sub(r"\s+", " ", rhs).strip()
        st = Statement(name=m.group(1), rhs=rhs, start=ln, end=end_idx + 1, section=section)
        for k in range(st.start, st.end + 1):
            if k in comments:
                st.trailing.append(comments[k])
        # continuation: indented comment-only lines directly below
        k = st.end + 1
        while k in comments and not comments[k].code_before and comments[k].col > 0 \
                and not code_lines[k - 1].strip():
            st.continuation.append(comments[k])
            k += 1
        # leading: column-0 comment-only lines directly above
        k = st.start - 1
        lead: list[Comment] = []
        while k in comments and not comments[k].code_before and comments[k].col == 0 \
                and not code_lines[k - 1].strip():
            lead.insert(0, comments[k])
            k -= 1
        st.leading = [c for c in lead if c.text and not BANNER.match(c.text)]
        out.append(st)
    return out


def comment_text(comments: list[Comment]) -> str:
    return re.sub(r"\s+", " ", " ".join(c.text for c in comments if c.text)).strip()


# ----- device data files ----------------------------------------------------------------------------


@dataclass
class PortSource:
    id: str
    above: list[str]   # comment-only lines directly above the port's first line, in order
    inner: list[str]   # comments on the port's own lines (inside or trailing), in order


@dataclass
class DeviceSource:
    header: list[str]       # the file's leading comment block, rule lines dropped
    size_comment: str       # trailing comment of the ["size", ...] row
    ports: list[PortSource]


def _line_start_depths(code_lines: list[str]) -> list[int]:
    depths, depth, in_str = [], 0, False
    for line in code_lines:
        depths.append(depth)
        j = 0
        while j < len(line):
            ch = line[j]
            if in_str:
                if ch == "\\":
                    j += 2
                    continue
                if ch == '"':
                    in_str = False
            elif ch == '"':
                in_str = True
            elif ch in "([{":
                depth += 1
            elif ch in ")]}":
                depth -= 1
            j += 1
    return depths


def read_device_source(path: Path, var_name: str) -> DeviceSource:
    """Comments of a lib/mcc/devices/<slug>.scad file, attributed to the header, the size row and
    each port row (a port row starts at bracket depth 3 with `[["id", ...`)."""
    text = path.read_text(encoding="utf-8")
    code_lines, comments = lex(text)
    st = next(s for s in read_variables(path, re.escape(var_name)))
    depths = _line_start_depths(code_lines)

    header: list[str] = []
    for ln in range(1, st.start):
        c = comments.get(ln)
        if c is None:
            if code_lines[ln - 1].strip():
                break
            continue
        if c.text.strip("/ ") == "":
            continue
        header.append(c.text)

    size_comment = ""
    starts: list[tuple[int, str]] = []
    for ln in range(st.start, st.end + 1):
        code = code_lines[ln - 1]
        if re.search(r'\[\s*"size"\s*,', code) and ln in comments:
            size_comment = comments[ln].text
        m = re.match(r'\s*\[\s*\[\s*"id"\s*,\s*"([^"]+)"', code)
        if m and depths[ln - 1] == 3:
            starts.append((ln, m.group(1)))

    ports: list[PortSource] = []
    for k, (s, pid) in enumerate(starts):
        limit = (starts[k + 1][0] - 1) if k + 1 < len(starts) else st.end
        code_end = s
        for ln in range(s, limit + 1):
            if code_lines[ln - 1].strip():
                code_end = ln
        inner = [comments[ln].text for ln in range(s, code_end + 1) if ln in comments and comments[ln].text]
        above: list[str] = []
        ln = s - 1
        while ln > st.start and ln in comments and not code_lines[ln - 1].strip():
            above.insert(0, comments[ln].text)
            ln -= 1
        ports.append(PortSource(pid, above, inner))
    return DeviceSource(header, size_comment, ports)
