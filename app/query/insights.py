def generate_insight(result: dict) -> str:
    if not result:
        return "No data found"

    value = result.get("value")
    meta = result.get("meta", {})
    label = meta.get("label", "records")
    selected_fields = meta.get("selected_fields") or []

    # COUNT
    if isinstance(value, int):
        return f"We have {value} {label}"

    # LIST
    if not isinstance(value, list):
        return f"Result: {value}"

    if len(value) == 0:
        return f"No matching {label} found"

    # Single-field selection: enumerate the values directly.
    if len(selected_fields) == 1:
        field = selected_fields[0]
        vals = [str(r.get(field, "?")) for r in value]
        return f"Found {len(value)} {label} — {field}: {', '.join(vals)}"

    first = value[0]

    if label == "products":
        name = first.get("name", "unknown")
        price = first.get("price")
        stock = first.get("stock")
        if len(value) == 1:
            return f"Found 1 product: {name} priced at {price} with stock {stock}"
        return (
            f"Found {len(value)} products. "
            f"Example: {name} priced at {price} with stock {stock}"
        )

    if label == "orders":
        if len(value) == 1:
            o = first
            return (
                f"Found 1 order: ID {o.get('id')} — "
                f"qty {o.get('quantity')}, total {o.get('total_price')}"
            )
        return (
            f"Found {len(value)} orders. "
            f"Latest: order ID {first.get('id')} for {first.get('total_price')}"
        )

    if label == "users":
        name = first.get("name", first.get("email", "unknown"))
        if len(value) == 1:
            return f"Found 1 user: {name}"
        return f"Found {len(value)} users"

    # Generic fallback for any future table.
    return f"Found {len(value)} {label}"
