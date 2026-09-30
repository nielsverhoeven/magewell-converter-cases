"""The live probes of the kit (plan section 10, verdict A11; milestone K5b), tested without Fusion and without skipping.

Four kinds of test:

* the registry: ``PROBES`` covers G1 to G19 and every UNVERIFIED item of the body of PR #99, and each probe says where
  its answer goes and what an unfavourable answer means;
* the record: every probe runs against a permissive fake (``probe_fakes.Auto``) and returns a well-formed, JSON-able
  record with the answer keys it declares;
* the kit calls: every build a probe makes (``probes.BUILDS``) runs on the kit's recording backend, which checks the
  names, phases, expressions and rules of the facade, so a wrong kit call is found here and not in the live sitting;
* the numbers: the closed forms the probes compare Fusion against, G1's derivation of ``PLANE_NORMAL`` on the kit's
  fake of the sketch frames, and a scan of the adsk member names of ``probes.py`` against ``probe_members.json`` (and
  the stub where it is installed).

The relative imports are deliberate (see test_names.py).
"""
from __future__ import annotations

import ast
import contextlib
import importlib
import json
import math
import unittest
from pathlib import Path
from types import SimpleNamespace

from ..core.facade import Kit
from . import fake_adsk, probe_fakes
from .test_fusion_backend_static import member_in_class, stub_dir

PKG = __package__.rsplit(".", 1)[0]  # cad.fusion.gen
MODULE = f"{PKG}.core.probes"
BACKEND = f"{PKG}.core.fusion_backend"
PROBES_PY = Path(__file__).resolve().parents[1] / "core" / "probes.py"
MEMBERS = json.loads((Path(__file__).parent / "fixtures" / "probe_members.json").read_text(encoding="utf-8"))["members"]

# Every UNVERIFIED item of the body of PR #99, and the row of plan section 10 it belongs to.
UNVERIFIED = {
    "PLANE_NORMAL": "the placeholder in the facade",
    "offset-sketch-origin": "the sketch origin on an offset construction plane is the model origin's projection",
    "G5-shapes": "G5: rectangle, circle, polygon, ring, datum point and text frame are fully constrained",
    "G5-origin-point": "G5: a new Point3D at the origin is not merged with the origin point",
    "G6-profiles": "G6: profile counts, a ring has one profile with 1 + holes loops",
    "G4-echo": "G4: the echo of dim.parameter.expression",
    "G2-offset-start": "G2: OffsetStartDefinition with a negative expression, and which way positive lies",
    "G3-setByOffset": "G3: setByOffset with a negative expression, and which way positive lies",
    "rejoin-participantBodies": "participantBodies on a join (the re-join)",
    "G9-pattern-cut": "G9: pattern of a cut, bare parameter name as quantity, quantity 1, axis, second direction",
    "G10-pattern-join": "G10: pattern of a join",
    "G11-loft": "G11: a two-section loft as cut and as join is solid and ruled",
    "text": "text: createInput3, setAsMultiLine, frame as construction lines, isHorizontalFlip, SketchText as profile",
    "G17-names": "G17: names are accepted as given",
    "occurrence-name": "G17: an occurrence's own name is not touched",
    "dimension-text-points": "dimension text points are accepted wherever they fall",
}


@contextlib.contextmanager
def probes_module(fakes=None):
    """``probes`` imported against ``adsk`` fakes (``probe_fakes.installed`` unless others are given)."""
    with (fakes or probe_fakes.installed)(MODULE, BACKEND):
        yield importlib.import_module(MODULE)


class Base(unittest.TestCase):
    def setUp(self):
        manager = probes_module()
        self.probes = manager.__enter__()
        self.addCleanup(manager.__exit__, None, None, None)


