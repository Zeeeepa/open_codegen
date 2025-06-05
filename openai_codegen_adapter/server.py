"""
FastAPI server providing OpenAI-compatible API endpoints.
Based on h2ogpt's server.py structure and patterns.
Enhanced with comprehensive logging for completion tracking and OpenAI response generation.
Enhanced with Anthropic Claude API compatibility.
"""

import logging
import traceback
import time
from datetime import datetime
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn

from .models import (
    ChatRequest, TextRequest, ChatResponse, TextResponse,
    ErrorResponse, ErrorDetail, AnthropicRequest, AnthropicResponse,
    GeminiRequest, GeminiResponse
)
from .config import get_codegen_config, get_server_config
from .codegen_client import CodegenClient
from .request_transformer import (
    chat_request_to_prompt, text_request_to_prompt,
    extract_generation_params
)
from .response_transformer import (
    create_chat_response, create_text_response,
    estimate_tokens, clean_content
)
from .streaming import create_streaming_response, collect_streaming_response
from .anthropic_transformer import (
    anthropic_request_to_prompt, create_anthropic_response,
    extract_anthropic_generation_params
)
from .anthropic_streaming import (
    create_anthropic_streaming_response, collect_anthropic_streaming_response
)
from .gemini_transformer import (
    gemini_request_to_prompt, create_gemini_response,
    extract_gemini_generation_params
)
from .gemini_streaming import (
    create_gemini_streaming_response, collect_gemini_streaming_response
)

# Enhanced logging configuration
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(name)s | %(levelname)s | %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
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

def log_request_start(endpoint: str, request_data: dict):
    """Log the start of a request with enhanced details."""
    logger.info(f"🚀 REQUEST START | Endpoint: {endpoint}")
    logger.info(f"   📊 Request Data: {request_data}")
    logger.info(f"   🕐 Timestamp: {datetime.now().isoformat()}")

def log_completion_tracking(task_id: str, status: str, attempt: int, duration: float):
    """Log completion checking process with detailed tracking."""
    logger.info(f"🔍 COMPLETION CHECK | Task: {task_id} | Status: {status} | Attempt: {attempt} | Duration: {duration:.2f}s")

def log_openai_response_generation(response_data: dict, processing_time: float):
    """Log OpenAI API compatible response generation."""
    logger.info(f"📤 OPENAI RESPONSE GENERATED | Processing Time: {processing_time:.2f}s")
    logger.info(f"   🆔 Response ID: {response_data.get('id', 'N/A')}")
    logger.info(f"   ���������� Model: {response_data.get('model', 'N/A')}")
    logger.info(f"   📝 Choices: {len(response_data.get('choices', []))}")
    
    if 'usage' in response_data:
        usage = response_data['usage']
        logger.info(f"   🔢 Token Usage - Prompt: {usage.get('prompt_tokens', 0)}, "
                   f"Completion: {usage.get('completion_tokens', 0)}, "
                   f"Total: {usage.get('total_tokens', 0)}")
    
    # Log first 100 chars of response content
    if response_data.get('choices') and len(response_data['choices']) > 0:
        choice = response_data['choices'][0]
        if 'message' in choice and 'content' in choice['message']:
            content = choice['message']['content']
            logger.info(f"   📄 Content Preview: {content[:100]}...")

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


@app.get("/v1/models")
async def list_models():
    """List available models (OpenAI and Anthropic compatibility)."""
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
                "id": "gpt-3.5-turbo-instruct",
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
                "id": "claude-3-haiku-20240307",
                "object": "model",
                "created": 1677610602,
                "owned_by": "anthropic"
            },
            {
                "id": "claude-3-opus-20240229",
                "object": "model",
                "created": 1677610602,
                "owned_by": "anthropic"
            },
            {
                "id": "gemini-1.5-pro",
                "object": "model",
                "created": 1677610602,
                "owned_by": "google"
            },
            {
                "id": "gemini-1.5-flash",
                "object": "model",
                "created": 1677610602,
                "owned_by": "google"
            },
            {
                "id": "gemini-pro",
                "object": "model",
                "created": 1677610602,
                "owned_by": "google"
            }
        ]
    }


