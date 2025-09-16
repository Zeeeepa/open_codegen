"""
WebSocket routes for real-time chat functionality.
Provides WebSocket endpoints for real-time communication with AI providers.
"""

import json
import logging
import asyncio
from typing import Dict, List, Optional, Any
from datetime import datetime
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends
from fastapi.websockets import WebSocketState

from backend.supabase.client import get_supabase_manager, SupabaseManager
from backend.supabase.models import ChatSession, ChatMessage, EndpointContext

logger = logging.getLogger(__name__)

router = APIRouter()


class ConnectionManager:
    """Manages WebSocket connections for real-time chat."""
    
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
        self.session_connections: Dict[str, List[str]] = {}  # session_id -> [connection_ids]
    
    async def connect(self, websocket: WebSocket, connection_id: str, session_id: Optional[str] = None):
        """Accept a new WebSocket connection."""
        await websocket.accept()
        self.active_connections[connection_id] = websocket
        
        if session_id:
            if session_id not in self.session_connections:
                self.session_connections[session_id] = []
            self.session_connections[session_id].append(connection_id)
        
        logger.info(f"WebSocket connection {connection_id} connected for session {session_id}")
    
    def disconnect(self, connection_id: str, session_id: Optional[str] = None):
        """Remove a WebSocket connection."""
        if connection_id in self.active_connections:
            del self.active_connections[connection_id]
        
        if session_id and session_id in self.session_connections:
            if connection_id in self.session_connections[session_id]:
                self.session_connections[session_id].remove(connection_id)
            
            # Clean up empty session lists
            if not self.session_connections[session_id]:
                del self.session_connections[session_id]
        
        logger.info(f"WebSocket connection {connection_id} disconnected from session {session_id}")
    
    async def send_personal_message(self, message: dict, connection_id: str):
        """Send a message to a specific connection."""
        if connection_id in self.active_connections:
            websocket = self.active_connections[connection_id]
            if websocket.client_state == WebSocketState.CONNECTED:
                try:
                    await websocket.send_text(json.dumps(message))
                except Exception as e:
                    logger.error(f"Failed to send message to {connection_id}: {e}")
                    self.disconnect(connection_id)
    
    async def broadcast_to_session(self, message: dict, session_id: str):
        """Broadcast a message to all connections in a session."""
        if session_id in self.session_connections:
            disconnected_connections = []
            
            for connection_id in self.session_connections[session_id]:
                if connection_id in self.active_connections:
                    websocket = self.active_connections[connection_id]
                    if websocket.client_state == WebSocketState.CONNECTED:
                        try:
                            await websocket.send_text(json.dumps(message))
                        except Exception as e:
                            logger.error(f"Failed to broadcast to {connection_id}: {e}")
                            disconnected_connections.append(connection_id)
            
            # Clean up disconnected connections
            for connection_id in disconnected_connections:
                self.disconnect(connection_id, session_id)
    
    def get_session_connections(self, session_id: str) -> List[str]:
        """Get all connection IDs for a session."""
        return self.session_connections.get(session_id, [])


# Global connection manager
manager = ConnectionManager()


def get_db() -> Optional[SupabaseManager]:
    """Dependency to get the Supabase manager (optional for WebSocket)."""
    return get_supabase_manager()


@router.websocket("/ws/chat/{session_id}")
async def websocket_chat_endpoint(
    websocket: WebSocket, 
    session_id: str,
    connection_id: Optional[str] = None
):
    """
    WebSocket endpoint for real-time chat communication.
    
    Message format:
    {
        "type": "message|system|error|status",
        "content": "message content",
        "role": "user|assistant|system",
        "endpoint_id": "optional endpoint id",
        "provider": "optional provider name",
        "metadata": {}
    }
    """
    if not connection_id:
        connection_id = f"conn_{datetime.now().timestamp()}_{id(websocket)}"
    
    db = get_db()
    
    await manager.connect(websocket, connection_id, session_id)
    
    try:
        # Send connection confirmation
        await manager.send_personal_message({
            "type": "system",
            "content": "Connected to chat session",
            "session_id": session_id,
            "connection_id": connection_id,
            "timestamp": datetime.now().isoformat()
        }, connection_id)
        
        # Load existing session if available
        if db:
            try:
                session = await db.get_chat_session(session_id)
                if session:
                    await manager.send_personal_message({
                        "type": "session_info",
                        "session": session.dict(),
                        "timestamp": datetime.now().isoformat()
                    }, connection_id)
                
                # Load recent messages
                messages = await db.get_chat_messages(session_id, limit=50)
                for message in messages:
                    await manager.send_personal_message({
                        "type": "history_message",
                        "message": message.dict(),
                        "timestamp": datetime.now().isoformat()
                    }, connection_id)
                    
            except Exception as e:
                logger.error(f"Failed to load session data: {e}")
        
        # Handle incoming messages
        while True:
            try:
                data = await websocket.receive_text()
                message_data = json.loads(data)
                
                await handle_websocket_message(
                    message_data, 
                    session_id, 
                    connection_id, 
                    db
                )
                
            except WebSocketDisconnect:
                break
            except json.JSONDecodeError as e:
                await manager.send_personal_message({
                    "type": "error",
                    "content": f"Invalid JSON format: {str(e)}",
                    "timestamp": datetime.now().isoformat()
                }, connection_id)
            except Exception as e:
                logger.error(f"Error handling WebSocket message: {e}")
                await manager.send_personal_message({
                    "type": "error",
                    "content": f"Server error: {str(e)}",
                    "timestamp": datetime.now().isoformat()
                }, connection_id)
    
    except WebSocketDisconnect:
        pass
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
    finally:
        manager.disconnect(connection_id, session_id)


