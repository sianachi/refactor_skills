from orders.errors import ValidationError


class Validator:
    def validate(self, value):
        raise NotImplementedError


class CustomerValidator(Validator):
    def validate(self, value):
        if not isinstance(value, str) or value.strip() == "":
            raise ValidationError("customer is required")


class TierValidator(Validator):
    VALID = ("standard", "silver", "gold")

    def validate(self, value):
        if value not in self.VALID:
            raise ValidationError("unknown tier: " + str(value))


class ItemsValidator(Validator):
    def __init__(self, max_items):
        self.max_items = max_items

    def validate(self, value):
        if not isinstance(value, list) or len(value) == 0:
            raise ValidationError("an order needs at least one item")
        if len(value) > self.max_items:
            raise ValidationError("too many items")
        for item in value:
            ItemValidator().validate(item)


class ItemValidator(Validator):
    def validate(self, value):
        if not isinstance(value.get("sku"), str) or value.get("sku") == "":
            raise ValidationError("item sku is required")
        qty = value.get("qty")
        if not isinstance(qty, int) or isinstance(qty, bool) or qty <= 0:
            raise ValidationError("item qty must be a positive integer")
        price = value.get("unit_price")
        if not isinstance(price, (int, float)) or isinstance(price, bool) or price < 0:
            raise ValidationError("item unit_price must be a non-negative number")


class ValidatorChain:
    def __init__(self):
        self.steps = []

    def add(self, field_name, validator):
        self.steps.append((field_name, validator))
        return self

    def run(self, data):
        for field_name, validator in self.steps:
            validator.validate(data.get(field_name))
