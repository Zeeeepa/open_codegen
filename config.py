"""
Configuration management for the unified API system.
Handles environment variables and settings for all three providers.
"""

import os
from typing import Optional
from pydantic import BaseModel


class APIConfig(BaseModel):
    """Configuration for API settings."""
    
    # Codegen settings
    codegen_api_key: Optional[str] = None
    codegen_base_url: Optional[str] = None
    
    # Server settings
    host: str = "0.0.0.0"
    port: int = 8887
    debug: bool = False
    
    # Provider settings
    default_openai_model: str = "gpt-3.5-turbo"
    default_anthropic_model: str = "claude-3-sonnet-20240229"
    default_google_model: str = "gemini-1.5-pro"
    
    # Request settings
    default_max_tokens: int = 150
    default_temperature: float = 0.7
    request_timeout: int = 30
    
    # UI settings
    enable_web_ui: bool = True
    static_files_path: str = "static"
    
    @classmethod
    def from_env(cls) -> "APIConfig":
        """Create configuration from environment variables."""
        return cls(
            codegen_api_key=os.getenv("CODEGEN_API_KEY"),
            codegen_base_url=os.getenv("CODEGEN_BASE_URL"),
            host=os.getenv("HOST", "0.0.0.0"),
            port=int(os.getenv("PORT", "8887")),
            debug=os.getenv("DEBUG", "false").lower() == "true",
            default_openai_model=os.getenv("DEFAULT_OPENAI_MODEL", "gpt-3.5-turbo"),
            default_anthropic_model=os.getenv("DEFAULT_ANTHROPIC_MODEL", "claude-3-sonnet-20240229"),
            default_google_model=os.getenv("DEFAULT_GOOGLE_MODEL", "gemini-1.5-pro"),
            default_max_tokens=int(os.getenv("DEFAULT_MAX_TOKENS", "150")),
            default_temperature=float(os.getenv("DEFAULT_TEMPERATURE", "0.7")),
            request_timeout=int(os.getenv("REQUEST_TIMEOUT", "30")),
            enable_web_ui=os.getenv("ENABLE_WEB_UI", "true").lower() == "true",
            static_files_path=os.getenv("STATIC_FILES_PATH", "static")
        )


# Global configuration instance
config = APIConfig.from_env()


def get_config() -> APIConfig:
    """Get the global configuration instance."""
    return config


def reload_config() -> APIConfig:
    """Reload configuration from environment variables."""
    global config
    config = APIConfig.from_env()
    return config

