#!/usr/bin/env python3
"""
Simple test script to verify Gemini endpoint fixes
"""

import asyncio
import sys
import os

# Add the openai_codegen_adapter directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'openai_codegen_adapter'))

# Mock the codegen client for testing
class MockCodegenClient:
    async def run_task(self, prompt: str, stream: bool = False):
        """Mock implementation that yields chunks if streaming"""
        if stream:
            # Simulate streaming response
            chunks = ["Hello", " there", "! This", " is", " a", " test", " response", "."]
            for chunk in chunks:
                yield chunk

async def test_gemini_streaming_functions():
    """Test the Gemini streaming functions"""
    print("🧪 Testing Gemini streaming functions...")
    
    try:
        # Import the functions we need to test
        from gemini_streaming import collect_gemini_streaming_response
        
        # Create a mock client
        client = MockCodegenClient()
        
        # Test collect_gemini_streaming_response
        print("📦 Testing collect_gemini_streaming_response...")
        result = await collect_gemini_streaming_response(client, "Test prompt")
        print(f"✅ Streaming collection result: {result}")
        
        # Test that the function works with streaming=True
        print("🌊 Testing direct streaming...")
        full_content = ""
        async for chunk in client.run_task("Test prompt", stream=True):
            full_content += chunk
        print(f"✅ Direct streaming result: {full_content}")
        
        print("🎉 Streaming tests passed!")
        return True
        
    except Exception as e:
        print(f"❌ Streaming test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_gemini_request_model():
    """Test the GeminiRequest model with stream field"""
    print("🧪 Testing GeminiRequest model...")
    
    try:
        from models import GeminiRequest, GeminiContent
        
        # Test with stream=True
        request_data = {
            "contents": [{"parts": [{"text": "Hello"}]}],
            "stream": True
        }
        request = GeminiRequest(**request_data)
        print(f"✅ Request with stream=True: {request.stream}")
        
        # Test with stream=False (default)
        request_data = {
            "contents": [{"parts": [{"text": "Hello"}]}]
        }
        request = GeminiRequest(**request_data)
        print(f"✅ Request with default stream: {request.stream}")
        
        print("🎉 Model tests passed!")
        return True
        
    except Exception as e:
        print(f"❌ Model test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    """Run all tests"""
    print("🚀 Starting Gemini fix verification tests...")
    print("=" * 50)
    
    # Test the model
    model_test = await test_gemini_request_model()
    
    # Test the streaming functions
    streaming_test = await test_gemini_streaming_functions()
    
    print("=" * 50)
    if model_test and streaming_test:
        print("🎉 All tests passed! The Gemini fixes should work correctly.")
        return 0
    else:
        print("❌ Some tests failed. Please check the implementation.")
        return 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)