async def handle_websocket_message(
    message_data: dict, 
    session_id: str, 
    connection_id: str, 
    db: Optional[SupabaseManager]
):
    """Handle incoming WebSocket messages."""
    message_type = message_data.get("type", "message")
    
    if message_type == "message":
        await handle_chat_message(message_data, session_id, connection_id, db)
    elif message_type == "system":
        await handle_system_message(message_data, session_id, connection_id, db)
    elif message_type == "ping":
        await manager.send_personal_message({
            "type": "pong",
            "timestamp": datetime.now().isoformat()
        }, connection_id)
    else:
        await manager.send_personal_message({
            "type": "error",
            "content": f"Unknown message type: {message_type}",
            "timestamp": datetime.now().isoformat()
        }, connection_id)


async def handle_chat_message(
    message_data: dict, 
    session_id: str, 
    connection_id: str, 
    db: Optional[SupabaseManager]
):
    """Handle chat messages from users."""
    try:
        content = message_data.get("content", "")
        role = message_data.get("role", "user")
        endpoint_id = message_data.get("endpoint_id")
        provider = message_data.get("provider")
        metadata = message_data.get("metadata", {})
        
        if not content.strip():
            await manager.send_personal_message({
                "type": "error",
                "content": "Message content cannot be empty",
                "timestamp": datetime.now().isoformat()
            }, connection_id)
            return
        
        # Create message object
        chat_message = ChatMessage(
            session_id=session_id,
            role=role,
            content=content,
            endpoint_id=endpoint_id,
            provider=provider,
            metadata=metadata
        )
        
        # Store message in database if available
        if db:
            try:
                stored_message = await db.add_chat_message(chat_message)
                chat_message = stored_message
            except Exception as e:
                logger.error(f"Failed to store message: {e}")
        
        # Broadcast message to all session connections
        await manager.broadcast_to_session({
            "type": "message",
            "message": chat_message.dict(),
            "timestamp": datetime.now().isoformat()
        }, session_id)
        
        # If this is a user message, process it and generate AI response
        if role == "user":
            await process_ai_response(
                chat_message, 
                session_id, 
                connection_id, 
                db
            )
    
    except Exception as e:
        logger.error(f"Error handling chat message: {e}")
        await manager.send_personal_message({
            "type": "error",
            "content": f"Failed to process message: {str(e)}",
            "timestamp": datetime.now().isoformat()
        }, connection_id)


async def handle_system_message(
    message_data: dict, 
    session_id: str, 
    connection_id: str, 
    db: Optional[SupabaseManager]
):
    """Handle system messages (session management, etc.)."""
    try:
        action = message_data.get("action")
        
        if action == "switch_endpoint":
            endpoint_id = message_data.get("endpoint_id")
            if endpoint_id and db:
                # Update session endpoint
                try:
                    endpoint = await db.get_endpoint(endpoint_id)
                    if endpoint:
                        # Update session (this would need to be implemented in SupabaseManager)
                        await manager.broadcast_to_session({
                            "type": "system",
                            "content": f"Switched to endpoint: {endpoint.name}",
                            "endpoint": endpoint.dict(),
                            "timestamp": datetime.now().isoformat()
                        }, session_id)
                    else:
                        await manager.send_personal_message({
                            "type": "error",
                            "content": "Endpoint not found",
                            "timestamp": datetime.now().isoformat()
                        }, connection_id)
                except Exception as e:
                    logger.error(f"Failed to switch endpoint: {e}")
        
        elif action == "get_session_info":
            if db:
                try:
                    session = await db.get_chat_session(session_id)
                    if session:
                        await manager.send_personal_message({
                            "type": "session_info",
                            "session": session.dict(),
                            "timestamp": datetime.now().isoformat()
                        }, connection_id)
                except Exception as e:
                    logger.error(f"Failed to get session info: {e}")
        
        else:
            await manager.send_personal_message({
                "type": "error",
                "content": f"Unknown system action: {action}",
                "timestamp": datetime.now().isoformat()
            }, connection_id)
    
    except Exception as e:
        logger.error(f"Error handling system message: {e}")


