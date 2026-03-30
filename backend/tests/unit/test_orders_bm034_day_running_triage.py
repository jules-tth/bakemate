import asyncio
from datetime import date, datetime, timezone
from uuid import uuid4

import app.services.order_service as order_service_module
from app.api.v1.endpoints.orders import read_orders
from app.models.order import Order, OrderDayRunningTriageFilter, OrderItem, OrderStatus
from app.models.user import User
from sqlalchemy.pool import StaticPool
from sqlmodel import SQLModel, Session, create_engine


def _add_item(session: Session, order: Order, amount: float) -> None:
    session.add(
        OrderItem(
            order_id=order.id,
            name="Cake",
            description="Vanilla cake with buttercream",
            quantity=1,
            unit_price=amount,
            total_price=amount,
        )
    )


def test_bm034_read_orders_endpoint_filters_by_day_running_readiness(monkeypatch):
    monkeypatch.setattr(
        order_service_module,
        "_utcnow",
        lambda: datetime(2026, 3, 19, 13, 0, tzinfo=timezone.utc),
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
            email="bm034@example.com",
            hashed_password="not-used",
            is_active=True,
            is_superuser=False,
        )
        session.add(current_user)

        ready_order = Order(
            user_id=current_user.id,
            order_number="ORD-READY",
            customer_name="Ready Customer",
            customer_email="ready@example.com",
            customer_phone="555-111-2222",
            due_date=datetime(2026, 3, 19, 18, 0, tzinfo=timezone.utc),
            delivery_method="pickup",
            total_amount=85.0,
            subtotal=85.0,
            balance_due=0.0,
            status=OrderStatus.CONFIRMED,
            payment_status="paid_in_full",
        )
        blocked_order = Order(
            user_id=current_user.id,
            order_number="ORD-BLOCKED",
            customer_name="Blocked Customer",
            customer_email="blocked@example.com",
            customer_phone="555-222-3333",
            due_date=datetime(2026, 3, 19, 17, 0, tzinfo=timezone.utc),
            delivery_method="pickup",
            total_amount=60.0,
            subtotal=60.0,
            balance_due=60.0,
            deposit_amount=30.0,
            deposit_due_date=date(2026, 3, 18),
            status=OrderStatus.CONFIRMED,
        )
        attention_order = Order(
            user_id=current_user.id,
            order_number="ORD-ATTENTION",
            customer_name="Attention Customer",
            customer_email="attention@example.com",
            customer_phone="555-333-4444",
            due_date=datetime(2026, 3, 19, 19, 0, tzinfo=timezone.utc),
            delivery_method="pickup",
            total_amount=120.0,
            subtotal=120.0,
            balance_due=120.0,
            balance_due_date=date(2026, 3, 20),
            status=OrderStatus.CONFIRMED,
        )
        session.add_all([ready_order, blocked_order, attention_order])
        session.flush()
        _add_item(session, ready_order, 85.0)
        _add_item(session, blocked_order, 60.0)
        _add_item(session, attention_order, 120.0)
        session.commit()

        blocked_payload = asyncio.run(
            read_orders(
                session=session,
                skip=0,
                limit=100,
                status_filter=None,
                imported_only=False,
                search=None,
                needs_review=None,
                review_reason=None,
                day_running=OrderDayRunningTriageFilter.BLOCKED,
                current_user=current_user,
            )
        )
        attention_payload = asyncio.run(
            read_orders(
                session=session,
                skip=0,
                limit=100,
                status_filter=None,
                imported_only=False,
                search=None,
                needs_review=None,
                review_reason=None,
                day_running=OrderDayRunningTriageFilter.NEEDS_ATTENTION,
                current_user=current_user,
            )
        )
        ready_payload = asyncio.run(
            read_orders(
                session=session,
                skip=0,
                limit=100,
                status_filter=None,
                imported_only=False,
                search=None,
                needs_review=None,
                review_reason=None,
                day_running=OrderDayRunningTriageFilter.READY,
                current_user=current_user,
            )
        )

    assert [order.order_number for order in blocked_payload] == ["ORD-BLOCKED"]
    assert blocked_payload[0].day_running_focus_summary.readiness_label == "Blocked for today"

    assert [order.order_number for order in attention_payload] == ["ORD-ATTENTION"]
    assert attention_payload[0].day_running_focus_summary.readiness_label == "Needs attention today"

    assert [order.order_number for order in ready_payload] == ["ORD-READY"]
    assert ready_payload[0].day_running_focus_summary.readiness_label == "Ready for today"


def test_bm034_day_running_filter_layers_with_existing_action_filter_inputs(monkeypatch):
    monkeypatch.setattr(
        order_service_module,
        "_utcnow",
        lambda: datetime(2026, 3, 19, 13, 0, tzinfo=timezone.utc),
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
            email="bm034-layering@example.com",
            hashed_password="not-used",
            is_active=True,
            is_superuser=False,
        )
        session.add(current_user)

        ready_imported = Order(
            user_id=current_user.id,
            order_number="ORD-READY-IMPORTED",
            customer_name="Imported Ready",
            customer_email="imported@example.com",
            customer_phone="555-000-1111",
            due_date=datetime(2026, 3, 19, 18, 0, tzinfo=timezone.utc),
            delivery_method="pickup",
            total_amount=100.0,
            subtotal=100.0,
            balance_due=0.0,
            status=OrderStatus.CONFIRMED,
            payment_status="paid_in_full",
            internal_notes="Imported row\nLegacy OrderStatusId: 2\nLegacy legacy_status_raw: 2\nReady import",
        )
        ready_native = Order(
            user_id=current_user.id,
            order_number="ORD-READY-NATIVE",
            customer_name="Native Ready",
            customer_email="native@example.com",
            customer_phone="555-222-3333",
            due_date=datetime(2026, 3, 19, 18, 30, tzinfo=timezone.utc),
            delivery_method="pickup",
            total_amount=95.0,
            subtotal=95.0,
            balance_due=0.0,
            status=OrderStatus.CONFIRMED,
            payment_status="paid_in_full",
        )
        blocked_imported = Order(
            user_id=current_user.id,
            order_number="ORD-BLOCKED-IMPORTED",
            customer_name="Imported Blocked",
            customer_email="blocked-imported@example.com",
            customer_phone="555-444-5555",
            due_date=datetime(2026, 3, 19, 16, 0, tzinfo=timezone.utc),
            delivery_method="pickup",
            total_amount=50.0,
            subtotal=50.0,
            balance_due=50.0,
            deposit_amount=25.0,
            deposit_due_date=date(2026, 3, 18),
            status=OrderStatus.CONFIRMED,
            internal_notes="Imported row\nLegacy OrderStatusId: 2\nLegacy legacy_status_raw: 2",
        )
        session.add_all([ready_imported, ready_native, blocked_imported])
        session.flush()
        _add_item(session, ready_imported, 100.0)
        _add_item(session, ready_native, 95.0)
        _add_item(session, blocked_imported, 50.0)
        session.commit()

        payload = asyncio.run(
            read_orders(
                session=session,
                skip=0,
                limit=100,
                status_filter=None,
                imported_only=True,
                search="ready",
                needs_review=None,
                review_reason=None,
                day_running=OrderDayRunningTriageFilter.READY,
                current_user=current_user,
            )
        )

    assert [order.order_number for order in payload] == ["ORD-READY-IMPORTED"]
    assert payload[0].is_imported is True
    assert payload[0].day_running_focus_summary.readiness_label == "Ready for today"
