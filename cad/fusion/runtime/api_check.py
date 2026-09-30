"""Offline check of the modules that call the Fusion API: every attribute name they use must exist as a member
somewhere in the installed stubs (adsk/core.py, adsk/fusion.py), or be a known Python or runtime name.

It finds a misspelt member without Fusion. It cannot tell whether a member is used on the right class.
Run: python -m cad.fusion.runtime.api_check
"""
import ast
import glob
import json
import os
import re
import sys

FILES = ("fusion_app.py", "fusion_port.py", "capture.py", "testdoc/builder.py", "probe/core_probes.py",
         "host/MccRun/MccRun.py")
FIXTURE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "tests", "fixtures", "adsk_members.json")
KNOWN = frozenset("""
path join dirname abspath isfile isdir exists realpath basename getsize split append add update get items keys values
pop format_exc version executable name modules util spec_from_file_location module_from_spec loader exec_module
monotonic sleep time inf pi tan cos radians unpack_from findall error PortError contextmanager
core fusion adsk __file__ __stdout__ __name__ current_thread main_thread startswith endswith replace lower
job session out_dir checkout args cache app ui log new_design close_documents design doc previous before report
keep_documents _guard __enter__ __exit__ backend sketch z x_is_horizontal along_x along_y point dimension
constrain_along_x constrain_along_y rows parameter_set order_rows initial_text load build_document
BuildFailed stage violations normalise references ExprError ModalBlocked is_z_up FusionDocument _health snapshot
add_parameters export export_archive close measures internal_to_user save_view measure_all _build_fusion
find_checkout run_pending Bridge BridgeRuntime EVENT_ID on_main_thread start stop events
_solid_bodies _solids _component _component_name _plane_ref _item _owner_index _timeline x y
DocumentPort read _ask SCRATCH_PREFIX _refuse_scratch
""".split())


def stub_dir():
    """The adsk stub directory of the newest installed Fusion, or the folder named by MCC_ADSK_STUBS, or None."""
    override = os.environ.get("MCC_ADSK_STUBS")
    if override and os.path.isfile(os.path.join(override, "fusion.py")):
        return override
    root = os.path.expandvars(r"%LOCALAPPDATA%\Autodesk\webdeploy\production")
    hits = glob.glob(os.path.join(root, "*", "Api", "Python", "packages", "adsk"))
    hits = [h for h in hits if os.path.isfile(os.path.join(h, "fusion.py"))]
    return max(hits, key=os.path.getmtime) if hits else None


def stub_members(directory):
    names = {"cast"}
    for module in ("core", "fusion"):
        with open(os.path.join(directory, module + ".py"), encoding="utf-8", errors="replace") as fh:
            text = fh.read()
        names.update(re.findall(r"^\s+def (?:_get_|_set_)?(\w+)\(", text, re.M))
        names.update(re.findall(r"^class (\w+)\(", text, re.M))
        names.update(re.findall(r"^\s+(\w+) = _(?:core|fusion)\.\w+$", text, re.M))
    return names


def scan(runtime_dir, members):
    """{file: [attribute names that are neither in the stubs nor known]}; an empty list means the file is clean."""
    out = {}
    for rel in FILES:
        with open(os.path.join(runtime_dir, *rel.split("/")), encoding="utf-8") as fh:
            tree = ast.parse(fh.read())
        attrs = sorted({n.attr for n in ast.walk(tree) if isinstance(n, ast.Attribute)})
        out[rel] = [a for a in attrs if a not in members and a not in KNOWN]
    return out


def member_line(stub_lines, cls, member):
    """1-based line of `member` (a def, a property getter or an enumeration value) inside `class cls` of a stub file
    given as a list of lines, or None."""
    start = next((i for i, text in enumerate(stub_lines) if re.match(r"class %s\(" % re.escape(cls), text)), None)
    if start is None:
        return None
    for j in range(start + 1, len(stub_lines)):
        if stub_lines[j].startswith("class "):
            break
        if re.match(r"\s+(?:def (?:_get_)?%s\(|%s = _)" % (re.escape(member), re.escape(member)), stub_lines[j]):
            return j + 1
    return None


def check_fixture(directory, members):
    """Entries of the committed fixture ('module:Class.member': line) that the stubs in `directory` do not confirm."""
    stubs, wrong = {}, []
    for key, line in sorted(members.items()):
        module, rest = key.split(":")
        cls, member = rest.split(".")
        if module not in stubs:
            with open(os.path.join(directory, module + ".py"), encoding="utf-8", errors="replace") as fh:
                stubs[module] = fh.read().split("\n")
        found = member_line(stubs[module], cls, member)
        if found != line:
            wrong.append("%s: fixture says line %s, stub has %s" % (key, line, found))
    return wrong


def main():
    directory = stub_dir()
    if directory is None:
        print("no Fusion installation found")
        return 2
    result = scan(os.path.dirname(os.path.abspath(__file__)), stub_members(directory))
    for rel, unknown in result.items():
        print("%-42s %d not in the stubs%s" % (rel, len(unknown), ": " + ", ".join(unknown) if unknown else ""))
    with open(FIXTURE, encoding="utf-8") as fh:
        members = json.load(fh)["members"]
    wrong = check_fixture(directory, members)
    print("%-42s %d of %d entries not confirmed%s" % ("tests/fixtures/adsk_members.json", len(wrong), len(members),
                                                       ": " + "; ".join(wrong) if wrong else ""))
    return 1 if any(result.values()) or wrong else 0


if __name__ == "__main__":
    sys.exit(main())
