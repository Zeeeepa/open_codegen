"""
Consolidated FastAPI server for unified API system.
Provides essential endpoints for OpenAI, Anthropic, and Google APIs with web UI.
"""

import asyncio
import logging
import time
import json
from pathlib import Path
from typing import Dict, Any, Optional

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
import uvicorn

from client import UnifiedClient, ProviderType
from models import ChatRequest, ChatResponse, HealthResponse, ErrorResponse, TestResult
from config import get_config

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Get configuration
config = get_config()

# Create FastAPI app
app = FastAPI(
    title="Unified API Server",
    description="Consolidated server for OpenAI, Anthropic, and Google APIs",
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

# Mount static files for Web UI
if config.enable_web_ui and Path(config.static_files_path).exists():
    app.mount("/static", StaticFiles(directory=config.static_files_path), name="static")

# Global client instance
unified_client = UnifiedClient()


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler."""
    logger.error(f"Global exception: {exc}")
    return JSONResponse(
        status_code=500,
        content={"error": f"Internal server error: {str(exc)}"}
    )


# Health and status endpoints
@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint."""
    health = unified_client.health_check()
    return HealthResponse(
        status=health["status"],
        timestamp=health["timestamp"],
        providers=health["supported_providers"]
    )


@app.get("/api/status")
async def api_status():
    """API status endpoint for web UI."""
    health = unified_client.health_check()
    return {
        "status": "online",
        "providers": health["supported_providers"],
        "timestamp": health["timestamp"]
    }


# OpenAI-compatible endpoints
@app.post("/v1/chat/completions")
async def openai_chat_completions(request: ChatRequest):
    """OpenAI-compatible chat completions endpoint."""
    try:
        start_time = time.time()
        result = await unified_client.send_message(
            message=request.messages[-1].content,  # Get last user message
            provider=ProviderType.OPENAI,
            model=request.model
        )
        
        if result["success"]:
            return {
                "id": f"chatcmpl-{int(time.time())}",
                "object": "chat.completion",
                "created": int(start_time),
                "model": request.model,
                "choices": [{
                    "index": 0,
                    "message": {
                        "role": "assistant",
                        "content": str(result.get("response", "Response received"))
                    },
                    "finish_reason": "stop"
                }],
                "usage": {
                    "prompt_tokens": len(request.messages[-1].content.split()),
                    "completion_tokens": 10,  # Estimated
                    "total_tokens": len(request.messages[-1].content.split()) + 10
                }
            }
        else:
            raise HTTPException(status_code=500, detail=result.get("error", "Unknown error"))
            
    except Exception as e:
        logger.error(f"OpenAI chat completion error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Anthropic endpoints
@app.post("/v1/anthropic/completions")
async def anthropic_completions(request: ChatRequest):
    """Anthropic completions endpoint."""
    try:
        result = await unified_client.send_message(
            message=request.messages[-1].content,
            provider=ProviderType.ANTHROPIC,
            model=request.model
        )
        
        if result["success"]:
            return {
                "id": f"msg_{int(time.time())}",
                "type": "message",
                "role": "assistant",
                "content": [{"type": "text", "text": str(result.get("response", "Response received"))}],
                "model": request.model,
                "stop_reason": "end_turn",
                "usage": {
                    "input_tokens": len(request.messages[-1].content.split()),
                    "output_tokens": 10
                }
            }
        else:
            raise HTTPException(status_code=500, detail=result.get("error", "Unknown error"))
            
    except Exception as e:
        logger.error(f"Anthropic completion error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/v1/messages")
async def anthropic_messages(request: ChatRequest):
    """Anthropic messages endpoint (alternative format)."""
    return await anthropic_completions(request)


# Google/Gemini endpoints
@app.post("/v1/gemini/completions")
async def gemini_completions(request: ChatRequest):
    """Google Gemini completions endpoint."""
    try:
        result = await unified_client.send_message(
            message=request.messages[-1].content,
            provider=ProviderType.GOOGLE,
            model=request.model
        )
        
        if result["success"]:
            return {
                "candidates": [{
                    "content": {
                        "parts": [{"text": str(result.get("response", "Response received"))}],
                        "role": "model"
                    },
                    "finishReason": "STOP",
                    "index": 0
                }],
                "usageMetadata": {
                    "promptTokenCount": len(request.messages[-1].content.split()),
                    "candidatesTokenCount": 10,
                    "totalTokenCount": len(request.messages[-1].content.split()) + 10
                }
            }
        else:
            raise HTTPException(status_code=500, detail=result.get("error", "Unknown error"))
            
    except Exception as e:
        logger.error(f"Gemini completion error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/v1/gemini/generateContent")
async def gemini_generate_content(request: ChatRequest):
    """Google Gemini generateContent endpoint (alternative format)."""
    return await gemini_completions(request)


# Test endpoints for each provider
@app.post("/api/test/{provider}")
async def test_provider(provider: str, request: Dict[str, Any]):
    """Test endpoint for each provider."""
    try:
        provider_type = ProviderType(provider.lower())
        message = request.get("message", "Hello! Please respond with just 'Hi there!'")
        model = request.get("model")
        
        result = await unified_client.send_message(message, provider_type, model)
        
        return TestResult(
            provider=provider,
            model=model or f"default-{provider}-model",
            success=result["success"],
            response=result.get("response") if result["success"] else None,
            error=result.get("error") if not result["success"] else None,
            processing_time=result["processing_time"],
            timestamp=time.time()
        )
        
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Unsupported provider: {provider}")
    except Exception as e:
        logger.error(f"Test provider error: {e}")
        return TestResult(
            provider=provider,
            model=model or f"default-{provider}-model",
            success=False,
            error=str(e),
            processing_time=0.0,
            timestamp=time.time()
        )


# Web UI endpoint
@app.get("/", response_class=HTMLResponse)
async def web_ui():
    """Serve the web UI."""
    if config.enable_web_ui:
        static_path = Path(config.static_files_path) / "index.html"
        if static_path.exists():
            return HTMLResponse(content=static_path.read_text(), status_code=200)
    
    # Fallback HTML if no static UI found
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


def main():
    """Main function to run the server."""
    logger.info(f"Starting Unified API Server on {config.host}:{config.port}")
    logger.info(f"Web UI enabled: {config.enable_web_ui}")
    logger.info(f"Supported providers: {unified_client.get_supported_providers()}")
    
    uvicorn.run(
        "server:app",
        host=config.host,
        port=config.port,
        reload=config.debug,
        log_level="info" if not config.debug else "debug"
    )


if __name__ == "__main__":
    main()

