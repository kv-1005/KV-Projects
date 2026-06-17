#!/usr/bin/env python3
"""
Standalone script to add is_sac column - doesn't require importing app.py
Uses Railway DATABASE_URL environment variable
"""

import os
import sys

try:
    import psycopg2
    from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
except ImportError:
    print("❌ psycopg2 not installed. Installing...")
    print("Run: pip install psycopg2-binary")
    sys.exit(1)

def fix_is_sac_column():
    """Add is_sac column to invoice table"""
    
    print("🔧 Fixing is_sac column in invoice table...")
    print("=" * 60)
    
    # Get database URL from Railway environment
    database_url = os.environ.get('DATABASE_URL')
    if not database_url:
        print("❌ DATABASE_URL not found in environment variables")
        print("💡 Make sure you're running this with: railway run python fix_is_sac_standalone.py")
        return False
    
    try:
        # Connect to PostgreSQL database
        print("📡 Connecting to Railway PostgreSQL database...")
        conn = psycopg2.connect(database_url)
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cursor = conn.cursor()
        
        print("✅ Connected to database")
        
        # Check if column exists
        print("🔍 Checking if is_sac column exists...")
        cursor.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'invoice' AND column_name = 'is_sac'
        """)
        
        if cursor.fetchone():
            print("✅ Column 'is_sac' already exists in invoice table")
            cursor.close()
            conn.close()
            return True
        
        # Add the column
        print("📝 Adding is_sac column to invoice table...")
        cursor.execute("""
            ALTER TABLE invoice ADD COLUMN is_sac BOOLEAN DEFAULT FALSE
        """)
        
        print("✅ Successfully added is_sac column to invoice table!")
        print("=" * 60)
        
        # Verify
        cursor.execute("""
            SELECT column_name, data_type, column_default 
            FROM information_schema.columns 
            WHERE table_name = 'invoice' AND column_name = 'is_sac'
        """)
        result = cursor.fetchone()
        if result:
            print(f"✅ Verified: {result[0]} ({result[1]}) with default {result[2]}")
        
        cursor.close()
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        print("=" * 60)
        return False

if __name__ == "__main__":
    success = fix_is_sac_column()
    sys.exit(0 if success else 1)

