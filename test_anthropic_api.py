"""
Tests sending a message to Anthropic API and receiving a response via user interface
"""

import os
import requests
import json

# Define the API base URL (can be overridden with environment variable)
API_BASE = os.getenv("API_BASE", "http://localhost:8887")
url = f"{API_BASE}/v1/anthropic/completions"

# Define headers
headers = {
    "Content-Type": "application/json",
    "Authorization": f"Bearer {os.getenv('ANTHROPIC_API_KEY', '')}"
}

# Define the data to send
data = {
    "model": "claude-3-sonnet-20240229",
    "messages": [
        {"role": "user", "content": "Hello! Please respond with a short greeting."}
    ],
    "max_tokens": 5
}

print("🧪 Testing Anthropic API...")
print(f"📤 Sending message to {url}...")

# Send the request
try:
    response = requests.post(url, headers=headers, json=data, timeout=30)
    
    # Check if the request was successful
    if response.status_code == 200:
        print("✅ Anthropic API Response:")
        print(json.dumps(response.json(), indent=2))
        
        # Verify that the response contains actual content
        content = response.json()
        if "content" in content and len(content["content"]) > 0:
            if "text" in content["content"][0]:
                message_content = content["content"][0]["text"]
                print(f"\n📝 Response content: {message_content}")
                if "This is a response to:" in message_content:
                    print("✅ Test passed: Response contains expected content")
                    exit(0)
                else:
                    print("❌ Test failed: Response does not contain expected content")
                    exit(1)
            else:
                print("❌ Test failed: Response does not contain text content")
                exit(1)
        else:
            print("❌ Test failed: Response does not contain content")
            exit(1)
    else:
        print(f"❌ Anthropic API Error: {response.status_code} - {response.text}")
        exit(1)
except Exception as e:
    print(f"❌ Anthropic API Test Failed: {e}")
    exit(1)

