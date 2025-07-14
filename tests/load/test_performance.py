"""Load and performance tests for the e-commerce application."""

import concurrent.futures
import json
import random
import time
from datetime import datetime

import pytest
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.db import transaction
from django.test import TestCase, TransactionTestCase, Client
from django.urls import reverse

from devops_pipeline.apps.catalog.models import Product
from devops_pipeline.apps.orders.models import Order

User = get_user_model()


class DatabasePerformanceTests(TransactionTestCase):
    """Test database performance under load."""

    def setUp(self):
        """Set up test data."""
        self.client = Client()
        
        # Create test users
        self.users = []
        for i in range(10):
            user = User.objects.create_user(
                username=f"loaduser{i}",
                password="test_password123",
                email=f"loaduser{i}@example.com"
            )
            self.users.append(user)
        
        # Create test products
        self.products = []
        for i in range(50):
            product = Product.objects.create(
                sku=f"LOAD-{i:03d}",
                name=f"Load Test Product {i}",
                description=f"Description for product {i}",
                price=f"{random.uniform(10, 100):.2f}",
                stock=random.randint(5, 100)
            )
            self.products.append(product)

    def test_product_list_query_performance(self):
        """Test product list query performance."""
        start_time = time.time()
        
        # Make multiple requests to product list
        for _ in range(20):
            response = self.client.get(reverse('catalog:product_list'))
            self.assertEqual(response.status_code, 200)
        
        end_time = time.time()
        avg_response_time = (end_time - start_time) / 20
        
        # Should complete within reasonable time (adjust threshold as needed)
        self.assertLess(avg_response_time, 0.5, 
                       f"Average response time {avg_response_time:.3f}s too slow")

    def test_concurrent_order_creation(self):
        """Test concurrent order creation performance."""
        def create_order(user_id, product_sku):
            """Create an order for testing."""
            user = self.users[user_id % len(self.users)]
            client = Client()
            client.force_login(user)
            
            start_time = time.time()
            response = client.post(
                reverse('orders:create'),
                json.dumps({'sku': product_sku, 'qty': random.randint(1, 5)}),
                content_type='application/json'
            )
            end_time = time.time()
            
            return {
                'status_code': response.status_code,
                'response_time': end_time - start_time,
                'user_id': user_id,
                'product_sku': product_sku
            }

        # Run concurrent order creation
        results = []
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            futures = []
            for i in range(25):
                product_sku = random.choice(self.products).sku
                future = executor.submit(create_order, i, product_sku)
                futures.append(future)
            
            for future in concurrent.futures.as_completed(futures):
                results.append(future.result())

        # Analyze results
        successful_orders = [r for r in results if r['status_code'] == 201]
        failed_orders = [r for r in results if r['status_code'] != 201]
        
        success_rate = len(successful_orders) / len(results)
        avg_response_time = sum(r['response_time'] for r in successful_orders) / len(successful_orders)
        
        # Assertions
        self.assertGreater(success_rate, 0.9, f"Success rate {success_rate:.2%} too low")
        self.assertLess(avg_response_time, 2.0, 
                       f"Average response time {avg_response_time:.3f}s too slow")
        
        print(f"Concurrent orders: {len(results)} total, "
              f"{len(successful_orders)} successful ({success_rate:.2%}), "
              f"avg response: {avg_response_time:.3f}s")

    def test_database_connection_pooling(self):
        """Test database connection handling under load."""
        def make_database_request():
            """Make a request that hits the database."""
            client = Client()
            user = random.choice(self.users)
            client.force_login(user)
            
            response = client.get(reverse('orders:list'))
            return response.status_code == 200

        # Make many concurrent database requests
        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(make_database_request) for _ in range(50)]
            results = [future.result() for future in concurrent.futures.as_completed(futures)]

        success_rate = sum(results) / len(results)
        self.assertGreater(success_rate, 0.95, 
                          f"Database connection success rate {success_rate:.2%} too low")

    def test_large_dataset_performance(self):
        """Test performance with larger datasets."""
        # Create additional products
        large_products = []
        for i in range(500):
            product = Product.objects.create(
                sku=f"LARGE-{i:04d}",
                name=f"Large Dataset Product {i}",
                price=f"{random.uniform(5, 200):.2f}",
                stock=random.randint(1, 50)
            )
            large_products.append(product)

        start_time = time.time()
        response = self.client.get(reverse('catalog:product_list'))
        end_time = time.time()
        
        self.assertEqual(response.status_code, 200)
        response_time = end_time - start_time
        
        # Should handle large dataset efficiently
        self.assertLess(response_time, 2.0, 
                       f"Large dataset response time {response_time:.3f}s too slow")
        
        # Cleanup
        for product in large_products:
            product.delete()


