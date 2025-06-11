#!/usr/bin/env python3
"""
Run all API tests for the unified API system.
"""

import os
import sys
import subprocess
import time

# Define colors for terminal output
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
RESET = "\033[0m"

# Define test files
TEST_FILES = [
    "test_openai_api.py",
    "test_anthropic_api.py",
    "test_google_api.py"
]

def run_test(test_file):
    """Run a single test file and return success status."""
    print(f"{YELLOW}Running {test_file}...{RESET}")
    try:
        result = subprocess.run(
            [sys.executable, test_file],
            capture_output=True,
            text=True,
            timeout=30
        )
        
        # Print the output
        print(result.stdout)
        if result.stderr:
            print(f"{RED}Errors:{RESET}\n{result.stderr}")
        
        if result.returncode == 0:
            print(f"{GREEN}✅ {test_file} passed!{RESET}")
            return True
        else:
            print(f"{RED}❌ {test_file} failed with exit code {result.returncode}{RESET}")
            return False
    except subprocess.TimeoutExpired:
        print(f"{RED}❌ {test_file} timed out after 30 seconds{RESET}")
        return False
    except Exception as e:
        print(f"{RED}❌ {test_file} failed with exception: {e}{RESET}")
        return False


def main():
    """Run all tests."""
    print(f"{YELLOW}🧪 Running all API tests...{RESET}")
    
    # Check if server is running
    try:
        import requests
        response = requests.get("http://localhost:8887/health", timeout=5)
        if response.status_code != 200 or response.json().get("status") != "healthy":
            print(f"{RED}❌ Server is not healthy. Please start the server first.{RESET}")
            print(f"{YELLOW}Run ./start_server.sh to start the server.{RESET}")
            return 1
    except Exception as e:
        print(f"{RED}❌ Server is not running or not accessible: {e}{RESET}")
        print(f"{YELLOW}Run ./start_server.sh to start the server.{RESET}")
        return 1
    
    # Run all tests
    results = []
    for test_file in TEST_FILES:
        success = run_test(test_file)
        results.append((test_file, success))
    
    # Print summary
    print("\n" + "=" * 50)
    print(f"{YELLOW}📊 Test Summary:{RESET}")
    passed = sum(1 for _, success in results if success)
    total = len(results)
    
    for test_file, success in results:
        status = f"{GREEN}✅ PASSED{RESET}" if success else f"{RED}❌ FAILED{RESET}"
        print(f"{test_file}: {status}")
    
    print("-" * 50)
    print(f"Passed: {passed}/{total} tests")
    
    if passed == total:
        print(f"{GREEN}🎉 All tests passed!{RESET}")
        return 0
    else:
        print(f"{RED}❌ Some tests failed.{RESET}")
        return 1


if __name__ == "__main__":
    sys.exit(main())

