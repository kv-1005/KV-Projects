import re
import json
import logging
import hmac
import hashlib
import razorpay
from decimal import Decimal
import random
import string
from datetime import timedelta
from functools import wraps

from django.shortcuts import render, redirect, get_object_or_404, reverse
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ObjectDoesNotExist
from django.http import HttpResponse, JsonResponse, HttpResponseRedirect, HttpResponseForbidden, Http404
from django.db import transaction
from django.views.decorators.csrf import csrf_exempt, csrf_protect
from django.views.decorators.http import require_http_methods
from django.db.models import Q, Sum, F, Case, When, Value, IntegerField
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.utils import timezone
from django.conf import settings
from django.contrib.auth import login as auth_login, logout, authenticate
from django.contrib.auth.models import User
from django.contrib.auth.hashers import make_password, check_password
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.html import strip_tags

from .models import *
from .forms import *
from .payment_service import get_razorpay_service, RazorpayService

logger = logging.getLogger(__name__)


def send_order_confirmation_email(order):
    """Send order confirmation email to customer"""
    try:
        if not hasattr(order, 'customer') or not hasattr(order.customer, 'user') or not hasattr(order.customer.user, 'email'):
            logger.error(f"Invalid order or customer data for order {getattr(order, 'id', 'N/A')}")
            return False
            
        subject = f'Order Confirmation - #{getattr(order, "order_number", "")}'
        
        # Create a simple text email as fallback
        message = f"""
        Thank you for your order #{getattr(order, 'order_number', '')}!
        
        Order Details:
        - Order Number: {getattr(order, 'order_number', 'N/A')}
        - Date: {getattr(order, 'created_at', '').strftime('%B %d, %Y %H:%M') if hasattr(order, 'created_at') else 'N/A'}
        - Status: {getattr(order, 'get_status_display', lambda: 'N/A')()}
        - Total: ₹{getattr(order, 'total', 0):.2f}
        
        You can view your order details by logging into your account.
        
        Thank you for shopping with us!
        """
        
        # Try to send HTML email if template exists
        try:
            html_message = render_to_string('emails/order_confirmation.html', {
                'order': order,
                'customer': getattr(order, 'customer', None),
            })
            
            send_mail(
                subject=subject,
                message=message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[order.customer.user.email],
                html_message=html_message,
                fail_silently=False,
            )
        except Exception as template_error:
            logger.warning(f"Failed to render HTML email template, sending plain text: {str(template_error)}")
            send_mail(
                subject=subject,
                message=message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[order.customer.user.email],
                fail_silently=False,
            )
        
        logger.info(f"Order confirmation email sent for order #{getattr(order, 'order_number', 'N/A')}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to send order confirmation email: {str(e)}", exc_info=True)
        return False


@login_required
def payment(request):
    """
    Handle the payment page for Razorpay integration.
    This view is called after the checkout form is submitted with Razorpay as the payment method.
    """
    try:
        # Get the order ID from session
        order_id = request.session.get('order_id')
        razorpay_order_id = request.session.get('razorpay_order_id')
        
        logger.info(f"Payment view - Session data retrieved:")
        logger.info(f"  order_id: {order_id}")
        logger.info(f"  razorpay_order_id: {razorpay_order_id}")
        logger.info(f"  All session keys: {list(request.session.keys())}")
        
        if not order_id or not razorpay_order_id:
            logger.error(f"Missing order_id or razorpay_order_id in session. order_id: {order_id}, razorpay_order_id: {razorpay_order_id}")
            messages.error(request, 'Invalid payment session. Please try again.')
            return redirect('checkout')
        
        # Get the order
        try:
            order = Order.objects.get(id=order_id, customer=request.user.customer)
        except Order.DoesNotExist:
            logger.error(f"Order not found. Order ID: {order_id}, User: {request.user}")
            messages.error(request, 'Order not found.')
            return redirect('checkout')
        
        # Check if Razorpay is configured
        if not settings.RAZORPAY_KEY_ID or not settings.RAZORPAY_KEY_SECRET:
            logger.warning("Razorpay keys not configured. Redirecting to COD checkout.")
            messages.warning(request, 'Online payment is not available. Please use Cash on Delivery.')
            return redirect('checkout')
        
        # Get Razorpay client
        razorpay_client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))
        
        # Get order details from Razorpay
        try:
            razorpay_order = razorpay_client.order.fetch(razorpay_order_id)
        except Exception as e:
            logger.error(f"Failed to fetch Razorpay order: {str(e)}")
            messages.error(request, 'Failed to fetch payment details. Please try again.')
            return redirect('checkout')
        
        # Prepare context for the payment template
        context = {
            'order': order,
            'razorpay_order_id': razorpay_order_id,
            'razorpay_key_id': settings.RAZORPAY_KEY_ID,
            'amount': int(order.total_amount * 100),  # Convert to paise
            'currency': 'INR',
            'callback_url': request.build_absolute_uri(reverse('payment_callback')),
            'customer_name': f"{request.user.first_name} {request.user.last_name}",
            'customer_email': request.user.email,
            'customer_phone': order.phone,
            'razorpay_configured': bool(settings.RAZORPAY_KEY_ID and settings.RAZORPAY_KEY_SECRET),
        }
        
        # Add debugging information
        logger.info(f"Payment view context - Order ID: {order.id}, Razorpay Order ID: {razorpay_order_id}")
        logger.info(f"Session data - order_id: {request.session.get('order_id')}, razorpay_order_id: {request.session.get('razorpay_order_id')}")
        logger.info(f"Razorpay order details: {razorpay_order}")
        
        return render(request, 'payment.html', context)
        
    except Exception as e:
        logger.error(f"Error in payment view: {str(e)}", exc_info=True)
        messages.error(request, 'An error occurred while processing your payment. Please try again.')
        return redirect('checkout')


@csrf_exempt
@require_http_methods(["POST"])
def payment_callback(request):
    """Handle Razorpay payment callback for both webhook and direct verification"""
    try:
        # Handle both JSON and form data
        if request.content_type == 'application/json':
            try:
                payment_data = json.loads(request.body)
            except json.JSONDecodeError:
                logger.error('Invalid JSON in request body')
                return JsonResponse({'error': 'Invalid JSON'}, status=400)
        else:
            payment_data = request.POST.dict()
        
        logger.info(f"Payment callback received with data: {payment_data}")
        
        # Check if this is a webhook or direct payment verification
        is_webhook = 'event' in payment_data
        
        if is_webhook:
            # Handle Razorpay webhook
            return handle_razorpay_webhook(request, payment_data)
        else:
            # Handle direct payment verification (from frontend)
            return handle_direct_payment_verification(request, payment_data)
            
    except Exception as e:
        logger.error(f"Error in payment_callback: {str(e)}", exc_info=True)
        return JsonResponse({'status': 'error', 'message': 'Internal server error'}, status=500)


def handle_razorpay_webhook(request, payment_data):
    """Handle Razorpay webhook events"""
    try:
        # Verify the webhook signature
        webhook_secret = getattr(settings, 'RAZORPAY_WEBHOOK_SECRET', '')
        
        if not webhook_secret:
            logger.error("RAZORPAY_WEBHOOK_SECRET not set in settings")
            return JsonResponse({'status': 'error', 'message': 'Server configuration error'}, status=500)
        
        # Verify the signature
        received_signature = request.headers.get('X-Razorpay-Signature')
        
        if not received_signature:
            logger.error("No X-Razorpay-Signature header found")
            return JsonResponse({'status': 'error', 'message': 'Invalid request'}, status=400)
        
        # Verify the webhook signature
        key = webhook_secret.encode('utf-8')
        payload = request.body
        
        hmac_obj = hmac.new(key, payload, hashlib.sha256)
        generated_signature = hmac_obj.hexdigest()
        
        if not hmac.compare_digest(received_signature, generated_signature):
            logger.error("Invalid webhook signature")
            return JsonResponse({'status': 'error', 'message': 'Invalid signature'}, status=400)
        
        # Handle different webhook events
        event = payment_data.get('event')
        
        if event == 'payment.captured':
            # Handle successful payment
            payment_entity = payment_data.get('payload', {}).get('payment', {}).get('entity', {})
            order_id = payment_entity.get('order_id')
            payment_id = payment_entity.get('id')
            amount = payment_entity.get('amount', 0) / 100  # Convert from paise to INR
            
            if not order_id or not payment_id:
                logger.error("Missing order_id or payment_id in payment.captured event")
                return JsonResponse({'status': 'error', 'message': 'Invalid payment data'}, status=400)
            
            # Find the order
            try:
                order = Order.objects.get(razorpay_order_id=order_id)
                
                # Update order status
                order.status = 'confirmed'
                order.payment_status = 'paid'
                order.save()
                
                # Create or update payment record
                payment, created = Payment.objects.get_or_create(
                    order=order,
                    defaults={
                        'payment_id': payment_id,
                        'amount': amount,
                        'status': 'completed',
                        'payment_method': 'razorpay',
                        'gateway': 'razorpay'
                    }
                )
                
                if not created:
                    payment.status = 'completed'
                    payment.save()
                
                # Send order confirmation email
                try:
                    send_order_confirmation_email(order)
                except Exception as email_error:
                    logger.error(f"Failed to send order confirmation email: {str(email_error)}")
                
                logger.info(f"Payment {payment_id} for order {order.id} processed successfully")
                
            except Order.DoesNotExist:
                logger.error(f"Order with razorpay_order_id {order_id} not found")
                return JsonResponse({'status': 'error', 'message': 'Order not found'}, status=404)
            
            except Exception as e:
                logger.error(f"Error processing payment: {str(e)}", exc_info=True)
                return JsonResponse({'status': 'error', 'message': 'Error processing payment'}, status=500)
        
        return JsonResponse({'status': 'success'})
        
    except Exception as e:
        logger.error(f"Error handling webhook: {str(e)}", exc_info=True)
        return JsonResponse({'status': 'error', 'message': 'Internal server error'}, status=500)


