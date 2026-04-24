from __future__ import annotations

from collections import defaultdict
from datetime import date, datetime, timezone
from io import BytesIO
from typing import Iterable, Optional
from uuid import UUID, uuid4
from zoneinfo import ZoneInfo

from fastapi import HTTPException, status
from sqlalchemy import case, or_
from sqlmodel import Session, select

from app.models.contact import Contact, ContactType
from app.models.order import (
    DayRunningQueueSummary,
    ImportedOrderQueueSummary,
    ImportedOrderReviewReason,
    Order,
    OrderCreate,
    OrderCustomerSummary,
    OrderCustomerHistorySummary,
    OrderDayRunningTriageFilter,
    OrderRecentCustomerOrder,
    OrderHandoffFocusSummary,
    OrderContactFocusSummary,
    OrderDayRunningFocusSummary,
    OrderInvoiceFocusSummary,
    OrderInvoiceSummary,
    OrderItem,
    OrderOpsSummary,
    OrderPaymentFocusSummary,
    OrderPaymentSummary,
    OrderProductionFocusSummary,
    OrderReviewFocusSummary,
    OrderQueueSummary,
    OrderRead,
    OrderRiskSummary,
    OrderStatus,
    OrderUpdate,
    PaymentStatus,
    Quote,
    QuoteCreate,
    QuoteItem,
    QuoteRead,
    QuoteStatus,
    QuoteUpdate,
)
from app.models.user import User
from app.services.order_service_functions import (
    apply_discount,
    calculate_delivery_fee,
    calculate_order_tax,
    calculate_order_total,
    cancel_order,
    get_order_by_id,
    get_order_items,
    get_orders_by_date_range,
    update_order_status,
    validate_order_data,
)


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _build_contact_name(contact: Contact) -> Optional[str]:
    parts = [part for part in [contact.first_name, contact.last_name] if part]
    if parts:
        return " ".join(parts)
    return contact.company_name


def _split_name(full_name: Optional[str]) -> tuple[Optional[str], Optional[str]]:
    if not full_name:
        return None, None
    parts = full_name.strip().split(maxsplit=1)
    if len(parts) == 1:
        return parts[0], None
    return parts[0], parts[1]


def _date_in_user_timezone(value: datetime) -> date:
    return _as_bakery_datetime(value).date()


def _humanize_reason(reason: str) -> str:
    labels = {
        "deposit_overdue": "Deposit is overdue.",
        "balance_overdue": "Final balance is overdue.",
        "order_overdue_with_balance": "The order due date already passed with money still open.",
        "large_unpaid_balance": "A large unpaid balance is still open.",
    }
    return labels.get(reason, reason.replace("_", " ").capitalize() + ".")


def _humanize_invoice_field(field: str) -> str:
    labels = {
        "customer_identity": "Add a customer name or email before treating the invoice as send-ready.",
        "line_items": "Add line items so the invoice total reflects the actual order.",
        "due_date": "Add the order due date before relying on invoice timing.",
    }
    return labels.get(field, field.replace("_", " ").capitalize() + ".")


def _import_review_next_check(reason: ImportedOrderReviewReason) -> str:
    guidance = {
        ImportedOrderReviewReason.OVERDUE_PAYMENT_RISK: "Verify the overdue payment dates and remaining amount before contacting the customer.",
        ImportedOrderReviewReason.INVOICE_MISSING_FIELDS: "Fill the missing invoice basics shown below before treating this import as send-ready.",
        ImportedOrderReviewReason.MISSING_CONTACT_DETAILS: "Confirm at least one working email or phone number on the imported record.",
        ImportedOrderReviewReason.UNLINKED_CONTACT: "Match this imported customer snapshot to a BakeMate contact if the customer is already known.",
    }
    return guidance[reason]


DAY_RUNNING_READINESS_LABELS = {
    OrderDayRunningTriageFilter.BLOCKED: "Blocked for today",
    OrderDayRunningTriageFilter.NEEDS_ATTENTION: "Needs attention today",
    OrderDayRunningTriageFilter.READY: "Ready for today",
}


IMPORT_REVIEW_REASON_PRIORITY = {
    ImportedOrderReviewReason.OVERDUE_PAYMENT_RISK: 0,
    ImportedOrderReviewReason.INVOICE_MISSING_FIELDS: 1,
    ImportedOrderReviewReason.MISSING_CONTACT_DETAILS: 2,
    ImportedOrderReviewReason.UNLINKED_CONTACT: 3,
}

IMPORT_PRIORITY_LABELS = {
    ImportedOrderReviewReason.OVERDUE_PAYMENT_RISK: "Payment risk first",
    ImportedOrderReviewReason.INVOICE_MISSING_FIELDS: "Invoice fix first",
    ImportedOrderReviewReason.MISSING_CONTACT_DETAILS: "Contact info first",
    ImportedOrderReviewReason.UNLINKED_CONTACT: "Match contact next",
}

RECENT_CUSTOMER_HISTORY_LIMIT = 4
BAKERY_TIMEZONE = ZoneInfo("America/New_York")
BAKERY_TIMEZONE_LABEL = "ET"


def _as_bakery_datetime(value: datetime) -> datetime:
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    return value.astimezone(BAKERY_TIMEZONE)


def _format_bakery_date(value: date) -> str:
    return value.strftime("%a %b") + f" {value.day}"


def _format_bakery_date_only(value: date) -> str:
    return value.strftime("%b") + f" {value.day}, {value.year}"


def _format_datetime_label(value: datetime) -> str:
    local_value = _as_bakery_datetime(value)
    return (
        local_value.strftime("%a %b")
        + f" {local_value.day} at {local_value.strftime('%I:%M %p').lstrip('0')} {BAKERY_TIMEZONE_LABEL}"
    )


def _humanize_enum_label(value: str) -> str:
    return value.replace("_", " ").replace("-", " ").title()


def _compact_contact_address(contact: Optional[Contact]) -> Optional[str]:
    if not contact:
        return None
    parts = [
        contact.address_line1,
        contact.address_line2,
        ", ".join(part for part in [contact.city, contact.state_province] if part) or None,
        contact.postal_code,
    ]
    address = ", ".join(part for part in parts if part)
    return address or None


