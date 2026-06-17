# Invoice & Offer Management System

A comprehensive business automation platform built with Python Flask, designed for small-to-medium enterprises with full GST compliance in India. The system digitizes and automates the complete billing and quotation workflow, including invoice generation, commercial offers, and delivery challan management.

## Features

### Core Features
- ✅ **Invoice Management** - Automated invoice generation with customizable templates, auto-increment invoice numbers, discount handling (percentage/amount-based), E-way bill integration
- ✅ **GST Calculation** - Intelligent automatic GST/IGST/CGST/SGST calculation based on interstate/intrastate transactions (determined by GSTIN analysis)
- ✅ **Offer/Quotation System** - Template-based offer generation with dynamic item listing, terms & conditions, payment terms, delivery, and warranty management
- ✅ **Delivery Challan Management** - Delivery note generation with item tracking, integrated with invoice system
- ✅ **Company Management** - Store company details with GSTIN, PAN, logo, bank details, multi-address support
- ✅ **Customer Management** - Customer database with GSTIN validation, multi-address support (main office, branch offices)
- ✅ **PDF Generation** - Multi-library PDF generation system (ReportLab, xhtml2pdf, WeasyPrint) with fallback mechanisms for reliable document export
- ✅ **User Authentication** - Role-based access control (Admin, Staff) with session management
- ✅ **Analytics Dashboard** - Real-time revenue tracking, invoice statistics, monthly/yearly financial summaries, customer-wise transaction analysis, visual charts
- ✅ **Payment Tracking** - Mark invoices as paid/unpaid/partially paid with payment status management
- ✅ **Email Integration** - Send invoices directly to customers via email
- ✅ **Multi-Signature System** - Support for multiple signatures with selection per invoice/offer
- ✅ **AI Chatbot Integration** - Context-aware chatbot for invoice queries with natural language processing
- ✅ **Activity Logging** - Comprehensive audit trail of all user actions (invoice creation, modification, deletion)

### Advanced Features
- 📋 **Purchase Orders** - Complete PO management with vendor support
- 📋 **Security Features** - CSRF protection, rate limiting, password hashing
- 📋 **QR Code Generation** - QR codes on invoices for quick verification
- 📋 **Cloud Deployment Ready** - Docker containerization, Railway deployment support

## Technology Stack

- **Backend**: Python 3.8+ with Flask, SQLAlchemy ORM
- **Database**: PostgreSQL (production), SQLite (development fallback)
- **Frontend**: HTML5, CSS3, Bootstrap 5, JavaScript, Jinja2 Templates
- **PDF Generation**: ReportLab, xhtml2pdf, WeasyPrint (multi-library fallback system)
- **Authentication**: Flask-Login with role-based access control
- **Forms**: Flask-WTF with WTForms
- **Deployment**: Docker, Gunicorn, Railway cloud platform
- **Other**: QR Code generation, Base64 image encoding, Pandas for data processing

## Installation & Setup

### Prerequisites
- Python 3.8 or higher
- pip (Python package installer)
- PostgreSQL (for production) or SQLite (for development)

### Environment Variables
Create a `.env` file in the project root (or copy from `env.example`):
```env
FLASK_ENV=development
SECRET_KEY=your-secret-key-here
DATABASE_URL=postgresql://user:password@localhost/invoice_db
# For development with SQLite, leave DATABASE_URL empty or use:
# DATABASE_URL=sqlite:///invoice_generator.db
```

### Quick Setup (Recommended)
```bash
# 1. Download/Clone the project
git clone <repository-url>
cd "MD Invoice"

# 2. Create virtual environment (recommended)
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# 3. Install Dependencies
pip install -r requirements.txt

# 4. Set up environment variables
cp env.example .env
# Edit .env with your configuration

# 5. Initialize Database
python init_db.py

# 6. Start the application
python run.py
```

### Manual Setup
```bash
# 1. Clone/Download the Project
git clone <repository-url>
cd "MD Invoice"

# 2. Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# 3. Install Dependencies
pip install -r requirements.txt

# 4. Create necessary directories
mkdir -p static/uploads templates/errors instance

# 5. Configure environment
cp env.example .env
# Edit .env file with your settings

# 6. Initialize Database
python init_db.py

# 7. Run the Application
python run.py
```

### Database Setup

**For Development (SQLite):**
- No additional setup required. SQLite database will be created automatically.

