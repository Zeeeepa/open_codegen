"""
Streaming utilities for Google Gemini API compatibility.
"""

import asyncio
import json
import logging
import time
from typing import AsyncGenerator, Dict, Any
from fastapi.responses import StreamingResponse
from .codegen_client import CodegenClient

logger = logging.getLogger(__name__)


async def stream_gemini_response(
    client: CodegenClient,
    prompt: str
) -> AsyncGenerator[str, None]:
    """
    Stream Gemini response as Server-Sent Events.
    
    Args:
        client: Codegen client
        prompt: Prompt to send
        
    Yields:
        SSE-formatted response chunks
    """
    try:
        # Stream the actual response
        accumulated_content = ""
        async for content_chunk in client.run_task(prompt, stream=True):
            if content_chunk:
                # Clean the content
                cleaned_chunk = content_chunk.strip()
                if cleaned_chunk:
                    # Create chunk response
                    chunk_response = {
                        "candidates": [
                            {
                                "content": {
                                    "parts": [
                                        {"text": cleaned_chunk}
                                    ],
                                    "role": "model"
                                },
                                "finishReason": None,
                                "index": 0,
                                "safetyRatings": []
                            }
                        ],
                        "promptFeedback": {}
                    }
                    
                    # Send chunk
                    yield f"data: {json.dumps(chunk_response)}\n\n"
                    accumulated_content += cleaned_chunk
                    
                    # Small delay to prevent overwhelming the client
                    await asyncio.sleep(0.01)
        
        # Send final chunk with finish_reason
        final_chunk = {
            "candidates": [
                {
                    "content": {
                        "parts": [
                            {"text": ""}
                        ],
                        "role": "model"
                    },
                    "finishReason": "STOP",
                    "index": 0,
                    "safetyRatings": []
                }
            ],
            "promptFeedback": {}
        }
        yield f"data: {json.dumps(final_chunk)}\n\n"
        
        # Send completion marker
        yield "data: [DONE]\n\n"
        
    except Exception as e:
        logger.error(f"Error in Gemini streaming response: {e}")
        # Send error chunk
        error_chunk = {
            "error": {
                "code": 500,
                "message": str(e),
                "status": "INTERNAL"
            }
        }
        yield f"data: {json.dumps(error_chunk)}\n\n"
        yield "data: [DONE]\n\n"


def create_gemini_streaming_response(
    client: CodegenClient,
    prompt: str
) -> StreamingResponse:
    """
    Create a FastAPI StreamingResponse for Gemini API.
    
    Args:
        client: Codegen client
        prompt: Prompt to send
        
    Returns:
        FastAPI StreamingResponse
    """
    return StreamingResponse(
        stream_gemini_response(client, prompt),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Content-Type": "text/event-stream",
        }
    )


async def collect_gemini_streaming_response(
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

