"""
Z.ai streaming response handler for OpenAI API compatibility.
Handles streaming responses with proper error handling and format conversion.
"""

import json
import logging
import asyncio
from typing import AsyncGenerator, Optional
from fastapi import HTTPException
from fastapi.responses import StreamingResponse

from .zai_client import ZaiClient
from .zai_transformer import ZaiTransformer
from .models import ChatRequest, ZaiChatRequest
from .zai_exceptions import ZaiError, ZaiStreamingError

logger = logging.getLogger(__name__)


class ZaiStreamingHandler:
    """Handles Z.ai streaming responses with OpenAI compatibility."""
    
    def __init__(self, client: ZaiClient):
        """
        Initialize streaming handler.
        
        Args:
            client: Z.ai API client
        """
        self.client = client
        self.transformer = ZaiTransformer()
    
    async def stream_chat_completion(
        self, 
        openai_request: ChatRequest
    ) -> StreamingResponse:
        """
        Handle streaming chat completion request.
        
        Args:
            openai_request: OpenAI format request
            
        Returns:
            FastAPI StreamingResponse
            
        Raises:
            HTTPException: On errors
        """
        try:
            # Validate request
            self.transformer.validate_openai_request(openai_request)
            
            # Convert to Z.ai format
            zai_request = self.transformer.openai_to_zai_request(openai_request)
            zai_request.stream = True  # Ensure streaming is enabled
            
            # Create streaming response
            return StreamingResponse(
                self._generate_stream(zai_request, openai_request.model),
                media_type="text/plain",
                headers={
                    "Cache-Control": "no-cache",
                    "Connection": "keep-alive",
                    "Content-Type": "text/plain; charset=utf-8"
                }
            )
            
        except ZaiError as e:
            logger.error(f"Z.ai streaming error: {e}")
            raise HTTPException(
                status_code=e.status_code or 500,
                detail=self.transformer.create_error_response(e.message)
            )
        except Exception as e:
            logger.error(f"Unexpected streaming error: {e}")
            raise HTTPException(
                status_code=500,
                detail=self.transformer.create_error_response(
                    "Internal server error during streaming"
                )
            )
    
    async def _generate_stream(
        self, 
        zai_request: ZaiChatRequest, 
        original_model: str
    ) -> AsyncGenerator[str, None]:
        """
        Generate streaming response data.
        
        Args:
            zai_request: Z.ai format request
            original_model: Original OpenAI model name
            
        Yields:
            Server-sent events formatted strings
        """
        try:
            async for zai_chunk in self.client.chat_completion_stream(zai_request):
                # Convert Z.ai chunk to OpenAI format
                openai_chunk = self.transformer.zai_to_openai_stream_response(
                    zai_chunk, 
                    original_model
                )
                
                # Format as server-sent event
                chunk_json = openai_chunk.json(exclude_none=True)
                yield f"data: {chunk_json}\n\n"
            
            # Send completion marker
            yield "data: [DONE]\n\n"
            
        except ZaiStreamingError as e:
            logger.error(f"Z.ai streaming error: {e}")
            # Send error as final chunk
            error_response = self.transformer.create_error_response(e.message)
            yield f"data: {json.dumps(error_response)}\n\n"
            
        except Exception as e:
            logger.error(f"Unexpected error in stream generation: {e}")
            # Send error as final chunk
            error_response = self.transformer.create_error_response(
                "Stream generation failed"
            )
            yield f"data: {json.dumps(error_response)}\n\n"
    
    async def _handle_stream_error(self, error: Exception) -> str:
        """
        Handle streaming errors and return formatted error response.
        
        Args:
            error: Exception that occurred
            
        Returns:
            Formatted error response as SSE
        """
        if isinstance(error, ZaiError):
            error_response = self.transformer.create_error_response(error.message)
        else:
            error_response = self.transformer.create_error_response(
                "Streaming error occurred"
            )
        
        return f"data: {json.dumps(error_response)}\n\n"
    
    def _format_sse_chunk(self, data: dict) -> str:
        """
        Format data as Server-Sent Event.
        
        Args:
            data: Data to format
            
        Returns:
            SSE formatted string
        """
        return f"data: {json.dumps(data, ensure_ascii=False)}\n\n"
    
    async def close(self):
        """Close the streaming handler and cleanup resources."""
        if self.client:
            await self.client.close()


async def create_zai_streaming_response(
    openai_request: ChatRequest,
    zai_base_url: str = "https://z.ai/api/v1",
    timeout: int = 60
) -> StreamingResponse:
    """
    Create Z.ai streaming response for OpenAI request.
    
    Args:
        openai_request: OpenAI format request
        zai_base_url: Z.ai API base URL
        timeout: Request timeout
        
    Returns:
        FastAPI StreamingResponse
    """
    client = ZaiClient(base_url=zai_base_url, timeout=timeout)
    handler = ZaiStreamingHandler(client)
    
    try:
        return await handler.stream_chat_completion(openai_request)
    finally:
        # Ensure cleanup happens
        await handler.close()
