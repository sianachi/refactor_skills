from orders.controller import OrderController
from orders.notifier import ListNotifier
from orders.repository import RepositoryFactory
from orders.service import OrderService


class Container:
    """Wires the application together (dependency injection)."""

    _instance = None

    def __init__(self):
        self.repository = RepositoryFactory.create("memory")
        self.notifier = ListNotifier()
        self.service = OrderService(self.repository, self.notifier)
        self.controller = OrderController(self.service)

    @classmethod
    def get(cls):
        if cls._instance is None:
            cls._instance = Container()
        return cls._instance

    @classmethod
    def reset(cls):
        cls._instance = None
