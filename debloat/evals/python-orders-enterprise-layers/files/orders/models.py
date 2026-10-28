from dataclasses import dataclass, field


@dataclass
class OrderItem:
    sku: str
    qty: int
    unit_price: float


@dataclass
class Order:
    id: str
    customer: str
    tier: str
    items: list = field(default_factory=list)
    status: str = "open"


@dataclass
class OrderDTO:
    id: str
    customer: str
    tier: str
    items: list
    status: str


def order_to_dto(order):
    return OrderDTO(
        id=order.id,
        customer=order.customer,
        tier=order.tier,
        items=[{"sku": i.sku, "qty": i.qty, "unit_price": i.unit_price} for i in order.items],
        status=order.status,
    )


def dto_to_dict(dto):
    return {
        "id": dto.id,
        "customer": dto.customer,
        "tier": dto.tier,
        "items": [dict(i) for i in dto.items],
        "status": dto.status,
    }


def dict_to_items(raw_items):
    items = []
    for raw in raw_items:
        items.append(OrderItem(sku=raw["sku"], qty=raw["qty"], unit_price=raw["unit_price"]))
    return items
