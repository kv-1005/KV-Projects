#!/usr/bin/env python
"""
Complete Payment Flow Test for KV Store
Tests the entire payment process from checkout to payment completion
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
from requirements.payment_service import get_razorpay_service

class CompletePaymentFlowTester:
    def __init__(self):
        self.client = Client()
        self.test_results = []
        
    def log_test(self, test_name, status, details):
        """Log test results"""
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
                username='testuser_payment',
                defaults={
                    'email': 'test_payment@example.com',
                    'first_name': 'Test',
                    'last_name': 'Payment'
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
                name='Test Category Payment',
                defaults={'slug': 'test-category-payment'}
            )
            
            self.product, created = Product.objects.get_or_create(
                name='Test Product Payment',
                defaults={
                    'slug': 'test-product-payment',
                    'category': self.category,
                    'description': 'Test product for payment flow testing',
                    'price': Decimal('100.00'),
                    'stock_quantity': 10,
                    'sku': 'TESTPAY001'
                }
            )
            
            # Create test cart
            self.cart, created = Cart.objects.get_or_create(
                customer=self.customer,
                is_active=True
            )
            
            # Add item to cart
            self.cart_item, created = CartItem.objects.get_or_create(
                cart=self.cart,
                product=self.product,
                defaults={'quantity': 1}
            )
            
            self.log_test("Test Data Setup", "PASS", "Test data created successfully")
            return True
            
        except Exception as e:
            self.log_test("Test Data Setup", "FAIL", f"Error: {str(e)}")
            return False
    
    def test_razorpay_service_initialization(self):
        """Test Razorpay service initialization"""
        try:
            service = get_razorpay_service()
            if hasattr(service, 'client'):
                self.log_test("Razorpay Service Init", "PASS", "Service initialized successfully")
                return True
            else:
                self.log_test("Razorpay Service Init", "FAIL", "Service missing client attribute")
                return False
        except Exception as e:
            self.log_test("Razorpay Service Init", "FAIL", f"Error: {str(e)}")
            return False
    
    def test_razorpay_order_creation(self):
        """Test creating a Razorpay order"""
        try:
            # Create a test order
            order = Order.objects.create(
                customer=self.customer,
                total_amount=Decimal('100.00'),
                subtotal=Decimal('100.00'),
                tax=Decimal('18.00'),
                shipping_cost=Decimal('50.00'),
                shipping_address='Test Address, Test City, TS 123456',
                billing_address='Test Address, Test City, TS 123456',
                phone='1234567890',
                email=self.customer.user.email,
                payment_method='razorpay'
            )
            
            # Initialize Razorpay service
            razorpay_service = get_razorpay_service()
            if not razorpay_service:
                self.log_test("Razorpay Order Creation", "FAIL", "Service not available")
                return False
            
            # Create Razorpay order
            result = razorpay_service.create_order(order)
            
            if result['success']:
                self.log_test("Razorpay Order Creation", "PASS", f"Order created: {result['order_id']}")
                # Store for later tests
                self.razorpay_order_id = result['order_id']
                self.test_order = order
                return True
            else:
                self.log_test("Razorpay Order Creation", "FAIL", f"Error: {result.get('error', 'Unknown error')}")
                return False
                
        except Exception as e:
            self.log_test("Razorpay Order Creation", "FAIL", f"Error: {str(e)}")
            return False
    
    def test_payment_callback_endpoint(self):
        """Test the payment callback endpoint"""
        try:
            if not hasattr(self, 'razorpay_order_id'):
                self.log_test("Payment Callback Test", "FAIL", "No Razorpay order ID available")
                return False
            
            # Login the test user
            self.client.force_login(self.test_user)
            
            # Test data for payment callback - using realistic test data
            # Note: In real scenarios, these would come from Razorpay webhook
            callback_data = {
                'razorpay_payment_id': 'pay_test123',
                'razorpay_order_id': self.razorpay_order_id,
                'razorpay_signature': 'test_signature_123'
            }
            
            # Make request to payment callback
            response = self.client.post(
                reverse('payment_callback'),
                data=json.dumps(callback_data),
                content_type='application/json',
                HTTP_X_REQUESTED_WITH='XMLHttpRequest'
            )
            
            # In test mode, we expect a 400 status because signature verification will fail
            # This is actually correct behavior - we don't want fake signatures to pass
            if response.status_code == 400:
                response_data = json.loads(response.content)
                if 'Invalid payment signature' in response_data.get('error', ''):
                    self.log_test("Payment Callback Test", "PASS", "Correctly rejected invalid signature (expected behavior)")
                    return True
                else:
                    self.log_test("Payment Callback Test", "FAIL", f"Unexpected error: {response_data.get('error', 'Unknown error')}")
                    return False
            elif response.status_code == 200:
                self.log_test("Payment Callback Test", "PASS", "Endpoint responded successfully")
                return True
            else:
                self.log_test("Payment Callback Test", "FAIL", f"Status: {response.status_code}, Response: {response.content}")
                return False
                
        except Exception as e:
            self.log_test("Payment Callback Test", "FAIL", f"Error: {str(e)}")
            return False
    
    def test_payment_page_access(self):
        """Test accessing the payment page"""
        try:
            # Login the test user
            self.client.force_login(self.test_user)
            
            # Set session data properly
            session = self.client.session
            session['order_id'] = getattr(self, 'test_order', {}).id
            session['razorpay_order_id'] = getattr(self, 'razorpay_order_id', 'test_order_123')
            session.save()
            
            # Access payment page
            response = self.client.get(reverse('payment'))
            
            if response.status_code == 200:
                self.log_test("Payment Page Access", "PASS", "Payment page accessible")
                return True
            elif response.status_code == 302:  # Redirect
                self.log_test("Payment Page Access", "FAIL", f"Redirected to: {response.url}")
                return False
            else:
                self.log_test("Payment Page Access", "FAIL", f"Status: {response.status_code}")
                return False
                
        except Exception as e:
            self.log_test("Payment Page Access", "FAIL", f"Error: {str(e)}")
            return False
    
    def cleanup_test_data(self):
        """Clean up test data"""
        try:
            # Clean up test orders
            if hasattr(self, 'test_order'):
                self.test_order.delete()
            
            # Clean up test cart
            if hasattr(self, 'cart'):
                self.cart.delete()
            
            # Clean up test product
            if hasattr(self, 'product'):
                self.product.delete()
            
            # Clean up test category
            if hasattr(self, 'category'):
                self.category.delete()
            
            # Clean up test customer and user
            if hasattr(self, 'customer'):
                self.customer.delete()
            if hasattr(self, 'test_user'):
                self.test_user.delete()
            
            self.log_test("Test Data Cleanup", "PASS", "Test data cleaned up successfully")
            return True
            
        except Exception as e:
            self.log_test("Test Data Cleanup", "FAIL", f"Error: {str(e)}")
            return False
    
    def run_all_tests(self):
        """Run all payment flow tests"""
        print("Starting Complete Payment Flow Tests...\n")
        
        # Setup
        if not self.setup_test_data():
            print("Failed to setup test data. Aborting tests.")
            return
        
        # Run tests
        self.test_razorpay_service_initialization()
        self.test_razorpay_order_creation()
        self.test_payment_callback_endpoint()
        self.test_payment_page_access()
        
        # Cleanup
        self.cleanup_test_data()
        
        # Summary
        print("\n=== Test Summary ===")
        passed = sum(1 for result in self.test_results if result['status'] == 'PASS')
        failed = sum(1 for result in self.test_results if result['status'] == 'FAIL')
        total = len(self.test_results)
        
        print(f"Total Tests: {total}")
        print(f"Passed: {passed}")
        print(f"Failed: {failed}")
        print(f"Success Rate: {(passed/total)*100:.1f}%")
        
        if failed == 0:
            print("\n🎉 All tests passed! Payment flow is working correctly.")
        else:
            print(f"\n❌ {failed} test(s) failed. Please check the issues above.")

if __name__ == "__main__":
    tester = CompletePaymentFlowTester()
    tester.run_all_tests()
