#!/usr/bin/env python3
"""
Migration script to add summary column to chat_conversations table
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import app, db
from sqlalchemy import text, inspect

def add_summary_column():
    """Add summary column to chat_conversations table if it doesn't exist"""
    print("Checking for summary column in chat_conversations...")
    
    with app.app_context():
        try:
            inspector = inspect(db.engine)
            
            # Check if column exists
            columns = [col['name'] for col in inspector.get_columns('chat_conversations')]
            
            if 'summary' not in columns:
                print("Adding summary column to chat_conversations...")
                # Add the column
                if 'sqlite' in str(db.engine.url):
                    # SQLite doesn't support ALTER TABLE ADD COLUMN with constraints well
                    # But we can add it as nullable text
                    db.session.execute(text("""
                        ALTER TABLE chat_conversations 
                        ADD COLUMN summary TEXT
                    """))
                else:
                    # PostgreSQL/MySQL
                    db.session.execute(text("""
                        ALTER TABLE chat_conversations 
                        ADD COLUMN summary TEXT
                    """))
                
                db.session.commit()
                print("[OK] Summary column added successfully!")
            else:
                print("[INFO] Summary column already exists")
            
            return True
            
        except Exception as e:
            db.session.rollback()
            print(f"[ERROR] Error adding summary column: {e}")
            import traceback
            traceback.print_exc()
            return False

if __name__ == '__main__':
    add_summary_column()

