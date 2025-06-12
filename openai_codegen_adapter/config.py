"""
Configuration management for the OpenAI Codegen Adapter.
"""

import os
from typing import Optional, List
from pydantic import BaseModel


class CodegenConfig(BaseModel):
    """Configuration for Codegen SDK connection."""
    org_id: str
    token: str
    base_url: Optional[str] = None
    timeout: int = 300  # 5 minutes default timeout


class ServerConfig(BaseModel):
    """Configuration for the adapter server."""
    host: str = "0.0.0.0"
    port: int = 8887
    log_level: str = "info"
    cors_origins: List[str] = ["*"]


def get_codegen_config() -> CodegenConfig:
    """Get Codegen configuration from environment variables or defaults."""
    return CodegenConfig(
        org_id=os.getenv("CODEGEN_ORG_ID", "323"),
        token=os.getenv("CODEGEN_TOKEN", "sk-ce027fa7-3c8d-4beb-8c86-ed8ae982ac99"),
        base_url=os.getenv("CODEGEN_BASE_URL"),
        timeout=int(os.getenv("CODEGEN_TIMEOUT", "300"))
    )


def get_server_config() -> ServerConfig:
    """Get server configuration from environment variables or defaults."""
    return ServerConfig(
        host=os.getenv("SERVER_HOST", "0.0.0.0"),
        port=int(os.getenv("SERVER_PORT", "8887")),
        log_level=os.getenv("LOG_LEVEL", "info"),
        cors_origins=os.getenv("CORS_ORIGINS", "*").split(",")
    )

