#!/usr/bin/env python
"""
Debug script to test session data persistence
"""

import os
import sys
import django
from django.conf import settings
from decimal import Decimal

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'kv10.settings')
django.setup()

from django.contrib.auth.models import User
from django.test import Client
from django.urls import reverse
from requirements.models import *
from requirements.payment_service import get_razorpay_service

def test_session_persistence():
    """Test if session data is being saved and retrieved correctly"""
    
    print("Testing session data persistence...")
    
    # Create test client
    client = Client()
    
    # Create test user
    user, created = User.objects.get_or_create(
        username='testuser_session',
        defaults={
            'email': 'test_session@example.com',
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
    
    # Login the user
    client.force_login(user)
    
    # Test session data
    print(f"User logged in: {user.username}")
    
    # Set session data
    session = client.session
    session['test_key'] = 'test_value'
    session['order_id'] = 123
    session['razorpay_order_id'] = 'order_test123'
    session.save()
    
    print(f"Session data set:")
    print(f"  test_key: {session.get('test_key')}")
    print(f"  order_id: {session.get('order_id')}")
    print(f"  razorpay_order_id: {session.get('razorpay_order_id')}")
    
    # Create a new client instance to simulate a new request
    client2 = Client()
    client2.force_login(user)
    
    # Check if session data persists
    session2 = client2.session
    print(f"\nSession data after new request:")
    print(f"  test_key: {session2.get('test_key')}")
    print(f"  order_id: {session2.get('order_id')}")
    print(f"  razorpay_order_id: {session2.get('razorpay_order_id')}")
    
    # Test checkout to payment flow
    print(f"\nTesting checkout to payment flow...")
    
    # Create a test order
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
    
    print(f"Created test order: {order.id}")
    
    # Test Razorpay service
    razorpay_service = get_razorpay_service()
    if razorpay_service:
        result = razorpay_service.create_order(order)
        if result['success']:
            razorpay_order_id = result['order_id']
            print(f"Created Razorpay order: {razorpay_order_id}")
            
            # Set session data
            session2['order_id'] = order.id
            session2['razorpay_order_id'] = razorpay_order_id
            session2.save()
            
            print(f"Session data set:")
            print(f"  order_id: {session2.get('order_id')}")
            print(f"  razorpay_order_id: {session2.get('razorpay_order_id')}")
            
            # Test payment page access
            response = client2.get(reverse('payment'))
            print(f"Payment page response status: {response.status_code}")
            
            if response.status_code == 200:
                print("Payment page accessible")
                # Check if the template context has the right data
                if hasattr(response, 'context') and response.context:
                    if 'razorpay_order_id' in response.context:
                        print(f"Template context razorpay_order_id: {response.context['razorpay_order_id']}")
                    else:
                        print("Template context missing razorpay_order_id")
                else:
                    print("No context available in response")
            else:
                print(f"Payment page error: {response.content}")
        else:
            print(f"Failed to create Razorpay order: {result.get('error')}")
    else:
        print("Razorpay service not available")
    
    # Cleanup
    order.delete()
    user.delete()
    print("\nTest completed.")

if __name__ == '__main__':
    test_session_persistence()
