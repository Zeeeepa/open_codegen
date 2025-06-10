#!/usr/bin/env python3
"""
Anthropic SDK Compatibility Test Suite
Tests the adapter using the official Anthropic Python SDK to ensure full compatibility.
"""

import asyncio
import json
import time
import sys
from typing import List, Dict, Any

# Test configuration
BASE_URL = "http://localhost:8887"
TEST_TIMEOUT = 30

class AnthropicSDKTester:
    def __init__(self, base_url: str = BASE_URL):
        self.base_url = base_url
        self.results = []
        self.client = None
        
    def setup_client(self):
        """Setup Anthropic client pointing to our adapter."""
        try:
            import anthropic
            self.client = anthropic.Anthropic(
                api_key="dummy-key",  # Our adapter doesn't validate this
                base_url=f"{self.base_url}/v1"
            )
            print("✅ Anthropic SDK client initialized successfully")
            return True
        except ImportError:
            print("❌ Anthropic SDK not installed. Install with: pip install anthropic")
            return False
        except Exception as e:
            print(f"❌ Failed to initialize Anthropic client: {e}")
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
    
    def test_basic_message(self):
        """Test basic message creation."""
        try:
            response = self.client.messages.create(
                model="claude-3-sonnet-20240229",
                max_tokens=100,
                messages=[
                    {"role": "user", "content": "Hello, Claude! This is a test message."}
                ]
            )
            
            # Validate response structure
            assert hasattr(response, 'id'), "Response missing 'id' field"
            assert hasattr(response, 'type'), "Response missing 'type' field"
            assert hasattr(response, 'role'), "Response missing 'role' field"
            assert hasattr(response, 'content'), "Response missing 'content' field"
            assert hasattr(response, 'model'), "Response missing 'model' field"
            assert hasattr(response, 'usage'), "Response missing 'usage' field"
            
            assert response.type == "message", f"Expected type 'message', got '{response.type}'"
            assert response.role == "assistant", f"Expected role 'assistant', got '{response.role}'"
            assert len(response.content) > 0, "Response content is empty"
            assert response.content[0].type == "text", "First content block should be text"
            
            self.log_test("Basic Message", "PASS", f"Response ID: {response.id}")
            return True
            
        except Exception as e:
            self.log_test("Basic Message", "FAIL", str(e))
            return False
    
    def test_system_message(self):
        """Test system message support."""
        try:
            response = self.client.messages.create(
                model="claude-3-sonnet-20240229",
                max_tokens=100,
                system="You are a helpful assistant that responds in exactly 5 words.",
                messages=[
                    {"role": "user", "content": "What is the weather like?"}
                ]
            )
            
            assert hasattr(response, 'content'), "Response missing content"
            assert len(response.content) > 0, "Response content is empty"
            
            self.log_test("System Message", "PASS", "System instruction processed")
            return True
            
        except Exception as e:
            self.log_test("System Message", "FAIL", str(e))
            return False
    
    def test_multi_turn_conversation(self):
        """Test multi-turn conversation."""
        try:
            response = self.client.messages.create(
                model="claude-3-sonnet-20240229",
                max_tokens=150,
                messages=[
                    {"role": "user", "content": "Hello, what's your name?"},
                    {"role": "assistant", "content": "Hello! I'm Claude, an AI assistant created by Anthropic."},
                    {"role": "user", "content": "Can you help me with a coding question?"}
                ]
            )
            
            assert hasattr(response, 'content'), "Response missing content"
            assert len(response.content) > 0, "Response content is empty"
            
            self.log_test("Multi-turn Conversation", "PASS", "Conversation history processed")
            return True
            
        except Exception as e:
            self.log_test("Multi-turn Conversation", "FAIL", str(e))
            return False
    
    def test_content_blocks(self):
        """Test content blocks format."""
        try:
            response = self.client.messages.create(
                model="claude-3-sonnet-20240229",
                max_tokens=100,
                messages=[
                    {
                        "role": "user", 
                        "content": [
                            {"type": "text", "text": "Analyze this text content block."}
                        ]
                    }
                ]
            )
            
            assert hasattr(response, 'content'), "Response missing content"
            assert isinstance(response.content, list), "Content should be a list"
            assert len(response.content) > 0, "Response content is empty"
            assert response.content[0].type == "text", "First content block should be text"
            
            self.log_test("Content Blocks", "PASS", "Content blocks processed correctly")
            return True
            
        except Exception as e:
            self.log_test("Content Blocks", "FAIL", str(e))
            return False
    
    def test_temperature_parameter(self):
        """Test temperature parameter."""
        try:
            response = self.client.messages.create(
                model="claude-3-sonnet-20240229",
                max_tokens=100,
                temperature=0.5,
                messages=[
                    {"role": "user", "content": "Generate a creative story opening."}
                ]
            )
            
            assert hasattr(response, 'content'), "Response missing content"
            
            self.log_test("Temperature Parameter", "PASS", "Temperature parameter accepted")
            return True
            
        except Exception as e:
            self.log_test("Temperature Parameter", "FAIL", str(e))
            return False
    
    def test_stop_sequences(self):
        """Test stop sequences parameter."""
        try:
            response = self.client.messages.create(
                model="claude-3-sonnet-20240229",
                max_tokens=200,
                stop_sequences=["END", "STOP"],
                messages=[
                    {"role": "user", "content": "Write a short story and end it with END."}
                ]
            )
            
            assert hasattr(response, 'content'), "Response missing content"
            assert hasattr(response, 'stop_reason'), "Response missing stop_reason"
            
            self.log_test("Stop Sequences", "PASS", f"Stop reason: {response.stop_reason}")
            return True
            
        except Exception as e:
            self.log_test("Stop Sequences", "FAIL", str(e))
            return False
    
    def test_streaming(self):
        """Test streaming responses."""
        try:
            stream = self.client.messages.create(
                model="claude-3-sonnet-20240229",
                max_tokens=100,
                stream=True,
                messages=[
                    {"role": "user", "content": "Count from 1 to 10."}
                ]
            )
            
            chunks_received = 0
            for chunk in stream:
                chunks_received += 1
                if chunks_received > 10:  # Limit for testing
                    break
            
            assert chunks_received > 0, "No streaming chunks received"
            
            self.log_test("Streaming", "PASS", f"Received {chunks_received} chunks")
            return True
            
        except Exception as e:
            self.log_test("Streaming", "FAIL", str(e))
            return False
    
    def test_error_handling(self):
        """Test error handling for invalid requests."""
        try:
            # Test with invalid max_tokens
            try:
                response = self.client.messages.create(
                    model="claude-3-sonnet-20240229",
                    max_tokens=0,  # Invalid
                    messages=[
                        {"role": "user", "content": "This should fail."}
                    ]
                )
                self.log_test("Error Handling", "FAIL", "Should have failed with invalid max_tokens")
                return False
            except Exception as expected_error:
                # This should fail, which is correct
                pass
            
            # Test with missing messages
            try:
                response = self.client.messages.create(
                    model="claude-3-sonnet-20240229",
                    max_tokens=100,
                    messages=[]  # Invalid
                )
                self.log_test("Error Handling", "FAIL", "Should have failed with empty messages")
                return False
            except Exception as expected_error:
                # This should fail, which is correct
                pass
            
            self.log_test("Error Handling", "PASS", "Proper error responses for invalid requests")
            return True
            
        except Exception as e:
            self.log_test("Error Handling", "FAIL", str(e))
            return False
    
    def run_all_tests(self):
        """Run all Anthropic SDK compatibility tests."""
        print("🧪 Starting Anthropic SDK Compatibility Tests")
        print("=" * 60)
        
        if not self.setup_client():
            print("❌ Cannot proceed without Anthropic SDK client")
            return False, 0, 1
        
        tests = [
            self.test_basic_message,
            self.test_system_message,
            self.test_multi_turn_conversation,
            self.test_content_blocks,
            self.test_temperature_parameter,
            self.test_stop_sequences,
            self.test_streaming,
            self.test_error_handling
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
        print("📊 Anthropic SDK Compatibility Test Summary")
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
    print("🤖 Anthropic SDK Compatibility Test Suite")
    print("Testing adapter compatibility with official Anthropic Python SDK")
    print()
    
    tester = AnthropicSDKTester()
    
    try:
        passed, failed, total = tester.run_all_tests()
        
        if failed == 0:
            print("\n🎉 All Anthropic SDK tests passed! Full compatibility achieved.")
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

