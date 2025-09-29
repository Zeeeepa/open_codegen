#!/usr/bin/env python3
"""
Service Registry for AI Provider Management
Manages all 14 AI provider services with health monitoring and port allocation
"""

import asyncio
import json
import logging
import time
from dataclasses import dataclass, asdict
from typing import Dict, List, Optional, Any
from enum import Enum
import aiohttp
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ServiceStatus(Enum):
    STARTING = "starting"
    HEALTHY = "healthy"
    UNHEALTHY = "unhealthy"
    STOPPED = "stopped"
    ERROR = "error"

class ServiceType(Enum):
    PYTHON = "python"
    GO = "go"
    TYPESCRIPT = "typescript"
    NODE = "node"

@dataclass
class ServiceInfo:
    name: str
    port: int
    service_type: ServiceType
    status: ServiceStatus
    health_endpoint: str
    api_endpoint: str
    start_command: str
    working_directory: str
    last_health_check: float
    response_time: float
    error_count: int
    uptime_start: Optional[float] = None
    version: str = "1.0.0"
    models: List[str] = None
    
    def __post_init__(self):
        if self.models is None:
            self.models = ["gpt-3.5-turbo", "gpt-4"]

class ServiceRegistry:
    """Central registry for all AI provider services"""
    
    def __init__(self):
        self.services: Dict[str, ServiceInfo] = {}
        self.port_range_start = 8000
        self.port_range_end = 8020
        self.allocated_ports = set()
        self.health_check_interval = 30  # seconds
        self.health_check_timeout = 10   # seconds
        self._initialize_services()
    
    def _initialize_services(self):
        """Initialize all 14 AI provider services with correct entry points"""
        services_config = [
            # Services with actual code files
            {
                "name": "k2think2api3",
                "service_type": ServiceType.PYTHON,
                "start_command": "python k2think_proxy.py",
                "working_directory": "apis/k2think2api3",
                "models": ["k2-think", "gpt-4"]
            },
            {
                "name": "k2think2api2",
                "service_type": ServiceType.PYTHON,
                "start_command": "python main.py",
                "working_directory": "apis/k2think2api2",
                "models": ["k2-think", "gpt-3.5-turbo"]
            },
            {
                "name": "k2Think2Api",
                "service_type": ServiceType.PYTHON,
                "start_command": "python main.py",
                "working_directory": "apis/k2Think2Api",
                "models": ["k2-think"]
            },
            {
                "name": "grok2api",
                "service_type": ServiceType.PYTHON,
                "start_command": "python app.py",  # Uses app.py, not main.py
                "working_directory": "apis/grok2api",
                "models": ["grok-2", "grok-beta"]
            },
            {
                "name": "openai-proxy-z",
                "service_type": ServiceType.GO,  # This is a Go service, not Python
                "start_command": "go run main.go",
                "working_directory": "apis/OpenAI-Compatible-API-Proxy-for-Z",
                "models": ["glm-4.5", "glm-4.5v"]
            },
            {
                "name": "z-ai2api",
                "service_type": ServiceType.PYTHON,
                "start_command": "python app.py",  # Uses app.py, not npm start
                "working_directory": "apis/Z.ai2api",
                "models": ["glm-4.5"]
            },
            {
                "name": "z-ai2api-python",
                "service_type": ServiceType.PYTHON,
                "start_command": "python main.py",
                "working_directory": "apis/z.ai2api_python",
                "models": ["glm-4.5", "glm-4.5v", "longcat"]
            },
            {
                "name": "ztoapi",
                "service_type": ServiceType.GO,
                "start_command": "go run main.go",
                "working_directory": "apis/ZtoApi",
                "models": ["glm-4.5", "glm-4.5v"]
            },
            {
                "name": "talkai",
                "service_type": ServiceType.PYTHON,
                "start_command": "python main.py",
                "working_directory": "apis/talkai",
                "models": ["gpt-3.5-turbo", "gpt-4"]
            },
            {
                "name": "copilot-proxy",
                "service_type": ServiceType.PYTHON,
                "start_command": "python main.py",
                "working_directory": "apis/copilot-proxy",
                "models": ["gpt-4", "gpt-3.5-turbo", "copilot-codex"]
            },
            # Documentation-only repositories (disabled for now)
            # {
            #     "name": "qwen-api",
            #     "service_type": ServiceType.PYTHON,
            #     "start_command": "echo 'Documentation only'",
            #     "working_directory": "apis/qwen-api",
            #     "models": ["qwen-turbo", "qwen-plus", "qwen-max"]
            # },
            # {
            #     "name": "qwenchat2api", 
            #     "service_type": ServiceType.PYTHON,
            #     "start_command": "echo 'Documentation only'",
            #     "working_directory": "apis/qwenchat2api",
            #     "models": ["qwen-turbo", "qwen-plus"]
            # },
            # {
            #     "name": "zai-python-sdk",
            #     "service_type": ServiceType.PYTHON,
            #     "start_command": "echo 'SDK only'",
            #     "working_directory": "apis/zai-python-sdk",
            #     "models": ["glm-4.5", "glm-4.5v"]
            # },
            # {
            #     "name": "ztoapits",
            #     "service_type": ServiceType.TYPESCRIPT,
            #     "start_command": "echo 'No package.json'",
            #     "working_directory": "apis/ZtoApits",
            #     "models": ["glm-4.5", "glm-4.5v"]
            # }
        ]
        
        for i, config in enumerate(services_config):
            port = self.port_range_start + i
            self.allocated_ports.add(port)
            
            service = ServiceInfo(
                name=config["name"],
                port=port,
                service_type=config["service_type"],
                status=ServiceStatus.STOPPED,
                health_endpoint=f"http://localhost:{port}/health",
                api_endpoint=f"http://localhost:{port}/v1/chat/completions",
                start_command=config["start_command"],
                working_directory=config["working_directory"],
                last_health_check=0,
                response_time=0,
                error_count=0,
                models=config["models"]
            )
            
            self.services[config["name"]] = service
            logger.info(f"Registered service: {config['name']} on port {port}")
    
    def get_service(self, name: str) -> Optional[ServiceInfo]:
        """Get service by name"""
        return self.services.get(name)
    
    def get_all_services(self) -> Dict[str, ServiceInfo]:
        """Get all registered services"""
        return self.services.copy()
    
    def get_healthy_services(self) -> Dict[str, ServiceInfo]:
        """Get only healthy services"""
        return {
            name: service for name, service in self.services.items()
            if service.status == ServiceStatus.HEALTHY
        }
    
    def get_services_by_model(self, model: str) -> List[ServiceInfo]:
        """Get services that support a specific model"""
        return [
            service for service in self.services.values()
            if model in service.models and service.status == ServiceStatus.HEALTHY
        ]
    
    def update_service_status(self, name: str, status: ServiceStatus, response_time: float = 0):
        """Update service status"""
        if name in self.services:
            service = self.services[name]
            old_status = service.status
            service.status = status
            service.last_health_check = time.time()
            service.response_time = response_time
            
            if status == ServiceStatus.HEALTHY and old_status != ServiceStatus.HEALTHY:
                service.uptime_start = time.time()
                service.error_count = 0
            elif status in [ServiceStatus.UNHEALTHY, ServiceStatus.ERROR]:
                service.error_count += 1
            
            logger.info(f"Service {name} status updated: {old_status.value} -> {status.value}")
    
    async def health_check_service(self, service: ServiceInfo) -> bool:
        """Perform health check on a single service"""
        try:
            start_time = time.time()
            
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    service.health_endpoint,
                    timeout=aiohttp.ClientTimeout(total=self.health_check_timeout)
                ) as response:
                    response_time = time.time() - start_time
                    
                    if response.status == 200:
                        self.update_service_status(service.name, ServiceStatus.HEALTHY, response_time)
                        return True
                    else:
                        self.update_service_status(service.name, ServiceStatus.UNHEALTHY, response_time)
                        return False
                        
        except asyncio.TimeoutError:
            logger.warning(f"Health check timeout for {service.name}")
            self.update_service_status(service.name, ServiceStatus.UNHEALTHY)
            return False
        except Exception as e:
            logger.error(f"Health check error for {service.name}: {e}")
            self.update_service_status(service.name, ServiceStatus.ERROR)
            return False
    
    async def health_check_all_services(self) -> Dict[str, bool]:
        """Perform health check on all services"""
        tasks = []
        for service in self.services.values():
            if service.status != ServiceStatus.STOPPED:
                tasks.append(self.health_check_service(service))
        
        if tasks:
            results = await asyncio.gather(*tasks, return_exceptions=True)
            return {
                service.name: result for service, result in 
                zip(self.services.values(), results)
                if not isinstance(result, Exception)
            }
        return {}
    
    async def start_health_monitoring(self):
        """Start continuous health monitoring"""
        logger.info("Starting health monitoring...")
        
        while True:
            try:
                await self.health_check_all_services()
                await asyncio.sleep(self.health_check_interval)
            except Exception as e:
                logger.error(f"Health monitoring error: {e}")
                await asyncio.sleep(5)
    
    def get_service_stats(self) -> Dict[str, Any]:
        """Get overall service statistics"""
        total_services = len(self.services)
        healthy_count = len(self.get_healthy_services())
        
        status_counts = {}
        for status in ServiceStatus:
            status_counts[status.value] = len([
                s for s in self.services.values() if s.status == status
            ])
        
        return {
            "total_services": total_services,
            "healthy_services": healthy_count,
            "unhealthy_services": total_services - healthy_count,
            "status_breakdown": status_counts,
            "allocated_ports": sorted(list(self.allocated_ports)),
            "last_updated": time.time()
        }
    
    def export_config(self) -> Dict[str, Any]:
        """Export service configuration"""
        return {
            "services": {
                name: asdict(service) for name, service in self.services.items()
            },
            "stats": self.get_service_stats()
        }
    
    def save_config(self, filepath: str = "config/services.json"):
        """Save service configuration to file"""
        config = self.export_config()
        
        # Ensure directory exists
        Path(filepath).parent.mkdir(parents=True, exist_ok=True)
        
        with open(filepath, 'w') as f:
            json.dump(config, f, indent=2, default=str)
        
        logger.info(f"Service configuration saved to {filepath}")

# Global service registry instance
service_registry = ServiceRegistry()

async def main():
    """Main function for testing"""
    logger.info("🚀 Starting Service Registry...")
    
    # Print all registered services
    services = service_registry.get_all_services()
    logger.info(f"Registered {len(services)} services:")
    
    for name, service in services.items():
        logger.info(f"  - {name}: {service.service_type.value} on port {service.port}")
    
    # Save configuration
    service_registry.save_config()
    
    # Start health monitoring (would run continuously in production)
    logger.info("Health monitoring would start here...")

if __name__ == "__main__":
    asyncio.run(main())
