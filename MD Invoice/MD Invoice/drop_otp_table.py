#!/usr/bin/env python3
"""
Migration script to drop OTPVerification table from existing database
Run this script to remove the OTP functionality from your existing database
"""

import sys
from app import app, db
from sqlalchemy import text

# Fix Windows console encoding
if sys.platform == 'win32':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')

def drop_otp_table():
    """Drop the OTPVerification table if it exists"""
    with app.app_context():
        print("Dropping OTPVerification table...")
        try:
            # Check if table exists
            inspector = db.inspect(db.engine)
            tables = inspector.get_table_names()
            
            if 'otp_verification' in tables:
                print(f"[INFO] Found OTPVerification table. Dropping...")
                
                # Drop the table
                db.session.execute(text('DROP TABLE IF EXISTS otp_verification CASCADE'))
                db.session.commit()
                
                print("[OK] OTPVerification table dropped successfully!")
            else:
                print("[INFO] OTPVerification table does not exist. Nothing to drop.")
            
            # Verify the table was dropped
            inspector = db.inspect(db.engine)
            tables = inspector.get_table_names()
            if 'otp_verification' not in tables:
                print("[OK] OTPVerification table verified as dropped.")
            else:
                print("[WARNING] Table still exists after drop attempt.")
            
        except Exception as e:
            print(f"[ERROR] Error dropping OTPVerification table: {str(e)}")
            db.session.rollback()
            raise

if __name__ == '__main__':
    print("=" * 50)
    print("OTP Removal Migration Script")
    print("=" * 50)
    drop_otp_table()
    print("=" * 50)
    print("Migration completed!")
    print("=" * 50)

