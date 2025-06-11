#!/usr/bin/env python3
"""
Test script for Google/Gemini API.
This script sends a message to the Google/Gemini API and receives a response.
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

# Base URL for the Google/Gemini API
# This can be changed to point to the router program
BASE_URL = os.environ.get("GEMINI_API_URL", "http://localhost:8887/v1")
API_URL = f"{BASE_URL}/gemini/completions"

# Test message
TEST_MESSAGE = "Hello, this is a test message from Google/Gemini API test."

def test_google_api():
    """Send a message to the Google/Gemini API and receive a response."""
    print(f"{YELLOW}🧪 Testing Google/Gemini API...{RESET}")
    
    # Prepare request payload
    payload = {
        "model": "gemini-1.5-pro",
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
        if "candidates" in data and len(data["candidates"]) > 0:
            candidate = data["candidates"][0]
            if "content" in candidate and "parts" in candidate["content"] and len(candidate["content"]["parts"]) > 0:
                part = candidate["content"]["parts"][0]
                if "text" in part:
                    content = part["text"]
        
        print(f"{GREEN}✅ Google/Gemini API test passed!{RESET}")
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
    print(f"{YELLOW}🔍 Using Google/Gemini API base URL: {BASE_URL}{RESET}")
    print(f"{YELLOW}💡 Set GEMINI_API_URL environment variable to change this.{RESET}")
    print()
    
    success = test_google_api()
    sys.exit(0 if success else 1)

