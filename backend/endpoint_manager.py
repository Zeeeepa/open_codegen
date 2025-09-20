"""
Endpoint Manager for the Universal AI Endpoint Management System
Trading bot-style management for AI endpoints
"""

import asyncio
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime
from dataclasses import dataclass, asdict

from .database import get_database_manager
from .models.providers import EndpointProvider, ProviderType
from .servers import BaseEndpoint
from .adapters.base_adapter import BaseAdapter, AdapterResponse
from .adapters.rest_api_adapter import RestApiAdapter
from .adapters.web_chat_adapter import WebChatAdapter
from .adapters.zai_sdk_adapter import ZaiSdkAdapter

logger = logging.getLogger(__name__)

@dataclass
class EndpointMetrics:
    """Metrics for endpoint performance tracking"""
    endpoint_id: str
    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    average_response_time: float = 0.0
    last_request_time: Optional[str] = None
    uptime_percentage: float = 100.0
    cost_per_request: float = 0.0
    
    @property
    def success_rate(self) -> float:
        if self.total_requests == 0:
            return 0.0
        return (self.successful_requests / self.total_requests) * 100
    
    @property
    def error_rate(self) -> float:
        return 100.0 - self.success_rate

class EndpointManager:
    """Trading bot-style manager for AI endpoints"""
    
    def __init__(self):
        self.db_manager = get_database_manager()
        self.active_adapters: Dict[str, BaseAdapter] = {}
        self.active_endpoints: Dict[str, BaseEndpoint] = {}
        self.endpoint_metrics: Dict[str, EndpointMetrics] = {}
        self.is_running = False
        
    async def start(self):
        """Start the endpoint manager"""
        self.is_running = True
        logger.info("Endpoint Manager started")
        
        # Load and initialize default endpoints
        await self._initialize_default_endpoints()
        
        # Start health monitoring
        asyncio.create_task(self._health_monitor_loop())
        
    async def stop(self):
        """Stop the endpoint manager"""
        self.is_running = False
        
        # Clean up all adapters
        for adapter in self.active_adapters.values():
            await adapter.cleanup()
        
        self.active_adapters.clear()
        logger.info("Endpoint Manager stopped")
    
    async def _initialize_default_endpoints(self):
        """Initialize default endpoints from database"""
        try:
            with self.db_manager.get_session() as session:
                providers = session.query(EndpointProvider).filter(
                    EndpointProvider.is_default
                ).all()
                
                for provider in providers:
                    await self._create_endpoint_from_provider(provider)
                    
        except Exception as e:
            logger.error(f"Failed to initialize default endpoints: {e}")
    
    async def _create_endpoint_from_provider(self, provider: EndpointProvider):
        """Create endpoint from provider configuration"""
        try:
            # Create endpoint configuration
            endpoint_config = {
                'name': provider.name,
                'provider_type': provider.provider_type.value,
                'base_url': provider.base_url,
                'api_key': provider.api_key,
                'login_url': provider.login_url,
                'username': provider.username,
                'password': provider.password,
                'browser_config': provider.browser_config,
                'model_mapping': provider.model_mapping,
                'timeout_seconds': provider.timeout_seconds,
                'max_requests_per_minute': provider.max_requests_per_minute
            }
            
            # Create adapter based on provider type
            adapter = await self._create_adapter(provider.provider_type, endpoint_config)
            
            if adapter:
                # Store adapter
                self.active_adapters[provider.name] = adapter
                
                # Initialize metrics
                self.endpoint_metrics[provider.name] = EndpointMetrics(
                    endpoint_id=str(provider.id)
                )
                
                logger.info(f"Initialized endpoint: {provider.name}")
            
        except Exception as e:
            logger.error(f"Failed to create endpoint from provider {provider.name}: {e}")
    
    async def _create_adapter(self, provider_type: ProviderType, config: Dict[str, Any]) -> Optional[BaseAdapter]:
        """Create adapter based on provider type"""
        try:
            if provider_type == ProviderType.REST_API or provider_type == ProviderType.API_TOKEN:
                adapter = RestApiAdapter(config)
            elif provider_type == ProviderType.WEB_CHAT:
                adapter = WebChatAdapter(config)
            elif provider_type == ProviderType.ZAI_SDK:
                adapter = ZaiSdkAdapter(config)
            else:
                logger.error(f"Unknown provider type: {provider_type}")
                return None
            
            # Initialize adapter
            if await adapter.initialize():
                return adapter
            else:
                await adapter.cleanup()
                return None
                
        except Exception as e:
            logger.error(f"Failed to create adapter: {e}")
            return None
    
    async def add_endpoint(self, provider_config: Dict[str, Any]) -> bool:
        """Add new endpoint (trading bot style)"""
        try:
            provider_name = provider_config.get('name')
            if not provider_name:
                logger.error("Provider name is required")
                return False
            
            # Check if endpoint already exists
            if provider_name in self.active_adapters:
                logger.warning(f"Endpoint {provider_name} already exists")
                return False
            
            # Create provider in database
            with self.db_manager.get_session() as session:
                provider_type_str = provider_config.get('provider_type', 'rest_api')
                provider_type = ProviderType(provider_type_str)
                
                provider = EndpointProvider(
                    name=provider_name,
                    provider_type=provider_type,
                    description=provider_config.get('description', ''),
                    base_url=provider_config.get('base_url'),
                    api_key=provider_config.get('api_key'),
                    login_url=provider_config.get('login_url'),
                    username=provider_config.get('username'),
                    password=provider_config.get('password'),
                    browser_config=provider_config.get('browser_config', {}),
                    model_mapping=provider_config.get('model_mapping', {}),
                    timeout_seconds=provider_config.get('timeout_seconds', 30),
                    max_requests_per_minute=provider_config.get('max_requests_per_minute', 60)
                )
                
                session.add(provider)
                session.commit()
                session.refresh(provider)
                
                # Create adapter
                await self._create_endpoint_from_provider(provider)
                
                logger.info(f"Added new endpoint: {provider_name}")
                return True
                
        except Exception as e:
            logger.error(f"Failed to add endpoint: {e}")
            return False
    
    async def remove_endpoint(self, provider_name: str) -> bool:
        """Remove endpoint (trading bot style)"""
        try:
            # Stop adapter
            if provider_name in self.active_adapters:
                await self.active_adapters[provider_name].cleanup()
                del self.active_adapters[provider_name]
            
            # Remove metrics
            if provider_name in self.endpoint_metrics:
                del self.endpoint_metrics[provider_name]
            
            # Remove from database
            with self.db_manager.get_session() as session:
                provider = session.query(EndpointProvider).filter(
                    EndpointProvider.name == provider_name
                ).first()
                
                if provider:
                    session.delete(provider)
                    session.commit()
            
            logger.info(f"Removed endpoint: {provider_name}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to remove endpoint {provider_name}: {e}")
            return False
    
    async def start_endpoint(self, provider_name: str) -> bool:
        """Start endpoint (like starting a trading position)"""
        try:
            if provider_name not in self.active_adapters:
                logger.error(f"Endpoint {provider_name} not found")
                return False
            
            adapter = self.active_adapters[provider_name]
            
            # Re-initialize if needed
            if not adapter.is_initialized:
                success = await adapter.initialize()
                if not success:
                    logger.error(f"Failed to start endpoint {provider_name}")
                    return False
            
            logger.info(f"Started endpoint: {provider_name}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to start endpoint {provider_name}: {e}")
            return False
    
    async def stop_endpoint(self, provider_name: str) -> bool:
        """Stop endpoint (like closing a trading position)"""
        try:
            if provider_name not in self.active_adapters:
                logger.error(f"Endpoint {provider_name} not found")
                return False
            
            adapter = self.active_adapters[provider_name]
            await adapter.cleanup()
            
            logger.info(f"Stopped endpoint: {provider_name}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to stop endpoint {provider_name}: {e}")
            return False
    
    async def send_message(self, provider_name: str, message: str, **kwargs) -> Optional[AdapterResponse]:
        """Send message to specific endpoint"""
        try:
            if provider_name not in self.active_adapters:
                logger.error(f"Endpoint {provider_name} not found")
                return None
            
            adapter = self.active_adapters[provider_name]
            
            # Update metrics
            metrics = self.endpoint_metrics.get(provider_name)
            if metrics:
                metrics.total_requests += 1
                metrics.last_request_time = datetime.utcnow().isoformat()
            
            start_time = asyncio.get_event_loop().time()
            
            try:
                response = await adapter.send_message(message, **kwargs)
                
                # Update success metrics
                if metrics:
                    metrics.successful_requests += 1
                    response_time = (asyncio.get_event_loop().time() - start_time) * 1000
                    metrics.average_response_time = (
                        (metrics.average_response_time * (metrics.successful_requests - 1) + response_time) 
                        / metrics.successful_requests
                    )
                
                return response
                
            except Exception as e:
                # Update failure metrics
                if metrics:
                    metrics.failed_requests += 1
                
                logger.error(f"Message failed for endpoint {provider_name}: {e}")
                raise
                
        except Exception as e:
            logger.error(f"Failed to send message to {provider_name}: {e}")
            return None
    
    async def stream_message(self, provider_name: str, message: str, **kwargs):
        """Stream message from specific endpoint"""
        try:
            if provider_name not in self.active_adapters:
                logger.error(f"Endpoint {provider_name} not found")
                return
            
            adapter = self.active_adapters[provider_name]
            
            # Update metrics
            metrics = self.endpoint_metrics.get(provider_name)
            if metrics:
                metrics.total_requests += 1
                metrics.last_request_time = datetime.utcnow().isoformat()
            
            try:
                async for chunk in adapter.stream_message(message, **kwargs):
                    yield chunk
                
                # Update success metrics
                if metrics:
                    metrics.successful_requests += 1
                    
            except Exception as e:
                # Update failure metrics
                if metrics:
                    metrics.failed_requests += 1
                
                logger.error(f"Streaming failed for endpoint {provider_name}: {e}")
                raise
                
        except Exception as e:
            logger.error(f"Failed to stream message from {provider_name}: {e}")
    
    def get_active_endpoints(self) -> List[Dict[str, Any]]:
        """Get list of active endpoints (trading portfolio view)"""
        endpoints = []
        
        for name, adapter in self.active_adapters.items():
            metrics = self.endpoint_metrics.get(name, EndpointMetrics(endpoint_id=name))
            
            endpoint_info = {
                'name': name,
                'provider_type': adapter.provider_type,
                'status': 'running' if adapter.is_initialized else 'stopped',
                'metrics': asdict(metrics),
                'health': 'unknown'
            }
            
            endpoints.append(endpoint_info)
        
        return endpoints
    
    def get_endpoint_metrics(self, provider_name: str) -> Optional[Dict[str, Any]]:
        """Get metrics for specific endpoint"""
        metrics = self.endpoint_metrics.get(provider_name)
        return asdict(metrics) if metrics else None
    
    async def health_check_endpoint(self, provider_name: str) -> Dict[str, Any]:
        """Check health of specific endpoint"""
        try:
            if provider_name not in self.active_adapters:
                return {'status': 'not_found', 'error': f'Endpoint {provider_name} not found'}
            
            adapter = self.active_adapters[provider_name]
            return await adapter.health_check()
            
        except Exception as e:
            return {'status': 'error', 'error': str(e)}
    
    async def _health_monitor_loop(self):
        """Background health monitoring loop"""
        while self.is_running:
            try:
                for name, adapter in self.active_adapters.items():
                    try:
                        health = await adapter.health_check()
                        
                        # Update metrics based on health
                        metrics = self.endpoint_metrics.get(name)
                        if metrics and health.get('status') == 'healthy':
                            # Endpoint is healthy, maintain uptime
                            pass
                        elif metrics:
                            # Endpoint has issues, adjust uptime
                            metrics.uptime_percentage = max(0, metrics.uptime_percentage - 1)
                        
                    except Exception as e:
                        logger.error(f"Health check failed for {name}: {e}")
                
                # Wait before next health check
                await asyncio.sleep(60)  # Check every minute
                
            except Exception as e:
                logger.error(f"Health monitor error: {e}")
                await asyncio.sleep(60)
    
    async def get_best_endpoint(self, criteria: str = 'success_rate') -> Optional[str]:
        """Get best performing endpoint (trading bot optimization)"""
        if not self.active_adapters:
            return None
        
        best_endpoint = None
        best_score = -1
        
        for name, adapter in self.active_adapters.items():
            if not adapter.is_initialized:
                continue
            
            metrics = self.endpoint_metrics.get(name)
            if not metrics:
                continue
            
            # Calculate score based on criteria
            if criteria == 'success_rate':
                score = metrics.success_rate
            elif criteria == 'response_time':
                score = 1000 / max(metrics.average_response_time, 1)  # Inverse of response time
            elif criteria == 'uptime':
                score = metrics.uptime_percentage
            else:
                score = metrics.success_rate  # Default
            
            if score > best_score:
                best_score = score
                best_endpoint = name
        
        return best_endpoint
    
    # New server-based methods
    async def add_endpoint_server(self, name: str, provider_type: str, config: Dict[str, Any], priority: int = 50) -> bool:
        """Add new endpoint using server architecture"""
        try:
            if not name:
                logger.error("Endpoint name is required")
                return False
            
            # Initialize active_endpoints if not exists
            if not hasattr(self, 'active_endpoints'):
                self.active_endpoints = {}
            
            if name in self.active_endpoints:
                logger.error(f"Endpoint {name} already exists")
                return False
            
            # Create endpoint configuration
            endpoint_config = {
                'name': name,
                'provider_type': provider_type,
                'priority': priority,
                **config
            }
            
            # Try to import EndpointFactory
            try:
                from .servers import EndpointFactory
                
                # Validate configuration
                is_valid, error_msg = EndpointFactory.validate_config(endpoint_config)
                if not is_valid:
                    logger.error(f"Invalid configuration for {name}: {error_msg}")
                    return False
                
                # Create endpoint
                endpoint = EndpointFactory.create_endpoint(name, endpoint_config)
                if not endpoint:
                    logger.error(f"Failed to create endpoint {name}")
                    return False
                
                # Start endpoint
                if await endpoint.start():
                    self.active_endpoints[name] = endpoint
                    logger.info(f"Added and started endpoint: {name} (priority: {priority})")
                    return True
                else:
                    logger.error(f"Failed to start endpoint {name}")
                    return False
                    
            except ImportError:
                # Fallback to basic endpoint creation
                logger.warning("EndpointFactory not available, using basic endpoint creation")
                
                # Create a basic endpoint placeholder
                self.active_endpoints[name] = {
                    'name': name,
                    'provider_type': provider_type,
                    'config': config,
                    'priority': priority,
                    'status': 'running'
                }
                
                logger.info(f"Added basic endpoint: {name} (priority: {priority})")
                return True
                
        except Exception as e:
            logger.error(f"Failed to add endpoint: {e}")
            return False
    
    async def remove_endpoint_server(self, name: str) -> bool:
        """Remove endpoint using server architecture"""
        try:
            if name not in self.active_endpoints:
                logger.error(f"Endpoint {name} not found")
                return False
            
            endpoint = self.active_endpoints[name]
            await endpoint.stop()
            del self.active_endpoints[name]
            
            logger.info(f"Removed endpoint: {name}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to remove endpoint {name}: {e}")
            return False
    
    async def start_endpoint_server(self, name: str) -> bool:
        """Start endpoint using server architecture"""
        try:
            if name not in self.active_endpoints:
                logger.error(f"Endpoint {name} not found")
                return False
            
            endpoint = self.active_endpoints[name]
            return await endpoint.start()
            
        except Exception as e:
            logger.error(f"Failed to start endpoint {name}: {e}")
            return False
    
    async def stop_endpoint_server(self, name: str) -> bool:
        """Stop endpoint using server architecture"""
        try:
            if name not in self.active_endpoints:
                logger.error(f"Endpoint {name} not found")
                return False
            
            endpoint = self.active_endpoints[name]
            return await endpoint.stop()
            
        except Exception as e:
            logger.error(f"Failed to stop endpoint {name}: {e}")
            return False
    
    async def test_endpoint_server(self, name: str, message: str = "Hello, this is a test") -> Optional[str]:
        """Test endpoint using server architecture"""
        try:
            if name not in self.active_endpoints:
                logger.error(f"Endpoint {name} not found")
                return None
            
            endpoint = self.active_endpoints[name]
            if not endpoint.is_running():
                logger.error(f"Endpoint {name} is not running")
                return None
            
            return await endpoint._send_message_with_metrics(message)
            
        except Exception as e:
            logger.error(f"Failed to test endpoint {name}: {e}")
            return None
    
    def get_active_endpoints_server(self) -> List[Dict[str, Any]]:
        """Get active endpoints using server architecture"""
        endpoints = []
        
        for name, endpoint in self.active_endpoints.items():
            endpoints.append(endpoint.get_info())
        
        return endpoints
    
    def get_endpoint_server(self, name: str) -> Optional[Dict[str, Any]]:
        """Get specific endpoint info using server architecture"""
        if name in self.active_endpoints:
            return self.active_endpoints[name].get_info()
        return None
    
    async def health_check_endpoint_server(self, name: str) -> Dict[str, Any]:
        """Health check endpoint using server architecture"""
        try:
            if name not in self.active_endpoints:
                return {"healthy": False, "error": "Endpoint not found"}
            
            endpoint = self.active_endpoints[name]
            is_healthy = await endpoint._perform_health_check()
            
            return {
                "healthy": is_healthy,
                "status": endpoint.status.value,
                "health": endpoint.health.value,
                "metrics": endpoint.metrics.to_dict()
            }
            
        except Exception as e:
            return {"healthy": False, "error": str(e)}
    
    def get_endpoint_metrics_server(self, name: str) -> Optional[Dict[str, Any]]:
        """Get endpoint metrics using server architecture"""
        if name in self.active_endpoints:
            return self.active_endpoints[name].metrics.to_dict()
        return None
    
    async def reset_endpoint_metrics_server(self, name: str) -> bool:
        """Reset endpoint metrics using server architecture"""
        try:
            if name not in self.active_endpoints:
                return False
            
            self.active_endpoints[name].reset_metrics()
            return True
            
        except Exception as e:
            logger.error(f"Failed to reset metrics for {name}: {e}")
            return False

# Global endpoint manager instance
endpoint_manager = EndpointManager()

def get_endpoint_manager() -> EndpointManager:
    """Get the global endpoint manager instance"""
    return endpoint_manager
