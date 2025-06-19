#!/usr/bin/env python3
"""
Test transparent OpenAI API interception.
This test verifies that unmodified OpenAI client code works with the interceptor.
"""

import os
import sys
import time
import socket
import subprocess
from pathlib import Path

def test_dns_resolution():
    """Test that api.openai.com resolves to localhost."""
    print("🧪 Testing DNS resolution...")
    try:
        ip = socket.gethostbyname("api.openai.com")
        if ip == "127.0.0.1":
            print(f"✅ DNS interception working: api.openai.com -> {ip}")
            return True
        else:
            print(f"❌ DNS not intercepted: api.openai.com -> {ip}")
            return False
    except Exception as e:
        print(f"❌ DNS resolution failed: {e}")
        return False

def test_openai_client_transparent():
    """Test OpenAI client works transparently without modification."""
    print("🧪 Testing transparent OpenAI client...")
    
    try:
        # This is the key test - using OpenAI client WITHOUT modifying base_url
        from openai import OpenAI
        
        # Standard OpenAI client initialization (no base_url modification!)
        client = OpenAI(
            api_key="test-key-for-interceptor"  # Dummy key for testing
        )
        
        print("✅ OpenAI client initialized without base_url modification")
        
        # Test a simple completion request
        try:
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "user", "content": "Hello! This is a test of transparent interception."}
                ],
                max_tokens=50
            )
            
            print("✅ OpenAI API call succeeded through transparent interception")
            print(f"📝 Response: {response.choices[0].message.content[:100]}...")
            return True
            
        except Exception as e:
            print(f"❌ OpenAI API call failed: {e}")
            return False
            
    except ImportError:
        print("⚠️ OpenAI library not installed. Install with: pip install openai")
        return False
    except Exception as e:
        print(f"❌ OpenAI client test failed: {e}")
        return False

def test_requests_transparent():
    """Test direct HTTP requests to api.openai.com are intercepted."""
    print("🧪 Testing transparent HTTP interception...")
    
    try:
        import requests
        
        # Direct request to api.openai.com (should be intercepted)
        response = requests.get(
            "http://api.openai.com/v1/models",
            headers={"Authorization": "Bearer test-key"},
            timeout=10
        )
        
        if response.status_code in [200, 401, 403]:  # Any response means interception worked
            print("✅ HTTP request to api.openai.com was intercepted")
            return True
        else:
            print(f"❌ Unexpected response status: {response.status_code}")
            return False
            
    except requests.exceptions.ConnectionError as e:
        if "127.0.0.1" in str(e) or "localhost" in str(e):
            print("✅ Request intercepted (connection to localhost)")
            return True
        else:
            print(f"❌ Connection error: {e}")
            return False
    except Exception as e:
        print(f"❌ HTTP test failed: {e}")
        return False

def check_interceptor_status():
    """Check if the interceptor service is running."""
    print("🔍 Checking interceptor status...")
    
    # Check if service is running
    try:
        result = subprocess.run(
            ["systemctl", "is-active", "openai-interceptor"],
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0:
            print("✅ OpenAI Interceptor service is running")
            return True
        else:
            print("❌ OpenAI Interceptor service is not running")
            print("   Start with: sudo systemctl start openai-interceptor")
            return False
    except FileNotFoundError:
        print("⚠️ systemctl not found - checking manually...")
        
        # Try to connect to the interceptor port
        try:
            import socket
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(2)
            result = sock.connect_ex(('127.0.0.1', 80))
            sock.close()
            
            if result == 0:
                print("✅ Interceptor appears to be running on port 80")
                return True
            else:
                print("❌ No service running on port 80")
                return False
        except Exception as e:
            print(f"❌ Status check failed: {e}")
            return False

def main():
    """Run all transparent mode tests."""
    print("🚀 OpenAI API Transparent Interception Test")
    print("=" * 50)
    print()
    
    tests_passed = 0
    total_tests = 4
    
    # Test 1: Check interceptor service status
    if check_interceptor_status():
        tests_passed += 1
    print()
    
    # Test 2: DNS resolution
    if test_dns_resolution():
        tests_passed += 1
    print()
    
    # Test 3: HTTP interception
    if test_requests_transparent():
        tests_passed += 1
    print()
    
    # Test 4: OpenAI client transparent mode
    if test_openai_client_transparent():
        tests_passed += 1
    print()
    
    # Results
    print("=" * 50)
    print(f"📊 Test Results: {tests_passed}/{total_tests} tests passed")
    
    if tests_passed == total_tests:
        print("🎉 All tests passed! Transparent interception is working correctly.")
        print("✅ Applications using OpenAI API will work without modification.")
        return True
    else:
        print("❌ Some tests failed. Check the interceptor configuration.")
        print()
        print("🔧 Troubleshooting:")
        print("  1. Ensure interceptor is installed: sudo ./install-ubuntu.sh")
        print("  2. Check service status: sudo systemctl status openai-interceptor")
        print("  3. Check DNS: sudo python3 -m interceptor.ubuntu_dns status")
        print("  4. Check SSL: sudo python3 -m interceptor.ubuntu_ssl status")
        print("  5. View logs: sudo journalctl -u openai-interceptor -f")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