class CachePerformanceTests(TransactionTestCase):
    """Test Redis cache performance."""

    def setUp(self):
        """Set up test data."""
        self.client = Client()
        self.user = User.objects.create_user(
            username="cacheuser",
            password="test_password123"
        )
        self.product = Product.objects.create(
            sku="CACHE-001",
            name="Cache Test Product",
            price="25.99",
            stock=10
        )
        cache.clear()

    def test_cache_write_performance(self):
        """Test cache write performance."""
        start_time = time.time()
        
        # Write many cache entries
        for i in range(100):
            cache.set(f"test_key_{i}", f"test_value_{i}", 3600)
        
        end_time = time.time()
        write_time = end_time - start_time
        
        # Should complete cache writes quickly
        self.assertLess(write_time, 1.0, 
                       f"Cache write time {write_time:.3f}s too slow")

    def test_cache_read_performance(self):
        """Test cache read performance."""
        # Pre-populate cache
        for i in range(100):
            cache.set(f"read_test_{i}", f"value_{i}", 3600)
        
        start_time = time.time()
        
        # Read from cache
        for i in range(100):
            value = cache.get(f"read_test_{i}")
            self.assertEqual(value, f"value_{i}")
        
        end_time = time.time()
        read_time = end_time - start_time
        
        # Should read from cache quickly
        self.assertLess(read_time, 0.5, 
                       f"Cache read time {read_time:.3f}s too slow")

    def test_order_cache_under_load(self):
        """Test order caching under load."""
        self.client.force_login(self.user)
        
        # Create multiple orders to test caching
        order_times = []
        for i in range(20):
            start_time = time.time()
            response = self.client.post(
                reverse('orders:create'),
                json.dumps({'sku': 'CACHE-001', 'qty': 1}),
                content_type='application/json'
            )
            end_time = time.time()
            
            self.assertEqual(response.status_code, 201)
            order_times.append(end_time - start_time)
            
            # Verify cache entry was created
            order_data = json.loads(response.content)
            cached_total = cache.get(f"order:{order_data['id']}:total")
            self.assertIsNotNone(cached_total)

        avg_order_time = sum(order_times) / len(order_times)
        self.assertLess(avg_order_time, 1.0, 
                       f"Average order creation time {avg_order_time:.3f}s too slow")

    def test_cache_memory_usage(self):
        """Test cache memory usage patterns."""
        # Store large amount of data in cache
        large_data = "x" * 1024  # 1KB of data
        
        start_memory = self._get_cache_info()
        
        # Cache many large entries
        for i in range(100):
            cache.set(f"memory_test_{i}", large_data, 3600)
        
        end_memory = self._get_cache_info()
        
        # Verify data was cached
        test_value = cache.get("memory_test_50")
        self.assertEqual(test_value, large_data)
        
        # Clean up
        for i in range(100):
            cache.delete(f"memory_test_{i}")

    def _get_cache_info(self):
        """Get cache memory info (implementation depends on cache backend)."""
        try:
            # This would work with Redis
            from django.core.cache.backends.redis import RedisCache
            if isinstance(cache, RedisCache):
                return cache._cache.get_client().info('memory')
        except:
            pass
        return {}


