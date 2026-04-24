from typing import Any, Dict, Generic, List, Optional, Type, TypeVar, Union
from uuid import UUID

from fastapi.encoders import jsonable_encoder
from pydantic import BaseModel
from sqlalchemy import inspect, text
from sqlmodel import SQLModel, Session, create_engine, select

from app.core.config import (
    settings,
)  # Assuming settings.DATABASE_URL will be configured
from app.repositories.base import IRepository

ModelType = TypeVar("ModelType", bound=SQLModel)
CreateSchemaType = TypeVar("CreateSchemaType", bound=BaseModel)
UpdateSchemaType = TypeVar("UpdateSchemaType", bound=BaseModel)

# For SQLite, the engine is created once
# The project scope specifies `bakemate_dev.db`
# DATABASE_URL = "sqlite:///./bakemate_dev.db"
# engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False}) # check_same_thread for SQLite
engine = create_engine(
    settings.DATABASE_URL,
    connect_args=(
        {"check_same_thread": False} if "sqlite" in settings.DATABASE_URL else {}
    ),
)

_schema_ensured = False


def ensure_sqlite_order_schema(target_engine=None) -> None:
    global _schema_ensured

    engine_to_use = target_engine or engine
    if "sqlite" not in str(engine_to_use.url):
        _schema_ensured = True
        return
    if target_engine is None and _schema_ensured:
        return

    inspector = inspect(engine_to_use)
    if "order" not in inspector.get_table_names():
        if target_engine is None:
            _schema_ensured = True
        return

    existing_columns = {column["name"] for column in inspector.get_columns("order")}
    required_columns = {
        "user_id": "VARCHAR",
        "customer_contact_id": "VARCHAR",
        "customer_name": "VARCHAR",
        "customer_email": "VARCHAR",
        "customer_phone": "VARCHAR",
        "status": "VARCHAR",
        "payment_status": "VARCHAR",
        "order_date": "DATETIME",
        "delivery_method": "VARCHAR",
        "subtotal": "FLOAT",
        "tax": "FLOAT",
        "total_amount": "FLOAT",
        "deposit_amount": "FLOAT",
        "balance_due": "FLOAT",
        "deposit_due_date": "TEXT",
        "balance_due_date": "TEXT",
        "notes_to_customer": "VARCHAR",
        "internal_notes": "VARCHAR",
        "stripe_payment_intent_id": "VARCHAR",
        "stripe_checkout_session_id": "VARCHAR",
    }

    with engine_to_use.begin() as connection:
        for column_name, column_type in required_columns.items():
            if column_name not in existing_columns:
                connection.execute(
                    text(f'ALTER TABLE "order" ADD COLUMN {column_name} {column_type}')
                )

    if target_engine is None:
        _schema_ensured = True


def get_session():
    ensure_sqlite_order_schema()
    with Session(engine) as session:
        yield session


class SQLiteRepository(
    IRepository[ModelType, CreateSchemaType, UpdateSchemaType],
    Generic[ModelType, CreateSchemaType, UpdateSchemaType],
):
    def __init__(self, model: Type[ModelType]):
        """
        CRUD object with default methods to Create, Read, Update, Delete (CRUD).

        **Parameters**

        * `model`: A SQLModel class
        """
        self.model = model
        # self.engine is global for SQLite in this example
        self.engine = engine

    def _get_session(self) -> Session:
        # In a real FastAPI app, you would inject the session using Depends
        # For this structure, we create a new session per operation or manage it externally.
        return Session(self.engine)

    async def create(self, *, obj_in: CreateSchemaType, **kwargs) -> ModelType:
        obj_in_data = jsonable_encoder(obj_in)
        db_obj = self.model(**obj_in_data)
        with self._get_session() as session:
            session.add(db_obj)
            session.commit()
            session.refresh(db_obj)
            return db_obj

    async def get(self, *, id: UUID, **kwargs) -> Optional[ModelType]:
        with self._get_session() as session:
            statement = select(self.model).where(self.model.id == id)
            obj = session.exec(statement).first()
            return obj

    async def get_multi(
        self,
        *,
        skip: int = 0,
        limit: Optional[int] = 100,
        filters: Optional[Dict[str, Any]] = None,
        sort_by: Optional[str] = None,
        sort_desc: bool = False,
        **kwargs,
    ) -> List[ModelType]:
        with self._get_session() as session:
            statement = select(self.model)
            if filters:
                for key, value in filters.items():
                    if "__" in key:
                        attr, op = key.split("__", 1)
                        column = getattr(self.model, attr, None)
                        if not column:
                            continue
                        if op == "gte":
                            statement = statement.where(column >= value)
                        elif op == "lte":
                            statement = statement.where(column <= value)
                        elif op == "gt":
                            statement = statement.where(column > value)
                        elif op == "lt":
                            statement = statement.where(column < value)
                    elif hasattr(self.model, key):
                        statement = statement.where(getattr(self.model, key) == value)
            if sort_by and hasattr(self.model, sort_by):
                column = getattr(self.model, sort_by)
                statement = statement.order_by(
                    column.desc() if sort_desc else column.asc()
                )
            statement = statement.offset(skip)
            if limit is not None:
                statement = statement.limit(limit)
            objs = session.exec(statement).all()
            return objs

    async def update(
        self,
        *,
        db_obj: ModelType,
        obj_in: Union[UpdateSchemaType, Dict[str, Any]],
        **kwargs,
    ) -> ModelType:
        obj_data = jsonable_encoder(db_obj)
        if isinstance(obj_in, dict):
            update_data = obj_in
        else:
            update_data = obj_in.model_dump(exclude_unset=True)  # Pydantic V2
            # update_data = obj_in.dict(exclude_unset=True) # Pydantic V1
        for field in obj_data:
            if field in update_data:
                setattr(db_obj, field, update_data[field])
        with self._get_session() as session:
            session.add(db_obj)
            session.commit()
            session.refresh(db_obj)
            return db_obj

    async def delete(self, *, id: UUID, **kwargs) -> Optional[ModelType]:
        with self._get_session() as session:
            statement = select(self.model).where(self.model.id == id)
            obj = session.exec(statement).first()
            if obj:
                session.delete(obj)
                session.commit()
                return obj
            return None

    async def get_by_attribute(
        self, *, attribute_name: str, attribute_value: Any, **kwargs
    ) -> Optional[ModelType]:
        with self._get_session() as session:
            if not hasattr(self.model, attribute_name):
                # Or raise an error, or return None, depending on desired behavior
                return None
            statement = select(self.model).where(
                getattr(self.model, attribute_name) == attribute_value
            )
            obj = session.exec(statement).first()
            return obj

    async def get_multi_by_attribute(
        self,
        *,
        attribute_name: str,
        attribute_value: Any,
        skip: int = 0,
        limit: int = 100,
        **kwargs,
    ) -> List[ModelType]:
        with self._get_session() as session:
            if not hasattr(self.model, attribute_name):
                return []
            statement = select(self.model).where(
                getattr(self.model, attribute_name) == attribute_value
            )
            statement = statement.offset(skip).limit(limit)
            objs = session.exec(statement).all()
            return objs


# Example of how to create the tables (usually in main.py or a db setup script)
# def create_db_and_tables():
#     SQLModel.metadata.create_all(engine)
