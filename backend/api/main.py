"""
Enhanced FastAPI server with Supabase integration and web chat interface
"""
import os
import uuid
import json
import asyncio
from datetime import datetime
from typing import Dict, List, Optional, Any
from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, StreamingResponse
from pydantic import BaseModel
import logging

from ..database import db_manager, EndpointConfig, ChatMessage, Conversation, WebsiteIntegration
from ..services.endpoint_manager import endpoint_manager

logger = logging.getLogger(__name__)

# Pydantic models for API requests
class SupabaseConnectionRequest(BaseModel):
    supabase_url: str
    supabase_key: str

class EndpointCreateRequest(BaseModel):
    name: str
    url: str
    method: str = "POST"
    headers: Dict[str, str] = {}
    model_name: str = "custom-model"
    text_input_selector: str = ""
    send_button_selector: str = ""
    response_selector: str = ""
    variables: Dict[str, Any] = {}
    user_id: str

class EndpointUpdateRequest(BaseModel):
    name: Optional[str] = None
    url: Optional[str] = None
    method: Optional[str] = None
    headers: Optional[Dict[str, str]] = None
    model_name: Optional[str] = None
    text_input_selector: Optional[str] = None
    send_button_selector: Optional[str] = None
    response_selector: Optional[str] = None
    variables: Optional[Dict[str, Any]] = None
    is_active: Optional[bool] = None

class ChatRequest(BaseModel):
    message: str
    conversation_id: Optional[str] = None
    endpoint_id: Optional[str] = None
    user_id: str

class EndpointTestRequest(BaseModel):
    endpoint_id: str
    test_data: Optional[Dict[str, Any]] = None

class WebInterfaceTestRequest(BaseModel):
    endpoint_id: str
    message: str

class AIEndpointCreateRequest(BaseModel):
    description: str
    user_id: str

class WebsiteDiscoveryRequest(BaseModel):
    url: str

# Create FastAPI app
app = FastAPI(
    title="OpenCodegen Enhanced API",
    description="Enhanced OpenAI Codegen Adapter with Supabase integration and web chat interface",
    version="2.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# WebSocket connection manager
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def send_personal_message(self, message: str, websocket: WebSocket):
        await websocket.send_text(message)

    async def broadcast(self, message: str):
        for connection in self.active_connections:
            await connection.send_text(message)

manager = ConnectionManager()

# Startup and shutdown events
@app.on_event("startup")
async def startup_event():
    """Initialize services on startup"""
    await endpoint_manager.initialize()
    logger.info("Enhanced OpenCodegen API server started")

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    await endpoint_manager.cleanup()
    logger.info("Enhanced OpenCodegen API server stopped")

# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "supabase_connected": db_manager.is_connected()
    }

# Supabase connection endpoints
@app.post("/api/supabase/connect")
async def connect_supabase(request: SupabaseConnectionRequest):
    """Connect to Supabase database"""
    try:
        success = await db_manager.connect(request.supabase_url, request.supabase_key)
        if success:
            return {"success": True, "message": "Successfully connected to Supabase"}
        else:
            raise HTTPException(status_code=400, detail="Failed to connect to Supabase")
    except Exception as e:
        logger.error(f"Supabase connection error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/supabase/status")
async def supabase_status():
    """Get Supabase connection status"""
    return {
        "connected": db_manager.is_connected(),
        "timestamp": datetime.utcnow().isoformat()
    }

# Endpoint management endpoints
@app.post("/api/endpoints")
async def create_endpoint(request: EndpointCreateRequest):
    """Create a new endpoint configuration"""
    try:
        endpoint = EndpointConfig(
            id=str(uuid.uuid4()),
            name=request.name,
            url=request.url,
            method=request.method,
            headers=request.headers,
            model_name=request.model_name,
            text_input_selector=request.text_input_selector,
            send_button_selector=request.send_button_selector,
            response_selector=request.response_selector,
            variables=request.variables,
            user_id=request.user_id
        )
        
        success = await db_manager.create_endpoint(endpoint)
        if success:
            return {"success": True, "endpoint": endpoint.__dict__}
        else:
            raise HTTPException(status_code=400, detail="Failed to create endpoint")
    except Exception as e:
        logger.error(f"Endpoint creation error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/endpoints")
