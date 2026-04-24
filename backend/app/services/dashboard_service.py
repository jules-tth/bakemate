from __future__ import annotations

"""Service helpers for dashboard related metrics."""

from datetime import date, datetime, timezone
from typing import List, Tuple

from sqlmodel import Session, func, select

from app.models.order import Order, OrderStatus
from app.models.ingredient import Ingredient
from app.models.user import User


def _parse_range(range_str: str) -> Tuple[datetime, datetime]:
    """Convert a range string like ``"YTD"`` or ``"2024"`` into start and end datetimes."""

    today = datetime.now(timezone.utc).date()
    if range_str.upper() == "YTD":
        start_date = date(today.year, 1, 1)
        end_date = today
    else:
        try:
            year = int(range_str)
            start_date = date(year, 1, 1)
            end_date = date(year, 12, 31)
        except ValueError:
            start_date = date(today.year, 1, 1)
            end_date = today

    start_dt = datetime.combine(start_date, datetime.min.time(), tzinfo=timezone.utc)
    end_dt = datetime.combine(end_date, datetime.max.time(), tzinfo=timezone.utc)
    return start_dt, end_dt


class DashboardService:
    def __init__(self, session: Session) -> None:
        self.session = session

    async def get_summary(self, *, current_user: User, range: str) -> dict:
        start_dt, end_dt = _parse_range(range)

        revenue_stmt = select(func.sum(Order.total_amount)).where(
            Order.user_id == current_user.id,
            Order.status == OrderStatus.COMPLETED,
            Order.order_date >= start_dt,
            Order.order_date <= end_dt,
        )
        revenue = self.session.exec(revenue_stmt).one_or_none() or 0

        orders_count_stmt = select(func.count(Order.id)).where(
            Order.user_id == current_user.id,
            Order.order_date >= start_dt,
            Order.order_date <= end_dt,
        )
        total_orders = self.session.exec(orders_count_stmt).one_or_none() or 0

        low_stock_stmt = select(func.count(Ingredient.id)).where(
            Ingredient.user_id == current_user.id,
            Ingredient.low_stock_threshold != None,  # noqa: E711
            Ingredient.quantity_on_hand < Ingredient.low_stock_threshold,
        )
        ingredients_low = self.session.exec(low_stock_stmt).one_or_none() or 0

        return {
            "revenue": float(revenue),
            "total_orders": int(total_orders),
            "ingredients_low": int(ingredients_low),
        }

    async def get_orders_over_time(
        self, *, current_user: User, range: str
    ) -> List[dict]:
        start_dt, end_dt = _parse_range(range)

        orders_stmt = (
            select(
                func.strftime("%m", Order.order_date).label("month"),
                func.count(Order.id),
            )
            .where(
                Order.user_id == current_user.id,
                Order.order_date >= start_dt,
                Order.order_date <= end_dt,
            )
            .group_by("month")
            .order_by("month")
        )

        rows = self.session.exec(orders_stmt).all()
        results = []
        for month, count in rows:
            month_name = datetime(1900, int(month), 1).strftime("%b")
            results.append({"date": month_name, "count": int(count)})
        return results

    async def get_revenue_over_time(
        self, *, current_user: User, range: str
    ) -> List[dict]:
        start_dt, end_dt = _parse_range(range)

        revenue_stmt = (
            select(
                func.strftime("%m", Order.order_date).label("month"),
                func.sum(Order.total_amount),
            )
            .where(
                Order.user_id == current_user.id,
                Order.status == OrderStatus.COMPLETED,
                Order.order_date >= start_dt,
                Order.order_date <= end_dt,
            )
            .group_by("month")
            .order_by("month")
        )

        rows = self.session.exec(revenue_stmt).all()
        results = []
        for month, revenue in rows:
            month_name = datetime(1900, int(month), 1).strftime("%b")
            results.append({"date": month_name, "revenue": float(revenue or 0)})
        return results
