#!/usr/bin/env python3
"""
Example: Using Context Retrieval for AI Prompting
=================================================

This example demonstrates how to use the Codegen context retrieval system
to enhance AI prompts with relevant context from agent runs.

Use cases:
1. Code analysis context for improvement suggestions
2. Documentation context for technical writing
3. Project context for planning and architecture decisions
4. Historical context from previous agent runs
"""

import os
import sys
import json
import time
from typing import Optional, Dict, Any

# Import the integration module
try:
    from codegen_integration import CodegenClient, get_agent_response_for_context
    INTEGRATION_AVAILABLE = True
except ImportError:
    INTEGRATION_AVAILABLE = False
    print("⚠️ codegen_integration module not available")

def example_1_code_analysis_context():
    """
    Example 1: Get code analysis context for improvement suggestions
    """
    print("📊 Example 1: Code Analysis Context")
    print("-" * 40)
    
    if not INTEGRATION_AVAILABLE:
        print("❌ Integration not available")
        return
    
    # Step 1: Get analysis context from Codegen
    analysis_prompt = """
    Please analyze the current codebase structure and identify:
    1. Main components and their responsibilities
    2. Code quality issues or technical debt
    3. Architecture patterns being used
    4. Areas that need improvement
    
    Provide a concise summary suitable for planning improvements.
    """
    
    print("🔄 Getting code analysis context...")
    context = get_agent_response_for_context(
        prompt=analysis_prompt,
        max_length=3000,
        timeout=180
    )
    
    if context:
        print(f"✅ Analysis context retrieved ({len(context)} chars)")
        
        # Step 2: Use context in AI prompt for improvements
        improvement_prompt = f"""
        Based on this code analysis:
        
        {context}
        
        Please suggest 5 specific, actionable improvements that would:
        1. Improve code maintainability
        2. Enhance performance
        3. Reduce technical debt
        4. Improve developer experience
        5. Strengthen the architecture
        
        For each suggestion, provide:
        - What to change
        - Why it's important
        - How to implement it
        """
        
        print("\n🤖 Enhanced AI Prompt:")
        print(improvement_prompt[:500] + "...")
        
        return improvement_prompt
    else:
        print("❌ Failed to get analysis context")
        return None

def example_2_documentation_context():
    """
    Example 2: Get project context for documentation writing
    """
    print("\n📚 Example 2: Documentation Context")
    print("-" * 40)
    
    if not INTEGRATION_AVAILABLE:
        print("❌ Integration not available")
        return
    
    # Step 1: Get project overview context
    overview_prompt = """
    Please provide a comprehensive overview of this project including:
    1. Project purpose and main functionality
    2. Key technologies and frameworks used
    3. Project structure and organization
    4. Setup and installation requirements
    5. Main entry points and usage patterns
    
    Focus on information that would be useful for documentation.
    """
    
    print("🔄 Getting project overview context...")
    context = get_agent_response_for_context(
        prompt=overview_prompt,
        max_length=2500,
        timeout=120
    )
    
    if context:
        print(f"✅ Project context retrieved ({len(context)} chars)")
        
        # Step 2: Use context for README generation
        readme_prompt = f"""
        Based on this project analysis:
        
        {context}
        
        Please create a comprehensive README.md file that includes:
        1. Clear project title and description
        2. Features and capabilities
        3. Installation instructions
        4. Usage examples
        5. API documentation (if applicable)
        6. Contributing guidelines
        7. License information
        
        Make it professional and user-friendly for developers.
        """
        
        print("\n📝 README Generation Prompt:")
        print(readme_prompt[:400] + "...")
        
        return readme_prompt
    else:
        print("❌ Failed to get project context")
        return None

