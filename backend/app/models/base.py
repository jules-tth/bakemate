from sqlmodel import SQLModel, Field
from typing import Optional
from datetime import datetime
import uuid

def generate_uuid():
    return uuid.uuid4()

class BaseUUIDModel(SQLModel):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True, index=True, nullable=False)
    created_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)
    updated_at: datetime = Field(default_factory=datetime.utcnow, nullable=False, sa_column_kwargs={"onupdate": datetime.utcnow})

class TenantBaseModel(BaseUUIDModel):
    # All models that are tenant-specific should inherit from this
    # The actual tenant_id field will be added to specific models that need it
    # For now, this serves as a marker and can be expanded later if common tenant fields arise
    pass

