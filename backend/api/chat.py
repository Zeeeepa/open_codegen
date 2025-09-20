"""
Chat API endpoints for the Universal AI Endpoint Management System
OpenAI-compatible API that routes to managed endpoints
"""

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import Dict, Any, List, Optional, Union, AsyncGenerator
import json
import logging
from datetime import datetime

from ..endpoint_manager import get_endpoint_manager

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/v1", tags=["chat"])

class ChatMessage(BaseModel):
    role: str
    content: str

class ChatCompletionRequest(BaseModel):
    model: str
    messages: List[ChatMessage]
    temperature: Optional[float] = 0.7
    max_tokens: Optional[int] = 2048
    stream: Optional[bool] = False
    top_p: Optional[float] = 1.0
    frequency_penalty: Optional[float] = 0.0
    presence_penalty: Optional[float] = 0.0
    stop: Optional[Union[str, List[str]]] = None
    user: Optional[str] = None

class ChatCompletionResponse(BaseModel):
    id: str
    object: str = "chat.completion"
    created: int
    model: str
    choices: List[Dict[str, Any]]
    usage: Dict[str, Any]

class ChatCompletionStreamResponse(BaseModel):
    id: str
    object: str = "chat.completion.chunk"
    created: int
    model: str
    choices: List[Dict[str, Any]]

@router.post("/chat/completions")
async def create_chat_completion(request: ChatCompletionRequest):
    """OpenAI-compatible chat completions endpoint"""
    try:
        manager = get_endpoint_manager()
        
        # Get the best endpoint for this request
        best_endpoint = await manager.get_best_endpoint('success_rate')
        
        if not best_endpoint:
            raise HTTPException(status_code=503, detail="No endpoints available")
        
        # Extract the user message (last message typically)
        user_message = ""
        for message in reversed(request.messages):
            if message.role == "user":
                user_message = message.content
                break
        
        if not user_message:
            raise HTTPException(status_code=400, detail="No user message found")
        
        # Prepare request parameters
        kwargs = {
            'model': request.model,
            'temperature': request.temperature,
            'max_tokens': request.max_tokens,
            'user': request.user
        }
        
        if request.stream:
            return StreamingResponse(
                _stream_chat_completion(manager, best_endpoint, user_message, request, kwargs),
                media_type="text/plain"
            )
        else:
            # Send message to best endpoint
            response = await manager.send_message(best_endpoint, user_message, **kwargs)
            
            if not response:
                raise HTTPException(status_code=500, detail="Failed to get response from endpoint")
            
            # Format as OpenAI-compatible response
            return ChatCompletionResponse(
                id=response.id,
                created=int(datetime.utcnow().timestamp()),
                model=response.model,
                choices=[{
                    "index": 0,
                    "message": {
                        "role": "assistant",
                        "content": response.content
                    },
                    "finish_reason": "stop"
                }],
                usage=response.usage or {
                    "prompt_tokens": len(user_message.split()),
                    "completion_tokens": len(response.content.split()),
                    "total_tokens": len(user_message.split()) + len(response.content.split())
                }
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Chat completion error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

async def _stream_chat_completion(
    manager, 
    endpoint_name: str, 
    message: str, 
    request: ChatCompletionRequest,
    kwargs: Dict[str, Any]
) -> AsyncGenerator[str, None]:
    """Stream chat completion response"""
    try:
        response_id = f"chatcmpl-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
        created = int(datetime.utcnow().timestamp())
        
        # Send initial chunk
        initial_chunk = ChatCompletionStreamResponse(
            id=response_id,
            created=created,
            model=request.model,
            choices=[{
                "index": 0,
                "delta": {"role": "assistant"},
                "finish_reason": None
            }]
        )
        
        yield f"data: {initial_chunk.json()}\n\n"
        
        # Stream content
        async for chunk in manager.stream_message(endpoint_name, message, **kwargs):
            stream_chunk = ChatCompletionStreamResponse(
                id=response_id,
                created=created,
                model=request.model,
                choices=[{
                    "index": 0,
                    "delta": {"content": chunk},
                    "finish_reason": None
                }]
            )
            
            yield f"data: {stream_chunk.json()}\n\n"
        
        # Send final chunk
        final_chunk = ChatCompletionStreamResponse(
            id=response_id,
            created=created,
            model=request.model,
            choices=[{
                "index": 0,
                "delta": {},
                "finish_reason": "stop"
            }]
        )
        
        yield f"data: {final_chunk.json()}\n\n"
        yield "data: [DONE]\n\n"
        
    except Exception as e:
        logger.error(f"Streaming error: {e}")
        error_chunk = {
            "error": {
                "message": str(e),
                "type": "server_error",
                "code": "internal_error"
            }
        }
        yield f"data: {json.dumps(error_chunk)}\n\n"

@router.get("/models")
async def list_models():
    """List available models (from all endpoints)"""
    try:
        manager = get_endpoint_manager()
        endpoints = manager.get_active_endpoints()
        
        models = []
        for endpoint in endpoints:
            # Create model entries for each endpoint
            model_name = f"{endpoint['name'].lower().replace(' ', '-')}"
            models.append({
                "id": model_name,
                "object": "model",
                "created": int(datetime.utcnow().timestamp()),
                "owned_by": endpoint['name'],
                "permission": [],
                "root": model_name,
                "parent": None
            })
        
        return {"object": "list", "data": models}
        
    except Exception as e:
        logger.error(f"List models error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/models/{model_id}")
async def get_model(model_id: str):
    """Get specific model information"""
    try:
        manager = get_endpoint_manager()
        endpoints = manager.get_active_endpoints()
        
        # Find endpoint by model name
        for endpoint in endpoints:
            endpoint_model = f"{endpoint['name'].lower().replace(' ', '-')}"
            if endpoint_model == model_id:
                return {
                    "id": model_id,
                    "object": "model",
                    "created": int(datetime.utcnow().timestamp()),
                    "owned_by": endpoint['name'],
                    "permission": [],
                    "root": model_id,
                    "parent": None
                }
        
        raise HTTPException(status_code=404, detail="Model not found")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get model error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/completions")
async def create_completion(request: Dict[str, Any]):
    """Legacy completions endpoint (redirects to chat completions)"""
    try:
        # Convert legacy completion to chat completion format
        prompt = request.get('prompt', '')
        
        chat_request = ChatCompletionRequest(
            model=request.get('model', 'gpt-3.5-turbo'),
            messages=[{"role": "user", "content": prompt}],
            temperature=request.get('temperature', 0.7),
            max_tokens=request.get('max_tokens', 2048),
            stream=request.get('stream', False)
        )
        
        return await create_chat_completion(chat_request)
        
    except Exception as e:
        logger.error(f"Completion error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
