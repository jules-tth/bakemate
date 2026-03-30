from sqlmodel import SQLModel, Field, Relationship
from typing import Optional, List, TYPE_CHECKING
from enum import Enum
import uuid
from datetime import date, datetime, timezone

from .base import TenantBaseModel, generate_uuid

if TYPE_CHECKING:
    from .user import User, UserRead
    from .recipe import Recipe, RecipeRead  # For linking order items to recipes
    from .contact import Contact, ContactRead


class OrderStatus(str, Enum):
    INQUIRY = "inquiry"
    QUOTE_SENT = "quote_sent"
    CONFIRMED = "confirmed"
    IN_PROGRESS = "in_progress"
    READY_FOR_PICKUP = "ready_for_pickup"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    NEW_ONLINE = "new-online"  # For differentiator A


class PaymentStatus(str, Enum):
    UNPAID = "unpaid"
    DEPOSIT_PAID = "deposit_paid"
    PAID_IN_FULL = "paid_in_full"
    REFUNDED = "refunded"


class ImportedOrderReviewReason(str, Enum):
    OVERDUE_PAYMENT_RISK = "overdue_payment_risk"
    INVOICE_MISSING_FIELDS = "invoice_missing_fields"
    MISSING_CONTACT_DETAILS = "missing_contact_details"
    UNLINKED_CONTACT = "unlinked_contact"


# This could represent an item within an order or a quote
class ItemBase(SQLModel):
    # recipe_id: Optional[uuid.UUID] = Field(default=None, foreign_key="recipe.id") # If it_s a standard recipe item
    name: str  # Name of the item (e.g., "Custom Birthday Cake", or Recipe Name)
    description: Optional[str] = None
    quantity: int
    unit_price: float  # Price for one unit of this item


class OrderItem(TenantBaseModel, table=True):
    id: uuid.UUID = Field(default_factory=generate_uuid, primary_key=True, index=True)
    order_id: uuid.UUID = Field(foreign_key="order.id")
    name: str
    description: Optional[str] = None
    quantity: int
    unit_price: float
    total_price: float  # quantity * unit_price

    # recipe: Optional["Recipe"] = Relationship()
    order: "Order" = Relationship(back_populates="items")


class Order(TenantBaseModel, table=True):
    user_id: uuid.UUID = Field(
        foreign_key="user.id"
    )  # The baker/user who owns this order
    customer_contact_id: Optional[uuid.UUID] = Field(
        default=None, foreign_key="contact.id", index=True
    )

    order_number: str = Field(unique=True, index=True)  # Human-readable order number
    customer_name: Optional[str] = None
    customer_email: Optional[str] = Field(default=None, index=True)
    customer_phone: Optional[str] = None
    status: OrderStatus = Field(default=OrderStatus.INQUIRY)
    payment_status: PaymentStatus = Field(default=PaymentStatus.UNPAID)

    order_date: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    due_date: datetime
    delivery_method: Optional[str] = None  # e.g., Pickup, Delivery

    subtotal: float = Field(default=0)
    tax: float = Field(default=0)
    total_amount: float = Field(default=0)
    deposit_amount: Optional[float] = Field(default=None)
    balance_due: Optional[float] = Field(default=None)
    deposit_due_date: Optional[date] = None
    balance_due_date: Optional[date] = None

    notes_to_customer: Optional[str] = None
    internal_notes: Optional[str] = None

    # Stripe related fields
    stripe_payment_intent_id: Optional[str] = Field(default=None, index=True)
    stripe_checkout_session_id: Optional[str] = Field(default=None)

    # Relationships
    # user: "User" = Relationship(back_populates="orders")
    customer: Optional["Contact"] = Relationship()
    items: List["OrderItem"] = Relationship(
        back_populates="order", sa_relationship_kwargs={"cascade": "all, delete-orphan"}
    )
    # attached_files: List["OrderAttachment"] = Relationship(back_populates="order")


# --- Pydantic Models for API --- #


class OrderItemCreate(ItemBase):
    # recipe_id: Optional[uuid.UUID] = None
    pass


class OrderItemRead(ItemBase):
    id: uuid.UUID
    total_price: float
    # recipe: Optional[RecipeRead] = None


class OrderBase(SQLModel):
    customer_contact_id: Optional[uuid.UUID] = None
    customer_name: Optional[str] = None
    customer_email: Optional[str] = None
    customer_phone: Optional[str] = None
    due_date: datetime
    delivery_method: Optional[str] = None
    notes_to_customer: Optional[str] = None
    internal_notes: Optional[str] = None
    deposit_amount: Optional[float] = None
    deposit_due_date: Optional[date] = None
    balance_due_date: Optional[date] = None


class OrderCreate(OrderBase):
    user_id: Optional[uuid.UUID] = None
    items: List[OrderItemCreate] = []
    status: Optional[OrderStatus] = OrderStatus.INQUIRY


