"""
Configuration settings for the unified API system.
"""

import os
from pydantic import BaseSettings, Field
from typing import Optional, Dict, Any, List


class Config(BaseSettings):
    """Configuration settings for the unified API system."""
    
    # Server settings
    host: str = "localhost"  # Changed from "0.0.0.0" to "localhost"
    port: int = 8887
    debug: bool = False
    
    # API keys (optional, can be set via environment variables)
    openai_api_key: Optional[str] = None
    anthropic_api_key: Optional[str] = None
    google_api_key: Optional[str] = None
    codegen_api_key: Optional[str] = None
    
    # Codegen SDK settings
    codegen_base_url: Optional[str] = None
    
    # Default models
    default_openai_model: str = "gpt-3.5-turbo"
    default_anthropic_model: str = "claude-3-sonnet-20240229"
    default_google_model: str = "gemini-1.5-pro"
    
    # Rate limiting
    rate_limit_enabled: bool = True
    rate_limit_requests: int = 60
    rate_limit_window_seconds: int = 60
    
    class Config:
        """Pydantic config"""
        env_file = ".env"
        env_file_encoding = "utf-8"
        
    @classmethod
    def from_env(cls) -> "Config":
        """Create config from environment variables."""
        return cls(
            host=os.getenv("HOST", "localhost"),  # Changed from "0.0.0.0" to "localhost"
            port=int(os.getenv("PORT", "8887")),
            debug=os.getenv("DEBUG", "").lower() in ("true", "1", "yes"),
            openai_api_key=os.getenv("OPENAI_API_KEY"),
            anthropic_api_key=os.getenv("ANTHROPIC_API_KEY"),
            google_api_key=os.getenv("GOOGLE_API_KEY"),
            codegen_api_key=os.getenv("CODEGEN_API_KEY") or os.getenv("CODEGEN_TOKEN"),
            codegen_base_url=os.getenv("CODEGEN_BASE_URL"),
            default_openai_model=os.getenv("DEFAULT_OPENAI_MODEL", "gpt-3.5-turbo"),
            default_anthropic_model=os.getenv("DEFAULT_ANTHROPIC_MODEL", "claude-3-sonnet-20240229"),
            default_google_model=os.getenv("DEFAULT_GOOGLE_MODEL", "gemini-1.5-pro"),
            rate_limit_enabled=os.getenv("RATE_LIMIT_ENABLED", "").lower() not in ("false", "0", "no"),
            rate_limit_requests=int(os.getenv("RATE_LIMIT_REQUESTS", "60")),
            rate_limit_window_seconds=int(os.getenv("RATE_LIMIT_WINDOW_SECONDS", "60")),
        )


# Create a global config instance
config = Config.from_env()

