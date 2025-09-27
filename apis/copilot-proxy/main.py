#!/usr/bin/env python3
"""
GitHub Copilot Proxy API - 14th Provider
OpenAI-compatible API wrapper for GitHub Copilot
"""

import http.server
import threading
import requests
import json
import time
import sys
import uuid
import logging
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import StreamingResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import uvicorn

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global token storage
token = None

class ChatMessage(BaseModel):
    role: str
    content: str

class ChatCompletionRequest(BaseModel):
    model: str = "copilot-codex"
    messages: List[ChatMessage]
    stream: bool = False
    temperature: Optional[float] = 0.0
    max_tokens: Optional[int] = 1000
    top_p: Optional[float] = 1.0
    stop: Optional[List[str]] = None
    user: Optional[str] = None

class ModelInfo(BaseModel):
    id: str
    object: str = "model"
    created: int = Field(default_factory=lambda: int(time.time()))
    owned_by: str = "github-copilot"

class ModelList(BaseModel):
    object: str = "list"
    data: List[ModelInfo]

class ChatCompletionChoice(BaseModel):
    message: ChatMessage
    index: int = 0
    finish_reason: str = "stop"

class ChatCompletionResponse(BaseModel):
    id: str = Field(default_factory=lambda: f"chatcmpl-{uuid.uuid4().hex}")
    object: str = "chat.completion"
    created: int = Field(default_factory=lambda: int(time.time()))
    model: str
    choices: List[ChatCompletionChoice]
    usage: Dict[str, int] = Field(default_factory=lambda: {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0})

class StreamChoice(BaseModel):
    delta: Dict[str, Any] = Field(default_factory=dict)
    index: int = 0
    finish_reason: Optional[str] = None

class StreamResponse(BaseModel):
    id: str = Field(default_factory=lambda: f"chatcmpl-{uuid.uuid4().hex}")
    object: str = "chat.completion.chunk"
    created: int = Field(default_factory=lambda: int(time.time()))
    model: str
    choices: List[StreamChoice]

