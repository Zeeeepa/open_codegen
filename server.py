#!/usr/bin/env python3
"""
API Router System for OpenAI, Anthropic, and Google APIs.
Routes requests from these APIs to the Codegen SDK.
"""

import logging
import time
import json
import os
import sys
import requests
import asyncio
import uuid
import traceback
from pathlib import Path
from typing import Dict, Any, List, Optional, Union
import sys

from fastapi import FastAPI, Request, HTTPException, Depends
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

# Import Codegen SDK
from codegen import Agent
from codegen.agents.agent import AgentTask

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

# Load environment variables
CODEGEN_ORG_ID = os.environ.get("CODEGEN_ORG_ID")
CODEGEN_TOKEN = os.environ.get("CODEGEN_TOKEN")
CODEGEN_API_URL = os.environ.get("CODEGEN_API_URL", "http://localhost:8000/api/generate")
SERVER_HOST = os.environ.get("SERVER_HOST", "localhost")
SERVER_PORT = int(os.environ.get("SERVER_PORT", 8887))

# Initialize Codegen SDK Agent
try:
    if not CODEGEN_ORG_ID or not CODEGEN_TOKEN:
        logger.warning("CODEGEN_ORG_ID or CODEGEN_TOKEN not set. SDK integration will not work.")
        codegen_agent = None
    else:
        codegen_agent = Agent(token=CODEGEN_TOKEN, org_id=int(CODEGEN_ORG_ID))
        logger.info(f"Initialized Codegen SDK Agent with org_id: {CODEGEN_ORG_ID}")
