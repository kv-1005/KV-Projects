#!/usr/bin/env python
"""
Direct Razorpay API Test
Tests the API configuration without Django
"""

import os
import razorpay
from decimal import Decimal

def test_razorpay_api():
    """Test Razorpay API directly"""
    
    # Load environment variables
    from dotenv import load_dotenv
    load_dotenv()
    
    # Get API credentials
    key_id = os.getenv('RAZORPAY_KEY_ID')
    key_secret = os.getenv('RAZORPAY_KEY_SECRET')
    
    print("🔑 Razorpay API Configuration:")
    print(f"  Key ID: {key_id}")
    print(f"  Key Secret: {'*' * 8 + key_secret[-4:] if key_secret else 'Not set'}")
    print()
    
    if not key_id or not key_secret:
        print("❌ Missing Razorpay credentials!")
        return False
    
    try:
        # Initialize Razorpay client
        print("🔌 Testing Razorpay connection...")
        client = razorpay.Client(auth=(key_id, key_secret))
        
        # Test connection by fetching payments
        payments = client.payment.all()
        print("✅ Razorpay connection successful!")
        print(f"  Found {len(payments.get('items', []))} payments")
        print()
        
        # Test order creation
        print("📝 Testing order creation...")
        order_data = {
            'amount': 10000,  # 100 INR in paise
            'currency': 'INR',
            'receipt': 'test_order_001',
            'payment_capture': 1,
            'notes': {
                'test': 'true',
                'description': 'Test order for API verification'
            }
        }
        
        print(f"  Order data: {order_data}")
        
        # Create test order
        order = client.order.create(order_data)
        print("✅ Test order created successfully!")
        print(f"  Order ID: {order['id']}")
        print(f"  Amount: {order['amount']} paise")
        print(f"  Currency: {order['currency']}")
        print(f"  Status: {order['status']}")
        print()
        
        # Test payment link creation
        print("🔗 Testing payment link creation...")
        payment_link_data = {
            'amount': 10000,
            'currency': 'INR',
            'accept_partial': False,
            'reference_id': f"test_ref_{order['id']}",
            'description': 'Test payment for API verification',
            'callback_url': 'http://127.0.0.1:8000/payment/callback/',
            'callback_method': 'get'
        }
        
        payment_link = client.payment_link.create(payment_link_data)
        print("✅ Payment link created successfully!")
        print(f"  Payment Link ID: {payment_link['id']}")
        print(f"  Short URL: {payment_link['short_url']}")
        print(f"  Full URL: {payment_link['payment_link']}")
        print()
        
        # Clean up test order
        print("🧹 Cleaning up test order...")
        # Note: Razorpay doesn't allow order deletion, but we can mark it as cancelled
        print("  Test order will remain in Razorpay (cannot be deleted)")
        print()
        
        print("🎉 All Razorpay API tests passed!")
        print()
        print("📱 Next Steps:")
        print("  1. Your API configuration is working correctly")
        print("  2. The payment failure might be in the Django integration")
        print("  3. Check browser console for JavaScript errors")
        print("  4. Verify session data is being passed correctly")
        
        return True
        
    except Exception as e:
        print(f"❌ Razorpay API test failed: {str(e)}")
        print()
        print("🔍 Debugging tips:")
        print("  1. Check if your API keys are correct")
        print("  2. Verify your Razorpay account is active")
        print("  3. Check if you're using test keys for test environment")
        return False

if __name__ == '__main__':
    print("🚀 Razorpay API Direct Test")
    print("=" * 40)
    print()
    
    test_razorpay_api()
    
    print()
    print("=" * 40)
    print("Test completed!")
