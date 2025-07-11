from abc import ABC, abstractmethod
from typing import Generic, TypeVar, List, Optional, Any, Dict
from uuid import UUID
from sqlmodel import SQLModel

ModelType = TypeVar("ModelType", bound=SQLModel)
CreateSchemaType = TypeVar("CreateSchemaType", bound=SQLModel)
UpdateSchemaType = TypeVar("UpdateSchemaType", bound=SQLModel)


class IRepository(Generic[ModelType, CreateSchemaType, UpdateSchemaType], ABC):
    """Base interface for data access layer adapters."""

    @abstractmethod
    async def create(self, *, obj_in: CreateSchemaType, **kwargs) -> ModelType:
        pass

    @abstractmethod
    async def get(self, *, id: UUID, **kwargs) -> Optional[ModelType]:
        pass

    @abstractmethod
    async def get_multi(
        self,
        *,
        skip: int = 0,
        limit: int = 100,
        filters: Optional[Dict[str, Any]] = None,  # e.g. {"user_id": user.id}
        **kwargs
    ) -> List[ModelType]:
        pass

    @abstractmethod
    async def update(
        self, *, db_obj: ModelType, obj_in: UpdateSchemaType | Dict[str, Any], **kwargs
    ) -> ModelType:
        pass

    @abstractmethod
    async def delete(
        self, *, id: UUID, **kwargs
    ) -> Optional[ModelType]:  # Returns the deleted object or None
        pass

    @abstractmethod
    async def get_by_attribute(
        self, *, attribute_name: str, attribute_value: Any, **kwargs
    ) -> Optional[ModelType]:
        pass

    @abstractmethod
    async def get_multi_by_attribute(
        self,
        *,
        attribute_name: str,
        attribute_value: Any,
        skip: int = 0,
        limit: int = 100,
        **kwargs
    ) -> List[ModelType]:
        pass