async def list_endpoints(user_id: Optional[str] = None):
    """List all endpoints, optionally filtered by user"""
    try:
        endpoints = await db_manager.list_endpoints(user_id)
        return {"endpoints": [endpoint.__dict__ for endpoint in endpoints]}
    except Exception as e:
        logger.error(f"Endpoint listing error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/endpoints/{endpoint_id}")
async def get_endpoint(endpoint_id: str):
    """Get a specific endpoint by ID"""
    try:
        endpoint = await db_manager.get_endpoint(endpoint_id)
        if endpoint:
            return {"endpoint": endpoint.__dict__}
        else:
            raise HTTPException(status_code=404, detail="Endpoint not found")
    except Exception as e:
        logger.error(f"Endpoint retrieval error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.put("/api/endpoints/{endpoint_id}")
async def update_endpoint(endpoint_id: str, request: EndpointUpdateRequest):
    """Update an existing endpoint"""
    try:
        # Get existing endpoint
        endpoint = await db_manager.get_endpoint(endpoint_id)
        if not endpoint:
            raise HTTPException(status_code=404, detail="Endpoint not found")
        
        # Update fields
        if request.name is not None:
            endpoint.name = request.name
        if request.url is not None:
            endpoint.url = request.url
        if request.method is not None:
            endpoint.method = request.method
        if request.headers is not None:
            endpoint.headers = request.headers
        if request.model_name is not None:
            endpoint.model_name = request.model_name
        if request.text_input_selector is not None:
            endpoint.text_input_selector = request.text_input_selector
        if request.send_button_selector is not None:
            endpoint.send_button_selector = request.send_button_selector
        if request.response_selector is not None:
            endpoint.response_selector = request.response_selector
        if request.variables is not None:
            endpoint.variables = request.variables
        if request.is_active is not None:
            endpoint.is_active = request.is_active
        
        success = await db_manager.update_endpoint(endpoint)
        if success:
            return {"success": True, "endpoint": endpoint.__dict__}
        else:
            raise HTTPException(status_code=400, detail="Failed to update endpoint")
    except Exception as e:
        logger.error(f"Endpoint update error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/api/endpoints/{endpoint_id}")
async def delete_endpoint(endpoint_id: str):
    """Delete an endpoint"""
    try:
        success = await db_manager.delete_endpoint(endpoint_id)
        if success:
            return {"success": True, "message": "Endpoint deleted successfully"}
        else:
            raise HTTPException(status_code=404, detail="Endpoint not found")
    except Exception as e:
        logger.error(f"Endpoint deletion error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# AI-assisted endpoint creation
@app.post("/api/endpoints/ai-create")
async def ai_create_endpoint(request: AIEndpointCreateRequest):
    """Create an endpoint using AI from natural language description"""
    try:
        endpoint = await endpoint_manager.create_endpoint_from_description(
            request.description, 
            request.user_id
        )
        if endpoint:
            return {"success": True, "endpoint": endpoint.__dict__}
        else:
            raise HTTPException(status_code=400, detail="Failed to create endpoint from description")
    except Exception as e:
        logger.error(f"AI endpoint creation error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Website discovery
@app.post("/api/websites/discover")
async def discover_website_endpoints(request: WebsiteDiscoveryRequest):
    """Discover API endpoints from a website"""
    try:
        endpoints = await endpoint_manager.discover_website_endpoints(request.url)
        return {"endpoints": endpoints}
    except Exception as e:
        logger.error(f"Website discovery error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Endpoint testing
@app.post("/api/endpoints/test")
async def test_endpoint(request: EndpointTestRequest):
    """Test an endpoint configuration"""
    try:
        endpoint = await db_manager.get_endpoint(request.endpoint_id)
        if not endpoint:
            raise HTTPException(status_code=404, detail="Endpoint not found")
        
        result = await endpoint_manager.test_endpoint(endpoint, request.test_data)
        return result
    except Exception as e:
        logger.error(f"Endpoint testing error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/endpoints/test-web")
async def test_web_interface(request: WebInterfaceTestRequest):
    """Test web interface interaction"""
    try:
        endpoint = await db_manager.get_endpoint(request.endpoint_id)
        if not endpoint:
            raise HTTPException(status_code=404, detail="Endpoint not found")
        
        result = await endpoint_manager.test_web_interface(endpoint, request.message)
        return result
    except Exception as e:
        logger.error(f"Web interface testing error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Chat endpoints
@app.post("/api/chat")
async def send_chat_message(request: ChatRequest):
    """Send a chat message"""
    try:
        # Create conversation if not provided
        conversation_id = request.conversation_id
        if not conversation_id:
            conversation_id = str(uuid.uuid4())
            conversation = Conversation(
                id=conversation_id,
                title="New Conversation",
                user_id=request.user_id
            )
            await db_manager.create_conversation(conversation)
        
        # Add user message
        user_message = ChatMessage(
            id=str(uuid.uuid4()),
            conversation_id=conversation_id,
            role="user",
            content=request.message,
            endpoint_id=request.endpoint_id
        )
        await db_manager.add_message(user_message)
        
        # Process message based on endpoint
        if request.endpoint_id:
            endpoint = await db_manager.get_endpoint(request.endpoint_id)
            if endpoint:
                # Test the endpoint with the message
                if endpoint.text_input_selector:
                    # Use web interface
                    result = await endpoint_manager.test_web_interface(endpoint, request.message)
                    response_content = result.get("response", "No response received")
                else:
                    # Use API endpoint
                    result = await endpoint_manager.test_endpoint(endpoint, {"message": request.message})
                    response_content = result.get("response_data", "No response received")
                
                # Add assistant message
                assistant_message = ChatMessage(
                    id=str(uuid.uuid4()),
                    conversation_id=conversation_id,
                    role="assistant",
                    content=response_content,
                    endpoint_id=request.endpoint_id
                )
                await db_manager.add_message(assistant_message)
                
                return {
                    "conversation_id": conversation_id,
                    "response": response_content,
                    "endpoint_used": endpoint.name
                }
        
        # Default response if no endpoint specified
        return {
            "conversation_id": conversation_id,
            "response": "Message received. Please specify an endpoint to get a response.",
            "endpoint_used": None
        }
        
    except Exception as e:
        logger.error(f"Chat error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/conversations/{conversation_id}/messages")
async def get_conversation_messages(conversation_id: str):
    """Get all messages for a conversation"""
    try:
        messages = await db_manager.get_conversation_messages(conversation_id)
        return {"messages": [message.__dict__ for message in messages]}
    except Exception as e:
        logger.error(f"Message retrieval error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# WebSocket endpoint for real-time chat
@app.websocket("/ws/chat")
async def websocket_chat_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time chat"""
    await manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            message_data = json.loads(data)
            
            # Process the message
            # This is a simplified version - you'd want to integrate with your chat logic
            response = {
                "type": "message",
                "content": f"Echo: {message_data.get('message', '')}",
                "timestamp": datetime.utcnow().isoformat()
            }
            
            await manager.send_personal_message(json.dumps(response), websocket)
            
    except WebSocketDisconnect:
        manager.disconnect(websocket)

# Serve static files (React frontend)
app.mount("/static", StaticFiles(directory="frontend/build/static"), name="static")

# Serve React app
@app.get("/", response_class=HTMLResponse)
async def serve_react_app():
    """Serve the React frontend"""
    try:
        with open("frontend/build/index.html", "r") as f:
            return HTMLResponse(content=f.read())
    except FileNotFoundError:
        return HTMLResponse(content="""
        <html>
            <head><title>OpenCodegen Enhanced</title></head>
            <body>
                <h1>OpenCodegen Enhanced API</h1>
                <p>Frontend not built yet. Please run: <code>cd frontend && npm run build</code></p>
                <p>API Documentation: <a href="/docs">/docs</a></p>
            </body>
        </html>
        """)

# Catch-all route for React Router
@app.get("/{path:path}", response_class=HTMLResponse)
async def serve_react_app_routes(path: str):
    """Serve React app for all routes (SPA routing)"""
    return await serve_react_app()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
