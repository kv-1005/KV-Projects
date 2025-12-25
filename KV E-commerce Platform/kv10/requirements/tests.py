from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from .models import Category, Product, Customer, Cart, CartItem, Order, Wishlist

class KVStoreFunctionalityTest(TestCase):
    """Comprehensive test suite for KV Store functionality"""
    
    def setUp(self):
        """Set up test data"""
        self.client = Client()
        
        # Create test user
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123',
            first_name='Test',
            last_name='User'
        )
        
        # Create customer profile
        self.customer = Customer.objects.create(
            user=self.user,
            phone='1234567890',
            address='123 Test St',
            city='Test City',
            state='Test State',
            zip_code='12345'
        )
        
        # Create test category
        self.category = Category.objects.create(
            name='Electronics',
            slug='electronics',
            description='Electronic devices and gadgets'
        )
        
        # Create test product
        self.product = Product.objects.create(
            category=self.category,
            name='Test Product',
            slug='test-product',
            description='A test product for testing',
            price=99.99,
            stock_quantity=10,
            sku='TEST001',
            is_active=True,
            is_featured=True
        )
        
        # Create cart for user
        self.cart = Cart.objects.create(
            customer=self.customer,
            is_active=True
        )

    def test_home_page(self):
        """Test home page functionality"""
        print("🔍 Testing Home Page...")
        
        # Test home page loads
        response = self.client.get(reverse('home'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'KV Store')
        self.assertContains(response, 'Discover Amazing Products')
        
        # Test featured products section
        self.assertContains(response, 'Featured Products')
        
        # Test categories section
        self.assertContains(response, 'Shop by Category')
        
        # Test navigation links
        self.assertContains(response, 'href="/products/"')
        self.assertContains(response, 'href="/about/"')
        self.assertContains(response, 'href="/contact/"')
        
        print("Home page functionality working correctly")

    def test_navigation(self):
        """Test navigation menu functionality"""
        print("🔍 Testing Navigation...")
        
        # Test unauthenticated navigation
        response = self.client.get(reverse('home'))
        self.assertContains(response, 'Login')
        self.assertContains(response, 'Sign Up')
        self.assertNotContains(response, 'Profile')
        self.assertNotContains(response, 'Cart')
        
        # Test authenticated navigation
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(reverse('home'))
        self.assertContains(response, 'Profile')
        self.assertContains(response, 'Orders')
        self.assertContains(response, 'Wishlist')
        self.assertContains(response, 'Logout')
        
        print("Navigation functionality working correctly")

    def test_authentication(self):
        """Test authentication system"""
        print("🔍 Testing Authentication...")
        
        # Test registration page
        response = self.client.get(reverse('register'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Create Your Account')
        
        # Test login page
        response = self.client.get(reverse('login'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Welcome Back')
        
        # Test login functionality
        response = self.client.post(reverse('login'), {
            'username': 'testuser',
            'password': 'testpass123'
        })
        self.assertEqual(response.status_code, 302)  # Redirect after login
        
        # Test logout
        response = self.client.get(reverse('logout'))
        self.assertEqual(response.status_code, 302)  # Redirect after logout
        
        print("Authentication functionality working correctly")

    def test_product_listing(self):
        """Test product listing page"""
        print("🔍 Testing Product Listing...")
        
        response = self.client.get(reverse('products'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'All Products')
        self.assertContains(response, 'Test Product')
        
        # Test search functionality
        response = self.client.get(reverse('products'), {'query': 'Test'})
        self.assertContains(response, 'Test Product')
        
        # Test category filter
        response = self.client.get(reverse('products'), {'category': 'electronics'})
        self.assertContains(response, 'Test Product')
        
        # Test price filter
        response = self.client.get(reverse('products'), {'min_price': '50', 'max_price': '150'})
        self.assertContains(response, 'Test Product')
        
        print("Product listing functionality working correctly")

    def test_product_detail(self):
        """Test product detail page"""
        print("🔍 Testing Product Detail...")
        
        response = self.client.get(reverse('product_detail', kwargs={'slug': 'test-product'}))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Test Product')
        self.assertContains(response, '₹99.99')
        self.assertContains(response, 'Add to Cart')
        
        # Test add to cart button (requires authentication)
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(reverse('add_to_cart', kwargs={'product_id': self.product.id}))
        self.assertEqual(response.status_code, 302)  # Redirect after adding to cart
        
        print("Product detail functionality working correctly")

    def test_shopping_cart(self):
        """Test shopping cart functionality"""
        print("🔍 Testing Shopping Cart...")
        
        # Login required for cart
        self.client.login(username='testuser', password='testpass123')
        
        # Add item to cart
        response = self.client.get(reverse('add_to_cart', kwargs={'product_id': self.product.id}))
        self.assertEqual(response.status_code, 302)
        
        # Test cart page
        response = self.client.get(reverse('cart'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Shopping Cart')
        self.assertContains(response, 'Test Product')
        
        # Test quantity update
        cart_item = CartItem.objects.get(cart=self.cart, product=self.product)
        response = self.client.post(reverse('cart'), {
            f'quantity_{cart_item.id}': '2'
        })
        self.assertEqual(response.status_code, 200)
        
        # Test remove from cart
        response = self.client.get(reverse('remove_from_cart', kwargs={'item_id': cart_item.id}))
        self.assertEqual(response.status_code, 302)
        
        print("Shopping cart functionality working correctly")

    def test_wishlist(self):
        """Test wishlist functionality"""
        print("🔍 Testing Wishlist...")
        
        # Login required for wishlist
        self.client.login(username='testuser', password='testpass123')
        
        # Add to wishlist
        response = self.client.get(reverse('add_to_wishlist', kwargs={'product_id': self.product.id}))
        self.assertEqual(response.status_code, 302)
        
        # Test wishlist page
        response = self.client.get(reverse('wishlist'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'My Wishlist')
        self.assertContains(response, 'Test Product')
        
        # Test remove from wishlist
        wishlist_item = Wishlist.objects.get(customer=self.customer, product=self.product)
        response = self.client.get(reverse('remove_from_wishlist', kwargs={'item_id': wishlist_item.id}))
        self.assertEqual(response.status_code, 302)
        
        print("Wishlist functionality working correctly")

    def test_checkout(self):
        """Test checkout functionality"""
        print("🔍 Testing Checkout...")
        
        # Login required for checkout
        self.client.login(username='testuser', password='testpass123')
        
        # Add item to cart first
        self.client.get(reverse('add_to_cart', kwargs={'product_id': self.product.id}))
        
        # Test checkout page
        response = self.client.get(reverse('checkout'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Checkout')
        self.assertContains(response, 'Shipping Information')
        
        print("Checkout functionality working correctly")

    def test_search(self):
        """Test search functionality"""
        print("🔍 Testing Search...")
        
        response = self.client.get(reverse('search'), {'q': 'Test Product'})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Test Product')
        
        # Test empty search
        response = self.client.get(reverse('search'), {'q': 'Nonexistent'})
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, 'Test Product')
        
        print("Search functionality working correctly")

    def test_category_pages(self):
        """Test category pages"""
        print("🔍 Testing Category Pages...")
        
        response = self.client.get(reverse('category_detail', kwargs={'slug': 'electronics'}))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Electronics')
        self.assertContains(response, 'Test Product')
        
        print("Category pages functionality working correctly")

    def test_user_profile(self):
        """Test user profile functionality"""
        print("🔍 Testing User Profile...")
        
        # Login required for profile
        self.client.login(username='testuser', password='testpass123')
        
        response = self.client.get(reverse('profile'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Profile')
        self.assertContains(response, 'Test User')
        
        print("User profile functionality working correctly")

    def test_order_management(self):
        """Test order management"""
        print("🔍 Testing Order Management...")
        
        # Login required for orders
        self.client.login(username='testuser', password='testpass123')
        
        # Create a test order
        order = Order.objects.create(
            order_number='TEST001',
            customer=self.customer,
            subtotal=99.99,
            total_amount=99.99,
            shipping_address='123 Test St, Test City, Test State 12345',
            billing_address='123 Test St, Test City, Test State 12345',
            phone='1234567890',
            email='test@example.com'
        )
        
        # Test order list
        response = self.client.get(reverse('order_list'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'My Orders')
        self.assertContains(response, 'TEST001')
        
        # Test order detail
        response = self.client.get(reverse('order_detail', kwargs={'order_id': order.id}))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Order Details')
        self.assertContains(response, 'TEST001')
        
        print("Order management functionality working correctly")

    def test_static_pages(self):
        """Test static pages"""
        print("🔍 Testing Static Pages...")
        
        # Test about page
        response = self.client.get(reverse('about'))
        self.assertEqual(response.status_code, 200)
        
        # Test contact page
        response = self.client.get(reverse('contact'))
        self.assertEqual(response.status_code, 200)
        
        print("Static pages functionality working correctly")

    def test_mobile_responsiveness(self):
        """Test mobile responsiveness indicators"""
        print("🔍 Testing Mobile Responsiveness...")
        
        response = self.client.get(reverse('home'))
        
        # Check for mobile CSS inclusion
        self.assertContains(response, 'mobile.css')
        
        # Check for viewport meta tag
        self.assertContains(response, 'width=device-width, initial-scale=1.0')
        
        # Check for touch-friendly elements
        self.assertContains(response, 'btn')
        self.assertContains(response, 'nav-link')
        
        print("Mobile responsiveness indicators present")

    def test_error_handling(self):
        """Test error handling"""
        print("🔍 Testing Error Handling...")
        
        # Test 404 for non-existent product
        response = self.client.get(reverse('product_detail', kwargs={'slug': 'non-existent'}))
        self.assertEqual(response.status_code, 404)
        
        # Test 404 for non-existent category
        response = self.client.get(reverse('category_detail', kwargs={'slug': 'non-existent'}))
        self.assertEqual(response.status_code, 404)
        
        print("Error handling working correctly")

    def test_security(self):
        """Test security features"""
        print("🔍 Testing Security Features...")
        
        # Test authentication required pages
        response = self.client.get(reverse('cart'))
        self.assertEqual(response.status_code, 302)  # Redirect to login
        
        response = self.client.get(reverse('profile'))
        self.assertEqual(response.status_code, 302)  # Redirect to login
        
        print("Security features working correctly")
