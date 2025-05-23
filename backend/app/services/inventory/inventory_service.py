from sqlmodel import Session, select
from uuid import UUID
from typing import List, Optional, Dict, Any
from fastapi import HTTPException
from decimal import Decimal

from app.models.ingredient import Ingredient
from app.models.recipe import Recipe, RecipeIngredientLink
from app.models.order import Order, OrderItem, OrderStatus
from app.models.user import User
from app.services.email_service import EmailService # For low stock alerts
from app.core.config import settings

class InventoryService:
    def __init__(self, session: Session):
        self.session = session
        self.email_service = EmailService()

    async def update_ingredient_stock(self, ingredient_id: UUID, quantity_change: float, user_id: UUID) -> Optional[Ingredient]:
        """
        Directly updates the stock for a given ingredient. 
        `quantity_change` can be positive (for adding stock) or negative (for manual deduction).
        """
        ingredient = self.session.get(Ingredient, ingredient_id)
        if not ingredient or ingredient.user_id != user_id:
            return None # Or raise HTTPException
        
        if ingredient.quantity_on_hand is None:
            ingredient.quantity_on_hand = 0
        
        ingredient.quantity_on_hand += Decimal(quantity_change)
        self.session.add(ingredient)
        self.session.commit()
        self.session.refresh(ingredient)
        
        # Check for low stock after update
        await self.check_and_notify_low_stock(ingredient, user_id)
        return ingredient

    async def deduct_stock_for_order(self, order_id: UUID, user_id: UUID) -> bool:
        """
        Deducts ingredient quantities based on recipes in a confirmed order.
        This should be called when an order status changes to a state that implies production (e.g., Confirmed).
        """
        order = self.session.get(Order, order_id)
        if not order or order.user_id != user_id:
            # Consider raising an error or returning a more specific status
            return False

        # Only deduct for orders that are confirmed or in a similar state
        # This logic might need adjustment based on the exact order workflow
        if order.status not in [OrderStatus.CONFIRMED, OrderStatus.PREPARING]: # Add other relevant statuses
            # print(f"Order 	hemed_id} not in a state for stock deduction (status: 	hemed.status}).")
            return False # Or True, if no action is needed for this status

        for item in order.items:
            if not item.recipe_id:
                continue # Skip items not linked to a recipe

            recipe = self.session.get(Recipe, item.recipe_id)
            if not recipe or recipe.user_id != user_id:
                continue # Skip if recipe not found or doesn_t belong to user

            recipe_ingredients_stmt = select(RecipeIngredientLink).where(RecipeIngredientLink.recipe_id == recipe.id)
            recipe_ingredient_links = self.session.exec(recipe_ingredients_stmt).all()

            for link in recipe_ingredient_links:
                ingredient = self.session.get(Ingredient, link.ingredient_id)
                if not ingredient or ingredient.user_id != user_id:
                    continue # Skip if ingredient not found or doesn_t belong to user
                
                if ingredient.quantity_on_hand is None: # Initialize if not set
                    ingredient.quantity_on_hand = Decimal(0)
                
                quantity_to_deduct = Decimal(item.quantity) * Decimal(link.quantity_used)
                ingredient.quantity_on_hand -= quantity_to_deduct
                self.session.add(ingredient)
                
                # Check for low stock immediately after deduction for this ingredient
                await self.check_and_notify_low_stock(ingredient, user_id)
        
        self.session.commit()
        # Refresh related ingredients if needed, but commit handles saving.
        return True

    async def check_and_notify_low_stock(self, ingredient: Ingredient, user_id: UUID):
        """
        Checks if a specific ingredient is below its low stock threshold and sends an alert if so.
        Assumes ingredient.user_id is already validated.
        """
        if (
            ingredient.quantity_on_hand is not None 
            and ingredient.low_stock_threshold is not None 
            and ingredient.quantity_on_hand < ingredient.low_stock_threshold
        ):
            baker_user = self.session.get(User, user_id)
            if baker_user and baker_user.email and settings.SENDGRID_API_KEY and settings.EMAILS_FROM_EMAIL:
                try:
                    await self.email_service.send_low_stock_alert(
                        to_email=baker_user.email,
                        ingredient_name=ingredient.name,
                        current_quantity=float(ingredient.quantity_on_hand),
                        threshold=float(ingredient.low_stock_threshold),
                        unit=ingredient.unit
                    )
                except Exception as e:
                    print(f"Failed to send low stock alert for {ingredient.name}: {e}")
                    # Log this error
            else:
                print(f"Low stock for {ingredient.name}, but email notification could not be sent (missing user email or SendGrid config).")

    async def run_low_stock_check_for_user(self, current_user: User) -> List[Dict[str, Any]]:
        """
        Checks all ingredients for a user and sends alerts for those below threshold.
        Intended to be called by a cron job or a manual trigger.
        Returns a list of ingredients that are low on stock.
        """
        low_stock_ingredients_alerted = []
        
        ingredients_stmt = select(Ingredient).where(Ingredient.user_id == current_user.id)
        all_user_ingredients = self.session.exec(ingredients_stmt).all()

        for ingredient in all_user_ingredients:
            if (
                ingredient.quantity_on_hand is not None 
                and ingredient.low_stock_threshold is not None 
                and ingredient.quantity_on_hand < ingredient.low_stock_threshold
            ):
                low_stock_ingredients_alerted.append({
                    "id": ingredient.id,
                    "name": ingredient.name,
                    "quantity_on_hand": float(ingredient.quantity_on_hand),
                    "low_stock_threshold": float(ingredient.low_stock_threshold),
                    "unit": ingredient.unit
                })
                # Send email alert (check_and_notify_low_stock handles SendGrid config check)
                await self.check_and_notify_low_stock(ingredient, current_user.id)
        
        # Note: Commits for stock changes are handled by other methods.
        # This method is primarily for checking and alerting.
        return low_stock_ingredients_alerted

    # Placeholder for API endpoint to manually adjust stock
    # (Could be part of Ingredient CRUD or a dedicated Inventory endpoint)
    async def adjust_stock_api_handler(self, ingredient_id: UUID, quantity_change: float, current_user: User):
        updated_ingredient = await self.update_ingredient_stock(
            ingredient_id=ingredient_id, 
            quantity_change=quantity_change, 
            user_id=current_user.id
        )
        if not updated_ingredient:
            raise HTTPException(status_code=404, detail="Ingredient not found or not owned by user.")
        return updated_ingredient