class OrderCustomerSummary(SQLModel):
    contact_id: Optional[uuid.UUID] = None
    name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    is_linked_contact: bool = False


class OrderPaymentSummary(SQLModel):
    amount_paid: float
    amount_due: float
    deposit_required: float
    deposit_outstanding: float
    balance_due: float
    is_paid_in_full: bool


class OrderInvoiceSummary(SQLModel):
    is_ready: bool
    status: str
    missing_fields: List[str] = []
    pdf_path: Optional[str] = None
    client_portal_path: Optional[str] = None


class OrderQueueSummary(SQLModel):
    is_due_today: bool
    is_overdue: bool
    days_until_due: int
    due_bucket: str
    urgency_label: str
    urgency_rank: int


class OrderCustomerHistorySummary(SQLModel):
    total_orders: int
    completed_orders: int
    active_orders: int
    last_order_date: Optional[datetime] = None


class OrderRecentCustomerOrder(SQLModel):
    id: uuid.UUID
    order_number: str
    order_date: datetime
    due_date: datetime
    status: OrderStatus
    payment_status: PaymentStatus
    total_amount: float


class OrderRiskSummary(SQLModel):
    level: str
    reasons: List[str] = []
    overdue_amount: float
    outstanding_amount: float
    has_overdue_payment: bool


class OrderPaymentFocusSummary(SQLModel):
    amount_owed_now: float
    payment_state: str
    collection_stage: str
    deposit_status: str
    balance_status: str
    due_timing: str
    risk_note: str
    next_step: str
    next_step_detail: str


class OrderHandoffFocusSummary(SQLModel):
    handoff_time_label: str
    method_status: str
    method_label: str
    contact_name: Optional[str] = None
    primary_contact: str
    secondary_contact: Optional[str] = None
    destination_label: str
    destination_detail: str
    readiness_note: str
    missing_basics: List[str] = []
    next_step: str
    next_step_detail: str


class OrderReviewFocusSummary(SQLModel):
    order_number: str
    customer_name: str
    due_label: str
    status_label: str
    item_summary: str
    item_count_label: str
    payment_confidence: str
    invoice_confidence: str
    handoff_confidence: str
    missing_basics: List[str] = []
    risk_note: str
    next_step: str
    next_step_detail: str


class OrderProductionFocusSummary(SQLModel):
    contents_summary: str
    item_count_label: str
    readiness_label: str
    missing_basics: List[str] = []
    attention_note: str
    next_step: str
    next_step_detail: str


class OrderContactFocusSummary(SQLModel):
    customer_display_name: str
    best_contact_methods_summary: str
    readiness_label: str
    missing_basics: List[str] = []
    attention_note: str
    next_step: str
    next_step_detail: str


class OrderDayRunningFocusSummary(SQLModel):
    readiness_label: str
    reason_summary: str
    primary_blocker_category: str
    primary_blocker_label: str
    queue_reason_preview: Optional[str] = None
    queue_next_step_preview: Optional[str] = None
    queue_contact_preview: Optional[str] = None
    queue_payment_preview: Optional[str] = None
    queue_handoff_preview: Optional[str] = None
    queue_production_preview: Optional[str] = None
    queue_invoice_preview: Optional[str] = None
    queue_review_preview: Optional[str] = None
    next_step: str
    supporting_items: List[str] = []


class OrderDayRunningTriageFilter(str, Enum):
    BLOCKED = "blocked"
    NEEDS_ATTENTION = "needs_attention"
    READY = "ready"


class DayRunningQueueSummary(SQLModel):
    all_count: int
    blocked_count: int
    needs_attention_count: int
    ready_count: int


class OrderInvoiceFocusSummary(SQLModel):
    status_label: str
    readiness_note: str
    order_identity: str
    customer_identity: str
    amount_summary: str
    payment_context: str
    blockers: List[str] = []
    missing_basics: List[str] = []
    next_step: str
    next_step_detail: str


class OrderOpsSummary(SQLModel):
    next_action: str
    ops_attention: str
    action_class: str
    primary_cta_label: str
    primary_cta_path: str
    primary_cta_panel: str


class OrderRead(OrderBase):
    id: uuid.UUID
    user_id: uuid.UUID
    order_number: str
    status: OrderStatus
    payment_status: PaymentStatus
    order_date: datetime
    subtotal: float
    tax: float
    total_amount: float
    balance_due: Optional[float]
    # customer: Optional[ContactRead] = None
    items: List[OrderItemRead] = []
    created_at: datetime
    updated_at: datetime
    stripe_payment_intent_id: Optional[str] = None
    customer_summary: OrderCustomerSummary
    payment_summary: OrderPaymentSummary
    invoice_summary: OrderInvoiceSummary
    queue_summary: OrderQueueSummary
    customer_history_summary: OrderCustomerHistorySummary
    recent_customer_orders: List[OrderRecentCustomerOrder] = []
    risk_summary: OrderRiskSummary
    payment_focus_summary: OrderPaymentFocusSummary
    handoff_focus_summary: OrderHandoffFocusSummary
    review_focus_summary: OrderReviewFocusSummary
    production_focus_summary: OrderProductionFocusSummary
    contact_focus_summary: OrderContactFocusSummary
    day_running_focus_summary: OrderDayRunningFocusSummary
    invoice_focus_summary: OrderInvoiceFocusSummary
    ops_summary: OrderOpsSummary
    is_imported: bool = False
    legacy_status_raw: Optional[str] = None
    import_source: Optional[str] = None
    review_reasons: List[ImportedOrderReviewReason] = []
    primary_review_reason: Optional[ImportedOrderReviewReason] = None
    review_next_check: Optional[str] = None
    imported_priority_rank: int = 0
    imported_priority_label: Optional[str] = None


