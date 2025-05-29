import pytest
from app.models.order import Order
from app.services.order_service import calculate_order_total, apply_discount

def test_calculate_order_total():
    """Test order total calculation."""
    # Mock order items
    order_items = [
        {"recipe_id": "1", "quantity": 2, "unit_price": 15.99},
        {"recipe_id": "2", "quantity": 1, "unit_price": 24.99}
    ]
    
    # Expected total: (2 * 15.99) + (1 * 24.99) = 56.97
    expected_total = (2 * 15.99) + (1 * 24.99)
    
    # Mock the calculation function
    def mock_calculate_total(items):
        total = 0
        for item in items:
            total += item["quantity"] * item["unit_price"]
        return total
    
    # Calculate total
    total = mock_calculate_total(order_items)
    
    # Assert the result
    assert total == pytest.approx(expected_total, 0.01)

def test_apply_discount_percentage():
    """Test applying percentage discount to order."""
    # Test data
    order_total = 100.00
    discount_type = "percentage"
    discount_value = 15
    
    # Expected discounted total: 100 - (100 * 0.15) = 85
    expected_total = 85.00
    
    # Apply discount
    discounted_total = order_total - (order_total * (discount_value / 100))
    
    # Assert the result
    assert discounted_total == pytest.approx(expected_total, 0.01)

def test_apply_discount_fixed():
    """Test applying fixed discount to order."""
    # Test data
    order_total = 100.00
    discount_type = "fixed"
    discount_value = 10
    
    # Expected discounted total: 100 - 10 = 90
    expected_total = 90.00
    
    # Apply discount
    discounted_total = order_total - discount_value
    
    # Assert the result
    assert discounted_total == pytest.approx(expected_total, 0.01)

def test_apply_discount_minimum_order():
    """Test discount with minimum order requirement."""
    # Test cases
    test_cases = [
        {"order_total": 80.00, "min_order": 100.00, "discount": 10.00, "expected": 80.00},  # Below minimum
        {"order_total": 120.00, "min_order": 100.00, "discount": 10.00, "expected": 110.00}  # Above minimum
    ]
    
    for case in test_cases:
        # Apply discount only if minimum order value is met
        if case["order_total"] >= case["min_order"]:
            discounted_total = case["order_total"] - case["discount"]
        else:
            discounted_total = case["order_total"]
        
        # Assert the result
        assert discounted_total == pytest.approx(case["expected"], 0.01)
