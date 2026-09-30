"""Inventory schema 1: normal form, hash, committed layout, diff, record-only fields."""
import copy
import unittest

from cad.fusion.runtime import inventory

RAW = {"schema": 1, "document": "MCC-RuntimeTest", "items": [
    {"kind": "component", "name": "TestBlock"},
    {"kind": "sketch", "name": "Test_Block_Sketch", "component": "TestBlock", "on": "origin:XY",
     "expressions": ["V_TEST_W", "V_TEST_L"]},
    {"kind": "feature", "type": "ExtrudeFeature", "name": "Test_Block_Extrude", "component": "TestBlock",
     "expressions": ["V_TEST_H"]},
    {"kind": "plane", "name": "Test_Pin_Plane", "component": "TestBlock", "on": "origin:XY",
     "expressions": ["V_TEST_H"]},
    {"kind": "sketch", "name": "Test_Hole_Sketch", "component": "TestBlock", "on": "origin:XY",
     "expressions": ["V_TEST_HOLE_D", "V_TEST_L/2", "V_TEST_W - TST_WALL - V_TEST_HOLE_D/2"]},
    {"kind": "feature", "type": "ExtrudeFeature", "name": "Test_Hole_Cut", "component": "TestBlock"},
]}
REJOIN = {"kind": "feature", "type": "ExtrudeFeature", "name": "Test_Hole_Rejoin", "component": "TestBlock",
          "expressions": ["TST_WALL"], "within": "Test_Hole_Cut"}
THREAD = {"kind": "feature", "type": "ThreadFeature", "name": "Test_Thread_ModeledThread",
          "component": "TestBlock", "phase": "enhance"}


def snapshot_of(raw):
    """What a read-back of a design built from `raw` looks like: no record-only field."""
    timeline = []
    for n, item in enumerate(raw["items"]):
        entry = {"index": n, "kind": item["kind"], "name": item["name"], "component": item.get("component") or ".",
                 "parameters": [{"expression": e} for e in item.get("expressions") or []]}
        for key in ("type", "on", "texts"):
            if key in item:
                entry[key] = item[key]
        timeline.append(entry)
    return {"document": raw["document"], "timeline": timeline}


