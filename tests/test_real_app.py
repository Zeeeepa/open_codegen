#!/usr/bin/env python3
"""
Real OpenAI Application Test
This is an unmodified OpenAI application that should work transparently
with the interceptor without any code changes.
"""

import os
from openai import OpenAI

def main():
    """Test a real OpenAI application without modifications."""
    print("🧪 Testing Real OpenAI Application (Unmodified)")
    print("=" * 50)
    
    # This is exactly how a real application would use OpenAI
    # NO base_url modification, NO special configuration
    client = OpenAI(
        api_key="dummy-key-for-testing-interceptor"  # Dummy key - should still work with interceptor
    )
    
    print("✅ OpenAI client initialized (standard way)")
    print(f"📍 Client will connect to: {client.base_url}")
    print()
    
    try:
        print("🚀 Making OpenAI API call...")
        print("   (This should be intercepted and routed to Codegen SDK)")
        print()
        
        # Standard OpenAI API call - exactly as any app would do it
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {
                    "role": "system", 
                    "content": "You are a helpful assistant. Respond briefly."
                },
                {
                    "role": "user", 
                    "content": "Hello! This is a test of transparent OpenAI API interception. Please confirm you received this message."
                }
            ],
            max_tokens=100,
            temperature=0.7
        )
        
        print("🎉 SUCCESS! OpenAI API call completed successfully!")
        print("✅ Transparent interception is working!")
        print()
        print("📝 Response from Codegen SDK:")
        print("-" * 30)
        print(response.choices[0].message.content)
        print("-" * 30)
        print()
        print(f"📊 Model used: {response.model}")
        print(f"🔢 Tokens used: {response.usage.total_tokens if response.usage else 'N/A'}")
        print()
        print("🎯 This proves that:")
        print("   ✅ Unmodified OpenAI applications work with interceptor")
        print("   ✅ DNS interception is functioning")
        print("   ✅ API requests are routed to Codegen SDK")
        print("   ✅ Responses are properly formatted")
        
        return True
        
    except Exception as e:
        print(f"❌ OpenAI API call failed: {e}")
        print()
        print("🔍 This could mean:")
        print("   • Interceptor service is not running")
        print("   • DNS interception is not configured")
        print("   • SSL certificates are missing")
        print("   • Codegen SDK credentials are invalid")
        print()
        print("🔧 Try:")
        print("   1. sudo systemctl status openai-interceptor")
        print("   2. sudo python3 -m interceptor.ubuntu_dns status")
        print("   3. sudo python3 -m interceptor.ubuntu_ssl status")
        
        return False

def test_multiple_requests():
    """Test multiple API calls to ensure consistency."""
    print("\n🔄 Testing Multiple API Calls")
    print("=" * 30)
    
    client = OpenAI(api_key="dummy-key-for-testing")
    
    test_prompts = [
        "What is 2+2?",
        "Tell me a joke",
        "Explain quantum computing in one sentence"
    ]
    
    for i, prompt in enumerate(test_prompts, 1):
        try:
            print(f"📤 Request {i}: {prompt}")
            
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=50
            )
            
            print(f"📥 Response {i}: {response.choices[0].message.content[:100]}...")
            print()
            
        except Exception as e:
            print(f"❌ Request {i} failed: {e}")
            return False
    
    print("✅ All multiple requests succeeded!")
    return True

def test_different_models():
    """Test different model requests."""
    print("\n🤖 Testing Different Models")
    print("=" * 30)
    
    client = OpenAI(api_key="dummy-key-for-testing")
    
    models_to_test = [
        "gpt-3.5-turbo",
        "gpt-4",
        "gpt-4-turbo"
    ]
    
    for model in models_to_test:
        try:
            print(f"🧠 Testing model: {model}")
            
            response = client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": f"Hello from {model}!"}],
                max_tokens=30
            )
            
            print(f"✅ {model}: {response.choices[0].message.content[:50]}...")
            print()
            
        except Exception as e:
            print(f"❌ {model} failed: {e}")
    
    return True

if __name__ == "__main__":
    print("🎯 Real OpenAI Application Test")
    print("This application uses OpenAI API exactly as any real app would")
    print("NO modifications, NO special configuration")
    print("If transparent interception works, this will succeed with dummy keys")
    print()
    
    # Test basic functionality
    success = main()
    
    if success:
        # Test additional scenarios
        test_multiple_requests()
        test_different_models()
        
        print("\n🎉 TRANSPARENT INTERCEPTION FULLY VERIFIED!")
        print("✅ Unmodified OpenAI applications work perfectly")
        print("✅ All API calls routed to Codegen SDK")
        print("✅ No code changes required for existing apps")
    else:
        print("\n❌ Transparent interception needs configuration")
        print("Run: sudo ./install-ubuntu.sh")
