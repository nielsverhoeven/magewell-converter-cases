"""THE OpenSCAD runner of cad/ (transition tool, issue #76): every harness of every issue goes through it.

    find_openscad()                      the executable: env MCC_OPENSCAD, else the Windows nightly, else PATH
    run_harness(text, defines)           evaluate a harness, return its ECHO lines, warnings and errors (RunResult)
    run_export(text, out_path, defines)  render a harness to a file (format by suffix: .stl .off .svg .dxf .csg .3mf .echo)
    export_2d(text)                      a 2-D harness as SVG contours
    decode(value)                        exact numbers from the lossless echo encoding

The generator's oracle harness (#81) and the parity tools call these functions instead of copying the executable lookup of
scripts/build.py:362-385.  Used by the exporter (#76) and the layout oracle (#77) while `lib/mcc` is the frozen oracle;
removed together with it at the cutover (#86).

Design points
  * OpenSCAD evaluates every value; this module never evaluates OpenSCAD source itself.
  * echo()/str() print 6 significant digits only, so harnesses wrap values in `oracle_enc()` (ENCODER_SCAD, a Python
    string written into every temporary harness: no .scad file is committed); `decode()` turns the strings back into
    exact floats.
  * The executable is located like scripts/build.py does (env MCC_OPENSCAD, the Windows nightly default, then PATH)
    but WITHOUT importing build.py, which issue #80 owns and will change.
"""
from __future__ import annotations

import os
import re
import shutil
import subprocess
import tempfile
from dataclasses import dataclass, field
from fractions import Fraction
from pathlib import Path

REPO_ROOT = Path(os.environ.get("MCC_REPO_ROOT") or Path(__file__).resolve().parents[2])
LIB_DIR = REPO_ROOT / "lib"
WINDOWS_DEFAULT = Path(r"C:\Program Files\OpenSCAD (Nightly)\openscad.com")


# The lossless encoder lives here as a string and is written into every temporary harness: no .scad
# file is added to git (01-ARCH-BRIEF F4; precedent scripts/rail_fit.py:105-107).
ENCODER_SCAD = r"""// Lossless number encoding for OpenSCAD echo output (transition tool, removed at the cutover).
//
// echo() and str() print only 6 significant digits, which is 1e-3 mm at 100+ mm - too coarse to
// prove a Python port equal.  oracle_enc() replaces every number in a value by a string that
// carries the exact IEEE double:
//
//   "#<sign>|<hi>|<ip>|<c1>|<c2>|<c3>|<c4>|<rest>"
//   |v| = (hi*2^19 + ip) + (c1 + (c2 + (c3 + (c4 + rest) / 2^19) / 2^19) / 2^19) / 2^19
//
// Every limb is an integer below 10^6, which echo prints exactly.  `rest` is 0 for every double
// whose lowest set bit is >= 2^-76 (all values of this repository); a decoder must refuse a
// non-zero rest so that a value which does not round-trip fails loudly.
// Strings, booleans and undef pass through unchanged; lists are encoded element by element.

ORACLE_ENC_B = 524288; // 2^19

function oracle_enc_num(v) =
    (v != v) ? "#nan" :
    (abs(v) > 1e308) ? (v < 0 ? "#-inf" : "#+inf") :
    let(
        a  = abs(v),
        hi = floor(a / ORACLE_ENC_B),
        r0 = a - hi * ORACLE_ENC_B,
        ip = floor(r0),
        f0 = r0 - ip,
        m1 = f0 * ORACLE_ENC_B, c1 = floor(m1), f1 = m1 - c1,
        m2 = f1 * ORACLE_ENC_B, c2 = floor(m2), f2 = m2 - c2,
        m3 = f2 * ORACLE_ENC_B, c3 = floor(m3), f3 = m3 - c3,
        m4 = f3 * ORACLE_ENC_B, c4 = floor(m4), f4 = m4 - c4
    )
    str("#", (v < 0 ? "-" : "+"), "|", hi, "|", ip, "|", c1, "|", c2, "|", c3, "|", c4, "|", f4);

function oracle_enc(v) =
    is_undef(v) ? v :
    is_num(v)   ? oracle_enc_num(v) :
    is_list(v)  ? [for (x = v) oracle_enc(x)] :
    v;
"""


