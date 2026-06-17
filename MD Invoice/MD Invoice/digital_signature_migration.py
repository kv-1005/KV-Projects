#!/usr/bin/env python3
"""
Digital signatures audit fields migration script
Adds signed_at, signed_by_id, and signature_hash to document tables
"""

import os
import sys
from datetime import datetime

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

def add_audit_columns():
    """Add audit columns to document tables"""
    tables = ['invoice', 'offer', 'purchase_order', 'delivery_challan']
    columns = [
        ('signed_at', 'DATETIME'),
        ('signed_by_id', 'INTEGER'),
        ('signature_hash', 'VARCHAR(128)')
    ]
    
    print("🚀 DIGITAL SIGNATURE MIGRATION STARTING")
    print("=" * 60)
    
    try:
        with app.app_context():
            from sqlalchemy import inspect
            inspector = inspect(db.engine)
            
            for table in tables:
                print(f"\n🔧 Processing table: {table}")
                existing_columns = [col['name'] for col in inspector.get_columns(table)]
                
                for col_name, col_type in columns:
                    if col_name in existing_columns:
                        print(f"   ✅ Column {col_name} already exists in {table}")
                    else:
                        print(f"   ➕ Adding {col_name} to {table}...")
                        try:
                            # Use proper SQL for column addition
                            # Note: SQLite doesn't support multiple columns in one ALTER TABLE
                            db.session.execute(text(f"ALTER TABLE {table} ADD COLUMN {col_name} {col_type}"))
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
    if add_audit_columns():
        sys.exit(0)
    else:
        sys.exit(1)
