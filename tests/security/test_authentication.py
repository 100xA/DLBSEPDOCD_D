"""Security tests for authentication and authorization."""

import pytest
from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse

from devops_pipeline.apps.catalog.models import Product
from devops_pipeline.apps.orders.models import Order

User = get_user_model()


class AuthenticationSecurityTests(TestCase):
    """Test authentication security measures."""

    def setUp(self):
        """Set up test data."""
        self.client = Client()
        self.user = User.objects.create_user(
            username="testuser",
            password="secure_password123",
            email="test@example.com"
        )
        self.other_user = User.objects.create_user(
            username="otheruser",
            password="secure_password123",
            email="other@example.com"
        )
        self.product = Product.objects.create(
            sku="TEST-001",
            name="Test Product",
            price="29.99",
            stock=10
        )

    def test_unauthenticated_access_to_protected_endpoints(self):
        """Test that protected endpoints require authentication."""
        protected_urls = [
            reverse('orders:create'),
            reverse('orders:list'),
            reverse('orders:create_web'),
        ]
        
        for url in protected_urls:
            response = self.client.get(url)
            self.assertIn(response.status_code, [302, 401, 403], 
                         f"Endpoint {url} should require authentication")

    def test_user_can_only_access_own_orders(self):
        """Test that users can only access their own orders."""
        # Create orders for both users
        order1 = Order.objects.create(user=self.user, total="29.99")
        order2 = Order.objects.create(user=self.other_user, total="39.99")
        
        # Login as first user
        self.client.login(username="testuser", password="secure_password123")
        
        response = self.client.get(reverse('orders:list'))
        self.assertEqual(response.status_code, 200)
        
        # Check that only own orders are visible
        orders = response.context['orders']
        self.assertIn(order1, orders)
        self.assertNotIn(order2, orders)

    def test_session_security(self):
        """Test session security measures."""
        # Login
        self.client.login(username="testuser", password="secure_password123")
        
        # Check that session is created
        session_key = self.client.session.session_key
        self.assertIsNotNone(session_key)
        
        # Check session data
        self.assertIn('_auth_user_id', self.client.session)
        
        # Logout
        self.client.logout()
        
        # Verify session is cleared
        self.assertNotIn('_auth_user_id', self.client.session)

    def test_password_security_requirements(self):
        """Test password validation."""
        weak_passwords = [
            "123",
            "password",
            "testuser",  # username similarity
            "12345678",  # all numeric
        ]
        
        for weak_password in weak_passwords:
            with self.assertRaises(Exception):
                User.objects.create_user(
                    username="newuser",
                    password=weak_password,
                    email="new@example.com"
                )

    def test_brute_force_protection(self):
        """Test protection against brute force attacks."""
        # Attempt multiple failed logins
        for i in range(10):
            response = self.client.post(reverse('auth:login'), {
                'username': 'testuser',
                'password': 'wrong_password'
            })
            self.assertNotEqual(response.status_code, 200)


