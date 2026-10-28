"""Hidden contract tests: only the public API from the README. Each test gets a fresh import."""
import importlib
import sys
import unittest


def fresh():
    for name in [m for m in sys.modules if m == "orders" or m.startswith("orders.")]:
        del sys.modules[name]
    return importlib.import_module("orders")


ITEM = {"sku": "a", "qty": 1, "unit_price": 1}


class Contract(unittest.TestCase):
    def setUp(self):
        self.o = fresh()

    def err(self, exc, msg, *args):
        with self.assertRaises(exc) as cm:
            self.o.create_order(*args)
        self.assertEqual(str(cm.exception), msg)

    def test_shape_and_ids(self):
        a = self.o.create_order("  ann ", "gold", [{"sku": "x", "qty": 2, "unit_price": 3}])
        self.assertEqual(a, {"id": "ord-0001", "customer": "ann", "tier": "gold",
                             "items": [{"sku": "x", "qty": 2, "unit_price": 3}], "status": "open"})
        self.assertIsInstance(a["items"][0]["unit_price"], int)
        self.assertEqual(self.o.create_order("b", "silver", [ITEM])["id"], "ord-0002")

    def test_failed_create_does_not_use_an_id(self):
        with self.assertRaises(self.o.ValidationError):
            self.o.create_order("", "gold", [ITEM])
        self.assertEqual(self.o.create_order("a", "gold", [ITEM])["id"], "ord-0001")

    def test_returned_and_input_dicts_are_copies(self):
        items = [{"sku": "x", "qty": 1, "unit_price": 2}]
        a = self.o.create_order("a", "standard", items)
        items[0]["qty"] = 99
        a["status"] = "hacked"
        a["items"][0]["sku"] = "zzz"
        g = self.o.get_order(a["id"])
        self.assertEqual(g["status"], "open")
        self.assertEqual(g["items"], [{"sku": "x", "qty": 1, "unit_price": 2}])
        g["status"] = "x"
        self.assertEqual(self.o.list_orders()[0]["status"], "open")

    def test_not_found(self):
        with self.assertRaises(self.o.NotFoundError) as cm:
            self.o.get_order("ord-9999")
        self.assertEqual(str(cm.exception), "order not found: ord-9999")
        self.assertTrue(issubclass(self.o.NotFoundError, self.o.OrderError))
        self.assertTrue(issubclass(self.o.ValidationError, self.o.OrderError))
        for fn in (self.o.cancel_order, self.o.order_total):
            with self.assertRaises(self.o.NotFoundError):
                fn("nope")

    def test_list_sort_and_filter(self):
        for c in "abc":
            self.o.create_order(c, "standard", [ITEM])
        self.o.cancel_order("ord-0002")
        self.assertEqual([x["id"] for x in self.o.list_orders()], ["ord-0001", "ord-0002", "ord-0003"])
        self.assertEqual([x["id"] for x in self.o.list_orders("open")], ["ord-0001", "ord-0003"])
        self.assertEqual([x["id"] for x in self.o.list_orders(status="cancelled")], ["ord-0002"])
        self.assertEqual(self.o.list_orders("nope"), [])

    def test_cancel(self):
        a = self.o.create_order("a", "gold", [ITEM])
        c = self.o.cancel_order(a["id"])
        self.assertEqual(c["status"], "cancelled")
        with self.assertRaises(self.o.OrderError) as cm:
            self.o.cancel_order(a["id"])
        self.assertIs(type(cm.exception), self.o.OrderError)
        self.assertEqual(str(cm.exception), "order already cancelled: ord-0001")

    def test_totals(self):
        items = [{"sku": "a", "qty": 3, "unit_price": 3.33}, {"sku": "b", "qty": 1, "unit_price": 0.01}]
        for tier, rate in (("standard", 0.0), ("silver", 0.05), ("gold", 0.10)):
            oid = self.o.create_order("a", tier, items)["id"]
            sub = 0.0
            for i in items:
                sub = sub + i["qty"] * i["unit_price"]
            self.assertEqual(self.o.order_total(oid), round(sub - sub * rate, 2))
        cancelled = self.o.create_order("a", "gold", [ITEM])["id"]
        self.o.cancel_order(cancelled)
        self.assertEqual(self.o.order_total(cancelled), 0.9)

    def test_validation_messages(self):
        V = self.o.ValidationError
        self.err(V, "customer is required", "   ", "gold", [ITEM])
        self.err(V, "customer is required", None, "gold", [ITEM])
        self.err(V, "customer is required", "", "platinum", [])
        self.err(V, "unknown tier: platinum", "a", "platinum", [ITEM])
        self.err(V, "unknown tier: None", "a", None, [ITEM])
        self.err(V, "an order needs at least one item", "a", "gold", [])
        self.err(V, "an order needs at least one item", "a", "gold", (ITEM,))
        self.err(V, "too many items", "a", "gold", [ITEM] * 51)
        self.o.create_order("a", "gold", [ITEM] * 50)
        self.err(V, "item sku is required", "a", "gold", [{"qty": 1, "unit_price": 1}])
        self.err(V, "item sku is required", "a", "gold", [{"sku": "", "qty": 1, "unit_price": 1}])
        for q in (0, -1, 1.5, True, None, "2"):
            self.err(V, "item qty must be a positive integer", "a", "gold", [{"sku": "a", "qty": q, "unit_price": 1}])
        for p in (-0.01, True, None, "1"):
            self.err(V, "item unit_price must be a non-negative number", "a", "gold", [{"sku": "a", "qty": 1, "unit_price": p}])
        self.o.create_order("a", "gold", [{"sku": "a", "qty": 1, "unit_price": 0}])

    def test_notifications(self):
        a = self.o.create_order(" ann ", "gold", [ITEM])
        self.o.cancel_order(a["id"])
        n = self.o.notifications()
        self.assertEqual(n, ["created ord-0001 for ann", "cancelled ord-0001"])
        n.append("x")
        self.assertEqual(len(self.o.notifications()), 2)
        with self.assertRaises(self.o.ValidationError):
            self.o.create_order("", "gold", [ITEM])
        self.assertEqual(len(self.o.notifications()), 2)

    def test_public_names(self):
        for name in ["create_order", "get_order", "list_orders", "cancel_order", "order_total",
                     "notifications", "OrderError", "ValidationError", "NotFoundError"]:
            self.assertTrue(hasattr(self.o, name), name)


if __name__ == "__main__":
    unittest.main()
