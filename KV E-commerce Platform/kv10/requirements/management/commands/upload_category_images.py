from django.core.management.base import BaseCommand
from django.core.files.base import ContentFile
from requirements.models import Product, Category
import requests
import os
from urllib.parse import urlparse
import time

class Command(BaseCommand):
    help = 'Upload images for products in a specific category'

    def add_arguments(self, parser):
        parser.add_argument(
            'category',
            type=str,
            help='Category name to process'
        )
        parser.add_argument(
            '--limit',
            type=int,
            default=20,
            help='Limit the number of products to process'
        )
        parser.add_argument(
            '--replace',
            action='store_true',
            help='Replace existing images'
        )

    def download_image(self, url, filename):
        """Download image from URL and return ContentFile"""
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            response = requests.get(url, headers=headers, timeout=15)
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

    def get_category_images(self, category_name):
        """Get relevant images for a specific category"""
        category_images = {
            'electronics': [
                'https://images.unsplash.com/photo-1498049794561-7780e7231661?w=800',
                'https://images.unsplash.com/photo-1526738549149-8e07eca6c147?w=800',
                'https://images.unsplash.com/photo-1511707171634-5f897ff02aa9?w=800',
                'https://images.unsplash.com/photo-1505740420928-5e560c06d30e?w=800',
                'https://images.unsplash.com/photo-1516035069371-29a1b244cc32?w=800',
                'https://images.unsplash.com/photo-1541140532154-b024d705b90a?w=800',
                'https://images.unsplash.com/photo-1527864550417-7fd91fc51a46?w=800',
                'https://images.unsplash.com/photo-1593642632823-8f785ba67e45?w=800',
                'https://images.unsplash.com/photo-1545454675-3531b543be5d?w=800',
                'https://images.unsplash.com/photo-1544244015-0df4b3ffc6b0?w=800',
                'https://images.unsplash.com/photo-1523275335684-37898b6baf30?w=800',
                'https://images.unsplash.com/photo-1579829366248-204fe8413f31?w=800',
                'https://images.unsplash.com/photo-1593359677879-a4bb92f829d1?w=800',
            ],
            'fashion': [
                'https://images.unsplash.com/photo-1445205170230-053b83016050?w=800',
                'https://images.unsplash.com/photo-1521572163474-6864f9cf17ab?w=800',
                'https://images.unsplash.com/photo-1441986300917-64674bd600d8?w=800',
                'https://images.unsplash.com/photo-1549298916-b41d501d3772?w=800',
                'https://images.unsplash.com/photo-1542272604-787c3835535d?w=800',
                'https://images.unsplash.com/photo-1515372039744-b8f02a3ae446?w=800',
                'https://images.unsplash.com/photo-1551028719-00167b16eac5?w=800',
                'https://images.unsplash.com/photo-1548036328-c9fa89d128fa?w=800',
                'https://images.unsplash.com/photo-1572635196237-14b3f281503f?w=800',
            ],
            'home': [
                'https://images.unsplash.com/photo-1586023492125-27b2c045efd7?w=800',
                'https://images.unsplash.com/photo-1555041469-a586c61ea9bc?w=800',
                'https://images.unsplash.com/photo-1560448204-e02f11c3d0e2?w=800',
                'https://images.unsplash.com/photo-1505693314120-0d443867891c?w=800',
                'https://images.unsplash.com/photo-1567538096630-e0c55bd6374c?w=800',
                'https://images.unsplash.com/photo-1507473885765-e6ed057f782c?w=800',
                'https://images.unsplash.com/photo-1481627834876-b7833e8f5570?w=800',
                'https://images.unsplash.com/photo-1556306535-38febf6782e7?w=800',
                'https://images.unsplash.com/photo-1416879595882-3373a0480b5b?w=800',
                'https://images.unsplash.com/photo-1514228742587-6b1558fcca3d?w=800',
                'https://images.unsplash.com/photo-1495474472287-4d71bcdd2085?w=800',
            ],
            'sports': [
                'https://images.unsplash.com/photo-1571019613454-1cb2f99b2d8b?w=800',
                'https://images.unsplash.com/photo-1544551763-46a013bb70d5?w=800',
                'https://images.unsplash.com/photo-1546519638-68e109498ffc?w=800',
                'https://images.unsplash.com/photo-1554068865-24cecd4e34b8?w=800',
                'https://images.unsplash.com/photo-1544367567-0f2fcb009e0b?w=800',
                'https://images.unsplash.com/photo-1534438327276-14e5300c3a48?w=800',
            ],
            'books': [
                'https://images.unsplash.com/photo-1481627834876-b7833e8f5570?w=800',
                'https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?w=800',
                'https://images.unsplash.com/photo-1512820790803-83ca734da794?w=800',
            ],
            'beauty': [
                'https://images.unsplash.com/photo-1596462502278-27bfdc403348?w=800',
                'https://images.unsplash.com/photo-1522335789203-aabd1fc54bc9?w=800',
                'https://images.unsplash.com/photo-1556228720-195a672e8a03?w=800',
                'https://images.unsplash.com/photo-1541643600914-78b084683601?w=800',
            ],
            'automotive': [
                'https://images.unsplash.com/photo-1549317661-bd32c8ce0db2?w=800',
                'https://images.unsplash.com/photo-1503376780353-7e6692767b70?w=800',
                'https://images.unsplash.com/photo-1485291571150-772bcfc10da5?w=800',
            ],
        }
        
        # Determine category key
        category_lower = category_name.lower()
        for key in category_images.keys():
            if key in category_lower:
                return category_images[key]
        
        # Default to home category
        return category_images['home']

    def handle(self, *args, **options):
        category_name = options['category']
        limit = options['limit']
        
        self.stdout.write(f'Uploading images for category: {category_name}')
        
        # Get products in the specified category
        products = Product.objects.filter(
            category__name__icontains=category_name,
            is_active=True
        )[:limit]
        
        if not products.exists():
            self.stdout.write(self.style.ERROR(f'No products found in category: {category_name}'))
            return
        
        self.stdout.write(f'Found {products.count()} products in category: {category_name}')
        
        # Get images for this category
        category_images = self.get_category_images(category_name)
        
        # Process each product
        success_count = 0
        skipped_count = 0
        
        for i, product in enumerate(products, 1):
            try:
                # Skip if product already has an image and we're not replacing
                if product.image and not options['replace']:
                    self.stdout.write(f'{i}. Skipping {product.name} (already has image)')
                    skipped_count += 1
                    continue
                
                # Select an image from the category (cycle through them)
                image_url = category_images[i % len(category_images)]
                
                # Download and save image
                image_file = self.download_image(image_url, f"{product.slug}")
                
                if image_file:
                    # Remove old image if replacing
                    if product.image and options['replace']:
                        try:
                            product.image.delete(save=False)
                        except:
                            pass
                    
                    product.image.save(
                        f"{product.slug}.jpg",
                        image_file,
                        save=True
                    )
                    success_count += 1
                    self.stdout.write(f'{i}. ✓ Uploaded image for {product.name}')
                else:
                    self.stdout.write(f'{i}. ✗ Failed to download image for {product.name}')
                
                # Add a small delay
                time.sleep(0.3)
                
            except Exception as e:
                self.stdout.write(f'{i}. ✗ Error processing {product.name}: {e}')
        
        self.stdout.write(
            self.style.SUCCESS(f'Successfully uploaded {success_count} images! Skipped {skipped_count} existing images.')
        )
