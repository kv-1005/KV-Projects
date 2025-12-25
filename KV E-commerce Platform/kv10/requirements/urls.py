from django.urls import path
from . import views
from django.views.decorators.csrf import csrf_exempt
from . import views_test

urlpatterns = [
    # Main pages
    path('', views.home, name='home'),
    path('about/', views.about, name='about'),
    path('contact/', views.contact, name='contact'),
    
    # Authentication
    path('register/', views.register, name='register'),
    path('login/', views.user_login, name='login'),
    path('logout/', views.user_logout, name='logout'),
    path('profile/', views.profile, name='profile'),
    # Address management
    path('addresses/add/', views.address_create, name='address_create'),
    path('addresses/<int:address_id>/edit/', views.address_edit, name='address_edit'),
    path('addresses/<int:address_id>/delete/', views.address_delete, name='address_delete'),
    path('addresses/<int:address_id>/set-default/<str:which>/', views.address_set_default, name='address_set_default'),
    
    # Products
    path('products/', views.product_list, name='products'),
    path('product/<slug:slug>/', views.product_detail, name='product_detail'),
    path('category/<slug:slug>/', views.category_detail, name='category_detail'),
    path('search/', views.search, name='search'),
    
    # Shopping cart
    path('cart/', views.cart, name='cart'),
    
    # Test endpoints
    path('test/razorpay/', views.test_razorpay, name='test_razorpay'),
    path('add-to-cart/<int:product_id>/', views.add_to_cart, name='add_to_cart'),
    path('remove-from-cart/<int:item_id>/', views.remove_from_cart, name='remove_from_cart'),
    
    # Checkout and orders
    path('checkout/', views.checkout, name='checkout'),
    path('orders/', views.order_list, name='order_list'),
    path('order/<int:order_id>/', views.order_detail, name='order_detail'),
    
    # Wishlist
    path('wishlist/', views.wishlist, name='wishlist'),
    path('add-to-wishlist/<int:product_id>/', views.add_to_wishlist, name='add_to_wishlist'),
    path('remove-from-wishlist/<int:item_id>/', views.remove_from_wishlist, name='remove_from_wishlist'),
    path('add-all-to-cart/', views.add_all_to_cart, name='add_all_to_cart'),
    path('clear-wishlist/', views.clear_wishlist, name='clear_wishlist'),
    
    # Payment endpoints
    path('payment/', views.payment, name='payment'),
    path('payment/callback/', views.payment_callback, name='payment_callback'),
    path('payment/failure/', views.payment_failure, name='payment_failure'),
    path('payment/analytics/', views.payment_analytics, name='payment_analytics'),
    path('analytics/', views.payment_analytics, name='analytics'),  # Shortcut URL
    path('payment/refund/<str:payment_id>/', views.initiate_refund, name='initiate_refund'),
    
    # Test endpoints
    path('test/razorpay/', views_test.test_razorpay_connection, name='test_razorpay'),
    
    # API endpoints
    path('api/cart-count/', views.cart_count_api, name='cart_count_api'),
    path('api/chatbot/', views.chatbot_api, name='chatbot_api'),
    
    # ============ NEW ESSENTIAL E-COMMERCE FEATURES ============
    
    # Post-payment and order management
    path('payment/success/<int:order_id>/', views.payment_success, name='payment_success'),
    path('payment/success/', views.payment_success_fallback, name='payment_success_fallback'),
    path('order_tracking/', views.order_tracking_search, name='order_tracking_search'),
    path('order/<int:order_id>/track/', views.order_tracking, name='order_tracking'),
    path('order/<int:order_id>/invoice/', views.download_invoice, name='download_invoice'),
    path('order/<int:order_id>/cancel/', views.cancel_order, name='cancel_order'),
    path('order/<int:order_id>/return/', views.return_request, name='return_request'),
    
    # Enhanced features
    path('newsletter/', views.newsletter_signup, name='newsletter'),
    path('faq/', views.faq, name='faq'),
    path('terms/', views.terms, name='terms'),
    path('privacy/', views.privacy, name='privacy'),
    path('contact-enhanced/', views.contact_enhanced, name='contact_enhanced'),
    
    # Enhanced existing features
    path('orders/history/', views.order_history, name='order_history'),
    path('wishlist/enhanced/', views.wishlist_enhanced, name='wishlist_enhanced'),
    path('product/<int:product_id>/reviews/', views.product_reviews, name='product_reviews'),
    
    # Admin features
    path('admin/dashboard/', views.admin_dashboard, name='admin_dashboard'),
    
    # Features dashboard
    path('features/', views.features_dashboard, name='features_dashboard'),
    
    # Legacy URLs for backward compatibility
    path('signup/', views.signup_func, name='signup'),
    path('home', views.home, name='home_old'),
    path('products', views.product_list, name='products_old'),
    # Test endpoints
    path('test/', views.test, name='test'),
    path('producttest/', views.producttest, name='producttest'),
    path('test-images/', views.test_images, name='test_images'),
    path('test/urls/', csrf_exempt(views.test_urls), name='test_urls'),
    path('test/razorpay/', csrf_exempt(views.test_razorpay), name='test_razorpay'),
    path('test-working/', views.test_working, name='test_working'),
]
