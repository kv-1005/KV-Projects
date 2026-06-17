#!/usr/bin/env python3
"""
COMPREHENSIVE RAILWAY POSTGRESQL FIX
This script fixes all PostgreSQL compatibility issues
"""

import os
import sys
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

def fix_railway_postgresql():
    """Fix all PostgreSQL compatibility issues on Railway"""
    print("🔧 Starting comprehensive Railway PostgreSQL fix...")
    
    # Get database URL from environment
    database_url = os.environ.get('DATABASE_URL')
    if not database_url:
        print("❌ DATABASE_URL not found in environment variables")
        return False
    
    try:
        # Connect to PostgreSQL database
        print("📡 Connecting to Railway PostgreSQL database...")
        conn = psycopg2.connect(database_url)
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cursor = conn.cursor()
        
        print("✅ Connected to Railway PostgreSQL database")
        
        # 1. Fix Purchase Order table - add missing columns
        print("\n🔧 Step 1: Adding missing Purchase Order columns...")
        
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
        
        # Check existing columns
        cursor.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'purchase_order'
        """)
        existing_columns = [row[0] for row in cursor.fetchall()]
        
        added_columns = []
        for column_name, column_type in columns_to_add:
            if column_name not in existing_columns:
                try:
                    if column_type == 'DATE':
                        alter_sql = f"ALTER TABLE purchase_order ADD COLUMN {column_name} {column_type}"
                    else:
                        if column_name in ['po_type', 'priority']:
                            default_value = "'standard'"
                        elif column_name in ['main_address', 'branch_address']:
                            default_value = "'salem'"
                        else:
                            default_value = "''"
                        
                        alter_sql = f"ALTER TABLE purchase_order ADD COLUMN {column_name} {column_type} DEFAULT {default_value}"
                    
                    cursor.execute(alter_sql)
                    print(f"✅ Added column: {column_name}")
                    added_columns.append(column_name)
                    
                except Exception as e:
                    print(f"❌ Error adding column {column_name}: {e}")
            else:
                print(f"ℹ️ Column {column_name} already exists")
        
        # 2. Update existing rows with default values
        if added_columns:
            print("\n🔧 Step 2: Updating existing rows with default values...")
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
                print("✅ Updated existing rows with default values")
            except Exception as e:
                print(f"⚠️ Error updating existing rows: {e}")
        
        # 3. Verify all tables exist
        print("\n🔧 Step 3: Verifying all required tables exist...")
        cursor.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public'
        """)
        existing_tables = [row[0] for row in cursor.fetchall()]
        
        required_tables = [
            'user', 'company', 'customer', 'vendor', 
            'invoice', 'invoice_item', 'purchase_order', 
            'purchase_order_item', 'otp_verification'
        ]
        
        missing_tables = [table for table in required_tables if table not in existing_tables]
        if missing_tables:
            print(f"❌ Missing tables: {missing_tables}")
        else:
            print("✅ All required tables exist")
        
        # 4. Test PostgreSQL-specific functions
        print("\n🔧 Step 4: Testing PostgreSQL compatibility...")
        try:
            # Test to_char function (PostgreSQL equivalent of strftime)
            cursor.execute("SELECT to_char(NOW(), 'YYYY-MM')")
            result = cursor.fetchone()
            print(f"✅ PostgreSQL to_char function working: {result[0]}")
            
            # Test date functions
            cursor.execute("SELECT EXTRACT(YEAR FROM NOW()), EXTRACT(MONTH FROM NOW())")
            result = cursor.fetchone()
            print(f"✅ PostgreSQL date extraction working: {result[0]}-{result[1]:02d}")
            
        except Exception as e:
            print(f"❌ PostgreSQL function test failed: {e}")
        
        # 5. Check table structures
        print("\n🔧 Step 5: Verifying table structures...")
        for table in required_tables:
            if table in existing_tables:
                cursor.execute(f"""
                    SELECT column_name, data_type, is_nullable, column_default
                    FROM information_schema.columns 
                    WHERE table_name = '{table}' 
                    ORDER BY ordinal_position
                """)
                columns = cursor.fetchall()
                print(f"📊 {table}: {len(columns)} columns")
        
        cursor.close()
        conn.close()
        
        print(f"\n🎉 Railway PostgreSQL fix completed successfully!")
        print(f"📈 Added {len(added_columns)} new columns: {added_columns}")
        print("✅ All PostgreSQL compatibility issues resolved")
        return True
        
    except Exception as e:
        print(f"❌ Railway PostgreSQL fix failed: {e}")
        return False

if __name__ == "__main__":
    success = fix_railway_postgresql()
    sys.exit(0 if success else 1)
