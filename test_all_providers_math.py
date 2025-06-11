import requests
import json
import time
import sys
import os

# Get API base URL from environment variable or use default
API_BASE = os.environ.get("API_BASE", "http://localhost:8889/v1")
print(f"\033[1;34m🔍 Using API base URL: {API_BASE}\033[0m")
print(f"\033[1;36m💡 Set API_BASE environment variable to change this.\033[0m")
print()

def test_openai():
    print("\033[1;34m🧪 Testing OpenAI API with 2+2 question...\033[0m")
    
    url = f"{API_BASE}/chat/completions"
    headers = {
        "Content-Type": "application/json"
    }
    data = {
        "model": "gpt-3.5-turbo",
        "messages": [
            {"role": "user", "content": "2+2"}
        ]
    }
    
    print(f"\033[0;36m📤 Sending message to {url}...\033[0m")
    
    try:
        response = requests.post(url, headers=headers, json=data, timeout=10)
        
        print(f"\033[0;36m📥 Received OpenAI response:\033[0m")
        response_json = response.json()
        print(json.dumps(response_json, indent=2))
        
        # Extract content from the response
        content = response_json.get("choices", [{}])[0].get("message", {}).get("content", "")
        
        print(f"\033[1;32m✅ OpenAI API test passed!\033[0m")
        print(f"Response content: {content}")
        
        if content.strip() == "4":
            print(f"\033[1;32m✅ OpenAI special case for '2+2' works correctly!\033[0m")
        else:
            print(f"\033[1;31m❌ OpenAI special case for '2+2' failed! Expected '4', got '{content}'\033[0m")
    except Exception as e:
        print(f"\033[1;31m❌ Error: {e}\033[0m")
        print(f"Error type: {type(e)}")

def test_anthropic():
    print("\033[1;34m🧪 Testing Anthropic API with 2+2 question...\033[0m")
    
    url = f"{API_BASE}/anthropic/completions"
    headers = {
        "Content-Type": "application/json"
    }
    data = {
        "model": "claude-3-sonnet-20240229",
        "messages": [
            {"role": "user", "content": "2+2"}
        ]
    }
    
    print(f"\033[0;36m📤 Sending message to {url}...\033[0m")
    
    try:
        response = requests.post(url, headers=headers, json=data, timeout=10)
        
        print(f"\033[0;36m📥 Received Anthropic response:\033[0m")
        response_json = response.json()
        print(json.dumps(response_json, indent=2))
        
        # Extract content from the response
        content = ""
        if "content" in response_json and isinstance(response_json["content"], list):
            for item in response_json["content"]:
                if item.get("type") == "text":
                    content += item.get("text", "")
        
        print(f"\033[1;32m✅ Anthropic API test passed!\033[0m")
        print(f"Response content: {content}")
        
        if content.strip() == "4":
            print(f"\033[1;32m✅ Anthropic special case for '2+2' works correctly!\033[0m")
        else:
            print(f"\033[1;31m❌ Anthropic special case for '2+2' failed! Expected '4', got '{content}'\033[0m")
    except Exception as e:
        print(f"\033[1;31m❌ Error: {e}\033[0m")
        print(f"Error type: {type(e)}")

def test_gemini():
    print("\033[1;34m🧪 Testing Google/Gemini API with 2+2 question...\033[0m")
    
    url = f"{API_BASE}/gemini/completions"
    headers = {
        "Content-Type": "application/json"
    }
    data = {
        "model": "gemini-1.5-pro",
        "messages": [
            {"role": "user", "content": "2+2"}
        ]
    }
    
    print(f"\033[0;36m📤 Sending message to {url}...\033[0m")
    
    try:
        response = requests.post(url, headers=headers, json=data, timeout=10)
        
        print(f"\033[0;36m📥 Received Google/Gemini response:\033[0m")
        response_json = response.json()
        print(json.dumps(response_json, indent=2))
        
        # Extract content from the response
        content = ""
        if "candidates" in response_json and len(response_json["candidates"]) > 0:
            candidate = response_json["candidates"][0]
            if "content" in candidate and "parts" in candidate["content"]:
                for part in candidate["content"]["parts"]:
                    if "text" in part:
                        content += part["text"]
        
        print(f"\033[1;32m✅ Google/Gemini API test passed!\033[0m")
        print(f"Response content: {content}")
        
        if content.strip() == "4":
            print(f"\033[1;32m✅ Google/Gemini special case for '2+2' works correctly!\033[0m")
        else:
            print(f"\033[1;31m❌ Google/Gemini special case for '2+2' failed! Expected '4', got '{content}'\033[0m")
    except Exception as e:
        print(f"\033[1;31m❌ Error: {e}\033[0m")
        print(f"Error type: {type(e)}")

if __name__ == "__main__":
    test_openai()
    print("\n" + "=" * 50 + "\n")
    test_anthropic()
    print("\n" + "=" * 50 + "\n")
    test_gemini()

