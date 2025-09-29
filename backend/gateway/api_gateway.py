#!/usr/bin/env python3
"""
OpenAI API Gateway
Intercepts OpenAI API calls and routes them to AI provider services
"""

import asyncio
import json
import logging
import os
import time
from typing import Dict, Any, Optional, List
import aiohttp
import uvicorn
from fastapi import FastAPI, HTTPException, Request, Depends
from fastapi.responses import StreamingResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from contextlib import asynccontextmanager

from backend.registry.service_registry import service_registry, ServiceStatus
from backend.routing.load_balancer import LoadBalancer, LoadBalancingStrategy
from backend.services.service_manager import service_manager

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuration
GATEWAY_PORT = int(os.getenv("GATEWAY_PORT", "7999"))
OPENAI_INTERCEPT_PORT = int(os.getenv("OPENAI_INTERCEPT_PORT", "443"))  # Standard HTTPS port

class ChatMessage(BaseModel):
    role: str
    content: str

class ChatCompletionRequest(BaseModel):
    model: str = "gpt-3.5-turbo"
    messages: List[ChatMessage]
    temperature: float = 0.7
    max_tokens: Optional[int] = None
    stream: bool = False
    top_p: float = 1.0
    frequency_penalty: float = 0.0
    presence_penalty: float = 0.0
    user: Optional[str] = None

class CompletionRequest(BaseModel):
    model: str = "gpt-3.5-turbo"
    prompt: str
    temperature: float = 0.7
    max_tokens: Optional[int] = None
    stream: bool = False
    top_p: float = 1.0
    frequency_penalty: float = 0.0
    presence_penalty: float = 0.0

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    logger.info("🚀 OpenAI API Gateway starting up...")
    
    # Start service manager and health monitoring
    asyncio.create_task(service_manager.health_monitor_loop())
    
    yield
    
    logger.info("🛑 OpenAI API Gateway shutting down...")
    await service_manager.stop_all_services()

app = FastAPI(
    title="OpenAI API Gateway",
    description="Intercepts OpenAI API calls and routes to AI providers",
    version="1.0.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize load balancer
load_balancer = LoadBalancer()

@app.get("/health")
async def health_check():
    """Gateway health check"""
    healthy_services = service_registry.get_healthy_services()
    stats = service_registry.get_service_stats()
    
    return {
        "status": "healthy",
        "service": "openai-api-gateway",
        "timestamp": time.time(),
        "version": "1.0.0",
        "healthy_providers": len(healthy_services),
        "total_providers": stats["total_services"],
        "provider_stats": stats
    }

@app.get("/v1/models")
async def list_models():
    """List all available models from all providers"""
    models = []
    model_set = set()
    
    for service in service_registry.get_healthy_services().values():
        for model in service.models:
            if model not in model_set:
                models.append({
                    "id": model,
                    "object": "model",
                    "created": int(time.time()),
                    "owned_by": service.name,
                    "permission": [],
                    "root": model,
                    "parent": None
                })
                model_set.add(model)
    
    return {
        "object": "list",
        "data": models
    }

@app.get("/providers")
async def list_providers():
    """List all available providers and their status"""
    providers = []
    
    for name, service in service_registry.get_all_services().items():
        providers.append({
            "name": name,
            "status": service.status.value,
            "port": service.port,
            "models": service.models,
            "response_time": service.response_time,
            "error_count": service.error_count,
            "last_health_check": service.last_health_check,
            "uptime": time.time() - service.uptime_start if service.uptime_start else 0
        })
    
    return {
        "providers": providers,
        "stats": service_registry.get_service_stats()
    }

@app.post("/providers/{provider_name}/start")
async def start_provider(provider_name: str):
    """Start a specific provider"""
    if not service_registry.get_service(provider_name):
        raise HTTPException(status_code=404, detail=f"Provider {provider_name} not found")
    
    success = await service_manager.start_service(provider_name)
    
    return {
        "provider": provider_name,
        "action": "start",
        "success": success,
        "timestamp": time.time()
    }

@app.post("/providers/{provider_name}/stop")
async def stop_provider(provider_name: str):
    """Stop a specific provider"""
    if not service_registry.get_service(provider_name):
        raise HTTPException(status_code=404, detail=f"Provider {provider_name} not found")
    
    success = await service_manager.stop_service(provider_name)
    
    return {
        "provider": provider_name,
        "action": "stop",
        "success": success,
        "timestamp": time.time()
    }

@app.post("/providers/{provider_name}/restart")
async def restart_provider(provider_name: str):
    """Restart a specific provider"""
    if not service_registry.get_service(provider_name):
        raise HTTPException(status_code=404, detail=f"Provider {provider_name} not found")
    
    success = await service_manager.restart_service(provider_name)
    
    return {
        "provider": provider_name,
        "action": "restart",
        "success": success,
        "timestamp": time.time()
    }

@app.post("/providers/start-all")
async def start_all_providers():
    """Start all providers"""
    results = await service_manager.start_all_services()
    successful = sum(1 for success in results.values() if success)
    
    return {
        "action": "start-all",
        "results": results,
        "successful": successful,
        "total": len(results),
        "timestamp": time.time()
    }

@app.post("/providers/stop-all")
async def stop_all_providers():
    """Stop all providers"""
    results = await service_manager.stop_all_services()
    successful = sum(1 for success in results.values() if success)
    
    return {
        "action": "stop-all",
        "results": results,
        "successful": successful,
        "total": len(results),
        "timestamp": time.time()
    }

async def route_request_to_provider(
    service_name: str,
    endpoint: str,
    payload: Dict[str, Any],
    stream: bool = False
) -> Any:
    """Route request to a specific provider"""
    service = service_registry.get_service(service_name)
    if not service or service.status != ServiceStatus.HEALTHY:
        raise HTTPException(
            status_code=503,
            detail=f"Provider {service_name} is not available"
        )
    
    url = f"http://localhost:{service.port}{endpoint}"
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                url,
                json=payload,
                timeout=aiohttp.ClientTimeout(total=60)
            ) as response:
                if stream:
                    # Handle streaming response
                    async def stream_generator():
                        async for chunk in response.content.iter_chunked(1024):
                            yield chunk.decode('utf-8', errors='ignore')
                    
                    return StreamingResponse(
                        stream_generator(),
                        media_type="text/plain",
                        headers={"Cache-Control": "no-cache", "Connection": "keep-alive"}
                    )
                else:
                    # Handle regular response
                    if response.status == 200:
                        return await response.json()
                    else:
                        error_text = await response.text()
                        raise HTTPException(status_code=response.status, detail=error_text)
                        
    except aiohttp.ClientError as e:
        logger.error(f"Error routing to {service_name}: {e}")
        raise HTTPException(status_code=503, detail=f"Provider {service_name} connection error")

