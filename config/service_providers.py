"""
Service Provider Base URLs Configuration
========================================

This module contains the official base URLs for all supported AI service providers.
Use these URLs for local development, testing, and production deployments.

For local development, you can override these URLs using environment variables
or by modifying the configuration in your application.
"""

from typing import Dict, Optional
import os
from dataclasses import dataclass


@dataclass
class ServiceProviderConfig:
    """Configuration for a service provider."""
    name: str
    base_url: str
    api_version: str
    documentation_url: str
    authentication_type: str
    default_model: Optional[str] = None
    supports_streaming: bool = True
    supports_multimodal: bool = False


class ServiceProviderURLs:
    """
    Official base URLs for all supported AI service providers.
    
    These URLs are the official endpoints provided by each service.
    For local development, you can override these using environment variables.
    """
    
    # OpenAI Service URLs
    OPENAI = ServiceProviderConfig(
        name="OpenAI",
        base_url="https://api.openai.com",
        api_version="v1",
        documentation_url="https://platform.openai.com/docs/api-reference",
        authentication_type="Bearer Token",
        default_model="gpt-4",
        supports_streaming=True,
        supports_multimodal=True
    )
    
    # Anthropic Claude Service URLs
    ANTHROPIC = ServiceProviderConfig(
        name="Anthropic Claude",
        base_url="https://api.anthropic.com",
        api_version="v1",
        documentation_url="https://docs.anthropic.com/claude/reference",
        authentication_type="x-api-key Header",
        default_model="claude-3-5-sonnet-20241022",
        supports_streaming=True,
        supports_multimodal=True
    )
    
    # Google Vertex AI Service URLs
    GOOGLE_VERTEX_AI = ServiceProviderConfig(
        name="Google Vertex AI",
        base_url="https://{location}-aiplatform.googleapis.com",
        api_version="v1",
        documentation_url="https://cloud.google.com/vertex-ai/docs/reference/rest",
        authentication_type="OAuth 2.0 / Service Account",
        default_model="gemini-1.5-pro",
        supports_streaming=True,
        supports_multimodal=True
    )
    
    # Google AI Studio (Gemini API) Service URLs
    GOOGLE_AI_STUDIO = ServiceProviderConfig(
        name="Google AI Studio (Gemini API)",
        base_url="https://generativelanguage.googleapis.com",
        api_version="v1beta",
        documentation_url="https://ai.google.dev/api/rest",
        authentication_type="API Key",
        default_model="gemini-1.5-pro",
        supports_streaming=True,
        supports_multimodal=True
    )
    
    # Azure OpenAI Service URLs
    AZURE_OPENAI = ServiceProviderConfig(
        name="Azure OpenAI",
        base_url="https://{resource-name}.openai.azure.com",
        api_version="2024-02-01",
        documentation_url="https://learn.microsoft.com/en-us/azure/ai-services/openai/reference",
        authentication_type="API Key / Azure AD",
        default_model="gpt-4",
        supports_streaming=True,
        supports_multimodal=True
    )
    
    # Cohere Service URLs
    COHERE = ServiceProviderConfig(
        name="Cohere",
        base_url="https://api.cohere.ai",
        api_version="v1",
        documentation_url="https://docs.cohere.com/reference/about",
        authentication_type="Bearer Token",
        default_model="command-r-plus",
        supports_streaming=True,
        supports_multimodal=False
    )
    
    # Hugging Face Inference API URLs
    HUGGINGFACE = ServiceProviderConfig(
        name="Hugging Face Inference API",
        base_url="https://api-inference.huggingface.co",
        api_version="v1",
        documentation_url="https://huggingface.co/docs/api-inference/index",
        authentication_type="Bearer Token",
        default_model="meta-llama/Llama-2-70b-chat-hf",
        supports_streaming=True,
        supports_multimodal=True
    )
    
    # Mistral AI Service URLs
    MISTRAL = ServiceProviderConfig(
        name="Mistral AI",
        base_url="https://api.mistral.ai",
        api_version="v1",
        documentation_url="https://docs.mistral.ai/api/",
        authentication_type="Bearer Token",
        default_model="mistral-large-latest",
        supports_streaming=True,
        supports_multimodal=False
    )
    
    # Together AI Service URLs
    TOGETHER = ServiceProviderConfig(
        name="Together AI",
        base_url="https://api.together.xyz",
        api_version="v1",
        documentation_url="https://docs.together.ai/reference/inference",
        authentication_type="Bearer Token",
        default_model="meta-llama/Llama-2-70b-chat-hf",
        supports_streaming=True,
        supports_multimodal=True
    )
    
    # Replicate Service URLs
    REPLICATE = ServiceProviderConfig(
        name="Replicate",
        base_url="https://api.replicate.com",
        api_version="v1",
        documentation_url="https://replicate.com/docs/reference/http",
        authentication_type="Bearer Token",
        default_model="meta/llama-2-70b-chat",
        supports_streaming=True,
        supports_multimodal=True
    )


