"""
Main FastAPI application for the Universal AI Endpoint Management System
"""

import asyncio
import logging
import os
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse

from .database import init_database, get_database_manager
from .endpoint_manager import get_endpoint_manager
from .api.endpoints import router as endpoints_router
from .api.chat import router as chat_router
from .api.config import router as config_router

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    logger.info("Starting Universal AI Endpoint Management System...")
    
    try:
        # Initialize database
        init_database()
        logger.info("Database initialized")
        
        # Start endpoint manager
        endpoint_manager = get_endpoint_manager()
        await endpoint_manager.start()
        logger.info("Endpoint Manager started")
        
        yield
        
    except Exception as e:
        logger.error(f"Startup error: {e}")
        raise
    finally:
        # Cleanup
        logger.info("Shutting down...")
        endpoint_manager = get_endpoint_manager()
        await endpoint_manager.stop()
        logger.info("Endpoint Manager stopped")

# Create FastAPI app
app = FastAPI(
    title="Universal AI Endpoint Management System",
    description="Trading bot-style management for AI endpoints with web chat and REST API support",
    version="1.0.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routers
app.include_router(config_router)
app.include_router(endpoints_router)
app.include_router(chat_router)

# Serve static files (for web UI)
if os.path.exists("frontend/static"):
    app.mount("/static", StaticFiles(directory="frontend/static"), name="static")
elif os.path.exists("frontend/dist"):
    app.mount("/static", StaticFiles(directory="frontend/dist"), name="static")

@app.get("/", response_class=HTMLResponse)
async def root():
    """Root endpoint - serve web UI or API info"""
    if os.path.exists("frontend/index.html"):
        with open("frontend/index.html", "r") as f:
            return HTMLResponse(content=f.read())
    elif os.path.exists("frontend/dist/index.html"):
        with open("frontend/dist/index.html", "r") as f:
            return HTMLResponse(content=f.read())
    else:
        return HTMLResponse(content="""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Universal AI Endpoint Manager</title>
            <style>
                body { font-family: Arial, sans-serif; margin: 40px; }
                .container { max-width: 800px; margin: 0 auto; }
                .endpoint { background: #f5f5f5; padding: 15px; margin: 10px 0; border-radius: 5px; }
                .status { padding: 3px 8px; border-radius: 3px; color: white; font-size: 12px; }
                .running { background: #28a745; }
                .stopped { background: #dc3545; }
                .metrics { font-size: 12px; color: #666; margin-top: 5px; }
            </style>
        </head>
        <body>
            <div class="container">
                <h1>🤖 Universal AI Endpoint Manager</h1>
                <p>Trading bot-style management for AI endpoints</p>
                
                <h2>📊 API Documentation</h2>
                <ul>
                    <li><a href="/docs">Interactive API Documentation (Swagger)</a></li>
                    <li><a href="/redoc">Alternative API Documentation (ReDoc)</a></li>
                </ul>
                
                <h2>🔗 API Endpoints</h2>
                <ul>
                    <li><strong>GET /api/endpoints/</strong> - List all endpoints</li>
                    <li><strong>POST /api/endpoints/</strong> - Create new endpoint</li>
                    <li><strong>POST /api/endpoints/{name}/start</strong> - Start endpoint</li>
                    <li><strong>POST /api/endpoints/{name}/stop</strong> - Stop endpoint</li>
                    <li><strong>POST /api/endpoints/{name}/test</strong> - Test endpoint</li>
                    <li><strong>POST /v1/chat/completions</strong> - OpenAI-compatible chat API</li>
                    <li><strong>GET /v1/models</strong> - List available models</li>
                </ul>
                
                <h2>🚀 Quick Start</h2>
                <pre><code># List endpoints
curl http://localhost:8000/api/endpoints/

# Test chat completion
curl -X POST http://localhost:8000/v1/chat/completions \\
  -H "Content-Type: application/json" \\
  -d '{
    "model": "gpt-3.5-turbo",
    "messages": [{"role": "user", "content": "Hello!"}]
  }'</code></pre>
                
                <div id="endpoints"></div>
            </div>
            
            <script>
                // Load endpoints dynamically
                fetch('/api/endpoints/')
                    .then(response => response.json())
                    .then(endpoints => {
                        const container = document.getElementById('endpoints');
                        if (endpoints.length > 0) {
                            container.innerHTML = '<h2>📡 Active Endpoints</h2>' + 
                                endpoints.map(ep => `
                                    <div class="endpoint">
                                        <strong>${ep.name}</strong>
                                        <span class="status ${ep.status}">${ep.status}</span>
                                        <div class="metrics">
                                            Success Rate: ${ep.metrics.success_rate.toFixed(1)}% | 
                                            Requests: ${ep.metrics.total_requests} | 
                                            Avg Response: ${ep.metrics.average_response_time.toFixed(0)}ms
                                        </div>
                                    </div>
                                `).join('');
                        }
                    })
                    .catch(err => console.error('Failed to load endpoints:', err));
            </script>
        </body>
        </html>
        """)

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    try:
        endpoint_manager = get_endpoint_manager()
        endpoints = endpoint_manager.get_active_endpoints()
        
        return {
            "status": "healthy",
            "endpoints_count": len(endpoints),
            "running_endpoints": len([ep for ep in endpoints if ep['status'] == 'running']),
            "timestamp": asyncio.get_event_loop().time()
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/status")
async def system_status():
    """Detailed system status"""
    try:
        endpoint_manager = get_endpoint_manager()
        endpoints = endpoint_manager.get_active_endpoints()
        
        # Calculate aggregate metrics
        total_requests = sum(ep['metrics']['total_requests'] for ep in endpoints)
        total_successful = sum(ep['metrics']['successful_requests'] for ep in endpoints)
        avg_success_rate = (total_successful / total_requests * 100) if total_requests > 0 else 0
        
        return {
            "system": {
                "status": "running" if endpoint_manager.is_running else "stopped",
                "endpoints_total": len(endpoints),
                "endpoints_running": len([ep for ep in endpoints if ep['status'] == 'running']),
                "total_requests": total_requests,
                "average_success_rate": round(avg_success_rate, 2)
            },
            "endpoints": endpoints
        }
    except Exception as e:
        logger.error(f"Status check failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    
    # Get configuration from environment
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", 8000))
    reload = os.getenv("RELOAD", "false").lower() == "true"
    
    logger.info(f"Starting server on {host}:{port}")
    
    uvicorn.run(
        "backend.main:app",
        host=host,
        port=port,
        reload=reload,
        log_level="info"
    )
