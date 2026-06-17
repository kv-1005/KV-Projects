"""
PDF generation functions compatible with Railway deployment
Uses ReportLab instead of Selenium to avoid Chrome dependencies
"""

from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from io import BytesIO
from decimal import Decimal
from datetime import datetime
import tempfile
import os
from flask import render_template
import subprocess
import base64


def apply_digital_signature(pdf_bytes, pfx_data_base64=None, password=None, signer_name="Authorised Signatory", reason="Digitally Signed"):
    """
    Applies a cryptographic digital signature to a PDF.
    This is a stub implementation. To fully implement cryptographic PDF signing,
    a library like 'pyHanko' or 'endesive' would be required.
    For now, it returns the original PDF.
    """
    print(f"Applying digital signature for {signer_name} (stub)")
    return pdf_bytes

def convert_image_to_base64(image_path):
    """Convert image file to base64 data URI for embedding in HTML"""
    try:
        if not os.path.exists(image_path):
            print(f"Image file not found: {image_path}")
            return None
        
        with open(image_path, 'rb') as image_file:
            image_data = image_file.read()
            base64_data = base64.b64encode(image_data).decode('utf-8')
            
            # Determine file extension for MIME type
            file_ext = os.path.splitext(image_path)[1].lower()
            mime_types = {
                '.jpg': 'image/jpeg',
                '.jpeg': 'image/jpeg',
                '.png': 'image/png',
                '.gif': 'image/gif',
                '.bmp': 'image/bmp',
                '.webp': 'image/webp'
            }
            
            mime_type = mime_types.get(file_ext, 'image/jpeg')
            data_uri = f"data:{mime_type};base64,{base64_data}"
            
            print(f"Successfully converted image to base64 data URI (length: {len(data_uri)})")
            return data_uri
            
    except Exception as e:
        print(f"Error converting image to base64: {str(e)}")
        return None


