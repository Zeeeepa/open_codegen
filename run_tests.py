#!/usr/bin/env python3
"""
Run all API tests and report results.
"""

import os
import sys
import subprocess
import requests
import time

# ANSI color codes for output formatting
YELLOW = "\033[93m"
GREEN = "\033[92m"
RED = "\033[91m"
RESET = "\033[0m"

# Test files to run
TEST_FILES = [
    "test_openai_api.py",
    "test_anthropic_api.py",
    "test_google_api.py"
]

def check_server_health():
    """Check if the server is running and healthy."""
    try:
        response = requests.get("http://localhost:8887/health")
        data = response.json()
        return data.get("status") == "healthy"
    except:
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
    
    # Run each test file
    for test_file in TEST_FILES:
        print(f"{YELLOW}Running {test_file}...{RESET}")
        
        # Run the test script
        result = subprocess.run(["python", test_file], capture_output=True, text=True)
        
        # Print output
        print(result.stdout)
        
        # Store result
        results[test_file] = result.returncode == 0
        
        # Add a newline for separation
        print()
    
    # Print summary
    print("=" * 50)
    print(f"{YELLOW}📊 Test Summary:{RESET}")
    
    all_passed = True
    for test_file, passed in results.items():
        status = f"{GREEN}✅ PASSED{RESET}" if passed else f"{RED}❌ FAILED{RESET}"
        print(f"{test_file}: {status}")
        all_passed = all_passed and passed
    
    print("-" * 50)
    print(f"Passed: {sum(results.values())}/{len(results)} tests")
    
    if all_passed:
        print(f"{GREEN}🎉 All tests passed!{RESET}")
    else:
        print(f"{RED}❌ Some tests failed!{RESET}")
    
    return all_passed

if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)

