"""
Pydantic models for OpenAI API compatibility.
Based on h2ogpt's server.py request/response models.
Enhanced with Anthropic Claude API compatibility.
"""

from typing import Optional, List, Union, Any, Dict, Literal
from pydantic import BaseModel, Field
import time
import uuid


class Message(BaseModel):
    role: Literal["system", "user", "assistant", "tool"]
    content: str
    name: Optional[str] = None


class ChatRequest(BaseModel):
    model: str = "gpt-3.5-turbo"
    messages: List[Message]
    temperature: Optional[float] = Field(default=0.7, ge=0.0, le=2.0)
    max_tokens: Optional[int] = Field(default=None, ge=1)
    top_p: Optional[float] = Field(default=1.0, ge=0.0, le=1.0)
    frequency_penalty: Optional[float] = Field(default=0.0, ge=-2.0, le=2.0)
    presence_penalty: Optional[float] = Field(default=0.0, ge=-2.0, le=2.0)
    stream: Optional[bool] = False
    stop: Optional[Union[str, List[str]]] = None
    user: Optional[str] = None


class TextRequest(BaseModel):
    model: str = "gpt-3.5-turbo-instruct"
    prompt: Union[str, List[str]]
    temperature: Optional[float] = Field(default=0.7, ge=0.0, le=2.0)
    max_tokens: Optional[int] = Field(default=16, ge=1)
    top_p: Optional[float] = Field(default=1.0, ge=0.0, le=1.0)
    frequency_penalty: Optional[float] = Field(default=0.0, ge=-2.0, le=2.0)
    presence_penalty: Optional[float] = Field(default=0.0, ge=-2.0, le=2.0)
    stream: Optional[bool] = False
    stop: Optional[Union[str, List[str]]] = None
    user: Optional[str] = None


# Anthropic Claude API Models
class AnthropicMessage(BaseModel):
    role: Literal["user", "assistant"]
    content: str


class AnthropicRequest(BaseModel):
    model: str = "claude-3-sonnet-20240229"
    max_tokens: int = Field(default=1024, ge=1)
    messages: List[AnthropicMessage]
    temperature: Optional[float] = Field(default=1.0, ge=0.0, le=1.0)
    top_p: Optional[float] = Field(default=None, ge=0.0, le=1.0)
    top_k: Optional[int] = Field(default=None, ge=1)
    stream: Optional[bool] = False
    stop_sequences: Optional[List[str]] = None
    system: Optional[str] = None


class AnthropicUsage(BaseModel):
    input_tokens: int
    output_tokens: int


class AnthropicResponse(BaseModel):
    id: str = Field(default_factory=lambda: f"msg_{uuid.uuid4().hex[:29]}")
    type: str = "message"
    role: str = "assistant"
    content: List[Dict[str, str]] = Field(default_factory=lambda: [{"type": "text", "text": ""}])
    model: str
    stop_reason: Optional[str] = "end_turn"
    stop_sequence: Optional[str] = None
    usage: AnthropicUsage


class AnthropicStreamEvent(BaseModel):
    type: str
    message: Optional[Dict[str, Any]] = None
    content_block: Optional[Dict[str, Any]] = None
    delta: Optional[Dict[str, Any]] = None
    usage: Optional[AnthropicUsage] = None


# Google Gemini API Models
class GeminiPart(BaseModel):
    text: str


class GeminiContent(BaseModel):
    role: Optional[str] = "user"
    parts: List[GeminiPart]


class GeminiGenerationConfig(BaseModel):
    temperature: Optional[float] = Field(default=None, ge=0.0, le=2.0)
    topP: Optional[float] = Field(default=None, ge=0.0, le=1.0)
    topK: Optional[int] = Field(default=None, ge=1)
    maxOutputTokens: Optional[int] = Field(default=None, ge=1)
    stopSequences: Optional[List[str]] = None


class GeminiRequest(BaseModel):
    contents: List[GeminiContent]
    generationConfig: Optional[GeminiGenerationConfig] = None
    systemInstruction: Optional[GeminiContent] = None


class GeminiUsageMetadata(BaseModel):
    promptTokenCount: int
    candidatesTokenCount: int
    totalTokenCount: int


