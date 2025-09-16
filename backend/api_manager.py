"""
API Manager for OpenAI Codegen Adapter Web UI

This module extends the existing FastAPI server with management endpoints
for the web UI, including chat routing, endpoint management, and website analysis.
"""

import os
import json
import asyncio
import logging
from datetime import datetime
from typing import Dict, Any, List, Optional
from pathlib import Path

from fastapi import FastAPI, HTTPException, Request, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse
from pydantic import BaseModel

# Import existing components
from backend.adapter.codegen_client import CodegenClient
from backend.adapter.config import get_codegen_config

# Import our new components
from backend.chat_handler import ChatHandler
from backend.endpoint_manager import EndpointManager
from backend.web_scraper import WebScraper
from backend.providers.zai_provider import ZaiProvider

logger = logging.getLogger(__name__)

# Pydantic models for API requests/responses
class ChatRequest(BaseModel):
    message: str
    provider: str = "openai"
    model: str = "gpt-4"
    conversation_history: List[Dict[str, Any]] = []
    stream: bool = True

class EndpointRequest(BaseModel):
    name: str
    description: str
    method: str = "GET"
    url: str
    headers: Dict[str, str] = {}
    body: str = ""
    provider: str = "openai"
    variables: List[Dict[str, Any]] = []

class WebsiteAnalysisRequest(BaseModel):
    url: str

class ConfigUpdateRequest(BaseModel):
    config: Dict[str, Any]

