#!/usr/bin/env python3
"""
Unified test module for API endpoints.
"""

import json
import requests
import sys
import subprocess
import time
import argparse
import os

# ANSI color codes for output formatting
YELLOW = "\033[93m"
GREEN = "\033[92m"
RED = "\033[91m"
RESET = "\033[0m"

# API endpoints
OPENAI_URL = "http://localhost:8887/v1/chat/completions"
ANTHROPIC_URL = "http://localhost:8887/v1/anthropic/completions"
GOOGLE_URL = "http://localhost:8887/v1/gemini/completions"

# Test message
TEST_MESSAGE = "Hello, this is a test message."


def check_server_health():
    """Check if the server is running and healthy."""
    try:
        response = requests.get("http://localhost:8887/health")
        data = response.json()
        return data.get("status") == "healthy"
    except:
        return False


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
    print(f"{YELLOW}📤 Sending message to {OPENAI_URL}...{RESET}")
    try:
        response = requests.post(OPENAI_URL, json=payload)
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
        
        # Check if this is a simulated response
        content = ""
        if "choices" in data and len(data["choices"]) > 0:
            # OpenAI format
            choice = data["choices"][0]
            if "message" in choice and "content" in choice["message"]:
                content = choice["message"]["content"]
                
                # Check if this is a simulated response
                if content.startswith("This is a simulated response"):
                    print(f"{YELLOW}⚠️ Warning: Received simulated response. API key may not be set.{RESET}")
                    print(f"{YELLOW}⚠️ Set OPENAI_API_KEY environment variable for real API responses.{RESET}")
        
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
    print(f"{YELLOW}📤 Sending message to {ANTHROPIC_URL}...{RESET}")
    try:
        response = requests.post(ANTHROPIC_URL, json=payload)
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
        
        # Check if this is a simulated response
        content = ""
        if "content" in data and isinstance(data["content"], list) and len(data["content"]) > 0:
            # Anthropic format
            content_item = data["content"][0]
            if "text" in content_item:
                content = content_item["text"]
                
                # Check if this is a simulated response
                if content.startswith("This is a simulated Anthropic response"):
                    print(f"{YELLOW}⚠️ Warning: Received simulated response. API key may not be set.{RESET}")
                    print(f"{YELLOW}⚠️ Set ANTHROPIC_API_KEY environment variable for real API responses.{RESET}")
        
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
    print(f"{YELLOW}📤 Sending message to {GOOGLE_URL}...{RESET}")
    try:
        response = requests.post(GOOGLE_URL, json=payload)
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
        
        # Check if this is a simulated response
        content = ""
        if "candidates" in data and len(data["candidates"]) > 0:
            # Google format
            candidate = data["candidates"][0]
            if "content" in candidate and "parts" in candidate["content"] and len(candidate["content"]["parts"]) > 0:
                part = candidate["content"]["parts"][0]
                if "text" in part:
                    content = part["text"]
                    
                    # Check if this is a simulated response
                    if content.startswith("This is a simulated Gemini response"):
                        print(f"{YELLOW}⚠️ Warning: Received simulated response. API key may not be set.{RESET}")
                        print(f"{YELLOW}⚠️ Set GOOGLE_API_KEY environment variable for real API responses.{RESET}")
        
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


def run_tests():
    """Run all API tests and report results."""
    print(f"{YELLOW}🧪 Running all API tests...{RESET}")
    
    # Check if server is running
    if not check_server_health():
        print(f"{RED}❌ Server is not running or not healthy!{RESET}")
        print(f"Please start the server with: ./start_server.sh")
        return False
    
    results = {}
    
    # Run each test
    tests = [
        ("test_openai_api.py", test_openai_api),
        ("test_anthropic_api.py", test_anthropic_api),
        ("test_google_api.py", test_google_api)
    ]
    
    for test_name, test_func in tests:
        print(f"{YELLOW}Running {test_name}...{RESET}")
        
        # Run the test
        result = test_func()
        
        # Store result
        results[test_name] = result
        
        # Add a newline for separation
        print()
    
    # Print summary
    print("=" * 50)
    print(f"{YELLOW}📊 Test Summary:{RESET}")
    
    all_passed = True
    for test_name, passed in results.items():
        status = f"{GREEN}✅ PASSED{RESET}" if passed else f"{RED}❌ FAILED{RESET}"
        print(f"{test_name}: {status}")
        all_passed = all_passed and passed
    
    print("-" * 50)
    print(f"Passed: {sum(results.values())}/{len(results)} tests")
    
    if all_passed:
        print(f"{GREEN}🎉 All tests passed!{RESET}")
    else:
        print(f"{RED}❌ Some tests failed!{RESET}")
    
    return all_passed


def main():
    """Main function."""
    parser = argparse.ArgumentParser(description="Test API endpoints")
    parser.add_argument("--openai", action="store_true", help="Test only OpenAI API")
    parser.add_argument("--anthropic", action="store_true", help="Test only Anthropic API")
    parser.add_argument("--google", action="store_true", help="Test only Google/Gemini API")
    parser.add_argument("--all", action="store_true", help="Test all APIs (default)")
    
    args = parser.parse_args()
    
    # If no specific test is requested, run all tests
    if not (args.openai or args.anthropic or args.google or args.all):
        args.all = True
    
    # Check if server is running
    if not check_server_health():
        print(f"{RED}❌ Server is not running or not healthy!{RESET}")
        print(f"Please start the server with: ./start_server.sh")
        return 1
    
    success = True
    
    # Run requested tests
    if args.openai or args.all:
        success = test_openai_api() and success
    
    if args.anthropic or args.all:
        success = test_anthropic_api() and success
    
    if args.google or args.all:
        success = test_google_api() and success
    
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())

