#!/usr/bin/env python
"""
Real Checkout Flow Test
Simulates the actual checkout form submission and redirect
"""

import os
import sys
import django
from django.conf import settings

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'kv10.settings')
django.setup()

from django.contrib.auth.models import User
from django.test import Client
from django.urls import reverse
from requirements.models import *
from requirements.payment_service import get_razorpay_service
from decimal import Decimal

def test_real_checkout_flow():
    """Test the actual checkout form submission and redirect flow"""
    
    print("🚀 Real Checkout Flow Test")
    print("=" * 50)
    print()
    
    # Create test client
    client = Client()
    
    # Create test user
    user, created = User.objects.get_or_create(
        username='testuser_real',
        defaults={
            'email': 'test_real@example.com',
            'first_name': 'Test',
            'last_name': 'User'
        }
    )
    
    if created:
        user.set_password('testpass123')
        user.save()
    
    # Create test customer
    customer, created = Customer.objects.get_or_create(
        user=user,
        defaults={'phone': '1234567890'}
    )
    
    print(f"👤 Test user: {user.username}")
    print(f"📱 Customer ID: {customer.id}")
    print()
    
    # Login the user
    client.force_login(user)
    print("✅ User logged in")
    print()
    
    try:
        # Create test cart with items
        cart = Cart.objects.create(customer=customer, is_active=True)
        
        # Create test product and category
        category = Category.objects.create(name='Test Category')
        product = Product.objects.create(
            name='Test Product',
            description='Test Description',
            price=Decimal('50.00'),
            category=category,
            stock_quantity=10
        )
        
        # Add item to cart
        cart_item = CartItem.objects.create(
            cart=cart,
            product=product,
            quantity=2
        )
        
        print(f"🛒 Test cart created with {cart_item.quantity} items")
        print(f"   Product: {product.name} - ₹{product.price}")
        print(f"   Cart total: ₹{cart_item.total_price}")
        print()
        
        # Test checkout page access
        print("📍 Step 1: Testing checkout page access...")
        response = client.get(reverse('checkout'))
        
        if response.status_code == 200:
            print("✅ Checkout page accessible")
            
            # Check if Razorpay is configured
            if hasattr(response, 'context') and response.context:
                razorpay_configured = response.context.get('razorpay_configured', False)
                print(f"   Razorpay configured: {razorpay_configured}")
            else:
                print("   No context available")
        else:
            print(f"❌ Checkout page error: {response.status_code}")
            print(f"   Content: {response.content[:200]}...")
            return
        
        print()
        
        # Step 2: Submit checkout form with Razorpay
        print("📝 Step 2: Submitting checkout form with Razorpay...")
        
        # Prepare checkout form data
        checkout_data = {
            'shipping_first_name': 'Test',
            'shipping_last_name': 'User',
            'shipping_address': 'Test Address, Test City, TS 123456',
            'shipping_city': 'Test City',
            'shipping_state': 'Test State',
            'shipping_zip_code': '123456',
            'shipping_phone': '1234567890',
            'shipping_country': 'India',
            'payment_method': 'razorpay'
        }
        
        print(f"   Form data: {checkout_data}")
        
        # Submit checkout form
        response = client.post(reverse('checkout'), data=checkout_data)
        
        print(f"   Response status: {response.status_code}")
        
        if response.status_code == 302:  # Redirect
            print(f"   Redirected to: {response.url}")
            
            # Check if redirected to payment page
            if 'payment' in response.url:
                print("✅ Redirected to payment page")
                
                # Check session data after checkout
                session = client.session
                print(f"   Session data after checkout:")
                print(f"     order_id: {session.get('order_id')}")
                print(f"     razorpay_order_id: {session.get('razorpay_order_id')}")
                
                # Step 3: Access payment page
                print()
                print("💳 Step 3: Accessing payment page...")
                
                payment_response = client.get(reverse('payment'))
                print(f"   Payment page status: {payment_response.status_code}")
                
                if payment_response.status_code == 200:
                    print("✅ Payment page accessible")
                    
                    # Check payment page content
                    content = payment_response.content.decode('utf-8')
                    
                    # Look for specific data
                    if 'razorpay_order_id' in content:
                        print("✅ Template contains razorpay_order_id")
                    else:
                        print("❌ Template missing razorpay_order_id")
                    
                    # Look for the actual order ID
                    if session.get('razorpay_order_id') and session.get('razorpay_order_id') in content:
                        print(f"✅ Template contains correct Razorpay order ID: {session.get('razorpay_order_id')}")
                    else:
                        print("❌ Template missing correct Razorpay order ID")
                        print(f"   Expected: {session.get('razorpay_order_id')}")
                    
                else:
                    print(f"❌ Payment page error: {payment_response.status_code}")
                    print(f"   Content: {payment_response.content[:200]}...")
            else:
                print(f"❌ Unexpected redirect: {response.url}")
                
        elif response.status_code == 200:
            print("   Form submission returned 200 (form errors)")
            # Check for form errors
            if hasattr(response, 'context') and response.context:
                form = response.context.get('form')
                if form and form.errors:
                    print(f"   Form errors: {form.errors}")
        else:
            print(f"   Unexpected response: {response.status_code}")
            print(f"   Content: {response.content[:200]}...")
        
        # Cleanup
        cart_item.delete()
        product.delete()
        category.delete()
        cart.delete()
        
    except Exception as e:
        print(f"❌ Test error: {str(e)}")
        import traceback
        traceback.print_exc()
    
    print()
    
    # Cleanup
    user.delete()
    print("🧹 Test data cleaned up")
    print()
    print("=" * 50)
    print("Test completed!")

if __name__ == '__main__':
    test_real_checkout_flow()
