#!/usr/bin/env python3
"""
Quick fix script to add is_sac column to invoice table
Run this in Railway console or locally if connected to Railway database
"""

import os
import sys

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import app, db
from sqlalchemy import text

def fix_is_sac_column():
    """Add is_sac column to invoice table if it doesn't exist"""
    
    print("🔧 Fixing is_sac column in invoice table...")
    print("=" * 60)
    
    with app.app_context():
        try:
            # Check if column exists
            from sqlalchemy import inspect
            inspector = inspect(db.engine)
            
            # Get all columns in invoice table
            columns = inspector.get_columns('invoice')
            column_names = [col['name'] for col in columns]
            
            if 'is_sac' in column_names:
                print("✅ Column 'is_sac' already exists in invoice table")
                return True
            
            # Add the column
            print("📝 Adding is_sac column to invoice table...")
            
            # Determine SQL based on database type
            db_url = str(db.engine.url)
            if 'postgresql' in db_url:
                # PostgreSQL
                db.session.execute(text("""
                    DO $$ 
                    BEGIN
                        IF NOT EXISTS (
                            SELECT 1 FROM information_schema.columns 
                            WHERE table_name = 'invoice' AND column_name = 'is_sac'
                        ) THEN
                            ALTER TABLE invoice ADD COLUMN is_sac BOOLEAN DEFAULT FALSE;
                        END IF;
                    END $$;
                """))
            else:
                # SQLite
                db.session.execute(text("ALTER TABLE invoice ADD COLUMN is_sac INTEGER DEFAULT 0"))
            
            db.session.commit()
            print("✅ Successfully added is_sac column to invoice table!")
            print("=" * 60)
            return True
            
        except Exception as e:
            db.session.rollback()
            print(f"❌ Error: {str(e)}")
            print("=" * 60)
            
            # If it's a "column already exists" error, that's okay
            if "already exists" in str(e) or "duplicate column" in str(e).lower():
                print("✅ Column already exists (this is fine)")
                return True
            
            return False

if __name__ == "__main__":
    success = fix_is_sac_column()
    sys.exit(0 if success else 1)

