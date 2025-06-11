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
    "messages": [{"role": "user", "content": "Hello! Please respond with a short greeting."}],
    "contents": [
        {"parts": [{"text": "Hello! Please respond with a short greeting."}]}
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
        
        # Verify that the response contains actual content
        content = response.json()
        if "candidates" in content and len(content["candidates"]) > 0:
            if "content" in content["candidates"][0] and "parts" in content["candidates"][0]["content"]:
                parts = content["candidates"][0]["content"]["parts"]
                if len(parts) > 0 and "text" in parts[0]:
                    message_content = parts[0]["text"]
                    print(f"\n📝 Response content: {message_content}")
                    if "This is a response to:" in message_content:
                        print("✅ Test passed: Response contains expected content")
                        exit(0)
                    else:
                        print("❌ Test failed: Response does not contain expected content")
                        exit(1)
                else:
                    print("❌ Test failed: Response does not contain text in parts")
                    exit(1)
            else:
                print("❌ Test failed: Response does not contain content or parts")
                exit(1)
        else:
            print("❌ Test failed: Response does not contain candidates")
            exit(1)
    else:
        print(f"❌ Google API Error: {response.status_code} - {response.text}")
        exit(1)
except Exception as e:
    print(f"❌ Google API Test Failed: {e}")
    exit(1)

