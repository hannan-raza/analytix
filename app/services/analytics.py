from datetime import datetime, timezone
from typing import Optional

from sqlalchemy.orm import Session
from sqlalchemy import func, and_

from app.models.user import User
from app.models.product import Product
from app.models.order import Order
from app.logger import get_logger

logger = get_logger(__name__)


def _round(value) -> float:
    return round(float(value or 0), 2)


def _trunc(period: str) -> str:
    return period if period in ("day", "week", "month") else "month"


# ── Dashboard ────────────────────────────────────────────────────────────────

def get_dashboard_overview(db: Session) -> dict:
    total_users = db.query(func.count(User.id)).scalar() or 0
    total_orders = db.query(func.count(Order.id)).scalar() or 0
    total_revenue = _round(db.query(func.sum(Order.total_price)).scalar())
    avg_order_value = _round(db.query(func.avg(Order.total_price)).scalar())
    active_customers = db.query(func.count(func.distinct(Order.user_id))).scalar() or 0

    now = datetime.now(timezone.utc)
    this_month = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    last_month = (
        this_month.replace(month=this_month.month - 1)
        if this_month.month > 1
        else this_month.replace(year=this_month.year - 1, month=12)
    )

    rev_this = _round(
        db.query(func.sum(Order.total_price))
        .filter(Order.created_at >= this_month)
        .scalar()
    )
    rev_last = _round(
        db.query(func.sum(Order.total_price))
        .filter(and_(Order.created_at >= last_month, Order.created_at < this_month))
        .scalar()
    )
    growth_pct = (
        round(((rev_this - rev_last) / rev_last) * 100, 2)
        if rev_last > 0
        else (100.0 if rev_this > 0 else 0.0)
    )

    return {
        "total_users": total_users,
        "total_orders": total_orders,
        "total_revenue": total_revenue,
        "avg_order_value": avg_order_value,
        "active_customers": active_customers,
        "monthly_growth": {
            "revenue_this_month": rev_this,
            "revenue_last_month": rev_last,
            "growth_pct": growth_pct,
        },
    }


# ── Revenue ──────────────────────────────────────────────────────────────────

def get_revenue_analytics(
    db: Session,
    period: str = "month",
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
) -> dict:
    trunc = _trunc(period)

    q = db.query(
        func.date_trunc(trunc, Order.created_at).label("period"),
        func.sum(Order.total_price).label("revenue"),
        func.count(Order.id).label("order_count"),
    )
    if start_date:
        q = q.filter(Order.created_at >= start_date)
    if end_date:
        q = q.filter(Order.created_at <= end_date)

    rows = (
        q.group_by(func.date_trunc(trunc, Order.created_at))
        .order_by(func.date_trunc(trunc, Order.created_at))
        .all()
    )

    data = []
    for i, row in enumerate(rows):
        rev = _round(row.revenue)
        prev_rev = _round(rows[i - 1].revenue) if i > 0 else 0.0
        growth_pct = (
            round(((rev - prev_rev) / prev_rev) * 100, 2) if prev_rev > 0 else None
        )
        data.append(
            {
                "period": row.period.isoformat() if row.period else None,
                "revenue": rev,
                "order_count": row.order_count or 0,
                "growth_pct": growth_pct,
            }
        )

    total = round(sum(r["revenue"] for r in data), 2)
    avg_per_period = round(total / len(data), 2) if data else 0.0

    return {
        "period_type": trunc,
        "data": data,
        "total_revenue": total,
        "avg_revenue_per_period": avg_per_period,
    }


# ── Orders ───────────────────────────────────────────────────────────────────

