"""Security tests for input validation and data sanitization."""

import json
import pytest
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse

from devops_pipeline.apps.catalog.models import Product
from devops_pipeline.apps.orders.models import Order

User = get_user_model()


class InputValidationSecurityTests(TestCase):
    """Test input validation security measures."""

    def setUp(self):
        """Set up test data."""
        self.client = Client()
        self.user = User.objects.create_user(
            username="testuser",
            password="secure_password123"
        )
        self.product = Product.objects.create(
            sku="VALID-001",
            name="Valid Product",
            price="25.99",
            stock=10
        )
        self.client.login(username="testuser", password="secure_password123")

    def test_quantity_validation(self):
        """Test quantity input validation."""
        invalid_quantities = [
            -1,          # Negative
            0,           # Zero
            999999,      # Extremely large
            "abc",       # Non-numeric
            "1.5",       # Decimal
            None,        # Null
        ]
        
        for qty in invalid_quantities:
            response = self.client.post(
                reverse('orders:create'),
                json.dumps({'sku': 'VALID-001', 'qty': qty}),
                content_type='application/json'
            )
            # Should handle invalid quantities gracefully
            self.assertIn(response.status_code, [400, 404])

    def test_sku_validation(self):
        """Test SKU input validation."""
        invalid_skus = [
            "",                    # Empty string
            " ",                   # Whitespace only
            None,                  # Null
            "A" * 100,            # Too long
            "../../etc/passwd",    # Path traversal attempt
            "<script>",           # XSS attempt
            "'; DROP TABLE",      # SQL injection attempt
        ]
        
        for sku in invalid_skus:
            response = self.client.post(
                reverse('orders:create'),
                json.dumps({'sku': sku, 'qty': 1}),
                content_type='application/json'
            )
            # Should return 404 (product not found) or 400 (bad request)
            self.assertIn(response.status_code, [400, 404])

    def test_price_manipulation_attempts(self):
        """Test protection against price manipulation."""
        # Attempt to send custom price
        malicious_data = {
            'sku': 'VALID-001',
            'qty': 1,
            'price': '0.01',  # Attempt to override price
            'total': '0.01',  # Attempt to override total
        }
        
        response = self.client.post(
            reverse('orders:create'),
            json.dumps(malicious_data),
            content_type='application/json'
        )
        
        if response.status_code == 201:
            # If order was created, verify price wasn't manipulated
            order_data = json.loads(response.content)
            order = Order.objects.get(id=order_data['id'])
            self.assertEqual(order.total, Decimal('25.99'))

    def test_order_tampering_attempts(self):
        """Test protection against order data tampering."""
        tampering_attempts = [
            {'user_id': 999, 'sku': 'VALID-001', 'qty': 1},
            {'user': 'admin', 'sku': 'VALID-001', 'qty': 1},
            {'status': 'delivered', 'sku': 'VALID-001', 'qty': 1},
            {'id': 1, 'sku': 'VALID-001', 'qty': 1},
        ]
        
        for attempt in tampering_attempts:
            response = self.client.post(
                reverse('orders:create'),
                json.dumps(attempt),
                content_type='application/json'
            )
            
            if response.status_code == 201:
                # Verify tampering was ignored
                order_data = json.loads(response.content)
                order = Order.objects.get(id=order_data['id'])
                self.assertEqual(order.user, self.user)
                self.assertEqual(order.status, Order.Status.PAID)

    def test_json_structure_validation(self):
        """Test JSON structure validation."""
        invalid_json_data = [
            "not_json",
            '{"incomplete": json',
            '[]',  # Array instead of object
            'null',
            '{"nested": {"too": {"deep": {"structure": true}}}}',
        ]
        
        for invalid_data in invalid_json_data:
            response = self.client.post(
                reverse('orders:create'),
                invalid_data,
                content_type='application/json'
            )
            self.assertEqual(response.status_code, 400)

    def test_unicode_and_encoding_handling(self):
        """Test handling of unicode and special encoding."""
        unicode_test_cases = [
            "SKU-émojis-🛒",
            "SKU-中文-测试",
            "SKU-العربية",
            "SKU-русский",
            "\x00\x01\x02",  # Null bytes and control characters
        ]
        
        for test_sku in unicode_test_cases:
            response = self.client.post(
                reverse('orders:create'),
                json.dumps({'sku': test_sku, 'qty': 1}),
                content_type='application/json'
            )
            # Should handle gracefully without server error
            self.assertNotEqual(response.status_code, 500)

    def test_web_form_validation(self):
        """Test web form input validation."""
        # Test CSRF protection with valid token
        response = self.client.get(reverse('catalog:product_list'))
        csrf_token = response.context['csrf_token']
        
        # Valid form submission
        response = self.client.post(
            reverse('orders:create_web'),
            {
                'sku': 'VALID-001',
                'qty': '2',
                'csrfmiddlewaretoken': csrf_token
            }
        )
        self.assertEqual(response.status_code, 200)
        
        # Invalid quantity in form
        response = self.client.post(
            reverse('orders:create_web'),
            {
                'sku': 'VALID-001',
                'qty': '-1',
                'csrfmiddlewaretoken': csrf_token
            }
        )
        # Should redirect back to product list
        self.assertEqual(response.status_code, 302)

    def test_file_upload_security(self):
        """Test file upload security (if applicable)."""
        # Note: Current app doesn't have file uploads,
        # but this would test for malicious file uploads
        malicious_files = [
            ('shell.php', b'<?php system($_GET["cmd"]); ?>'),
            ('script.html', b'<script>alert("XSS")</script>'),
            ('large_file.txt', b'A' * (10 * 1024 * 1024)),  # 10MB file
        ]
        
        # This would be relevant if the app had file upload functionality
        # for product images or user avatars
        pass

    def test_http_method_validation(self):
        """Test HTTP method validation."""
        # Test that endpoints only accept intended methods
        order_create_url = reverse('orders:create')
        
        # Should only accept POST
        response = self.client.get(order_create_url)
        self.assertEqual(response.status_code, 405)  # Method not allowed
        
        response = self.client.put(order_create_url)
        self.assertEqual(response.status_code, 405)
        
        response = self.client.delete(order_create_url)
        self.assertEqual(response.status_code, 405)

    def test_content_type_validation(self):
        """Test content type validation."""
        valid_data = {'sku': 'VALID-001', 'qty': 1}
        
        # Test with wrong content type
        response = self.client.post(
            reverse('orders:create'),
            json.dumps(valid_data),
            content_type='text/plain'
        )
        # Should handle gracefully
        self.assertIn(response.status_code, [400, 415])
        
        # Test with no content type
        response = self.client.post(
            reverse('orders:create'),
            json.dumps(valid_data)
        )
        # Should handle gracefully
        self.assertIn(response.status_code, [201, 400])


