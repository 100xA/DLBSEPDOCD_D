"""E2E test configuration and fixtures."""

from django.contrib.auth import get_user_model

import pytest
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

from devops_pipeline.apps.catalog.models import Product

User = get_user_model()


# Use the built-in live_server fixture from pytest-django
# No need to define our own - it's automatically available


@pytest.fixture(scope="session")
def browser():
    """Create Chrome browser instance for E2E tests."""
    options = Options()
    options.add_argument("--headless")  # Run headless for CI
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--window-size=1920,1080")

    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)
    driver.implicitly_wait(10)

    yield driver

    driver.quit()


@pytest.fixture
def test_user(db):
    """Create a test user."""
    return User.objects.create_user(
        username="testuser", email="test@example.com", password="testpassword123"
    )


@pytest.fixture
def test_product(db):
    """Create a test product."""
    return Product.objects.create(
        sku="TEST-001",
        name="Test Product",
        description="A test product for E2E testing",
        price="29.99",
        stock=10,
        is_active=True,
    )