class APILoadTests(TransactionTestCase):
    """Test API endpoints under load."""

    def setUp(self):
        """Set up test data."""
        self.client = Client()
        
        # Create test users
        self.test_users = []
        for i in range(20):
            user = User.objects.create_user(
                username=f"apiuser{i}",
                password="api_password123"
            )
            self.test_users.append(user)
        
        # Create test products
        self.test_products = []
        for i in range(30):
            product = Product.objects.create(
                sku=f"API-{i:03d}",
                name=f"API Test Product {i}",
                price=f"{random.uniform(15, 75):.2f}",
                stock=random.randint(10, 100)
            )
            self.test_products.append(product)

    def test_api_throughput(self):
        """Test API throughput under load."""
        def make_api_request(user_index):
            """Make API request for testing."""
            client = Client()
            user = self.test_users[user_index % len(self.test_users)]
            client.force_login(user)
            
            product = random.choice(self.test_products)
            
            start_time = time.time()
            response = client.post(
                reverse('orders:create'),
                json.dumps({'sku': product.sku, 'qty': random.randint(1, 3)}),
                content_type='application/json'
            )
            end_time = time.time()
            
            return {
                'response_time': end_time - start_time,
                'status_code': response.status_code,
                'timestamp': datetime.now()
            }

        # Execute load test
        results = []
        start_test = time.time()
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=8) as executor:
            futures = [executor.submit(make_api_request, i) for i in range(100)]
            results = [future.result() for future in concurrent.futures.as_completed(futures)]
        
        end_test = time.time()
        total_test_time = end_test - start_test
        
        # Analyze results
        successful_requests = [r for r in results if r['status_code'] == 201]
        failed_requests = [r for r in results if r['status_code'] != 201]
        
        success_rate = len(successful_requests) / len(results)
        avg_response_time = sum(r['response_time'] for r in successful_requests) / len(successful_requests)
        throughput = len(results) / total_test_time
        
        # Performance assertions
        self.assertGreater(success_rate, 0.95, f"Success rate {success_rate:.2%} too low")
        self.assertLess(avg_response_time, 1.5, 
                       f"Average response time {avg_response_time:.3f}s too slow")
        self.assertGreater(throughput, 10, f"Throughput {throughput:.1f} req/s too low")
        
        print(f"API Load Test Results:")
        print(f"  Total requests: {len(results)}")
        print(f"  Success rate: {success_rate:.2%}")
        print(f"  Average response time: {avg_response_time:.3f}s")
        print(f"  Throughput: {throughput:.1f} requests/second")

    def test_sustained_load(self):
        """Test sustained load over longer period."""
        def sustained_request_worker():
            """Worker for sustained load testing."""
            client = Client()
            user = random.choice(self.test_users)
            client.force_login(user)
            
            results = []
            test_duration = 30  # 30 seconds
            start_time = time.time()
            
            while time.time() - start_time < test_duration:
                product = random.choice(self.test_products)
                
                request_start = time.time()
                response = client.post(
                    reverse('orders:create'),
                    json.dumps({'sku': product.sku, 'qty': 1}),
                    content_type='application/json'
                )
                request_end = time.time()
                
                results.append({
                    'response_time': request_end - request_start,
                    'status_code': response.status_code,
                    'timestamp': request_end
                })
                
                # Small delay between requests
                time.sleep(0.1)
            
            return results

        # Run sustained load test with multiple workers
        all_results = []
        with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
            futures = [executor.submit(sustained_request_worker) for _ in range(3)]
            for future in concurrent.futures.as_completed(futures):
                all_results.extend(future.result())

        # Analyze sustained load results
        if all_results:
            successful_requests = [r for r in all_results if r['status_code'] == 201]
            success_rate = len(successful_requests) / len(all_results)
            avg_response_time = sum(r['response_time'] for r in successful_requests) / len(successful_requests)
            
            self.assertGreater(success_rate, 0.90, 
                              f"Sustained load success rate {success_rate:.2%} too low")
            self.assertLess(avg_response_time, 2.0, 
                           f"Sustained load avg response time {avg_response_time:.3f}s too slow")

    def test_memory_leak_detection(self):
        """Test for potential memory leaks during load."""
        import psutil
        import os
        
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss
        
        # Make many requests to detect memory leaks
        client = Client()
        user = self.test_users[0]
        client.force_login(user)
        
        for i in range(100):
            product = random.choice(self.test_products)
            response = client.post(
                reverse('orders:create'),
                json.dumps({'sku': product.sku, 'qty': 1}),
                content_type='application/json'
            )
            
            # Force garbage collection periodically
            if i % 20 == 0:
                import gc
                gc.collect()
        
        final_memory = process.memory_info().rss
        memory_increase = final_memory - initial_memory
        memory_increase_mb = memory_increase / (1024 * 1024)
        
        # Memory increase should be reasonable (adjust threshold as needed)
        self.assertLess(memory_increase_mb, 50, 
                       f"Memory increase {memory_increase_mb:.1f}MB too high - possible leak")


class StressTests(TransactionTestCase):
    """Stress tests to find breaking points."""

    def setUp(self):
        """Set up stress test data."""
        self.client = Client()
        self.user = User.objects.create_user(
            username="stressuser",
            password="stress_password123"
        )
        self.product = Product.objects.create(
            sku="STRESS-001",
            name="Stress Test Product",
            price="99.99",
            stock=1000
        )

    def test_rapid_fire_requests(self):
        """Test rapid fire API requests."""
        self.client.force_login(self.user)
        
        start_time = time.time()
        responses = []
        
        # Make rapid requests without delays
        for i in range(50):
            response = self.client.post(
                reverse('orders:create'),
                json.dumps({'sku': 'STRESS-001', 'qty': 1}),
                content_type='application/json'
            )
            responses.append(response.status_code)
        
        end_time = time.time()
        total_time = end_time - start_time
        
        successful_responses = [r for r in responses if r == 201]
        success_rate = len(successful_responses) / len(responses)
        
        # Should handle rapid requests gracefully
        self.assertGreater(success_rate, 0.8, 
                          f"Rapid fire success rate {success_rate:.2%} too low")
        
        print(f"Rapid fire test: {len(responses)} requests in {total_time:.2f}s, "
              f"success rate: {success_rate:.2%}")

    def test_large_order_quantities(self):
        """Test handling of large order quantities."""
        self.client.force_login(self.user)
        
        large_quantities = [100, 500, 999, 1000]
        
        for qty in large_quantities:
            response = self.client.post(
                reverse('orders:create'),
                json.dumps({'sku': 'STRESS-001', 'qty': qty}),
                content_type='application/json'
            )
            
            # Should handle large quantities appropriately
            self.assertIn(response.status_code, [201, 400, 404])
            
            if response.status_code == 201:
                order_data = json.loads(response.content)
                order = Order.objects.get(id=order_data['id'])
                expected_total = self.product.price * qty
                self.assertEqual(order.total, expected_total) 