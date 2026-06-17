#!/bin/bash

# Start script for Railway deployment
# This ensures the PORT environment variable is properly set

# Set default port if PORT is not set
export PORT=${PORT:-8000}

echo "🚀 Starting Invoice Management System..."
echo "📡 Port: $PORT"
echo "🌍 Host: 0.0.0.0"

# Run database migration for Railway (fixes invoice deletion)
if [ -n "$DATABASE_URL" ]; then
    echo "🔧 Running Railway database migration..."
    python railway_migration.py
    if [ $? -eq 0 ]; then
        echo "✅ Migration completed successfully"
    else
        echo "⚠️  Migration failed - continuing anyway"
    fi
fi

# Start the application with enhanced configuration for Docker
exec gunicorn --bind 0.0.0.0:$PORT \
    --workers 1 \
    --timeout 300 \
    --keep-alive 2 \
    --max-requests 1000 \
    --max-requests-jitter 100 \
    --worker-class sync \
    --worker-connections 1000 \
    --preload \
    --log-level info \
    wsgi:app
