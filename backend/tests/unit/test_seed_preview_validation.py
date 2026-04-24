import asyncio

from sqlalchemy.pool import StaticPool
from sqlmodel import Session, SQLModel, create_engine, select

from app.models.order import Order
from app.models.recipe import Recipe
from app.models.user import User
from seed import (
    PREVIEW_VALIDATION_ORDER_NUMBER,
    PREVIEW_VALIDATION_USER_EMAIL,
    ensure_preview_validation_order,
    ensure_seed_recipes,
    ensure_seed_user,
)


def test_seed_helpers_create_repeatable_preview_validation_fixture():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(engine)

    with Session(engine) as session:
        user = asyncio.run(ensure_seed_user(session))
        ensure_seed_recipes(session, user=user)
        order = ensure_preview_validation_order(session, user=user)

        same_user = asyncio.run(ensure_seed_user(session))
        ensure_seed_recipes(session, user=same_user)
        same_order = ensure_preview_validation_order(session, user=same_user)

        users = session.exec(select(User)).all()
        recipes = session.exec(select(Recipe)).all()
        orders = session.exec(select(Order)).all()

        assert user.id == same_user.id
        assert order.id == same_order.id
        assert [user.email for user in users] == [PREVIEW_VALIDATION_USER_EMAIL]
        assert len(recipes) == 3
        assert len(orders) == 1
        assert orders[0].order_number == PREVIEW_VALIDATION_ORDER_NUMBER
        assert orders[0].items[0].name == "Preview Validation Cake"