**For Production (PostgreSQL):**
```bash
# Create PostgreSQL database
createdb invoice_db

# Or using psql:
psql -U postgres
CREATE DATABASE invoice_db;

# Set DATABASE_URL in .env file
DATABASE_URL=postgresql://user:password@localhost/invoice_db
```

### First Login
- **Username**: `admin`
- **Password**: `admin123`

**⚠️ Important**: Change the default password after first login!

### Production Deployment

**Using Gunicorn:**
```bash
gunicorn --config gunicorn.conf.py wsgi:app
```

**Using Docker:**
```bash
# Build and run with docker-compose
docker-compose up -d

# Or build manually
docker build -t invoice-generator .
docker run -p 8000:8000 --env-file .env invoice-generator
```

**Deploying on Railway:**
1. Connect your GitHub repository to Railway
2. Set environment variables in Railway dashboard
3. Railway will automatically detect and deploy the application
4. See `RAILWAY_DEPLOYMENT_FINAL_GUIDE.md` for detailed instructions

## Quick Start Guide

### 1. Setup Company Details
1. Login to the application (default: `admin` / `admin123`)
2. Go to **Company** in the sidebar
3. Fill in your company details:
   - Company name, GSTIN, PAN
   - Complete address (billing and shipping)
   - Phone and email
   - Bank details (account number, IFSC, bank name)
   - Upload company logo (optional, recommended for professional invoices)

### 2. Add Customers
1. Go to **Customers** → **Add Customer**
2. Fill customer details:
   - Name, GSTIN (if B2B customer)
   - Complete address (supports multiple addresses)
   - Contact information (phone, email)
   - State (important for GST calculation)

### 3. Create Your First Invoice
1. Go to **Invoices** → **Create Invoice**
2. Select customer and set invoice date
3. Add items with:
   - Description, HSN/SAC code
   - Quantity and rate
   - Tax rate (0%, 5%, 12%, 18%, 28%)
   - Discount (optional, percentage or amount)
4. GST will be calculated automatically:
   - **Intra-state** (same state): CGST + SGST
   - **Inter-state** (different states): IGST
5. Add E-way bill reference (optional)
6. Download PDF or send via email

### 4. Create Commercial Offer/Quotation
1. Go to **Offers** → **Create Offer**
2. Similar to invoice creation but for quotations
3. Add terms & conditions, payment terms, delivery terms
4. Generate professional PDF offer document

### 5. Generate Delivery Challan
1. Go to **Delivery Challan** → **Create Challan**
2. Link to existing invoice or create standalone
3. Track delivery items and generate delivery note PDF

## GST Calculation Logic

The app automatically calculates GST based on Indian tax regulations:

- **Intra-state** (same state): CGST + SGST (50% each of total GST rate)
  - Example: 18% GST = 9% CGST + 9% SGST
- **Inter-state** (different states): IGST (100% of total GST rate)
  - Example: 18% GST = 18% IGST

**How it works:**
- The system extracts the state code from the GSTIN (first 2 digits after country code)
- Compares company GSTIN state code with customer GSTIN state code
- If same state → CGST + SGST
- If different state → IGST

**GST rates supported:** 0%, 5%, 12%, 18%, 28%

**Additional features:**
- Automatic discount calculation (before or after tax)
- SAC (Service Accounting Code) support for service invoices
- HSN (Harmonized System of Nomenclature) support for goods

## File Structure

```
MD Invoice/
├── app.py                      # Main Flask application file
├── config.py                   # Configuration (Development/Production/Testing)
├── requirements.txt            # Python dependencies
├── README.md                   # This file
├── run.py                      # Application entry point
├── wsgi.py                     # WSGI entry point for production
├── init_db.py                  # Database initialization script
├── chatbot_service.py          # AI chatbot service
├── dashboard_analytics.py      # Analytics and dashboard data
├── generate_pdf_railway.py     # PDF generation with multi-library fallback
├── docker-compose.yml          # Docker Compose configuration
├── Dockerfile                  # Docker configuration
├── gunicorn.conf.py            # Gunicorn configuration
├── .env                        # Environment variables (create from env.example)
├── templates/                  # Jinja2 HTML templates
│   ├── base.html
│   ├── login.html
│   ├── dashboard.html
│   ├── company.html
│   ├── customers.html
│   ├── invoices.html
│   ├── offers.html
│   ├── delivery_challan.html
│   └── ...
├── static/                     # Static files (CSS, JS, images)
│   ├── css/
│   ├── js/
│   └── uploads/               # Uploaded logos, signatures
├── instance/                   # Instance-specific files
└── invoice_generator.db        # SQLite database (development, created automatically)
```

