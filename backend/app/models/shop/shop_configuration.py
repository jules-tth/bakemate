from sqlmodel import SQLModel, Field
from typing import Optional, List, Dict, Any
from enum import Enum
import uuid
from sqlalchemy import Column, JSON
from datetime import datetime

class ShopStatus(str, Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    MAINTENANCE = "maintenance"

class ShopProduct(SQLModel):
    recipe_id: uuid.UUID
    name: str
    price: float
    description: Optional[str] = None
    image_url: Optional[str] = None
    is_available: bool = True

class ShopConfiguration(SQLModel, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    user_id: uuid.UUID = Field(default=None, index=True, nullable=False)

    shop_slug: str = Field(unique=True, index=True, description="Unique URL-friendly slug for the shop page, e.g., /shop/{slug}")
    shop_name: Optional[str] = None
    description: Optional[str] = None
    contact_email: Optional[str] = None
    logo_url: Optional[str] = None
    theme_color_primary: Optional[str] = Field(default="#FFB6C1")
    theme_color_secondary: Optional[str] = Field(default="#F9F7F5")
    status: ShopStatus = Field(default=ShopStatus.INACTIVE)
    allow_online_orders: bool = Field(default=False)
    min_order_amount: Optional[float] = None
    max_order_amount: Optional[float] = None
    delivery_options: Optional[Dict[str, Any]] = Field(default=None, sa_column=Column(JSON))

    # Refactor this to be a Dict ensuring compatibility with JSON storage
    products_json: Dict[str, List[Dict[str, Any]]] = Field(default_factory=lambda: {"items": []}, sa_column=Column(JSON, name="products"))

    @property
    def products(self) -> List[ShopProduct]:
        return [ShopProduct(**p) for p in self.products_json.get("items", [])]

    def set_products(self, products: List[ShopProduct]):
        self.products_json["items"] = [p.dict() for p in products]

class ShopConfigurationBase(SQLModel):
    shop_slug: str
    shop_name: Optional[str] = None
    description: Optional[str] = None
    contact_email: Optional[str] = None
    logo_url: Optional[str] = None
    theme_color_primary: Optional[str] = "#FFB6C1"
    theme_color_secondary: Optional[str] = "#F9F7F5"
    status: Optional[ShopStatus] = ShopStatus.INACTIVE
    allow_online_orders: Optional[bool] = False
    min_order_amount: Optional[float] = None
    max_order_amount: Optional[float] = None
    delivery_options: Optional[Dict[str, Any]] = None
    payment_methods_accepted: Optional[List[str]] = ["stripe"]
    products: Optional[List[ShopProduct]] = []

class ShopConfigurationCreate(ShopConfigurationBase):
    user_id: uuid.UUID

class ShopConfigurationUpdate(SQLModel):
    shop_slug: Optional[str] = None
    shop_name: Optional[str] = None
    description: Optional[str] = None
    contact_email: Optional[str] = None
    logo_url: Optional[str] = None
    theme_color_primary: Optional[str] = None
    theme_color_secondary: Optional[str] = None
    status: Optional[ShopStatus] = None
    allow_online_orders: Optional[bool] = None
    min_order_amount: Optional[float] = None
    max_order_amount: Optional[float] = None
    delivery_options: Optional[Dict[str, Any]] = None
    payment_methods_accepted: Optional[List[str]] = None
    products: Optional[List[ShopProduct]] = None

class ShopConfigurationRead(ShopConfigurationBase):
    id: uuid.UUID
    user_id: uuid.UUID
    created_at: datetime
    updated_at: datetime

# Implementing PublicShopView and associated models
class PublicShopProductView(SQLModel):
    recipe_id: uuid.UUID
    name: str
    price: float
    description: Optional[str] = None
    image_url: Optional[str] = None

class PublicShopView(SQLModel):
    shop_name: Optional[str] = None
    description: Optional[str] = None
    logo_url: Optional[str] = None
    contact_email: Optional[str] = None
    theme_color_primary: Optional[str] = None
    theme_color_secondary: Optional[str] = None
    products: List[PublicShopProductView] = []
    delivery_options: Optional[Dict[str, Any]] = None
    min_order_amount: Optional[float] = None

# Implementing ShopOrderCreate and associated model
class ShopOrderItemCreate(SQLModel):
    recipe_id: uuid.UUID
    quantity: int = Field(gt=0)

class ShopOrderCreate(SQLModel):
    customer_name: str
    customer_email: str
    customer_phone: Optional[str] = None
    delivery_address: Optional[str] = None
    delivery_instructions: Optional[str] = None
    pickup_time_slot: Optional[str] = None
    items: List[ShopOrderItemCreate] = []
    shop_slug: str
