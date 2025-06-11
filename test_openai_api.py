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
        {"role": "user", "content": "This is a test message."}
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
        exit(0)
    else:
        print(f"❌ OpenAI API Error: {response.status_code} - {response.text}")
        exit(1)
except Exception as e:
    print(f"❌ OpenAI API Test Failed: {e}")
    exit(1)