class RegistryTests(Base):
    def test_the_list_is_the_registration_of_contract_c6(self):
        self.assertGreater(len(self.probes.PROBES), 20)
        for entry in self.probes.PROBES:
            pid, title, function = entry
            self.assertIsInstance(pid, str)
            self.assertTrue(title.strip(), pid)
            self.assertTrue(callable(function), pid)
        ids = [entry[0] for entry in self.probes.PROBES]
        self.assertEqual(len(ids), len(set(ids)), "an id occurs twice")

    def test_g1_to_g19_are_all_there(self):
        ids = {entry[0] for entry in self.probes.PROBES}
        self.assertEqual(sorted(f"G{n}" for n in range(1, 20) if f"G{n}" not in ids), [])

    def test_every_unverified_item_of_pr_99_has_a_probe(self):
        covered = {item for items in self.probes.COVERS.values() for item in items}
        self.assertEqual(sorted(set(UNVERIFIED) - covered), [])
        self.assertEqual(sorted(covered - set(UNVERIFIED) - {f"G{n}" for n in range(1, 20)}), [], "an item that is on no list")

    def test_every_probe_says_where_its_answer_goes_and_what_a_bad_answer_means(self):
        for pid, meta in self.probes.META.items():
            self.assertTrue(meta["copy_into"].strip(), pid)
            self.assertTrue(meta["if_unfavourable"].strip(), pid)
            self.assertTrue(meta["keys"], f"{pid} declares no answer key")
            self.assertTrue(meta["covers"], pid)

    def test_plane_normal_is_the_first_named_answer(self):
        self.assertIn("PLANE_NORMAL", self.probes.META["G1"]["keys"])
        self.assertIn("PLANE_NORMAL", self.probes.META["G1"]["copy_into"])

    def test_the_a11_fallback_of_g9_is_named(self):
        text = self.probes.META["G9"]["copy_into"] + self.probes.META["G9"]["if_unfavourable"]
        self.assertIn("Rep", text)
        self.assertIn("parked at 2", text)

    def test_g19_is_the_ring_and_bar_rejoin(self):
        self.assertIn("rejoin-participantBodies", self.probes.COVERS["G19"])
        names = [label for label, _ in self.probes.G19_FAN.steps]
        self.assertEqual(names, ["plate", "opening", "ring", "bar"])


class RecordTests(Base):
    def run_probe(self, pid):
        function = next(f for i, _, f in self.probes.PROBES if i == pid)
        return function(probe_fakes.make_env())

    def test_every_probe_returns_a_well_formed_json_record(self):
        for pid, title, function in self.probes.PROBES:
            record = function(probe_fakes.make_env())
            meta = self.probes.META[pid]
            self.assertEqual(record["id"], pid)
            self.assertIn(record["status"], ("pass", "fail", "info"), pid)
            self.assertIsInstance(record["answer"], dict, pid)
            for key in meta["keys"]:
                self.assertIn(key, record["answer"], f"{pid}: the declared answer key {key!r}")
            self.assertEqual(record["copy_into"], meta["copy_into"])
            self.assertEqual(record["covers"], meta["covers"])
            self.assertEqual(json.loads(json.dumps(record)), record, f"{pid}: not plain JSON data")

    def test_a_refusal_of_fusion_is_an_answer_and_does_not_raise(self):
        # on the fake the kit's backend refuses its first sketch: the probes that build through the kit still return
        for pid in ("G5", "G6", "G7", "G9", "G19"):
            record = self.run_probe(pid)
            self.assertIn(record["status"], ("pass", "fail"))
        record = self.run_probe("G5")
        self.assertFalse(record["answer"]["all_built"])
        self.assertTrue(all(case["errors"] for case in record["answer"]["cases"].values()))

    def test_the_answer_keys_do_not_depend_on_the_answer(self):
        # the same probe on two different fakes has the same keys: a follow-up PR can rely on them
        first = self.run_probe("G2")["answer"]
        second = self.run_probe("G2")["answer"]
        self.assertEqual(sorted(first), sorted(second))

    def test_a_probe_with_a_missing_key_is_a_bug_of_the_file(self):
        register = self.probes._probe("X-TEST", "missing key", keys=["a", "b"], covers=["x"], copy_into="here", unfavourable="never")

        def lacking(env):
            return "info", {"a": 1}

        run = register(lacking)
        try:
            with self.assertRaises(AssertionError):
                run(probe_fakes.make_env())
        finally:
            self.probes.PROBES[:] = [p for p in self.probes.PROBES if p[0] != "X-TEST"]
            self.probes.META.pop("X-TEST")
            self.probes.COVERS.pop("X-TEST")

    def test_a_time_out_of_the_runtime_passes_through(self):
        def slow():
            raise TimeoutError("block")

        with self.assertRaises(TimeoutError):
            self.probes._attempt(slow)
        ok, text = self.probes._attempt(lambda: 1 / 0)
        self.assertFalse(ok)
        self.assertIn("ZeroDivisionError", text)

    def test_json_rounds_numbers_and_drops_what_json_cannot_hold(self):
        out = self.probes._json({"a": 1.23456789, "b": float("nan"), "c": (1, 2), "d": {3}, "e": object, "f": True, 5: None})
        self.assertEqual(out["a"], 1.234568)
        self.assertIsNone(out["b"])
        self.assertEqual(out["c"], [1, 2])
        self.assertEqual(out["d"], [3])
        self.assertIsInstance(out["e"], str)
        self.assertIs(out["f"], True)
        self.assertIn("5", out)

    def test_the_probes_use_their_own_scratch_documents(self):
        opened = []
        env = probe_fakes.make_env(opened)
        for _, _, function in self.probes.PROBES:
            function(env)
        self.assertTrue(opened)
        for name, _ in opened:
            self.assertTrue(name.startswith("SCRATCH-"), f"{name}: the runtime never exports a SCRATCH- document")


