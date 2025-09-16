"""
Z.ai request/response transformer for OpenAI API compatibility.
Converts between OpenAI format and Z.ai format following KISS principles.
"""

import time
import uuid
import logging
from typing import Dict, Any, List

from .models import (
    ChatRequest, ChatResponse, ChatResponseStream,
    Message, ChatChoice, ChatChoiceStream, Usage,
    ZaiChatRequest, ZaiChatResponse, ZaiStreamResponse,
    ZaiMessage, ZaiChoice, ZaiUsage
)
from .zai_exceptions import ZaiValidationError

logger = logging.getLogger(__name__)


class ZaiTransformer:
    """Transforms requests/responses between OpenAI and Z.ai formats."""
    
    # Model mapping from OpenAI to Z.ai
    MODEL_MAPPING = {
        "gpt-3.5-turbo": "glm-4.5",
        "gpt-4": "glm-4.5",
        "gpt-4-turbo": "glm-4.5",
        "gpt-4o": "glm-4.5v",
        "gpt-4-vision-preview": "glm-4.5v",
        "gpt-4-turbo-preview": "glm-4.5"
    }
    
    @classmethod
    def openai_to_zai_request(cls, openai_request: ChatRequest) -> ZaiChatRequest:
        """
        Convert OpenAI chat request to Z.ai format.
        
        Args:
            openai_request: OpenAI format request
            
        Returns:
            Z.ai format request
            
        Raises:
            ZaiValidationError: On validation failures
        """
        try:
            # Map model name
            zai_model = cls.MODEL_MAPPING.get(
                openai_request.model, 
                "glm-4.5"  # Default fallback
            )
            
            # Convert messages
            zai_messages = []
            for msg in openai_request.messages:
                if msg.role not in ["user", "assistant", "system"]:
                    logger.warning(f"Unsupported role '{msg.role}', converting to 'user'")
                    role = "user"
                else:
                    role = msg.role
                
                zai_messages.append(ZaiMessage(
                    role=role,
                    content=msg.content
                ))
            
            # Create Z.ai request
            zai_request = ZaiChatRequest(
                model=zai_model,
                messages=zai_messages,
                temperature=openai_request.temperature,
                max_tokens=openai_request.max_tokens,
                stream=openai_request.stream
            )
            
            return zai_request
            
        except Exception as e:
            raise ZaiValidationError(f"Failed to convert OpenAI request: {str(e)}")
    
    @classmethod
    def zai_to_openai_response(
        cls, 
        zai_response: ZaiChatResponse, 
        original_model: str
    ) -> ChatResponse:
        """
        Convert Z.ai response to OpenAI format.
        
        Args:
            zai_response: Z.ai format response
            original_model: Original OpenAI model name requested
            
        Returns:
            OpenAI format response
        """
        # Convert choices
        openai_choices = []
        for choice in zai_response.choices:
            openai_message = Message(
                role=choice.message.role,
                content=choice.message.content
            )
            
            openai_choice = ChatChoice(
                index=choice.index,
                message=openai_message,
                finish_reason=choice.finish_reason
            )
            openai_choices.append(openai_choice)
        
        # Convert usage
        openai_usage = Usage(
            prompt_tokens=zai_response.usage.prompt_tokens,
            completion_tokens=zai_response.usage.completion_tokens,
            total_tokens=zai_response.usage.total_tokens
        )
        
        # Create OpenAI response
        return ChatResponse(
            id=zai_response.id,
            model=original_model,  # Return original model name
            choices=openai_choices,
            usage=openai_usage
        )
    
    @classmethod
    def zai_to_openai_stream_response(
        cls, 
        zai_stream: ZaiStreamResponse, 
        original_model: str
    ) -> ChatResponseStream:
        """
        Convert Z.ai streaming response to OpenAI format.
        
        Args:
            zai_stream: Z.ai streaming response
            original_model: Original OpenAI model name requested
            
        Returns:
            OpenAI streaming response
        """
        # Convert streaming choices
        openai_choices = []
        for choice in zai_stream.choices:
            # Convert delta
            delta = {}
            if 'role' in choice.delta:
                delta['role'] = choice.delta['role']
            if 'content' in choice.delta:
                delta['content'] = choice.delta['content']
            
            openai_choice = ChatChoiceStream(
                index=choice.index,
                delta=delta,
                finish_reason=choice.finish_reason
            )
            openai_choices.append(openai_choice)
        
        return ChatResponseStream(
            id=zai_stream.id,
            model=original_model,  # Return original model name
            choices=openai_choices
        )
    
    @classmethod
    def create_error_response(cls, error_message: str, error_type: str = "api_error") -> Dict[str, Any]:
        """
        Create OpenAI-compatible error response.
        
        Args:
            error_message: Error message
            error_type: Error type
            
        Returns:
            OpenAI error response format
        """
        return {
            "error": {
                "message": error_message,
                "type": error_type,
                "param": None,
                "code": None
            }
        }
    
    @classmethod
    def validate_openai_request(cls, request: ChatRequest) -> None:
        """
        Validate OpenAI request for Z.ai compatibility.
        
        Args:
            request: OpenAI chat request
            
        Raises:
            ZaiValidationError: On validation failures
        """
        # Check if messages exist
        if not request.messages:
            raise ZaiValidationError("Messages cannot be empty")
        
        # Check message content
        for i, msg in enumerate(request.messages):
            if not msg.content or not msg.content.strip():
                raise ZaiValidationError(f"Message {i} content cannot be empty")
        
        # Check temperature range (Z.ai uses 0.0-1.0)
        if request.temperature is not None and request.temperature > 1.0:
            logger.warning(f"Temperature {request.temperature} > 1.0, clamping to 1.0 for Z.ai")
        
        # Check max_tokens
        if request.max_tokens is not None and request.max_tokens <= 0:
            raise ZaiValidationError("max_tokens must be positive")
    
    @classmethod
    def get_supported_models(cls) -> List[str]:
        """Get list of supported OpenAI model names."""
        return list(cls.MODEL_MAPPING.keys())
    
    @classmethod
    def is_model_supported(cls, model: str) -> bool:
        """Check if OpenAI model is supported by Z.ai."""
        return model in cls.MODEL_MAPPING