class OpenScadError(RuntimeError):
    """OpenSCAD ran but reported an ERROR (assertion failure, parse error, ...)."""

    def __init__(self, message: str, errors: list[str]):
        super().__init__(message)
        self.errors = errors


def find_openscad() -> Path | None:
    env = os.environ.get("MCC_OPENSCAD")
    if env:
        p = Path(env)
        if p.is_file():
            return p
        which = shutil.which(env)
        return Path(which) if which else None
    if WINDOWS_DEFAULT.is_file():
        return WINDOWS_DEFAULT
    which = shutil.which("openscad")
    return Path(which) if which else None


def openscad_version(exe: Path) -> str:
    proc = subprocess.run([str(exe), "--version"], capture_output=True, text=True,
                          encoding="utf-8", errors="replace", check=False)
    text = ((proc.stdout or "") + (proc.stderr or "")).strip()
    return text.splitlines()[-1] if text else "unknown"


# ---------------------------------------------------------------------------------------------
# echo() output grammar:  value := number | "string" | true | false | undef | inf | -inf | nan
#                                  | [ value, value, ... ]
# ---------------------------------------------------------------------------------------------

_NUM = re.compile(r"-?(?:\d+\.?\d*(?:[eE][+-]?\d+)?|\.\d+(?:[eE][+-]?\d+)?)")
_ESC = {"n": "\n", "t": "\t", "r": "\r", '"': '"', "\\": "\\"}


class _Parser:
    def __init__(self, s: str):
        self.s, self.i = s, 0

    def ws(self) -> None:
        while self.i < len(self.s) and self.s[self.i] in " \t":
            self.i += 1

    def value(self):
        self.ws()
        s, i = self.s, self.i
        if s.startswith("[", i):
            self.i += 1
            out: list = []
            self.ws()
            if s.startswith("]", self.i):
                self.i += 1
                return out
            while True:
                out.append(self.value())
                self.ws()
                if s.startswith(",", self.i):
                    self.i += 1
                    continue
                if s.startswith("]", self.i):
                    self.i += 1
                    return out
                raise ValueError(f"bad list at {self.i}: {s[self.i:self.i + 40]!r}")
        if s.startswith('"', i):
            j, buf = i + 1, []
            while True:
                ch = s[j]
                if ch == "\\":
                    nxt = s[j + 1]
                    buf.append(_ESC.get(nxt, nxt))
                    j += 2
                elif ch == '"':
                    self.i = j + 1
                    return "".join(buf)
                else:
                    buf.append(ch)
                    j += 1
        for lit, val in (("true", True), ("false", False), ("undef", None),
                         ("-inf", float("-inf")), ("inf", float("inf")), ("nan", float("nan"))):
            if s.startswith(lit, i):
                self.i += len(lit)
                return val
        m = _NUM.match(s, i)
        if m:
            self.i = m.end()
            txt = m.group(0)
            return float(txt) if any(c in txt for c in ".eE") else int(txt)
        raise ValueError(f"cannot parse echo value at {i}: {s[i:i + 40]!r}")


def parse_echo_line(line: str) -> list:
    """`ECHO: "TAG", "name", [...]` -> ['TAG', 'name', [...]]."""
    body = line.split("ECHO:", 1)[1].strip()
    p = _Parser(body)
    out = [p.value()]
    p.ws()
    while p.i < len(p.s):
        if p.s[p.i] != ",":
            raise ValueError(f"trailing text in echo line: {p.s[p.i:p.i + 40]!r}")
        p.i += 1
        out.append(p.value())
        p.ws()
    return out


