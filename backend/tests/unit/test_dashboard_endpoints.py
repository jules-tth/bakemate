from datetime import datetime, timezone
import asyncio

from fastapi.testclient import TestClient
from sqlmodel import Session, delete, select

from app.models.order import Order, OrderStatus, PaymentStatus
from app.models.ingredient import Ingredient
from app.models.user import User
from app.repositories.sqlite_adapter import engine
from main import app, create_db_and_tables
from seed import seed_data

client = TestClient(app)


def _auth_headers() -> dict:
    resp = client.post(
        "/api/v1/auth/login/access-token",
        data={"username": "test@example.com", "password": "password"},
    )
    token = resp.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def _seed_data() -> None:
    create_db_and_tables()
    asyncio.run(seed_data())
    with Session(engine) as session:
        user = session.exec(select(User).where(User.email == "test@example.com")).one()
        session.exec(delete(Order))
        session.exec(delete(Ingredient))
        order1 = Order(
            user_id=user.id,
            order_number="ORD1",
            status=OrderStatus.COMPLETED,
            payment_status=PaymentStatus.PAID_IN_FULL,
            order_date=datetime(2024, 1, 15, tzinfo=timezone.utc),
            due_date=datetime(2024, 1, 20, tzinfo=timezone.utc),
            subtotal=100,
            tax=0,
            total_amount=100,
        )
        order2 = Order(
            user_id=user.id,
            order_number="ORD2",
            status=OrderStatus.COMPLETED,
            payment_status=PaymentStatus.PAID_IN_FULL,
            order_date=datetime(2024, 2, 10, tzinfo=timezone.utc),
            due_date=datetime(2024, 2, 15, tzinfo=timezone.utc),
            subtotal=150,
            tax=0,
            total_amount=150,
        )
        ingredient = Ingredient(
            name="Flour",
            unit="kg",
            cost=1.0,
            quantity_on_hand=1,
            low_stock_threshold=5,
            user_id=user.id,
        )
        session.add_all([order1, order2, ingredient])
        session.commit()


def test_dashboard_endpoints_return_data():
    _seed_data()
    headers = _auth_headers()

    resp = client.get(
        "/api/v1/dashboard/summary", params={"range": "2024"}, headers=headers
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["revenue"] == 250.0
    assert data["total_orders"] == 2
    assert data["ingredients_low"] == 1

    resp = client.get(
        "/api/v1/dashboard/orders", params={"range": "2024"}, headers=headers
    )
    assert resp.status_code == 200
    orders = resp.json()
    assert orders[0]["date"] == "Jan"
    assert orders[0]["count"] == 1

    resp = client.get(
        "/api/v1/dashboard/revenue", params={"range": "2024"}, headers=headers
    )
    assert resp.status_code == 200
    revenue = resp.json()
    assert revenue[0]["date"] == "Jan"
    assert revenue[0]["revenue"] == 100.0
