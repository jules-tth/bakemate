#!/usr/bin/env python3
"""
Payment service for BakeMate backend.
Handles payment calculations and scheduling.
"""

from datetime import datetime, timedelta


def calculate_scheduled_payment(order_total, payment_schedule, delivery_date):
    """
    Calculate payment amount and date based on payment schedule.

    Args:
        order_total: Total order amount
        payment_schedule: Payment schedule type ('full', 'deposit', 'split')
        delivery_date: Date of delivery

    Returns:
        tuple: (payment_amount, payment_date)
    """
    today = datetime.now().date()

    if payment_schedule == "full":
        # Full payment due now
        return order_total, today
    elif payment_schedule == "deposit":
        # 25% deposit now, 75% on delivery
        deposit_amount = order_total * 0.25
        return deposit_amount, delivery_date
    elif payment_schedule == "split":
        # 50% now, 50% on delivery
        split_amount = order_total * 0.5
        return split_amount, delivery_date
    else:
        # Default to full payment
        return order_total, today
