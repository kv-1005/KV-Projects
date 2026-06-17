#!/usr/bin/env python3
"""
Simple migration script to create tables for multiple signatures
"""

import os
import sys

# Add the project root to Python path
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

try:
    from app import app, db
    
    print("🚀 Running Multiple Signatures Migration...")
    print("=" * 50)
    
    with app.app_context():
        try:
            # Create all tables (this will create user_signature table)
            db.create_all()
            print("✅ Tables created successfully!")
            
            # Check if user_signature table exists
            from sqlalchemy import inspect
            inspector = inspect(db.engine)
            tables = inspector.get_table_names()
            
            if 'user_signature' in tables:
                print("✅ user_signature table exists")
            else:
                print("❌ user_signature table not found")
            
            print("\n🎉 Migration completed!")
            
        except Exception as e:
            print(f"❌ Error during migration: {str(e)}")
            sys.exit(1)
            
except ImportError as e:
    print(f"❌ Could not import app module: {str(e)}")
    sys.exit(1)