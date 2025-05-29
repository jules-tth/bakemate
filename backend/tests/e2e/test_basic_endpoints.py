import pytest
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_basic_endpoints():
    """Test basic endpoints return 200 status code."""
    # Test health endpoint
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
    
    # Test OpenAPI endpoint
    response = client.get("/api/v1/openapi.json")
    assert response.status_code == 200
    
    # Test docs endpoint
    response = client.get("/docs")
    assert response.status_code in (200, 301, 302, 307, 308)
