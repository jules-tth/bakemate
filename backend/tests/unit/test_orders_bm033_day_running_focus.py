import asyncio
from datetime import date, datetime, timezone
from uuid import uuid4

import app.services.order_service as order_service_module
from app.models.order import OrderCreate, OrderDayRunningFocusSummary, OrderItemCreate, OrderReviewFocusSummary, OrderStatus, OrderUpdate, PaymentStatus
from app.models.user import User
from app.services.order_service import OrderService
from sqlalchemy.pool import StaticPool
from sqlmodel import SQLModel, Session, create_engine


def test_bm033_day_running_focus_marks_order_ready_for_today(monkeypatch):
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
            email="bm033-ready@example.com",
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
                    customer_phone="555-111-2222",
                    due_date=datetime(2026, 3, 19, 18, 0, tzinfo=timezone.utc),
                    delivery_method="pickup",
                    status=OrderStatus.CONFIRMED,
                    notes_to_customer="Vanilla cake with strawberry filling and message plaque.",
                    items=[
                        OrderItemCreate(
                            name="Birthday Cake",
                            description="8-inch vanilla cake with strawberry filling and message plaque",
                            quantity=1,
                            unit_price=85.0,
                        )
                    ],
                ),
            )
        )

    assert order.day_running_focus_summary.readiness_label == "Ready for today"
    assert order.day_running_focus_summary.primary_blocker_category == "none"
    assert order.day_running_focus_summary.primary_blocker_label == "No Obvious Blocker"
    assert order.day_running_focus_summary.reason_summary == (
        "No obvious blocker stands out from the current record for today."
    )
    assert order.day_running_focus_summary.queue_reason_preview is None
    assert order.day_running_focus_summary.queue_next_step_preview is None
    assert order.day_running_focus_summary.queue_payment_preview is None
    assert order.day_running_focus_summary.queue_handoff_preview is None
    assert order.day_running_focus_summary.queue_production_preview is None
    assert order.day_running_focus_summary.queue_invoice_preview is None
    assert order.day_running_focus_summary.next_step == "Proceed with today’s order plan"
    assert order.day_running_focus_summary.supporting_items == []


def test_bm033_day_running_focus_names_attention_preview(monkeypatch):
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
            email="bm033-attention@example.com",
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
                    customer_name="Attention Customer",
                    customer_email="attention@example.com",
                    customer_phone="555-111-3333",
                    due_date=datetime(2026, 3, 19, 17, 0, tzinfo=timezone.utc),
                    delivery_method="pickup",
                    status=OrderStatus.CONFIRMED,
                    deposit_amount=25.0,
                    deposit_due_date=datetime(2026, 3, 20, 0, 0, tzinfo=timezone.utc).date(),
                    items=[
                        OrderItemCreate(
                            name="Cupcakes",
                            description="Chocolate cupcakes with vanilla buttercream",
                            quantity=12,
                            unit_price=3.0,
                        )
                    ],
                ),
            )
        )

    assert order.day_running_focus_summary.readiness_label == "Needs attention today"
    assert order.day_running_focus_summary.primary_blocker_category == "payment"
    assert order.day_running_focus_summary.primary_blocker_label == "Deposit Still Open"
    assert order.day_running_focus_summary.reason_summary == (
        "Deposit is still open (25.00) before handoff."
    )
    assert order.day_running_focus_summary.queue_reason_preview == (
        "Attention: Deposit still open"
    )
    assert order.day_running_focus_summary.queue_next_step_preview == "Next: review deposit"
    assert order.day_running_focus_summary.queue_contact_preview == "Contact: call 555-111-3333"
    assert order.day_running_focus_summary.queue_payment_preview == "Collect: $25.00 deposit"
    assert order.day_running_focus_summary.queue_handoff_preview is None
    assert order.day_running_focus_summary.queue_production_preview is None
    assert order.day_running_focus_summary.next_step == "Review deposit follow-up"
    assert order.day_running_focus_summary.supporting_items == []


