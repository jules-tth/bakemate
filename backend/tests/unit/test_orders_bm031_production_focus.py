import asyncio
from datetime import datetime, timezone
from uuid import uuid4

import app.services.order_service as order_service_module
from app.models.order import OrderCreate, OrderItemCreate, OrderStatus
from app.models.user import User
from app.services.order_service import OrderService
from sqlalchemy.pool import StaticPool
from sqlmodel import SQLModel, Session, create_engine


def test_bm031_production_focus_marks_order_ready_to_make(monkeypatch):
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
            email="bm031-ready@example.com",
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
                    customer_name="Ready Customer",
                    customer_email="ready@example.com",
                    due_date=datetime(2026, 3, 20, 15, 0, tzinfo=timezone.utc),
                    delivery_method="pickup",
                    status=OrderStatus.CONFIRMED,
                    notes_to_customer="Vanilla cake with strawberry filling and gold message plaque.",
                    items=[
                        OrderItemCreate(
                            name="Birthday Cake",
                            description="8-inch vanilla cake with strawberry filling and gold message plaque",
                            quantity=1,
                            unit_price=85.0,
                        )
                    ],
                ),
            )
        )

    assert order.production_focus_summary.readiness_label == "Ready to make"
    assert order.production_focus_summary.contents_summary == "Birthday Cake"
    assert order.production_focus_summary.item_count_label == "1 item"
    assert order.production_focus_summary.missing_basics == []
    assert order.production_focus_summary.next_step == "Proceed with production prep"


def test_bm031_production_focus_calls_out_missing_basics_and_clarification(monkeypatch):
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
            email="bm031-missing@example.com",
            hashed_password="not-used",
            is_active=True,
            is_superuser=False,
        )
        session.add(current_user)
        session.commit()

        service = OrderService(session=session)
        missing_order = asyncio.run(
            service.create_order(
                current_user=current_user,
                order_in=OrderCreate(
                    customer_name="Missing Basics",
                    due_date=datetime(2026, 3, 19, 18, 0, tzinfo=timezone.utc),
                    status=OrderStatus.CONFIRMED,
                    items=[OrderItemCreate(name="", quantity=0, unit_price=0.0)],
                ),
            )
        )
        clarification_order = asyncio.run(
            service.create_order(
                current_user=current_user,
                order_in=OrderCreate(
                    customer_name="Needs Clarification",
                    due_date=datetime(2026, 3, 20, 16, 0, tzinfo=timezone.utc),
                    delivery_method="pickup",
                    status=OrderStatus.CONFIRMED,
                    items=[OrderItemCreate(name="Cake", quantity=1, unit_price=55.0)],
                ),
            )
        )

    assert missing_order.production_focus_summary.readiness_label == "Missing basics"
    assert missing_order.production_focus_summary.missing_basics == [
        "Item names are blank — add a usable item summary before baking.",
        "Quantity/count cue is missing — capture how many items need to be made.",
        "Handoff method is missing — confirm pickup vs delivery before prep starts.",
    ]
    assert missing_order.production_focus_summary.next_step == "Lock the missing production basics"

    assert clarification_order.production_focus_summary.readiness_label == "Needs clarification"
    assert clarification_order.production_focus_summary.missing_basics == [
        "Production details are thin — confirm flavor, theme, message, or design notes before baking."
    ]
    assert clarification_order.production_focus_summary.next_step == "Confirm production details"
