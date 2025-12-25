import os
import random
from django.core.files import File
from requirements.models import Product, Category, ProductImage

def create_products():
    # Get or create categories
    categories = {
        'Electronics': {
            'description': 'Electronic devices and accessories',
            'products': [
                ('Smartphone', 'Latest smartphone with advanced features', 699.99, 599.99, 100, 'PHN001'),
                ('Laptop', 'High-performance laptop for work and play', 1299.99, 1099.99, 50, 'LPT001'),
                ('Headphones', 'Noise-cancelling wireless headphones', 299.99, 249.99, 75, 'HP001'),
                ('Smart Watch', 'Feature-rich smartwatch with health tracking', 199.99, 179.99, 60, 'WTCH001'),
                ('Bluetooth Speaker', 'Portable speaker with 24h battery life', 129.99, 99.99, 90, 'SPK001'),
                ('Tablet', '10-inch tablet with stylus support', 499.99, 449.99, 40, 'TAB001'),
                ('Wireless Earbuds', 'True wireless earbuds with charging case', 149.99, 129.99, 85, 'BUD001'),
                ('External SSD', '1TB portable SSD with USB-C', 199.99, 179.99, 65, 'SSD001'),
            ]
        },
        'Clothing': {
            'description': 'Fashion and apparel',
            'products': [
                ('T-Shirt', '100% cotton crew neck t-shirt', 29.99, 24.99, 200, 'TSH001'),
                ('Jeans', 'Slim fit denim jeans', 79.99, 69.99, 150, 'JNS001'),
                ('Hoodie', 'Cozy fleece hoodie with drawstring hood', 59.99, 49.99, 100, 'HD001'),
                ('Running Shorts', 'Lightweight running shorts with pockets', 39.99, 34.99, 120, 'SHT001'),
                ('Winter Jacket', 'Waterproof winter jacket with insulation', 199.99, 179.99, 60, 'JKT001'),
                ('Dress Shirt', 'Classic fit formal dress shirt', 49.99, 44.99, 90, 'SHRT001'),
                ('Yoga Pants', 'High-waisted yoga pants with pocket', 54.99, 44.99, 85, 'YP001'),
                ('Swim Trunks', 'Quick-dry swim trunks with liner', 34.99, 29.99, 70, 'SWM001'),
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
            ]
        }
    }

    # Base media path
    media_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'media', 'products')
    
    # Get all image files
    image_files = [f for f in os.listdir(media_path) if f.endswith(('.jpg', '.jpeg', '.png', '.webp'))]
    
    # Create categories and products
    for category_name, data in categories.items():
        # Get or create category
        category, created = Category.objects.get_or_create(
            name=category_name,
            defaults={'description': data['description'], 'slug': category_name.lower().replace(' ', '-')}
        )
        
        print(f"\nProcessing category: {category_name}")
        
        # Create products for this category
        for product_data in data['products']:
            name, description, price, sale_price, stock_quantity, sku = product_data
            
            # Check if product already exists
            if Product.objects.filter(sku=sku).exists():
                print(f"Product {name} ({sku}) already exists, skipping...")
                continue
            
            # Select a random image for the product
            if not image_files:
                print("No more images available in the media folder")
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
            
            # Save product first to get ID
            product.save()
            
            # Add main product image
            image_path = os.path.join(media_path, image_file)
            with open(image_path, 'rb') as f:
                product.image.save(image_file, File(f), save=True)
            
            # Add additional images (1-3 per product)
            num_additional = random.randint(1, min(3, len(image_files)))
            for _ in range(num_additional):
                if not image_files:
                    break
                    
                extra_image = random.choice(image_files)
                image_files.remove(extra_image)
                
                product_image = ProductImage(
                    product=product,
                    alt_text=f"{name} - Additional Image {_ + 1}",
                    is_primary=False,
                    order=_ + 1
                )
                
                with open(os.path.join(media_path, extra_image), 'rb') as f:
                    product_image.image.save(extra_image, File(f), save=True)
                
                product_image.save()
            
            print(f"Created product: {name} (SKU: {sku})")

if __name__ == '__main__':
    import django
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'kv10.settings')
    django.setup()
    create_products()