async def process_ai_response(
    user_message: ChatMessage, 
    session_id: str, 
    connection_id: str, 
    db: Optional[SupabaseManager]
):
    """Process user message and generate AI response."""
    try:
        # This is a placeholder for the actual AI processing logic
        # In a real implementation, this would:
        # 1. Load the endpoint configuration
        # 2. Format the request based on the endpoint type
        # 3. Send the request to the appropriate AI provider or website
        # 4. Stream the response back to the client
        # 5. Store the response in the database
        
        # Send typing indicator
        await manager.broadcast_to_session({
            "type": "status",
            "content": "AI is typing...",
            "status": "typing",
            "timestamp": datetime.now().isoformat()
        }, session_id)
        
        # Simulate AI processing delay
        await asyncio.sleep(1)
        
        # Generate mock response
        ai_response = ChatMessage(
            session_id=session_id,
            role="assistant",
            content=f"This is a mock response to: {user_message.content}",
            endpoint_id=user_message.endpoint_id,
            provider=user_message.provider or "mock",
            metadata={"response_time": 1.0, "tokens_used": 50}
        )
        
        # Store AI response in database if available
        if db:
            try:
                stored_response = await db.add_chat_message(ai_response)
                ai_response = stored_response
            except Exception as e:
                logger.error(f"Failed to store AI response: {e}")
        
        # Send AI response
        await manager.broadcast_to_session({
            "type": "message",
            "message": ai_response.dict(),
            "timestamp": datetime.now().isoformat()
        }, session_id)
        
        # Clear typing indicator
        await manager.broadcast_to_session({
            "type": "status",
            "content": "",
            "status": "idle",
            "timestamp": datetime.now().isoformat()
        }, session_id)
    
    except Exception as e:
        logger.error(f"Error processing AI response: {e}")
        await manager.broadcast_to_session({
            "type": "error",
            "content": f"Failed to generate AI response: {str(e)}",
            "timestamp": datetime.now().isoformat()
        }, session_id)


@router.websocket("/ws/status")
async def websocket_status_endpoint(websocket: WebSocket):
    """WebSocket endpoint for system status updates."""
    connection_id = f"status_{datetime.now().timestamp()}_{id(websocket)}"
    
    await websocket.accept()
    
    try:
        # Send initial status
        db = get_db()
        status = {
            "type": "status",
            "supabase_connected": db is not None and db.connected if db else False,
            "active_connections": len(manager.active_connections),
            "active_sessions": len(manager.session_connections),
            "timestamp": datetime.now().isoformat()
        }
        
        await websocket.send_text(json.dumps(status))
        
        # Keep connection alive and send periodic updates
        while True:
            await asyncio.sleep(30)  # Send status every 30 seconds
            
            # Update status
            status["active_connections"] = len(manager.active_connections)
            status["active_sessions"] = len(manager.session_connections)
            status["timestamp"] = datetime.now().isoformat()
            
            if db:
                try:
                    health = await db.health_check()
                    status["supabase_status"] = health
                except Exception as e:
                    status["supabase_error"] = str(e)
            
            await websocket.send_text(json.dumps(status))
    
    except WebSocketDisconnect:
        pass
    except Exception as e:
        logger.error(f"Status WebSocket error: {e}")


# Utility functions for external use

def get_connection_manager() -> ConnectionManager:
    """Get the global connection manager."""
    return manager


async def broadcast_system_message(message: dict, session_id: Optional[str] = None):
    """Broadcast a system message to all connections or a specific session."""
    if session_id:
        await manager.broadcast_to_session(message, session_id)
    else:
        # Broadcast to all connections
        for connection_id in manager.active_connections:
            await manager.send_personal_message(message, connection_id)
