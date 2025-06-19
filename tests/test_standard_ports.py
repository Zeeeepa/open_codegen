#!/usr/bin/env python3
"""
Test script to verify transparent interception works on standard ports.
This uses the standard OpenAI client without any base_url modifications.
"""

import os
from openai import OpenAI

def main():
    """Test transparent OpenAI API interception on standard ports."""
    print("🧪 Testing Transparent Interception on Standard Ports")
    print("=" * 60)
    
    # Use standard OpenAI client - exactly as users would in production
    client = OpenAI(api_key="test-key")  # No base_url needed!
    
    try:
        print("📋 Listing available models...")
        models = client.models.list()
        
        print(f"✅ Found {len(models.data)} models via transparent interception!")
        print("\n🤖 Available models:")
        for model in models.data:
            print(f"  - {model.id} (owned by {model.owned_by})")
        
        print("\n🧪 Testing complete chat completion...")
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "user", "content": "Say hello from the transparent interceptor!"}
            ],
            max_tokens=100
        )
        
        print("✅ Response received!")
        print(f"📝 Content: {response.choices[0].message.content}")
        print(f"🔢 Tokens: {response.usage.total_tokens}")
        print(f"🤖 Model: {response.model}")
        
        print("\n🎉 Perfect! Transparent interception working on standard ports!")
        print("🎯 Your existing OpenAI applications will work with ZERO code changes!")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        print("\n🔧 Troubleshooting:")
        print("1. Make sure server is running: sudo python3 server.py")
        print("2. Verify DNS: python3 -c \"import socket; print(socket.gethostbyname('api.openai.com'))\"")
        print("3. Check server on port 80: curl http://api.openai.com/v1/models")
        print("4. Ensure you're running server with sudo (needed for port 80)")

if __name__ == "__main__":
    main()
