#!/usr/bin/env python3
"""
Enhanced Anthropic API Test Script
=================================

Tests the Anthropic-compatible endpoint with the Codegen adapter.
Can output JSON for dashboard integration.
"""

import os
import sys
import json
import requests

def test_anthropic_api():
    """Test the Anthropic API endpoint."""
    try:
        # Get base URL from environment or use default
        base_url = os.getenv("ANTHROPIC_BASE_URL", "http://localhost:8887")
        api_key = os.getenv("ANTHROPIC_API_KEY", "dummy-key")
        
        print(f"🧠 Testing Anthropic API at: {base_url}", file=sys.stderr)
        
        url = f"{base_url}/v1/messages"
        prompt = "What are three interesting facts about space exploration?"
        
        payload = {
            "model": "claude-3-sonnet-20240229",
            "max_tokens": 200,
            "messages": [
                {"role": "user", "content": prompt}
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
            response_text = data.get("content", [{}])[0].get("text", "No response text")
            
            result = {
                "success": True,
                "service": "Anthropic",
                "prompt": prompt,
                "response": response_text,
                "model": data.get("model", "claude-3-sonnet-20240229"),
                "usage": data.get("usage", {})
            }
            print(json.dumps(result))
            return True
        else:
            error_msg = f"HTTP {response.status_code}: {response.text}"
            result = {
                "success": False,
                "service": "Anthropic",
                "prompt": prompt,
                "response": "",
                "error": error_msg
            }
            print(json.dumps(result))
            return False
        
    except Exception as e:
        error_msg = str(e)
        
        result = {
            "success": False,
            "service": "Anthropic",
            "prompt": "What are three interesting facts about space exploration?",
            "response": "",
            "error": error_msg
        }
        print(json.dumps(result))
        return False

if __name__ == "__main__":
    success = test_anthropic_api()
    sys.exit(0 if success else 1)

