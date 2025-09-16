"""
Universal AI Endpoint Manager - Core Management System

Trading bot-style endpoint management similar to the cryptocurrency bot's main class.
Manages AI endpoints with individual server control, health monitoring, and performance tracking.
"""

import asyncio
import logging
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Callable
from concurrent.futures import ThreadPoolExecutor
import threading

from ..models.endpoint import EndpointConfig, EndpointStatus, EndpointType, HealthStatus, BrowserConfig
from ..models.session import SessionManager
from .registry import EndpointRegistry
from .health_monitor import HealthMonitor
from ..providers.factory import ProviderFactory
from ..schemas.response import StandardResponse

logger = logging.getLogger(__name__)

class UniversalEndpointManager:
    """
    Main endpoint manager class - similar to the cryptocurrency bot's KiteAI class
    Manages all AI endpoints with trading bot-style architecture
    """
    
    def __init__(self, config_dir: str = "config"):
        """Initialize the Universal Endpoint Manager"""
        
        # Core components - similar to crypto bot initialization
        self.registry = EndpointRegistry(config_dir)
        self.session_manager = SessionManager(config_dir)
        self.health_monitor = HealthMonitor(self)
        self.provider_factory = ProviderFactory()
        
        # Trading bot-style settings
        self.auto_restart_failed_endpoints = True
        self.health_check_interval = 60  # seconds
        self.performance_monitoring = True
        self.max_concurrent_endpoints = 100
        
        # Runtime state - similar to crypto bot's runtime variables
        self.running_endpoints: Dict[str, Any] = {}  # endpoint_id -> provider instance
        self.endpoint_threads: Dict[str, threading.Thread] = {}
        self.request_queues: Dict[str, asyncio.Queue] = {}
        self.active_requests: Dict[str, int] = {}  # endpoint_id -> active request count
        
        # Performance tracking - similar to crypto bot's metrics
        self.total_requests = 0
        self.successful_requests = 0
        self.failed_requests = 0
        self.start_time = datetime.now()
        
        # Background tasks
        self.background_tasks: List[asyncio.Task] = []
        self.shutdown_event = asyncio.Event()
        
        # Thread pool for blocking operations
        self.executor = ThreadPoolExecutor(max_workers=10)
        
        logger.info("Universal AI Endpoint Manager initialized")
    
    async def start(self):
        """Start the endpoint manager - similar to crypto bot's main loop"""
        logger.info("Starting Universal AI Endpoint Manager...")
        
        # Load existing endpoints from registry
        await self.registry.load_endpoints()
        
        # Start background monitoring tasks
        if self.performance_monitoring:
            self.background_tasks.append(
                asyncio.create_task(self._health_monitoring_loop())
            )
            self.background_tasks.append(
                asyncio.create_task(self._performance_monitoring_loop())
            )
            self.background_tasks.append(
                asyncio.create_task(self._auto_restart_loop())
            )
        
        # Auto-start endpoints that were running before shutdown
        await self._restore_running_endpoints()
        
        logger.info(f"Universal AI Endpoint Manager started with {len(self.registry.endpoints)} endpoints")
    
    async def stop(self):
        """Stop the endpoint manager and cleanup resources"""
        logger.info("Stopping Universal AI Endpoint Manager...")
        
        # Signal shutdown
        self.shutdown_event.set()
        
        # Stop all running endpoints
        await self._stop_all_endpoints()
        
        # Cancel background tasks
        for task in self.background_tasks:
            task.cancel()
        
        # Wait for tasks to complete
        if self.background_tasks:
            await asyncio.gather(*self.background_tasks, return_exceptions=True)
        
        # Cleanup resources
        self.executor.shutdown(wait=True)
        await self.session_manager.cleanup()
        
        logger.info("Universal AI Endpoint Manager stopped")
    
    async def add_endpoint(self, config: EndpointConfig) -> bool:
        """
        Add a new endpoint - similar to crypto bot's account management
        
        Args:
            config: Endpoint configuration
            
        Returns:
            bool: True if endpoint was added successfully
        """
        try:
            # Validate configuration
            if not self._validate_endpoint_config(config):
                logger.error(f"Invalid endpoint configuration: {config.name}")
                return False
            
            # Add to registry
            success = await self.registry.add_endpoint(config)
            if not success:
                logger.error(f"Failed to add endpoint to registry: {config.name}")
                return False
            
            # Initialize request queue
            self.request_queues[config.id] = asyncio.Queue()
            self.active_requests[config.id] = 0
            
            logger.info(f"Added endpoint: {config.name} ({config.id})")
            return True
            
        except Exception as e:
            logger.error(f"Error adding endpoint {config.name}: {e}")
            return False
    
    async def remove_endpoint(self, endpoint_id: str) -> bool:
        """
        Remove an endpoint - similar to crypto bot's account removal
        
        Args:
            endpoint_id: ID of endpoint to remove
            
        Returns:
            bool: True if endpoint was removed successfully
        """
        try:
            # Stop endpoint if running
            if endpoint_id in self.running_endpoints:
                await self.stop_endpoint(endpoint_id)
            
            # Remove from registry
            success = await self.registry.remove_endpoint(endpoint_id)
            if not success:
                logger.error(f"Failed to remove endpoint from registry: {endpoint_id}")
                return False
            
            # Cleanup runtime state
            self.request_queues.pop(endpoint_id, None)
            self.active_requests.pop(endpoint_id, None)
            
            logger.info(f"Removed endpoint: {endpoint_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error removing endpoint {endpoint_id}: {e}")
            return False
    
    async def start_endpoint(self, endpoint_id: str) -> bool:
        """
        Start an endpoint - similar to crypto bot's process management
        
        Args:
            endpoint_id: ID of endpoint to start
            
        Returns:
            bool: True if endpoint started successfully
        """
        try:
            config = await self.registry.get_endpoint(endpoint_id)
            if not config:
                logger.error(f"Endpoint not found: {endpoint_id}")
                return False
            
            if endpoint_id in self.running_endpoints:
                logger.warning(f"Endpoint already running: {endpoint_id}")
                return True
            
            # Update status to starting
            config.update_status(EndpointStatus.STARTING)
            await self.registry.update_endpoint(config)
            
            # Create provider instance
            provider = await self.provider_factory.create_provider(config)
            if not provider:
                logger.error(f"Failed to create provider for endpoint: {endpoint_id}")
                config.update_status(EndpointStatus.ERROR)
                await self.registry.update_endpoint(config)
                return False
            
            # Initialize provider
            try:
                await provider.initialize()
                self.running_endpoints[endpoint_id] = provider
                
                # Update status to running
                config.update_status(EndpointStatus.RUNNING)
                config.update_health(HealthStatus.GOOD)
                await self.registry.update_endpoint(config)
                
                logger.info(f"Started endpoint: {config.name} ({endpoint_id})")
                return True
                
            except Exception as e:
                logger.error(f"Failed to initialize provider for {endpoint_id}: {e}")
                config.update_status(EndpointStatus.ERROR)
                config.update_health(HealthStatus.CRITICAL)
                await self.registry.update_endpoint(config)
                return False
            
        except Exception as e:
            logger.error(f"Error starting endpoint {endpoint_id}: {e}")
            return False
    
    async def stop_endpoint(self, endpoint_id: str) -> bool:
        """
        Stop an endpoint - similar to crypto bot's process stopping
        
        Args:
            endpoint_id: ID of endpoint to stop
            
        Returns:
            bool: True if endpoint stopped successfully
        """
        try:
            config = await self.registry.get_endpoint(endpoint_id)
            if not config:
                logger.error(f"Endpoint not found: {endpoint_id}")
                return False
            
            if endpoint_id not in self.running_endpoints:
                logger.warning(f"Endpoint not running: {endpoint_id}")
                config.update_status(EndpointStatus.STOPPED)
                await self.registry.update_endpoint(config)
                return True
            
            # Update status to stopping
            config.update_status(EndpointStatus.STOPPING)
            await self.registry.update_endpoint(config)
            
            # Stop provider
            provider = self.running_endpoints[endpoint_id]
            try:
                await provider.cleanup()
            except Exception as e:
                logger.warning(f"Error during provider cleanup for {endpoint_id}: {e}")
            
            # Remove from running endpoints
            del self.running_endpoints[endpoint_id]
            
            # Update status to stopped
            config.update_status(EndpointStatus.STOPPED)
            config.update_health(HealthStatus.UNKNOWN)
            await self.registry.update_endpoint(config)
            
            logger.info(f"Stopped endpoint: {config.name} ({endpoint_id})")
            return True
            
        except Exception as e:
            logger.error(f"Error stopping endpoint {endpoint_id}: {e}")
            return False
    
    async def send_request(self, endpoint_id: str, prompt: str, **kwargs) -> StandardResponse:
        """
        Send a request to an endpoint - similar to crypto bot's transaction processing
        
        Args:
            endpoint_id: ID of target endpoint
            prompt: Text prompt to send
            **kwargs: Additional parameters
            
        Returns:
            StandardResponse: Standardized response
        """
        start_time = time.time()
        
        try:
            # Get endpoint configuration
            config = await self.registry.get_endpoint(endpoint_id)
            if not config:
                raise ValueError(f"Endpoint not found: {endpoint_id}")
            
            # Check if endpoint can handle request
            if not config.can_handle_request():
                raise ValueError(f"Endpoint cannot handle request: {endpoint_id} (status: {config.status.value}, health: {config.health.value})")
            
            # Check rate limiting
            if not await self._check_rate_limit(endpoint_id):
                raise ValueError(f"Rate limit exceeded for endpoint: {endpoint_id}")
            
            # Get provider
            provider = self.running_endpoints.get(endpoint_id)
            if not provider:
                raise ValueError(f"Provider not available for endpoint: {endpoint_id}")
            
            # Track active request
            self.active_requests[endpoint_id] = self.active_requests.get(endpoint_id, 0) + 1
            self.total_requests += 1
            
            try:
                # Send request to provider
                response = await provider.send_request(prompt, **kwargs)
                
                # Record successful request
                response_time = time.time() - start_time
                config.record_request(
                    success=True,
                    response_time=response_time,
                    tokens_used=response.usage.get("total_tokens", 0) if response.usage else 0,
                    cost=response.usage.get("cost", 0.0) if response.usage else 0.0
                )
                await self.registry.update_endpoint(config)
                
                self.successful_requests += 1
                logger.debug(f"Request successful for {endpoint_id}: {response_time:.2f}s")
                
                return response
                
            except Exception as e:
                # Record failed request
                response_time = time.time() - start_time
                config.record_request(success=False, response_time=response_time)
                await self.registry.update_endpoint(config)
                
                self.failed_requests += 1
                logger.error(f"Request failed for {endpoint_id}: {e}")
                raise
            
            finally:
                # Decrease active request count
                self.active_requests[endpoint_id] = max(0, self.active_requests.get(endpoint_id, 1) - 1)
        
        except Exception as e:
            logger.error(f"Error processing request for {endpoint_id}: {e}")
            raise
    
    async def get_endpoint_status(self, endpoint_id: str) -> Optional[Dict[str, Any]]:
        """Get detailed status of an endpoint - similar to crypto bot's account status"""
        config = await self.registry.get_endpoint(endpoint_id)
        if not config:
            return None
        
        return {
            "config": config.to_dict(),
            "is_running": endpoint_id in self.running_endpoints,
            "active_requests": self.active_requests.get(endpoint_id, 0),
            "queue_size": self.request_queues[endpoint_id].qsize() if endpoint_id in self.request_queues else 0
        }
    
    async def list_endpoints(self, status_filter: Optional[EndpointStatus] = None) -> List[Dict[str, Any]]:
        """List all endpoints with their status - similar to crypto bot's account listing"""
        endpoints = []
        
        for endpoint_id, config in self.registry.endpoints.items():
            if status_filter and config.status != status_filter:
                continue
            
            endpoint_info = {
                "config": config.to_dict(),
                "is_running": endpoint_id in self.running_endpoints,
                "active_requests": self.active_requests.get(endpoint_id, 0),
                "queue_size": self.request_queues[endpoint_id].qsize() if endpoint_id in self.request_queues else 0
            }
            endpoints.append(endpoint_info)
        
        # Sort by priority (higher first) then by name
        endpoints.sort(key=lambda x: (-x["config"]["priority"], x["config"]["name"]))
        return endpoints
    
    async def get_system_metrics(self) -> Dict[str, Any]:
        """Get overall system metrics - similar to crypto bot's performance metrics"""
        uptime = (datetime.now() - self.start_time).total_seconds()
        
        return {
            "uptime_seconds": uptime,
            "total_endpoints": len(self.registry.endpoints),
            "running_endpoints": len(self.running_endpoints),
            "total_requests": self.total_requests,
            "successful_requests": self.successful_requests,
            "failed_requests": self.failed_requests,
            "success_rate": (self.successful_requests / max(1, self.total_requests)) * 100,
            "requests_per_second": self.total_requests / max(1, uptime),
            "active_requests_total": sum(self.active_requests.values()),
            "memory_usage": await self._get_memory_usage()
        }
    
    # Private methods - similar to crypto bot's internal methods
    
    def _validate_endpoint_config(self, config: EndpointConfig) -> bool:
        """Validate endpoint configuration"""
        if not config.name or not config.url:
            return False
        
        if config.endpoint_type in [EndpointType.WEB_CHAT, EndpointType.ZAI_WEB, EndpointType.CUSTOM_WEB]:
            if not config.browser_config:
                config.browser_config = BrowserConfig()
        
        return True
    
    async def _check_rate_limit(self, endpoint_id: str) -> bool:
        """Check if endpoint is within rate limits"""
        config = await self.registry.get_endpoint(endpoint_id)
        if not config:
            return False
        
        # Simple rate limiting - can be enhanced with more sophisticated algorithms
        active_count = self.active_requests.get(endpoint_id, 0)
        return active_count < config.max_concurrent_requests
    
    async def _health_monitoring_loop(self):
        """Background health monitoring loop - similar to crypto bot's monitoring"""
        while not self.shutdown_event.is_set():
            try:
                await self.health_monitor.check_all_endpoints()
                await asyncio.sleep(self.health_check_interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in health monitoring loop: {e}")
                await asyncio.sleep(5)
    
    async def _performance_monitoring_loop(self):
        """Background performance monitoring loop"""
        while not self.shutdown_event.is_set():
            try:
                # Log system metrics periodically
                metrics = await self.get_system_metrics()
                logger.info(f"System metrics: {metrics['running_endpoints']}/{metrics['total_endpoints']} endpoints running, "
                           f"{metrics['success_rate']:.1f}% success rate, {metrics['requests_per_second']:.2f} req/s")
                
                await asyncio.sleep(300)  # Every 5 minutes
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in performance monitoring loop: {e}")
                await asyncio.sleep(30)
    
    async def _auto_restart_loop(self):
        """Auto-restart failed endpoints loop - similar to crypto bot's auto-recovery"""
        while not self.shutdown_event.is_set():
            try:
                if self.auto_restart_failed_endpoints:
                    for endpoint_id, config in self.registry.endpoints.items():
                        if config.status == EndpointStatus.ERROR and config.auto_restart:
                            logger.info(f"Auto-restarting failed endpoint: {config.name}")
                            await self.start_endpoint(endpoint_id)
                
                await asyncio.sleep(60)  # Check every minute
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in auto-restart loop: {e}")
                await asyncio.sleep(30)
    
    async def _restore_running_endpoints(self):
        """Restore endpoints that were running before shutdown"""
        for endpoint_id, config in self.registry.endpoints.items():
            if config.status == EndpointStatus.RUNNING:
                logger.info(f"Restoring endpoint: {config.name}")
                await self.start_endpoint(endpoint_id)
    
    async def _stop_all_endpoints(self):
        """Stop all running endpoints"""
        stop_tasks = []
        for endpoint_id in list(self.running_endpoints.keys()):
            stop_tasks.append(self.stop_endpoint(endpoint_id))
        
        if stop_tasks:
            await asyncio.gather(*stop_tasks, return_exceptions=True)
    
    async def _get_memory_usage(self) -> Dict[str, Any]:
        """Get memory usage statistics"""
        try:
            import psutil
            process = psutil.Process()
            memory_info = process.memory_info()
            return {
                "rss": memory_info.rss,
                "vms": memory_info.vms,
                "percent": process.memory_percent()
            }
        except ImportError:
            return {"error": "psutil not available"}
        except Exception as e:
            return {"error": str(e)}