class ImportedOrderQueueSummary(SQLModel):
    all_imported_count: int
    needs_review_count: int
    no_current_review_count: int
    review_reason_counts: dict[ImportedOrderReviewReason, int] = {}


class OrderUpdate(SQLModel):
    customer_contact_id: Optional[uuid.UUID] = None
    customer_name: Optional[str] = None
    customer_email: Optional[str] = None
    customer_phone: Optional[str] = None
    due_date: Optional[datetime] = None
    delivery_method: Optional[str] = None
    status: Optional[OrderStatus] = None
    payment_status: Optional[PaymentStatus] = None
    notes_to_customer: Optional[str] = None
    internal_notes: Optional[str] = None
    items: Optional[List[OrderItemCreate]] = None  # Allow updating items
    deposit_amount: Optional[float] = None
    deposit_due_date: Optional[date] = None
    balance_due_date: Optional[date] = None
    stripe_payment_intent_id: Optional[str] = None
    stripe_checkout_session_id: Optional[str] = None


# --- Quote Models --- #
class QuoteStatus(str, Enum):
    DRAFT = "draft"
    SENT = "sent"
    ACCEPTED = "accepted"
    DECLINED = "declined"
    EXPIRED = "expired"


class QuoteItem(TenantBaseModel, table=True):
    id: uuid.UUID = Field(default_factory=generate_uuid, primary_key=True, index=True)
    quote_id: uuid.UUID = Field(foreign_key="quote.id")
    name: str
    description: Optional[str] = None
    quantity: int
    unit_price: float
    total_price: float

    # recipe_id: Optional[uuid.UUID] = Field(default=None, foreign_key="recipe.id")
    # recipe: Optional["Recipe"] = Relationship()
    quote: "Quote" = Relationship(back_populates="items")


class Quote(TenantBaseModel, table=True):
    user_id: uuid.UUID = Field(foreign_key="user.id")
    # customer_id: Optional[uuid.UUID] = Field(default=None, foreign_key="contact.id")

    quote_number: str = Field(unique=True, index=True)
    status: QuoteStatus = Field(default=QuoteStatus.DRAFT)
    quote_date: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    expiry_date: Optional[datetime] = None
    notes: Optional[str] = None
    subtotal: float = Field(default=0)
    tax: float = Field(default=0)  # Or link to a tax rate model
    total_amount: float = Field(default=0)

    # user: "User" = Relationship(back_populates="quotes")
    # customer: Optional["Contact"] = Relationship()
    items: List["QuoteItem"] = Relationship(
        back_populates="quote", sa_relationship_kwargs={"cascade": "all, delete-orphan"}
    )
    converted_to_order_id: Optional[uuid.UUID] = Field(
        default=None, foreign_key="order.id"
    )
    # converted_order: Optional["Order"] = Relationship()


# --- Pydantic Models for Quote API --- #


class QuoteItemCreate(ItemBase):
    # recipe_id: Optional[uuid.UUID] = None
    pass


class QuoteItemRead(ItemBase):
    id: uuid.UUID
    total_price: float
    # recipe: Optional[RecipeRead] = None


class QuoteBase(SQLModel):
    # customer_id: Optional[uuid.UUID] = None
    expiry_date: Optional[datetime] = None
    notes: Optional[str] = None


class QuoteCreate(QuoteBase):
    user_id: uuid.UUID
    items: List[QuoteItemCreate] = []
    status: Optional[QuoteStatus] = QuoteStatus.DRAFT


class QuoteRead(QuoteBase):
    id: uuid.UUID
    user_id: uuid.UUID
    quote_number: str
    status: QuoteStatus
    quote_date: datetime
    subtotal: float
    tax: float
    total_amount: float
    items: List[QuoteItemRead] = []
    created_at: datetime
    updated_at: datetime
    converted_to_order_id: Optional[uuid.UUID] = None


class QuoteUpdate(SQLModel):
    # customer_id: Optional[uuid.UUID] = None
    expiry_date: Optional[datetime] = None
    notes: Optional[str] = None
    status: Optional[QuoteStatus] = None
    items: Optional[List[QuoteItemCreate]] = None
