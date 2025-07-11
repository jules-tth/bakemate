import pytest
from app.services.payment_service import calculate_scheduled_payment
from datetime import datetime, timedelta


def test_payment_calculation_full():
    """Test full payment calculation."""
    # Test data
    order_total = 500.00
    payment_schedule = "full"
    delivery_date = datetime.now() + timedelta(days=30)

    # Calculate payment
    payment_amount, payment_date = calculate_scheduled_payment(
        order_total, payment_schedule, delivery_date
    )

    # For full payment, expect 100% now
    assert payment_amount == pytest.approx(500.00, 0.01)
    assert payment_date == datetime.now().date()


def test_payment_calculation_deposit():
    """Test deposit payment calculation."""
    # Test data
    order_total = 500.00
    payment_schedule = "deposit"
    delivery_date = datetime.now() + timedelta(days=30)

    # Calculate payment
    payment_amount, payment_date = calculate_scheduled_payment(
        order_total, payment_schedule, delivery_date
    )

    # For deposit, expect 25% now, 75% on delivery
    assert payment_amount == pytest.approx(125.00, 0.01)
    assert payment_date == delivery_date


def test_payment_calculation_split():
    """Test split payment calculation."""
    # Test data
    order_total = 500.00
    payment_schedule = "split"
    delivery_date = datetime.now() + timedelta(days=30)

    # Calculate payment
    payment_amount, payment_date = calculate_scheduled_payment(
        order_total, payment_schedule, delivery_date
    )

    # For split payment, expect 50% now, 50% on delivery
    assert payment_amount == pytest.approx(250.00, 0.01)
    assert payment_date == delivery_date


def test_payment_calculation_invalid():
    """Test invalid payment schedule defaults to full payment."""
    # Test data
    order_total = 500.00
    payment_schedule = "invalid"
    delivery_date = datetime.now() + timedelta(days=30)

    # Calculate payment
    payment_amount, payment_date = calculate_scheduled_payment(
        order_total, payment_schedule, delivery_date
    )

    # For invalid schedule, expect default to full payment
    assert payment_amount == pytest.approx(500.00, 0.01)
    assert payment_date == datetime.now().date()
