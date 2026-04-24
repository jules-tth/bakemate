import asyncio
from datetime import datetime, timezone
from uuid import uuid4

import app.services.order_service as order_service_module
from app.models.order import OrderCreate, OrderItemCreate, OrderStatus
from app.models.user import User
from app.services.order_service import OrderService
from sqlalchemy.pool import StaticPool
from sqlmodel import SQLModel, Session, create_engine


def test_bm032_contact_focus_marks_order_ready_to_contact(monkeypatch):
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
            email="bm032-ready@example.com",
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
                    customer_name="Reachable Customer",
                    customer_email="reachable@example.com",
                    customer_phone="555-111-2222",
                    due_date=datetime(2026, 3, 20, 15, 0, tzinfo=timezone.utc),
                    delivery_method="pickup",
                    status=OrderStatus.CONFIRMED,
                    items=[
                        OrderItemCreate(
                            name="Birthday Cake",
                            description="Chocolate cake",
                            quantity=1,
                            unit_price=85.0,
                        )
                    ],
                ),
            )
        )

    assert order.contact_focus_summary.customer_display_name == "Reachable Customer"
    assert order.contact_focus_summary.readiness_label == "Ready to contact"
    assert order.contact_focus_summary.best_contact_methods_summary == (
        "Email: reachable@example.com • Phone: 555-111-2222"
    )
    assert order.contact_focus_summary.missing_basics == []
    assert order.contact_focus_summary.next_step == "Use the saved contact details"


def test_bm032_contact_focus_calls_out_limited_and_missing_contact_basics(monkeypatch):
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
            email="bm032-missing@example.com",
            hashed_password="not-used",
            is_active=True,
            is_superuser=False,
        )
        session.add(current_user)
        session.commit()

        service = OrderService(session=session)
        limited_order = asyncio.run(
            service.create_order(
                current_user=current_user,
                order_in=OrderCreate(
                    customer_name="Email Only Customer",
                    customer_email="email-only@example.com",
                    due_date=datetime(2026, 3, 19, 18, 0, tzinfo=timezone.utc),
                    delivery_method="pickup",
                    status=OrderStatus.CONFIRMED,
                    deposit_amount=30.0,
                    deposit_due_date=datetime(2026, 3, 18, 0, 0, tzinfo=timezone.utc).date(),
                    items=[OrderItemCreate(name="Cake", quantity=1, unit_price=60.0)],
                ),
            )
        )
        missing_order = asyncio.run(
            service.create_order(
                current_user=current_user,
                order_in=OrderCreate(
                    due_date=datetime(2026, 3, 20, 16, 0, tzinfo=timezone.utc),
                    status=OrderStatus.CONFIRMED,
                    items=[OrderItemCreate(name="Cupcakes", quantity=1, unit_price=24.0)],
                ),
            )
        )

    assert limited_order.contact_focus_summary.readiness_label == "Limited contact info"
    assert limited_order.contact_focus_summary.best_contact_methods_summary == "Email only: email-only@example.com"
    assert limited_order.contact_focus_summary.missing_basics == [
        "No phone number on file — live follow-up may be slower if questions come up.",
        "Only one direct contact path is on file — follow-up fallback is thin if that method fails.",
    ]
    assert limited_order.contact_focus_summary.next_step == "Add a phone backup if you reach the customer"

    assert missing_order.contact_focus_summary.readiness_label == "Missing contact basics"
    assert missing_order.contact_focus_summary.customer_display_name == "Customer name still missing"
    assert missing_order.contact_focus_summary.best_contact_methods_summary == "No usable email or phone on file"
    assert missing_order.contact_focus_summary.missing_basics == [
        "Customer name is missing — confirm who this order belongs to before follow-up.",
        "No phone number on file — live follow-up may be slower if questions come up.",
        "No email on file — written follow-up and invoice delivery backup are limited.",
    ]
    assert missing_order.contact_focus_summary.next_step == "Confirm the customer identity first"
