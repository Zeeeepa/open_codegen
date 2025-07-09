#!/usr/bin/env python3
"""
Codegen AI Proxy - Transparent API Gateway
Intercepts OpenAI, Anthropic, and Gemini API calls and routes them to Codegen API
"""

import os
import logging
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import StreamingResponse, JSONResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
import httpx
import json
from typing import Dict, Any, Optional
import yaml
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=getattr(logging, os.getenv("LOG_LEVEL", "INFO")),
    format='%(asctime)s | %(name)s | %(levelname)s | %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="Codegen AI Proxy",
    description="Transparent proxy for OpenAI, Anthropic, and Gemini APIs → Codegen API",
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

# Configuration
class Config:
    def __init__(self):
        self.codegen_api_key = os.getenv("CODEGEN_API_KEY", "your-codegen-api-key-here")
        self.codegen_base_url = os.getenv("CODEGEN_BASE_URL", "https://api.codegen.com")
        self.default_system_message = os.getenv("DEFAULT_SYSTEM_MESSAGE", "You are a helpful AI assistant.")
        self.log_requests = os.getenv("LOG_REQUESTS", "true").lower() == "true"
        
        # Load config file if exists
        config_path = Path("config/config.yaml")
        if config_path.exists():
            try:
                with open(config_path) as f:
                    file_config = yaml.safe_load(f)
                    self._update_from_dict(file_config)
            except Exception as e:
                logger.warning(f"Failed to load config file: {e}")
    
    def _update_from_dict(self, config_dict: Dict[str, Any]):
        """Update configuration from dictionary"""
        if "codegen" in config_dict:
            codegen_config = config_dict["codegen"]
            self.codegen_api_key = codegen_config.get("api_key", self.codegen_api_key)
            self.codegen_base_url = codegen_config.get("base_url", self.codegen_base_url)
        
        if "system_message" in config_dict:
            self.default_system_message = config_dict["system_message"]

config = Config()

# HTTP client for Codegen API
client = httpx.AsyncClient(timeout=300.0)

async def inject_system_message(messages: list, system_message: Optional[str] = None) -> list:
    """Inject system message into conversation"""
    if not system_message:
        system_message = config.default_system_message
    
    # Check if there's already a system message
    has_system = any(msg.get("role") == "system" for msg in messages)
    
    if not has_system and system_message:
        # Prepend system message
        return [{"role": "system", "content": system_message}] + messages
    
    return messages

async def transform_to_codegen_request(request_data: Dict[str, Any], provider: str) -> Dict[str, Any]:
    """Transform provider-specific request to Codegen format"""
    
    if provider == "openai":
        # OpenAI format is already compatible, just inject system message
        if "messages" in request_data:
            request_data["messages"] = await inject_system_message(request_data["messages"])
        return request_data
    
    elif provider == "anthropic":
        # Transform Anthropic format to OpenAI format
        messages = []
        
        # Handle system message from Anthropic request
        system_msg = request_data.get("system", config.default_system_message)
        if system_msg:
            messages.append({"role": "system", "content": system_msg})
        
        # Transform Anthropic messages
        for msg in request_data.get("messages", []):
            if msg["role"] in ["user", "assistant"]:
                content = msg["content"]
                if isinstance(content, list):
                    # Handle complex content (text + images)
                    text_content = ""
                    for item in content:
                        if item.get("type") == "text":
                            text_content += item.get("text", "")
                    messages.append({"role": msg["role"], "content": text_content})
                else:
                    messages.append({"role": msg["role"], "content": content})
        
        return {
            "model": request_data.get("model", "claude-3-sonnet-20240229"),
            "messages": messages,
            "max_tokens": request_data.get("max_tokens", 1000),
            "temperature": request_data.get("temperature", 0.7),
            "stream": request_data.get("stream", False)
        }
    
    elif provider == "gemini":
        # Transform Gemini format to OpenAI format
        messages = []
        
        # Add system message
        messages.append({"role": "system", "content": config.default_system_message})
        
        # Transform Gemini contents to messages
        for content in request_data.get("contents", []):
            role = "user"  # Gemini uses "user" role primarily
            text = ""
            
            for part in content.get("parts", []):
                if "text" in part:
                    text += part["text"]
            
            if text:
                messages.append({"role": role, "content": text})
        
        generation_config = request_data.get("generationConfig", {})
        
        return {
            "model": "gemini-pro",
            "messages": messages,
            "max_tokens": generation_config.get("maxOutputTokens", 1000),
            "temperature": generation_config.get("temperature", 0.7),
            "stream": False  # Handle streaming separately
        }
    
    return request_data

