"""
FastAPI server providing OpenAI-compatible API endpoints.
Based on h2ogpt's server.py structure and patterns.
Enhanced with comprehensive logging for completion tracking and OpenAI response generation.
Enhanced with Anthropic Claude API compatibility.
Enhanced with Web UI for service control.
"""

import logging
import traceback
import time
import uuid
from datetime import datetime
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
import uvicorn
import os
from pathlib import Path
import sys
import subprocess
import json

from .models import (
    ChatRequest, TextRequest, AnthropicRequest, GeminiRequest,
    ChatResponse, TextResponse, AnthropicResponse, GeminiResponse,
    ErrorResponse, ErrorDetail,
    EmbeddingRequest, EmbeddingResponse, EmbeddingData, EmbeddingUsage,
    AudioTranscriptionRequest, AudioTranscriptionResponse,
    AudioTranslationRequest, AudioTranslationResponse,
    ImageGenerationRequest, ImageGenerationResponse, ImageData
)
from .config import get_codegen_config, get_server_config
from .client import CodegenClient, ClientMode
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
codegen_client = CodegenClient(codegen_config, mode=ClientMode.PRODUCTION)

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

# Add static files for Web UI
app.mount("/static", StaticFiles(directory="static"), name="static")

def log_request_start(endpoint: str, request_data: dict):
    """Log the start of a request with enhanced details."""
    logger.info(f"ğŸš€ REQUEST START | Endpoint: {endpoint}")
    logger.info(f"   ğŸ“Š Request Data: {request_data}")
    logger.info(f"   ğŸ• Timestamp: {datetime.now().isoformat()}")

def log_completion_tracking(task_id: str, status: str, attempt: int, duration: float):
    """Log completion checking process with detailed tracking."""
    logger.info(f"ğŸ” COMPLETION CHECK | Task: {task_id} | Status: {status} | Attempt: {attempt} | Duration: {duration:.2f}s")

