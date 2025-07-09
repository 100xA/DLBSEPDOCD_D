"""E-commerce integration tests."""

import json
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.urls import reverse

import pytest

from devops_pipeline.apps.catalog.models import Product
from devops_pipeline.apps.orders.models import Order

User = get_user_model()


@pytest.fixture(autouse=True)
def product(db):
    return Product.objects.create(
        sku="T-1000",
        name="Test Product",
        price=Decimal("199.00"),
        stock=5,
    )


@pytest.mark.integration
@pytest.mark.django_db(transaction=True)
def test_checkout_creates_order_and_caches_price(client, product):
    """Test that checkout creates order and caches the price."""
    # Create a user
    user = User.objects.create_user(
        username="testuser", email="test@example.com", password="testpass123"
    )
    client.force_login(user)

    url = reverse("orders:create")
    payload = {"sku": product.sku, "qty": 2}

    response = client.post(
        url,
        data=json.dumps(payload),
        content_type="application/json",
    )

    assert response.status_code == 201
    data = response.json()

    order = Order.objects.get(pk=data["id"])
    assert order.total == product.price * 2
    assert order.status == Order.Status.PAID

    cached_price = cache.get(f"order:{order.pk}:total")
    assert cached_price == str(order.total)
