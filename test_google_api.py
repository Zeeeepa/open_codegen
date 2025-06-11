#!/usr/bin/env python3
"""
Test the Google/Gemini API endpoint.
"""

import sys
import json
import time
import requests

# Define colors for terminal output
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
RESET = "\033[0m"

# Define the API endpoint
API_URL = "http://localhost:8887/v1/gemini/completions"
TEST_MESSAGE = "Hello, this is a test message. Please respond with a short greeting."


def main():
    """Run the Google/Gemini API test."""
    print(f"{YELLOW}🧪 Testing Google/Gemini API...{RESET}")
    
    # Prepare the request payload
    payload = {
        "model": "gemini-1.5-pro",
        "messages": [
            {
                "role": "user",
                "content": TEST_MESSAGE
            }
        ]
    }
    
    try:
        # Send the request
        print(f"{YELLOW}📤 Sending message to {API_URL}...{RESET}")
        response = requests.post(
            API_URL,
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=30
        )
        
        # Check if the request was successful
        if response.status_code == 200:
            data = response.json()
            
            # Validate the response format
            if (
                "candidates" in data and
                len(data["candidates"]) > 0 and
                "content" in data["candidates"][0] and
                "parts" in data["candidates"][0]["content"] and
                len(data["candidates"][0]["content"]["parts"]) > 0 and
                "text" in data["candidates"][0]["content"]["parts"][0]
            ):
                content = data["candidates"][0]["content"]["parts"][0]["text"]
                print(f"{GREEN}✅ Google/Gemini API test passed!{RESET}")
                print(f"{YELLOW}Response:{RESET} {content}")
                return 0
            else:
                print(f"{RED}❌ Google/Gemini API returned invalid response format:{RESET}")
                print(json.dumps(data, indent=2))
                return 1
        else:
            print(f"{RED}❌ Google/Gemini API Error: {response.status_code} - {response.text}{RESET}")
            return 1
            
    except Exception as e:
        print(f"{RED}❌ Error testing Google/Gemini API: {e}{RESET}")
        return 1


if __name__ == "__main__":
    sys.exit(main())

