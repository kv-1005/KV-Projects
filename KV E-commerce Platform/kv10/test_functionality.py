#!/usr/bin/env python
"""
Comprehensive functionality test for KV Django E-commerce Project
This script tests all major features and functionalities of the application.
"""

import os
import sys
import django
import time

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'kv10.settings')
django.setup()

from django.test import Client, TestCase
from django.contrib.auth.models import User
from django.urls import reverse
from requirements.models import Category, Product, Customer, Cart, CartItem, Order, Wishlist, Coupon
from decimal import Decimal

class EcommerceFunctionalityTest:
    def __init__(self):
        self.client = Client()
        self.test_results = []
        
    def log_test(self, test_name, status, details=""):
        """Log test results"""
        result = {
            'test': test_name,
            'status': status,
            'details': details,
            'timestamp': time.strftime('%Y-%m-%d %H:%M:%S')
        }
        self.test_results.append(result)
        
        status_icon = "PASS" if status == "PASS" else "FAIL"
        print(f"{status_icon} {test_name}: {status}")
        if details:
            print(f"   Details: {details}")
        print()

    def test_home_page(self):
        """Test home page functionality"""
        try:
            response = self.client.get('/')
            if response.status_code == 200:
                content = response.content.decode()
                if 'KV Store' in content:
                    self.log_test("Home Page", "PASS", "Home page loads successfully")
                    return True
                else:
                    self.log_test("Home Page", "FAIL", "Home page missing key content")
                    return False
            else:
                self.log_test("Home Page", "FAIL", f"Status code: {response.status_code}")
                return False
        except Exception as e:
            self.log_test("Home Page", "FAIL", f"Error: {e}")
            return False

    def test_product_listing(self):
        """Test product listing page"""
        try:
            response = self.client.get('/products/')
            if response.status_code == 200:
                self.log_test("Product Listing", "PASS", "Product listing page loads")
                return True
            else:
                self.log_test("Product Listing", "FAIL", f"Status code: {response.status_code}")
                return False
        except Exception as e:
            self.log_test("Product Listing", "FAIL", f"Error: {e}")
            return False

    def test_product_detail(self):
        """Test product detail page"""
        try:
            product = Product.objects.filter(is_active=True).first()
            if not product:
                self.log_test("Product Detail", "SKIP", "No products available")
                return True
                
            response = self.client.get(f'/product/{product.slug}/')
            if response.status_code == 200:
                self.log_test("Product Detail", "PASS", f"Product detail page loads for {product.name}")
                return True
            else:
                self.log_test("Product Detail", "FAIL", f"Status code: {response.status_code}")
                return False
        except Exception as e:
            self.log_test("Product Detail", "FAIL", f"Error: {e}")
            return False

    def test_category_pages(self):
        """Test category detail pages"""
        try:
            category = Category.objects.filter(is_active=True).first()
            if not category:
                self.log_test("Category Pages", "SKIP", "No categories available")
                return True
                
            response = self.client.get(f'/category/{category.slug}/')
            if response.status_code == 200:
                self.log_test("Category Pages", "PASS", f"Category page loads for {category.name}")
                return True
            else:
                self.log_test("Category Pages", "FAIL", f"Status code: {response.status_code}")
                return False
        except Exception as e:
            self.log_test("Category Pages", "FAIL", f"Error: {e}")
            return False

    def test_search_functionality(self):
        """Test search functionality"""
        try:
            product = Product.objects.filter(is_active=True).first()
            if not product:
                self.log_test("Search Functionality", "SKIP", "No products available for search")
                return True
                
            response = self.client.get(f'/search/?q={product.name}')
            if response.status_code == 200:
                self.log_test("Search Functionality", "PASS", "Search page loads")
                return True
            else:
                self.log_test("Search Functionality", "FAIL", f"Status code: {response.status_code}")
                return False
        except Exception as e:
            self.log_test("Search Functionality", "FAIL", f"Error: {e}")
            return False

    def test_static_pages(self):
        """Test static pages"""
        pages = [
            ('/about/', 'About Page'),
            ('/contact/', 'Contact Page'),
        ]
        
        for url, name in pages:
            try:
                response = self.client.get(url)
                if response.status_code == 200:
                    self.log_test(name, "PASS", f"{name} loads successfully")
                else:
                    self.log_test(name, "FAIL", f"{name} status: {response.status_code}")
            except Exception as e:
                self.log_test(name, "FAIL", f"Error: {e}")

    def test_user_registration(self):
        """Test user registration"""
        try:
            response = self.client.get('/register/')
            if response.status_code == 200:
                self.log_test("Registration Form", "PASS", "Registration form loads")
                
                # Test registration with valid data - use unique username
                import time
                unique_id = int(time.time())
                registration_data = {
                    'first_name': 'Test',
                    'last_name': 'User',
                    'email': f'testuser{unique_id}@example.com',
                    'username': f'testuser{unique_id}',
                    'password1': 'testpass123',
                    'password2': 'testpass123'
                }
                
                # First get the registration form to get CSRF token
                response = self.client.get('/register/')
                if response.status_code == 200:
                    # Extract CSRF token from the form
                    content = response.content.decode()
                    import re
                    csrf_match = re.search(r'name="csrfmiddlewaretoken" value="([^"]+)"', content)
                    if csrf_match:
                        csrf_token = csrf_match.group(1)
                        registration_data['csrfmiddlewaretoken'] = csrf_token
                
                response = self.client.post('/register/', registration_data)
                if response.status_code == 302:  # Redirect after successful registration
                    self.log_test("User Registration", "PASS", "User registration successful")
                    return True
                else:
                    # Debug: Check what the response contains
                    content = response.content.decode()
                    if 'error' in content.lower() or 'invalid' in content.lower():
                        self.log_test("User Registration", "FAIL", f"Registration failed - Form errors: {content[:200]}...")
                    else:
                        self.log_test("User Registration", "FAIL", f"Registration failed - Status: {response.status_code}")
                    return False
            else:
                self.log_test("User Registration", "FAIL", f"Registration form status: {response.status_code}")
                return False
        except Exception as e:
            self.log_test("User Registration", "FAIL", f"Error: {e}")
            return False

    def test_user_login_logout(self):
        """Test user login and logout"""
        try:
            response = self.client.get('/login/')
            if response.status_code == 200:
                self.log_test("Login Form", "PASS", "Login form loads")
                
                # Test login with test user
                login_data = {
                    'username': 'testuser',
                    'password': 'testpass123'
                }
                
                response = self.client.post('/login/', login_data)
                if response.status_code == 302:  # Redirect after successful login
                    self.log_test("User Login", "PASS", "User login successful")
                    
                    # Test logout
                    response = self.client.get('/logout/')
                    if response.status_code == 302:
                        self.log_test("User Logout", "PASS", "User logout successful")
                        return True
                    else:
                        self.log_test("User Logout", "FAIL", "Logout failed")
                        return False
                else:
                    self.log_test("User Login", "FAIL", "Login failed")
                    return False
            else:
                self.log_test("User Login", "FAIL", f"Login form status: {response.status_code}")
                return False
        except Exception as e:
            self.log_test("User Login", "FAIL", f"Error: {e}")
            return False

    def test_shopping_cart(self):
        """Test shopping cart functionality"""
        try:
            # Login first
            self.client.post('/login/', {'username': 'testuser', 'password': 'testpass123'})
            
            # Test cart page access
            response = self.client.get('/cart/')
            if response.status_code == 200:
                self.log_test("Cart Page Access", "PASS", "Cart page loads for authenticated user")
                
                # Test adding item to cart
                product = Product.objects.filter(is_active=True, stock_quantity__gt=0).first()
                if not product:
                    self.log_test("Add to Cart", "SKIP", "No products with stock available")
                    return True
                
                response = self.client.post(f'/add-to-cart/{product.id}/', {'quantity': 1})
                if response.status_code == 302:
                    self.log_test("Add to Cart", "PASS", f"Added {product.name} to cart")
                    return True
                else:
                    self.log_test("Add to Cart", "FAIL", "Failed to add item to cart")
                    return False
            else:
                self.log_test("Cart Page Access", "FAIL", f"Cart page status: {response.status_code}")
                return False
        except Exception as e:
            self.log_test("Shopping Cart", "FAIL", f"Error: {e}")
            return False

    def test_wishlist(self):
        """Test wishlist functionality"""
        try:
            # Login first
            self.client.post('/login/', {'username': 'testuser', 'password': 'testpass123'})
            
            # Test wishlist page access
            response = self.client.get('/wishlist/')
            if response.status_code == 200:
                self.log_test("Wishlist Page Access", "PASS", "Wishlist page loads")
                
                # Test adding item to wishlist
                product = Product.objects.filter(is_active=True).first()
                if not product:
                    self.log_test("Add to Wishlist", "SKIP", "No products available")
                    return True
                
                response = self.client.get(f'/add-to-wishlist/{product.id}/')
                if response.status_code == 302:
                    self.log_test("Add to Wishlist", "PASS", f"Added {product.name} to wishlist")
                    return True
                else:
                    self.log_test("Add to Wishlist", "FAIL", "Failed to add item to wishlist")
                    return False
            else:
                self.log_test("Wishlist Page Access", "FAIL", f"Wishlist page status: {response.status_code}")
                return False
        except Exception as e:
            self.log_test("Wishlist", "FAIL", f"Error: {e}")
            return False

    def test_checkout_process(self):
        """Test checkout process"""
        try:
            # Login first
            self.client.post('/login/', {'username': 'testuser', 'password': 'testpass123'})
            
            # Add item to cart first
            product = Product.objects.filter(is_active=True, stock_quantity__gt=0).first()
            if not product:
                self.log_test("Checkout Process", "SKIP", "No products with stock available")
                return True
            
            self.client.post(f'/add-to-cart/{product.id}/', {'quantity': 1})
            
            # Test checkout page access
            response = self.client.get('/checkout/')
            if response.status_code == 200:
                self.log_test("Checkout Page Access", "PASS", "Checkout page loads")
                return True
            else:
                self.log_test("Checkout Page Access", "FAIL", f"Checkout page status: {response.status_code}")
                return False
        except Exception as e:
            self.log_test("Checkout Process", "FAIL", f"Error: {e}")
            return False

    def test_order_management(self):
        """Test order management"""
        try:
            # Login first
            self.client.post('/login/', {'username': 'testuser', 'password': 'testpass123'})
            
            # Test order list page
            response = self.client.get('/orders/')
            if response.status_code == 200:
                self.log_test("Order List Page", "PASS", "Order list page loads")
                return True
            else:
                self.log_test("Order List Page", "FAIL", f"Order list page status: {response.status_code}")
                return False
        except Exception as e:
            self.log_test("Order Management", "FAIL", f"Error: {e}")
            return False

    def test_profile_management(self):
        """Test user profile management"""
        try:
            # Login first
            self.client.post('/login/', {'username': 'testuser', 'password': 'testpass123'})
            
            # Test profile page access
            response = self.client.get('/profile/')
            if response.status_code == 200:
                self.log_test("Profile Page Access", "PASS", "Profile page loads")
                return True
            else:
                self.log_test("Profile Page Access", "FAIL", f"Profile page status: {response.status_code}")
                return False
        except Exception as e:
            self.log_test("Profile Management", "FAIL", f"Error: {e}")
            return False

    def test_navigation_links(self):
        """Test navigation links in header"""
        try:
            response = self.client.get('/')
            content = response.content.decode()
            
            # Check for key navigation links
            nav_links = [
                'href="/"',
                'href="/products/"',
                'href="/about/"',
                'href="/contact/"',
                'href="/login/"',
                'href="/register/"'
            ]
            
            missing_links = []
            for link in nav_links:
                if link not in content:
                    missing_links.append(link)
            
            if not missing_links:
                self.log_test("Navigation Links", "PASS", "All navigation links present")
                return True
            else:
                self.log_test("Navigation Links", "FAIL", f"Missing links: {missing_links}")
                return False
        except Exception as e:
            self.log_test("Navigation Links", "FAIL", f"Error: {e}")
            return False

    def test_responsive_design(self):
        """Test responsive design elements"""
        try:
            response = self.client.get('/')
            content = response.content.decode()
            
            # Check for responsive design elements
            responsive_elements = [
                'viewport',
                'mobile.css',
                'media query',
                'responsive'
            ]
            
            found_elements = []
            for element in responsive_elements:
                if element.lower() in content.lower():
                    found_elements.append(element)
            
            if len(found_elements) >= 2:  # At least viewport and mobile CSS
                self.log_test("Responsive Design", "PASS", f"Responsive elements found: {found_elements}")
                return True
            else:
                self.log_test("Responsive Design", "FAIL", f"Limited responsive elements: {found_elements}")
                return False
        except Exception as e:
            self.log_test("Responsive Design", "FAIL", f"Error: {e}")
            return False

    def test_form_validation(self):
        """Test form validation"""
        try:
            # Test registration form validation
            invalid_data = {
                'fullname': '',
                'email': 'invalid-email',
                'username': '',
                'password': '123',
                'confirmpassword': '456'
            }
            
            response = self.client.post('/register/', invalid_data)
            if response.status_code == 200:  # Form should reload with errors
                self.log_test("Form Validation", "PASS", "Form validation working")
                return True
            else:
                self.log_test("Form Validation", "FAIL", "Form validation not working")
                return False
        except Exception as e:
            self.log_test("Form Validation", "FAIL", f"Error: {e}")
            return False

    def test_legacy_urls(self):
        """Test legacy URLs for backward compatibility"""
        legacy_urls = [
            ('/signup/', 'Legacy Signup'),
            ('/home', 'Legacy Home'),
            ('/products', 'Legacy Products'),
            ('/test', 'Test Page'),
            ('/producttest', 'Product Test Page'),
        ]
        
        for url, name in legacy_urls:
            try:
                response = self.client.get(url)
                if response.status_code == 200:
                    self.log_test(name, "PASS", f"{name} loads successfully")
                else:
                    self.log_test(name, "FAIL", f"{name} status: {response.status_code}")
            except Exception as e:
                self.log_test(name, "FAIL", f"Error: {e}")

    def run_all_tests(self):
        """Run all tests"""
        print("Starting Comprehensive E-commerce Functionality Test")
        print("=" * 60)
        
        # Run all tests
        tests = [
            self.test_home_page,
            self.test_product_listing,
            self.test_product_detail,
            self.test_category_pages,
            self.test_search_functionality,
            self.test_navigation_links,
            self.test_static_pages,
            self.test_responsive_design,
            self.test_form_validation,
            self.test_legacy_urls,
            self.test_user_registration,
            self.test_user_login_logout,
            self.test_shopping_cart,
            self.test_wishlist,
            self.test_checkout_process,
            self.test_order_management,
            self.test_profile_management,
        ]
        
        for test in tests:
            try:
                test()
            except Exception as e:
                self.log_test(test.__name__, "ERROR", f"Test crashed: {e}")
        
        # Generate summary
        self.generate_summary()

    def generate_summary(self):
        """Generate test summary"""
        print("\n" + "=" * 60)
        print("📊 TEST SUMMARY")
        print("=" * 60)
        
        total_tests = len(self.test_results)
        passed_tests = len([r for r in self.test_results if r['status'] == 'PASS'])
        failed_tests = len([r for r in self.test_results if r['status'] == 'FAIL'])
        error_tests = len([r for r in self.test_results if r['status'] == 'ERROR'])
        skipped_tests = len([r for r in self.test_results if r['status'] == 'SKIP'])
        
        print(f"Total Tests: {total_tests}")
        print(f"Passed: {passed_tests}")
        print(f"Failed: {failed_tests}")
        print(f"⚠️  Errors: {error_tests}")
        print(f"⏭️  Skipped: {skipped_tests}")
        
        success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
        print(f"Success Rate: {success_rate:.1f}%")
        
        if failed_tests > 0 or error_tests > 0:
            print("\nFAILED TESTS:")
            for result in self.test_results:
                if result['status'] in ['FAIL', 'ERROR']:
                    print(f"  - {result['test']}: {result['details']}")
        
        if success_rate >= 90:
            print("\nEXCELLENT! Your e-commerce application is working very well!")
        elif success_rate >= 75:
            print("\nGOOD! Your e-commerce application is mostly working with minor issues.")
        elif success_rate >= 50:
            print("\nFAIR! Your e-commerce application has several issues that need attention.")
        else:
            print("\nPOOR! Your e-commerce application has significant issues that need immediate attention.")

if __name__ == "__main__":
    tester = EcommerceFunctionalityTest()
    tester.run_all_tests() 