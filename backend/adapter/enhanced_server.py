"""
Enhanced FastAPI server with model selection and prompt template support.
"""

import logging
import traceback
import time
from datetime import datetime
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles

from backend.adapter.models import (
    ChatRequest, TextRequest, ChatResponse, TextResponse,
    ErrorResponse, ErrorDetail, AnthropicRequest, AnthropicResponse,
    TokenCountRequest, TokenCountResponse, GeminiRequest, GeminiResponse
)
from backend.adapter.config import get_enhanced_codegen_config, get_server_config
from backend.adapter.auth import get_auth
from backend.adapter.model_mapper import get_model_mapper
from backend.adapter.enhanced_transformer import (
    enhanced_chat_request_to_prompt,
    enhanced_text_request_to_prompt,
    enhanced_anthropic_request_to_prompt,
    enhanced_gemini_request_to_prompt,
    create_prompt_template
)
from backend.adapter.enhanced_client import create_enhanced_client
from backend.adapter.response_transformer import (
    create_chat_response, create_text_response,
    estimate_tokens, clean_content
)
from backend.adapter.enhanced_streaming import (
    create_enhanced_streaming_response, collect_enhanced_streaming_response
)
from backend.adapter.anthropic_transformer import create_anthropic_response
from backend.adapter.anthropic_streaming import (
    create_anthropic_streaming_response, collect_anthropic_streaming_response
)
from backend.adapter.gemini_transformer import create_gemini_response
from backend.adapter.gemini_streaming import (
    create_gemini_streaming_response, collect_gemini_streaming_response
)
from backend.adapter.system_message_manager import get_system_message_manager

# Enhanced logging configuration
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(name)s | %(levelname)s | %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

# Initialize configurations
codegen_config = get_enhanced_codegen_config()
server_config = get_server_config()

# Initialize components
auth = get_auth()
model_mapper = get_model_mapper()
prompt_template = create_prompt_template(codegen_config)
system_message_manager = get_system_message_manager()

# Initialize enhanced client
enhanced_client = create_enhanced_client(
    config=codegen_config,
    auth=auth,
    model_mapper=model_mapper,
    prompt_template=prompt_template
)