class APIManager:
    """Main API manager for the web UI backend"""
    
    def __init__(self, app: FastAPI):
        self.app = app
        self.codegen_client = None
        self.chat_handler = None
        self.endpoint_manager = EndpointManager()
        self.web_scraper = WebScraper()
        self.zai_provider = ZaiProvider()
        
        # Initialize components
        self._initialize_components()
        
        # Add CORS middleware
        self._setup_cors()
        
        # Register routes
        self._register_routes()
    
    def _initialize_components(self):
        """Initialize core components"""
        try:
            # Initialize Codegen client
            config = get_codegen_config()
            self.codegen_client = CodegenClient(config)
            
            # Initialize chat handler with the client
            self.chat_handler = ChatHandler(self.codegen_client)
            
            logger.info("API Manager components initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize API Manager components: {e}")
            raise
    
    def _setup_cors(self):
        """Setup CORS middleware for web UI"""
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
    
    def _register_routes(self):
        """Register all API routes"""
        
        # Chat endpoints
        @self.app.post("/api/chat")
        async def chat_endpoint(request: ChatRequest):
            """Handle chat requests with multi-provider support"""
            try:
                if request.stream:
                    return StreamingResponse(
                        self._stream_chat_response(request),
                        media_type="text/plain"
                    )
                else:
                    response = await self.chat_handler.handle_chat(
                        message=request.message,
                        provider=request.provider,
                        model=request.model,
                        conversation_history=request.conversation_history
                    )
                    return {"content": response}
            except Exception as e:
                logger.error(f"Chat endpoint error: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        # Configuration endpoints
        @self.app.get("/api/config")
        async def get_config():
            """Get current configuration"""
            try:
                config = get_codegen_config()
                # Remove sensitive information
                safe_config = {k: v for k, v in config.items() if 'key' not in k.lower()}
                return safe_config
            except Exception as e:
                logger.error(f"Get config error: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.put("/api/config")
        async def update_config(request: ConfigUpdateRequest):
            """Update configuration"""
            try:
                # Save configuration (implement based on your config system)
                # This is a placeholder - implement actual config saving
                return {"status": "success", "message": "Configuration updated"}
            except Exception as e:
                logger.error(f"Update config error: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        # Endpoint management
        @self.app.get("/api/endpoints")
        async def get_endpoints():
            """Get all managed endpoints"""
            try:
                return await self.endpoint_manager.get_endpoints()
            except Exception as e:
                logger.error(f"Get endpoints error: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.post("/api/endpoints")
        async def create_endpoint(request: EndpointRequest):
            """Create a new endpoint"""
            try:
                endpoint_data = request.dict()
                result = await self.endpoint_manager.create_endpoint(endpoint_data)
                return result
            except Exception as e:
                logger.error(f"Create endpoint error: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.put("/api/endpoints/{endpoint_id}")
        async def update_endpoint(endpoint_id: str, request: EndpointRequest):
            """Update an existing endpoint"""
            try:
                endpoint_data = request.dict()
                result = await self.endpoint_manager.update_endpoint(endpoint_id, endpoint_data)
                return result
            except Exception as e:
                logger.error(f"Update endpoint error: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.delete("/api/endpoints/{endpoint_id}")
        async def delete_endpoint(endpoint_id: str):
            """Delete an endpoint"""
            try:
                result = await self.endpoint_manager.delete_endpoint(endpoint_id)
                return result
            except Exception as e:
                logger.error(f"Delete endpoint error: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.post("/api/endpoints/{endpoint_id}/test")
        async def test_endpoint(endpoint_id: str):
            """Test an endpoint"""
            try:
                result = await self.endpoint_manager.test_endpoint(endpoint_id)
                return result
            except Exception as e:
                logger.error(f"Test endpoint error: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.post("/api/endpoints/generate")
        async def generate_endpoint(request: dict):
            """Generate endpoint using AI"""
            try:
                prompt = request.get("prompt", "")
                result = await self.endpoint_manager.generate_endpoint_with_ai(prompt)
                return result
            except Exception as e:
                logger.error(f"Generate endpoint error: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        # Website management
        @self.app.get("/api/websites")
        async def get_websites():
            """Get all analyzed websites"""
            try:
                return await self.web_scraper.get_websites()
            except Exception as e:
                logger.error(f"Get websites error: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.post("/api/websites/analyze")
        async def analyze_website(request: WebsiteAnalysisRequest, background_tasks: BackgroundTasks):
            """Start website analysis"""
            try:
                analysis_id = await self.web_scraper.start_analysis(request.url)
                background_tasks.add_task(self.web_scraper.analyze_website, request.url, analysis_id)
                return {"analysis_id": analysis_id}
            except Exception as e:
                logger.error(f"Analyze website error: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.get("/api/websites/analysis/{analysis_id}/progress")
        async def get_analysis_progress(analysis_id: str):
            """Get analysis progress"""
            try:
                return await self.web_scraper.get_analysis_progress(analysis_id)
            except Exception as e:
                logger.error(f"Get analysis progress error: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.get("/api/websites/analysis/{analysis_id}/results")
        async def get_analysis_results(analysis_id: str):
            """Get analysis results"""
            try:
                return await self.web_scraper.get_analysis_results(analysis_id)
            except Exception as e:
                logger.error(f"Get analysis results error: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.post("/api/websites")
        async def save_website(request: dict):
            """Save analyzed website"""
            try:
                result = await self.web_scraper.save_website(request)
                return result
            except Exception as e:
                logger.error(f"Save website error: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        # Provider endpoints
        @self.app.get("/api/providers")
        async def get_providers():
            """Get available providers"""
            return {
                "providers": [
                    {"id": "openai", "name": "OpenAI", "models": ["gpt-4", "gpt-3.5-turbo"]},
                    {"id": "anthropic", "name": "Anthropic", "models": ["claude-3-opus", "claude-3-sonnet"]},
                    {"id": "gemini", "name": "Google Gemini", "models": ["gemini-pro", "gemini-pro-vision"]},
                    {"id": "zai", "name": "Z.ai", "models": ["glm-4.5", "glm-4.5v"]},
                    {"id": "codegen", "name": "Codegen", "models": ["codegen-standard", "codegen-advanced"]},
                ]
            }
        
        @self.app.post("/api/providers/{provider}/test")
        async def test_provider(provider: str, request: dict):
            """Test provider connection"""
            try:
                if provider == "zai":
                    api_key = request.get("api_key")
                    zai_provider = ZaiProvider(api_key=api_key)
                    result = await zai_provider.test_connection()
                    return result
                else:
                    # Test other providers through chat handler
                    result = await self.chat_handler.test_provider(provider, request.get("api_key"))
                    return result
            except Exception as e:
                logger.error(f"Test provider error: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        # System endpoints
        @self.app.get("/api/system/stats")
        async def get_system_stats():
            """Get system statistics"""
            return {
                "totalRequests": 0,  # Implement actual stats
                "successfulRequests": 0,
                "failedRequests": 0,
                "averageResponseTime": 0,
                "activeEndpoints": len(await self.endpoint_manager.get_endpoints()),
                "totalWebsites": len(await self.web_scraper.get_websites()),
                "uptime": 0,
            }
        
        @self.app.get("/api/system/health")
        async def health_check():
            """Health check endpoint"""
            return {"status": "healthy", "timestamp": datetime.now().isoformat()}
    
    async def _stream_chat_response(self, request: ChatRequest):
        """Stream chat response"""
        try:
            async for chunk in self.chat_handler.handle_chat_stream(
                message=request.message,
                provider=request.provider,
                model=request.model,
                conversation_history=request.conversation_history
            ):
                yield f"data: {json.dumps(chunk)}\n\n"
            yield "data: [DONE]\n\n"
        except Exception as e:
            logger.error(f"Stream chat error: {e}")
            yield f"data: {json.dumps({'error': str(e)})}\n\n"


def create_api_manager(app: FastAPI) -> APIManager:
    """Create and configure the API manager"""
    return APIManager(app)


# Export for use in main server
__all__ = ['APIManager', 'create_api_manager']

