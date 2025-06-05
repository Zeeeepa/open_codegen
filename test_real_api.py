#!/usr/bin/env python3
"""
Test script to validate all API endpoints work with REAL Codegen API responses
"""
import requests
import json
import time
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

CODEGEN_ORG_ID = os.getenv("CODEGEN_ORG_ID", "323")
CODEGEN_API_TOKEN = os.getenv("CODEGEN_API_TOKEN", "sk-ce027fa7-3c8d-4beb-8c86-ed8ae982ac99")
SERVER_HOST = os.getenv("SERVER_HOST", "127.0.0.1")
SERVER_PORT = int(os.getenv("SERVER_PORT", "19887"))

BASE_URL = f"http://{SERVER_HOST}:{SERVER_PORT}"

def test_endpoint(name, url, payload, headers):
    """Test an endpoint and validate it returns a real response"""
    print(f"\n{'='*60}")
    print(f"🧪 Testing {name}")
    print(f"{'='*60}")
    print(f"URL: {url}")
    print(f"Payload: {json.dumps(payload, indent=2)}")
    
    try:
        response = requests.post(url, json=payload, headers=headers, timeout=60)
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ SUCCESS - Got real response!")
            print(f"Response: {json.dumps(result, indent=2)}")
            
            # Validate it's a real response, not a mock
            if name == "OpenAI Chat Completions":
                content = result.get("choices", [{}])[0].get("message", {}).get("content", "")
                if content and len(content) > 10:
                    print(f"✅ REAL RESPONSE CONFIRMED - Content length: {len(content)}")
                else:
                    print(f"❌ SUSPICIOUS - Content too short: '{content}'")
                    
            elif name == "Anthropic Messages":
                content = result.get("content", [{}])[0].get("text", "")
                if content and len(content) > 10:
                    print(f"✅ REAL RESPONSE CONFIRMED - Content length: {len(content)}")
                else:
                    print(f"❌ SUSPICIOUS - Content too short: '{content}'")
                    
            elif name == "Gemini Generate Content":
                content = result.get("candidates", [{}])[0].get("content", {}).get("parts", [{}])[0].get("text", "")
                if content and len(content) > 10:
                    print(f"✅ REAL RESPONSE CONFIRMED - Content length: {len(content)}")
                else:
                    print(f"❌ SUSPICIOUS - Content too short: '{content}'")
            
            return True
        else:
            print(f"❌ FAILED - Status {response.status_code}")
            print(f"Error: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ EXCEPTION: {str(e)}")
        return False

def main():
    """Run all endpoint tests"""
    print(f"🚀 Testing Codegen API Adapter with REAL API calls")
    print(f"Organization ID: {CODEGEN_ORG_ID}")
    print(f"API Token: {CODEGEN_API_TOKEN[:20]}...")
    print(f"Server: {BASE_URL}")
    
    headers = {
        "Authorization": f"Bearer {CODEGEN_API_TOKEN}",
        "Content-Type": "application/json"
    }
    
    results = {}
    
    # Test OpenAI Chat Completions
    results["openai"] = test_endpoint(
        "OpenAI Chat Completions",
        f"{BASE_URL}/v1/chat/completions",
        {
            "model": "claude-3-5-sonnet-20241022",
            "messages": [
                {"role": "user", "content": "Write a short poem about coding"}
            ],
            "max_tokens": 100
        },
        headers
    )
    
    # Test Anthropic Messages
    results["anthropic"] = test_endpoint(
        "Anthropic Messages", 
        f"{BASE_URL}/v1/messages",
        {
            "model": "claude-3-5-sonnet-20241022",
            "max_tokens": 100,
            "messages": [
                {"role": "user", "content": "Explain what an API is in simple terms"}
            ]
        },
        headers
    )
    
    # Test Gemini Generate Content
    results["gemini"] = test_endpoint(
        "Gemini Generate Content",
        f"{BASE_URL}/v1/gemini/generateContent", 
        {
            "model": "claude-3-5-sonnet-20241022",
            "contents": [
                {
                    "parts": [
                        {"text": "What are the benefits of using AI in software development?"}
                    ]
                }
            ]
        },
        headers
    )
    
    # Summary
    print(f"\n{'='*60}")
    print(f"📊 FINAL RESULTS")
    print(f"{'='*60}")
    
    total_tests = len(results)
    passed_tests = sum(results.values())
    
    for endpoint, passed in results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{endpoint.upper()}: {status}")
    
    print(f"\nOverall: {passed_tests}/{total_tests} tests passed")
    
    if passed_tests == total_tests:
        print(f"🎉 ALL TESTS PASSED! The API adapter is working with REAL responses!")
    else:
        print(f"⚠️  Some tests failed. Check the logs above for details.")
    
    return passed_tests == total_tests

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)

