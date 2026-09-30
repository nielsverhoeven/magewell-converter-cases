"""The build pipeline on the recording backend and on a geometry stand-in: apply, gates, export,
manifest, regression. Everything is written into a temporary copy of the checkout."""
import copy
import json
import os
import shutil
import subprocess
import sys
import tempfile
import types
import unittest

from cad.fusion.runtime import pipeline, inventory, manifest, plan as planmod, registry
from cad.fusion.runtime.recording import RecordingDocument
from cad.fusion.runtime.testdoc import builder as testdoc_builder, expected
from cad.fusion.runtime.tests import runtime_support as support

PLAN = "cad/fusion/runtime/testdoc/plan.json"
CHECKOUT = None
OUT = None


class FakeGeometryDocument(RecordingDocument):
    """Plays Fusion: a recording document that also 'has' solids, analytic measures and dummy export files."""
    backend = "fusion"

    def __init__(self, document, break_health_in=None):
        RecordingDocument.__init__(self, document)
        self.break_health_in, self.computes = break_health_in, 0

    def info(self):
        return dict(RecordingDocument.info(self), backend=self.backend, fusion_version="fake-1")

    def snapshot(self):
        snap = RecordingDocument.snapshot(self)
        snap["backend"] = self.backend
        for c in snap["components"]:
            c["solids"] = 0 if c["name"] == "." else 1
        values = self._values()
        for p in snap["user_parameters"]:
            p["value"] = values.get(p["name"])
        for item in snap["timeline"]:
            if item["kind"] == "sketch":
                item["fully_constrained"] = True
            if item["kind"] == "feature" and item["type"] == "ExtrudeFeature":
                item["parameters"].append({"name": "d9", "role": "TaperAngle", "expression": "0.0 deg"})
        if self.break_health_in is not None and self.computes == self.break_health_in:
            snap["timeline"][2]["health"], snap["timeline"][2]["message"] = "error", "profile lost"
        return snap

    def _values(self):
        out = {}
        for p in self.params:
            text = p["expression"].split()
            try:
                out[p["name"]] = float(text[0])
            except ValueError:
                pass
        return out

    def _hole_suppressed(self):
        return any(i["name"] == "Test_Hole_Cut" and i["suppressed"] for i in self.items)

    def load_recorded(self, raw):
        self.load_inventory(raw)

    def compute(self):
        RecordingDocument.compute(self)
        self.computes += 1

    def measure(self, component):
        return expected.measures(self._values(), self._hole_suppressed())

    def export(self, component, fmt, path, settings):
        with open(path, "w", encoding="utf-8") as fh:
            fh.write("%s %s %r %s\n" % (fmt, component, sorted(self._values().items()), self._hole_suppressed()))
        if fmt == "step":
            return {"units": "mm"}
        return {"units": "mm", "stl_binary": True, "stl_refinement": settings["stl_refinement"],
                "stl_surface_deviation_mm": 0.005, "stl_normal_deviation_rad": 0.087}


IMPLICIT = [{"type": "ExtrudeFeature", "role": "TaperAngle", "expression": "0 deg"}]


def fake_builder_module(doc, raw=None):
    """The pipeline imports the builder by name; on the stand-in the builder fills the document itself."""
    raw = raw or testdoc_builder.RECORDED

    def build_entry(ctx):
        if ctx.backend != "recording":
            doc.load_recorded(raw)
        return raw
    testdoc_builder.build = build_entry


def with_rejoin(name):
    """The recorded test document plus one re-join that refills the hole cut."""
    raw = copy.deepcopy(testdoc_builder.RECORDED)
    at = next(n for n, i in enumerate(raw["items"]) if i["name"] == "Test_Hole_Cut") + 1
    raw["items"].insert(at, {"kind": "feature", "type": "ExtrudeFeature", "name": name, "component": "TestBlock",
                             "expressions": ["TST_WALL"], "within": "Test_Hole_Cut"})
    return raw


class BuildTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.mkdtemp(prefix="mcc-build-")
        global CHECKOUT, OUT
        CHECKOUT = support.make_checkout(cls.tmp)
        OUT = os.path.join(CHECKOUT, "exports", "fusion", "MCC-RuntimeTest")

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.tmp, ignore_errors=True)

    def setUp(self):
        shutil.rmtree(OUT, ignore_errors=True)
        if os.path.exists(self._inv()):
            os.remove(self._inv())
        self.plan = planmod.load(CHECKOUT, PLAN)
        self.addCleanup(lambda: os.path.exists(self._inv()) and os.remove(self._inv()))
        self.addCleanup(setattr, testdoc_builder, "build", testdoc_builder.build)

    def _inv(self):
        return os.path.join(CHECKOUT, "cad", "fusion", "runtime", "testdoc", "inventory.json")

    def commit_inventory(self):
        with open(self._inv(), "w", encoding="utf-8", newline="\n") as fh:
            fh.write(inventory.dumps(testdoc_builder.RECORDED))

    def run_fake(self, run_id, plan=None, **kw):
        doc = FakeGeometryDocument("MCC-RuntimeTest", break_health_in=kw.pop("break_health_in", None))
        fake_builder_module(doc)
        return doc, pipeline.build_document(plan or self.plan, doc, checkout=CHECKOUT, out_dir=os.path.join(OUT, run_id),
                                         run_id=run_id, implicit=IMPLICIT, log=lambda *_: None, **kw)

    def test_recording_backend(self):
        doc = RecordingDocument("MCC-RuntimeTest")
        fake_builder_module(doc)
        m = pipeline.build_document(self.plan, doc, checkout=CHECKOUT, out_dir=os.path.join(OUT, "r0"), run_id="r0",
                                 log=lambda *_: None)
        self.assertEqual(m["result"], "recorded")
        self.assertFalse(os.path.exists(OUT))
        self.assertEqual(m["inventory"]["sha256"], inventory.inventory_hash(testdoc_builder.RECORDED))
        for c in m["configurations"]:
            self.assertTrue(c["gates"]["passed"], c["gates"])
            statuses = {r["gate"]: r["status"] for r in c["gates"]["results"]}
            self.assertEqual(statuses["sketches"], "not_checked")
            self.assertEqual(statuses["names"], "pass")
            self.assertEqual(statuses["dimensions"], "pass")
        # one add, then per configuration exactly one modifyParameters with the whole set
        self.assertEqual([c for c in doc.calls if c[0] == "modify_parameters"], [("modify_parameters", 5)] * 2)
        self.assertEqual(doc.calls[0], ("add_parameters", 9))
        order = [p["name"] for p in doc.params]
        self.assertLess(order.index("TST_WALL"), order.index("TST_PIN_D"))
        self.assertLess(order.index("TST_PIN_D"), order.index("TST_PITCH"))

    def test_complete_run(self):
        self.commit_inventory()
        doc, m = self.run_fake("r1")
        run = os.path.join(OUT, "r1")
        self.assertEqual(m["result"], "complete")
        self.assertEqual(manifest.validate(m), [])
        self.assertFalse(os.path.exists(run + ".partial"))
        with open(os.path.join(run, "manifest.json"), encoding="utf-8") as fh:
            on_disk = json.load(fh)
        self.assertEqual(on_disk["input_digest"], m["input_digest"])
        self.assertEqual(m["aba"], {"checked": True, "passed": True, "a": "runtime-test/a", "b": "runtime-test/b"})
        self.assertEqual(m["inventory"]["committed_sha256"], m["inventory"]["sha256"])
        self.assertEqual(m["regression"]["checked"], False)
        self.assertEqual(m["fusion"]["version"], "fake-1")
        with open(os.path.join(run, "regression.txt"), encoding="utf-8") as fh:
            text = fh.read()
        self.assertIn("runtime-test/b | values 5 | flags set 1 | healthy", text)
        self.assertIn("result: CLEAN, 2 parts", text)
        a, b = m["configurations"]
        self.assertEqual(a["values"]["V_TEST_L"], 60)
        self.assertEqual(a["values"]["V_N_TEST_PINS"], 3)
        self.assertEqual(b["suppress"], {"Test_Hole": True})
        self.assertEqual(b["health"]["counts"]["suppressed"], 2)
        self.assertEqual(b["health"]["problems"], [])
        self.assertEqual(a["gates"]["violations"], [])
        self.assertEqual(m["export_settings"]["formats"], ["step", "stl"])
        self.assertEqual(m["parameters"]["V_TEST_L"], "60 mm")           # the last applied configuration is A
        self.assertEqual(sorted(f["role"] for f in m["files"]), ["audit", "inventory", "log", "report"])
        listed = {f["path"] for c in m["configurations"] for p in c["parts"] for f in p["files"]} \
            | {f["path"] for f in m["files"]} | {"manifest.json"}
        on_disk_files = {os.path.relpath(os.path.join(d, n), run).replace(os.sep, "/")
                         for d, _, names in os.walk(run) for n in names}
        self.assertEqual(listed, on_disk_files)                          # nothing unlisted in the run directory
        self.assertAlmostEqual(a["parts"][0]["volume_mm3"], 17038.672648, places=5)
        self.assertAlmostEqual(b["parts"][0]["volume_mm3"], 28856.548668, places=5)
        self.assertEqual(b["parts"][0]["bbox"]["max"], [80.0, 30.0, 14.0])
        for c in (a, b):
            for f in c["parts"][0]["files"]:
                self.assertEqual(manifest.sha256_file(os.path.join(run, *f["path"].split("/"))), f["sha256"])
        self.assertEqual(sorted(f["path"] for f in a["parts"][0]["files"]),
                         ["runtime-test/block_a.model.stl", "runtime-test/block_a.step"])
        self.assertEqual(m["parameters"]["TST_WALL"], "4 mm")
        self.assertEqual(m["inventory"]["recorded_sha256"], m["inventory"]["sha256"])
        self.assertTrue(os.path.isfile(os.path.join(run, "inventory.json")))

    def test_regression_pass(self):
        self.commit_inventory()
        doc, m = self.run_fake("r1b", regression=True)
        self.assertEqual(m["result"], "complete")
        self.assertTrue(m["regression"]["checked"] and m["regression"]["passed"])
        self.assertEqual([r["id"] for r in m["regression"]["pass2"]], ["runtime-test/b", "runtime-test/a"])
        self.assertEqual(m["regression"]["sets_live_in_one_configuration"], ["Test_Hole"])
        # 2 applies in pass 1, 2 in pass 2, 3 for A-B-A: each is exactly one modifyParameters call
        self.assertEqual(len([c for c in doc.calls if c[0] == "modify_parameters"]), 7)

    def test_subset_or_options_make_a_run_diagnostic(self):
        doc, m = self.run_fake("r1c", configurations=["runtime-test/a"])
        self.assertEqual(m["result"], "diagnostic")
        doc, m = self.run_fake("r1d", diagnostic=True)
        self.assertEqual(m["result"], "diagnostic")

    def test_build_configuration_without_exports(self):
        plan = copy.deepcopy(self.plan)
        plan["registry"]["sets"]["_build"] = copy.deepcopy(plan["registry"]["sets"]["a"])
        plan["configurations"].insert(0, {"id": "_build", "set": {"config": "_build"}, "exports": []})
        plan["build_configuration"] = "_build"
        self.assertEqual(planmod.validate(plan), [])
        self.commit_inventory()
        doc, m = self.run_fake("r1e", plan=plan)
        self.assertEqual(m["result"], "complete")
        self.assertEqual([c["id"] for c in m["configurations"]], ["_build", "runtime-test/a", "runtime-test/b"])
        self.assertEqual(m["aba"]["a"], "runtime-test/a")

    def test_unhealthy_configuration_exports_nothing(self):
        with self.assertRaises(pipeline.BuildFailed) as cm:
            self.run_fake("r2", break_health_in=2)
        self.assertIn("health", " ".join(cm.exception.violations))
        self.assertFalse(os.path.exists(os.path.join(OUT, "r2")))
        self.assertFalse(os.path.exists(os.path.join(OUT, "r2.partial")))

    def test_report_mode_writes_a_diagnostic_run(self):
        doc, m = self.run_fake("r3", break_health_in=2, gates_mode="report")
        self.assertEqual(m["result"], "diagnostic")
        self.assertTrue(os.path.isfile(os.path.join(OUT, "r3", "manifest.json")))

    def test_literal_dimension_fails(self):
        doc = FakeGeometryDocument("MCC-RuntimeTest")
        fake_builder_module(doc)
        with self.assertRaises(pipeline.BuildFailed) as cm:       # no implicit list: the taper angle is a literal
            pipeline.build_document(self.plan, doc, checkout=CHECKOUT, out_dir=os.path.join(OUT, "r4"), run_id="r4",
                                 log=lambda *_: None)
        self.assertIn("literal", " ".join(cm.exception.violations))

    def test_set_not_total(self):
        plan = copy.deepcopy(self.plan)
        del plan["registry"]["sets"]["b"]["values"]["V_TEST_H"]
        with self.assertRaises(pipeline.BuildFailed) as cm:
            self.run_fake("r5", plan=plan)
        self.assertEqual(cm.exception.stage, "sets")

    def test_flag_without_members_and_protected_flag(self):
        plan = copy.deepcopy(self.plan)
        for s in plan["registry"]["sets"].values():
            s["suppress"]["Test_Nothing"] = False
            s["suppress"]["Reserve_TestBay"] = False
        with self.assertRaises(pipeline.BuildFailed) as cm:
            self.run_fake("r6", plan=plan)
        text = " ".join(cm.exception.violations)
        self.assertIn("Test_Nothing has no member", text)
        self.assertIn("Reserve_TestBay names a protected set", text)

    def test_unknown_owner_and_missing_required(self):
        plan = copy.deepcopy(self.plan)
        plan["owners"] = ["Test"]
        plan["required_components"] = ["Reserve_Other"]
        with self.assertRaises(pipeline.BuildFailed) as cm:
            self.run_fake("r7", plan=plan)
        text = " ".join(cm.exception.violations)
        self.assertIn("owner 'Reserve'", text)
        self.assertIn("Reserve_Other is missing", text)

    def test_committed_inventory(self):
        doc, m = self.run_fake("r8a")
        self.assertEqual(m["result"], "diagnostic")                      # no committed inventory: never complete
        self.commit_inventory()
        doc, m = self.run_fake("r8")
        self.assertEqual(m["result"], "complete")
        self.assertEqual(m["inventory"]["committed_sha256"], m["inventory"]["sha256"])
        other = copy.deepcopy(testdoc_builder.RECORDED)
        other["items"][2]["expressions"] = ["V_TEST_H / 2"]
        with open(self._inv(), "w", encoding="utf-8", newline="\n") as fh:
            fh.write(inventory.dumps(other))
        with self.assertRaises(pipeline.BuildFailed) as cm:
            self.run_fake("r9")
        self.assertIn("inventory_committed", " ".join(cm.exception.violations))

    def test_parameter_drift_is_caught(self):
        doc = FakeGeometryDocument("MCC-RuntimeTest")
        fake_builder_module(doc)
        original = doc.snapshot

        def drifted():
            snap = original()
            for p in snap["user_parameters"]:
                if p["name"] == "TST_WALL":
                    p["expression"], p["value"] = "4.5 mm", 4.5          # typed in Fusion, not in git
            snap["user_parameters"].append({"name": "EXTRA", "unit": "mm", "expression": "1 mm", "value": 1.0})
            return snap
        doc.snapshot = drifted
        with self.assertRaises(pipeline.BuildFailed) as cm:
            pipeline.build_document(self.plan, doc, checkout=CHECKOUT, out_dir=os.path.join(OUT, "r10"), run_id="r10",
                                 implicit=IMPLICIT, log=lambda *_: None)
        text = " ".join(cm.exception.violations)
        self.assertIn("TST_WALL: document has '4.5 mm', git has '4 mm'", text)
        self.assertIn("EXTRA is not in the registry", text)

    def test_plan_validation(self):
        bad = copy.deepcopy(self.plan)
        bad["configurations"][1]["exports"][0]["part"] = "block_a"
        bad["builder"]["module"] = "os.path"
        problems = planmod.validate(bad)
        self.assertTrue(any("exported twice" in p for p in problems))
        self.assertTrue(any("under cad.fusion" in p for p in problems))

    def test_plan_keys(self):
        plan = copy.deepcopy(self.plan)
        plan["shared_exceptions"] = [{"builder": "rail.male", "argument": "lock_e", "reason": "coupon ladder"}]
        self.assertEqual(planmod.validate(plan), [])
        for key, value, text in (("shared_exceptions", "rail.male", "shared_exceptions must be a list"),
                                 ("protected_prefix", ["Reserve_"], "unknown key(s): protected_prefix"),
                                 ("document", "SCRATCH-1", "reserved for scratch documents"),
                                 ("inventory", "../elsewhere.json", "inside the checkout"),
                                 ("inputs", ["cad/fusion/replay/**/*.py"], "the replay is no build input")):
            bad = copy.deepcopy(self.plan)
            bad[key] = value
            self.assertTrue(any(text in p for p in planmod.validate(bad)), (key, planmod.validate(bad)))
        bad = copy.deepcopy(self.plan)
        bad["configurations"][0]["overlays"] = []
        bad["configurations"][0]["exports"][0]["export_set"] = "cad"
        bad["configurations"][1]["id"] = "runtime-test/b@cad"
        bad["configurations"][1]["exports"].append("... one more")
        bad["export"]["archives"] = True
        problems = planmod.validate(bad)
        for text in ("unknown key(s): overlays", "unknown key(s): export_set", "'runtime-test/b@cad' is missing",
                     "an export must be an object", "export: unknown key(s): archives"):
            self.assertTrue(any(text in p for p in problems), (text, problems))
        bad = copy.deepcopy(self.plan)
        bad["builder"]["module"] = "cad.fusion.replay.ocp_replay"
        self.assertTrue(any("must not lie under cad.fusion.replay" in p for p in planmod.validate(bad)))
        del plan["inventory"]
        self.assertEqual(planmod.validate(plan), [])
        plan["configurations"][0]["exports"][0]["part"] = "tile-NE8FDP-B"
        self.assertEqual(planmod.validate(plan), [])
        plan["configurations"][1]["exports"][0].update(target="runtime-test", part="TILE-ne8fdp-b")
        self.assertTrue(any("exported twice" in p for p in planmod.validate(plan)))

    def test_only_the_fusion_backend_can_be_complete(self):
        self.commit_inventory()
        doc = FakeGeometryDocument("MCC-RuntimeTest")
        doc.backend = "replay"
        fake_builder_module(doc)
        m = pipeline.build_document(self.plan, doc, checkout=CHECKOUT, out_dir=os.path.join(OUT, "r11"), run_id="r11",
                                 implicit=IMPLICIT, log=lambda *_: None)
        self.assertEqual(m["result"], "diagnostic")
        m["result"] = "complete"
        self.assertIn("only a run of Fusion can be complete", manifest.validate(m))

    def test_forbidden_module(self):
        name = "cad.fusion.replay"
        sys.modules[name] = types.ModuleType(name)
        self.addCleanup(sys.modules.pop, name, None)
        self.commit_inventory()
        doc, m = self.run_fake("r12")                                     # not forbidden unless the caller says so
        self.assertEqual(m["result"], "complete")
        with self.assertRaises(pipeline.BuildFailed) as cm:
            self.run_fake("r13", forbidden_modules=(name,))
        self.assertEqual(cm.exception.stage, "layering")
        self.assertFalse(os.path.exists(os.path.join(OUT, "r13")))

    def test_committed_inventory_can_be_left_out(self):
        other = copy.deepcopy(testdoc_builder.RECORDED)
        other["items"][2]["expressions"] = ["V_TEST_H / 2"]
        with open(self._inv(), "w", encoding="utf-8", newline="\n") as fh:
            fh.write(inventory.dumps(other))
        doc, m = self.run_fake("r14", committed="ignore")
        self.assertEqual(m["result"], "diagnostic")                       # never complete without the committed hash
        self.assertEqual(m["inventory"]["committed_sha256"], None)
        support.write(self._inv(), "{broken")
        with self.assertRaises(pipeline.BuildFailed) as cm:
            self.run_fake("r15")
        self.assertEqual(cm.exception.stage, "inventory")

    def test_rejoin_in_the_set_of_its_cut(self):
        raw = with_rejoin("Test_Hole_Rejoin")
        support.write(self._inv(), inventory.dumps(raw))
        doc = FakeGeometryDocument("MCC-RuntimeTest")
        fake_builder_module(doc, raw)
        m = pipeline.build_document(self.plan, doc, checkout=CHECKOUT, out_dir=os.path.join(OUT, "r16"), run_id="r16",
                                 implicit=IMPLICIT, log=lambda *_: None)
        self.assertEqual(m["result"], "complete")                         # the read-back took "within" from the record
        self.assertEqual(m["inventory"]["recorded_sha256"], inventory.inventory_hash(raw))
        statuses = {r["gate"]: r["status"] for r in m["configurations"][1]["gates"]["results"]}
        self.assertEqual(statuses["rejoin"], "pass")
        with open(os.path.join(OUT, "r16", "inventory.json"), encoding="utf-8") as fh:
            self.assertIn('"within":"Test_Hole_Cut"', fh.read())

    def test_rejoin_outside_the_set_of_its_cut(self):
        raw = with_rejoin("Test_Pin_Rejoin")                              # set b suppresses the cut, not this
        doc = FakeGeometryDocument("MCC-RuntimeTest")
        fake_builder_module(doc, raw)
        with self.assertRaises(pipeline.BuildFailed) as cm:
            pipeline.build_document(self.plan, doc, checkout=CHECKOUT, out_dir=os.path.join(OUT, "r17"), run_id="r17",
                                 implicit=IMPLICIT, log=lambda *_: None)
        self.assertIn("rejoin: Test_Pin_Rejoin is live while the cut Test_Hole_Cut", " ".join(cm.exception.violations))

    def test_a_loaded_module_that_no_input_pattern_matches_fails_the_build(self):
        rel = "cad/fusion/gen/shared/stub.py"
        name = "cad.fusion.gen.shared.stub"
        sys.modules[name] = types.ModuleType(name)
        sys.modules[name].__file__ = os.path.join(CHECKOUT, *rel.split("/"))
        self.addCleanup(sys.modules.pop, name, None)
        support.write(os.path.join(CHECKOUT, *rel.split("/")), "x = 1\n")
        doc = RecordingDocument("MCC-RuntimeTest")
        fake_builder_module(doc)
        with self.assertRaises(pipeline.BuildFailed) as cm:               # the plan lacks cad/fusion/gen/shared/**
            pipeline.build_document(self.plan, doc, checkout=CHECKOUT, out_dir=os.path.join(OUT, "r19"), run_id="r19",
                                    log=lambda *_: None)
        self.assertEqual(cm.exception.stage, "inputs")
        self.assertEqual(len(cm.exception.violations), 1)
        self.assertIn(rel, cm.exception.violations[0])
        self.assertIn("no input pattern", cm.exception.violations[0])
        plan = copy.deepcopy(self.plan)
        plan["inputs"].append("cad/fusion/gen/shared/**/*.py")
        doc = RecordingDocument("MCC-RuntimeTest")
        fake_builder_module(doc)
        m = pipeline.build_document(plan, doc, checkout=CHECKOUT, out_dir=os.path.join(OUT, "r20"), run_id="r20",
                                    log=lambda *_: None)
        self.assertEqual(m["result"], "recorded")                          # named now: the digest covers it

    def test_the_offline_run_of_the_test_document_is_complete_in_its_inputs(self):
        """A fresh process loads exactly what the run needs, so the real tree shows whether the plan's inputs cover it."""
        code = ("import sys; from cad.fusion.runtime import planrun; "
                "r = planrun.record(%r, %r); print(r['ok'], r.get('stage'), r.get('violations')); sys.exit(0 if r['ok'] else 1)"
                % (support.REPO, PLAN))
        p = subprocess.run([sys.executable, "-B", "-c", code], capture_output=True, text=True, timeout=120, cwd=support.REPO)
        self.assertEqual(p.returncode, 0, p.stdout + p.stderr)

    def test_plan_keys_never_export(self):
        plan = copy.deepcopy(self.plan)
        self.assertEqual(plan["never_export"], ["Ghost_", "Reserve_"])
        self.assertEqual(planmod.validate(plan), [])
        plan["configurations"][0]["exports"][0]["component"] = "Reserve_TestBay"
        self.assertTrue(any("runtime-test/a: component Reserve_TestBay starts with a never_export prefix" in p
                            for p in planmod.validate(plan)), planmod.validate(plan))
        plan["configurations"][0]["exports"][0]["component"] = "Ghost_Device"
        self.assertTrue(any("Ghost_Device starts with a never_export prefix" in p for p in planmod.validate(plan)))
        plan["configurations"][0]["exports"][0]["component"] = "TestBlock"
        plan["never_export"] = []
        self.assertEqual(planmod.validate(plan), [])
        del plan["never_export"]
        self.assertEqual(planmod.validate(plan), [])
        for bad in ("Ghost_", [1], [""]):
            plan["never_export"] = bad
            self.assertTrue(any("never_export must be a list" in p for p in planmod.validate(plan)), bad)

    def product_plan(self):
        """The test document's plan re-pointed at the repository's real parameter data, every configuration listed."""
        plan = copy.deepcopy(self.plan)
        plan["registry"] = {"source": "cad.params", "csv": ["cad/parameters/constants.csv"],
                            "sets": ["cad/parameters/variants/*.json"]}
        pairs = registry.set_configurations(plan, support.REPO)
        plan["configurations"] = [{"id": "c%d" % n, "set": {"file": f, "config": c}, "exports": []}
                                  for n, (f, c) in enumerate(pairs)]
        plan["build_configuration"] = "c0"
        plan["aba"] = False
        return plan

    def test_every_configuration_of_a_referenced_set_file_must_be_in_the_plan(self):
        plan = self.product_plan()
        self.assertGreater(len(plan["configurations"]), 8)
        self.assertEqual(planmod.validate(plan, support.REPO), [])
        self.assertEqual(planmod.validate(plan), [])                       # without a checkout the files are not read
        lost = plan["configurations"].pop(3)                               # exported or not, it has to be listed
        problems = planmod.validate(plan, support.REPO)
        self.assertEqual(len(problems), 1, problems)
        self.assertIn("configuration %s of %s is not in configurations" % (lost["set"]["config"], lost["set"]["file"]), problems[0])
        plan["configurations"].insert(3, lost)
        plan["configurations"][3]["exports"] = [{"component": "TestBlock", "target": "x", "part": "y"}]
        self.assertEqual(planmod.validate(plan, support.REPO), [])         # exported is fine as well
        plan["configurations"][3]["set"]["file"] = "cad/parameters/variants/missing.json"
        self.assertTrue(any("cannot read the parameter-set files" in p for p in planmod.validate(plan, support.REPO)))

    def test_a_set_file_that_only_a_configuration_names_counts_as_referenced(self):
        plan = self.product_plan()
        plan["registry"]["sets"] = []
        only = [c for c in plan["configurations"] if c["set"]["file"].endswith("pro-convert-for-ndi-to-hdmi.json")]
        self.assertEqual(len(only), 3)
        plan["configurations"] = only[:2]
        plan["build_configuration"] = only[0]["id"]
        problems = planmod.validate(plan, support.REPO)
        self.assertEqual(len(problems), 1, problems)
        self.assertIn("pro-convert-for-ndi-to-hdmi.json", problems[0])

    def test_an_inventory_the_schema_refuses(self):
        raw = copy.deepcopy(testdoc_builder.RECORDED)
        raw["items"][2]["phase"] = "polish"
        doc = RecordingDocument("MCC-RuntimeTest")
        fake_builder_module(doc, raw)
        with self.assertRaises(pipeline.BuildFailed) as cm:
            pipeline.build_document(self.plan, doc, checkout=CHECKOUT, out_dir=os.path.join(OUT, "r18"), run_id="r18",
                                 log=lambda *_: None)
        self.assertEqual(cm.exception.stage, "inventory")

if __name__ == "__main__":
    unittest.main()
