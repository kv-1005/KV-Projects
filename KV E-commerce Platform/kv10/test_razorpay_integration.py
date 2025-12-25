"""
Test script to verify Razorpay integration
"""
import os
import sys
import django
from django.conf import settings

# Set up Django environment
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'kv10.settings')
django.setup()

# Now import your models and services
from requirements.models import Order, Cart, Customer, CartItem, Product, Category
from requirements.payment_service import RazorpayService
from decimal import Decimal
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_razorpay_connection():
    """Test Razorpay API connection"""
    try:
        logger.info("Testing Razorpay connection...")
        razorpay = RazorpayService()
        
        # Test API connection
        payments = razorpay.client.payment.all({"count": 1})
        logger.info("Razorpay connection successful!")
        logger.info(f"API Response: {payments}")
        return True
    except Exception as e:
        logger.error(f"Razorpay connection failed: {str(e)}")
        return False

def create_test_order():
    """Create a test order for Razorpay integration testing"""
    try:
        from django.contrib.auth.models import User
        import uuid
        
        # Generate unique username for this test run
        unique_id = str(uuid.uuid4())[:8]
        test_username = f"testuser_{unique_id}"
        test_email = f"test_{unique_id}@example.com"
        
        # Get or create a test user first
        user, user_created = User.objects.get_or_create(
            username=test_username,
            defaults={
                'email': test_email,
                'first_name': 'Test',
                'last_name': 'User'
            }
        )
        
        if user_created:
            user.set_password('testpass123')
            user.save()
        
        # Get or create a test customer
        customer, customer_created = Customer.objects.get_or_create(
            user=user,
            defaults={
                'phone': '1234567890'
            }
        )
        
        # Create a test product if it doesn't exist
        category, _ = Category.objects.get_or_create(name='Test Category')
        product, _ = Product.objects.get_or_create(
            name='Test Product',
            defaults={
                'description': 'Test product for Razorpay integration',
                'price': Decimal('100.00'),
                'stock_quantity': 10,
                'category': category
            }
        )
        
        # Create a test cart
        cart, _ = Cart.objects.get_or_create(customer=customer, is_active=True)
        
        # Add item to cart
        cart_item, _ = CartItem.objects.get_or_create(
            cart=cart,
            product=product,
            defaults={'quantity': 1}
        )
        
        # Create a test order with correct field names
        order = Order.objects.create(
            customer=customer,
            total_amount=Decimal('100.00'),
            subtotal=Decimal('100.00'),
            tax=Decimal('18.00'),
            shipping_cost=Decimal('50.00'),
            shipping_address='Test Address, Test City, TS 123456',
            billing_address='Test Address, Test City, TS 123456',
            phone='1234567890',
            email=customer.user.email,
            payment_method='razorpay'
        )
        
        logger.info(f"Created test order: {order.id}")
        return order
        
    except Exception as e:
        logger.error(f"Error creating test order: {str(e)}")
        return None

def test_create_razorpay_order():
    """Test creating a Razorpay order"""
    try:
        logger.info("Testing Razorpay order creation...")
        
        # Create a test order
        order = create_test_order()
        if not order:
            logger.error("Failed to create test order")
            return False
        
        # Initialize Razorpay service
        razorpay = RazorpayService()
        
        # Create Razorpay order
        result = razorpay.create_order(order)
        
        if result['success']:
            logger.info(f"Successfully created Razorpay order: {result['order_id']}")
            logger.info(f"Amount: {result['amount'] / 100} {result['currency']}")
            return True
        else:
            logger.error(f"Failed to create Razorpay order: {result.get('error', 'Unknown error')}")
            return False
            
    except Exception as e:
        logger.error(f"Error testing Razorpay order creation: {str(e)}")
        return False

if __name__ == "__main__":
    logger.info("Starting Razorpay integration tests...")
    
    # Test 1: Check Razorpay connection
    logger.info("\n=== Test 1: Razorpay Connection ===")
    connection_test = test_razorpay_connection()
    if connection_test:
        logger.info("✅ Razorpay connection test passed!")
    else:
        logger.error("❌ Razorpay connection test failed!")
    
    # Test 2: Create a test order
    logger.info("\n=== Test 2: Create Test Order ===")
    order = create_test_order()
    if order:
        logger.info(f"✅ Successfully created test order: {order.id}")
    else:
        logger.error("❌ Failed to create test order")
    
    # Test 3: Create Razorpay order
    logger.info("\n=== Test 3: Create Razorpay Order ===")
    razorpay_test = test_create_razorpay_order()
    if razorpay_test:
        logger.info("✅ Razorpay order creation test passed!")
    else:
        logger.error("❌ Razorpay order creation test failed!")
    
    logger.info("\n=== Test Summary ===")
    logger.info(f"1. Razorpay Connection: {'✅ Passed' if connection_test else '❌ Failed'}")
    logger.info(f"2. Test Order Creation: {'✅ Passed' if order else '❌ Failed'}")
    logger.info(f"3. Razorpay Order Creation: {'✅ Passed' if razorpay_test else '❌ Failed'}")
