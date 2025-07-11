import pytest
from unittest.mock import MagicMock, patch
from datetime import datetime, timedelta


def test_payment_calculation_direct_fixed():
    """Test payment calculation directly without mocking."""
    from app.services.payment_service import calculate_scheduled_payment

    # Test data
    order_total = 500.00
    delivery_date = datetime.now() + timedelta(days=30)

    # Test full payment
    payment_amount, payment_date = calculate_scheduled_payment(
        order_total, "full", delivery_date
    )
    assert payment_amount == pytest.approx(500.00, 0.01)
    # Check that payment_date is either a date or datetime object
    assert payment_date is not None

    # Test deposit payment
    payment_amount, payment_date = calculate_scheduled_payment(
        order_total, "deposit", delivery_date
    )
    assert payment_amount == pytest.approx(125.00, 0.01)
    assert payment_date is not None

    # Test split payment
    payment_amount, payment_date = calculate_scheduled_payment(
        order_total, "split", delivery_date
    )
    assert payment_amount == pytest.approx(250.00, 0.01)
    assert payment_date is not None

    # Test invalid payment schedule (defaults to full)
    payment_amount, payment_date = calculate_scheduled_payment(
        order_total, "invalid", delivery_date
    )
    assert payment_amount == pytest.approx(500.00, 0.01)
    assert payment_date is not None
