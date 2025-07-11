from datetime import datetime

from sqlmodel import SQLModel, Field, Relationship
from typing import Optional, List, TYPE_CHECKING
from pydantic import ConfigDict
import uuid
from .base import TenantBaseModel

if TYPE_CHECKING:
    from .ingredient import Ingredient, IngredientRead  # Forward reference
    from .user import User  # Forward reference


# Link table for Many-to-Many relationship between Recipe and Ingredient
class RecipeIngredientLink(TenantBaseModel, table=True):
    recipe_id: uuid.UUID = Field(
        default=None, foreign_key="recipe.id", primary_key=True
    )
    ingredient_id: uuid.UUID = Field(
        default=None, foreign_key="ingredient.id", primary_key=True
    )
    quantity: float  # Quantity of the ingredient in the recipe
    unit: str  # Unit of the ingredient for this specific recipe quantity (e.g. grams, cups)

    # Relationships to the actual Recipe and Ingredient tables
    recipe: Optional["Recipe"] = Relationship(back_populates="ingredient_links")
    ingredient: Optional["Ingredient"] = Relationship(back_populates="recipe_links")


class Recipe(TenantBaseModel, table=True):
    # tenant_id: uuid.UUID = Field(foreign_key="tenant.id")
    user_id: Optional[uuid.UUID] = Field(
        default=None, foreign_key="user.id", nullable=True
    )  # Owner of the recipe

    name: str = Field(index=True, nullable=False)
    description: Optional[str] = None
    steps: str = Field(alias="instructions")  # Could be JSON or Markdown formatted text
    prep_time: Optional[int] = None
    cook_time: Optional[int] = None
    yield_quantity: Optional[float] = None
    yield_unit: Optional[str] = None  # e.g., cookies, loaves, servings
    calculated_cost: Optional[float] = Field(
        default=0
    )  # Auto-updated based on ingredients

    # Relationship to User (owner)
    # owner: Optional["User"] = Relationship(back_populates="recipes")

    # Relationship to Ingredients via the link table
    ingredient_links: List["RecipeIngredientLink"] = Relationship(
        back_populates="recipe"
    )

    @property
    def instructions(self) -> str:
        return self.steps

    @instructions.setter
    def instructions(self, value: str) -> None:
        self.steps = value

    @property
    def total_time(self) -> Optional[int]:
        if self.prep_time is None and self.cook_time is None:
            return None
        prep = self.prep_time or 0
        cook = self.cook_time or 0
        return prep + cook


# Pydantic models for API requests/responses


class RecipeIngredientLinkCreate(SQLModel):
    ingredient_id: uuid.UUID
    quantity: float
    unit: str


class RecipeIngredientLinkRead(SQLModel):
    ingredient_id: uuid.UUID
    ingredient_name: str  # For easier display
    quantity: float
    unit: str
    cost: float  # Cost of this ingredient amount in the recipe


class RecipeCreate(SQLModel):
    user_id: Optional[uuid.UUID] = None  # Set internally
    name: str
    description: Optional[str] = None
    steps: str = Field(alias="instructions")
    prep_time: Optional[int] = None
    cook_time: Optional[int] = None
    yield_quantity: Optional[float] = None
    yield_unit: Optional[str] = None
    ingredients: List[RecipeIngredientLinkCreate] = []


class RecipeRead(SQLModel):
    id: uuid.UUID
    user_id: str  # Ensure user_id is serialized as string
    name: str
    description: Optional[str]
    steps: str
    prep_time: Optional[int]
    cook_time: Optional[int]
    yield_quantity: Optional[float]
    yield_unit: Optional[str]
    calculated_cost: Optional[float]
    ingredients: List[RecipeIngredientLinkRead] = []  # To show ingredient details
    created_at: str
    updated_at: str

    # Pydantic v2 handles ``uuid.UUID`` and ``datetime`` types natively so
    # custom JSON encoders are no longer required. Using ``json_encoders``
    # also triggers a deprecation warning in Pydantic 2.x.  The built-in
    # serializers already produce ISO formatted datetimes and strings for
    # UUIDs, so the explicit configuration has been removed.
    model_config = ConfigDict(arbitrary_types_allowed=True)


class RecipeUpdate(SQLModel):
    name: Optional[str] = None
    description: Optional[str] = None
    steps: Optional[str] = Field(default=None, alias="instructions")
    prep_time: Optional[int] = None
    cook_time: Optional[int] = None
    yield_quantity: Optional[float] = None
    yield_unit: Optional[str] = None
    ingredients: Optional[List[RecipeIngredientLinkCreate]] = (
        None  # Allow updating ingredients
    )
