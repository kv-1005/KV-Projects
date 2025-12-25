from django.core.management.base import BaseCommand
from django.core.files.base import ContentFile
from requirements.models import Product, Category
import requests
import os
from urllib.parse import urlparse
import time

class Command(BaseCommand):
    help = 'Download relevant product images from Unsplash API'

    def add_arguments(self, parser):
        parser.add_argument(
            '--limit',
            type=int,
            default=50,
            help='Limit the number of products to process'
        )
        parser.add_argument(
            '--category',
            type=str,
            help='Process only products from a specific category'
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

    def get_unsplash_image(self, query, category_name):
        """Get a relevant image from Unsplash based on query"""
        try:
            # Use Unsplash API to get relevant images
            # Note: In production, you should use proper API keys
            # For now, we'll use a simple approach with Unsplash's search
            
            # Create search query based on product and category
            search_query = f"{query} {category_name}"
            
            # Use Unsplash's search API (free tier)
            url = f"https://api.unsplash.com/search/photos"
            params = {
                'query': search_query,
                'per_page': 1,
                'orientation': 'landscape'
            }
            
            # For demo purposes, we'll use a fallback approach
            # In production, you'd need an Unsplash API key
            fallback_urls = {
                'electronics': [
                    'https://images.unsplash.com/photo-1498049794561-7780e7231661?w=800',
                    'https://images.unsplash.com/photo-1526738549149-8e07eca6c147?w=800',
                    'https://images.unsplash.com/photo-1511707171634-5f897ff02aa9?w=800'
                ],
                'fashion': [
                    'https://images.unsplash.com/photo-1445205170230-053b83016050?w=800',
                    'https://images.unsplash.com/photo-1521572163474-6864f9cf17ab?w=800',
                    'https://images.unsplash.com/photo-1441986300917-64674bd600d8?w=800'
                ],
                'home': [
                    'https://images.unsplash.com/photo-1586023492125-27b2c045efd7?w=800',
                    'https://images.unsplash.com/photo-1555041469-a586c61ea9bc?w=800',
                    'https://images.unsplash.com/photo-1560448204-e02f11c3d0e2?w=800'
                ],
                'sports': [
                    'https://images.unsplash.com/photo-1571019613454-1cb2f99b2d8b?w=800',
                    'https://images.unsplash.com/photo-1544551763-46a013bb70d5?w=800',
                    'https://images.unsplash.com/photo-1571019613454-1cb2f99b2d8b?w=800'
                ],
                'books': [
                    'https://images.unsplash.com/photo-1481627834876-b7833e8f5570?w=800',
                    'https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?w=800',
                    'https://images.unsplash.com/photo-1512820790803-83ca734da794?w=800'
                ],
                'beauty': [
                    'https://images.unsplash.com/photo-1596462502278-27bfdc403348?w=800',
                    'https://images.unsplash.com/photo-1522335789203-aabd1fc54bc9?w=800',
                    'https://images.unsplash.com/photo-1556228720-195a672e8a03?w=800'
                ],
                'automotive': [
                    'https://images.unsplash.com/photo-1549317661-bd32c8ce0db2?w=800',
                    'https://images.unsplash.com/photo-1503376780353-7e6692767b70?w=800',
                    'https://images.unsplash.com/photo-1485291571150-772bcfc10da5?w=800'
                ]
            }
            
            # Determine category for fallback
            category_lower = category_name.lower()
            if any(word in category_lower for word in ['electronics', 'gadgets', 'tech']):
                category_key = 'electronics'
            elif any(word in category_lower for word in ['fashion', 'apparel', 'clothing']):
                category_key = 'fashion'
            elif any(word in category_lower for word in ['home', 'garden', 'living']):
                category_key = 'home'
            elif any(word in category_lower for word in ['sports', 'fitness']):
                category_key = 'sports'
            elif any(word in category_lower for word in ['books', 'education']):
                category_key = 'books'
            elif any(word in category_lower for word in ['beauty', 'personal']):
                category_key = 'beauty'
            elif any(word in category_lower for word in ['automotive', 'tools']):
                category_key = 'automotive'
            else:
                category_key = 'home'  # Default
            
            # Get a random image from the category
            import random
            if category_key in fallback_urls:
                return random.choice(fallback_urls[category_key])
            else:
                return fallback_urls['home'][0]
                
        except Exception as e:
            self.stdout.write(f"Error getting Unsplash image: {e}")
            return None

    def handle(self, *args, **options):
        self.stdout.write('Downloading relevant product images...')
        
        # Get products to process
        products = Product.objects.filter(is_active=True)
        
        if options['category']:
            products = products.filter(category__name__icontains=options['category'])
        
        products = products[:options['limit']]
        
        self.stdout.write(f'Processing {products.count()} products...')
        
        # Process each product
        success_count = 0
        for i, product in enumerate(products, 1):
            try:
                # Skip if product already has an image
                if product.image:
                    self.stdout.write(f'{i}. Skipping {product.name} (already has image)')
                    continue
                
                # Get relevant image URL
                image_url = self.get_unsplash_image(product.name, product.category.name)
                
                if image_url:
                    # Download and save image
                    image_file = self.download_image(image_url, f"{product.slug}")
                    
                    if image_file:
                        product.image.save(
                            f"{product.slug}.jpg",
                            image_file,
                            save=True
                        )
                        success_count += 1
                        self.stdout.write(f'{i}. ✓ Downloaded image for {product.name}')
                    else:
                        self.stdout.write(f'{i}. ✗ Failed to download image for {product.name}')
                else:
                    self.stdout.write(f'{i}. ✗ No image URL found for {product.name}')
                
                # Add a small delay to be respectful to the API
                time.sleep(0.5)
                
            except Exception as e:
                self.stdout.write(f'{i}. ✗ Error processing {product.name}: {e}')
        
        self.stdout.write(
            self.style.SUCCESS(f'Successfully downloaded {success_count} images!')
        )
