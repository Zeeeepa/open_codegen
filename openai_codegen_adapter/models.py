"""
Pydantic models for OpenAI API compatibility.
Based on h2ogpt's server.py request/response models.
Enhanced with Anthropic Claude API compatibility.
"""

from typing import List, Optional, Dict, Any, Union, Literal
from pydantic import BaseModel, Field, field_validator
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
    
    @field_validator('input_tokens', 'output_tokens', mode='before')
    @classmethod
    def convert_float_to_int(cls, v):
        """Convert float values to integers for token counts"""
        if isinstance(v, float):
            return int(round(v))
        return v


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
    model: str  # Add missing model field
    contents: List[GeminiContent]
    generationConfig: Optional[GeminiGenerationConfig] = None
    systemInstruction: Optional[GeminiContent] = None
    stream: Optional[bool] = False


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