def test_bm033_day_running_focus_uses_missing_phone_preview_for_follow_up(monkeypatch):
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
            email="bm033-missing-phone@example.com",
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
                    customer_name="Email Follow Up Customer",
                    customer_email="email-followup@example.com",
                    due_date=datetime(2026, 3, 19, 17, 0, tzinfo=timezone.utc),
                    delivery_method="pickup",
                    status=OrderStatus.CONFIRMED,
                    notes_to_customer="Assorted cookie box with chocolate chip, sugar cookies, and a thank-you note.",
                    deposit_amount=20.0,
                    deposit_due_date=datetime(2026, 3, 20, 0, 0, tzinfo=timezone.utc).date(),
                    items=[
                        OrderItemCreate(
                            name="Cookie Box",
                            description="Assorted cookies",
                            quantity=1,
                            unit_price=40.0,
                        )
                    ],
                ),
            )
        )

    assert order.day_running_focus_summary.readiness_label == "Needs attention today"
    assert order.day_running_focus_summary.queue_next_step_preview == "Next: review deposit"
    assert order.day_running_focus_summary.queue_contact_preview == "Contact: missing phone"
    assert order.day_running_focus_summary.queue_payment_preview == "Collect: $20.00 deposit"
    assert order.day_running_focus_summary.queue_handoff_preview is None


def test_bm033_day_running_focus_names_top_blocker_and_supporting_items(monkeypatch):
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
            email="bm033-blocked@example.com",
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
                    customer_name="Blocked Customer",
                    customer_email="blocked@example.com",
                    due_date=datetime(2026, 3, 19, 17, 0, tzinfo=timezone.utc),
                    status=OrderStatus.CONFIRMED,
                    deposit_amount=30.0,
                    deposit_due_date=datetime(2026, 3, 18, 0, 0, tzinfo=timezone.utc).date(),
                    items=[OrderItemCreate(name="", quantity=0, unit_price=60.0)],
                ),
            )
        )

    assert order.day_running_focus_summary.readiness_label == "Blocked for today"
    assert order.day_running_focus_summary.primary_blocker_category == "handoff"
    assert order.day_running_focus_summary.primary_blocker_label == "Handoff Basics Missing"
    assert order.day_running_focus_summary.reason_summary == (
        "Confirm pickup vs delivery so today’s release plan is clear."
    )
    assert order.day_running_focus_summary.queue_reason_preview == (
        "Blocked: Handoff method not confirmed"
    )
    assert order.day_running_focus_summary.queue_next_step_preview == "Next: lock handoff basics"
    assert order.day_running_focus_summary.queue_contact_preview is None
    assert order.day_running_focus_summary.queue_payment_preview is None
    assert order.day_running_focus_summary.queue_handoff_preview == "Handoff: method needs confirmation"
    assert order.day_running_focus_summary.next_step == "Lock the handoff basics"
    assert order.day_running_focus_summary.supporting_items == [
        "Item names are blank — add a usable item summary before baking.",
        "Deposit is still unpaid for today's work (30.00 open).",
        "Invoice is still missing basics for today.",
    ]


def test_bm033_day_running_focus_previews_production_clue_when_next_step_is_production_related(monkeypatch):
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
            email="bm041-production@example.com",
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
                    customer_name="Production Preview Customer",
                    customer_email="production@example.com",
                    due_date=datetime(2026, 3, 19, 18, 0, tzinfo=timezone.utc),
                    delivery_method="pickup",
                    status=OrderStatus.CONFIRMED,
                    items=[OrderItemCreate(name="Cake", quantity=1, unit_price=65.0)],
                ),
            )
        )

    assert order.day_running_focus_summary.readiness_label == "Needs attention today"
    assert order.day_running_focus_summary.primary_blocker_category == "production"
    assert order.day_running_focus_summary.queue_next_step_preview == "Next: clarify bake details"
    assert order.day_running_focus_summary.queue_production_preview == "Production: flavor needs confirmation"
    assert order.production_focus_summary.readiness_label == "Needs clarification"
    assert order.production_focus_summary.attention_note == (
        "Production details are thin — confirm flavor, theme, message, or design notes before baking."
    )


