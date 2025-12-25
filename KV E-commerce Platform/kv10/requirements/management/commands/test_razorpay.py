from django.core.management.base import BaseCommand
import razorpay
from django.conf import settings
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Test Razorpay connection and configuration'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Testing Razorpay connection...'))
        
        # Check if keys exist in settings
        if not hasattr(settings, 'RAZORPAY_KEY_ID') or not hasattr(settings, 'RAZORPAY_KEY_SECRET'):
            self.stdout.write(self.style.ERROR('Razorpay keys not found in settings!'))
            return
            
        self.stdout.write(f"RAZORPAY_KEY_ID: {settings.RAZORPAY_KEY_ID}")
        self.stdout.write(f"RAZORPAY_KEY_SECRET: {'*' * 8}{settings.RAZORPAY_KEY_SECRET[-4:] if settings.RAZORPAY_KEY_SECRET else 'None'}")
        
        if not settings.RAZORPAY_KEY_ID or not settings.RAZORPAY_KEY_SECRET:
            self.stdout.write(self.style.ERROR('Razorpay keys are empty!'))
            return
            
        # Test Razorpay connection
        try:
            client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))
            self.stdout.write(self.style.SUCCESS('Successfully initialized Razorpay client'))
            
            # Test API connection
            payments = client.payment.all()
            self.stdout.write(self.style.SUCCESS('Successfully connected to Razorpay API'))
            self.stdout.write(f"Found {len(payments.get('items', []))} payments in test mode")
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error connecting to Razorpay: {str(e)}'))
            import traceback
            self.stdout.write(self.style.ERROR(traceback.format_exc()))
