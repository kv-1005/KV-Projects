from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, send_file, abort, make_response
from flask_wtf.csrf import generate_csrf
import json

# Optional rate limiting import
try:
    from flask_limiter import Limiter
    from flask_limiter.util import get_remote_address
    RATE_LIMITING_AVAILABLE = True
except ImportError:
    RATE_LIMITING_AVAILABLE = False
    print("Warning: Flask-Limiter not available. Rate limiting disabled.")
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed
from wtforms import StringField, TextAreaField, DecimalField, IntegerField, SelectField, PasswordField, SubmitField, BooleanField
from wtforms.validators import DataRequired, Email, Length, NumberRange, Regexp, Optional, ValidationError
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
import re
from datetime import datetime, date, timedelta
import os
import io
from types import SimpleNamespace


 
import base64
import qrcode
from reportlab.lib.pagesizes import letter, A4, landscape
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image, PageBreak, KeepTogether
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
import io
from io import BytesIO
import base64
from PIL import Image as PILImage
from decimal import Decimal

# Load environment variables from .env file
from dotenv import load_dotenv
load_dotenv()

app = Flask(__name__)

# Load configuration
config_name = os.environ.get('FLASK_ENV', 'development')
if config_name == 'production':
    from config import ProductionConfig
    app.config.from_object(ProductionConfig)
elif config_name == 'testing':
    from config import TestingConfig
    app.config.from_object(TestingConfig)
else:
    from config import DevelopmentConfig
    app.config.from_object(DevelopmentConfig)

# Initialize extensions
db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.login_message = 'Please log in to access this page.'

# Add custom Jinja2 filters
@app.template_filter('float')
def float_filter(value):
    """Convert value to float for Jinja2 templates"""
    try:
        return float(value)
    except (ValueError, TypeError):
        return 0.0

# Initialize rate limiter (if available)
if RATE_LIMITING_AVAILABLE:
    limiter = Limiter(
        key_func=get_remote_address,
        default_limits=["200 per day", "50 per hour"]
    )
    limiter.init_app(app)
else:
    # Create a dummy limiter decorator that does nothing
    class DummyLimiter:
        def limit(self, *args, **kwargs):
            def decorator(f):
                return f
            return decorator
    limiter = DummyLimiter()

# Create upload directory if it doesn't exist
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Security headers middleware
@app.after_request
def add_security_headers(response):
    """Add security headers to all responses"""
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'DENY'
    response.headers['X-XSS-Protection'] = '1; mode=block'
    response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
    response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
    response.headers['Content-Security-Policy'] = "default-src 'self'; script-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net https://cdnjs.cloudflare.com; style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net https://cdnjs.cloudflare.com; img-src 'self' data:; font-src 'self' https://cdnjs.cloudflare.com;"
    return response

# Database Models
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(120), nullable=False)
    role = db.Column(db.String(20), default='staff')  # admin, accountant, staff
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    signature_data = db.Column(db.Text)  # Base64 encoded signature image (legacy support)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class UserSignature(db.Model):
    """Store multiple signatures per user"""
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    signature_name = db.Column(db.String(100), nullable=False)  # e.g., "CEO Signature", "Manager Signature"
    signature_data = db.Column(db.Text, nullable=False)  # Base64 encoded signature image
    is_default = db.Column(db.Boolean, default=False)  # Default signature for new invoices
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    created_by = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    
    # Relationships
    user = db.relationship('User', foreign_keys=[user_id], backref='signatures')
    creator = db.relationship('User', foreign_keys=[created_by], backref='created_signatures')

