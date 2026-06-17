#!/usr/bin/env python3
"""
Setup script for Invoice Generator
Handles installation and initial setup
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path

def run_command(command, description):
    """Run a command and handle errors"""
    print(f"📦 {description}...")
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        print(f"✓ {description} completed")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} failed: {e.stderr}")
        return False

def check_python_version():
    """Check if Python version is compatible"""
    print("🐍 Checking Python version...")
    if sys.version_info < (3, 8):
        print("❌ Python 3.8 or higher is required")
        print(f"Current version: {sys.version}")
        return False
    print(f"✓ Python {sys.version.split()[0]} is compatible")
    return True

def install_dependencies():
    """Install Python dependencies"""
    print("📚 Installing dependencies...")
    if not os.path.exists('requirements.txt'):
        print("❌ requirements.txt not found")
        return False
    
    return run_command(f"{sys.executable} -m pip install -r requirements.txt", "Installing Python packages")

def create_directories():
    """Create necessary directories"""
    print("📁 Creating directories...")
    directories = [
        'static/uploads',
        'templates/errors',
        'logs'
    ]
    
    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)
        print(f"✓ Created directory: {directory}")
    
    return True

def setup_environment():
    """Setup environment file"""
    print("⚙️ Setting up environment...")
    
    env_file = Path('.env')
    env_example = Path('env.example')
    
    if not env_file.exists() and env_example.exists():
        shutil.copy(env_example, env_file)
        print("✓ Created .env file from template")
        print("⚠️  Please update .env file with your configuration")
    elif env_file.exists():
        print("✓ .env file already exists")
    else:
        print("⚠️  No environment template found")
    
    return True

def initialize_database():
    """Initialize the database"""
    print("🗄️ Initializing database...")
    return run_command(f"{sys.executable} init_db.py", "Database initialization")

def main():
    """Main setup function"""
    print("=" * 60)
    print("🚀 Invoice Generator - Setup Script")
    print("=" * 60)
    
    # Check Python version
    if not check_python_version():
        sys.exit(1)
    
    # Create directories
    if not create_directories():
        sys.exit(1)
    
    # Install dependencies
    if not install_dependencies():
        print("❌ Failed to install dependencies")
        print("💡 Try running: pip install -r requirements.txt")
        sys.exit(1)
    
    # Setup environment
    setup_environment()
    
    # Initialize database
    if not initialize_database():
        print("❌ Failed to initialize database")
        print("💡 Try running: python init_db.py")
        sys.exit(1)
    
    print("\n" + "=" * 60)
    print("🎉 Setup completed successfully!")
    print("=" * 60)
    print("\nNext steps:")
    print("1. Update .env file with your configuration")
    print("2. Run the application:")
    print("   python run.py")
    print("3. Open http://localhost:5000 in your browser")
    print("4. Login with: admin / admin123")
    print("5. Change the default password")
    print("\nFor production deployment:")
    print("- Use gunicorn: gunicorn --config gunicorn.conf.py wsgi:app")
    print("- Or use Docker: docker-compose up")
    print("\nHappy invoicing! 🎉")

if __name__ == '__main__':
    main()
