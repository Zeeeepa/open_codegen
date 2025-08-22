"""
Configuration management for the OpenAI Codegen Adapter.
Enhanced with model mapping and authentication options.
"""

import os
import logging
from typing import Dict, Optional, List
from pathlib import Path
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

class EnhancedCodegenConfig(BaseModel):
    """Enhanced configuration for Codegen SDK connection."""
    org_id: str
    token: str
    base_url: Optional[str] = "https://codegen-sh--rest-api.modal.run"
    timeout: int = 300
    
    # New parameters
    model_mapping: Dict[str, str] = Field(default_factory=dict)
    default_model: Optional[str] = "codegen-standard"
    
    # Authentication settings
    use_auth_file: bool = True
    auth_file_path: Path = Field(default=Path("~/.config/codegen-sh/auth.json").expanduser())
    
    # Operation modes
    transparent_mode: bool = False
    intercept_openai: bool = True
    intercept_anthropic: bool = True
    intercept_gemini: bool = True
    
    # API settings
    max_retries: int = 20
    base_delay: int = 2
    
    # Prompt template settings
    prompt_template_enabled: bool = False
    prompt_template_prefix: Optional[str] = None
    prompt_template_suffix: Optional[str] = None
    
    @classmethod
    def from_environment(cls) -> "EnhancedCodegenConfig":
        """Create configuration from environment variables."""
        # Parse model mapping from environment
        model_mapping = {}
        mapping_str = os.environ.get("CODEGEN_MODEL_MAPPING", "")
        if mapping_str:
            try:
                pairs = mapping_str.split(",")
                for pair in pairs:
                    provider_model, codegen_model = pair.split(":")
                    model_mapping[provider_model.strip()] = codegen_model.strip()
            except Exception as e:
                logger.warning(f"Failed to parse CODEGEN_MODEL_MAPPING: {e}")
        
        return cls(
            org_id=os.environ.get("CODEGEN_ORG_ID", "323"),
            token=os.environ.get("CODEGEN_API_TOKEN", ""),  # Updated to use CODEGEN_API_TOKEN
            base_url=os.environ.get("CODEGEN_BASE_URL", "https://codegen-sh--rest-api.modal.run"),
            timeout=int(os.environ.get("CODEGEN_TIMEOUT", "300")),
            model_mapping=model_mapping,
            default_model=os.environ.get("CODEGEN_DEFAULT_MODEL", "codegen-standard"),
            use_auth_file=os.environ.get("CODEGEN_USE_AUTH_FILE", "true").lower() == "true",
            transparent_mode=os.environ.get("TRANSPARENT_MODE", "false").lower() == "true",
            intercept_openai=os.environ.get("INTERCEPT_OPENAI", "true").lower() == "true",
            intercept_anthropic=os.environ.get("INTERCEPT_ANTHROPIC", "true").lower() == "true",
            intercept_gemini=os.environ.get("INTERCEPT_GEMINI", "true").lower() == "true",
            max_retries=int(os.environ.get("CODEGEN_MAX_RETRIES", "20")),
            base_delay=int(os.environ.get("CODEGEN_BASE_DELAY", "2")),
            prompt_template_enabled=os.environ.get("CODEGEN_PROMPT_TEMPLATE_ENABLED", "false").lower() == "true",
            prompt_template_prefix=os.environ.get("CODEGEN_PROMPT_TEMPLATE_PREFIX"),
            prompt_template_suffix=os.environ.get("CODEGEN_PROMPT_TEMPLATE_SUFFIX")
        )


class ServerConfig(BaseModel):
    """Configuration for the adapter server."""
    host: str = "0.0.0.0"
    port: int = 8000
    https_port: int = 8443
    log_level: str = "info"
    cors_origins: List[str] = ["*"]
    transparent_mode: bool = False
    ssl_cert_path: Optional[str] = None
    ssl_key_path: Optional[str] = None
    bind_privileged_ports: bool = False  # For ports 80/443


def get_enhanced_codegen_config() -> EnhancedCodegenConfig:
    """Get enhanced Codegen configuration from environment variables."""
    config = EnhancedCodegenConfig.from_environment()
    logger.info(f"Loaded enhanced Codegen configuration - org_id: {config.org_id}, model: {config.default_model}")
    return config


def get_server_config() -> ServerConfig:
    """Get server configuration from environment variables."""
    return ServerConfig(
        host=os.environ.get("SERVER_HOST", "0.0.0.0"),
        port=int(os.environ.get("SERVER_PORT", "8000")),
        https_port=int(os.environ.get("HTTPS_PORT", "8443")),
        log_level=os.environ.get("LOG_LEVEL", "info"),
        cors_origins=os.environ.get("CORS_ORIGINS", "*").split(","),
        transparent_mode=os.environ.get("TRANSPARENT_MODE", "false").lower() == "true",
        ssl_cert_path=os.environ.get("SSL_CERT_PATH"),
        ssl_key_path=os.environ.get("SSL_KEY_PATH"),
        bind_privileged_ports=os.environ.get("BIND_PRIVILEGED_PORTS", "false").lower() == "true"
    )

