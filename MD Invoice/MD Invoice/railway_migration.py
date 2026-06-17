#!/usr/bin/env python3
"""
Railway automatic migration script
Runs on deployment to fix database constraints
"""

import os
import sys
from datetime import datetime

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import app, db
from sqlalchemy import text

def run_railway_migration():
    """Run migrations specifically for Railway deployment"""
    
    print("🚀 RAILWAY MIGRATION STARTING")
    print("=" * 60)
    
    with app.app_context():
        try:
            # Check database type
            db_url = app.config.get('SQLALCHEMY_DATABASE_URI', '')
            is_postgresql = 'postgresql://' in db_url
            
            if not is_postgresql:
                print("ℹ️  Not a PostgreSQL database - skipping migration")
                return True
            
            print("✅ PostgreSQL detected - applying migration")
            
            # Fix OTP foreign key constraints
            print("\n🔧 Fixing OTPVerification constraints...")
            
            # Drop and recreate invoice_id foreign key with CASCADE
            try:
                db.session.execute(text("""
                    DO $$ 
                    BEGIN
                        -- Drop existing constraint if exists
                        IF EXISTS (
                            SELECT 1 FROM pg_constraint 
                            WHERE conname = 'otp_verification_invoice_id_fkey'
                        ) THEN
                            ALTER TABLE otp_verification 
                            DROP CONSTRAINT otp_verification_invoice_id_fkey;
                        END IF;
                        
                        -- Add new constraint with CASCADE
                        ALTER TABLE otp_verification 
                        ADD CONSTRAINT otp_verification_invoice_id_fkey 
                        FOREIGN KEY (invoice_id) REFERENCES invoice(id) ON DELETE CASCADE;
                    END $$;
                """))
                print("   ✅ invoice_id constraint updated with CASCADE")
            except Exception as e:
                print(f"   ⚠️  invoice_id constraint: {str(e)}")
            
            # Drop and recreate user_id foreign key with CASCADE
            try:
                db.session.execute(text("""
                    DO $$ 
                    BEGIN
                        -- Drop existing constraint if exists
                        IF EXISTS (
                            SELECT 1 FROM pg_constraint 
                            WHERE conname = 'otp_verification_user_id_fkey'
                        ) THEN
                            ALTER TABLE otp_verification 
                            DROP CONSTRAINT otp_verification_user_id_fkey;
                        END IF;
                        
                        -- Add new constraint with CASCADE
                        ALTER TABLE otp_verification 
                        ADD CONSTRAINT otp_verification_user_id_fkey 
                        FOREIGN KEY (user_id) REFERENCES "user"(id) ON DELETE CASCADE;
                    END $$;
                """))
                print("   ✅ user_id constraint updated with CASCADE")
            except Exception as e:
                print(f"   ⚠️  user_id constraint: {str(e)}")
            
            # Add signature_data column for e-signature feature
            print("\n🔧 Adding signature_data column...")
            try:
                db.session.execute(text("ALTER TABLE \"user\" ADD COLUMN signature_data TEXT"))
                print("   ✅ signature_data column added")
            except Exception as e:
                if "already exists" in str(e) or "duplicate column" in str(e).lower():
                    print("   ✅ signature_data column already exists")
                else:
                    print(f"   ⚠️  signature_data column: {str(e)}")
            
            # Commit all changes
            db.session.commit()
            
            print("\n✅ MIGRATION COMPLETED SUCCESSFULLY!")
            print("=" * 60)
            
            return True
            
        except Exception as e:
            db.session.rollback()
            print(f"\n❌ MIGRATION FAILED: {str(e)}")
            print("=" * 60)
            return False

if __name__ == "__main__":
    success = run_railway_migration()
    sys.exit(0 if success else 1)

