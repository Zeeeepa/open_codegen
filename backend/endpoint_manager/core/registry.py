"""
Endpoint Registry for Universal AI Endpoint Manager

Manages endpoint configurations with persistent storage.
Similar to the cryptocurrency bot's account registry.
"""

import json
import logging
from pathlib import Path
from typing import Dict, Optional, List
from ..models.endpoint import EndpointConfig

logger = logging.getLogger(__name__)

class EndpointRegistry:
    """Registry for managing endpoint configurations"""
    
    def __init__(self, config_dir: str = "config"):
        self.config_dir = Path(config_dir)
        self.endpoints_file = self.config_dir / "endpoints.json"
        self.endpoints: Dict[str, EndpointConfig] = {}
        
        # Ensure config directory exists
        self.config_dir.mkdir(exist_ok=True)
        
        logger.info(f"Endpoint registry initialized with config dir: {config_dir}")
    
    async def load_endpoints(self):
        """Load endpoints from disk"""
        try:
            if self.endpoints_file.exists():
                with open(self.endpoints_file, 'r') as f:
                    data = json.load(f)
                
                self.endpoints = {
                    endpoint_id: EndpointConfig.from_dict(endpoint_data)
                    for endpoint_id, endpoint_data in data.items()
                }
                
                logger.info(f"Loaded {len(self.endpoints)} endpoints from disk")
            else:
                logger.info("No existing endpoints file found")
        
        except Exception as e:
            logger.error(f"Error loading endpoints: {e}")
            self.endpoints = {}
    
    async def save_endpoints(self):
        """Save endpoints to disk"""
        try:
            data = {
                endpoint_id: endpoint.to_dict()
                for endpoint_id, endpoint in self.endpoints.items()
            }
            
            with open(self.endpoints_file, 'w') as f:
                json.dump(data, f, indent=2)
            
            logger.debug(f"Saved {len(self.endpoints)} endpoints to disk")
        
        except Exception as e:
            logger.error(f"Error saving endpoints: {e}")
    
    async def add_endpoint(self, config: EndpointConfig) -> bool:
        """Add an endpoint to the registry"""
        try:
            self.endpoints[config.id] = config
            await self.save_endpoints()
            logger.info(f"Added endpoint to registry: {config.name}")
            return True
        except Exception as e:
            logger.error(f"Error adding endpoint to registry: {e}")
            return False
    
    async def remove_endpoint(self, endpoint_id: str) -> bool:
        """Remove an endpoint from the registry"""
        try:
            if endpoint_id in self.endpoints:
                del self.endpoints[endpoint_id]
                await self.save_endpoints()
                logger.info(f"Removed endpoint from registry: {endpoint_id}")
                return True
            return False
        except Exception as e:
            logger.error(f"Error removing endpoint from registry: {e}")
            return False
    
    async def get_endpoint(self, endpoint_id: str) -> Optional[EndpointConfig]:
        """Get an endpoint by ID"""
        return self.endpoints.get(endpoint_id)
    
    async def update_endpoint(self, config: EndpointConfig) -> bool:
        """Update an endpoint in the registry"""
        try:
            if config.id in self.endpoints:
                self.endpoints[config.id] = config
                await self.save_endpoints()
                return True
            return False
        except Exception as e:
            logger.error(f"Error updating endpoint in registry: {e}")
            return False
    
    async def list_endpoints(self) -> List[EndpointConfig]:
        """List all endpoints"""
        return list(self.endpoints.values())
