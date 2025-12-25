# KV Store - Full-Stack E-commerce Platform

A comprehensive Django-based e-commerce platform with Razorpay payment integration, featuring complete shopping cart, order management, user authentication, and admin dashboard.

## 📋 Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Technology Stack](#technology-stack)
- [Prerequisites](#prerequisites)
- [Installation & Setup](#installation--setup)
- [Configuration](#configuration)
- [Running the Application](#running-the-application)
- [Testing](#testing)
- [API Endpoints](#api-endpoints)
- [Payment Integration](#payment-integration)
- [Project Structure](#project-structure)
- [Custom Management Commands](#custom-management-commands)
- [Production Deployment](#production-deployment)
- [Troubleshooting](#troubleshooting)
- [Contact Information](#contact-information)
- [Additional Documentation](#additional-documentation)

## 🎯 Overview

KV Store is a production-ready e-commerce web application built with Django framework, providing a complete online shopping experience with secure payment processing, comprehensive order management, and intuitive user interface. The platform is optimized for mobile devices, specifically iPhone 14 Pro Max.

**Key Highlights:**
- Full-featured e-commerce functionality
- Multiple payment methods (Card, UPI, Net Banking, Wallets, COD)
- Real-time payment tracking and analytics
- Automated refund processing
- Mobile-responsive design
- Comprehensive admin dashboard

## ✨ Features

### 1. User Management & Authentication
- User registration with email validation
- Secure login/logout with session management
- Password validation and security
- User profile management
- Address book (multiple shipping/billing addresses)
- Customer dashboard with order history

### 2. Product Catalog System
- Product listing with pagination, search, and advanced filtering
- Category-based product organization with hierarchical structure
- Product detail pages with multiple images, descriptions, specifications
- Featured products and latest products sections
- Stock quantity management and inventory tracking
- Sale pricing with automatic discount calculation
- Product reviews and ratings system (1-5 stars) with approval workflow

### 3. Shopping Cart & Checkout
- Dynamic shopping cart with add/remove/update quantity functionality
- Real-time cart total calculation including taxes and shipping
- Coupon code application with validation
- Multi-step checkout process with address selection
- Order summary and confirmation

### 4. Payment Integration (Razorpay)
- Integrated Razorpay payment gateway with full API implementation
- Support for multiple payment methods:
  - Credit/Debit Cards
  - UPI
  - Net Banking
  - Digital Wallets
  - Cash on Delivery (COD)
- Secure payment processing with HMAC signature verification
- Payment status tracking and webhook handling
- Automated refund processing with partial and full refund support
- Payment analytics and transaction history

### 5. Order Management
- Complete order lifecycle: Pending → Confirmed → Processing → Shipped → Delivered
- Order tracking with real-time status updates
- Order history with detailed invoice generation
- Email notifications for order confirmation and status changes
- Return/refund request system with admin approval workflow
- Order cancellation functionality

### 6. Wishlist
- Add/remove items to wishlist
- Wishlist management
- Add all wishlist items to cart

### 7. Search & Filtering
- Product search functionality with keyword matching
- Category filtering
- Price range filtering
- Stock filtering

### 8. Additional Features
- Newsletter subscription with email preferences
- Contact form with categorized inquiries
- About page with founder information
- FAQ page
- Terms and Privacy pages
- Chatbot integration
- Image management

### 9. Admin Dashboard
- Product management (CRUD operations)
- Order management with status updates
- Customer management and analytics
- Category and coupon management
- Payment analytics and refund processing
- Return request management
- User management

### 10. Mobile Responsiveness
- iPhone 14 Pro Max optimized
- Responsive design for all screen sizes
- Mobile-friendly navigation
- Touch-optimized interface

## 🛠️ Technology Stack

### Backend
- **Django 5.2.4** - Web framework
- **Python 3.8+** - Programming language
- **SQLite** - Database (default, can be changed to PostgreSQL/MySQL)
- **Razorpay 1.4.2** - Payment gateway SDK
- **Pillow 10.4.0** - Image processing
- **python-dotenv 1.0.0** - Environment variable management

### Frontend
- **HTML5** - Markup
- **CSS3/SCSS** - Styling with SCSS compilation
- **JavaScript** - Client-side interactivity
- **AJAX** - Asynchronous requests

### Security
- CSRF protection
- XSS protection headers
- Secure session cookies
- SQL injection prevention (Django ORM)
- HMAC signature verification for payments
- Password hashing and validation

## 📦 Prerequisites

- Python 3.8 or higher
- pip (Python package installer)
- Git (optional, for version control)

## 🚀 Installation & Setup

### 1. Navigate to the Project Directory

Open your terminal/command prompt and navigate to the project directory:

```bash
cd "G:\Fita\DJango\KV DJANGO PROJECT\KV\kv10"
```

### 2. Create a Virtual Environment (Recommended)

Create a virtual environment to isolate project dependencies:

**Windows (PowerShell):**
```powershell
python -m venv venv
```

**Windows (Command Prompt):**
```cmd
python -m venv venv
```

**Activate the virtual environment:**

**Windows (PowerShell):**
```powershell
.\venv\Scripts\Activate.ps1
```

**Windows (Command Prompt):**
```cmd
venv\Scripts\activate.bat
```

**Linux/Mac:**
```bash
python3 -m venv venv
source venv/bin/activate
```

> **Note:** If you get an execution policy error in PowerShell, use Command Prompt or Git Bash instead.

### 3. Install Dependencies

Install all required packages:

```bash
pip install -r requirements.txt
```

### 4. Create Environment Variables File

Create a `.env` file in the project root directory (`kv10/`) with the following variables:

```env
# Django Settings
SECRET_KEY=your-secret-key-here
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1,testserver
CSRF_TRUSTED_ORIGINS=http://localhost,http://127.0.0.1

# Razorpay Settings (Required for payment functionality)
RAZORPAY_KEY_ID=your-razorpay-key-id
RAZORPAY_KEY_SECRET=your-razorpay-key-secret
RAZORPAY_WEBHOOK_SECRET=your-razorpay-webhook-secret

# Email Settings (Optional)
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password
DEFAULT_FROM_EMAIL=your-email@gmail.com
```

**Generate a Django Secret Key:**
```python
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

### 5. Run Database Migrations

Set up the database:

```bash
python manage.py migrate
```

### 6. Create a Superuser (Optional but Recommended)

Create an admin user to access the Django admin panel:

```bash
python manage.py createsuperuser
```

Follow the prompts to set up your admin username, email, and password.

### 7. Collect Static Files (Optional)

If you need to collect static files for production:

```bash
python manage.py collectstatic
```

### 8. Run the Development Server

Start the Django development server:

```bash
python manage.py runserver
```

The server will start at `http://127.0.0.1:8000/` or `http://localhost:8000/`

### 9. Access the Application

- **Main Application:** http://127.0.0.1:8000/
- **Admin Panel:** http://127.0.0.1:8000/admin/
- **Payment Analytics:** http://127.0.0.1:8000/payment/analytics/
- **Features Dashboard:** http://127.0.0.1:8000/features/

## 🧪 Testing

### Test Cards (Razorpay Test Mode)

When testing payments in Razorpay test mode, use these test cards:

- **Successful Payment:** `4111 1111 1111 1111`
- **Failed Payment:** `4000 0000 0000 0002`
- **Insufficient Funds:** `4000 0000 0000 9995`
- **CVV:** Any 3 digits
- **Expiry:** Any future date

### Test UPI IDs

- **Success:** `success@razorpay`
- **Failure:** `failure@razorpay`

### Running Tests

```bash
# Test Razorpay integration
python manage.py test_razorpay

# Run Django test suite
python manage.py test
```

## 🔌 API Endpoints

### Main Pages
- `GET /` - Home page
- `GET /about/` - About page
- `GET /contact/` - Contact page
- `GET /faq/` - FAQ page
- `GET /terms/` - Terms of service
- `GET /privacy/` - Privacy policy

### Authentication
- `GET/POST /register/` - User registration
- `GET/POST /login/` - User login
- `POST /logout/` - User logout
- `GET /profile/` - User profile

### Address Management
- `GET/POST /addresses/add/` - Add new address
- `GET/POST /addresses/<id>/edit/` - Edit address
- `POST /addresses/<id>/delete/` - Delete address
- `POST /addresses/<id>/set-default/<which>/` - Set default address

### Products
- `GET /products/` - Product listing
- `GET /product/<slug>/` - Product detail
- `GET /category/<slug>/` - Category detail
- `GET /search/` - Product search
- `GET /product/<id>/reviews/` - Product reviews

### Shopping Cart
- `GET /cart/` - View cart
- `POST /add-to-cart/<product_id>/` - Add to cart
- `POST /remove-from-cart/<item_id>/` - Remove from cart

### Checkout & Orders
- `GET/POST /checkout/` - Checkout process
- `GET /orders/` - Order list
- `GET /order/<id>/` - Order detail
- `GET /order/<id>/track/` - Order tracking
- `GET /order/<id>/invoice/` - Download invoice
- `POST /order/<id>/cancel/` - Cancel order
- `GET/POST /order/<id>/return/` - Return request
- `GET /order_tracking/` - Order tracking search

### Wishlist
- `GET /wishlist/` - View wishlist
- `POST /add-to-wishlist/<product_id>/` - Add to wishlist
- `POST /remove-from-wishlist/<item_id>/` - Remove from wishlist
- `POST /add-all-to-cart/` - Add all wishlist items to cart
- `POST /clear-wishlist/` - Clear wishlist

### Payment
- `GET/POST /payment/` - Payment page
- `POST /payment/callback/` - Payment success callback
- `POST /payment/failure/` - Payment failure handler
- `GET /payment/analytics/` - Payment analytics (admin)
- `POST /payment/refund/<payment_id>/` - Initiate refund
- `GET /payment/success/<order_id>/` - Payment success page

### API Endpoints
- `GET /api/cart-count/` - Get cart item count
- `POST /api/chatbot/` - Chatbot API

### Admin
- `GET /admin/dashboard/` - Admin dashboard
- `GET /features/` - Features dashboard

### Newsletter
- `POST /newsletter/` - Newsletter subscription

## 💳 Payment Integration

### Razorpay Setup

1. **Create Razorpay Account**
   - Visit [https://razorpay.com](https://razorpay.com)
   - Sign up for a business account
   - Complete KYC verification

2. **Get API Credentials**
   - Go to Dashboard → Account & Settings → API Keys
   - Generate Test/Live API keys
   - Copy `Key ID` and `Key Secret`

3. **Update Environment Variables**
   ```env
   RAZORPAY_KEY_ID=your_actual_razorpay_key_id
   RAZORPAY_KEY_SECRET=your_actual_razorpay_key_secret
   RAZORPAY_WEBHOOK_SECRET=your_razorpay_webhook_secret
   ```

### Payment Flow

1. **Checkout Process**
   ```
   Customer Cart → Checkout Form → Payment Method Selection → Razorpay Payment
   ```

2. **Payment Processing**
   ```
   Razorpay Order Creation → Payment Gateway → Signature Verification → Order Completion
   ```

3. **Failure Handling**
   ```
   Payment Failure → Error Recording → User Notification → Retry Option
   ```

### Payment Methods Supported

- Cash on Delivery (COD)
- Credit/Debit Cards
- UPI
- Net Banking
- Digital Wallets

### Refund Process

1. Go to order detail page
2. Click "Refund" button (admin only)
3. Enter refund amount and reason
4. Refund is processed automatically via Razorpay

**Refund Types Supported:**
- Full Refund: Complete order amount
- Partial Refund: Specific amount
- Multiple Refunds: Multiple partial refunds

### Payment Analytics

Access payment analytics at `/payment/analytics/` (admin access required)

**Key Metrics Tracked:**
- Total payments processed
- Success/failure rates
- Revenue and processing fees
- Payment method preferences
- Refund statistics

## 📁 Project Structure

```
kv10/
├── kv10/                    # Main Django project settings
│   ├── settings.py          # Project settings
│   ├── urls.py              # Main URL configuration
│   ├── wsgi.py              # WSGI configuration
│   └── asgi.py              # ASGI configuration
├── requirements/            # Main application
│   ├── models.py            # Database models
│   ├── views.py             # View functions
│   ├── forms.py             # Form definitions
│   ├── urls.py              # Application URLs
│   ├── admin.py             # Admin configuration
│   ├── payment_service.py   # Payment service layer
│   ├── templatetags/        # Custom template tags
│   └── management/          # Custom management commands
│       └── commands/
├── templates/               # HTML templates
│   ├── base.html            # Base template
│   ├── components/          # Reusable components
│   ├── home.html            # Home page
│   ├── products.html        # Product listing
│   ├── cart.html            # Shopping cart
│   ├── checkout.html        # Checkout page
│   ├── order_list.html      # Order list
│   └── ...                  # Other templates
├── static/                  # Static files
│   ├── styles/              # CSS/SCSS files
│   ├── scripts/             # JavaScript files
│   └── images/              # Static images
├── media/                   # User-uploaded files
│   └── products/            # Product images
├── db.sqlite3               # SQLite database file
├── requirements.txt         # Python dependencies
├── manage.py                # Django management script
└── .env                     # Environment variables (create this)
```

## 🎮 Custom Management Commands

### Create Sample Data

```bash
python manage.py create_sample_data
```

### Add Products

```bash
python manage.py add_products
```

### Test Razorpay Integration

```bash
python manage.py test_razorpay
```

## 🚀 Production Deployment

### Pre-deployment Checklist

- [ ] Update Razorpay keys to live credentials
- [ ] Set `DEBUG = False` in environment variables
- [ ] Configure HTTPS
- [ ] Set up proper logging
- [ ] Test webhook endpoints
- [ ] Configure monitoring
- [ ] Set up database backups
- [ ] Update `ALLOWED_HOSTS` with production domain
- [ ] Configure email backend
- [ ] Set up CDN for static files (optional)
- [ ] Implement caching (Redis recommended)
- [ ] Set up error tracking

### Environment Variables for Production

```env
SECRET_KEY=your_production_secret_key
DEBUG=False
ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com
CSRF_TRUSTED_ORIGINS=https://yourdomain.com,https://www.yourdomain.com

RAZORPAY_KEY_ID=your_live_key_id
RAZORPAY_KEY_SECRET=your_live_key_secret
RAZORPAY_WEBHOOK_SECRET=your_live_webhook_secret

# Email Configuration
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password
DEFAULT_FROM_EMAIL=your-email@gmail.com
```

### Security Recommendations

1. **Change SECRET_KEY** - Generate a new secret key for production
2. **Set DEBUG = False** - Never run with debug mode in production
3. **Configure HTTPS** - Use SSL/TLS certificates
4. **Set up proper email backend** - Configure SMTP settings
5. **Database** - Consider using PostgreSQL or MySQL for production
6. **Static Files** - Use CDN or dedicated static file server
7. **Caching** - Implement Redis or Memcached
8. **Monitoring** - Set up error tracking (Sentry, etc.)

## 🔧 Troubleshooting

### Issue: ModuleNotFoundError for 'dotenv'

If you get an error about `dotenv` not being found, install it:

```bash
pip install python-dotenv
```

### Issue: PowerShell Execution Policy Error

If PowerShell blocks script execution, use Command Prompt or Git Bash instead, or run:

```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

### Issue: Database Errors

If you encounter database errors, try:

```bash
python manage.py makemigrations
python manage.py migrate
```

### Issue: Static Files Not Loading

Make sure the `static` directory exists and run:

```bash
python manage.py collectstatic
```

### Issue: "Invalid Key ID" Error (Razorpay)

- Check `RAZORPAY_KEY_ID` in `.env` file
- Ensure using correct test/live keys
- Verify keys are copied correctly without extra spaces

### Issue: Payment Verification Failed

- Verify `RAZORPAY_KEY_SECRET` is correct
- Check webhook signature validation
- Ensure webhook secret matches in Razorpay dashboard

### Issue: Order Not Found

- Ensure order creation before payment
- Check session management
- Verify database migrations are applied

## 📞 Contact Information

**KV Store**  
**Founder:** K.Vigneshar  
**Address:** SSN COLLEGE, Chennai  
**Phone:** +91 7397381106  
**Email:** kvigneshar@ssn.edu.in

### Adding Founder Image

To add the founder image:

1. Save your image file as `founder.jpg`
2. Place it in the `static/images/` folder
3. The image will automatically appear on the About page

**Image Requirements:**
- Format: JPG/JPEG
- Recommended size: 400x400 pixels or larger
- The image will be automatically resized and cropped to fit

## 📚 Additional Documentation

This project includes additional documentation files:

- **PAYMENT_INTEGRATION_GUIDE.md** - Detailed payment integration guide
- **PROJECT_ANALYSIS_REPORT.md** - Complete project analysis and bug fixes
- **IMAGE_INSTRUCTIONS.md** - Instructions for adding images
- **RESUME_PROJECT_DESCRIPTION.md** - Project description for resume/portfolio

## 📊 Project Statistics

- **15+** database models with complex relationships
- **50+** view functions handling various business logic
- **30+** HTML templates with reusable components
- **10+** custom management commands
- **365+** product images managed
- Comprehensive test suite for functionality validation

## 🎯 Key Achievements

- ✅ Successfully integrated third-party payment gateway with full error handling
- ✅ Implemented secure payment processing meeting industry standards
- ✅ Created scalable architecture supporting future feature additions
- ✅ Designed intuitive user interface with excellent mobile responsiveness
- ✅ Built comprehensive admin panel for efficient business operations
- ✅ Optimized for iPhone 14 Pro Max with modern CSS and JavaScript

## 🔐 Security Features

- Password hashing and validation
- CSRF token protection
- XSS protection headers
- Secure session cookies
- SQL injection prevention (Django ORM)
- Environment variable management for sensitive data
- HMAC signature verification for payments
- PCI DSS compliant (via Razorpay)

## 📝 Development Notes

- The project uses SQLite database by default (can be changed to PostgreSQL/MySQL)
- Debug mode is controlled by the `DEBUG` environment variable
- Razorpay integration requires valid API keys for payment processing
- Media files are stored in the `media/` directory
- Static files are served from the `static/` directory
- Custom template tags are available in `requirements/templatetags/`

## 🤝 Contributing

This is a personal project, but suggestions and improvements are welcome!

## 📄 License

This project is for educational and personal use.

---

**Built with ❤️ using Django**

For more information or support, please contact: kvigneshar@ssn.edu.in
