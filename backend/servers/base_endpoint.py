"""
Base Endpoint Server Class
Abstract base class for all endpoint types (web_chat, rest_api)
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, AsyncGenerator
import asyncio
import logging
import time
from enum import Enum

logger = logging.getLogger(__name__)

class EndpointStatus(Enum):
    """Endpoint status enumeration"""
    STOPPED = "stopped"
    STARTING = "starting"
    RUNNING = "running"
    STOPPING = "stopping"
    ERROR = "error"
    UNKNOWN = "unknown"

class EndpointHealth(Enum):
    """Endpoint health enumeration"""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"

class EndpointMetrics:
    """Endpoint metrics tracking"""
    
    def __init__(self):
        self.total_requests = 0
        self.successful_requests = 0
        self.failed_requests = 0
        self.total_response_time = 0.0
        self.start_time = time.time()
        self.last_request_time = None
        self.last_error = None
        self.error_count = 0
        
    @property
    def success_rate(self) -> float:
        """Calculate success rate percentage"""
        if self.total_requests == 0:
            return 0.0
        return (self.successful_requests / self.total_requests) * 100
    
    @property
    def average_response_time(self) -> float:
        """Calculate average response time in milliseconds"""
        if self.successful_requests == 0:
            return 0.0
        return self.total_response_time / self.successful_requests
    
    @property
    def uptime(self) -> float:
        """Calculate uptime in seconds"""
        return time.time() - self.start_time
    
    def record_request(self, success: bool, response_time: float, error: Optional[str] = None):
        """Record a request and its metrics"""
        self.total_requests += 1
        self.last_request_time = time.time()
        
        if success:
            self.successful_requests += 1
            self.total_response_time += response_time
        else:
            self.failed_requests += 1
            if error:
                self.last_error = error
                self.error_count += 1
    
    def reset(self):
        """Reset all metrics"""
        self.total_requests = 0
        self.successful_requests = 0
        self.failed_requests = 0
        self.total_response_time = 0.0
        self.start_time = time.time()
        self.last_request_time = None
        self.last_error = None
        self.error_count = 0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert metrics to dictionary"""
        return {
            "total_requests": self.total_requests,
            "successful_requests": self.successful_requests,
            "failed_requests": self.failed_requests,
            "success_rate": round(self.success_rate, 2),
            "average_response_time": round(self.average_response_time, 2),
            "uptime": round(self.uptime, 2),
            "last_request_time": self.last_request_time,
            "last_error": self.last_error,
            "error_count": self.error_count
        }

