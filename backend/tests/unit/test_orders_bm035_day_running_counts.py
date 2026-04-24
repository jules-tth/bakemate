import asyncio
from datetime import date, datetime, timezone
from uuid import uuid4

import app.services.order_service as order_service_module
from app.api.v1.endpoints.orders import read_day_running_queue_summary, read_orders
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


def test_bm035_day_running_summary_counts_match_current_queue_scope(monkeypatch):
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
            email="bm035@example.com",
            hashed_password="not-used",
            is_active=True,
            is_superuser=False,
        )
        session.add(current_user)

        ready_imported = Order(
            user_id=current_user.id,
            order_number="ORD-READY-IMPORTED",
            customer_name="Imported Ready",
            customer_email="imported-ready@example.com",
            customer_phone="555-000-1111",
            due_date=datetime(2026, 3, 19, 18, 0, tzinfo=timezone.utc),
            delivery_method="pickup",
            total_amount=100.0,
            subtotal=100.0,
            balance_due=0.0,
            status=OrderStatus.CONFIRMED,
            payment_status="paid_in_full",
            internal_notes="Imported row\nLegacy OrderStatusId: 2\nLegacy legacy_status_raw: 2\nready work",
        )
        blocked_imported = Order(
            user_id=current_user.id,
            order_number="ORD-BLOCKED-IMPORTED",
            customer_name="Imported Blocked",
            customer_email="imported-blocked@example.com",
            customer_phone="555-000-2222",
            due_date=datetime(2026, 3, 19, 17, 0, tzinfo=timezone.utc),
            delivery_method="pickup",
            total_amount=60.0,
            subtotal=60.0,
            balance_due=60.0,
            deposit_amount=30.0,
            deposit_due_date=date(2026, 3, 18),
            status=OrderStatus.CONFIRMED,
            internal_notes="Imported row\nLegacy OrderStatusId: 2\nLegacy legacy_status_raw: 2\nblocked work",
        )
        attention_native = Order(
            user_id=current_user.id,
            order_number="ORD-ATTENTION-NATIVE",
            customer_name="Native Attention",
            customer_email="native-attention@example.com",
            customer_phone="555-000-3333",
            due_date=datetime(2026, 3, 19, 19, 0, tzinfo=timezone.utc),
            delivery_method="pickup",
            total_amount=120.0,
            subtotal=120.0,
            balance_due=120.0,
            balance_due_date=date(2026, 3, 20),
            status=OrderStatus.CONFIRMED,
        )
        ready_native = Order(
            user_id=current_user.id,
            order_number="ORD-READY-NATIVE",
            customer_name="Native Ready",
            customer_email="native-ready@example.com",
            customer_phone="555-000-4444",
            due_date=datetime(2026, 3, 19, 20, 0, tzinfo=timezone.utc),
            delivery_method="pickup",
            total_amount=90.0,
            subtotal=90.0,
            balance_due=0.0,
            status=OrderStatus.CONFIRMED,
            payment_status="paid_in_full",
        )
        session.add_all([ready_imported, blocked_imported, attention_native, ready_native])
        session.flush()
        for order, amount in [
            (ready_imported, 100.0),
            (blocked_imported, 60.0),
            (attention_native, 120.0),
            (ready_native, 90.0),
        ]:
            _add_item(session, order, amount)
        session.commit()

        summary = asyncio.run(
            read_day_running_queue_summary(
                session=session,
                status_filter=None,
                imported_only=True,
                search="imported",
                needs_review=None,
                review_reason=None,
                action_class=None,
                urgency=None,
                current_user=current_user,
            )
        )

        blocked_orders = asyncio.run(
            read_orders(
                session=session,
                skip=0,
                limit=100,
                status_filter=None,
                imported_only=True,
                search="imported",
                needs_review=None,
                review_reason=None,
                day_running=OrderDayRunningTriageFilter.BLOCKED,
                action_class=None,
                urgency=None,
                current_user=current_user,
            )
        )
        ready_orders = asyncio.run(
            read_orders(
                session=session,
                skip=0,
                limit=100,
                status_filter=None,
                imported_only=True,
                search="imported",
                needs_review=None,
                review_reason=None,
                day_running=OrderDayRunningTriageFilter.READY,
                action_class=None,
                urgency=None,
                current_user=current_user,
            )
        )
        attention_orders = asyncio.run(
            read_orders(
                session=session,
                skip=0,
                limit=100,
                status_filter=None,
                imported_only=True,
                search="imported",
                needs_review=None,
                review_reason=None,
                day_running=OrderDayRunningTriageFilter.NEEDS_ATTENTION,
                action_class=None,
                urgency=None,
                current_user=current_user,
            )
        )

    assert summary.all_count == 2
    assert summary.blocked_count == 1
    assert summary.needs_attention_count == 0
    assert summary.ready_count == 1

    assert len(blocked_orders) == summary.blocked_count
    assert len(attention_orders) == summary.needs_attention_count
    assert len(ready_orders) == summary.ready_count
    assert [order.order_number for order in blocked_orders] == ["ORD-BLOCKED-IMPORTED"]
    assert [order.order_number for order in ready_orders] == ["ORD-READY-IMPORTED"]


