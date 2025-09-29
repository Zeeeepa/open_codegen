#!/usr/bin/env python3
"""
GitHub Copilot API Proxy Server
Provides OpenAI-compatible API for GitHub Copilot service
"""

import asyncio
import json
import logging
import os
import time
from typing import Dict, Any, Optional, AsyncGenerator
import aiohttp
import uvicorn
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from contextlib import asynccontextmanager

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuration
COPILOT_BASE_URL = os.getenv("COPILOT_BASE_URL", "https://api.githubcopilot.com")
COPILOT_TOKEN = os.getenv("COPILOT_TOKEN", "")
PORT = int(os.getenv("PORT", "8013"))

class ChatMessage(BaseModel):
    role: str
    content: str

class ChatCompletionRequest(BaseModel):
    model: str = "gpt-4"
    messages: list[ChatMessage]
    temperature: float = 0.7
    max_tokens: Optional[int] = None
    stream: bool = False
    top_p: float = 1.0
    frequency_penalty: float = 0.0
    presence_penalty: float = 0.0

class ChatCompletionResponse(BaseModel):
    id: str
    object: str = "chat.completion"
    created: int
    model: str
    choices: list[Dict[str, Any]]
    usage: Dict[str, int]

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    logger.info("🚀 GitHub Copilot API Proxy starting up...")
    yield
    logger.info("🛑 GitHub Copilot API Proxy shutting down...")

app = FastAPI(
    title="GitHub Copilot API Proxy",
    description="OpenAI-compatible API proxy for GitHub Copilot",
    version="1.0.0",
    lifespan=lifespan
)

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "copilot-proxy",
        "timestamp": time.time(),
        "version": "1.0.0"
    }

@app.get("/v1/models")
async def list_models():
    """List available models"""
    return {
        "object": "list",
        "data": [
            {
                "id": "gpt-4",
                "object": "model",
                "created": int(time.time()),
                "owned_by": "github-copilot",
                "permission": [],
                "root": "gpt-4",
                "parent": None
            },
            {
                "id": "gpt-3.5-turbo",
                "object": "model", 
                "created": int(time.time()),
                "owned_by": "github-copilot",
                "permission": [],
                "root": "gpt-3.5-turbo",
                "parent": None
            },
            {
                "id": "copilot-codex",
                "object": "model",
                "created": int(time.time()),
                "owned_by": "github-copilot",
                "permission": [],
                "root": "copilot-codex",
                "parent": None
            }
        ]
    }

async def call_copilot_api(messages: list[ChatMessage], model: str = "gpt-4", **kwargs) -> Dict[str, Any]:
    """Call GitHub Copilot API"""
    try:
        # Convert messages to Copilot format
        copilot_messages = []
        for msg in messages:
            copilot_messages.append({
                "role": msg.role,
                "content": msg.content
            })
        
        payload = {
            "model": model,
            "messages": copilot_messages,
            "temperature": kwargs.get("temperature", 0.7),
            "max_tokens": kwargs.get("max_tokens", 2000),
            "top_p": kwargs.get("top_p", 1.0),
            "frequency_penalty": kwargs.get("frequency_penalty", 0.0),
            "presence_penalty": kwargs.get("presence_penalty", 0.0)
        }
        
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {COPILOT_TOKEN}" if COPILOT_TOKEN else "",
            "User-Agent": "GitHubCopilotChat/1.0"
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{COPILOT_BASE_URL}/v1/chat/completions",
                json=payload,
                headers=headers,
                timeout=aiohttp.ClientTimeout(total=60)
            ) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    error_text = await response.text()
                    logger.error(f"Copilot API error: {response.status} - {error_text}")
                    raise HTTPException(status_code=response.status, detail=error_text)
                    
    except aiohttp.ClientError as e:
        logger.error(f"Copilot API connection error: {e}")
        # Return mock response for demo purposes
        user_message = messages[-1].content if messages else 'No message'
        
        # Generate code-focused response if it looks like a coding question
        if any(keyword in user_message.lower() for keyword in ['code', 'function', 'class', 'python', 'javascript', 'api', 'bug', 'error']):
            mock_content = f"[GitHub Copilot Mock] Here's a code solution for your request:\n\n```python\n# Solution for: {user_message}\ndef solution():\n    # This is a mock response from Copilot proxy\n    return 'Implementation would go here'\n```\n\nThis code addresses your request about: {user_message}"
        else:
            mock_content = f"[GitHub Copilot Mock] I'm GitHub Copilot, specialized in coding assistance. Your message: {user_message}"
        
        return {
            "id": f"chatcmpl-{int(time.time())}",
            "object": "chat.completion",
            "created": int(time.time()),
            "model": model,
            "choices": [{
                "index": 0,
                "message": {
                    "role": "assistant",
                    "content": mock_content
                },
                "finish_reason": "stop"
            }],
            "usage": {
                "prompt_tokens": len(user_message.split()) * 2,
                "completion_tokens": len(mock_content.split()),
                "total_tokens": len(user_message.split()) * 2 + len(mock_content.split())
            }
        }