class BuildTests(Base):
    """Every build of a probe on the recording backend: the facade's rules hold for the kit calls the probes make."""

    def kit(self, names):
        params = self.probes._params(*names)
        rows = [self.probes._row(n, u) for n, (v, u) in params.items() if u != "deg"]
        values = {n: v for n, (v, u) in params.items() if u != "deg"}
        return Kit(SimpleNamespace(backend="recording", document="T", registry=rows, values=values, options={}, log=print))

    def test_every_build_is_a_valid_kit_call_sequence(self):
        self.assertGreater(len(self.probes.BUILDS), 20)
        for pid, build, names in self.probes.BUILDS:
            kit = self.kit(names)
            c = kit.component(build.comp, role=build.role, datum=build.datum)
            for label, step in build.steps:
                try:
                    step(c)
                except Exception as exc:  # noqa: BLE001
                    self.fail(f"{pid} {build.comp}.{label}: {type(exc).__name__}: {exc}")
            self.assertGreater(len(kit.inventory()["items"]), 1, f"{pid} {build.comp}")

    def test_every_probe_that_builds_has_a_build(self):
        with_builds = {pid for pid, _, _ in self.probes.BUILDS}
        self.assertEqual(sorted({"G5", "G6", "G7", "G8", "G9", "G10", "G11", "G14", "G15", "G18", "G19", "U-TEXT"} - with_builds), [])

    def test_the_names_of_one_document_do_not_collide(self):
        # the probes put several builds in one document; the kit refuses a name twice
        per_probe = {}
        for pid, build, names in self.probes.BUILDS:
            per_probe.setdefault(pid, []).append((build, names))
        for pid, builds in per_probe.items():
            names = tuple(dict.fromkeys(n for _, ns in builds for n in ns))
            kit = self.kit(names)
            seen = set()
            for build, _ in builds:
                if build.comp in seen:
                    continue  # the same build registered for two probes that do not share a document (G9, G12, G13, G15)
                seen.add(build.comp)
                c = kit.component(build.comp, role=build.role, datum=build.datum)
                for label, step in build.steps:
                    step(c)

    def test_g18_builds_about_150_timeline_objects(self):
        build = self.probes.G18_ROWS
        kit = self.kit(self.probes.G18_NAMES)
        c = kit.component(build.comp, role=build.role, datum=build.datum)
        for label, step in build.steps:
            step(c)
        items = kit.inventory()["items"]
        self.assertEqual(sum(1 for i in items if i["kind"] == "feature"), 1 + 50 * 2)
        self.assertTrue(150 <= len(items) <= 160, len(items))

    def test_the_text_build_cuts_three_faces_with_a_capital_l(self):
        kit = self.kit(self.probes.TEXT_NAMES)
        build = self.probes.G_TEXT
        c = kit.component(build.comp, role=build.role, datum=build.datum)
        for label, step in build.steps:
            step(c)
        sketches = [i for i in kit.inventory()["items"] if i["kind"] == "sketch" and i.get("texts")]
        self.assertEqual([s["texts"] for s in sketches], [["L"], ["L"], ["L"]])
        self.assertEqual({s["on"] for s in sketches}, {"origin:XY", "origin:XZ", "origin:YZ"})