def example_3_api_endpoint_usage():
    """
    Example 3: Using the API endpoints for context retrieval
    """
    print("\n🌐 Example 3: API Endpoint Usage")
    print("-" * 40)
    
    import requests
    
    base_url = "http://localhost:8887"
    
    # Check if server is running
    try:
        health_response = requests.get(f"{base_url}/health", timeout=5)
        if health_response.status_code != 200:
            print("❌ Server not available")
            return
    except:
        print("❌ Cannot connect to server")
        return
    
    print("✅ Server is available")
    
    # Example: Async context retrieval
    print("🔄 Creating async agent run...")
    
    create_payload = {
        "prompt": "Analyze the testing strategy of this project and suggest improvements for test coverage and quality."
    }
    
    try:
        # Create agent run
        create_response = requests.post(
            f"{base_url}/api/context/create",
            json=create_payload,
            timeout=30
        )
        
        if create_response.status_code == 200:
            create_data = create_response.json()
            if create_data.get('success'):
                agent_run_id = create_data.get('agent_run_id')
                print(f"✅ Agent run created: {agent_run_id}")
                
                # Poll for completion (simplified)
                print("⏳ Waiting for completion...")
                for i in range(6):  # 1 minute polling
                    time.sleep(10)
                    
                    status_response = requests.get(
                        f"{base_url}/api/context/status/{agent_run_id}",
                        timeout=10
                    )
                    
                    if status_response.status_code == 200:
                        status_data = status_response.json()
                        status = status_data.get('status', 'unknown')
                        
                        print(f"📊 Status: {status}")
                        
                        if status.lower() == 'completed':
                            context_text = status_data.get('context_text', '')
                            print(f"✅ Context retrieved: {len(context_text)} chars")
                            
                            # Use the context
                            enhanced_prompt = f"""
                            Based on this testing analysis:
                            
                            {context_text[:1000]}...
                            
                            Please create a detailed testing improvement plan.
                            """
                            
                            print("\n🧪 Testing Improvement Prompt:")
                            print(enhanced_prompt[:300] + "...")
                            
                            return enhanced_prompt
                        elif status.lower() in ['failed', 'cancelled']:
                            print(f"❌ Agent run failed: {status}")
                            return None
                
                print("⏰ Polling timed out")
                return None
            else:
                print(f"❌ Failed to create agent run: {create_data.get('error')}")
                return None
        else:
            print(f"❌ API request failed: {create_response.status_code}")
            return None
            
    except Exception as e:
        print(f"❌ API example failed: {e}")
        return None

def example_4_context_chaining():
    """
    Example 4: Chaining multiple context retrievals
    """
    print("\n🔗 Example 4: Context Chaining")
    print("-" * 40)
    
    if not INTEGRATION_AVAILABLE:
        print("❌ Integration not available")
        return
    
    # Step 1: Get architecture context
    print("🏗️ Getting architecture context...")
    arch_context = get_agent_response_for_context(
        "Analyze the software architecture of this project. Focus on design patterns, component relationships, and architectural decisions.",
        max_length=1500,
        timeout=120
    )
    
    if not arch_context:
        print("❌ Failed to get architecture context")
        return
    
    print(f"✅ Architecture context: {len(arch_context)} chars")
    
    # Step 2: Get performance context
    print("⚡ Getting performance context...")
    perf_context = get_agent_response_for_context(
        "Analyze the performance characteristics of this project. Identify bottlenecks, optimization opportunities, and performance best practices.",
        max_length=1500,
        timeout=120
    )
    
    if not perf_context:
        print("❌ Failed to get performance context")
        return
    
    print(f"✅ Performance context: {len(perf_context)} chars")
    
    # Step 3: Combine contexts for comprehensive analysis
    combined_prompt = f"""
    Based on these two analyses:
    
    ARCHITECTURE ANALYSIS:
    {arch_context}
    
    PERFORMANCE ANALYSIS:
    {perf_context}
    
    Please create a comprehensive improvement roadmap that addresses both architectural and performance concerns. Prioritize the recommendations and provide implementation timelines.
    """
    
    print("\n🗺️ Combined Analysis Prompt:")
    print(combined_prompt[:400] + "...")
    
    return combined_prompt

def main():
    """Run all examples"""
    print("🚀 Context Retrieval Usage Examples")
    print("=" * 50)
    
    # Check environment
    org_id = os.getenv('CODEGEN_ORG_ID')
    token = os.getenv('CODEGEN_TOKEN')
    
    if not org_id or not token:
        print("⚠️ Environment variables not set:")
        print(f"   CODEGEN_ORG_ID: {'✅' if org_id else '❌'}")
        print(f"   CODEGEN_TOKEN: {'✅' if token else '❌'}")
        print("\nPlease set these variables to run the examples.")
        return
    
    print(f"✅ Environment configured (Org: {org_id})")
    
    # Run examples
    examples = [
        example_1_code_analysis_context,
        example_2_documentation_context,
        example_3_api_endpoint_usage,
        example_4_context_chaining
    ]
    
    for i, example_func in enumerate(examples, 1):
        try:
            result = example_func()
            if result:
                print(f"✅ Example {i} completed successfully")
            else:
                print(f"⚠️ Example {i} completed with issues")
        except Exception as e:
            print(f"❌ Example {i} failed: {e}")
        
        if i < len(examples):
            print("\n" + "=" * 50)
    
    print("\n🎯 All examples completed!")
    print("\nThese examples show how to:")
    print("1. 📊 Get code analysis context for improvements")
    print("2. 📚 Get project context for documentation")
    print("3. 🌐 Use API endpoints for async retrieval")
    print("4. 🔗 Chain multiple contexts for comprehensive analysis")

if __name__ == "__main__":
    main()

