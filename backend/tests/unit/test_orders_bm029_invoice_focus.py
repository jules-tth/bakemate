import asyncio
from datetime import date, datetime, timezone
from uuid import uuid4

from app.models.contact import Contact, ContactType
from app.models.order import OrderCreate, OrderItemCreate, OrderStatus, OrderUpdate, PaymentStatus
from app.models.user import User
from app.services.order_service import OrderService
from sqlalchemy.pool import StaticPool
from sqlmodel import SQLModel, Session, create_engine


def test_invoice_focus_summary_surfaces_readiness_identity_and_payment_context():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(engine)

    with Session(engine) as session:
        current_user = User(
            id=uuid4(),
            email="bm029-ready@example.com",
            hashed_password="not-used",
            is_active=True,
            is_superuser=False,
        )
        session.add(current_user)
        session.commit()

        contact = Contact(
            user_id=current_user.id,
            first_name="Mara",
            last_name="Client",
            email="mara@example.com",
            phone="555-0303",
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
                    due_date=datetime(2026, 3, 24, 17, 0, tzinfo=timezone.utc),
                    deposit_amount=80.0,
                    deposit_due_date=date(2026, 3, 21),
                    balance_due_date=date(2026, 3, 24),
                    status=OrderStatus.CONFIRMED,
                    items=[OrderItemCreate(name="Celebration Cake", quantity=1, unit_price=240.0)],
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

    assert order.invoice_focus_summary.status_label == "ready_to_send"
    assert order.invoice_focus_summary.readiness_note == "Invoice basics are complete from the current order record."
    assert order.invoice_focus_summary.order_identity == f"{order.order_number} due Tue Mar 24"
    assert order.invoice_focus_summary.customer_identity == "Mara Client | mara@example.com | 555-0303"
    assert order.invoice_focus_summary.amount_summary == "Invoice total $240.00"
    assert order.invoice_focus_summary.payment_context == (
        "Payment status: deposit paid with $160.00 still due by Mar 24, 2026."
    )
    assert order.invoice_focus_summary.blockers == []
    assert order.invoice_focus_summary.missing_basics == []
    assert order.invoice_focus_summary.next_step == "Confirm final payment timing"
    assert "double-check the remaining amount and due date" in order.invoice_focus_summary.next_step_detail


def test_invoice_focus_summary_calls_out_blockers_and_missing_basics():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(engine)

    with Session(engine) as session:
        current_user = User(
            id=uuid4(),
            email="bm029-blocked@example.com",
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
                    due_date=datetime(2026, 3, 26, 11, 0, tzinfo=timezone.utc),
                    status=OrderStatus.CONFIRMED,
                    items=[],
                ),
            )
        )

    assert order.invoice_focus_summary.status_label == "blocked"
    assert order.invoice_focus_summary.readiness_note == (
        "Invoice is not send-ready yet because key billing basics are still missing."
    )
    assert order.invoice_focus_summary.customer_identity == (
        "Customer identity is still too thin for invoice send confidence."
    )
    assert order.invoice_focus_summary.blockers == [
        "Add a customer name or email before treating the invoice as send-ready.",
        "Add line items so the invoice total reflects the actual order.",
    ]
    assert order.invoice_focus_summary.missing_basics == [
        "Add at least one customer contact method before sending the invoice.",
    ]
    assert order.invoice_focus_summary.next_step == "Complete invoice basics"
    assert order.invoice_focus_summary.next_step_detail == (
        "Add a customer name or email before treating the invoice as send-ready."
    )