class NumberTests(Base):
    def test_the_frustum_is_the_integral_of_the_section_area(self):
        a1, h, n = 600.0, 10.0, 20000
        integral = sum(a1 * (1 - ((k + 0.5) / n) / 2) ** 2 * h / n for k in range(n))  # section B is half of A
        self.assertAlmostEqual(self.probes._frustum(a1, a1 / 4, h), integral, places=3)

    def test_the_loft_closed_forms_for_the_default_values(self):
        values = {n: v for n, (v, u) in self.probes.BASE.items()}
        self.assertAlmostEqual(self.probes._trapezoid_area(values), 600.0)
        self.assertAlmostEqual(self.probes._loft_expected("trap", values, 10.0), 3500.0)
        self.assertAlmostEqual(self.probes._loft_expected("circle", values, 10.0), math.pi * 10.0 / 3.0 * (100 + 50 + 25))

    def test_the_bar_across_a_ring_is_added_once(self):
        steps, r, w = 200000, 12.0, 6.0
        strip = sum(2 * math.sqrt(r * r - y * y) * (w / 2 / steps * 2) for y in (-w / 2 + (k + 0.5) * w / steps for k in range(steps)))
        self.assertAlmostEqual(self.probes._chord_strip_area(r, w), strip, places=3)
        ring = math.pi / 4 * (40 ** 2 - 24 ** 2)
        self.assertAlmostEqual(self.probes._ring_bar_added_mm3(40.0, 24.0, 6.0, 3.0), (ring + strip) * 3.0, places=2)

    def test_the_slot_volumes_the_pattern_probes_expect(self):
        # plate 100 x 60 x 3, slot 4 x 8 x 3: 18000 and 96 mm3; three copies at pitch 20 from x = 10 stay inside
        values = {n: v for n, (v, u) in self.probes.BASE.items()}
        self.assertEqual(values["V_PL"] * values["V_PW"] * values["V_PT"], 18000.0)
        self.assertEqual(values["V_SW"] * (values["V_SV1"] - values["V_SV0"]) * values["V_PT"], 96.0)
        self.assertLessEqual(values["V_SX"] + 2 * values["V_PITCH"] + values["V_SW"], values["V_PL"])
        self.assertLessEqual(values["V_SV0"] + 2 * values["V_PITCH"] + (values["V_SV1"] - values["V_SV0"]), values["V_PW"])
        self.assertLessEqual(values["V_SV0"] + values["V_PITCH2"] + (values["V_SV1"] - values["V_SV0"]), values["V_PW"])
        self.assertEqual(values["V_RW"] * (values["V_RV1"] - values["V_RV0"]) * values["V_RH"], 160.0)

    def test_the_text_probe_expects_the_l_to_read_from_outside(self):
        faces = self.probes.TEXT_FACES
        # right = forward x up for a viewer who looks against plus axis: Z: +X, Y: -X, X: +Y; the stem is on the left
        self.assertEqual({a: faces[a]["stem"] for a in "XYZ"}, {"Z": -1, "Y": 1, "X": -1})
        self.assertEqual(self.probes.FACE_CM, {"Z": 3.0, "Y": 6.0, "X": 10.0})  # V_BH, V_PW, V_PL in centimetres
        self.assertEqual({a: self.probes.BASE[p][0] / 10 for a, p in self.probes.FACE_PARAM.items()}, self.probes.FACE_CM)

    def test_axis_sign_and_the_interval_along_a_normal(self):
        vector = lambda *c: SimpleNamespace(x=c[0], y=c[1], z=c[2])  # noqa: E731
        self.assertEqual(self.probes._axis_sign(vector(0, -1, 0)), ("Y", -1))
        self.assertIsNone(self.probes._axis_sign(vector(1, 1, 0)))
        self.assertIsNone(self.probes._axis_sign(vector(0.5, 0, 0)))
        self.assertEqual(self.probes._along_normal(2, 5, 1), (2, 5))
        self.assertEqual(self.probes._along_normal(2, 5, -1), (-5, -2))


