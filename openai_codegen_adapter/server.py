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
                "id": "cla���q�^u�蛭|�g!j��[��\�����YH]][YK����
B����\��[������\��X�H��[�X�Y	�Y��[��\��[�X�Y[�H	�\�X�Y	�H]��[��\�����YH�B��]\���[��\��[�X�Y��Y��]��]\��[�N���]\����]\Ȏ��ۈ�Y��[��\��[�X�Y[�H�ٙ����\�����Y���[��\�����Y�\�ٛܛX]

K��\[YH����]][YK����
HH�[��\�����Y
B�B����ؘ[�\��X�H�]B��\��X�W��]HH�\��X�T�]J
B���\��]
�ȋ�\�ۜ�W��\��RS�\�ۜ�JB�\�[��Y��X��ZJ
N������\��HH�X�RH�܈�\��X�H�۝��������]X��]H]
��]X��[�^�[�B�Y��]X��]�^\��
N���]\��S�\�ۜ�J�۝[�\�]X��]��XY�^

K�]\����OL�
B�[�N���]\��S�\�ۜ�J��۝[�H����[����O��O��[�RH��Y�[�Y\\��O����X�RH����[��X\�H[��\�H�]X��[�^�[^\�ˏ����H�Y�H��X[��X[�X���O����؛�O���[�������]\����OL��
B���\��]
��\K��]\ȊB�\�[��Y��]��\��X�W��]\�
N������]�\��[��\��X�H�]\ˈ�����N���]\��]HH�\��X�W��]K��]��]\�
B���YX[�X��[��ܛX][ۂ�X[��]\�H]�Z]X[��X��
B��]\��]VȚX[�HHX[��]\��]\���]\��]B�^�\^�\[ۈ\�N�����\��\��܊��\��܈�][���\��X�H�]\Έ�_H�B��Z\�H^�\[ۊ�]\����OML]Z[H��Z[Y��]�\��X�H�]\ȊB���\���
��\K����H�B�\�[��Y����W��\��X�J
N��������H�\��X�Hۋ�ٙ�������N���]���]\�H�\��X�W��]K����J
B��]\��]HH�\��X�W��]K��]��]\�
B���]\����]\Ȏ��]���]\���Y\��Y�H�����\��X�H��[�X�Y	�Y��]���]\�[�H	�\�X�Y	�H���]H���]\��]B�B�^�\^�\[ۈ\�N�����\��\��܊��\��܈���[���\��X�N��_H�B��Z\�H^�\[ۊ�]\����OML]Z[H��Z[Y����H�\��X�H�B���\���
��\K�\����ݚY\�H�B�\�[��Y�\���ݚY\��ݚY\�����\]Y\��X�
N�����\�H�X�Y�X��ݚY\�\�[��H\��ܚ\ˈ�����N����[Y]H�ݚY\���[Y��ݚY\��Hț�[�ZH��[���Xȋ�����H�B�Y��ݚY\���[��[Y��ݚY\�΂��Z\�H^�\[ۊ�]\����OM]Z[Y��[��[Y�ݚY\��]\��HۙHَ�ݘ[Y��ݚY\��H�B����]\��ܚ\]��ܚ\�]H]
��\����ݚY\�K�H�B�Y����ܚ\�]�^\��
N���Z\�H^�\[ۊ�]\����OM]Z[Y��\��ܚ\�܈��ݚY\�H����[��B����\\�H��[X[�\��[Y[��YH��\˙^X�]X�K���ܚ\�]
K�KZ��ۈ�B���Y�\��H��\Y��ݚYY�Y����\�[��\]Y\�[��\]Y\�Ȝ��\�N���Y�^[�
ȋK\��\��\]Y\�Ȝ��\�WJB���Y�\�HT�Y��ݚYY�Y���\�W�\��[��\]Y\�[��\]Y\�Ș�\�W�\��N���Y�^[�
ȋKX�\�K]\���\]Y\�Ș�\�W�\��WJB���Y[�[Y��ݚYY�Y��[�[�[��\]Y\�[��\]Y\�ț[�[�N���Y�^[�
ȋK[[�[��\]Y\�ț[�[�WJB����[�H\��ܚ\��\�[H�X����\�˜�[���Y��\\�W��]]U�YK�^U�YK�[Y[�]L��
B���\��HH��ӈ�]]�Y��\�[���]���N��\�ܙ\�[H��ۋ��Y��\�[���]
B��]\��\�ܙ\�[�^�\��ۋ���ӑX��Q\��܎���Y���ӈ\��[���Z[��]\���]��]]��]\����X��\�Ȏ��\�[��]\����HOH���\��X�H���ݚY\��]J
K���\�ۜ�H���\�[���]��\��܈���\�[��\��Y��\�[��]\����HOH[�H�ۙB�B�[�N���]\����X��\�Ȏ��[�K���\��X�H���ݚY\��]J
K���\�ۜ�H������\��܈���\�[��\��܈����]]���H\��ܚ\��B��^�\�X����\�˕[Y[�]^\�Y���]\����X��\�Ȏ��[�K���\��X�H���ݚY\��]J
K���\�ۜ�H������\��܈���\��ܚ\[YY�]Y�\���X�ۙȂ�B�^�\^�\[ۈ\�N�����\��\��܊��\��܈\�[����ݚY\�N��_H�B��]\����X��\�Ȏ��[�K���\��X�H���ݚY\��]J
K���\�ۜ�H������\��܈����JB�B��\���
��YZ[���X\�X�X�H�B�\�[��Y��X\���X�J
N������X\�H�\�ۜ�H�X�H�܈��\��\�ۜ�\ˈ�����N�����]�H��Y�[���Y[���]��X�W��]�
B���Y�[���Y[���X\���X�J
B��]\����]\Ȏ���X��\�ȋ��Y\��Y�H����X�H�X\�Y�X��\�ٝ[H����]�[�\���X�W��]Ȏ����]���[Y\�[\��[YK�[YJ
B�B�^�\^�\[ۈ\�N�����\��\��܊���c�X�H�X\��Z[Y��_H�B��]\��Ȝ�]\Ȏ��\��܈��\��܈����J_B��\���
��YZ[���][[�H�B�\�[��Y��]��Y[��[�J[�N���N������[��HH�Y[��\�][ۈ[�K������N����[Y]H[�B��N���Y[��[�HH�Y[�[�J[�K���\�
JB�^�\�[YQ\��܎���]\����]\Ȏ��\��܈���\��܈����[��[Y[�K��[Y[�\Έ��K��[YH�܈H[��Y[�[�W_H��B�����]�H��Y�[���Y[���]��]�
B���Y�[���Y[���]�[�J�Y[��[�JB��]���]�H��Y�[���Y[���]��]�
B���]\����]\Ȏ���X��\�ȋ��Y\��Y�H�����Y[�[�H�[��Y��[�_H�����[�H�����]˙�]
�[�H�K���]��[�H���]���]˙�]
�[�H�K��[Y\�[\��[YK�[YJ
B�B�^�\^�\[ۈ\�N�����\��\��܊���c[�H�[��H�Z[Y��_H�B��]\��Ȝ�]\Ȏ��\��܈��\��܈����J_B���ZY]�\�H��X���\��X�H�]\��܈TH[��[�\�ZY]�\�J��B�\�[��Y��\��X�W��]\��ZY]�\�J�\]Y\���\]Y\��[ۙ^
N�����ZY]�\�H��X��Y��\��X�H\�[�X�Y�܈TH[��[�ˈ�����[��X��\����X�RK�]\����K[�X[[��[�[��Y�]�Hȋȋ��\K��]\ȋ��\K����H���X[����]XȗB��Y�[�J�\]Y\��\��]��\���]
]
H�܈][�[��Y�]�N���\�ۜ�HH]�Z]�[ۙ^
�\]Y\�
B��]\���\�ۜ�B����X��Y��\��X�H\�[�X�Y�܈�\�[��[�Y����\��X�W��]K�\��[�X�Y���]\����Ӕ�\�ۜ�J��]\����OML���۝[�^�\��܈���Y\��Y�H����\��X�H\��\��[�H\�X�Y�\�HH�X�RH�[�X�H]����\H����\��X�W�\�X�Y�����H����\��X�W�\�X�Y��B�B�
B���\�ۜ�HH]�Z]�[ۙ^
�\]Y\�
B��]\���\�ۜ�B���Y��ۘ[YW��OH���XZ[��Ȏ��]�X�ܛ���[����[�ZW���Y�[��Y\\���\��\��\����\�\��\���ۙ�Y˚���ܝ\�\��\���ۙ�Y˜ܝ����]�[\�\��\���ۙ�Y˛���]�[��[�YQ�[�B�
B