from sqlmodel import SQLModel, Field, Relationship
from typing import Optional, List, TYPE_CHECKING
from enum import Enum
import uuid
from datetime import datetime, date

from .base import TenantBaseModel, generate_uuid

if TYPE_CHECKING:
    from .user import User

class ExpenseCategory(str, Enum):
    INGREDIENTS = "ingredients"
    SUPPLIES = "supplies"
    UTILITIES = "utilities"
    RENT = "rent"
    MARKETING = "marketing"
    FEES = "fees"
    OTHER = "other"

class Expense(TenantBaseModel, table=True):
    user_id: uuid.UUID = Field(foreign_key="user.id")

    date: date
    description: str
    amount: float
    category: ExpenseCategory = Field(default=ExpenseCategory.OTHER)
    vendor: Optional[str] = None
    notes: Optional[str] = None

    # For receipt uploads
    receipt_filename: Optional[str] = None # Original filename
    receipt_s3_key: Optional[str] = None # Key if stored in S3 or similar
    receipt_url: Optional[str] = None # Public or signed URL to access the receipt

    # user: "User" = Relationship(back_populates="expenses")

# --- Pydantic Models for API --- #

class ExpenseBase(SQLModel):
    date: date
    description: str
    amount: float
    category: Optional[ExpenseCategory] = ExpenseCategory.OTHER
    vendor: Optional[str] = None
    notes: Optional[str] = None
    receipt_filename: Optional[str] = None

class ExpenseCreate(ExpenseBase):
    user_id: uuid.UUID

class ExpenseRead(ExpenseBase):
    id: uuid.UUID
    user_id: uuid.UUID
    created_at: datetime
    updated_at: datetime
    receipt_url: Optional[str] = None # Include URL in read model

class ExpenseUpdate(SQLModel):
    date: Optional[date] = None
    description: Optional[str] = None
    amount: Optional[float] = None
    category: Optional[ExpenseCategory] = None
    vendor: Optional[str] = None
    notes: Optional[str] = None
    # Receipt update might be handled by a separate endpoint or by providing new filename/key
    receipt_filename: Optional[str] = None 
    receipt_s3_key: Optional[str] = None
    receipt_url: Optional[str] = None

