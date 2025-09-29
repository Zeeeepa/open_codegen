"""
Base Provider class for all AI providers
"""

import asyncio
import logging
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, AsyncGenerator
from datetime import datetime

logger = logging.getLogger(__name__)

class BaseProvider(ABC):
    """Base class for all AI providers."""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.name = self.__class__.__name__.replace("Provider", "").lower()
        self.enabled = config.get("enabled", False)
        self.priority = config.get("priority", 999)
        self.timeout = config.get("timeout", 60)
        self.credentials = config.get("credentials", {})
        
        # Statistics
        self.stats = {
            "requests_total": 0,
            "requests_successful": 0,
            "requests_failed": 0,
            "total_response_time": 0.0,
            "last_request_time": None,
            "last_error": None,
            "initialized_at": None
        }
        
        self.initialized = False
    
    @abstractmethod
    async def initialize(self):
        """Initialize the provider."""
        pass
    
    @abstractmethod
    async def process_request(self, webchat_request: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process a WebChat format request and return WebChat format response.
        
        Args:
            webchat_request: Request in universal WebChat format
            
        Returns:
            Response in universal WebChat format
        """
        pass
    
    @abstractmethod
    async def health_check(self) -> bool:
        """Check if the provider is healthy and responsive."""
        pass
    
    async def shutdown(self):
        """Shutdown the provider and cleanup resources."""
        self.initialized = False
        logger.info(f"Provider {self.name} shutdown")
    
    async def get_stats(self) -> Dict[str, Any]:
        """Get provider statistics."""
        stats = self.stats.copy()
        
        # Calculate average response time
        if stats["requests_successful"] > 0:
            stats["avg_response_time"] = stats["total_response_time"] / stats["requests_successful"]
        else:
            stats["avg_response_time"] = 0.0
        
        # Calculate success rate
        if stats["requests_total"] > 0:
            stats["success_rate"] = stats["requests_successful"] / stats["requests_total"]
        else:
            stats["success_rate"] = 0.0
        
        return stats
    
    def _record_request_start(self):
        """Record the start of a request."""
        self.stats["requests_total"] += 1
        self.stats["last_request_time"] = datetime.now().isoformat()
        return asyncio.get_event_loop().time()
    
    def _record_request_success(self, start_time: float):
        """Record a successful request."""
        response_time = asyncio.get_event_loop().time() - start_time
        self.stats["requests_successful"] += 1
        self.stats["total_response_time"] += response_time
        self.stats["last_error"] = None
    
    def _record_request_failure(self, error: str):
        """Record a failed request."""
        self.stats["requests_failed"] += 1
        self.stats["last_error"] = error
    
    def _create_error_response(self, error_message: str) -> Dict[str, Any]:
        """Create a standard error response in WebChat format."""
        return {
            "success": False,
            "error": error_message,
            "provider": self.name,
            "timestamp": datetime.now().isoformat(),
            "content": f"Error from {self.name}: {error_message}",
            "metadata": {
                "error_type": "provider_error",
                "provider": self.name
            }
        }
    
    def _create_success_response(self, content: str, metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Create a standard success response in WebChat format."""
        return {
            "success": True,
            "provider": self.name,
            "timestamp": datetime.now().isoformat(),
            "content": content,
            "metadata": metadata or {},
            "streaming": False
        }
    
    def _create_streaming_response(self, stream: AsyncGenerator[str, None], metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Create a streaming response in WebChat format."""
        return {
            "success": True,
            "provider": self.name,
            "timestamp": datetime.now().isoformat(),
            "streaming": True,
            "stream": stream,
            "metadata": metadata or {}
        }
    
    def __str__(self):
        return f"{self.name}Provider(enabled={self.enabled}, priority={self.priority})"
    
    def __repr__(self):
        return self.__str__()
