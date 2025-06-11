#!/usr/bin/env python3
"""
Run all API tests in sequence
"""

import os
import subprocess
import sys

def run_test(test_file):
    """Run a single test file and return success status"""
    print(f"\n{'='*50}")
    print(f"Running {test_file}...")
    print(f"{'='*50}\n")
    
    result = subprocess.run([sys.executable, test_file], capture_output=False)
    return result.returncode == 0

def main():
    """Run all tests"""
    tests = [
        "test_openai_api.py",
        "test_anthropic_api.py",
        "test_google_api.py"
    ]
    
    success_count = 0
    failure_count = 0
    
    for test in tests:
        if run_test(test):
            success_count += 1
        else:
            failure_count += 1
    
    print(f"\n{'='*50}")
    print(f"Test Results: {success_count} passed, {failure_count} failed")
    print(f"{'='*50}\n")
    
    return 0 if failure_count == 0 else 1

if __name__ == "__main__":
    sys.exit(main())

