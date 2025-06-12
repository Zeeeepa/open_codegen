"""
Anthropic-specific transformers for request and response handling.
"""

from typing import Dict, Any, List, Optional
from .models import Message, AnthropicContentBlock, AnthropicResponse


def anthropic_request_to_prompt(request) -> str:
    """
    Convert Anthropic request to prompt string.
    
    Args:
        request: Anthropic API request
        
    Returns:
        Prompt string for Codegen
    """
    if hasattr(request, 'messages'):
        # Convert messages to a format Codegen understands
        system_content = getattr(request, 'system', None)
        messages = request.messages
        
        prompt_parts = []
        
        if system_content:
            prompt_parts.append(f"System: {system_content}")
        
        for message in messages:
            role = message.role
            content = message.content
            
            if role == "user":
                prompt_parts.append(f"Human: {content}")
            elif role == "assistant":
                prompt_parts.append(f"Assistant: {content}")
        
        # Add a prompt for the assistant to respond if the last message is from user
        if messages and messages[-1].role == "user":
            prompt_parts.append("Assistant:")
        
        return "\n\n".join(prompt_parts)
    
    # Fallback to direct prompt if available
    return getattr(request, 'prompt', "")


def extract_anthropic_generation_params(request) -> Dict[str, Any]:
    """
    Extract generation parameters from Anthropic request.
    
    Args:
        request: Anthropic API request
        
    Returns:
        Dictionary of generation parameters
    """
    params = {}
    
    if hasattr(request, 'temperature') and request.temperature is not None:
        params['temperature'] = request.temperature
    
    if hasattr(request, 'max_tokens') and request.max_tokens is not None:
        params['max_tokens'] = request.max_tokens
    
    if hasattr(request, 'top_p') and request.top_p is not None:
        params['top_p'] = request.top_p
    
    if hasattr(request, 'top_k') and request.top_k is not None:
        params['top_k'] = request.top_k
    
    if hasattr(request, 'stop_sequences') and request.stop_sequences is not None:
        params['stop'] = request.stop_sequences
    
    if hasattr(request, 'stream') and request.stream is not None:
        params['stream'] = request.stream
    
    return params


def create_anthropic_response(
    content: str,
    model: str,
    input_tokens: int,
    output_tokens: int,
    stop_reason: str = "end_turn"
) -> AnthropicResponse:
    """
    Create an Anthropic-compatible response.
    
    Args:
        content: Generated content
        model: Model name
        input_tokens: Number of input tokens
        output_tokens: Number of output tokens
        stop_reason: Reason for stopping
        
    Returns:
        Anthropic-compatible response
    """
    content_block = AnthropicContentBlock(type="text", text=content)
    
    usage = {
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
        "total_tokens": input_tokens + output_tokens
    }
    
    return AnthropicResponse(
        model=model,
        content=[content_block],
        stop_reason=stop_reason,
        usage=usage
    )

