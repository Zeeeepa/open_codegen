"""
Configuration management for OpenAI Codegen Adapter
"""

import os
from typing import Optional
from pydantic_settings import BaseSettings
from pydantic import Field


class CodegenConfig(BaseSettings):
    """Configuration for Codegen API integration"""
    
    # Codegen API settings
    api_token: Optional[str] = Field(default=None, alias="CODEGEN_API_TOKEN")
    org_id: Optional[str] = Field(default=None, alias="CODEGEN_ORG_ID")  # Keep as str for compatibility
    base_url: str = Field(default="https://api.codegen.com", alias="CODEGEN_BASE_URL")
    
    # Request settings
    default_timeout: int = Field(default=300, alias="CODEGEN_TIMEOUT")  # 5 minutes
    max_retries: int = Field(default=3, alias="CODEGEN_MAX_RETRIES")
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False
        extra = "ignore"  # Ignore extra fields


class ServerConfig(BaseSettings):
    """Configuration for FastAPI server"""
    
    # Server settings
    host: str = Field(default="0.0.0.0", alias="SERVER_HOST")
    port: int = Field(default=8887, alias="SERVER_PORT")
    log_level: str = Field(default="info", alias="LOG_LEVEL")
    
    # CORS settings - handle the JSON string properly
    cors_origins: list = Field(default=["*"])
    allow_credentials: bool = Field(default=True, alias="SERVER_ALLOW_CREDENTIALS")
    allow_methods: list = Field(default=["*"], alias="SERVER_ALLOW_METHODS")
    allow_headers: list = Field(default=["*"], alias="SERVER_ALLOW_HEADERS")
    
    # Rate limiting
    rate_limit_enabled: bool = Field(default=False, alias="SERVER_RATE_LIMIT_ENABLED")
    rate_limit_requests: int = Field(default=100, alias="SERVER_RATE_LIMIT_REQUESTS")
    rate_limit_window: int = Field(default=60, alias="SERVER_RATE_LIMIT_WINDOW")  # seconds
    
    # Security
    api_key_header: str = Field(default="Authorization", alias="SERVER_API_KEY_HEADER")
    require_api_key: bool = Field(default=False, alias="SERVER_REQUIRE_API_KEY")  # Set to False for testing
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False
        extra = "ignore"  # Ignore extra fields
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Handle CORS_ORIGINS from environment
        cors_env = os.getenv("CORS_ORIGINS")
        if cors_env:
            try:
                # Try to parse as JSON-like string
                if cors_env.startswith("[") and cors_env.endswith("]"):
                    # Remove brackets and quotes, split by comma
                    cors_env = cors_env.strip("[]")
                    self.cors_origins = [origin.strip().strip('"') for origin in cors_env.split(",")]
                else:
                    self.cors_origins = [cors_env]
            except:
                self.cors_origins = ["*"]  # Fallback


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
export SERVER_HOST="0.0.0.0"
export SERVER_PORT="8887"
export LOG_LEVEL="info"

# Optional: Request settings
export CODEGEN_TIMEOUT="300"
export CODEGEN_MAX_RETRIES="3"

# Optional: Server security
export SERVER_REQUIRE_API_KEY="false"
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
    print(f"  Timeout: {codegen_config.default_timeout}s")
    
    print(f"\nServer Config:")
    print(f"  Host: {server_config.host}")
    print(f"  Port: {server_config.port}")
    print(f"  Log Level: {server_config.log_level}")
    print(f"  CORS Origins: {server_config.cors_origins}")
    print(f"  Rate Limiting: {'Enabled' if server_config.rate_limit_enabled else 'Disabled'}")
    print(f"  API Key Required: {'Yes' if server_config.require_api_key else 'No'}")

