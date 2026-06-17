import sqlite3
import os

db_path = 'instance/invoice_generator_dev.db'

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

cursor.execute("PRAGMA table_info(invoice)")
columns = cursor.fetchall()
print("Invoice Table Columns:")
for col in columns:
    print(f"- {col[1]} ({col[2]})")

cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='payment_record'")
table_exists = cursor.fetchone()
print(f"\nPaymentRecord table exists: {bool(table_exists)}")

conn.close()