class BaseEndpoint(ABC):
    """Abstract base class for all endpoint types"""
    
    def __init__(self, name: str, config: Dict[str, Any], priority: int = 50):
        self.name = name
        self.config = config
        self.priority = priority  # Higher numbers = higher priority
        self.status = EndpointStatus.STOPPED
        self.health = EndpointHealth.UNKNOWN
        self.metrics = EndpointMetrics()
        self._running = False
        self._session_data = {}
        
        # Extract common configuration
        self.url = config.get('url', '')
        self.timeout = config.get('timeout', 30)
        self.max_retries = config.get('max_retries', 3)
        self.use_proxy = config.get('use_proxy', False)
        
        logger.info(f"Initialized endpoint: {self.name} ({self.__class__.__name__})")
    
    @abstractmethod
    async def start(self) -> bool:
        """Start the endpoint server"""
        pass
    
    @abstractmethod
    async def stop(self) -> bool:
        """Stop the endpoint server"""
        pass
    
    @abstractmethod
    async def send_message(self, message: str, **kwargs) -> Optional[str]:
        """Send a message and get response"""
        pass
    
    @abstractmethod
    async def health_check(self) -> bool:
        """Perform health check"""
        pass
    
    async def stream_message(self, message: str, **kwargs) -> AsyncGenerator[str, None]:
        """Stream message response (default implementation)"""
        # Default implementation for non-streaming endpoints
        response = await self.send_message(message, **kwargs)
        if response:
            # Simulate streaming by yielding chunks
            words = response.split()
            for i, word in enumerate(words):
                if i == 0:
                    yield word
                else:
                    yield f" {word}"
                await asyncio.sleep(0.01)  # Small delay to simulate streaming
    
    async def test_connection(self) -> Dict[str, Any]:
        """Test the endpoint connection"""
        start_time = time.time()
        
        try:
            # Send a simple test message
            test_message = "Hello, this is a connection test."
            response = await self.send_message(test_message)
            
            end_time = time.time()
            response_time = (end_time - start_time) * 1000  # Convert to milliseconds
            
            if response:
                return {
                    "success": True,
                    "response_time": round(response_time, 2),
                    "response": response[:100] + "..." if len(response) > 100 else response
                }
            else:
                return {
                    "success": False,
                    "response_time": round(response_time, 2),
                    "error": "No response received"
                }
                
        except Exception as e:
            end_time = time.time()
            response_time = (end_time - start_time) * 1000
            
            return {
                "success": False,
                "response_time": round(response_time, 2),
                "error": str(e)
            }
    
    def update_status(self, status: EndpointStatus):
        """Update endpoint status"""
        old_status = self.status
        self.status = status
        logger.info(f"Endpoint {self.name} status changed: {old_status.value} -> {status.value}")
    
    def update_health(self, health: EndpointHealth):
        """Update endpoint health"""
        old_health = self.health
        self.health = health
        if old_health != health:
            logger.info(f"Endpoint {self.name} health changed: {old_health.value} -> {health.value}")
    
    async def _perform_health_check(self):
        """Internal health check with metrics update"""
        try:
            is_healthy = await self.health_check()
            
            if is_healthy:
                self.update_health(EndpointHealth.HEALTHY)
            else:
                self.update_health(EndpointHealth.UNHEALTHY)
                
            return is_healthy
            
        except Exception as e:
            logger.error(f"Health check failed for {self.name}: {e}")
            self.update_health(EndpointHealth.UNHEALTHY)
            return False
    
    async def _send_message_with_metrics(self, message: str, **kwargs) -> Optional[str]:
        """Send message with automatic metrics tracking"""
        start_time = time.time()
        
        try:
            response = await self.send_message(message, **kwargs)
            end_time = time.time()
            response_time = (end_time - start_time) * 1000  # Convert to milliseconds
            
            # Record successful request
            self.metrics.record_request(True, response_time)
            
            return response
            
        except Exception as e:
            end_time = time.time()
            response_time = (end_time - start_time) * 1000
            
            # Record failed request
            self.metrics.record_request(False, response_time, str(e))
            
            logger.error(f"Message send failed for {self.name}: {e}")
            raise
    
    def get_info(self) -> Dict[str, Any]:
        """Get endpoint information"""
        return {
            "name": self.name,
            "type": self.__class__.__name__.replace("Endpoint", "").lower(),
            "url": self.url,
            "status": self.status.value,
            "health": self.health.value,
            "config": self.config,
            "metrics": self.metrics.to_dict(),
            "session_data": {
                "has_session": bool(self._session_data),
                "session_keys": list(self._session_data.keys()) if self._session_data else []
            }
        }
    
    def reset_metrics(self):
        """Reset endpoint metrics"""
        self.metrics.reset()
        logger.info(f"Metrics reset for endpoint: {self.name}")
    
    def is_running(self) -> bool:
        """Check if endpoint is running"""
        return self._running and self.status == EndpointStatus.RUNNING
    
    def get_session_data(self, key: str, default=None):
        """Get session data"""
        return self._session_data.get(key, default)
    
    def set_session_data(self, key: str, value: Any):
        """Set session data"""
        self._session_data[key] = value
    
    def clear_session_data(self):
        """Clear all session data"""
        self._session_data.clear()
        logger.info(f"Session data cleared for endpoint: {self.name}")
    
    async def __aenter__(self):
        """Async context manager entry"""
        await self.start()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        await self.stop()
    
    def __repr__(self):
        return f"{self.__class__.__name__}(name='{self.name}', status='{self.status.value}', health='{self.health.value}')"
