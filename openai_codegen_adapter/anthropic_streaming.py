"""
Streaming utilities for Anthropic Claude API compatibility.
"""

import asyncio
import json
import logging
import time
from typing import AsyncGenerator, Dict, Any
from fastapi.responses import StreamingResponse
from .codegen_client import CodegenClient

logger = logging.getLogger(__name__)


async def stream_anthropic_response(
    client: CodegenClient,
    prompt: str,
    model: str,
    request_id: str
) -> AsyncGenerator[str, None]:
    """
    Stream Anthropic response as Server-Sent Events.
    
    Args:
        client: Codegen client
        prompt: Prompt to send
        model: Model name
        request_id: Request ID
        
    Yields:
        SSE-formatted response chunks
    """
    try:
        # Send initial event to start the stream
        yield f"event: message_start\ndata: {json.dumps({'type': 'message_start', 'message': {'id': request_id, 'type': 'message', 'role': 'assistant', 'model': model}})}\n\n"
        
        # Stream the actual response
        accumulated_content = ""
        async for content_chunk in client.run_task(prompt, stream=True):
            if content_chunk:
                # Clean the content
                cleaned_chunk = content_chunk.strip()
                if cleaned_chunk:
                    # Create content block
                    content_block = {
                        "type": "content_block_delta",
                        "delta": {
                            "type": "text_delta",
                            "text": cleaned_chunk
                        },
                        "index": 0
                    }
                    
                    # Send content block
                    yield f"event: content_block_delta\ndata: {json.dumps(content_block)}\n\n"
                    accumulated_content += cleaned_chunk
                    
                    # Small delay to prevent overwhelming the client
                    await asyncio.sleep(0.01)
        
        # Send message stop event
        stop_event = {
            "type": "message_stop",
            "message": {
                "id": request_id,
                "type": "message",
                "role": "assistant",
                "content": [
                    {
                        "type": "text",
                        "text": accumulated_content
                    }
                ],
                "model": model,
                "stop_reason": "end_turn"
            }
        }
        yield f"event: message_stop\ndata: {json.dumps(stop_event)}\n\n"
        
    except Exception as e:
        logger.error(f"Error in Anthropic streaming response: {e}")
        # Send error event
        error_event = {
            "type": "error",
            "error": {
                "type": "server_error",
                "message": str(e)
            }
        }
        yield f"event: error\ndata: {json.dumps(error_event)}\n\n"


def create_anthropic_streaming_response(
    client: CodegenClient,
    prompt: str,
    model: str,
    request_id: str
) -> StreamingResponse:
    """
    Create a FastAPI StreamingResponse for Anthropic API.
    
    Args:
        client: Codegen client
        prompt: Prompt to send
        model: Model name
        request_id: Request ID
        
    Returns:
        FastAPI StreamingResponse
    """
    return StreamingResponse(
        stream_anthropic_response(client, prompt, model, request_id),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Content-Type": "text/event-stream",
        }
    )


async def collect_anthropic_streaming_response(
    client: CodegenClient,
    prompt: str
) -> str:
    """
    Collect a complete response from streaming for non-streaming requests.
    
    Args:
        client: Codegen client
        prompt: Prompt to send
        
    Returns:
        Complete response content
    """
    content_parts = []
    
    async for content_chunk in client.run_task(prompt, stream=False):
        if content_chunk:
            content_parts.append(content_chunk)
    
    return "".join(content_parts)

