from django.contrib import admin
from django.utils.html import format_html
from .models import *

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug', 'is_active', 'created_at', 'image_preview']
    list_filter = ['is_active', 'created_at']
    search_fields = ['name', 'description']
    prepopulated_fields = {'slug': ('name',)}
    readonly_fields = ['image_preview']
    
    def image_preview(self, obj):
        if obj.image:
            return format_html('<img src="{}" style="max-height: 50px; max-width: 50px;" />', obj.image.url)
        return "No Image"
    image_preview.short_description = 'Image Preview'

class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 1

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ['name', 'category', 'price', 'sale_price', 'stock_quantity', 'is_active', 'is_featured', 'image_preview']
    list_filter = ['category', 'is_active', 'is_featured', 'created_at']
    search_fields = ['name', 'description', 'sku']
    prepopulated_fields = {'slug': ('name',)}
    inlines = [ProductImageInline]
    readonly_fields = ['created_at', 'updated_at', 'image_preview']
    
    def image_preview(self, obj):
        if obj.image:
            return format_html('<img src="{}" style="max-height: 50px; max-width: 50px;" />', obj.image.url)
        return "No Image"
    image_preview.short_description = 'Image Preview'

@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = ['user', 'phone', 'city', 'country', 'created_at']
    list_filter = ['country', 'created_at']
    search_fields = ['user__username', 'user__email', 'phone']

@admin.register(Cart)
class CartAdmin(admin.ModelAdmin):
    list_display = ['id', 'customer', 'total_items', 'total_price', 'is_active', 'created_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['customer__user__username', 'customer__user__email']

@admin.register(CartItem)
class CartItemAdmin(admin.ModelAdmin):
    list_display = ['cart', 'product', 'quantity', 'total_price', 'added_at']
    list_filter = ['added_at']

class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ['total_price']

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ['order_number', 'customer', 'status', 'payment_status', 'payment_method', 'total_amount', 'created_at']
    list_filter = ['status', 'payment_status', 'payment_method', 'created_at']
    search_fields = ['order_number', 'customer__user__username', 'customer__user__email', 'razorpay_payment_id']
    inlines = [OrderItemInline]
    readonly_fields = ['order_number', 'razorpay_order_id', 'razorpay_payment_id', 'razorpay_signature', 'created_at', 'updated_at']

@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = ['order', 'product', 'quantity', 'price', 'total_price']
    list_filter = ['order__status']

@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ['product', 'customer', 'rating', 'title', 'is_approved', 'created_at']
    list_filter = ['rating', 'is_approved', 'created_at']
    search_fields = ['product__name', 'customer__user__username', 'title']

@admin.register(Wishlist)
class WishlistAdmin(admin.ModelAdmin):
    list_display = ['customer', 'product', 'added_at']
    list_filter = ['added_at']
    search_fields = ['customer__user__username', 'product__name']

@admin.register(Coupon)
class CouponAdmin(admin.ModelAdmin):
    list_display = ['code', 'discount_type', 'discount_value', 'is_active', 'valid_until', 'used_count']
    list_filter = ['discount_type', 'is_active', 'valid_until']
    search_fields = ['code', 'description']

@admin.register(Address)
class AddressAdmin(admin.ModelAdmin):
    list_display = ['customer', 'label', 'city', 'state', 'is_default_shipping', 'is_default_billing', 'created_at']
    list_filter = ['is_default_shipping', 'is_default_billing', 'country', 'state', 'created_at']
    search_fields = ['customer__user__username', 'first_name', 'last_name', 'city', 'address']

@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ['payment_id', 'order', 'amount', 'status', 'payment_method', 'gateway', 'initiated_at', 'completed_at']
    list_filter = ['status', 'payment_method', 'gateway', 'initiated_at']
    search_fields = ['payment_id', 'gateway_payment_id', 'order__order_number', 'order__customer__user__username']
    readonly_fields = ['payment_id', 'gateway_payment_id', 'gateway_order_id', 'gateway_signature', 'gateway_response', 
                      'net_amount', 'initiated_at', 'completed_at', 'updated_at']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('order', 'payment_id', 'amount', 'currency', 'status', 'payment_method', 'gateway')
        }),
        ('Gateway Details', {
            'fields': ('gateway_payment_id', 'gateway_order_id', 'gateway_signature', 'gateway_response'),
            'classes': ('collapse',)
        }),
        ('Financial Details', {
            'fields': ('processing_fee', 'net_amount', 'failure_reason', 'retry_count')
        }),
        ('Refund Information', {
            'fields': ('refund_amount', 'refund_reason', 'refund_initiated_at', 'refund_completed_at', 'refund_reference'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('initiated_at', 'completed_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
    
    def has_delete_permission(self, request, obj=None):
        # Prevent deletion of payment records for audit purposes
        return False

# Old models removed for security and to use Django's built-in auth system