class GeminiCandidate(BaseModel):
    content: GeminiContent
    finishReason: Optional[str] = "STOP"
    index: Optional[int] = 0


class GeminiResponse(BaseModel):
    candidates: List[GeminiCandidate]
    usageMetadata: Optional[GeminiUsageMetadata] = None
    modelVersion: Optional[str] = None


class Usage(BaseModel):
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int


class ChatChoice(BaseModel):
    index: int
    message: Message
    finish_reason: Optional[str] = "stop"


class ChatChoiceStream(BaseModel):
    index: int
    delta: Message
    finish_reason: Optional[str] = None


class TextChoice(BaseModel):
    index: int
    text: str
    finish_reason: Optional[str] = "stop"


class ChatResponse(BaseModel):
    id: str = Field(default_factory=lambda: f"chatcmpl-{uuid.uuid4().hex[:29]}")
    object: str = "chat.completion"
    created: int = Field(default_factory=lambda: int(time.time()))
    model: str
    choices: List[ChatChoice]
    usage: Usage


class ChatResponseStream(BaseModel):
    id: str = Field(default_factory=lambda: f"chatcmpl-{uuid.uuid4().hex[:29]}")
    object: str = "chat.completion.chunk"
    created: int = Field(default_factory=lambda: int(time.time()))
    model: str
    choices: List[ChatChoiceStream]


class TextResponse(BaseModel):
    id: str = Field(default_factory=lambda: f"cmpl-{uuid.uuid4().hex[:29]}")
    object: str = "text_completion"
    created: int = Field(default_factory=lambda: int(time.time()))
    model: str
    choices: List[TextChoice]
    usage: Usage


class ErrorDetail(BaseModel):
    message: str
    type: str
    param: Optional[str] = None
    code: Optional[str] = None


class ErrorResponse(BaseModel):
    error: ErrorDetail


# Add new request models for missing OpenAI endpoints
class EmbeddingRequest(BaseModel):
    """Request model for OpenAI embeddings endpoint."""
    input: Union[str, List[str]]
    model: str = "text-embedding-ada-002"
    encoding_format: Optional[str] = "float"
    dimensions: Optional[int] = None
    user: Optional[str] = None

class AudioTranscriptionRequest(BaseModel):
    """Request model for OpenAI audio transcription endpoint."""
    file: str  # Base64 encoded audio file
    model: str = "whisper-1"
    language: Optional[str] = None
    prompt: Optional[str] = None
    response_format: Optional[str] = "json"
    temperature: Optional[float] = 0

class AudioTranslationRequest(BaseModel):
    """Request model for OpenAI audio translation endpoint."""
    file: str  # Base64 encoded audio file
    model: str = "whisper-1"
    prompt: Optional[str] = None
    response_format: Optional[str] = "json"
    temperature: Optional[float] = 0

class ImageGenerationRequest(BaseModel):
    """Request model for OpenAI image generation endpoint."""
    prompt: str
    model: Optional[str] = "dall-e-3"
    n: Optional[int] = 1
    quality: Optional[str] = "standard"
    response_format: Optional[str] = "url"
    size: Optional[str] = "1024x1024"
    style: Optional[str] = "vivid"
    user: Optional[str] = None


# Add new response models for missing OpenAI endpoints
class EmbeddingData(BaseModel):
    """Individual embedding data."""
    object: str = "embedding"
    embedding: List[float]
    index: int

class EmbeddingUsage(BaseModel):
    """Usage information for embeddings."""
    prompt_tokens: int
    total_tokens: int

class EmbeddingResponse(BaseModel):
    """Response model for OpenAI embeddings endpoint."""
    object: str = "list"
    data: List[EmbeddingData]
    model: str
    usage: EmbeddingUsage

class AudioTranscriptionResponse(BaseModel):
    """Response model for OpenAI audio transcription endpoint."""
    text: str

class AudioTranslationResponse(BaseModel):
    """Response model for OpenAI audio translation endpoint."""
    text: str

class ImageData(BaseModel):
    """Individual image data."""
    url: Optional[str] = None
    b64_json: Optional[str] = None
    revised_prompt: Optional[str] = None

class ImageGenerationResponse(BaseModel):
    """Response model for OpenAI image generation endpoint."""
    created: int
    data: List[ImageData]
