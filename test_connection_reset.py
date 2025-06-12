import requests
import json
import time
import sys

def test_openai():
    print("\n\033[1;34m🧪 Testing OpenAI API with 2+2 question...\033[0m")
    
    api_base = "http://localhost:8889/v1"
    
    url = f"{api_base}/chat/completions"
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
        
        print(f"\033[0;36m📥 Received response with status code: {response.status_code}\033[0m")
        
        if response.status_code == 200:
            response_json = response.json()
            print(f"\033[0;36m📥 Received OpenAI response:\033[0m")
            print(json.dumps(response_json, indent=2))
            
            # Extract content from the response
            content = response_json.get("choices", [{}])[0].get("message", {}).get("content", "")
            
            if content.strip() == "4":
                print("\033[1;32m✅ OpenAI API test passed!\033[0m")
                print(f"Response content: {content}")
                print("\033[1;32m✅ OpenAI special case for '2+2' works correctly!\033[0m")
            else:
                print(f"\033[1;31m❌ OpenAI API test failed! Expected '4', got '{content}'\033[0m")
        else:
            print(f"\033[1;31m❌ OpenAI API test failed with status code {response.status_code}\033[0m")
            print(f"Response: {response.text}")
    except requests.exceptions.ConnectionError as e:
        print(f"\033[1;31m❌ Connection error: {e}\033[0m")
        print(f"Error details: {e.__class__.__name__}")
        if hasattr(e, 'errno'):
            print(f"Error number: {e.errno}")
        if hasattr(e, 'strerror'):
            print(f"Error string: {e.strerror}")
        if hasattr(e, 'args'):
            print(f"Error args: {e.args}")
    except Exception as e:
        print(f"\033[1;31m❌ Error: {e}\033[0m")
        print(f"Error type: {type(e)}")
        print(f"Error details: {e.__class__.__name__}")
        if hasattr(e, 'args'):
            print(f"Error args: {e.args}")

if __name__ == "__main__":
    test_openai()

