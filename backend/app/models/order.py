from sqlmodel import SQLModel, Field, Relationship
from typing import Optional, List, TYPE_CHECKING
from enum import Enum
import uuid
from datetime import date, datetime

from .base import TenantBaseModel, generate_uuid

if TYPE_CHECKING:
    from .user import User, UserRead
    from .recipe import Recipe, RecipeRead # For linking order items to recipes
    # from .contact import Contact, ContactRead # For linking to a customer

class OrderStatus(str, Enum):
    INQUIRY = "inquiry"
    QUOTE_SENT = "quote_sent"
    CONFIRMED = "confirmed"
    IN_PROGRESS = "in_progress"
    READY_FOR_PICKUP = "ready_for_pickup"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    NEW_ONLINE = "new-online" # For differentiator A

class PaymentStatus(str, Enum):
    UNPAID = "unpaid"
    DEPOSIT_PAID = "deposit_paid"
    PAID_IN_FULL = "paid_in_full"
    REFUNDED = "refunded"

# This could represent an item within an order or a quote
class ItemBase(SQLModel):
    # recipe_id: Optional[uuid.UUID] = Field(default=None, foreign_key="recipe.id") # If it_s a standard recipe item
    name: str # Name of the item (e.g., "Custom Birthday Cake", or Recipe Name)
    description: Optional[str] = None
    quantity: int
    unit_price: float # Price for one unit of this item

class OrderItem(TenantBaseModel, table=True):
    id: uuid.UUID = Field(default_factory=generate_uuid, primary_key=True, index=True)
    order_id: uuid.UUID = Field(foreign_key="order.id")
    name: str 
    description: Optional[str] = None
    quantity: int
    unit_price: float 
    total_price: float # quantity * unit_price

    # recipe: Optional["Recipe"] = Relationship()
    order: "Order" = Relationship(back_populates="items")

class Order(TenantBaseModel, table=True):
    user_id: uuid.UUID = Field(foreign_key="user.id") # The baker/user who owns this order
    # customer_id: Optional[uuid.UUID] = Field(default=None, foreign_key="contact.id") # Link to CRM

    order_number: str = Field(unique=True, index=True) # Human-readable order number
    status: OrderStatus = Field(default=OrderStatus.INQUIRY)
    payment_status: PaymentStatus = Field(default=PaymentStatus.UNPAID)

    order_date: datetime = Field(default_factory=datetime.utcnow)
    due_date: datetime
    delivery_method: Optional[str] = None # e.g., Pickup, Delivery

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
    # customer: Optional["Contact"] = Relationship()
    items: List["OrderItem"] = Relationship(back_populates="order", sa_relationship_kwargs={"cascade": "all, delete-orphan"})
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
    # customer_id: Optional[uuid.UUID] = None
    due_date: datetime
    delivery_method: Optional[str] = None
    notes_to_customer: Optional[str] = None
    internal_notes: Optional[str] = None
    deposit_amount: Optional[float] = None
    deposit_due_date: Optional[date] = None
    balance_due_date: Optional[date] = None

class OrderCreate(OrderBase):
    user_id: uuid.UUID
    items: List[OrderItemCreate] = []
    status: Optional[OrderStatus] = OrderStatus.INQUIRY

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

class OrderUpdate(SQLModel):
    # customer_id: Optional[uuid.UUID] = None
    due_date: Optional[datetime] = None
    delivery_method: Optional[str] = None
    status: Optional[OrderStatus] = None
    payment_status: Optional[PaymentStatus] = None
    notes_to_customer: Optional[str] = None
    internal_notes: Optional[str] = None
    items: Optional[List[OrderItemCreate]] = None # Allow updating items
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
    quote_date: datetime = Field(default_factory=datetime.utcnow)
    expiry_date: Optional[datetime] = None
    notes: Optional[str] = None
    subtotal: float = Field(default=0)
    tax: float = Field(default=0) # Or link to a tax rate model
    total_amount: float = Field(default=0)

    # user: "User" = Relationship(back_populates="quotes")
    # customer: Optional["Contact"] = Relationship()
    items: List["QuoteItem"] = Relationship(back_populates="quote", sa_relationship_kwargs={"cascade": "all, delete-orphan"})
    converted_to_order_id: Optional[uuid.UUID] = Field(default=None, foreign_key="order.id")
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

