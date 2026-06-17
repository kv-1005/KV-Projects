#!/usr/bin/env python3
"""
Create database indexes for chatbot tables to optimize queries
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import app, db
from sqlalchemy import text

INDEX_STATEMENTS = [
    # Chat conversations indexes
    "CREATE INDEX IF NOT EXISTS idx_chat_conv_user_id ON chat_conversations(user_id)",
    "CREATE INDEX IF NOT EXISTS idx_chat_conv_updated_at ON chat_conversations(updated_at DESC)",
    "CREATE INDEX IF NOT EXISTS idx_chat_conv_user_updated ON chat_conversations(user_id, updated_at DESC)",
    
    # Chat messages indexes
    "CREATE INDEX IF NOT EXISTS idx_chat_msg_conv_id ON chat_messages(conversation_id)",
    "CREATE INDEX IF NOT EXISTS idx_chat_msg_created_at ON chat_messages(created_at DESC)",
    "CREATE INDEX IF NOT EXISTS idx_chat_msg_conv_created ON chat_messages(conversation_id, created_at ASC)",
    "CREATE INDEX IF NOT EXISTS idx_chat_msg_role ON chat_messages(role)",
    
    # Chatbot knowledge indexes
    "CREATE INDEX IF NOT EXISTS idx_chatbot_kb_keyword ON chatbot_knowledge(keyword)",
    "CREATE INDEX IF NOT EXISTS idx_chatbot_kb_category ON chatbot_knowledge(category)",
]


def create_indexes():
    """Create indexes for chatbot tables"""
    print("Creating chatbot table indexes...")
    
    with app.app_context():
        try:
            created = 0
            for stmt in INDEX_STATEMENTS:
                try:
                    db.session.execute(text(stmt))
                    db.session.commit()
                    created += 1
                    print(f"[OK] Created index: {stmt.split('IF NOT EXISTS')[1].split('ON')[0].strip()}")
                except Exception as e:
                    db.session.rollback()
                    print(f"[WARN] Index creation: {e}")
            
            print(f"\n[OK] Created {created}/{len(INDEX_STATEMENTS)} indexes successfully!")
            return True
            
        except Exception as e:
            print(f"[ERROR] Error creating indexes: {e}")
            return False


if __name__ == '__main__':
    create_indexes()