class Company(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    gstin = db.Column(db.String(15), unique=True, nullable=False)
    pan = db.Column(db.String(10), nullable=False)
    address = db.Column(db.Text, nullable=False)
    city = db.Column(db.String(100), nullable=False)
    state = db.Column(db.String(100), nullable=False)
    pincode = db.Column(db.String(10), nullable=False)
    phone = db.Column(db.String(15), nullable=False)
    email = db.Column(db.String(120), nullable=False)
    logo_path = db.Column(db.String(200))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class Customer(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    gstin = db.Column(db.String(15))
    address = db.Column(db.Text, nullable=False)
    city = db.Column(db.String(100), nullable=False)
    state = db.Column(db.String(100), nullable=False)
    pincode = db.Column(db.String(10), nullable=False)
    phone = db.Column(db.String(15), nullable=False)
    email = db.Column(db.String(120))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class Vendor(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    gstin = db.Column(db.String(15))
    address = db.Column(db.Text, nullable=False)
    city = db.Column(db.String(100), nullable=False)
    state = db.Column(db.String(100), nullable=False)
    pincode = db.Column(db.String(10), nullable=False)
    phone = db.Column(db.String(15), nullable=False)
    email = db.Column(db.String(120))
    contact_person = db.Column(db.String(100))
    payment_terms = db.Column(db.String(200))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class Invoice(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    invoice_number = db.Column(db.String(50), unique=True, nullable=False)
    customer_id = db.Column(db.Integer, db.ForeignKey('customer.id'), nullable=False)
    company_id = db.Column(db.Integer, db.ForeignKey('company.id'), nullable=False)
    invoice_date = db.Column(db.Date, nullable=False)
    due_date = db.Column(db.Date)
    subtotal = db.Column(db.Numeric(10, 2), nullable=False)
    cgst_amount = db.Column(db.Numeric(10, 2), default=0)
    sgst_amount = db.Column(db.Numeric(10, 2), default=0)
    igst_amount = db.Column(db.Numeric(10, 2), default=0)
    shipping_charges = db.Column(db.Numeric(10, 2), default=0)
    total_amount = db.Column(db.Numeric(10, 2), nullable=False)
    status = db.Column(db.String(20), default='unpaid')  # paid, unpaid, partially_paid
    notes = db.Column(db.Text)
    # E-Way Bill fields
    eway_bill = db.Column(db.String(50))  # E-way Bill number (legacy/primary)
    eway_mode = db.Column(db.String(10))  # road or rail
    vehicle_number = db.Column(db.String(20))  # for road
    rr_number = db.Column(db.String(30))  # Railway Receipt number for rail
    transporter_id = db.Column(db.String(30))
    from_place = db.Column(db.String(100))
    from_state_code = db.Column(db.String(2))
    to_place = db.Column(db.String(100))
    to_state_code = db.Column(db.String(2))
    eway_valid_upto = db.Column(db.Date)
    eway_qr = db.Column(db.Text)  # Base64 data URI for QR code image
    selected_signature_id = db.Column(db.Integer, db.ForeignKey('user_signature.id'), nullable=True)  # Selected signature for this invoice
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    customer = db.relationship('Customer', backref='invoices')
    company = db.relationship('Company', backref='invoices')
    items = db.relationship('InvoiceItem', backref='invoice', cascade='all, delete-orphan')
    selected_signature = db.relationship('UserSignature', backref='used_invoices')

class InvoiceItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    invoice_id = db.Column(db.Integer, db.ForeignKey('invoice.id'), nullable=False)
    description = db.Column(db.String(200), nullable=False)
    hsn_code = db.Column(db.String(20), default='85044090')  # Default HSN code
    quantity = db.Column(db.Numeric(10, 2), nullable=False)
    unit_price = db.Column(db.Numeric(10, 2), nullable=False)
    discount_type = db.Column(db.String(10), default='amount')  # 'amount' or 'percentage'
    discount_value = db.Column(db.Numeric(10, 2), default=0)  # Discount amount or percentage
    tax_rate = db.Column(db.Numeric(5, 2), default=18)  # Default 18% GST
    amount = db.Column(db.Numeric(10, 2), nullable=False)

class PurchaseOrder(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    po_number = db.Column(db.String(50), unique=True, nullable=False)
    vendor_id = db.Column(db.Integer, db.ForeignKey('vendor.id'), nullable=False)
    company_id = db.Column(db.Integer, db.ForeignKey('company.id'), nullable=False)
    po_date = db.Column(db.Date, nullable=False)
    delivery_date = db.Column(db.Date)
    expected_delivery_date = db.Column(db.Date)
    actual_delivery_date = db.Column(db.Date)
    reference_no = db.Column(db.String(50))
    eway_bill = db.Column(db.String(50))  # E-way Bill number
    place_of_supply = db.Column(db.String(100))
    po_type = db.Column(db.String(20), default='standard')  # standard, urgent, bulk, recurring
    priority = db.Column(db.String(10), default='medium')  # low, medium, high, urgent
    subtotal = db.Column(db.Numeric(10, 2), nullable=False)
    cgst_amount = db.Column(db.Numeric(10, 2), default=0)
    sgst_amount = db.Column(db.Numeric(10, 2), default=0)
    igst_amount = db.Column(db.Numeric(10, 2), default=0)
    shipping_charges = db.Column(db.Numeric(10, 2), default=0)
    total_amount = db.Column(db.Numeric(10, 2), nullable=False)
    status = db.Column(db.String(20), default='draft')  # draft, pending, approved, sent, partially_received, received, completed, cancelled
    notes = db.Column(db.Text)
    terms_conditions = db.Column(db.Text)
    payment_terms = db.Column(db.Text)
    extra_billing_info = db.Column(db.Text)  # Additional billing address info
    main_address = db.Column(db.String(20), default='salem')  # salem, chennai
    branch_address = db.Column(db.String(20), default='chennai')  # salem, chennai
    selected_signature_id = db.Column(db.Integer, db.ForeignKey('user_signature.id'), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    vendor = db.relationship('Vendor', backref='purchase_orders')
    company = db.relationship('Company', backref='purchase_orders')
    selected_signature = db.relationship('UserSignature', backref='used_purchase_orders')
    items = db.relationship('PurchaseOrderItem', backref='purchase_order', cascade='all, delete-orphan')

class PurchaseOrderItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    po_id = db.Column(db.Integer, db.ForeignKey('purchase_order.id'), nullable=False)
    description = db.Column(db.String(200), nullable=False)
    hsn_code = db.Column(db.String(20), default='85044090')  # Default HSN code
    quantity = db.Column(db.Numeric(10, 2), nullable=False)
    unit_price = db.Column(db.Numeric(10, 2), nullable=False)
    discount_type = db.Column(db.String(10), default='amount')  # 'amount' or 'percentage'
    discount_value = db.Column(db.Numeric(10, 2), default=0)  # Discount amount or percentage
    tax_rate = db.Column(db.Numeric(5, 2), default=18)  # Default 18% GST
    amount = db.Column(db.Numeric(10, 2), nullable=False)

class DeliveryChallan(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    challan_number = db.Column(db.String(50), unique=True, nullable=False)
    consignee_name = db.Column(db.String(200), nullable=False)
    consignee_details = db.Column(db.Text)  # Consignee contact details
    consignee_address = db.Column(db.Text, nullable=False)
    company_id = db.Column(db.Integer, db.ForeignKey('company.id'), nullable=False)
    challan_date = db.Column(db.Date, nullable=False)
    delivery_date = db.Column(db.Date)
    expected_delivery_date = db.Column(db.Date)
    actual_delivery_date = db.Column(db.Date)
    reference_no = db.Column(db.String(50))
    place_of_supply = db.Column(db.String(100))
    subtotal = db.Column(db.Numeric(10, 2), nullable=False)
    cgst_amount = db.Column(db.Numeric(10, 2), default=0)
    sgst_amount = db.Column(db.Numeric(10, 2), default=0)
    igst_amount = db.Column(db.Numeric(10, 2), default=0)
    shipping_charges = db.Column(db.Numeric(10, 2), default=0)
    total_amount = db.Column(db.Numeric(10, 2), nullable=False)
    status = db.Column(db.String(20), default='draft')  # draft, pending, sent, delivered, cancelled
    notes = db.Column(db.Text)
    extra_billing_info = db.Column(db.Text)  # Additional address info
    main_address = db.Column(db.String(20), default='salem')  # salem, chennai
    branch_address = db.Column(db.String(20), default='chennai')  # salem, chennai
    selected_signature_id = db.Column(db.Integer, db.ForeignKey('user_signature.id'), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    company = db.relationship('Company', backref='delivery_challans')
    selected_signature = db.relationship('UserSignature', backref='used_delivery_challans')
    items = db.relationship('DeliveryChallanItem', backref='delivery_challan', cascade='all, delete-orphan')

class DeliveryChallanItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    challan_id = db.Column(db.Integer, db.ForeignKey('delivery_challan.id'), nullable=False)
    description = db.Column(db.String(200), nullable=False)
    hsn_code = db.Column(db.String(20), default='85044090')  # Default HSN code
    quantity = db.Column(db.Numeric(10, 2), nullable=False)
    unit_price = db.Column(db.Numeric(10, 2), nullable=False)
    discount_type = db.Column(db.String(10), default='amount')  # 'amount' or 'percentage'
    discount_value = db.Column(db.Numeric(10, 2), default=0)  # Discount amount or percentage
    tax_rate = db.Column(db.Numeric(5, 2), default=18)  # Default 18% GST
    amount = db.Column(db.Numeric(10, 2), nullable=False)

class ActivityLog(db.Model):
    """Comprehensive activity logging system"""
    id = db.Column(db.Integer, primary_key=True)
    
    # Who
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    username = db.Column(db.String(80), nullable=False)  # Store for history even if user deleted
    
    # What - Action Details
    action_type = db.Column(db.String(50), nullable=False)  # create, update, delete, view, export, login, logout
    entity_type = db.Column(db.String(50), nullable=False)  # invoice, customer, vendor, company, purchase_order, signature, user
    entity_id = db.Column(db.Integer, nullable=True)  # ID of the affected entity
    
    # Where - Context
    resource_identifier = db.Column(db.String(200), nullable=True)  # invoice_number, customer_name, etc.
    old_value = db.Column(db.Text, nullable=True)  # Previous state (for updates)
    new_value = db.Column(db.Text, nullable=True)  # New state (for updates/changes)
    
    # When
    timestamp = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, index=True)
    ip_address = db.Column(db.String(45), nullable=True)  # IPv4 or IPv6
    
    # Additional Context
    description = db.Column(db.Text, nullable=True)  # Human-readable description
    meta_data = db.Column(db.Text, nullable=True)  # JSON string for additional data (note: 'metadata' is reserved by SQLAlchemy)
    
    # Relationships
    user = db.relationship('User', backref='activity_logs')
    
    def __repr__(self):
        return f'<ActivityLog {self.id}: {self.username} {self.action_type} {self.entity_type} at {self.timestamp}>'
    
    def to_dict(self):
        """Convert log entry to dictionary for JSON response"""
        return {
            'id': self.id,
            'username': self.username,
            'action_type': self.action_type,
            'entity_type': self.entity_type,
            'entity_id': self.entity_id,
            'resource_identifier': self.resource_identifier,
            'old_value': self.old_value,
            'new_value': self.new_value,
            'timestamp': self.timestamp.strftime('%Y-%m-%d %H:%M:%S'),
            'ip_address': self.ip_address,
            'description': self.description,
            'metadata': self.meta_data
        }

# Chatbot Models
class ChatConversation(db.Model):
    """Store chat conversations"""
    __tablename__ = 'chat_conversations'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False, index=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, index=True)
    # Summary for quick context retrieval
    summary = db.Column(db.Text, nullable=True)
    
    # Relationships
    user = db.relationship('User', backref='chat_conversations')
    messages = db.relationship('ChatMessage', backref='conversation', cascade='all, delete-orphan', lazy='dynamic')
    
    def __repr__(self):
        return f'<ChatConversation {self.id}: User {self.user_id}>'

class ChatMessage(db.Model):
    """Store individual chat messages"""
    __tablename__ = 'chat_messages'
    
    id = db.Column(db.Integer, primary_key=True)
    conversation_id = db.Column(db.Integer, db.ForeignKey('chat_conversations.id'), nullable=False, index=True)
    role = db.Column(db.String(10), nullable=False, index=True)  # 'user' or 'assistant'
    message = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    
    def __repr__(self):
        return f'<ChatMessage {self.id}: {self.role}>'

class ChatbotKnowledge(db.Model):
    """Knowledge base for rule-based responses"""
    __tablename__ = 'chatbot_knowledge'
    
    id = db.Column(db.Integer, primary_key=True)
    keyword = db.Column(db.String(100), nullable=False)
    pattern = db.Column(db.String(200))  # Regex pattern
    response = db.Column(db.Text, nullable=False)
    category = db.Column(db.String(50))  # invoice, customer, gst, etc.
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<ChatbotKnowledge {self.id}: {self.keyword}>'

@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))

# Context processor to make CSRF token available in all templates
@app.context_processor
def inject_csrf_token():
    return dict(csrf_token=generate_csrf)

# Input sanitization functions
def sanitize_input(text):
    """Sanitize user input to prevent XSS attacks"""
    if not text:
        return text
    # Remove potentially dangerous characters
    text = re.sub(r'[<>"\']', '', str(text))
    return text

# Custom validators
def validate_date_format(form, field):
    """Validate date format - accepts both YYYY-MM-DD (HTML5 date input) and DD/MM/YYYY"""
    if field.data:
        try:
            # Try HTML5 date format first (YYYY-MM-DD)
            datetime.strptime(field.data, '%Y-%m-%d')
        except ValueError:
            try:
                # Try DD/MM/YYYY format
                datetime.strptime(field.data, '%d/%m/%Y')
            except ValueError:
                raise ValidationError('Please enter a valid date.')

def validate_numeric_input(value, min_val=None, max_val=None):
    """Validate and sanitize numeric input"""
    try:
        num = float(value)
        if min_val is not None and num < min_val:
            return None
        if max_val is not None and num > max_val:
            return None
        return num
    except (ValueError, TypeError):
        return None

def validate_discount_value(discount_type, discount_value, gross_amount=None):
    """Validate discount value based on type with precision fixes"""
    from decimal import Decimal, ROUND_HALF_UP
    
    # Convert to Decimal first, then check
    discount_value = Decimal(str(discount_value))
    
    if not discount_value or discount_value <= 0:
        return Decimal('0')
    
    if discount_type == 'percentage':
        # Ensure percentage doesn't exceed 100%
        validated_discount = min(discount_value, Decimal('100'))
        # Round to 2 decimal places to prevent precision issues
        return validated_discount.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
    elif discount_type == 'amount':
        # Ensure discount doesn't exceed gross amount if provided
        if gross_amount:
            validated_discount = min(discount_value, Decimal(str(gross_amount)))
        else:
            validated_discount = discount_value
        # Round to 2 decimal places to prevent precision issues
        return validated_discount.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
    
    return Decimal('0')

# ============================================
# ACTIVITY LOGGING FUNCTIONS
# ============================================

def log_activity(action_type, entity_type, entity_id=None, resource_identifier=None, 
                 old_value=None, new_value=None, description=None, metadata=None):
    """
    Comprehensive activity logging function
    
    Args:
        action_type: create, update, delete, view, export, login, logout, etc.
        entity_type: invoice, customer, vendor, company, purchase_order, signature, user
        entity_id: ID of the affected entity
        resource_identifier: human-readable identifier (invoice_number, customer_name, etc.)
        old_value: previous state (for updates/deletes)
        new_value: new state (for updates/creates)
        description: human-readable description
        metadata: additional JSON data
    """
    try:
        # Only log if user is authenticated
        if not current_user.is_authenticated:
            return
        
        # Get IP address
        ip_address = request.remote_addr if request else None
        
        # Create log entry
        log_entry = ActivityLog(
            user_id=current_user.id,
            username=current_user.username,
            action_type=action_type,
            entity_type=entity_type,
            entity_id=entity_id,
            resource_identifier=resource_identifier,
            old_value=str(old_value) if old_value else None,
            new_value=str(new_value) if new_value else None,
            ip_address=ip_address,
            description=description,
            meta_data=metadata if isinstance(metadata, str) else (json.dumps(metadata) if metadata else None)
        )
        
        db.session.add(log_entry)
        # Commit immediately for audit trail integrity
        db.session.commit()
        
    except Exception as e:
        # Don't break main functionality if logging fails
        app.logger.error(f"Failed to log activity: {str(e)}")
        db.session.rollback()

def get_entity_summary(entity_type, entity_id, entity_obj=None):
    """Get a human-readable summary of an entity"""
    if entity_obj is None:
        return f"{entity_type} #{entity_id}"
    
    summary_map = {
        'invoice': lambda obj: f"Invoice #{obj.invoice_number} (₹{obj.total_amount})",
        'customer': lambda obj: f"{obj.name} ({obj.city})",
        'vendor': lambda obj: f"{obj.name} ({obj.city})",
        'company': lambda obj: f"{obj.name}",
        'purchase_order': lambda obj: f"PO #{obj.po_number} (₹{obj.total_amount})",
        'user': lambda obj: f"{obj.username}",
        'signature': lambda obj: f"Signature: {obj.signature_name}",
    }
    
    func = summary_map.get(entity_type)
    return func(entity_obj) if func else f"{entity_type} #{entity_id}"

# Forms
class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Login')

class CompanyForm(FlaskForm):
    name = StringField('Company Name', validators=[DataRequired(), Length(max=200)])
    gstin = StringField('GSTIN', validators=[
        DataRequired(), 
        Length(min=15, max=15),
        Regexp(r'^[0-9]{2}[A-Z]{5}[0-9]{4}[A-Z]{1}[1-9A-Z]{1}Z[0-9A-Z]{1}$', message='Invalid GSTIN format')
    ])
    pan = StringField('PAN', validators=[
        DataRequired(), 
        Length(min=10, max=10),
        Regexp(r'^[A-Z]{5}[0-9]{4}[A-Z]{1}$', message='Invalid PAN format')
    ])
    address = TextAreaField('Address', validators=[DataRequired(), Length(max=500)])
    city = StringField('City', validators=[DataRequired(), Length(max=100)])
    state = StringField('State', validators=[DataRequired(), Length(max=100)])
    pincode = StringField('Pincode', validators=[
        DataRequired(), 
        Length(min=6, max=6),
        Regexp(r'^[0-9]{6}$', message='Invalid pincode format')
    ])
    phone = StringField('Phone', validators=[
        DataRequired(), 
        Length(min=10, max=15),
        Regexp(r'^[\+]?[0-9\s\-\(\)]{10,15}$', message='Invalid phone number format')
    ])
    email = StringField('Email', validators=[DataRequired(), Email(), Length(max=120)])
    logo = FileField('Company Logo', validators=[
        FileAllowed(['jpg', 'jpeg', 'png', 'gif'], 'Only image files are allowed!')
    ])
    submit = SubmitField('Save Company Details')

class CustomerForm(FlaskForm):
    name = StringField('Customer Name', validators=[DataRequired(), Length(max=200)])
    gstin = StringField('GSTIN', validators=[
        Optional(),
        Length(min=15, max=15),
        Regexp(r'^[0-9]{2}[A-Z]{5}[0-9]{4}[A-Z]{1}[1-9A-Z]{1}Z[0-9A-Z]{1}$', message='Invalid GSTIN format')
    ])
    address = TextAreaField('Address', validators=[DataRequired(), Length(max=500)])
    city = StringField('City', validators=[DataRequired(), Length(max=100)])
    state = StringField('State', validators=[DataRequired(), Length(max=100)])
    pincode = StringField('Pincode', validators=[
        DataRequired(), 
        Length(min=6, max=6),
        Regexp(r'^[0-9]{6}$', message='Invalid pincode format')
    ])
    phone = StringField('Phone', validators=[
        DataRequired(), 
        Length(min=10, max=15),
        Regexp(r'^[\+]?[0-9\s\-\(\)]{10,15}$', message='Invalid phone number format')
    ])
    email = StringField('Email', validators=[
        Optional(),
        Email(), 
        Length(max=120)
    ])
    submit = SubmitField('Save Customer')

class VendorForm(FlaskForm):
    name = StringField('Vendor Name', validators=[DataRequired(), Length(max=200)])
    gstin = StringField('GSTIN', validators=[
        Optional(),
        Length(min=15, max=15),
        Regexp(r'^[0-9]{2}[A-Z]{5}[0-9]{4}[A-Z]{1}[1-9A-Z]{1}Z[0-9A-Z]{1}$', message='Invalid GSTIN format')
    ])
    address = TextAreaField('Address', validators=[DataRequired(), Length(max=500)])
    city = StringField('City', validators=[DataRequired(), Length(max=100)])
    state = StringField('State', validators=[DataRequired(), Length(max=100)])
    pincode = StringField('Pincode', validators=[
        DataRequired(), 
        Length(min=6, max=6),
        Regexp(r'^[0-9]{6}$', message='Invalid pincode format')
    ])
    phone = StringField('Phone', validators=[
        DataRequired(), 
        Length(min=10, max=15),
        Regexp(r'^[\+]?[0-9\s\-\(\)]{10,15}$', message='Invalid phone number format')
    ])
    email = StringField('Email', validators=[
        Optional(),
        Email(), 
        Length(max=120)
    ])
    contact_person = StringField('Contact Person', validators=[Optional(), Length(max=100)])
    payment_terms = StringField('Payment Terms', validators=[Optional(), Length(max=200)])
    submit = SubmitField('Save Vendor')

class InvoiceForm(FlaskForm):
    customer_id = SelectField('Customer', coerce=int, validators=[DataRequired()])
    invoice_number = StringField('Invoice No.', validators=[DataRequired(), Length(max=20)])
    reference_no = StringField('Reference No.', validators=[Length(max=50)])
    eway_bill = StringField('E-way Bill No.', validators=[Length(max=50)])
    eway_bill_date = StringField('E-way Bill Date', validators=[Optional()])
    eway_mode = SelectField('Transport Mode', choices=[('', 'Select'), ('road', 'Road'), ('rail', 'Rail')], validators=[Optional()])
    vehicle_number = StringField('Vehicle Number (Road)', validators=[Optional(), Length(max=20)])
    rr_number = StringField('RR Number (Rail)', validators=[Optional(), Length(max=30)])
    transporter_id = StringField('Transporter ID', validators=[Optional(), Length(max=30)])
    from_place = StringField('From Place', validators=[Optional(), Length(max=100)])
    from_state_code = StringField('From State Code', validators=[Optional(), Length(max=2)])
    to_place = StringField('To Place', validators=[Optional(), Length(max=100)])
    to_state_code = StringField('To State Code', validators=[Optional(), Length(max=2)])
    eway_valid_upto = StringField('E-way Valid Upto', validators=[Optional(), validate_date_format])
    invoice_date = StringField('Invoice Date', validators=[DataRequired(), validate_date_format])
    due_date = StringField('Due Date', validators=[validate_date_format])
    shipping_charges = DecimalField('Shipping Charges', places=2, default=0)
    extra_billing_info = TextAreaField('Extra Billing Address Info', 
                                     validators=[Optional(), Length(max=200)],
                                     render_kw={'placeholder': 'Additional billing address elements (e.g., Floor, Building, Landmark)'})
    terms_text = TextAreaField('Terms & Conditions')
    payment_text = TextAreaField('Payment/Warranty/Only For')
    notes = TextAreaField('Notes')
    # Address selection fields
    main_address = SelectField('Main Address (Header)', 
                              choices=[('salem', 'Salem Office'), ('chennai', 'Chennai Branch')], 
                              default='salem',
                              validators=[DataRequired()])
    branch_address = SelectField('Branch Address (Footer)', 
                                choices=[('salem', 'Salem Office'), ('chennai', 'Chennai Branch')], 
                                default='chennai',
                                validators=[DataRequired()])
    selected_signature = SelectField('Select Signature', coerce=str, validators=[Optional()])
    is_sac = BooleanField('SAC', default=False)  # Stored in metadata, not database column
    submit = SubmitField('Create Invoice')

class PurchaseOrderForm(FlaskForm):
    vendor_id = SelectField('Vendor', coerce=int, validators=[DataRequired()])
    po_number = StringField('PO No.', validators=[DataRequired(), Length(max=20)])
    reference_no = StringField('Reference No.', validators=[Length(max=50)])
    # e-way bill removed per requirement
    po_date = StringField('PO Date', validators=[DataRequired(), validate_date_format])
    delivery_date = StringField('Delivery Date', validators=[validate_date_format])
    expected_delivery_date = StringField('Expected Delivery Date', validators=[validate_date_format])
    place_of_supply = StringField('Place of Supply', validators=[Length(max=100)])
    # po_type and priority removed per requirement
    delivery = StringField('Delivery', validators=[Optional(), Length(max=100)])
    shipping_charges = DecimalField('Shipping Charges', places=2, default=0)
    extra_billing_info = TextAreaField('Extra Billing Address Info', 
                                     validators=[Optional(), Length(max=200)],
                                     render_kw={'placeholder': 'Additional billing address elements (e.g., Floor, Building, Landmark)'})
    terms_conditions = TextAreaField('Terms & Conditions')
    payment_terms = TextAreaField('Payment Terms')
    notes = TextAreaField('Notes')
    # Address selection fields
    main_address = SelectField('Main Address (Header)', 
                              choices=[('salem', 'Salem Office'), ('chennai', 'Chennai Branch')], 
                              default='salem',
                              validators=[DataRequired()])
    branch_address = SelectField('Branch Address (Footer)', 
                                choices=[('salem', 'Salem Office'), ('chennai', 'Chennai Branch')], 
                                default='chennai',
                                validators=[DataRequired()])
    selected_signature = SelectField('Select Signature', coerce=str, validators=[Optional()])
    submit = SubmitField('Create Purchase Order')

class DeliveryChallanForm(FlaskForm):
    consignee_name = StringField('Consignee Name', validators=[DataRequired(), Length(max=200)])
    consignee_details = TextAreaField('Consignee Details', 
                                     validators=[Optional(), Length(max=500)],
                                     render_kw={'placeholder': 'Contact person, phone, email, etc.'})
    consignee_address = TextAreaField('Consignee Address', validators=[DataRequired(), Length(max=500)])
    challan_number = StringField('Challan No.', validators=[DataRequired(), Length(max=20)])
    reference_no = StringField('Reference No.', validators=[Length(max=50)])
    challan_date = StringField('Challan Date', validators=[DataRequired(), validate_date_format])
    delivery_date = StringField('Delivery Date', validators=[validate_date_format])
    expected_delivery_date = StringField('Expected Delivery Date', validators=[validate_date_format])
    place_of_supply = StringField('Place of Supply', validators=[Length(max=100)])
    delivery = StringField('Delivery', validators=[Optional(), Length(max=100)])
    shipping_charges = DecimalField('Shipping Charges', places=2, default=0)
    extra_billing_info = TextAreaField('Extra Address Info', 
                                     validators=[Optional(), Length(max=200)],
                                     render_kw={'placeholder': 'Additional address elements (e.g., Floor, Building, Landmark)'})
    notes = TextAreaField('Notes')
    # Address selection fields
    main_address = SelectField('Main Address (Header)', 
                              choices=[('salem', 'Salem Office'), ('chennai', 'Chennai Branch')], 
                              default='salem',
                              validators=[DataRequired()])
    branch_address = SelectField('Branch Address (Footer)', 
                                choices=[('salem', 'Salem Office'), ('chennai', 'Chennai Branch')], 
                                default='chennai',
                                validators=[DataRequired()])
    selected_signature = SelectField('Select Signature', coerce=str, validators=[Optional()])
    submit = SubmitField('Create Delivery Challan')

# Routes
@app.route('/')
@login_required
def dashboard():
    """
    Enhanced Dashboard Route
    Uses optimized analytics module for efficient data retrieval
    """
    try:
        # Get enhanced dashboard data from optimized analytics module
        from dashboard_analytics import get_dashboard_data
        # Pass db and models to avoid circular import issues
        models_dict = {
            'Invoice': Invoice,
            'Customer': Customer,
            'Company': Company,
            'PurchaseOrder': PurchaseOrder,
            'Vendor': Vendor,
            'InvoiceItem': InvoiceItem
        }
        dashboard_data = get_dashboard_data(db_session=db, models=models_dict)
        
        # Check if dashboard_data is valid (not empty defaults)
        # If total_revenue is 0, it might mean no data OR an error occurred
        # So we'll use it but also have fallback queries
        
        # Extract values from dashboard_data for template compatibility
        total_invoices = dashboard_data.get('invoice_metrics', {}).get('total_invoices', 0)
        total_amount = dashboard_data.get('revenue_metrics', {}).get('total_revenue', 0)
        paid_amount = dashboard_data.get('payment_status', {}).get('paid', {}).get('amount', 0)
        unpaid_amount = dashboard_data.get('payment_status', {}).get('unpaid', {}).get('amount', 0)
        partially_paid_amount = dashboard_data.get('payment_status', {}).get('partially_paid', {}).get('amount', 0)
        unpaid_invoices = dashboard_data.get('payment_status', {}).get('unpaid', {}).get('count', 0)
        paid_invoices = dashboard_data.get('payment_status', {}).get('paid', {}).get('count', 0)
        partially_paid_invoices = dashboard_data.get('payment_status', {}).get('partially_paid', {}).get('count', 0)
        overdue_invoices = dashboard_data.get('payment_status', {}).get('overdue', {}).get('count', 0)
        
        total_customers = dashboard_data.get('company_stats', {}).get('total_customers', 0)
        total_vendors = dashboard_data.get('company_stats', {}).get('total_vendors', 0)
        total_purchase_orders = dashboard_data.get('company_stats', {}).get('total_purchase_orders', 0)
        
        # If analytics returned zeros but we have invoices, use direct queries as fallback
        if total_invoices == 0:
            # Double-check with direct query
            direct_count = Invoice.query.count()
            if direct_count > 0:
                app.logger.warning("Analytics returned 0 invoices but direct query found invoices. Using direct queries.")
                total_invoices = direct_count
                total_amount = float(db.session.query(db.func.sum(Invoice.total_amount)).scalar() or 0)
                paid_amount = float(db.session.query(db.func.sum(Invoice.total_amount)).filter_by(status='paid').scalar() or 0)
                unpaid_amount = float(db.session.query(db.func.sum(Invoice.total_amount)).filter_by(status='unpaid').scalar() or 0)
                partially_paid_amount = float(db.session.query(db.func.sum(Invoice.total_amount)).filter_by(status='partially_paid').scalar() or 0)
                unpaid_invoices = Invoice.query.filter_by(status='unpaid').count()
                paid_invoices = Invoice.query.filter_by(status='paid').count()
                partially_paid_invoices = Invoice.query.filter_by(status='partially_paid').count()
                overdue_invoices = Invoice.query.filter(
                    Invoice.due_date < datetime.now().date(),
                    Invoice.status.in_(['unpaid', 'partially_paid'])
                ).count() if Invoice.due_date else 0
                total_customers = Customer.query.count()
                total_vendors = Vendor.query.count() if hasattr(Vendor, '__tablename__') else 0
                total_purchase_orders = PurchaseOrder.query.count() if hasattr(PurchaseOrder, '__tablename__') else 0
                # Keep dashboard_data but update it with actual values
                if dashboard_data:
                    dashboard_data['invoice_metrics']['total_invoices'] = total_invoices
                    dashboard_data['revenue_metrics']['total_revenue'] = total_amount
                    dashboard_data['payment_status']['paid']['amount'] = paid_amount
                    dashboard_data['payment_status']['paid']['count'] = paid_invoices
                    dashboard_data['payment_status']['unpaid']['amount'] = unpaid_amount
                    dashboard_data['payment_status']['unpaid']['count'] = unpaid_invoices
                    dashboard_data['payment_status']['partially_paid']['amount'] = partially_paid_amount
                    dashboard_data['payment_status']['partially_paid']['count'] = partially_paid_invoices
                    dashboard_data['company_stats']['total_customers'] = total_customers
                    dashboard_data['company_stats']['total_vendors'] = total_vendors
                    dashboard_data['company_stats']['total_purchase_orders'] = total_purchase_orders
        
        # Handle Purchase Order queries gracefully
        try:
            pending_pos = PurchaseOrder.query.filter_by(status='pending').count()
            completed_pos = PurchaseOrder.query.filter_by(status='completed').count()
            cancelled_pos = PurchaseOrder.query.filter_by(status='cancelled').count()
            recent_purchase_orders = PurchaseOrder.query.order_by(PurchaseOrder.created_at.desc()).limit(5).all()
        except Exception as e:
            app.logger.warning(f"Purchase Order queries failed: {e}")
            db.session.rollback()
            pending_pos = 0
            completed_pos = 0
            cancelled_pos = 0
            recent_purchase_orders = []
        
        # Recent activity - optimized queries
        try:
            recent_invoices = Invoice.query.order_by(Invoice.created_at.desc()).limit(5).all()
            recent_customers = Customer.query.order_by(Customer.created_at.desc()).limit(3).all()
        except Exception as e:
            app.logger.warning(f"Recent activity query failed: {e}")
            db.session.rollback()
            recent_invoices = []
            recent_customers = []
        
        # Convert monthly trends to format expected by template
        monthly_trends = dashboard_data.get('monthly_trends', [])
        monthly_invoices = []
        for trend in monthly_trends:
            monthly_invoices.append({
                'month': trend.get('month', ''),
                'count': trend.get('count', 0),
                'amount': trend.get('revenue', 0)
            })
        
        # Convert top customers format
        top_customers_list = dashboard_data.get('top_customers', {}).get('by_revenue', [])
        top_customers = []
        for cust in top_customers_list:
            top_customers.append({
                'name': cust[0] if isinstance(cust, tuple) else cust.get('name', ''),
                'total_revenue': cust[1] if isinstance(cust, tuple) else cust.get('revenue', 0),
                'invoice_count': cust[2] if isinstance(cust, tuple) else cust.get('count', 0)
            })
        
        enhanced_mode = True
        
    except Exception as e:
        app.logger.error(f"Dashboard data generation failed: {e}")
        import traceback
        traceback.print_exc()
        
        # Fallback to basic queries if analytics module fails
        dashboard_data = None
        enhanced_mode = False
        
        try:
            total_invoices = Invoice.query.count()
            total_customers = Customer.query.count()
            total_vendors = Vendor.query.count() if hasattr(Vendor, '__tablename__') else 0
            total_purchase_orders = PurchaseOrder.query.count() if hasattr(PurchaseOrder, '__tablename__') else 0
            
            total_amount = float(db.session.query(db.func.sum(Invoice.total_amount)).scalar() or 0)
            paid_amount = float(db.session.query(db.func.sum(Invoice.total_amount)).filter_by(status='paid').scalar() or 0)
            unpaid_amount = float(db.session.query(db.func.sum(Invoice.total_amount)).filter_by(status='unpaid').scalar() or 0)
            partially_paid_amount = float(db.session.query(db.func.sum(Invoice.total_amount)).filter_by(status='partially_paid').scalar() or 0)
            
            unpaid_invoices = Invoice.query.filter_by(status='unpaid').count()
            paid_invoices = Invoice.query.filter_by(status='paid').count()
            partially_paid_invoices = Invoice.query.filter_by(status='partially_paid').count()
            overdue_invoices = Invoice.query.filter(
                Invoice.due_date < datetime.now().date(),
                Invoice.status.in_(['unpaid', 'partially_paid'])
            ).count() if Invoice.due_date else 0
            
            pending_pos = PurchaseOrder.query.filter_by(status='pending').count() if hasattr(PurchaseOrder, '__tablename__') else 0
            completed_pos = PurchaseOrder.query.filter_by(status='completed').count() if hasattr(PurchaseOrder, '__tablename__') else 0
            cancelled_pos = PurchaseOrder.query.filter_by(status='cancelled').count() if hasattr(PurchaseOrder, '__tablename__') else 0
            recent_purchase_orders = PurchaseOrder.query.order_by(PurchaseOrder.created_at.desc()).limit(5).all() if hasattr(PurchaseOrder, '__tablename__') else []
            
            recent_invoices = Invoice.query.order_by(Invoice.created_at.desc()).limit(5).all()
            recent_customers = Customer.query.order_by(Customer.created_at.desc()).limit(3).all()
            monthly_invoices = []
            top_customers = []
        except Exception as fallback_error:
            app.logger.error(f"Fallback queries also failed: {fallback_error}")
            # Set all to defaults
            total_invoices = 0
            total_customers = 0
            total_vendors = 0
            total_purchase_orders = 0
            total_amount = 0
            paid_amount = 0
            unpaid_amount = 0
            partially_paid_amount = 0
            unpaid_invoices = 0
            paid_invoices = 0
            partially_paid_invoices = 0
            overdue_invoices = 0
            pending_pos = 0
            completed_pos = 0
            cancelled_pos = 0
            recent_purchase_orders = []
            recent_invoices = []
            recent_customers = []
            monthly_invoices = []
            top_customers = []
    
    return render_template('dashboard.html',
                          dashboard_data=dashboard_data,
                          enhanced_mode=enhanced_mode, 
                          total_invoices=total_invoices,
                          total_customers=total_customers,
                          total_vendors=total_vendors,
                          total_purchase_orders=total_purchase_orders,
                          total_amount=total_amount,
                          paid_amount=paid_amount,
                          unpaid_amount=unpaid_amount,
                          partially_paid_amount=partially_paid_amount,
                          unpaid_invoices=unpaid_invoices,
                          paid_invoices=paid_invoices,
                          partially_paid_invoices=partially_paid_invoices,
                          pending_pos=pending_pos,
                          completed_pos=completed_pos,
                          cancelled_pos=cancelled_pos,
                          recent_invoices=recent_invoices,
                          recent_purchase_orders=recent_purchase_orders,
                          recent_customers=recent_customers,
                          monthly_invoices=monthly_invoices,
                          top_customers=top_customers,
                          overdue_invoices=overdue_invoices)

@app.route('/api/dashboard-data')
@login_required
def dashboard_api():
    """API endpoint for dashboard data (for AJAX updates)"""
    try:
        from dashboard_analytics import get_dashboard_data
        
        # Pass db and models to avoid circular import issues (same as dashboard route)
        models_dict = {
            'Invoice': Invoice,
            'Customer': Customer,
            'Company': Company,
            'PurchaseOrder': PurchaseOrder,
            'Vendor': Vendor,
            'InvoiceItem': InvoiceItem
        }
        dashboard_data = get_dashboard_data(db_session=db, models=models_dict)
        
        # If analytics returned zeros but we have invoices, use direct queries as fallback
        total_invoices = dashboard_data.get('invoice_metrics', {}).get('total_invoices', 0)
        if total_invoices == 0:
            direct_count = Invoice.query.count()
            if direct_count > 0:
                # Update dashboard_data with actual values
                dashboard_data['invoice_metrics']['total_invoices'] = direct_count
                total_amount = float(db.session.query(db.func.sum(Invoice.total_amount)).scalar() or 0)
                dashboard_data['revenue_metrics']['total_revenue'] = total_amount
        
        return jsonify({
            'success': True,
            'data': dashboard_data
        })
    except Exception as e:
        import traceback
        app.logger.error(f"Dashboard API error: {str(e)}")
        app.logger.error(traceback.format_exc())
        return jsonify({
            'success': False,
            'error': str(e)
        })
# Secure redirect validation
def is_safe_url(target):
    """Check if URL is safe for redirect"""
    from urllib.parse import urlparse, urljoin
    ref_url = urlparse(request.host_url)
    test_url = urlparse(urljoin(request.host_url, target))
    return test_url.scheme in ('http', 'https') and ref_url.netloc == test_url.netloc
    

@app.route('/login', methods=['GET', 'POST'])
@limiter.limit("5 per minute")
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    
    form = LoginForm()
    if form.validate_on_submit():
        try:
            user = User.query.filter_by(username=form.username.data).first()
            if user and user.check_password(form.password.data) and user.is_active:
                login_user(user)
                # Log successful login
                log_activity(
                    action_type='login',
                    entity_type='user',
                    entity_id=user.id,
                    resource_identifier=user.username,
                    description=f"User logged in successfully"
                )
                next_page = request.args.get('next')
                return redirect(next_page) if next_page and is_safe_url(next_page) else redirect(url_for('dashboard'))
            else:
                # Log failed login attempt
                log_activity(
                    action_type='login_attempt_failed',
                    entity_type='user',
                    resource_identifier=form.username.data,
                    description=f"Failed login attempt for username: {form.username.data}"
                )
                flash('Invalid username or password', 'error')
        except Exception as e:
            app.logger.error(f"Login error: {str(e)}")
            flash('An error occurred during login. Please try again.', 'error')
    
    return render_template('login.html', form=form)

@app.route('/logout')
@login_required
def logout():
    # Log logout before session ends
    log_activity(
        action_type='logout',
        entity_type='user',
        entity_id=current_user.id,
        resource_identifier=current_user.username,
        description=f"User logged out"
    )
    logout_user()
    return redirect(url_for('login'))

@app.route('/company', methods=['GET', 'POST'])
@login_required
def company():
    company = Company.query.first()
    form = CompanyForm()
    
    if form.validate_on_submit():
        if company:
            # Update existing company
            old_name = company.name
            company.name = form.name.data
            company.gstin = form.gstin.data
            company.pan = form.pan.data
            company.address = form.address.data
            company.city = form.city.data
            company.state = form.state.data
            company.pincode = form.pincode.data
            company.phone = form.phone.data
            company.email = form.email.data
            company.updated_at = datetime.utcnow()
        else:
            # Create new company
            company = Company(
                name=form.name.data,
                gstin=form.gstin.data,
                pan=form.pan.data,
                address=form.address.data,
                city=form.city.data,
                state=form.state.data,
                pincode=form.pincode.data,
                phone=form.phone.data,
                email=form.email.data
            )
            db.session.add(company)
        
        # Handle logo upload
        if form.logo.data:
            logo_file = form.logo.data
            if logo_file.filename:
                # Validate file type
                allowed_extensions = {'jpg', 'jpeg', 'png', 'gif'}
                file_ext = logo_file.filename.rsplit('.', 1)[1].lower() if '.' in logo_file.filename else ''
                
                if file_ext not in allowed_extensions:
                    flash('Invalid file type. Only JPG, PNG, and GIF files are allowed.', 'error')
                    return redirect(url_for('company'))
                
                # Secure the filename
                filename = secure_filename(logo_file.filename)
                # Add timestamp to avoid conflicts
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S_')
                filename = timestamp + filename
                
                # Save file
                logo_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                logo_file.save(logo_path)
                
                # Validate and resize image
                try:
                    with PILImage.open(logo_path) as img:
                        # Validate image format
                        if img.format not in ['JPEG', 'PNG', 'GIF']:
                            os.remove(logo_path)
                            flash('Invalid image format.', 'error')
                            return redirect(url_for('company'))
                        
                        # Resize if too large
                        if img.width > 300 or img.height > 300:
                            img.thumbnail((300, 300), PILImage.Resampling.LANCZOS)
                            img.save(logo_path, optimize=True, quality=85)
                        
                        # Remove old logo if exists
                        if company and company.logo_path:
                            old_logo_path = os.path.join(app.config['UPLOAD_FOLDER'], company.logo_path)
                            if os.path.exists(old_logo_path):
                                os.remove(old_logo_path)
                        
                        # Update company logo path
                        company.logo_path = filename
                        
                except Exception as e:
                    # Clean up file if processing failed
                    if os.path.exists(logo_path):
                        os.remove(logo_path)
                    flash(f'Error processing image: {str(e)}', 'error')
                    return redirect(url_for('company'))
        
        try:
            db.session.commit()
            # Log activity
            if old_name:
                log_activity(
                    action_type='update',
                    entity_type='company',
                    entity_id=company.id,
                    resource_identifier=company.name,
                    old_value=old_name,
                    new_value=company.name,
                    description=f"Updated company details: {company.name}"
                )
            else:
                log_activity(
                    action_type='create',
                    entity_type='company',
                    entity_id=company.id,
                    resource_identifier=company.name,
                    description=f"Created company: {company.name}"
                )
            flash('Company details saved successfully!', 'success')
            return redirect(url_for('company'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error saving company details: {str(e)}', 'error')
            return redirect(url_for('company'))
    
    if company:
        form.name.data = company.name
        form.gstin.data = company.gstin
        form.pan.data = company.pan
        form.address.data = company.address
        form.city.data = company.city
        form.state.data = company.state
        form.pincode.data = company.pincode
        form.phone.data = company.phone
        form.email.data = company.email
    
    return render_template('company.html', form=form, company=company)

@app.route('/customers')
@login_required
def customers():
    customers = Customer.query.order_by(Customer.name).all()
    return render_template('customers.html', customers=customers)

@app.route('/customers/add', methods=['GET', 'POST'])
@login_required
def add_customer():
    form = CustomerForm()
    if form.validate_on_submit():
        customer = Customer(
            name=form.name.data,
            gstin=form.gstin.data,
            address=form.address.data,
            city=form.city.data,
            state=form.state.data,
            pincode=form.pincode.data,
            phone=form.phone.data,
            email=form.email.data
        )
        db.session.add(customer)
        db.session.commit()
        
        # Log activity
        log_activity(
            action_type='create',
            entity_type='customer',
            entity_id=customer.id,
            resource_identifier=customer.name,
            description=f"Created customer: {customer.name}"
        )
        
        flash('Customer added successfully!', 'success')
        return redirect(url_for('customers'))
    
    return render_template('add_customer.html', form=form)

@app.route('/customers/edit/<int:customer_id>', methods=['GET', 'POST'])
@login_required
def edit_customer(customer_id):
    customer = Customer.query.get_or_404(customer_id)
    form = CustomerForm()
    
    if form.validate_on_submit():
        customer.name = form.name.data
        customer.gstin = form.gstin.data
        customer.address = form.address.data
        customer.city = form.city.data
        customer.state = form.state.data
        customer.pincode = form.pincode.data
        customer.phone = form.phone.data
        customer.email = form.email.data
        customer.updated_at = datetime.utcnow()
        
        db.session.commit()
        
        # Log activity
        log_activity(
            action_type='update',
            entity_type='customer',
            entity_id=customer.id,
            resource_identifier=customer.name,
            description=f"Updated customer: {customer.name}"
        )
        
        flash('Customer updated successfully!', 'success')
        return redirect(url_for('customers'))
    
    # Populate form with existing data
    form.name.data = customer.name
    form.gstin.data = customer.gstin
    form.address.data = customer.address
    form.city.data = customer.city
    form.state.data = customer.state
    form.pincode.data = customer.pincode
    form.phone.data = customer.phone
    form.email.data = customer.email
    
    return render_template('edit_customer.html', form=form, customer=customer)

@app.route('/invoices')
@login_required
def invoices():
    # Get query parameters for filtering and sorting
    search = request.args.get('search', '').strip()
    status_filter = request.args.get('status', '')
    customer_filter = request.args.get('customer', '')
    date_from = request.args.get('date_from', '')
    date_to = request.args.get('date_to', '')
    amount_min = request.args.get('amount_min', '')
    amount_max = request.args.get('amount_max', '')
    sort_by = request.args.get('sort_by', 'invoice_number')
    sort_order = request.args.get('sort_order', 'desc')
    page = request.args.get('page', 1, type=int)
    per_page = 15
    
    # Start with base query
    query = Invoice.query
    
    # Apply search filter
    if search:
        query = query.join(Customer).filter(
            db.or_(
                Invoice.invoice_number.ilike(f'%{search}%'),
                Customer.name.ilike(f'%{search}%'),
                Customer.email.ilike(f'%{search}%'),
                Customer.phone.ilike(f'%{search}%'),
                Customer.gstin.ilike(f'%{search}%')
            )
        )
    
    # Apply status filter
    if status_filter:
        query = query.filter(Invoice.status == status_filter)
    
    # Apply customer filter
    if customer_filter:
        query = query.filter(Invoice.customer_id == customer_filter)
    
    # Apply date range filter
    if date_from:
        try:
            date_from_obj = datetime.strptime(date_from, '%Y-%m-%d').date()
            query = query.filter(Invoice.invoice_date >= date_from_obj)
        except ValueError:
            pass
    
    if date_to:
        try:
            date_to_obj = datetime.strptime(date_to, '%Y-%m-%d').date()
            query = query.filter(Invoice.invoice_date <= date_to_obj)
        except ValueError:
            pass
    
    # Apply amount range filter
    if amount_min:
        try:
            amount_min_val = float(amount_min)
            query = query.filter(Invoice.total_amount >= amount_min_val)
        except ValueError:
            pass
    
    if amount_max:
        try:
            amount_max_val = float(amount_max)
            query = query.filter(Invoice.total_amount <= amount_max_val)
        except ValueError:
            pass
    
    # Apply sorting
    if sort_by == 'invoice_number':
        if sort_order == 'desc':
            query = query.order_by(Invoice.invoice_number.desc())
        else:
            query = query.order_by(Invoice.invoice_number.asc())
    elif sort_by == 'date':
        if sort_order == 'desc':
            query = query.order_by(Invoice.invoice_date.desc())
        else:
            query = query.order_by(Invoice.invoice_date.asc())
    elif sort_by == 'customer':
        query = query.join(Customer)
        if sort_order == 'desc':
            query = query.order_by(Customer.name.desc())
        else:
            query = query.order_by(Customer.name.asc())
    elif sort_by == 'amount':
        if sort_order == 'desc':
            query = query.order_by(Invoice.total_amount.desc())
        else:
            query = query.order_by(Invoice.total_amount.asc())
    elif sort_by == 'status':
        if sort_order == 'desc':
            query = query.order_by(Invoice.status.desc())
        else:
            query = query.order_by(Invoice.status.asc())
    else:
        # Default sorting by invoice number descending
        query = query.order_by(Invoice.invoice_number.desc())
    
    # Apply pagination
    pagination = query.paginate(
        page=page, 
        per_page=per_page, 
        error_out=False
    )
    
    invoices = pagination.items
    
    # Get all customers for filter dropdown
    customers = Customer.query.order_by(Customer.name).all()
    
    # Get total count for stats (across all pages)
    total_query = Invoice.query
    if search:
        total_query = total_query.join(Customer).filter(
            db.or_(
                Invoice.invoice_number.ilike(f'%{search}%'),
                Customer.name.ilike(f'%{search}%'),
                Customer.email.ilike(f'%{search}%'),
                Customer.phone.ilike(f'%{search}%'),
                Customer.gstin.ilike(f'%{search}%')
            )
        )
    if status_filter:
        total_query = total_query.filter(Invoice.status == status_filter)
    if customer_filter:
        total_query = total_query.filter(Invoice.customer_id == customer_filter)
    if date_from:
        try:
            date_from_obj = datetime.strptime(date_from, '%Y-%m-%d').date()
            total_query = total_query.filter(Invoice.invoice_date >= date_from_obj)
        except ValueError:
            pass
    if date_to:
        try:
            date_to_obj = datetime.strptime(date_to, '%Y-%m-%d').date()
            total_query = total_query.filter(Invoice.invoice_date <= date_to_obj)
        except ValueError:
            pass
    if amount_min:
        try:
            amount_min_val = float(amount_min)
            total_query = total_query.filter(Invoice.total_amount >= amount_min_val)
        except ValueError:
            pass
    if amount_max:
        try:
            amount_max_val = float(amount_max)
            total_query = total_query.filter(Invoice.total_amount <= amount_max_val)
        except ValueError:
            pass
    
    all_invoices = total_query.all()
    
    return render_template('invoices.html', 
                         invoices=invoices, 
                         customers=customers,
                         all_invoices=all_invoices,  # For stats
                         pagination=pagination,
                         search=search,
                         status_filter=status_filter,
                         customer_filter=customer_filter,
                         date_from=date_from,
                         date_to=date_to,
                         amount_min=amount_min,
                         amount_max=amount_max,
                         sort_by=sort_by,
                         sort_order=sort_order)

@app.route('/invoices/create', methods=['GET', 'POST'])
@login_required
def create_invoice():
    form = InvoiceForm()
    form.customer_id.choices = [(c.id, f"{c.name} - {c.city}, {c.state}") for c in Customer.query.order_by(Customer.name, Customer.city).all()]
    
    # Populate signature choices
    user_signatures = UserSignature.query.filter_by(user_id=current_user.id).order_by(UserSignature.is_default.desc(), UserSignature.created_at.desc()).all()
    signature_choices = [(sig.id, f"{sig.signature_name}{' (Default)' if sig.is_default else ''}") for sig in user_signatures]
    signature_choices.insert(0, ('', 'No Signature'))  # Option for no signature
    form.selected_signature.choices = signature_choices
    
    # Generate next invoice number for display (starting fresh from 001)
    business_year = 2526
    
    # Find the highest sequential number that follows the new format (001, 002, 003...)
    existing_invoices = Invoice.query.filter(
        Invoice.invoice_number.like(f'MD{business_year}-%')
    ).all()
    
    # Look for invoices with 3-digit sequential format (001, 002, 003...)
    sequential_numbers = []
    for invoice in existing_invoices:
        try:
            number_part = invoice.invoice_number.split('-')[-1]
            if number_part.isdigit() and len(number_part) == 3:
                sequential_numbers.append(int(number_part))
        except (IndexError, ValueError):
            continue
    
    if sequential_numbers:
        next_number = max(sequential_numbers) + 1
    else:
        next_number = 1
    
    next_invoice_number = f"MD{business_year}-{next_number:03d}"
    
    # Set default dates to current date (HTML5 date format: YYYY-MM-DD)
    if request.method == 'GET':
        current_date = datetime.now().strftime('%Y-%m-%d')
        form.invoice_date.data = current_date
        # Set due date to 30 days from today
        due_date = datetime.now() + timedelta(days=30)
        form.due_date.data = due_date.strftime('%Y-%m-%d')
        # Set the suggested invoice number
        form.invoice_number.data = next_invoice_number
        
        # Set default text for terms and payment (editable)
        form.terms_text.data = 'CERTIFIED THAT THE PARTICULARS GIVEN ABOVE ARE TRUE AND CORRECT. WE FURTHER DECLARE THAT WE SHALL REMIT THE APPLICABLE GST AMOUNT AND FILE THE CORRESPONDING GST RETURNS.'
        form.payment_text.data = 'Payment: 100% against supply, immediate.\nWarranty: 12 months from the date of supply.\nApplicable only for: AC drive, PLC, servo drive & servo motors.'
    
    if form.validate_on_submit():
        # Use the invoice number from the form (user can edit it)
        invoice_number = form.invoice_number.data.strip()
        
        # Check if invoice number already exists
        existing_invoice = Invoice.query.filter_by(invoice_number=invoice_number).first()
        if existing_invoice:
            flash(f'Invoice number "{invoice_number}" already exists. Please use a different number.', 'error')
            return render_template('create_invoice.html', form=form, next_invoice_number=next_invoice_number)
        
        # Parse dates - handle both YYYY-MM-DD (HTML5 date input) and DD/MM/YYYY formats
        try:
            # Try HTML5 date format first (YYYY-MM-DD)
            invoice_date = datetime.strptime(form.invoice_date.data, '%Y-%m-%d').date()
        except ValueError:
            # Fall back to DD/MM/YYYY format
            invoice_date = datetime.strptime(form.invoice_date.data, '%d/%m/%Y').date()
        
        due_date = None
        if form.due_date.data:
            try:
                # Try HTML5 date format first (YYYY-MM-DD)
                due_date = datetime.strptime(form.due_date.data, '%Y-%m-%d').date()
            except ValueError:
                # Fall back to DD/MM/YYYY format
                due_date = datetime.strptime(form.due_date.data, '%d/%m/%Y').date()
        
        # Get company (assuming single company setup)
        company = Company.query.first()
        if not company:
            flash('Company details not found. Please set up company information first.', 'error')
            return redirect(url_for('company'))
        
        # Create invoice (will be updated with items and totals)
        # Compose metadata for terms/payment/reference/addresses to store in notes as JSON
        meta = {
            'reference_no': form.reference_no.data or '-',
            'eway_bill': form.eway_bill.data or '-',
            'eway_bill_date': form.eway_bill_date.data or '',
            'extra_billing_info': form.extra_billing_info.data or '',
            'terms_text': form.terms_text.data or 'CERTIFIED THAT THE PARTICULARS GIVEN ABOVE ARE TRUE AND CORRECT. WE FURTHER DECLARE THAT WE SHALL REMIT THE APPLICABLE GST AMOUNT AND FILE THE CORRESPONDING GST RETURNS.',
            'payment_text': form.payment_text.data or 'Payment: 100% against supply, immediate.\nWarranty: 12 months from the date of supply.\nApplicable only for: AC drive, PLC, servo drive & servo motors.',
            'main_address': form.main_address.data,
            'branch_address': form.branch_address.data,
            'is_sac': form.is_sac.data or False  # SAC checkbox - stored in metadata
        }

        # Handle signature selection
        selected_signature_id = None
        if form.selected_signature.data and form.selected_signature.data != '':
            try:
                selected_signature_id = int(form.selected_signature.data)
            except (ValueError, TypeError):
                # Skip if invalid ID provided
                selected_signature_id = None

        # Prepare e-way bill fields
        eway_mode = form.eway_mode.data or None
        vehicle_number = form.vehicle_number.data.strip() if form.vehicle_number.data else None
        rr_number = form.rr_number.data.strip() if form.rr_number.data else None
        transporter_id = form.transporter_id.data.strip() if form.transporter_id.data else None
        from_place = form.from_place.data.strip() if form.from_place.data else None
        from_state_code = (form.from_state_code.data or '').strip()[:2] or None
        to_place = form.to_place.data.strip() if form.to_place.data else None
        to_state_code = (form.to_state_code.data or '').strip()[:2] or None
        eway_valid_upto = None
        if form.eway_valid_upto.data:
            try:
                eway_valid_upto = datetime.strptime(form.eway_valid_upto.data, '%Y-%m-%d').date()
            except ValueError:
                try:
                    eway_valid_upto = datetime.strptime(form.eway_valid_upto.data, '%d/%m/%Y').date()
                except ValueError:
                    eway_valid_upto = None

        invoice = Invoice(
            invoice_number=invoice_number,
            customer_id=form.customer_id.data,
            company_id=company.id,
            invoice_date=invoice_date,
            due_date=due_date,
            shipping_charges=form.shipping_charges.data or 0,
            notes=json.dumps(meta),
            subtotal=0,
            total_amount=0,
            selected_signature_id=selected_signature_id,
            eway_bill=(form.eway_bill.data.strip() if form.eway_bill.data else None),
            eway_mode=eway_mode,
            vehicle_number=vehicle_number,
            rr_number=rr_number,
            transporter_id=transporter_id,
            from_place=from_place,
            from_state_code=from_state_code,
            to_place=to_place,
            to_state_code=to_state_code,
            eway_valid_upto=eway_valid_upto
        )
        
        db.session.add(invoice)
        db.session.commit()
        
        # Log activity
        log_activity(
            action_type='create',
            entity_type='invoice',
            entity_id=invoice.id,
            resource_identifier=invoice.invoice_number,
            description=f"Created invoice: {invoice.invoice_number}"
        )
        
        # Send email notification
        # Notifications disabled
        
        flash('Invoice created! Now add items to complete it.', 'success')
        return redirect(url_for('edit_invoice', invoice_id=invoice.id))
    
    return render_template('create_invoice.html', form=form, next_invoice_number=next_invoice_number)

@app.route('/invoices/<int:invoice_id>')
@login_required
def view_invoice(invoice_id):
    invoice = Invoice.query.get_or_404(invoice_id)
    # Parse notes JSON if it exists
    meta = {}
    if invoice.notes:
        try:
            meta = json.loads(invoice.notes)
        except (json.JSONDecodeError, TypeError):
            meta = {}
    return render_template('view_invoice.html', invoice=invoice, meta=meta)

@app.route('/invoices/<int:invoice_id>/edit')
@login_required
def edit_invoice(invoice_id):
    invoice = Invoice.query.get_or_404(invoice_id)
    
    # Parse metadata from notes
    import json
    meta = json.loads(invoice.notes) if invoice.notes else {}
    
    # Convert items to JSON-serializable format
    items_data = []
    for item in invoice.items:
        items_data.append({
            'id': item.id,
            'description': item.description,
            'quantity': float(item.quantity),
            'unit_price': float(item.unit_price),
            'tax_rate': float(item.tax_rate),
            'amount': float(item.amount),
            'hsn_code': item.hsn_code
        })
    
    return render_template('edit_invoice.html', invoice=invoice, items_json=json.dumps(items_data), meta=meta)


@app.route('/invoices/<int:invoice_id>/edit/details', methods=['GET', 'POST'])
@login_required
def edit_invoice_details(invoice_id):
    invoice = Invoice.query.get_or_404(invoice_id)
    form = InvoiceForm()

    # Populate customer choices
    form.customer_id.choices = [(c.id, f"{c.name} - {c.city}, {c.state}") for c in Customer.query.order_by(Customer.name, Customer.city).all()]

    # Populate signature choices
    user_signatures = UserSignature.query.filter_by(user_id=current_user.id).order_by(UserSignature.is_default.desc(), UserSignature.created_at.desc()).all()
    signature_choices = [(sig.id, f"{sig.signature_name}{' (Default)' if sig.is_default else ''}") for sig in user_signatures]
    signature_choices.insert(0, ('', 'No Signature'))
    form.selected_signature.choices = signature_choices

    # Parse existing metadata
    try:
        meta = json.loads(invoice.notes) if invoice.notes else {}
    except Exception:
        meta = {}

    if request.method == 'GET':
        # Pre-fill with existing values
        form.customer_id.data = invoice.customer_id
        form.invoice_date.data = invoice.invoice_date.strftime('%Y-%m-%d') if invoice.invoice_date else ''
        form.due_date.data = invoice.due_date.strftime('%Y-%m-%d') if invoice.due_date else ''
        form.invoice_number.data = invoice.invoice_number
        form.shipping_charges.data = float(invoice.shipping_charges or 0)
        form.reference_no.data = meta.get('reference_no') or '-'
        form.eway_bill.data = meta.get('eway_bill') or '-'
        form.eway_bill_date.data = meta.get('eway_bill_date') or ''
        form.extra_billing_info.data = meta.get('extra_billing_info') or ''
        form.terms_text.data = meta.get('terms_text') or ''
        form.payment_text.data = meta.get('payment_text') or ''
        form.main_address.data = meta.get('main_address') or 'salem'
        form.branch_address.data = meta.get('branch_address') or 'chennai'
        form.selected_signature.data = str(invoice.selected_signature_id or '')
        form.is_sac.data = meta.get('is_sac', False)  # Get from metadata, not database column
        # Transport fields are intentionally not edited here

    if form.validate_on_submit():
        # Invoice number uniqueness (excluding current invoice)
        new_invoice_number = form.invoice_number.data.strip()
        existing = Invoice.query.filter(Invoice.invoice_number == new_invoice_number, Invoice.id != invoice.id).first()
        if existing:
            flash(f'Invoice number "{new_invoice_number}" already exists. Please use a different number.', 'error')
            return render_template('edit_invoice_details.html', form=form, invoice=invoice)

        # Parse dates
        try:
            invoice_date = datetime.strptime(form.invoice_date.data, '%Y-%m-%d').date() if form.invoice_date.data else None
        except ValueError:
            try:
                invoice_date = datetime.strptime(form.invoice_date.data, '%d/%m/%Y').date()
            except ValueError:
                invoice_date = None

        due_date = None
        if form.due_date.data:
            try:
                due_date = datetime.strptime(form.due_date.data, '%Y-%m-%d').date()
            except ValueError:
                try:
                    due_date = datetime.strptime(form.due_date.data, '%d/%m/%Y').date()
                except ValueError:
                    due_date = None

        # Update metadata
        updated_meta = {
            'reference_no': form.reference_no.data or '-',
            'eway_bill': form.eway_bill.data or '-',
            'eway_bill_date': form.eway_bill_date.data or '',
            'extra_billing_info': form.extra_billing_info.data or '',
            'terms_text': form.terms_text.data or '',
            'payment_text': form.payment_text.data or '',
            'main_address': form.main_address.data,
            'branch_address': form.branch_address.data,
            'is_sac': form.is_sac.data or False  # SAC checkbox - stored in metadata
        }

        # Handle signature selection
        selected_signature_id = None
        if form.selected_signature.data and form.selected_signature.data != '':
            try:
                selected_signature_id = int(form.selected_signature.data)
            except (ValueError, TypeError):
                selected_signature_id = None

        # Apply updates
        invoice.invoice_number = new_invoice_number
        invoice.customer_id = form.customer_id.data
        invoice.invoice_date = invoice_date
        invoice.due_date = due_date
        invoice.shipping_charges = form.shipping_charges.data or 0
        invoice.notes = json.dumps(updated_meta)
        invoice.selected_signature_id = selected_signature_id
        # Transport fields left unchanged

        try:
            db.session.commit()
            flash('Invoice details updated successfully.', 'success')
            return redirect(url_for('edit_invoice', invoice_id=invoice.id))
        except Exception as e:
            db.session.rollback()
            flash(f'Error updating invoice: {str(e)}', 'error')

    return render_template('edit_invoice_details.html', form=form, invoice=invoice)

@app.route('/customers/delete/<int:customer_id>', methods=['POST'])
@login_required
def delete_customer(customer_id):
    from flask_wtf.csrf import validate_csrf
    from wtforms import ValidationError
    
    try:
        validate_csrf(request.form.get('csrf_token'))
    except ValidationError:
        flash('Invalid request. Please try again.', 'error')
        return redirect(url_for('customers'))
    
    customer = Customer.query.get_or_404(customer_id)
    
    # Check if customer has invoices
    if customer.invoices:
        flash('Cannot delete customer with existing invoices. Please delete invoices first.', 'error')
        return redirect(url_for('customers'))
    
    try:
        db.session.delete(customer)
        db.session.commit()
        flash('Customer deleted successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error deleting customer: {str(e)}', 'error')
    
    return redirect(url_for('customers'))

# Vendor Routes
@app.route('/vendors')
@login_required
def vendors():
    vendors = Vendor.query.order_by(Vendor.name).all()
    return render_template('vendors.html', vendors=vendors)

@app.route('/vendors/add', methods=['GET', 'POST'])
@login_required
def add_vendor():
    form = VendorForm()
    if form.validate_on_submit():
        vendor = Vendor(
            name=form.name.data,
            gstin=form.gstin.data,
            address=form.address.data,
            city=form.city.data,
            state=form.state.data,
            pincode=form.pincode.data,
            phone=form.phone.data,
            email=form.email.data,
            contact_person=form.contact_person.data,
            payment_terms=form.payment_terms.data
        )
        db.session.add(vendor)
        db.session.commit()
        flash('Vendor added successfully!', 'success')
        return redirect(url_for('vendors'))
    
    return render_template('add_vendor.html', form=form)

@app.route('/vendors/edit/<int:vendor_id>', methods=['GET', 'POST'])
@login_required
def edit_vendor(vendor_id):
    vendor = Vendor.query.get_or_404(vendor_id)
    form = VendorForm()
    
    if form.validate_on_submit():
        vendor.name = form.name.data
        vendor.gstin = form.gstin.data
        vendor.address = form.address.data
        vendor.city = form.city.data
        vendor.state = form.state.data
        vendor.pincode = form.pincode.data
        vendor.phone = form.phone.data
        vendor.email = form.email.data
        vendor.contact_person = form.contact_person.data
        vendor.payment_terms = form.payment_terms.data
        vendor.updated_at = datetime.utcnow()
        
        db.session.commit()
        flash('Vendor updated successfully!', 'success')
        return redirect(url_for('vendors'))
    
    # Populate form with existing data
    form.name.data = vendor.name
    form.gstin.data = vendor.gstin
    form.address.data = vendor.address
    form.city.data = vendor.city
    form.state.data = vendor.state
    form.pincode.data = vendor.pincode
    form.phone.data = vendor.phone
    form.email.data = vendor.email
    form.contact_person.data = vendor.contact_person
    form.payment_terms.data = vendor.payment_terms
    
    return render_template('edit_vendor.html', form=form, vendor=vendor)

@app.route('/vendors/delete/<int:vendor_id>', methods=['POST'])
@login_required
def delete_vendor(vendor_id):
    from flask_wtf.csrf import validate_csrf
    from wtforms import ValidationError
    
    try:
        validate_csrf(request.form.get('csrf_token'))
    except ValidationError:
        flash('Invalid request. Please try again.', 'error')
        return redirect(url_for('vendors'))
    
    vendor = Vendor.query.get_or_404(vendor_id)
    
    # Check if vendor has purchase orders
    if vendor.purchase_orders:
        flash('Cannot delete vendor with existing purchase orders. Please delete purchase orders first.', 'error')
        return redirect(url_for('vendors'))
    
    try:
        db.session.delete(vendor)
        db.session.commit()
        flash('Vendor deleted successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error deleting vendor: {str(e)}', 'error')
    
    return redirect(url_for('vendors'))

@app.route('/api/customers/<int:customer_id>', methods=['GET'])
@login_required
def get_customer_details(customer_id):
    customer = Customer.query.get_or_404(customer_id)
    return jsonify({
        'id': customer.id,
        'name': customer.name,
        'address': customer.address,
        'city': customer.city,
        'state': customer.state,
        'pincode': customer.pincode,
        'gstin': customer.gstin,
        'phone': customer.phone,
        'email': customer.email
    })

@app.route('/api/vendors/<int:vendor_id>', methods=['GET'])
@login_required
def get_vendor_details(vendor_id):
    vendor = Vendor.query.get_or_404(vendor_id)
    return jsonify({
        'id': vendor.id,
        'name': vendor.name,
        'address': vendor.address,
        'city': vendor.city,
        'state': vendor.state,
        'pincode': vendor.pincode,
        'gstin': vendor.gstin,
        'phone': vendor.phone,
        'email': vendor.email,
        'contact_person': vendor.contact_person,
        'payment_terms': vendor.payment_terms
    })

@app.route('/api/invoices/<int:invoice_id>/items', methods=['POST'])
@login_required
def add_invoice_item(invoice_id):
    invoice = Invoice.query.get_or_404(invoice_id)
    
    data = request.get_json()
    description = data.get('description')
    hsn_code = data.get('hsn_code', '85044090')
    
    from decimal import Decimal
    quantity = Decimal(str(data.get('quantity', 0)))
    unit_price = Decimal(str(data.get('unit_price', 0)))
    tax_rate = Decimal(str(data.get('tax_rate', 18)))
    discount_type = data.get('discount_type', 'amount')
    discount_value = Decimal(str(data.get('discount_value', 0)))
    
    if not description or quantity <= 0 or unit_price <= 0:
        return jsonify({'error': 'Invalid item data'}), 400
    
    # Calculate amount with discount using proper validation and precision
    gross_amount = quantity * unit_price
    
    # Validate and calculate discount amount using our fixed validation
    validated_discount_value = validate_discount_value(discount_type, discount_value, gross_amount)
    
    if discount_type == 'percentage' and validated_discount_value > 0:
        discount_amount = gross_amount * validated_discount_value / Decimal('100')
    elif discount_type == 'amount' and validated_discount_value > 0:
        discount_amount = validated_discount_value
    else:
        discount_amount = Decimal('0')
    
    # Round discount amount to 2 decimal places
    from decimal import ROUND_HALF_UP
    discount_amount = discount_amount.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
    
    # Calculate final amount and ensure it's not negative
    amount = max(gross_amount - discount_amount, Decimal('0'))
    amount = amount.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
    
    # Create new invoice item
    item = InvoiceItem(
        invoice_id=invoice_id,
        description=description,
        hsn_code=hsn_code,
        quantity=quantity,
        unit_price=unit_price,
        discount_type=discount_type,
        discount_value=validated_discount_value,  # FIXED: Store validated value, not original
        tax_rate=tax_rate,
        amount=amount
    )
    
    db.session.add(item)
    
    # Update invoice totals
    update_invoice_totals(invoice)
    
    db.session.commit()
    
    # Log activity
    log_activity(
        action_type='add_item',
        entity_type='invoice',
        entity_id=invoice.id,
        resource_identifier=invoice.invoice_number,
        description=f"Added item to invoice {invoice.invoice_number}: {description} (Qty: {quantity})"
    )
    
    return jsonify({
        'success': True,
        'item': {
            'id': item.id,
            'description': item.description,
            'hsn_code': item.hsn_code,
            'quantity': float(item.quantity),
            'unit_price': float(item.unit_price),
            'discount_type': item.discount_type,
            'discount_value': float(item.discount_value),
            'tax_rate': float(item.tax_rate),
            'amount': float(item.amount)
        }
    })

@app.route('/api/invoices/<int:invoice_id>/items/<int:item_id>', methods=['DELETE'])
@login_required
def delete_invoice_item(invoice_id, item_id):
    invoice = Invoice.query.get_or_404(invoice_id)
    item = InvoiceItem.query.filter_by(id=item_id, invoice_id=invoice_id).first_or_404()
    
    db.session.delete(item)
    
    # Check if invoice still has items before updating totals
    if invoice.items:
        # Update invoice totals only if there are still items
        update_invoice_totals(invoice)
    else:
        # Reset totals to zero if no items left
        invoice.subtotal = 0
        invoice.cgst_amount = 0
        invoice.sgst_amount = 0
        invoice.igst_amount = 0
        invoice.total_amount = 0
    
    db.session.commit()
    
    # Log activity
    log_activity(
        action_type='remove_item',
        entity_type='invoice',
        entity_id=invoice.id,
        resource_identifier=invoice.invoice_number,
        description=f"Removed item from invoice {invoice.invoice_number}: {item.description}"
    )
    
    return jsonify({'success': True})

@app.route('/api/invoices/<int:invoice_id>/items/<int:item_id>', methods=['PUT'])
@login_required
def update_invoice_item(invoice_id, item_id):
    invoice = Invoice.query.get_or_404(invoice_id)
    item = InvoiceItem.query.filter_by(id=item_id, invoice_id=invoice_id).first_or_404()
    
    data = request.get_json()
    
    # Update item fields
    item.description = data.get('description', item.description)
    item.hsn_code = data.get('hsn_code', item.hsn_code)
    item.quantity = Decimal(str(data.get('quantity', item.quantity)))
    item.unit_price = Decimal(str(data.get('unit_price', item.unit_price)))
    item.tax_rate = Decimal(str(data.get('tax_rate', item.tax_rate)))
    item.discount_type = data.get('discount_type', item.discount_type)
    item.discount_value = Decimal(str(data.get('discount_value', item.discount_value)))
    
    # Recalculate amount with discount using proper Decimal arithmetic
    from decimal import Decimal
    gross_amount = Decimal(str(item.quantity)) * Decimal(str(item.unit_price))
    
    # Validate and calculate discount amount
    validated_discount_value = validate_discount_value(item.discount_type, item.discount_value, gross_amount)
    
    if item.discount_type == 'percentage' and validated_discount_value > 0:
        discount_amount = gross_amount * validated_discount_value / Decimal('100')
    elif item.discount_type == 'amount' and validated_discount_value > 0:
        discount_amount = validated_discount_value
    else:
        discount_amount = Decimal('0')
    
    # Calculate final amount after discount (ensure it's not negative)
    final_amount = gross_amount - discount_amount
    item.amount = max(final_amount, Decimal('0'))
    
    # FIXED: Update the discount_value with validated value
    item.discount_value = validated_discount_value
    
    # Update invoice totals
    update_invoice_totals(invoice)
    
    db.session.commit()
    
    # Log activity
    log_activity(
        action_type='update_item',
        entity_type='invoice',
        entity_id=invoice.id,
        resource_identifier=invoice.invoice_number,
        description=f"Updated item in invoice {invoice.invoice_number}: {item.description}"
    )
    
    return jsonify({
        'success': True,
        'item': {
            'id': item.id,
            'description': item.description,
            'hsn_code': item.hsn_code,
            'quantity': float(item.quantity),
            'unit_price': float(item.unit_price),
            'discount_type': item.discount_type,
            'discount_value': float(item.discount_value),
            'tax_rate': float(item.tax_rate),
            'amount': float(item.amount)
        }
    })

@app.route('/api/invoices/<int:invoice_id>/status', methods=['POST'])
@login_required
def update_invoice_status(invoice_id):
    invoice = Invoice.query.get_or_404(invoice_id)
    
    data = request.get_json()
    status = data.get('status')
    
    if status not in ['paid', 'unpaid', 'partially_paid']:
        return jsonify({'error': 'Invalid status'}), 400
    
    invoice.status = status
    db.session.commit()
    
    # Log activity
    log_activity(
        action_type='update_status',
        entity_type='invoice',
        entity_id=invoice.id,
        resource_identifier=invoice.invoice_number,
        description=f"Changed invoice {invoice.invoice_number} status to: {status}"
    )
    
    return jsonify({'success': True, 'status': status})

@app.route('/api/invoices/<int:invoice_id>/settings', methods=['POST'])
@login_required
def update_invoice_settings(invoice_id):
    invoice = Invoice.query.get_or_404(invoice_id)
    
    data = request.get_json()
    from decimal import Decimal
    shipping_charges = Decimal(str(data.get('shipping_charges', 0)))
    
    invoice.shipping_charges = shipping_charges
    
    # Update metadata (reference_no, eway_bill, etc.)
    import json
    meta = json.loads(invoice.notes) if invoice.notes else {}
    meta['reference_no'] = data.get('reference_no', '-')
    meta['eway_bill'] = data.get('eway_bill', '-')
    meta['eway_bill_date'] = data.get('eway_bill_date', '')
    invoice.notes = json.dumps(meta)
    
    # Update invoice totals
    update_invoice_totals(invoice)
    
    db.session.commit()
    
    # Log activity
    log_activity(
        action_type='update_settings',
        entity_type='invoice',
        entity_id=invoice.id,
        resource_identifier=invoice.invoice_number,
        description=f"Updated settings for invoice {invoice.invoice_number}"
    )
    
    return jsonify({'success': True})

@app.route('/invoices/<int:invoice_id>/pdf')
@login_required
def invoice_pdf(invoice_id):
    """Generate PDF invoice matching exact reference design - A4 single page"""
    invoice = Invoice.query.get_or_404(invoice_id)
    company = Company.query.first()
    
    if not company:
        flash('Company details not found. Please set up company information first.', 'error')
        return redirect(url_for('company'))

    def compose_address_block(name, address, city, state, pincode, phone=None, email=None):
        lines = [name] if name else []
        if address:
            lines.append(address.strip())
        location_line = ", ".join([part for part in [city, pincode] if part])
        if location_line:
            lines.append(location_line)
        if state:
            lines.append(f"{state}, India")
        if phone:
            lines.append(f"Ph: {phone}")
        if email:
            lines.append(email)
        return "\n".join([line for line in lines if line])

    default_to_block = compose_address_block(
        invoice.customer.name,
        invoice.customer.address,
        invoice.customer.city,
        invoice.customer.state,
        invoice.customer.pincode,
        invoice.customer.phone,
        invoice.customer.email
    )

    default_from_block = compose_address_block(
        company.name,
        company.address,
        company.city,
        company.state,
        company.pincode,
        company.phone,
        company.email
    )

    def compose_address_block(name, address, city, state, pincode, phone=None, email=None):
        lines = [name] if name else []
        if address:
            lines.append(address.strip())
        location_line = ", ".join([part for part in [city, pincode] if part])
        if location_line:
            lines.append(location_line)
        if state:
            lines.append(f"{state}, India")
        if phone:
            lines.append(f"Ph: {phone}")
        if email:
            lines.append(email)
        return "\n".join([line for line in lines if line])

    default_to_block = compose_address_block(
        invoice.customer.name,
        invoice.customer.address,
        invoice.customer.city,
        invoice.customer.state,
        invoice.customer.pincode,
        invoice.customer.phone,
        invoice.customer.email
    )

    default_from_block = compose_address_block(
        company.name,
        company.address,
        company.city,
        company.state,
        company.pincode,
        company.phone,
        company.email
    )
    
    # Validate invoice has items
    if not invoice.items:
        flash('Cannot generate PDF for invoice with no items. Please add items first.', 'error')
        return redirect(url_for('edit_invoice', invoice_id=invoice_id))
    
    # Validate invoice data
    try:
        validate_invoice_data(invoice)
    except ValueError as e:
        flash(f'Invoice validation error: {str(e)}', 'error')
        return redirect(url_for('edit_invoice', invoice_id=invoice_id))
    
    # Create PDF buffer - tight margins for A4 single page
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, 
                          leftMargin=0.3*inch, rightMargin=0.3*inch,
                          topMargin=0.3*inch, bottomMargin=0.3*inch)
    
    # Styles matching your reference exactly
    styles = getSampleStyleSheet()
    
    # TAX INVOICE title - Large, bold, red, centered
    title_style = ParagraphStyle(
        'TaxInvoiceTitle',
        parent=styles['Heading1'],
        fontSize=20,
        fontName='Helvetica-Bold',
        textColor=colors.HexColor('#d32f2f'),  # Red color
        alignment=TA_CENTER,
        spaceAfter=8,
        spaceBefore=4
    )
    
    # Company name - Blue, bold
    company_style = ParagraphStyle(
        'CompanyName',
        parent=styles['Normal'],
        fontSize=12,
        fontName='Helvetica-Bold',
        textColor=colors.HexColor('#1f4e79'),  # Blue color
        spaceAfter=2
    )
    
    # Tagline - Blue, smaller
    tagline_style = ParagraphStyle(
        'Tagline',
        parent=styles['Normal'],
        fontSize=7,
        fontName='Helvetica',
        textColor=colors.HexColor('#1f4e79'),  # Blue color
        spaceAfter=4
    )
    
    # Address style
    address_style = ParagraphStyle(
        'Address',
        parent=styles['Normal'],
        fontSize=7,
        fontName='Helvetica',
        textColor=colors.black,
        spaceAfter=1,
        leading=9
    )
    
    # Contact style
    contact_style = ParagraphStyle(
        'Contact',
        parent=styles['Normal'],
        fontSize=7,
        fontName='Helvetica',
        textColor=colors.black,
        spaceAfter=1
    )
    
    # Invoice details style
    invoice_detail_style = ParagraphStyle(
        'InvoiceDetail',
        parent=styles['Normal'],
        fontSize=7,
        fontName='Helvetica-Bold',
        textColor=colors.black,
        spaceAfter=1
    )
    
    # Normal text style
    normal_style = ParagraphStyle(
        'Normal',
        parent=styles['Normal'],
        fontSize=7,
        fontName='Helvetica',
        textColor=colors.black,
        spaceAfter=2
    )
    
    # Build the story
    story = []
    
    # Header section with logo, company info, and invoice details
    header_data = []
    
    # Left column - Logo and company info
    left_col = []
    
    # Add logo if available - FORCE logo display
    logo_path = os.path.join('static', 'uploads', 'md_logo.jpg')
    if os.path.exists(logo_path):
        try:
            logo = Image(logo_path, width=1.2*inch, height=1.2*inch)
            left_col.append(logo)
            left_col.append(Spacer(1, 6))
        except Exception as e:
            # If logo fails, add a placeholder
            left_col.append(Paragraph("LOGO", company_style))
            left_col.append(Spacer(1, 6))
    else:
        # Add placeholder if logo not found
        left_col.append(Paragraph("LOGO", company_style))
        left_col.append(Spacer(1, 6))
    
    # Get company details
    company_details = get_company_details()
    
    # Company name and tagline
    left_col.append(Paragraph("MAHADEVI&CO", company_style))
    left_col.append(Paragraph(company_details['tagline'], tagline_style))
    
    # Company address - EXACT from your reference
    address_text = """
    I/462-1, National Nagar,<br/>
    Alangar Theatre Back side,<br/>
    Omalur (T.K), Salem (D.T) 636 455<br/>
    Ph: +91-4290 796930, +91-9444201021<br/>
    Email: mahadevico@yahoo.in, mahadevico77@gmail.com
    """
    left_col.append(Paragraph(address_text, address_style))
    
    # Right column - Invoice details - EXACT from your reference
    right_col = []
    right_col.append(Paragraph(f"GSTIN: {company_details['gstin']}", invoice_detail_style))
    right_col.append(Paragraph(f"State: {company_details['state']}", invoice_detail_style))
    right_col.append(Paragraph(f"PAN: {company_details['pan']}", invoice_detail_style))
    right_col.append(Paragraph(f"Invoice Date: {invoice.invoice_date.strftime('%d/%m/%Y')}", invoice_detail_style))
    right_col.append(Paragraph(f"Invoice No.: {invoice.invoice_number}", invoice_detail_style))
    right_col.append(Paragraph("Reference No.: -", invoice_detail_style))
    
    # Create header table - Better column widths
    header_table = Table([left_col, right_col], colWidths=[4*inch, 2*inch])
    header_table.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('LEFTPADDING', (0, 0), (-1, -1), 0),
        ('RIGHTPADDING', (0, 0), (-1, -1), 0),
        ('TOPPADDING', (0, 0), (-1, -1), 0),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 0),
    ]))
    
    story.append(header_table)
    story.append(Spacer(1, 4))
    
    # TAX INVOICE title
    story.append(Paragraph("TAX INVOICE", title_style))
    story.append(Spacer(1, 4))
    
    # Customer and shipping details table - EXACT format from reference
    customer_data = [
        ['Customer Name', 'Billing Address', 'Shipping Address'],
        [f"{invoice.customer.name}<br/>Customer GSTIN: {invoice.customer.gstin}", 
         f"{invoice.customer.name}<br/>{invoice.customer.address}", 
         f"{invoice.customer.name}<br/>{invoice.customer.address}<br/>{invoice.customer.gstin}"],
        ['Place of Supply', get_state_from_gstin(invoice.customer.gstin) if invoice.customer.gstin else "Unknown State", ''],
        ['Due Date', invoice.due_date.strftime('%d/%m/%Y') if invoice.due_date else '', '']
    ]
    
    customer_table = Table(customer_data, colWidths=[1.8*inch, 2.1*inch, 2.1*inch])
    customer_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#f5f5f5')),  # Light grey header
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 8),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 6),
        ('BACKGROUND', (0, 1), (-1, -1), colors.white),
        ('FONTSIZE', (0, 1), (-1, -1), 7),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('LEFTPADDING', (0, 0), (-1, -1), 4),
        ('RIGHTPADDING', (0, 0), (-1, -1), 4),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
    ]))
    
    story.append(customer_table)
    story.append(Spacer(1, 4))
    
    # Items table with yellow background (matching your reference)
    items_data = [['Item', 'HSN/SAC', 'Quantity', 'Rate/Item (₹)', 'Discount (₹)', 'Taxable Value (₹)', 'CGST (₹)', 'SGST/UTGST (₹)', 'CESS (₹)', 'Total (₹)']]
    
    total_taxable = 0
    total_cgst = 0
    total_sgst = 0
    total_cess = 0
    total_amount = 0
    
    for item in invoice.items:
        # Calculate GST based on interstate/intrastate
        # Get company state from GSTIN
        company_details = get_company_details()
        if not company_details['gstin']:
            flash('Company GSTIN is missing. Please update company details with GSTIN.', 'error')
            return redirect(url_for('invoices'))
        
        company_state = get_state_from_gstin(company_details['gstin'])
        
        # Get customer state from GSTIN
        if not invoice.customer.gstin:
            flash('Customer GSTIN is missing. Please update customer details with GSTIN.', 'error')
            return redirect(url_for('invoices'))
        
        customer_state = get_state_from_gstin(invoice.customer.gstin)
        is_interstate = customer_state != company_state
        cgst, sgst, igst = calculate_gst(item.amount, item.tax_rate, is_interstate)
        
        if is_interstate:
            cgst_display = "0.00"
            sgst_display = f"{igst:.2f} @{item.tax_rate}%"
        else:
            cgst_display = f"{cgst:.2f} @{item.tax_rate/2}%"
            sgst_display = f"{sgst:.2f} @{item.tax_rate/2}%"
        
        item_total = item.amount + cgst + sgst + igst
        
        items_data.append([
            item.description,
            '85044090',  # Default HSN code
            f"{item.quantity:.2f}",
            f"{item.unit_price:.2f}",
            "0.00",
            f"{item.amount:.2f}",
            cgst_display,
            sgst_display,
            "0.00",
            f"{item_total:.2f}"
        ])
        
        total_taxable += item.amount
        total_cgst += cgst
        total_sgst += sgst
        total_cess += 0
        total_amount += item_total
    
    # Add totals row
    items_data.append([
        'Total', '', '', '', '', 
        f"{total_taxable:.2f}", 
        f"{total_cgst:.2f}", 
        f"{total_sgst:.2f}", 
        f"{total_cess:.2f}", 
        f"{total_amount:.2f}"
    ])
    
    items_table = Table(items_data, colWidths=[1.2*inch, 0.6*inch, 0.5*inch, 0.7*inch, 0.5*inch, 0.7*inch, 0.7*inch, 0.7*inch, 0.5*inch, 0.7*inch])
    items_table.setStyle(TableStyle([
        # Header row styling
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#fff9c4')),  # Light yellow header
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
        ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 7),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 6),
        
        # Data rows styling - YELLOW BACKGROUND like your reference
        ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#fff9c4')),  # Light yellow rows
        ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
        ('ALIGN', (0, 1), (0, -1), 'LEFT'),  # Item description left aligned
        ('ALIGN', (1, 1), (-1, -1), 'CENTER'),  # Numbers center aligned
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -1), 6),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('LEFTPADDING', (0, 0), (-1, -1), 3),
        ('RIGHTPADDING', (0, 0), (-1, -1), 3),
        ('TOPPADDING', (0, 0), (-1, -1), 3),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
        
        # Total row styling
        ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, -1), (-1, -1), 7),
    ]))
    
    story.append(items_table)
    story.append(Spacer(1, 4))
    
    # Summary section - right aligned
    summary_data = [
        ['', 'Taxable Amount', f"₹ {total_taxable:.2f}"],
        ['', 'Total Tax', f"₹ {total_cgst + total_sgst:.2f}"],
        ['', 'Total Value', f"₹ {total_amount:.2f}"]
    ]
    
    summary_table = Table(summary_data, colWidths=[3.5*inch, 1.2*inch, 1.3*inch])
    summary_table.setStyle(TableStyle([
        ('ALIGN', (1, 0), (2, -1), 'RIGHT'),
        ('FONTNAME', (1, 0), (1, -1), 'Helvetica-Bold'),
        ('FONTNAME', (2, 0), (2, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (1, 0), (2, -1), 8),
        ('TEXTCOLOR', (2, -1), (2, -1), colors.HexColor('#d32f2f')),  # Red for total
        ('FONTSIZE', (2, -1), (2, -1), 10),  # Larger font for total
        ('LEFTPADDING', (1, 0), (2, -1), 4),
        ('RIGHTPADDING', (1, 0), (2, -1), 4),
        ('TOPPADDING', (1, 0), (2, -1), 2),
        ('BOTTOMPADDING', (1, 0), (2, -1), 2),
    ]))
    
    story.append(summary_table)
    story.append(Spacer(1, 2))
    
    # Amount in words
    amount_words = number_to_words(int(total_amount))
    story.append(Paragraph(f"<b>Total amount (in words):</b> {amount_words}", normal_style))
    story.append(Spacer(1, 3))
    
    # Bank details with red border
    bank_data = [
        ['Bank Details:', ''],
        ['Account Number:', company_details['bank_details']['account_number']],
        ['IFSC:', company_details['bank_details']['ifsc']],
        ['Bank Name:', company_details['bank_details']['bank_name']],
        ['Branch Name:', company_details['bank_details']['branch_name']]
    ]
    
    bank_table = Table(bank_data, colWidths=[1.2*inch, 1.8*inch])
    bank_table.setStyle(TableStyle([
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 7),
        ('GRID', (0, 1), (-1, -1), 1, colors.HexColor('#d32f2f')),  # Red border
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#d32f2f')),  # Red header
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('BACKGROUND', (0, 1), (-1, -1), colors.white),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('LEFTPADDING', (0, 0), (-1, -1), 4),
        ('RIGHTPADDING', (0, 0), (-1, -1), 4),
        ('TOPPADDING', (0, 0), (-1, -1), 3),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
    ]))
    
    story.append(bank_table)
    story.append(Spacer(1, 3))
    
    # Terms & Conditions and Signatory in one row - EXACT from reference
    footer_data = []
    
    # Left side - Terms & Conditions
    left_footer = []
    terms_text = """
    <b>CERTIFIED THAT THE PARTICULARS GIVEN ABOVE ARE TRUE AND CORRECT. WE ALSO DECLARE THAT WE WILL REMIT THE GST AMOUNT AND FILE APPLICABLE GST RETURNS</b><br/><br/>
    
    <b>Branch Office:</b><br/>
    #16, 2nd floor, A-Pravesh "A"<br/>
    19th street, Annai Therasa Nagar,<br/>
    Puzhuthivakkam, Chennai-600091<br/>
    Email: mahadevico@yahoo.in, mahadevico77@gmail.com<br/><br/>
    
    <b>Payment:</b> 100% Against supply Immediate.<br/>
    <b>Warranty:</b> 12 Month From the date of Supply.<br/>
    <b>Only For:</b> Ac Drive, PLC, Servo Drive & Servo Motors
    """
    left_footer.append(Paragraph(terms_text, normal_style))
    
    # Right side - Signatory
    right_footer = []
    right_footer.append(Spacer(1, 0.2*inch))
    right_footer.append(Paragraph("<b>For MAHADEVI&CO</b>", normal_style))
    right_footer.append(Paragraph("_____________________", normal_style))
    right_footer.append(Paragraph("Authorised Signatory", normal_style))
    
    footer_table = Table([left_footer, right_footer], colWidths=[4*inch, 2*inch])
    footer_table.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('LEFTPADDING', (0, 0), (-1, -1), 0),
        ('RIGHTPADDING', (0, 0), (-1, -1), 0),
    ]))
    
    story.append(footer_table)
    
    # Build PDF
    doc.build(story)
    
    # Get PDF content
    pdf_content = buffer.getvalue()
    buffer.close()
    
    # Create response
    response = make_response(pdf_content)
    response.headers['Content-Type'] = 'application/pdf'
    response.headers['Content-Disposition'] = f'inline; filename=invoice_{invoice.invoice_number}.pdf'
    
    return response

