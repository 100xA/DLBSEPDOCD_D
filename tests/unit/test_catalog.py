"""Catalog unit tests."""

from decimal import Decimal

import pytest

from devops_pipeline.apps.catalog import services


@pytest.mark.unit
def test_create_discounted_product_calls_orm_once(mocker):
    """Test that create_discounted_product calls ORM only once."""
    create_mock = mocker.patch("devops_pipeline.apps.catalog.models.Product.objects.create")
    fake_instance = object()
    create_mock.return_value = fake_instance

    result = services.create_discounted_product(price=Decimal("100.00"), discount=Decimal("10.00"))

    create_mock.assert_called_once_with(
        sku="DISC-100.00-10.00",
        name="Discounted Product 100.00",
        description="A discounted product for testing",
        price=Decimal("90.00"),
        stock=10,
    )
    assert result is fake_instance
