from sqlmodel import SQLModel, Field, Relationship
from typing import Optional, List
from pydantic import EmailStr
import uuid
from .base import BaseUUIDModel


class User(BaseUUIDModel, table=True):
    email: EmailStr = Field(unique=True, index=True, nullable=False)
    hashed_password: str = Field(nullable=False)
    is_active: bool = Field(default=True)
    is_superuser: bool = Field(default=False)
    # A user belongs to a bakery/tenant. This ID links them.
    # This will be the primary key of a `Tenant` or `Bakery` table if we create one explicitly.
    # For now, we can assume a user *is* the tenant/bakery owner for simplicity in a solo baker context.
    # Or, we can add a tenant_id to all other models to scope data.
    # The prompt mentions "multi-tenant schema so each bakery’s data is isolated".
    # This implies a tenant_id on other models, and a User might manage one tenant.

    # Relationships (examples, will be fleshed out as models are created)
    # recipes: List["Recipe"] = Relationship(back_populates="owner")
    # orders: List["Order"] = Relationship(back_populates="owner")


class UserCreate(SQLModel):
    email: EmailStr
    password: str


class UserRead(SQLModel):
    id: uuid.UUID
    email: EmailStr
    is_active: bool
    is_superuser: bool


class UserUpdate(SQLModel):
    email: Optional[EmailStr] = None
    password: Optional[str] = None
    is_active: Optional[bool] = None
    is_superuser: Optional[bool] = None