class DataSanitizationTests(TestCase):
    """Test data sanitization and encoding."""

    def setUp(self):
        """Set up test data."""
        self.client = Client()
        self.user = User.objects.create_user(
            username="testuser",
            password="secure_password123"
        )

    def test_html_escaping_in_templates(self):
        """Test that HTML is properly escaped in templates."""
        # Create product with potential XSS payload
        xss_product = Product.objects.create(
            sku="XSS-TEST",
            name='<script>alert("XSS")</script>Malicious Product',
            description='<img src="x" onerror="alert(1)">',
            price="29.99",
            stock=1
        )
        
        response = self.client.get(reverse('catalog:product_list'))
        content = response.content.decode()
        
        # Check that script tags are escaped
        self.assertNotIn('<script>alert("XSS")</script>', content)
        self.assertNotIn('<img src="x" onerror="alert(1)">', content)
        
        # Check that escaped versions are present
        self.assertIn('&lt;script&gt;', content)
        self.assertIn('&lt;img', content)

    def test_database_storage_sanitization(self):
        """Test that data is properly sanitized before database storage."""
        malicious_inputs = [
            '<script>alert("XSS")</script>',
            '"><script>alert("XSS")</script>',
            "'; DROP TABLE products; --",
            '\x00\x01\x02',  # Null bytes
        ]
        
        for malicious_input in malicious_inputs:
            product = Product.objects.create(
                sku=f"SANITIZE-{hash(malicious_input)}",
                name=malicious_input,
                description=malicious_input,
                price="19.99",
                stock=1
            )
            
            # Data should be stored as-is (Django ORM handles sanitization)
            # but should be escaped when rendered
            self.assertEqual(product.name, malicious_input)
            self.assertEqual(product.description, malicious_input)

    def test_json_response_sanitization(self):
        """Test that JSON responses are properly sanitized."""
        self.client.login(username="testuser", password="secure_password123")
        
        # Create product with special characters
        special_product = Product.objects.create(
            sku="SPECIAL-001",
            name='Product with "quotes" and \'apostrophes\'',
            price="15.99",
            stock=1
        )
        
        response = self.client.post(
            reverse('orders:create'),
            json.dumps({'sku': 'SPECIAL-001', 'qty': 1}),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 201)
        
        # Verify JSON is properly formatted
        response_data = json.loads(response.content)
        self.assertIsInstance(response_data, dict)
        self.assertIn('id', response_data)
        self.assertIn('total', response_data) 