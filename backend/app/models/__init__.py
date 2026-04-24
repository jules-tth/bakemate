# This file makes the 'models' directory a Python package.
# It also provides a convenient way to import all models.

from .base import BaseUUIDModel, TenantBaseModel
from .user import User, UserCreate, UserRead, UserUpdate, UserReadWithRecipes
from .ingredient import Ingredient, IngredientCreate, IngredientRead, IngredientUpdate
from .recipe import (
    Recipe,
    RecipeCreate,
    RecipeRead,
    RecipeUpdate,
    RecipeIngredientLink,
    RecipeIngredientLinkCreate,
    RecipeIngredientLinkRead,
)
from .order import (
    Order,
    OrderCreate,
    OrderCustomerSummary,
    OrderInvoiceSummary,
    OrderPaymentFocusSummary,
    OrderPaymentSummary,
    OrderRead,
    OrderUpdate,
    OrderItem,
    OrderItemCreate,
    OrderItemRead,
    OrderStatus,
    PaymentStatus,
    Quote,
)
from .contact import Contact, ContactCreate, ContactRead, ContactUpdate, ContactType
from .task import Task, TaskCreate, TaskRead, TaskUpdate, TaskStatus
from .expense import Expense, ExpenseCreate, ExpenseRead, ExpenseUpdate, ExpenseCategory
from .mileage import MileageLog, MileageLogCreate, MileageLogRead, MileageLogUpdate
from .shop import ShopConfiguration, ShopProduct, PublicShopView, ShopOrderCreate

# Resolve forward references
UserReadWithRecipes.model_rebuild()
RecipeRead.model_rebuild()

# You can define __all__ to specify what gets imported with 'from .models import *'
__all__ = [
    "BaseUUIDModel",
    "TenantBaseModel",
    "User",
    "UserCreate",
    "UserRead",
    "UserUpdate",
    "UserReadWithRecipes",
    "Ingredient",
    "IngredientCreate",
    "IngredientRead",
    "IngredientUpdate",
    "Recipe",
    "RecipeCreate",
    "RecipeRead",
    "RecipeUpdate",
    "RecipeIngredientLink",
    "RecipeIngredientLinkCreate",
    "RecipeIngredientLinkRead",
    "Order",
    "OrderCreate",
    "OrderCustomerSummary",
    "OrderInvoiceSummary",
    "OrderPaymentFocusSummary",
    "OrderPaymentSummary",
    "OrderRead",
    "OrderUpdate",
    "OrderItem",
    "OrderItemCreate",
    "OrderItemRead",
    "OrderStatus",
    "PaymentStatus",
    "Quote",
    "Contact",
    "ContactCreate",
    "ContactRead",
    "ContactUpdate",
    "ContactType",
    "Task",
    "TaskCreate",
    "TaskRead",
    "TaskUpdate",
    "TaskStatus",
    "Expense",
    "ExpenseCreate",
    "ExpenseRead",
    "ExpenseUpdate",
    "ExpenseCategory",
    "MileageLog",
    "MileageLogCreate",
    "MileageLogRead",
    "MileageLogUpdate",
    "ShopConfiguration",
    "ShopProduct",
    "PublicShopView",
    "ShopOrderCreate",
]
