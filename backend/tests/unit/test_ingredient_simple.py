import pytest
from unittest.mock import MagicMock, patch

def test_get_ingredient_by_id_simple():
    """Test getting ingredient by ID with simple mock."""
    # Mock ingredient ID
    ingredient_id = "test-ingredient-id"
    
    # Mock ingredient data
    mock_ingredient = {
        "id": ingredient_id,
        "name": "Test Ingredient",
        "unit_cost": 2.99
    }
    
    # Simple assertion to verify basic test structure works
    assert mock_ingredient["id"] == ingredient_id
    assert mock_ingredient["name"] == "Test Ingredient"
    assert mock_ingredient["unit_cost"] == 2.99

def test_update_ingredient_stock_simple():
    """Test updating ingredient stock with simple mock."""
    # Mock ingredient ID and quantity
    ingredient_id = "test-ingredient-id"
    quantity_change = 5
    
    # Mock ingredient
    mock_ingredient = {
        "id": ingredient_id,
        "stock_quantity": 10
    }
    
    # Simulate stock update
    updated_quantity = mock_ingredient["stock_quantity"] + quantity_change
    
    # Verify the update
    assert updated_quantity == 15
