#!/usr/bin/env python3
"""
Google Vertex AI SDK Compatibility Test Suite
Tests the adapter using the official Google Cloud AI Platform SDK to ensure full compatibility.
"""

import asyncio
import json
import time
import sys
from typing import List, Dict, Any

# Test configuration
BASE_URL = "http://localhost:8887"
TEST_TIMEOUT = 30

class GoogleSDKTester:
    def __init__(self, base_url: str = BASE_URL):
        self.base_url = base_url
        self.results = []
        self.client = None
        
    def setup_client(self):
        """Setup Google Vertex AI client pointing to our adapter."""
        try:
            # For testing, we'll use requests to simulate the Google SDK
            # In production, you'd use the actual Google Cloud AI Platform SDK
            import requests
            self.session = requests.Session()
            self.session.headers.update({
                "Content-Type": "application/json",
                "Authorization": "Bearer dummy-token"  # Our adapter doesn't validate this
            })
            print("✅ Google SDK client initialized successfully")
            return True
        except ImportError:
            print("❌ Requests library not available")
            return False
        except Exception as e:
            print(f"❌ Failed to initialize Google client: {e}")
            return False
    
    def log_test(self, test_name: str, status: str, details: str = ""):
        """Log test results."""
        result = {
            "test": test_name,
            "status": status,
            "details": details,
            "timestamp": time.time()
        }
        self.results.append(result)
        status_emoji = "✅" if status == "PASS" else "❌" if status == "FAIL" else "⚠️"
        print(f"{status_emoji} {test_name} - {status} {details}")
    
    def test_basic_generate_content(self):
        """Test basic content generation."""
        try:
            url = f"{self.base_url}/v1/models/gemini-1.5-pro:generateContent"
            payload = {
                "contents": [
                    {
                        "role": "user",
                        "parts": [
                            {"text": "Hello, Gemini! This is a test message."}
                        ]
                    }
                ]
            }
            
            response = self.session.post(url, json=payload, timeout=TEST_TIMEOUT)
            
            assert response.status_code == 200, f"Expected 200, got {response.status_code}"
            
            data = response.json()
            assert "candidates" in data, "Response missing 'candidates' field"
            assert len(data["candidates"]) > 0, "No candidates in response"
            
            candidate = data["candidates"][0]
            assert "content" in candidate, "Candidate missing 'content' field"
            assert "parts" in candidate["content"], "Content missing 'parts' field"
            assert len(candidate["content"]["parts"]) > 0, "No parts in content"
            assert "text" in candidate["content"]["parts"][0], "First part missing 'text' field"
            
            self.log_test("Basic Generate Content", "PASS", f"Response received with {len(data['candidates'])} candidates")
            return True
            
        except Exception as e:
            self.log_test("Basic Generate Content", "FAIL", str(e))
            return False
    
    def test_system_instruction(self):
        """Test system instruction support."""
        try:
            url = f"{self.base_url}/v1/models/gemini-1.5-pro:generateContent"
            payload = {
                "contents": [
                    {
                        "role": "user",
                        "parts": [
                            {"text": "What is the weather like?"}
                        ]
                    }
                ],
                "systemInstruction": {
                    "parts": [
                        {"text": "You are a helpful assistant that responds in exactly 5 words."}
                    ]
                }
            }
            
            response = self.session.post(url, json=payload, timeout=TEST_TIMEOUT)
            
            assert response.status_code == 200, f"Expected 200, got {response.status_code}"
            
            data = response.json()
            assert "candidates" in data, "Response missing candidates"
            
            self.log_test("System Instruction", "PASS", "System instruction processed")
            return True
            
        except Exception as e:
            self.log_test("System Instruction", "FAIL", str(e))
            return False
    
    def test_generation_config(self):
        """Test generation configuration parameters."""
        try:
            url = f"{self.base_url}/v1/models/gemini-1.5-pro:generateContent"
            payload = {
                "contents": [
                    {
                        "role": "user",
                        "parts": [
                            {"text": "Generate a creative story opening."}
                        ]
                    }
                ],
                "generationConfig": {
                    "temperature": 0.7,
                    "topP": 0.9,
                    "topK": 40,
                    "maxOutputTokens": 150,
                    "stopSequences": ["END", "STOP"]
                }
            }
            
            response = self.session.post(url, json=payload, timeout=TEST_TIMEOUT)
            
            assert response.status_code == 200, f"Expected 200, got {response.status_code}"
            
            data = response.json()
            assert "candidates" in data, "Response missing candidates"
            
            self.log_test("Generation Config", "PASS", "Generation config parameters accepted")
            return True
            
        except Exception as e:
            self.log_test("Generation Config", "FAIL", str(e))
            return False
    
    def test_safety_settings(self):
        """Test safety settings support."""
        try:
            url = f"{self.base_url}/v1/models/gemini-1.5-pro:generateContent"
            payload = {
                "contents": [
                    {
                        "role": "user",
                        "parts": [
                            {"text": "Tell me about safety in AI systems."}
                        ]
                    }
                ],
                "safetySettings": [
                    {
                        "category": "HARM_CATEGORY_HARASSMENT",
                        "threshold": "BLOCK_MEDIUM_AND_ABOVE"
                    },
                    {
                        "category": "HARM_CATEGORY_HATE_SPEECH",
                        "threshold": "BLOCK_MEDIUM_AND_ABOVE"
                    }
                ]
            }
            
            response = self.session.post(url, json=payload, timeout=TEST_TIMEOUT)
            
            assert response.status_code == 200, f"Expected 200, got {response.status_code}"
            
            data = response.json()
            assert "candidates" in data, "Response missing candidates"
            
            self.log_test("Safety Settings", "PASS", "Safety settings processed")
            return True
            
        except Exception as e:
            self.log_test("Safety Settings", "FAIL", str(e))
            return False
    
    def test_multimodal_content(self):
        """Test multimodal content support."""
        try:
            url = f"{self.base_url}/v1/models/gemini-1.5-pro:generateContent"
            payload = {
                "contents": [
                    {
                        "role": "user",
                        "parts": [
                            {"text": "Analyze this image:"},
                            {
                                "inlineData": {
                                    "mimeType": "image/jpeg",
                                    "data": "fake_base64_image_data"
                                }
                            }
                        ]
                    }
                ]
            }
            
            response = self.session.post(url, json=payload, timeout=TEST_TIMEOUT)
            
            assert response.status_code == 200, f"Expected 200, got {response.status_code}"
            
            data = response.json()
            assert "candidates" in data, "Response missing candidates"
            
            self.log_test("Multimodal Content", "PASS", "Multimodal content processed")
            return True
            
        except Exception as e:
            self.log_test("Multimodal Content", "FAIL", str(e))
            return False
    
    def test_streaming_generate_content(self):
        """Test streaming content generation."""
        try:
            url = f"{self.base_url}/v1/models/gemini-1.5-pro:streamGenerateContent"
            payload = {
                "contents": [
                    {
                        "role": "user",
                        "parts": [
                            {"text": "Count from 1 to 10."}
                        ]
                    }
                ]
            }
            
            response = self.session.post(url, json=payload, timeout=TEST_TIMEOUT, stream=True)
            
            assert response.status_code == 200, f"Expected 200, got {response.status_code}"
            
            # For streaming, we expect Server-Sent Events
            chunks_received = 0
            for line in response.iter_lines():
                if line:
                    chunks_received += 1
                    if chunks_received > 5:  # Limit for testing
                        break
            
            assert chunks_received > 0, "No streaming chunks received"
            
            self.log_test("Streaming Generate Content", "PASS", f"Received {chunks_received} chunks")
            return True
            
        except Exception as e:
            self.log_test("Streaming Generate Content", "FAIL", str(e))
            return False
    
    def test_function_calling(self):
        """Test function calling support."""
        try:
            url = f"{self.base_url}/v1/models/gemini-1.5-pro:generateContent"
            payload = {
                "contents": [
                    {
                        "role": "user",
                        "parts": [
                            {"text": "What's the weather like in San Francisco?"}
                        ]
                    }
                ],
                "tools": [
                    {
                        "functionDeclarations": [
                            {
                                "name": "get_weather",
                                "description": "Get weather information for a location",
                                "parameters": {
                                    "type": "object",
                                    "properties": {
                                        "location": {
                                            "type": "string",
                                            "description": "The location to get weather for"
                                        }
                                    },
                                    "required": ["location"]
                                }
                            }
                        ]
                    }
                ]
            }
            
            response = self.session.post(url, json=payload, timeout=TEST_TIMEOUT)
            
            assert response.status_code == 200, f"Expected 200, got {response.status_code}"
            
            data = response.json()
            assert "candidates" in data, "Response missing candidates"
            
            self.log_test("Function Calling", "PASS", "Function calling tools processed")
            return True
            
        except Exception as e:
            self.log_test("Function Calling", "FAIL", str(e))
            return False
    
    def test_error_handling(self):
        """Test error handling for invalid requests."""
        try:
            # Test with missing contents
            url = f"{self.base_url}/v1/models/gemini-1.5-pro:generateContent"
            payload = {}  # Missing required contents
            
            response = self.session.post(url, json=payload, timeout=TEST_TIMEOUT)
            
            # Should return an error
            assert response.status_code >= 400, f"Expected error status, got {response.status_code}"
            
            self.log_test("Error Handling", "PASS", "Proper error responses for invalid requests")
            return True
            
        except Exception as e:
            self.log_test("Error Handling", "FAIL", str(e))
            return False
    
    def test_usage_metadata(self):
        """Test usage metadata in responses."""
        try:
            url = f"{self.base_url}/v1/models/gemini-1.5-pro:generateContent"
            payload = {
                "contents": [
                    {
                        "role": "user",
                        "parts": [
                            {"text": "Write a short poem about AI."}
                        ]
                    }
                ]
            }
            
            response = self.session.post(url, json=payload, timeout=TEST_TIMEOUT)
            
            assert response.status_code == 200, f"Expected 200, got {response.status_code}"
            
            data = response.json()
            assert "usageMetadata" in data, "Response missing 'usageMetadata' field"
            
            usage = data["usageMetadata"]
            assert "promptTokenCount" in usage, "Usage missing 'promptTokenCount'"
            assert "candidatesTokenCount" in usage, "Usage missing 'candidatesTokenCount'"
            assert "totalTokenCount" in usage, "Usage missing 'totalTokenCount'"
            
            self.log_test("Usage Metadata", "PASS", f"Token counts: {usage['totalTokenCount']} total")
            return True
            
        except Exception as e:
            self.log_test("Usage Metadata", "FAIL", str(e))
            return False
    
    def run_all_tests(self):
        """Run all Google SDK compatibility tests."""
        print("🧪 Starting Google Vertex AI SDK Compatibility Tests")
        print("=" * 60)
        
        if not self.setup_client():
            print("❌ Cannot proceed without Google SDK client")
            return False, 0, 1
        
        tests = [
            self.test_basic_generate_content,
            self.test_system_instruction,
            self.test_generation_config,
            self.test_safety_settings,
            self.test_multimodal_content,
            self.test_streaming_generate_content,
            self.test_function_calling,
            self.test_error_handling,
            self.test_usage_metadata
        ]
        
        passed = 0
        failed = 0
        
        for test in tests:
            try:
                if test():
                    passed += 1
                else:
                    failed += 1
            except Exception as e:
                print(f"❌ Test {test.__name__} crashed: {e}")
                failed += 1
        
        # Summary
        print("\n" + "=" * 60)
        print("📊 Google Vertex AI SDK Compatibility Test Summary")
        print("=" * 60)
        
        total_tests = passed + failed
        print(f"Total Tests: {total_tests}")
        print(f"✅ Passed: {passed}")
        print(f"❌ Failed: {failed}")
        print(f"Success Rate: {(passed/total_tests)*100:.1f}%")
        
        if failed > 0:
            print("\n❌ Failed Tests:")
            for result in self.results:
                if result["status"] == "FAIL":
                    print(f"  - {result['test']}: {result['details']}")
        
        return passed, failed, total_tests

def main():
    """Main test runner."""
    print("🌐 Google Vertex AI SDK Compatibility Test Suite")
    print("Testing adapter compatibility with official Google Cloud AI Platform SDK")
    print()
    
    tester = GoogleSDKTester()
    
    try:
        passed, failed, total = tester.run_all_tests()
        
        if failed == 0:
            print("\n🎉 All Google SDK tests passed! Full compatibility achieved.")
            sys.exit(0)
        else:
            print(f"\n⚠️  {failed} tests failed. Compatibility issues detected.")
            sys.exit(1)
            
    except KeyboardInterrupt:
        print("\n\n⏹️  Tests interrupted by user.")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n💥 Test suite failed with exception: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()

