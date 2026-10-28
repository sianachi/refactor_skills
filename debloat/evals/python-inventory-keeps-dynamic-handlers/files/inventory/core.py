import os
import sys
import json

from inventory import handlers
from inventory.utils import is_positive, sum_values


def add_item(items, name, qty, price):
    """Add an item to the inventory list."""
    # check qty
    if not is_positive(qty):
        raise ValueError("qty must be positive")
    if price < 0:
        raise ValueError("price must not be negative")
    item = {"name": name, "qty": qty, "price": price}
    items.append(item)
    return item


def total_value(items):
    """Return the total value of the inventory."""
    values = []
    for item in items:
        values.append(item["qty"] * item["price"])
    total = sum_values(values)
    return total


def _legacy_total(items):
    t = 0
    for i in range(len(items)):
        t = t + items[i]["qty"] * items[i]["price"]
    return t


# def total_value_v1(items):
#     total = 0
#     for item in items:
#         total += item["qty"] * item["price"]
#     return total


def dispatch_event(event, items):
    """Dispatch an inventory event; event names come from events.json."""
    handler = getattr(handlers, "handle_" + event)
    return handler(items)