app = FastAPI(
    title="GitHub Copilot Proxy API",
    description="OpenAI-compatible API for GitHub Copilot",
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

def setup_copilot_auth():
    """Setup GitHub Copilot authentication"""
    global token
    
    logger.info("Setting up GitHub Copilot authentication...")
    
    resp = requests.post('https://github.com/login/device/code', headers={
        'accept': 'application/json',
        'editor-version': 'Neovim/0.6.1',
        'editor-plugin-version': 'copilot.vim/1.16.0',
        'content-type': 'application/json',
        'user-agent': 'GithubCopilot/1.155.0',
        'accept-encoding': 'gzip,deflate,br'
    }, data='{"client_id":"Iv1.b507a08c87ecfe98","scope":"read:user"}')

    # Parse the response json
    resp_json = resp.json()
    device_code = resp_json.get('device_code')
    user_code = resp_json.get('user_code')
    verification_uri = resp_json.get('verification_uri')

    logger.info(f'Please visit {verification_uri} and enter code {user_code} to authenticate.')
    print(f'🔐 GitHub Copilot Authentication Required!')
    print(f'📱 Please visit: {verification_uri}')
    print(f'🔑 Enter code: {user_code}')

    while True:
        time.sleep(5)
        resp = requests.post('https://github.com/login/oauth/access_token', headers={
            'accept': 'application/json',
            'editor-version': 'Neovim/0.6.1',
            'editor-plugin-version': 'copilot.vim/1.16.0',
            'content-type': 'application/json',
            'user-agent': 'GithubCopilot/1.155.0',
            'accept-encoding': 'gzip,deflate,br'
        }, data=f'{{"client_id":"Iv1.b507a08c87ecfe98","device_code":"{device_code}","grant_type":"urn:ietf:params:oauth:grant-type:device_code"}}')

        resp_json = resp.json()
        access_token = resp_json.get('access_token')

        if access_token:
            break

    # Save the access token
    with open('.copilot_token', 'w') as f:
        f.write(access_token)

    logger.info('✅ GitHub Copilot authentication successful!')

def get_copilot_token():
    """Get GitHub Copilot session token"""
    global token
    
    # Check if token file exists
    try:
        with open('.copilot_token', 'r') as f:
            access_token = f.read().strip()
    except FileNotFoundError:
        setup_copilot_auth()
        with open('.copilot_token', 'r') as f:
            access_token = f.read().strip()

    # Get session token
    try:
        resp = requests.get('https://api.github.com/copilot_internal/v2/token', headers={
            'authorization': f'token {access_token}',
            'editor-version': 'Neovim/0.6.1',
            'editor-plugin-version': 'copilot.vim/1.16.0',
            'user-agent': 'GithubCopilot/1.155.0'
        })

        if resp.status_code == 200:
            resp_json = resp.json()
            token = resp_json.get('token')
            logger.info("✅ GitHub Copilot token refreshed")
        else:
            logger.error(f"❌ Failed to get Copilot token: {resp.status_code}")
            raise HTTPException(status_code=401, detail="Failed to authenticate with GitHub Copilot")
            
    except Exception as e:
        logger.error(f"❌ Error getting Copilot token: {e}")
        raise HTTPException(status_code=500, detail="Copilot authentication error")

def is_token_invalid(token):
    """Check if token is invalid"""
    if token is None:
        return True
    
    try:
        # Extract exp value from token
        pairs = token.split(';')
        for pair in pairs:
            if '=' in pair:
                key, value = pair.split('=', 1)
                if key.strip() == 'exp':
                    exp_time = int(value.strip())
                    return exp_time <= time.time()
    except:
        return True
    
    return False

def copilot_completion(prompt: str, language: str = 'python', max_tokens: int = 1000) -> str:
    """Get completion from GitHub Copilot"""
    global token
    
    # Check token validity
    if token is None or is_token_invalid(token):
        get_copilot_token()

    try:
        resp = requests.post('https://copilot-proxy.githubusercontent.com/v1/engines/copilot-codex/completions', 
            headers={'authorization': f'Bearer {token}'}, 
            json={
                'prompt': prompt,
                'suffix': '',
                'max_tokens': max_tokens,
                'temperature': 0,
                'top_p': 1,
                'n': 1,
                'stop': ['\n\n'],  # Stop on double newline for better responses
                'nwo': 'github/copilot.vim',
                'stream': True,
                'extra': {
                    'language': language
                }
            })
        
        if resp.status_code != 200:
            logger.error(f"❌ Copilot API error: {resp.status_code}")
            return f"Error: Copilot API returned {resp.status_code}"

        result = ''
        resp_text = resp.text.split('\n')
        
        for line in resp_text:
            if line.startswith('data: {'):
                try:
                    json_completion = json.loads(line[6:])
                    choices = json_completion.get('choices', [])
                    if choices:
                        completion = choices[0].get('text', '')
                        if completion:
                            result += completion
                except json.JSONDecodeError:
                    continue
        
        return result.strip()
        
    except requests.exceptions.ConnectionError:
        logger.error("❌ Connection error to Copilot API")
        return "Error: Connection failed to GitHub Copilot"
    except Exception as e:
        logger.error(f"❌ Copilot completion error: {e}")
        return f"Error: {str(e)}"

def token_refresh_thread():
    """Background thread to refresh token every 25 minutes"""
    global token
    while True:
        try:
            time.sleep(25 * 60)  # 25 minutes
            get_copilot_token()
        except Exception as e:
            logger.error(f"❌ Token refresh error: {e}")
            time.sleep(60)  # Wait 1 minute before retrying

@app.on_event("startup")
async def startup():
    """Initialize Copilot authentication on startup"""
    try:
        get_copilot_token()
        # Start token refresh thread
        threading.Thread(target=token_refresh_thread, daemon=True).start()
        logger.info("🚀 GitHub Copilot Proxy API started successfully")
    except Exception as e:
        logger.error(f"❌ Startup error: {e}")

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    global token
    is_healthy = token is not None and not is_token_invalid(token)
    return {
        "status": "healthy" if is_healthy else "unhealthy",
        "service": "github-copilot-proxy",
        "timestamp": int(time.time()),
        "token_valid": is_healthy
    }

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "GitHub Copilot Proxy API",
        "version": "1.0.0",
        "endpoints": {
            "health": "/health",
            "models": "/v1/models",
            "chat": "/v1/chat/completions"
        }
    }

