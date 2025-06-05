#!/usr/bin/env python3
"""
Simple test for Anthropic Claude API compatibility.
Uses Anthropic client with modified base_url to test the server.
"""

import requests
import json

def test_anthropic_api():
    """Test Anthropic API endpoint with modified base_url."""
    print("🤖 Testing Anthropic Claude API Compatibility")
    print("=" * 50)
    
    # Anthropic API endpoint
    url = "http://localhost:8887/v1/messages"
    
    # Anthropic API request format
    payload = {
        "model": "claude-3-sonnet-20240229",
        "max_tokens": 1024,
        "messages": [
            {
                "role": "user",
                "content": "Hello, how are you today?"
            }
        ]
    }
    
    headers = {
        "Content-Type": "application/json",
        "x-api-key": "dummy-key",  # Server doesn't validate this
        "anthropic-version": "2023-06-01"
    }
    
    print("📤 Sending test message...")
    print(f"   🎯 URL: {url}")
    print(f"   📝 Message: {payload['messages'][0]['content']}")
    
    try:
        # Send request
        response = requests.post(url, json=payload, headers=headers)
        
        if response.status_code == 200:
            data = response.json()
            print("📥 Response received:")
            print(f"   ✅ Status: {response.status_code}")
            print(f"   🆔 ID: {data.get('id', 'N/A')}")
            print(f"   🤖 Model: {data.get('model', 'N/A')}")
            print(f"   📄 Content: {data.get('content', [{}])[0].get('text', 'N/A')[:100]}...")
            print(f"   🔢 Usage: {data.get('usage', {})}")
            print("✅ Test completed successfully!")
        else:
            print(f"❌ Test failed with status {response.status_code}")
            print(f"   📄 Response: {response.text}")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")

def test_anthropic_streaming():
    """Test Anthropic streaming API."""
    print("\n🌊 Testing Anthropic Streaming API")
    print("=" * 50)
    
    # Anthropic API endpoint
    url = "http://localhost:8887/v1/messages"
    
    # Anthropic API request format with streaming
    payload = {
        "model": "claude-3-sonnet-20240229",
        "max_tokens": 1024,
        "stream": True,
        "messages": [
            {
                "role": "user",
                "content": "Tell me a short joke"
            }
        ]
    }
    
    headers = {
        "Content-Type": "application/json",
        "x-api-key": "dummy-key",
        "anthropic-version": "2023-06-01"
    }
    
    print("📤 Sending streaming test message...")
    
    try:
        # Send streaming request
        response = requests.post(url, json=payload, headers=headers, stream=True)
        
        if response.status_code == 200:
            print("📥 Streaming response received:")
            event_count = 0
            for line in response.iter_lines():
                if line:
                    line_str = line.decode('utf-8')
                    if line_str.startswith('data: '):
                        event_count += 1
                        data_str = line_str[6:]  # Remove 'data: ' prefix
                        try:
                            data = json.loads(data_str)
                            print(f"   📦 Event {event_count}: {data.get('type', 'unknown')}")
                        except json.JSONDecodeError:
                            print(f"   📦 Event {event_count}: {data_str[:50]}...")
            print(f"✅ Streaming test completed! Received {event_count} events")
        else:
            print(f"❌ Streaming test failed with status {response.status_code}")
            print(f"   📄 Response: {response.text}")
        
    except Exception as e:
        print(f"❌ Streaming test failed: {e}")

if __name__ == "__main__":
    test_anthropic_api()
    test_anthropic_streaming()

