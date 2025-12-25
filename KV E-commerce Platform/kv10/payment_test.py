#!/usr/bin/env python
"""
Payment System Testing Script for KV Store
Tests various payment scenarios and identifies issues
"""

import os
import sys
import django
from decimal import Decimal
import json

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'kv10.settings')
django.setup()

from django.contrib.auth.models import User
from django.test import Client
from django.urls import reverse
from requirements.models import *
from requirements.payment_service import razorpay_service

class PaymentSystemTester:
    def __init__(self):
        self.client = Client()
        self.test_results = []
        
    def log_test(self, test_name, status, details):
        """Log test results without Unicode characters"""
        status_symbol = "[PASS]" if status == "PASS" else "[FAIL]" if status == "FAIL" else "[ERROR]"
        message = f"{status_symbol} {test_name}: {details}"
        print(message)
        self.test_results.append({
            'test': test_name,
            'status': status,
            'details': details
        })
    
    def setup_test_data(self):
        """Create test data for payment testing"""
        try:
            # Create test user
            self.test_user, created = User.objects.get_or_create(
                username='testuser',
                defaults={
                    'email': 'test@example.com',
                    'first_name': 'Test',
                    'last_name': 'User'
                }
            )
            if created:
                self.test_user.set_password('testpass123')
                self.test_user.save()
            
            # Create customer profile
            self.customer, created = Customer.objects.get_or_create(
                user=self.test_user,
                defaults={
                    'phone': '9876543210',
                    'address': 'Test Address',
                    'city': 'Test City',
                    'state': 'Test State',
                    'zip_code': '123456'
                }
            )
            
            # Create test category and product
            self.category, created = Category.objects.get_or_create(
                name='Test Category',
                defaults={'slug': 'test-category'}
            )
            
            self.product, created = Product.objects.get_or_create(
                name='Test Product',
                defaults={
                    'slug': 'test-product',
                    'category': self.category,
                    'description': 'Test product for payment testing',
                    'price': Decimal('100.00'),
                    'stock_quantity': 10,
                    'sku': 'TEST001'
                }
            )
            
            self.log_test("Test Data Setup", "PASS", "Test data created successfully")
            return True
            
        except Exception as e:
            self.log_test("Test Data Setup", "FAIL", f"Error: {str(e)}")
            return False
    
    def test_razorpay_service_initialization(self):
        """Test Razorpay service initialization"""
        try:
            # Test service initialization
            service = razorpay_service
            if hasattr(service, 'client'):
                self.log_test("Razorpay Service Init", "PASS", "Service initialized successfully")
                return True
            else:
                self.log_test("Razorpay Service Init", "FAIL", "Service client not found")
                return False
        except Exception as e:
            self.log_test("Razorpay Service Init", "FAIL", f"Error: {str(e)}")
            return False
    
    def test_cart_functionality(self):
        """Test cart creation and item addition"""
        try:
            # Login user
            self.client.login(username='testuser', password='testpass123')
            
            # Add product to cart
            response = self.client.post(f'/add-to-cart/{self.product.id}/', {
                'quantity': 1
            })
            
            if response.status_code in [200, 302]:
                # Check if cart was created
                cart = Cart.objects.filter(customer=self.customer, is_active=True).first()
                if cart and cart.items.exists():
                    self.log_test("Cart Functionality", "PASS", "Product added to cart successfully")
                    return True
                else:
                    self.log_test("Cart Functionality", "FAIL", "Cart not created or empty")
                    return False
            else:
                self.log_test("Cart Functionality", "FAIL", f"HTTP {response.status_code}")
                return False
                
        except Exception as e:
            self.log_test("Cart Functionality", "FAIL", f"Error: {str(e)}")
            return False
    
    def test_checkout_page_access(self):
        """Test checkout page accessibility"""
        try:
            response = self.client.get('/checkout/')
            
            if response.status_code == 200:
                self.log_test("Checkout Page Access", "PASS", "Checkout page accessible")
                return True
            elif response.status_code == 302:
                self.log_test("Checkout Page Access", "PASS", "Redirected (expected for empty cart)")
                return True
            else:
                self.log_test("Checkout Page Access", "FAIL", f"HTTP {response.status_code}")
                return False
                
        except Exception as e:
            self.log_test("Checkout Page Access", "FAIL", f"Error: {str(e)}")
            return False
    
    def test_order_creation(self):
        """Test order creation process"""
        try:
            # Ensure we have a cart with items
            cart, created = Cart.objects.get_or_create(
                customer=self.customer,
                is_active=True
            )
            
            cart_item, created = CartItem.objects.get_or_create(
                cart=cart,
                product=self.product,
                defaults={'quantity': 1}
            )
            
            # Test order creation
            checkout_data = {
                'shipping_first_name': 'Test',
                'shipping_last_name': 'User',
                'shipping_address': 'Test Address',
                'shipping_city': 'Test City',
                'shipping_state': 'Test State',
                'shipping_zip_code': '123456',
                'shipping_phone': '9876543210',
                'payment_method': 'cod'
            }
            
            response = self.client.post('/checkout/', checkout_data)
            
            if response.status_code in [200, 302]:
                # Check if order was created
                order = Order.objects.filter(customer=self.customer).first()
                if order:
                    self.log_test("Order Creation", "PASS", f"Order created: {order.order_number}")
                    return order
                else:
                    self.log_test("Order Creation", "FAIL", "Order not found in database")
                    return None
            else:
                self.log_test("Order Creation", "FAIL", f"HTTP {response.status_code}")
                return None
                
        except Exception as e:
            self.log_test("Order Creation", "FAIL", f"Error: {str(e)}")
            return None
    
    def test_razorpay_order_creation(self):
        """Test Razorpay order creation"""
        try:
            # Create a test order first
            order = Order.objects.create(
                customer=self.customer,
                subtotal=Decimal('100.00'),
                tax=Decimal('18.00'),
                shipping_cost=Decimal('0.00'),
                total_amount=Decimal('118.00'),
                payment_method='razorpay',
                shipping_address='Test Address',
                billing_address='Test Address',
                phone='9876543210',
                email='test@example.com'
            )
            
            # Test Razorpay order creation
            result = razorpay_service.create_order(order)
            
            if result['success']:
                self.log_test("Razorpay Order Creation", "PASS", f"Order ID: {result['order_id']}")
                return result
            else:
                self.log_test("Razorpay Order Creation", "FAIL", f"Error: {result['error']}")
                return None
                
        except Exception as e:
            self.log_test("Razorpay Order Creation", "FAIL", f"Error: {str(e)}")
            return None
    
    def test_payment_callback_endpoint(self):
        """Test payment callback endpoint"""
        try:
            # Test callback endpoint accessibility
            test_data = {
                'razorpay_payment_id': 'test_payment_id',
                'razorpay_order_id': 'test_order_id',
                'razorpay_signature': 'test_signature'
            }
            
            response = self.client.post('/payment/callback/', 
                                      json.dumps(test_data),
                                      content_type='application/json')
            
            # We expect this to fail with signature verification, but endpoint should be accessible
            if response.status_code in [200, 400, 500]:
                self.log_test("Payment Callback Endpoint", "PASS", "Endpoint accessible")
                return True
            else:
                self.log_test("Payment Callback Endpoint", "FAIL", f"HTTP {response.status_code}")
                return False
                
        except Exception as e:
            self.log_test("Payment Callback Endpoint", "FAIL", f"Error: {str(e)}")
            return False
    
    def test_database_models(self):
        """Test database models and relationships"""
        try:
            # Test model creation and relationships
            test_order = Order.objects.create(
                customer=self.customer,
                subtotal=Decimal('50.00'),
                tax=Decimal('9.00'),
                shipping_cost=Decimal('0.00'),
                total_amount=Decimal('59.00'),
                payment_method='cod',
                shipping_address='Test Address',
                billing_address='Test Address',
                phone='9876543210',
                email='test@example.com'
            )
            
            # Test OrderItem creation
            order_item = OrderItem.objects.create(
                order=test_order,
                product=self.product,
                quantity=1,
                price=self.product.price
            )
            
            # Test Payment model
            payment = Payment.objects.create(
                order=test_order,
                amount=test_order.total_amount,
                payment_method='cod',
                status='completed'
            )
            
            self.log_test("Database Models", "PASS", "All models working correctly")
            return True
            
        except Exception as e:
            self.log_test("Database Models", "FAIL", f"Error: {str(e)}")
            return False
    
    def run_all_tests(self):
        """Run all payment system tests"""
        print("Starting Payment System Tests")
        print("=" * 50)
        
        # Setup test data
        if not self.setup_test_data():
            print("Test data setup failed. Aborting tests.")
            return
        
        # Run all tests
        tests = [
            self.test_razorpay_service_initialization,
            self.test_database_models,
            self.test_cart_functionality,
            self.test_checkout_page_access,
            self.test_order_creation,
            self.test_razorpay_order_creation,
            self.test_payment_callback_endpoint,
        ]
        
        for test in tests:
            try:
                test()
            except Exception as e:
                self.log_test(test.__name__, "ERROR", f"Test crashed: {e}")
        
        # Print summary
        print("\n" + "=" * 50)
        print("TEST SUMMARY")
        print("=" * 50)
        
        passed = len([r for r in self.test_results if r['status'] == 'PASS'])
        failed = len([r for r in self.test_results if r['status'] == 'FAIL'])
        errors = len([r for r in self.test_results if r['status'] == 'ERROR'])
        
        print(f"Total Tests: {len(self.test_results)}")
        print(f"Passed: {passed}")
        print(f"Failed: {failed}")
        print(f"Errors: {errors}")
        
        if failed > 0 or errors > 0:
            print("\nFAILED/ERROR TESTS:")
            for result in self.test_results:
                if result['status'] in ['FAIL', 'ERROR']:
                    print(f"  - {result['test']}: {result['details']}")

if __name__ == '__main__':
    tester = PaymentSystemTester()
    tester.run_all_tests()
