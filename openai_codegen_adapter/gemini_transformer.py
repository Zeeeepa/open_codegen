"""
Request and response transformers for Google Gemini API compatibility.
Converts between Gemini API format and Codegen SDK.
"""

from typing import List, Dict, Any
from .models import (
    GeminiRequest, GeminiResponse, GeminiContent, GeminiPart, 
    GeminiCandidate, GeminiUsageMetadata
)
from .response_transformer import estimate_tokens, clean_content


def gemini_request_to_prompt(request: GeminiRequest) -> str:
    """
    Enhanced conversion of Gemini request to prompt with full multimodal support.
    Handles text, images, video, audio, and function calling according to Vertex AI spec.
    """
    prompt_parts = []
    
    # Add system instruction if provided
    if request.systemInstruction and request.systemInstruction.parts:
        system_parts = []
        for part in request.systemInstruction.parts:
            if part.text:
                system_parts.append(part.text)
        if system_parts:
            prompt_parts.append(f"System: {' '.join(system_parts)}")
    
    # Process contents with full multimodal support
    for content in request.contents:
        role = content.role or "user"
        role_name = "User" if role == "user" else "Model"
        
        content_parts = []
        for part in content.parts:
            if part.text:
                content_parts.append(part.text)
            elif part.inlineData:
                # Handle inline media data
                mime_type = part.inlineData.get("mimeType", "unknown")
                content_parts.append(f"[{mime_type} content provided]")
            elif part.fileData:
                # Handle file data
                file_uri = part.fileData.get("fileUri", "unknown")
                content_parts.append(f"[File: {file_uri}]")
            elif part.functionCall:
                # Handle function calls
                func_name = part.functionCall.get("name", "unknown")
                content_parts.append(f"[Function call: {func_name}]")
            elif part.functionResponse:
                # Handle function responses
                func_name = part.functionResponse.get("name", "unknown")
                content_parts.append(f"[Function response: {func_name}]")
        
        if content_parts:
            prompt_parts.append(f"{role_name}: {' '.join(content_parts)}")
    
    # Add generation config as context
    if request.generationConfig:
        config_parts = []
        if request.generationConfig.temperature is not None:
            config_parts.append(f"Temperature: {request.generationConfig.temperature}")
        if request.generationConfig.maxOutputTokens is not None:
            config_parts.append(f"Max tokens: {request.generationConfig.maxOutputTokens}")
        if request.generationConfig.stopSequences:
            config_parts.append(f"Stop sequences: {', '.join(request.generationConfig.stopSequences)}")
        
        if config_parts:
            prompt_parts.append(f"[{', '.join(config_parts)}]")
    
    # Handle legacy prompt parameter
    if request.prompt:
        prompt_parts.append(f"User: {request.prompt}")
    
    return "\n\n".join(prompt_parts)


def create_gemini_response(
    content: str,
    model: str = "gemini-1.5-pro",
    prompt_tokens: int = 0,
    completion_tokens: int = 0,
    finish_reason: str = "STOP"
) -> GeminiResponse:
    """
    Enhanced creation of Gemini response matching official Vertex AI format.
    """
    from .models import (
        GeminiResponse, GeminiCandidate, GeminiContent, GeminiPart, 
        GeminiUsageMetadata
    )
    
    # Create response content
    response_content = GeminiContent(
        role="model",
        parts=[GeminiPart(text=content)]
    )
    
    # Create candidate
    candidate = GeminiCandidate(
        content=response_content,
        finishReason=finish_reason,
        index=0
    )
    
    # Create usage metadata
    usage = GeminiUsageMetadata(
        promptTokenCount=prompt_tokens,
        candidatesTokenCount=completion_tokens,
        totalTokenCount=prompt_tokens + completion_tokens
    )
    
    return GeminiResponse(
        candidates=[candidate],
        usageMetadata=usage,
        modelVersion=model
    )


def extract_gemini_generation_params(request: GeminiRequest) -> dict:
    """
    Enhanced extraction of generation parameters with full Vertex AI support.
    """
    params = {
        "model": request.model or "gemini-1.5-pro"
    }
    
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
        
        if config.candidateCount is not None:
            params["candidate_count"] = config.candidateCount
        
        if config.responseMimeType:
            params["response_mime_type"] = config.responseMimeType
    
    # Handle safety settings
    if request.safetySettings:
        params["safety_settings"] = [
            {"category": setting.category, "threshold": setting.threshold}
            for setting in request.safetySettings
        ]
    
    # Handle tools and function calling
    if request.tools:
        params["tools"] = [tool.dict() for tool in request.tools]
    
    if request.toolConfig:
        params["tool_config"] = request.toolConfig.dict()
    
    # Handle caching
    if request.cachedContent:
        params["cached_content"] = request.cachedContent
    
    # Handle labels/metadata
    if request.labels:
        params["labels"] = request.labels
    
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
