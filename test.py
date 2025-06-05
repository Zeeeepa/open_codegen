#!/usr/bin/env python3
"""
Comprehensive test suite for OpenAI Codegen Adapter.
Tests OpenAI compatibility, Anthropic, and Gemini endpoints.
"""

import asyncio
import os
import sys
import time
from openai import OpenAI


def test_openai_chat_completion():
    """Test OpenAI chat completions endpoint."""
    print("🤖 Testing OpenAI Chat Completions...")
    
    client = OpenAI(
        api_key=os.getenv("CODEGEN_API_TOKEN", "dummy-key"),
        base_url="http://localhost:18887/v1"
    )
    
    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": "Write a simple Python function to add two numbers."}
            ],
            max_tokens=200
        )
        
        print("✅ Chat completion successful")
        print(f"   Response: {response.choices[0].message.content[:100]}...")
        return True
        
    except Exception as e:
        print(f"❌ Chat completion failed: {e}")
        return False


def test_openai_streaming():
    """Test OpenAI streaming chat completions."""
    print("🌊 Testing OpenAI Streaming...")
    
    client = OpenAI(
        api_key=os.getenv("CODEGEN_API_TOKEN", "dummy-key"),
        base_url="http://localhost:18887/v1"
    )
    
    try:
        stream = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "user", "content": "Count from 1 to 5."}
            ],
            stream=True,
            max_tokens=50
        )
        
        content = ""
        for chunk in stream:
            if chunk.choices[0].delta.content:
                content += chunk.choices[0].delta.content
        
        print("✅ Streaming successful")
        print(f"   Streamed content: {content[:100]}...")
        return True
        
    except Exception as e:
        print(f"❌ Streaming failed: {e}")
        return False


def test_openai_text_completion():
    """Test OpenAI text completions endpoint."""
    print("📝 Testing OpenAI Text Completions...")
    
    client = OpenAI(
        api_key=os.getenv("CODEGEN_API_TOKEN", "dummy-key"),
        base_url="http://localhost:18887/v1"
    )
    
    try:
        response = client.completions.create(
            model="text-davinci-003",
            prompt="The capital of France is",
            max_tokens=50
        )
        
        print("✅ Text completion successful")
        print(f"   Response: {response.choices[0].text[:100]}...")
        return True
        
    except Exception as e:
        print(f"❌ Text completion failed: {e}")
        return False


def test_health_endpoint():
    """Test health check endpoint."""
    print("🏥 Testing Health Endpoint...")
    
    try:
        import requests
        response = requests.get("http://localhost:18887/health")
        
        if response.status_code == 200:
            print("✅ Health check successful")
            print(f"   Status: {response.json()}")
            return True
        else:
            print(f"❌ Health check failed: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Health check failed: {e}")
        return False


def test_models_endpoint():
    """Test models listing endpoint."""
    print("📋 Testing Models Endpoint...")
    
    try:
        import requests
        response = requests.get("http://localhost:18887/v1/models")
        
        if response.status_code == 200:
            models = response.json()
            print("✅ Models endpoint successful")
            print(f"   Available models: {len(models.get('data', []))}")
            return True
        else:
            print(f"❌ Models endpoint failed: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Models endpoint failed: {e}")
        return False


def test_codegen_sdk():
    """Test Codegen SDK integration."""
    print("🚀 Testing Codegen SDK Integration...")
    
    try:
        from codegen import Agent
        
        agent = Agent(
            org_id=os.getenv("CODEGEN_ORG_ID", "323"),
            token=os.getenv("CODEGEN_API_TOKEN", "sk-dummy-token")
        )
        
        task = agent.run("Generate a simple 'Hello World' message")
        
        # Poll for completion (with timeout)
        max_attempts = 10
        for attempt in range(max_attempts):
            task.refresh()
            if task.status == "completed":
                print("✅ Codegen SDK test successful")
                print(f"   Result: {str(task.result)[:100]}...")
                return True
            elif task.status == "failed":
                print(f"❌ Codegen SDK task failed: {getattr(task, 'error', 'Unknown error')}")
                return False
            
            time.sleep(2)
        
        print("⏰ Codegen SDK test timed out")
        return False
        
    except ImportError:
        print("⚠️  Codegen SDK not available (import failed)")
        return True  # Don't fail the test if SDK isn't installed
    except Exception as e:
        print(f"❌ Codegen SDK test failed: {e}")
        return False


def main():
    """Run all tests."""
    print("🧪 OpenAI Codegen Adapter Test Suite")
    print("=" * 50)
    
    # Check if server is running
    try:
        import requests
        response = requests.get("http://localhost:18887/health", timeout=5)
        if response.status_code != 200:
            print("❌ Server not responding at http://localhost:18887")
            print("   Please start the server first:")
            print("   cd openai_codegen_adapter && python -m uvicorn server:app --host 0.0.0.0 --port 18887")
            return 1
    except Exception:
        print("❌ Server not running at http://localhost:18887")
        print("   Please start the server first:")
        print("   cd openai_codegen_adapter && python -m uvicorn server:app --host 0.0.0.0 --port 18887")
        return 1
    
    print("✅ Server is running, starting tests...\n")
    
    # Run all tests
    tests = [
        test_health_endpoint,
        test_models_endpoint,
        test_openai_chat_completion,
        test_openai_streaming,
        test_openai_text_completion,
        test_codegen_sdk
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        try:
            if test():
                passed += 1
            print()  # Add spacing between tests
        except Exception as e:
            print(f"❌ Test {test.__name__} crashed: {e}\n")
    
    # Summary
    print("=" * 50)
    print(f"📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed!")
        return 0
    else:
        print(f"⚠️  {total - passed} tests failed")
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
