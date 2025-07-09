#!/usr/bin/env python3
"""
Comprehensive test script for system message functionality.
Tests the complete flow from API endpoints to AI responses.
"""

import requests
import json
import time
import sys
import os
from pathlib import Path

# Test configuration
BASE_URL = "http://127.0.0.1:8000"  # Adjust port as needed
TEST_SYSTEM_MESSAGE = "your name is Bubu"
TEST_USER_MESSAGE = "What is your name?"

def print_test_header(test_name):
    """Print a formatted test header."""
    print(f"\n{'='*60}")
    print(f"🧪 {test_name}")
    print(f"{'='*60}")

def print_success(message):
    """Print a success message."""
    print(f"✅ {message}")

def print_error(message):
    """Print an error message."""
    print(f"❌ {message}")

def print_info(message):
    """Print an info message."""
    print(f"ℹ️  {message}")

def test_system_message_api():
    """Test the system message API endpoints."""
    print_test_header("Testing System Message API Endpoints")
    
    try:
        # Test 1: Clear any existing system message
        print_info("Clearing any existing system message...")
        response = requests.delete(f"{BASE_URL}/api/system-message")
        if response.status_code == 200:
            print_success("System message cleared successfully")
        else:
            print_error(f"Failed to clear system message: {response.status_code}")
            return False
        
        # Test 2: Get system message (should be empty)
        print_info("Getting system message (should be empty)...")
        response = requests.get(f"{BASE_URL}/api/system-message")
        if response.status_code == 200:
            data = response.json()
            if not data["data"]["has_message"]:
                print_success("No system message found (as expected)")
            else:
                print_error(f"Unexpected system message found: {data['data']['message']}")
                return False
        else:
            print_error(f"Failed to get system message: {response.status_code}")
            return False
        
        # Test 3: Save a system message
        print_info(f"Saving system message: '{TEST_SYSTEM_MESSAGE}'...")
        response = requests.post(f"{BASE_URL}/api/system-message", 
                               json={"message": TEST_SYSTEM_MESSAGE})
        if response.status_code == 200:
            data = response.json()
            print_success(f"System message saved: {data['data']['character_count']} characters")
        else:
            print_error(f"Failed to save system message: {response.status_code}")
            return False
        
        # Test 4: Get system message (should return our message)
        print_info("Getting system message (should return our message)...")
        response = requests.get(f"{BASE_URL}/api/system-message")
        if response.status_code == 200:
            data = response.json()
            if data["data"]["has_message"] and data["data"]["message"] == TEST_SYSTEM_MESSAGE:
                print_success(f"System message retrieved correctly: '{data['data']['message']}'")
            else:
                print_error(f"System message mismatch. Expected: '{TEST_SYSTEM_MESSAGE}', Got: '{data['data']['message']}'")
                return False
        else:
            print_error(f"Failed to get system message: {response.status_code}")
            return False
        
        return True
        
    except Exception as e:
        print_error(f"Exception during API testing: {e}")
        return False

def test_ai_response_with_system_message():
    """Test that AI responses reflect the custom system message."""
    print_test_header("Testing AI Response with Custom System Message")
    
    try:
        # Make sure our system message is set
        print_info(f"Ensuring system message is set to: '{TEST_SYSTEM_MESSAGE}'...")
        response = requests.post(f"{BASE_URL}/api/system-message", 
                               json={"message": TEST_SYSTEM_MESSAGE})
        if response.status_code != 200:
            print_error("Failed to set system message for AI test")
            return False
        
        # Test OpenAI chat completions endpoint
        print_info(f"Testing OpenAI chat completions with message: '{TEST_USER_MESSAGE}'...")
        
        chat_request = {
            "model": "gpt-3.5-turbo",
            "messages": [
                {"role": "user", "content": TEST_USER_MESSAGE}
            ]
        }
        
        response = requests.post(f"{BASE_URL}/v1/chat/completions", 
                               json=chat_request,
                               headers={"Authorization": "Bearer dummy-key"})
        
        if response.status_code == 200:
            data = response.json()
            ai_response = data["choices"][0]["message"]["content"]
            print_info(f"AI Response: {ai_response}")
            
            # Check if the response contains "Bubu" (case insensitive)
            if "bubu" in ai_response.lower():
                print_success("✨ AI correctly identified as 'Bubu'! System message is working!")
                return True
            else:
                print_error(f"AI did not identify as 'Bubu'. Response: {ai_response}")
                print_error("This suggests the system message is not being applied correctly.")
                return False
        else:
            print_error(f"Failed to get AI response: {response.status_code}")
            print_error(f"Response: {response.text}")
            return False
            
    except Exception as e:
        print_error(f"Exception during AI response testing: {e}")
        return False

def test_fallback_behavior():
    """Test fallback behavior when no custom system message is set."""
    print_test_header("Testing Fallback Behavior (No Custom System Message)")
    
    try:
        # Clear system message
        print_info("Clearing system message...")
        response = requests.delete(f"{BASE_URL}/api/system-message")
        if response.status_code != 200:
            print_error("Failed to clear system message")
            return False
        
        # Test AI response without custom system message
        print_info("Testing AI response without custom system message...")
        
        chat_request = {
            "model": "gpt-3.5-turbo",
            "messages": [
                {"role": "user", "content": "What are you?"}
            ]
        }
        
        response = requests.post(f"{BASE_URL}/v1/chat/completions", 
                               json=chat_request,
                               headers={"Authorization": "Bearer dummy-key"})
        
        if response.status_code == 200:
            data = response.json()
            ai_response = data["choices"][0]["message"]["content"]
            print_info(f"AI Response: {ai_response}")
            
            # Should fall back to default behavior (mentioning coding assistant, etc.)
            if any(keyword in ai_response.lower() for keyword in ["assistant", "help", "coding", "software"]):
                print_success("AI correctly fell back to default system instruction")
                return True
            else:
                print_error(f"AI response doesn't seem to use default system instruction: {ai_response}")
                return False
        else:
            print_error(f"Failed to get AI response: {response.status_code}")
            return False
            
    except Exception as e:
        print_error(f"Exception during fallback testing: {e}")
        return False

