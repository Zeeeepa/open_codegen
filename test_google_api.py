#!/usr/bin/env python3
"""
Test script for Google/Gemini API endpoint.
"""

import json
import requests
import sys

# ANSI color codes for output formatting
YELLOW = "\033[93m"
GREEN = "\033[92m"
RED = "\033[91m"
RESET = "\033[0m"

# API endpoint
API_URL = "http://localhost:8887/v1/gemini/completions"

# Test message
TEST_MESSAGE = "Hello, this is a test message."

def test_google_api():
    """Test the Google/Gemini API endpoint."""
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
        
        # Check required fields
        required_fields = ["candidates", "usageMetadata"]
        for field in required_fields:
            if field not in data:
                print(f"{RED}❌ Missing required field: {field}{RESET}")
                return False
        
        # Check candidates
        if not isinstance(data["candidates"], list) or len(data["candidates"]) == 0:
            print(f"{RED}❌ Invalid candidates: {data.get('candidates')}{RESET}")
            return False
        
        # Check first candidate
        candidate = data["candidates"][0]
        if "content" not in candidate or "parts" not in candidate["content"]:
            print(f"{RED}❌ Invalid candidate format{RESET}")
            return False
        
        # Check parts
        parts = candidate["content"]["parts"]
        if not isinstance(parts, list) or len(parts) == 0 or "text" not in parts[0]:
            print(f"{RED}❌ Invalid parts format{RESET}")
            return False
        
        # Extract and print content
        content = parts[0]["text"]
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
    success = test_google_api()
    sys.exit(0 if success else 1)