def number_to_words(number):
    """
    Convert number to words
    """
    ones = ["", "One", "Two", "Three", "Four", "Five", "Six", "Seven", "Eight", "Nine"]
    tens = ["", "Ten", "Twenty", "Thirty", "Forty", "Fifty", "Sixty", "Seventy", "Eighty", "Ninety"]
    teens = ["Ten", "Eleven", "Twelve", "Thirteen", "Fourteen", "Fifteen", "Sixteen", "Seventeen", "Eighteen", "Nineteen"]
    
    if number == 0:
        return "Zero"
    
    def convert_hundreds(n):
        result = ""
        if n >= 100:
            result += ones[n // 100] + " Hundred"
            n %= 100
            if n > 0:
                result += " "
        if n >= 20:
            result += tens[n // 10]
            n %= 10
            if n > 0:
                result += " " + ones[n]
        elif n >= 10:
            result += teens[n - 10]
        else:
            if n > 0:
                result += ones[n]
        return result.strip()
    
    def convert_number(n):
        if n == 0:
            return ""
        
        groups = ["", "Thousand", "Lakh", "Crore"]
        result = ""
        
        # Indian numbering system
        if n >= 10000000:  # Crore
            result += convert_hundreds(n // 10000000) + " Crore "
            n %= 10000000
        if n >= 100000:  # Lakh
            result += convert_hundreds(n // 100000) + " Lakh "
            n %= 100000
        if n >= 1000:  # Thousand
            result += convert_hundreds(n // 1000) + " Thousand "
            n %= 1000
        if n > 0:
            if result.strip():
                result += convert_hundreds(n)
            else:
                result += convert_hundreds(n)
        
        return result.strip()


def generate_invoice_pdf_reportlab(invoice, company):
    """Generate PDF for a single invoice using ReportLab (Railway-compatible)"""
    try:
        # Create PDF buffer - tight margins for A4 single page
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4, 
                              leftMargin=0.3*inch, rightMargin=0.3*inch,
                              topMargin=0.3*inch, bottomMargin=0.3*inch)
        
        # Styles matching your reference exactly
        styles = getSampleStyleSheet()
        
        # TAX INVOICE title - Large, bold, red, centered
        title_style = ParagraphStyle(
            'TaxInvoiceTitle',
            parent=styles['Heading1'],
            fontSize=20,
            fontName='Helvetica-Bold',
            textColor=colors.HexColor('#d32f2f'),  # Red color
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
            textColor=colors.HexColor('#1f4e79'),  # Blue color
            spaceAfter=2
        )
        
        # Normal text style
        normal_style = ParagraphStyle(
            'Normal',
            parent=styles['Normal'],
            fontSize=7,
            fontName='Helvetica',
            textColor=colors.black,
            spaceAfter=1
        )
        
        # Table header style
        table_header_style = ParagraphStyle(
            'TableHeader',
            parent=styles['Normal'],
            fontSize=7,
            fontName='Helvetica-Bold',
            textColor=colors.black,
            alignment=TA_CENTER,
            spaceAfter=2
        )
        
        # Build PDF content
        content = []
        
        # Title
        content.append(Paragraph("TAX INVOICE", title_style))
        
        # Company header row
        company_row_data = []
        
        # Left column - Company details
        company_text = f"{company.name}\n\n"
        company_text += f"{company.address}\n"
        company_text += f"{company.city}, {company.state} - {company.pincode}\n"
        company_text += f"GSTIN: {company.gstin}\n"
        company_text += f"PAN: {company.pan}\n"
        company_text += f"Contact: {company.phone}\n"
        company_text += f"Email: {company.email}"
        
        company_row_data.append(Paragraph(company_text, company_style))
        
        # Right column - Invoice details
        invoice_text = f"Invoice No: {invoice.invoice_number}\n"
        invoice_text += f"Date: {invoice.invoice_date.strftime('%d/%m/%Y')}\n"
        if invoice.due_date:
            invoice_text += f"Due Date: {invoice.due_date.strftime('%d/%m/%Y')}\n"
        if hasattr(invoice, 'eway_bill') and invoice.eway_bill:
            invoice_text += f"E-Way Bill No: {invoice.eway_bill}"
        
        company_row_data.append(Paragraph(invoice_text, normal_style))
        
        content.append(Table([company_row_data], colWidths=[4*inch, 2*inch]))
        content.append(Spacer(1, 12))
        
        # Customer details row
        customer_row_data = []
        
        # Left column - Bill to
        bill_to_text = f"BILL TO:\n{invoice.customer.name}\n"
        if invoice.customer.address:
            bill_to_text += f"{invoice.customer.address}\n"
        bill_to_text += f"{invoice.customer.city}, {invoice.customer.state} - {invoice.customer.pincode}\n"
        if invoice.customer.gstin:
            bill_to_text += f"GSTIN: {invoice.customer.gstin}"
        
        customer_row_data.append(Paragraph(bill_to_text, normal_style))
        
        # Right column - Ship to  
        ship_to_text = f"SHIP TO:\n"
        ship_to_text += f"{invoice.customer.name}\n"
        if invoice.customer.address:
            ship_to_text += f"{invoice.customer.address}\n"
        ship_to_text += f"{invoice.customer.city}, {invoice.customer.state} - {invoice.customer.pincode}"
        
        customer_row_data.append(Paragraph(ship_to_text, normal_style))
        
        content.append(Table([customer_row_data], colWidths=[3*inch, 3*inch]))
        content.append(Spacer(1, 12))
        
        # Calculate totals
        total_taxable_amount = 0
        total_tax_amount = 0
        
        for item in invoice.items:
            try:
                qty = float(item.quantity) if item.quantity else 0.0
                price = float(item.unit_price) if item.unit_price else 0.0
                discount_percent = float(item.discount_value) if item.discount_value else 0.0
                
                # Calculate discount
                subtotal = qty * price
                if hasattr(item, 'discount_type') and item.discount_type == 'percentage':
                    discount_amount = subtotal * (discount_percent / 100.0)
                else:
                    discount_amount = discount_percent  # Amount-based discount
                
                # Calculate taxable amount
                taxable_amount = subtotal - discount_amount
                total_taxable_amount += taxable_amount
                
                # Calculate tax using item's tax_rate
                gst_rate = float(item.tax_rate) if hasattr(item, 'tax_rate') else 18.0
                tax_amount = taxable_amount * (gst_rate / 100.0)
                
                total_tax_amount += tax_amount
                
            except (ValueError, TypeError):
                continue
        
        total_amount = total_taxable_amount + total_tax_amount
        
        # Items table
        table_data = [
            [Paragraph("<b>S.No.</b>", table_header_style),
             Paragraph("<b>Description of Goods/Services</b>", table_header_style),
             Paragraph("<b>Qty</b>", table_header_style),
             Paragraph("<b>Rate</b>", table_header_style),
             Paragraph("<b>Amount</b>", table_header_style)]
        ]
        
        for i, item in enumerate(invoice.items):
            try:
                qty = float(item.quantity) if item.quantity else 0.0
                price = float(item.unit_price) if item.unit_price else 0.0
                discount_percent = float(item.discount_value) if item.discount_value else 0.0
                
                subtotal = qty * price
                if hasattr(item, 'discount_type') and item.discount_type == 'percentage':
                    discount_amount = subtotal * (discount_percent / 100.0)
                else:
                    discount_amount = discount_percent  # Amount-based discount
                taxable_amount = subtotal - discount_amount
                
                table_data.append([
                    Paragraph(str(i + 1), normal_style),
                    Paragraph(item.description, normal_style),
                    Paragraph(f"{qty:.2f}", normal_style),
                    Paragraph(f"₹{price:.2f}", normal_style),
                    Paragraph(f"₹{subtotal:.2f}", normal_style)
                ])
            except (ValueError, TypeError):
                continue
        
        # Add totals row
        table_data.extend([
            [Paragraph("", normal_style), Paragraph("", normal_style), Paragraph("", normal_style), Paragraph("<b>Subtotal:</b>", normal_style), Paragraph(f"<b>₹{total_taxable_amount:.2f}</b>", normal_style)],
            [Paragraph("", normal_style), Paragraph("", normal_style), Paragraph("", normal_style), Paragraph("<b>GST:</b>", normal_style), Paragraph(f"<b>₹{total_tax_amount:.2f}</b>", normal_style)],
            [Paragraph("", normal_style), Paragraph("", normal_style), Paragraph("", normal_style), Paragraph("<b>Total:</b>", normal_style), Paragraph(f"<b>₹{total_amount:.2f}</b>", normal_style)]
        ])
        
        items_table = Table(table_data, colWidths=[0.5*inch, 3*inch, 0.8*inch, 1*inch, 1*inch])
        items_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('ALIGN', (1, 0), (1, -1), 'LEFT'),
            ('ALIGN', (2, 0), (-1, -1), 'RIGHT'),
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 7),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('FONTNAME', (0, -3), (-1, -1), 'Helvetica-Bold'),
        ]))
        
        content.append(items_table)
        content.append(Spacer(1, 20))
        
        # Amount in words
        amount_words = number_to_words(total_amount)
        content.append(Paragraph(f"Amount in words: <b>{amount_words}</b>", normal_style))
        content.append(Spacer(1, 10))
        
        # Terms and conditions
        if hasattr(invoice, 'notes') and invoice.notes:
            content.append(Paragraph(f"Notes:\n{invoice.notes}", normal_style))
        
        # Footer
        footer_text = f"Thank you for your business!\nFor any queries, contact us at {company.email} or {company.phone}"
        content.append(Spacer(1, 20))
        content.append(Paragraph(footer_text, normal_style))
        
        # Build PDF
        doc.build(content)
        buffer.seek(0)
        pdf_data = buffer.getvalue()
        

        
        return pdf_data
        
    except Exception as e:
        print(f"Error generating PDF: {str(e)}")
        return None


