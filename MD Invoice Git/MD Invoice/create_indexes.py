#!/usr/bin/env python3
"""
One-off script to create helpful database indexes in production.
Safe to run multiple times.
"""

from app import app, db
from sqlalchemy import text


INDEX_STATEMENTS = [
    # Purchase Orders
    "CREATE INDEX IF NOT EXISTS idx_po_created_at ON purchase_order(created_at DESC)",
    "CREATE INDEX IF NOT EXISTS idx_po_vendor_id ON purchase_order(vendor_id)",
    # Invoices
    "CREATE INDEX IF NOT EXISTS idx_invoice_created_at ON invoice(created_at DESC)",
]


def main():
    with app.app_context():
        for stmt in INDEX_STATEMENTS:
            try:
                db.session.execute(text(stmt))
                db.session.commit()
                print(f"OK: {stmt}")
            except Exception as e:
                db.session.rollback()
                print(f"WARN: {stmt} -> {e}")


if __name__ == "__main__":
    main()


