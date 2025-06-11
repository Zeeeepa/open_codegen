"""
Configuration settings for the OpenAI Codegen Adapter.
"""

import os
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List


class Config(BaseModel):
    """Configuration settings for the OpenAI Codegen Adapter."""
    
    # Server settings
    host: str = "localhost"  # Changed from "0.0.0.0" to "localhost"
    port: int = 8887
    debug: bool = False
    
    # API keys (optional, can be set via environment variables)
    openai_api_key: Optional[str] = None
    codegen_api_key: Optional[str] = None
    
    # Codegen SDK settings
    codegen_base_url: Optional[str] = None
    
    # Default models
    default_model: str = "gpt-3.5-turbo"
    
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
            host=os.getenv("SERVER_HOST", "localhost"),  # Changed from "0.0.0.0" to "localhost"
            port=int(os.getenv("SERVER_PORT", "8887")),
            debug=os.getenv("DEBUG", "").lower() in ("true", "1", "yes"),
            openai_api_key=os.getenv("OPENAI_API_KEY"),
            codegen_api_key=os.getenv("CODEGEN_API_KEY") or os.getenv("CODEGEN_TOKEN"),
            codegen_base_url=os.getenv("CODEGEN_BASE_URL"),
            default_model=os.getenv("DEFAULT_MODEL", "gpt-3.5-turbo"),
            rate_limit_enabled=os.getenv("RATE_LIMIT_ENABLED", "").lower() not in ("false", "0", "no"),
            rate_limit_requests=int(os.getenv("RATE_LIMIT_REQUESTS", "60")),
            rate_limit_window_seconds=int(os.getenv("RATE_LIMIT_WINDOW_SECONDS", "60")),
        )


# Create a global config instance
config = Config.from_env()

