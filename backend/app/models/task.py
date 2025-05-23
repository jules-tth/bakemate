from sqlmodel import SQLModel, Field, Relationship
from typing import Optional, List, TYPE_CHECKING
from enum import Enum
import uuid
from datetime import datetime

from .base import TenantBaseModel, generate_uuid

if TYPE_CHECKING:
    from .user import User
    from .order import Order # For linking tasks to orders
    # from .calendar import CalendarEvent # For linking tasks to calendar events

class TaskStatus(str, Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    DEFERRED = "deferred"

class Task(TenantBaseModel, table=True):
    user_id: uuid.UUID = Field(foreign_key="user.id")

    title: str
    description: Optional[str] = None
    status: TaskStatus = Field(default=TaskStatus.PENDING)
    due_date: Optional[datetime] = None
    priority: int = Field(default=0) # e.g., 0=Low, 1=Medium, 2=High

    order_id: Optional[uuid.UUID] = Field(default=None, foreign_key="order.id") # Optional link to an order
    # order: Optional["Order"] = Relationship()

    # If a task can have multiple calendar entries or is represented by one primary event
    # calendar_events: List["CalendarEvent"] = Relationship(back_populates="task")

# --- Pydantic Models for API --- #

class TaskBase(SQLModel):
    title: str
    description: Optional[str] = None
    status: Optional[TaskStatus] = TaskStatus.PENDING
    due_date: Optional[datetime] = None
    priority: Optional[int] = 0
    order_id: Optional[uuid.UUID] = None

class TaskCreate(TaskBase):
    user_id: uuid.UUID

class TaskRead(TaskBase):
    id: uuid.UUID
    user_id: uuid.UUID
    created_at: datetime
    updated_at: datetime

class TaskUpdate(SQLModel):
    title: Optional[str] = None
    description: Optional[str] = None
    status: Optional[TaskStatus] = None
    due_date: Optional[datetime] = None
    priority: Optional[int] = None
    order_id: Optional[uuid.UUID] = None

