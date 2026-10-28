from orders.container import Container


def create_order(customer, tier, items):
    """Create an order and return it as a dict."""
    return Container.get().controller.create({"customer": customer, "tier": tier, "items": items})


def get_order(order_id):
    """Return the order with this id as a dict."""
    return Container.get().controller.get(order_id)


def list_orders(status=None):
    """Return all orders sorted by id, optionally only those with this status."""
    return Container.get().controller.list(status)


def cancel_order(order_id):
    """Cancel an open order and return it."""
    return Container.get().controller.cancel(order_id)


def order_total(order_id):
    """Return the order total after the tier discount, rounded to cents."""
    return Container.get().controller.total(order_id)


def notifications():
    """Return the notification messages sent so far."""
    return list(Container.get().notifier.sent)
