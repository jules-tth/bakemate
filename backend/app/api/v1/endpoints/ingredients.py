from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import List
from uuid import UUID

from sqlmodel import Session

from app.repositories.sqlite_adapter import get_session # Or your DB session getter
from app.services.ingredient_service import IngredientService
from app.models.ingredient import Ingredient, IngredientCreate, IngredientRead, IngredientUpdate
from app.models.user import User # For current_user dependency
from app.auth.dependencies import get_current_active_user

router = APIRouter()

@router.post("/", response_model=IngredientRead, status_code=status.HTTP_201_CREATED)
async def create_ingredient(
    *, 
    session: Session = Depends(get_session),
    ingredient_in: IngredientCreate,
    current_user: User = Depends(get_current_active_user)
):
    """
    Create a new ingredient for the authenticated user.
    """
    # Ensure the ingredient_in.user_id matches the current_user.id or set it here
    if ingredient_in.user_id != current_user.id:
        # This could be an error, or we could override ingredient_in.user_id
        # For now, let's assume the API client is responsible for setting it correctly
        # or the service layer handles this logic if it's more complex.
        # A stricter approach would be to remove user_id from IngredientCreate and set it from current_user.id
        # For example: ingredient_data = ingredient_in.model_dump(); ingredient_data["user_id"] = current_user.id
        # ingredient_in_corrected = IngredientCreate(**ingredient_data)
        # For now, we rely on the service to handle it or assume it's correct.
        pass

    ingredient_service = IngredientService(session=session)
    # The service should ideally take current_user to ensure ownership
    new_ingredient = await ingredient_service.create_ingredient(ingredient_in=ingredient_in, current_user=current_user)
    return new_ingredient

@router.get("/", response_model=List[IngredientRead])
async def read_ingredients(
    *, 
    session: Session = Depends(get_session),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=200),
    current_user: User = Depends(get_current_active_user)
):
    """
    Retrieve all ingredients for the authenticated user.
    """
    ingredient_service = IngredientService(session=session)
    ingredients = await ingredient_service.get_ingredients_by_user(current_user=current_user, skip=skip, limit=limit)
    return ingredients

@router.get("/{ingredient_id}", response_model=IngredientRead)
async def read_ingredient(
    *, 
    session: Session = Depends(get_session),
    ingredient_id: UUID,
    current_user: User = Depends(get_current_active_user)
):
    """
    Retrieve a specific ingredient by ID for the authenticated user.
    """
    ingredient_service = IngredientService(session=session)
    ingredient = await ingredient_service.get_ingredient_by_id(ingredient_id=ingredient_id, current_user=current_user)
    if not ingredient:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ingredient not found or not owned by user")
    return ingredient

@router.put("/{ingredient_id}", response_model=IngredientRead)
async def update_ingredient(
    *, 
    session: Session = Depends(get_session),
    ingredient_id: UUID,
    ingredient_in: IngredientUpdate,
    current_user: User = Depends(get_current_active_user)
):
    """
    Update an ingredient for the authenticated user.
    """
    ingredient_service = IngredientService(session=session)
    updated_ingredient = await ingredient_service.update_ingredient(
        ingredient_id=ingredient_id, ingredient_in=ingredient_in, current_user=current_user
    )
    if not updated_ingredient:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ingredient not found or not owned by user")
    return updated_ingredient

@router.delete("/{ingredient_id}", response_model=IngredientRead) # Or just status 204 No Content
async def delete_ingredient(
    *, 
    session: Session = Depends(get_session),
    ingredient_id: UUID,
    current_user: User = Depends(get_current_active_user)
):
    """
    Delete an ingredient for the authenticated user.
    """
    ingredient_service = IngredientService(session=session)
    deleted_ingredient = await ingredient_service.delete_ingredient(ingredient_id=ingredient_id, current_user=current_user)
    if not deleted_ingredient:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ingredient not found or not owned by user")
    return deleted_ingredient # Or return a success message/status code

