"""The runtime's door to the parameter data against the real registry and parameter sets of the repository."""
import glob
import os
import sys
import types
import unittest

from cad.fusion.runtime import expr, paramset, recording, registry
from cad.fusion.runtime.tests import runtime_support as support

CSV = "cad/parameters/constants.csv"
SETS = "cad/parameters/variants/*.json"
ROW_KEYS = ["comment", "fusion", "kind", "name", "unit"]          # every row; cad.params adds the keys of its rows


class RegistryContract(unittest.TestCase):
    def setUp(self):
        root = support.REPO
        files = sorted(f.replace("\\", "/") for f in glob.glob(SETS, root_dir=root))
        self.assertTrue(os.path.isfile(os.path.join(root, "cad", "params.py")))
        self.assertTrue(os.path.isfile(os.path.join(root, *CSV.split("/"))))
        self.assertTrue(files)
        import cad.params
        configurations = []
        for f in files:
            for config in cad.params.parameter_set_configurations(os.path.join(root, *f.split("/"))):
                configurations.append({"id": "%s:%s" % (f, config), "set": {"file": f, "config": config}, "exports": []})
        self.plan = {"registry": {"source": "cad.params", "csv": [CSV], "sets": [SETS]},
                     "configurations": configurations}

    def test_rows(self):
        for in_fusion in (True, False):
            rows = registry.rows(self.plan, support.REPO, minmax_in_fusion=in_fusion)
            self.assertEqual(paramset.check_rows(rows), [])
            self.assertEqual(len(paramset.order_rows(rows)), len(rows))
            for row in rows:
                self.assertTrue(set(ROW_KEYS) <= set(row), row)
                if row["kind"] != "solver":
                    self.assertTrue(row["expression"], row)            # what a builder evaluates its expressions from
                if row["fusion"] is not None:
                    expr.normalise(row["fusion"])
            if not in_fusion:
                self.assertEqual([r["name"] for r in rows if r["fusion"] and ("min(" in r["fusion"]
                                                                              or "max(" in r["fusion"])], [])

    def test_sets_are_total_and_a_document_takes_them(self):
        rows = registry.rows(self.plan, support.REPO)
        ordered = paramset.order_rows(rows)
        sets = [registry.parameter_set(self.plan, support.REPO, c["id"]) for c in self.plan["configurations"]]
        for one in sets:
            self.assertEqual(set(one["values"]), set(sets[0]["values"]))
            self.assertEqual(set(one["suppress"]), set(sets[0]["suppress"]))
            self.assertTrue(all(isinstance(v, bool) for v in one["suppress"].values()))
        document = recording.RecordingDocument("Contract")
        document.add_parameters(ordered, {r["name"]: paramset.initial_text(r, sets[0]["values"]) for r in ordered})
        for one in sets:
            document.modify_parameters(paramset.set_texts(one["values"], rows))

    def test_the_set_files_of_a_plan_and_their_configurations(self):
        found = registry.set_configurations(self.plan, support.REPO)
        self.assertEqual(sorted(found), sorted((c["set"]["file"], c["set"]["config"]) for c in self.plan["configurations"]))
        self.assertGreater(len(found), 8)
        self.assertEqual(registry.set_configurations({"registry": {"source": "inline"}}, support.REPO), [])


class ResetTests(unittest.TestCase):
    def test_reset_clears_the_cache_of_cad_params_when_it_is_loaded(self):
        import cad.params
        params = cad.params
        params.constants()                                              # fill the cache
        self.assertGreater(params._constants_cached.cache_info().currsize, 0)
        registry.reset()
        self.assertEqual(params._constants_cached.cache_info().currsize, 0)

    def test_reset_calls_clear_cache_and_imports_nothing(self):
        calls = []
        stand_in = types.ModuleType("cad.params")
        stand_in.clear_cache = lambda: calls.append("clear_cache")
        original = sys.modules.pop("cad.params", None)
        sys.modules["cad.params"] = stand_in
        try:
            registry.reset()
            self.assertEqual(calls, ["clear_cache"])
            del sys.modules["cad.params"]
            registry.reset()                                            # not loaded: nothing to forget, nothing imported
            self.assertEqual(calls, ["clear_cache"])
            self.assertNotIn("cad.params", sys.modules)
        finally:
            sys.modules.pop("cad.params", None)
            if original is not None:
                sys.modules["cad.params"] = original


if __name__ == "__main__":
    unittest.main()