## Database Models

- **User**: Staff authentication and roles (Admin, Staff)
- **Company**: Company profile with GST details, logo, bank information
- **Customer**: Customer database with GSTIN support, multi-address support
- **Invoice**: Invoice header with totals, status, payment tracking, E-way bill
- **InvoiceItem**: Individual line items for each invoice (HSN/SAC, quantity, rate, tax)
- **Offer**: Commercial offer/quotation management
- **OfferItem**: Items in offers/quotations
- **DeliveryChallan**: Delivery note/challan management
- **DeliveryChallanItem**: Items in delivery challans
- **Signature**: Multiple signature management for invoices/offers
- **ActivityLog**: Comprehensive audit trail of user actions
- **ChatbotConversation**: AI chatbot conversation history

## Security Features

- **Password Security**: Password hashing with Werkzeug (bcrypt)
- **CSRF Protection**: CSRF tokens on all forms via Flask-WTF
- **Rate Limiting**: API rate limiting to prevent abuse (Flask-Limiter)
- **Role-Based Access Control**: Admin and Staff roles with different permissions
- **Session Management**: Secure session management with Flask-Login
- **Security Headers**: X-Content-Type-Options, X-Frame-Options headers
- **Input Validation**: Comprehensive form validation with WTForms

## Advanced Features

### AI Chatbot
The system includes an AI-powered chatbot that can answer queries about:
- Invoice details and status
- Customer information
- System operations and help
- Natural language processing for user assistance

Access the chatbot from the dashboard or dedicated chatbot page.

### Activity Logging
All user actions are logged for audit purposes:
- Invoice creation, modification, deletion
- Customer management actions
- User login/logout
- System configuration changes

View activity logs from the dashboard or admin panel.

### Multi-Signature Support
- Upload multiple signatures
- Select signature per invoice/offer
- Support for authorized signatories
- Digital signature integration ready

### Analytics Dashboard
Real-time business insights:
- Revenue tracking (daily, monthly, yearly)
- Invoice statistics and trends
- Customer-wise transaction analysis
- Payment status overview
- GST collection summary
- Visual charts and graphs

## Customization

### Adding New GST Rates
Edit the tax rate dropdown in invoice templates:
```html
<select class="form-select" id="tax_rate">
    <option value="0">0%</option>
    <option value="5">5%</option>
    <option value="12">12%</option>
    <option value="18" selected>18%</option>
    <option value="28">28%</option>
    <!-- Add new rates here -->
</select>
```

### Modifying Invoice PDF
The PDF generation uses a multi-library fallback system:
- Primary: xhtml2pdf (HTML to PDF)
- Fallback 1: WeasyPrint
- Fallback 2: ReportLab (direct PDF generation)

Edit PDF templates in `templates/invoice_pdf.html` or modify `generate_pdf_railway.py` for advanced customization.

### Custom Invoice Templates
- Edit templates in `templates/` directory
- Modify CSS in `static/css/` for styling
- PDF templates use Jinja2 for dynamic content

## Troubleshooting

### Common Issues

1. **Port already in use**
   ```bash
   # Change port in app.py
   app.run(debug=True, port=5001)
   ```

2. **Database errors**
   ```bash
   # Delete the database file and restart
   rm invoice_generator.db
   python app.py
   ```

3. **PDF generation issues**
   - Ensure ReportLab is installed: `pip install ReportLab`
   - Check file permissions in the project directory

### Getting Help

1. Check the console output for error messages
2. Ensure all dependencies are installed correctly
3. Verify Python version (3.8+ required)

## Development

### Adding New Features

1. **Database Changes**: Modify models in `app.py`
2. **New Pages**: Add routes and templates
3. **Forms**: Create new forms using Flask-WTF
4. **PDF**: Extend ReportLab functionality

### Code Structure

- **Routes**: All URL endpoints in `app.py`
- **Models**: Database models defined in `app.py`
- **Forms**: WTForms classes for form handling
- **Templates**: Jinja2 templates in `templates/` folder

## License

This project is open source and available under the MIT License.

## Support

For support and feature requests, please create an issue in the project repository.

---

**Built with ❤️ for Indian businesses**
