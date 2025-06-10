#!/usr/bin/env python3
"""
Test Context Retrieval Functionality
====================================

Test script to verify the context retrieval endpoints and functionality.
Tests both the direct integration and the API endpoints.
"""

import os
import sys
import json
import time
import requests
import argparse
from typing import Dict, Any

def test_direct_integration():
    """Test the direct integration module"""
    print("🧪 Testing Direct Integration...")
    
    try:
        from codegen_integration import CodegenClient, get_agent_response_for_context
        
        # Test environment setup
        org_id = os.getenv('CODEGEN_ORG_ID')
        token = os.getenv('CODEGEN_TOKEN')
        
        if not org_id or not token:
            print("❌ Missing environment variables:")
            print(f"   - CODEGEN_ORG_ID: {'✅' if org_id else '❌'}")
            print(f"   - CODEGEN_TOKEN: {'✅' if token else '❌'}")
            return False
        
        print(f"✅ Environment configured (Org ID: {org_id})")
        
        # Test simple context retrieval
        print("🔄 Testing simple context retrieval...")
        context = get_agent_response_for_context(
            "Hello! Please respond with a brief greeting and confirm you can help with code analysis.",
            max_length=500,
            timeout=60
        )
        
        if context:
            print(f"✅ Context retrieved: {len(context)} characters")
            print(f"📝 Preview: {context[:150]}...")
            return True
        else:
            print("❌ No context retrieved")
            return False
            
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False

def test_api_endpoints(base_url: str = "http://localhost:8887"):
    """Test the API endpoints"""
    print(f"🌐 Testing API Endpoints at {base_url}...")
    
    # Test 1: Synchronous context retrieval
    print("🔄 Testing /api/context/retrieve endpoint...")
    
    try:
        response = requests.post(
            f"{base_url}/api/context/retrieve",
            json={
                "prompt": "Hello! Please respond with a brief greeting.",
                "max_length": 500,
                "timeout": 60
            },
            timeout=70
        )
        
        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                print(f"✅ Sync retrieval successful: {data.get('length', 0)} characters")
                print(f"📝 Preview: {data.get('context_text', '')[:100]}...")
                
                # Test 2: Status check endpoint
                agent_run_id = data.get('agent_run_id')
                if agent_run_id:
                    print(f"🔄 Testing status endpoint for agent run {agent_run_id}...")
                    
                    status_response = requests.get(
                        f"{base_url}/api/context/status/{agent_run_id}",
                        timeout=10
                    )
                    
                    if status_response.status_code == 200:
                        status_data = status_response.json()
                        print(f"✅ Status check successful: {status_data.get('status')}")
                    else:
                        print(f"❌ Status check failed: {status_response.status_code}")
                
                return True
            else:
                print(f"❌ Sync retrieval failed: {data.get('error')}")
                return False
        else:
            print(f"❌ API request failed: {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
    except requests.exceptions.Timeout:
        print("⏰ API request timed out")
        return False
    except Exception as e:
        print(f"❌ API test failed: {e}")
        return False

def test_async_endpoints(base_url: str = "http://localhost:8887"):
    """Test the async create/status endpoints"""
    print(f"🔄 Testing Async Endpoints at {base_url}...")
    
    try:
        # Test 1: Create async agent run
        print("🚀 Creating async agent run...")
        
        create_response = requests.post(
            f"{base_url}/api/context/create",
            json={
                "prompt": "Please analyze the concept of microservices architecture and provide a brief summary."
            },
            timeout=30
        )
        
        if create_response.status_code == 200:
            create_data = create_response.json()
            if create_data.get('success'):
                agent_run_id = create_data.get('agent_run_id')
                print(f"✅ Agent run created: {agent_run_id}")
                print(f"🔗 Web URL: {create_data.get('web_url')}")
                
                # Test 2: Poll for completion
                print("⏳ Polling for completion...")
                max_polls = 12  # 2 minutes with 10s intervals
                
                for i in range(max_polls):
                    time.sleep(10)
                    
                    status_response = requests.get(
                        f"{base_url}/api/context/status/{agent_run_id}",
                        timeout=10
                    )
                    
                    if status_response.status_code == 200:
                        status_data = status_response.json()
                        status = status_data.get('status', 'unknown')
                        
                        print(f"📊 Poll {i+1}: Status = {status}")
                        
                        if status.lower() in ['completed', 'failed', 'cancelled']:
                            if status.lower() == 'completed':
                                context_text = status_data.get('context_text', '')
                                print(f"✅ Async completion successful: {len(context_text)} characters")
                                print(f"📝 Preview: {context_text[:150]}...")
                                return True
                            else:
                                print(f"❌ Agent run failed with status: {status}")
                                return False
                    else:
                        print(f"❌ Status check failed: {status_response.status_code}")
                
                print("⏰ Async test timed out")
                return False
            else:
                print(f"❌ Agent run creation failed: {create_data.get('error')}")
                return False
        else:
            print(f"❌ Create request failed: {create_response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Async test failed: {e}")
        return False

def test_server_availability(base_url: str = "http://localhost:8887"):
    """Test if the server is running and accessible"""
    print(f"🔍 Checking server availability at {base_url}...")
    
    try:
        response = requests.get(f"{base_url}/health", timeout=5)
        if response.status_code == 200:
            print("✅ Server is running and accessible")
            return True
        else:
            print(f"❌ Server responded with status: {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to server. Is it running?")
        return False
    except Exception as e:
        print(f"❌ Server check failed: {e}")
        return False

def main():
    """Main test runner"""
    parser = argparse.ArgumentParser(description="Test context retrieval functionality")
    parser.add_argument("--base-url", default="http://localhost:8887", help="Server base URL")
    parser.add_argument("--skip-direct", action="store_true", help="Skip direct integration tests")
    parser.add_argument("--skip-api", action="store_true", help="Skip API endpoint tests")
    parser.add_argument("--skip-async", action="store_true", help="Skip async endpoint tests")
    parser.add_argument("--server-only", action="store_true", help="Only test server availability")
    
    args = parser.parse_args()
    
    print("🧪 Context Retrieval Test Suite")
    print("=" * 50)
    
    results = []
    
    # Test server availability first
    server_available = test_server_availability(args.base_url)
    results.append(("Server Availability", server_available))
    
    if args.server_only:
        print("\n📊 Test Results:")
        for test_name, result in results:
            status = "✅ PASS" if result else "❌ FAIL"
            print(f"   {test_name}: {status}")
        return
    
    # Test direct integration
    if not args.skip_direct:
        print("\n" + "=" * 50)
        direct_result = test_direct_integration()
        results.append(("Direct Integration", direct_result))
    
    # Test API endpoints (only if server is available)
    if server_available and not args.skip_api:
        print("\n" + "=" * 50)
        api_result = test_api_endpoints(args.base_url)
        results.append(("API Endpoints", api_result))
    
    # Test async endpoints (only if server is available)
    if server_available and not args.skip_async:
        print("\n" + "=" * 50)
        async_result = test_async_endpoints(args.base_url)
        results.append(("Async Endpoints", async_result))
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 Test Results:")
    
    passed = 0
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"   {test_name}: {status}")
        if result:
            passed += 1
    
    print(f"\n🎯 Overall: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Context retrieval is working correctly.")
        sys.exit(0)
    else:
        print("⚠️ Some tests failed. Check the configuration and server status.")
        sys.exit(1)

if __name__ == "__main__":
    main()

