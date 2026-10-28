from orders.config import get_settings
from orders.errors import NotFoundError, OrderError
from orders.models import Order, dict_to_items
from orders.pricing import PricingStrategyFactory, compute_total
from orders.utils import IdGenerator
from orders.validators import (
    CustomerValidator,
    ItemsValidator,
    TierValidator,
    ValidatorChain,
)


class OrderService:
    def __init__(self, repository, notifier, settings=None):
        self.repository = repository
        self.notifier = notifier
        self.settings = settings or get_settings()
        self.ids = IdGenerator(self.settings.ID_PREFIX, self.settings.ID_WIDTH)
        self.validator = (
            ValidatorChain()
            .add("customer", CustomerValidator())
            .add("tier", TierValidator())
            .add("items", ItemsValidator(self.settings.MAX_ITEMS))
        )

    def create(self, data):
        self.validator.run(data)
        order = Order(
            id=self.ids.next_id(),
            customer=data["customer"].strip(),
            tier=data["tier"],
            items=dict_to_items(data["items"]),
        )
        self.repository.save(order)
        self._notify("created " + order.id + " for " + order.customer)
        return order

    def get(self, order_id):
        order = self.repository.get(order_id)
        if order is None:
            raise NotFoundError("order not found: " + order_id)
        return order

    def list(self, status=None):
        orders = self.repository.all()
        if status is not None:
            filtered = []
            for o in orders:
                if o.status == status:
                    filtered.append(o)
            orders = filtered
        orders.sort(key=lambda o: o.id)
        return orders

    def cancel(self, order_id):
        order = self.get(order_id)
        if order.status == "cancelled":
            raise OrderError("order already cancelled: " + order_id)
        order.status = "cancelled"
        self.repository.save(order)
        self._notify("cancelled " + order.id)
        return order

    def total(self, order_id):
        order = self.get(order_id)
        strategy = PricingStrategyFactory.for_tier(order.tier)
        return compute_total(order.items, strategy)

    def _notify(self, message):
        if self.settings.ENABLE_NOTIFICATIONS:
            self.notifier.notify(message)
