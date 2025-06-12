#!/usr/bin/env python3
"""
Quick test script to verify server functionality
"""
import requests
import json
import time

def test_server():
    """Test basic server functionality"""
    base_url = "http://localhost:8887"
    
    tests = [
        {
            "name": "Health Check",
            "url": f"{base_url}/health",
            "method": "GET",
            "timeout": 5
        },
        {
            "name": "Models Endpoint",
            "url": f"{base_url}/v1/models",
            "method": "GET", 
            "timeout": 5
        },
        {
            "name": "Web UI",
            "url": f"{base_url}/",
            "method": "GET",
            "timeout": 5
        }
    ]
    
    results = []
    
    for test in tests:
        print(f"🧪 Testing {test['name']}...")
        try:
            start_time = time.time()
            
            if test['method'] == 'GET':
                response = requests.get(test['url'], timeout=test['timeout'])
            else:
                response = requests.post(test['url'], timeout=test['timeout'])
            
            duration = time.time() - start_time
            
            if response.status_code == 200:
                print(f"✅ {test['name']}: SUCCESS ({duration:.2f}s)")
                results.append({
                    "test": test['name'],
                    "success": True,
                    "status_code": response.status_code,
                    "duration": duration
                })
            else:
                print(f"❌ {test['name']}: FAILED (Status: {response.status_code})")
                results.append({
                    "test": test['name'],
                    "success": False,
                    "status_code": response.status_code,
                    "duration": duration,
                    "error": f"HTTP {response.status_code}"
                })
                
        except requests.exceptions.Timeout:
            print(f"⏰ {test['name']}: TIMEOUT after {test['timeout']}s")
            results.append({
                "test": test['name'],
                "success": False,
                "status_code": 0,
                "duration": test['timeout'],
                "error": "Timeout"
            })
        except Exception as e:
            print(f"❌ {test['name']}: ERROR - {str(e)}")
            results.append({
                "test": test['name'],
                "success": False,
                "status_code": 0,
                "duration": 0,
                "error": str(e)
            })
    
    # Summary
    successful = sum(1 for r in results if r['success'])
    total = len(results)
    
    print(f"\n📊 Test Summary: {successful}/{total} tests passed")
    
    if successful == total:
        print("🎉 All tests passed! Server is working correctly.")
        return True
    else:
        print("⚠️ Some tests failed. Check the server configuration.")
        return False

if __name__ == "__main__":
    test_server()

