"""
FastAPI routes for Supabase integration.
Provides REST API endpoints for managing database connections, endpoints, and configurations.
"""

import logging
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from fastapi.responses import JSONResponse

from backend.supabase.client import get_supabase_manager, initialize_supabase, SupabaseManager
from backend.supabase.models import (
    SupabaseConnectionConfig, SupabaseConnectionTest,
    EndpointContext, WebsiteConfig, ChatSession, ChatMessage,
    EndpointVariable, BrowserInteraction, EndpointTest,
    CreateEndpointRequest, UpdateEndpointRequest, TestEndpointRequest,
    EndpointType, EndpointStatus, VariableType
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/supabase", tags=["supabase"])


def get_db() -> SupabaseManager:
    """Dependency to get the Supabase manager."""
    db = get_supabase_manager()
    if not db:
        raise HTTPException(status_code=503, detail="Supabase not connected")
    return db


@router.post("/connect", response_model=SupabaseConnectionTest)
async def connect_supabase(config: SupabaseConnectionConfig):
    """
    Connect to Supabase database with the provided configuration.
    Tests the connection and creates tables if needed.
    """
    try:
        result = await initialize_supabase(config)
        return result
    except Exception as e:
        logger.error(f"Failed to connect to Supabase: {e}")
        raise HTTPException(status_code=500, detail=f"Connection failed: {str(e)}")


@router.get("/status")
async def get_connection_status():
    """Get the current Supabase connection status."""
    db = get_supabase_manager()
    if not db:
        return {"connected": False, "message": "Not connected to Supabase"}
    
    try:
        health = await db.health_check()
        return health
    except Exception as e:
        return {"connected": False, "error": str(e)}


@router.get("/stats")
async def get_database_stats(db: SupabaseManager = Depends(get_db)):
    """Get database statistics."""
    try:
        stats = await db.get_stats()
        return stats
    except Exception as e:
        logger.error(f"Failed to get database stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Endpoint management routes

@router.post("/endpoints", response_model=EndpointContext)
async def create_endpoint(request: CreateEndpointRequest, db: SupabaseManager = Depends(get_db)):
    """Create a new endpoint."""
    try:
        # Create the main endpoint
        endpoint = EndpointContext(
            name=request.name,
            endpoint_type=request.endpoint_type,
            url=request.url,
            model_name=request.model_name,
            description=request.description
        )
        
        created_endpoint = await db.create_endpoint(endpoint)
        
        # Create associated website config if provided
        if request.website_config:
            website_config = await db.create_website_config(request.website_config)
            # Update endpoint with website config reference
            await db.update_endpoint(created_endpoint.id, {
                'website_config_id': website_config.id
            })
        
        # Create variables if provided
        for var_data in request.variables:
            var_data.endpoint_id = created_endpoint.id
            await db.create_variable(var_data)
        
        # Create browser interactions if provided
        for interaction_data in request.browser_interactions:
            interaction_data.endpoint_id = created_endpoint.id
            # Note: Browser interactions would be created via a separate method
            # This is a placeholder for the actual implementation
        
        return created_endpoint
        
    except Exception as e:
        logger.error(f"Failed to create endpoint: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/endpoints", response_model=List[EndpointContext])
async def list_endpoints(
    endpoint_type: Optional[EndpointType] = None,
    status: Optional[EndpointStatus] = None,
    db: SupabaseManager = Depends(get_db)
):
    """List all endpoints with optional filtering."""
    try:
        endpoints = await db.list_endpoints(endpoint_type=endpoint_type, status=status)
        return endpoints
    except Exception as e:
        logger.error(f"Failed to list endpoints: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/endpoints/{endpoint_id}", response_model=EndpointContext)
async def get_endpoint(endpoint_id: str, db: SupabaseManager = Depends(get_db)):
    """Get a specific endpoint by ID."""
    try:
        endpoint = await db.get_endpoint(endpoint_id)
        if not endpoint:
            raise HTTPException(status_code=404, detail="Endpoint not found")
        return endpoint
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get endpoint {endpoint_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/endpoints/{endpoint_id}", response_model=EndpointContext)
async def update_endpoint(
    endpoint_id: str, 
    request: UpdateEndpointRequest, 
    db: SupabaseManager = Depends(get_db)
):
    """Update an endpoint."""
    try:
        updates = request.dict(exclude_unset=True)
        updated_endpoint = await db.update_endpoint(endpoint_id, updates)
        if not updated_endpoint:
            raise HTTPException(status_code=404, detail="Endpoint not found")
        return updated_endpoint
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update endpoint {endpoint_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/endpoints/{endpoint_id}")
async def delete_endpoint(endpoint_id: str, db: SupabaseManager = Depends(get_db)):
    """Delete an endpoint."""
    try:
        success = await db.delete_endpoint(endpoint_id)
        if not success:
            raise HTTPException(status_code=404, detail="Endpoint not found")
        return {"message": "Endpoint deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete endpoint {endpoint_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/endpoints/{endpoint_id}/test")
async def test_endpoint(
    endpoint_id: str,
    request: TestEndpointRequest,
    background_tasks: BackgroundTasks,
    db: SupabaseManager = Depends(get_db)
):
    """Test an endpoint functionality."""
    try:
        endpoint = await db.get_endpoint(endpoint_id)
        if not endpoint:
            raise HTTPException(status_code=404, detail="Endpoint not found")
        
        # Add background task to perform the actual test
        background_tasks.add_task(
            _perform_endpoint_test, 
            db, 
            endpoint_id, 
            request.test_message, 
            request.test_type,
            request.timeout
        )
        
        return {"message": "Endpoint test started", "endpoint_id": endpoint_id}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to test endpoint {endpoint_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


async def _perform_endpoint_test(
    db: SupabaseManager, 
    endpoint_id: str, 
    test_message: str, 
    test_type: str,
    timeout: int
):
    """Background task to perform endpoint testing."""
    # This is a placeholder for the actual endpoint testing logic
    # In a real implementation, this would:
    # 1. Load the endpoint configuration
    # 2. Send a test request based on the endpoint type
    # 3. Measure response time and validate the response
    # 4. Store the test results in the database
    
    try:
        # Placeholder test result
        test_result = {
            "status": "success",
            "response_time": 1.5,
            "message": "Test completed successfully"
        }
        
        # Store test result (this would be implemented in the SupabaseManager)
        logger.info(f"Test completed for endpoint {endpoint_id}: {test_result}")
        
    except Exception as e:
        logger.error(f"Test failed for endpoint {endpoint_id}: {e}")


# Variable management routes

@router.get("/endpoints/{endpoint_id}/variables", response_model=List[EndpointVariable])
async def get_endpoint_variables(endpoint_id: str, db: SupabaseManager = Depends(get_db)):
    """Get all variables for an endpoint."""
    try:
        variables = await db.get_endpoint_variables(endpoint_id)
        return variables
    except Exception as e:
        logger.error(f"Failed to get variables for endpoint {endpoint_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/endpoints/{endpoint_id}/variables", response_model=EndpointVariable)
async def create_endpoint_variable(
    endpoint_id: str, 
    variable: EndpointVariable, 
    db: SupabaseManager = Depends(get_db)
):
    """Create a new variable for an endpoint."""
    try:
        # Verify endpoint exists
        endpoint = await db.get_endpoint(endpoint_id)
        if not endpoint:
            raise HTTPException(status_code=404, detail="Endpoint not found")
        
        variable.endpoint_id = endpoint_id
        created_variable = await db.create_variable(variable)
        return created_variable
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to create variable for endpoint {endpoint_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Chat session management routes

@router.post("/chat/sessions", response_model=ChatSession)
async def create_chat_session(session: ChatSession, db: SupabaseManager = Depends(get_db)):
    """Create a new chat session."""
    try:
        created_session = await db.create_chat_session(session)
        return created_session
    except Exception as e:
        logger.error(f"Failed to create chat session: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/chat/sessions/{session_id}", response_model=ChatSession)
async def get_chat_session(session_id: str, db: SupabaseManager = Depends(get_db)):
    """Get a chat session by ID."""
    try:
        session = await db.get_chat_session(session_id)
        if not session:
            raise HTTPException(status_code=404, detail="Chat session not found")
        return session
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get chat session {session_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/chat/sessions/{session_id}/messages", response_model=ChatMessage)
async def add_chat_message(
    session_id: str, 
    message: ChatMessage, 
    db: SupabaseManager = Depends(get_db)
):
    """Add a message to a chat session."""
    try:
        # Verify session exists
        session = await db.get_chat_session(session_id)
        if not session:
            raise HTTPException(status_code=404, detail="Chat session not found")
        
        message.session_id = session_id
        created_message = await db.add_chat_message(message)
        return created_message
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to add message to session {session_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/chat/sessions/{session_id}/messages", response_model=List[ChatMessage])
async def get_chat_messages(
    session_id: str, 
    limit: int = 100, 
    db: SupabaseManager = Depends(get_db)
):
    """Get messages for a chat session."""
    try:
        messages = await db.get_chat_messages(session_id, limit=limit)
        return messages
    except Exception as e:
        logger.error(f"Failed to get messages for session {session_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Website configuration routes

@router.post("/website-configs", response_model=WebsiteConfig)
async def create_website_config(config: WebsiteConfig, db: SupabaseManager = Depends(get_db)):
    """Create a new website configuration."""
    try:
        created_config = await db.create_website_config(config)
        return created_config
    except Exception as e:
        logger.error(f"Failed to create website config: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/website-configs/{config_id}", response_model=WebsiteConfig)
async def get_website_config(config_id: str, db: SupabaseManager = Depends(get_db)):
    """Get a website configuration by ID."""
    try:
        config = await db.get_website_config(config_id)
        if not config:
            raise HTTPException(status_code=404, detail="Website configuration not found")
        return config
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get website config {config_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Utility routes

@router.get("/health")
async def health_check():
    """Health check endpoint."""
    db = get_supabase_manager()
    if not db:
        return {"status": "unhealthy", "message": "Supabase not connected"}
    
    try:
        health = await db.health_check()
        return health
    except Exception as e:
        return {"status": "unhealthy", "error": str(e)}


@router.get("/tables")
async def list_tables(db: SupabaseManager = Depends(get_db)):
    """List all database tables."""
    try:
        return {"tables": list(db.tables.keys()), "table_names": list(db.tables.values())}
    except Exception as e:
        logger.error(f"Failed to list tables: {e}")
        raise HTTPException(status_code=500, detail=str(e))
