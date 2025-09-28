"""
Provider Metadata Models
Defines metadata structures for AI providers
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
from enum import Enum
from datetime import datetime


class ProviderType(Enum):
    """Types of AI providers"""
    QWEN = "qwen"
    K2THINK = "k2think"
    GROK = "grok"
    ZAI = "zai"
    CODEGEN = "codegen"
    TALKAI = "talkai"
    COPILOT = "copilot"


class ProviderStatus(Enum):
    """Provider status states"""
    ACTIVE = "active"
    INACTIVE = "inactive"
    DISABLED = "disabled"
    ERROR = "error"
    MAINTENANCE = "maintenance"


class ProviderCapability(Enum):
    """Provider capabilities"""
    CHAT_COMPLETION = "chat_completion"
    TEXT_COMPLETION = "text_completion"
    EMBEDDINGS = "embeddings"
    IMAGE_GENERATION = "image_generation"
    IMAGE_EDITING = "image_editing"
    AUDIO_TRANSCRIPTION = "audio_transcription"
    AUDIO_TRANSLATION = "audio_translation"
    VISION = "vision"
    FUNCTION_CALLING = "function_calling"
    STREAMING = "streaming"
    WEB_SEARCH = "web_search"
    THINKING_MODE = "thinking_mode"


@dataclass
class ModelInfo:
    """Information about a specific model"""
    name: str
    display_name: str
    description: str = ""
    context_length: int = 4096
    max_tokens: int = 2048
    supports_streaming: bool = True
    supports_function_calling: bool = False
    supports_vision: bool = False
    cost_per_1k_tokens: float = 0.0
    capabilities: List[ProviderCapability] = field(default_factory=list)


@dataclass
class HealthMetrics:
    """Health metrics for a provider"""
    last_check: datetime
    response_time_ms: float
    success_rate: float
    error_count: int
    consecutive_failures: int
    uptime_percentage: float
    last_error: Optional[str] = None


@dataclass
class UsageMetrics:
    """Usage metrics for a provider"""
    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    total_tokens: int = 0
    total_cost: float = 0.0
    average_response_time: float = 0.0
    requests_per_minute: float = 0.0
    last_request_time: Optional[datetime] = None


@dataclass
class RateLimitInfo:
    """Rate limiting information"""
    requests_per_minute: int = 60
    requests_per_hour: int = 3600
    requests_per_day: int = 86400
    tokens_per_minute: int = 90000
    concurrent_requests: int = 10
    burst_limit: int = 100


@dataclass
class ProviderConfiguration:
    """Provider-specific configuration"""
    endpoint_url: str
    api_key: Optional[str] = None
    timeout: int = 30
    max_retries: int = 3
    retry_delay: float = 1.0
    custom_headers: Dict[str, str] = field(default_factory=dict)
    custom_params: Dict[str, Any] = field(default_factory=dict)
    
    # Provider-specific settings
    use_proxy: bool = False
    proxy_url: Optional[str] = None
    verify_ssl: bool = True
    connection_pool_size: int = 10


@dataclass
class ProviderMetadata:
    """Complete metadata for an AI provider"""
    
    # Basic information
    provider_id: str
    provider_type: ProviderType
    name: str
    display_name: str
    description: str
    version: str = "1.0.0"
    
    # Status and configuration
    status: ProviderStatus = ProviderStatus.INACTIVE
    enabled: bool = False
    priority: int = 100  # Lower number = higher priority
    weight: float = 1.0  # For load balancing
    
    # Capabilities and models
    capabilities: List[ProviderCapability] = field(default_factory=list)
    supported_models: List[ModelInfo] = field(default_factory=list)
    default_model: Optional[str] = None
    
    # Configuration
    configuration: Optional[ProviderConfiguration] = None
    rate_limits: RateLimitInfo = field(default_factory=RateLimitInfo)
    
    # Metrics
    health_metrics: Optional[HealthMetrics] = None
    usage_metrics: UsageMetrics = field(default_factory=UsageMetrics)
    
    # Metadata
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    tags: List[str] = field(default_factory=list)
    
    def is_healthy(self) -> bool:
        """Check if provider is healthy"""
        if not self.health_metrics:
            return False
        
        # Consider healthy if success rate > 90% and consecutive failures < 5
        return (
            self.health_metrics.success_rate > 90.0 and
            self.health_metrics.consecutive_failures < 5 and
            self.status == ProviderStatus.ACTIVE
        )
    
    def is_available(self) -> bool:
        """Check if provider is available for requests"""
        return (
            self.enabled and
            self.status == ProviderStatus.ACTIVE and
            self.is_healthy()
        )
    
    def supports_capability(self, capability: ProviderCapability) -> bool:
        """Check if provider supports a specific capability"""
        return capability in self.capabilities
    
    def get_model_by_name(self, model_name: str) -> Optional[ModelInfo]:
        """Get model information by name"""
        for model in self.supported_models:
            if model.name == model_name or model.display_name == model_name:
                return model
        return None
    
    def get_models_with_capability(self, capability: ProviderCapability) -> List[ModelInfo]:
        """Get all models that support a specific capability"""
        return [
            model for model in self.supported_models
            if capability in model.capabilities
        ]
    
    def update_health_metrics(self, response_time: float, success: bool, error: Optional[str] = None):
        """Update health metrics after a request"""
        now = datetime.utcnow()
        
        if not self.health_metrics:
            self.health_metrics = HealthMetrics(
                last_check=now,
                response_time_ms=response_time,
                success_rate=100.0 if success else 0.0,
                error_count=0 if success else 1,
                consecutive_failures=0 if success else 1,
                uptime_percentage=100.0 if success else 0.0
            )
        else:
            # Update metrics
            self.health_metrics.last_check = now
            self.health_metrics.response_time_ms = (
                self.health_metrics.response_time_ms * 0.9 + response_time * 0.1
            )
            
            if success:
                self.health_metrics.consecutive_failures = 0
                # Gradually improve success rate
                self.health_metrics.success_rate = min(100.0, self.health_metrics.success_rate + 1.0)
            else:
                self.health_metrics.consecutive_failures += 1
                self.health_metrics.error_count += 1
                self.health_metrics.last_error = error
                # Gradually decrease success rate
                self.health_metrics.success_rate = max(0.0, self.health_metrics.success_rate - 5.0)
        
        self.updated_at = now
    
    def update_usage_metrics(self, tokens_used: int = 0, cost: float = 0.0, response_time: float = 0.0):
        """Update usage metrics after a request"""
        now = datetime.utcnow()
        
        self.usage_metrics.total_requests += 1
        self.usage_metrics.successful_requests += 1
        self.usage_metrics.total_tokens += tokens_used
        self.usage_metrics.total_cost += cost
        self.usage_metrics.last_request_time = now
        
        # Update average response time
        if self.usage_metrics.total_requests == 1:
            self.usage_metrics.average_response_time = response_time
        else:
            self.usage_metrics.average_response_time = (
                self.usage_metrics.average_response_time * 0.9 + response_time * 0.1
            )
        
        self.updated_at = now
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            "provider_id": self.provider_id,
            "provider_type": self.provider_type.value,
            "name": self.name,
            "display_name": self.display_name,
            "description": self.description,
            "version": self.version,
            "status": self.status.value,
            "enabled": self.enabled,
            "priority": self.priority,
            "weight": self.weight,
            "capabilities": [cap.value for cap in self.capabilities],
            "supported_models": [
                {
                    "name": model.name,
                    "display_name": model.display_name,
                    "description": model.description,
                    "context_length": model.context_length,
                    "max_tokens": model.max_tokens,
                    "supports_streaming": model.supports_streaming,
                    "supports_function_calling": model.supports_function_calling,
                    "supports_vision": model.supports_vision,
                    "cost_per_1k_tokens": model.cost_per_1k_tokens,
                    "capabilities": [cap.value for cap in model.capabilities]
                }
                for model in self.supported_models
            ],
            "default_model": self.default_model,
            "is_healthy": self.is_healthy(),
            "is_available": self.is_available(),
            "health_metrics": {
                "last_check": self.health_metrics.last_check.isoformat() if self.health_metrics else None,
                "response_time_ms": self.health_metrics.response_time_ms if self.health_metrics else 0,
                "success_rate": self.health_metrics.success_rate if self.health_metrics else 0,
                "error_count": self.health_metrics.error_count if self.health_metrics else 0,
                "consecutive_failures": self.health_metrics.consecutive_failures if self.health_metrics else 0,
                "uptime_percentage": self.health_metrics.uptime_percentage if self.health_metrics else 0,
                "last_error": self.health_metrics.last_error if self.health_metrics else None
            } if self.health_metrics else None,
            "usage_metrics": {
                "total_requests": self.usage_metrics.total_requests,
                "successful_requests": self.usage_metrics.successful_requests,
                "failed_requests": self.usage_metrics.failed_requests,
                "total_tokens": self.usage_metrics.total_tokens,
                "total_cost": self.usage_metrics.total_cost,
                "average_response_time": self.usage_metrics.average_response_time,
                "requests_per_minute": self.usage_metrics.requests_per_minute,
                "last_request_time": self.usage_metrics.last_request_time.isoformat() if self.usage_metrics.last_request_time else None
            },
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "tags": self.tags
        }
