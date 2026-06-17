#!/usr/bin/env python3
"""
Multiple signatures migration script
Creates user_signatures table and adds selected_signature_id to invoices
"""

import os
import sys
from datetime import datetime

# Add the project root to Python path
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

try:
    from app import app, db
    from sqlalchemy import text
    print("✅ Successfully imported app module")
except ImportError as e:
    print(f"❌ Could not import app module: {str(e)}")
    print("Make sure you're running this from the project root directory")
    sys.exit(1)

def create_multiple_signatures_tables():
    """Create user_signatures table and update invoice table"""
    
    print("🚀 MULTIPLE SIGNATURES MIGRATION STARTING")
    print("=" * 60)
    
    try:
        with app.app_context():
            print("\n🔧 Creating user_signatures table...")
            
            # Check database type for proper table creation
            from sqlalchemy import inspect
            inspector = inspect(db.engine)
            tables = inspector.get_table_names()
            
            table_name = 'user_signature'
            if table_name in tables:
                print(f"   ✅ {table_name} table already exists")
            else:
                # Create table using app context
                db.create_all()
                print("   ✅ user_signature table created via db.create_all()")
            
            
            # Add selected_signature_id column to invoice table
            print("\n🔧 Adding selected_signature_id to invoice table...")
            
            # Check if selected_signature_id column exists in invoice table
            try:
                inspector = inspect(db.engine)
                columns = inspector.get_columns('invoice')
                column_names = [col['name'] for col in columns]
                
                if 'selected_signature_id' in column_names:
                    print("   ✅ selected_signature_id column already exists in invoice table")
                else:
                    # Add the column
                    try:
                        db.session.execute(text("ALTER TABLE invoice ADD COLUMN selected_signature_id INTEGER REFERENCES user_signature(id)"))
                        db.session.commit()
                        print("   ✅ selected_signature_id column added to invoice table")
                    except Exception as add_error:
                        print(f"   ⚠️  Could not add selected_signature_id column: {str(add_error)}")
            except Exception as check_error:
                print(f"   ⚠️  Could not check invoice table columns: {str(check_error)}")
            
            # Commit all changes
            db.session.commit()
            print("\n✅ Multiple signatures migration completed successfully!")
            return True
            
    except Exception as e:
        print(f"❌ Error during migration: {str(e)}")
        db.session.rollback()
        return False

def migrate_existing_signatures():
    """Migrate existing signatures from user.signature_data to user_signature table"""
    
    print("\n🔄 Migrating existing signatures...")
    
    try:
        with app.app_context():
            # Get users with existing signatures
            from app import User, UserSignature
            
            users_with_signatures = User.query.filter(User.signature_data.isnot(None)).all()
            
            for user in users_with_signatures:
                # Create new signature record
                existing_signature = UserSignature(
                    user_id=user.id,
                    signature_name="Default Signature",  # Generic name for migrated signature
                    signature_data=user.signature_data,
                    is_default=True,  # Mark as default since it was their only signature
                    created_by=user.id
                )
                
                db.session.add(existing_signature)
                print(f"   ✅ Migrated signature for user: {user.username}")
            
            db.session.commit()
            print(f"✅ Migrated {len(users_with_signatures)} existing signatures")
            return True
            
    except Exception as e:
        print(f"❌ Error migrating existing signatures: {str(e)}")
        db.session.rollback()
        return False

def validate_migration():
    """Validate that migration was successful"""
    
    print("\n🔍 Validating migration...")
    
    try:
        with app.app_context():
            from sqlalchemy import text
            
            # Check if user_signature table exists and has data
            result = db.session.execute(text("SELECT COUNT(*) FROM information_schema.tables WHERE table_name = 'user_signature'"))
            table_exists = result.fetchone()[0] > 0
            
            if table_exists:
                signature_count = db.session.execute(text("SELECT COUNT(*) FROM user_signature")).fetchone()[0]
                print(f"   ✅ user_signature table exists with {signature_count} signatures")
            else:
                print("   ❌ user_signature table not found")
                return False
            
            # Check if selected_signature_id column exists in invoice table
            try:
                db.session.execute(text("SELECT selected_signature_id FROM invoice LIMIT 1"))
                print("   ✅ selected_signature_id column exists in invoice table")
            except Exception as e:
                print(f"   ❌ selected_signature_id column not found: {str(e)}")
                return False
            
            return True
            
    except Exception as e:
        print(f"❌ Error validating migration: {str(e)}")
        return False

if __name__ == "__main__":
    print("🔄 Multiple Signatures Migration Starting...")
    
    # Step 1: Create tables and add columns
    if not create_multiple_signatures_tables():
        print("❌ Migration failed!")
        sys.exit(1)
    
    # Step 2: Migrate existing signatures
    if not migrate_existing_signatures():
        print("⚠️  Existing signatures migration failed, but core migration succeeded")
    
    # Step 3: Validate migration
    if validate_migration():
        print("\n🎉 Multiple signatures migration completed successfully!")
        print("\n📋 Next Steps:")
        print("   1. Restart your application")
        print("   2. Go to Signature Management to add more signatures")
        print("   3. Create/edit invoices to select specific signatures")
        sys.exit(0)
    else:
        print("❌ Migration validation failed!")
        sys.exit(1)
