#!/usr/bin/env python3
"""
Test script to verify true transparent interception works with both HTTP and HTTPS.
This tests the standard OpenAI client without any modifications.
"""

import os
import ssl
import urllib3
from openai import OpenAI

# Disable SSL warnings for self-signed certificates
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def test_https_with_self_signed():
    """Test HTTPS with self-signed certificate (ignore SSL verification)."""
    print("🔐 Testing HTTPS with self-signed certificate...")
    
    # Create SSL context that ignores certificate verification
    import httpx
    
    # Create client that ignores SSL verification for testing
    client = OpenAI(
        api_key="test-key",
        http_client=httpx.Client(verify=False)  # Ignore SSL verification for self-signed cert
    )
    
    try:
        print("📋 Listing models via HTTPS...")
        models = client.models.list()
        print(f"✅ HTTPS Success! Found {len(models.data)} models")
        return True
    except Exception as e:
        print(f"❌ HTTPS Error: {e}")
        return False

def test_http_fallback():
    """Test HTTP fallback."""
    print("🌐 Testing HTTP fallback...")
    
    client = OpenAI(
        api_key="test-key",
        base_url="http://api.openai.com/v1"
    )
    
    try:
        print("📋 Listing models via HTTP...")
        models = client.models.list()
        print(f"✅ HTTP Success! Found {len(models.data)} models")
        return True
    except Exception as e:
        print(f"❌ HTTP Error: {e}")
        return False

def test_standard_client():
    """Test standard OpenAI client (should use HTTPS by default)."""
    print("🎯 Testing standard OpenAI client (HTTPS default)...")
    
    client = OpenAI(api_key="test-key")
    
    try:
        print("📋 Listing models with standard client...")
        models = client.models.list()
        print(f"✅ Standard Client Success! Found {len(models.data)} models")
        print("🎉 TRUE TRANSPARENT INTERCEPTION WORKING!")
        return True
    except Exception as e:
        print(f"❌ Standard Client Error: {e}")
        return False

def main():
    """Test transparent interception with both HTTP and HTTPS."""
    print("🧪 Testing True Transparent Interception")
    print("=" * 60)
    
    results = {
        'https_self_signed': False,
        'http_fallback': False,
        'standard_client': False
    }
    
    # Test HTTPS with self-signed certificate
    results['https_self_signed'] = test_https_with_self_signed()
    print()
    
    # Test HTTP fallback
    results['http_fallback'] = test_http_fallback()
    print()
    
    # Test standard client (the ultimate test)
    results['standard_client'] = test_standard_client()
    print()
    
    # Summary
    print("📊 Test Results Summary:")
    print("=" * 40)
    for test, passed in results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{test.replace('_', ' ').title()}: {status}")
    
    if results['standard_client']:
        print("\n🎉 SUCCESS: True transparent interception is working!")
        print("🎯 OpenAI applications work with ZERO code changes!")
    elif results['http_fallback']:
        print("\n⚠️ PARTIAL: HTTP interception working, HTTPS needs attention")
        print("🔧 Standard OpenAI clients may need SSL certificate trust")
    else:
        print("\n❌ FAILED: Transparent interception not working")
        print("🔧 Check server status and DNS configuration")
    
    print("\n🔧 Troubleshooting:")
    print("1. Make sure server is running: sudo python3 server.py")
    print("2. Verify DNS: python3 -c \"import socket; print(socket.gethostbyname('api.openai.com'))\"")
    print("3. Check HTTP: curl http://api.openai.com/v1/models")
    print("4. Check HTTPS: curl -k https://api.openai.com/v1/models")

if __name__ == "__main__":
    main()
