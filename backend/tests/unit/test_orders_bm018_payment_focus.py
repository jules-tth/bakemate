import asyncio
from datetime import date, datetime, timezone
from uuid import uuid4

import app.services.order_service as order_service_module
from app.services.order_service import OrderService
from app.models.order import OrderCreate, OrderItemCreate, OrderStatus, OrderUpdate, PaymentStatus
from app.models.user import User
from sqlalchemy.pool import StaticPool
from sqlmodel import SQLModel, Session, create_engine


def test_payment_focus_summary_prioritizes_overdue_deposit_context(monkeypatch):
    monkeypatch.setattr(
        order_service_module,
        "_utcnow",
        lambda: datetime(2026, 3, 14, 13, 0, tzinfo=timezone.utc),
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
            email="bm018@example.com",
            hashed_password="not-used",
            is_active=True,
            is_superuser=False,
        )
        session.add(current_user)
        session.commit()
        session.refresh(current_user)

        service = OrderService(session=session)
        order = asyncio.run(
            service.create_order(
                current_user=current_user,
                order_in=OrderCreate(
                    due_date=datetime(2026, 3, 18, 15, 0, tzinfo=timezone.utc),
                    customer_name="Deposit Test",
                    customer_email="deposit@example.com",
                    deposit_amount=60.0,
                    deposit_due_date=date(2026, 3, 13),
                    balance_due_date=date(2026, 3, 18),
                    status=OrderStatus.CONFIRMED,
                    items=[OrderItemCreate(name="Cake", quantity=1, unit_price=180.0)],
                ),
            )
        )

    assert order.payment_focus_summary.amount_owed_now == 60.0
    assert order.payment_focus_summary.collection_stage == "deposit"
    assert order.payment_focus_summary.payment_state == "Deposit still needed"
    assert "Deposit overdue since Mar 13, 2026" in order.payment_focus_summary.deposit_status
    assert order.payment_focus_summary.balance_status == "Balance will unlock after the deposit is collected"
    assert order.payment_focus_summary.due_timing == "Next payment checkpoint: deposit on Mar 13, 2026."
    assert "Deposit is overdue." in order.payment_focus_summary.risk_note
    assert order.payment_focus_summary.next_step == "Collect overdue deposit"
    assert "Deposit due Mar 13, 2026" in order.payment_focus_summary.next_step_detail


def test_payment_focus_summary_shows_final_balance_after_deposit_is_paid(monkeypatch):
    monkeypatch.setattr(
        order_service_module,
        "_utcnow",
        lambda: datetime(2026, 3, 14, 13, 0, tzinfo=timezone.utc),
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
            email="bm018-balance@example.com",
            hashed_password="not-used",
            is_active=True,
            is_superuser=False,
        )
        session.add(current_user)
        session.commit()
        session.refresh(current_user)

        service = OrderService(session=session)
        order = asyncio.run(
            service.create_order(
                current_user=current_user,
                order_in=OrderCreate(
                    due_date=datetime(2026, 3, 20, 12, 0, tzinfo=timezone.utc),
                    customer_name="Balance Test",
                    customer_email="balance@example.com",
                    deposit_amount=50.0,
                    deposit_due_date=date(2026, 3, 10),
                    balance_due_date=date(2026, 3, 20),
                    status=OrderStatus.CONFIRMED,
                    items=[OrderItemCreate(name="Tiered cake", quantity=1, unit_price=200.0)],
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

    assert order is not None
    assert order.payment_focus_summary.amount_owed_now == 150.0
    assert order.payment_focus_summary.collection_stage == "balance"
    assert order.payment_focus_summary.payment_state == "Waiting on final balance"
    assert order.payment_focus_summary.deposit_status == "Deposit collected"
    assert "Final balance due Mar 20, 2026" in order.payment_focus_summary.balance_status
    assert order.payment_focus_summary.due_timing == "Next payment checkpoint: final balance on Mar 20, 2026."
    assert "A large unpaid balance is still open." in order.payment_focus_summary.risk_note
    assert order.payment_focus_summary.next_step == "Collect final balance"


def test_payment_focus_summary_shows_zero_when_fully_paid(monkeypatch):
    monkeypatch.setattr(
        order_service_module,
        "_utcnow",
        lambda: datetime(2026, 3, 14, 13, 0, tzinfo=timezone.utc),
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
            email="bm020-paid@example.com",
            hashed_password="not-used",
            is_active=True,
            is_superuser=False,
        )
        session.add(current_user)
        session.commit()
        session.refresh(current_user)

        service = OrderService(session=session)
        order = asyncio.run(
            service.create_order(
                current_user=current_user,
                order_in=OrderCreate(
                    due_date=datetime(2026, 3, 20, 12, 0, tzinfo=timezone.utc),
                    customer_name="Paid Test",
                    customer_email="paid@example.com",
                    deposit_amount=50.0,
                    deposit_due_date=date(2026, 3, 10),
                    balance_due_date=date(2026, 3, 20),
                    status=OrderStatus.CONFIRMED,
                    items=[OrderItemCreate(name="Tiered cake", quantity=1, unit_price=200.0)],
                ),
            )
        )
        order = asyncio.run(
            service.update_order(
                order_id=order.id,
                current_user=current_user,
                order_in=OrderUpdate(payment_status=PaymentStatus.PAID_IN_FULL),
            )
        )

    assert order is not None
    assert order.payment_focus_summary.amount_owed_now == 0.0
    assert order.payment_focus_summary.collection_stage == "settled"
    assert order.payment_focus_summary.payment_state == "Paid in full"
    assert order.payment_focus_summary.due_timing == "No money is due right now."


def test_payment_focus_summary_falls_back_to_total_remaining_without_checkpoints(monkeypatch):
    monkeypatch.setattr(
        order_service_module,
        "_utcnow",
        lambda: datetime(2026, 3, 14, 13, 0, tzinfo=timezone.utc),
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
            email="bm020-fallback@example.com",
            hashed_password="not-used",
            is_active=True,
            is_superuser=False,
        )
        session.add(current_user)
        session.commit()
        session.refresh(current_user)

        service = OrderService(session=session)
        order = asyncio.run(
            service.create_order(
                current_user=current_user,
                order_in=OrderCreate(
                    due_date=datetime(2026, 3, 22, 12, 0, tzinfo=timezone.utc),
                    customer_name="Fallback Test",
                    customer_email="fallback@example.com",
                    status=OrderStatus.CONFIRMED,
                    items=[OrderItemCreate(name="Cupcakes", quantity=1, unit_price=96.0)],
                ),
            )
        )

    assert order.payment_focus_summary.amount_owed_now == 96.0
    assert order.payment_focus_summary.collection_stage == "balance"
    assert order.payment_focus_summary.payment_state == "Waiting on final balance"
    assert order.payment_focus_summary.due_timing == "Order due date is Sun Mar 22."
