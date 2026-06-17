"""
AI Chatbot Service for Invoice Management System
Implements hybrid rule-based + AI approach with caching and optimizations
Supports both Hugging Face API and local AI models
"""

import os
import re
import requests
from typing import Optional, Dict, List, Tuple
from datetime import datetime, timedelta
from functools import lru_cache
import hashlib
import time

# Try to import local AI model (optional)
try:
    from local_ai_model import LocalAIModel
    LOCAL_AI_AVAILABLE = True
except ImportError:
    LOCAL_AI_AVAILABLE = False
    LocalAIModel = None

# Knowledge base patterns for rule-based responses
KNOWLEDGE_BASE = [
    {
        'keywords': ['create invoice', 'new invoice', 'make invoice', 'generate invoice'],
        'pattern': r'(create|make|generate|new).*(invoice)',
        'response': """To create an invoice:
1. Go to the **Invoices** menu in the sidebar
2. Click **"Create New Invoice"** button
3. Select a customer from the dropdown
4. Add invoice items with descriptions, quantities, and rates
5. The system will automatically calculate GST and totals
6. Click **"Save Invoice"** to generate the invoice

You can also convert a Purchase Order to an invoice if you have one.""",
        'category': 'invoice'
    },
    {
        'keywords': ['gst', 'tax', 'tax calculation', 'gst calculation'],
        'pattern': r'\b(gst|tax).*(calculat|how|what|rate)',
        'response': """GST (Goods and Services Tax) is calculated automatically in this system:

**How it works:**
- **Intrastate (Same State):** CGST + SGST = Total GST%
- **Interstate (Different State):** IGST = Total GST%
- Default GST rate is 18% but can be customized per item

**Calculation:**
- GST Amount = (Item Subtotal × GST Rate) / 100
- Total Amount = Item Subtotal + GST Amount

You can set GST rates when adding items to invoices.""",
        'category': 'gst'
    },
    {
        'keywords': ['add customer', 'new customer', 'create customer', 'register customer'],
        'pattern': r'(add|create|new|register).*(customer|client)',
        'response': """To add a new customer:
1. Navigate to **Customers** in the sidebar
2. Click **"Add New Customer"** button
3. Fill in the required fields:
   - Customer Name
   - GSTIN (if applicable)
   - PAN Number
   - Complete Address (Street, City, State, Pincode)
   - Contact details (Phone, Email)
4. Click **"Save Customer"**

Once saved, you can select this customer when creating invoices.""",
        'category': 'customer'
    },
    {
        'keywords': ['print invoice', 'download invoice', 'pdf invoice', 'export invoice'],
        'pattern': r'(print|download|pdf|export).*(invoice)',
        'response': """To print or download an invoice:
1. Go to the **Invoices** page
2. Find the invoice you want to print
3. Click the **"View"** or **"PDF"** button
4. The invoice will open in a new window
5. Use your browser's print function (Ctrl+P) or download as PDF

You can also email invoices directly from the invoice view page.""",
        'category': 'invoice'
    },
    {
        'keywords': ['signature', 'digital signature', 'add signature', 'upload signature'],
        'pattern': r'(signature|sign).*(upload|add|how|where)',
        'response': """To add or upload your signature:
1. Go to **Signature** in the sidebar
2. Click **"Upload Signature"** or **"Add Signature"**
3. Upload an image of your signature (JPG, PNG)
4. Name your signature (e.g., "CEO Signature")
5. Set it as default if needed

Signatures will automatically appear on generated invoices and purchase orders.""",
        'category': 'signature'
    },
    {
        'keywords': ['dashboard', 'revenue', 'total sales', 'statistics'],
        'pattern': r'(dashboard|revenue|sales|statistics|stats|total)',
        'response': """The Dashboard shows:
- **Total Revenue:** Sum of all invoice amounts
- **Total Invoices:** Count of all invoices
- **Pending Amount:** Outstanding payments
- **Recent Invoices:** Latest invoice activity
- **Charts:** Visual representation of sales trends

Data is filtered by date ranges and automatically calculated from your invoices.""",
        'category': 'dashboard'
    },
    {
        'keywords': ['purchase order', 'po', 'create po', 'purchase'],
        'pattern': r'(purchase.*order|po|create.*po)',
        'response': """Purchase Orders help you track orders before converting to invoices:

**To create a PO:**
1. Go to **Purchase Orders** in the sidebar
2. Click **"Create New Purchase Order"**
3. Fill in vendor and item details
4. Save the PO

**To convert PO to Invoice:**
- Go to Purchase Orders list
- Click **"Convert to Invoice"** on any PO
- The system will auto-populate invoice details from the PO""",
        'category': 'purchase_order'
    },
    {
        'keywords': ['math', 'calculate', 'calculation', '=', 'equals', 'add', 'subtract', 'multiply', 'divide'],
        'pattern': r'(\d+\s*[+\-*/×÷]\s*\d+|^\d+\s*=\s*|\d+\s*\?\s*$)',
        'response': """I can help with math calculations! Here are some examples:

**Basic Math:**
- 1 + 1 = 2
- 5 × 3 = 15
- 10 ÷ 2 = 5
- 7 - 3 = 4

**For specific calculations**, I need the AI service enabled. However, I can tell you:
- **Addition:** Sum of two numbers
- **Subtraction:** Difference between numbers
- **Multiplication:** Product of numbers
- **Division:** Quotient of numbers

For your question "1+1=?", the answer is **2**.

Would you like help with a specific calculation or mathematical concept?""",
        'category': 'general'
    },
    {
        'keywords': ['boiling point', 'boiling', 'water', 'temperature', 'freezing point', 'boil', 'freeze'],
        'pattern': r'(boiling|freezing).*(point|temperature|water)|(what|is).*(boiling|freezing).*(point|temperature)',
        'response': """**Boiling Point of Water:**

- **Standard Conditions (Sea Level):** 100°C (212°F)
- **At Higher Altitudes:** Lower (due to reduced atmospheric pressure)
- **Freezing Point:** 0°C (32°F)

**Key Facts:**
- Pure water boils at exactly 100°C at standard atmospheric pressure (1 atm)
- Adding salt raises the boiling point slightly
- The boiling point decreases as altitude increases (about 1°C per 300m)

**Freezing Point:**
- Water freezes at 0°C (32°F) at standard pressure
- Can be lower with impurities or under pressure

Is there anything specific about water or temperature you'd like to know?""",
        'category': 'general'
    },
    {
        'keywords': ['biggest animal', 'largest animal', 'big animal', 'largest creature', 'biggest creature'],
        'pattern': r'(biggest|largest).*(animal|creature|mammal|sea|ocean|land)',
        'response': """**Biggest/Largest Animals:**

**Overall Largest Animal (by size and weight):**
- **Blue Whale** - The largest animal that has ever existed on Earth
  - Length: Up to 100 feet (30 meters)
  - Weight: Up to 200 tons (180,000 kg)
  - Lives in: Oceans worldwide
  - Heart size: As big as a small car!

**By Category:**
- **Largest Land Animal:** African Elephant (up to 13 feet tall, 7 tons)
- **Largest Reptile:** Saltwater Crocodile (up to 23 feet long)
- **Largest Bird:** Ostrich (up to 9 feet tall, 300 pounds)
- **Largest Fish:** Whale Shark (up to 40 feet long)

**Interesting Facts:**
- Blue whales eat up to 4 tons of krill per day
- Their tongue alone weighs as much as an elephant
- They communicate across hundreds of miles underwater

Did you know blue whales are not only the biggest animals alive today, but the biggest animals that have EVER lived, even bigger than dinosaurs!""",
        'category': 'general'
    },
    {
        'keywords': ['capital', 'capital city', 'what is the capital'],
        'pattern': r'(what|which).*(capital|capital city).*',
        'response': """I can help you find capital cities! 

**To get a specific answer**, please ask:
- "What is the capital of [country name]?"

For example:
- "What is the capital of India?" → New Delhi
- "What is the capital of France?" → Paris
- "What is the capital of Japan?" → Tokyo

**Top Capital Cities by Population:**
1. Tokyo, Japan (~37 million)
2. Delhi, India (~32 million)
3. Beijing, China (~21 million)

Ask me about any country's capital, and I'll provide the answer!""",
        'category': 'general'
    },
    {
        'keywords': ['edit invoice', 'update invoice', 'modify invoice', 'change invoice'],
        'pattern': r'(edit|update|modify|change).*(invoice)',
        'response': """**How to Edit an Invoice:**

1. Go to **Invoices** page from the sidebar
2. Find the invoice you want to edit
3. Click the **"Edit"** button (pencil icon) next to the invoice
4. Make your changes:
   - Update customer details
   - Modify items (add, edit, or remove)
   - Change dates, GST rates, amounts
   - Update status (paid/unpaid/partially paid)
5. Click **"Update Invoice"** to save changes

**Note:** Once an invoice is marked as paid, be careful when editing to maintain accurate records.

**To delete an invoice:** Use the delete button (trash icon) with OTP verification for security.""",
        'category': 'invoice'
    },
    {
        'keywords': ['delete invoice', 'remove invoice', 'cancel invoice'],
        'pattern': r'(delete|remove|cancel).*(invoice)',
        'response': """**How to Delete an Invoice:**

1. Go to **Invoices** page
2. Find the invoice you want to delete
3. Click the **"Delete"** button (trash icon)
4. Enter the OTP sent to your email for security verification
5. Confirm deletion

**Important:**
- Deletion is permanent and cannot be undone
- All associated invoice items will also be deleted
- This action is logged in the activity log
- You need admin privileges or proper authorization

**Note:** For record-keeping, consider marking invoices as "Cancelled" by editing the status instead of deleting.""",
        'category': 'invoice'
    },
    {
        'keywords': ['invoice status', 'paid invoice', 'unpaid invoice', 'mark paid', 'payment status'],
        'pattern': r'(invoice.*status|paid|unpaid|payment.*status|mark.*paid)',
        'response': """**Invoice Payment Status:**

The system tracks three payment statuses:

**1. Unpaid (Default)**
- Invoice created but payment not received
- Shown in red/orange on the dashboard
- Appears in "Outstanding" or "Pending" section

**2. Partially Paid**
- Some payment received but not full amount
- Useful for tracking large invoices paid in installments
- System tracks how much is still owed

**3. Paid**
- Full payment received
- Shown in green
- Invoice is considered complete

**To Change Status:**
1. Go to **Invoices** page
2. Click **"Edit"** on the invoice
3. Change the "Status" dropdown to desired status
4. Save changes

**Dashboard shows:**
- Total paid amount
- Total unpaid amount
- Number of overdue invoices
- Payment trends""",
        'category': 'invoice'
    },
    {
        'keywords': ['email invoice', 'send invoice', 'email invoice to customer'],
        'pattern': r'(email|send).*(invoice)',
        'response': """**How to Email an Invoice:**

1. Go to **Invoices** page
2. Open the invoice you want to email (click **"View"**)
3. Click the **"Email"** or **"Send Email"** button
4. The invoice PDF will be automatically attached
5. Enter recipient email (or select from customer email)
6. Add optional message
7. Click **"Send"**

**Requirements:**
- Company email must be configured in Company settings
- SMTP settings must be set up in environment variables
- Customer email should be available for auto-fill

**Email Includes:**
- Professional invoice PDF attachment
- Custom message (optional)
- Invoice details in email body

**Note:** Check your email configuration if emails are not sending.""",
        'category': 'invoice'
    },
    {
        'keywords': ['edit customer', 'update customer', 'modify customer', 'change customer'],
        'pattern': r'(edit|update|modify|change).*(customer|client)',
        'response': """**How to Edit Customer Information:**

1. Go to **Customers** page from sidebar
2. Find the customer you want to edit
3. Click the **"Edit"** button (pencil icon)
4. Update any information:
   - Name, GSTIN, PAN
   - Address details
   - Contact information
5. Click **"Update Customer"** to save

**All invoices associated with this customer will show updated information in future invoices.**""",
        'category': 'customer'
    },
    {
        'keywords': ['delete customer', 'remove customer'],
        'pattern': r'(delete|remove).*(customer|client)',
        'response': """**How to Delete a Customer:**

1. Go to **Customers** page
2. Find the customer to delete
3. Click **"Delete"** button (trash icon)
4. Confirm deletion

**Important:**
- Only delete if customer has no associated invoices
- If invoices exist, the system will prevent deletion to maintain data integrity
- Consider editing instead of deleting for record-keeping purposes""",
        'category': 'customer'
    },
    {
        'keywords': ['company setup', 'company details', 'setup company', 'company information', 'company profile'],
        'pattern': r'(company|setup|profile).*(company|details|information)',
        'response': """**Company Setup & Profile:**

**To Set Up Company Information:**
1. Click **"Company"** in the sidebar
2. Fill in all required fields:
   - **Company Name** (as registered)
   - **GSTIN** (15 characters, required for GST invoices)
   - **PAN Number** (10 characters)
   - **Complete Address** (Street, City, State, Pincode)
   - **Phone & Email**
3. **Upload Company Logo** (optional but recommended)
   - Formats: JPG, PNG, GIF
   - Logo appears on all invoices and purchase orders
4. Click **"Save"** or **"Update"**

**Why It's Important:**
- Company details appear on all invoices
- Required for GST compliance
- Logo adds professionalism to documents
- Contact info used for email communications

**To Update:** Go to Company page and modify any field, then save.""",
        'category': 'company'
    },
    {
        'keywords': ['convert po to invoice', 'po to invoice', 'create invoice from po'],
        'pattern': r'(convert|create.*from).*(po|purchase.*order).*(invoice)',
        'response': """**Convert Purchase Order to Invoice:**

**Step-by-Step:**
1. Go to **Purchase Orders** page
2. Find the PO you want to convert
3. Click **"Convert to Invoice"** button
4. System automatically:
   - Creates new invoice with PO details
   - Copies all items from PO
   - Sets customer from PO vendor
   - Pre-fills dates and amounts
5. Review and make any adjustments needed
6. Click **"Save Invoice"**

**Benefits:**
- Saves time - no need to re-enter all items
- Ensures accuracy - same items from PO
- Maintains connection between PO and Invoice

**Note:** You can still edit the invoice after conversion before saving.""",
        'category': 'purchase_order'
    },
    {
        'keywords': ['vendor', 'add vendor', 'create vendor', 'supplier'],
        'pattern': r'(vendor|supplier).*(add|create|new|manage)',
        'response': """**Vendor Management:**

**To Add a New Vendor:**
1. Go to **Vendors** in sidebar (if available) or Purchase Orders section
2. Click **"Add Vendor"** or **"New Vendor"**
3. Fill in vendor details:
   - Vendor Name
   - GSTIN (if applicable)
   - Complete Address
   - Contact Person
   - Phone & Email
   - Payment Terms
4. Save vendor

**Vendors are used when creating Purchase Orders.**

**Vendor vs Customer:**
- **Customer:** Who buys FROM you (for invoices)
- **Vendor:** Who you buy FROM (for purchase orders)""",
        'category': 'vendor'
    },
    {
        'keywords': ['delivery challan', 'challan', 'delivery note'],
        'pattern': r'(delivery.*challan|challan|delivery.*note)',
        'response': """**Delivery Challan:**

A delivery challan is a document used when goods are delivered to a customer.

**To Generate Delivery Challan:**
1. Go to **Invoices** page
2. Find the invoice for which you need a challan
3. Click **"Delivery Challan"** button (if available)
4. Fill in challan details:
   - PO Date
   - PO Type
   - Department
   - Contact Person
   - Number of Products
5. Generate PDF

**Use Cases:**
- For physical goods delivery
- Required for transportation
- Proof of delivery
- Contains PO reference details

**Note:** Delivery Challan is generated from invoice items and includes all product details.""",
        'category': 'invoice'
    },
    {
        'keywords': ['eway bill', 'e-way bill', 'eway', 'gst eway'],
        'pattern': r'(eway|e-way).*(bill|gst)',
        'response': """**E-Way Bill:**

E-Way Bill is required for transportation of goods under GST.

**How to Add E-Way Bill to Invoice:**
1. Create or edit an invoice
2. Scroll to **E-Way Bill** section
3. Fill in details:
   - **E-Way Bill Number** (primary)
   - **Mode:** Road or Rail
   - **Vehicle Number** (if road transport)
   - **RR Number** (if rail transport)
   - **Transporter ID**
   - **From Place** & **To Place**
   - **From State Code** & **To State Code**
   - **Valid Upto** date
4. System generates QR code automatically
5. Save invoice

**Requirements:**
- Mandatory for goods movement above ₹50,000
- Must be generated before transportation
- Valid for specified number of days
- QR code can be scanned for verification

**Note:** E-Way Bill details appear on invoice PDF.""",
        'category': 'gst'
    },
    {
        'keywords': ['cgst', 'sgst', 'igst', 'intrastate', 'interstate'],
        'pattern': r'\b(cgst|sgst|igst|intrastate|interstate)\b',
        'response': """**CGST, SGST, and IGST Explained:**

**Intrastate Transaction (Same State):**
- **CGST (Central GST):** Tax to Central Government
- **SGST (State GST):** Tax to State Government
- Both charged equally (e.g., 9% CGST + 9% SGST = 18% total)

**Interstate Transaction (Different States):**
- **IGST (Integrated GST):** Single tax to Central Government
- Covers both Central and State share
- Rate equals total GST (e.g., 18% IGST)

**How System Determines:**
- Checks if invoice company and customer are in same state
- If **same state:** Applies CGST + SGST
- If **different states:** Applies IGST

**Calculation Example:**
- Item Value: ₹10,000
- GST Rate: 18%
- Same State: ₹900 CGST + ₹900 SGST = ₹1,800 total GST
- Different State: ₹1,800 IGST

**Total Invoice = Item Value + GST Amount**""",
        'category': 'gst'
    },
    {
        'keywords': ['dashboard', 'analytics', 'statistics', 'reports', 'sales report'],
        'pattern': r'(dashboard|analytics|statistics|reports|sales.*report)',
        'response': """**Dashboard Features:**

The Dashboard provides comprehensive business insights:

**Key Metrics:**
- **Total Revenue:** Sum of all invoice amounts
- **Total Invoices:** Count of invoices created
- **Pending Amount:** Outstanding/unpaid invoices
- **Paid Amount:** Successfully paid invoices

**Invoice Status Breakdown:**
- Paid invoices (count and amount)
- Unpaid invoices
- Partially paid invoices
- Overdue invoices

**Business Statistics:**
- Total customers in database
- Total vendors
- Recent invoice activity
- Revenue trends

**Date Filtering:**
- Filter dashboard data by:
  - Today, This Week, This Month
  - Custom date range
  - Yearly view

**Quick Actions:**
- Create new invoice
- View recent invoices
- Quick access to key features

**Navigation:** Click **"Dashboard"** in sidebar to view.""",
        'category': 'dashboard'
    },
    {
        'keywords': ['login', 'logout', 'sign in', 'sign out', 'account', 'password'],
        'pattern': r'(login|logout|sign.*in|sign.*out|account|password|forgot.*password)',
        'response': """**User Account Management:**

**To Login:**
1. Go to login page
2. Enter your **Username** and **Password**
3. Click **"Login"**
4. You'll be redirected to Dashboard

**To Logout:**
1. Click your username/profile in top right
2. Select **"Logout"** option
3. Or click **"Logout"** in sidebar

**User Roles:**
- **Admin:** Full access to all features
- **Staff:** Limited access (depends on system configuration)

**Security Features:**
- Session-based authentication
- Password encryption
- CSRF protection
- Activity logging

**Note:** Contact administrator for password reset or account issues.""",
        'category': 'account'
    },
    {
        'keywords': ['navigation', 'menu', 'sidebar', 'how to navigate', 'where to find'],
        'pattern': r'(navigation|menu|sidebar|navigate|where.*find|how.*find)',
        'response': """**Navigation Guide:**

**Main Menu (Sidebar):**
- **Dashboard:** Home page with statistics
- **Invoices:** Create, view, edit, delete invoices
- **Customers:** Manage customer database
- **Purchase Orders:** Create and manage POs
- **Vendors:** Manage supplier information (if available)
- **Company:** Setup company profile and logo
- **Signature:** Upload and manage digital signatures
- **Logout:** Sign out from system

**Quick Actions:**
- Use search bar to find invoices/customers quickly
- Filter options available on list pages
- Breadcrumbs show your current location

**Tips:**
- Click menu items to navigate
- Menu collapses on mobile - click hamburger icon
- Use browser back button to return
- Keyboard shortcuts available (see Help menu)""",
        'category': 'navigation'
    },
    {
        'keywords': ['invoice number', 'invoice format', 'invoice numbering', 'invoice prefix'],
        'pattern': r'(invoice.*number|invoice.*format|invoice.*prefix|numbering)',
        'response': """**Invoice Numbering System:**

**Auto-Generated Invoice Numbers:**
- System automatically generates unique invoice numbers
- Format: Prefix + Sequential Number (e.g., INV-0001, INV-0002)
- No duplicate numbers allowed

**Invoice Number Features:**
- Unique identifier for each invoice
- Used for tracking and reference
- Appears on all invoice documents
- Cannot be manually changed (auto-generated)

**Invoice Number Format:**
- Default prefix: "INV"
- Can be customized in settings
- Sequential numbering ensures no gaps
- Includes leading zeros for sorting

**Finding Invoices:**
- Search by invoice number in invoices list
- Invoice number appears in:
  - Invoice list table
  - Invoice PDF header
  - Email subject line
  - Dashboard recent invoices""",
        'category': 'invoice'
    },
    {
        'keywords': ['troubleshoot', 'error', 'problem', 'issue', 'not working', 'help'],
        'pattern': r'(troubleshoot|error|problem|issue|not.*working|can.*t.*find|help)',
        'response': """**Troubleshooting Common Issues:**

**Invoice Not Saving:**
- Check all required fields are filled
- Verify customer is selected
- Ensure at least one item is added
- Check GST calculations are valid

**PDF Not Generating:**
- Clear browser cache
- Try different browser
- Check company details are complete
- Verify invoice has items

**Email Not Sending:**
- Check SMTP settings in environment
- Verify company email is configured
- Test with different email address
- Check spam folder

**Can't Delete Invoice:**
- Ensure you have admin privileges
- Check OTP was received in email
- Verify invoice isn't locked

**Data Not Showing:**
- Refresh the page
- Clear browser cache
- Check date filters are set correctly
- Verify you're logged in with correct account

**For More Help:** Ask specific questions like "How do I [action]?" and I'll provide detailed steps.""",
        'category': 'help'
    },
    {
        'keywords': ['help', 'how to', 'guide', 'tutorial', 'how do i'],
        'pattern': r'\b(help|how.*to|guide|tutorial|how.*do.*i|what.*is|where.*is)\b',
        'response': """**I'm Marvel, your Invoice System Assistant!**

I can help you with:

📄 **Invoice Management:**
- Create, edit, delete, print invoices
- Email invoices to customers
- Track payment status
- Generate delivery challans

👥 **Customer Management:**
- Add, edit, delete customers
- Manage customer database
- View customer history

📝 **Purchase Orders:**
- Create and manage POs
- Convert PO to invoice
- Track vendor orders

💰 **GST & Taxes:**
- Understand GST calculations
- CGST, SGST, IGST explained
- E-Way Bill generation
- Tax compliance

🏢 **Company Setup:**
- Configure company details
- Upload company logo
- Set up email/SMTP

✍️ **Digital Signatures:**
- Upload multiple signatures
- Set default signature
- Manage signatures

📊 **Dashboard & Reports:**
- View statistics
- Revenue tracking
- Invoice status overview

**Just ask me:**
- "How do I create an invoice?"
- "What is GST?"
- "How to email an invoice?"
- "Where do I find customers?"

I'm here to help with everything about the Invoice system! 🚀""",
        'category': 'help'
    }
]


