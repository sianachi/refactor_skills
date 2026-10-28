from orders.models import dto_to_dict, order_to_dto


class OrderController:
    def __init__(self, service):
        self.service = service

    def create(self, data):
        order = self.service.create(data)
        return dto_to_dict(order_to_dto(order))

    def get(self, order_id):
        order = self.service.get(order_id)
        return dto_to_dict(order_to_dto(order))

    def list(self, status=None):
        orders = self.service.list(status)
        result = []
        for order in orders:
            result.append(dto_to_dict(order_to_dto(order)))
        return result

    def cancel(self, order_id):
        order = self.service.cancel(order_id)
        return dto_to_dict(order_to_dto(order))

    def total(self, order_id):
        return self.service.total(order_id)
