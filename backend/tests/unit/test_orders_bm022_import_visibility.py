import asyncio
from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy.pool import StaticPool
from sqlmodel import SQLModel, Session, create_engine, select

from app.api.v1.endpoints.orders import read_imported_order_summary, read_order, read_orders
from app.models.contact import Contact, ContactType
from app.models.order import ImportedOrderReviewReason, Order, OrderStatus, PaymentStatus
from app.models.user import User


def test_read_orders_endpoint_supports_imported_search_and_needs_review_filters():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(engine)

    with Session(engine) as session:
        current_user = User(
            id=uuid4(),
            email="bm022@example.com",
            hashed_password="not-used",
            is_active=True,
            is_superuser=False,
        )
        contact = Contact(
            user_id=current_user.id,
            first_name="Ivy",
            last_name="Imported",
            email="ivy@example.com",
            phone="555-1000",
            contact_type=ContactType.CUSTOMER,
        )
        session.add(current_user)
        session.add(contact)
        session.flush()

        session.add(
            Order(
                user_id=current_user.id,
                customer_contact_id=contact.id,
                customer_name="Ivy Imported",
                customer_email="ivy@example.com",
                customer_phone="555-1000",
                order_number="LEG-100",
                status=OrderStatus.CONFIRMED,
                payment_status=PaymentStatus.UNPAID,
                order_date=datetime(2026, 3, 1, 12, 0, tzinfo=timezone.utc),
                due_date=datetime(2026, 3, 20, 12, 0, tzinfo=timezone.utc),
                total_amount=150.0,
                subtotal=150.0,
                balance_due=150.0,
                internal_notes=(
                    "Imported row\n\n"
                    "Legacy OrderStatusId: 7\n"
                    "Legacy legacy_status_raw: 7\n"
                    "Legacy bakemate_status: confirmed"
                ),
            )
        )
        session.add(
            Order(
                user_id=current_user.id,
                customer_name="No Contact Import",
                order_number="LEG-REVIEW",
                status=OrderStatus.INQUIRY,
                payment_status=PaymentStatus.UNPAID,
                order_date=datetime(2026, 3, 2, 12, 0, tzinfo=timezone.utc),
                due_date=datetime(2026, 3, 21, 12, 0, tzinfo=timezone.utc),
                total_amount=0.0,
                subtotal=0.0,
                balance_due=0.0,
                internal_notes=(
                    "Legacy OrderStatusId: 8\n"
                    "Legacy legacy_status_raw: 8\n"
                    "Legacy bakemate_status: cancelled"
                ),
            )
        )
        session.add(
            Order(
                user_id=current_user.id,
                customer_name="Native Order",
                customer_email="native@example.com",
                order_number="ORD-NATIVE",
                status=OrderStatus.CONFIRMED,
                payment_status=PaymentStatus.PAID_IN_FULL,
                order_date=datetime(2026, 3, 3, 12, 0, tzinfo=timezone.utc),
                due_date=datetime(2026, 3, 22, 12, 0, tzinfo=timezone.utc),
                total_amount=95.0,
                subtotal=95.0,
                balance_due=0.0,
                internal_notes="Created in BakeMate",
            )
        )
        session.commit()

        imported_payload = asyncio.run(
            read_orders(
                session=session,
                skip=0,
                limit=100,
                status_filter=None,
                imported_only=True,
                search=None,
                needs_review=None,
                review_reason=None,
                current_user=current_user,
            )
        )
        search_payload = asyncio.run(
            read_orders(
                session=session,
                skip=0,
                limit=100,
                status_filter=None,
                imported_only=True,
                search="ivy@example.com",
                needs_review=None,
                review_reason=None,
                current_user=current_user,
            )
        )
        review_payload = asyncio.run(
            read_orders(
                session=session,
                skip=0,
                limit=100,
                status_filter=None,
                imported_only=True,
                search=None,
                needs_review=True,
                review_reason=None,
                current_user=current_user,
            )
        )
        review_reason_payload = asyncio.run(
            read_orders(
                session=session,
                skip=0,
                limit=100,
                status_filter=None,
                imported_only=True,
                search=None,
                needs_review=None,
                review_reason=ImportedOrderReviewReason.UNLINKED_CONTACT,
                current_user=current_user,
            )
        )

    assert {order.order_number for order in imported_payload} == {"LEG-100", "LEG-REVIEW"}
    assert search_payload[0].order_number == "LEG-100"
    assert search_payload[0].is_imported is True
    assert search_payload[0].legacy_status_raw == "7"
    assert search_payload[0].import_source == "marvelous_creations"
    assert search_payload[0].review_reasons == []
    assert search_payload[0].primary_review_reason is None
    assert search_payload[0].review_next_check is None
    assert search_payload[0].imported_priority_label == "Ready after review pile"
    assert [order.order_number for order in review_payload] == ["LEG-REVIEW"]
    assert review_payload[0].review_reasons == [
        ImportedOrderReviewReason.INVOICE_MISSING_FIELDS,
        ImportedOrderReviewReason.MISSING_CONTACT_DETAILS,
        ImportedOrderReviewReason.UNLINKED_CONTACT,
    ]
    assert (
        review_payload[0].primary_review_reason
        == ImportedOrderReviewReason.INVOICE_MISSING_FIELDS
    )
    assert "missing invoice basics" in (review_payload[0].review_next_check or "")
    assert [order.order_number for order in review_reason_payload] == ["LEG-REVIEW"]


