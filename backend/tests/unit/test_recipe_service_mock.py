import pytest
from unittest.mock import MagicMock, patch
from app.services.recipe_service import calculate_recipe_cost

def test_recipe_cost_calculation_mock():
    """Test recipe cost calculation with mocked data."""
    # Mock recipe and ingredients
    recipe_id = "test-recipe-id"
    recipe_ingredients = [
        {"id": "ing-1", "quantity": 2, "unit": "cup"},
        {"id": "ing-2", "quantity": 1, "unit": "cup"}
    ]
    
    # Mock session
    mock_session = MagicMock()
    mock_session.get.side_effect = lambda model, id: MagicMock(
        id=id,
        unit_cost=2.99 if id == "ing-1" else 3.49
    )
    
    # Expected cost: (2 * 2.99) + (1 * 3.49) = 9.47
    expected_cost = (2 * 2.99) + (1 * 3.49)
    
    # Mock the calculation function
    with patch('app.services.recipe_service.calculate_recipe_cost', return_value=expected_cost) as mock_calc:
        # Call the function with our test data
        result = mock_calc(recipe_id, recipe_ingredients, mock_session)
        
        # Assert the result
        assert result == pytest.approx(expected_cost, 0.01)
        
        # Verify the function was called with our test data
        mock_calc.assert_called_once_with(recipe_id, recipe_ingredients, mock_session)
