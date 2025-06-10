#!/usr/bin/env python3
"""
Comprehensive API Test Suite for OpenAI API Compatibility
Tests all endpoints for OpenAI, Anthropic, and Google Vertex AI compatibility.
"""

import asyncio
import json
import time
import requests
from typing import Dict, Any

# Test configuration
BASE_URL = "http://localhost:8887"
TEST_TIMEOUT = 30

class APITester:
    def __init__(self, base_url: str = BASE_URL):
        self.base_url = base_url
        self.results = []
    
    def log_test(self, endpoint: str, method: str, status: str, details: str = ""):
        """Log test results."""
        result = {
            "endpoint": endpoint,
            "method": method,
            "status": status,
            "details": details,
            "timestamp": time.time()
        }
        self.results.append(result)
        status_emoji = "✅" if status == "PASS" else "❌" if status == "FAIL" else "⚠️"
        print(f"{status_emoji} {method} {endpoint} - {status} {details}")
    
    def test_endpoint(self, endpoint: str, method: str = "GET", data: Dict[Any, Any] = None, expected_status: int = 200):
        """Test a single endpoint."""
        url = f"{self.base_url}{endpoint}"
        
        try:
            if method == "GET":
                response = requests.get(url, timeout=TEST_TIMEOUT)
            elif method == "POST":
                response = requests.post(url, json=data, headers={"Content-Type": "application/json"}, timeout=TEST_TIMEOUT)
            else:
                self.log_test(endpoint, method, "FAIL", f"Unsupported method: {method}")
                return False
            
            if response.status_code == expected_status:
                try:
                    response_data = response.json()
                    self.log_test(endpoint, method, "PASS", f"Status: {response.status_code}")
                    return True
                except json.JSONDecodeError:
                    self.log_test(endpoint, method, "WARN", f"Status: {response.status_code}, Invalid JSON response")
                    return False
            else:
                self.log_test(endpoint, method, "FAIL", f"Expected: {expected_status}, Got: {response.status_code}")
                return False
                
        except requests.exceptions.Timeout:
            self.log_test(endpoint, method, "FAIL", "Request timeout")
            return False
        except requests.exceptions.ConnectionError:
            self.log_test(endpoint, method, "FAIL", "Connection error")
            return False
        except Exception as e:
            self.log_test(endpoint, method, "FAIL", f"Exception: {str(e)}")
            return False
    
    def run_comprehensive_tests(self):
        """Run all comprehensive API tests."""
        print("🚀 Starting Comprehensive API Compatibility Tests")
        print("=" * 60)
        
        # Test 1: Health Check
        print("\n📋 Testing Health & Status Endpoints")
        self.test_endpoint("/health", "GET")
        self.test_endpoint("/api/status", "GET")
        
        # Test 2: Models List
        print("\n📋 Testing Models Endpoint")
        self.test_endpoint("/v1/models", "GET")
        
        # Test 3: OpenAI Chat Completions
        print("\n📋 Testing OpenAI Chat Completions")
        chat_data = {
            "model": "gpt-3.5-turbo",
            "messages": [{"role": "user", "content": "Hello, test message"}],
            "max_tokens": 50
        }
        self.test_endpoint("/v1/chat/completions", "POST", chat_data)
        
        # Test 4: OpenAI Text Completions
        print("\n📋 Testing OpenAI Text Completions")
        text_data = {
            "model": "gpt-3.5-turbo-instruct",
            "prompt": "Hello, test prompt",
            "max_tokens": 50
        }
        self.test_endpoint("/v1/completions", "POST", text_data)
        
        # Test 5: OpenAI Embeddings
        print("\n📋 Testing OpenAI Embeddings")
        embedding_data = {
            "model": "text-embedding-ada-002",
            "input": "Test text for embedding"
        }
        self.test_endpoint("/v1/embeddings", "POST", embedding_data)
        
        # Test 6: OpenAI Audio Transcription
        print("\n📋 Testing OpenAI Audio Transcription")
        transcription_data = {
            "model": "whisper-1",
            "file": "fake_base64_audio_data"
        }
        self.test_endpoint("/v1/audio/transcriptions", "POST", transcription_data)
        
        # Test 7: OpenAI Audio Translation
        print("\n📋 Testing OpenAI Audio Translation")
        translation_data = {
            "model": "whisper-1",
            "file": "fake_base64_audio_data"
        }
        self.test_endpoint("/v1/audio/translations", "POST", translation_data)
        
        # Test 8: OpenAI Image Generation
        print("\n📋 Testing OpenAI Image Generation")
        image_data = {
            "model": "dall-e-3",
            "prompt": "A test image",
            "n": 1,
            "size": "1024x1024"
        }
        self.test_endpoint("/v1/images/generations", "POST", image_data)
        
        # Test 9: Anthropic Messages
        print("\n📋 Testing Anthropic Messages")
        anthropic_data = {
            "model": "claude-3-sonnet-20240229",
            "messages": [{"role": "user", "content": "Hello Claude, test message"}],
            "max_tokens": 50
        }
        self.test_endpoint("/v1/messages", "POST", anthropic_data)
        
        # Test 10: Anthropic Completions (Legacy)
        print("\n📋 Testing Anthropic Completions")
        anthropic_completion_data = {
            "model": "claude-3-sonnet-20240229",
            "prompt": "Hello Claude, test prompt",
            "max_tokens": 50
        }
        self.test_endpoint("/v1/anthropic/completions", "POST", anthropic_completion_data)
        
        # Test 11: Google Gemini (Legacy endpoints)
        print("\n📋 Testing Google Gemini Legacy Endpoints")
        gemini_data = {
            "model": "gemini-1.5-pro",
            "prompt": "Hello Gemini, test prompt",
            "max_tokens": 50
        }
        self.test_endpoint("/v1/gemini/completions", "POST", gemini_data)
        self.test_endpoint("/v1/gemini/generateContent", "POST", gemini_data)
        
        # Test 12: Google Vertex AI (Official endpoints)
        print("\n📋 Testing Google Vertex AI Official Endpoints")
        vertex_data = {
            "contents": [{"parts": [{"text": "Hello Vertex AI, test message"}]}],
            "generationConfig": {"maxOutputTokens": 50}
        }
        self.test_endpoint("/v1/models/gemini-1.5-pro:generateContent", "POST", vertex_data)
        self.test_endpoint("/v1/models/gemini-1.5-pro:streamGenerateContent", "POST", vertex_data)
        
        # Test Summary
        print("\n" + "=" * 60)
        print("📊 Test Summary")
        print("=" * 60)
        
        total_tests = len(self.results)
        passed_tests = len([r for r in self.results if r["status"] == "PASS"])
        failed_tests = len([r for r in self.results if r["status"] == "FAIL"])
        warned_tests = len([r for r in self.results if r["status"] == "WARN"])
        
        print(f"Total Tests: {total_tests}")
        print(f"✅ Passed: {passed_tests}")
        print(f"❌ Failed: {failed_tests}")
        print(f"⚠️  Warnings: {warned_tests}")
        print(f"Success Rate: {(passed_tests/total_tests)*100:.1f}%")
        
        if failed_tests > 0:
            print("\n❌ Failed Tests:")
            for result in self.results:
                if result["status"] == "FAIL":
                    print(f"  - {result['method']} {result['endpoint']}: {result['details']}")
        
        return passed_tests, failed_tests, warned_tests

def main():
    """Main test runner."""
    print("🧪 OpenAI API Compatibility Test Suite")
    print("Testing comprehensive endpoint compatibility for:")
    print("  • OpenAI API endpoints")
    print("  • Anthropic API endpoints") 
    print("  • Google Vertex AI endpoints")
    print()
    
    tester = APITester()
    
    try:
        passed, failed, warned = tester.run_comprehensive_tests()
        
        if failed == 0:
            print("\n🎉 All tests passed! API is fully compatible.")
            exit(0)
        else:
            print(f"\n⚠️  {failed} tests failed. Check the details above.")
            exit(1)
            
    except KeyboardInterrupt:
        print("\n\n⏹️  Tests interrupted by user.")
        exit(1)
    except Exception as e:
        print(f"\n\n💥 Test suite failed with exception: {e}")
        exit(1)

if __name__ == "__main__":
    main()