def log_openai_response_generation(response_data: dict, processing_time: float):
    """Log OpenAI API compatible response generation."""
    logger.info(f"ğŸ“¤ OPENAI RESPONSE GENERATED | Processing Time: {processing_time:.2f}s")
    logger.info(f"   ğŸ†” Response ID: {response_data.get('id', 'N/A')}")
    logger.info(f"   ï¿½ï¿½ï¿½ï¿½ï¿½ï¿½ï¿½ï¿½ï¿½ï¿½ Model: {response_data.get('model', 'N/A')}")
    logger.info(f"   ğŸ“ Choices: {len(response_data.get('choices', []))}")
    
    if 'usage' in response_data:
        usage = response_data['usage']
        logger.info(f"   ğŸ”¢ Token Usage - Prompt: {usage.get('prompt_tokens', 0)}, "
                   f"Completion: {usage.get('completion_tokens', 0)}, "
                   f"Total: {usage.get('total_tokens', 0)}")
    
    # Log first 100 chars of response content
    if response_data.get('choices') and len(response_data['choices']) > 0:
        choice = response_data['choices'][0]
        if 'message' in choice and 'content' in choice['message']:
            content = choice['message']['content']
            logger.info(f"   ğŸ“„ Content Preview: {content[:100]}...")

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Enhanced global exception handler to return OpenAI-compatible errors."""
    logger.error(f"Unhandled exception: {exc}\n{traceback.format_exc()}")
    
    # Map different exception types to appropriate error responses
    if isinstance(exc, ValueError):
        error_type = "invalid_request_error"
        status_code = 400
    elif isinstance(exc, KeyError):
        error_type = "invalid_request_error"
        status_code = 400
    elif isinstance(exc, TimeoutError):
        error_type = "timeout_error"
        status_code = 408
    elif isinstance(exc, ConnectionError):
        error_type = "connection_error"
        status_code = 503
    else:
        error_type = "internal_server_error"
        status_code = 500
    
    error_response = ErrorResponse(
        error=ErrorDetail(
            message=str(exc),
            type=error_type,
            code="server_error"
        )
    )
    
    return JSONResponse(
        status_code=status_code,
        content=error_response.dict()
    )

@app.get("/v1/models")
async def list_models():
    """List available models (OpenAI, Anthropic, and Google compatibility)."""
    return {
        "object": "list",
        "data": [
            # OpenAI Models
            {
                "id": "gpt-4",
                "object": "model",
                "created": 1677610602,
                "owned_by": "openai"
            },
            {
                "id": "gpt-4-turbo",
                "object": "model",
                "created": 1677610602,
                "owned_by": "openai"
            },
            {
                "id": "gpt-3.5-turbo",
                "object": "model",
                "created": 1677610602,
                "owned_by": "openai"
            },
            {
                "id": "text-embedding-ada-002",
                "object": "model",
                "created": 1677610602,
                "owned_by": "openai"
            },
            {
                "id": "whisper-1",
                "object": "model",
                "created": 1677610602,
                "owned_by": "openai"
            },
            {
                "id": "dall-e-3",
                "object": "model",
                "created": 1677610602,
                "owned_by": "openai"
            },
            # Anthropic Models
            {
                "id": "claude-3-opus-20240229",
                "object": "model",
                "created": 1677610602,
                "owned_by": "anthropic"
            },
            {
                "id": "claude-3-sonnet-20240229",
                "object": "model",
                "created": 1677610602,
                "owned_by": "anthropic"
            },
            {
                "id": "cla¶»§q«^uúè›­|÷g!j»Ù[‹›\İİÙÙÛYH]][YK››İÊ
BˆÙÙÙ\‹š[™›Êˆ”Ù\šXÙHÉÙ[˜X›Y	ÈYˆÙ[‹š\×Ù[˜X›Y[ÙH	Ù\ØX›Y	ßH]ÜÙ[‹›\İİÙÙÛYHŠBˆ™]\›ˆÙ[‹š\×Ù[˜X›YˆˆYˆÙ]Üİ]\ÊÙ[ŠN‚ˆ™]\›ˆÂˆœİ]\Èˆ›ÛˆˆYˆÙ[‹š\×Ù[˜X›Y[ÙH›Ù™ˆ‹ˆ›\İİÙÙÛYˆÙ[‹›\İİÙÙÛYš\ÛÙ›Ü›X]

Kˆ\[YHˆİŠ]][YK››İÊ
HHÙ[‹›\İİÙÙÛY
BˆB‚ˆÈÛØ˜[Ù\šXÙHİ]BœÙ\šXÙWÜİ]HHÙ\šXÙTİ]J
B‚‚\™Ù]
‹È‹™\ÜÛœÙWØÛ\ÜÏRS™\ÜÛœÙJB˜\Ş[˜ÈYˆÙX—İZJ
N‚ˆˆˆ”Ù\™HHÙXˆRH›ÜˆÙ\šXÙHÛÛ›Ûˆˆˆ‚ˆİ]X×Ü]H]
œİ]XËÚ[™^š[ŠBˆYˆİ]X×Ü]™^\İÊ
N‚ˆ™]\›ˆS™\ÜÛœÙJÛÛ[\İ]X×Ü]œ™XYİ^

Kİ]\×ØÛÙOLŒ
Bˆ[ÙN‚ˆ™]\›ˆS™\ÜÛœÙJˆÛÛ[Hˆˆ‚ˆ[‚ˆ›ÙO‚ˆO“Ü[RHÛÙYÙ[ˆY\\ÚO‚ˆ•ÙXˆRH›İ›İ[™ˆX\ÙH[œİ\™Hİ]XËÚ[™^š[^\İËÜ‚ˆH™YH‹ÚX[’X[ÚXÚÏØOÜ‚ˆØ›ÙO‚ˆÚ[‚ˆˆˆ‹ˆİ]\×ØÛÙOLŒˆ
B‚‚\™Ù]
‹Ø\KÜİ]\ÈŠB˜\Ş[˜ÈYˆÙ]ÜÙ\šXÙWÜİ]\Ê
N‚ˆˆˆ‘Ù]İ\œ™[Ù\šXÙHİ]\Ëˆˆˆ‚ˆN‚ˆİ]\×Ù]HHÙ\šXÙWÜİ]K™Ù]Üİ]\Ê
BˆˆÈYX[ÚXÚÈ[™›Ü›X][Û‚ˆX[Üİ]\ÈH]ØZ]X[ØÚXÚÊ
Bˆİ]\×Ù]VÈšX[—HHX[Üİ]\Âˆˆ™]\›ˆİ]\×Ù]Bˆ^Ù\^Ù\[Ûˆ\ÈN‚ˆÙÙÙ\‹™\œ›ÜŠˆ‘\œ›ÜˆÙ][™ÈÙ\šXÙHİ]\ÎˆÙ_HŠBˆ˜Z\ÙH^Ù\[ÛŠİ]\×ØÛÙOML]Z[H‘˜Z[YÈÙ]Ù\šXÙHİ]\ÈŠB‚‚\œÜİ
‹Ø\KİÙÙÛHŠB˜\Ş[˜ÈYˆÙÙÛWÜÙ\šXÙJ
N‚ˆˆˆ•ÙÙÛHÙ\šXÙHÛ‹ÛÙ™‹ˆˆˆ‚ˆN‚ˆ™]×Üİ]\ÈHÙ\šXÙWÜİ]KÙÙÛJ
Bˆİ]\×Ù]HHÙ\šXÙWÜİ]K™Ù]Üİ]\Ê
Bˆˆ™]\›ˆÂˆœİ]\Èˆ™]×Üİ]\Ëˆ›Y\ÜØYÙHˆˆ”Ù\šXÙHÉÙ[˜X›Y	ÈYˆ™]×Üİ]\È[ÙH	Ù\ØX›Y	ßH‹ˆ™]Hˆİ]\×Ù]BˆBˆ^Ù\^Ù\[Ûˆ\ÈN‚ˆÙÙÙ\‹™\œ›ÜŠˆ‘\œ›ÜˆÙÙÛ[™ÈÙ\šXÙNˆÙ_HŠBˆ˜Z\ÙH^Ù\[ÛŠİ]\×ØÛÙOML]Z[H‘˜Z[YÈÙÙÛHÙ\šXÙHŠB‚‚\œÜİ
‹Ø\Kİ\İŞÜ›İšY\ŸHŠB˜\Ş[˜ÈYˆ\İÜ›İšY\Š›İšY\ˆİ‹™\]Y\İˆXİ
N‚ˆˆˆ•\İHÜXÚYšXÈ›İšY\ˆ\Ú[™ÈH\İØÜš\Ëˆˆˆ‚ˆN‚ˆÈ˜[Y]H›İšY\‚ˆ˜[YÜ›İšY\œÈHÈ›Ü[˜ZH‹˜[›ÜXÈ‹™ÛÛÙÛH—BˆYˆ›İšY\ˆ›İ[ˆ˜[YÜ›İšY\œÎ‚ˆ˜Z\ÙH^Ù\[ÛŠİ]\×ØÛÙOM]Z[Yˆ’[˜[Y›İšY\‹ˆ]\İ™HÛ™HÙˆİ˜[YÜ›İšY\œßHŠBˆˆÈÙ]\İØÜš\]ˆØÜš\Ü]H]
ˆ\İŞÜ›İšY\ŸKœHŠBˆYˆ›İØÜš\Ü]™^\İÊ
N‚ˆ˜Z\ÙH^Ù\[ÛŠİ]\×ØÛÙOM]Z[Yˆ•\İØÜš\›ÜˆÜ›İšY\ŸH›İ›İ[™ŠBˆˆÈ™\\™HÛÛ[X[™\™İ[Y[ÂˆÛYHÜŞ\Ë™^Xİ]X›KİŠØÜš\Ü]
K‹KZœÛÛˆ—BˆˆÈYİ\İÛH›Û\Yˆ›İšYYˆYˆœ›Û\ˆ[ˆ™\]Y\İ[™™\]Y\İÈœ›Û\—N‚ˆÛY™^[™
È‹K\›Û\‹™\]Y\İÈœ›Û\—WJBˆˆÈY˜\ÙHT“Yˆ›İšYYˆYˆ˜˜\ÙWİ\›ˆ[ˆ™\]Y\İ[™™\]Y\İÈ˜˜\ÙWİ\›—N‚ˆÛY™^[™
È‹KX˜\ÙK]\›‹™\]Y\İÈ˜˜\ÙWİ\›—WJBˆˆÈY[Ù[Yˆ›İšYYˆYˆ›[Ù[ˆ[ˆ™\]Y\İ[™™\]Y\İÈ›[Ù[—N‚ˆÛY™^[™
È‹K[[Ù[‹™\]Y\İÈ›[Ù[—WJBˆˆÈ[ˆH\İØÜš\ˆ™\İ[HİXœ›ØÙ\ÜËœ[ŠˆÛYˆØ\\™WÛİ]]UYKˆ^UYKˆ[Y[İ]LÌˆ
BˆˆÈ\œÙHH”ÓÓˆİ]]ˆYˆ™\İ[œİİ]‚ˆN‚ˆ\İÜ™\İ[HœÛÛ‹›ØYÊ™\İ[œİİ]
Bˆ™]\›ˆ\İÜ™\İ[ˆ^Ù\œÛÛ‹’”ÓÓ‘XÛÙQ\œ›Ü‚ˆÈYˆ”ÓÓˆ\œÚ[™È˜Z[Ë™]\›ˆ˜]Èİ]]ˆ™]\›ˆÂˆœİXØÙ\ÜÈˆ™\İ[œ™]\›˜ÛÙHOHˆœÙ\šXÙHˆ›İšY\‹]J
Kˆœ™\ÜÛœÙHˆ™\İ[œİİ]ˆ™\œ›Üˆˆ™\İ[œİ\œˆYˆ™\İ[œ™]\›˜ÛÙHOH[ÙH›Û™BˆBˆ[ÙN‚ˆ™]\›ˆÂˆœİXØÙ\ÜÈˆ˜[ÙKˆœÙ\šXÙHˆ›İšY\‹]J
Kˆœ™\ÜÛœÙHˆˆ‹ˆ™\œ›Üˆˆ™\İ[œİ\œˆÜˆ“›Èİ]]œ›ÛH\İØÜš\‚ˆBˆˆ^Ù\İXœ›ØÙ\ÜË•[Y[İ]^\™Y‚ˆ™]\›ˆÂˆœİXØÙ\ÜÈˆ˜[ÙKˆœÙ\šXÙHˆ›İšY\‹]J
Kˆœ™\ÜÛœÙHˆˆ‹ˆ™\œ›Üˆˆ•\İØÜš\[YYİ]Y\ˆÌÙXÛÛ™È‚ˆBˆ^Ù\^Ù\[Ûˆ\ÈN‚ˆÙÙÙ\‹™\œ›ÜŠˆ‘\œ›Üˆ\İ[™ÈÜ›İšY\ŸNˆÙ_HŠBˆ™]\›ˆÂˆœİXØÙ\ÜÈˆ˜[ÙKˆœÙ\šXÙHˆ›İšY\‹]J
Kˆœ™\ÜÛœÙHˆˆ‹ˆ™\œ›ÜˆˆİŠJBˆB‚\œÜİ
‹ØYZ[‹ØÛX\‹XØXÚHŠB˜\Ş[˜ÈYˆÛX\—ØØXÚJ
N‚ˆˆˆÛX\ˆH™\ÜÛœÙHØXÚH›Üˆœ™\Ú™\ÜÛœÙ\Ëˆˆˆ‚ˆN‚ˆÛÜİ]ÈHÛÙYÙ[—ØÛY[™Ù]ØØXÚWÜİ]Ê
BˆÛÙYÙ[—ØÛY[˜ÛX\—ØØXÚJ
Bˆ™]\›ˆÂˆœİ]\ÈˆœİXØÙ\ÜÈ‹ˆ›Y\ÜØYÙHˆØXÚHÛX\™YİXØÙ\ÜÙ[H‹ˆœ™]š[İ\×ØØXÚWÜİ]ÈˆÛÜİ]Ëˆ[Y\İ[\ˆ[YK[YJ
BˆBˆ^Ù\^Ù\[Ûˆ\ÈN‚ˆÙÙÙ\‹™\œ›ÜŠˆ¸§cØXÚHÛX\ˆ˜Z[YˆÙ_HŠBˆ™]\›ˆÈœİ]\Èˆ™\œ›Üˆ‹™\œ›ÜˆˆİŠJ_B‚\œÜİ
‹ØYZ[‹ÜÙ][[ÙHŠB˜\Ş[˜ÈYˆÙ]ØÛY[Û[ÙJ[ÙNˆİŠN‚ˆˆˆÚ[™ÙHHÛY[Ü\˜][Ûˆ[ÙKˆˆˆ‚ˆN‚ˆÈ˜[Y]H[ÙBˆN‚ˆÛY[Û[ÙHHÛY[[ÙJ[ÙK›İÙ\Š
JBˆ^Ù\˜[YQ\œ›Ü‚ˆ™]\›ˆÂˆœİ]\Èˆ™\œ›Üˆ‹ˆ™\œ›Üˆˆˆ’[˜[Y[ÙKˆ˜[Y[Ù\ÎˆÖÛK˜[YH›ÜˆH[ˆÛY[[ÙW_H‚ˆBˆˆÛÜİ]ÈHÛÙYÙ[—ØÛY[™Ù]Üİ]Ê
BˆÛÙYÙ[—ØÛY[œÙ]Û[ÙJÛY[Û[ÙJBˆ™]×Üİ]ÈHÛÙYÙ[—ØÛY[™Ù]Üİ]Ê
Bˆˆ™]\›ˆÂˆœİ]\ÈˆœİXØÙ\ÜÈ‹ˆ›Y\ÜØYÙHˆˆÛY[[ÙHÚ[™ÙYÈÛ[Ù_H‹ˆ›ÛÛ[ÙHˆÛÜİ]Ë™Ù]
›[ÙHŠKˆ›™]×Û[ÙHˆ™]×Üİ]Ë™Ù]
›[ÙHŠKˆ[Y\İ[\ˆ[YK[YJ
BˆBˆ^Ù\^Ù\[Ûˆ\ÈN‚ˆÙÙÙ\‹™\œ›ÜŠˆ¸§c[ÙHÚ[™ÙH˜Z[YˆÙ_HŠBˆ™]\›ˆÈœİ]\Èˆ™\œ›Üˆ‹™\œ›ÜˆˆİŠJ_B‚ˆÈZY]Ø\™HÈÚXÚÈÙ\šXÙHİ]\È›ÜˆTH[™Ú[Â\›ZY]Ø\™JšŠB˜\Ş[˜ÈYˆÙ\šXÙWÜİ]\×ÛZY]Ø\™J™\]Y\İˆ™\]Y\İØ[Û™^
N‚ˆˆˆ“ZY]Ø\™HÈÚXÚÈYˆÙ\šXÙH\È[˜X›Y›ÜˆTH[™Ú[Ëˆˆˆ‚ˆÈ[İÈXØÙ\ÜÈÈÙXˆRKİ]\ËÙÙÛK[™X[[™Ú[Âˆ[İÙYÜ]ÈHÈ‹È‹‹Ø\KÜİ]\È‹‹Ø\KİÙÙÛH‹‹ÚX[‹‹Üİ]XÈ—BˆˆYˆ[J™\]Y\İ\›œ]œİ\İÚ]
]
H›Üˆ][ˆ[İÙYÜ]ÊN‚ˆ™\ÜÛœÙHH]ØZ]Ø[Û™^
™\]Y\İ
Bˆ™]\›ˆ™\ÜÛœÙBˆˆÈÚXÚÈYˆÙ\šXÙH\È[˜X›Y›Üˆİ\ˆ[™Ú[ÂˆYˆ›İÙ\šXÙWÜİ]Kš\×Ù[˜X›Y‚ˆ™]\›ˆ”ÓÓ”™\ÜÛœÙJˆİ]\×ØÛÙOMLËˆÛÛ[^Âˆ™\œ›ÜˆˆÂˆ›Y\ÜØYÙHˆ”Ù\šXÙH\Èİ\œ™[H\ØX›Yˆ\ÙHHÙXˆRHÈ[˜X›H]ˆ‹ˆ\HˆœÙ\šXÙWÙ\ØX›Y‹ˆ˜ÛÙHˆœÙ\šXÙWÙ\ØX›Y‚ˆBˆBˆ
Bˆˆ™\ÜÛœÙHH]ØZ]Ø[Û™^
™\]Y\İ
Bˆ™]\›ˆ™\ÜÛœÙB‚‚šYˆ×Û˜[YW×ÈOH—×ÛXZ[—×È‚ˆ]šXÛÜ›‹œ[Šˆ›Ü[˜ZWØÛÙYÙ[—ØY\\‹œÙ\™\˜\‹ˆÜİ\Ù\™\—ØÛÛ™šYËšÜİˆÜ\Ù\™\—ØÛÛ™šYËœÜˆÙ×Û]™[\Ù\™\—ØÛÛ™šYË›Ù×Û]™[ˆ™[ØYQ˜[ÙBˆ
B