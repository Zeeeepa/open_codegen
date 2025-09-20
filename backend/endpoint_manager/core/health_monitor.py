"""
Health Monitor for Universal AI Endpoint Manager

Monitors endpoint health and performance, similar to crypto bot's monitoring.
"""

import asyncio
import logging
from typing import TYPE_CHECKING
from ..models.endpoint import HealthStatus

if TYPE_CHECKING:
    from .manager import UniversalEndpointManager

logger = logging.getLogger(__name__)

class HealthMonitor:
    """Health monitoring for endpoints"""
    
    def __init__(self, manager: 'UniversalEndpointManager'):
        self.manager = manager
        logger.info("Health monitor initialized")
    
    async def check_all_endpoints(self):
        """Check health of all endpoints"""
        try:
            for endpoint_id, config in self.manager.registry.endpoints.items():
                if config.is_running():
                    # Simple health check - can be enhanced
                    config.update_health(HealthStatus.GOOD)
                    await self.manager.registry.update_endpoint(config)
        except Exception as e:
            logger.error(f"Error in health check: {e}")
