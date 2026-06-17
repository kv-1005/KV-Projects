#!/usr/bin/env python3
"""
Database migration script to create chatbot tables
Run this script to add chatbot functionality to your database
"""

import os
import sys

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import app, db, ChatConversation, ChatMessage, ChatbotKnowledge

def create_chatbot_tables():
    """Create chatbot-related database tables"""
    print("Creating chatbot tables...")
    
    with app.app_context():
        try:
            # Create tables
            db.create_all()
            
            # Check if tables were created
            from sqlalchemy import inspect
            inspector = inspect(db.engine)
            
            tables_created = []
            for table_name in ['chat_conversations', 'chat_messages', 'chatbot_knowledge']:
                if inspector.has_table(table_name):
                    tables_created.append(table_name)
            
            if tables_created:
                print(f"[OK] Chatbot tables created successfully: {', '.join(tables_created)}")
            else:
                print("[OK] Database tables initialized (may already exist)")
            
            # Initialize knowledge base with default entries
            print("\nInitializing knowledge base...")
            initialize_knowledge_base()
            
            print("\n[OK] Chatbot setup completed successfully!")
            print("\nTo enable AI features, set HUGGINGFACE_API_KEY in your environment variables.")
            print("Get a free API key at: https://huggingface.co/settings/tokens")
            
        except Exception as e:
            print(f"[ERROR] Error creating chatbot tables: {e}")
            return False
    
    return True

def initialize_knowledge_base():
    """Initialize the knowledge base with default entries"""
    knowledge_entries = [
        {
            'keyword': 'invoice creation',
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
            'keyword': 'gst calculation',
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
            'keyword': 'customer management',
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
        }
    ]
    
    entries_added = 0
    for entry in knowledge_entries:
        # Check if entry already exists
        existing = ChatbotKnowledge.query.filter_by(keyword=entry['keyword']).first()
        if not existing:
            kb_entry = ChatbotKnowledge(
                keyword=entry['keyword'],
                pattern=entry.get('pattern'),
                response=entry['response'],
                category=entry['category']
            )
            db.session.add(kb_entry)
            entries_added += 1
    
    if entries_added > 0:
        db.session.commit()
        print(f"[OK] Added {entries_added} knowledge base entries")
    else:
        print("[INFO] Knowledge base entries already exist")

if __name__ == '__main__':
    create_chatbot_tables()

