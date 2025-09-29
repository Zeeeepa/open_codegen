"""Load Balancer - Selects providers based on strategy"""
import asyncio
import logging
from typing import Dict, Any, List

logger = logging.getLogger(__name__)

class LoadBalancer:
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.strategy = config.get("load_balancing", {}).get("strategy", "priority")
        self.current_index = 0
    
    async def select_provider(self, webchat_request: Dict[str, Any]) -> str:
        """Select a provider based on the configured strategy."""
        
        # Get enabled providers sorted by priority
        providers = self.config.get("providers", {})
        enabled_providers = [
            (name, config) for name, config in providers.items()
            if config.get("enabled", False)
        ]
        
        if not enabled_providers:
            raise Exception("No enabled providers available")
        
        # Sort by priority (lower number = higher priority)
        enabled_providers.sort(key=lambda x: x[1].get("priority", 999))
        
        if self.strategy == "priority":
            # Always use highest priority provider
            return enabled_providers[0][0]
        elif self.strategy == "round_robin":
            # Round robin through providers
            provider_name = enabled_providers[self.current_index % len(enabled_providers)][0]
            self.current_index += 1
            return provider_name
        else:
            # Default to priority
            return enabled_providers[0][0]
