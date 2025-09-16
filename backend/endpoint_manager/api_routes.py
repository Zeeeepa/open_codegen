"""
API routes for AI Endpoint Management System
FastAPI routes for managing AI endpoints
"""
import uuid
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel, Field

from backend.database.models import (
    EndpointConfig, SessionState, EndpointMetrics,
    ProviderType, EndpointStatus, AuthType,
    RestApiConfig, WebChatConfig,
    get_database_manager
)
from backend.endpoint_manager.endpoint_service import EndpointService
from backend.endpoint_manager.ai_assistant import AIEndpointAssistant
from backend.endpoint_manager.default_configs import DefaultEndpointConfigs, RoutingConfigManager
from backend.middleware.openai_proxy import ProxyConfig

logger = logging.getLogger(__name__)

# Pydantic models for API requests/responses
class CreateEndpointRequest(BaseModel):
    name: str = Field(..., description="Human-readable name for the endpoint")
    model_name: str = Field(..., description="Model name to expose (e.g., 'gpt-4', 'claude-3')")
    description: Optional[str] = Field(None, description="Optional description")
    provider_type: ProviderType = Field(..., description="Type of provider")
    provider_name: str = Field(..., description="Name of the provider")
    config_data: Dict[str, Any] = Field(..., description="Provider-specific configuration")
    priority: int = Field(1, description="Priority for load balancing (1=highest)")
    max_concurrent_requests: int = Field(1, description="Maximum concurrent requests")
    timeout_seconds: int = Field(30, description="Request timeout in seconds")
    retry_attempts: int = Field(3, description="Number of retry attempts")


class UpdateEndpointRequest(BaseModel):
    name: Optional[str] = None
    model_name: Optional[str] = None
    description: Optional[str] = None
    provider_type: Optional[ProviderType] = None
    provider_name: Optional[str] = None
    config_data: Optional[Dict[str, Any]] = None
    is_enabled: Optional[bool] = None
    priority: Optional[int] = None
    max_concurrent_requests: Optional[int] = None
    timeout_seconds: Optional[int] = None
    retry_attempts: Optional[int] = None


class EndpointResponse(BaseModel):
    id: str
    user_id: str
    name: str
    model_name: str
    description: Optional[str]
    provider_type: str
    provider_name: str
    config_data: Dict[str, Any]
    status: str
    is_enabled: bool
    priority: int
    max_concurrent_requests: int
    timeout_seconds: int
    retry_attempts: int
    created_at: str
    updated_at: str


class EndpointStatsResponse(BaseModel):
    endpoint_id: str
    total_requests: int
    successful_requests: int
    success_rate: float
    avg_response_time: float
    total_input_tokens: int
    total_output_tokens: int


class AIAssistantRequest(BaseModel):
    message: str = Field(..., description="User message for AI assistant")
    context: Optional[Dict[str, Any]] = Field(None, description="Additional context")


class AIAssistantResponse(BaseModel):
    response: str = Field(..., description="AI assistant response")
    suggested_config: Optional[Dict[str, Any]] = Field(None, description="Suggested endpoint configuration")
    actions: Optional[List[str]] = Field(None, description="Suggested actions")


# Create router
router = APIRouter(prefix="/api/endpoints", tags=["endpoints"])

# Dependency to get current user (placeholder - implement based on your auth system)
def get_current_user() -> str:
    """Get current user ID - implement based on your authentication system"""
    return "default_user"  # Placeholder


# Initialize services
endpoint_service = EndpointService()
ai_assistant = AIEndpointAssistant()


@router.get("/", response_model=List[EndpointResponse])
async def list_endpoints(
    user_id: str = Depends(get_current_user),
    status: Optional[EndpointStatus] = Query(None, description="Filter by status"),
    provider_type: Optional[ProviderType] = Query(None, description="Filter by provider type"),
    enabled_only: bool = Query(False, description="Show only enabled endpoints")
):
    """List all endpoints for the current user"""
    try:
        db = get_database_manager()
        configs = db.get_user_endpoint_configs(user_id)
        
        # Apply filters
        if status:
            configs = [c for c in configs if c.status == status.value]
        if provider_type:
            configs = [c for c in configs if c.provider_type == provider_type.value]
        if enabled_only:
            configs = [c for c in configs if c.is_enabled]
        
        return [EndpointResponse(**config.to_dict()) for config in configs]
    
    except Exception as e:
        logger.error(f"Error listing endpoints: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/", response_model=EndpointResponse)
