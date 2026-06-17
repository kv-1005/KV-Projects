#!/usr/bin/env python3
"""
Startup script for Invoice Generator
Handles different environments and configurations
"""

import os
import sys
from app import app, db, init_db

def main():
    """Main startup function"""
    print("=" * 50)
    print("Invoice Generator - Starting Application")
    print("=" * 50)
    
    # Check if database exists, if not initialize it
    # Check for both possible database names
    db_paths = ['invoice_generator.db', 'invoice_generator_dev.db', 'instance/invoice_generator_dev.db']
    db_exists = any(os.path.exists(path) for path in db_paths)
    
    if not db_exists:
        print("Database not found. Initializing database...")
        init_db()
        print("v Database initialized")
    else:
        # Ensure all tables exist (for new models like DeliveryChallan)
        print("Ensuring all database tables exist...")
        with app.app_context():
            db.create_all()
        print("v Database tables verified")
    
    # Get configuration from environment
    debug = os.environ.get('FLASK_DEBUG', 'False').lower() == 'true'
    host = os.environ.get('FLASK_HOST', '0.0.0.0')
    port = int(os.environ.get('FLASK_PORT', 5000))
    
    print("Starting server on " + host + ":" + str(port))
    print(f"Debug mode: {'ON' if debug else 'OFF'}")
    print(f"Environment: {os.environ.get('FLASK_ENV', 'development')}")
    
    if debug:
        print("\n" + "=" * 50)
        print("Development Server Started!")
        print("=" * 50)
        print("Open your browser: http://localhost:" + str(port))
        print("Default login: admin / admin123")
        print("Warning: Remember to change the default password!")
        print("=" * 50)
    
    # Run the application
    try:
        app.run(host=host, port=port, debug=debug)
    except KeyboardInterrupt:
        print("\n\nShutting down server...")
        sys.exit(0)
    except Exception as e:
        print(f"\nX Error starting server: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()
