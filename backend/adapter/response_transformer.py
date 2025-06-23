"""
Response transformation utilities to convert Codegen responses to OpenAI format.
Based on h2ogpt's backend.py response formatting patterns.
"""

import time
import uuid
from typing import Optional
from backend.adapter.models import (
    ChatResponse, ChatResponseStream, TextResponse,
    ChatChoice, ChatChoiceStream, TextChoice,
    Message, Usage
)


def create_chat_response(
    content: str,
    model: str,
    prompt_tokens: int,
    completion_tokens: int,
    finish_reason: str = "stop"
) -> ChatResponse:
    """
    Create a ChatResponse from Codegen output.
    Based on h2ogpt's achat_completion_action response format.
    
    Args:
        content: The generated content from Codegen
        model: Model name to return
        prompt_tokens: Number of tokens in the prompt
        completion_tokens: Number of tokens in the completion
        finish_reason: Reason for completion
        
    Returns:
        OpenAI-compatible ChatResponse
    """
    message = Message(role="assistant", content=content)
    choice = ChatChoice(
        index=0,
        message=message,
        finish_reason=finish_reason
    )
    usage = Usage(
        prompt_tokens=prompt_tokens,
        completion_tokens=completion_tokens,
        total_tokens=prompt_tokens + completion_tokens
    )
    
    return ChatResponse(
        model=model,
        choices=[choice],
        usage=usage
    )


def create_chat_stream_chunk(
    content: str,
    model: str,
    finish_reason: Optional[str] = None,
    request_id: Optional[str] = None
) -> ChatResponseStream:
    """
    Create a streaming chat response chunk.
    Based on h2ogpt's chat_streaming_chunk function.
    
    Args:
        content: The content chunk
        model: Model name
        finish_reason: Reason for completion (None for intermediate chunks)
        request_id: Request ID to maintain consistency
        
    Returns:
        OpenAI-compatible streaming response chunk
    """
    delta = Message(role="assistant", content=content)
    choice = ChatChoiceStream(
        index=0,
        delta=delta,
        finish_reason=finish_reason
    )
    
    response = ChatResponseStream(
        model=model,
        choices=[choice]
    )
    
    if request_id:
        response.id = request_id
    
    return response


def create_text_response(
    content: str,
    model: str,
    prompt_tokens: int,
    completion_tokens: int,
    finish_reason: str = "stop"
) -> TextResponse:
    """
    Create a TextResponse from Codegen output.
    Based on h2ogpt's acompletions_action response format.
    
    Args:
        content: The generated content from Codegen
        model: Model name to return
        prompt_tokens: Number of tokens in the prompt
        completion_tokens: Number of tokens in the completion
        finish_reason: Reason for completion
        
    Returns:
        OpenAI-compatible TextResponse
    """
    choice = TextChoice(
        index=0,
        text=content,
        finish_reason=finish_reason
    )
    usage = Usage(
        prompt_tokens=prompt_tokens,
        completion_tokens=completion_tokens,
        total_tokens=prompt_tokens + completion_tokens
    )
    
    return TextResponse(
        model=model,
        choices=[choice],
        usage=usage
    )


def format_sse_chunk(chunk: ChatResponseStream) -> str:
    """
    Format a streaming chunk as Server-Sent Event.
    Based on h2ogpt's streaming response format.
    
    Args:
        chunk: The streaming response chunk
        
    Returns:
        SSE-formatted string
    """
    import json
    return f"data: {json.dumps(chunk.dict())}\n\n"


def format_sse_done() -> str:
    """
    Format the final SSE chunk to indicate completion.
    
    Returns:
        SSE-formatted completion string
    """
    return "data: [DONE]\n\n"


def estimate_tokens(text: str) -> int:
    """
    Estimate token count for text.
    Simple approximation - in production you might want a proper tokenizer.
    
    Args:
        text: Text to count tokens for
        
    Returns:
        Estimated token count
    """
    # Simple approximation: ~4 characters per token
    return max(1, len(text) // 4)


def clean_content(content: str) -> str:
    """
    Clean and format content from Codegen response.
    
    Args:
        content: Raw content from Codegen
        
    Returns:
        Cleaned content suitable for OpenAI response
    """
    if not content:
        return ""
    
    # Remove any special markers that might be in Codegen responses
    content = content.replace('<FINISHED_ALL_TASKS>', '')
    content = content.replace('ENDOFTURN', '')
    
    # Strip extra whitespace
    content = content.strip()
    
    return content

