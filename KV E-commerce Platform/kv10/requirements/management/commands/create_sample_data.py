from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.core.files.base import ContentFile
from requirements.models import Category, Product, Customer
from decimal import Decimal
import requests
import os
from urllib.parse import urlparse

class Command(BaseCommand):
    help = 'Create sample data for the e-commerce store'

    def download_image(self, url, filename):
        """Download image from URL and return ContentFile"""
        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            
            # Get file extension from URL
            parsed_url = urlparse(url)
            path = parsed_url.path
            ext = os.path.splitext(path)[1]
            if not ext:
                ext = '.jpg'  # Default to jpg if no extension found
            
            # Create filename with proper extension
            full_filename = f"{filename}{ext}"
            
            return ContentFile(response.content, name=full_filename)
        except Exception as e:
            self.stdout.write(f"Failed to download image from {url}: {e}")
            return None

    def handle(self, *args, **options):
        self.stdout.write('Creating sample data...')
        
        # Create categories
        categories_data = [
            {
                'name': 'Electronics',
                'slug': 'electronics',
                'description': 'Latest electronic gadgets and devices'
            },
            {
                'name': 'Fashion',
                'slug': 'fashion',
                'description': 'Trendy clothing and accessories'
            },
            {
                'name': 'Home & Garden',
                'slug': 'home-garden',
                'description': 'Everything for your home and garden'
            },
            {
                'name': 'Books',
                'slug': 'books',
                'description': 'Books for all ages and interests'
            },
            {
                'name': 'Sports',
                'slug': 'sports',
                'description': 'Sports equipment and activewear'
            }
        ]
        
        categories = {}
        for cat_data in categories_data:
            category, created = Category.objects.get_or_create(
                slug=cat_data['slug'],
                defaults=cat_data
            )
            categories[cat_data['slug']] = category
            if created:
                self.stdout.write(f'Created category: {category.name}')
        
        # Create sample products
        products_data = [
            {
                'name': 'Wireless Bluetooth Headphones',
                'slug': 'wireless-bluetooth-headphones',
                'category': categories['electronics'],
                'description': 'High-quality wireless headphones with noise cancellation and long battery life.',
                'price': Decimal('2999.00'),
                'sale_price': Decimal('2499.00'),
                'stock_quantity': 50,
                'sku': 'WH-001',
                'is_featured': True
            },
            {
                'name': 'Smartphone Case',
                'slug': 'smartphone-case',
                'category': categories['electronics'],
                'description': 'Durable protective case for smartphones with shock absorption.',
                'price': Decimal('599.00'),
                'stock_quantity': 100,
                'sku': 'SC-001'
            },
            {
                'name': 'Cotton T-Shirt',
                'slug': 'cotton-tshirt',
                'category': categories['fashion'],
                'description': 'Comfortable cotton t-shirt available in multiple colors and sizes.',
                'price': Decimal('799.00'),
                'sale_price': Decimal('599.00'),
                'stock_quantity': 200,
                'sku': 'TS-001',
                'is_featured': True
            },
            {
                'name': 'Denim Jeans',
                'slug': 'denim-jeans',
                'category': categories['fashion'],
                'description': 'Classic denim jeans with perfect fit and comfort.',
                'price': Decimal('1499.00'),
                'stock_quantity': 75,
                'sku': 'DJ-001'
            },
            {
                'name': 'Garden Plant Pot',
                'slug': 'garden-plant-pot',
                'category': categories['home-garden'],
                'description': 'Beautiful ceramic plant pot for indoor and outdoor plants.',
                'price': Decimal('399.00'),
                'stock_quantity': 150,
                'sku': 'GP-001'
            },
            {
                'name': 'LED Desk Lamp',
                'slug': 'led-desk-lamp',
                'category': categories['home-garden'],
                'description': 'Modern LED desk lamp with adjustable brightness and color temperature.',
                'price': Decimal('899.00'),
                'sale_price': Decimal('699.00'),
                'stock_quantity': 60,
                'sku': 'DL-001',
                'is_featured': True
            },
            {
                'name': 'Programming Book',
                'slug': 'programming-book',
                'category': categories['books'],
                'description': 'Comprehensive guide to modern programming techniques and best practices.',
                'price': Decimal('1299.00'),
                'stock_quantity': 30,
                'sku': 'PB-001'
            },
            {
                'name': 'Yoga Mat',
                'slug': 'yoga-mat',
                'category': categories['sports'],
                'description': 'Non-slip yoga mat perfect for yoga, pilates, and fitness activities.',
                'price': Decimal('699.00'),
                'stock_quantity': 80,
                'sku': 'YM-001'
            },
            {
                'name': 'Running Shoes',
                'slug': 'running-shoes',
                'category': categories['sports'],
                'description': 'Comfortable running shoes with excellent cushioning and support.',
                'price': Decimal('2499.00'),
                'sale_price': Decimal('1999.00'),
                'stock_quantity': 40,
                'sku': 'RS-001',
                'is_featured': True
            },
            {
                'name': 'Coffee Mug Set',
                'slug': 'coffee-mug-set',
                'category': categories['home-garden'],
                'description': 'Set of 4 beautiful ceramic coffee mugs, perfect for daily use.',
                'price': Decimal('499.00'),
                'stock_quantity': 120,
                'sku': 'CMS-001'
            }
        ]
        
        # Sample product images (placeholder URLs)
        product_images = {
            'wireless-bluetooth-headphones': 'https://images.pexels.com/photos/3394650/pexels-photo-3394650.jpeg',
            'smartphone-case': 'https://images.pexels.com/photos/1647976/pexels-photo-1647976.jpeg',
            'cotton-tshirt': 'https://images.pexels.com/photos/991509/pexels-photo-991509.jpeg',
            'denim-jeans': 'https://images.pexels.com/photos/1082529/pexels-photo-1082529.jpeg',
            'garden-plant-pot': 'https://images.pexels.com/photos/4503269/pexels-photo-4503269.jpeg',
            'led-desk-lamp': 'https://images.pexels.com/photos/3937174/pexels-photo-3937174.jpeg',
            'programming-book': 'https://images.pexels.com/photos/3747468/pexels-photo-3747468.jpeg',
            'yoga-mat': 'https://images.pexels.com/photos/4056530/pexels-photo-4056530.jpeg',
            'running-shoes': 'https://images.pexels.com/photos/2526878/pexels-photo-2526878.jpeg',
            'coffee-mug-set': 'https://images.pexels.com/photos/302899/pexels-photo-302899.jpeg',
        }
        
        for prod_data in products_data:
            prod_data_copy = prod_data.copy()
            
            # Download and save image if available
            if prod_data['slug'] in product_images:
                image_url = product_images[prod_data['slug']]
                image_file = self.download_image(image_url, prod_data['slug'])
                if image_file:
                    prod_data_copy['image'] = image_file
                    self.stdout.write(f'Downloaded image for: {prod_data["name"]}')
            
            product, created = Product.objects.get_or_create(
                slug=prod_data['slug'],
                defaults=prod_data_copy
            )
            if created:
                self.stdout.write(f'Created product: {product.name}')
        
        # Create a test user
        if not User.objects.filter(username='testuser').exists():
            user = User.objects.create_user(
                username='testuser',
                email='test@example.com',
                password='testpass123',
                first_name='Test',
                last_name='User'
            )
            
            # Create customer profile
            customer = Customer.objects.create(
                user=user,
                phone='+91 9876543210',
                address='123 Test Street',
                city='Mumbai',
                state='Maharashtra',
                zip_code='400001',
                country='India'
            )
            
            self.stdout.write(f'Created test user: {user.username}')
            self.stdout.write('Test user credentials:')
            self.stdout.write('Username: testuser')
            self.stdout.write('Password: testpass123')
        
        self.stdout.write(
            self.style.SUCCESS('Successfully created sample data!')
        ) 