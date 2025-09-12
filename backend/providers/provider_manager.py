"""
Provider Manager
Manages all provider instances, their lifecycle, and operations
"""

from typing import Dict, List, Optional, Any
import asyncio
import logging
from .base_provider import BaseProvider, ProviderStatus, ProviderContext, ProviderResponse
from .provider_factory import ProviderFactory

logger = logging.getLogger(__name__)

class ProviderManager:
    """Manages all provider instances and their operations"""
    
    def __init__(self):
        self.providers: Dict[str, BaseProvider] = {}
        self.contexts: Dict[str, ProviderContext] = {}
        self._lock = asyncio.Lock()
    
    async def add_provider(self, provider: BaseProvider) -> bool:
        """Add a provider to the manager"""
        async with self._lock:
            try:
                self.providers[provider.name] = provider
                logger.info(f"Added provider: {provider.name}")
                return True
            except Exception as e:
                logger.error(f"Failed to add provider {provider.name}: {str(e)}")
                return False
    
    async def remove_provider(self, provider_name: str) -> bool:
        """Remove a provider from the manager"""
        async with self._lock:
            try:
                if provider_name in self.providers:
                    provider = self.providers[provider_name]
                    await provider.cleanup()
                    del self.providers[provider_name]
                    
                    # Also remove context if exists
                    if provider_name in self.contexts:
                        del self.contexts[provider_name]
                    
                    logger.info(f"Removed provider: {provider_name}")
                    return True
                else:
                    logger.warning(f"Provider not found: {provider_name}")
                    return False
            except Exception as e:
                logger.error(f"Failed to remove provider {provider_name}: {str(e)}")
                return False
    
    async def get_provider(self, provider_name: str) -> Optional[BaseProvider]:
        """Get a provider by name"""
        return self.providers.get(provider_name)
    
    async def list_providers(self) -> List[Dict[str, Any]]:
        """List all providers with their information"""
        provider_list = []
        for provider in self.providers.values():
            info = await provider.get_info()
            provider_list.append(info)
        return provider_list
    
    async def set_provider_context(self, provider_name: str, context: ProviderContext) -> bool:
        """Set authentication context for a provider"""
        try:
            if provider_name not in self.providers:
                logger.error(f"Provider not found: {provider_name}")
                return False
            
            provider = self.providers[provider_name]
            
            # Initialize provider with context
            success = await provider.initialize(context)
            if success:
                self.contexts[provider_name] = context
                logger.info(f"Set context for provider: {provider_name}")
                return True
            else:
                logger.error(f"Failed to initialize provider with context: {provider_name}")
                return False
                
        except Exception as e:
            logger.error(f"Failed to set context for {provider_name}: {str(e)}")
            return False
    
    async def get_provider_context(self, provider_name: str) -> Optional[ProviderContext]:
        """Get authentication context for a provider"""
        return self.contexts.get(provider_name)
    
    async def test_provider(self, provider_name: str, test_message: str = "Hello - what is your model name?") -> ProviderResponse:
        """Test a specific provider"""
        provider = await self.get_provider(provider_name)
        if not provider:
            return ProviderResponse(
                content="",
                provider_name=provider_name,
                success=False,
                error="Provider not found"
            )
        
        return await provider.test_connection(test_message)
    
    async def test_all_providers(self, test_message: str = "Hello - what is your model name?") -> Dict[str, ProviderResponse]:
        """Test all active providers"""
        results = {}
        
        # Get only active providers
        active_providers = [
            provider for provider in self.providers.values()
            if provider.status == ProviderStatus.ACTIVE
        ]
        
        if not active_providers:
            return results
        
        # Test all providers concurrently
        tasks = []
        for provider in active_providers:
            task = asyncio.create_task(provider.test_connection(test_message))
            tasks.append((provider.name, task))
        
        # Wait for all tests to complete
        for provider_name, task in tasks:
            try:
                result = await task
                results[provider_name] = result
            except Exception as e:
                results[provider_name] = ProviderResponse(
                    content="",
                    provider_name=provider_name,
                    success=False,
                    error=str(e)
                )
        
        return results
    
    async def send_message(self, provider_name: str, message: str, **kwargs) -> ProviderResponse:
        """Send a message to a specific provider"""
        provider = await self.get_provider(provider_name)
        if not provider:
            return ProviderResponse(
                content="",
                provider_name=provider_name,
                success=False,
                error="Provider not found"
            )
        
        if provider.status != ProviderStatus.ACTIVE:
            return ProviderResponse(
                content="",
                provider_name=provider_name,
                success=False,
                error=f"Provider not active. Status: {provider.status.value}"
            )
        
        return await provider.send_message(message, **kwargs)
    
    async def send_message_parallel(self, provider_names: List[str], message: str, **kwargs) -> Dict[str, ProviderResponse]:
        """Send a message to multiple providers in parallel"""
        if not provider_names:
            return {}
        
        # Filter to only active providers
        active_providers = []
        for name in provider_names:
            provider = await self.get_provider(name)
            if provider and provider.status == ProviderStatus.ACTIVE:
                active_providers.append(provider)
        
        if not active_providers:
            return {name: ProviderResponse(
                content="",
                provider_name=name,
                success=False,
                error="No active providers found"
            ) for name in provider_names}
        
        # Send to all providers concurrently
        tasks = []
        for provider in active_providers:
            task = asyncio.create_task(provider.send_message(message, **kwargs))
            tasks.append((provider.name, task))
        
        # Collect results
        results = {}
        for provider_name, task in tasks:
            try:
                result = await task
                results[provider_name] = result
            except Exception as e:
                results[provider_name] = ProviderResponse(
                    content="",
                    provider_name=provider_name,
                    success=False,
                    error=str(e)
                )
        
        return results
    
    async def health_check_all(self) -> Dict[str, bool]:
        """Perform health check on all providers"""
        results = {}
        
        tasks = []
        for provider in self.providers.values():
            task = asyncio.create_task(provider.health_check())
            tasks.append((provider.name, task))
        
        for provider_name, task in tasks:
            try:
                result = await task
                results[provider_name] = result
            except Exception as e:
                logger.error(f"Health check failed for {provider_name}: {str(e)}")
                results[provider_name] = False
        
        return results
    
    async def get_active_providers(self) -> List[str]:
        """Get list of active provider names"""
        active = []
        for provider in self.providers.values():
            if provider.status == ProviderStatus.ACTIVE:
                active.append(provider.name)
        return active
    
    async def get_provider_stats(self) -> Dict[str, Dict[str, Any]]:
        """Get statistics for all providers"""
        stats = {}
        for provider in self.providers.values():
            info = await provider.get_info()
            stats[provider.name] = {
                "status": info["status"],
                "request_count": info["request_count"],
                "error_count": info["error_count"],
                "last_used_at": info["last_used_at"],
                "last_error": info["last_error"]
            }
        return stats
    
    async def cleanup_all(self):
        """Cleanup all providers"""
        tasks = []
        for provider in self.providers.values():
            task = asyncio.create_task(provider.cleanup())
            tasks.append(task)
        
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)
        
        self.providers.clear()
        self.contexts.clear()
        logger.info("Cleaned up all providers")
