#!/usr/bin/env python3
"""
Comprehensive test script for all OpenAI Codegen Adapter endpoints.
Tests OpenAI, Anthropic, Google Gemini APIs, and health endpoints.
"""

import requests
import json
import time
from typing import Dict, Any, List


class AdapterTester:
    """Test runner for all adapter endpoints."""
    
    def __init__(self, base_url: str = "http://localhost:8887"):
        self.base_url = base_url
        self.results = []
    
    def log_test(self, test_name: str, success: bool, details: str = ""):
        """Log test result."""
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {test_name}")
        if details:
            print(f"   📝 {details}")
        
        self.results.append({
            "test": test_name,
            "success": success,
            "details": details,
            "timestamp": time.time()
        })
    
    def test_health_endpoints(self):
        """Test all health check endpoints."""
        print("\n🏥 Testing Health Endpoints")
        print("=" * 50)
        
        # Basic health check
        try:
            response = requests.get(f"{self.base_url}/health")
            success = response.status_code == 200 and "healthy" in response.text
            self.log_test("Basic Health Check", success, f"Status: {response.status_code}")
        except Exception as e:
            self.log_test("Basic Health Check", False, str(e))
        
        # Detailed health check
        try:
            response = requests.get(f"{self.base_url}/health/detailed")
            success = response.status_code == 200
            if success:
                data = response.json()
                details = f"Status: {data.get('status', 'unknown')}, Uptime: {data.get('uptime_minutes', 0):.1f}m"
            else:
                details = f"Status: {response.status_code}"
            self.log_test("Detailed Health Check", success, details)
        except Exception as e:
            self.log_test("Detailed Health Check", False, str(e))
        
        # Metrics endpoint
        try:
            response = requests.get(f"{self.base_url}/health/metrics")
            success = response.status_code == 200
            if success:
                data = response.json()
                total_requests = data.get('summary', {}).get('all_time', {}).get('total_requests', 0)
                details = f"Total requests tracked: {total_requests}"
            else:
                details = f"Status: {response.status_code}"
            self.log_test("Metrics Endpoint", success, details)
        except Exception as e:
            self.log_test("Metrics Endpoint", False, str(e))
        
        # Readiness check
        try:
            response = requests.get(f"{self.base_url}/health/readiness")
            success = response.status_code == 200
            if success:
                data = response.json()
                details = f"Status: {data.get('status', 'unknown')}"
            else:
                details = f"Status: {response.status_code}"
            self.log_test("Readiness Check", success, details)
        except Exception as e:
            self.log_test("Readiness Check", False, str(e))
    
    def test_openai_endpoints(self):
        """Test OpenAI compatible endpoints."""
        print("\n🤖 Testing OpenAI Endpoints")
        print("=" * 50)
        
        # Models endpoint
        try:
            response = requests.get(f"{self.base_url}/v1/models")
            success = response.status_code == 200
            if success:
                data = response.json()
                model_count = len(data.get('data', []))
                details = f"Found {model_count} models"
            else:
                details = f"Status: {response.status_code}"
            self.log_test("OpenAI Models List", success, details)
        except Exception as e:
            self.log_test("OpenAI Models List", False, str(e))
        
        # Chat completions
        try:
            payload = {
                "model": "gpt-3.5-turbo",
                "messages": [{"role": "user", "content": "Hello, test message!"}],
                "max_tokens": 50
            }
            response = requests.post(
                f"{self.base_url}/v1/chat/completions",
                json=payload,
                headers={"Authorization": "Bearer dummy-key"}
            )
            success = response.status_code == 200
            if success:
                data = response.json()
                content = data.get('choices', [{}])[0].get('message', {}).get('content', '')
                details = f"Response length: {len(content)} chars"
            else:
                details = f"Status: {response.status_code}"
            self.log_test("OpenAI Chat Completions", success, details)
        except Exception as e:
            self.log_test("OpenAI Chat Completions", False, str(e))
        
        # Text completions
        try:
            payload = {
                "model": "gpt-3.5-turbo-instruct",
                "prompt": "Hello, test prompt!",
                "max_tokens": 50
            }
            response = requests.post(
                f"{self.base_url}/v1/completions",
                json=payload,
                headers={"Authorization": "Bearer dummy-key"}
            )
            success = response.status_code == 200
            if success:
                data = response.json()
                content = data.get('choices', [{}])[0].get('text', '')
                details = f"Response length: {len(content)} chars"
            else:
                details = f"Status: {response.status_code}"
            self.log_test("OpenAI Text Completions", success, details)
        except Exception as e:
            self.log_test("OpenAI Text Completions", False, str(e))
    
    def test_anthropic_endpoints(self):
        """Test Anthropic compatible endpoints."""
        print("\n🧠 Testing Anthropic Endpoints")
        print("=" * 50)
        
        # Messages endpoint
        try:
            payload = {
                "model": "claude-3-sonnet-20240229",
                "max_tokens": 50,
                "messages": [{"role": "user", "content": "Hello, test message!"}]
            }
            response = requests.post(
                f"{self.base_url}/v1/messages",
                json=payload,
                headers={"x-api-key": "dummy-key"}
            )
            success = response.status_code == 200
            if success:
                data = response.json()
                content = data.get('content', [{}])[0].get('text', '')
                details = f"Response length: {len(content)} chars"
            else:
                details = f"Status: {response.status_code}"
            self.log_test("Anthropic Messages", success, details)
        except Exception as e:
            self.log_test("Anthropic Messages", False, str(e))
        
        # Anthropic completions
        try:
            payload = {
                "model": "claude-3-sonnet-20240229",
                "max_tokens": 50,
                "messages": [{"role": "user", "content": "Hello, test message!"}]
            }
            response = requests.post(
                f"{self.base_url}/v1/anthropic/completions",
                json=payload,
                headers={"x-api-key": "dummy-key"}
            )
            success = response.status_code == 200
            if success:
                data = response.json()
                content = data.get('content', [{}])[0].get('text', '')
                details = f"Response length: {len(content)} chars"
            else:
                details = f"Status: {response.status_code}"
            self.log_test("Anthropic Completions", success, details)
        except Exception as e:
            self.log_test("Anthropic Completions", False, str(e))
    
    def test_gemini_endpoints(self):
        """Test Google Gemini compatible endpoints."""
        print("\n🔮 Testing Google Gemini Endpoints")
        print("=" * 50)
        
        # Gemini generateContent
        try:
            payload = {
                "contents": [
                    {
                        "role": "user",
                        "parts": [{"text": "Hello, test message!"}]
                    }
                ],
                "generationConfig": {
                    "maxOutputTokens": 50
                }
            }
            response = requests.post(
                f"{self.base_url}/v1/gemini/generateContent",
                json=payload
            )
            success = response.status_code == 200
            if success:
                data = response.json()
                content = data.get('candidates', [{}])[0].get('content', {}).get('parts', [{}])[0].get('text', '')
                details = f"Response length: {len(content)} chars"
            else:
                details = f"Status: {response.status_code}"
            self.log_test("Gemini Generate Content", success, details)
        except Exception as e:
            self.log_test("Gemini Generate Content", False, str(e))
        
        # Gemini completions
        try:
            payload = {
                "contents": [
                    {
                        "role": "user",
                        "parts": [{"text": "Hello, test message!"}]
                    }
                ],
                "generationConfig": {
                    "maxOutputTokens": 50
                }
            }
            response = requests.post(
                f"{self.base_url}/v1/gemini/completions",
                json=payload
            )
            success = response.status_code == 200
            if success:
                data = response.json()
                content = data.get('candidates', [{}])[0].get('content', {}).get('parts', [{}])[0].get('text', '')
                details = f"Response length: {len(content)} chars"
            else:
                details = f"Status: {response.status_code}"
            self.log_test("Gemini Completions", success, details)
        except Exception as e:
            self.log_test("Gemini Completions", False, str(e))
    
    def test_error_handling(self):
        """Test error handling."""
        print("\n🚨 Testing Error Handling")
        print("=" * 50)
        
        # Invalid endpoint
        try:
            response = requests.get(f"{self.base_url}/v1/invalid-endpoint")
            success = response.status_code == 404
            self.log_test("Invalid Endpoint (404)", success, f"Status: {response.status_code}")
        except Exception as e:
            self.log_test("Invalid Endpoint (404)", False, str(e))
        
        # Invalid JSON
        try:
            response = requests.post(
                f"{self.base_url}/v1/chat/completions",
                data="invalid json",
                headers={"Content-Type": "application/json"}
            )
            success = response.status_code in [400, 422]
            self.log_test("Invalid JSON (400/422)", success, f"Status: {response.status_code}")
        except Exception as e:
            self.log_test("Invalid JSON (400/422)", False, str(e))
    
    def run_all_tests(self):
        """Run all tests."""
        print("🧪 OpenAI Codegen Adapter - Comprehensive Test Suite")
        print("=" * 60)
        print(f"🎯 Target URL: {self.base_url}")
        print(f"⏰ Started at: {time.strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Run all test suites
        self.test_health_endpoints()
        self.test_openai_endpoints()
        self.test_anthropic_endpoints()
        self.test_gemini_endpoints()
        self.test_error_handling()
        
        # Print summary
        self.print_summary()
    
    def print_summary(self):
        """Print test summary."""
        print("\n📊 Test Summary")
        print("=" * 50)
        
        total_tests = len(self.results)
        passed_tests = sum(1 for r in self.results if r['success'])
        failed_tests = total_tests - passed_tests
        
        print(f"Total Tests: {total_tests}")
        print(f"✅ Passed: {passed_tests}")
        print(f"❌ Failed: {failed_tests}")
        print(f"📈 Success Rate: {(passed_tests/total_tests)*100:.1f}%")
        
        if failed_tests > 0:
            print("\n❌ Failed Tests:")
            for result in self.results:
                if not result['success']:
                    print(f"   • {result['test']}: {result['details']}")
        
        print(f"\n⏰ Completed at: {time.strftime('%Y-%m-%d %H:%M:%S')}")


def main():
    """Main test runner."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Test OpenAI Codegen Adapter endpoints")
    parser.add_argument(
        "--url", 
        default="http://localhost:8887",
        help="Base URL of the adapter server (default: http://localhost:8887)"
    )
    parser.add_argument(
        "--suite",
        choices=["all", "health", "openai", "anthropic", "gemini", "errors"],
        default="all",
        help="Test suite to run (default: all)"
    )
    
    args = parser.parse_args()
    
    tester = AdapterTester(args.url)
    
    if args.suite == "all":
        tester.run_all_tests()
    elif args.suite == "health":
        tester.test_health_endpoints()
        tester.print_summary()
    elif args.suite == "openai":
        tester.test_openai_endpoints()
        tester.print_summary()
    elif args.suite == "anthropic":
        tester.test_anthropic_endpoints()
        tester.print_summary()
    elif args.suite == "gemini":
        tester.test_gemini_endpoints()
        tester.print_summary()
    elif args.suite == "errors":
        tester.test_error_handling()
        tester.print_summary()


if __name__ == "__main__":
    main()