def handle_direct_payment_verification(request, payment_data):
    """Handle direct payment verification from frontend"""
    try:
        # Get payment method from request or detect from data
        payment_method = payment_data.get('payment_method', 'razorpay')
        
        if payment_method == 'razorpay':
            razorpay_payment_id = payment_data.get('razorpay_payment_id')
            razorpay_order_id = payment_data.get('razorpay_order_id')
            razorpay_signature = payment_data.get('razorpay_signature')
            
            logger.info(f"Processing Razorpay verification - Payment ID: {razorpay_payment_id}, Order ID: {razorpay_order_id}")
            
            if not all([razorpay_payment_id, razorpay_order_id, razorpay_signature]):
                error_msg = 'Missing payment parameters. '
                error_msg += f'Payment ID: {razorpay_payment_id}, '
                error_msg += f'Order ID: {razorpay_order_id}, '
                error_msg += f'Signature: {bool(razorpay_signature)}'
                
                logger.error(error_msg)
                return JsonResponse({
                    'success': False,
                    'error': 'Missing payment parameters',
                    'payment_method': payment_method,
                    'debug': error_msg
                }, status=400)
            
            try:
                # Verify payment with Razorpay
                razorpay_service = get_razorpay_service()
                if not razorpay_service:
                    return JsonResponse({'success': False, 'error': 'Payment service unavailable'}, status=500)
                
                result = razorpay_service.verify_payment(
                    razorpay_payment_id,
                    razorpay_order_id,
                    razorpay_signature
                )
                
                logger.info(f"Razorpay verification result: {result}")
                
                if not result.get('success'):
                    error_msg = result.get('error', 'Payment verification failed')
                    logger.error(f"Payment verification failed: {error_msg}")
                    return JsonResponse({
                        'success': False,
                        'error': error_msg,
                        'payment_method': payment_method,
                        'debug': str(result)
                    }, status=400)
                    
            except Exception as e:
                logger.error(f"Error in Razorpay verification: {str(e)}", exc_info=True)
                return JsonResponse({
                    'success': False,
                    'error': 'Error processing payment verification',
                    'payment_method': payment_method,
                    'debug': str(e)
                }, status=500)
            
            order = result.get('order')
            if not order:
                error_msg = f'Order not found in verification result for Razorpay Order ID: {razorpay_order_id}'
                logger.error(error_msg)
                return JsonResponse({
                    'success': False,
                    'error': 'Order not found',
                    'payment_method': payment_method,
                    'debug': error_msg
                }, status=404)
            
            # Update order status
            order.status = 'confirmed'
            order.payment_status = 'paid'
            order.save()
            
            # Create or update payment record
            payment, created = Payment.objects.get_or_create(
                order=order,
                defaults={
                    'amount': order.total_amount,
                    'status': 'completed',
                    'payment_method': 'razorpay',
                    'gateway': 'razorpay',
                    'gateway_payment_id': razorpay_payment_id,
                    'gateway_order_id': razorpay_order_id,
                    'gateway_signature': razorpay_signature,
                    'gateway_response': json.dumps(payment_data)
                }
            )
            
            if not created:
                payment.status = 'completed'
                payment.gateway_payment_id = razorpay_payment_id
                payment.gateway_order_id = razorpay_order_id
                payment.gateway_signature = razorpay_signature
                payment.gateway_response = json.dumps(payment_data)
                payment.save()
            
            # Send order confirmation email
            try:
                send_order_confirmation_email(order)
            except Exception as e:
                logger.error(f"Failed to send order confirmation email: {str(e)}")
            
            # Clear cart and session
            try:
                clear_checkout_session(request, request.user.customer)
            except Exception as e:
                logger.warning(f"Failed to clear checkout session: {str(e)}")
            
            # Redirect to success page
            success_url = reverse('payment_success', args=[order.id])
            logger.info(f"Payment successful, redirecting to: {success_url}")
            
            # If this is an AJAX request, return JSON
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': True,
                    'message': 'Payment successful',
                    'order_id': order.id,
                    'redirect_url': success_url
                })
            # Otherwise redirect directly
            return redirect(success_url)
        
        else:
            return JsonResponse({
                'success': False,
                'error': f'Unsupported payment method: {payment_method}'
            }, status=400)
            
    except Exception as e:
        logger.error(f"Error handling direct payment verification: {str(e)}", exc_info=True)
        return JsonResponse({
            'success': False,
            'error': 'Error processing payment verification',
            'debug': str(e)
        }, status=500)


def verify_razorpay_webhook(view_func):
    """
    Custom decorator to verify Razorpay webhook signature.
    This ensures the request is coming from Razorpay servers.
    """
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        # For Razorpay webhook, we'll verify the signature
        if request.method == 'POST' and 'HTTP_X_RAZORPAY_SIGNATURE' in request.META:
            # Get the webhook secret from settings
            webhook_secret = getattr(settings, 'RAZORPAY_WEBHOOK_SECRET', '')
            if not webhook_secret:
                logger.error("RAZORPAY_WEBHOOK_SECRET not configured in settings")
                return JsonResponse({'error': 'Server configuration error'}, status=500)
                
            # Get the signature and request body
            signature = request.META['HTTP_X_RAZORPAY_SIGNATURE']
            body = request.body
            
            # Verify the signature
            try:
                get_razorpay_service().client.utility.verify_webhook_signature(
                    body.decode('utf-8'),
                    signature,
                    webhook_secret
                )
                # If verification passes, process the webhook
                return view_func(request, *args, **kwargs)
            except Exception as e:
                logger.error(f"Webhook signature verification failed: {str(e)}")
                return JsonResponse({'error': 'Invalid signature'}, status=400)
        
        # For regular form submissions, use CSRF protection
        return csrf_protect(view_func)(request, *args, **kwargs)
    
    return _wrapped_view

from django.conf import settings
import json
import logging

# Import the new models explicitly to avoid any import issues
from .models import (
    NewsletterSubscription, ReturnRequest, ReturnRequestImage, 
    OrderStatusHistory, ContactMessage, Cart, CartItem, Product, Category, Order, OrderItem, Address, Wishlist, Coupon, Payment
)

logger = logging.getLogger(__name__)

def csrf_failure(request, reason=""):
    """
    Custom view for handling CSRF verification failures.
    Returns a user-friendly error page with a 403 status code.
    """
    context = {
        'title': 'Session Expired',
        'message': 'Your session has expired. Please refresh the page and try again.',
        'status_code': 403
    }
    return render(request, 'error.html', context, status=403)


def home(request):
    """Home page with featured products and categories"""
    try:
        featured_products = Product.objects.filter(is_featured=True, is_active=True)[:8]
        categories = Category.objects.filter(is_active=True)[:6]
        latest_products = Product.objects.filter(is_active=True).order_by('-created_at')[:4]
        
        context = {
            'featured_products': featured_products,
            'categories': categories,
            'latest_products': latest_products,
        }
        return render(request, 'home.html', context)
    except Exception as e:
        messages.error(request, f'Error loading home page: {str(e)}')
        return render(request, 'home.html', {})

def product_list(request):
    """Product listing page with search and filter functionality"""
    try:
        products = Product.objects.filter(is_active=True)
        
        # Search functionality
        query = request.GET.get('query')
        if query:
            products = products.filter(
                Q(name__icontains=query) | 
                Q(description__icontains=query) |
                Q(category__name__icontains=query)
            )
        
        # Category filter
        category_slug = request.GET.get('category')
        if category_slug:
            products = products.filter(category__slug=category_slug)
        
        # Price filter
        min_price = request.GET.get('min_price')
        max_price = request.GET.get('max_price')
        if min_price:
            try:
                products = products.filter(price__gte=float(min_price))
            except ValueError:
                messages.error(request, 'Invalid minimum price')
        if max_price:
            try:
                products = products.filter(price__lte=float(max_price))
            except ValueError:
                messages.error(request, 'Invalid maximum price')
        
        # Stock filter
        in_stock_only = request.GET.get('in_stock_only')
        if in_stock_only:
            products = products.filter(stock_quantity__gt=0)
        
        # Sorting
        sort_by = request.GET.get('sort_by', '-created_at')
        valid_sort_fields = ['name', '-name', 'price', '-price', '-created_at', 'created_at']
        if sort_by in valid_sort_fields:
            products = products.order_by(sort_by)
        else:
            products = products.order_by('-created_at')
        
        # Pagination 
        paginator = Paginator(products, 12)
        page_number = request.GET.get('page')
        try:
            page_obj = paginator.get_page(page_number)
        except:
            page_obj = paginator.get_page(1)
        
        categories = Category.objects.filter(is_active=True)
        
        context = {
            'products': page_obj,
            'categories': categories,
            'search_form': ProductSearchForm(request.GET),
        }
        return render(request, 'products.html', context)
    except Exception as e:
        messages.error(request, f'Error loading products: {str(e)}')
        return render(request, 'products.html', {'products': [], 'categories': []})

def product_detail(request, slug):
    """Product detail page with reviews and related products"""
    try:
        product = get_object_or_404(Product, slug=slug, is_active=True)
        reviews = product.reviews.filter(is_approved=True)
        related_products = Product.objects.filter(
            category=product.category, 
            is_active=True
        ).exclude(id=product.id)[:4]
        
        # Calculate average rating
        avg_rating = reviews.aggregate(Avg('rating'))['rating__avg'] or 0
        
        if request.method == 'POST' and request.user.is_authenticated:
            review_form = ReviewForm(request.POST)
            if review_form.is_valid():
                review = review_form.save(commit=False)
                review.product = product
                review.customer = request.user.customer
                review.save()
                messages.success(request, 'Review submitted successfully!')
                return redirect('product_detail', slug=slug)
            else:
                messages.error(request, 'Please correct the errors in your review.')
        else:
            review_form = ReviewForm()
        
        context = {
            'product': product,
            'reviews': reviews,
            'related_products': related_products,
            'review_form': review_form,
            'avg_rating': avg_rating,
        }
        return render(request, 'product_detail.html', context)
    except Http404:
        # Let 404 propagate for non-existent products
        raise
    except Exception as e:
        messages.error(request, f'Error loading product: {str(e)}')
        return redirect('products')

