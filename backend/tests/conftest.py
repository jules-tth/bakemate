import pytest
from httpx import AsyncClient
import asyncio

@pytest.fixture
async def async_client():
    """Create an async client for testing."""
    from main import app
    async with AsyncClient(app=app, base_url="http://test") as client:
        yield client

@pytest.fixture
def db_rollback():
    """Fixture to rollback database changes after tests."""
    # This would normally use a transaction that gets rolled back
    # For simplicity, we're just creating a placeholder
    yield
    # Rollback would happen here in a real implementation