# Purchase Order Routes
@app.route('/purchase-orders')
@login_required
def purchase_orders():
    # Default sort by PO number descending
    # Eager-load vendor to avoid N+1 and reduce latency
    purchase_orders = PurchaseOrder.query.options(db.joinedload(PurchaseOrder.vendor)).order_by(PurchaseOrder.po_number.desc()).all()
    return render_template('purchase_orders.html', purchase_orders=purchase_orders)

@app.route('/purchase-orders/create', methods=['GET', 'POST'])
@login_required
def create_purchase_order():
    form = PurchaseOrderForm()
    form.vendor_id.choices = [(v.id, f"{v.name} - {v.city}, {v.state}") for v in Vendor.query.order_by(Vendor.name, Vendor.city).all()]
    # Populate signature choices for PO
    user_signatures = UserSignature.query.filter_by(user_id=current_user.id).order_by(UserSignature.is_default.desc(), UserSignature.created_at.desc()).all()
    signature_choices = [(sig.id, f"{sig.signature_name}{' (Default)' if sig.is_default else ''}") for sig in user_signatures]
    signature_choices.insert(0, ('', 'No Signature'))
    form.selected_signature.choices = signature_choices
    
    # Generate next PO number for display (starting fresh from 001)
    business_year = 2526
    
    # Find the highest sequential number that follows the new format (001, 002, 003...)
    existing_pos = PurchaseOrder.query.filter(
        PurchaseOrder.po_number.like(f'MD{business_year}-PO-%')
    ).all()
    
    # Look for POs with 3-digit sequential format (001, 002, 003...)
    sequential_numbers = []
    for po in existing_pos:
        try:
            number_part = po.po_number.split('-')[-1]
            if number_part.isdigit() and len(number_part) == 3:
                sequential_numbers.append(int(number_part))
        except (IndexError, ValueError):
            continue
    
    if sequential_numbers:
        next_number = max(sequential_numbers) + 1
    else:
        next_number = 1
    
    next_po_number = f"MD{business_year}-PO-{next_number:03d}"
    
    # Set default dates to current date (HTML5 date format: YYYY-MM-DD)
    if request.method == 'GET':
        current_date = datetime.now().strftime('%Y-%m-%d')
        form.po_date.data = current_date
        # Set delivery date to 30 days from today
        delivery_date = datetime.now() + timedelta(days=30)
        form.delivery_date.data = delivery_date.strftime('%Y-%m-%d')
        # Set expected delivery date to 15 days from today
        expected_delivery_date = datetime.now() + timedelta(days=15)
        form.expected_delivery_date.data = expected_delivery_date.strftime('%Y-%m-%d')
        # Set the suggested PO number
        form.po_number.data = next_po_number
    
    if form.validate_on_submit():
        # Use the PO number from the form (user can edit it)
        po_number = form.po_number.data.strip()
        
        # Check if PO number already exists
        existing_po = PurchaseOrder.query.filter_by(po_number=po_number).first()
        if existing_po:
            flash(f'PO number "{po_number}" already exists. Please use a different number.', 'error')
            return render_template('create_purchase_order.html', form=form, next_po_number=next_po_number)
        
        # Parse dates - handle both YYYY-MM-DD (HTML5 date input) and DD/MM/YYYY formats
        try:
            # Try HTML5 date format first (YYYY-MM-DD)
            po_date = datetime.strptime(form.po_date.data, '%Y-%m-%d').date()
        except ValueError:
            # Fall back to DD/MM/YYYY format
            po_date = datetime.strptime(form.po_date.data, '%d/%m/%Y').date()
        
        try:
            delivery_date = datetime.strptime(form.delivery_date.data, '%Y-%m-%d').date() if form.delivery_date.data else None
        except ValueError:
            delivery_date = datetime.strptime(form.delivery_date.data, '%d/%m/%Y').date() if form.delivery_date.data else None
        
        try:
            expected_delivery_date = datetime.strptime(form.expected_delivery_date.data, '%Y-%m-%d').date() if form.expected_delivery_date.data else None
        except ValueError:
            expected_delivery_date = datetime.strptime(form.expected_delivery_date.data, '%d/%m/%Y').date() if form.expected_delivery_date.data else None
        
        # Get company (assuming single company setup)
        company = Company.query.first()
        if not company:
            flash('Company details not found. Please set up company information first.', 'error')
            return redirect(url_for('company'))
        
        # Create purchase order (will be updated with items and totals)
        # Handle signature selection (allow empty for no signature)
        selected_signature_id = None
        if form.selected_signature.data and form.selected_signature.data != '':
            try:
                selected_signature_id = int(form.selected_signature.data)
            except (ValueError, TypeError):
                selected_signature_id = None

        po = PurchaseOrder(
            po_number=po_number,
            vendor_id=form.vendor_id.data,
            company_id=company.id,
            po_date=po_date,
            delivery_date=delivery_date,
            expected_delivery_date=expected_delivery_date,
            reference_no=form.reference_no.data or '-',
            place_of_supply=form.place_of_supply.data or '33',
            shipping_charges=form.shipping_charges.data or 0,
            terms_conditions=form.terms_conditions.data or 'Payment: 45 Days from the date of invoice. Delivery: Immediate / One week. Freight: Inclusive',
            payment_terms=form.payment_terms.data or 'Make all checks payable to MAHADEVI&CO.',
            notes=((('Delivery: ' + form.delivery.data + '\n') if hasattr(form, 'delivery') and form.delivery.data else '') + (form.notes.data or '')),
            extra_billing_info=form.extra_billing_info.data,
            main_address=form.main_address.data,
            branch_address=form.branch_address.data,
            selected_signature_id=selected_signature_id,
            subtotal=0,
            total_amount=0
        )
        
        db.session.add(po)
        db.session.commit()
        
        # Log activity
        log_activity(
            action_type='create',
            entity_type='purchase_order',
            entity_id=po.id,
            resource_identifier=po.po_number,
            description=f"Created purchase order: {po.po_number}"
        )
        
        # Send email notification
        # Notifications disabled
        
        flash('Purchase Order created! Now add items to complete it.', 'success')
        return redirect(url_for('edit_purchase_order', po_id=po.id))
    
    return render_template('create_purchase_order.html', form=form, next_po_number=next_po_number)

