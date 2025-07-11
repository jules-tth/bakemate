from typing import List, Optional
from uuid import UUID
from sqlmodel import Session, select
from app.models.ingredient import Ingredient, IngredientCreate, IngredientUpdate
from app.models.user import User  # For type hinting current_user
from app.repositories.sqlite_adapter import (
    SQLiteRepository,
)  # Or a generic repository factory


def get_ingredient_by_id(ingredient_id: UUID, session: Session) -> Optional[Ingredient]:
    """Utility used by unit tests to fetch an ingredient."""
    return session.get(Ingredient, ingredient_id)


def update_ingredient_stock(
    ingredient_id: UUID, quantity_change: float, session: Session
) -> Optional[Ingredient]:
    """Simple stock update helper for unit tests."""
    ingredient = session.get(Ingredient, ingredient_id)
    if not ingredient:
        return None
    current = getattr(ingredient, "stock_quantity", 0) or 0
    ingredient.stock_quantity = current + quantity_change
    session.add(ingredient)
    session.commit()
    session.refresh(ingredient)
    return ingredient


class IngredientService:
    def __init__(self, session: Session):
        self.ingredient_repo = SQLiteRepository(model=Ingredient)  # type: ignore
        self.session = session

    async def create_ingredient(
        self, *, ingredient_in: IngredientCreate, current_user: User
    ) -> Ingredient:
        # Ensure the ingredient is associated with the current user
        # The user_id is already in IngredientCreate model, but good to enforce/check here if needed.
        if ingredient_in.user_id != current_user.id:
            # This case should ideally be caught by frontend or API validation
            # or the user_id should be set here based on current_user
            # For now, assume IngredientCreate comes with the correct user_id from a trusted source (e.g., API sets it)
            pass

        # The repository handles the actual creation
        # db_ingredient = Ingredient(**ingredient_in.model_dump(), user_id=current_user.id) # Ensure user_id is set
        db_ingredient = Ingredient(
            **ingredient_in.model_dump(exclude={"user_id"}), user_id=current_user.id
        )  # Ensure user_id is explicitly set
        self.session.add(db_ingredient)
        self.session.commit()  # Remove the await
        self.session.refresh(db_ingredient)  # Remove the await
        return db_ingredient

    async def get_ingredient_by_id(
        self, *, ingredient_id: UUID, current_user: User
    ) -> Optional[Ingredient]:
        ingredient = await self.ingredient_repo.get(id=ingredient_id)
        if ingredient and ingredient.user_id == current_user.id:
            return ingredient
        return None

    async def get_ingredients_by_user(
        self, *, current_user: User, skip: int = 0, limit: int = 100
    ) -> List[Ingredient]:
        # Using get_multi with a filter for user_id
        ingredients = await self.ingredient_repo.get_multi(
            filters={"user_id": current_user.id}, skip=skip, limit=limit
        )
        return ingredients

    async def update_ingredient(
        self,
        *,
        ingredient_id: UUID,
        ingredient_in: IngredientUpdate,
        current_user: User
    ) -> Optional[Ingredient]:
        db_ingredient = await self.ingredient_repo.get(id=ingredient_id)
        if not db_ingredient or db_ingredient.user_id != current_user.id:
            return None

        updated_ingredient = await self.ingredient_repo.update(
            db_obj=db_ingredient, obj_in=ingredient_in
        )
        return updated_ingredient

    async def delete_ingredient(
        self, *, ingredient_id: UUID, current_user: User
    ) -> Optional[Ingredient]:
        db_ingredient = await self.ingredient_repo.get(id=ingredient_id)
        if not db_ingredient or db_ingredient.user_id != current_user.id:
            return None

        deleted_ingredient = await self.ingredient_repo.delete(id=ingredient_id)
        return deleted_ingredient
