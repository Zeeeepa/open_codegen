#!/usr/bin/env python3
"""
Configuration Management for OpenAI Codegen Adapter
Provides centralized configuration loading and validation
"""
import os
import json
import logging
from typing import Dict, Any, Optional
from dataclasses import dataclass
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

@dataclass
class ServerConfig:
    """Server configuration settings"""
    host: str = "127.0.0.1"
    port: int = 8887
    log_level: str = "info"
    cors_origins: list = None
    
    def __post_init__(self):
        if self.cors_origins is None:
            self.cors_origins = ["*"]

@dataclass
class CodegenConfig:
    """Codegen API configuration settings"""
    org_id: str = ""
    api_token: str = ""
    base_url: str = "https://api.codegen.com"
    timeout: int = 30
    max_retries: int = 3
    
    def is_valid(self) -> bool:
        """Check if configuration is valid"""
        return bool(self.org_id and self.api_token)

@dataclass
class AppConfig:
    """Main application configuration"""
    server: ServerConfig
    codegen: CodegenConfig
    debug: bool = False
    
    @classmethod
    def from_env(cls) -> 'AppConfig':
        """Load configuration from environment variables"""
        # Server configuration
        server = ServerConfig(
            host=os.getenv("SERVER_HOST", "127.0.0.1"),
            port=int(os.getenv("SERVER_PORT", "8887")),
            log_level=os.getenv("LOG_LEVEL", "info"),
            cors_origins=json.loads(os.getenv("CORS_ORIGINS", '["*"]'))
        )
        
        # Codegen API configuration
        codegen = CodegenConfig(
            org_id=os.getenv("CODEGEN_ORG_ID", ""),
            api_token=os.getenv("CODEGEN_API_TOKEN", ""),
            base_url=os.getenv("CODEGEN_BASE_URL", "https://api.codegen.com"),
            timeout=int(os.getenv("CODEGEN_TIMEOUT", "30")),
            max_retries=int(os.getenv("CODEGEN_MAX_RETRIES", "3"))
        )
        
        # Debug mode
        debug = os.getenv("DEBUG", "false").lower() in ("true", "1", "yes")
        
        return cls(server=server, codegen=codegen, debug=debug)
    
    def validate(self) -> list:
        """Validate configuration and return list of errors"""
        errors = []
        
        if not self.codegen.is_valid():
            errors.append("Missing required Codegen API credentials (CODEGEN_ORG_ID, CODEGEN_API_TOKEN)")
        
        if self.server.port < 1 or self.server.port > 65535:
            errors.append(f"Invalid server port: {self.server.port}")
        
        if self.server.log_level not in ["debug", "info", "warning", "error", "critical"]:
            errors.append(f"Invalid log level: {self.server.log_level}")
        
        return errors
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary"""
        return {
            "server": {
                "host": self.server.host,
                "port": self.server.port,
                "log_level": self.server.log_level,
                "cors_origins": self.server.cors_origins
            },
            "codegen": {
                "org_id": self.codegen.org_id,
                "api_token": f"{self.codegen.api_token[:10]}..." if self.codegen.api_token else "",
                "base_url": self.codegen.base_url,
                "timeout": self.codegen.timeout,
                "max_retries": self.codegen.max_retries
            },
            "debug": self.debug
        }

def setup_logging(config: AppConfig) -> logging.Logger:
    """Setup application logging"""
    log_level = getattr(logging, config.server.log_level.upper())
    
    # Configure root logger
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Create application logger
    logger = logging.getLogger("codegen_adapter")
    
    if config.debug:
        logger.setLevel(logging.DEBUG)
        logger.debug("Debug mode enabled")
    
    return logger

def load_config() -> AppConfig:
    """Load and validate application configuration"""
    config = AppConfig.from_env()
    
    # Validate configuration
    errors = config.validate()
    if errors:
        raise ValueError(f"Configuration errors: {', '.join(errors)}")
    
    return config

if __name__ == "__main__":
    # Test configuration loading
    try:
        config = load_config()
        logger = setup_logging(config)
        
        logger.info("Configuration loaded successfully")
        logger.debug(f"Configuration: {json.dumps(config.to_dict(), indent=2)}")
        
    except Exception as e:
        print(f"Configuration error: {e}")
        exit(1)

