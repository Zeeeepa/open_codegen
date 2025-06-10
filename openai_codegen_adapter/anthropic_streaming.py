"""
Anthropic Claude API streaming response handling.
Provides streaming responses compatible with Anthropic's API format.
"""

import json
import asyncio
import logging
from typing import AsyncGenerator
from fastapi.responses import StreamingResponse
from .client import CodegenClient
from .anthropic_transformer import create_anthropic_stream_event
from .response_transformer import estimate_tokens

logger = logging.getLogger(__name__)


async def collect_anthropic_streaming_response(
    codegen_client: CodegenClient, 
    prompt: str
) -> str:
    """
    Collect complete response from Codegen client for Anthropic API.
    
    Args:
        codegen_client: The Codegen client instance
        prompt: The prompt to send
        
    Returns:
        str: Complete response content
    """
    logger.info("🔄 Starting response collection from Codegen for Anthropic...")
    logger.info(f"   📝 Prompt length: {len(prompt)} characters")
    
    full_content = ""
    chunk_count = 0
    
    try:
        async for chunk in codegen_client.run_task(prompt, stream=False):
            chunk_count += 1
            if chunk_count == 1:
                logger.info(f"📦 First response chunk received ({len(chunk)} chars)")
            else:
                logger.info(f"📦 Chunk {chunk_count} received (Total: {len(full_content + chunk)} chars)")
            
            full_content += chunk
            
        logger.info(f"✅ Response collection completed")
        logger.info(f"   📊 Total chunks: {chunk_count}")
        logger.info(f"   📏 Final content length: {len(full_content)} characters")
        logger.info(f"   🔢 Estimated tokens: {estimate_tokens(full_content)}")
        logger.info(f"   📄 Content preview: {full_content[:100]}...")
        
        return full_content
        
    except Exception as e:
        logger.error(f"❌ Error collecting streaming response: {e}")
        raise


def create_anthropic_streaming_response(
    codegen_client: CodegenClient,
    prompt: str,
    model: str,
    message_id: str
) -> StreamingResponse:
    """
    Create a streaming response compatible with Anthropic's API.
    
    Args:
        codegen_client: The Codegen client instance
        prompt: The prompt to send
        model: Model name to include in response
        message_id: Unique message ID
        
    Returns:
        StreamingResponse: FastAPI streaming response
    """
    
    async def generate_anthropic_stream():
        """Generate Anthropic-compatible streaming events."""
        try:
            logger.info("🌊 Starting Anthropic streaming response generation...")
            
            # Send message_start event
            start_event = create_anthropic_stream_event("message_start", model=model)
            yield f"event: message_start\ndata: {json.dumps(start_event)}\n\n"
            
            # Send content_block_start event
            block_start_event = create_anthropic_stream_event("content_block_start")
            yield f"event: content_block_start\ndata: {json.dumps(block_start_event)}\n\n"
            
            # Collect response from Codegen and stream it
            full_content = ""
            chunk_count = 0
            
            async for chunk in codegen_client.run_task(prompt, stream=False):
                chunk_count += 1
                full_content += chunk
                
                # Send content_block_delta event for each chunk
                delta_event = create_anthropic_stream_event("content_block_delta", content=chunk)
                yield f"event: content_block_delta\ndata: {json.dumps(delta_event)}\n\n"
                
                # Small delay to make streaming visible
                await asyncio.sleep(0.01)
            
            # Send content_block_stop event
            block_stop_event = create_anthropic_stream_event("content_block_stop")
            yield f"event: content_block_stop\ndata: {json.dumps(block_stop_event)}\n\n"
            
            # Send message_delta event with usage
            from .models import AnthropicUsage
            usage = AnthropicUsage(
                input_tokens=estimate_tokens(prompt),
                output_tokens=estimate_tokens(full_content)
            )
            delta_event = create_anthropic_stream_event("message_delta", usage=usage)
            yield f"event: message_delta\ndata: {json.dumps(delta_event)}\n\n"
            
            # Send message_stop event
            stop_event = create_anthropic_stream_event("message_stop")
            yield f"event: message_stop\ndata: {json.dumps(stop_event)}\n\n"
            
            logger.info(f"✅ Anthropic streaming completed: {chunk_count} chunks, {len(full_content)} chars")
            
        except Exception as e:
            logger.error(f"❌ Error in Anthropic streaming: {e}")
            # Send error event
            error_event = {
                "type": "error",
                "error": {
                    "type": "api_error",
                    "message": str(e)
                }
            }
            yield f"event: error\ndata: {json.dumps(error_event)}\n\n"
    
    return StreamingResponse(
        generate_anthropic_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Content-Type": "text/event-stream",
        }
    )
