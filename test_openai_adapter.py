#!/usr/bin/env python3
"""
Test script for OpenAI Codegen Adapter.
This script tests the basic functionality of the adapter by making requests to the endpoints.
"""

import os
import sys
import json
import time
import requests
import argparse
from typing import Dict, Any, Optional

# Default server URL
DEFAULT_SERVER_URL = "http://localhost:8887"

def test_health_endpoint(base_url: str) -> bool:
    """Test the health endpoint."""
    print("\n🔍 Testing health endpoint...")
    try:
        response = requests.get(f"{base_url}/health")
        response.raise_for_status()
        data = response.json()
        print(f"✅ Health endpoint response: {json.dumps(data, indent=2)}")
        return True
    except Exception as e:
        print(f"❌ Health endpoint error: {e}")
        return False

def test_models_endpoint(base_url: str) -> bool:
    """Test the models endpoint."""
    print("\n🔍 Testing models endpoint...")
    try:
        response = requests.get(f"{base_url}/v1/models")
        response.raise_for_status()
        data = response.json()
        print(f"✅ Models endpoint response: {json.dumps(data, indent=2)}")
        return True
    except Exception as e:
        print(f"❌ Models endpoint error: {e}")
        return False

def test_openai_chat_completion(base_url: str, timeout: int = 60) -> bool:
    """Test the OpenAI chat completion endpoint."""
    print("\n🔍 Testing OpenAI chat completion endpoint...")
    try:
        payload = {
            "model": "gpt-3.5-turbo",
            "messages": [
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": "Hello! Please respond with a short greeting."}
            ],
            "temperature": 0.7,
            "max_tokens": 50
        }
        
        print(f"📤 Request payload: {json.dumps(payload, indent=2)}")
        
        response = requests.post(
            f"{base_url}/v1/chat/completions", 
            json=payload,
            timeout=timeout
        )
        
        print(f"📥 Response status: {response.status_code}")
        print(f"📥 Response headers: {response.headers}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ OpenAI chat completion response: {json.dumps(data, indent=2)}")
            return True
        else:
            print(f"❌ OpenAI chat completion error: {response.text}")
            return False
    except requests.exceptions.Timeout:
        print(f"⏱️ OpenAI chat completion timed out after {timeout} seconds")
        return False
    except Exception as e:
        print(f"❌ OpenAI chat completion error: {e}")
        return False

def test_anthropic_completion(base_url: str, timeout: int = 60) -> bool:
    """Test the Anthropic completion endpoint."""
    print("\n🔍 Testing Anthropic completion endpoint...")
    try:
        payload = {
            "model": "claude-3-sonnet-20240229",
            "messages": [
                {"role": "user", "content": "Hello! Please respond with a short greeting."}
            ],
            "max_tokens": 50,
            "temperature": 0.7
        }
        
        print(f"📤 Request payload: {json.dumps(payload, indent=2)}")
        
        response = requests.post(
            f"{base_url}/v1/anthropic/completions", 
            json=payload,
            timeout=timeout
        )
        
        print(f"📥 Response status: {response.status_code}")
        print(f"📥 Response headers: {response.headers}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Anthropic completion response: {json.dumps(data, indent=2)}")
            return True
        else:
            print(f"❌ Anthropic completion error: {response.text}")
            return False
    except requests.exceptions.Timeout:
        print(f"⏱️ Anthropic completion timed out after {timeout} seconds")
        return False
    except Exception as e:
        print(f"❌ Anthropic completion error: {e}")
        return False

def test_gemini_completion(base_url: str, timeout: int = 60) -> bool:
    """Test the Gemini completion endpoint."""
    print("\n🔍 Testing Gemini completion endpoint...")
    try:
        payload = {
            "model": "gemini-1.5-pro",
            "contents": [
                {
                    "role": "user",
                    "parts": [{"text": "Hello! Please respond with a short greeting."}]
                }
            ],
            "max_output_tokens": 50,
            "temperature": 0.7
        }
        
        print(f"📤 Request payload: {json.dumps(payload, indent=2)}")
        
        response = requests.post(
            f"{base_url}/v1/gemini/completions", 
            json=payload,
            timeout=timeout
        )
        
        print(f"📥 Response status: {response.status_code}")
        print(f"📥 Response headers: {response.headers}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Gemini completion response: {json.dumps(data, indent=2)}")
            return True
        else:
            print(f"❌ Gemini completion error: {response.text}")
            return False
    except requests.exceptions.Timeout:
        print(f"⏱️ Gemini completion timed out after {timeout} seconds")
        return False
    except Exception as e:
        print(f"❌ Gemini completion error: {e}")
        return False

