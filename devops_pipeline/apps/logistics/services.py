"""Logistics services."""

import random
import string
from datetime import datetime, timedelta

from .models import Shipping, ShippingEvent, Warehouse


def generate_tracking_number(carrier):
    """Generate a realistic tracking number for the carrier."""
    if carrier == "dhl":
        return f"DHL{random.randint(10000000, 99999999)}"
    elif carrier == "ups":
        return f"1Z{''.join(random.choices(string.ascii_uppercase + string.digits, k=16))}"
    elif carrier == "fedex":
        return f"{random.randint(1000, 9999)} {random.randint(1000, 9999)} {random.randint(1000, 9999)}"
    elif carrier == "hermes":
        return f"H{random.randint(100000000000, 999999999999)}"
    elif carrier == "dpd":
        return f"{random.randint(10000000000000, 99999999999999)}"
    else:
        return f"TRACK{random.randint(100000000, 999999999)}"


def create_shipment(order, shipping_address, carrier="dhl"):
    """Create a shipment for an order."""
    # Find an active warehouse (simplified logic)
    warehouse = Warehouse.objects.filter(is_active=True).first()
    if not warehouse:
        warehouse = Warehouse.objects.create(
            name="Main Warehouse",
            code="MAIN",
            address="Hauptlager Str. 1, 70173 Stuttgart",
            capacity=10000
        )
    
    # Generate tracking number
    tracking_number = generate_tracking_number(carrier)
    
    # Create shipping record
    shipping = Shipping.objects.create(
        order=order,
        warehouse=warehouse,
        tracking_number=tracking_number,
        carrier=carrier,
        shipping_address=shipping_address,
        estimated_delivery=datetime.now() + timedelta(days=3),
        weight=0.5,  # Default weight
        dimensions="20 x 15 x 10 cm"
    )
    
    # Create initial shipping event
    ShippingEvent.objects.create(
        shipping=shipping,
        status=Shipping.Status.PENDING,
        location=warehouse.address,
        description="Order received at warehouse"
    )
    
    return shipping


def update_shipping_status(shipping, new_status, location="", description=""):
    """Update shipping status with event tracking."""
    shipping.status = new_status
    shipping.save()
    
    # Create shipping event
    ShippingEvent.objects.create(
        shipping=shipping,
        status=new_status,
        location=location,
        description=description or f"Status updated to {shipping.get_status_display()}"
    )
    
    # Update order status if delivered
    if new_status == Shipping.Status.DELIVERED:
        shipping.order.status = "delivered"
        shipping.order.save()
        shipping.actual_delivery = datetime.now()
        shipping.save()


def simulate_shipping_progress(shipping):
    """Simulate realistic shipping progress for testing."""
    statuses = [
        (Shipping.Status.PICKED, "Package picked from shelf"),
        (Shipping.Status.PACKED, "Package packed and ready for shipment"),
        (Shipping.Status.SHIPPED, "Package shipped from warehouse"),
        (Shipping.Status.IN_TRANSIT, "Package in transit to destination"),
        (Shipping.Status.DELIVERED, "Package delivered successfully")
    ]
    
    for status, description in statuses:
        if shipping.status != status:
            update_shipping_status(
                shipping, 
                status, 
                location=f"Transit Hub {random.randint(1, 5)}", 
                description=description
            )
            break 