def test_bm033_day_running_focus_skips_production_preview_for_non_production_exception(monkeypatch):
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
            email="bm041-nonproduction@example.com",
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
                    customer_name="Payment Preview Customer",
                    customer_email="pay@example.com",
                    customer_phone="555-333-4444",
                    due_date=datetime(2026, 3, 19, 17, 0, tzinfo=timezone.utc),
                    delivery_method="pickup",
                    status=OrderStatus.CONFIRMED,
                    deposit_amount=25.0,
                    deposit_due_date=datetime(2026, 3, 20, 0, 0, tzinfo=timezone.utc).date(),
                    items=[
                        OrderItemCreate(
                            name="Cupcakes",
                            description="Chocolate cupcakes with vanilla buttercream",
                            quantity=12,
                            unit_price=3.0,
                        )
                    ],
                ),
            )
        )

    assert order.day_running_focus_summary.readiness_label == "Needs attention today"
    assert order.day_running_focus_summary.primary_blocker_category == "payment"
    assert order.day_running_focus_summary.queue_payment_preview == "Collect: $25.00 deposit"
    assert order.day_running_focus_summary.queue_production_preview is None
    assert order.day_running_focus_summary.queue_invoice_preview is None


def test_bm042_day_running_focus_previews_invoice_clue_for_invoice_exception(monkeypatch):
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
            email="bm042-invoice@example.com",
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
                    customer_name="Invoice Preview Customer",
                    customer_email="invoice-preview@example.com",
                    customer_phone="555-888-9999",
                    due_date=datetime(2026, 3, 19, 17, 0, tzinfo=timezone.utc),
                    delivery_method="pickup",
                    status=OrderStatus.CONFIRMED,
                    notes_to_customer="Detailed floral buttercream cake with inscription and pickup window confirmed.",
                    items=[
                        OrderItemCreate(
                            name="Floral Celebration Cake",
                            description="Buttercream cake with inscription and floral piping",
                            quantity=1,
                            unit_price=0.0,
                        )
                    ],
                ),
            )
        )

    assert order.day_running_focus_summary.readiness_label == "Blocked for today"
    assert order.day_running_focus_summary.primary_blocker_category == "invoice"
    assert order.day_running_focus_summary.queue_reason_preview == "Blocked: Invoice details missing"
    assert order.day_running_focus_summary.queue_next_step_preview == "Next: finish invoice"
    assert order.day_running_focus_summary.queue_invoice_preview == "Invoice: item totals need review"
    assert order.day_running_focus_summary.queue_payment_preview is None


def test_bm042_queue_reason_preview_uses_compact_issue_statement_shape_for_contact_backup():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(engine)

    with Session(engine) as session:
        service = OrderService(session=session)
        assert service._build_queue_reason_preview(
            readiness_label="Needs attention today",
            reason_summary="contact fallback is thin",
        ) == "Attention: Backup contact info missing"


def test_bm044_queue_next_step_preview_aligns_contact_action_terminology():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(engine)

    with Session(engine) as session:
        service = OrderService(session=session)
        assert service._build_queue_next_step_preview(
            next_step="Use the saved contact details",
            reason_summary="contact fallback is thin",
        ) == "Next: use contact info"


def test_bm045_queue_next_step_preview_uses_consistent_action_shape_for_similar_cards():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(engine)

    with Session(engine) as session:
        service = OrderService(session=session)
        assert service._build_queue_next_step_preview(
            next_step="Review final balance collection",
            reason_summary="Final balance is still open for today's handoff (140.00).",
        ) == "Next: review balance collection"
        assert service._build_queue_next_step_preview(
            next_step="Confirm delivery release details",
            reason_summary="Add the delivery destination before this order leaves the kitchen.",
        ) == "Next: confirm delivery handoff"
        assert service._build_queue_next_step_preview(
            next_step="Confirm pickup handoff details",
            reason_summary="Confirm who is collecting the pickup order.",
        ) == "Next: confirm pickup handoff"


