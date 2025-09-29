"""
Core API Gateway - Handles format detection, conversion, and routing
"""

import asyncio
import json
import logging
from typing import Dict, Any, Optional, AsyncGenerator, Union

from fastapi import HTTPException
from formats.format_detector import FormatDetector
from formats.universal_chat import UniversalChatFormat
from converters.converter_factory import ConverterFactory
from providers.provider_manager import ProviderManager
from balancing.load_balancer import LoadBalancer

logger = logging.getLogger(__name__)

class APIGateway:
    """
    Core API Gateway that handles:
    1. Format detection (OpenAI/Gemini/Anthropic)
    2. Conversion to WebChat format
    3. Provider routing and load balancing
    4. Response conversion back to original format
    """
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.format_detector = FormatDetector()
        self.converter_factory = ConverterFactory()
        self.provider_manager = ProviderManager(config)
        self.load_balancer = LoadBalancer(config)
        
    async def process_request(
        self,
        request_data: Dict[str, Any],
        headers: Dict[str, str],
        provider_override: Optional[str] = None
    ) -> Union[Dict[str, Any], AsyncGenerator[str, None]]:
        """
        Process an API request through the gateway.
        
        Args:
            request_data: The API request data
            headers: Request headers
            provider_override: Optional provider to use instead of load balancing
            
        Returns:
            Response data or async generator for streaming
        """
        
        try:
            # Step 1: Detect API format
            api_format = self.format_detector.detect_format(request_data, headers)
            logger.info(f"🔍 Detected API format: {api_format}")
            
            # Step 2: Convert to WebChat format
            converter = self.converter_factory.get_converter(api_format)
            webchat_request = converter.to_webchat(request_data)
            logger.info(f"🔄 Converted to WebChat format")
            
            # Step 3: Select provider
            if provider_override:
                provider_name = provider_override
                logger.info(f"🎯 Using override provider: {provider_name}")
            else:
                provider_name = await self.load_balancer.select_provider(webchat_request)
                logger.info(f"⚖️  Load balancer selected: {provider_name}")
            
            # Step 4: Route to provider
            provider = self.provider_manager.get_provider(provider_name)
            if not provider:
                raise HTTPException(status_code=503, detail=f"Provider {provider_name} not available")
            
            # Step 5: Get response from provider
            webchat_response = await provider.process_request(webchat_request)
            logger.info(f"✅ Received response from {provider_name}")
            
            # Step 6: Convert back to original format
            if webchat_response.get("streaming", False):
                # Handle streaming response
                return self._handle_streaming_response(
                    webchat_response, converter, api_format, provider_name
                )
            else:
                # Handle regular response
                original_response = converter.from_webchat(webchat_response)
                logger.info(f"🔄 Converted back to {api_format} format")
                return original_response
                
        except Exception as e:
            logger.error(f"❌ Gateway processing failed: {e}")
            raise
    
    async def _handle_streaming_response(
        self,
        webchat_response: Dict[str, Any],
        converter,
        api_format: str,
        provider_name: str
    ) -> AsyncGenerator[str, None]:
        """Handle streaming response conversion."""
        
        logger.info(f"🌊 Starting streaming response from {provider_name}")
        
        try:
            async for chunk in webchat_response["stream"]:
                # Convert each chunk back to original format
                original_chunk = converter.stream_chunk_from_webchat(chunk, api_format)
                yield original_chunk
                
        except Exception as e:
            logger.error(f"❌ Streaming error: {e}")
            # Send error chunk in appropriate format
            error_chunk = converter.create_error_chunk(str(e), api_format)
            yield error_chunk
    
    async def health_check(self) -> Dict[str, Any]:
        """Check health of all system components."""
        
        health_status = {
            "gateway": "healthy",
            "providers": {},
            "load_balancer": "healthy",
            "timestamp": asyncio.get_event_loop().time()
        }
        
        # Check provider health
        for provider_name in self.provider_manager.get_provider_names():
            try:
                provider = self.provider_manager.get_provider(provider_name)
                if provider:
                    is_healthy = await provider.health_check()
                    health_status["providers"][provider_name] = "healthy" if is_healthy else "unhealthy"
                else:
                    health_status["providers"][provider_name] = "unavailable"
            except Exception as e:
                health_status["providers"][provider_name] = f"error: {str(e)}"
        
        return health_status
    
    async def get_available_providers(self) -> Dict[str, Dict[str, Any]]:
        """Get list of available providers with their status."""
        
        providers = {}
        
        for provider_name in self.provider_manager.get_provider_names():
            provider = self.provider_manager.get_provider(provider_name)
            if provider:
                providers[provider_name] = {
                    "enabled": True,
                    "priority": self.config.get("providers", {}).get(provider_name, {}).get("priority", 999),
                    "healthy": await provider.health_check(),
                    "stats": await provider.get_stats()
                }
            else:
                providers[provider_name] = {
                    "enabled": False,
                    "priority": 999,
                    "healthy": False,
                    "stats": {}
                }
        
        return providers
    
    async def test_provider(self, provider_name: str, test_message: str = "Hello, world!") -> Dict[str, Any]:
        """Test a specific provider with a simple message."""
        
        try:
            provider = self.provider_manager.get_provider(provider_name)
            if not provider:
                return {
                    "success": False,
                    "error": f"Provider {provider_name} not available"
                }
            
            # Create test WebChat request
            test_request = UniversalChatFormat.create_simple_request(test_message)
            
            # Send test request
            start_time = asyncio.get_event_loop().time()
            response = await provider.process_request(test_request)
            end_time = asyncio.get_event_loop().time()
            
            return {
                "success": True,
                "provider": provider_name,
                "response_time": end_time - start_time,
                "response": response.get("content", "No content"),
                "metadata": response.get("metadata", {})
            }
            
        except Exception as e:
            logger.error(f"Provider test failed for {provider_name}: {e}")
            return {
                "success": False,
                "provider": provider_name,
                "error": str(e)
            }
