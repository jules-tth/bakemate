from typing import List, Optional, Any
from uuid import UUID
from datetime import datetime, timedelta

from sqlmodel import Session, select, delete

from app.models.order import Order, OrderCreate, OrderUpdate, OrderItem, OrderItemCreate, OrderStatus, PaymentStatus, Quote, QuoteCreate, QuoteUpdate, QuoteItem, QuoteItemCreate, QuoteStatus # Added Quote models
from app.models.user import User
from app.models.recipe import Recipe # For inventory deduction if linked
from app.models.ingredient import Ingredient # For inventory deduction
from app.repositories.sqlite_adapter import SQLiteRepository
from app.services.recipe_service import RecipeService # For fetching recipe details
# from app.services.ingredient_service import IngredientService # For inventory updates

class OrderService:
    def __init__(self, session: Session):
        self.order_repo = SQLiteRepository(model=Order) # type: ignore
        self.order_item_repo = SQLiteRepository(model=OrderItem) # type: ignore
        self.session = session
        # self.recipe_service = RecipeService(session) # If needed for deeper recipe logic
        # self.ingredient_service = IngredientService(session) # For inventory

    async def _generate_order_number(self, current_user: User) -> str:
        today_str = datetime.utcnow().strftime("%Y%m%d")
        user_prefix = str(current_user.id)[:4].upper()
        count_statement = select(Order).where(Order.user_id == current_user.id).where(Order.order_number.startswith(f"{today_str}-{user_prefix}"))
        orders_today = self.session.exec(count_statement).all()
        count = len(orders_today) + 1
        return f"{today_str}-{user_prefix}-{count:03d}"

    async def create_order(self, *, order_in: OrderCreate, current_user: User) -> Order:
        if order_in.user_id != current_user.id:
            pass 

        order_data = order_in.model_dump(exclude={"items"})
        order_data["order_number"] = await self._generate_order_number(current_user)
        
        db_order = Order(**order_data)
        db_order.user_id = current_user.id

        subtotal = 0.0
        for item_in in order_in.items:
            item_total = item_in.quantity * item_in.unit_price
            subtotal += item_total

        db_order.subtotal = round(subtotal, 2)
        db_order.tax = 0.0 
        db_order.total_amount = round(db_order.subtotal + db_order.tax, 2)
        
        if db_order.deposit_amount and db_order.deposit_amount > 0:
            db_order.balance_due = round(db_order.total_amount - db_order.deposit_amount, 2)
            db_order.payment_status = PaymentStatus.UNPAID 
        else:
            db_order.balance_due = db_order.total_amount

        self.session.add(db_order)
        self.session.commit()
        self.session.refresh(db_order)

        for item_in in order_in.items:
            item_data = item_in.model_dump()
            item_data["order_id"] = db_order.id
            item_data["total_price"] = item_in.quantity * item_in.unit_price
            db_item = OrderItem(**item_data)
            self.session.add(db_item)
        
        self.session.commit()
        self.session.refresh(db_order) 
        return db_order

    async def get_order_by_id(self, *, order_id: UUID, current_user: User) -> Optional[Order]:
        order = await self.order_repo.get(id=order_id)
        if not order or order.user_id != current_user.id:
            return None
        items_statement = select(OrderItem).where(OrderItem.order_id == order.id)
        order.items = self.session.exec(items_statement).all()
        return order

    async def get_orders_by_user(self, *, current_user: User, skip: int = 0, limit: int = 100, status: Optional[OrderStatus] = None) -> List[Order]:
        filters = {"user_id": current_user.id}
        if status:
            filters["status"] = status
        
        orders = await self.order_repo.get_multi(filters=filters, skip=skip, limit=limit)
        for order in orders:
            items_statement = select(OrderItem).where(OrderItem.order_id == order.id)
            order.items = self.session.exec(items_statement).all()
        return orders

    async def update_order(self, *, order_id: UUID, order_in: OrderUpdate, current_user: User) -> Optional[Order]:
        db_order = await self.order_repo.get(id=order_id)
        if not db_order or db_order.user_id != current_user.id:
            return None

        update_data = order_in.model_dump(exclude_unset=True, exclude={"items"})
        recalculate_totals = False

        for key, value in update_data.items():
            setattr(db_order, key, value)
            if key in ["deposit_amount"]:
                 recalculate_totals = True

        if order_in.items is not None:
            recalculate_totals = True
            delete_items_statement = delete(OrderItem).where(OrderItem.order_id == order_id)
            self.session.exec(delete_items_statement)

            new_subtotal = 0.0
            for item_in in order_in.items:
                item_data = item_in.model_dump()
                item_data["order_id"] = db_order.id
                item_data["total_price"] = item_in.quantity * item_in.unit_price
                new_subtotal += item_data["total_price"]
                db_item = OrderItem(**item_data)
                self.session.add(db_item)
            db_order.subtotal = round(new_subtotal, 2)
        
        if recalculate_totals or order_in.items is not None:
            db_order.tax = db_order.tax if order_in.tax is None else (order_in.tax or 0.0) 
            db_order.total_amount = round(db_order.subtotal + db_order.tax, 2)
            if db_order.deposit_amount and db_order.deposit_amount > 0:
                db_order.balance_due = round(db_order.total_amount - db_order.deposit_amount, 2)
            else:
                db_order.balance_due = db_order.total_amount

        if "status" in update_data and update_data["status"] == OrderStatus.CONFIRMED:
            await self._handle_order_confirmation(db_order)

        self.session.add(db_order)
        self.session.commit()
        self.session.refresh(db_order)
        items_statement = select(OrderItem).where(OrderItem.order_id == db_order.id)
        db_order.items = self.session.exec(items_statement).all()
        return db_order

    async def delete_order(self, *, order_id: UUID, current_user: User) -> Optional[Order]:
        db_order = await self.order_repo.get(id=order_id)
        if not db_order or db_order.user_id != current_user.id:
            return None
        
        delete_items_statement = delete(OrderItem).where(OrderItem.order_id == order_id)
        self.session.exec(delete_items_statement)

        deleted_order = await self.order_repo.delete(id=order_id)
        return deleted_order

    async def _handle_order_confirmation(self, order: Order):
        print(f"Order {order.order_number} confirmed. Placeholder for inventory deduction.")
        pass

    async def convert_quote_to_order(self, *, quote_id: UUID, current_user: User) -> Optional[Order]:
        quote_service = QuoteService(self.session)
        quote = await quote_service.get_quote_by_id(quote_id=quote_id, current_user=current_user)
        if not quote or quote.status != QuoteStatus.ACCEPTED:
            # Or if quote doesn_t exist / not owned / not in accepted state
            return None

        # Create OrderCreate schema from Quote data
        order_items_create = [
            OrderItemCreate(
                name=item.name,
                description=item.description,
                quantity=item.quantity,
                unit_price=item.unit_price
            ) for item in quote.items
        ]

        order_in = OrderCreate(
            user_id=current_user.id,
            # customer_id=quote.customer_id, # If customer_id is part of quote
            due_date=datetime.utcnow() + timedelta(days=7), # Example: due in 7 days, or from quote
            delivery_method="Pickup", # Example, or from quote
            notes_to_customer=quote.notes,
            items=order_items_create,
            status=OrderStatus.CONFIRMED # Or INQUIRY and then update
            # deposit_amount, etc. could also be copied if relevant
        )

        new_order = await self.create_order(order_in=order_in, current_user=current_user)
        
        # Mark Quote as converted
        quote.converted_to_order_id = new_order.id
        quote.status = QuoteStatus.EXPIRED # Or a new status like CONVERTED
        self.session.add(quote)
        self.session.commit()
        self.session.refresh(quote)
        return new_order

    async def create_stripe_payment_intent(self, order_id: UUID, current_user: User) -> Optional[str]:
        print(f"Placeholder: Creating Stripe Payment Intent for order {order_id}")
        return "pi_test_client_secret_placeholder"

    async def handle_stripe_webhook(self, payload: dict, signature: str) -> bool:
        print(f"Placeholder: Handling Stripe webhook. Event type: {payload.get('type')}")
        return True

    async def generate_invoice_pdf(self, order_id: UUID, current_user: User) -> Optional[bytes]:
        print(f"Placeholder: Generating PDF invoice for order {order_id}")
        return b"%PDF-1.4...placeholder PDF content..."

    async def get_client_portal_url(self, order_id: UUID, current_user: User) -> Optional[str]:
        print(f"Placeholder: Generating client portal URL for order {order_id}")
        return f"/portal/order/{order_id}?token=signed_jwt_placeholder"

