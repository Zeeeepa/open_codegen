"""
Tests sending a message to OpenAI API and receiving a response via user interface
"""

import os
import requests
import json

# Define the API base URL (can be overridden with environment variable)
API_BASE = os.getenv("API_BASE", "http://localhost:8887")
url = f"{API_BASE}/v1/chat/completions"

# Define headers
headers = {
    "Content-Type": "application/json",
    "Authorization": f"Bearer {os.getenv('OPENAI_API_KEY', '')}"
}

# Define the data to send
data = {
    "model": "gpt-3.5-turbo",
    "messages": [
        {"role": "user", "content": "Hello! Please respond with a short greeting."}
    ],
    "max_tokens": 5
}

print("🧪 Testing OpenAI API...")
print(f"📤 Sending message to {url}...")

# Send the request
try:
    response = requests.post(url, headers=headers, json=data, timeout=30)
    
    # Check if the request was successful
    if response.status_code == 200:
        print("✅ OpenAI API Response:")
        print(json.dumps(response.json(), indent=2))
        
        # Verify that the response contains actual content
        content = response.json()
        if "choices" in content and len(content["choices"]) > 0:
            if "message" in content["choices"][0] and "content" in content["choices"][0]["message"]:
                message_content = content["choices"][0]["message"]["content"]
                print(f"\n📝 Response content: {message_content}")
                if "This is a response to:" in message_content:
                    print("✅ Test passed: Response contains expected content")
                    exit(0)
                else:
                    print("❌ Test failed: Response does not contain expected content")
                    exit(1)
            else:
                print("❌ Test failed: Response does not contain message content")
                exit(1)
        else:
            print("❌ Test failed: Response does not contain choices")
            exit(1)
    else:
        print(f"❌ OpenAI API Error: {response.status_code} - {response.text}")
        exit(1)
except Exception as e:
    print(f"❌ OpenAI API Test Failed: {e}")
    exit(1)

