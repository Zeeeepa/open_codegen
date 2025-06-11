"""
Unified API System for OpenAI, Anthropic, and Google APIs.
This module provides a consolidated interface for all three APIs.
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

# API endpoints
OPENAI_API_URL = "https://api.openai.com/v1/chat/completions"
ANTHROPIC_API_URL = "https://api.anthropic.com/v1/messages"
GOOGLE_API_URL = "https://generativelanguage.googleapis.com/v1beta/models"

# Get API keys from environment variables
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "")
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")
GOOGLE_API_KEY = os.environ.get("GOOGLE_API_KEY", "")


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
        
        # Check if API key is available
        api_key = OPENAI_API_KEY
        if not api_key:
            logger.warning("OpenAI API key not found. Using simulated response.")
            return create_simulated_openai_response(body)
        
        # Forward request to OpenAI API
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}"
        }
        
        logger.info(f"Sending request to OpenAI API: {json.dumps(body)}")
        response = requests.post(OPENAI_API_URL, headers=headers, json=body)
        
        # Check response status
        if response.status_code != 200:
            logger.error(f"OpenAI API error: {response.status_code} - {response.text}")
            return JSONResponse(
                status_code=response.status_code,
                content=response.json() if response.text else {"error": "Unknown error"}
            )
        
        # Return response from OpenAI
        return response.json()
        
    except Exception as e:
        logger.error(f"OpenAI chat completion error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


def create_simulated_openai_response(body):
    """Create a simulated OpenAI response for testing."""
    # Extract message
    messages = body.get("messages", [])
    user_message = None
    for msg in reversed(messages):
        if msg.get("role") == "user":
            user_message = msg.get("content")
            break
    
    if not user_message:
        user_message = "No message provided"
    
    # Get model
    model = body.get("model", "gpt-3.5-turbo")
    
    # Create mock response
    return {
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


# Anthropic endpoint
@app.post("/v1/anthropic/completions")
async def anthropic_completions(request: Request):
    """Anthropic completions endpoint."""
    try:
        # Parse request body
        body = await request.json()
        
        # Check if API key is available
        api_key = ANTHROPIC_API_KEY
        if not api_key:
            logger.warning("Anthropic API key not found. Using simulated response.")
            return create_simulated_anthropic_response(body)
        
        # Convert from our API format to Anthropic's format if needed
        anthropic_body = convert_to_anthropic_format(body)
        
        # Forward request to Anthropic API
        headers = {
            "Content-Type": "application/json",
            "X-API-Key": api_key,
            "anthropic-version": "2023-06-01"
        }
        
        logger.info(f"Sending request to Anthropic API: {json.dumps(anthropic_body)}")
        response = requests.post(ANTHROPIC_API_URL, headers=headers, json=anthropic_body)
        
        # Check response status
        if response.status_code != 200:
            logger.error(f"Anthropic API error: {response.status_code} - {response.text}")
            return JSONResponse(
                status_code=response.status_code,
                content=response.json() if response.text else {"error": "Unknown error"}
            )
        
        # Return response from Anthropic
        return response.json()
        
    except Exception as e:
        logger.error(f"Anthropic completion error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


def convert_to_anthropic_format(body):
    """Convert from our API format to Anthropic's format."""
    # Extract messages
    messages = body.get("messages", [])
    
    # If already in Anthropic format, return as is
    if "model" in body and "messages" in body:
        return body
    
    # Convert to Anthropic format
    anthropic_body = {
        "model": body.get("model", "claude-3-sonnet-20240229"),
        "messages": messages,
        "max_tokens": body.get("max_tokens", 1024)
    }
    
    return anthropic_body


def create_simulated_anthropic_response(body):
    """Create a simulated Anthropic response for testing."""
    # Extract message
    messages = body.get("messages", [])
    user_message = None
    for msg in reversed(messages):
        if msg.get("role") == "user":
            user_message = msg.get("content")
            break
    
    if not user_message:
        user_message = "No message provided"
    
    # Get model
    model = body.get("model", "claude-3-sonnet-20240229")
    
    # Create mock response
    return {
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


# Google/Gemini endpoint
@app.post("/v1/gemini/completions")
async def gemini_completions(request: Request):
    """Google Gemini completions endpoint."""
    try:
        # Parse request body
        body = await request.json()
        
        # Check if API key is available
        api_key = GOOGLE_API_KEY
        if not api_key:
            logger.warning("Google API key not found. Using simulated response.")
            return create_simulated_gemini_response(body)
        
        # Extract message from different possible formats
        user_message = extract_user_message(body)
        
        # Get model
        model = body.get("model", "gemini-1.5-pro")
        model_endpoint = f"{model}:generateContent"
        
        # Prepare Google API request
        google_url = f"{GOOGLE_API_URL}/{model_endpoint}?key={api_key}"
        
        # Convert to Google format
        google_body = convert_to_google_format(body, user_message)
        
        # Forward request to Google API
        headers = {
            "Content-Type": "application/json"
        }
        
        logger.info(f"Sending request to Google API: {json.dumps(google_body)}")
        response = requests.post(google_url, headers=headers, json=google_body)
        
        # Check response status
        if response.status_code != 200:
            logger.error(f"Google API error: {response.status_code} - {response.text}")
            return JSONResponse(
                status_code=response.status_code,
                content=response.json() if response.text else {"error": "Unknown error"}
            )
        
        # Return response from Google
        return response.json()
        
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
    
    return user_message or "No message provided"


def convert_to_google_format(body, user_message):
    """Convert from our API format to Google's format."""
    # If already in Google format, return as is
    if "contents" in body:
        return body
    
    # Convert to Google format
    google_body = {
        "contents": [
            {
                "parts": [
                    {
                        "text": user_message
                    }
                ]
            }
        ]
    }
    
    return google_body


def create_simulated_gemini_response(body):
    """Create a simulated Gemini response for testing."""
    # Extract message
    user_message = extract_user_message(body)
    
    # Create mock response
    return {
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
    
    # Check for API keys
    if not OPENAI_API_KEY:
        logger.warning("OPENAI_API_KEY not found in environment variables. OpenAI API will use simulated responses.")
    if not ANTHROPIC_API_KEY:
        logger.warning("ANTHROPIC_API_KEY not found in environment variables. Anthropic API will use simulated responses.")
    if not GOOGLE_API_KEY:
        logger.warning("GOOGLE_API_KEY not found in environment variables. Google API will use simulated responses.")
    
    uvicorn.run(
        app,
        host=host,
        port=port,
        log_level="info"
    )


if __name__ == "__main__":
    start_server()

