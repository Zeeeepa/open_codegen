"""
Universal AI Endpoint Manager Server Integration

Enhanced FastAPI server that integrates the Universal AI Endpoint Manager
with the existing open_codegen architecture. Provides trading bot-style
endpoint management with web UI and API endpoints.
"""

import logging
import asyncio
from datetime import datetime
from typing import Dict, List, Optional, Any
from fastapi import FastAPI, HTTPException, Request, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles

# Import existing open_codegen components
from backend.adapter.enhanced_server import app as base_app
from backend.adapter.config import get_enhanced_codegen_config, get_server_config
from backend.adapter.auth import get_auth

# Import Universal AI Endpoint Manager components
from backend.endpoint_manager.core.manager import UniversalEndpointManager
from backend.endpoint_manager.models.endpoint import (
    EndpointConfig, EndpointStatus, EndpointType, HealthStatus,
    EndpointCredentials, BrowserConfig
)
from backend.endpoint_manager.schemas.response import StandardResponse

logger = logging.getLogger(__name__)

# Initialize Universal Endpoint Manager
endpoint_manager = UniversalEndpointManager()

# Enhanced FastAPI app with endpoint management
app = FastAPI(
    title="Universal AI Endpoint Manager",
    description="Trading bot-style AI endpoint management with open_codegen integration",
    version="2.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount existing open_codegen app
app.mount("/api/v1", base_app, name="codegen_api")

# Startup and shutdown events
@app.on_event("startup")
async def startup_event():
    """Initialize the Universal Endpoint Manager on startup"""
    logger.info("Starting Universal AI Endpoint Manager...")
    await endpoint_manager.start()
    
    # Add default endpoints from existing configuration
    await _initialize_default_endpoints()

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    logger.info("Shutting down Universal AI Endpoint Manager...")
    await endpoint_manager.stop()

# Universal Endpoint Manager API Routes

@app.get("/endpoints", response_model=List[Dict[str, Any]])
async def list_endpoints(status: Optional[str] = None):
    """List all endpoints with their status - trading bot style"""
    try:
        status_filter = EndpointStatus(status) if status else None
        endpoints = await endpoint_manager.list_endpoints(status_filter)
        return endpoints
    except Exception as e:
        logger.error(f"Error listing endpoints: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/endpoints", response_model=Dict[str, Any])
async def add_endpoint(endpoint_data: Dict[str, Any]):
    """Add a new endpoint - similar to adding a trading position"""
    try:
        # Create endpoint configuration
        config = EndpointConfig.from_dict(endpoint_data)
        
        # Add endpoint
        success = await endpoint_manager.add_endpoint(config)
        if not success:
            raise HTTPException(status_code=400, detail="Failed to add endpoint")
        
        return {"success": True, "endpoint_id": config.id, "message": "Endpoint added successfully"}
    except Exception as e:
        logger.error(f"Error adding endpoint: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/endpoints/{endpoint_id}", response_model=Dict[str, Any])
async def get_endpoint_status(endpoint_id: str):
    """Get detailed status of a specific endpoint"""
    try:
        status = await endpoint_manager.get_endpoint_status(endpoint_id)
        if not status:
            raise HTTPException(status_code=404, detail="Endpoint not found")
        return status
    except Exception as e:
        logger.error(f"Error getting endpoint status: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/endpoints/{endpoint_id}/start")
async def start_endpoint(endpoint_id: str):
    """Start an endpoint - like starting a trading position"""
    try:
        success = await endpoint_manager.start_endpoint(endpoint_id)
        if not success:
            raise HTTPException(status_code=400, detail="Failed to start endpoint")
        return {"success": True, "message": "Endpoint started successfully"}
    except Exception as e:
        logger.error(f"Error starting endpoint: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/endpoints/{endpoint_id}/stop")
async def stop_endpoint(endpoint_id: str):
    """Stop an endpoint - like closing a trading position"""
    try:
        success = await endpoint_manager.stop_endpoint(endpoint_id)
        if not success:
            raise HTTPException(status_code=400, detail="Failed to stop endpoint")
        return {"success": True, "message": "Endpoint stopped successfully"}
    except Exception as e:
        logger.error(f"Error stopping endpoint: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/endpoints/{endpoint_id}")
async def remove_endpoint(endpoint_id: str):
    """Remove an endpoint"""
    try:
        success = await endpoint_manager.remove_endpoint(endpoint_id)
        if not success:
            raise HTTPException(status_code=400, detail="Failed to remove endpoint")
        return {"success": True, "message": "Endpoint removed successfully"}
    except Exception as e:
        logger.error(f"Error removing endpoint: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/endpoints/{endpoint_id}/chat")
async def chat_with_endpoint(endpoint_id: str, request_data: Dict[str, Any]):
    """Send a chat request to a specific endpoint"""
    try:
        prompt = request_data.get("prompt", "")
        if not prompt:
            raise HTTPException(status_code=400, detail="Prompt is required")
        
        response = await endpoint_manager.send_request(endpoint_id, prompt, **request_data)
        return response.to_dict()
    except Exception as e:
        logger.error(f"Error sending chat request: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/system/metrics")
async def get_system_metrics():
    """Get overall system metrics - trading bot style dashboard"""
    try:
        metrics = await endpoint_manager.get_system_metrics()
        return metrics
    except Exception as e:
        logger.error(f"Error getting system metrics: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Web UI Routes
@app.get("/", response_class=HTMLResponse)
async def dashboard():
    """Main dashboard - trading bot style interface"""
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Universal AI Endpoint Manager</title>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <style>
            body { font-family: Arial, sans-serif; margin: 0; padding: 20px; background: #f5f5f5; }
            .container { max-width: 1200px; margin: 0 auto; }
            .header { background: #2c3e50; color: white; padding: 20px; border-radius: 8px; margin-bottom: 20px; }
            .metrics { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 15px; margin-bottom: 20px; }
            .metric-card { background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
            .metric-value { font-size: 2em; font-weight: bold; color: #3498db; }
            .metric-label { color: #7f8c8d; margin-top: 5px; }
            .endpoints { background: white; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
            .endpoint-header { background: #34495e; color: white; padding: 15px; border-radius: 8px 8px 0 0; }
            .endpoint-item { padding: 15px; border-bottom: 1px solid #ecf0f1; display: flex; justify-content: space-between; align-items: center; }
            .endpoint-name { font-weight: bold; }
            .endpoint-status { padding: 5px 10px; border-radius: 4px; color: white; font-size: 0.8em; }
            .status-running { background: #27ae60; }
            .status-stopped { background: #e74c3c; }
            .status-error { background: #e67e22; }
            .controls { display: flex; gap: 10px; }
            .btn { padding: 8px 16px; border: none; border-radius: 4px; cursor: pointer; font-size: 0.9em; }
            .btn-start { background: #27ae60; color: white; }
            .btn-stop { background: #e74c3c; color: white; }
            .btn-test { background: #3498db; color: white; }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>🚀 Universal AI Endpoint Manager</h1>
                <p>Trading bot-style AI endpoint management with real-time monitoring</p>
            </div>
            
            <div class="metrics" id="metrics">
                <!-- Metrics will be loaded here -->
            </div>
            
            <div class="endpoints">
                <div class="endpoint-header">
                    <h2>📊 Active Endpoints Portfolio</h2>
                </div>
                <div id="endpoints-list">
                    <!-- Endpoints will be loaded here -->
                </div>
            </div>
        </div>
        
        <script>
            async function loadMetrics() {
                try {
                    const response = await fetch('/system/metrics');
                    const metrics = await response.json();
                    
                    document.getElementById('metrics').innerHTML = `
                        <div class="metric-card">
                            <div class="metric-value">${metrics.total_endpoints}</div>
                            <div class="metric-label">Total Endpoints</div>
                        </div>
                        <div class="metric-card">
                            <div class="metric-value">${metrics.running_endpoints}</div>
                            <div class="metric-label">Running</div>
                        </div>
                        <div class="metric-card">
                            <div class="metric-value">${metrics.success_rate.toFixed(1)}%</div>
                            <div class="metric-label">Success Rate</div>
                        </div>
                        <div class="metric-card">
                            <div class="metric-value">${metrics.requests_per_second.toFixed(2)}</div>
                            <div class="metric-label">Req/sec</div>
                        </div>
                    `;
                } catch (error) {
                    console.error('Error loading metrics:', error);
                }
            }
            
            async function loadEndpoints() {
                try {
                    const response = await fetch('/endpoints');
                    const endpoints = await response.json();
                    
                    const endpointsList = document.getElementById('endpoints-list');
                    endpointsList.innerHTML = endpoints.map(endpoint => {
                        const config = endpoint.config;
                        const statusClass = `status-${config.status}`;
                        
                        return `
                            <div class="endpoint-item">
                                <div>
                                    <div class="endpoint-name">${config.display_name}</div>
                                    <div style="color: #7f8c8d; font-size: 0.9em;">
                                        ${config.model_identifier} • ${config.endpoint_type}
                                    </div>
                                </div>
                                <div style="display: flex; align-items: center; gap: 15px;">
                                    <div>
                                        <div style="font-size: 0.8em; color: #7f8c8d;">Requests: ${config.metrics.total_requests}</div>
                                        <div style="font-size: 0.8em; color: #7f8c8d;">Success: ${config.metrics.success_rate.toFixed(1)}%</div>
                                    </div>
                                    <span class="endpoint-status ${statusClass}">${config.status.toUpperCase()}</span>
                                    <div class="controls">
                                        <button class="btn btn-start" onclick="startEndpoint('${config.id}')">Start</button>
                                        <button class="btn btn-stop" onclick="stopEndpoint('${config.id}')">Stop</button>
                                        <button class="btn btn-test" onclick="testEndpoint('${config.id}')">Test</button>
                                    </div>
                                </div>
                            </div>
                        `;
                    }).join('');
                } catch (error) {
                    console.error('Error loading endpoints:', error);
                }
            }
            
            async function startEndpoint(endpointId) {
                try {
                    await fetch(`/endpoints/${endpointId}/start`, { method: 'POST' });
                    loadEndpoints();
                } catch (error) {
                    console.error('Error starting endpoint:', error);
                }
            }
            
            async function stopEndpoint(endpointId) {
                try {
                    await fetch(`/endpoints/${endpointId}/stop`, { method: 'POST' });
                    loadEndpoints();
                } catch (error) {
                    console.error('Error stopping endpoint:', error);
                }
            }
            
            async function testEndpoint(endpointId) {
                const prompt = prompt('Enter test prompt:', 'Hello, how are you?');
                if (prompt) {
                    try {
                        const response = await fetch(`/endpoints/${endpointId}/chat`, {
                            method: 'POST',
                            headers: { 'Content-Type': 'application/json' },
                            body: JSON.stringify({ prompt })
                        });
                        const result = await response.json();
                        alert(`Response: ${result.response.content}`);
                    } catch (error) {
                        console.error('Error testing endpoint:', error);
                        alert('Error testing endpoint');
                    }
                }
            }
            
            // Load data on page load
            loadMetrics();
            loadEndpoints();
            
            // Refresh every 30 seconds
            setInterval(() => {
                loadMetrics();
                loadEndpoints();
            }, 30000);
        </script>
    </body>
    </html>
    """

# Helper functions
async def _initialize_default_endpoints():
    """Initialize default endpoints from existing open_codegen configuration"""
    try:
        # Add Codegen API endpoint
        codegen_config = EndpointConfig(
            name="codegen_api",
            display_name="Codegen API",
            endpoint_type=EndpointType.CODEGEN_API,
            url="https://codegen-sh--rest-api.modal.run",
            model_name="codegen-standard",
            default_model="codegen-standard",
            supported_models=["codegen-standard", "codegen-advanced", "codegen-premium"],
            priority=10,
            auto_restart=True
        )
        await endpoint_manager.add_endpoint(codegen_config)
        
        # Add OpenAI API endpoint (if configured)
        openai_config = EndpointConfig(
            name="openai_api",
            display_name="OpenAI API",
            endpoint_type=EndpointType.OPENAI_API,
            url="https://api.openai.com/v1",
            model_name="gpt-4",
            default_model="gpt-4",
            supported_models=["gpt-3.5-turbo", "gpt-4", "gpt-4-turbo"],
            priority=8,
            auto_restart=True
        )
        await endpoint_manager.add_endpoint(openai_config)
        
        logger.info("Default endpoints initialized")
        
    except Exception as e:
        logger.error(f"Error initializing default endpoints: {e}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
