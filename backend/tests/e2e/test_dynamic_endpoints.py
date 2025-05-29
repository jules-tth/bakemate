import pytest
from fastapi.testclient import TestClient
import csv
import os
from main import app

client = TestClient(app)

def get_endpoints():
    """Read endpoints from CSV file."""
    endpoints = []
    csv_path = os.path.join(os.path.dirname(__file__), '../../../.dump/endpoints.csv')
    
    with open(csv_path, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            endpoints.append(row)
    
    return endpoints

def get_test_data_for_endpoint(method, path, requires_body):
    """Generate test data for the given endpoint."""
    # Extract path parameters
    path_params = {}
    for segment in path.split('/'):
        if segment.startswith('{') and segment.endswith('}'):
            param_name = segment[1:-1]
            # Use test IDs for different parameter types
            if 'id' in param_name:
                path_params[param_name] = '00000000-0000-0000-0000-000000000001'
            elif 'slug' in param_name:
                path_params[param_name] = 'test-slug'
            else:
                path_params[param_name] = 'test-value'
    
    # Generate request body if needed
    body = None
    if requires_body.lower() == 'true':
        # Basic request body based on endpoint path
        if 'recipes' in path:
            body = {
                "name": "Test Recipe",
                "description": "Test description",
                "ingredients": [{"id": "00000000-0000-0000-0000-000000000001", "quantity": 1, "unit": "cup"}],
                "instructions": "Test instructions"
            }
        elif 'ingredients' in path:
            body = {
                "name": "Test Ingredient",
                "description": "Test description",
                "unit_cost": 1.99,
                "stock_quantity": 10,
                "unit": "cup"
            }
        elif 'customers' in path:
            body = {
                "name": "Test Customer",
                "email": "test@example.com",
                "phone": "555-1234"
            }
        elif 'quotes' in path:
            body = {
                "customer_id": "00000000-0000-0000-0000-000000000001",
                "items": [{"recipe_id": "00000000-0000-0000-0000-000000000001", "quantity": 1}],
                "delivery_date": "2025-06-01"
            }
        elif 'orders' in path:
            body = {
                "customer_id": "00000000-0000-0000-0000-000000000001",
                "items": [{"recipe_id": "00000000-0000-0000-0000-000000000001", "quantity": 1}],
                "delivery_date": "2025-06-01"
            }
        elif 'calendar' in path:
            body = {
                "title": "Test Event",
                "start_time": "2025-06-01T09:00:00Z",
                "end_time": "2025-06-01T10:00:00Z",
                "description": "Test description"
            }
        elif 'tasks' in path:
            body = {
                "title": "Test Task",
                "description": "Test description",
                "due_date": "2025-06-01"
            }
        elif 'expenses' in path:
            body = {
                "description": "Test Expense",
                "amount": 19.99,
                "date": "2025-06-01"
            }
        elif 'mileage' in path:
            body = {
                "date": "2025-06-01",
                "miles": 10.5,
                "purpose": "Test purpose"
            }
        elif 'shop' in path:
            body = {
                "name": "Test Shop",
                "description": "Test description",
                "enabled": True
            }
        elif 'marketing' in path:
            body = {
                "name": "Test Campaign",
                "subject": "Test Subject",
                "content": "Test content",
                "segment": "all_customers"
            }
        else:
            # Generic body for other endpoints
            body = {
                "name": "Test Item",
                "description": "Test description"
            }
    
    return path_params, body

@pytest.mark.parametrize("endpoint", get_endpoints())
def test_endpoint(endpoint):
    """Test each endpoint from the CSV file."""
    method = endpoint['method']
    path = endpoint['path']
    requires_body = endpoint['requires_body']
    
    # Skip health endpoint as it's tested separately
    if path == '/health':
        pytest.skip("Health endpoint tested separately")
    
    # Get test data
    path_params, body = get_test_data_for_endpoint(method, path, requires_body)
    
    # Replace path parameters
    test_path = path
    for param_name, param_value in path_params.items():
        test_path = test_path.replace(f"{{{param_name}}}", param_value)
    
    # Make the request
    request_func = getattr(client, method.lower())
    
    try:
        if body:
            response = request_func(test_path, json=body)
        else:
            response = request_func(test_path)
        
        # Check for successful response or documented error
        # For simplicity, we'll accept 2xx, 3xx, 4xx as valid responses
        # In a real test, we'd check for specific status codes based on the API spec
        assert response.status_code < 500, f"Endpoint {method} {path} returned server error: {response.status_code}"
        
        # For successful responses, check that we got valid JSON
        if response.status_code < 400:
            try:
                response.json()
            except Exception as e:
                pytest.fail(f"Endpoint {method} {path} returned invalid JSON: {e}")
    
    except Exception as e:
        pytest.fail(f"Error testing endpoint {method} {path}: {e}")
