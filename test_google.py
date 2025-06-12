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
    
    # Check if server is running
    try:
        health_url = BASE_URL.rsplit("/", 1)[0] + "/health"
        health_response = requests.get(health_url)
        if health_response.status_code == 200:
            health_data = health_response.json()
            print(f"{GREEN}✅ Server is healthy{RESET}")
            if "routing_to" in health_data:
                print(f"{YELLOW}ℹ️ Routing to: {health_data['routing_to']}{RESET}")
            if "codegen_available" in health_data and not health_data["codegen_available"]:
                print(f"{YELLOW}⚠️ Warning: Codegen SDK is not available. Mock responses are {'enabled' if health_data.get('mock_responses_enabled', False) else 'disabled'}.{RESET}")
        else:
            print(f"{RED}❌ Server health check failed: {health_response.status_code}{RESET}")
    except requests.RequestException as e:
        print(f"{RED}❌ Server health check failed: {e}{RESET}")
    
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
        response = requests.post(API_URL, json=payload, timeout=10)
        
        # Check response status
        if response.status_code != 200:
            print(f"{RED}❌ Request failed with status code {response.status_code}{RESET}")
            print(f"{RED}Error: {response.text}{RESET}")
            return False
        
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

