"""
Provider Factory
Creates provider instances based on configuration
"""

from typing import Dict, Any, Optional, Type
import logging
from .base_provider import BaseProvider, ProviderType

logger = logging.getLogger(__name__)

class ProviderFactory:
    """Factory for creating provider instances"""
    
    _provider_classes: Dict[str, Type[BaseProvider]] = {}
    
    @classmethod
    def register_provider(cls, provider_name: str, provider_class: Type[BaseProvider]):
        """Register a provider class with the factory"""
        cls._provider_classes[provider_name] = provider_class
        logger.info(f"Registered provider: {provider_name}")
    
    @classmethod
    def create_provider(cls, provider_name: str, config: Dict[str, Any]) -> Optional[BaseProvider]:
        """
        Create a provider instance
        
        Args:
            provider_name: Name of the provider to create
            config: Configuration dictionary for the provider
            
        Returns:
            Provider instance or None if creation failed
        """
        try:
            if provider_name not in cls._provider_classes:
                logger.error(f"Unknown provider: {provider_name}")
                return None
            
            provider_class = cls._provider_classes[provider_name]
            provider_type = config.get('type', 'api_based')
            
            # Convert string to enum
            if isinstance(provider_type, str):
                provider_type = ProviderType(provider_type)
            
            instance = provider_class(
                name=provider_name,
                provider_type=provider_type,
                config=config
            )
            
            logger.info(f"Created provider instance: {provider_name}")
            return instance
            
        except Exception as e:
            logger.error(f"Failed to create provider {provider_name}: {str(e)}")
            return None
    
    @classmethod
    def get_available_providers(cls) -> Dict[str, str]:
        """Get list of available provider types"""
        return {name: cls_type.__name__ for name, cls_type in cls._provider_classes.items()}
    
    @classmethod
    def create_from_config(cls, providers_config: Dict[str, Dict[str, Any]]) -> Dict[str, BaseProvider]:
        """
        Create multiple providers from configuration dictionary
        
        Args:
            providers_config: Dictionary with provider configs
            
        Returns:
            Dictionary of created provider instances
        """
        providers = {}
        
        for provider_name, config in providers_config.items():
            provider = cls.create_provider(provider_name, config)
            if provider:
                providers[provider_name] = provider
            else:
                logger.warning(f"Failed to create provider: {provider_name}")
        
        return providers

# Auto-registration decorator
def register_provider(provider_name: str):
    """Decorator to automatically register provider classes"""
    def decorator(provider_class: Type[BaseProvider]):
        ProviderFactory.register_provider(provider_name, provider_class)
        return provider_class
    return decorator
