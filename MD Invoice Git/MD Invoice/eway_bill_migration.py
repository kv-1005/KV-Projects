#!/usr/bin/env python3
"""
Migration: Add E-Way Bill columns to invoice table if they don't exist.
Works for SQLite and PostgreSQL. Safe to run multiple times.
"""

from sqlalchemy import inspect, text
from app import app, db

INVOICE_COLUMNS = [
    ("eway_mode", "VARCHAR(10)"),
    ("vehicle_number", "VARCHAR(20)"),
    ("rr_number", "VARCHAR(30)"),
    ("transporter_id", "VARCHAR(30)"),
    ("from_place", "VARCHAR(100)"),
    ("from_state_code", "VARCHAR(2)"),
    ("to_place", "VARCHAR(100)"),
    ("to_state_code", "VARCHAR(2)"),
    ("eway_valid_upto", "DATE"),
    ("eway_qr", "TEXT"),
]


def column_exists(inspector, table_name: str, column_name: str) -> bool:
    try:
        cols = inspector.get_columns(table_name)
        return any(c["name"] == column_name for c in cols)
    except Exception:
        return False


def add_column_if_missing(engine, table_name: str, column_name: str, sql_type: str):
    inspector = inspect(engine)
    if column_exists(inspector, table_name, column_name):
        print(f"   ✅ Column '{column_name}' already exists")
        return

    ddl = f"ALTER TABLE {table_name} ADD COLUMN {column_name} {sql_type}"
    try:
        with engine.begin() as conn:
            conn.execute(text(ddl))
        print(f"   ✅ Added column '{column_name}' ({sql_type})")
    except Exception as e:
        print(f"   ⚠️  Failed to add column '{column_name}': {e}")


def run_migration():
    print("🚀 E-WAY BILL MIGRATION STARTING")
    print("=" * 60)
    with app.app_context():
        engine = db.engine
        inspector = inspect(engine)

        if "invoice" not in inspector.get_table_names():
            print("❌ 'invoice' table not found. Ensure database is initialized.")
            return False

        print("\n🔧 Adding E-Way Bill columns to 'invoice' table if missing...")
        for name, sql_type in INVOICE_COLUMNS:
            add_column_if_missing(engine, "invoice", name, sql_type)

        print("\n✅ E-Way Bill migration completed.")
        return True


if __name__ == "__main__":
    ok = run_migration()
    raise SystemExit(0 if ok else 1)


