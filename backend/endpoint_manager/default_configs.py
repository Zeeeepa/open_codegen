"""
Default endpoint configurations for Codegen REST API and Z.AI Web UI.
Provides pre-configured templates that are automatically available in the system.
"""
import uuid
from typing import Dict, Any, List
from datetime import datetime

from backend.database.models import EndpointConfig, ProviderType


class DefaultEndpointConfigs:
    """Manager for default endpoint configurations."""
    
    @staticmethod
    def get_codegen_rest_api_config(org_id: str = None, token: str = None) -> EndpointConfig:
        """
        Get default Codegen REST API endpoint configuration.
        
        Args:
            org_id: Organization ID for Codegen API
            token: Authentication token for Codegen API
            
        Returns:
            EndpointConfig for Codegen REST API
        """
        config_data = {
            "api_base_url": "https://api.codegen.com",
            "auth_type": "bearer_token",
            "bearer_token": token or "[YOUR_CODEGEN_TOKEN]",
            "timeout": 30,
            "max_retries": 3,
            "headers": {
                "Content-Type": "application/json",
                "User-Agent": "open-codegen-proxy/1.0"
            }
        }
        
        # Add org_id to config if provided
        if org_id:
            config_data["org_id"] = org_id
        
        return EndpointConfig(
            id=str(uuid.uuid4()),
            user_id="system",
            name="Codegen REST API",
            model_name="codegen-agent",
            description="Default Codegen REST API endpoint with org_id and token authentication",
            provider_type=ProviderType.REST_API.value,
            provider_name="codegen",
            config_data=config_data,
            status="stopped",
            is_enabled=True,
            priority=1,
            max_concurrent_requests=5,
            timeout_seconds=30,
            retry_attempts=3,
            created_at=datetime.utcnow().isoformat(),
            updated_at=datetime.utcnow().isoformat()
        )
    
    @staticmethod
    def get_zai_webui_config(
        base_url: str = "https://chat.z.ai",
        model: str = "glm-4.5v",
        pool_size: int = 3,
        max_pool_size: int = 10
    ) -> EndpointConfig:
        """
        Get default Z.AI Web UI endpoint configuration.
        
        Args:
            base_url: Base URL for Z.AI service
            model: Default model to use (glm-4.5v or 0727-360B-API)
            pool_size: Initial client pool size
            max_pool_size: Maximum client pool size for autoscaling
            
        Returns:
            EndpointConfig for Z.AI Web UI
        """
        config_data = {
            "provider_type": "zai",
            "base_url": base_url,
            "timeout": 180,
            "auto_auth": True,
            "verbose": False,
            "model": model,
            "pool_size": pool_size,
            "autoscaling": True,
            "max_pool_size": max_pool_size,
            "enable_thinking": True,
            "temperature": 0.7,
            "top_p": 0.9,
            "max_tokens": 2000
        }
        
        return EndpointConfig(
            id=str(uuid.uuid4()),
            user_id="system",
            name="Z.AI Web UI",
            model_name=model,
            description="Default Z.AI Web UI endpoint with automatic authentication and autoscaling",
            provider_type=ProviderType.WEB_CHAT.value,
            provider_name="zai",
            config_data=config_data,
            status="stopped",
            is_enabled=True,
            priority=2,
            max_concurrent_requests=10,
            timeout_seconds=180,
            retry_attempts=3,
            created_at=datetime.utcnow().isoformat(),
            updated_at=datetime.utcnow().isoformat()
        )
    
    @staticmethod
    def get_all_default_configs(
        codegen_org_id: str = None,
        codegen_token: str = None
    ) -> List[EndpointConfig]:
        """
        Get all default endpoint configurations.
        
        Args:
            codegen_org_id: Organization ID for Codegen API
            codegen_token: Authentication token for Codegen API
            
        Returns:
            List of default EndpointConfig objects
        """
        return [
            DefaultEndpointConfigs.get_codegen_rest_api_config(codegen_org_id, codegen_token),
            DefaultEndpointConfigs.get_zai_webui_config()
        ]
    
    @staticmethod
    def get_provider_templates() -> Dict[str, Dict[str, Any]]:
        """
        Get provider configuration templates for the UI.
        
        Returns:
            Dictionary of provider templates with configuration schemas
        """
        return {
            "codegen_rest_api": {
                "name": "Codegen REST API",
                "description": "Codegen's intelligent code generation API",
                "provider_type": ProviderType.REST_API.value,
                "required_fields": ["org_id", "token"],
                "optional_fields": ["timeout", "max_retries"],
                "template": {
                    "api_base_url": "https://api.codegen.com",
                    "auth_type": "bearer_token",
                    "bearer_token": "[YOUR_CODEGEN_TOKEN]",
                    "org_id": "[YOUR_ORG_ID]",
                    "timeout": 30,
                    "max_retries": 3
                },
                "models": ["codegen-agent"],
                "capabilities": ["code_generation", "debugging", "refactoring", "documentation"]
            },
            
            "zai_webui": {
                "name": "Z.AI Web UI",
                "description": "Z.AI's advanced language models via web interface",
                "provider_type": ProviderType.WEB_CHAT.value,
                "required_fields": [],
                "optional_fields": ["base_url", "model", "pool_size", "max_pool_size"],
                "template": {
                    "provider_type": "zai",
                    "base_url": "https://chat.z.ai",
                    "auto_auth": True,
                    "model": "glm-4.5v",
                    "pool_size": 3,
                    "autoscaling": True,
                    "max_pool_size": 10,
                    "enable_thinking": True,
                    "temperature": 0.7,
                    "top_p": 0.9,
                    "max_tokens": 2000
                },
                "models": ["glm-4.5v", "0727-360B-API"],
                "capabilities": ["chat", "reasoning", "visual_understanding", "code_generation"]
            },
            
            "openai_compatible": {
                "name": "OpenAI Compatible API",
                "description": "Any OpenAI-compatible API endpoint",
                "provider_type": ProviderType.REST_API.value,
                "required_fields": ["api_base_url", "api_key"],
                "optional_fields": ["timeout", "max_retries", "headers"],
                "template": {
                    "api_base_url": "https://api.openai.com",
                    "auth_type": "api_key",
                    "api_key": "[YOUR_API_KEY]",
                    "timeout": 30,
                    "max_retries": 3,
                    "headers": {
                        "Content-Type": "application/json"
                    }
                },
                "models": ["gpt-3.5-turbo", "gpt-4", "gpt-4-turbo"],
                "capabilities": ["chat", "completion", "embeddings"]
            },
            
            "anthropic_api": {
                "name": "Anthropic API",
                "description": "Anthropic's Claude models via REST API",
                "provider_type": ProviderType.REST_API.value,
                "required_fields": ["api_key"],
                "optional_fields": ["timeout", "max_retries"],
                "template": {
                    "api_base_url": "https://api.anthropic.com",
                    "auth_type": "api_key",
                    "api_key": "[YOUR_ANTHROPIC_API_KEY]",
                    "timeout": 30,
                    "max_retries": 3,
                    "headers": {
                        "Content-Type": "application/json",
                        "anthropic-version": "2023-06-01"
                    }
                },
                "models": ["claude-3-haiku", "claude-3-sonnet", "claude-3-opus"],
                "capabilities": ["chat", "reasoning", "analysis"]
            },
            
            "google_gemini": {
                "name": "Google Gemini API",
                "description": "Google's Gemini models via REST API",
                "provider_type": ProviderType.REST_API.value,
                "required_fields": ["api_key"],
                "optional_fields": ["timeout", "max_retries"],
                "template": {
                    "api_base_url": "https://generativelanguage.googleapis.com",
                    "auth_type": "api_key",
                    "api_key": "[YOUR_GOOGLE_API_KEY]",
                    "timeout": 30,
                    "max_retries": 3
                },
                "models": ["gemini-pro", "gemini-pro-vision"],
                "capabilities": ["chat", "vision", "reasoning"]
            }
        }
    
    @staticmethod
    def create_endpoint_from_template(
        template_name: str,
        user_id: str,
        name: str,
        config_overrides: Dict[str, Any] = None
    ) -> EndpointConfig:
        """
        Create an endpoint configuration from a template.
        
        Args:
            template_name: Name of the template to use
            user_id: User ID for the endpoint
            name: Custom name for the endpoint
            config_overrides: Configuration values to override
            
        Returns:
            EndpointConfig created from template
            
        Raises:
            ValueError: If template_name is not found
        """
        templates = DefaultEndpointConfigs.get_provider_templates()
        
        if template_name not in templates:
            raise ValueError(f"Template '{template_name}' not found")
        
        template = templates[template_name]
        config_data = template["template"].copy()
        
        # Apply overrides
        if config_overrides:
            config_data.update(config_overrides)
        
        # Determine model name
        model_name = config_data.get("model", template["models"][0] if template["models"] else "default")
        
        return EndpointConfig(
            id=str(uuid.uuid4()),
            user_id=user_id,
            name=name,
            model_name=model_name,
            description=template["description"],
            provider_type=template["provider_type"],
            provider_name=template_name,
            config_data=config_data,
            status="stopped",
            is_enabled=True,
            priority=1,
            max_concurrent_requests=5,
            timeout_seconds=config_data.get("timeout", 30),
            retry_attempts=config_data.get("max_retries", 3),
            created_at=datetime.utcnow().isoformat(),
            updated_at=datetime.utcnow().isoformat()
        )


