#!/usr/bin/env python3
"""
Simple test runner for the unified API system
Runs all 3 API tests: OpenAI, Anthropic, and Google
"""

import subprocess
import sys

def run_test(test_file, test_name):
    """Run a single test file"""
    print(f"\n{'='*50}")
    print(f"🚀 Running {test_name} Test")
    print(f"{'='*50}")
    
    try:
        result = subprocess.run([sys.executable, test_file], 
                              capture_output=True, text=True, timeout=120)
        
        print(result.stdout)
        if result.stderr:
            print(f"⚠️ Warnings: {result.stderr}")
            
        if result.returncode == 0:
            print(f"✅ {test_name} Test PASSED")
            return True
        else:
            print(f"❌ {test_name} Test FAILED (exit code: {result.returncode})")
            return False
            
    except subprocess.TimeoutExpired:
        print(f"⏰ {test_name} Test TIMED OUT")
        return False
    except Exception as e:
        print(f"💥 {test_name} Test ERROR: {e}")
        return False

def main():
    """Run all API tests"""
    print("🧪 Starting Unified API System Tests")
    print("Testing all 3 providers: OpenAI, Anthropic, Google")
    
    tests = [
        ("test_openai_api.py", "OpenAI"),
        ("test_anthropic_api.py", "Anthropic"), 
        ("test_google_api.py", "Google")
    ]
    
    results = []
    for test_file, test_name in tests:
        success = run_test(test_file, test_name)
        results.append((test_name, success))
    
    # Summary
    print(f"\n{'='*50}")
    print("📊 TEST SUMMARY")
    print(f"{'='*50}")
    
    passed = sum(1 for _, success in results if success)
    total = len(results)
    
    for test_name, success in results:
        status = "✅ PASSED" if success else "❌ FAILED"
        print(f"{test_name:12} {status}")
    
    print(f"\nTotal: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Unified API system is working correctly.")
        return 0
    else:
        print("⚠️ Some tests failed. Check the output above for details.")
        return 1

if __name__ == "__main__":
    exit(main())

