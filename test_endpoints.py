#!/usr/bin/env python3
"""
Test script to validate all OpenAI Codegen Adapter endpoints
"""

import json
import requests
import time
from typing import Dict, Any

# Server configuration
BASE_URL = "http://127.0.0.1:19887"
HEADERS = {
    "Content-Type": "application/json",
    "Authorization": "Bearer sk-ce027fa7-3c8d-4beb-8c86-ed8ae982ac99"
}

def test_endpoint(method: str, endpoint: str, data: Dict[Any, Any] = None, stream: bool = False) -> Dict[str, Any]:
    """Test a single endpoint and return results"""
    url = f"{BASE_URL}{endpoint}"
    
    try:
        print(f"🔍 Testing {method} {endpoint}")
        
        if method.upper() == "GET":
            response = requests.get(url, headers=HEADERS, timeout=10)
        elif method.upper() == "POST":
            if stream:
                response = requests.post(url, headers=HEADERS, json=data, stream=True, timeout=30)
            else:
                response = requests.post(url, headers=HEADERS, json=data, timeout=30)
        else:
            return {"status": "error", "message": f"Unsupported method: {method}"}
        
        result = {
            "endpoint": endpoint,
            "method": method,
            "status_code": response.status_code,
            "success": response.status_code < 400,
            "headers": dict(response.headers),
        }
        
        if stream and response.status_code == 200:
            # For streaming responses, read first few chunks
            chunks = []
            try:
                for i, line in enumerate(response.iter_lines(decode_unicode=True)):
                    if line and i < 3:  # Read first 3 chunks
                        chunks.append(line)
                    if i >= 3:
                        break
                result["response"] = {"chunks": chunks, "streaming": True}
            except Exception as e:
                result["response"] = {"error": f"Streaming error: {e}"}
        else:
            # For non-streaming responses
            try:
                if response.headers.get('content-type', '').startswith('application/json'):
                    result["response"] = response.json()
                else:
                    result["response"] = response.text[:500]  # Truncate long responses
            except Exception as e:
                result["response"] = {"error": f"Parse error: {e}", "raw": response.text[:200]}
        
        return result
        
    except requests.exceptions.Timeout:
        return {
            "endpoint": endpoint,
            "method": method,
            "status": "error",
            "message": "Request timeout"
        }
    except requests.exceptions.ConnectionError:
        return {
            "endpoint": endpoint,
            "method": method,
            "status": "error",
            "message": "Connection error - server may not be running"
        }
    except Exception as e:
        return {
            "endpoint": endpoint,
            "method": method,
            "status": "error",
            "message": f"Unexpected error: {e}"
        }

def main():
    """Test all endpoints"""
    print("🧪 OpenAI Codegen Adapter - Endpoint Testing")
    print("=" * 60)
    
    # Test cases
    test_cases = [
        # Health check
        {
            "method": "GET",
            "endpoint": "/health",
            "description": "Health check endpoint"
        },
        
        # OpenAI API compatibility endpoints
        {
            "method": "GET",
            "endpoint": "/v1/models",
            "description": "List available models"
        },
        
        # Chat completions (non-streaming)
        {
            "method": "POST",
            "endpoint": "/v1/chat/completions",
            "description": "Chat completion (non-streaming)",
            "data": {
                "model": "gpt-4",
                "messages": [
                    {"role": "user", "content": "Hello, this is a test message. Please respond briefly."}
                ],
                "max_tokens": 50,
                "stream": False
            }
        },
        
        # Chat completions (streaming)
        {
            "method": "POST",
            "endpoint": "/v1/chat/completions",
            "description": "Chat completion (streaming)",
            "data": {
                "model": "gpt-4",
                "messages": [
                    {"role": "user", "content": "Hello, this is a streaming test. Please respond briefly."}
                ],
                "max_tokens": 50,
                "stream": True
            },
            "stream": True
        },
        
        # Completions (non-streaming)
        {
            "method": "POST",
            "endpoint": "/v1/completions",
            "description": "Text completion (non-streaming)",
            "data": {
                "model": "gpt-3.5-turbo-instruct",
                "prompt": "The capital of France is",
                "max_tokens": 10,
                "stream": False
            }
        },
        
        # Completions (streaming)
        {
            "method": "POST",
            "endpoint": "/v1/completions",
            "description": "Text completion (streaming)",
            "data": {
                "model": "gpt-3.5-turbo-instruct",
                "prompt": "The capital of France is",
                "max_tokens": 10,
                "stream": True
            },
            "stream": True
        }
    ]
    
    results = []
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n[{i}/{len(test_cases)}] {test_case['description']}")
        print("-" * 40)
        
        result = test_endpoint(
            method=test_case["method"],
            endpoint=test_case["endpoint"],
            data=test_case.get("data"),
            stream=test_case.get("stream", False)
        )
        
        results.append(result)
        
        # Print result summary
        if result.get("success"):
            print(f"✅ Status: {result['status_code']} - SUCCESS")
            if "response" in result:
                if isinstance(result["response"], dict) and "chunks" in result["response"]:
                    print(f"📡 Streaming response received ({len(result['response']['chunks'])} chunks)")
                elif isinstance(result["response"], dict):
                    print(f"📄 Response keys: {list(result['response'].keys())}")
                else:
                    print(f"📄 Response: {str(result['response'])[:100]}...")
        else:
            print(f"❌ Status: {result.get('status_code', 'N/A')} - FAILED")
            if "message" in result:
                print(f"💬 Error: {result['message']}")
            elif "response" in result:
                print(f"💬 Response: {result['response']}")
        
        # Small delay between requests
        time.sleep(1)
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 TEST SUMMARY")
    print("=" * 60)
    
    successful = sum(1 for r in results if r.get("success"))
    total = len(results)
    
    print(f"Total Tests: {total}")
    print(f"Successful: {successful}")
    print(f"Failed: {total - successful}")
    print(f"Success Rate: {(successful/total)*100:.1f}%")
    
    # Detailed results
    print(f"\n📋 Detailed Results:")
    for result in results:
        status = "✅ PASS" if result.get("success") else "❌ FAIL"
        endpoint = result.get("endpoint", "Unknown")
        method = result.get("method", "Unknown")
        status_code = result.get("status_code", "N/A")
        print(f"  {status} {method} {endpoint} ({status_code})")
    
    # Configuration info
    print(f"\n🔧 Configuration Used:")
    print(f"  Server: {BASE_URL}")
    print(f"  Org ID: 323")
    print(f"  API Token: ***{HEADERS['Authorization'][-4:]}")
    
    if successful == total:
        print(f"\n🎉 All endpoints are working correctly!")
        return True
    else:
        print(f"\n⚠️  Some endpoints failed. Check the details above.")
        return False

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)