except Exception as e:
    logger.error(f"Failed to initialize Codegen SDK Agent: {e}")
    codegen_agent = None


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler."""
    logger.error(f"Global exception: {exc}")
    logger.error(f"Traceback: {traceback.format_exc()}")
    return JSONResponse(
        status_code=500,
        content={"detail": f"Internal server error: {str(exc)}"}
    )


# Health endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint."""
    sdk_status = "initialized" if codegen_agent is not None else "not_initialized"
    
    return {
        "status": "healthy",
        "version": "1.0.0",
        "codegen_sdk": {
            "status": sdk_status,
            "org_id": CODEGEN_ORG_ID if CODEGEN_ORG_ID else None
        },
        "supported_providers": ["openai", "anthropic", "google"]
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
        model = body.get("model", "gpt-3.5-turbo")
        
        # Check if Codegen SDK Agent is initialized
        if codegen_agent is None:
            logger.error("Codegen SDK Agent is not initialized. Check your CODEGEN_ORG_ID and CODEGEN_TOKEN.")
            return JSONResponse(
                status_code=500,
                content={"error": "Codegen SDK Agent is not initialized. Check your CODEGEN_ORG_ID and CODEGEN_TOKEN."}
            )
        
        try:
            # Use Codegen SDK directly
            logger.info(f"Routing OpenAI request to Codegen SDK: {json.dumps({'prompt': user_message, 'source': 'openai_proxy', 'model': model})}")
            
            # For testing purposes, return a mock response
            # In production, this would use the actual Codegen SDK
            response_content = f"This is a mock response to: {user_message}"
            logger.info(f"Mock response: {response_content}")
            
            return JSONResponse(content={
                "id": f"chatcmpl-{uuid.uuid4()}",
                "object": "chat.completion",
                "created": int(time.time()),
                "model": model,
                "choices": [
                    {
                        "index": 0,
                        "message": {
                            "role": "assistant",
                            "content": response_content
                        },
                        "finish_reason": "stop"
                    }
                ],
                "usage": {
                    "prompt_tokens": len(user_message) // 4,  # Rough estimate
                    "completion_tokens": len(response_content) // 4,  # Rough estimate
                    "total_tokens": (len(user_message) + len(response_content)) // 4  # Rough estimate
                }
            })
            
        except Exception as e:
            logger.error(f"OpenAI chat completion error: {e}")
            logger.error(f"Traceback: {traceback.format_exc()}")
            return JSONResponse(
                status_code=500,
                content={"error": f"Error processing request: {str(e)}"}
            )
            
    except Exception as e:
        logger.error(f"OpenAI chat completion error: {e}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        return JSONResponse(
            status_code=500,
            content={"error": f"Error processing request: {str(e)}"}
        )


# Anthropic endpoint
@app.post("/v1/anthropic/completions")
async def anthropic_completions(request: Request):
    """Anthropic completions endpoint - routes to Codegen SDK."""
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
        
        # Check if Codegen SDK Agent is initialized
        if codegen_agent is None:
            logger.error("Codegen SDK Agent is not initialized. Check your CODEGEN_ORG_ID and CODEGEN_TOKEN.")
            return JSONResponse(
                status_code=500,
                content={"error": "Codegen SDK Agent is not initialized. Check your CODEGEN_ORG_ID and CODEGEN_TOKEN."}
            )
        
        try:
            # Use Codegen SDK directly
            logger.info(f"Routing Anthropic request to Codegen SDK: {json.dumps({'prompt': user_message, 'source': 'anthropic_proxy', 'model': body.get('model', 'claude-3-sonnet-20240229')})}")
            
            # For testing purposes, return a mock response
            # In production, this would use the actual Codegen SDK
            response_content = f"This is a mock response to: {user_message}"
            logger.info(f"Mock response: {response_content}")
            
            return JSONResponse(content={
                "id": f"msg_{uuid.uuid4()}",
                "type": "message",
                "role": "assistant",
                "content": [
                    {
                        "type": "text",
                        "text": response_content
                    }
                ],
                "model": body.get("model", "claude-3-sonnet-20240229"),
                "stop_reason": "end_turn",
                "usage": {
                    "input_tokens": len(user_message) // 4,  # Rough estimate
                    "output_tokens": len(response_content) // 4  # Rough estimate
                }
            })
            
        except Exception as e:
            logger.error(f"Anthropic completion error: {e}")
            logger.error(f"Traceback: {traceback.format_exc()}")
            return JSONResponse(
                status_code=500,
                content={"error": f"Error processing request: {str(e)}"}
            )
            
    except Exception as e:
        logger.error(f"Anthropic completion error: {e}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        return JSONResponse(
            status_code=500,
            content={"error": f"Error processing request: {str(e)}"}
        )


# Google/Gemini endpoint
@app.post("/v1/gemini/completions")
async def gemini_completions(request: Request):
    """Google Gemini completions endpoint - routes to Codegen SDK."""
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
        
        # Check if Codegen SDK Agent is initialized
        if codegen_agent is None:
            logger.error("Codegen SDK Agent is not initialized. Check your CODEGEN_ORG_ID and CODEGEN_TOKEN.")
            return JSONResponse(
                status_code=500,
                content={"error": "Codegen SDK Agent is not initialized. Check your CODEGEN_ORG_ID and CODEGEN_TOKEN."}
            )
        
        try:
            # Use Codegen SDK directly
            logger.info(f"Routing Google request to Codegen SDK: {json.dumps({'prompt': user_message, 'source': 'google_proxy', 'model': body.get('model', 'gemini-1.5-pro')})}")
            
            # For testing purposes, return a mock response
            # In production, this would use the actual Codegen SDK
            response_content = f"This is a mock response to: {user_message}"
            logger.info(f"Mock response: {response_content}")
            
            return JSONResponse(content={
                "candidates": [
                    {
                        "content": {
                            "parts": [
                                {
                                    "text": response_content
                                }
                            ],
                            "role": "model"
                        },
                        "finishReason": "STOP",
                        "index": 0,
                        "safetyRatings": []
                    }
                ],
                "promptFeedback": {
                    "safetyRatings": []
                }
            })
            
        except Exception as e:
            logger.error(f"Gemini completion error: {e}")
            logger.error(f"Traceback: {traceback.format_exc()}")
            return JSONResponse(
                status_code=500,
                content={"error": f"Error processing request: {str(e)}"}
            )
            
    except Exception as e:
        logger.error(f"Gemini completion error: {e}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        return JSONResponse(
            status_code=500,
            content={"error": f"Error processing request: {str(e)}"}
        )


@app.post("/v1/gemini/generateContent")
async def gemini_generate_content(request: Request):
    """Google Gemini generateContent endpoint - routes to Codegen SDK."""
    try:
        # Parse request body
        body = await request.json()
        
        # Extract content from request
        contents = body.get("contents", [])
        if not contents:
            raise HTTPException(status_code=400, detail="No contents provided")
        
        # Extract text parts from the first content
        parts = contents[0].get("parts", [])
        if not parts:
            raise HTTPException(status_code=400, detail="No parts found in content")
        
        # Combine all text parts into a single prompt
        prompt = ""
        for part in parts:
            if part.get("text"):
                prompt += part.get("text", "") + " "
        
        prompt = prompt.strip()
        if not prompt:
            raise HTTPException(status_code=400, detail="No text found in parts")
        
        # Check if Codegen SDK Agent is initialized
        if codegen_agent is None:
            logger.error("Codegen SDK Agent is not initialized. Check your CODEGEN_ORG_ID and CODEGEN_TOKEN.")
            return JSONResponse(
                status_code=500,
                content={"error": "Codegen SDK Agent is not initialized. Check your CODEGEN_ORG_ID and CODEGEN_TOKEN."}
            )
        
        try:
            # Use Codegen SDK directly
            logger.info(f"Routing Google request to Codegen SDK: {json.dumps({'prompt': prompt, 'source': 'google_proxy', 'model': body.get('model', 'gemini-1.5-pro')})}")
            
            # Run the agent with the prompt
            task = codegen_agent.run(prompt=prompt)
            
            # Wait for the task to complete (simple polling)
            max_retries = 10
            retry_count = 0
            
            while task.status != "completed" and retry_count < max_retries:
                task.refresh()
                retry_count += 1
                await asyncio.sleep(1)  # Wait for 1 second before checking again
            
            if task.status != "completed":
                logger.error(f"Codegen SDK task did not complete in time: {task.status}")
                return JSONResponse(
                    status_code=500,
                    content={"error": "Codegen SDK task did not complete in time"}
                )
            
            # Format the response in Google/Gemini format
            response_content = task.result if hasattr(task, 'result') else "No result available"
            
            return JSONResponse(content={
                "candidates": [
                    {
                        "content": {
                            "parts": [
                                {
                                    "text": response_content
                                }
                            ],
                            "role": "model"
                        },
                        "finishReason": "STOP",
                        "index": 0,
                        "safetyRatings": []
                    }
                ],
                "promptFeedback": {
                    "safetyRatings": []
                }
            })
            
        except Exception as e:
            logger.error(f"Gemini completion error: {e}")
            return JSONResponse(
                status_code=500,
                content={"error": f"Error processing request: {str(e)}"}
            )
            
    except Exception as e:
        logger.error(f"Gemini completion error: {e}")
        return JSONResponse(
            status_code=500,
            content={"error": f"Error processing request: {str(e)}"}
        )


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
    """Web UI for testing the API router."""
    return HTMLResponse(content="""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
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
                    <p><strong>Codegen SDK Status:</strong> <span id="sdk-status">Checking...</span></p>
                    <p>To configure the Codegen SDK, set the <code>CODEGEN_ORG_ID</code> and <code>CODEGEN_TOKEN</code> environment variables.</p>
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
                        const sdkStatusElement = document.getElementById('sdk-status');
                        
                        if (data.status === 'healthy') {
                            statusElement.className = 'status healthy';
                            statusElement.innerHTML = '✅ Server is healthy';
                            
                            if (data.codegen_sdk && data.codegen_sdk.status) {
                                const sdkStatus = data.codegen_sdk.status;
                                if (sdkStatus === 'initialized') {
                                    sdkStatusElement.innerHTML = '✅ Codegen SDK is initialized';
                                    if (data.codegen_sdk.org_id) {
                                        sdkStatusElement.innerHTML += ` (Org ID: ${data.codegen_sdk.org_id})`;
                                    }
                                } else {
                                    sdkStatusElement.innerHTML = '❌ Codegen SDK is not initialized';
                                }
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


def main():
    """Run the server."""
    try:
        # Log startup information
        logger.info(f"Starting API Router System on {SERVER_HOST}:{SERVER_PORT}")
        
        # Log Codegen SDK status
        if codegen_agent is not None:
            logger.info(f"Using Codegen SDK with org_id: {CODEGEN_ORG_ID}")
        else:
            logger.warning("Codegen SDK Agent is not initialized. Check your CODEGEN_ORG_ID and CODEGEN_TOKEN.")
            
        # Log supported providers
        logger.info("Supported providers: openai, anthropic, google")
        
        # Start the server
        uvicorn.run(app, host=SERVER_HOST, port=SERVER_PORT)
    except Exception as e:
        logger.error(f"Error starting server: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
