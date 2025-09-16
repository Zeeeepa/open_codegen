"""
Core service layer for AI endpoint lifecycle management.
Handles starting, stopping, testing, and monitoring endpoints.
"""
import asyncio
import logging
import uuid
from datetime import datetime
from typing import Dict, Any, Optional, List
from contextlib import asynccontextmanager

from backend.database.models import (
    EndpointConfig, EndpointStatus, ProviderType,
    EndpointMetrics, get_database_manager
)

logger = logging.getLogger(__name__)


class EndpointServiceError(Exception):
    """Base exception for endpoint service errors."""
    pass


class EndpointNotFoundError(EndpointServiceError):
    """Raised when endpoint is not found."""
    pass


class EndpointStartError(EndpointServiceError):
    """Raised when endpoint fails to start."""
    pass


class EndpointService:
    """
    Core service for managing AI endpoint lifecycle.
    
    Handles starting, stopping, testing, and monitoring endpoints
    across different provider types (REST_API, WEB_CHAT, API_TOKEN).
    """
    
    def __init__(self):
        self.db = get_database_manager()
        self._running_endpoints: Dict[str, Any] = {}
        self._health_check_tasks: Dict[str, asyncio.Task] = {}
    
    async def start_endpoint(self, endpoint_id: str) -> bool:
        """
        Start an endpoint and begin health monitoring.
        
        Args:
            endpoint_id: ID of the endpoint to start
            
        Returns:
            True if started successfully, False otherwise
            
        Raises:
            EndpointNotFoundError: If endpoint doesn't exist
            EndpointStartError: If endpoint fails to start
        """
        config = self.db.get_endpoint_config(endpoint_id)
        if not config:
            raise EndpointNotFoundError(f"Endpoint {endpoint_id} not found")
        
        if config.status == EndpointStatus.RUNNING.value:
            logger.info(f"Endpoint {endpoint_id} already running")
            return True
        
        try:
            # Update status to starting
            config.status = EndpointStatus.STARTING.value
            self.db.update_endpoint_config(config)
            
            # Initialize provider-specific handler
            handler = await self._create_provider_handler(config)
            
            # Start the endpoint
            await handler.start()
            
            # Store running endpoint
            self._running_endpoints[endpoint_id] = handler
            
            # Update status to running
            config.status = EndpointStatus.RUNNING.value
            self.db.update_endpoint_config(config)
            
            # Start health monitoring
            await self._start_health_monitoring(endpoint_id)
            
            logger.info(f"Successfully started endpoint {endpoint_id}")
            return True
            
        except Exception as e:
            # Update status to error
            config.status = EndpointStatus.ERROR.value
            self.db.update_endpoint_config(config)
            
            logger.error(f"Failed to start endpoint {endpoint_id}: {e}")
            raise EndpointStartError(f"Failed to start endpoint: {e}")
    
    async def stop_endpoint(self, endpoint_id: str) -> bool:
        """
        Stop an endpoint and cleanup resources.
        
        Args:
            endpoint_id: ID of the endpoint to stop
            
        Returns:
            True if stopped successfully, False otherwise
        """
        config = self.db.get_endpoint_config(endpoint_id)
        if not config:
            logger.warning(f"Endpoint {endpoint_id} not found for stopping")
            return False
        
        try:
            # Stop health monitoring
            await self._stop_health_monitoring(endpoint_id)
            
            # Stop the endpoint handler
            if endpoint_id in self._running_endpoints:
                handler = self._running_endpoints[endpoint_id]
                await handler.stop()
                del self._running_endpoints[endpoint_id]
            
            # Update status
            config.status = EndpointStatus.STOPPED.value
            self.db.update_endpoint_config(config)
            
            logger.info(f"Successfully stopped endpoint {endpoint_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error stopping endpoint {endpoint_id}: {e}")
            return False
    
    async def test_endpoint(
        self, 
        endpoint_id: str, 
        test_message: str = "Hello, this is a test message"
    ) -> Dict[str, Any]:
        """
        Test an endpoint with a simple message.
        
        Args:
            endpoint_id: ID of the endpoint to test
            test_message: Message to send for testing
            
        Returns:
            Dictionary with test results including success, response, and timing
        """
        config = self.db.get_endpoint_config(endpoint_id)
        if not config:
            return {
                "success": False,
                "error": f"Endpoint {endpoint_id} not found",
                "response_time_ms": 0
            }
        
        start_time = datetime.utcnow()
        
        try:
            # Create temporary handler for testing
            handler = await self._create_provider_handler(config)
            
            # Send test message
            response = await handler.send_message(test_message)
            
            # Calculate response time
            end_time = datetime.utcnow()
            response_time_ms = int((end_time - start_time).total_seconds() * 1000)
            
            # Record metrics
            await self._record_test_metrics(
                endpoint_id, response_time_ms, True, None, test_message, response
            )
            
            return {
                "success": True,
                "response": response,
                "response_time_ms": response_time_ms,
                "error": None
            }
            
        except Exception as e:
            # Calculate response time for failed request
            end_time = datetime.utcnow()
            response_time_ms = int((end_time - start_time).total_seconds() * 1000)
            
            # Record failed metrics
            await self._record_test_metrics(
                endpoint_id, response_time_ms, False, str(e), test_message, None
            )
            
            logger.error(f"Test failed for endpoint {endpoint_id}: {e}")
            return {
                "success": False,
                "error": str(e),
                "response_time_ms": response_time_ms,
                "response": None
            }
    
    async def get_endpoint_status(self, endpoint_id: str) -> Optional[str]:
        """Get current status of an endpoint."""
        config = self.db.get_endpoint_config(endpoint_id)
        return config.status if config else None
    
    async def list_running_endpoints(self) -> List[str]:
        """Get list of currently running endpoint IDs."""
        return list(self._running_endpoints.keys())
    
    async def shutdown_all_endpoints(self):
        """Shutdown all running endpoints gracefully."""
        logger.info("Shutting down all endpoints...")
        
        # Stop all endpoints
        for endpoint_id in list(self._running_endpoints.keys()):
            await self.stop_endpoint(endpoint_id)
        
        logger.info("All endpoints shut down")
    
    async def _create_provider_handler(self, config: EndpointConfig):
        """Create appropriate handler based on provider type."""
        from backend.endpoint_manager.providers import (
            RestApiHandler, WebChatHandler, ApiTokenHandler
        )
        
        if config.provider_type == ProviderType.REST_API.value:
            return RestApiHandler(config)
        elif config.provider_type == ProviderType.WEB_CHAT.value:
            return WebChatHandler(config)
        elif config.provider_type == ProviderType.API_TOKEN.value:
            return ApiTokenHandler(config)
        else:
            raise ValueError(f"Unsupported provider type: {config.provider_type}")
    
    async def _start_health_monitoring(self, endpoint_id: str):
        """Start background health monitoring for an endpoint."""
        if endpoint_id in self._health_check_tasks:
            return  # Already monitoring
        
        async def health_check_loop():
            """Background task for health monitoring."""
            while endpoint_id in self._running_endpoints:
                try:
                    # Perform health check
                    await self._perform_health_check(endpoint_id)
                    
                    # Wait before next check (30 seconds)
                    await asyncio.sleep(30)
                    
                except asyncio.CancelledError:
                    break
                except Exception as e:
                    logger.error(f"Health check error for {endpoint_id}: {e}")
                    await asyncio.sleep(30)  # Continue monitoring despite errors
        
        # Start the health check task
        task = asyncio.create_task(health_check_loop())
        self._health_check_tasks[endpoint_id] = task
    
    async def _stop_health_monitoring(self, endpoint_id: str):
        """Stop health monitoring for an endpoint."""
        if endpoint_id in self._health_check_tasks:
            task = self._health_check_tasks[endpoint_id]
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass
            del self._health_check_tasks[endpoint_id]
    
    async def _perform_health_check(self, endpoint_id: str):
        """Perform a health check on a running endpoint."""
        if endpoint_id not in self._running_endpoints:
            return
        
        try:
            handler = self._running_endpoints[endpoint_id]
            is_healthy = await handler.health_check()
            
            if not is_healthy:
                logger.warning(f"Health check failed for endpoint {endpoint_id}")
                # Update status to error
                config = self.db.get_endpoint_config(endpoint_id)
                if config:
                    config.status = EndpointStatus.ERROR.value
                    self.db.update_endpoint_config(config)
            
        except Exception as e:
            logger.error(f"Health check exception for {endpoint_id}: {e}")
    
    async def _record_test_metrics(
        self,
        endpoint_id: str,
        response_time_ms: int,
        success: bool,
        error_message: Optional[str],
        test_message: str,
        response: Optional[str]
    ):
        """Record test metrics to database."""
        try:
            metrics = EndpointMetrics(
                id=str(uuid.uuid4()),
                endpoint_id=endpoint_id,
                response_time_ms=response_time_ms,
                success=success,
                error_message=error_message,
                input_tokens=len(test_message.split()) if test_message else 0,
                output_tokens=len(response.split()) if response else 0,
                request_id=f"test-{uuid.uuid4()}",
                user_agent="endpoint-service-test",
                created_at=""  # Will be set by database
            )
            
            self.db.record_endpoint_metrics(metrics)
            
        except Exception as e:
            logger.error(f"Failed to record test metrics: {e}")


# Global service instance
_endpoint_service = None


def get_endpoint_service() -> EndpointService:
    """Get global endpoint service instance."""
    global _endpoint_service
    if _endpoint_service is None:
        _endpoint_service = EndpointService()
    return _endpoint_service


@asynccontextmanager
async def endpoint_service_lifespan():
    """Context manager for endpoint service lifecycle."""
    service = get_endpoint_service()
    try:
        yield service
    finally:
        await service.shutdown_all_endpoints()
