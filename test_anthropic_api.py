#!/usr/bin/env python3
"""
Test script for Anthropic API endpoint.
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
API_URL = "http://localhost:8887/v1/anthropic/completions"

# Test message
TEST_MESSAGE = "Hello, this is a test message."

def test_anthropic_api():
    """Test the Anthropic API endpoint."""
    print(f"{YELLOW}🧪 Testing Anthropic API...{RESET}")
    
    # Prepare request payload
    payload = {
        "model": "claude-3-sonnet-20240229",
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
        required_fields = ["id", "type", "role", "content", "model", "stop_reason", "usage"]
        for field in required_fields:
            if field not in data:
                print(f"{RED}❌ Missing required field: {field}{RESET}")
                return False
        
        # Check content
        if not isinstance(data["content"], list) or len(data["content"]) == 0:
            print(f"{RED}❌ Invalid content: {data.get('content')}{RESET}")
            return False
        
        # Check first content item
        content_item = data["content"][0]
        if "type" not in content_item or "text" not in content_item:
            print(f"{RED}❌ Invalid content item format{RESET}")
            return False
        
        # Extract and print content
        content = content_item["text"]
        print(f"{GREEN}✅ Anthropic API test passed!{RESET}")
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
    success = test_anthropic_api()
    sys.exit(0 if success else 1)

