"""
Order service module for BakeMate backend.
This module imports and exposes the core order processing functions.
"""

# Import all functions from the order_service_functions module
from app.services.order_service_functions import (
    calculate_order_total,
    apply_discount,
    get_order_by_id,
    calculate_order_tax,
    calculate_delivery_fee,
    validate_order_data,
    get_order_items,
    cancel_order,
    get_orders_by_date_range,
    create_order,
    update_order_status
)

# Re-export all functions to maintain the expected API
__all__ = [
    'calculate_order_total',
    'apply_discount',
    'get_order_by_id',
    'calculate_order_tax',
    'calculate_delivery_fee',
    'validate_order_data',
    'get_order_items',
    'cancel_order',
    'get_orders_by_date_range',
    'create_order',
    'update_order_status'
]

# Keep the original OrderService class implementation
# This is just a placeholder to maintain compatibility with existing code
class OrderService:
    """Order service class that wraps the functional API."""
    
    def __init__(self, session=None):
        self.session = session
    
    # Add wrapper methods as needed to maintain compatibility
    # with existing code that uses the OrderService class

# Keep the original OrderService class implementation
# This is just a placeholder to maintain compatibility with existing code
class QuoteService:
    """Quote service class that wraps the functional API."""
    
    def __init__(self, session=None):
        self.session = session
    
    # Add wrapper methods as needed to maintain compatibility
    # with existing code that uses the QuoteService class
