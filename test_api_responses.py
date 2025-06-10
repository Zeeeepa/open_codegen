#!/usr/bin/env python3
"""
Test script to verify that OpenAI, Anthropic, and Google API responses 
are properly returned to users.
"""

import requests
import json
import time
import sys

# Test configuration
BASE_URL = "http://localhost:8887"
TEST_PROMPT = "Hello! Please respond with a simple greeting."

def test_openai_api():
    """Test OpenAI API endpoint"""
    print("🔵 Testing OpenAI API...")
    
    url = f"{BASE_URL}/v1/chat/completions"
    headers = {"Content-Type": "application/json"}
    data = {
        "model": "gpt-3.5-turbo",
        "messages": [{"role": "user", "content": TEST_PROMPT}],
        "stream": False
    }
    
    try:
        start_time = time.time()
        response = requests.post(url, headers=headers, json=data, timeout=180)
        elapsed = time.time() - start_time
        
        print(f"   Status: {response.status_code}")
        print(f"   Time: {elapsed:.1f}s")
        
        if response.status_code == 200:
            result = response.json()
            content = result.get('choices', [{}])[0].get('message', {}).get('content', '')
            print(f"   Response: {content[:100]}...")
            print("   ✅ OpenAI API working!")
            return True
        else:
            print(f"   ❌ Error: {response.text}")
            return False
            
    except Exception as e:
        print(f"   ❌ Exception: {e}")
        return False

def test_anthropic_api():
    """Test Anthropic API endpoint"""
    print("\n🟠 Testing Anthropic API...")
    
    url = f"{BASE_URL}/v1/messages"
    headers = {"Content-Type": "application/json"}
    data = {
        "model": "claude-3-sonnet-20240229",
        "messages": [{"role": "user", "content": TEST_PROMPT}],
        "max_tokens": 100,
        "stream": False
    }
    
    try:
        start_time = time.time()
        response = requests.post(url, headers=headers, json=data, timeout=180)
        elapsed = time.time() - start_time
        
        print(f"   Status: {response.status_code}")
        print(f"   Time: {elapsed:.1f}s")
        
        if response.status_code == 200:
            result = response.json()
            content = result.get('content', [{}])[0].get('text', '')
            print(f"   Response: {content[:100]}...")
            print("   ✅ Anthropic API working!")
            return True
        else:
            print(f"   ❌ Error: {response.text}")
            return False
            
    except Exception as e:
        print(f"   ❌ Exception: {e}")
        return False

def test_google_api():
    """Test Google/Gemini API endpoint"""
    print("\n🔴 Testing Google/Gemini API...")
    
    url = f"{BASE_URL}/v1/gemini/generateContent"
    headers = {"Content-Type": "application/json"}
    data = {
        "model": "gemini-pro",
        "contents": [{"parts": [{"text": TEST_PROMPT}]}],
        "generationConfig": {"maxOutputTokens": 100}
    }
    
    try:
        start_time = time.time()
        response = requests.post(url, headers=headers, json=data, timeout=180)
        elapsed = time.time() - start_time
        
        print(f"   Status: {response.status_code}")
        print(f"   Time: {elapsed:.1f}s")
        
        if response.status_code == 200:
            result = response.json()
            candidates = result.get('candidates', [])
            if candidates:
                content = candidates[0].get('content', {}).get('parts', [{}])[0].get('text', '')
                print(f"   Response: {content[:100]}...")
                print("   ✅ Google API working!")
                return True
            else:
                print("   ❌ No candidates in response")
                return False
        else:
            print(f"   ❌ Error: {response.text}")
            return False
            
    except Exception as e:
        print(f"   ❌ Exception: {e}")
        return False

def test_server_health():
    """Test server health endpoint"""
    print("🏥 Testing server health...")
    
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=10)
        if response.status_code == 200:
            print("   ✅ Server is healthy!")
            return True
        else:
            print(f"   ❌ Health check failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"   ❌ Health check exception: {e}")
        return False

def main():
    """Run all API tests"""
    print("🧪 Testing API Response Visibility")
    print("=" * 50)
    
    # Test server health first
    if not test_server_health():
        print("\n❌ Server is not responding. Please start the server first:")
        print("   python server.py")
        sys.exit(1)
    
    # Test all APIs
    results = []
    results.append(test_openai_api())
    results.append(test_anthropic_api())
    results.append(test_google_api())
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 Test Results Summary:")
    
    api_names = ["OpenAI", "Anthropic", "Google"]
    for i, (name, result) in enumerate(zip(api_names, results)):
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"   {name} API: {status}")
    
    total_passed = sum(results)
    print(f"\n🎯 Overall: {total_passed}/3 APIs working properly")
    
    if total_passed == 3:
        print("🎉 All APIs are returning responses to users!")
    else:
        print("⚠️  Some APIs are not working properly. Check the logs above.")
        sys.exit(1)

if __name__ == "__main__":
    main()

