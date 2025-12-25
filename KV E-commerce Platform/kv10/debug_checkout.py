#!/usr/bin/env python
import os
import sys
import django

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'kv10.settings')
django.setup()

from django.test import Client
from django.contrib.auth.models import User
from requirements.forms import CheckoutForm
from requirements.models import Cart, Customer

def test_checkout_flow():
    print("=== DEBUGGING CHECKOUT FLOW ===")
    
    # 1. Check user and cart setup
    try:
        user = User.objects.get(username='testuser')
        customer = Customer.objects.get(user=user)
        cart = Cart.objects.get(customer=customer, is_active=True)
        print(f"✓ User: {user.username}")
        print(f"✓ Customer: {customer.id}")
        print(f"✓ Cart: {cart.id} with {cart.items.count()} items")
    except Exception as e:
        print(f"✗ User/Cart setup error: {e}")
        return
    
    # 2. Test form validation
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
    
    form = CheckoutForm(form_data)
    print(f"\n=== FORM VALIDATION ===")
    print(f"Form valid: {form.is_valid()}")
    if not form.is_valid():
        print(f"Form errors: {form.errors}")
        return
    else:
        print("✓ Form validation passed!")
    
    # 3. Test checkout view with authenticated client
    client = Client()
    client.force_login(user)
    
    print(f"\n=== TESTING CHECKOUT VIEW ===")
    
    # GET request
    response = client.get('/checkout/')
    print(f"GET /checkout/ Status: {response.status_code}")
    
    # POST request
    response = client.post('/checkout/', form_data)
    print(f"POST /checkout/ Status: {response.status_code}")
    
    if response.status_code == 302:
        print(f"✓ Redirect to: {response.get('Location', 'Unknown')}")
        print("SUCCESS: Checkout form is working!")
    elif response.status_code == 200:
        print("✗ Form returned 200 instead of redirecting")
        # Check if there are form errors in the response
        content = response.content.decode()
        if 'error' in content.lower():
            print("Form contains errors")
        else:
            print("Form rendered without errors but didn't redirect")
    else:
        print(f"✗ Unexpected status code: {response.status_code}")

if __name__ == '__main__':
    test_checkout_flow()
