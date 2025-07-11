from sqlmodel import SQLModel, Field
from typing import Optional
from uuid import UUID

from .base import TenantBaseModel  # Assuming pricing config is per user/tenant


class PricingConfiguration(TenantBaseModel, table=True):
    user_id: UUID = Field(
        foreign_key="user.id", unique=True
    )  # Each user has one pricing config

    hourly_rate: float = Field(default=25.0)  # Default hourly rate
    overhead_per_month: float = Field(default=100.0)  # Default monthly overhead
    # How overhead is distributed (e.g., per_order, per_hour_of_labor) - for now, assume per_order implicitly
    # Default profit margin percentage (optional, can be applied per recipe or globally)
    # profit_margin_percent: Optional[float] = Field(default=None)


# Pydantic models for API
class PricingConfigurationBase(SQLModel):
    hourly_rate: Optional[float] = None
    overhead_per_month: Optional[float] = None


class PricingConfigurationCreate(PricingConfigurationBase):
    user_id: UUID  # Must be set on creation
    hourly_rate: float = 25.0
    overhead_per_month: float = 100.0


class PricingConfigurationRead(PricingConfigurationBase):
    id: UUID
    user_id: UUID
    hourly_rate: float
    overhead_per_month: float
    created_at: str  # datetime
    updated_at: str  # datetime


class PricingConfigurationUpdate(SQLModel):
    hourly_rate: Optional[float] = None
    overhead_per_month: Optional[float] = None
