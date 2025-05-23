from sqlmodel import SQLModel, Field, Relationship
from typing import Optional, TYPE_CHECKING
import uuid
from datetime import datetime, date

from .base import TenantBaseModel, generate_uuid

if TYPE_CHECKING:
    from .user import User

class MileageLog(TenantBaseModel, table=True):
    user_id: uuid.UUID = Field(foreign_key="user.id")

    date: date
    start_location: Optional[str] = None
    end_location: Optional[str] = None
    distance: float # in miles or km, user preference might be a setting
    purpose: Optional[str] = None # e.g., Delivery, Supply Run, Client Meeting
    vehicle_identifier: Optional[str] = None # e.g., "My Car", "Van"
    notes: Optional[str] = None

    # For reimbursement calculation
    reimbursement_rate: Optional[float] = Field(default=None) # Rate at the time of logging, can be from user settings
    reimbursement_amount: Optional[float] = Field(default=None) # distance * reimbursement_rate

    # user: "User" = Relationship(back_populates="mileage_logs")

# --- Pydantic Models for API --- #

class MileageLogBase(SQLModel):
    date: date
    start_location: Optional[str] = None
    end_location: Optional[str] = None
    distance: float
    purpose: Optional[str] = None
    vehicle_identifier: Optional[str] = None
    notes: Optional[str] = None
    reimbursement_rate: Optional[float] = None # Allow setting if not using global default

class MileageLogCreate(MileageLogBase):
    user_id: uuid.UUID

class MileageLogRead(MileageLogBase):
    id: uuid.UUID
    user_id: uuid.UUID
    created_at: datetime
    updated_at: datetime
    reimbursement_amount: Optional[float] = None

class MileageLogUpdate(SQLModel):
    date: Optional[date] = None
    start_location: Optional[str] = None
    end_location: Optional[str] = None
    distance: Optional[float] = None
    purpose: Optional[str] = None
    vehicle_identifier: Optional[str] = None
    notes: Optional[str] = None
    reimbursement_rate: Optional[float] = None

