#!/usr/bin/env python3
import os
import json
import time
import logging
import requests
from pathlib import Path
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from codegen.agents.agent import Agent

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(levelname)s:%(name)s:%(message)s"
)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI()

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve static files if they exist
static_path = Path("static")
if static_path.exists():
    app.mount("/static", StaticFiles(directory="static"), name="static")

# Environment variables
CODEGEN_ORG_ID = os.environ.get("CODEGEN_ORG_ID", "")
CODEGEN_TOKEN = os.environ.get("CODEGEN_TOKEN", "")
SERVER_HOST = os.environ.get("SERVER_HOST", "localhost")
SERVER_PORT = int(os.environ.get("SERVER_PORT", "8887"))

# Initialize Codegen Agent
agent = Agent(
    org_id=CODEGEN_ORG_ID,
    token=CODEGEN_TOKEN
)

# Health endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "timestamp": time.time(),
        "providers": ["openai", "anthropic", "google"],
        "routing_to": agent.api_url
    }


# Root endpoint - HTML UI
@app.get("/", response_class=HTMLResponse)
async def root():
    """Root endpoint - returns HTML UI."""
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>API Router System</title>
        <style>
            body {
                font-family: Arial, sans-serif;
                max-width: 800px;
                margin: 0 auto;
                padding: 20px;
                line-height: 1.6;
            }
            .card {
                background: #f9f9f9;
                border-radius: 8px;
                padding: 20px;
                margin-bottom: 20px;
                box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
            }
            .status {
                padding: 8px 12px;
                border-radius: 4px;
                display: inline-block;
                margin-top: 10px;
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
                background: #b44ac0;
                color: white;
            }
            .google {
                background: #4285f4;
                color: white;
            }
            .hidden {
                display: none;
            }
            pre {
                background: #f1f1f1;
                padding: 10px;
                border-radius: 5px;
                overflow-x: auto;
            }
            textarea {
                width: 100%;
                padding: 8px;
                border-radius: 5px;
                border: 1px solid #ddd;
                margin-bottom: 10px;
            }
        </style>
    </head>
    <body>
        <h1>API Router System</h1>
        
        <div class="card">
            <h2>Status</h2>
            <p>Routing requests to Codegen SDK at: <code id="api-url"></code></p>
            <p>Server status: <span id="server-status" class="status">Checking...</span></p>
        </div>
        
        <div class="card">
            <h2>Test API Endpoints</h2>
            <div>
                <h3>Simple Test</h3>
                <div>
                    <button class="test-button openai" onclick="testAPI('openai')">🟢 Test OpenAI API</button>
                    <button class="test-button anthropic" onclick="testAPI('anthropic')">🟣 Test Anthropic API</button>
                    <button class="test-button google" onclick="testAPI('google')">🔵 Test Google API</button>
                </div>
            </div>
            
            <div>
                <h3>Custom Prompt</h3>
                <textarea id="custom-prompt" rows="3" placeholder="Enter your custom prompt here...">Hello! Please respond with a short greeting.</textarea>
                <div>
                    <button class="test-button openai" onclick="testAPIWithCustomPrompt('openai')">🟢 Test OpenAI API</button>
                    <button class="test-button anthropic" onclick="testAPIWithCustomPrompt('anthropic')">🟣 Test Anthropic API</button>
                    <button class="test-button google" onclick="testAPIWithCustomPrompt('google')">🔵 Test Google API</button>
                </div>
            </div>
            
            <div id="response-container" class="hidden">
                <h3>Response:</h3>
                <pre id="response-content"></pre>
            </div>
        </div>
        
        <script>
            document.getElementById('api-url').textContent = window.location.origin;
            
            // Check server health on page load
            window.onload = function() {
                checkHealth();
            };
            
            function checkHealth() {
                const statusElement = document.getElementById('server-status');
                
                fetch('/health')
                    .then(response => response.json())
                    .then(data => {
                        if (data.status === 'healthy') {
                            statusElement.className = 'status healthy';
                            statusElement.innerHTML = '✅ Server is healthy';
                        } else {
                            statusElement.className = 'status unhealthy';
                            statusElement.innerHTML = '❌ Server is unhealthy';
                        }
                    })
                    .catch(error => {
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
            
            function sendRequest(provider, prompt) {
                const responseContainer = document.getElementById('response-container');
                const responseContent = document.getElementById('response-content');
                
                responseContainer.className = 'hidden';
                responseContent.textContent = 'Loading...';
                
                let endpoint = '';
                let payload = {};
                
                if (provider === 'openai') {
                    endpoint = '/v1/chat/completions';
                    payload = {
                        model: 'gpt-3.5-turbo',
                        messages: [
                            { role: 'user', content: prompt }
                        ]
                    };
                } else if (provider === 'anthropic') {
                    endpoint = '/v1/anthropic/completions';
                    payload = {
                        model: 'claude-3-sonnet-20240229',
                        messages: [
                            { role: 'user', content: prompt }
                        ]
                    };
                } else if (provider === 'google') {
                    endpoint = '/v1/gemini/completions';
                    payload = {
                        model: 'gemini-1.5-pro',
                        messages: [
                            { role: 'user', content: prompt }
                        ]
                    };
                }
                
                fetch(endpoint, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify(payload)
                })
                .then(response => {
                    if (!response.ok) {
                        throw new Error(`HTTP error! Status: ${response.status}`);
                    }
                    return response.json();
                })
                .then(data => {
                    responseContainer.className = '';
                    responseContent.textContent = JSON.stringify(data, null, 2);
                })
                .catch(error => {
                    responseContainer.className = '';
                    responseContent.textContent = `Error: ${error.message}`;
                    console.error('API request error:', error);
                });
            }
        </script>
    </body>
    </html>
    """


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
        
        # Use the Codegen SDK to run the agent
        logger.info(f"Routing OpenAI request to Codegen SDK: {user_message}")
        
        try:
            # Run the agent with the prompt
            task = agent.run(
                prompt=user_message,
                source="openai_proxy",
                model=body.get("model", "gpt-3.5-turbo")
            )
            
            # Wait for the task to complete (with timeout)
            start_time = time.time()
            timeout = 30  # 30 seconds timeout
            
            while task.status not in ["completed", "failed", "error"] and time.time() - start_time < timeout:
                time.sleep(1)
                task.refresh()
            
            if task.status == "completed":
                generated_text = task.result
                logger.info(f"Codegen SDK task completed successfully")
            else:
                logger.error(f"Codegen SDK task failed or timed out: {task.status}")
                generated_text = f"Error: Task {task.status}. Please try again later."
        
        except Exception as e:
            logger.error(f"Error running Codegen agent: {e}")
            raise HTTPException(status_code=500, detail=f"Error running Codegen agent: {str(e)}")
        
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
        
        # Use the Codegen SDK to run the agent
        logger.info(f"Routing Anthropic request to Codegen SDK: {user_message}")
        
        try:
            # Run the agent with the prompt
            task = agent.run(
                prompt=user_message,
                source="anthropic_proxy",
                model=body.get("model", "claude-3-sonnet-20240229")
            )
            
            # Wait for the task to complete (with timeout)
            start_time = time.time()
            timeout = 30  # 30 seconds timeout
            
            while task.status not in ["completed", "failed", "error"] and time.time() - start_time < timeout:
                time.sleep(1)
                task.refresh()
            
            if task.status == "completed":
                generated_text = task.result
                logger.info(f"Codegen SDK task completed successfully")
            else:
                logger.error(f"Codegen SDK task failed or timed out: {task.status}")
                generated_text = f"Error: Task {task.status}. Please try again later."
        
        except Exception as e:
            logger.error(f"Error running Codegen agent: {e}")
            raise HTTPException(status_code=500, detail=f"Error running Codegen agent: {str(e)}")
        
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
        
        # Use the Codegen SDK to run the agent
        logger.info(f"Routing Google request to Codegen SDK: {user_message}")
        
        try:
            # Run the agent with the prompt
            task = agent.run(
                prompt=user_message,
                source="google_proxy",
                model=body.get("model", "gemini-1.5-pro")
            )
            
            # Wait for the task to complete (with timeout)
            start_time = time.time()
            timeout = 30  # 30 seconds timeout
            
            while task.status not in ["completed", "failed", "error"] and time.time() - start_time < timeout:
                time.sleep(1)
                task.refresh()
            
            if task.status == "completed":
                generated_text = task.result
                logger.info(f"Codegen SDK task completed successfully")
            else:
                logger.error(f"Codegen SDK task failed or timed out: {task.status}")
                generated_text = f"Error: Task {task.status}. Please try again later."
        
        except Exception as e:
            logger.error(f"Error running Codegen agent: {e}")
            raise HTTPException(status_code=500, detail=f"Error running Codegen agent: {str(e)}")
        
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
    
    # If still not found, try prompt field (fallback)
    if not user_message:
        user_message = body.get("prompt", "")
    
    return user_message


def start_server(host="localhost", port=8887):
    """Start the FastAPI server."""
    import uvicorn
    logger.info(f"Starting API Router System on {host}:{port}")
    logger.info(f"Routing requests to Codegen SDK at: {agent.api_url}")
    logger.info(f"Supported providers: openai, anthropic, google")
    uvicorn.run(app, host=host, port=port)


if __name__ == "__main__":
    start_server(SERVER_HOST, SERVER_PORT)