def category_detail(request, slug):
    """Category detail page"""
    try:
        category = get_object_or_404(Category, slug=slug, is_active=True)
        products = Product.objects.filter(category=category, is_active=True)
        
        # Pagination
        paginator = Paginator(products, 12)
        page_number = request.GET.get('page')
        try:
            page_obj = paginator.get_page(page_number)
        except:
            page_obj = paginator.get_page(1)
        
        context = {
            'category': category,
            'products': page_obj,
        }
        return render(request, 'category_detail.html', context)
    except Http404:
        # Let 404 propagate for non-existent categories
        raise
    except Exception as e:
        messages.error(request, f'Error loading category: {str(e)}')
        return redirect('products')

@login_required
def add_to_cart(request, product_id):
    """Add product to cart. Supports POST (with quantity) and GET (defaults to 1)."""
    try:
        product = get_object_or_404(Product, id=product_id, is_active=True)
        quantity = 1
        if request.method == 'POST':
            try:
                quantity = int(request.POST.get('quantity', 1))
            except (TypeError, ValueError):
                quantity = 1

        if quantity <= 0:
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': False,
                    'message': 'Quantity must be greater than 0!'
                })
            messages.error(request, 'Quantity must be greater than 0!')
            return redirect('product_detail', slug=product.slug)

        if quantity > product.stock_quantity:
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': False,
                    'message': 'Not enough stock available!'
                })
            messages.error(request, 'Not enough stock available!')
            return redirect('product_detail', slug=product.slug)

        cart, created = Cart.objects.get_or_create(
            customer=request.user.customer,
            is_active=True
        )

        cart_item, created = CartItem.objects.get_or_create(
            cart=cart,
            product=product,
            defaults={'quantity': quantity}
        )

        if not created:
            cart_item.quantity += quantity
            cart_item.save()

        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'success': True,
                'message': f'{product.name} added to cart!',
                'cart_count': cart.total_items
            })

        messages.success(request, f'{product.name} added to cart!')
        return redirect('cart')
    except Http404:
        raise
    except Exception as e:
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'success': False,
                'message': f'Error adding to cart: {str(e)}'
            })
        messages.error(request, f'Error adding to cart: {str(e)}')
        return redirect('products')

@login_required
def cart(request):
    """Shopping cart page"""
    try:
        cart = Cart.objects.get(customer=request.user.customer, is_active=True)
        cart_items = cart.items.all()
    except Cart.DoesNotExist:
        cart = None
        cart_items = []
    
    if request.method == 'POST':
        try:
            # Update quantities
            for item in cart_items:
                quantity = request.POST.get(f'quantity_{item.id}')
                if quantity:
                    new_quantity = int(quantity)
                    if new_quantity > 0:
                        if new_quantity <= item.product.stock_quantity:
                            item.quantity = new_quantity
                            item.save()
                        else:
                            messages.error(request, f'Not enough stock for {item.product.name}')
                    else:
                        item.delete()
                else:
                    item.delete()
            
            # Apply coupon
            coupon_code = request.POST.get('coupon_code')
            if coupon_code:
                try:
                    coupon = Coupon.objects.get(code=coupon_code)
                    if coupon.is_valid():
                        request.session['coupon_id'] = coupon.id
                        messages.success(request, f'Coupon "{coupon.code}" applied!')
                    else:
                        messages.error(request, 'Invalid or expired coupon!')
                except Coupon.DoesNotExist:
                    messages.error(request, 'Coupon not found!')
            # Fall through to re-render page with updated data (HTTP 200 expected by tests)
        except Exception as e:
            messages.error(request, f'Error updating cart: {str(e)}')
    
    # Calculate totals
    subtotal = sum(item.total_price for item in cart_items)
    shipping_cost = Decimal('50.00') if subtotal < Decimal('500.00') else Decimal('0.00')
    tax = subtotal * Decimal('0.18')  # 18% GST
    
    # Apply coupon discount
    discount = Decimal('0.00')
    if 'coupon_id' in request.session:
        try:
            coupon = Coupon.objects.get(id=request.session['coupon_id'])
            if coupon.is_valid():
                if coupon.discount_type == 'percentage':
                    discount = subtotal * (coupon.discount_value / 100)
                else:
                    discount = coupon.discount_value
        except Coupon.DoesNotExist:
            del request.session['coupon_id']
    
    total = subtotal + shipping_cost + tax - discount
    
    context = {
        'cart': cart,
        'cart_items': cart_items,
        'subtotal': subtotal,
        'shipping_cost': shipping_cost,
        'tax': tax,
        'discount': discount,
        'total': total,
    }
    return render(request, 'cart.html', context)

@login_required
def remove_from_cart(request, item_id):
    """Remove item from cart"""
    try:
        cart_item = get_object_or_404(CartItem, id=item_id, cart__customer=request.user.customer)
        cart_item.delete()
        messages.success(request, 'Item removed from cart!')
    except Exception as e:
        messages.error(request, f'Error removing item: {str(e)}')
    return redirect('cart')

import logging

logger = logging.getLogger(__name__)

