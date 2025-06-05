"""
Request and response transformers for Anthropic Claude API compatibility.
Converts between Anthropic API format and Codegen SDK.
"""

from typing import List, Dict, Any
from .models import AnthropicRequest, AnthropicResponse, AnthropicUsage, AnthropicMessage
from .response_transformer import estimate_tokens, clean_content
import uuid


def anthropic_request_to_prompt(request: AnthropicRequest) -> str:
    """
    Convert Anthropic API request to a prompt string for Codegen SDK.
    
    Args:
        request: AnthropicRequest object
        
    Returns:
        str: Formatted prompt string
    """
    prompt_parts = []
    
    # Add system message if provided
    if request.system:
        prompt_parts.append(f"System: {request.system}")
    
    # Add conversation messages
    for message in request.messages:
        if message.role == "user":
            prompt_parts.append(f"Human: {message.content}")
        elif message.role == "assistant":
            prompt_parts.append(f"Assistant: {message.content}")
    
    # Add final assistant prompt
    prompt_parts.append("Assistant:")
    
    return "\n\n".join(prompt_parts)


def create_anthropic_response(
    content: str,
    model: str,
    input_tokens: int = None,
    output_tokens: int = None
) -> AnthropicResponse:
    """
    Create an Anthropic API compatible response.
    
    Args:
        content: The response content
        model: Model name used
        input_tokens: Number of input tokens (estimated if not provided)
        output_tokens: Number of output tokens (estimated if not provided)
        
    Returns:
        AnthropicResponse: Formatted response
    """
    # Clean the content
    cleaned_content = clean_content(content)
    
    # Estimate tokens if not provided
    if output_tokens is None:
        output_tokens = estimate_tokens(cleaned_content)
    if input_tokens is None:
        input_tokens = 0  # We don't have the original prompt here
    
    # Create the response
    response = AnthropicResponse(
        model=model,
        content=[{"type": "text", "text": cleaned_content}],
        usage=AnthropicUsage(
            input_tokens=input_tokens,
            output_tokens=output_tokens
        )
    )
    
    return response


def extract_anthropic_generation_params(request: AnthropicRequest) -> Dict[str, Any]:
    """
    Extract generation parameters from Anthropic request.
    
    Args:
        request: AnthropicRequest object
        
    Returns:
        Dict[str, Any]: Generation parameters
    """
    params = {}
    
    if request.temperature is not None:
        params["temperature"] = request.temperature
    if request.max_tokens is not None:
        params["max_tokens"] = request.max_tokens
    if request.top_p is not None:
        params["top_p"] = request.top_p
    if request.top_k is not None:
        params["top_k"] = request.top_k
    if request.stop_sequences:
        params["stop_sequences"] = request.stop_sequences
    
    return params


def create_anthropic_stream_event(
    event_type: str,
    content: str = None,
    model: str = None,
    usage: AnthropicUsage = None
) -> Dict[str, Any]:
    """
    Create an Anthropic streaming event.
    
    Args:
        event_type: Type of the event
        content: Content for the event (if applicable)
        model: Model name (if applicable)
        usage: Usage information (if applicable)
        
    Returns:
        Dict[str, Any]: Streaming event data
    """
    event = {"type": event_type}
    
    if event_type == "message_start":
        event["message"] = {
            "id": f"msg_{uuid.uuid4().hex[:29]}",
            "type": "message",
            "role": "assistant",
            "content": [],
            "model": model or "claude-3-sonnet-20240229",
            "stop_reason": None,
            "stop_sequence": None,
            "usage": {"input_tokens": 0, "output_tokens": 0}
        }
    elif event_type == "content_block_start":
        event["index"] = 0
        event["content_block"] = {"type": "text", "text": ""}
    elif event_type == "content_block_delta":
        event["index"] = 0
        event["delta"] = {"type": "text_delta", "text": content or ""}
    elif event_type == "content_block_stop":
        event["index"] = 0
    elif event_type == "message_delta":
        event["delta"] = {"stop_reason": "end_turn", "stop_sequence": None}
        if usage:
            event["usage"] = {"output_tokens": usage.output_tokens}
    elif event_type == "message_stop":
        pass  # No additional data needed
    
    return event

