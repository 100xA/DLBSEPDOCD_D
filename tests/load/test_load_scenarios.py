"""Realistic load testing scenarios for e-commerce application."""

import concurrent.futures
import json
import random
import time
from datetime import datetime, timedelta

import pytest
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.test import TransactionTestCase, Client
from django.urls import reverse

from devops_pipeline.apps.catalog.models import Product
from devops_pipeline.apps.orders.models import Order

User = get_user_model()


class EcommerceLoadScenarios(TransactionTestCase):
    """Realistic e-commerce load testing scenarios."""

    def setUp(self):
        """Set up realistic test data."""
        # Create user base
        self.users = []
        for i in range(100):
            user = User.objects.create_user(
                username=f"customer{i:03d}",
                password="customer_password123",
                email=f"customer{i:03d}@example.com"
            )
            self.users.append(user)
        
        # Create product catalog
        self.products = []
        categories = ['Electronics', 'Clothing', 'Books', 'Home', 'Sports']
        
        for i in range(200):
            category = random.choice(categories)
            product = Product.objects.create(
                sku=f"{category[:3].upper()}-{i:04d}",
                name=f"{category} Product {i}",
                description=f"High quality {category.lower()} product with great features",
                price=f"{random.uniform(9.99, 299.99):.2f}",
                stock=random.randint(0, 500),
                is_active=random.choice([True, True, True, False])  # 75% active
            )
            self.products.append(product)
        
        # Create some existing orders for realistic data
        for _ in range(50):
            user = random.choice(self.users)
            product = random.choice(self.products)
            Order.objects.create(
                user=user,
                total=f"{random.uniform(20, 500):.2f}",
                status=random.choice(list(Order.Status.choices))[0]
            )

    def test_black_friday_scenario(self):
        """Simulate Black Friday traffic surge."""
        print("🛍️ Black Friday Load Test Scenario")
        
        def black_friday_customer_session(customer_id):
            """Simulate a customer's Black Friday shopping session."""
            client = Client()
            user = self.users[customer_id % len(self.users)]
            client.force_login(user)
            
            session_results = {
                'customer_id': customer_id,
                'page_views': 0,
                'orders_placed': 0,
                'total_response_time': 0,
                'errors': []
            }
            
            # Browse products (typical Black Friday behavior)
            for _ in range(random.randint(3, 8)):
                start_time = time.time()
                response = client.get(reverse('catalog:product_list'))
                end_time = time.time()
                
                session_results['page_views'] += 1
                session_results['total_response_time'] += (end_time - start_time)
                
                if response.status_code != 200:
                    session_results['errors'].append(f"Product list: {response.status_code}")
                
                # Small delay between page views
                time.sleep(random.uniform(0.1, 0.5))
            
            # Place 1-3 orders (high purchase intent on Black Friday)
            for _ in range(random.randint(1, 3)):
                product = random.choice([p for p in self.products if p.is_active and p.stock > 0])
                qty = random.randint(1, 5)
                
                start_time = time.time()
                response = client.post(
                    reverse('orders:create'),
                    json.dumps({'sku': product.sku, 'qty': qty}),
                    content_type='application/json'
                )
                end_time = time.time()
                
                session_results['total_response_time'] += (end_time - start_time)
                
                if response.status_code == 201:
                    session_results['orders_placed'] += 1
                else:
                    session_results['errors'].append(f"Order creation: {response.status_code}")
                
                # Quick succession of orders
                time.sleep(random.uniform(0.1, 0.3))
            
            return session_results

        # Simulate high concurrent traffic
        start_time = time.time()
        results = []
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=20) as executor:
            # Simulate 200 concurrent customers
            futures = [executor.submit(black_friday_customer_session, i) for i in range(200)]
            results = [future.result() for future in concurrent.futures.as_completed(futures)]
        
        end_time = time.time()
        total_test_time = end_time - start_time
        
        # Analyze Black Friday results
        total_page_views = sum(r['page_views'] for r in results)
        total_orders = sum(r['orders_placed'] for r in results)
        total_errors = sum(len(r['errors']) for r in results)
        avg_response_time = sum(r['total_response_time'] for r in results) / len(results)
        
        success_rate = (total_page_views + total_orders - total_errors) / (total_page_views + total_orders)
        
        print(f"Black Friday Results:")
        print(f"  🎯 200 concurrent customers in {total_test_time:.1f}s")
        print(f"  📄 {total_page_views} page views")
        print(f"  🛒 {total_orders} orders placed")
        print(f"  ❌ {total_errors} errors")
        print(f"  ✅ Success rate: {success_rate:.2%}")
        print(f"  ⏱️ Avg response time: {avg_response_time:.3f}s")
        
        # Assertions for Black Friday performance
        self.assertGreater(success_rate, 0.95, f"Black Friday success rate {success_rate:.2%} too low")
        self.assertLess(avg_response_time, 2.0, f"Black Friday response time {avg_response_time:.3f}s too slow")
        self.assertGreater(total_orders, 100, "Not enough orders placed during Black Friday")

    def test_normal_browsing_scenario(self):
        """Simulate normal daily browsing patterns."""
        print("👥 Normal Browsing Pattern Test")
        
        def normal_customer_session(customer_id):
            """Simulate normal customer browsing behavior."""
            client = Client()
            
            # 70% of visitors are logged in
            if random.random() < 0.7:
                user = self.users[customer_id % len(self.users)]
                client.force_login(user)
                is_logged_in = True
            else:
                is_logged_in = False
            
            session_metrics = {
                'page_views': 0,
                'orders': 0,
                'response_times': [],
                'logged_in': is_logged_in
            }
            
            # Browse products (normal browsing behavior)
            browse_count = random.randint(1, 5)
            for _ in range(browse_count):
                start_time = time.time()
                response = client.get(reverse('catalog:product_list'))
                end_time = time.time()
                
                session_metrics['page_views'] += 1
                session_metrics['response_times'].append(end_time - start_time)
                
                # Realistic browsing delays
                time.sleep(random.uniform(2, 10))
            
            # Only 20% of visitors make a purchase
            if is_logged_in and random.random() < 0.2:
                product = random.choice([p for p in self.products if p.is_active and p.stock > 0])
                
                start_time = time.time()
                response = client.post(
                    reverse('orders:create'),
                    json.dumps({'sku': product.sku, 'qty': 1}),
                    content_type='application/json'
                )
                end_time = time.time()
                
                session_metrics['response_times'].append(end_time - start_time)
                
                if response.status_code == 201:
                    session_metrics['orders'] = 1
            
            return session_metrics

        # Simulate normal traffic over time
        results = []
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            # 100 customers with normal browsing patterns
            futures = [executor.submit(normal_customer_session, i) for i in range(100)]
            results = [future.result() for future in concurrent.futures.as_completed(futures)]
        
        # Analyze normal browsing results
        total_page_views = sum(r['page_views'] for r in results)
        total_orders = sum(r['orders'] for r in results)
        logged_in_users = sum(1 for r in results if r['logged_in'])
        
        all_response_times = []
        for r in results:
            all_response_times.extend(r['response_times'])
        
        avg_response_time = sum(all_response_times) / len(all_response_times)
        conversion_rate = total_orders / logged_in_users if logged_in_users > 0 else 0
        
        print(f"Normal Browsing Results:")
        print(f"  👤 {len(results)} visitors")
        print(f"  🔐 {logged_in_users} logged in ({logged_in_users/len(results):.1%})")
        print(f"  📄 {total_page_views} page views")
        print(f"  🛒 {total_orders} orders")
        print(f"  💰 Conversion rate: {conversion_rate:.1%}")
        print(f"  ⏱️ Avg response time: {avg_response_time:.3f}s")
        
        # Normal browsing should have excellent performance
        self.assertLess(avg_response_time, 1.0, f"Normal browsing response time {avg_response_time:.3f}s too slow")
        self.assertGreater(conversion_rate, 0.1, f"Conversion rate {conversion_rate:.1%} too low")

    def test_mobile_app_api_scenario(self):
        """Simulate mobile app API usage patterns."""
        print("📱 Mobile App API Load Test")
        
        def mobile_api_session(session_id):
            """Simulate mobile app API usage."""
            client = Client()
            user = self.users[session_id % len(self.users)]
            client.force_login(user)
            
            api_metrics = {
                'api_calls': 0,
                'successful_calls': 0,
                'failed_calls': 0,
                'response_times': []
            }
            
            # Mobile apps make frequent API calls
            for _ in range(random.randint(10, 30)):
                api_metrics['api_calls'] += 1
                
                # Mix of different API operations
                operation = random.choice(['view_products', 'view_orders', 'create_order'])
                
                start_time = time.time()
                
                if operation == 'view_products':
                    response = client.get(reverse('catalog:product_list'))
                elif operation == 'view_orders':
                    response = client.get(reverse('orders:list'))
                else:  # create_order
                    product = random.choice([p for p in self.products if p.is_active and p.stock > 0])
                    response = client.post(
                        reverse('orders:create'),
                        json.dumps({'sku': product.sku, 'qty': 1}),
                        content_type='application/json'
                    )
                
                end_time = time.time()
                response_time = end_time - start_time
                api_metrics['response_times'].append(response_time)
                
                if response.status_code in [200, 201]:
                    api_metrics['successful_calls'] += 1
                else:
                    api_metrics['failed_calls'] += 1
                
                # Mobile apps have minimal delays between API calls
                time.sleep(random.uniform(0.1, 0.5))
            
            return api_metrics

        # Simulate mobile app load
        results = []
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=15) as executor:
            # 50 mobile app sessions
            futures = [executor.submit(mobile_api_session, i) for i in range(50)]
            results = [future.result() for future in concurrent.futures.as_completed(futures)]
        
        # Analyze mobile API results
        total_api_calls = sum(r['api_calls'] for r in results)
        total_successful = sum(r['successful_calls'] for r in results)
        total_failed = sum(r['failed_calls'] for r in results)
        
        all_response_times = []
        for r in results:
            all_response_times.extend(r['response_times'])
        
        avg_response_time = sum(all_response_times) / len(all_response_times)
        success_rate = total_successful / total_api_calls
        
        print(f"Mobile API Results:")
        print(f"  📱 {len(results)} mobile sessions")
        print(f"  🔗 {total_api_calls} API calls")
        print(f"  ✅ {total_successful} successful")
        print(f"  ❌ {total_failed} failed")
        print(f"  📊 Success rate: {success_rate:.2%}")
        print(f"  ⏱️ Avg response time: {avg_response_time:.3f}s")
        
        # Mobile APIs need to be very responsive
        self.assertGreater(success_rate, 0.98, f"Mobile API success rate {success_rate:.2%} too low")
        self.assertLess(avg_response_time, 0.5, f"Mobile API response time {avg_response_time:.3f}s too slow")

    def test_inventory_depletion_scenario(self):
        """Test behavior when popular products run out of stock."""
        print("📦 Inventory Depletion Scenario")
        
        # Create a popular product with limited stock
        popular_product = Product.objects.create(
            sku="POPULAR-001",
            name="Limited Edition Product",
            price="99.99",
            stock=20,  # Limited stock
            is_active=True
        )
        
        def compete_for_product(customer_id):
            """Customers competing for limited stock."""
            client = Client()
            user = self.users[customer_id % len(self.users)]
            client.force_login(user)
            
            attempt_metrics = {
                'customer_id': customer_id,
                'attempts': 0,
                'successful_orders': 0,
                'out_of_stock': 0,
                'errors': 0
            }
            
            # Each customer tries to order multiple items
            for _ in range(random.randint(1, 3)):
                attempt_metrics['attempts'] += 1
                
                response = client.post(
                    reverse('orders:create'),
                    json.dumps({'sku': 'POPULAR-001', 'qty': random.randint(1, 5)}),
                    content_type='application/json'
                )
                
                if response.status_code == 201:
                    attempt_metrics['successful_orders'] += 1
                elif response.status_code == 404:
                    attempt_metrics['out_of_stock'] += 1
                else:
                    attempt_metrics['errors'] += 1
                
                # Quick attempts to simulate competition
                time.sleep(random.uniform(0.05, 0.2))
            
            return attempt_metrics

        # Many customers competing for limited stock
        results = []
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=25) as executor:
            futures = [executor.submit(compete_for_product, i) for i in range(50)]
            results = [future.result() for future in concurrent.futures.as_completed(futures)]
        
        # Analyze inventory competition
        total_attempts = sum(r['attempts'] for r in results)
        total_successful = sum(r['successful_orders'] for r in results)
        total_out_of_stock = sum(r['out_of_stock'] for r in results)
        total_errors = sum(r['errors'] for r in results)
        
        # Check final stock level
        popular_product.refresh_from_db()
        remaining_stock = popular_product.stock
        
        print(f"Inventory Depletion Results:")
        print(f"  🎯 {len(results)} customers competed")
        print(f"  🔄 {total_attempts} order attempts")
        print(f"  ✅ {total_successful} successful orders")
        print(f"  📦 {total_out_of_stock} out-of-stock responses")
        print(f"  ❌ {total_errors} errors")
        print(f"  📊 Remaining stock: {remaining_stock}")
        
        # Verify inventory management works correctly
        self.assertGreaterEqual(remaining_stock, 0, "Stock should not go negative")
        self.assertLess(total_errors / total_attempts, 0.05, "Too many errors during stock competition")
        
        # Stock should be depleted or very low
        self.assertLess(remaining_stock, 5, "Stock should be mostly depleted")

    def test_cache_warming_scenario(self):
        """Test cache warming and cold cache performance."""
        print("🔥 Cache Warming Scenario")
        
        # Clear all caches to simulate cold start
        cache.clear()
        
        def cold_cache_request():
            """Make request with cold cache."""
            client = Client()
            start_time = time.time()
            response = client.get(reverse('catalog:product_list'))
            end_time = time.time()
            return {
                'response_time': end_time - start_time,
                'status_code': response.status_code,
                'cache_state': 'cold'
            }
        
        def warm_cache_request():
            """Make request with warm cache."""
            client = Client()
            start_time = time.time()
            response = client.get(reverse('catalog:product_list'))
            end_time = time.time()
            return {
                'response_time': end_time - start_time,
                'status_code': response.status_code,
                'cache_state': 'warm'
            }
        
        # Test cold cache performance
        cold_results = []
        for _ in range(5):
            cold_results.append(cold_cache_request())
            time.sleep(0.1)
        
        # Test warm cache performance
        warm_results = []
        for _ in range(20):
            warm_results.append(warm_cache_request())
        
        # Analyze cache performance
        cold_avg_time = sum(r['response_time'] for r in cold_results) / len(cold_results)
        warm_avg_time = sum(r['response_time'] for r in warm_results) / len(warm_results)
        
        cache_improvement = (cold_avg_time - warm_avg_time) / cold_avg_time
        
        print(f"Cache Performance Results:")
        print(f"  ❄️ Cold cache avg: {cold_avg_time:.3f}s")
        print(f"  🔥 Warm cache avg: {warm_avg_time:.3f}s")
        print(f"  📈 Improvement: {cache_improvement:.1%}")
        
        # Cache should provide meaningful improvement
        self.assertGreater(cache_improvement, 0.1, "Cache should provide at least 10% improvement")
        self.assertLess(warm_avg_time, 0.5, f"Warm cache response time {warm_avg_time:.3f}s too slow") 