def test_imported_queue_prioritizes_review_needed_records_and_reason_rank():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(engine)

    with Session(engine) as session:
        current_user = User(
            id=uuid4(),
            email="bm025-priority@example.com",
            hashed_password="not-used",
            is_active=True,
            is_superuser=False,
        )
        contact = Contact(
            user_id=current_user.id,
            first_name="Ready",
            last_name="Import",
            email="ready@example.com",
            phone="555-4400",
            contact_type=ContactType.CUSTOMER,
        )
        session.add(current_user)
        session.add(contact)
        session.flush()
        session.add_all(
            [
                Order(
                    user_id=current_user.id,
                    customer_contact_id=contact.id,
                    customer_name="Ready Import",
                    customer_email="ready@example.com",
                    customer_phone="555-4400",
                    order_number="LEG-READY-LAST",
                    status=OrderStatus.CONFIRMED,
                    payment_status=PaymentStatus.UNPAID,
                    order_date=datetime(2026, 3, 10, 12, 0, tzinfo=timezone.utc),
                    due_date=datetime(2026, 3, 28, 12, 0, tzinfo=timezone.utc),
                    total_amount=90.0,
                    subtotal=90.0,
                    balance_due=90.0,
                    internal_notes="Imported row\nLegacy OrderStatusId: 1\nLegacy legacy_status_raw: 1",
                ),
                Order(
                    user_id=current_user.id,
                    customer_name="Unlinked Import",
                    customer_email="unlinked@example.com",
                    order_number="LEG-UNLINKED",
                    status=OrderStatus.CONFIRMED,
                    payment_status=PaymentStatus.UNPAID,
                    order_date=datetime(2026, 3, 9, 12, 0, tzinfo=timezone.utc),
                    due_date=datetime(2026, 3, 27, 12, 0, tzinfo=timezone.utc),
                    total_amount=120.0,
                    subtotal=120.0,
                    balance_due=120.0,
                    internal_notes="Imported row\nLegacy OrderStatusId: 2\nLegacy legacy_status_raw: 2",
                ),
                Order(
                    user_id=current_user.id,
                    customer_name="Invoice Gap Import",
                    order_number="LEG-INVOICE",
                    status=OrderStatus.INQUIRY,
                    payment_status=PaymentStatus.UNPAID,
                    order_date=datetime(2026, 3, 8, 12, 0, tzinfo=timezone.utc),
                    due_date=datetime(2026, 3, 26, 12, 0, tzinfo=timezone.utc),
                    total_amount=0.0,
                    subtotal=0.0,
                    balance_due=0.0,
                    internal_notes="Imported row\nLegacy OrderStatusId: 3\nLegacy legacy_status_raw: 3",
                ),
                Order(
                    user_id=current_user.id,
                    customer_name="Risk Import",
                    order_number="LEG-RISK-FIRST",
                    status=OrderStatus.CONFIRMED,
                    payment_status=PaymentStatus.UNPAID,
                    order_date=datetime(2026, 3, 7, 12, 0, tzinfo=timezone.utc),
                    due_date=datetime(2026, 3, 25, 12, 0, tzinfo=timezone.utc),
                    total_amount=180.0,
                    subtotal=180.0,
                    balance_due=180.0,
                    deposit_amount=60.0,
                    deposit_due_date=datetime(2026, 3, 1, 0, 0, tzinfo=timezone.utc).date(),
                    internal_notes="Imported row\nLegacy OrderStatusId: 4\nLegacy legacy_status_raw: 4",
                ),
            ]
        )
        session.commit()

        payload = asyncio.run(
            read_orders(
                session=session,
                skip=0,
                limit=100,
                status_filter=None,
                imported_only=True,
                search=None,
                needs_review=None,
                review_reason=None,
                current_user=current_user,
            )
        )

    assert [order.order_number for order in payload] == [
        "LEG-RISK-FIRST",
        "LEG-INVOICE",
        "LEG-UNLINKED",
        "LEG-READY-LAST",
    ]
    assert payload[0].imported_priority_label == "Payment risk first"
    assert payload[1].imported_priority_label == "Invoice fix first"
    assert payload[2].imported_priority_label == "Match contact next"
    assert payload[3].imported_priority_label == "Ready after review pile"
    assert payload[0].review_reasons[0] == ImportedOrderReviewReason.OVERDUE_PAYMENT_RISK


