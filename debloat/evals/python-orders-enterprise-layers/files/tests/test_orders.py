import unittest

import orders
from orders.container import Container


class OrdersTest(unittest.TestCase):
    def setUp(self):
        Container.reset()

    def test_create_and_total(self):
        o = orders.create_order("ann", "gold", [{"sku": "a", "qty": 2, "unit_price": 10.0}])
        self.assertEqual(o["id"], "ord-0001")
        self.assertEqual(orders.order_total(o["id"]), 18.0)

    def test_cancel(self):
        o = orders.create_order("bob", "standard", [{"sku": "a", "qty": 1, "unit_price": 5}])
        self.assertEqual(orders.cancel_order(o["id"])["status"], "cancelled")

    def test_validation(self):
        with self.assertRaises(orders.ValidationError):
            orders.create_order("", "gold", [{"sku": "a", "qty": 1, "unit_price": 1}])


if __name__ == "__main__":
    unittest.main()