async def transform_codegen_response(response_data: Dict[str, Any], provider: str) -> Dict[str, Any]:
    """Transform Codegen response to provider-specific format"""
    
    if provider == "openai":
        # Already in OpenAI format
        return response_data
    
    elif provider == "anthropic":
        # Transform to Anthropic format
        if "choices" in response_data and response_data["choices"]:
            choice = response_data["choices"][0]
            message = choice.get("message", {})
            
            return {
                "id": response_data.get("id", "msg_123"),
                "type": "message",
                "role": "assistant",
                "content": [{"type": "text", "text": message.get("content", "")}],
                "model": response_data.get("model", "claude-3-sonnet-20240229"),
                "stop_reason": "end_turn" if choice.get("finish_reason") == "stop" else "max_tokens",
                "stop_sequence": None,
                "usage": {
                    "input_tokens": response_data.get("usage", {}).get("prompt_tokens", 0),
                    "output_tokens": response_data.get("usage", {}).get("completion_tokens", 0)
                }
            }
    
    elif provider == "gemini":
        # Transform to Gemini format
        if "choices" in response_data and response_data["choices"]:
            choice = response_data["choices"][0]
            message = choice.get("message", {})
            
            return {
                "candidates": [{
                    "content": {
                        "parts": [{"text": message.get("content", "")}],
                        "role": "model"
                    },
                    "finishReason": "STOP" if choice.get("finish_reason") == "stop" else "MAX_TOKENS",
                    "index": 0,
                    "safetyRatings": []
                }],
                "promptFeedback": {
                    "safetyRatings": []
                }
            }
    
    return response_data

