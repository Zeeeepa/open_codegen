#!/usr/bin/env python3
"""
Simple test for Google API endpoint
Tests sending a message to Google API and receiving a response via user interface
"""

import requests
import json
import time

def test_google_api():
    """Test Google API message sending and receiving"""
    print("🧪 Testing Google API...")
    
    # Test data
    url = "http://localhost:8887/v1/gemini/generateContent"
    headers = {"Content-Type": "application/json"}
    data = {
        "contents": [{"parts": [{"text": "Hello! Please respond with just 'Hi from Google!'"}]}],
        "generationConfig": {"maxOutputTokens": 50}
    }
    
    try:
        # Send request
        print("📤 Sending message to Google API...")
        response = requests.post(url, headers=headers, json=data, timeout=60)
        
        # Check response
        if response.status_code == 200:
            result = response.json()
            content = result.get("candidates", [{}])[0].get("content", {}).get("parts", [{}])[0].get("text", "")
            print(f"✅ Google API Response: {content}")
            print(f"📊 Tokens used: {result.get('usageMetadata', {})}")
            return True
        else:
            print(f"❌ Google API Error: {response.status_code} - {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Google API Test Failed: {e}")
        return False

if __name__ == "__main__":
    success = test_google_api()
    exit(0 if success else 1)

