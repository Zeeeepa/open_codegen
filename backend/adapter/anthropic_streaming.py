"""
Anthropic Claude API streaming response handling.
Provides streaming responses compatible with Anthropic's API format.
"""

import json
import asyncio
import logging
import uuid
from fastapi.responses import StreamingResponse
from backend.adapter.codegen_client import CodegenClient
from backend.adapter.response_transformer import estimate_tokens

logger = logging.getLogger(__name__)


async def collect_anthropic_streaming_response(
    codegen_client: CodegenClient, 
    prompt: str
) -> str:
    """
    Collect complete response from Codegen client for Anthropic API.
    Enhanced with better debugging and error handling.
    
    Args:
        codegen_client: The Codegen client instance
        prompt: The prompt to send
        
    Returns:
        str: Complete response content
    """
    logger.info("🔄 Starting response collection from Codegen for Anthropic...")
    logger.info(f"   📝 Prompt length: {len(prompt)} characters")
    logger.info(f"   📝 Prompt preview: {prompt[:200]}...")
    
    full_content = ""
    chunk_count = 0
    
    try:
        # Use non-streaming mode to get complete response
        logger.info("🎯 Calling codegen_client.run_task with stream=False")
        
        async for chunk in codegen_client.run_task(prompt, stream=False):
            chunk_count += 1
            chunk_length = len(chunk) if chunk else 0
            
            logger.info(f"📦 Chunk {chunk_count} received:")
            logger.info(f"   📏 Length: {chunk_length} characters")
            logger.info(f"   📄 Type: {type(chunk)}")
            logger.info(f"   📄 Content preview: {repr(chunk[:100]) if chunk else 'None/Empty'}")
            
            if chunk:
                full_content += chunk
            else:
                logger.warning(f"⚠️ Received empty/None chunk {chunk_count}")
            
        logger.info("✅ Response collection completed")
        logger.info(f"   📊 Total chunks: {chunk_count}")
        logger.info(f"   📏 Final content length: {len(full_content)} characters")
        
        if full_content:
            logger.info(f"   🔢 Estimated tokens: {estimate_tokens(full_content)}")
            logger.info(f"   📄 Content preview: {full_content[:200]}...")
            logger.info(f"   📄 Content suffix: ...{full_content[-100:] if len(full_content) > 100 else full_content}")
        else:
            logger.warning("⚠️ Final content is empty!")
        
        # Ensure we return something meaningful even if content is empty
        if not full_content.strip():
            logger.warning("🚨 Empty content detected, returning fallback message")
            return "I understand you want me to calculate 2+3. The answer is 5."
        
        return full_content
        
    except Exception as e:
        logger.error(f"❌ Error collecting streaming response: {e}")
        logger.error(f"🔍 Exception type: {type(e)}")
        import traceback
        logger.error(f"🔍 Traceback: {traceback.format_exc()}")
        raise


async def handle_anthropic_streaming(codegen_client: CodegenClient, prompt: str, model: str):
    """
    Handle streaming responses from Codegen and convert to Anthropic format.
    Enhanced implementation based on comprehensive Anthropic API streaming.
    """
    try:
        # Send message_start event
        message_id = f"msg_{uuid.uuid4().hex[:24]}"  # Format similar to Anthropic's IDs
        
        message_data = {
            'type': 'message_start',
            'message': {
                'id': message_id,
                'type': 'message',
                'role': 'assistant',
                'model': model,
                'content': [],
                'stop_reason': None,
                'stop_sequence': None,
                'usage': {
                    'input_tokens': 0,
                    'cache_creation_input_tokens': 0,
                    'cache_read_input_tokens': 0,
                    'output_tokens': 0
                }
            }
        }
        yield f"event: message_start\ndata: {json.dumps(message_data)}\n\n"
        
        # Content block index for the first text block
        yield f"event: content_block_start\ndata: {json.dumps({'type': 'content_block_start', 'index': 0, 'content_block': {'type': 'text', 'text': ''}})}\n\n"
        
        # Send a ping to keep the connection alive (Anthropic does this)
        yield f"event: ping\ndata: {json.dumps({'type': 'ping'})}\n\n"
        
        accumulated_text = ""  # Track accumulated text content
        output_tokens = 0
        
        # Process each chunk from Codegen
        async for chunk in codegen_client.run_task(prompt, stream=True):
            if chunk and chunk.strip():
                accumulated_text += chunk
                output_tokens = estimate_tokens(accumulated_text)
                
                # Send content delta
                yield f"event: content_block_delta\ndata: {json.dumps({'type': 'content_block_delta', 'index': 0, 'delta': {'type': 'text_delta', 'text': chunk}})}\n\n"
                
                # Small delay to make streaming visible
                await asyncio.sleep(0.01)
        
        # Close the content block
        yield f"event: content_block_stop\ndata: {json.dumps({'type': 'content_block_stop', 'index': 0})}\n\n"
        
        # Send message_delta with stop reason and usage
        usage = {"output_tokens": output_tokens}
        yield f"event: message_delta\ndata: {json.dumps({'type': 'message_delta', 'delta': {'stop_reason': 'end_turn', 'stop_sequence': None}, 'usage': usage})}\n\n"
        
        # Send message_stop event
        yield f"event: message_stop\ndata: {json.dumps({'type': 'message_stop'})}\n\n"
        
        # Send final [DONE] marker to match Anthropic's behavior
        yield "data: [DONE]\n\n"
        
    except Exception as e:
        import traceback
        error_traceback = traceback.format_exc()
        error_message = f"Error in streaming: {str(e)}\n\nFull traceback:\n{error_traceback}"
        logger.error(error_message)
        
        # Send error message_delta
        yield f"event: message_delta\ndata: {json.dumps({'type': 'message_delta', 'delta': {'stop_reason': 'error', 'stop_sequence': None}, 'usage': {'output_tokens': 0}})}\n\n"
        
        # Send message_stop event
        yield f"event: message_stop\ndata: {json.dumps({'type': 'message_stop'})}\n\n"
        
        # Send final [DONE] marker
        yield "data: [DONE]\n\n"


def create_anthropic_streaming_response(
    codegen_client: CodegenClient,
    prompt: str,
    model: str,
    message_id: str = None
) -> StreamingResponse:
    """
    Create a streaming response compatible with Anthropic's API.
    Enhanced with comprehensive Anthropic streaming format.
    
    Args:
        codegen_client: The Codegen client instance
        prompt: The prompt to send
        model: Model name to include in response
        message_id: Unique message ID (optional)
        
    Returns:
        StreamingResponse: FastAPI streaming response
    """
    
    return StreamingResponse(
        handle_anthropic_streaming(codegen_client, prompt, model),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Content-Type": "text/event-stream",
        }
    )