@login_required
def checkout(request):
    """
    Checkout view that handles both AJAX and regular form submissions.
    Supports both Razorpay and COD payment methods.
    """
    logger.info(f"Checkout request - Method: {request.method}, User: {request.user}")
    
    # Log request data for debugging (excluding sensitive fields)
    request_data = request.POST.dict() if request.method == 'POST' else {}
    safe_request_data = {k: v for k, v in request_data.items() if 'password' not in k.lower() and 'token' not in k.lower()}
    logger.debug(f"Checkout request data: {safe_request_data}")
    
    # Log Razorpay configuration status
    logger.debug(f"RAZORPAY_KEY_ID: {getattr(settings, 'RAZORPAY_KEY_ID', 'Not set')}")
    logger.debug(f"RAZORPAY_KEY_SECRET: {'*' * 8 + getattr(settings, 'RAZORPAY_KEY_SECRET', 'Not set')[-4:] if getattr(settings, 'RAZORPAY_KEY_SECRET', None) else 'Not set'}")
    
    # Check if Razorpay is configured
    razorpay_configured = bool(settings.RAZORPAY_KEY_ID and settings.RAZORPAY_KEY_SECRET)
    
    # Test Razorpay connection
    try:
        import razorpay
        client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))
        test_payment = client.payment.all()
        logger.info("Successfully connected to Razorpay API")
    except Exception as e:
        logger.error(f"Razorpay connection test failed: {str(e)}")
        messages.error(request, f"Payment service is currently unavailable. Please try again later. Error: {str(e)}")
    
    # Check for active cart
    try:
        cart, created = Cart.objects.get_or_create(customer=request.user.customer, is_active=True)
        cart_items = cart.items.select_related('product')
        
        # Initialize addresses variable
        addresses = Address.objects.none()
        
        # Get user's addresses if user is authenticated and has customer profile
        if request.user.is_authenticated and hasattr(request.user, 'customer'):
            addresses = Address.objects.filter(customer=request.user.customer).order_by('-is_default_shipping')
        
        if not cart_items:
            raise Cart.DoesNotExist("Cart is empty")
            
    except Cart.DoesNotExist as e:
        error_msg = f"No active cart found for user {request.user}: {str(e)}"
        logger.error(error_msg)
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest' or request.content_type == 'application/json':
            return JsonResponse({
                'success': False,
                'error': 'Your cart is empty!',
                'debug': error_msg if settings.DEBUG else None,
                'redirect': reverse('products')
            }, status=400)
        messages.error(request, 'Your cart is empty!')
        return redirect('products')
    
    # Handle form submission
    if request.method == 'POST':
        is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest' or request.content_type == 'application/json'
        logger.info(f"Processing {'AJAX ' if is_ajax else ''}checkout form submission")
        
        # Parse request data
        if request.content_type == 'application/json':
            try:
                form_data = json.loads(request.body)
                logger.info(f"Received JSON form data: {form_data}")
                form = CheckoutForm(form_data)
            except json.JSONDecodeError as e:
                error_msg = f"Invalid JSON data: {str(e)}"
                logger.error(error_msg)
                return JsonResponse({
                    'success': False,
                    'error': 'Invalid request data',
                    'debug': error_msg if settings.DEBUG else None
                }, status=400)
        else:
            logger.info(f"Received form data: {request.POST}")
            form = CheckoutForm(request.POST)
            
        # Log form data for debugging
        logger.info(f"Form data received: {dict(request.POST)}")
        logger.info(f"Form is bound: {form.is_bound}")
        logger.info(f"Form is valid: {form.is_valid()}")
        
        # Log payment method
        payment_method = request.POST.get('payment_method') or (form.cleaned_data.get('payment_method') if form.is_bound and form.is_valid() else None)
        logger.info(f"Payment method received: {payment_method}")
        if not payment_method:
            logger.warning("No payment method specified in request")
        
        # Validate form
        if not form.is_valid():
            logger.warning(f"Form validation errors: {form.errors}")
            logger.warning(f"Form data that failed validation: {dict(request.POST)}")
            
            if is_ajax:
                # Convert form errors to a more frontend-friendly format
                errors = {}
                for field, error_list in form.errors.items():
                    errors[field] = [str(error) for error in error_list]
                
                return JsonResponse({
                    'success': False,
                    'error': 'Form validation failed',
                    'errors': errors,
                    'message': 'Please correct the errors below.'
                }, status=400)
                
            return render(request, 'checkout.html', {
                'form': form,
                'cart_items': cart_items,
                'subtotal': sum(item.total_price for item in cart_items),
                'shipping_cost': Decimal('50.00') if sum(item.total_price for item in cart_items) < Decimal('500.00') else Decimal('0.00'),
                'razorpay_configured': razorpay_configured
            })
            
        try:
            with transaction.atomic():
                # Calculate order totals
                subtotal = sum(item.total_price for item in cart_items)
                shipping_cost = Decimal('50.00') if subtotal < Decimal('500.00') else Decimal('0.00')
                tax = subtotal * Decimal('0.18')  # 18% tax
                total = subtotal + shipping_cost + tax
                
                # Apply coupon if available
                coupon = None
                if 'coupon_id' in request.session:
                    try:
                        coupon = Coupon.objects.get(id=request.session['coupon_id'])
                        if not coupon.is_valid():
                            coupon = None
                            del request.session['coupon_id']
                    except Coupon.DoesNotExist:
                        del request.session['coupon_id']
                
                # Create order
                order = Order.objects.create(
                    customer=request.user.customer,
                    status='pending',
                    payment_method=form.cleaned_data.get('payment_method', 'cod'),
                    subtotal=subtotal,
                    shipping_cost=shipping_cost,
                    tax=tax,
                    total_amount=total,
                    shipping_address=form.cleaned_data['shipping_address'],
                    billing_address=form.cleaned_data['shipping_address'],  # Use same address for billing
                    phone=form.cleaned_data['shipping_phone'],
                    email=request.user.email
                )
                
                # Create order items
                for item in cart_items:
                    OrderItem.objects.create(
                        order=order,
                        product=item.product,
                        quantity=item.quantity,
                        price=item.product.current_price
                    )
                
                # Handle payment based on method
                payment_method = form.cleaned_data.get('payment_method', 'cod')
                
                if payment_method == 'razorpay':
                    # Check if Razorpay is configured
                    if not settings.RAZORPAY_KEY_ID or not settings.RAZORPAY_KEY_SECRET:
                        if is_ajax:
                            return JsonResponse({
                                'success': False,
                                'error': 'Online payment is not available. Please use Cash on Delivery.',
                                'redirect': reverse('checkout')
                            }, status=400)
                        messages.warning(request, 'Online payment is not available. Please use Cash on Delivery.')
                        return redirect('checkout')
                    
                    # Create Razorpay order
                    razorpay_service = get_razorpay_service()
                    if razorpay_service:
                        razorpay_result = razorpay_service.create_order(order)
                        logger.info(f"Razorpay order creation result: {razorpay_result}")
                    else:
                        raise Exception("Razorpay service is not available")
                    
                    if not razorpay_result.get('success'):
                        raise Exception(f"Failed to create Razorpay order: {razorpay_result.get('error')}")
                    
                    # Store order ID in session for verification
                    razorpay_order_id = razorpay_result.get('order_id')
                    logger.info(f"Storing Razorpay order ID in session: {razorpay_order_id}")
                    request.session['razorpay_order_id'] = razorpay_order_id
                    request.session['order_id'] = order.id
                    
                    # Force session save and verify
                    request.session.save()
                    request.session.modified = True
                    logger.info(f"Session saved. Verifying - order_id: {request.session.get('order_id')}, razorpay_order_id: {request.session.get('razorpay_order_id')}")
                    
                    # Prepare response data
                    response_data = {
                        'success': True,
                        'redirect_url': reverse('payment'),
                        'order_id': order.id,
                        'razorpay_order_id': razorpay_order_id,  # Add Razorpay order ID
                        'amount': int(order.total_amount * 100),  # Convert to paise
                        'currency': 'INR',
                        'key': settings.RAZORPAY_KEY_ID,
                        'name': 'KV Store',
                        'description': f'Order #{order.id}',
                        'prefill': {
                            'name': f"{request.user.first_name} {request.user.last_name}",
                            'email': request.user.email,
                            'contact': form.cleaned_data['shipping_phone']
                        }
                    }
                    
                    # Clear cart after successful order creation
                    cart.is_active = False
                    cart.save()
                    
                    if is_ajax:
                        return JsonResponse(response_data)
                    
                    # For non-AJAX requests, directly render payment page instead of redirecting
                    # This ensures session data is preserved
                    try:
                        # Get Razorpay client
                        razorpay_client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))
                        
                        # Get order details from Razorpay
                        razorpay_order = razorpay_client.order.fetch(razorpay_order_id)
                        
                        # Prepare context for the payment template
                        context = {
                            'order': order,
                            'razorpay_order_id': razorpay_order_id,
                            'razorpay_key_id': settings.RAZORPAY_KEY_ID,
                            'amount': int(order.total_amount * 100),  # Convert to paise
                            'currency': 'INR',
                            'callback_url': request.build_absolute_uri(reverse('payment_callback')),
                            'customer_name': f"{request.user.first_name} {request.user.last_name}",
                            'customer_email': request.user.email,
                            'customer_phone': order.phone,
                            'razorpay_configured': bool(settings.RAZORPAY_KEY_ID and settings.RAZORPAY_KEY_SECRET),
                        }
                        
                        # Add debugging information
                        logger.info(f"Checkout view - Direct payment render - Order ID: {order.id}, Razorpay Order ID: {razorpay_order_id}")
                        logger.info(f"Session data - order_id: {request.session.get('order_id')}, razorpay_order_id: {request.session.get('razorpay_order_id')}")
                        
                        return render(request, 'payment.html', context)
                        
                    except Exception as e:
                        logger.error(f"Error rendering payment page directly: {str(e)}")
                        # Fallback to redirect if direct render fails
                        return redirect('payment')
                
                else:  # COD (Cash on Delivery)
                    order.status = 'confirmed'
                    order.save()
                    
                    # Clear cart
                    cart.is_active = False
                    cart.save()
                    
                    # Clear coupon if used
                    if 'coupon_id' in request.session:
                        del request.session['coupon_id']
                    
                    # Send order confirmation email
                    try:
                        send_order_confirmation_email(order)
                    except Exception as email_error:
                        logger.error(f"Failed to send order confirmation email: {str(email_error)}")
                    
                    if is_ajax:
                        return JsonResponse({
                            'success': True,
                            'order_id': order.id,
                            'order_number': order.order_number,
                            'redirect_url': reverse('order_detail', args=[order.id])
                        })
                    
                    messages.success(request, 'Your order has been placed successfully!')
                    return redirect('order_detail', order_id=order.id)
                    
        except Exception as e:
            logger.error(f"Error during checkout: {str(e)}", exc_info=True)
            
            if is_ajax or request.content_type == 'application/json':
                return JsonResponse({
                    'success': False,
                    'error': 'An error occurred while processing your order. Please try again.',
                    'debug': str(e) if settings.DEBUG else None,
                    'redirect': reverse('checkout')
                }, status=500)
            
            messages.error(request, 'An error occurred while processing your order. Please try again.')
            return redirect('checkout')
    
    # GET request - show checkout form
    # Prefill form with user's default shipping address if available
    initial = {}
    try:
        customer = request.user.customer
        default_address = customer.addresses.filter(is_default_shipping=True).first()
        if default_address:
            initial.update({
                'shipping_first_name': default_address.first_name or request.user.first_name,
                'shipping_last_name': default_address.last_name or request.user.last_name,
                'shipping_address': default_address.address,
                'shipping_city': default_address.city,
                'shipping_state': default_address.state,
                'shipping_zip_code': default_address.zip_code,
                'shipping_phone': default_address.phone or getattr(customer, 'phone', ''),
                'shipping_country': getattr(default_address, 'country', 'India')
            })
    except Exception as e:
        logger.error(f"Error loading default address: {str(e)}")
        initial = {}
    
    form = CheckoutForm(initial=initial)
    
    # Check if Razorpay is configured
    razorpay_configured = bool(settings.RAZORPAY_KEY_ID and settings.RAZORPAY_KEY_SECRET)
    
    # Get available coupons
    available_coupons = Coupon.objects.filter(
        is_active=True, 
        valid_from__lte=timezone.now(), 
        valid_until__gte=timezone.now()
    )
    
    # Calculate totals
    subtotal = sum(item.total_price for item in cart_items)
    shipping_cost = Decimal('50.00') if subtotal < Decimal('500.00') else Decimal('0.00')
    tax = subtotal * Decimal('0.18')
    
    # Apply coupon discount if any
    discount = Decimal('0.00')
    if 'coupon_id' in request.session:
        try:
            coupon = Coupon.objects.get(id=request.session['coupon_id'])
            if coupon.is_valid():
                if coupon.discount_type == 'percentage':
                    discount = subtotal * (coupon.discount_value / 100)
                else:
                    discount = coupon.discount_value
        except Coupon.DoesNotExist:
            del request.session['coupon_id']
    
    total = subtotal + shipping_cost + tax - discount
    
    context = {
        'form': form,
        'cart_items': cart_items,
        'subtotal': subtotal,
        'shipping_cost': shipping_cost,
        'tax': tax,
        'discount': discount,
        'total': total,
        'addresses': addresses,
        'available_coupons': available_coupons,
        'razorpay_key_id': settings.RAZORPAY_KEY_ID,
        'razorpay_currency': 'INR'
    }
    
    # Handle POST request (form submission)
    if request.method == 'POST':
        is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'
        logger.info(f"Processing {'AJAX ' if is_ajax else ''}checkout form submission")
        
        # Parse request data
        if request.content_type == 'application/json':
            try:
                form_data = json.loads(request.body)
                form = CheckoutForm(form_data)
            except json.JSONDecodeError as e:
                error_msg = f"Invalid JSON data: {str(e)}"
                logger.error(error_msg)
                return JsonResponse({
                    'success': False,
                    'error': 'Invalid request data',
                    'debug': error_msg
                }, status=400)
        else:
            form = CheckoutForm(request.POST)
        
        # Validate form
        if not form.is_valid():
            logger.warning(f"Form validation errors: {form.errors}")
            if is_ajax:
                return JsonResponse({
                    'success': False,
                    'error': 'Form validation failed',
                    'errors': form.errors
                }, status=400)
            return render(request, 'checkout.html', {
                'form': form,
                'cart_items': cart_items,
                'subtotal': subtotal,
                'shipping_cost': shipping_cost,
                'tax': tax,
                'discount': discount,
                'total': total,
                'addresses': addresses,
                'available_coupons': available_coupons,
                'razorpay_key_id': settings.RAZORPAY_KEY_ID,
                'razorpay_currency': 'INR',
                'razorpay_configured': razorpay_configured
            })
        
        try:
            with transaction.atomic():
                # Create order
                order = Order.objects.create(
                    customer=request.user.customer,
                    subtotal=subtotal,
                    tax=tax,
                    shipping_cost=shipping_cost,
                    total_amount=total,
                    payment_method=form.cleaned_data.get('payment_method', 'cod'),
                    shipping_address=form.cleaned_data['shipping_address'],
                    billing_address=form.cleaned_data.get('billing_address', form.cleaned_data['shipping_address']),
                    phone=form.cleaned_data['shipping_phone'],
                    email=request.user.email,
                    notes=form.cleaned_data.get('notes', ''),
                )
                
                # Create order items and update product stock
                for item in cart_items:
                    OrderItem.objects.create(
                        order=order,
                        product=item.product,
                        quantity=item.quantity,
                        price=item.product.current_price
                    )
                    # Update product stock
                    item.product.stock_quantity -= item.quantity
                    item.product.save()
                
                # Clear the cart
                cart.is_active = False
                cart.save()
                
                # Clear coupon if used
                if 'coupon_id' in request.session:
                    del request.session['coupon_id']
                
                # Handle payment based on method
                payment_method = form.cleaned_data.get('payment_method', 'cod')
                
                if payment_method == 'razorpay':
                    razorpay_service = get_razorpay_service()
                    if razorpay_service:
                        razorpay_result = razorpay_service.create_order(order)
                        
                        if not razorpay_result.get('success'):
                            error_msg = razorpay_result.get('error', 'Failed to create Razorpay order')
                            logger.error(f"Razorpay order creation failed: {error_msg}")
                            raise Exception(f"Payment gateway error: {error_msg}")
                    else:
                        raise Exception("Razorpay service is not available")
                    
                    # Store order in session for payment completion
                    request.session['pending_order_id'] = order.id
                    logger.info(f"Razorpay order created for order {order.order_number}")
                    
                    response_data = {
                        'success': True,
                        'order_id': order.id,
                        'razorpay_order_id': razorpay_result.get('order_id'),
                        'razorpay_key_id': settings.RAZORPAY_KEY_ID,
                        'amount': int(order.total_amount * 100),  # Convert to paise
                        'currency': 'INR',
                        'redirect_url': reverse('payment_page')
                    }
                    
                    if is_ajax:
                        return JsonResponse(response_data)
                    
                    # For non-AJAX requests, redirect to payment page
                    return redirect('payment_page')
                
                else:  # COD (Cash on Delivery)
                    order.status = 'confirmed'
                    order.save()
                    
                    # Send order confirmation email
                    try:
                        send_order_confirmation_email(order)
                    except Exception as e:
                        logger.error(f"Failed to send order confirmation email: {str(e)}")
                    
                    if is_ajax:
                        return JsonResponse({
                            'success': True,
                            'order_id': order.id,
                            'order_number': order.order_number,
                            'redirect_url': reverse('order_detail', args=[order.id])
                        })
                    
                    messages.success(request, 'Your order has been placed successfully!')
                    return redirect('order_detail', order_id=order.id)
        
        except Exception as e:
            logger.error(f"Error during checkout: {str(e)}", exc_info=True)
            error_msg = "An error occurred while processing your order. Please try again."
            
            if is_ajax:
                return JsonResponse({
                    'success': False,
                    'error': error_msg,
                    'debug': str(e) if settings.DEBUG else None
                }, status=500)
            
            messages.error(request, error_msg)
            return redirect('checkout')
    
    # GET request - show checkout form with pre-filled data
    form = CheckoutForm(initial=initial)
    
    # Calculate totals for display
    subtotal = sum(item.total_price for item in cart_items)
    shipping_cost = Decimal('50.00') if subtotal < Decimal('500.00') else Decimal('0.00')
    tax = subtotal * Decimal('0.18')
    
    # Apply coupon discount if any
    discount = Decimal('0.00')
    if 'coupon_id' in request.session:
        try:
            coupon = Coupon.objects.get(id=request.session['coupon_id'])
            if coupon.is_valid():
                if coupon.discount_type == 'percentage':
                    discount = subtotal * (coupon.discount_value / 100)
                else:
                    discount = coupon.discount_value
        except Coupon.DoesNotExist:
            del request.session['coupon_id']
    
    total = subtotal + shipping_cost + tax - discount
    
    # Get saved addresses for the user
    customer = request.user.customer
    addresses = customer.addresses.all()
    
    # Pre-fill form with default address if available
    default_address = customer.addresses.filter(is_default_shipping=True).first()
    initial = {}
    if default_address:
        initial.update({
            'shipping_first_name': default_address.first_name or request.user.first_name,
            'shipping_last_name': default_address.last_name or request.user.last_name,
            'shipping_address': default_address.address,
            'shipping_city': default_address.city,
            'shipping_state': default_address.state,
            'shipping_zip_code': default_address.zip_code,
            'shipping_phone': default_address.phone or customer.phone,
        })
    
    form = CheckoutForm(initial=initial)
    
    context = {
        'form': form,
        'cart_items': cart_items,
        'subtotal': subtotal,
        'shipping_cost': shipping_cost,
        'tax': tax,
        'discount': discount,
        'total': total,
        'addresses': addresses,
        'razorpay_configured': razorpay_configured
    }
    return render(request, 'checkout.html', context)

