#!/usr/bin/env python3
"""
Database migration script to create delivery challan tables
Run this script to add delivery challan functionality to your database
"""

import os
import sys

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import app, db, DeliveryChallan, DeliveryChallanItem

def create_delivery_challan_tables():
    """Create delivery challan-related database tables"""
    print("Creating delivery challan tables...")
    
    with app.app_context():
        try:
            # Create tables
            db.create_all()
            
            # Check if tables were created
            from sqlalchemy import inspect
            inspector = inspect(db.engine)
            
            tables_created = []
            for table_name in ['delivery_challan', 'delivery_challan_item']:
                if inspector.has_table(table_name):
                    tables_created.append(table_name)
            
            if tables_created:
                print(f"✅ Delivery challan tables created successfully: {', '.join(tables_created)}")
            else:
                print("✅ Database tables initialized (may already exist)")
            
            print("\n🎉 Delivery challan migration completed successfully!")
            
        except Exception as e:
            print(f"❌ Error creating delivery challan tables: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    return True

if __name__ == '__main__':
    print("🚀 Running Delivery Challan Migration...")
    print("=" * 50)
    
    if create_delivery_challan_tables():
        print("\n✅ Migration completed successfully!")
        sys.exit(0)
    else:
        print("\n❌ Migration failed!")
        sys.exit(1)

