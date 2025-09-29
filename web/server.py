"""
Web server for the Universal AI API Gateway
"""

import asyncio
import logging
from pathlib import Path
from typing import Dict, Any

import uvicorn
from fastapi import FastAPI, Request, HTTPException, Depends
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse

from config.config_manager import ConfigManager
from gateway.api_gateway import APIGateway
from web.routes import setup_routes

logger = logging.getLogger(__name__)

class WebServer:
    """Main web server for the Universal AI API Gateway."""
    
    def __init__(self, api_gateway=None):
        self.config_manager = ConfigManager()
        self.config = self.config_manager.load_config()
        self.api_gateway = api_gateway  # Use provided API gateway
        self.app = self._create_app()
        
    def _create_app(self) -> FastAPI:
        """Create FastAPI application."""
        
        app = FastAPI(
            title="Universal AI API Gateway",
            description="Intercepts OpenAI/Gemini/Anthropic API calls and routes through 9 providers",
            version="1.0.0",
            docs_url="/docs",
            redoc_url="/redoc"
        )
        
        # Add CORS middleware
        app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
        
        # Setup static files
        static_dir = Path("web/static")
        static_dir.mkdir(parents=True, exist_ok=True)
        app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")
        
        # Setup templates
        template_dir = Path("web/templates")
        template_dir.mkdir(parents=True, exist_ok=True)
        templates = Jinja2Templates(directory=str(template_dir))
        
        # Initialize API Gateway if not provided
        if not self.api_gateway:
            self.api_gateway = APIGateway(self.config)
        
        # Setup routes
        setup_routes(app, templates, self.api_gateway, self.config_manager)
        
        return app
    
    async def run(self):
        """Run the web server."""
        
        server_config = self.config.get("server", {})
        
        config = uvicorn.Config(
            app=self.app,
            host=server_config.get("host", "0.0.0.0"),
            port=server_config.get("port", 8000),
            workers=server_config.get("workers", 1),
            reload=server_config.get("reload", False),
            log_level="info"
        )
        
        server = uvicorn.Server(config)
        await server.serve()
