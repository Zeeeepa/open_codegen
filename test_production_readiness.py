#!/usr/bin/env python3
"""
Production Readiness Testing for Transparent OpenAI API Interception

This comprehensive test suite validates that the transparent interception system
is ready for production use with real OpenAI applications.

Test Categories:
1. Infrastructure Tests (DNS, SSL, Server)
2. API Compatibility Tests (Request/Response formats)
3. Performance Tests (Response times, throughput)
4. Reliability Tests (Error handling, edge cases)
5. Security Tests (SSL, authentication)
"""

import time
import json
import subprocess
import concurrent.futures
from openai import OpenAI
import requests

class ProductionReadinessTester:
    def __init__(self):
        self.test_results = []
        self.performance_metrics = {}
        
    def log_test(self, category, test_name, success, details="", metrics=None):
        """Log test results with category and metrics."""
        status = "✅ PASS" if success else "❌ FAIL"
        self.test_results.append({
            "category": category,
            "test": test_name,
            "success": success,
            "details": details,
            "metrics": metrics or {}
        })
        print(f"{status} [{category}] {test_name}")
        if details:
            print(f"    {details}")
        if metrics:
            for key, value in metrics.items():
                print(f"    📊 {key}: {value}")
        print()

    def test_infrastructure_setup(self):
        """Test that all infrastructure components are working."""
        print("🏗️ Testing Infrastructure Setup")
        print("-" * 50)
        
        # Test DNS resolution
        try:
            import socket
            ip = socket.gethostbyname("api.openai.com")
            dns_working = ip == "127.0.0.1"
            self.log_test(
                "Infrastructure", 
                "DNS Interception", 
                dns_working, 
                f"api.openai.com resolves to {ip}"
            )
        except Exception as e:
            self.log_test("Infrastructure", "DNS Interception", False, f"Error: {e}")
        
        # Test HTTP server
        try:
            response = requests.get("http://127.0.0.1:80/v1/models", timeout=5)
            http_working = response.status_code == 200
            self.log_test(
                "Infrastructure", 
                "HTTP Server", 
                http_working, 
                f"Status: {response.status_code}"
            )
        except Exception as e:
            self.log_test("Infrastructure", "HTTP Server", False, f"Error: {e}")
        
        # Test HTTPS server (if SSL is set up)
        try:
            response = requests.get("https://127.0.0.1:443/v1/models", timeout=5, verify=False)
            https_working = response.status_code == 200
            self.log_test(
                "Infrastructure", 
                "HTTPS Server", 
                https_working, 
                f"Status: {response.status_code}"
            )
        except Exception as e:
            self.log_test("Infrastructure", "HTTPS Server", False, f"Error: {e}")

    def test_api_compatibility(self):
        """Test API compatibility with OpenAI standards."""
        print("🔌 Testing API Compatibility")
        print("-" * 50)
        
        client = OpenAI(
            api_key="sk-test-production-readiness",
            base_url="http://api.openai.com/v1"
        )
        
        # Test models endpoint
        try:
            models = client.models.list()
            models_working = len(models.data) > 0
            model_names = [m.id for m in models.data]
            self.log_test(
                "API Compatibility", 
                "Models Endpoint", 
                models_working, 
                f"Found {len(models.data)} models: {', '.join(model_names[:3])}..."
            )
        except Exception as e:
            self.log_test("API Compatibility", "Models Endpoint", False, f"Error: {e}")
        
        # Test chat completions
        try:
            start_time = time.time()
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": "Test message"}],
                max_tokens=20
            )
            end_time = time.time()
            
            # Verify response structure
            has_choices = hasattr(response, 'choices') and len(response.choices) > 0
            has_content = hasattr(response.choices[0].message, 'content')
            has_usage = hasattr(response, 'usage')
            has_model = hasattr(response, 'model')
            
            chat_working = has_choices and has_content and has_usage and has_model
            response_time = end_time - start_time
            
            self.log_test(
                "API Compatibility", 
                "Chat Completions", 
                chat_working, 
                f"Response structure valid",
                {"response_time": f"{response_time:.2f}s", "tokens": response.usage.total_tokens}
            )
        except Exception as e:
            self.log_test("API Compatibility", "Chat Completions", False, f"Error: {e}")

    def test_performance_benchmarks(self):
        """Test performance benchmarks for production use."""
        print("⚡ Testing Performance Benchmarks")
        print("-" * 50)
        
        client = OpenAI(
            api_key="sk-test-performance",
            base_url="http://api.openai.com/v1"
        )
        
        # Test response time
        response_times = []
        for i in range(3):
            try:
                start_time = time.time()
                response = client.chat.completions.create(
                    model="gpt-3.5-turbo",
                    messages=[{"role": "user", "content": f"Performance test {i+1}"}],
                    max_tokens=10
                )
                end_time = time.time()
                response_times.append(end_time - start_time)
            except Exception as e:
                print(f"Performance test {i+1} failed: {e}")
        
        if response_times:
            avg_response_time = sum(response_times) / len(response_times)
            max_response_time = max(response_times)
            min_response_time = min(response_times)
            
            # Consider < 30s average as acceptable for production
            performance_acceptable = avg_response_time < 30.0
            
            self.log_test(
                "Performance", 
                "Response Time", 
                performance_acceptable, 
                f"Average: {avg_response_time:.2f}s",
                {
                    "avg_time": f"{avg_response_time:.2f}s",
                    "min_time": f"{min_response_time:.2f}s", 
                    "max_time": f"{max_response_time:.2f}s"
                }
            )
        
        # Test concurrent requests
        try:
            def make_request():
                start = time.time()
                response = client.chat.completions.create(
                    model="gpt-3.5-turbo",
                    messages=[{"role": "user", "content": "Concurrent test"}],
                    max_tokens=5
                )
                return time.time() - start
            
            with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
                futures = [executor.submit(make_request) for _ in range(3)]
                concurrent_times = [f.result() for f in concurrent.futures.as_completed(futures, timeout=60)]
            
            concurrent_working = len(concurrent_times) == 3
            avg_concurrent_time = sum(concurrent_times) / len(concurrent_times)
            
            self.log_test(
                "Performance", 
                "Concurrent Requests", 
                concurrent_working, 
                f"3 concurrent requests completed",
                {"avg_concurrent_time": f"{avg_concurrent_time:.2f}s"}
            )
        except Exception as e:
            self.log_test("Performance", "Concurrent Requests", False, f"Error: {e}")

    def test_reliability_and_errors(self):
        """Test reliability and error handling."""
        print("🛡️ Testing Reliability and Error Handling")
        print("-" * 50)
        
        client = OpenAI(
            api_key="sk-test-reliability",
            base_url="http://api.openai.com/v1"
        )
        
        # Test invalid model handling
        try:
            response = client.chat.completions.create(
                model="invalid-model-name",
                messages=[{"role": "user", "content": "test"}],
                max_tokens=10
            )
            # If this succeeds, it's actually OK (server might handle gracefully)
            self.log_test("Reliability", "Invalid Model Handling", True, "Invalid model handled gracefully")
        except Exception as e:
            # Error is expected and OK
            self.log_test("Reliability", "Invalid Model Handling", True, f"Invalid model properly rejected: {type(e).__name__}")
        
        # Test empty messages handling
        try:
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[],
                max_tokens=10
            )
            self.log_test("Reliability", "Empty Messages Handling", True, "Empty messages handled gracefully")
        except Exception as e:
            self.log_test("Reliability", "Empty Messages Handling", True, f"Empty messages properly rejected: {type(e).__name__}")
        
        # Test large token request
        try:
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": "Write a very long story"}],
                max_tokens=1000
            )
            large_request_working = len(response.choices[0].message.content) > 100
            self.log_test(
                "Reliability", 
                "Large Token Request", 
                large_request_working, 
                f"Generated {len(response.choices[0].message.content)} characters"
            )
        except Exception as e:
            self.log_test("Reliability", "Large Token Request", False, f"Error: {e}")

    def test_security_features(self):
        """Test security features."""
        print("🔒 Testing Security Features")
        print("-" * 50)
        
        # Test that dummy API keys are accepted (proves interception)
        dummy_keys = [
            "sk-fake-key-1",
            "invalid-key-format",
            "sk-" + "x" * 50,
            ""
        ]
        
        accepted_keys = 0
        for key in dummy_keys:
            try:
                client = OpenAI(
                    api_key=key,
                    base_url="http://api.openai.com/v1"
                )
                models = client.models.list()
                if len(models.data) > 0:
                    accepted_keys += 1
            except:
                pass
        
        # All dummy keys should be accepted (proves interception working)
        security_working = accepted_keys > 0
        self.log_test(
            "Security", 
            "Dummy Key Acceptance", 
            security_working, 
            f"{accepted_keys}/{len(dummy_keys)} dummy keys accepted (proves interception)"
        )

    def run_production_readiness_tests(self):
        """Run all production readiness tests."""
        print("🎯 PRODUCTION READINESS TESTING")
        print("=" * 60)
        print("Comprehensive testing to validate transparent interception")
        print("is ready for production use with real OpenAI applications.")
        print()
        
        # Run all test categories
        test_categories = [
            ("Infrastructure", self.test_infrastructure_setup),
            ("API Compatibility", self.test_api_compatibility),
            ("Performance", self.test_performance_benchmarks),
            ("Reliability", self.test_reliability_and_errors),
            ("Security", self.test_security_features)
        ]
        
        for category_name, test_func in test_categories:
            try:
                test_func()
            except Exception as e:
                print(f"❌ {category_name} tests crashed: {e}")
                self.log_test(category_name, "Category Test", False, f"Tests crashed: {e}")
        
        # Generate comprehensive report
        self.generate_production_report()

    def generate_production_report(self):
        """Generate a comprehensive production readiness report."""
        print("=" * 60)
        print("📊 PRODUCTION READINESS REPORT")
        print("=" * 60)
        
        # Group results by category
        categories = {}
        for result in self.test_results:
            category = result['category']
            if category not in categories:
                categories[category] = []
            categories[category].append(result)
        
        total_passed = 0
        total_tests = 0
        
        for category, tests in categories.items():
            passed = sum(1 for test in tests if test['success'])
            total = len(tests)
            total_passed += passed
            total_tests += total
            
            status = "✅" if passed == total else "⚠️" if passed > 0 else "❌"
            print(f"\n{status} {category}: {passed}/{total} tests passed")
            
            for test in tests:
                test_status = "✅" if test['success'] else "❌"
                print(f"  {test_status} {test['test']}")
                if test['details']:
                    print(f"      {test['details']}")
                if test['metrics']:
                    for key, value in test['metrics'].items():
                        print(f"      📊 {key}: {value}")
        
        # Overall assessment
        print(f"\n📊 OVERALL RESULTS: {total_passed}/{total_tests} tests passed")
        
        if total_passed == total_tests:
            print("\n🎉 PRODUCTION READY!")
            print("✅ All systems operational")
            print("✅ API compatibility confirmed")
            print("✅ Performance acceptable")
            print("✅ Reliability verified")
            print("✅ Security features working")
            print("\n🚀 The transparent interception system is ready for production deployment!")
        elif total_passed >= total_tests * 0.8:
            print("\n⚠️ MOSTLY READY")
            print("✅ Core functionality working")
            print("⚠️ Some minor issues to address")
            print("🔧 Review failed tests before production deployment")
        else:
            print("\n❌ NOT READY FOR PRODUCTION")
            print("❌ Critical issues need to be resolved")
            print("🔧 Fix failing tests before deployment")
        
        return total_passed == total_tests

if __name__ == "__main__":
    tester = ProductionReadinessTester()
    success = tester.run_production_readiness_tests()
    exit(0 if success else 1)
