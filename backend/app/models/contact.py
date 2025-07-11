from sqlmodel import SQLModel, Field, Relationship
from typing import Optional, List, TYPE_CHECKING
from pydantic import EmailStr
from enum import Enum
import uuid
from datetime import date

from .base import TenantBaseModel

if TYPE_CHECKING:
    from .order import Order  # For linking orders to a contact

    # from .user import User # A contact is usually associated with a user/bakery


class ContactType(str, Enum):
    CUSTOMER = "customer"
    SUPPLIER = "supplier"
    OTHER = "other"


class Contact(TenantBaseModel, table=True):
    user_id: uuid.UUID = Field(
        foreign_key="user.id"
    )  # The baker/user who owns this contact

    first_name: Optional[str] = None
    last_name: Optional[str] = None
    company_name: Optional[str] = None
    email: Optional[EmailStr] = Field(default=None, index=True)
    phone: Optional[str] = None
    address_line1: Optional[str] = None
    address_line2: Optional[str] = None
    city: Optional[str] = None
    state_province: Optional[str] = None
    postal_code: Optional[str] = None
    country: Optional[str] = Field(default="US")

    contact_type: ContactType = Field(default=ContactType.CUSTOMER)
    notes: Optional[str] = None

    # For CRM features like birthday reminders
    birthday: Optional[date] = None  # YYYY-MM-DD
    # anniversary: Optional[date] = None # Could be another special date

    # Relationships
    # orders: List["Order"] = Relationship(back_populates="customer")


# --- Pydantic Models for API --- #


class ContactBase(SQLModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    company_name: Optional[str] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    address_line1: Optional[str] = None
    address_line2: Optional[str] = None
    city: Optional[str] = None
    state_province: Optional[str] = None
    postal_code: Optional[str] = None
    country: Optional[str] = "US"
    contact_type: ContactType = ContactType.CUSTOMER
    notes: Optional[str] = None
    birthday: Optional[date] = None


class ContactCreate(ContactBase):
    user_id: uuid.UUID  # Must be provided


class ContactRead(ContactBase):
    id: uuid.UUID
    user_id: uuid.UUID
    created_at: str  # datetime converted to str
    updated_at: str  # datetime converted to str


class ContactUpdate(SQLModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    company_name: Optional[str] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    address_line1: Optional[str] = None
    address_line2: Optional[str] = None
    city: Optional[str] = None
    state_province: Optional[str] = None
    postal_code: Optional[str] = None
    country: Optional[str] = None
    contact_type: Optional[ContactType] = None
    notes: Optional[str] = None
    birthday: Optional[date] = None
