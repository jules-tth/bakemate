import pytest
from unittest.mock import MagicMock, patch

def test_payment_calculation_direct():
    """Test payment calculation directly without mocking."""
    from app.services.payment_service import calculate_scheduled_payment
    from datetime import datetime, timedelta
    
    # Test data
    order_total = 500.00
    delivery_date = datetime.now() + timedelta(days=30)
    
    # Test full payment
    payment_amount, payment_date = calculate_scheduled_payment(
        order_total, "full", delivery_date
    )
    assert payment_amount == pytest.approx(500.00, 0.01)
    assert isinstance(payment_date, datetime.date)
    
    # Test deposit payment
    payment_amount, payment_date = calculate_scheduled_payment(
        order_total, "deposit", delivery_date
    )
    assert payment_amount == pytest.approx(125.00, 0.01)
    assert isinstance(payment_date, datetime.date)
    
    # Test split payment
    payment_amount, payment_date = calculate_scheduled_payment(
        order_total, "split", delivery_date
    )
    assert payment_amount == pytest.approx(250.00, 0.01)
    assert isinstance(payment_date, datetime.date)
    
    # Test invalid payment schedule (defaults to full)
    payment_amount, payment_date = calculate_scheduled_payment(
        order_total, "invalid", delivery_date
    )
    assert payment_amount == pytest.approx(500.00, 0.01)
    assert isinstance(payment_date, datetime.date)
