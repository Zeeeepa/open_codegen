#!/usr/bin/env python3
"""
Deployment script for the Universal AI Endpoint Management System
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path

def run_command(command, description=""):
    """Run a command and handle errors"""
    print(f"🔄 {description or command}")
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        if result.stdout:
            print(f"   {result.stdout.strip()}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed: {e}")
        if e.stderr:
            print(f"   Error: {e.stderr.strip()}")
        return False

def check_prerequisites():
    """Check if all prerequisites are installed"""
    print("🔍 Checking prerequisites...")
    
    # Check Python version
    if sys.version_info < (3, 8):
        print("❌ Python 3.8+ is required")
        return False
    print(f"✅ Python {sys.version.split()[0]} found")
    
    # Check if pip is available
    if not run_command("pip --version", "Checking pip"):
        return False
    
    # Check if Node.js is available (for browser automation)
    if not run_command("node --version", "Checking Node.js"):
        print("⚠️  Node.js not found. Browser automation may not work.")
    
    return True

def install_dependencies():
    """Install Python dependencies"""
    print("📦 Installing dependencies...")
    
    # Install main dependencies
    dependencies = [
        "fastapi>=0.104.0",
        "uvicorn[standard]>=0.24.0",
        "sqlalchemy>=2.0.0",
        "alembic>=1.12.0",
        "pydantic>=2.5.0",
        "python-dotenv>=1.0.0",
        "aiohttp>=3.9.0",
        "playwright>=1.40.0",
        "cryptography>=41.0.0",
        "python-multipart>=0.0.6",
        "jinja2>=3.1.0",
        "prometheus-client>=0.19.0",
        "psutil>=5.9.0"
    ]
    
    for dep in dependencies:
        if not run_command(f"pip install {dep}", f"Installing {dep.split('>=')[0]}"):
            return False
    
    # Install Playwright browsers
    if not run_command("playwright install", "Installing Playwright browsers"):
        print("⚠️  Playwright browser installation failed. Web chat automation may not work.")
    
    return True

def setup_environment():
    """Setup environment configuration"""
    print("⚙️  Setting up environment...")
    
    # Copy environment template if .env doesn't exist
    if not os.path.exists('.env'):
        if os.path.exists('.env.example'):
            shutil.copy('.env.example', '.env')
            print("✅ Created .env from template")
            print("📝 Please edit .env with your configuration")
        else:
            print("❌ .env.example not found")
            return False
    else:
        print("✅ .env already exists")
    
    return True

def initialize_database():
    """Initialize the database"""
    print("🗄️  Initializing database...")
    
    try:
        # Import and initialize database
        sys.path.append('.')
        from backend.database import init_database
        init_database()
        print("✅ Database initialized successfully")
        return True
    except Exception as e:
        print(f"❌ Database initialization failed: {e}")
        return False

def run_validation():
    """Run validation tests"""
    print("🧪 Running validation tests...")
    
    if not run_command("python test_validation.py", "Running comprehensive validation"):
        return False
    
    print("✅ All validation tests passed")
    return True

def create_startup_script():
    """Create startup scripts for different platforms"""
    print("📝 Creating startup scripts...")
    
    # Unix/Linux startup script
    unix_script = """#!/bin/bash
# Universal AI Endpoint Management System Startup Script

echo "🚀 Starting Universal AI Endpoint Management System..."

# Load environment variables
if [ -f .env ]; then
    export $(cat .env | grep -v '^#' | xargs)
fi

# Start the server
python -m uvicorn backend.main:app --host ${HOST:-0.0.0.0} --port ${PORT:-8000} --reload
"""
    
    with open('start.sh', 'w') as f:
        f.write(unix_script)
    os.chmod('start.sh', 0o755)
    print("✅ Created start.sh")
    
    # Windows startup script
    windows_script = """@echo off
REM Universal AI Endpoint Management System Startup Script

echo 🚀 Starting Universal AI Endpoint Management System...

