#!/usr/bin/env python3
"""
AI API Client Test Interface
Tests multiple AI providers through the OpenAI Codegen Adapter
"""

import requests
import json
import sys

def test_google_gemini(prompt):
    """Test Google Gemini API endpoint."""
    print("\n--- Calling Google Gemini API ---\n")
    
    url = "http://localhost:8001/v1/gemini/generateContent"
    
    payload = {
        "contents": [
            {
                "parts": [
                    {"text": prompt}
                ]
            }
        ],
        "generationConfig": {
            "temperature": 0.7,
            "maxOutputTokens": 1000
        }
    }
    
    headers = {
        "Content-Type": "application/json",
        "Authorization": "Bearer dummy-key"
    }
    
    try:
        response = requests.post(url, json=payload, headers=headers, timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            if "candidates" in data and len(data["candidates"]) > 0:
                content = data["candidates"][0]["content"]["parts"][0]["text"]
                return content
            else:
                return f"No content in response: {data}"
        else:
            return f"Error {response.status_code}: {response.text}"
            
    except requests.exceptions.RequestException as e:
        return f"Request failed: {e}"

def test_anthropic_claude(prompt):
    """Test Anthropic Claude API endpoint."""
    print("\n--- Calling Anthropic Claude API ---\n")
    
    url = "http://localhost:8001/v1/messages"
    
    payload = {
        "model": "claude-3-sonnet-20240229",
        "max_tokens": 1000,
        "messages": [
            {
                "role": "user",
                "content": prompt
            }
        ]
    }
    
    headers = {
        "Content-Type": "application/json",
        "Authorization": "Bearer dummy-key",
        "anthropic-version": "2023-06-01"
    }
    
    try:
        response = requests.post(url, json=payload, headers=headers, timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            if "content" in data and len(data["content"]) > 0:
                return data["content"][0]["text"]
            else:
                return f"No content in response: {data}"
        else:
            return f"Error {response.status_code}: {response.text}"
            
    except requests.exceptions.RequestException as e:
        return f"Request failed: {e}"

def test_openai_gpt(prompt):
    """Test OpenAI GPT API endpoint."""
    print("\n--- Calling OpenAI API ---\n")
    
    url = "http://localhost:8001/v1/chat/completions"
    
    payload = {
        "model": "gpt-3.5-turbo",
        "messages": [
            {
                "role": "user",
                "content": prompt
            }
        ],
        "max_tokens": 1000,
        "temperature": 0.7
    }
    
    headers = {
        "Content-Type": "application/json",
        "Authorization": "Bearer dummy-key"
    }
    
    try:
        response = requests.post(url, json=payload, headers=headers, timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            if "choices" in data and len(data["choices"]) > 0:
                return data["choices"][0]["message"]["content"]
            else:
                return f"No content in response: {data}"
        else:
            return f"Error {response.status_code}: {response.text}"
            
    except requests.exceptions.RequestException as e:
        return f"Request failed: {e}"

def get_prompt_for_option(option):
    """Get appropriate prompt for each API option."""
    prompts = {
        1: "What are three interesting facts about space exploration?",
        2: "Write a short poem about technology.",
        3: "Explain quantum computing in simple terms."
    }
    return prompts.get(option, "Hello, how are you?")

def main():
    """Main test interface."""
    
    # Test functions mapping
    test_functions = {
        1: test_google_gemini,
        2: test_anthropic_claude,
        3: test_openai_gpt
    }
    
    while True:
        print("\n=== AI API Client ===")
        print("1. Google Gemini")
        print("2. Anthropic Claude")
        print("3. OpenAI GPT")
        print("0. Exit")
        
        try:
            choice = input("\nSelect an API (1-3) or 0 to exit: ")
            choice = int(choice)
            
            if choice == 0:
                print("\nExiting...")
                break
            elif choice in [1, 2, 3]:
                prompt = get_prompt_for_option(choice)
                print(f"\nSending prompt: '{prompt}'")
                
                # Call the appropriate test function
                test_func = test_functions[choice]
                response = test_func(prompt)
                
                print("Response:")
                print("=" * 50)
                print(response)
                print("=" * 50)
                
                input("\nPress Enter to continue...")
            else:
                print("Invalid choice. Please select 1-3 or 0 to exit.")
                
        except ValueError:
            print("Invalid input. Please enter a number.")
        except KeyboardInterrupt:
            print("\n\nExiting...")
            break

if __name__ == "__main__":
    main()
