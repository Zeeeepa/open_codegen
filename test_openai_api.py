#!/usr/bin/env python3
"""
Simple test for OpenAI API endpoint
Tests sending a message to OpenAI API and receiving a response via user interface
"""

import requests
import json
import time

def test_openai_api():
    """Test OpenAI API message sending and receiving"""
    print("🧪 Testing OpenAI API...")
    
    # Test data
    url = "http://localhost:8887/v1/chat/completions"
    headers = {"Content-Type": "application/json"}
    data = {
        "model": "gpt-4",
        "messages": [{"role": "user", "content": "Hello! Please respond with just 'Hi from OpenAI!'"}],
        "max_tokens": 50
    }
    
    try:
        # Send request
        print("📤 Sending message to OpenAI API...")
        response = requests.post(url, headers=headers, json=data, timeout=60)
        
        # Check response
        if response.status_code == 200:
            result = response.json()
            content = result.get("choices", [{}])[0].get("message", {}).get("content", "")
            print(f"✅ OpenAI API Response: {content}")
            print(f"📊 Tokens used: {result.get('usage', {})}")
            return True
        else:
            print(f"❌ OpenAI API Error: {response.status_code} - {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ OpenAI API Test Failed: {e}")
        return False

if __name__ == "__main__":
    success = test_openai_api()
    exit(0 if success else 1)

