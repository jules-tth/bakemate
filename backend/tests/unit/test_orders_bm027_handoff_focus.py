import asyncio
from datetime import datetime, timezone
from uuid import uuid4

import app.services.order_service as order_service_module
from app.models.contact import Contact, ContactType
from app.models.order import OrderCreate, OrderItemCreate, OrderStatus
from app.models.user import User
from app.services.order_service import OrderService
from sqlalchemy.pool import StaticPool
from sqlmodel import SQLModel, Session, create_engine


def test_handoff_focus_summary_surfaces_delivery_contact_destination_and_next_step(monkeypatch):
    monkeypatch.setattr(
        order_service_module,
        "_utcnow",
        lambda: datetime(2026, 3, 18, 14, 0, tzinfo=timezone.utc),
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
            email="bm027-delivery@example.com",
            hashed_password="not-used",
            is_active=True,
            is_superuser=False,
        )
        session.add(current_user)
        session.commit()

        contact = Contact(
            user_id=current_user.id,
            first_name="Dana",
            last_name="Customer",
            email="dana@example.com",
            phone="555-0101",
            address_line1="123 Main St",
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
                    due_date=datetime(2026, 3, 18, 17, 30, tzinfo=timezone.utc),
                    delivery_method="delivery",
                    status=OrderStatus.CONFIRMED,
                    items=[OrderItemCreate(name="Cake", quantity=1, unit_price=85.0)],
                ),
            )
        )

    assert order.handoff_focus_summary.method_status == "delivery"
    assert order.handoff_focus_summary.method_label == "Delivery"
    assert order.handoff_focus_summary.contact_name == "Dana Customer"
    assert order.handoff_focus_summary.primary_contact == "dana@example.com"
    assert order.handoff_focus_summary.secondary_contact == "555-0101"
    assert "123 Main St" in order.handoff_focus_summary.destination_label
    assert order.handoff_focus_summary.readiness_note == "Handoff basics are in place for today."
    assert order.handoff_focus_summary.missing_basics == []
    assert order.handoff_focus_summary.next_step == "Confirm delivery release details"
    assert "saved delivery contact and destination" in order.handoff_focus_summary.next_step_detail


def test_handoff_focus_summary_calls_out_missing_handoff_basics(monkeypatch):
    monkeypatch.setattr(
        order_service_module,
        "_utcnow",
        lambda: datetime(2026, 3, 18, 14, 0, tzinfo=timezone.utc),
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
            email="bm027-missing@example.com",
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
                    customer_name="Mystery Order",
                    due_date=datetime(2026, 3, 18, 16, 0, tzinfo=timezone.utc),
                    status=OrderStatus.CONFIRMED,
                    items=[OrderItemCreate(name="Cupcakes", quantity=1, unit_price=48.0)],
                ),
            )
        )

    assert order.handoff_focus_summary.method_status == "unclear"
    assert order.handoff_focus_summary.primary_contact == "No customer contact details on file"
    assert order.handoff_focus_summary.destination_label == "Method not confirmed"
    assert order.handoff_focus_summary.readiness_note == "Handoff is not ready yet — key basics are still missing."
    assert order.handoff_focus_summary.missing_basics == [
        "Confirm whether this order is pickup or delivery.",
        "Add at least one customer contact method before handoff.",
    ]
    assert order.handoff_focus_summary.next_step == "Lock the handoff basics first"
    assert order.handoff_focus_summary.next_step_detail == "Confirm whether this order is pickup or delivery."
