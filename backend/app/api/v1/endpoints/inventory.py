from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import List, Dict, Any
from uuid import UUID

from sqlmodel import Session

from app.repositories.sqlite_adapter import get_session
from app.services.inventory.inventory_service import InventoryService
from app.models.ingredient import IngredientRead  # To return updated ingredient
from app.models.user import User
from app.auth.dependencies import get_current_active_user

router = APIRouter()


@router.post("/ingredients/{ingredient_id}/adjust-stock", response_model=IngredientRead)
async def adjust_ingredient_stock(
    *,
    session: Session = Depends(get_session),
    ingredient_id: UUID,
    quantity_change: float = Query(
        ...,
        description="Amount to change stock by. Positive to add, negative to deduct.",
    ),
    current_user: User = Depends(get_current_active_user)
):
    """
    Manually adjust the stock quantity for a specific ingredient.
    """
    inventory_service = InventoryService(session=session)
    updated_ingredient = await inventory_service.adjust_stock_api_handler(
        ingredient_id=ingredient_id,
        quantity_change=quantity_change,
        current_user=current_user,
    )
    # The adjust_stock_api_handler in service already raises HTTPException if not found
    return updated_ingredient


@router.post("/run-low-stock-check", response_model=List[Dict[str, Any]])
async def trigger_low_stock_check(
    *,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_active_user)
):
    """
    Manually trigger a low stock check for all ingredients for the current user.
    This will also attempt to send email alerts if configured and items are low.
    Returns a list of ingredients found to be low in stock.
    """
    inventory_service = InventoryService(session=session)
    low_stock_items = await inventory_service.run_low_stock_check_for_user(
        current_user=current_user
    )
    return low_stock_items


# Note: Deduction of stock upon order confirmation should be integrated into the OrderService workflow
# when an order status changes to CONFIRMED or a similar state.
# No direct API endpoint is typically exposed for that specific action, as it_s an internal process.

# The low-stock cron job mentioned in todo.md would call `run_low_stock_check_for_user` periodically.
# Setting up actual cron jobs is outside the scope of API endpoint creation but would be a deployment task.
