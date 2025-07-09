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
        self.codegen_api_key = os.getenv("CODEGEN_API_KEY", "")
        self.codegen_org_id = os.getenv("CODEGEN_ORG_ID", "")
        self.codegen_token = os.getenv("CODEGEN_TOKEN", "")
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
            self.codegen_org_id = codegen_config.get("org_id", self.codegen_org_id)
            self.codegen_token = codegen_config.get("token", self.codegen_token)
            self.codegen_base_url = codegen_config.get("base_url", self.codegen_base_url)
        
        if "system_message" in config_dict:
            self.default_system_message = config_dict["system_message"]
    
    def save_to_file(self):
        """Save current configuration to file"""
        config_data = {
            "codegen": {
                "api_key": self.codegen_api_key,
                "org_id": self.codegen_org_id,
                "token": self.codegen_token,
                "base_url": self.codegen_base_url
            },
            "system_message": self.default_system_message,
            "logging": {
                "level": "INFO",
                "log_requests": self.log_requests
            }
        }
        
        config_path = Path("config/config.yaml")
        config_path.parent.mkdir(exist_ok=True)
        
        with open(config_path, 'w') as f:
            yaml.dump(config_data, f, default_flow_style=False)
    
    def is_configured(self):
        """Check if Codegen credentials are configured"""
        return bool(self.codegen_org_id and self.codegen_token)

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
            "Authorization": f"Bearer {config.codegen_token}",
            "Content-Type": "application/json"
        }
        
        # Add org ID if available
        if config.codegen_org_id:
            headers["X-Org-ID"] = config.codegen_org_id
        
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
            "Authorization": f"Bearer {config.codegen_token}",
            "Content-Type": "application/json"
        }
        
        # Add org ID if available
        if config.codegen_org_id:
            headers["X-Org-ID"] = config.codegen_org_id
        
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
            "Authorization": f"Bearer {config.codegen_token}",
            "Content-Type": "application/json"
        }
        
        # Add org ID if available
        if config.codegen_org_id:
            headers["X-Org-ID"] = config.codegen_org_id
        
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

# Configuration API endpoints
@app.post("/api/config/verify")
async def verify_codegen_config(request: Request):
    """Verify Codegen API credentials"""
    try:
        data = await request.json()
        org_id = data.get("org_id", "")
        token = data.get("token", "")
        base_url = data.get("base_url", "https://api.codegen.com")
        
        if not org_id or not token:
            return JSONResponse(
                status_code=400,
                content={"success": False, "error": "Organization ID and Token are required"}
            )
        
        # Test the credentials by making a simple API call
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        
        if org_id:
            headers["X-Org-ID"] = org_id
        
        # Try a simple test request
        test_response = await client.get(
            f"{base_url}/health",
            headers=headers,
            timeout=10.0
        )
        
        if test_response.status_code == 200:
            return JSONResponse(content={
                "success": True,
                "message": "Credentials verified successfully!"
            })
        else:
            return JSONResponse(
                status_code=400,
                content={
                    "success": False,
                    "error": f"API returned status {test_response.status_code}: {test_response.text}"
                }
            )
            
    except Exception as e:
        logger.error(f"Error verifying credentials: {e}")
        return JSONResponse(
            status_code=500,
            content={"success": False, "error": f"Verification failed: {str(e)}"}
        )

@app.post("/api/config/save")
async def save_config(request: Request):
    """Save configuration"""
    try:
        data = await request.json()
        
        # Update configuration
        config.codegen_org_id = data.get("org_id", "")
        config.codegen_token = data.get("token", "")
        config.codegen_base_url = data.get("base_url", "https://api.codegen.com")
        config.default_system_message = data.get("system_message", "You are a helpful AI assistant.")
        
        # Save to file
        config.save_to_file()
        
        return JSONResponse(content={
            "success": True,
            "message": "Configuration saved successfully!"
        })
        
    except Exception as e:
        logger.error(f"Error saving configuration: {e}")
        return JSONResponse(
            status_code=500,
            content={"success": False, "error": f"Failed to save configuration: {str(e)}"}
        )

