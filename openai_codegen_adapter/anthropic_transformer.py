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
    Enhanced conversion of Anthropic request to prompt with full content block support.
    Handles text, images, and system instructions according to official API spec.
    """
    prompt_parts = []
    
    # Add system instruction if provided
    if request.system:
        prompt_parts.append(f"System: {request.system}")
    
    # Process messages with full content block support
    for message in request.messages:
        role = message.role.title()
        
        if isinstance(message.content, str):
            # Simple string content
            prompt_parts.append(f"{role}: {message.content}")
        elif isinstance(message.content, list):
            # Content blocks (text, images, etc.)
            content_parts = []
            for block in message.content:
                if block.type == "text" and block.text:
                    content_parts.append(block.text)
                elif block.type == "image" and block.source:
                    # Handle image content - for now, describe it
                    content_parts.append("[Image content provided]")
                # Add support for other content types as needed
            
            if content_parts:
                prompt_parts.append(f"{role}: {' '.join(content_parts)}")
    
    # Add generation parameters as context
    if request.temperature is not None and request.temperature != 1.0:
        prompt_parts.append(f"[Temperature: {request.temperature}]")
    
    if request.stop_sequences:
        prompt_parts.append(f"[Stop sequences: {', '.join(request.stop_sequences)}]")
    
    return "\n\n".join(prompt_parts)


def create_anthropic_response(
    content: str,
    model: str,
    prompt_tokens: int,
    completion_tokens: int,
    stop_reason: str = "end_turn",
    stop_sequence: str = None
) -> AnthropicResponse:
    """
    Enhanced creation of Anthropic response matching official API format.
    """
    from .models import AnthropicResponse, AnthropicResponseContent, AnthropicUsage
    
    return AnthropicResponse(
        content=[AnthropicResponseContent(type="text", text=content)],
        model=model,
        stop_reason=stop_reason,
        stop_sequence=stop_sequence,
        usage=AnthropicUsage(
            input_tokens=prompt_tokens,
            output_tokens=completion_tokens
        )
    )


def extract_anthropic_generation_params(request: AnthropicRequest) -> dict:
    """
    Enhanced extraction of generation parameters with full Anthropic API support.
    """
    params = {
        "stream": request.stream or False,
        "max_tokens": request.max_tokens,
        "model": request.model
    }
    
    if request.temperature is not None:
        params["temperature"] = request.temperature
    
    if request.top_p is not None:
        params["top_p"] = request.top_p
    
    if request.top_k is not None:
        params["top_k"] = request.top_k
    
    if request.stop_sequences:
        params["stop_sequences"] = request.stop_sequences
    
    if request.system:
        params["system"] = request.system
    
    if request.metadata:
        params["metadata"] = request.metadata
    
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
