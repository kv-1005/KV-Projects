#!/usr/bin/env python3
"""
Script to create the exact invoice with your provided data
"""

import sys
import os
from datetime import date, timedelta

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import app, db, Customer, Invoice, InvoiceItem, Company

def create_exact_invoice():
    """Create the exact invoice with your provided data"""
    print("Creating exact invoice with your data...")
    
    with app.app_context():
        # Get or create company
        company = Company.query.first()
        if not company:
            print("❌ Company not found. Please run init_db.py first.")
            return
        
        # Create DEVA POLYMER customer
        customer = Customer.query.filter_by(name="DEVA POLYMER").first()
        if not customer:
            customer = Customer(
                name="DEVA POLYMER",
                email="deva@example.com",
                phone="1234567890",
                address="#7/96 KUDI STREET, PULIYAMPATTI, OMALUR, 636455",
                city="OMALUR",
                state="Tamil Nadu",
                pincode="636455",
                gstin="33AMEPR4718E1Z7"
            )
            db.session.add(customer)
            db.session.flush()
            print("✓ Created DEVA POLYMER customer")
        else:
            print("✓ DEVA POLYMER customer already exists")
        
        # Create the exact invoice
        invoice = Invoice(
            invoice_number="MD2526-0044",
            customer_id=customer.id,
            company_id=company.id,
            invoice_date=date(2023, 2, 25),  # 25/02/2023
            due_date=date(2023, 2, 26),      # 26/02/2023
            subtotal=91800.00,
            discount_amount=0.00,
            cgst_amount=8262.00,
            sgst_amount=8262.00,
            igst_amount=0.00,
            shipping_charges=0.00,
            total_amount=108324.00,
            status='unpaid',
            notes='Thank you for your business!'
        )
        db.session.add(invoice)
        db.session.flush()  # Get the invoice ID
        
        # Add the exact item
        item = InvoiceItem(
            invoice_id=invoice.id,
            description="YASKAWA AC DRIVE A1000 MODEL :CIMR-4DA4058AMA",
            hsn_code="85044090",
            quantity=1.00,
            unit_price=91800.00,
            amount=91800.00,
            tax_rate=18.0  # 9% CGST + 9% SGST
        )
        db.session.add(item)
        
        # Commit all changes
        db.session.commit()
        
        print("✓ Created exact invoice with:")
        print(f"  - Invoice Number: {invoice.invoice_number}")
        print(f"  - Customer: {customer.name}")
        print(f"  - Item: {item.description}")
        print(f"  - Amount: ₹{invoice.total_amount}")
        print(f"  - Date: {invoice.invoice_date.strftime('%d/%m/%Y')}")
        print(f"  - Due Date: {invoice.due_date.strftime('%d/%m/%Y')}")
        
        return invoice.id

if __name__ == '__main__':
    try:
        invoice_id = create_exact_invoice()
        print(f"\n🎉 Success! Invoice ID: {invoice_id}")
        print("\nTo view the invoice:")
        print("1. Go to http://localhost:5000")
        print("2. Login with admin/admin123")
        print("3. Go to Invoices")
        print("4. Click on invoice 0044")
        print("5. Click 'Generate PDF' to see the perfect result!")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)
