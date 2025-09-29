#!/usr/bin/env python3
"""
Load Balancer for AI Provider Services
Implements multiple load balancing strategies for routing requests
"""

import asyncio
import logging
import random
import time
from enum import Enum
from typing import Dict, List, Optional, Any
from collections import defaultdict, deque

from backend.registry.service_registry import service_registry, ServiceStatus

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class LoadBalancingStrategy(Enum):
    ROUND_ROBIN = "round_robin"
    LEAST_CONNECTIONS = "least_connections"
    RESPONSE_TIME = "response_time"
    RANDOM = "random"
    WEIGHTED_ROUND_ROBIN = "weighted_round_robin"
    HEALTH_BASED = "health_based"
    MODEL_SPECIFIC = "model_specific"

class LoadBalancer:
    """Intelligent load balancer for AI provider services"""
    
    def __init__(self):
        self.service_registry = service_registry
        self.default_strategy = LoadBalancingStrategy.ROUND_ROBIN
        
        # Round robin state
        self.round_robin_index = 0
        
        # Connection tracking
        self.active_connections: Dict[str, int] = defaultdict(int)
        
        # Response time tracking
        self.response_times: Dict[str, deque] = defaultdict(lambda: deque(maxlen=10))
        
        # Request history for analytics
        self.request_history: List[Dict[str, Any]] = []
        self.max_history = 1000
        
        # Weights for weighted round robin
        self.service_weights: Dict[str, int] = {}
        self._initialize_weights()
    
    def _initialize_weights(self):
        """Initialize service weights based on capabilities"""
        for name, service in self.service_registry.get_all_services().items():
            # Base weight
            weight = 1
            
            # Increase weight for services with more models
            weight += len(service.models)
            
            # Increase weight for certain service types
            if service.service_type.value == "go":
                weight += 2  # Go services might be faster
            elif service.service_type.value == "python":
                weight += 1
            
            self.service_weights[name] = weight
    
    async def select_provider(
        self,
        model: str = "gpt-3.5-turbo",
        strategy: Optional[LoadBalancingStrategy] = None,
        exclude_services: List[str] = None
    ) -> Optional[str]:
        """Select the best provider based on strategy"""
        
        if strategy is None:
            strategy = self.default_strategy
        
        if exclude_services is None:
            exclude_services = []
        
        # Get healthy services that support the model
        available_services = []
        for service in self.service_registry.get_services_by_model(model):
            if service.name not in exclude_services:
                available_services.append(service)
        
        if not available_services:
            logger.warning(f"No healthy services available for model {model}")
            return None
        
        # Apply load balancing strategy
        selected_service = None
        
        if strategy == LoadBalancingStrategy.ROUND_ROBIN:
            selected_service = self._round_robin_select(available_services)
        
        elif strategy == LoadBalancingStrategy.LEAST_CONNECTIONS:
            selected_service = self._least_connections_select(available_services)
        
        elif strategy == LoadBalancingStrategy.RESPONSE_TIME:
            selected_service = self._response_time_select(available_services)
        
        elif strategy == LoadBalancingStrategy.RANDOM:
            selected_service = self._random_select(available_services)
        
        elif strategy == LoadBalancingStrategy.WEIGHTED_ROUND_ROBIN:
            selected_service = self._weighted_round_robin_select(available_services)
        
        elif strategy == LoadBalancingStrategy.HEALTH_BASED:
            selected_service = self._health_based_select(available_services)
        
        elif strategy == LoadBalancingStrategy.MODEL_SPECIFIC:
            selected_service = self._model_specific_select(available_services, model)
        
        if selected_service:
            # Record the selection
            self._record_selection(selected_service.name, model, strategy)
            logger.info(f"Selected provider: {selected_service.name} for model {model} using {strategy.value}")
            return selected_service.name
        
        return None
    
    def _round_robin_select(self, services: List[Any]) -> Optional[Any]:
        """Round robin selection"""
        if not services:
            return None
        
        service = services[self.round_robin_index % len(services)]
        self.round_robin_index = (self.round_robin_index + 1) % len(services)
        return service
    
    def _least_connections_select(self, services: List[Any]) -> Optional[Any]:
        """Select service with least active connections"""
        if not services:
            return None
        
        min_connections = float('inf')
        selected_service = None
        
        for service in services:
            connections = self.active_connections[service.name]
            if connections < min_connections:
                min_connections = connections
                selected_service = service
        
        return selected_service
    
    def _response_time_select(self, services: List[Any]) -> Optional[Any]:
        """Select service with best average response time"""
        if not services:
            return None
        
        best_time = float('inf')
        selected_service = None
        
        for service in services:
            # Use recent response time or service's last response time
            if service.name in self.response_times and self.response_times[service.name]:
                avg_time = sum(self.response_times[service.name]) / len(self.response_times[service.name])
            else:
                avg_time = service.response_time if service.response_time > 0 else 1.0
            
            if avg_time < best_time:
                best_time = avg_time
                selected_service = service
        
        return selected_service
    
    def _random_select(self, services: List[Any]) -> Optional[Any]:
        """Random selection"""
        if not services:
            return None
        
        return random.choice(services)
    
    def _weighted_round_robin_select(self, services: List[Any]) -> Optional[Any]:
        """Weighted round robin based on service capabilities"""
        if not services:
            return None
        
        # Create weighted list
        weighted_services = []
        for service in services:
            weight = self.service_weights.get(service.name, 1)
            weighted_services.extend([service] * weight)
        
        if not weighted_services:
            return services[0]
        
        service = weighted_services[self.round_robin_index % len(weighted_services)]
        self.round_robin_index = (self.round_robin_index + 1) % len(weighted_services)
        return service
    
    def _health_based_select(self, services: List[Any]) -> Optional[Any]:
        """Select based on health metrics (error count, uptime)"""
        if not services:
            return None
        
        best_score = -1
        selected_service = None
        
        for service in services:
            # Calculate health score (higher is better)
            score = 100  # Base score
            
            # Penalize for errors
            score -= service.error_count * 10
            
            # Reward for uptime
            if service.uptime_start:
                uptime_hours = (time.time() - service.uptime_start) / 3600
                score += min(uptime_hours, 24)  # Max 24 points for uptime
            
            # Reward for good response time
            if service.response_time > 0:
                score += max(0, 10 - service.response_time)  # Better response time = higher score
            
            if score > best_score:
                best_score = score
                selected_service = service
        
        return selected_service
    
    def _model_specific_select(self, services: List[Any], model: str) -> Optional[Any]:
        """Select based on model-specific optimization"""
        if not services:
            return None
        
        # Prefer services that specialize in the requested model
        specialized_services = []
        general_services = []
        
        for service in services:
            if len(service.models) <= 2 and model in service.models:
                # Service with few models that supports this one (specialized)
                specialized_services.append(service)
            else:
                general_services.append(service)
        
        # Prefer specialized services
        if specialized_services:
            return self._response_time_select(specialized_services)
        else:
            return self._response_time_select(general_services)
    
    def _record_selection(self, service_name: str, model: str, strategy: LoadBalancingStrategy):
        """Record provider selection for analytics"""
        record = {
            "timestamp": time.time(),
            "service": service_name,
            "model": model,
            "strategy": strategy.value
        }
        
        self.request_history.append(record)
        
        # Trim history if too long
        if len(self.request_history) > self.max_history:
            self.request_history = self.request_history[-self.max_history:]
    
    def increment_connections(self, service_name: str):
        """Increment active connection count"""
        self.active_connections[service_name] += 1
    
    def decrement_connections(self, service_name: str):
        """Decrement active connection count"""
        if self.active_connections[service_name] > 0:
            self.active_connections[service_name] -= 1
    
    def record_response_time(self, service_name: str, response_time: float):
        """Record response time for a service"""
        self.response_times[service_name].append(response_time)
    
    def get_load_balancing_stats(self) -> Dict[str, Any]:
        """Get load balancing statistics"""
        # Service usage stats
        service_usage = defaultdict(int)
        model_usage = defaultdict(int)
        strategy_usage = defaultdict(int)
        
        for record in self.request_history:
            service_usage[record["service"]] += 1
            model_usage[record["model"]] += 1
            strategy_usage[record["strategy"]] += 1
        
        # Response time stats
        response_time_stats = {}
        for service_name, times in self.response_times.items():
            if times:
                response_time_stats[service_name] = {
                    "avg": sum(times) / len(times),
                    "min": min(times),
                    "max": max(times),
                    "count": len(times)
                }
        
        return {
            "total_requests": len(self.request_history),
            "service_usage": dict(service_usage),
            "model_usage": dict(model_usage),
            "strategy_usage": dict(strategy_usage),
            "active_connections": dict(self.active_connections),
            "response_time_stats": response_time_stats,
            "service_weights": self.service_weights,
            "current_strategy": self.default_strategy.value,
            "timestamp": time.time()
        }
    
    def reset_stats(self):
        """Reset all statistics"""
        self.request_history.clear()
        self.active_connections.clear()
        self.response_times.clear()
        self.round_robin_index = 0
        logger.info("Load balancer statistics reset")
    
    async def health_check_and_rebalance(self):
        """Periodic health check and rebalancing"""
        while True:
            try:
                # Update service weights based on current performance
                for name, service in self.service_registry.get_all_services().items():
                    base_weight = len(service.models) + 1
                    
                    # Adjust weight based on error count
                    if service.error_count > 5:
                        base_weight = max(1, base_weight - 2)
                    elif service.error_count == 0:
                        base_weight += 1
                    
                    # Adjust weight based on response time
                    if service.response_time > 0:
                        if service.response_time < 1.0:
                            base_weight += 1
                        elif service.response_time > 5.0:
                            base_weight = max(1, base_weight - 1)
                    
                    self.service_weights[name] = base_weight
                
                await asyncio.sleep(60)  # Rebalance every minute
                
            except Exception as e:
                logger.error(f"Health check and rebalance error: {e}")
                await asyncio.sleep(10)

# Global load balancer instance
load_balancer = LoadBalancer()

async def main():
    """Main function for testing"""
    logger.info("🚀 Load Balancer Test")
    
    # Test different strategies
    strategies = [
        LoadBalancingStrategy.ROUND_ROBIN,
        LoadBalancingStrategy.LEAST_CONNECTIONS,
        LoadBalancingStrategy.RESPONSE_TIME,
        LoadBalancingStrategy.RANDOM,
        LoadBalancingStrategy.HEALTH_BASED
    ]
    
    for strategy in strategies:
        logger.info(f"\nTesting {strategy.value}:")
        for i in range(3):
            provider = await load_balancer.select_provider(
                model="gpt-3.5-turbo",
                strategy=strategy
            )
            logger.info(f"  Request {i+1}: {provider}")
    
    # Print stats
    stats = load_balancer.get_load_balancing_stats()
    logger.info(f"\nLoad Balancing Stats: {stats}")

if __name__ == "__main__":
    asyncio.run(main())