class ChatbotService:
    """
    Hybrid chatbot service with rule engine and AI fallback
    Singleton pattern for shared instance across requests
    """
    _instance = None
    _initialized = False
    
    def __new__(cls):
        """Singleton pattern - return same instance"""
        if cls._instance is None:
            cls._instance = super(ChatbotService, cls).__new__(cls)
        return cls._instance
    
    def __init__(self):
        # Only initialize once
        if ChatbotService._initialized:
            return
        
        self.huggingface_api_key = os.environ.get('HUGGINGFACE_API_KEY')
        self.huggingface_model = os.environ.get('HUGGINGFACE_MODEL', 'mistralai/Mistral-7B-Instruct-v0.2')
        self.use_ai = bool(self.huggingface_api_key)
        self.use_local_ai = os.environ.get('USE_LOCAL_AI', 'false').lower() == 'true'
        self.local_ai_model_name = os.environ.get('LOCAL_AI_MODEL')
        self.local_ai = None
        
        # Initialize local AI if requested
        if self.use_local_ai and LOCAL_AI_AVAILABLE:
            try:
                self.local_ai = LocalAIModel(
                    model_name=self.local_ai_model_name,
                    device=os.environ.get('LOCAL_AI_DEVICE', 'cpu')
                )
                if self.local_ai.is_loaded():
                    print("✅ Local AI model loaded successfully")
                    self.use_ai = True  # Enable AI responses
                else:
                    print("⚠️ Local AI model failed to load, falling back to API/rules")
                    self.local_ai = None
            except Exception as e:
                print(f"⚠️ Local AI initialization error: {e}")
                print("💡 Falling back to Hugging Face API or rule-based responses")
                self.local_ai = None
        
        self.knowledge_base = KNOWLEDGE_BASE
        # Response cache: key -> (response, timestamp)
        self._response_cache: Dict[str, Tuple[str, float]] = {}
        self._cache_ttl = 3600  # 1 hour cache TTL
        self._max_retries = 2
        self._request_timeout = 15  # Increased timeout
        # Conversation summaries cache
        self._conversation_summaries: Dict[int, str] = {}
        
        ChatbotService._initialized = True
        
    def get_conversation_context(self, db_session, conversation_id: int, max_messages: int = 5) -> List[Dict[str, str]]:
        """
        Get recent conversation history for context
        Returns list of {role, message} dicts
        """
        try:
            from app import ChatMessage
            
            messages = db_session.query(ChatMessage).filter_by(
                conversation_id=conversation_id
            ).order_by(ChatMessage.created_at.desc()).limit(max_messages).all()
            
            # Reverse to get chronological order
            context = []
            for msg in reversed(messages):
                context.append({
                    'role': msg.role,
                    'message': msg.message
                })
            
            return context
        except Exception as e:
            print(f"Error getting conversation context: {e}")
            return []
    
    def _detect_query_type(self, message: str) -> Optional[str]:
        """Detect the type of query for better response tailoring"""
        message_lower = message.lower()
        
        # Question types
        if any(word in message_lower for word in ['how to', 'how do', 'how can', 'steps', 'guide', 'tutorial']):
            return "How-To / Step-by-Step Guide"
        elif any(word in message_lower for word in ['what is', 'what are', 'define', 'explain', 'meaning']):
            return "Definition / Explanation"
        elif any(word in message_lower for word in ['why', 'reason', 'because']):
            return "Reasoning / Cause-Effect"
        elif any(word in message_lower for word in ['compare', 'difference', 'vs', 'versus', 'better']):
            return "Comparison / Analysis"
        elif any(word in message_lower for word in ['when', 'time', 'schedule', 'deadline']):
            return "Time-Based / Scheduling"
        elif any(word in message_lower for word in ['where', 'location', 'place']):
            return "Location-Based"
        elif any(word in message_lower for word in ['calculate', 'formula', 'math', 'compute']):
            return "Calculation / Mathematical"
        elif any(word in message_lower for word in ['code', 'program', 'script', 'function', 'python', 'javascript']):
            return "Programming / Technical"
        elif any(word in message_lower for word in ['problem', 'error', 'issue', 'fix', 'troubleshoot']):
            return "Problem-Solving / Troubleshooting"
        elif message_lower.endswith('?'):
            return "General Question"
        
        return None
    
    def summarize_conversation(self, conversation_context: List[Dict[str, str]]) -> str:
        """Generate a brief summary of conversation for context"""
        if len(conversation_context) <= 2:
            return ""
        
        # Extract key topics from recent messages
        topics = []
        for msg in conversation_context[-5:]:  # Last 5 messages
            if msg['role'] == 'user':
                # Extract keywords (simple approach)
                words = msg['message'].lower().split()[:5]  # First 5 words
                topics.extend([w for w in words if len(w) > 3])
        
        if topics:
            unique_topics = list(set(topics))[:3]  # Top 3 unique topics
            return f"Recent conversation topics: {', '.join(unique_topics)}"
        
        return ""
    
    def process_message(self, user_message: str, user_context: Optional[Dict] = None, 
                       conversation_history: Optional[List[Dict[str, str]]] = None) -> str:
        """
        Process user message and return response
        First tries rule-based matching, then falls back to AI
        Uses caching for better performance
        """
        try:
            # Validate inputs
            if not user_message or not isinstance(user_message, str):
                return self.get_default_response()
            
            # Ensure conversation_history is a list
            if conversation_history is None:
                conversation_history = []
            elif not isinstance(conversation_history, list):
                conversation_history = []
            
            # Clean and normalize user input
            user_message_lower = user_message.lower().strip()
            
            if not user_message_lower:
                return self.get_default_response()
            
            # Check cache first
            cache_key = self._generate_cache_key(user_message_lower, user_context)
            cached_response = self._get_cached_response(cache_key)
            if cached_response:
                return cached_response
            
            # Try to answer simple math questions FIRST (before rule matching to prioritize calculations)
            math_answer = self._answer_math_question(user_message_lower)
            if math_answer:
                self._cache_response(cache_key, math_answer)
                return math_answer
            
            # Try rule-based matching (after math check)
            rule_response = self._match_rules(user_message_lower)
            if rule_response:
                self._cache_response(cache_key, rule_response)
                return rule_response
            
            # Fall back to AI if available (local or API)
            if self.use_ai:
                try:
                    # Try local AI first if available
                    if self.local_ai and self.local_ai.is_loaded():
                        ai_response = self._get_local_ai_response(user_message, conversation_history)
                    else:
                        # Fall back to Hugging Face API
                        ai_response = self._get_ai_response(user_message, user_context, conversation_history)
                    
                    if ai_response and ai_response != self.get_default_response():
                        self._cache_response(cache_key, ai_response)
                    return ai_response if ai_response else self._get_enhanced_fallback(user_message)
                except Exception as e:
                    print(f"Error in AI response: {e}")
                    return self._get_enhanced_fallback(user_message)
            
            # Enhanced fallback for better responses
            return self._get_enhanced_fallback(user_message)
        except Exception as e:
            print(f"Error in process_message: {e}")
            import traceback
            traceback.print_exc()
            return self.get_default_response()
    
    def _generate_cache_key(self, message: str, context: Optional[Dict] = None) -> str:
        """Generate cache key from message and context"""
        key_data = message
        if context:
            # Include relevant context for cache key
            key_data += f"|inv:{context.get('total_invoices', 0)}|cust:{context.get('total_customers', 0)}"
        return hashlib.md5(key_data.encode()).hexdigest()
    
    def _get_cached_response(self, cache_key: str) -> Optional[str]:
        """Get cached response if available and not expired"""
        if cache_key in self._response_cache:
            response, timestamp = self._response_cache[cache_key]
            if time.time() - timestamp < self._cache_ttl:
                return response
            else:
                # Remove expired entry
                del self._response_cache[cache_key]
        return None
    
    def _cache_response(self, cache_key: str, response: str):
        """Cache response"""
        # Limit cache size (keep last 100 entries)
        if len(self._response_cache) >= 100:
            # Remove oldest entry
            oldest_key = min(self._response_cache.keys(), 
                           key=lambda k: self._response_cache[k][1])
            del self._response_cache[oldest_key]
        
        self._response_cache[cache_key] = (response, time.time())
    
    def _match_rules(self, message: str) -> Optional[str]:
        """Enhanced rule matching with fuzzy matching and better pattern detection"""
        message_lower = message.lower()
        
        # PRIORITY: Check app-related categories first (invoice, customer, etc.)
        app_categories = ['invoice', 'customer', 'gst', 'dashboard', 'company', 'signature', 
                         'purchase_order', 'vendor', 'account', 'navigation', 'help']
        
        # First pass: Pattern matching (more specific, checked first) - prioritize app queries
        best_pattern_match = None
        best_pattern_score = 0
        
        # Check app-related entries first
        for knowledge in self.knowledge_base:
            if knowledge.get('pattern') and knowledge.get('category') in app_categories:
                try:
                    matches = re.search(knowledge['pattern'], message_lower, re.IGNORECASE)
                    if matches:
                        # Calculate match score (boost for app categories)
                        match_score = len(matches.group()) / len(message_lower) if message_lower else 0
                        keyword_overlap = sum(1 for kw in knowledge['keywords'] if kw in message_lower)
                        total_score = match_score + (keyword_overlap * 0.3) + 0.2  # Bonus for app category
                        
                        if total_score > best_pattern_score:
                            best_pattern_score = total_score
                            best_pattern_match = knowledge['response']
                except re.error:
                    continue
        
        # Then check general categories
        if not best_pattern_match or best_pattern_score < 0.4:
            for knowledge in self.knowledge_base:
                if knowledge.get('pattern') and knowledge.get('category') not in app_categories:
                    try:
                        matches = re.search(knowledge['pattern'], message_lower, re.IGNORECASE)
                        if matches:
                            match_score = len(matches.group()) / len(message_lower) if message_lower else 0
                            keyword_overlap = sum(1 for kw in knowledge['keywords'] if kw in message_lower)
                            total_score = match_score + (keyword_overlap * 0.3)
                            
                            if total_score > best_pattern_score:
                                best_pattern_score = total_score
                                best_pattern_match = knowledge['response']
                    except re.error:
                        continue
        
        if best_pattern_match and best_pattern_score > 0.3:  # Only return if score is good
            return best_pattern_match
        
        # Second pass: Exact keyword matching with priority - APP CATEGORIES FIRST
        app_keyword_matches = []
        general_keyword_matches = []
        
        for knowledge in self.knowledge_base:
            keywords = knowledge['keywords']
            matches = sum(1 for keyword in keywords if keyword in message_lower)
            if matches > 0:
                if knowledge.get('category') in app_categories:
                    app_keyword_matches.append((matches + 0.5, knowledge))  # Boost app matches
                else:
                    general_keyword_matches.append((matches, knowledge))
        
        # Sort by number of matches (descending)
        all_matches = sorted(app_keyword_matches + general_keyword_matches, reverse=True, key=lambda x: x[0])
        
        if all_matches:
            # Return the entry with most keyword matches
            if all_matches[0][0] >= 2.5:  # At least 2 keywords matched (app gets boost)
                return all_matches[0][1]['response']
            elif all_matches[0][0] >= 1.5:  # App category with 1+ keywords
                return all_matches[0][1]['response']
            elif all_matches[0][0] >= 1:
                # Single keyword match - check if it's a primary keyword
                knowledge = all_matches[0][1]
                if any(kw in message_lower for kw in knowledge['keywords'][:2]):  # Top 2 keywords
                    return knowledge['response']
        
        # Third pass: Lower priority pattern matching (fallback)
        best_match = None
        best_score = 0
        
        for knowledge in self.knowledge_base:
            if knowledge.get('pattern'):
                try:
                    matches = re.search(knowledge['pattern'], message_lower, re.IGNORECASE)
                    if matches:
                        # Calculate match score based on match length and keyword overlap
                        match_score = len(matches.group()) / len(message_lower) if message_lower else 0
                        keyword_overlap = sum(1 for kw in knowledge['keywords'] if kw in message_lower)
                        total_score = match_score + (keyword_overlap * 0.3)
                        
                        if total_score > best_score:
                            best_score = total_score
                            best_match = knowledge['response']
                except re.error:
                    continue
        
        # Third pass: Fuzzy matching for common variations
        if not best_match:
            # Common query patterns
            fuzzy_patterns = {
                r'\b(how\s+to|steps?\s+to|way\s+to)\s+(create|make|generate|add|do)\s+(invoice)': 'invoice',
                r'\b(gst|tax)\s+(rate|calculation|how|what|explain)': 'gst',
                r'\b(add|create|new|register)\s+(customer|client)': 'customer',
                r'\b(help|guide|tutorial|how)\s+(with|for|on)': 'general'
            }
            
            for pattern, category in fuzzy_patterns.items():
                if re.search(pattern, message_lower, re.IGNORECASE):
                    for knowledge in self.knowledge_base:
                        if knowledge.get('category') == category:
                            return knowledge['response']
        
        return best_match
    
    def _get_local_ai_response(
        self,
        user_message: str,
        conversation_history: Optional[List[Dict[str, str]]] = None
    ) -> str:
        """Get response from local AI model"""
        if not self.local_ai or not self.local_ai.is_loaded():
            return self.get_default_response()
        
        try:
            system_prompt = """You are Marvel, an advanced, highly intelligent AI assistant with comprehensive knowledge across all domains. 
You can answer questions about invoices, business, technology, science, general knowledge, and anything else.
Be helpful, accurate, and provide detailed, well-structured responses."""
            
            response = self.local_ai.generate_response(
                user_message=user_message,
                system_prompt=system_prompt,
                conversation_history=conversation_history,
                max_length=512,
                temperature=0.7,
                top_p=0.9
            )
            
            return response if response else self.get_default_response()
            
        except Exception as e:
            print(f"Local AI error: {e}")
            return self.get_default_response()
    
    def _answer_math_question(self, message: str) -> Optional[str]:
        """Answer simple math questions including multi-number expressions"""
        try:
            # First, try to evaluate simple expressions like "1+233+434+3"
            # Clean the message: remove spaces and question marks
            clean_msg = message.strip().rstrip('?').replace(' ', '')
            
            # Pattern: sequence of numbers with +, -, *, /, ×, ÷
            # Examples: "1+233+434+3", "10*5*2", "100-50-25"
            if re.match(r'^[\d+\-*/×÷]+$', clean_msg):
                try:
                    # Replace Unicode operators
                    expression = clean_msg.replace('×', '*').replace('÷', '/')
                    
                    # Simple safety check - only allow digits and operators
                    if not re.match(r'^[\d+\-*/]+$', expression):
                        return None
                    
                    # Evaluate safely
                    result = eval(expression)
                    
                    # Format the expression nicely
                    formatted = expression.replace('*', ' × ').replace('/', ' ÷ ').replace('+', ' + ').replace('-', ' - ')
                    formatted = formatted.strip()
                    
                    return f"**Answer:** {formatted} = **{result}**"
                except:
                    pass
            
            # Also handle two-number operations (original patterns)
            math_patterns = [
                (r'^(\d+)\s*\+\s*(\d+)\s*=?\s*\??$', lambda m: f"{m.group(1)} + {m.group(2)} = {int(m.group(1)) + int(m.group(2))}"),
                (r'^(\d+)\s*-\s*(\d+)\s*=?\s*\??$', lambda m: f"{m.group(1)} - {m.group(2)} = {int(m.group(1)) - int(m.group(2))}"),
                (r'^(\d+)\s*[\*×]\s*(\d+)\s*=?\s*\??$', lambda m: f"{m.group(1)} × {m.group(2)} = {int(m.group(1)) * int(m.group(2))}"),
                (r'^(\d+)\s*[\/÷]\s*(\d+)\s*=?\s*\??$', lambda m: f"{m.group(1)} ÷ {m.group(2)} = {int(m.group(1)) / int(m.group(2))}" if int(m.group(2)) != 0 else "Cannot divide by zero"),
                # Also handle with spaces and question marks: "1 + 1 = ?"
                (r'(\d+)\s*\+\s*(\d+)\s*=?\s*\?', lambda m: f"{m.group(1)} + {m.group(2)} = {int(m.group(1)) + int(m.group(2))}"),
                (r'(\d+)\s*-\s*(\d+)\s*=?\s*\?', lambda m: f"{m.group(1)} - {m.group(2)} = {int(m.group(1)) - int(m.group(2))}"),
                (r'(\d+)\s*[\*×]\s*(\d+)\s*=?\s*\?', lambda m: f"{m.group(1)} × {m.group(2)} = {int(m.group(1)) * int(m.group(2))}"),
                (r'(\d+)\s*[\/÷]\s*(\d+)\s*=?\s*\?', lambda m: f"{m.group(1)} ÷ {m.group(2)} = {int(m.group(1)) / int(m.group(2))}" if int(m.group(2)) != 0 else "Cannot divide by zero"),
            ]
            
            for pattern, func in math_patterns:
                match = re.search(pattern, message)
                if match:
                    try:
                        result = func(match)
                        return f"**Answer:** {result}"
                    except Exception as e:
                        print(f"Math calculation error: {e}")
                        pass
            
        except Exception as e:
            print(f"Math question processing error: {e}")
        
        return None
    
    def _get_ai_response(self, user_message: str, user_context: Optional[Dict] = None,
                        conversation_history: Optional[List[Dict[str, str]]] = None) -> str:
        """Get response from Hugging Face API with retry logic"""
        if not self.huggingface_api_key:
            return self.get_default_response()
        
        # Enhanced system prompt for handling ALL types of queries perfectly
        system_prompt = """You are Marvel, an advanced, highly intelligent AI assistant with comprehensive knowledge across all domains. You excel at:

**Core Expertise:**
- Invoice management systems, GST calculations, business finance, accounting
- Business strategies, management, entrepreneurship, marketing, sales
- Technology: Programming (Python, JavaScript, etc.), software development, web technologies
- Mathematics, science, physics, chemistry, biology
- History, geography, culture, literature, arts
- Current events, news, politics, economics
- Health, medicine, psychology, wellness
- Education, learning, productivity, personal development
- Engineering, architecture, design
- Cooking, recipes, nutrition
- Travel, languages, translation
- Sports, entertainment, gaming
- And ANY other topic imaginable

**Response Guidelines:**
1. **Accuracy First**: Provide factually correct, up-to-date information
2. **Comprehensive**: Give complete, thorough answers that fully address the question
3. **Well-Structured**: Use clear formatting with headers, bullet points, examples when helpful
4. **Adaptive Style**: Match the complexity of your answer to the question's complexity
5. **Context-Aware**: Consider conversation history and related topics
6. **Multi-Angle Approach**: For complex topics, cover multiple perspectives
7. **Practical Examples**: Include real-world examples and use cases
8. **Step-by-Step**: For how-to questions, provide clear step-by-step instructions
9. **Code Examples**: For programming questions, provide working code examples
10. **Honesty**: If uncertain, clearly state limitations and suggest resources

**Response Format:**
- Use markdown for formatting (headers, bold, lists, code blocks)
- Break down complex answers into digestible sections
- Use examples and analogies for clarity
- End with a helpful summary or next steps when appropriate

**Your Goal**: Provide the most comprehensive, accurate, and helpful response possible for every query, regardless of topic complexity."""

        # Add user context if available
        context_info = ""
        if user_context:
            if user_context.get('total_invoices'):
                context_info += f"\nUser has {user_context['total_invoices']} invoices."
            if user_context.get('total_customers'):
                context_info += f"\nUser has {user_context['total_customers']} customers."
        
        # Enhanced conversation history context
        history_context = ""
        if conversation_history and len(conversation_history) > 1:
            # Include last few messages for context (excluding current message)
            recent_history = conversation_history[-6:-1] if len(conversation_history) > 1 else conversation_history[:-1]
            if recent_history:
                history_context = "\n\nConversation History (for context - answer based on this):\n"
                for i, msg in enumerate(recent_history, 1):
                    role_label = "User" if msg['role'] == 'user' else "Marvel (Assistant)"
                    # Include more context for better continuity
                    msg_content = msg['message'][:150] if len(msg['message']) > 150 else msg['message']
                    history_context += f"{i}. {role_label}: {msg_content}\n"
                history_context += "\nNote: Use the conversation history to provide contextually relevant answers. Reference previous topics when relevant."
        
        # Enhanced prompt construction
        query_type = self._detect_query_type(user_message)
        type_hint = ""
        if query_type:
            type_hint = f"\n\nQuery Type Detected: {query_type}\nProvide a comprehensive, well-structured answer suitable for this type of query."
        
        prompt = f"{system_prompt}{context_info}{history_context}{type_hint}\n\nCurrent User Question: {user_message}\n\nProvide a comprehensive, accurate, and helpful response:\n\nMarvel:"
        
        # Retry logic
        for attempt in range(self._max_retries + 1):
            try:
                # Call Hugging Face Inference API
                api_url = f"https://api-inference.huggingface.co/models/{self.huggingface_model}"
                headers = {
                    "Authorization": f"Bearer {self.huggingface_api_key}",
                    "Content-Type": "application/json"
                }
                
                # Enhanced parameters for better, more comprehensive responses
                payload = {
                    "inputs": prompt,
                    "parameters": {
                        "max_new_tokens": 500,  # Increased for comprehensive responses
                        "temperature": 0.8,  # Slightly higher for more creative/detailed responses
                        "return_full_text": False,
                        "top_p": 0.95,  # Higher for more diverse, comprehensive answers
                        "top_k": 50,  # Top-k sampling for better quality
                        "repetition_penalty": 1.2,  # Prevent repetitive responses
                        "do_sample": True  # Enable sampling for better diversity
                    }
                }
                
                response = requests.post(api_url, headers=headers, json=payload, 
                                      timeout=self._request_timeout)
                
                if response.status_code == 200:
                    result = response.json()
                    if isinstance(result, list) and len(result) > 0:
                        generated_text = result[0].get('generated_text', '')
                        # Enhanced response cleaning and formatting
                        generated_text = generated_text.strip()
                        
                        # Remove duplicate prompt if present
                        if user_message.lower() in generated_text.lower():
                            generated_text = re.sub(re.escape(user_message), '', generated_text, flags=re.IGNORECASE).strip()
                        
                        # Remove common prefixes and markers
                        prefixes = ['assistant:', 'marvel:', 'answer:', 'response:', 'here', 'sure', 'of course']
                        for prefix in prefixes:
                            if generated_text.lower().startswith(prefix.lower() + ' '):
                                generated_text = generated_text[len(prefix):].strip()
                            if generated_text.lower().startswith(prefix.lower() + ':'):
                                generated_text = generated_text[len(prefix) + 1:].strip()
                        
                        # Remove common suffixes
                        suffixes = ['hope this helps', 'let me know if', 'feel free to ask']
                        for suffix in suffixes:
                            if generated_text.lower().endswith(suffix.lower()):
                                # Keep the main content, just remove the ending phrase
                                pass
                        
                        # Clean up multiple newlines
                        generated_text = re.sub(r'\n{3,}', '\n\n', generated_text)
                        
                        # Ensure minimum response length for quality
                        if len(generated_text) < 10:
                            # Try alternative response generation
                            return self._get_enhanced_fallback(user_message)
                        
                        return generated_text if generated_text else self.get_default_response()
                
                # Handle rate limiting or model loading
                if response.status_code == 503:
                    if attempt < self._max_retries:
                        wait_time = (attempt + 1) * 2  # Exponential backoff
                        time.sleep(wait_time)
                        continue
                    return "I'm processing your request. The model is loading. Please try again in a few moments."
                
                # Handle other errors
                if response.status_code == 429:
                    return "I've hit my rate limit. Please wait a moment and try again."
                
            except requests.exceptions.Timeout:
                if attempt < self._max_retries:
                    continue
                return "Request timed out. Please try again."
            except requests.exceptions.RequestException as e:
                if attempt < self._max_retries:
                    time.sleep(1)  # Brief wait before retry
                    continue
                print(f"AI API Error: {e}")
        
        return self._get_enhanced_fallback(user_message)
    
    def get_default_response(self) -> str:
        """Default response when no match is found"""
        return """I'm Marvel, and I'm here to help with anything you need!

I can assist with:
• **Invoice System** - Creating invoices, GST calculations, customers, etc.
• **Business Questions** - Business strategies, management, finance
• **General Knowledge** - Ask me about anything
• **Technical Help** - Programming, technology, tools

Feel free to ask me any question, and I'll do my best to help!"""
    
    def _get_enhanced_fallback(self, user_message: str) -> str:
        """Enhanced fallback for better responses when AI fails"""
        message_lower = user_message.lower()
        
        # Category detection for better fallback responses
        if any(word in message_lower for word in ['how', 'what', 'why', 'when', 'where', 'who']):
            return f"""I understand you're asking: "{user_message}"

I'm Marvel, your AI assistant, and I'm designed to help with a wide range of topics including:
• **Technical Questions**: Programming, software, technology
• **Business & Finance**: Accounting, invoicing, GST, business strategies
• **General Knowledge**: Science, history, current events
• **How-To Guides**: Step-by-step instructions for tasks
• **Problem Solving**: Troubleshooting, analysis, solutions

To provide the most accurate and comprehensive answer, I need access to the AI service. 

**Current Status**: AI service is temporarily unavailable. 

**What you can do:**
1. Check if `HUGGINGFACE_API_KEY` is set in your environment
2. Get a free API key at: https://huggingface.co/settings/tokens
3. For invoice system questions, try asking: "How do I create an invoice?"

I'll do my best to help once the AI service is available!"""
        
        return self.get_default_response()
    
    def get_context_for_user(self, db_session, user_id: int) -> Dict:
        """Get user context for AI responses"""
        try:
            from app import Invoice, Customer
            
            total_invoices = db_session.query(Invoice).filter_by(user_id=user_id).count()
            total_customers = db_session.query(Customer).filter_by(user_id=user_id).count()
            
            return {
                'total_invoices': total_invoices,
                'total_customers': total_customers
            }
        except Exception as e:
            print(f"Error getting user context: {e}")
            return {}

