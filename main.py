#!/usr/bin/env python3
"""
AI Endpoint Orchestrator - Main Application
Universal AI endpoint management system with OpenAI-compatible API
"""

import os
import sys
import logging
from pathlib import Path

# Add backend to Python path
backend_path = Path(__file__).parent / "backend"
sys.path.insert(0, str(backend_path))

from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
import uvicorn

# Import our modules
from adapter.models import ChatRequest, ChatResponse
from api.config import router as config_router
from middleware.openai_proxy import OpenAIProxyMiddleware

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="AI Endpoint Orchestrator",
    description="Universal AI endpoint management system with OpenAI-compatible API",
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add OpenAI Proxy Middleware for API interception
proxy_middleware = OpenAIProxyMiddleware()
app.middleware("http")(proxy_middleware)

# Include API routers
app.include_router(config_router)

# Mount static files for frontend
try:
    app.mount("/static", StaticFiles(directory="frontend/static"), name="static")
    logger.info("✅ Static files mounted successfully")
except Exception as e:
    logger.warning(f"⚠️ Failed to mount static files: {e}")

# Default endpoint configurations
DEFAULT_ENDPOINTS = {
    "zai-web": {
        "name": "Z.AI Web Chat",
        "provider_type": "web_chat",
        "base_url": "https://chat.z.ai",
        "importance": 100,  # Highest importance
        "model": "glm-4.5v",
        "enabled": True,
        "config": {
            "interface_elements": {
                "text_input": "textarea[placeholder*='message'], input[type='text']",
                "send_button": "button[type='submit'], button:contains('Send')",
                "response_area": ".message-content, .response-text",
                "new_conversation": "button:contains('New'), .new-chat-button"
            },
            "browser_settings": {
                "headless": False,
                "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                "viewport": {"width": 1920, "height": 1080}
            }
        }
    },
    "codegen-api": {
        "name": "Codegen API",
        "provider_type": "rest_api", 
        "base_url": "https://api.codegen.com",
        "importance": 90,  # High importance
        "model": "codegen-latest",
        "enabled": True,
        "config": {
            "headers": {
                "Content-Type": "application/json"
            },
            "timeout": 30,
            "max_retries": 3
        }
    }
}

# In-memory endpoint storage (replace with database in production)
active_endpoints = DEFAULT_ENDPOINTS.copy()

@app.get("/", response_class=HTMLResponse)
async def dashboard():
    """Serve the main dashboard"""
    try:
        with open("frontend/index.html", "r") as f:
            return HTMLResponse(content=f.read())
    except FileNotFoundError:
        return HTMLResponse(content="""
        <html>
            <head><title>AI Endpoint Orchestrator</title></head>
            <body>
                <h1>AI Endpoint Orchestrator</h1>
                <p>Dashboard not found. Please ensure frontend files are available.</p>
                <p><a href="/docs">View API Documentation</a></p>
            </body>
        </html>
        """)

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "version": "2.0.0",
        "endpoints": len(active_endpoints),
        "active_endpoints": [name for name, config in active_endpoints.items() if config.get("enabled", False)]
    }