class LocalDevelopmentURLs:
    """
    Local development URLs for testing and development.
    
    These URLs point to local instances of services or mock servers
    that you can run for development and testing purposes.
    """
    
    # Local OpenAI-compatible server (like text-generation-webui, LocalAI, etc.)
    LOCAL_OPENAI_COMPATIBLE = ServiceProviderConfig(
        name="Local OpenAI Compatible",
        base_url="http://localhost:8080",
        api_version="v1",
        documentation_url="https://github.com/oobabooga/text-generation-webui/wiki/12-%E2%80%90-OpenAI-API",
        authentication_type="None / API Key",
        default_model="local-model",
        supports_streaming=True,
        supports_multimodal=False
    )
    
    # Local Ollama server
    OLLAMA = ServiceProviderConfig(
        name="Ollama",
        base_url="http://localhost:11434",
        api_version="v1",
        documentation_url="https://github.com/ollama/ollama/blob/main/docs/api.md",
        authentication_type="None",
        default_model="llama2",
        supports_streaming=True,
        supports_multimodal=True
    )
    
    # Local LM Studio server
    LM_STUDIO = ServiceProviderConfig(
        name="LM Studio",
        base_url="http://localhost:1234",
        api_version="v1",
        documentation_url="https://lmstudio.ai/docs/api/openai-api",
        authentication_type="None / API Key",
        default_model="local-model",
        supports_streaming=True,
        supports_multimodal=False
    )
    
    # Local text-generation-webui server
    TEXT_GENERATION_WEBUI = ServiceProviderConfig(
        name="Text Generation WebUI",
        base_url="http://localhost:5000",
        api_version="v1",
        documentation_url="https://github.com/oobabooga/text-generation-webui",
        authentication_type="None / API Key",
        default_model="local-model",
        supports_streaming=True,
        supports_multimodal=False
    )
    
    # Local vLLM server
    VLLM = ServiceProviderConfig(
        name="vLLM",
        base_url="http://localhost:8000",
        api_version="v1",
        documentation_url="https://docs.vllm.ai/en/latest/serving/openai_compatible_server.html",
        authentication_type="None / API Key",
        default_model="local-model",
        supports_streaming=True,
        supports_multimodal=True
    )


def get_service_provider_config(provider_name: str) -> Optional[ServiceProviderConfig]:
    """
    Get configuration for a specific service provider.
    
    Args:
        provider_name: Name of the service provider (case-insensitive)
        
    Returns:
        ServiceProviderConfig object or None if not found
    """
    provider_name = provider_name.upper().replace("-", "_").replace(" ", "_")
    
    # Check official providers
    if hasattr(ServiceProviderURLs, provider_name):
        return getattr(ServiceProviderURLs, provider_name)
    
    # Check local development providers
    if hasattr(LocalDevelopmentURLs, provider_name):
        return getattr(LocalDevelopmentURLs, provider_name)
    
    return None


def get_all_service_providers() -> Dict[str, ServiceProviderConfig]:
    """
    Get all available service provider configurations.
    
    Returns:
        Dictionary mapping provider names to their configurations
    """
    providers = {}
    
    # Add official providers
    for attr_name in dir(ServiceProviderURLs):
        if not attr_name.startswith('_'):
            attr_value = getattr(ServiceProviderURLs, attr_name)
            if isinstance(attr_value, ServiceProviderConfig):
                providers[attr_name.lower()] = attr_value
    
    # Add local development providers
    for attr_name in dir(LocalDevelopmentURLs):
        if not attr_name.startswith('_'):
            attr_value = getattr(LocalDevelopmentURLs, attr_name)
            if isinstance(attr_value, ServiceProviderConfig):
                providers[f"local_{attr_name.lower()}"] = attr_value
    
    return providers


def get_base_url_from_env(provider_name: str, default_config: ServiceProviderConfig) -> str:
    """
    Get base URL from environment variable or use default.
    
    Args:
        provider_name: Name of the service provider
        default_config: Default configuration
        
    Returns:
        Base URL to use
    """
    env_var_name = f"{provider_name.upper()}_BASE_URL"
    return os.getenv(env_var_name, default_config.base_url)


# Environment variable mappings for easy configuration
ENV_VAR_MAPPINGS = {
    "OPENAI_BASE_URL": "Override OpenAI base URL",
    "ANTHROPIC_BASE_URL": "Override Anthropic base URL", 
    "GOOGLE_VERTEX_AI_BASE_URL": "Override Google Vertex AI base URL",
    "GOOGLE_AI_STUDIO_BASE_URL": "Override Google AI Studio base URL",
    "AZURE_OPENAI_BASE_URL": "Override Azure OpenAI base URL",
    "COHERE_BASE_URL": "Override Cohere base URL",
    "HUGGINGFACE_BASE_URL": "Override Hugging Face base URL",
    "MISTRAL_BASE_URL": "Override Mistral AI base URL",
    "TOGETHER_BASE_URL": "Override Together AI base URL",
    "REPLICATE_BASE_URL": "Override Replicate base URL",
    "LOCAL_OPENAI_COMPATIBLE_BASE_URL": "Override local OpenAI compatible server URL",
    "OLLAMA_BASE_URL": "Override Ollama server URL",
    "LM_STUDIO_BASE_URL": "Override LM Studio server URL",
    "TEXT_GENERATION_WEBUI_BASE_URL": "Override text-generation-webui server URL",
    "VLLM_BASE_URL": "Override vLLM server URL"
}


if __name__ == "__main__":
    # Example usage and testing
    print("🌐 Service Provider Base URLs Configuration")
    print("=" * 50)
    
    all_providers = get_all_service_providers()
    
    print(f"\n📋 Available Service Providers ({len(all_providers)}):")
    for name, config in all_providers.items():
        print(f"  • {config.name}: {config.base_url}")
    
    print(f"\n🔧 Environment Variable Overrides:")
    for env_var, description in ENV_VAR_MAPPINGS.items():
        print(f"  • {env_var}: {description}")
    
    print(f"\n🧪 Example Usage:")
    print(f"  export OPENAI_BASE_URL=http://localhost:8080")
    print(f"  export ANTHROPIC_BASE_URL=http://localhost:8081")
    print(f"  python -m openai_codegen_adapter.main")

