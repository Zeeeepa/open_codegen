"""
Universal Request Interceptor - Intercepts any URL and routes intelligently
"""
import logging
from typing import Optional, Dict, Any
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse
import re
import json

from ..routing.priority_router import PriorityRouter
from ..routing.url_matcher import URLMatcher
from ..discovery.service_registry import ServiceRegistry

logger = logging.getLogger(__name__)

class UniversalRequestInterceptor(BaseHTTPMiddleware):
    """
    Middleware that intercepts all requests and intelligently routes them
    to appropriate AI endpoints based on URL patterns, model names, and priorities.
    """
    
    def __init__(self, app, endpoint_manager):
        super().__init__(app)
        self.endpoint_manager = endpoint_manager
        self.priority_router = PriorityRouter(endpoint_manager)
        self.url_matcher = URLMatcher()
        self.service_registry = ServiceRegistry()
        
        # Patterns for AI service URLs
        self.ai_service_patterns = [
            r'.*chat\.openai\.com.*',
            r'.*api\.openai\.com.*',
            r'.*chat\.deepseek\.com.*',
            r'.*api\.deepseek\.com.*',
            r'.*chat\.z\.ai.*',
            r'.*z\.ai.*',
            r'.*aistudio\.google\.com.*',
            r'.*gemini\.google\.com.*',
            r'.*chat\.mistral\.ai.*',
            r'.*api\.mistral\.ai.*',
            r'.*bolt\.new.*',
            r'.*claude\.ai.*',
            r'.*api\.anthropic\.com.*',
            r'.*codegen.*\.modal\.run.*'
        ]
        
    async def dispatch(self, request: Request, call_next):
        """
        Main dispatch method that intercepts and routes requests
        """
        try:
            # Check if this is an AI service request
            if await self._should_intercept(request):
                logger.info(f"Intercepting request to {request.url}")
                return await self._handle_ai_request(request)
            
            # For non-AI requests, proceed normally
            response = await call_next(request)
            return response
            
        except Exception as e:
            logger.error(f"Error in request interceptor: {e}")
            return await call_next(request)
    
    async def _should_intercept(self, request: Request) -> bool:
        """
        Determine if this request should be intercepted and routed
        """
        url_str = str(request.url)
        
        # Always intercept OpenAI-compatible API calls
        if '/v1/chat/completions' in url_str:
            return True
            
        # Intercept known AI service URLs
        for pattern in self.ai_service_patterns:
            if re.match(pattern, url_str, re.IGNORECASE):
                return True
                
        # Check if URL matches any configured endpoint
        if self.url_matcher.matches_known_service(url_str):
            return True
            
        return False
    
    async def _handle_ai_request(self, request: Request) -> Response:
        """
        Handle intercepted AI requests with intelligent routing
        """
        try:
            # Parse request body
            body = await request.body()
            if body:
                try:
                    request_data = json.loads(body.decode())
                except json.JSONDecodeError:
                    request_data = {}
            else:
                request_data = {}
            
            # Extract model name and messages
            model = request_data.get('model')
            messages = request_data.get('messages', [])
            
            if not messages:
                return JSONResponse(
                    status_code=400,
                    content={"error": "No messages provided"}
                )
            
            # Get the user message
            user_message = None
            for msg in messages:
                if msg.get('role') == 'user':
                    user_message = msg.get('content', '')
                    break
            
            if not user_message:
                return JSONResponse(
                    status_code=400,
                    content={"error": "No user message found"}
                )
            
            # Route the request using priority-based routing
            response = await self.priority_router.route_request(
                model=model,
                message=user_message,
                url=str(request.url),
                request_data=request_data
            )
            
            if response:
                return JSONResponse(content=response)
            else:
                return JSONResponse(
                    status_code=503,
                    content={"error": "No available endpoints"}
                )
                
        except Exception as e:
            logger.error(f"Error handling AI request: {e}")
            return JSONResponse(
                status_code=500,
                content={"error": f"Internal server error: {str(e)}"}
            )
    
    async def _auto_discover_service(self, url: str) -> Optional[Dict[str, Any]]:
        """
        Automatically discover and configure a new AI service from URL
        """
        try:
            service_config = await self.service_registry.discover_service(url)
            if service_config:
                # Auto-add the discovered service
                await self.endpoint_manager.add_endpoint_from_config(service_config)
                logger.info(f"Auto-discovered and added service: {service_config['name']}")
                return service_config
        except Exception as e:
            logger.error(f"Error auto-discovering service from {url}: {e}")
        
        return None
