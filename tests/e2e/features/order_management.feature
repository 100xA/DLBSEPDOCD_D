Feature: Order Management
  As a customer
  I want to browse products and place orders
  So that I can purchase items from the e-commerce store

  Background:
    Given the application is running
    And a test user exists with username "testuser" and password "testpassword123"
    And a test product exists with SKU "TEST-001", name "Test Product", price "29.99", and stock 10

  Scenario: Successful order placement
    Given the user is on the product catalog page
    When the user logs in with username "testuser" and password "testpassword123"
    And the user is redirected to the product catalog
    And the user selects quantity "2" for product "TEST-001"
    And the user clicks "Order Now"
    Then the user should see a success message
    And the order should be created with total "59.98"
    And the order status should be "Paid"

  Scenario: User must be logged in to place order
    Given the user is on the product catalog page
    And the user is not logged in
    When the user views the product "TEST-001"
    Then the user should see "Login to order"
    And the user should not see an order form

  Scenario: User can view order history
    Given the user is logged in as "testuser"
    And the user has placed an order for product "TEST-001" with quantity 1
    When the user navigates to "View My Orders"
    Then the user should see their order history
    And the order should show "1x Test Product - $29.99 each"
    
  Scenario: User can continue shopping after placing an order
    Given the user is logged in as "testuser"
    And the user has placed an order for product "TEST-001" with quantity 1
    When the user sees the order confirmation page
    And the user clicks "Continue Shopping"
    Then the user should be back on the product catalog page 