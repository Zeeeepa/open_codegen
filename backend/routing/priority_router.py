"""
Priority-Based Router - Routes requests based on endpoint priorities with intelligent fallback
"""
import logging
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class PriorityRouter:
    """
    Routes requests to endpoints based on priority levels with intelligent fallback chains
    Higher numbers = higher priority
    """
    
    def __init__(self, endpoint_manager):
        self.endpoint_manager = endpoint_manager
        self.failure_counts = {}  # Track failures for circuit breaker
        self.last_failure_time = {}
        self.circuit_breaker_threshold = 5  # Failures before circuit opens
        self.circuit_breaker_timeout = 300  # 5 minutes
        
    async def route_request(
        self, 
        model: Optional[str] = None,
        message: str = "",
        url: str = "",
        request_data: Dict[str, Any] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Route request using priority-based selection with fallback
        """
        try:
            # Get all active endpoints sorted by priority (highest first)
            endpoints = await self._get_prioritized_endpoints()
            
            if not endpoints:
                logger.warning("No active endpoints available")
                return None
            
            # If model is specified, try to find matching endpoint first
            if model:
                target_endpoint = await self._find_endpoint_by_model(model, endpoints)
                if target_endpoint:
                    response = await self._try_endpoint(target_endpoint, message, request_data)
                    if response:
                        return response
                    # If specific model fails, continue with priority fallback
            
            # Try endpoints in priority order
            for endpoint in endpoints:
                if await self._is_endpoint_available(endpoint):
                    response = await self._try_endpoint(endpoint, message, request_data)
                    if response:
                        await self._record_success(endpoint['name'])
                        return response
                    else:
                        await self._record_failure(endpoint['name'])
            
            logger.error("All endpoints failed or unavailable")
            return None
            
        except Exception as e:
            logger.error(f"Error in priority routing: {e}")
            return None
    
    async def _get_prioritized_endpoints(self) -> List[Dict[str, Any]]:
        """
        Get all active endpoints sorted by priority (highest first)
        """
        try:
            # Get active endpoints from endpoint manager
            active_endpoints = self.endpoint_manager.get_active_endpoints_server()
            
            # Sort by priority (highest first), then by name for consistency
            sorted_endpoints = sorted(
                active_endpoints,
                key=lambda x: (x.get('priority', 0), x.get('name', '')),
                reverse=True
            )
            
            return sorted_endpoints
            
        except Exception as e:
            logger.error(f"Error getting prioritized endpoints: {e}")
            return []
    
    async def _find_endpoint_by_model(
        self, 
        model: str, 
        endpoints: List[Dict[str, Any]]
    ) -> Optional[Dict[str, Any]]:
        """
        Find endpoint that matches the specified model name
        """
        # Direct name match
        for endpoint in endpoints:
            if endpoint.get('name') == model:
                return endpoint
        
        # Partial name match
        for endpoint in endpoints:
            if model.lower() in endpoint.get('name', '').lower():
                return endpoint
        
        # Model field match
        for endpoint in endpoints:
            if endpoint.get('model') == model:
                return endpoint
        
        return None
    
    async def _is_endpoint_available(self, endpoint: Dict[str, Any]) -> bool:
        """
        Check if endpoint is available (not in circuit breaker state)
        """
        endpoint_name = endpoint.get('name')
        
        # Check circuit breaker
        if endpoint_name in self.failure_counts:
            failure_count = self.failure_counts[endpoint_name]
            last_failure = self.last_failure_time.get(endpoint_name)
            
            if failure_count >= self.circuit_breaker_threshold:
                if last_failure and datetime.now() - last_failure < timedelta(seconds=self.circuit_breaker_timeout):
                    logger.warning(f"Endpoint {endpoint_name} is in circuit breaker state")
                    return False
                else:
                    # Reset circuit breaker after timeout
                    self.failure_counts[endpoint_name] = 0
                    logger.info(f"Circuit breaker reset for endpoint {endpoint_name}")
        
        # Check endpoint health
        try:
            health = await self.endpoint_manager.health_check_endpoint_server(endpoint_name)
            return health.get('status') == 'healthy'
        except Exception as e:
            logger.error(f"Health check failed for {endpoint_name}: {e}")
            return False
    
    async def _try_endpoint(
        self, 
        endpoint: Dict[str, Any], 
        message: str,
        request_data: Dict[str, Any] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Try to get response from specific endpoint
        """
        endpoint_name = endpoint.get('name')
        
        try:
            logger.info(f"Trying endpoint: {endpoint_name} (priority: {endpoint.get('priority', 0)})")
            
            # Use endpoint manager to send message
            response = await self.endpoint_manager.test_endpoint_server(endpoint_name, message)
            
            if response:
                # Format as OpenAI-compatible response
                return {
                    "id": f"chatcmpl-{datetime.now().strftime('%Y%m%d%H%M%S')}",
                    "object": "chat.completion",
                    "created": int(datetime.now().timestamp()),
                    "model": endpoint_name,
                    "choices": [
                        {
                            "index": 0,
                            "message": {
                                "role": "assistant",
                                "content": response
                            },
                            "finish_reason": "stop"
                        }
                    ],
                    "usage": {
                        "prompt_tokens": len(message.split()),
                        "completion_tokens": len(response.split()),
                        "total_tokens": len(message.split()) + len(response.split())
                    },
                    "endpoint_info": {
                        "name": endpoint_name,
                        "priority": endpoint.get('priority', 0),
                        "provider_type": endpoint.get('provider_type', 'unknown')
                    }
                }
            
            return None
            
        except Exception as e:
            logger.error(f"Error trying endpoint {endpoint_name}: {e}")
            return None
    
    async def _record_success(self, endpoint_name: str):
        """
        Record successful request for endpoint
        """
        # Reset failure count on success
        if endpoint_name in self.failure_counts:
            self.failure_counts[endpoint_name] = 0
        
        logger.debug(f"Success recorded for endpoint: {endpoint_name}")
    
    async def _record_failure(self, endpoint_name: str):
        """
        Record failed request for endpoint
        """
        if endpoint_name not in self.failure_counts:
            self.failure_counts[endpoint_name] = 0
        
        self.failure_counts[endpoint_name] += 1
        self.last_failure_time[endpoint_name] = datetime.now()
        
        logger.warning(f"Failure recorded for endpoint: {endpoint_name} (count: {self.failure_counts[endpoint_name]})")
    
    def get_endpoint_priorities(self) -> Dict[str, int]:
        """
        Get current endpoint priorities
        """
        try:
            endpoints = self.endpoint_manager.get_active_endpoints_server()
            return {ep.get('name'): ep.get('priority', 0) for ep in endpoints}
        except Exception as e:
            logger.error(f"Error getting endpoint priorities: {e}")
            return {}
    
    async def set_endpoint_priority(self, endpoint_name: str, priority: int) -> bool:
        """
        Set priority for specific endpoint
        """
        try:
            # This would need to be implemented in the endpoint manager
            # For now, return True as placeholder
            logger.info(f"Setting priority {priority} for endpoint {endpoint_name}")
            return True
        except Exception as e:
            logger.error(f"Error setting endpoint priority: {e}")
            return False
