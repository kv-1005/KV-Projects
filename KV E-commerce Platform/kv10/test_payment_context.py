#!/usr/bin/env python
"""
Payment View Context Debug Test
Tests specifically the payment view context rendering
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

def test_payment_context():
    """Test payment view context specifically"""
    
    print("🔍 Payment View Context Debug Test")
    print("=" * 50)
    print()
    
    # Create test client
    client = Client()
    
    # Create test user
    user, created = User.objects.get_or_create(
        username='testuser_context',
        defaults={
            'email': 'test_context@example.com',
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
        # Create test order
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
        
        print(f"📦 Test order created: {order.id}")
        print(f"   Total amount: {order.total_amount}")
        print()
        
        # Create Razorpay order
        razorpay_service = get_razorpay_service()
        result = razorpay_service.create_order(order)
        
        if result['success']:
            razorpay_order_id = result['order_id']
            print(f"🔌 Razorpay order created: {razorpay_order_id}")
            print()
            
            # Set session data
            session = client.session
            session['order_id'] = order.id
            session['razorpay_order_id'] = razorpay_order_id
            session.save()
            
            print(f"💾 Session data saved:")
            print(f"   order_id: {session.get('order_id')}")
            print(f"   razorpay_order_id: {session.get('razorpay_order_id')}")
            print()
            
            # Test payment view directly
            print("💳 Testing payment view context...")
            
            # Make request to payment view
            response = client.get(reverse('payment'))
            
            print(f"📊 Response details:")
            print(f"   Status: {response.status_code}")
            print(f"   Content-Type: {response.get('Content-Type', 'Not set')}")
            print(f"   Content Length: {len(response.content)}")
            print()
            
            # Check if response has context
            if hasattr(response, 'context'):
                print("✅ Response has context attribute")
                if response.context:
                    print("✅ Context is not None")
                    
                    # Check specific context variables
                    context = response.context
                    print(f"📋 Context variables:")
                    print(f"   order: {context.get('order', 'Not found')}")
                    print(f"   razorpay_order_id: {context.get('razorpay_order_id', 'Not found')}")
                    print(f"   amount: {context.get('amount', 'Not found')}")
                    print(f"   currency: {context.get('currency', 'Not found')}")
                    print(f"   razorpay_key_id: {context.get('razorpay_key_id', 'Not found')}")
                    
                    # Check if the right data is in context
                    if context.get('razorpay_order_id') == razorpay_order_id:
                        print("✅ Correct Razorpay order ID in context")
                    else:
                        print("❌ Wrong Razorpay order ID in context")
                        print(f"   Expected: {razorpay_order_id}")
                        print(f"   Got: {context.get('razorpay_order_id')}")
                        
                else:
                    print("❌ Context is None")
            else:
                print("❌ Response has no context attribute")
            
            # Check response content
            print()
            print("📄 Response content preview:")
            content = response.content.decode('utf-8')
            print(f"   First 500 chars: {content[:500]}...")
            
            # Look for specific template variables
            if 'razorpay_order_id' in content:
                print("✅ Template contains razorpay_order_id")
            else:
                print("❌ Template missing razorpay_order_id")
                
            if razorpay_order_id in content:
                print(f"✅ Template contains correct order ID: {razorpay_order_id}")
            else:
                print(f"❌ Template missing correct order ID: {razorpay_order_id}")
            
            # Cleanup
            order.delete()
            
        else:
            print(f"❌ Razorpay order creation failed: {result.get('error')}")
            order.delete()
            
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
    test_payment_context()
