"""
FastAPI server providing OpenAI-compatible API endpoints.
Based on h2ogpt's server.py structure and patterns.
Enhanced with comprehensive logging for completion tracking and OpenAI response generation.
Enhanced with Anthropic Claude API compatibility.
Enhanced with Web UI for service control.
"""

import logging
import traceback
import time
from datetime import datetime
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
import uvicorn
import os
from pathlib import Path

from backend.adapter.models import (
    ChatRequest, TextRequest, ChatResponse, TextResponse,
    ErrorResponse, ErrorDetail, AnthropicRequest, AnthropicResponse,
    TokenCountRequest, TokenCountResponse, GeminiRequest, GeminiResponse
)
from backend.adapter.config import get_codegen_config, get_server_config
from backend.adapter.codegen_client import CodegenClient
from backend.adapter.request_transformer import (
    chat_request_to_prompt, text_request_to_prompt,
    extract_generation_params
)
from backend.adapter.response_transformer import (
    create_chat_response, create_text_response,
    estimate_tokens, clean_content
)
from backend.adapter.streaming import create_streaming_response, collect_streaming_response
from backend.adapter.anthropic_transformer import (
    anthropic_request_to_prompt, create_anthropic_response,
    extract_anthropic_generation_params
)
from backend.adapter.anthropic_streaming import (
    create_anthropic_streaming_response, collect_anthropic_streaming_response
)
from backend.adapter.gemini_transformer import (
    gemini_request_to_prompt, create_gemini_response,
    extract_gemini_generation_params
)
from backend.adapter.gemini_streaming import (
    create_gemini_streaming_response, collect_gemini_streaming_response
)

# Enhanced logging configuration
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(name)s | %(levelname)s | %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

# Initialize configurations
codegen_config = get_codegen_config()
server_config = get_server_config()

# Initialize Codegen client
codegen_client = CodegenClient(codegen_config)

