#!/usr/bin/env python3
"""
Example: Using Codegen SDK directly

This example shows how to use the Codegen SDK to interact
with the platform for generating OpenAI-compatible responses.
"""

import os
import time
from codegen import Agent


def main():
    """Main example function"""
    print("🚀 Codegen SDK Example")
    print("=" * 50)
    
    # Initialize the agent
    try:
        agent = Agent(
            org_id=os.getenv("CODEGEN_ORG_ID", "323"),
            token=os.getenv("CODEGEN_API_TOKEN", "sk-your-token-here")
        )
        print("✅ Codegen agent initialized")
        print(f"🏢 Organization ID: {os.getenv('CODEGEN_ORG_ID', '323')}")
        print()
        
    except Exception as e:
        print(f"❌ Failed to initialize agent: {e}")
        return
    
    # Example 1: Simple task execution
    print("🎯 Example 1: Simple Task Execution")
    print("-" * 30)
    
    try:
        task = agent.run("Generate a Python function that calculates the factorial of a number")
        
        print("📋 Task created, waiting for completion...")
        
        # Poll for completion
        max_attempts = 30
        attempt = 0
        
        while attempt < max_attempts:
            task.refresh()
            print(f"⏳ Status: {task.status} (attempt {attempt + 1}/{max_attempts})")
            
            if task.status == "completed":
                print("✅ Task completed!")
                print("📄 Result:")
                print(task.result)
                break
            elif task.status == "failed":
                print("❌ Task failed!")
                if hasattr(task, 'error'):
                    print(f"Error: {task.error}")
                break
            
            time.sleep(2)
            attempt += 1
        
        if attempt >= max_attempts:
            print("⏰ Task timed out")
        
        print()
        
    except Exception as e:
        print(f"❌ Task execution error: {e}")
        print()
    
    # Example 2: OpenAI-style prompt
    print("🤖 Example 2: OpenAI-style Response Generation")
    print("-" * 30)
    
    try:
        prompt = """Generate response as if this prompt was sent to OpenAI API:

User: "Explain the difference between synchronous and asynchronous programming in JavaScript"

Please format the response as if it came from GPT-3.5-turbo."""
        
        task = agent.run(prompt)
        
        print("📋 OpenAI-style task created...")
        
        # Poll for completion
        max_attempts = 30
        attempt = 0
        
        while attempt < max_attempts:
            task.refresh()
            print(f"⏳ Status: {task.status} (attempt {attempt + 1}/{max_attempts})")
            
            if task.status == "completed":
                print("✅ OpenAI-style response generated!")
                print("📄 Response:")
                print(task.result)
                break
            elif task.status == "failed":
                print("❌ Task failed!")
                break
            
            time.sleep(2)
            attempt += 1
        
        print()
        
    except Exception as e:
        print(f"❌ OpenAI-style task error: {e}")
        print()
    
    # Example 3: Code generation task
    print("💻 Example 3: Code Generation Task")
    print("-" * 30)
    
    try:
        code_prompt = """Create a complete Python class for a simple todo list manager with the following features:
- Add tasks
- Mark tasks as complete
- List all tasks
- List only incomplete tasks
- Remove tasks

Include proper docstrings and type hints."""
        
        task = agent.run(code_prompt)
        
        print("📋 Code generation task created...")
        
        # Poll for completion
        max_attempts = 30
        attempt = 0
        
        while attempt < max_attempts:
            task.refresh()
            print(f"⏳ Status: {task.status} (attempt {attempt + 1}/{max_attempts})")
            
            if task.status == "completed":
                print("✅ Code generated!")
                print("📄 Generated Code:")
                print(task.result)
                break
            elif task.status == "failed":
                print("❌ Code generation failed!")
                break
            
            time.sleep(2)
            attempt += 1
        
        print()
        
    except Exception as e:
        print(f"❌ Code generation error: {e}")
        print()
    
    print("🎉 Codegen SDK examples completed!")
    print("\n💡 Tips:")
    print("  - Set CODEGEN_API_TOKEN and CODEGEN_ORG_ID environment variables")
    print("  - Tasks may take some time to complete depending on complexity")
    print("  - Check task.status regularly to monitor progress")
    print("  - Use specific, clear prompts for better results")


if __name__ == "__main__":
    main()

