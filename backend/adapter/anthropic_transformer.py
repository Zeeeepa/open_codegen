"""
Request and response transformers for Anthropic Claude API compatibility.
Converts between Anthropic API format and Codegen SDK.
Enhanced with comprehensive content block and tool support.
"""

from typing import Dict, Any
from backend.adapter.models import (
    AnthropicRequest, AnthropicResponse, AnthropicUsage, ContentBlockText
)
from backend.adapter.response_transformer import estimate_tokens, clean_content
import uuid
import json
import logging

logger = logging.getLogger(__name__)


def parse_tool_result_content(content):
    """Helper function to properly parse and normalize tool result content."""
    if content is None:
        return "No content provided"
        
    if isinstance(content, str):
        return content
        
    if isinstance(content, list):
        result = ""
        for item in content:
            if isinstance(item, dict) and item.get("type") == "text":
                result += item.get("text", "") + "\n"
            elif isinstance(item, str):
                result += item + "\n"
            elif isinstance(item, dict):
                if "text" in item:
                    result += item.get("text", "") + "\n"
                else:
                    try:
                        result += json.dumps(item) + "\n"
                    except (TypeError, ValueError):
                        result += str(item) + "\n"
            else:
                try:
                    result += str(item) + "\n"
                except (TypeError, ValueError):
                    result += "Unparseable content\n"
        return result.strip()
        
    if isinstance(content, dict):
        if content.get("type") == "text":
            return content.get("text", "")
        try:
            return json.dumps(content)
        except (TypeError, ValueError):
            return str(content)
            
    # Fallback for any other type
    try:
        return str(content)
    except (TypeError, ValueError):
        return "Unparseable content"


def anthropic_request_to_prompt(request: AnthropicRequest) -> str:
    """
    Convert Anthropic API request to a prompt string for Codegen SDK.
    Enhanced to handle complex content blocks, tools, and system messages.
    
    Args:
        request: AnthropicRequest object
        
    Returns:
        str: Formatted prompt string
    """
    prompt_parts = []
    
    # Add system message if provided
    if request.system:
        # Handle different formats of system messages
        if isinstance(request.system, str):
            prompt_parts.append(f"System: {request.system}")
        elif isinstance(request.system, list):
            system_text = ""
            for block in request.system:
                if hasattr(block, 'type') and block.type == "text":
                    system_text += block.text + "\n\n"
                elif isinstance(block, dict) and block.get("type") == "text":
                    system_text += block.get("text", "") + "\n\n"
            
            if system_text:
                prompt_parts.append(f"System: {system_text.strip()}")
    
    # Add conversation messages
    for message in request.messages:
        content = message.content
        if isinstance(content, str):
            # Simple string content
            if message.role == "user":
                prompt_parts.append(f"Human: {content}")
            elif message.role == "assistant":
                prompt_parts.append(f"Assistant: {content}")
        else:
            # Complex content blocks
            message_content = ""
            
            for block in content:
                if hasattr(block, "type"):
                    if block.type == "text":
                        message_content += block.text + "\n"
                    elif block.type == "tool_use":
                        # Format tool use
                        tool_input = json.dumps(block.input) if isinstance(block.input, dict) else str(block.input)
                        message_content += f"[Tool: {block.name} (ID: {block.id})]\nInput: {tool_input}\n\n"
                    elif block.type == "tool_result":
                        # Format tool result
                        tool_id = block.tool_use_id if hasattr(block, "tool_use_id") else ""
                        result_content = parse_tool_result_content(block.content)
                        message_content += f"[Tool Result ID: {tool_id}]\n{result_content}\n\n"
                    elif block.type == "image":
                        message_content += "[Image content - not displayed in text format]\n"
            
            if message.role == "user":
                prompt_parts.append(f"Human: {message_content.strip()}")
            elif message.role == "assistant":
                prompt_parts.append(f"Assistant: {message_content.strip()}")
    
    # Add final assistant prompt
    prompt_parts.append("Assistant:")
    
    return "\n\n".join(prompt_parts)


def create_anthropic_response(
    content: str,
    model: str,
    input_tokens: int = None,
    output_tokens: int = None,
    request_id: str = None
) -> AnthropicResponse:
    """
    Create an Anthropic API compatible response.
    Enhanced to match the exact Anthropic API format.
    
    Args:
        content: The response content
        model: Model name used
        input_tokens: Number of input tokens (estimated if not provided)
        output_tokens: Number of output tokens (estimated if not provided)
        request_id: Optional request ID
        
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
    
    # Create content blocks
    content_blocks = []
    if cleaned_content:
        content_blocks.append(ContentBlockText(type="text", text=cleaned_content))
    
    # Create the response
    response = AnthropicResponse(
        id=request_id or f"msg_{uuid.uuid4().hex[:29]}",
        model=model,
        content=content_blocks,
        stop_reason="end_turn",
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
