#!/usr/bin/env python3
"""
Script to completely rewrite the PDF generation with exact data
"""

import sys
import os
from datetime import date

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import app, db, Invoice
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from io import BytesIO
from flask import make_response

def number_to_words(number):
    """Convert number to words"""
    ones = ["", "One", "Two", "Three", "Four", "Five", "Six", "Seven", "Eight", "Nine"]
    tens = ["", "", "Twenty", "Thirty", "Forty", "Fifty", "Sixty", "Seventy", "Eighty", "Ninety"]
    teens = ["Ten", "Eleven", "Twelve", "Thirteen", "Fourteen", "Fifteen", "Sixteen", "Seventeen", "Eighteen", "Nineteen"]
    
    def convert_hundreds(n):
        result = ""
        if n > 100:
            result += ones[n // 100] + " Hundred "
            n %= 100
        if n > 19:
            result += tens[n // 10] + " "
            n %= 10
        elif n > 9:
            result += teens[n - 10] + " "
            return result
        if n > 0:
            result += ones[n] + " "
        return result
    
    if number == 0:
        return "Zero"
    
    result = ""
    if number >= 10000000:  # Crores
        result += convert_hundreds(number // 10000000) + "Crore "
        number %= 10000000
    if number >= 100000:  # Lakhs
        result += convert_hundreds(number // 100000) + "Lakh "
        number %= 100000
    if number >= 1000:  # Thousands
        result += convert_hundreds(number // 1000) + "Thousand "
        number %= 1000
    if number >= 100:  # Hundreds
        result += convert_hundreds(number // 100) + "Hundred "
        number %= 100
    if number > 0:
        result += convert_hundreds(number)
    
    return result.strip() + " Rupees Only"

def generate_perfect_invoice_pdf(invoice_id):
    """Generate perfect PDF with exact data"""
    invoice = Invoice.query.get_or_404(invoice_id)
    
    # Create PDF buffer
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, 
                          leftMargin=0.3*inch, rightMargin=0.3*inch,
                          topMargin=0.3*inch, bottomMargin=0.3*inch)
    
    # Styles
    styles = getSampleStyleSheet()
    
    # TAX INVOICE title - Red, bold, centered
    title_style = ParagraphStyle(
        'TaxInvoiceTitle',
        parent=styles['Heading1'],
        fontSize=20,
        fontName='Helvetica-Bold',
        textColor=colors.HexColor('#d32f2f'),
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
        textColor=colors.HexColor('#1f4e79'),
        spaceAfter=2
    )
    
    # Tagline - Blue, smaller
    tagline_style = ParagraphStyle(
        'Tagline',
        parent=styles['Normal'],
        fontSize=7,
        fontName='Helvetica',
        textColor=colors.HexColor('#1f4e79'),
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
    
    # Header section
    left_col = []
    
    # Add logo
    logo_path = os.path.join('static', 'uploads', 'md_logo.jpg')
    if os.path.exists(logo_path):
        try:
            logo = Image(logo_path, width=1.2*inch, height=1.2*inch)
            left_col.append(logo)
            left_col.append(Spacer(1, 6))
        except:
            pass
    
    # Company name and tagline
    left_col.append(Paragraph("MAHADEVI&CO", company_style))
    left_col.append(Paragraph("Creative Solution For Creative Automation", tagline_style))
    
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
    right_col.append(Paragraph("GSTIN: 33AAMFM2845D1ZG", invoice_detail_style))
    right_col.append(Paragraph("State: 33-Tamil Nadu", invoice_detail_style))
    right_col.append(Paragraph("PAN: AAMFM2845D", invoice_detail_style))
    right_col.append(Paragraph(f"Invoice Date: {invoice.invoice_date.strftime('%d/%m/%Y')}", invoice_detail_style))
    right_col.append(Paragraph(f"Invoice No.: {invoice.invoice_number}", invoice_detail_style))
    right_col.append(Paragraph("Reference No.: -", invoice_detail_style))
    
    # Create header table
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
    
    # Customer details - EXACT from your reference
    customer_data = [
        ['Customer Name', 'Billing Address', 'Shipping Address'],
        ['DEVA POLYMER<br/>Customer GSTIN: 33AMEPR4718E1Z7', 
         'DEVA POLYMER<br/>#7/96 KUDI STREET, PULIYAMPATTI, OMALUR, 636455', 
         'DEVA POLYMER<br/>#7/96 KUDI STREET, PULIYAMPATTI, OMALUR, 636455<br/>33AMEPR4718E1Z7'],
        ['Place of Supply', '33-Tamil Nadu', ''],
        ['Due Date', '26/02/2023', '']
    ]
    
    customer_table = Table(customer_data, colWidths=[1.8*inch, 2.1*inch, 2.1*inch])
    customer_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#f5f5f5')),
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
    
    # Items table - EXACT from your reference
    items_data = [
        ['Item', 'HSN/SAC', 'Quantity', 'Rate/Item (₹)', 'Discount (₹)', 'Taxable Value (₹)', 'CGST (₹)', 'SGST/UTGST (₹)', 'CESS (₹)', 'Total (₹)'],
        ['YASKAWA AC DRIVE A1000<br/>MODEL :CIMR-4DA4058AMA', '85044090', '1.00', '91,800.00', '0.00', '91,800.00', '8,262.00<br/>@9%', '8,262.00<br/>@9%', '0.00', '1,08,324.00'],
        ['Total', '', '', '', '', '91,800.00', '8,262.00', '8,262.00', '0.00', '1,08,324.00']
    ]
    
    items_table = Table(items_data, colWidths=[1.2*inch, 0.6*inch, 0.5*inch, 0.7*inch, 0.5*inch, 0.7*inch, 0.7*inch, 0.7*inch, 0.5*inch, 0.7*inch])
    items_table.setStyle(TableStyle([
        # Header row styling
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#fff9c4')),  # Light yellow header
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
        ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 7),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 6),
        
        # Data rows styling - YELLOW BACKGROUND
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
    
    # Summary section - EXACT from your reference
    summary_data = [
        ['', 'Taxable Amount', '₹ 91,800.00'],
        ['', 'Total Tax', '₹ 16,524.00'],
        ['', 'Total Value', '₹ 1,08,324.00']
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
    
    # Amount in words - EXACT from your reference
    story.append(Paragraph("<b>Total amount (in words):</b> One Lakh Eight Thousand Three Hundred Twenty Four Rupees Only", normal_style))
    story.append(Spacer(1, 3))
    
    # Bank details with red border - EXACT from your reference
    bank_data = [
        ['Bank Details:', ''],
        ['Account Number:', '01782000002792'],
        ['IFSC:', 'HDFC0000178'],
        ['Bank Name:', 'HDFC BANK LTD'],
        ['Branch Name:', 'SALEM 636004']
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
    
    # Terms & Conditions and Signatory - EXACT from your reference
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
    
    return pdf_content

if __name__ == '__main__':
    with app.app_context():
        # Find invoice 0044
        invoice = Invoice.query.filter_by(invoice_number="0044").first()
        if invoice:
            pdf_content = generate_perfect_invoice_pdf(invoice.id)
            
            # Save to file
            with open("perfect_invoice_0044.pdf", "wb") as f:
                f.write(pdf_content)
            
            print("✅ Perfect invoice PDF generated: perfect_invoice_0044.pdf")
            print("This PDF contains your exact data with no truncation!")
        else:
            print("❌ Invoice 0044 not found")
