class IdGenerator:
    def __init__(self, prefix, width):
        self.prefix = prefix
        self.width = width
        self.counter = 0

    def next_id(self):
        self.counter = self.counter + 1
        number = str(self.counter)
        while len(number) < self.width:
            number = "0" + number
        return self.prefix + number


def chunk(values, size):
    out = []
    for i in range(0, len(values), size):
        out.append(values[i : i + size])
    return out


def is_empty(value):
    if value is None:
        return True
    if len(value) == 0:
        return True
    return False
