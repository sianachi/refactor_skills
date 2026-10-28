"""Hidden contract tests through `inventory`'s public names only."""
import json
import os
import tempfile
import unittest

from inventory import add_item, total_value, dispatch_event, load_items


class Contract(unittest.TestCase):
    def test_add_item(self):
        items = []
        got = add_item(items, "bolt", 2, 0)
        self.assertEqual(got, {"name": "bolt", "qty": 2, "price": 0})
        self.assertIs(items[0], got)
        add_item(items, "x", 0.5, 1.5)
        for qty, price, msg in ((0, 1, "qty must be positive"), (-1, -1, "qty must be positive"), (1, -0.01, "price must not be negative")):
            with self.assertRaises(ValueError) as cm:
                add_item(items, "y", qty, price)
            self.assertEqual(str(cm.exception), msg)
        self.assertEqual(len(items), 2)

    def test_total(self):
        self.assertEqual(total_value([]), 0)
        self.assertAlmostEqual(total_value([{"name": "a", "qty": 3, "price": 0.1}, {"name": "b", "qty": 2, "price": 5}]), 10.3)

    def test_events(self):
        items = [{"name": "b", "qty": 9, "price": 1}, {"name": "a", "qty": 1, "price": 1}]
        self.assertEqual(dispatch_event("restock", items), ["a"])
        self.assertEqual(dispatch_event("audit", items), {"count": 2, "names": ["a", "b"]})
        for e in json.load(open("events.json")):
            dispatch_event(e, items)
        with self.assertRaises(AttributeError):
            dispatch_event("nope", items)

    def test_load(self):
        with self.assertRaises(FileNotFoundError):
            load_items("/nonexistent/x.json")
        with tempfile.TemporaryDirectory() as d:
            p = os.path.join(d, "i.json")
            json.dump({"a": 1}, open(p, "w"))
            self.assertEqual(load_items(p), {"a": 1})


if __name__ == "__main__":
    unittest.main()