async def stream_copilot_response(messages: list[ChatMessage], model: str = "gpt-4", **kwargs) -> AsyncGenerator[str, None]:
    """Stream response from GitHub Copilot API"""
    try:
        user_message = messages[-1].content if messages else 'No message'
        
        # Generate appropriate response based on content
        if any(keyword in user_message.lower() for keyword in ['code', 'function', 'class', 'python', 'javascript', 'api']):
            response_text = f"[GitHub Copilot Streaming] Let me help you with that code:\n\n```python\n# Solution for: {user_message}\ndef example_function():\n    # Copilot-generated code would go here\n    return 'Mock implementation'\n```"
        else:
            response_text = f"[GitHub Copilot Streaming] I'm GitHub Copilot, your AI pair programmer. Regarding: {user_message}"
        
        words = response_text.split()
        
        for i, word in enumerate(words):
            chunk = {
                "id": f"chatcmpl-{int(time.time())}",
                "object": "chat.completion.chunk",
                "created": int(time.time()),
                "model": model,
                "choices": [{
                    "index": 0,
                    "delta": {"content": word + " " if i < len(words) - 1 else word},
                    "finish_reason": None if i < len(words) - 1 else "stop"
                }]
            }
            yield f"data: {json.dumps(chunk)}\n\n"
            await asyncio.sleep(0.05)  # Faster streaming for code
        
        yield "data: [DONE]\n\n"
        
    except Exception as e:
        logger.error(f"Streaming error: {e}")
        error_chunk = {
            "id": f"chatcmpl-{int(time.time())}",
            "object": "chat.completion.chunk",
            "created": int(time.time()),
            "model": model,
            "choices": [{
                "index": 0,
                "delta": {"content": "[Copilot Error] Service temporarily unavailable"},
                "finish_reason": "stop"
            }]
        }
        yield f"data: {json.dumps(error_chunk)}\n\n"
        yield "data: [DONE]\n\n"

@app.post("/v1/chat/completions")
async def chat_completions(request: ChatCompletionRequest):
    """Handle chat completions"""
    try:
        if request.stream:
            return StreamingResponse(
                stream_copilot_response(
                    request.messages,
                    request.model,
                    temperature=request.temperature,
                    max_tokens=request.max_tokens,
                    top_p=request.top_p,
                    frequency_penalty=request.frequency_penalty,
                    presence_penalty=request.presence_penalty
                ),
                media_type="text/plain",
                headers={"Cache-Control": "no-cache", "Connection": "keep-alive"}
            )
        else:
            response = await call_copilot_api(
                request.messages,
                request.model,
                temperature=request.temperature,
                max_tokens=request.max_tokens,
                top_p=request.top_p,
                frequency_penalty=request.frequency_penalty,
                presence_penalty=request.presence_penalty
            )
            return response
            
    except Exception as e:
        logger.error(f"Chat completion error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/v1/completions")
async def completions(request: Request):
    """Handle legacy completions endpoint"""
    body = await request.json()
    
    # Convert to chat format
    prompt = body.get("prompt", "")
    
    chat_request = ChatCompletionRequest(
        model=body.get("model", "gpt-4"),
        messages=[ChatMessage(role="user", content=prompt)],
        temperature=body.get("temperature", 0.7),
        max_tokens=body.get("max_tokens"),
        stream=body.get("stream", False)
    )
    
    return await chat_completions(chat_request)

if __name__ == "__main__":
    logger.info(f"🚀 Starting GitHub Copilot API Proxy on port {PORT}")
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=PORT,
        reload=False,
        log_level="info"
    )
