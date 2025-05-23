from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import List, Optional, Any
from uuid import UUID

from sqlmodel import Session

from app.repositories.sqlite_adapter import get_session
from app.services.shop.shop_service import ShopService
from app.models.shop.shop_configuration import (
    ShopConfiguration, ShopConfigurationCreate, ShopConfigurationRead, ShopConfigurationUpdate,
    PublicShopView, ShopOrderCreate
)
from app.models.user import User
from app.models.order import OrderRead # For returning the created order from shop
from app.auth.dependencies import get_current_active_user

# Router for baker-facing shop management
management_router = APIRouter()
# Router for public-facing shop view and ordering
public_router = APIRouter()

# --- Management Endpoints (for authenticated bakers) --- #

@management_router.post("/configuration/", response_model=ShopConfigurationRead, status_code=status.HTTP_201_CREATED)
async def create_shop_configuration(
    *, 
    session: Session = Depends(get_session),
    shop_config_in: ShopConfigurationCreate,
    current_user: User = Depends(get_current_active_user)
):
    """
    Create a new shop configuration for the authenticated baker.
    A baker can only have one shop configuration.
    """
    shop_config_in.user_id = current_user.id # Ensure it's for the current user
    shop_service = ShopService(session=session)
    new_shop_config = await shop_service.create_shop_configuration(shop_config_in=shop_config_in, current_user=current_user)
    return new_shop_config

@management_router.get("/configuration/", response_model=Optional[ShopConfigurationRead])
async def get_shop_configuration(
    *, 
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_active_user)
):
    """
    Retrieve the shop configuration for the authenticated baker.
    """
    shop_service = ShopService(session=session)
    shop_config = await shop_service.get_shop_configuration_by_user(current_user=current_user)
    # if not shop_config:
    #     raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Shop configuration not found for this user.")
    return shop_config

@management_router.put("/configuration/", response_model=ShopConfigurationRead)
async def update_shop_configuration(
    *, 
    session: Session = Depends(get_session),
    shop_config_in: ShopConfigurationUpdate,
    current_user: User = Depends(get_current_active_user)
):
    """
    Update the shop configuration for the authenticated baker.
    Assumes user has one config; if not, an ID would be needed.
    """
    shop_service = ShopService(session=session)
    # Get existing config to find its ID
    existing_config = await shop_service.get_shop_configuration_by_user(current_user=current_user)
    if not existing_config:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Shop configuration not found. Create one first.")
    
    updated_shop_config = await shop_service.update_shop_configuration(
        shop_config_id=existing_config.id, shop_config_in=shop_config_in, current_user=current_user
    )
    if not updated_shop_config:
        # This case should ideally be handled by the service raising specific HTTPExceptions
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Failed to update shop configuration.")
    return updated_shop_config

@management_router.delete("/configuration/", response_model=ShopConfigurationRead) # Or just status 204
async def delete_shop_configuration(
    *, 
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_active_user)
):
    """
    Delete the shop configuration for the authenticated baker.
    """
    shop_service = ShopService(session=session)
    existing_config = await shop_service.get_shop_configuration_by_user(current_user=current_user)
    if not existing_config:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Shop configuration not found.")

    deleted_config = await shop_service.delete_shop_configuration(shop_config_id=existing_config.id, current_user=current_user)
    if not deleted_config:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Failed to delete shop configuration or not found.")
    return deleted_config

@management_router.get("/configuration/embed-snippet/", response_model=str)
async def get_shop_embed_snippet(
    *, 
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_active_user)
):
    """
    Get the embeddable HTML/JS snippet for the baker's shop.
    Requires an active shop configuration with a slug.
    """
    shop_service = ShopService(session=session)
    shop_config = await shop_service.get_shop_configuration_by_user(current_user=current_user)
    if not shop_config or not shop_config.shop_slug:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Shop configuration or slug not found. Please configure your shop first.")
    
    snippet = await shop_service.get_embed_snippet(shop_slug=shop_config.shop_slug, current_user=current_user)
    return snippet

# --- Public Endpoints (for customers viewing the shop) --- #

@public_router.get("/{shop_slug}", response_model=PublicShopView)
async def view_public_shop(
    *, 
    session: Session = Depends(get_session),
    shop_slug: str
):
    """
    Retrieve the public view of a shop by its slug.
    Only shows active shops that allow online orders.
    """
    shop_service = ShopService(session=session)
    public_shop_view = await shop_service.get_public_shop_view(shop_slug=shop_slug)
    if not public_shop_view:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Shop not found, is inactive, or does not allow online orders.")
    return public_shop_view

@public_router.post("/{shop_slug}/order", response_model=OrderRead, status_code=status.HTTP_201_CREATED)
async def place_order_from_public_shop(
    *, 
    session: Session = Depends(get_session),
    shop_slug: str,
    order_in: ShopOrderCreate # Contains customer details and items
):
    """
    Place an order from a public shop.
    The order will be created in the baker's main order system with status 'new-online'.
    Confirmation emails will be sent.
    """
    if order_in.shop_slug != shop_slug:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Shop slug in path does not match shop slug in order payload.")

    shop_service = ShopService(session=session)
    created_order = await shop_service.create_order_from_shop(order_in=order_in)
    # The created_order is an instance of the main app's Order model.
    # We need to return OrderRead.
    # This assumes OrderService.create_order returns an Order object that can be directly used for OrderRead.
    # If not, a conversion or re-fetch might be needed, but typically the ORM object is fine.
    return created_order

# Include these routers in the main API router (app/api/v1/api.py)
# e.g.:
# from app.api.v1.endpoints.shop import shop_management_router, shop_public_router
# api_router.include_router(shop_management_router, prefix="/shop/manage", tags=["Shop Management"])
# api_router.include_router(shop_public_router, prefix="/shop/public", tags=["Public Shop"])

