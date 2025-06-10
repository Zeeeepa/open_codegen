#!/usr/bin/env python3
"""
OpenAI Codegen Adapter Server
============================

Simple launcher that starts the complete OpenAI Codegen Adapter server
with Web UI, API endpoints, and testing capabilities.

Usage: python server.py
"""

import os
import sys
import uvicorn
from pathlib import Path

def setup_environment():
    """Set up required environment variables."""
    # Set default credentials if not already set
    if not os.environ.get('CODEGEN_ORG_ID'):
        os.environ['CODEGEN_ORG_ID'] = "323"
    
    if not os.environ.get('CODEGEN_TOKEN'):
        os.environ['CODEGEN_TOKEN'] = "sk-ce027fa7-3c8d-4beb-8c86-ed8ae982ac99"

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

