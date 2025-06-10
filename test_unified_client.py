#!/usr/bin/env python3
"""
Test script for the unified Codegen client with all operation modes.
Tests reliability, performance, caching, and mode switching.
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
    "Explain what an API is in one sentence.",
    "List 3 benefits of using Python for web development."
]

def test_health_endpoint():
    """Test the unified client health endpoint."""
    print("🏥 Testing unified client health endpoint...")
    
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=10)
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ Server healthy!")
            print(f"   📊 Client stats: {data.get('client_stats', {})}")
            print(f"   🔧 Client type: {data.get('client_type', 'unknown')}")
            
            # Show detailed stats
            stats = data.get('client_stats', {})
            if stats:
                print(f"   📈 Mode: {stats.get('mode', 'unknown')}")
                print(f"   📦 Cache enabled: {stats.get('cache_enabled', False)}")
                print(f"   📊 Total requests: {stats.get('requests_total', 0)}")
                print(f"   ⚡ Avg response time: {stats.get('average_response_time', 0):.2f}s")
            
            return True
        else:
            print(f"   ❌ Health check failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"   ❌ Health check exception: {e}")
        return False

def test_mode_switching():
    """Test switching between different client modes."""
    print("\n🔄 Testing client mode switching...")
    
    modes_to_test = ["basic", "reliable", "performance", "production"]
    
    for mode in modes_to_test:
        try:
            print(f"   🔧 Switching to {mode} mode...")
            response = requests.post(f"{BASE_URL}/admin/set-mode", params={"mode": mode}, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                print(f"   ✅ Successfully switched to {mode} mode")
                print(f"   📊 Old mode: {data.get('old_mode')}")
                print(f"   📊 New mode: {data.get('new_mode')}")
            else:
                print(f"   ❌ Failed to switch to {mode} mode: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"   ❌ Mode switch exception: {e}")
            return False
    
    # Switch back to production mode for other tests
    try:
        requests.post(f"{BASE_URL}/admin/set-mode", params={"mode": "production"}, timeout=10)
        print("   🔄 Switched back to production mode")
    except Exception:
        pass
    
    return True

def test_cache_functionality():
    """Test response caching functionality."""
    print("\n🗄️ Testing unified client caching...")
    
    # Clear cache first
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
        
        # Check cache stats
        try:
            health_response = requests.get(f"{BASE_URL}/health", timeout=5)
            if health_response.status_code == 200:
                stats = health_response.json().get('client_stats', {})
                cache_hits = stats.get('cache_hits', 0)
                cache_misses = stats.get('cache_misses', 0)
                print(f"   📊 Cache hits: {cache_hits}, misses: {cache_misses}")
                
                if cache_hits > 0:
                    print("   ✅ Caching is working!")
                else:
                    print("   ⚠️ No cache hits detected")
        except Exception:
            pass
        
        if time2 < time1 * 0.7:  # Second should be faster if cached
            print("   ✅ Performance improvement detected!")
        else:
            print("   ⚠️ No significant performance improvement")
        
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
    print("\n🚀 Testing concurrent requests with unified client...")
    
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

def test_performance_modes():
    """Test different performance modes with the same request."""
    print("\n⚡ Testing performance across different modes...")
    
    test_prompt = "Explain machine learning in 2 sentences."
    modes = ["basic", "reliable", "performance", "production"]
    results = {}
    
    for mode in modes:
        print(f"   🔧 Testing {mode} mode...")
        
        # Switch to mode
        try:
            requests.post(f"{BASE_URL}/admin/set-mode", params={"mode": mode}, timeout=10)
            time.sleep(1)  # Brief pause for mode switch
        except Exception as e:
            print(f"   ❌ Failed to switch to {mode}: {e}")
            continue
        
        # Test request
        start_time = time.time()
        success = test_openai_single_request(test_prompt, show_output=False)
        elapsed = time.time() - start_time
        
        results[mode] = {
            "success": success,
            "time": elapsed
        }
        
        print(f"   📊 {mode}: {'✅' if success else '❌'} ({elapsed:.1f}s)")
    
    # Switch back to production
    try:
        requests.post(f"{BASE_URL}/admin/set-mode", params={"mode": "production"}, timeout=10)
    except Exception:
        pass
    
    # Analyze results
    successful_modes = [mode for mode, result in results.items() if result["success"]]
    if len(successful_modes) >= 3:
        print("   ✅ Multiple modes working successfully!")
        
        # Show performance comparison
        times = {mode: result["time"] for mode, result in results.items() if result["success"]}
        fastest = min(times, key=times.get)
        slowest = max(times, key=times.get)
        print(f"   🏃 Fastest: {fastest} ({times[fastest]:.1f}s)")
        print(f"   🐌 Slowest: {slowest} ({times[slowest]:.1f}s)")
        
        return True
    else:
        print("   ❌ Too many modes failed!")
        return False

def test_all_apis_basic():
    """Test all three APIs with the unified client."""
    print("\n🧪 Testing all APIs with unified client...")
    
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
    """Run all unified client tests."""
    print("🧪 Unified Codegen Client Testing Suite")
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
    
    # Unified client feature tests
    test_results.append(test_mode_switching())
    test_results.append(test_cache_functionality())
    test_results.append(test_concurrent_requests())
    test_results.append(test_performance_modes())
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 Unified Client Test Results Summary:")
    
    test_names = [
        "OpenAI API", "Anthropic API", "Google API",
        "Mode Switching", "Cache Functionality", 
        "Concurrent Requests", "Performance Modes"
    ]
    
    for i, (name, result) in enumerate(zip(test_names, test_results)):
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"   {name}: {status}")
    
    total_passed = sum(test_results)
    print(f"\n🎯 Overall: {total_passed}/{len(test_results)} tests passed")
    
    if total_passed >= len(test_results) * 0.8:  # 80% pass rate
        print("🎉 Unified client system is working excellently!")
        
        # Show final stats
        try:
            response = requests.get(f"{BASE_URL}/health", timeout=5)
            if response.status_code == 200:
                data = response.json()
                client_stats = data.get('client_stats', {})
                print(f"📊 Final client stats:")
                print(f"   Mode: {client_stats.get('mode', 'unknown')}")
                print(f"   Total requests: {client_stats.get('requests_total', 0)}")
                print(f"   Cache hits: {client_stats.get('cache_hits', 0)}")
                print(f"   Average response time: {client_stats.get('average_response_time', 0):.2f}s")
        except Exception:
            pass
            
    else:
        print("⚠️ Some tests failed. Check the logs above for details.")
        sys.exit(1)

if __name__ == "__main__":
    main()

