from django.core.management.base import BaseCommand
from requirements.models import Product
from django.utils.text import slugify

class Command(BaseCommand):
    help = 'Update all Product slugs to be URL-safe using slugify.'

    def handle(self, *args, **options):
        updated = 0
        for product in Product.objects.all():
            new_slug = slugify(product.name)
            if product.slug != new_slug:
                self.stdout.write(f'Updating slug for "{product.name}" from "{product.slug}" to "{new_slug}"')
                product.slug = new_slug
                product.save()
                updated += 1
        self.stdout.write(self.style.SUCCESS(f'Updated {updated} product slugs.'))