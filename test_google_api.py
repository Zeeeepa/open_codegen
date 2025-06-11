"""
Tests sending a message to Google API and receiving a response via user interface
"""

import os
import requests
import json

# Define the API base URL (can be overridden with environment variable)
API_BASE = os.getenv("API_BASE", "http://localhost:8887")
url = f"{API_BASE}/v1/gemini/generateContent"

# Define headers
headers = {
    "Content-Type": "application/json",
    "Authorization": f"Bearer {os.getenv('GOOGLE_API_KEY', '')}"
}

# Define the data to send
data = {
    "model": "gemini-1.5-pro",
    "contents": [
        {"parts": [{"text": "This is a test message."}]}
    ],
    "generationConfig": {
        "maxOutputTokens": 5
    }
}

print("🧪 Testing Google API...")
print(f"📤 Sending message to {url}...")

# Send the request
try:
    response = requests.post(url, headers=headers, json=data, timeout=30)
    
    # Check if the request was successful
    if response.status_code == 200:
        print("✅ Google API Response:")
        print(json.dumps(response.json(), indent=2))
        exit(0)
    else:
        print(f"❌ Google API Error: {response.status_code} - {response.text}")
        exit(1)
except Exception as e:
    print(f"❌ Google API Test Failed: {e}")
    exit(1)

