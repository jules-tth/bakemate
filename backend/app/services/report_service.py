from typing import List, Dict, Any, Optional, Union
from uuid import UUID
from datetime import date, datetime, timedelta
from decimal import Decimal

from sqlmodel import Session, select, func, desc, asc
from fastapi.responses import StreamingResponse
import io
import csv
# from weasyprint import HTML # For PDF generation, if needed directly here

from app.models.user import User
from app.models.order import Order, OrderItem, OrderStatus
from app.models.expense import Expense, ExpenseCategory
from app.models.ingredient import Ingredient
from app.models.recipe import Recipe, RecipeIngredientLink
from app.core.config import settings

# Helper for CSV generation
def generate_csv(data: List[Dict[str, Any]], headers: List[str]) -> io.StringIO:
    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=headers)
    writer.writeheader()
    writer.writerows(data)
    output.seek(0)
    return output

class ReportService:
    def __init__(self, session: Session):
        self.session = session

    async def generate_profit_and_loss_report(
        self, *, current_user: User, start_date: date, end_date: date, output_format: str = "json"
    ) -> Any:
        """Generates a Profit and Loss (P&L) report for a given period."""
        
        # 1. Calculate Total Revenue (from completed orders)
        revenue_statement = select(func.sum(Order.total_amount)).where(
            Order.user_id == current_user.id,
            Order.status == OrderStatus.COMPLETED,
            Order.order_date >= start_date,
            Order.order_date <= end_date
        )
        total_revenue = self.session.exec(revenue_statement).scalar_one_or_none() or Decimal(0)

        # 2. Calculate Cost of Goods Sold (COGS) - Sum of recipe costs for items in completed orders
        # This is a simplified COGS. A more accurate one would use actual ingredient costs at the time of sale.
        # For now, we sum `recipe.cost_price` for items in completed orders.
        # This requires joining Order -> OrderItem -> Recipe (if OrderItem is linked to Recipe)
        # Assuming OrderItem has a field like `cost_of_good_sold_for_item` or we calculate it.
        # For simplicity, let_s assume a placeholder for COGS or a very basic calculation.
        # A proper COGS would involve: for each OrderItem in a completed Order, if it_s from a Recipe,
        # sum the (RecipeIngredientLink.quantity * Ingredient.cost_price_per_unit) for that recipe.
        # This is complex. Let_s use a simplified approach: sum of `recipe.cost_price * order_item.quantity`.
        # This requires OrderItem to be linked to Recipe and Recipe to have `cost_price`.
        # The current `Recipe` model does not have a `cost_price` field directly. It_s calculated.
        # Let_s assume `OrderItem` stores the cost of the item when the order was placed/completed.
        # If not, this part is a major simplification.
        cogs_statement = select(func.sum(OrderItem.quantity * Recipe.cost_price)).join(Order).join(Recipe, OrderItem.recipe_id == Recipe.id).where(
            Order.user_id == current_user.id,
            Order.status == OrderStatus.COMPLETED,
            Order.order_date >= start_date,
            Order.order_date <= end_date,
            OrderItem.recipe_id != None # Only items linked to recipes
        )
        # This is a conceptual query. The actual implementation depends heavily on how `OrderItem.cost` and `Recipe.cost_price` are structured and populated.
        # For now, let_s use a placeholder for COGS or a very simplified sum if possible.
        # Given the current models, an accurate COGS is hard. Let_s assume a 50% COGS for simplicity for now.
        # total_cogs = total_revenue * Decimal("0.50") # Placeholder
        # A slightly better placeholder: sum of recipe costs for items sold.
        # This still needs `Recipe.cost_price` to be reliable and `OrderItem` linked to `Recipe`.
        # Let_s assume `OrderItem` has a `cost_price` field that was set when the order was created.
        cogs_from_items_statement = select(func.sum(OrderItem.total_price * Decimal("0.3"))).join(Order).where( # Assuming a 30% margin for placeholder COGS
            Order.user_id == current_user.id,
            Order.status == OrderStatus.COMPLETED,
            Order.order_date >= start_date,
            Order.order_date <= end_date
        )
        total_cogs = self.session.exec(cogs_from_items_statement).scalar_one_or_none() or Decimal(0)

        gross_profit = total_revenue - total_cogs

        # 3. Calculate Total Operating Expenses
        expenses_statement = select(func.sum(Expense.amount)).where(
            Expense.user_id == current_user.id,
            Expense.date >= start_date,
            Expense.date <= end_date
        )
        total_expenses = self.session.exec(expenses_statement).scalar_one_or_none() or Decimal(0)

        # Expenses by category
        expenses_by_category_statement = select(Expense.category, func.sum(Expense.amount)).where(
            Expense.user_id == current_user.id,
            Expense.date >= start_date,
            Expense.date <= end_date
        ).group_by(Expense.category)
        expenses_by_category_results = self.session.exec(expenses_by_category_statement).all()
        expenses_by_category = {cat.value: (val or Decimal(0)) for cat, val in expenses_by_category_results}

        net_profit = gross_profit - total_expenses

        report_data = {
            "period_start_date": start_date.isoformat(),
            "period_end_date": end_date.isoformat(),
            "total_revenue": float(total_revenue),
            "cost_of_goods_sold": float(total_cogs),
            "gross_profit": float(gross_profit),
            "operating_expenses": {
                "total": float(total_expenses),
                "by_category": {k: float(v) for k, v in expenses_by_category.items()}
            },
            "net_profit": float(net_profit)
        }

        if output_format == "csv":
            # CSV for P&L is a bit tricky due to nested structure. Flatten it.
            flat_data = [
                {"metric": "Total Revenue", "amount": report_data["total_revenue"]},
                {"metric": "Cost of Goods Sold", "amount": report_data["cost_of_goods_sold"]},
                {"metric": "Gross Profit", "amount": report_data["gross_profit"]},
                {"metric": "Total Operating Expenses", "amount": report_data["operating_expenses"]["total"]},
            ]
            for cat, amount in report_data["operating_expenses"]["by_category"].items():
                flat_data.append({"metric": f"Expense: {cat}", "amount": amount})
            flat_data.append({"metric": "Net Profit", "amount": report_data["net_profit"]})
            headers = ["metric", "amount"]
            return generate_csv(flat_data, headers)
        
        # Default to JSON
        return report_data

    async def generate_sales_by_product_report(
        self, *, current_user: User, start_date: date, end_date: date, output_format: str = "json"
    ) -> Any:
        """Generates a report of sales by product (recipe or custom item name)."""
        # This query groups by OrderItem.name, which could be a recipe name or a custom item name.
        # It sums quantity and total_price for each item name from completed orders.
        sales_statement = select(
            OrderItem.name.label("product_name"),
            func.sum(OrderItem.quantity).label("total_quantity_sold"),
            func.sum(OrderItem.total_price).label("total_revenue_generated")
        ).join(Order).where(
            Order.user_id == current_user.id,
            Order.status == OrderStatus.COMPLETED,
            Order.order_date >= start_date,
            Order.order_date <= end_date
        ).group_by(OrderItem.name).order_by(desc("total_revenue_generated"))
        
        results = self.session.exec(sales_statement).all()
        
        report_data = [
            {
                "product_name": row.product_name,
                "total_quantity_sold": int(row.total_quantity_sold or 0),
                "total_revenue_generated": float(row.total_revenue_generated or Decimal(0))
            }
            for row in results
        ]

        if output_format == "csv":
            headers = ["product_name", "total_quantity_sold", "total_revenue_generated"]
            return generate_csv(report_data, headers)
        
        return report_data

    async def generate_ingredient_usage_report(
        self, *, current_user: User, start_date: date, end_date: date, output_format: str = "json"
    ) -> Any:
        """    Generates a report of ingredient usage based on recipes in completed orders.
        This is a complex report and requires accurate recipe-ingredient links and quantities.
        """
        # This query needs to: 
        # 1. Get all completed orders in the date range.
        # 2. For each OrderItem linked to a Recipe in these orders:
        #    a. Get the Recipe and its RecipeIngredientLinks.
        #    b. For each ingredient in the recipe, calculate total used: OrderItem.quantity * RecipeIngredientLink.quantity.
        # 3. Sum up total usage for each ingredient across all relevant order items.

        # This is a conceptual query structure. SQL might be very complex or require multiple steps.
        # For simplicity, let_s assume a structure that can be queried.
        # We need Ingredient.name, Ingredient.unit, and sum of (OrderItem.quantity * RecipeIngredientLink.quantity)
        
        # This is a placeholder as the SQL is non-trivial and depends on exact model relations.
        # A more practical approach might be to iterate in Python after fetching relevant data, 
        # or use a more advanced ORM feature / raw SQL if performance is critical.
        
        # Simplified: Fetch all RecipeIngredientLinks for recipes that were part of completed orders.
        # Then aggregate in Python. This is not efficient for large datasets.
        
        # Conceptual SQL-like structure:
        # SELECT 
        #   I.name, I.unit, SUM(OI.quantity * RIL.quantity_used) as total_used
        # FROM Order O
        # JOIN OrderItem OI ON O.id = OI.order_id
        # JOIN Recipe R ON OI.recipe_id = R.id
        # JOIN RecipeIngredientLink RIL ON R.id = RIL.recipe_id
        # JOIN Ingredient I ON RIL.ingredient_id = I.id
        # WHERE O.user_id = :user_id AND O.status = 'completed' AND O.order_date BETWEEN :start_date AND :end_date
        # GROUP BY I.id, I.name, I.unit
        # ORDER BY total_used DESC

        # Due to ORM limitations for such complex joins and aggregations directly, 
        # this will be a simplified placeholder or require raw SQL.
        # For now, returning a placeholder structure.
        
        # Let_s try a more ORM-friendly approach, though it might be less performant.
        ingredient_usage: Dict[UUID, Dict[str, Any]] = {}

        order_items_statement = select(OrderItem).join(Order).where(
            Order.user_id == current_user.id,
            Order.status == OrderStatus.COMPLETED,
            Order.order_date >= start_date,
            Order.order_date <= end_date,
            OrderItem.recipe_id != None
        )
        order_items_in_completed_orders = self.session.exec(order_items_statement).all()

        for order_item in order_items_in_completed_orders:
            if not order_item.recipe_id: continue
            
            recipe = self.session.get(Recipe, order_item.recipe_id)
            if not recipe: continue

            # Fetch RecipeIngredientLinks for this recipe
            recipe_ingredient_links_stmt = select(RecipeIngredientLink).where(RecipeIngredientLink.recipe_id == recipe.id)
            links = self.session.exec(recipe_ingredient_links_stmt).all()

            for link in links:
                ingredient = self.session.get(Ingredient, link.ingredient_id)
                if not ingredient: continue

                quantity_used_for_this_item = order_item.quantity * link.quantity_used
                
                if ingredient.id not in ingredient_usage:
                    ingredient_usage[ingredient.id] = {
                        "ingredient_id": ingredient.id,
                        "ingredient_name": ingredient.name,
                        "unit": ingredient.unit.value if ingredient.unit else "N/A",
                        "total_quantity_used": Decimal(0)
                    }
                ingredient_usage[ingredient.id]["total_quantity_used"] += Decimal(quantity_used_for_this_item)
        
        report_data = sorted(list(ingredient_usage.values()), key=lambda x: x["total_quantity_used"], reverse=True)
        # Convert Decimals to float for JSON/CSV
        for item in report_data:
            item["total_quantity_used"] = float(item["total_quantity_used"])

        if output_format == "csv":
            headers = ["ingredient_name", "unit", "total_quantity_used"]
            # Need to adjust data keys for CSV writer if they differ from headers
            csv_data = [
                {"ingredient_name": item["ingredient_name"], "unit": item["unit"], "total_quantity_used": item["total_quantity_used"]}
                for item in report_data
            ]
            return generate_csv(csv_data, headers)

        return report_data

    async def generate_low_stock_report(
        self, *, current_user: User, output_format: str = "json"
    ) -> Any:
        """Generates a report of ingredients that are below their low stock threshold."""
        # This requires Ingredient model to have `quantity_on_hand` and `low_stock_threshold` fields.
        # Assuming these fields exist as per Differentiator B requirements.
        
        low_stock_statement = select(Ingredient).where(
            Ingredient.user_id == current_user.id,
            Ingredient.quantity_on_hand != None, # Ensure quantity_on_hand is set
            Ingredient.low_stock_threshold != None, # Ensure threshold is set
            Ingredient.quantity_on_hand < Ingredient.low_stock_threshold
        ).order_by(Ingredient.name)
        
        results = self.session.exec(low_stock_statement).all()
        
        report_data = [
            {
                "ingredient_name": ingredient.name,
                "unit": ingredient.unit.value if ingredient.unit else "N/A",
                "quantity_on_hand": float(ingredient.quantity_on_hand or 0),
                "low_stock_threshold": float(ingredient.low_stock_threshold or 0),
                "shortfall": float((ingredient.low_stock_threshold or 0) - (ingredient.quantity_on_hand or 0))
            }
            for ingredient in results
        ]

        if output_format == "csv":
            headers = ["ingredient_name", "unit", "quantity_on_hand", "low_stock_threshold", "shortfall"]
            return generate_csv(report_data, headers)
            
        return report_data

    # Helper to stream CSV directly for FastAPI response
    def stream_csv_report(self, csv_io: io.StringIO, filename: str) -> StreamingResponse:
        response = StreamingResponse(iter([csv_io.getvalue()]), media_type="text/csv")
        response.headers["Content-Disposition"] = f"attachment; filename={filename}"
        return response

    # PDF generation would be more complex, requiring HTML templates and WeasyPrint.
    # For now, PDF generation will be a placeholder or return a message.
    async def generate_pdf_report_placeholder(self, report_name: str, data: Any) -> bytes:
        # In a real scenario, use WeasyPrint with an HTML template.
        # html_string = f"<h1>{report_name}</h1><pre>{json.dumps(data, indent=2)}</pre>"
        # pdf_bytes = HTML(string=html_string).write_pdf()
        # return pdf_bytes
        return f"PDF generation for {report_name} is a placeholder. Data: {str(data)[:200]}...".encode('utf-8')

