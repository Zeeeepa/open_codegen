#!/usr/bin/env python3
"""
OpenAI Codegen Adapter Server
============================

A unified server that provides OpenAI-compatible API endpoints for the Codegen service.
Supports OpenAI, Anthropic, and Google API formats with a built-in web UI.

Features:
- OpenAI-compatible chat completions API
- Anthropic Claude API compatibility  
- Google Gemini API compatibility
- Web UI for testing and configuration
- Real-time service status control
- Comprehensive API testing tools

Usage:
    python server.py

The server will start on http://localhost:8887 with all features enabled.
"""

import os
import uvicorn
import sys
from pathlib import Path

# Load environment variables from .env file if it exists
def load_env_file():
    """Load environment variables from .env file"""
    env_file = Path('.env')
    if env_file.exists():
        print("📄 Loading environment variables from .env file")
        with open(env_file, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    os.environ[key.strip()] = value.strip()
    else:
        print("⚠️ No .env file found, using system environment variables")

def setup_environment():
    """Setup environment variables with defaults"""
    load_env_file()
    
    # Set default values if not provided
    defaults = {
        'CODEGEN_ORG_ID': '323',
        'CODEGEN_TOKEN': 'your-token-here',
        'HOST': '127.0.0.1',
        'PORT': '8887'
    }
    
    for key, default_value in defaults.items():
        if key not in os.environ:
            os.environ[key] = default_value
            print(f"🔧 Using default {key}: {default_value}")
        else:
            # Don't print the actual token for security
            if 'TOKEN' in key:
                print(f"✅ {key}: [CONFIGURED]")
            else:
                print(f"✅ {key}: {os.environ[key]}")

def main():
    """Start the OpenAI Codegen Adapter server with all features."""
    print("🚀 OpenAI Codegen Adapter Server")
    print("=" * 50)
    
    # Setup environment
    setup_environment()
    
    # Display startup information
    print("📍 Server will be available at: http://localhost:8887")
    print("🌐 Web UI: http://localhost:8887")
    print("🔗 OpenAI API: http://localhost:8887/v1")
    print("🔗 Anthropic API: http://localhost:8887/v1/messages")
    print("🔗 Google API: http://localhost:8887/v1/gemini")
    print()
    print("✨ Features:")
    print("   • OpenAI-compatible API endpoints")
    print("   • Anthropic Claude API compatibility")
    print("   • Google Gemini API compatibility")
    print("   • Web UI for testing and configuration")
    print("   • Real-time service status control")
    print("   • Comprehensive API testing tools")
    print()
    print("🧪 Test endpoints:")
    print("   • POST /api/test/openai")
    print("   • POST /api/test/anthropic")
    print("   • POST /api/test/google")
    print()
    print("Press Ctrl+C to stop the server")
    print("=" * 50)
    
    try:
        # Start the FastAPI server
        uvicorn.run(
            "openai_codegen_adapter.server:app",
            host="127.0.0.1",
            port=8887,
            log_level="info",
            reload=False,
            access_log=True
        )
    except KeyboardInterrupt:
        print("\n👋 Server stopped by user")
    except Exception as e:
        print(f"❌ Error starting server: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
