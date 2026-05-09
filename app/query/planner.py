from app.query.registry import resolve_entity, SCHEMA_REGISTRY

_INTENT_NORMALIZE = {
    "check": "list",
    "find": "list",
    "get": "list",
    "show": "list",
    "list": "list",
    "query": "list",
    "retrieve": "list",
    "fetch": "list",
    "inquire": "list",
    "inquiry": "list",
}


def plan(intent: dict):
    intent_type = intent.get("intent", "")
    entity_raw = (intent.get("entity") or "").strip()
    filters = dict(intent.get("filters") or {})
    time_range = (intent.get("time_range") or "").strip() or None
    metrics = intent.get("metrics") or []

    # Normalize all list-like intent verbs; leave "count" untouched.
    if intent_type != "count":
        intent_type = _INTENT_NORMALIZE.get(intent_type, "list")

    canonical, schema = resolve_entity(entity_raw)

    # Entity fallback: unrecognized entity treated as a product name search.
    if canonical is None:
        filters["name_search"] = entity_raw
        canonical = "products"
        schema = SCHEMA_REGISTRY["products"]
        intent_type = "list"

    # For product searches, map product_name → name_search (text search on Product.name).
    # For other tables (e.g. orders), keep product_name as a cross-table filter key
    # so the executor can do a subquery join.
    if canonical == "products" and "product_name" in filters and "name_search" not in filters:
        filters["name_search"] = filters.pop("product_name")

    # Validate requested metrics against schema; fall back to full fields if
    # metrics is absent or contains only unrecognised field names.
    valid_metrics = [m for m in metrics if m in schema["fields"]]
    selected_fields = valid_metrics if valid_metrics else schema["fields"]

    return {
        "table": canonical,
        "model": schema["model"],
        "operation": intent_type,           # "list" | "count"
        "filters": {**filters, "time_range": time_range},
        "fields": schema["fields"],         # full schema (for reference)
        "selected_fields": selected_fields, # what executor will actually fetch
        "schema": schema,
        "meta": {
            "label": canonical,
            "selected_fields": selected_fields,
            "is_partial": bool(valid_metrics),
            "time_range": time_range,
            "search_field": schema.get("search_field"),
        },
    }