@app.route('/purchase-orders/<int:po_id>')
@login_required
def view_purchase_order(po_id):
    po = PurchaseOrder.query.get_or_404(po_id)
    return render_template('view_purchase_order.html', po=po)

@app.route('/purchase-orders/<int:po_id>/edit')
@login_required
def edit_purchase_order(po_id):
    po = PurchaseOrder.query.get_or_404(po_id)
    
    # Convert items to JSON-serializable format
    items_data = []
    for item in po.items:
        items_data.append({
            'id': item.id,
            'description': item.description,
            'quantity': float(item.quantity),
            'unit_price': float(item.unit_price),
            'tax_rate': float(item.tax_rate),
            'amount': float(item.amount),
            'hsn_code': item.hsn_code
        })
    
    return render_template('edit_purchase_order.html', po=po, items_json=json.dumps(items_data))

@app.route('/purchase-orders/<int:po_id>/print')
@login_required
def purchase_order_print(po_id):
    """Render an HTML print view that matches the reference purchase order and prints to A4."""
    try:
        po = PurchaseOrder.query.get_or_404(po_id)
        company = Company.query.first()
        
        # Validate PO has items
        if not po.items:
            flash('Cannot print purchase order with no items. Please add items first.', 'error')
            return redirect(url_for('edit_purchase_order', po_id=po_id))
        
        # Validate company exists
        if not company:
            flash('Company details not found. Please set up company information first.', 'error')
            return redirect(url_for('company'))
        
        if not po.vendor:
            flash('Vendor information not found for this purchase order.', 'error')
            return redirect(url_for('purchase_orders'))
        
        logo_path = url_for('static', filename='uploads/md_logo.jpg')
        
        # Get company business details
        try:
            company_details = get_company_details()
        except Exception as company_error:
            flash(f'Error getting company details: {str(company_error)}', 'error')
            company_details = get_company_details()  # Fallback
        
        # Calculate item-level details for accurate display
        from decimal import Decimal
        
        # Get company state from GSTIN
        if not company_details['gstin']:
            flash('Company GSTIN is missing. Please update company details with GSTIN.', 'error')
            return redirect(url_for('edit_purchase_order', po_id=po_id))
        
        company_state = get_state_from_gstin(company_details['gstin'])
        
        # Validate vendor GSTIN
        if not po.vendor:
            flash('Vendor information is missing for this purchase order.', 'error')
            return redirect(url_for('edit_purchase_order', po_id=po_id))
        
        if not po.vendor.gstin:
            flash('Vendor GSTIN is missing. Please update vendor details with GSTIN.', 'error')
            return redirect(url_for('edit_purchase_order', po_id=po_id))
        
        vendor_state = get_state_from_gstin(po.vendor.gstin)
        is_interstate = vendor_state != company_state
        
        # Calculate item details
        item_details = []
        if not po.items or len(po.items) == 0:
            flash('Purchase order has no items to calculate. Please add items first.', 'error')
            return redirect(url_for('edit_purchase_order', po_id=po_id))
            
        for item in po.items:
            try:
                # Validate item data
                if not item or not hasattr(item, 'amount') or not hasattr(item, 'tax_rate'):
                    flash(f'Invalid item data for item {item.id if item else "unknown"}', 'error')
                    continue
                
                # Calculate item-level discount using the same logic as our fixed functions
                gross_amount = Decimal(str(item.quantity)) * Decimal(str(item.unit_price))
                
                # Validate and calculate discount amount using our fixed validation
                validated_discount_value = validate_discount_value(item.discount_type, item.discount_value, gross_amount)
                
                if item.discount_type == 'percentage' and validated_discount_value > 0:
                    item_discount = gross_amount * validated_discount_value / Decimal('100')
                elif item.discount_type == 'amount' and validated_discount_value > 0:
                    item_discount = validated_discount_value
                else:
                    item_discount = Decimal('0')
                
                # Calculate taxable amount for this item (recalculate instead of using stored amount)
                item_taxable = max(gross_amount - item_discount, Decimal('0'))
                
                # Calculate tax for this item
                cgst, sgst, igst = calculate_gst(item_taxable, item.tax_rate, is_interstate)
                
                # Calculate total for this item
                item_total = item_taxable + cgst + sgst + igst
                
                item_details.append({
                    'item': item,
                    'discount': float(item_discount),
                    'taxable': float(item_taxable),
                    'cgst': float(cgst),
                    'sgst': float(sgst),
                    'igst': float(igst),
                    'total': float(item_total)
                })
            except Exception as item_error:
                flash(f'Error calculating item details for item {item.id if item else "unknown"}: {str(item_error)}', 'error')
                raise
        
        # Final validation
        if not item_details or len(item_details) == 0:
            flash('No valid items found for calculation. Please check your purchase order items.', 'error')
            return redirect(url_for('edit_purchase_order', po_id=po_id))
        
        # Vendor state already calculated above

        # Extract delivery text from notes (prefixed as "Delivery: ...")
        delivery_text = ''
        try:
            if po.notes:
                for line in str(po.notes).splitlines():
                    if line.strip().lower().startswith('delivery:'):
                        delivery_text = line.split(':', 1)[1].strip()
                        break
        except Exception:
            delivery_text = ''

        # Determine signature for PO - only if explicitly selected; else none
        signature_data = po.selected_signature.signature_data if po.selected_signature else None

        return render_template('print_purchase_order.html', 
                             po=po, 
                             company=company, 
                             logo_path=logo_path, 
                             float=float, 
                             number_to_words=number_to_words,
                             item_details=item_details,
                             is_interstate=is_interstate,
                             vendor_state=vendor_state,
                             company_details=company_details,
                             delivery_text=delivery_text,
                             signature_data=signature_data)
    
    except Exception as e:
        flash(f'Error generating print view: {str(e)}', 'error')
        return redirect(url_for('purchase_orders'))

# Purchase Order API Routes
@app.route('/api/purchase-orders/<int:po_id>/items', methods=['POST'])
@login_required
def add_purchase_order_item(po_id):
    po = PurchaseOrder.query.get_or_404(po_id)
    
    data = request.get_json()
    description = data.get('description')
    hsn_code = data.get('hsn_code', '85044090')
    
    from decimal import Decimal
    quantity = Decimal(str(data.get('quantity', 0)))
    unit_price = Decimal(str(data.get('unit_price', 0)))
    tax_rate = Decimal(str(data.get('tax_rate', 18)))
    discount_type = data.get('discount_type', 'amount')
    discount_value = Decimal(str(data.get('discount_value', 0)))
    
    if not description or quantity <= 0 or unit_price <= 0:
        return jsonify({'error': 'Invalid item data'}), 400
    
    # Calculate amount with discount using proper validation and precision
    gross_amount = quantity * unit_price
    
    # Validate and calculate discount amount using our fixed validation
    validated_discount_value = validate_discount_value(discount_type, discount_value, gross_amount)
    
    if discount_type == 'percentage' and validated_discount_value > 0:
        discount_amount = gross_amount * validated_discount_value / Decimal('100')
    elif discount_type == 'amount' and validated_discount_value > 0:
        discount_amount = validated_discount_value
    else:
        discount_amount = Decimal('0')
    
    # Round discount amount to 2 decimal places
    from decimal import ROUND_HALF_UP
    discount_amount = discount_amount.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
    
    # Calculate final amount and ensure it's not negative
    amount = max(gross_amount - discount_amount, Decimal('0'))
    amount = amount.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
    
    # Create new purchase order item
    item = PurchaseOrderItem(
        po_id=po_id,
        description=description,
        hsn_code=hsn_code,
        quantity=quantity,
        unit_price=unit_price,
        discount_type=discount_type,
        discount_value=validated_discount_value,  # FIXED: Store validated value, not original
        tax_rate=tax_rate,
        amount=amount
    )
    
    db.session.add(item)
    
    # Update purchase order totals
    update_purchase_order_totals(po)
    
    db.session.commit()
    
    # Log activity
    log_activity(
        action_type='add_item',
        entity_type='purchase_order',
        entity_id=po.id,
        resource_identifier=po.po_number,
        description=f"Added item to PO {po.po_number}: {description} (Qty: {quantity})"
    )
    
    return jsonify({
        'success': True,
        'item': {
            'id': item.id,
            'description': item.description,
            'hsn_code': item.hsn_code,
            'quantity': float(item.quantity),
            'unit_price': float(item.unit_price),
            'tax_rate': float(item.tax_rate),
            'discount_type': item.discount_type,
            'discount_value': float(item.discount_value),
            'amount': float(item.amount)
        }
    })

@app.route('/api/purchase-orders/<int:po_id>/items/<int:item_id>', methods=['DELETE'])
@login_required
def delete_purchase_order_item(po_id, item_id):
    po = PurchaseOrder.query.get_or_404(po_id)
    item = PurchaseOrderItem.query.filter_by(id=item_id, po_id=po_id).first_or_404()
    
    db.session.delete(item)
    
    # Update purchase order totals
    update_purchase_order_totals(po)
    
    db.session.commit()
    
    # Log activity
    log_activity(
        action_type='remove_item',
        entity_type='purchase_order',
        entity_id=po.id,
        resource_identifier=po.po_number,
        description=f"Removed item from PO {po.po_number}: {item.description}"
    )
    
    return jsonify({'success': True})

@app.route('/api/purchase-orders/<int:po_id>/items/<int:item_id>', methods=['PUT'])
@login_required
def update_purchase_order_item(po_id, item_id):
    po = PurchaseOrder.query.get_or_404(po_id)
    item = PurchaseOrderItem.query.filter_by(id=item_id, po_id=po_id).first_or_404()
    
    data = request.get_json()
    
    # Update item fields
    item.description = data.get('description', item.description)
    item.hsn_code = data.get('hsn_code', item.hsn_code)
    item.quantity = Decimal(str(data.get('quantity', item.quantity)))
    item.unit_price = Decimal(str(data.get('unit_price', item.unit_price)))
    item.tax_rate = Decimal(str(data.get('tax_rate', item.tax_rate)))
    item.discount_type = data.get('discount_type', item.discount_type)
    item.discount_value = Decimal(str(data.get('discount_value', item.discount_value)))
    
    # Recalculate amount with discount using proper Decimal arithmetic
    from decimal import Decimal
    gross_amount = Decimal(str(item.quantity)) * Decimal(str(item.unit_price))
    
    # Validate and calculate discount amount
    validated_discount_value = validate_discount_value(item.discount_type, item.discount_value, gross_amount)
    
    if item.discount_type == 'percentage' and validated_discount_value > 0:
        discount_amount = gross_amount * validated_discount_value / Decimal('100')
    elif item.discount_type == 'amount' and validated_discount_value > 0:
        discount_amount = validated_discount_value
    else:
        discount_amount = Decimal('0')
    
    # Calculate final amount after discount (ensure it's not negative)
    final_amount = gross_amount - discount_amount
    item.amount = max(final_amount, Decimal('0'))
    
    # FIXED: Update the discount_value with validated value
    item.discount_value = validated_discount_value
    
    # Update purchase order totals
    update_purchase_order_totals(po)
    
    db.session.commit()
    
    # Log activity
    log_activity(
        action_type='update_item',
        entity_type='purchase_order',
        entity_id=po.id,
        resource_identifier=po.po_number,
        description=f"Updated item in PO {po.po_number}: {item.description}"
    )
    
    return jsonify({
        'success': True,
        'item': {
            'id': item.id,
            'description': item.description,
            'hsn_code': item.hsn_code,
            'quantity': float(item.quantity),
            'unit_price': float(item.unit_price),
            'tax_rate': float(item.tax_rate),
            'discount_type': item.discount_type,
            'discount_value': float(item.discount_value),
            'amount': float(item.amount)
        }
    })

@app.route('/api/purchase-orders/<int:po_id>/status', methods=['POST'])
@login_required
def update_purchase_order_status(po_id):
    po = PurchaseOrder.query.get_or_404(po_id)
    
    data = request.get_json()
    status = data.get('status')
    
    if status not in ['pending', 'approved', 'received', 'cancelled']:
        return jsonify({'error': 'Invalid status'}), 400
    
    po.status = status
    db.session.commit()
    
    # Log activity
    log_activity(
        action_type='update_status',
        entity_type='purchase_order',
        entity_id=po.id,
        resource_identifier=po.po_number,
        description=f"Changed PO {po.po_number} status to: {status}"
    )
    
    return jsonify({'success': True, 'status': status})

@app.route('/api/purchase-orders/<int:po_id>/settings', methods=['POST'])
@login_required
def update_purchase_order_settings(po_id):
    po = PurchaseOrder.query.get_or_404(po_id)
    
    data = request.get_json()
    from decimal import Decimal
    shipping_charges = Decimal(str(data.get('shipping_charges', 0)))
    
    po.shipping_charges = shipping_charges
    po.reference_no = data.get('reference_no', '-')
    po.place_of_supply = data.get('place_of_supply', '33')
    po.terms_conditions = data.get('terms_conditions', 'Payment: 45 Days from the date of invoice. Delivery: Immediate / One week. Freight: Inclusive')
    po.payment_terms = data.get('payment_terms', 'Make all checks payable to MAHADEVI&CO.')
    po.notes = data.get('notes', '')
    
    # Update purchase order totals
    update_purchase_order_totals(po)
    
    db.session.commit()
    
    # Log activity
    log_activity(
        action_type='update_settings',
        entity_type='purchase_order',
        entity_id=po.id,
        resource_identifier=po.po_number,
        description=f"Updated settings for PO {po.po_number}"
    )
    
    return jsonify({'success': True})

@app.route('/purchase-orders/<int:po_id>/delete', methods=['POST'])
@login_required
def delete_purchase_order(po_id):
    """Delete a purchase order"""
    po = PurchaseOrder.query.get_or_404(po_id)
    
    # Store PO details for email notification
    po_number = po.po_number
    user_name = current_user.username if current_user.is_authenticated else 'Unknown User'
    
    try:
        # Delete all PO items first
        for item in po.items:
            db.session.delete(item)
        
        # Delete the purchase order
        db.session.delete(po)
        db.session.commit()
        
        # Log activity
        log_activity(
            action_type='delete',
            entity_type='purchase_order',
            entity_id=None,
            resource_identifier=po_number,
            description=f"Deleted purchase order: {po_number}"
        )
        
        # Notifications disabled
        
        flash(f'Purchase Order {po_number} has been deleted successfully.', 'success')
        
    except Exception as e:
        db.session.rollback()
        flash(f'Error deleting purchase order: {str(e)}', 'error')
    
    return redirect(url_for('purchase_orders'))

@app.route('/purchase-orders/<int:po_id>/convert-to-invoice', methods=['GET', 'POST'])
@login_required
def convert_po_to_invoice(po_id):
    """Convert a purchase order to an invoice"""
    po = PurchaseOrder.query.get_or_404(po_id)
    
    def compose_address_block(name, address, city, state, pincode, phone=None, email=None):
        lines = [name] if name else []
        if address:
            lines.append(address.strip())
        location_line = ", ".join([part for part in [city, pincode] if part])
        if location_line:
            lines.append(location_line)
        if state:
            lines.append(f"{state}, India")
        if phone:
            lines.append(f"Ph: {phone}")
        if email:
            lines.append(email)
        return "\n".join([line for line in lines if line])

    default_to_block = compose_address_block(
        invoice.customer.name,
        invoice.customer.address,
        invoice.customer.city,
        invoice.customer.state,
        invoice.customer.pincode,
        invoice.customer.phone,
        invoice.customer.email
    )

    default_from_block = compose_address_block(
        company.name,
        company.address,
        company.city,
        company.state,
        company.pincode,
        company.phone,
        company.email
    )
    
    def compose_address_block(name, address, city, state, pincode, phone=None, email=None):
        lines = [name] if name else []
        if address:
            lines.append(address.strip())
        location_line = ", ".join([part for part in [city, pincode] if part])
        if location_line:
            lines.append(location_line)
        if state:
            lines.append(f"{state}, India")
        if phone:
            lines.append(f"Ph: {phone}")
        if email:
            lines.append(email)
        return "\n".join([line for line in lines if line])

    default_to_block = compose_address_block(
        invoice.customer.name,
        invoice.customer.address,
        invoice.customer.city,
        invoice.customer.state,
        invoice.customer.pincode,
        invoice.customer.phone,
        invoice.customer.email
    )

    default_from_block = compose_address_block(
        company.name,
        company.address,
        company.city,
        company.state,
        company.pincode,
        company.phone,
        company.email
    )

    if request.method == 'POST':
        # Generate next invoice number
        business_year = 2526
        existing_invoices = Invoice.query.filter(
            Invoice.invoice_number.like(f'MD{business_year}-%')
        ).all()
        
        sequential_numbers = []
        for invoice in existing_invoices:
            try:
                number_part = invoice.invoice_number.split('-')[-1]
                if number_part.isdigit() and len(number_part) == 3:
                    sequential_numbers.append(int(number_part))
            except (IndexError, ValueError):
                continue
        
        if sequential_numbers:
            next_number = max(sequential_numbers) + 1
        else:
            next_number = 1
        
        invoice_number = f"MD{business_year}-{next_number:03d}"
        
        # Get company
        company = Company.query.first()
        if not company:
            flash('Company details not found.', 'error')
            return redirect(url_for('view_purchase_order', po_id=po_id))
        
        # Create customer from vendor (or find existing)
        customer = Customer.query.filter_by(
            name=po.vendor.name,
            email=po.vendor.email
        ).first()
        
        if not customer:
            customer = Customer(
                name=po.vendor.name,
                gstin=po.vendor.gstin,
                address=po.vendor.address,
                city=po.vendor.city,
                state=po.vendor.state,
                pincode=po.vendor.pincode,
                phone=po.vendor.phone,
                email=po.vendor.email,
                contact_person=po.vendor.contact_person,
                payment_terms=po.vendor.payment_terms
            )
            db.session.add(customer)
            db.session.flush()  # Get the customer ID
        
        # Create invoice
        invoice = Invoice(
            invoice_number=invoice_number,
            customer_id=customer.id,
            company_id=company.id,
            invoice_date=po.po_date,
            due_date=po.delivery_date,
            subtotal=po.subtotal,
            cgst_amount=po.cgst_amount,
            sgst_amount=po.sgst_amount,
            igst_amount=po.igst_amount,
            shipping_charges=po.shipping_charges,
            total_amount=po.total_amount,
            status='unpaid',
            notes=f"Converted from PO: {po.po_number}",
            eway_bill=po.eway_bill,
            extra_billing_info=po.extra_billing_info,
            main_address=po.main_address,
            branch_address=po.branch_address
        )
        
        db.session.add(invoice)
        db.session.flush()  # Get the invoice ID
        
        # Copy items
        for po_item in po.items:
            invoice_item = InvoiceItem(
                invoice_id=invoice.id,
                description=po_item.description,
                hsn_code=po_item.hsn_code,
                quantity=po_item.quantity,
                unit_price=po_item.unit_price,
                discount_type=po_item.discount_type,
                discount_value=po_item.discount_value,
                tax_rate=po_item.tax_rate,
                amount=po_item.amount
            )
            db.session.add(invoice_item)
        
        # Update PO status
        po.status = 'completed'
        
        db.session.commit()
        
        flash(f'Purchase Order converted to Invoice {invoice_number} successfully!', 'success')
        return redirect(url_for('view_invoice', invoice_id=invoice.id))
    
    return render_template('convert_po_to_invoice.html', po=po)

