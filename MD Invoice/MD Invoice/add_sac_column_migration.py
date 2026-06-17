#!/usr/bin/env python3
"""
Migration: Add is_sac column to invoice table if it doesn't exist.
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
    inspector = inspect(engine)
    if column_exists(inspector, table_name, column_name):
        print(f"   ✅ Column '{column_name}' already exists")
        return

    # Use safe PostgreSQL pattern for adding columns
    db_url = str(engine.url)
    if 'postgresql' in db_url:
        # PostgreSQL safe pattern
        ddl = f"""
            DO $$ 
            BEGIN
                IF NOT EXISTS (
                    SELECT 1 FROM information_schema.columns 
                    WHERE table_name = '{table_name}' AND column_name = '{column_name}'
                ) THEN
                    ALTER TABLE {table_name} ADD COLUMN {column_name} {sql_type};
                END IF;
            END $$;
        """
    else:
        # SQLite simple pattern
        ddl = f"ALTER TABLE {table_name} ADD COLUMN {column_name} {sql_type}"
    
    try:
        with engine.begin() as conn:
            conn.execute(text(ddl))
        print(f"   ✅ Added column '{column_name}' ({sql_type})")
    except Exception as e:
        if "already exists" in str(e) or "duplicate column" in str(e).lower():
            print(f"   ✅ Column '{column_name}' already exists")
        else:
            print(f"   ⚠️  Failed to add column '{column_name}': {e}")


def run_migration():
    print("🚀 SAC COLUMN MIGRATION STARTING")
    print("=" * 60)
    with app.app_context():
        engine = db.engine
        inspector = inspect(engine)

        if "invoice" not in inspector.get_table_names():
            print("❌ 'invoice' table not found. Ensure database is initialized.")
            return False

        print("\n🔧 Adding is_sac column to 'invoice' table if missing...")
        
        # Determine SQL type based on database
        db_url = str(engine.url)
        if 'postgresql' in db_url:
            sql_type = "BOOLEAN DEFAULT FALSE"
        else:
            # SQLite uses INTEGER for boolean (0 = False, 1 = True)
            sql_type = "INTEGER DEFAULT 0"
        
        add_column_if_missing(engine, "invoice", "is_sac", sql_type)

        print("\n✅ SAC column migration completed.")
        return True


if __name__ == "__main__":
    ok = run_migration()
    raise SystemExit(0 if ok else 1)