class OrderService:
    """SQL-backed order workflow helpers used by the order endpoints."""

    def __init__(self, session: Optional[Session] = None):
        self.session = session

    async def create_order(self, *, order_in: OrderCreate, current_user: User) -> OrderRead:
        contact = self._resolve_or_create_contact(
            current_user=current_user,
            customer_contact_id=order_in.customer_contact_id,
            customer_name=order_in.customer_name,
            customer_email=order_in.customer_email,
            customer_phone=order_in.customer_phone,
        )
        customer_name = order_in.customer_name or (
            _build_contact_name(contact) if contact else None
        )
        order = Order(
            user_id=current_user.id,
            customer_contact_id=contact.id if contact else None,
            customer_name=customer_name,
            customer_email=order_in.customer_email or (contact.email if contact else None),
            customer_phone=order_in.customer_phone or (contact.phone if contact else None),
            order_number=self._generate_order_number(),
            status=order_in.status or OrderStatus.INQUIRY,
            payment_status=PaymentStatus.UNPAID,
            due_date=order_in.due_date,
            delivery_method=order_in.delivery_method,
            notes_to_customer=order_in.notes_to_customer,
            internal_notes=order_in.internal_notes,
            deposit_amount=order_in.deposit_amount,
            deposit_due_date=order_in.deposit_due_date,
            balance_due_date=order_in.balance_due_date,
        )
        self._replace_order_items(order=order, item_inputs=order_in.items)
        self._recalculate_order_financials(order)
        self.session.add(order)
        self.session.commit()
        self.session.refresh(order)
        return self._build_order_reads([order])[0]

    async def get_orders_by_user(
        self,
        *,
        current_user: User,
        skip: int = 0,
        limit: int = 100,
        status: Optional[OrderStatus] = None,
        imported_only: bool = False,
        search: Optional[str] = None,
        needs_review: Optional[bool] = None,
        review_reason: Optional[ImportedOrderReviewReason] = None,
        day_running: Optional[OrderDayRunningTriageFilter] = None,
        action_class: Optional[str] = None,
        urgency: Optional[str] = None,
    ) -> list[OrderRead]:
        statement = select(Order).where(Order.user_id == current_user.id)
        if status is not None:
            statement = statement.where(Order.status == status)
        search_text = search.strip() if search else None
        if search_text:
            search_pattern = f"%{search_text}%"
            statement = statement.where(
                or_(
                    Order.order_number.ilike(search_pattern),
                    Order.customer_name.ilike(search_pattern),
                    Order.customer_email.ilike(search_pattern),
                    Order.customer_phone.ilike(search_pattern),
                    Order.delivery_method.ilike(search_pattern),
                    Order.notes_to_customer.ilike(search_pattern),
                    Order.internal_notes.ilike(search_pattern),
                )
            )
        active_ordering = case(
            (Order.status.in_([OrderStatus.COMPLETED, OrderStatus.CANCELLED]), 1),
            else_=0,
        )
        statement = statement.order_by(
            active_ordering,
            Order.due_date.asc(),
            Order.created_at.asc(),
        )
        orders = self.session.exec(statement).all()
        order_reads = self._build_order_reads(orders)
        if imported_only:
            order_reads = [
                order_read for order_read in order_reads if order_read.is_imported
            ]
        if needs_review is not None:
            order_reads = [
                order_read
                for order_read in order_reads
                if self._order_needs_review(order_read) is needs_review
            ]
        if review_reason is not None:
            order_reads = [
                order_read
                for order_read in order_reads
                if review_reason in order_read.review_reasons
            ]
        if day_running is not None:
            readiness_label = DAY_RUNNING_READINESS_LABELS[day_running]
            order_reads = [
                order_read
                for order_read in order_reads
                if order_read.day_running_focus_summary.readiness_label == readiness_label
            ]
        if action_class is not None:
            order_reads = [
                order_read
                for order_read in order_reads
                if order_read.ops_summary.action_class == action_class
            ]
        if urgency is not None:
            order_reads = [
                order_read
                for order_read in order_reads
                if order_read.queue_summary.urgency_label == urgency
            ]
        if imported_only:
            order_reads = self._sort_imported_order_reads(order_reads)
        return order_reads[skip : skip + limit]

    async def get_day_running_queue_summary(
        self,
        *,
        current_user: User,
        status: Optional[OrderStatus] = None,
        imported_only: bool = False,
        search: Optional[str] = None,
        needs_review: Optional[bool] = None,
        review_reason: Optional[ImportedOrderReviewReason] = None,
        action_class: Optional[str] = None,
        urgency: Optional[str] = None,
    ) -> DayRunningQueueSummary:
        scoped_orders = await self.get_orders_by_user(
            current_user=current_user,
            status=status,
            imported_only=imported_only,
            search=search,
            needs_review=needs_review,
            review_reason=review_reason,
            action_class=action_class,
            urgency=urgency,
            limit=100_000,
        )

        counts = {
            "Blocked for today": 0,
            "Needs attention today": 0,
            "Ready for today": 0,
        }
        for order in scoped_orders:
            readiness_label = order.day_running_focus_summary.readiness_label
            if readiness_label in counts:
                counts[readiness_label] += 1

        return DayRunningQueueSummary(
            all_count=len(scoped_orders),
            blocked_count=counts["Blocked for today"],
            needs_attention_count=counts["Needs attention today"],
            ready_count=counts["Ready for today"],
        )


    async def get_imported_order_queue_summary(
        self,
        *,
        current_user: User,
        search: Optional[str] = None,
    ) -> ImportedOrderQueueSummary:
        imported_orders = await self.get_orders_by_user(
            current_user=current_user,
            imported_only=True,
            search=search,
            limit=100_000,
        )
        review_reason_counts = {
            reason: 0 for reason in ImportedOrderReviewReason
        }
        needs_review_count = 0

        for order in imported_orders:
            if order.review_reasons:
                needs_review_count += 1
            for reason in order.review_reasons:
                review_reason_counts[reason] += 1

        all_imported_count = len(imported_orders)
        return ImportedOrderQueueSummary(
            all_imported_count=all_imported_count,
            needs_review_count=needs_review_count,
            no_current_review_count=all_imported_count - needs_review_count,
            review_reason_counts=review_reason_counts,
        )

    async def get_order_by_id(
        self, *, order_id: UUID, current_user: User
    ) -> Optional[OrderRead]:
        order = self._get_owned_order(order_id=order_id, user_id=current_user.id)
        if not order:
            return None
        return self._build_order_reads([order])[0]

    async def update_order(
        self, *, order_id: UUID, order_in: OrderUpdate, current_user: User
    ) -> Optional[OrderRead]:
        order = self._get_owned_order(order_id=order_id, user_id=current_user.id)
        if not order:
            return None

        update_data = order_in.model_dump(exclude_unset=True)
        contact = None
        if any(
            field in update_data
            for field in ["customer_contact_id", "customer_name", "customer_email", "customer_phone"]
        ):
            contact = self._resolve_or_create_contact(
                current_user=current_user,
                customer_contact_id=update_data.get("customer_contact_id"),
                customer_name=update_data.get("customer_name", order.customer_name),
                customer_email=update_data.get("customer_email", order.customer_email),
                customer_phone=update_data.get("customer_phone", order.customer_phone),
            )
            order.customer_contact_id = contact.id if contact else None
            order.customer_name = update_data.get("customer_name") or (_build_contact_name(contact) if contact else None)
            order.customer_email = update_data.get("customer_email") or (contact.email if contact else None)
            order.customer_phone = update_data.get("customer_phone") or (contact.phone if contact else None)

        for field in [
            "due_date",
            "delivery_method",
            "status",
            "payment_status",
            "notes_to_customer",
            "internal_notes",
            "deposit_amount",
            "deposit_due_date",
            "balance_due_date",
            "stripe_payment_intent_id",
            "stripe_checkout_session_id",
        ]:
            if field in update_data:
                setattr(order, field, update_data[field])

        if "items" in update_data and order_in.items is not None:
            self._replace_order_items(order=order, item_inputs=order_in.items)

        self._recalculate_order_financials(order)
        order.updated_at = _utcnow()
        self.session.add(order)
        self.session.commit()
        self.session.refresh(order)
        return self._build_order_reads([order])[0]

    async def delete_order(
        self, *, order_id: UUID, current_user: User
    ) -> Optional[OrderRead]:
        order = self._get_owned_order(order_id=order_id, user_id=current_user.id)
        if not order:
            return None
        order_read = self._build_order_reads([order])[0]
        self.session.delete(order)
        self.session.commit()
        return order_read

    async def create_stripe_payment_intent(
        self, *, order_id: UUID, current_user: User
    ) -> Optional[str]:
        order = self._get_owned_order(order_id=order_id, user_id=current_user.id)
        if not order:
            return None
        order.stripe_payment_intent_id = f"pi_mock_{order.id.hex[:10]}"
        order.stripe_checkout_session_id = f"cs_mock_{order.id.hex[:10]}"
        order.updated_at = _utcnow()
        self.session.add(order)
        self.session.commit()
        return f"{order.stripe_payment_intent_id}_secret_mock"

    async def handle_stripe_webhook(self, *, payload: str, signature: str) -> bool:
        return bool(payload and signature)

    async def generate_invoice_pdf(
        self, *, order_id: UUID, current_user: User
    ) -> Optional[bytes]:
        order = self._get_owned_order(order_id=order_id, user_id=current_user.id)
        if not order:
            return None

        buffer = BytesIO()
        lines = [
            "%PDF-1.1",
            "1 0 obj<<>>endobj",
            "2 0 obj<< /Length 3 0 R >>stream",
            f"Invoice {order.order_number}",
            f"Customer: {order.customer_name or order.customer_email or 'Unknown'}",
            f"Total: {order.total_amount:.2f}",
            "endstream endobj",
            "3 0 obj 0 endobj",
            "trailer<<>>",
            "%%EOF",
        ]
        buffer.write("\n".join(lines).encode("utf-8"))
        return buffer.getvalue()

    async def get_client_portal_url(
        self, *, order_id: UUID, current_user: User
    ) -> Optional[str]:
        order = self._get_owned_order(order_id=order_id, user_id=current_user.id)
        if not order:
            return None
        return f"/orders/{order.id}"

    async def convert_quote_to_order(
        self, *, quote_id: UUID, current_user: User
    ) -> Optional[OrderRead]:
        quote = self.session.get(Quote, quote_id)
        if not quote or quote.user_id != current_user.id:
            return None
        if quote.status not in {QuoteStatus.ACCEPTED, QuoteStatus.SENT}:
            return None

        order = Order(
            user_id=current_user.id,
            order_number=self._generate_order_number(),
            status=OrderStatus.CONFIRMED,
            payment_status=PaymentStatus.UNPAID,
            due_date=quote.expiry_date or _utcnow(),
            notes_to_customer=quote.notes,
        )
        order.items = [
            OrderItem(
                name=item.name,
                description=item.description,
                quantity=item.quantity,
                unit_price=item.unit_price,
                total_price=round(item.quantity * item.unit_price, 2),
            )
            for item in quote.items
        ]
        self._recalculate_order_financials(order)
        self.session.add(order)
        quote.converted_to_order_id = order.id
        self.session.add(quote)
        self.session.commit()
        self.session.refresh(order)
        return self._build_order_reads([order])[0]

    def _get_owned_order(self, *, order_id: UUID, user_id: UUID) -> Optional[Order]:
        statement = select(Order).where(Order.id == order_id, Order.user_id == user_id)
        return self.session.exec(statement).first()

    def _generate_order_number(self) -> str:
        while True:
            candidate = f"ORD-{_utcnow().strftime('%Y%m%d')}-{uuid4().hex[:6].upper()}"
            exists = self.session.exec(
                select(Order).where(Order.order_number == candidate)
            ).first()
            if not exists:
                return candidate

    def _replace_order_items(self, *, order: Order, item_inputs) -> None:
        order.items = [
            OrderItem(
                name=item.name,
                description=item.description,
                quantity=item.quantity,
                unit_price=item.unit_price,
                total_price=round(item.quantity * item.unit_price, 2),
            )
            for item in item_inputs
        ]

    def _resolve_or_create_contact(
        self,
        *,
        current_user: User,
        customer_contact_id: Optional[UUID],
        customer_name: Optional[str],
        customer_email: Optional[str],
        customer_phone: Optional[str],
    ) -> Optional[Contact]:
        contact: Optional[Contact] = None
        if customer_contact_id:
            contact = self.session.get(Contact, customer_contact_id)
            if not contact or contact.user_id != current_user.id:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Customer contact not found for this user.",
                )
            return contact

        if customer_email:
            contact = self.session.exec(
                select(Contact).where(
                    Contact.user_id == current_user.id, Contact.email == customer_email
                )
            ).first()
        if not contact and customer_phone:
            contact = self.session.exec(
                select(Contact).where(
                    Contact.user_id == current_user.id, Contact.phone == customer_phone
                )
            ).first()
        if contact:
            return contact

        if not any([customer_name, customer_email, customer_phone]):
            return None

        first_name, last_name = _split_name(customer_name)
        contact = Contact(
            user_id=current_user.id,
            first_name=first_name,
            last_name=last_name,
            email=customer_email,
            phone=customer_phone,
            contact_type=ContactType.CUSTOMER,
        )
        self.session.add(contact)
        self.session.flush()
        return contact

    def _recalculate_order_financials(self, order: Order) -> None:
        subtotal = round(sum(item.total_price for item in order.items), 2)
        order.subtotal = subtotal
        order.tax = 0.0
        order.total_amount = round(subtotal + order.tax, 2)

        deposit_required = round(order.deposit_amount or 0.0, 2)
        amount_paid = 0.0
        if order.payment_status == PaymentStatus.DEPOSIT_PAID:
            amount_paid = deposit_required
        elif order.payment_status == PaymentStatus.PAID_IN_FULL:
            amount_paid = order.total_amount
        elif order.payment_status == PaymentStatus.REFUNDED:
            amount_paid = 0.0

        order.balance_due = round(max(order.total_amount - amount_paid, 0.0), 2)

    def _extract_legacy_metadata(self, internal_notes: Optional[str]) -> dict[str, str]:
        if not internal_notes:
            return {}

        metadata: dict[str, str] = {}
        for line in internal_notes.splitlines():
            text = line.strip()
            if not text.startswith("Legacy ") or ":" not in text:
                continue
            key, value = text[len("Legacy ") :].split(":", 1)
            key = key.strip()
            value = value.strip()
            if key and value:
                metadata[key] = value
        return metadata

    def _derive_import_metadata(self, order: Order) -> tuple[bool, Optional[str], Optional[str]]:
        metadata = self._extract_legacy_metadata(order.internal_notes)
        is_imported = bool(metadata)
        legacy_status_raw = metadata.get("legacy_status_raw") or metadata.get("OrderStatusId")
        import_source = "marvelous_creations" if is_imported else None
        return is_imported, legacy_status_raw, import_source

    def _primary_history_key(self, order: Order) -> Optional[str]:
        if order.customer_contact_id:
            return f"contact:{order.customer_contact_id}"
        if order.customer_email:
            return f"email:{order.customer_email.strip().lower()}"
        if order.customer_phone:
            return f"phone:{order.customer_phone.strip().lower()}"
        return None

    def _build_related_orders_map(
        self, orders: Iterable[Order]
    ) -> dict[str, list[Order]]:
        order_list = list(orders)
        contact_ids = {
            order.customer_contact_id
            for order in order_list
            if order.customer_contact_id is not None
        }
        emails = {
            order.customer_email.strip().lower()
            for order in order_list
            if order.customer_email
        }
        phones = {
            order.customer_phone.strip().lower()
            for order in order_list
            if order.customer_phone
        }

        if not contact_ids and not emails and not phones:
            return {}

        match_clauses = []
        if contact_ids:
            match_clauses.append(Order.customer_contact_id.in_(contact_ids))
        if emails:
            match_clauses.append(Order.customer_email.in_(emails))
        if phones:
            match_clauses.append(Order.customer_phone.in_(phones))

        user_ids = {order.user_id for order in order_list}
        statement = select(Order).where(Order.user_id.in_(user_ids), or_(*match_clauses))
        candidates = self.session.exec(statement).all()

        related_by_key: dict[str, list[Order]] = defaultdict(list)
        for candidate in candidates:
            key = self._primary_history_key(candidate)
            if key:
                related_by_key[key].append(candidate)
        return related_by_key

    def _build_customer_history_summary_from_related(
        self,
        order: Order,
        related_orders: list[Order],
    ) -> OrderCustomerHistorySummary:
        primary_key = self._primary_history_key(order)
        if not primary_key:
            return OrderCustomerHistorySummary(
                total_orders=1,
                completed_orders=0,
                active_orders=1 if order.status not in {OrderStatus.COMPLETED, OrderStatus.CANCELLED} else 0,
                last_order_date=None,
            )

        siblings = [candidate for candidate in related_orders if candidate.id != order.id]
        all_orders = [order, *siblings]
        prior_orders = [
            candidate
            for candidate in siblings
            if candidate.order_date <= order.order_date
        ]
        last_order_date = max(
            (candidate.order_date for candidate in prior_orders),
            default=None,
        )
        completed_orders = sum(
            1 for candidate in all_orders if candidate.status == OrderStatus.COMPLETED
        )
        active_orders = sum(
            1
            for candidate in all_orders
            if candidate.status not in {OrderStatus.COMPLETED, OrderStatus.CANCELLED}
        )
        return OrderCustomerHistorySummary(
            total_orders=len(all_orders),
            completed_orders=completed_orders,
            active_orders=active_orders,
            last_order_date=last_order_date,
        )

    def _build_recent_customer_orders(
        self,
        order: Order,
        related_orders: list[Order],
    ) -> list[OrderRecentCustomerOrder]:
        siblings = sorted(
            (candidate for candidate in related_orders if candidate.id != order.id),
            key=lambda candidate: (candidate.order_date, candidate.created_at),
            reverse=True,
        )
        return [
            OrderRecentCustomerOrder(
                id=candidate.id,
                order_number=candidate.order_number,
                order_date=candidate.order_date,
                due_date=candidate.due_date,
                status=candidate.status,
                payment_status=candidate.payment_status,
                total_amount=candidate.total_amount,
            )
            for candidate in siblings[:RECENT_CUSTOMER_HISTORY_LIMIT]
        ]

    def _order_needs_review(self, order_read: OrderRead) -> bool:
        return (
            not order_read.customer_summary.is_linked_contact
            or (
                not order_read.customer_summary.email
                and not order_read.customer_summary.phone
            )
            or bool(order_read.invoice_summary.missing_fields)
            or order_read.risk_summary.has_overdue_payment
        )

    def _build_import_review_triage(
        self,
        *,
        is_imported: bool,
        customer_summary: OrderCustomerSummary,
        invoice_summary: OrderInvoiceSummary,
        risk_summary: OrderRiskSummary,
    ) -> tuple[list[ImportedOrderReviewReason], Optional[ImportedOrderReviewReason], Optional[str]]:
        if not is_imported:
            return [], None, None

        review_reasons: list[ImportedOrderReviewReason] = []
        if risk_summary.has_overdue_payment:
            review_reasons.append(ImportedOrderReviewReason.OVERDUE_PAYMENT_RISK)
        if invoice_summary.missing_fields:
            review_reasons.append(ImportedOrderReviewReason.INVOICE_MISSING_FIELDS)
        if not customer_summary.email and not customer_summary.phone:
            review_reasons.append(ImportedOrderReviewReason.MISSING_CONTACT_DETAILS)
        if not customer_summary.is_linked_contact:
            review_reasons.append(ImportedOrderReviewReason.UNLINKED_CONTACT)

        primary_review_reason = review_reasons[0] if review_reasons else None
        review_next_check = (
            _import_review_next_check(primary_review_reason)
            if primary_review_reason is not None
            else None
        )
        return review_reasons, primary_review_reason, review_next_check

    def _build_payment_summary(self, order: Order) -> OrderPaymentSummary:
        deposit_required = round(order.deposit_amount or 0.0, 2)
        amount_paid = 0.0
        if order.payment_status == PaymentStatus.DEPOSIT_PAID:
            amount_paid = deposit_required
        elif order.payment_status == PaymentStatus.PAID_IN_FULL:
            amount_paid = order.total_amount

        amount_due = round(max(order.total_amount - amount_paid, 0.0), 2)
        deposit_outstanding = round(max(deposit_required - amount_paid, 0.0), 2)
        return OrderPaymentSummary(
            amount_paid=round(amount_paid, 2),
            amount_due=amount_due,
            deposit_required=deposit_required,
            deposit_outstanding=deposit_outstanding,
            balance_due=round(order.balance_due or amount_due, 2),
            is_paid_in_full=order.payment_status == PaymentStatus.PAID_IN_FULL,
        )

    def _build_import_priority(
        self,
        order_read: OrderRead,
    ) -> tuple[int, Optional[str]]:
        if not order_read.is_imported:
            return 999, None

        if order_read.review_reasons:
            top_reason = min(
                order_read.review_reasons,
                key=lambda reason: IMPORT_REVIEW_REASON_PRIORITY[reason],
            )
            return IMPORT_REVIEW_REASON_PRIORITY[top_reason], IMPORT_PRIORITY_LABELS[top_reason]

        return 50, "Ready after review pile"

    def _sort_imported_order_reads(self, order_reads: list[OrderRead]) -> list[OrderRead]:
        def due_key(order_read: OrderRead) -> float:
            return order_read.due_date.timestamp() if order_read.due_date else float("inf")

        def order_key(order_read: OrderRead) -> tuple[int, int, float, float, float]:
            needs_review_rank = 0 if order_read.review_reasons else 1
            priority_rank = order_read.imported_priority_rank
            urgency_rank = order_read.queue_summary.urgency_rank
            due_timestamp = due_key(order_read)
            order_timestamp = order_read.order_date.timestamp()
            return (
                needs_review_rank,
                priority_rank,
                urgency_rank,
                due_timestamp,
                -order_timestamp,
            )

        return sorted(order_reads, key=order_key)

    def _build_queue_summary(self, order: Order) -> OrderQueueSummary:
        today = _utcnow().date()
        due_date = _date_in_user_timezone(order.due_date)
        days_until_due = (due_date - today).days
        is_due_today = days_until_due == 0
        is_overdue = days_until_due < 0 and order.status not in {
            OrderStatus.COMPLETED,
            OrderStatus.CANCELLED,
        }

        if is_overdue:
            due_bucket = "overdue"
            urgency_label = "Urgent"
            urgency_rank = 0
        elif is_due_today:
            due_bucket = "today"
            urgency_label = "Today"
            urgency_rank = 1
        elif days_until_due <= 3:
            due_bucket = "next_up"
            urgency_label = "Next up"
            urgency_rank = 2
        else:
            due_bucket = "upcoming"
            urgency_label = "Watch"
            urgency_rank = 3

        return OrderQueueSummary(
            is_due_today=is_due_today,
            is_overdue=is_overdue,
            days_until_due=days_until_due,
            due_bucket=due_bucket,
            urgency_label=urgency_label,
            urgency_rank=urgency_rank,
        )

    def _build_customer_history_summary(self, order: Order) -> OrderCustomerHistorySummary:
        related_orders = self._build_related_orders_map([order]).get(
            self._primary_history_key(order) or "",
            [],
        )
        return self._build_customer_history_summary_from_related(order, related_orders)

    def _build_risk_summary(
        self,
        order: Order,
        payment_summary: OrderPaymentSummary,
        queue_summary: OrderQueueSummary,
    ) -> OrderRiskSummary:
        today = _utcnow().date()
        reasons: list[str] = []
        overdue_amount = 0.0

        if (
            payment_summary.deposit_outstanding > 0
            and order.deposit_due_date is not None
            and order.deposit_due_date < today
        ):
            reasons.append("deposit_overdue")
            overdue_amount += payment_summary.deposit_outstanding

        balance_due_amount = round(max(payment_summary.amount_due - payment_summary.deposit_outstanding, 0.0), 2)
        if (
            balance_due_amount > 0
            and order.balance_due_date is not None
            and order.balance_due_date < today
        ):
            reasons.append("balance_overdue")
            overdue_amount += balance_due_amount

        if queue_summary.is_overdue and payment_summary.amount_due > 0:
            reasons.append("order_overdue_with_balance")

        if payment_summary.amount_due >= max(order.total_amount * 0.5, 100):
            reasons.append("large_unpaid_balance")

        if overdue_amount > 0:
            level = "high"
        elif "order_overdue_with_balance" in reasons or "large_unpaid_balance" in reasons:
            level = "medium"
        else:
            level = "low"

        return OrderRiskSummary(
            level=level,
            reasons=reasons,
            overdue_amount=round(overdue_amount, 2),
            outstanding_amount=payment_summary.amount_due,
            has_overdue_payment=overdue_amount > 0,
        )

    def _build_invoice_summary(self, order: Order) -> OrderInvoiceSummary:
        missing_fields = []
        if not (order.customer_name or order.customer_email):
            missing_fields.append("customer_identity")
        if order.total_amount <= 0:
            missing_fields.append("line_items")
        if not order.due_date:
            missing_fields.append("due_date")

        is_ready = not missing_fields
        status_label = "ready" if is_ready else "needs_attention"
        return OrderInvoiceSummary(
            is_ready=is_ready,
            status=status_label,
            missing_fields=missing_fields,
            pdf_path=f"/api/v1/orders/{order.id}/invoice/pdf" if is_ready else None,
            client_portal_path=f"/api/v1/orders/{order.id}/client-portal-url",
        )

    def _build_invoice_focus_summary(
        self,
        order: Order,
        customer_summary: OrderCustomerSummary,
        payment_summary: OrderPaymentSummary,
        invoice_summary: OrderInvoiceSummary,
    ) -> OrderInvoiceFocusSummary:
        due_label = _format_bakery_date(_date_in_user_timezone(order.due_date))
        order_identity = f"{order.order_number} due {due_label}"

        customer_bits = [
            bit
            for bit in [
                customer_summary.name,
                customer_summary.email,
                customer_summary.phone,
            ]
            if bit
        ]
        customer_identity = (
            " | ".join(customer_bits)
            if customer_bits
            else "Customer identity is still too thin for invoice send confidence."
        )

        amount_summary = f"Invoice total ${order.total_amount:.2f}"
        if payment_summary.amount_due <= 0:
            payment_context = "Payment status: paid in full."
        elif payment_summary.deposit_outstanding > 0:
            if order.deposit_due_date is not None:
                payment_context = (
                    "Payment status: deposit still open "
                    f"(${payment_summary.deposit_outstanding:.2f}) due {_format_bakery_date_only(order.deposit_due_date)}."
                )
            else:
                payment_context = (
                    "Payment status: deposit still open "
                    f"(${payment_summary.deposit_outstanding:.2f}) with no deposit due date."
                )
        else:
            balance_due_amount = round(
                max(payment_summary.amount_due - payment_summary.deposit_outstanding, 0.0),
                2,
            )
            if order.balance_due_date is not None:
                payment_context = (
                    f"Payment status: {order.payment_status.value.replace('_', ' ')} with "
                    f"${balance_due_amount:.2f} still due by {_format_bakery_date_only(order.balance_due_date)}."
                )
            else:
                payment_context = (
                    f"Payment status: {order.payment_status.value.replace('_', ' ')} with "
                    f"${payment_summary.amount_due:.2f} still open."
                )

        blockers = [_humanize_invoice_field(field) for field in invoice_summary.missing_fields]

        missing_basics: list[str] = []
        if not customer_summary.email and not customer_summary.phone:
            missing_basics.append("Add at least one customer contact method before sending the invoice.")
        if payment_summary.amount_due > 0 and not order.deposit_due_date and not order.balance_due_date:
            missing_basics.append("Add a payment due date so the invoice gives the customer a clear timing cue.")

        if invoice_summary.is_ready and payment_summary.amount_due <= 0:
            status_label = "ready_and_paid"
            readiness_note = "Invoice basics are complete and the order is already paid."
            next_step = "Share or archive the invoice record"
            next_step_detail = "The invoice is ready from the current order details and no money is still open."
        elif invoice_summary.is_ready:
            status_label = "ready_to_send"
            readiness_note = "Invoice basics are complete from the current order record."
            if payment_summary.deposit_outstanding > 0:
                next_step = "Send invoice with deposit guidance"
                next_step_detail = "Lead with the deposit amount and due date so the customer knows the first payment checkpoint."
            else:
                next_step = "Confirm final payment timing"
                next_step_detail = "The invoice is ready; double-check the remaining amount and due date before sending."
        else:
            status_label = "blocked"
            readiness_note = "Invoice is not send-ready yet because key billing basics are still missing."
            next_step = "Complete invoice basics"
            next_step_detail = blockers[0] if blockers else "Fill the missing invoice basics before sending anything."

        return OrderInvoiceFocusSummary(
            status_label=status_label,
            readiness_note=readiness_note,
            order_identity=order_identity,
            customer_identity=customer_identity,
            amount_summary=amount_summary,
            payment_context=payment_context,
            blockers=blockers,
            missing_basics=missing_basics,
            next_step=next_step,
            next_step_detail=next_step_detail,
        )

    def _build_payment_focus_summary(
        self,
        order: Order,
        payment_summary: OrderPaymentSummary,
        queue_summary: OrderQueueSummary,
        risk_summary: OrderRiskSummary,
        ops_summary: OrderOpsSummary,
        *,
        is_imported: bool,
    ) -> OrderPaymentFocusSummary:
        today = _utcnow().date()
        balance_due_amount = round(max(payment_summary.amount_due - payment_summary.deposit_outstanding, 0.0), 2)

        if payment_summary.amount_due <= 0:
            payment_state = "Paid in full"
            collection_stage = "settled"
        elif payment_summary.deposit_outstanding > 0:
            payment_state = "Deposit still needed"
            collection_stage = "deposit"
        elif balance_due_amount > 0:
            payment_state = "Waiting on final balance"
            collection_stage = "balance"
        else:
            payment_state = "Payment review needed"
            collection_stage = "review"

        if payment_summary.deposit_required <= 0:
            deposit_status = "No deposit required"
        elif payment_summary.deposit_outstanding <= 0:
            deposit_status = "Deposit collected"
        elif order.deposit_due_date is None:
            deposit_status = f"Deposit outstanding: ${payment_summary.deposit_outstanding:.2f} with no due date"
        elif order.deposit_due_date < today:
            deposit_status = (
                f"Deposit overdue since {_format_bakery_date_only(order.deposit_due_date)} "
                f"(${payment_summary.deposit_outstanding:.2f} still open)"
            )
        elif order.deposit_due_date == today:
            deposit_status = (
                f"Deposit due today (${payment_summary.deposit_outstanding:.2f} still open)"
            )
        else:
            deposit_status = (
                f"Deposit due {_format_bakery_date_only(order.deposit_due_date)} "
                f"(${payment_summary.deposit_outstanding:.2f} still open)"
            )

        if payment_summary.amount_due <= 0:
            balance_status = "No balance remaining"
        elif payment_summary.deposit_outstanding > 0:
            balance_status = "Balance will unlock after the deposit is collected"
        elif balance_due_amount <= 0:
            balance_status = "No balance remaining"
        elif order.balance_due_date is None:
            balance_status = f"Final balance outstanding: ${balance_due_amount:.2f} with no due date"
        elif order.balance_due_date < today:
            balance_status = (
                f"Final balance overdue since {_format_bakery_date_only(order.balance_due_date)} "
                f"(${balance_due_amount:.2f} still open)"
            )
        elif order.balance_due_date == today:
            balance_status = f"Final balance due today (${balance_due_amount:.2f} still open)"
        else:
            balance_status = (
                f"Final balance due {_format_bakery_date_only(order.balance_due_date)} "
                f"(${balance_due_amount:.2f} still open)"
            )

        if payment_summary.amount_due <= 0:
            due_timing = "No money is due right now."
        elif payment_summary.deposit_outstanding > 0 and order.deposit_due_date is not None:
            due_timing = f"Next payment checkpoint: deposit on {_format_bakery_date_only(order.deposit_due_date)}."
        elif balance_due_amount > 0 and order.balance_due_date is not None:
            due_timing = f"Next payment checkpoint: final balance on {_format_bakery_date_only(order.balance_due_date)}."
        elif queue_summary.is_overdue:
            due_timing = f"Order due date passed on {_format_bakery_date(_date_in_user_timezone(order.due_date))}."
        elif queue_summary.is_due_today:
            due_timing = "Order is due today."
        else:
            due_timing = f"Order due date is {_format_bakery_date(_date_in_user_timezone(order.due_date))}."

        risk_note = (
            " ".join(_humanize_reason(reason) for reason in risk_summary.reasons)
            if risk_summary.reasons
            else "No payment-specific risk flags right now."
        )

        has_payment_checkpoint = payment_summary.deposit_required > 0 or order.balance_due_date is not None
        if payment_summary.amount_due <= 0:
            amount_owed_now = 0.0
        elif collection_stage == "deposit":
            amount_owed_now = payment_summary.deposit_outstanding
        elif collection_stage == "balance":
            amount_owed_now = balance_due_amount
        elif has_payment_checkpoint:
            amount_owed_now = balance_due_amount
        else:
            amount_owed_now = payment_summary.amount_due

        trust_state = "current"
        trust_label = "Current BakeMate payment context"
        trust_note = "Payment status comes from current BakeMate order data."
        historical_payment_label: Optional[str] = None
        historical_payment_note: Optional[str] = None
        if is_imported:
            trust_state = "legacy_limited"
            trust_label = "Imported payment history is legacy-limited"
            trust_note = (
                "This order was imported from legacy data, so BakeMate is showing a conservative payment snapshot "
                "instead of a reconstructed payment ledger. Treat historical payment history as unknown unless you have a second source."
            )
            historical_payment_label = "Historical payment: unknown"
            historical_payment_note = (
                "Legacy payment history may be incomplete in this import. Use a second source before treating earlier payments as confirmed."
            )

        return OrderPaymentFocusSummary(
            amount_owed_now=round(amount_owed_now, 2),
            payment_state=payment_state,
            collection_stage=collection_stage,
            deposit_status=deposit_status,
            balance_status=balance_status,
            due_timing=due_timing,
            risk_note=risk_note,
            next_step=ops_summary.next_action,
            next_step_detail=ops_summary.ops_attention,
            trust_state=trust_state,
            trust_label=trust_label,
            trust_note=trust_note,
            historical_payment_label=historical_payment_label,
            historical_payment_note=historical_payment_note,
        )

    def _build_handoff_focus_summary(
        self,
        order: Order,
        customer_summary: OrderCustomerSummary,
        queue_summary: OrderQueueSummary,
        ops_summary: OrderOpsSummary,
    ) -> OrderHandoffFocusSummary:
        method_raw = (order.delivery_method or "").strip().lower()
        if "deliver" in method_raw:
            method_status = "delivery"
            method_label = "Delivery"
        elif "pickup" in method_raw or "pick up" in method_raw:
            method_status = "pickup"
            method_label = "Pickup"
        else:
            method_status = "unclear"
            method_label = "Method still unclear"

        contact_name = customer_summary.name
        primary_contact = customer_summary.email or customer_summary.phone or "No customer contact details on file"
        secondary_contact = None
        if customer_summary.email and customer_summary.phone:
            secondary_contact = customer_summary.phone

        destination_from_contact = _compact_contact_address(order.customer)
        if method_status == "delivery":
            destination_label = destination_from_contact or "Delivery destination still missing"
            destination_detail = (
                "Use the saved delivery address for this handoff."
                if destination_from_contact
                else "No delivery address is stored on the linked contact yet."
            )
        elif method_status == "pickup":
            destination_label = "Customer pickup"
            destination_detail = "Pickup flow is expected for this order."
        else:
            destination_label = "Method not confirmed"
            destination_detail = "Pickup vs delivery is still not explicit on this order."

        missing_basics: list[str] = []
        if method_status == "unclear":
            missing_basics.append("Confirm whether this order is pickup or delivery.")
        if not customer_summary.email and not customer_summary.phone:
            missing_basics.append("Add at least one customer contact method before handoff.")
        if method_status == "delivery" and not destination_from_contact:
            missing_basics.append("Add the delivery destination before this order leaves the kitchen.")
        if method_status == "pickup" and not customer_summary.phone and not customer_summary.email:
            missing_basics.append("Confirm who is collecting the pickup order.")

        if missing_basics:
            readiness_note = "Handoff is not ready yet — key basics are still missing."
        elif queue_summary.is_due_today:
            readiness_note = "Handoff basics are in place for today."
        else:
            readiness_note = "Handoff basics are present, but timing should still be rechecked before release."

        if method_status == "delivery":
            next_step = "Confirm delivery release details"
            next_step_detail = (
                missing_basics[0]
                if missing_basics
                else "Use the saved delivery contact and destination as the final leave-the-kitchen check."
            )
        elif method_status == "pickup":
            next_step = "Confirm pickup handoff details"
            next_step_detail = (
                missing_basics[0]
                if missing_basics
                else "Make sure the pickup contact and ready time are clear before customer arrival."
            )
        else:
            next_step = "Lock the handoff basics first"
            next_step_detail = missing_basics[0] if missing_basics else ops_summary.ops_attention

        return OrderHandoffFocusSummary(
            handoff_time_label=(
                "Due today — " + _format_datetime_label(order.due_date)
                if queue_summary.is_due_today
                else _format_datetime_label(order.due_date)
            ),
            method_status=method_status,
            method_label=method_label,
            contact_name=contact_name,
            primary_contact=primary_contact,
            secondary_contact=secondary_contact,
            destination_label=destination_label,
            destination_detail=destination_detail,
            readiness_note=readiness_note,
            missing_basics=missing_basics,
            next_step=next_step,
            next_step_detail=next_step_detail,
        )

    def _build_item_scan_summary(self, order: Order) -> tuple[str, str, int, list[str]]:
        item_count = sum(max(item.quantity, 0) for item in order.items)
        primary_names = [item.name.strip() for item in order.items if item.name and item.name.strip()]

        if primary_names:
            if len(primary_names) == 1:
                contents_summary = primary_names[0]
            elif len(primary_names) == 2:
                contents_summary = f"{primary_names[0]} + {primary_names[1]}"
            else:
                contents_summary = f"{primary_names[0]} + {len(primary_names) - 1} more item(s)"
        else:
            contents_summary = "Line items still missing"

        if item_count <= 0:
            item_count_label = "No item quantity captured"
        elif item_count == 1:
            item_count_label = "1 item"
        else:
            item_count_label = f"{item_count} total items"

        return contents_summary, item_count_label, item_count, primary_names

    def _build_production_focus_summary(
        self,
        order: Order,
        queue_summary: OrderQueueSummary,
        handoff_focus_summary: OrderHandoffFocusSummary,
    ) -> OrderProductionFocusSummary:
        contents_summary, item_count_label, item_count, primary_names = self._build_item_scan_summary(order)
        missing_basics: list[str] = []
        clarification_flags: list[str] = []

        detail_bits = [
            item.description.strip()
            for item in order.items
            if item.description and item.description.strip()
        ]
        if order.notes_to_customer and order.notes_to_customer.strip():
            detail_bits.append(order.notes_to_customer.strip())
        if order.internal_notes and order.internal_notes.strip():
            detail_bits.append(order.internal_notes.strip())
        detail_text = " ".join(detail_bits)
        has_detail_signal = len(detail_text) >= 20

        generic_names = {
            "cake",
            "cakes",
            "cupcake",
            "cupcakes",
            "cookies",
            "cookie",
            "dessert",
            "desserts",
            "other",
            "assorted",
            "treats",
        }
        has_only_generic_names = bool(primary_names) and all(
            name.lower() in generic_names or len(name.split()) <= 2 for name in primary_names
        )

        if not order.items:
            missing_basics.append("No usable item summary yet — add at least one line item before baking.")
        elif not primary_names:
            missing_basics.append("Item names are blank — add a usable item summary before baking.")

        if order.items and item_count <= 0:
            missing_basics.append("Quantity/count cue is missing — capture how many items need to be made.")

        if not order.delivery_method:
            missing_basics.append("Handoff method is missing — confirm pickup vs delivery before prep starts.")

        if order.items and item_count > 0 and has_only_generic_names and not has_detail_signal:
            clarification_flags.append("Production details are thin — confirm flavor, theme, message, or design notes before baking.")
        elif order.items and item_count > 0 and not has_detail_signal and len(primary_names) <= 1:
            clarification_flags.append("Order details look light — confirm the key production notes before baking.")

        combined_gaps = (missing_basics + [flag for flag in clarification_flags if flag not in missing_basics])[:4]

        if missing_basics:
            readiness_label = "Missing basics"
            attention_note = missing_basics[0]
            next_step = "Lock the missing production basics"
            next_step_detail = missing_basics[0]
        elif clarification_flags:
            readiness_label = "Needs clarification"
            attention_note = clarification_flags[0]
            next_step = "Confirm production details"
            next_step_detail = clarification_flags[0]
        else:
            readiness_label = "Ready to make"
            if queue_summary.is_due_today:
                attention_note = "Production basics look clear from the current order record for today’s work."
            elif queue_summary.is_overdue:
                attention_note = "Production basics look clear, but timing should be rechecked because the order is overdue."
            else:
                attention_note = "Production basics look clear from the current order record."
            next_step = "Proceed with production prep"
            next_step_detail = (
                "Use the handoff panel to recheck the final timing and release details."
                if handoff_focus_summary.missing_basics
                else "Proceed with the current production plan and recheck timing before release."
            )

        return OrderProductionFocusSummary(
            contents_summary=contents_summary,
            item_count_label=item_count_label,
            readiness_label=readiness_label,
            missing_basics=combined_gaps,
            attention_note=attention_note,
            next_step=next_step,
            next_step_detail=next_step_detail,
        )

    def _build_contact_focus_summary(
        self,
        order: Order,
        customer_summary: OrderCustomerSummary,
        queue_summary: OrderQueueSummary,
        risk_summary: OrderRiskSummary,
        ops_summary: OrderOpsSummary,
    ) -> OrderContactFocusSummary:
        display_name = customer_summary.name or "Customer name still missing"
        has_name = bool(customer_summary.name and customer_summary.name.strip())
        has_email = bool(customer_summary.email and str(customer_summary.email).strip())
        has_phone = bool(customer_summary.phone and customer_summary.phone.strip())
        contact_path_count = int(has_email) + int(has_phone)
        follow_up_pressure = (
            queue_summary.is_due_today
            or queue_summary.is_overdue
            or risk_summary.has_overdue_payment
            or ops_summary.action_class in {"payment_now", "handoff_today"}
        )

        if has_email and has_phone:
            best_contact_methods_summary = f"Email: {customer_summary.email} • Phone: {customer_summary.phone}"
        elif has_email:
            best_contact_methods_summary = f"Email only: {customer_summary.email}"
        elif has_phone:
            best_contact_methods_summary = f"Phone only: {customer_summary.phone}"
        else:
            best_contact_methods_summary = "No usable email or phone on file"

        missing_basics: list[str] = []
        if not has_name:
            missing_basics.append("Customer name is missing — confirm who this order belongs to before follow-up.")
        if not has_phone:
            missing_basics.append("No phone number on file — live follow-up may be slower if questions come up.")
        if not has_email:
            missing_basics.append("No email on file — written follow-up and invoice delivery backup are limited.")
        if contact_path_count == 1 and follow_up_pressure:
            missing_basics.append("Only one direct contact path is on file — follow-up fallback is thin if that method fails.")
        missing_basics = missing_basics[:4]

        if has_name and contact_path_count >= 2:
            readiness_label = "Ready to contact"
            attention_note = (
                "Two direct contact paths are on file for quick follow-up today."
                if follow_up_pressure
                else "Two direct contact paths are on file from the current order record."
            )
            next_step = "Use the saved contact details"
            next_step_detail = "Reach out using the current phone/email on file if clarification, payment, or handoff follow-up is needed."
        elif has_name and contact_path_count == 1:
            readiness_label = "Limited contact info"
            attention_note = (
                "Only one direct contact method is on file, so follow-up is possible but not resilient."
            )
            if has_phone:
                next_step = "Add an email backup if you talk to the customer"
                next_step_detail = "Phone follow-up is possible now, but capturing an email would make future clarification and invoice follow-up safer."
            else:
                next_step = "Add a phone backup if you reach the customer"
                next_step_detail = "Email follow-up is possible now, but capturing a phone number would make urgent same-day follow-up safer."
        else:
            readiness_label = "Missing contact basics"
            attention_note = missing_basics[0] if missing_basics else "Key contact basics are missing from this order record."
            if not has_name:
                next_step = "Confirm the customer identity first"
                next_step_detail = "Lock the customer name plus at least one direct contact method before treating follow-up as reliable."
            elif contact_path_count == 0:
                next_step = "Capture a direct contact method"
                next_step_detail = "Add at least one phone number or email before relying on this order for follow-up."
            elif not has_phone:
                next_step = "Add a phone number for faster follow-up"
                next_step_detail = "Urgent questions are harder to resolve without a callable number on the order."
            else:
                next_step = "Add an email backup"
                next_step_detail = "Written follow-up is thin until an email is captured on the order."

        return OrderContactFocusSummary(
            customer_display_name=display_name,
            best_contact_methods_summary=best_contact_methods_summary,
            readiness_label=readiness_label,
            missing_basics=missing_basics,
            attention_note=attention_note,
            next_step=next_step,
            next_step_detail=next_step_detail,
        )

    def _build_queue_next_step_preview(self, *, next_step: str, reason_summary: str) -> str:
        normalized_reason = reason_summary.strip().rstrip(".").lower()
        compact_next_step = {
            "Share or archive the invoice record": "Share invoice record",
            "Send invoice with deposit guidance": "Send invoice",
            "Confirm final payment timing": "Confirm final payment",
            "Complete invoice basics": "Finish invoice",
            "Confirm delivery release details": "Confirm delivery handoff",
            "Confirm pickup handoff details": "Confirm pickup handoff",
            "Lock the handoff basics": "Lock handoff basics",
            "Lock the handoff basics first": "Lock handoff basics",
            "Lock the missing production basics": "Lock production basics",
            "Confirm production details": "Confirm production basics",
            "Proceed with production prep": "Start production prep",
            "Use the saved contact details": "Use contact info",
            "Add an email backup if you talk to the customer": "Add email backup",
            "Add a phone backup if you reach the customer": "Add phone backup",
            "Confirm the customer identity first": "Confirm customer identity",
            "Capture a direct contact method": "Add contact method",
            "Add a phone number for faster follow-up": "Add phone number",
            "Add an email backup": "Add email backup",
            "Review deposit follow-up": "Review deposit",
            "Collect the overdue deposit": "Collect deposit",
            "Collect the overdue balance": "Collect final balance",
            "Review final balance collection": "Review final balance",
            "Proceed with today’s order plan": "Proceed with order plan",
            "Recheck timing and proceed": "Recheck timing",
            "Keep the order on track": "Keep on track",
        }.get(next_step, next_step)

        if normalized_reason == "production details need clarification" and compact_next_step == "Confirm production basics":
            compact_next_step = "Clarify production basics"
        elif normalized_reason.startswith("production details are thin") and compact_next_step == "Confirm production basics":
            compact_next_step = "Clarify production basics"
        elif normalized_reason == "invoice is still missing basics for today" and compact_next_step in {"Finish invoice", "Complete invoice details"}:
            compact_next_step = "Finish invoice"

        return f"Next: {compact_next_step[:1].lower() + compact_next_step[1:]}"

    def _build_queue_reason_preview(self, *, readiness_label: str, reason_summary: str) -> str:
        normalized_reason = reason_summary.strip().rstrip(".")

        if normalized_reason.startswith("Deposit is still open "):
            compact_reason = "Deposit due"
        elif normalized_reason.startswith("Deposit is still unpaid "):
            compact_reason = "Overdue deposit"
        elif normalized_reason.startswith("Final balance is overdue "):
            compact_reason = "Overdue final balance"
        elif normalized_reason.startswith("Final balance is still open "):
            compact_reason = "Final balance due"
        else:
            compact_reason = {
                "Confirm pickup vs delivery so today’s release plan is clear": "Handoff method not confirmed",
                "Invoice is still missing basics for today": "Invoice basics missing",
                "production basics missing": "Production basics missing",
                "production details need clarification": "Production basics need clarification",
                "contact basics missing": "Contact info missing",
                "contact fallback is thin": "Backup contact info missing",
                "handoff basics missing": "Handoff basics missing",
            }.get(normalized_reason, normalized_reason)

        prefix = "Blocked" if readiness_label == "Blocked for today" else "Attention"
        return f"{prefix}: {compact_reason}"

    def _build_queue_payment_trust_preview(self, *, payment_focus_summary: OrderPaymentFocusSummary) -> Optional[str]:
        if payment_focus_summary.trust_state != "legacy_limited":
            return None
        return "Payment trust: legacy-limited"

    def _build_review_payment_trust_preview(self, *, payment_focus_summary: OrderPaymentFocusSummary) -> Optional[str]:
        if payment_focus_summary.trust_state != "legacy_limited":
            return None
        return "Payment trust: legacy-limited"

    def _build_day_running_contact_preview(
        self,
        *,
        readiness_label: str,
        primary_category: str,
        next_step: str,
        contact_focus_summary: OrderContactFocusSummary,
        customer_summary: OrderCustomerSummary,
    ) -> Optional[str]:
        if readiness_label not in {"Blocked for today", "Needs attention today"}:
            return None

        follow_up_next_steps = {
            "Review deposit follow-up",
            "Collect the overdue deposit",
            "Collect the overdue balance",
            "Review final balance collection",
            "Confirm production details",
            "Use the saved contact details",
        }
        follow_up_categories = {"payment", "contact"}
        if primary_category == "handoff" and "confirm" in next_step.lower():
            follow_up_categories.add("handoff")
        if primary_category not in follow_up_categories and next_step not in follow_up_next_steps:
            return None

        has_email = bool(customer_summary.email and customer_summary.email.strip())
        has_phone = bool(customer_summary.phone and customer_summary.phone.strip())

        missing_basics_text = " ".join(contact_focus_summary.missing_basics).lower()
        if has_phone:
            return f"Contact: call {customer_summary.phone}"
        if "no phone number on file" in missing_basics_text and has_email:
            return "Contact: missing phone"
        if has_email:
            return "Contact: email on file"

        if contact_focus_summary.readiness_label == "Limited contact info":
            return "Contact: limited info"
        if contact_focus_summary.readiness_label == "Missing contact basics":
            return "Contact: limited info"

        return None

    def _build_day_running_payment_preview(
        self,
        *,
        readiness_label: str,
        primary_category: str,
        next_step: str,
        payment_focus_summary: OrderPaymentFocusSummary,
    ) -> Optional[str]:
        if readiness_label not in {"Blocked for today", "Needs attention today"}:
            return None
        if primary_category != "payment":
            return None

        payment_related_next_steps = {
            "Review deposit follow-up",
            "Collect the overdue deposit",
            "Collect the overdue balance",
            "Review final balance collection",
        }
        if next_step not in payment_related_next_steps:
            return None

        if payment_focus_summary.collection_stage == "deposit":
            return f"Collect: ${payment_focus_summary.amount_owed_now:.2f} deposit"
        if payment_focus_summary.collection_stage == "balance":
            return f"Collect: ${payment_focus_summary.amount_owed_now:.2f} final balance"
        if payment_focus_summary.collection_stage == "settled":
            return "Paid in full"
        if next_step == "Review deposit follow-up":
            return "Deposit review needed"
        if next_step == "Review final balance collection":
            return "Final balance review needed"
        return "Payment review needed"

    def _build_day_running_production_preview(
        self,
        *,
        readiness_label: str,
        primary_category: str,
        next_step: str,
        production_focus_summary: OrderProductionFocusSummary,
    ) -> Optional[str]:
        if readiness_label not in {"Blocked for today", "Needs attention today"}:
            return None

        production_related_next_steps = {
            "Lock the missing production basics",
            "Confirm production details",
            "Proceed with production prep",
        }
        next_step_lower = next_step.lower()
        is_production_related = primary_category == "production" or next_step in production_related_next_steps or any(
            token in next_step_lower for token in ["production", "baking", "make"]
        )
        if not is_production_related:
            return None

        if production_focus_summary.readiness_label == "Ready to make":
            return "Production: ready to make"

        attention_note = production_focus_summary.attention_note.lower()
        if production_focus_summary.readiness_label == "Needs clarification":
            if "flavor" in attention_note:
                return "Production: flavor needs confirmation"
            if "theme" in attention_note or "design" in attention_note or "message" in attention_note:
                return "Production: design notes need confirmation"
            if "details are thin" in attention_note or "details look light" in attention_note:
                return "Production: quantity/details need review"
            return "Production: details need confirmation"

        if production_focus_summary.missing_basics:
            top_missing = production_focus_summary.missing_basics[0]
            if top_missing == "No usable item summary yet — add at least one line item before baking.":
                return "Production: item summary needs review"
            if top_missing == "Item names are blank — add a usable item summary before baking.":
                return "Production: item summary needs review"
            if top_missing == "Quantity/count cue is missing — capture how many items need to be made.":
                return "Production: quantity/details need review"
            if top_missing == "Handoff method is missing — confirm pickup vs delivery before prep starts.":
                return "Production: handoff method needs confirmation"
            return f"Production: {top_missing[:1].lower() + top_missing[1:]}"

        return None

    def _build_day_running_invoice_preview(
        self,
        *,
        readiness_label: str,
        primary_category: str,
        next_step: str,
        invoice_focus_summary: OrderInvoiceFocusSummary,
    ) -> Optional[str]:
        if readiness_label not in {"Blocked for today", "Needs attention today"}:
            return None

        invoice_related_next_steps = {
            "Complete invoice basics",
            "Complete invoice basics",
            "Send invoice with deposit guidance",
            "Confirm final payment timing",
            "Share or archive the invoice record",
        }
        next_step_lower = next_step.lower()
        is_invoice_related = primary_category == "invoice" or next_step in invoice_related_next_steps or "invoice" in next_step_lower
        if not is_invoice_related:
            return None

        if invoice_focus_summary.status_label == "ready_to_send":
            return "Invoice: ready to send"
        if invoice_focus_summary.status_label == "ready_and_paid":
            return "Invoice: ready and paid"

        blocker_text = " ".join(invoice_focus_summary.blockers + invoice_focus_summary.missing_basics).lower()
        if "customer name or email" in blocker_text or "contact method" in blocker_text:
            return "Invoice: customer contact needs review"
        if "line items" in blocker_text:
            return "Invoice: item totals need review"
        if "due date" in blocker_text:
            return "Invoice: due date needs review"

        return "Invoice: basics need review"

    def _build_day_running_handoff_preview(
        self,
        *,
        readiness_label: str,
        primary_category: str,
        next_step: str,
        handoff_focus_summary: OrderHandoffFocusSummary,
    ) -> Optional[str]:
        if readiness_label not in {"Blocked for today", "Needs attention today"}:
            return None

        handoff_related_next_steps = {
            "Lock the handoff basics",
            "Confirm delivery release details",
            "Confirm pickup handoff details",
        }
        next_step_lower = next_step.lower()
        is_handoff_related = primary_category == "handoff" or next_step in handoff_related_next_steps or any(
            token in next_step_lower for token in ["handoff", "pickup", "delivery"]
        )
        if not is_handoff_related:
            return None

        if handoff_focus_summary.missing_basics:
            top_missing = handoff_focus_summary.missing_basics[0]
            if top_missing == "Confirm whether this order is pickup or delivery.":
                return "Handoff: method needs confirmation"
            if top_missing == "Add the delivery destination before this order leaves the kitchen.":
                return "Handoff: delivery address needs confirmation"
            if "pickup order" in top_missing.lower() or "collecting the pickup order" in top_missing.lower():
                return "Handoff: pickup contact needs confirmation"
            if "customer contact method" in top_missing.lower():
                if handoff_focus_summary.method_status == "pickup":
                    return "Handoff: pickup contact needs confirmation"
                if handoff_focus_summary.method_status == "delivery":
                    return "Handoff: delivery contact needs confirmation"
                return "Handoff: handoff contact needs confirmation"
            return f"Handoff: {top_missing[:1].lower() + top_missing[1:]}"

        if handoff_focus_summary.method_status == "pickup":
            handoff_time_label = handoff_focus_summary.handoff_time_label
            if handoff_time_label.startswith("Due today — ") and " at " in handoff_time_label:
                time_part = handoff_time_label.split(" at ", 1)[1]
                return f"Handoff: pickup today at {time_part}"
            if handoff_time_label.startswith("Due today — "):
                return "Handoff: pickup today"
            return f"Handoff: pickup — {handoff_time_label}"

        if handoff_focus_summary.method_status == "delivery":
            if handoff_focus_summary.handoff_time_label.startswith("Due today — "):
                if handoff_focus_summary.destination_label == "Delivery destination still missing":
                    return "Handoff: delivery today — address needs confirmation"
                return "Handoff: delivery today — address confirmed"
            if handoff_focus_summary.destination_label == "Delivery destination still missing":
                return "Handoff: delivery — address needs confirmation"
            return "Handoff: delivery — address confirmed"

        return "Handoff: method needs confirmation"

    def _build_day_running_invoice_preview(
        self,
        *,
        readiness_label: str,
        primary_category: str,
        next_step: str,
        invoice_focus_summary: OrderInvoiceFocusSummary,
    ) -> Optional[str]:
        if readiness_label not in {"Blocked for today", "Needs attention today"}:
            return None

        next_step_lower = next_step.lower()
        is_invoice_related = (
            primary_category == "invoice"
            or "invoice" in next_step_lower
            or "billing" in next_step_lower
        )
        if not is_invoice_related:
            return None

        blockers_text = " ".join(invoice_focus_summary.blockers).lower()
        missing_basics_text = " ".join(invoice_focus_summary.missing_basics).lower()

        if "customer contact method" in missing_basics_text:
            return "Invoice: customer contact needs review"
        if "customer name or email" in blockers_text:
            return "Invoice: customer identity needs review"
        if "line items" in blockers_text:
            return "Invoice: item totals need review"
        if "payment due date" in missing_basics_text or "order due date" in blockers_text:
            return "Invoice: due date needs review"
        if invoice_focus_summary.status_label == "ready_and_paid":
            return "Invoice: ready to share"
        if invoice_focus_summary.status_label == "ready_to_send":
            return "Invoice: ready to send"

        return "Invoice: basics need review"

    def _build_day_running_review_preview(
        self,
        *,
        readiness_label: str,
        next_step: str,
        review_focus_summary: OrderReviewFocusSummary,
        queue_contact_preview: Optional[str],
        queue_payment_preview: Optional[str],
        queue_handoff_preview: Optional[str],
        queue_production_preview: Optional[str],
        queue_invoice_preview: Optional[str],
    ) -> Optional[str]:
        if readiness_label not in {"Blocked for today", "Needs attention today"}:
            return None

        if any(
            preview
            for preview in (
                queue_contact_preview,
                queue_payment_preview,
                queue_handoff_preview,
                queue_production_preview,
                queue_invoice_preview,
            )
        ):
            return None

        next_step_lower = next_step.lower()
        if not any(token in next_step_lower for token in ("review", "confirm", "clarify", "recheck")):
            return None

        top_missing = review_focus_summary.missing_basics[0] if review_focus_summary.missing_basics else ""
        top_missing_lower = top_missing.lower()
        if "line items" in top_missing_lower or "pickup or delivery" in top_missing_lower:
            return "Review: order basics need confirmation"
        if "customer contact method" in top_missing_lower:
            return "Review: customer contact basics need review"

        item_summary = review_focus_summary.item_summary.strip()
        if item_summary and item_summary != "Line items still missing":
            item_count_label = review_focus_summary.item_count_label.strip()
            if item_count_label and item_count_label != "No item quantity captured":
                return f"Review: {item_count_label[:1].lower() + item_count_label[1:]} — {item_summary}"
            return f"Review: {item_summary}"

        risk_note = review_focus_summary.risk_note.strip()
        if risk_note and risk_note != "Core order basics look present from the current record.":
            return f"Review: {risk_note[:1].lower() + risk_note[1:]}"

        return "Review: order basics need confirmation"

    def _build_day_running_focus_summary(
        self,
        *,
        order: Order,
        queue_summary: OrderQueueSummary,
        invoice_summary: OrderInvoiceSummary,
        payment_summary: OrderPaymentSummary,
        payment_focus_summary: OrderPaymentFocusSummary,
        handoff_focus_summary: OrderHandoffFocusSummary,
        production_focus_summary: OrderProductionFocusSummary,
        contact_focus_summary: OrderContactFocusSummary,
        customer_summary: OrderCustomerSummary,
        invoice_focus_summary: OrderInvoiceFocusSummary,
        review_focus_summary: OrderReviewFocusSummary,
    ) -> OrderDayRunningFocusSummary:
        concerns: list[tuple[str, str, str, str]] = []

        if not invoice_summary.is_ready:
            concerns.append(
                (
                    "invoice",
                    "Invoice is still missing basics for today.",
                    "Complete invoice basics",
                    invoice_summary.missing_fields[0].replace("_", " ") if invoice_summary.missing_fields else "invoice basics missing",
                )
            )

        if payment_summary.deposit_outstanding > 0 and order.deposit_due_date is not None:
            if order.deposit_due_date <= _utcnow().date():
                concerns.append(
                    (
                        "payment",
                        f"Deposit is still unpaid for today's work ({payment_summary.deposit_outstanding:.2f} open).",
                        "Collect the overdue deposit",
                        "deposit overdue",
                    )
                )
            else:
                concerns.append(
                    (
                        "payment",
                        f"Deposit is still open ({payment_summary.deposit_outstanding:.2f}) before handoff.",
                        "Review deposit follow-up",
                        "deposit still open",
                    )
                )
        else:
            balance_due_amount = round(max(payment_summary.amount_due - payment_summary.deposit_outstanding, 0.0), 2)
            if balance_due_amount > 0 and order.balance_due_date is not None:
                if order.balance_due_date <= _utcnow().date():
                    concerns.append(
                        (
                            "payment",
                            f"Final balance is overdue for today's work ({balance_due_amount:.2f} open).",
                            "Collect the overdue balance",
                            "final balance overdue",
                        )
                    )
                elif queue_summary.is_due_today or queue_summary.is_overdue:
                    concerns.append(
                        (
                            "payment",
                            f"Final balance is still open for today's handoff ({balance_due_amount:.2f}).",
                            "Review final balance collection",
                            "final balance still open",
                        )
                    )

        if production_focus_summary.readiness_label == "Missing basics":
            concerns.append(
                (
                    "production",
                    production_focus_summary.attention_note,
                    production_focus_summary.next_step,
                    "production basics missing",
                )
            )
        elif production_focus_summary.readiness_label == "Needs clarification":
            concerns.append(
                (
                    "production",
                    production_focus_summary.attention_note,
                    production_focus_summary.next_step,
                    "production details need clarification",
                )
            )

        if handoff_focus_summary.missing_basics and (queue_summary.is_due_today or queue_summary.is_overdue):
            handoff_reason = handoff_focus_summary.missing_basics[0]
            if handoff_reason == "Confirm whether this order is pickup or delivery.":
                handoff_reason = "Confirm pickup vs delivery so today’s release plan is clear."
            concerns.append(
                (
                    "handoff",
                    handoff_reason,
                    "Lock the handoff basics",
                    "handoff basics missing",
                )
            )

        if contact_focus_summary.readiness_label == "Missing contact basics":
            concerns.append(
                (
                    "contact",
                    contact_focus_summary.attention_note,
                    contact_focus_summary.next_step,
                    "contact basics missing",
                )
            )
        elif (
            contact_focus_summary.readiness_label == "Limited contact info"
            and (queue_summary.is_due_today or queue_summary.is_overdue)
        ):
            concerns.append(
                (
                    "contact",
                    contact_focus_summary.attention_note,
                    contact_focus_summary.next_step,
                    "contact fallback is thin",
                )
            )

        priority = {
            "handoff": 0,
            "production": 1,
            "payment": 2,
            "invoice": 3,
            "contact": 4,
        }
        concerns.sort(key=lambda item: priority.get(item[0], 99))

        blocked_categories = set()
        if not invoice_summary.is_ready:
            blocked_categories.add("invoice")
        if any(
            category == "payment" and label in {"deposit overdue", "final balance overdue"}
            for category, _reason, _next, label in concerns
        ):
            blocked_categories.add("payment")
        if production_focus_summary.readiness_label == "Missing basics":
            blocked_categories.add("production")
        if handoff_focus_summary.missing_basics and (queue_summary.is_due_today or queue_summary.is_overdue):
            blocked_categories.add("handoff")
        if contact_focus_summary.readiness_label == "Missing contact basics" and (queue_summary.is_due_today or queue_summary.is_overdue):
            blocked_categories.add("contact")

        supporting_items = [reason for _category, reason, _next_step, _label in concerns[1:4]]

        if blocked_categories and concerns:
            primary_category, reason_summary, next_step, primary_label = concerns[0]
            readiness_label = "Blocked for today"
        elif concerns:
            primary_category, reason_summary, next_step, primary_label = concerns[0]
            readiness_label = "Needs attention today"
        else:
            primary_category = "none"
            primary_label = "No obvious blocker"
            if queue_summary.is_due_today:
                reason_summary = "No obvious blocker stands out from the current record for today."
                next_step = "Proceed with today’s order plan"
            elif queue_summary.is_overdue:
                reason_summary = "No obvious blocker stands out, but timing should be rechecked because the order is overdue."
                next_step = "Recheck timing and proceed"
            else:
                reason_summary = "No obvious blocker stands out from the current record for today."
                next_step = "Keep the order on track"
            readiness_label = "Ready for today"

        queue_reason_preview: Optional[str]
        queue_next_step_preview: Optional[str]
        if readiness_label == "Blocked for today":
            queue_reason_preview = self._build_queue_reason_preview(
                readiness_label=readiness_label,
                reason_summary=reason_summary,
            )
            queue_next_step_preview = self._build_queue_next_step_preview(
                next_step=next_step,
                reason_summary=reason_summary,
            )
        elif readiness_label == "Needs attention today":
            queue_reason_preview = self._build_queue_reason_preview(
                readiness_label=readiness_label,
                reason_summary=reason_summary,
            )
            queue_next_step_preview = self._build_queue_next_step_preview(
                next_step=next_step,
                reason_summary=reason_summary,
            )
        else:
            queue_reason_preview = None
            queue_next_step_preview = None

        queue_payment_trust_preview = self._build_queue_payment_trust_preview(
            payment_focus_summary=payment_focus_summary,
        )
        queue_contact_preview = self._build_day_running_contact_preview(
            readiness_label=readiness_label,
            primary_category=primary_category,
            next_step=next_step,
            contact_focus_summary=contact_focus_summary,
            customer_summary=customer_summary,
        )
        queue_payment_preview = self._build_day_running_payment_preview(
            readiness_label=readiness_label,
            primary_category=primary_category,
            next_step=next_step,
            payment_focus_summary=payment_focus_summary,
        )
        queue_handoff_preview = self._build_day_running_handoff_preview(
            readiness_label=readiness_label,
            primary_category=primary_category,
            next_step=next_step,
            handoff_focus_summary=handoff_focus_summary,
        )
        queue_production_preview = self._build_day_running_production_preview(
            readiness_label=readiness_label,
            primary_category=primary_category,
            next_step=next_step,
            production_focus_summary=production_focus_summary,
        )
        queue_invoice_preview = self._build_day_running_invoice_preview(
            readiness_label=readiness_label,
            primary_category=primary_category,
            next_step=next_step,
            invoice_focus_summary=invoice_focus_summary,
        )
        queue_review_preview = self._build_day_running_review_preview(
            readiness_label=readiness_label,
            next_step=next_step,
            review_focus_summary=review_focus_summary,
            queue_contact_preview=queue_contact_preview,
            queue_payment_preview=queue_payment_preview,
            queue_handoff_preview=queue_handoff_preview,
            queue_production_preview=queue_production_preview,
            queue_invoice_preview=queue_invoice_preview,
        )

        return OrderDayRunningFocusSummary(
            readiness_label=readiness_label,
            reason_summary=reason_summary,
            primary_blocker_category=primary_category,
            primary_blocker_label=_humanize_enum_label(primary_label),
            queue_reason_preview=queue_reason_preview,
            queue_next_step_preview=queue_next_step_preview,
            queue_payment_trust_preview=queue_payment_trust_preview,
            queue_contact_preview=queue_contact_preview,
            queue_payment_preview=queue_payment_preview,
            queue_handoff_preview=queue_handoff_preview,
            queue_production_preview=queue_production_preview,
            queue_invoice_preview=queue_invoice_preview,
            queue_review_preview=queue_review_preview,
            next_step=next_step,
            supporting_items=supporting_items,
        )

    def _build_review_focus_summary(
        self,
        order: Order,
        customer_summary: OrderCustomerSummary,
        payment_summary: OrderPaymentSummary,
        invoice_summary: OrderInvoiceSummary,
        queue_summary: OrderQueueSummary,
        risk_summary: OrderRiskSummary,
        handoff_focus_summary: OrderHandoffFocusSummary,
        payment_focus_summary: OrderPaymentFocusSummary,
        ops_summary: OrderOpsSummary,
    ) -> OrderReviewFocusSummary:
        customer_name = customer_summary.name or "Customer name still missing"

        if queue_summary.is_due_today:
            due_label = f"Due today — {_format_datetime_label(order.due_date)}"
        elif queue_summary.is_overdue:
            due_label = f"Overdue — {_format_datetime_label(order.due_date)}"
        else:
            due_label = _format_datetime_label(order.due_date)

        item_summary, item_count_label, item_count, _primary_names = self._build_item_scan_summary(order)

        if payment_summary.amount_due <= 0:
            payment_confidence = "Payment looks settled."
        elif risk_summary.has_overdue_payment:
            payment_confidence = f"Payment follow-up still risky — {payment_summary.amount_due:.2f} remains open and dated money is overdue."
        elif payment_summary.deposit_outstanding > 0:
            payment_confidence = f"Deposit still needs collection — {payment_summary.deposit_outstanding:.2f} remains open."
        else:
            payment_confidence = f"Payment is partly open — {payment_summary.amount_due:.2f} still remaining."

        if invoice_summary.is_ready:
            invoice_confidence = "Invoice basics are complete."
        else:
            invoice_confidence = "Invoice still needs attention: " + ", ".join(
                field.replace("_", " ") for field in invoice_summary.missing_fields
            )

        if handoff_focus_summary.missing_basics:
            handoff_confidence = handoff_focus_summary.missing_basics[0]
        else:
            handoff_confidence = handoff_focus_summary.readiness_note

        missing_basics: list[str] = []
        if not customer_summary.email and not customer_summary.phone:
            missing_basics.append("Add at least one customer contact method.")
        if not order.items:
            missing_basics.append("Add line items so the order contents are clear.")
        if not order.delivery_method:
            missing_basics.append("Confirm whether this order is pickup or delivery.")
        if invoice_summary.missing_fields:
            missing_basics.append("Invoice basics are incomplete for this order.")
        if risk_summary.has_overdue_payment:
            missing_basics.append("Payment follow-up is still blocking confidence.")
        for item in handoff_focus_summary.missing_basics:
            if item not in missing_basics:
                missing_basics.append(item)
        missing_basics = missing_basics[:4]

        if risk_summary.reasons:
            risk_note = " ".join(_humanize_reason(reason) for reason in risk_summary.reasons)
        elif missing_basics:
            risk_note = missing_basics[0]
        else:
            risk_note = "Core order basics look present from the current record."

        return OrderReviewFocusSummary(
            order_number=order.order_number,
            customer_name=customer_name,
            due_label=due_label,
            status_label=_humanize_enum_label(order.status.value),
            item_summary=item_summary,
            item_count_label=item_count_label,
            payment_confidence=payment_confidence,
            invoice_confidence=invoice_confidence,
            handoff_confidence=handoff_confidence,
            payment_trust_preview=self._build_review_payment_trust_preview(
                payment_focus_summary=payment_focus_summary,
            ),
            missing_basics=missing_basics,
            risk_note=risk_note,
            next_step=ops_summary.next_action,
            next_step_detail=ops_summary.ops_attention,
        )

    def _build_ops_summary(
        self,
        order: Order,
        payment_summary: OrderPaymentSummary,
        queue_summary: OrderQueueSummary,
        invoice_summary: OrderInvoiceSummary,
        risk_summary: OrderRiskSummary,
    ) -> OrderOpsSummary:
        def format_due(value: Optional[date]) -> str:
            return _format_bakery_date_only(value) if value else "not scheduled"

        def build_summary(
            *,
            action_class: str,
            next_action: str,
            ops_attention: str,
            primary_cta_label: str,
            primary_cta_panel: str,
            primary_cta_path: Optional[str] = None,
        ) -> OrderOpsSummary:
            return OrderOpsSummary(
                action_class=action_class,
                next_action=next_action,
                ops_attention=ops_attention,
                primary_cta_label=primary_cta_label,
                primary_cta_panel=primary_cta_panel,
                primary_cta_path=primary_cta_path or f"/orders/{order.id}?panel={primary_cta_panel}",
            )

        balance_due_amount = round(max(payment_summary.amount_due - payment_summary.deposit_outstanding, 0.0), 2)

        if not invoice_summary.is_ready:
            return build_summary(
                action_class="invoice_blocked",
                next_action="Complete invoice basics",
                ops_attention="Invoice blocked until missing fields are filled in.",
                primary_cta_label="Finish invoice",
                primary_cta_panel="invoice",
            )

        if payment_summary.deposit_outstanding > 0 and order.deposit_due_date is not None:
            if order.deposit_due_date <= _utcnow().date():
                return build_summary(
                    action_class="payment_now",
                    next_action="Collect overdue deposit",
                    ops_attention=(
                        f"Deposit due {format_due(order.deposit_due_date)} — "
                        f"{payment_summary.deposit_outstanding:.2f} still unpaid."
                    ),
                    primary_cta_label="Collect payment",
                    primary_cta_panel="payment",
                )
            return build_summary(
                action_class="payment_now",
                next_action="Collect deposit",
                ops_attention=(
                    f"Deposit due {format_due(order.deposit_due_date)} — "
                    f"{payment_summary.deposit_outstanding:.2f} still unpaid."
                ),
                primary_cta_label="Collect payment",
                primary_cta_panel="payment",
            )

        if balance_due_amount > 0 and order.balance_due_date is not None:
            if order.balance_due_date <= _utcnow().date():
                return build_summary(
                    action_class="payment_now",
                    next_action="Collect overdue balance",
                    ops_attention=(
                        f"Balance due {format_due(order.balance_due_date)} — "
                        f"{balance_due_amount:.2f} still unpaid."
                    ),
                    primary_cta_label="Collect payment",
                    primary_cta_panel="payment",
                )
            return build_summary(
                action_class="payment_now",
                next_action="Collect final balance",
                ops_attention=(
                    f"Balance due {format_due(order.balance_due_date)} — "
                    f"{balance_due_amount:.2f} still unpaid."
                ),
                primary_cta_label="Collect payment",
                primary_cta_panel="payment",
            )

        if queue_summary.is_due_today:
            return build_summary(
                action_class="handoff_today",
                next_action="Prep handoff for today",
                ops_attention="Order is due today — confirm production and pickup/delivery timing.",
                primary_cta_label="Prep handoff",
                primary_cta_panel="handoff",
            )

        if queue_summary.is_overdue and payment_summary.amount_due > 0:
            return build_summary(
                action_class="payment_now",
                next_action="Contact customer about overdue order",
                ops_attention="Order due date has passed and money is still outstanding.",
                primary_cta_label="Review payment",
                primary_cta_panel="payment",
            )

        if risk_summary.level == "medium":
            return build_summary(
                action_class="watch",
                next_action="Review payment follow-up",
                ops_attention="Large unpaid balance is open even though no dated payment is overdue yet.",
                primary_cta_label="Review order",
                primary_cta_panel="review",
            )

        return build_summary(
            action_class="watch",
            next_action="Monitor upcoming order",
            ops_attention=f"Due {queue_summary.days_until_due} day(s) from now.",
            primary_cta_label="Review order",
            primary_cta_panel="review",
        )

    def _build_order_reads(self, orders: Iterable[Order]) -> list[OrderRead]:
        order_list = list(orders)
        related_by_key = self._build_related_orders_map(order_list)
        return [
            self._to_order_read(
                order,
                related_orders=related_by_key.get(self._primary_history_key(order) or "", []),
            )
            for order in order_list
        ]

    def _to_order_read(
        self,
        order: Order,
        *,
        related_orders: Optional[list[Order]] = None,
    ) -> OrderRead:
        customer_name = order.customer_name or (_build_contact_name(order.customer) if order.customer else None)
        customer_email = order.customer_email or (order.customer.email if order.customer else None)
        customer_phone = order.customer_phone or (order.customer.phone if order.customer else None)
        related_order_list = related_orders
        if related_order_list is None:
            related_order_list = self._build_related_orders_map([order]).get(
                self._primary_history_key(order) or "",
                [],
            )
        payment_summary = self._build_payment_summary(order)
        queue_summary = self._build_queue_summary(order)
        invoice_summary = self._build_invoice_summary(order)
        customer_summary = OrderCustomerSummary(
            contact_id=order.customer_contact_id,
            name=customer_name,
            email=customer_email,
            phone=customer_phone,
            is_linked_contact=order.customer_contact_id is not None,
        )
        invoice_focus_summary = self._build_invoice_focus_summary(
            order,
            customer_summary,
            payment_summary,
            invoice_summary,
        )
        risk_summary = self._build_risk_summary(order, payment_summary, queue_summary)
        ops_summary = self._build_ops_summary(
            order,
            payment_summary,
            queue_summary,
            invoice_summary,
            risk_summary,
        )
        is_imported, legacy_status_raw, import_source = self._derive_import_metadata(order)
        payment_focus_summary = self._build_payment_focus_summary(
            order,
            payment_summary,
            queue_summary,
            risk_summary,
            ops_summary,
            is_imported=is_imported,
        )
        review_reasons, primary_review_reason, review_next_check = self._build_import_review_triage(
            is_imported=is_imported,
            customer_summary=customer_summary,
            invoice_summary=invoice_summary,
            risk_summary=risk_summary,
        )
        handoff_focus_summary = self._build_handoff_focus_summary(
            order,
            customer_summary,
            queue_summary,
            ops_summary,
        )
        review_focus_summary = self._build_review_focus_summary(
            order,
            customer_summary,
            payment_summary,
            invoice_summary,
            queue_summary,
            risk_summary,
            handoff_focus_summary,
            payment_focus_summary,
            ops_summary,
        )
        production_focus_summary = self._build_production_focus_summary(
            order,
            queue_summary,
            handoff_focus_summary,
        )
        contact_focus_summary = self._build_contact_focus_summary(
            order,
            customer_summary,
            queue_summary,
            risk_summary,
            ops_summary,
        )
        day_running_focus_summary = self._build_day_running_focus_summary(
            order=order,
            queue_summary=queue_summary,
            invoice_summary=invoice_summary,
            payment_summary=payment_summary,
            payment_focus_summary=payment_focus_summary,
            handoff_focus_summary=handoff_focus_summary,
            production_focus_summary=production_focus_summary,
            contact_focus_summary=contact_focus_summary,
            customer_summary=customer_summary,
            invoice_focus_summary=invoice_focus_summary,
            review_focus_summary=review_focus_summary,
        )
        priority_probe = OrderRead(
            id=order.id,
            user_id=order.user_id,
            customer_contact_id=order.customer_contact_id,
            customer_name=customer_name,
            customer_email=customer_email,
            customer_phone=customer_phone,
            due_date=order.due_date,
            delivery_method=order.delivery_method,
            notes_to_customer=order.notes_to_customer,
            internal_notes=order.internal_notes,
            deposit_amount=order.deposit_amount,
            deposit_due_date=order.deposit_due_date,
            balance_due_date=order.balance_due_date,
            order_number=order.order_number,
            status=order.status,
            payment_status=order.payment_status,
            order_date=order.order_date,
            subtotal=order.subtotal,
            tax=order.tax,
            total_amount=order.total_amount,
            balance_due=order.balance_due,
            items=list(order.items),
            created_at=order.created_at,
            updated_at=order.updated_at,
            stripe_payment_intent_id=order.stripe_payment_intent_id,
            customer_summary=customer_summary,
            payment_summary=payment_summary,
            invoice_summary=invoice_summary,
            queue_summary=queue_summary,
            customer_history_summary=self._build_customer_history_summary_from_related(
                order,
                related_order_list,
            ),
            recent_customer_orders=self._build_recent_customer_orders(
                order,
                related_order_list,
            ),
            risk_summary=risk_summary,
            payment_focus_summary=payment_focus_summary,
            handoff_focus_summary=handoff_focus_summary,
            review_focus_summary=review_focus_summary,
            production_focus_summary=production_focus_summary,
            contact_focus_summary=contact_focus_summary,
            day_running_focus_summary=day_running_focus_summary,
            invoice_focus_summary=invoice_focus_summary,
            ops_summary=ops_summary,
            is_imported=is_imported,
            legacy_status_raw=legacy_status_raw,
            import_source=import_source,
            review_reasons=review_reasons,
            primary_review_reason=primary_review_reason,
            review_next_check=review_next_check,
        )
        imported_priority_rank, imported_priority_label = self._build_import_priority(priority_probe)
        return OrderRead(
            id=order.id,
            user_id=order.user_id,
            customer_contact_id=order.customer_contact_id,
            customer_name=customer_name,
            customer_email=customer_email,
            customer_phone=customer_phone,
            due_date=order.due_date,
            delivery_method=order.delivery_method,
            notes_to_customer=order.notes_to_customer,
            internal_notes=order.internal_notes,
            deposit_amount=order.deposit_amount,
            deposit_due_date=order.deposit_due_date,
            balance_due_date=order.balance_due_date,
            order_number=order.order_number,
            status=order.status,
            payment_status=order.payment_status,
            order_date=order.order_date,
            subtotal=order.subtotal,
            tax=order.tax,
            total_amount=order.total_amount,
            balance_due=order.balance_due,
            items=list(order.items),
            created_at=order.created_at,
            updated_at=order.updated_at,
            stripe_payment_intent_id=order.stripe_payment_intent_id,
            customer_summary=customer_summary,
            payment_summary=payment_summary,
            invoice_summary=invoice_summary,
            queue_summary=queue_summary,
            customer_history_summary=self._build_customer_history_summary_from_related(
                order,
                related_order_list,
            ),
            recent_customer_orders=self._build_recent_customer_orders(
                order,
                related_order_list,
            ),
            risk_summary=risk_summary,
            payment_focus_summary=payment_focus_summary,
            review_focus_summary=review_focus_summary,
            production_focus_summary=production_focus_summary,
            contact_focus_summary=contact_focus_summary,
            day_running_focus_summary=day_running_focus_summary,
            invoice_focus_summary=invoice_focus_summary,
            ops_summary=ops_summary,
            is_imported=is_imported,
            legacy_status_raw=legacy_status_raw,
            import_source=import_source,
            review_reasons=review_reasons,
            primary_review_reason=primary_review_reason,
            review_next_check=review_next_check,
            handoff_focus_summary=handoff_focus_summary,
            imported_priority_rank=imported_priority_rank,
            imported_priority_label=imported_priority_label,
        )