@login_required
def order_list(request):
    """Order list page"""
    try:
        orders = Order.objects.filter(customer=request.user.customer).order_by('-created_at')
        context = {'orders': orders}
        return render(request, 'order_list_dark.html', context)
    except Exception as e:
        messages.error(request, f'Error loading orders: {str(e)}')
        return render(request, 'order_list_dark.html', {'orders': []})

def test_urls(request):
    from django.urls import get_resolver
    from django.http import HttpResponse
    
    try:
        resolver = get_resolver()
        urls = []
        
        def get_urls(url_patterns, prefix=''):
            for pattern in url_patterns:
                try:
                    full_pattern = f"{prefix}{str(pattern.pattern)}"
                    urls.append(full_pattern)
                    if hasattr(pattern, 'url_patterns'):
                        get_urls(pattern.url_patterns, prefix=full_pattern)
                except Exception as e:
                    urls.append(f"Error processing pattern: {pattern} - {str(e)}")
        
        get_urls(resolver.url_patterns)
        return HttpResponse("\n".join(urls), content_type="text/plain")
    except Exception as e:
        return HttpResponse(f"Error getting URLs: {str(e)}", status=500)

@login_required
def order_detail(request, order_id):
    """Order detail page"""
    try:
        order = get_object_or_404(Order, id=order_id, customer=request.user.customer)
        context = {'order': order}
        return render(request, 'order_detail_dark.html', context)
    except Exception as e:
        messages.error(request, f'Error loading order: {str(e)}')
        return redirect('order_list')

@login_required
def wishlist(request):
    """Wishlist page"""
    try:
        wishlist_items = Wishlist.objects.filter(customer=request.user.customer)
        context = {'wishlist_items': wishlist_items}
        return render(request, 'wishlist_dark.html', context)
    except Exception as e:
        messages.error(request, f'Error loading wishlist: {str(e)}')
        return render(request, 'wishlist_dark.html', {'wishlist_items': []})

@csrf_exempt
@login_required
def add_to_wishlist(request, product_id):
    """
    Add/remove product from wishlist.
    Handles both AJAX and regular requests.
    Returns JSON for AJAX, redirects for regular requests.
    """
    print(f"DEBUG: add_to_wishlist called. Method: {request.method}, User: {request.user}, Auth: {request.user.is_authenticated}")
    print(f"DEBUG: Headers: {dict(request.headers)}")
    
    if request.method != 'POST' or not request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        print("DEBUG: Invalid request method or not AJAX")
        return redirect('home')
        
    response_data = {'success': False, 'message': '', 'added': False, 'wishlist_count': 0}
    
    if not request.user.is_authenticated:
        response_data['message'] = 'Please log in to update your wishlist.'
        print("DEBUG: User not authenticated")
        return JsonResponse(response_data, status=401)
    
    try:
        product = get_object_or_404(Product, id=product_id, is_active=True)
        wishlist_item, created = Wishlist.objects.get_or_create(
            customer=request.user.customer,
            product=product
        )
        
        if created:
            response_data.update({
                'success': True,
                'message': f'{product.name} added to wishlist!',
                'added': True,
                'wishlist_count': request.user.customer.wishlist.count()
            })
        else:
            # Item exists, so remove it
            wishlist_item.delete()
            response_data.update({
                'success': True,
                'message': f'{product.name} removed from wishlist',
                'added': False,
                'wishlist_count': request.user.customer.wishlist.count()
            })
            
    except Exception as e:
        logger.error(f'Wishlist error: {str(e)}')
        response_data['message'] = 'Error updating wishlist. Please try again.'
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse(response_data)
    else:
        if response_data['success']:
            messages.success(request, response_data['message'])
        else:
            messages.error(request, response_data['message'])
        return redirect(request.META.get('HTTP_REFERER', 'home'))

