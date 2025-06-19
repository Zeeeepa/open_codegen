#!/usr/bin/env python3
"""
Test script to demonstrate automatic transparent OpenAI API interception.
This script uses the standard OpenAI client without any modifications.
"""

import os
from openai import OpenAI

def main():
    """Test transparent OpenAI API interception."""
    print("🧪 Testing Transparent OpenAI API Interception")
    print("=" * 50)
    
    # Use standard OpenAI client - no modifications needed!
    client = OpenAI(api_key="test-key")  # Any key works with interceptor
    
    try:
        print("📋 Listing available models...")
        models = client.models.list()
        
        print(f"✅ Found {len(models.data)} models via transparent interception!")
        print("\n🤖 Available models:")
        for model in models.data:
            print(f"  - {model.id} (owned by {model.owned_by})")
        
        print("\n💬 Testing chat completion...")
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "user", "content": "Say hello from the transparent interceptor!"}
            ],
            max_tokens=100
        )
        
        print("✅ Chat completion successful!")
        print(f"📝 Response: {response.choices[0].message.content}")
        print(f"🔢 Tokens used: {response.usage.total_tokens}")
        print(f"🆔 Response ID: {response.id}")
        
        print("\n🎉 Transparent interception is working perfectly!")
        print("🎯 Your OpenAI applications will work without any code changes!")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        print("\n🔧 Troubleshooting:")
        print("1. Make sure the server is running: sudo python3 server.py")
        print("2. Check DNS resolution: python3 -c \"import socket; print(socket.gethostbyname('api.openai.com'))\"")
        print("3. Verify server is responding: curl http://api.openai.com:8001/v1/models")

if __name__ == "__main__":
    main()
