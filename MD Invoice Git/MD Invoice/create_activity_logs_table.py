#!/usr/bin/env python3
"""
Migration script to create ActivityLog table in existing database
Run this script to add the activity logging feature to your existing database
"""

import sys
from app import app, db
from datetime import datetime

# Fix Windows console encoding
if sys.platform == 'win32':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')

def create_activity_logs_table():
    """Create the ActivityLog table if it doesn't exist"""
    with app.app_context():
        print("Creating ActivityLog table...")
        try:
            # Create all tables (will skip existing ones)
            db.create_all()
            print("[OK] ActivityLog table created successfully!")
            
            # Verify the table was created
            from app import ActivityLog
            count = ActivityLog.query.count()
            print(f"[OK] ActivityLog table verified. Current log entries: {count}")
            
        except Exception as e:
            print(f"[ERROR] Error creating ActivityLog table: {str(e)}")
            raise

if __name__ == '__main__':
    print("=" * 50)
    print("Activity Logs Migration Script")
    print("=" * 50)
    create_activity_logs_table()
    print("=" * 50)
    print("Migration completed!")
    print("=" * 50)

