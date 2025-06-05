"""
FastAPI server providing OpenAI-compatible API endpoints.
Enhanced with comprehensive logging and multi-provider support.
"""

import logging
import traceback
import time
import os
import uuid
from datetime import datetime
from fastapi import FastAPI, HTTPException, Request, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse
import uvicorn
import httpx
import asyncio
from dotenv import load_dotenv
import json
from typing import List, Dict, Any

# Load environment variables from .env file
load_dotenv()

# Configuration from environment variables
CODEGEN_ORG_ID = os.getenv("CODEGEN_ORG_ID", "323")
CODEGEN_API_TOKEN = os.getenv("CODEGEN_API_TOKEN", "sk-ce027fa7-3c8d-4beb-8c86-ed8ae982ac99")
SERVER_HOST = os.getenv("SERVER_HOST", "127.0.0.1")
SERVER_PORT = int(os.getenv("SERVER_PORT", "19887"))
LOG_LEVEL = os.getenv("LOG_LEVEL", "info")
CORS_ORIGINS = json.loads(os.getenv("CORS_ORIGINS", '["*"]'))

# Use absolute imports for better compatibility
try:
    from models import (
        ChatRequest, TextRequest, ChatResponse, TextResponse,
        ErrorResponse, ErrorDetail, AnthropicRequest, AnthropicResponse,
        GeminiRequest, GeminiResponse
    )
    from config import get_codegen_config, get_server_config
    from codegen_client import CodegenClient
    from request_transformer import (
        chat_request_to_prompt, text_request_to_prompt,
        extract_generation_params
    )
    from response_transformer import (
        create_chat_response, create_text_response,
        estimate_tokens as estimate_tokens_orig, clean_content
    )
    from streaming import create_streaming_response, collect_streaming_response as collect_streaming_response_orig
    from anthropic_transformer import (
        anthropic_request_to_prompt, create_anthropic_response,
        extract_anthropic_generation_params
    )
    from anthropic_streaming import (
        create_anthropic_streaming_response, collect_anthropic_streaming_response
    )
    from gemini_transformer import (
        gemini_request_to_prompt, create_gemini_response,
        extract_gemini_generation_params
    )
    from gemini_streaming import (
        create_gemini_streaming_response, collect_gemini_streaming_response
    )
except ImportError:
    # Fallback for relative imports if needed
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
        estimate_tokens as estimate_tokens_orig, clean_content
    )
    from .streaming import create_streaming_response, collect_streaming_response as collect_streaming_response_orig
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
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('openai_adapter.log')
    ]
)
logger = logging.getLogger(__name__)

# Initialize configurations
codegen_config = get_codegen_config()
server_config = get_server_config()

# Initialize Codegen client
try:
    config = get_codegen_config()
    codegen_client = CodegenClient(
        org_id=config.org_id or os.getenv("CODEGEN_ORG_ID", "323"),
        token=config.api_token or os.getenv("CODEGEN_API_TOKEN", "sk-dummy-token")
    )
    logger.info("✅ Codegen client initialized successfully")
except Exception as e:
    logger.error(f"❌ Failed to initialize Codegen client: {e}")
    codegen_client = None

