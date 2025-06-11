#!/usr/bin/env python3
"""
Test script for OpenAI API endpoint.
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
API_URL = "http://localhost:8887/v1/chat/completions"

# Test message
TEST_MESSAGE = "Hello, this is a test message."

def test_openai_api():
    """Test the OpenAI API endpoint."""
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
        
        # Check required fields
        required_fields = ["id", "object", "created", "model", "choices", "usage"]
        for field in required_fields:
            if field not in data:
                print(f"{RED}❌ Missing required field: {field}{RESET}")
                return False
        
        # Check choices
        if not isinstance(data["choices"], list) or len(data["choices"]) == 0:
            print(f"{RED}❌ Invalid choices: {data.get('choices')}{RESET}")
            return False
        
        # Check first choice
        choice = data["choices"][0]
        if "message" not in choice or "role" not in choice["message"] or "content" not in choice["message"]:
            print(f"{RED}❌ Invalid message format in choice{RESET}")
            return False
        
        # Extract and print content
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
    success = test_openai_api()
    sys.exit(0 if success else 1)

