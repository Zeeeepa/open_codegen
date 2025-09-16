#!/usr/bin/env python3
"""
Setup script for Universal AI Endpoint Management System
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path

def run_command(command, check=True):
    """Run a command and handle errors"""
    print(f"Running: {command}")
    try:
        result = subprocess.run(command, shell=True, check=check, capture_output=True, text=True)
        if result.stdout:
            print(result.stdout)
        return result.returncode == 0
    except subprocess.CalledProcessError as e:
        print(f"Error running command: {e}")
        if e.stderr:
            print(f"Error output: {e.stderr}")
        return False

def check_python_version():
    """Check if Python version is compatible"""
    if sys.version_info < (3, 8):
        print("Error: Python 3.8 or higher is required")
        sys.exit(1)
    print(f"✓ Python {sys.version_info.major}.{sys.version_info.minor} detected")

def install_dependencies():
    """Install Python dependencies"""
    print("\n📦 Installing Python dependencies...")
    
    # Upgrade pip first
    if not run_command(f"{sys.executable} -m pip install --upgrade pip"):
        print("Warning: Failed to upgrade pip")
    
    # Install requirements
    if not run_command(f"{sys.executable} -m pip install -r requirements.txt"):
        print("Error: Failed to install dependencies")
        return False
    
    print("✓ Dependencies installed successfully")
    return True

def install_playwright():
    """Install Playwright browsers"""
    print("\n🎭 Installing Playwright browsers...")
    
    if not run_command("playwright install chromium"):
        print("Error: Failed to install Playwright browsers")
        return False
    
    print("✓ Playwright browsers installed successfully")
    return True

def setup_environment():
    """Set up environment configuration"""
    print("\n⚙️ Setting up environment...")
    
    env_file = Path(".env")
    env_example = Path(".env.example")
    
    if not env_file.exists() and env_example.exists():
        shutil.copy(env_example, env_file)
        print("✓ Created .env file from .env.example")
        print("📝 Please edit .env file with your configuration")
    elif env_file.exists():
        print("✓ .env file already exists")
    else:
        print("Warning: No .env.example file found")
    
    return True

def create_directories():
    """Create necessary directories"""
    print("\n📁 Creating directories...")
    
    directories = [
        "logs",
        "data",
        "sessions",
        "frontend/dist"
    ]
    
    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)
        print(f"✓ Created directory: {directory}")
    
    return True

def test_installation():
    """Test the installation"""
    print("\n🧪 Testing installation...")
    
    # Test imports
    try:
        import fastapi
        import sqlalchemy
        import playwright
        import aiohttp
        print("✓ All core dependencies can be imported")
    except ImportError as e:
        print(f"Error: Failed to import dependency: {e}")
        return False
    
    # Test database creation
    try:
        from backend.database import init_database
        init_database()
        print("✓ Database initialization successful")
    except Exception as e:
        print(f"Warning: Database initialization failed: {e}")
    
    return True

def print_next_steps():
    """Print next steps for the user"""
    print("\n🎉 Setup completed successfully!")
    print("\n📋 Next steps:")
    print("1. Edit .env file with your configuration:")
    print("   - Add your Codegen API token")
    print("   - Configure Z.ai credentials (optional)")
    print("   - Adjust other settings as needed")
    print("\n2. Start the server:")
    print("   python -m backend.main")
    print("\n3. Access the interface:")
    print("   - Web UI: http://localhost:8000")
    print("   - API Docs: http://localhost:8000/docs")
    print("   - Health Check: http://localhost:8000/health")
    print("\n4. Create your first endpoint:")
    print("   curl -X POST http://localhost:8000/api/endpoints/ \\")
    print("     -H 'Content-Type: application/json' \\")
    print("     -d '{\"name\": \"test\", \"provider_type\": \"rest_api\", \"base_url\": \"https://api.openai.com\"}'")

def main():
    """Main setup function"""
    print("🤖 Universal AI Endpoint Management System Setup")
    print("=" * 50)
    
    # Check Python version
    check_python_version()
    
    # Install dependencies
    if not install_dependencies():
        print("❌ Setup failed during dependency installation")
        sys.exit(1)
    
    # Install Playwright
    if not install_playwright():
        print("❌ Setup failed during Playwright installation")
        sys.exit(1)
    
    # Setup environment
    if not setup_environment():
        print("❌ Setup failed during environment setup")
        sys.exit(1)
    
    # Create directories
    if not create_directories():
        print("❌ Setup failed during directory creation")
        sys.exit(1)
    
    # Test installation
    if not test_installation():
        print("❌ Setup completed with warnings")
    
    # Print next steps
    print_next_steps()

if __name__ == "__main__":
    main()