def generate_offer_pdf_from_data(data):
    """Generate Offer PDF using the new HTML template and existing HTML-to-PDF pipeline."""
    try:
        from flask import current_app

        # Ensure required keys exist to avoid template errors
        safe_data = {
            'page_title': data.get('page_title', 'Offer'),
            'offer_title': data.get('offer_title', 'OFFER'),
            'company_name': data.get('company_name'),
            'company_address': data.get('company_address'),
            'company_contact': data.get('company_contact'),
            'logo_path': data.get('logo_path'),
            'to_name': data.get('to_name'),
            'to_address': data.get('to_address', []) if isinstance(data.get('to_address'), list) else ([data.get('to_address')] if data.get('to_address') else []),
            'attention': data.get('attention'),
            'subject': data.get('subject'),
            'reference': data.get('reference'),
            'ref_date': data.get('ref_date'),
            'intro_paragraph': data.get('intro_paragraph'),
            'items': data.get('items', []),
            'prices_text': data.get('prices_text'),
            'gst_text': data.get('gst_text'),
            'pf_text': data.get('pf_text'),
            'validity_text': data.get('validity_text'),
            'payment_terms': data.get('payment_terms', []),
            'payment_note': data.get('payment_note'),
            'delivery_text': data.get('delivery_text'),
            'warranty_text': data.get('warranty_text'),
            'closing_text': data.get('closing_text'),
            'signature_path': data.get('signature_path'),
            'stamp_path': data.get('stamp_path'),
            'sign_name': data.get('sign_name'),
            'page_tag': data.get('page_tag'),
        }

        # Convert local images to base64 if paths are provided
        for key in ['logo_path', 'signature_path', 'stamp_path']:
            path_val = safe_data.get(key)
            if path_val and isinstance(path_val, str) and os.path.exists(path_val):
                encoded = convert_image_to_base64(path_val)
                if encoded:
                    safe_data[key] = encoded

        # Render HTML and convert to PDF
        with tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False, encoding='utf-8') as temp_file:
            with current_app.test_request_context():
                html_content = render_template('offer_print.html', data=safe_data)
            temp_file.write(html_content)
            temp_file_path = temp_file.name

        pdf_data = convert_html_to_pdf_railway(temp_file_path)

        try:
            os.unlink(temp_file_path)
        except Exception:
            pass

        return pdf_data

    except Exception as e:
        print(f"Error generating Offer PDF: {str(e)}")
        return None

