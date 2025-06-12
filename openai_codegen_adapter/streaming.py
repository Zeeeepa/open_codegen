"""
Streaming response utilities for Server-Sent Events.
Based on h2ogpt's streaming patterns.
Enhanced with completion tracking and detailed logging.
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
from .client import CodegenClient

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
        media_type="text/plain",
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
    Enhanced with detailed completion tracking and logging.
    
    Args:
        client: Codegen client instance
        prompt: The prompt to send to Codegen
        
    Returns:
        Complete response content
    """
    content_parts = []
    start_time = time.time()
    
    try:
        logger.info("🔄 Starting response collection from Codegen...")
        logger.info(f"   📝 Prompt length: {len(prompt)} characters")
        
        chunk_count = 0
        async for content_chunk in client.run_task(prompt, stream=False):
            if content_chunk:
                chunk_count += 1
                content_parts.append(content_chunk)
                
                # Log progress for long responses
                if chunk_count == 1:
                    logger.info(f"📦 First response chunk received ({len(content_chunk)} chars)")
                elif chunk_count % 5 == 0:  # Log every 5th chunk
                    total_length = sum(len(part) for part in content_parts)
                    logger.info(f"📦 Chunk {chunk_count} received (Total: {total_length} chars)")
        
        full_content = "".join(content_parts)
        cleaned_content = clean_content(full_content)
        
        collection_time = time.time() - start_time
        
        logger.info(f"✅ Response collection completed in {collection_time:.2f}s")
        logger.info(f"   📊 Total chunks: {chunk_count}")
        logger.info(f"   📏 Final content length: {len(cleaned_content)} characters")
        logger.info(f"   🔢 Estimated tokens: {estimate_tokens(cleaned_content)}")
        logger.info(f"   📄 Content preview: {cleaned_content[:100]}...")
        
        return cleaned_content
        
    except Exception as e:
        collection_time = time.time() - start_time
        logger.error(f"❌ Error collecting streaming response after {collection_time:.2f}s: {e}")
        return f"Error: {str(e)}"