def test_persistence():
    """Test that system messages persist (simulate server restart by checking storage file)."""
    print_test_header("Testing System Message Persistence")
    
    try:
        # Set a system message
        test_message = "I am a persistent test message"
        print_info(f"Setting system message: '{test_message}'...")
        
        response = requests.post(f"{BASE_URL}/api/system-message", 
                               json={"message": test_message})
        if response.status_code != 200:
            print_error("Failed to set system message")
            return False
        
        # Check if storage file exists
        storage_path = Path("backend/data/system_messages.json")
        if storage_path.exists():
            print_success(f"Storage file exists at: {storage_path}")
            
            # Read the file and verify content
            with open(storage_path, 'r') as f:
                data = json.load(f)
            
            if data.get("default_message") == test_message:
                print_success("System message correctly stored in persistence file")
                return True
            else:
                print_error(f"System message not found in persistence file. Found: {data.get('default_message')}")
                return False
        else:
            print_error(f"Storage file not found at: {storage_path}")
            return False
            
    except Exception as e:
        print_error(f"Exception during persistence testing: {e}")
        return False

def test_error_handling():
    """Test error handling for invalid requests."""
    print_test_header("Testing Error Handling")
    
    try:
        # Test 1: Empty system message
        print_info("Testing empty system message...")
        response = requests.post(f"{BASE_URL}/api/system-message", 
                               json={"message": ""})
        if response.status_code == 400:
            print_success("Empty system message correctly rejected")
        else:
            print_error(f"Empty system message should return 400, got: {response.status_code}")
            return False
        
        # Test 2: Invalid JSON
        print_info("Testing invalid JSON...")
        response = requests.post(f"{BASE_URL}/api/system-message", 
                               data="invalid json",
                               headers={"Content-Type": "application/json"})
        if response.status_code in [400, 422]:
            print_success("Invalid JSON correctly rejected")
        else:
            print_error(f"Invalid JSON should return 400/422, got: {response.status_code}")
            return False
        
        return True
        
    except Exception as e:
        print_error(f"Exception during error handling testing: {e}")
        return False

def main():
    """Run all tests."""
    print("🚀 Starting System Message Functionality Tests")
    print(f"Testing against server: {BASE_URL}")
    
    # Check if server is running
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=5)
        if response.status_code != 200:
            print_error(f"Server health check failed: {response.status_code}")
            sys.exit(1)
        print_success("Server is running and healthy")
    except requests.exceptions.RequestException as e:
        print_error(f"Cannot connect to server at {BASE_URL}: {e}")
        print_info("Make sure the server is running with: python3 backend/server.py")
        sys.exit(1)
    
    # Run all tests
    tests = [
        ("System Message API", test_system_message_api),
        ("AI Response with Custom System Message", test_ai_response_with_system_message),
        ("Fallback Behavior", test_fallback_behavior),
        ("Persistence", test_persistence),
        ("Error Handling", test_error_handling),
    ]
    
    passed = 0
    failed = 0
    
    for test_name, test_func in tests:
        try:
            if test_func():
                passed += 1
            else:
                failed += 1
        except Exception as e:
            print_error(f"Test '{test_name}' crashed: {e}")
            failed += 1
    
    # Final results
    print_test_header("Test Results Summary")
    print(f"✅ Passed: {passed}")
    print(f"❌ Failed: {failed}")
    print(f"📊 Total: {passed + failed}")
    
    if failed == 0:
        print_success("🎉 All tests passed! System message functionality is working correctly!")
        
        # Final validation with the original test case
        print_test_header("Final Validation - Original Test Case")
        print_info("Setting up the original test case: 'your name is Bubu'")
        
        # Set the original system message
        requests.post(f"{BASE_URL}/api/system-message", 
                     json={"message": "your name is Bubu"})
        
        # Test with the original question
        chat_request = {
            "model": "gpt-3.5-turbo",
            "messages": [
                {"role": "user", "content": "What is your name?"}
            ]
        }
        
        response = requests.post(f"{BASE_URL}/v1/chat/completions", 
                               json=chat_request,
                               headers={"Authorization": "Bearer dummy-key"})
        
        if response.status_code == 200:
            data = response.json()
            ai_response = data["choices"][0]["message"]["content"]
            print_info(f"🤖 AI Response: {ai_response}")
            
            if "bubu" in ai_response.lower():
                print_success("🎯 Perfect! The AI now correctly responds as 'Bubu'!")
                print_success("✨ Your system message configuration is working!")
            else:
                print_error("❌ The AI is still not responding as 'Bubu'")
        
        sys.exit(0)
    else:
        print_error("❌ Some tests failed. Please check the issues above.")
        sys.exit(1)

if __name__ == "__main__":
    main()

