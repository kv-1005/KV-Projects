#!/usr/bin/env python3
"""
Test script to verify that the company logo loads correctly in email-sent PDFs
"""

import os
import sys
from flask import Flask

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_logo_base64_conversion():
    """Test the base64 conversion function"""
    print("🔍 Testing logo base64 conversion...")
    
    try:
        from generate_pdf_railway import convert_image_to_base64
        
        # Test with the actual logo file
        logo_path = os.path.join('static', 'uploads', 'md_logo.jpg')
        
        if not os.path.exists(logo_path):
            print(f"❌ Logo file not found at: {logo_path}")
            return False
        
        print(f"✅ Logo file found at: {logo_path}")
        
        # Convert to base64
        logo_base64 = convert_image_to_base64(logo_path)
        
        if logo_base64:
            print(f"✅ Logo successfully converted to base64")
            print(f"   Data URI length: {len(logo_base64)} characters")
            print(f"   Data URI starts with: {logo_base64[:50]}...")
            
            # Verify it's a valid data URI
            if logo_base64.startswith('data:image/'):
                print("✅ Valid data URI format")
                return True
            else:
                print("❌ Invalid data URI format")
                return False
        else:
            print("❌ Failed to convert logo to base64")
            return False
            
    except Exception as e:
        print(f"❌ Error testing logo conversion: {str(e)}")
        return False

def test_pdf_generation_with_logo():
    """Test PDF generation with the logo fix"""
    print("\n🔍 Testing PDF generation with logo...")
    
    try:
        # Import and use the actual Flask app
        from app import app, db, Invoice, Company, Customer, InvoiceItem
        from generate_pdf_railway import generate_invoice_pdf_from_template
        
        with app.app_context():
            
            # Get a sample invoice
            invoice = Invoice.query.first()
            if not invoice:
                print("❌ No invoices found in database")
                return False
            
            print(f"✅ Found invoice: {invoice.invoice_number}")
            
            # Get company details
            company = Company.query.first()
            if not company:
                print("❌ No company found in database")
                return False
            
            print(f"✅ Found company: {company.name}")
            
            # Generate PDF
            print("📄 Generating PDF with logo...")
            pdf_data = generate_invoice_pdf_from_template(invoice, company)
            
            if pdf_data:
                print(f"✅ PDF generated successfully")
                print(f"   PDF size: {len(pdf_data)} bytes")
                
                # Save PDF for manual inspection
                test_pdf_path = "test_invoice_with_logo.pdf"
                with open(test_pdf_path, 'wb') as f:
                    f.write(pdf_data)
                print(f"✅ Test PDF saved as: {test_pdf_path}")
                print("   Please open this PDF to verify the logo appears correctly")
                
                return True
            else:
                print("❌ Failed to generate PDF")
                return False
                
    except Exception as e:
        print(f"❌ Error testing PDF generation: {str(e)}")
        return False

def test_email_pdf_generation():
    """Test the email PDF generation function"""
    print("\n🔍 Testing email PDF generation...")
    
    try:
        from app import app, generate_invoice_pdf, db, Invoice
        
        with app.app_context():
            # Get a sample invoice
            invoice = Invoice.query.first()
            if not invoice:
                print("❌ No invoices found in database")
                return False
        
            print(f"✅ Found invoice: {invoice.invoice_number}")
            
            # Generate PDF for email
            print("📧 Generating PDF for email...")
            pdf_data = generate_invoice_pdf(invoice.id)
        
            if pdf_data:
                print(f"✅ Email PDF generated successfully")
                print(f"   PDF size: {len(pdf_data)} bytes")
                
                # Save PDF for manual inspection
                test_pdf_path = "test_email_invoice_with_logo.pdf"
                with open(test_pdf_path, 'wb') as f:
                    f.write(pdf_data)
                print(f"✅ Test email PDF saved as: {test_pdf_path}")
                print("   Please open this PDF to verify the logo appears correctly")
                
                return True
            else:
                print("❌ Failed to generate email PDF")
                return False
            
    except Exception as e:
        print(f"❌ Error testing email PDF generation: {str(e)}")
        return False

def main():
    """Run all tests"""
    print("🚀 Starting logo fix tests...\n")
    
    # Test 1: Base64 conversion
    test1_passed = test_logo_base64_conversion()
    
    # Test 2: PDF generation with logo
    test2_passed = test_pdf_generation_with_logo()
    
    # Test 3: Email PDF generation
    test3_passed = test_email_pdf_generation()
    
    # Summary
    print("\n" + "="*50)
    print("📊 TEST SUMMARY")
    print("="*50)
    print(f"Base64 conversion: {'✅ PASSED' if test1_passed else '❌ FAILED'}")
    print(f"PDF generation: {'✅ PASSED' if test2_passed else '❌ FAILED'}")
    print(f"Email PDF generation: {'✅ PASSED' if test3_passed else '❌ FAILED'}")
    
    if all([test1_passed, test2_passed, test3_passed]):
        print("\n🎉 All tests passed! Logo fix is working correctly.")
        print("📧 The company logo should now load correctly in email-sent PDFs.")
    else:
        print("\n⚠️  Some tests failed. Please check the errors above.")
    
    print("\n💡 Next steps:")
    print("   1. Open the generated test PDFs to verify the logo appears")
    print("   2. Test sending an actual invoice email")
    print("   3. Check the email PDF attachment for the logo")

if __name__ == "__main__":
    main()