def generate_invoice_pdf_from_template(invoice, company):
    """Generate PDF using the same HTML template as single invoices (Railway-compatible)"""
    try:
        from flask import current_app
        from app import get_company_details, calculate_gst, generate_payment_qr_code, get_company_addresses, number_to_words
        
        # Get company details
        company_details = get_company_details()
        
        # Get customer details
        customer = invoice.customer
        
        # Get company state from GSTIN (same as print route)
        from app import get_state_from_gstin, validate_discount_value
        company_state = get_state_from_gstin(company_details['gstin'])
        
        # Get customer state from GSTIN (same as print route)
        customer_state = get_state_from_gstin(customer.gstin) if customer.gstin else "Unknown State"
        is_interstate = customer_state != company_state
        
        # Calculate item details (exact same logic as print route)
        item_details = []
        for item in invoice.items:
            try:
                # Calculate gross amount
                gross_amount = Decimal(str(item.quantity)) * Decimal(str(item.unit_price))
                
                # Validate and calculate discount amount using our fixed validation
                validated_discount_value = validate_discount_value(item.discount_type, item.discount_value, gross_amount)
                
                if item.discount_type == 'percentage' and validated_discount_value > 0:
                    item_discount = gross_amount * validated_discount_value / Decimal('100')
                elif item.discount_type == 'amount' and validated_discount_value > 0:
                    item_discount = validated_discount_value
                else:
                    item_discount = Decimal('0')
                
                # Calculate taxable amount for this item
                item_taxable = max(gross_amount - item_discount, Decimal('0'))
                
                # Calculate tax for this item
                cgst, sgst, igst = calculate_gst(item_taxable, item.tax_rate, is_interstate)
                
                # Calculate total for this item
                item_total = item_taxable + cgst + sgst + igst
                
                item_details.append({
                    'item': item,
                    'discount': float(item_discount),
                    'taxable': float(item_taxable),
                    'cgst': float(cgst),
                    'sgst': float(sgst),
                    'igst': float(igst),
                    'total': float(item_total)
                })
            except Exception as item_error:
                print(f'Error calculating item details for item {item.id if item else "unknown"}: {str(item_error)}')
                continue
        
        # Generate QR code for payment (same as print route)
        qr_code = generate_payment_qr_code(invoice.total_amount, invoice.invoice_number, customer.name)
        
        # Parse metadata from notes JSON
        import json
        meta = {}
        if invoice.notes:
            try:
                meta = json.loads(invoice.notes)
            except (json.JSONDecodeError, TypeError):
                # Fallback if notes is not JSON
                meta = {
                    'reference_no': '-',
                    'eway_bill': '-',
                    'terms_text': 'CERTIFIED THAT THE PARTICULARS GIVEN ABOVE ARE TRUE AND CORRECT. WE ALSO DECLARE THAT WE WILL REMIT THE GST AMOUNT AND FILE APPLICABLE GST RETURNS',
                    'payment_text': 'Payment: 100% Against supply Immediate.  Warranty: 12 Month From the date of Supply.  Only For: Ac Drive, PLC, Servo Drive & Servo Motors'
                }
        else:
            meta = {
                'reference_no': '-',
                'eway_bill': '-',
                'terms_text': 'CERTIFIED THAT THE PARTICULARS GIVEN ABOVE ARE TRUE AND CORRECT. WE ALSO DECLARE THAT WE WILL REMIT THE GST AMOUNT AND FILE APPLICABLE GST RETURNS',
                'payment_text': 'Payment: 100% Against supply Immediate.  Warranty: 12 Month From the date of Supply.  Only For: Ac Drive, PLC, Servo Drive & Servo Motors'
            }
        
        # Get address information (same as print route)
        addresses = get_company_addresses()
        main_address_key = meta.get('main_address', 'salem')
        branch_address_key = meta.get('branch_address', 'chennai')
        
        # Validate that the address keys exist
        if not addresses or main_address_key not in addresses:
            main_address_key = 'salem'
        if not addresses or branch_address_key not in addresses:
            branch_address_key = 'chennai'
        
        # Get the absolute path to the logo file and convert to base64
        logo_path = os.path.join(current_app.root_path, 'static', 'uploads', 'md_logo.jpg')
        logo_base64 = convert_image_to_base64(logo_path)
        
        # Create a temporary HTML file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False, encoding='utf-8') as temp_file:
            # Render template with proper context (exact same as print route)
            with current_app.test_request_context():
                html_content = render_template('print_invoice.html',
                    invoice=invoice,
                    company=company,
                    company_details=company_details,
                    customer=customer,
                    item_details=item_details,
                    qr_code=qr_code,
                    meta=meta,
                    addresses=addresses,
                    main_address_key=main_address_key,
                    branch_address_key=branch_address_key,
                    logo_path=logo_base64 if logo_base64 else logo_path,
                    float=float,
                    number_to_words=number_to_words,
                    is_interstate=is_interstate,
                    customer_state=customer_state
                )
            
            temp_file.write(html_content)
            temp_file_path = temp_file.name
        
        # Use HTML-to-PDF conversion for 100% exact template match
        pdf_data = convert_html_to_pdf_railway(temp_file_path)
        
        # Clean up temporary file after conversion
        try:
            os.unlink(temp_file_path)
        except:
            pass
        
        # If HTML-to-PDF failed, fallback to ReportLab enhanced version
        if not pdf_data:
            print("HTML-to-PDF conversion failed, using ReportLab fallback...")
            try:
                pdf_data = generate_invoice_pdf_reportlab_enhanced(invoice, company, company_details, customer, item_details, qr_code, meta, addresses, main_address_key, branch_address_key, logo_path, logo_base64)
                if pdf_data:
                    print("✅ ReportLab fallback PDF generation successful")
                else:
                    print("❌ ReportLab fallback PDF generation failed")
            except Exception as fallback_error:
                print(f"❌ ReportLab fallback error: {str(fallback_error)}")
                # Final fallback - simple ReportLab PDF without logo
                try:
                    from generate_pdf_railway import generate_invoice_pdf_reportlab
                    pdf_data = generate_invoice_pdf_reportlab(invoice, company)
                    if pdf_data:
                        print("✅ Simple ReportLab PDF generation successful")
                    else:
                        print("❌ Simple ReportLab PDF generation failed")
                except Exception as simple_error:
                    print(f"❌ Simple ReportLab error: {str(simple_error)}")
                    pdf_data = None
        
        # Apply cryptographic Digital Signature if selected
        requires_local_signature = False
        
        if pdf_data and invoice.require_digital_signature and hasattr(invoice, 'selected_signature') and invoice.selected_signature:
            if invoice.selected_signature.signature_format == 'usb_token':
                # Bypass server-side signing, flag for local bridge signing
                requires_local_signature = True
            elif invoice.selected_signature.signature_format == 'pfx':
                # Traditional server-side PFX signing
                signed_pdf = apply_digital_signature(
                    pdf_bytes=pdf_data,
                    pfx_data_base64=invoice.selected_signature.signature_data,
                    password=invoice.selected_signature.certificate_password,
                    signer_name=invoice.signed_by.username if invoice.signed_by else "Authorised Signatory",
                    reason=f"Tax Invoice {invoice.invoice_number} Digitally Signed"
                )
                if signed_pdf:
                    pdf_data = signed_pdf
        
        # We now return a tuple: (pdf_bytes, requires_local_signature)
        return pdf_data, requires_local_signature
        
    except Exception as e:
        print(f"Error generating PDF from template: {str(e)}")
        return None


