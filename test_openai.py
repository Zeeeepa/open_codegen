#!/usr/bin/env python3
"""
Test script for OpenAI API.
This script sends a message to the OpenAI API and receives a response.
"""

import requests
import json
import sys
import os

# ANSI color codes for output formatting
YELLOW = "\033[93m"
GREEN = "\033[92m"
RED = "\033[91m"
RESET = "\033[0m"

# Base URL for the OpenAI API
# This can be changed to point to the router program
BASE_URL = os.environ.get("OPENAI_API_BASE", "http://localhost:8887/v1")
API_URL = f"{BASE_URL}/chat/completions"

# Test message
TEST_MESSAGE = "Hello, this is a test message from OpenAI API test."

def test_openai_api():
    """Send a message to the OpenAI API and receive a response."""
    print(f"{YELLOW}🧪 Testing OpenAI API...{RESET}")
    
    # Prepare request payload
    payload = {
        "model": "gpt-3.5-turbo",
        "messages": [
            {"role": "user", "content": TEST_MESSAGE}
        ]
    }
    
    # Send request
    print(f"{YELLOW}📤 Sending message to {API_URL}...{RESET}")
    try:
        response = requests.post(API_URL, json=payload)
        response.raise_for_status()  # Raise exception for 4XX/5XX responses
        
        # Parse response
        data = response.json()
        
        # Pretty print response
        print(f"{YELLOW}📥 Received response:{RESET}")
        print(json.dumps(data, indent=2))
        
        # Validate response format
        if not isinstance(data, dict):
            print(f"{RED}❌ Invalid response format: not a dictionary{RESET}")
            return False
        
        # Extract content if available
        content = ""
        if "choices" in data and len(data["choices"]) > 0:
            choice = data["choices"][0]
            if "message" in choice and "content" in choice["message"]:
                content = choice["message"]["content"]
        
        print(f"{GREEN}✅ OpenAI API test passed!{RESET}")
        print(f"{YELLOW}Response content:{RESET} {content}")
        return True
        
    except requests.exceptions.RequestException as e:
        print(f"{RED}❌ Request failed: {e}{RESET}")
        return False
    except json.JSONDecodeError:
        print(f"{RED}❌ Invalid JSON response{RESET}")
        return False
    except Exception as e:
        print(f"{RED}❌ Test failed: {e}{RESET}")
        return False

if __name__ == "__main__":
    print(f"{YELLOW}🔍 Using OpenAI API base URL: {BASE_URL}{RESET}")
    print(f"{YELLOW}💡 Set OPENAI_API_BASE environment variable to change this.{RESET}")
    print()
    
    success = test_openai_api()
    sys.exit(0 if success else 1)