def test_bm035_day_running_summary_counts_match_backend_action_and_urgency_scope(monkeypatch):
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
            email="bm035-scope@example.com",
            hashed_password="not-used",
            is_active=True,
            is_superuser=False,
        )
        session.add(current_user)

        orders = [
            Order(
                user_id=current_user.id,
                order_number="ORD-PAYMENT-BLOCKED",
                customer_name="Payment Blocked",
                customer_email="payment-blocked@example.com",
                customer_phone="555-000-1111",
                due_date=datetime(2026, 3, 19, 16, 0, tzinfo=timezone.utc),
                delivery_method="pickup",
                total_amount=80.0,
                subtotal=80.0,
                balance_due=80.0,
                deposit_amount=40.0,
                deposit_due_date=date(2026, 3, 18),
                status=OrderStatus.CONFIRMED,
            ),
            Order(
                user_id=current_user.id,
                order_number="ORD-PAYMENT-ATTENTION",
                customer_name="Payment Attention",
                customer_email="payment-attention@example.com",
                customer_phone="555-000-2222",
                due_date=datetime(2026, 3, 20, 17, 0, tzinfo=timezone.utc),
                delivery_method="pickup",
                total_amount=120.0,
                subtotal=120.0,
                balance_due=120.0,
                balance_due_date=date(2026, 3, 20),
                status=OrderStatus.CONFIRMED,
            ),
            Order(
                user_id=current_user.id,
                order_number="ORD-HANDOFF-READY",
                customer_name="Handoff Ready",
                customer_email="handoff-ready@example.com",
                customer_phone="555-000-3333",
                due_date=datetime(2026, 3, 19, 18, 0, tzinfo=timezone.utc),
                delivery_method="pickup",
                total_amount=95.0,
                subtotal=95.0,
                balance_due=0.0,
                status=OrderStatus.CONFIRMED,
                payment_status="paid_in_full",
            ),
            Order(
                user_id=current_user.id,
                order_number="ORD-WATCH-READY",
                customer_name="Watch Ready",
                customer_email="watch-ready@example.com",
                customer_phone="555-000-4444",
                due_date=datetime(2026, 3, 24, 18, 0, tzinfo=timezone.utc),
                delivery_method="pickup",
                total_amount=70.0,
                subtotal=70.0,
                balance_due=0.0,
                status=OrderStatus.CONFIRMED,
                payment_status="paid_in_full",
            ),
        ]
        session.add_all(orders)
        session.flush()
        for order, amount in zip(orders, [80.0, 120.0, 95.0, 70.0]):
            _add_item(session, order, amount)
        session.commit()

        all_orders = asyncio.run(
            read_orders(
                session=session,
                skip=0,
                limit=100,
                status_filter=None,
                imported_only=False,
                search=None,
                needs_review=None,
                review_reason=None,
                day_running=None,
                action_class=None,
                urgency=None,
                current_user=current_user,
            )
        )

        scoped_reference = next(order for order in all_orders if order.order_number == "ORD-PAYMENT-BLOCKED")
        action_class = scoped_reference.ops_summary.action_class
        urgency = scoped_reference.queue_summary.urgency_label
        expected_scoped_orders = [
            order
            for order in all_orders
            if order.ops_summary.action_class == action_class and order.queue_summary.urgency_label == urgency
        ]

        summary = asyncio.run(
            read_day_running_queue_summary(
                session=session,
                status_filter=None,
                imported_only=False,
                search=None,
                needs_review=None,
                review_reason=None,
                action_class=action_class,
                urgency=urgency,
                current_user=current_user,
            )
        )
        blocked_orders = asyncio.run(
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
                action_class=action_class,
                urgency=urgency,
                current_user=current_user,
            )
        )
        ready_orders = asyncio.run(
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
                action_class=action_class,
                urgency=urgency,
                current_user=current_user,
            )
        )
        attention_orders = asyncio.run(
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
                action_class=action_class,
                urgency=urgency,
                current_user=current_user,
            )
        )

    assert summary.all_count == len(expected_scoped_orders)
    assert summary.blocked_count == len(blocked_orders)
    assert summary.needs_attention_count == len(attention_orders)
    assert summary.ready_count == len(ready_orders)
    assert summary.all_count == summary.blocked_count + summary.needs_attention_count + summary.ready_count
    assert [order.order_number for order in blocked_orders] == ["ORD-PAYMENT-BLOCKED"]
