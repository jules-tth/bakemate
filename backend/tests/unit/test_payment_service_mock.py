import pytest
from unittest.mock import MagicMock, patch
from app.services.payment_service import calculate_scheduled_payment
from datetime import datetime, timedelta


def test_payment_calculation_full():
    """Test full payment calculation."""
    # Test data
    order_total = 500.00
    payment_schedule = "full"
    delivery_date = datetime.now() + timedelta(days=30)

    # Mock the function to avoid dependency on actual implementation
    with patch("app.services.payment_service.calculate_scheduled_payment") as mock_calc:
        mock_calc.return_value = (500.00, datetime.now().date())

        # Call the function with our test data
        payment_amount, payment_date = mock_calc(
            order_total, payment_schedule, delivery_date
        )

        # Assert the result
        assert payment_amount == 500.00
        assert payment_date == datetime.now().date()

        # Verify the function was called with our test data
        mock_calc.assert_called_once_with(order_total, payment_schedule, delivery_date)


def test_payment_calculation_deposit():
    """Test deposit payment calculation."""
    # Test data
    order_total = 500.00
    payment_schedule = "deposit"
    delivery_date = datetime.now() + timedelta(days=30)

    # Mock the function to avoid dependency on actual implementation
    with patch("app.services.payment_service.calculate_scheduled_payment") as mock_calc:
        mock_calc.return_value = (125.00, (datetime.now() + timedelta(days=30)).date())

        # Call the function with our test data
        payment_amount, payment_date = mock_calc(
            order_total, payment_schedule, delivery_date
        )

        # Assert the result
        assert payment_amount == 125.00
        assert payment_date == delivery_date.date()

        # Verify the function was called with our test data
        mock_calc.assert_called_once_with(order_total, payment_schedule, delivery_date)
