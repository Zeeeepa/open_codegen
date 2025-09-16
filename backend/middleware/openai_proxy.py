"""
OpenAI API Proxy Middleware for routing API calls to configured endpoints.
Intercepts OpenAI, Anthropic, and Gemini API calls and routes them to either
Codegen API or Z.AI Web UI based on configuration.
"""
import json
import logging
from typing import Dict, Any, Optional, List
from fastapi import Request, Response, HTTPException
from fastapi.responses import StreamingResponse
import asyncio

from backend.endpoint_manager.endpoint_service import get_endpoint_service
from backend.database.models import get_database_manager, ProviderType

logger = logging.getLogger(__name__)


class OpenAIProxyMiddleware:
    """
    Middleware to intercept and route OpenAI-compatible API calls.
    
    Routes requests to configured endpoints based on routing rules:
    - Codegen API (default)
    - Z.AI Web UI (with toggle and autoscaling)
    """
    
    def __init__(self):
        self.db = get_database_manager()
        self.endpoint_service = get_endpoint_service()
        self.routing_config = {
            "default_route": "codegen_api",  # codegen_api or zai_webui
            "zai_webui_enabled": True,
            "load_balancing": "round_robin",  # round_robin, random, least_connections
            "fallback_enabled": True
        }
        self._route_index = 0
    
    async def __call__(self, request: Request, call_next):
        """Process incoming requests and route appropriately."""
        # Check if this is an API request we should intercept
        if not self._should_intercept(request):
            return await call_next(request)
        
        try:
            # Determine the API provider from the request
            api_provider = self._detect_api_provider(request)
            
            # Get routing configuration for this request
            target_endpoint = await self._get_target_endpoint(request, api_provider)
            
            if not target_endpoint:
                # No configured endpoint, pass through to original handler
                return await call_next(request)
            
            # Route the request to the target endpoint
            return await self._route_request(request, target_endpoint, api_provider)
        
        except Exception as e:
            logger.error(f"Error in OpenAI proxy middleware: {e}")
            # Fallback to original handler on error
            return await call_next(request)
    
    def _should_intercept(self, request: Request) -> bool:
        """Determine if this request should be intercepted."""
        path = request.url.path
        
        # OpenAI API endpoints
        openai_paths = [
            "/v1/chat/completions",
            "/v1/completions",
            "/v1/embeddings"
        ]
        
        # Anthropic API endpoints
        anthropic_paths = [
            "/v1/messages",
            "/v1/complete"
        ]
        
        # Gemini API endpoints
        gemini_paths = [
            "/v1/models/",
            "/v1beta/models/"
        ]
        
        # Check if path matches any interceptable endpoint
        for api_path in openai_paths + anthropic_paths + gemini_paths:
            if path.startswith(api_path) or api_path in path:
                return True
        
        return False
    
    def _detect_api_provider(self, request: Request) -> str:
        """Detect which API provider this request is for."""
        path = request.url.path
        headers = request.headers
        
        # Check path patterns
        if "/v1/chat/completions" in path or "/v1/completions" in path:
            return "openai"
        elif "/v1/messages" in path:
            return "anthropic"
        elif "/v1/models/" in path or "/v1beta/models/" in path:
            return "gemini"
        
        # Check headers for additional clues
        auth_header = headers.get("authorization", "").lower()
        if "sk-ant-" in auth_header:
            return "anthropic"
        elif "bearer" in auth_header and "goog" in auth_header:
            return "gemini"
        
        # Default to OpenAI
        return "openai"
    
    async def _get_target_endpoint(self, request: Request, api_provider: str) -> Optional[Dict[str, Any]]:
        """Get the target endpoint configuration for routing."""
        # Get user context (in a real implementation, extract from auth)
        user_id = self._extract_user_id(request)
        
        if not user_id:
            # Use default system endpoints
            return await self._get_default_endpoint(api_provider)
        
        # Get user's configured endpoints
        endpoints = self.db.get_user_endpoint_configs(user_id)
        active_endpoints = [ep for ep in endpoints if ep.is_enabled and ep.status == "running"]
        
        if not active_endpoints:
            return await self._get_default_endpoint(api_provider)
        
        # Apply routing logic
        return self._select_endpoint_by_routing_rule(active_endpoints, api_provider)
    
    def _extract_user_id(self, request: Request) -> Optional[str]:
        """Extract user ID from request (placeholder implementation)."""
        # In a real implementation, this would extract user ID from:
        # - JWT token
        # - API key mapping
        # - Session data
        # For now, return None to use default endpoints
        return None
    
    async def _get_default_endpoint(self, api_provider: str) -> Optional[Dict[str, Any]]:
        """Get default system endpoint configuration."""
        # Check routing configuration
        if self.routing_config["zai_webui_enabled"] and self.routing_config["default_route"] == "zai_webui":
            return {
                "id": "default_zai_webui",
                "type": "zai_webui",
                "provider_type": ProviderType.WEB_CHAT.value,
                "config": {
                    "provider_type": "zai",
                    "base_url": "https://chat.z.ai",
                    "auto_auth": True,
                    "model": "glm-4.5v",
                    "pool_size": 3,
                    "autoscaling": True,
                    "max_pool_size": 10
                }
            }
        else:
            return {
                "id": "default_codegen_api",
                "type": "codegen_api",
                "provider_type": ProviderType.REST_API.value,
                "config": {
                    "api_base_url": "https://api.codegen.com",
                    "auth_type": "api_key",
                    "timeout": 30,
                    "max_retries": 3
                }
            }
    
    def _select_endpoint_by_routing_rule(self, endpoints: List[Any], api_provider: str) -> Dict[str, Any]:
        """Select endpoint based on routing rules."""
        if not endpoints:
            return None
        
        routing_method = self.routing_config.get("load_balancing", "round_robin")
        
        if routing_method == "round_robin":
            endpoint = endpoints[self._route_index % len(endpoints)]
            self._route_index += 1
            return {
                "id": endpoint.id,
                "type": "user_endpoint",
                "provider_type": endpoint.provider_type,
                "config": endpoint.config_data
            }
        
        elif routing_method == "random":
            import random
            endpoint = random.choice(endpoints)
            return {
                "id": endpoint.id,
                "type": "user_endpoint", 
                "provider_type": endpoint.provider_type,
                "config": endpoint.config_data
            }
        
        else:
            # Default to first endpoint
            endpoint = endpoints[0]
            return {
                "id": endpoint.id,
                "type": "user_endpoint",
                "provider_type": endpoint.provider_type,
                "config": endpoint.config_data
            }
    
    async def _route_request(self, request: Request, target_endpoint: Dict[str, Any], api_provider: str) -> Response:
        """Route the request to the target endpoint."""
        try:
            # Get request body
            body = await request.body()
            request_data = json.loads(body) if body else {}
            
            # Convert request format if needed
            converted_request = self._convert_request_format(request_data, api_provider, target_endpoint)
            
            # Route based on endpoint type
            if target_endpoint["provider_type"] == ProviderType.WEB_CHAT.value:
                return await self._route_to_web_chat(converted_request, target_endpoint)
            elif target_endpoint["provider_type"] == ProviderType.REST_API.value:
                return await self._route_to_rest_api(converted_request, target_endpoint)
            else:
                raise HTTPException(status_code=500, detail="Unsupported endpoint type")
        
        except Exception as e:
            logger.error(f"Error routing request: {e}")
            if self.routing_config.get("fallback_enabled", True):
                # Try fallback endpoint
                return await self._handle_fallback(request, api_provider)
            else:
                raise HTTPException(status_code=500, detail=f"Routing failed: {e}")
    
    def _convert_request_format(self, request_data: Dict[str, Any], api_provider: str, target_endpoint: Dict[str, Any]) -> Dict[str, Any]:
        """Convert request format between different API providers."""
        # Extract common fields
        messages = request_data.get("messages", [])
        model = request_data.get("model", "")
        temperature = request_data.get("temperature", 0.7)
        max_tokens = request_data.get("max_tokens", 1000)
        
        # Handle different input formats
        if api_provider == "anthropic":
            # Anthropic uses different message format
            if "content" in request_data:
                messages = [{"role": "user", "content": request_data["content"]}]
        
        elif api_provider == "gemini":
            # Gemini uses different structure
            if "contents" in request_data:
                contents = request_data["contents"]
                messages = []
                for content in contents:
                    if "parts" in content:
                        text = content["parts"][0].get("text", "")
                        messages.append({"role": "user", "content": text})
        
        # Convert to unified format
        return {
            "messages": messages,
            "model": model,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "stream": request_data.get("stream", False)
        }
    
    async def _route_to_web_chat(self, request_data: Dict[str, Any], target_endpoint: Dict[str, Any]) -> Response:
        """Route request to web chat handler (Z.AI)."""
        from backend.endpoint_manager.providers.web_chat_handler import WebChatHandler
        from backend.database.models import EndpointConfig
        
        # Create temporary endpoint config
        config = EndpointConfig(
            id=target_endpoint["id"],
            user_id="system",
            name="Z.AI Web UI",
            model_name=request_data.get("model", "glm-4.5v"),
            description="Z.AI Web UI endpoint",
            provider_type=ProviderType.WEB_CHAT.value,
            provider_name="zai",
            config_data=target_endpoint["config"],
            status="running",
            is_enabled=True,
            priority=1,
            max_concurrent_requests=10,
            timeout_seconds=180,
            retry_attempts=3,
            created_at="",
            updated_at=""
        )
        
        # Create handler and send message
        handler = WebChatHandler(config)
        await handler.start()
        
        try:
            # Extract message from request
            messages = request_data.get("messages", [])
            if messages:
                last_message = messages[-1].get("content", "")
                response_content = await handler.send_message(last_message)
                
                # Format response in OpenAI format
                response_data = {
                    "id": f"chatcmpl-{target_endpoint['id']}",
                    "object": "chat.completion",
                    "created": int(asyncio.get_event_loop().time()),
                    "model": request_data.get("model", "glm-4.5v"),
                    "choices": [{
                        "index": 0,
                        "message": {
                            "role": "assistant",
                            "content": response_content
                        },
                        "finish_reason": "stop"
                    }],
                    "usage": {
                        "prompt_tokens": len(last_message.split()),
                        "completion_tokens": len(response_content.split()),
                        "total_tokens": len(last_message.split()) + len(response_content.split())
                    }
                }
                
                return Response(
                    content=json.dumps(response_data),
                    media_type="application/json",
                    status_code=200
                )
            else:
                raise HTTPException(status_code=400, detail="No messages provided")
        
        finally:
            await handler.stop()
    
    async def _route_to_rest_api(self, request_data: Dict[str, Any], target_endpoint: Dict[str, Any]) -> Response:
        """Route request to REST API handler (Codegen API)."""
        from backend.endpoint_manager.providers.rest_api_handler import RestApiHandler
        from backend.database.models import EndpointConfig
        
        # Create temporary endpoint config
        config = EndpointConfig(
            id=target_endpoint["id"],
            user_id="system",
            name="Codegen REST API",
            model_name=request_data.get("model", "gpt-3.5-turbo"),
            description="Codegen REST API endpoint",
            provider_type=ProviderType.REST_API.value,
            provider_name="codegen",
            config_data=target_endpoint["config"],
            status="running",
            is_enabled=True,
            priority=1,
            max_concurrent_requests=10,
            timeout_seconds=30,
            retry_attempts=3,
            created_at="",
            updated_at=""
        )
        
        # Create handler and send message
        handler = RestApiHandler(config)
        await handler.start()
        
        try:
            # Extract message from request
            messages = request_data.get("messages", [])
            if messages:
                last_message = messages[-1].get("content", "")
                response_content = await handler.send_message(last_message)
                
                # Format response in OpenAI format
                response_data = {
                    "id": f"chatcmpl-{target_endpoint['id']}",
                    "object": "chat.completion",
                    "created": int(asyncio.get_event_loop().time()),
                    "model": request_data.get("model", "gpt-3.5-turbo"),
                    "choices": [{
                        "index": 0,
                        "message": {
                            "role": "assistant",
                            "content": response_content
                        },
                        "finish_reason": "stop"
                    }],
                    "usage": {
                        "prompt_tokens": len(last_message.split()),
                        "completion_tokens": len(response_content.split()),
                        "total_tokens": len(last_message.split()) + len(response_content.split())
                    }
                }
                
                return Response(
                    content=json.dumps(response_data),
                    media_type="application/json",
                    status_code=200
                )
            else:
                raise HTTPException(status_code=400, detail="No messages provided")
        
        finally:
            await handler.stop()
    
    async def _handle_fallback(self, request: Request, api_provider: str) -> Response:
        """Handle fallback when primary routing fails."""
        # Try the opposite of default route
        fallback_route = "codegen_api" if self.routing_config["default_route"] == "zai_webui" else "zai_webui"
        
        # Get fallback endpoint
        if fallback_route == "zai_webui" and self.routing_config["zai_webui_enabled"]:
            fallback_endpoint = {
                "id": "fallback_zai_webui",
                "type": "zai_webui",
                "provider_type": ProviderType.WEB_CHAT.value,
                "config": {
                    "provider_type": "zai",
                    "base_url": "https://chat.z.ai",
                    "auto_auth": True,
                    "model": "glm-4.5v"
                }
            }
        else:
            fallback_endpoint = {
                "id": "fallback_codegen_api",
                "type": "codegen_api",
                "provider_type": ProviderType.REST_API.value,
                "config": {
                    "api_base_url": "https://api.codegen.com",
                    "auth_type": "api_key"
                }
            }
        
        # Try routing to fallback
        body = await request.body()
        request_data = json.loads(body) if body else {}
        converted_request = self._convert_request_format(request_data, api_provider, fallback_endpoint)
        
        if fallback_endpoint["provider_type"] == ProviderType.WEB_CHAT.value:
            return await self._route_to_web_chat(converted_request, fallback_endpoint)
        else:
            return await self._route_to_rest_api(converted_request, fallback_endpoint)


# Configuration management
class ProxyConfig:
    """Configuration manager for the OpenAI proxy."""
    
    @staticmethod
    def update_routing_config(config: Dict[str, Any]) -> None:
        """Update routing configuration."""
        # This would typically update a persistent configuration store
        pass
    
    @staticmethod
    def get_routing_config() -> Dict[str, Any]:
        """Get current routing configuration."""
        return {
            "default_route": "codegen_api",
            "zai_webui_enabled": True,
            "load_balancing": "round_robin",
            "fallback_enabled": True
        }
    
    @staticmethod
    def toggle_zai_webui(enabled: bool) -> None:
        """Toggle Z.AI Web UI routing on/off."""
        # This would update the configuration
        pass