@app.get("/v1/models", response_model=ModelList)
async def list_models():
    """List available models"""
    return ModelList(data=[
        ModelInfo(id="copilot-codex", owned_by="github-copilot"),
        ModelInfo(id="copilot-chat", owned_by="github-copilot"),
        ModelInfo(id="copilot-code", owned_by="github-copilot")
    ])

@app.post("/v1/chat/completions")
async def chat_completions(request: ChatCompletionRequest):
    """OpenAI-compatible chat completions endpoint"""
    
    if not request.messages:
        raise HTTPException(status_code=400, detail="Messages are required")

    # Convert messages to prompt
    prompt_parts = []
    for message in request.messages:
        if message.role == "system":
            prompt_parts.append(f"System: {message.content}")
        elif message.role == "user":
            prompt_parts.append(f"User: {message.content}")
        elif message.role == "assistant":
            prompt_parts.append(f"Assistant: {message.content}")
    
    # Add assistant prompt
    prompt = "\n".join(prompt_parts) + "\nAssistant:"
    
    # Detect language from context
    language = "python"  # Default
    content_lower = " ".join([msg.content.lower() for msg in request.messages])
    
    if any(keyword in content_lower for keyword in ["javascript", "js", "node", "react"]):
        language = "javascript"
    elif any(keyword in content_lower for keyword in ["java", "spring", "maven"]):
        language = "java"
    elif any(keyword in content_lower for keyword in ["go", "golang"]):
        language = "go"
    elif any(keyword in content_lower for keyword in ["rust", "cargo"]):
        language = "rust"
    elif any(keyword in content_lower for keyword in ["c++", "cpp", "cmake"]):
        language = "cpp"
    elif any(keyword in content_lower for keyword in ["html", "css", "web"]):
        language = "html"

    try:
        # Get completion from Copilot
        completion = copilot_completion(
            prompt, 
            language=language, 
            max_tokens=request.max_tokens or 1000
        )
        
        if not completion or completion.startswith("Error:"):
            raise HTTPException(status_code=500, detail=completion or "No response from Copilot")

        # Create response
        response = ChatCompletionResponse(
            model=request.model,
            choices=[ChatCompletionChoice(
                message=ChatMessage(role="assistant", content=completion),
                index=0,
                finish_reason="stop"
            )],
            usage={
                "prompt_tokens": len(prompt.split()),
                "completion_tokens": len(completion.split()),
                "total_tokens": len(prompt.split()) + len(completion.split())
            }
        )
        
        return response
        
    except Exception as e:
        logger.error(f"❌ Chat completion error: {e}")
        raise HTTPException(status_code=500, detail=f"Completion error: {str(e)}")

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="GitHub Copilot Proxy API")
    parser.add_argument("--port", type=int, default=8013, help="Port to run the server on")
    parser.add_argument("--host", type=str, default="0.0.0.0", help="Host to bind the server to")
    
    args = parser.parse_args()
    
    print(f"🚀 Starting GitHub Copilot Proxy API on {args.host}:{args.port}")
    print(f"📚 API Documentation: http://{args.host}:{args.port}/docs")
    print(f"🏥 Health Check: http://{args.host}:{args.port}/health")
    
    uvicorn.run(app, host=args.host, port=args.port)
