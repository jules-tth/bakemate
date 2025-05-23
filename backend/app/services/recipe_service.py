from datetime import datetime

from typing import List, Optional, Tuple
from uuid import UUID
from sqlmodel import Session, select, delete

from app.models.recipe import Recipe, RecipeCreate, RecipeUpdate, RecipeIngredientLink, RecipeIngredientLinkCreate
from app.models.ingredient import Ingredient
from app.models.user import User # For type hinting current_user
from app.repositories.sqlite_adapter import SQLiteRepository # Or a generic repository factory

class RecipeService:
    def __init__(self, session: Session):
        self.recipe_repo = SQLiteRepository(model=Recipe) # type: ignore
        self.ingredient_repo = SQLiteRepository(model=Ingredient) # type: ignore
        self.recipe_ingredient_link_repo = SQLiteRepository(model=RecipeIngredientLink) # type: ignore
        self.session = session

    async def _calculate_recipe_cost(self, recipe_id: UUID, ingredients_data: List[RecipeIngredientLinkCreate]) -> float:
        total_cost = 0.0
        for item_link in ingredients_data:
            ingredient = await self.ingredient_repo.get(id=item_link.ingredient_id)
            if ingredient:
                # This is a simplified cost calculation. 
                # It assumes the unit in RecipeIngredientLinkCreate matches the base unit cost of the Ingredient.
                # A more robust system would handle unit conversions (e.g., ingredient cost is per kg, recipe uses grams).
                # For now, direct multiplication.
                total_cost += ingredient.cost * item_link.quantity
            else:
                # Handle missing ingredient - maybe raise an error or skip
                print(f"Warning: Ingredient with ID {item_link.ingredient_id} not found for cost calculation.")
        return round(total_cost, 2)

    async def create_recipe(self, *, recipe_in: RecipeCreate, current_user: User) -> Recipe:
        if recipe_in.user_id != current_user.id:
            # As with ingredients, ensure ownership or raise error
            pass 

        recipe_data = recipe_in.model_dump(exclude={"ingredients"})
        db_recipe = Recipe(**recipe_data)
        # db_recipe.user_id = current_user.id # Ensure user_id is set from current_user

        # Calculate initial cost
        calculated_cost = await self._calculate_recipe_cost(recipe_id=db_recipe.id, ingredients_data=recipe_in.ingredients)
        db_recipe.calculated_cost = calculated_cost

        self.session.add(db_recipe)
        self.session.commit()
        self.session.refresh(db_recipe)

        # Create RecipeIngredientLink entries
        for ingredient_link_in in recipe_in.ingredients:
            link_data = ingredient_link_in.model_dump()
            link_data["recipe_id"] = db_recipe.id
            # Assuming TenantBaseModel requirements for RecipeIngredientLink if any (e.g. user_id)
            # If RecipeIngredientLink needs user_id, it should be added here, possibly from current_user.id
            # For now, model definition of RecipeIngredientLink does not explicitly show user_id, but TenantBaseModel might imply it.
            # Let_s assume it does not need user_id directly if it_s linked via Recipe which has user_id.
            db_link = RecipeIngredientLink(**link_data)
            self.session.add(db_link)
        
        self.session.commit()
        self.session.refresh(db_recipe) # Refresh again to get the links populated if relationships are set up correctly
        return db_recipe

    async def get_recipe_by_id(self, *, recipe_id: UUID, current_user: User) -> Optional[Recipe]:
        # Fetch recipe
        recipe = await self.recipe_repo.get(id=recipe_id)
        if not recipe or recipe.user_id != current_user.id:
            return None
        
        # Manually load ingredient links if not automatically populated by SQLModel relationship
        # (depends on session state and relationship configuration)
        # This is often needed if the session that loaded `recipe` is closed or if lazy loading is not effective here.
        links_statement = select(RecipeIngredientLink).where(RecipeIngredientLink.recipe_id == recipe.id)
        recipe.ingredient_links = self.session.exec(links_statement).all()
        return recipe

    async def get_recipes_by_user(self, *, current_user: User, skip: int = 0, limit: int = 100) -> List[Recipe]:
        links_statement = (select(Recipe, RecipeIngredientLink)
                          .join(RecipeIngredientLink, Recipe.id == RecipeIngredientLink.recipe_id)
                          .where(Recipe.user_id == current_user.id))
        result = self.session.exec(links_statement).all()

        # Map to hold the recipes.
        recipes_map = {}
        for recipe, link in result:
            user_id=str(recipe.user_id) if recipe.user_id else '',  # Ensure user_id is converted
            if recipe.id not in recipes_map:
                recipes_map[recipe.id] = recipe
                recipes_map[recipe.id].ingredient_links = []
            recipes_map[recipe.id].ingredient_links.append(link)

        # Ensure collections are appropriately set as list-like.
        recipes = [ Recipe(
                    id=recipe_id,
                    user_id=str(recipes_map[recipe_id].user_id),  # Correct conversion of user_id to string
                    name=recipes_map[recipe_id].name,
                    description=recipes_map[recipe_id].description,
                    steps=recipes_map[recipe_id].steps,
                    yield_quantity=recipes_map[recipe_id].yield_quantity,
                    yield_unit=recipes_map[recipe_id].yield_unit,
                    calculated_cost=recipes_map[recipe_id].calculated_cost,
                    ingredient_links=[link for link in recipes_map[recipe_id].ingredient_links],
                    created_at=recipes_map[recipe_id].created_at.isoformat() if isinstance(recipes_map[recipe_id].created_at, datetime) else recipes_map[recipe_id].created_at,
                    updated_at=recipes_map[recipe_id].updated_at.isoformat() if isinstance(recipes_map[recipe_id].updated_at, datetime) else recipes_map[recipe_id].updated_at,
                ) for recipe_id in recipes_map]

        return recipes

    async def update_recipe(
        self, *, recipe_id: UUID, recipe_in: RecipeUpdate, current_user: User
    ) -> Optional[Recipe]:
        db_recipe = await self.recipe_repo.get(id=recipe_id)
        if not db_recipe or db_recipe.user_id != current_user.id:
            return None

        update_data = recipe_in.model_dump(exclude_unset=True, exclude={"ingredients"})
        for key, value in update_data.items():
            setattr(db_recipe, key, value)

        if recipe_in.ingredients is not None:
            # Delete existing links
            delete_links_statement = delete(RecipeIngredientLink).where(RecipeIngredientLink.recipe_id == recipe_id)
            self.session.exec(delete_links_statement)
            # self.session.commit() # Commit deletion of old links

            # Add new links
            for ingredient_link_in in recipe_in.ingredients:
                link_data = ingredient_link_in.model_dump()
                link_data["recipe_id"] = db_recipe.id
                db_link = RecipeIngredientLink(**link_data)
                self.session.add(db_link)
            
            # Recalculate cost if ingredients change
            db_recipe.calculated_cost = await self._calculate_recipe_cost(recipe_id=db_recipe.id, ingredients_data=recipe_in.ingredients)

        self.session.add(db_recipe)
        self.session.commit()
        self.session.refresh(db_recipe)
        # Manually load links again after update
        links_statement = select(RecipeIngredientLink).where(RecipeIngredientLink.recipe_id == db_recipe.id)
        db_recipe.ingredient_links = self.session.exec(links_statement).all()
        return db_recipe

    async def delete_recipe(self, *, recipe_id: UUID, current_user: User) -> Optional[Recipe]:
        db_recipe = await self.recipe_repo.get(id=recipe_id)
        if not db_recipe or db_recipe.user_id != current_user.id:
            return None
        
        # Delete associated RecipeIngredientLink entries first to avoid foreign key constraints
        delete_links_statement = delete(RecipeIngredientLink).where(RecipeIngredientLink.recipe_id == recipe_id)
        self.session.exec(delete_links_statement)
        # self.session.commit() # Commit deletion of links

        deleted_recipe = await self.recipe_repo.delete(id=recipe_id) # This will commit the recipe deletion
        # The session commit within repo.delete() should handle it.
        return deleted_recipe

    async def update_recipe_cost_on_ingredient_change(self, ingredient_id: UUID):
        """    Find all recipes using this ingredient and update their costs.
        This should be triggered when an ingredient_s cost changes.
        """
        # Find all RecipeIngredientLink entries for this ingredient
        links_statement = select(RecipeIngredientLink).where(RecipeIngredientLink.ingredient_id == ingredient_id)
        affected_links = self.session.exec(links_statement).all()

        affected_recipe_ids = list(set([link.recipe_id for link in affected_links]))

        for recipe_id in affected_recipe_ids:
            recipe = await self.recipe_repo.get(id=recipe_id)
            if recipe:
                # Get all ingredient links for this recipe to recalculate cost
                current_ingredient_links_statement = select(RecipeIngredientLink).where(RecipeIngredientLink.recipe_id == recipe_id)
                current_ingredient_links = self.session.exec(current_ingredient_links_statement).all()
                
                # Convert to RecipeIngredientLinkCreate for cost calculation function
                ingredients_data_for_cost_calc = [
                    RecipeIngredientLinkCreate(
                        ingredient_id=link.ingredient_id, 
                        quantity=link.quantity, 
                        unit=link.unit
                    ) for link in current_ingredient_links
                ]
                
                new_cost = await self._calculate_recipe_cost(recipe_id=recipe.id, ingredients_data=ingredients_data_for_cost_calc)
                if recipe.calculated_cost != new_cost:
                    recipe.calculated_cost = new_cost
                    self.session.add(recipe)
        
        if affected_recipe_ids:
            self.session.commit()
            print(f"Updated costs for recipes affected by ingredient {ingredient_id} change.")

