#!/usr/bin/env python3
"""
API Router System for OpenAI, Anthropic, and Google APIs.
Routes requests from these APIs to the Codegen SDK.
"""

import logging
import time
import json
import os
import requests
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
    title="API Router System",
    description="Routes requests from OpenAI, Anthropic, and Google APIs to Codegen SDK",
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

# Codegen SDK API endpoint (default to localhost, can be overridden with env var)
CODEGEN_API_URL = os.environ.get("CODEGEN_API_URL", "http://localhost:8000/api/generate")


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
        "providers": ["openai", "anthropic", "google"],
        "routing_to": CODEGEN_API_URL
    }


# OpenAI endpoint
@app.post("/v1/chat/completions")
async def openai_chat_completions(request: Request):
    """OpenAI chat completions endpoint - routes to Codegen SDK."""
    try:
        # Parse request body
        body = await request.json()
        
        # Extract message content
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
        
        # Prepare request to Codegen SDK
        codegen_request = {
            "prompt": user_message,
            "source": "openai_proxy",
            "model": body.get("model", "gpt-3.5-turbo")
        }
        
        # Send request to Codegen SDK
        logger.info(f"Routing OpenAI request to Codegen SDK: {json.dumps(codegen_request)}")
        
        response = requests.post(CODEGEN_API_URL, json=codegen_request)
        
        # Check response status
        if response.status_code != 200:
            logger.error(f"Codegen SDK error: {response.status_code} - {response.text}")
            return JSONResponse(
                status_code=response.status_code,
                content={"error": f"Codegen SDK error: {response.text}"}
            )
        
        # Parse Codegen SDK response
        codegen_response = response.json()
        
        # Extract the generated text from Codegen response
        generated_text = codegen_response.get("response", "No response from Codegen SDK")
        
        # Format response in OpenAI format
        openai_response = {
            "id": f"chatcmpl-{int(time.time())}",
            "object": "chat.completion",
            "created": int(time.time()),
            "model": body.get("model", "gpt-3.5-turbo"),
            "choices": [
                {
                    "index": 0,
                    "message": {
                        "role": "assistant",
                        "content": generated_text
                    },
                    "finish_reason": "stop"
                }
            ],
            "usage": {
                "prompt_tokens": len(user_message.split()),
                "completion_tokens": len(generated_text.split()),
                "total_tokens": len(user_message.split()) + len(generated_text.split())
            }
        }
        
        return openai_response
        
    except Exception as e:
        logger.error(f"OpenAI chat completion error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Anthropic endpoint
@app.post("/v1/anthropic/completions")
async def anthropic_completions(request: Request):
    """Anthropic completions endpoint - routes to Codegen SDK."""
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
        
        # Prepare request to Codegen SDK
        codegen_request = {
            "prompt": user_message,
            "source": "anthropic_proxy",
            "model": body.get("model", "claude-3-sonnet-20240229")
        }
        
        # Send request to Codegen SDK
        logger.info(f"Routing Anthropic request to Codegen SDK: {json.dumps(codegen_request)}")
        
        response = requests.post(CODEGEN_API_URL, json=codegen_request)
        
        # Check response status
        if response.status_code != 200:
            logger.error(f"Codegen SDK error: {response.status_code} - {response.text}")
            return JSONResponse(
                status_code=response.status_code,
                content={"error": f"Codegen SDK error: {response.text}"}
            )
        
        # Parse Codegen SDK response
        codegen_response = response.json()
        
        # Extract the generated text from Codegen response
        generated_text = codegen_response.get("response", "No response from Codegen SDK")
        
        # Format response in Anthropic format
        anthropic_response = {
            "id": f"msg_{int(time.time())}",
            "type": "message",
            "role": "assistant",
            "content": [
                {
                    "type": "text",
                    "text": generated_text
                }
            ],
            "model": body.get("model", "claude-3-sonnet-20240229"),
            "stop_reason": "end_turn",
            "usage": {
                "input_tokens": len(user_message.split()),
                "output_tokens": len(generated_text.split())
            }
        }
        
        return anthropic_response
        
    except Exception as e:
        logger.error(f"Anthropic completion error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Google/Gemini endpoint
@app.post("/v1/gemini/completions")
async def gemini_completions(request: Request):
    """Google Gemini completions endpoint - routes to Codegen SDK."""
    try:
        # Parse request body
        body = await request.json()
        
        # Extract message from different possible formats
        user_message = extract_user_message(body)
        
        if not user_message:
            raise HTTPException(status_code=400, detail="No user message found")
        
        # Prepare request to Codegen SDK
        codegen_request = {
            "prompt": user_message,
            "source": "google_proxy",
            "model": body.get("model", "gemini-1.5-pro")
        }
        
        # Send request to Codegen SDK
        logger.info(f"Routing Google request to Codegen SDK: {json.dumps(codegen_request)}")
        
        response = requests.post(CODEGEN_API_URL, json=codegen_request)
        
        # Check response status
        if response.status_code != 200:
            logger.error(f"Codegen SDK error: {response.status_code} - {response.text}")
            return JSONResponse(
                status_code=response.status_code,
                content={"error": f"Codegen SDK error: {response.text}"}
            )
        
        # Parse Codegen SDK response
        codegen_response = response.json()
        
        # Extract the generated text from Codegen response
        generated_text = codegen_response.get("response", "No response from Codegen SDK")
        
        # Format response in Google/Gemini format
        gemini_response = {
            "candidates": [
                {
                    "content": {
                        "parts": [
                            {
                                "text": generated_text
                            }
                        ],
                        "role": "model"
                    },
                    "finishReason": "STOP",
                    "index": 0
                }
            ],
            "usageMetadata": {
                "promptTokenCount": len(user_message.split()),
                "candidatesTokenCount": len(generated_text.split()),
                "totalTokenCount": len(user_message.split()) + len(generated_text.split())
            }
        }
        
        return gemini_response
        
    except Exception as e:
        logger.error(f"Gemini completion error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


def extract_user_message(body):
    """Extract user message from different possible formats."""
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
    
    return user_message


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
        <title>API Router System</title>
        <style>
            body { 
                font-family: Arial, sans-serif; 
                margin: 0;
                padding: 0;
                background-color: #f5f7fa;
            }
            .container { 
                max-width: 800px; 
                margin: 0 auto;
                padding: 20px;
            }
            header {
                background-color: #4a6cf7;
                color: white;
                padding: 20px 0;
                text-align: center;
                box-shadow: 0 2px 5px rgba(0, 0, 0, 0.1);
            }
            header h1 {
                margin: 0;
                font-size: 2.5rem;
            }
            header p {
                margin: 10px 0 0;
                font-size: 1.2rem;
                opacity: 0.9;
            }
            .card {
                background-color: white;
                border-radius: 8px;
                box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
                padding: 20px;
                margin-bottom: 20px;
            }
            .endpoint { 
                background: #f5f5f5; 
                padding: 10px; 
                margin: 10px 0; 
                border-radius: 5px; 
            }
            .method { 
                color: #007acc; 
                font-weight: bold; 
            }
            .status { 
                padding: 10px; 
                margin: 10px 0; 
                border-radius: 5px; 
            }
            .healthy { 
                background: #d4edda; 
                color: #155724; 
            }
            .unhealthy { 
                background: #f8d7da; 
                color: #721c24; 
            }
            .test-button { 
                padding: 10px 15px; 
                margin: 5px;
                border: none;
                border-radius: 5px;
                cursor: pointer;
                font-weight: bold;
                transition: transform 0.3s ease, box-shadow 0.3s ease;
            }
            .test-button:hover {
                transform: translateY(-2px);
                box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
            }
            .openai { 
                background: #10a37f; 
                color: white; 
            }
            .anthropic { 
                background: #7b2cbf; 
                color: white; 
            }
            .google { 
                background: #4285f4; 
                color: white; 
            }
            #response-container {
                background: #f8f9fa;
                padding: 15px;
                border-radius: 5px;
                margin-top: 20px;
                white-space: pre-wrap;
                max-height: 300px;
                overflow-y: auto;
                border: 1px solid #e0e0e0;
            }
            .hidden { 
                display: none; 
            }
            #status-container {
                margin-bottom: 20px;
            }
            #custom-prompt {
                width: 100%;
                padding: 10px;
                margin: 10px 0;
                border-radius: 5px;
                border: 1px solid #ddd;
                font-family: inherit;
                resize: vertical;
            }
            h2 {
                color: #4a6cf7;
                border-bottom: 1px solid #e0e0e0;
                padding-bottom: 10px;
            }
            footer {
                text-align: center;
                margin-top: 40px;
                padding: 20px 0;
                border-top: 1px solid #e0e0e0;
                color: #666;
            }
            .config-info {
                background-color: #fff8e1;
                border-left: 4px solid #ffc107;
                padding: 10px 15px;
                margin: 15px 0;
                border-radius: 0 5px 5px 0;
            }
        </style>
    </head>
    <body>
        <header>
            <div class="container">
                <h1>API Router System</h1>
                <p>Routes requests from OpenAI, Anthropic, and Google APIs to Codegen SDK</p>
            </div>
        </header>

        <div class="container">
            <div class="card">
                <div id="status-container">
                    <h2>Health Status</h2>
                    <div id="health-status" class="status">Checking...</div>
                </div>
                
                <div class="config-info">
                    <p><strong>Routing to:</strong> <span id="routing-to">Checking...</span></p>
                    <p>To change the Codegen SDK endpoint, set the <code>CODEGEN_API_URL</code> environment variable.</p>
                </div>
            </div>
            
            <div class="card">
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
            </div>
            
            <div class="card">
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
            
            <div class="card">
                <h2>How to Use</h2>
                <p>To use this API router with your existing applications:</p>
                <ol>
                    <li>Start this server on your desired host and port</li>
                    <li>In your application that uses OpenAI, Anthropic, or Google APIs, change the API base URL to point to this server</li>
                    <li>No API keys or other configuration needed - all requests will be routed to the Codegen SDK</li>
                </ol>
                
                <h3>Example Configuration</h3>
                <div class="endpoint">
                    <strong>OpenAI:</strong> <code>OPENAI_API_BASE=http://localhost:8887/v1</code>
                </div>
                <div class="endpoint">
                    <strong>Anthropic:</strong> <code>ANTHROPIC_API_URL=http://localhost:8887/v1</code>
                </div>
                <div class="endpoint">
                    <strong>Google/Gemini:</strong> <code>GEMINI_API_URL=http://localhost:8887/v1</code>
                </div>
            </div>
        </div>

        <footer>
            <div class="container">
                <p>API Router System &copy; 2024</p>
            </div>
        </footer>
        
        <script>
            // Check server health on page load
            document.addEventListener('DOMContentLoaded', checkHealth);
            
            function checkHealth() {
                fetch('/health')
                    .then(response => response.json())
                    .then(data => {
                        const statusElement = document.getElementById('health-status');
                        const routingElement = document.getElementById('routing-to');
                        
                        if (data.status === 'healthy') {
                            statusElement.className = 'status healthy';
                            statusElement.innerHTML = '✅ Server is healthy';
                            
                            if (data.routing_to) {
                                routingElement.textContent = data.routing_to;
                            }
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
    logger.info(f"Starting API Router System on {host}:{port}")
    logger.info(f"Routing requests to Codegen SDK at: {CODEGEN_API_URL}")
    logger.info(f"Supported providers: openai, anthropic, google")
    
    uvicorn.run(
        app,
        host=host,
        port=port,
        log_level="info"
    )


if __name__ == "__main__":
    start_server()

