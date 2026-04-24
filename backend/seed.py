import asyncio
from datetime import date, datetime, timezone

from sqlmodel import Session
from sqlmodel import select

from app.models.order import Order, OrderItem, OrderStatus, PaymentStatus
from app.models.user import User, UserCreate
from app.models.recipe import Recipe, RecipeCreate
from app.services.user_service import UserService
from app.repositories.sqlite_adapter import engine

PREVIEW_VALIDATION_ORDER_NUMBER = "ORD-PREVIEW-VALIDATION"
PREVIEW_VALIDATION_USER_EMAIL = "test@example.com"
PREVIEW_VALIDATION_PASSWORD = "password"


async def ensure_seed_user(
    session: Session,
    *,
    email: str = PREVIEW_VALIDATION_USER_EMAIL,
    password: str = PREVIEW_VALIDATION_PASSWORD,
) -> User:
    user_service = UserService(session)
    user = await user_service.get_user_by_email(email)
    if user:
        return user
    return await user_service.create_user(UserCreate(email=email, password=password))


def ensure_seed_recipes(session: Session, *, user: User) -> None:
    existing_recipe = session.exec(
        select(Recipe).where(Recipe.user_id == user.id)
    ).first()
    if existing_recipe:
        return

    recipes_data = [
        {
            "name": "Classic Chocolate Chip Cookies",
            "description": "The best chocolate chip cookies ever!",
            "user_id": user.id,
            "instructions": "1. Preheat oven. 2. Mix dough. 3. Bake until edges are browned.",
        },
        {
            "name": "Sourdough Bread",
            "description": "A crusty, chewy sourdough bread.",
            "user_id": user.id,
            "instructions": "1. Feed starter. 2. Mix dough. 3. Ferment, shape, and bake.",
        },
        {
            "name": "New York-Style Pizza",
            "description": "A classic New York-style pizza with a thin, crisp crust.",
            "user_id": user.id,
            "instructions": "1. Make dough. 2. Make sauce. 3. Assemble and bake.",
        },
    ]

    for recipe_data in recipes_data:
        recipe_in = RecipeCreate(**recipe_data)
        session.add(Recipe(**recipe_in.model_dump(by_alias=False)))
    session.commit()


def ensure_preview_validation_order(session: Session, *, user: User) -> Order:
    existing_order = session.exec(
        select(Order).where(
            Order.user_id == user.id,
            Order.order_number == PREVIEW_VALIDATION_ORDER_NUMBER,
        )
    ).first()
    if existing_order:
        return existing_order

    order = Order(
        user_id=user.id,
        order_number=PREVIEW_VALIDATION_ORDER_NUMBER,
        customer_name="Preview Validation Customer",
        customer_email="preview-validation@example.com",
        customer_phone="555-0195",
        status=OrderStatus.CONFIRMED,
        payment_status=PaymentStatus.UNPAID,
        order_date=datetime(2026, 4, 21, 12, 0, tzinfo=timezone.utc),
        due_date=datetime(2026, 4, 22, 14, 0, tzinfo=timezone.utc),
        delivery_method="Pickup",
        subtotal=96.0,
        tax=0.0,
        total_amount=96.0,
        deposit_amount=48.0,
        balance_due=96.0,
        deposit_due_date=date(2026, 4, 21),
        balance_due_date=date(2026, 4, 22),
        internal_notes="Repeatable BM-095 local browser validation fixture.",
    )
    order.items = [
        OrderItem(
            name="Preview Validation Cake",
            description="Repeatable local validation order",
            quantity=1,
            unit_price=96.0,
            total_price=96.0,
        )
    ]
    session.add(order)
    session.commit()
    session.refresh(order)
    return order


async def seed_data():
    with Session(engine) as session:
        user = await ensure_seed_user(session)
        ensure_seed_recipes(session, user=user)
        validation_order = ensure_preview_validation_order(session, user=user)
        print(
            "Database seed ensured with preview validation user, recipes, "
            f"and order {validation_order.order_number}."
        )