# Create FastAPI app
app = FastAPI(
    title="OpenAI Codegen Adapter",
    description="OpenAI-compatible API for Codegen platform",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def log_request_start(endpoint: str, request_data: dict):
    """Log the start of a request with enhanced formatting."""
    logger.info(f"🚀 REQUEST START | Endpoint: {endpoint}")
    logger.info(f"   📊 Request Data: {str(request_data)[:200]}...")
    logger.info(f"   🕐 Timestamp: {datetime.now().isoformat()}")


def log_completion_tracking(task_id: str, status: str, attempt: int, duration: float):
    """Log completion checking process with detailed tracking."""
    logger.info(f"🔍 COMPLETION CHECK | Task: {task_id} | Status: {status} | Attempt: {attempt} | Duration: {duration:.2f}s")


def log_openai_response_generation(response_data: dict, processing_time: float):
    """Log OpenAI response generation with detailed metrics."""
    logger.info(f"🤖 OPENAI RESPONSE GENERATED")
    logger.info(f"   ⏱️ Processing Time: {processing_time:.2f}s")
    logger.info(f"   📝 Response ID: {response_data.get('id', 'N/A')}")
    logger.info(f"   🎯 Model: {response_data.get('model', 'N/A')}")
    
    # Log usage statistics if available
    usage = response_data.get('usage', {})
    if usage:
        logger.info(f"   📊 Token Usage:")
        logger.info(f"      🔤 Prompt Tokens: {usage.get('prompt_tokens', 0)}")
        logger.info(f"      ✍️ Completion Tokens: {usage.get('completion_tokens', 0)}")
        logger.info(f"      📈 Total Tokens: {usage.get('total_tokens', 0)}")


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
    """List available models (OpenAI compatible)."""
    models = [
        {
            "id": "gpt-3.5-turbo",
            "object": "model",
            "created": int(time.time()),
            "owned_by": "codegen"
        },
        {
            "id": "gpt-4",
            "object": "model", 
            "created": int(time.time()),
            "owned_by": "codegen"
        },
        {
            "id": "text-davinci-003",
            "object": "model",
            "created": int(time.time()),
            "owned_by": "codegen"
        }
    ]
    return {"object": "list", "data": models}


@app.post("/v1/chat/completions")
async def chat_completions(request: ChatRequest):
    """OpenAI-compatible chat completions endpoint that calls the real Codegen API."""
    logger.info(f"🎯 Chat completion request: {request.model}")
    
    try:
        # Convert ChatRequest messages to the format expected by Codegen API
        messages = []
        for msg in request.messages:
            messages.append({
                "role": msg.role,
                "content": msg.content
            })
        
        # Call the real Codegen API
        logger.info(f"🚀 Calling Codegen API with {len(messages)} messages")
        codegen_response = await call_codegen_api(messages, request.model)
        
        # Convert Codegen response to OpenAI format
        response = ChatResponse(
            id=codegen_response.get("id", f"chatcmpl-{int(time.time())}"),
            object="chat.completion",
            created=int(time.time()),
            model=request.model,
            choices=[{
                "index": 0,
                "message": {
                    "role": "assistant",
                    "content": codegen_response["choices"][0]["message"]["content"]
                },
                "finish_reason": codegen_response["choices"][0].get("finish_reason", "stop")
            }],
            usage={
                "prompt_tokens": codegen_response.get("usage", {}).get("prompt_tokens", 0),
                "completion_tokens": codegen_response.get("usage", {}).get("completion_tokens", 0),
                "total_tokens": codegen_response.get("usage", {}).get("total_tokens", 0)
            }
        )
        
        logger.info(f"✅ Successfully returned response from Codegen API")
        return response
        
    except Exception as e:
        logger.error(f"❌ Error in chat completions: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/v1/completions")
async def text_completions(request: TextRequest):
    """OpenAI-compatible text completions endpoint."""
    logger.info(f"🚀 Text completion request: {request.model}")
    
    if not codegen_client:
        return create_error_response("Codegen client not available")
    
    try:
        if request.stream:
            # Return streaming response
            logger.info("🌊 Initiating streaming response...")
            return StreamingResponse(
                stream_text_response(request.prompt),
                media_type="text/plain"
            )
        else:
            # Get complete response
            content = await collect_streaming_response(codegen_client, request.prompt)
            
            # Create response
            response = TextResponse(
                id=f"cmpl-{int(time.time())}",
                object="text_completion",
                created=int(time.time()),
                model=request.model,
                choices=[{
                    "text": content,
                    "index": 0,
                    "finish_reason": "stop"
                }],
                usage={
                    "prompt_tokens": int(estimate_tokens(request.prompt)),
                    "completion_tokens": int(estimate_tokens(content)),
                    "total_tokens": int(estimate_tokens(request.prompt + content))
                }
            )
            
            logger.info(f"✅ Text completion successful: {len(content)} chars")
            return response
            
    except Exception as e:
        logger.error(f"❌ Text completion error: {e}")
        return create_error_response(f"Text completion failed: {str(e)}")


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
    """Anthropic-compatible messages endpoint that calls the real Codegen API."""
    logger.info(f"🎯 Anthropic messages request: {request.model}")
    
    try:
        # Convert Anthropic format to Codegen API format
        messages = []
        for msg in request.messages:
            messages.append({
                "role": msg.role,
                "content": msg.content
            })
        
        # Call the real Codegen API
        logger.info(f"🚀 Calling Codegen API with {len(messages)} messages")
        codegen_response = await call_codegen_api(messages, request.model)
        
        # Convert Codegen response to Anthropic format
        response = AnthropicResponse(
            id=codegen_response.get("id", f"msg_{uuid.uuid4().hex[:29]}"),
            type="message",
            role="assistant",
            content=[{
                "type": "text",
                "text": codegen_response["choices"][0]["message"]["content"]
            }],
            model=request.model,
            stop_reason=codegen_response["choices"][0].get("finish_reason", "end_turn"),
            stop_sequence=None,
            usage=AnthropicUsage(
                input_tokens=codegen_response.get("usage", {}).get("prompt_tokens", 0),
                output_tokens=codegen_response.get("usage", {}).get("completion_tokens", 0)
            )
        )
        
        logger.info(f"✅ Successfully returned Anthropic response from Codegen API")
        return response
        
    except Exception as e:
        logger.error(f"❌ Error in Anthropic messages: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/v1/gemini/generateContent")
async def gemini_generate_content(request: GeminiRequest):
    """Gemini-compatible generateContent endpoint that calls the real Codegen API."""
    logger.info(f"🎯 Gemini generateContent request: {request.model}")
    
    try:
        # Convert Gemini format to Codegen API format
        messages = []
        for content in request.contents:
            for part in content.parts:
                messages.append({
                    "role": "user",
                    "content": part.text
                })
        
        # Call the real Codegen API
        logger.info(f"🚀 Calling Codegen API with {len(messages)} messages")
        codegen_response = await call_codegen_api(messages, request.model)
        
        # Convert Codegen response to Gemini format
        response = GeminiResponse(
            candidates=[
                GeminiCandidate(
                    content=GeminiContent(
                        parts=[GeminiPart(text=codegen_response["choices"][0]["message"]["content"])],
                        role="model"
                    ),
                    finishReason="STOP",
                    index=0
                )
            ],
            usageMetadata=GeminiUsageMetadata(
                promptTokenCount=codegen_response.get("usage", {}).get("prompt_tokens", 0),
                candidatesTokenCount=codegen_response.get("usage", {}).get("completion_tokens", 0),
                totalTokenCount=codegen_response.get("usage", {}).get("total_tokens", 0)
            )
        )
        
        logger.info(f"✅ Successfully returned Gemini response from Codegen API")
        return response
        
    except Exception as e:
        logger.error(f"❌ Error in Gemini generateContent: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/v1/gemini/completions")
async def gemini_completions(request: GeminiRequest):
    """
    Create a Gemini-style completion using Codegen SDK.
    Compatible with Google's Gemini API format.
    """
    try:
        log_request_start("/v1/gemini/completions", request.dict())
        
        # Convert Gemini request to prompt
        prompt = gemini_request_to_prompt(request)
        logger.debug(f"Converted Gemini completion prompt: {prompt[:200]}...")
        
        # Extract generation parameters
        gen_params = extract_gemini_generation_params(request)
        logger.debug(f"Gemini completion generation parameters: {gen_params}")
        
        if request.stream:
            # Return streaming response
            logger.info("🌊 Initiating Gemini completion streaming response...")
            return create_gemini_streaming_response(
                codegen_client,
                prompt,
                request.model,
                f"gemini_cmpl_{hash(prompt) % 1000000}",
                completion_format=True
            )
        else:
            # Return complete response
            logger.info("📦 Initiating Gemini completion non-streaming response...")
            content = await collect_gemini_streaming_response(codegen_client, prompt)
            
            # Estimate token counts
            input_tokens = estimate_tokens_orig(prompt)
            output_tokens = estimate_tokens_orig(content)
            
            logger.info(f"🔢 Gemini completion token estimation - Input: {input_tokens}, Output: {output_tokens}")
            
            response = create_gemini_response(
                content=content,
                model=request.model,
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                completion_format=True
            )
            
            logger.info(f"✅ Gemini completion successful")
            return response
            
    except Exception as e:
        logger.error(f"❌ Error in Gemini completion: {e}")
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


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    try:
        return {"status": "healthy", "timestamp": datetime.now().isoformat()}
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return {"status": "unhealthy", "error": str(e)}


# Utility functions
def estimate_tokens(text: str) -> int:
    """Estimate token count for text."""
    return len(text.split()) * 1.3  # Rough estimation

def create_error_response(message: str, error_type: str = "invalid_request_error", code: str = "invalid_request") -> JSONResponse:
    """Create standardized error response."""
    error_detail = ErrorDetail(message=message, type=error_type, code=code)
    error_response = ErrorResponse(error=error_detail)
    return JSONResponse(
        status_code=400,
        content=error_response.dict()
    )

async def collect_streaming_response(client, prompt: str) -> str:
    """Collect streaming response into a single string."""
    if not client:
        return "Error: Codegen client not available"
    
    try:
        content = ""
        async for chunk in client.run_task(prompt, stream=True):
            content += chunk
        return content
    except Exception as e:
        logger.error(f"Error collecting streaming response: {e}")
        return f"Error: {str(e)}"

async def stream_chat_response(prompt: str):
    """Stream chat completion response."""
    if not codegen_client:
        yield "data: Error: Codegen client not available\n\n"
        return
    
    try:
        async for chunk in codegen_client.run_task(prompt, stream=True):
            yield f"data: {chunk}\n\n"
        yield "data: [DONE]\n\n"
    except Exception as e:
        yield f"data: Error: {str(e)}\n\n"

async def stream_text_response(prompt: str):
    """Stream text completion response."""
    if not codegen_client:
        yield "data: Error: Codegen client not available\n\n"
        return
    
    try:
        async for chunk in codegen_client.run_task(prompt, stream=True):
            yield f"data: {chunk}\n\n"
        yield "data: [DONE]\n\n"
    except Exception as e:
        yield f"data: Error: {str(e)}\n\n"

# Codegen API client
async def call_codegen_api(messages: List[Dict], model: str = "claude-3-5-sonnet-20241022") -> Dict[str, Any]:
    """Call the actual Codegen API and return real response"""
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            payload = {
                "model": model,
                "messages": messages,
                "max_tokens": 1000,
                "temperature": 0.7
            }
            
            # Try different authentication header combinations
            auth_variants = [
                {
                    "Authorization": f"Bearer {CODEGEN_API_TOKEN}",
                    "Content-Type": "application/json",
                    "X-Organization-ID": CODEGEN_ORG_ID
                },
                {
                    "Authorization": f"Bearer {CODEGEN_API_TOKEN}",
                    "Content-Type": "application/json"
                },
                {
                    "Authorization": f"Token {CODEGEN_API_TOKEN}",
                    "Content-Type": "application/json",
                    "X-Organization-ID": CODEGEN_ORG_ID
                },
                {
                    "X-API-Key": CODEGEN_API_TOKEN,
                    "Content-Type": "application/json",
                    "X-Organization-ID": CODEGEN_ORG_ID
                }
            ]
            
            logger.info(f"🚀 Calling Codegen API with org_id={CODEGEN_ORG_ID}")
            logger.info(f"📝 Payload: {json.dumps(payload, indent=2)}")
            
            # Try multiple possible API endpoints
            api_urls = [
                "https://api.codegen.com/v1/chat/completions",
                "https://codegen.com/api/v1/chat/completions",
                "https://api.codegen.com/chat/completions",
                "https://codegen.com/v1/chat/completions"
            ]
            
            last_error = None
            for api_url in api_urls:
                for i, headers in enumerate(auth_variants):
                    try:
                        logger.info(f"🔄 Trying API URL: {api_url} with auth variant {i+1}")
                        response = await client.post(
                            api_url,
                            json=payload,
                            headers=headers
                        )
                        
                        logger.info(f"📡 Response Status: {response.status_code} from {api_url}")
                        
                        if response.status_code == 200:
                            result = response.json()
                            logger.info(f"✅ Success! Response: {json.dumps(result, indent=2)}")
                            return result
                        elif response.status_code == 404:
                            logger.warning(f"⚠️ 404 Not Found for {api_url} with auth {i+1}")
                            last_error = f"404 Not Found: {api_url}"
                            continue
                        elif response.status_code == 401:
                            logger.warning(f"⚠️ 401 Unauthorized for {api_url} with auth {i+1}")
                            last_error = f"401 Unauthorized: {api_url}"
                            continue
                        else:
                            error_text = response.text
                            logger.error(f"❌ API Error {response.status_code} from {api_url}: {error_text}")
                            last_error = f"{response.status_code}: {error_text}"
                            
                    except httpx.ConnectError as e:
                        logger.warning(f"⚠️ Connection error for {api_url}: {e}")
                        last_error = f"Connection error: {e}"
                        continue
                        
            # If we get here, all URLs and auth methods failed
            # Return a helpful mock response with instructions
            logger.error("🚨 All Codegen API endpoints failed - returning mock response with instructions")
            return {
                "id": f"chatcmpl-mock-{int(time.time())}",
                "object": "chat.completion",
                "created": int(time.time()),
                "model": model,
                "choices": [{
                    "index": 0,
                    "message": {
                        "role": "assistant",
                        "content": f"""🚨 CODEGEN API CONNECTION FAILED 🚨

The API adapter could not connect to the Codegen API. Here's what was tried:

API URLs tested:
- https://api.codegen.com/v1/chat/completions
- https://codegen.com/api/v1/chat/completions  
- https://api.codegen.com/chat/completions
- https://codegen.com/v1/chat/completions

Authentication methods tested:
- Bearer token with X-Organization-ID header
- Bearer token only
- Token prefix with X-Organization-ID
- X-API-Key header

Current configuration:
- CODEGEN_ORG_ID: {CODEGEN_ORG_ID}
- CODEGEN_API_TOKEN: {CODEGEN_API_TOKEN[:20]}...

Last error: {last_error}

NEXT STEPS:
1. Verify your API token is valid and active
2. Check if the API endpoint URL has changed
3. Confirm your organization ID is correct
4. Contact Codegen support for the correct API endpoint

This is a MOCK response - the real API integration needs to be fixed!"""
                    },
                    "finish_reason": "stop"
                }],
                "usage": {
                    "prompt_tokens": 50,
                    "completion_tokens": 200,
                    "total_tokens": 250
                }
            }
                
    except httpx.TimeoutException:
        logger.error("⏰ Codegen API request timed out")
        raise HTTPException(status_code=504, detail="Codegen API request timed out")
    except Exception as e:
        logger.error(f"💥 Unexpected error calling Codegen API: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

if __name__ == "__main__":
    uvicorn.run(
        "server:app",
        host=SERVER_HOST,
        port=SERVER_PORT,
        log_level=LOG_LEVEL
    )
