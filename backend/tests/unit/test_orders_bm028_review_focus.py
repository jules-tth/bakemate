import asyncio
from datetime import date, datetime, timezone
from uuid import uuid4

import app.services.order_service as order_service_module
from app.models.contact import Contact, ContactType
from app.models.order import OrderCreate, OrderItemCreate, OrderStatus
from app.models.user import User
from app.services.order_service import OrderService
from sqlalchemy.pool import StaticPool
from sqlmodel import SQLModel, Session, create_engine


def test_review_focus_summary_surfaces_operator_at_a_glance_context(monkeypatch):
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
            email="bm028-review@example.com",
            hashed_password="not-used",
            is_active=True,
            is_superuser=False,
        )
        session.add(current_user)
        session.commit()

        contact = Contact(
            user_id=current_user.id,
            first_name="Marlene",
            last_name="Buyer",
            email="marlene@example.com",
            phone="555-0222",
            address_line1="9 Baker Lane",
            city="Queens",
            state_province="NY",
            postal_code="11101",
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
                    due_date=datetime(2026, 3, 20, 15, 30, tzinfo=timezone.utc),
                    delivery_method="delivery",
                    deposit_amount=75.0,
                    deposit_due_date=date(2026, 3, 18),
                    balance_due_date=date(2026, 3, 20),
                    status=OrderStatus.CONFIRMED,
                    items=[
                        OrderItemCreate(name="Wedding Cake", quantity=1, unit_price=300.0),
                        OrderItemCreate(name="Cupcakes", quantity=24, unit_price=3.5),
                    ],
                ),
            )
        )

    assert order.review_focus_summary.order_number == order.order_number
    assert order.review_focus_summary.customer_name == "Marlene Buyer"
    assert "Thu Mar 20" in order.review_focus_summary.due_label or "Fri Mar 20" in order.review_focus_summary.due_label
    assert order.review_focus_summary.status_label == "Confirmed"
    assert order.review_focus_summary.item_summary == "Wedding Cake + Cupcakes"
    assert order.review_focus_summary.item_count_label == "25 total items"
    assert order.review_focus_summary.payment_confidence == "Payment follow-up still risky — 384.00 remains open and dated money is overdue."
    assert order.review_focus_summary.invoice_confidence == "Invoice basics are complete."
    assert order.review_focus_summary.handoff_confidence == "Handoff basics are present, but timing should still be rechecked before release."
    assert order.review_focus_summary.missing_basics == ["Payment follow-up is still blocking confidence."]
    assert order.review_focus_summary.risk_note == "Deposit is overdue. A large unpaid balance is still open."
    assert order.review_focus_summary.next_step == "Collect overdue deposit"


def test_review_focus_summary_calls_out_missing_cross_cutting_basics(monkeypatch):
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
            email="bm028-missing@example.com",
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
                    customer_name="Mystery Review",
                    due_date=datetime(2026, 3, 19, 17, 0, tzinfo=timezone.utc),
                    status=OrderStatus.CONFIRMED,
                    items=[],
                ),
            )
        )

    assert order.review_focus_summary.customer_name == "Mystery Review"
    assert order.review_focus_summary.item_summary == "Line items still missing"
    assert order.review_focus_summary.item_count_label == "No item quantity captured"
    assert order.review_focus_summary.payment_confidence == "Payment looks settled."
    assert order.review_focus_summary.invoice_confidence == "Invoice still needs attention: line items"
    assert order.review_focus_summary.handoff_confidence == "Confirm whether this order is pickup or delivery."
    assert order.review_focus_summary.missing_basics == [
        "Add at least one customer contact method.",
        "Add line items so the order contents are clear.",
        "Confirm whether this order is pickup or delivery.",
        "Invoice basics are incomplete for this order.",
    ]
    assert order.review_focus_summary.risk_note == "Add at least one customer contact method."
    assert order.review_focus_summary.next_step == "Complete invoice details"
