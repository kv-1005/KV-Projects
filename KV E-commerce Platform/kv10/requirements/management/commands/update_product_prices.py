from django.core.management.base import BaseCommand
from requirements.models import Product
from decimal import Decimal
import random

class Command(BaseCommand):
    help = 'Update all product prices to be more realistic and reasonable'

    def handle(self, *args, **options):
        self.stdout.write('Updating product prices to be more realistic...')
        
        # Define realistic price ranges for different categories
        price_ranges = {
            'electronics-gadgets': {
                'smartphones': (15000, 80000),
                'laptops': (30000, 150000),
                'tablets': (15000, 60000),
                'headphones': (1000, 15000),
                'speakers': (500, 8000),
                'cameras': (8000, 50000),
                'monitors': (5000, 25000),
                'keyboards': (500, 3000),
                'mice': (300, 2000),
                'webcams': (800, 5000),
                'default': (1000, 50000)
            },
            'fashion-apparel': {
                'sneakers': (1500, 8000),
                'running-shoes': (2000, 12000),
                'athletic-shoes': (1500, 10000),
                'casual-shoes': (1000, 6000),
                'training-shoes': (1500, 8000),
                'basketball-shoes': (2000, 12000),
                'soccer-cleats': (1500, 8000),
                'tennis-shoes': (1500, 8000),
                'hiking-boots': (2000, 12000),
                'slides': (500, 3000),
                'jeans': (800, 4000),
                't-shirts': (300, 1500),
                'blazers': (2000, 8000),
                'bags': (1000, 15000),
                'sunglasses': (500, 5000),
                'watches': (1000, 20000),
                'default': (500, 8000)
            },
            'home-living': {
                'sofa': (8000, 50000),
                'dining-table': (5000, 30000),
                'bed-frame': (3000, 25000),
                'dresser': (2000, 15000),
                'bookshelf': (1000, 8000),
                'coffee-table': (2000, 12000),
                'side-table': (1000, 5000),
                'chair': (1000, 8000),
                'lamp': (500, 3000),
                'mirror': (500, 3000),
                'appliances': (2000, 50000),
                'default': (500, 30000)
            },
            'books-education': {
                'books': (200, 2000),
                'e-readers': (5000, 15000),
                'memberships': (1000, 20000),
                'default': (200, 2000)
            },
            'sports-fitness': {
                'bikes': (15000, 100000),
                'dumbbells': (2000, 30000),
                'leggings': (1000, 8000),
                'fitness-trackers': (2000, 20000),
                'tennis-rackets': (3000, 25000),
                'yoga-mats': (500, 3000),
                'default': (500, 30000)
            },
            'beauty-personal-care': {
                'hair-tools': (2000, 40000),
                'skincare': (500, 30000),
                'toothbrushes': (1000, 20000),
                'facial-cleansers': (1000, 20000),
                'perfumes': (1000, 10000),
                'default': (500, 30000)
            },
            'automotive-tools': {
                'drills': (2000, 15000),
                'adapters': (1000, 5000),
                'dash-cams': (2000, 8000),
                'default': (1000, 15000)
            },
            'toys-games': {
                'lego': (1000, 80000),
                'gaming-consoles': (15000, 35000),
                'board-games': (500, 3000),
                'default': (500, 80000)
            },
            'health-wellness': {
                'smart-rings': (15000, 35000),
                'blenders': (5000, 50000),
                'espresso-machines': (15000, 40000),
                'default': (2000, 50000)
            },
            'garden-outdoor': {
                'grills': (15000, 40000),
                'coolers': (5000, 30000),
                'tents': (2000, 8000),
                'default': (2000, 40000)
            }
        }

        # Update prices for each product
        updated_count = 0
        for product in Product.objects.all():
            category_slug = product.category.slug
            product_name_lower = product.name.lower()
            
            # Determine the appropriate price range
            price_range = price_ranges.get(category_slug, {}).get('default', (500, 10000))
            
            # Check for specific product types
            for product_type, type_range in price_ranges.get(category_slug, {}).items():
                if product_type != 'default' and product_type in product_name_lower:
                    price_range = type_range
                    break
            
            # Generate a realistic price within the range
            min_price, max_price = price_range
            new_price = Decimal(str(random.randint(min_price, max_price)))
            
            # Add some variation to make prices more natural
            if random.random() > 0.7:
                new_price = new_price + Decimal(str(random.randint(99, 999)))
            
            # Update the product price
            old_price = product.price
            product.price = new_price
            
            # Update sale price if it exists (make it 10-30% off)
            if product.sale_price:
                discount_percentage = random.uniform(0.1, 0.3)
                new_sale_price = new_price * (1 - Decimal(str(discount_percentage)))
                product.sale_price = new_sale_price.quantize(Decimal('0.01'))
            
            product.save()
            updated_count += 1
            
            if updated_count % 50 == 0:
                self.stdout.write(f'Updated {updated_count} products...')
        
        self.stdout.write(
            self.style.SUCCESS(f'Successfully updated prices for {updated_count} products!')
        )
        self.stdout.write('All product prices are now more realistic and reasonable.')
