"""
Configuration management for the Universal AI API Gateway
"""

import json
import logging
import os
from pathlib import Path
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

class ConfigManager:
    """Manages system configuration."""
    
    def __init__(self, config_file: str = "config.json"):
        self.config_file = Path(config_file)
        self.config_cache = None
        
    def load_config(self) -> Dict[str, Any]:
        """Load configuration from file or create default."""
        
        if self.config_cache:
            return self.config_cache
        
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r') as f:
                    config = json.load(f)
                logger.info(f"Loaded configuration from {self.config_file}")
            except Exception as e:
                logger.error(f"Failed to load config: {e}")
                config = self._get_default_config()
        else:
            config = self._get_default_config()
            self.save_config(config)
        
        # Override with environment variables
        config = self._apply_env_overrides(config)
        
        self.config_cache = config
        return config
    
    def save_config(self, config: Dict[str, Any]):
        """Save configuration to file."""
        
        try:
            with open(self.config_file, 'w') as f:
                json.dump(config, f, indent=2)
            logger.info(f"Saved configuration to {self.config_file}")
            self.config_cache = config
        except Exception as e:
            logger.error(f"Failed to save config: {e}")
            raise
    
    def _get_default_config(self) -> Dict[str, Any]:
        """Get default configuration."""
        
        return {
            "server": {
                "host": "0.0.0.0",
                "port": 8000,
                "workers": 1,
                "reload": False
            },
            "gateway": {
                "timeout": 300,
                "max_retries": 3,
                "enable_streaming": True,
                "enable_logging": True
            },
            "providers": {
                "zai": {
                    "enabled": True,
                    "priority": 1,
                    "timeout": 60,
                    "credentials": {
                        "base_url": "https://chat.z.ai",
                        "username": os.getenv("ZAI_USERNAME", ""),
                        "password": os.getenv("ZAI_PASSWORD", "")
                    }
                },
                "k2": {
                    "enabled": True,
                    "priority": 2,
                    "timeout": 60,
                    "credentials": {
                        "base_url": "https://www.k2think.ai",
                        "username": os.getenv("K2_USERNAME", ""),
                        "password": os.getenv("K2_PASSWORD", "")
                    }
                },
                "qwen": {
                    "enabled": True,
                    "priority": 3,
                    "timeout": 60,
                    "credentials": {
                        "base_url": "https://chat.qwen.ai",
                        "username": os.getenv("QWEN_USERNAME", ""),
                        "password": os.getenv("QWEN_PASSWORD", "")
                    }
                },
                "grok": {
                    "enabled": True,
                    "priority": 4,
                    "timeout": 60,
                    "credentials": {
                        "base_url": "https://grok.com",
                        "username": os.getenv("GROK_USERNAME", ""),
                        "password": os.getenv("GROK_PASSWORD", "")
                    }
                },
                "chatgpt": {
                    "enabled": True,
                    "priority": 5,
                    "timeout": 60,
                    "credentials": {
                        "api_key": os.getenv("CHATGPT_API_KEY", "")
                    }
                },
                "bing": {
                    "enabled": True,
                    "priority": 6,
                    "timeout": 60,
                    "credentials": {}
                },
                "codegen": {
                    "enabled": True,
                    "priority": 7,
                    "timeout": 300,
                    "credentials": {
                        "api_token": os.getenv("CODEGEN_API_TOKEN", ""),
                        "org_id": os.getenv("CODEGEN_ORG_ID", "323"),
                        "base_url": os.getenv("CODEGEN_BASE_URL", "https://codegen-sh--rest-api.modal.run")
                    }
                },
                "copilot": {
                    "enabled": False,
                    "priority": 8,
                    "timeout": 60,
                    "credentials": {
                        "github_token": os.getenv("GITHUB_TOKEN", "")
                    }
                },
                "talkai": {
                    "enabled": False,
                    "priority": 9,
                    "timeout": 60,
                    "credentials": {}
                }
            },
            "load_balancing": {
                "strategy": "priority",  # priority, round_robin, performance
                "health_check_interval": 60,
                "failure_threshold": 3,
                "recovery_time": 300
            },
            "flareprox": {
                "enabled": False,
                "api_token": os.getenv("CLOUDFLARE_API_TOKEN", ""),
                "account_id": os.getenv("CLOUDFLARE_ACCOUNT_ID", ""),
                "zone_id": os.getenv("CLOUDFLARE_ZONE_ID", "")
            },
            "security": {
                "api_keys": [],
                "rate_limiting": {
                    "enabled": True,
                    "requests_per_minute": 60
                }
            }
        }
    
    def _apply_env_overrides(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Apply environment variable overrides."""
        
        # Server overrides
        if os.getenv("SERVER_HOST"):
            config["server"]["host"] = os.getenv("SERVER_HOST")
        if os.getenv("SERVER_PORT"):
            config["server"]["port"] = int(os.getenv("SERVER_PORT"))
        
        # Gateway overrides
        if os.getenv("GATEWAY_TIMEOUT"):
            config["gateway"]["timeout"] = int(os.getenv("GATEWAY_TIMEOUT"))
        
        return config
    
    def get_provider_config(self, provider_name: str) -> Optional[Dict[str, Any]]:
        """Get configuration for a specific provider."""
        
        config = self.load_config()
        return config.get("providers", {}).get(provider_name)
    
    def update_provider_config(self, provider_name: str, provider_config: Dict[str, Any]):
        """Update configuration for a specific provider."""
        
        config = self.load_config()
        if "providers" not in config:
            config["providers"] = {}
        
        config["providers"][provider_name] = provider_config
        self.save_config(config)
    
    def get_enabled_providers(self) -> Dict[str, Dict[str, Any]]:
        """Get all enabled providers."""
        
        config = self.load_config()
        providers = config.get("providers", {})
        
        return {
            name: provider_config
            for name, provider_config in providers.items()
            if provider_config.get("enabled", False)
        }
