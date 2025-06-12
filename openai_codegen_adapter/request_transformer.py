"""
Request transformation utilities to convert OpenAI API requests to Codegen format.
"""

from typing import List, Dict, Any, Union
from .models import Message, ChatRequest, TextRequest


def messages_to_prompt(messages: List[Message]) -> str:
    """
    Convert OpenAI messages format to a single prompt string for Codegen.
    
    Args:
        messages: List of OpenAI format messages
        
    Returns:
        Single prompt string combining all messages
    """
    system_message = ""
    conversation_parts = []
    
    for message in messages:
        role = message.role
        content = message.content
        
        if role == "system":
            system_message = content
        elif role == "user":
            conversation_parts.append(f"Human: {content}")
        elif role == "assistant":
            conversation_parts.append(f"Assistant: {content}")
        elif role == "tool":
            # Handle tool messages if needed
            conversation_parts.append(f"Tool: {content}")
    
    # Combine system message and conversation
    prompt_parts = []
    
    if system_message:
        prompt_parts.append(f"System: {system_message}")
    
    if conversation_parts:
        prompt_parts.extend(conversation_parts)
    
    # Add a prompt for the assistant to respond
    if conversation_parts and not conversation_parts[-1].startswith("Assistant:"):
        prompt_parts.append("Assistant:")
    
    return "\n\n".join(prompt_parts)


def extract_user_message(request_data: Dict[str, Any]) -> str:
    """
    Extract the user message from various request formats.
    
    Args:
        request_data: Request data dictionary
        
    Returns:
        The user message content
    """
    # Try to get from messages array (OpenAI format)
    if "messages" in request_data:
        messages = request_data["messages"]
        for message in reversed(messages):
            if message.get("role") == "user":
                return message.get("content", "")
    
    # Try to get from prompt field (older OpenAI format or Gemini)
    if "prompt" in request_data:
        prompt = request_data["prompt"]
        if isinstance(prompt, str):
            return prompt
        elif isinstance(prompt, list) and all(isinstance(p, str) for p in prompt):
            return "\n".join(prompt)
    
    # Try to get from contents (Gemini format)
    if "contents" in request_data:
        contents = request_data["contents"]
        for content in reversed(contents):
            if content.get("role") == "user":
                parts = content.get("parts", [])
                for part in parts:
                    if "text" in part:
                        return part["text"]
    
    # Fallback
    return ""


def chat_request_to_prompt(request: ChatRequest) -> str:
    """
    Convert OpenAI chat request to a prompt string for Codegen SDK.
    
    Args:
        request: ChatRequest object
        
    Returns:
        str: Formatted prompt string
    """
    return messages_to_prompt(request.messages)


def text_request_to_prompt(request: TextRequest) -> str:
    """
    Convert a TextRequest to a prompt string for Codegen.
    
    Args:
        request: OpenAI text completion request
        
    Returns:
        Prompt string for Codegen agent
    """
    if isinstance(request.prompt, str):
        return request.prompt
    elif isinstance(request.prompt, list):
        # If it's a list of strings, join them
        if all(isinstance(p, str) for p in request.prompt):
            return "\n".join(request.prompt)
        else:
            # If it's a list of token IDs, we can't handle that directly
            raise ValueError("Token ID prompts are not supported")
    else:
        raise ValueError(f"Unsupported prompt type: {type(request.prompt)}")


def extract_generation_params(request) -> Dict[str, Any]:
    """
    Extract generation parameters from OpenAI request.
    
    Args:
        request: OpenAI request (ChatRequest or TextRequest)
        
    Returns:
        Dictionary of parameters that could be used for generation control
    """
    params = {}
    
    if hasattr(request, 'temperature') and request.temperature is not None:
        params['temperature'] = request.temperature
    
    if hasattr(request, 'max_tokens') and request.max_tokens is not None:
        params['max_tokens'] = request.max_tokens
    
    if hasattr(request, 'top_p') and request.top_p is not None:
        params['top_p'] = request.top_p
    
    if hasattr(request, 'frequency_penalty') and request.frequency_penalty is not None:
        params['frequency_penalty'] = request.frequency_penalty
    
    if hasattr(request, 'presence_penalty') and request.presence_penalty is not None:
        params['presence_penalty'] = request.presence_penalty
    
    if hasattr(request, 'stop') and request.stop is not None:
        params['stop'] = request.stop
    
    return params


# Anthropic-specific transformers
def anthropic_request_to_prompt(request) -> str:
    """Convert Anthropic request to prompt string."""
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
        
        return "\n\n".join(prompt_parts)
    
    # Fallback to direct prompt if available
    return getattr(request, 'prompt', "")


def extract_anthropic_generation_params(request) -> Dict[str, Any]:
    """Extract generation parameters from Anthropic request."""
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
    
    return params


# Gemini-specific transformers
def gemini_request_to_prompt(request) -> str:
    """Convert Gemini request to prompt string."""
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

