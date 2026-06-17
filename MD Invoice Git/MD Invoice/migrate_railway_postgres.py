#!/usr/bin/env python3
"""
Database migration script for Railway PostgreSQL
Adds missing columns to purchase_order table
"""

import os
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

def migrate_railway_database():
    """Add missing columns to purchase_order table in Railway PostgreSQL"""
    
    # Get database URL from environment
    database_url = os.environ.get('DATABASE_URL')
    if not database_url:
        print("DATABASE_URL not found in environment variables")
        return False
    
    try:
        # Connect to PostgreSQL database
        conn = psycopg2.connect(database_url)
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cursor = conn.cursor()
        
        print("Connected to Railway PostgreSQL database")
        
        # Check if columns already exist
        cursor.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'purchase_order' 
            AND column_name IN ('expected_delivery_date', 'actual_delivery_date', 'eway_bill', 'po_type', 'priority', 'extra_billing_info', 'main_address', 'branch_address')
        """)
        
        existing_columns = [row[0] for row in cursor.fetchall()]
        print(f"Existing columns: {existing_columns}")
        
        # Define columns to add
        columns_to_add = [
            ('expected_delivery_date', 'DATE'),
            ('actual_delivery_date', 'DATE'),
            ('eway_bill', 'VARCHAR(50)'),
            ('po_type', 'VARCHAR(20)'),
            ('priority', 'VARCHAR(20)'),
            ('extra_billing_info', 'TEXT'),
            ('main_address', 'VARCHAR(50)'),
            ('branch_address', 'VARCHAR(50)')
        ]
        
        # Add missing columns
        for column_name, column_type in columns_to_add:
            if column_name not in existing_columns:
                try:
                    if column_type in ['DATE']:
                        # For DATE columns, add with default NULL
                        alter_sql = f"ALTER TABLE purchase_order ADD COLUMN {column_name} {column_type}"
                    else:
                        # For other columns, add with default values
                        if column_name in ['po_type', 'priority']:
                            default_value = "'standard'"
                        elif column_name in ['main_address', 'branch_address']:
                            default_value = "'salem'"
                        else:
                            default_value = "''"
                        
                        alter_sql = f"ALTER TABLE purchase_order ADD COLUMN {column_name} {column_type} DEFAULT {default_value}"
                    
                    cursor.execute(alter_sql)
                    print(f"Added column: {column_name}")
                    
                except Exception as e:
                    print(f"Error adding column {column_name}: {e}")
            else:
                print(f"Column {column_name} already exists")
        
        # Update existing rows with default values for new columns
        try:
            cursor.execute("""
                UPDATE purchase_order 
                SET 
                    po_type = COALESCE(po_type, 'standard'),
                    priority = COALESCE(priority, 'medium'),
                    main_address = COALESCE(main_address, 'salem'),
                    branch_address = COALESCE(branch_address, 'salem'),
                    eway_bill = COALESCE(eway_bill, ''),
                    extra_billing_info = COALESCE(extra_billing_info, '')
                WHERE po_type IS NULL OR priority IS NULL OR main_address IS NULL OR branch_address IS NULL
            """)
            print("Updated existing rows with default values")
        except Exception as e:
            print(f"Error updating existing rows: {e}")
        
        # Verify the changes
        cursor.execute("""
            SELECT column_name, data_type, is_nullable, column_default
            FROM information_schema.columns 
            WHERE table_name = 'purchase_order' 
            ORDER BY ordinal_position
        """)
        
        columns = cursor.fetchall()
        print("\nPurchase Order table structure:")
        for col in columns:
            print(f"  {col[0]} - {col[1]} - {'NULL' if col[2] == 'YES' else 'NOT NULL'} - Default: {col[3]}")
        
        cursor.close()
        conn.close()
        
        print("\nMigration completed successfully!")
        return True
        
    except Exception as e:
        print(f"Migration failed: {e}")
        return False

if __name__ == "__main__":
    print("Starting Railway PostgreSQL migration...")
    success = migrate_railway_database()
    
    if success:
        print("Migration completed successfully!")
    else:
        print("Migration failed!")