def convert_html_to_pdf_railway(html_file_path):
    """Convert HTML to PDF using a Railway-compatible method for 100% exact template match"""
    try:
        # Try using Playwright first (best rendering quality)
        try:
            import os
            # Force playwright to look in the local site-packages where we installed the browsers during the Railway build
            os.environ['PLAYWRIGHT_BROWSERS_PATH'] = '0'
            from playwright.sync_api import sync_playwright
            
            with open(html_file_path, 'r', encoding='utf-8') as f:
                html_content = f.read()
            
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True)
                page = browser.new_page()
                page.set_content(html_content)
                
                # Generate PDF with exact A4 settings matching the HTML template
                pdf_bytes = page.pdf(
                    format='A4',
                    margin={'top': '1cm', 'right': '1cm', 'bottom': '1cm', 'left': '1cm'},
                    print_background=True,
                    prefer_css_page_size=True,
                    display_header_footer=False
                )
                browser.close()
                return pdf_bytes
                
        except ImportError as e:
            print(f"Playwright not available: {e}")
        except Exception as e:
            print(f"Playwright error: {e}")

        # Try using xhtml2pdf as fallback (pure Python, Railway compatible)
        try:
            from xhtml2pdf import pisa
            with open(html_file_path, 'r', encoding='utf-8') as f:
                html_content = f.read()
            
            pdf_buffer = BytesIO()
            result = pisa.CreatePDF(html_content, pdf_buffer)
            if not result.err:
                return pdf_buffer.getvalue()
            else:
                print(f"xhtml2pdf error: {result.err}")
                
        except ImportError as e:
            print(f"xhtml2pdf not available: {e}")
        except Exception as e:
            print(f"xhtml2pdf error: {e}")
        
        # Try using weasyprint (good for CSS rendering)
        try:
            import weasyprint
            with open(html_file_path, 'r', encoding='utf-8') as f:
                html_content = f.read()
            
            # Create PDF from HTML with exact settings
            pdf_bytes = weasyprint.HTML(string=html_content).write_pdf()
            return pdf_bytes
            
        except ImportError as e:
            print(f"WeasyPrint not available: {e}")
        except Exception as e:
            print(f"WeasyPrint error: {e}")
        
        # Try using pdfkit (if available)
        try:
            import pdfkit
            with open(html_file_path, 'r', encoding='utf-8') as f:
                html_content = f.read()
            
            # Configure pdfkit options for Railway
            options = {
                'page-size': 'A4',
                'margin-top': '1cm',
                'margin-right': '1cm',
                'margin-bottom': '1cm',
                'margin-left': '1cm',
                'encoding': "UTF-8",
                'no-outline': None,
                'enable-local-file-access': None
            }
            
            pdf_bytes = pdfkit.from_string(html_content, False, options=options)
            return pdf_bytes
            
        except ImportError as e:
            print(f"pdfkit not available: {e}")
        except Exception as e:
            print(f"pdfkit error: {e}")
        
        # Fallback to ReportLab enhanced version
        print("All HTML-to-PDF libraries unavailable, using ReportLab fallback")
        return None
        
    except Exception as e:
        print(f"Error converting HTML to PDF: {str(e)}")
        return None