# OpenAI API Routes
@app.api_route("/v1/chat/completions", methods=["POST"])
@app.api_route("/chat/completions", methods=["POST"])
async def openai_chat_completions(request: Request):
    """OpenAI Chat Completions API"""
    try:
        request_data = await request.json()
        
        if config.log_requests:
            logger.info(f"OpenAI Chat Request: {json.dumps(request_data, indent=2)}")
        
        # Transform request
        codegen_request = await transform_to_codegen_request(request_data, "openai")
        
        # Forward to Codegen API
        headers = {
            "Authorization": f"Bearer {config.codegen_api_key}",
            "Content-Type": "application/json"
        }
        
        response = await client.post(
            f"{config.codegen_base_url}/v1/chat/completions",
            json=codegen_request,
            headers=headers
        )
        
        if response.status_code != 200:
            logger.error(f"Codegen API error: {response.status_code} - {response.text}")
            raise HTTPException(status_code=response.status_code, detail=response.text)
        
        response_data = response.json()
        
        # Transform response
        final_response = await transform_codegen_response(response_data, "openai")
        
        if config.log_requests:
            logger.info(f"OpenAI Response: {json.dumps(final_response, indent=2)}")
        
        return JSONResponse(content=final_response)
        
    except Exception as e:
        logger.error(f"Error in OpenAI chat completions: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.api_route("/v1/models", methods=["GET"])
@app.api_route("/models", methods=["GET"])
async def openai_models():
    """OpenAI Models API"""
    return JSONResponse(content={
        "object": "list",
        "data": [
            {
                "id": "gpt-3.5-turbo",
                "object": "model",
                "created": 1677610602,
                "owned_by": "openai",
                "permission": [],
                "root": "gpt-3.5-turbo",
                "parent": None
            },
            {
                "id": "gpt-4",
                "object": "model", 
                "created": 1687882411,
                "owned_by": "openai",
                "permission": [],
                "root": "gpt-4",
                "parent": None
            }
        ]
    })

# Anthropic API Routes
@app.api_route("/v1/messages", methods=["POST"])
async def anthropic_messages(request: Request):
    """Anthropic Messages API"""
    try:
        request_data = await request.json()
        
        if config.log_requests:
            logger.info(f"Anthropic Request: {json.dumps(request_data, indent=2)}")
        
        # Transform request
        codegen_request = await transform_to_codegen_request(request_data, "anthropic")
        
        # Forward to Codegen API
        headers = {
            "Authorization": f"Bearer {config.codegen_api_key}",
            "Content-Type": "application/json"
        }
        
        response = await client.post(
            f"{config.codegen_base_url}/v1/chat/completions",
            json=codegen_request,
            headers=headers
        )
        
        if response.status_code != 200:
            logger.error(f"Codegen API error: {response.status_code} - {response.text}")
            raise HTTPException(status_code=response.status_code, detail=response.text)
        
        response_data = response.json()
        
        # Transform response
        final_response = await transform_codegen_response(response_data, "anthropic")
        
        if config.log_requests:
            logger.info(f"Anthropic Response: {json.dumps(final_response, indent=2)}")
        
        return JSONResponse(content=final_response)
        
    except Exception as e:
        logger.error(f"Error in Anthropic messages: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Gemini API Routes
@app.api_route("/v1/models/{model}:generateContent", methods=["POST"])
async def gemini_generate_content(model: str, request: Request):
    """Google Gemini Generate Content API"""
    try:
        request_data = await request.json()
        
        if config.log_requests:
            logger.info(f"Gemini Request: {json.dumps(request_data, indent=2)}")
        
        # Transform request
        codegen_request = await transform_to_codegen_request(request_data, "gemini")
        
        # Forward to Codegen API
        headers = {
            "Authorization": f"Bearer {config.codegen_api_key}",
            "Content-Type": "application/json"
        }
        
        response = await client.post(
            f"{config.codegen_base_url}/v1/chat/completions",
            json=codegen_request,
            headers=headers
        )
        
        if response.status_code != 200:
            logger.error(f"Codegen API error: {response.status_code} - {response.text}")
            raise HTTPException(status_code=response.status_code, detail=response.text)
        
        response_data = response.json()
        
        # Transform response
        final_response = await transform_codegen_response(response_data, "gemini")
        
        if config.log_requests:
            logger.info(f"Gemini Response: {json.dumps(final_response, indent=2)}")
        
        return JSONResponse(content=final_response)
        
    except Exception as e:
        logger.error(f"Error in Gemini generate content: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Health and Status
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "codegen-ai-proxy"}

@app.get("/status")
async def status():
    """Status endpoint with configuration info"""
    return {
        "status": "running",
        "service": "codegen-ai-proxy",
        "version": "1.0.0",
        "codegen_base_url": config.codegen_base_url,
        "system_message_configured": bool(config.default_system_message),
        "endpoints": {
            "openai": "http://localhost:8000/v1/chat/completions",
            "anthropic": "http://localhost:8000/v1/messages", 
            "gemini": "http://localhost:8000/v1/models/gemini-pro:generateContent"
        }
    }

# Web UI
@app.get("/", response_class=HTMLResponse)
async def web_ui():
    """Simple web UI for monitoring and configuration"""
    html_content = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Codegen AI Proxy</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 40px; background: #f5f5f5; }
            .container { max-width: 800px; margin: 0 auto; background: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
            .header { text-align: center; margin-bottom: 30px; }
            .endpoint { background: #f8f9fa; padding: 15px; margin: 10px 0; border-radius: 5px; border-left: 4px solid #007bff; }
            .endpoint-url { font-family: monospace; background: #e9ecef; padding: 5px; border-radius: 3px; }
            .status { padding: 10px; border-radius: 5px; margin: 20px 0; }
            .status.healthy { background: #d4edda; color: #155724; border: 1px solid #c3e6cb; }
            .copy-btn { background: #007bff; color: white; border: none; padding: 5px 10px; border-radius: 3px; cursor: pointer; margin-left: 10px; }
            .copy-btn:hover { background: #0056b3; }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>🚀 Codegen AI Proxy</h1>
                <p>Transparent API Gateway for OpenAI, Anthropic & Gemini → Codegen</p>
            </div>
            
            <div class="status healthy">
                ✅ Proxy is running and ready to intercept API calls!
            </div>
            
            <h2>📡 API Endpoints</h2>
            <p>Use these URLs in your applications (no code changes needed!):</p>
            
            <div class="endpoint">
                <h3>🟢 OpenAI API</h3>
                <div class="endpoint-url">http://localhost:8000/v1/chat/completions</div>
                <button class="copy-btn" onclick="copyToClipboard('http://localhost:8000/v1/chat/completions')">Copy</button>
                <p><small>Drop-in replacement for api.openai.com</small></p>
            </div>
            
            <div class="endpoint">
                <h3>🟠 Anthropic API</h3>
                <div class="endpoint-url">http://localhost:8000/v1/messages</div>
                <button class="copy-btn" onclick="copyToClipboard('http://localhost:8000/v1/messages')">Copy</button>
                <p><small>Drop-in replacement for api.anthropic.com</small></p>
            </div>
            
            <div class="endpoint">
                <h3>🔷 Google Gemini API</h3>
                <div class="endpoint-url">http://localhost:8000/v1/models/gemini-pro:generateContent</div>
                <button class="copy-btn" onclick="copyToClipboard('http://localhost:8000/v1/models/gemini-pro:generateContent')">Copy</button>
                <p><small>Drop-in replacement for generativelanguage.googleapis.com</small></p>
            </div>
            
            <h2>💡 Usage Examples</h2>
            <div class="endpoint">
                <h4>Python OpenAI Client:</h4>
                <pre><code>import openai
openai.api_base = "http://localhost:8000/v1"
# Your existing code works unchanged!</code></pre>
            </div>
            
            <div class="endpoint">
                <h4>Environment Variable:</h4>
                <pre><code>export OPENAI_API_BASE=http://localhost:8000/v1</code></pre>
            </div>
            
            <h2>⚙️ Configuration</h2>
            <p>System Message: <strong>""" + config.default_system_message + """</strong></p>
            <p>Codegen API: <strong>""" + config.codegen_base_url + """</strong></p>
            
            <div style="margin-top: 30px; text-align: center; color: #666;">
                <p>🔄 All API calls are automatically routed to Codegen with system message injection</p>
            </div>
        </div>
        
        <script>
            function copyToClipboard(text) {
                navigator.clipboard.writeText(text).then(function() {
                    alert('Copied to clipboard: ' + text);
                });
            }
        </script>
    </body>
    </html>
    """
    return HTMLResponse(content=html_content)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
