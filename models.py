"""
Data models for the unified API system.
"""

from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from enum import Enum


class MessageRole(str, Enum):
    """Message role in a chat conversation."""
    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"
    FUNCTION = "function"


class Message(BaseModel):
    """Message in a chat conversation."""
    role: MessageRole = Field(..., description="Role of the message sender")
    content: str = Field(..., description="Content of the message")
    name: Optional[str] = Field(None, description="Name of the sender (optional)")


class ChatRequest(BaseModel):
    """Request for chat completion."""
    model: str = Field(..., description="Model to use for completion")
    messages: List[Message] = Field(..., description="Messages in the conversation")
    max_tokens: Optional[int] = Field(None, description="Maximum number of tokens to generate")
    temperature: Optional[float] = Field(None, description="Sampling temperature")
    top_p: Optional[float] = Field(None, description="Nucleus sampling parameter")
    n: Optional[int] = Field(None, description="Number of completions to generate")
    stream: Optional[bool] = Field(None, description="Whether to stream the response")
    stop: Optional[List[str]] = Field(None, description="Sequences where the API will stop generating")
    presence_penalty: Optional[float] = Field(None, description="Presence penalty")
    frequency_penalty: Optional[float] = Field(None, description="Frequency penalty")
    logit_bias: Optional[Dict[str, float]] = Field(None, description="Logit bias")
    user: Optional[str] = Field(None, description="User identifier")


class ChatResponse(BaseModel):
    """Response from chat completion."""
    id: str = Field(..., description="Unique identifier for the completion")
    object: str = Field(..., description="Object type")
    created: int = Field(..., description="Unix timestamp of when the completion was created")
    model: str = Field(..., description="Model used for completion")
    choices: List[Dict[str, Any]] = Field(..., description="List of completion choices")
    usage: Dict[str, int] = Field(..., description="Token usage information")


class HealthResponse(BaseModel):
    """Response from health check endpoint."""
    status: str = Field(..., description="Health status (healthy or unhealthy)")
    timestamp: float = Field(..., description="Unix timestamp of when the health check was performed")
    providers: List[str] = Field(..., description="List of supported providers")


class ErrorResponse(BaseModel):
    """Error response."""
    error: str = Field(..., description="Error message")
    code: Optional[int] = Field(None, description="Error code")
    param: Optional[str] = Field(None, description="Parameter that caused the error")
    type: Optional[str] = Field(None, description="Error type")


class TestResult(BaseModel):
    """Result of a provider test."""
    provider: str = Field(..., description="Provider name")
    model: str = Field(..., description="Model used for test")
    success: bool = Field(..., description="Whether the test was successful")
    response: Optional[Any] = Field(None, description="Response from the provider")
    error: Optional[str] = Field(None, description="Error message if the test failed")
    processing_time: float = Field(..., description="Time taken to process the request")
    timestamp: float = Field(..., description="Unix timestamp of when the test was performed")

