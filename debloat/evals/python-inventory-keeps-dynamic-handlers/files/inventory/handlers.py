def handle_restock(items):
    return [i["name"] for i in items if i["qty"] < 5]


def handle_audit(items):
    return {"count": len(items), "names": sorted(i["name"] for i in items)}