_ENC = re.compile(r"#([+-])\|(\d+)\|(\d+)\|(\d+)\|(\d+)\|(\d+)\|(\d+)\|([0-9.eE+-]+)")


def decode_number(s: str) -> float:
    if s == "#nan":
        return float("nan")
    if s in ("#+inf", "#-inf"):
        return float("inf") if s[1] == "+" else float("-inf")
    m = _ENC.fullmatch(s)
    if not m:
        raise ValueError(f"not a lossless-encoded number: {s!r}")
    sign, hi, ip, c1, c2, c3, c4, rest = m.groups()
    if float(rest) != 0.0:
        raise ValueError(f"value does not round-trip (rest={rest}): {s!r}")
    b = 2 ** 19
    frac = (Fraction(int(c1), b) + Fraction(int(c2), b ** 2) + Fraction(int(c3), b ** 3)
            + Fraction(int(c4), b ** 4))
    v = Fraction(int(hi) * b + int(ip)) + frac
    return float(-v if sign == "-" else v)


def decode(value):
    """Recursively turn oracle_enc() strings back into floats (ints stay floats: OpenSCAD has no
    int/float distinction, and 3.0 == 3 in Python)."""
    if isinstance(value, str) and value.startswith("#") and (
            value in ("#nan", "#+inf", "#-inf") or _ENC.fullmatch(value)):
        return decode_number(value)
    if isinstance(value, list):
        return [decode(v) for v in value]
    return value


# ---------------------------------------------------------------------------------------------


@dataclass
class RunResult:
    returncode: int
    echo_lines: list[str] = field(default_factory=list)   # raw `ECHO: ...` lines, unparsed
    warnings: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    stderr: str = ""

    @property
    def ok(self) -> bool:
        return self.returncode == 0 and not self.errors

    def tagged(self, tag: str) -> list[list]:
        """Parsed argument lists (tag removed) of the ECHO lines that start with `"<tag>",`.  Lines of
        the model's own echo() calls (free text, not our grammar) are never parsed."""
        prefix = f'ECHO: "{tag}",'
        return [parse_echo_line(l)[1:] for l in self.echo_lines if l.startswith(prefix)]


def run_harness(harness_text: str, defines: dict[str, str] | None = None, *, exe: Path | None = None,
                lib_dir: Path = LIB_DIR, timeout: int = 600, keep_dir: Path | None = None) -> RunResult:
    """Write `harness_text` to a temp .scad, run OpenSCAD on it with OPENSCADPATH=<lib_dir>, parse
    every ECHO line.  `defines` become -D name=value (value is an OpenSCAD expression)."""
    exe = exe or find_openscad()
    if exe is None:
        raise FileNotFoundError("OpenSCAD not found (set MCC_OPENSCAD, install the nightly or put "
                                "openscad on PATH)")
    with tempfile.TemporaryDirectory(prefix="mcc_scad_") as tmp:
        tmpdir = Path(tmp)
        scad = tmpdir / "harness.scad"
        scad.write_text(harness_text, encoding="utf-8", newline="\n")
        out = tmpdir / "out.echo"
        cmd = [str(exe), "--backend=Manifold"]
        for k, v in (defines or {}).items():
            cmd += ["-D", f"{k}={v}"]
        cmd += ["-o", str(out), str(scad)]
        env = dict(os.environ)
        env["OPENSCADPATH"] = str(lib_dir)
        proc = subprocess.run(cmd, cwd=tmpdir, env=env, capture_output=True, text=True,
                              encoding="utf-8", errors="replace", timeout=timeout, check=False)
        stderr = (proc.stderr or "") + (proc.stdout or "")
        echo_text = out.read_text(encoding="utf-8", errors="replace") if out.is_file() else ""
        if not echo_text.strip():                       # some builds print ECHO lines on stderr
            echo_text = "\n".join(l for l in stderr.splitlines() if l.startswith("ECHO:"))
        if keep_dir is not None:
            keep_dir.mkdir(parents=True, exist_ok=True)
            shutil.copy(scad, keep_dir / "harness.scad")
            (keep_dir / "out.echo").write_text(echo_text, encoding="utf-8")
    res = RunResult(returncode=proc.returncode, stderr=stderr)
    res.echo_lines = [l for l in echo_text.splitlines() if l.startswith("ECHO:")]
    for line in stderr.splitlines():
        if line.startswith("WARNING:"):
            res.warnings.append(line)
        elif line.startswith("ERROR:"):
            res.errors.append(line)
    return res