@csrf_exempt
@login_required
def remove_from_wishlist(request, item_id):
    """
    Remove item from wishlist.
    Handles both AJAX and regular requests.
    """
    response_data = {'success': False, 'message': ''}
    
    try:
        wishlist_item = get_object_or_404(Wishlist, id=item_id, customer=request.user.customer)
        product_name = wishlist_item.product.name
        wishlist_item.delete()
        
        response_data.update({
            'success': True,
            'message': f'{product_name} removed from wishlist!',
            'wishlist_count': request.user.customer.wishlist_products.count()
        })
        
    except Exception as e:
        logger.error(f'Error removing from wishlist: {str(e)}')
        response_data['message'] = 'Error removing item from wishlist.'
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse(response_data)
    else:
        if response_data['success']:
            messages.success(request, response_data['message'])
        else:
            messages.error(request, response_data['message'])
        return redirect('wishlist')

@login_required
def profile(request):
    """User profile page"""
    try:
        customer = request.user.customer
        if request.method == 'POST':
            form = CustomerProfileForm(request.POST, request.FILES, instance=customer)
            if form.is_valid():
                form.save()
                messages.success(request, 'Profile updated successfully!')
                return redirect('profile')
            else:
                messages.error(request, 'Please correct the errors in your form.')
        else:
            form = CustomerProfileForm(instance=customer)

        # Related data for tabs
        orders = Order.objects.filter(customer=customer).order_by('-created_at')
        wishlist_items = Wishlist.objects.filter(customer=customer).select_related('product')

        context = {
            'form': form,
            'orders': orders,
            'wishlist_items': wishlist_items,
            # Derive a simple addresses list from Customer fields since there is no Address model
            'addresses': customer.addresses.all(),
        }
        return render(request, 'profile.html', context)
    except Exception as e:
        messages.error(request, f'Error loading profile: {str(e)}')
        return render(request, 'profile.html', {})

@login_required
def address_create(request):
    try:
        if request.method == 'POST':
            form = AddressForm(request.POST)
            if form.is_valid():
                address = form.save(commit=False)
                address.customer = request.user.customer
                if address.is_default_shipping:
                    request.user.customer.addresses.update(is_default_shipping=False)
                if address.is_default_billing:
                    request.user.customer.addresses.update(is_default_billing=False)
                address.save()
                messages.success(request, 'Address added successfully!')
                return redirect('profile')
            else:
                messages.error(request, 'Please correct the errors in your address form.')
        else:
            form = AddressForm()
        return render(request, 'address_form.html', {'form': form, 'mode': 'create'})
    except Exception as e:
        messages.error(request, f'Error adding address: {str(e)}')
        return redirect('profile')

@login_required
def address_edit(request, address_id):
    try:
        address = get_object_or_404(Address, id=address_id, customer=request.user.customer)
        if request.method == 'POST':
            form = AddressForm(request.POST, instance=address)
            if form.is_valid():
                updated = form.save(commit=False)
                if updated.is_default_shipping:
                    request.user.customer.addresses.exclude(id=address.id).update(is_default_shipping=False)
                if updated.is_default_billing:
                    request.user.customer.addresses.exclude(id=address.id).update(is_default_billing=False)
                updated.save()
                messages.success(request, 'Address updated successfully!')
                return redirect('profile')
            else:
                messages.error(request, 'Please correct the errors in your address form.')
        else:
            form = AddressForm(instance=address)
        return render(request, 'address_form.html', {'form': form, 'mode': 'edit'})
    except Exception as e:
        messages.error(request, f'Error updating address: {str(e)}')
        return redirect('profile')

@login_required
def address_delete(request, address_id):
    try:
        address = get_object_or_404(Address, id=address_id, customer=request.user.customer)
        address.delete()
        messages.success(request, 'Address deleted successfully!')
    except Exception as e:
        messages.error(request, f'Error deleting address: {str(e)}')
    return redirect('profile')

@login_required
def address_set_default(request, address_id, which):
    try:
        address = get_object_or_404(Address, id=address_id, customer=request.user.customer)
        if which == 'shipping':
            request.user.customer.addresses.update(is_default_shipping=False)
            address.is_default_shipping = True
        elif which == 'billing':
            request.user.customer.addresses.update(is_default_billing=False)
            address.is_default_billing = True
        address.save()
        messages.success(request, f'Default {which} address updated!')
    except Exception as e:
        messages.error(request, f'Error setting default address: {str(e)}')
    return redirect('profile')

def register(request):
    """User registration"""
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            try:
                user = form.save()
                auth_login(request, user)
                messages.success(request, 'Registration successful! Welcome to our store!')
                return redirect('home')
            except Exception as e:
                messages.error(request, f'Registration failed: {str(e)}')
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f'{field}: {error}')
    else:
        form = UserRegistrationForm()
    
    return render(request, 'register.html', {'form': form})

def user_login(request):
    """User login"""
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        if not username or not password:
            messages.error(request, 'Please enter both username and password!')
            return render(request, 'login.html')
        
        try:
            user = authenticate(request, username=username, password=password)
            
            if user is not None:
                auth_login(request, user)
                messages.success(request, f'Welcome back, {user.get_full_name() or user.username}!')
                return redirect('home')
            else:
                messages.error(request, 'Invalid username or password!')
        except Exception as e:
            messages.error(request, f'Login error: {str(e)}')
    
    return render(request, 'login.html')

@login_required
def user_logout(request):
    """User logout"""
    logout(request)
    messages.success(request, 'You have been logged out successfully!')
    return redirect('home')

def contact(request):
    """Contact page"""
    if request.method == 'POST':
        form = ContactForm(request.POST)
        if form.is_valid():
            # Here you would typically send an email
            messages.success(request, 'Thank you for your message! We will get back to you soon.')
            return redirect('contact')
        else:
            messages.error(request, 'Please correct the errors in your form.')
    else:
        form = ContactForm()
    
    return render(request, 'contact.html', {'form': form})

def about(request):
    """About page"""
    return render(request, 'about.html')

def search(request):
    """Search functionality"""
    query = request.GET.get('q', '')
    if query:
        try:
            products = Product.objects.filter(
                Q(name__icontains=query) | 
                Q(description__icontains=query) |
                Q(category__name__icontains=query),
                is_active=True
            )
        except Exception as e:
            messages.error(request, f'Search error: {str(e)}')
            products = Product.objects.none()
    else:
        products = Product.objects.none()
    
    context = {
        'products': products,
        'query': query,
    }
    return render(request, 'search.html', context)

# Keep old functions for backward compatibility
def login(request):
    return user_login(request)

def signup_func(request):
    return register(request)

def test(request):
    data=[{
        'name':'John',
        'age':30,
        'city':'New York',
        'is_married':True,
        'items': [1,2,3,]

    },
    {'name':'Joswqdewhn',
        'age':3320,
        'city':'New York',
        'is_married':True,
        'items': [1,2,3,]
        }
    ]
    
    return render(request, 'test.html',{'data':data})

def test_razorpay_config(request):
    """Test Razorpay configuration and return status"""
    from django.conf import settings
    import razorpay
    
    config = {
        'RAZORPAY_KEY_ID': settings.RAZORPAY_KEY_ID,
        'RAZORPAY_KEY_SECRET': f"{settings.RAZORPAY_KEY_SECRET[:4]}..." if settings.RAZORPAY_KEY_SECRET else None,
        'is_configured': bool(settings.RAZORPAY_KEY_ID and settings.RAZORPAY_KEY_SECRET)
    }
    
    # Test Razorpay client
    try:
        client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))
        payments = client.payment.all({'count': 1})
        config['connection_success'] = True
        config['test_payment_count'] = payments.get('count', 0)
    except Exception as e:
        config['connection_error'] = str(e)
    
    from django.http import JsonResponse
    return JsonResponse(config)

def producttest(request):
    context ={
        'product_form':ProductForm()
    }

    return render(request, 'producttest.html',context)

def test_images(request):
    """Test view to verify image loading"""
    from django.conf import settings
    try:
        products = Product.objects.filter(is_active=True)[:5]
        context = {
            'products': products,
            'MEDIA_ROOT': settings.MEDIA_ROOT,
        }
        return render(request, 'test_images.html', context)
    except Exception as e:
        messages.error(request, f'Error loading test images: {str(e)}')
        return render(request, 'test_images.html', {'products': []})

@login_required
def clear_checkout_session(request, customer):
    """Helper function to clear cart and session data after successful order"""
    try:
        # Clear active cart
        cart = Cart.objects.filter(customer=customer, is_active=True).first()
        if cart:
            cart.is_active = False
            cart.save()
            
        # Clear session data
        session_keys = ['pending_order_id', 'coupon_id', 'applied_coupon_code']
        for key in session_keys:
            if key in request.session:
                del request.session[key]
                
    except Exception as e:
        logger.error(f"Error clearing checkout session: {str(e)}")
        # Don't fail the whole request if cleanup fails
        
def cart_count_api(request):
    """API endpoint to get cart count"""
    try:
        if request.user.is_authenticated and hasattr(request.user, 'customer'):
            cart = Cart.objects.get(customer=request.user.customer, is_active=True)
            count = cart.total_items
        else:
            count = 0
    except Cart.DoesNotExist:
        count = 0
    except Exception as e:
        logger.error(f"Error in cart_count_api: {str(e)}")
        count = 0
    
    return JsonResponse({'count': count})

