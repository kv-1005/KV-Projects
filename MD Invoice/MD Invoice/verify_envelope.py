import sys
import os
from io import BytesIO
from decimal import Decimal
import json
from datetime import datetime

# Add project root to sys.path
sys.path.insert(0, os.getcwd())

# Mock environment
os.environ['DATABASE_URL'] = 'sqlite:///:memory:'

import app as app_module
from app import app, generate_envelope_pdf, Company, Customer, Invoice

def verify_envelope():
    print(f"DEBUG: Importing from {app_module.__file__}")
    with app.app_context():
        # Create mock data
        company = Company(
            name="MAHADEVI & CO",
            address="I/462-1, National Nagar, Omalur (T.K)",
            city="Salem",
            state="Tamil Nadu",
            pincode="636455",
            phone="+91-9444201021",
            email="mahadevico@yahoo.in"
        )
        
        customer = Customer(
            name="Vigneshar K",
            address="No 12, Main Road, Anna Nagar",
            city="Chennai",
            state="Tamil Nadu",
            pincode="600040",
            phone="90000 12345"
        )
        
        invoice = Invoice(
            invoice_number="INV/25-26/089",
            invoice_date=datetime.now().date(),
            customer=customer,
            notes='{"main_address": "salem"}'
        )
        
        print("Generating professional envelope PDF...")
        pdf_buffer = generate_envelope_pdf(invoice, company, from_extra="DEPT: ACCOUNTS", to_extra="URGENT")
        
        output_path = "verify_envelope_final.pdf"
        with open(output_path, "wb") as f:
            f.write(pdf_buffer.getvalue())
        
        print(f"Professional Envelope PDF saved to {output_path}")

if __name__ == "__main__":
    verify_envelope()
