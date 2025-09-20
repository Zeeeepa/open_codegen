"""
Default Endpoints Configuration - Auto-configure Z.ai and Codegen API by default
"""
import os
import logging
from typing import Dict, List, Any, Optional
import asyncio

logger = logging.getLogger(__name__)

class DefaultEndpointsConfig:
    """
    Manages default endpoint configurations for Z.ai and Codegen API
    """
    
    def __init__(self):
        self.default_endpoints = self._get_default_configurations()
    
    def _get_default_configurations(self) -> List[Dict[str, Any]]:
        """
        Get default endpoint configurations
        """
        return [
            {
                "name": "zai-sdk",
                "provider_type": "zai_sdk",
                "base_url": "https://chat.z.ai",
                "priority": 100,  # Highest priority as requested
                "enabled": True,
                "auto_configured": True,
                "description": "Z.ai Python SDK - highest priority default endpoint with automatic authentication",
                "config": {
                    "base_url": "https://chat.z.ai",
                    "timeout_seconds": 180,
                    "auto_auth": True,  # Automatic guest token authentication
                    "verbose": False,  # Set to True for debugging
                    "model_mapping": {
                        "gpt-3.5-turbo": "glm-4.5v",
                        "gpt-4": "0727-360B-API",
                        "gpt-4-turbo": "0727-360B-API",
                        "claude-3-sonnet": "0727-360B-API",
                        "claude-3-haiku": "glm-4.5v",
                        "claude-3.5-sonnet": "0727-360B-API"
                    },
                    "default_models": ["glm-4.5v", "0727-360B-API"],
                    "default_params": {
                        "enable_thinking": True,
                        "temperature": 0.7,
                        "top_p": 0.9,
                        "max_tokens": 4000
                    }
                }
            },
            {
                "name": "codegen-api",
                "provider_type": "rest_api",
                "base_url": os.getenv("CODEGEN_BASE_URL", "https://codegen-sh--rest-api.modal.run"),
                "priority": 90,  # High priority as requested
                "enabled": True,
                "auto_configured": True,
                "description": "Codegen API - high priority default endpoint",
                "config": {
                    "api_key": os.getenv("CODEGEN_TOKEN", ""),
                    "model": "codegen-chat",
                    "headers": {
                        "Authorization": f"Bearer {os.getenv('CODEGEN_TOKEN', '')}",
                        "Content-Type": "application/json"
                    },
                    "endpoints": {
                        "chat": "/v1/chat/completions",
                        "models": "/v1/models"
                    },
                    "max_requests_per_minute": 60,
                    "timeout": 30
                }
            },
            {
                "name": "deepseek-web",
                "provider_type": "web_chat", 
                "base_url": "https://chat.deepseek.com",
                "priority": 80,
                "enabled": False,  # Disabled by default, can be enabled by user
                "auto_configured": True,
                "description": "DeepSeek web chat interface - auto-configured template",
                "config": {
                    "login_url": "https://chat.deepseek.com/login",
                    "username": os.getenv("DEEPSEEK_USERNAME", ""),
                    "password": os.getenv("DEEPSEEK_PASSWORD", ""),
                    "chat_input_selector": "textarea[placeholder*='message'], #chat-input",
                    "send_button_selector": "button[type='submit'], .send-button",
                    "response_selector": ".message-content, .ai-response",
                    "new_chat_selector": ".new-chat-button, button:contains('New Chat')",
                    "browser_config": {
                        "headless": True,
                        "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                        "viewport": {"width": 1920, "height": 1080},
                        "timeout": 30000
                    }
                }
            },
            {
                "name": "openai-web",
                "provider_type": "web_chat",
                "base_url": "https://chat.openai.com",
                "priority": 75,
                "enabled": False,  # Disabled by default
                "auto_configured": True,
                "description": "OpenAI ChatGPT web interface - auto-configured template",
                "config": {
                    "login_url": "https://chat.openai.com/auth/login",
                    "username": os.getenv("OPENAI_USERNAME", ""),
                    "password": os.getenv("OPENAI_PASSWORD", ""),
                    "chat_input_selector": "#prompt-textarea, textarea[placeholder*='message']",
                    "send_button_selector": "button[data-testid='send-button'], button:contains('Send')",
                    "response_selector": ".markdown, .message-content",
                    "new_chat_selector": "button:contains('New chat'), .new-chat-button",
                    "browser_config": {
                        "headless": True,
                        "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                        "viewport": {"width": 1920, "height": 1080},
                        "timeout": 30000
                    }
                }
            }
        ]
    
    async def initialize_default_endpoints(self, endpoint_manager) -> Dict[str, bool]:
        """
        Initialize default endpoints in the endpoint manager
        """
        results = {}
        
        for endpoint_config in self.default_endpoints:
            try:
                endpoint_name = endpoint_config["name"]
                
                # Check if endpoint already exists
                existing_adapters = list(endpoint_manager.active_adapters.keys())
                if endpoint_name in existing_adapters:
                    logger.info(f"Default endpoint {endpoint_name} already exists, skipping")
                    results[endpoint_name] = True
                    continue
                
                # Only initialize enabled endpoints
                if not endpoint_config.get("enabled", False):
                    logger.info(f"Default endpoint {endpoint_name} is disabled, skipping")
                    results[endpoint_name] = False
                    continue
                
                # Check if required credentials are available
                if not self._has_required_credentials(endpoint_config):
                    logger.warning(f"Missing credentials for {endpoint_name}, skipping initialization")
                    results[endpoint_name] = False
                    continue
                
                # Add the endpoint using the adapter system
                full_config = {
                    'name': endpoint_name,
                    'provider_type': endpoint_config["provider_type"],
                    'priority': endpoint_config.get("priority", 50),
                    'description': endpoint_config.get("description", ""),
                    **endpoint_config["config"]
                }
                
                success = await endpoint_manager.add_endpoint(full_config)
                
                if success:
                    logger.info(f"Successfully initialized default endpoint: {endpoint_name}")
                    results[endpoint_name] = True
                else:
                    logger.error(f"Failed to initialize default endpoint: {endpoint_name}")
                    results[endpoint_name] = False
                    
            except Exception as e:
                logger.error(f"Error initializing default endpoint {endpoint_config.get('name', 'unknown')}: {e}")
                results[endpoint_config.get('name', 'unknown')] = False
        
        return results
    
    def _has_required_credentials(self, endpoint_config: Dict[str, Any]) -> bool:
        """
        Check if endpoint has required credentials
        """
        provider_type = endpoint_config.get("provider_type")
        config = endpoint_config.get("config", {})
        
        if provider_type == "web_chat":
            # For web chat, we need username and password
            username = config.get("username", "")
            password = config.get("password", "")
            return bool(username and password)
        
        elif provider_type == "rest_api":
            # For REST API, we need API key
            api_key = config.get("api_key", "")
            return bool(api_key)
        
        elif provider_type == "zai_sdk":
            # For Z.ai SDK with auto_auth, no credentials needed
            # It uses automatic guest token authentication
            return True
        
        return True  # For other types, assume no credentials needed
    
    def get_default_endpoint_names(self) -> List[str]:
        """
        Get list of default endpoint names
        """
        return [ep["name"] for ep in self.default_endpoints]
    
    def get_enabled_default_endpoints(self) -> List[Dict[str, Any]]:
        """
        Get only enabled default endpoints
        """
        return [ep for ep in self.default_endpoints if ep.get("enabled", False)]
    
    def update_endpoint_credentials(self, endpoint_name: str, credentials: Dict[str, str]) -> bool:
        """
        Update credentials for a default endpoint
        """
        for endpoint in self.default_endpoints:
            if endpoint["name"] == endpoint_name:
                config = endpoint.get("config", {})
                
                # Update credentials based on provider type
                if endpoint["provider_type"] == "web_chat":
                    if "username" in credentials:
                        config["username"] = credentials["username"]
                    if "password" in credentials:
                        config["password"] = credentials["password"]
                
                elif endpoint["provider_type"] == "rest_api":
                    if "api_key" in credentials:
                        config["api_key"] = credentials["api_key"]
                        # Update headers if needed
                        if "headers" in config:
                            config["headers"]["Authorization"] = f"Bearer {credentials['api_key']}"
                
                return True
        
        return False
    
    def enable_endpoint(self, endpoint_name: str) -> bool:
        """
        Enable a default endpoint
        """
        for endpoint in self.default_endpoints:
            if endpoint["name"] == endpoint_name:
                endpoint["enabled"] = True
                return True
        return False
    
    def disable_endpoint(self, endpoint_name: str) -> bool:
        """
        Disable a default endpoint
        """
        for endpoint in self.default_endpoints:
            if endpoint["name"] == endpoint_name:
                endpoint["enabled"] = False
                return True
        return False
    
    def get_endpoint_config(self, endpoint_name: str) -> Optional[Dict[str, Any]]:
        """
        Get configuration for a specific default endpoint
        """
        for endpoint in self.default_endpoints:
            if endpoint["name"] == endpoint_name:
                return endpoint.copy()
        return None
    
    def create_env_template(self) -> str:
        """
        Create .env template with required variables
        """
        template = """# Universal AI Endpoint Manager Configuration

# Database Configuration
DATABASE_URL=sqlite:///endpoint_manager.db
DB_ECHO=false

# Default Endpoints Configuration

# Z.ai SDK Configuration (Highest Priority - 100)
# No credentials needed - uses automatic guest token authentication
# The Z.ai SDK automatically handles authentication

# Codegen API Configuration (High Priority - 90)
CODEGEN_BASE_URL=https://codegen-sh--rest-api.modal.run
CODEGEN_TOKEN=your_codegen_token_here

# Optional: DeepSeek Configuration (Priority - 80)
DEEPSEEK_USERNAME=your_email@example.com
DEEPSEEK_PASSWORD=your_password_here

# Optional: OpenAI Configuration (Priority - 75)
OPENAI_USERNAME=your_email@example.com
OPENAI_PASSWORD=your_password_here
OPENAI_API_KEY=sk-your_openai_api_key_here

# Server Configuration
HOST=0.0.0.0
PORT=8000
LOG_LEVEL=INFO

# Browser Automation
BROWSER_HEADLESS=true
BROWSER_TIMEOUT=30000

# Performance
MAX_CONCURRENT_REQUESTS=10
DEFAULT_REQUEST_TIMEOUT=30
"""
        return template
