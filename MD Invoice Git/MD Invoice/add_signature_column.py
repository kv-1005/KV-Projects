#!/usr/bin/env python3
"""
Add signature_data column to the user table
Database migration script
"""

import sqlite3
import os
import sys

def add_signature_column():
    """Add signature_data column to user table"""
    
    # Database file path
    db_path = 'instance/invoice_generator_dev.db'
    
    if not os.path.exists(db_path):
        print(f"❌ Database file not found: {db_path}")
        return False
    
    try:
        # Connect to database
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check if column already exists
        cursor.execute("PRAGMA table_info(user)")
        columns = [column[1] for column in cursor.fetchall()]
        
        if 'signature_data' in columns:
            print("✅ signature_data column already exists")
            conn.close()
            return True
        
        # Add signature_data column
        cursor.execute("ALTER TABLE user ADD COLUMN signature_data TEXT")
        conn.commit()
        
        print("✅ signature_data column added successfully")
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Error adding signature_data column: {str(e)}")
        if 'conn' in locals():
            conn.close()
        return False

if __name__ == "__main__":
    print("🔄 Adding signature_data column to user table...")
    success = add_signature_column()
    
    if success:
        print("🎉 Migration completed successfully!")
        print("✅ E-signature feature ready")
    else:
        print("❌ Migration failed!")
        sys.exit(1)
