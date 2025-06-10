#!/usr/bin/env python3
"""
OpenAI API Test
==============

Comprehensive test for OpenAI-compatible endpoints through the Codegen adapter.
Supports both CLI and UI integration with custom prompts.
"""

import os
import sys
import json
import argparse
from openai import OpenAI

def test_openai_api(prompt=None, base_url=None, model=None):
    """
    Test the OpenAI API endpoint with custom or default parameters.
    
    Args:
        prompt (str): Custom prompt to test with
        base_url (str): Custom base URL for the API
        model (str): Model to use for the test
    
    Returns:
        dict: Test result with success status, response, and metadata
    """
    # Default values
    default_prompt = "Explain quantum computing in simple terms."
    default_base_url = os.getenv("OPENAI_BASE_URL", "http://localhost:8887/v1")
    default_model = "gpt-3.5-turbo"
    
    # Use provided values or defaults
    test_prompt = prompt or default_prompt
    test_base_url = base_url or default_base_url
    test_model = model or default_model
    api_key = os.getenv("OPENAI_API_KEY", "dummy-key")
    
    try:
        print(f"🤖 Testing OpenAI API", file=sys.stderr)
        print(f"📍 Endpoint: {test_base_url}", file=sys.stderr)
        print(f"🎯 Model: {test_model}", file=sys.stderr)
        print(f"💬 Prompt: {test_prompt}", file=sys.stderr)
        
        client = OpenAI(
            api_key=api_key,
            base_url=test_base_url
        )
        
        response = client.chat.completions.create(
            model=test_model,
            messages=[
                {"role": "user", "content": test_prompt}
            ],
            max_tokens=200,
            temperature=0.7
        )
        
        response_text = response.choices[0].message.content
        
        result = {
            "success": True,
            "service": "OpenAI",
            "endpoint": f"{test_base_url}/chat/completions",
            "model": response.model,
            "prompt": test_prompt,
            "response": response_text,
            "usage": {
                "prompt_tokens": response.usage.prompt_tokens if response.usage else 0,
                "completion_tokens": response.usage.completion_tokens if response.usage else 0,
                "total_tokens": response.usage.total_tokens if response.usage else 0
            },
            "metadata": {
                "finish_reason": response.choices[0].finish_reason,
                "created": response.created,
                "id": response.id
            }
        }
        
        print(json.dumps(result))
        return result
        
    except Exception as e:
        error_msg = str(e)
        
        result = {
            "success": False,
            "service": "OpenAI",
            "endpoint": f"{test_base_url}/chat/completions",
            "model": test_model,
            "prompt": test_prompt,
            "response": "",
            "error": error_msg,
            "usage": {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}
        }
        
        print(json.dumps(result))
        return result

def main():
    """Main entry point for CLI usage."""
    parser = argparse.ArgumentParser(description="Test OpenAI API endpoint")
    parser.add_argument("--prompt", type=str, help="Custom prompt to test with")
    parser.add_argument("--base-url", type=str, help="Custom base URL for the API")
    parser.add_argument("--model", type=str, help="Model to use for the test")
    parser.add_argument("--json", action="store_true", help="Output JSON format")
    
    args = parser.parse_args()
    
    result = test_openai_api(
        prompt=args.prompt,
        base_url=args.base_url,
        model=args.model
    )
    
    if not args.json:
        if result["success"]:
            print(f"✅ OpenAI API Test Successful!", file=sys.stderr)
            print(f"📝 Response: {result['response']}", file=sys.stderr)
            print(f"🔢 Tokens: {result['usage']['total_tokens']}", file=sys.stderr)
        else:
            print(f"❌ OpenAI API Test Failed!", file=sys.stderr)
            print(f"🚨 Error: {result['error']}", file=sys.stderr)
    
    sys.exit(0 if result["success"] else 1)

if __name__ == "__main__":
    main()

