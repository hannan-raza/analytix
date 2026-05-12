from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.auth.deps import get_current_user
from app.services import analytics as svc
from app.logger import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/analytics", tags=["Analytics"])

_PERIOD_ENUM = Query("month", enum=["day", "week", "month"])


@router.get("/dashboard", summary="Dashboard overview")
def dashboard_overview(
    db: Session = Depends(get_db),
    _: int = Depends(get_current_user),
):
    logger.info("dashboard overview requested")
    return svc.get_dashboard_overview(db)


@router.get("/revenue", summary="Revenue grouped by period with growth trends")
def revenue_analytics(
    period: str = _PERIOD_ENUM,
    start_date: Optional[datetime] = Query(None, description="ISO 8601, e.g. 2024-01-01T00:00:00Z"),
    end_date: Optional[datetime] = Query(None, description="ISO 8601, e.g. 2024-12-31T23:59:59Z"),
    db: Session = Depends(get_db),
    _: int = Depends(get_current_user),
):
    return svc.get_revenue_analytics(db, period, start_date, end_date)


@router.get("/orders", summary="Order trends and status counts")
def orders_analytics(
    period: str = _PERIOD_ENUM,
    start_date: Optional[datetime] = Query(None, description="ISO 8601"),
    end_date: Optional[datetime] = Query(None, description="ISO 8601"),
    db: Session = Depends(get_db),
    _: int = Depends(get_current_user),
):
    return svc.get_orders_analytics(db, period, start_date, end_date)


@router.get("/users", summary="User registrations, active users, returning customers")
def user_analytics(
    period: str = _PERIOD_ENUM,
    db: Session = Depends(get_db),
    _: int = Depends(get_current_user),
):
    return svc.get_user_analytics(db, period)


@router.get("/products", summary="Top-selling and most profitable products")
def product_analytics(
    limit: int = Query(10, ge=1, le=50, description="Max products to return per list"),
    db: Session = Depends(get_db),
    _: int = Depends(get_current_user),
):
    return svc.get_product_analytics(db, limit)


@router.get("/revenue/distribution", summary="Revenue split per product for pie/donut charts")
def revenue_distribution(
    db: Session = Depends(get_db),
    _: int = Depends(get_current_user),
):
    return svc.get_revenue_distribution(db)
