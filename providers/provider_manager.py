"""
Provider Manager - Manages all AI providers
"""

import asyncio
import logging
from typing import Dict, Any, Optional, List

from providers.base_provider import BaseProvider
from providers.zai_provider import ZAIProvider
from providers.k2_provider import K2Provider
from providers.qwen_provider import QwenProvider
from providers.grok_provider import GrokProvider
from providers.chatgpt_provider import ChatGPTProvider
from providers.bing_provider import BingProvider
from providers.codegen_provider import CodegenProvider
from providers.copilot_provider import CopilotProvider
from providers.talkai_provider import TalkAIProvider

logger = logging.getLogger(__name__)

class ProviderManager:
    """Manages all AI providers."""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.providers: Dict[str, BaseProvider] = {}
        self.provider_classes = {
            "zai": ZAIProvider,
            "k2": K2Provider,
            "qwen": QwenProvider,
            "grok": GrokProvider,
            "chatgpt": ChatGPTProvider,
            "bing": BingProvider,
            "codegen": CodegenProvider,
            "copilot": CopilotProvider,
            "talkai": TalkAIProvider
        }
        
    async def initialize_provider(self, provider_name: str) -> bool:
        """Initialize a specific provider."""
        
        try:
            provider_config = self.config.get("providers", {}).get(provider_name)
            if not provider_config:
                logger.error(f"No configuration found for provider: {provider_name}")
                return False
            
            if not provider_config.get("enabled", False):
                logger.info(f"Provider {provider_name} is disabled")
                return False
            
            provider_class = self.provider_classes.get(provider_name)
            if not provider_class:
                logger.error(f"No provider class found for: {provider_name}")
                return False
            
            # Initialize the provider
            provider = provider_class(provider_config)
            await provider.initialize()
            
            self.providers[provider_name] = provider
            logger.info(f"✅ Provider {provider_name} initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize provider {provider_name}: {e}")
            return False
    
    async def initialize_all_providers(self) -> int:
        """Initialize all enabled providers."""
        
        success_count = 0
        provider_configs = self.config.get("providers", {})
        
        for provider_name, provider_config in provider_configs.items():
            if provider_config.get("enabled", False):
                if await self.initialize_provider(provider_name):
                    success_count += 1
        
        logger.info(f"Initialized {success_count}/{len(provider_configs)} providers")
        return success_count
    
    def get_provider(self, provider_name: str) -> Optional[BaseProvider]:
        """Get a specific provider instance."""
        return self.providers.get(provider_name)
    
    def get_provider_names(self) -> List[str]:
        """Get list of all provider names."""
        return list(self.provider_classes.keys())
    
    def get_enabled_providers(self) -> Dict[str, BaseProvider]:
        """Get all enabled and initialized providers."""
        return self.providers.copy()
    
    async def health_check_all(self) -> Dict[str, bool]:
        """Check health of all providers."""
        
        health_status = {}
        
        for provider_name, provider in self.providers.items():
            try:
                is_healthy = await provider.health_check()
                health_status[provider_name] = is_healthy
            except Exception as e:
                logger.error(f"Health check failed for {provider_name}: {e}")
                health_status[provider_name] = False
        
        return health_status
    
    async def get_provider_stats(self) -> Dict[str, Dict[str, Any]]:
        """Get statistics for all providers."""
        
        stats = {}
        
        for provider_name, provider in self.providers.items():
            try:
                provider_stats = await provider.get_stats()
                stats[provider_name] = provider_stats
            except Exception as e:
                logger.error(f"Failed to get stats for {provider_name}: {e}")
                stats[provider_name] = {"error": str(e)}
        
        return stats
    
    async def shutdown_all(self):
        """Shutdown all providers."""
        
        for provider_name, provider in self.providers.items():
            try:
                await provider.shutdown()
                logger.info(f"Shutdown provider: {provider_name}")
            except Exception as e:
                logger.error(f"Failed to shutdown {provider_name}: {e}")
        
        self.providers.clear()
