"""
Base handler interface for AI endpoint providers.
Defines the common interface that all provider handlers must implement.
"""
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional

from backend.database.models import EndpointConfig


class BaseProviderHandler(ABC):
    """
    Abstract base class for AI endpoint provider handlers.
    
    All provider handlers (REST API, Web Chat, API Token) must implement
    this interface to ensure consistent behavior across different provider types.
    """
    
    def __init__(self, config: EndpointConfig):
        """
        Initialize the provider handler with endpoint configuration.
        
        Args:
            config: Endpoint configuration containing provider-specific settings
        """
        self.config = config
        self.endpoint_id = config.id
        self.provider_name = config.provider_name
        self.config_data = config.config_data
        self._is_started = False
    
    @abstractmethod
    async def start(self) -> None:
        """
        Start the endpoint and initialize any required resources.
        
        This method should:
        - Initialize connections/sessions
        - Validate configuration
        - Set up any required authentication
        - Mark the handler as started
        
        Raises:
            Exception: If the endpoint fails to start
        """
        pass
    
    @abstractmethod
    async def stop(self) -> None:
        """
        Stop the endpoint and cleanup resources.
        
        This method should:
        - Close connections/sessions
        - Cleanup temporary resources
        - Mark the handler as stopped
        """
        pass
    
    @abstractmethod
    async def send_message(self, message: str) -> str:
        """
        Send a message to the AI endpoint and return the response.
        
        Args:
            message: The message to send to the AI endpoint
            
        Returns:
            The response from the AI endpoint
            
        Raises:
            Exception: If the message fails to send or receive response
        """
        pass
    
    @abstractmethod
    async def health_check(self) -> bool:
        """
        Perform a health check on the endpoint.
        
        Returns:
            True if the endpoint is healthy and responsive, False otherwise
        """
        pass
    
    @property
    def is_started(self) -> bool:
        """Check if the handler is currently started."""
        return self._is_started
    
    def get_config_value(self, key: str, default: Any = None) -> Any:
        """
        Get a configuration value from the provider-specific config data.
        
        Args:
            key: Configuration key to retrieve
            default: Default value if key is not found
            
        Returns:
            Configuration value or default
        """
        return self.config_data.get(key, default)
    
    def validate_required_config(self, required_keys: list) -> None:
        """
        Validate that all required configuration keys are present.
        
        Args:
            required_keys: List of required configuration keys
            
        Raises:
            ValueError: If any required keys are missing
        """
        missing_keys = []
        for key in required_keys:
            if key not in self.config_data or self.config_data[key] is None:
                missing_keys.append(key)
        
        if missing_keys:
            raise ValueError(
                f"Missing required configuration keys: {', '.join(missing_keys)}"
            )
