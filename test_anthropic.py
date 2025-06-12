#!/usr/bin/env python3
"""
Anthropic API Test
=================

Comprehensive test for Anthropic Claude API through the Codegen adapter.
Supports both CLI and UI integration with custom prompts.
"""

import os
import sys
import json
import argparse
import requests

def test_anthropic_api(prompt=None, base_url=None, model=None):
    """
    Test the Anthropic API endpoint with custom or default parameters.
    
    Args:
        prompt (str): Custom prompt to test with
        base_url (str): Custom base URL for the API
        model (str): Model to use for the test
    
    Returns:
        dict: Test result with success status, response, and metadata
    """
    # Default values
    default_prompt = "What are three fascinating facts about space exploration?"
    default_base_url = os.getenv("ANTHROPIC_BASE_URL", "http://localhost:8887")
    default_model = "claude-3-sonnet-20240229"
    
    # Use provided values or defaults
    test_prompt = prompt or default_prompt
    test_base_url = base_url or default_base_url
    test_model = model or default_model
    api_key = os.getenv("ANTHROPIC_API_KEY", "dummy-key")
    
    try:
        print(f"🧠 Testing Anthropic API", file=sys.stderr)
        print(f"📍 Endpoint: {test_base_url}/v1/messages", file=sys.stderr)
        print(f"🎯 Model: {test_model}", file=sys.stderr)
        print(f"💬 Prompt: {test_prompt}", file=sys.stderr)
        
        url = f"{test_base_url}/v1/messages"
        
        payload = {
            "model": test_model,
            "max_tokens": 200,
            "temperature": 0.7,
            "messages": [
                {"role": "user", "content": test_prompt}
            ]
        }
        
        headers = {
            "x-api-key": api_key,
            "Content-Type": "application/json",
            "anthropic-version": "2023-06-01"
        }
        
        response = requests.post(url, json=payload, headers=headers, timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            
            # Extract response text from Anthropic format
            response_text = ""
            if "content" in data and len(data["content"]) > 0:
                response_text = data["content"][0].get("text", "No response text")
            else:
                response_text = "No content in response"
            
            result = {
                "success": True,
                "service": "Anthropic",
                "endpoint": url,
                "model": data.get("model", test_model),
                "prompt": test_prompt,
                "response": response_text,
                "usage": data.get("usage", {
                    "input_tokens": 0,
                    "output_tokens": 0
                }),
                "metadata": {
                    "id": data.get("id", ""),
                    "type": data.get("type", "message"),
                    "role": data.get("role", "assistant"),
                    "stop_reason": data.get("stop_reason", "")
                }
            }
            
            print(json.dumps(result))
            return result
        else:
            error_msg = f"HTTP {response.status_code}: {response.text}"
            
            result = {
                "success": False,
                "service": "Anthropic",
                "endpoint": url,
                "model": test_model,
                "prompt": test_prompt,
                "response": "",
                "error": error_msg,
                "usage": {"input_tokens": 0, "output_tokens": 0}
            }
            
            print(json.dumps(result))
            return result
        
    except Exception as e:
        error_msg = str(e)
        
        result = {
            "success": False,
            "service": "Anthropic",
            "endpoint": f"{test_base_url}/v1/messages",
            "model": test_model,
            "prompt": test_prompt,
            "response": "",
            "error": error_msg,
            "usage": {"input_tokens": 0, "output_tokens": 0}
        }
        
        print(json.dumps(result))
        return result

def main():
    """Main entry point for CLI usage."""
    parser = argparse.ArgumentParser(description="Test Anthropic API endpoint")
    parser.add_argument("--prompt", type=str, help="Custom prompt to test with")
    parser.add_argument("--base-url", type=str, help="Custom base URL for the API")
    parser.add_argument("--model", type=str, help="Model to use for the test")
    parser.add_argument("--json", action="store_true", help="Output JSON format")
    
    args = parser.parse_args()
    
    result = test_anthropic_api(
        prompt=args.prompt,
        base_url=args.base_url,
        model=args.model
    )
    
    if not args.json:
        if result["success"]:
            print(f"✅ Anthropic API Test Successful!", file=sys.stderr)
            print(f"📝 Response: {result['response']}", file=sys.stderr)
            print(f"🔢 Tokens: {result['usage'].get('input_tokens', 0) + result['usage'].get('output_tokens', 0)}", file=sys.stderr)
        else:
            print(f"❌ Anthropic API Test Failed!", file=sys.stderr)
            print(f"🚨 Error: {result['error']}", file=sys.stderr)
    
    sys.exit(0 if result["success"] else 1)

if __name__ == "__main__":
    main()

