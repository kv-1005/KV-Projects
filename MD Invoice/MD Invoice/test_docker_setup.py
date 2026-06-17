#!/usr/bin/env python3
"""
Test script to verify Docker setup with all PDF libraries
"""

import os
import sys

def test_pdf_libraries():
    """Test all PDF generation libraries"""
    print("🔍 Testing PDF Generation Libraries in Docker")
    print("=" * 60)
    
    # Test 1: xhtml2pdf
    print("\n📄 Test 1: xhtml2pdf")
    try:
        from xhtml2pdf import pisa
        print("   ✅ xhtml2pdf: Available")
        
        # Test basic functionality
        from io import BytesIO
        html_content = "<html><body><h1>Test</h1></body></html>"
        pdf_buffer = BytesIO()
        result = pisa.CreatePDF(html_content, pdf_buffer)
        if not result.err:
            print("   ✅ xhtml2pdf: Working correctly")
        else:
            print(f"   ⚠️  xhtml2pdf: Error - {result.err}")
    except ImportError as e:
        print(f"   ❌ xhtml2pdf: Not available - {e}")
    except Exception as e:
        print(f"   ⚠️  xhtml2pdf: Error - {e}")
    
    # Test 2: WeasyPrint
    print("\n📄 Test 2: WeasyPrint")
    try:
        import weasyprint
        print("   ✅ WeasyPrint: Available")
        
        # Test basic functionality
        html_content = "<html><body><h1>Test</h1></body></html>"
        pdf_bytes = weasyprint.HTML(string=html_content).write_pdf()
        if pdf_bytes:
            print("   ✅ WeasyPrint: Working correctly")
        else:
            print("   ⚠️  WeasyPrint: No output")
    except ImportError as e:
        print(f"   ❌ WeasyPrint: Not available - {e}")
    except Exception as e:
        print(f"   ⚠️  WeasyPrint: Error - {e}")
    
    # Test 3: pdfkit
    print("\n📄 Test 3: pdfkit")
    try:
        import pdfkit
        print("   ✅ pdfkit: Available")
        
        # Test basic functionality
        html_content = "<html><body><h1>Test</h1></body></html>"
        options = {
            'page-size': 'A4',
            'margin-top': '1cm',
            'margin-right': '1cm',
            'margin-bottom': '1cm',
            'margin-left': '1cm',
            'encoding': "UTF-8",
            'no-outline': None
        }
        pdf_bytes = pdfkit.from_string(html_content, False, options=options)
        if pdf_bytes:
            print("   ✅ pdfkit: Working correctly")
        else:
            print("   ⚠️  pdfkit: No output")
    except ImportError as e:
        print(f"   ❌ pdfkit: Not available - {e}")
    except Exception as e:
        print(f"   ⚠️  pdfkit: Error - {e}")
    
    # Test 4: Playwright
    print("\n📄 Test 4: Playwright")
    try:
        from playwright.sync_api import sync_playwright
        print("   ✅ Playwright: Available")
        
        # Test basic functionality
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            page.set_content("<html><body><h1>Test</h1></body></html>")
            pdf_bytes = page.pdf(format='A4')
            browser.close()
            
            if pdf_bytes:
                print("   ✅ Playwright: Working correctly")
            else:
                print("   ⚠️  Playwright: No output")
    except ImportError as e:
        print(f"   ❌ Playwright: Not available - {e}")
    except Exception as e:
        print(f"   ⚠️  Playwright: Error - {e}")
    
    # Test 5: ReportLab
    print("\n📄 Test 5: ReportLab")
    try:
        from reportlab.lib.pagesizes import A4
        from reportlab.platypus import SimpleDocTemplate, Paragraph
        from reportlab.lib.styles import getSampleStyleSheet
        print("   ✅ ReportLab: Available")
        
        # Test basic functionality
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4)
        styles = getSampleStyleSheet()
        story = [Paragraph("Test", styles['Normal'])]
        doc.build(story)
        
        if buffer.getvalue():
            print("   ✅ ReportLab: Working correctly")
        else:
            print("   ⚠️  ReportLab: No output")
    except ImportError as e:
        print(f"   ❌ ReportLab: Not available - {e}")
    except Exception as e:
        print(f"   ⚠️  ReportLab: Error - {e}")

def test_system_dependencies():
    """Test system dependencies"""
    print("\n🔍 Testing System Dependencies")
    print("=" * 60)
    
    # Test Chrome
    print("\n🌐 Test 1: Chrome")
    try:
        import subprocess
        result = subprocess.run(['google-chrome', '--version'], 
                              capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            print(f"   ✅ Chrome: {result.stdout.strip()}")
        else:
            print("   ❌ Chrome: Not available")
    except Exception as e:
        print(f"   ❌ Chrome: Error - {e}")
    
    # Test wkhtmltopdf
    print("\n📄 Test 2: wkhtmltopdf")
    try:
        import subprocess
        result = subprocess.run(['wkhtmltopdf', '--version'], 
                              capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            print(f"   ✅ wkhtmltopdf: {result.stdout.strip()}")
        else:
            print("   ❌ wkhtmltopdf: Not available")
    except Exception as e:
        print(f"   ❌ wkhtmltopdf: Error - {e}")
    
    # Test system libraries
    print("\n📚 Test 3: System Libraries")
    libraries = [
        'libpango-1.0-0',
        'libharfbuzz0b',
        'libcairo2',
        'libgobject-2.0-0'
    ]
    
    for lib in libraries:
        try:
            import subprocess
            result = subprocess.run(['ldconfig', '-p'], 
                                  capture_output=True, text=True, timeout=10)
            if lib in result.stdout:
                print(f"   ✅ {lib}: Available")
            else:
                print(f"   ❌ {lib}: Not available")
        except Exception as e:
            print(f"   ❌ {lib}: Error - {e}")

def test_application():
    """Test application functionality"""
    print("\n🔍 Testing Application Functionality")
    print("=" * 60)
    
    try:
        from app import app
        print("   ✅ Flask app: Imported successfully")
        
        with app.app_context():
            print("   ✅ App context: Working")
            
            # Test database
            from app import db
            db.session.execute('SELECT 1')
            print("   ✅ Database: Connection working")
            
            # Test PDF generation
            from generate_pdf_railway import convert_image_to_base64
            logo_path = 'static/uploads/md_logo.jpg'
            if os.path.exists(logo_path):
                logo_base64 = convert_image_to_base64(logo_path)
                if logo_base64:
                    print("   ✅ Logo conversion: Working")
                else:
                    print("   ❌ Logo conversion: Failed")
            else:
                print("   ⚠️  Logo file: Not found")
                
    except Exception as e:
        print(f"   ❌ Application test failed: {e}")

def main():
    """Run all tests"""
    print("🚀 DOCKER SETUP VERIFICATION")
    print("=" * 80)
    print(f"📅 Test Date: {__import__('datetime').datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 80)
    
    # Run tests
    test_pdf_libraries()
    test_system_dependencies()
    test_application()
    
    # Summary
    print("\n" + "=" * 80)
    print("📊 TEST SUMMARY")
    print("=" * 80)
    print("🎯 Docker setup verification completed!")
    print("\n💡 Next steps:")
    print("   1. Build Docker image: docker build -f Dockerfile.advanced -t invoice-app .")
    print("   2. Test locally: docker run -p 8080:8080 invoice-app")
    print("   3. Deploy to Railway with Docker configuration")
    print("   4. Verify all PDF libraries work in production")

if __name__ == "__main__":
    main()
