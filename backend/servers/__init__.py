"""
Server factory for creating different endpoint types
"""

from typing import Dict, Any, Optional
import logging

from .base_endpoint import BaseEndpoint
from .web_chat_endpoint import WebChatEndpoint
from .rest_api_endpoint import RestApiEndpoint

logger = logging.getLogger(__name__)

class EndpointFactory:
    """Factory for creating endpoint instances"""
    
    @staticmethod
    def create_endpoint(name: str, config: Dict[str, Any], priority: int = 50) -> Optional[BaseEndpoint]:
        """Create an endpoint instance based on configuration"""
        try:
            endpoint_type = config.get('provider_type', config.get('type', 'rest_api'))
            
            if endpoint_type == 'web_chat':
                return WebChatEndpoint(name, config, priority)
            elif endpoint_type == 'rest_api':
                return RestApiEndpoint(name, config, priority)
            elif endpoint_type == 'api_token':
                # API token is essentially a REST API endpoint
                return RestApiEndpoint(name, config, priority)
            else:
                logger.error(f"Unknown endpoint type: {endpoint_type}")
                return None
                
        except Exception as e:
            logger.error(f"Failed to create endpoint {name}: {e}")
            return None
    
    @staticmethod
    def get_supported_types() -> list:
        """Get list of supported endpoint types"""
        return ['web_chat', 'rest_api', 'api_token']
    
    @staticmethod
    def validate_config(config: Dict[str, Any]) -> tuple[bool, str]:
        """Validate endpoint configuration"""
        try:
            # Check required fields
            if 'name' not in config:
                return False, "Missing required field: name"
            
            if 'provider_type' not in config and 'type' not in config:
                return False, "Missing required field: provider_type or type"
            
            endpoint_type = config.get('provider_type', config.get('type'))
            
            if endpoint_type not in EndpointFactory.get_supported_types():
                return False, f"Unsupported endpoint type: {endpoint_type}"
            
            # Type-specific validation
            if endpoint_type == 'web_chat':
                if 'base_url' not in config and 'login_url' not in config:
                    return False, "Web chat endpoints require base_url or login_url"
            
            elif endpoint_type in ['rest_api', 'api_token']:
                if 'base_url' not in config:
                    return False, "REST API endpoints require base_url"
            
            return True, "Configuration is valid"
            
        except Exception as e:
            return False, f"Configuration validation error: {str(e)}"

# Export main classes
__all__ = [
    'BaseEndpoint',
    'WebChatEndpoint', 
    'RestApiEndpoint',
    'EndpointFactory'
]
