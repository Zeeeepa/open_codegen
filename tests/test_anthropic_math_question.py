#!/usr/bin/env python3
"""
Test Anthropic API with a specific math question: "22+12 and how are you"
This test demonstrates the working Anthropic API compatibility.
"""

import requests
import json
import time

def test_anthropic_math_question():
    """Test Anthropic API with the specific question: 22+12 and how are you."""
    print("🧮 Testing Anthropic API with Math Question")
    print("=" * 60)
    
    # Anthropic API endpoint
    url = "http://localhost:8001/v1/messages"
    
    # The specific question requested
    question = "22+12 and how are you"
    
    # Anthropic API request format
    payload = {
        "model": "claude-3-sonnet-20240229",
        "max_tokens": 150,
        "messages": [
            {
                "role": "user",
                "content": question
            }
        ]
    }
    
    headers = {
        "Content-Type": "application/json",
        "x-api-key": "dummy-key",  # Server doesn't validate this
        "anthropic-version": "2023-06-01"
    }
    
    print(f"📤 Sending question: '{question}'")
    print(f"   🎯 URL: {url}")
    print(f"   🤖 Model: {payload['model']}")
    print(f"   🔢 Max tokens: {payload['max_tokens']}")
    print()
    
    try:
        # Record start time
        start_time = time.time()
        
        # Send request
        response = requests.post(url, json=payload, headers=headers, timeout=60)
        
        # Record end time
        end_time = time.time()
        duration = end_time - start_time
        
        if response.status_code == 200:
            data = response.json()
            
            print("📥 RESPONSE RECEIVED:")
            print("=" * 60)
            print(f"   ✅ Status Code: {response.status_code}")
            print(f"   ⏱️  Response Time: {duration:.2f} seconds")
            print(f"   🆔 Message ID: {data.get('id', 'N/A')}")
            print(f"   🤖 Model: {data.get('model', 'N/A')}")
            print(f"   🛑 Stop Reason: {data.get('stop_reason', 'N/A')}")
            
            # Extract and display the content
            content_blocks = data.get('content', [])
            if content_blocks and len(content_blocks) > 0:
                response_text = content_blocks[0].get('text', 'No text content')
                print(f"   📝 Response Type: {content_blocks[0].get('type', 'unknown')}")
                print()
                print("💬 CLAUDE'S RESPONSE:")
                print("-" * 60)
                print(response_text)
                print("-" * 60)
            else:
                print("   ⚠️  No content blocks found in response")
            
            # Display usage statistics
            usage = data.get('usage', {})
            if usage:
                print()
                print("📊 TOKEN USAGE:")
                print(f"   📥 Input tokens: {usage.get('input_tokens', 0)}")
                print(f"   📤 Output tokens: {usage.get('output_tokens', 0)}")
                print(f"   💾 Cache creation tokens: {usage.get('cache_creation_input_tokens', 0)}")
                print(f"   🔄 Cache read tokens: {usage.get('cache_read_input_tokens', 0)}")
            
            print()
            print("✅ TEST COMPLETED SUCCESSFULLY!")
            return True
            
        else:
            print("❌ TEST FAILED:")
            print(f"   📊 Status Code: {response.status_code}")
            print(f"   ⏱️  Response Time: {duration:.2f} seconds")
            print(f"   📄 Error Response: {response.text}")
            return False
        
    except requests.exceptions.Timeout:
        print("❌ TEST FAILED: Request timed out after 60 seconds")
        return False
    except requests.exceptions.ConnectionError:
        print("❌ TEST FAILED: Could not connect to server")
        print("   💡 Make sure the server is running on localhost:8001")
        return False
    except Exception as e:
        print(f"❌ TEST FAILED: Unexpected error: {e}")
        return False

def test_anthropic_streaming_math():
    """Test the same question with streaming enabled."""
    print("\n🌊 Testing Anthropic Streaming API with Math Question")
    print("=" * 60)
    
    # Anthropic API endpoint
    url = "http://localhost:8001/v1/messages"
    
    # The specific question requested
    question = "22+12 and how are you"
    
    # Anthropic API request format with streaming
    payload = {
        "model": "claude-3-sonnet-20240229",
        "max_tokens": 150,
        "stream": True,
        "messages": [
            {
                "role": "user",
                "content": question
            }
        ]
    }
    
    headers = {
        "Content-Type": "application/json",
        "x-api-key": "dummy-key",
        "anthropic-version": "2023-06-01"
    }
    
    print(f"📤 Sending streaming question: '{question}'")
    print()
    
    try:
        # Send streaming request with timeout
        response = requests.post(url, json=payload, headers=headers, stream=True, timeout=30)
        
        if response.status_code == 200:
            print("📥 STREAMING RESPONSE:")
            print("-" * 60)
            
            event_count = 0
            content_chunks = []
            
            for line in response.iter_lines(decode_unicode=True):
                if line:
                    if line.startswith('data: '):
                        event_count += 1
                        data_str = line[6:]  # Remove 'data: ' prefix
                        
                        if data_str == "[DONE]":
                            print("🏁 Stream completed")
                            break
                        
                        try:
                            data = json.loads(data_str)
                            event_type = data.get('type', 'unknown')
                            print(f"📦 Event {event_count}: {event_type}")
                            
                            # Collect content deltas
                            if event_type == "content_block_delta":
                                delta = data.get("delta", {})
                                if delta.get("type") == "text_delta":
                                    text = delta.get("text", "")
                                    content_chunks.append(text)
                                    print(f"   📝 Text chunk: {repr(text)}")
                            
                        except json.JSONDecodeError:
                            print(f"📦 Event {event_count}: {data_str[:50]}...")
            
            # Show full assembled content
            if content_chunks:
                full_content = "".join(content_chunks)
                print()
                print("💬 ASSEMBLED STREAMING RESPONSE:")
                print("-" * 60)
                print(full_content)
                print("-" * 60)
            
            print(f"✅ Streaming test completed! Received {event_count} events")
            return True
            
        else:
            print(f"❌ Streaming test failed with status {response.status_code}")
            print(f"   📄 Response: {response.text}")
            return False
        
    except requests.exceptions.Timeout:
        print("❌ Streaming test failed: Request timed out after 30 seconds")
        return False
    except Exception as e:
        print(f"❌ Streaming test failed: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Starting Anthropic API Math Question Tests")
    print("=" * 60)
    
    # Test non-streaming first
    success1 = test_anthropic_math_question()
    
    # Test streaming (with shorter timeout due to known issues)
    success2 = test_anthropic_streaming_math()
    
    print("\n" + "=" * 60)
    print("📊 TEST SUMMARY:")
    print(f"   Non-streaming: {'✅ PASS' if success1 else '❌ FAIL'}")
    print(f"   Streaming: {'✅ PASS' if success2 else '❌ FAIL'}")
    
    if success1:
        print("\n🎉 The Anthropic API compatibility is working!")
        print("   Applications can now use Claude models through open_codegen!")
    else:
        print("\n⚠️  There may be an issue with the server or configuration.")