@app.post("/v1/chat/completions")
async def chat_completions(request: ChatRequest):
    """
    Create a chat completion using Codegen SDK.
    Compatible with OpenAI's /v1/chat/completions endpoint.
    """
    start_time = time.time()
    
    try:
        log_request_start("/v1/chat/completions", request.dict())
        
        # Convert request to prompt
        prompt = chat_request_to_prompt(request)
        logger.debug(f"🔄 Converted prompt: {prompt[:200]}...")
        
        # Extract generation parameters (for future use)
        gen_params = extract_generation_params(request)
        logger.debug(f"⚙️ Generation parameters: {gen_params}")
        
        if request.stream:
            # Return streaming response
            logger.info("🌊 Initiating streaming response...")
            return create_streaming_response(
                codegen_client,
                prompt,
                request.model,
                f"chatcmpl-{hash(prompt) % 1000000}"
            )
        else:
            # Return complete response
            logger.info("📦 Initiating non-streaming response...")
            content = await collect_streaming_response(codegen_client, prompt)
            
            # Estimate token counts
            prompt_tokens = estimate_tokens(prompt)
            completion_tokens = estimate_tokens(content)
            
            logger.info(f"🔢 Token estimation - Prompt: {prompt_tokens}, Completion: {completion_tokens}")
            
            response = create_chat_response(
                content=content,
                model=request.model,
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens
            )
            
            # Log the OpenAI response generation
            processing_time = time.time() - start_time
            log_openai_response_generation(response.dict(), processing_time)
            
            logger.info(f"✅ Chat completion successful in {processing_time:.2f}s")
            return response
            
    except Exception as e:
        processing_time = time.time() - start_time
        logger.error(f"❌ Error in chat completion after {processing_time:.2f}s: {e}")
        logger.error(f"🔍 Traceback: {traceback.format_exc()}")
        raise HTTPException(
            status_code=500,
            detail={
                "error": {
                    "message": str(e),
                    "type": "server_error",
                    "code": "500"
                }
            }
        )


@app.post("/v1/completions")
async def completions(request: TextRequest):
    """
    Create a text completion using Codegen SDK.
    Compatible with OpenAI's /v1/completions endpoint.
    """
    try:
        log_request_start("/v1/completions", request.dict())
        
        # Convert request to prompt
        prompt = text_request_to_prompt(request)
        logger.debug(f"Converted prompt: {prompt[:200]}...")
        
        # Extract generation parameters (for future use)
        gen_params = extract_generation_params(request)
        logger.debug(f"Generation parameters: {gen_params}")
        
        if request.stream:
            # For text completions streaming, we'd need a different streaming format
            # For now, fall back to non-streaming
            logger.warning("Streaming not yet implemented for text completions, falling back to non-streaming")
        
        # Get complete response
        content = await collect_streaming_response(codegen_client, prompt)
        
        # Estimate token counts
        prompt_tokens = estimate_tokens(prompt)
        completion_tokens = estimate_tokens(content)
        
        response = create_text_response(
            content=content,
            model=request.model,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens
        )
        
        logger.info(f"Text completion response: {completion_tokens} tokens")
        return response
        
    except Exception as e:
        logger.error(f"Error in text completion: {e}\n{traceback.format_exc()}")
        raise HTTPException(
            status_code=500,
            detail={
                "error": {
                    "message": str(e),
                    "type": "server_error",
                    "code": "500"
                }
            }
        )


@app.post("/v1/anthropic/completions")
async def anthropic_completions(request: AnthropicRequest):
    """
    Create a text completion using Anthropic Claude API.
    Compatible with Anthropic's /v1/anthropic/completions endpoint.
    """
    try:
        log_request_start("/v1/anthropic/completions", request.dict())
        
        # Convert request to prompt
        prompt = anthropic_request_to_prompt(request)
        logger.debug(f"Converted prompt: {prompt[:200]}...")
        
        # Extract generation parameters (for future use)
        gen_params = extract_anthropic_generation_params(request)
        logger.debug(f"Generation parameters: {gen_params}")
        
        if request.stream:
            # For text completions streaming, we'd need a different streaming format
            # For now, fall back to non-streaming
            logger.warning("Streaming not yet implemented for text completions, falling back to non-streaming")
        
        # Get complete response
        content = await collect_anthropic_streaming_response(codegen_client, prompt)
        
        # Estimate token counts
        prompt_tokens = estimate_tokens(prompt)
        completion_tokens = estimate_tokens(content)
        
        response = create_anthropic_response(
            content=content,
            model=request.model,
            input_tokens=prompt_tokens,
            output_tokens=completion_tokens
        )
        
        logger.info(f"Anthropic completion response: {completion_tokens} tokens")
        return response
        
    except Exception as e:
        logger.error(f"Error in text completion: {e}\n{traceback.format_exc()}")
        raise HTTPException(
            status_code=500,
            detail={
                "error": {
                    "message": str(e),
                    "type": "server_error",
                    "code": "500"
                }
            }
        )


