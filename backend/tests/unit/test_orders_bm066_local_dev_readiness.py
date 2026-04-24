import asyncio
from uuid import uuid4

import pytest
from sqlalchemy.exc import OperationalError
from sqlmodel import Session, SQLModel, create_engine

from app.api.v1.endpoints.orders import read_day_running_queue_summary, read_orders
from app.models.order import DayRunningQueueSummary
from app.models.user import User
from app.services.order_service import OrderService
from fastapi import HTTPException


@pytest.fixture
def session_and_user():
    engine = create_engine("sqlite://")
    SQLModel.metadata.create_all(engine)

    with Session(engine) as session:
        current_user = User(
            id=uuid4(),
            email="bm066@example.com",
            hashed_password="not-used",
            is_active=True,
            is_superuser=False,
        )
        session.add(current_user)
        session.commit()
        yield session, current_user


@pytest.mark.parametrize(
    ("endpoint", "method_name"),
    [
        (read_orders, "get_orders_by_user"),
        (read_day_running_queue_summary, "get_day_running_queue_summary"),
    ],
)
def test_ops_endpoints_surface_local_dev_readiness_for_stale_schema(
    monkeypatch, session_and_user, endpoint, method_name
):
    session, current_user = session_and_user

    async def raise_stale_schema(*args, **kwargs):
        raise OperationalError(
            'SELECT "order".customer_name FROM "order"',
            {},
            Exception("no such column: order.customer_name"),
        )

    monkeypatch.setattr(OrderService, method_name, raise_stale_schema)

    with pytest.raises(HTTPException) as exc_info:
        asyncio.run(endpoint(session=session, current_user=current_user))

    exc = exc_info.value
    assert exc.status_code == 503
    assert exc.detail["code"] == "local_dev_schema_stale"
    assert exc.detail["title"] == "Local dev setup needs refresh"
    assert "local BakeMate setup issue" in exc.detail["note"]
    assert "schema refresh" in exc.detail["message"]
    assert exc.detail["guidance_title"] == "How to recover locally"
    assert exc.detail["guidance_source"] == "README.md and docs/developer_guide.md"
    assert exc.detail["recovery_command_label"] == "Run locally from the BakeMate repo"
    assert exc.detail["recovery_command"] == "docker compose up --build -d"
    assert len(exc.detail["guidance_steps"]) == 3
    assert "README.md or docs/developer_guide.md" in exc.detail["guidance_steps"][0]


def test_ops_endpoints_keep_healthy_behavior_when_data_is_available(monkeypatch, session_and_user):
    session, current_user = session_and_user

    expected_orders = ["healthy-order"]
    expected_summary = DayRunningQueueSummary(
        all_count=4,
        blocked_count=1,
        needs_attention_count=2,
        ready_count=1,
    )

    async def return_orders(*args, **kwargs):
        return expected_orders

    async def return_summary(*args, **kwargs):
        return expected_summary

    monkeypatch.setattr(OrderService, "get_orders_by_user", return_orders)
    monkeypatch.setattr(OrderService, "get_day_running_queue_summary", return_summary)

    orders_payload = asyncio.run(read_orders(session=session, current_user=current_user))
    summary_payload = asyncio.run(
        read_day_running_queue_summary(session=session, current_user=current_user)
    )

    assert orders_payload == expected_orders
    assert summary_payload == expected_summary
    assert not hasattr(orders_payload, "detail")
    assert not hasattr(summary_payload, "detail")
