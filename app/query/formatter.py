def format_response(result: dict) -> str:
    """Converts raw executor output into a human-readable answer string.

    Four cases, resolved in order:
      D  value is int          → count summary
      A  is_partial, 1 field   → "User names: Ali, Sara"
      B  is_partial, N fields  → bulleted list with primary + extras in parens
      C  full object (default) → table-specific prose summary

    When time_range is present, every case surfaces it in the answer text.
    """
    if not result:
        return "No data found."

    value = result.get("value")
    meta = result.get("meta", {})
    label = meta.get("label", "records")
    selected_fields = meta.get("selected_fields") or []
    is_partial = meta.get("is_partial", False)
    time_range = meta.get("time_range") or ""
    search_field = meta.get("search_field")

    singular = label.rstrip("s")
    phrase = _time_phrase(time_range)   # "" when no time_range

    # Case D — count
    if isinstance(value, int):
        suffix = f" {phrase}" if phrase else ""
        return f"Found {value} {label}{suffix}."

    if not isinstance(value, list):
        return f"Result: {value}"

    if len(value) == 0:
        suffix = f" {phrase}" if phrase else ""
        return f"No {label}{suffix} found."

    # Case A — single requested field
    if is_partial and len(selected_fields) == 1:
        field = selected_fields[0]
        vals = [str(r.get(field, "?")) for r in value]
        header = f"{singular.title()} {field}s"
        if phrase:
            header = f"{header} {phrase}"
        return f"{header}: {', '.join(vals)}"

    # Case B — multiple requested fields
    if is_partial and len(selected_fields) > 1:
        lines = "\n".join(_format_row(r, selected_fields) for r in value)
        header = label.title()
        if phrase:
            header = f"{header} {phrase}"
        return f"{header}:\n{lines}"

    # Case C — full object
    # With time_range: bulleted list keyed on the table's search_field (name/identifier).
    # Without time_range: original table-specific prose.
    if phrase:
        return _time_list(label, value, phrase, search_field)

    return _full_summary(label, value)


# ── helpers ───────────────────────────────────────────────────────────────────

def _time_phrase(time_range: str) -> str:
    """Map a raw time_range string to a readable phrase, or return '' if empty."""
    if not time_range:
        return ""
    mapping = {
        "today": "created today",
        "this_week": "created this week",
        "week": "created this week",
        "last_7_days": "created in the last 7 days",
        "last7days": "created in the last 7 days",
        "this_month": "created this month",
        "month": "created this month",
        "last_30_days": "created in the last 30 days",
        "last 7 days": "created in the last 7 days",
        "last 30 days": "created in the last 30 days",
    }
    return mapping.get(time_range.lower().strip(), f"created {time_range}")


def _format_row(row: dict, fields: list) -> str:
    primary = str(row.get(fields[0], "?"))
    extras = [str(row.get(f, "?")) for f in fields[1:]]
    return f"- {primary} ({', '.join(extras)})" if extras else f"- {primary}"


def _time_list(label: str, rows: list, phrase: str, search_field: str) -> str:
    """Bulleted list used for Case C when a time filter is active."""
    header = f"{label.title()} {phrase}:"
    if search_field:
        lines = [f"- {r.get(search_field, '?')}" for r in rows]
    else:
        # Orders have no search_field — fall back to id + total_price.
        lines = [f"- Order #{r.get('id', '?')} — total ${r.get('total_price', '?')}" for r in rows]
    return f"{header}\n" + "\n".join(lines)


def _full_summary(label: str, rows: list) -> str:
    """Original prose summary for full-object queries with no time filter."""
    count = len(rows)
    first = rows[0]

    if label == "products":
        name = first.get("name", "unknown")
        price = first.get("price", "?")
        stock = first.get("stock", "?")
        blurb = f"{name} — ${price} ({stock} in stock)"
        if count == 1:
            return f"Found 1 product: {blurb}"
        return f"Found {count} products. Example: {blurb}"

    if label == "orders":
        oid = first.get("id", "?")
        qty = first.get("quantity", "?")
        total = first.get("total_price", "?")
        blurb = f"Order #{oid} — qty {qty}, total ${total}"
        if count == 1:
            return f"Found 1 order: {blurb}"
        return f"Found {count} orders. Latest: {blurb}"

    if label == "users":
        name = first.get("name", "unknown")
        email = first.get("email", "")
        detail = f" ({email})" if email else ""
        if count == 1:
            return f"Found 1 user: {name}{detail}"
        return f"Found {count} users."

    return f"Found {count} {label}."