# Create FastAPI app
app = FastAPI(
    title="Enhanced OpenAI Codegen Adapter",
    description="OpenAI-compatible API server with model selection and prompt templates",
    version="2.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=server_config.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add static files for Web UI
try:
    app.mount("/static", StaticFiles(directory="src"), name="static")
except Exception as e:
    logger.warning(f"Failed to mount static files: {e}")

def log_request_start(endpoint: str, request_data: dict, host: str = None, transparent: bool = False):
    """Log the start of a request with enhanced details."""
    mode_indicator = "🔄 TRANSPARENT" if transparent else "🚀 DIRECT"
    logger.info(f"{mode_indicator} REQUEST START | Endpoint: {endpoint}")
    if host and transparent:
        logger.info(f"   🌐 Original Host: {host} -> Intercepted")
    logger.info(f"   📊 Request Data: {request_data}")
    logger.info(f"   🕐 Timestamp: {datetime.now().isoformat()}")

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler to return OpenAI-compatible errors."""
    logger.error(f"Unhandled exception: {exc}\n{traceback.format_exc()}")
    
    error_response = ErrorResponse(
        error=ErrorDetail(
            message=str(exc),
            type="server_error",
            code="500"
        )
    )
    return JSONResponse(
        status_code=500,
        content=error_response.dict()
    )

@app.get("/v1/models")
async def list_models():
    """List available models (OpenAI and Anthropic compatibility)."""
    return {
        "object": "list",
        "data": [
            {
                "id": "gpt-3.5-turbo",
                "object": "model",
                "created": 1677610602,
                "owned_by": "codegen"
            },
            {
                "id": "gpt-4",
                "object": "model", 
                "created": 1677610602,
                "owned_by": "codegen"
            },
            {
                "id": "gpt-3.5-turbo-instruct",
                "object": "model",
                "created": 1677610602,
                "owned_by": "codegen"
            },
            {
                "id": "claude-3-sonnet-20240229",
                "object": "model",
                "created": 1677610602,
                "owned_by": "anthropic"
            },
            {
                "id": "claude-3-haiku-20240307",
                "object": "model",
                "created": 1677610602,
                "owned_by": "anthropic"
            },
            {
                "id": "claude-3-opus-20240229",
                "object": "model",
                "created": 1677610602,
                "owned_by": "anthropic"
            },
            {
                "id": "gemini-1.5-pro",
                "object": "model",
                "created": 1677610602,
                "owned_by": "google"
            },
            {
                "id": "gemini-1.5-flash",
                "object": "model",
                "created": 1677610602,
                "owned_by": "google"
            },
            {
                "id": "gemini-pro",
                "object": "model",
                "created": 1677610602,
                "owned_by": "google"
            }
        ]
    }

@app.post("/v1/chat/completions")
async def chat_completions(request: ChatRequest, http_request: Request):
    """
    Create a chat completion using enhanced Codegen client.
    Compatible with OpenAI's /v1/chat/completions endpoint.
    """
    start_time = time.time()
    
    try:
        # Check if this is a transparent interception
        host = http_request.headers.get("host", "")
        is_transparent = server_config.transparent_mode and ("api.openai.com" in host or "openai.com" in host)
        
        log_request_start("/v1/chat/completions", request.dict(), host, is_transparent)
        
        # Convert request to prompt with model selection
        prompt, codegen_model = enhanced_chat_request_to_prompt(
            request=request,
            model_mapper=model_mapper,
            prompt_template=prompt_template
        )
        
        logger.info(f"Using Codegen model: {codegen_model}")
        logger.debug(f"🔄 Converted prompt: {prompt[:200]}...")
        
        if request.stream:
            # Return streaming response
            logger.info("🌊 Initiating streaming response...")
            return create_enhanced_streaming_response(
                enhanced_client,
                prompt,
                request.model,
                f"chatcmpl-{hash(prompt) % 1000000}",
                codegen_model
            )
        else:
            # Return complete response
            logger.info("📦 Initiating non-streaming response...")
            content = await collect_enhanced_streaming_response(enhanced_client, prompt, codegen_model)
            
            # Estimate token counts
            prompt_tokens = estimate_tokens(prompt)
            completion_tokens = estimate_tokens(content)
            
            logger.info(f"🔢 Token estimation - Prompt: {prompt_tokens}, Completion: {completion_tokens}")
            
            response = create_chat_response(
                content=content,
                model=request.model,
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens
            )
            
            # Log the OpenAI response generation
            processing_time = time.time() - start_time
            logger.info(f"📤 OpenAI response generated in {processing_time:.2f}s")
            
            logger.info(f"✅ Chat completion successful in {processing_time:.2f}s")
            return response
            
    except Exception as e:
        processing_time = time.time() - start_time
        logger.error(f"❌ Error in chat completion after {processing_time:.2f}s: {e}")
        logger.error(f"🔍 Traceback: {traceback.format_exc()}")
        raise HTTPException(
            status_code=500,
            detail={
                "error": {
                    "message": str(e),
                    "type": "server_error",
                    "code": "500"
                }
            }
        )

@app.post("/v1/completions")
async def text_completions(request: TextRequest, http_request: Request):
    """
    Create a text completion using enhanced Codegen client.
    Compatible with OpenAI's /v1/completions endpoint.
    """
    start_time = time.time()
    
    try:
        # Check if this is a transparent interception
        host = http_request.headers.get("host", "")
        is_transparent = server_config.transparent_mode and ("api.openai.com" in host or "openai.com" in host)
        
        log_request_start("/v1/completions", request.dict(), host, is_transparent)
        
        # Convert request to prompt with model selection
        prompt, codegen_model = enhanced_text_request_to_prompt(
            request=request,
            model_mapper=model_mapper,
            prompt_template=prompt_template
        )
        
        logger.info(f"Using Codegen model: {codegen_model}")
        logger.debug(f"🔄 Converted prompt: {prompt[:200]}...")
        
        if request.stream:
            # Return streaming response
            logger.info("🌊 Initiating streaming response...")
            # Use the chat streaming response for text completions
            return create_enhanced_streaming_response(
                enhanced_client,
                prompt,
                request.model,
                f"cmpl-{hash(prompt) % 1000000}",
                codegen_model
            )
        else:
            # Return complete response
            logger.info("📦 Initiating non-streaming response...")
            content = await collect_enhanced_streaming_response(enhanced_client, prompt, codegen_model)
            
            # Estimate token counts
            prompt_tokens = estimate_tokens(prompt)
            completion_tokens = estimate_tokens(content)
            
            logger.info(f"🔢 Token estimation - Prompt: {prompt_tokens}, Completion: {completion_tokens}")
            
            response = create_text_response(
                content=content,
                model=request.model,
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens
            )
            
            # Log the OpenAI response generation
            processing_time = time.time() - start_time
            logger.info(f"📤 OpenAI text response generated in {processing_time:.2f}s")
            
            logger.info(f"✅ Text completion successful in {processing_time:.2f}s")
            return response
            
    except Exception as e:
        processing_time = time.time() - start_time
        logger.error(f"❌ Error in text completion after {processing_time:.2f}s: {e}")
        logger.error(f"🔍 Traceback: {traceback.format_exc()}")
        raise HTTPException(
            status_code=500,
            detail={
                "error": {
                    "message": str(e),
                    "type": "server_error",
                    "code": "500"
                }
            }
        )

@app.post("/v1/messages")
async def anthropic_messages(request: AnthropicRequest, http_request: Request):
    """
    Create a message using enhanced Codegen client.
    Compatible with Anthropic's /v1/messages endpoint.
    """
    start_time = time.time()
    
    try:
        # Check if this is a transparent interception
        host = http_request.headers.get("host", "")
        is_transparent = server_config.transparent_mode and ("api.anthropic.com" in host or "anthropic.com" in host)
        
        log_request_start("/v1/messages", request.dict(), host, is_transparent)
        
        # Store original model for response
        request.original_model = request.model
        
        # Convert request to prompt with model selection
        prompt, codegen_model = enhanced_anthropic_request_to_prompt(
            request=request,
            model_mapper=model_mapper,
            prompt_template=prompt_template
        )
        
        logger.info(f"Using Codegen model: {codegen_model}")
        logger.debug(f"🔄 Converted prompt: {prompt[:200]}...")
        
        if request.stream:
            # Return streaming response
            logger.info("🌊 Initiating Anthropic streaming response...")
            return create_anthropic_streaming_response(
                enhanced_client,
                prompt,
                request.model,
                codegen_model
            )
        else:
            # Return complete response
            logger.info("📦 Initiating Anthropic non-streaming response...")
            content = await collect_enhanced_streaming_response(enhanced_client, prompt, codegen_model)
            
            # Estimate token counts
            prompt_tokens = estimate_tokens(prompt)
            completion_tokens = estimate_tokens(content)
            
            logger.info(f"🔢 Token estimation - Prompt: {prompt_tokens}, Completion: {completion_tokens}")
            
            response = create_anthropic_response(
                content=content,
                model=request.original_model,
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens
            )
            
            # Log the Anthropic response generation
            processing_time = time.time() - start_time
            logger.info(f"📤 Anthropic response generated in {processing_time:.2f}s")
            
            logger.info(f"✅ Anthropic message successful in {processing_time:.2f}s")
            return response
            
    except Exception as e:
        processing_time = time.time() - start_time
        logger.error(f"❌ Error in Anthropic message after {processing_time:.2f}s: {e}")
        logger.error(f"🔍 Traceback: {traceback.format_exc()}")
        raise HTTPException(
            status_code=500,
            detail={
                "error": {
                    "message": str(e),
                    "type": "server_error",
                    "code": "500"
                }
            }
        )

@app.post("/v1/gemini/generateContent")
async def gemini_generate_content(request: GeminiRequest, http_request: Request):
    """
    Generate content using enhanced Codegen client.
    Compatible with Gemini's /v1/generateContent endpoint.
    """
    start_time = time.time()
    
    try:
        # Check if this is a transparent interception
        host = http_request.headers.get("host", "")
        is_transparent = server_config.transparent_mode and ("generativelanguage.googleapis.com" in host)
        
        log_request_start("/v1/gemini/generateContent", request.dict(), host, is_transparent)
        
        # Convert request to prompt with model selection
        prompt, codegen_model = enhanced_gemini_request_to_prompt(
            request=request,
            model_mapper=model_mapper,
            prompt_template=prompt_template
        )
        
        logger.info(f"Using Codegen model: {codegen_model}")
        logger.debug(f"🔄 Converted prompt: {prompt[:200]}...")
        
        # Check if streaming is requested
        is_streaming = request.stream
        
        if is_streaming:
            # Return streaming response
            logger.info("🌊 Initiating Gemini streaming response...")
            return create_gemini_streaming_response(enhanced_client, prompt, codegen_model)
        else:
            # Return complete response
            logger.info("📦 Initiating Gemini non-streaming response...")
            content = await collect_enhanced_streaming_response(enhanced_client, prompt, codegen_model)
            
            # Estimate token counts
            prompt_tokens = estimate_tokens(prompt)
            completion_tokens = estimate_tokens(content)
            
            logger.info(f"🔢 Token estimation - Input: {prompt_tokens}, Output: {completion_tokens}")
            
            response = create_gemini_response(
                content=content,
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens
            )
            
            # Log the Gemini response generation
            processing_time = time.time() - start_time
            logger.info(f"📤 Gemini response generated in {processing_time:.2f}s")
            
            logger.info(f"✅ Gemini content generation successful in {processing_time:.2f}s")
            return response
            
    except Exception as e:
        processing_time = time.time() - start_time
        logger.error(f"❌ Error in Gemini content generation after {processing_time:.2f}s: {e}")
        logger.error(f"🔍 Traceback: {traceback.format_exc()}")
        raise HTTPException(
            status_code=500,
            detail={
                "error": {
                    "code": 500,
                    "message": str(e),
                    "status": "INTERNAL"
                }
            }
        )

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    try:
        # Test enhanced client
        if enhanced_client.validate():
            return {
                "status": "healthy",
                "codegen": "connected",
                "auth": "valid" if auth.validate() else "invalid",
                "model_mapper": "initialized",
                "prompt_template": "enabled" if prompt_template.enabled else "disabled"
            }
        else:
            return {
                "status": "unhealthy",
                "codegen": "disconnected",
                "auth": "invalid",
                "error": "Codegen client validation failed"
            }
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e)
        }

# Service state management
class ServiceState:
    def __init__(self):
        self.is_enabled = True  # Service starts enabled by default
        self.last_toggled = datetime.now()
    
    def toggle(self):
        self.is_enabled = not self.is_enabled
        self.last_toggled = datetime.now()
        logger.info(f"Service {'enabled' if self.is_enabled else 'disabled'} at {self.last_toggled}")
        return self.is_enabled
    
    def get_status(self):
        return {
            "status": "on" if self.is_enabled else "off",
            "last_toggled": self.last_toggled.isoformat(),
            "uptime": str(datetime.now() - self.last_toggled)
        }

# Global service state
service_state = ServiceState()

@app.get("/", response_class=HTMLResponse)
async def web_ui():
    """Serve the Web UI for service control."""
    return HTMLResponse(
        content="""
        <html>
            <head>
                <title>Enhanced OpenAI Codegen Adapter</title>
                <style>
                    body {
                        font-family: Arial, sans-serif;
                        max-width: 800px;
                        margin: 0 auto;
                        padding: 20px;
                    }
                    h1 {
                        color: #333;
                    }
                    .card {
                        border: 1px solid #ddd;
                        border-radius: 8px;
                        padding: 20px;
                        margin-bottom: 20px;
                        background-color: #f9f9f9;
                    }
                    .status {
                        font-weight: bold;
                    }
                    .on {
                        color: green;
                    }
                    .off {
                        color: red;
                    }
                    button {
                        background-color: #4CAF50;
                        color: white;
                        padding: 10px 15px;
                        border: none;
                        border-radius: 4px;
                        cursor: pointer;
                    }
                    button:hover {
                        background-color: #45a049;
                    }
                    textarea {
                        width: 100%;
                        height: 100px;
                        margin-bottom: 10px;
                        padding: 8px;
                        border-radius: 4px;
                        border: 1px solid #ddd;
                    }
                </style>
            </head>
            <body>
                <h1>Enhanced OpenAI Codegen Adapter</h1>
                
                <div class="card">
                    <h2>Service Status</h2>
                    <p>Status: <span id="status" class="status">Loading...</span></p>
                    <p>Last toggled: <span id="lastToggled">Loading...</span></p>
                    <p>Uptime: <span id="uptime">Loading...</span></p>
                    <button id="toggleBtn">Toggle Service</button>
                </div>
                
                <div class="card">
                    <h2>System Message</h2>
                    <textarea id="systemMessage" placeholder="Enter system message..."></textarea>
                    <button id="saveSystemMessage">Save</button>
                    <button id="clearSystemMessage">Clear</button>
                </div>
                
                <div class="card">
                    <h2>Health Check</h2>
                    <p>Codegen: <span id="codegenStatus">Loading...</span></p>
                    <p>Auth: <span id="authStatus">Loading...</span></p>
                    <p>Model Mapper: <span id="modelMapperStatus">Loading...</span></p>
                    <p>Prompt Template: <span id="promptTemplateStatus">Loading...</span></p>
                </div>
                
                <script>
                    // Fetch service status
                    function fetchStatus() {
                        fetch('/api/status')
                            .then(response => response.json())
                            .then(data => {
                                document.getElementById('status').textContent = data.status;
                                document.getElementById('status').className = data.status === 'on' ? 'status on' : 'status off';
                                document.getElementById('lastToggled').textContent = data.last_toggled;
                                document.getElementById('uptime').textContent = data.uptime;
                                
                                if (data.health) {
                                    document.getElementById('codegenStatus').textContent = data.health.codegen || 'unknown';
                                    document.getElementById('authStatus').textContent = data.health.auth || 'unknown';
                                    document.getElementById('modelMapperStatus').textContent = data.health.model_mapper || 'unknown';
                                    document.getElementById('promptTemplateStatus').textContent = data.health.prompt_template || 'unknown';
                                }
                            })
                            .catch(error => console.error('Error fetching status:', error));
                    }
                    
                    // Toggle service
                    document.getElementById('toggleBtn').addEventListener('click', function() {
                        fetch('/api/toggle', { method: 'POST' })
                            .then(response => response.json())
                            .then(data => {
                                fetchStatus();
                            })
                            .catch(error => console.error('Error toggling service:', error));
                    });
                    
                    // Fetch system message
                    function fetchSystemMessage() {
                        fetch('/api/system-message')
                            .then(response => response.json())
                            .then(data => {
                                if (data.success && data.data.has_message) {
                                    document.getElementById('systemMessage').value = data.data.message;
                                } else {
                                    document.getElementById('systemMessage').value = '';
                                }
                            })
                            .catch(error => console.error('Error fetching system message:', error));
                    }
                    
                    // Save system message
                    document.getElementById('saveSystemMessage').addEventListener('click', function() {
                        const message = document.getElementById('systemMessage').value;
                        fetch('/api/system-message', {
                            method: 'POST',
                            headers: {
                                'Content-Type': 'application/json'
                            },
                            body: JSON.stringify({ message })
                        })
                            .then(response => response.json())
                            .then(data => {
                                if (data.success) {
                                    alert('System message saved successfully');
                                } else {
                                    alert('Failed to save system message');
                                }
                            })
                            .catch(error => console.error('Error saving system message:', error));
                    });
                    
                    // Clear system message
                    document.getElementById('clearSystemMessage').addEventListener('click', function() {
                        fetch('/api/system-message', { method: 'DELETE' })
                            .then(response => response.json())
                            .then(data => {
                                if (data.success) {
                                    document.getElementById('systemMessage').value = '';
                                    alert('System message cleared successfully');
                                } else {
                                    alert('Failed to clear system message');
                                }
                            })
                            .catch(error => console.error('Error clearing system message:', error));
                    });
                    
                    // Initial fetch
                    fetchStatus();
                    fetchSystemMessage();
                    
                    // Refresh status every 30 seconds
                    setInterval(fetchStatus, 30000);
                </script>
            </body>
        </html>
        """,
        status_code=200
    )

@app.get("/api/status")
async def get_service_status():
    """Get current service status."""
    try:
        status_data = service_state.get_status()
        
        # Add health check information
        health_status = await health_check()
        status_data["health"] = health_status
        
        return status_data
    except Exception as e:
        logger.error(f"Error getting service status: {e}")
        raise HTTPException(status_code=500, detail="Failed to get service status")

@app.post("/api/toggle")
async def toggle_service():
    """Toggle service on/off."""
    try:
        new_status = service_state.toggle()
        status_data = service_state.get_status()
        
        logger.info(f"Service toggled to: {'ON' if new_status else 'OFF'}")
        
        return {
            "message": f"Service {'enabled' if new_status else 'disabled'} successfully",
            **status_data
        }
    except Exception as e:
        logger.error(f"Error toggling service: {e}")
        raise HTTPException(status_code=500, detail="Failed to toggle service")

# System Message Management Endpoints
@app.get("/api/system-message")
async def get_system_message():
    """Get the current system message configuration."""
    try:
        manager = get_system_message_manager()
        message_info = manager.get_system_message_info()
        
        return {
            "success": True,
            "data": message_info
        }
    except Exception as e:
        logger.error(f"Error getting system message: {e}")
        raise HTTPException(status_code=500, detail="Failed to get system message")

@app.post("/api/system-message")
async def save_system_message(request: Request):
    """Save a new system message configuration."""
    try:
        body = await request.json()
        message = body.get("message", "").strip()
        
        if not message:
            raise HTTPException(status_code=400, detail="Message cannot be empty")
        
        manager = get_system_message_manager()
        success = manager.save_system_message(message)
        
        if not success:
            raise HTTPException(status_code=500, detail="Failed to save system message")
        
        # Get updated info to return
        message_info = manager.get_system_message_info()
        
        return {
            "success": True,
            "message": "System message saved successfully",
            "data": message_info
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error saving system message: {e}")
        raise HTTPException(status_code=500, detail="Failed to save system message")

@app.delete("/api/system-message")
async def clear_system_message():
    """Clear the current system message configuration."""
    try:
        manager = get_system_message_manager()
        success = manager.clear_system_message()
        
        if not success:
            raise HTTPException(status_code=500, detail="Failed to clear system message")
        
        return {
            "success": True,
            "message": "System message cleared successfully",
            "data": {
                "message": None,
                "created_at": None,
                "character_count": 0,
                "has_message": False
            }
        }
    except Exception as e:
        logger.error(f"Error clearing system message: {e}")
        raise HTTPException(status_code=500, detail="Failed to clear system message")

# Middleware to check service status for API endpoints
@app.middleware("http")
async def service_status_middleware(request: Request, call_next):
    """Middleware to check if service is enabled for API endpoints."""
    # Allow access to Web UI, status, toggle, system message, and health endpoints
    allowed_paths = ["/", "/api/status", "/api/toggle", "/api/system-message", "/health", "/static"]
    
    if any(request.url.path.startswith(path) for path in allowed_paths):
        response = await call_next(request)
        return response
    
    # Check if service is enabled for other endpoints
    if not service_state.is_enabled:
        return JSONResponse(
            status_code=503,
            content={
                "error": {
                    "message": "Service is currently disabled. Use the Web UI to enable it.",
                    "type": "service_disabled",
                    "code": "service_disabled"
                }
            }
        )
    
    response = await call_next(request)
    return response

