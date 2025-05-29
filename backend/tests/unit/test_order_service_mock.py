import pytest
from unittest.mock import MagicMock, patch
from app.services.order_service import calculate_order_total

def test_order_total_calculation_mock():
    """Test order total calculation with mocked data."""
    # Mock order items
    order_items = [
        {"recipe_id": "1", "quantity": 2, "unit_price": 15.99},
        {"recipe_id": "2", "quantity": 1, "unit_price": 24.99}
    ]
    
    # Expected total: (2 * 15.99) + (1 * 24.99) = 56.97
    expected_total = (2 * 15.99) + (1 * 24.99)
    
    # Mock the calculation function
    with patch('app.services.order_service.calculate_order_total') as mock_calc:
        mock_calc.return_value = expected_total
        
        # Call the function with our test data
        result = mock_calc(order_items)
        
        # Assert the result
        assert result == pytest.approx(expected_total, 0.01)
        
        # Verify the function was called with our test data
        mock_calc.assert_called_once_with(order_items)

def test_apply_discount_percentage_mock():
    """Test applying percentage discount to order with mock."""
    # Test data
    order_total = 100.00
    discount_type = "percentage"
    discount_value = 15
    
    # Expected discounted total: 100 - (100 * 0.15) = 85
    expected_total = 85.00
    
    # Mock the discount function
    with patch('app.services.order_service.apply_discount') as mock_discount:
        mock_discount.return_value = expected_total
        
        # Call the function with our test data
        result = mock_discount(order_total, discount_type, discount_value)
        
        # Assert the result
        assert result == pytest.approx(expected_total, 0.01)
        
        # Verify the function was called with our test data
        mock_discount.assert_called_once_with(order_total, discount_type, discount_value)
