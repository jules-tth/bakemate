import asyncio
from datetime import date, datetime, timezone
from uuid import uuid4

from sqlalchemy.pool import StaticPool
from sqlmodel import Session, SQLModel, create_engine, select

from app.models.contact import Contact
from app.models.order import OrderCreate, OrderItemCreate, OrderStatus, OrderUpdate, PaymentStatus
from app.models.user import User
import app.services.order_service as order_service_module
from app.services.order_service import OrderService


def test_order_service_normalizes_customer_and_summaries():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(engine)

    with Session(engine) as session:
        current_user = User(
            id=uuid4(),
            email="ops@example.com",
            hashed_password="not-used",
            is_active=True,
            is_superuser=False,
        )
        session.add(current_user)
        session.commit()
        session.refresh(current_user)

        service = OrderService(session=session)
        created_order = asyncio.run(
            service.create_order(
                current_user=current_user,
                order_in=OrderCreate(
                    due_date=datetime(2026, 4, 15, 14, 30, tzinfo=timezone.utc),
                    delivery_method="pickup",
                    customer_name="Jamie Rivera",
                    customer_email="jamie@example.com",
                    customer_phone="555-0100",
                    deposit_amount=25.0,
                    items=[
                        OrderItemCreate(
                            name="Celebration Cake",
                            description="8 inch",
                            quantity=1,
                            unit_price=80.0,
                        )
                    ],
                ),
            )
        )

        contacts = session.exec(select(Contact)).all()
        assert len(contacts) == 1
        assert created_order.customer_contact_id == contacts[0].id
        assert created_order.customer_summary.is_linked_contact is True
        assert created_order.customer_summary.name == "Jamie Rivera"
        assert created_order.payment_summary.amount_due == 80.0
        assert created_order.payment_summary.deposit_required == 25.0
        assert created_order.invoice_summary.is_ready is True

        listed_orders = asyncio.run(
            service.get_orders_by_user(current_user=current_user, skip=0, limit=20)
        )
        assert len(listed_orders) == 1
        assert listed_orders[0].id == created_order.id

        updated_order = asyncio.run(
            service.update_order(
                order_id=created_order.id,
                current_user=current_user,
                order_in=OrderUpdate(
                    payment_status=PaymentStatus.DEPOSIT_PAID,
                    items=[
                        OrderItemCreate(
                            name="Celebration Cake",
                            description="10 inch",
                            quantity=1,
                            unit_price=100.0,
                        )
                    ],
                ),
            )
        )

        assert updated_order is not None
        assert updated_order.subtotal == 100.0
        assert updated_order.payment_summary.amount_paid == 25.0
        assert updated_order.payment_summary.amount_due == 75.0
        assert updated_order.invoice_summary.status == "ready"


def test_order_service_prioritizes_nearest_due_and_builds_queue_risk_history(monkeypatch):
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
            email="queue@example.com",
            hashed_password="not-used",
            is_active=True,
            is_superuser=False,
        )
        session.add(current_user)
        session.commit()
        session.refresh(current_user)

        service = OrderService(session=session)
        oldest_completed = asyncio.run(
            service.create_order(
                current_user=current_user,
                order_in=OrderCreate(
                    due_date=datetime(2026, 3, 10, 12, 0, tzinfo=timezone.utc),
                    customer_email="jamie@example.com",
                    customer_name="Jamie Rivera",
                    items=[OrderItemCreate(name="Cookies", quantity=1, unit_price=20.0)],
                    status=OrderStatus.COMPLETED,
                ),
            )
        )
        _ = oldest_completed

        today_order = asyncio.run(
            service.create_order(
                current_user=current_user,
                order_in=OrderCreate(
                    due_date=datetime(2026, 3, 13, 16, 0, tzinfo=timezone.utc),
                    customer_email="jamie@example.com",
                    customer_name="Jamie Rivera",
                    deposit_amount=30.0,
                    deposit_due_date=date(2026, 3, 12),
                    balance_due_date=date(2026, 3, 13),
                    items=[OrderItemCreate(name="Cake", quantity=1, unit_price=120.0)],
                ),
            )
        )
        future_order = asyncio.run(
            service.create_order(
                current_user=current_user,
                order_in=OrderCreate(
                    due_date=datetime(2026, 3, 18, 9, 0, tzinfo=timezone.utc),
                    customer_email="future@example.com",
                    customer_name="Future Customer",
                    items=[OrderItemCreate(name="Brownies", quantity=1, unit_price=45.0)],
                ),
            )
        )

        listed_orders = asyncio.run(
            service.get_orders_by_user(current_user=current_user, skip=0, limit=20)
        )

        assert [order.id for order in listed_orders] == [
            today_order.id,
            future_order.id,
            oldest_completed.id,
        ]

        queue_order = listed_orders[0]
        assert queue_order.queue_summary.is_due_today is True
        assert queue_order.queue_summary.is_overdue is False
        assert queue_order.queue_summary.due_bucket == "today"
        assert queue_order.customer_history_summary.total_orders == 2
        assert queue_order.customer_history_summary.completed_orders == 1
        assert queue_order.customer_history_summary.last_order_date is not None
        assert queue_order.risk_summary.level == "high"
        assert queue_order.risk_summary.has_overdue_payment is True
        assert "deposit_overdue" in queue_order.risk_summary.reasons
        assert queue_order.risk_summary.outstanding_amount == 120.0
        assert queue_order.deposit_due_date == date(2026, 3, 12)
        assert queue_order.balance_due_date == date(2026, 3, 13)
        assert queue_order.ops_summary.next_action == "Collect overdue deposit"
        assert queue_order.ops_summary.primary_cta_label == "Collect payment"
        assert "Deposit due 2026-03-12" in queue_order.ops_summary.ops_attention
