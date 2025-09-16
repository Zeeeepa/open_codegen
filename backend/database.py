"""
Database models and Supabase integration for OpenCodegen
"""
import os
import json
import asyncio
from datetime import datetime
from typing import Optional, List, Dict, Any
from dataclasses import dataclass, asdict
from supabase import create_client, Client
import logging

logger = logging.getLogger(__name__)

@dataclass
class EndpointConfig:
    """Configuration for a custom API endpoint"""
    id: str
    name: str
    url: str
    method: str = "POST"
    headers: Dict[str, str] = None
    model_name: str = "custom-model"
    text_input_selector: str = ""
    send_button_selector: str = ""
    response_selector: str = ""
    variables: Dict[str, Any] = None
    created_at: datetime = None
    updated_at: datetime = None
    user_id: str = None
    is_active: bool = True
    
    def __post_init__(self):
        if self.headers is None:
            self.headers = {}
        if self.variables is None:
            self.variables = {}
        if self.created_at is None:
            self.created_at = datetime.utcnow()
        if self.updated_at is None:
            self.updated_at = datetime.utcnow()

@dataclass
class ChatMessage:
    """Chat message model"""
    id: str
    conversation_id: str
    role: str  # user, assistant, system
    content: str
    endpoint_id: Optional[str] = None
    created_at: datetime = None
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.utcnow()
        if self.metadata is None:
            self.metadata = {}

@dataclass
class Conversation:
    """Conversation model"""
    id: str
    title: str
    user_id: str
    created_at: datetime = None
    updated_at: datetime = None
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.utcnow()
        if self.updated_at is None:
            self.updated_at = datetime.utcnow()
        if self.metadata is None:
            self.metadata = {}

@dataclass
class WebsiteIntegration:
    """Website integration configuration"""
    id: str
    name: str
    url: str
    text_selectors: List[str]
    api_endpoints: List[str] = None
    authentication: Dict[str, Any] = None
    rate_limit: int = 60  # requests per minute
    created_at: datetime = None
    updated_at: datetime = None
    user_id: str = None
    is_active: bool = True
    
    def __post_init__(self):
        if self.api_endpoints is None:
            self.api_endpoints = []
        if self.authentication is None:
            self.authentication = {}
        if self.created_at is None:
            self.created_at = datetime.utcnow()
        if self.updated_at is None:
            self.updated_at = datetime.utcnow()

