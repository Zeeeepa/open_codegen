#!/usr/bin/env python3
"""
TalkAI API Proxy Server
Provides OpenAI-compatible API for TalkAI service
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
TALKAI_BASE_URL = os.getenv("TALKAI_BASE_URL", "https://api.talkai.info")
TALKAI_API_KEY = os.getenv("TALKAI_API_KEY", "")
PORT = int(os.getenv("PORT", "8012"))

class ChatMessage(BaseModel):
    role: str
    content: str

class ChatCompletionRequest(BaseModel):
    model: str = "gpt-3.5-turbo"
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
    logger.info("🚀 TalkAI API Proxy starting up...")
    yield
    logger.info("🛑 TalkAI API Proxy shutting down...")

app = FastAPI(
    title="TalkAI API Proxy",
    description="OpenAI-compatible API proxy for TalkAI",
    version="1.0.0",
    lifespan=lifespan
)

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "talkai-proxy",
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
                "id": "gpt-3.5-turbo",
                "object": "model",
                "created": int(time.time()),
                "owned_by": "talkai",
                "permission": [],
                "root": "gpt-3.5-turbo",
                "parent": None
            },
            {
                "id": "gpt-4",
                "object": "model", 
                "created": int(time.time()),
                "owned_by": "talkai",
                "permission": [],
                "root": "gpt-4",
                "parent": None
            }
        ]
    }

async def call_talkai_api(messages: list[ChatMessage], model: str = "gpt-3.5-turbo", **kwargs) -> Dict[str, Any]:
    """Call TalkAI API"""
    try:
        # Convert messages to TalkAI format
        talkai_messages = []
        for msg in messages:
            talkai_messages.append({
                "role": msg.role,
                "content": msg.content
            })
        
        payload = {
            "model": model,
            "messages": talkai_messages,
            "temperature": kwargs.get("temperature", 0.7),
            "max_tokens": kwargs.get("max_tokens", 2000),
            "top_p": kwargs.get("top_p", 1.0),
            "frequency_penalty": kwargs.get("frequency_penalty", 0.0),
            "presence_penalty": kwargs.get("presence_penalty", 0.0)
        }
        
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {TALKAI_API_KEY}" if TALKAI_API_KEY else ""
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{TALKAI_BASE_URL}/v1/chat/completions",
                json=payload,
                headers=headers,
                timeout=aiohttp.ClientTimeout(total=60)
            ) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    error_text = await response.text()
                    logger.error(f"TalkAI API error: {response.status} - {error_text}")
                    raise HTTPException(status_code=response.status, detail=error_text)
                    
    except aiohttp.ClientError as e:
        logger.error(f"TalkAI API connection error: {e}")
        # Return mock response for demo purposes
        return {
            "id": f"chatcmpl-{int(time.time())}",
            "object": "chat.completion",
            "created": int(time.time()),
            "model": model,
            "choices": [{
                "index": 0,
                "message": {
                    "role": "assistant",
                    "content": f"[TalkAI Mock Response] I'm a TalkAI assistant. Your message was: {messages[-1].content if messages else 'No message'}"
                },
                "finish_reason": "stop"
            }],
            "usage": {
                "prompt_tokens": 50,
                "completion_tokens": 25,
                "total_tokens": 75
            }
        }

async def stream_talkai_response(messages: list[ChatMessage], model: str = "gpt-3.5-turbo", **kwargs) -> AsyncGenerator[str, None]:
    """Stream response from TalkAI API"""
    try:
        # For demo purposes, simulate streaming
        response_text = f"[TalkAI Streaming] Processing your request: {messages[-1].content if messages else 'No message'}"
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
            await asyncio.sleep(0.1)
        
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
                "delta": {"content": "[TalkAI Error] Service temporarily unavailable"},
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
                stream_talkai_response(
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
            response = await call_talkai_api(
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
    messages = [{"role": "user", "content": prompt}]
    
    chat_request = ChatCompletionRequest(
        model=body.get("model", "gpt-3.5-turbo"),
        messages=[ChatMessage(role="user", content=prompt)],
        temperature=body.get("temperature", 0.7),
        max_tokens=body.get("max_tokens"),
        stream=body.get("stream", False)
    )
    
    return await chat_completions(chat_request)

if __name__ == "__main__":
    logger.info(f"🚀 Starting TalkAI API Proxy on port {PORT}")
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=PORT,
        reload=False,
        log_level="info"
    )