def generate_invoice_pdf_reportlab_enhanced(invoice, company, company_details, customer, item_details, qr_code, meta, addresses, main_address_key, branch_address_key, logo_path, logo_base64=None):
    """Generate enhanced PDF that matches the HTML template exactly using ReportLab"""
    try:
        # Get customer state from GSTIN (same as print route)
        from app import get_state_from_gstin
        company_state = get_state_from_gstin(company_details['gstin'])
        customer_state = get_state_from_gstin(customer.gstin) if customer.gstin else "Unknown State"
        is_interstate = customer_state != company_state
        
        # Create PDF buffer - A4 with 1cm margins to match template exactly
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4, 
                              leftMargin=1*inch, rightMargin=1*inch,
                              topMargin=1*inch, bottomMargin=1*inch)
        
        # Styles matching your template exactly
        styles = getSampleStyleSheet()
        
        # TAX INVOICE title - Large, bold, red, centered (28px)
        title_style = ParagraphStyle(
            'TaxInvoiceTitle',
            parent=styles['Heading1'],
            fontSize=28,
            fontName='Helvetica-Bold',
            textColor=colors.HexColor('#d32f2f'),  # Red color
            alignment=TA_CENTER,
            spaceAfter=8,
            spaceBefore=4
        )
        
        # Company name - Red, bold (18px)
        company_style = ParagraphStyle(
            'CompanyName',
            parent=styles['Normal'],
            fontSize=18,
            fontName='Helvetica-Bold',
            textColor=colors.HexColor('#d32f2f'),  # Red color
            spaceAfter=2
        )
        
        # Normal text style (11px)
        normal_style = ParagraphStyle(
            'Normal',
            parent=styles['Normal'],
            fontSize=11,
            fontName='Helvetica',
            textColor=colors.black,
            spaceAfter=1
        )
        
        # Small text style (9px)
        small_style = ParagraphStyle(
            'Small',
            parent=styles['Normal'],
            fontSize=9,
            fontName='Helvetica',
            textColor=colors.black,
            spaceAfter=1
        )
        
        # Table header style (9px)
        table_header_style = ParagraphStyle(
            'TableHeader',
            parent=styles['Normal'],
            fontSize=9,
            fontName='Helvetica-Bold',
            textColor=colors.black,
            alignment=TA_CENTER,
            spaceAfter=2
        )
        
        # Build PDF content to match HTML template exactly
        content = []
        
        # Add initial spacing to match HTML template
        content.append(Spacer(1, 6))
        
        # Title - TAX INVOICE (centered, red, 28px)
        content.append(Paragraph("TAX INVOICE", title_style))
        content.append(Spacer(1, 12))
        
        # Header section with logo, company details, and invoice details (matching HTML flexbox layout)
        header_data = []
        
        # Left column - Logo and tagline (38mm width)
        logo_col_data = []
        if logo_base64:
            try:
                # Create a temporary file from base64 data for ReportLab
                import tempfile
                with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as temp_logo:
                    # Decode base64 and write to temporary file
                    logo_data = base64.b64decode(logo_base64.split(',')[1])
                    temp_logo.write(logo_data)
                    temp_logo_path = temp_logo.name
                
                # Ensure file is written and closed before using
                temp_logo.flush()
                temp_logo.close()
                
                # Verify file exists and has content
                if os.path.exists(temp_logo_path) and os.path.getsize(temp_logo_path) > 0:
                    logo_img = Image(temp_logo_path, width=1.18*inch, height=1.18*inch)  # 30mm = 1.18 inch
                    logo_col_data.append(logo_img)
                    print(f"✅ Logo loaded from base64 temporary file: {temp_logo_path}")
                else:
                    print(f"⚠️ Temporary logo file not found or empty: {temp_logo_path}")
                
                # Clean up temporary file
                try:
                    os.unlink(temp_logo_path)
                except:
                    pass
            except Exception as e:
                print(f"Error using base64 logo in ReportLab: {str(e)}")
                # Fallback to file path
                if os.path.exists(logo_path):
                    try:
                        logo_img = Image(logo_path, width=1.18*inch, height=1.18*inch)
                        logo_col_data.append(logo_img)
                        print(f"✅ Logo loaded from file path: {logo_path}")
                    except Exception as file_error:
                        print(f"Error loading logo from file path: {str(file_error)}")
                        pass
        elif os.path.exists(logo_path):
            try:
                logo_img = Image(logo_path, width=1.18*inch, height=1.18*inch)  # 30mm = 1.18 inch
                logo_col_data.append(logo_img)
            except:
                pass
        
        if company_details.get('tagline'):
            logo_col_data.append(Paragraph(company_details['tagline'], small_style))
        
        if logo_col_data:
            header_data.append(Table([logo_col_data], colWidths=[1.5*inch]))
        else:
            header_data.append(Paragraph("", normal_style))
        
        # Middle column - Company details (80mm width)
        company_name = addresses.get(main_address_key, {}).get('name', company.name) if addresses and main_address_key in addresses else company.name
        company_address = addresses.get(main_address_key, {}).get('address', company.address) if addresses and main_address_key in addresses else company.address
        # Clean HTML tags from address
        import re
        company_address = re.sub(r'<br\s*/?>', '\n', company_address)
        company_phone = addresses.get(main_address_key, {}).get('phone', company.phone) if addresses and main_address_key in addresses else company.phone
        company_email = addresses.get(main_address_key, {}).get('email', company.email) if addresses and main_address_key in addresses else company.email
        
        # Create company details with exact HTML structure
        company_text = f"<b>{company_name}</b>\n{company_address}\n{company_phone}\n{company_email}\n<b>GSTIN:</b> {company_details.get('gstin', company.gstin)}\n<b>State:</b> {company_details.get('state', company.state)}\n<b>PAN:</b> {company_details.get('pan', company.pan)}"
        
        header_data.append(Paragraph(company_text, company_style))
        
        # Right column - Invoice details with ORIGINAL stamp (56-60mm width)
        invoice_text = "<b>ORIGINAL</b>\n<small>For Recipient</small>\n\n<b>Invoice Date:</b> {}\n<b>Invoice No:</b> {}".format(
            invoice.invoice_date.strftime('%d/%m/%Y'), invoice.invoice_number)
        
        if meta.get('reference_no') and meta['reference_no'] != '-':
            invoice_text += f"\n<b>Reference No:</b> {meta['reference_no']}"
        if meta.get('eway_bill') and meta['eway_bill'] != '-':
            invoice_text += f"\n<b>E-way Bill:</b> {meta['eway_bill']}"
        
        header_data.append(Paragraph(invoice_text, normal_style))
        
        # Create header table with exact column widths from HTML template
        content.append(Table([header_data], colWidths=[1.5*inch, 3.15*inch, 2.2*inch]))
        content.append(Spacer(1, 6))
        
        # Red separator line
        content.append(Spacer(1, 2))
        
        # Customer details table
        customer_table_data = [
            [Paragraph("<b>Customer Details</b>", table_header_style),
             Paragraph("<b>Billing Information</b>", table_header_style),
             Paragraph("<b>Shipping Information</b>", table_header_style)]
        ]
        
        # Customer details - use simple text without HTML (matching HTML template)
        # Clean HTML tags from customer address
        clean_customer_address = re.sub(r'<br\s*/?>', '\n', customer.address)
        customer_details = f"<b>{customer.name}</b>\n{clean_customer_address}"
        if customer.city:
            customer_details += f", {customer.city}"
        if customer.pincode:
            customer_details += f", {customer.pincode}"
        customer_details += "\n"
        if customer.phone:
            customer_details += f"Phone: {customer.phone}\n"
        if customer.email:
            customer_details += f"Email: {customer.email}\n"
        if customer.gstin:
            customer_details += f"Customer GSTIN: {customer.gstin}"
        
        # Billing info (same as customer)
        billing_info = customer_details
        
        # Shipping info - use simple text without HTML (matching HTML template)
        shipping_info = f"<b>{customer.name}</b>\n"
        if meta.get('extra_billing_info'):
            # Clean HTML tags from extra billing info
            clean_extra_info = re.sub(r'<br\s*/?>', '\n', meta['extra_billing_info'])
            shipping_info += f"{clean_extra_info}\n"
        else:
            shipping_info += f"{clean_customer_address}"
            if customer.city:
                shipping_info += f", {customer.city}"
            if customer.pincode:
                shipping_info += f", {customer.pincode}"
            shipping_info += "\n"
        if customer.gstin:
            shipping_info += f"GSTIN: {customer.gstin}"
        
        customer_table_data.append([
            Paragraph(customer_details, normal_style),
            Paragraph(billing_info, normal_style),
            Paragraph(shipping_info, normal_style)
        ])
        
        # Additional customer info row (matching HTML template)
        customer_table_data.append([
            Paragraph(f"<b>Place of Supply:</b> {customer_state}", normal_style),
            Paragraph(f"<b>GSTIN:</b> {customer.gstin if customer.gstin else 'No GSTIN'}", normal_style),
            Paragraph(f"<b>Due Date:</b> {invoice.due_date.strftime('%d/%m/%Y') if invoice.due_date else 'Not specified'}", normal_style)
        ])
        
        content.append(Table(customer_table_data, colWidths=[2.5*inch, 2.5*inch, 2.5*inch]))
        content.append(Spacer(1, 4))
        
        # Items table with all columns (matching HTML template structure)
        has_discounts = any(detail['discount'] > 0 for detail in item_details)
        is_interstate = customer_state != company_state
        
        # Table headers (matching HTML template exactly)
        table_headers = [
            Paragraph("<b>Sl. No.</b>", table_header_style),
            Paragraph("<b>Item</b>", table_header_style),
            Paragraph("<b>HSN</b>", table_header_style),
            Paragraph("<b>Qty</b>", table_header_style),
            Paragraph("<b>Rate</b>", table_header_style)
        ]
        
        if has_discounts:
            table_headers.append(Paragraph("<b>Disc</b>", table_header_style))
        
        table_headers.append(Paragraph("<b>Taxable Value</b>", table_header_style))
        
        if is_interstate:
            table_headers.append(Paragraph("<b>IGST</b>", table_header_style))
        else:
            table_headers.append(Paragraph("<b>CGST</b>", table_header_style))
            table_headers.append(Paragraph("<b>SGST</b>", table_header_style))
        
        table_headers.append(Paragraph("<b>Total</b>", table_header_style))
        
        table_data = [table_headers]
        
        # Add item rows (matching HTML template exactly)
        for i, detail in enumerate(item_details):
            item = detail['item']
            row_data = [
                Paragraph(str(i + 1), normal_style),
                Paragraph(item.description, normal_style),
                Paragraph(item.hsn_code or company_details.get('default_hsn', '85044090'), normal_style),
                Paragraph(f"{item.quantity:.2f}", normal_style),
                Paragraph(f"{item.unit_price:,.2f}", normal_style)
            ]
            
            if has_discounts:
                if item.discount_value > 0:
                    if item.discount_type == 'percentage':
                        row_data.append(Paragraph(f"{item.discount_value:.1f}%", normal_style))
                    else:
                        row_data.append(Paragraph(f"{item.discount_value:,.2f}", normal_style))
                else:
                    row_data.append(Paragraph("0.00", normal_style))
            
            row_data.append(Paragraph(f"{detail['taxable']:,.2f}", normal_style))
            
            if is_interstate:
                row_data.append(Paragraph(f"{detail['igst']:,.2f}\n@{item.tax_rate:.0f}%", normal_style))
            else:
                row_data.append(Paragraph(f"{detail['cgst']:,.2f}\n@{item.tax_rate/2:.1f}%", normal_style))
                row_data.append(Paragraph(f"{detail['sgst']:,.2f}\n@{item.tax_rate/2:.1f}%", normal_style))
            
            row_data.append(Paragraph(f"{detail['total']:,.2f}", normal_style))
            table_data.append(row_data)
        
        # Add totals row (matching HTML template exactly)
        total_row = [Paragraph("<b>Total</b>", normal_style), Paragraph("", normal_style), 
                    Paragraph("", normal_style), Paragraph("", normal_style), Paragraph("", normal_style)]
        
        if has_discounts:
            total_discount = sum(detail['discount'] for detail in item_details)
            total_row.append(Paragraph(f"<b>{total_discount:,.2f}</b>", normal_style))
        
        total_row.append(Paragraph(f"<b>{invoice.subtotal:,.2f}</b>", normal_style))
        
        if is_interstate:
            total_row.append(Paragraph(f"<b>{invoice.igst_amount:,.2f}</b>", normal_style))
        else:
            total_row.append(Paragraph(f"<b>{invoice.cgst_amount:,.2f}</b>", normal_style))
            total_row.append(Paragraph(f"<b>{invoice.sgst_amount:,.2f}</b>", normal_style))
        
        total_row.append(Paragraph(f"<b>{invoice.total_amount:,.2f}</b>", normal_style))
        table_data.append(total_row)
        
        # Calculate column widths to match HTML template exactly
        col_widths = [0.4*inch, 2*inch, 0.6*inch, 0.5*inch, 0.8*inch]
        if has_discounts:
            col_widths.append(0.5*inch)
        col_widths.extend([0.8*inch])  # Taxable
        if is_interstate:
            col_widths.append(0.8*inch)  # IGST
        else:
            col_widths.extend([0.8*inch, 0.8*inch])  # CGST, SGST
        col_widths.append(0.8*inch)  # Total
        
        items_table = Table(table_data, colWidths=col_widths)
        items_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#fff3bf')),  # Yellow header background
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('ALIGN', (1, 0), (1, -1), 'LEFT'),  # Item description left-aligned
            ('ALIGN', (3, 0), (-1, -1), 'RIGHT'),  # Numeric columns right-aligned
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
            ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor('#fff7d6')),  # Light yellow total row
            ('ROWBACKGROUNDS', (0, 1), (-1, -2), [colors.white, colors.HexColor('#f9f9f9')]),
        ]))
        
        content.append(items_table)
        content.append(Spacer(1, 12))
        
        # Two-column layout for bank details and summary (matching HTML template exactly)
        two_col_data = []
        
        # Left column - Bank details and terms (48% width)
        left_col_content = []
        
        # Bank details table with red header (matching HTML template)
        bank_table_data = [
            [Paragraph("<b>Bank Details:</b>", table_header_style), Paragraph("", table_header_style)]
        ]
        
        if company_details.get('bank_details'):
            bank = company_details['bank_details']
            bank_table_data.extend([
                [Paragraph("Account Number:", small_style), Paragraph(bank.get('account_number', 'N/A'), small_style)],
                [Paragraph("Account Type:", small_style), Paragraph(bank.get('account_type', 'N/A'), small_style)],
                [Paragraph("IFSC:", small_style), Paragraph(bank.get('ifsc', 'N/A'), small_style)],
                [Paragraph("Bank Name:", small_style), Paragraph(bank.get('bank_name', 'N/A'), small_style)],
                [Paragraph("Branch Name:", small_style), Paragraph(bank.get('branch_name', 'N/A'), small_style)],
                [Paragraph("Virtual Payment:", small_style), Paragraph(bank.get('virtual_payment', 'N/A'), small_style)]
            ])
        
        bank_table = Table(bank_table_data, colWidths=[1.2*inch, 1.8*inch])
        bank_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#d32f2f')),  # Red header
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#d32f2f')),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ]))
        
        left_col_content.append(bank_table)
        left_col_content.append(Spacer(1, 6))
        
        # Terms and conditions (matching HTML template)
        terms_text = meta.get('terms_text', company_details.get('default_terms', 'Standard terms apply'))
        # Clean HTML tags from terms text
        clean_terms_text = re.sub(r'<br\s*/?>', '\n', terms_text)
        left_col_content.append(Paragraph(f"<b>Terms & Conditions:</b>\n{clean_terms_text}", small_style))
        
        # Branch office (matching HTML template)
        if addresses and branch_address_key in addresses:
            branch_address = addresses[branch_address_key].get('address', 'Branch Address')
            branch_email = addresses[branch_address_key].get('email', 'Branch Email')
            # Clean HTML tags from branch address
            clean_branch_address = re.sub(r'<br\s*/?>', '\n', branch_address)
            left_col_content.append(Paragraph(f"<b>Branch Office:</b>\n{clean_branch_address}\n{branch_email}", small_style))
        
        # Payment terms (matching HTML template)
        if meta.get('payment_text'):
            # Clean HTML tags from payment text
            clean_payment_text = re.sub(r'<br\s*/?>', '\n', meta['payment_text'])
            left_col_content.append(Paragraph(clean_payment_text, small_style))
        
        # Right column - Summary and total in words (52% width)
        right_col_content = []
        
        # Summary table (matching HTML template)
        summary_table_data = [
            [Paragraph("Subtotal", small_style), Paragraph(f"₹ {invoice.subtotal:,.2f}", small_style)],
            [Paragraph("Taxable Amount", small_style), Paragraph(f"₹ {invoice.subtotal:,.2f}", small_style)],
            [Paragraph("Total Tax", small_style), Paragraph(f"₹ {(invoice.cgst_amount + invoice.sgst_amount + invoice.igst_amount):,.2f}", small_style)],
            [Paragraph("Total Value", small_style), Paragraph(f"₹ {invoice.total_amount:,.2f}", small_style)]
        ]
        
        summary_table = Table(summary_table_data, colWidths=[2*inch, 1*inch])
        summary_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'RIGHT'),
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),  # Bold total row
            ('FONTSIZE', (0, -1), (-1, -1), 14),  # Larger font for total
        ]))
        
        right_col_content.append(summary_table)
        right_col_content.append(Spacer(1, 6))
        
        # Amount in words box (matching HTML template)
        amount_words = number_to_words(float(invoice.total_amount))
        amount_words_text = f"<b>Total amount (in words):</b>\n{amount_words}"
        right_col_content.append(Paragraph(amount_words_text, small_style))
        
        # QR code section (matching HTML template)
        if qr_code:
            right_col_content.append(Spacer(1, 8))
            right_col_content.append(Paragraph("<b>Scan to Pay</b>", small_style))
            # Note: QR code image would need to be handled separately in ReportLab
        
        # Combine left and right columns (matching HTML template)
        two_col_data.append([Table([[left_col_content]], colWidths=[3*inch]), 
                            Table([[right_col_content]], colWidths=[3*inch])])
        
        content.append(Table(two_col_data, colWidths=[3*inch, 3*inch]))
        content.append(Spacer(1, 8))
        
        # Signature section (matching HTML template)
        signature_data = []
        signature_data.append(Paragraph("", normal_style))  # Empty left column
        signature_data.append(Paragraph(f"For {company_details.get('signature_name', company.name)}\nAuthorised Signatory", normal_style))
        
        content.append(Table([signature_data], colWidths=[3*inch, 3*inch]))
        content.append(Spacer(1, 6))
        
        # Page number (matching HTML template)
        content.append(Paragraph("ORG 1/1", small_style))
        
        # Build PDF
        doc.build(content)
        buffer.seek(0)
        pdf_data = buffer.getvalue()
        
        # Apply cryptographic Digital Signature if PFX is selected and required
        if pdf_data and invoice.require_digital_signature and hasattr(invoice, 'selected_signature') and invoice.selected_signature and invoice.selected_signature.signature_format == 'pfx':
            signed_pdf = apply_digital_signature(
                pdf_bytes=pdf_data,
                pfx_data_base64=invoice.selected_signature.signature_data,
                password=invoice.selected_signature.certificate_password,
                signer_name=invoice.signed_by.username if invoice.signed_by else "Authorised Signatory",
                reason=f"Tax Invoice {invoice.invoice_number} Digitally Signed"
            )
            if signed_pdf:
                pdf_data = signed_pdf
        
        return pdf_data
        
    except Exception as e:
        print(f"Error generating enhanced PDF: {str(e)}")
        return None
