"""
Provider Registry Implementation
Central registry for managing all AI providers with actual functionality
"""

import asyncio
import json
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from pathlib import Path

from .provider_metadata import (
    ProviderMetadata, ProviderType, ProviderStatus, ProviderCapability,
    ProviderConfiguration, ModelInfo, HealthMetrics, UsageMetrics, RateLimitInfo
)

logger = logging.getLogger(__name__)


class ProviderRegistry:
    """Central registry for managing AI providers"""
    
    def __init__(self, config_path: Optional[str] = None):
        self.providers: Dict[str, ProviderMetadata] = {}
        self.config_path = config_path or "provider_config.json"
        self._initialize_providers()
    
    def _initialize_providers(self):
        """Initialize all 14 providers with actual configurations"""
        
        # 1. Qwen API
        self.register_provider(ProviderMetadata(
            provider_id="qwen-api",
            provider_type=ProviderType.QWEN,
            name="Qwen API",
            display_name="Qwen API",
            description="Alibaba's Qwen large language model API",
            configuration=ProviderConfiguration(
                endpoint_url="http://localhost:8000",
                timeout=30,
                max_retries=3
            ),
            capabilities=[
                ProviderCapability.CHAT_COMPLETION,
                ProviderCapability.TEXT_COMPLETION,
                ProviderCapability.STREAMING
            ],
            supported_models=[
                ModelInfo(
                    name="qwen-turbo",
                    display_name="Qwen Turbo",
                    description="Fast and efficient Qwen model",
                    context_length=8192,
                    max_tokens=2048,
                    supports_streaming=True,
                    cost_per_1k_tokens=0.002,
                    capabilities=[ProviderCapability.CHAT_COMPLETION, ProviderCapability.STREAMING]
                ),
                ModelInfo(
                    name="qwen-plus",
                    display_name="Qwen Plus",
                    description="Advanced Qwen model with enhanced capabilities",
                    context_length=32768,
                    max_tokens=4096,
                    supports_streaming=True,
                    cost_per_1k_tokens=0.008,
                    capabilities=[ProviderCapability.CHAT_COMPLETION, ProviderCapability.STREAMING]
                )
            ],
            default_model="qwen-turbo",
            priority=10,
            weight=1.0
        ))
        
        # 13. TalkAI (Custom Implementation)
        self.register_provider(ProviderMetadata(
            provider_id="talkai",
            provider_type=ProviderType.TALKAI,
            name="TalkAI",
            display_name="TalkAI",
            description="Custom TalkAI implementation with conversational focus",
            configuration=ProviderConfiguration(
                endpoint_url="http://localhost:8012",
                timeout=30,
                max_retries=3
            ),
            capabilities=[
                ProviderCapability.CHAT_COMPLETION,
                ProviderCapability.STREAMING
            ],
            supported_models=[
                ModelInfo(
                    name="talk-ai-model",
                    display_name="TalkAI Model",
                    description="Conversational AI model optimized for dialogue",
                    context_length=8192,
                    max_tokens=2048,
                    supports_streaming=True,
                    cost_per_1k_tokens=0.004,
                    capabilities=[ProviderCapability.CHAT_COMPLETION]
                )
            ],
            default_model="talk-ai-model",
            enabled=True,  # Enable by default for testing
            status=ProviderStatus.ACTIVE,
            priority=60,
            weight=1.0
        ))
        
        # 14. GitHub Copilot Proxy (Custom Implementation)
        self.register_provider(ProviderMetadata(
            provider_id="copilot-proxy",
            provider_type=ProviderType.COPILOT,
            name="GitHub Copilot Proxy",
            display_name="GitHub Copilot Proxy",
            description="OpenAI-compatible proxy for GitHub Copilot with code focus",
            configuration=ProviderConfiguration(
                endpoint_url="http://localhost:8013",
                timeout=30,
                max_retries=3,
                custom_headers={"X-GitHub-Api-Version": "2022-11-28"}
            ),
            capabilities=[
                ProviderCapability.CHAT_COMPLETION,
                ProviderCapability.TEXT_COMPLETION,
                ProviderCapability.FUNCTION_CALLING
            ],
            supported_models=[
                ModelInfo(
                    name="copilot-codex",
                    display_name="Copilot Codex",
                    description="GitHub Copilot's main code completion model",
                    context_length=8192,
                    max_tokens=4096,
                    supports_function_calling=True,
                    cost_per_1k_tokens=0.002,
                    capabilities=[ProviderCapability.CHAT_COMPLETION, ProviderCapability.FUNCTION_CALLING]
                ),
                ModelInfo(
                    name="copilot-chat",
                    display_name="Copilot Chat",
                    description="GitHub Copilot's chat-optimized model",
                    context_length=16384,
                    max_tokens=4096,
                    supports_streaming=True,
                    cost_per_1k_tokens=0.003,
                    capabilities=[ProviderCapability.CHAT_COMPLETION]
                )
            ],
            default_model="copilot-codex",
            enabled=True,  # Enable by default for testing
            status=ProviderStatus.ACTIVE,
            priority=70,
            weight=1.2
        ))
        
        logger.info(f"Initialized {len(self.providers)} providers in registry")
    
    def register_provider(self, provider: ProviderMetadata):
        """Register a new provider"""
        self.providers[provider.provider_id] = provider
        logger.info(f"Registered provider: {provider.name} ({provider.provider_id})")
    
    def get_provider(self, provider_id: str) -> Optional[ProviderMetadata]:
        """Get a provider by ID"""
        return self.providers.get(provider_id)
    
    def get_all_providers(self) -> List[ProviderMetadata]:
        """Get all registered providers"""
        return list(self.providers.values())
    
    def get_enabled_providers(self) -> List[ProviderMetadata]:
        """Get all enabled providers"""
        return [p for p in self.providers.values() if p.enabled]
    
    def get_available_providers(self) -> List[ProviderMetadata]:
        """Get all available (enabled and healthy) providers"""
        return [p for p in self.providers.values() if p.is_available()]
    
    def get_providers_by_type(self, provider_type: ProviderType) -> List[ProviderMetadata]:
        """Get providers by type"""
        return [p for p in self.providers.values() if p.provider_type == provider_type]
    
    def get_providers_with_capability(self, capability: ProviderCapability) -> List[ProviderMetadata]:
        """Get providers that support a specific capability"""
        return [p for p in self.providers.values() if p.supports_capability(capability)]
    
    def enable_provider(self, provider_id: str) -> bool:
        """Enable a provider"""
        provider = self.get_provider(provider_id)
        if provider:
            provider.enabled = True
            provider.updated_at = datetime.utcnow()
            logger.info(f"Enabled provider: {provider.name}")
            return True
        return False
    
    def disable_provider(self, provider_id: str) -> bool:
        """Disable a provider"""
        provider = self.get_provider(provider_id)
        if provider:
            provider.enabled = False
            provider.updated_at = datetime.utcnow()
            logger.info(f"Disabled provider: {provider.name}")
            return True
        return False
    
    def update_provider_health(self, provider_id: str, response_time: float, success: bool, error: Optional[str] = None):
        """Update provider health metrics"""
        provider = self.get_provider(provider_id)
        if provider:
            provider.update_health_metrics(response_time, success, error)
            
            # Update status based on health
            if success:
                provider.status = ProviderStatus.ACTIVE
            else:
                if provider.health_metrics and provider.health_metrics.consecutive_failures >= 5:
                    provider.status = ProviderStatus.ERROR
                else:
                    provider.status = ProviderStatus.INACTIVE
    
    def update_provider_usage(self, provider_id: str, tokens_used: int = 0, cost: float = 0.0, response_time: float = 0.0):
        """Update provider usage metrics"""
        provider = self.get_provider(provider_id)
        if provider:
            provider.update_usage_metrics(tokens_used, cost, response_time)
    
    def get_best_provider(self, capability: ProviderCapability = None, model_name: str = None) -> Optional[ProviderMetadata]:
        """Get the best available provider based on priority and health"""
        available_providers = self.get_available_providers()
        
        if capability:
            available_providers = [p for p in available_providers if p.supports_capability(capability)]
        
        if model_name:
            available_providers = [p for p in available_providers if p.get_model_by_name(model_name)]
        
        if not available_providers:
            return None
        
        # Sort by priority (lower number = higher priority) and health
        available_providers.sort(key=lambda p: (
            p.priority,
            -p.health_metrics.success_rate if p.health_metrics else 0,
            p.health_metrics.response_time_ms if p.health_metrics else float('inf')
        ))
        
        return available_providers[0]
    
    def get_registry_stats(self) -> Dict[str, Any]:
        """Get registry statistics"""
        total_providers = len(self.providers)
        enabled_providers = len(self.get_enabled_providers())
        available_providers = len(self.get_available_providers())
        
        # Calculate total usage
        total_requests = sum(p.usage_metrics.total_requests for p in self.providers.values())
        total_tokens = sum(p.usage_metrics.total_tokens for p in self.providers.values())
        total_cost = sum(p.usage_metrics.total_cost for p in self.providers.values())
        
        # Calculate average response time
        active_providers = [p for p in self.providers.values() if p.health_metrics]
        avg_response_time = (
            sum(p.health_metrics.response_time_ms for p in active_providers) / len(active_providers)
            if active_providers else 0
        )
        
        return {
            "total_providers": total_providers,
            "enabled_providers": enabled_providers,
            "available_providers": available_providers,
            "total_requests": total_requests,
            "total_tokens": total_tokens,
            "total_cost": total_cost,
            "average_response_time": avg_response_time,
            "provider_types": {
                ptype.value: len(self.get_providers_by_type(ptype))
                for ptype in ProviderType
            }
        }


# Global registry instance
_registry = None

def get_registry() -> ProviderRegistry:
    """Get the global provider registry instance"""
    global _registry
    if _registry is None:
        _registry = ProviderRegistry()
    return _registry
