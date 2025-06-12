"""
Pydantic models for OpenAI, Anthropic, and Google API compatibility.
"""

from typing import List, Optional, Union, Dict, Any
from pydantic import BaseModel, Field


class Message(BaseModel):
    """Message in a conversation."""
    role: str
    content: str


class ChatRequest(BaseModel):
    """OpenAI chat completion request."""
    model: str
    messages: List[Message]
    temperature: Optional[float] = None
    top_p: Optional[float] = None
    n: Optional[int] = 1
    stream: Optional[bool] = False
    stop: Optional[Union[str, List[str]]] = None
    max_tokens: Optional[int] = None
    presence_penalty: Optional[float] = None
    frequency_penalty: Optional[float] = None
    logit_bias: Optional[Dict[str, float]] = None
    user: Optional[str] = None


class TextRequest(BaseModel):
    """OpenAI text completion request."""
    model: str
    prompt: Union[str, List[str], List[int]]
    temperature: Optional[float] = None
    top_p: Optional[float] = None
    n: Optional[int] = 1
    stream: Optional[bool] = False
    stop: Optional[Union[str, List[str]]] = None
    max_tokens: Optional[int] = None
    presence_penalty: Optional[float] = None
    frequency_penalty: Optional[float] = None
    logit_bias: Optional[Dict[str, float]] = None
    user: Optional[str] = None


class ChatChoice(BaseModel):
    """Choice in a chat completion response."""
    index: int
    message: Message
    finish_reason: Optional[str] = None


class ChatChoiceStream(BaseModel):
    """Choice in a streaming chat completion response."""
    index: int
    delta: Message
    finish_reason: Optional[str] = None


class TextChoice(BaseModel):
    """Choice in a text completion response."""
    index: int
    text: str
    finish_reason: Optional[str] = None


class Usage(BaseModel):
    """Token usage information."""
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int


class ChatResponse(BaseModel):
    """OpenAI chat completion response."""
    id: str = Field(default_factory=lambda: f"chatcmpl-{int(time.time())}")
    object: str = "chat.completion"
    created: int = Field(default_factory=lambda: int(time.time()))
    model: str
    choices: List[ChatChoice]
    usage: Usage


class ChatResponseStream(BaseModel):
    """OpenAI streaming chat completion response."""
    id: str = Field(default_factory=lambda: f"chatcmpl-{int(time.time())}")
    object: str = "chat.completion.chunk"
    created: int = Field(default_factory=lambda: int(time.time()))
    model: str
    choices: List[ChatChoiceStream]


class TextResponse(BaseModel):
    """OpenAI text completion response."""
    id: str = Field(default_factory=lambda: f"cmpl-{int(time.time())}")
    object: str = "text_completion"
    created: int = Field(default_factory=lambda: int(time.time()))
    model: str
    choices: List[TextChoice]
    usage: Usage


class ErrorDetail(BaseModel):
    """Error details for API responses."""
    message: str
    type: str
    code: str


class ErrorResponse(BaseModel):
    """Error response format."""
    error: ErrorDetail


# Anthropic Models
class AnthropicRequest(BaseModel):
    """Anthropic Claude API request."""
    model: str
    messages: List[Message]
    max_tokens: Optional[int] = None
    temperature: Optional[float] = None
    top_p: Optional[float] = None
    top_k: Optional[int] = None
    stream: Optional[bool] = False
    stop_sequences: Optional[List[str]] = None
    system: Optional[str] = None


class AnthropicContentBlock(BaseModel):
    """Content block in Anthropic response."""
    type: str = "text"
    text: str


class AnthropicResponse(BaseModel):
    """Anthropic Claude API response."""
    id: str = Field(default_factory=lambda: f"msg_{int(time.time())}")
    type: str = "message"
    role: str = "assistant"
    content: List[AnthropicContentBlock]
    model: str
    stop_reason: Optional[str] = "end_turn"
    usage: Optional[Dict[str, int]] = None


# Google/Gemini Models
class GeminiContent(BaseModel):
    """Content for Gemini request/response."""
    role: Optional[str] = None
    parts: List[Dict[str, Any]]


class GeminiRequest(BaseModel):
    """Google Gemini API request."""
    model: str
    messages: Optional[List[Message]] = None
    contents: Optional[List[GeminiContent]] = None
    temperature: Optional[float] = None
    top_p: Optional[float] = None
    top_k: Optional[int] = None
    stream: Optional[bool] = False
    max_output_tokens: Optional[int] = None
    prompt: Optional[str] = None  # For backward compatibility


class GeminiCandidate(BaseModel):
    """Candidate in Gemini response."""
    content: GeminiContent
    finishReason: str = "STOP"
    index: int = 0


class GeminiUsageMetadata(BaseModel):
    """Token usage for Gemini."""
    promptTokenCount: int
    candidatesTokenCount: int
    totalTokenCount: int


class GeminiResponse(BaseModel):
    """Google Gemini API response."""
    candidates: List[GeminiCandidate]
    usageMetadata: Optional[GeminiUsageMetadata] = None


# Import time at the end to avoid circular imports
import time