@app.route('/api/purchase-orders/<int:po_id>/delivery', methods=['POST'])
@login_required
def update_delivery_status(po_id):
    """Update delivery status and actual delivery date"""
    po = PurchaseOrder.query.get_or_404(po_id)
    
    data = request.get_json()
    actual_delivery_date = data.get('actual_delivery_date')
    delivery_status = data.get('delivery_status', 'received')
    
    if actual_delivery_date:
        try:
            # Parse date (YYYY-MM-DD format)
            po.actual_delivery_date = datetime.strptime(actual_delivery_date, '%Y-%m-%d').date()
        except ValueError:
            return jsonify({'success': False, 'error': 'Invalid date format'})
    
    # Update status based on delivery
    if delivery_status == 'received':
        po.status = 'received'
    elif delivery_status == 'partially_received':
        po.status = 'partially_received'
    elif delivery_status == 'completed':
        po.status = 'completed'
    
    db.session.commit()
    
    return jsonify({
        'success': True, 
        'status': po.status,
        'actual_delivery_date': po.actual_delivery_date.strftime('%Y-%m-%d') if po.actual_delivery_date else None
    })

@app.route('/purchase-orders/delivery-tracking')
@login_required
def delivery_tracking():
    """Delivery tracking dashboard"""
    # Get POs with delivery dates
    pending_deliveries = PurchaseOrder.query.filter(
        PurchaseOrder.expected_delivery_date.isnot(None),
        PurchaseOrder.status.in_(['pending', 'approved', 'sent'])
    ).order_by(PurchaseOrder.expected_delivery_date.asc()).all()
    
    overdue_deliveries = PurchaseOrder.query.filter(
        PurchaseOrder.expected_delivery_date < datetime.now().date(),
        PurchaseOrder.status.in_(['pending', 'approved', 'sent'])
    ).order_by(PurchaseOrder.expected_delivery_date.asc()).all()
    
    recent_deliveries = PurchaseOrder.query.filter(
        PurchaseOrder.actual_delivery_date.isnot(None)
    ).order_by(PurchaseOrder.actual_delivery_date.desc()).limit(10).all()
    
    return render_template('delivery_tracking.html', 
                         pending_deliveries=pending_deliveries,
                         overdue_deliveries=overdue_deliveries,
                         recent_deliveries=recent_deliveries)

@app.route('/vendors/performance')
@login_required
def vendor_performance():
    """Vendor performance metrics dashboard"""
    vendors = Vendor.query.all()
    vendor_metrics = []
    
    for vendor in vendors:
        # Get all POs for this vendor
        pos = PurchaseOrder.query.filter_by(vendor_id=vendor.id).all()
        
        if not pos:
            continue
            
        # Calculate metrics
        total_pos = len(pos)
        total_amount = sum(po.total_amount for po in pos)
        avg_amount = total_amount / total_pos if total_pos > 0 else 0
        
        # Status breakdown
        status_counts = {}
        for po in pos:
            status_counts[po.status] = status_counts.get(po.status, 0) + 1
        
        # Delivery performance
        delivered_pos = [po for po in pos if po.actual_delivery_date]
        on_time_deliveries = 0
        late_deliveries = 0
        
        for po in delivered_pos:
            if po.expected_delivery_date and po.actual_delivery_date:
                if po.actual_delivery_date <= po.expected_delivery_date:
                    on_time_deliveries += 1
                else:
                    late_deliveries += 1
        
        delivery_performance = (on_time_deliveries / len(delivered_pos) * 100) if delivered_pos else 0
        
        # Recent activity (last 30 days)
        recent_pos = [po for po in pos if po.created_at >= datetime.now() - timedelta(days=30)]
        
        vendor_metrics.append({
            'vendor': vendor,
            'total_pos': total_pos,
            'total_amount': total_amount,
            'avg_amount': avg_amount,
            'status_counts': status_counts,
            'delivery_performance': delivery_performance,
            'on_time_deliveries': on_time_deliveries,
            'late_deliveries': late_deliveries,
            'recent_pos': len(recent_pos)
        })
    
    # Sort by total amount
    vendor_metrics.sort(key=lambda x: x['total_amount'], reverse=True)
    
    return render_template('vendor_performance.html', vendor_metrics=vendor_metrics)

@app.route('/api/purchase-orders/bulk-status', methods=['POST'])
@login_required
def bulk_update_po_status():
    """Bulk update PO status"""
    data = request.get_json()
    po_ids = data.get('po_ids', [])
    new_status = data.get('status')
    
    if not po_ids or not new_status:
        return jsonify({'success': False, 'error': 'Missing required data'})
    
    try:
        updated_count = 0
        for po_id in po_ids:
            po = PurchaseOrder.query.get(po_id)
            if po:
                po.status = new_status
                updated_count += 1
        
        db.session.commit()
        return jsonify({'success': True, 'updated_count': updated_count})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/purchase-orders/bulk-delete', methods=['POST'])
@login_required
def bulk_delete_pos():
    """Bulk delete purchase orders"""
    data = request.get_json()
    po_ids = data.get('po_ids', [])
    
    if not po_ids:
        return jsonify({'success': False, 'error': 'No POs selected'})
    
    try:
        deleted_count = 0
        for po_id in po_ids:
            po = PurchaseOrder.query.get(po_id)
            if po:
                # Delete all PO items first
                for item in po.items:
                    db.session.delete(item)
                db.session.delete(po)
                deleted_count += 1
        
        db.session.commit()
        return jsonify({'success': True, 'deleted_count': deleted_count})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)})

@app.route('/purchase-orders/bulk-operations')
@login_required
def bulk_operations():
    """Bulk operations page for purchase orders"""
    return render_template('bulk_operations.html')

@app.route('/api/purchase-orders/all')
@login_required
def get_all_purchase_orders():
    """Get all purchase orders for bulk operations"""
    pos = PurchaseOrder.query.order_by(PurchaseOrder.created_at.desc()).all()
    
    result = []
    for po in pos:
        result.append({
            'id': po.id,
            'po_number': po.po_number,
            'vendor_id': po.vendor_id,
            'vendor': {
                'id': po.vendor.id,
                'name': po.vendor.name
            },
            'po_date': po.po_date.isoformat(),
            'total_amount': float(po.total_amount),
            'status': po.status,
            'priority': po.priority,
            'po_type': po.po_type
        })
    
    return jsonify(result)

# Delivery Challan Routes
@app.route('/delivery-challans')
@login_required
def delivery_challans():
    # Default sort by challan number descending
    challans = DeliveryChallan.query.order_by(DeliveryChallan.challan_number.desc()).all()
    return render_template('delivery_challans.html', challans=challans)

@app.route('/delivery-challans/create', methods=['GET', 'POST'])
@login_required
def create_delivery_challan():
    form = DeliveryChallanForm()
    # Populate signature choices
    user_signatures = UserSignature.query.filter_by(user_id=current_user.id).order_by(UserSignature.is_default.desc(), UserSignature.created_at.desc()).all()
    signature_choices = [(sig.id, f"{sig.signature_name}{' (Default)' if sig.is_default else ''}") for sig in user_signatures]
    signature_choices.insert(0, ('', 'No Signature'))
    form.selected_signature.choices = signature_choices
    
    # Generate next challan number for display
    business_year = 2526
    
    # Find the highest sequential number
    existing_challans = DeliveryChallan.query.filter(
        DeliveryChallan.challan_number.like(f'MD{business_year}-CH-%')
    ).all()
    
    sequential_numbers = []
    for challan in existing_challans:
        try:
            number_part = challan.challan_number.split('-')[-1]
            if number_part.isdigit() and len(number_part) == 3:
                sequential_numbers.append(int(number_part))
        except (IndexError, ValueError):
            continue
    
    if sequential_numbers:
        next_number = max(sequential_numbers) + 1
    else:
        next_number = 1
    
    next_challan_number = f"MD{business_year}-CH-{next_number:03d}"
    
    # Set default dates to current date
    if request.method == 'GET':
        current_date = datetime.now().strftime('%Y-%m-%d')
        form.challan_date.data = current_date
        # Set delivery date to 30 days from today
        delivery_date = datetime.now() + timedelta(days=30)
        form.delivery_date.data = delivery_date.strftime('%Y-%m-%d')
        # Set expected delivery date to 15 days from today
        expected_delivery_date = datetime.now() + timedelta(days=15)
        form.expected_delivery_date.data = expected_delivery_date.strftime('%Y-%m-%d')
        # Set the suggested challan number
        form.challan_number.data = next_challan_number
    
    if form.validate_on_submit():
        # Use the challan number from the form (user can edit it)
        challan_number = form.challan_number.data.strip()
        
        # Check if challan number already exists
        existing_challan = DeliveryChallan.query.filter_by(challan_number=challan_number).first()
        if existing_challan:
            flash(f'Challan number "{challan_number}" already exists. Please use a different number.', 'error')
            return render_template('create_delivery_challan.html', form=form, next_challan_number=next_challan_number)
        
        # Parse dates
        try:
            challan_date = datetime.strptime(form.challan_date.data, '%Y-%m-%d').date()
        except ValueError:
            challan_date = datetime.strptime(form.challan_date.data, '%d/%m/%Y').date()
        
        try:
            delivery_date = datetime.strptime(form.delivery_date.data, '%Y-%m-%d').date() if form.delivery_date.data else None
        except ValueError:
            delivery_date = datetime.strptime(form.delivery_date.data, '%d/%m/%Y').date() if form.delivery_date.data else None
        
        try:
            expected_delivery_date = datetime.strptime(form.expected_delivery_date.data, '%Y-%m-%d').date() if form.expected_delivery_date.data else None
        except ValueError:
            expected_delivery_date = datetime.strptime(form.expected_delivery_date.data, '%d/%m/%Y').date() if form.expected_delivery_date.data else None
        
        # Get company
        company = Company.query.first()
        if not company:
            flash('Company details not found. Please set up company information first.', 'error')
            return redirect(url_for('company'))
        
        # Handle signature selection
        selected_signature_id = None
        if form.selected_signature.data and form.selected_signature.data != '':
            try:
                selected_signature_id = int(form.selected_signature.data)
            except (ValueError, TypeError):
                selected_signature_id = None

        challan = DeliveryChallan(
            challan_number=challan_number,
            consignee_name=form.consignee_name.data,
            consignee_details=form.consignee_details.data,
            consignee_address=form.consignee_address.data,
            company_id=company.id,
            challan_date=challan_date,
            delivery_date=delivery_date,
            expected_delivery_date=expected_delivery_date,
            reference_no=form.reference_no.data or '-',
            place_of_supply=form.place_of_supply.data or '33',
            shipping_charges=form.shipping_charges.data or 0,
            notes=((('Delivery: ' + form.delivery.data + '\n') if hasattr(form, 'delivery') and form.delivery.data else '') + (form.notes.data or '')),
            extra_billing_info=form.extra_billing_info.data,
            main_address=form.main_address.data,
            branch_address=form.branch_address.data,
            selected_signature_id=selected_signature_id,
            subtotal=0,
            total_amount=0
        )
        
        db.session.add(challan)
        db.session.commit()
        
        # Log activity
        log_activity(
            action_type='create',
            entity_type='delivery_challan',
            entity_id=challan.id,
            resource_identifier=challan.challan_number,
            description=f"Created delivery challan: {challan.challan_number}"
        )
        
        flash('Delivery Challan created! Now add items to complete it.', 'success')
        return redirect(url_for('edit_delivery_challan', challan_id=challan.id))
    
    return render_template('create_delivery_challan.html', form=form, next_challan_number=next_challan_number)

@app.route('/delivery-challans/<int:challan_id>')
@login_required
def view_delivery_challan(challan_id):
    challan = DeliveryChallan.query.get_or_404(challan_id)
    return render_template('view_delivery_challan.html', challan=challan)

@app.route('/delivery-challans/<int:challan_id>/edit')
@login_required
def edit_delivery_challan(challan_id):
    challan = DeliveryChallan.query.get_or_404(challan_id)
    
    # Convert items to JSON-serializable format
    items_data = []
    for item in challan.items:
        items_data.append({
            'id': item.id,
            'description': item.description,
            'quantity': float(item.quantity),
            'unit_price': float(item.unit_price),
            'tax_rate': float(item.tax_rate),
            'amount': float(item.amount),
            'hsn_code': item.hsn_code
        })
    
    return render_template('edit_delivery_challan.html', challan=challan, items_json=json.dumps(items_data))

@app.route('/delivery-challans/<int:challan_id>/print')
@login_required
def delivery_challan_print(challan_id):
    """Render an HTML print view for delivery challan."""
    try:
        challan = DeliveryChallan.query.get_or_404(challan_id)
        company = Company.query.first()
        
        # Validate challan has items
        if not challan.items:
            flash('Cannot print delivery challan with no items. Please add items first.', 'error')
            return redirect(url_for('edit_delivery_challan', challan_id=challan_id))
        
        # Validate company exists
        if not company:
            flash('Company details not found. Please set up company information first.', 'error')
            return redirect(url_for('company'))
        
        logo_path = url_for('static', filename='uploads/md_logo.jpg')
        
        # Get company business details
        try:
            company_details = get_company_details()
        except Exception as company_error:
            flash(f'Error getting company details: {str(company_error)}', 'error')
            company_details = get_company_details()
        
        # Calculate item-level details
        from decimal import Decimal
        
        # Get company state from GSTIN
        if not company_details['gstin']:
            flash('Company GSTIN is missing. Please update company details with GSTIN.', 'error')
            return redirect(url_for('edit_delivery_challan', challan_id=challan_id))
        
        company_state = get_state_from_gstin(company_details['gstin'])
        
        # For delivery challan, we'll use company state for both (no separate consignee GSTIN)
        is_interstate = False  # Default to intrastate
        
        # Calculate item details
        item_details = []
        if not challan.items or len(challan.items) == 0:
            flash('Delivery challan has no items to calculate. Please add items first.', 'error')
            return redirect(url_for('edit_delivery_challan', challan_id=challan_id))
            
        for item in challan.items:
            try:
                # Validate item data
                if not item or not hasattr(item, 'amount') or not hasattr(item, 'tax_rate'):
                    flash(f'Invalid item data for item {item.id if item else "unknown"}', 'error')
                    continue
                
                # Calculate item-level discount
                gross_amount = Decimal(str(item.quantity)) * Decimal(str(item.unit_price))
                
                # Validate and calculate discount amount
                validated_discount_value = validate_discount_value(item.discount_type, item.discount_value, gross_amount)
                
                if item.discount_type == 'percentage' and validated_discount_value > 0:
                    item_discount = gross_amount * validated_discount_value / Decimal('100')
                elif item.discount_type == 'amount' and validated_discount_value > 0:
                    item_discount = validated_discount_value
                else:
                    item_discount = Decimal('0')
                
                # Calculate taxable amount
                item_taxable = max(gross_amount - item_discount, Decimal('0'))
                
                # Calculate tax
                cgst, sgst, igst = calculate_gst(item_taxable, item.tax_rate, is_interstate)
                
                # Calculate total
                item_total = item_taxable + cgst + sgst + igst
                
                item_details.append({
                    'item': item,
                    'discount': float(item_discount),
                    'taxable': float(item_taxable),
                    'cgst': float(cgst),
                    'sgst': float(sgst),
                    'igst': float(igst),
                    'total': float(item_total)
                })
            except Exception as item_error:
                flash(f'Error calculating item details: {str(item_error)}', 'error')
                raise
        
        if not item_details or len(item_details) == 0:
            flash('No valid items found for calculation.', 'error')
            return redirect(url_for('edit_delivery_challan', challan_id=challan_id))
        
        # Extract delivery text from notes
        delivery_text = ''
        try:
            if challan.notes:
                for line in str(challan.notes).splitlines():
                    if line.strip().lower().startswith('delivery:'):
                        delivery_text = line.split(':', 1)[1].strip()
                        break
        except Exception:
            delivery_text = ''

        # Determine signature
        signature_data = challan.selected_signature.signature_data if challan.selected_signature else None

        return render_template('print_delivery_challan.html', 
                             challan=challan, 
                             company=company, 
                             logo_path=logo_path, 
                             float=float, 
                             number_to_words=number_to_words,
                             item_details=item_details,
                             is_interstate=is_interstate,
                             company_details=company_details,
                             delivery_text=delivery_text,
                             signature_data=signature_data)
    
    except Exception as e:
        flash(f'Error generating print view: {str(e)}', 'error')
        return redirect(url_for('delivery_challans'))

# Delivery Challan API Routes
@app.route('/api/delivery-challans/<int:challan_id>/items', methods=['POST'])
@login_required
def add_delivery_challan_item(challan_id):
    challan = DeliveryChallan.query.get_or_404(challan_id)
    
    data = request.get_json()
    description = data.get('description')
    hsn_code = data.get('hsn_code', '85044090')
    
    from decimal import Decimal
    
    quantity = Decimal(str(data.get('quantity', 0)))
    unit_price = Decimal(str(data.get('unit_price', 0)))
    tax_rate = Decimal(str(data.get('tax_rate', 18)))
    discount_type = data.get('discount_type', 'amount')
    discount_value = Decimal(str(data.get('discount_value', 0)))
    
    if not description:
        return jsonify({'error': 'Description is required'}), 400
    
    # Calculate discount
    gross_amount = quantity * unit_price
    validated_discount_value = validate_discount_value(discount_type, discount_value, gross_amount)
    
    if discount_type == 'percentage' and validated_discount_value > 0:
        discount_amount = gross_amount * validated_discount_value / Decimal('100')
    elif discount_type == 'amount' and validated_discount_value > 0:
        discount_amount = validated_discount_value
    else:
        discount_amount = Decimal('0')
    
    taxable = max(gross_amount - discount_amount, Decimal('0'))
    
    # Calculate GST (default to intrastate for delivery challan)
    cgst, sgst, igst = calculate_gst(taxable, tax_rate, False)
    
    amount = taxable + cgst + sgst + igst
    
    item = DeliveryChallanItem(
        challan_id=challan.id,
        description=description,
        hsn_code=hsn_code,
        quantity=quantity,
        unit_price=unit_price,
        discount_type=discount_type,
        discount_value=validated_discount_value,
        tax_rate=tax_rate,
        amount=amount
    )
    
    db.session.add(item)
    
    # Recalculate totals
    challan.subtotal = sum(Decimal(str(i.quantity)) * Decimal(str(i.unit_price)) - 
                           (Decimal(str(i.quantity)) * Decimal(str(i.unit_price)) * Decimal(str(i.discount_value)) / Decimal('100') if i.discount_type == 'percentage' and i.discount_value > 0 else Decimal(str(i.discount_value)) if i.discount_type == 'amount' and i.discount_value > 0 else Decimal('0'))
                           for i in challan.items)
    
    challan.cgst_amount = sum(calculate_gst(
        max(Decimal(str(i.quantity)) * Decimal(str(i.unit_price)) - 
            (Decimal(str(i.quantity)) * Decimal(str(i.unit_price)) * Decimal(str(i.discount_value)) / Decimal('100') if i.discount_type == 'percentage' and i.discount_value > 0 else Decimal(str(i.discount_value)) if i.discount_type == 'amount' and i.discount_value > 0 else Decimal('0')),
            Decimal('0')),
        i.tax_rate, False)[0] for i in challan.items)
    
    challan.sgst_amount = sum(calculate_gst(
        max(Decimal(str(i.quantity)) * Decimal(str(i.unit_price)) - 
            (Decimal(str(i.quantity)) * Decimal(str(i.unit_price)) * Decimal(str(i.discount_value)) / Decimal('100') if i.discount_type == 'percentage' and i.discount_value > 0 else Decimal(str(i.discount_value)) if i.discount_type == 'amount' and i.discount_value > 0 else Decimal('0')),
            Decimal('0')),
        i.tax_rate, False)[1] for i in challan.items)
    
    challan.total_amount = challan.subtotal + challan.cgst_amount + challan.sgst_amount + challan.shipping_charges
    
    db.session.commit()
    
    log_activity(
        action_type='add_item',
        entity_type='delivery_challan',
        entity_id=challan.id,
        resource_identifier=challan.challan_number,
        description=f"Added item to delivery challan {challan.challan_number}: {description}"
    )
    
    return jsonify({
        'success': True,
        'item': {
            'id': item.id,
            'description': item.description,
            'hsn_code': item.hsn_code,
            'quantity': float(item.quantity),
            'unit_price': float(item.unit_price),
            'tax_rate': float(item.tax_rate),
            'discount_type': item.discount_type,
            'discount_value': float(item.discount_value),
            'amount': float(item.amount)
        },
        'totals': {
            'subtotal': float(challan.subtotal),
            'cgst_amount': float(challan.cgst_amount),
            'sgst_amount': float(challan.sgst_amount),
            'total_amount': float(challan.total_amount)
        }
    })

@app.route('/api/delivery-challans/<int:challan_id>/items/<int:item_id>', methods=['DELETE'])
@login_required
def delete_delivery_challan_item(challan_id, item_id):
    challan = DeliveryChallan.query.get_or_404(challan_id)
    item = DeliveryChallanItem.query.get_or_404(item_id)
    
    if item.challan_id != challan.id:
        return jsonify({'error': 'Item does not belong to this challan'}), 400
    
    description = item.description
    db.session.delete(item)
    
    # Recalculate totals
    from decimal import Decimal
    challan.subtotal = sum(Decimal(str(i.quantity)) * Decimal(str(i.unit_price)) - 
                           (Decimal(str(i.quantity)) * Decimal(str(i.unit_price)) * Decimal(str(i.discount_value)) / Decimal('100') if i.discount_type == 'percentage' and i.discount_value > 0 else Decimal(str(i.discount_value)) if i.discount_type == 'amount' and i.discount_value > 0 else Decimal('0'))
                           for i in challan.items)
    
    challan.cgst_amount = sum(calculate_gst(
        max(Decimal(str(i.quantity)) * Decimal(str(i.unit_price)) - 
            (Decimal(str(i.quantity)) * Decimal(str(i.unit_price)) * Decimal(str(i.discount_value)) / Decimal('100') if i.discount_type == 'percentage' and i.discount_value > 0 else Decimal(str(i.discount_value)) if i.discount_type == 'amount' and i.discount_value > 0 else Decimal('0')),
            Decimal('0')),
        i.tax_rate, False)[0] for i in challan.items)
    
    challan.sgst_amount = sum(calculate_gst(
        max(Decimal(str(i.quantity)) * Decimal(str(i.unit_price)) - 
            (Decimal(str(i.quantity)) * Decimal(str(i.unit_price)) * Decimal(str(i.discount_value)) / Decimal('100') if i.discount_type == 'percentage' and i.discount_value > 0 else Decimal(str(i.discount_value)) if i.discount_type == 'amount' and i.discount_value > 0 else Decimal('0')),
            Decimal('0')),
        i.tax_rate, False)[1] for i in challan.items)
    
    challan.total_amount = challan.subtotal + challan.cgst_amount + challan.sgst_amount + challan.shipping_charges
    
    db.session.commit()
    
    log_activity(
        action_type='delete_item',
        entity_type='delivery_challan',
        entity_id=challan.id,
        resource_identifier=challan.challan_number,
        description=f"Deleted item from delivery challan {challan.challan_number}: {description}"
    )
    
    return jsonify({
        'success': True,
        'totals': {
            'subtotal': float(challan.subtotal),
            'cgst_amount': float(challan.cgst_amount),
            'sgst_amount': float(challan.sgst_amount),
            'total_amount': float(challan.total_amount)
        }
    })

@app.route('/api/delivery-challans/<int:challan_id>/items/<int:item_id>', methods=['PUT'])
@login_required
def update_delivery_challan_item(challan_id, item_id):
    challan = DeliveryChallan.query.get_or_404(challan_id)
    item = DeliveryChallanItem.query.get_or_404(item_id)
    
    if item.challan_id != challan.id:
        return jsonify({'error': 'Item does not belong to this challan'}), 400
    
    data = request.get_json()
    from decimal import Decimal
    
    item.description = data.get('description', item.description)
    item.hsn_code = data.get('hsn_code', item.hsn_code)
    item.quantity = Decimal(str(data.get('quantity', item.quantity)))
    item.unit_price = Decimal(str(data.get('unit_price', item.unit_price)))
    item.tax_rate = Decimal(str(data.get('tax_rate', item.tax_rate)))
    item.discount_type = data.get('discount_type', item.discount_type)
    item.discount_value = Decimal(str(data.get('discount_value', item.discount_value)))
    
    # Recalculate item amount
    gross_amount = item.quantity * item.unit_price
    validated_discount_value = validate_discount_value(item.discount_type, item.discount_value, gross_amount)
    
    if item.discount_type == 'percentage' and validated_discount_value > 0:
        discount_amount = gross_amount * validated_discount_value / Decimal('100')
    elif item.discount_type == 'amount' and validated_discount_value > 0:
        discount_amount = validated_discount_value
    else:
        discount_amount = Decimal('0')
    
    item.discount_value = validated_discount_value
    taxable = max(gross_amount - discount_amount, Decimal('0'))
    cgst, sgst, igst = calculate_gst(taxable, item.tax_rate, False)
    item.amount = taxable + cgst + sgst + igst
    
    # Recalculate challan totals
    challan.subtotal = sum(Decimal(str(i.quantity)) * Decimal(str(i.unit_price)) - 
                           (Decimal(str(i.quantity)) * Decimal(str(i.unit_price)) * Decimal(str(i.discount_value)) / Decimal('100') if i.discount_type == 'percentage' and i.discount_value > 0 else Decimal(str(i.discount_value)) if i.discount_type == 'amount' and i.discount_value > 0 else Decimal('0'))
                           for i in challan.items)
    
    challan.cgst_amount = sum(calculate_gst(
        max(Decimal(str(i.quantity)) * Decimal(str(i.unit_price)) - 
            (Decimal(str(i.quantity)) * Decimal(str(i.unit_price)) * Decimal(str(i.discount_value)) / Decimal('100') if i.discount_type == 'percentage' and i.discount_value > 0 else Decimal(str(i.discount_value)) if i.discount_type == 'amount' and i.discount_value > 0 else Decimal('0')),
            Decimal('0')),
        i.tax_rate, False)[0] for i in challan.items)
    
    challan.sgst_amount = sum(calculate_gst(
        max(Decimal(str(i.quantity)) * Decimal(str(i.unit_price)) - 
            (Decimal(str(i.quantity)) * Decimal(str(i.unit_price)) * Decimal(str(i.discount_value)) / Decimal('100') if i.discount_type == 'percentage' and i.discount_value > 0 else Decimal(str(i.discount_value)) if i.discount_type == 'amount' and i.discount_value > 0 else Decimal('0')),
            Decimal('0')),
        i.tax_rate, False)[1] for i in challan.items)
    
    challan.total_amount = challan.subtotal + challan.cgst_amount + challan.sgst_amount + challan.shipping_charges
    
    db.session.commit()
    
    log_activity(
        action_type='update_item',
        entity_type='delivery_challan',
        entity_id=challan.id,
        resource_identifier=challan.challan_number,
        description=f"Updated item in delivery challan {challan.challan_number}: {item.description}"
    )
    
    return jsonify({
        'success': True,
        'item': {
            'id': item.id,
            'description': item.description,
            'hsn_code': item.hsn_code,
            'quantity': float(item.quantity),
            'unit_price': float(item.unit_price),
            'tax_rate': float(item.tax_rate),
            'discount_type': item.discount_type,
            'discount_value': float(item.discount_value),
            'amount': float(item.amount)
        },
        'totals': {
            'subtotal': float(challan.subtotal),
            'cgst_amount': float(challan.cgst_amount),
            'sgst_amount': float(challan.sgst_amount),
            'total_amount': float(challan.total_amount)
        }
    })

@app.route('/api/delivery-challans/<int:challan_id>/settings', methods=['POST'])
@login_required
def update_delivery_challan_settings(challan_id):
    challan = DeliveryChallan.query.get_or_404(challan_id)
    
    data = request.get_json()
    from decimal import Decimal
    shipping_charges = Decimal(str(data.get('shipping_charges', 0)))
    
    challan.shipping_charges = shipping_charges
    challan.reference_no = data.get('reference_no', '-')
    challan.place_of_supply = data.get('place_of_supply', '33')
    challan.notes = data.get('notes', '')
    
    # Recalculate totals
    challan.total_amount = challan.subtotal + challan.cgst_amount + challan.sgst_amount + challan.shipping_charges
    
    db.session.commit()
    
    # Log activity
    log_activity(
        action_type='update_settings',
        entity_type='delivery_challan',
        entity_id=challan.id,
        resource_identifier=challan.challan_number,
        description=f"Updated settings for delivery challan {challan.challan_number}"
    )
    
    return jsonify({'success': True})