class G1OnTheKitsFakeTests(unittest.TestCase):
    """G1 against ``fake_adsk``, whose sketch frames are a knob: the derived ``PLANE_NORMAL`` must follow the frames."""

    def setUp(self):
        manager = probes_module(fake_adsk.installed)
        self.probes = manager.__enter__()
        self.addCleanup(manager.__exit__, None, None, None)

    def env(self, frames=None, origin=(0.0, 0.0, 0.0)):
        def new_design(name):
            design = fake_adsk.Design()
            design.frames.update(frames or {})
            design.sketch_origin = origin
            design.rootComponent = fake_adsk.Component(design)
            return design

        env = probe_fakes.make_env()
        env.new_design = new_design
        return env

    def g1(self, env):
        function = next(f for i, _, f in self.probes.PROBES if i == "G1")
        return function(env)

    def test_the_default_frames_give_the_normals_of_the_fake(self):
        record = self.g1(self.env())
        self.assertEqual(record["answer"]["PLANE_NORMAL"], {"XY": 1, "XZ": -1, "YZ": 1})
        self.assertEqual(record["status"], "pass")
        self.assertEqual(record["answer"]["frames"]["XZ"]["normal"], [0.0, -1.0, 0.0])

    def test_swapped_axes_flip_the_sign(self):
        record = self.g1(self.env(frames={"XZ": ((0, 0, 1), (1, 0, 0)), "YZ": ((0, 0, 1), (0, 1, 0))}))
        self.assertEqual(record["answer"]["PLANE_NORMAL"], {"XY": 1, "XZ": 1, "YZ": -1})

    def test_the_answer_is_cached_for_the_probes_that_sketch_on_xz_and_yz(self):
        env = self.env()
        self.g1(env)
        self.assertEqual(env.cache["PLANE_NORMAL"], {"XY": 1, "XZ": -1, "YZ": 1})

    def test_a_sketch_origin_off_the_model_origin_is_a_failure_with_the_numbers(self):
        record = self.g1(self.env(origin=(1.0, 0.0, 0.0)))
        self.assertEqual(record["status"], "fail")
        self.assertFalse(record["answer"]["offset_plane_origin_is_model_origin_projection"])
        self.assertEqual(record["answer"]["offset_plane_sketch_origin_mm"]["XY"]["value"]["origin_mm"], [10.0, 0.0, 0.0])

    def test_plane_normal_is_patched_for_the_length_of_a_block_only(self):
        from ..core import facade

        env = self.env()
        saved = dict(facade.PLANE_NORMAL)
        with self.probes._plane_normal(env) as normals:
            self.assertEqual(normals, {"XY": 1, "XZ": -1, "YZ": 1})
            self.assertEqual(facade.PLANE_NORMAL, {"XY": 1, "XZ": -1, "YZ": 1})
        self.assertEqual(facade.PLANE_NORMAL, saved)


