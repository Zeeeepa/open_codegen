#!/usr/bin/env python3
"""
Test the Anthropic API endpoint.
"""

import sys
import json
import requests

# Define colors for terminal output
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
RESET = "\033[0m"

# Define the API endpoint
API_URL = "http://localhost:8887/v1/anthropic/completions"
TEST_MESSAGE = "Hello, this is a test message."


def main():
    """Run the Anthropic API test."""
    print(f"{YELLOW}🧪 Testing Anthropic API...{RESET}")
    
    # Prepare the request payload
    payload = {
        "model": "claude-3-sonnet-20240229",
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
            print(f"{YELLOW}📥 Received response:{RESET}")
            print(json.dumps(data, indent=2))
            
            # Validate the response format
            if (
                "content" in data and
                len(data["content"]) > 0 and
                "text" in data["content"][0]
            ):
                content = data["content"][0]["text"]
                print(f"{GREEN}✅ Anthropic API test passed!{RESET}")
                print(f"{YELLOW}Response content:{RESET} {content}")
                return 0
            else:
                print(f"{RED}❌ Anthropic API returned invalid response format{RESET}")
                return 1
        else:
            print(f"{RED}❌ Anthropic API Error: {response.status_code} - {response.text}{RESET}")
            return 1
            
    except Exception as e:
        print(f"{RED}❌ Error testing Anthropic API: {e}{RESET}")
        return 1


if __name__ == "__main__":
    sys.exit(main())