@app.route('/delivery-challans/<int:challan_id>/delete', methods=['POST'])
@login_required
def delete_delivery_challan(challan_id):
    challan = DeliveryChallan.query.get_or_404(challan_id)
    challan_number = challan.challan_number
    
    # Delete all items (cascade should handle this, but explicit for safety)
    for item in challan.items:
        db.session.delete(item)
    
    db.session.delete(challan)
    db.session.commit()
    
    # Log activity
    log_activity(
        action_type='delete',
        entity_type='delivery_challan',
        entity_id=challan_id,
        resource_identifier=challan_number,
        description=f"Deleted delivery challan: {challan_number}"
    )
    
    flash(f'Delivery Challan {challan_number} has been deleted.', 'success')
    return redirect(url_for('delivery_challans'))

@app.route('/admin/create-tables', methods=['GET', 'POST'])
@login_required
def create_tables():
    """Admin route to create missing database tables"""
    # Only allow admin users
    if current_user.role != 'admin':
        flash('Access denied. Admin privileges required.', 'error')
        return redirect(url_for('dashboard'))
    
    try:
        with app.app_context():
            db.create_all()
            flash('✅ Database tables created successfully!', 'success')
            return redirect(url_for('dashboard'))
    except Exception as e:
        flash(f'❌ Error creating tables: {str(e)}', 'error')
        return redirect(url_for('dashboard'))

@app.route('/api/vendors')
@login_required
def get_vendors_api():
    """Get all vendors for API"""
    vendors = Vendor.query.order_by(Vendor.name).all()
    
    result = []
    for vendor in vendors:
        result.append({
            'id': vendor.id,
            'name': vendor.name,
            'city': vendor.city,
            'state': vendor.state
        })
    
    return jsonify(result)

@app.route('/api/addresses')
@login_required
def get_all_addresses():
    """Get all addresses from customers and vendors for delivery challan"""
    customers = Customer.query.order_by(Customer.name).all()
    vendors = Vendor.query.order_by(Vendor.name).all()
    
    result = []
    
    # Add customers
    for customer in customers:
        result.append({
            'id': f'customer_{customer.id}',
            'type': 'Customer',
            'name': customer.name,
            'address': customer.address,
            'city': customer.city,
            'state': customer.state,
            'pincode': customer.pincode,
            'phone': customer.phone,
            'email': customer.email,
            'contact_person': None,
            'display': f"{customer.name} (Customer) - {customer.city}, {customer.state}"
        })
    
    # Add vendors
    for vendor in vendors:
        result.append({
            'id': f'vendor_{vendor.id}',
            'type': 'Vendor',
            'name': vendor.name,
            'address': vendor.address,
            'city': vendor.city,
            'state': vendor.state,
            'pincode': vendor.pincode,
            'phone': vendor.phone,
            'email': vendor.email,
            'contact_person': vendor.contact_person,
            'display': f"{vendor.name} (Vendor) - {vendor.city}, {vendor.state}"
        })
    
    return jsonify(result)

@app.route('/invoices/bulk-download')
@login_required
def bulk_download_invoices():
    """Bulk download invoices page"""
    return render_template('bulk_download_invoices.html')

@app.route('/api/invoices/bulk-download', methods=['POST'])
@login_required
def generate_bulk_invoice_download():
    """Generate bulk invoice download with preview support"""
    import zipfile
    import io
    from datetime import datetime, timedelta
    import tempfile
    import os
    
    data = request.get_json()
    
    # Check if this is a preview request
    preview_only = data.get('preview_only', False)
    
    if preview_only:
        # Handle preview request
        filter_type = data.get('filter_type', 'month')
        start_date = data.get('start_date')
        end_date = data.get('end_date')
        month = data.get('month')
        year = data.get('year', datetime.now().year)
        
        try:
            # Calculate date range based on filter type
            if filter_type == 'month' and month:
                start_date = datetime(year, month, 1).date()
                if month == 12:
                    end_date = datetime(year + 1, 1, 1).date() - timedelta(days=1)
                else:
                    end_date = datetime(year, month + 1, 1).date() - timedelta(days=1)
            elif filter_type == 'quarter':
                quarter = data.get('quarter', 1)
                start_month = (quarter - 1) * 3 + 1
                start_date = datetime(year, start_month, 1).date()
                end_month = start_month + 2
                if end_month > 12:
                    end_date = datetime(year + 1, 1, 1).date() - timedelta(days=1)
                else:
                    end_date = datetime(year, end_month + 1, 1).date() - timedelta(days=1)
            elif filter_type == 'year':
                start_date = datetime(year, 1, 1).date()
                end_date = datetime(year, 12, 31).date()
            elif filter_type == 'custom':
                if not start_date or not end_date:
                    return jsonify({'success': False, 'error': 'Start date and end date required for custom range'})
                start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
                end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
            elif filter_type == 'all':
                # Get all invoices without date filtering
                start_date = None
                end_date = None
            else:
                return jsonify({'success': False, 'error': 'Invalid filter type'})
            
            # Get invoices for preview
            if filter_type == 'all':
                invoices = Invoice.query.order_by(Invoice.invoice_date.desc()).all()
            else:
                invoices = Invoice.query.filter(
                    Invoice.invoice_date >= start_date,
                    Invoice.invoice_date <= end_date
                ).order_by(Invoice.invoice_date.desc()).all()
            
            # Convert to preview format
            preview_invoices = []
            for invoice in invoices:
                customer = Customer.query.get(invoice.customer_id)
                preview_invoices.append({
                    'id': invoice.id,
                    'invoice_number': invoice.invoice_number,
                    'invoice_date': invoice.invoice_date.isoformat(),
                    'customer_name': customer.name if customer else 'N/A',
                    'total_amount': float(invoice.total_amount),
                    'status': invoice.status
                })
            
            return jsonify({
                'success': True,
                'invoices': preview_invoices
            })
            
        except Exception as e:
            return jsonify({'success': False, 'error': str(e)})
    
    else:
        # Handle download request with selected invoice IDs
        selected_invoice_ids = data.get('selected_invoice_ids', [])
        
        if not selected_invoice_ids:
            return jsonify({'success': False, 'error': 'No invoices selected for download'})
        
        try:
            # Get selected invoices
            invoices = Invoice.query.filter(Invoice.id.in_(selected_invoice_ids)).all()
            
            if not invoices:
                return jsonify({'success': False, 'error': 'No valid invoices found'})
            
            # Create ZIP file in memory
            zip_buffer = io.BytesIO()
            
            with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
                pdf_count = 0
                for invoice in invoices:
                    try:
                        # Generate PDF for each invoice
                        pdf_content = generate_invoice_pdf(invoice.id)
                        if pdf_content:
                            filename = f"Invoice_{invoice.invoice_number}_{invoice.invoice_date.strftime('%Y%m%d')}.pdf"
                            zip_file.writestr(filename, pdf_content)
                            pdf_count += 1
                    except Exception as e:
                        print(f"Error generating PDF for invoice {invoice.id}: {str(e)}")
                        continue
            
            zip_buffer.seek(0)
            
            # Generate filename with timestamp
            filename = f"Selected_Invoices_{datetime.now().strftime('%Y%m%d_%H%M%S')}.zip"
            
            return jsonify({
                'success': True,
                'zip_data': base64.b64encode(zip_buffer.getvalue()).decode(),
                'filename': filename,
                'count': len(invoices)
            })
            
        except Exception as e:
            return jsonify({'success': False, 'error': str(e)})

def generate_invoice_pdf(invoice_id):
    """Generate PDF for a single invoice using HTML template (Railway-compatible)"""
    try:
        from generate_pdf_railway import generate_invoice_pdf_from_template
        
        # Get invoice data
        invoice = Invoice.query.get(invoice_id)
        if not invoice:
            return None
            
        company = Company.query.first()
        if not company:
            return None
        
        # Validate invoice has items
        if not invoice.items:
            return None
        
        # Validate invoice data
        try:
            validate_invoice_data(invoice)
        except ValueError:
            return None
        
        # Use HTML template-based PDF generation
        return generate_invoice_pdf_from_template(invoice, company)
        
    except Exception as e:
        print(f"Error generating PDF for invoice {invoice_id}: {str(e)}")
        return None

@app.route('/invoices/<int:invoice_id>/print')
@login_required
def invoice_print(invoice_id):
    """Render an HTML print view that matches the reference invoice and prints to A4.
    Users can use the browser's Print → Save as PDF for perfect pagination.
    """
    try:
        invoice = Invoice.query.get_or_404(invoice_id)
        company = Company.query.first()
        
        # Validate invoice has items
        if not invoice.items:
            flash('Cannot print invoice with no items. Please add items first.', 'error')
            return redirect(url_for('edit_invoice', invoice_id=invoice_id))
        
        # Additional validation for empty items list
        if len(invoice.items) == 0:
            flash('Invoice has no items. Please add at least one item before printing.', 'error')
            return redirect(url_for('edit_invoice', invoice_id=invoice_id))
        
        # Validate company exists
        if not company:
            flash('Company details not found. Please set up company information first.', 'error')
            return redirect(url_for('company'))
        
        if not invoice.customer:
            flash('Customer information not found for this invoice.', 'error')
            return redirect(url_for('invoices'))
        
        # Validate invoice data
        try:
            validate_invoice_data(invoice)
        except ValueError as e:
            flash(f'Invoice validation error: {str(e)}', 'error')
            return redirect(url_for('edit_invoice', invoice_id=invoice_id))
        
        logo_path = url_for('static', filename='uploads/md_logo.jpg')
        
        # Parse metadata from notes JSON
        meta = {}
        if invoice.notes:
            try:
                meta = json.loads(invoice.notes)
            except (json.JSONDecodeError, TypeError):
                # Fallback if notes is not JSON
                meta = {
                    'reference_no': '-',
                    'eway_bill': '-',
                    'terms_text': 'CERTIFIED THAT THE PARTICULARS GIVEN ABOVE ARE TRUE AND CORRECT. WE FURTHER DECLARE THAT WE SHALL REMIT THE APPLICABLE GST AMOUNT AND FILE THE CORRESPONDING GST RETURNS.',
                    'payment_text': 'Payment: 100% against supply, immediate.\nWarranty: 12 months from the date of supply.\nApplicable only for: AC drive, PLC, servo drive & servo motors.'
                }
        else:
            meta = {
                'reference_no': '-',
                'eway_bill': '-',
                'terms_text': 'CERTIFIED THAT THE PARTICULARS GIVEN ABOVE ARE TRUE AND CORRECT. WE FURTHER DECLARE THAT WE SHALL REMIT THE APPLICABLE GST AMOUNT AND FILE THE CORRESPONDING GST RETURNS.',
                'payment_text': 'Payment: 100% against supply, immediate.\nWarranty: 12 months from the date of supply.\nApplicable only for: AC drive, PLC, servo drive & servo motors.'
            }
        
        # Get address information with defensive programming
        try:
            addresses = get_company_addresses()
            main_address_key = meta.get('main_address', 'salem')
            branch_address_key = meta.get('branch_address', 'chennai')
            
            # Validate that the address keys exist
            if not addresses or main_address_key not in addresses:
                main_address_key = 'salem'
            if not addresses or branch_address_key not in addresses:
                branch_address_key = 'chennai'
                
            # Ensure we have valid addresses
            if not addresses:
                flash('Company address information not found. Please set up company addresses first.', 'error')
                return redirect(url_for('company'))
                
        except Exception as address_error:
            flash(f'Error getting address information: {str(address_error)}', 'error')
            return redirect(url_for('company'))
        
        # Get company business details
        try:
            company_details = get_company_details()
        except Exception as company_error:
            flash(f'Error getting company details: {str(company_error)}', 'error')
            company_details = get_company_details()  # Fallback
        
        # Calculate item-level details for accurate display
        from decimal import Decimal
        
        # Validate customer state
        if not invoice.customer:
            flash('Customer information is missing for this invoice.', 'error')
            return redirect(url_for('edit_invoice', invoice_id=invoice_id))
        
        # Get company state from GSTIN
        if not company_details['gstin']:
            flash('Company GSTIN is missing. Please update company details with GSTIN.', 'error')
            return redirect(url_for('edit_invoice', invoice_id=invoice_id))
        
        company_state = get_state_from_gstin(company_details['gstin'])
        
        # Get customer state from GSTIN
        if not invoice.customer.gstin:
            flash('Customer GSTIN is missing. Please update customer details with GSTIN.', 'error')
            return redirect(url_for('edit_invoice', invoice_id=invoice_id))
        
        customer_state = get_state_from_gstin(invoice.customer.gstin)
        is_interstate = customer_state != company_state
        
        # Calculate item details
        item_details = []
        if not invoice.items or len(invoice.items) == 0:
            flash('Invoice has no items to calculate. Please add items first.', 'error')
            return redirect(url_for('edit_invoice', invoice_id=invoice_id))
            
        for item in invoice.items:
            try:
                # Validate item data
                if not item or not hasattr(item, 'amount') or not hasattr(item, 'tax_rate'):
                    flash(f'Invalid item data for item {item.id if item else "unknown"}', 'error')
                    continue
                
                # Calculate item-level discount using the same logic as our fixed functions
                gross_amount = Decimal(str(item.quantity)) * Decimal(str(item.unit_price))
                
                # Validate and calculate discount amount using our fixed validation
                validated_discount_value = validate_discount_value(item.discount_type, item.discount_value, gross_amount)
                
                if item.discount_type == 'percentage' and validated_discount_value > 0:
                    item_discount = gross_amount * validated_discount_value / Decimal('100')
                elif item.discount_type == 'amount' and validated_discount_value > 0:
                    item_discount = validated_discount_value
                else:
                    item_discount = Decimal('0')
                
                # Calculate taxable amount for this item (recalculate instead of using stored amount)
                item_taxable = max(gross_amount - item_discount, Decimal('0'))
                
                # Calculate tax for this item
                cgst, sgst, igst = calculate_gst(item_taxable, item.tax_rate, is_interstate)
                
                # Calculate total for this item
                item_total = item_taxable + cgst + sgst + igst
                
                item_details.append({
                    'item': item,
                    'discount': float(item_discount),
                    'taxable': float(item_taxable),
                    'cgst': float(cgst),
                    'sgst': float(sgst),
                    'igst': float(igst),
                    'total': float(item_total)
                })
            except Exception as item_error:
                flash(f'Error calculating item details for item {item.id if item else "unknown"}: {str(item_error)}', 'error')
                raise
        
        # Final validation
        if not item_details or len(item_details) == 0:
            flash('No valid items found for calculation. Please check your invoice items.', 'error')
            return redirect(url_for('edit_invoice', invoice_id=invoice_id))
        
        # Get customer state from GSTIN
        try:
            customer_state = get_state_from_gstin(invoice.customer.gstin) if invoice.customer.gstin else "Unknown State"
        except Exception as state_error:
            flash(f'Error getting customer state: {str(state_error)}', 'error')
            customer_state = "Unknown State"
        
        # Generate QR code for payment
        qr_code = generate_payment_qr_code(invoice.total_amount, invoice.invoice_number, invoice.customer.name)
        
        # Get signature data - only if explicitly selected; else none
        signature_data = invoice.selected_signature.signature_data if invoice.selected_signature else None
        
        return render_template('print_invoice.html', 
                             invoice=invoice, 
                             company=company, 
                             logo_path=logo_path, 
                             meta=meta, 
                             float=float, 
                             number_to_words=number_to_words,
                             addresses=addresses,
                             main_address_key=main_address_key,
                             branch_address_key=branch_address_key,
                             item_details=item_details,
                             is_interstate=is_interstate,
                             customer_state=customer_state,
                             company_details=company_details,
                             qr_code=qr_code,
                             signature_data=signature_data)
    
    except Exception as e:
        try:
            import traceback
            app.logger.error('Error generating print view', exc_info=True)
            app.logger.error(traceback.format_exc())
        except Exception:
            pass
        flash(f'Error generating print view: {str(e)}', 'error')
        return redirect(url_for('invoices'))



 
@app.route('/invoices/<int:invoice_id>/delivery-challan', methods=['GET', 'POST'])
@login_required
def delivery_challan(invoice_id):
    """Generate delivery challan PDF with PO details"""
    invoice = Invoice.query.get_or_404(invoice_id)
    company = Company.query.first()
    
    if not company:
        flash('Company details not found. Please set up company information first.', 'error')
        return redirect(url_for('company'))
    
    def compose_address_block(name, address, city, state, pincode, phone=None, email=None):
        lines = [name] if name else []
        if address:
            lines.append(address.strip())
        location_line = ", ".join([part for part in [city, pincode] if part])
        if location_line:
            lines.append(location_line)
        if state:
            lines.append(f"{state}, India")
        if phone:
            lines.append(f"Ph: {phone}")
        if email:
            lines.append(email)
        return "\n".join([line for line in lines if line])

    default_to_block = compose_address_block(
        invoice.customer.name,
        invoice.customer.address,
        invoice.customer.city,
        invoice.customer.state,
        invoice.customer.pincode,
        invoice.customer.phone,
        invoice.customer.email
    )

    # Get company addresses for dropdown
    company_addresses = get_company_addresses()
    # Parse meta from invoice.notes (stored as JSON) with error handling
    try:
        meta = json.loads(invoice.notes) if invoice.notes else {}
    except (json.JSONDecodeError, TypeError):
        meta = {}
    main_address_key = meta.get('main_address', 'salem')
    company_address_info = company_addresses.get(main_address_key, company_addresses.get('salem', {}))
    
    default_from_block = compose_address_block(
        company_address_info.get('name', company.name),
        company_address_info.get('address', company.address).replace('<br>', '\n') if company_address_info.get('address') else company.address,
        company.city,
        get_state_from_gstin(company.gstin) if company.gstin else company.state,
        company.pincode,
        company_address_info.get('phone', company.phone),
        company_address_info.get('email', company.email)
    )

    # Build recipient catalog from customers and vendors (for dropdown)
    def build_recipient_option(record, recipient_type):
        if not record:
            return None
        option_value = f"{recipient_type}-{record.id}"
        safe_address = (record.address or '').strip()
        city_value = (record.city or '').strip()
        state_value = (record.state or '').strip()
        email_value = (record.email or '').strip()
        label_city = city_value or state_value
        address_lines = []
        if safe_address:
            for raw_line in re.split(r'[\r\n]+', safe_address):
                cleaned = raw_line.strip()
                if cleaned:
                    address_lines.append(cleaned)
        city_state = ", ".join([part for part in [record.city, record.state] if part])
        if record.pincode:
            if city_state:
                city_state = f"{city_state} - {record.pincode}"
            else:
                city_state = record.pincode
        if city_state:
            address_lines.append(city_state)
        contact_hint_parts = []
        if record.phone:
            contact_hint_parts.append(f"Ph: {record.phone}")
        if record.email:
            contact_hint_parts.append(f"Email: {record.email}")
        formatted_lines = [record.name] + address_lines + contact_hint_parts
        search_terms = [
            recipient_type.lower(),
            (record.name or '').lower(),
            city_value.lower(),
            state_value.lower(),
            safe_address.lower(),
            email_value.lower(),
            (record.phone or '').lower()
        ]
        return {
            'value': option_value,
            'label': f"{recipient_type.title()} • {record.name}" + (f" ({label_city})" if label_city else ""),
            'type': recipient_type.title(),
            'name': record.name,
            'address': safe_address,
            'city': city_value,
            'state': state_value,
            'pincode': record.pincode,
            'phone': record.phone,
            'email': email_value,
            'gstin': getattr(record, 'gstin', None),
            'formatted': "\n".join([line for line in formatted_lines if line]),
            'contact_hint': "\n".join(contact_hint_parts),
            'search_blob': " ".join([term for term in search_terms if term])
        }

    customer_records = Customer.query.order_by(Customer.name.asc()).all()
    vendor_records = Vendor.query.order_by(Vendor.name.asc()).all()

    recipient_options = []
    # Add current invoice customer as first option (pre-selected)
    current_customer_option = build_recipient_option(invoice.customer, 'customer')
    if current_customer_option:
        recipient_options.append(current_customer_option)
        current_customer_value = current_customer_option['value']
    else:
        current_customer_value = None
    
    # Add other customers and vendors
    for cust in customer_records:
        if cust.id != invoice.customer.id:  # Skip current customer (already added)
            option = build_recipient_option(cust, 'customer')
            if option:
                recipient_options.append(option)
    for vendor in vendor_records:
        option = build_recipient_option(vendor, 'vendor')
        if option:
            recipient_options.append(option)

    recipient_lookup = {opt['value']: opt for opt in recipient_options}

    if request.method == 'POST':
        # Get form data
        po_date_raw = request.form.get('po_date', '').strip()
        po_type = request.form.get('po_type', '').strip()
        dept = request.form.get('dept', '').strip()
        contact = request.form.get('contact', '').strip()
        try:
            num_products = int(request.form.get('num_products', 1))
            if num_products < 1:
                num_products = 1
            if num_products > 100:
                num_products = 100
        except (ValueError, TypeError):
            num_products = 1
        
        # Get address overrides - check dropdowns first, then textareas
        to_recipient_value = request.form.get('to_recipient', '').strip()
        to_override = request.form.get('to_override', '').strip()
        
        # If dropdown was selected and textarea is empty, use dropdown value
        if to_recipient_value and not to_override and recipient_lookup:
            selected_recipient = recipient_lookup.get(to_recipient_value)
            if selected_recipient and selected_recipient.get('formatted'):
                to_override = selected_recipient['formatted']
        
        # If still empty, use default
        if not to_override:
            to_override = default_to_block
        
        # Handle "From" address - check dropdown first
        from_address_key = request.form.get('from_address', '').strip()
        from_override = request.form.get('from_override', '').strip()
        
        # If dropdown was selected and textarea is empty, use dropdown value
        if from_address_key and not from_override:
            selected_company_info = company_addresses.get(from_address_key)
            if selected_company_info:
                from_lines = []
                if selected_company_info.get('name'):
                    from_lines.append(selected_company_info['name'])
                if selected_company_info.get('address'):
                    # Convert <br> to newlines
                    addr = selected_company_info['address'].replace('<br>', '\n').replace('<br/>', '\n').replace('<br />', '\n')
                    from_lines.extend([line.strip() for line in addr.split('\n') if line.strip()])
                if selected_company_info.get('phone'):
                    from_lines.append(selected_company_info['phone'])
                if selected_company_info.get('email'):
                    from_lines.append(selected_company_info['email'])
                from_override = '\n'.join(from_lines)
        
        # If still empty, use default
        if not from_override:
            from_override = default_from_block
        
        if not po_date_raw or num_products < 1:
            flash('Please fill in all required fields (Date and Number of Products).', 'error')
            form_data = request.form.to_dict()
            return render_template('delivery_challan_form.html',
                                   invoice=invoice,
                                   company=company,
                                   default_to_block=default_to_block,
                                   default_from_block=default_from_block,
                                   company_addresses=company_addresses,
                                   recipient_options=recipient_options,
                                   current_customer_value=current_customer_value,
                                   main_address_key=main_address_key,
                                   form_data=form_data)
        
        # Format date to DD.MM.YYYY format
        try:
            if po_date_raw:
                po_date_obj = datetime.strptime(po_date_raw, '%Y-%m-%d')
                po_date = po_date_obj.strftime('%d.%m.%Y')
            else:
                po_date = po_date_raw
        except:
            po_date = po_date_raw  # Use as-is if parsing fails
        
        # Generate PDF
        try:
            pdf_buffer = generate_delivery_challan_pdf(
                invoice=invoice,
                company=company,
                po_number='',  # Not used anymore
                po_date=po_date,
                po_type=po_type,
                dept=dept,
                contact=contact,
                num_products=num_products,
                to_override=to_override,
                from_override=from_override
            )
            
            # Return PDF as response
            response = make_response(pdf_buffer.getvalue())
            response.headers['Content-Type'] = 'application/pdf'
            # If print option is checked, add header to suggest printing
            auto_print = request.form.get('auto_print', '')
            if auto_print:
                response.headers['Content-Disposition'] = f'inline; filename=delivery_challan_{invoice.invoice_number}.pdf'
            else:
                response.headers['Content-Disposition'] = f'inline; filename=delivery_challan_{invoice.invoice_number}.pdf'
            return response
            
        except Exception as e:
            flash(f'Error generating delivery challan: {str(e)}', 'error')
            form_data = request.form.to_dict()
            return render_template('delivery_challan_form.html',
                                   invoice=invoice,
                                   company=company,
                                   default_to_block=default_to_block,
                                   default_from_block=default_from_block,
                                   company_addresses=company_addresses,
                                   recipient_options=recipient_options,
                                   current_customer_value=current_customer_value,
                                   main_address_key=main_address_key,
                                   form_data=form_data)
    
    # GET request - show form
    form_data = request.form.to_dict() if request.method == 'POST' else {}
    return render_template('delivery_challan_form.html',
                           invoice=invoice,
                           company=company,
                           default_to_block=default_to_block,
                           default_from_block=default_from_block,
                           company_addresses=company_addresses,
                           recipient_options=recipient_options,
                           current_customer_value=current_customer_value,
                           main_address_key=main_address_key,
                           form_data=form_data)


@app.route('/invoices/<int:invoice_id>/envelope', methods=['GET'])
@login_required
def envelope_print(invoice_id):
    """Generate envelope PDF with from and to addresses"""
    invoice = Invoice.query.get_or_404(invoice_id)
    company = Company.query.first()
    
    if not company:
        flash('Company details not found. Please set up company information first.', 'error')
        return redirect(url_for('invoices'))
    
    # Get optional address overrides from query parameters
    to_override = request.args.get('to_override', '').strip()
    from_override = request.args.get('from_override', '').strip()
    
    # Generate envelope PDF
    try:
        pdf_buffer = generate_envelope_pdf(invoice, company, to_override=to_override, from_override=from_override)
        
        response = make_response(pdf_buffer.getvalue())
        response.headers['Content-Type'] = 'application/pdf'
        response.headers['Content-Disposition'] = f'inline; filename=envelope_{invoice.invoice_number}.pdf'
        return response
    except Exception as e:
        flash(f'Error generating envelope: {str(e)}', 'error')
        return redirect(url_for('view_invoice', invoice_id=invoice_id))


@app.route('/envelope/builder', methods=['GET', 'POST'])
@login_required
def envelope_builder():
    """Envelope builder - select invoice to generate envelope"""
    company = Company.query.first()
    if not company:
        flash('Company details not found. Please set up company information first.', 'error')
        return redirect(url_for('company'))
    
    # Get all invoices for selection
    invoices = Invoice.query.order_by(Invoice.invoice_date.desc(), Invoice.invoice_number.desc()).limit(100).all()
    
    if request.method == 'POST':
        invoice_id = request.form.get('invoice_id', '').strip()
        if not invoice_id:
            flash('Please select an invoice.', 'error')
            return render_template('envelope_builder.html', invoices=invoices, company=company)
        
        try:
            invoice_id = int(invoice_id)
            invoice = Invoice.query.get_or_404(invoice_id)
            # Redirect to envelope print route
            return redirect(url_for('envelope_print', invoice_id=invoice_id))
        except (ValueError, TypeError):
            flash('Invalid invoice selected.', 'error')
            return render_template('envelope_builder.html', invoices=invoices, company=company)
    
    return render_template('envelope_builder.html', invoices=invoices, company=company)


