"""
FastAPI server providing OpenAI-compatible API endpoints.
"""

import logging
import traceback
import time
import json
from typing import Dict, Any, Optional
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse
import asyncio

from .models import (
    ChatRequest, TextRequest, ChatResponse, TextResponse,
    ErrorResponse, ErrorDetail, AnthropicRequest, AnthropicResponse,
    GeminiRequest, GeminiResponse
)
from .config import get_codegen_config, get_server_config
from .codegen_client import CodegenClient
from .request_transformer import (
    chat_request_to_prompt, text_request_to_prompt,
    extract_generation_params, extract_user_message,
    anthropic_request_to_prompt, extract_anthropic_generation_params,
    gemini_request_to_prompt
)
from .response_transformer import (
    create_chat_response, create_text_response,
    create_chat_stream_chunk, format_sse_chunk, format_sse_done,
    estimate_tokens, clean_content,
    create_anthropic_response, create_gemini_response
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize configurations
codegen_config = get_codegen_config()
server_config = get_server_config()

# Initialize Codegen client
codegen_client = CodegenClient(codegen_config)

# Create FastAPI app
app = FastAPI(
    title="OpenAI Codegen Adapter",
    description="OpenAI-compatible API server that forwards requests to Codegen SDK",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=server_config.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler to return OpenAI-compatible errors."""
    logger.error(f"Unhandled exception: {exc}\n{traceback.format_exc()}")
    
    error_response = ErrorResponse(
        error=ErrorDetail(
            message=str(exc),
            type="server_error",
            code="500"
        )
    )
    return JSONResponse(
        status_code=500,
        content=error_response.dict()
    )


@app.get("/")
async def root():
    """Root endpoint for health check."""
    return {
        "message": "OpenAI Codegen Adapter",
        "version": "1.0.0",
        "status": "running"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "timestamp": time.time(),
        "providers": ["openai", "anthropic", "google"],
        "routing_to": "Codegen SDK"
    }


@app.get("/v1/models")
async def list_models():
    """List available models (OpenAI compatibility)."""
    return {
        "object": "list",
        "data": [
            {
                "id": "gpt-3.5-turbo",
                "object": "model",
                "created": 1677610602,
                "owned_by": "codegen"
            },
            {
                "id": "gpt-4",
                "object": "model", 
                "created": 1677610602,
                "owned_by": "codegen"
            },
            {
                "id": "claude-3-sonnet-20240229",
                "object": "model",
                "created": 1677610602,
                "owned_by": "anthropic"
            },
            {
                "id": "gemini-1.5-pro",
                "object": "model",
                "created": 1677610602,
                "owned_by": "google"
            }
        ]
    }


async def stream_chat_response(prompt: str, model: str, request_id: str):
    """Stream chat completion response as Server-Sent Events."""
    try:
        # Send initial empty chunk to start the stream
        initial_chunk = create_chat_stream_chunk("", model, request_id=request_id)
        yield format_sse_chunk(initial_chunk)
        
        # Stream the actual response
        accumulated_content = ""
        async for content_chunk in codegen_client.run_task(prompt, stream=True):
            if content_chunk:
                cleaned_chunk = clean_content(content_chunk)
                if cleaned_chunk:
                    # For streaming, we send the incremental content
                    chunk = create_chat_stream_chunk(
                        cleaned_chunk, 
                        model, 
                        request_id=request_id
                    )
                    yield format_sse_chunk(chunk)
                    accumulated_content += cleaned_chunk
                    
                    # Small delay to prevent overwhelming the client
                    await asyncio.sleep(0.01)
        
        # Send final chunk with finish_reason
        final_chunk = create_chat_stream_chunk(
            "", 
            model, 
            finish_reason="stop",
            request_id=request_id
        )
        yield format_sse_chunk(final_chunk)
        
        # Send completion marker
        yield format_sse_done()
        
    except Exception as e:
        logger.error(f"Error in streaming response: {e}")
        # Send error chunk
        error_chunk = create_chat_stream_chunk(
            f"Error: {str(e)}", 
            model, 
            finish_reason="error",
            request_id=request_id
        )
        yield format_sse_chunk(error_chunk)
        yield format_sse_done()


async def collect_streaming_response(prompt: str) -> str:
    """Collect a complete response from streaming for non-streaming requests."""
    content_parts = []
    
    async for content_chunk in codegen_client.run_task(prompt, stream=False):
        if content_chunk:
            content_parts.append(content_chunk)
    
    return "".join(content_parts)


@app.post("/v1/chat/completions")
async def chat_completions(request: ChatRequest):
    """
    Create a chat completion using Codegen SDK.
    Compatible with OpenAI's /v1/chat/completions endpoint.
    """
    try:
        logger.info(f"Routing OpenAI request to Codegen SDK: {request.dict()}")
        
        # Convert request to prompt
        prompt = chat_request_to_prompt(request)
        
        if request.stream:
            # Return streaming response
            return StreamingResponse(
                stream_chat_response(
                    prompt, 
                    request.model, 
                    f"chatcmpl-{int(time.time())}"
                ),
                media_type="text/event-stream"
            )
        else:
            # Return complete response
            content = await collect_streaming_response(prompt)
            
            # Estimate token counts
            prompt_tokens = estimate_tokens(prompt)
            completion_tokens = estimate_tokens(content)
            
            response = create_chat_response(
                content=content,
                model=request.model,
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens
            )
            
            return response
            
    except Exception as e:
        logger.error(f"OpenAI chat completion error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/v1/completions")
async def completions(request: TextRequest):
    """
    Create a text completion using Codegen SDK.
    Compatible with OpenAI's /v1/completions endpoint.
    """
    try:
        logger.info(f"Routing OpenAI text completion request to Codegen SDK: {request.dict()}")
        
        # Convert request to prompt
        prompt = text_request_to_prompt(request)
        
        # Get complete response
        content = await collect_streaming_response(prompt)
        
        # Estimate token counts
        prompt_tokens = estimate_tokens(prompt)
        completion_tokens = estimate_tokens(content)
        
        response = create_text_response(
            content=content,
            model=request.model,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens
        )
        
        return response
        
    except Exception as e:
        logger.error(f"OpenAI text completion error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/v1/anthropic/completions")
async def anthropic_completions(request: AnthropicRequest):
    """
    Create a completion using Anthropic Claude API.
    Compatible with Anthropic's API.
    """
    try:
        logger.info(f"Routing Anthropic request to Codegen SDK: {request.dict()}")
        
        # Convert request to prompt
        prompt = anthropic_request_to_prompt(request)
        
        # Get complete response
        content = await collect_streaming_response(prompt)
        
        # Estimate token counts
        input_tokens = estimate_tokens(prompt)
        output_tokens = estimate_tokens(content)
        
        response = create_anthropic_response(
            content=content,
            model=request.model,
            input_tokens=input_tokens,
            output_tokens=output_tokens
        )
        
        return response
        
    except Exception as e:
        logger.error(f"Anthropic completion error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/v1/gemini/completions")
async def gemini_completions(request: GeminiRequest):
    """
    Create a completion using Google Gemini API.
    Compatible with Google's API.
    """
    try:
        # Parse request body if it's a raw request
        if isinstance(request, Request):
            body = await request.json()
            # Extract message from different possible formats
            user_message = extract_user_message(body)
        else:
            # Extract from Pydantic model
            user_message = gemini_request_to_prompt(request)
        
        if not user_message:
            raise HTTPException(status_code=400, detail="No user message found")
        
        logger.info(f"Routing Google request to Codegen SDK: {user_message}")
        
        # Get complete response
        content = await collect_streaming_response(user_message)
        
        # Estimate token counts
        prompt_tokens = estimate_tokens(user_message)
        completion_tokens = estimate_tokens(content)
        
        response = create_gemini_response(
            content=content,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens
        )
        
        return response
        
    except Exception as e:
        logger.error(f"Gemini completion error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

