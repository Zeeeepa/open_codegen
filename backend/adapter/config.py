"""
Configuration management for the OpenAI Codegen Adapter.
"""

import os
from typing import Optional
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
    port: int = 8001
    https_port: int = 8443
    log_level: str = "info"
    cors_origins: list = ["*"]
    transparent_mode: bool = False
    ssl_cert_path: Optional[str] = None
    ssl_key_path: Optional[str] = None
    bind_privileged_ports: bool = False  # For ports 80/443


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
        port=int(os.getenv("SERVER_PORT", "8001")),
        https_port=int(os.getenv("HTTPS_PORT", "8443")),
        log_level=os.getenv("LOG_LEVEL", "info"),
        cors_origins=os.getenv("CORS_ORIGINS", "*").split(","),
        transparent_mode=os.getenv("TRANSPARENT_MODE", "false").lower() == "true",
        ssl_cert_path=os.getenv("SSL_CERT_PATH"),
        ssl_key_path=os.getenv("SSL_KEY_PATH"),
        bind_privileged_ports=os.getenv("BIND_PRIVILEGED_PORTS", "false").lower() == "true"
    )