def run_export(harness_text: str, out_path: Path, defines: dict[str, str] | None = None, *, exe: Path | None = None,
               lib_dir: Path = LIB_DIR, timeout: int = 600) -> RunResult:
    """Run OpenSCAD on `harness_text` (written to a temporary .scad, OPENSCADPATH=<lib_dir>, --backend=Manifold) and export
    the top-level geometry to `out_path`; the suffix selects the format (.stl, .off, .svg, .dxf, .csg, .3mf, .echo).
    `defines` become -D name=value.  Returns the RunResult (return code, ECHO lines, warnings, errors); the caller checks
    `ok` and that `out_path` exists."""
    exe = exe or find_openscad()
    if exe is None:
        raise FileNotFoundError("OpenSCAD not found (set MCC_OPENSCAD, install the nightly or put openscad on PATH)")
    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="mcc_scad_") as tmp:
        scad = Path(tmp) / "harness.scad"
        scad.write_text(harness_text, encoding="utf-8", newline="\n")
        cmd = [str(exe), "--backend=Manifold"]
        for k, v in (defines or {}).items():
            cmd += ["-D", f"{k}={v}"]
        cmd += ["-o", str(out_path), str(scad)]
        env = dict(os.environ)
        env["OPENSCADPATH"] = str(lib_dir)
        proc = subprocess.run(cmd, cwd=tmp, env=env, capture_output=True, text=True, encoding="utf-8", errors="replace",
                              timeout=timeout, check=False)
    text = (proc.stderr or "") + (proc.stdout or "")
    res = RunResult(returncode=proc.returncode, stderr=text)
    res.echo_lines = [l for l in text.splitlines() if l.startswith("ECHO:")]
    res.warnings = [l for l in text.splitlines() if l.startswith("WARNING:")]
    res.errors = [l for l in text.splitlines() if l.startswith("ERROR:")]
    return res


def export_2d(harness_text: str, *, exe: Path | None = None, lib_dir: Path = LIB_DIR, timeout: int = 300) -> list[list[tuple[float, float]]]:
    """Run a harness whose top-level object is 2-D, export it as SVG and return its contours as lists of
    (x, y) vertices.  SVG carries 6 significant digits, so a caller compares with about 1e-4 mm."""
    with tempfile.TemporaryDirectory(prefix="mcc_scad_") as tmp:
        out = Path(tmp) / "out.svg"
        res = run_export(harness_text, out, exe=exe, lib_dir=lib_dir, timeout=timeout)
        if not res.ok or not out.is_file():
            raise OpenScadError("OpenSCAD SVG export failed: " + res.stderr[-400:], res.errors)
        svg = out.read_text(encoding="utf-8")
    number = r"-?\d+(?:\.\d+)?(?:e[-+]?\d+)?"
    contours = []
    for path in re.findall(r'd="([^"]+)"', svg):
        for sub in path.split("M")[1:]:
            contours.append([(float(a), float(b)) for a, b in re.findall(rf"({number}),({number})", sub)])
    return contours


def assertion_code(error_line: str) -> str | None:
    """`ERROR: Assertion '...' failed: mcc: T1-43 fan switch ...` -> 'T1-43' (first T1-xx[.y] id)."""
    m = re.search(r"\b(T1-\d+(?:\.\d+)?[a-z]?(?:\([a-z]\))?)", error_line)
    return m.group(1) if m else None