class RoutingConfigManager:
    """Manager for routing configuration."""
    
    @staticmethod
    def get_default_routing_config() -> Dict[str, Any]:
        """Get default routing configuration."""
        return {
            "default_route": "codegen_api",  # codegen_api or zai_webui
            "zai_webui_enabled": True,
            "load_balancing": "round_robin",  # round_robin, random, least_connections
            "fallback_enabled": True,
            "auto_scaling": {
                "enabled": True,
                "min_instances": 1,
                "max_instances": 10,
                "scale_up_threshold": 0.8,  # CPU/memory threshold
                "scale_down_threshold": 0.3,
                "cooldown_seconds": 300
            },
            "health_check": {
                "enabled": True,
                "interval_seconds": 30,
                "timeout_seconds": 10,
                "failure_threshold": 3
            }
        }
    
    @staticmethod
    def create_routing_rule(
        name: str,
        conditions: Dict[str, Any],
        target_endpoint: str,
        priority: int = 1
    ) -> Dict[str, Any]:
        """
        Create a routing rule.
        
        Args:
            name: Name of the routing rule
            conditions: Conditions for applying this rule
            target_endpoint: Target endpoint ID or type
            priority: Rule priority (lower = higher priority)
            
        Returns:
            Routing rule configuration
        """
        return {
            "name": name,
            "priority": priority,
            "conditions": conditions,
            "target_endpoint": target_endpoint,
            "enabled": True,
            "created_at": datetime.utcnow().isoformat()
        }
    
    @staticmethod
    def get_example_routing_rules() -> List[Dict[str, Any]]:
        """Get example routing rules for different scenarios."""
        return [
            RoutingConfigManager.create_routing_rule(
                name="Route OpenAI to Z.AI",
                conditions={
                    "api_provider": "openai",
                    "model_prefix": "gpt-"
                },
                target_endpoint="zai_webui",
                priority=1
            ),
            RoutingConfigManager.create_routing_rule(
                name="Route Anthropic to Codegen",
                conditions={
                    "api_provider": "anthropic",
                    "model_prefix": "claude-"
                },
                target_endpoint="codegen_api",
                priority=2
            ),
            RoutingConfigManager.create_routing_rule(
                name="High Priority Users to Premium",
                conditions={
                    "user_tier": "premium",
                    "request_size": {"max": 10000}
                },
                target_endpoint="premium_endpoint",
                priority=0
            )
        ]
