"""
Configuration file for Invoice Generator
"""
import os
from datetime import timedelta

class Config:
    """Base configuration class"""
    
    # Flask Configuration
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-key-change-in-production-' + os.urandom(24).hex()
    
    # Database Configuration
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///invoice_generator.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # File Upload Configuration
    UPLOAD_FOLDER = 'static/uploads'
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max file size
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
    
    # Session Configuration
    PERMANENT_SESSION_LIFETIME = timedelta(hours=24)
    
    # Security Configuration
    WTF_CSRF_ENABLED = True
    WTF_CSRF_TIME_LIMIT = 3600  # 1 hour
    
    # Application Security Passwords
    DELETE_PASSWORD = os.environ.get('DELETE_PASSWORD') or 'Mahadevi&Co2211'
    DEFAULT_ADMIN_PASSWORD = os.environ.get('DEFAULT_ADMIN_PASSWORD') or 'admin123'
    
    # Application Configuration
    INVOICE_PREFIX = 'INV'
    DEFAULT_TAX_RATE = 18.0
    DEFAULT_DUE_DAYS = 30
    
    # Company Configuration
    COMPANY_NAME = os.environ.get('COMPANY_NAME') or 'Your Company Name'
    COMPANY_EMAIL = os.environ.get('COMPANY_EMAIL') or 'company@example.com'
    
    # Pagination
    INVOICES_PER_PAGE = 20
    CUSTOMERS_PER_PAGE = 20

class DevelopmentConfig(Config):
    """Development configuration"""
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = os.environ.get('DEV_DATABASE_URL') or 'sqlite:///invoice_generator_dev.db'

class ProductionConfig(Config):
    """Production configuration"""
    DEBUG = False
    
    # Use environment variables for production
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-key-change-in-production'
    
    # Handle Railway PostgreSQL SSL requirements
    if os.environ.get('DATABASE_URL'):
        db_url = os.environ.get('DATABASE_URL')
        # Add SSL parameters for Railway PostgreSQL
        if 'postgresql://' in db_url:
            if '?' in db_url:
                db_url += '&sslmode=require'
            else:
                db_url += '?sslmode=require'
        SQLALCHEMY_DATABASE_URI = db_url
        # Add engine options for PostgreSQL
        SQLALCHEMY_ENGINE_OPTIONS = {
            'pool_pre_ping': True,
            'pool_recycle': 300,
            'pool_size': int(os.environ.get('DB_POOL_SIZE', 5)),
            'max_overflow': int(os.environ.get('DB_MAX_OVERFLOW', 10)),
            'pool_timeout': int(os.environ.get('DB_POOL_TIMEOUT', 10)),
            'connect_args': {
                'sslmode': 'require',
                # Set a server-side statement timeout (in milliseconds)
                'options': f"-c statement_timeout={int(os.environ.get('DB_STATEMENT_TIMEOUT_MS', 5000))}"
            }
        }
    else:
        SQLALCHEMY_DATABASE_URI = 'sqlite:///invoice_generator.db'

class TestingConfig(Config):
    """Testing configuration"""
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    WTF_CSRF_ENABLED = False

# Configuration dictionary
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}
