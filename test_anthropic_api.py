#!/usr/bin/env python3
"""
Simple test for Anthropic API endpoint
Tests sending a message to Anthropic API and receiving a response via user interface
"""

import requests
import json
import time

def test_anthropic_api():
    """Test Anthropic API message sending and receiving"""
    print("🧪 Testing Anthropic API...")
    
    # Test data
    url = "http://localhost:8887/v1/anthropic/completions"
    headers = {"Content-Type": "application/json"}
    data = {
        "model": "claude-3-sonnet-20240229",
        "messages": [{"role": "user", "content": "Hello! Please respond with just 'Hi from Anthropic!'"}],
        "max_tokens": 50
    }
    
    try:
        # Send request
        print("📤 Sending message to Anthropic API...")
        response = requests.post(url, headers=headers, json=data, timeout=60)
        
        # Check response
        if response.status_code == 200:
            result = response.json()
            content = result.get("content", [{}])[0].get("text", "")
            print(f"✅ Anthropic API Response: {content}")
            print(f"📊 Tokens used: {result.get('usage', {})}")
            return True
        else:
            print(f"❌ Anthropic API Error: {response.status_code} - {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Anthropic API Test Failed: {e}")
        return False

if __name__ == "__main__":
    success = test_anthropic_api()
    exit(0 if success else 1)

