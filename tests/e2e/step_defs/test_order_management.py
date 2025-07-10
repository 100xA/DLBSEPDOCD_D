"""Step definitions for order management E2E tests."""

from django.contrib.auth import get_user_model

from pytest_bdd import given, parsers, scenarios, then, when
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select, WebDriverWait

from devops_pipeline.apps.catalog.models import Product

User = get_user_model()

# Load scenarios from feature file
scenarios("../features/order_management.feature")


@given("the application is running")
def application_running(live_server):
    """Ensure the Django live server is running."""
    assert live_server.url is not None


@given(parsers.parse('a test user exists with username "{username}" and password "{password}"'))
def create_test_user(db, username, password):
    """Create a test user."""
    User.objects.create_user(username=username, password=password)


@given(
    parsers.parse(
        'a test product exists with SKU "{sku}", name "{name}", price "{price}", and stock {stock:d}'
    )
)
def create_test_product(db, sku, name, price, stock):
    """Create a test product."""
    Product.objects.create(
        sku=sku,
        name=name,
        description=f"Description for {name}",
        price=price,
        stock=stock,
        is_active=True,
    )


@given("the user is on the product catalog page")
def navigate_to_catalog(browser, live_server):
    """Navigate to the product catalog page."""
    browser.get(live_server.url)
    wait = WebDriverWait(browser, 10)
    wait.until(EC.presence_of_element_located((By.TAG_NAME, "h1")))


@given("the user is not logged in")
def ensure_logged_out(browser):
    """Ensure user is not logged in."""
    # Check if logout link exists and click it
    try:
        logout_link = browser.find_element(By.LINK_TEXT, "Logout")
        logout_link.click()
    except Exception:
        pass  # User is already logged out


@given(parsers.parse('the user is logged in as "{username}"'))
def login_user(browser, live_server, username):
    """Log in the user."""
    browser.get(live_server.url)

    # Click login link
    login_link = browser.find_element(By.LINK_TEXT, "Login")
    login_link.click()

    # Fill login form
    username_field = browser.find_element(By.NAME, "username")
    password_field = browser.find_element(By.NAME, "password")

    username_field.send_keys(username)
    password_field.send_keys("testpassword123")

    # Submit form
    login_button = browser.find_element(By.CSS_SELECTOR, 'button[type="submit"]')
    login_button.click()

    # Wait for redirect
    wait = WebDriverWait(browser, 10)
    wait.until(EC.presence_of_element_located((By.TEXT, f"Welcome, {username}!")))


@given(parsers.parse('the user has placed an order for product "{sku}" with quantity {quantity:d}'))
def place_order(browser, live_server, sku, quantity):
    """Place an order for a product."""
    browser.get(live_server.url)

    # Find product and select quantity
    product_item = browser.find_element(By.CSS_SELECTOR, f'[data-sku="{sku}"]')
    select_element = product_item.find_element(By.NAME, "qty")
    select = Select(select_element)
    select.select_by_value(str(quantity))

    # Click order button
    order_button = product_item.find_element(By.NAME, "add_to_order")
    order_button.click()

    # Wait for success page
    wait = WebDriverWait(browser, 10)
    wait.until(EC.presence_of_element_located((By.TEXT, "Order Successfully Created!")))


@when(parsers.parse('the user logs in with username "{username}" and password "{password}"'))
def when_user_logs_in(browser, username, password):
    """User performs login action."""
    # Click login link
    login_link = browser.find_element(By.LINK_TEXT, "Login")
    login_link.click()

    # Fill and submit login form
    username_field = browser.find_element(By.NAME, "username")
    password_field = browser.find_element(By.NAME, "password")

    username_field.send_keys(username)
    password_field.send_keys(password)

    login_button = browser.find_element(By.CSS_SELECTOR, 'button[type="submit"]')
    login_button.click()


@when("the user is redirected to the product catalog")
def wait_for_catalog_redirect(browser):
    """Wait for redirect to catalog page."""
    wait = WebDriverWait(browser, 10)
    wait.until(EC.presence_of_element_located((By.TEXT, "Available Products")))


