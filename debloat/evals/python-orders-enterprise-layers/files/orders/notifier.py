from orders.interfaces import INotifier


class ListNotifier(INotifier):
    def __init__(self):
        self.sent = []

    def notify(self, message):
        self.sent.append(message)


class NullNotifier(INotifier):
    def notify(self, message):
        pass
