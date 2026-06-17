from app import app, generate_envelope_pdf, Company, Invoice, Customer
from io import BytesIO

def verify_envelope_fix():
    print("Verifying Professional Envelope Fix...")
    with app.app_context():
        # Setup dummy data
        company = Company.query.first()
        customer = Customer(name="JSW STEEL LTD POTTANERI", 
                           address="Mecheri (TK) Salem-, Tamilnadu- India",
                           city="Salem", 
                           state="TAMIL NADU", 
                           pincode="636453",
                           phone="04298272584")
        
        invoice = Invoice(invoice_number="TEST-001")
        invoice.customer = customer
        invoice.notes = "" # Empty notes
        
        print(f"Generating envelope for: {customer.name}")
        pdf_buffer = generate_envelope_pdf(invoice, company)
        
        output_path = "verify_envelope_professional_v2.pdf"
        with open(output_path, "wb") as f:
            f.write(pdf_buffer.getvalue())
        
        print(f"Success! Professional envelope generated at: {output_path}")
        print("Please check the PDF for Landscape orientation and clean address (no duplicate Salem/India).")

if __name__ == "__main__":
    verify_envelope_fix()
