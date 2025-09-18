"""
API endpoints for endpoint management (trading bot style)
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel
from typing import Dict, Any, List, Optional
import logging

from ..endpoint_manager import get_endpoint_manager
from ..models.providers import ProviderType

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/endpoints", tags=["endpoints"])

class EndpointCreateRequest(BaseModel):
    name: str
    provider_type: str  # "rest_api", "web_chat", "api_token"
    description: Optional[str] = ""
    base_url: Optional[str] = None
    api_key: Optional[str] = None
    login_url: Optional[str] = None
    username: Optional[str] = None
    password: Optional[str] = None
    browser_config: Optional[Dict[str, Any]] = {}
    model_mapping: Optional[Dict[str, str]] = {}
    timeout_seconds: Optional[int] = 30
    max_requests_per_minute: Optional[int] = 60

class EndpointResponse(BaseModel):
    name: str
    provider_type: str
    status: str
    metrics: Dict[str, Any]
    health: str

class MessageRequest(BaseModel):
    message: str
    model: Optional[str] = "gpt-3.5-turbo"
    temperature: Optional[float] = 0.7
    max_tokens: Optional[int] = 2048
    session_id: Optional[str] = None

@router.get("/", response_model=List[EndpointResponse])
async def list_endpoints():
    """List all active endpoints (trading portfolio view)"""
    try:
        manager = get_endpoint_manager()
        endpoints = manager.get_active_endpoints_server()
        return endpoints
    except Exception as e:
        logger.error(f"Failed to list endpoints: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/", response_model=Dict[str, str])
async def create_endpoint(request: EndpointCreateRequest, background_tasks: BackgroundTasks):
    """Create new endpoint (add new trading position)"""
    try:
        manager = get_endpoint_manager()
        
        # Validate provider type
        try:
            ProviderType(request.provider_type)
        except ValueError:
            raise HTTPException(
                status_code=400, 
                detail=f"Invalid provider type: {request.provider_type}"
            )
        
        # Convert to dict for manager
        config = request.dict()
        
        # Add endpoint using new server architecture
        success = await manager.add_endpoint_server(
            name=request.name,
            provider_type=request.provider_type,
            config=config,
            priority=50  # Default priority
        )
        
        if success:
            return {"status": "success", "message": f"Endpoint {request.name} created successfully"}
        else:
            raise HTTPException(status_code=400, detail="Failed to create endpoint")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to create endpoint: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/{endpoint_name}", response_model=Dict[str, str])
async def delete_endpoint(endpoint_name: str):
    """Delete endpoint (close trading position)"""
    try:
        manager = get_endpoint_manager()
        success = await manager.remove_endpoint_server(endpoint_name)
        
        if success:
            return {"status": "success", "message": f"Endpoint {endpoint_name} deleted successfully"}
        else:
            raise HTTPException(status_code=404, detail="Endpoint not found")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete endpoint: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/{endpoint_name}/start", response_model=Dict[str, str])
async def start_endpoint(endpoint_name: str):
    """Start endpoint (open trading position)"""
    try:
        manager = get_endpoint_manager()
        success = await manager.start_endpoint_server(endpoint_name)
        
        if success:
            return {"status": "success", "message": f"Endpoint {endpoint_name} started successfully"}
        else:
            raise HTTPException(status_code=400, detail="Failed to start endpoint")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to start endpoint: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/{endpoint_name}/stop", response_model=Dict[str, str])
async def stop_endpoint(endpoint_name: str):
    """Stop endpoint (close trading position)"""
    try:
        manager = get_endpoint_manager()
        success = await manager.stop_endpoint_server(endpoint_name)
        
        if success:
            return {"status": "success", "message": f"Endpoint {endpoint_name} stopped successfully"}
        else:
            raise HTTPException(status_code=400, detail="Failed to stop endpoint")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to stop endpoint: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{endpoint_name}/metrics", response_model=Dict[str, Any])
async def get_endpoint_metrics(endpoint_name: str):
    """Get endpoint performance metrics"""
    try:
        manager = get_endpoint_manager()
        metrics = manager.get_endpoint_metrics_server(endpoint_name)
        
        if metrics:
            return metrics
        else:
            raise HTTPException(status_code=404, detail="Endpoint not found")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get metrics: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{endpoint_name}/health", response_model=Dict[str, Any])
async def check_endpoint_health(endpoint_name: str):
    """Check endpoint health status"""
    try:
        manager = get_endpoint_manager()
        health = await manager.health_check_endpoint_server(endpoint_name)
        return health
        
    except Exception as e:
        logger.error(f"Failed to check health: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/{endpoint_name}/test", response_model=Dict[str, Any])
async def test_endpoint(endpoint_name: str, request: MessageRequest):
    """Test endpoint with a message"""
    try:
        manager = get_endpoint_manager()
        
        response = await manager.test_endpoint_server(endpoint_name, request.message)
        
        if response:
            return {
                "status": "success",
                "response": {
                    "content": response,
                    "endpoint": endpoint_name
                }
            }
        else:
            raise HTTPException(status_code=400, detail="Failed to send message")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to test endpoint: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/best", response_model=Dict[str, str])
async def get_best_endpoint(criteria: str = "success_rate"):
    """Get best performing endpoint (trading optimization)"""
    try:
        manager = get_endpoint_manager()
        best_endpoint = await manager.get_best_endpoint(criteria)
        
        if best_endpoint:
            return {"best_endpoint": best_endpoint, "criteria": criteria}
        else:
            raise HTTPException(status_code=404, detail="No endpoints available")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get best endpoint: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/types", response_model=List[str])
async def get_provider_types():
    """Get available provider types"""
    return [provider_type.value for provider_type in ProviderType]
