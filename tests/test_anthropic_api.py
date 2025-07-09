#!/usr/bin/env python3
"""
Test script for Anthropic API compatibility in open_codegen.
Tests both streaming and non-streaming endpoints.
"""

import asyncio
import json
import httpx
import time
from typing import Dict, Any

# Test configuration
BASE_URL = "http://localhost:8001"  # Adjust port as needed
TEST_MODEL = "claude-3-sonnet-20240229"

async def test_anthropic_messages_non_streaming():
    """Test the /v1/messages endpoint without streaming."""
    print("🧪 Testing /v1/messages (non-streaming)...")
    
    request_data = {
        "model": TEST_MODEL,
        "max_tokens": 100,
        "messages": [
            {
                "role": "user",
                "content": "Hello! Can you help me with a simple math problem? What is 2 + 3?"
            }
        ],
        "temperature": 0.7,
        "stream": False
    }
    
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{BASE_URL}/v1/messages",
                json=request_data,
                headers={"Content-Type": "application/json"}
            )
            
            print(f"   📊 Status Code: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                print(f"   ✅ Success!")
                print(f"   🆔 Message ID: {result.get('id', 'N/A')}")
                print(f"   🤖 Model: {result.get('model', 'N/A')}")
                print(f"   🛑 Stop Reason: {result.get('stop_reason', 'N/A')}")
                
                if 'content' in result and len(result['content']) > 0:
                    content_text = result['content'][0].get('text', '')
                    print(f"   📝 Response: {content_text[:200]}...")
                
                if 'usage' in result:
                    usage = result['usage']
                    print(f"   🔢 Tokens - Input: {usage.get('input_tokens', 0)}, Output: {usage.get('output_tokens', 0)}")
                
                return True
            else:
                print(f"   ❌ Failed: {response.text}")
                return False
                
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False

async def test_anthropic_messages_streaming():
    """Test the /v1/messages endpoint with streaming."""
    print("🧪 Testing /v1/messages (streaming)...")
    
    request_data = {
        "model": TEST_MODEL,
        "max_tokens": 100,
        "messages": [
            {
                "role": "user",
                "content": "Tell me a short joke about programming."
            }
        ],
        "temperature": 0.7,
        "stream": True
    }
    
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            async with client.stream(
                "POST",
                f"{BASE_URL}/v1/messages",
                json=request_data,
                headers={"Content-Type": "application/json"}
            ) as response:
                
                print(f"   📊 Status Code: {response.status_code}")
                
                if response.status_code == 200:
                    print(f"   ✅ Streaming started!")
                    
                    event_count = 0
                    content_chunks = []
                    
                    async for line in response.aiter_lines():
                        if line.startswith("data: "):
                            data = line[6:]  # Remove "data: " prefix
                            
                            if data == "[DONE]":
                                print(f"   🏁 Stream completed")
                                break
                            
                            try:
                                event = json.loads(data)
                                event_type = event.get("type", "unknown")
                                event_count += 1
                                
                                print(f"   📦 Event {event_count}: {event_type}")
                                
                                # Collect content deltas
                                if event_type == "content_block_delta":
                                    delta = event.get("delta", {})
                                    if delta.get("type") == "text_delta":
                                        text = delta.get("text", "")
                                        content_chunks.append(text)
                                        print(f"      📝 Text: {repr(text)}")
                                
                            except json.JSONDecodeError:
                                print(f"   ⚠️ Invalid JSON: {data}")
                    
                    full_content = "".join(content_chunks)
                    print(f"   📄 Full Response: {full_content}")
                    print(f"   📊 Total Events: {event_count}")
                    
                    return True
                else:
                    print(f"   ❌ Failed: {response.text}")
                    return False
                    
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False

async def test_anthropic_count_tokens():
    """Test the /v1/messages/count_tokens endpoint."""
    print("🧪 Testing /v1/messages/count_tokens...")
    
    request_data = {
        "model": TEST_MODEL,
        "messages": [
            {
                "role": "user",
                "content": "This is a test message to count tokens. How many tokens does this message contain?"
            }
        ]
    }
    
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{BASE_URL}/v1/messages/count_tokens",
                json=request_data,
                headers={"Content-Type": "application/json"}
            )
            
            print(f"   📊 Status Code: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                print(f"   ✅ Success!")
                print(f"   🔢 Input Tokens: {result.get('input_tokens', 0)}")
                return True
            else:
                print(f"   ❌ Failed: {response.text}")
                return False
                
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False

async def test_models_endpoint():
    """Test the /v1/models endpoint to ensure Anthropic models are listed."""
    print("🧪 Testing /v1/models...")
    
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(f"{BASE_URL}/v1/models")
            
            print(f"   📊 Status Code: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                models = result.get("data", [])
                
                anthropic_models = [m for m in models if m.get("owned_by") == "anthropic"]
                print(f"   ✅ Success!")
                print(f"   📋 Total Models: {len(models)}")
                print(f"   🤖 Anthropic Models: {len(anthropic_models)}")
                
                for model in anthropic_models:
                    print(f"      - {model.get('id', 'N/A')}")
                
                return True
            else:
                print(f"   ❌ Failed: {response.text}")
                return False
                
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False

async def main():
    """Run all tests."""
    print("🚀 Starting Anthropic API Tests")
    print("=" * 50)
    
    tests = [
        ("Models Endpoint", test_models_endpoint),
        ("Token Counting", test_anthropic_count_tokens),
        ("Non-Streaming Messages", test_anthropic_messages_non_streaming),
        ("Streaming Messages", test_anthropic_messages_streaming),
    ]
    
    results = []
    
    for test_name, test_func in tests:
        print(f"\n🔍 {test_name}")
        print("-" * 30)
        
        start_time = time.time()
        success = await test_func()
        duration = time.time() - start_time
        
        results.append((test_name, success, duration))
        
        if success:
            print(f"   ⏱️ Completed in {duration:.2f}s")
        else:
            print(f"   ⏱️ Failed after {duration:.2f}s")
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 Test Results Summary")
    print("=" * 50)
    
    passed = sum(1 for _, success, _ in results if success)
    total = len(results)
    
    for test_name, success, duration in results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {test_name} ({duration:.2f}s)")
    
    print(f"\n🎯 Overall: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Anthropic API implementation is working!")
    else:
        print("⚠️ Some tests failed. Check the implementation.")

if __name__ == "__main__":
    asyncio.run(main())
