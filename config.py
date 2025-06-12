"""
Configuration for the unified API system.
"""

import os
from dataclasses import dataclass


@dataclass
class Config:
    """Configuration for the unified API system."""
    host: str = "localhost"
    port: int = 8887
    debug: bool = False
    enable_web_ui: bool = True
    static_files_path: str = "static"
    default_openai_model: str = "gpt-3.5-turbo"
    default_anthropic_model: str = "claude-3-sonnet-20240229"
    default_google_model: str = "gemini-1.5-pro"


def get_config() -> Config:
    """Get configuration from environment variables or defaults."""
    return Config(
        host=os.getenv("HOST", "localhost"),
        port=int(os.getenv("PORT", "8887")),
        debug=os.getenv("DEBUG", "").lower() in ("true", "1", "yes"),
        enable_web_ui=os.getenv("ENABLE_WEB_UI", "true").lower() in ("true", "1", "yes"),
        static_files_path=os.getenv("STATIC_FILES_PATH", "static"),
        default_openai_model=os.getenv("DEFAULT_OPENAI_MODEL", "gpt-3.5-turbo"),
        default_anthropic_model=os.getenv("DEFAULT_ANTHROPIC_MODEL", "claude-3-sonnet-20240229"),
        default_google_model=os.getenv("DEFAULT_GOOGLE_MODEL", "gemini-1.5-pro")
    )