def test_imported_order_summary_returns_review_bucket_counts():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(engine)

    with Session(engine) as session:
        current_user = User(
            id=uuid4(),
            email="bm024-summary@example.com",
            hashed_password="not-used",
            is_active=True,
            is_superuser=False,
        )
        contact = Contact(
            user_id=current_user.id,
            first_name="Ready",
            last_name="Import",
            email="ready@example.com",
            phone="555-3000",
            contact_type=ContactType.CUSTOMER,
        )
        session.add(current_user)
        session.add(contact)
        session.flush()

        session.add(
            Order(
                user_id=current_user.id,
                customer_contact_id=contact.id,
                customer_name="Ready Import",
                customer_email="ready@example.com",
                customer_phone="555-3000",
                order_number="LEG-READY",
                status=OrderStatus.CONFIRMED,
                payment_status=PaymentStatus.UNPAID,
                order_date=datetime(2026, 3, 5, 12, 0, tzinfo=timezone.utc),
                due_date=datetime(2026, 3, 25, 12, 0, tzinfo=timezone.utc),
                total_amount=125.0,
                subtotal=125.0,
                balance_due=125.0,
                internal_notes=(
                    "Imported row\n"
                    "Legacy OrderStatusId: 4\n"
                    "Legacy legacy_status_raw: 4"
                ),
            )
        )
        session.add(
            Order(
                user_id=current_user.id,
                customer_name="Review Import",
                order_number="LEG-REVIEW-2",
                status=OrderStatus.INQUIRY,
                payment_status=PaymentStatus.UNPAID,
                order_date=datetime(2026, 3, 6, 12, 0, tzinfo=timezone.utc),
                due_date=datetime(2026, 3, 26, 12, 0, tzinfo=timezone.utc),
                total_amount=0.0,
                subtotal=0.0,
                balance_due=0.0,
                internal_notes=(
                    "Imported row\n"
                    "Legacy OrderStatusId: 9\n"
                    "Legacy legacy_status_raw: 9"
                ),
            )
        )
        session.commit()

        payload = asyncio.run(
            read_imported_order_summary(
                session=session,
                search=None,
                current_user=current_user,
            )
        )

    assert payload.all_imported_count == 2
    assert payload.needs_review_count == 1
    assert payload.no_current_review_count == 1
    assert (
        payload.review_reason_counts[ImportedOrderReviewReason.INVOICE_MISSING_FIELDS] == 1
    )
    assert (
        payload.review_reason_counts[ImportedOrderReviewReason.MISSING_CONTACT_DETAILS] == 1
    )
    assert payload.review_reason_counts[ImportedOrderReviewReason.UNLINKED_CONTACT] == 1
    assert (
        payload.review_reason_counts[ImportedOrderReviewReason.OVERDUE_PAYMENT_RISK] == 0
    )


