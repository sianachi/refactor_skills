from abc import ABC, abstractmethod


class IOrderRepository(ABC):
    @abstractmethod
    def save(self, order):
        pass

    @abstractmethod
    def get(self, order_id):
        pass

    @abstractmethod
    def all(self):
        pass


class IPricingStrategy(ABC):
    @abstractmethod
    def discount_rate(self):
        pass


class INotifier(ABC):
    @abstractmethod
    def notify(self, message):
        pass
