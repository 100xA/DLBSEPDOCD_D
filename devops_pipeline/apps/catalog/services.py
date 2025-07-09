"""Catalog services."""

from .models import Product


def create_discounted_product(price, discount, final_price=None):
    """Create a discounted product for testing."""
    if final_price is None:
        final_price = price - discount

    product = Product.objects.create(
        sku=f"DISC-{price}-{discount}",
        name=f"Discounted Product {price}",
        description="A discounted product for testing",
        price=final_price,
        stock=10,
    )

    return product