@app.get("/api/config")
async def get_config():
    """Get current configuration (without sensitive data)"""
    return JSONResponse(content={
        "org_id": config.codegen_org_id,
        "base_url": config.codegen_base_url,
        "system_message": config.default_system_message,
        "is_configured": config.is_configured(),
        "has_token": bool(config.codegen_token)
    })

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
        "codegen_configured": config.is_configured(),
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
    """Web UI with settings dialog for Codegen configuration"""
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Codegen AI Proxy</title>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <style>
            * {{ margin: 0; padding: 0; box-sizing: border-box; }}
            
            body {{ 
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; 
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                min-height: 100vh;
                display: flex;
                align-items: center;
                justify-content: center;
                color: #333;
            }}
            
            .container {{ 
                max-width: 900px; 
                width: 90%;
                background: white; 
                padding: 40px; 
                border-radius: 20px; 
                box-shadow: 0 20px 40px rgba(0,0,0,0.1);
            }}
            
            .header {{ 
                text-align: center; 
                margin-bottom: 40px; 
            }}
            
            .header h1 {{ 
                font-size: 2.5em; 
                margin-bottom: 10px; 
                background: linear-gradient(135deg, #667eea, #764ba2);
                -webkit-background-clip: text;
                -webkit-text-fill-color: transparent;
                background-clip: text;
            }}
            
            .status {{ 
                padding: 20px; 
                border-radius: 10px; 
                margin: 20px 0; 
                text-align: center;
                font-weight: 500;
            }}
            
            .status.configured {{ 
                background: #d4edda; 
                color: #155724; 
                border: 2px solid #c3e6cb; 
            }}
            
            .status.not-configured {{ 
                background: #f8d7da; 
                color: #721c24; 
                border: 2px solid #f5c6cb; 
            }}
            
            .settings-btn {{ 
                background: linear-gradient(135deg, #667eea, #764ba2);
                color: white; 
                border: none; 
                padding: 15px 30px; 
                border-radius: 10px; 
                cursor: pointer; 
                font-size: 16px;
                font-weight: 500;
                margin: 10px;
                transition: transform 0.2s;
            }}
            
            .settings-btn:hover {{ 
                transform: translateY(-2px);
                box-shadow: 0 5px 15px rgba(0,0,0,0.2);
            }}
            
            .modal {{ 
                display: none; 
                position: fixed; 
                z-index: 1000; 
                left: 0; 
                top: 0; 
                width: 100%; 
                height: 100%; 
                background-color: rgba(0,0,0,0.5); 
            }}
            
            .modal-content {{ 
                background-color: white; 
                margin: 5% auto; 
                padding: 30px; 
                border-radius: 15px; 
                width: 90%; 
                max-width: 600px;
                box-shadow: 0 20px 40px rgba(0,0,0,0.3);
            }}
            
            .close {{ 
                color: #aaa; 
                float: right; 
                font-size: 28px; 
                font-weight: bold; 
                cursor: pointer; 
            }}
            
            .close:hover {{ color: #000; }}
            
            .form-group {{ 
                margin-bottom: 20px; 
            }}
            
            .form-group label {{ 
                display: block; 
                margin-bottom: 8px; 
                font-weight: 500;
                color: #333;
            }}
            
            .form-group input, .form-group textarea {{ 
                width: 100%; 
                padding: 12px; 
                border: 2px solid #e1e5e9; 
                border-radius: 8px; 
                font-size: 14px;
                transition: border-color 0.3s;
            }}
            
            .form-group input:focus, .form-group textarea:focus {{ 
                outline: none; 
                border-color: #667eea; 
            }}
            
            .btn {{ 
                padding: 12px 24px; 
                border: none; 
                border-radius: 8px; 
                cursor: pointer; 
                font-size: 14px;
                font-weight: 500;
                margin-right: 10px;
                transition: all 0.3s;
            }}
            
            .btn-primary {{ 
                background: linear-gradient(135deg, #667eea, #764ba2);
                color: white; 
            }}
            
            .btn-secondary {{ 
                background: #6c757d; 
                color: white; 
            }}
            
            .btn:hover {{ 
                transform: translateY(-1px);
                box-shadow: 0 3px 10px rgba(0,0,0,0.2);
            }}
            
            .endpoint {{ 
                background: #f8f9fa; 
                padding: 20px; 
                margin: 15px 0; 
                border-radius: 10px; 
                border-left: 4px solid #667eea; 
            }}
            
            .endpoint-url {{ 
                font-family: 'Courier New', monospace; 
                background: #e9ecef; 
                padding: 10px; 
                border-radius: 5px; 
                margin: 10px 0;
                word-break: break-all;
            }}
            
            .copy-btn {{ 
                background: #28a745; 
                color: white; 
                border: none; 
                padding: 8px 16px; 
                border-radius: 5px; 
                cursor: pointer; 
                font-size: 12px;
                margin-left: 10px;
            }}
            
            .copy-btn:hover {{ background: #218838; }}
            
            .alert {{ 
                padding: 15px; 
                border-radius: 8px; 
                margin: 15px 0; 
                display: none;
            }}
            
            .alert-success {{ 
                background: #d4edda; 
                color: #155724; 
                border: 1px solid #c3e6cb; 
            }}
            
            .alert-error {{ 
                background: #f8d7da; 
                color: #721c24; 
                border: 1px solid #f5c6cb; 
            }}
            
            .loading {{ 
                display: none; 
                text-align: center; 
                margin: 20px 0; 
            }}
            
            .spinner {{ 
                border: 4px solid #f3f3f3; 
                border-top: 4px solid #667eea; 
                border-radius: 50%; 
                width: 40px; 
                height: 40px; 
                animation: spin 1s linear infinite; 
                margin: 0 auto;
            }}
            
            @keyframes spin {{ 
                0% {{ transform: rotate(0deg); }} 
                100% {{ transform: rotate(360deg); }} 
            }}
            
            .endpoints-section {{ 
                margin-top: 30px; 
            }}
            
            .usage-example {{ 
                background: #f8f9fa; 
                padding: 15px; 
                border-radius: 8px; 
                margin: 15px 0; 
            }}
            
            .usage-example pre {{ 
                background: #2d3748; 
                color: #e2e8f0; 
                padding: 15px; 
                border-radius: 5px; 
                overflow-x: auto; 
                margin: 10px 0;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>🚀 Codegen AI Proxy</h1>
                <p>Transparent API Gateway for OpenAI, Anthropic & Gemini → Codegen</p>
            </div>
            
            <div id="status" class="status">
                <span id="status-text">Loading...</span>
            </div>
            
            <div style="text-align: center; margin: 30px 0;">
                <button class="settings-btn" onclick="openSettings()">⚙️ Configure Codegen</button>
                <button class="settings-btn" onclick="testConnection()">🔍 Test Connection</button>
            </div>
            
            <div id="endpoints-section" class="endpoints-section" style="display: none;">
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
                
                <div class="usage-example">
                    <h4>💡 Usage Example:</h4>
                    <pre><code>import openai
openai.api_base = "http://localhost:8000/v1"
openai.api_key = "any-key"  # Proxy handles auth

# Your existing code works unchanged!
response = openai.ChatCompletion.create(
    model="gpt-3.5-turbo",
    messages=[{{"role": "user", "content": "Hello!"}}]
)</code></pre>
                </div>
            </div>
        </div>
        
        <!-- Settings Modal -->
        <div id="settingsModal" class="modal">
            <div class="modal-content">
                <span class="close" onclick="closeSettings()">&times;</span>
                <h2>⚙️ Codegen Configuration</h2>
                
                <div id="alert" class="alert"></div>
                
                <form id="configForm">
                    <div class="form-group">
                        <label for="orgId">Organization ID *</label>
                        <input type="text" id="orgId" name="orgId" placeholder="e.g., 323" required>
                        <small>Your Codegen organization ID</small>
                    </div>
                    
                    <div class="form-group">
                        <label for="token">API Token *</label>
                        <input type="password" id="token" name="token" placeholder="sk-..." required>
                        <small>Your Codegen API token</small>
                    </div>
                    
                    <div class="form-group">
                        <label for="baseUrl">Base URL</label>
                        <input type="url" id="baseUrl" name="baseUrl" value="https://api.codegen.com">
                        <small>Codegen API base URL (usually default is fine)</small>
                    </div>
                    
                    <div class="form-group">
                        <label for="systemMessage">System Message</label>
                        <textarea id="systemMessage" name="systemMessage" rows="3" placeholder="You are a helpful AI assistant."></textarea>
                        <small>Default system message for all requests</small>
                    </div>
                    
                    <div class="loading" id="loading">
                        <div class="spinner"></div>
                        <p>Verifying credentials...</p>
                    </div>
                    
                    <div style="margin-top: 30px;">
                        <button type="button" class="btn btn-primary" onclick="verifyAndSave()">🔍 Verify & Save</button>
                        <button type="button" class="btn btn-secondary" onclick="closeSettings()">Cancel</button>
                    </div>
                </form>
            </div>
        </div>
        
        <script>
            let currentConfig = {{}};
            
            // Load configuration on page load
            window.onload = function() {{
                loadConfig();
            }};
            
            async function loadConfig() {{
                try {{
                    const response = await fetch('/api/config');
                    const config = await response.json();
                    currentConfig = config;
                    
                    updateStatus(config);
                    
                    // Pre-fill form
                    document.getElementById('orgId').value = config.org_id || '';
                    document.getElementById('baseUrl').value = config.base_url || 'https://api.codegen.com';
                    document.getElementById('systemMessage').value = config.system_message || 'You are a helpful AI assistant.';
                    
                }} catch (error) {{
                    console.error('Failed to load config:', error);
                    updateStatus({{is_configured: false}});
                }}
            }}
            
            function updateStatus(config) {{
                const statusDiv = document.getElementById('status');
                const statusText = document.getElementById('status-text');
                const endpointsSection = document.getElementById('endpoints-section');
                
                if (config.is_configured) {{
                    statusDiv.className = 'status configured';
                    statusText.textContent = '✅ Codegen configured and ready! Proxy is intercepting API calls.';
                    endpointsSection.style.display = 'block';
                }} else {{
                    statusDiv.className = 'status not-configured';
                    statusText.textContent = '⚠️ Codegen not configured. Please configure your credentials to start using the proxy.';
                    endpointsSection.style.display = 'none';
                }}
            }}
            
            function openSettings() {{
                document.getElementById('settingsModal').style.display = 'block';
            }}
            
            function closeSettings() {{
                document.getElementById('settingsModal').style.display = 'none';
                hideAlert();
            }}
            
            function showAlert(message, type) {{
                const alert = document.getElementById('alert');
                alert.textContent = message;
                alert.className = `alert alert-${{type}}`;
                alert.style.display = 'block';
            }}
            
            function hideAlert() {{
                document.getElementById('alert').style.display = 'none';
            }}
            
            function showLoading(show) {{
                document.getElementById('loading').style.display = show ? 'block' : 'none';
            }}
            
            async function verifyAndSave() {{
                const formData = new FormData(document.getElementById('configForm'));
                const config = {{
                    org_id: formData.get('orgId'),
                    token: formData.get('token'),
                    base_url: formData.get('baseUrl'),
                    system_message: formData.get('systemMessage')
                }};
                
                if (!config.org_id || !config.token) {{
                    showAlert('Organization ID and Token are required!', 'error');
                    return;
                }}
                
                hideAlert();
                showLoading(true);
                
                try {{
                    // First verify credentials
                    const verifyResponse = await fetch('/api/config/verify', {{
                        method: 'POST',
                        headers: {{'Content-Type': 'application/json'}},
                        body: JSON.stringify(config)
                    }});
                    
                    const verifyResult = await verifyResponse.json();
                    
                    if (!verifyResult.success) {{
                        showAlert(`Verification failed: ${{verifyResult.error}}`, 'error');
                        showLoading(false);
                        return;
                    }}
                    
                    // If verification successful, save config
                    const saveResponse = await fetch('/api/config/save', {{
                        method: 'POST',
                        headers: {{'Content-Type': 'application/json'}},
                        body: JSON.stringify(config)
                    }});
                    
                    const saveResult = await saveResponse.json();
                    
                    if (saveResult.success) {{
                        showAlert('✅ Configuration verified and saved successfully!', 'success');
                        setTimeout(() => {{
                            closeSettings();
                            loadConfig(); // Reload to update status
                        }}, 2000);
                    }} else {{
                        showAlert(`Save failed: ${{saveResult.error}}`, 'error');
                    }}
                    
                }} catch (error) {{
                    showAlert(`Error: ${{error.message}}`, 'error');
                }} finally {{
                    showLoading(false);
                }}
            }}
            
            async function testConnection() {{
                try {{
                    const response = await fetch('/health');
                    const result = await response.json();
                    
                    if (result.status === 'healthy') {{
                        alert('✅ Proxy is healthy and running!');
                    }} else {{
                        alert('⚠️ Proxy responded but status is: ' + result.status);
                    }}
                }} catch (error) {{
                    alert('❌ Failed to connect to proxy: ' + error.message);
                }}
            }}
            
            function copyToClipboard(text) {{
                navigator.clipboard.writeText(text).then(function() {{
                    // Create a temporary notification
                    const notification = document.createElement('div');
                    notification.textContent = 'Copied to clipboard!';
                    notification.style.cssText = `
                        position: fixed;
                        top: 20px;
                        right: 20px;
                        background: #28a745;
                        color: white;
                        padding: 10px 20px;
                        border-radius: 5px;
                        z-index: 10000;
                        font-size: 14px;
                    `;
                    document.body.appendChild(notification);
                    
                    setTimeout(() => {{
                        document.body.removeChild(notification);
                    }}, 2000);
                }});
            }}
            
            // Close modal when clicking outside
            window.onclick = function(event) {{
                const modal = document.getElementById('settingsModal');
                if (event.target === modal) {{
                    closeSettings();
                }}
            }}
        </script>
    </body>
    </html>
    """
    return HTMLResponse(content=html_content)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
