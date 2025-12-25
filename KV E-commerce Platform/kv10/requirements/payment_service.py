"""
Razorpay Payment Service
Handles all payment-related operations including creation, verification, and refunds
"""

import razorpay
import hmac
import hashlib
import json
from django.conf import settings
from django.utils import timezone
from decimal import Decimal
from .models import Payment, Order
import logging

logger = logging.getLogger(__name__)

class RazorpayService:
    def __init__(self):
        try:
            logger.info("Initializing Razorpay service...")
            
            # Check if settings attributes exist
            if not hasattr(settings, 'RAZORPAY_KEY_ID') or not hasattr(settings, 'RAZORPAY_KEY_SECRET'):
                error_msg = "Razorpay credentials not found in settings"
                logger.error(error_msg)
                raise ValueError(error_msg)
                
            # Check if keys are not empty
            if not settings.RAZORPAY_KEY_ID or not settings.RAZORPAY_KEY_SECRET:
                error_msg = "Razorpay credentials are empty"
                logger.error(f"{error_msg}. Key ID: {bool(settings.RAZORPAY_KEY_ID)}, Key Secret: {bool(settings.RAZORPAY_KEY_SECRET)}")
                raise ValueError(error_msg)
                
            logger.info(f"Using Razorpay Key ID: {settings.RAZORPAY_KEY_ID}")
            logger.info(f"Key Secret: {'*' * 8}{settings.RAZORPAY_KEY_SECRET[-4:] if settings.RAZORPAY_KEY_SECRET else 'None'}")
            
            # Initialize Razorpay client
            self.client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))
            
            # Test the client connection
            try:
                self.client.payment.all()
                logger.info("Successfully connected to Razorpay API")
            except Exception as e:
                logger.error(f"Failed to connect to Razorpay API: {str(e)}")
                raise
                
        except Exception as e:
            logger.error(f"Failed to initialize Razorpay client: {str(e)}", exc_info=True)
            raise
    
    def create_order(self, order, amount_in_paise=None):
        """
        Create a Razorpay order for payment
        """
        try:
            logger.info(f"Creating Razorpay order for order {order.id}")
            logger.info(f"Using Razorpay Key ID: {settings.RAZORPAY_KEY_ID}")
            
            if amount_in_paise is None:
                amount_in_paise = int(order.total_amount * 100)  # Convert to paise
            
            logger.info(f"Order amount: {amount_in_paise} paise")
            
            order_data = {
                'amount': amount_in_paise,
                'currency': 'INR',
                'receipt': order.order_number,
                'payment_capture': 1,  # Auto capture payment
                'notes': {
                    'order_id': str(order.id),
                    'customer_id': str(order.customer.id),
                    'customer_email': order.email,
                }
            }
            
            logger.info(f"Sending order data to Razorpay: {order_data}")
            
            razorpay_order = self.client.order.create(order_data)
            logger.info(f"Razorpay order created: {razorpay_order}")
            
            # Update order with Razorpay order ID
            order.razorpay_order_id = razorpay_order['id']
            order.save()
            
            # Create payment record
            payment = Payment.objects.create(
                order=order,
                amount=order.total_amount,
                payment_method='razorpay',
                gateway='razorpay',
                gateway_order_id=razorpay_order['id'],
                status='initiated'
            )
            
            response = {
                'success': True,
                'order_id': razorpay_order['id'],
                'amount': razorpay_order['amount'],
                'currency': razorpay_order['currency'],
                'payment_id': payment.payment_id,
                'order': razorpay_order
            }
            
            logger.info(f"Successfully created Razorpay order: {response}")
            return response
            
        except Exception as e:
            error_msg = f"Error creating Razorpay order: {str(e)}"
            logger.error(error_msg, exc_info=True)
            logger.error(f"Razorpay credentials: Key ID: {settings.RAZORPAY_KEY_ID}, Key Secret: {'*' * 8}{settings.RAZORPAY_KEY_SECRET[-4:] if settings.RAZORPAY_KEY_SECRET else 'None'}")
            return {
                'success': False,
                'error': error_msg,
                'debug': {
                    'key_id': settings.RAZORPAY_KEY_ID,
                    'key_secret_set': bool(settings.RAZORPAY_KEY_SECRET),
                    'order_id': order.id if order else None,
                    'order_amount': amount_in_paise if amount_in_paise else None,
                    'exception_type': type(e).__name__
                }
            }
    
    def verify_payment(self, razorpay_payment_id, razorpay_order_id, razorpay_signature):
        """
        Verify payment signature from Razorpay
        """
        try:
            # Verify signature
            generated_signature = hmac.new(
                settings.RAZORPAY_KEY_SECRET.encode('utf-8'),
                f"{razorpay_order_id}|{razorpay_payment_id}".encode('utf-8'),
                hashlib.sha256
            ).hexdigest()
            
            if generated_signature != razorpay_signature:
                return {
                    'success': False,
                    'error': 'Invalid payment signature'
                }
            
            # Get payment details from Razorpay
            payment_details = self.client.payment.fetch(razorpay_payment_id)
            
            # Find the order and payment record
            try:
                order = Order.objects.get(razorpay_order_id=razorpay_order_id)
                payment = Payment.objects.get(
                    order=order,
                    gateway_order_id=razorpay_order_id
                )
            except (Order.DoesNotExist, Payment.DoesNotExist):
                return {
                    'success': False,
                    'error': 'Order or payment record not found'
                }
            
            # Update payment record
            payment.gateway_payment_id = razorpay_payment_id
            payment.gateway_signature = razorpay_signature
            payment.gateway_response = payment_details
            payment.status = 'completed'
            payment.completed_at = timezone.now()
            payment.payment_method = self._get_payment_method(payment_details)
            
            # Calculate processing fee (Razorpay charges ~2.36% + GST)
            payment.processing_fee = Decimal(str(payment_details.get('fee', 0))) / 100
            payment.save()
            
            # Update order
            order.razorpay_payment_id = razorpay_payment_id
            order.razorpay_signature = razorpay_signature
            order.payment_status = 'paid'
            order.payment_method = payment.payment_method
            order.save()
            
            logger.info(f"Payment verified successfully: {razorpay_payment_id}")
            
            return {
                'success': True,
                'payment': payment,
                'order': order,
                'payment_details': payment_details
            }
            
        except Exception as e:
            logger.error(f"Error verifying payment: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def handle_payment_failure(self, razorpay_payment_id, error_description=None):
        """
        Handle failed payment
        """
        try:
            # Try to get payment details
            try:
                payment_details = self.client.payment.fetch(razorpay_payment_id)
                order_id = payment_details.get('order_id')
                
                if order_id:
                    order = Order.objects.get(razorpay_order_id=order_id)
                    payment = Payment.objects.get(
                        order=order,
                        gateway_order_id=order_id
                    )
                    
                    payment.gateway_payment_id = razorpay_payment_id
                    payment.gateway_response = payment_details
                    payment.status = 'failed'
                    payment.failure_reason = error_description or payment_details.get('error_description', 'Payment failed')
                    payment.retry_count += 1
                    payment.save()
                    
                    order.payment_status = 'failed'
                    order.save()
                    
                    logger.warning(f"Payment failed: {razorpay_payment_id}")
                    
            except Exception as inner_e:
                logger.error(f"Error handling payment failure: {str(inner_e)}")
                
        except Exception as e:
            logger.error(f"Error in handle_payment_failure: {str(e)}")
    
    def initiate_refund(self, payment, amount=None, reason="Customer request"):
        """
        Initiate refund for a payment
        """
        try:
            if not payment.is_refundable:
                return {
                    'success': False,
                    'error': 'Payment is not refundable'
                }
            
            refund_amount = amount or payment.remaining_refund_amount
            refund_amount_paise = int(refund_amount * 100)
            
            refund_data = {
                'amount': refund_amount_paise,
                'notes': {
                    'reason': reason,
                    'order_id': str(payment.order.id),
                    'payment_id': payment.payment_id
                }
            }
            
            refund = self.client.payment.refund(payment.gateway_payment_id, refund_data)
            
            # Update payment record
            payment.refund_amount += refund_amount
            payment.refund_reason = reason
            payment.refund_initiated_at = timezone.now()
            payment.refund_reference = refund['id']
            
            if payment.refund_amount >= payment.amount:
                payment.status = 'refunded'
            else:
                payment.status = 'partially_refunded'
            
            payment.save()
            
            # Update order if fully refunded
            if payment.refund_amount >= payment.amount:
                payment.order.payment_status = 'refunded'
                payment.order.status = 'refunded'
                payment.order.save()
            
            logger.info(f"Refund initiated: {refund['id']} for payment {payment.payment_id}")
            
            return {
                'success': True,
                'refund': refund,
                'payment': payment
            }
            
        except Exception as e:
            logger.error(f"Error initiating refund: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def get_payment_analytics(self, start_date=None, end_date=None):
        """
        Get payment analytics data
        """
        try:
            payments = Payment.objects.all()
            
            if start_date:
                payments = payments.filter(initiated_at__gte=start_date)
            if end_date:
                payments = payments.filter(initiated_at__lte=end_date)
            
            total_payments = payments.count()
            successful_payments = payments.filter(status='completed').count()
            failed_payments = payments.filter(status='failed').count()
            refunded_payments = payments.filter(status__in=['refunded', 'partially_refunded']).count()
            
            total_amount = sum(p.amount for p in payments.filter(status='completed'))
            total_fees = sum(p.processing_fee for p in payments.filter(status='completed'))
            total_refunds = sum(p.refund_amount for p in payments.filter(refund_amount__gt=0))
            
            success_rate = (successful_payments / total_payments * 100) if total_payments > 0 else 0
            
            # Payment method breakdown
            method_stats = {}
            for payment in payments.filter(status='completed'):
                method = payment.payment_method
                if method not in method_stats:
                    method_stats[method] = {'count': 0, 'amount': 0}
                method_stats[method]['count'] += 1
                method_stats[method]['amount'] += payment.amount
            
            return {
                'total_payments': total_payments,
                'successful_payments': successful_payments,
                'failed_payments': failed_payments,
                'refunded_payments': refunded_payments,
                'success_rate': round(success_rate, 2),
                'total_amount': total_amount,
                'total_fees': total_fees,
                'total_refunds': total_refunds,
                'net_revenue': total_amount - total_fees - total_refunds,
                'payment_methods': method_stats
            }
            
        except Exception as e:
            logger.error(f"Error getting payment analytics: {str(e)}")
            return {}
    
    def _get_payment_method(self, payment_details):
        """
        Extract payment method from Razorpay payment details
        """
        method = payment_details.get('method', 'card')
        method_mapping = {
            'card': 'card',
            'netbanking': 'netbanking',
            'upi': 'upi',
            'wallet': 'wallet',
            'emi': 'emi'
        }
        return method_mapping.get(method, 'card')

# Singleton instance - lazy initialization
razorpay_service = None

def get_razorpay_service():
    global razorpay_service
    if razorpay_service is None:
        try:
            razorpay_service = RazorpayService()
        except Exception as e:
            logger.error(f"Failed to initialize Razorpay service: {str(e)}")
            return None
    return razorpay_service