@app.route('/packing-slips/designer', methods=['GET', 'POST'])
@login_required
def packing_slip_builder():
    """Standalone packing slip designer with company/from and recipient/to selectors"""
    company = Company.query.first()
    if not company:
        flash('Company details not found. Please set up company information first.', 'error')
        return redirect(url_for('company'))

    company_addresses = get_company_addresses()

    # Build recipient catalog from customers and vendors
    def build_recipient_option(record, recipient_type):
        if not record:
            return None
        option_value = f"{recipient_type}-{record.id}"
        safe_address = (record.address or '').strip()
        city_value = (record.city or '').strip()
        state_value = (record.state or '').strip()
        email_value = (record.email or '').strip()
        label_city = city_value or state_value
        address_lines = []
        if safe_address:
            for raw_line in re.split(r'[\r\n]+', safe_address):
                cleaned = raw_line.strip()
                if cleaned:
                    address_lines.append(cleaned)
        city_state = ", ".join([part for part in [record.city, record.state] if part])
        if record.pincode:
            if city_state:
                city_state = f"{city_state} - {record.pincode}"
            else:
                city_state = record.pincode
        if city_state:
            address_lines.append(city_state)
        contact_hint_parts = []
        if record.phone:
            contact_hint_parts.append(f"Ph: {record.phone}")
        if record.email:
            contact_hint_parts.append(f"Email: {record.email}")
        formatted_lines = [record.name] + address_lines + contact_hint_parts
        search_terms = [
            recipient_type.lower(),
            (record.name or '').lower(),
            city_value.lower(),
            state_value.lower(),
            safe_address.lower(),
            email_value.lower(),
            (record.phone or '').lower()
        ]
        return {
            'value': option_value,
            'label': f"{recipient_type.title()} • {record.name}" + (f" ({label_city})" if label_city else ""),
            'type': recipient_type.title(),
            'name': record.name,
            'address': safe_address,
            'city': city_value,
            'state': state_value,
            'pincode': record.pincode,
            'phone': record.phone,
            'email': email_value,
            'gstin': getattr(record, 'gstin', None),
            'formatted': "\n".join([line for line in formatted_lines if line]),
            'contact_hint': "\n".join(contact_hint_parts),
            'search_blob': " ".join([term for term in search_terms if term])
        }

    customer_records = Customer.query.order_by(Customer.name.asc()).all()
    vendor_records = Vendor.query.order_by(Vendor.name.asc()).all()

    recipient_options = []
    for cust in customer_records:
        option = build_recipient_option(cust, 'customer')
        if option:
            recipient_options.append(option)
    for vendor in vendor_records:
        option = build_recipient_option(vendor, 'vendor')
        if option:
            recipient_options.append(option)

    recipient_lookup = {opt['value']: opt for opt in recipient_options}
    recipient_stats = {
        'customer_count': len(customer_records),
        'vendor_count': len(vendor_records),
        'total_count': len(customer_records) + len(vendor_records)
    }

    form_data = {}

    if request.method == 'POST':
        form_data = request.form.to_dict()
        from_address_key = form_data.get('from_address', 'salem')
        if from_address_key not in company_addresses:
            from_address_key = 'salem'

        selected_recipient = recipient_lookup.get(form_data.get('to_recipient', ''))
        custom_to_text = form_data.get('to_custom_text', '').strip()

        if not selected_recipient and not custom_to_text:
            flash('Please choose a recipient from the dropdown or enter a custom address.', 'error')
            return render_template(
                'packing_slip_form.html',
                company=company,
                company_addresses=company_addresses,
                recipient_options=recipient_options,
                recipient_stats=recipient_stats,
                form_data=form_data,
                default_po_date=date.today().isoformat()
            )

        reference_no = form_data.get('reference_no', '').strip()
        eway_bill = form_data.get('eway_bill', '').strip()
        po_type = form_data.get('po_type', '').strip()
        dept = form_data.get('dept', '').strip()
        contact = form_data.get('contact', '').strip()
        po_date_raw = form_data.get('po_date', '').strip()
        shipping_notes = custom_to_text if custom_to_text else (selected_recipient['formatted'] if selected_recipient else '')

        if not po_date_raw:
            flash('Date is required to generate packing slips.', 'error')
            return render_template(
                'packing_slip_form.html',
                company=company,
                company_addresses=company_addresses,
                recipient_options=recipient_options,
                recipient_stats=recipient_stats,
                form_data=form_data,
                default_po_date=date.today().isoformat()
            )

        try:
            po_date_obj = datetime.strptime(po_date_raw, '%Y-%m-%d')
            po_date = po_date_obj.strftime('%d.%m.%Y')
        except ValueError:
            po_date = po_date_raw

        try:
            num_products = max(1, min(100, int(form_data.get('num_products', 1))))
        except ValueError:
            num_products = 1

        if selected_recipient:
            recipient_name = selected_recipient['name']
            recipient_address = selected_recipient['address'] or selected_recipient['formatted']
            recipient_city = selected_recipient['city']
            recipient_state = selected_recipient['state']
            recipient_pincode = selected_recipient['pincode']
            recipient_phone = selected_recipient['phone']
            recipient_email = selected_recipient['email']
            recipient_gstin = selected_recipient.get('gstin')
        else:
            custom_lines = [line.strip() for line in custom_to_text.splitlines() if line.strip()]
            recipient_name = custom_lines[0] if custom_lines else 'Custom Recipient'
            recipient_address = "\n".join(custom_lines[1:]) if len(custom_lines) > 1 else custom_to_text
            recipient_city = ''
            recipient_state = ''
            recipient_pincode = ''
            recipient_phone = ''
            recipient_email = ''
            recipient_gstin = None

        meta_payload = {
            'reference_no': reference_no or '-',
            'eway_bill': eway_bill or '-',
            'extra_billing_info': shipping_notes,
            'main_address': from_address_key
        }

        virtual_invoice = SimpleNamespace(
            invoice_number=f"PS-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}",
            eway_bill=eway_bill,
            notes=json.dumps(meta_payload),
            customer=SimpleNamespace(
                name=recipient_name,
                address=recipient_address or shipping_notes or recipient_name,
                city=recipient_city or '',
                state=recipient_state or '',
                pincode=recipient_pincode or '',
                phone=recipient_phone or '',
                email=recipient_email or '',
                gstin=recipient_gstin
            )
        )

        try:
            pdf_buffer = generate_delivery_challan_pdf(
                invoice=virtual_invoice,
                company=company,
                po_number='',
                po_date=po_date,
                po_type=po_type,
                dept=dept,
                contact=contact,
                num_products=num_products
            )
        except Exception as pdf_error:
            flash(f'Error generating packing slip: {str(pdf_error)}', 'error')
            return render_template(
                'packing_slip_form.html',
                company=company,
                company_addresses=company_addresses,
                recipient_options=recipient_options,
                recipient_stats=recipient_stats,
                form_data=form_data,
                default_po_date=date.today().isoformat()
            )

        filename_base = re.sub(r'[^A-Za-z0-9]+', '_', recipient_name).strip('_') or 'packing_slip'
        filename = f"packing_slip_{filename_base}_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}.pdf"

        response = make_response(pdf_buffer.getvalue())
        response.headers['Content-Type'] = 'application/pdf'
        response.headers['Content-Disposition'] = f'inline; filename={filename}'
        return response

    return render_template(
        'packing_slip_form.html',
        company=company,
        company_addresses=company_addresses,
        recipient_options=recipient_options,
        recipient_stats=recipient_stats,
        form_data=form_data,
        default_po_date=date.today().isoformat()
    )


def escape_xml_text(text):
    """Escape special characters for XML/PDF rendering to ensure all characters are visible.
    Preserves HTML tags like <b>, <br/>, etc. but escapes user content."""
    if not text:
        return ""
    # Convert to string if not already
    text = str(text)
    # Ensure proper encoding - decode if bytes
    if isinstance(text, bytes):
        try:
            text = text.decode('utf-8', errors='replace')
        except:
            text = text.decode('latin-1', errors='replace')
    
    # Preserve HTML tags by temporarily replacing them
    import re
    html_tags = re.findall(r'<[^>]+>', text)
    tag_placeholders = {}
    for i, tag in enumerate(html_tags):
        placeholder = f"___HTML_TAG_{i}___"
        tag_placeholders[placeholder] = tag
        text = text.replace(tag, placeholder, 1)
    
    # Escape XML special characters in user content
    text = text.replace('&', '&amp;')
    text = text.replace('<', '&lt;')
    text = text.replace('>', '&gt;')
    
    # Restore HTML tags
    for placeholder, tag in tag_placeholders.items():
        text = text.replace(placeholder, tag)
    
    return text

def generate_delivery_challan_pdf(invoice, company, po_number, po_date, po_type, dept, contact, num_products, to_override=None, from_override=None):
    # Note: po_number parameter kept for backward compatibility but not used
    """Generate delivery challan PDF in A4 landscape format - professional grid layout"""
    buffer = BytesIO()
    
    # Create landscape A4 document with optimized margins to prevent page breaks
    landscape_a4 = landscape(A4)
    doc = SimpleDocTemplate(buffer, pagesize=landscape_a4,
                          leftMargin=0.4*inch, rightMargin=0.4*inch,
                          topMargin=0.4*inch, bottomMargin=0.3*inch)
    
    styles = getSampleStyleSheet()
    
    # Get company tagline
    company_details = get_company_details()
    tagline = company_details.get('tagline', 'Creative Solution <br/> For Creative Automation')

    # Extract reference_no, eway_bill, and shipping address from invoice
    invoice_ref_no = '-'
    invoice_eway_bill = '-'
    shipping_address = None
    meta = {}
    
    # Get eway_bill from direct field (primary source)
    if invoice.eway_bill:
        invoice_eway_bill = invoice.eway_bill
    
    # Extract from notes JSON as fallback or additional source
    if invoice.notes:
        try:
            meta = json.loads(invoice.notes)
            invoice_ref_no = meta.get('reference_no', '-') or '-'
            # If eway_bill not in direct field, try from metadata
            if not invoice_eway_bill or invoice_eway_bill == '-':
                invoice_eway_bill = meta.get('eway_bill', '-') or '-'
            # Get shipping address from extra_billing_info
            shipping_address = meta.get('extra_billing_info', '').strip() if meta.get('extra_billing_info') else None
        except (json.JSONDecodeError, TypeError):
            pass
    
    # Apply overrides or fallback to defaults
    override_to_text = to_override.strip() if to_override and to_override.strip() else None
    override_from_text = from_override.strip() if from_override and from_override.strip() else None

    def normalize_override(block_text):
        if not block_text:
            return None
        lines = [line.strip() for line in block_text.replace('\r', '\n').split('\n') if line.strip()]
        return "<br/>".join(lines)

    if not shipping_address:
        shipping_address = f"{invoice.customer.address.strip()}{', ' if invoice.customer.city else ''}{invoice.customer.city if invoice.customer.city else ''}{', ' if invoice.customer.pincode else ''}{invoice.customer.pincode if invoice.customer.pincode else ''}"
    
    # Get company addresses - may need to use main_address from invoice
    company_addresses = get_company_addresses()
    main_address_key = meta.get('main_address', 'salem') if meta else 'salem'
    
    # Get the appropriate company address
    company_address_info = company_addresses.get(main_address_key, company_addresses.get('salem', {}))
    
    # Define professional styles - using Arial font family for consistency
    document_title_style = ParagraphStyle(
        'DocumentTitle',
        parent=styles['Heading1'],
        fontSize=18,
        fontName='Helvetica-Bold',  # Arial equivalent
        textColor=colors.black,
        spaceAfter=12,
        spaceBefore=0,
        alignment=TA_CENTER,
        leading=22
    )
    
    section_label_style = ParagraphStyle(
        'SectionLabel',
        parent=styles['Normal'],
        fontSize=18,
        fontName='Helvetica-Bold',
        textColor=colors.black,
        spaceAfter=12,
        spaceBefore=0,
        leading=20
    )
    
    normal_style = ParagraphStyle(
        'Normal',
        parent=styles['Normal'],
        fontSize=10,
        fontName='Helvetica',
        textColor=colors.black,
        spaceAfter=2,
        leading=12
    )
    
    po_label_style = ParagraphStyle(
        'POLabel',
        parent=styles['Normal'],
        fontSize=16,
        fontName='Helvetica-Bold',
        textColor=colors.black,
        spaceAfter=6,
        leading=18
    )
    
    po_value_style = ParagraphStyle(
        'POValue',
        parent=styles['Normal'],
        fontSize=16,
        fontName='Helvetica',
        textColor=colors.black,
        spaceAfter=6,
        leading=18
    )
    
    address_style = ParagraphStyle(
        'Address',
        parent=styles['Normal'],
        fontSize=16,
        fontName='Helvetica',
        textColor=colors.black,
        spaceAfter=5,
        leading=18
    )
    
    tagline_style = ParagraphStyle(
        'Tagline',
        parent=styles['Normal'],
        fontSize=12,
        fontName='Helvetica-Oblique',
        textColor=colors.HexColor('#666666'),
        spaceAfter=6,
        spaceBefore=0,
        alignment=0,
        leading=10
    )
    
    page_counter_style = ParagraphStyle(
        'PageCounter',
        parent=styles['Normal'],
        fontSize=60,
        fontName='Helvetica-Bold',
        textColor=colors.black,
        alignment=TA_RIGHT,
        spaceAfter=0,
        leading=58
    )
    
    # Load logo if available
    logo_path = os.path.join('static', 'uploads', 'md_logo.jpg')
    logo_available = os.path.exists(logo_path)
    logo_img = None
    if logo_available:
        try:
            logo_img = Image(logo_path, width=1.2*inch, height=1.2*inch)
        except Exception as e:
            print(f"Logo loading error: {e}")
            logo_available = False
    
    # Build content for each page
    story = []
    
    for page_num in range(1, num_products + 1):
        # Build all content for this page
        page_content = []
        
        # 1. DOCUMENT TITLE at top center
        page_content.append(Paragraph("PACKING SLIP LABEL", document_title_style))
        page_content.append(Spacer(1, 0.15*inch))
        
        # 2. HEADER SECTION: Company Logo + Tagline only (address removed from here)
        # Prepare company (From) details - Mahadevi & Co address
        # Use company_address_info if available, otherwise fallback to company object
        if override_from_text:
            from_text = normalize_override(override_from_text)
        elif company_address_info and company_address_info.get('name'):
            # Use formatted address from company_addresses
            from_lines = []
            from_lines.append(company_address_info.get('name', company.name))
            # Address may already contain HTML line breaks
            addr = company_address_info.get('address', '')
            if addr:
                from_lines.append(addr.replace('<br>', '<br/>').replace('<br />', '<br/>'))
            if company_address_info.get('phone'):
                from_lines.append(company_address_info.get('phone'))
            if company_address_info.get('email'):
                from_lines.append(company_address_info.get('email'))
            from_text = "<br/>".join([line for line in from_lines if line.strip()])
        else:
            # Fallback to company object fields
            from_address_lines = [
                company.name if company.name else 'MAHADEVI&CO',
                company.address.strip() if company.address else '',
                f"{company.city}, {company.pincode}" if company.city and company.pincode else (company.city if company.city else ''),
                f"{company.state}, India" if company.state else 'India',
                f"Ph: {company.phone}" if company.phone else "",
                company.email if company.email else ""
            ]
            from_text = "<br/>".join([line for line in from_address_lines if line.strip()])
        
        # Prepare shipping address (To) - from invoice extra_billing_info or customer address
        # Parse shipping address and format it properly
        if override_to_text:
            to_text = normalize_override(override_to_text)
        elif shipping_address and shipping_address.strip():
            # If shipping address is provided, format it nicely
            shipping_lines = []
            
            # Check if customer name is already in the shipping address
            shipping_lower = shipping_address.lower()
            customer_name_lower = invoice.customer.name.lower()
            if customer_name_lower not in shipping_lower:
                shipping_lines.append(invoice.customer.name)
            
            # Process shipping address - handle newlines and commas
            # Replace newlines with commas first, then split
            address_text = shipping_address.replace('\r\n', ',').replace('\n', ',').replace('\r', ',')
            address_parts = [part.strip() for part in address_text.split(',') if part.strip()]
            
            # Add all non-empty parts
            for part in address_parts:
                if part:
                    shipping_lines.append(part)
            
            # Add phone if available
            if invoice.customer.phone:
                shipping_lines.append(f"Ph: {invoice.customer.phone}")
            
            to_text = "<br/>".join(shipping_lines) if shipping_lines else ""
        else:
            # Fallback to customer address
            to_address_lines = [
                invoice.customer.name,
                invoice.customer.address.strip(),
                f"{invoice.customer.city}, {invoice.customer.pincode}",
                f"{invoice.customer.state}, India",
                f"Ph: {invoice.customer.phone}" if invoice.customer.phone else ""
            ]
            to_text = "<br/>".join([line for line in to_address_lines if line.strip()])
        
        # Header: Logo + Tagline only (no address here)
        header_left = []
        if logo_img:
            header_left.append(logo_img)
            header_left.append(Spacer(1, 0.08*inch))
        header_left.append(Paragraph(tagline, tagline_style))
        header_left.append(Spacer(1, 0.02*inch))
        header_left.append(Paragraph(f"<b>Date:</b> {po_date}", po_value_style))
        
        # Header right: Delivery Information consolidated
        header_right = []
        header_right.append(Paragraph("Delivery Detail", section_label_style))
        header_right.append(Spacer(1, 0.05*inch))
        
        def collapse_lines(value):
            if not value:
                return ''
            segments = [seg.strip() for seg in re.split(r'[\r\n]+', str(value)) if seg.strip()]
            return ' | '.join(segments)

        delivery_info_data = []

        def add_delivery_line(label, value):
            if value:
                compact_value = collapse_lines(value)
                delivery_info_data.append([Paragraph(f"<b>{label}</b> {compact_value}", po_value_style)])

        add_delivery_line("PO No.:", None if not invoice_ref_no or invoice_ref_no == '-' else invoice_ref_no)
        add_delivery_line("E-way Bill No.:", None if not invoice_eway_bill or invoice_eway_bill == '-' else invoice_eway_bill)
        if po_type or dept:
            type_dept_parts = []
            if po_type:
                po_type_safe = escape_xml_text(collapse_lines(po_type)) if po_type else ""
                type_dept_parts.append(f"<b>Type:</b> {po_type_safe}")
            if dept:
                dept_safe = escape_xml_text(collapse_lines(dept)) if dept else ""
                type_dept_parts.append(f"<b>Dept.:</b> {dept_safe}")
            delivery_info_data.append([Paragraph(" &nbsp; ".join(type_dept_parts), po_value_style)])
        add_delivery_line("Contact:", contact)
        
        po_table = Table(delivery_info_data, colWidths=[4.7*inch])
        po_table.setStyle(TableStyle([
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('TOPPADDING', (0, 0), (-1, -1), 1),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 1),
            ('LEFTPADDING', (0, 0), (-1, -1), 0),
            ('RIGHTPADDING', (0, 0), (-1, -1), 0),
        ]))
        header_right.append(po_table)
        
        # Create header table - reduced padding
        header_table = Table([[header_left, header_right]], colWidths=[4.5*inch, 4.5*inch])
        header_table.setStyle(TableStyle([
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('ALIGN', (0, 0), (0, 0), 'LEFT'),
            ('ALIGN', (1, 0), (1, 0), 'LEFT'),
            ('TOPPADDING', (0, 0), (-1, -1), 4),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ('LEFTPADDING', (0, 0), (-1, -1), 15),
            ('RIGHTPADDING', (0, 0), (-1, -1), 15),
        ]))
        page_content.append(header_table)
        
        # Thin horizontal divider line - reduced padding
        divider_line = Table([[Spacer(1, 0.005*inch)]], colWidths=[9*inch])
        divider_line.setStyle(TableStyle([
            ('LINEBELOW', (0, 0), (0, 0), 0.5, colors.black),
            ('TOPPADDING', (0, 0), (0, 0), 0.05*inch),
            ('BOTTOMPADDING', (0, 0), (0, 0), 0.05*inch),
        ]))
        page_content.append(divider_line)
        
        # 3. MAIN BODY: Symmetrical From and To addresses side-by-side
        page_content.append(Spacer(1, 0.08*inch))
        
        # Create side-by-side addresses (From=Company/Mahadevi & Co, To=Shipping Address)
        # Ensure addresses are properly encoded
        from_text_safe = escape_xml_text(from_text) if from_text else ""
        to_text_safe = escape_xml_text(to_text) if to_text else ""
        
        from_section_body = []
        from_section_body.append(Paragraph("From", section_label_style))
        from_section_body.append(Spacer(1, 0.08*inch))
        from_section_body.append(Paragraph(from_text_safe, address_style))
        
        to_section = []
        to_section.append(Paragraph("To", section_label_style))
        to_section.append(Spacer(1, 0.08*inch))
        to_section.append(Paragraph(to_text_safe, address_style))
        
        # Addresses table - symmetrical placement - reduced padding (From left, To right)
        addresses_table = Table([[from_section_body, to_section]], colWidths=[4.5*inch, 4.5*inch])
        addresses_table.setStyle(TableStyle([
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('LEFTPADDING', (0, 0), (-1, -1), 15),
            ('RIGHTPADDING', (0, 0), (-1, -1), 15),
            ('LINEBEFORE', (1, 0), (1, 0), 0.5, colors.black),  # Thin vertical divider between From and To
        ]))
        page_content.append(addresses_table)
        
        # Another thin horizontal divider - minimal spacing
        page_content.append(Spacer(1, 0.05*inch))
        page_content.append(divider_line)
        
        # 4. FOOTER: Page counter at bottom right - minimal spacing to keep on same page
        page_content.append(Spacer(1, 0.02*inch))
        
        # Create footer with page counter - ensure it's part of the same flowable
        # Make page counter very prominent and ensure it stays on same page
        footer_content = Table([[Spacer(1, 0.01*inch), Paragraph(f'{page_num}/{num_products}', page_counter_style)]], 
                            colWidths=[6.5*inch, 2.5*inch])
        footer_content.setStyle(TableStyle([
            ('VALIGN', (0, 0), (-1, -1), 'BOTTOM'),
            ('ALIGN', (1, 0), (1, 0), 'RIGHT'),
            ('TOPPADDING', (0, 0), (-1, -1), 5),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
            ('LEFTPADDING', (1, 0), (1, 0), 0),
            ('RIGHTPADDING', (1, 0), (1, 0), 0),
        ]))
        page_content.append(footer_content)
        
        # Wrap entire page content in KeepTogether to ensure footer stays on same page
        # This prevents the page counter from splitting to next page
        story.append(KeepTogether(page_content))
        
        # Add page break except for last page
        if page_num < num_products:
            story.append(PageBreak())
    
    # Build PDF
    doc.build(story)
    buffer.seek(0)
    return buffer


def generate_envelope_pdf(invoice, company, to_override=None, from_override=None):
    """Generate envelope PDF with exact #10 envelope measurements (4.125" x 9.5")"""
    buffer = BytesIO()
    
    # Standard #10 envelope size: 4.125" x 9.5" (105mm x 241mm)
    envelope_width = 4.125 * inch
    envelope_height = 9.5 * inch
    
    # Create envelope-sized document with minimal margins
    from reportlab.lib.pagesizes import portrait
    envelope_size = (envelope_width, envelope_height)
    doc = SimpleDocTemplate(buffer, pagesize=envelope_size,
                          leftMargin=0.3*inch, rightMargin=0.3*inch,
                          topMargin=0.3*inch, bottomMargin=0.3*inch)
    
    styles = getSampleStyleSheet()
    
    # Extract shipping address from invoice
    shipping_address = None
    meta = {}
    if invoice.notes:
        try:
            meta = json.loads(invoice.notes)
            shipping_address = meta.get('extra_billing_info', '').strip() if meta.get('extra_billing_info') else None
        except (json.JSONDecodeError, TypeError):
            pass
    
    # Apply overrides or fallback to defaults
    override_to_text = to_override.strip() if to_override and to_override.strip() else None
    override_from_text = from_override.strip() if from_override and from_override.strip() else None
    
    def normalize_override(block_text):
        if not block_text:
            return None
        lines = [line.strip() for line in block_text.replace('\r', '\n').split('\n') if line.strip()]
        return "<br/>".join(lines)
    
    # Get company addresses
    company_addresses = get_company_addresses()
    main_address_key = meta.get('main_address', 'salem') if meta else 'salem'
    company_address_info = company_addresses.get(main_address_key, company_addresses.get('salem', {}))
    
    # Prepare FROM address (return address - top left)
    if override_from_text:
        from_text = normalize_override(override_from_text)
    elif company_address_info and company_address_info.get('name'):
        from_lines = []
        from_lines.append(company_address_info.get('name', company.name))
        addr = company_address_info.get('address', '')
        if addr:
            from_lines.append(addr.replace('<br>', '<br/>').replace('<br />', '<br/>'))
        if company_address_info.get('phone'):
            from_lines.append(company_address_info.get('phone'))
        if company_address_info.get('email'):
            from_lines.append(company_address_info.get('email'))
        from_text = "<br/>".join([line for line in from_lines if line.strip()])
    else:
        from_address_lines = [
            company.name if company.name else 'MAHADEVI&CO',
            company.address.strip() if company.address else '',
            f"{company.city}, {company.pincode}" if company.city and company.pincode else (company.city if company.city else ''),
            f"{company.state}, India" if company.state else 'India',
            f"Ph: {company.phone}" if company.phone else "",
            company.email if company.email else ""
        ]
        from_text = "<br/>".join([line for line in from_address_lines if line.strip()])
    
    # Prepare TO address (recipient address - center-right)
    if override_to_text:
        to_text = normalize_override(override_to_text)
    elif shipping_address and shipping_address.strip():
        shipping_lines = []
        shipping_lower = shipping_address.lower()
        customer_name_lower = invoice.customer.name.lower()
        if customer_name_lower not in shipping_lower:
            shipping_lines.append(invoice.customer.name)
        address_text = shipping_address.replace('\r\n', ',').replace('\n', ',').replace('\r', ',')
        address_parts = [part.strip() for part in address_text.split(',') if part.strip()]
        for part in address_parts:
            if part:
                shipping_lines.append(part)
        if invoice.customer.phone:
            shipping_lines.append(f"Ph: {invoice.customer.phone}")
        to_text = "<br/>".join(shipping_lines) if shipping_lines else ""
    else:
        to_address_lines = [
            invoice.customer.name,
            invoice.customer.address.strip(),
            f"{invoice.customer.city}, {invoice.customer.pincode}",
            f"{invoice.customer.state}, India",
            f"Ph: {invoice.customer.phone}" if invoice.customer.phone else ""
        ]
        to_text = "<br/>".join([line for line in to_address_lines if line.strip()])
    
    # Get company tagline
    company_details = get_company_details()
    tagline = company_details.get('tagline', 'Creative Solution <br/> For Creative Automation')
    
    # Load logo if available
    logo_path = os.path.join('static', 'uploads', 'md_logo.jpg')
    logo_available = os.path.exists(logo_path)
    logo_img = None
    if logo_available:
        try:
            # Smaller logo for envelope - 0.6 inch to fit nicely
            logo_img = Image(logo_path, width=0.6*inch, height=0.6*inch)
        except Exception as e:
            print(f"Logo loading error: {e}")
            logo_available = False
    
    # Define styles for envelope
    from_address_style = ParagraphStyle(
        'FromAddress',
        parent=styles['Normal'],
        fontSize=9,
        fontName='Helvetica',
        textColor=colors.black,
        spaceAfter=2,
        leading=11,
        leftIndent=0
    )
    
    tagline_style = ParagraphStyle(
        'Tagline',
        parent=styles['Normal'],
        fontSize=8,
        fontName='Helvetica-Oblique',
        textColor=colors.HexColor('#666666'),
        spaceAfter=3,
        spaceBefore=0,
        leading=10,
        leftIndent=0
    )
    
    to_address_style = ParagraphStyle(
        'ToAddress',
        parent=styles['Normal'],
        fontSize=11,
        fontName='Helvetica-Bold',
        textColor=colors.black,
        spaceAfter=3,
        leading=13,
        leftIndent=0
    )
    
    # Build content - VERTICAL PATTERN
    story = []
    
    # FROM address section (return address) - positioned at top-left
    # Include logo and tagline
    from_section = []
    
    if logo_img:
        from_section.append(logo_img)
        from_section.append(Spacer(1, 0.05*inch))
    
    # Add tagline
    from_section.append(Paragraph(tagline, tagline_style))
    from_section.append(Spacer(1, 0.05*inch))
    
    # Add FROM address
    if from_text:
        from_section.append(Paragraph(from_text, from_address_style))
    
    # Add FROM section to story
    if from_section:
        story.extend(from_section)
    
    # Vertical spacing between FROM and TO addresses
    story.append(Spacer(1, 0.4*inch))
    
    # TO address (recipient address) - positioned below FROM address, vertically aligned
    # Center the TO address horizontally on the envelope
    to_table_data = [[Paragraph(to_text, to_address_style)]]
    to_table = Table(to_table_data, colWidths=[3.5*inch])
    to_table.setStyle(TableStyle([
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('LEFTPADDING', (0, 0), (-1, -1), 0),
        ('RIGHTPADDING', (0, 0), (-1, -1), 0),
        ('TOPPADDING', (0, 0), (-1, -1), 0),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 0),
    ]))
    story.append(to_table)
    
    # Build PDF
    doc.build(story)
    buffer.seek(0)
    return buffer


@app.route('/invoices/<int:invoice_id>/delete', methods=['POST'])
@login_required  
def delete_invoice(invoice_id):
    """Simple invoice deletion with company password"""
    try:
        # Get password from form data (sent via JavaScript prompt)
        password = request.form.get('delete_password', '').strip()
        
        if not password:
            flash('Please enter the company password to confirm deletion.', 'error')
            return redirect(url_for('invoices'))
        
        # Check company password from environment variable
        company_password = app.config.get('DELETE_PASSWORD', 'Mahadevi&Co2211')
        if password != company_password:
            flash('❌ Incorrect company password. Deletion cancelled.', 'error')
            print(f"❌ Wrong password attempted by user {current_user.username}: '{password[:10]}...'")
            return redirect(url_for('invoices'))
        
        # Get invoice
        invoice = Invoice.query.get_or_404(invoice_id)
        invoice_number = invoice.invoice_number
        
        print(f"📦 Company password confirmed by {current_user.username} - deleting invoice: {invoice_number}")
        
        try:
            # Delete invoice directly (CASCADE handles related records)
            db.session.delete(invoice)
            db.session.commit()
            
            # Log activity
            log_activity(
                action_type='delete',
                entity_type='invoice',
                entity_id=None,
                resource_identifier=invoice_number,
                description=f"Deleted invoice with company password verification: {invoice_number}"
            )
            
            print(f"✅ Invoice {invoice_number} deleted successfully with company password verification")
            flash(f'✅ Invoice {invoice_number} has been deleted successfully.', 'success')
            
        except Exception as db_error:
            db.session.rollback()
            print(f"❌ Database error deleting invoice: {str(db_error)}")
            flash(f'Error deleting invoice: {str(db_error)}', 'error')
            
        return redirect(url_for('invoices'))
        
    except Exception as e:
        print(f"❌ Critical error in delete_invoice: {str(e)}")
        flash(f'System error: {str(e)}', 'error')
        return redirect(url_for('invoices'))

@app.route('/signature/upload', methods=['GET', 'POST'])
@login_required
def upload_signature():
    """Upload and manage multiple user signatures"""
    if request.method == 'POST':
        try:
            signature_name = request.form.get('signature_name', '').strip()
            
            if not signature_name:
                flash('Signature name is required.', 'error')
                return render_template('signature_upload.html')
            
            # Check if signature file was uploaded
            if 'signature' not in request.files:
                flash('No signature file selected.', 'error')
                return render_template('signature_upload.html')
            
            file = request.files['signature']
            
            if file.filename == '':
                flash('No signature file selected.', 'error')
                return render_template('signature_upload.html')
            
            # Check file type
            if file and file.filename.lower().endswith(('.png', '.jpg', '.jpeg')):
                # Read file and convert to base64
                file_data = file.read()
                base64_data = base64.b64encode(file_data).decode('utf-8')
                
                # Determine file extension for MIME type
                file_ext = os.path.splitext(file.filename)[1].lower()
                mime_types = {
                    '.jpg': 'image/jpeg',
                    '.jpeg': 'image/jpeg',
                    '.png': 'image/png'
                }
                mime_type = mime_types.get(file_ext, 'image/png')
                
                # Create base64 data URI
                signature_uri = f"data:{mime_type};base64,{base64_data}"
                
                # Check if this is set as default
                is_default = request.form.get('is_default') == 'on'
                
                # If setting as default, unset other defaults
                if is_default:
                    UserSignature.query.filter_by(user_id=current_user.id, is_default=True).update({'is_default': False})
                
                # Create new signature
                new_signature = UserSignature(
                    user_id=current_user.id,
                    signature_name=signature_name,
                    signature_data=signature_uri,
                    is_default=is_default,
                    created_by=current_user.id
                )
                
                db.session.add(new_signature)
                
                # Update legacy signature_data (for backward compatibility)
                current_user.signature_data = signature_uri
                
                db.session.commit()
                
                print(f"✅ Signature '{signature_name}' uploaded for user {current_user.username}")
                flash(f'✅ Signature "{signature_name}" uploaded successfully!', 'success')
                
            else:
                flash('❌ Invalid file type. Please upload PNG or JPG images only.', 'error')
                
        except Exception as e:
            print(f"❌ Error uploading signature: {str(e)}")
            db.session.rollback()
            flash(f'Error uploading signature: {str(e)}', 'error')
    
    # Get all signatures for this user
    user_signatures = UserSignature.query.filter_by(user_id=current_user.id).order_by(UserSignature.is_default.desc(), UserSignature.created_at.desc()).all()
    
    return render_template('signature_upload.html', user_signatures=user_signatures)

