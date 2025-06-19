#!/usr/bin/env python3
"""
Test script to verify custom port functionality works correctly.
Tests the server running on a custom port with direct access mode.
"""

import openai
import requests
import json
import sys

def test_health_endpoint():
    """Test the health endpoint."""
    print("🏥 Testing health endpoint...")
    try:
        response = requests.get("http://127.0.0.1:8002/health")
        if response.status_code == 200:
            data = response.json()
            if data.get("status") == "healthy" and data.get("codegen") == "connected":
                print("  ✅ Health check passed")
                return True
            else:
                print(f"  ❌ Unexpected health response: {data}")
                return False
        else:
            print(f"  ❌ Health check failed with status {response.status_code}")
            return False
    except Exception as e:
        print(f"  ❌ Health check error: {e}")
        return False

def test_models_endpoint():
    """Test the models endpoint."""
    print("📋 Testing models endpoint...")
    try:
        response = requests.get("http://127.0.0.1:8002/v1/models")
        if response.status_code == 200:
            data = response.json()
            if data.get("object") == "list" and "data" in data:
                models = data["data"]
                print(f"  ✅ Found {len(models)} models")
                for model in models[:3]:
                    print(f"    - {model['id']} (owned by {model['owned_by']})")
                return True
            else:
                print(f"  ❌ Unexpected models response: {data}")
                return False
        else:
            print(f"  ❌ Models endpoint failed with status {response.status_code}")
            return False
    except Exception as e:
        print(f"  ❌ Models endpoint error: {e}")
        return False

def test_chat_completion():
    """Test chat completion endpoint."""
    print("💬 Testing chat completion...")
    try:
        client = openai.OpenAI(
            api_key="test-key",
            base_url="http://127.0.0.1:8002/v1"
        )
        
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": "Say 'test successful' and nothing else."}],
            max_tokens=10
        )
        
        if response.choices and response.choices[0].message:
            content = response.choices[0].message.content
            print(f"  ✅ Chat completion successful")
            print(f"    Response: {content}")
            print(f"    Model: {response.model}")
            print(f"    Tokens: {response.usage.total_tokens}")
            return True
        else:
            print(f"  ❌ No response content received")
            return False
            
    except Exception as e:
        print(f"  ❌ Chat completion error: {e}")
        return False

def test_streaming_completion():
    """Test streaming chat completion."""
    print("🌊 Testing streaming completion...")
    try:
        client = openai.OpenAI(
            api_key="test-key",
            base_url="http://127.0.0.1:8002/v1"
        )
        
        stream = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": "Count to 3"}],
            max_tokens=20,
            stream=True
        )
        
        chunks = []
        for chunk in stream:
            if chunk.choices and chunk.choices[0].delta.content:
                chunks.append(chunk.choices[0].delta.content)
        
        if chunks:
            full_response = "".join(chunks)
            print(f"  ✅ Streaming successful")
            print(f"    Received {len(chunks)} chunks")
            print(f"    Full response: {full_response}")
            return True
        else:
            print("  ❌ No streaming chunks received")
            return False
            
    except Exception as e:
        print(f"  ❌ Streaming error: {e}")
        return False

def main():
    """Run all tests."""
    print("🧪 Testing Custom Port Server (Port 8002)")
    print("=" * 60)
    
    tests = [
        ("Health Endpoint", test_health_endpoint),
        ("Models Endpoint", test_models_endpoint),
        ("Chat Completion", test_chat_completion),
        ("Streaming Completion", test_streaming_completion),
    ]
    
    results = {}
    for test_name, test_func in tests:
        print(f"\n🔍 {test_name}")
        print("-" * 40)
        results[test_name] = test_func()
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 TEST RESULTS SUMMARY")
    print("=" * 60)
    
    passed = 0
    total = len(tests)
    
    for test_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} {test_name}")
        if result:
            passed += 1
    
    print(f"\n🎯 Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 ALL TESTS PASSED! Custom port server is working perfectly!")
        return 0
    else:
        print("⚠️  Some tests failed. Check server status.")
        return 1

if __name__ == "__main__":
    sys.exit(main())

