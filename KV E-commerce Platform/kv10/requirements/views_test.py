"""
Test view to verify Razorpay integration
"""
import logging
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
import razorpay

logger = logging.getLogger(__name__)

def test_razorpay_connection(request):
    """Test Razorpay connection and return status"""
    try:
        # Initialize Razorpay client directly
        client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))
        
        # Test connection by fetching payments
        payments = client.payment.all()
        
        return JsonResponse({
            'status': 'success',
            'message': 'Successfully connected to Razorpay',
            'test_mode': settings.RAZORPAY_KEY_ID.startswith('rzp_test_')
        })
    except Exception as e:
        logger.error(f"Razorpay connection test failed: {str(e)}", exc_info=True)
        return JsonResponse({
            'status': 'error',
            'message': str(e),
            'key_id': settings.RAZORPAY_KEY_ID,
            'key_secret_set': bool(settings.RAZORPAY_KEY_SECRET)
        }, status=500)
