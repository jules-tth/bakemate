import pytest
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)


def test_health_endpoint():
    """Test the health endpoint returns 200 and correct status."""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_openapi_endpoint():
    """Test the OpenAPI endpoint returns 200 and valid schema."""
    response = client.get("/api/v1/openapi.json")
    assert response.status_code == 200
    # Verify it's valid JSON and has expected OpenAPI structure
    json_data = response.json()
    assert "openapi" in json_data
    assert "paths" in json_data
    assert "components" in json_data
