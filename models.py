"""
Simplified data models for the unified API system.
Contains only the essential models needed for the three providers.
"""

from typing import List, Dict, Any, Optional, Union
from pydantic import BaseModel
from enum import Enum


class MessageRole(str, Enum):
    """Message roles for chat completions."""
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


class ChatMessage(BaseModel):
    """A single chat message."""
    role: MessageRole
    content: str


class ChatRequest(BaseModel):
    """Unified chat completion request for all providers."""
    model: str
    messages: List[ChatMessage]
    max_tokens: Optional[int] = 150
    temperature: Optional[float] = 0.7
    stream: Optional[bool] = False


class ChatResponse(BaseModel):
    """Unified chat completion response."""
    id: str
    object: str = "chat.completion"
    created: int
    model: str
    choices: List[Dict[str, Any]]
    usage: Optional[Dict[str, int]] = None


class HealthResponse(BaseModel):
    """Health check response."""
    status: str
    timestamp: float
    providers: List[str]


class ErrorResponse(BaseModel):
    """Error response model."""
    error: str
    provider: Optional[str] = None
    timestamp: float


class TestResult(BaseModel):
    """Test result model."""
    provider: str
    model: str
    success: bool
    response: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    processing_time: float
    timestamp: float


# Provider-specific models (simplified)
class OpenAIRequest(ChatRequest):
    """OpenAI-specific request model."""
    pass


class AnthropicRequest(ChatRequest):
    """Anthropic-specific request model."""
    pass


class GoogleRequest(ChatRequest):
    """Google/Gemini-specific request model."""
    pass


# Model lists for each provider
OPENAI_MODELS = [
    "gpt-3.5-turbo",
    "gpt-4",
    "gpt-4-turbo"
]

ANTHROPIC_MODELS = [
    "claude-3-sonnet-20240229",
    "claude-3-opus-20240229",
    "claude-3-haiku-20240307"
]

GOOGLE_MODELS = [
    "gemini-1.5-pro",
    "gemini-1.5-flash",
    "gemini-pro"
]

ALL_MODELS = {
    "openai": OPENAI_MODELS,
    "anthropic": ANTHROPIC_MODELS,
    "google": GOOGLE_MODELS
}

