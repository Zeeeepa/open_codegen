"""
Unified API System for OpenAI, Anthropic, and Google APIs.
This module provides a consolidated interface for all three APIs.
"""

import logging
import time
import json
import os
from pathlib import Path
from typing import Dict, Any, List, Optional

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
    title="Unified API System",
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
        <title>Unified API System</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 40px; }
            .container { max-width: 800px; margin: 0 auto; }
            .endpoint { background: #f5f5f5; padding: 10px; margin: 10px 0; border-radius: 5px; }
            .method { color: #007acc; font-weight: bold; }
            .status { padding: 10px; margin: 10px 0; border-radius: 5px; }
            .healthy { background: #d4edda; color: #155724; }
            .unhealthy { background: #f8d7da; color: #721c24; }
            .test-button { 
                padding: 10px 15px; 
                margin: 5px;
                border: none;
                border-radius: 5px;
                cursor: pointer;
                font-weight: bold;
            }
            .openai { background: #10a37f; color: white; }
            .anthropic { background: #7b2cbf; color: white; }
            .google { background: #4285f4; color: white; }
            #response-container {
                background: #f8f9fa;
                padding: 15px;
                border-radius: 5px;
                margin-top: 20px;
                white-space: pre-wrap;
                max-height: 300px;
                overflow-y: auto;
            }
            .hidden { display: none; }
            #status-container {
                margin-bottom: 20px;
            }
            #custom-prompt {
                width: 100%;
                padding: 10px;
                margin: 10px 0;
                border-radius: 5px;
                border: 1px solid #ddd;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>Unified API System</h1>
            
            <div id="status-container">
                <h2>Health Status</h2>
                <div id="health-status" class="status">Checking...</div>
            </div>
            
            <h2>Test API Endpoints</h2>
            <div>
                <h3>Simple Test</h3>
                <button class="test-button openai" onclick="testAPI('openai')">🟢 Test OpenAI API</button>
                <button class="test-button anthropic" onclick="testAPI('anthropic')">🟣 Test Anthropic API</button>
                <button class="test-button google" onclick="testAPI('google')">🔵 Test Google API</button>
            </div>
            
            <div>
                <h3>Custom Prompt</h3>
                <textarea id="custom-prompt" rows="3" placeholder="Enter your custom prompt here...">Hello! Please respond with a short greeting.</textarea>
                <button class="test-button openai" onclick="testAPIWithCustomPrompt('openai')">🟢 Test OpenAI API</button>
                <button class="test-button anthropic" onclick="testAPIWithCustomPrompt('anthropic')">🟣 Test Anthropic API</button>
                <button class="test-button google" onclick="testAPIWithCustomPrompt('google')">🔵 Test Google API</button>
            </div>
            
            <div id="response-container" class="hidden">
                <h3>Response:</h3>
                <pre id="response-content"></pre>
            </div>
            
            <h2>Available Endpoints</h2>
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
        </div>
        
        <script>
            // Check server health on page load
            document.addEventListener('DOMContentLoaded', checkHealth);
            
            function checkHealth() {
                fetch('/health')
                    .then(response => response.json())
                    .then(data => {
                        const statusElement = document.getElementById('health-status');
                        if (data.status === 'healthy') {
                            statusElement.className = 'status healthy';
                            statusElement.innerHTML = '✅ Server is healthy';
                        } else {
                            statusElement.className = 'status unhealthy';
                            statusElement.innerHTML = '❌ Server is unhealthy';
                        }
                    })
                    .catch(error => {
                        const statusElement = document.getElementById('health-status');
                        statusElement.className = 'status unhealthy';
                        statusElement.innerHTML = '❌ Server is unhealthy';
                        console.error('Error checking health:', error);
                    });
            }
            
            function testAPI(provider) {
                const defaultPrompt = "Hello! Please respond with a short greeting.";
                sendRequest(provider, defaultPrompt);
            }
            
            function testAPIWithCustomPrompt(provider) {
                const prompt = document.getElementById('custom-prompt').value.trim();
                if (!prompt) {
                    alert('Please enter a prompt');
                    return;
                }
                sendRequest(provider, prompt);
            }
            
            function sendRequest(provider, message) {
                const responseContainer = document.getElementById('response-container');
                const responseContent = document.getElementById('response-content');
                
                responseContainer.className = ''; // Show container
                responseContent.textContent = 'Sending request...';
                
                let endpoint = '';
                let payload = {};
                
                if (provider === 'openai') {
                    endpoint = '/v1/chat/completions';
                    payload = {
                        model: 'gpt-3.5-turbo',
                        messages: [{ role: 'user', content: message }]
                    };
                } else if (provider === 'anthropic') {
                    endpoint = '/v1/anthropic/completions';
                    payload = {
                        model: 'claude-3-sonnet-20240229',
                        messages: [{ role: 'user', content: message }]
                    };
                } else if (provider === 'google') {
                    endpoint = '/v1/gemini/completions';
                    payload = {
                        model: 'gemini-1.5-pro',
                        messages: [{ role: 'user', content: message }]
                    };
                }
                
                fetch(endpoint, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify(payload)
                })
                .then(response => response.json())
                .then(data => {
                    responseContent.textContent = 'Request successful!\nResponse:\n' + JSON.stringify(data, null, 2);
                })
                .catch(error => {
                    responseContent.textContent = 'Error: ' + error.message;
                    console.error('Error:', error);
                });
            }
        </script>
    </body>
    </html>
    """, status_code=200)


def start_server(host="localhost", port=8887):
    """Start the server."""
    logger.info(f"Starting Unified API System on {host}:{port}")
    logger.info(f"Supported providers: openai, anthropic, google")
    
    uvicorn.run(
        app,
        host=host,
        port=port,
        log_level="info"
    )


if __name__ == "__main__":
    start_server()

