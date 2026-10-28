from orders.interfaces import IPricingStrategy


class StandardPricing(IPricingStrategy):
    def discount_rate(self):
        return 0.0


class SilverPricing(IPricingStrategy):
    def discount_rate(self):
        return 0.05


class GoldPricing(IPricingStrategy):
    def discount_rate(self):
        return 0.10


class PricingStrategyFactory:
    @staticmethod
    def for_tier(tier):
        if tier == "standard":
            return StandardPricing()
        elif tier == "silver":
            return SilverPricing()
        elif tier == "gold":
            return GoldPricing()
        else:
            return None


def compute_subtotal(items):
    subtotal = 0.0
    for item in items:
        line = item.qty * item.unit_price
        subtotal = subtotal + line
    return subtotal


def compute_total(items, strategy):
    subtotal = compute_subtotal(items)
    discount = subtotal * strategy.discount_rate()
    total = subtotal - discount
    return round(total, 2)
