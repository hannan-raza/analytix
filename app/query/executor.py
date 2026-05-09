from datetime import datetime, timedelta

from sqlalchemy import or_

from app.logger import get_logger
from app.query.exceptions import PipelineError
from app.models.product import Product as ProductModel

logger = get_logger(__name__)


def _apply_time_filter(query, col, time_range: str):
    now = datetime.utcnow()
    tr = time_range.lower().strip().replace(" ", "_")

    if tr == "today":
        start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    elif tr in ("last_7_days", "last7days", "this_week", "week"):
        start = now - timedelta(days=7)
    elif tr in ("last_30_days", "this_month", "month"):
        start = now - timedelta(days=30)
    else:
        logger.warning("Unknown time_range %r — filter skipped", time_range)
        return query

    return query.filter(col >= start)


def _to_json_safe(val):
    if hasattr(val, "isoformat"):
        return val.isoformat()
    return val


def execute(dsl: dict, db, user_id: int = None) -> dict:
    if not dsl:
        raise PipelineError(
            "The question could not be mapped to a database query.",
            stage="executor",
        )

    model = dsl["model"]
    operation = dsl["operation"]
    filters = dsl.get("filters", {})
    fields = dsl["fields"]
    schema = dsl.get("schema", {})
    selected_fields = dsl.get("selected_fields") or fields

    logger.info(
        "Executing: table=%s operation=%s selected_fields=%s filters=%s",
        dsl["table"], operation, selected_fields, filters,
    )

    try:
        query = db.query(model)

        # Scope order queries to the logged-in user so "how many orders do I have"
        # only counts that user's orders, not the entire table.
        if dsl.get("table") == "orders" and user_id:
            query = query.filter(model.user_id == user_id)

        name_search = filters.get("name_search")
        search_field = schema.get("search_field")
        if name_search and search_field:
            col = getattr(model, search_field)
            words = name_search.lower().strip().split()
            query = query.filter(or_(*[col.ilike(f"%{w}%") for w in words]))

        # Cross-table: filter orders by product name via subquery.
        # Handles questions like "how many orders of cricket bat?"
        product_name_filter = filters.get("product_name")
        if product_name_filter and dsl.get("table") == "orders":
            words = product_name_filter.lower().strip().split()
            matching_ids = (
                db.query(ProductModel.id)
                .filter(or_(*[ProductModel.name.ilike(f"%{w}%") for w in words]))
                .subquery()
            )
            query = query.filter(model.product_id.in_(matching_ids))

        time_range = filters.get("time_range")
        time_field = schema.get("time_field")
        if time_range and time_field:
            query = _apply_time_filter(query, getattr(model, time_field), time_range)

        if operation == "count":
            value = query.count()
        else:
            cols = [getattr(model, f) for f in selected_fields]
            rows = query.with_entities(*cols).all()
            value = [
                {f: _to_json_safe(v) for f, v in zip(selected_fields, row)}
                for row in rows
            ]

    except PipelineError:
        raise
    except Exception as e:
        logger.error("SQLAlchemy error: %s", e)
        raise PipelineError(
            "Database query failed. Please try again.",
            stage="executor",
        )

    return {
        "type": "single",
        "name": f"{dsl['table']}_{operation}",
        "value": value,
        "meta": dsl.get("meta", {}),
    }
