from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import List
from uuid import UUID

from sqlmodel import Session

from app.repositories.sqlite_adapter import get_session  # Or your DB session getter
from app.services.recipe_service import RecipeService
from app.services.ingredient_service import IngredientService  # For cost update trigger
from app.models.recipe import Recipe, RecipeCreate, RecipeRead, RecipeUpdate
from app.models.user import User  # For current_user dependency
from app.auth.dependencies import get_current_active_user

router = APIRouter()


@router.post("/", response_model=RecipeRead, status_code=status.HTTP_201_CREATED)
async def create_recipe(
    *,
    session: Session = Depends(get_session),
    recipe_in: RecipeCreate,
    current_user: User = Depends(get_current_active_user),
):
    """
    Create a new recipe for the authenticated user.
    """
    # Ensure recipe_in.user_id matches current_user.id or is set by service
    if recipe_in.user_id != current_user.id:
        # This should be handled, e.g., by overriding or raising an error.
        # For now, assume service or validation handles it.
        pass
    recipe_data = recipe_in.model_dump(exclude_unset=True)
    recipe_data["user_id"] = current_user.id
    recipe_in_corrected = RecipeCreate(**recipe_data)

    recipe_service = RecipeService(session=session)
    new_recipe = await recipe_service.create_recipe(
        recipe_in=recipe_in_corrected, current_user=current_user
    )
    return new_recipe


@router.get("/", response_model=List[RecipeRead])
async def read_recipes(
    *,
    session: Session = Depends(get_session),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=200),
    current_user: User = Depends(get_current_active_user),
):
    """
    Retrieve all recipes for the authenticated user.
    """
    recipe_service = RecipeService(session=session)
    recipes = await recipe_service.get_recipes_by_user(
        current_user=current_user, skip=skip, limit=limit
    )
    return recipes


@router.get("/{recipe_id}", response_model=RecipeRead)
async def read_recipe(
    *,
    session: Session = Depends(get_session),
    recipe_id: UUID,
    current_user: User = Depends(get_current_active_user),
):
    """
    Retrieve a specific recipe by ID for the authenticated user.
    """
    recipe_service = RecipeService(session=session)
    recipe = await recipe_service.get_recipe_by_id(
        recipe_id=recipe_id, current_user=current_user
    )
    if not recipe:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Recipe not found or not owned by user",
        )
    return recipe


@router.put("/{recipe_id}", response_model=RecipeRead)
async def update_recipe(
    *,
    session: Session = Depends(get_session),
    recipe_id: UUID,
    recipe_in: RecipeUpdate,
    current_user: User = Depends(get_current_active_user),
):
    """
    Update a recipe for the authenticated user.
    """
    recipe_service = RecipeService(session=session)
    updated_recipe = await recipe_service.update_recipe(
        recipe_id=recipe_id, recipe_in=recipe_in, current_user=current_user
    )
    if not updated_recipe:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Recipe not found or not owned by user",
        )

    # Optional: If ingredients were part of the update and their costs might have changed globally,
    # this is a place to consider triggering updates for other recipes, though typically
    # ingredient cost changes are handled separately (e.g., when an ingredient is updated).
    # The RecipeService.update_recipe_cost_on_ingredient_change is for that scenario.
    return updated_recipe


@router.delete("/{recipe_id}", response_model=RecipeRead)  # Or status 204
async def delete_recipe(
    *,
    session: Session = Depends(get_session),
    recipe_id: UUID,
    current_user: User = Depends(get_current_active_user),
):
    """
    Delete a recipe for the authenticated user.
    """
    recipe_service = RecipeService(session=session)
    deleted_recipe = await recipe_service.delete_recipe(
        recipe_id=recipe_id, current_user=current_user
    )
    if not deleted_recipe:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Recipe not found or not owned by user",
        )
    return deleted_recipe


# Endpoint to manually trigger cost update for recipes if an ingredient cost changes
# This might be better as a background task or an event-driven update in a real system.
@router.post(
    "/trigger-cost-update/ingredient/{ingredient_id}",
    status_code=status.HTTP_202_ACCEPTED,
)
async def trigger_recipe_cost_updates_for_ingredient(
    *,
    session: Session = Depends(get_session),
    ingredient_id: UUID,
    current_user: User = Depends(
        get_current_active_user
    ),  # Ensure only authorized users can trigger this
):
    """
    Manually trigger recalculation of costs for all recipes using a specific ingredient.
    This is useful if an ingredient_s cost is updated globally.
    Requires appropriate authorization (e.g., admin or owner of the ingredient).
    """
    # First, verify the current user has rights to manage this ingredient or trigger this global update.
    # For simplicity, we assume an active user can trigger this for ingredients they might own or manage.
    # A more robust check would be needed here.
    ingredient_service = IngredientService(session=session)
    ingredient = await ingredient_service.get_ingredient_by_id(
        ingredient_id=ingredient_id, current_user=current_user
    )
    if not ingredient:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Ingredient not found or not accessible by user.",
        )

    recipe_service = RecipeService(session=session)
    await recipe_service.update_recipe_cost_on_ingredient_change(
        ingredient_id=ingredient_id
    )
    return {
        "msg": f"Recipe cost update process triggered for ingredient {ingredient_id}"
    }
