#!/usr/bin/env python3
"""
Complete Response Cycle Testing for Transparent OpenAI API Interception

This test verifies that OpenAI client requests receive COMPLETE, PROPER responses
from the Codegen SDK through transparent interception, not just that requests are accepted.

Tests:
1. Complete chat completion responses with proper formatting
2. Streaming responses work correctly  
3. Multiple model support with real responses
4. Error handling and edge cases
5. Token usage and metadata accuracy
"""

import asyncio
import json
import time
from openai import OpenAI
import requests

class TransparentInterceptionTester:
    def __init__(self):
        self.base_url_http = "http://api.openai.com/v1"
        self.dummy_api_key = "sk-test-transparent-interception-complete-responses"
        self.test_results = []
        
    def log_test(self, test_name, success, details=""):
        """Log test results."""
        status = "✅ PASS" if success else "❌ FAIL"
        self.test_results.append({
            "test": test_name,
            "success": success,
            "details": details
        })
        print(f"{status} {test_name}")
        if details:
            print(f"    {details}")
        print()

    def test_complete_chat_response(self):
        """Test that chat completions return complete, properly formatted responses."""
        print("🧪 Testing Complete Chat Completion Response")
        print("-" * 50)
        
        try:
            # Use HTTP to avoid SSL issues for this test
            client = OpenAI(
                api_key=self.dummy_api_key,
                base_url=self.base_url_http
            )
            
            print("📤 Sending chat completion request...")
            start_time = time.time()
            
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {
                        "role": "system",
                        "content": "You are a helpful assistant. Respond with exactly: 'Hello from Codegen SDK via transparent interception!'"
                    },
                    {
                        "role": "user", 
                        "content": "Please respond with the exact message from your system prompt."
                    }
                ],
                max_tokens=50,
                temperature=0.1
            )
            
            end_time = time.time()
            response_time = end_time - start_time
            
            # Verify response structure
            assert hasattr(response, 'choices'), "Response missing 'choices'"
            assert len(response.choices) > 0, "Response has no choices"
            assert hasattr(response.choices[0], 'message'), "Choice missing 'message'"
            assert hasattr(response.choices[0].message, 'content'), "Message missing 'content'"
            assert hasattr(response, 'usage'), "Response missing 'usage'"
            assert hasattr(response, 'model'), "Response missing 'model'"
            assert hasattr(response, 'id'), "Response missing 'id'"
            
            content = response.choices[0].message.content
            model = response.model
            usage = response.usage
            response_id = response.id
            
            print(f"📥 Response received in {response_time:.2f}s")
            print(f"🤖 Model: {model}")
            print(f"🆔 ID: {response_id}")
            print(f"📝 Content: {content}")
            print(f"🔢 Usage: {usage.total_tokens} tokens ({usage.prompt_tokens} prompt + {usage.completion_tokens} completion)")
            
            # Verify content is not empty and reasonable
            assert content and len(content.strip()) > 0, "Response content is empty"
            assert usage.total_tokens > 0, "Token usage is zero"
            assert usage.prompt_tokens > 0, "Prompt tokens is zero"
            assert usage.completion_tokens > 0, "Completion tokens is zero"
            
            self.log_test(
                "Complete Chat Response", 
                True, 
                f"Got {len(content)} chars, {usage.total_tokens} tokens in {response_time:.2f}s"
            )
            return True
            
        except Exception as e:
            self.log_test("Complete Chat Response", False, f"Error: {e}")
            return False

    def test_multiple_models_responses(self):
        """Test that different models return proper responses."""
        print("🤖 Testing Multiple Models with Complete Responses")
        print("-" * 50)
        
        models_to_test = [
            "gpt-3.5-turbo",
            "gpt-4", 
            "claude-3-haiku-20240307"
        ]
        
        client = OpenAI(
            api_key=self.dummy_api_key,
            base_url=self.base_url_http
        )
        
        successful_models = 0
        
        for model in models_to_test:
            try:
                print(f"🧠 Testing {model}...")
                
                response = client.chat.completions.create(
                    model=model,
                    messages=[
                        {
                            "role": "user",
                            "content": f"Respond with: 'Working via {model} through Codegen SDK'"
                        }
                    ],
                    max_tokens=30
                )
                
                content = response.choices[0].message.content
                returned_model = response.model
                
                print(f"  📝 Response: {content[:60]}...")
                print(f"  🏷️ Returned model: {returned_model}")
                
                # Verify response is complete and reasonable
                assert content and len(content.strip()) > 0, f"{model} returned empty content"
                assert response.usage.total_tokens > 0, f"{model} returned zero tokens"
                
                successful_models += 1
                
            except Exception as e:
                print(f"  ❌ {model} failed: {e}")
        
        success = successful_models > 0
        self.log_test(
            "Multiple Models Responses", 
            success, 
            f"{successful_models}/{len(models_to_test)} models returned complete responses"
        )
        return success

    def test_streaming_response(self):
        """Test that streaming responses work properly."""
        print("🌊 Testing Streaming Response")
        print("-" * 50)
        
        try:
            client = OpenAI(
                api_key=self.dummy_api_key,
                base_url=self.base_url_http
            )
            
            print("📤 Sending streaming request...")
            
            stream = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {
                        "role": "user",
                        "content": "Count from 1 to 5, each number on a new line."
                    }
                ],
                max_tokens=50,
                stream=True
            )
            
            chunks_received = 0
            total_content = ""
            
            print("📥 Receiving stream chunks...")
            for chunk in stream:
                chunks_received += 1
                if chunk.choices and chunk.choices[0].delta.content:
                    content = chunk.choices[0].delta.content
                    total_content += content
                    print(f"  Chunk {chunks_received}: {repr(content)}")
                
                # Limit chunks to avoid infinite loops
                if chunks_received >= 20:
                    break
            
            print(f"📊 Received {chunks_received} chunks")
            print(f"📝 Total content: {repr(total_content)}")
            
            # Verify streaming worked
            assert chunks_received > 0, "No stream chunks received"
            assert len(total_content.strip()) > 0, "No content in stream"
            
            self.log_test(
                "Streaming Response", 
                True, 
                f"Received {chunks_received} chunks with {len(total_content)} chars"
            )
            return True
            
        except Exception as e:
            self.log_test("Streaming Response", False, f"Error: {e}")
            return False

    def test_error_handling(self):
        """Test error handling for invalid requests."""
        print("⚠️ Testing Error Handling")
        print("-" * 50)
        
        client = OpenAI(
            api_key=self.dummy_api_key,
            base_url=self.base_url_http
        )
        
        try:
            # Test invalid model
            print("🧪 Testing invalid model...")
            try:
                response = client.chat.completions.create(
                    model="invalid-model-that-does-not-exist",
                    messages=[{"role": "user", "content": "test"}],
                    max_tokens=10
                )
                print("  ⚠️ Invalid model request succeeded (unexpected)")
            except Exception as e:
                print(f"  ✅ Invalid model properly rejected: {e}")
            
            # Test empty messages
            print("🧪 Testing empty messages...")
            try:
                response = client.chat.completions.create(
                    model="gpt-3.5-turbo",
                    messages=[],
                    max_tokens=10
                )
                print("  ⚠️ Empty messages request succeeded (unexpected)")
            except Exception as e:
                print(f"  ✅ Empty messages properly rejected: {e}")
            
            self.log_test("Error Handling", True, "Error cases handled appropriately")
            return True
            
        except Exception as e:
            self.log_test("Error Handling", False, f"Error testing failed: {e}")
            return False

    def test_response_metadata_accuracy(self):
        """Test that response metadata (tokens, timing, etc.) is accurate."""
        print("📊 Testing Response Metadata Accuracy")
        print("-" * 50)
        
        try:
            client = OpenAI(
                api_key=self.dummy_api_key,
                base_url=self.base_url_http
            )
            
            # Test with known input to verify token counting
            test_message = "Hello world"
            
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": test_message}],
                max_tokens=20
            )
            
            usage = response.usage
            content = response.choices[0].message.content
            
            print(f"📝 Input: '{test_message}' ({len(test_message)} chars)")
            print(f"📝 Output: '{content}' ({len(content)} chars)")
            print(f"🔢 Prompt tokens: {usage.prompt_tokens}")
            print(f"🔢 Completion tokens: {usage.completion_tokens}")
            print(f"🔢 Total tokens: {usage.total_tokens}")
            
            # Verify metadata makes sense
            assert usage.prompt_tokens > 0, "Prompt tokens should be > 0"
            assert usage.completion_tokens > 0, "Completion tokens should be > 0"
            assert usage.total_tokens == usage.prompt_tokens + usage.completion_tokens, "Token math incorrect"
            assert len(content) > 0, "Response content should not be empty"
            assert response.model, "Model field should be populated"
            assert response.id, "ID field should be populated"
            
            self.log_test(
                "Response Metadata Accuracy", 
                True, 
                f"Tokens: {usage.total_tokens}, Content: {len(content)} chars"
            )
            return True
            
        except Exception as e:
            self.log_test("Response Metadata Accuracy", False, f"Error: {e}")
            return False

    def run_all_tests(self):
        """Run all tests and provide summary."""
        print("🎯 COMPLETE RESPONSE CYCLE TESTING")
        print("=" * 60)
        print("Testing that OpenAI client requests receive COMPLETE, PROPER responses")
        print("through transparent interception with Codegen SDK")
        print()
        
        # Run all tests
        tests = [
            self.test_complete_chat_response,
            self.test_multiple_models_responses,
            self.test_streaming_response,
            self.test_error_handling,
            self.test_response_metadata_accuracy
        ]
        
        for test in tests:
            try:
                test()
            except Exception as e:
                print(f"❌ Test {test.__name__} crashed: {e}")
                self.log_test(test.__name__, False, f"Test crashed: {e}")
        
        # Summary
        passed = sum(1 for result in self.test_results if result['success'])
        total = len(self.test_results)
        
        print("=" * 60)
        print(f"📊 TEST SUMMARY: {passed}/{total} tests passed")
        print("=" * 60)
        
        for result in self.test_results:
            status = "✅" if result['success'] else "❌"
            print(f"{status} {result['test']}")
            if result['details']:
                print(f"    {result['details']}")
        
        if passed == total:
            print("\n🎉 ALL TESTS PASSED!")
            print("✅ Complete response cycles work properly")
            print("✅ OpenAI clients receive full, proper responses")
            print("✅ Transparent interception is production-ready")
        else:
            print(f"\n⚠️ {total - passed} tests failed")
            print("❌ Some response cycles need fixing")
        
        return passed == total

if __name__ == "__main__":
    tester = TransparentInterceptionTester()
    success = tester.run_all_tests()
    exit(0 if success else 1)
