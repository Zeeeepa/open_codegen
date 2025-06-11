#!/usr/bin/env python3
"""
Test script for OpenAI API endpoint.
Sends a message to the OpenAI API and receives a response via the unified server.
"""

import asyncio
import json
import time
import httpx
from typing import Dict, Any


async def test_openai_api(
    base_url: str = "http://localhost:8887",
    model: str = "gpt-3.5-turbo",
    message: str = "Hello! Please respond with just 'Hi there!'",
    timeout: int = 30
) -> Dict[str, Any]:
    """
    Test the OpenAI API endpoint.
    
    Args:
        base_url: Base URL of the server
        model: OpenAI model to use
        message: Message to send
        timeout: Request timeout in seconds
        
    Returns:
        Dict containing test results
    """
    print(f"🤖 Testing OpenAI API...")
    print(f"   Server: {base_url}")
    print(f"   Model: {model}")
    print(f"   Message: {message}")
    
    start_time = time.time()
    
    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            # Test the OpenAI chat completions endpoint
            response = await client.post(
                f"{base_url}/v1/chat/completions",
                headers={"Content-Type": "application/json"},
                json={
                    "model": model,
                    "messages": [{"role": "user", "content": message}],
                    "max_tokens": 150,
                    "temperature": 0.7
                }
            )
            
            processing_time = time.time() - start_time
            
            if response.status_code == 200:
                result = response.json()
                print(f"✅ OpenAI API Test Successful!")
                print(f"   Response: {result.get('choices', [{}])[0].get('message', {}).get('content', 'No content')}")
                print(f"   Processing time: {processing_time:.2f}s")
                
                return {
                    "success": True,
                    "provider": "openai",
                    "model": model,
                    "response": result,
                    "processing_time": processing_time,
                    "status_code": response.status_code
                }
            else:
                print(f"❌ OpenAI API Test Failed!")
                print(f"   Status: {response.status_code}")
                print(f"   Error: {response.text}")
                
                return {
                    "success": False,
                    "provider": "openai",
                    "model": model,
                    "error": response.text,
                    "processing_time": processing_time,
                    "status_code": response.status_code
                }
                
    except Exception as e:
        processing_time = time.time() - start_time
        print(f"❌ OpenAI API Test Exception!")
        print(f"   Error: {str(e)}")
        print(f"   Processing time: {processing_time:.2f}s")
        
        return {
            "success": False,
            "provider": "openai",
            "model": model,
            "error": str(e),
            "processing_time": processing_time,
            "status_code": None
        }


async def test_via_test_endpoint(
    base_url: str = "http://localhost:8887",
    model: str = "gpt-3.5-turbo",
    message: str = "Hello! Please respond with just 'Hi there!'"
) -> Dict[str, Any]:
    """Test OpenAI via the unified test endpoint."""
    print(f"\n🧪 Testing OpenAI via test endpoint...")
    
    try:
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.post(
                f"{base_url}/api/test/openai",
                headers={"Content-Type": "application/json"},
                json={
                    "message": message,
                    "model": model
                }
            )
            
            if response.status_code == 200:
                result = response.json()
                print(f"✅ Test endpoint successful!")
                print(f"   Success: {result.get('success')}")
                print(f"   Response: {result.get('response', 'No response')}")
                return result
            else:
                print(f"❌ Test endpoint failed: {response.status_code}")
                return {"success": False, "error": response.text}
                
    except Exception as e:
        print(f"❌ Test endpoint exception: {str(e)}")
        return {"success": False, "error": str(e)}


def main():
    """Main function to run the OpenAI API test."""
    print("=" * 60)
    print("OpenAI API Test")
    print("=" * 60)
    
    # Run the async test
    result = asyncio.run(test_openai_api())
    
    # Also test via the test endpoint
    test_result = asyncio.run(test_via_test_endpoint())
    
    print("\n" + "=" * 60)
    print("Test Summary:")
    print(f"Direct API Test: {'✅ PASSED' if result['success'] else '❌ FAILED'}")
    print(f"Test Endpoint: {'✅ PASSED' if test_result.get('success') else '❌ FAILED'}")
    print("=" * 60)
    
    return result['success'] and test_result.get('success', False)


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)

