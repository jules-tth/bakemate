from sqlalchemy import create_engine, inspect, text

from app.repositories.sqlite_adapter import ensure_sqlite_order_schema


def test_ensure_sqlite_order_schema_adds_bm006_columns():
    engine = create_engine("sqlite://")

    with engine.begin() as connection:
        connection.execute(
            text(
                'CREATE TABLE "order" (id VARCHAR PRIMARY KEY, order_number VARCHAR, due_date VARCHAR)'
            )
        )

    ensure_sqlite_order_schema(engine)

    columns = {column["name"] for column in inspect(engine).get_columns("order")}
    assert "deposit_due_date" in columns
    assert "balance_due_date" in columns
    assert "stripe_checkout_session_id" in columns