def test_bm047_queue_reason_preview_names_targets_in_generic_fallback_cases():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(engine)

    with Session(engine) as session:
        service = OrderService(session=session)
        assert service._build_queue_reason_preview(
            readiness_label="Blocked for today",
            reason_summary="production basics missing",
        ) == "Blocked: Bake details missing"
        assert service._build_queue_reason_preview(
            readiness_label="Needs attention today",
            reason_summary="production details need clarification",
        ) == "Attention: Bake details need clarification"
        assert service._build_queue_reason_preview(
            readiness_label="Blocked for today",
            reason_summary="contact basics missing",
        ) == "Blocked: Contact info missing"
        assert service._build_queue_reason_preview(
            readiness_label="Blocked for today",
            reason_summary="handoff basics missing",
        ) == "Blocked: Handoff basics missing"
        assert service._build_queue_reason_preview(
            readiness_label="Blocked for today",
            reason_summary="Confirm pickup vs delivery so today’s release plan is clear.",
        ) == "Blocked: Handoff method not confirmed"


def test_bm048_queue_next_step_preview_uses_matching_bake_target_terms_for_production_exceptions():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(engine)

    with Session(engine) as session:
        service = OrderService(session=session)
        assert service._build_queue_next_step_preview(
            next_step="Lock the missing production basics",
            reason_summary="production basics missing",
        ) == "Next: lock bake details"
        assert service._build_queue_next_step_preview(
            next_step="Confirm production details",
            reason_summary="production details need clarification",
        ) == "Next: clarify bake details"


def test_bm033_day_running_focus_previews_final_balance_when_collection_is_current(monkeypatch):
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
            email="bm033-balance-preview@example.com",
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
                    customer_name="Balance Preview Customer",
                    customer_email="balance-preview@example.com",
                    customer_phone="555-444-5555",
                    due_date=datetime(2026, 3, 19, 17, 0, tzinfo=timezone.utc),
                    delivery_method="pickup",
                    status=OrderStatus.CONFIRMED,
                    deposit_amount=60.0,
                    deposit_due_date=date(2026, 3, 10),
                    balance_due_date=date(2026, 3, 19),
                    notes_to_customer="Custom birthday cake with vanilla sponge, floral piping, and gold message plaque.",
                    items=[
                        OrderItemCreate(
                            name="Birthday Cake",
                            description="Custom vanilla sponge cake with floral piping and gold message plaque",
                            quantity=1,
                            unit_price=200.0,
                        )
                    ],
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
    assert order.day_running_focus_summary.primary_blocker_category == "payment"
    assert order.day_running_focus_summary.queue_next_step_preview == "Next: collect balance"
    assert order.day_running_focus_summary.queue_payment_preview == "Collect: $140.00 balance"
    assert order.day_running_focus_summary.queue_handoff_preview is None


def test_bm033_day_running_focus_skips_payment_preview_for_non_payment_exception(monkeypatch):
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
            email="bm033-no-payment-preview@example.com",
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
                    customer_name="Handoff Customer",
                    customer_email="handoff@example.com",
                    due_date=datetime(2026, 3, 19, 17, 0, tzinfo=timezone.utc),
                    status=OrderStatus.CONFIRMED,
                    items=[OrderItemCreate(name="", quantity=0, unit_price=60.0)],
                ),
            )
        )

    assert order.day_running_focus_summary.readiness_label == "Blocked for today"
    assert order.day_running_focus_summary.primary_blocker_category == "handoff"
    assert order.day_running_focus_summary.queue_payment_preview is None
    assert order.day_running_focus_summary.queue_handoff_preview == "Handoff: method needs confirmation"



