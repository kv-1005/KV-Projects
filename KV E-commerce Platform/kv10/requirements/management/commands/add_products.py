import os
import random
from django.core.management.base import BaseCommand
from django.core.files import File
from requirements.models import Product, Category, ProductImage

class Command(BaseCommand):
    help = 'Add sample products to the database'

    def handle(self, *args, **options):
        # Get or create categories
        categories = {
            'Electronics': {
                'description': 'Electronic devices and accessories',
                'products': [
                    ('Smartphone', 'Latest smartphone with advanced features', 699.99, 599.99, 100, 'PHN001'),
                    ('Laptop', 'High-performance laptop for work and play', 1299.99, 1099.99, 50, 'LPT001'),
                    ('Headphones', 'Noise-cancelling wireless headphones', 299.99, 249.99, 75, 'HP001'),
                    ('Smart Watch', 'Feature-rich smartwatch with health tracking', 249.99, 199.99, 60, 'WTCH001'),
                    ('Tablet', '10.5" HD display tablet with stylus', 399.99, 349.99, 45, 'TAB001'),
                    ('Wireless Earbuds', 'True wireless earbuds with charging case', 129.99, 99.99, 85, 'BUD001'),
                    ('Bluetooth Speaker', 'Portable waterproof speaker', 89.99, 69.99, 65, 'SPK001'),
                    ('Gaming Console', 'Next-gen gaming console', 499.99, 449.99, 30, 'GAME001'),
                    ('4K Smart TV', '55" 4K Ultra HD Smart LED TV', 799.99, 699.99, 25, 'TV001'),
                    ('Digital Camera', 'Mirrorless camera with 4K video', 899.99, 799.99, 35, 'CAM001')
                ]
            },
            'Clothing': {
                'description': 'Fashion and apparel',
                'products': [
                    ('T-Shirt', '100% cotton crew neck t-shirt', 29.99, 24.99, 200, 'TSH001'),
                    ('Jeans', 'Slim fit denim jeans', 79.99, 69.99, 150, 'JNS001'),
                    ('Hoodie', 'Cozy fleece hoodie with drawstring hood', 59.99, 49.99, 100, 'HD001'),
                    ('Dress Shirt', 'Classic fit cotton dress shirt', 49.99, 39.99, 120, 'SHIRT001'),
                    ('Running Shorts', 'Lightweight running shorts with pockets', 34.99, 29.99, 90, 'SHORTS001'),
                    ('Winter Jacket', 'Waterproof insulated winter jacket', 199.99, 169.99, 40, 'JKT001'),
                    ('Yoga Pants', 'High-waisted yoga pants with pocket', 54.99, 44.99, 85, 'YP001'),
                    ('Leather Jacket', 'Genuine leather biker jacket', 299.99, 249.99, 30, 'LJ001'),
                    ('Swim Trunks', 'Quick-dry swim trunks with liner', 39.99, 34.99, 70, 'SWIM001'),
                    ('Sneakers', 'Casual running shoes', 89.99, 74.99, 65, 'SNKRS001')
                ]
            },
            'Books': {
                'description': 'Books and publications',
                'products': [
                    ('Atomic Habits', 'Build good habits and break bad ones', 16.99, 14.99, 50, 'BK001'),
                    ('The Psychology of Money', 'Timeless lessons on wealth', 19.99, 17.99, 45, 'BK002'),
                    ('Project Hail Mary', 'Science fiction novel by Andy Weir', 14.99, 12.99, 60, 'BK003'),
                    ('The Midnight Library', 'Novel by Matt Haig', 15.99, 13.99, 55, 'BK004'),
                    ('Educated', 'Memoir by Tara Westover', 18.99, 15.99, 40, 'BK005'),
                    ('The Song of Achilles', 'Novel by Madeline Miller', 16.99, 14.99, 50, 'BK006'),
                    ('Dune', 'Science fiction novel by Frank Herbert', 12.99, 10.99, 65, 'BK007'),
                    ('The Hobbit', 'Fantasy novel by J.R.R. Tolkien', 13.99, 11.99, 70, 'BK008'),
                    ('1984', 'Dystopian novel by George Orwell', 10.99, 9.99, 80, 'BK009'),
                    ('The Great Gatsby', 'Classic novel by F. Scott Fitzgerald', 11.99, 9.99, 75, 'BK010')
                ]
            },
            'Home & Kitchen': {
                'description': 'Home appliances and kitchenware',
                'products': [
                    ('Air Fryer', '5.8QT digital air fryer', 129.99, 99.99, 40, 'AF001'),
                    ('Coffee Maker', '12-cup programmable coffee maker', 89.99, 79.99, 55, 'CF001'),
                    ('Blender', 'High-speed blender with 64oz pitcher', 79.99, 69.99, 60, 'BL001'),
                    ('Knife Set', '15-piece premium knife set', 149.99, 129.99, 35, 'KN001'),
                    ('Stand Mixer', '5.5qt tilt-head stand mixer', 329.99, 299.99, 25, 'MX001'),
                    ('Food Processor', '14-cup food processor', 199.99, 179.99, 30, 'FP001'),
                    ('Toaster Oven', '6-slice convection toaster oven', 119.99, 99.99, 45, 'TO001'),
                    ('Rice Cooker', '10-cup digital rice cooker', 59.99, 49.99, 50, 'RC001'),
                    ('Cookware Set', '10-piece non-stick cookware set', 199.99, 179.99, 30, 'CK001'),
                    ('Air Purifier', 'HEPA air purifier for large rooms', 249.99, 199.99, 35, 'AP001')
                ]
            },
            'Sports & Outdoors': {
                'description': 'Sports equipment and outdoor gear',
                'products': [
                    ('Yoga Mat', '6mm thick non-slip yoga mat', 39.99, 34.99, 80, 'YM001'),
                    ('Dumbbell Set', 'Adjustable dumbbell set (5-25lbs)', 199.99, 179.99, 30, 'DB001'),
                    ('Tent', '4-person camping tent', 149.99, 129.99, 25, 'TENT001'),
                    ('Hiking Backpack', '65L hiking backpack with rain cover', 129.99, 109.99, 40, 'BP001'),
                    ('Running Shoes', 'Cushioned running shoes', 119.99, 99.99, 60, 'RS001'),
                    ('Bicycle', '21-speed mountain bike', 499.99, 449.99, 20, 'BIKE001'),
                    ('Fitness Tracker', 'Waterproof fitness tracker', 79.99, 69.99, 70, 'FT001'),
                    ('Camping Stove', 'Portable butane camping stove', 59.99, 49.99, 45, 'STV001'),
                    ('Treadmill', 'Folding treadmill with LCD display', 599.99, 499.99, 15, 'TM001'),
                    ('Kayak', '2-person inflatable kayak', 299.99, 249.99, 18, 'KY001')
                ]
            },
            'Beauty & Personal Care': {
                'description': 'Beauty and personal care products',
                'products': [
                    ('Electric Toothbrush', 'Rechargeable electric toothbrush', 99.99, 79.99, 90, 'TB001'),
                    ('Hair Dryer', 'Ionic hair dryer with diffuser', 89.99, 69.99, 60, 'HD001'),
                    ('Facial Cleanser', 'Gentle foaming facial cleanser', 24.99, 19.99, 120, 'FC001'),
                    ('Moisturizer', '24-hour hydration moisturizer', 34.99, 29.99, 100, 'MZ001'),
                    ('Perfume', 'Eau de parfum 100ml', 89.99, 79.99, 50, 'PF001'),
                    ('Makeup Set', 'Complete makeup kit with brushes', 129.99, 99.99, 40, 'MK001'),
                    ('Hair Straightener', 'Ceramic flat iron with adjustable temp', 79.99, 59.99, 55, 'HS001'),
                    ('Electric Shaver', 'Wet/dry electric shaver', 149.99, 129.99, 45, 'ES001'),
                    ('Sunscreen', 'Broad spectrum SPF 50+', 19.99, 16.99, 150, 'SS001'),
                    ('Skincare Set', 'Complete daily skincare routine', 149.99, 129.99, 35, 'SK001')
                ]
            }
        }

        # Base media path
        media_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))), 'media', 'products')
        
        # Get all image files
        try:
            image_files = [f for f in os.listdir(media_path) if f.endswith(('.jpg', '.jpeg', '.png', '.webp'))]
        except FileNotFoundError:
            self.stderr.write(self.style.ERROR(f'Media directory not found at: {media_path}'))
            return
        
        if not image_files:
            self.stderr.write(self.style.ERROR('No image files found in media directory'))
            return
            
        self.stdout.write(self.style.SUCCESS(f'Found {len(image_files)} image files'))
        
        # Create categories and products
        for category_name, data in categories.items():
            # Get or create category
            category, created = Category.objects.get_or_create(
                name=category_name,
                defaults={'description': data['description'], 'slug': category_name.lower().replace(' ', '-')}
            )
            
            self.stdout.write(self.style.SUCCESS(f'\nProcessing category: {category_name}'))
            
            # Create products for this category
            for product_data in data['products']:
                name, description, price, sale_price, stock_quantity, sku = product_data
                
                # Check if product already exists
                if Product.objects.filter(sku=sku).exists():
                    self.stdout.write(self.style.WARNING(f'Product {name} ({sku}) already exists, skipping...'))
                    continue
                
                # Select a random image for the product
                if not image_files:
                    self.stderr.write(self.style.ERROR('No more images available in the media folder'))
                    return
                    
                image_file = random.choice(image_files)
                image_files.remove(image_file)  # Remove used image to avoid duplicates
                
                # Create product
                product = Product(
                    category=category,
                    name=name,
                    description=description,
                    price=price,
                    sale_price=sale_price,
                    stock_quantity=stock_quantity,
                    sku=sku,
                    is_active=True,
                    is_featured=random.choice([True, False])
                )
                
                try:
                    # Save product first to get ID
                    product.save()
                    
                    # Add main product image
                    image_path = os.path.join(media_path, image_file)
                    with open(image_path, 'rb') as f:
                        product.image.save(image_file, File(f), save=True)
                    
                    # Add additional images (1-2 per product)
                    num_additional = random.randint(1, min(2, len(image_files)))
                    for i in range(num_additional):
                        if not image_files:
                            break
                            
                        extra_image = random.choice(image_files)
                        image_files.remove(extra_image)
                        
                        product_image = ProductImage(
                            product=product,
                            alt_text=f"{name} - Additional Image {i + 1}",
                            is_primary=False,
                            order=i + 1
                        )
                        
                        with open(os.path.join(media_path, extra_image), 'rb') as f:
                            product_image.image.save(extra_image, File(f), save=True)
                        
                        product_image.save()
                    
                    self.stdout.write(self.style.SUCCESS(f'Created product: {name} (SKU: {sku})'))
                    
                except Exception as e:
                    self.stderr.write(self.style.ERROR(f'Error creating product {name}: {str(e)}'))
                    continue
        
        self.stdout.write(self.style.SUCCESS('\nFinished adding products!'))