def test_streaming_chat_completion(base_url: str, timeout: int = 60) -> bool:
    """Test the OpenAI streaming chat completion endpoint."""
    print("\n🔍 Testing OpenAI streaming chat completion endpoint...")
    try:
        payload = {
            "model": "gpt-3.5-turbo",
            "messages": [
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": "Hello! Please respond with a short greeting."}
            ],
            "temperature": 0.7,
            "max_tokens": 50,
            "stream": True
        }
        
        print(f"📤 Request payload: {json.dumps(payload, indent=2)}")
        
        response = requests.post(
            f"{base_url}/v1/chat/completions", 
            json=payload,
            stream=True,
            timeout=timeout
        )
        
        print(f"📥 Response status: {response.status_code}")
        print(f"📥 Response headers: {response.headers}")
        
        if response.status_code == 200:
            print("📥 Streaming response chunks:")
            for chunk in response.iter_lines():
                if chunk:
                    decoded_chunk = chunk.decode('utf-8')
                    if decoded_chunk.startswith('data: '):
                        data = decoded_chunk[6:]
                        if data == '[DONE]':
                            print("✅ Stream completed with [DONE] marker")
                        else:
                            try:
                                json_data = json.loads(data)
                                print(f"📦 Chunk: {json.dumps(json_data, indent=2)}")
                            except json.JSONDecodeError:
                                print(f"⚠️ Non-JSON chunk: {data}")
            return True
        else:
            print(f"❌ OpenAI streaming chat completion error: {response.text}")
            return False
    except requests.exceptions.Timeout:
        print(f"⏱️ OpenAI streaming chat completion timed out after {timeout} seconds")
        return False
    except Exception as e:
        print(f"❌ OpenAI streaming chat completion error: {e}")
        return False

def run_all_tests(base_url: str, timeout: int = 60) -> None:
    """Run all tests."""
    print(f"🚀 Starting tests against server at {base_url}")
    print(f"⏱️ Request timeout set to {timeout} seconds")
    
    results = {
        "health": test_health_endpoint(base_url),
        "models": test_models_endpoint(base_url),
        "openai_chat": test_openai_chat_completion(base_url, timeout),
        "anthropic": test_anthropic_completion(base_url, timeout),
        "gemini": test_gemini_completion(base_url, timeout),
        "streaming": test_streaming_chat_completion(base_url, timeout)
    }
    
    print("\n📊 Test Results Summary:")
    for test_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} - {test_name}")
    
    total_tests = len(results)
    passed_tests = sum(1 for result in results.values() if result)
    
    print(f"\n🏁 {passed_tests}/{total_tests} tests passed")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Test OpenAI Codegen Adapter")
    parser.add_argument("--url", default=DEFAULT_SERVER_URL, help=f"Server URL (default: {DEFAULT_SERVER_URL})")
    parser.add_argument("--timeout", type=int, default=60, help="Request timeout in seconds (default: 60)")
    parser.add_argument("--test", choices=["health", "models", "openai", "anthropic", "gemini", "streaming", "all"], 
                        default="all", help="Specific test to run (default: all)")
    
    args = parser.parse_args()
    
    if args.test == "all":
        run_all_tests(args.url, args.timeout)
    elif args.test == "health":
        test_health_endpoint(args.url)
    elif args.test == "models":
        test_models_endpoint(args.url)
    elif args.test == "openai":
        test_openai_chat_completion(args.url, args.timeout)
    elif args.test == "anthropic":
        test_anthropic_completion(args.url, args.timeout)
    elif args.test == "gemini":
        test_gemini_completion(args.url, args.timeout)
    elif args.test == "streaming":
        test_streaming_chat_completion(args.url, args.timeout)

