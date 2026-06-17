# Dockerfile for Invoice Generator - Railway Optimized
# Force rebuild by changing this comment

FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV FLASK_ENV=production
ENV PORT=8000

# Install system dependencies
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        gcc \
        libc6-dev \
        curl \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create uploads directory
RUN mkdir -p static/uploads

# Create non-root user with specific UID/GID for security
RUN groupadd -r appuser && useradd -r -g appuser -d /app -s /bin/bash appuser
RUN chown -R appuser:appuser /app
RUN chmod -R 755 /app
USER appuser

# Expose port (Railway will set PORT environment variable)
EXPOSE 8000

# Health check - use default port
HEALTHCHECK --interval=30s --timeout=30s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:8000/ || exit 1

# Make start script executable
RUN chmod +x start.sh

# Run the application with start script
CMD ["./start.sh"]
