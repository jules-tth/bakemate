from datetime import datetime

from sqlmodel import SQLModel, Field, Relationship
from typing import Optional, List, TYPE_CHECKING
import uuid
from .base import TenantBaseModel # Assuming tenant-specific data

if TYPE_CHECKING:
    from .recipe import Recipe, RecipeIngredientLink # Forward reference for relationship

class Ingredient(TenantBaseModel, table=True):
    # tenant_id: uuid.UUID = Field(foreign_key="tenant.id") # Example if we have a Tenant table
    user_id: uuid.UUID = Field(foreign_key="user.id") # Assuming tied to a user/bakery owner

    name: str = Field(index=True, nullable=False)
    unit: str = Field(nullable=False)  # e.g., g, kg, ml, l, pcs
    cost: float = Field(nullable=False)  # Cost per unit
    density: Optional[float] = Field(default=None)  # Optional, e.g., g/ml for conversions

    # For real-time inventory (Differentiator B)
    quantity_on_hand: Optional[float] = Field(default=0)
    low_stock_threshold: Optional[float] = Field(default=None)

    # Relationship to Recipe through a link table
    recipe_links: List["RecipeIngredientLink"] = Relationship(back_populates="ingredient")

class IngredientCreate(SQLModel):
    name: str
    unit: str
    cost: float
    density: Optional[float] = None
    user_id: Optional[uuid.UUID] = None # Set internally
    quantity_on_hand: Optional[float] = 0
    low_stock_threshold: Optional[float] = None

class IngredientRead(SQLModel):
    id: uuid.UUID
    name: str
    unit: str
    cost: float
    density: Optional[float]
    user_id: uuid.UUID
    quantity_on_hand: Optional[float]
    low_stock_threshold: Optional[float]
    created_at: datetime
    updated_at: datetime

    def to_str(self):
        self.created_at = self.created_at.isoformat()
        self.updated_at = self.updated_at.isoformat()

class IngredientUpdate(SQLModel):
    name: Optional[str] = None
    unit: Optional[str] = None
    cost: Optional[float] = None
    density: Optional[float] = None
    quantity_on_hand: Optional[float] = None
    low_stock_threshold: Optional[float] = None

