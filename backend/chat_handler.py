"""
Multi-Provider Chat Handler for OpenAI Codegen Adapter

This module handles chat requests across multiple AI providers including
OpenAI, Anthropic, Gemini, Z.ai, and Codegen, with proper routing and
integration with the existing Codegen client.
"""

import asyncio
import json
import logging
from typing import Dict, Any, List, Optional, AsyncGenerator

from backend.adapter.codegen_client import CodegenClient
from backend.providers.zai_provider import ZaiProvider

logger = logging.getLogger(__name__)

class ChatHandler:
    """Handles multi-provider chat requests with Codegen integration"""
    
    def __init__(self, codegen_client: CodegenClient):
        self.codegen_client = codegen_client
        self.zai_provider = ZaiProvider()
        
        # Provider routing map
        self.providers = {
            "openai": self._handle_openai,
            "anthropic": self._handle_anthropic,
            "gemini": self._handle_gemini,
            "zai": self._handle_zai,
            "codegen": self._handle_codegen,
        }
    
    async def handle_chat(
        self,
        message: str,
        provider: str = "openai",
        model: str = "gpt-4",
        conversation_history: List[Dict[str, Any]] = None
    ) -> str:
        """
        Handle a chat request with the specified provider
        
        Args:
            message: The user message
            provider: AI provider to use
            model: Model name
            conversation_history: Previous conversation messages
            
        Returns:
            The AI response as a string
        """
        if conversation_history is None:
            conversation_history = []
        
        if provider not in self.providers:
            raise ValueError(f"Unsupported provider: {provider}")
        
        try:
            handler = self.providers[provider]
            response = await handler(message, model, conversation_history)
            return response
        except Exception as e:
            logger.error(f"Chat handler error for provider {provider}: {e}")
            raise
    
    async def handle_chat_stream(
        self,
        message: str,
        provider: str = "openai",
        model: str = "gpt-4",
        conversation_history: List[Dict[str, Any]] = None
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """
        Handle a streaming chat request
        
        Args:
            message: The user message
            provider: AI provider to use
            model: Model name
            conversation_history: Previous conversation messages
            
        Yields:
            Streaming response chunks
        """
        if conversation_history is None:
            conversation_history = []
        
        if provider not in self.providers:
            raise ValueError(f"Unsupported provider: {provider}")
        
        try:
            if provider == "zai":
                # Handle Z.ai streaming
                async for chunk in self._handle_zai_stream(message, model, conversation_history):
                    yield chunk
            else:
                # Handle other providers through Codegen client
                async for chunk in self._handle_codegen_stream(message, model, conversation_history, provider):
                    yield chunk
        except Exception as e:
            logger.error(f"Stream chat handler error for provider {provider}: {e}")
            yield {"error": str(e)}
    
    async def _handle_openai(self, message: str, model: str, conversation_history: List[Dict[str, Any]]) -> str:
        """Handle OpenAI requests through Codegen client"""
        try:
            # Format messages for OpenAI
            messages = self._format_conversation_history(conversation_history)
            messages.append({"role": "user", "content": message})
            
            # Use the existing Codegen client to handle OpenAI requests
            response_chunks = []
            
            # Create a task request for the Codegen client
            task_prompt = self._messages_to_prompt(messages)
            
            async for chunk in self.codegen_client.run_task(
                prompt=task_prompt,
                model=model,
                stream=False
            ):
                response_chunks.append(chunk)
            
            return "".join(response_chunks)
        except Exception as e:
            logger.error(f"OpenAI handler error: {e}")
            return f"Error processing OpenAI request: {str(e)}"
    
    async def _handle_anthropic(self, message: str, model: str, conversation_history: List[Dict[str, Any]]) -> str:
        """Handle Anthropic requests through Codegen client"""
        try:
            # Format messages for Anthropic
            messages = self._format_conversation_history(conversation_history)
            messages.append({"role": "user", "content": message})
            
            # Convert to prompt format for Codegen client
            task_prompt = self._messages_to_anthropic_prompt(messages)
            
            response_chunks = []
            async for chunk in self.codegen_client.run_task(
                prompt=task_prompt,
                model=model,
                stream=False
            ):
                response_chunks.append(chunk)
            
            return "".join(response_chunks)
        except Exception as e:
            logger.error(f"Anthropic handler error: {e}")
            return f"Error processing Anthropic request: {str(e)}"
    
    async def _handle_gemini(self, message: str, model: str, conversation_history: List[Dict[str, Any]]) -> str:
        """Handle Gemini requests through Codegen client"""
        try:
            # Format messages for Gemini
            messages = self._format_conversation_history(conversation_history)
            messages.append({"role": "user", "content": message})
            
            # Convert to prompt format for Codegen client
            task_prompt = self._messages_to_prompt(messages)
            
            response_chunks = []
            async for chunk in self.codegen_client.run_task(
                prompt=task_prompt,
                model=model,
                stream=False
            ):
                response_chunks.append(chunk)
            
            return "".join(response_chunks)
        except Exception as e:
            logger.error(f"Gemini handler error: {e}")
            return f"Error processing Gemini request: {str(e)}"
    
    async def _handle_zai(self, message: str, model: str, conversation_history: List[Dict[str, Any]]) -> str:
        """Handle Z.ai requests directly"""
        try:
            # Format messages for Z.ai
            messages = self._format_conversation_history(conversation_history)
            messages.append({"role": "user", "content": message})
            
            # Use Z.ai provider directly
            async for response in self.zai_provider.chat_completion(
                messages=messages,
                model=model,
                stream=False
            ):
                if "choices" in response and len(response["choices"]) > 0:
                    return response["choices"][0]["message"]["content"]
                return str(response)
            
            return "No response from Z.ai"
        except Exception as e:
            logger.error(f"Z.ai handler error: {e}")
            return f"Error processing Z.ai request: {str(e)}"
    
    async def _handle_codegen(self, message: str, model: str, conversation_history: List[Dict[str, Any]]) -> str:
        """Handle direct Codegen requests"""
        try:
            # Format messages for Codegen
            messages = self._format_conversation_history(conversation_history)
            messages.append({"role": "user", "content": message})
            
            # Convert to prompt format
            task_prompt = self._messages_to_prompt(messages)
            
            response_chunks = []
            async for chunk in self.codegen_client.run_task(
                prompt=task_prompt,
                model=model,
                stream=False
            ):
                response_chunks.append(chunk)
            
            return "".join(response_chunks)
        except Exception as e:
            logger.error(f"Codegen handler error: {e}")
            return f"Error processing Codegen request: {str(e)}"
    
    async def _handle_zai_stream(
        self,
        message: str,
        model: str,
        conversation_history: List[Dict[str, Any]]
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """Handle Z.ai streaming requests"""
        try:
            messages = self._format_conversation_history(conversation_history)
            messages.append({"role": "user", "content": message})
            
            async for chunk in self.zai_provider.chat_completion(
                messages=messages,
                model=model,
                stream=True
            ):
                yield chunk
        except Exception as e:
            logger.error(f"Z.ai stream handler error: {e}")
            yield {"error": str(e)}
    
    async def _handle_codegen_stream(
        self,
        message: str,
        model: str,
        conversation_history: List[Dict[str, Any]],
        provider: str
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """Handle streaming requests through Codegen client"""
        try:
            messages = self._format_conversation_history(conversation_history)
            messages.append({"role": "user", "content": message})
            
            # Convert to prompt format
            if provider == "anthropic":
                task_prompt = self._messages_to_anthropic_prompt(messages)
            else:
                task_prompt = self._messages_to_prompt(messages)
            
            # Stream through Codegen client
            async for chunk in self.codegen_client.run_task(
                prompt=task_prompt,
                model=model,
                stream=True
            ):
                # Format as OpenAI-compatible streaming response
                yield {
                    "choices": [{
                        "delta": {"content": chunk},
                        "index": 0,
                        "finish_reason": None
                    }]
                }
        except Exception as e:
            logger.error(f"Codegen stream handler error: {e}")
            yield {"error": str(e)}
    
    def _format_conversation_history(self, history: List[Dict[str, Any]]) -> List[Dict[str, str]]:
        """Format conversation history for API compatibility"""
        formatted = []
        for msg in history:
            if isinstance(msg, dict) and "role" in msg and "content" in msg:
                formatted.append({
                    "role": msg["role"],
                    "content": str(msg["content"])
                })
        return formatted
    
    def _messages_to_prompt(self, messages: List[Dict[str, str]]) -> str:
        """Convert messages to a single prompt string"""
        prompt_parts = []
        for msg in messages:
            role = msg.get("role", "user")
            content = msg.get("content", "")
            
            if role == "system":
                prompt_parts.append(f"System: {content}")
            elif role == "user":
                prompt_parts.append(f"User: {content}")
            elif role == "assistant":
                prompt_parts.append(f"Assistant: {content}")
        
        return "\n\n".join(prompt_parts)
    
    def _messages_to_anthropic_prompt(self, messages: List[Dict[str, str]]) -> str:
        """Convert messages to Anthropic-style prompt"""
        prompt_parts = []
        for msg in messages:
            role = msg.get("role", "user")
            content = msg.get("content", "")
            
            if role == "system":
                prompt_parts.append(f"System: {content}")
            elif role == "user":
                prompt_parts.append(f"Human: {content}")
            elif role == "assistant":
                prompt_parts.append(f"Assistant: {content}")
        
        # Add final Assistant prompt for Anthropic
        prompt = "\n\n".join(prompt_parts)
        if not prompt.endswith("Assistant:"):
            prompt += "\n\nAssistant:"
        
        return prompt
    
    async def test_provider(self, provider: str, api_key: Optional[str] = None) -> Dict[str, Any]:
        """Test a provider connection"""
        try:
            if provider == "zai":
                zai_provider = ZaiProvider(api_key=api_key)
                return await zai_provider.test_connection()
            else:
                # Test through Codegen client
                test_message = "Hello, this is a test message."
                response = await self._handle_provider_test(provider, test_message)
                return {
                    "status": "success",
                    "message": f"{provider} connection successful",
                    "response": response[:100] + "..." if len(response) > 100 else response
                }
        except Exception as e:
            return {
                "status": "error",
                "message": f"{provider} connection failed: {str(e)}"
            }
    
    async def _handle_provider_test(self, provider: str, message: str) -> str:
        """Handle provider test through appropriate handler"""
        if provider == "openai":
            return await self._handle_openai(message, "gpt-3.5-turbo", [])
        elif provider == "anthropic":
            return await self._handle_anthropic(message, "claude-3-sonnet", [])
        elif provider == "gemini":
            return await self._handle_gemini(message, "gemini-pro", [])
        elif provider == "codegen":
            return await self._handle_codegen(message, "codegen-standard", [])
        else:
            raise ValueError(f"Unknown provider: {provider}")


# Export main class
__all__ = ['ChatHandler']

