#!/usr/bin/env python3
"""
Database initialization script for Invoice Generator
Run this script to create the database and add sample data
"""

import os
import sys
from datetime import datetime, date
from werkzeug.security import generate_password_hash

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import app, db, User, Company, Customer, Invoice, InvoiceItem, Vendor, PurchaseOrder, PurchaseOrderItem

def create_tables():
    """Create all database tables"""
    print("Creating database tables...")
    with app.app_context():
        db.create_all()
        print("✓ Database tables created successfully")

def create_default_admin():
    """Create default admin user"""
    print("Creating default admin user...")
    with app.app_context():
        # Check if admin user already exists
        admin = User.query.filter_by(username='admin').first()
        if not admin:
            admin = User(
                username='admin',
                email='admin@company.com',
                role='admin',
                is_active=True
            )
            admin.set_password(os.environ.get('DEFAULT_ADMIN_PASSWORD', 'admin123'))
            db.session.add(admin)
            db.session.commit()
            admin_password = os.environ.get('DEFAULT_ADMIN_PASSWORD', 'admin123')
            print("✓ Default admin user created")
            print("  Username: admin")
            print(f"  Password: {admin_password}")
            print("  ⚠️  Please change the password after first login!")
        else:
            print("✓ Admin user already exists")

def create_sample_company():
    """Create sample company data"""
    print("Creating sample company...")
    with app.app_context():
        company = Company.query.first()
        if not company:
            company = Company(
                name='MAHADEVI&CO',
                gstin='33AAMFM2845D1ZG',
                pan='AAMFM2845D',
                address='1/462-1, National Nagar, Alangar Thetre Back side, Omalur (T.K), Salem (D.T) 636 455',
                city='Salem',
                state='Tamil Nadu',
                pincode='636455',
                phone='+91-4290 796930, +91-9444201021',
                email='mahadevico@yahoo.in, mahadevico77@gmail.com'
            )
            db.session.add(company)
            db.session.commit()
            print("✓ Sample company created")
        else:
            print("✓ Company already exists")

def create_sample_customers():
    """Create sample customer data"""
    print("Creating sample customers...")
    with app.app_context():
        if Customer.query.count() == 0:
            customers = [
                Customer(
                    name='ABC Enterprises',
                    gstin='27BBBBB0000B1Z6',
                    address='456 Corporate Avenue, Business District',
                    city='Pune',
                    state='Maharashtra',
                    pincode='411001',
                    phone='+91 9876543211',
                    email='contact@abcenterprises.com'
                ),
                Customer(
                    name='XYZ Solutions',
                    gstin='33CCCCC0000C1Z7',
                    address='789 Innovation Hub, IT Park',
                    city='Bangalore',
                    state='Karnataka',
                    pincode='560001',
                    phone='+91 9876543212',
                    email='info@xyzsolutions.com'
                ),
                Customer(
                    name='John Doe',
                    address='321 Residential Area, Downtown',
                    city='Delhi',
                    state='Delhi',
                    pincode='110001',
                    phone='+91 9876543213',
                    email='john.doe@email.com'
                )
            ]
            
            for customer in customers:
                db.session.add(customer)
            
            db.session.commit()
            print(f"✓ Created {len(customers)} sample customers")
        else:
            print("✓ Customers already exist")

def create_sample_invoices():
    """Create sample invoice data"""
    print("Creating sample invoices...")
    with app.app_context():
        if Invoice.query.count() == 0:
            company = Company.query.first()
            customers = Customer.query.all()
            
            if company and customers:
                # Create sample invoice
                from datetime import timedelta
                invoice = Invoice(
                    invoice_number='INV-0001',
                    customer_id=customers[0].id,
                    company_id=company.id,
                    invoice_date=date.today(),
                    due_date=date.today() + timedelta(days=30),
                    subtotal=10000.00,
                    discount_amount=1000.00,
                    cgst_amount=810.00,
                    sgst_amount=810.00,
                    igst_amount=0.00,
                    shipping_charges=200.00,
                    total_amount=9820.00,
                    status='unpaid',
                    notes='Thank you for your business!'
                )
                db.session.add(invoice)
                db.session.flush()  # Get the invoice ID
                
                # Add sample items
                items = [
                    InvoiceItem(
                        invoice_id=invoice.id,
                        description='Web Development Services',
                        quantity=40.0,
                        unit_price=200.00,
                        tax_rate=18.0,
                        amount=8000.00
                    ),
                    InvoiceItem(
                        invoice_id=invoice.id,
                        description='Domain Registration',
                        quantity=1.0,
                        unit_price=1000.00,
                        tax_rate=18.0,
                        amount=1000.00
                    ),
                    InvoiceItem(
                        invoice_id=invoice.id,
                        description='SSL Certificate',
                        quantity=1.0,
                        unit_price=1000.00,
                        tax_rate=18.0,
                        amount=1000.00
                    )
                ]
                
                for item in items:
                    db.session.add(item)
                
                db.session.commit()
                print("✓ Created sample invoice with items")
            else:
                print("⚠️  Cannot create sample invoice - missing company or customers")
        else:
            print("✓ Invoices already exist")

def main():
    """Main initialization function"""
    print("=" * 50)
    print("Invoice Generator - Database Initialization")
    print("=" * 50)
    
    try:
        # Create tables
        create_tables()
        
        # Create default data
        create_default_admin()
        create_sample_company()
        create_sample_customers()
        create_sample_invoices()
        
        print("\n" + "=" * 50)
        print("✓ Database initialization completed successfully!")
        print("=" * 50)
        print("\nNext steps:")
        print("1. Run the application: python app.py")
        print("2. Open http://localhost:5000 in your browser")
        print("3. Login with: admin / A=!P}5c|.zu<)VV/")
        print("4. Change the default password")
        print("5. Update company details")
        print("\nHappy invoicing! 🎉")
        
    except Exception as e:
        print(f"\n❌ Error during initialization: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()
