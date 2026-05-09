from app.models.product import Product
from app.models.order import Order
from app.models.user import User

# Single source of truth for all queryable tables.
# search_field: column used for ilike name searches (None = not searchable by name)
# time_field:   column used for time_range filtering (None = not applicable)
SCHEMA_REGISTRY = {
    "products": {
        "model": Product,
        "fields": ["id", "name", "price", "stock", "created_at"],
        "search_field": "name",
        "time_field": "created_at",
    },
    "orders": {
        "model": Order,
        "fields": ["id", "user_id", "product_id", "quantity", "total_price", "created_at"],
        "search_field": None,
        "time_field": "created_at",
    },
    "users": {
        "model": User,
        "fields": ["id", "name", "email", "created_at"],
        "search_field": "name",
        "time_field": "created_at",
    },
}

_ALIASES = {
    "product": "products",
    "products": "products",
    "order": "orders",
    "orders": "orders",
    "user": "users",
    "users": "users",
}


def resolve_entity(entity: str):
    """Return (canonical_name, schema) or (None, None) if not a known entity."""
    canonical = _ALIASES.get(entity.lower().strip())
    if not canonical:
        return None, None
    return canonical, SCHEMA_REGISTRY[canonical]
