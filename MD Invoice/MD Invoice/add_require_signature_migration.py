#!/usr/bin/env python3
"""
Digital signatures migration script
Adds require_digital_signature boolean column to document tables
"""

import os
import sys

# Add the project root to Python path
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

try:
    from app import app, db
    from sqlalchemy import text
    print("✅ Successfully imported app module")
except ImportError as e:
    print(f"❌ Could not import app module: {str(e)}")
    print("Make sure you're running this from the project root directory")
    sys.exit(1)

def add_require_signature_column():
    """Add require_digital_signature column to document tables"""
    tables = ['invoice', 'offer', 'purchase_order', 'delivery_challan']
    col_name = 'require_digital_signature'
    col_type = 'BOOLEAN'
    
    print("🚀 DIGITAL SIGNATURE (REQUIRE) MIGRATION STARTING")
    print("=" * 60)
    
    try:
        with app.app_context():
            from sqlalchemy import inspect
            inspector = inspect(db.engine)
            
            for table in tables:
                print(f"\n🔧 Processing table: {table}")
                existing_columns = [col['name'] for col in inspector.get_columns(table)]
                
                if col_name in existing_columns:
                    print(f"   ✅ Column {col_name} already exists in {table}")
                else:
                    print(f"   ➕ Adding {col_name} to {table}...")
                    try:
                        # SQLite doesn't strictly enforce BOOLEAN but it accepts it
                        # Set default to False (0 in SQLite)
                        db.session.execute(text(f"ALTER TABLE {table} ADD COLUMN {col_name} {col_type} DEFAULT 0"))
                        db.session.commit()
                        print(f"   ✅ Column {col_name} added to {table}")
                    except Exception as e:
                        print(f"   ❌ Error adding {col_name} to {table}: {str(e)}")
                        db.session.rollback()

            print("\n✅ Migration completed successfully!")
            return True
            
    except Exception as e:
        print(f"❌ Error during migration: {str(e)}")
        db.session.rollback()
        return False

if __name__ == "__main__":
    if add_require_signature_column():
        sys.exit(0)
    else:
        sys.exit(1)
