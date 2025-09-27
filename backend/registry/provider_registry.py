"""
Provider Registry
Central registry for managing AI providers
"""

import asyncio
import logging
from typing import Dict, List, Optional, Set, Any
from datetime import datetime, timedelta
import json

from .provider_metadata import (
    ProviderMetadata, ProviderType, ProviderStatus, ProviderCapability,
    ModelInfo, ProviderConfiguration, RateLimitInfo
)

logger = logging.getLogger(__name__)


class ProviderRegistry:
    """
    Central registry for managing AI providers
    
    Responsibilities:
    - Register and manage provider metadata
    - Track provider health and status
    - Provide provider discovery and selection
    - Handle provider configuration updates
    - Manage provider priorities and weights
    """
    
    def __init__(self):
        self._providers: Dict[str, ProviderMetadata] = {}
        self._providers_by_type: Dict[ProviderType, List[str]] = {}
        self._providers_by_capability: Dict[ProviderCapability, List[str]] = {}
        self._health_check_interval = 60  # seconds
        self._health_check_task: Optional[asyncio.Task] = None
        self._running = False
        
        # Initialize provider type mapping
        for provider_type in ProviderType:
            self._providers_by_type[provider_type] = []
        
        # Initialize capability mapping
        for capability in ProviderCapability:
            self._providers_by_capability[capability] = []
    
    async def start(self):
        """Start the provider registry"""
        self._running = True
        self._health_check_task = asyncio.create_task(self._health_check_loop())
        logger.info("Provider registry started")
    
    async def stop(self):
        """Stop the provider registry"""
        self._running = False
        if self._health_check_task:
            self._health_check_task.cancel()
            try:
                await self._health_check_task
            except asyncio.CancelledError:
                pass
        logger.info("Provider registry stopped")
    
    def register_provider(self, provider: ProviderMetadata) -> bool:
        """
        Register a new provider
        
        Args:
            provider: Provider metadata
            
        Returns:
            True if registered successfully, False if already exists
        """
        if provider.provider_id in self._providers:
            logger.warning(f"Provider {provider.provider_id} already registered")
            return False
        
        # Add to main registry
        self._providers[provider.provider_id] = provider
        
        # Add to type mapping
        if provider.provider_id not in self._providers_by_type[provider.provider_type]:
            self._providers_by_type[provider.provider_type].append(provider.provider_id)
        
        # Add to capability mapping
        for capability in provider.capabilities:
            if provider.provider_id not in self._providers_by_capability[capability]:
                self._providers_by_capability[capability].append(provider.provider_id)
        
        logger.info(f"Registered provider: {provider.provider_id} ({provider.provider_type.value})")
        return True
    
    def unregister_provider(self, provider_id: str) -> bool:
        """
        Unregister a provider
        
        Args:
            provider_id: Provider ID to unregister
            
        Returns:
            True if unregistered successfully, False if not found
        """
        if provider_id not in self._providers:
            return False
        
        provider = self._providers[provider_id]
        
        # Remove from main registry
        del self._providers[provider_id]
        
        # Remove from type mapping
        if provider_id in self._providers_by_type[provider.provider_type]:
            self._providers_by_type[provider.provider_type].remove(provider_id)
        
        # Remove from capability mapping
        for capability in provider.capabilities:
            if provider_id in self._providers_by_capability[capability]:
                self._providers_by_capability[capability].remove(provider_id)
        
        logger.info(f"Unregistered provider: {provider_id}")
        return True
    
    def get_provider(self, provider_id: str) -> Optional[ProviderMetadata]:
        """Get provider by ID"""
        return self._providers.get(provider_id)
    
    def get_all_providers(self) -> List[ProviderMetadata]:
        """Get all registered providers"""
        return list(self._providers.values())
    
    def get_providers_by_type(self, provider_type: ProviderType) -> List[ProviderMetadata]:
        """Get all providers of a specific type"""
        provider_ids = self._providers_by_type.get(provider_type, [])
        return [self._providers[pid] for pid in provider_ids if pid in self._providers]
    
    def get_providers_by_capability(self, capability: ProviderCapability) -> List[ProviderMetadata]:
        """Get all providers that support a specific capability"""
        provider_ids = self._providers_by_capability.get(capability, [])
        return [self._providers[pid] for pid in provider_ids if pid in self._providers]
    
    def get_available_providers(self) -> List[ProviderMetadata]:
        """Get all available (enabled and healthy) providers"""
        return [provider for provider in self._providers.values() if provider.is_available()]
    
    def get_available_providers_by_capability(self, capability: ProviderCapability) -> List[ProviderMetadata]:
        """Get available providers that support a specific capability"""
        return [
            provider for provider in self.get_providers_by_capability(capability)
            if provider.is_available()
        ]
    
    def get_providers_by_priority(self, capability: Optional[ProviderCapability] = None) -> List[ProviderMetadata]:
        """
        Get providers sorted by priority (lower number = higher priority)
        
        Args:
            capability: Optional capability filter
            
        Returns:
            List of providers sorted by priority
        """
        if capability:
            providers = self.get_available_providers_by_capability(capability)
        else:
            providers = self.get_available_providers()
        
        return sorted(providers, key=lambda p: (p.priority, p.provider_id))
    
    def update_provider_status(self, provider_id: str, status: ProviderStatus) -> bool:
        """Update provider status"""
        if provider_id not in self._providers:
            return False
        
        self._providers[provider_id].status = status
        self._providers[provider_id].updated_at = datetime.utcnow()
        
        logger.info(f"Updated provider {provider_id} status to {status.value}")
        return True
    
    def enable_provider(self, provider_id: str) -> bool:
        """Enable a provider"""
        if provider_id not in self._providers:
            return False
        
        self._providers[provider_id].enabled = True
        self._providers[provider_id].updated_at = datetime.utcnow()
        
        logger.info(f"Enabled provider: {provider_id}")
        return True
    
    def disable_provider(self, provider_id: str) -> bool:
        """Disable a provider"""
        if provider_id not in self._providers:
            return False
        
        self._providers[provider_id].enabled = False
        self._providers[provider_id].updated_at = datetime.utcnow()
        
        logger.info(f"Disabled provider: {provider_id}")
        return True
    
    def update_provider_priority(self, provider_id: str, priority: int) -> bool:
        """Update provider priority"""
        if provider_id not in self._providers:
            return False
        
        old_priority = self._providers[provider_id].priority
        self._providers[provider_id].priority = priority
        self._providers[provider_id].updated_at = datetime.utcnow()
        
        logger.info(f"Updated provider {provider_id} priority from {old_priority} to {priority}")
        return True
    
    def update_provider_weight(self, provider_id: str, weight: float) -> bool:
        """Update provider weight for load balancing"""
        if provider_id not in self._providers:
            return False
        
        old_weight = self._providers[provider_id].weight
        self._providers[provider_id].weight = weight
        self._providers[provider_id].updated_at = datetime.utcnow()
        
        logger.info(f"Updated provider {provider_id} weight from {old_weight} to {weight}")
        return True
    
    def update_provider_configuration(self, provider_id: str, configuration: ProviderConfiguration) -> bool:
        """Update provider configuration"""
        if provider_id not in self._providers:
            return False
        
        self._providers[provider_id].configuration = configuration
        self._providers[provider_id].updated_at = datetime.utcnow()
        
        logger.info(f"Updated configuration for provider: {provider_id}")
        return True
    
    def update_provider_health(self, provider_id: str, response_time: float, 
                             success: bool, error: Optional[str] = None) -> bool:
        """Update provider health metrics"""
        if provider_id not in self._providers:
            return False
        
        self._providers[provider_id].update_health_metrics(response_time, success, error)
        
        # Auto-disable provider if too many consecutive failures
        if (self._providers[provider_id].health_metrics and 
            self._providers[provider_id].health_metrics.consecutive_failures >= 10):
            self._providers[provider_id].status = ProviderStatus.ERROR
            logger.warning(f"Provider {provider_id} disabled due to consecutive failures")
        
        return True
    
    def update_provider_usage(self, provider_id: str, tokens_used: int = 0, 
                            cost: float = 0.0, response_time: float = 0.0) -> bool:
        """Update provider usage metrics"""
        if provider_id not in self._providers:
            return False
        
        self._providers[provider_id].update_usage_metrics(tokens_used, cost, response_time)
        return True
    
    def get_provider_statistics(self) -> Dict[str, Any]:
        """Get overall provider statistics"""
        total_providers = len(self._providers)
        active_providers = len([p for p in self._providers.values() if p.status == ProviderStatus.ACTIVE])
        enabled_providers = len([p for p in self._providers.values() if p.enabled])
        healthy_providers = len([p for p in self._providers.values() if p.is_healthy()])
        available_providers = len([p for p in self._providers.values() if p.is_available()])
        
        # Provider type breakdown
        type_breakdown = {}
        for provider_type in ProviderType:
            type_breakdown[provider_type.value] = len(self._providers_by_type[provider_type])
        
        # Capability breakdown
        capability_breakdown = {}
        for capability in ProviderCapability:
            available_count = len(self.get_available_providers_by_capability(capability))
            capability_breakdown[capability.value] = available_count
        
        return {
            "total_providers": total_providers,
            "active_providers": active_providers,
            "enabled_providers": enabled_providers,
            "healthy_providers": healthy_providers,
            "available_providers": available_providers,
            "provider_types": type_breakdown,
            "capabilities": capability_breakdown,
            "last_updated": datetime.utcnow().isoformat()
        }
    
    def export_configuration(self) -> Dict[str, Any]:
        """Export provider configuration for backup/restore"""
        return {
            "providers": [provider.to_dict() for provider in self._providers.values()],
            "exported_at": datetime.utcnow().isoformat()
        }
    
    def import_configuration(self, config: Dict[str, Any]) -> int:
        """
        Import provider configuration
        
        Returns:
            Number of providers imported
        """
        imported_count = 0
        
        for provider_data in config.get("providers", []):
            try:
                # Reconstruct provider metadata from dict
                provider = self._provider_from_dict(provider_data)
                if self.register_provider(provider):
                    imported_count += 1
            except Exception as e:
                logger.error(f"Failed to import provider {provider_data.get('provider_id', 'unknown')}: {e}")
        
        logger.info(f"Imported {imported_count} providers")
        return imported_count
    
    def _provider_from_dict(self, data: Dict[str, Any]) -> ProviderMetadata:
        """Reconstruct ProviderMetadata from dictionary"""
        # This is a simplified version - in production, you'd want more robust deserialization
        provider = ProviderMetadata(
            provider_id=data["provider_id"],
            provider_type=ProviderType(data["provider_type"]),
            name=data["name"],
            display_name=data["display_name"],
            description=data["description"],
            version=data.get("version", "1.0.0"),
            status=ProviderStatus(data["status"]),
            enabled=data["enabled"],
            priority=data["priority"],
            weight=data["weight"],
            capabilities=[ProviderCapability(cap) for cap in data["capabilities"]],
            default_model=data.get("default_model"),
            created_at=datetime.fromisoformat(data["created_at"]),
            updated_at=datetime.fromisoformat(data["updated_at"]),
            tags=data.get("tags", [])
        )
        
        # Reconstruct models
        for model_data in data.get("supported_models", []):
            model = ModelInfo(
                name=model_data["name"],
                display_name=model_data["display_name"],
                description=model_data.get("description", ""),
                context_length=model_data.get("context_length", 4096),
                max_tokens=model_data.get("max_tokens", 2048),
                supports_streaming=model_data.get("supports_streaming", True),
                supports_function_calling=model_data.get("supports_function_calling", False),
                supports_vision=model_data.get("supports_vision", False),
                cost_per_1k_tokens=model_data.get("cost_per_1k_tokens", 0.0),
                capabilities=[ProviderCapability(cap) for cap in model_data.get("capabilities", [])]
            )
            provider.supported_models.append(model)
        
        return provider
    
    async def _health_check_loop(self):
        """Background task for health checking providers"""
        while self._running:
            try:
                await self._perform_health_checks()
                await asyncio.sleep(self._health_check_interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in health check loop: {e}")
                await asyncio.sleep(5)  # Short delay before retrying
    
    async def _perform_health_checks(self):
        """Perform health checks on all active providers"""
        active_providers = [
            provider for provider in self._providers.values()
            if provider.status == ProviderStatus.ACTIVE and provider.enabled
        ]
        
        if not active_providers:
            return
        
        logger.debug(f"Performing health checks on {len(active_providers)} providers")
        
        # TODO: Implement actual health check logic
        # For now, just update the last check time
        for provider in active_providers:
            if provider.health_metrics:
                provider.health_metrics.last_check = datetime.utcnow()


# Global registry instance
_provider_registry: Optional[ProviderRegistry] = None


def get_provider_registry() -> ProviderRegistry:
    """Get the global provider registry instance"""
    global _provider_registry
    if _provider_registry is None:
        _provider_registry = ProviderRegistry()
    return _provider_registry