@app.route('/signature/clear', methods=['POST'])
@login_required
def clear_signature():
    """Clear user signature (legacy support)"""
    try:
        current_user.signature_data = None
        db.session.commit()
        print(f"✅ Signature cleared for user {current_user.username}")
        flash('✅ Signature cleared successfully!', 'success')
    except Exception as e:
        print(f"❌ Error clearing signature: {str(e)}")
        db.session.rollback()
        flash(f'Error clearing signature: {str(e)}', 'error')
    
    return redirect(url_for('upload_signature'))

@app.route('/signature/delete/<int:signature_id>', methods=['POST'])
@login_required
def delete_signature(signature_id):
    """Delete a specific signature"""
    try:
        signature = UserSignature.query.filter_by(id=signature_id, user_id=current_user.id).first()
        
        if not signature:
            flash('Signature not found.', 'error')
            return redirect(url_for('upload_signature'))
        
        # Check if this signature needs to be removed from invoices
        invoices_using_signature = Invoice.query.filter_by(selected_signature_id=signature_id).all()
        if invoices_using_signature:
            # Set invoices back to default signature or None
            Invoice.query.filter_by(selected_signature_id=signature_id).update({'selected_signature_id': None})
            
        # Delete the signature
        db.session.delete(signature)
        db.session.commit()
        
        print(f"✅ Signature '{signature.signature_name}' deleted for user {current_user.username}")
        flash(f'Signature "{signature.signature_name}" deleted successfully!', 'success')
        
    except Exception as e:
        print(f"❌ Error deleting signature: {str(e)}")
        db.session.rollback()
        flash(f'Error deleting signature: {str(e)}', 'error')
    
    return redirect(url_for('upload_signature'))

@app.route('/signature/set-default/<int:signature_id>', methods=['POST'])
@login_required
def set_default_signature(signature_id):
    """Set a signature as default"""
    try:
        signature = UserSignature.query.filter_by(id=signature_id, user_id=current_user.id).first()
        
        if not signature:
            flash('Signature not found.', 'error')
            return redirect(url_for('upload_signature'))
        
        # Unset all other defaults
        UserSignature.query.filter_by(user_id=current_user.id, is_default=True).update({'is_default': False})
        
        # Set this signature as default
        signature.is_default = True
        db.session.commit()
        
        print(f"✅ Signature '{signature.signature_name}' set as default for user {current_user.username}")
        flash(f'"{signature.signature_name}" is now your default signature!', 'success')
        
    except Exception as e:
        print(f"❌ Error setting default signature: {str(e)}")
        db.session.rollback()
        flash(f'Error setting default signature: {str(e)}', 'error')
    
    return redirect(url_for('upload_signature'))

@app.route('/api/signatures', methods=['GET'])
@login_required
def get_signatures_api():
    """API endpoint to get user signatures for AJAX calls"""
    try:
        signatures = UserSignature.query.filter_by(user_id=current_user.id).order_by(
            UserSignature.is_default.desc(), 
            UserSignature.created_at.desc()
        ).all()
        
        signature_list = []
        for sig in signatures:
            signature_list.append({
                'id': sig.id,
                'name': sig.signature_name,
                'is_default': sig.is_default,
                'data': sig.signature_data,
                'created_at': sig.created_at.isoformat()
            })
        
        return jsonify({
            'success': True,
            'signatures': signature_list
        })
        
    except Exception as e:
        print(f"❌ Error getting signatures: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        })

# Error handlers
@app.errorhandler(404)
def not_found_error(error):
    return render_template('errors/404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    db.session.rollback()
    return render_template('errors/500.html'), 500

@app.errorhandler(413)
def too_large(error):
    flash('File too large. Maximum file size is 16MB.', 'error')
    return redirect(request.url)

# Utility functions
def calculate_gst(subtotal, tax_rate, is_interstate=False):
    """Calculate GST amounts based on tax rate and state with proper rounding"""
    from decimal import Decimal, ROUND_HALF_UP
    
    # Ensure inputs are Decimal for precise calculations
    subtotal_decimal = Decimal(str(subtotal))
    tax_rate_decimal = Decimal(str(tax_rate))
    
    # Calculate total tax amount with proper rounding
    tax_amount = (subtotal_decimal * tax_rate_decimal / 100).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
    
    if is_interstate:
        # Interstate: Only IGST
        return Decimal('0'), Decimal('0'), tax_amount
    else:
        # Intrastate: Split into CGST and SGST with proper rounding
        half_tax = (tax_amount / 2).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
        return half_tax, half_tax, Decimal('0')

def number_to_words(num):
    """Convert number to words in Indian format including paise.
    Defensive: handles None, non-numeric, and malformed strings gracefully.
    """
    try:
        # Use string formatting to avoid floating point precision issues
        num_float = float(num) if num is not None else 0.0
        num_str = f"{num_float:.2f}"
        parts = num_str.split('.')
        if len(parts) != 2:
            parts = [parts[0], '00'] if parts else ['0', '00']
        rupees_part, paise_part = parts[0], parts[1]
        rupees = int(rupees_part)
        # Ensure two-digit paise
        paise_str = (paise_part + '00')[:2]
        paise = int(paise_str)
    except Exception:
        rupees, paise = 0, 0
    
    ones = ['', 'One', 'Two', 'Three', 'Four', 'Five', 'Six', 'Seven', 'Eight', 'Nine']
    tens = ['', '', 'Twenty', 'Thirty', 'Forty', 'Fifty', 'Sixty', 'Seventy', 'Eighty', 'Ninety']
    teens = ['Ten', 'Eleven', 'Twelve', 'Thirteen', 'Fourteen', 'Fifteen', 'Sixteen', 'Seventeen', 'Eighteen', 'Nineteen']
    
    def convert_hundreds(n):
        result = ''
        if n >= 100:
            result += ones[n // 100] + ' Hundred '
            n %= 100
        if n >= 20:
            result += tens[n // 10] + ' '
            n %= 10
        elif n >= 10:
            result += teens[n - 10] + ' '
            return result
        if n > 0:
            result += ones[n] + ' '
        return result
    
    # Convert rupees (Indian numbering system: Crore, Lakh, Thousand, Hundreds)
    rupees_text = ''
    if rupees == 0:
        rupees_text = 'Zero'
    else:
        # Handle Crore (>= 1,00,00,000)
        if rupees >= 10000000:
            crores = rupees // 10000000
            rupees_text += convert_hundreds(crores) + 'Crore '
            rupees %= 10000000
        # Handle Lakh (>= 1,00,000)
        if rupees >= 100000:
            lakhs = rupees // 100000
            rupees_text += convert_hundreds(lakhs) + 'Lakh '
            rupees %= 100000
        # Handle Thousand (>= 1,000)
        if rupees >= 1000:
            thousands = rupees // 1000
            rupees_text += convert_hundreds(thousands) + 'Thousand '
            rupees %= 1000
        if rupees > 0:
            rupees_text += convert_hundreds(rupees)
        rupees_text = rupees_text.strip()
    
    # Convert paise
    paise_text = ''
    if paise > 0:
        if paise >= 20:
            paise_text += tens[paise // 10] + ' '
            remaining_paise = paise % 10
            if remaining_paise > 0:
                paise_text += ones[remaining_paise] + ' '
        elif paise >= 10:
            paise_text += teens[paise - 10] + ' '
        else:
            paise_text += ones[paise] + ' '
        paise_text = paise_text.strip() + ' Paise'
    
    # Combine rupees and paise
    if paise_text:
        rupee_word = "Rupee" if rupees == 1 else "Rupees"
        return f"{rupees_text} {rupee_word} and {paise_text} Only"
    else:
        rupee_word = "Rupee" if rupees == 1 else "Rupees"
        return f"{rupees_text} {rupee_word} Only"

def get_company_addresses():
    """Get company address details"""
    return {
        'salem': {
            'name': 'MAHADEVI&CO',
            'address': 'I/462-1, National Nagar,<br>Alangar Theatre Back side,<br>Omalur (T.K), Salem (D.T) 636 455',
            'phone': 'Ph: +91-4290 796930, +91-9444201021',
            'email': 'Email: mahadevico@yahoo.in, mahadevico77@gmail.com'
        },
        'chennai': {
            'name': 'MAHADEVI&CO',
            'address': '#16, 2nd floor, A-Pravesh "A", 19th street,<br>Annai Therasa Nagar, Puzhuthivakkam,<br>Chennai-600091',
            'phone': 'Ph: +91-44-35541362, +91-9444201021',
            'email': 'Email: mahadevico@yahoo.in, mahadevico77@gmail.com'
        }
    }

def get_company_details():
    """Get company business details"""
    return {
        'gstin': '33AAMFM2845D1ZG',
        'pan': 'AAMFM2845D',
        'state': '33-Tamil Nadu',
        'tagline': 'Creative Solution For Creative Automation',
        'signature_name': 'MAHADEVI&CO',
        'default_hsn': '85044090',
        # Address blocks for templates that render location-specific company addresses
        'salem_address': 'I/462-1, National Nagar,<br>Alangar Theatre Back side,<br>Omalur (T.K), Salem (D.T) 636 455',
        'chennai_address': '#16, 2nd floor, A-Pravesh "A", 19th street,<br>Annai Therasa Nagar, Puzhuthivakkam,<br>Chennai-600091',
        'bank_details': {
            'account_number': '01782000002792',
            'ifsc': 'HDFC0000178',
            'bank_name': 'HDFC BANK LTD',
            'branch_name': 'SALEM MAIN BRANCH 636004',
            'account_type': 'CURRENT',
            'virtual_payment': '9444201021@hdfcbank'
        },
        'default_terms': 'CERTIFIED THAT THE PARTICULARS GIVEN ABOVE ARE TRUE AND CORRECT. WE ALSO DECLARE THAT WE WILL REMIT THE GST AMOUNT AND FILE APPLICABLE GST RETURNS',
        'default_payment_terms': 'Payment: 100% Against supply Immediate.  Warranty: 12 Month From the date of Supply.  Only For: Ac Drive, PLC, Servo Drive & Servo Motors'
    }

def generate_payment_qr_code(amount, invoice_number, customer_name):
    """Generate QR code for UPI payment"""
    try:
        # Get company details
        company_details = get_company_details()
        
        # Create UPI payment URL
        upi_id = company_details['bank_details']['virtual_payment']  # 9444201021@hdfcbank
        company_name = company_details['signature_name']  # MAHADEVI&CO
        
        # Format amount to 2 decimal places
        formatted_amount = f"{float(amount):.2f}"
        
        # Create UPI payment URL
        upi_url = f"upi://pay?pa={upi_id}&pn={company_name}&am={formatted_amount}&cu=INR&tn=Invoice {invoice_number} - {customer_name}"
        
        # Generate QR code
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(upi_url)
        qr.make(fit=True)
        
        # Create QR code image
        qr_image = qr.make_image(fill_color="black", back_color="white")
        
        # Convert to base64 for embedding in HTML
        buffer = io.BytesIO()
        qr_image.save(buffer, format='PNG')
        buffer.seek(0)
        qr_base64 = base64.b64encode(buffer.getvalue()).decode()
        
        return f"data:image/png;base64,{qr_base64}"
        
    except Exception as e:
        print(f"Error generating QR code: {str(e)}")
        return None

def get_gst_state_mapping():
    """Get GST state code to state name mapping"""
    return {
        '01': 'Jammu and Kashmir',
        '02': 'Himachal Pradesh',
        '03': 'Punjab',
        '04': 'Chandigarh',
        '05': 'Uttarakhand',
        '06': 'Haryana',
        '07': 'Delhi',
        '08': 'Rajasthan',
        '09': 'Uttar Pradesh',
        '10': 'Bihar',
        '11': 'Sikkim',
        '12': 'Arunachal Pradesh',
        '13': 'Nagaland',
        '14': 'Manipur',
        '15': 'Mizoram',
        '16': 'Tripura',
        '17': 'Meghalaya',
        '18': 'Assam',
        '19': 'West Bengal',
        '20': 'Jharkhand',
        '21': 'Odisha',
        '22': 'Chhattisgarh',
        '23': 'Madhya Pradesh',
        '24': 'Gujarat',
        '25': 'Daman and Diu',
        '26': 'Dadra and Nagar Haveli',
        '27': 'Maharashtra',
        '28': 'Andhra Pradesh',
        '29': 'Karnataka',
        '30': 'Goa',
        '31': 'Lakshadweep',
        '32': 'Kerala',
        '33': 'Tamil Nadu',
        '34': 'Puducherry',
        '35': 'Andaman and Nicobar Islands',
        '36': 'Telangana',
        '37': 'Andhra Pradesh',
        '38': 'Ladakh'
    }

def get_state_from_gstin(gstin):
    """Extract state name from GSTIN"""
    if not gstin or len(gstin) < 2:
        return "Unknown State"
    
    state_code = gstin[:2]
    state_mapping = get_gst_state_mapping()
    return f"{state_code}-{state_mapping.get(state_code, 'Unknown State')}"

def validate_invoice_data(invoice):
    """Validate invoice has required data"""
    if not invoice.items:
        raise ValueError("Invoice must have at least one item")
    if not invoice.customer:
        raise ValueError("Invoice must have a customer")
    if not invoice.company:
        raise ValueError("Invoice must have company information")
    return True

def calculate_item_amount_with_discount(item):
    """Calculate item amount after applying discount"""
    from decimal import Decimal
    
    # Calculate gross amount
    gross_amount = Decimal(str(item.quantity)) * Decimal(str(item.unit_price))
    
    # Validate and calculate discount amount
    validated_discount_value = validate_discount_value(item.discount_type, item.discount_value, gross_amount)
    
    if item.discount_type == 'percentage' and validated_discount_value > 0:
        discount_amount = gross_amount * validated_discount_value / Decimal('100')
    elif item.discount_type == 'amount' and validated_discount_value > 0:
        discount_amount = validated_discount_value
    else:
        discount_amount = Decimal('0')
    
    # Calculate final amount after discount (ensure it's not negative)
    final_amount = gross_amount - discount_amount
    return max(final_amount, Decimal('0'))

def update_invoice_totals(invoice):
    """Update invoice totals based on items and settings"""
    # Validate invoice has required data
    validate_invoice_data(invoice)
    
    # Calculate subtotal from items with individual discounts
    from decimal import Decimal
    subtotal = sum(calculate_item_amount_with_discount(item) for item in invoice.items)
    
    # Taxable amount is the same as subtotal (no invoice-level discount)
    taxable_amount = subtotal
    
    # Calculate GST (simplified - using first item's tax rate or default 18%)
    if invoice.items:
        # Use the most common tax rate among items
        tax_rates = [Decimal(str(item.tax_rate)) for item in invoice.items]
        tax_rate = max(set(tax_rates), key=tax_rates.count)
    else:
        tax_rate = Decimal('18')
    
    # Determine if interstate (company state vs customer state)
    # Get company state from GSTIN
    company_details = get_company_details()
    if not company_details['gstin']:
        raise ValueError("Company GSTIN is missing. Please update company details with GSTIN.")
    
    company_state = get_state_from_gstin(company_details['gstin'])
    
    # Get customer state from GSTIN
    if not invoice.customer.gstin:
        raise ValueError("Customer GSTIN is missing. Please update customer details with GSTIN.")
    
    customer_state = get_state_from_gstin(invoice.customer.gstin)
    is_interstate = customer_state != company_state
    
    # Calculate GST amounts
    cgst, sgst, igst = calculate_gst(taxable_amount, tax_rate, is_interstate)
    
    # Calculate total (ensure all values are Decimal)
    shipping_charges = Decimal(str(invoice.shipping_charges or 0))
    total_amount = taxable_amount + cgst + sgst + igst + shipping_charges
    
    # Update invoice (ensure all values are Decimal)
    invoice.subtotal = subtotal
    invoice.cgst_amount = cgst
    invoice.sgst_amount = sgst
    invoice.igst_amount = igst
    invoice.total_amount = total_amount

def update_purchase_order_totals(po):
    """Update purchase order totals based on items and settings"""
    # Calculate subtotal from items with individual discounts
    from decimal import Decimal
    subtotal = sum(calculate_item_amount_with_discount(item) for item in po.items)
    
    # Taxable amount is the same as subtotal (no PO-level discount)
    taxable_amount = subtotal
    
    # Calculate GST (simplified - using first item's tax rate or default 18%)
    if po.items:
        # Use the most common tax rate among items
        tax_rates = [Decimal(str(item.tax_rate)) for item in po.items]
        tax_rate = max(set(tax_rates), key=tax_rates.count)
    else:
        tax_rate = Decimal('18')
    
    # Determine if interstate (company state vs vendor state)
    # Get company state from GSTIN
    company_details = get_company_details()
    if not company_details['gstin']:
        raise ValueError("Company GSTIN is missing. Please update company details with GSTIN.")
    
    company_state = get_state_from_gstin(company_details['gstin'])
    
    # Get vendor state from GSTIN
    if not po.vendor.gstin:
        raise ValueError("Vendor GSTIN is missing. Please update vendor details with GSTIN.")
    
    vendor_state = get_state_from_gstin(po.vendor.gstin)
    is_interstate = vendor_state != company_state
    
    # Calculate GST amounts
    cgst, sgst, igst = calculate_gst(taxable_amount, tax_rate, is_interstate)
    
    # Calculate total (ensure all values are Decimal)
    shipping_charges = Decimal(str(po.shipping_charges or 0))
    total_amount = taxable_amount + cgst + sgst + igst + shipping_charges
    
    # Update purchase order (ensure all values are Decimal)
    po.subtotal = subtotal
    po.cgst_amount = cgst
    po.sgst_amount = sgst
    po.igst_amount = igst
    po.total_amount = total_amount

# ============================================
# ACTIVITY LOGS ROUTES
# ============================================

@app.route('/activity-logs')
@login_required
def activity_logs():
    """View activity logs with filtering and pagination"""
    # Get filter parameters
    page = request.args.get('page', 1, type=int)
    per_page = 20
    
    search = request.args.get('search', '').strip()
    action_filter = request.args.get('action', '').strip()
    entity_filter = request.args.get('entity', '').strip()
    user_filter = request.args.get('user', '').strip()
    date_from = request.args.get('date_from', '').strip()
    date_to = request.args.get('date_to', '').strip()
    
    # Start with base query
    query = ActivityLog.query
    
    # Apply filters
    if search:
        query = query.filter(
            db.or_(
                ActivityLog.username.ilike(f'%{search}%'),
                ActivityLog.resource_identifier.ilike(f'%{search}%'),
                ActivityLog.description.ilike(f'%{search}%')
            )
        )
    
    if action_filter:
        query = query.filter(ActivityLog.action_type == action_filter)
    
    if entity_filter:
        query = query.filter(ActivityLog.entity_type == entity_filter)
    
    if user_filter:
        query = query.filter(ActivityLog.username == user_filter)
    
    if date_from:
        try:
            date_from_obj = datetime.strptime(date_from, '%Y-%m-%d')
            query = query.filter(ActivityLog.timestamp >= date_from_obj)
        except ValueError:
            pass
    
    if date_to:
        try:
            date_to_obj = datetime.strptime(date_to, '%Y-%m-%d')
            # Add 23:59:59 to include the full day
            date_to_obj = date_to_obj.replace(hour=23, minute=59, second=59)
            query = query.filter(ActivityLog.timestamp <= date_to_obj)
        except ValueError:
            pass
    
    # Order by timestamp descending (most recent first)
    query = query.order_by(ActivityLog.timestamp.desc())
    
    # Paginate
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)
    logs = pagination.items
    
    # Get unique values for filter dropdowns
    action_types = db.session.query(ActivityLog.action_type).distinct().all()
    entity_types = db.session.query(ActivityLog.entity_type).distinct().all()
    usernames = db.session.query(ActivityLog.username).distinct().all()
    
    # Convert to lists
    action_types = [action[0] for action in action_types if action[0]]
    entity_types = [entity[0] for entity in entity_types if entity[0]]
    usernames = [user[0] for user in usernames if user[0]]
    
    return render_template('activity_logs.html',
                         logs=logs,
                         pagination=pagination,
                         search=search,
                         action_filter=action_filter,
                         entity_filter=entity_filter,
                         user_filter=user_filter,
                         date_from=date_from,
                         date_to=date_to,
                         action_types=sorted(action_types),
                         entity_types=sorted(entity_types),
                         usernames=sorted(usernames))

@app.route('/activity-logs/export')
@login_required
def export_activity_logs():
    """Export activity logs as CSV"""
    from io import StringIO
    import csv
    
    # Get filter parameters (same as activity_logs route)
    search = request.args.get('search', '').strip()
    action_filter = request.args.get('action', '').strip()
    entity_filter = request.args.get('entity', '').strip()
    user_filter = request.args.get('user', '').strip()
    date_from = request.args.get('date_from', '').strip()
    date_to = request.args.get('date_to', '').strip()
    
    # Build query (same as activity_logs route)
    query = ActivityLog.query
    
    if search:
        query = query.filter(
            db.or_(
                ActivityLog.username.ilike(f'%{search}%'),
                ActivityLog.resource_identifier.ilike(f'%{search}%'),
                ActivityLog.description.ilike(f'%{search}%')
            )
        )
    
    if action_filter:
        query = query.filter(ActivityLog.action_type == action_filter)
    
    if entity_filter:
        query = query.filter(ActivityLog.entity_type == entity_filter)
    
    if user_filter:
        query = query.filter(ActivityLog.username == user_filter)
    
    if date_from:
        try:
            date_from_obj = datetime.strptime(date_from, '%Y-%m-%d')
            query = query.filter(ActivityLog.timestamp >= date_from_obj)
        except ValueError:
            pass
    
    if date_to:
        try:
            date_to_obj = datetime.strptime(date_to, '%Y-%m-%d')
            date_to_obj = date_to_obj.replace(hour=23, minute=59, second=59)
            query = query.filter(ActivityLog.timestamp <= date_to_obj)
        except ValueError:
            pass
    
    query = query.order_by(ActivityLog.timestamp.desc())
    logs = query.all()
    
    # Create CSV
    output = StringIO()
    writer = csv.writer(output)
    
    # Write header
    writer.writerow(['ID', 'Timestamp', 'User', 'Action', 'Entity', 'Resource', 'Old Value', 'New Value', 'IP Address', 'Description'])
    
    # Write data
    for log in logs:
        writer.writerow([
            log.id,
            log.timestamp.strftime('%Y-%m-%d %H:%M:%S'),
            log.username,
            log.action_type,
            log.entity_type,
            log.resource_identifier or '',
            log.old_value or '',
            log.new_value or '',
            log.ip_address or '',
            log.description or ''
        ])
    
    # Prepare response
    output.seek(0)
    response = make_response(output.getvalue())
    response.headers['Content-Type'] = 'text/csv'
    response.headers['Content-Disposition'] = f'attachment; filename=activity_logs_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
    
    return response

# ==================== CHATBOT ROUTES ====================

@app.route('/api/chat/send', methods=['POST'])
@login_required
@limiter.limit("30 per minute")  # Rate limit: 30 messages per minute
def chat_send():
    """Send a message to the chatbot"""
    try:
        data = request.get_json()
        message = data.get('message', '').strip()
        
        if not message:
            return jsonify({'error': 'Message cannot be empty'}), 400
        
        # Get or create conversation
        conversation = ChatConversation.query.filter_by(user_id=current_user.id).order_by(ChatConversation.updated_at.desc()).first()
        
        if not conversation:
            conversation = ChatConversation(user_id=current_user.id)
            db.session.add(conversation)
            db.session.flush()
        
        # Save user message
        user_msg = ChatMessage(
            conversation_id=conversation.id,
            role='user',
            message=message
        )
        db.session.add(user_msg)
        db.session.flush()
        
        # Import chatbot service once
        from chatbot_service import ChatbotService
        chatbot = ChatbotService()
        
        # Get user context for AI (optimized query)
        user_context = {}
        try:
            # This appears to be a single-user system where invoices/customers are not user-specific
            # Simply get total counts - can be enhanced later if multi-user support is added
            total_invoices = db.session.query(Invoice).count() or 0
            total_customers = db.session.query(Customer).count() or 0
            
            user_context = {
                'total_invoices': total_invoices,
                'total_customers': total_customers
            }
        except Exception as e:
            print(f"Error getting user context: {e}")
            import traceback
            traceback.print_exc()
        
        # Get conversation history for context (last 5 messages)
        conversation_history = []
        try:
            if conversation and conversation.id:
                conversation_history = chatbot.get_conversation_context(db.session, conversation.id, max_messages=5) or []
        except Exception as e:
            print(f"Error getting conversation history: {e}")
            import traceback
            traceback.print_exc()
        
        # Always add current message to history
        if not isinstance(conversation_history, list):
            conversation_history = []
        conversation_history.append({'role': 'user', 'message': message})
        
        # Process message with chatbot service (singleton instance)
        try:
            response_text = chatbot.process_message(message, user_context, conversation_history)
            if not response_text or not response_text.strip():
                # Use fallback directly instead of accessing private method
                response_text = """I'm Marvel, your AI assistant. I can help you with invoices, business questions, or anything else.

**What I can help with:**
• Invoice management and GST calculations
• Business and finance questions  
• Technical and programming help
• General knowledge

Try asking me something specific!"""
        except Exception as e:
            print(f"Error processing message with chatbot: {e}")
            import traceback
            traceback.print_exc()
            # Fallback response
            response_text = """I'm MD, your AI assistant. I can help you with invoices, business questions, or anything else.

**What I can help with:**
• Invoice management and GST calculations
• Business and finance questions  
• Technical and programming help
• General knowledge

Try asking me something specific, or check that your HUGGINGFACE_API_KEY is set if you want AI-powered responses."""
        
        # Save assistant response
        assistant_msg = ChatMessage(
            conversation_id=conversation.id,
            role='assistant',
            message=response_text
        )
        db.session.add(assistant_msg)
        
        # Update conversation timestamp (use utcnow for compatibility, or datetime.now(timezone.utc) for Python 3.11+)
        try:
            from datetime import timezone
            conversation.updated_at = datetime.now(timezone.utc)
        except:
            conversation.updated_at = datetime.utcnow()
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'response': response_text,
            'message_id': user_msg.id
        })
        
    except Exception as e:
        db.session.rollback()
        import traceback
        error_details = traceback.format_exc()
        print(f"Chat error: {e}")
        print(f"Full traceback:\n{error_details}")
        
        # Always return a valid response, even on error
        try:
            from chatbot_service import ChatbotService
            chatbot = ChatbotService()
            fallback_response = chatbot.get_default_response()
        except:
            fallback_response = "I'm Marvel, your AI assistant. I'm experiencing a technical issue. Please try again."
        
        return jsonify({
            'success': True,  # Still return success to show message
            'response': fallback_response,
            'error': str(e) if app.config.get('DEBUG') else None
        })

@app.route('/api/chat/history', methods=['GET'])
@login_required
def chat_history():
    """Get chat conversation history (optimized query)"""
    try:
        # Optimized: Single query with join and ordering
        conversation = db.session.query(ChatConversation).filter_by(
            user_id=current_user.id
        ).order_by(ChatConversation.updated_at.desc()).first()
        
        if not conversation:
            return jsonify({'messages': []})
        
        # Optimized: Single query with proper ordering
        messages = db.session.query(ChatMessage).filter_by(
            conversation_id=conversation.id
        ).order_by(ChatMessage.created_at.asc()).all()
        
        return jsonify({
            'messages': [
                {
                    'id': msg.id,
                    'role': msg.role,
                    'message': msg.message,
                    'created_at': msg.created_at.strftime('%Y-%m-%d %H:%M:%S')
                }
                for msg in messages
            ]
        })
        
    except Exception as e:
        print(f"Chat history error: {e}")
        return jsonify({'messages': []})

@app.route('/api/chat/clear', methods=['POST'])
@login_required
def chat_clear():
    """Clear chat conversation history"""
    try:
        conversation = ChatConversation.query.filter_by(user_id=current_user.id).first()
        if conversation:
            # Delete all messages
            ChatMessage.query.filter_by(conversation_id=conversation.id).delete()
            # Delete conversation
            db.session.delete(conversation)
            db.session.commit()
        
        return jsonify({'success': True})
        
    except Exception as e:
        db.session.rollback()
        print(f"Chat clear error: {e}")
        return jsonify({'error': 'Failed to clear chat'}), 500

# Initialize database
def init_db():
    """Initialize database and create all tables"""
    with app.app_context():
        db.create_all()
        
        # Create default admin user if no users exist
        if not User.query.first():
            admin = User(
                username='admin',
                email='admin@company.com',
                role='admin'
            )
            admin.set_password(app.config.get('DEFAULT_ADMIN_PASSWORD'))
            db.session.add(admin)
            db.session.commit()
            admin_password = app.config.get('DEFAULT_ADMIN_PASSWORD')
            print(f"Default admin user created: username='admin', password='{admin_password}'")
        else:
            # Update existing admin user password if environment variable is set
            admin = User.query.filter_by(username='admin').first()
            if admin and os.environ.get('DEFAULT_ADMIN_PASSWORD'):
                new_password = app.config.get('DEFAULT_ADMIN_PASSWORD')
                admin.set_password(new_password)
                db.session.commit()
                print(f"✅ Admin password updated: username='admin', password='{new_password}'")

if __name__ == '__main__':
    init_db()
    app.run(debug=os.environ.get('FLASK_DEBUG', 'False').lower() == 'true')