async def create_endpoint(
    request: CreateEndpointRequest,
    user_id: str = Depends(get_current_user)
):
    """Create a new AI endpoint"""
    try:
        # Create endpoint configuration
        config = EndpointConfig(
            id=str(uuid.uuid4()),
            user_id=user_id,
            name=request.name,
            model_name=request.model_name,
            description=request.description,
            provider_type=request.provider_type.value,
            provider_name=request.provider_name,
            config_data=request.config_data,
            status=EndpointStatus.STOPPED.value,
            is_enabled=True,
            priority=request.priority,
            max_concurrent_requests=request.max_concurrent_requests,
            timeout_seconds=request.timeout_seconds,
            retry_attempts=request.retry_attempts,
            created_at="",  # Will be set by database
            updated_at=""   # Will be set by database
        )
        
        # Save to database
        db = get_database_manager()
        created_config = db.create_endpoint_config(config)
        
        logger.info(f"Created endpoint {created_config.id} for user {user_id}")
        return EndpointResponse(**created_config.to_dict())
    
    except Exception as e:
        logger.error(f"Error creating endpoint: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{endpoint_id}", response_model=EndpointResponse)
async def get_endpoint(
    endpoint_id: str,
    user_id: str = Depends(get_current_user)
):
    """Get a specific endpoint by ID"""
    try:
        db = get_database_manager()
        config = db.get_endpoint_config(endpoint_id)
        
        if not config:
            raise HTTPException(status_code=404, detail="Endpoint not found")
        
        if config.user_id != user_id:
            raise HTTPException(status_code=403, detail="Access denied")
        
        return EndpointResponse(**config.to_dict())
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting endpoint {endpoint_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/{endpoint_id}", response_model=EndpointResponse)
async def update_endpoint(
    endpoint_id: str,
    request: UpdateEndpointRequest,
    user_id: str = Depends(get_current_user)
):
    """Update an existing endpoint"""
    try:
        db = get_database_manager()
        config = db.get_endpoint_config(endpoint_id)
        
        if not config:
            raise HTTPException(status_code=404, detail="Endpoint not found")
        
        if config.user_id != user_id:
            raise HTTPException(status_code=403, detail="Access denied")
        
        # Update fields
        update_data = request.dict(exclude_unset=True)
        for field, value in update_data.items():
            if hasattr(config, field):
                setattr(config, field, value)
        
        # Save changes
        updated_config = db.update_endpoint_config(config)
        
        logger.info(f"Updated endpoint {endpoint_id} for user {user_id}")
        return EndpointResponse(**updated_config.to_dict())
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating endpoint {endpoint_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{endpoint_id}")
async def delete_endpoint(
    endpoint_id: str,
    user_id: str = Depends(get_current_user)
):
    """Delete an endpoint"""
    try:
        db = get_database_manager()
        config = db.get_endpoint_config(endpoint_id)
        
        if not config:
            raise HTTPException(status_code=404, detail="Endpoint not found")
        
        if config.user_id != user_id:
            raise HTTPException(status_code=403, detail="Access denied")
        
        # Stop endpoint if running
        if config.status == EndpointStatus.RUNNING.value:
            await endpoint_service.stop_endpoint(endpoint_id)
        
        # Delete from database
        success = db.delete_endpoint_config(endpoint_id)
        
        if not success:
            raise HTTPException(status_code=500, detail="Failed to delete endpoint")
        
        logger.info(f"Deleted endpoint {endpoint_id} for user {user_id}")
        return {"message": "Endpoint deleted successfully"}
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting endpoint {endpoint_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{endpoint_id}/start")
async def start_endpoint(
    endpoint_id: str,
    user_id: str = Depends(get_current_user)
):
    """Start an endpoint"""
    try:
        db = get_database_manager()
        config = db.get_endpoint_config(endpoint_id)
        
        if not config:
            raise HTTPException(status_code=404, detail="Endpoint not found")
        
        if config.user_id != user_id:
            raise HTTPException(status_code=403, detail="Access denied")
        
        # Start the endpoint
        success = await endpoint_service.start_endpoint(endpoint_id)
        
        if not success:
            raise HTTPException(status_code=500, detail="Failed to start endpoint")
        
        logger.info(f"Started endpoint {endpoint_id} for user {user_id}")
        return {"message": "Endpoint started successfully"}
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error starting endpoint {endpoint_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{endpoint_id}/stop")
async def stop_endpoint(
    endpoint_id: str,
    user_id: str = Depends(get_current_user)
):
    """Stop an endpoint"""
    try:
        db = get_database_manager()
        config = db.get_endpoint_config(endpoint_id)
        
        if not config:
            raise HTTPException(status_code=404, detail="Endpoint not found")
        
        if config.user_id != user_id:
            raise HTTPException(status_code=403, detail="Access denied")
        
        # Stop the endpoint
        success = await endpoint_service.stop_endpoint(endpoint_id)
        
        if not success:
            raise HTTPException(status_code=500, detail="Failed to stop endpoint")
        
        logger.info(f"Stopped endpoint {endpoint_id} for user {user_id}")
        return {"message": "Endpoint stopped successfully"}
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error stopping endpoint {endpoint_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{endpoint_id}/stats", response_model=EndpointStatsResponse)
async def get_endpoint_stats(
    endpoint_id: str,
    hours: int = Query(24, description="Hours to look back for stats"),
    user_id: str = Depends(get_current_user)
):
    """Get endpoint performance statistics"""
    try:
        db = get_database_manager()
        config = db.get_endpoint_config(endpoint_id)
        
        if not config:
            raise HTTPException(status_code=404, detail="Endpoint not found")
        
        if config.user_id != user_id:
            raise HTTPException(status_code=403, detail="Access denied")
        
        # Get statistics
        stats = db.get_endpoint_stats(endpoint_id, hours)
        stats['endpoint_id'] = endpoint_id
        
        return EndpointStatsResponse(**stats)
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting stats for endpoint {endpoint_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{endpoint_id}/test")
async def test_endpoint(
    endpoint_id: str,
    test_message: str = "Hello, this is a test message",
    user_id: str = Depends(get_current_user)
):
    """Test an endpoint with a simple message"""
    try:
        db = get_database_manager()
        config = db.get_endpoint_config(endpoint_id)
        
        if not config:
            raise HTTPException(status_code=404, detail="Endpoint not found")
        
        if config.user_id != user_id:
            raise HTTPException(status_code=403, detail="Access denied")
        
        # Test the endpoint
        result = await endpoint_service.test_endpoint(endpoint_id, test_message)
        
        return {
            "success": result.get("success", False),
            "response": result.get("response", ""),
            "error": result.get("error"),
            "response_time_ms": result.get("response_time_ms", 0)
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error testing endpoint {endpoint_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/ai-assistant", response_model=AIAssistantResponse)
async def ai_assistant_chat(
    request: AIAssistantRequest,
    user_id: str = Depends(get_current_user)
):
    """Chat with AI assistant for endpoint configuration help"""
    try:
        # Get user's existing endpoints for context
        db = get_database_manager()
        existing_endpoints = db.get_user_endpoint_configs(user_id)
        
        context = {
            "user_id": user_id,
            "existing_endpoints": [ep.to_dict() for ep in existing_endpoints],
            "additional_context": request.context or {}
        }
        
        # Get AI assistant response
        response = await ai_assistant.process_message(request.message, context)
        
        return AIAssistantResponse(**response)
    
    except Exception as e:
        logger.error(f"Error in AI assistant chat: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/templates/provider-types")
async def get_provider_types():
    """Get available provider types and their configuration templates"""
    return {
        "provider_types": [
            {
                "type": ProviderType.REST_API.value,
                "name": "REST API",
                "description": "Standard REST API endpoints with authentication",
                "config_template": {
                    "api_base_url": "https://api.example.com",
                    "auth_type": "api_key",
                    "api_key": "",
                    "headers": {},
                    "timeout": 30,
                    "max_retries": 3
                }
            },
            {
                "type": ProviderType.WEB_CHAT.value,
                "name": "Web Chat Interface",
                "description": "Browser-based chat interfaces (ChatGPT, Claude, etc.)",
                "config_template": {
                    "url": "https://chat.example.com",
                    "username": "",
                    "password": "",
                    "input_selector": "#message-input",
                    "send_button_selector": "#send-button",
                    "response_selector": ".message-response",
                    "wait_for_response": 10,
                    "use_stealth": True
                }
            },
            {
                "type": ProviderType.API_TOKEN.value,
                "name": "API Token",
                "description": "Token-based API access with custom authentication",
                "config_template": {
                    "api_base_url": "https://api.example.com",
                    "auth_type": "bearer_token",
                    "bearer_token": "",
                    "custom_headers": {},
                    "token_refresh_url": "",
                    "timeout": 30
                }
            }
        ],
        "auth_types": [auth_type.value for auth_type in AuthType]
    }


# Routing Configuration Models
class RoutingConfigRequest(BaseModel):
    default_route: str = Field(..., description="Default routing target (codegen_api or zai_webui)")
    zai_webui_enabled: bool = Field(True, description="Enable Z.AI Web UI routing")
    load_balancing: str = Field("round_robin", description="Load balancing strategy")
    fallback_enabled: bool = Field(True, description="Enable fallback routing")

class RoutingConfigResponse(BaseModel):
    default_route: str
    zai_webui_enabled: bool
    load_balancing: str
    fallback_enabled: bool
    auto_scaling: Dict[str, Any]
    health_check: Dict[str, Any]

class DefaultEndpointResponse(BaseModel):
    id: str
    name: str
    model_name: str
    description: str
    provider_type: str
    provider_name: str
    config_data: Dict[str, Any]
    status: str
    is_enabled: bool


# Routing Configuration Endpoints
@router.get("/routing/config", response_model=RoutingConfigResponse)
async def get_routing_config():
    """Get current routing configuration"""
    try:
        config = RoutingConfigManager.get_default_routing_config()
        return RoutingConfigResponse(**config)
    
    except Exception as e:
        logger.error(f"Error getting routing config: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/routing/config")
async def update_routing_config(
    config: RoutingConfigRequest,
    user_id: str = Depends(get_current_user)
):
    """Update routing configuration"""
    try:
        # Update the routing configuration
        config_dict = config.dict()
        ProxyConfig.update_routing_config(config_dict)
        
        return {
            "message": "Routing configuration updated successfully",
            "config": config_dict
        }
    
    except Exception as e:
        logger.error(f"Error updating routing config: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/routing/toggle-zai-webui")
async def toggle_zai_webui(
    enabled: bool = Query(..., description="Enable or disable Z.AI Web UI routing"),
    user_id: str = Depends(get_current_user)
):
    """Toggle Z.AI Web UI routing on/off"""
    try:
        ProxyConfig.toggle_zai_webui(enabled)
        
        return {
            "message": f"Z.AI Web UI routing {'enabled' if enabled else 'disabled'}",
            "zai_webui_enabled": enabled
        }
    
    except Exception as e:
        logger.error(f"Error toggling Z.AI Web UI: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/defaults/endpoints", response_model=List[DefaultEndpointResponse])
async def get_default_endpoints(
    codegen_org_id: Optional[str] = Query(None, description="Codegen organization ID"),
    codegen_token: Optional[str] = Query(None, description="Codegen authentication token")
):
    """Get default endpoint configurations"""
    try:
        default_configs = DefaultEndpointConfigs.get_all_default_configs(
            codegen_org_id=codegen_org_id,
            codegen_token=codegen_token
        )
        
        return [
            DefaultEndpointResponse(
                id=config.id,
                name=config.name,
                model_name=config.model_name,
                description=config.description,
                provider_type=config.provider_type,
                provider_name=config.provider_name,
                config_data=config.config_data,
                status=config.status,
                is_enabled=config.is_enabled
            )
            for config in default_configs
        ]
    
    except Exception as e:
        logger.error(f"Error getting default endpoints: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/templates/providers")
async def get_provider_templates():
    """Get provider configuration templates"""
    try:
        templates = DefaultEndpointConfigs.get_provider_templates()
        return {
            "templates": templates,
            "count": len(templates)
        }
    
    except Exception as e:
        logger.error(f"Error getting provider templates: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/endpoints/from-template")
async def create_endpoint_from_template(
    template_name: str = Query(..., description="Template name to use"),
    name: str = Query(..., description="Custom name for the endpoint"),
    config_overrides: Optional[Dict[str, Any]] = None,
    user_id: str = Depends(get_current_user)
):
    """Create an endpoint from a template"""
    try:
        # Create endpoint from template
        endpoint_config = DefaultEndpointConfigs.create_endpoint_from_template(
            template_name=template_name,
            user_id=user_id,
            name=name,
            config_overrides=config_overrides or {}
        )
        
        # Save to database
        db = get_database_manager()
        db.create_endpoint_config(endpoint_config)
        
        return {
            "message": "Endpoint created from template successfully",
            "endpoint": {
                "id": endpoint_config.id,
                "name": endpoint_config.name,
                "template_used": template_name,
                "provider_type": endpoint_config.provider_type
            }
        }
    
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error creating endpoint from template: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/routing/rules/examples")
async def get_example_routing_rules():
    """Get example routing rules for different scenarios"""
    try:
        examples = RoutingConfigManager.get_example_routing_rules()
        return {
            "examples": examples,
            "count": len(examples)
        }
    
    except Exception as e:
        logger.error(f"Error getting example routing rules: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health")
async def health_check():
    """Health check endpoint"""
    try:
        # Test database connection
        db = get_database_manager()
        with db.get_connection() as conn:
            conn.execute("SELECT 1").fetchone()
        
        return {
            "status": "healthy",
            "timestamp": datetime.utcnow().isoformat(),
            "database": "connected"
        }
    
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(status_code=503, detail="Service unhealthy")
