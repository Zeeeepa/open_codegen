#!/usr/bin/env python3
"""
Google Gemini API Test
=====================

Comprehensive test for Google Gemini API through the Codegen adapter.
Supports both CLI and UI integration with custom prompts.
"""

import os
import sys
import json
import argparse
import requests

def test_google_api(prompt=None, base_url=None, model=None):
    """
    Test the Google Gemini API endpoint with custom or default parameters.
    
    Args:
        prompt (str): Custom prompt to test with
        base_url (str): Custom base URL for the API
        model (str): Model to use for the test
    
    Returns:
        dict: Test result with success status, response, and metadata
    """
    # Default values
    default_prompt = "Explain the concept of artificial intelligence in simple terms."
    default_base_url = os.getenv("GOOGLE_BASE_URL", "http://localhost:8887")
    default_model = "gemini-1.5-pro"
    
    # Use provided values or defaults
    test_prompt = prompt or default_prompt
    test_base_url = base_url or default_base_url
    test_model = model or default_model
    api_key = os.getenv("GOOGLE_API_KEY", "dummy-key")
    
    try:
        print(f"🌟 Testing Google Gemini API", file=sys.stderr)
        print(f"📍 Endpoint: {test_base_url}/v1/models/{test_model}:generateContent", file=sys.stderr)
        print(f"🎯 Model: {test_model}", file=sys.stderr)
        print(f"💬 Prompt: {test_prompt}", file=sys.stderr)
        
        url = f"{test_base_url}/v1/models/{test_model}:generateContent"
        
        payload = {
            "contents": [
                {
                    "parts": [
                        {"text": test_prompt}
                    ]
                }
            ],
            "generationConfig": {
                "maxOutputTokens": 200,
                "temperature": 0.7,
                "topP": 0.8,
                "topK": 40
            }
        }
        
        headers = {
            "Content-Type": "application/json"
        }
        
        # Add API key if provided
        if api_key and api_key != "dummy-key":
            headers["Authorization"] = f"Bearer {api_key}"
        
        response = requests.post(url, json=payload, headers=headers, timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            
            # Extract response text from Gemini format
            response_text = ""
            if "candidates" in data and len(data["candidates"]) > 0:
                candidate = data["candidates"][0]
                if "content" in candidate and "parts" in candidate["content"]:
                    parts = candidate["content"]["parts"]
                    if len(parts) > 0 and "text" in parts[0]:
                        response_text = parts[0]["text"]
                    else:
                        response_text = "No text in response parts"
                else:
                    response_text = "No content in candidate"
            else:
                response_text = "No candidates in response"
            
            # Extract usage metadata
            usage_metadata = data.get("usageMetadata", {})
            
            result = {
                "success": True,
                "service": "Google Gemini",
                "endpoint": url,
                "model": test_model,
                "prompt": test_prompt,
                "response": response_text,
                "usage": {
                    "prompt_token_count": usage_metadata.get("promptTokenCount", 0),
                    "candidates_token_count": usage_metadata.get("candidatesTokenCount", 0),
                    "total_token_count": usage_metadata.get("totalTokenCount", 0)
                },
                "metadata": {
                    "finish_reason": data["candidates"][0].get("finishReason", "") if "candidates" in data and len(data["candidates"]) > 0 else "",
                    "safety_ratings": data["candidates"][0].get("safetyRatings", []) if "candidates" in data and len(data["candidates"]) > 0 else []
                }
            }
            
            print(json.dumps(result))
            return result
        else:
            error_msg = f"HTTP {response.status_code}: {response.text}"
            
            result = {
                "success": False,
                "service": "Google Gemini",
                "endpoint": url,
                "model": test_model,
                "prompt": test_prompt,
                "response": "",
                "error": error_msg,
                "usage": {"prompt_token_count": 0, "candidates_token_count": 0, "total_token_count": 0}
            }
            
            print(json.dumps(result))
            return result
        
    except Exception as e:
        error_msg = str(e)
        
        result = {
            "success": False,
            "service": "Google Gemini",
            "endpoint": f"{test_base_url}/v1/models/{test_model}:generateContent",
            "model": test_model,
            "prompt": test_prompt,
            "response": "",
            "error": error_msg,
            "usage": {"prompt_token_count": 0, "candidates_token_count": 0, "total_token_count": 0}
        }
        
        print(json.dumps(result))
        return result

def main():
    """Main entry point for CLI usage."""
    parser = argparse.ArgumentParser(description="Test Google Gemini API endpoint")
    parser.add_argument("--prompt", type=str, help="Custom prompt to test with")
    parser.add_argument("--base-url", type=str, help="Custom base URL for the API")
    parser.add_argument("--model", type=str, help="Model to use for the test")
    parser.add_argument("--json", action="store_true", help="Output JSON format")
    
    args = parser.parse_args()
    
    result = test_google_api(
        prompt=args.prompt,
        base_url=args.base_url,
        model=args.model
    )
    
    if not args.json:
        if result["success"]:
            print(f"✅ Google Gemini API Test Successful!", file=sys.stderr)
            print(f"📝 Response: {result['response']}", file=sys.stderr)
            print(f"🔢 Tokens: {result['usage']['total_token_count']}", file=sys.stderr)
        else:
            print(f"❌ Google Gemini API Test Failed!", file=sys.stderr)
            print(f"🚨 Error: {result['error']}", file=sys.stderr)
    
    sys.exit(0 if result["success"] else 1)

if __name__ == "__main__":
    main()