# Create FastAPI app
app = FastAPI(
    title="OpenAI Codegen Adapter",
    description="OpenAI-compatible API server that forwards requests to Codegen SDK",
    version="1.0.0"
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
app.mount("/static", StaticFiles(directory="src"), name="static")

def log_request_start(endpoint: str, request_data: dict, host: str = None, transparent: bool = False):
    """Log the start of a request with enhanced details."""
    mode_indicator = "🔄 TRANSPARENT" if transparent else "🚀 DIRECT"
    logger.info(f"{mode_indicator} REQUEST START | Endpoint: {endpoint}")
    if host and transparent:
        logger.info(f"   🌐 Original Host: {host} -> Intercepted")
    logger.info(f"   📊 Request Data: {request_data}")
    logger.info(f"   🕐 Timestamp: {datetime.now().isoformat()}")

def log_completion_tracking(task_id: str, status: str, attempt: int, duration: float):
    """Log completion checking process with detailed tracking."""
    logger.info(f"🔍 COMPLETION CHECK | Task: {task_id} | Status: {status} | Attempt: {attempt} | Duration: {duration:.2f}s")

def log_openai_response_generation(response_data: dict, processing_time: float):
    """Log OpenAI API compatible response generation."""
    logger.info(f"📤 OPENAI RESPONSE GENERATED | Processing Time: {processing_time:.2f}s")
    logger.info(f"   🆔 Response ID: {response_data.get('id', 'N/A')}")
    logger.info(f"   ���������� Model: {response_data.get('model', 'N/A')}")
    logger.info(f"   📝 Choices: {len(response_data.get('choices', []))}")
    
    if 'usage' in response_data:
        usage = response_data['usage']
        logger.info(f"   🔢 Token Usage - Prompt: {usage.get('prompt_tokens', 0)}, "
                   f"Completion: {usage.get('completion_tokens', 0)}, "
                   f"Total: {usage.get('total_tokens', 0)}")
    
    # Log first 100 chars of response content
    if response_data.get('choices') and len(response_data['choices']) > 0:
        choice = response_data['choices'][0]
        if 'message' in choice and 'content' in choice['message']:
            content = choice['message']['content']
            logger.info(f"   📄 Content Preview: {content[:100]}...")

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
    Create a chat completion using Codegen SDK.
    Compatible with OpenAI's /v1/chat/completions endpoint.
    """
    start_time = time.time()
    
    try:
        # Check if this is a transparent interception
        host = http_request.headers.get("host", "")
        is_transparent = server_config.transparent_mode and ("api.openai.com" in host or "openai.com" in host)
        
        log_request_start("/v1/chat/completions", request.dict(), host, is_transparent)
        
        # Convert request to prompt
        prompt = chat_request_to_prompt(request)
        logger.debug(f"🔄 Converted prompt: {prompt[:200]}...")
        
        # Extract generation parameters (for future use)
        gen_params = extract_generation_params(request)
        logger.debug(f"⚙️ Generation parameters: {gen_params}")
        
        if request.stream:
            # Return streaming response
            logger.info("🌊 Initiating streaming response...")
            return create_streaming_response(
                codegen_client,
                prompt,
                request.model,
                f"chatcmpl-{hash(prompt) % 1000000}"
            )
        else:
            # Return complete response
            logger.info("📦 Initiating non-streaming response...")
            content = await collect_streaming_response(codegen_client, prompt)
            
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
            log_openai_response_generation(response.dict(), processing_time)
            
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
async def completions(request: TextRequest):
    """
    Create a text completion using Codegen SDK.
    Compatible with OpenAI's /v1/completions endpoint.
    """
    try:
        log_request_start("/v1/completions", request.dict())
        
        # Convert request to prompt
        prompt = text_request_to_prompt(request)
        logger.debug(f"Converted prompt: {prompt[:200]}...")
        
        # Extract generation parameters (for future use)
        gen_params = extract_generation_params(request)
        logger.debug(f"Generation parameters: {gen_params}")
        
        if request.stream:
            # For text completions streaming, we'd need a different streaming format
            # For now, fall back to non-streaming
            logger.warning("Streaming not yet implemented for text completions, falling back to non-streaming")
        
        # Get complete response
        content = await collect_streaming_response(codegen_client, prompt)
        
        # Estimate token counts
        prompt_tokens = estimate_tokens(prompt)
        completion_tokens = estimate_tokens(content)
        
        response = create_text_response(
            content=content,
            model=request.model,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens
        )
        
        logger.info(f"Text completion response: {completion_tokens} tokens")
        return response
        
    except Exception as e:
        logger.error(f"Error in text completion: {e}\n{traceback.format_exc()}")
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


@app.post("/v1/anthropic/completions")
async def anthropic_completions(request: AnthropicRequest):
    """
    Create a text completion using Anthropic Claude API.
    Compatible with Anthropic's /v1/anthropic/completions endpoint.
    """
    try:
        log_request_start("/v1/anthropic/completions", request.dict())
        
        # Convert request to prompt
        prompt = anthropic_request_to_prompt(request)
        logger.debug(f"Converted prompt: {prompt[:200]}...")
        
        # Extract generation parameters (for future use)
        gen_params = extract_anthropic_generation_params(request)
        logger.debug(f"Generation parameters: {gen_params}")
        
        if request.stream:
            # For text completions streaming, we'd need a different streaming format
            # For now, fall back to non-streaming
            logger.warning("Streaming not yet implemented for text completions, falling back to non-streaming")
        
        # Get complete response
        content = await collect_anthropic_streaming_response(codegen_client, prompt)
        
        # Estimate token counts
        prompt_tokens = estimate_tokens(prompt)
        completion_tokens = estimate_tokens(content)
        
        response = create_anthropic_response(
            content=content,
            model=request.model,
            input_tokens=prompt_tokens,
            output_tokens=completion_tokens
        )
        
        logger.info(f"Anthropic completion response: {completion_tokens} tokens")
        return response
        
    except Exception as e:
        logger.error(f"Error in text completion: {e}\n{traceback.format_exc()}")
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
async def anthropic_messages(request: AnthropicRequest):
    """
    Create a message using Anthropic Claude API.
    Compatible with Anthropic's /v1/messages endpoint.
    """
    start_time = time.time()
    
    try:
        log_request_start("/v1/messages", request.dict())
        
        # Convert request to prompt
        prompt = anthropic_request_to_prompt(request)
        logger.debug(f"🔄 Converted prompt: {prompt[:200]}...")
        
        # Extract generation parameters (for future use)
        gen_params = extract_anthropic_generation_params(request)
        logger.debug(f"⚙️ Generation parameters: {gen_params}")
        
        if request.stream:
            # Return streaming response
            logger.info("🌊 Initiating Anthropic streaming response...")
            return create_anthropic_streaming_response(
                codegen_client,
                prompt,
                request.model,
                f"msg_{hash(prompt) % 1000000}"
            )
        else:
            # Return complete response
            logger.info("📦 Initiating Anthropic non-streaming response...")
            content = await collect_anthropic_streaming_response(codegen_client, prompt)
            
            # Estimate token counts
            input_tokens = estimate_tokens(prompt)
            output_tokens = estimate_tokens(content)
            
            logger.info(f"�� Token estimation - Input: {input_tokens}, Output: {output_tokens}")
            
            response = create_anthropic_response(
                content=content,
                model=request.model,
                input_tokens=input_tokens,
                output_tokens=output_tokens
            )
            
            # Log the Anthropic response generation
            processing_time = time.time() - start_time
            logger.info(f"📤 Anthropic response generated in {processing_time:.2f}s")
            
            logger.info(f"✅ Anthropic message completion successful in {processing_time:.2f}s")
            return response
            
    except Exception as e:
        processing_time = time.time() - start_time
        logger.error(f"❌ Error in Anthropic message completion after {processing_time:.2f}s: {e}")
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


@app.post("/v1/messages/count_tokens")
async def anthropic_count_tokens(request: TokenCountRequest, http_request: Request):
    """
    Count tokens for Anthropic Claude API messages.
    Compatible with Anthropic's /v1/messages/count_tokens endpoint.
    """
    try:
        # Check if this is a transparent interception
        host = http_request.headers.get("host", "")
        is_transparent = server_config.transparent_mode and ("api.anthropic.com" in host or "anthropic.com" in host)
        
        log_request_start("/v1/messages/count_tokens", request.dict(), host, is_transparent)
        
        # Convert the messages to a prompt format for token estimation
        prompt = anthropic_request_to_prompt(
            AnthropicRequest(
                model=request.model,
                max_tokens=100,  # Arbitrary value not used for token counting
                messages=request.messages,
                system=request.system,
                tools=request.tools,
                tool_choice=request.tool_choice,
                thinking=request.thinking
            )
        )
        
        # Estimate input tokens
        input_tokens = estimate_tokens(prompt)
        
        logger.info(f"🔢 Token count estimation - Input: {input_tokens} tokens")
        
        # Return Anthropic-style response
        return TokenCountResponse(input_tokens=input_tokens)
        
    except Exception as e:
        logger.error(f"❌ Error counting tokens: {e}\n{traceback.format_exc()}")
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


@app.post("/v1/gemini/completions")
async def gemini_completions(request: GeminiRequest):
    """
    Create a text completion using Gemini API.
    Compatible with Gemini's /v1/gemini/completions endpoint.
    """
    try:
        log_request_start("/v1/gemini/completions", request.dict())
        
        # Convert request to prompt
        prompt = gemini_request_to_prompt(request)
        logger.debug(f"Converted prompt: {prompt[:200]}...")
        
        # Extract generation parameters (for future use)
        gen_params = extract_gemini_generation_params(request)
        logger.debug(f"Generation parameters: {gen_params}")
        
        if request.stream:
            # For text completions streaming, we'd need a different streaming format
            # For now, fall back to non-streaming
            logger.warning("Streaming not yet implemented for text completions, falling back to non-streaming")
        
        # Get complete response
        content = await collect_gemini_streaming_response(codegen_client, prompt)
        
        # Estimate token counts
        prompt_tokens = estimate_tokens(prompt)
        completion_tokens = estimate_tokens(content)
        
        # For /v1/gemini/completions, return OpenAI-compatible format
        response = create_chat_response(
            content=content,
            model="gemini-pro",
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens
        )
        
        logger.info(f"Gemini completion response: {completion_tokens} tokens")
        return response
        
    except Exception as e:
        logger.error(f"Error in text completion: {e}\n{traceback.format_exc()}")
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
async def gemini_generate_content(request: GeminiRequest):
    """
    Generate content using Gemini API.
    Compatible with Gemini's /v1/generateContent endpoint.
    """
    start_time = time.time()
    
    try:
        log_request_start("/v1/gemini/generateContent", request.dict())
        
        # Convert request to prompt
        prompt = gemini_request_to_prompt(request)
        logger.debug(f"🔄 Converted prompt: {prompt[:200]}...")
        
        # Extract generation parameters (for future use)
        gen_params = extract_gemini_generation_params(request)
        logger.debug(f"⚙️ Generation parameters: {gen_params}")
        
        # Check if streaming is requested
        is_streaming = gen_params.get("stream", False)
        
        if is_streaming:
            # Return streaming response
            logger.info("🌊 Initiating Gemini streaming response...")
            return create_gemini_streaming_response(codegen_client, prompt, request.model)
        else:
            # Return complete response
            logger.info("📦 Initiating Gemini non-streaming response...")
            content = await collect_gemini_streaming_response(codegen_client, prompt)
            
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
        # Test Codegen client
        if codegen_client.agent:
            return {"status": "healthy", "codegen": "connected"}
        else:
            return {"status": "unhealthy", "codegen": "disconnected"}
    except Exception as e:
        return {"status": "unhealthy", "error": str(e)}


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
    static_path = Path("src/index.html")
    if static_path.exists():
        return HTMLResponse(content=static_path.read_text(), status_code=200)
    else:
        return HTMLResponse(
            content="""
            <html>
                <body>
                    <h1>OpenAI Codegen Adapter</h1>
                    <p>Web UI not found. Please ensure static/index.html exists.</p>
                    <p><a href="/health">Health Check</a></p>
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


@app.get("/api/system-message")
async def get_system_message():
    """Get the current system message."""
    try:
        from backend.adapter.system_message_manager import get_system_message_manager
        manager = get_system_message_manager()
        message = manager.get_system_message()
        
        if message:
            return {
                "success": True,
                "data": {
                    "message": message,
                    "character_count": len(message)
                }
            }
        else:
            return {
                "success": True,
                "data": None
            }
    except Exception as e:
        logger.error(f"Error getting system message: {e}")
        raise HTTPException(status_code=500, detail="Failed to get system message")


@app.post("/api/system-message")
async def save_system_message(request: dict):
    """Save a new system message."""
    try:
        message = request.get("message", "").strip()
        if not message:
            raise HTTPException(status_code=400, detail="Message cannot be empty")
        
        from backend.adapter.system_message_manager import get_system_message_manager
        manager = get_system_message_manager()
        manager.save_system_message(message)
        
        logger.info(f"System message saved: {len(message)} characters")
        
        return {
            "success": True,
            "data": {
                "message": message,
                "character_count": len(message)
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error saving system message: {e}")
        raise HTTPException(status_code=500, detail="Failed to save system message")


@app.delete("/api/system-message")
async def clear_system_message():
    """Clear the current system message."""
    try:
        from backend.adapter.system_message_manager import get_system_message_manager
        manager = get_system_message_manager()
        manager.clear_system_message()
        
        logger.info("System message cleared")
        
        return {
            "success": True,
            "message": "System message cleared successfully"
        }
    except Exception as e:
        logger.error(f"Error clearing system message: {e}")
        raise HTTPException(status_code=500, detail="Failed to clear system message")


# Middleware to check service status for API endpoints
@app.middleware("http")
async def service_status_middleware(request: Request, call_next):
    """Middleware to check if service is enabled for API endpoints."""
    # Allow access to Web UI, status, toggle, and health endpoints
    allowed_paths = ["/", "/api/status", "/api/toggle", "/health", "/static"]
    
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


if __name__ == "__main__":
    uvicorn.run(
        "backend.adapter.server:app",
        host=server_config.host,
        port=server_config.port,
        log_level=server_config.log_level,
        reload=False
    )