@app.post("/v1/chat/completions")
async def chat_completions(
    request: ChatCompletionRequest,
    provider: Optional[str] = None
):
    """Handle OpenAI chat completions - main interception point"""
    try:
        # Convert request to dict
        payload = request.dict()
        
        # Select provider
        if provider:
            # Use specific provider if requested
            selected_service = service_registry.get_service(provider)
            if not selected_service or selected_service.status != ServiceStatus.HEALTHY:
                raise HTTPException(
                    status_code=400,
                    detail=f"Requested provider {provider} is not available"
                )
            service_name = provider
        else:
            # Use load balancer to select provider
            service_name = await load_balancer.select_provider(
                model=request.model,
                strategy=LoadBalancingStrategy.ROUND_ROBIN
            )
            
            if not service_name:
                raise HTTPException(
                    status_code=503,
                    detail="No healthy providers available"
                )
        
        logger.info(f"Routing chat completion to {service_name} (model: {request.model})")
        
        # Route request to selected provider
        response = await route_request_to_provider(
            service_name,
            "/v1/chat/completions",
            payload,
            stream=request.stream
        )
        
        # Add provider info to response metadata
        if not request.stream and isinstance(response, dict):
            response["_provider"] = service_name
            response["_gateway_timestamp"] = time.time()
        
        return response
        
    except Exception as e:
        logger.error(f"Chat completion error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/v1/completions")
async def completions(
    request: CompletionRequest,
    provider: Optional[str] = None
):
    """Handle OpenAI completions (legacy endpoint)"""
    try:
        # Convert to chat format
        chat_request = ChatCompletionRequest(
            model=request.model,
            messages=[ChatMessage(role="user", content=request.prompt)],
            temperature=request.temperature,
            max_tokens=request.max_tokens,
            stream=request.stream,
            top_p=request.top_p,
            frequency_penalty=request.frequency_penalty,
            presence_penalty=request.presence_penalty
        )
        
        return await chat_completions(chat_request, provider)
        
    except Exception as e:
        logger.error(f"Completion error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/v1/test")
async def test_endpoint(
    message: str = "Hello, AI!",
    provider: Optional[str] = None,
    model: str = "gpt-3.5-turbo"
):
    """Test endpoint for quick provider testing"""
    try:
        test_request = ChatCompletionRequest(
            model=model,
            messages=[ChatMessage(role="user", content=message)],
            temperature=0.7,
            max_tokens=100,
            stream=False
        )
        
        response = await chat_completions(test_request, provider)
        
        return {
            "test_message": message,
            "provider_used": response.get("_provider") if isinstance(response, dict) else "unknown",
            "model_used": model,
            "response": response,
            "timestamp": time.time()
        }
        
    except Exception as e:
        logger.error(f"Test endpoint error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/config")
async def get_config():
    """Get gateway configuration"""
    return {
        "gateway_port": GATEWAY_PORT,
        "load_balancing_strategies": [strategy.value for strategy in LoadBalancingStrategy],
        "current_strategy": load_balancer.default_strategy.value,
        "service_registry": service_registry.export_config(),
        "timestamp": time.time()
    }

@app.post("/config/load-balancing")
async def set_load_balancing_strategy(strategy: str):
    """Set load balancing strategy"""
    try:
        strategy_enum = LoadBalancingStrategy(strategy)
        load_balancer.default_strategy = strategy_enum
        
        return {
            "strategy": strategy,
            "success": True,
            "timestamp": time.time()
        }
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid strategy. Available: {[s.value for s in LoadBalancingStrategy]}"
        )

if __name__ == "__main__":
    import os
    logger.info(f"🚀 Starting OpenAI API Gateway on port {GATEWAY_PORT}")
    uvicorn.run(
        "backend.gateway.api_gateway:app",
        host="0.0.0.0",
        port=GATEWAY_PORT,
        reload=False,
        log_level="info"
    )