@when(parsers.parse('the user selects quantity "{quantity}" for product "{sku}"'))
def select_quantity(browser, quantity, sku):
    """Select quantity for a product."""
    product_item = browser.find_element(By.CSS_SELECTOR, f'[data-sku="{sku}"]')
    select_element = product_item.find_element(By.NAME, "qty")
    select = Select(select_element)
    select.select_by_value(quantity)


@when('the user clicks "Order Now"')
def click_order_now(browser):
    """Click the Order Now button."""
    order_button = browser.find_element(By.NAME, "add_to_order")
    order_button.click()


@when(parsers.parse('the user views the product "{sku}"'))
def view_product(browser, sku):
    """View a specific product."""
    product_item = browser.find_element(By.CSS_SELECTOR, f'[data-sku="{sku}"]')
    browser.execute_script("arguments[0].scrollIntoView();", product_item)


@when('the user navigates to "View My Orders"')
def navigate_to_orders(browser):
    """Navigate to the orders page."""
    orders_link = browser.find_element(By.LINK_TEXT, "View My Orders")
    orders_link.click()


@when("the user sees the order confirmation page")
def on_confirmation_page(browser):
    """Verify user is on order confirmation page."""
    wait = WebDriverWait(browser, 10)
    wait.until(EC.presence_of_element_located((By.TEXT, "Order Successfully Created!")))


@when('the user clicks "Continue Shopping"')
def click_continue_shopping(browser):
    """Click the Continue Shopping button."""
    continue_button = browser.find_element(By.LINK_TEXT, "Continue Shopping")
    continue_button.click()


@then("the user should see a success message")
def verify_success_message(browser):
    """Verify success message is displayed."""
    wait = WebDriverWait(browser, 10)
    success_element = wait.until(EC.presence_of_element_located((By.CLASS_NAME, "success")))
    assert "Order Successfully Created!" in success_element.text


@then(parsers.parse('the order should be created with total "{total}"'))
def verify_order_total(browser, total):
    """Verify the order total."""
    wait = WebDriverWait(browser, 10)
    total_element = wait.until(
        EC.presence_of_element_located((By.XPATH, f"//*[contains(text(), '${total}')]"))
    )
    assert total_element is not None


@then(parsers.parse('the order status should be "{status}"'))
def verify_order_status(browser, status):
    """Verify the order status."""
    wait = WebDriverWait(browser, 10)
    status_element = wait.until(
        EC.presence_of_element_located((By.XPATH, f"//*[contains(text(), '{status}')]"))
    )
    assert status_element is not None


@then(parsers.parse('the user should see "{text}"'))
def verify_text_present(browser, text):
    """Verify specific text is present on the page."""
    wait = WebDriverWait(browser, 10)
    element = wait.until(
        EC.presence_of_element_located((By.XPATH, f"//*[contains(text(), '{text}')]"))
    )
    assert element is not None


@then("the user should not see an order form")
def verify_no_order_form(browser):
    """Verify no order form is present."""
    order_forms = browser.find_elements(By.CLASS_NAME, "order-form")
    assert len(order_forms) == 0


@then("the user should see their order history")
def verify_order_history(browser):
    """Verify order history is displayed."""
    wait = WebDriverWait(browser, 10)
    order_list = wait.until(EC.presence_of_element_located((By.CLASS_NAME, "order-list")))
    assert order_list is not None


@then(parsers.parse('the order should show "{item_text}"'))
def verify_order_item(browser, item_text):
    """Verify specific order item text."""
    wait = WebDriverWait(browser, 10)
    item_element = wait.until(
        EC.presence_of_element_located((By.XPATH, f"//*[contains(text(), '{item_text}')]"))
    )
    assert item_element is not None


@then("the user should be back on the product catalog page")
def verify_back_on_catalog(browser):
    """Verify user is back on the catalog page."""
    wait = WebDriverWait(browser, 10)
    catalog_header = wait.until(EC.presence_of_element_located((By.TEXT, "Available Products")))
    assert catalog_header is not None
