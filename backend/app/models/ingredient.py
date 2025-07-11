from datetime import datetime

from sqlmodel import SQLModel, Field, Relationship
from typing import Optional, List, TYPE_CHECKING
import uuid
from .base import TenantBaseModel  # Assuming tenant-specific data

if TYPE_CHECKING:
    from .recipe import (
        Recipe,
        RecipeIngredientLink,
    )  # Forward reference for relationship


class Ingredient(TenantBaseModel, table=True):
    # tenant_id: uuid.UUID = Field(foreign_key="tenant.id") # Example if we have a Tenant table
    user_id: Optional[uuid.UUID] = Field(
        default=None, foreign_key="user.id", nullable=True
    )  # Assuming tied to a user/bakery owner

    name: str = Field(index=True, nullable=False)
    unit: str = Field(nullable=False)  # e.g., g, kg, ml, l, pcs
    description: Optional[str] = None
    cost: float = Field(nullable=False, alias="unit_cost")  # Cost per unit
    density: Optional[float] = Field(
        default=None
    )  # Optional, e.g., g/ml for conversions

    # For real-time inventory (Differentiator B)
    quantity_on_hand: Optional[float] = Field(default=0, alias="stock_quantity")
    low_stock_threshold: Optional[float] = Field(default=None)

    # Relationship to Recipe through a link table
    recipe_links: List["RecipeIngredientLink"] = Relationship(
        back_populates="ingredient"
    )

    @property
    def unit_cost(self) -> float:
        return self.cost

    @unit_cost.setter
    def unit_cost(self, value: float) -> None:
        self.cost = value

    @property
    def stock_quantity(self) -> Optional[float]:
        return self.quantity_on_hand

    @stock_quantity.setter
    def stock_quantity(self, value: Optional[float]) -> None:
        self.quantity_on_hand = value

    def is_low_stock(self) -> bool:
        if self.low_stock_threshold is None or self.quantity_on_hand is None:
            return False
        return self.quantity_on_hand < self.low_stock_threshold


class IngredientCreate(SQLModel):
    name: str
    unit: str
    unit_cost: float = Field(alias="cost")
    description: Optional[str] = None
    density: Optional[float] = None
    user_id: Optional[uuid.UUID] = None  # Set internally
    stock_quantity: Optional[float] = Field(default=0, alias="quantity_on_hand")
    low_stock_threshold: Optional[float] = None


class IngredientRead(SQLModel):
    id: uuid.UUID
    name: str
    unit: str
    unit_cost: float = Field(alias="cost")
    description: Optional[str]
    density: Optional[float]
    user_id: uuid.UUID
    stock_quantity: Optional[float] = Field(alias="quantity_on_hand")
    low_stock_threshold: Optional[float]
    created_at: datetime
    updated_at: datetime

    def to_str(self):
        self.created_at = self.created_at.isoformat()
        self.updated_at = self.updated_at.isoformat()


class IngredientUpdate(SQLModel):
    name: Optional[str] = None
    unit: Optional[str] = None
    unit_cost: Optional[float] = Field(default=None, alias="cost")
    description: Optional[str] = None
    density: Optional[float] = None
    stock_quantity: Optional[float] = Field(default=None, alias="quantity_on_hand")
    low_stock_threshold: Optional[float] = None
