"""
Request and response transformers for Google Gemini API compatibility.
Converts between Gemini API format and Codegen SDK.
"""

from typing import List, Dict, Any
from backend.adapter.models import (
    GeminiRequest, GeminiResponse, GeminiContent, GeminiPart, 
    GeminiCandidate, GeminiUsageMetadata
)
from backend.adapter.response_transformer import estimate_tokens, clean_content


def gemini_request_to_prompt(request: GeminiRequest) -> str:
    """
    Convert Gemini API request to a prompt string for Codegen SDK.
    
    Args:
        request: GeminiRequest object
        
    Returns:
        str: Formatted prompt string
    """
    prompt_parts = []
    
    # Add system instruction if provided
    if request.systemInstruction:
        system_text = " ".join([part.text for part in request.systemInstruction.parts])
        prompt_parts.append(f"System: {system_text}")
    
    # Add conversation contents
    for content in request.contents:
        text = " ".join([part.text for part in content.parts])
        
        if content.role == "user":
            prompt_parts.append(f"Human: {text}")
        elif content.role == "model":
            prompt_parts.append(f"Assistant: {text}")
        else:
            # Default to user if role is not specified
            prompt_parts.append(f"Human: {text}")
    
    # Add final assistant prompt
    prompt_parts.append("Assistant:")
    
    return "\n\n".join(prompt_parts)


def create_gemini_response(
    content: str,
    prompt_tokens: int = None,
    completion_tokens: int = None
) -> GeminiResponse:
    """
    Create a Gemini API compatible response.
    
    Args:
        content: The response content
        prompt_tokens: Number of input tokens (estimated if not provided)
        completion_tokens: Number of output tokens (estimated if not provided)
        
    Returns:
        GeminiResponse: Formatted response
    """
    # Clean the content
    cleaned_content = clean_content(content)
    
    # Estimate tokens if not provided
    if completion_tokens is None:
        completion_tokens = estimate_tokens(cleaned_content)
    if prompt_tokens is None:
        prompt_tokens = 0  # We don't have the original prompt here
    
    # Create the response content
    response_content = GeminiContent(
        role="model",
        parts=[GeminiPart(text=cleaned_content)]
    )
    
    # Create the candidate
    candidate = GeminiCandidate(
        content=response_content,
        finishReason="STOP",
        index=0
    )
    
    # Create usage metadata
    usage_metadata = GeminiUsageMetadata(
        promptTokenCount=prompt_tokens,
        candidatesTokenCount=completion_tokens,
        totalTokenCount=prompt_tokens + completion_tokens
    )
    
    # Create the response
    response = GeminiResponse(
        candidates=[candidate],
        usageMetadata=usage_metadata,
        modelVersion="gemini-1.5-pro"
    )
    
    return response


def extract_gemini_generation_params(request: GeminiRequest) -> Dict[str, Any]:
    """
    Extract generation parameters from Gemini request.
    
    Args:
        request: GeminiRequest object
        
    Returns:
        Dict[str, Any]: Generation parameters
    """
    params = {}
    
    if request.generationConfig:
        config = request.generationConfig
        
        if config.temperature is not None:
            params["temperature"] = config.temperature
        if config.topP is not None:
            params["top_p"] = config.topP
        if config.topK is not None:
            params["top_k"] = config.topK
        if config.maxOutputTokens is not None:
            params["max_tokens"] = config.maxOutputTokens
        if config.stopSequences:
            params["stop_sequences"] = config.stopSequences
    
    return params


def create_gemini_stream_chunk(
    content: str,
    is_final: bool = False,
    prompt_tokens: int = 0,
    completion_tokens: int = 0
) -> Dict[str, Any]:
    """
    Create a Gemini streaming chunk.
    
    Args:
        content: Content for the chunk
        is_final: Whether this is the final chunk
        prompt_tokens: Number of input tokens
        completion_tokens: Number of output tokens
        
    Returns:
        Dict[str, Any]: Streaming chunk data
    """
    # Create the response content
    response_content = GeminiContent(
        role="model",
        parts=[GeminiPart(text=content)]
    )
    
    # Create the candidate
    candidate = GeminiCandidate(
        content=response_content,
        finishReason="STOP" if is_final else None,
        index=0
    )
    
    chunk = {
        "candidates": [candidate.dict()]
    }
    
    # Add usage metadata for final chunk
    if is_final:
        chunk["usageMetadata"] = {
            "promptTokenCount": prompt_tokens,
            "candidatesTokenCount": completion_tokens,
            "totalTokenCount": prompt_tokens + completion_tokens
        }
    
    return chunk

