"""
Configuration management for OpenAI Codegen Adapter
"""

import os
from typing import Optional
from pydantic_settings import BaseSettings


class CodegenConfig(BaseSettings):
    """Configuration for Codegen API integration"""
    
    # Codegen API settings
    api_token: Optional[str] = None
    org_id: Optional[int] = None  # Changed from str to int
    base_url: str = "https://api.codegen.com"
    
    # Server settings
    host: str = "0.0.0.0"
    port: int = 8000
    log_level: str = "INFO"
    
    # Request settings
    default_timeout: int = 300  # 5 minutes
    max_retries: int = 3
    
    class Config:
        env_prefix = "CODEGEN_"
        case_sensitive = False


class ServerConfig(BaseSettings):
    """Configuration for FastAPI server"""
    
    # CORS settings
    allow_origins: list = ["*"]
    allow_credentials: bool = True
    allow_methods: list = ["*"]
    allow_headers: list = ["*"]
    
    # Rate limiting
    rate_limit_enabled: bool = False
    rate_limit_requests: int = 100
    rate_limit_window: int = 60  # seconds
    
    # Security
    api_key_header: str = "Authorization"
    require_api_key: bool = True
    
    class Config:
        env_prefix = "SERVER_"
        case_sensitive = False


def get_codegen_config() -> CodegenConfig:
    """Get Codegen configuration from environment variables"""
    return CodegenConfig()


def get_server_config() -> ServerConfig:
    """Get server configuration from environment variables"""
    return ServerConfig()


def validate_config() -> bool:
    """Validate that required configuration is present"""
    config = get_codegen_config()
    
    if not config.api_token:
        print("⚠️  Warning: CODEGEN_API_TOKEN not set")
        return False
    
    if not config.org_id:
        print("⚠️  Warning: CODEGEN_ORG_ID not set")
        return False
    
    return True


# Environment variable examples
ENV_EXAMPLE = """
# Example environment variables for OpenAI Codegen Adapter

# Required: Codegen API credentials
export CODEGEN_API_TOKEN="sk-ce027fa7-3c8d-4beb-8c86-ed8ae982ac99"
export CODEGEN_ORG_ID="323"

# Optional: Server configuration
export CODEGEN_BASE_URL="https://api.codegen.com"
export CODEGEN_HOST="0.0.0.0"
export CODEGEN_PORT="8000"
export CODEGEN_LOG_LEVEL="INFO"

# Optional: Request settings
export CODEGEN_DEFAULT_TIMEOUT="300"
export CODEGEN_MAX_RETRIES="3"

# Optional: Server security
export SERVER_REQUIRE_API_KEY="true"
export SERVER_RATE_LIMIT_ENABLED="false"
"""

if __name__ == "__main__":
    print("OpenAI Codegen Adapter Configuration")
    print("=" * 40)
    
    # Validate configuration
    if validate_config():
        print("✅ Configuration is valid")
    else:
        print("❌ Configuration is incomplete")
        print("\nExample environment variables:")
        print(ENV_EXAMPLE)
    
    # Show current config
    codegen_config = get_codegen_config()
    server_config = get_server_config()
    
    print(f"\nCodegen Config:")
    print(f"  API Token: {'***' + codegen_config.api_token[-4:] if codegen_config.api_token else 'Not set'}")
    print(f"  Org ID: {codegen_config.org_id or 'Not set'}")
    print(f"  Base URL: {codegen_config.base_url}")
    print(f"  Log Level: {codegen_config.log_level}")
    
    print(f"\nServer Config:")
    print(f"  Host: {server_config.allow_origins}")
    print(f"  Rate Limiting: {'Enabled' if server_config.rate_limit_enabled else 'Disabled'}")
    print(f"  API Key Required: {'Yes' if server_config.require_api_key else 'No'}")
