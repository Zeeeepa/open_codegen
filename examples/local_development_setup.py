#!/usr/bin/env python3
"""
Local Development Setup Example
==============================

This example shows how to set up the OpenAI Codegen Adapter
for local development using different AI service providers.

Run this script to see examples of different configurations.
"""

import os
import sys
from pathlib import Path

# Add the parent directory to the path so we can import our modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from config.service_providers import (
    ServiceProviderURLs, LocalDevelopmentURLs,
    get_all_service_providers, get_base_url_from_env
)


def show_configuration_examples():
    """Show different configuration examples."""
    print("🛠️  Local Development Setup Examples")
    print("=" * 50)
    
    print("\n📋 Example 1: Using Ollama (Recommended for beginners)")
    print("-" * 30)
    print("# 1. Install and start Ollama")
    print("curl -fsSL https://ollama.ai/install.sh | sh")
    print("ollama serve")
    print("ollama pull llama2")
    print()
    print("# 2. Configure environment")
    print("export CODEGEN_ORG_ID='your_org_id'")
    print("export CODEGEN_TOKEN='sk-your-codegen-token'")
    print("export OPENAI_BASE_URL='http://localhost:11434'")
    print()
    print("# 3. Start the adapter")
    print("python -m openai_codegen_adapter.main")
    
    print("\n📋 Example 2: Using LM Studio")
    print("-" * 30)
    print("# 1. Download and install LM Studio from https://lmstudio.ai")
    print("# 2. Start the local server on port 1234")
    print("# 3. Configure environment")
    print("export CODEGEN_ORG_ID='your_org_id'")
    print("export CODEGEN_TOKEN='sk-your-codegen-token'")
    print("export OPENAI_BASE_URL='http://localhost:1234'")
    print()
    print("# 4. Start the adapter")
    print("python -m openai_codegen_adapter.main")
    
    print("\n📋 Example 3: Using Official OpenAI")
    print("-" * 30)
    print("# 1. Get your OpenAI API key from https://platform.openai.com")
    print("# 2. Configure environment")
    print("export CODEGEN_ORG_ID='your_org_id'")
    print("export CODEGEN_TOKEN='sk-your-codegen-token'")
    print("export OPENAI_API_KEY='sk-your-openai-key'")
    print("export OPENAI_BASE_URL='https://api.openai.com'")
    print()
    print("# 3. Start the adapter")
    print("python -m openai_codegen_adapter.main")
    
    print("\n📋 Example 4: Multi-Provider Setup")
    print("-" * 30)
    print("# Use different providers for different endpoints")
    print("export CODEGEN_ORG_ID='your_org_id'")
    print("export CODEGEN_TOKEN='sk-your-codegen-token'")
    print("export OPENAI_BASE_URL='http://localhost:11434'  # Ollama for chat")
    print("export ANTHROPIC_BASE_URL='https://api.anthropic.com'  # Official Anthropic")
    print("export ANTHROPIC_API_KEY='sk-ant-your-anthropic-key'")
    print()
    print("# Start the adapter")
    print("python -m openai_codegen_adapter.main")


def show_testing_examples():
    """Show testing examples."""
    print("\n🧪 Testing Your Setup")
    print("=" * 30)
    
    print("\n📋 Test with curl:")
    print("curl -X POST http://localhost:8887/v1/chat/completions \\")
    print("  -H 'Content-Type: application/json' \\")
    print("  -d '{")
    print("    \"model\": \"gpt-3.5-turbo\",")
    print("    \"messages\": [{\"role\": \"user\", \"content\": \"Hello!\"}]")
    print("  }'")
    
    print("\n📋 Test with Python:")
    print("""
import openai

# Configure client to use your adapter
client = openai.OpenAI(
    base_url="http://localhost:8887/v1",
    api_key="dummy"  # Not needed for local development
)

# Test chat completion
response = client.chat.completions.create(
    model="gpt-3.5-turbo",
    messages=[{"role": "user", "content": "Hello!"}]
)

print(response.choices[0].message.content)
""")
    
    print("\n📋 Test with Anthropic SDK:")
    print("""
import anthropic

# Configure client to use your adapter
client = anthropic.Anthropic(
    api_key="dummy",  # Not needed for local development
    base_url="http://localhost:8887"
)

# Test message
response = client.messages.create(
    model="claude-3-sonnet-20240229",
    max_tokens=100,
    messages=[{"role": "user", "content": "Hello!"}]
)

print(response.content[0].text)
""")


def show_troubleshooting():
    """Show troubleshooting tips."""
    print("\n🚨 Troubleshooting")
    print("=" * 20)
    
    print("\n❌ Issue: Connection Refused")
    print("💡 Solution:")
    print("  • Check if your local server is running")
    print("  • Verify the port number is correct")
    print("  • Test with: curl http://localhost:11434/api/tags  # For Ollama")
    
    print("\n❌ Issue: Model Not Found")
    print("💡 Solution:")
    print("  • List available models: curl http://localhost:8887/v1/models")
    print("  • For Ollama: ollama pull llama2")
    print("  • Check the model name matches what's available")
    
    print("\n❌ Issue: Authentication Failed")
    print("💡 Solution:")
    print("  • For local development, set API_KEY to 'dummy'")
    print("  • For cloud providers, check your API key is correct")
    print("  • Verify the authentication method (Bearer vs x-api-key)")


def show_configuration_tools():
    """Show configuration tools."""
    print("\n🔧 Configuration Tools")
    print("=" * 25)
    
    print("\n📋 Use the Configuration CLI:")
    print("# List all available providers")
    print("python scripts/configure_providers.py --list")
    print()
    print("# Configure OpenAI to use local Ollama")
    print("python scripts/configure_providers.py --provider openai --url http://localhost:11434")
    print()
    print("# Generate .env template")
    print("python scripts/configure_providers.py --generate-env")
    print()
    print("# Test connection")
    print("python scripts/configure_providers.py --test-connection openai")
    print()
    print("# Show current configuration")
    print("python scripts/configure_providers.py --show-config")


def main():
    """Main function to show all examples."""
    print("🌟 OpenAI Codegen Adapter - Local Development Setup")
    print("=" * 60)
    print("This guide shows you how to set up the adapter for local development")
    print("with different AI service providers.")
    
    show_configuration_examples()
    show_configuration_tools()
    show_testing_examples()
    show_troubleshooting()
    
    print("\n🎯 Quick Start Recommendation:")
    print("1. Start with Ollama (easiest setup)")
    print("2. Use the configuration CLI for guided setup")
    print("3. Test your setup before deploying")
    print("4. Read the full documentation in docs/")
    
    print("\n📚 Additional Resources:")
    print("• Quick Start Guide: docs/QUICK_START_GUIDE.md")
    print("• Service Provider Configuration: docs/SERVICE_PROVIDER_CONFIGURATION.md")
    print("• Configuration CLI: python scripts/configure_providers.py --help")
    
    print("\n🚀 Happy coding!")


if __name__ == "__main__":
    main()

