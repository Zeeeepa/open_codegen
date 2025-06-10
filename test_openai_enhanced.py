#!/usr/bin/env python3
"""
Enhanced OpenAI API Test Script
==============================

Tests the OpenAI-compatible endpoint with the Codegen adapter.
Can output JSON for dashboard integration.
"""

import os
import sys
import json
from openai import OpenAI

def test_openai_api():
    """Test the OpenAI API endpoint."""
    try:
        # Get base URL from environment or use default
        base_url = os.getenv("OPENAI_BASE_URL", "http://localhost:8887/v1")
        api_key = os.getenv("OPENAI_API_KEY", "dummy-key")
        
        print(f"🤖 Testing OpenAI API at: {base_url}", file=sys.stderr)
        
        client = OpenAI(
            api_key=api_key,
            base_url=base_url
        )
        
        prompt = "Explain quantum computing in simple terms."
        
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "user", "content": prompt}
            ],
            max_tokens=150
        )
        
        response_text = response.choices[0].message.content
        
        # Always output JSON for dashboard integration
        result = {
            "success": True,
            "service": "OpenAI",
            "prompt": prompt,
            "response": response_text,
            "model": response.model,
            "usage": {
                "prompt_tokens": response.usage.prompt_tokens if response.usage else 0,
                "completion_tokens": response.usage.completion_tokens if response.usage else 0,
                "total_tokens": response.usage.total_tokens if response.usage else 0
            }
        }
        print(json.dumps(result))
        return True
        
    except Exception as e:
        error_msg = str(e)
        
        result = {
            "success": False,
            "service": "OpenAI",
            "prompt": "Explain quantum computing in simple terms.",
            "response": "",
            "error": error_msg
        }
        print(json.dumps(result))
        return False

if __name__ == "__main__":
    success = test_openai_api()
    sys.exit(0 if success else 1)