REM Start the server
python -m uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload
"""
    
    with open('start.bat', 'w') as f:
        f.write(windows_script)
    print("✅ Created start.bat")
    
    return True

def create_docker_files():
    """Create Docker configuration files"""
    print("🐳 Creating Docker configuration...")
    
    dockerfile = """FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \\
    curl \\
    && rm -rf /var/lib/apt/lists/*

# Install Node.js for Playwright
RUN curl -fsSL https://deb.nodesource.com/setup_18.x | bash - \\
    && apt-get install -y nodejs

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Install Playwright browsers
RUN playwright install --with-deps

# Copy application code
COPY . .

# Create non-root user
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \\
    CMD curl -f http://localhost:8000/health || exit 1

# Start the application
CMD ["python", "-m", "uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]
"""
    
    with open('Dockerfile', 'w') as f:
        f.write(dockerfile)
    print("✅ Created Dockerfile")
    
    # Docker Compose
    docker_compose = """version: '3.8'

services:
  ai-endpoint-manager:
    build: .
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=sqlite:///data/endpoint_manager.db
      - LOG_LEVEL=INFO
    volumes:
      - ./data:/app/data
      - ./.env:/app/.env
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3

  # Optional: PostgreSQL database
  postgres:
    image: postgres:15
    environment:
      POSTGRES_DB: endpoint_manager
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: password
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"
    restart: unless-stopped

  # Optional: Redis for session storage
  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    restart: unless-stopped

volumes:
  postgres_data:
"""
    
    with open('docker-compose.yml', 'w') as f:
        f.write(docker_compose)
    print("✅ Created docker-compose.yml")
    
    return True

def create_requirements_file():
    """Create requirements.txt file"""
    print("📋 Creating requirements.txt...")
    
    requirements = """fastapi>=0.104.0
uvicorn[standard]>=0.24.0
sqlalchemy>=2.0.0
alembic>=1.12.0
pydantic>=2.5.0
python-dotenv>=1.0.0
aiohttp>=3.9.0
playwright>=1.40.0
cryptography>=41.0.0
python-multipart>=0.0.6
jinja2>=3.1.0
prometheus-client>=0.19.0
psutil>=5.9.0
gunicorn>=21.2.0
"""
    
    with open('requirements.txt', 'w') as f:
        f.write(requirements)
    print("✅ Created requirements.txt")
    
    return True

def main():
    """Main deployment function"""
    print("🚀 Universal AI Endpoint Management System Deployment")
    print("=" * 60)
    
    steps = [
        ("Prerequisites Check", check_prerequisites),
        ("Requirements File", create_requirements_file),
        ("Dependencies Installation", install_dependencies),
        ("Environment Setup", setup_environment),
        ("Database Initialization", initialize_database),
        ("Validation Tests", run_validation),
        ("Startup Scripts", create_startup_script),
        ("Docker Configuration", create_docker_files),
    ]
    
    failed_steps = []
    
    for step_name, step_func in steps:
        print(f"\n📋 Step: {step_name}")
        print("-" * 40)
        
        if not step_func():
            failed_steps.append(step_name)
            print(f"❌ {step_name} failed")
        else:
            print(f"✅ {step_name} completed")
    
    print("\n" + "=" * 60)
    print("📊 DEPLOYMENT SUMMARY")
    print("=" * 60)
    
    if not failed_steps:
        print("🎉 DEPLOYMENT SUCCESSFUL!")
        print("\n🚀 To start the system:")
        print("   Unix/Linux: ./start.sh")
        print("   Windows: start.bat")
        print("   Docker: docker-compose up")
        print("\n📖 Documentation: http://localhost:8000/docs")
        print("🔍 Health Check: http://localhost:8000/health")
        return True
    else:
        print(f"⚠️  {len(failed_steps)} steps failed:")
        for step in failed_steps:
            print(f"   - {step}")
        print("\n🔧 Please fix the issues above and run the deployment again.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