def get_orders_analytics(
    db: Session,
    period: str = "month",
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
) -> dict:
    trunc = _trunc(period)

    q = db.query(
        func.date_trunc(trunc, Order.created_at).label("period"),
        func.count(Order.id).label("order_count"),
        func.sum(Order.total_price).label("total_revenue"),
    )
    if start_date:
        q = q.filter(Order.created_at >= start_date)
    if end_date:
        q = q.filter(Order.created_at <= end_date)

    rows = (
        q.group_by(func.date_trunc(trunc, Order.created_at))
        .order_by(func.date_trunc(trunc, Order.created_at))
        .all()
    )

    total_orders = db.query(func.count(Order.id)).scalar() or 0

    return {
        "note": "Schema has no order status field — all recorded orders are treated as completed.",
        "status_counts": [{"status": "completed", "count": total_orders}],
        "period_type": trunc,
        "trends": [
            {
                "period": row.period.isoformat() if row.period else None,
                "order_count": row.order_count or 0,
                "total_revenue": _round(row.total_revenue),
            }
            for row in rows
        ],
        "total_orders": total_orders,
    }


# ── Users ────────────────────────────────────────────────────────────────────

def get_user_analytics(db: Session, period: str = "month") -> dict:
    trunc = _trunc(period)

    rows = (
        db.query(
            func.date_trunc(trunc, User.created_at).label("period"),
            func.count(User.id).label("new_users"),
        )
        .group_by(func.date_trunc(trunc, User.created_at))
        .order_by(func.date_trunc(trunc, User.created_at))
        .all()
    )

    total_users = db.query(func.count(User.id)).scalar() or 0
    active_users = db.query(func.count(func.distinct(Order.user_id))).scalar() or 0

    # Users with more than one order
    returning_subq = (
        db.query(Order.user_id)
        .group_by(Order.user_id)
        .having(func.count(Order.id) > 1)
        .subquery()
    )
    returning_customers = (
        db.query(func.count()).select_from(returning_subq).scalar() or 0
    )

    return {
        "period_type": trunc,
        "registrations_over_time": [
            {
                "period": row.period.isoformat() if row.period else None,
                "new_users": row.new_users or 0,
            }
            for row in rows
        ],
        "total_users": total_users,
        "active_users": active_users,
        "returning_customers": returning_customers,
    }


# ── Products ─────────────────────────────────────────────────────────────────

def get_product_analytics(db: Session, limit: int = 10) -> dict:
    def _query_products(order_col):
        return (
            db.query(
                Product.id,
                Product.name,
                Product.price,
                func.sum(Order.quantity).label("total_quantity_sold"),
                func.sum(Order.total_price).label("total_revenue"),
            )
            .join(Order, Product.id == Order.product_id)
            .group_by(Product.id, Product.name, Product.price)
            .order_by(order_col.desc())
            .limit(limit)
            .all()
        )

    def _serialize(row) -> dict:
        return {
            "product_id": row.id,
            "name": row.name,
            "price": _round(row.price),
            "total_quantity_sold": row.total_quantity_sold or 0,
            "total_revenue": _round(row.total_revenue),
        }

    top_selling = _query_products(func.sum(Order.quantity))
    most_profitable = _query_products(func.sum(Order.total_price))

    return {
        "top_selling": [_serialize(r) for r in top_selling],
        "most_profitable": [_serialize(r) for r in most_profitable],
        "limit": limit,
    }


# ── Revenue distribution ─────────────────────────────────────────────────────

def get_revenue_distribution(db: Session) -> dict:
    rows = (
        db.query(
            Product.name,
            func.sum(Order.total_price).label("revenue"),
        )
        .join(Order, Product.id == Order.product_id)
        .group_by(Product.name)
        .order_by(func.sum(Order.total_price).desc())
        .all()
    )

    total = round(sum(float(r.revenue or 0) for r in rows), 2)

    return {
        "data": [
            {
                "product_name": r.name,
                "revenue": _round(r.revenue),
                "percentage": round(float(r.revenue or 0) / total * 100, 2)
                if total > 0
                else 0.0,
            }
            for r in rows
        ],
        "total_revenue": total,
    }
