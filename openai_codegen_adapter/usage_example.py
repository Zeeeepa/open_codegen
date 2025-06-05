"""
Example usage of the OpenAI Codegen Adapter.

This demonstrates how to use the adapter with standard OpenAI client libraries.
"""

import openai
import asyncio
import json

# Configure OpenAI client to use our adapter
openai.api_base = "http://localhost:8887/v1"
openai.api_key = "dummy-key"  # Not used by our adapter, but required by OpenAI client

# Alternative using the new OpenAI client (v1.0+)
from openai import OpenAI

client = OpenAI(
    base_url="http://localhost:8887/v1",
    api_key="dummy-key"  # Not used by our adapter
)


def example_chat_completion():
    """Example of using chat completions."""
    print("=== Chat Completion Example ===")
    
    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": "What is the capital of France?"}
            ],
            temperature=0.7,
            max_tokens=150
        )
        
        print(f"Response: {response.choices[0].message.content}")
        print(f"Usage: {response.usage}")
        
    except Exception as e:
        print(f"Error: {e}")


def example_streaming_chat():
    """Example of streaming chat completions."""
    print("\n=== Streaming Chat Example ===")
    
    try:
        stream = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "user", "content": "Write a short poem about coding."}
            ],
            stream=True,
            temperature=0.8
        )
        
        print("Streaming response:")
        for chunk in stream:
            if chunk.choices[0].delta.content is not None:
                print(chunk.choices[0].delta.content, end="", flush=True)
        print("\n")
        
    except Exception as e:
        print(f"Error: {e}")


def example_text_completion():
    """Example of using text completions."""
    print("\n=== Text Completion Example ===")
    
    try:
        response = client.completions.create(
            model="gpt-3.5-turbo-instruct",
            prompt="The future of artificial intelligence is",
            max_tokens=100,
            temperature=0.6
        )
        
        print(f"Response: {response.choices[0].text}")
        print(f"Usage: {response.usage}")
        
    except Exception as e:
        print(f"Error: {e}")


def example_with_conversation():
    """Example of a multi-turn conversation."""
    print("\n=== Multi-turn Conversation Example ===")
    
    messages = [
        {"role": "system", "content": "You are a helpful coding assistant."}
    ]
    
    # First turn
    messages.append({"role": "user", "content": "How do I create a list in Python?"})
    
    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=messages,
            temperature=0.5
        )
        
        assistant_response = response.choices[0].message.content
        print(f"Assistant: {assistant_response}")
        
        # Add assistant response to conversation
        messages.append({"role": "assistant", "content": assistant_response})
        
        # Second turn
        messages.append({"role": "user", "content": "Can you show me an example with numbers?"})
        
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=messages,
            temperature=0.5
        )
        
        print(f"Assistant: {response.choices[0].message.content}")
        
    except Exception as e:
        print(f"Error: {e}")


async def example_async_usage():
    """Example of async usage with the OpenAI client."""
    print("\n=== Async Usage Example ===")
    
    from openai import AsyncOpenAI
    
    async_client = AsyncOpenAI(
        base_url="http://localhost:8887/v1",
        api_key="dummy-key"
    )
    
    try:
        response = await async_client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "user", "content": "Explain async programming in Python briefly."}
            ],
            temperature=0.7
        )
        
        print(f"Async response: {response.choices[0].message.content}")
        
    except Exception as e:
        print(f"Error: {e}")
    finally:
        await async_client.close()


def test_health_endpoint():
    """Test the health endpoint."""
    print("\n=== Health Check ===")
    
    import requests
    
    try:
        response = requests.get("http://localhost:8887/health")
        print(f"Health status: {response.json()}")
    except Exception as e:
        print(f"Health check failed: {e}")


def test_models_endpoint():
    """Test the models endpoint."""
    print("\n=== Available Models ===")
    
    try:
        models = client.models.list()
        print("Available models:")
        for model in models.data:
            print(f"  - {model.id}")
    except Exception as e:
        print(f"Error listing models: {e}")


if __name__ == "__main__":
    print("OpenAI Codegen Adapter Usage Examples")
    print("=====================================")
    print("Make sure the adapter server is running on localhost:8887")
    print()
    
    # Test health first
    test_health_endpoint()
    
    # Test models
    test_models_endpoint()
    
    # Run examples
    example_chat_completion()
    example_text_completion()
    example_with_conversation()
    example_streaming_chat()
    
    # Run async example
    asyncio.run(example_async_usage())
    
    print("\n=== Examples completed ===")
    print("You can now use any OpenAI-compatible application with:")
    print("  base_url: http://localhost:8887/v1")
    print("  api_key: any-dummy-key (not validated)")

