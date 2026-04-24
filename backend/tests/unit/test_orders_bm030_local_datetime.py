import asyncio
from datetime import date, datetime, timezone
from uuid import uuid4

import app.services.order_service as order_service_module
from app.models.contact import Contact, ContactType
from app.models.order import OrderCreate, OrderItemCreate, OrderStatus, OrderUpdate, PaymentStatus
from app.models.user import User
from app.services.order_service import OrderService
from sqlalchemy.pool import StaticPool
from sqlmodel import SQLModel, Session, create_engine


def test_bm030_operator_local_datetime_labels_align_across_surfaces(monkeypatch):
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
            email="bm030@example.com",
            hashed_password="not-used",
            is_active=True,
            is_superuser=False,
        )
        session.add(current_user)
        session.commit()

        contact = Contact(
            user_id=current_user.id,
            first_name="Bakery",
            last_name="Buyer",
            email="buyer@example.com",
            phone="555-0404",
            address_line1="44 Atlantic Ave",
            city="Brooklyn",
            state_province="NY",
            postal_code="11201",
            contact_type=ContactType.CUSTOMER,
        )
        session.add(contact)
        session.commit()
        session.refresh(contact)

        service = OrderService(session=session)
        order = asyncio.run(
            service.create_order(
                current_user=current_user,
                order_in=OrderCreate(
                    customer_contact_id=contact.id,
                    due_date=datetime(2026, 3, 19, 17, 30, tzinfo=timezone.utc),
                    delivery_method="delivery",
                    deposit_amount=90.0,
                    deposit_due_date=date(2026, 3, 19),
                    balance_due_date=date(2026, 3, 21),
                    status=OrderStatus.CONFIRMED,
                    items=[OrderItemCreate(name="Tiered Cake", quantity=1, unit_price=300.0)],
                ),
            )
        )
        order = asyncio.run(
            service.update_order(
                order_id=order.id,
                current_user=current_user,
                order_in=OrderUpdate(payment_status=PaymentStatus.DEPOSIT_PAID),
            )
        )

    assert order.queue_summary.is_due_today is True
    assert order.handoff_focus_summary.handoff_time_label == "Due today — Thu Mar 19 at 1:30 PM ET"
    assert order.review_focus_summary.due_label == "Due today — Thu Mar 19 at 1:30 PM ET"
    assert order.invoice_focus_summary.order_identity == f"{order.order_number} due Thu Mar 19"
    assert order.invoice_focus_summary.payment_context == (
        "Payment status: deposit paid with $210.00 still due by Mar 21, 2026."
    )
    assert order.payment_focus_summary.deposit_status == "Deposit collected"
    assert order.payment_focus_summary.balance_status == (
        "Final balance due Mar 21, 2026 ($210.00 still open)"
    )
    assert order.payment_focus_summary.due_timing == (
        "Next payment checkpoint: final balance on Mar 21, 2026."
    )


def test_bm030_date_only_payment_copy_stays_date_only(monkeypatch):
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
            email="bm030-date-only@example.com",
            hashed_password="not-used",
            is_active=True,
            is_superuser=False,
        )
        session.add(current_user)
        session.commit()

        service = OrderService(session=session)
        order = asyncio.run(
            service.create_order(
                current_user=current_user,
                order_in=OrderCreate(
                    customer_name="Date Only",
                    due_date=datetime(2026, 3, 22, 15, 0, tzinfo=timezone.utc),
                    deposit_amount=60.0,
                    deposit_due_date=date(2026, 3, 20),
                    status=OrderStatus.CONFIRMED,
                    items=[OrderItemCreate(name="Cookies", quantity=12, unit_price=3.0)],
                ),
            )
        )

    assert order.payment_focus_summary.deposit_status == "Deposit due Mar 20, 2026 ($60.00 still open)"
    assert order.payment_focus_summary.due_timing == "Next payment checkpoint: deposit on Mar 20, 2026."
    assert order.ops_summary.ops_attention == "Deposit due Mar 20, 2026 — 60.00 still unpaid."
    assert "12:00" not in order.payment_focus_summary.deposit_status
    assert "UTC" not in order.payment_focus_summary.due_timing