class QuoteService:
    def __init__(self, session: Optional[Session] = None):
        self.session = session

    async def create_quote(self, *, quote_in: QuoteCreate, current_user: User) -> QuoteRead:
        quote = Quote(
            user_id=current_user.id,
            quote_number=self._generate_quote_number(),
            status=quote_in.status or QuoteStatus.DRAFT,
            expiry_date=quote_in.expiry_date,
            notes=quote_in.notes,
        )
        quote.items = [
            QuoteItem(
                name=item.name,
                description=item.description,
                quantity=item.quantity,
                unit_price=item.unit_price,
                total_price=round(item.quantity * item.unit_price, 2),
            )
            for item in quote_in.items
        ]
        self._recalculate_quote_totals(quote)
        self.session.add(quote)
        self.session.commit()
        self.session.refresh(quote)
        return QuoteRead.model_validate(quote)

    async def get_quotes_by_user(
        self,
        *,
        current_user: User,
        skip: int = 0,
        limit: int = 100,
        status: Optional[QuoteStatus] = None,
    ) -> list[QuoteRead]:
        statement = select(Quote).where(Quote.user_id == current_user.id)
        if status is not None:
            statement = statement.where(Quote.status == status)
        statement = statement.order_by(Quote.quote_date.desc()).offset(skip).limit(limit)
        quotes = self.session.exec(statement).all()
        return [QuoteRead.model_validate(quote) for quote in quotes]

    async def get_quote_by_id(
        self, *, quote_id: UUID, current_user: User
    ) -> Optional[QuoteRead]:
        quote = self._get_owned_quote(quote_id=quote_id, user_id=current_user.id)
        if not quote:
            return None
        return QuoteRead.model_validate(quote)

    async def update_quote(
        self, *, quote_id: UUID, quote_in: QuoteUpdate, current_user: User
    ) -> Optional[QuoteRead]:
        quote = self._get_owned_quote(quote_id=quote_id, user_id=current_user.id)
        if not quote:
            return None
        update_data = quote_in.model_dump(exclude_unset=True)
        for field in ["expiry_date", "notes", "status"]:
            if field in update_data:
                setattr(quote, field, update_data[field])
        if "items" in update_data and quote_in.items is not None:
            quote.items = [
                QuoteItem(
                    name=item.name,
                    description=item.description,
                    quantity=item.quantity,
                    unit_price=item.unit_price,
                    total_price=round(item.quantity * item.unit_price, 2),
                )
                for item in quote_in.items
            ]
        self._recalculate_quote_totals(quote)
        quote.updated_at = _utcnow()
        self.session.add(quote)
        self.session.commit()
        self.session.refresh(quote)
        return QuoteRead.model_validate(quote)

    async def delete_quote(
        self, *, quote_id: UUID, current_user: User
    ) -> Optional[QuoteRead]:
        quote = self._get_owned_quote(quote_id=quote_id, user_id=current_user.id)
        if not quote:
            return None
        quote_read = QuoteRead.model_validate(quote)
        self.session.delete(quote)
        self.session.commit()
        return quote_read

    def _get_owned_quote(self, *, quote_id: UUID, user_id: UUID) -> Optional[Quote]:
        statement = select(Quote).where(Quote.id == quote_id, Quote.user_id == user_id)
        return self.session.exec(statement).first()

    def _generate_quote_number(self) -> str:
        while True:
            candidate = f"Q-{_utcnow().strftime('%Y%m%d')}-{uuid4().hex[:6].upper()}"
            exists = self.session.exec(
                select(Quote).where(Quote.quote_number == candidate)
            ).first()
            if not exists:
                return candidate

    def _recalculate_quote_totals(self, quote: Quote) -> None:
        quote.subtotal = round(sum(item.total_price for item in quote.items), 2)
        quote.tax = 0.0
        quote.total_amount = round(quote.subtotal + quote.tax, 2)


__all__ = [
    "OrderService",
    "QuoteService",
    "calculate_order_total",
    "apply_discount",
    "get_order_by_id",
    "calculate_order_tax",
    "calculate_delivery_fee",
    "validate_order_data",
    "get_order_items",
    "cancel_order",
    "get_orders_by_date_range",
    "update_order_status",
]
