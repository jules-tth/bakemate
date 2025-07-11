"""
Order service utility functions for BakeMate backend.
These functions implement core order processing logic.
"""

from typing import List, Dict, Any, Tuple, Optional
from datetime import datetime, timedelta
from uuid import UUID
from sqlmodel import Session, select


def calculate_order_total(order_items: List[Dict[str, Any]]) -> float:
    """
    Calculate the total cost of an order based on item quantities and unit prices.

    Args:
        order_items: List of order items with quantity and unit_price

    Returns:
        float: Total order cost
    """
    total = 0.0
    for item in order_items:
        total += item["quantity"] * item["unit_price"]
    return round(total, 2)


def apply_discount(
    order_total: float, discount_type: str, discount_value: float
) -> float:
    """
    Apply a discount to an order total.

    Args:
        order_total: The original order total
        discount_type: Type of discount ('percentage' or 'fixed')
        discount_value: Value of the discount (percentage or fixed amount)

    Returns:
        float: Discounted order total
    """
    if discount_type == "percentage":
        discount_amount = order_total * (discount_value / 100)
    elif discount_type == "fixed":
        discount_amount = discount_value
    else:
        # Invalid discount type, no discount applied
        return order_total

    discounted_total = order_total - discount_amount
    return max(0, round(discounted_total, 2))  # Ensure total is not negative


def get_order_by_id(order_id: str, session: Session) -> Optional[Any]:
    """
    Retrieve an order by its ID.

    Args:
        order_id: The ID of the order to retrieve
        session: Database session

    Returns:
        Order object if found, None otherwise
    """
    # This is a mock implementation since we don't have the actual Order model
    # In a real implementation, we would query the database
    from app.models.order import Order

    return session.get(Order, order_id)


def calculate_order_tax(order_subtotal: float, tax_rate: float) -> float:
    """
    Calculate tax for an order.

    Args:
        order_subtotal: The order subtotal before tax
        tax_rate: The tax rate as a decimal (e.g., 0.08 for 8%)

    Returns:
        float: Tax amount
    """
    return round(order_subtotal * tax_rate, 2)


def calculate_delivery_fee(distance_km: float) -> float:
    """
    Calculate delivery fee based on distance.

    Args:
        distance_km: Distance in kilometers

    Returns:
        float: Delivery fee
    """
    base_fee = 5.00
    per_km_fee = 0.50
    return round(base_fee + (distance_km * per_km_fee), 2)


def validate_order_data(order_data: Dict[str, Any]) -> bool:
    """
    Validate order data to ensure it contains all required fields.

    Args:
        order_data: Order data dictionary

    Returns:
        bool: True if valid, False otherwise
    """
    required_fields = [
        "customer_name",
        "customer_email",
        "delivery_date",
        "delivery_address",
        "items",
    ]

    # Check if all required fields are present
    for field in required_fields:
        if field not in order_data:
            return False

    # Check if items list is not empty
    if not order_data["items"]:
        return False

    return True


def get_order_items(order_id: str, session: Session) -> List[Any]:
    """
    Get all items for a specific order.

    Args:
        order_id: The ID of the order
        session: Database session

    Returns:
        List of order items
    """
    # This is a mock implementation since we don't have the actual OrderItem model
    # In a real implementation, we would query the database
    from app.models.order import OrderItem

    statement = select(OrderItem).where(OrderItem.order_id == order_id)
    return session.exec(statement).all()


def cancel_order(order_id: str, session: Session) -> Optional[Any]:
    """
    Cancel an order by updating its status.

    Args:
        order_id: The ID of the order to cancel
        session: Database session

    Returns:
        Updated order object if found, None otherwise
    """
    # This is a mock implementation since we don't have the actual Order model
    # In a real implementation, we would query the database
    from app.models.order import Order

    order = session.get(Order, order_id)
    if order:
        order.status = "canceled"
        session.commit()
        session.refresh(order)
    return order


def get_orders_by_date_range(
    start_date: datetime, end_date: datetime, session: Session
) -> List[Any]:
    """
    Get all orders within a specific date range.

    Args:
        start_date: Start date of the range
        end_date: End date of the range
        session: Database session

    Returns:
        List of orders within the date range
    """
    # This is a mock implementation since we don't have the actual Order model
    # In a real implementation, we would query the database
    from app.models.order import Order

    statement = select(Order).where(
        Order.created_at >= start_date, Order.created_at <= end_date
    )
    return session.exec(statement).all()


def create_order(order_data: Dict[str, Any], session: Session) -> Any:
    """
    Create a new order.

    Args:
        order_data: Order data dictionary
        session: Database session

    Returns:
        Newly created order object
    """
    # This is a mock implementation since we don't have the actual Order model
    # In a real implementation, we would create a new Order object
    from app.models.order import Order, OrderItem

    # Validate order data
    if not validate_order_data(order_data):
        raise ValueError("Invalid order data")

    # Calculate order total
    items = order_data.get("items", [])
    subtotal = calculate_order_total(items)

    # Create order
    order = Order(
        customer_name=order_data["customer_name"],
        customer_email=order_data["customer_email"],
        delivery_date=order_data["delivery_date"],
        delivery_address=order_data["delivery_address"],
        subtotal=subtotal,
        total=subtotal,  # Will be updated with tax and fees
        status="pending",
    )

    session.add(order)
    session.commit()
    session.refresh(order)

    # Create order items
    for item_data in items:
        item = OrderItem(
            order_id=order.id,
            recipe_id=item_data["recipe_id"],
            quantity=item_data["quantity"],
            unit_price=item_data["unit_price"],
            total_price=item_data["quantity"] * item_data["unit_price"],
        )
        session.add(item)

    session.commit()
    session.refresh(order)

    return order


def update_order_status(order_id: str, status: str, session: Session) -> Optional[Any]:
    """
    Update the status of an order.

    Args:
        order_id: The ID of the order to update
        status: New status value
        session: Database session

    Returns:
        Updated order object if found, None otherwise
    """
    # This is a mock implementation since we don't have the actual Order model
    # In a real implementation, we would query the database
    from app.models.order import Order

    order = session.get(Order, order_id)
    if order:
        order.status = status
        session.commit()
        session.refresh(order)
    return order