class QuoteService:
    def __init__(self, session: Session):
        self.quote_repo = SQLiteRepository(model=Quote) # type: ignore
        self.quote_item_repo = SQLiteRepository(model=QuoteItem) # type: ignore
        self.session = session

    async def _generate_quote_number(self, current_user: User) -> str:
        today_str = datetime.utcnow().strftime("%Y%m%d")
        user_prefix = str(current_user.id)[:4].upper()
        count_statement = select(Quote).where(Quote.user_id == current_user.id).where(Quote.quote_number.startswith(f"Q-{today_str}-{user_prefix}"))
        quotes_today = self.session.exec(count_statement).all()
        count = len(quotes_today) + 1
        return f"Q-{today_str}-{user_prefix}-{count:03d}"

    async def create_quote(self, *, quote_in: QuoteCreate, current_user: User) -> Quote:
        if quote_in.user_id != current_user.id:
            pass

        quote_data = quote_in.model_dump(exclude={"items"})
        quote_data["quote_number"] = await self._generate_quote_number(current_user)
        
        db_quote = Quote(**quote_data)
        db_quote.user_id = current_user.id

        subtotal = 0.0
        for item_in in quote_in.items:
            item_total = item_in.quantity * item_in.unit_price
            subtotal += item_total

        db_quote.subtotal = round(subtotal, 2)
        db_quote.tax = 0.0  # Placeholder for tax logic
        db_quote.total_amount = round(db_quote.subtotal + db_quote.tax, 2)

        self.session.add(db_quote)
        self.session.commit()
        self.session.refresh(db_quote)

        for item_in in quote_in.items:
            item_data = item_in.model_dump()
            item_data["quote_id"] = db_quote.id
            item_data["total_price"] = item_in.quantity * item_in.unit_price
            db_item = QuoteItem(**item_data)
            self.session.add(db_item)
        
        self.session.commit()
        self.session.refresh(db_quote)
        return db_quote

    async def get_quote_by_id(self, *, quote_id: UUID, current_user: User) -> Optional[Quote]:
        quote = await self.quote_repo.get(id=quote_id)
        if not quote or quote.user_id != current_user.id:
            return None
        items_statement = select(QuoteItem).where(QuoteItem.quote_id == quote.id)
        quote.items = self.session.exec(items_statement).all()
        return quote

    async def get_quotes_by_user(self, *, current_user: User, skip: int = 0, limit: int = 100, status: Optional[QuoteStatus] = None) -> List[Quote]:
        filters = {"user_id": current_user.id}
        if status:
            filters["status"] = status
        
        quotes = await self.quote_repo.get_multi(filters=filters, skip=skip, limit=limit)
        for quote in quotes:
            items_statement = select(QuoteItem).where(QuoteItem.quote_id == quote.id)
            quote.items = self.session.exec(items_statement).all()
        return quotes

    async def update_quote(self, *, quote_id: UUID, quote_in: QuoteUpdate, current_user: User) -> Optional[Quote]:
        db_quote = await self.quote_repo.get(id=quote_id)
        if not db_quote or db_quote.user_id != current_user.id:
            return None

        update_data = quote_in.model_dump(exclude_unset=True, exclude={"items"})
        recalculate_totals = False

        for key, value in update_data.items():
            setattr(db_quote, key, value)

        if quote_in.items is not None:
            recalculate_totals = True
            delete_items_statement = delete(QuoteItem).where(QuoteItem.quote_id == quote_id)
            self.session.exec(delete_items_statement)

            new_subtotal = 0.0
            for item_in in quote_in.items:
                item_data = item_in.model_dump()
                item_data["quote_id"] = db_quote.id
                item_data["total_price"] = item_in.quantity * item_in.unit_price
                new_subtotal += item_data["total_price"]
                db_item = QuoteItem(**item_data)
                self.session.add(db_item)
            db_quote.subtotal = round(new_subtotal, 2)
        
        if recalculate_totals or quote_in.items is not None:
            db_quote.tax = db_quote.tax if quote_in.tax is None else (quote_in.tax or 0.0)
            db_quote.total_amount = round(db_quote.subtotal + db_quote.tax, 2)

        self.session.add(db_quote)
        self.session.commit()
        self.session.refresh(db_quote)
        items_statement = select(QuoteItem).where(QuoteItem.quote_id == db_quote.id)
        db_quote.items = self.session.exec(items_statement).all()
        return db_quote

    async def delete_quote(self, *, quote_id: UUID, current_user: User) -> Optional[Quote]:
        db_quote = await self.quote_repo.get(id=quote_id)
        if not db_quote or db_quote.user_id != current_user.id:
            return None
        
        delete_items_statement = delete(QuoteItem).where(QuoteItem.quote_id == quote_id)
        self.session.exec(delete_items_statement)

        deleted_quote = await self.quote_repo.delete(id=quote_id)
        return deleted_quote