@csrf_exempt  
def payment_failure(request):
    """Handle payment failure"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            razorpay_payment_id = data.get('razorpay_payment_id')
            error_description = data.get('error_description', 'Payment failed')
            
            if razorpay_payment_id:
                razorpay_service = get_razorpay_service()
                if razorpay_service:
                    razorpay_service.handle_payment_failure(razorpay_payment_id, error_description)
                
                return JsonResponse({
                    'success': True,
                    'message': 'Payment failure recorded'
                })
                
        except Exception as e:
            logger.error(f"Payment failure handler error: {str(e)}")
            return JsonResponse({
                'success': False,
                'error': 'Error recording payment failure'
            }, status=500)
    
    return JsonResponse({'error': 'Method not allowed'}, status=405)

@login_required
def payment_analytics(request):
    """Payment analytics dashboard"""
    try:
        # Get date range from request
        from datetime import datetime, timedelta
        end_date = timezone.now()
        start_date = end_date - timedelta(days=30)  # Default to last 30 days
        
        if request.GET.get('start_date'):
            start_date = datetime.strptime(request.GET.get('start_date'), '%Y-%m-%d')
        if request.GET.get('end_date'):
            end_date = datetime.strptime(request.GET.get('end_date'), '%Y-%m-%d')
        
        # Get analytics data
        razorpay_service = get_razorpay_service()
        if razorpay_service:
            analytics = razorpay_service.get_payment_analytics(start_date, end_date)
        else:
            analytics = {}
        
        # Get recent payments
        recent_payments = Payment.objects.filter(
            initiated_at__gte=start_date,
            initiated_at__lte=end_date
        ).select_related('order', 'order__customer').order_by('-initiated_at')[:20]
        
        context = {
            'analytics': analytics,
            'recent_payments': recent_payments,
            'start_date': start_date.strftime('%Y-%m-%d'),
            'end_date': end_date.strftime('%Y-%m-%d'),
        }
        
        return render(request, 'payment_analytics_dark.html', context)
        
    except Exception as e:
        messages.error(request, f'Error loading analytics: {str(e)}')
        return render(request, 'payment_analytics_dark.html', {})

@login_required
def initiate_refund(request, payment_id):
    """Initiate refund for a payment"""
    if request.method == 'POST':
        try:
            payment = get_object_or_404(Payment, payment_id=payment_id)
            
            # Check permissions (admin or order owner)
            if not (request.user.is_staff or payment.order.customer.user == request.user):
                messages.error(request, 'Permission denied')
                return redirect('order_detail', order_id=payment.order.id)
            
            refund_amount = request.POST.get('refund_amount')
            refund_reason = request.POST.get('refund_reason', 'Customer request')
            
            if refund_amount:
                refund_amount = Decimal(refund_amount)
                if refund_amount > payment.remaining_refund_amount:
                    messages.error(request, 'Refund amount exceeds available amount')
                    return redirect('order_detail', order_id=payment.order.id)
            
            razorpay_service = get_razorpay_service()
            if not razorpay_service:
                return JsonResponse({'success': False, 'error': 'Payment service unavailable'}, status=500)
            
            result = razorpay_service.initiate_refund(payment, refund_amount, refund_reason)
            
            if result['success']:
                messages.success(request, 'Refund initiated successfully!')
            else:
                messages.error(request, f'Refund failed: {result["error"]}')
                
        except Exception as e:
            messages.error(request, f'Error initiating refund: {str(e)}')
    
    return redirect('order_detail', order_id=payment.order.id)

@csrf_exempt
def chatbot_api(request):
    """Chatbot API endpoint for handling user messages and returning responses."""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            user_message = data.get('message', '').lower()
        except Exception:
            return JsonResponse({'response': "Invalid request."}, status=400)

        # Simple rule-based logic for demonstration
        if 'recommend' in user_message or 'suggest' in user_message:
            # Recommend top 3 featured products
            products = Product.objects.filter(is_featured=True, is_active=True)[:3]
            if products:
                product_names = ', '.join([p.name for p in products])
                response = f"Here are some recommendations: {product_names}."
            else:
                response = "Sorry, I couldn't find any featured products right now."
        elif 'buy' in user_message or 'order' in user_message:
            response = "You can browse our products and add them to your cart. Would you like help finding something specific?"
        elif 'hello' in user_message or 'hi' in user_message:
            response = "Hello! How can I assist you with your shopping today?"
        elif 'category' in user_message:
            categories = Category.objects.filter(is_active=True)[:5]
            if categories:
                category_names = ', '.join([c.name for c in categories])
                response = f"We have these categories: {category_names}."
            else:
                response = "Sorry, no categories are available right now."
        else:
            response = "I'm here to help you find products, make recommendations, or answer questions about your orders. Ask me anything!"

        return JsonResponse({'response': response})
    else:
        return JsonResponse({'response': "Only POST requests are allowed."}, status=405)

def test_working(request):
    return HttpResponse("Test working!", content_type="text/plain")

def test_razorpay(request):
    """Test Razorpay integration"""
    from django.http import JsonResponse
    import razorpay
    from django.conf import settings
    
    try:
        # Initialize Razorpay client
        client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))
        
        # Test payment creation
        payment = client.order.create({
            'amount': 100,  # amount in smallest currency unit (paise for INR)
            'currency': 'INR',
            'payment_capture': '1',
            'receipt': 'test_receipt_1'
        })
        
        return JsonResponse({
            'status': 'success',
            'message': 'Razorpay integration is working!',
            'payment': payment
        })
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        }, status=500)

# ============ NEW ESSENTIAL E-COMMERCE FEATURES ============

@login_required
def payment_success(request, order_id):
    """Payment success page with order confirmation"""
    try:
        order = get_object_or_404(Order, id=order_id, customer__user=request.user)
        
        # Create order status history
        OrderStatusHistory.objects.create(
            order=order,
            status='confirmed',
            notes='Payment successful and order confirmed',
            created_by=request.user
        )
        
        context = {
            'order': order,
        }
        return render(request, 'payment_success.html', context)
    except Exception as e:
        logger.error(f'Payment success page error: {str(e)}')
        messages.error(request, 'Error loading payment confirmation.')
        return redirect('order_list')

@login_required
def payment_success_fallback(request):
    """Fallback payment success page when no order_id is provided"""
    try:
        # Try to get the most recent order for this user
        order = Order.objects.filter(customer__user=request.user).order_by('-created_at').first()
        if order:
            return redirect('payment_success', order_id=order.id)
        else:
            messages.info(request, 'No recent orders found.')
            return redirect('order_list')
    except Exception as e:
        logger.error(f'Payment success fallback error: {str(e)}')
        messages.error(request, 'Error loading payment confirmation.')
        return redirect('home')

@login_required
def order_tracking_search(request):
    """Order tracking search page - allows users to enter order number"""
    if request.method == 'POST':
        order_number = request.POST.get('order_number', '').strip()
        if order_number:
            try:
                # Find order by order number for the current user
                order = Order.objects.get(order_number=order_number, customer__user=request.user)
                return redirect('order_tracking', order_id=order.id)
            except Order.DoesNotExist:
                messages.error(request, f'Order #{order_number} not found or does not belong to your account.')
        else:
            messages.error(request, 'Please enter a valid order number.')
    
    return render(request, 'order_tracking_search.html')

@login_required
def order_tracking(request, order_id):
    """Order tracking page with detailed status updates"""
    try:
        order = get_object_or_404(Order, id=order_id, customer__user=request.user)
        
        context = {
            'order': order,
        }
        return render(request, 'order_tracking.html', context)
    except Exception as e:
        logger.error(f'Order tracking error: {str(e)}')
        messages.error(request, 'Error loading order tracking.')
        return redirect('order_list')

@login_required
def download_invoice(request, order_id):
    """Generate and download invoice PDF"""
    try:
        order = get_object_or_404(Order, id=order_id, customer__user=request.user)
        
        context = {
            'order': order,
        }
        return render(request, 'invoice.html', context)
    except Exception as e:
        logger.error(f'Invoice generation error: {str(e)}')
        messages.error(request, 'Error generating invoice.')
        return redirect('order_detail', order_id=order_id)

@login_required
def cancel_order(request, order_id):
    """Cancel an order if it's still pending or confirmed"""
    try:
        order = get_object_or_404(Order, id=order_id, customer__user=request.user)
        
        if order.status in ['pending', 'confirmed']:
            order.status = 'cancelled'
            order.save()
            
            # Create status history
            OrderStatusHistory.objects.create(
                order=order,
                status='cancelled',
                notes='Order cancelled by customer',
                created_by=request.user
            )
            
            messages.success(request, f'Order #{order.order_number} has been cancelled successfully.')
        else:
            messages.error(request, 'This order cannot be cancelled as it is already being processed.')
            
        return redirect('order_detail', order_id=order_id)
    except Exception as e:
        logger.error(f'Order cancellation error: {str(e)}')
        messages.error(request, 'Error cancelling order.')
        return redirect('order_list')

@login_required
def return_request(request, order_id):
    """Create a return request for delivered orders"""
    try:
        order = get_object_or_404(Order, id=order_id, customer__user=request.user)
        
        if order.status != 'delivered':
            messages.error(request, 'Returns can only be requested for delivered orders.')
            return redirect('order_detail', order_id=order_id)
        
        if request.method == 'POST':
            return_items_ids = request.POST.getlist('return_items')
            reason = request.POST.get('return_reason')
            description = request.POST.get('return_description')
            preferred_resolution = request.POST.get('preferred_resolution')
            
            if not return_items_ids:
                messages.error(request, 'Please select at least one item to return.')
                return render(request, 'return_request.html', {'order': order})
            
            # Create return request
            return_request_obj = ReturnRequest.objects.create(
                order=order,
                customer=order.customer,
                reason=reason,
                description=description,
                preferred_resolution=preferred_resolution
            )
            
            # Add selected items to return request
            return_items = OrderItem.objects.filter(id__in=return_items_ids, order=order)
            return_request_obj.return_items.set(return_items)
            
            # Handle uploaded images
            if 'return_images' in request.FILES:
                for image in request.FILES.getlist('return_images'):
                    ReturnRequestImage.objects.create(
                        return_request=return_request_obj,
                        image=image
                    )
            
            messages.success(request, f'Return request #{return_request_obj.id} has been submitted successfully. We will review it within 24 hours.')
            return redirect('order_detail', order_id=order_id)
        
        context = {
            'order': order,
        }
        return render(request, 'return_request.html', context)
    except Exception as e:
        logger.error(f'Return request error: {str(e)}')
        messages.error(request, 'Error processing return request.')
        return redirect('order_detail', order_id=order_id)

