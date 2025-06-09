"""
Google Gemini API streaming response handling.
Provides streaming responses compatible with Gemini's API format.
"""

import json
import asyncio
import logging
from typing import AsyncGenerator
from fastapi.responses import StreamingResponse
from .codegen_client import CodegenClient
from .gemini_transformer import create_gemini_stream_chunk
from .response_transformer import estimate_tokens

logger = logging.getLogger(__name__)


async def collect_gemini_streaming_response(
    codegen_client: CodegenClient, 
    prompt: str
) -> str:
    """
    Collect complete response from Codegen client for Gemini API.
    
    Args:
        codegen_client: The Codegen client instance
        prompt: The prompt to send
        
    Returns:
        str: Complete response content
    """
    logger.info("🔄 Starting response collection from Codegen for Gemini...")
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


def create_gemini_streaming_response(
    codegen_client: CodegenClient,
    prompt: str,
    model: str
) -> StreamingResponse:
    """
    Create a streaming response compatible with Gemini's API.
    
    Args:
        codegen_client: The Codegen client instance
        prompt: The prompt to send
        model: Model name to include in response
        
    Returns:
        StreamingResponse: FastAPI streaming response
    """
    
    async def generate_gemini_stream():
        """Generate Gemini-compatible streaming chunks."""
        try:
            logger.info("🌊 Starting Gemini streaming response generation...")
            
            # Collect response from Codegen and stream it
            full_content = ""
            chunk_count = 0
            prompt_tokens = estimate_tokens(prompt)
            
            async for chunk in codegen_client.run_task(prompt, stream=False):
                chunk_count += 1
                full_content += chunk
                
                # Create streaming chunk
                is_final = False  # We'll mark the last chunk as final
                stream_chunk = create_gemini_stream_chunk(
                    content=chunk,
                    is_final=is_final,
                    prompt_tokens=prompt_tokens,
                    completion_tokens=estimate_tokens(full_content)
                )
                
                # Send chunk as JSON
                yield f"data: {json.dumps(stream_chunk)}\n\n"
                
                # Small delay to make streaming visible
                await asyncio.sleep(0.01)
            
            # Send final chunk with usage metadata
            final_chunk = create_gemini_stream_chunk(
                content="",  # Empty content for final chunk
                is_final=True,
                prompt_tokens=prompt_tokens,
                completion_tokens=estimate_tokens(full_content)
            )
            yield f"data: {json.dumps(final_chunk)}\n\n"
            
            # Send done signal
            yield "data: [DONE]\n\n"
            
            logger.info(f"✅ Gemini streaming completed: {chunk_count} chunks, {len(full_content)} chars")
            
        except Exception as e:
            logger.error(f"❌ Error in Gemini streaming: {e}")
            # Send error chunk
            error_chunk = {
                "error": {
                    "code": 500,
                    "message": str(e),
                    "status": "INTERNAL"
                }
            }
            yield f"data: {json.dumps(error_chunk)}\n\n"
    
    return StreamingResponse(
        generate_gemini_stream(),
        media_type="text/plain",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Content-Type": "text/plain",
        }
    )
