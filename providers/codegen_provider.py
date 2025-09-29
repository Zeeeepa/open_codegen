"""
Codegen Provider - Uses existing Codegen SDK integration
"""

import asyncio
import logging
from typing import Dict, Any

from providers.base_provider import BaseProvider

logger = logging.getLogger(__name__)

class CodegenProvider(BaseProvider):
    """Provider for Codegen SDK integration."""
    
    async def initialize(self):
        """Initialize the Codegen provider."""
        try:
            # Import existing Codegen components
            from backend.adapter.enhanced_client import EnhancedCodegenClient
            from backend.adapter.config import get_enhanced_codegen_config
            from backend.adapter.auth import get_auth
            
            # Get configuration
            codegen_config = get_enhanced_codegen_config()
            auth = get_auth()
            
            # Initialize client (initialization happens in constructor)
            self.client = EnhancedCodegenClient(
                config=codegen_config,
                auth=auth
            )
            
            self.initialized = True
            self.stats["initialized_at"] = asyncio.get_event_loop().time()
            
            logger.info("✅ Codegen provider initialized successfully")
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize Codegen provider: {e}")
            raise
    
    async def process_request(self, webchat_request: Dict[str, Any]) -> Dict[str, Any]:
        """Process request using Codegen SDK."""
        
        if not self.initialized:
            return self._create_error_response("Provider not initialized")
        
        start_time = self._record_request_start()
        
        try:
            # Extract message from WebChat format
            message = webchat_request.get("message", "")
            if not message:
                raise ValueError("No message provided")
            
            # Use existing Codegen client
            response_content = ""
            async for chunk in self.client.run_task(message, stream=False):
                response_content += chunk
            
            self._record_request_success(start_time)
            
            return self._create_success_response(
                content=response_content,
                metadata={
                    "model": "codegen",
                    "provider": "codegen"
                }
            )
            
        except Exception as e:
            error_msg = f"Codegen request failed: {str(e)}"
            logger.error(error_msg)
            self._record_request_failure(error_msg)
            return self._create_error_response(error_msg)
    
    async def health_check(self) -> bool:
        """Check if Codegen provider is healthy."""
        
        if not self.initialized:
            return False
        
        try:
            # Simple test request
            test_request = {"message": "Hello"}
            response = await self.process_request(test_request)
            return response.get("success", False)
            
        except Exception as e:
            logger.error(f"Codegen health check failed: {e}")
            return False
