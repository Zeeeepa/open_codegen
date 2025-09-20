#!/usr/bin/env python3
"""
Deployment Validation Script
Automatically tests all three endpoints to validate deployment
"""

import requests
import sys
import time

def test_google_gemini():
    """Test Google Gemini API endpoint."""
    print("\n🔍 Testing Google Gemini API...")
    
    url = "http://localhost/v1/gemini/generateContent"
    
    payload = {
        "contents": [
            {
                "parts": [
                    {"text": "What are three interesting facts about space exploration?"}
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
        response = requests.post(url, json=payload, headers=headers, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            if "candidates" in data and len(data["candidates"]) > 0:
                content = data["candidates"][0]["content"]["parts"][0]["text"]
                print(f"✅ Gemini API: SUCCESS - Response received ({len(content)} chars)")
                return True
            else:
                print(f"❌ Gemini API: No content in response: {data}")
                return False
        else:
            print(f"❌ Gemini API: Error {response.status_code}: {response.text}")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Gemini API: Request failed: {e}")
        return False

def test_anthropic_claude():
    """Test Anthropic Claude API endpoint."""
    print("\n🔍 Testing Anthropic Claude API...")
    
    url = "http://localhost/v1/messages"
    
    payload = {
        "model": "claude-3-sonnet-20240229",
        "max_tokens": 1000,
        "messages": [
            {
                "role": "user",
                "content": "Write a short poem about technology."
            }
        ]
    }
    
    headers = {
        "Content-Type": "application/json",
        "Authorization": "Bearer dummy-key",
        "anthropic-version": "2023-06-01"
    }
    
    try:
        response = requests.post(url, json=payload, headers=headers, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            if "content" in data and len(data["content"]) > 0:
                content = data["content"][0]["text"]
                print(f"✅ Anthropic API: SUCCESS - Response received ({len(content)} chars)")
                return True
            else:
                print(f"❌ Anthropic API: No content in response: {data}")
                return False
        else:
            print(f"❌ Anthropic API: Error {response.status_code}: {response.text}")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Anthropic API: Request failed: {e}")
        return False

def test_openai_gpt():
    """Test OpenAI GPT API endpoint."""
    print("\n🔍 Testing OpenAI GPT API...")
    
    url = "http://localhost/v1/chat/completions"
    
    payload = {
        "model": "gpt-3.5-turbo",
        "messages": [
            {
                "role": "user",
                "content": "Explain quantum computing in simple terms."
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
        response = requests.post(url, json=payload, headers=headers, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            if "choices" in data and len(data["choices"]) > 0:
                content = data["choices"][0]["message"]["content"]
                print(f"✅ OpenAI API: SUCCESS - Response received ({len(content)} chars)")
                return True
            else:
                print(f"❌ OpenAI API: No content in response: {data}")
                return False
        else:
            print(f"❌ OpenAI API: Error {response.status_code}: {response.text}")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"❌ OpenAI API: Request failed: {e}")
        return False

def test_ui_content():
    """Test UI content is served correctly."""
    print("\n🔍 Testing UI Content...")
    
    try:
        response = requests.get("http://localhost/", timeout=5)
        
        if response.status_code == 200:
            content = response.text
            
            # Check for key UI elements
            checks = [
                ("System Message Configuration", "💬 System Message Configuration" in content),
                ("Save Button", 'class="system-message-button save"' in content),
                ("Clear Button", 'class="system-message-button clear"' in content),
                ("Test Buttons", 'class="test-button' in content),
                ("JavaScript Functions", 'function saveSystemMessage()' in content),
                ("localStorage Support", 'localStorage.setItem' in content)
            ]
            
            all_passed = True
            for check_name, passed in checks:
                if passed:
                    print(f"  ✅ {check_name}: Found")
                else:
                    print(f"  ❌ {check_name}: Missing")
                    all_passed = False
            
            if all_passed:
                print(f"✅ UI Content: SUCCESS - All elements present ({len(content)} chars)")
                return True
            else:
                print("❌ UI Content: Some elements missing")
                return False
        else:
            print(f"❌ UI Content: Error {response.status_code}")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"❌ UI Content: Request failed: {e}")
        return False

def main():
    """Run all validation tests."""
    print("🚀 Starting Deployment Validation...")
    print("=" * 50)
    
    # Wait a moment for server to be fully ready
    print("⏳ Waiting for server to be ready...")
    time.sleep(2)
    
    tests = [
        ("UI Content", test_ui_content),
        ("Google Gemini", test_google_gemini),
        ("Anthropic Claude", test_anthropic_claude),
        ("OpenAI GPT", test_openai_gpt)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name}: Exception occurred: {e}")
            results.append((test_name, False))
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 VALIDATION SUMMARY")
    print("=" * 50)
    
    passed = 0
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} - {test_name}")
        if result:
            passed += 1
    
    print(f"\n🎯 Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 ALL TESTS PASSED - Deployment is successful!")
        return 0
    else:
        print("⚠️  Some tests failed - Check the issues above")
        return 1

if __name__ == "__main__":
    sys.exit(main())