class APISecurityTests(TestCase):
    """Test API endpoint security."""

    def setUp(self):
        """Set up test data."""
        self.client = Client()
        self.user = User.objects.create_user(
            username="apiuser",
            password="secure_password123"
        )
        self.product = Product.objects.create(
            sku="API-001",
            name="API Test Product",
            price="19.99",
            stock=5
        )

    def test_csrf_protection_on_web_endpoints(self):
        """Test CSRF protection on web form submissions."""
        self.client.login(username="apiuser", password="secure_password123")
        
        # Attempt POST without CSRF token
        response = self.client.post(
            reverse('orders:create_web'),
            {'sku': 'API-001', 'qty': 1},
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )
        
        # Should fail due to missing CSRF token
        self.assertEqual(response.status_code, 403)

    def test_json_input_validation(self):
        """Test JSON input validation for API endpoints."""
        self.client.login(username="apiuser", password="secure_password123")
        
        # Test invalid JSON
        response = self.client.post(
            reverse('orders:create'),
            'invalid json',
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 400)
        
        # Test missing required fields
        response = self.client.post(
            reverse('orders:create'),
            '{}',
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 404)  # Product not found

    def test_sql_injection_protection(self):
        """Test protection against SQL injection attacks."""
        self.client.login(username="apiuser", password="secure_password123")
        
        malicious_inputs = [
            "'; DROP TABLE catalog_product; --",
            "' OR '1'='1",
            "'; DELETE FROM orders_order; --",
            "' UNION SELECT * FROM auth_user --"
        ]
        
        for malicious_input in malicious_inputs:
            response = self.client.post(
                reverse('orders:create'),
                {'sku': malicious_input, 'qty': 1},
                content_type='application/json'
            )
            # Should not cause server error (500)
            self.assertNotEqual(response.status_code, 500)

    def test_xss_protection(self):
        """Test protection against XSS attacks."""
        # Create product with malicious script in name
        malicious_product = Product.objects.create(
            sku="XSS-001",
            name="<script>alert('XSS')</script>Test Product",
            price="29.99",
            stock=1
        )
        
        response = self.client.get(reverse('catalog:product_list'))
        self.assertEqual(response.status_code, 200)
        
        # Check that script tags are escaped
        self.assertNotContains(response, "<script>alert('XSS')</script>")
        self.assertContains(response, "&lt;script&gt;")

    def test_input_length_limits(self):
        """Test input length validation."""
        self.client.login(username="apiuser", password="secure_password123")
        
        # Test extremely long SKU
        long_sku = "A" * 1000
        response = self.client.post(
            reverse('orders:create'),
            {'sku': long_sku, 'qty': 1},
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 404)  # Product not found

    def test_rate_limiting_considerations(self):
        """Test rapid requests to detect potential rate limiting needs."""
        self.client.login(username="apiuser", password="secure_password123")
        
        # Make rapid requests to order creation endpoint
        responses = []
        for i in range(20):
            response = self.client.post(
                reverse('orders:create'),
                {'sku': 'API-001', 'qty': 1},
                content_type='application/json'
            )
            responses.append(response.status_code)
        
        # All requests should succeed (no rate limiting implemented)
        # This test documents current behavior
        success_responses = [r for r in responses if r == 201]
        self.assertGreater(len(success_responses), 0)


class DataAccessSecurityTests(TestCase):
    """Test data access security."""

    def setUp(self):
        """Set up test data."""
        self.client = Client()
        self.user1 = User.objects.create_user(
            username="user1",
            password="secure_password123"
        )
        self.user2 = User.objects.create_user(
            username="user2", 
            password="secure_password123"
        )
        self.product = Product.objects.create(
            sku="DATA-001",
            name="Data Test Product",
            price="15.99",
            stock=3
        )

    def test_order_data_isolation(self):
        """Test that users can only access their own order data."""
        # Create orders for both users
        order1 = Order.objects.create(user=self.user1, total="15.99")
        order2 = Order.objects.create(user=self.user2, total="31.98")
        
        # Login as user1
        self.client.login(username="user1", password="secure_password123")
        
        # Access own orders
        response = self.client.get(reverse('orders:list'))
        self.assertEqual(response.status_code, 200)
        orders = response.context['orders']
        order_ids = [order.id for order in orders]
        
        self.assertIn(order1.id, order_ids)
        self.assertNotIn(order2.id, order_ids)

    def test_admin_access_protection(self):
        """Test that admin interface requires proper permissions."""
        # Regular user should not access admin
        self.client.login(username="user1", password="secure_password123")
        response = self.client.get('/admin/')
        self.assertEqual(response.status_code, 302)  # Redirect to login
        
        # Create admin user
        admin_user = User.objects.create_superuser(
            username="admin",
            password="admin_password123",
            email="admin@example.com"
        )
        
        # Admin should access admin interface
        self.client.login(username="admin", password="admin_password123")
        response = self.client.get('/admin/')
        self.assertEqual(response.status_code, 200) 