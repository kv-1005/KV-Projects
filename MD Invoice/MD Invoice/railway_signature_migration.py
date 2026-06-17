#!/usr/bin/env python3
"""
Migration: Add selected_signature_id column to purchase_order if it doesn't exist.
Works for SQLite and PostgreSQL. Safe to run multiple times.
"""

from sqlalchemy import inspect, text
from app import app, db


def column_exists(inspector, table_name: str, column_name: str) -> bool:
    try:
        cols = inspector.get_columns(table_name)
        return any(c["name"] == column_name for c in cols)
    except Exception:
        return False


def add_column_if_missing(engine, table_name: str, column_name: str, sql_type: str):
    with engine.connect() as conn:
        try:
            conn.execute(text(f'ALTER TABLE {table_name} ADD COLUMN {column_name} {sql_type}'))
            print(f"Added column {column_name} to {table_name}")
        except Exception as e:
            print(f"Skipping add column {column_name}: {e}")


def migrate():
    with app.app_context():
        engine = db.engine
        inspector = inspect(engine)

        if not column_exists(inspector, 'purchase_order', 'selected_signature_id'):
            # Reference is optional, so just add as INTEGER/INT
            dialect_name = engine.url.get_dialect().name
            if dialect_name == 'postgresql':
                add_column_if_missing(engine, 'purchase_order', 'selected_signature_id', 'INTEGER')
            else:
                add_column_if_missing(engine, 'purchase_order', 'selected_signature_id', 'INTEGER')
        else:
            print('Column purchase_order.selected_signature_id already exists')


if __name__ == '__main__':
    migrate()

#!/usr/bin/env python3
"""
Railway signature migration script
Adds signature_data column to user table for PostgreSQL
"""

import os
import sys
from sqlalchemy import text

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from app import app, db
except ImportError:
    print("❌ Could not import app module")
    sys.exit(1)

def add_signature_column_railway():
    """Add signature_data column to user table in Railway PostgreSQL"""
    
    print("🚀 RAILWAY SIGNATURE MIGRATION STARTING")
    print("=" * 60)
    
    with app.app_context():
        try:
            # Check database type
            db_url = app.config.get('SQLALCHEMY_DATABASE_URI', '')
            is_postgresql = 'postgresql://' in db_url
            
            if not is_postgresql:
                print("ℹ️  Not a PostgreSQL database - checking SQLite...")
                
                # For SQLite, check if column exists
                try:
                    db.session.execute(text("SELECT signature_data FROM user LIMIT 1"))
                    print("✅ signature_data column already exists in SQLite")
                    return True
                except:
                    # Add column if it doesn't exist
                    db.session.execute(text("ALTER TABLE user ADD COLUMN signature_data TEXT"))
                    db.session.commit()
                    print("✅ signature_data column added to SQLite")
                    return True
            
            if is_postgresql:
                print("✅ PostgreSQL detected - adding signature_data column")
                
                # Check if column exists
                try:
                    db.session.execute(text("SELECT signature_data FROM \"user\" LIMIT 1"))
                    print("✅ signature_data column already exists")
                    return True
                except Exception as e:
                    # Column doesn't exist, add it
                    try:
                        db.session.execute(text("ALTER TABLE \"user\" ADD COLUMN signature_data TEXT"))
                        db.session.commit()
                        print("✅ signature_data column added successfully to PostgreSQL")
                        return True
                    except Exception as add_error:
                        print(f"❌ Error adding signature_data column: {str(add_error)}")
                        return False
            
        except Exception as e:
            db.session.rollback()
            print(f"❌ Migration error: {str(e)}")
            return False
    
    print("✅ SIGNATURE MIGRATION COMPLETED!")
    return True

if __name__ == "__main__":
    success = add_signature_column_railway()
    if success:
        print("🎉 Railway signature migration successful!")
        sys.exit(0)
    else:
        print("❌ Railway signature migration failed!")
        sys.exit(1)
