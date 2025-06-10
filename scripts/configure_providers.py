#!/usr/bin/env python3
"""
Service Provider Configuration CLI Tool
======================================

A command-line tool to help users configure service provider base URLs
for local development and testing.

Usage:
    python scripts/configure_providers.py --list
    python scripts/configure_providers.py --provider openai --url http://localhost:8080
    python scripts/configure_providers.py --generate-env
    python scripts/configure_providers.py --test-connection openai
"""

import argparse
import os
import sys
import json
import requests
from typing import Dict, Optional
from pathlib import Path

# Add the parent directory to the path so we can import our modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from config.service_providers import (
    ServiceProviderURLs, LocalDevelopmentURLs, 
    get_all_service_providers, get_service_provider_config,
    ENV_VAR_MAPPINGS
)


class ProviderConfigCLI:
    """CLI tool for configuring service providers."""
    
    def __init__(self):
        self.providers = get_all_service_providers()
    
    def list_providers(self):
        """List all available service providers."""
        print("🌐 Available Service Providers")
        print("=" * 50)
        
        print("\n🏢 Official Cloud Providers:")
        official_providers = [
            ServiceProviderURLs.OPENAI,
            ServiceProviderURLs.ANTHROPIC,
            ServiceProviderURLs.GOOGLE_VERTEX_AI,
            ServiceProviderURLs.GOOGLE_AI_STUDIO,
            ServiceProviderURLs.AZURE_OPENAI,
            ServiceProviderURLs.COHERE,
            ServiceProviderURLs.HUGGINGFACE,
            ServiceProviderURLs.MISTRAL,
            ServiceProviderURLs.TOGETHER,
            ServiceProviderURLs.REPLICATE
        ]
        
        for provider in official_providers:
            multimodal = "✅" if provider.supports_multimodal else "❌"
            streaming = "✅" if provider.supports_streaming else "❌"
            print(f"  • {provider.name}")
            print(f"    URL: {provider.base_url}")
            print(f"    Auth: {provider.authentication_type}")
            print(f"    Multimodal: {multimodal} | Streaming: {streaming}")
            print()
        
        print("🏠 Local Development Providers:")
        local_providers = [
            LocalDevelopmentURLs.OLLAMA,
            LocalDevelopmentURLs.LM_STUDIO,
            LocalDevelopmentURLs.TEXT_GENERATION_WEBUI,
            LocalDevelopmentURLs.VLLM,
            LocalDevelopmentURLs.LOCAL_OPENAI_COMPATIBLE
        ]
        
        for provider in local_providers:
            multimodal = "✅" if provider.supports_multimodal else "❌"
            streaming = "✅" if provider.supports_streaming else "❌"
            print(f"  • {provider.name}")
            print(f"    URL: {provider.base_url}")
            print(f"    Auth: {provider.authentication_type}")
            print(f"    Multimodal: {multimodal} | Streaming: {streaming}")
            print()
    
    def set_provider_url(self, provider_name: str, url: str):
        """Set the base URL for a provider via environment variable."""
        provider_config = get_service_provider_config(provider_name)
        if not provider_config:
            print(f"❌ Provider '{provider_name}' not found.")
            print("Use --list to see available providers.")
            return False
        
        env_var_name = f"{provider_name.upper()}_BASE_URL"
        
        print(f"🔧 Configuring {provider_config.name}")
        print(f"Setting {env_var_name}={url}")
        
        # Set in current environment
        os.environ[env_var_name] = url
        
        # Append to .env file
        env_file = Path(".env")
        env_line = f"{env_var_name}={url}\n"
        
        if env_file.exists():
            # Check if the variable already exists
            content = env_file.read_text()
            lines = content.split('\n')
            updated = False
            
            for i, line in enumerate(lines):
                if line.startswith(f"{env_var_name}="):
                    lines[i] = env_line.strip()
                    updated = True
                    break
            
            if updated:
                env_file.write_text('\n'.join(lines))
                print(f"✅ Updated {env_var_name} in .env file")
            else:
                with env_file.open('a') as f:
                    f.write(env_line)
                print(f"✅ Added {env_var_name} to .env file")
        else:
            env_file.write_text(env_line)
            print(f"✅ Created .env file with {env_var_name}")
        
        return True
    
    def generate_env_file(self):
        """Generate a comprehensive .env file template."""
        print("📝 Generating .env file template...")
        
        env_content = [
            "# OpenAI Codegen Adapter Configuration",
            "# =====================================",
            "",
            "# Codegen API Configuration (Required)",
            "CODEGEN_ORG_ID=your_org_id_here",
            "CODEGEN_TOKEN=sk-your-codegen-token-here",
            "",
            "# Server Configuration (Optional)",
            "SERVER_HOST=127.0.0.1",
            "SERVER_PORT=8887",
            "LOG_LEVEL=info",
            "",
            "# CORS Configuration (Optional)",
            "CORS_ORIGINS=[\"*\"]",
            "",
            "# Service Provider Base URLs (Optional - Override defaults)",
            "# =========================================================",
            "",
            "# Official Cloud Providers",
            "# OPENAI_BASE_URL=https://api.openai.com",
            "# ANTHROPIC_BASE_URL=https://api.anthropic.com",
            "# GOOGLE_VERTEX_AI_BASE_URL=https://us-central1-aiplatform.googleapis.com",
            "# GOOGLE_AI_STUDIO_BASE_URL=https://generativelanguage.googleapis.com",
            "# AZURE_OPENAI_BASE_URL=https://your-resource.openai.azure.com",
            "# COHERE_BASE_URL=https://api.cohere.ai",
            "# HUGGINGFACE_BASE_URL=https://api-inference.huggingface.co",
            "# MISTRAL_BASE_URL=https://api.mistral.ai",
            "# TOGETHER_BASE_URL=https://api.together.xyz",
            "# REPLICATE_BASE_URL=https://api.replicate.com",
            "",
            "# Local Development Providers",
            "# OPENAI_BASE_URL=http://localhost:8080  # LocalAI or other OpenAI-compatible",
            "# OPENAI_BASE_URL=http://localhost:11434  # Ollama",
            "# OPENAI_BASE_URL=http://localhost:1234   # LM Studio",
            "# OPENAI_BASE_URL=http://localhost:5000   # Text Generation WebUI",
            "# OPENAI_BASE_URL=http://localhost:8000   # vLLM",
            "",
            "# API Keys (Set these for the providers you're using)",
            "# ===================================================",
            "",
            "# OPENAI_API_KEY=sk-your-openai-key",
            "# ANTHROPIC_API_KEY=sk-ant-your-anthropic-key",
            "# GOOGLE_API_KEY=your-google-api-key",
            "# AZURE_OPENAI_API_KEY=your-azure-key",
            "# COHERE_API_KEY=your-cohere-key",
            "# HUGGINGFACE_API_KEY=your-hf-key",
            "# MISTRAL_API_KEY=your-mistral-key",
            "# TOGETHER_API_KEY=your-together-key",
            "# REPLICATE_API_TOKEN=your-replicate-token",
            "",
            "# Google Cloud Authentication (for Vertex AI)",
            "# GOOGLE_APPLICATION_CREDENTIALS=/path/to/service-account.json",
            "",
            "# Azure OpenAI Configuration",
            "# AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com",
            "# AZURE_OPENAI_API_VERSION=2024-02-01",
        ]
        
        env_file = Path(".env.template")
        env_file.write_text('\n'.join(env_content))
        
        print(f"✅ Generated {env_file}")
        print("\n📋 Next steps:")
        print("1. Copy .env.template to .env")
        print("2. Edit .env and set your actual values")
        print("3. Uncomment the providers you want to use")
        print("\nExample:")
        print("  cp .env.template .env")
        print("  # Edit .env with your preferred editor")
        print("  nano .env")
    
    def test_connection(self, provider_name: str):
        """Test connection to a service provider."""
        provider_config = get_service_provider_config(provider_name)
        if not provider_config:
            print(f"❌ Provider '{provider_name}' not found.")
            return False
        
        # Get the actual URL to use (with env var override)
        env_var_name = f"{provider_name.upper()}_BASE_URL"
        base_url = os.getenv(env_var_name, provider_config.base_url)
        
        print(f"🔍 Testing connection to {provider_config.name}")
        print(f"URL: {base_url}")
        
        # Try to connect to the base URL
        try:
            # For most APIs, try a simple GET to the base URL or health endpoint
            test_urls = [
                f"{base_url}/health",
                f"{base_url}/v1/models",
                f"{base_url}",
                f"{base_url}/api/health"
            ]
            
            for test_url in test_urls:
                try:
                    print(f"  Trying: {test_url}")
                    response = requests.get(test_url, timeout=5)
                    print(f"  ✅ Status: {response.status_code}")
                    
                    if response.status_code < 400:
                        print(f"✅ Connection successful to {provider_config.name}")
                        return True
                    
                except requests.exceptions.RequestException as e:
                    print(f"  ❌ Failed: {e}")
                    continue
            
            print(f"❌ Could not connect to {provider_config.name}")
            print("💡 Tips:")
            print(f"  • Make sure the server is running on {base_url}")
            print(f"  • Check firewall settings")
            print(f"  • Verify the URL is correct")
            
            return False
            
        except Exception as e:
            print(f"❌ Connection test failed: {e}")
            return False
    
    def show_current_config(self):
        """Show current configuration from environment variables."""
        print("🔧 Current Configuration")
        print("=" * 30)
        
        print("\n📋 Environment Variables:")
        for env_var, description in ENV_VAR_MAPPINGS.items():
            value = os.getenv(env_var, "Not set")
            status = "✅" if value != "Not set" else "❌"
            print(f"  {status} {env_var}: {value}")
        
        print("\n🔑 API Keys:")
        api_keys = [
            "OPENAI_API_KEY", "ANTHROPIC_API_KEY", "GOOGLE_API_KEY",
            "AZURE_OPENAI_API_KEY", "COHERE_API_KEY", "HUGGINGFACE_API_KEY",
            "MISTRAL_API_KEY", "TOGETHER_API_KEY", "REPLICATE_API_TOKEN"
        ]
        
        for key in api_keys:
            value = os.getenv(key)
            if value:
                masked_value = value[:8] + "..." + value[-4:] if len(value) > 12 else "***"
                print(f"  ✅ {key}: {masked_value}")
            else:
                print(f"  ❌ {key}: Not set")


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Configure service provider base URLs for OpenAI Codegen Adapter",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # List all available providers
  python scripts/configure_providers.py --list
  
  # Set OpenAI to use local Ollama server
  python scripts/configure_providers.py --provider openai --url http://localhost:11434
  
  # Set Anthropic to use local server
  python scripts/configure_providers.py --provider anthropic --url http://localhost:8081
  
  # Generate .env template file
  python scripts/configure_providers.py --generate-env
  
  # Test connection to a provider
  python scripts/configure_providers.py --test-connection openai
  
  # Show current configuration
  python scripts/configure_providers.py --show-config
        """
    )
    
    parser.add_argument("--list", action="store_true", 
                       help="List all available service providers")
    parser.add_argument("--provider", type=str,
                       help="Provider name to configure")
    parser.add_argument("--url", type=str,
                       help="Base URL to set for the provider")
    parser.add_argument("--generate-env", action="store_true",
                       help="Generate a .env template file")
    parser.add_argument("--test-connection", type=str,
                       help="Test connection to a provider")
    parser.add_argument("--show-config", action="store_true",
                       help="Show current configuration")
    
    args = parser.parse_args()
    
    cli = ProviderConfigCLI()
    
    if args.list:
        cli.list_providers()
    elif args.provider and args.url:
        cli.set_provider_url(args.provider, args.url)
    elif args.generate_env:
        cli.generate_env_file()
    elif args.test_connection:
        cli.test_connection(args.test_connection)
    elif args.show_config:
        cli.show_current_config()
    else:
        parser.print_help()


if __name__ == "__main__":
    main()