@app.post("/v1/chat/completions")
async def chat_completions(request: ChatRequest, http_request: Request):
    """
    OpenAI-compatible chat completions endpoint with intelligent routing
    
    Supports:
    - Model-based routing: "zai-web", "codegen-api", or custom endpoint names
    - Importance-based routing: Higher numbers get priority
    - Automatic fallback to default endpoints
    """
    try:
        logger.info(f"🚀 Chat completion request: model={request.model}")
        
        # Determine target endpoint
        target_endpoint = await get_target_endpoint(request.model)
        
        if not target_endpoint:
            raise HTTPException(
                status_code=400, 
                detail=f"No available endpoint for model: {request.model}"
            )
        
        logger.info(f"📍 Routing to endpoint: {target_endpoint['name']}")
        
        # Route to appropriate handler based on provider type
        if target_endpoint["provider_type"] == "web_chat":
            return await handle_web_chat_request(request, target_endpoint)
        elif target_endpoint["provider_type"] == "rest_api":
            return await handle_rest_api_request(request, target_endpoint)
        else:
            raise HTTPException(
                status_code=500,
                detail=f"Unsupported provider type: {target_endpoint['provider_type']}"
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error in chat completion: {e}")
        raise HTTPException(status_code=500, detail=str(e))

async def get_target_endpoint(model: str):
    """
    Get target endpoint based on model name or importance level
    
    Priority:
    1. Exact model name match
    2. Importance level (if model is numeric)
    3. Highest importance available endpoint
    """
    
    # Direct model name match
    if model in active_endpoints and active_endpoints[model].get("enabled", False):
        return active_endpoints[model]
    
    # Check if model is an importance level (numeric)
    try:
        importance_level = int(model)
        # Find endpoint with matching or closest importance level
        available_endpoints = [
            (name, config) for name, config in active_endpoints.items() 
            if config.get("enabled", False)
        ]
        
        # Sort by importance (highest first)
        available_endpoints.sort(key=lambda x: x[1].get("importance", 0), reverse=True)
        
        # Find endpoint with importance >= requested level
        for name, config in available_endpoints:
            if config.get("importance", 0) >= importance_level:
                return config
                
        # If no match, return highest importance endpoint
        if available_endpoints:
            return available_endpoints[0][1]
            
    except ValueError:
        pass  # Not a numeric importance level
    
    # Fallback to highest importance endpoint
    available_endpoints = [
        (name, config) for name, config in active_endpoints.items() 
        if config.get("enabled", False)
    ]
    
    if available_endpoints:
        # Sort by importance and return highest
        available_endpoints.sort(key=lambda x: x[1].get("importance", 0), reverse=True)
        return available_endpoints[0][1]
    
    return None

async def handle_web_chat_request(request: ChatRequest, endpoint_config: dict):
    """Handle web chat endpoint requests"""
    # This would integrate with browser automation
    # For now, return a mock response
    
    logger.info(f"🌐 Handling web chat request for {endpoint_config['name']}")
    
    # Extract the user message
    user_message = ""
    if request.messages:
        user_message = request.messages[-1].content
    
    # Mock response (replace with actual browser automation)
    mock_response = f"Response from {endpoint_config['name']}: I received your message '{user_message}'. This is a mock response - browser automation will be implemented."
    
    return ChatResponse(
        id=f"chatcmpl-{hash(user_message) % 1000000}",
        object="chat.completion",
        created=1234567890,
        model=request.model,
        choices=[{
            "index": 0,
            "message": {
                "role": "assistant",
                "content": mock_response
            },
            "finish_reason": "stop"
        }],
        usage={
            "prompt_tokens": len(user_message.split()),
            "completion_tokens": len(mock_response.split()),
            "total_tokens": len(user_message.split()) + len(mock_response.split())
        }
    )

async def handle_rest_api_request(request: ChatRequest, endpoint_config: dict):
    """Handle REST API endpoint requests"""
    # This would make actual API calls
    # For now, return a mock response
    
    logger.info(f"🔗 Handling REST API request for {endpoint_config['name']}")
    
    # Extract the user message
    user_message = ""
    if request.messages:
        user_message = request.messages[-1].content
    
    # Mock response (replace with actual API calls)
    mock_response = f"Response from {endpoint_config['name']} API: I received your message '{user_message}'. This is a mock response - actual API integration will be implemented."
    
    return ChatResponse(
        id=f"chatcmpl-{hash(user_message) % 1000000}",
        object="chat.completion", 
        created=1234567890,
        model=request.model,
        choices=[{
            "index": 0,
            "message": {
                "role": "assistant",
                "content": mock_response
            },
            "finish_reason": "stop"
        }],
        usage={
            "prompt_tokens": len(user_message.split()),
            "completion_tokens": len(mock_response.split()),
            "total_tokens": len(user_message.split()) + len(mock_response.split())
        }
    )

@app.post("/api/endpoints")
async def create_endpoint(endpoint_data: dict):
    """
    Create a new endpoint dynamically
    
    Supports adding any web chat or REST API endpoint
    """
    try:
        name = endpoint_data.get("name")
        if not name:
            raise HTTPException(status_code=400, detail="Endpoint name is required")
        
        if name in active_endpoints:
            raise HTTPException(status_code=400, detail=f"Endpoint {name} already exists")
        
        # Set default values
        endpoint_config = {
            "name": name,
            "provider_type": endpoint_data.get("provider_type", "web_chat"),
            "base_url": endpoint_data.get("base_url", ""),
            "importance": endpoint_data.get("importance", 50),
            "model": endpoint_data.get("model", name),
            "enabled": endpoint_data.get("enabled", True),
            "config": endpoint_data.get("config", {})
        }
        
        # Add to active endpoints
        active_endpoints[name] = endpoint_config
        
        logger.info(f"✅ Created endpoint: {name}")
        
        return {
            "status": "success",
            "message": f"Endpoint {name} created successfully",
            "endpoint": endpoint_config
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error creating endpoint: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/endpoints")
async def list_endpoints():
    """List all configured endpoints"""
    return {
        "endpoints": active_endpoints,
        "total": len(active_endpoints),
        "active": len([ep for ep in active_endpoints.values() if ep.get("enabled", False)])
    }

@app.delete("/api/endpoints/{endpoint_name}")
async def delete_endpoint(endpoint_name: str):
    """Delete an endpoint"""
    if endpoint_name not in active_endpoints:
        raise HTTPException(status_code=404, detail=f"Endpoint {endpoint_name} not found")
    
    del active_endpoints[endpoint_name]
    logger.info(f"🗑️ Deleted endpoint: {endpoint_name}")
    
    return {"status": "success", "message": f"Endpoint {endpoint_name} deleted"}

if __name__ == "__main__":
    print("🚀 Starting AI Endpoint Orchestrator...")
    print("📊 Dashboard: http://localhost:8000")
    print("📚 API Docs: http://localhost:8000/docs")
    print("🔗 OpenAI Compatible: http://localhost:8000/v1/chat/completions")
    
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