def test_imported_order_review_triage_prioritizes_existing_overdue_payment_signal():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(engine)

    with Session(engine) as session:
        current_user = User(
            id=uuid4(),
            email="bm023-review@example.com",
            hashed_password="not-used",
            is_active=True,
            is_superuser=False,
        )
        session.add(current_user)
        session.add(
            Order(
                user_id=current_user.id,
                customer_name="Risky Import",
                order_number="LEG-RISK",
                status=OrderStatus.CONFIRMED,
                payment_status=PaymentStatus.UNPAID,
                order_date=datetime(2026, 3, 4, 12, 0, tzinfo=timezone.utc),
                due_date=datetime(2026, 3, 24, 12, 0, tzinfo=timezone.utc),
                total_amount=180.0,
                subtotal=180.0,
                balance_due=180.0,
                deposit_amount=60.0,
                deposit_due_date=datetime(2026, 3, 1, 0, 0, tzinfo=timezone.utc).date(),
                internal_notes=(
                    "Imported row\n"
                    "Legacy OrderStatusId: 5\n"
                    "Legacy legacy_status_raw: 5"
                ),
            )
        )
        session.commit()
        imported_order = session.exec(select(Order)).first()

        payload = asyncio.run(
            read_order(
                session=session,
                order_id=imported_order.id,
                current_user=current_user,
            )
        )

    assert payload is not None
    assert payload.is_imported is True
    assert payload.review_reasons == [
        ImportedOrderReviewReason.OVERDUE_PAYMENT_RISK,
        ImportedOrderReviewReason.MISSING_CONTACT_DETAILS,
        ImportedOrderReviewReason.UNLINKED_CONTACT,
    ]
    assert (
        payload.primary_review_reason
        == ImportedOrderReviewReason.OVERDUE_PAYMENT_RISK
    )
    assert "overdue payment dates" in (payload.review_next_check or "")


