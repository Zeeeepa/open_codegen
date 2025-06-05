#!/usr/bin/env python3
"""
Example: Using OpenAI client with Codegen Adapter

This example shows how to use the standard OpenAI Python client
to interact with the Codegen platform through the adapter.
"""

import os
from openai import OpenAI


def main():
    """Main example function"""
    print("🤖 OpenAI Client + Codegen Adapter Example")
    print("=" * 50)
    
    # Configure the client to use our adapter
    client = OpenAI(
        base_url="http://localhost:8000/v1",  # Point to our adapter
        api_key=os.getenv("CODEGEN_API_TOKEN", "sk-your-token-here")
    )
    
    print("📡 Configured OpenAI client to use Codegen adapter")
    print("🔗 Base URL: http://localhost:8000/v1")
    print()
    
    # Example 1: Simple chat completion
    print("💬 Example 1: Simple Chat Completion")
    print("-" * 30)
    
    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a helpful coding assistant."},
                {"role": "user", "content": "Write a Python function to calculate fibonacci numbers."}
            ],
            max_tokens=500
        )
        
        print("✅ Response received:")
        print(response.choices[0].message.content)
        print()
        
    except Exception as e:
        print(f"❌ Error: {e}")
        print()
    
    # Example 2: Streaming chat completion
    print("🌊 Example 2: Streaming Chat Completion")
    print("-" * 30)
    
    try:
        stream = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "user", "content": "Explain how REST APIs work in simple terms."}
            ],
            stream=True,
            max_tokens=300
        )
        
        print("✅ Streaming response:")
        for chunk in stream:
            if chunk.choices[0].delta.content:
                print(chunk.choices[0].delta.content, end="", flush=True)
        print("\n")
        
    except Exception as e:
        print(f"❌ Streaming error: {e}")
        print()
    
    # Example 3: Text completion (legacy)
    print("📝 Example 3: Text Completion")
    print("-" * 30)
    
    try:
        response = client.completions.create(
            model="text-davinci-003",
            prompt="The benefits of using TypeScript over JavaScript are:",
            max_tokens=200,
            temperature=0.7
        )
        
        print("✅ Text completion:")
        print(response.choices[0].text)
        print()
        
    except Exception as e:
        print(f"❌ Text completion error: {e}")
        print()
    
    # Example 4: Multiple messages conversation
    print("💭 Example 4: Multi-turn Conversation")
    print("-" * 30)
    
    try:
        messages = [
            {"role": "system", "content": "You are a helpful assistant that explains programming concepts."},
            {"role": "user", "content": "What is recursion?"},
            {"role": "assistant", "content": "Recursion is a programming technique where a function calls itself to solve a problem by breaking it down into smaller, similar subproblems."},
            {"role": "user", "content": "Can you give me a simple example?"}
        ]
        
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=messages,
            max_tokens=300
        )
        
        print("✅ Conversation response:")
        print(response.choices[0].message.content)
        print()
        
    except Exception as e:
        print(f"❌ Conversation error: {e}")
        print()
    
    print("🎉 Examples completed!")
    print("\n💡 Tips:")
    print("  - Make sure the adapter server is running on localhost:8000")
    print("  - Set your CODEGEN_API_TOKEN environment variable")
    print("  - Check the adapter logs for detailed request/response info")


if __name__ == "__main__":
    main()

