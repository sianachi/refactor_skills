def is_positive(x):
    if x > 0:
        return True
    else:
        return False


def sum_values(values):
    result = 0
    for v in values:
        result = result + v
    return result


def flatten(list_of_lists):
    out = []
    for sub in list_of_lists:
        for x in sub:
            out.append(x)
    return out
