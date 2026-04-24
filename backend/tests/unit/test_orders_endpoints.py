import asyncio
from datetime import datetime, timezone

from fastapi.testclient import TestClient
from sqlmodel import Session, delete, select

from app.models.order import Order, OrderStatus, PaymentStatus
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


def _seed_orders() -> None:
    create_db_and_tables()
    asyncio.run(seed_data())
    with Session(engine) as session:
        user = session.exec(select(User).where(User.email == "test@example.com")).one()
        session.exec(delete(Order))
        open_order = Order(
            user_id=user.id,
            order_number="OPEN1",
            status=OrderStatus.CONFIRMED,
            payment_status=PaymentStatus.UNPAID,
            order_date=datetime(2025, 9, 15, tzinfo=timezone.utc),
            due_date=datetime(2025, 9, 20, tzinfo=timezone.utc),
            subtotal=50,
            tax=0,
            total_amount=50,
        )
        closed_order = Order(
            user_id=user.id,
            order_number="CLOSED1",
            status=OrderStatus.COMPLETED,
            payment_status=PaymentStatus.PAID_IN_FULL,
            order_date=datetime(2025, 9, 10, tzinfo=timezone.utc),
            due_date=datetime(2025, 9, 12, tzinfo=timezone.utc),
            subtotal=100,
            tax=0,
            total_amount=100,
        )
        session.add_all([open_order, closed_order])
        session.commit()


def test_orders_summary_open_status():
    _seed_orders()
    headers = _auth_headers()

    resp = client.get(
        "/api/v1/orders/",
        params={"status": "Open"},
        headers=headers,
    )
    assert resp.status_code == 200
    orders = resp.json()
    assert len(orders) == 1
    assert orders[0]["order_number"] == "OPEN1"

    resp = client.get(
        "/api/v1/orders/summary",
        params={
            "start": "2025-09-01",
            "end": "2025-09-30",
            "status": "Open",
        },
        headers=headers,
    )
    assert resp.status_code == 200
    summary = resp.json()
    assert summary["count"] == 1
