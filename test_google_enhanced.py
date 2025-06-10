#!/usr/bin/env python3
"""
Enhanced Google Gemini API Test Script
=====================================

Tests the Google Gemini-compatible endpoint with the Codegen adapter.
Can output JSON for dashboard integration.
"""

import os
import sys
import json
import requests

def test_google_api():
    """Test the Google Gemini API endpoint."""
    try:
        # Get base URL from environment or use default
        base_url = os.getenv("GOOGLE_BASE_URL", "http://localhost:8887")
        api_key = os.getenv("GOOGLE_API_KEY", "dummy-key")
        
        print(f"🌟 Testing Google Gemini API at: {base_url}", file=sys.stderr)
        
        url = f"{base_url}/v1/gemini/generateContent"
        prompt = "What are three interesting facts about space exploration?"
        
        payload = {
            "contents": [
                {
                    "parts": [
                        {"text": prompt}
                    ]
                }
            ],
            "generationConfig": {
                "maxOutputTokens": 200,
                "temperature": 0.7
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
            candidates = data.get("candidates", [])
            if candidates and "content" in candidates[0]:
                parts = candidates[0]["content"].get("parts", [])
                if parts and "text" in parts[0]:
                    response_text = parts[0]["text"]
                else:
                    response_text = "No response text found"
            else:
                response_text = str(data)
            
            result = {
                "success": True,
                "service": "Google Gemini",
                "prompt": prompt,
                "response": response_text,
                "model": "gemini-pro",
                "usage": data.get("usageMetadata", {})
            }
            print(json.dumps(result))
            return True
        else:
            error_msg = f"HTTP {response.status_code}: {response.text}"
            result = {
                "success": False,
                "service": "Google Gemini",
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
            "service": "Google Gemini",
            "prompt": "What are three interesting facts about space exploration?",
            "response": "",
            "error": error_msg
        }
        print(json.dumps(result))
        return False

if __name__ == "__main__":
    success = test_google_api()
    sys.exit(0 if success else 1)

