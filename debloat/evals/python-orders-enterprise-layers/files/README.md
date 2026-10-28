# orders

Order management library used by the checkout and support services.

Public API (import from `orders`): `create_order`, `get_order`, `list_orders`, `cancel_order`,
`order_total`, `notifications`, and the errors `OrderError`, `ValidationError`, `NotFoundError`.
Orders are plain dicts. Run tests with `python3 -m unittest`.
