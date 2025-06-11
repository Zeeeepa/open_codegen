"""
Simple FastAPI server for unified API system.
Provides endpoints for OpenAI, Anthropic, and Google APIs with web UI.
"""

import logging
import time
import json
from pathlib import Path
from typing import Dict, Any

from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
import uvicorn

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="Unified API Server",
    description="Simple server for OpenAI, Anthropic, and Google APIs",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files for Web UI if available
static_path = Path("static")
if static_path.exists():
    app.mount("/static", StaticFiles(directory="static"), name="static")


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler."""
    logger.error(f"Global exception: {exc}")
    return JSONResponse(
        status_code=500,
        content={"detail": f"Internal server error: {str(exc)}"}
    )


# Health endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "timestamp": time.time(),
        "providers": ["openai", "anthropic", "google"]
    }


# OpenAI endpoint
@app.post("/v1/chat/completions")
async def openai_chat_completions(request: Request):
    """OpenAI chat completions endpoint."""
    try:
        # Parse request body
        body = await request.json()
        
        # Extract message
        messages = body.get("messages", [])
        if not messages:
            raise HTTPException(status_code=400, detail="No messages provided")
        
        # Get the last user message
        user_message = None
        for msg in reversed(messages):
            if msg.get("role") == "user":
                user_message = msg.get("content")
                break
        
        if not user_message:
            raise HTTPException(status_code=400, detail="No user message found")
        
        # Get model
        model = body.get("model", "gpt-3.5-turbo")
        
        # Create mock response
        response = {
            "id": "chatcmpl-123456789",
            "object": "chat.completion",
            "created": int(time.time()),
            "model": model,
            "choices": [
                {
                    "index": 0,
                    "message": {
                        "role": "assistant",
                        "content": f"This is a simulated response to: {user_message}"
                    },
                    "finish_reason": "stop"
                }
            ],
            "usage": {
                "prompt_tokens": 0,
                "completion_tokens": 0,
                "total_tokens": 0
            }
        }
        
        return response
        
    except Exception as e:
        logger.error(f"OpenAI chat completion error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Anthropic endpoint
@app.post("/v1/anthropic/completions")
async def anthropic_completions(request: Request):
    """Anthropic completions endpoint."""
    try:
        # Parse request body
        body = await request.json()
        
        # Extract message
        messages = body.get("messages", [])
        if not messages:
            raise HTTPException(status_code=400, detail="No messages provided")
        
        # Get the last user message
        user_message = None
        for msg in reversed(messages):
            if msg.get("role") == "user":
                user_message = msg.get("content")
                break
        
        if not user_message:
            raise HTTPException(status_code=400, detail="No user message found")
        
        # Get model
        model = body.get("model", "claude-3-sonnet-20240229")
        
        # Create mock response
        response = {
            "id": "msg_012345678",
            "type": "message",
            "role": "assistant",
            "content": [
                {
                    "type": "text",
                    "text": f"This is a simulated Anthropic response to: {user_message}"
                }
            ],
            "model": model,
            "stop_reason": "end_turn",
            "usage": {
                "input_tokens": 10,
                "output_tokens": 20
            }
        }
        
        return response
        
    except Exception as e:
        logger.error(f"Anthropic completion error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Google/Gemini endpoint
@app.post("/v1/gemini/completions")
async def gemini_completions(request: Request):
    """Google Gemini completions endpoint."""
    try:
        # Parse request body
        body = await request.json()
        
        # Extract message from different possible formats
        user_message = None
        
        # Try messages format first (like OpenAI)
        messages = body.get("messages", [])
        if messages:
            for msg in reversed(messages):
                if msg.get("role") == "user":
                    user_message = msg.get("content")
                    break
        
        # If not found, try contents format (like Gemini)
        if not user_message:
            contents = body.get("contents", [])
            for content in contents:
                parts = content.get("parts", [])
                for part in parts:
                    if "text" in part:
                        user_message = part["text"]
                        break
                if user_message:
                    break
        
        if not user_message:
            raise HTTPException(status_code=400, detail="No user message found")
        
        # Get model
        model = body.get("model", "gemini-1.5-pro")
        
        # Create mock response
        response = {
            "candidates": [
                {
                    "content": {
                        "parts": [
                            {
                                "text": f"This is a simulated Gemini response to: {user_message}"
                            }
                        ],
                        "role": "model"
                    },
                    "finishReason": "STOP",
                    "index": 0
                }
            ],
            "usageMetadata": {
                "promptTokenCount": 10,
                "candidatesTokenCount": 20,
                "totalTokenCount": 30
            }
        }
        
        return response
        
    except Exception as e:
        logger.error(f"Gemini completion error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Alternative Gemini endpoint
@app.post("/v1/gemini/generateContent")
async def gemini_generate_content(request: Request):
    """Alternative Gemini endpoint."""
    return await gemini_completions(request)


# Alternative Anthropic endpoint
@app.post("/v1/messages")
async def anthropic_messages(request: Request):
    """Alternative Anthropic endpoint."""
    return await anthropic_completions(request)


# Test endpoint
@app.post("/api/test/{provider}")
async def test_provider(provider: str, request: Request):
    """Test endpoint for each provider."""
    try:
        # Parse request body
        body = await request.json()
        
        # Get message and model
        message = body.get("message", "Hello! Please respond with a short greeting.")
        model = body.get("model")
        
        # Validate provider
        if provider.lower() not in ["openai", "anthropic", "google"]:
            raise HTTPException(status_code=400, detail=f"Unsupported provider: {provider}")
        
        # Create response based on provider
        if provider.lower() == "openai":
            response_content = f"OpenAI test response to: {message}"
            model = model or "gpt-3.5-turbo"
        elif provider.lower() == "anthropic":
            response_content = f"Anthropic test response to: {message}"
            model = model or "claude-3-sonnet-20240229"
        else:  # google
            response_content = f"Google test response to: {message}"
            model = model or "gemini-1.5-pro"
        
        # Return response
        return {
            "provider": provider,
            "model": model,
            "success": True,
            "response": {
                "content": response_content
            },
            "processing_time": 0.1,
            "timestamp": time.time()
        }
        
    except Exception as e:
        logger.error(f"Test provider error: {e}")
        return {
            "provider": provider,
            "success": False,
            "error": str(e),
            "timestamp": time.time()
        }


# Web UI endpoint
@app.get("/", response_class=HTMLResponse)
async def web_ui():
    """Serve the web UI."""
    static_index = Path("static/index.html")
    if static_index.exists():
        return HTMLResponse(content=static_index.read_text(), status_code=200)
    
    # Fallback HTML
    return HTMLResponse(content="""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Unified API Server</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 40px; }
            .container { max-width: 800px; margin: 0 auto; }
            .endpoint { background: #f5f5f5; padding: 10px; margin: 10px 0; border-radius: 5px; }
            .method { color: #007acc; font-weight: bold; }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>Unified API Server</h1>
            <p>Server is running! Available endpoints:</p>
            
            <div class="endpoint">
                <span class="method">GET</span> /health - Health check
            </div>
            <div class="endpoint">
                <span class="method">POST</span> /v1/chat/completions - OpenAI chat completions
            </div>
            <div class="endpoint">
                <span class="method">POST</span> /v1/anthropic/completions - Anthropic completions
            </div>
            <div class="endpoint">
                <span class="method">POST</span> /v1/gemini/completions - Google Gemini completions
            </div>
            <div class="endpoint">
                <span class="method">POST</span> /api/test/{provider} - Test provider (openai, anthropic, google)
            </div>
            
            <h2>Quick Test</h2>
            <p>Test the APIs using curl:</p>
            <pre>
# Test OpenAI
curl -X POST http://localhost:8887/v1/chat/completions \\
  -H "Content-Type: application/json" \\
  -d '{"model":"gpt-3.5-turbo","messages":[{"role":"user","content":"Hello!"}]}'

# Test Anthropic  
curl -X POST http://localhost:8887/v1/anthropic/completions \\
  -H "Content-Type: application/json" \\
  -d '{"model":"claude-3-sonnet-20240229","messages":[{"role":"user","content":"Hello!"}]}'

# Test Google
curl -X POST http://localhost:8887/v1/gemini/completions \\
  -H "Content-Type: application/json" \\
  -d '{"model":"gemini-1.5-pro","messages":[{"role":"user","content":"Hello!"}]}'
            </pre>
        </div>
    </body>
    </html>
    """, status_code=200)


if __name__ == "__main__":
    host = "localhost"
    port = 8887
    
    logger.info(f"Starting Unified API Server on {host}:{port}")
    logger.info(f"Supported providers: openai, anthropic, google")
    
    uvicorn.run(
        app,
        host=host,
        port=port,
        log_level="info"
    )

