import pytest
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)


def test_api_v1_openapi_json():
    """Test the OpenAPI JSON endpoint returns 200 and valid schema."""
    response = client.get("/api/v1/openapi.json")
    assert response.status_code == 200
    # Verify it's valid JSON and has expected OpenAPI structure
    json_data = response.json()
    assert "openapi" in json_data
    assert "paths" in json_data
    assert "components" in json_data

    # Verify some key endpoints are present
    assert "/api/v1/recipes/" in json_data["paths"]
    assert "/api/v1/ingredients/" in json_data["paths"]
    assert "/api/v1/orders/" in json_data["paths"]
