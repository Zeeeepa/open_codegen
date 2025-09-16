"""
Endpoint Registry - Central management system for AI endpoints.

Acts as the central hub for managing all endpoint instances, similar to a
trading bot's position manager. Handles registration, status tracking,
and lifecycle management of both REST API and web chat endpoints.
"""

import uuid
import asyncio
import logging
from typing import Dict, List, Optional, Set, Any
from datetime import datetime, timedelta
from collections import defaultdict

from ..config_manager.yaml_schema import EndpointConfig, EndpointType, YAMLConfigManager
from .endpoint_status import (
    EndpointStatus, HealthStatus, EndpointInstance, EndpointSummary, PerformanceMetrics
)

logger = logging.getLogger(__name__)


class EndpointRegistry:
    """
    Central registry for managing AI endpoints - trading bot style.
    
    Manages endpoints like a trading bot manages positions:
    - Register/deregister endpoints (like opening/closing positions)
    - Start/stop instances (like activating/deactivating strategies)
    - Monitor performance (like tracking P&L)
    - Auto-scale based on demand (like adjusting position sizes)
    """
    
    def __init__(self, config_manager: Optional[YAMLConfigManager] = None):
        self.config_manager = config_manager or YAMLConfigManager()
        
        # Core data structures - like trading bot's position tracking
        self.endpoints: Dict[str, EndpointConfig] = {}  # Endpoint configurations
        self.instances: Dict[str, EndpointInstance] = {}  # Active instances
        self.instance_groups: Dict[str, List[str]] = defaultdict(list)  # Instances per endpoint
        
        # Status tracking - like portfolio monitoring
        self.summaries: Dict[str, EndpointSummary] = {}  # Endpoint summaries
        self.global_metrics: Dict[str, Any] = {}  # Overall system metrics
        
        # Management state
        self.is_running = False
        self.monitoring_task: Optional[asyncio.Task] = None
        self.last_cleanup: datetime = datetime.utcnow()
        
        # Event callbacks - like trading signals
        self.event_callbacks: Dict[str, List[callable]] = defaultdict(list)
        
        logger.info("Endpoint Registry initialized")
    
    async def start(self):
        """Start the endpoint registry and monitoring systems."""
        if self.is_running:
            logger.warning("Registry already running")
            return
        
        self.is_running = True
        
        # Load existing configurations
        await self.load_configurations()
        
        # Start monitoring task
        self.monitoring_task = asyncio.create_task(self._monitoring_loop())
        
        logger.info("Endpoint Registry started")
    
    async def stop(self):
        """Stop the registry and all managed endpoints."""
        if not self.is_running:
            return
        
        self.is_running = False
        
        # Stop monitoring
        if self.monitoring_task:
            self.monitoring_task.cancel()
            try:
                await self.monitoring_task
            except asyncio.CancelledError:
                pass
        
        # Stop all instances
        await self.stop_all_instances()
        
        logger.info("Endpoint Registry stopped")
    
    async def load_configurations(self):
        """Load endpoint configurations from YAML files."""
        try:
            configs = self.config_manager.load_all_configs()
            
            for name, config in configs.items():
                await self.register_endpoint(config)
            
            logger.info(f"Loaded {len(configs)} endpoint configurations")
            
        except Exception as e:
            logger.error(f"Failed to load configurations: {e}")
    
    async def register_endpoint(self, config: EndpointConfig) -> bool:
        """
        Register a new endpoint - like adding a new trading strategy.
        
        Args:
            config: Endpoint configuration
            
        Returns:
            bool: True if registered successfully
        """
        try:
            # Validate configuration
            errors = self.config_manager.validate_config(config)
            if errors:
                logger.error(f"Invalid configuration for {config.name}: {errors}")
                return False
            
            # Register the endpoint
            self.endpoints[config.name] = config
            
            # Initialize summary
            self.summaries[config.name] = EndpointSummary(
                endpoint_name=config.name,
                model_name=config.model_name,
                endpoint_type=config.endpoint_type.value,
                enabled=config.enabled,
                priority=config.priority,
                max_instances=config.scaling.max_instances
            )
            
            # Emit registration event
            await self._emit_event("endpoint_registered", {
                "endpoint_name": config.name,
                "endpoint_type": config.endpoint_type.value,
                "model_name": config.model_name
            })
            
            logger.info(f"Registered endpoint: {config.name} ({config.endpoint_type.value})")
            return True
            
        except Exception as e:
            logger.error(f"Failed to register endpoint {config.name}: {e}")
            return False
    
    async def unregister_endpoint(self, endpoint_name: str) -> bool:
        """
        Unregister an endpoint - like closing a trading position.
        
        Args:
            endpoint_name: Name of endpoint to unregister
            
        Returns:
            bool: True if unregistered successfully
        """
        try:
            if endpoint_name not in self.endpoints:
                logger.warning(f"Endpoint {endpoint_name} not found")
                return False
            
            # Stop all instances first
            await self.stop_endpoint_instances(endpoint_name)
            
            # Remove from registry
            del self.endpoints[endpoint_name]
            if endpoint_name in self.summaries:
                del self.summaries[endpoint_name]
            if endpoint_name in self.instance_groups:
                del self.instance_groups[endpoint_name]
            
            # Emit unregistration event
            await self._emit_event("endpoint_unregistered", {
                "endpoint_name": endpoint_name
            })
            
            logger.info(f"Unregistered endpoint: {endpoint_name}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to unregister endpoint {endpoint_name}: {e}")
            return False
    
    async def start_endpoint_instance(self, endpoint_name: str, instance_count: int = 1) -> List[str]:
        """
        Start instances for an endpoint - like opening trading positions.
        
        Args:
            endpoint_name: Name of endpoint
            instance_count: Number of instances to start
            
        Returns:
            List[str]: Instance IDs of started instances
        """
        if endpoint_name not in self.endpoints:
            logger.error(f"Endpoint {endpoint_name} not registered")
            return []
        
        config = self.endpoints[endpoint_name]
        if not config.enabled:
            logger.warning(f"Endpoint {endpoint_name} is disabled")
            return []
        
        started_instances = []
        
        try:
            for i in range(instance_count):
                # Check if we can start more instances
                current_instances = len(self.instance_groups[endpoint_name])
                if current_instances >= config.scaling.max_instances:
                    logger.warning(f"Max instances reached for {endpoint_name}")
                    break
                
                # Create new instance
                instance_id = f"{endpoint_name}-{uuid.uuid4().hex[:8]}"
                instance = EndpointInstance(
                    instance_id=instance_id,
                    endpoint_name=endpoint_name,
                    model_name=config.model_name,
                    priority=config.priority,
                    config_hash=str(hash(str(config.to_dict())))
                )
                
                # Add to registry
                self.instances[instance_id] = instance
                self.instance_groups[endpoint_name].append(instance_id)
                
                # Update status to starting
                instance.update_status(EndpointStatus.STARTING, "Instance created")
                
                # Start the actual endpoint (this would be implemented by specific handlers)
                success = await self._start_instance_handler(instance, config)
                
                if success:
                    instance.update_status(EndpointStatus.RUNNING, "Instance started successfully")
                    started_instances.append(instance_id)
                    
                    # Emit start event
                    await self._emit_event("instance_started", {
                        "instance_id": instance_id,
                        "endpoint_name": endpoint_name,
                        "model_name": config.model_name
                    })
                else:
                    instance.update_status(EndpointStatus.ERROR, "Failed to start instance")
                    instance.record_error("Instance startup failed")
            
            logger.info(f"Started {len(started_instances)} instances for {endpoint_name}")
            return started_instances
            
        except Exception as e:
            logger.error(f"Failed to start instances for {endpoint_name}: {e}")
            return started_instances
    
    async def stop_endpoint_instances(self, endpoint_name: str, instance_count: Optional[int] = None) -> List[str]:
        """
        Stop instances for an endpoint - like closing trading positions.
        
        Args:
            endpoint_name: Name of endpoint
            instance_count: Number of instances to stop (None = all)
            
        Returns:
            List[str]: Instance IDs of stopped instances
        """
        if endpoint_name not in self.instance_groups:
            logger.warning(f"No instances found for {endpoint_name}")
            return []
        
        instance_ids = self.instance_groups[endpoint_name].copy()
        if instance_count is not None:
            instance_ids = instance_ids[:instance_count]
        
        stopped_instances = []
        
        try:
            for instance_id in instance_ids:
                if instance_id in self.instances:
                    instance = self.instances[instance_id]
                    
                    # Update status to stopping
                    instance.update_status(EndpointStatus.STOPPING, "Stopping instance")
                    
                    # Stop the actual endpoint
                    success = await self._stop_instance_handler(instance)
                    
                    if success:
                        instance.update_status(EndpointStatus.STOPPED, "Instance stopped successfully")
                    else:
                        instance.update_status(EndpointStatus.ERROR, "Failed to stop instance gracefully")
                    
                    # Remove from registry
                    del self.instances[instance_id]
                    self.instance_groups[endpoint_name].remove(instance_id)
                    stopped_instances.append(instance_id)
                    
                    # Emit stop event
                    await self._emit_event("instance_stopped", {
                        "instance_id": instance_id,
                        "endpoint_name": endpoint_name
                    })
            
            logger.info(f"Stopped {len(stopped_instances)} instances for {endpoint_name}")
            return stopped_instances
            
        except Exception as e:
            logger.error(f"Failed to stop instances for {endpoint_name}: {e}")
            return stopped_instances
    
    async def stop_all_instances(self):
        """Stop all running instances - like closing all positions."""
        for endpoint_name in list(self.instance_groups.keys()):
            await self.stop_endpoint_instances(endpoint_name)
    
    def get_endpoint_summary(self, endpoint_name: str) -> Optional[EndpointSummary]:
        """Get summary for a specific endpoint."""
        if endpoint_name not in self.summaries:
            return None
        
        # Update summary with current instances
        instances = [
            self.instances[instance_id] 
            for instance_id in self.instance_groups.get(endpoint_name, [])
            if instance_id in self.instances
        ]
        
        summary = self.summaries[endpoint_name]
        summary.update_from_instances(instances)
        
        return summary
    
    def get_all_summaries(self) -> Dict[str, EndpointSummary]:
        """Get summaries for all endpoints."""
        summaries = {}
        for endpoint_name in self.endpoints.keys():
            summary = self.get_endpoint_summary(endpoint_name)
            if summary:
                summaries[endpoint_name] = summary
        return summaries
    
    def get_instance(self, instance_id: str) -> Optional[EndpointInstance]:
        """Get specific instance by ID."""
        return self.instances.get(instance_id)
    
    def get_endpoint_instances(self, endpoint_name: str) -> List[EndpointInstance]:
        """Get all instances for an endpoint."""
        instance_ids = self.instance_groups.get(endpoint_name, [])
        return [
            self.instances[instance_id] 
            for instance_id in instance_ids 
            if instance_id in self.instances
        ]
    
    def get_healthy_instances(self, endpoint_name: str) -> List[EndpointInstance]:
        """Get healthy instances for an endpoint."""
        instances = self.get_endpoint_instances(endpoint_name)
        return [instance for instance in instances if instance.is_healthy()]
    
    def get_global_metrics(self) -> Dict[str, Any]:
        """Get global system metrics - like portfolio overview."""
        total_endpoints = len(self.endpoints)
        total_instances = len(self.instances)
        running_instances = sum(1 for i in self.instances.values() if i.status == EndpointStatus.RUNNING)
        healthy_instances = sum(1 for i in self.instances.values() if i.is_healthy())
        
        # Calculate aggregate metrics
        total_requests = sum(i.metrics.total_requests for i in self.instances.values())
        avg_success_rate = 0.0
        avg_response_time = 0.0
        avg_profit_score = 0.0
        
        if self.instances:
            total_weight = sum(max(1, i.metrics.total_requests) for i in self.instances.values())
            if total_weight > 0:
                avg_success_rate = sum(
                    i.metrics.success_rate * max(1, i.metrics.total_requests)
                    for i in self.instances.values()
                ) / total_weight
                
                avg_response_time = sum(
                    i.metrics.avg_response_time_ms * max(1, i.metrics.total_requests)
                    for i in self.instances.values()
                ) / total_weight
                
                avg_profit_score = sum(
                    i.metrics.profit_score * max(1, i.metrics.total_requests)
                    for i in self.instances.values()
                ) / total_weight
        
        return {
            "endpoints": {
                "total": total_endpoints,
                "enabled": sum(1 for e in self.endpoints.values() if e.enabled),
                "disabled": sum(1 for e in self.endpoints.values() if not e.enabled)
            },
            "instances": {
                "total": total_instances,
                "running": running_instances,
                "healthy": healthy_instances,
                "unhealthy": total_instances - healthy_instances
            },
            "performance": {
                "total_requests": total_requests,
                "avg_success_rate": avg_success_rate,
                "avg_response_time_ms": avg_response_time,
                "avg_profit_score": avg_profit_score
            },
            "system": {
                "uptime_seconds": (datetime.utcnow() - self.last_cleanup).total_seconds(),
                "last_updated": datetime.utcnow().isoformat()
            }
        }
    
    async def auto_scale_endpoint(self, endpoint_name: str) -> bool:
        """
        Auto-scale an endpoint based on demand - like adjusting position size.
        
        Args:
            endpoint_name: Name of endpoint to scale
            
        Returns:
            bool: True if scaling action was taken
        """
        if endpoint_name not in self.endpoints:
            return False
        
        config = self.endpoints[endpoint_name]
        if not config.scaling.enabled:
            return False
        
        instances = self.get_endpoint_instances(endpoint_name)
        healthy_instances = [i for i in instances if i.is_healthy()]
        
        current_count = len(instances)
        healthy_count = len(healthy_instances)
        
        # Calculate load metrics
        if healthy_instances:
            avg_requests_per_minute = sum(i.metrics.requests_per_minute for i in healthy_instances) / healthy_count
            avg_cpu_usage = sum(i.metrics.cpu_usage_percent for i in healthy_instances) / healthy_count
            
            # Scale up if high load
            if (avg_cpu_usage > config.scaling.scale_up_threshold * 100 or 
                avg_requests_per_minute > 50) and current_count < config.scaling.max_instances:
                
                await self.start_endpoint_instance(endpoint_name, 1)
                logger.info(f"Scaled up {endpoint_name}: {current_count} -> {current_count + 1}")
                return True
            
            # Scale down if low load
            elif (avg_cpu_usage < config.scaling.scale_down_threshold * 100 and 
                  avg_requests_per_minute < 10) and current_count > config.scaling.min_instances:
                
                await self.stop_endpoint_instances(endpoint_name, 1)
                logger.info(f"Scaled down {endpoint_name}: {current_count} -> {current_count - 1}")
                return True
        
        return False
    
    async def _monitoring_loop(self):
        """Background monitoring loop - like trading bot's market monitoring."""
        while self.is_running:
            try:
                # Update summaries
                for endpoint_name in self.endpoints.keys():
                    self.get_endpoint_summary(endpoint_name)
                
                # Auto-scale endpoints
                for endpoint_name in self.endpoints.keys():
                    if self.endpoints[endpoint_name].scaling.enabled:
                        await self.auto_scale_endpoint(endpoint_name)
                
                # Cleanup unhealthy instances
                await self._cleanup_unhealthy_instances()
                
                # Update global metrics
                self.global_metrics = self.get_global_metrics()
                
                # Wait before next monitoring cycle
                await asyncio.sleep(30)  # Monitor every 30 seconds
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}")
                await asyncio.sleep(10)
    
    async def _cleanup_unhealthy_instances(self):
        """Clean up unhealthy instances - like cutting losses."""
        current_time = datetime.utcnow()
        
        # Only cleanup every 5 minutes
        if (current_time - self.last_cleanup).total_seconds() < 300:
            return
        
        instances_to_remove = []
        
        for instance_id, instance in self.instances.items():
            # Remove instances that have been in error state for too long
            if (instance.status == EndpointStatus.ERROR and 
                instance.last_error_time and
                (current_time - instance.last_error_time).total_seconds() > 600):  # 10 minutes
                
                instances_to_remove.append(instance_id)
            
            # Remove instances with too many consecutive errors
            elif instance.consecutive_errors >= 10:
                instances_to_remove.append(instance_id)
        
        # Remove unhealthy instances
        for instance_id in instances_to_remove:
            instance = self.instances[instance_id]
            endpoint_name = instance.endpoint_name
            
            logger.warning(f"Removing unhealthy instance: {instance_id}")
            
            # Stop and remove
            await self._stop_instance_handler(instance)
            del self.instances[instance_id]
            if instance_id in self.instance_groups[endpoint_name]:
                self.instance_groups[endpoint_name].remove(instance_id)
        
        self.last_cleanup = current_time
    
    async def _start_instance_handler(self, instance: EndpointInstance, config: EndpointConfig) -> bool:
        """
        Start the actual endpoint instance - to be implemented by specific handlers.
        This is a placeholder that would be overridden by specific endpoint types.
        """
        # This would be implemented by specific endpoint handlers
        # For now, just simulate successful startup
        await asyncio.sleep(0.1)  # Simulate startup time
        return True
    
    async def _stop_instance_handler(self, instance: EndpointInstance) -> bool:
        """
        Stop the actual endpoint instance - to be implemented by specific handlers.
        This is a placeholder that would be overridden by specific endpoint types.
        """
        # This would be implemented by specific endpoint handlers
        # For now, just simulate successful shutdown
        await asyncio.sleep(0.1)  # Simulate shutdown time
        return True
    
    def add_event_callback(self, event_type: str, callback: callable):
        """Add event callback for monitoring endpoint events."""
        self.event_callbacks[event_type].append(callback)
    
    async def _emit_event(self, event_type: str, data: Dict[str, Any]):
        """Emit event to registered callbacks."""
        for callback in self.event_callbacks[event_type]:
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback(event_type, data)
                else:
                    callback(event_type, data)
            except Exception as e:
                logger.error(f"Error in event callback for {event_type}: {e}")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert registry state to dictionary for API responses."""
        return {
            "endpoints": {name: config.to_dict() for name, config in self.endpoints.items()},
            "summaries": {name: summary.to_dict() for name, summary in self.get_all_summaries().items()},
            "global_metrics": self.global_metrics,
            "is_running": self.is_running,
            "total_instances": len(self.instances)
        }
