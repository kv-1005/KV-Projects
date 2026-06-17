import sqlite3
import os

db_path = 'instance/invoice_generator_dev.db'

# Try to find the DB path from app.py if possible or common locations
if not os.path.exists(db_path):
    db_path = 'invoices.db'

print(f"Opening database: {db_path}")

try:
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # List of columns to check/add
    # Based on the error log, these might be missing or need verification
    new_columns = [
        ('paid_amount', 'DECIMAL(10,2) DEFAULT 0'),
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
        ('eway_qr', 'TEXT'),
        ('selected_signature_id', 'INTEGER')
    ]
    
    # Get current columns
    cursor.execute("PRAGMA table_info(invoice)")
    existing_columns = [row[1] for row in cursor.fetchall()]
    
    for col_name, col_def in new_columns:
        if col_name not in existing_columns:
            print(f"Adding column {col_name}...")
            try:
                cursor.execute(f"ALTER TABLE invoice ADD COLUMN {col_name} {col_def}")
                print(f"Successfully added {col_name}")
            except Exception as e:
                print(f"Error adding {col_name}: {e}")
        else:
            print(f"Column {col_name} already exists.")
            
    conn.commit()
    conn.close()
    print("Database migration completed.")

except Exception as e:
    print(f"Migration failed: {e}")
