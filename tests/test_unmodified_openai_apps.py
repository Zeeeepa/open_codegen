#!/usr/bin/env python3
"""
Test Unmodified OpenAI Applications with Transparent Interception

This test validates that REAL, UNMODIFIED OpenAI applications work properly
with transparent interception, including HTTPS support and proper response handling.

Key Tests:
1. Standard OpenAI client initialization (no base_url override)
2. HTTPS requests work properly with SSL certificates
3. Dummy API keys are accepted and processed
4. Complete responses are returned with proper formatting
5. Real-world usage patterns work correctly
"""

import os
import sys
import time
import subprocess
from openai import OpenAI

class UnmodifiedOpenAIAppTester:
    def __init__(self):
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

    def setup_transparent_interception(self):
        """Set up transparent interception for testing."""
        print("🔧 Setting up transparent interception...")
        
        try:
            # Enable DNS interception
            result = subprocess.run(
                ["sudo", "python3", "-m", "interceptor.ubuntu_dns", "enable"],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode == 0:
                print("✅ DNS interception enabled")
            else:
                print(f"⚠️ DNS setup warning: {result.stderr}")
            
            # Check if SSL certificates exist, if not create them
            ssl_result = subprocess.run(
                ["sudo", "python3", "-m", "interceptor.ubuntu_ssl", "status"],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if "not found" in ssl_result.stdout.lower():
                print("🔐 Setting up SSL certificates...")
                ssl_setup = subprocess.run(
                    ["sudo", "python3", "-m", "interceptor.ubuntu_ssl", "setup"],
                    capture_output=True,
                    text=True,
                    timeout=60
                )
                if ssl_setup.returncode == 0:
                    print("✅ SSL certificates created")
                else:
                    print(f"⚠️ SSL setup failed: {ssl_setup.stderr}")
            
            return True
            
        except Exception as e:
            print(f"❌ Setup failed: {e}")
            return False

    def start_interceptor_server(self):
        """Start the interceptor server."""
        print("🚀 Starting interceptor server...")
        
        try:
            # Start server in background
            env = os.environ.copy()
            env.update({
                "TRANSPARENT_MODE": "true",
                "BIND_PRIVILEGED_PORTS": "true",
                "SERVER_PORT": "80"
            })
            
            self.server_process = subprocess.Popen(
                ["python3", "server.py"],
                env=env,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            
            # Give server time to start
            time.sleep(3)
            
            # Check if server is running
            if self.server_process.poll() is None:
                print("✅ Server started successfully")
                return True
            else:
                stdout, stderr = self.server_process.communicate()
                print(f"❌ Server failed to start: {stderr.decode()}")
                return False
                
        except Exception as e:
            print(f"❌ Failed to start server: {e}")
            return False

    def test_standard_openai_client(self):
        """Test standard OpenAI client initialization (exactly as real apps do)."""
        print("🧪 Testing Standard OpenAI Client (Unmodified)")
        print("-" * 50)
        
        try:
            # This is EXACTLY how real OpenAI applications initialize the client
            # NO base_url override, NO special configuration
            client = OpenAI(
                api_key="sk-fake-key-for-transparent-interception-testing"
            )
            
            print(f"✅ Client initialized with base_url: {client.base_url}")
            print(f"🔑 Using dummy API key (would fail with real OpenAI)")
            
            # Verify it's using the standard OpenAI URL
            assert str(client.base_url) == "https://api.openai.com/v1/", "Client not using standard OpenAI URL"
            
            self.log_test(
                "Standard OpenAI Client Init", 
                True, 
                f"Client uses {client.base_url} with dummy key"
            )
            return client
            
        except Exception as e:
            self.log_test("Standard OpenAI Client Init", False, f"Error: {e}")
            return None

    def test_https_interception(self, client):
        """Test that HTTPS requests are properly intercepted."""
        print("🔐 Testing HTTPS Interception")
        print("-" * 50)
        
        try:
            print("📤 Making HTTPS request to api.openai.com...")
            
            # This should be intercepted and routed to our local server
            models = client.models.list()
            
            print(f"📥 Response received!")
            print(f"📋 Found {len(models.data)} models")
            
            # Verify we got a reasonable response
            assert len(models.data) > 0, "No models returned"
            
            model_names = [model.id for model in models.data[:3]]
            print(f"🤖 First 3 models: {', '.join(model_names)}")
            
            self.log_test(
                "HTTPS Interception", 
                True, 
                f"Retrieved {len(models.data)} models via HTTPS"
            )
            return True
            
        except Exception as e:
            self.log_test("HTTPS Interception", False, f"Error: {e}")
            return False

    def test_complete_chat_workflow(self, client):
        """Test complete chat completion workflow with unmodified client."""
        print("💬 Testing Complete Chat Workflow")
        print("-" * 50)
        
        try:
            print("📤 Sending chat completion request...")
            
            # Standard chat completion request - exactly as real apps do it
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {
                        "role": "system",
                        "content": "You are a helpful assistant. Always respond with 'SUCCESS: Transparent interception working!' followed by a brief confirmation."
                    },
                    {
                        "role": "user",
                        "content": "Please confirm that transparent interception is working properly."
                    }
                ],
                max_tokens=100,
                temperature=0.1
            )
            
            # Verify response structure and content
            assert hasattr(response, 'choices'), "Response missing choices"
            assert len(response.choices) > 0, "No choices in response"
            assert hasattr(response.choices[0], 'message'), "Choice missing message"
            assert hasattr(response.choices[0].message, 'content'), "Message missing content"
            
            content = response.choices[0].message.content
            model = response.model
            usage = response.usage
            
            print(f"📥 Response received!")
            print(f"🤖 Model: {model}")
            print(f"📝 Content: {content}")
            print(f"🔢 Tokens: {usage.total_tokens} ({usage.prompt_tokens} + {usage.completion_tokens})")
            
            # Verify content is reasonable
            assert content and len(content.strip()) > 0, "Empty response content"
            assert usage.total_tokens > 0, "Zero token usage"
            
            self.log_test(
                "Complete Chat Workflow", 
                True, 
                f"Got {len(content)} chars, {usage.total_tokens} tokens"
            )
            return True
            
        except Exception as e:
            self.log_test("Complete Chat Workflow", False, f"Error: {e}")
            return False

    def test_multiple_requests(self, client):
        """Test multiple sequential requests work properly."""
        print("🔄 Testing Multiple Sequential Requests")
        print("-" * 50)
        
        successful_requests = 0
        total_requests = 3
        
        for i in range(total_requests):
            try:
                print(f"📤 Request {i+1}/{total_requests}...")
                
                response = client.chat.completions.create(
                    model="gpt-3.5-turbo",
                    messages=[
                        {
                            "role": "user",
                            "content": f"This is test request #{i+1}. Please respond with 'Request {i+1} processed successfully.'"
                        }
                    ],
                    max_tokens=30
                )
                
                content = response.choices[0].message.content
                print(f"📥 Response {i+1}: {content[:50]}...")
                
                successful_requests += 1
                
            except Exception as e:
                print(f"❌ Request {i+1} failed: {e}")
        
        success = successful_requests == total_requests
        self.log_test(
            "Multiple Sequential Requests", 
            success, 
            f"{successful_requests}/{total_requests} requests succeeded"
        )
        return success

    def test_real_world_usage_pattern(self, client):
        """Test a real-world usage pattern that apps commonly use."""
        print("🌍 Testing Real-World Usage Pattern")
        print("-" * 50)
        
        try:
            # Pattern: List models, then use one for chat
            print("1️⃣ Listing available models...")
            models = client.models.list()
            available_models = [m.id for m in models.data]
            print(f"   Found models: {', '.join(available_models[:3])}...")
            
            # Pick a model and use it
            model_to_use = "gpt-3.5-turbo"
            if model_to_use not in available_models:
                model_to_use = available_models[0]
            
            print(f"2️⃣ Using model: {model_to_use}")
            
            # Make a chat request
            print("3️⃣ Making chat request...")
            response = client.chat.completions.create(
                model=model_to_use,
                messages=[
                    {
                        "role": "user",
                        "content": "Explain what transparent API interception means in one sentence."
                    }
                ],
                max_tokens=50
            )
            
            content = response.choices[0].message.content
            print(f"4️⃣ Got response: {content[:60]}...")
            
            # Verify everything worked
            assert len(available_models) > 0, "No models available"
            assert content and len(content.strip()) > 0, "Empty chat response"
            
            self.log_test(
                "Real-World Usage Pattern", 
                True, 
                f"Models→Chat workflow completed successfully"
            )
            return True
            
        except Exception as e:
            self.log_test("Real-World Usage Pattern", False, f"Error: {e}")
            return False

    def cleanup(self):
        """Clean up after testing."""
        print("\n🧹 Cleaning up...")
        
        try:
            # Stop server
            if hasattr(self, 'server_process'):
                self.server_process.terminate()
                self.server_process.wait(timeout=5)
                print("✅ Server stopped")
        except:
            pass
        
        try:
            # Disable DNS interception
            subprocess.run(
                ["sudo", "python3", "-m", "interceptor.ubuntu_dns", "disable"],
                capture_output=True,
                timeout=30
            )
            print("✅ DNS interception disabled")
        except:
            pass

    def run_all_tests(self):
        """Run all tests for unmodified OpenAI applications."""
        print("🎯 UNMODIFIED OPENAI APPLICATION TESTING")
        print("=" * 60)
        print("Testing that REAL, UNMODIFIED OpenAI applications work properly")
        print("with transparent interception and return complete responses.")
        print()
        
        # Setup
        if not self.setup_transparent_interception():
            print("❌ Failed to set up transparent interception")
            return False
        
        if not self.start_interceptor_server():
            print("❌ Failed to start interceptor server")
            return False
        
        try:
            # Test standard client initialization
            client = self.test_standard_openai_client()
            if not client:
                return False
            
            # Run all tests with the unmodified client
            tests = [
                lambda: self.test_https_interception(client),
                lambda: self.test_complete_chat_workflow(client),
                lambda: self.test_multiple_requests(client),
                lambda: self.test_real_world_usage_pattern(client)
            ]
            
            for test in tests:
                try:
                    test()
                except Exception as e:
                    print(f"❌ Test crashed: {e}")
            
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
                print("✅ Unmodified OpenAI applications work perfectly")
                print("✅ HTTPS interception is working")
                print("✅ Complete responses are returned")
                print("✅ Real-world usage patterns work")
                print("✅ Transparent interception is production-ready")
            else:
                print(f"\n⚠️ {total - passed} tests failed")
                print("❌ Some functionality needs fixing")
            
            return passed == total
            
        finally:
            self.cleanup()

if __name__ == "__main__":
    tester = UnmodifiedOpenAIAppTester()
    success = tester.run_all_tests()
    exit(0 if success else 1)