def test_read_order_endpoint_returns_recent_customer_history_for_same_contact():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(engine)

    with Session(engine) as session:
        current_user = User(
            id=uuid4(),
            email="bm022-history@example.com",
            hashed_password="not-used",
            is_active=True,
            is_superuser=False,
        )
        contact = Contact(
            user_id=current_user.id,
            first_name="Casey",
            last_name="Customer",
            email="casey@example.com",
            phone="555-2000",
            contact_type=ContactType.CUSTOMER,
        )
        session.add(current_user)
        session.add(contact)
        session.flush()

        orders = [
            Order(
                user_id=current_user.id,
                customer_contact_id=contact.id,
                customer_name="Casey Customer",
                customer_email="casey@example.com",
                customer_phone="555-2000",
                order_number=f"LEG-HIST-{index}",
                status=OrderStatus.CONFIRMED if index < 5 else OrderStatus.COMPLETED,
                payment_status=PaymentStatus.UNPAID if index < 5 else PaymentStatus.PAID_IN_FULL,
                order_date=datetime(2026, 3, index + 1, 9, 0, tzinfo=timezone.utc),
                due_date=datetime(2026, 3, index + 10, 9, 0, tzinfo=timezone.utc),
                total_amount=100.0 + index,
                subtotal=100.0 + index,
                balance_due=100.0 if index < 5 else 0.0,
                internal_notes=(
                    "Legacy OrderStatusId: 2.0\n"
                    "Legacy legacy_status_raw: 2.0\n"
                    "Legacy bakemate_status: completed"
                )
                if index < 5
                else "Created in BakeMate",
            )
            for index in range(6)
        ]
        for order in orders:
            session.add(order)
        session.commit()
        target_order = orders[4]

        payload = asyncio.run(
            read_order(
                session=session,
                order_id=target_order.id,
                current_user=current_user,
            )
        )

    assert payload is not None
    assert payload.customer_history_summary.total_orders == 6
    assert payload.recent_customer_orders
    assert [item.order_number for item in payload.recent_customer_orders] == [
        "LEG-HIST-5",
        "LEG-HIST-3",
        "LEG-HIST-2",
        "LEG-HIST-1",
    ]
    assert len(payload.recent_customer_orders) == 4
    assert payload.is_imported is True
    assert payload.legacy_status_raw == "2.0"


def test_read_orders_exposes_queue_payment_trust_cue_only_for_imported_legacy_limited_orders():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(engine)

    with Session(engine) as session:
        current_user = User(
            id=uuid4(),
            email="bm062-queue@example.com",
            hashed_password="not-used",
            is_active=True,
            is_superuser=False,
        )
        session.add(current_user)
        session.add(
            Order(
                user_id=current_user.id,
                customer_name="Imported Queue Trust",
                order_number="LEG-QUEUE-1",
                status=OrderStatus.CONFIRMED,
                payment_status=PaymentStatus.UNPAID,
                order_date=datetime(2026, 3, 7, 12, 0, tzinfo=timezone.utc),
                due_date=datetime(2026, 3, 25, 12, 0, tzinfo=timezone.utc),
                total_amount=150.0,
                subtotal=150.0,
                balance_due=150.0,
                internal_notes=(
                    "Legacy OrderStatusId: 2.0\n"
                    "Legacy legacy_status_raw: 2.0\n"
                    "Legacy bakemate_status: confirmed\n"
                    "Legacy AmountPaid: 0"
                ),
            )
        )
        session.add(
            Order(
                user_id=current_user.id,
                customer_name="Native Queue Trust",
                order_number="ORD-QUEUE-1",
                status=OrderStatus.CONFIRMED,
                payment_status=PaymentStatus.UNPAID,
                order_date=datetime(2026, 3, 8, 12, 0, tzinfo=timezone.utc),
                due_date=datetime(2026, 3, 26, 12, 0, tzinfo=timezone.utc),
                total_amount=90.0,
                subtotal=90.0,
                balance_due=90.0,
                internal_notes="Created in BakeMate",
            )
        )
        session.commit()

        payload = asyncio.run(
            read_orders(
                session=session,
                skip=0,
                limit=100,
                status_filter=None,
                imported_only=None,
                search=None,
                needs_review=None,
                review_reason=None,
                current_user=current_user,
            )
        )

    imported = next(order for order in payload if order.order_number == "LEG-QUEUE-1")
    native = next(order for order in payload if order.order_number == "ORD-QUEUE-1")

    assert imported.payment_focus_summary.trust_state == "legacy_limited"
    assert imported.payment_focus_summary.historical_payment_label == "Historical payment: unknown"
    assert "Legacy payment history may be incomplete" in imported.payment_focus_summary.historical_payment_note
    assert imported.review_focus_summary.payment_trust_preview == "Payment trust: legacy-limited"
    assert imported.day_running_focus_summary.queue_payment_trust_preview == "Payment trust: legacy-limited"
    assert native.payment_focus_summary.trust_state == "current"
    assert native.payment_focus_summary.historical_payment_label is None
    assert native.payment_focus_summary.historical_payment_note is None
    assert native.review_focus_summary.payment_trust_preview is None
    assert native.day_running_focus_summary.queue_payment_trust_preview is None


