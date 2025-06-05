#!/usr/bin/env python3
"""
Simple test for OpenAI Codegen Adapter.
Uses OpenAI client with modified baseURL to test the server.
"""

from openai import OpenAI

def main():
    """Test OpenAI API endpoint with modified baseURL."""
    print("🧪 Testing OpenAI Codegen Adapter")
    print("=" * 40)
    
    # Create OpenAI client with modified baseURL
    client = OpenAI(
        api_key="dummy-key",  # Server doesn't validate this
        base_url="http://localhost:8887/v1"  # Point to our server
    )
    
    print("📤 Sending test message...")
    
    try:
        # Send a simple chat completion request
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "user", "content": "Hello, how are you?"}
            ]
        )
        
        print("📥 Response received:")
        print(f"   Content: {response.choices[0].message.content}")
        print("✅ Test completed successfully!")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")

if __name__ == "__main__":
    main()