@app.post("/v1/messages")
async def anthropic_messages(request: AnthropicRequest):
    """
    Create a message using Anthropic Claude API.
    Compatible with Anthropic's /v1/messages endpoint.
    """
    start_time = time.time()
    
    try:
        log_request_start("/v1/messages", request.dict())
        
        # Convert request to prompt
        prompt = anthropic_request_to_prompt(request)
        logger.debug(f"🔄 Converted prompt: {prompt[:200]}...")
        
        # Extract generation parameters (for future use)
        gen_params = extract_anthropic_generation_params(request)
        logger.debug(f"⚙️ Generation parameters: {gen_params}")
        
        if request.stream:
            # Return streaming response
            logger.info("🌊 Initiating Anthropic streaming response...")
            return create_anthropic_streaming_response(
                codegen_client,
                prompt,
                request.model,
                f"msg_{hash(prompt) % 1000000}"
            )
        else:
            # Return complete response
            logger.info("📦 Initiating Anthropic non-streaming response...")
            content = await collect_anthropic_streaming_response(codegen_client, prompt)
            
            # Estimate token counts
            input_tokens = estimate_tokens(prompt)
            output_tokens = estimate_tokens(content)
            
            logger.info(f"🔢 Token estimation - Input: {input_tokens}, Output: {output_tokens}")
            
            response = create_anthropic_response(
                content=content,
                model=request.model,
                input_tokens=input_tokens,
                output_tokens=output_tokens
            )
            
            # Log the Anthropic response generation
            processing_time = time.time() - start_time
            logger.info(f"📤 Anthropic response generated in {processing_time:.2f}s")
            
            logger.info(f"✅ Anthropic message completion successful in {processing_time:.2f}s")
            return response
            
    except Exception as e:
        processing_time = time.time() - start_time
        logger.error(f"❌ Error in Anthropic message completion after {processing_time:.2f}s: {e}")
        logger.error(f"🔍 Traceback: {traceback.format_exc()}")
        raise HTTPException(
            status_code=500,
            detail={
                "error": {
                    "message": str(e),
                    "type": "server_error",
                    "code": "500"
                }
            }
        )


@app.post("/v1/gemini/completions")
async def gemini_completions(request: GeminiRequest):
    """
    Create a text completion using Gemini API.
    Compatible with Gemini's /v1/gemini/completions endpoint.
    """
    try:
        log_request_start("/v1/gemini/completions", request.dict())
        
        # Convert request to prompt
        prompt = gemini_request_to_prompt(request)
        logger.debug(f"Converted prompt: {prompt[:200]}...")
        
        # Extract generation parameters (for future use)
        gen_params = extract_gemini_generation_params(request)
        logger.debug(f"Generation parameters: {gen_params}")
        
        if request.stream:
            # For text completions streaming, we'd need a different streaming format
            # For now, fall back to non-streaming
            logger.warning("Streaming not yet implemented for text completions, falling back to non-streaming")
        
        # Get complete response
        content = await collect_gemini_streaming_response(codegen_client, prompt)
        
        # Estimate token counts
        prompt_tokens = estimate_tokens(prompt)
        completion_tokens = estimate_tokens(content)
        
        response = create_gemini_response(
            content=content,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens
        )
        
        logger.info(f"Gemini completion response: {completion_tokens} tokens")
        return response
        
    except Exception as e:
        logger.error(f"Error in text completion: {e}\n{traceback.format_exc()}")
        raise HTTPException(
            status_code=500,
            detail={
                "error": {
                    "message": str(e),
                    "type": "server_error",
                    "code": "500"
                }
            }
        )


@app.post("/v1/gemini/generateContent")
async def gemini_generate_content(request: GeminiRequest):
    """
    Generate content using Gemini API.
    Compatible with Gemini's /v1/generateContent endpoint.
    """
    start_time = time.time()
    
    try:
        log_request_start("/v1/gemini/generateContent", request.dict())
        
        # Convert request to prompt
        prompt = gemini_request_to_prompt(request)
        logger.debug(f"🔄 Converted prompt: {prompt[:200]}...")
        
        # Extract generation parameters (for future use)
        gen_params = extract_gemini_generation_params(request)
        logger.debug(f"⚙️ Generation parameters: {gen_params}")
        
        # Check if streaming is requested
        is_streaming = gen_params.get("stream", False)
        
        if is_streaming:
            # Return streaming response
            logger.info("🌊 Initiating Gemini streaming response...")
            return create_gemini_streaming_response(codegen_client, prompt)
        else:
            # Return complete response
            logger.info("📦 Initiating Gemini non-streaming response...")
            content = await collect_gemini_streaming_response(codegen_client, prompt)
            
            # Estimate token counts
            prompt_tokens = estimate_tokens(prompt)
            completion_tokens = estimate_tokens(content)
            
            logger.info(f"🔢 Token estimation - Input: {prompt_tokens}, Output: {completion_tokens}")
            
            response = create_gemini_response(
                content=content,
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens
            )
            
            # Log the Gemini response generation
            processing_time = time.time() - start_time
            logger.info(f"📤 Gemini response generated in {processing_time:.2f}s")
            
            logger.info(f"✅ Gemini content generation successful in {processing_time:.2f}s")
            return response
            
    except Exception as e:
        processing_time = time.time() - start_time
        logger.error(f"❌ Error in Gemini content generation after {processing_time:.2f}s: {e}")
        logger.error(f"🔍 Traceback: {traceback.format_exc()}")
        raise HTTPException(
            status_code=500,
            detail={
                "error": {
                    "code": 500,
                    "message": str(e),
                    "status": "INTERNAL"
                }
            }
        )


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    try:
        # Test Codegen client
        if codegen_client.agent:
            return {"status": "healthy", "codegen": "connected"}
        else:
            return {"status": "unhealthy", "codegen": "disconnected"}
    except Exception as e:
        return {"status": "unhealthy", "error": str(e)}


if __name__ == "__main__":
    uvicorn.run(
        "openai_codegen_adapter.server:app",
        host=server_config.host,
        port=server_config.port,
        log_level=server_config.log_level,
        reload=False
    )
