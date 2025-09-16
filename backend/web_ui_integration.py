"""
Web UI Integration for OpenAI Codegen Adapter

This module integrates the web UI API manager with the existing FastAPI server,
providing a seamless experience between the OpenAI API interception and the
management interface.
"""

import os
import logging
from pathlib import Path
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from backend.api_manager import create_api_manager

logger = logging.getLogger(__name__)

def integrate_web_ui(app: FastAPI) -> None:
    """
    Integrate the web UI with the existing FastAPI application
    
    Args:
        app: The existing FastAPI application instance
    """
    
    # Create and configure the API manager
    api_manager = create_api_manager(app)
    
    # Serve static files from the built frontend
    frontend_build_path = Path(__file__).parent.parent / "frontend" / "build"
    
    if frontend_build_path.exists():
        logger.info(f"Serving frontend from: {frontend_build_path}")
        
        # Mount static files
        app.mount(
            "/static",
            StaticFiles(directory=str(frontend_build_path / "static")),
            name="static"
        )
        
        # Serve the React app for all non-API routes
        @app.get("/")
        async def serve_frontend():
            """Serve the main React application"""
            return FileResponse(str(frontend_build_path / "index.html"))
        
        @app.get("/{path:path}")
        async def serve_frontend_routes(path: str):
            """Serve React app for all frontend routes"""
            # Don't intercept API routes
            if path.startswith("api/") or path.startswith("v1/"):
                return {"error": "Not found"}
            
            # Check if it's a static file request
            static_file = frontend_build_path / path
            if static_file.exists() and static_file.is_file():
                return FileResponse(str(static_file))
            
            # Otherwise serve the React app (for client-side routing)
            return FileResponse(str(frontend_build_path / "index.html"))
        
        logger.info("Web UI integration completed successfully")
    else:
        logger.warning(f"Frontend build directory not found: {frontend_build_path}")
        logger.warning("Web UI will not be available. Run 'npm run build' in the frontend directory.")
        
        # Add a simple endpoint to indicate web UI is not available
        @app.get("/")
        async def no_frontend():
            return {
                "message": "OpenAI Codegen Adapter API Server",
                "status": "running",
                "web_ui": "not available",
                "note": "Run 'npm run build' in the frontend directory to enable the web UI"
            }


def setup_web_ui_environment():
    """Setup environment variables for web UI integration"""
    
    # Set default environment variables if not already set
    env_defaults = {
        "ENABLE_WEB_UI": "true",
        "ENABLE_CORS": "true",
        "WEB_UI_PORT": "3000",
        "API_PORT": "8000",
    }
    
    for key, default_value in env_defaults.items():
        if key not in os.environ:
            os.environ[key] = default_value
    
    logger.info("Web UI environment configured")


# Export integration function
__all__ = ['integrate_web_ui', 'setup_web_ui_environment']

