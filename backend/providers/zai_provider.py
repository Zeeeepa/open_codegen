"""
Z.ai Provider Integration for OpenAI Codegen Adapter

This module provides integration with Z.ai's GLM-4.5 and GLM-4.5V models,
supporting both streaming and non-streaming responses with proper authentication.
"""

import json
import asyncio
import aiohttp
from typing import Dict, Any, Optional, AsyncGenerator
import logging

logger = logging.getLogger(__name__)

class ZaiProvider:
    """Z.ai API provider with streaming support"""
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key
        self.base_url = "https://open.zai.chat/v1"
        self.models = {
            "glm-4.5": {
                "name": "GLM-4.5",
                "max_tokens": 8192,
                "supports_vision": False,
            },
            "glm-4.5v": {
                "name": "GLM-4.5V",
                "max_tokens": 8192,
                "supports_vision": True,
            }
        }
    
    def get_headers(self) -> Dict[str, str]:
        """Get headers for Z.ai API requests"""
        headers = {
            "Content-Type": "application/json",
            "User-Agent": "OpenAI-Codegen-Adapter/1.0.0",
        }
        
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        
        return headers
    
    async def chat_completion(
        self,
        messages: list,
        model: str = "glm-4.5",
        stream: bool = False,
        temperature: float = 0.7,
        max_tokens: int = 4096,
        **kwargs
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """
        Send chat completion request to Z.ai API
        
        Args:
            messages: List of message objects
            model: Model name (glm-4.5 or glm-4.5v)
            stream: Whether to stream the response
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate
            **kwargs: Additional parameters
        
        Yields:
            Response chunks for streaming, or single response for non-streaming
        """
        
        if model not in self.models:
            raise ValueError(f"Unsupported model: {model}. Available models: {list(self.models.keys())}")
        
        # Prepare request payload
        payload = {
            "model": model,
            "messages": messages,
            "stream": stream,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        
        # Add additional parameters
        for key, value in kwargs.items():
            if key not in ["messages", "model", "stream"]:
                payload[key] = value
        
        url = f"{self.base_url}/chat/completions"
        headers = self.get_headers()
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    url,
                    json=payload,
                    headers=headers,
                    timeout=aiohttp.ClientTimeout(total=60)
                ) as response:
                    
                    if response.status != 200:
                        error_text = await response.text()
                        logger.error(f"Z.ai API error {response.status}: {error_text}")
                        raise Exception(f"Z.ai API error: {response.status} - {error_text}")
                    
                    if stream:
                        # Handle streaming response
                        async for chunk in self._handle_streaming_response(response):
                            yield chunk
                    else:
                        # Handle non-streaming response
                        data = await response.json()
                        yield data
                        
        except aiohttp.ClientError as e:
            logger.error(f"Z.ai API connection error: {e}")
            raise Exception(f"Failed to connect to Z.ai API: {str(e)}")
        except Exception as e:
            logger.error(f"Z.ai API request failed: {e}")
            raise
    
    async def _handle_streaming_response(self, response) -> AsyncGenerator[Dict[str, Any], None]:
        """Handle streaming response from Z.ai API"""
        
        async for line in response.content:
            line = line.decode('utf-8').strip()
            
            if not line:
                continue
                
            if line.startswith('data: '):
                data = line[6:]  # Remove 'data: ' prefix
                
                if data == '[DONE]':
                    break
                
                try:
                    chunk = json.loads(data)
                    yield chunk
                except json.JSONDecodeError as e:
                    logger.warning(f"Failed to parse streaming chunk: {e}")
                    continue
    
    async def get_models(self) -> Dict[str, Any]:
        """Get available models from Z.ai"""
        return {
            "models": [
                {
                    "id": model_id,
                    "object": "model",
                    "created": 1677610602,
                    "owned_by": "zai",
                    "permission": [],
                    "root": model_id,
                    "parent": None,
                    **model_info
                }
                for model_id, model_info in self.models.items()
            ]
        }
    
    async def test_connection(self) -> Dict[str, Any]:
        """Test connection to Z.ai API"""
        try:
            test_messages = [
                {"role": "user", "content": "Hello, this is a test message."}
            ]
            
            async for response in self.chat_completion(
                messages=test_messages,
                model="glm-4.5",
                stream=False,
                max_tokens=10
            ):
                return {
                    "status": "success",
                    "message": "Z.ai API connection successful",
                    "model": "glm-4.5",
                    "response": response
                }
                
        except Exception as e:
            return {
                "status": "error",
                "message": f"Z.ai API connection failed: {str(e)}"
            }
    
    def format_messages_for_zai(self, messages: list) -> list:
        """Format messages for Z.ai API compatibility"""
        formatted_messages = []
        
        for message in messages:
            if isinstance(message, dict):
                # Standard OpenAI format
                formatted_messages.append({
                    "role": message.get("role", "user"),
                    "content": message.get("content", "")
                })
            else:
                # Handle other formats
                formatted_messages.append({
                    "role": "user",
                    "content": str(message)
                })
        
        return formatted_messages
    
    async def create_embedding(self, text: str, model: str = "text-embedding-ada-002") -> Dict[str, Any]:
        """
        Create embeddings using Z.ai API (if supported)
        Note: This is a placeholder - Z.ai may not support embeddings
        """
        raise NotImplementedError("Z.ai embeddings not yet implemented")
    
    def get_provider_info(self) -> Dict[str, Any]:
        """Get provider information"""
        return {
            "name": "Z.ai",
            "description": "Z.ai GLM-4.5 and GLM-4.5V models",
            "base_url": self.base_url,
            "models": self.models,
            "supports_streaming": True,
            "supports_vision": True,
            "supports_embeddings": False,
            "api_key_required": False,  # Z.ai may work without API key
        }


# Convenience functions for easy integration
async def create_zai_completion(
    messages: list,
    model: str = "glm-4.5",
    api_key: Optional[str] = None,
    **kwargs
) -> AsyncGenerator[Dict[str, Any], None]:
    """Create a Z.ai completion with default settings"""
    provider = ZaiProvider(api_key=api_key)
    async for response in provider.chat_completion(messages=messages, model=model, **kwargs):
        yield response


async def test_zai_connection(api_key: Optional[str] = None) -> Dict[str, Any]:
    """Test Z.ai API connection"""
    provider = ZaiProvider(api_key=api_key)
    return await provider.test_connection()


# Export main classes and functions
__all__ = [
    'ZaiProvider',
    'create_zai_completion',
    'test_zai_connection',
]

