#!/usr/bin/env python3
"""
Test script for the Web UI functionality.
"""

import asyncio
import httpx
import time
import subprocess
import signal
import os
from pathlib import Path

async def test_webui():
    """Test the Web UI endpoints."""
    base_url = "http://localhost:8887"
    
    print("🧪 Testing Web UI functionality")
    print("=" * 50)
    
    # Test if server is running
    try:
        async with httpx.AsyncClient() as client:
            # Test root endpoint (Web UI)
            print("📄 Testing Web UI (GET /)...")
            response = await client.get(f"{base_url}/")
            print(f"   Status: {response.status_code}")
            if response.status_code == 200:
                print("   ✅ Web UI loads successfully")
                # Check if it contains expected content
                if "Codegen Adapter" in response.text:
                    print("   ✅ Web UI contains expected content")
                else:
                    print("   ⚠️  Web UI content might be incomplete")
            else:
                print(f"   ❌ Web UI failed to load: {response.status_code}")
            
            # Test status endpoint
            print("\n📊 Testing Status API (GET /api/status)...")
            response = await client.get(f"{base_url}/api/status")
            print(f"   Status: {response.status_code}")
            if response.status_code == 200:
                data = response.json()
                print(f"   ✅ Status API works: {data.get('status', 'unknown')}")
                print(f"   Service status: {data.get('status', 'unknown')}")
                print(f"   Health: {data.get('health', {}).get('status', 'unknown')}")
            else:
                print(f"   ❌ Status API failed: {response.status_code}")
            
            # Test toggle endpoint
            print("\n🔄 Testing Toggle API (POST /api/toggle)...")
            response = await client.post(f"{base_url}/api/toggle")
            print(f"   Status: {response.status_code}")
            if response.status_code == 200:
                data = response.json()
                print(f"   ✅ Toggle API works")
                print(f"   New status: {data.get('status', 'unknown')}")
                print(f"   Message: {data.get('message', 'No message')}")
            else:
                print(f"   ❌ Toggle API failed: {response.status_code}")
            
            # Test toggle again to switch back
            print("\n🔄 Testing Toggle API again...")
            response = await client.post(f"{base_url}/api/toggle")
            if response.status_code == 200:
                data = response.json()
                print(f"   ✅ Second toggle works")
                print(f"   New status: {data.get('status', 'unknown')}")
            
            # Test health endpoint
            print("\n🏥 Testing Health API (GET /health)...")
            response = await client.get(f"{base_url}/health")
            print(f"   Status: {response.status_code}")
            if response.status_code == 200:
                data = response.json()
                print(f"   ✅ Health API works: {data.get('status', 'unknown')}")
            else:
                print(f"   ❌ Health API failed: {response.status_code}")
                
    except httpx.ConnectError:
        print("❌ Could not connect to server. Make sure it's running on localhost:8887")
        return False
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        return False
    
    print("\n✅ All Web UI tests completed!")
    return True

def start_server():
    """Start the server in background."""
    print("🚀 Starting server...")
    
    # Set environment variables
    env = os.environ.copy()
    env['CODEGEN_ORG_ID'] = "323"
    env['CODEGEN_TOKEN'] = "sk-ce027fa7-3c8d-4beb-8c86-ed8ae982ac99"
    
    # Start server
    process = subprocess.Popen(
        ["python3", "server.py"],
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    
    # Wait a bit for server to start
    time.sleep(3)
    
    return process

async def main():
    """Main test function."""
    # Check if static files exist
    if not Path("static/index.html").exists():
        print("❌ static/index.html not found!")
        return
    
    print("📁 Static files found")
    
    # Start server
    server_process = start_server()
    
    try:
        # Run tests
        await test_webui()
    finally:
        # Clean up server
        print("\n🛑 Stopping server...")
        server_process.terminate()
        try:
            server_process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            server_process.kill()
        print("✅ Server stopped")

if __name__ == "__main__":
    asyncio.run(main())

