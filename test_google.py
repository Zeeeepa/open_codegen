#!/usr/bin/env python3
"""
Simple test for Google Gemini API compatibility.
Tests the Gemini generateContent endpoint with the adapter.
"""

import requests
import json

def test_gemini_api():
    """Test Gemini API endpoint with generateContent format."""
    print("🤖 Testing Google Gemini API Compatibility")
    print("=" * 50)
    
    # Gemini API endpoint
    url = "http://localhost:18887/v1/gemini/generateContent"
    
    # Gemini API request format
    payload = {
        "contents": [
            {
                "role": "user",
                "parts": [
                    {
                        "text": "Hello! Can you help me write a simple Python function to calculate the factorial of a number?"
                    }
                ]
            }
        ],
        "generationConfig": {
            "temperature": 0.7,
            "maxOutputTokens": 1024,
            "topP": 0.9
        }
    }
    
    headers = {
        "Content-Type": "application/json"
    }
    
    print("📤 Sending test message...")
    print(f"   🎯 URL: {url}")
    print(f"   📝 Message: {payload['contents'][0]['parts'][0]['text']}")
    
    try:
        # Send request
        response = requests.post(url, json=payload, headers=headers)
        
        if response.status_code == 200:
            data = response.json()
            print("📥 Response received:")
            print(f"   ✅ Status: {response.status_code}")
            
            if 'candidates' in data and len(data['candidates']) > 0:
                candidate = data['candidates'][0]
                if 'content' in candidate and 'parts' in candidate['content']:
                    content = candidate['content']['parts'][0]['text']
                    print(f"   📄 Content: {content[:200]}...")
                    
            if 'usageMetadata' in data:
                usage = data['usageMetadata']
                print(f"   🔢 Usage: {usage}")
                
            print("✅ Test completed successfully!")
        else:
            print(f"❌ Test failed with status {response.status_code}")
            print(f"   📄 Response: {response.text}")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")

def test_gemini_streaming():
    """Test Gemini streaming API."""
    print("\n🌊 Testing Gemini Streaming API")
    print("=" * 50)
    
    # Gemini API endpoint
    url = "http://localhost:18887/v1/gemini/generateContent"
    
    # Gemini API request format with streaming
    payload = {
        "contents": [
            {
                "role": "user",
                "parts": [
                    {
                        "text": "Write a short poem about coding"
                    }
                ]
            }
        ],
        "generationConfig": {
            "temperature": 0.8,
            "maxOutputTokens": 512
        }
    }
    
    headers = {
        "Content-Type": "application/json"
    }
    
    print("📤 Sending streaming test message...")
    
    try:
        # Send streaming request
        response = requests.post(url, json=payload, headers=headers, stream=True)
        
        if response.status_code == 200:
            print("📥 Streaming response received:")
            chunk_count = 0
            for line in response.iter_lines():
                if line:
                    line_str = line.decode('utf-8')
                    if line_str.startswith('data: '):
                        chunk_count += 1
                        data_str = line_str[6:]  # Remove 'data: ' prefix
                        if data_str != '[DONE]':
                            try:
                                data = json.loads(data_str)
                                print(f"   📦 Chunk {chunk_count}: {data.get('candidates', [{}])[0].get('content', {}).get('parts', [{}])[0].get('text', '')[:50]}...")
                            except json.JSONDecodeError:
                                print(f"   📦 Chunk {chunk_count}: {data_str[:50]}...")
                        else:
                            print(f"   🏁 Stream completed")
            print(f"✅ Streaming test completed! Received {chunk_count} chunks")
        else:
            print(f"❌ Streaming test failed with status {response.status_code}")
            print(f"   📄 Response: {response.text}")
        
    except Exception as e:
        print(f"❌ Streaming test failed: {e}")

def test_gemini_with_system_instruction():
    """Test Gemini API with system instruction."""
    print("\n🎯 Testing Gemini with System Instruction")
    print("=" * 50)
    
    # Gemini API endpoint
    url = "http://localhost:18887/v1/gemini/generateContent"
    
    # Gemini API request format with system instruction
    payload = {
        "systemInstruction": {
            "parts": [
                {
                    "text": "You are a helpful coding assistant. Always provide clear, well-commented code examples."
                }
            ]
        },
        "contents": [
            {
                "role": "user",
                "parts": [
                    {
                        "text": "Show me how to create a simple REST API with FastAPI"
                    }
                ]
            }
        ],
        "generationConfig": {
            "temperature": 0.3,
            "maxOutputTokens": 1024
        }
    }
    
    headers = {
        "Content-Type": "application/json"
    }
    
    print("📤 Sending test with system instruction...")
    
    try:
        # Send request
        response = requests.post(url, json=payload, headers=headers)
        
        if response.status_code == 200:
            data = response.json()
            print("📥 Response received:")
            print(f"   ✅ Status: {response.status_code}")
            
            if 'candidates' in data and len(data['candidates']) > 0:
                candidate = data['candidates'][0]
                if 'content' in candidate and 'parts' in candidate['content']:
                    content = candidate['content']['parts'][0]['text']
                    print(f"   📄 Content: {content[:300]}...")
                    
            print("✅ System instruction test completed successfully!")
        else:
            print(f"❌ Test failed with status {response.status_code}")
            print(f"   📄 Response: {response.text}")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")

if __name__ == "__main__":
    test_gemini_api()
    test_gemini_streaming()
    test_gemini_with_system_instruction()
