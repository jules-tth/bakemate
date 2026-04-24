import asyncio
from datetime import date, datetime, timezone
from uuid import uuid4

from sqlalchemy.pool import StaticPool
from sqlmodel import Session, SQLModel, create_engine

import app.services.order_service as order_service_module
from app.api.v1.endpoints.orders import read_orders
from app.models.order import Order, OrderStatus
from app.models.user import User


def test_read_orders_endpoint_returns_ops_queue_fields_in_nearest_due_order(monkeypatch):
    monkeypatch.setattr(
        order_service_module,
        "_utcnow",
        lambda: datetime(2026, 3, 13, 14, 0, tzinfo=timezone.utc),
    )
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(engine)

    with Session(engine) as session:
        current_user = User(
            id=uuid4(),
            email="api-queue@example.com",
            hashed_password="not-used",
            is_active=True,
            is_superuser=False,
        )
        session.add(current_user)
        session.add(
            Order(
                user_id=current_user.id,
                order_number="ORD-OVERDUE",
                customer_name="Jamie Rivera",
                customer_email="jamie@example.com",
                status=OrderStatus.CONFIRMED,
                due_date=datetime(2026, 3, 12, 15, 0, tzinfo=timezone.utc),
                total_amount=120.0,
                subtotal=120.0,
                balance_due=120.0,
                deposit_amount=30.0,
                deposit_due_date=date(2026, 3, 11),
            )
        )
        session.add(
            Order(
                user_id=current_user.id,
                order_number="ORD-FUTURE",
                customer_name="Taylor Future",
                customer_email="future@example.com",
                status=OrderStatus.CONFIRMED,
                due_date=datetime(2026, 3, 16, 15, 0, tzinfo=timezone.utc),
                total_amount=80.0,
                subtotal=80.0,
                balance_due=80.0,
            )
        )
        session.commit()

        payload = asyncio.run(
            read_orders(
                session=session,
                skip=0,
                limit=100,
                status_filter=None,
                current_user=current_user,
            )
        )

    assert [order.order_number for order in payload] == ["ORD-OVERDUE", "ORD-FUTURE"]
    assert payload[0].queue_summary.is_overdue is True
    assert payload[0].risk_summary.level == "high"
    assert "deposit_overdue" in payload[0].risk_summary.reasons
    assert payload[0].customer_history_summary.total_orders == 1
    assert payload[0].deposit_due_date == date(2026, 3, 11)
    assert payload[0].ops_summary.next_action == "Collect overdue deposit"
    assert "Deposit due" in payload[0].ops_summary.ops_attention
    assert payload[1].queue_summary.due_bucket == "next_up"
