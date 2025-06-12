"""
Gemini-specific transformers for request and response handling.
"""

from typing import Dict, Any, List, Optional
from .models import GeminiContent, GeminiCandidate, GeminiUsageMetadata, GeminiResponse


def gemini_request_to_prompt(request) -> str:
    """
    Convert Gemini request to prompt string.
    
    Args:
        request: Gemini API request
        
    Returns:
        Prompt string for Codegen
    """
    # Try to extract from messages
    if hasattr(request, 'messages') and request.messages:
        prompt_parts = []
        
        for message in request.messages:
            role = message.role
            content = message.content
            
            if role == "user":
                prompt_parts.append(f"Human: {content}")
            elif role == "model" or role == "assistant":
                prompt_parts.append(f"Assistant: {content}")
        
        # Add a prompt for the assistant to respond if the last message is from user
        if request.messages and request.messages[-1].role == "user":
            prompt_parts.append("Assistant:")
        
        return "\n\n".join(prompt_parts)
    
    # Try to extract from contents
    if hasattr(request, 'contents') and request.contents:
        prompt_parts = []
        
        for content in request.contents:
            role = content.role if hasattr(content, 'role') else None
            parts = content.parts if hasattr(content, 'parts') else []
            
            text_parts = []
            for part in parts:
                if 'text' in part:
                    text_parts.append(part['text'])
            
            combined_text = " ".join(text_parts)
            
            if role == "user":
                prompt_parts.append(f"Human: {combined_text}")
            elif role == "model" or role == "assistant":
                prompt_parts.append(f"Assistant: {combined_text}")
            else:
                prompt_parts.append(combined_text)
        
        return "\n\n".join(prompt_parts)
    
    # Fallback to direct prompt if available
    return getattr(request, 'prompt', "")


def extract_gemini_generation_params(request) -> Dict[str, Any]:
    """
    Extract generation parameters from Gemini request.
    
    Args:
        request: Gemini API request
        
    Returns:
        Dictionary of generation parameters
    """
    params = {}
    
    if hasattr(request, 'temperature') and request.temperature is not None:
        params['temperature'] = request.temperature
    
    if hasattr(request, 'max_output_tokens') and request.max_output_tokens is not None:
        params['max_tokens'] = request.max_output_tokens
    
    if hasattr(request, 'top_p') and request.top_p is not None:
        params['top_p'] = request.top_p
    
    if hasattr(request, 'top_k') and request.top_k is not None:
        params['top_k'] = request.top_k
    
    if hasattr(request, 'stream') and request.stream is not None:
        params['stream'] = request.stream
    
    return params


def create_gemini_response(
    content: str,
    prompt_tokens: int,
    completion_tokens: int
) -> GeminiResponse:
    """
    Create a Gemini-compatible response.
    
    Args:
        content: Generated content
        prompt_tokens: Number of prompt tokens
        completion_tokens: Number of completion tokens
        
    Returns:
        Gemini-compatible response
    """
    gemini_content = GeminiContent(
        role="model",
        parts=[{"text": content}]
    )
    
    candidate = GeminiCandidate(
        content=gemini_content,
        finishReason="STOP",
        index=0
    )
    
    usage_metadata = GeminiUsageMetadata(
        promptTokenCount=prompt_tokens,
        candidatesTokenCount=completion_tokens,
        totalTokenCount=prompt_tokens + completion_tokens
    )
    
    return GeminiResponse(
        candidates=[candidate],
        usageMetadata=usage_metadata
    )

