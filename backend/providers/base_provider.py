"""
Base Provider Abstract Class
Defines the unified interface for all AI providers (API-based and web automation)
"""

from abc import ABC, abstractmethod
from enum import Enum
from typing import Dict, Any, Optional, List, AsyncGenerator
from dataclasses import dataclass
from datetime import datetime
import asyncio
import logging

logger = logging.getLogger(__name__)

class ProviderType(Enum):
    """Types of AI providers supported"""
    API_BASED = "api_based"           # Direct API calls (Codegen, OpenAI, etc.)
    WEB_AUTOMATION = "web_automation" # Browser automation (Claude Web, Z.AI, etc.)
    CUSTOM_WEB = "custom_web"         # Configurable web automation

class ProviderStatus(Enum):
    """Provider operational status"""
    INACTIVE = "inactive"       # Provider is disabled
    INITIALIZING = "initializing" # Provider is starting up
    ACTIVE = "active"          # Provider is ready and operational
    BUSY = "busy"              # Provider is processing a request
    ERROR = "error"            # Provider encountered an error
    RATE_LIMITED = "rate_limited" # Provider is rate limited
    AUTHENTICATION_REQUIRED = "auth_required" # Needs authentication

@dataclass
class ProviderResponse:
    """Standardized response from any provider"""
    content: str
    provider_name: str
    model_name: Optional[str] = None
    success: bool = True
    error: Optional[str] = None
    metadata: Dict[str, Any] = None
    response_time: Optional[float] = None
    tokens_used: Optional[int] = None
    cost: Optional[float] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}

@dataclass
class ProviderContext:
    """Authentication and configuration context for providers"""
    provider_name: str
    auth_type: str  # "token", "username_password", "cookies", "custom"
    credentials: Dict[str, Any]
    settings: Dict[str, Any] = None
    session_data: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.settings is None:
            self.settings = {}
        if self.session_data is None:
            self.session_data = {}

class BaseProvider(ABC):
    """
    Abstract base class for all AI providers
    Defines the unified interface that both API and web automation providers must implement
    """
    
    def __init__(self, name: str, provider_type: ProviderType, config: Dict[str, Any] = None):
        self.name = name
        self.provider_type = provider_type
        self.config = config or {}
        self.status = ProviderStatus.INACTIVE
        self.context: Optional[ProviderContext] = None
        self.last_error: Optional[str] = None
        self.created_at = datetime.now()
        self.last_used_at: Optional[datetime] = None
        self.request_count = 0
        self.error_count = 0
        
    @abstractmethod
    async def initialize(self, context: ProviderContext) -> bool:
        """
        Initialize the provider with authentication context
        Returns True if successful, False otherwise
        """
        pass
    
    @abstractmethod
    async def send_message(self, message: str, **kwargs) -> ProviderResponse:
        """
        Send a message to the AI provider and get response
        Args:
            message: The prompt/message to send
            **kwargs: Additional parameters (model, temperature, etc.)
        Returns:
            ProviderResponse with the AI's response
        """
        pass
    
    @abstractmethod
    async def stream_message(self, message: str, **kwargs) -> AsyncGenerator[str, None]:
        """
        Send a message and stream the response in chunks
        Args:
            message: The prompt/message to send
            **kwargs: Additional parameters
        Yields:
            String chunks of the response as they arrive
        """
        pass
    
    @abstractmethod
    async def health_check(self) -> bool:
        """
        Check if the provider is healthy and responsive
        Returns True if healthy, False otherwise
        """
        pass
    
    @abstractmethod
    async def cleanup(self) -> None:
        """
        Clean up resources (close browser sessions, connections, etc.)
        """
        pass
    
    # Common methods implemented in base class
    
    async def get_status(self) -> ProviderStatus:
        """Get current provider status"""
        return self.status
    
    async def set_status(self, status: ProviderStatus, error: Optional[str] = None):
        """Set provider status and optional error message"""
        self.status = status
        if error:
            self.last_error = error
            self.error_count += 1
            logger.error(f"Provider {self.name} error: {error}")
    
    async def get_info(self) -> Dict[str, Any]:
        """Get provider information and statistics"""
        return {
            "name": self.name,
            "type": self.provider_type.value,
            "status": self.status.value,
            "created_at": self.created_at.isoformat(),
            "last_used_at": self.last_used_at.isoformat() if self.last_used_at else None,
            "request_count": self.request_count,
            "error_count": self.error_count,
            "last_error": self.last_error,
            "config": self.config,
            "has_context": self.context is not None
        }
    
    async def update_config(self, new_config: Dict[str, Any]) -> bool:
        """Update provider configuration"""
        try:
            self.config.update(new_config)
            return True
        except Exception as e:
            await self.set_status(ProviderStatus.ERROR, f"Config update failed: {str(e)}")
            return False
    
    def _record_request(self):
        """Record that a request was made"""
        self.request_count += 1
        self.last_used_at = datetime.now()
    
    def _validate_context(self, context: ProviderContext) -> bool:
        """Validate that the context has required fields for this provider"""
        if not context.provider_name == self.name:
            return False
        
        # Basic validation - subclasses can override for specific requirements
        if not context.auth_type or not context.credentials:
            return False
            
        return True
    
    async def test_connection(self, test_message: str = "Hello - what is your model name?") -> ProviderResponse:
        """
        Test the provider with a standard test message
        """
        try:
            await self.set_status(ProviderStatus.BUSY)
            response = await self.send_message(test_message)
            await self.set_status(ProviderStatus.ACTIVE)
            return response
        except Exception as e:
            await self.set_status(ProviderStatus.ERROR, str(e))
            return ProviderResponse(
                content="",
                provider_name=self.name,
                success=False,
                error=str(e)
            )
    
    def __str__(self) -> str:
        return f"{self.__class__.__name__}(name='{self.name}', type='{self.provider_type.value}', status='{self.status.value}')"
    
    def __repr__(self) -> str:
        return self.__str__()
