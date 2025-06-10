#!/usr/bin/env python3
"""
OpenAI Codegen Adapter Dashboard Launcher
=========================================

Easy launcher for the web UI dashboard.
"""

import os
import sys
import subprocess
from pathlib import Path

def main():
    """Launch the dashboard server."""
    print("🚀 OpenAI Codegen Adapter Dashboard")
    print("=" * 40)
    
    # Check if required dependencies are installed
    try:
        import fastapi
        import uvicorn
        import jinja2
    except ImportError as e:
        print(f"❌ Missing required dependency: {e}")
        print("📦 Please install required packages:")
        print("   pip install fastapi uvicorn jinja2")
        sys.exit(1)
    
    # Get the dashboard server path
    dashboard_path = Path(__file__).parent / "web_ui" / "dashboard_server.py"
    
    if not dashboard_path.exists():
        print(f"❌ Dashboard server not found at: {dashboard_path}")
        sys.exit(1)
    
    print("🌐 Starting dashboard server...")
    print("📊 Dashboard will be available at: http://127.0.0.1:8888")
    print("🔧 Configure service providers and run tests")
    print("💬 View real-time message history")
    print()
    print("Press Ctrl+C to stop the server")
    print()
    
    try:
        # Run the dashboard server
        subprocess.run([
            sys.executable, str(dashboard_path),
            "--host", "127.0.0.1",
            "--port", "8888"
        ], check=True)
    except KeyboardInterrupt:
        print("\n👋 Dashboard server stopped")
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to start dashboard server: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()

