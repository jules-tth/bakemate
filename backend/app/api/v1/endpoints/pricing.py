from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session
from uuid import UUID

from app.repositories.sqlite_adapter import get_session
from app.services.pricing_service import PricingService
from app.models.pricing_config import (
    PricingConfiguration,
    PricingConfigurationRead,
    PricingConfigurationUpdate,
)
from app.models.user import User
from app.auth.dependencies import get_current_active_user

router = APIRouter()


@router.get("/configuration", response_model=PricingConfigurationRead)
async def get_pricing_configuration(
    *,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_active_user)
):
    """
    Retrieve the pricing configuration for the authenticated user.
    If no configuration exists, default values might be returned by the service or it might return None.
    The service currently returns None if not found, so we might want to create one with defaults if it doesn_t exist.
    For now, let_s assume it can be None and the frontend would prompt to create one.
    Alternatively, create one on user registration with defaults.
    """
    pricing_service = PricingService(session=session)
    config = await pricing_service.get_pricing_configuration(current_user=current_user)
    if not config:
        # Optionally, create a default one here if desired, or let client handle it.
        # For now, return 404 if not explicitly set by user.
        # Or, service could return a default Pydantic model not saved to DB.
        # Let_s refine this: the service should probably create one with defaults if it doesn_t exist.
        # Modifying service `get_pricing_configuration` or `create_or_update` to handle this.
        # For now, let the service handle creation if it doesn_t exist upon an update/create call.
        # If just GETTING and it_s not there, it means user hasn_t set it up.
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Pricing configuration not found. Please create one.",
        )
    return config


@router.post("/configuration", response_model=PricingConfigurationRead)
async def create_or_update_pricing_configuration(
    *,
    session: Session = Depends(get_session),
    config_in: PricingConfigurationUpdate,  # Use Update schema as it allows partial updates / initial creation
    current_user: User = Depends(get_current_active_user)
):
    """
    Create or update the pricing configuration for the authenticated user.
    """
    pricing_service = PricingService(session=session)
    # The service method `create_or_update_pricing_configuration` handles both cases.
    config = await pricing_service.create_or_update_pricing_configuration(
        config_in=config_in, current_user=current_user
    )
    return config


# Placeholder for an endpoint that uses the pricing engine
# @router.get("/calculate/recipe/{recipe_id}", response_model=float) # Or a more complex PriceBreakdown model
# async def calculate_recipe_price(
#     *,
#     session: Session = Depends(get_session),
#     recipe_id: UUID,
#     current_user: User = Depends(get_current_active_user)
# ):
#     pricing_service = PricingService(session=session)
#     price = await pricing_service.calculate_final_price_for_recipe(recipe_id=recipe_id, current_user=current_user)
#     if price is None:
#         raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Could not calculate price. Recipe or configuration missing.")
#     return price
