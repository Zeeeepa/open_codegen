"""
Request transformation utilities to convert OpenAI API requests to Codegen format.
Based on h2ogpt's backend_utils.py message conversion patterns.
"""

from typing import List
from backend.adapter.models import Message, ChatRequest, TextRequest
from backend.adapter.system_message_manager import get_system_message_manager


def messages_to_prompt(messages: List[Message]) -> str:
    """
    Convert OpenAI messages format to a single prompt string for Codegen.
    Based on h2ogpt's convert_messages_to_structure function.
    
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
            conversation_parts.append(f"User: {content}")
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


def extract_user_message(messages: List[Message]) -> str:
    """
    Extract the last user message for simple prompt-based requests.
    
    Args:
        messages: List of OpenAI format messages
        
    Returns:
        The last user message content
    """
    for message in reversed(messages):
        if message.role == "user":
            return message.content
    
    # Fallback to converting all messages
    return messages_to_prompt(messages)


def chat_request_to_prompt(request: ChatRequest) -> str:
    """
    Convert OpenAI chat request to a prompt string for Codegen SDK.
    Uses stored system message if available, falls back to default instruction.
    
    Args:
        request: ChatRequest object
        
    Returns:
        str: Formatted prompt string optimized for Codegen
    """
    prompt_parts = []
    
    # Get stored system message from manager
    manager = get_system_message_manager()
    stored_system_message = manager.get_system_message()
    
    # Default system instruction for fallback
    default_system_instruction = """You are an expert software engineer and coding assistant. When responding to coding questions:

1. Provide clear, well-commented code examples
2. Explain your reasoning and approach
3. Consider edge cases and best practices
4. Use appropriate design patterns when relevant
5. Provide complete, runnable code when possible
6. Include error handling where appropriate
7. Suggest improvements or alternatives when helpful

For non-coding questions, provide thorough, accurate, and helpful responses."""
    
    # Determine which system message to use
    system_instruction = stored_system_message if stored_system_message else default_system_instruction
    
    # Check if there's already a system message in the request
    has_system_message = any(msg.role == "system" for msg in request.messages)
    
    if not has_system_message:
        # No system message in request, use our configured one
        prompt_parts.append(f"System: {system_instruction}")
    
    # Process messages
    for message in request.messages:
        if message.role == "system":
            # If there's a stored system message, use it instead of the request's system message
            if stored_system_message:
                prompt_parts.append(f"System: {stored_system_message}")
            else:
                # Enhance existing system message with coding context
                enhanced_system = f"{message.content}\n\n{default_system_instruction}"
                prompt_parts.append(f"System: {enhanced_system}")
        elif message.role == "user":
            prompt_parts.append(f"Human: {message.content}")
        elif message.role == "assistant":
            prompt_parts.append(f"Assistant: {message.content}")
    
    # Add final assistant prompt
    if stored_system_message:
        # If we have a custom system message, use a simpler prompt
        prompt_parts.append("Assistant:")
    else:
        # Use enhanced instruction for default behavior
        prompt_parts.append("Assistant: I'll help you with that. Let me provide a comprehensive and well-structured response.")
    
    return "\n\n".join(prompt_parts)


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


def extract_generation_params(request) -> dict:
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
