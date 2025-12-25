from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.core.files.base import ContentFile
from requirements.models import Category, Product, Customer
from decimal import Decimal
import requests
import os
import random
from urllib.parse import urlparse

class Command(BaseCommand):
    help = 'Create massive amount of product data for the e-commerce store'

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
        self.stdout.write('Creating massive product data...')
        
        # Create comprehensive categories
        categories_data = [
            {
                'name': 'Electronics & Gadgets',
                'slug': 'electronics-gadgets',
                'description': 'Latest electronic gadgets, smartphones, laptops, and accessories'
            },
            {
                'name': 'Fashion & Apparel',
                'slug': 'fashion-apparel',
                'description': 'Trendy clothing, shoes, bags, and fashion accessories'
            },
            {
                'name': 'Home & Living',
                'slug': 'home-living',
                'description': 'Furniture, decor, kitchen appliances, and home essentials'
            },
            {
                'name': 'Books & Education',
                'slug': 'books-education',
                'description': 'Books, educational materials, and learning resources'
            },
            {
                'name': 'Sports & Fitness',
                'slug': 'sports-fitness',
                'description': 'Sports equipment, fitness gear, and activewear'
            },
            {
                'name': 'Beauty & Personal Care',
                'slug': 'beauty-personal-care',
                'description': 'Skincare, makeup, haircare, and personal hygiene products'
            },
            {
                'name': 'Automotive & Tools',
                'slug': 'automotive-tools',
                'description': 'Car accessories, tools, and automotive supplies'
            },
            {
                'name': 'Toys & Games',
                'slug': 'toys-games',
                'description': 'Toys, board games, puzzles, and entertainment items'
            },
            {
                'name': 'Health & Wellness',
                'slug': 'health-wellness',
                'description': 'Health supplements, medical devices, and wellness products'
            },
            {
                'name': 'Garden & Outdoor',
                'slug': 'garden-outdoor',
                'description': 'Gardening tools, outdoor furniture, and camping gear'
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
        
        # Massive product data
        products_data = [
            # Electronics & Gadgets (50 products)
            {
                'name': 'iPhone 15 Pro Max',
                'slug': 'iphone-15-pro-max',
                'category': categories['electronics-gadgets'],
                'description': 'Latest iPhone with A17 Pro chip, titanium design, and advanced camera system.',
                'price': Decimal('89999.00'),
                'sale_price': Decimal('79999.00'),
                'stock_quantity': 25,
                'sku': 'IPH15PM-001',
                'is_featured': True
            },
            {
                'name': 'Samsung Galaxy S24 Ultra',
                'slug': 'samsung-galaxy-s24-ultra',
                'category': categories['electronics-gadgets'],
                'description': 'Premium Android flagship with S Pen, 200MP camera, and AI features.',
                'price': Decimal('84999.00'),
                'stock_quantity': 30,
                'sku': 'SGS24U-001',
                'is_featured': True
            },
            {
                'name': 'MacBook Pro 16-inch M3',
                'slug': 'macbook-pro-16-m3',
                'category': categories['electronics-gadgets'],
                'description': 'Powerful laptop with M3 chip, 16-inch Liquid Retina display, and up to 22 hours battery.',
                'price': Decimal('189999.00'),
                'sale_price': Decimal('169999.00'),
                'stock_quantity': 15,
                'sku': 'MBP16M3-001',
                'is_featured': True
            },
            {
                'name': 'Dell XPS 15 Laptop',
                'slug': 'dell-xps-15-laptop',
                'category': categories['electronics-gadgets'],
                'description': 'Premium Windows laptop with 4K OLED display and Intel Core i9 processor.',
                'price': Decimal('129999.00'),
                'stock_quantity': 20,
                'sku': 'DXP15-001'
            },
            {
                'name': 'Sony WH-1000XM5 Headphones',
                'slug': 'sony-wh-1000xm5-headphones',
                'category': categories['electronics-gadgets'],
                'description': 'Industry-leading noise-canceling wireless headphones with 30-hour battery life.',
                'price': Decimal('24999.00'),
                'sale_price': Decimal('19999.00'),
                'stock_quantity': 50,
                'sku': 'SWHXM5-001',
                'is_featured': True
            },
            {
                'name': 'Apple Watch Series 9',
                'slug': 'apple-watch-series-9',
                'category': categories['electronics-gadgets'],
                'description': 'Advanced smartwatch with health monitoring, GPS, and cellular connectivity.',
                'price': Decimal('39999.00'),
                'stock_quantity': 40,
                'sku': 'AWS9-001'
            },
            {
                'name': 'iPad Pro 12.9-inch M2',
                'slug': 'ipad-pro-12-9-m2',
                'category': categories['electronics-gadgets'],
                'description': 'Professional tablet with M2 chip, Liquid Retina XDR display, and Apple Pencil support.',
                'price': Decimal('79999.00'),
                'stock_quantity': 25,
                'sku': 'IPP12M2-001'
            },
            {
                'name': 'Samsung 65-inch QLED 4K TV',
                'slug': 'samsung-65-qled-4k-tv',
                'category': categories['electronics-gadgets'],
                'description': 'Premium QLED TV with Quantum HDR, Smart TV features, and Alexa built-in.',
                'price': Decimal('99999.00'),
                'sale_price': Decimal('84999.00'),
                'stock_quantity': 10,
                'sku': 'S65QLED-001',
                'is_featured': True
            },
            {
                'name': 'DJI Mini 3 Pro Drone',
                'slug': 'dji-mini-3-pro-drone',
                'category': categories['electronics-gadgets'],
                'description': 'Ultra-lightweight drone with 4K camera, obstacle avoidance, and 34-minute flight time.',
                'price': Decimal('59999.00'),
                'stock_quantity': 15,
                'sku': 'DJIM3P-001'
            },
            {
                'name': 'GoPro Hero 11 Black',
                'slug': 'gopro-hero-11-black',
                'category': categories['electronics-gadgets'],
                'description': 'Action camera with 5.3K video, HyperSmooth 5.0 stabilization, and waterproof design.',
                'price': Decimal('29999.00'),
                'stock_quantity': 30,
                'sku': 'GPH11B-001'
            },
            
            # Fashion & Apparel (60 products)
            {
                'name': 'Nike Air Jordan 1 Retro',
                'slug': 'nike-air-jordan-1-retro',
                'category': categories['fashion-apparel'],
                'description': 'Classic basketball sneakers with premium leather construction and iconic design.',
                'price': Decimal('12999.00'),
                'sale_price': Decimal('9999.00'),
                'stock_quantity': 100,
                'sku': 'NAJ1R-001',
                'is_featured': True
            },
            {
                'name': 'Adidas Ultraboost 22',
                'slug': 'adidas-ultraboost-22',
                'category': categories['fashion-apparel'],
                'description': 'Premium running shoes with responsive Boost midsole and Primeknit upper.',
                'price': Decimal('15999.00'),
                'stock_quantity': 80,
                'sku': 'AUB22-001'
            },
            {
                'name': 'Levi\'s 501 Original Jeans',
                'slug': 'levis-501-original-jeans',
                'category': categories['fashion-apparel'],
                'description': 'Timeless straight-fit jeans with classic 5-pocket design and durable denim.',
                'price': Decimal('2999.00'),
                'sale_price': Decimal('1999.00'),
                'stock_quantity': 200,
                'sku': 'L501-001',
                'is_featured': True
            },
            {
                'name': 'Zara Oversized Blazer',
                'slug': 'zara-oversized-blazer',
                'category': categories['fashion-apparel'],
                'description': 'Trendy oversized blazer with structured shoulders and modern silhouette.',
                'price': Decimal('4999.00'),
                'stock_quantity': 75,
                'sku': 'ZOB-001'
            },
            {
                'name': 'H&M Cotton T-Shirt Pack',
                'slug': 'hm-cotton-tshirt-pack',
                'category': categories['fashion-apparel'],
                'description': 'Pack of 3 comfortable cotton t-shirts in assorted colors.',
                'price': Decimal('999.00'),
                'stock_quantity': 300,
                'sku': 'HMCTP-001'
            },
            {
                'name': 'Michael Kors Tote Bag',
                'slug': 'michael-kors-tote-bag',
                'category': categories['fashion-apparel'],
                'description': 'Luxury leather tote bag with gold-tone hardware and spacious interior.',
                'price': Decimal('12999.00'),
                'sale_price': Decimal('9999.00'),
                'stock_quantity': 25,
                'sku': 'MKTB-001',
                'is_featured': True
            },
            {
                'name': 'Ray-Ban Aviator Classic',
                'slug': 'ray-ban-aviator-classic',
                'category': categories['fashion-apparel'],
                'description': 'Iconic aviator sunglasses with gold frame and green lenses.',
                'price': Decimal('6999.00'),
                'stock_quantity': 50,
                'sku': 'RBAC-001'
            },
            {
                'name': 'Casio G-Shock Watch',
                'slug': 'casio-g-shock-watch',
                'category': categories['fashion-apparel'],
                'description': 'Durable digital watch with shock resistance, water resistance, and multiple functions.',
                'price': Decimal('3999.00'),
                'stock_quantity': 100,
                'sku': 'CGSW-001'
            },
            {
                'name': 'Uniqlo Heattech Long Sleeve',
                'slug': 'uniqlo-heattech-long-sleeve',
                'category': categories['fashion-apparel'],
                'description': 'Thermal long sleeve shirt with Heattech technology for warmth and comfort.',
                'price': Decimal('1499.00'),
                'stock_quantity': 150,
                'sku': 'UHLS-001'
            },
            {
                'name': 'Converse Chuck Taylor All Star',
                'slug': 'converse-chuck-taylor-all-star',
                'category': categories['fashion-apparel'],
                'description': 'Classic canvas sneakers with vulcanized rubber sole and timeless design.',
                'price': Decimal('2999.00'),
                'sale_price': Decimal('1999.00'),
                'stock_quantity': 120,
                'sku': 'CCTAS-001'
            },
            
            # Home & Living (40 products)
            {
                'name': 'IKEA MALM Bed Frame',
                'slug': 'ikea-malm-bed-frame',
                'category': categories['home-living'],
                'description': 'Modern bed frame with clean lines and under-bed storage drawers.',
                'price': Decimal('12999.00'),
                'stock_quantity': 20,
                'sku': 'IMBF-001',
                'is_featured': True
            },
            {
                'name': 'Philips Hue Smart Bulb Starter Kit',
                'slug': 'philips-hue-smart-bulb-starter-kit',
                'category': categories['home-living'],
                'description': 'Smart lighting system with 3 color bulbs, bridge, and app control.',
                'price': Decimal('6999.00'),
                'sale_price': Decimal('4999.00'),
                'stock_quantity': 30,
                'sku': 'PHSK-001'
            },
            {
                'name': 'KitchenAid Stand Mixer',
                'slug': 'kitchenaid-stand-mixer',
                'category': categories['home-living'],
                'description': 'Professional stand mixer with 10-speed motor and tilt-head design.',
                'price': Decimal('24999.00'),
                'stock_quantity': 15,
                'sku': 'KASM-001',
                'is_featured': True
            },
            {
                'name': 'Dyson V15 Detect Vacuum',
                'slug': 'dyson-v15-detect-vacuum',
                'category': categories['home-living'],
                'description': 'Cordless vacuum with laser dust detection and 60-minute runtime.',
                'price': Decimal('39999.00'),
                'sale_price': Decimal('29999.00'),
                'stock_quantity': 10,
                'sku': 'DV15D-001'
            },
            {
                'name': 'West Elm Sofa',
                'slug': 'west-elm-sofa',
                'category': categories['home-living'],
                'description': 'Modern 3-seater sofa with clean lines and comfortable fabric upholstery.',
                'price': Decimal('69999.00'),
                'stock_quantity': 8,
                'sku': 'WES-001'
            },
            {
                'name': 'Nespresso Vertuo Coffee Machine',
                'slug': 'nespresso-vertuo-coffee-machine',
                'category': categories['home-living'],
                'description': 'Automatic coffee machine with barcode recognition and 19-bar pressure.',
                'price': Decimal('15999.00'),
                'stock_quantity': 25,
                'sku': 'NVCM-001'
            },
            {
                'name': 'Samsung 4-Door French Door Refrigerator',
                'slug': 'samsung-4-door-french-door-refrigerator',
                'category': categories['home-living'],
                'description': 'Large capacity refrigerator with Family Hub touchscreen and WiFi connectivity.',
                'price': Decimal('99999.00'),
                'stock_quantity': 5,
                'sku': 'S4DFDR-001'
            },
            {
                'name': 'LG Front Load Washer',
                'slug': 'lg-front-load-washer',
                'category': categories['home-living'],
                'description': 'High-efficiency front load washer with Steam function and WiFi control.',
                'price': Decimal('39999.00'),
                'stock_quantity': 12,
                'sku': 'LFLW-001'
            },
            {
                'name': 'Crate & Barrel Dining Table',
                'slug': 'crate-barrel-dining-table',
                'category': categories['home-living'],
                'description': 'Solid wood dining table with clean modern design, seats 6-8 people.',
                'price': Decimal('29999.00'),
                'stock_quantity': 10,
                'sku': 'CBTDT-001'
            },
            {
                'name': 'Target Threshold Throw Pillows',
                'slug': 'target-threshold-throw-pillows',
                'category': categories['home-living'],
                'description': 'Set of 4 decorative throw pillows with removable covers.',
                'price': Decimal('1999.00'),
                'stock_quantity': 50,
                'sku': 'TTTP-001'
            },
            
            # Books & Education (30 products)
            {
                'name': 'The Psychology of Money',
                'slug': 'psychology-of-money',
                'category': categories['books-education'],
                'description': 'Timeless lessons on wealth, greed, and happiness by Morgan Housel.',
                'price': Decimal('399.00'),
                'sale_price': Decimal('299.00'),
                'stock_quantity': 100,
                'sku': 'POM-001',
                'is_featured': True
            },
            {
                'name': 'Atomic Habits by James Clear',
                'slug': 'atomic-habits-james-clear',
                'category': categories['books-education'],
                'description': 'Proven way to build good habits and break bad ones.',
                'price': Decimal('499.00'),
                'stock_quantity': 150,
                'sku': 'AHJC-001'
            },
            {
                'name': 'Python Crash Course',
                'slug': 'python-crash-course',
                'category': categories['books-education'],
                'description': 'A hands-on, project-based introduction to programming.',
                'price': Decimal('599.00'),
                'stock_quantity': 75,
                'sku': 'PCC-001'
            },
            {
                'name': 'Kindle Paperwhite',
                'slug': 'kindle-paperwhite',
                'category': categories['books-education'],
                'description': 'Waterproof e-reader with 6.8-inch display and weeks of battery life.',
                'price': Decimal('9999.00'),
                'sale_price': Decimal('7999.00'),
                'stock_quantity': 40,
                'sku': 'KPW-001'
            },
            {
                'name': 'MasterClass Annual Membership',
                'slug': 'masterclass-annual-membership',
                'category': categories['books-education'],
                'description': 'Access to 100+ classes from world-class instructors.',
                'price': Decimal('12999.00'),
                'stock_quantity': 1000,
                'sku': 'MAM-001'
            },
            
            # Sports & Fitness (35 products)
            {
                'name': 'Peloton Bike+',
                'slug': 'peloton-bike-plus',
                'category': categories['sports-fitness'],
                'description': 'Premium indoor cycling bike with 24-inch HD touchscreen and live classes.',
                'price': Decimal('199999.00'),
                'stock_quantity': 5,
                'sku': 'PB+-001',
                'is_featured': True
            },
            {
                'name': 'Bowflex SelectTech Dumbbells',
                'slug': 'bowflex-selecttech-dumbbells',
                'category': categories['sports-fitness'],
                'description': 'Adjustable dumbbells that replace 15 sets of weights in one.',
                'price': Decimal('24999.00'),
                'stock_quantity': 20,
                'sku': 'BSD-001'
            },
            {
                'name': 'Lululemon Align Leggings',
                'slug': 'lululemon-align-leggings',
                'category': categories['sports-fitness'],
                'description': 'Ultra-soft, lightweight leggings perfect for yoga and everyday wear.',
                'price': Decimal('6999.00'),
                'stock_quantity': 60,
                'sku': 'LAL-001'
            },
            {
                'name': 'Fitbit Charge 6',
                'slug': 'fitbit-charge-6',
                'category': categories['sports-fitness'],
                'description': 'Advanced fitness tracker with heart rate monitoring and GPS.',
                'price': Decimal('12999.00'),
                'sale_price': Decimal('9999.00'),
                'stock_quantity': 45,
                'sku': 'FC6-001'
            },
            {
                'name': 'Wilson Pro Staff Tennis Racket',
                'slug': 'wilson-pro-staff-tennis-racket',
                'category': categories['sports-fitness'],
                'description': 'Professional tennis racket with precision engineering and control.',
                'price': Decimal('15999.00'),
                'stock_quantity': 25,
                'sku': 'WPSTR-001'
            },
            
            # Beauty & Personal Care (25 products)
            {
                'name': 'Dyson Airwrap Multi-Styler',
                'slug': 'dyson-airwrap-multi-styler',
                'category': categories['beauty-personal-care'],
                'description': 'Revolutionary hair styling tool that uses air to curl, wave, and smooth.',
                'price': Decimal('29999.00'),
                'sale_price': Decimal('24999.00'),
                'stock_quantity': 15,
                'sku': 'DAMS-001',
                'is_featured': True
            },
            {
                'name': 'La Mer Moisturizing Cream',
                'slug': 'la-mer-moisturizing-cream',
                'category': categories['beauty-personal-care'],
                'description': 'Luxury moisturizing cream with Miracle Broth and sea kelp.',
                'price': Decimal('24999.00'),
                'stock_quantity': 20,
                'sku': 'LMMC-001'
            },
            {
                'name': 'Oral-B iO Series 9 Toothbrush',
                'slug': 'oral-b-io-series-9-toothbrush',
                'category': categories['beauty-personal-care'],
                'description': 'Smart electric toothbrush with AI recognition and 3D tracking.',
                'price': Decimal('15999.00'),
                'stock_quantity': 30,
                'sku': 'OBIOS9-001'
            },
            {
                'name': 'Foreo Luna 3 Facial Cleanser',
                'slug': 'foreo-luna-3-facial-cleanser',
                'category': categories['beauty-personal-care'],
                'description': 'Sonic facial cleansing device with T-Sonic technology.',
                'price': Decimal('12999.00'),
                'stock_quantity': 25,
                'sku': 'FL3FC-001'
            },
            {
                'name': 'Chanel N°5 Eau de Parfum',
                'slug': 'chanel-no5-eau-de-parfum',
                'category': categories['beauty-personal-care'],
                'description': 'Iconic fragrance with notes of rose, jasmine, and vanilla.',
                'price': Decimal('6999.00'),
                'stock_quantity': 40,
                'sku': 'CN5EDP-001'
            },
            
            # Automotive & Tools (20 products)
            {
                'name': 'DeWalt 20V MAX Cordless Drill',
                'slug': 'dewalt-20v-max-cordless-drill',
                'category': categories['automotive-tools'],
                'description': 'Professional cordless drill with brushless motor and 2-speed transmission.',
                'price': Decimal('6999.00'),
                'stock_quantity': 35,
                'sku': 'D20MCD-001'
            },
            {
                'name': 'CarPlay Wireless Adapter',
                'slug': 'carplay-wireless-adapter',
                'category': categories['automotive-tools'],
                'description': 'Wireless CarPlay adapter for older vehicles without built-in CarPlay.',
                'price': Decimal('2999.00'),
                'stock_quantity': 50,
                'sku': 'CWA-001'
            },
            {
                'name': 'Dash Cam Front & Rear',
                'slug': 'dash-cam-front-rear',
                'category': categories['automotive-tools'],
                'description': 'Dual dash cam with 4K front camera and 1080p rear camera.',
                'price': Decimal('4999.00'),
                'stock_quantity': 40,
                'sku': 'DCFR-001'
            },
            
            # Toys & Games (15 products)
            {
                'name': 'LEGO Star Wars Millennium Falcon',
                'slug': 'lego-star-wars-millennium-falcon',
                'category': categories['toys-games'],
                'description': 'Ultimate collector series Millennium Falcon with 7,500+ pieces.',
                'price': Decimal('59999.00'),
                'stock_quantity': 10,
                'sku': 'LSWMF-001',
                'is_featured': True
            },
            {
                'name': 'Nintendo Switch OLED',
                'slug': 'nintendo-switch-oled',
                'category': categories['toys-games'],
                'description': 'Gaming console with 7-inch OLED screen and enhanced audio.',
                'price': Decimal('24999.00'),
                'stock_quantity': 25,
                'sku': 'NSO-001'
            },
            {
                'name': 'Catan Board Game',
                'slug': 'catan-board-game',
                'category': categories['toys-games'],
                'description': 'Award-winning strategy board game for 3-4 players.',
                'price': Decimal('1499.00'),
                'stock_quantity': 60,
                'sku': 'CBG-001'
            },
            
            # Health & Wellness (15 products)
            {
                'name': 'Oura Ring Gen 3',
                'slug': 'oura-ring-gen-3',
                'category': categories['health-wellness'],
                'description': 'Smart ring that tracks sleep, activity, and recovery with advanced sensors.',
                'price': Decimal('24999.00'),
                'stock_quantity': 20,
                'sku': 'ORG3-001'
            },
            {
                'name': 'Vitamix Professional Series 750',
                'slug': 'vitamix-professional-series-750',
                'category': categories['health-wellness'],
                'description': 'Professional-grade blender with 10 variable speeds and pulse feature.',
                'price': Decimal('39999.00'),
                'stock_quantity': 15,
                'sku': 'VPS750-001'
            },
            {
                'name': 'Breville BES870XL Espresso Machine',
                'slug': 'breville-bes870xl-espresso-machine',
                'category': categories['health-wellness'],
                'description': 'Semi-automatic espresso machine with built-in grinder and steam wand.',
                'price': Decimal('29999.00'),
                'stock_quantity': 12,
                'sku': 'BBES870XL-001'
            },
            
            # Garden & Outdoor (10 products)
            {
                'name': 'Weber Spirit II E-310 Gas Grill',
                'slug': 'weber-spirit-ii-e-310-gas-grill',
                'category': categories['garden-outdoor'],
                'description': '3-burner gas grill with GS4 grilling system and porcelain-enameled grates.',
                'price': Decimal('29999.00'),
                'stock_quantity': 8,
                'sku': 'WS2E310-001'
            },
            {
                'name': 'Yeti Tundra 65 Cooler',
                'slug': 'yeti-tundra-65-cooler',
                'category': categories['garden-outdoor'],
                'description': 'Premium rotomolded cooler with 65-quart capacity and bear-resistant design.',
                'price': Decimal('24999.00'),
                'stock_quantity': 15,
                'sku': 'YT65C-001'
            },
            {
                'name': 'Coleman Sundome 4-Person Tent',
                'slug': 'coleman-sundome-4-person-tent',
                'category': categories['garden-outdoor'],
                'description': 'Weather-resistant tent with easy setup and spacious interior.',
                'price': Decimal('2999.00'),
                'stock_quantity': 30,
                'sku': 'CS4PT-001'
            }
        ]
        
        # Generate additional products with variations
        additional_products = []
        
        # Electronics variations
        electronics_brands = ['Apple', 'Samsung', 'Sony', 'LG', 'Bose', 'JBL', 'Canon', 'Nikon', 'Microsoft', 'Google']
        electronics_types = ['Smartphone', 'Laptop', 'Tablet', 'Headphones', 'Speaker', 'Camera', 'Monitor', 'Keyboard', 'Mouse', 'Webcam']
        
        for i in range(50):
            brand = random.choice(electronics_brands)
            product_type = random.choice(electronics_types)
            name = f"{brand} {product_type} {random.randint(1000, 9999)}"
            slug = f"{brand.lower()}-{product_type.lower()}-{random.randint(1000, 9999)}"
            
            # Define realistic price ranges for electronics
            if 'smartphone' in product_type.lower():
                price_range = (15000, 80000)
            elif 'laptop' in product_type.lower():
                price_range = (30000, 150000)
            elif 'tablet' in product_type.lower():
                price_range = (15000, 60000)
            elif 'headphones' in product_type.lower():
                price_range = (1000, 15000)
            elif 'speaker' in product_type.lower():
                price_range = (500, 8000)
            elif 'camera' in product_type.lower():
                price_range = (8000, 50000)
            elif 'monitor' in product_type.lower():
                price_range = (5000, 25000)
            elif 'keyboard' in product_type.lower():
                price_range = (500, 3000)
            elif 'mouse' in product_type.lower():
                price_range = (300, 2000)
            elif 'webcam' in product_type.lower():
                price_range = (800, 5000)
            else:
                price_range = (1000, 50000)
            
            price = random.randint(price_range[0], price_range[1])
            sale_price = None
            if random.random() > 0.6:
                sale_price = int(price * random.uniform(0.7, 0.9))
            
            additional_products.append({
                'name': name,
                'slug': slug,
                'category': categories['electronics-gadgets'],
                'description': f'High-quality {product_type.lower()} from {brand} with advanced features and premium build quality.',
                'price': Decimal(str(price)),
                'sale_price': Decimal(str(sale_price)) if sale_price else None,
                'stock_quantity': random.randint(10, 100),
                'sku': f"{brand[:3].upper()}{product_type[:3].upper()}{random.randint(100, 999)}",
                'is_featured': random.random() > 0.8
            })
        
        # Fashion variations
        fashion_brands = ['Nike', 'Adidas', 'Puma', 'Under Armour', 'New Balance', 'Converse', 'Vans', 'Reebok', 'ASICS', 'Brooks']
        fashion_types = ['Sneakers', 'Running Shoes', 'Athletic Shoes', 'Casual Shoes', 'Training Shoes', 'Basketball Shoes', 'Soccer Cleats', 'Tennis Shoes', 'Hiking Boots', 'Slides']
        
        for i in range(60):
            brand = random.choice(fashion_brands)
            product_type = random.choice(fashion_types)
            name = f"{brand} {product_type} {random.randint(100, 999)}"
            slug = f"{brand.lower()}-{product_type.lower()}-{random.randint(100, 999)}"
            
            # Define realistic price ranges for fashion
            if 'sneakers' in product_type.lower():
                price_range = (1500, 8000)
            elif 'running-shoes' in product_type.lower():
                price_range = (2000, 12000)
            elif 'athletic-shoes' in product_type.lower():
                price_range = (1500, 10000)
            elif 'casual-shoes' in product_type.lower():
                price_range = (1000, 6000)
            elif 'training-shoes' in product_type.lower():
                price_range = (1500, 8000)
            elif 'basketball-shoes' in product_type.lower():
                price_range = (2000, 12000)
            elif 'soccer-cleats' in product_type.lower():
                price_range = (1500, 8000)
            elif 'tennis-shoes' in product_type.lower():
                price_range = (1500, 8000)
            elif 'hiking-boots' in product_type.lower():
                price_range = (2000, 12000)
            elif 'slides' in product_type.lower():
                price_range = (500, 3000)
            else:
                price_range = (500, 8000)
            
            price = random.randint(price_range[0], price_range[1])
            sale_price = None
            if random.random() > 0.5:
                sale_price = int(price * random.uniform(0.7, 0.9))
            
            additional_products.append({
                'name': name,
                'slug': slug,
                'category': categories['fashion-apparel'],
                'description': f'Comfortable and stylish {product_type.lower()} from {brand} with premium materials and modern design.',
                'price': Decimal(str(price)),
                'sale_price': Decimal(str(sale_price)) if sale_price else None,
                'stock_quantity': random.randint(20, 200),
                'sku': f"{brand[:3].upper()}{product_type[:3].upper()}{random.randint(100, 999)}",
                'is_featured': random.random() > 0.85
            })
        
        # Home & Living variations
        home_brands = ['IKEA', 'West Elm', 'Crate & Barrel', 'Pottery Barn', 'Target', 'Walmart', 'Home Depot', 'Lowe\'s', 'Wayfair', 'Overstock']
        home_types = ['Sofa', 'Dining Table', 'Bed Frame', 'Dresser', 'Bookshelf', 'Coffee Table', 'Side Table', 'Chair', 'Lamp', 'Mirror']
        
        for i in range(40):
            brand = random.choice(home_brands)
            product_type = random.choice(home_types)
            name = f"{brand} {product_type} {random.randint(100, 999)}"
            slug = f"{brand.lower().replace(' ', '-').replace('&', 'and')}-{product_type.lower()}-{random.randint(100, 999)}"
            
            # Define realistic price ranges for home & living
            if 'sofa' in product_type.lower():
                price_range = (8000, 50000)
            elif 'dining-table' in product_type.lower():
                price_range = (5000, 30000)
            elif 'bed-frame' in product_type.lower():
                price_range = (3000, 25000)
            elif 'dresser' in product_type.lower():
                price_range = (2000, 15000)
            elif 'bookshelf' in product_type.lower():
                price_range = (1000, 8000)
            elif 'coffee-table' in product_type.lower():
                price_range = (2000, 12000)
            elif 'side-table' in product_type.lower():
                price_range = (1000, 5000)
            elif 'chair' in product_type.lower():
                price_range = (1000, 8000)
            elif 'lamp' in product_type.lower():
                price_range = (500, 3000)
            elif 'mirror' in product_type.lower():
                price_range = (500, 3000)
            else:
                price_range = (500, 30000)
            
            price = random.randint(price_range[0], price_range[1])
            sale_price = None
            if random.random() > 0.6:
                sale_price = int(price * random.uniform(0.7, 0.9))
            
            additional_products.append({
                'name': name,
                'slug': slug,
                'category': categories['home-living'],
                'description': f'Beautiful {product_type.lower()} from {brand} with quality craftsmanship and modern design.',
                'price': Decimal(str(price)),
                'sale_price': Decimal(str(sale_price)) if sale_price else None,
                'stock_quantity': random.randint(5, 50),
                'sku': f"{brand[:3].upper()}{product_type[:3].upper()}{random.randint(100, 999)}",
                'is_featured': random.random() > 0.8
            })
        
        # Combine all products
        all_products = products_data + additional_products
        
        # Sample product images (using placeholder URLs)
        product_images = {
            'iphone-15-pro-max': 'https://images.pexels.com/photos/1647976/pexels-photo-1647976.jpeg',
            'samsung-galaxy-s24-ultra': 'https://images.pexels.com/photos/1647976/pexels-photo-1647976.jpeg',
            'macbook-pro-16-m3': 'https://images.pexels.com/photos/18105/pexels-photo.jpg',
            'sony-wh-1000xm5-headphones': 'https://images.pexels.com/photos/3394650/pexels-photo-3394650.jpeg',
            'nike-air-jordan-1-retro': 'https://images.pexels.com/photos/2526878/pexels-photo-2526878.jpeg',
            'levis-501-original-jeans': 'https://images.pexels.com/photos/1082529/pexels-photo-1082529.jpeg',
            'ikea-malm-bed-frame': 'https://images.pexels.com/photos/3937174/pexels-photo-3937174.jpeg',
            'philips-hue-smart-bulb-starter-kit': 'https://images.pexels.com/photos/3937174/pexels-photo-3937174.jpeg',
            'psychology-of-money': 'https://images.pexels.com/photos/3747468/pexels-photo-3747468.jpeg',
            'peloton-bike-plus': 'https://images.pexels.com/photos/4056530/pexels-photo-4056530.jpeg',
            'dyson-airwrap-multi-styler': 'https://images.pexels.com/photos/3993449/pexels-photo-3993449.jpeg',
            'dewalt-20v-max-cordless-drill': 'https://images.pexels.com/photos/4489749/pexels-photo-4489749.jpeg',
            'lego-star-wars-millennium-falcon': 'https://images.pexels.com/photos/4489749/pexels-photo-4489749.jpeg',
            'oura-ring-gen-3': 'https://images.pexels.com/photos/3993449/pexels-photo-3993449.jpeg',
            'weber-spirit-ii-e-310-gas-grill': 'https://images.pexels.com/photos/4503269/pexels-photo-4503269.jpeg',
        }
        
        # Create products
        created_count = 0
        for prod_data in all_products:
            prod_data_copy = prod_data.copy()
            
            # Download and save image if available
            if prod_data['slug'] in product_images:
                image_url = product_images[prod_data['slug']]
                image_file = self.download_image(image_url, prod_data['slug'])
                if image_file:
                    prod_data_copy['image'] = image_file
                    self.stdout.write(f'Downloaded image for: {prod_data["name"]}')
            
            # Remove sale_price if it's None
            if prod_data_copy.get('sale_price') is None:
                prod_data_copy.pop('sale_price', None)
            
            product, created = Product.objects.get_or_create(
                slug=prod_data['slug'],
                defaults=prod_data_copy
            )
            if created:
                created_count += 1
                if created_count % 50 == 0:
                    self.stdout.write(f'Created {created_count} products...')
        
        # Create test users
        test_users = [
            {
                'username': 'testuser1',
                'email': 'test1@example.com',
                'password': 'testpass123',
                'first_name': 'John',
                'last_name': 'Doe'
            },
            {
                'username': 'testuser2',
                'email': 'test2@example.com',
                'password': 'testpass123',
                'first_name': 'Jane',
                'last_name': 'Smith'
            },
            {
                'username': 'testuser3',
                'email': 'test3@example.com',
                'password': 'testpass123',
                'first_name': 'Mike',
                'last_name': 'Johnson'
            }
        ]
        
        for user_data in test_users:
            if not User.objects.filter(username=user_data['username']).exists():
                user = User.objects.create_user(
                    username=user_data['username'],
                    email=user_data['email'],
                    password=user_data['password'],
                    first_name=user_data['first_name'],
                    last_name=user_data['last_name']
                )
                
                # Create customer profile
                customer = Customer.objects.create(
                    user=user,
                    phone=f'+91 {random.randint(7000000000, 9999999999)}',
                    address=f'{random.randint(1, 999)} Test Street',
                    city=random.choice(['Mumbai', 'Delhi', 'Bangalore', 'Chennai', 'Kolkata']),
                    state=random.choice(['Maharashtra', 'Delhi', 'Karnataka', 'Tamil Nadu', 'West Bengal']),
                    zip_code=str(random.randint(100000, 999999)),
                    country='India'
                )
                
                self.stdout.write(f'Created test user: {user.username}')
        
        self.stdout.write('Test user credentials:')
        self.stdout.write('Username: testuser1, testuser2, testuser3')
        self.stdout.write('Password: testpass123')
        
        self.stdout.write(
            self.style.SUCCESS(f'Successfully created {created_count} products across {len(categories)} categories!')
        )
        self.stdout.write(
            self.style.SUCCESS('Your e-commerce store now has a massive product catalog!')
        ) 