def test_bm033_day_running_focus_previews_pickup_handoff_context(monkeypatch):
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
            email="bm033-pickup-handoff@example.com",
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
                    customer_name="Pickup Customer",
                    due_date=datetime(2026, 3, 19, 18, 30, tzinfo=timezone.utc),
                    delivery_method="pickup",
                    status=OrderStatus.CONFIRMED,
                    items=[OrderItemCreate(name="Cake", quantity=1, unit_price=120.0)],
                ),
            )
        )

    assert order.day_running_focus_summary.readiness_label == "Blocked for today"
    assert order.day_running_focus_summary.primary_blocker_category == "handoff"
    assert order.day_running_focus_summary.queue_handoff_preview == "Handoff: pickup contact needs confirmation"



def test_bm033_day_running_focus_previews_delivery_handoff_context_when_handoff_is_primary(monkeypatch):
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
            email="bm033-delivery-handoff@example.com",
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
                    customer_name="Delivery Customer",
                    customer_email="delivery@example.com",
                    due_date=datetime(2026, 3, 19, 18, 0, tzinfo=timezone.utc),
                    delivery_method="delivery",
                    status=OrderStatus.CONFIRMED,
                    items=[OrderItemCreate(name="Cake", quantity=1, unit_price=85.0)],
                ),
            )
        )

    assert order.day_running_focus_summary.readiness_label == "Blocked for today"
    assert order.day_running_focus_summary.primary_blocker_category == "handoff"
    assert order.day_running_focus_summary.queue_handoff_preview == "Handoff: delivery address needs confirmation"
    assert order.day_running_focus_summary.queue_payment_preview is None


def test_bm043_day_running_focus_previews_generic_review_context_when_no_specialized_preview(monkeypatch):
    monkeypatch.setattr(
        order_service_module,
        "_utcnow",
        lambda: datetime(2026, 3, 20, 5, 0, tzinfo=timezone.utc),
    )
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(engine)

    with Session(engine) as session:
        service = OrderService(session=session)
        review_preview = service._build_day_running_review_preview(
            readiness_label="Needs attention today",
            next_step="Review order basics",
            review_focus_summary=OrderReviewFocusSummary(
                order_number="BM-043-1",
                customer_name="Review Customer",
                due_label="Due today — Thu Mar 20 at 11:00 AM ET",
                status_label="Confirmed",
                item_summary="Birthday Cake + Cupcakes",
                item_count_label="2 items",
                payment_confidence="Payment looks settled.",
                invoice_confidence="Invoice basics are complete.",
                handoff_confidence="Pickup is planned.",
                missing_basics=[],
                risk_note="Core order basics look present from the current record.",
                next_step="Review order",
                next_step_detail="Use the review panel to confirm the basics.",
            ),
            queue_contact_preview=None,
            queue_payment_preview=None,
            queue_handoff_preview=None,
            queue_production_preview=None,
            queue_invoice_preview=None,
        )

    assert review_preview == "Review: 2 items — Birthday Cake + Cupcakes"


def test_bm043_day_running_focus_skips_generic_review_preview_when_specialized_preview_exists(monkeypatch):
    monkeypatch.setattr(
        order_service_module,
        "_utcnow",
        lambda: datetime(2026, 3, 20, 5, 0, tzinfo=timezone.utc),
    )
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(engine)

    with Session(engine) as session:
        service = OrderService(session=session)
        review_preview = service._build_day_running_review_preview(
            readiness_label="Blocked for today",
            next_step="Review order",
            review_focus_summary=OrderReviewFocusSummary(
                order_number="BM-043-2",
                customer_name="Invoice Customer",
                due_label="Due today — Thu Mar 20 at 1:00 PM ET",
                status_label="Confirmed",
                item_summary="Wedding Cake",
                item_count_label="1 item",
                payment_confidence="Payment looks settled.",
                invoice_confidence="Invoice still needs attention: line items",
                handoff_confidence="Pickup is planned.",
                missing_basics=["Invoice basics are incomplete for this order."],
                risk_note="Invoice basics are incomplete for this order.",
                next_step="Review order",
                next_step_detail="Use the review panel to confirm the basics.",
            ),
            queue_contact_preview=None,
            queue_payment_preview=None,
            queue_handoff_preview=None,
            queue_production_preview=None,
            queue_invoice_preview="Invoice: item totals need review",
        )

    assert review_preview is None
