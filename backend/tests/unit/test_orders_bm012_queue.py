import asyncio
from datetime import date, datetime, timezone
from uuid import uuid4

import app.services.order_service as order_service_module
from app.api.v1.endpoints.orders import read_order, read_orders
from app.models.order import Order, OrderStatus
from app.models.user import User
from sqlalchemy.pool import StaticPool
from sqlmodel import SQLModel, Session, create_engine


def test_read_orders_endpoint_exposes_action_class_and_urgency_groups(monkeypatch):
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
            email="bm012@example.com",
            hashed_password="not-used",
            is_active=True,
            is_superuser=False,
        )
        session.add(current_user)
        invoice_blocked = Order(
            user_id=current_user.id,
            order_number="ORD-INVOICE",
            due_date=datetime(2026, 3, 20, 10, 0, tzinfo=timezone.utc),
            total_amount=0.0,
            subtotal=0.0,
            balance_due=0.0,
            status=OrderStatus.INQUIRY,
        )
        payment_now = Order(
            user_id=current_user.id,
            order_number="ORD-PAYMENT",
            customer_name="Mina",
            customer_email="mina@example.com",
            due_date=datetime(2026, 3, 15, 10, 0, tzinfo=timezone.utc),
            total_amount=240.0,
            subtotal=240.0,
            balance_due=240.0,
            deposit_amount=80.0,
            deposit_due_date=date(2026, 3, 13),
            status=OrderStatus.CONFIRMED,
        )
        handoff_today = Order(
            user_id=current_user.id,
            order_number="ORD-HANDOFF",
            customer_name="Handoff Hero",
            customer_email="handoff@example.com",
            due_date=datetime(2026, 3, 13, 18, 0, tzinfo=timezone.utc),
            total_amount=110.0,
            subtotal=110.0,
            balance_due=0.0,
            status=OrderStatus.CONFIRMED,
            payment_status="paid_in_full",
        )
        watch = Order(
            user_id=current_user.id,
            order_number="ORD-WATCH",
            customer_name="Future Watch",
            customer_email="watch@example.com",
            due_date=datetime(2026, 3, 19, 10, 0, tzinfo=timezone.utc),
            total_amount=90.0,
            subtotal=90.0,
            balance_due=0.0,
            status=OrderStatus.CONFIRMED,
            payment_status="paid_in_full",
        )
        session.add(invoice_blocked)
        session.add(payment_now)
        session.add(handoff_today)
        session.add(watch)
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

    by_number = {order.order_number: order for order in payload}

    assert by_number["ORD-PAYMENT"].ops_summary.action_class == "payment_now"
    assert by_number["ORD-PAYMENT"].queue_summary.urgency_label == "Next up"
    assert by_number["ORD-PAYMENT"].queue_summary.urgency_rank == 2
    assert by_number["ORD-PAYMENT"].ops_summary.primary_cta_label == "Collect payment"
    assert by_number["ORD-PAYMENT"].ops_summary.primary_cta_panel == "payment"
    assert by_number["ORD-PAYMENT"].ops_summary.primary_cta_path == (
        f"/orders/{by_number['ORD-PAYMENT'].id}?panel=payment"
    )

    assert by_number["ORD-INVOICE"].ops_summary.action_class == "invoice_blocked"
    assert by_number["ORD-INVOICE"].ops_summary.primary_cta_label == "Finish invoice"
    assert by_number["ORD-INVOICE"].ops_summary.primary_cta_panel == "invoice"
    assert by_number["ORD-INVOICE"].queue_summary.urgency_label == "Watch"

    assert by_number["ORD-HANDOFF"].ops_summary.action_class == "handoff_today"
    assert by_number["ORD-HANDOFF"].ops_summary.primary_cta_label == "Prep handoff"
    assert by_number["ORD-HANDOFF"].ops_summary.primary_cta_panel == "handoff"
    assert by_number["ORD-HANDOFF"].queue_summary.urgency_label == "Today"
    assert by_number["ORD-HANDOFF"].queue_summary.urgency_rank == 1

    assert by_number["ORD-WATCH"].ops_summary.action_class == "watch"
    assert by_number["ORD-WATCH"].ops_summary.primary_cta_label == "Review order"
    assert by_number["ORD-WATCH"].ops_summary.primary_cta_panel == "review"
    assert by_number["ORD-WATCH"].queue_summary.urgency_label == "Watch"
    assert by_number["ORD-WATCH"].queue_summary.urgency_rank == 3


def test_read_order_endpoint_returns_action_specific_primary_cta(monkeypatch):
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
            email="bm012-detail@example.com",
            hashed_password="not-used",
            is_active=True,
            is_superuser=False,
        )
        session.add(current_user)
        order = Order(
            user_id=current_user.id,
            order_number="ORD-DETAIL",
            customer_name="Detail Test",
            customer_email="detail@example.com",
            due_date=datetime(2026, 3, 13, 18, 0, tzinfo=timezone.utc),
            total_amount=110.0,
            subtotal=110.0,
            balance_due=0.0,
            status=OrderStatus.CONFIRMED,
            payment_status="paid_in_full",
        )
        session.add(order)
        session.commit()
        session.refresh(order)

        payload = asyncio.run(
            read_order(
                session=session,
                order_id=order.id,
                current_user=current_user,
            )
        )

    assert payload.ops_summary.primary_cta_label == "Prep handoff"
    assert payload.ops_summary.primary_cta_panel == "handoff"
    assert payload.ops_summary.primary_cta_path == f"/orders/{order.id}?panel=handoff"


def test_read_orders_endpoint_uses_review_payment_cta_for_overdue_open_balance_without_schedule(
    monkeypatch,
):
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
            email="bm012-review-payment@example.com",
            hashed_password="not-used",
            is_active=True,
            is_superuser=False,
        )
        session.add(current_user)
        order = Order(
            user_id=current_user.id,
            order_number="ORD-REVIEW-PAYMENT",
            customer_name="Review Payment",
            customer_email="review@example.com",
            due_date=datetime(2026, 3, 12, 18, 0, tzinfo=timezone.utc),
            total_amount=160.0,
            subtotal=160.0,
            balance_due=160.0,
            status=OrderStatus.CONFIRMED,
        )
        session.add(order)
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

    assert payload[0].ops_summary.action_class == "payment_now"
    assert payload[0].ops_summary.next_action == "Contact customer about overdue order"
    assert payload[0].ops_summary.primary_cta_label == "Review payment"
    assert payload[0].ops_summary.primary_cta_panel == "payment"
    assert payload[0].ops_summary.primary_cta_path == f"/orders/{payload[0].id}?panel=payment"
