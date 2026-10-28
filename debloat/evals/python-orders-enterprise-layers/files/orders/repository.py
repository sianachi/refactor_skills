import copy

from orders.interfaces import IOrderRepository


class InMemoryOrderRepository(IOrderRepository):
    def __init__(self):
        self._orders = {}

    def save(self, order):
        self._orders[order.id] = copy.deepcopy(order)

    def get(self, order_id):
        order = self._orders.get(order_id)
        if order is None:
            return None
        return copy.deepcopy(order)

    def all(self):
        result = []
        for key in self._orders:
            result.append(copy.deepcopy(self._orders[key]))
        return result


class RepositoryFactory:
    @staticmethod
    def create(kind="memory"):
        if kind == "memory":
            return InMemoryOrderRepository()
        raise ValueError("unknown repository kind: " + kind)
