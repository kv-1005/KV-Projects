from django.core.management.base import BaseCommand
from django.core.files import File
from requirements.models import Product
import os
from pathlib import Path

class Command(BaseCommand):
    help = 'Assign existing product images from media directory to products'

    def handle(self, *args, **options):
        self.stdout.write('Assigning product images...')
        
        # Get the media directory path
        media_root = Path('media/products')
        
        if not media_root.exists():
            self.stdout.write(self.style.ERROR(f'Media directory {media_root} does not exist'))
            return
        
        # Get all image files in the media directory
        image_files = list(media_root.glob('*.jpeg')) + list(media_root.glob('*.jpg')) + list(media_root.glob('*.png'))
        
        self.stdout.write(f'Found {len(image_files)} image files')
        
        # Get all products without images
        products_without_images = Product.objects.filter(image='')
        self.stdout.write(f'Found {products_without_images.count()} products without images')
        
        # Create a mapping of product names to image files
        image_mapping = {}
        for image_file in image_files:
            # Extract product name from filename (remove extension and replace hyphens with spaces)
            filename = image_file.stem
            product_name = filename.replace('-', ' ').title()
            image_mapping[product_name] = image_file
        
        self.stdout.write(f'Created mapping for {len(image_mapping)} images')
        
        # Assign images to products
        assigned_count = 0
        for product in products_without_images:
            # Try to find a matching image by product name
            product_name = product.name
            matching_image = None
            
            # Try exact match first
            if product_name in image_mapping:
                matching_image = image_mapping[product_name]
            else:
                # Try partial matches
                for image_name, image_file in image_mapping.items():
                    if any(word in product_name.lower() for word in image_name.lower().split()):
                        matching_image = image_file
                        break
            
            if matching_image:
                try:
                    # Open the image file and assign it to the product
                    with open(matching_image, 'rb') as f:
                        product.image.save(
                            matching_image.name,
                            File(f),
                            save=True
                        )
                    assigned_count += 1
                    self.stdout.write(f'Assigned {matching_image.name} to {product.name}')
                except Exception as e:
                    self.stdout.write(self.style.ERROR(f'Error assigning {matching_image.name} to {product.name}: {e}'))
            else:
                self.stdout.write(f'No matching image found for {product.name}')
        
        self.stdout.write(
            self.style.SUCCESS(f'Successfully assigned {assigned_count} images to products!')
        )
