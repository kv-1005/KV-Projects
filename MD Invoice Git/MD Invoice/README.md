# Invoice Generator App

A comprehensive invoice management system built with Python Flask, designed for small businesses with GST compliance in India.

## Features

### Core Features (MVP)
- ✅ **Invoice Creation** - Auto-increment invoice numbers, add products/services
- ✅ **GST Calculation** - Automatic GST/IGST/CGST/SGST calculation
- ✅ **Company Management** - Store company details with GSTIN, PAN, logo
- ✅ **Customer Management** - Customer database with GSTIN support
- ✅ **PDF Generation** - Professional invoice PDFs with ReportLab
- ✅ **User Authentication** - Role-based access (Admin, Staff)
- ✅ **Dashboard** - Overview of invoices, customers, and revenue

### Intermediate Features (Planned)
- 🔄 **Payment Tracking** - Mark invoices as paid/unpaid/partially paid
- 🔄 **Email Integration** - Send invoices directly to customers
- 🔄 **Advanced Reports** - Sales reports, GST reports, customer analytics
- 🔄 **Invoice Templates** - Multiple invoice designs and layouts

### Advanced Features (Future)
- 📋 **Recurring Invoices** - Auto-generate for subscription customers
- 📋 **Multi-Currency** - Support for different currencies
- 📋 **Backup & Export** - Data backup and migration tools

## Technology Stack

- **Backend**: Python 3.8+ with Flask
- **Database**: SQLite (file-based, no server setup)
- **Frontend**: HTML5, CSS3, Bootstrap 5, JavaScript
- **PDF Generation**: ReportLab
- **Authentication**: Flask-Login
- **Forms**: Flask-WTF with WTForms

## Installation & Setup

### Prerequisites
- Python 3.8 or higher
- pip (Python package installer)

### Quick Setup (Recommended)
```bash
# 1. Download/Clone the project
git clone <repository-url>
cd invoice-generator

# 2. Run the automated setup script
python setup.py

# 3. Start the application
python run.py
```

### Manual Setup
```bash
# 1. Clone/Download the Project
git clone <repository-url>
cd invoice-generator

# 2. Install Dependencies
pip install -r requirements.txt

# 3. Create necessary directories
mkdir -p static/uploads templates/errors

# 4. Initialize Database
python init_db.py

# 5. Run the Application
python run.py
```

### First Login
- **Username**: `admin`
- **Password**: `admin123`

**⚠️ Important**: Change the default password after first login!

### Production Deployment
```bash
# Using Gunicorn
gunicorn --config gunicorn.conf.py wsgi:app

# Using Docker
docker-compose up

# Using Docker build
docker build -t invoice-generator .
docker run -p 8000:8000 invoice-generator
```

## Quick Start Guide

### 1. Setup Company Details
1. Login to the application
2. Go to **Company** in the sidebar
3. Fill in your company details:
   - Company name, GSTIN, PAN
   - Complete address
   - Phone and email
   - Upload company logo (optional)

### 2. Add Customers
1. Go to **Customers** → **Add Customer**
2. Fill customer details:
   - Name, GSTIN (if B2B)
   - Complete address
   - Contact information

### 3. Create Your First Invoice
1. Go to **Invoices** → **Create Invoice**
2. Select customer and set dates
3. Add items with quantities and rates
4. GST will be calculated automatically
5. Download PDF or print

## GST Calculation Logic

The app automatically calculates GST based on:

- **Intra-state** (same state): CGST + SGST (50% each of total GST)
- **Inter-state** (different states): IGST (100% of total GST)

GST rates supported: 0%, 5%, 12%, 18%, 28%

## File Structure

```
invoice-generator/
├── app.py                 # Main application file
├── requirements.txt       # Python dependencies
├── README.md             # This file
├── templates/            # HTML templates
│   ├── base.html
│   ├── login.html
│   ├── dashboard.html
│   ├── company.html
│   ├── customers.html
│   ├── invoices.html
│   └── ...
├── static/               # CSS, JS, images
└── invoice_generator.db  # SQLite database (created automatically)
```

## Database Models

- **User**: Staff authentication and roles
- **Company**: Single company profile with GST details
- **Customer**: Customer database with GSTIN support
- **Invoice**: Invoice header with totals and status
- **InvoiceItem**: Individual line items for each invoice

## Security Features

- Password hashing with Werkzeug
- CSRF protection on forms
- Role-based access control
- Session management with Flask-Login

## Customization

### Adding New GST Rates
Edit the tax rate dropdown in `templates/edit_invoice.html`:
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
Edit the PDF generation code in `app.py` around line 400 in the `invoice_pdf` function.

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
