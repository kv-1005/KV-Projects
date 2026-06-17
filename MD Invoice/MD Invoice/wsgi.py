#!/usr/bin/env python3
"""
WSGI entry point for Invoice Generator
Used for production deployment with Gunicorn, uWSGI, etc.
"""

import os
import sys

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import app, db, User

# Initialize database tables and create admin user
with app.app_context():
    try:
        db.create_all()
        print("✅ Database tables created successfully")
        
        # Create default admin user if no users exist
        if not User.query.first():
            admin = User(
                username='admin',
                email='admin@company.com',
                role='admin'
            )
            admin.set_password(app.config.get('DEFAULT_ADMIN_PASSWORD'))
            db.session.add(admin)
            db.session.commit()
            admin_password = app.config.get('DEFAULT_ADMIN_PASSWORD')
            print(f"✅ Default admin user created: username='admin', password='{admin_password}'")
        else:
            # Update existing admin user password if environment variable is set
            admin = User.query.filter_by(username='admin').first()
            if admin and os.environ.get('DEFAULT_ADMIN_PASSWORD'):
                new_password = app.config.get('DEFAULT_ADMIN_PASSWORD')
                admin.set_password(new_password)
                db.session.commit()
                print(f"✅ Admin password updated: username='admin', password='{new_password}'")
            else:
                print("ℹ️ Admin user already exists")
        
        # Fix PostgreSQL schema issues
        try:
            from sqlalchemy import text
            
            # Check if we're using PostgreSQL
            if 'postgresql' in str(db.engine.url):
                print("🔧 Detected PostgreSQL - fixing schema issues...")
                
                # Add missing Purchase Order columns
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
                
                for column_name, column_type in columns_to_add:
                    try:
                        # Check if column exists
                        result = db.session.execute(text(f"""
                            SELECT column_name 
                            FROM information_schema.columns 
                            WHERE table_name = 'purchase_order' 
                            AND column_name = '{column_name}'
                        """)).fetchone()
                        
                        if not result:
                            # Add column
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
                            
                            db.session.execute(text(alter_sql))
                            print(f"✅ Added column: {column_name}")
                        else:
                            print(f"ℹ️ Column {column_name} already exists")
                            
                    except Exception as e:
                        print(f"⚠️ Error adding column {column_name}: {e}")
                
                # Update existing rows with defaults
                try:
                    db.session.execute(text("""
                        UPDATE purchase_order 
                        SET 
                            po_type = COALESCE(po_type, 'standard'),
                            priority = COALESCE(priority, 'medium'),
                            main_address = COALESCE(main_address, 'salem'),
                            branch_address = COALESCE(branch_address, 'salem'),
                            eway_bill = COALESCE(eway_bill, ''),
                            extra_billing_info = COALESCE(extra_billing_info, '')
                        WHERE po_type IS NULL OR priority IS NULL OR main_address IS NULL OR branch_address IS NULL
                    """))
                    print("✅ Updated existing rows with default values")
                except Exception as e:
                    print(f"⚠️ Error updating existing rows: {e}")
                
                db.session.commit()
                print("✅ PostgreSQL schema fixes completed")
            else:
                print("ℹ️ Using SQLite - no schema fixes needed")
                
        except Exception as e:
            print(f"⚠️ Schema fix warning: {e}")
            
    except Exception as e:
        print(f"⚠️ Database initialization warning: {e}")

if __name__ == "__main__":
    port = int(os.environ.get('PORT', 8000))
    print(f"🚀 Starting Flask app on port {port}")
    app.run(host='0.0.0.0', port=port, debug=False)