class InventoryTests(unittest.TestCase):
    def test_hash_is_stable_under_formatting(self):
        readback = {"schema": 1, "document": "MCC-RuntimeTest", "items": [dict(i) for i in RAW["items"]]}
        readback["items"][1]["expressions"] = ["V_TEST_L", "V_TEST_W", "0 deg"]          # other order, implicit literal
        readback["items"][4]["expressions"] = ["V_TEST_L / 2", "V_TEST_HOLE_D",
                                               "V_TEST_W - TST_WALL - V_TEST_HOLE_D / 2"]
        readback["items"][5]["expressions"] = ["0.0 deg"]
        self.assertEqual(inventory.inventory_hash(RAW), inventory.inventory_hash(readback))
        self.assertEqual(inventory.diff(RAW, readback), [])

    def test_round_trip_and_line_format(self):
        text = inventory.dumps(RAW)
        self.assertEqual(inventory.inventory_hash(inventory.loads(text)), inventory.inventory_hash(RAW))
        self.assertEqual(text.count("\n"), len(RAW["items"]) + 6)
        self.assertNotIn("\r", text)
        self.assertEqual(inventory.inventory_hash(inventory.loads(text.replace("\n", "\r\n"))),
                         inventory.inventory_hash(RAW))

    def test_changes_change_the_hash(self):
        for mutate in (lambda d: d["items"][2].__setitem__("expressions", ["V_TEST_H / 2"]),
                       lambda d: d["items"][2].__setitem__("name", "Test_Block_Extrude2"),
                       lambda d: d["items"][2].__setitem__("type", "RevolveFeature"),
                       lambda d: d["items"][1].__setitem__("on", "origin:XZ"),
                       lambda d: d["items"].reverse(),
                       lambda d: d["items"].pop()):
            other = copy.deepcopy(RAW)
            mutate(other)
            self.assertNotEqual(inventory.inventory_hash(RAW), inventory.inventory_hash(other))
            self.assertTrue(inventory.diff(RAW, other))

    def test_rejects(self):
        bad = copy.deepcopy(RAW)
        bad["items"].append(dict(bad["items"][2]))
        with self.assertRaises(inventory.InventoryError):
            inventory.normalise(bad)
        bad = copy.deepcopy(RAW)
        del bad["items"][2]["type"]
        with self.assertRaises(inventory.InventoryError):
            inventory.normalise(bad)

    def test_suppress_members(self):
        self.assertEqual(inventory.suppress_members(RAW, "Test_Hole"), ["Test_Hole_Sketch", "Test_Hole_Cut"])
        self.assertEqual(inventory.suppress_members(RAW, "Test_Nothing"), [])

    def test_record_only_fields(self):
        raw = copy.deepcopy(RAW)
        raw["items"] += [dict(REJOIN), dict(THREAD)]
        inv = inventory.normalise(raw)
        self.assertEqual(inv["items"][-2]["within"], "Test_Hole_Cut")
        self.assertEqual(inv["items"][-1], {"kind": "feature", "name": "Test_Thread_ModeledThread",
                                            "component": "TestBlock", "type": "ThreadFeature", "expressions": [],
                                            "phase": "enhance"})
        self.assertEqual(inventory.annotations(raw), {"Test_Hole_Rejoin": {"within": "Test_Hole_Cut"},
                                                      "Test_Thread_ModeledThread": {"phase": "enhance"}})
        self.assertEqual(inventory.annotations(RAW), {})
        self.assertEqual(inventory.loads(inventory.dumps(raw)), inv)             # the committed layout keeps them
        for field, other in (("within", "Test_Block_Extrude"), ("phase", None)):
            changed = copy.deepcopy(raw)
            target = changed["items"][-2] if field == "within" else changed["items"][-1]
            target[field] = other
            self.assertNotEqual(inventory.inventory_hash(changed), inventory.inventory_hash(raw))
            self.assertTrue(inventory.diff(changed, raw))

    def test_strip_phase(self):
        raw = copy.deepcopy(RAW)
        raw["items"] += [dict(REJOIN), dict(THREAD)]
        plain = copy.deepcopy(RAW)
        plain["items"].append(dict(REJOIN))
        self.assertEqual(inventory.inventory_hash(inventory.strip_phase(raw, "enhance")),
                         inventory.inventory_hash(plain))

    def test_read_back_takes_record_only_fields_from_the_record(self):
        raw = copy.deepcopy(RAW)
        raw["items"] += [dict(REJOIN), dict(THREAD)]
        snapshot = snapshot_of(raw)
        self.assertNotEqual(inventory.inventory_hash(inventory.from_snapshot(snapshot)), inventory.inventory_hash(raw))
        read_back = inventory.from_snapshot(snapshot, inventory.annotations(raw))
        self.assertEqual(inventory.inventory_hash(read_back), inventory.inventory_hash(raw))
        del snapshot["timeline"][-1]                                             # the design lacks the thread
        self.assertTrue(inventory.diff(raw, inventory.from_snapshot(snapshot, inventory.annotations(raw))))

    def test_record_only_fields_are_checked(self):
        feature = {"kind": "feature", "type": "ExtrudeFeature", "name": "Test_Other_Rejoin", "component": "TestBlock"}
        for extra in (dict(feature, within="Test_Nothing_Cut"),                   # no such item
                      dict(feature, within="Test_Block_Sketch"),                  # not a feature
                      dict(feature, component=".", within="Test_Hole_Cut"),       # another component
                      dict(feature, within="Test_Other_Rejoin"),                  # itself
                      {"kind": "sketch", "name": "Test_Other_Sketch", "component": "TestBlock", "on": "origin:XY",
                       "within": "Test_Hole_Cut"},                                # only a feature refills
                      dict(feature, phase="polish"),                              # unknown phase
                      {"kind": "component", "name": "Other", "phase": "enhance"}):
            raw = copy.deepcopy(RAW)
            raw["items"].append(extra)
            with self.assertRaises(inventory.InventoryError, msg=repr(extra)):
                inventory.normalise(raw)
        raw = copy.deepcopy(RAW)
        raw["items"].insert(2, dict(REJOIN))                                      # before the cut it names
        with self.assertRaises(inventory.InventoryError):
            inventory.normalise(raw)

    def test_sketch_text(self):
        raw = copy.deepcopy(RAW)
        raw["items"] += [
            {"kind": "sketch", "name": "Test_Label_Sketch", "component": "TestBlock", "on": "origin:XY",
             "expressions": ["TST_TEXT_H", "TST_WALL", "TST_WALL * 2"], "texts": ["MW-01"]},
            {"kind": "feature", "type": "ExtrudeFeature", "name": "Test_Label_TextCut", "component": "TestBlock",
             "expressions": ["TST_WALL / 4"]}]
        inv = inventory.normalise(raw)
        self.assertEqual(inv["items"][-2]["texts"], ["MW-01"])
        self.assertIn("TST_TEXT_H", inv["items"][-2]["expressions"])
        other = copy.deepcopy(raw)
        other["items"][-2]["texts"] = ["MW-02"]
        self.assertNotEqual(inventory.inventory_hash(other), inventory.inventory_hash(raw))
        read_back = inventory.from_snapshot(snapshot_of(raw))
        self.assertEqual(inventory.inventory_hash(read_back), inventory.inventory_hash(raw))


if __name__ == "__main__":
    unittest.main()