def newsletter_signup(request):
    """Newsletter subscription page"""
    if request.method == 'POST':
        email = request.POST.get('email')
        first_name = request.POST.get('first_name', '')
        preferences = request.POST.getlist('preferences')
        
        try:
            subscription, created = NewsletterSubscription.objects.get_or_create(
                email=email,
                defaults={
                    'first_name': first_name,
                    'preferences': preferences,
                    'is_active': True
                }
            )
            
            if created:
                messages.success(request, 'Thank you for subscribing to our newsletter!')
            else:
                if not subscription.is_active:
                    subscription.is_active = True
                    subscription.preferences = preferences
                    subscription.save()
                    messages.success(request, 'Welcome back! Your subscription has been reactivated.')
                else:
                    messages.info(request, 'You are already subscribed to our newsletter.')
            
            return JsonResponse({'success': True, 'message': 'Subscription successful!'})
        except Exception as e:
            logger.error(f'Newsletter subscription error: {str(e)}')
            return JsonResponse({'success': False, 'message': 'Error processing subscription.'})
    
    return render(request, 'newsletter.html')

def faq(request):
    """FAQ page"""
    return render(request, 'faq.html')

def terms(request):
    """Terms & Conditions page"""
    return render(request, 'terms.html')

def privacy(request):
    """Privacy Policy page"""
    return render(request, 'privacy.html')

def test_razorpay(request):
    """Test Razorpay integration and return configuration status"""
    try:
        # Test Razorpay client initialization
        client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))
        
        # Test API connection
        test_payment = client.payment.all({
            'count': 1,
            'skip': 0
        })
        
        return JsonResponse({
            'status': 'success',
            'razorpay_configured': True,
            'test_payment_count': test_payment.get('count', 0),
            'keys': {
                'key_id': settings.RAZORPAY_KEY_ID,
                'key_secret': f"{settings.RAZORPAY_KEY_SECRET[:4]}...{settings.RAZORPAY_KEY_SECRET[-4:]}" if settings.RAZORPAY_KEY_SECRET else 'Not set'
            },
            'test_payment': test_payment.get('items', [])[:1] if test_payment.get('items') else 'No test payments found'
        })
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'razorpay_configured': False,
            'error': str(e),
            'keys': {
                'key_id': settings.RAZORPAY_KEY_ID,
                'key_secret': 'Not shown for security'
            }
        }, status=500)

def contact_enhanced(request):
    """Enhanced contact page with form submission"""
    if request.method == 'POST':
        name = request.POST.get('name')
        email = request.POST.get('email')
        phone = request.POST.get('phone', '')
        subject = request.POST.get('subject', 'general')
        message = request.POST.get('message')
        order_number = request.POST.get('order_number', '')
        
        try:
            contact_message = ContactMessage.objects.create(
                name=name,
                email=email,
                phone=phone,
                subject=subject,
                message=message,
                order_number=order_number
            )
            
            messages.success(request, 'Thank you for contacting us! We will respond within 24 hours.')
            return redirect('contact')
        except Exception as e:
            logger.error(f'Contact form error: {str(e)}')
            messages.error(request, 'Error sending message. Please try again.')
    
    return render(request, 'contact.html')

@login_required
def order_history(request):
    """Enhanced order history with filtering and search"""
    try:
        orders = Order.objects.filter(customer__user=request.user).order_by('-created_at')
        
        # Filter by status
        status_filter = request.GET.get('status')
        if status_filter:
            orders = orders.filter(status=status_filter)
        
        # Search by order number
        search = request.GET.get('search')
        if search:
            orders = orders.filter(order_number__icontains=search)
        
        # Pagination
        paginator = Paginator(orders, 10)
        page_number = request.GET.get('page')
        page_obj = paginator.get_page(page_number)
        
        context = {
            'page_obj': page_obj,
            'status_filter': status_filter,
            'search': search,
            'status_choices': Order.STATUS_CHOICES,
        }
        return render(request, 'order_list.html', context)
    except Exception as e:
        logger.error(f'Order history error: {str(e)}')
        messages.error(request, 'Error loading order history.')
        return render(request, 'order_list.html', {'page_obj': None})

@login_required
def wishlist_enhanced(request):
    """Enhanced wishlist with better functionality"""
    try:
        wishlist_items = Wishlist.objects.filter(customer__user=request.user).select_related('product')
        
        context = {
            'wishlist_items': wishlist_items,
        }
        return render(request, 'wishlist_dark.html', context)
    except Exception as e:
        logger.error(f'Wishlist error: {str(e)}')
        messages.error(request, 'Error loading wishlist.')
        return render(request, 'wishlist_dark.html', {'wishlist_items': []})

@login_required
def add_all_to_cart(request):
    """Add all wishlist items to cart"""
    try:
        wishlist_items = Wishlist.objects.filter(customer__user=request.user).select_related('product')
        cart, created = Cart.objects.get_or_create(
            customer=request.user.customer,
            is_active=True
        )
        
        added_count = 0
        failed_items = []
        
        for wishlist_item in wishlist_items:
            product = wishlist_item.product
            if product.is_active and product.stock_quantity > 0:
                cart_item, created = CartItem.objects.get_or_create(
                    cart=cart,
                    product=product,
                    defaults={'quantity': 1}
                )
                
                if not created:
                    cart_item.quantity += 1
                    cart_item.save()
                
                added_count += 1
            else:
                failed_items.append(product.name)
        
        if added_count > 0:
            messages.success(request, f'Successfully added {added_count} item(s) to your cart!')
        
        if failed_items:
            messages.warning(request, f'Could not add {len(failed_items)} item(s) due to stock issues.')
        
        return redirect('cart')
        
    except Exception as e:
        logger.error(f'Error adding all to cart: {str(e)}')
        messages.error(request, 'Error adding items to cart. Please try again.')
        return redirect('wishlist')

@login_required
def clear_wishlist(request):
    """Clear all items from wishlist"""
    try:
        wishlist_items = Wishlist.objects.filter(customer__user=request.user)
        count = wishlist_items.count()
        wishlist_items.delete()
        
        messages.success(request, f'Successfully removed {count} item(s) from your wishlist!')
        return redirect('wishlist')
        
    except Exception as e:
        logger.error(f'Error clearing wishlist: {str(e)}')
        messages.error(request, 'Error clearing wishlist. Please try again.')
        return redirect('wishlist')

def product_reviews(request, product_id):
    """Product reviews and ratings"""
    try:
        product = get_object_or_404(Product, id=product_id, is_active=True)
        reviews = Review.objects.filter(product=product, is_approved=True).order_by('-created_at')
        
        # Calculate average rating
        avg_rating = reviews.aggregate(Avg('rating'))['rating__avg'] or 0
        
        if request.method == 'POST' and request.user.is_authenticated:
            # Check if user has purchased this product
            has_purchased = Order.objects.filter(
                customer__user=request.user,
                items__product=product,
                status='delivered'
            ).exists()
            
            if has_purchased:
                rating = request.POST.get('rating')
                title = request.POST.get('title')
                comment = request.POST.get('comment')
                
                # Check if user already reviewed this product
                existing_review = Review.objects.filter(
                    product=product,
                    customer__user=request.user
                ).first()
                
                if existing_review:
                    messages.info(request, 'You have already reviewed this product.')
                else:
                    customer = Customer.objects.get(user=request.user)
                    Review.objects.create(
                        product=product,
                        customer=customer,
                        rating=rating,
                        title=title,
                        comment=comment
                    )
                    messages.success(request, 'Thank you for your review! It will be published after approval.')
            else:
                messages.error(request, 'You can only review products you have purchased.')
            
            return redirect('product_detail', slug=product.slug)
        
        context = {
            'product': product,
            'reviews': reviews,
            'avg_rating': round(avg_rating, 1),
            'total_reviews': reviews.count(),
        }
        return render(request, 'product_reviews.html', context)
    except Exception as e:
        logger.error(f'Product reviews error: {str(e)}')
        messages.error(request, 'Error loading product reviews.')
        return redirect('product_list')

# Admin Dashboard Views (Basic)
@login_required
def admin_dashboard(request):
    """Basic admin dashboard - only for staff users"""
    if not request.user.is_staff:
        messages.error(request, 'Access denied.')
        return redirect('home')
    
    try:
        # Basic statistics
        total_orders = Order.objects.count()
        pending_orders = Order.objects.filter(status='pending').count()
        total_customers = Customer.objects.count()
        total_products = Product.objects.filter(is_active=True).count()
        
        # Recent orders
        recent_orders = Order.objects.order_by('-created_at')[:10]
        
        # Return requests
        pending_returns = ReturnRequest.objects.filter(status='pending').count()
        
        context = {
            'total_orders': total_orders,
            'pending_orders': pending_orders,
            'total_customers': total_customers,
            'total_products': total_products,
            'recent_orders': recent_orders,
            'pending_returns': pending_returns,
        }
        return render(request, 'admin_dashboard.html', context)
    except Exception as e:
        logger.error(f'Admin dashboard error: {str(e)}')
        messages.error(request, 'Error loading dashboard.')
        return render(request, 'admin_dashboard.html', {})

def features_dashboard(request):
    """Features dashboard - central hub for all functionality"""
    return render(request, 'features_dashboard.html')