#!/usr/bin/env python
"""
Django Payment Flow Debug Test
Tests the Django payment integration step by step
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

def test_django_payment_flow():
    """Test Django payment flow step by step"""
    
    print("🚀 Django Payment Flow Debug Test")
    print("=" * 50)
    print()
    
    # Create test client
    client = Client()
    
    # Create test user
    user, created = User.objects.get_or_create(
        username='testuser_payment',
        defaults={
            'email': 'test_payment@example.com',
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
    
    print(f"👤 Test user created: {user.username}")
    print(f"📱 Customer created: {customer.id}")
    print()
    
    # Login the user
    client.force_login(user)
    print("✅ User logged in successfully")
    print()
    
    # Step 1: Test checkout page access
    print("📍 Step 1: Testing checkout page access...")
    try:
        response = client.get(reverse('checkout'))
        if response.status_code == 200:
            print("✅ Checkout page accessible")
            print(f"   Status: {response.status_code}")
            
            # Check if Razorpay is configured in context
            if hasattr(response, 'context') and response.context:
                razorpay_configured = response.context.get('razorpay_configured', False)
                print(f"   Razorpay configured: {razorpay_configured}")
            else:
                print("   No context available")
        else:
            print(f"❌ Checkout page error: {response.status_code}")
            print(f"   Content: {response.content[:200]}...")
    except Exception as e:
        print(f"❌ Checkout page error: {str(e)}")
    
    print()
    
    # Step 2: Test Razorpay service
    print("🔌 Step 2: Testing Razorpay service...")
    try:
        razorpay_service = get_razorpay_service()
        if razorpay_service:
            print("✅ Razorpay service available")
            
            # Test order creation
            order = Order.objects.create(
                customer=customer,
                total_amount=Decimal('100.00'),
                subtotal=Decimal('100.00'),
                tax=Decimal('18.00'),
                shipping_cost=Decimal('50.00'),
                shipping_address='Test Address',
                billing_address='Test Address',
                phone='1234567890',
                email=user.email,
                payment_method='razorpay'
            )
            
            print(f"✅ Test order created: {order.id}")
            
            # Create Razorpay order
            result = razorpay_service.create_order(order)
            if result['success']:
                razorpay_order_id = result['order_id']
                print(f"✅ Razorpay order created: {razorpay_order_id}")
                
                # Store in session
                session = client.session
                session['order_id'] = order.id
                session['razorpay_order_id'] = razorpay_order_id
                session.save()
                
                print(f"✅ Session data saved:")
                print(f"   order_id: {session.get('order_id')}")
                print(f"   razorpay_order_id: {session.get('razorpay_order_id')}")
                
                # Step 3: Test payment page access
                print()
                print("💳 Step 3: Testing payment page access...")
                
                response = client.get(reverse('payment'))
                if response.status_code == 200:
                    print("✅ Payment page accessible")
                    print(f"   Status: {response.status_code}")
                    
                    # Check context data
                    if hasattr(response, 'context') and response.context:
                        context = response.context
                        print("   Context data:")
                        print(f"     order_id: {context.get('order_id', 'Not found')}")
                        print(f"     razorpay_order_id: {context.get('razorpay_order_id', 'Not found')}")
                        print(f"     amount: {context.get('amount', 'Not found')}")
                        print(f"     currency: {context.get('currency', 'Not found')}")
                        
                        # Check if the right data is being passed
                        if context.get('razorpay_order_id') == razorpay_order_id:
                            print("✅ Correct Razorpay order ID in context")
                        else:
                            print("❌ Wrong Razorpay order ID in context")
                            print(f"   Expected: {razorpay_order_id}")
                            print(f"   Got: {context.get('razorpay_order_id')}")
                    else:
                        print("❌ No context available")
                        
                else:
                    print(f"❌ Payment page error: {response.status_code}")
                    print(f"   Content: {response.content[:200]}...")
                
                # Cleanup
                order.delete()
                
            else:
                print(f"❌ Razorpay order creation failed: {result.get('error')}")
                order.delete()
        else:
            print("❌ Razorpay service not available")
    except Exception as e:
        print(f"❌ Razorpay service error: {str(e)}")
    
    print()
    
    # Cleanup
    user.delete()
    print("🧹 Test data cleaned up")
    print()
    print("=" * 50)
    print("Test completed!")

if __name__ == '__main__':
    test_django_payment_flow()
