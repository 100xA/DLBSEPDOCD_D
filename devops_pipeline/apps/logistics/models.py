"""Logistics models."""

from django.db import models

from devops_pipeline.apps.orders.models import Order


class Warehouse(models.Model):
    """Warehouse model for inventory management."""

    name = models.CharField(max_length=100)
    address = models.TextField()
    code = models.CharField(max_length=10, unique=True)
    capacity = models.PositiveIntegerField()
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} ({self.code})"


class Shipping(models.Model):
    """Shipping model for order logistics."""

    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        PICKED = "picked", "Picked"
        PACKED = "packed", "Packed"
        SHIPPED = "shipped", "Shipped"
        IN_TRANSIT = "in_transit", "In Transit"
        DELIVERED = "delivered", "Delivered"
        RETURNED = "returned", "Returned"

    class Carrier(models.TextChoices):
        DHL = "dhl", "DHL"
        UPS = "ups", "UPS"
        FEDEX = "fedex", "FedEx"
        HERMES = "hermes", "Hermes"
        DPD = "dpd", "DPD"

    order = models.OneToOneField(Order, on_delete=models.CASCADE, related_name="shipping")
    warehouse = models.ForeignKey(Warehouse, on_delete=models.CASCADE)
    tracking_number = models.CharField(max_length=50, unique=True)
    carrier = models.CharField(max_length=20, choices=Carrier.choices)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    shipping_address = models.TextField()
    estimated_delivery = models.DateTimeField(null=True, blank=True)
    actual_delivery = models.DateTimeField(null=True, blank=True)
    weight = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    dimensions = models.CharField(max_length=50, blank=True)  # Format: "L x W x H cm"
    shipping_cost = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"Shipping for Order #{self.order.pk} - {self.tracking_number}"


class ShippingEvent(models.Model):
    """Track shipping events for detailed logistics."""

    shipping = models.ForeignKey(Shipping, related_name="events", on_delete=models.CASCADE)
    status = models.CharField(max_length=20, choices=Shipping.Status.choices)
    location = models.CharField(max_length=100, blank=True)
    description = models.TextField()
    event_time = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-event_time"]

    def __str__(self):
        return f"{self.shipping.tracking_number} - {self.status} at {self.event_time}"


class Inventory(models.Model):
    """Inventory tracking across warehouses."""

    product = models.ForeignKey("catalog.Product", on_delete=models.CASCADE)
    warehouse = models.ForeignKey(Warehouse, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=0)
    reserved_quantity = models.PositiveIntegerField(default=0)  # Reserved for pending orders
    last_updated = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ["product", "warehouse"]
        ordering = ["product__name", "warehouse__name"]

    def __str__(self):
        return f"{self.product.sku} at {self.warehouse.code}: {self.quantity}"

    @property
    def available_quantity(self):
        """Calculate available inventory."""
        return max(0, self.quantity - self.reserved_quantity) 