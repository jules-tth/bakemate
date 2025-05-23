from sqlmodel import SQLModel, Field, Relationship
from typing import Optional, List, TYPE_CHECKING
from enum import Enum
import uuid
from datetime import datetime, date

from .base import TenantBaseModel, generate_uuid

if TYPE_CHECKING:
    from .user import User
    from .order import Order # For linking tasks or calendar events to orders
    from .task import Task # For linking calendar events to tasks

class CalendarEventType(str, Enum):
    ORDER_DUE_DATE = "order_due_date"
    TASK_DEADLINE = "task_deadline"
    PERSONAL_EVENT = "personal_event"
    REMINDER = "reminder"

class CalendarEvent(TenantBaseModel, table=True):
    user_id: uuid.UUID = Field(foreign_key="user.id")

    title: str
    description: Optional[str] = None
    start_datetime: datetime
    end_datetime: datetime
    is_all_day: bool = Field(default=False)

    event_type: CalendarEventType = Field(default=CalendarEventType.PERSONAL_EVENT)
    color: Optional[str] = None # e.g., hex color for display

    # For linking to other entities
    order_id: Optional[uuid.UUID] = Field(default=None, foreign_key="order.id")
    task_id: Optional[uuid.UUID] = Field(default=None, foreign_key="task.id") 

    # For Google Calendar Sync
    google_calendar_id: Optional[str] = Field(default=None, index=True) # ID of the event in Google Calendar
    google_event_id: Optional[str] = Field(default=None, index=True) # ID of this specific event instance in Google Calendar

    # order: Optional["Order"] = Relationship()
    # task: Optional["Task"] = Relationship(back_populates="calendar_events") # If Task model has a calendar_events relationship

# --- Pydantic Models for API --- #

class CalendarEventBase(SQLModel):
    title: str
    description: Optional[str] = None
    start_datetime: datetime
    end_datetime: datetime
    is_all_day: Optional[bool] = False
    event_type: Optional[CalendarEventType] = CalendarEventType.PERSONAL_EVENT
    color: Optional[str] = None
    order_id: Optional[uuid.UUID] = None
    task_id: Optional[uuid.UUID] = None

class CalendarEventCreate(CalendarEventBase):
    user_id: uuid.UUID

class CalendarEventRead(CalendarEventBase):
    id: uuid.UUID
    user_id: uuid.UUID
    created_at: datetime
    updated_at: datetime
    google_calendar_id: Optional[str] = None
    google_event_id: Optional[str] = None

class CalendarEventUpdate(SQLModel):
    title: Optional[str] = None
    description: Optional[str] = None
    start_datetime: Optional[datetime] = None
    end_datetime: Optional[datetime] = None
    is_all_day: Optional[bool] = None
    event_type: Optional[CalendarEventType] = None
    color: Optional[str] = None
    order_id: Optional[uuid.UUID] = None
    task_id: Optional[uuid.UUID] = None
    google_calendar_id: Optional[str] = None 
    google_event_id: Optional[str] = None

