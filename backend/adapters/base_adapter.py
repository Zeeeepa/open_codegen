"""
Base adapter interface for the Universal AI Endpoint Management System
"""

import logging
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List, AsyncGenerator
from dataclasses import dataclass
from datetime import datetime
import uuid

logger = logging.getLogger(__name__)

@dataclass
class AdapterResponse:
    """Standardized response format for all adapters"""
    id: str
    provider: str
    model: str
    content: str
    response_type: str = "text"
    metadata: Dict[str, Any] = None
    usage: Dict[str, Any] = None
    session_id: Optional[str] = None
    timestamp: str = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}
        if self.usage is None:
            self.usage = {}
        if self.timestamp is None:
            self.timestamp = datetime.utcnow().isoformat()
        if not self.id:
            self.id = f"resp-{uuid.uuid4().hex[:8]}"

class AdapterError(Exception):
    """Base exception for adapter errors"""
    def __init__(self, message: str, error_code: str = None, details: Dict[str, Any] = None):
        super().__init__(message)
        self.error_code = error_code or "ADAPTER_ERROR"
        self.details = details or {}

class BaseAdapter(ABC):
    """Base adapter interface for all AI providers"""
    
    def __init__(self, provider_config: Dict[str, Any]):
        self.provider_config = provider_config
        self.provider_name = provider_config.get('name', 'unknown')
        self.provider_type = provider_config.get('provider_type', 'unknown')
        self.is_initialized = False
        self.session_data = {}
        
    @abstractmethod
    async def initialize(self) -> bool:
        """Initialize the adapter (authentication, setup, etc.)"""
        pass
    
    @abstractmethod
    async def send_message(self, message: str, **kwargs) -> AdapterResponse:
        """Send a message and get response"""
        pass
    
    @abstractmethod
    async def stream_message(self, message: str, **kwargs) -> AsyncGenerator[str, None]:
        """Send a message and stream response"""
        pass
    
    @abstractmethod
    async def health_check(self) -> Dict[str, Any]:
        """Check adapter health and availability"""
        pass
    
    @abstractmethod
    async def cleanup(self) -> None:
        """Clean up resources"""
        pass
    
    async def start_session(self, session_id: str = None) -> str:
        """Start a new session"""
        if session_id is None:
            session_id = f"sess-{uuid.uuid4().hex[:8]}"
        
        self.session_data[session_id] = {
            'created_at': datetime.utcnow().isoformat(),
            'last_activity': datetime.utcnow().isoformat(),
            'message_count': 0,
            'conversation_history': []
        }
        
        logger.info(f"Started session {session_id} for provider {self.provider_name}")
        return session_id
    
    async def end_session(self, session_id: str) -> bool:
        """End a session"""
        if session_id in self.session_data:
            del self.session_data[session_id]
            logger.info(f"Ended session {session_id} for provider {self.provider_name}")
            return True
        return False
    
    def get_session_data(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get session data"""
        return self.session_data.get(session_id)
    
    def update_session_activity(self, session_id: str):
        """Update session last activity"""
        if session_id in self.session_data:
            self.session_data[session_id]['last_activity'] = datetime.utcnow().isoformat()
            self.session_data[session_id]['message_count'] += 1
    
    def add_to_conversation_history(self, session_id: str, role: str, content: str):
        """Add message to conversation history"""
        if session_id in self.session_data:
            self.session_data[session_id]['conversation_history'].append({
                'role': role,
                'content': content,
                'timestamp': datetime.utcnow().isoformat()
            })
    
    def get_conversation_history(self, session_id: str) -> List[Dict[str, Any]]:
        """Get conversation history for session"""
        session = self.session_data.get(session_id, {})
        return session.get('conversation_history', [])
    
    def get_model_mapping(self, requested_model: str) -> str:
        """Map requested model to provider-specific model"""
        model_mapping = self.provider_config.get('model_mapping', {})
        return model_mapping.get(requested_model, requested_model)
    
    def validate_request(self, message: str, **kwargs) -> bool:
        """Validate request parameters"""
        if not message or not message.strip():
            raise AdapterError("Message cannot be empty", "INVALID_MESSAGE")
        
        max_length = self.provider_config.get('max_message_length', 10000)
        if len(message) > max_length:
            raise AdapterError(f"Message too long (max {max_length} characters)", "MESSAGE_TOO_LONG")
        
        return True
    
    def create_response(self, content: str, model: str, session_id: str = None, **kwargs) -> AdapterResponse:
        """Create standardized response"""
        return AdapterResponse(
            id=f"resp-{uuid.uuid4().hex[:8]}",
            provider=self.provider_name,
            model=model,
            content=content,
            session_id=session_id,
            metadata=kwargs.get('metadata', {}),
            usage=kwargs.get('usage', {})
        )
    
    async def __aenter__(self):
        """Async context manager entry"""
        await self.initialize()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        await self.cleanup()
