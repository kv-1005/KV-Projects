#!/usr/bin/env python3
"""
COMPREHENSIVE RAILWAY POSTGRESQL MIGRATION
Adds all missing columns to invoice, purchase_order, and other tables.
"""

import os
import sys
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

def migrate():
    print("🚀 Starting comprehensive Railway PostgreSQL migration...")
    
    # Get database URL from environment
    database_url = os.environ.get('DATABASE_URL')
    if not database_url:
        print("❌ DATABASE_URL not found in environment variables")
        return False
    
    try:
        # Connect to PostgreSQL database
        print("📡 Connecting to PostgreSQL...")
        conn = psycopg2.connect(database_url)
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cursor = conn.cursor()
        print("✅ Connected!")

        # Define tables and columns to add
        migrations = {
            'invoice': [
                ('paid_amount', 'DECIMAL(10,2) DEFAULT 0'),
                ('require_digital_signature', 'BOOLEAN DEFAULT FALSE'),
                ('selected_signature_id', 'INTEGER'),
                ('signed_at', 'TIMESTAMP'),
                ('signed_by_id', 'INTEGER'),
                ('signature_hash', 'VARCHAR(128)'),
                ('notes', 'TEXT'),
                ('eway_bill', 'VARCHAR(20)'),
                ('eway_mode', 'VARCHAR(20)'),
                ('vehicle_number', 'VARCHAR(20)'),
                ('rr_number', 'VARCHAR(20)'),
                ('transporter_id', 'VARCHAR(50)'),
                ('from_place', 'VARCHAR(100)'),
                ('from_state_code', 'VARCHAR(2)'),
                ('to_place', 'VARCHAR(100)'),
                ('to_state_code', 'VARCHAR(2)'),
                ('eway_valid_upto', 'VARCHAR(20)'),
                ('eway_qr', 'TEXT')
            ],
            'purchase_order': [
                ('require_digital_signature', 'BOOLEAN DEFAULT FALSE'),
                ('selected_signature_id', 'INTEGER'),
                ('signed_at', 'TIMESTAMP'),
                ('signed_by_id', 'INTEGER'),
                ('signature_hash', 'VARCHAR(128)')
            ],
            'delivery_challan': [
                ('require_digital_signature', 'BOOLEAN DEFAULT FALSE'),
                ('selected_signature_id', 'INTEGER'),
                ('signed_at', 'TIMESTAMP'),
                ('signed_by_id', 'INTEGER'),
                ('signature_hash', 'VARCHAR(128)')
            ],
            'offer': [
                ('require_digital_signature', 'BOOLEAN DEFAULT FALSE'),
                ('selected_signature_id', 'INTEGER'),
                ('signed_at', 'TIMESTAMP'),
                ('signed_by_id', 'INTEGER'),
                ('signature_hash', 'VARCHAR(128)')
            ]
        }

        for table, columns in migrations.items():
            print(f"\n🔧 Checking table: {table}")
            
            # Check existing columns
            cursor.execute(f"""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = '{table}'
            """)
            existing_columns = [row[0] for row in cursor.fetchall()]
            
            for col_name, col_type in columns:
                if col_name in existing_columns:
                    print(f"   ✅ Column '{col_name}' already exists")
                else:
                    print(f"   ➕ Adding column '{col_name}' ({col_type})...")
                    try:
                        cursor.execute(f"ALTER TABLE {table} ADD COLUMN {col_name} {col_type}")
                        print(f"   ✅ Successfully added '{col_name}'")
                    except Exception as e:
                        print(f"   ❌ Error adding '{col_name}': {e}")

        cursor.close()
        conn.close()
        print("\n🎉 Migration process finished!")
        return True

    except Exception as e:
        print(f"❌ Migration failed: {e}")
        return False

if __name__ == "__main__":
    success = migrate()
    sys.exit(0 if success else 1)
