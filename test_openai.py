#!/usr/bin/env python3
"""
Test script for OpenAI API endpoint
"""
import requests
import json
import argparse
import sys
import time
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

def create_session_with_retries():
    """Create a requests session with retry strategy and timeout handling"""
    session = requests.Session()
    
    # Define retry strategy
    retry_strategy = Retry(
        total=3,
        backoff_factor=1,
        status_forcelist=[429, 500, 502, 503, 504],
    )
    
    # Mount adapter with retry strategy
    adapter = HTTPAdapter(max_retries=retry_strategy)
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    
    return session

def test_openai_api(base_url="http://localhost:8887/v1", model="gpt-3.5-turbo", prompt="Hello! Please respond with just 'Hi there!'", timeout=15):
    """Test OpenAI API endpoint with improved timeout handling"""
    
    endpoint = f"{base_url}/chat/completions"
    
    headers = {
        "Content-Type": "application/json",
        "Authorization": "Bearer dummy-key"  # The server doesn't validate this
    }
    
    data = {
        "model": model,
        "messages": [
            {"role": "user", "content": prompt}
        ],
        "max_tokens": 50,
        "temperature": 0.7
    }
    
    session = create_session_with_retries()
    
    try:
        print(f"🤖 Testing OpenAI API")
        print(f"📍 Endpoint: {endpoint}")
        print(f"🎯 Model: {model}")
        print(f"💬 Prompt: {prompt}")
        print(f"⏱️ Timeout: {timeout}s")
        print("🔄 Making request...")
        
        start_time = time.time()
        
        response = session.post(
            endpoint,
            headers=headers,
            json=data,
            timeout=timeout  # Set explicit timeout
        )
        
        end_time = time.time()
        duration = end_time - start_time
        
        print(f"⏱️ Request completed in {duration:.2f}s")
        
        if response.status_code == 200:
            result = response.json()
            content = result.get('choices', [{}])[0].get('message', {}).get('content', '')
            usage = result.get('usage', {})
            
            return {
                "success": True,
                "service": "OpenAI",
                "endpoint": endpoint,
                "model": model,
                "prompt": prompt,
                "response": content,
                "duration": duration,
                "usage": usage,
                "status_code": response.status_code
            }
        else:
            return {
                "success": False,
                "service": "OpenAI",
                "endpoint": endpoint,
                "model": model,
                "prompt": prompt,
                "response": "",
                "error": response.text,
                "duration": duration,
                "status_code": response.status_code,
                "usage": {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}
            }
            
    except requests.exceptions.Timeout:
        return {
            "success": False,
            "service": "OpenAI",
            "endpoint": endpoint,
            "model": model,
            "prompt": prompt,
            "response": "",
            "error": f"Request timed out after {timeout} seconds",
            "duration": timeout,
            "status_code": 0,
            "usage": {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}
        }
    except requests.exceptions.ConnectionError as e:
        return {
            "success": False,
            "service": "OpenAI",
            "endpoint": endpoint,
            "model": model,
            "prompt": prompt,
            "response": "",
            "error": f"Connection error: {str(e)}",
            "duration": 0,
            "status_code": 0,
            "usage": {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}
        }
    except Exception as e:
        return {
            "success": False,
            "service": "OpenAI",
            "endpoint": endpoint,
            "model": model,
            "prompt": prompt,
            "response": "",
            "error": str(e),
            "duration": 0,
            "status_code": 0,
            "usage": {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}
        }

def main():
    """Main entry point for CLI usage."""
    parser = argparse.ArgumentParser(description="Test OpenAI API endpoint")
    parser.add_argument("--prompt", default="Hello! Please respond with just 'Hi there!'", help="Custom prompt to test with")
    parser.add_argument("--base-url", default="http://localhost:8887/v1", help="Custom base URL for the API")
    parser.add_argument("--model", default="gpt-3.5-turbo", help="Model to use for the test")
    parser.add_argument("--timeout", type=int, default=15, help="Request timeout in seconds")
    parser.add_argument("--json", action="store_true", help="Output JSON format")
    
    args = parser.parse_args()
    
    result = test_openai_api(
        base_url=args.base_url,
        model=args.model,
        prompt=args.prompt,
        timeout=args.timeout
    )
    
    if args.json:
        print(json.dumps(result, indent=2))
    else:
        if result["success"]:
            print(f"✅ Success! Response: {result['response']}")
            print(f"📊 Usage: {result['usage']}")
            print(f"⏱️ Duration: {result['duration']:.2f}s")
        else:
            print(f"❌ Failed: {result['error']}")
            sys.exit(1)

if __name__ == "__main__":
    main()
