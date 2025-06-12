"""
Streaming response utilities for Server-Sent Events.
"""

import asyncio
import json
import logging
import time
from typing import AsyncGenerator
from fastapi.responses import StreamingResponse
from .models import ChatResponseStream
from .response_transformer import (
    create_chat_stream_chunk, format_sse_chunk, format_sse_done,
    clean_content, estimate_tokens
)
from .codegen_client import CodegenClient

logger = logging.getLogger(__name__)


async def stream_chat_response(
    client: CodegenClient,
    prompt: str,
    model: str,
    request_id: str
) -> AsyncGenerator[str, None]:
    """
    Stream chat completion response as Server-Sent Events.
    
    Args:
        client: Codegen client instance
        prompt: The prompt to send to Codegen
        model: Model name for response
        request_id: Request ID for consistency
        
    Yields:
        SSE-formatted response chunks
    """
    try:
        # Send initial empty chunk to start the stream
        initial_chunk = create_chat_stream_chunk("", model, request_id=request_id)
        yield format_sse_chunk(initial_chunk)
        
        # Stream the actual response
        accumulated_content = ""
        async for content_chunk in client.run_task(prompt, stream=True):
            if content_chunk:
                cleaned_chunk = clean_content(content_chunk)
                if cleaned_chunk:
                    # For streaming, we send the incremental content
                    chunk = create_chat_stream_chunk(
                        cleaned_chunk, 
                        model, 
                        request_id=request_id
                    )
                    yield format_sse_chunk(chunk)
                    accumulated_content += cleaned_chunk
                    
                    # Small delay to prevent overwhelming the client
                    await asyncio.sleep(0.01)
        
        # Send final chunk with finish_reason
        final_chunk = create_chat_stream_chunk(
            "", 
            model, 
            finish_reason="stop",
            request_id=request_id
        )
        yield format_sse_chunk(final_chunk)
        
        # Send completion marker
        yield format_sse_done()
        
    except Exception as e:
        logger.error(f"Error in streaming response: {e}")
        # Send error chunk
        error_chunk = create_chat_stream_chunk(
            f"Error: {str(e)}", 
            model, 
            finish_reason="error",
            request_id=request_id
        )
        yield format_sse_chunk(error_chunk)
        yield format_sse_done()


def create_streaming_response(
    client: CodegenClient,
    prompt: str,
    model: str,
    request_id: str
) -> StreamingResponse:
    """
    Create a FastAPI StreamingResponse for chat completion.
    
    Args:
        client: Codegen client instance
        prompt: The prompt to send to Codegen
        model: Model name for response
        request_id: Request ID for consistency
        
    Returns:
        FastAPI StreamingResponse with SSE headers
    """
    return StreamingResponse(
        stream_chat_response(client, prompt, model, request_id),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Content-Type": "text/event-stream",
        }
    )


async def collect_streaming_response(
    client: CodegenClient,
    prompt: str
) -> str:
    """
    Collect a complete response from streaming for non-streaming requests.
    
    Args:
        client: Codegen client instance
        prompt: The prompt to send to Codegen
        
    Returns:
        Complete response content
    """
    content_parts = []
    
    async for content_chunk in client.run_task(prompt, stream=False):
        if content_chunk:
            content_parts.append(content_chunk)
    
    return "".join(content_parts)

