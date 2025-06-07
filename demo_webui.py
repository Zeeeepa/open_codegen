#!/usr/bin/env python3
"""
Demo script for the Web UI functionality.
Shows how to start the server and access the Web UI.
"""

import subprocess
import time
import webbrowser
import os
import signal
import sys

def main():
    """Demo the Web UI functionality."""
    print("🚀 OpenAI Codegen Adapter - Web UI Demo")
    print("=" * 50)
    
    # Set environment variables
    os.environ['CODEGEN_ORG_ID'] = "323"
    os.environ['CODEGEN_TOKEN'] = "sk-ce027fa7-3c8d-4beb-8c86-ed8ae982ac99"
    
    print("📋 Starting the OpenAI Codegen Adapter server...")
    print("🔗 Server will be available at: http://localhost:8887")
    print("🎛️ Web UI will be available at: http://localhost:8887")
    print("📡 API endpoints at: http://localhost:8887/v1")
    print()
    
    try:
        # Start the server
        process = subprocess.Popen(
            ["python3", "server.py"],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            universal_newlines=True
        )
        
        # Wait for server to start
        print("⏳ Waiting for server to start...")
        time.sleep(3)
        
        # Open web browser
        print("🌐 Opening Web UI in your default browser...")
        webbrowser.open("http://localhost:8887")
        
        print()
        print("✅ Server is running!")
        print("📖 Web UI Features:")
        print("   • Real-time service status (ON/OFF)")
        print("   • Toggle button to enable/disable service")
        print("   • Health monitoring")
        print("   • Beautiful, responsive interface")
        print()
        print("🎯 Try these actions in the Web UI:")
        print("   1. View the current service status")
        print("   2. Click 'Turn Off' to disable the service")
        print("   3. Click 'Turn On' to re-enable the service")
        print("   4. Watch the real-time status updates")
        print()
        print("🔧 API Testing:")
        print("   • Status: curl http://localhost:8887/api/status")
        print("   • Toggle: curl -X POST http://localhost:8887/api/toggle")
        print("   • Health: curl http://localhost:8887/health")
        print()
        print("Press Ctrl+C to stop the server...")
        
        # Keep the server running
        try:
            process.wait()
        except KeyboardInterrupt:
            print("\n🛑 Stopping server...")
            process.terminate()
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()
            print("✅ Server stopped successfully!")
            
    except FileNotFoundError:
        print("❌ Error: Could not find server.py")
        print("   Make sure you're in the correct directory")
    except Exception as e:
        print(f"❌ Error starting server: {e}")

if __name__ == "__main__":
    main()

