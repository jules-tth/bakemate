from fastapi import APIRouter

from app.api.v1.endpoints import (
    auth,
    users,
    ingredients,
    recipes,
    pricing,
    orders,
    calendar,
    tasks,
    expenses,
    mileage,
    reports,
    inventory,
    marketing,
)
from app.api.v1.endpoints.shop import (
    shop_endpoints,
)  # Import the consolidated shop endpoints module

api_router = APIRouter()

# Auth and User routes
api_router.include_router(auth.router, prefix="/auth", tags=["Auth"])
api_router.include_router(users.router, prefix="/users", tags=["Users"])

# Recipes, Ingredients & Pricing routes
api_router.include_router(
    ingredients.router, prefix="/ingredients", tags=["Ingredients"]
)
api_router.include_router(recipes.router, prefix="/recipes", tags=["Recipes"])
api_router.include_router(pricing.router, prefix="/pricing", tags=["Pricing"])

# Orders and Quotes routes
api_router.include_router(orders.router, prefix="/orders", tags=["Orders & Quotes"])

# Calendar and Tasks routes
api_router.include_router(calendar.router, prefix="/calendar", tags=["Calendar"])
api_router.include_router(tasks.router, prefix="/tasks", tags=["Tasks"])

# Expenses, Mileage & Reports routes
api_router.include_router(expenses.router, prefix="/expenses", tags=["Expenses"])
api_router.include_router(mileage.router, prefix="/mileage", tags=["Mileage"])
api_router.include_router(reports.router, prefix="/reports", tags=["Reports"])

# Shop routes
api_router.include_router(
    shop_endpoints.management_router, prefix="/shop/manage", tags=["Shop Management"]
)
api_router.include_router(
    shop_endpoints.public_router, prefix="/shop/public", tags=["Public Shop"]
)

# Inventory routes
api_router.include_router(inventory.router, prefix="/inventory", tags=["Inventory"])

# Marketing routes
api_router.include_router(marketing.router, prefix="/marketing", tags=["Marketing"])
