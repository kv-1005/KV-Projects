#!/usr/bin/env python
import os
import sys
import django

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'kv10.settings')
django.setup()

from django.test import Client
from django.contrib.auth.models import User
from requirements.models import Customer, Cart, Product, CartItem

def test_complete_flow():
    print("=== TESTING COMPLETE CHECKOUT FLOW ===")
    
    # Create test client
    client = Client()
    
    # 1. Test login
    print("\n1. Testing Login...")
    login_data = {
        'username': 'testuser',
        'password': 'testpass123'
    }
    response = client.post('/login/', login_data)
    print(f"Login Status: {response.status_code}")
    
    if response.status_code == 302:
        print("✓ Login successful")
    else:
        print("✗ Login failed")
        return
    
    # 2. Test cart access
    print("\n2. Testing Cart...")
    response = client.get('/cart/')
    print(f"Cart Status: {response.status_code}")
    
    # 3. Test checkout access
    print("\n3. Testing Checkout Access...")
    response = client.get('/checkout/')
    print(f"Checkout GET Status: {response.status_code}")
    
    if response.status_code != 200:
        print("✗ Cannot access checkout page")
        return
    
    # 4. Test checkout form submission
    print("\n4. Testing Checkout Form Submission...")
    form_data = {
        'shipping_first_name': 'Test',
        'shipping_last_name': 'User',
        'shipping_address': '123 Test Street',
        'shipping_city': 'Test City',
        'shipping_state': 'Test State',
        'shipping_zip_code': '12345',
        'shipping_phone': '1234567890',
        'payment_method': 'razorpay',
        'billing_same_as_shipping': True
    }
    
    response = client.post('/checkout/', form_data)
    print(f"Checkout POST Status: {response.status_code}")
    
    if response.status_code == 200:
        content = response.content.decode()
        if 'Secure Payment' in content:
            print("✓ SUCCESS: Checkout redirected to payment page!")
            print("✓ Razorpay integration is working!")
        else:
            print("✗ Checkout form has errors")
            if 'errorlist' in content:
                print("Found form validation errors")
    elif response.status_code == 302:
        print(f"✓ Redirect to: {response.get('Location')}")
    else:
        print(f"✗ Unexpected status: {response.status_code}")
    
    print("\n=== FLOW TEST COMPLETE ===")

if __name__ == '__main__':
    test_complete_flow()
