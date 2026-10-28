import json
import os
import tempfile
import unittest

from inventory import add_item, total_value, dispatch_event, load_items


class InventoryTest(unittest.TestCase):
    def test_add_and_total(self):
        items = []
        add_item(items, "bolt", 10, 0.5)
        add_item(items, "nut", 3, 0.25)
        self.assertAlmostEqual(total_value(items), 5.75)

    def test_rejects_bad_qty(self):
        with self.assertRaises(ValueError):
            add_item([], "bolt", 0, 1)

    def test_restock(self):
        items = [{"name": "a", "qty": 1, "price": 1}, {"name": "b", "qty": 9, "price": 1}]
        self.assertEqual(dispatch_event("restock", items), ["a"])

    def test_load(self):
        with tempfile.TemporaryDirectory() as d:
            p = os.path.join(d, "i.json")
            with open(p, "w") as f:
                json.dump([{"name": "x", "qty": 1, "price": 2}], f)
            self.assertEqual(load_items(p)[0]["name"], "x")


if __name__ == "__main__":
    unittest.main()
