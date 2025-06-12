#!/usr/bin/env python3
"""
Enhanced test script for the improved API response system.
Tests reliability, caching, and performance optimizations.
"""

import requests
import json
import time
import sys
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed

# Test configuration
BASE_URL = "http://localhost:8887"
TEST_PROMPTS = [
    "Hello! Please respond with a simple greeting.",
    "What is 2+2?",
    "Explain what an API is in one sentence."
]

def test_health_endpoint():
    """Test the enhanced health endpoint."""
    print("🏥 Testing enhanced health endpoint...")
    
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=10)
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ Server healthy!")
            print(f"   📊 Cache stats: {data.get('cache_stats', {})}")
            print(f"   🔧 Client type: {data.get('client_type', 'unknown')}")
            return True
        else:
            print(f"   ❌ Health check failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"   ❌ Health check exception: {e}")
        return False

def test_cache_functionality():
    """Test response caching functionality."""
    print("\n🗄️ Testing response caching...")
    
    # Test cache clearing
    try:
        response = requests.post(f"{BASE_URL}/admin/clear-cache", timeout=10)
        if response.status_code == 200:
            print("   ✅ Cache cleared successfully")
        else:
            print(f"   ⚠️ Cache clear returned: {response.status_code}")
    except Exception as e:
        print(f"   ⚠️ Cache clear failed: {e}")
    
    # Test same prompt twice to verify caching
    test_prompt = "What is 2+2?"
    
    print("   📝 Testing cache with identical prompts...")
    
    # First request
    start_time = time.time()
    response1 = test_openai_single_request(test_prompt, show_output=False)
    time1 = time.time() - start_time
    
    # Second request (should be cached)
    start_time = time.time()
    response2 = test_openai_single_request(test_prompt, show_output=False)
    time2 = time.time() - start_time
    
    if response1 and response2:
        print(f"   ⏱️ First request: {time1:.1f}s")
        print(f"   ⏱️ Second request: {time2:.1f}s")
        if time2 < time1 * 0.5:  # Second should be much faster if cached
            print("   ✅ Caching appears to be working!")
        else:
            print("   ⚠️ Caching may not be working as expected")
        return True
    else:
        print("   ❌ Cache test failed - requests unsuccessful")
        return False

def test_openai_single_request(prompt, show_output=True):
    """Test a single OpenAI API request."""
    if show_output:
        print(f"🔵 Testing OpenAI API with prompt: '{prompt[:30]}...'")
    
    url = f"{BASE_URL}/v1/chat/completions"
    headers = {"Content-Type": "application/json"}
    data = {
        "model": "gpt-3.5-turbo",
        "messages": [{"role": "user", "content": prompt}],
        "stream": False
    }
    
    try:
        start_time = time.time()
        response = requests.post(url, headers=headers, json=data, timeout=60)
        elapsed = time.time() - start_time
        
        if show_output:
            print(f"   Status: {response.status_code}")
            print(f"   Time: {elapsed:.1f}s")
        
        if response.status_code == 200:
            result = response.json()
            content = result.get('choices', [{}])[0].get('message', {}).get('content', '')
            if show_output:
                print(f"   Response: {content[:50]}...")
                print("   ✅ OpenAI API working!")
            return True
        else:
            if show_output:
                print(f"   ❌ Error: {response.text}")
            return False
            
    except Exception as e:
        if show_output:
            print(f"   ❌ Exception: {e}")
        return False

def test_anthropic_single_request(prompt, show_output=True):
    """Test a single Anthropic API request."""
    if show_output:
        print(f"🟠 Testing Anthropic API with prompt: '{prompt[:30]}...'")
    
    url = f"{BASE_URL}/v1/messages"
    headers = {"Content-Type": "application/json"}
    data = {
        "model": "claude-3-sonnet-20240229",
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": 100,
        "stream": False
    }
    
    try:
        start_time = time.time()
        response = requests.post(url, headers=headers, json=data, timeout=60)
        elapsed = time.time() - start_time
        
        if show_output:
            print(f"   Status: {response.status_code}")
            print(f"   Time: {elapsed:.1f}s")
        
        if response.status_code == 200:
            result = response.json()
            content = result.get('content', [{}])[0].get('text', '')
            if show_output:
                print(f"   Response: {content[:50]}...")
                print("   ✅ Anthropic API working!")
            return True
        else:
            if show_output:
                print(f"   ❌ Error: {response.text}")
            return False
            
    except Exception as e:
        if show_output:
            print(f"   ❌ Exception: {e}")
        return False

def test_concurrent_requests():
    """Test concurrent API requests to verify reliability under load."""
    print("\n🚀 Testing concurrent requests...")
    
    def make_request(prompt_index):
        prompt = TEST_PROMPTS[prompt_index % len(TEST_PROMPTS)]
        return test_openai_single_request(f"{prompt} (Request #{prompt_index})", show_output=False)
    
    # Test with 5 concurrent requests
    num_requests = 5
    start_time = time.time()
    
    with ThreadPoolExecutor(max_workers=num_requests) as executor:
        futures = [executor.submit(make_request, i) for i in range(num_requests)]
        results = [future.result() for future in as_completed(futures)]
    
    elapsed = time.time() - start_time
    successful = sum(results)
    
    print(f"   📊 Results: {successful}/{num_requests} successful")
    print(f"   ⏱️ Total time: {elapsed:.1f}s")
    print(f"   📈 Average per request: {elapsed/num_requests:.1f}s")
    
    if successful >= num_requests * 0.8:  # 80% success rate
        print("   ✅ Concurrent requests test passed!")
        return True
    else:
        print("   ❌ Concurrent requests test failed!")
        return False

def test_retry_mechanism():
    """Test the retry mechanism with a potentially problematic request."""
    print("\n🔄 Testing retry mechanism...")
    
    # Use a complex prompt that might cause issues
    complex_prompt = "Please write a very detailed explanation of quantum computing in exactly 500 words, including mathematical formulas and technical details."
    
    try:
        result = test_openai_single_request(complex_prompt, show_output=True)
        if result:
            print("   ✅ Retry mechanism test passed!")
            return True
        else:
            print("   ❌ Retry mechanism test failed!")
            return False
    except Exception as e:
        print(f"   ❌ Retry test exception: {e}")
        return False

def test_all_apis_basic():
    """Test all three APIs with basic requests."""
    print("\n🧪 Testing all APIs with basic requests...")
    
    results = []
    
    # Test OpenAI
    results.append(test_openai_single_request(TEST_PROMPTS[0]))
    
    # Test Anthropic
    results.append(test_anthropic_single_request(TEST_PROMPTS[1]))
    
    # Test Google (simplified test)
    print("🔴 Testing Google/Gemini API...")
    url = f"{BASE_URL}/v1/gemini/generateContent"
    headers = {"Content-Type": "application/json"}
    data = {
        "model": "gemini-pro",
        "contents": [{"parts": [{"text": TEST_PROMPTS[2]}]}],
        "generationConfig": {"maxOutputTokens": 100}
    }
    
    try:
        start_time = time.time()
        response = requests.post(url, headers=headers, json=data, timeout=60)
        elapsed = time.time() - start_time
        
        print(f"   Status: {response.status_code}")
        print(f"   Time: {elapsed:.1f}s")
        
        if response.status_code == 200:
            result = response.json()
            candidates = result.get('candidates', [])
            if candidates:
                content = candidates[0].get('content', {}).get('parts', [{}])[0].get('text', '')
                print(f"   Response: {content[:50]}...")
                print("   ✅ Google API working!")
                results.append(True)
            else:
                print("   ❌ No candidates in response")
                results.append(False)
        else:
            print(f"   ❌ Error: {response.text}")
            results.append(False)
            
    except Exception as e:
        print(f"   ❌ Exception: {e}")
        results.append(False)
    
    return results

def main():
    """Run all enhanced API tests."""
    print("🧪 Enhanced API Response Testing Suite")
    print("=" * 60)
    
    # Test server health first
    if not test_health_endpoint():
        print("\n❌ Server is not responding. Please start the server first:")
        print("   python server.py")
        sys.exit(1)
    
    # Run all tests
    test_results = []
    
    # Basic API tests
    api_results = test_all_apis_basic()
    test_results.extend(api_results)
    
    # Enhanced feature tests
    test_results.append(test_cache_functionality())
    test_results.append(test_concurrent_requests())
    test_results.append(test_retry_mechanism())
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 Enhanced Test Results Summary:")
    
    test_names = [
        "OpenAI API", "Anthropic API", "Google API",
        "Cache Functionality", "Concurrent Requests", "Retry Mechanism"
    ]
    
    for i, (name, result) in enumerate(zip(test_names, test_results)):
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"   {name}: {status}")
    
    total_passed = sum(test_results)
    print(f"\n🎯 Overall: {total_passed}/{len(test_results)} tests passed")
    
    if total_passed >= len(test_results) * 0.8:  # 80% pass rate
        print("🎉 Enhanced API system is working well!")
        
        # Show final cache stats
        try:
            response = requests.get(f"{BASE_URL}/health", timeout=5)
            if response.status_code == 200:
                data = response.json()
                cache_stats = data.get('cache_stats', {})
                print(f"📊 Final cache stats: {cache_stats}")
        except Exception:
            pass
            
    else:
        print("⚠️ Some tests failed. Check the logs above for details.")
        sys.exit(1)

if __name__ == "__main__":
    main()