class SupabaseManager:
    """Manages Supabase database operations"""
    
    def __init__(self):
        self.client: Optional[Client] = None
        self.connected = False
        
    async def connect(self, supabase_url: str, supabase_key: str) -> bool:
        """Connect to Supabase"""
        try:
            self.client = create_client(supabase_url, supabase_key)
            
            # Test connection
            result = self.client.table('endpoints').select('id').limit(1).execute()
            self.connected = True
            logger.info("Successfully connected to Supabase")
            return True
            
        except Exception as e:
            logger.error(f"Failed to connect to Supabase: {e}")
            self.connected = False
            return False
    
    def is_connected(self) -> bool:
        """Check if connected to Supabase"""
        return self.connected and self.client is not None
    
    # Endpoint CRUD operations
    async def create_endpoint(self, endpoint: EndpointConfig) -> bool:
        """Create a new endpoint configuration"""
        try:
            if not self.is_connected():
                return False
                
            data = {
                'id': endpoint.id,
                'name': endpoint.name,
                'url': endpoint.url,
                'method': endpoint.method,
                'headers': json.dumps(endpoint.headers),
                'model_name': endpoint.model_name,
                'text_input_selector': endpoint.text_input_selector,
                'send_button_selector': endpoint.send_button_selector,
                'response_selector': endpoint.response_selector,
                'variables': json.dumps(endpoint.variables),
                'user_id': endpoint.user_id,
                'is_active': endpoint.is_active,
                'created_at': endpoint.created_at.isoformat(),
                'updated_at': endpoint.updated_at.isoformat()
            }
            
            result = self.client.table('endpoints').insert(data).execute()
            return len(result.data) > 0
            
        except Exception as e:
            logger.error(f"Failed to create endpoint: {e}")
            return False
    
    async def get_endpoint(self, endpoint_id: str) -> Optional[EndpointConfig]:
        """Get endpoint by ID"""
        try:
            if not self.is_connected():
                return None
                
            result = self.client.table('endpoints').select('*').eq('id', endpoint_id).execute()
            
            if result.data:
                data = result.data[0]
                return EndpointConfig(
                    id=data['id'],
                    name=data['name'],
                    url=data['url'],
                    method=data['method'],
                    headers=json.loads(data['headers']) if data['headers'] else {},
                    model_name=data['model_name'],
                    text_input_selector=data['text_input_selector'],
                    send_button_selector=data['send_button_selector'],
                    response_selector=data['response_selector'],
                    variables=json.loads(data['variables']) if data['variables'] else {},
                    user_id=data['user_id'],
                    is_active=data['is_active'],
                    created_at=datetime.fromisoformat(data['created_at']),
                    updated_at=datetime.fromisoformat(data['updated_at'])
                )
            return None
            
        except Exception as e:
            logger.error(f"Failed to get endpoint: {e}")
            return None
    
    async def list_endpoints(self, user_id: Optional[str] = None) -> List[EndpointConfig]:
        """List all endpoints, optionally filtered by user"""
        try:
            if not self.is_connected():
                return []
                
            query = self.client.table('endpoints').select('*')
            if user_id:
                query = query.eq('user_id', user_id)
                
            result = query.execute()
            
            endpoints = []
            for data in result.data:
                endpoints.append(EndpointConfig(
                    id=data['id'],
                    name=data['name'],
                    url=data['url'],
                    method=data['method'],
                    headers=json.loads(data['headers']) if data['headers'] else {},
                    model_name=data['model_name'],
                    text_input_selector=data['text_input_selector'],
                    send_button_selector=data['send_button_selector'],
                    response_selector=data['response_selector'],
                    variables=json.loads(data['variables']) if data['variables'] else {},
                    user_id=data['user_id'],
                    is_active=data['is_active'],
                    created_at=datetime.fromisoformat(data['created_at']),
                    updated_at=datetime.fromisoformat(data['updated_at'])
                ))
            
            return endpoints
            
        except Exception as e:
            logger.error(f"Failed to list endpoints: {e}")
            return []
    
    async def update_endpoint(self, endpoint: EndpointConfig) -> bool:
        """Update an existing endpoint"""
        try:
            if not self.is_connected():
                return False
                
            endpoint.updated_at = datetime.utcnow()
            
            data = {
                'name': endpoint.name,
                'url': endpoint.url,
                'method': endpoint.method,
                'headers': json.dumps(endpoint.headers),
                'model_name': endpoint.model_name,
                'text_input_selector': endpoint.text_input_selector,
                'send_button_selector': endpoint.send_button_selector,
                'response_selector': endpoint.response_selector,
                'variables': json.dumps(endpoint.variables),
                'is_active': endpoint.is_active,
                'updated_at': endpoint.updated_at.isoformat()
            }
            
            result = self.client.table('endpoints').update(data).eq('id', endpoint.id).execute()
            return len(result.data) > 0
            
        except Exception as e:
            logger.error(f"Failed to update endpoint: {e}")
            return False
    
    async def delete_endpoint(self, endpoint_id: str) -> bool:
        """Delete an endpoint"""
        try:
            if not self.is_connected():
                return False
                
            result = self.client.table('endpoints').delete().eq('id', endpoint_id).execute()
            return len(result.data) > 0
            
        except Exception as e:
            logger.error(f"Failed to delete endpoint: {e}")
            return False
    
    # Chat operations
    async def create_conversation(self, conversation: Conversation) -> bool:
        """Create a new conversation"""
        try:
            if not self.is_connected():
                return False
                
            data = {
                'id': conversation.id,
                'title': conversation.title,
                'user_id': conversation.user_id,
                'metadata': json.dumps(conversation.metadata),
                'created_at': conversation.created_at.isoformat(),
                'updated_at': conversation.updated_at.isoformat()
            }
            
            result = self.client.table('conversations').insert(data).execute()
            return len(result.data) > 0
            
        except Exception as e:
            logger.error(f"Failed to create conversation: {e}")
            return False
    
    async def add_message(self, message: ChatMessage) -> bool:
        """Add a message to a conversation"""
        try:
            if not self.is_connected():
                return False
                
            data = {
                'id': message.id,
                'conversation_id': message.conversation_id,
                'role': message.role,
                'content': message.content,
                'endpoint_id': message.endpoint_id,
                'metadata': json.dumps(message.metadata),
                'created_at': message.created_at.isoformat()
            }
            
            result = self.client.table('messages').insert(data).execute()
            return len(result.data) > 0
            
        except Exception as e:
            logger.error(f"Failed to add message: {e}")
            return False
    
    async def get_conversation_messages(self, conversation_id: str) -> List[ChatMessage]:
        """Get all messages for a conversation"""
        try:
            if not self.is_connected():
                return []
                
            result = self.client.table('messages').select('*').eq('conversation_id', conversation_id).order('created_at').execute()
            
            messages = []
            for data in result.data:
                messages.append(ChatMessage(
                    id=data['id'],
                    conversation_id=data['conversation_id'],
                    role=data['role'],
                    content=data['content'],
                    endpoint_id=data['endpoint_id'],
                    metadata=json.loads(data['metadata']) if data['metadata'] else {},
                    created_at=datetime.fromisoformat(data['created_at'])
                ))
            
            return messages
            
        except Exception as e:
            logger.error(f"Failed to get conversation messages: {e}")
            return []
    
    # Website integration operations
    async def create_website_integration(self, integration: WebsiteIntegration) -> bool:
        """Create a new website integration"""
        try:
            if not self.is_connected():
                return False
                
            data = {
                'id': integration.id,
                'name': integration.name,
                'url': integration.url,
                'text_selectors': json.dumps(integration.text_selectors),
                'api_endpoints': json.dumps(integration.api_endpoints),
                'authentication': json.dumps(integration.authentication),
                'rate_limit': integration.rate_limit,
                'user_id': integration.user_id,
                'is_active': integration.is_active,
                'created_at': integration.created_at.isoformat(),
                'updated_at': integration.updated_at.isoformat()
            }
            
            result = self.client.table('website_integrations').insert(data).execute()
            return len(result.data) > 0
            
        except Exception as e:
            logger.error(f"Failed to create website integration: {e}")
            return False

# Global database manager instance
db_manager = SupabaseManager()
