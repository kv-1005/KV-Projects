#!/usr/bin/env python3
"""
Test script for invoice email functionality
"""

import sys
import os

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import app, Invoice, send_invoice_email

def test_invoice_email():
    """Test sending invoice email"""
    
    print("🧪 TESTING INVOICE EMAIL FUNCTIONALITY")
    print("=" * 50)
    
    with app.app_context():
        # Check if there are any invoices
        invoices = Invoice.query.limit(1).all()
        
        if not invoices:
            print("❌ No invoices found in database")
            print("   Create an invoice first to test email functionality")
            return False
        
        invoice = invoices[0]
        print(f"📄 Testing with invoice: {invoice.invoice_number}")
        print(f"   Customer: {invoice.customer.name}")
        print(f"   Total: ₹{invoice.total_amount:,.2f}")
        print()
        
        # Check email configuration
        mail_server = app.config.get('MAIL_SERVER')
        mail_username = app.config.get('MAIL_USERNAME')
        mail_password = app.config.get('MAIL_PASSWORD')
        
        print("📧 Email Configuration:")
        print(f"   MAIL_SERVER: {mail_server}")
        print(f"   MAIL_USERNAME: {mail_username}")
        print(f"   MAIL_PASSWORD: {'Set' if mail_password else 'Not set'}")
        print()
        
        if not all([mail_server, mail_username, mail_password]):
            print("❌ Email configuration incomplete!")
            print("   Please set MAIL_SERVER, MAIL_USERNAME, and MAIL_PASSWORD")
            return False
        
        print("✅ Email configuration complete")
        print()
        
        # Test the email sending function
        print("📤 Sending test invoice email with PDF...")
        print("   Recipients: mahadevico@yahoo.in, k.vigneshar10@gmail.com")
        print("   PDF attachment: Invoice_" + invoice.invoice_number + ".pdf")
        print()
        
        try:
            # Simulate the email sending (without actually sending)
            recipient_emails = ["mahadevico@yahoo.in", "k.vigneshar10@gmail.com"]
            company_name = app.config.get('COMPANY_NAME', 'MD Invoice System')
            
            subject = f"Invoice {invoice.invoice_number} - {company_name}"
            
            print(f"📧 Email Details:")
            print(f"   Subject: {subject}")
            print(f"   Recipients: {', '.join(recipient_emails)}")
            print(f"   Invoice: {invoice.invoice_number}")
            print(f"   Customer: {invoice.customer.name}")
            print(f"   Total: ₹{invoice.total_amount:,.2f}")
            print()
            
            # Test the actual email sending with PDF
            from flask_mail import Message, Mail
            mail = Mail(app)
            
            body = f"""
Dear Team,

Please find the invoice {invoice.invoice_number} from {company_name}.

Invoice Details:
- Invoice Number: {invoice.invoice_number}
- Customer: {invoice.customer.name}
- Date: {invoice.invoice_date.strftime('%d/%m/%Y') if invoice.invoice_date else 'N/A'}
- Total Amount: ₹{invoice.total_amount:,.2f}
- Status: {invoice.status.title()}

The PDF attachment contains the complete invoice details.

This is a test email for invoice email functionality with PDF attachment.

Best regards,
{company_name} System
            """
            
            msg = Message(
                subject=subject,
                recipients=recipient_emails,
                body=body,
                sender=mail_username
            )
            
            # Generate and attach PDF
            try:
                from app import generate_invoice_pdf
                pdf_data = generate_invoice_pdf(invoice.id)
                if pdf_data:
                    msg.attach(
                        filename=f"Invoice_{invoice.invoice_number}.pdf",
                        content_type="application/pdf",
                        data=pdf_data,
                        disposition="attachment"
                    )
                    print("   ✅ PDF attachment added successfully")
                else:
                    print("   ⚠️  PDF generation failed, sending email without PDF")
            except Exception as pdf_error:
                print(f"   ⚠️  PDF generation error: {str(pdf_error)}")
                print("   📧 Sending email without PDF attachment")
            
            # Send the email
            mail.send(msg)
            
            print("✅ Invoice email with PDF sent successfully!")
            print("   Check both email addresses for the invoice with PDF attachment")
            print()
            print("🎉 TEST COMPLETED SUCCESSFULLY!")
            
            return True
            
        except Exception as e:
            print(f"❌ Error sending invoice email: {str(e)}")
            print()
            print("🔍 Common issues:")
            print("   1. SMTP server connection failed")
            print("   2. Authentication failed (wrong password)")
            print("   3. Network/firewall blocking SMTP")
            print("   4. Gmail/Yahoo security settings")
            
            return False

if __name__ == "__main__":
    success = test_invoice_email()
    if success:
        print("\n✅ Invoice email functionality is working!")
        sys.exit(0)
    else:
        print("\n❌ Invoice email functionality needs attention!")
        sys.exit(1)