def test_imported_order_payment_focus_marks_legacy_limited_trust_boundary():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(engine)

    with Session(engine) as session:
        current_user = User(
            id=uuid4(),
            email="bm061-imported@example.com",
            hashed_password="not-used",
            is_active=True,
            is_superuser=False,
        )
        session.add(current_user)
        session.add(
            Order(
                user_id=current_user.id,
                customer_name="Imported Payment Trust",
                customer_email="imported-payment@example.com",
                order_number="LEG-PAY-1",
                status=OrderStatus.CONFIRMED,
                payment_status=PaymentStatus.UNPAID,
                order_date=datetime(2026, 3, 7, 12, 0, tzinfo=timezone.utc),
                due_date=datetime(2026, 3, 25, 12, 0, tzinfo=timezone.utc),
                total_amount=150.0,
                subtotal=150.0,
                balance_due=150.0,
                internal_notes=(
                    "Legacy OrderStatusId: 2.0\n"
                    "Legacy legacy_status_raw: 2.0\n"
                    "Legacy bakemate_status: confirmed\n"
                    "Legacy AmountPaid: 0"
                ),
            )
        )
        session.commit()
        imported_order = session.exec(select(Order)).first()
        assert imported_order is not None

        payload = asyncio.run(
            read_order(
                session=session,
                order_id=imported_order.id,
                current_user=current_user,
            )
        )

    assert payload is not None
    assert payload.is_imported is True
    assert payload.payment_focus_summary.trust_state == "legacy_limited"
    assert payload.payment_focus_summary.trust_label == "Imported payment history is legacy-limited"
    assert "conservative payment snapshot" in payload.payment_focus_summary.trust_note
    assert payload.payment_focus_summary.historical_payment_label == "Historical payment: unknown"
    assert "Use a second source" in payload.payment_focus_summary.historical_payment_note
    assert payload.review_focus_summary.payment_trust_preview == "Payment trust: legacy-limited"
    assert payload.day_running_focus_summary.queue_payment_trust_preview == "Payment trust: legacy-limited"


def test_native_order_read_stays_safe_when_no_legacy_metadata_exists():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(engine)

    with Session(engine) as session:
        current_user = User(
            id=uuid4(),
            email="bm022-native@example.com",
            hashed_password="not-used",
            is_active=True,
            is_superuser=False,
        )
        session.add(current_user)
        session.add(
            Order(
                user_id=current_user.id,
                customer_name="Native",
                order_number="ORD-SAFE",
                status=OrderStatus.CONFIRMED,
                payment_status=PaymentStatus.UNPAID,
                order_date=datetime(2026, 3, 7, 12, 0, tzinfo=timezone.utc),
                due_date=datetime(2026, 3, 25, 12, 0, tzinfo=timezone.utc),
                total_amount=50.0,
                subtotal=50.0,
                balance_due=50.0,
                internal_notes="Created in BakeMate",
            )
        )
        session.commit()
        native_order = session.exec(select(Order)).first()
        assert native_order is not None

        payload = asyncio.run(
            read_order(
                session=session,
                order_id=native_order.id,
                current_user=current_user,
            )
        )

    assert payload is not None
    assert payload.is_imported is False
    assert payload.legacy_status_raw is None
    assert payload.import_source is None
    assert payload.review_reasons == []
    assert payload.primary_review_reason is None
    assert payload.review_next_check is None
    assert payload.recent_customer_orders == []
    assert payload.payment_focus_summary.trust_state == "current"
    assert payload.payment_focus_summary.historical_payment_label is None
    assert payload.payment_focus_summary.historical_payment_note is None
    assert payload.review_focus_summary.payment_trust_preview is None
    assert payload.day_running_focus_summary.queue_payment_trust_preview is None