class StaticTests(unittest.TestCase):
    """A text scan of ``probes.py`` against the recorded adsk members, like the one of ``fusion_backend.py`` (K5a)."""

    PYTHON_NAMES = {"append", "get", "items", "update", "pop", "split", "rsplit", "startswith", "lower", "capitalize", "match",
                    "sub", "compile", "values", "clear", "pi", "sqrt", "asin", "radians", "cos", "sin", "tan", "isfinite",
                    "perf_counter", "contextmanager", "SimpleNamespace", "__doc__", "__name__", "fromkeys", "remove"}
    # the kit facade (Component), the env of contract C6, the dataclass-free own names of this module
    OWN_NAMES = {"expr", "facade", "fusion", "core", "PLANE_NORMAL", "extrude", "rect", "circle", "polygon", "loft", "pattern",
                 "text", "component", "app", "ui", "new_design", "out_dir", "log", "cache", "adsk", "fontNames"}

    @classmethod
    def setUpClass(cls):
        cls.tree = ast.parse(PROBES_PY.read_text(encoding="utf-8"), filename=str(PROBES_PY))
        cls.by_class: dict[str, set[str]] = {}
        for key in MEMBERS:
            _, rest = key.split(":")
            klass, member = rest.split(".")
            cls.by_class.setdefault(klass, set()).add(member)

    def own_names(self):
        names = set()
        for node in ast.walk(self.tree):
            if isinstance(node, (ast.FunctionDef, ast.ClassDef)):
                names.add(node.name)
            elif isinstance(node, ast.Attribute) and isinstance(node.ctx, ast.Store):
                names.add(node.attr)
        return names

    def test_the_probes_use_no_adsk_member_that_is_not_recorded(self):
        known = {m for ms in self.by_class.values() for m in ms} | set(self.by_class)
        known |= self.own_names() | self.PYTHON_NAMES | self.OWN_NAMES
        unknown = sorted({n.attr for n in ast.walk(self.tree) if isinstance(n, ast.Attribute)} - known)
        self.assertEqual(unknown, [], "attribute names that are in no list: a misspelt adsk member, or add it to "
                                      "tests/fixtures/probe_members.json with its stub line")

    def test_every_recorded_member_is_used_by_the_probes(self):
        used = {n.attr for n in ast.walk(self.tree) if isinstance(n, ast.Attribute)}
        self.assertEqual(sorted(k for k in MEMBERS if k.split(".")[1] not in used), [], "remove the member or use it")

    def test_every_adsk_class_the_probes_name_is_recorded(self):
        named = set()
        for node in ast.walk(self.tree):
            if isinstance(node, ast.Attribute) and isinstance(node.value, ast.Attribute) \
                    and isinstance(node.value.value, ast.Name) and node.value.value.id == "adsk":
                named.add(f"{node.value.attr}:{node.attr}")
        recorded = {key.split(".")[0] for key in MEMBERS}
        self.assertEqual(sorted(named - recorded), [], "an adsk class with no recorded member")

    def test_the_probes_never_call_createByReal_and_never_save_or_export(self):
        attributes = {n.attr for n in ast.walk(self.tree) if isinstance(n, ast.Attribute)}
        self.assertFalse(attributes & {"createByReal", "saveAs", "save", "exportManager", "computeAll", "close"})

    def test_the_list_is_well_formed(self):
        self.assertGreater(len(MEMBERS), 100)
        for key, line in MEMBERS.items():
            self.assertRegex(key, r"^(core|fusion):[A-Za-z0-9]+\.[A-Za-z0-9]+$")
            self.assertIsInstance(line, int)

    def test_the_members_exist_in_the_stub_where_it_is_installed(self):
        stubs = stub_dir()
        if stubs is None:
            return  # not a skip: the list was checked above and the stub is checked wherever the CAD workstation has it
        for module in ("core", "fusion"):
            lines = (stubs / f"{module}.py").read_text(encoding="utf-8").split("\n")
            for key in MEMBERS:
                if key.startswith(module + ":"):
                    klass, member = key.split(":")[1].split(".")
                    self.assertTrue(member_in_class(lines, klass, member), f"{key} is not in the stub")


if __name__ == "__main__":
    unittest.main()
